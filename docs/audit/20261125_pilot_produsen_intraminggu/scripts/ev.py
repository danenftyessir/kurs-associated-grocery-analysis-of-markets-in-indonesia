"""D-151: evaluasi exp.py vs base sesuai PROTOKOL.md §4.

Argumen: FAM PART (iw|pr, dev|test). Keluaran hasil/<FAM>_<PART>_{metrics,paired,per_commodity}.csv dan (dev) <FAM>_dev_adoption.csv.
- Cek base = `direction_tuned_preds` C1t pada baris yang sama (maks |Δp|).
- Metrik lengkap + Δ macro F1 berpasangan (bootstrap blok origin 1.999) keseluruhan & kuintil |y| terkecil (ambang dari base).
- Aturan buka test: Δ rerata ≥ +0,005, interval > 0 di ≥ 1 horizon, Δ ≥ 0 di horizon lain; satu kandidat per keluarga.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from evalx import bh, full_metrics, paired_diff, per_commodity  # noqa: E402
from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
NOT_CANDIDATE = {"IW_REF"}
NCOLS = {"IW_REF": 2, "IW_FULL": 6, "IW_NAT": 8, "PR_DYN": 5, "PR_TRANS": 10, "PR_ALL": 16}
fam, part = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("iw", "dev")
preds = pd.read_parquet(os.path.join(EXP, f"d151_{fam}_{part}_preds.parquet")).rename(columns={"p_up": "score"})
preds = preds[np.isfinite(preds["y_true"])]

# base harus mereproduksi artefak resmi C1t
off = read_artifact(cfg, "direction_tuned_preds")
off = off[off["model"] == "C1t"][["origin", "horizon", "province_id", "commodity", "p_up"]]
chk = preds[preds["variant"] == "base"].merge(off, on=["origin", "horizon", "province_id", "commodity"], how="inner")
print(f"cek base vs direction_tuned_preds C1t: {len(chk)} baris, maks |Δp| {np.abs(chk['score'] - chk['p_up']).max():.2e}")

rows, pairs, pcs = [], [], []
for h in (4, 8):
    ph = preds[preds["horizon"] == h]
    b = ph[ph["variant"] == "base"]
    thr_small = b.loc[b["y_true"] != 0, "y_true"].abs().quantile(0.2)
    b_sm = b[(b["y_true"] != 0) & (b["y_true"].abs() <= thr_small)]
    pc_base = per_commodity(b, 0.5)
    for v, x in ph.groupby("variant"):
        st = full_metrics(x, 0.5, h)
        nz = x[x["y_true"] != 0]
        sm = nz[nz["y_true"].abs() <= thr_small]
        rows.append({"variant": v, "horizon": h, **{k: st[k] for k in ("macro_f1", "macro_f1_lo", "macro_f1_hi", "f1_up", "f1_down",
                                                                       "mcc", "roc_auc", "share_pred_up", "n", "n_origins")},
                     "macro_f1_q1_small": full_metrics(sm, 0.5, h)["macro_f1"], "n_q1_small": len(sm)})
        if v != "base":
            d = paired_diff(x, b, 0.5, 0.5, h)
            ds = paired_diff(sm, b_sm, 0.5, 0.5, h)
            pairs.append({"variant": v, "horizon": h, **d, "diff_q1_small": ds["diff"], "lo_q1_small": ds["lo"],
                          "hi_q1_small": ds["hi"], "n_q1_small": ds["n"]})
            pcs += [{"variant": v, "horizon": h, "commodity": c, "diff": f - pc_base[c]} for c, f in per_commodity(x, 0.5).items()]
met, pr, pc = pd.DataFrame(rows), pd.DataFrame(pairs), pd.DataFrame(pcs)
if part == "test" and len(pr):
    pr["q_bh"] = bh(pr["p"].to_numpy())
met.round(4).to_csv(os.path.join(OUT, f"{fam}_{part}_metrics.csv"), index=False)
pr.round(4).to_csv(os.path.join(OUT, f"{fam}_{part}_paired.csv"), index=False)
pc.round(4).to_csv(os.path.join(OUT, f"{fam}_{part}_per_commodity.csv"), index=False)
pd.set_option("display.width", 250)
print(met.round(3).to_string(index=False))
print(pr.round(4).to_string(index=False))
print(pc.pivot_table(index="commodity", columns=["variant", "horizon"], values="diff").round(3).to_string())
if part == "dev":
    piv = pr.pivot(index="variant", columns="horizon", values=["diff", "lo", "diff_q1_small"])
    ad = pd.DataFrame({"mean_diff": (piv[("diff", 4)] + piv[("diff", 8)]) / 2})
    ad["pass_rule"] = ((ad["mean_diff"] >= 0.005) & ((piv[("lo", 4)] > 0) | (piv[("lo", 8)] > 0))
                       & (piv[[("diff", 4), ("diff", 8)]].min(axis=1) >= 0))
    ad["candidate"] = ~ad.index.isin(NOT_CANDIDATE)
    ad["flag_small"] = (piv[("diff_q1_small", 4)] < -0.01) & (piv[("diff_q1_small", 8)] < -0.01)
    ad["n_cols"] = [NCOLS[v] for v in ad.index]
    ok = ad[ad["pass_rule"] & ad["candidate"]].sort_values(["mean_diff", "n_cols"], ascending=[False, True])
    ad["open_test"] = ad.index.isin(ok.index[:1])
    ad.round(4).to_csv(os.path.join(OUT, f"{fam}_dev_adoption.csv"))
    print(ad.round(4).to_string())
