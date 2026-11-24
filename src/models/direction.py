"""Klasifier arah perubahan harga (EKSPLORATIF, D-141; bukan uji praregistrasi).

Diagnostik D-139/D-140 menunjukkan ramalan regresi M1/M2 tidak lebih baik dari menebak arah terbanyak. Pertanyaan
eksploratif: apakah model yang LANGSUNG dilatih untuk arah (bukan regresi yang tandanya diambil) lebih baik, dan apakah
fitur kurs membantu di sana? Dua varian, fitur & protokol sama dengan Task 4 (features.forecast, rolling-origin,
latih hanya t + h ≤ origin, harga dunia as-of `available_at`):

- C1: HistGradientBoostingClassifier, kelompok fitur base + id (tanpa kurs/harga dunia);
- C2: C1 + fx (= fitur M3) → selisih C2 − C1 = ablation fitur kurs pada klasifier.

Hiperparameter = params.forecast.hgb (sama dengan M3; tidak ada angka analisis baru). Target biner naik/turun; baris
latih dengan y = 0 (harga tidak berubah) dibuang karena kelas "tetap" butuh ambang yang tidak ada di praregistrasi.
Keluaran = probabilitas naik (`p_up`).

Varian tuned (D-145, juga eksploratif): C1t = C1 + fitur dinamika harga (`features.price_dynamics`, kelompok terpilih) dengan
hyperparameter HGB dari Optuna pada origin pengembangan (target ≤ 2023); C2t = C1t + fx (ablation kurs). Konstanta TUNED_HGB
dibekukan dari eksperimen itu (bukan `params.yaml`, yang beku sejak G6); laporan `docs/audit/20261124_task4_optimasi_arah.md`.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from kagami.features import price_dynamics
from kagami.features.forecast import FEATURE_GROUPS, feature_table, origins, split_origin
from kagami.models.forecasting import _codes
from kagami.utils.config import Config

CLASSIFIERS = {"C1": ("base", "id"), "C2": ("base", "fx", "id")}
TUNED_CLASSIFIERS = {"C1t": ("base", "id"), "C2t": ("base", "fx", "id")}   # + price_dynamics.SELECTED_GROUPS
TUNED_HGB = {"learning_rate": 0.028084987257103646, "max_iter": 250, "max_leaf_nodes": 23, "min_samples_leaf": 319,
             "l2_regularization": 3.8547243967604845, "max_features": 0.3348578429717507}   # Optuna trial 39 (D-145)


def fit_predict_proba(cfg: Config, model: str, train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    """D-141. Probabilitas naik untuk baris test. Latih pada baris train dengan y ≠ 0; kategori (commodity, region) sebagai
    fitur kategori HGB; kolom yang kosong total di train dibuang. Train satu kelas → probabilitas konstan kelas itu."""
    if model not in CLASSIFIERS:
        raise ValueError(f"klasifier tidak dikenal: {model}")
    cols = [c for g in CLASSIFIERS[model] for c in FEATURE_GROUPS[g]]
    cats = [c for c in cols if c in FEATURE_GROUPS["id"]]
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    num = [c for c in cols if c not in cats and tr[c].notna().any()]
    up = (tr["y"] > 0).to_numpy()
    if len(tr) == 0 or up.all() or (~up).all():
        return pd.Series(float(up.mean()) if len(tr) else 0.5, index=test.index)
    p = cfg.params["forecast"]["hgb"]
    Xtr = np.column_stack([tr[num].astype(float).to_numpy(), _codes(cfg, tr, cats)])
    Xte = np.column_stack([test[num].astype(float).to_numpy(), _codes(cfg, test, cats)])
    m = HistGradientBoostingClassifier(max_iter=int(p["max_iter"]), learning_rate=float(p["learning_rate"]),
                                       max_leaf_nodes=int(p["max_leaf_nodes"]),
                                       categorical_features=[False] * len(num) + [True] * len(cats),
                                       random_state=cfg.seed)
    m.fit(Xtr, up)
    return pd.Series(m.predict_proba(Xte)[:, list(m.classes_).index(True)], index=test.index)


def rolling_direction(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                      done: pd.DataFrame | None = None,
                      checkpoint: Callable[[pd.DataFrame], None] | None = None,
                      checkpoint_every: int = 10) -> pd.DataFrame:
    """D-141. Loop horizon × origin (sama dengan `forecasting.rolling_predictions`) × klasifier → origin, horizon, model,
    province_id|region, commodity, y_true, p_up, large_move. `done`/`checkpoint` seperti Task 4 (lanjut dari run sebelumnya)."""
    p = cfg.params["forecast"]
    horizons = [int(h) for h in p["horizons"]]
    table = feature_table(cfg, panel, drivers, world, horizons)
    key = "province_id" if "province_id" in table else None
    keep = ([key] if key else []) + ["region", "commodity"]
    cols = ["origin", "horizon", "model"] + keep + ["y_true", "p_up", "large_move"]
    out = [done[cols]] if done is not None and len(done) else []
    finished = set(zip(done["horizon"], done["origin"])) if done is not None and len(done) else set()
    n_new = 0
    for h in horizons:
        for o in origins(cfg, table["week"].drop_duplicates(), h):
            if (h, o) in finished:
                continue
            train, test = split_origin(cfg, table, o, h)
            if train.empty or test.empty:
                continue
            thr = np.nanpercentile(train["de_4"].abs(), p["large_move_pct"])
            base = test[keep].assign(origin=o, horizon=h, y_true=test["y"], large_move=test["de_4"].abs() > thr)
            for m in CLASSIFIERS:
                out.append(base.assign(model=m, p_up=fit_predict_proba(cfg, m, train, test).to_numpy()))
            print(f"[task4-arah] h={h} origin={o.date()} train={len(train)} test={len(test)}")
            n_new += 1
            if checkpoint is not None and n_new % checkpoint_every == 0:
                checkpoint(pd.concat(out, ignore_index=True)[cols])
    return pd.concat(out, ignore_index=True)[cols] if out else pd.DataFrame(columns=cols)


def tuned_columns(model: str, horizon: int) -> tuple[list[str], list[str]]:
    """D-145. (kolom numerik, kolom kategori) klasifier tuned untuk satu horizon, dengan urutan tetap."""
    if model not in TUNED_CLASSIFIERS:
        raise ValueError(f"klasifier tuned tidak dikenal: {model}")
    groups = TUNED_CLASSIFIERS[model]
    num = [c for g in groups if g != "id" for c in FEATURE_GROUPS[g]]
    num += price_dynamics.group_columns(price_dynamics.SELECTED_GROUPS, horizon)
    return num, list(FEATURE_GROUPS["id"])


def fit_predict_proba_tuned(cfg: Config, model: str, train: pd.DataFrame, test: pd.DataFrame,
                            horizon: int) -> pd.Series:
    """D-145. Probabilitas naik dari HGB dengan TUNED_HGB pada kolom `tuned_columns`. Baris latih y = 0 dibuang;
    kolom kosong total di train dibuang; train satu kelas → probabilitas konstan (sama dengan `fit_predict_proba`)."""
    cols, cats = tuned_columns(model, horizon)
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    num = [c for c in cols if tr[c].notna().any()]
    up = (tr["y"] > 0).to_numpy()
    if len(tr) == 0 or up.all() or (~up).all():
        return pd.Series(float(up.mean()) if len(tr) else 0.5, index=test.index)
    Xtr = np.column_stack([tr[num].astype(float).to_numpy(), _codes(cfg, tr, cats)])
    Xte = np.column_stack([test[num].astype(float).to_numpy(), _codes(cfg, test, cats)])
    m = HistGradientBoostingClassifier(**TUNED_HGB, categorical_features=[False] * len(num) + [True] * len(cats),
                                       random_state=cfg.seed)
    m.fit(Xtr, up)
    return pd.Series(m.predict_proba(Xte)[:, list(m.classes_).index(True)], index=test.index)


def rolling_direction_tuned(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                            models: list[str] | None = None, done: pd.DataFrame | None = None,
                            checkpoint: Callable[[pd.DataFrame], None] | None = None,
                            checkpoint_every: int = 10) -> pd.DataFrame:
    """D-145. Seperti `rolling_direction` (origin, split t + h ≤ origin, kolom keluaran sama) untuk C1t/C2t pada
    `feature_table` + `price_dynamics.extend_table`. Pasangan (model, horizon, origin) di `done` dilewati."""
    p = cfg.params["forecast"]
    horizons = [int(h) for h in p["horizons"]]
    models = list(models or TUNED_CLASSIFIERS)
    table = price_dynamics.extend_table(feature_table(cfg, panel, drivers, world, horizons), panel, horizons)
    key = "province_id" if "province_id" in table else None
    keep = ([key] if key else []) + ["region", "commodity"]
    cols = ["origin", "horizon", "model"] + keep + ["y_true", "p_up", "large_move"]
    out = [done[cols]] if done is not None and len(done) else []
    finished = set(zip(done["model"], done["horizon"], done["origin"])) if done is not None and len(done) else set()
    n_new = 0
    for h in horizons:
        for o in origins(cfg, table["week"].drop_duplicates(), h):
            todo = [m for m in models if (m, h, o) not in finished]
            if not todo:
                continue
            train, test = split_origin(cfg, table, o, h)
            if train.empty or test.empty:
                continue
            thr = np.nanpercentile(train["de_4"].abs(), p["large_move_pct"])
            base = test[keep].assign(origin=o, horizon=h, y_true=test["y"], large_move=test["de_4"].abs() > thr)
            for m in todo:
                out.append(base.assign(model=m, p_up=fit_predict_proba_tuned(cfg, m, train, test, h).to_numpy()))
            print(f"[task4-arah-tuned] h={h} origin={o.date()} train={len(train)} test={len(test)}")
            n_new += 1
            if checkpoint is not None and n_new % checkpoint_every == 0:
                checkpoint(pd.concat(out, ignore_index=True)[cols])
    return pd.concat(out, ignore_index=True)[cols] if out else pd.DataFrame(columns=cols)
