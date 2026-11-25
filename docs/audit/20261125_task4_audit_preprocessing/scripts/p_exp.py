"""Eksperimen preprocessing dengan evaluator TETAP = C1-tuned (fitur `tuned_columns('C1t', h)`, `TUNED_HGB`, seed resmi).

Protokol (ditetapkan sebelum melihat hasil):
- Rolling-origin Task 4 apa adanya (`split_origin`: latih t + h ≤ origin). Hanya origin PENGEMBANGAN (origin + h ≤ 2023-12-31).
- Label evaluasi = label resmi (tanda y = log rerata hari teramati t+h − t; y = 0 dikeluarkan). Tidak ada varian yang
  mengubah baris atau label evaluasi; yang berubah hanya fitur, bobot latih, atau penyaring baris LATIH.
- Pembanding = varian `base` (harus mereproduksi `direction_tuned_preds` C1t persis).
- Aturan buka test: Δ macro F1 rerata (h 4, h 8) ≥ +0,005, interval berpasangan > 0 di ≥ 1 horizon, dan Δ ≥ 0 di horizon lain.
  Bila tidak ada yang lolos, test final tidak dibuka.
Keluaran: hasil/exp_dev_metrics.csv, hasil/exp_dev_paired.csv, EXP_DIR/exp_dev_preds.parquet.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.features.forecast import origins, split_origin  # noqa: E402
from kagami.models.direction import TUNED_HGB, tuned_columns  # noqa: E402
from kagami.models.forecasting import _codes  # noqa: E402

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "hasil")
EXP = os.environ.get("KAGAMI_EXP", r"C:\Users\HYPERS~1\AppData\Local\Temp\claude\92509b33971ecddd\b18f9307-3852-462a-bd0d-67a285eb70b9\scratchpad\exp")
DEV_END = pd.Timestamp("2023-12-31")
CATS = ["commodity", "region"]
H = [4, 8]

# nama → (tabel, kolom tambahan, penyaring latih, bobot)
VARIANTS = {
    "base": ("base", [], None, None),
    "P06_drop_subtick": ("base", [], "ticks>=1", None),
    "P06_drop_lt2ticks": ("base", [], "ticks>=2", None),
    "P06_weight_stability": ("base", [], None, "stability"),
    "P03_train_observed_ends": ("base", [], "observed_ends", None),
    "P04_features_lastday": ("last", [], None, None),
    "P04_intraweek": ("base", ["iw_gap", "n_days"], None, None),
    "P03_no_ffill": ("noffill", ["n_missing_13"], None, None),
    "P08_volnorm": ("volnorm", [], None, None),
    "P09_commodity_balanced": ("base", [], None, "commodity"),
}
_T = {}


def tab(name):
    if name not in _T:
        _T[name] = pd.read_parquet(os.path.join(EXP, f"{name}.parquet"))
    return _T[name]


def fit(train, test, cols, filt, weight, h, seed):
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    n_all = len(tr)
    if filt == "ticks>=1":
        tr = tr[tr[f"ticks_{h}"] >= 1]
    elif filt == "ticks>=2":
        tr = tr[tr[f"ticks_{h}"] >= 2]
    elif filt == "observed_ends":
        tr = tr[(tr["st0"] == "observed") & (tr[f"st_{h}"] == "observed")]
    num = [c for c in cols if tr[c].notna().any()]
    up = (tr["y"] > 0).to_numpy()
    w = None
    if weight == "stability":
        w = np.clip(1 - 2 * tr[f"flip_{h}"].fillna(0).to_numpy(), 0, 1)
    elif weight == "commodity":
        cnt = tr["commodity"].map(tr["commodity"].value_counts()).to_numpy(float)
        w = len(tr) / (tr["commodity"].nunique() * cnt)
    from sklearn.ensemble import HistGradientBoostingClassifier
    Xtr = np.column_stack([tr[num].astype(float).to_numpy(), _codes(cfg, tr, CATS)])
    Xte = np.column_stack([test[num].astype(float).to_numpy(), _codes(cfg, test, CATS)])
    m = HistGradientBoostingClassifier(**TUNED_HGB, categorical_features=[False] * len(num) + [True] * len(CATS),
                                       random_state=seed)
    m.fit(Xtr, up, sample_weight=w)
    return m.predict_proba(Xte)[:, list(m.classes_).index(True)], n_all, len(tr)


def one(h, o, names=None):
    out, meta = [], []
    for name in (names or list(VARIANTS)):
        tname, extra, filt, weight = VARIANTS[name]
        t0 = time.perf_counter()
        train, test = split_origin(cfg, tab(tname), o, h)
        cols = tuned_columns("C1t", h)[0] + extra
        p, n_all, n_used = fit(train, test, cols, filt, weight, h, cfg.seed)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, variant=name,
                                                             y_true=test["y"].to_numpy(), p_up=p))
        meta.append({"origin": o, "horizon": h, "variant": name, "n_train_nonzero": n_all, "n_train_used": n_used,
                     "sec": time.perf_counter() - t0})
    return pd.concat(out, ignore_index=True), pd.DataFrame(meta)


if __name__ == "__main__":
    from joblib import Parallel, delayed
    part = os.environ.get("PART", "dev")           # test hanya untuk varian yang lolos aturan buka test
    only = [v for v in os.environ.get("ONLY", "").split(",") if v]
    names = ["base"] + only if only else list(VARIANTS)
    weeks = tab("base")["week"].drop_duplicates()
    if part == "dev":
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h) if o + pd.Timedelta(weeks=h) <= DEV_END]
    else:
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h) if o >= pd.Timestamp("2024-01-01")]
    print(part, "pekerjaan", len(jobs), "varian", names)
    t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=5)(delayed(one)(h, o, names) for h, o in jobs)
    preds = pd.concat([r[0] for r in res], ignore_index=True)
    meta = pd.concat([r[1] for r in res], ignore_index=True)
    preds.to_parquet(os.path.join(EXP, f"exp_{part}_preds.parquet"))
    meta.to_csv(os.path.join(OUT, f"exp_{part}_meta.csv"), index=False)
    print("selesai", round(time.time() - t0), "dtk")
