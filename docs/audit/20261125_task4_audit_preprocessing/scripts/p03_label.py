"""P03/P04/P06: pembentukan label & kepekaannya terhadap presisi (tick Rp50), agregasi hari → minggu, dan status sel.

Untuk setiap baris prediksi C1-tuned (`direction_tuned_preds`, model C1t; origin = minggu t) dihitung dari `pihps_daily`:
- Δ Rp rerata mingguan (definisi resmi panel) dan jumlah tick Rp50;
- tanda label menurut representasi lain minggu t dan t+h: median hari, hari teramati terakhir, hari pertama;
- peluang label berbalik bila hari teramati dalam minggu t dan t+h di-resample (bootstrap hari, B = 200);
- status sel kedua ujung (panel_weekly).
Lalu akurasi & macro F1 C1-tuned per kelompok. Hanya analisis (tidak memilih apa pun). Keluaran: hasil/p03_*.csv/json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

HERE = os.path.dirname(__file__)
from p_exp import EXP  # noqa: E402  (data per baris turunan PIHPS disimpan di luar repo)
OUT = os.path.join(HERE, "..", "hasil")
DEV_END, TEST_START = pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-01")
TICK = 50.0
B = 200
rng = np.random.default_rng(cfg.seed + 7101)

daily = read_artifact(cfg, "pihps_daily")
daily["week"] = daily["date"] - pd.to_timedelta(daily["date"].dt.dayofweek, unit="D")
daily = daily.sort_values(["province_id", "commodity", "date"])
g = daily.groupby(["province_id", "commodity", "week"])["price"]
wk = pd.DataFrame({"mean": g.mean(), "median": g.median(), "last": g.last(), "first": g.first(), "n": g.size(),
                   "vmin": g.min(), "vmax": g.max()})
# matriks hari (maks 5 hari kerja) untuk bootstrap
pos = daily.groupby(["province_id", "commodity", "week"]).cumcount()
daily["pos"] = pos.to_numpy()
mat = daily.pivot_table(index=["province_id", "commodity", "week"], columns="pos", values="price", aggfunc="first")
mat = mat.reindex(wk.index)
M = mat.to_numpy(float)
nday = wk["n"].to_numpy()
cell_idx = pd.Series(np.arange(len(wk)), index=wk.index)

panel = read_artifact(cfg, "panel_weekly").set_index(["province_id", "commodity", "week"])["status"]

pred = pd.read_parquet(os.path.join(cfg.root, "data", "interim", "direction_tuned_preds.parquet"))
pred = pred[(pred["model"] == "C1t") & np.isfinite(pred["y_true"]) & (pred["y_true"] != 0)].copy()
pred["t0"] = pred["origin"]
pred["t1"] = pred["origin"] + pd.to_timedelta(pred["horizon"] * 7, unit="D")
pred["part"] = np.where(pred["origin"] >= TEST_START, "test",
                        np.where(pred["t1"] <= DEV_END, "dev", "gap"))
k0 = pd.MultiIndex.from_arrays([pred["province_id"], pred["commodity"], pred["t0"]])
k1 = pd.MultiIndex.from_arrays([pred["province_id"], pred["commodity"], pred["t1"]])
i0 = cell_idx.reindex(k0).to_numpy()
i1 = cell_idx.reindex(k1).to_numpy()
assert not np.isnan(i0).any() and not np.isnan(i1).any(), "ujung label tanpa hari teramati"
i0, i1 = i0.astype(int), i1.astype(int)

for rep in ("mean", "median", "last", "first"):
    v = wk[rep].to_numpy(float)
    pred[f"y_{rep}"] = np.log(v[i1]) - np.log(v[i0])
# cek: definisi resmi = rerata hari teramati
assert np.allclose(pred["y_mean"], pred["y_true"], atol=1e-12), "y_true ≠ log rerata mingguan"
mean = wk["mean"].to_numpy(float)
pred["d_rp"] = mean[i1] - mean[i0]
pred["ticks"] = pred["d_rp"].abs() / TICK
pred["tick_pct"] = TICK / mean[i0] * 100
pred["flat_ends"] = (wk["vmin"].to_numpy()[i0] == wk["vmax"].to_numpy()[i0]) & (wk["vmin"].to_numpy()[i1] == wk["vmax"].to_numpy()[i1])
pred["st0"] = panel.reindex(k0).to_numpy()
pred["st1"] = panel.reindex(k1).to_numpy()
up = pred["y_true"].to_numpy() > 0


def boot_mean(idx):
    """B rerata bootstrap hari untuk sel `idx` (array) → (len(idx), B)."""
    n = nday[idx]
    u = rng.random((len(idx), B, 5))
    j = np.floor(u * n[:, None, None]).astype(int)
    vals = np.take_along_axis(np.repeat(M[idx][:, None, :], B, 1), j, axis=2)
    keep = np.arange(5)[None, None, :] < n[:, None, None]
    return np.where(keep, vals, 0).sum(2) / n[:, None]


flip = np.empty(len(pred))
for s in range(0, len(pred), 4000):
    a, b = i0[s:s + 4000], i1[s:s + 4000]
    yb = np.log(boot_mean(b)) - np.log(boot_mean(a))
    sgn = up[s:s + 4000][:, None]
    flip[s:s + 4000] = ((yb > 0) != sgn).mean(1) + 0.0 * (yb == 0).mean(1)
pred["flip_boot"] = flip
for rep in ("median", "last", "first"):
    y = pred[f"y_{rep}"].to_numpy()
    pred[f"agree_{rep}"] = np.where(y == 0, np.nan, ((y > 0) == up).astype(float))
pred["pred_up"] = pred["p_up"] > 0.5
pred["correct"] = (pred["pred_up"] == up).astype(float)


def macro_f1(df):
    yt, yp = df["y_true"].to_numpy() > 0, df["pred_up"].to_numpy()
    tp, fp, fn, tn = (yt & yp).sum(), (~yt & yp).sum(), (yt & ~yp).sum(), (~yt & ~yp).sum()
    f1u = 2 * tp / max(2 * tp + fp + fn, 1)
    f1d = 2 * tn / max(2 * tn + fn + fp, 1)
    return (f1u + f1d) / 2


def summarize(df, by):
    rows = []
    for k, x in df.groupby(by, observed=True):
        rows.append({**dict(zip(by, k if isinstance(k, tuple) else (k,))), "n": len(x), "share": len(x) / len(df),
                     "acc": x["correct"].mean(), "macro_f1": macro_f1(x), "rec_down": (~(x["pred_up"]) & (x["y_true"] < 0)).sum() / max((x["y_true"] < 0).sum(), 1),
                     "flip_boot_mean": x["flip_boot"].mean(), "unstable_share": (x["flip_boot"] >= 0.05).mean(),
                     "agree_last": x["agree_last"].mean(), "agree_median": x["agree_median"].mean(),
                     "flat_ends_share": x["flat_ends"].mean(), "median_abs_y_pct": x["y_true"].abs().median() * 100})
    return pd.DataFrame(rows)


bins = [0, 1, 2, 3, 5, 10, np.inf]
labels = ["<1 tick", "1-2", "2-3", "3-5", "5-10", ">=10"]
pred["tick_bin"] = pd.cut(pred["ticks"], bins, right=False, labels=labels)
pred["stab"] = pd.cut(pred["flip_boot"], [-0.01, 0.0001, 0.05, 0.2, 1.0], labels=["0", "(0,5%)", "[5,20%)", ">=20%"])
pred["q_absy"] = pred.groupby(["part", "horizon"])["y_true"].transform(lambda s: pd.qcut(s.abs(), 5, labels=False) + 1)
both = pred[pred["part"].isin(["dev", "test"])]
tabs = {
    "by_tick": summarize(both, ["part", "horizon", "tick_bin"]),
    "by_stab": summarize(both, ["part", "horizon", "stab"]),
    "by_quintile": summarize(both, ["part", "horizon", "q_absy"]),
    "by_status": summarize(both.assign(st=both["st0"] + "→" + both["st1"]), ["part", "horizon", "st"]),
    "by_commodity": summarize(both, ["part", "horizon", "commodity"]),
}
for name, t in tabs.items():
    t.round(4).to_csv(os.path.join(OUT, f"p03_{name}.csv"), index=False)
# ringkasan per komoditas: porsi label di bawah 1 tick dan tick sebagai % harga
com = (both.groupby(["part", "horizon", "commodity"])
       .agg(tick_pct=("tick_pct", "median"), sub_tick=("ticks", lambda s: (s < 1).mean()),
            le2_ticks=("ticks", lambda s: (s < 2).mean()), unstable=("flip_boot", lambda s: (s >= 0.05).mean()),
            agree_last=("agree_last", "mean")).reset_index())
com.round(4).to_csv(os.path.join(OUT, "p03_commodity_ticks.csv"), index=False)

summ = {}
for (part, h), x in both.groupby(["part", "horizon"]):
    summ[f"{part}_h{h}"] = {
        "n": len(x), "acc": x["correct"].mean(), "macro_f1": macro_f1(x),
        "sub_tick_share": (x["ticks"] < 1).mean(), "le2_ticks_share": (x["ticks"] < 2).mean(),
        "unstable_share_5pct": (x["flip_boot"] >= 0.05).mean(), "flip_boot_mean": x["flip_boot"].mean(),
        "agree_last": x["agree_last"].mean(), "agree_median": x["agree_median"].mean(), "agree_first": x["agree_first"].mean(),
        "last_zero_share": (x["y_last"] == 0).mean(), "median_zero_share": (x["y_median"] == 0).mean(),
        "endpoint_short_share": ((x["st0"] == "short") | (x["st1"] == "short")).mean(),
        "endpoint_cf_share": ((x["st0"] == "carry_forward") | (x["st1"] == "carry_forward")).mean(),
        "acc_stable": x.loc[x["flip_boot"] < 0.05, "correct"].mean(), "f1_stable": macro_f1(x[x["flip_boot"] < 0.05]),
        "acc_unstable": x.loc[x["flip_boot"] >= 0.05, "correct"].mean(), "f1_unstable": macro_f1(x[x["flip_boot"] >= 0.05]),
        "acc_ge2ticks": x.loc[x["ticks"] >= 2, "correct"].mean(), "f1_ge2ticks": macro_f1(x[x["ticks"] >= 2]),
    }
with open(os.path.join(OUT, "p03_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summ, f, indent=1, default=float)
pred.drop(columns=["stab"]).to_parquet(os.path.join(EXP, "label_audit.parquet"))
pd.set_option("display.width", 220)
print(pd.DataFrame(summ).round(3).to_string())
for name in ("by_tick", "by_stab", "by_quintile", "by_status"):
    print("\n==", name)
    print(tabs[name].round(3).to_string(index=False))
print("\n== commodity ticks (test)")
print(com[com.part == "test"].round(3).to_string(index=False))
