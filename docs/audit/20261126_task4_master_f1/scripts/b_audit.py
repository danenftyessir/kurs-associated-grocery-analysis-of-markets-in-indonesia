"""Fase B (D-156): pemeriksaan preprocessing yang belum dicakup D-147 (tanpa model). Hanya baca; tidak ada yang diubah.

B01 kunci unik & grid lengkap · B02 seri tidak layak di baris evaluasi · B03 y = 0 vs hilang (asal baris yang dibuang)
B04 penyelarasan waktu: y_h dan lag dihitung ulang dari log_p · B05 minggu origin dengan hari teramati < 5 (bias arah)
B06 konsistensi komoditas/provinsi/wilayah · B07 hari yang hilang pada minggu 4 hari (komposisi rerata mingguan)
Keluaran hasil/b_*.csv + b_summary.json.
"""
import json

from m_common import DEV_END, H, OUT, cfg, dev_origins, np, official_c1t, os, pd, table
from kagami.utils.io import read_artifact

B = table()
res = {}
# B01
res["B01_duplicate_keys"] = int(B.duplicated(["province_id", "commodity", "week"]).sum())
res["B01_grid"] = {"series": int(B.groupby(["province_id", "commodity"]).ngroups), "weeks": int(B["week"].nunique()),
                   "rows": len(B), "complete": len(B) == B.groupby(["province_id", "commodity"]).ngroups * B["week"].nunique()}
# B02 kelayakan
el = read_artifact(cfg, "eligibility")
inel = el[~el["eligible"]][["province_id", "commodity"]]
P = official_c1t("dev")
m = P.merge(inel.assign(inel=True), on=["province_id", "commodity"], how="left")
res["B02_ineligible_series"] = inel.to_dict("records")
res["B02_ineligible_rows_in_dev_eval"] = int(m["inel"].fillna(False).sum())
res["B02_ineligible_rows_in_dev_eval_nonzero"] = int((m["inel"].fillna(False) & (m["y_true"] != 0)).sum())
# B03 asal baris yang tidak dievaluasi pada origin dev
rows = []
for h in H:
    for o in dev_origins(h):
        t = B[B["week"] == o]
        y = t[f"y_{h}"]
        lag_na = t[["lag_dp_1", "lag_dp_4", "lag_dp_8"]].isna().any(axis=1)
        rows.append({"horizon": h, "origin": o, "n_series": len(t), "y_nan": int(y.isna().sum()), "lag_nan": int(lag_na.sum()),
                     "y_zero": int((y == 0).sum()), "evaluated": int((y.notna() & ~lag_na & (y != 0)).sum())})
b03 = pd.DataFrame(rows)
b03.to_csv(os.path.join(OUT, "b03_row_accounting.csv"), index=False)
res["B03"] = b03.groupby("horizon")[["n_series", "y_nan", "lag_nan", "y_zero", "evaluated"]].sum().to_dict("index")
# y = 0: status ujung
st = B.set_index(["province_id", "commodity", "week"])["st0"]
z = []
for h in H:
    d = B[(B[f"y_{h}"] == 0)][["province_id", "commodity", "week"]].copy()
    d["st_t"] = st.reindex(pd.MultiIndex.from_frame(d)).to_numpy()
    d["st_th"] = st.reindex(pd.MultiIndex.from_arrays([d["province_id"], d["commodity"], d["week"] + pd.Timedelta(weeks=h)])).to_numpy()
    z.append(d.groupby(["st_t", "st_th"]).size().rename("n").reset_index().assign(horizon=h))
pd.concat(z).to_csv(os.path.join(OUT, "b03_zero_status.csv"), index=False)
# B04 penyelarasan waktu
wide = B.pivot(index="week", columns=["province_id", "commodity"], values="log_p").sort_index()
chk = {}
for h in H:
    yh = (wide.shift(-h) - wide).stack(["province_id", "commodity"], future_stack=True).rename("y").reset_index()
    mm = B[["week", "province_id", "commodity", f"y_{h}"]].merge(yh, on=["week", "province_id", "commodity"])
    a, b = mm[f"y_{h}"].to_numpy(float), mm["y"].to_numpy(float)
    chk[f"y_{h}_max_abs_diff"] = float(np.nanmax(np.abs(a - b)))
    chk[f"y_{h}_nan_pattern_equal"] = bool((np.isnan(a) == np.isnan(b)).all())
for k in (1, 4, 8):
    lk = (wide - wide.shift(k)).stack(["province_id", "commodity"], future_stack=True).rename("l").reset_index()
    mm = B[["week", "province_id", "commodity", f"lag_dp_{k}"]].merge(lk, on=["week", "province_id", "commodity"])
    a, b = mm[f"lag_dp_{k}"].to_numpy(float), mm["l"].to_numpy(float)
    chk[f"lag_dp_{k}_max_abs_diff"] = float(np.nanmax(np.abs(a - b)))
    chk[f"lag_dp_{k}_nan_pattern_equal"] = bool((np.isnan(a) == np.isnan(b)).all())
chk["week_is_monday"] = bool((B["week"].dt.dayofweek == 0).all())
res["B04"] = chk
# B05 minggu origin dengan hari teramati < 5
D = P.merge(B[["province_id", "commodity", "week", "n_days"]].rename(columns={"week": "origin"}), on=["origin", "province_id", "commodity"])
D = D[D["y_true"] != 0]
D["pred_up"], D["true_up"] = D["score"] > 0.5, D["y_true"] > 0
og = D.groupby(["horizon", "origin"]).agg(n=("n_days", "size"), share_nd_lt5=("n_days", lambda s: (s < 5).mean()),
                                          share_up_true=("true_up", "mean"), share_up_pred=("pred_up", "mean")).reset_index()
og["bias_pred_minus_true"] = og["share_up_pred"] - og["share_up_true"]
og.round(4).to_csv(os.path.join(OUT, "b05_origin_days.csv"), index=False)
res["B05_origins_majority_short_week"] = og[og["share_nd_lt5"] > 0.5][["horizon", "origin", "share_nd_lt5", "share_up_true", "share_up_pred"]].round(3).astype(str).to_dict("records")
res["B05_bias_by_short_origin"] = og.assign(short=og["share_nd_lt5"] > 0.5).groupby(["horizon", "short"])["bias_pred_minus_true"].agg(["mean", "size"]).round(4).reset_index().astype(str).to_dict("records")
# dalam origin yang sama: apakah n_days < 5 tetap bias?
within = D.groupby(["horizon", "origin"]).filter(lambda g: 0.1 < (g["n_days"] < 5).mean() < 0.9)
w = within.assign(short=within["n_days"] < 5).groupby(["horizon", "short"]).agg(n=("score", "size"), up_true=("true_up", "mean"), up_pred=("pred_up", "mean"))
w["bias"] = w["up_pred"] - w["up_true"]
res["B05_within_mixed_origins"] = w.round(4).reset_index().astype(str).to_dict("records")
# B07 hari mana yang hilang pada minggu 4 hari
daily = read_artifact(cfg, "pihps_daily")
daily = daily[daily["date"] <= DEV_END]
daily["week"] = daily["date"] - pd.to_timedelta(daily["date"].dt.dayofweek, unit="D")
daily["dow"] = daily["date"].dt.dayofweek
cnt = daily.groupby(["province_id", "commodity", "week"])["dow"].agg(["size", lambda s: tuple(sorted(s))])
cnt.columns = ["n", "days"]
four = cnt[cnt["n"] == 4]
missing_day = four["days"].map(lambda d: ({0, 1, 2, 3, 4} - set(d)).pop() if len(set(d)) == 4 else -1)
res["B07_missing_weekday_in_4day_weeks"] = missing_day.map({0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", -1: "other"}).value_counts(normalize=True).round(3).to_dict()
wk4 = four.reset_index().groupby("week").size()
res["B07_weeks_with_4day_majority"] = int((wk4 > 170).sum())
# B06 konsistensi
res["B06"] = {"commodities": sorted(B["commodity"].unique().tolist()) == sorted(cfg.commodities),
              "provinces": int(B["province_id"].nunique()), "region_na": int(B["region"].isna().sum()),
              "region_per_province_unique": bool(B.groupby("province_id")["region"].nunique().eq(1).all())}
json.dump(res, open(os.path.join(OUT, "b_summary.json"), "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
