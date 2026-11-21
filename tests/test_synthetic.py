"""Generator sintetis Task 1 (tests/synthetic.py): skema = kontrak artefak, jawaban tertanam dapat dipulihkan."""

import numpy as np

from kagami.stats.regression import ols_cluster
from kagami.utils.artifacts import ARTIFACTS
from synthetic import synthetic_national_profiles, synthetic_task1_panel


def test_panel_schema_and_label(cfg):
    panel, drivers, truth = synthetic_task1_panel(cfg, n_weeks=30)
    assert set(ARTIFACTS["panel_weekly"].columns) <= set(panel.columns)
    assert panel.attrs["dummy"] and drivers.attrs["dummy"]
    assert panel["province_id"].nunique() == 34 and panel["commodity"].nunique() == 3
    assert abs(sum(truth["delta"].values())) < 1e-12                           # Σ_r δ = 0


def test_panel_recovers_planted_response(cfg):
    panel, drivers, truth = synthetic_task1_panel(cfg, n_weeks=600, noise=0.001)
    h = 8
    c, r = "beras" if "beras" in truth["beta"] else next(iter(truth["beta"])), 5
    s = panel[(panel["commodity"] == c) & (panel["province_id"] == r)].reset_index(drop=True)
    y = s["log_price"].shift(-h) - s["log_price"].shift(1)                    # y^(h) = p_{t+h} - p_{t-1}
    fit = ols_cluster(y.to_numpy(), np.column_stack([np.ones(len(s)), drivers["de"].to_numpy()]), np.arange(len(s)))
    target = truth["beta"][c] + truth["delta"][r]
    assert abs(fit.beta[1] - target) < 2 * fit.se[1] + 0.02


def test_national_profiles_schema(cfg):
    p = synthetic_national_profiles(cfg)
    assert set(ARTIFACTS["profiles"].columns) <= set(p.columns)
    assert p.attrs["dummy"] and set(p["horizon"]) == set(range(13)) and set(p["driver"]) >= {"e", "w", "PT"}
    assert (p["ci_low"] <= p["estimate"]).all() and (p["estimate"] <= p["ci_high"]).all()
    assert p.groupby(["commodity", "driver"]).size().eq(13).all()
