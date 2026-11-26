"""D-156: evaluasi semua kandidat vs `base` (C1t) di origin pengembangan sesuai PROTOKOL.md §4–§5.

Membaca checkpoint EXP/d156/main (+ combo bila ada). Varian threshold walk-forward (D_thr_wf, D_thr_wf_comm) diturunkan dari prediksi
`base`: skor digeser (score − t + 0,5) sehingga semua metrik memakai threshold 0,5.
Keluaran hasil/e_metrics.csv, e_paired.csv, e_per_commodity.csv, e_per_year.csv, e_decision.csv, e_combo_selection.json,
e_du_concordance.csv; mode SELECT_COMBO=1 hanya menulis e_combo_selection.json (stage 1 C_COMBO).
"""
import glob
import json

from m_common import EXP, H, OUT, bh_fdr, mf1, np, official_c1t, os, pd, summary  # (mengatur sys.path → evalx)
from c_feats import FAMILIES
from evalx import paired_diff, per_commodity

SPLIT = pd.Timestamp("2022-07-01")            # dev-awal < SPLIT ≤ dev-akhir (C_COMBO)
GRID = np.round(np.arange(0.30, 0.7001, 0.005), 3)
NOT_SELECTABLE = {"E_lr"}
DAILY = {"C_D2"}


def load(stage):
    fs = sorted(glob.glob(os.path.join(EXP, "d156", stage, "*.parquet")))
    if not fs:
        return pd.DataFrame()
    r = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return r[np.isfinite(r["y_true"])]


def best_thr(y, s):
    vals = np.array([mf1(y, s, t) for t in GRID])
    ok = GRID[vals >= np.nanmax(vals) - 1e-12]
    return float(ok[np.argmin(np.abs(ok - 0.5))])


def walk_forward(b, h, by_commodity):
    out = []
    for o, g in b.groupby("origin"):
        prior = b[(b["origin"] + pd.Timedelta(weeks=h) <= o) & (b["y_true"] != 0)]
        t_glob = best_thr(prior["y_true"], prior["score"]) if prior["origin"].nunique() >= 4 else 0.5
        g = g.copy()
        if by_commodity:
            thr = {}
            for c in g["commodity"].unique():
                pc = prior[prior["commodity"] == c]
                thr[c] = best_thr(pc["y_true"], pc["score"]) if len(pc) >= 300 and prior["origin"].nunique() >= 4 else t_glob
            t = g["commodity"].map(thr).to_numpy()
        else:
            t = t_glob
        g["score"] = g["score"] - t + 0.5
        g["thr"] = t
        out.append(g)
    return pd.concat(out)


def compare(v, b, h):
    """Δ vs base pada baris & origin yang sama."""
    st, sb = summary(v, h), summary(b, h, ci=False)
    d = paired_diff(v, b, 0.5, 0.5, h)
    nzb = b[b["y_true"] != 0]
    thr_small = nzb["y_true"].abs().quantile(0.2)
    vs, bs = v[(v["y_true"] != 0) & (v["y_true"].abs() <= thr_small)], b[(b["y_true"] != 0) & (b["y_true"].abs() <= thr_small)]
    ds = paired_diff(vs, bs, 0.5, 0.5, h)
    po = []
    for o in sorted(b["origin"].unique()):
        vo, bo = v[(v["origin"] == o) & (v["y_true"] != 0)], b[(b["origin"] == o) & (b["y_true"] != 0)]
        po.append(mf1(vo["y_true"], vo["score"]) - mf1(bo["y_true"], bo["score"]))
    years = {}
    for yr in (2021, 2022, 2023):
        vo, bo = v[v["origin"].dt.year == yr], b[b["origin"].dt.year == yr]
        if len(bo):
            years[yr] = mf1(vo["y_true"], vo["score"]) - mf1(bo["y_true"], bo["score"])
    pc_v, pc_b = per_commodity(v, 0.5), per_commodity(b, 0.5)
    pcd = {c: pc_v[c] - pc_b[c] for c in pc_b}
    row = {"macro_f1": st["macro_f1"], "macro_f1_lo": st["macro_f1_lo"], "macro_f1_hi": st["macro_f1_hi"],
           "f1_up": st["f1_up"], "f1_down": st["f1_down"], "mcc": st["mcc"], "roc_auc": st.get("roc_auc", np.nan),
           "share_up_pred": st["share_up_pred"], "origin_f1_mean": st["origin_f1_mean"], "origin_f1_sd": st["origin_f1_sd"],
           "diff": d["diff"], "lo": d["lo"], "hi": d["hi"], "p": d["p"], "n": d["n"],
           "d_f1_up": st["f1_up"] - sb["f1_up"], "d_f1_down": st["f1_down"] - sb["f1_down"],
           "d_q1_small": ds["diff"], "lo_q1_small": ds["lo"], "hi_q1_small": ds["hi"],
           "share_origins_pos": float(np.mean(np.array(po) > 0)), "n_origins": len(po),
           "years_nonneg": int(sum(x >= 0 for x in years.values())),
           **{f"d_{yr}": x for yr, x in years.items()},
           "worst_commodity": min(pcd, key=pcd.get), "worst_commodity_diff": min(pcd.values())}
    return row, pcd


if __name__ == "__main__":
    R = load("main")
    base_all = R[R["variant"] == "base"]
    off = official_c1t("dev")
    chk = base_all.merge(off, on=["origin", "horizon", "province_id", "commodity"], suffixes=("", "_off"))
    print(f"cek base vs direction_tuned_preds C1t: {len(chk)} baris, maks |Δp| {np.abs(chk['score'] - chk['score_off']).max():.2e}",
          f"(baris base {len(base_all)}, resmi dev {len(off)})", flush=True)
    assert len(chk) == len(off) and np.abs(chk["score"] - chk["score_off"]).max() == 0

    if os.environ.get("SELECT_COMBO") == "1":
        sel = {}
        for f in FAMILIES:
            ds = []
            for h in H:
                e = R[(R["horizon"] == h) & (R["origin"] < SPLIT)]
                v, b = e[e["variant"] == f"C_{f}"], e[e["variant"] == "base"]
                ds.append(mf1(v["y_true"], v["score"]) - mf1(b["y_true"], b["score"]))
            sel[f] = {"d_h4": ds[0], "d_h8": ds[1], "mean": float(np.mean(ds)), "selected": bool(np.mean(ds) > 0)}
        json.dump(sel, open(os.path.join(OUT, "e_combo_selection.json"), "w"), indent=1)
        print(json.dumps(sel, indent=1))
        print("COMBO_FAMS=" + ",".join(f for f, s in sel.items() if s["selected"]))
        raise SystemExit(0)

    rows, pcs = [], []
    for h in H:
        Rh = R[R["horizon"] == h]
        b = Rh[Rh["variant"] == "base"]
        cands = {v: Rh[Rh["variant"] == v] for v in Rh["variant"].unique() if v != "base"}
        cands["D_thr_wf"] = walk_forward(b, h, False)
        cands["D_thr_wf_comm"] = walk_forward(b, h, True)
        rb, _ = compare(b, b, h)
        rows.append({"variant": "base", "horizon": h, "scope": "dev", **rb})
        for name, v in sorted(cands.items()):
            r, pcd = compare(v, b, h)
            if name.startswith("D_thr"):
                r["thr_mean"] = float(np.mean(v.drop_duplicates(["origin", "commodity"])["thr"]))
            rows.append({"variant": name, "horizon": h, "scope": "dev", **r})
            pcs += [{"variant": name, "horizon": h, "commodity": c, "diff": x} for c, x in pcd.items()]
            print(h, name, round(r["diff"], 4), flush=True)
    C = load("combo")
    if len(C):
        for h in H:
            Ch = C[(C["horizon"] == h) & (C["origin"] >= SPLIT)]
            b, v = Ch[Ch["variant"] == "base"], Ch[Ch["variant"] == "C_COMBO"]
            r, pcd = compare(v, b, h)
            rows.append({"variant": "C_COMBO", "horizon": h, "scope": "dev_late", **r})
            pcs += [{"variant": "C_COMBO", "horizon": h, "commodity": c, "diff": x} for c, x in pcd.items()]
            Ca = C[C["horizon"] == h]
            r2, _ = compare(Ca[Ca["variant"] == "C_COMBO"], Ca[Ca["variant"] == "base"], h)
            rows.append({"variant": "C_COMBO_fulldev_biased", "horizon": h, "scope": "dev (bias seleksi)", **r2})
    M = pd.DataFrame(rows)
    M["q_bh"] = np.nan
    for h in H:
        m = (M["horizon"] == h) & (M["variant"] != "base") & ~M["variant"].str.endswith("_biased")
        M.loc[m, "q_bh"] = bh_fdr(M.loc[m, "p"].to_numpy())
    M.round(4).to_csv(os.path.join(OUT, "e_metrics.csv"), index=False)
    pc = pd.DataFrame(pcs)
    pc.round(4).to_csv(os.path.join(OUT, "e_per_commodity.csv"), index=False)

    # keputusan §5
    X = M[(M["variant"] != "base") & ~M["variant"].str.endswith("_biased")]
    P = X.pivot(index="variant", columns="horizon")
    dec = pd.DataFrame(index=P.index)
    dec["d_h4"], dec["d_h8"] = P[("diff", 4)], P[("diff", 8)]
    dec["mean_d"] = (dec["d_h4"] + dec["d_h8"]) / 2
    dec["ci_pos_h4"], dec["ci_pos_h8"] = P[("lo", 4)] > 0, P[("lo", 8)] > 0
    dec["r1_effect"] = (dec["mean_d"] >= 0.005) & (dec["ci_pos_h4"] | dec["ci_pos_h8"]) & (dec[["d_h4", "d_h8"]].min(axis=1) >= 0)
    dec["r2_bh"] = ((dec["ci_pos_h4"] & (P[("q_bh", 4)] < 0.05)) | (dec["ci_pos_h8"] & (P[("q_bh", 8)] < 0.05)))
    dec["r3_consistent"] = (P[("years_nonneg", 4)] >= 2) & (P[("years_nonneg", 8)] >= 2) & \
                           (P[("share_origins_pos", 4)] >= 0.5) & (P[("share_origins_pos", 8)] >= 0.5)
    worst = pc.pivot_table(index=["variant", "commodity"], columns="horizon", values="diff")
    bad_comm = (worst[4] < -0.03) & (worst[8] < -0.03)
    dec["r4_no_hidden"] = (P[[("d_f1_up", 4), ("d_f1_up", 8), ("d_f1_down", 4), ("d_f1_down", 8)]].min(axis=1) >= -0.01) & \
                          ~dec.index.isin(bad_comm[bad_comm].index.get_level_values(0))
    dec["r5_leak"] = True
    dec["selectable"] = ~dec.index.isin(NOT_SELECTABLE)
    dec["pass_all"] = dec[["r1_effect", "r2_bh", "r3_consistent", "r4_no_hidden", "r5_leak", "selectable"]].all(axis=1)
    dec["daily_data"] = dec.index.isin(DAILY)
    dec = dec.sort_values("mean_d", ascending=False)
    dec.round(4).to_csv(os.path.join(OUT, "e_decision.csv"))

    # per tahun
    yr = X[["variant", "horizon", "d_2021", "d_2022", "d_2023", "share_origins_pos"]]
    yr.round(4).to_csv(os.path.join(OUT, "e_per_year.csv"), index=False)

    # konkordansi layar DU vs hasil Modeling (keluarga)
    du = pd.read_csv(os.path.join(OUT, "c_du.csv"))
    conc = []
    for f in FAMILIES:
        g = du[du["family"] == f]
        conc.append({"family": f, "du_max_abs_rho_h4": g[g["horizon"] == 4]["rho"].abs().max(),
                     "du_max_abs_rho_h8": g[g["horizon"] == 8]["rho"].abs().max(),
                     "du_min_q_h4": g[g["horizon"] == 4]["q_bh"].min(), "du_min_q_h8": g[g["horizon"] == 8]["q_bh"].min(),
                     "du_gate": False, "model_d_h4": dec.loc[f"C_{f}", "d_h4"], "model_d_h8": dec.loc[f"C_{f}", "d_h8"],
                     "model_pass": bool(dec.loc[f"C_{f}", "pass_all"])})
    pd.DataFrame(conc).round(4).to_csv(os.path.join(OUT, "e_du_concordance.csv"), index=False)
    pd.set_option("display.width", 250)
    print(dec.round(4).to_string())
    print(pd.DataFrame(conc).round(4).to_string(index=False))
