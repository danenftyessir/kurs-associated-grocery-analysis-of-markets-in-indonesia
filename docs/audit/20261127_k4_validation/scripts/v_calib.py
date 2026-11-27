"""Audit kalibrasi K4-E80 (dev saja; PROTOCOL_ADDENDUM §3). Tidak membuka test, tidak melatih ulang K4.

Kalibrator walk-forward C0..C6 pada himpunan peluang D-164, ukuran Brier/log loss/ECE/kemiringan, ΔBrier vs C0 (bootstrap blok origin),
diagnosis ekor atas & pergeseran laju per origin, oracle intersep per origin (ex-post, batas atas; bukan kalibrator yang dapat dipakai).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v_common import H, REGULATED, brier, ece, logit, np, pd, preds, reliability, save  # noqa: E402
from k4_common import OUT as K4OUT, logloss  # noqa: E402
from k4_eval import Origins  # noqa: E402
from kagami.stats.meta import bh_fdr  # noqa: E402
from kagami.tracking.metrics import bootstrap_p  # noqa: E402
from scipy.optimize import minimize_scalar  # noqa: E402
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

MIN_O = 6
EPS = 1e-4


def sig(x):
    return 1 / (1 + np.exp(-x))


def platt_fit(p, z):
    if len(np.unique(z)) < 2:
        return None
    return LogisticRegression(C=1e6, max_iter=1000).fit(logit(p)[:, None], z)


def platt_apply(m, p):
    return m.predict_proba(logit(p)[:, None])[:, 1]


def fit_intercept(p, z):
    lp = logit(p)
    f = lambda a: -np.mean(z * np.log(np.clip(sig(lp + a), EPS, 1 - EPS)) + (1 - z) * np.log(np.clip(1 - sig(lp + a), EPS, 1 - EPS)))
    return minimize_scalar(f, bounds=(-5, 5), method="bounded").x


def walk(d, h, method):
    out = np.full(len(d), np.nan)
    uo = np.sort(d["origin"].unique())
    for o in uo:
        pm = (d["origin"] + pd.Timedelta(weeks=h) <= o).to_numpy()
        past_o = np.sort(d.loc[pm, "origin"].unique())
        if len(past_o) < MIN_O:
            continue
        cur = (d["origin"] == o).to_numpy()
        past = d[pm]
        p, z = past["k4_e80"].to_numpy(float), past["z_e80"].to_numpy(int)
        pc = d.loc[cur, "k4_e80"].to_numpy(float)
        if method == "C1":
            m = platt_fit(p, z)
            out[cur] = platt_apply(m, pc)
        elif method == "C2":
            iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip").fit(p, z)
            out[cur] = iso.predict(pc)
        elif method == "C3":
            g = platt_fit(p, z)
            res = platt_apply(g, pc)
            cc = d.loc[cur, "commodity"].to_numpy()
            for c in np.unique(cc):
                pp = past["commodity"].to_numpy() == c
                if z[pp].sum() >= 30 and (1 - z[pp]).sum() >= 30:
                    m = platt_fit(p[pp], z[pp])
                    res[cc == c] = platt_apply(m, pc[cc == c])
            out[cur] = res
        elif method == "C4":
            a = fit_intercept(p, z)
            out[cur] = sig(logit(pc) + a)
        elif method == "C5":
            keep = np.isin(past["origin"].to_numpy(), past_o[-13:])
            m = platt_fit(p[keep], z[keep])
            out[cur] = platt_apply(m, pc)
        elif method == "C6":
            c = past["clim_e80"].to_numpy(float)
            ws = np.round(np.arange(0, 1.0001, 0.05), 2)
            b = [np.mean((w * p + (1 - w) * c - z) ** 2) for w in ws]
            w = ws[int(np.argmin(b))]
            out[cur] = w * pc + (1 - w) * d.loc[cur, "clim_e80"].to_numpy(float)
    return out


def cal_line(y, p):
    """Intersep & kemiringan kalibrasi (z ~ a + b·logit p), CITL = rerata y − rerata p."""
    m = LogisticRegression(C=1e6, max_iter=1000).fit(logit(p)[:, None], y)
    return float(m.intercept_[0]), float(m.coef_[0, 0]), float(np.mean(y) - np.mean(p))


def oracle_origin(d, col):
    """Ex-post: geser intersep per origin pada baris origin itu sendiri (batas atas manfaat mengetahui laju origin)."""
    out = np.empty(len(d))
    for o, g in d.groupby("origin"):
        idx = g.index.to_numpy()
        z = g["z_e80"].to_numpy(int)
        a = fit_intercept(g[col].to_numpy(float), z) if 0 < z.sum() < len(z) else (-5 if z.sum() == 0 else 5)
        out[idx] = sig(logit(g[col].to_numpy(float)) + a)
    return out


def main():
    D = preds("dev")
    meta = pd.read_csv(os.path.join(K4OUT, "k4_dev_meta.csv"), parse_dates=["origin"])
    M, PAIR, REL, TAIL, PO, COM, REG = [], [], [], [], [], [], []
    for h in H:
        d = D[D["horizon"] == h].reset_index(drop=True)
        for c in ("C1", "C2", "C3", "C4", "C5", "C6"):
            d[c] = walk(d, h, c)
        d["C0"] = d["k4_e80"]
        e = d[d["C1"].notna()].reset_index(drop=True)
        assert e[["C2", "C3", "C4", "C5", "C6"]].notna().all().all()
        e["ORACLE_origin"] = oracle_origin(e, "k4_e80")
        O = Origins(e, h)
        y = e["z_e80"].to_numpy(float)
        bc = (e["clim_e80"].to_numpy(float) - y) ** 2
        n = O.per_origin_sum(np.ones(len(e)))
        b0 = (e["C0"].to_numpy(float) - y) ** 2
        for c in ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "clim_e80", "clims_e80", "ORACLE_origin"):
            p = np.clip(e[c].to_numpy(float), 0, 1)
            bm = (p - y) ** 2
            a, b, citl = cal_line(y, np.clip(p, EPS, 1 - EPS))
            bss_b = 1 - O.per_origin_sum(bm)[O.idx].sum(1) / O.per_origin_sum(bc)[O.idx].sum(1)
            M.append({"horizon": h, "calibrator": c, "n": len(e), "n_origins": e["origin"].nunique(), "base_rate": y.mean(),
                      "mean_p": p.mean(), "brier": bm.mean(), "logloss": logloss(y, p), "ece": ece(y, p),
                      "cal_intercept": a, "cal_slope": b, "citl": citl, "bss_vs_clim": 1 - bm.sum() / bc.sum(),
                      "bss_lo": np.percentile(bss_b, 2.5), "bss_hi": np.percentile(bss_b, 97.5),
                      "max_p": p.max(), "n_p_ge_0.6": int((p >= 0.6).sum()), "n_p_ge_0.7": int((p >= 0.7).sum()),
                      "obs_rate_p_ge_0.6": float(y[p >= 0.6].mean()) if (p >= 0.6).any() else np.nan,
                      "obs_rate_p_ge_0.7": float(y[p >= 0.7].mean()) if (p >= 0.7).any() else np.nan})
            if c in ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "ORACLE_origin"):
                bd = (O.per_origin_sum(bm)[O.idx].sum(1) - O.per_origin_sum(b0)[O.idx].sum(1)) / n[O.idx].sum(1)
                if c != "C0":
                    PAIR.append({"horizon": h, "a": c, "b": "C0", "dbrier": bm.mean() - b0.mean(),
                                 "lo": np.percentile(bd, 2.5), "hi": np.percentile(bd, 97.5), "p": bootstrap_p(bd, 0.0)})
                rel = reliability(y, p).reset_index()
                ob = pd.DataFrame({"b": np.clip((p * 10).astype(int), 0, 9), "o": e["origin"]}).groupby("b")["o"].nunique()
                REL.append(rel.assign(horizon=h, calibrator=c, n_origins=rel["b"].map(ob)))
        # ---- diagnosis ekor atas (mentah)
        for lo in (0.6, 0.7, 0.8):
            t = e[e["C0"] >= lo]
            for key, g in [("ALL", t)] + [(f"commodity={k}", gg) for k, gg in t.groupby("commodity")] + \
                    [(f"year={k}", gg) for k, gg in t.groupby(t["origin"].dt.year)]:
                TAIL.append({"horizon": h, "p_min": lo, "group": key, "n": len(g), "n_origins": g["origin"].nunique(),
                             "mean_p": g["C0"].mean(), "obs_rate": g["z_e80"].mean()})
            top = t.groupby("origin").agg(n=("C0", "size"), mean_p=("C0", "mean"), obs=("z_e80", "mean")).sort_values("n", ascending=False)
            for o, r in top.head(5).iterrows():
                TAIL.append({"horizon": h, "p_min": lo, "group": f"origin={o.date()}", "n": int(r["n"]), "n_origins": 1,
                             "mean_p": r["mean_p"], "obs_rate": r["obs"]})
        # ---- per origin: laju latih vs prediksi vs terealisasi + rezim ex-ante
        mo = meta[meta["horizon"] == h].set_index("origin")["train_rate_e80"]
        po = d.groupby("origin").agg(realized=("z_e80", "mean"), mean_p=("k4_e80", "mean"), mean_p_c1=("C1", "mean"),
                                     nat_mom=("nat_dp_4", "mean"), share_p_ge_0_6=("k4_e80", lambda s: (s >= 0.6).mean()))
        po["train_rate"] = mo.reindex(po.index).to_numpy()
        po["horizon"] = h
        po["regime_tercile"] = pd.qcut(po["nat_mom"], 3, labels=["turun", "datar", "naik"]).astype(str)
        PO.append(po.reset_index())
        for t_, gg in e.assign(reg=e["origin"].map(po["regime_tercile"])).groupby("reg"):
            REG.append({"horizon": h, "regime_ex_ante": t_, "n_origins": gg["origin"].nunique(), "base_rate": gg["z_e80"].mean(),
                        "mean_p_C0": gg["C0"].mean(), "mean_p_C1": gg["C1"].mean(), "brier_C0": brier(gg["z_e80"], gg["C0"]),
                        "brier_C1": brier(gg["z_e80"], gg["C1"]), "brier_clim": brier(gg["z_e80"], gg["clim_e80"]),
                        "ece_C0": ece(gg["z_e80"], gg["C0"]),
                        "obs_rate_p_ge_0.6": gg.loc[gg["C0"] >= 0.6, "z_e80"].mean(), "n_p_ge_0.6": int((gg["C0"] >= 0.6).sum())})
        for c, gg in e.groupby("commodity"):
            COM.append({"horizon": h, "commodity": c, "regulated": c in REGULATED, "n": len(gg), "base_rate": gg["z_e80"].mean(),
                        "mean_p_C0": gg["C0"].mean(), "mean_p_C1": gg["C1"].mean(), "mean_p_C3": gg["C3"].mean(),
                        "brier_C0": brier(gg["z_e80"], gg["C0"]), "brier_C1": brier(gg["z_e80"], gg["C1"]),
                        "brier_C3": brier(gg["z_e80"], gg["C3"]), "brier_clim": brier(gg["z_e80"], gg["clim_e80"]),
                        "n_p_ge_0.6": int((gg["C0"] >= 0.6).sum()),
                        "obs_rate_p_ge_0.6": gg.loc[gg["C0"] >= 0.6, "z_e80"].mean()})
    M, PR = pd.DataFrame(M), pd.DataFrame(PAIR)
    fam = PR["a"].isin(["C1", "C2", "C3", "C4", "C5", "C6"])
    PR.loc[fam, "q_bh"] = bh_fdr(PR.loc[fam, "p"].to_numpy(float))
    # aturan kandidat (PROTOCOL_ADDENDUM §3)
    cand = []
    for c in ("C1", "C2", "C3", "C4", "C5", "C6"):
        r8 = PR[(PR["a"] == c) & (PR["horizon"] == 8)].iloc[0]
        r4 = PR[(PR["a"] == c) & (PR["horizon"] == 4)].iloc[0]
        ec = M[(M["calibrator"] == c)].set_index("horizon")["ece"]
        ok = (r8["dbrier"] < 0) and (r8["hi"] < 0) and (r8["q_bh"] < 0.05) and (r4["dbrier"] <= 0) and (ec <= 0.05).all()
        cand.append({"calibrator": c, "dbrier_h8": r8["dbrier"], "hi_h8": r8["hi"], "q_h8": r8["q_bh"], "dbrier_h4": r4["dbrier"],
                     "ece_h4": ec[4], "ece_h8": ec[8], "candidate": bool(ok)})
    save(M, "cal_metrics.csv")
    save(PR, "cal_paired_vs_raw.csv")
    save(pd.DataFrame(cand), "cal_candidates.csv")
    save(pd.concat(REL), "cal_reliability.csv")
    save(pd.DataFrame(TAIL), "cal_tail_composition.csv")
    POd = pd.concat(PO)
    save(POd, "cal_per_origin.csv")
    save(pd.DataFrame(REG), "cal_by_regime.csv")
    save(pd.DataFrame(COM), "cal_by_commodity.csv")
    stats = []
    for h, g in POd.groupby("horizon"):
        stats.append({"horizon": h, "corr_realized_meanp": g["realized"].corr(g["mean_p"]),
                      "slope_meanp_on_realized": np.polyfit(g["realized"], g["mean_p"], 1)[0],
                      "sd_realized": g["realized"].std(), "sd_mean_p": g["mean_p"].std(),
                      "mean_abs_train_minus_realized": (g["train_rate"] - g["realized"]).abs().mean(),
                      "corr_share_hi_vs_realized": g["share_p_ge_0_6"].corr(g["realized"])})
    save(pd.DataFrame(stats), "cal_origin_shift_stats.csv")
    pd.set_option("display.width", 250)
    print(M.round(4).to_string(index=False))
    print(PR.round(4).to_string(index=False))
    print(pd.DataFrame(cand).round(4).to_string(index=False))
    print(pd.DataFrame(stats).round(3).to_string(index=False))
    print(pd.DataFrame(REG).round(3).to_string(index=False))
    T = pd.DataFrame(TAIL)
    print(T[T["p_min"] >= 0.7].round(3).to_string(index=False))
    print(pd.DataFrame(COM).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
