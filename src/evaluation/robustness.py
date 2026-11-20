"""Robustness Tier 1/2 dan validasi V2-V4 (WP-28, WP-29, WP-30). docs/METHODS.md §M5.

Tier 1 TIDAK BOLEH dipotong (D-014). Semua keluaran -> artefak 'robustness'.
"""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config

TIER1 = (
    "horizon_8_vs_12",
    "lags_2_4_8",
    "subperiod_pre_post_2021-04-05",      # juga V3
    "exclude_covid_and_extreme_brent",
    "fx_decomposition_global_dollar_vs_idr_specific",
    "monthly_frequency",
)
TIER2 = (
    "alternative_variants",               # termasuk Minyak Goreng Curah (D-023)
    "last_observation_aggregation",
    "alternative_exposure_remoteness",
    "bapanas_outcome",
)


def tier1(cfg: Config) -> pd.DataFrame:
    """WP-28. Jalankan ulang LP nasional (models.local_projection) untuk setiap cek di TIER1; baseline_estimate = spesifikasi utama.

    fx_decomposition: regresikan de pada d_dxy -> komponen dolar global (fitted) & spesifik rupiah (resid).
    """
    todo("WP-28")


def validation(cfg: Config) -> pd.DataFrame:
    """WP-29. V2 studi kasus 2026 (origin dengan outcome lengkap saja, deskriptif),
    V4 LP vs event study (arah & besaran; ketidaksesuaian dilaporkan). V1 = Task 4, V3 = Tier 1 subperiod.
    """
    todo("WP-29")


def tier2(cfg: Config) -> pd.DataFrame:
    """WP-30. Opsional; yang pertama dipotong bila waktu habis."""
    todo("WP-30")

