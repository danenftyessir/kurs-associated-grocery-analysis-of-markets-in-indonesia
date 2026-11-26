"""D-162 (U108): bandingkan artefak Task 4 sebelum (flag `episode` periode penuh) vs sesudah (flag real-time).

Argumen: folder cadangan artefak lama (forecast_preds.parquet, forecast_eval.csv, ablation.csv, direction_preds.parquet,
direction_tuned_preds.parquet). Artefak baru dibaca dari lokasi resmi. -> ../hasil/u108_*.csv
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
OLD = sys.argv[1]
KEYS = ["origin", "horizon", "model", "province_id", "commodity"]
DEV_END = pd.Timestamp("2023-12-31")


def macro_f1(y, p):
    m = (y != 0) & np.isfinite(p)
    up, pu = y[m] > 0, p[m] > 0.5
    f = []
    for a, b in ((up, pu), (~up, ~pu)):
        tp, fp, fn = (a & b).sum(), (~a & b).sum(), (a & ~b).sum()
        f.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return float(np.mean(f)), float((up == pu).mean()), int(m.sum())


def keys(d):
    return [k for k in KEYS if k in d.columns]


if __name__ == "__main__":
    rows = []
    # prediksi regresi resmi
    for name, score in (("forecast_preds", "y_pred"), ("direction_preds", "p_up"), ("direction_tuned_preds", "p_up")):
        a = pd.read_parquet(os.path.join(OLD, f"{name}.parquet"))
        b = pd.read_parquet(os.path.join(ROOT, "data", "interim", f"{name}.parquet"))
        k = keys(a) if "province_id" in a else [x for x in KEYS if x != "province_id"] + ["region"]
        m = a.merge(b, on=[x for x in k if x in b.columns], suffixes=("_old", "_new"), how="outer", indicator=True)
        for mod, g in m.groupby("model"):
            both = g[g["_merge"] == "both"]
            diff = (both[f"{score}_old"] - both[f"{score}_new"]).abs()
            r = {"artifact": name, "model": mod, "n_old": int((g["_merge"] != "right_only").sum()),
                 "n_new": int((g["_merge"] != "left_only").sum()), "max_abs_diff": float(diff.max()) if len(diff) else np.nan,
                 "share_changed": float((diff > 1e-12).mean()) if len(diff) else np.nan}
            if score == "p_up":
                for part, sel in (("dev", both["origin"] + pd.to_timedelta(both["horizon"] * 7, unit="D") <= DEV_END),
                                  ("test", both["origin"] >= "2024-01-01")):
                    for h in (4, 8):
                        s = both[sel & (both["horizon"] == h)]
                        y = s["y_true_old"].to_numpy()
                        f_old, acc_old, n = macro_f1(y, s[f"{score}_old"].to_numpy())
                        f_new, acc_new, _ = macro_f1(y, s[f"{score}_new"].to_numpy())
                        r.update({f"f1_{part}_h{h}_old": f_old, f"f1_{part}_h{h}_new": f_new, f"n_{part}_h{h}": n})
            rows.append(r)
    P = pd.DataFrame(rows)
    P.round(6).to_csv(os.path.join(OUT, "u108_preds.csv"), index=False)
    # evaluasi resmi Task 4
    ea = pd.read_csv(os.path.join(OLD, "forecast_eval.csv"))
    eb = pd.read_csv(os.path.join(ROOT, "results", "task4", "forecast_eval.csv"))
    k = ["horizon", "model", "subset", "level", "commodity", "region"]
    E = ea.merge(eb, on=k, suffixes=("_old", "_new"))
    cols = ["mae", "mae_ratio_vs_m1", "dm_p", "h5_p_holm"]
    sel = E[E["model"].isin(["M2", "M3"]) & E["level"].isin(["all", "path"])]
    sel = sel[[*k, "n_origins_new", *[f"{c}_{x}" for c in cols for x in ("old", "new")]]]
    sel.round(5).to_csv(os.path.join(OUT, "u108_forecast_eval.csv"), index=False)
    others = E[E["model"].isin(["M0", "M1", "M2_nofx"])]
    print("selisih maks MAE model tanpa fx (M0/M1/M2_nofx):", float((others["mae_old"] - others["mae_new"]).abs().max()))
    pd.set_option("display.width", 240)
    print(P.round(4).to_string(index=False))
    print(sel.round(4).to_string(index=False))
