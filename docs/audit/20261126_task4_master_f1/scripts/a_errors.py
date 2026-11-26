"""Fase A (D-156): analisis galat C1-tuned di origin PENGEMBANGAN (origin + h ≤ 2023-12-31). Test 2024+ tidak dibaca.

Sumber prediksi = artefak resmi `direction_tuned_preds` (C1t, threshold 0,5). Karakteristik baris dari tabel `base.parquet`
(ex-ante: nilai pada minggu origin; ex-post: |y|, tick, flip, status ujung t + h — hanya untuk diagnosis, tidak untuk model).
Keluaran hasil/a_*.csv + a_summary.json.
"""
import json

from m_common import H, OUT, REGULATED, boot_ci, conf, mf1, np, official_c1t, os, pd, stats_from, summary, table

P = official_c1t("dev")
B = table()
cols = ["province_id", "commodity", "week", "std_dp_13", "std_dp_52", "cf_age", "zero_share_13", "st0", "n_days", "iw_gap",
        "lag_dp_4", "spatial_dev", "region"] + [f"{k}_{h}" for h in H for k in ("ticks", "flip", "st")]
D = P.merge(B[cols].rename(columns={"week": "origin"}), on=["origin", "province_id", "commodity"], how="left")
assert D["std_dp_13"].notna().mean() > 0.95
D["abs_y"] = D["y_true"].abs()
D["conf"] = (D["score"] - 0.5).abs()
D["pred_up"] = D["score"] > 0.5
D["true_up"] = D["y_true"] > 0
D["regulated"] = D["commodity"].isin(REGULATED)
NZ = D[D["y_true"] != 0].copy()
res = {}


def grp_table(df, by, h):
    rows = []
    for k, g in df.groupby(by, observed=True):
        C = conf(g["y_true"], g["score"])
        s = stats_from(C)
        rows.append({"horizon": h, by if isinstance(by, str) else "group": k, "n": int(C.sum()), "macro_f1": s["macro_f1"],
                     "f1_up": s["f1_up"], "f1_down": s["f1_down"], "rec_up": s["rec_up"], "rec_down": s["rec_down"],
                     "acc": s["acc"], "share_up_true": float(g["true_up"].mean()), "share_up_pred": float(g["pred_up"].mean()),
                     "median_abs_y": float(g["abs_y"].median()), "mean_conf": float(g["conf"].mean())})
    return pd.DataFrame(rows)


overall, per_o, per_c, per_p, mag, vol, qual, fpfn, cal, small, decomp = ([] for _ in range(11))
for h in H:
    d, nz = D[D["horizon"] == h], NZ[NZ["horizon"] == h].copy()
    st = summary(d, h)
    st["horizon"] = h
    for k in ("f1_up", "f1_down"):
        st[f"{k}_lo"], st[f"{k}_hi"] = boot_ci(d, h, k)
    overall.append(st)

    # per origin
    po = nz.groupby("origin").apply(lambda g: pd.Series({
        "n": len(g), "macro_f1": mf1(g["y_true"], g["score"]), "share_up_true": g["true_up"].mean(),
        "share_up_pred": g["pred_up"].mean(), "acc": (g["true_up"] == g["pred_up"]).mean()}), include_groups=False).reset_index()
    po["horizon"], po["year"] = h, po["origin"].dt.year
    per_o.append(po)
    per_c.append(grp_table(nz, "commodity", h))
    per_p.append(grp_table(nz, "province_id", h))

    # besar perubahan: kuintil |y| (ambang dari dev h ini)
    nz["q_abs_y"] = pd.qcut(nz["abs_y"], 5, labels=[f"Q{i}" for i in range(1, 6)])
    mag.append(grp_table(nz, "q_abs_y", h))
    # volatilitas ex-ante (sd Δp 13 minggu pada origin)
    nz["q_vol"] = pd.qcut(nz["std_dp_13"].rank(method="first"), 5, labels=[f"V{i}" for i in range(1, 6)])
    vol.append(grp_table(nz, "q_vol", h))
    # kualitas data ex-ante
    nz["cf_age_bin"] = pd.cut(nz["cf_age"], [-1, 0, 2, 8, 26, 1e9], labels=["0", "1-2", "3-8", "9-26", ">26"])
    nz["zero13_bin"] = pd.cut(nz["zero_share_13"], [-0.01, 0.0, 0.25, 0.5, 0.75, 1.0], labels=["0", "≤.25", "≤.5", "≤.75", "≤1"])
    nz["n_days_bin"] = nz["n_days"].clip(upper=5).astype(int).astype(str)
    for col in ("st0", "cf_age_bin", "zero13_bin", "n_days_bin", f"st_{h}"):
        t = grp_table(nz, col, h).rename(columns={col: "level"})
        t.insert(1, "feature", col)
        qual.append(t)

    # FP vs FN
    nz["kind"] = np.select([nz["true_up"] & nz["pred_up"], ~nz["true_up"] & ~nz["pred_up"], ~nz["true_up"] & nz["pred_up"]],
                           ["TP", "TN", "FP (turun→naik)"], "FN (naik→turun)")
    for k, g in nz.groupby("kind"):
        fpfn.append({"horizon": h, "kind": k, "n": len(g), "share_regulated": g["regulated"].mean(),
                     "median_abs_y": g["abs_y"].median(), "share_lt2ticks": (g[f"ticks_{h}"] < 2).mean(),
                     "share_unstable_flip05": (g[f"flip_{h}"] >= 0.05).mean(), "mean_conf": g["conf"].mean(),
                     "share_conf_lt05": (g["conf"] < 0.05).mean(), "median_std_dp_13": g["std_dp_13"].median(),
                     "share_st0_cf": (g["st0"] == "carry_forward").mean(), "median_cf_age": g["cf_age"].median()})

    # kalibrasi
    nz["p_bin"] = pd.cut(nz["score"], np.linspace(0, 1, 11))
    c = nz.groupby("p_bin", observed=True).agg(n=("score", "size"), mean_p=("score", "mean"), share_up=("true_up", "mean")).reset_index()
    c["horizon"] = h
    cal.append(c)

    # kuintil terkecil: apa isinya
    q1 = nz[nz["q_abs_y"] == "Q1"]
    q1["tick_grp"] = pd.cut(q1[f"ticks_{h}"], [-0.01, 1, 2, 1e9], labels=["<1", "1-2", "≥2"])
    q1["stable"] = np.where(q1[f"flip_{h}"] < 0.05, "stabil", "rapuh")
    for col in ("tick_grp", "stable", "regulated", "commodity"):
        t = grp_table(q1, col, h).rename(columns={col: "level"})
        t.insert(1, "feature", col)
        t["share_of_q1"] = t["n"] / len(q1)
        small.append(t)
    from sklearn.metrics import roc_auc_score
    auc_by_q = {q: float(roc_auc_score(g["true_up"], g["score"])) for q, g in nz.groupby("q_abs_y", observed=True)}

    # dekomposisi batas skor (semua oracle = batas atas hindsight, BUKAN metode)
    base_f1 = mf1(nz["y_true"], nz["score"])
    grid = np.round(np.arange(0.30, 0.701, 0.005), 3)
    g_best = max(grid, key=lambda t: mf1(nz["y_true"], nz["score"], t))

    def oracle_by(keys):
        # threshold terbaik per kelompok (hindsight) → prediksi gabungan
        pred = np.zeros(len(nz), bool)
        for _, idx in nz.groupby(keys).indices.items():
            g = nz.iloc[idx]
            t = max(grid, key=lambda t: mf1(g["y_true"], g["score"], t))
            pred[idx] = g["score"].to_numpy() > t
        return mf1(nz["y_true"], pred.astype(float), 0.5)

    stable = nz[(nz[f"flip_{h}"] < 0.05) & (nz[f"ticks_{h}"] >= 2)]
    within_auc = nz.groupby(["origin", "commodity"]).apply(
        lambda g: roc_auc_score(g["true_up"], g["score"]) if g["true_up"].nunique() == 2 else np.nan, include_groups=False)
    decomp.append({"horizon": h, "macro_f1_base": base_f1,
                   "oracle_global_thr": mf1(nz["y_true"], nz["score"], g_best), "oracle_global_thr_value": float(g_best),
                   "oracle_thr_per_origin": oracle_by(["origin"]),
                   "oracle_thr_per_commodity": oracle_by(["commodity"]),
                   "oracle_thr_per_origin_commodity": oracle_by(["origin", "commodity"]),
                   "macro_f1_stable_ge2ticks": mf1(stable["y_true"], stable["score"]), "share_stable_ge2ticks": len(stable) / len(nz),
                   "auc_pooled": float(roc_auc_score(nz["true_up"], nz["score"])),
                   "auc_within_origin_commodity_mean": float(within_auc.mean()),
                   **{f"auc_{q}": v for q, v in auc_by_q.items()}})

for name, rows in (("a_overall", overall), ("a_decomposition", decomp)):
    pd.DataFrame(rows).round(4).to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
for name, parts in (("a_per_origin", per_o), ("a_per_commodity", per_c), ("a_per_province", per_p), ("a_by_magnitude", mag),
                    ("a_by_volatility", vol), ("a_by_quality", qual), ("a_calibration", cal), ("a_small_moves", small)):
    pd.concat(parts, ignore_index=True).round(4).to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
pd.DataFrame(fpfn).round(4).to_csv(os.path.join(OUT, "a_fp_fn.csv"), index=False)

po = pd.concat(per_o)
res["per_origin"] = {int(h): {"mean": float(g["macro_f1"].mean()), "sd": float(g["macro_f1"].std()),
                              "min": float(g["macro_f1"].min()), "max": float(g["macro_f1"].max()),
                              "share_lt_0_6": float((g["macro_f1"] < 0.6).mean()),
                              "by_year": g.groupby("year")["macro_f1"].mean().round(4).to_dict()} for h, g in po.groupby("horizon")}
json.dump(res, open(os.path.join(OUT, "a_summary.json"), "w"), indent=1, default=str)
pd.set_option("display.width", 250)
for name in ("a_overall", "a_decomposition", "a_by_magnitude", "a_by_volatility", "a_fp_fn"):
    print("==", name)
    print(pd.read_csv(os.path.join(OUT, f"{name}.csv")).to_string(index=False))
print(json.dumps(res, indent=1, default=str))
