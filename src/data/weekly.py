"""Agregasi mingguan PIHPS + kode status + kelayakan seri (WP-03, WP-04). Spesifikasi: docs/METHODS.md §M0."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config
from kagami.data.loaders import norm_name
from kagami.utils.dates import week_start

STATUS_CODES = ("observed", "carry_forward", "short", "missing")



def select_variants(cfg: Config, pihps: pd.DataFrame) -> pd.DataFrame:
    """WP-03. Pilih varian representatif per komoditas (configs/commodities.yaml: variant).

    Input : keluaran loaders.load_pihps.
    Output: date, province_id, commodity (id internal), variant, price  -> artefak 'pihps_daily'.
            Hanya hari TERAMATI (price NaN dibuang); hari tak teramati muncul lagi sebagai n_days di agregasi.
    Wajib : nama varian dicocokkan setelah norm_name; komoditas tanpa varian cocok -> error, bukan diam.
    """
    lv2 = pihps[pihps["level"] == 2]
    items = lv2["item"].map(norm_name)
    frames = []
    for cid, spec in cfg.commodities.items():
        variant = norm_name(spec["variant"])
        mask = (lv2["commodity_group"] == spec["pihps_name"]) & (items == variant)
        if not mask.any():
            raise ValueError(f"{cid}: varian '{variant}' di bawah '{spec['pihps_name']}' tidak ada di PIHPS")
        frames.append(lv2.loc[mask, ["date", "province_id", "price"]].assign(commodity=cid, variant=variant))
    out = pd.concat(frames, ignore_index=True).dropna(subset=["price"])
    out = out[out["price"] > 0]
    out["province_id"] = out["province_id"].astype(int)
    return (out[["date", "province_id", "commodity", "variant", "price"]]
            .sort_values(["province_id", "commodity", "date"]).reset_index(drop=True))


def _carry_forward_flags(daily: pd.DataFrame, run_days: int) -> pd.Series:
    """True bila hari teramati termasuk rangkaian nilai identik >= run_days hari teramati berturut-turut.

    `daily` harus terurut per (province_id, commodity, date). Hari tak teramati tidak memutus rangkaian
    (pasar tutup lalu harga sama = tetap rangkaian identik).
    """
    new_series = (daily["province_id"].ne(daily["province_id"].shift())
                  | daily["commodity"].ne(daily["commodity"].shift()))
    new_run = new_series | daily["price"].ne(daily["price"].shift())
    run_id = new_run.cumsum()
    return run_id.map(run_id.value_counts()) >= run_days


def aggregate_weekly(cfg: Config, daily: pd.DataFrame) -> pd.DataFrame:
    """WP-03. Rerata hari kerja TERAMATI per minggu ISO -> artefak 'panel_weekly'.

    Kolom: week, province_id, commodity, price, log_price, n_days, status (+ cf_share informatif).
    status (prioritas D-021): missing (n_days == 0; price NaN) > carry_forward (cf_share > 0,5)
            > short (n_days <= weekly.short_week_days) > observed.
    Grid lengkap: 34 provinsi x 10 komoditas x minggu dari period.start s.d. minggu period.freeze.
    Hari carry-forward = bagian dari rangkaian nilai identik >= weekly.carry_forward_run_days hari kerja
    berturut-turut dalam satu seri (diduga pasar tutup / pedagang tidak berganti nilai). Rangkaian dihitung
    pada seluruh riwayat sebelum dipotong ke periode, sehingga rangkaian yang melintasi period.start terhitung.
    """
    wp = cfg.params["weekly"]
    period = cfg.params["period"]
    weeks = pd.date_range(week_start(pd.Series([pd.Timestamp(period["start"])])).iloc[0],
                          week_start(pd.Series([pd.Timestamp(period["freeze"])])).iloc[0], freq="W-MON")
    return _aggregate(daily, weeks, cfg.regions["province_id"].astype(int).tolist(), list(cfg.commodities),
                      run_days=wp["carry_forward_run_days"], short_days=wp["short_week_days"],
                      last_date=pd.Timestamp(period["freeze"]))


def _aggregate(daily: pd.DataFrame, weeks: pd.DatetimeIndex, provinces: list[int], commodities: list[str],
               run_days: int, short_days: int, last_date: pd.Timestamp) -> pd.DataFrame:
    d = daily.sort_values(["province_id", "commodity", "date"]).reset_index(drop=True)
    d["cf"] = _carry_forward_flags(d, run_days)
    d = d[(d["date"] >= weeks[0]) & (d["date"] <= last_date)].copy()
    d["week"] = week_start(d["date"])
    agg = (d.groupby(["province_id", "commodity", "week"])
           .agg(price=("price", "mean"), n_days=("price", "size"), cf_share=("cf", "mean"))
           .reset_index())
    grid = pd.MultiIndex.from_product([provinces, commodities, weeks],
                                      names=["province_id", "commodity", "week"]).to_frame(index=False)
    out = grid.merge(agg, on=["province_id", "commodity", "week"], how="left")
    out["n_days"] = out["n_days"].fillna(0).astype(int)
    out["log_price"] = np.log(out["price"])
    out["status"] = np.select(
        [out["n_days"] == 0, out["cf_share"] > 0.5, out["n_days"] <= short_days],
        ["missing", "carry_forward", "short"], default="observed")
    return out[["week", "province_id", "commodity", "price", "log_price", "n_days", "status", "cf_share"]]


def eligibility(cfg: Config, weekly: pd.DataFrame) -> pd.DataFrame:
    """WP-04. Kelayakan seri -> artefak 'eligibility'.

    eligible = missing_share <= 0.20 AND max_gap_weeks <= 8 AND min_year_coverage >= 0.70 (params.eligibility).
    Seri tidak layak tetap dilaporkan (jangan dibuang diam-diam).
    Hanya status `missing` yang dihitung kosong; `carry_forward`/`short` tetap teramati (U22).
    missing_share & max_gap_weeks dihitung atas seluruh grid minggu; min_year_coverage = porsi minggu teramati
    terendah di antara tahun kalender dalam grid (tahun parsial 2026 dinilai atas minggu yang ada di grid).
    """
    e = cfg.params["eligibility"]
    w = weekly.sort_values(["province_id", "commodity", "week"]).reset_index(drop=True)
    miss = w["status"].eq("missing")
    key = ["province_id", "commodity"]

    # panjang rangkaian minggu kosong berturut-turut per seri
    new_run = (miss.ne(miss.shift()) | w["province_id"].ne(w["province_id"].shift())
               | w["commodity"].ne(w["commodity"].shift()))
    run_id = new_run.cumsum()
    gap = (w.assign(miss=miss, run_id=run_id)[miss]
           .groupby(key + ["run_id"]).size().groupby(key).max().rename("max_gap_weeks"))

    year_cov = (w.assign(obs=~miss, year=w["week"].dt.year)
                .groupby(key + ["year"])["obs"].mean().groupby(key).min().rename("min_year_coverage"))
    out = (w.assign(miss=miss).groupby(key)["miss"].mean().rename("missing_share").to_frame()
           .join(gap).join(year_cov).reset_index())
    out["max_gap_weeks"] = out["max_gap_weeks"].fillna(0).astype(int)
    out["eligible"] = ((out["missing_share"] <= e["max_missing_share"])
                       & (out["max_gap_weeks"] <= e["max_gap_weeks"])
                       & (out["min_year_coverage"] >= e["min_year_coverage"]))
    return out[["province_id", "commodity", "missing_share", "max_gap_weeks", "min_year_coverage", "eligible"]]
