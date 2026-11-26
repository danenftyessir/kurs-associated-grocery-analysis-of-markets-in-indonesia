"""D-163a: kalibrasi walk-forward skor daftar pantau C1-tuned (protokol ../PROTOKOL.md, dibekukan sebelum diukur).

PART=dev (default): K1 Platt global, K2 Platt + intersep komoditas, K3 isotonik global vs C1-tuned tanpa kalibrasi; keputusan
menurut protokol -> hasil/kal_decision.json. PART=test: hanya varian terpilih (dibuka sekali; bukan validasi independen, D-155).
Data & definisi S1/S2 = `20261125_business_understanding/scripts/bu.py` (p_up = `d151_iw_*_preds` varian base = C1t resmi).
-> hasil/kal_{dev|test}.csv, kal_reliability_{varian}_h{h}{_test}.csv, kal_decision.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_business_understanding", "scripts"))
import bu  # noqa: E402  (top_flags, boot_idx, EXP, cfg, PCT, K; menambah path engine/kg/p_exp)
from bu import LAG_COLUMNS, np, pd  # noqa: E402
from engine import stats_from  # noqa: E402
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
PART = os.environ.get("PART", "dev")
SFX = "" if PART == "dev" else "_test"
MIN_ORIGINS, EPS = 6, 1e-3
KINDS = ["K1", "K2", "K3"]


def logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def fit_apply(kind, tr, te, comms):
    y = (tr["y_true"] > 0).astype(int).to_numpy()
    if kind == "K3":
        iso = IsotonicRegression(y_min=EPS, y_max=1 - EPS, out_of_bounds="clip").fit(tr["p_up"], y)
        return iso.predict(te["p_up"])

    def X(d):
        x = logit(d["p_up"])[:, None]
        if kind == "K2":
            x = np.column_stack([x, (d["commodity"].to_numpy()[:, None] == np.array(comms)[None, 1:]).astype(float)])
        return x
    m = LogisticRegression(C=1e6, max_iter=2000).fit(X(tr), y)
    return m.predict_proba(X(te))[:, 1]


def calibrate(P, h, kind):
    """Walk-forward: origin o memakai baris origin o' dengan o' + h <= o dan y != 0 (>= MIN_ORIGINS origin)."""
    d = P[P["horizon"] == h]
    out, active = d["p_up"].copy(), pd.Series(False, index=d.index)
    comms = sorted(d["commodity"].unique())
    lag = pd.Timedelta(weeks=h)
    for o in sorted(d["origin"].unique()):
        tr = d[(d["origin"] + lag <= o) & (d["y_true"] != 0)]
        if tr["origin"].nunique() < MIN_ORIGINS:
            continue
        idx = d.index[d["origin"] == o]
        out.loc[idx] = fit_apply(kind, tr, d.loc[idx], comms)
        active.loc[idx] = True
    return out, active


def thresholds(tab, preds):
    rows = []
    for h in (4, 8):
        t = tab[["week", "commodity", f"y_{h}"] + LAG_COLUMNS].dropna(subset=[f"y_{h}"] + LAG_COLUMNS)
        for o in sorted(preds.loc[preds["horizon"] == h, "origin"].unique()):
            tr = t[t["week"] + pd.Timedelta(weeks=h) <= o]
            thr = tr.groupby("commodity")[f"y_{h}"].apply(lambda s: np.nanpercentile(s.abs(), bu.PCT))
            clim = tr[tr[f"y_{h}"] != 0].groupby("commodity")[f"y_{h}"].apply(lambda s: (s > 0).mean())
            rows.append(pd.DataFrame({"origin": o, "horizon": h, "commodity": thr.index, "thr": thr.values,
                                      "clim_up": clim.reindex(thr.index).values}))
    return pd.concat(rows, ignore_index=True)


def ece_table(p, y):
    bins = np.clip((p * 10).astype(int), 0, 9)
    cal = pd.DataFrame({"b": bins, "p": p, "y": y}).groupby("b").agg(p=("p", "mean"), y=("y", "mean"), n=("y", "size"))
    return float((cal["n"] * (cal["p"] - cal["y"]).abs()).sum() / cal["n"].sum()), cal


def metrics(D, h, score, base_score="p_up"):
    d = D[(D["horizon"] == h)]
    s2 = d[(d["y_true"] != 0)].dropna(subset=["clim_up"])
    y = (s2["y_true"] > 0).astype(float).to_numpy()
    p, pb, pc = s2[score].to_numpy(), s2[base_score].to_numpy(), s2["clim_up"].to_numpy()
    uo, inv = np.unique(s2["origin"].to_numpy(), return_inverse=True)
    S = np.zeros((len(uo), 3))
    for j, v in enumerate(((p - y) ** 2, (pb - y) ** 2, (pc - y) ** 2)):
        np.add.at(S[:, j], inv, v)
    idx = bu.boot_idx(len(uo), h)
    Sb = S[idx].sum(1)
    n_o = np.bincount(inv, minlength=len(uo))[idx].sum(1)
    dbr = (Sb[:, 0] - Sb[:, 1]) / n_o
    bss_b = 1 - Sb[:, 0] / Sb[:, 2]
    ece, cal = ece_table(p, y)
    # S1 V1: 2 teratas per provinsi per origin, presisi kenaikan material
    uo1 = np.sort(d["origin"].unique())
    idx1 = bu.boot_idx(len(uo1), h)
    prec = {}
    for sc in (score, base_score):
        fl = bu.top_flags(d, sc, ["origin", "province_id"], k=2, seed=154)
        g = d.assign(fl=fl, hit=fl & d["mat_up"]).groupby("origin")
        prec[sc] = pd.DataFrame({"n": g["fl"].sum(), "hit": g["hit"].sum()}).reindex(uo1)
    a, b = prec[score], prec[base_score]
    dprec_b = (a["hit"].to_numpy()[idx1].sum(1) / a["n"].to_numpy()[idx1].sum(1)
               - b["hit"].to_numpy()[idx1].sum(1) / b["n"].to_numpy()[idx1].sum(1))
    up, pu = y > 0.5, p > 0.5
    f1 = stats_from(np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float))["macro_f1"]
    return {"ece": ece, "brier": float(((p - y) ** 2).mean()), "d_brier": float(((p - y) ** 2).mean() - ((pb - y) ** 2).mean()),
            "d_brier_lo": float(np.percentile(dbr, 2.5)), "d_brier_hi": float(np.percentile(dbr, 97.5)),
            "bss": float(1 - S[:, 0].sum() / S[:, 2].sum()), "bss_lo": float(np.percentile(bss_b, 2.5)),
            "s1_prec": float(a["hit"].sum() / a["n"].sum()), "d_s1_prec": float(a["hit"].sum() / a["n"].sum() - b["hit"].sum() / b["n"].sum()),
            "d_s1_lo": float(np.percentile(dprec_b, 2.5)), "d_s1_hi": float(np.percentile(dprec_b, 97.5)),
            "macro_f1_05": float(f1), "n_s2": int(len(s2))}, cal


if __name__ == "__main__":
    tab = pd.read_parquet(os.path.join(bu.EXP, "iw2.parquet"))
    dev = pd.read_parquet(os.path.join(bu.EXP, "d151_iw_dev_preds.parquet"))
    dev = dev[(dev["variant"] == "base") & np.isfinite(dev["y_true"])]
    if PART == "test":
        dec = json.load(open(os.path.join(OUT, "kal_decision.json"), encoding="utf-8"))
        kinds = [dec["chosen"]] if dec.get("chosen") else []
        if not kinds:
            raise SystemExit("tidak ada varian terpilih di dev -> test tidak dibuka (PROTOKOL)")
        tst = pd.read_parquet(os.path.join(bu.EXP, "d151_iw_test_preds.parquet"))
        tst = tst[(tst["variant"] == "base") & np.isfinite(tst["y_true"])]
        assert (tst["origin"] >= "2024-01-01").all()
        P = pd.concat([dev, tst], ignore_index=True)
    else:
        kinds, P = KINDS, dev.reset_index(drop=True)
    P = P.reset_index(drop=True)
    for kind in kinds:
        P["p_" + kind], P["act_" + kind] = np.nan, False
        for h in (4, 8):
            s, a = calibrate(P, h, kind)
            P.loc[s.index, "p_" + kind], P.loc[a.index, "act_" + kind] = s, a
    if PART == "test":
        P = P[P["origin"] >= "2024-01-01"]
    TH = thresholds(tab, P)
    D = P.merge(TH, on=["origin", "horizon", "commodity"], how="left")
    D["mat_up"] = D["y_true"] >= D["thr"]
    rows = []
    for h in (4, 8):
        m0, cal0 = metrics(D, h, "p_up")
        rows.append({"horizon": h, "variant": "C1t", "active_share": 0.0, **m0})
        cal0.assign(horizon=h, variant="C1t").to_csv(os.path.join(OUT, f"kal_reliability_C1t_h{h}{SFX}.csv"))
        for kind in kinds:
            m, cal = metrics(D, h, "p_" + kind)
            act = D.loc[D["horizon"] == h, "act_" + kind].mean()
            rows.append({"horizon": h, "variant": kind, "active_share": float(act), **m})
            cal.assign(horizon=h, variant=kind).to_csv(os.path.join(OUT, f"kal_reliability_{kind}_h{h}{SFX}.csv"))
    R = pd.DataFrame(rows)
    R.round(5).to_csv(os.path.join(OUT, f"kal_{PART}.csv"), index=False)
    pd.set_option("display.width", 240)
    print(R.round(4).to_string(index=False))
    if PART == "dev":
        ok = {}
        for kind in KINDS:
            r = R[R["variant"] == kind].set_index("horizon")
            ok[kind] = bool((r["ece"] <= 0.05).all() and (r["d_brier"] < 0).all() and (r["d_brier_hi"] <= 0).any()
                            and (r["d_s1_prec"] >= -0.005).all())
        chosen = next((k for k in ("K1", "K3", "K2") if ok[k]), None)
        json.dump({"pass": ok, "chosen": chosen, "protocol_sha256": "e0b50c8f26e42d60cb4bf26a51368b6de3d865124451cb14c274ad43e659c521"},
                  open(os.path.join(OUT, "kal_decision.json"), "w", encoding="utf-8"), indent=1)
        print("lolos:", ok, "terpilih:", chosen)
