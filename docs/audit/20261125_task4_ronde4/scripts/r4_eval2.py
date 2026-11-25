"""D-149 (split 2, pasca-hoc eksploratif): evaluasi fitur sadar-rezim dengan pengembangan = origin + h ≤ 2024-12-31
(r4_dev + r4_dev2x) dan test = origin ≥ 2025-01-01 (r4_test2, hanya varian yang lolos). Aturan buka test sama dengan D-147/D-148.
Argumen: dev | test. Keluaran: hasil/r4s2_*.csv. Diagnostik: beda pada origin dev baru (target terealisasi 2024).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from evalx import bh, full_metrics, paired_diff  # noqa: E402
from p_exp import EXP  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
REGULATED = ["beras", "minyak_goreng", "daging_sapi", "gula_pasir"]
part = sys.argv[1] if len(sys.argv) > 1 else "dev"
if part == "dev":
    preds = pd.concat([pd.read_parquet(os.path.join(EXP, "r4_dev_preds.parquet")),
                       pd.read_parquet(os.path.join(EXP, "r4_dev2x_preds.parquet"))], ignore_index=True)
else:
    preds = pd.read_parquet(os.path.join(EXP, "r4_test2_preds.parquet"))
preds = preds.rename(columns={"p_up": "score"})
preds = preds[np.isfinite(preds["y_true"])]


def excess(x):
    nz = x[x["y_true"] != 0]
    reg = nz[nz["commodity"].isin(REGULATED)]
    return float((reg["score"] > 0.5).mean() - (reg["y_true"] > 0).mean())


rows, pairs, diag = [], [], []
for h in (4, 8):
    ph = preds[preds["horizon"] == h]
    b = ph[ph["variant"] == "base"]
    new = ph["origin"] + pd.Timedelta(weeks=h) > pd.Timestamp("2023-12-31")
    for v, x in ph.groupby("variant"):
        st = full_metrics(x, 0.5, h)
        rows.append({"variant": v, "horizon": h, **{k: st[k] for k in ("macro_f1", "macro_f1_lo", "macro_f1_hi", "f1_up", "f1_down", "mcc", "rec_up", "rec_down", "share_pred_up", "n_origins")},
                     "excess_up_regulated": excess(x)})
        if v != "base":
            pairs.append({"variant": v, "horizon": h, **paired_diff(x, b, 0.5, 0.5, h)})
            if part == "dev":
                xn, bn = x[new.loc[x.index]], b[new.loc[b.index]]
                diag.append({"variant": v, "horizon": h, **paired_diff(xn, bn, 0.5, 0.5, h),
                             "excess_up_regulated": excess(xn), "excess_up_regulated_base": excess(bn)})
met, pr = pd.DataFrame(rows), pd.DataFrame(pairs)
pd.set_option("display.width", 250)
met.round(4).to_csv(os.path.join(OUT, f"r4s2_{part}_metrics.csv"), index=False)
if part == "test":
    pr["q_bh"] = bh(pr["p"].to_numpy())
pr.round(4).to_csv(os.path.join(OUT, f"r4s2_{part}_paired.csv"), index=False)
print(met.round(3).to_string(index=False))
print(pr.round(4).to_string(index=False))
if part == "dev":
    dg = pd.DataFrame(diag)
    dg.round(4).to_csv(os.path.join(OUT, "r4s2_dev2024_diag.csv"), index=False)
    print("diagnostik origin dev baru (target terealisasi 2024):")
    print(dg.round(4).to_string(index=False))
    piv = pr.pivot(index="variant", columns="horizon", values=["diff", "lo"])
    ad = pd.DataFrame({"mean_diff": (piv[("diff", 4)] + piv[("diff", 8)]) / 2})
    ad["open_test"] = ((ad["mean_diff"] >= 0.005) & ((piv[("lo", 4)] > 0) | (piv[("lo", 8)] > 0))
                       & (piv[[("diff", 4), ("diff", 8)]].min(axis=1) >= 0))
    ad.round(4).to_csv(os.path.join(OUT, "r4s2_dev_adoption.csv"))
    print(ad.round(4).to_string())
