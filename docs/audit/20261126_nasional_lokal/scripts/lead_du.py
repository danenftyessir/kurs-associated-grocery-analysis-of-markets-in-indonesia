"""D-158 iterasi 2 — layar DU "kota pemimpin" (leader markets), arah nasional, walk-forward, tanpa label masa depan.

Per komoditas c dan refit r (tiap 4 minggu, ≥ 52 minggu latih t' + h ≤ r): untuk setiap kota, korelasi Δp_4 kota pada minggu t' dengan
galat nasional terealisasi e(t') = share_up(t') − konsensus C1t(t') di data latih; K kota dengan korelasi terbesar (bertanda) → indeks
pemimpin LI(t) = rerata (tanda korelasi × Δp_4 kota terstandar latih) pada K kota itu. Lalu koreksi increment-only gabungan komoditas:
q = σ(L + γ·LI), γ dari regresi logistik dengan offset pada baris latih (indeks latih dihitung dengan pilihan kota refit yang sama — catatan:
pemilihan kota memakai baris latih yang sama dengan γ, sehingga γ in-sample; layar ini memakai prediksi out-of-sample minggu [r, r + 4)).
K ∈ {5, 10, 20}. AUC & akurasi arah nasional vs konsensus, mingguan 2021–2023 & origin dev. → hasil/lead_du.csv
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import EXP, H, dev_origins, np, pd  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
import kb_build as KBB  # noqa: E402
import meta_build as MB  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")


def city_dp4(daily, weeks):
    daily = daily.copy()
    daily["week"] = daily["date"] - pd.to_timedelta(daily["date"].dt.dayofweek, unit="D")
    wk = daily.groupby(["commodity", "regency_id", "week"])["price"].mean().reset_index()
    out = {}
    for c, g in wk.groupby("commodity"):
        L = np.log(g.pivot(index="week", columns="regency_id", values="price").reindex(weeks))
        out[c] = L - L.shift(4)
    return out


def leader_scores(nt, D4, h, K):
    """nt: tabel nasional (commodity, week, L, cons, share_up, z) mingguan → kolom li_K & q_lead_K (out-of-sample)."""
    nt = nt.copy()
    nt["err"] = (nt["share_up"] - nt["cons"]).where(nt["n_valid"] >= 10)
    weeks = np.array(sorted(nt["week"].unique()))
    li = np.full(len(nt), np.nan)
    q = np.full(len(nt), np.nan)
    for i in range(0, len(weeks), 4):
        r = weeks[i]
        nxt = weeks[i + 4] if i + 4 < len(weeks) else weeks[-1] + np.timedelta64(7, "D")
        tr_idx, tr_li, te_idx, te_li = [], [], [], []
        for c, g in nt.groupby("commodity"):
            if c not in D4:
                continue
            M = D4[c].reindex(pd.DatetimeIndex(g["week"]))
            wk = g["week"].to_numpy()
            trm = (wk + np.timedelta64(7 * h, "D") <= r) & g["err"].notna().to_numpy()
            if trm.sum() < 52:
                continue
            Mt = M[trm]
            mu, sd = Mt.mean(), Mt.std().replace(0, np.nan)
            Zall = ((M - mu) / sd)
            e = g["err"].to_numpy()[trm]
            cor = Zall[trm].apply(lambda col: pd.Series(col.to_numpy()).corr(pd.Series(e)) if col.notna().sum() >= 40 else np.nan)
            cor = cor.dropna()
            if len(cor) < K:
                continue
            top = cor.abs().sort_values(ascending=False).index[:K]
            idx_all = (Zall[top] * np.sign(cor[top])).mean(axis=1, skipna=True).to_numpy()
            tem = (wk >= r) & (wk < nxt)
            tr_idx += list(g.index[trm])
            tr_li += list(idx_all[trm])
            te_idx += list(g.index[tem])
            te_li += list(idx_all[tem])
        if not tr_idx or not te_idx:
            continue
        tr_idx, tr_li, te_idx, te_li = np.array(tr_idx), np.array(tr_li), np.array(te_idx), np.array(te_li)
        okt = np.isfinite(tr_li) & nt.loc[tr_idx, "z"].notna().to_numpy()
        g_ = MB.fit_offset_logit(tr_li[okt][:, None], nt.loc[tr_idx[okt], "z"].to_numpy(), nt.loc[tr_idx[okt], "L"].to_numpy())
        oke = np.isfinite(te_li)
        li[te_idx[oke]] = te_li[oke]
        q[te_idx[oke]] = 1 / (1 + np.exp(-(nt.loc[te_idx[oke], "L"].to_numpy() + g_[0] * te_li[oke])))
    nt[f"li_{K}"], nt[f"q_lead_{K}"] = li, q
    return nt


if __name__ == "__main__":
    daily = KBB.read_city_daily()
    weeks = pd.DatetimeIndex(sorted(pd.read_parquet(os.path.join(EXP, "c1t_weekly.parquet"))["week"].unique()))
    D4 = city_dp4(daily, weeks)
    rows = []
    for h in H:
        nt = MB.national(h).reset_index(drop=True)
        for K in (5, 10, 20):
            nt = leader_scores(nt, D4, h, K)
        nt.to_parquet(os.path.join(EXP, f"lead_national_h{h}.parquet"))
        base = nt[nt["z"].notna() & (nt["week"] >= pd.Timestamp("2021-01-04")) & (nt["week"] + pd.Timedelta(weeks=h) <= pd.Timestamp("2023-12-31"))]
        for scope, qq0 in (("mingguan", base), ("origin_dev", base[base["week"].isin(set(dev_origins(h)))])):
            for K in (5, 10, 20):
                qq = qq0[qq0[f"q_lead_{K}"].notna()]
                rows.append({"horizon": h, "scope": scope, "K": K, "n": len(qq), "auc_cons": roc_auc_score(qq["z"], qq["cons"]),
                             "auc_lead": roc_auc_score(qq["z"], qq[f"q_lead_{K}"]),
                             "acc_cons": float(((qq["cons"] > 0.5) == (qq["z"] > 0.5)).mean()),
                             "acc_lead": float(((qq[f"q_lead_{K}"] > 0.5) == (qq["z"] > 0.5)).mean()),
                             "corr_li_err": float(qq[f"li_{K}"].corr(qq["share_up"] - qq["cons"]))})
        print("h", h, "selesai", flush=True)
    t = pd.DataFrame(rows)
    t["d_auc"] = t["auc_lead"] - t["auc_cons"]
    t.round(4).to_csv(os.path.join(OUT, "lead_du.csv"), index=False)
    print(t.round(4).to_string(index=False))
