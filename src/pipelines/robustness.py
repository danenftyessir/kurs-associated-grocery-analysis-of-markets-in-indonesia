"""Robustness Tier 1/2 + validasi V2-V4 (proposal §6.2-6.4). Notebook: notebooks/05_robustness.ipynb.

SEDANG-BERAT (mengulang LP untuk tiap cek) -> disarankan Kaggle/Colab. Tier 1 tidak boleh dipotong (D-014).
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import robustness
from kagami.utils.config import Config
from kagami.utils.io import read_artifact, require, write_artifact

REQUIRES = ("profiles", "events", "episodes", "panel_weekly", "eligibility", "drivers_weekly",
            "world_prices_weekly", "forecast_eval")


def run(cfg: Config, include_tier2: bool = False) -> None:
    require(cfg, *REQUIRES)
    panel, elig, drv, world = (read_artifact(cfg, n) for n in
                               ("panel_weekly", "eligibility", "drivers_weekly", "world_prices_weekly"))
    profiles, events, eps, fe = (read_artifact(cfg, n) for n in ("profiles", "events", "episodes", "forecast_eval"))
    parts = [robustness.tier1(cfg, panel, drv, world, elig=elig),
             robustness.validation(cfg, profiles, events, eps, drv, world, fe)]
    if include_tier2:
        parts.append(robustness.tier2(cfg))
    write_artifact(cfg, "robustness", pd.concat(parts, ignore_index=True))
