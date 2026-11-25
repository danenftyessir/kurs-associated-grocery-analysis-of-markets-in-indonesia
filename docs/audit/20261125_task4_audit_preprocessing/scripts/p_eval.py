"""Evaluasi eksperimen preprocessing (origin pengembangan) vs `base`: metrik lengkap + beda berpasangan bootstrap blok origin.

Juga per subset label (hanya analisis): kuintil |y| terkecil dan label tidak stabil (flip bootstrap hari ≥ 5%) untuk melihat
apakah varian membantu tepat di tempat kesalahan terkonsentrasi. Aturan buka test: lihat p_exp.py.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from evalx import full_metrics, paired_diff  # noqa: E402
from p_exp import EXP, OUT  # noqa: E402

part = sys.argv[1] if len(sys.argv) > 1 else "dev"
preds = pd.read_parquet(os.path.join(EXP, f"exp_{part}_preds.parquet")).rename(columns={"p_up": "score"})
base_tab = pd.read_parquet(os.path.join(EXP, "base.parquet"), columns=["week", "province_id", "commodity", "flip_4", "flip_8"])
q = []
for h in (4, 8):
    f = base_tab.rename(columns={"week": "origin", f"flip_{h}": "flip"})[["origin", "province_id", "commodity", "flip"]]
    q.append(f.assign(horizon=h))
preds = preds.merge(pd.concat(q), on=["origin", "province_id", "commodity", "horizon"], how="left")
preds = preds[np.isfinite(preds["y_true"])]
rows, pairs = [], []
for h in (4, 8):
    ph = preds[preds["horizon"] == h]
    b = ph[ph["variant"] == "base"]
    small = b.loc[b["y_true"] != 0, "y_true"].abs()
    small_thr = small.quantile(0.2)
    for v, x in ph.groupby("variant"):
        st = full_metrics(x, 0.5, h)
        nz = x[x["y_true"] != 0]
        sm = nz[nz["y_true"].abs() <= small_thr]
        un = nz[nz["flip"] >= 0.05]
        st.update({"variant": v, "horizon": h,
                   "macro_f1_q1_small": full_metrics(sm.assign(), 0.5, h)["macro_f1"],
                   "macro_f1_unstable": full_metrics(un, 0.5, h)["macro_f1"]})
        rows.append(st)
        if v != "base":
            d = paired_diff(x, b, 0.5, 0.5, h)
            ds = paired_diff(sm, b[b["y_true"].abs() <= small_thr], 0.5, 0.5, h)
            pairs.append({"variant": v, "horizon": h, **d, "diff_q1_small": ds["diff"], "lo_q1_small": ds["lo"],
                          "hi_q1_small": ds["hi"]})
met = pd.DataFrame(rows)
pr = pd.DataFrame(pairs)
met.round(4).to_csv(os.path.join(OUT, f"exp_{part}_metrics.csv"), index=False)
pr.round(4).to_csv(os.path.join(OUT, f"exp_{part}_paired.csv"), index=False)
cols = ["variant", "horizon", "macro_f1", "macro_f1_lo", "macro_f1_hi", "f1_up", "f1_down", "mcc", "share_pred_up",
        "macro_f1_q1_small", "macro_f1_unstable", "n", "n_origins"]
pd.set_option("display.width", 250)
print(met[cols].round(3).to_string(index=False))
print(pr.round(4).to_string(index=False))
if part == "dev":
    piv = pr.pivot(index="variant", columns="horizon", values=["diff", "lo", "hi"])
    adopt = []
    for v in piv.index:
        d4, d8 = piv.loc[v, ("diff", 4)], piv.loc[v, ("diff", 8)]
        pos = [(piv.loc[v, ("lo", h)] > 0) for h in (4, 8)]
        ok = (d4 + d8) / 2 >= 0.005 and any(pos) and min(d4, d8) >= 0
        adopt.append({"variant": v, "mean_diff": (d4 + d8) / 2, "open_test": bool(ok)})
    ad = pd.DataFrame(adopt)
    ad.to_csv(os.path.join(OUT, "exp_dev_adoption.csv"), index=False)
    print(ad.round(4).to_string(index=False))
    with open(os.path.join(OUT, "exp_dev_adoption.json"), "w", encoding="utf-8") as f:
        json.dump(ad.to_dict(orient="records"), f, indent=1, default=float)
