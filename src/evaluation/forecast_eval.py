"""Metrik, uji Diebold-Mariano, ablation (WP-27). docs/METHODS.md §M4."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.regression import diebold_mariano  # noqa: F401  (WP-27)


def evaluate(cfg: Config, preds: pd.DataFrame) -> pd.DataFrame:
    """WP-27. MAE/RMSE per (horizon, model, subset ∈ {all, large_move}, commodity|ALL, region|ALL);
    rasio vs M1; DM HAC vs M1 (stats.regression.diebold_mariano, h dalam minggu / langkah origin);
    n_origins dan n_nonoverlap (origin berjarak >= h) SELALU dilaporkan. -> artefak 'forecast_eval'.
    H5 konfirmatori: grup fokus direct_import + imported_input, h=8, subset large_move.
    """
    todo("WP-27")


def ablation(cfg: Config, preds: pd.DataFrame) -> pd.DataFrame:
    """WP-27. delta_mae = MAE(M2 tanpa fx) - MAE(M2) per komoditas & kelompok wilayah. -> artefak 'ablation'."""
    todo("WP-27")
