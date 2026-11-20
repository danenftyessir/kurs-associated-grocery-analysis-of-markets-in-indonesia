"""Analisis daya / MDE (WP-09) -- dihitung SEBELUM hasil Task 1 dilihat (gerbang G-power)."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.regression import ols_cluster  # noqa: F401  (dipakai implementasi WP-09)


def compute_mde(cfg: Config, panel: pd.DataFrame, region_panel: pd.DataFrame,
                drivers: pd.DataFrame) -> pd.DataFrame:
    """WP-09. -> artefak 'mde'.

    Untuk tiap komoditas, level nasional & 7 wilayah, horizon di params.lp.key_horizons:
    1) estimasi LP TANPA kurs (hanya lag harga, Brent, musiman) -> residual;
    2) SE(β) yang diharapkan = sd(resid) / (sd(de) * sqrt(n_minggu_efektif)) dengan cluster per minggu;
    3) MDE_β = (z_{1-α/2} + z_{power}) * SE; MDE_PT = MDE_β / γ(h) (γ dari LP de pada dirinya sendiri).
    Aturan gerbang (D-007): MDE_PT(8) > 0.5 untuk ketiga params.power.mde_commodities -> LP jadi sekunder.
    """
    todo("WP-09")
