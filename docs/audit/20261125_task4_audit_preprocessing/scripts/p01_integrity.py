"""P01 + P06 (bagian data): integritas PIHPS mentah, presisi harga harian, pembentukan minggu.

Hanya membaca data; tidak menulis artefak. Keluaran: hasil/p01_integrity.json + cetakan.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.data.loaders import load_pihps, norm_name  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "hasil")
res = {}

raw = load_pihps(cfg)
lv2 = raw[raw["level"] == 2].copy()
lv2["item"] = lv2["item"].map(norm_name)
# baris item duplikat dalam satu file provinsi (nama sama muncul > 1 kali)
dup_rows = lv2.groupby(["province_id", "item", "date"]).size()
res["raw_level2_cells"] = int(len(lv2))
res["raw_duplicate_keys"] = int((dup_rows > 1).sum())
nonnull = lv2.dropna(subset=["price"])
res["raw_nonnull"] = int(len(nonnull))
res["raw_nonpositive"] = int((nonnull["price"] <= 0).sum())
res["raw_noninteger"] = int((nonnull["price"] % 1 != 0).sum())

daily = read_artifact(cfg, "pihps_daily")
res["daily_rows"] = int(len(daily))
res["daily_duplicate_keys"] = int(daily.duplicated(["province_id", "commodity", "date"]).sum())
daily["dow"] = daily["date"].dt.dayofweek
res["daily_weekday_share"] = daily["dow"].value_counts(normalize=True).sort_index().round(4).to_dict()

# presisi: kelipatan terbesar dari {1, 10, 25, 50, 100, 250, 500, 1000} yang membagi harga
def tick_share(s):
    out = {}
    for t in (10, 50, 100, 250, 500, 1000):
        out[t] = float((s % t == 0).mean())
    return out

prec = {}
for c, g in daily.groupby("commodity"):
    p = g["price"]
    d = g.sort_values(["province_id", "date"]).groupby("province_id")["price"].diff().dropna()
    d = d[d != 0].abs()
    prec[c] = {"median_price": float(p.median()), "share_multiple": tick_share(p),
               "share_nonzero_daily_change": float((g.sort_values(["province_id", "date"]).groupby("province_id")["price"].diff().dropna() != 0).mean()),
               "median_abs_daily_change_rp": float(d.median()) if len(d) else None,
               "p10_abs_daily_change_rp": float(d.quantile(0.1)) if len(d) else None,
               "share_change_lt50": float((d < 50).mean()) if len(d) else None,
               "median_abs_daily_change_pct": float((d / g.loc[d.index, "price"]).median() * 100) if len(d) else None}
res["precision"] = prec

# pembentukan minggu: berapa minggu yang harga hariannya tidak konstan di dalam minggu, dan selisih rerata vs hari terakhir
daily["week"] = daily["date"] - pd.to_timedelta(daily["dow"], unit="D")
w = daily.groupby(["province_id", "commodity", "week"])["price"].agg(["mean", "median", "last", "first", "min", "max", "size"])
w["within_var"] = w["max"] > w["min"]
res["weeks_with_within_week_variation"] = float(w["within_var"].mean())
res["n_days_dist"] = w["size"].value_counts(normalize=True).sort_index().round(4).to_dict()
w["mean_vs_last_logdiff"] = np.log(w["mean"]) - np.log(w["last"])
res["abs_mean_vs_last_median_pct"] = float(w.loc[w["within_var"], "mean_vs_last_logdiff"].abs().median() * 100)
by_c = w.groupby(level="commodity").agg(within_var=("within_var", "mean"), n_days=("size", "mean"))
res["within_week_by_commodity"] = by_c.round(4).to_dict(orient="index")

# harga mingguan bukan kelipatan Rp50 (hasil rerata hari bervariasi) → perubahan "di bawah satu tick"
panel = read_artifact(cfg, "panel_weekly")
pw = panel.dropna(subset=["price"])
res["weekly_price_not_multiple_of_50"] = float((pw["price"] % 50 != 0).mean())

with open(os.path.join(OUT, "p01_integrity.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in res.items() if k != "precision"}, indent=1, default=str))
for c, v in prec.items():
    print(c, round(v["median_price"]), {k: round(x, 3) for k, x in v["share_multiple"].items()},
          "chg≠0", round(v["share_nonzero_daily_change"], 3), "med|Δ|Rp", v["median_abs_daily_change_rp"],
          "p10", v["p10_abs_daily_change_rp"], "med%", round(v["median_abs_daily_change_pct"] or 0, 3))
