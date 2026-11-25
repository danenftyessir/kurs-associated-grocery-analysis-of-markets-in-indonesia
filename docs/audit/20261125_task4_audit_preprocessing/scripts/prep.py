"""Bangun tabel varian preprocessing untuk eksperimen (EXP_DIR = env KAGAMI_EXP, default scratchpad).

Semua tabel punya baris & urutan identik dengan tabel resmi C1-tuned (`feature_table` + `price_dynamics.extend_table`) dan
TARGET RESMI (y_4, y_8 dari rerata hari teramati). Yang berubah hanya fitur, bobot, atau penyaring baris LATIH.
- base.parquet     : tabel resmi + kolom kualitas label (ticks_h, flip_h, st0, st_h) + iw_gap, n_days (dipakai varian tertentu)
- last.parquet     : fitur dari harga hari teramati TERAKHIR minggu (bukan rerata); target tetap resmi
- noffill.parquet  : fitur tanpa ffill celah harga (FFILL_WEEKS = 0), range_pos_52 = NaN bila tak terdefinisi, + n_missing_13
- volnorm.parquet  : fitur bertipe return dibagi sd Δp 52 minggu ke belakang seri (normalisasi per seri, hanya masa lalu)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg, load  # noqa: E402
from kagami.features import price_dynamics  # noqa: E402
from kagami.features.forecast import feature_table  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

EXP = os.environ.get("KAGAMI_EXP", r"C:\Users\HYPERS~1\AppData\Local\Temp\claude\92509b33971ecddd\b18f9307-3852-462a-bd0d-67a285eb70b9\scratchpad\exp")
os.makedirs(EXP, exist_ok=True)
H = [4, 8]
KEYS = ["province_id", "commodity", "week"]
TICK, B = 50.0, 100
RETURN_LIKE = ["lag_dp_1", "lag_dp_4", "lag_dp_8", "dp1_l1", "dp1_l2", "dp1_l3", "lag_dp_13", "lag_dp_26", "lag_dp_52",
               "ewm_dp_4", "ewm_dp_13", "std_dp_4", "std_dp_13", "std_dp_26", "accel_4", "dev_ma13", "dev_ma52",
               "spatial_dev", "spatial_dev_chg4", "yseas_52_h4", "yseas_104_h4", "yseas_52_h8", "yseas_104_h8"]


def build(panel):
    return price_dynamics.extend_table(feature_table(cfg, panel, drivers, world, H), panel, H)


t0 = time.time()
panel, drivers, world = load()
base = build(panel)
order = base[KEYS].copy()

# ---- statistik harian per minggu
daily = read_artifact(cfg, "pihps_daily")
daily["week"] = daily["date"] - pd.to_timedelta(daily["date"].dt.dayofweek, unit="D")
daily = daily.sort_values(["province_id", "commodity", "date"])
g = daily.groupby(["province_id", "commodity", "week"])["price"]
wk = pd.DataFrame({"mean": g.mean(), "last": g.last(), "n": g.size()})
daily["pos"] = daily.groupby(["province_id", "commodity", "week"]).cumcount()
M = daily.pivot_table(index=["province_id", "commodity", "week"], columns="pos", values="price", aggfunc="first").reindex(wk.index).to_numpy(float)
nday = wk["n"].to_numpy()
cell = pd.Series(np.arange(len(wk)), index=wk.index)
key = pd.MultiIndex.from_frame(base[KEYS])
i0 = cell.reindex(key).to_numpy()
base["iw_gap"] = np.log(wk["last"].to_numpy()[np.nan_to_num(i0, nan=0).astype(int)]) - np.log(wk["mean"].to_numpy()[np.nan_to_num(i0, nan=0).astype(int)])
base.loc[np.isnan(i0), "iw_gap"] = np.nan
base["n_days"] = np.where(np.isnan(i0), 0, nday[np.nan_to_num(i0, nan=0).astype(int)])
st = panel.set_index(KEYS)["status"]
base["st0"] = st.reindex(key).to_numpy()
rng = np.random.default_rng(cfg.seed + 7102)


def boot_mean(idx):
    n = nday[idx]
    u = rng.random((len(idx), B, 5))
    j = np.floor(u * n[:, None, None]).astype(int)
    vals = np.take_along_axis(np.repeat(M[idx][:, None, :], B, 1), j, axis=2)
    keep = np.arange(5)[None, None, :] < n[:, None, None]
    return np.where(keep, vals, 0).sum(2) / n[:, None]


mean_v = wk["mean"].to_numpy(float)
for h in H:
    k1 = pd.MultiIndex.from_arrays([base["province_id"], base["commodity"], base["week"] + pd.Timedelta(weeks=h)])
    i1 = cell.reindex(k1).to_numpy()
    ok = ~np.isnan(i0) & ~np.isnan(i1) & base[f"y_{h}"].notna().to_numpy()
    a, b = i0[ok].astype(int), i1[ok].astype(int)
    base[f"ticks_{h}"] = np.nan
    base.loc[ok, f"ticks_{h}"] = np.abs(mean_v[b] - mean_v[a]) / TICK
    base[f"st_{h}"] = st.reindex(k1).to_numpy()
    flip = np.full(ok.sum(), np.nan)
    up = base.loc[ok, f"y_{h}"].to_numpy() > 0
    for s in range(0, len(a), 5000):
        yb = np.log(boot_mean(b[s:s + 5000])) - np.log(boot_mean(a[s:s + 5000]))
        flip[s:s + 5000] = ((yb > 0) != up[s:s + 5000][:, None]).mean(1)
    base[f"flip_{h}"] = np.nan
    base.loc[ok, f"flip_{h}"] = flip
    print(f"h{h}: ticks & flip", round(time.time() - t0), "dtk")
base.to_parquet(os.path.join(EXP, "base.parquet"))
ycols = [f"y_{h}" for h in H]

# ---- fitur dari hari terakhir minggu
pl = panel.copy()
k = pd.MultiIndex.from_frame(pl[KEYS])
pl["price"] = wk["last"].reindex(k).to_numpy()
pl["log_price"] = np.log(pl["price"])
last = build(pl)
assert last[KEYS].equals(order)
last[ycols] = base[ycols].to_numpy()
last.to_parquet(os.path.join(EXP, "last.parquet"))
print("last", round(time.time() - t0), "dtk")

# ---- tanpa ffill + range_pos jujur + jumlah minggu hilang 13
_ffill = pd.DataFrame.ffill


def _nofill(self, *a, limit=None, **k):          # limit = -1 → tanpa pengisian (pandas menolak limit 0)
    return self.copy() if limit == -1 else _ffill(self, *a, limit=limit, **k)


price_dynamics.FFILL_WEEKS, pd.DataFrame.ffill = -1, _nofill
nof = build(panel)
price_dynamics.FFILL_WEEKS, pd.DataFrame.ffill = 8, _ffill
assert nof[KEYS].equals(order)
wide = nof.pivot(index="week", columns=["province_id", "commodity"], values="log_p").sort_index()
hi, lo = wide.rolling(52, min_periods=26).max(), wide.rolling(52, min_periods=26).min()
rp = ((wide - lo) / (hi - lo)).where(hi > lo)
rp = rp.where(~(hi == lo), 0.5)                      # rentang datar terdefinisi = 0,5; tak terdefinisi = NaN
miss13 = wide.isna().astype(float).rolling(13, min_periods=1).sum()
for name, F in (("range_pos_52", rp), ("n_missing_13", miss13)):
    s = F.stack(["province_id", "commodity"], future_stack=True).rename(name).reset_index()
    nof = nof.drop(columns=[name], errors="ignore").merge(s, on=["week", "province_id", "commodity"], how="left")
nof = nof.set_index(KEYS).loc[pd.MultiIndex.from_frame(order)].reset_index()
assert nof[KEYS].equals(order)
nof.to_parquet(os.path.join(EXP, "noffill.parquet"))
print("noffill", round(time.time() - t0), "dtk; range_pos NaN", round(nof["range_pos_52"].isna().mean(), 4))

# ---- normalisasi per seri (sd Δp 52 minggu ke belakang)
vn = base.copy()
# skala = sd Δp 52 minggu; bila belum ada (pemanasan) sd ekspansif ke belakang (≥ 4 minggu); seri datar (sd 0) → 1.
# Pola NaN kolom lag resmi tidak berubah, jadi baris latih/test identik dengan base.
exp_sd = (vn.groupby(["province_id", "commodity"])["lag_dp_1"]
          .transform(lambda s: s.expanding(min_periods=4).std()))
scale = vn["std_dp_52"].where(vn["std_dp_52"] > 0).fillna(exp_sd.where(exp_sd > 0)).fillna(1.0)
for c in RETURN_LIKE:
    vn[c] = vn[c] / scale
for c in ("lag_dp_1", "lag_dp_4", "lag_dp_8"):
    assert vn[c].isna().equals(base[c].isna())
vn.to_parquet(os.path.join(EXP, "volnorm.parquet"))
print("volnorm selesai", round(time.time() - t0), "dtk; skala cadangan", round((vn["std_dp_52"].isna() | (vn["std_dp_52"] == 0)).mean(), 4))
