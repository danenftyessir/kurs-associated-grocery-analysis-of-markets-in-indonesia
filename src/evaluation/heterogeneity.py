"""Dekomposisi heterogenitas vs plasebo (WP-18) -- gerbang G-het. docs/METHODS.md §M2.1."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.meta import bh_fdr, dersimonian_laird  # noqa: F401  (WP-18)


def heterogeneity_stats(profiles: pd.DataFrame, horizon: int = 8) -> pd.DataFrame:
    """WP-18. Per komoditas dari δ(i,r,h) TANPA susut: Q, tau2, I2 (stats.meta.dersimonian_laird);
    lintas komoditas: rho_bar = rerata korelasi deviasi provinsi antar-komoditas.
    -> commodity ('ALL' untuk rho_bar), horizon, statistic, value.
    """
    todo("WP-18")


def placebo_pvalues(cfg: Config, observed: pd.DataFrame, placebo: pd.DataFrame) -> pd.DataFrame:
    """WP-18. p_placebo = (1 + #{plasebo >= aktual}) / (1 + R); q_fdr = BH antar 10 komoditas (H0-Het).
    -> artefak 'heterogeneity'.
    """
    todo("WP-18")
