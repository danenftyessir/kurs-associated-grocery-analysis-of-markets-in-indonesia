"""Fitur prediktif dengan as-of join (WP-25). docs/METHODS.md §M4, aturan kebocoran §6.5 proposal."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.data.drivers import realtime_episode_flag
from kagami.utils.config import Config

FEATURE_GROUPS = {
    "base": ["lag_dp_1", "lag_dp_4", "lag_dp_8", "month", "idf_rel_week", "db_1", "db_4"],   # M1
    "fx": ["de_1", "de_4", "de_8", "dw_1", "dw_4", "dw_8", "episode"],                       # M2 = base + fx
    "id": ["commodity", "region"],                                                             # M3 = M2 + id
}
LAG_COLUMNS = ["lag_dp_1", "lag_dp_4", "lag_dp_8"]
WEEK = pd.Timedelta(weeks=1)


def origins(cfg: Config, weeks: pd.Series, horizon: int) -> list[pd.Timestamp]:
    """WP-25. Origin tiap `origin_step_weeks` dari forecast.first_origin s.d. (minggu terakhir data - horizon minggu).

    Minggu terakhir data = max(weeks) (panel dibangun sampai minggu freeze), sehingga target t+h selalu ada untuk origin terakhir.
    """
    p = cfg.params["forecast"]
    last = pd.Timestamp(weeks.max()) - horizon * WEEK
    return list(pd.date_range(pd.Timestamp(p["first_origin"]), last, freq=f"{int(p['origin_step_weeks'])}W-MON"))


def _panel_wide(cfg: Config, panel: pd.DataFrame, weeks: pd.DatetimeIndex) -> tuple[pd.DataFrame, list[str]]:
    """Panel -> lebar (minggu x seri) log harga, serta nama kolom kunci seri (province_id|region + commodity)."""
    if "province_id" in panel.columns:
        key, value = "province_id", "log_price"
    else:
        key, value = "region", "log_price_index"
    wide = panel.pivot(index="week", columns=[key, "commodity"], values=value).reindex(weeks).sort_index(axis=1)
    return wide, [key, "commodity"]


def _driver_features(cfg: Config, drivers: pd.DataFrame, weeks: pd.DatetimeIndex, ks: list[int]) -> pd.DataFrame:
    d = drivers.set_index("week").reindex(weeks)
    out = pd.DataFrame(index=weeks)
    for k in ks:
        out[f"de_{k}"] = d["log_e"] - d["log_e"].shift(k)
        out[f"db_{k}"] = d["log_brent"] - d["log_brent"].shift(k)
    # D-162 (U108): flag real-time dari de s.d. t, bukan `episode` periode penuh (yang menggabungkan pemicu masa depan)
    out["episode"] = (realtime_episode_flag(cfg, drivers).reindex(weeks).fillna(0).astype(int)
                      if "de" in drivers else 0)
    out["month"] = d["month"]
    out["idf_rel_week"] = d["idf_rel_week"]
    return out


def _world_features(world: pd.DataFrame, weeks: pd.DatetimeIndex, ks: list[int]) -> pd.DataFrame:
    """As-of: untuk minggu t dipakai baris harga dunia terakhir dengan available_at <= t; dw_k = selisih level as-of."""
    w = world.dropna(subset=["log_w_idr"]).sort_values("available_at")
    grid = pd.DataFrame({"week": weeks})
    frames = []
    for c, g in w.groupby("commodity"):
        m = pd.merge_asof(grid, g[["available_at", "log_w_idr"]], left_on="week", right_on="available_at",
                          direction="backward")
        for k in ks:
            m[f"dw_{k}"] = m["log_w_idr"] - m["log_w_idr"].shift(k)
        m["commodity"] = c
        frames.append(m.rename(columns={"available_at": "world_available_at"}).drop(columns="log_w_idr"))
    cols = ["week", "commodity", "world_available_at"] + [f"dw_{k}" for k in ks]
    return pd.concat(frames, ignore_index=True)[cols] if frames else pd.DataFrame(columns=cols)


def feature_table(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                  horizons: list[int] | None = None) -> pd.DataFrame:
    """WP-25. Tabel fitur seluruh (minggu x seri) + target `y_<h>` = log_price_{t+h} - log_price_t untuk tiap horizon.

    Semua fitur pada minggu t hanya memakai informasi sampai minggu t: lag harga (selisih ke belakang), penggerak harian
    (JISDOR, Brent) tersedia pada minggu itu, harga dunia memakai as-of `available_at <= t` (kolom `world_available_at`
    disertakan untuk audit kebocoran). Seri = provinsi x komoditas bila panel punya `province_id`, selain itu wilayah x komoditas.
    """
    p = cfg.params["forecast"]
    ks, horizons = list(p["feature_changes_weeks"]), list(horizons or p["horizons"])
    weeks = pd.date_range(drivers["week"].min(), drivers["week"].max(), freq="W-MON")
    wide, keys = _panel_wide(cfg, panel, weeks)
    parts = {f"lag_dp_{k}": wide - wide.shift(k) for k in ks}
    parts["log_p"] = wide
    for h in horizons:
        parts[f"y_{h}"] = wide.shift(-h) - wide
    long = pd.concat({name: df.stack([0, 1], future_stack=True) for name, df in parts.items()}, axis=1)
    long.index.names = ["week"] + keys
    tab = long.reset_index()
    if keys[0] == "province_id":
        tab["region"] = tab["province_id"].map(cfg.regions.set_index("province_id")["region"])
    drv = _driver_features(cfg, drivers, weeks, ks).rename_axis("week").reset_index()
    tab = tab.merge(drv, on="week", how="left")
    tab = tab.merge(_world_features(world, weeks, ks), on=["week", "commodity"], how="left")
    for c in [c for c in tab.columns if c.startswith("dw_")] + ["world_available_at"]:
        if c not in tab:
            tab[c] = np.nan
    return tab.sort_values(keys + ["week"]).reset_index(drop=True)


def split_origin(cfg: Config, table: pd.DataFrame, origin: pd.Timestamp,
                 horizon: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WP-25. (train, test) untuk satu origin dari `feature_table`.

    Train = baris dengan t + h <= origin (outcome sudah terealisasi pada origin). Test = baris t == origin.
    Baris tanpa target atau tanpa lag harga dibuang. Kolom keluaran: fitur, `y` (target), `origin`, `horizon`.
    """
    origin = pd.Timestamp(origin)
    other = [c for c in table.columns if c.startswith("y_") and c != f"y_{horizon}"]
    t = table.drop(columns=other).rename(columns={f"y_{horizon}": "y"})
    t = t.dropna(subset=["y"] + LAG_COLUMNS).assign(origin=origin, horizon=horizon)
    train = t[t["week"] + horizon * WEEK <= origin].reset_index(drop=True)
    test = t[t["week"] == origin].reset_index(drop=True)
    return train, test


def build_features(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                   origin: pd.Timestamp, horizon: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WP-25. -> (train, test) untuk satu origin.

    Target = log_price_{t+h} - log_price_t per seri. Train hanya baris dengan t+h <= origin (outcome sudah
    terealisasi). Join harga dunia memakai available_at <= minggu fitur (as-of); data harian (JISDOR, Brent)
    tersedia hari yang sama. TIDAK ADA pembagian acak per baris.
    """
    return split_origin(cfg, feature_table(cfg, panel, drivers, world, [horizon]), origin, horizon)
