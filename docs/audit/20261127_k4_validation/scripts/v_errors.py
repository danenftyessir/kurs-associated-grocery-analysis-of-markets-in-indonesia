"""Analisis galat operasional K4-E80 (dev saja; PROTOCOL_ADDENDUM §4). Deskriptif; tidak memilih K atau τ.

Kategori alarm palsu & kenaikan terlewat, presisi@K1/2/3/5, persistensi, cakupan komoditas, sebaran alarm antarprovinsi (V2-setara),
kinerja menurut rezim ex-ante (tersil momentum harga nasional) dan laju terealisasi.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v_common import H, REGULATED, flags_k, np, pd, preds, save, top_flags  # noqa: E402
from k4_common import DEV_END, panel_logp  # noqa: E402

SCORES = ("k4_e80", "c1t", "clim_e80")
KS = (1, 2, 3, 5)
W = pd.Timedelta(weeks=1)


def late_rise(d, h, extra=4):
    """max_{k=h+1..h+extra} (log p_{t+k} − log p_t); NaN bila jendela melewati akhir dev atau semua minggu hilang."""
    lp = panel_logp()
    cols = lp.columns.get_indexer(pd.MultiIndex.from_frame(d[["province_id", "commodity"]]))
    r = np.arange(len(d))
    p0 = lp.reindex(pd.DatetimeIndex(d["origin"])).to_numpy()[r, cols]
    steps = []
    for k in range(h + 1, h + extra + 1):
        steps.append(lp.reindex(pd.DatetimeIndex(d["origin"] + k * W)).to_numpy()[r, cols] - p0)
    s = np.vstack(steps)
    with np.errstate(all="ignore"):
        mx = np.where(np.isnan(s).all(0), np.nan, np.nanmax(np.where(np.isnan(s), -np.inf, s), 0))
    beyond = (d["origin"] + (h + extra) * W > DEV_END).to_numpy()
    mx[beyond] = np.nan
    return mx


def main():
    D = preds("dev")
    POL, FP, FN, COV, PROV, REGM = [], [], [], [], [], []
    for h in H:
        d = D[D["horizon"] == h].reset_index(drop=True)
        y = d["z_e80"].to_numpy(int)
        d["late"] = late_rise(d, h)
        late_hit = (d["late"] >= d["thr_e80"]).to_numpy()
        late_known = np.isfinite(d["late"].to_numpy())
        rel = (d["y"] / d["thr_e80"]).to_numpy()
        cls = np.select([~d["has_target"], y == 1, d["y"] > 0, d["y"] < 0], ["hilang", "positif", "naik_bawah_ambang", "turun"], "tetap")
        reversed_mid = ((d["z_a80"] == 1) & (d["z_e80"] == 0)).to_numpy()
        flat4 = (d["lag_dp_4"].abs() < 1e-12).to_numpy()
        reg = d["commodity"].isin(REGULATED).to_numpy()
        po = d.groupby("origin").agg(rate=("z_e80", "mean"), mom=("nat_dp_4", "mean"))
        po["rate_t"] = pd.qcut(po["rate"], 3, labels=["rendah", "sedang", "tinggi"]).astype(str)
        po["mom_t"] = pd.qcut(po["mom"], 3, labels=["turun", "datar", "naik"]).astype(str)
        rate_t = d["origin"].map(po["rate_t"]).to_numpy()
        mom_t = d["origin"].map(po["mom_t"]).to_numpy()
        uo = np.sort(d["origin"].unique())
        nxt = dict(zip(uo[:-1], uo[1:]))
        no = len(uo)
        for s in SCORES:
            rnk = d.groupby(["origin", "province_id"])[s].rank(ascending=False, method="first").to_numpy()
            for k in KS:
                f = flags_k(d, s, k)
                hit = f & (y == 1)
                fl = d.loc[f, ["origin", "province_id", "commodity"]].copy()
                prev = fl.copy()
                prev["origin"] = prev["origin"].map(nxt)
                cur = fl[fl["origin"] > uo[0]]
                persist = len(cur.merge(prev, on=["origin", "province_id", "commodity"])) / max(len(cur), 1)
                per_o = d.assign(f=f).loc[f].groupby("origin")["commodity"].nunique()
                sh = d.loc[f, "commodity"].value_counts(normalize=True)
                POL.append({"horizon": h, "score": s, "K": k, "alarms_per_origin": f.sum() / no, "precision": hit.sum() / f.sum(),
                            "recall": hit.sum() / y.sum(), "tp_per_origin": hit.sum() / no, "fp_per_origin": (f & (y == 0)).sum() / no,
                            "fn_per_origin": (y.sum() - hit.sum()) / no, "persistence": persist,
                            "commodities_per_origin": per_o.mean(), "commodities_ever": d.loc[f, "commodity"].nunique(),
                            "max_commodity_share": sh.max(), "top_commodity": sh.idxmax(), "share_regulated": reg[f].mean(),
                            "lift_vs_base_rate": (hit.sum() / f.sum()) / y.mean()})
                fp = f & (y == 0)
                fn = ~f & (y == 1)
                r = {"horizon": h, "score": s, "K": k, "n_fp": int(fp.sum())}
                for c in ("naik_bawah_ambang", "turun", "tetap", "hilang"):
                    r[f"share_{c}"] = float((cls[fp] == c).mean())
                r["share_near_ge_0.5thr"] = float((rel[fp] >= 0.5).mean())
                r["share_near_ge_0.75thr"] = float((rel[fp] >= 0.75).mean())
                r["share_reversed_mid_window"] = float(reversed_mid[fp].mean())
                kn = fp & late_known
                r["share_late_rise_after_endpoint"] = float(late_hit[kn].mean()) if kn.any() else np.nan
                r["n_late_known"] = int(kn.sum())
                r["share_explained_by_timing"] = float((reversed_mid[kn] | late_hit[kn]).mean()) if kn.any() else np.nan
                tn = ~f & (y == 0)
                tnk = tn & late_known
                r["tn_share_reversed_mid_window"] = float(reversed_mid[tn].mean())
                r["tn_share_late_rise_after_endpoint"] = float(late_hit[tnk].mean())
                r["tn_share_near_ge_0.5thr"] = float((rel[tn] >= 0.5).mean())
                r["share_regulated"] = float(reg[fp].mean())
                r["share_low_rate_origin"] = float((rate_t[fp] == "rendah").mean())
                FP.append(r)
                q = {"horizon": h, "score": s, "K": k, "n_fn": int(fn.sum()),
                     "share_rank_K+1..K+2": float(((rnk[fn] > k) & (rnk[fn] <= k + 2)).mean()),
                     "share_rank_ge_6": float((rnk[fn] >= 6).mean()), "share_flat_prev4w": float(flat4[fn].mean()),
                     "share_regulated": float(reg[fn].mean()), "share_high_rate_origin": float((rate_t[fn] == "tinggi").mean()),
                     "median_rank": float(np.median(rnk[fn]))}
                FN.append(q)
                for t_ in ("rendah", "sedang", "tinggi"):
                    m = rate_t == t_
                    REGM.append({"horizon": h, "score": s, "K": k, "split": "laju_terealisasi", "tercile": t_,
                                 "n_origins": int(len(np.unique(d.loc[m, "origin"]))), "base_rate": y[m].mean(),
                                 "precision": (f[m] & (y[m] == 1)).sum() / f[m].sum(), "recall": (f[m] & (y[m] == 1)).sum() / y[m].sum()})
                for t_ in ("turun", "datar", "naik"):
                    m = mom_t == t_
                    REGM.append({"horizon": h, "score": s, "K": k, "split": "momentum_ex_ante", "tercile": t_,
                                 "n_origins": int(len(np.unique(d.loc[m, "origin"]))), "base_rate": y[m].mean(),
                                 "precision": (f[m] & (y[m] == 1)).sum() / f[m].sum(), "recall": (f[m] & (y[m] == 1)).sum() / y[m].sum()})
            # V2-setara nasional: 2 × jumlah provinsi per origin, sebaran antarprovinsi
            n2 = d.groupby("origin")["province_id"].nunique() * 2
            f2 = top_flags(d, s, ["origin"], n=n2, seed=154).to_numpy()
            cnt = d.assign(f=f2).groupby(["origin", "province_id"])["f"].sum()
            byo = cnt.groupby("origin")
            pp = d.assign(f=f2, hit=f2 & (y == 1)).groupby("province_id").agg(alarms=("f", "sum"), hits=("hit", "sum"),
                                                                                pos=("z_e80", "sum"))
            PROV.append({"horizon": h, "score": s, "precision_v2eq": (f2 & (y == 1)).sum() / f2.sum(),
                         "prov_without_alarm_per_origin": float(byo.apply(lambda x: (x == 0).sum()).mean()),
                         "max_alarms_one_province_per_origin": float(byo.max().mean()),
                         "alarms_per_province_sd": float(pp["alarms"].std() / no), "alarms_per_province_max": float(pp["alarms"].max() / no),
                         "alarms_per_province_min": float(pp["alarms"].min() / no),
                         "gini_alarms": float(gini(pp["alarms"].to_numpy(float))), "corr_alarms_pos": float(pp["alarms"].corr(pp["pos"]))})
            # cakupan per komoditas pada K = 2
            f = flags_k(d, s, 2)
            for c, g in d.assign(f=f, hit=f & (y == 1)).groupby("commodity"):
                COV.append({"horizon": h, "score": s, "commodity": c, "alarm_share": g["f"].sum() / f.sum(),
                            "precision": g["hit"].sum() / max(g["f"].sum(), 1), "recall": g["hit"].sum() / max(g["z_e80"].sum(), 1),
                            "positive_share": g["z_e80"].sum() / y.sum()})
    out = {}
    for name, rows in (("err_policies.csv", POL), ("err_false_alarms.csv", FP), ("err_missed.csv", FN),
                       ("err_by_regime.csv", REGM), ("err_province_spread.csv", PROV), ("err_commodity_coverage.csv", COV)):
        out[name] = save(pd.DataFrame(rows), name)
    pd.set_option("display.width", 260)
    for name, df in out.items():
        print(name)
        sub = df if "K" not in df else df[df["K"].isin([2]) | (name == "err_policies.csv")]
        print(sub.round(3).to_string(index=False))


def gini(x):
    x = np.sort(x)
    n = len(x)
    return (2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()) if x.sum() > 0 else np.nan


if __name__ == "__main__":
    main()
