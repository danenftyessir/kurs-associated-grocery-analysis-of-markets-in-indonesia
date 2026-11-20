"""Robustness Tier 1/2 + validasi V2-V4 (proposal §6.2-6.4). Notebook: notebooks/05_robustness.ipynb.

SEDANG-BERAT (mengulang LP untuk tiap cek) -> disarankan Kaggle/Colab. Tier 1 tidak boleh dipotong (D-014).
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import robustness
from kagami.utils.config import Config
from kagami.utils.io import require, write_artifact

REQUIRES = ("profiles", "events", "drivers_weekly", "world_prices_weekly", "forecast_eval")


def run(cfg: Config, include_tier2: bool = False) -> None:
    require(cfg, *REQUIRES)
    parts = [robustness.tier1(cfg), robustness.validation(cfg)]
    if include_tier2:
        parts.append(robustness.tier2(cfg))
    write_artifact(cfg, "robustness", pd.concat(parts, ignore_index=True))
