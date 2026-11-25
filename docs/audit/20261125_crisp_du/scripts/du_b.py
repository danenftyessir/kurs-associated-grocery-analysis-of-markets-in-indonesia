"""D-153 Data Understanding lanjutan (tetap dev saja): pemeriksaan pengganggu untuk tiga layar du.py.

B1 (DU-1): 6 pasangan teratas — tanda korelasi residual stabil antara origin 2021–2022 dan 2023? (co-trend sesaat vs pola berulang)
B2 (DU-2): galat per seri diganti SKILL = log loss laju-dasar seri − log loss C1-tuned (laju-dasar = porsi naik seri di dev, in-sample
    → batas atas skill dasar). Apakah klaster/karakteristik menjelaskan skill di luar komoditas, dan ke arah mana (koefisien dalam komoditas)?
B3 (DU-3): layar graf diulang terhadap residual `IW_NAT` (D-151): apakah tetangga menambah di atas intraminggu sendiri + nasional?
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from du import EXP, K, OUT, finish, screen  # noqa: E402

if __name__ == "__main__":
    tab = pd.read_parquet(os.path.join(EXP, "iw2.parquet"))
    preds = pd.read_parquet(os.path.join(EXP, "d151_iw_dev_preds.parquet"))
    preds = preds[np.isfinite(preds["y_true"]) & (preds["y_true"] != 0)].copy()
    preds["r"] = (preds["y_true"] > 0).astype(float) - preds["p_up"]
    base = preds[preds["variant"] == "base"].copy()

    # B1
    t1 = pd.read_csv(os.path.join(OUT, "du1_cross_commodity.csv")).sort_values("p").head(6)
    W = tab.pivot_table(index=["week", "province_id"], columns="commodity", values="lag_dp_4")
    nat = tab.groupby(["week", "commodity"])["lag_dp_4"].mean().unstack()
    rows = []
    for _, r in t1.iterrows():
        pair, lvl = r["signal"].rsplit(" ", 1)
        A, B = pair.split("->")
        h = int(r["horizon"])
        Db = base[(base["horizon"] == h) & (base["commodity"] == B)]
        key = pd.MultiIndex.from_arrays([Db["origin"], Db["province_id"]])
        x = W[A].reindex(key).to_numpy() if lvl == "prov" else nat[A].reindex(Db["origin"]).to_numpy()
        Db = Db.assign(x=x)
        for per, m in (("2021–2022", Db["origin"] < "2023-01-01"), ("2023", Db["origin"] >= "2023-01-01")):
            rows.append({"signal": r["signal"], "horizon": h, "period": per, **screen(Db[m], "x", h)})
    B1 = pd.DataFrame(rows)
    B1.round(4).to_csv(os.path.join(OUT, "du1b_subperiod.csv"), index=False)
    print(B1.round(3).to_string(index=False), flush=True)

    # B2
    ch = pd.read_csv(os.path.join(OUT, "du2_series_characteristics.csv"))
    eps = 1e-6
    base["up"] = base["y_true"] > 0
    br = base.groupby(["horizon"] + K)["up"].transform("mean").clip(eps, 1 - eps)
    p = base["p_up"].clip(eps, 1 - eps)
    base["ll_model"] = -np.where(base["up"], np.log(p), np.log(1 - p))
    base["ll_rate"] = -np.where(base["up"], np.log(br), np.log(1 - br))
    per = base.groupby(["horizon"] + K)[["ll_model", "ll_rate"]].mean().reset_index()
    per["skill"] = per["ll_rate"] - per["ll_model"]
    cols = ["vol", "zero_share", "up_share", "mag", "ac1"]
    rows, coefs = [], []
    rng = np.random.default_rng(1533)
    for h in (4, 8):
        s = per[per["horizon"] == h].merge(ch, on=K).reset_index(drop=True)
        y = s["skill"].to_numpy()
        Xc = pd.get_dummies(s["commodity"]).to_numpy(float)

        def fitr2(X):
            X1 = np.column_stack([np.ones(len(X)), X])
            b = np.linalg.lstsq(X1, y, rcond=None)[0]
            return 1 - ((y - X1 @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum(), b
        r2c, _ = fitr2(Xc)
        Xk = pd.get_dummies(s["cluster"]).to_numpy(float)
        Xch = StandardScaler().fit_transform(s[cols])
        for name, Xadd in (("klaster", Xk), ("karakteristik", Xch)):
            r2, b = fitr2(np.column_stack([Xc, Xadd]))
            null = []
            for _ in range(999):
                perm = s.groupby("commodity").sample(frac=1, random_state=int(rng.integers(1e9))).index.to_numpy()
                null.append(fitr2(np.column_stack([Xc, Xadd[perm]]))[0] - r2c)
            rows.append({"horizon": h, "added": name, "skill_mean": y.mean(), "share_series_skill_le0": float((y <= 0).mean()),
                         "r2_commodity": r2c, "r2_increment": r2 - r2c, "p_perm": (1 + np.sum(np.array(null) >= r2 - r2c)) / 1000})
            if name == "karakteristik":
                coefs += [{"horizon": h, "characteristic": c, "coef_within_commodity_per_sd": b[1 + Xc.shape[1] + i]} for i, c in enumerate(cols)]
        sk = s.groupby("cluster")["skill"].agg(["mean", "size"]).reset_index().assign(horizon=h)
        print(f"skill per klaster h{h}:\n", sk.round(4).to_string(index=False))
    B2 = pd.DataFrame(rows)
    B2.round(4).to_csv(os.path.join(OUT, "du2b_skill.csv"), index=False)
    pd.DataFrame(coefs).round(4).to_csv(os.path.join(OUT, "du2b_skill_coef.csv"), index=False)
    print(B2.round(4).to_string(index=False))
    print(pd.DataFrame(coefs).round(4).to_string(index=False), flush=True)

    # B3: graf vs residual IW_NAT (tetangga dihitung sama dengan du.py)
    import du as du_mod
    reg = du_mod.cfg.regions.set_index("province_id")
    ids = reg.index.astype(int).tolist()
    dist = np.array([[du_mod.haversine_km(reg.loc[a, "lat"], reg.loc[a, "lon"], reg.loc[b, "lat"], reg.loc[b, "lon"]) for b in ids] for a in ids])
    geo = {a: [ids[j] for j in np.argsort(dist[i])[1:4]] for i, a in enumerate(ids)}
    P = tab[tab["week"] <= du_mod.PRE_END].pivot_table(index="week", columns=K, values="log_p").sort_index().diff()
    corr_nb = {}
    for c in sorted(set(P.columns.get_level_values("commodity"))):
        M = P.xs(c, axis=1, level="commodity").corr(min_periods=52)
        for a in M.columns:
            corr_nb[(a, c)] = M[a].drop(a).dropna().sort_values(ascending=False).index[:3].tolist()
    Wc = tab.pivot_table(index=["week", "commodity"], columns="province_id", values="iw_gap")
    tot, cnt = Wc.sum(axis=1), Wc.notna().sum(axis=1)
    rows3 = []
    for gname in ("geo", "corr"):
        vals = {}
        for p_ in Wc.columns:
            own = Wc[p_]
            nat_loo = (tot - own.fillna(0)) / (cnt - own.notna().astype(int))
            if gname == "geo":
                nb = Wc[[q for q in geo[p_] if q in Wc.columns]].mean(axis=1)
            else:
                nb = pd.Series(np.nan, index=Wc.index)
                for c in Wc.index.get_level_values("commodity").unique():
                    qs = [q for q in corr_nb.get((p_, c), []) if q in Wc.columns]
                    if qs:
                        m = Wc.index.get_level_values("commodity") == c
                        nb[m] = Wc.loc[m, qs].mean(axis=1)
            vals[p_] = nb - nat_loo
        s = pd.DataFrame(vals).stack().rename_axis(["origin", "commodity", "province_id"]).rename("x").reset_index()
        for ref in ("base", "IW_NAT"):
            for h in (4, 8):
                d = preds[(preds["variant"] == ref) & (preds["horizon"] == h)].merge(s, on=["origin", "commodity", "province_id"], how="left")
                rows3.append({"du": "DU-3b", "role": "kandidat", "signal": f"tetangga − nasional: iw_gap ({gname})", "residual_of": ref,
                              "horizon": h, **screen(d, "x", h)})
    for h in (4, 8):        # kontrol: iw_gap sendiri pada residual IW_NAT harus ≈ 0 (sudah dipakai)
        d = preds[(preds["variant"] == "IW_NAT") & (preds["horizon"] == h)].merge(
            tab[["week"] + K + ["iw_gap"]].rename(columns={"week": "origin"}), on=["origin"] + K, how="left")
        rows3.append({"du": "DU-3b", "role": "kontrol-", "signal": "iw_gap sendiri", "residual_of": "IW_NAT", "horizon": h, **screen(d, "iw_gap", h)})
    B3 = finish(rows3, "du3b_graph_vs_iwnat")
    print(B3.round(4).to_string(index=False), flush=True)
