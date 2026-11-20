"""Penyusutan EB deviasi provinsi + ekstraksi fitur respons (WP-17). docs/METHODS.md §M1e-f."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.meta import dersimonian_laird, eb_shrink, reml_tau2  # noqa: F401  (WP-17)


def shrink_deviations(cfg: Config, profiles: pd.DataFrame) -> pd.DataFrame:
    """WP-17. Per (komoditas, driver, horizon): τ² DL (stats.meta.dersimonian_laird; REML sebagai cek),
    estimasi tersusut = stats.meta.eb_shrink. Tambah baris level='province', shrunk=True.
    """
    todo("WP-17")


def response_features(cfg: Config, profiles: pd.DataFrame) -> pd.DataFrame:
    """WP-17. -> artefak 'response_features'.

    R4,R8,R12 = respons kurs kumulatif; W4,W8,W12 = respons harga dunia rupiah; PT8 = β(8)/γ(8);
    t_half = horizon pertama respons >= 50% maksimum (NaN bila interval memuat nol di semua h);
    A8 = β+(8) - β-(8) (level komoditas saja).
    """
    todo("WP-17")
