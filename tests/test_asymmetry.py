"""H2 (D-125): uji Wald β⁺ = β⁻ nasional + pembanding bootstrap & plasebo."""

import numpy as np
import pandas as pd

from kagami.evaluation.asymmetry import COLUMNS, asymmetry_tests
from kagami.models.local_projection import asymmetry_wald, build_design, fit_lp
from tests.test_local_projection import _drivers, _panel


def test_wald_matches_asymmetric_lp_and_recovers_difference(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.6, 0.1)
    out = asymmetry_wald(cfg, panel, drv, None, horizons=[0, 4]).set_index("horizon")
    for h in (0, 4):
        r = fit_lp(cfg, build_design(cfg, panel, drv, None, "gula_pasir", h, 4, asymmetric=True)).set_index("driver")
        assert np.isclose(out.loc[h, "beta_pos"], r.loc["e_pos", "estimate"])        # parametrisasi ulang = model sama
        assert np.isclose(out.loc[h, "beta_neg"], r.loc["e_neg", "estimate"])
        assert np.isclose(out.loc[h, "estimate"], out.loc[h, "beta_pos"] - out.loc[h, "beta_neg"])
        assert out.loc[h, "n_obs"] == r.loc["e_pos", "n_obs"]
    assert abs(out.loc[0, "estimate"] - 0.5) < 2.5 * out.loc[0, "se"]
    assert out.loc[0, "estimate"] / out.loc[0, "se"] > 3                              # asimetri nyata terdeteksi


def test_wald_symmetric_data_not_rejected_too_often(cfg):
    drv = _drivers(cfg, seed=11)
    z = []
    for s in range(6):
        out = asymmetry_wald(cfg, _panel(cfg, drv, 0.4, 0.4, seed=100 + s), drv, None, horizons=[0])
        z.append(out["estimate"].iloc[0] / out["se"].iloc[0])
    assert np.mean(np.abs(z) > 1.96) <= 0.34                                          # β⁺ = β⁻ -> jarang ditolak


def test_asymmetry_tests_flags_bootstrap_and_placebo(cfg):
    wald = pd.DataFrame({"commodity": ["beras", "beras", "gula_pasir"], "horizon": [4, 8, 8],
                         "beta_pos": [0.3, 0.5, 0.2], "beta_neg": [0.1, 0.1, 0.1], "estimate": [0.2, 0.4, 0.1],
                         "se": [0.1, 0.1, 0.1], "n_weeks": 450, "n_obs": 15000})
    mde = pd.DataFrame({"commodity": ["beras", "gula_pasir", "bawang_putih", "minyak_goreng"], "level": "national",
                        "horizon": 8, "mde_pt": [0.3, 0.9, 2.0, 0.4], "mde_asym_pt": [0.44, 1.7, 6.0, 0.6],
                        "mde_asym_beta": [0.58, 2.2, 8.1, 0.8]})
    reps = []
    for r in range(99):                       # selisih replikasi: beras h8 = 0.4 + (r - 49)/100, lainnya 0
        for c, h in (("beras", 4), ("beras", 8), ("gula_pasir", 8)):
            d = (r - 49) / 100 + (0.4 if (c, h) == ("beras", 8) else 0.0)
            reps += [{"rep": r, "level": "national", "unit": "ALL", "commodity": c, "horizon": h,
                      "driver": "e_pos", "estimate": d}, {"rep": r, "level": "national", "unit": "ALL",
                      "commodity": c, "horizon": h, "driver": "e_neg", "estimate": 0.0}]
    boot = pd.DataFrame(reps)
    placebo = boot.copy()
    placebo.loc[placebo["driver"] == "e_pos", "estimate"] = ((placebo.loc[placebo["driver"] == "e_pos", "rep"] - 49)
                                                             / 100)
    out = asymmetry_tests(cfg, wald, boot, placebo, mde).set_index(["commodity", "horizon"])
    assert list(out.reset_index().columns) == COLUMNS
    assert out.loc[("beras", 8), "confirmatory"] and out.loc[("beras", 8), "reject"]          # p ≈ 6e-5, konfirmatori
    assert not out.loc[("beras", 4), "confirmatory"] and not out.loc[("beras", 4), "reject"]  # h ≠ 8 -> deskriptif
    assert not out.loc[("gula_pasir", 8), "confirmatory"]                                    # MDE asimetri > 0,5
    assert np.isclose(out.loc[("beras", 8), "p_value"], 2 * (1 - 0.9999683), atol=1e-6)
    assert np.isclose(out.loc[("beras", 8), "mde_asym_beta"], 0.58) and np.isnan(out.loc[("beras", 4), "mde_asym_beta"])
    lo, hi = out.loc[("beras", 8), ["boot_ci_low", "boot_ci_high"]]
    assert 0.4 - 0.49 <= lo < 0.4 < hi <= 0.4 + 0.49 and out.loc[("beras", 8), "n_boot"] == 99
    # plasebo |d*| = |r - 49|/100 ≥ 0.4 pada r ≤ 9 atau r ≥ 89 -> 20 dari 99
    assert np.isclose(out.loc[("beras", 8), "p_placebo"], (1 + 20) / 100)
    assert out.loc[("beras", 8), "n_placebo"] == 99
    # interval laporan = yang lebih lebar dari Wald (0,204..0,596) dan bootstrap -> memuat nol walau Wald menolak (D-127)
    b8 = out.loc[("beras", 8)]
    assert np.isclose(b8["wald_ci_low"], 0.4 - 0.196) and np.isclose(b8["wald_ci_high"], 0.4 + 0.196)
    assert np.isclose(b8["ci_low"], lo) and np.isclose(b8["ci_high"], hi) and lo < 0
    assert not b8["ci_excludes_zero"]
    assert (out["ci_low"] <= out["wald_ci_low"]).all() and (out["ci_high"] >= out["wald_ci_high"]).all()


def test_asymmetry_tests_without_replicates(cfg):
    wald = pd.DataFrame({"commodity": ["beras"], "horizon": [8], "beta_pos": [0.1], "beta_neg": [0.0],
                         "estimate": [0.1], "se": [0.1], "n_weeks": 450, "n_obs": 15000})
    out = asymmetry_tests(cfg, wald)
    assert not out["confirmatory"].iloc[0] and out["n_boot"].iloc[0] == 0 and np.isnan(out["p_placebo"].iloc[0])
    assert np.isclose(out["ci_low"].iloc[0], 0.1 - 0.196) and np.isclose(out["ci_low"].iloc[0], out["wald_ci_low"].iloc[0])
