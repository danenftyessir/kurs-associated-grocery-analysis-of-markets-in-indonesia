"""Model M0-M3 (WP-26). docs/METHODS.md §M4."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.features.forecast import FEATURE_GROUPS, build_features, origins  # noqa: F401  (WP-26)

MODELS = ("M0", "M1", "M2", "M3")


def fit_predict(cfg: Config, model: str, train: pd.DataFrame, test: pd.DataFrame,
                drop_groups: tuple[str, ...] = ()) -> pd.Series:
    """WP-26. Prediksi target untuk baris test.

    M0: nol (naive tanpa perubahan). M1: Ridge (alpha dipilih CV berbasis waktu di train) dengan FEATURE_GROUPS
    'base'. M2: M1 + 'fx'. M3: HistGradientBoostingRegressor (params.forecast.hgb, random_state=cfg.seed) dengan
    M2 + 'id' (kategori). drop_groups dipakai ablation (hapus 'fx').
    """
    todo("WP-26")


def rolling_predictions(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                        world: pd.DataFrame) -> pd.DataFrame:
    """WP-26. Loop horizon x origin (features.forecast.origins) x model (+ M2 tanpa fx untuk ablation);
    data per origin dari features.forecast.build_features.

    -> origin, horizon, model, province_id|region, commodity, y_true, y_pred, large_move (|Δe 4 mgg| > p80 train).
    Disimpan di data/interim/forecast_preds.parquet (bukan artefak kirim; dipakai evaluation).
    """
    todo("WP-26")
