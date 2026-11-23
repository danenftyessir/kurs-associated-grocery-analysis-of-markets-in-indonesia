"""WP-18 (heterogenitas vs plasebo) dan WP-22 (Kendall eksak) pada data sintetis (dummy, bukan hasil)."""

from itertools import permutations
from math import factorial

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from kagami.evaluation.heterogeneity import heterogeneity_stats, placebo_pvalues
from kagami.models.association import all_permutations, kendall_exact, kendall_permutation_test
from kagami.stats.meta import dersimonian_laird, reml_tau2

COMS = ["beras", "bawang_putih", "gula_pasir"]


def _dev_profiles(rng, tau=(0.0, 0.0, 0.5), se=0.1, n_prov=34, rep=None):
    """Deviasi provinsi δ ~ N(0, τ² + se²) per komoditas (driver e, h=8) + baris tersusut & horizon lain (diabaikan)."""
    rows = []
    for c, t in zip(COMS, tau):
        true = rng.normal(0, t, n_prov) if t > 0 else np.zeros(n_prov)
        est = true + rng.normal(0, se, n_prov)
        est -= est.mean()
        for r in range(n_prov):
            base = {"level": "province", "unit": str(r + 1), "commodity": c, "driver": "e", "se": se}
            rows.append({**base, "horizon": 8, "estimate": est[r], "shrunk": False})
            rows.append({**base, "horizon": 8, "estimate": 0.0, "shrunk": True})
            rows.append({**base, "horizon": 4, "estimate": 9.0, "shrunk": False})
    df = pd.DataFrame(rows)
    nat = pd.DataFrame({"level": "national", "unit": "ALL", "commodity": COMS, "driver": "e", "horizon": 8,
                        "estimate": 1.0, "se": 0.1, "shrunk": False})
    df = pd.concat([df, nat], ignore_index=True)
    return df.assign(rep=rep) if rep is not None else df


def test_heterogeneity_stats_matches_dl():
    rng = np.random.default_rng(1)
    prof = _dev_profiles(rng)
    out = heterogeneity_stats(prof, horizon=8)
    assert set(out["statistic"]) == {"Q", "tau2", "tau2_reml", "I2", "rho_bar"}
    g = prof[(prof.level == "province") & (prof.horizon == 8) & ~prof.shrunk & (prof.commodity == "gula_pasir")]
    r = dersimonian_laird(g["estimate"].to_numpy(), g["se"].to_numpy() ** 2)
    got = out[out.commodity == "gula_pasir"].set_index("statistic")["value"]
    assert got["Q"] == pytest.approx(r.Q) and got["tau2"] == pytest.approx(r.tau2)
    assert got["tau2_reml"] == pytest.approx(reml_tau2(g["estimate"].to_numpy(), g["se"].to_numpy() ** 2))
    assert got["tau2_reml"] > 0.1                                     # REML berdampingan dengan DL (WP-17)
    assert out.loc[out.commodity == "gula_pasir", "n_provinces"].iloc[0] == 34
    tau2 = out[out.statistic == "tau2"].set_index("commodity")["value"]
    assert tau2["gula_pasir"] > 0.1 and tau2["beras"] < 0.02
    assert -1 <= out.loc[out.statistic == "rho_bar", "value"].iloc[0] <= 1


def test_heterogeneity_needs_se():
    prof = _dev_profiles(np.random.default_rng(1)).drop(columns="se")
    with pytest.raises(KeyError):
        heterogeneity_stats(prof)


def test_rho_bar_detects_shared_pattern():
    rng = np.random.default_rng(3)
    prof = _dev_profiles(rng, tau=(0.3, 0.3, 0.3))
    common = rng.normal(0, 1, 34)
    m = (prof.level == "province") & (prof.horizon == 8) & ~prof.shrunk
    prof.loc[m, "estimate"] = np.tile(common, 3) + rng.normal(0, 0.05, m.sum())
    rho = heterogeneity_stats(prof).query("statistic == 'rho_bar'")["value"].iloc[0]
    assert rho > 0.9


def test_placebo_pvalues_flags_only_heterogeneous(cfg):
    rng = np.random.default_rng(7)
    obs = heterogeneity_stats(_dev_profiles(rng, tau=(0.0, 0.0, 0.5)))
    null = pd.concat([heterogeneity_stats(_dev_profiles(rng, tau=(0.0, 0.0, 0.0))).assign(rep=r)
                      for r in range(99)], ignore_index=True)
    out = placebo_pvalues(cfg, obs, null)
    assert list(out.columns[:6]) == ["commodity", "horizon", "statistic", "value", "p_placebo", "q_fdr"]
    assert (out["n_placebo"] == 99).all()
    q = out[out.statistic == "Q"].set_index("commodity")
    assert q.loc["gula_pasir", "p_placebo"] == pytest.approx(1 / 100)
    assert q.loc["gula_pasir", "reject"] and not q.loc["beras", "reject"]
    assert (out["p_placebo"].between(1 / 100, 1)).all()
    assert not out.loc[out.statistic != "Q", "reject"].any()
    # BH per statistik: q >= p
    assert (out["q_fdr"] >= out["p_placebo"] - 1e-12).all()


def test_placebo_pvalue_formula(cfg):
    obs = pd.DataFrame({"commodity": ["a"], "horizon": [8], "statistic": ["Q"], "value": [5.0], "n_provinces": [34]})
    null = pd.DataFrame({"commodity": "a", "horizon": 8, "statistic": "Q", "value": [1, 5, 7, np.nan], "rep": range(4)})
    out = placebo_pvalues(cfg, obs, null)
    assert out["n_placebo"].iloc[0] == 3 and out["p_placebo"].iloc[0] == pytest.approx(3 / 4)


@pytest.mark.parametrize("n", [1, 3, 5])
def test_all_permutations(n):
    P = all_permutations(n)
    assert P.shape == (factorial(n), n)
    assert {tuple(r) for r in P.tolist()} == set(permutations(range(n)))


def test_kendall_exact_matches_bruteforce():
    rng = np.random.default_rng(2)
    x = np.array([0.0, 0.0, 0.1, 0.4, 0.4, 0.7])                      # ties seperti rasio impor 0
    y = rng.normal(size=6)
    res = kendall_permutation_test(x, y)
    tau_obs = stats.kendalltau(x, y).statistic
    taus = np.array([stats.kendalltau(x, y[list(p)]).statistic for p in permutations(range(6))])
    assert res["tau"] == pytest.approx(tau_obs)
    assert res["p_two_sided"] == pytest.approx(np.mean(np.abs(taus) >= abs(tau_obs) - 1e-12))
    assert res["p_greater"] == pytest.approx(np.mean(taus >= tau_obs - 1e-12))
    assert res["n_perm"] == 720


def test_kendall_exact_ten_commodities(cfg):
    coms = cfg.commodity_ids()
    ratio = np.linspace(0, 0.9, 10)
    exposure = pd.DataFrame({"commodity": coms, "import_ratio_direct": ratio})
    feats = pd.DataFrame({"level": "national", "unit": "ALL", "commodity": coms, "PT8": ratio * 2 + 0.01})
    feats = pd.concat([feats, feats.assign(level="province", unit="1", PT8=-5.0)], ignore_index=True)
    out = kendall_exact(cfg, exposure, feats)
    r = out.iloc[0]
    assert list(out.columns[:10]) == ["level", "feature", "outcome", "estimate", "ci_low", "ci_high", "p_value",
                                     "method", "jackknife_min", "jackknife_max"]
    assert r["level"] == "commodity" and r["n"] == 10
    assert r["estimate"] == pytest.approx(1.0)
    assert r["p_greater"] == pytest.approx(1 / factorial(10))         # hanya urutan identitas
    assert r["p_value"] == pytest.approx(2 / factorial(10))
    assert r["jackknife_min"] == pytest.approx(1.0) and r["ci_high"] <= 1.0
