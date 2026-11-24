"""Evaluasi akhir pada origin test final: metrik lengkap, interval bootstrap blok origin, beda berpasangan vs baseline."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from engine import stats_from  # noqa: E402
from kg import cfg  # noqa: E402
from kagami.stats.meta import bh_fdr  # noqa: E402
from kagami.stats.resampling import moving_block_indices  # noqa: E402

KEY = ["origin", "province_id", "commodity"]
REPS = 1999


def block(h):
    return int(np.ceil(h / int(cfg.params["forecast"]["origin_step_weeks"]))) + 1


def origin_conf(df, thr):
    """Matriks confusion per origin (n_origin × 4) pada baris y ≠ 0."""
    d = df[df["y_true"] != 0]
    up, pu = d["y_true"].to_numpy() > 0, d["score"].to_numpy() > thr
    cells = np.stack([up & pu, up & ~pu, ~up & pu, ~up & ~pu], 1).astype(float)
    uo, inv = np.unique(d["origin"].to_numpy(), return_inverse=True)
    C = np.zeros((len(uo), 4))
    np.add.at(C, inv, cells)
    return uo, C


def full_metrics(df, thr, h, seed=0):
    fin = np.isfinite(df["y_true"]) & np.isfinite(df["score"])
    df = df[fin]
    nz = df["y_true"] != 0
    uo, C = origin_conf(df, thr)
    st = {k: float(v) for k, v in stats_from(C.sum(0)).items()}
    up = df.loc[nz, "y_true"] > 0
    st["roc_auc"] = float(roc_auc_score(up, df.loc[nz, "score"]))
    st["pr_auc"] = float(average_precision_score(up, df.loc[nz, "score"]))
    st["coverage"] = float(nz.sum() / len(df))
    st["n"] = int(nz.sum())
    st["n_origins"] = len(uo)
    st["share_pred_up"] = float((df.loc[nz, "score"] > thr).mean())
    idx = np.vstack([moving_block_indices(len(uo), block(h), np.random.default_rng(seed + r)) for r in range(REPS)])
    boot = stats_from(C[idx].sum(1))
    for k in ("macro_f1", "f1_up", "f1_down", "mcc", "bal_acc"):
        st[f"{k}_lo"], st[f"{k}_hi"] = (float(x) for x in np.nanpercentile(boot[k], [2.5, 97.5]))
    per_origin = stats_from(C)["macro_f1"]
    st["origin_f1_sd"] = float(np.nanstd(per_origin))
    st["origin_f1_q10"], st["origin_f1_q90"] = (float(x) for x in np.nanpercentile(per_origin, [10, 90]))
    return st


def paired_diff(a, b, thr_a, thr_b, h, seed=0):
    """Selisih macro F1 A − B pada baris yang sama (y ≠ 0) + interval & p bootstrap blok origin berpasangan."""
    m = a[KEY + ["y_true", "score"]].merge(b[KEY + ["score"]], on=KEY, suffixes=("_a", "_b"))
    m = m[np.isfinite(m["score_a"]) & np.isfinite(m["score_b"]) & np.isfinite(m["y_true"])]
    ua, Ca = origin_conf(m.rename(columns={"score_a": "score"}), thr_a)
    ub, Cb = origin_conf(m.rename(columns={"score_b": "score"}), thr_b)
    assert (ua == ub).all()
    idx = np.vstack([moving_block_indices(len(ua), block(h), np.random.default_rng(seed + r)) for r in range(REPS)])
    da = stats_from(Ca[idx].sum(1))["macro_f1"] - stats_from(Cb[idx].sum(1))["macro_f1"]
    diff = float(stats_from(Ca.sum(0))["macro_f1"] - stats_from(Cb.sum(0))["macro_f1"])
    lo, hi = np.nanpercentile(da, [2.5, 97.5])
    p = float(min(1.0, 2 * min((da <= 0).mean(), (da >= 0).mean()) + 1 / REPS))
    return {"diff": diff, "lo": float(lo), "hi": float(hi), "p": p, "n": int((m["y_true"] != 0).sum())}


def per_commodity(df, thr):
    out = {}
    for c, g in df[df["y_true"] != 0].groupby("commodity"):
        up, pu = g["y_true"] > 0, g["score"] > thr
        C = np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float)
        out[c] = float(stats_from(C)["macro_f1"])
    return out


def bh(ps):
    return bh_fdr(np.asarray(ps, float))
