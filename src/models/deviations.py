"""Deviasi provinsi & wilayah dari respons nasional (WP-15). docs/METHODS.md §M1c."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config


def demean_cross_section(panel: pd.DataFrame) -> pd.DataFrame:
    """WP-15. log_price provinsi - rerata lintas provinsi pada (minggu, komoditas) yang sama."""
    todo("WP-15")


def province_deviations(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                        world: pd.DataFrame) -> pd.DataFrame:
    """WP-15. δ(i,r,h) per provinsi (spesifikasi sama dengan LP nasional, pada harga ter-demean).

    Normalisasi: Σ_r δ(i,r,h) = 0 per (komoditas, horizon). -> baris 'profiles' level='province', shrunk=False.
    """
    todo("WP-15")


def region_profiles(cfg: Config, region_panel: pd.DataFrame, drivers: pd.DataFrame,
                    world: pd.DataFrame) -> pd.DataFrame:
    """WP-15. Profil untuk 7 wilayah dari panel_weekly_region (peta utama 7 wilayah)."""
    todo("WP-15")
