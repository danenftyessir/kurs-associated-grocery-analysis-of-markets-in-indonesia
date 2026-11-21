"""Task 1 end-to-end pada artefak sintetis berskema kontrak (B/R kecil): semua artefak tahap tertulis dan valid."""

import numpy as np
import pandas as pd

from kagami.pipelines import task1
from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config
from kagami.utils.io import read_artifact, write_artifact
from synthetic import synthetic_task4_inputs


def _region_panel(cfg, panel):
    reg = cfg.regions.set_index("province_id")["region"]
    g = panel.assign(region=panel["province_id"].map(reg)).groupby(["week", "region", "commodity"])
    out = g.agg(log_price_index=("log_price", "mean"), n_provinces=("province_id", "nunique")).reset_index()
    first = out.groupby(["region", "commodity"])["log_price_index"].transform("first")
    return out.assign(log_price_index=out["log_price_index"] - first)


def test_task1_run_end_to_end(cfg, tmp_path, monkeypatch):
    c = Config(root=cfg.root, out_root=tmp_path)
    monkeypatch.setitem(c.params["inference"], "bootstrap_B", 3)
    monkeypatch.setitem(c.params["inference"], "placebo_R", 3)
    monkeypatch.setitem(c.params["inference"], "event_placebo_windows", 20)
    panel, drivers, world = synthetic_task4_inputs(cfg, n_weeks=300, n_provinces=34)
    drivers = drivers.assign(log_dxy=4.6, d_dxy=0.0)
    world = world.assign(log_w_usd=world["log_w_idr"] - np.log(15000.0))
    weeks = sorted(drivers["week"])
    eps = pd.DataFrame({"episode_id": [1, 2], "start_week": [weeks[100], weeks[200]],
                        "end_week": [weeks[108], weeks[208]], "cum_dlog_e": [0.05, 0.04],
                        "peak_week": [weeks[104], weeks[204]], "n_trigger_weeks": [3, 2], "in_period": [True, True]})
    elig = pd.DataFrame([{"province_id": p, "commodity": cm, "missing_share": 0.0, "max_gap_weeks": 0,
                          "min_year_coverage": 1.0, "eligible": True}
                         for p in range(1, 35) for cm in panel["commodity"].unique()])
    for name, df in {"drivers_weekly": drivers, "world_prices_weekly": world, "episodes": eps, "eligibility": elig,
                     "panel_weekly": panel, "panel_weekly_region": _region_panel(cfg, panel)}.items():
        write_artifact(c, name, df)
    task1.run(c)

    for name in ("profiles", "boot_replicates", "placebo_stats", "events", "response_features"):
        df = read_artifact(c, name)
        assert len(df) > 0 and set(ARTIFACTS[name].columns) <= set(df.columns), name
    prof, feats = read_artifact(c, "profiles"), read_artifact(c, "response_features")
    assert {"national", "region", "province"} <= set(prof["level"])
    assert prof["shrunk"].any() and (prof.loc[prof["level"] == "province", "se"] > 0).any()
    wide = prof[(prof["level"] == "national") & prof["se"].notna()]
    assert (wide["ci_high"] - wide["ci_low"] >= 2 * 1.96 * wide["se"] - 1e-9).all()      # interval tidak menyempit
    assert set(read_artifact(c, "boot_replicates")["rep"]) == {0, 1, 2}
    assert {"national", "province"} <= set(feats["level"])
