"""WP-21: uji struktur tertanam pada matriks plasebo sintetis (dummy, bukan hasil)."""

import numpy as np
import pandas as pd
import pytest
from scipy.cluster.hierarchy import fcluster, linkage

from kagami.evaluation import planted as pl
from kagami.utils.todo import NotImplementedYet


def _ward(X, k):
    """Ward rujukan untuk tes (WP-19 milik Ardell masih stub)."""
    if k <= 1:
        return np.zeros(len(X), dtype=int)
    return fcluster(linkage(X, method="ward"), t=k, criterion="maxclust") - 1


def _placebo(n=30, n_prov=34, n_feat=12, sd=0.3, seed=0):
    rng = np.random.default_rng(seed)
    return [rng.normal(0, sd, (n_prov, n_feat)) for _ in range(n)]


def test_plant_structure_balanced_shift():
    X = np.zeros((34, 12))
    Xp, lab = pl.plant_structure(X, 3, 0.2, np.random.default_rng(1))
    assert sorted(np.bincount(lab)) == [11, 11, 12]
    C = np.array([Xp[lab == j].mean(axis=0) for j in range(3)])
    assert np.allclose(Xp, C[lab])                                     # pergeseran konstan per kelompok
    for i, j in ((0, 1), (0, 2), (1, 2)):                              # simpleks: semua pasangan berjarak δ·√F
        assert np.linalg.norm(C[i] - C[j]) == pytest.approx(0.2 * np.sqrt(12))
        assert np.sqrt(np.mean((C[i] - C[j]) ** 2)) == pytest.approx(0.2)   # RMS per fitur = δ
    with pytest.raises(ValueError):
        pl.plant_structure(np.zeros((34, 2)), 3, 0.2, np.random.default_rng(1))


def test_zscore_constant_column():
    Z = pl._zscore(np.column_stack([np.arange(5.0), np.ones(5)]))
    assert np.allclose(Z[:, 1], 0) and Z[:, 0].mean() == pytest.approx(0) and Z[:, 0].std() == pytest.approx(1)


def test_best_silhouette_finds_clear_groups():
    rng = np.random.default_rng(3)
    lab = np.repeat([0, 1, 2], [12, 11, 11])
    X = lab[:, None] * 5.0 + rng.normal(0, 0.1, (34, 4))
    k, s = pl.best_silhouette(X, [2, 3, 4, 5, 6], _ward)
    assert k == 3 and s > 0.8


def test_recovery_curve_monotone_and_reproducible(cfg):
    plac = _placebo()
    out = pl.recovery_curve(cfg, plac, ward=_ward, reps=20)
    assert list(out.columns[:4]) == pl.PLANTED_COLUMNS
    assert len(out) == len(cfg.params["clustering"]["planted_deltas"]) * len(pl.K_TRUE)
    assert out["recovery_rate"].between(0, 1).all() and np.isfinite(out["threshold"]).all()
    for k, g in out.groupby("k_true"):
        g = g.sort_values("delta")
        assert g["recovery_rate"].iloc[0] <= 0.2            # δ 0,1 << derau 0,3 -> tidak terdeteksi
        assert g["recovery_rate"].iloc[-1] >= 0.8           # δ 0,5 -> ditemukan kembali
        assert g["ari_mean"].iloc[-1] > g["ari_mean"].iloc[0]
    assert (out["recovery_rate"] <= out["k_correct_rate"] + 1e-12).all()
    again = pl.recovery_curve(cfg, plac, ward=_ward, reps=20)
    pd.testing.assert_frame_equal(out, again)                # seed + 2101


def test_threshold_from_noise_rejects_noise(cfg):
    """Matriks plasebo murni: proporsi yang lolos ambang p95 ≈ 5%."""
    plac = _placebo(n=200, seed=5)
    thr = pl.placebo_threshold(cfg, [pl._zscore(X) for X in plac], _ward)
    fresh = _placebo(n=100, seed=6)
    s = np.array([pl.best_silhouette(pl._zscore(X), [2, 3, 4, 5, 6], _ward)[1] for X in fresh])
    assert (s > thr).mean() < 0.15


def test_detection_limit():
    d = pd.DataFrame({"delta": [0.1, 0.2, 0.3] * 2, "k_true": [2] * 3 + [3] * 3,
                      "recovery_rate": [0.1, 0.85, 0.95, 0.0, 0.3, 0.6], "ari_mean": 0.5})
    lim = pl.detection_limit(d).set_index("k_true")["delta_min"]
    assert lim[2] == pytest.approx(0.2) and np.isnan(lim[3])


def test_default_ward_from_wp19(cfg):
    try:
        out = pl.recovery_curve(cfg, _placebo(n=5), reps=2)
    except NotImplementedYet:
        pytest.skip("ward_labels (WP-19, Ardell) belum diimplementasi")
    assert len(out) == len(cfg.params["clustering"]["planted_deltas"]) * len(pl.K_TRUE)
