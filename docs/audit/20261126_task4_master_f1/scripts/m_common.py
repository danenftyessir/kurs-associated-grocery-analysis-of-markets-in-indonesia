"""Bersama untuk audit & optimasi macro F1 Task 4 (D-156): path, cfg, tabel, origin, metrik.

EXP = folder tabel kerja besar (env KAGAMI_EXP; default scratchpad sesi). Tabel `base.parquet` = tabel resmi C1-tuned
(`feature_table` + `price_dynamics.extend_table`) + kolom kualitas label D-147 (dibangun `20261125_task4_audit_preprocessing/scripts/prep.py`).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))
os.environ.setdefault("KAGAMI_EXP", r"C:\Users\HYPERS~1\AppData\Local\Temp\claude\8d5bcb5a92202b85\4965e7d3-e55e-4722-a505-195187c99f2c\scratchpad\exp")
EXP = os.environ["KAGAMI_EXP"]
for d in ("20261124_task4_optimasi_arah", "20261125_task4_audit_preprocessing"):
    p = os.path.join(AUD, d, "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from kg import cfg  # noqa: E402,F401  (os.chdir ke root project + alias paket kagami)
from evalx import REPS, block, origin_conf  # noqa: E402,F401
from engine import stats_from  # noqa: E402
from kagami.features.forecast import origins  # noqa: E402
from kagami.stats.meta import bh_fdr  # noqa: E402,F401
from kagami.stats.resampling import moving_block_indices  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
DEV_END, TEST_START = pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-01")
H = (4, 8)
KEYS = ["province_id", "commodity", "week"]
REGULATED = ("beras", "daging_sapi", "gula_pasir", "minyak_goreng")   # carry_forward ≥ 50% (D-140)
_T = {}


def table(name="base"):
    if name not in _T:
        _T[name] = pd.read_parquet(os.path.join(EXP, f"{name}.parquet"))
    return _T[name]


def dev_origins(h, weeks=None):
    w = table()["week"].drop_duplicates() if weeks is None else weeks
    return [o for o in origins(cfg, w, h) if o + pd.Timedelta(weeks=h) <= DEV_END]


def official_c1t(part="dev"):
    """Prediksi resmi C1t (`direction_tuned_preds`) → origin, horizon, province_id, commodity, y_true, score."""
    from kagami.utils.io import read_artifact
    d = read_artifact(cfg, "direction_tuned_preds")
    d = d[d["model"] == "C1t"].rename(columns={"p_up": "score"})
    d = d[np.isfinite(d["y_true"])]
    if part == "dev":
        d = d[d["origin"] + pd.to_timedelta(d["horizon"] * 7, unit="D") <= DEV_END]
    elif part == "test":
        raise SystemExit("test 2024+ tidak dibuka di D-156 kecuali lewat aturan PROTOKOL §6")
    return d[["origin", "horizon", "province_id", "commodity", "y_true", "score"]].reset_index(drop=True)


def conf(y, s, thr=0.5):
    """Confusion [TP, FN, FP, TN] pada baris y ≠ 0 (naik = positif)."""
    y, s = np.asarray(y, float), np.asarray(s, float)
    m = (y != 0) & np.isfinite(y) & np.isfinite(s)
    up, pu = y[m] > 0, s[m] > thr
    return np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float)


def mf1(y, s, thr=0.5):
    return float(stats_from(conf(y, s, thr))["macro_f1"])


def boot_ci(df, h, stat="macro_f1", thr=0.5, seed=0, reps=REPS):
    """Interval bootstrap blok origin untuk statistik confusion (baris y ≠ 0)."""
    d = df[df["y_true"] != 0]
    if d.empty:
        return np.nan, np.nan
    uo, C = origin_conf(d, thr)
    idx = np.vstack([moving_block_indices(len(uo), block(h), np.random.default_rng(seed + r)) for r in range(reps)])
    b = stats_from(C[idx].sum(1))[stat]
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    return float(lo), float(hi)


def summary(df, h, thr=0.5, ci=True):
    """Metrik lengkap satu set prediksi (kolom y_true, score, origin)."""
    d = df[np.isfinite(df["y_true"]) & np.isfinite(df["score"])]
    nz = d[d["y_true"] != 0]
    C = conf(nz["y_true"], nz["score"], thr)
    st = {k: float(v) for k, v in stats_from(C).items()}
    st.update({"tp": C[0], "fn": C[1], "fp": C[2], "tn": C[3], "n": int(len(nz)), "n_origins": int(nz["origin"].nunique()),
               "share_up_true": float((nz["y_true"] > 0).mean()), "share_up_pred": float((nz["score"] > thr).mean())})
    if len(nz) and nz["y_true"].gt(0).nunique() == 2:
        from sklearn.metrics import roc_auc_score
        st["roc_auc"] = float(roc_auc_score(nz["y_true"] > 0, nz["score"]))
    per_o = nz.groupby("origin").apply(lambda g: mf1(g["y_true"], g["score"], thr), include_groups=False)
    st["origin_f1_mean"], st["origin_f1_sd"] = float(per_o.mean()), float(per_o.std())
    if ci:
        st["macro_f1_lo"], st["macro_f1_hi"] = boot_ci(d, h, "macro_f1", thr)
    return st
