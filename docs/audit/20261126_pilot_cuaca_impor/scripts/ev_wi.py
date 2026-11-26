"""D-157: evaluasi W_NAT / W_LOC / IMP vs base (PROTOKOL §3) di origin pengembangan; keseluruhan + kelompok sasaran.
Keluaran hasil/ev_metrics.csv, ev_decision.csv, ev_per_commodity.csv."""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, H, bh_fdr, np, official_c1t, pd  # noqa: E402
from e_eval import compare  # noqa: E402
import feats_wi as F  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
R = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(EXP, "d157", "*.parquet")))], ignore_index=True)
R = R[np.isfinite(R["y_true"])]
off = official_c1t("dev")
chk = R[R["variant"] == "base"].merge(off, on=["origin", "horizon", "province_id", "commodity"], suffixes=("", "_off"))
print(f"cek base vs resmi: {len(chk)} / {len(off)} baris, maks |Δp| {np.abs(chk['score'] - chk['score_off']).max():.2e}")
assert len(chk) == len(off) and np.abs(chk["score"] - chk["score_off"]).max() == 0
TARGET = {"W_NAT": list(F.HORTI), "W_LOC": list(F.HORTI), "IMP": list(F.BASKET)}
rows, pcs = [], []
for h in H:
    Rh = R[R["horizon"] == h]
    b = Rh[Rh["variant"] == "base"]
    for v in ("W_NAT", "W_LOC", "IMP"):
        x = Rh[Rh["variant"] == v]
        r, pcd = compare(x, b, h)
        rows.append({"variant": v, "horizon": h, "scope": "semua", **r})
        pcs += [{"variant": v, "horizon": h, "commodity": c, "diff": d} for c, d in pcd.items()]
        xs, bs = x[x["commodity"].isin(TARGET[v])], b[b["commodity"].isin(TARGET[v])]
        r2, _ = compare(xs, bs, h)
        rows.append({"variant": v, "horizon": h, "scope": "sasaran", **r2})
M = pd.DataFrame(rows)
M["q_bh"] = np.nan
for (h, sc), g in M.groupby(["horizon", "scope"]):
    M.loc[g.index, "q_bh"] = bh_fdr(g["p"].to_numpy())
M.round(4).to_csv(os.path.join(OUT, "ev_metrics.csv"), index=False)
pc = pd.DataFrame(pcs)
pc.round(4).to_csv(os.path.join(OUT, "ev_per_commodity.csv"), index=False)
A = M[M["scope"] == "semua"].pivot(index="variant", columns="horizon")
dec = pd.DataFrame(index=A.index)
dec["d_h4"], dec["d_h8"] = A[("diff", 4)], A[("diff", 8)]
dec["mean_d"] = dec[["d_h4", "d_h8"]].mean(axis=1)
dec["r1"] = (dec["mean_d"] >= 0.005) & ((A[("lo", 4)] > 0) | (A[("lo", 8)] > 0)) & (dec[["d_h4", "d_h8"]].min(axis=1) >= 0)
dec["r2"] = ((A[("lo", 4)] > 0) & (A[("q_bh", 4)] < 0.05)) | ((A[("lo", 8)] > 0) & (A[("q_bh", 8)] < 0.05))
dec["r3"] = (A[("years_nonneg", 4)] >= 2) & (A[("years_nonneg", 8)] >= 2) & (A[("share_origins_pos", 4)] >= 0.5) & (A[("share_origins_pos", 8)] >= 0.5)
w = pc.pivot_table(index=["variant", "commodity"], columns="horizon", values="diff")
bad = ((w[4] < -0.03) & (w[8] < -0.03)).groupby(level=0).any()
dec["r4"] = (A[[("d_f1_up", 4), ("d_f1_up", 8), ("d_f1_down", 4), ("d_f1_down", 8)]].min(axis=1) >= -0.01) & ~bad.reindex(dec.index).fillna(False)
dec["pass_all"] = dec[["r1", "r2", "r3", "r4"]].all(axis=1)
dec["skala_danen"] = pd.cut(dec["mean_d"], [-1, 0.001, 0.005, 0.010, 0.020, 0.030, 1],
                            labels=["≤ 0", "terlalu kecil", "menarik", "layak", "besar", "lompatan"])
dec.round(4).to_csv(os.path.join(OUT, "ev_decision.csv"))
pd.set_option("display.width", 250)
cols = ["variant", "horizon", "scope", "macro_f1", "diff", "lo", "hi", "q_bh", "d_f1_up", "d_f1_down", "d_q1_small", "share_origins_pos",
        "d_2021", "d_2022", "d_2023", "worst_commodity", "worst_commodity_diff"]
print(M[cols].round(4).to_string(index=False))
print(dec.round(4).to_string())
print(pc.pivot_table(index="commodity", columns=["variant", "horizon"], values="diff").round(3).to_string())
