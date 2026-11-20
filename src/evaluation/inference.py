"""Ketidakpastian bersama (bootstrap blok) dan null plasebo geser-melingkar (WP-16). docs/METHODS.md §M1d."""

from __future__ import annotations

from typing import Callable

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.resampling import circular_shift, moving_block_indices  # noqa: F401  (WP-16)


def joint_bootstrap(cfg: Config, estimator: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
                    panel: pd.DataFrame, drivers: pd.DataFrame, B: int) -> pd.DataFrame:
    """WP-16. B replikasi moving-block (blok 13 minggu) dengan SATU indeks minggu per replikasi
    (stats.resampling.moving_block_indices) yang dipakai untuk semua seri & horizon.

    estimator(panel_b, drivers_b) -> baris profil. -> artefak 'boot_replicates' (rep, level, unit, ...).
    Komputasi: komoditas fokus B=499, lainnya boleh B=199 (params.inference.bootstrap_B_nonfocus).
    """
    todo("WP-16")


def circular_placebo(cfg: Config, statistic: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
                     panel: pd.DataFrame, drivers: pd.DataFrame, R: int) -> pd.DataFrame:
    """WP-16. Geser de & dw sejauh s >= 52 minggu (np.roll) terhadap harga, hitung ulang profil.

    statistic(panel, drivers_shifted) -> baris profil (nasional + deviasi provinsi; provinsi cukup
    h ∈ params.lp.key_horizons agar ukuran file wajar). -> artefak 'placebo_stats'
    (rep, level, unit, commodity, driver, horizon, estimate). Q/τ²/silhouette plasebo dihitung di Task 2.
    """
    todo("WP-16")


def bootstrap_ci(profiles: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """WP-16. Ganti ci_low/ci_high dengan persentil bootstrap bila lebih lebar dari ±1.96·se."""
    todo("WP-16")
