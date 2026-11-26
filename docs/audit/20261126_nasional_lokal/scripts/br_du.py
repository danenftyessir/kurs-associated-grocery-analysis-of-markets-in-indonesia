"""D-158 layar DU Ide A (breadth kota), origin pengembangan.

(1) Baris provinsi: korelasi residual C1t resmi (r = 1[y > 0] − p) dengan kb_* / kp_*, mentah & parsial (per komoditas terhadap nat_dp_1,
    nat_dp_4, lag_dp_4, dev_ma13), bootstrap blok origin, q BH per keluarga × horizon.
(2) Arah nasional (komoditas × minggu, z = 1[share_up > 0,5]): AUC konsensus C1t (rerata p_up OOF mingguan) vs koreksi increment-only
    σ(L + γ·breadth) walk-forward (refit 4 minggu, ≥ 52 minggu) vs lapisan nasional HGB tanpa/dengan breadth (nat_hat, nat_hat_br);
    mingguan 2021-01 .. 2023-12 dan pada origin dev; bootstrap blok minggu untuk selisih AUC (increment − konsensus).
→ hasil/br_du_rows.csv, hasil/br_du_national.csv
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import AUD, EXP, H, bh_fdr, dev_origins, np, official_c1t, pd, table  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
import meta_build as MB  # noqa: E402

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
KB = ["kb_up_1", "kb_up_4", "kb_down_4", "kb_accel", "kb_med_4", "kb_p90_4", "kb_disp_4", "kb_persist", "kb_cov"]
KP = ["kp_up_4", "kp_disp_4", "kp_n", "kp_rel_up_4"]
CTRL = ["nat_dp_1", "nat_dp_4", "lag_dp_4", "dev_ma13"]
br = table("br")
P = official_c1t("dev")
P = P[P["y_true"] != 0].copy()
P["r"] = (P["y_true"] > 0).astype(float) - P["score"]
D = P.merge(br[["week", "province_id", "commodity"] + KB + KP + CTRL + ["iw_gap"]].rename(columns={"week": "origin"}),
            on=["origin", "province_id", "commodity"], how="left")


def partial(d, x):
    out = pd.Series(np.nan, index=d.index)
    for _, g in d.groupby("commodity"):
        g = g.dropna(subset=[x] + CTRL)
        if len(g) < 50 or g[x].std() == 0:
            continue
        X = np.column_stack([np.ones(len(g)), g[CTRL].to_numpy(float)])
        b, *_ = np.linalg.lstsq(X, g[x].to_numpy(float), rcond=None)
        out.loc[g.index] = g[x].to_numpy(float) - X @ b
    return out


rows = []
for h in H:
    d = D[D["horizon"] == h].copy()
    rows.append({"horizon": h, "family": "kontrol+", "feature": "iw_gap", "kind": "mentah", **screen(d, "iw_gap", h)})
    for fam, cols in (("KB", KB), ("KP", KP)):
        for c in cols:
            rows.append({"horizon": h, "family": fam, "feature": c, "kind": "mentah", **screen(d, c, h)})
            d[f"{c}__p"] = partial(d, c)
            rows.append({"horizon": h, "family": fam, "feature": c, "kind": "parsial", **screen(d, f"{c}__p", h)})
t = pd.DataFrame(rows)
t["q_bh"] = np.nan
for (h, fam, kind), g in t[t["family"] != "kontrol+"].groupby(["horizon", "family", "kind"]):
    ok = g["p"].notna()
    t.loc[g.index[ok], "q_bh"] = bh_fdr(g.loc[ok, "p"].to_numpy())
t.round(4).to_csv(os.path.join(OUT, "br_du_rows.csv"), index=False)

# (2) arah nasional
kb = pd.read_parquet(os.path.join(EXP, "kb_national.parquet"))
nat_rows = []
for h in H:
    nt = MB.national(h, kb)
    cols = MB.KBF
    X = nt[cols].to_numpy(float)
    wk, weeks = nt["week"].to_numpy(), np.array(sorted(nt["week"].unique()))
    ok = np.isfinite(X).all(1) & nt["z"].notna().to_numpy()
    out = np.full(len(nt), np.nan)
    for i in range(0, len(weeks), 4):
        r = weeks[i]
        trm = ok & (wk + np.timedelta64(7 * h, "D") <= r)
        if np.unique(wk[trm]).size < 52:
            continue
        mu, sd = X[trm].mean(0), X[trm].std(0)
        Z = (X - mu) / np.where(sd > 0, sd, 1)
        b = MB.fit_offset_logit(Z[trm], nt["z"].to_numpy()[trm], nt["L"].to_numpy()[trm])
        nxt = weeks[i + 4] if i + 4 < len(weeks) else weeks[-1] + np.timedelta64(7, "D")
        pm = np.isfinite(X).all(1) & (wk >= r) & (wk < nxt)
        out[pm] = 1 / (1 + np.exp(-(nt["L"].to_numpy()[pm] + Z[pm] @ b)))
    nt["q_inc_br"] = out
    hb = pd.read_parquet(os.path.join(EXP, f"natbr_h{h}.parquet"))[["commodity", "week", f"nat_hat_br_h{h}"]]
    hn = pd.read_parquet(os.path.join(EXP, f"nat_h{h}.parquet"))[["commodity", "week", f"nat_hat_h{h}"]]
    nt = nt.merge(hb, on=["commodity", "week"], how="left").merge(hn, on=["commodity", "week"], how="left")
    nt.to_parquet(os.path.join(EXP, f"br_national_h{h}.parquet"))
    q = nt[nt["z"].notna() & nt["q_inc_br"].notna() & nt[f"nat_hat_br_h{h}"].notna() & (nt["week"] >= pd.Timestamp("2021-01-04"))
           & (nt["week"] + pd.Timedelta(weeks=h) <= pd.Timestamp("2023-12-31"))]
    for scope, qq in (("mingguan", q), ("origin_dev", q[q["week"].isin(set(dev_origins(h)))])):
        res = {"horizon": h, "scope": scope, "n": len(qq)}
        for c in ("cons", "q_inc_br", f"nat_hat_h{h}", f"nat_hat_br_h{h}"):
            k = c.replace(f"_h{h}", "")
            res[f"auc_{k}"] = roc_auc_score(qq["z"], qq[c])
            res[f"acc_{k}"] = float(((qq[c] > 0.5) == (qq["z"] > 0.5)).mean())
        uw = np.array(sorted(qq["week"].unique()))
        pos = {w: np.where(qq["week"].to_numpy() == w)[0] for w in uw}
        diffs = []
        rng = np.random.default_rng(158)
        blk = 8 if scope == "mingguan" else 2
        for _ in range(999):
            starts = rng.integers(0, len(uw) - blk + 1, int(np.ceil(len(uw) / blk)))
            ii = np.concatenate([pos[uw[s + j]] for s in starts for j in range(blk)])
            zz = qq["z"].to_numpy()[ii]
            if zz.min() != zz.max():
                diffs.append(roc_auc_score(zz, qq["q_inc_br"].to_numpy()[ii]) - roc_auc_score(zz, qq["cons"].to_numpy()[ii]))
        res["d_auc_inc_vs_cons"] = res["auc_q_inc_br"] - res["auc_cons"]
        res["d_auc_lo"], res["d_auc_hi"] = np.percentile(diffs, [2.5, 97.5])
        nat_rows.append(res)
pd.DataFrame(nat_rows).round(4).to_csv(os.path.join(OUT, "br_du_national.csv"), index=False)
pd.set_option("display.width", 250)
print(t[t["kind"] == "parsial"].pivot_table(index=["family", "feature"], columns="horizon", values=["rho", "lo", "hi", "q_bh"]).round(3).to_string())
print(t[t["family"] == "kontrol+"][["horizon", "rho"]].to_string(index=False))
print(pd.DataFrame(nat_rows).round(4).T.to_string())
