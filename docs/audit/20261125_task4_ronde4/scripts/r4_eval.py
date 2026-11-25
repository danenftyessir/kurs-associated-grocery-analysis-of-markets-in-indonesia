"""Evaluasi r4_exp (fitur sadar-rezim) vs base: metrik, beda berpasangan bootstrap blok origin, kelebihan prediksi naik komoditas
diatur, aturan buka test (dev). Argumen: dev | test. Keluaran: hasil/r4_{part}_metrics.csv, r4_{part}_paired.csv, r4_dev_adoption.csv.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from evalx import full_metrics, paired_diff  # noqa: E402
from p_exp import EXP  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
REGULATED = ["beras", "minyak_goreng", "daging_sapi", "gula_pasir"]
part = sys.argv[1] if len(sys.argv) > 1 else "dev"
preds = pd.read_parquet(os.path.join(EXP, f"r4_{part}_preds.parquet")).rename(columns={"p_up": "score"})
preds = preds[np.isfinite(preds["y_true"])]
rows, pairs = [], []
for h in (4, 8):
    ph = preds[preds["horizon"] == h]
    b = ph[ph["variant"] == "base"]
    for v, x in ph.groupby("variant"):
        st = full_metrics(x, 0.5, h)
        nz = x[x["y_true"] != 0]
        reg = nz[nz["commodity"].isin(REGULATED)]
        rows.append({"variant": v, "horizon": h, **{k: st[k] for k in ("macro_f1", "macro_f1_lo", "macro_f1_hi", "f1_up", "f1_down", "mcc", "rec_up", "rec_down", "share_pred_up")},
                     "excess_up_regulated": float((reg["score"] > 0.5).mean() - (reg["y_true"] > 0).mean())})
        if v != "base":
            pairs.append({"variant": v, "horizon": h, **paired_diff(x, b, 0.5, 0.5, h)})
met, pr = pd.DataFrame(rows), pd.DataFrame(pairs)
met.round(4).to_csv(os.path.join(OUT, f"r4_{part}_metrics.csv"), index=False)
pr.round(4).to_csv(os.path.join(OUT, f"r4_{part}_paired.csv"), index=False)
pd.set_option("display.width", 250)
print(met.round(3).to_string(index=False))
print(pr.round(4).to_string(index=False))
if part == "dev":
    piv = pr.pivot(index="variant", columns="horizon", values=["diff", "lo"])
    ad = pd.DataFrame({"mean_diff": (piv[("diff", 4)] + piv[("diff", 8)]) / 2})
    ad["open_test"] = ((ad["mean_diff"] >= 0.005) & ((piv[("lo", 4)] > 0) | (piv[("lo", 8)] > 0))
                       & (piv[[("diff", 4), ("diff", 8)]].min(axis=1) >= 0))
    ad.round(4).to_csv(os.path.join(OUT, "r4_dev_adoption.csv"))
    print(ad.round(4).to_string())
