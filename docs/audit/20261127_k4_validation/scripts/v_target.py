"""Audit integritas target K4 (baca-saja; TARGET_INTEGRITY_AUDIT.md).

1. Target tak teramati: jumlah per bagian × horizon × komoditas; label yang diberikan; ikut latih atau tidak.
2. y_h & z di prediksi beku dihitung ulang dari artefak panel_weekly (harga teramati, tanpa isi) → harus identik.
3. Universe latih vs evaluasi: baris latih yang dibuang karena target hilang; seri tanpa prediksi di origin (lag hilang).
4. Kualitas label negatif: status ujung (observed / carry_forward / short) per kelas label.
5. Dampak koreksi (target hilang dikeluarkan dari evaluasi alih-alih z = 0): AP, presisi@K, Brier, ECE per bagian × horizon.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v_common import H, REGULATED, brier, ece, fast_ap, flags_k, np, pd, preds, save, table  # noqa: E402
from k4_common import LAG_COLUMNS, panel_logp, thresholds  # noqa: E402
from kg import cfg, read_artifact  # noqa: E402

W = pd.Timedelta(weeks=1)


def main():
    tab = table()
    panel = read_artifact(cfg, "panel_weekly")
    status = panel.pivot(index="week", columns=["province_id", "commodity"], values="status").sort_index()
    lp = panel_logp()
    P = {p: preds(p) for p in ("dev", "test", "forward")}

    # ---------------- 1. target tak teramati
    rows = []
    for part, d in P.items():
        for (h, c), g in d.groupby(["horizon", "commodity"]):
            rows.append({"part": part, "horizon": h, "commodity": c, "n": len(g), "n_no_target": int((~g["has_target"]).sum()),
                         "z_e80_on_no_target": g.loc[~g["has_target"], "z_e80"].unique().tolist(),
                         "z_a80_pos_on_no_target": int(g.loc[~g["has_target"], "z_a80"].sum())})
    miss = save(pd.DataFrame(rows), "ti_missing_by_commodity.csv")
    tot = miss.groupby(["part", "horizon"])[["n", "n_no_target"]].sum().reset_index()
    save(tot, "ti_missing_totals.csv")
    detail = pd.concat([d.loc[~d["has_target"], ["origin", "horizon", "province_id", "commodity", "y", "ymax", "z_e80", "z_a80",
                                                 "k4_e80", "c1t"]].assign(part=p)
                        for p, d in P.items() if p != "forward"])
    save(detail, "ti_missing_rows.csv")

    # ---------------- 2. hitung ulang y & z dari panel resmi
    chk = []
    for part in ("dev", "test"):
        d = P[part]
        for h in H:
            g = d[d["horizon"] == h]
            t0 = lp.reindex(pd.DatetimeIndex(g["origin"])).to_numpy()
            t1 = lp.reindex(pd.DatetimeIndex(g["origin"] + h * W)).to_numpy()
            cols = pd.MultiIndex.from_frame(g[["province_id", "commodity"]])
            ci = lp.columns.get_indexer(cols)
            r = np.arange(len(g))
            y_re = t1[r, ci] - t0[r, ci]
            same_nan = np.array_equal(np.isnan(y_re), np.isnan(g["y"].to_numpy()))
            fin = np.isfinite(y_re)
            maxdiff = float(np.nanmax(np.abs(y_re[fin] - g["y"].to_numpy()[fin]))) if fin.any() else 0.0
            z_re = (fin & (y_re >= g["thr_e80"].to_numpy())).astype(int)
            # ambang dihitung ulang untuk 3 origin
            thr_ok = []
            for o in sorted(g["origin"].unique())[:: max(1, len(g["origin"].unique()) // 3)][:3]:
                th = thresholds(tab, o, h, 80)
                gg = g[g["origin"] == o]
                thr_ok.append(float(np.nanmax(np.abs(gg["commodity"].map(th).to_numpy() - gg["thr_e80"].to_numpy()))))
            st0 = status.reindex(pd.DatetimeIndex(g["origin"])).to_numpy()[r, ci]
            st1 = status.reindex(pd.DatetimeIndex(g["origin"] + h * W)).to_numpy()[r, ci]
            chk.append({"part": part, "horizon": h, "n": len(g), "nan_pattern_equal": same_nan, "max_abs_dy": maxdiff,
                        "z_mismatch": int((z_re != g["z_e80"].to_numpy()).sum()), "thr_max_abs_diff_3_origins": max(thr_ok),
                        "no_target_end_status_missing": int(((~fin) & (st1 == "missing")).sum()),
                        "no_target_end_beyond_data": int(((~fin) & pd.isna(st1)).sum())})
            # ---------------- 4. kualitas label per kelas
            cls = np.select([~fin, z_re == 1, y_re > 0, y_re < 0], ["hilang", "positif", "naik_bawah_ambang", "turun"], "tetap")
            q = pd.DataFrame({"cls": cls, "st0": st0, "st1": st1, "commodity": g["commodity"].to_numpy(),
                              "ticks": g["y"].to_numpy() - g["thr_e80"].to_numpy()})
            q["both_cf"] = (q["st0"] == "carry_forward") & (q["st1"] == "carry_forward")
            q["any_short"] = (q["st0"] == "short") | (q["st1"] == "short")
            q["any_cf"] = (q["st0"] == "carry_forward") | (q["st1"] == "carry_forward")
            agg = q.groupby("cls").agg(n=("cls", "size"), share_any_cf=("any_cf", "mean"), share_both_cf=("both_cf", "mean"),
                                       share_any_short=("any_short", "mean"),
                                       share_regulated=("commodity", lambda s: s.isin(REGULATED).mean())).reset_index()
            chk_q = agg.assign(part=part, horizon=h)
            chk.append({"part": part, "horizon": h, "label_quality": chk_q.to_dict("records")})
    save(pd.DataFrame([c for c in chk if "n" in c]), "ti_recompute_checks.csv")
    lq = pd.DataFrame([r for c in chk if "label_quality" in c for r in c["label_quality"]])
    save(lq, "ti_label_quality.csv")

    # ---------------- 3. universe latih vs evaluasi
    uni = []
    grid = tab[["week", "province_id", "commodity", "log_p"] + LAG_COLUMNS + ["y_4", "y_8"]]
    lag_ok = grid[LAG_COLUMNS].notna().all(1)
    for part in ("dev", "test", "forward"):
        d = P[part]
        for h in H:
            os_ = sorted(d.loc[d["horizon"] == h, "origin"].unique())
            for o in os_:
                o = pd.Timestamp(o)
                at = grid["week"] == o
                eligible_series = int(grid.loc[at, "log_p"].notna().sum() + grid.loc[at, "log_p"].isna().sum())
                tr_window = (grid["week"] + h * W <= o) & lag_ok
                uni.append({"part": part, "horizon": h, "origin": o, "series_grid": int(at.sum()),
                            "series_price_at_origin": int(grid.loc[at, "log_p"].notna().sum()),
                            "series_in_universe": int((at & lag_ok).sum()),
                            "series_price_but_lag_missing": int((at & grid["log_p"].notna() & ~lag_ok).sum()),
                            "train_rows_window": int(tr_window.sum()),
                            "train_rows_dropped_no_target": int((tr_window & grid[f"y_{h}"].isna()).sum()),
                            "train_rows_y0": int((tr_window & (grid[f"y_{h}"] == 0)).sum()),
                            "_n": eligible_series})
    U = pd.DataFrame(uni).drop(columns="_n")
    save(U, "ti_universe_per_origin.csv")
    save(U.groupby(["part", "horizon"]).agg(origins=("origin", "size"), series_grid=("series_grid", "mean"),
                                            price_at_origin=("series_price_at_origin", "mean"),
                                            in_universe=("series_in_universe", "mean"),
                                            price_but_lag_missing_total=("series_price_but_lag_missing", "sum"),
                                            train_dropped_no_target_last=("train_rows_dropped_no_target", "last"),
                                            train_rows_last=("train_rows_window", "last"),
                                            train_y0_last=("train_rows_y0", "last")).reset_index(),
         "ti_universe_summary.csv")

    # ---------------- 5. dampak koreksi
    imp = []
    for part in ("dev", "test"):
        d = P[part]
        for h in H:
            g0 = d[d["horizon"] == h].reset_index(drop=True)
            g1 = g0[g0["has_target"]].reset_index(drop=True)
            for name, g in (("original_no_target_as_0", g0), ("corrected_exclude_no_target", g1)):
                y = g["z_e80"].to_numpy(int)
                r = {"part": part, "horizon": h, "handling": name, "n": len(g), "n_pos": int(y.sum()), "base_rate": y.mean()}
                for s in ("k4_e80", "c1t", "clim_e80"):
                    r[f"ap_{s}"] = fast_ap(y, g[s].to_numpy(float))
                    for k in (1, 2, 3):
                        f = flags_k(g, s, k)
                        r[f"prec_k{k}_{s}"] = (f & (y == 1)).sum() / f.sum()
                r["brier_k4_e80"] = brier(y, g["k4_e80"])
                r["ece_k4_e80"] = ece(y, g["k4_e80"])
                imp.append(r)
    I = pd.DataFrame(imp)
    save(I, "ti_correction_impact.csv")
    pd.set_option("display.width", 250)
    print(tot.to_string(index=False))
    print(pd.DataFrame([c for c in chk if "n" in c]).to_string(index=False))
    print(lq.round(3).to_string(index=False))
    print(pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "hasil", "ti_universe_summary.csv")).to_string(index=False))
    print(I.round(4).T.to_string())


if __name__ == "__main__":
    main()
