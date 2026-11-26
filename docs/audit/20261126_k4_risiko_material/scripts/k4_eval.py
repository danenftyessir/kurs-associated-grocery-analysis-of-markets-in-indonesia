"""K4 Fase D/E — evaluasi ranking, peluang, operasional, utilitas, galat, target kejadian, kepekaan; aturan PROTOCOL §5–§6.

PART=dev (seleksi; menulis hasil/k4_test_allowed.flag bila keputusan ACCEPT/PARTIAL) | test (sekali; deskriptif, kalibrator walk-forward
memakai prediksi dev + test lampau). Ditulis sesudah protokol dibekukan sebagai implementasi §3–§6 yang sudah tertulis.
Keluaran hasil/k4_{PART}_*.csv, k4_{PART}_decision.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k4_common import (EXP, H, OUT, REGULATED, boot_idx, brier, ece, logloss, np, pd, platt_walkforward, reliability,
                       top_flags)  # noqa: E402
from kagami.stats.meta import bh_fdr  # noqa: E402
from kagami.tracking.metrics import bootstrap_p  # noqa: E402

PART = os.environ.get("PART", "dev")
SFX = "" if PART == "dev" else f"_{PART}"
NAIVE = ["R_mom", "R_nat", "R_rev", "R_seas"]
SEED = 154


# ---------------------------------------------------------------- dasar
def fast_ap(y, s):
    """Average precision (= sklearn average_precision_score, ties dikelompokkan); NaN skor = paling bawah."""
    s = np.where(np.isfinite(s), s, -1e18)        # bukan −inf: diff(−inf, −inf) = NaN memecah kelompok skor kembar (uji mandiri)
    o = np.argsort(-s, kind="mergesort")
    y, s = y[o], s[o]
    npos = y.sum()
    if npos == 0 or npos == len(y):
        return np.nan
    idx = np.r_[np.where(np.diff(s))[0], len(y) - 1]
    tps = np.cumsum(y)[idx]
    prec = tps / (idx + 1)
    rec = tps / npos
    return float(np.sum(np.diff(np.r_[0.0, rec]) * prec))


def fast_auc(y, s):
    from scipy.stats import rankdata
    s = np.where(np.isfinite(s), s, -1e18)
    n1 = y.sum()
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


class Origins:
    """Struktur per origin untuk bootstrap berpasangan (satu horizon)."""

    def __init__(self, d, h):
        self.d = d.reset_index(drop=True)
        self.h = h
        self.uo = np.sort(self.d["origin"].unique())
        inv = np.searchsorted(self.uo, self.d["origin"].to_numpy())
        self.rows = [np.where(inv == i)[0] for i in range(len(self.uo))]
        self.inv = inv
        self.idx = boot_idx(len(self.uo), h)

    def per_origin_sum(self, v):
        out = np.zeros(len(self.uo))
        np.add.at(out, self.inv, np.asarray(v, float))
        return out

    def boot_ratio(self, num, den):
        n, m = self.per_origin_sum(num), self.per_origin_sum(den)
        return n[self.idx].sum(1) / m[self.idx].sum(1)

    def boot_ap(self, y, s):
        y, s = np.asarray(y, int), np.asarray(s, float)
        out = np.empty(len(self.idx))
        for r, ii in enumerate(self.idx):
            sel = np.concatenate([self.rows[i] for i in ii])
            out[r] = fast_ap(y[sel], s[sel])
        return out

    def boot_origin_mean(self, per_origin_vals):
        v = np.asarray(per_origin_vals, float)
        return np.array([np.nanmean(v[ii]) for ii in self.idx])


def flags_k(d, score, k):
    return top_flags(d, score, ["origin", "province_id"], k=k, seed=SEED).to_numpy()


def flags_eq(d, score):
    n = d.groupby("origin")["province_id"].nunique() * 2
    return top_flags(d, score, ["origin"], n=n, seed=SEED)


def ap_per_origin(d, z, s):
    return np.array([fast_ap(g[z].to_numpy(int), g[s].to_numpy(float)) for _, g in d.groupby("origin", sort=True)])


def ranking(d, s, z):
    y = d[z].to_numpy(int)
    r = {"score": s, "target": z, "n": len(d), "n_pos": int(y.sum()), "base_rate": float(y.mean()),
         "ap": fast_ap(y, d[s].to_numpy(float)), "ap_origin_mean": float(np.nanmean(ap_per_origin(d, z, s))),
         "roc_auc": fast_auc(y, d[s].to_numpy(float))}
    no = d["origin"].nunique()
    for k in (1, 2, 3):
        f = flags_k(d, s, k)
        hit = f & (y == 1)
        r.update({f"prec_k{k}": hit.sum() / f.sum(), f"rec_k{k}": hit.sum() / max(y.sum(), 1), f"alarms_k{k}": f.sum() / no,
                  f"tp_k{k}": hit.sum() / no, f"fp_k{k}": (f.sum() - hit.sum()) / no, f"fn_k{k}": (y.sum() - hit.sum()) / no})
    f = flags_eq(d, s).to_numpy()
    r.update({"prec_v2eq": (f & (y == 1)).sum() / f.sum(), "rec_v2eq": (f & (y == 1)).sum() / max(y.sum(), 1),
              "prov_alarm_v2eq": float(d.assign(f=f).groupby("origin").apply(lambda g: g.loc[g["f"], "province_id"].nunique(),
                                                                               include_groups=False).mean())})
    return r


def paired(O, a, b, z, metrics=("ap", "prec_k2")):
    """Δ (a − b) + interval & p bootstrap berpasangan untuk metrik ranking."""
    d = O.d
    y = d[z].to_numpy(int)
    out = []
    for m in metrics:
        if m == "ap":
            va, vb = fast_ap(y, d[a].to_numpy(float)), fast_ap(y, d[b].to_numpy(float))
            bd = O.boot_ap(y, d[a]) - O.boot_ap(y, d[b])
        elif m == "ap_origin_mean":
            pa, pb = ap_per_origin(d, z, a), ap_per_origin(d, z, b)
            va, vb = np.nanmean(pa), np.nanmean(pb)
            bd = O.boot_origin_mean(pa - pb)
        elif m.startswith("prec_k"):
            k = int(m[-1])
            fa, fb = flags_k(d, a, k), flags_k(d, b, k)
            va, vb = (fa & (y == 1)).sum() / fa.sum(), (fb & (y == 1)).sum() / fb.sum()
            bd = O.boot_ratio(fa & (y == 1), fa) - O.boot_ratio(fb & (y == 1), fb)
        out.append({"horizon": O.h, "target": z, "metric": m, "a": a, "b": b, "value_a": va, "value_b": vb, "diff": va - vb,
                    "lo": float(np.nanpercentile(bd, 2.5)), "hi": float(np.nanpercentile(bd, 97.5)),
                    "p": bootstrap_p(bd, 0.0)})
    return out


def prob_metrics(O, s, z, ref="clim_e80"):
    d = O.d
    y, p, c = d[z].to_numpy(float), d[s].to_numpy(float), d[ref].to_numpy(float)
    bm, bc = (p - y) ** 2, (c - y) ** 2
    bss_b = 1 - O.per_origin_sum(bm)[O.idx].sum(1) / O.per_origin_sum(bc)[O.idx].sum(1)
    return {"horizon": O.h, "score": s, "target": z, "n": len(d), "base_rate": y.mean(), "mean_p": p.mean(), "brier": brier(y, p),
            "logloss": logloss(y, p), "ece": ece(y, p), "bss_vs_" + ref: 1 - bm.sum() / bc.sum(),
            "bss_lo": float(np.percentile(bss_b, 2.5)), "bss_hi": float(np.percentile(bss_b, 97.5))}


def paired_brier(O, a, b, z):
    d = O.d
    y = d[z].to_numpy(float)
    da, db = (d[a].to_numpy(float) - y) ** 2, (d[b].to_numpy(float) - y) ** 2
    n = O.per_origin_sum(np.ones(len(d)))
    bd = (O.per_origin_sum(da)[O.idx].sum(1) - O.per_origin_sum(db)[O.idx].sum(1)) / n[O.idx].sum(1)
    return {"horizon": O.h, "target": z, "metric": "brier", "a": a, "b": b, "value_a": da.mean(), "value_b": db.mean(),
            "diff": da.mean() - db.mean(), "lo": float(np.percentile(bd, 2.5)), "hi": float(np.percentile(bd, 97.5)),
            "p": bootstrap_p(bd, 0.0)}


# ---------------------------------------------------------------- data
def load():
    P = pd.read_parquet(os.path.join(EXP, "k4_dev_preds.parquet")).assign(part="dev")
    if PART == "test":
        Q = pd.read_parquet(os.path.join(EXP, "k4_test_preds.parquet")).assign(part="test")
        assert (Q["origin"] >= "2024-01-01").all()
        P = pd.concat([P, Q], ignore_index=True)
    P["R_mom"], P["R_nat"], P["R_rev"], P["R_seas"] = P["lag_dp_4"], P["nat_dp_4"], -P["dev_ma13"], P["yseas_52"]
    out = []
    for h in H:
        d = P[P["horizon"] == h].sort_values(["origin", "province_id", "commodity"]).reset_index(drop=True)
        for s, z, name in (("c1t", "z_e80", "c1t_cal"), ("k4_e80", "z_e80", "k4_e80_cal"),
                           ("c1t", "z_a80", "c1t_cal_any"), ("k4_a80", "z_a80", "k4_a80_cal")):
            d[name] = platt_walkforward(d, s, z, h)
        out.append(d)
    P = pd.concat(out, ignore_index=True)
    return P[P["part"] == PART].reset_index(drop=True)


if __name__ == "__main__":
    D = load()
    # sanity AP cepat = sklearn
    from sklearn.metrics import average_precision_score, roc_auc_score
    chk = D[D["horizon"] == 4]
    assert abs(fast_ap(chk["z_e80"].to_numpy(int), chk["k4_e80"].to_numpy()) - average_precision_score(chk["z_e80"], chk["k4_e80"])) < 1e-12
    assert abs(fast_ap(chk["z_e80"].to_numpy(int), chk["clim_e80"].to_numpy()) - average_precision_score(chk["z_e80"], chk["clim_e80"])) < 1e-12
    assert abs(fast_auc(chk["z_e80"].to_numpy(int), chk["k4_e80"].to_numpy()) - roc_auc_score(chk["z_e80"], chk["k4_e80"])) < 1e-12

    RANK, PAIR, PROB, REL = [], [], [], []
    dec = {"part": PART}
    SC_MAIN = ["k4_e80", "c1t", "clim_e80", "clims_e80"] + NAIVE
    best_naive = {}
    if PART == "test":
        best_naive = {int(k): v for k, v in json.load(open(os.path.join(OUT, "k4_decision.json")))["best_naive"].items()}
    Ostore = {}
    for h in H:
        d = D[D["horizon"] == h].reset_index(drop=True)
        O = Origins(d, h)
        Ostore[h] = O
        for s in SC_MAIN + ["k4_a80"]:
            RANK.append({"horizon": h, **ranking(d, s, "z_e80")})
        rk = pd.DataFrame([r for r in RANK if r["horizon"] == h and r["target"] == "z_e80"]).set_index("score")
        if PART == "dev":
            best_naive[h] = rk.loc[["clim_e80", "clims_e80"] + NAIVE, "ap"].idxmax()
        bn = best_naive[h]
        PAIR += paired(O, "k4_e80", "c1t", "z_e80", ("ap", "ap_origin_mean", "prec_k1", "prec_k2", "prec_k3"))
        PAIR += paired(O, "k4_e80", bn, "z_e80", ("ap", "prec_k2"))
        for b in ("clim_e80", "clims_e80"):
            if b != bn:
                PAIR += paired(O, "k4_e80", b, "z_e80", ("ap", "prec_k2"))
        PAIR += paired(O, "c1t", bn, "z_e80", ("ap", "prec_k2"))
        # stabilitas per tahun
        for yr, g in d.groupby(d["origin"].dt.year):
            dec.setdefault("year_dap", {}).setdefault(h, {})[int(yr)] = (
                fast_ap(g["z_e80"].to_numpy(int), g["k4_e80"].to_numpy()) - fast_ap(g["z_e80"].to_numpy(int), g["c1t"].to_numpy()))
        # peluang (himpunan origin dengan kalibrator)
        dp = d[d["c1t_cal"].notna() & d["k4_e80_cal"].notna()].reset_index(drop=True)
        OP = Origins(dp, h)
        for s in ("k4_e80", "k4_e80_cal", "c1t_cal", "clim_e80", "clims_e80"):
            PROB.append(prob_metrics(OP, s, "z_e80"))
            rel = reliability(dp["z_e80"], dp[s]).reset_index()
            REL.append(rel.assign(horizon=h, score=s, target="z_e80"))
        PAIR.append(paired_brier(OP, "k4_e80", "c1t_cal", "z_e80"))
        PAIR.append(paired_brier(OP, "k4_e80_cal", "c1t_cal", "z_e80"))
        PAIR.append(paired_brier(OP, "k4_e80", "clims_e80", "z_e80"))
        dec.setdefault("prob_origins", {})[h] = int(dp["origin"].nunique())
        # target kejadian (Fase E)
        for s in ("k4_a80", "k4_e80", "c1t", "clim_a80", "clims_a80") + tuple(NAIVE):
            RANK.append({"horizon": h, **ranking(d, s, "z_a80")})
        PAIR += paired(O, "k4_a80", "c1t", "z_a80", ("ap", "prec_k2"))
        PAIR += paired(O, "k4_a80", "k4_e80", "z_a80", ("ap", "prec_k2"))
        PAIR += paired(O, "k4_a80", "clims_a80", "z_a80", ("ap", "prec_k2"))
        dpa = d[d["c1t_cal_any"].notna() & d["k4_a80_cal"].notna()].reset_index(drop=True)
        OPA = Origins(dpa, h)
        for s in ("k4_a80", "k4_a80_cal", "c1t_cal_any", "clim_a80", "clims_a80"):
            PROB.append(prob_metrics(OPA, s, "z_a80", ref="clim_a80"))
        PAIR.append(paired_brier(OPA, "k4_a80", "c1t_cal_any", "z_a80"))
        # kepekaan definisi target
        for key in ("e70", "e90", "s90"):
            for s in (f"k4_{key}", "c1t", f"clim_{key}", f"clims_{key}"):
                RANK.append({"horizon": h, **ranking(d, s, f"z_{key}")})
            PAIR += paired(O, f"k4_{key}", "c1t", f"z_{key}", ("ap", "prec_k2"))
            PAIR += paired(O, f"k4_{key}", f"clims_{key}", f"z_{key}", ("ap", "prec_k2"))
        print("h", h, "selesai metrik utama", flush=True)

    RK, PR, PB = pd.DataFrame(RANK), pd.DataFrame(PAIR), pd.DataFrame(PROB)
    RK.round(5).to_csv(os.path.join(OUT, f"k4{SFX}_ranking.csv"), index=False)
    PB.round(5).to_csv(os.path.join(OUT, f"k4{SFX}_probability.csv"), index=False)
    pd.concat(REL).round(5).to_csv(os.path.join(OUT, f"k4{SFX}_reliability.csv"), index=False)

    # ---------------- keputusan §5
    fam = PR[(PR["a"] == "k4_e80") & (PR["target"] == "z_e80") & (
        ((PR["b"] == "c1t") & PR["metric"].isin(["ap", "prec_k2"])) | ((PR["b"] == "c1t_cal") & (PR["metric"] == "brier")))]
    q = bh_fdr(fam["p"].to_numpy(float))
    PR["q_famF"] = np.nan
    PR.loc[fam.index, "q_famF"] = q
    famc = PR[((PR["a"] == "k4_e80") & (PR["b"] == "c1t") & PR["metric"].isin(["ap", "prec_k2"]) & (PR["target"] == "z_e80"))
              | ((PR["a"] == "k4_e80_cal") & (PR["b"] == "c1t_cal"))]
    PR["q_famF_cal"] = np.nan
    PR.loc[famc.index, "q_famF_cal"] = bh_fdr(famc["p"].to_numpy(float))
    PR.round(5).to_csv(os.path.join(OUT, f"k4{SFX}_paired.csv"), index=False)

    def g(a, b, m, h, z="z_e80"):
        return PR[(PR["a"] == a) & (PR["b"] == b) & (PR["metric"] == m) & (PR["horizon"] == h) & (PR["target"] == z)].iloc[0]

    ap_ = {h: g("k4_e80", "c1t", "ap", h) for h in H}
    pk_ = {h: g("k4_e80", "c1t", "prec_k2", h) for h in H}
    ci_pos = [h for h in H if ap_[h]["lo"] > 0]
    r1 = (len(ci_pos) >= 1 and all(ap_[h]["diff"] >= 0 for h in H) and all(pk_[h]["diff"] >= 0 for h in H)
          and all(ap_[h]["q_famF"] < 0.05 for h in ci_pos))
    if PART == "dev":
        r1 = r1 and all(sum(v >= 0 for v in dec["year_dap"][h].values()) >= 2 for h in H)
    r1b = all(g("k4_e80", best_naive[h], m, h)["diff"] >= 0 for h in H for m in ("ap", "prec_k2"))
    pbx = PB.set_index(["horizon", "score", "target"])

    def r2_for(s, qcol):
        br = {h: g(s, "c1t_cal", "brier", h) for h in H}
        ok = (any(br[h]["hi"] < 0 for h in H) and all(br[h]["diff"] <= 0 for h in H)
              and all(pbx.loc[(h, s, "z_e80"), "ece"] <= 0.05 for h in H)
              and all(pbx.loc[(h, s, "z_e80"), "bss_lo"] > 0 for h in H))
        return ok, {h: {"dbrier": br[h]["diff"], "lo": br[h]["lo"], "hi": br[h]["hi"], "q": br[h][qcol],
                        "ece": pbx.loc[(h, s, "z_e80"), "ece"], "bss": pbx.loc[(h, s, "z_e80"), "bss_vs_clim_e80"],
                        "bss_lo": pbx.loc[(h, s, "z_e80"), "bss_lo"]} for h in H}

    r2_raw, det_raw = r2_for("k4_e80", "q_famF")
    r2_cal, det_cal = r2_for("k4_e80_cal", "q_famF_cal")
    r2 = r2_raw or r2_cal
    sel_prob = "k4_e80" if r2_raw else ("k4_e80_cal" if r2_cal else None)
    decision = "ACCEPT" if (r1 and r1b and r2) else ("PARTIAL" if ((r1 and r1b) or r2) else "REJECT")
    dec.update({"best_naive": best_naive, "R1": bool(r1), "R1b": bool(r1b), "R2_raw": bool(r2_raw), "R2_cal": bool(r2_cal),
                "selected_prob_variant": sel_prob, "decision_technical": decision, "operational_status": "BLOCKED (U109)",
                "R1_detail": {h: {"dAP": ap_[h]["diff"], "lo": ap_[h]["lo"], "hi": ap_[h]["hi"], "q": ap_[h]["q_famF"],
                                  "dPrecK2": pk_[h]["diff"], "pk_lo": pk_[h]["lo"], "pk_hi": pk_[h]["hi"]} for h in H},
                "R2_raw_detail": det_raw, "R2_cal_detail": det_cal})
    with open(os.path.join(OUT, f"k4{SFX}_decision.json"), "w", encoding="utf-8") as f:
        json.dump(dec, f, indent=1, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x))
    if PART == "dev" and decision in ("ACCEPT", "PARTIAL"):
        open(os.path.join(OUT, "k4_test_allowed.flag"), "w").write(f"{decision} {sel_prob}\n")
    print(json.dumps(dec, indent=1, default=str), flush=True)

    # ---------------- operasional (§3): kebijakan K & ambang peluang
    OPS, SHARE, TAU = [], [], []
    for h in H:
        d = Ostore[h].d
        y = d["z_e80"].to_numpy(int)
        for s in ("k4_e80", "c1t", best_naive[h], "clim_e80", "clims_e80"):
            for k in (1, 2, 3):
                f = flags_k(d, s, k)
                dd = d.assign(f=f, hit=f & (y == 1))
                prev = dd[dd["f"]][["origin", "province_id", "commodity"]].copy()
                uo = np.sort(d["origin"].unique())
                nxt = dict(zip(uo[:-1], uo[1:]))
                prev["origin"] = prev["origin"].map(nxt)
                cur = dd[dd["f"] & (dd["origin"] > uo[0])][["origin", "province_id", "commodity"]]
                persist = len(cur.merge(prev, on=["origin", "province_id", "commodity"])) / max(len(cur), 1)
                no = d["origin"].nunique()
                OPS.append({"horizon": h, "score": s, "policy": f"V1-K{k}", "alarms_per_origin": f.sum() / no,
                            "tp_per_origin": dd["hit"].sum() / no, "fp_per_origin": (f.sum() - dd["hit"].sum()) / no,
                            "fn_per_origin": (y.sum() - dd["hit"].sum()) / no, "precision": dd["hit"].sum() / f.sum(),
                            "recall": dd["hit"].sum() / y.sum(), "share_regulated": dd.loc[dd["f"], "commodity"].isin(REGULATED).mean(),
                            "persistence_prev_origin": persist,
                            "n_commodities_alarmed": dd.loc[dd["f"], "commodity"].nunique()})
                if k == 2:
                    sh = dd[dd["f"]].groupby("commodity").agg(alarms=("f", "size"), hits=("hit", "sum"))
                    pos = d.groupby("commodity")["z_e80"].sum()
                    sh["share"] = sh["alarms"] / sh["alarms"].sum()
                    sh["precision"] = sh["hits"] / sh["alarms"]
                    sh["recall_in_commodity"] = sh["hits"] / pos.reindex(sh.index)
                    SHARE.append(sh.reset_index().assign(horizon=h, score=s))
        dp = d[d["c1t_cal"].notna()]
        yp = dp["z_e80"].to_numpy(int)
        for s in ("k4_e80", "k4_e80_cal", "c1t_cal", "clims_e80"):
            for tau in (0.2, 0.3, 0.4):
                f = dp[s].to_numpy() >= tau
                dd = dp.assign(f=f)
                per = dd.groupby("origin").agg(n=("f", "sum"), prov=("province_id", lambda x: 0))
                prov_with = dd[dd["f"]].groupby("origin")["province_id"].nunique().reindex(per.index).fillna(0)
                nprov = dd.groupby("origin")["province_id"].nunique()
                TAU.append({"horizon": h, "score": s, "tau": tau, "alarms_per_origin": f.sum() / dp["origin"].nunique(),
                            "precision": (f & (yp == 1)).sum() / max(f.sum(), 1), "recall": (f & (yp == 1)).sum() / yp.sum(),
                            "prov_without_alarm_per_origin": float((nprov - prov_with).mean()),
                            "origins_without_alarm": int((per["n"] == 0).sum()), "n_origins": int(len(per)),
                            "alarms_per_origin_sd": float(per["n"].std())})
    pd.DataFrame(OPS).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_ops_policies.csv"), index=False)
    pd.concat(SHARE).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_ops_commodity_share.csv"), index=False)
    pd.DataFrame(TAU).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_ops_tau.csv"), index=False)

    # ---------------- utilitas: kurva keputusan & skenario biaya
    NB, COST = [], []
    for h in H:
        d = Ostore[h].d
        dp = d[d["c1t_cal"].notna()]
        y = dp["z_e80"].to_numpy(int)
        N = len(dp)
        for tau in np.round(np.arange(0.05, 0.51, 0.05), 2):
            w = tau / (1 - tau)
            NB.append({"horizon": h, "score": "pantau_semua", "tau": tau, "net_benefit": y.mean() - (1 - y.mean()) * w})
            for s in ("k4_e80", "k4_e80_cal", "c1t_cal", "clims_e80", "clim_e80"):
                f = dp[s].to_numpy() >= tau
                tp, fp = (f & (y == 1)).sum(), (f & (y == 0)).sum()
                NB.append({"horizon": h, "score": s, "tau": tau, "net_benefit": tp / N - fp / N * w, "alarms_per_origin": f.sum() / dp["origin"].nunique()})
        yall = d["z_e80"].to_numpy(int)
        no = d["origin"].nunique()
        for r in (1, 2, 5, 10):
            COST.append({"horizon": h, "ratio_fn_fp": r, "score": "tanpa_alarm", "policy": "-", "cost_per_origin": r * yall.sum() / no})
            for s in ("k4_e80", "c1t", best_naive[h], "clims_e80"):
                for k in (1, 2, 3):
                    f = flags_k(d, s, k)
                    tp = (f & (yall == 1)).sum()
                    COST.append({"horizon": h, "ratio_fn_fp": r, "score": s, "policy": f"V1-K{k}",
                                 "cost_per_origin": ((f.sum() - tp) + r * (yall.sum() - tp)) / no})
            for s in ("k4_e80_cal", "c1t_cal", "clims_e80"):
                tau = 1 / (1 + r)
                f = dp[s].to_numpy() >= tau
                tp = (f & (y == 1)).sum()
                COST.append({"horizon": h, "ratio_fn_fp": r, "score": s, "policy": f"tau=1/(1+r)={tau:.3f} (himpunan peluang)",
                             "cost_per_origin": ((f.sum() - tp) + r * (y.sum() - tp)) / dp["origin"].nunique()})
    pd.DataFrame(NB).round(5).to_csv(os.path.join(OUT, f"k4{SFX}_utility_netbenefit.csv"), index=False)
    pd.DataFrame(COST).round(3).to_csv(os.path.join(OUT, f"k4{SFX}_utility_cost.csv"), index=False)

    # ---------------- per seri & analisis galat
    PC, PP, PO, ERR = [], [], [], []
    for h in H:
        d = Ostore[h].d
        y = d["z_e80"].to_numpy(int)
        fl = {s: flags_k(d, s, 2) for s in ("k4_e80", "c1t", "clims_e80")}
        for c, gg in d.groupby("commodity"):
            r = {"horizon": h, "commodity": c, "n": len(gg), "base_rate": gg["z_e80"].mean()}
            for s in ("k4_e80", "c1t", "clims_e80"):
                f = fl[s][gg.index]
                r[f"ap_{s}"] = fast_ap(gg["z_e80"].to_numpy(int), gg[s].to_numpy(float))
                r[f"alarms_{s}"] = int(f.sum())
                r[f"prec_{s}"] = (f & (gg["z_e80"].to_numpy() == 1)).sum() / max(f.sum(), 1)
                r[f"rec_{s}"] = (f & (gg["z_e80"].to_numpy() == 1)).sum() / max(gg["z_e80"].sum(), 1)
            PC.append(r)
        for p_, gg in d.groupby("province_id"):
            r = {"horizon": h, "province_id": p_, "base_rate": gg["z_e80"].mean()}
            for s in ("k4_e80", "c1t"):
                f = fl[s][gg.index]
                r[f"prec_{s}"] = (f & (gg["z_e80"].to_numpy() == 1)).sum() / f.sum()
                r[f"rec_{s}"] = (f & (gg["z_e80"].to_numpy() == 1)).sum() / max(gg["z_e80"].sum(), 1)
            PP.append(r)
        for o, gg in d.groupby("origin"):
            r = {"horizon": h, "origin": o, "base_rate": gg["z_e80"].mean(), "mean_k4_e80": gg["k4_e80"].mean()}
            for s in ("k4_e80", "c1t", "clims_e80"):
                f = fl[s][gg.index]
                r[f"ap_{s}"] = fast_ap(gg["z_e80"].to_numpy(int), gg[s].to_numpy(float))
                r[f"prec_{s}"] = (f & (gg["z_e80"].to_numpy() == 1)).sum() / f.sum()
            PO.append(r)
        # galat K4 vs C1t pada V1-K2
        cls = np.select([~d["has_target"], d["z_e80"] == 1, d["y"] > 0, d["y"] < 0], ["hilang", "naik_material", "naik_nonmaterial", "turun"], "tetap")
        near = (d["y"] >= 0.5 * d["thr_e80"]) & (d["z_e80"] == 0)
        flat4 = d["lag_dp_4"].abs() < 1e-12
        for s in ("k4_e80", "c1t"):
            f = fl[s]
            fp = f & (y == 0)
            fn = ~f & (y == 1)
            rnk = d.groupby(["origin", "province_id"])[s].rank(ascending=False, method="first")
            r = {"horizon": h, "score": s, "n_fp": int(fp.sum()), "n_fn": int(fn.sum())}
            for c in ("turun", "tetap", "naik_nonmaterial", "hilang"):
                r[f"fp_share_{c}"] = float((cls[fp] == c).mean())
            r["fp_share_near_miss_ge_half_thr"] = float(near[fp].mean())
            r["fp_share_regulated"] = float(d.loc[fp, "commodity"].isin(REGULATED).mean())
            r["fn_share_regulated"] = float(d.loc[fn, "commodity"].isin(REGULATED).mean())
            r["fn_share_flat_prev4w"] = float(flat4[fn].mean())
            r["tp_share_flat_prev4w"] = float(flat4[f & (y == 1)].mean())
            r["fn_rank_median"] = float(rnk[fn].median())
            r["fn_rank_ge6_share"] = float((rnk[fn] >= 6).mean())
            ERR.append(r)
        a, b = fl["k4_e80"], fl["c1t"]
        ERR.append({"horizon": h, "score": "overlap_k4_c1t", "jaccard_alarms": float((a & b).sum() / (a | b).sum()),
                    "hits_only_k4": int((a & ~b & (y == 1)).sum()), "hits_only_c1t": int((b & ~a & (y == 1)).sum()),
                    "hits_both": int((a & b & (y == 1)).sum())})
        # presisi menurut tersil laju-dasar origin (pergeseran base rate)
        po = pd.DataFrame([r for r in PO if r["horizon"] == h])
        po["tercile"] = pd.qcut(po["base_rate"], 3, labels=["rendah", "sedang", "tinggi"])
        for t_, gg in po.groupby("tercile", observed=True):
            ERR.append({"horizon": h, "score": f"origin_base_rate_{t_}", "base_rate_mean": gg["base_rate"].mean(),
                        "prec_k4_e80": gg["prec_k4_e80"].mean(), "prec_c1t": gg["prec_c1t"].mean(),
                        "mean_p_k4_e80": gg["mean_k4_e80"].mean()})
    pd.DataFrame(PC).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_per_commodity.csv"), index=False)
    pd.DataFrame(PP).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_per_province.csv"), index=False)
    pd.DataFrame(PO).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_per_origin.csv"), index=False)
    pd.DataFrame(ERR).round(4).to_csv(os.path.join(OUT, f"k4{SFX}_errors.csv"), index=False)
    pd.set_option("display.width", 250)
    cols = ["horizon", "score", "target", "base_rate", "ap", "ap_origin_mean", "roc_auc", "prec_k1", "prec_k2", "prec_k3", "rec_k2", "prec_v2eq"]
    print(RK[cols].round(4).to_string(index=False))
    print(PR.round(4).to_string(index=False))
    print(PB.round(4).to_string(index=False))
