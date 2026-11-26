"""K4 Fase B — Data Understanding target risiko kenaikan material (origin pengembangan saja; test 2024+ tidak dibaca).

B1 distribusi target per komoditas × h; B2 ambang walk-forward P70/P80/P90; B3 base rate menurut waktu (mingguan 2018-07..2023,
ambang walk-forward per minggu); B4 kualitas label (tick Rp50, dekat ambang, carry-forward, hilang, lonjakan yang berbalik).
Keluaran hasil/du_*.csv + du_summary.json.
"""
import json
import os

from k4_common import (DEV_END, H, K, OUT, REGULATED, TICK, add_event, cfg, origin_list, pd, np, split_k4, table,
                       thresholds)
from kagami.evaluation.regimes import regulation_changes

PCTS = (70, 80, 90)

if __name__ == "__main__":
    tab = add_event(table())
    tab = tab[tab["week"] <= DEV_END].copy()           # DU: hanya data s.d. akhir 2023 (target ≤ 2023 di bawah)
    S = {}
    # sanity: y_h dari panel = y_h resmi
    for h in H:
        d = tab.dropna(subset=[f"y_{h}", f"ymax_{h}"])
        S[f"ymax_ge_y_h{h}"] = bool((d[f"ymax_{h}"] >= d[f"y_{h}"] - 1e-12).all())

    # ---------------- universe evaluasi dev (origin resmi 4-mingguan)
    rows = []
    for h in H:
        for o in origin_list(h, "dev"):
            base = None
            for pct in PCTS:
                tr, te, thr = split_k4(tab, o, h, "end", pct)
                if base is None:
                    base = te[K + ["y", "has_target", "log_p", f"ymax_{h}", f"ticks_{h}", f"flip_{h}", "st0", f"st_{h}"]].copy()
                    base = base.rename(columns={f"ymax_{h}": "ymax", f"ticks_{h}": "ticks", f"flip_{h}": "flip", f"st_{h}": "st_h"})
                    base["train_rate_z80"] = np.nan
                base[f"thr{pct}"] = te["thr"].to_numpy()
                if pct == 80:
                    base["train_rate_z80"] = te["commodity"].map(tr.groupby("commodity")["z"].mean()).to_numpy()
            rows.append(base.assign(origin=o, horizon=h))
    U = pd.concat(rows, ignore_index=True)
    U["price"] = np.exp(U["log_p"])
    for pct in PCTS:
        U[f"z{pct}"] = (U["has_target"] & (U["y"] >= U[f"thr{pct}"])).astype(int)
        U[f"zany{pct}"] = (np.isfinite(U["ymax"]) & (U["ymax"] >= U[f"thr{pct}"])).astype(int)
    U["cls"] = np.select([~U["has_target"], U["z80"] == 1, U["y"] > 0, U["y"] < 0], ["hilang", "naik_material", "naik_nonmaterial",
                                                                                   "turun"], "tetap")
    U.to_parquet(os.path.join(os.environ["KAGAMI_EXP"], "k4_du_universe.parquet"))
    S["n_universe"] = U.groupby("horizon").size().to_dict()
    S["n_origins"] = U.groupby("horizon")["origin"].nunique().to_dict()

    # ---------------- B1 distribusi per komoditas × h
    b1 = []
    for (h, c), d in U.groupby(["horizon", "commodity"]):
        yy = d.loc[d["has_target"], "y"]
        pc = np.expm1(yy)
        rp = (d.loc[d["has_target"], "price"] * pc)
        cnt = d["cls"].value_counts()
        b1.append({"horizon": h, "commodity": c, "n": len(d), "n_naik_material": int(cnt.get("naik_material", 0)),
                   "n_naik_nonmaterial": int(cnt.get("naik_nonmaterial", 0)), "n_turun": int(cnt.get("turun", 0)),
                   "n_tetap": int(cnt.get("tetap", 0)), "n_hilang": int(cnt.get("hilang", 0)), "base_rate": d["z80"].mean(),
                   "thr80_pct_median": float(np.expm1(d["thr80"]).median() * 100),
                   "thr80_rp_median": float((d["price"] * np.expm1(d["thr80"])).median()),
                   "price_median": float(d["price"].median()),
                   **{f"chg_pct_p{q}": float(np.percentile(pc, q) * 100) for q in (5, 25, 50, 75, 95)},
                   **{f"chg_rp_p{q}": float(np.percentile(rp, q)) for q in (5, 50, 95)},
                   "n_pos_per_series_mean": d.groupby("province_id")["z80"].sum().mean()})
    for h, d in U.groupby("horizon"):
        cnt = d["cls"].value_counts()
        b1.append({"horizon": h, "commodity": "SEMUA", "n": len(d), "n_naik_material": int(cnt.get("naik_material", 0)),
                   "n_naik_nonmaterial": int(cnt.get("naik_nonmaterial", 0)), "n_turun": int(cnt.get("turun", 0)),
                   "n_tetap": int(cnt.get("tetap", 0)), "n_hilang": int(cnt.get("hilang", 0)), "base_rate": d["z80"].mean(),
                   "n_pos_per_series_mean": d.groupby(K)["z80"].sum().mean()})
    B1 = pd.DataFrame(b1)
    B1.round(4).to_csv(os.path.join(OUT, "du_b1_distribution.csv"), index=False)

    # ---------------- B2 ambang P70/P80/P90 (walk-forward) + drift ambang
    b2 = []
    for (h, c), d in U.groupby(["horizon", "commodity"]):
        r = {"horizon": h, "commodity": c}
        for pct in PCTS:
            r[f"thr{pct}_pct_median"] = float(np.expm1(d[f"thr{pct}"]).median() * 100)
            r[f"base_rate_z{pct}"] = d[f"z{pct}"].mean()
            r[f"base_rate_zany{pct}"] = d[f"zany{pct}"].mean()
        first, last = d[d["origin"] == d["origin"].min()], d[d["origin"] == d["origin"].max()]
        r["thr80_pct_first_origin"] = float(np.expm1(first["thr80"].iloc[0]) * 100)
        r["thr80_pct_last_origin"] = float(np.expm1(last["thr80"].iloc[0]) * 100)
        r["n_pos_z90"] = int(d["z90"].sum())
        b2.append(r)
    for h, d in U.groupby("horizon"):
        b2.append({"horizon": h, "commodity": "SEMUA", **{f"base_rate_z{p}": d[f"z{p}"].mean() for p in PCTS},
                   **{f"base_rate_zany{p}": d[f"zany{p}"].mean() for p in PCTS}, "n_pos_z90": int(d["z90"].sum())})
    pd.DataFrame(b2).round(4).to_csv(os.path.join(OUT, "du_b2_thresholds.csv"), index=False)

    # ---------------- B3 waktu: semua minggu 2018-07-02 .. 2023-12-31 − h (ambang walk-forward per minggu)
    from kagami.features.forecast import LAG_COLUMNS
    chg = regulation_changes(cfg, pd.read_csv(os.path.join(cfg.reference_dir, "regulation.csv")))
    wk_rows = []
    lagok = tab[LAG_COLUMNS].notna().all(1)
    for h in H:
        weeks = sorted(tab.loc[(tab["week"] >= "2018-07-02") & (tab["week"] + pd.Timedelta(weeks=h) <= DEV_END), "week"].unique())
        for w in weeks:
            thr = thresholds(tab, w, h)
            d = tab[(tab["week"] == w) & lagok][K + [f"y_{h}"]]
            th = d["commodity"].map(thr).to_numpy(float)
            yv = d[f"y_{h}"].to_numpy(float)
            wk_rows.append(pd.DataFrame({"week": w, "horizon": h, "province_id": d["province_id"].to_numpy(),
                                         "commodity": d["commodity"].to_numpy(),
                                         "z80": (np.isfinite(yv) & (yv >= th)).astype(int)}))
    W = pd.concat(wk_rows, ignore_index=True)
    W["year"] = W["week"].dt.year
    W["month"] = W["week"].dt.month
    W["regulated"] = W["commodity"].isin(REGULATED)
    # pasca perubahan harga acuan konsumen (≤ 13 minggu sesudah tanggal perubahan, komoditas itu)
    W["post_ref_change"] = False
    for _, r in chg.iterrows():
        m = (W["commodity"] == r["commodity"]) & (W["week"] >= r["change_date"]) & (W["week"] < r["change_date"] + pd.Timedelta(weeks=13))
        W.loc[m, "post_ref_change"] = True
    b3 = []
    for col in ("year", "month", "commodity", "province_id", "regulated", "post_ref_change"):
        g = W.groupby(["horizon", col])["z80"].agg(["mean", "size"]).reset_index().rename(columns={col: "level"})
        b3.append(g.assign(dim=col))
    g = W.groupby(["horizon", "regulated", "year"])["z80"].agg(["mean", "size"]).reset_index()
    g["level"] = g["regulated"].map({True: "diatur", False: "tidak_diatur"}) + "_" + g["year"].astype(str)
    b3.append(g.drop(columns=["regulated", "year"]).assign(dim="regulated_x_year"))
    B3 = pd.concat(b3, ignore_index=True)
    B3.round(4).to_csv(os.path.join(OUT, "du_b3_temporal.csv"), index=False)
    per_w = W.groupby(["horizon", "week"])["z80"].mean()
    S["weekly_base_rate_sd"] = per_w.groupby(level=0).std().round(4).to_dict()
    S["weekly_base_rate_p10_p90"] = {h: [round(float(per_w[h].quantile(.1)), 4), round(float(per_w[h].quantile(.9)), 4)] for h in H}
    S["weekly_base_rate_autocorr_lag_h"] = {h: round(float(per_w[h].autocorr(lag=h)), 4) for h in H}
    S["weekly_base_rate_autocorr_lag_2h"] = {h: round(float(per_w[h].autocorr(lag=2 * h)), 4) for h in H}
    per_o = U.groupby(["horizon", "origin"])["z80"].mean()
    per_o.rename("base_rate").reset_index().round(4).to_csv(os.path.join(OUT, "du_b3_per_origin.csv"), index=False)
    S["eval_origin_base_rate_range"] = {h: [round(float(per_o[h].min()), 4), round(float(per_o[h].max()), 4)] for h in H}
    # pergeseran: base rate latih (yang diketahui pada origin) vs base rate terealisasi origin itu
    sh = U.groupby(["horizon", "origin"]).agg(realized=("z80", "mean"), train=("train_rate_z80", "mean")).reset_index()
    sh["gap"] = sh["realized"] - sh["train"]
    sh.round(4).to_csv(os.path.join(OUT, "du_b3_train_vs_realized.csv"), index=False)
    S["train_vs_realized_gap_mean_sd"] = {h: [round(float(sh.loc[sh.horizon == h, "gap"].mean()), 4),
                                              round(float(sh.loc[sh.horizon == h, "gap"].std()), 4)] for h in H}

    # ---------------- B4 kualitas label
    b4 = []
    for h, d in U.groupby("horizon"):
        t = d[d["has_target"]].copy()
        tick_log = np.log1p(TICK / t["price"])
        near = (t["y"] - t["thr80"]).abs() < tick_log
        pos = t["z80"] == 1
        anyp = d["zany80"] == 1
        cf_end = (t["st0"] == "carry_forward") | (t["st_h"] == "carry_forward")
        b4.append({"horizon": h, "n_target": len(t), "n_missing_target": int((~d["has_target"]).sum()),
                   "pos_share_lt2ticks": float((t.loc[pos, "ticks"] < 2).mean()),
                   "pos_share_lt5ticks": float((t.loc[pos, "ticks"] < 5).mean()),
                   "thr80_in_ticks_median": float((np.expm1(t["thr80"]) * t["price"] / TICK).median()),
                   "near_threshold_share_all": float(near.mean()), "near_threshold_share_pos": float(near[pos].mean()),
                   "label_flip_if_1tick_share_pos": float(near[pos].mean()),
                   "dir_flip_ge5pct_pos": float((t.loc[pos, "flip"] >= 0.05).mean()),
                   "dir_flip_ge5pct_all": float((t["flip"] >= 0.05).mean()),
                   "cf_end_share_pos": float(cf_end[pos].mean()), "cf_end_share_all": float(cf_end.mean()),
                   "pos_share_regulated": float(t.loc[pos, "commodity"].isin(REGULATED).mean()),
                   "zany_rate": float(anyp.mean()), "zend_rate": float(d["z80"].mean()),
                   "spike_revert_share_of_any": float(((d["zany80"] == 1) & (d["z80"] == 0))[anyp].mean()),
                   "end_in_any": float(((d["zany80"] == 1) & (d["z80"] == 1)).sum() / max(d["z80"].sum(), 1))})
    pd.DataFrame(b4).round(4).to_csv(os.path.join(OUT, "du_b4_label_quality.csv"), index=False)
    b4c = []
    for (h, c), d in U[U["has_target"]].groupby(["horizon", "commodity"]):
        tick_log = np.log1p(TICK / d["price"])
        pos = d["z80"] == 1
        b4c.append({"horizon": h, "commodity": c, "thr80_ticks_median": float((np.expm1(d["thr80"]) * d["price"] / TICK).median()),
                    "near_threshold_share_pos": float(((d["y"] - d["thr80"]).abs() < tick_log)[pos].mean()),
                    "cf_end_share_pos": float(((d["st0"] == "carry_forward") | (d["st_h"] == "carry_forward"))[pos].mean()),
                    "zany_rate": float(U.loc[(U.horizon == h) & (U.commodity == c), "zany80"].mean()),
                    "zend_rate": float(d["z80"].mean())})
    pd.DataFrame(b4c).round(4).to_csv(os.path.join(OUT, "du_b4_by_commodity.csv"), index=False)

    # ---------------- skenario ilustratif (BUKAN ambang TPID): ambang seragam 5% / 10%
    il = []
    for (h, c), d in U[U["has_target"]].groupby(["horizon", "commodity"]):
        il.append({"horizon": h, "commodity": c, "rate_stat_p80": d["z80"].mean(),
                   "rate_uniform_5pct": float((d["y"] >= np.log(1.05)).mean()),
                   "rate_uniform_10pct": float((d["y"] >= np.log(1.10)).mean())})
    IL = pd.DataFrame(il)
    for h, d in U[U["has_target"]].groupby("horizon"):
        pos5 = d["y"] >= np.log(1.05)
        S[f"uniform5_regulated_share_of_pos_h{h}"] = round(float(d.loc[pos5, "commodity"].isin(REGULATED).mean()), 4)
        S[f"p80_regulated_share_of_pos_h{h}"] = round(float(d.loc[d["z80"] == 1, "commodity"].isin(REGULATED).mean()), 4)
    IL.round(4).to_csv(os.path.join(OUT, "du_illustrative_uniform.csv"), index=False)
    with open(os.path.join(OUT, "du_summary.json"), "w", encoding="utf-8") as f:
        json.dump(S, f, indent=1, default=str)
    pd.set_option("display.width", 250)
    print(B1.round(3).to_string(index=False))
    print(json.dumps(S, indent=1, default=str))
    print(pd.read_csv(os.path.join(OUT, "du_b4_label_quality.csv")).T)
