"""Penggerak mingguan: kurs, harga dunia dalam rupiah, Brent, indeks dolar, kalender, episode.
(WP-05, WP-06). Spesifikasi: docs/METHODS.md §M0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config
from kagami.utils.dates import week_start


def driver_weeks(cfg: Config) -> pd.DatetimeIndex:
    """Grid minggu penggerak: period.start - driver_buffer_weeks s.d. minggu period.freeze.

    Buffer memberi lag (L ≤ 8, db lag 4) dan jendela episode 8 minggu untuk minggu awal periode.
    """
    p = cfg.params["period"]
    start = pd.Timestamp(p["start"]) - pd.Timedelta(weeks=int(p["driver_buffer_weeks"]))
    first = week_start(pd.Series([start])).iloc[0]
    last = week_start(pd.Series([pd.Timestamp(p["freeze"])])).iloc[0]
    return pd.date_range(first, last, freq="W-MON")


def _weekly_log_mean(daily: pd.DataFrame, value_col: str, weeks: pd.DatetimeIndex,
                     last_date: pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    """Rerata log nilai harian per minggu ISO pada grid; minggu tanpa observasi = level minggu sebelumnya
    (pasar tutup -> tidak ada perubahan; D-025). Return (log_level, filled_flag)."""
    d = daily[(daily["date"] <= last_date) & (daily[value_col] > 0)]
    s = np.log(d[value_col]).groupby(week_start(d["date"]).values).mean()
    s = s.reindex(weeks)
    return s.ffill(), s.isna()


def idulfitri_relative_week(cfg: Config, weeks: pd.DatetimeIndex) -> pd.Series:
    """Minggu relatif terhadap minggu Idulfitri terdekat; NaN di luar params.calendar.idulfitri_window."""
    lo, hi = cfg.params["calendar"]["idulfitri_window"]
    idf = week_start(pd.Series(pd.to_datetime(cfg.params["calendar"]["idulfitri"]))).to_numpy()
    diff = (weeks.to_numpy()[:, None] - idf[None, :]) / np.timedelta64(7, "D")
    rel = diff[np.arange(len(weeks)), np.abs(diff).argmin(axis=1)]
    return pd.Series(np.where((rel >= lo) & (rel <= hi), rel, np.nan), index=weeks)


def build_national_drivers(cfg: Config, jisdor: pd.DataFrame, brent: pd.DataFrame,
                           dxy: pd.DataFrame) -> pd.DataFrame:
    """WP-05. Penggerak nasional mingguan (tanpa kolom `episode`; ditambahkan mark_episode_weeks, WP-06).

    log_e = rerata log JISDOR harian dalam minggu ISO; de = Δ log_e; de_pos = max(de,0); de_neg = min(de,0).
    log_brent/db dan log_dxy/d_dxy idem dari FRED. Minggu tanpa observasi: level diteruskan (D-025),
    ditandai e_filled/brent_filled/dxy_filled. month = bulan hari Senin (D-016). idf_rel_week = minggu relatif
    Idulfitri dalam params.calendar.idulfitri_window (NaN di luar jendela).
    Grid: driver_weeks (buffer sebelum period.start untuk lag).
    """
    weeks = driver_weeks(cfg)
    last = pd.Timestamp(cfg.params["period"]["freeze"])
    out = pd.DataFrame(index=weeks)
    for name, df, col in (("e", jisdor, "idr_per_usd"), ("brent", brent, "value"), ("dxy", dxy, "value")):
        level, filled = _weekly_log_mean(df, col, weeks, last)
        out[f"log_{name}"] = level
        out[f"{name}_filled"] = filled
    out["de"] = out["log_e"].diff()
    out["de_pos"] = out["de"].clip(lower=0)
    out["de_neg"] = out["de"].clip(upper=0)
    out["db"] = out["log_brent"].diff()
    out["d_dxy"] = out["log_dxy"].diff()
    out["month"] = weeks.month
    out["idf_rel_week"] = idulfitri_relative_week(cfg, weeks)
    out = out.rename_axis("week").reset_index()
    cols = ["week", "log_e", "de", "de_pos", "de_neg", "log_brent", "db", "log_dxy", "d_dxy", "month",
            "idf_rel_week", "e_filled", "brent_filled", "dxy_filled"]
    return out[cols]


def _second_business_day_next_month(months: pd.Series) -> pd.Series:
    nxt = (months + pd.offsets.MonthBegin(1)).values.astype("datetime64[D]")
    return pd.Series(np.busday_offset(nxt, 1, roll="forward").astype("datetime64[ns]"), index=months.index)


def build_world_prices(cfg: Config, pinksheet: pd.DataFrame, jisdor: pd.DataFrame) -> pd.DataFrame:
    """WP-05. Harga dunia padanan per komoditas -> artefak 'world_prices_weekly'.

    log_w_usd(i,m) = Σ bobot × log harga USD seri Pink Sheet (configs/commodities.yaml: pinksheet); NaN bila ada
    komponen yang kosong. log_w_idr(i,m) = log_w_usd(i,m) + rerata log JISDOR harian BULAN m (selaras periode
    observasi, Task 1-3; METHODS §M0.4, D-016). Mingguan: minggu memakai bulan hari Seninnya, sehingga
    dw = Δ log_w_idr mingguan bernilai nol di dalam bulan dan berubah pada minggu pertama bulan baru (D-025).
    available_at = hari kerja ke-2 bulan berikutnya (Senin-Jumat; as-of Task 4).
    Komoditas tanpa padanan tidak muncul (bukan diisi nol). Bulan setelah rilis Pink Sheet terakhir -> NaN.
    """
    weeks = driver_weeks(cfg)
    j = jisdor[jisdor["idr_per_usd"] > 0]
    log_e_month = np.log(j["idr_per_usd"]).groupby(j["date"].dt.to_period("M").dt.to_timestamp()).mean()
    needed = sorted({s for v in cfg.commodities.values() for s in v["pinksheet"]})
    ps = pinksheet[pinksheet["series"].isin(needed) & (pinksheet["usd_price"] > 0)]
    wide = np.log(ps.pivot_table(index="month", columns="series", values="usd_price", aggfunc="first"))
    wide = wide.reindex(columns=needed)
    frames = []
    for cid, spec in cfg.commodities.items():
        if not spec["pinksheet"]:
            continue
        comp = sum(w * wide[s] for s, w in spec["pinksheet"].items())   # NaN bila ada komponen kosong
        monthly = pd.DataFrame({"log_w_usd": comp, "log_w_idr": comp + log_e_month.reindex(comp.index)})
        wk = pd.DataFrame({"week": weeks, "month": weeks.to_period("M").to_timestamp()})
        wk = wk.merge(monthly, left_on="month", right_index=True, how="left")
        wk["dw"] = wk["log_w_idr"].diff()
        wk["available_at"] = _second_business_day_next_month(wk["month"])
        frames.append(wk.assign(commodity=cid))
    out = pd.concat(frames, ignore_index=True)
    return out[["week", "commodity", "month", "log_w_usd", "log_w_idr", "dw", "available_at"]]


class _CommodityOverride:
    """Config dengan `commodities` diganti (sisanya diteruskan ke Config asli); hanya untuk build_world_variants."""

    def __init__(self, cfg: Config, commodities: dict):
        self._cfg, self.commodities = cfg, commodities

    def __getattr__(self, name):
        return getattr(self._cfg, name)


def build_world_variants(cfg: Config, pinksheet: pd.DataFrame, jisdor: pd.DataFrame) -> pd.DataFrame:
    """WP-30. Komposit harga dunia alternatif untuk komoditas dengan >= 2 seri Pink Sheet (pakan: daging ayam,
    telur; D-012 robustness): bobot sama 1/k dan setiap seri tunggal. Konstruksi identik build_world_prices.

    Output: kolom build_world_prices + variant (mis. "equal_weights", "Maize", "Soybean meal").
    """
    frames = []
    for cid, spec in cfg.commodities.items():
        series = list(spec["pinksheet"] or {})
        if len(series) < 2:
            continue
        alts = {"equal_weights": {s: 1 / len(series) for s in series}} | {s: {s: 1.0} for s in series}
        for name, weights in alts.items():
            sub = _CommodityOverride(cfg, {cid: {**spec, "pinksheet": weights}})
            frames.append(build_world_prices(sub, pinksheet, jisdor).assign(variant=name))
    cols = ["week", "commodity", "month", "log_w_usd", "log_w_idr", "dw", "available_at", "variant"]
    return pd.concat(frames, ignore_index=True)[cols] if frames else pd.DataFrame(columns=cols)


def realtime_episode_flag(cfg: Config, drivers: pd.DataFrame) -> pd.Series:
    """D-162 (U108). Flag episode yang hanya memakai de s.d. minggu t (fitur `episode` Task 4).

    = 1 bila minggu t adalah minggu pemicu (Σ de 8 minggu s.d. t >= ambang, aturan `find_episodes`), selain itu 0.
    Setara dengan `mark_episode_weeks(drivers s.d. t, find_episodes(drivers s.d. t))` pada minggu t: dengan data s.d. t,
    akhir episode terbaru = pemicu terakhir <= t, jadi t berada di dalam episode hanya bila t sendiri pemicu. Flag periode
    penuh (`drivers_weekly.episode`) juga menandai minggu di antara dua pemicu yang digabung sebelum pemicu kedua diketahui.
    -> Series 0/1 berindeks week (urut).
    """
    p = cfg.params["episodes"]
    win, thr = int(p["window_weeks"]), float(p["cum_depreciation"])
    d = drivers.sort_values("week")
    roll = d["de"].rolling(win, min_periods=win).sum()
    return pd.Series((roll >= thr).to_numpy().astype(int), index=pd.DatetimeIndex(d["week"]), name="episode")


def mark_episode_weeks(drivers: pd.DataFrame, episodes: pd.DataFrame) -> pd.DataFrame:
    """WP-06. Tambah kolom `episode` (1 bila start_week <= week <= end_week suatu episode, selain itu 0)."""
    out = drivers.copy()
    flag = np.zeros(len(out), dtype=int)
    for s, e in zip(pd.to_datetime(episodes["start_week"]), pd.to_datetime(episodes["end_week"])):
        flag |= ((out["week"] >= s) & (out["week"] <= e)).to_numpy().astype(int)
    out["episode"] = flag
    return out


def find_episodes(cfg: Config, drivers: pd.DataFrame) -> pd.DataFrame:
    """WP-06. Episode depresiasi: Σ de dalam jendela 8 minggu >= 0.03 (params.episodes; METHODS §M0.5).

    Minggu t = pemicu bila Σ_{s=t-W+1..t} de_s >= ambang (W = window_weeks; butuh W nilai de lengkap).
    Pemicu yang jendelanya tumpang tindih atau berdempetan (jarak antar pemicu <= W minggu) digabung.
    start_week = pemicu pertama; end_week = pemicu terakhir; cum_dlog_e = Σ de jendela maksimum dalam episode.
    Kolom ekstra: peak_week (minggu Σ maksimum), n_trigger_weeks, in_period (start_week >= period.start).
    Seluruh grid penggerak dipakai (buffer 2017 ikut, agar episode yang melintasi awal periode tidak terpotong).
    -> artefak 'episodes' (episode_id, start_week, end_week, cum_dlog_e).
    """
    p = cfg.params["episodes"]
    win, thr = int(p["window_weeks"]), float(p["cum_depreciation"])
    d = drivers.sort_values("week").reset_index(drop=True)
    roll = d["de"].rolling(win, min_periods=win).sum()
    trig = np.flatnonzero((roll >= thr).to_numpy())
    cols = ["episode_id", "start_week", "end_week", "cum_dlog_e", "peak_week", "n_trigger_weeks", "in_period"]
    if len(trig) == 0:
        return pd.DataFrame(columns=cols)
    groups = np.concatenate([[0], np.cumsum(np.diff(trig) > win)])
    start = pd.Timestamp(cfg.params["period"]["start"])
    rows = []
    for g in np.unique(groups):
        idx = trig[groups == g]
        r = roll.iloc[idx]
        rows.append({"start_week": d["week"].iloc[idx[0]], "end_week": d["week"].iloc[idx[-1]],
                     "cum_dlog_e": float(r.max()), "peak_week": d["week"].iloc[int(r.idxmax())],
                     "n_trigger_weeks": len(idx)})
    out = pd.DataFrame(rows)
    out.insert(0, "episode_id", np.arange(1, len(out) + 1))
    out["in_period"] = out["start_week"] >= start
    return out[cols]


def fx_variation_table(cfg: Config, drivers: pd.DataFrame) -> pd.DataFrame:
    """WP-06. Jumlah & besar minggu depresiasi/apresiasi per tahun + total -> artefak 'fx_variation'.

    Hanya minggu period.start .. period.freeze (buffer tidak dihitung). period = tahun kalender minggu (Senin)
    atau 'total'. n_dep_weeks: de > 0; n_app_weeks: de < 0; mean_dep / mean_app = rerata de pada minggu itu;
    sd_de. Kolom ekstra: n_weeks, n_zero_weeks (termasuk minggu libur yang diteruskan, D-025), max_de, min_de,
    n_episode_weeks (bila kolom `episode` ada).
    """
    start = pd.Timestamp(cfg.params["period"]["start"])
    d = drivers[(drivers["week"] >= start) & drivers["de"].notna()].copy()
    if "episode" not in d:
        d["episode"] = 0

    def summarize(g: pd.DataFrame) -> dict:
        de = g["de"]
        return {"n_weeks": len(g), "n_dep_weeks": int((de > 0).sum()), "n_app_weeks": int((de < 0).sum()),
                "n_zero_weeks": int((de == 0).sum()), "mean_dep": de[de > 0].mean(), "mean_app": de[de < 0].mean(),
                "sd_de": de.std(), "max_de": de.max(), "min_de": de.min(), "n_episode_weeks": int(g["episode"].sum())}

    rows = [{"period": str(y), **summarize(g)} for y, g in d.groupby(d["week"].dt.year)]
    rows.append({"period": "total", **summarize(d)})
    out = pd.DataFrame(rows)
    return out[["period", "n_dep_weeks", "n_app_weeks", "mean_dep", "mean_app", "sd_de", "n_weeks",
                "n_zero_weeks", "max_de", "min_de", "n_episode_weeks"]]
