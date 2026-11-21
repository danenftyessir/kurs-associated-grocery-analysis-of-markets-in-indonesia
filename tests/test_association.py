"""WP-23/24: meta-regresi efek acak provinsi dan interaksi efek tetap, dengan koefisien tertanam."""

import numpy as np
import pandas as pd

from kagami.data.drivers import driver_weeks
from kagami.models.association import (ASSOC_COLUMNS, META_EXTRA, _fit_meta, _two_way_demean, fe_interaction,
                                       meta_regression)

COMS = ["gula_pasir", "beras", "daging_ayam"]


def _features(rng, with_rice=False, with_nk=False):
    ids = np.arange(1, 35)
    f = pd.DataFrame({"province_id": ids, "dist_hub_km": rng.uniform(0, 3000, 34)})
    f["ln_dist_hub"] = np.log1p(f["dist_hub_km"])
    f["rice_sufficiency"] = rng.uniform(0.3, 2.0, 34) if with_rice else np.nan
    f["n_kota"] = rng.integers(1, 8, 34).astype(float) if with_nk else np.nan
    return f


def _profiles(f, slope, se=0.05, rng=None, coms=COMS, h=4, intercepts=None):
    """δ_r = intercept + slope · z(ln_dist_hub) + derau(se); baris profiles provinsi driver e."""
    z = (f["ln_dist_hub"] - f["ln_dist_hub"].mean()) / f["ln_dist_hub"].std(ddof=0)
    rows = []
    for k, com in enumerate(coms):
        d = (0 if intercepts is None else intercepts[k]) + slope * z.to_numpy() + rng.normal(0, se, 34)
        for u in range(34):
            rows.append({"level": "province", "unit": str(u + 1), "commodity": com, "driver": "e", "horizon": h,
                         "estimate": float(d[u]), "se": se, "ci_low": d[u] - 1.96 * se, "ci_high": d[u] + 1.96 * se,
                         "n_weeks": 400, "shrunk": False})
    return pd.DataFrame(rows)


def test_fit_meta_recovers_coefficients_and_cr2_is_sane():
    rng = np.random.default_rng(0)
    n = 34
    Z = rng.normal(0, 1, n)
    X = np.column_stack([np.ones(n), Z])
    s2 = np.full(n, 0.05 ** 2)
    y = 0.2 - 0.3 * Z + rng.normal(0, 0.05, n)
    fit = _fit_meta(y, X, s2, np.arange(n))
    assert np.allclose(fit["beta"], [0.2, -0.3], atol=0.05) and fit["tau2"] < 0.002
    assert 0.6 < fit["se_cr2"][1] / fit["se_model"][1] < 1.6 and fit["df"] == n - 2     # CR2 ≈ SE model (homoskedastis)
    y2 = y + rng.normal(0, 0.3, n)                                                     # heterogenitas sisa -> τ² > 0
    assert _fit_meta(y2, X, s2, np.arange(n))["tau2"] > 0.02


def test_meta_regression_recovers_slope_and_h3(cfg):
    rng = np.random.default_rng(1)
    f = _features(rng)
    prof = _profiles(f, -0.10, rng=rng, h=4)
    out = meta_regression(cfg, prof, None, f)
    assert list(out.columns) == ASSOC_COLUMNS + META_EXTRA and set(out["feature"]) == {"ln_dist_hub"}
    assert {"ALL", *COMS} == set(out["commodity"]) and set(out["level"]) == {"province"}
    r = out[(out["commodity"] == "ALL") & (out["horizon"] == 4)].iloc[0]
    assert abs(r["estimate"] + 0.10) < 0.03 and r["ci_low"] < -0.10 < r["ci_high"]
    assert r["method"] == "meta_regression_re_one_sided" and r["p_value"] < 0.001        # H3: koefisien < 0
    assert r["jackknife_min"] <= r["estimate"] <= r["jackknife_max"] and r["ci_method"] == "cr2"
    assert (out["horizon"] == 4).all()                                                   # hanya h pada data


def test_meta_regression_h3_is_one_sided_and_other_horizon_two_sided(cfg):
    rng = np.random.default_rng(2)
    f = _features(rng)
    prof = pd.concat([_profiles(f, +0.10, rng=rng, h=4), _profiles(f, +0.10, rng=rng, h=12)])
    out = meta_regression(cfg, prof, None, f).query("commodity == 'ALL'").set_index("horizon")
    assert out.loc[4, "p_value"] > 0.99                                                  # arah salah pada uji satu sisi
    assert out.loc[12, "p_value"] < 0.001 and out.loc[12, "method"] == "meta_regression_re"


def test_meta_regression_drops_missing_features_and_uses_available(cfg):
    rng = np.random.default_rng(3)
    f = _features(rng, with_rice=True, with_nk=True)
    out = meta_regression(cfg, _profiles(f, -0.1, rng=rng), None, f)
    assert set(out["feature"]) == {"ln_dist_hub", "rice_sufficiency", "n_kota"}
    f2 = f.assign(rice_sufficiency=np.where(f["province_id"] == 5, np.nan, f["rice_sufficiency"]))
    assert "rice_sufficiency" not in set(meta_regression(cfg, _profiles(f2, -0.1, rng=rng), None, f2)["feature"])
    empty = meta_regression(cfg, _profiles(f, -0.1, rng=rng), None, f.assign(ln_dist_hub=np.nan, n_kota=np.nan,
                                                                             rice_sufficiency=np.nan))
    assert len(empty) == 0 and list(empty.columns) == ASSOC_COLUMNS + META_EXTRA


def test_meta_regression_bootstrap_widens_interval(cfg):
    rng = np.random.default_rng(4)
    f = _features(rng)
    prof = _profiles(f, -0.1, rng=rng, coms=["gula_pasir"])
    reps = []
    for r in range(60):                                      # replikasi dengan derau besar -> interval bootstrap lebih lebar
        g = _profiles(f, -0.1, se=0.05, rng=rng, coms=["gula_pasir"])
        g["estimate"] += rng.normal(0, 0.4, len(g))
        reps.append(g.assign(rep=r))
    boot = pd.concat(reps)
    cr2 = meta_regression(cfg, prof, None, f).query("commodity == 'gula_pasir'").iloc[0]
    both = meta_regression(cfg, prof, boot, f).query("commodity == 'gula_pasir'").iloc[0]
    assert both["ci_method"] == "max(cr2, bootstrap)" and both["se_boot"] > 0.05
    assert both["ci_low"] <= cr2["ci_low"] and both["ci_high"] >= cr2["ci_high"]
    assert (both["ci_high"] - both["ci_low"]) > 2 * (cr2["ci_high"] - cr2["ci_low"])


def test_two_way_demean_removes_both_effects():
    rng = np.random.default_rng(5)
    df = pd.DataFrame({"a": rng.integers(0, 4, 300), "b": rng.integers(0, 6, 300)})
    df["y"] = df["a"] * 2.0 + df["b"] * -1.5 + rng.normal(0, 0.1, 300)
    out = _two_way_demean(df, ["y"], ["a"], ["b"])
    assert out["y"].abs().max() < 0.6 and abs(out.groupby(df["a"])["y"].mean()).max() < 1e-6
    assert abs(out.groupby(df["b"])["y"].mean()).max() < 1e-6


def _panel(cfg, gamma, rng, coms=("gula_pasir", "beras"), n_weeks=440, noise=0.004):
    weeks = driver_weeks(cfg)
    de = rng.normal(0, 0.01, len(weeks))
    de[0] = np.nan
    drivers = pd.DataFrame({"week": weeks, "de": de})
    f = _features(rng)
    z = ((f["ln_dist_hub"] - f["ln_dist_hub"].mean()) / f["ln_dist_hub"].std(ddof=0)).to_numpy()
    wk = weeks[weeks >= pd.Timestamp(cfg.params["period"]["start"])][:n_weeks]
    cum = np.nan_to_num(drivers.set_index("week").loc[wk, "de"].to_numpy())
    rows = []
    for com in coms:
        for u in range(34):
            dp = (0.3 + gamma * z[u]) * cum + rng.normal(0, noise, len(wk))
            rows.append(pd.DataFrame({"week": wk, "province_id": u + 1, "commodity": com,
                                      "log_price": 8 + np.cumsum(dp)}))
    return pd.concat(rows, ignore_index=True), drivers, f


def test_fe_interaction_recovers_planted_gamma(cfg):
    rng = np.random.default_rng(6)
    panel, drivers, f = _panel(cfg, -0.15, rng)
    out = fe_interaction(cfg, panel, drivers, f, horizons=[4, 8])
    assert list(out.columns) == ASSOC_COLUMNS + META_EXTRA and set(out["method"]) == {"fe_interaction"}
    assert set(out["horizon"]) == {4, 8} and set(out["feature"]) == {"ln_dist_hub"}
    for _, r in out.iterrows():
        assert abs(r["estimate"] + 0.15) < 3 * (r["ci_high"] - r["estimate"]) / 1.96 + 0.02
        assert r["ci_low"] < r["estimate"] < r["ci_high"] and r["p_value"] < 0.01 and r["n"] > 5000


def test_fe_interaction_null_effect_and_eligibility(cfg):
    rng = np.random.default_rng(7)
    panel, drivers, f = _panel(cfg, 0.0, rng)
    out = fe_interaction(cfg, panel, drivers, f, horizons=[4])
    assert abs(out["estimate"].iloc[0]) < 0.08
    elig = pd.DataFrame({"province_id": np.repeat(np.arange(1, 35), 2), "commodity": ["gula_pasir", "beras"] * 34,
                         "eligible": [True, False] * 34})
    sub = fe_interaction(cfg, panel, drivers, f, elig=elig, horizons=[4])
    assert sub["n"].iloc[0] < out["n"].iloc[0] * 0.6
    assert len(fe_interaction(cfg, panel, drivers, f.assign(ln_dist_hub=np.nan), horizons=[4])) == 0
