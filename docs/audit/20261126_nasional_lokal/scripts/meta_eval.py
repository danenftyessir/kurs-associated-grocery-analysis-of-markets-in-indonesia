"""D-158 iterasi 2: META_FR / META_CITY / META_IW (PROTOKOL_I2 §2) → prediksi origin dev di EXP/d158/i2meta/ (format sama run_nl).

Lapisan nasional: increment-only σ(L + γ·x), γ walk-forward per refit 4 minggu (baris nasional t' + h ≤ r, ≥ 52 minggu). Pergeseran s(c, t) =
γ·x(c, t) out-of-sample. Lapisan provinsi: pada origin dev o, β dari regresi logistik offset logit p_C1t (OOS mingguan) pada baris provinsi
t' + h ≤ o dengan s tersedia; logit p' = logit p + β·s(c, o). Juga menyimpan γ & β per origin (hasil/meta_coef.csv)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import EXP, H, dev_origins, np, official_c1t, pd, table  # noqa: E402
import meta_build as MB  # noqa: E402

XS = {"META_FR": ["kb_iw_med", "kb_iw_up", "iw_gap_nat"], "META_CITY": ["kb_iw_med", "kb_iw_up"], "META_IW": ["iw_gap_nat"]}
OUTD = os.path.join(EXP, "d158", "i2meta")
os.makedirs(OUTD, exist_ok=True)
fr = table("fresh")
natf = fr.groupby(["commodity", "week"])[["kb_iw_med", "kb_iw_up", "iw_gap_nat"]].first().reset_index()
W = pd.read_parquet(os.path.join(EXP, "c1t_weekly.parquet"))
base_lab = table()[["week", "province_id", "commodity", "y_4", "y_8"]]
off = official_c1t("dev")
coefs, outs = [], []
for h in H:
    nt = MB.national(h).merge(natf, on=["commodity", "week"], how="left").reset_index(drop=True)
    wk, weeks = nt["week"].to_numpy(), np.array(sorted(nt["week"].unique()))
    Wh = W[W["horizon"] == h].merge(base_lab[["week", "province_id", "commodity", f"y_{h}"]], on=["week", "province_id", "commodity"])
    Wh = Wh[Wh[f"y_{h}"].notna() & (Wh[f"y_{h}"] != 0)]
    Wh["lp"] = MB.logit(Wh["p_up"])
    Wh["up"] = (Wh[f"y_{h}"] > 0).astype(float)
    P = off[off["horizon"] == h].copy()
    P["lp"] = MB.logit(P["score"])
    for name, cols in XS.items():
        X = nt[cols].to_numpy(float)
        ok = np.isfinite(X).all(1) & nt["z"].notna().to_numpy()
        s = np.full(len(nt), np.nan)
        for i in range(0, len(weeks), 4):
            r = weeks[i]
            trm = ok & (wk + np.timedelta64(7 * h, "D") <= r)
            if np.unique(wk[trm]).size < 52:
                continue
            mu, sd = X[trm].mean(0), X[trm].std(0)
            Z = (X - mu) / np.where(sd > 0, sd, 1)
            g = MB.fit_offset_logit(Z[trm], nt["z"].to_numpy()[trm], nt["L"].to_numpy()[trm])
            nxt = weeks[i + 4] if i + 4 < len(weeks) else weeks[-1] + np.timedelta64(7, "D")
            pm = np.isfinite(X).all(1) & (wk >= r) & (wk < nxt)
            s[pm] = Z[pm] @ g
            coefs.append({"variant": name, "horizon": h, "refit": r, "level": "gamma", **{f"g_{c}": v for c, v in zip(cols, g)}})
        S = nt[["commodity", "week"]].assign(s=s)
        Wv = Wh.merge(S, on=["commodity", "week"], how="inner").dropna(subset=["s"])
        Pv = P.merge(S.rename(columns={"week": "origin"}), on=["commodity", "origin"], how="left")
        Pv["score_new"] = Pv["score"]
        for o in dev_origins(h):
            tr = Wv[Wv["week"] + pd.Timedelta(weeks=h) <= o]
            if tr["week"].nunique() < 26:
                continue
            b = MB.fit_offset_logit(tr[["s"]].to_numpy(float), tr["up"].to_numpy(), tr["lp"].to_numpy())[0]
            m = (Pv["origin"] == o) & Pv["s"].notna()
            Pv.loc[m, "score_new"] = 1 / (1 + np.exp(-(Pv.loc[m, "lp"] + b * Pv.loc[m, "s"])))
            coefs.append({"variant": name, "horizon": h, "refit": o, "level": "beta", "beta": b, "n_rows": len(tr)})
        outs.append(Pv[["origin", "horizon", "province_id", "commodity", "y_true"]].assign(variant=name, score=Pv["score_new"].to_numpy()))
    outs.append(P[["origin", "horizon", "province_id", "commodity", "y_true", "score"]].assign(variant="base"))
R = pd.concat(outs, ignore_index=True)
for (h, o), g in R.groupby(["horizon", "origin"]):
    g.to_parquet(os.path.join(OUTD, f"h{h}_{pd.Timestamp(o).date()}.parquet"))
C = pd.DataFrame(coefs)
C.to_csv(os.path.join(HERE, "..", "hasil", "meta_coef.csv"), index=False)
print(C[C["level"] == "beta"].groupby(["variant", "horizon"])["beta"].describe().round(3).to_string())
print(C[C["level"] == "gamma"].groupby(["variant", "horizon"]).mean(numeric_only=True).round(3).to_string())
