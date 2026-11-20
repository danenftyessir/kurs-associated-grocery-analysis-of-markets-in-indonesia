"""Panel 7 wilayah (WP-08) -- peta utama 7 wilayah; ikut paket juri bersama panel provinsi (D-104)."""

from __future__ import annotations

import pandas as pd

from kagami.utils.config import Config

_MAX_ITER, _TOL = 500, 1e-10   # konstanta numerik dekomposisi dua arah (bukan parameter analisis)


def build_region_panel(cfg: Config, weekly: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """WP-08. -> artefak 'panel_weekly_region'.

    Hanya seri eligible. Per (week, region, commodity): rerata log harga provinsi (bobot sama),
    lalu dinormalkan: log_price_index = rerata - nilai minggu pertama seri (indeks, bukan level Rp,
    agar tidak merekonstruksi data mentah PIHPS). n_provinces = jumlah provinsi yang teramati minggu itu.

    Komposisi berubah (provinsi `missing` pada suatu minggu) tidak boleh menimbulkan lompatan level: per (wilayah,
    komoditas) log harga diurai p(r,t) = a_r + l_t (efek provinsi + efek minggu, alternating projection), lalu
    rerata wilayah = l_t + rerata a_r semua provinsi eligible (D-106). Bila semua provinsi teramati sepanjang
    periode, hasilnya identik dengan rerata biasa.
    Minggu tanpa satu pun provinsi teramati -> log_price_index NaN, n_provinces 0.
    """
    ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
    w = weekly.merge(ok, on=["province_id", "commodity"], how="inner")
    w = w.merge(cfg.regions[["province_id", "region"]], on="province_id", how="left")
    if w["region"].isna().any():
        raise ValueError("province_id tanpa wilayah di region_crosswalk.csv")
    keys = ["week", "region", "commodity"]
    series = ["province_id", "commodity"]
    # dekomposisi dua arah p(r,t) = a_r + l_t per (wilayah, komoditas), alternating projection sampai konvergen
    obs = w["log_price"].notna()
    lam = pd.Series(0.0, index=w.index)
    for _ in range(_MAX_ITER):
        a = (w["log_price"] - lam).groupby([w[c] for c in series]).transform("mean")
        new = (w["log_price"] - a).groupby([w[c] for c in keys]).transform("mean")
        if (new - lam)[obs].abs().max() < _TOL:
            lam = new
            break
        lam = new.fillna(0.0)
    w = w.assign(lam=lam.where(obs.groupby([w[c] for c in keys]).transform("any")), a=a)
    g = w.groupby(keys).agg(lam=("lam", "first"), n_provinces=("log_price", "count")).reset_index()
    level = (w.drop_duplicates(series).groupby(["region", "commodity"])["a"].mean()
             .rename("a_region").reset_index())
    g = g.merge(level, on=["region", "commodity"])
    g["log_mean"] = g["lam"] + g["a_region"]
    g = g.sort_values(keys).reset_index(drop=True)
    first = g.dropna(subset=["log_mean"]).groupby(["region", "commodity"])["log_mean"].first().rename("base")
    g = g.merge(first, on=["region", "commodity"], how="left")
    g["log_price_index"] = g["log_mean"] - g["base"]
    g["n_provinces"] = g["n_provinces"].astype(int)
    return g[["week", "region", "commodity", "log_price_index", "n_provinces"]].sort_values(
        ["commodity", "region", "week"]).reset_index(drop=True)
