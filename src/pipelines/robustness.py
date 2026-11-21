"""Robustness Tier 1/2 + validasi V2-V4 (proposal §6.2-6.4). Notebook: notebooks/05_robustness.ipynb.

SEDANG-BERAT (mengulang LP untuk tiap cek) -> disarankan Kaggle/Colab. Tier 1 tidak boleh dipotong (D-014).
"""

from __future__ import annotations

import pandas as pd

from kagami.data import drivers as drivers_mod
from kagami.data import loaders
from kagami.data import panel as panel_mod
from kagami.evaluation import robustness
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

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
        parts.append(robustness.tier2(cfg, panel, drv, world, elig=elig, profiles=profiles, **tier2_inputs(cfg)))
    write_artifact(cfg, "robustness", pd.concat(parts, ignore_index=True))


def tier2_inputs(cfg: Config) -> dict:
    """Input opsional Tier 2 (WP-30); yang sumbernya tidak ada dilewati dengan pesan.

    Butuh data mentah (pihps, pinksheet, jisdor, bapanas_panel) -> jalan di lokal/Kaggle/Colab dengan raw_dir,
    tidak dari paket juri (Tingkat B). Artefak `pihps_daily` & `exposure` dibaca bila ada.
    """
    out: dict = {}
    steps = {
        "variant_panels": lambda: panel_mod.build_variant_panels(cfg, loaders.load_pihps(cfg)),
        "world_variants": lambda: drivers_mod.build_world_variants(cfg, loaders.load_pinksheet(cfg),
                                                                   loaders.load_jisdor(cfg)),
        "bapanas": lambda: panel_mod.build_bapanas_panel(cfg, loaders.load_bapanas_panel(cfg)),
    }
    for key, fn in steps.items():
        try:
            out[key] = fn()
        except (FileNotFoundError, OSError) as exc:
            print(f"[robustness] Tier 2 {key} dilewati: {exc}")
    if exists(cfg, "pihps_daily"):
        out["last_obs_panel"] = panel_mod.last_observation_panel(cfg, read_artifact(cfg, "pihps_daily"))
    else:
        print("[robustness] Tier 2 last_obs dilewati: artefak pihps_daily tidak ada")
    if exists(cfg, "exposure"):
        out["exposure"] = read_artifact(cfg, "exposure")
    return out
