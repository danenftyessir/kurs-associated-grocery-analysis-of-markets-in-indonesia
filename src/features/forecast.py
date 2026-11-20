"""Fitur prediktif dengan as-of join (WP-25). docs/METHODS.md §M4, aturan kebocoran §6.5 proposal."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config

FEATURE_GROUPS = {
    "base": ["lag_dp_1", "lag_dp_4", "lag_dp_8", "month", "idf_rel_week", "db_1", "db_4"],   # M1
    "fx": ["de_1", "de_4", "de_8", "dw_1", "dw_4", "dw_8", "episode"],                       # M2 = base + fx
    "id": ["commodity", "region"],                                                             # M3 = M2 + id
}


def origins(cfg: Config, weeks: pd.Series, horizon: int) -> list[pd.Timestamp]:
    """WP-25. Origin tiap 4 minggu dari forecast.first_origin s.d. (freeze - horizon minggu)."""
    todo("WP-25")


def build_features(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                   origin: pd.Timestamp, horizon: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WP-25. -> (train, test) untuk satu origin.

    Target = log_price_{t+h} - log_price_t per seri. Train hanya baris dengan t+h <= origin (outcome sudah
    terealisasi). Join harga dunia memakai available_at <= minggu fitur (as-of); data harian (JISDOR, Brent)
    tersedia hari yang sama. TIDAK ADA pembagian acak per baris.
    """
    todo("WP-25")
