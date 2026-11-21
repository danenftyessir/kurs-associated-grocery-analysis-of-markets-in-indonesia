"""Panel 7 wilayah (WP-08) -- peta utama 7 wilayah; ikut paket juri bersama panel provinsi (D-104).

Juga panel alternatif untuk robustness Tier 2 (WP-30): varian non-representatif, agregasi observasi terakhir,
outcome Panel Harga Bapanas. Panel alternatif hanya dipakai `evaluation.robustness.tier2`, tidak ditulis sebagai artefak.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.data.loaders import norm_name
from kagami.data.qa import BAPANAS_TO_PIHPS
from kagami.data.weekly import aggregate_weekly, eligibility
from kagami.utils.config import Config
from kagami.utils.dates import week_start

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


# ------------------------------------------------------------------------------------ robustness Tier 2
def build_variant_panels(cfg: Config, pihps: pd.DataFrame) -> pd.DataFrame:
    """WP-30. Panel mingguan untuk setiap varian level-2 PIHPS NON-representatif dalam grup komoditas yang sama
    (mis. Minyak Goreng Curah, D-023; Beras Kualitas Super I). Aturan sama dengan panel utama: rerata hari
    teramati (weekly.aggregate_weekly) dan kelayakan per seri (weekly.eligibility).

    Input : keluaran loaders.load_pihps.
    Output: week, province_id, commodity, variant, log_price, status, eligible (eligible konstan per seri).
    Komoditas tanpa varian lain tidak muncul.
    """
    lv2 = pihps[pihps["level"] == 2]
    items = lv2["item"].map(norm_name)
    frames = []
    for cid, spec in cfg.commodities.items():
        grp = lv2["commodity_group"] == spec["pihps_name"]
        for v in sorted(set(items[grp]) - {norm_name(spec["variant"])}):
            d = lv2.loc[grp & (items == v), ["date", "province_id", "price"]].dropna(subset=["price"])
            d = d[d["price"] > 0].assign(commodity=cid, variant=v)
            d["province_id"] = d["province_id"].astype(int)
            w = aggregate_weekly(cfg, d)
            w = w[w["commodity"] == cid]
            el = eligibility(cfg, w)[["province_id", "commodity", "eligible"]]
            frames.append(w.merge(el, on=["province_id", "commodity"]).assign(variant=v))
    cols = ["week", "province_id", "commodity", "variant", "log_price", "status", "eligible"]
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)[cols]


def last_observation_panel(cfg: Config, daily: pd.DataFrame) -> pd.DataFrame:
    """WP-30. Agregasi mingguan alternatif: harga = hari TERAMATI terakhir minggu ISO (bukan rerata).

    Input : artefak 'pihps_daily' (date, province_id, commodity, price). Periode period.start..period.freeze.
    Output: week, province_id, commodity, price, log_price (hanya minggu teramati; build_design mengisi grid).
    """
    per = cfg.params["period"]
    d = daily[(daily["date"] >= pd.Timestamp(per["start"])) & (daily["date"] <= pd.Timestamp(per["freeze"]))]
    d = d[d["price"] > 0].sort_values("date").assign(week=lambda x: week_start(x["date"]))
    out = d.groupby(["province_id", "commodity", "week"], as_index=False)["price"].last()
    out["log_price"] = np.log(out["price"])
    return out[["week", "province_id", "commodity", "price", "log_price"]]


def build_bapanas_panel(cfg: Config, bapanas: pd.DataFrame) -> pd.DataFrame:
    """WP-30. Panel Harga Bapanas bulanan sebagai outcome alternatif (Tier 2 `bapanas_outcome`).

    Pemetaan komoditas qa.BAPANAS_TO_PIHPS (U20, D-110; Minyakita dikecualikan); provinsi pemekaran sudah
    dipetakan ke induk (loader) -> log harga = rerata log price_geomean per (bulan, province_id, commodity).
    Output: week (= awal bulan, label bulan untuk LP bulanan), province_id, commodity, log_price.
    """
    b = bapanas[bapanas["commodity_bapanas"].isin(BAPANAS_TO_PIHPS) & (bapanas["price_geomean"] > 0)]
    b = b.dropna(subset=["province_id"]).assign(
        commodity=lambda x: x["commodity_bapanas"].map(BAPANAS_TO_PIHPS),
        log_price=lambda x: np.log(x["price_geomean"]),
        week=lambda x: pd.to_datetime(x["month"]).dt.to_period("M").dt.to_timestamp())
    b["province_id"] = b["province_id"].astype(int)
    out = b.groupby(["week", "province_id", "commodity"], as_index=False)["log_price"].mean()
    return out[["week", "province_id", "commodity", "log_price"]]
