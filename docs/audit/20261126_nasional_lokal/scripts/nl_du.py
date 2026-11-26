"""D-158 layar DU Ide B (origin pengembangan): apakah lapisan nasional walk-forward memprediksi arah nasional lebih baik dari yang
sudah tersirat di C1-tuned? Label nasional z = 1[share_up > 0,5] per komoditas × origin (realisasi). Pembanding ex-ante: rerata p_up C1t
lintas provinsi (C1t tersirat), breadth Δp 4 minggu provinsi (`br_up_4`), tanda Δp 4 minggu nasional, laju-dasar. Bootstrap blok origin.
Plus korelasi residual C1t dengan nat_hat (mentah & parsial terhadap rerata p_up C1t per komoditas × origin). → hasil/nl_du.csv."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import AUD, EXP, H, block, moving_block_indices, np, official_c1t, pd, table  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

nl = table("nl")
P = official_c1t("dev")
rows = []
for h in H:
    nt = pd.read_parquet(os.path.join(EXP, f"nat_h{h}.parquet"))
    p = P[P["horizon"] == h]
    imp = p.groupby(["commodity", "origin"])["score"].mean().rename("c1t_nat").reset_index()
    d = imp.merge(nt.rename(columns={"week": "origin"})[["commodity", "origin", "share_up", "n_valid", f"nat_hat_h{h}", "br_up_4", "m_nat_dp_4"]],
                  on=["commodity", "origin"])
    d = d[d["n_valid"] >= 10].dropna(subset=[f"nat_hat_h{h}"])
    d["z"] = (d["share_up"] > 0.5).astype(int)
    uo = np.array(sorted(d["origin"].unique()))
    idx = np.vstack([moving_block_indices(len(uo), block(h), np.random.default_rng(r)) for r in range(999)])
    pos = {o: np.where(d["origin"].to_numpy() == o)[0] for o in uo}
    scores = {"nat_hat": d[f"nat_hat_h{h}"], "c1t_tersirat": d["c1t_nat"], "breadth_4": d["br_up_4"], "nat_dp_4": d["m_nat_dp_4"]}
    for name, s in scores.items():
        auc = roc_auc_score(d["z"], s)
        acc = ((s > (0.5 if name != "nat_dp_4" else 0)).astype(int) == d["z"]).mean()
        bs = []
        for b in idx:
            ii = np.concatenate([pos[uo[k]] for k in b])
            zz, ss = d["z"].to_numpy()[ii], np.asarray(s)[ii]
            if zz.min() != zz.max():
                bs.append(roc_auc_score(zz, ss))
        rows.append({"horizon": h, "kind": "arah_nasional", "measure": name, "auc": auc, "auc_lo": np.percentile(bs, 2.5),
                     "auc_hi": np.percentile(bs, 97.5), "acc": acc, "n": len(d), "base_rate_up": d["z"].mean()})
    # selisih AUC berpasangan nat_hat − c1t_tersirat
    diffs = []
    for b in idx:
        ii = np.concatenate([pos[uo[k]] for k in b])
        zz = d["z"].to_numpy()[ii]
        if zz.min() != zz.max():
            diffs.append(roc_auc_score(zz, d[f"nat_hat_h{h}"].to_numpy()[ii]) - roc_auc_score(zz, d["c1t_nat"].to_numpy()[ii]))
    rows.append({"horizon": h, "kind": "arah_nasional", "measure": "selisih_auc_nat_hat_vs_c1t",
                 "auc": roc_auc_score(d["z"], d[f"nat_hat_h{h}"]) - roc_auc_score(d["z"], d["c1t_nat"]),
                 "auc_lo": np.percentile(diffs, 2.5), "auc_hi": np.percentile(diffs, 97.5)})
    # residual tingkat baris
    q = p[p["y_true"] != 0].merge(imp, on=["commodity", "origin"]).merge(
        nl[["week", "province_id", "commodity", f"nat_hat_h{h}", f"follow_h{h}"]].rename(columns={"week": "origin"}),
        on=["origin", "province_id", "commodity"])
    q["r"] = (q["y_true"] > 0).astype(float) - q["score"]
    q["nat_hat_par"] = q[f"nat_hat_h{h}"] - q["c1t_nat"]
    for c, lab in ((f"nat_hat_h{h}", "nat_hat"), ("nat_hat_par", "nat_hat − c1t_tersirat"), (f"follow_h{h}", "follow")):
        rows.append({"horizon": h, "kind": "residual_baris", "measure": lab, **screen(q, c, h)})
t = pd.DataFrame(rows)
t.round(4).to_csv(os.path.join(HERE, "..", "hasil", "nl_du.csv"), index=False)
pd.set_option("display.width", 200)
print(t.round(4).to_string(index=False))
