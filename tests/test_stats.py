"""Uji unit mesin statistik bersama."""

import numpy as np

from kagami.stats.meta import bh_fdr, dersimonian_laird, eb_shrink, reml_tau2
from kagami.stats.regression import diebold_mariano, ols_cluster
from kagami.stats.resampling import circular_shift, moving_block_indices


def test_ols_recovers_beta():
    rng = np.random.default_rng(0)
    n = 2000
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    y = X @ np.array([1.0, 0.5]) + rng.normal(scale=0.1, size=n)
    res = ols_cluster(y, X, groups=np.arange(n) // 10)
    assert np.allclose(res.beta, [1.0, 0.5], atol=0.02)
    assert res.n_clusters == 200 and (res.se > 0).all()


def test_ols_cluster_se_larger_with_common_shock():
    rng = np.random.default_rng(1)
    weeks, units = 300, 30
    shock = np.repeat(rng.normal(size=weeks), units)        # guncangan bersama per minggu
    x = np.repeat(rng.normal(size=weeks), units)            # regresor nasional (seperti Δe)
    y = 0.2 * x + shock + rng.normal(scale=0.1, size=weeks * units)
    X = np.column_stack([np.ones_like(x), x])
    g = np.repeat(np.arange(weeks), units)
    se_week = ols_cluster(y, X, g).se[1]
    se_row = ols_cluster(y, X, np.arange(len(y))).se[1]
    assert se_week > 3 * se_row


def test_dl_and_shrinkage():
    est = np.array([0.0, 0.0, 0.0, 0.0])
    var = np.full(4, 0.01)
    r = dersimonian_laird(est, var)
    assert r.tau2 == 0 and r.I2 == 0
    assert np.allclose(eb_shrink(np.array([1.0, -1.0]), np.array([1.0, 1.0]), 0.0, 0.0), 0.0)
    rng = np.random.default_rng(2)
    est = rng.normal(scale=1.0, size=200)
    var = np.full(200, 0.04)
    r = dersimonian_laird(est, var)
    assert 0.7 < r.tau2 < 1.4 and r.I2 > 0.9
    assert abs(reml_tau2(est, var) - r.tau2) < 0.2


def test_bh_fdr_monotone():
    q = bh_fdr(np.array([0.01, 0.04, 0.03, 0.2]))
    assert np.allclose(q, [0.04, 0.16 / 3, 0.16 / 3, 0.2])


def test_resampling():
    rng = np.random.default_rng(3)
    idx = moving_block_indices(460, 13, rng)
    assert len(idx) == 460 and idx.min() >= 0 and idx.max() < 460
    assert (np.diff(idx[:13]) == 1).all()
    s = circular_shift(460, 52, rng)
    assert 52 <= s <= 408


def test_dm_detects_better_model():
    rng = np.random.default_rng(4)
    e_bad = rng.normal(scale=2.0, size=300)
    e_good = rng.normal(scale=1.0, size=300)
    stat, p = diebold_mariano(e_bad, e_good, h=1)
    assert stat > 0 and p < 0.01
