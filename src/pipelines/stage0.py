"""Tahap 0 -- fondasi data (proposal §5.1). Notebook: notebooks/00_stage0_data.ipynb. Ringan; bisa lokal.

Input: data mentah di cfg.raw_dir. Urutan = urutan dependensi; tiap langkah menulis artefaknya sendiri.
Tabel buatan tim (WP-07) dijalankan terakhir karena tidak menjadi input langkah lain di Tahap 0.
"""

from __future__ import annotations

import pandas as pd

from kagami.data import drivers, loaders, panel, qa, reference, snapshot, weekly
from kagami.evaluation import power
from kagami.utils.config import Config
from kagami.utils.io import write_artifact

REQUIRES: tuple[str, ...] = ()   # hanya data mentah


def run(cfg: Config) -> None:
    snapshot.run(cfg)

    # --- outcome PIHPS ---------------------------------------------------------
    pihps = loaders.load_pihps(cfg)
    daily = weekly.select_variants(cfg, pihps)
    write_artifact(cfg, "pihps_daily", daily)
    wk = weekly.aggregate_weekly(cfg, daily)
    write_artifact(cfg, "panel_weekly", wk)
    elig = weekly.eligibility(cfg, wk)
    write_artifact(cfg, "eligibility", elig)

    # --- penggerak -------------------------------------------------------------
    jisdor = loaders.load_jisdor(cfg)
    drv = drivers.build_national_drivers(cfg, jisdor, loaders.load_fred(cfg, "brent"),
                                         loaders.load_fred(cfg, "dollar_index"))
    world = drivers.build_world_prices(cfg, loaders.load_pinksheet(cfg), jisdor)
    write_artifact(cfg, "world_prices_weekly", world)
    eps = drivers.find_episodes(cfg, drv)
    write_artifact(cfg, "episodes", eps)
    drv = drivers.mark_episode_weeks(drv, eps)
    write_artifact(cfg, "drivers_weekly", drv)
    write_artifact(cfg, "fx_variation", drivers.fx_variation_table(cfg, drv))

    # --- panel wilayah & daya --------------------------------------------------
    region = panel.build_region_panel(cfg, wk, elig)
    write_artifact(cfg, "panel_weekly_region", region)
    write_artifact(cfg, "mde", power.compute_mde(cfg, wk, region, drv, world, elig))

    # --- QA & laporan ----------------------------------------------------------
    sections = {
        "price_outliers": qa.flag_price_outliers(daily),
        "import_totals": qa.check_import_totals(loaders.load_bps_import_monthly(cfg),
                                                loaders.load_bps_import_annual(cfg)),
        "bapanas_bias": qa.check_bapanas_bias(wk, loaders.load_bapanas_panel(cfg)),
    }
    write_artifact(cfg, "stage0_report", qa.stage0_report(cfg, sections))

    # --- tabel buatan tim (WP-07, Ardell) -- paling akhir: tidak dipakai langkah lain di tahap ini, ----
    # sehingga artefak Danen (P1: panel wilayah) tetap terbit walau WP-07 belum selesai.
    write_artifact(cfg, "concordance", reference.build_concordance(cfg))
    write_artifact(cfg, "exposure", reference.build_exposure(
        cfg, loaders.load_faostat_sua(cfg), loaders.load_bps_import_monthly(cfg),
        loaders.load_comtrade(cfg), loaders.load_neraca_beras(cfg)))
    write_artifact(cfg, "regulation", reference.build_regulation(
        cfg, loaders.load_het_hap_current(cfg), loaders.load_regulation_history(cfg),
        loaders.load_bapanas_het_settings(cfg)))
    padi = pd.concat([loaders.load_padi(cfg, 2024), loaders.load_padi(cfg, 2025)], ignore_index=True)
    write_artifact(cfg, "province_features",
                   reference.build_province_features(cfg, padi, loaders.load_konsumsi_beras(cfg)))
