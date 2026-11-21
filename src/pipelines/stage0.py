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
    fxv = drivers.fx_variation_table(cfg, drv)
    write_artifact(cfg, "fx_variation", fxv)

    # --- panel wilayah & daya --------------------------------------------------
    region = panel.build_region_panel(cfg, wk, elig)
    write_artifact(cfg, "panel_weekly_region", region)
    mde = power.compute_mde(cfg, wk, region, drv, world, elig)
    write_artifact(cfg, "mde", mde)
    gate = power.gate_g_power(cfg, mde)

    # --- QA & laporan ----------------------------------------------------------
    imp_m, bapanas = loaders.load_bps_import_monthly(cfg), loaders.load_bapanas_panel(cfg)
    coverage = qa.coverage_table({
        "pihps (varian representatif)": (daily, "date"), "jisdor": (jisdor, "date"),
        "pinksheet": (loaders.load_pinksheet(cfg), "month"), "brent": (loaders.load_fred(cfg, "brent"), "date"),
        "dollar_index": (loaders.load_fred(cfg, "dollar_index"), "date"), "bps_import_monthly": (imp_m, "month"),
        "comtrade_import": (loaders.load_comtrade(cfg), "month"), "bapanas_panel": (bapanas, "month"),
    })
    sections = {
        "coverage": coverage, "eligibility": elig, "episodes": eps, "fx_variation": fxv, "mde": mde,
        "g_power": pd.DataFrame({"commodity": list(gate["mde_pt8"]), "mde_pt8": list(gate["mde_pt8"].values()),
                                 "threshold": gate["threshold"], "lp_secondary": gate["lp_secondary"]}),
        "h2_status": pd.DataFrame({"commodity": list(gate.get("mde_asym_pt8", {})),
                                   "mde_asym_pt8": list(gate.get("mde_asym_pt8", {}).values()),
                                   "h2_confirmatory": list(gate.get("h2_confirmatory", {}).values())}),
        "price_outliers": qa.flag_price_outliers(daily),
        "import_totals": qa.check_import_totals(imp_m, loaders.load_bps_import_annual(cfg)),
        "bapanas_bias": qa.check_bapanas_bias(wk, bapanas),
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
