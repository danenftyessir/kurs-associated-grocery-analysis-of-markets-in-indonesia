"""D-158: evaluasi kandidat vs base (aturan D-156 §5) untuk tahap yang diberikan: `python ev_nl.py nl br` → hasil/ev_<tahap...>_*.csv.
q BH dihitung dalam keluarga semua kandidat tahap yang dievaluasi bersama (iterasi 1: nl + br; iterasi 2: i2)."""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, H, bh_fdr, np, official_c1t, pd  # noqa: E402
from e_eval import compare  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
stages = sys.argv[1:] or ["nl"]
tag = "_".join(stages)
off = official_c1t("dev")
rows, pcs = [], []
for st in stages:
    R = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(EXP, "d158", st, "*.parquet")))], ignore_index=True)
    R = R[np.isfinite(R["y_true"])]
    chk = R[R["variant"] == "base"].merge(off, on=["origin", "horizon", "province_id", "commodity"], suffixes=("", "_off"))
    assert len(chk) == len(off) and np.abs(chk["score"] - chk["score_off"]).max() == 0, st
    for h in H:
        Rh = R[R["horizon"] == h]
        b = Rh[Rh["variant"] == "base"]
        for v in [x for x in Rh["variant"].unique() if x != "base"]:
            r, pcd = compare(Rh[Rh["variant"] == v], b, h)
            rows.append({"stage": st, "variant": v, "horizon": h, **r})
            pcs += [{"variant": v, "horizon": h, "commodity": c, "diff": d} for c, d in pcd.items()]
            print(st, h, v, round(r["diff"], 4), flush=True)
M = pd.DataFrame(rows)
M["q_bh"] = np.nan
for h in H:
    g = M[M["horizon"] == h]
    M.loc[g.index, "q_bh"] = bh_fdr(g["p"].to_numpy())
pc = pd.DataFrame(pcs)
A = M.pivot(index="variant", columns="horizon")
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
M.round(4).to_csv(os.path.join(OUT, f"ev_{tag}_metrics.csv"), index=False)
pc.round(4).to_csv(os.path.join(OUT, f"ev_{tag}_per_commodity.csv"), index=False)
dec.round(4).to_csv(os.path.join(OUT, f"ev_{tag}_decision.csv"))
pd.set_option("display.width", 250)
print(M[["variant", "horizon", "macro_f1", "diff", "lo", "hi", "q_bh", "d_f1_up", "d_f1_down", "d_q1_small", "share_origins_pos",
         "d_2021", "d_2022", "d_2023", "worst_commodity", "worst_commodity_diff"]].round(4).to_string(index=False))
print(dec.round(4).to_string())
print(pc.pivot_table(index="commodity", columns=["variant", "horizon"], values="diff").round(3).to_string())
