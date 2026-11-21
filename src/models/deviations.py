"""Deviasi provinsi & wilayah dari respons nasional (WP-15). docs/METHODS.md §M1c."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.models import local_projection as lp
from kagami.utils.config import Config

KEEP = ["week", "province_id", "commodity", "dev"]
DEVIATION_DRIVERS = ("e", "w")      # deviasi dihitung untuk kurs & harga dunia (spesifikasi simetris)


def demean_cross_section(panel: pd.DataFrame, elig: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-15. log_price provinsi - rerata lintas provinsi pada (minggu, komoditas) yang sama.

    Rerata hanya atas provinsi teramati pada minggu itu (NaN dilewati); `elig` membatasi ke seri eligible.
    -> week, province_id, commodity, dev.
    """
    p = panel[["week", "province_id", "commodity", "log_price"]]
    if elig is not None:
        ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
        p = p.merge(ok, on=["province_id", "commodity"], how="inner")
    mean = p.groupby(["week", "commodity"])["log_price"].transform("mean")
    return p.assign(dev=p["log_price"] - mean)[KEEP]


def _single_unit(parts: dict, j: int) -> dict:
    """Bagian desain LP (lp._design_parts) untuk satu unit; cache regresor gabungan dibuang agar dibangun ulang."""
    one = {k: v for k, v in parts.items() if k not in ("X", "in_p", "x_ok")}
    one.update(units=parts["units"][[j]], P=parts["P"][:, [j]], dP=parts["dP"][:, [j]])
    return one


def province_deviations(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                        world: pd.DataFrame, *, elig: pd.DataFrame | None = None,
                        horizons: list[int] | None = None, commodities: list[str] | None = None) -> pd.DataFrame:
    """WP-15. δ(i,r,h) per provinsi (spesifikasi sama dengan LP nasional, pada harga ter-demean).

    Normalisasi: Σ_r δ(i,r,h) = 0 per (komoditas, horizon). -> baris 'profiles' level='province', shrunk=False.
    Tiap provinsi diestimasi sendiri (satu unit, efek tetap = rata-rata sendiri, SE cluster minggu) dengan
    `lp._design_parts/_design_arrays/_fit_arrays` agar desain identik dengan LP nasional (METHODS §M1.4).
    driver ∈ {e, w} (w hanya komoditas dengan padanan harga dunia); unit = province_id sebagai string.
    elig: hanya seri eligible; horizons default params.lp.horizons (plasebo: key_horizons); kolom ekstra n_obs.
    """
    L = int(cfg.params["lp"]["lags"])
    H = [int(h) for h in (horizons if horizons is not None else cfg.params["lp"]["horizons"])]
    dev = demean_cross_section(panel, elig)
    present = set(dev["commodity"].unique())
    rows = []
    for com in [c for c in (commodities or cfg.commodity_ids()) if c in present]:
        parts = lp._design_parts(cfg, dev, drivers, world, com, L, False, None, "province_id", "dev")
        for j, prov in enumerate(parts["units"]):
            one = _single_unit(parts, j)
            for h in H:
                y, X, names, wk, _, _ = lp._design_arrays(one, h)
                for drv, est, se, n_weeks, n_obs in lp._fit_arrays(y, X, names, wk):
                    if drv in DEVIATION_DRIVERS:
                        rows.append((com, str(int(prov)), drv, h, est, se, n_weeks, n_obs))
    out = pd.DataFrame(rows, columns=["commodity", "unit", "driver", "horizon", "estimate", "se", "n_weeks", "n_obs"])
    out["estimate"] -= out.groupby(["commodity", "driver", "horizon"])["estimate"].transform("mean")   # Σ_r δ = 0
    out["ci_low"] = out["estimate"] - 1.96 * out["se"]
    out["ci_high"] = out["estimate"] + 1.96 * out["se"]
    out["level"], out["shrunk"] = "province", False
    return out[lp.PROFILE_COLUMNS + ["n_obs"]].reset_index(drop=True)


def region_profiles(cfg: Config, region_panel: pd.DataFrame, drivers: pd.DataFrame,
                    world: pd.DataFrame, *, horizons: list[int] | None = None,
                    commodities: list[str] | None = None) -> pd.DataFrame:
    """WP-15. Profil untuk 7 wilayah dari panel_weekly_region (peta utama 7 wilayah).

    Tiap wilayah diestimasi sendiri dengan spesifikasi LP nasional (`lp.national_profiles` pada deret wilayah itu:
    driver e, w, e_pos, e_neg, PT) -> baris 'profiles' level='region', unit = nama wilayah. Tidak ada filter
    kelayakan (panel wilayah sudah hanya memuat seri eligible, WP-08); wilayah dengan seri kosong dilewati.
    """
    parts = []
    for region, g in region_panel.groupby("region"):
        if g["log_price_index"].notna().sum() == 0:
            continue
        prof = lp.national_profiles(cfg, g, drivers, world, horizons=horizons, commodities=commodities)
        parts.append(prof.assign(level="region", unit=str(region)))
    cols = lp.PROFILE_COLUMNS + ["n_obs"]
    return pd.concat(parts, ignore_index=True)[cols] if parts else pd.DataFrame(columns=cols)
