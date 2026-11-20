"""WP-09: MDE dari residual LP tanpa kurs (β̂ tidak dihitung)."""

import numpy as np
import pandas as pd
import pytest

from kagami.evaluation.power import compute_mde, gate_g_power, null_se
from kagami.models.local_projection import build_design, fit_lp, regressors
from kagami.stats.regression import ols_cluster

from test_local_projection import _drivers, _panel


def test_null_se_matches_cluster_se_under_null(cfg):
    drv = _drivers(cfg, seed=11)
    panel = _panel(cfg, drv, 0.0, 0.0, n_units=15, seed=12)           # β = 0
    D = build_design(cfg, panel, drv, None, "gula_pasir", 8, 4)
    se0, n = null_se(D)
    full = fit_lp(cfg, D).set_index("driver").loc["e", "se"]
    assert n == len(D)
    assert abs(se0 / full - 1) < 0.05                                 # SE skor ≈ SE regresi penuh bila β = 0
    # cocok dengan regresi residual-pada-x̃ (METHODS §M0.6 langkah 2)
    reg = regressors(D)
    ctrl = [c for c in reg if not c.startswith(("de", "dw"))]
    u = D["y"] - D[ctrl].to_numpy() @ np.linalg.lstsq(D[ctrl].to_numpy(), D["y"].to_numpy(), rcond=None)[0]
    O = D[[c for c in reg if c != "de"]].to_numpy()
    xt = D["de"] - O @ np.linalg.lstsq(O, D["de"].to_numpy(), rcond=None)[0]
    r = ols_cluster(u.to_numpy(), xt.to_numpy()[:, None], D["group"].to_numpy())
    assert abs(se0 / r.se[0] - 1) < 0.05


def test_null_se_scales_with_noise(cfg):
    drv = _drivers(cfg, seed=3)
    lo = null_se(build_design(cfg, _panel(cfg, drv, 0, 0, noise=0.01), drv, None, "gula_pasir", 4, 4))[0]
    hi = null_se(build_design(cfg, _panel(cfg, drv, 0, 0, noise=0.04), drv, None, "gula_pasir", 4, 4))[0]
    assert 3 < hi / lo < 5


def test_gate_g_power(cfg):
    def mde(vals):
        return pd.DataFrame({"commodity": list(vals), "level": "national", "horizon": 8, "mde_pt": list(vals.values())})
    assert gate_g_power(cfg, mde({"bawang_putih": 2.0, "gula_pasir": 0.9, "minyak_goreng": 0.6}))["lp_secondary"]
    assert not gate_g_power(cfg, mde({"bawang_putih": 2.0, "gula_pasir": 0.9, "minyak_goreng": 0.4}))["lp_secondary"]


def test_compute_mde_real(cfg):
    from kagami.utils.io import exists, read_artifact
    names = ("panel_weekly", "eligibility", "panel_weekly_region", "drivers_weekly", "world_prices_weekly")
    if not all(exists(cfg, n) for n in names):
        pytest.skip("artefak Tahap 0 belum ada")
    wk, el, rg, drv, wp = (read_artifact(cfg, n) for n in names)
    m = compute_mde(cfg, wk, rg, drv, wp, el)
    H = cfg.params["lp"]["key_horizons"]
    assert len(m) == 10 * len(H) * 8                                   # nasional + 7 wilayah
    assert m[["mde_beta", "mde_pt", "gamma"]].notna().all().all() and (m["mde_beta"] > 0).all()
    z = m["mde_beta"] / m["se_beta"]
    assert np.allclose(z, 2.8016, atol=1e-3)                           # z_{0,975} + z_{0,80}
    assert (m.loc[m.level == "national", "n_weeks"] > 400).all()
    nat = m[m.level == "national"].set_index(["commodity", "horizon"])["mde_beta"]
    reg = m[m.level == "region"].groupby(["commodity", "horizon"])["mde_beta"].median()
    assert (nat < reg.reindex(nat.index)).mean() > 0.8                                    # pooled nasional lebih presisi
