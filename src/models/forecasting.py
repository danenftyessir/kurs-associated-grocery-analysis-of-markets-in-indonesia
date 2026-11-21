"""Model M0-M3 (WP-26). docs/METHODS.md §M4."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from kagami.features.forecast import FEATURE_GROUPS, feature_table, origins, split_origin
from kagami.utils.config import Config

MODELS = ("M0", "M1", "M2", "M3")
ABLATION_MODEL = "M2_nofx"        # M2 tanpa kelompok fx (ablation, WP-27)
CV_FOLDS = 3                      # lipatan CV berbasis waktu untuk alpha ridge
GROUPS_OF = {"M1": ("base",), "M2": ("base", "fx"), "M3": ("base", "fx", "id")}


def _columns(model: str, drop_groups: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """(kolom numerik, kolom kategori) untuk sebuah model setelah kelompok `drop_groups` dibuang."""
    groups = [g for g in GROUPS_OF[model] if g not in drop_groups]
    cols = [c for g in groups for c in FEATURE_GROUPS[g]]
    cats = [c for c in cols if c in FEATURE_GROUPS["id"]]
    return [c for c in cols if c not in cats], cats


def _numeric(df: pd.DataFrame, cols: list[str], fill: pd.Series) -> np.ndarray:
    return df[cols].astype(float).fillna(fill).fillna(0.0).to_numpy()


def _ridge_alpha(cfg: Config, X: np.ndarray, y: np.ndarray, weeks: pd.Series, horizon: int) -> float:
    """Alpha ridge dari CV berbasis waktu (ekspansi, jeda `horizon` minggu agar target latih tidak menembus lipatan uji)."""
    alphas = list(cfg.params["forecast"]["ridge_alphas"])
    uw = np.sort(weeks.unique())
    if len(uw) < 4 * CV_FOLDS:
        return alphas[len(alphas) // 2]
    cuts = [uw[int(len(uw) * (0.5 + 0.5 * k / CV_FOLDS))] for k in range(CV_FOLDS)]
    cuts.append(uw[-1] + np.timedelta64(1, "D"))
    gap = np.timedelta64(7 * horizon, "D")
    wk = weeks.to_numpy()
    scores = dict.fromkeys(alphas, 0.0)
    for k in range(CV_FOLDS):
        tr, va = wk <= cuts[k] - gap, (wk > cuts[k]) & (wk <= cuts[k + 1])
        if tr.sum() < 10 or va.sum() < 1:
            continue
        sc = StandardScaler().fit(X[tr])
        for a in alphas:
            m = Ridge(alpha=a).fit(sc.transform(X[tr]), y[tr])
            scores[a] += float(np.mean((m.predict(sc.transform(X[va])) - y[va]) ** 2))
    return min(scores, key=scores.get) if any(scores.values()) else alphas[len(alphas) // 2]


def _codes(cfg: Config, df: pd.DataFrame, cats: list[str]) -> np.ndarray:
    """Kode bilangan bulat tetap untuk kategori (urutan commodities.yaml / wilayah crosswalk); tak dikenal = -1 -> NaN."""
    levels = {"commodity": list(cfg.commodities), "region": list(dict.fromkeys(cfg.regions["region"]))}
    out = np.column_stack([df[c].map({v: i for i, v in enumerate(levels[c])}).to_numpy(dtype=float) for c in cats])
    return out


def fit_predict(cfg: Config, model: str, train: pd.DataFrame, test: pd.DataFrame,
                drop_groups: tuple[str, ...] = ()) -> pd.Series:
    """WP-26. Prediksi target untuk baris test.

    M0: nol (naive tanpa perubahan). M1: Ridge (alpha dipilih CV berbasis waktu di train) dengan FEATURE_GROUPS
    'base'. M2: M1 + 'fx'. M3: HistGradientBoostingRegressor (params.forecast.hgb, random_state=cfg.seed) dengan
    M2 + 'id' (kategori). drop_groups dipakai ablation (hapus 'fx'). Nilai fitur kosong diisi median latih (ridge)
    atau ditangani HGB langsung.
    """
    if model == "M0":
        return pd.Series(0.0, index=test.index)
    if model not in GROUPS_OF:
        raise ValueError(f"model tidak dikenal: {model}")
    num, cats = _columns(model, tuple(drop_groups))
    num = [c for c in num if train[c].notna().any()]     # kolom kosong total di train: tak informatif, HGB error
    med = train[num].astype(float).median()
    y = train["y"].to_numpy(dtype=float)
    if model == "M3":
        p = cfg.params["forecast"]["hgb"]
        Xtr = np.column_stack([train[num].astype(float).to_numpy(), _codes(cfg, train, cats)])
        Xte = np.column_stack([test[num].astype(float).to_numpy(), _codes(cfg, test, cats)])
        mask = [False] * len(num) + [True] * len(cats)
        m = HistGradientBoostingRegressor(max_iter=int(p["max_iter"]), learning_rate=float(p["learning_rate"]),
                                          max_leaf_nodes=int(p["max_leaf_nodes"]),
                                          categorical_features=mask if cats else None, random_state=cfg.seed)
        return pd.Series(m.fit(Xtr, y).predict(Xte), index=test.index)
    Xtr, Xte = _numeric(train, num, med), _numeric(test, num, med)
    alpha = _ridge_alpha(cfg, Xtr, y, train["week"], int(train["horizon"].iloc[0]))
    sc = StandardScaler().fit(Xtr)
    m = Ridge(alpha=alpha).fit(sc.transform(Xtr), y)
    return pd.Series(m.predict(sc.transform(Xte)), index=test.index)


def rolling_predictions(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                        world: pd.DataFrame, include_m3: bool | None = None, done: pd.DataFrame | None = None,
                        checkpoint: Callable[[pd.DataFrame], None] | None = None,
                        checkpoint_every: int = 10) -> pd.DataFrame:
    """WP-26. Loop horizon x origin (features.forecast.origins) x model (+ M2 tanpa fx untuk ablation);
    data per origin dari features.forecast.build_features.

    -> origin, horizon, model, province_id|region, commodity, y_true, y_pred, large_move (|Δe 4 mgg| > p80 train).
    Disimpan di data/interim/forecast_preds.parquet (bukan artefak kirim; dipakai evaluation).
    M3 dapat dimatikan: include_m3=False atau params.forecast.run_m3 = false (D-014: dipotong terakhir).
    Tahan sesi habis: `done` = prediksi sebelumnya (pasangan horizon x origin yang sudah ada dilewati, hasilnya dipertahankan);
    `checkpoint(preds)` dipanggil tiap `checkpoint_every` origin baru (pipeline menyimpan + push ke Drive).
    """
    p = cfg.params["forecast"]
    include_m3 = bool(p.get("run_m3", True)) if include_m3 is None else include_m3
    horizons = [int(h) for h in p["horizons"]]
    table = feature_table(cfg, panel, drivers, world, horizons)
    models = [m for m in MODELS if include_m3 or m != "M3"] + [ABLATION_MODEL]
    key = "province_id" if "province_id" in table else None
    keep = ([key] if key else []) + ["region", "commodity"]
    cols = ["origin", "horizon", "model"] + keep + ["y_true", "y_pred", "large_move"]
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
            for m in models:
                pred = (fit_predict(cfg, "M2", train, test, drop_groups=("fx",)) if m == ABLATION_MODEL
                        else fit_predict(cfg, m, train, test))
                out.append(base.assign(model=m, y_pred=pred.to_numpy()))
            print(f"[task4] h={h} origin={o.date()} train={len(train)} test={len(test)}")
            n_new += 1
            if checkpoint is not None and n_new % checkpoint_every == 0:
                checkpoint(pd.concat(out, ignore_index=True)[cols])
    return pd.concat(out, ignore_index=True)[cols] if out else pd.DataFrame(columns=cols)
