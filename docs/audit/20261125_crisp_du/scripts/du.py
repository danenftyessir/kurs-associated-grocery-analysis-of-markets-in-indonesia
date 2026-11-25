"""D-153 Data Understanding (CRISP-DM fase 2) untuk tiga arah Task 4: pola sekuensial lintas komoditas, clustering seri, graf provinsi.

Hanya data pengembangan: residual C1-tuned di origin pengembangan (target ≤ 2023-12-31; prediksi `base` D-151 = `direction_tuned_preds`
C1t) dan karakteristik seri dari 2018-01..2020-12 (sebelum origin pertama). Test 2024+ tidak disentuh. Tidak ada model baru.

Layar "informasi yang belum dipakai": korelasi residual r = 1[y > 0] − p_up (baris y ≠ 0) dengan sinyal kandidat x pada origin.
Inferensi = bootstrap blok origin (blok ceil(h/4)+1, 1.999 replikasi), q BH per keluarga. Kontrol positif: `iw_gap` & `iw_return_nat_loo`
(terbukti menaikkan macro F1 bila ditambahkan, D-151/D-152); kontrol negatif: derau acak & `lag_dp_4` milik sendiri (sudah dipakai).
DU-1: momentum 4 minggu komoditas lain (provinsi sama / nasional) → residual komoditas target.
DU-2: karakteristik seri 2018–2020 → klaster; apakah klaster/karakteristik menjelaskan galat per seri di luar identitas komoditas.
DU-3: tetangga geografis (3 ibu kota terdekat) & tetangga korelasi (3 provinsi paling berkorelasi 2018–2020) − rerata nasional LOO.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.data.reference import haversine_km  # noqa: E402
from kagami.stats.meta import bh_fdr  # noqa: E402
from kagami.stats.resampling import moving_block_indices  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
REPS = 1999
PRE_END = pd.Timestamp("2020-12-28")
K = ["province_id", "commodity"]


def screen(d, xcol, h):
    """Korelasi pooled residual–x + interval & p bootstrap blok origin."""
    d = d[np.isfinite(d[xcol])]
    if len(d) < 100 or d[xcol].std() == 0:
        return {"rho": np.nan, "lo": np.nan, "hi": np.nan, "p": np.nan, "n": len(d)}
    uo, inv = np.unique(d["origin"].to_numpy(), return_inverse=True)
    x, r = d[xcol].to_numpy(float), d["r"].to_numpy(float)
    S = np.zeros((len(uo), 6))
    for j, v in enumerate((np.ones_like(x), x, r, x * r, x * x, r * r)):
        np.add.at(S[:, j], inv, v)

    def corr(T):
        n, sx, sr, sxr, sxx, srr = (T[..., j] for j in range(6))
        return (n * sxr - sx * sr) / np.sqrt((n * sxx - sx ** 2) * (n * srr - sr ** 2))
    rho = float(corr(S.sum(0)))
    blk = int(np.ceil(h / 4)) + 1
    idx = np.vstack([moving_block_indices(len(uo), blk, np.random.default_rng(r_)) for r_ in range(REPS)])
    b = corr(S[idx].sum(1))
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    p = float(min(1.0, 2 * min((b <= 0).mean(), (b >= 0).mean()) + 1 / REPS))
    return {"rho": rho, "lo": float(lo), "hi": float(hi), "p": p, "n": int(len(d))}


def finish(rows, name):
    t = pd.DataFrame(rows)
    fam = ~t["role"].isin(["kontrol+", "kontrol-"])
    t["q_bh"] = np.nan
    t.loc[fam & t["p"].notna(), "q_bh"] = bh_fdr(t.loc[fam & t["p"].notna(), "p"].to_numpy())
    t.round(4).to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
    return t


if __name__ == "__main__":
    tab = pd.read_parquet(os.path.join(EXP, "iw2.parquet"))
    preds = pd.read_parquet(os.path.join(EXP, "d151_iw_dev_preds.parquet"))
    base = preds[(preds["variant"] == "base") & np.isfinite(preds["y_true"]) & (preds["y_true"] != 0)].copy()
    base["r"] = (base["y_true"] > 0).astype(float) - base["p_up"]
    feat = tab[["week"] + K + ["lag_dp_4", "lag_dp_1", "log_p", "iw_gap", "iw_return", "iw_return_nat_loo"]].rename(columns={"week": "origin"})
    D = base.merge(feat, on=["origin"] + K, how="left")
    D["noise"] = np.random.default_rng(153).normal(size=len(D))
    print("baris residual dev:", len(D), "origin:", D.groupby("horizon")["origin"].nunique().to_dict(), flush=True)

    # kontrol
    ctrl = []
    for h in (4, 8):
        Dh = D[D["horizon"] == h]
        for x, role in (("iw_gap", "kontrol+"), ("iw_return_nat_loo", "kontrol+"), ("noise", "kontrol-"), ("lag_dp_4", "kontrol-")):
            ctrl.append({"du": "kontrol", "role": role, "signal": x, "horizon": h, **screen(Dh, x, h)})
    C = finish(ctrl, "du0_controls")
    print(C.round(4).to_string(index=False), flush=True)

    # DU-1: momentum komoditas lain
    W = tab.pivot_table(index=["week", "province_id"], columns="commodity", values="lag_dp_4")
    nat = tab.groupby(["week", "commodity"])["lag_dp_4"].mean().unstack()
    comms = list(W.columns)
    rows = []
    for h in (4, 8):
        Dh = D[D["horizon"] == h]
        for B in comms:
            Db = Dh[Dh["commodity"] == B]
            key = pd.MultiIndex.from_arrays([Db["origin"], Db["province_id"]])
            for A in comms:
                if A == B:
                    continue
                tmp = Db.assign(x_prov=W[A].reindex(key).to_numpy(), x_nat=nat[A].reindex(Db["origin"]).to_numpy())
                rows.append({"du": "DU-1", "role": "kandidat", "signal": f"{A}->{B} prov", "horizon": h, **screen(tmp, "x_prov", h)})
                rows.append({"du": "DU-1", "role": "kandidat", "signal": f"{A}->{B} nat", "horizon": h, **screen(tmp, "x_nat", h)})
    T1 = finish(rows, "du1_cross_commodity")
    print("DU-1:", len(T1), "uji; q<0,05:", int((T1["q_bh"] < 0.05).sum()), "; |rho| maks", round(T1["rho"].abs().max(), 4), flush=True)
    print(T1.sort_values("p").head(12).round(4).to_string(index=False), flush=True)

    # DU-2: karakteristik seri 2018-01..2020-12 → klaster
    P = tab[tab["week"] <= PRE_END].pivot_table(index="week", columns=K, values="log_p").sort_index()
    dP = P.diff()
    nz = dP.where(dP != 0)
    ch = pd.DataFrame({
        "vol": dP.std(), "zero_share": (dP == 0).sum() / dP.notna().sum(), "up_share": (nz > 0).sum() / nz.notna().sum(),
        "mag": nz.abs().median(), "ac1": dP.apply(lambda s: s.autocorr(1)),
    }).dropna()
    Z = StandardScaler().fit_transform(ch)
    sil = {k: silhouette_score(Z, KMeans(k, n_init=50, random_state=0).fit_predict(Z)) for k in range(2, 9)}
    k_best = max(sil, key=sil.get)
    lab = KMeans(k_best, n_init=50, random_state=0).fit_predict(Z)
    ch["cluster"] = lab
    ari_comm = adjusted_rand_score(ch.index.get_level_values("commodity"), lab)
    # galat per seri (dev): log loss C1-tuned
    eps = 1e-6
    base["ll"] = -((base["y_true"] > 0) * np.log(base["p_up"].clip(eps, 1 - eps)) + (base["y_true"] < 0) * np.log((1 - base["p_up"]).clip(eps, 1 - eps)))
    base["acc"] = ((base["p_up"] > 0.5) == (base["y_true"] > 0)).astype(float)
    per = base.groupby(["horizon"] + K)[["ll", "acc"]].mean().reset_index()
    rows2 = []
    rng = np.random.default_rng(1532)
    for h in (4, 8):
        s = per[per["horizon"] == h].merge(ch.reset_index(), on=K)
        y = s["ll"].to_numpy()
        Xc = pd.get_dummies(s["commodity"]).to_numpy(float)

        def r2(X):
            X1 = np.column_stack([np.ones(len(X)), X])
            beta = np.linalg.lstsq(X1, y, rcond=None)[0]
            return 1 - ((y - X1 @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        r2c = r2(Xc)
        Xk = pd.get_dummies(s["cluster"]).to_numpy(float)
        Xch = StandardScaler().fit_transform(s[["vol", "zero_share", "up_share", "mag", "ac1"]])
        for name, Xadd in (("klaster", Xk), ("karakteristik", Xch)):
            inc = r2(np.column_stack([Xc, Xadd])) - r2c
            null = []
            for _ in range(999):       # permutasi DI DALAM komoditas (mempertahankan efek komoditas)
                perm = s.groupby("commodity").sample(frac=1, random_state=int(rng.integers(1e9))).index
                null.append(r2(np.column_stack([Xc, Xadd[s.index.get_indexer(perm)]])) - r2c)
            rows2.append({"horizon": h, "added": name, "r2_commodity": r2c, "r2_increment": inc,
                          "p_perm": (1 + np.sum(np.array(null) >= inc)) / 1000, "n_series": len(s)})
    T2 = pd.DataFrame(rows2)
    T2.round(4).to_csv(os.path.join(OUT, "du2_cluster_errors.csv"), index=False)
    comp = pd.crosstab(ch.index.get_level_values("commodity"), ch["cluster"])
    comp.to_csv(os.path.join(OUT, "du2_cluster_composition.csv"))
    pd.Series(sil).round(4).to_csv(os.path.join(OUT, "du2_silhouette.csv"), header=["silhouette"])
    ch.round(4).to_csv(os.path.join(OUT, "du2_series_characteristics.csv"))
    print(f"DU-2: k terbaik {k_best} (silhouette {sil[k_best]:.3f}), ARI klaster vs komoditas {ari_comm:.3f}")
    print(comp.to_string())
    print(T2.round(4).to_string(index=False), flush=True)

    # DU-3: graf provinsi
    reg = cfg.regions.set_index("province_id")
    ids = reg.index.astype(int).tolist()
    dist = np.array([[haversine_km(reg.loc[a, "lat"], reg.loc[a, "lon"], reg.loc[b, "lat"], reg.loc[b, "lon"]) for b in ids] for a in ids])
    geo = {a: [ids[j] for j in np.argsort(dist[i])[1:4]] for i, a in enumerate(ids)}
    corr_nb = {}
    for c in sorted(set(dP.columns.get_level_values("commodity"))):
        M = dP.xs(c, axis=1, level="commodity").corr(min_periods=52)
        for a in M.columns:
            corr_nb[(a, c)] = M[a].drop(a).dropna().sort_values(ascending=False).index[:3].tolist()
    sig = {}
    for col in ("lag_dp_4", "iw_gap", "log_p"):
        Wc = tab.pivot_table(index=["week", "commodity"], columns="province_id", values=col)
        tot, cnt = Wc.sum(axis=1), Wc.notna().sum(axis=1)
        for gname in ("geo", "corr"):
            vals = {}
            for p in Wc.columns:
                own = Wc[p]
                nat_loo = (tot - own.fillna(0)) / (cnt - own.notna().astype(int))
                if gname == "geo":
                    nb = Wc[[q for q in geo[p] if q in Wc.columns]].mean(axis=1)
                else:
                    nb = pd.Series(np.nan, index=Wc.index)
                    for c in Wc.index.get_level_values("commodity").unique():
                        qs = [q for q in corr_nb.get((p, c), []) if q in Wc.columns]
                        if qs:
                            m = Wc.index.get_level_values("commodity") == c
                            nb[m] = Wc.loc[m, qs].mean(axis=1)
                vals[p] = (own - nb) if col == "log_p" else (nb - nat_loo)
            sig[(col, gname)] = pd.DataFrame(vals).stack().rename_axis(["origin", "commodity", "province_id"]).rename("x")
    rows3 = []
    for h in (4, 8):
        Dh = D[D["horizon"] == h]
        for (col, gname), s in sig.items():
            tmp = Dh.merge(s.reset_index(), on=["origin", "commodity", "province_id"], how="left")
            label = {"lag_dp_4": "tetangga − nasional: Δ4", "iw_gap": "tetangga − nasional: iw_gap", "log_p": "sendiri − tetangga: level"}[col]
            rows3.append({"du": "DU-3", "role": "kandidat", "signal": f"{label} ({gname})", "horizon": h, **screen(tmp, "x", h)})
    T3 = finish(rows3, "du3_graph")
    print(T3.round(4).to_string(index=False), flush=True)
