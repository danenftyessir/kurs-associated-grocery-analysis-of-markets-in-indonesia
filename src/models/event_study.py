"""Event study per episode depresiasi (WP-14). docs/METHODS.md §M1b."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.resampling import placebo_windows  # noqa: F401  (WP-14)


def event_paths(cfg: Config, panel: pd.DataFrame, episodes: pd.DataFrame, level: str) -> pd.DataFrame:
    """WP-14. Perubahan log harga 0..12 minggu setelah start_week tiap episode (level national|region).

    National = rerata lintas provinsi eligible. -> episode_id, level, unit, commodity, horizon, dlog_price.
    """
    todo("WP-14")


def placebo_bands(cfg: Config, panel: pd.DataFrame, episodes: pd.DataFrame, level: str) -> pd.DataFrame:
    """WP-14. 499 jendela plasebo dari minggu tanpa episode (stats.resampling.placebo_windows).

    -> placebo_lo/hi (persentil 2.5/97.5) dan placebo_p (proporsi |plasebo| >= |aktual|) per horizon.
    Gabung dengan event_paths -> artefak 'events'.
    """
    todo("WP-14")
