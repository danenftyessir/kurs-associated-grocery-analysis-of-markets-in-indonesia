"""P09 + laporan ketersediaan fitur.

(a) Evaluasi seimbang-seri C1-tuned: macro F1 per seri (provinsi × komoditas), per provinsi, per komoditas; rerata antarseri
    vs gabungan; porsi naik aktual vs prediksi per komoditas (asal drift naik) dan pergeseran prior kelas dev → test.
(b) Distribusi sampel latih per komoditas (y ≠ 0) pada origin pengembangan terakhir.
(c) Feature Availability Report: setiap fitur C1-tuned (+ fx & regulasi ronde 2): porsi kosong di baris latih/test, minggu
    pertama tersedia, jumlah seri tercakup, alasan kosong (pemanasan jendela / harga hilang / belum berlaku).
Hanya analisis. Keluaran: hasil/p09_*.csv, hasil/feature_availability.csv.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "20261125_task4_ronde2", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg, load  # noqa: E402
from kagami.features import price_dynamics  # noqa: E402
from kagami.features.forecast import FEATURE_GROUPS, feature_table, origins, split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402

HERE = os.path.dirname(__file__)
from p_exp import EXP  # noqa: E402  (data per baris turunan PIHPS disimpan di luar repo)
OUT = os.path.join(HERE, "..", "hasil")
pd.set_option("display.width", 220)


def mf1(yt, yp):
    tp, fp, fn, tn = (yt & yp).sum(), (~yt & yp).sum(), (yt & ~yp).sum(), (~yt & ~yp).sum()
    return ((2 * tp / max(2 * tp + fp + fn, 1)) + (2 * tn / max(2 * tn + fn + fp, 1))) / 2


lab = pd.read_parquet(os.path.join(EXP, "label_audit.parquet"))
lab = lab[lab["part"].isin(["dev", "test"])].copy()
lab["up"] = lab["y_true"] > 0
rows = []
for (part, h), x in lab.groupby(["part", "horizon"]):
    ser = x.groupby(["province_id", "commodity"]).apply(lambda s: pd.Series(
        {"n": len(s), "f1": mf1(s["up"].to_numpy(), s["pred_up"].to_numpy()), "acc": s["correct"].mean(),
         "up_share": s["up"].mean(), "pred_up_share": s["pred_up"].mean()}), include_groups=False)
    prov = x.groupby("province_id").apply(lambda s: mf1(s["up"].to_numpy(), s["pred_up"].to_numpy()), include_groups=False)
    com = x.groupby("commodity").apply(lambda s: mf1(s["up"].to_numpy(), s["pred_up"].to_numpy()), include_groups=False)
    rows.append({"part": part, "h": h, "pooled_f1": mf1(x["up"].to_numpy(), x["pred_up"].to_numpy()),
                 "series_mean_f1": ser["f1"].mean(), "series_median_f1": ser["f1"].median(),
                 "series_p10_f1": ser["f1"].quantile(0.1), "series_p90_f1": ser["f1"].quantile(0.9),
                 "series_lt_055": (ser["f1"] < 0.55).mean(), "n_series": len(ser),
                 "series_n_min": ser["n"].min(), "series_n_median": ser["n"].median(), "series_n_max": ser["n"].max(),
                 "province_mean_f1": prov.mean(), "province_min_f1": prov.min(), "province_max_f1": prov.max(),
                 "commodity_mean_f1": com.mean(), "commodity_min_f1": com.min(), "commodity_max_f1": com.max()})
    ser.reset_index().assign(part=part, h=h).to_csv(os.path.join(OUT, f"p09_series_{part}_h{h}.csv"), index=False)
    prov.rename("macro_f1").reset_index().assign(part=part, h=h).to_csv(os.path.join(OUT, f"p09_province_{part}_h{h}.csv"), index=False)
bal = pd.DataFrame(rows)
bal.round(4).to_csv(os.path.join(OUT, "p09_balance.csv"), index=False)
print(bal.round(3).T.to_string())

# drift naik per komoditas: porsi naik aktual vs prediksi, dev vs test
drift = (lab.groupby(["part", "horizon", "commodity"])
         .agg(n=("up", "size"), up_actual=("up", "mean"), up_pred=("pred_up", "mean"), acc=("correct", "mean"))
         .reset_index())
drift["excess_pred_up"] = drift["up_pred"] - drift["up_actual"]
drift.round(4).to_csv(os.path.join(OUT, "p09_drift.csv"), index=False)
piv = drift.pivot_table(index="commodity", columns=["horizon", "part"], values=["up_actual", "excess_pred_up"])
print(piv.round(3).to_string())

# (b) sampel latih per komoditas pada origin pengembangan terakhir (h 8) dan origin test terakhir
panel, drivers, world = load()
full = price_dynamics.extend_table(feature_table(cfg, panel, drivers, world, [4, 8]), panel, [4, 8])
o_dev = [o for o in origins(cfg, full["week"].drop_duplicates(), 8) if o + pd.Timedelta(weeks=8) <= pd.Timestamp("2023-12-31")][-1]
tr, _ = split_origin(cfg, full, o_dev, 8)
tr = tr[tr["y"] != 0]
samp = tr.groupby("commodity").agg(n_train=("y", "size"), up_share=("y", lambda s: (s > 0).mean()))
samp["share_of_train"] = samp["n_train"] / samp["n_train"].sum()
samp.round(4).to_csv(os.path.join(OUT, "p09_train_samples.csv"))
print("\nsampel latih y≠0 per komoditas, origin", o_dev.date())
print(samp.round(3).to_string())

# (c) Feature Availability Report
from feats2 import GROUPS2, extend2  # noqa: E402
reg = extend2(cfg, full[["week", "province_id", "commodity", "log_p"]])
full = full.merge(reg[["week", "province_id", "commodity"] + GROUPS2["reg"]], on=["week", "province_id", "commodity"], how="left")
num4, _ = tuned_columns("C1t", 4)
num8, _ = tuned_columns("C1t", 8)
feats = list(dict.fromkeys(num4 + [c for c in num8 if c not in num4] + FEATURE_GROUPS["fx"] + GROUPS2["reg"]))
grp = {c: g for g, cs in {**{k: v for k, v in FEATURE_GROUPS.items() if k != "id"},
                           **price_dynamics.GROUPS, "reg(ronde2)": GROUPS2["reg"]}.items() for c in cs}
start = pd.Timestamp(cfg.params["period"]["start"])
body = full[full["week"] >= start]
price_missing = body["log_p"].isna()
train_rows = body[(body["week"] < pd.Timestamp("2024-01-01"))]
test_rows = body[body["week"] >= pd.Timestamp("2024-01-01")]
rep = []
for c in feats:
    s = body[c]
    nn = s.notna()
    first = body.loc[nn, "week"].min()
    na = ~nn
    warm = na & (body["week"] < (first + pd.Timedelta(weeks=1)))       # sebelum fitur pertama kali ada
    rep.append({"feature": c, "group": grp.get(c.split("_h")[0] if c.startswith("yseas") else c, ""),
                "first_week": first.date() if pd.notna(first) else None,
                "na_share_all": float(na.mean()), "na_share_dev": float(train_rows[c].isna().mean()),
                "na_share_test": float(test_rows[c].isna().mean()),
                "na_due_price_missing": float((na & price_missing).sum() / max(na.sum(), 1)),
                "na_before_first_week": float(warm.sum() / max(na.sum(), 1)),
                "series_covered": int(body.loc[nn, ["province_id", "commodity"]].drop_duplicates().shape[0]),
                "zero_share": float((s == 0).mean()), "n_unique": int(s.nunique())})
far = pd.DataFrame(rep)
# alasan kosong
far["reason"] = np.select(
    [far["na_share_all"] < 0.001, far["group"].eq("reg(ronde2)"), far["na_before_first_week"] > 0.5,
     far["na_due_price_missing"] > 0.5],
    ["lengkap", "belum berlaku (regulasi) / harga hilang", "pemanasan jendela di awal periode", "harga mingguan hilang"],
    default="campuran (pemanasan + harga hilang)")
far.round(4).to_csv(os.path.join(OUT, "feature_availability.csv"), index=False)
print(far.round(3).to_string(index=False))
# regulasi: NaN 'belum berlaku' vs 'harga hilang' (keduanya NaN di reg_gap, HGB tidak membedakan)
r = body[["reg_gap", "reg_active", "log_p"]]
print("\nreg_gap NaN:", round(r["reg_gap"].isna().mean(), 3), "| dari itu belum berlaku:",
      round(((r["reg_active"] == 0) & r["reg_gap"].isna()).sum() / r["reg_gap"].isna().sum(), 4),
      "| berlaku tapi harga hilang:", round(((r["reg_active"] == 1) & r["log_p"].isna()).sum() / r["reg_gap"].isna().sum(), 4))
