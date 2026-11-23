"""WP-19/20: matriks fitur, Ward, pilih k vs plasebo, stabilitas, pembanding partisi (struktur tertanam diketahui)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from kagami.evaluation.stability import bootstrap_stability, compare_partitions, kmeans_agreement
from kagami.features.clustering import feature_columns, feature_matrix, replicate_feature_matrices
from kagami.models.clustering import best_silhouette, select_k, ward_labels

N, F = 34, 12


def _blobs(k, sep, seed=0, noise=1.0):
    rng = np.random.default_rng(seed)
    truth = np.arange(N) % k
    centers = rng.normal(0, 1, (k, F))
    centers = sep * centers / np.linalg.norm(centers, axis=1, keepdims=True)
    return centers[truth] + rng.normal(0, noise, (N, F)), truth


def _z(X):
    return (X - X.mean(0)) / X.std(0)


def test_ward_labels_basic():
    X, truth = _blobs(3, 8.0)
    lab = ward_labels(X, 3)
    assert set(lab) == {0, 1, 2} and adjusted_rand_score(truth, lab) == 1.0
    assert lab[0] == 0                                           # label menurut kemunculan pertama
    assert (ward_labels(X, 1) == 0).all() and len(ward_labels(X, 1)) == N
    assert (ward_labels(X, 3) == ward_labels(X, 3)).all()


def test_best_silhouette_and_select_k_detects_structure(cfg):
    X, truth = _blobs(3, 10.0)
    rng = np.random.default_rng(1)
    placebo = [_z(rng.normal(0, 1, (N, F))) for _ in range(60)]
    sel = select_k(cfg, _z(X), placebo).set_index("k")
    assert list(sel.columns) == ["silhouette", "placebo_p95", "accepted"] and 1 in sel.index
    assert sel["accepted"].sum() == 1 and bool(sel.loc[3, "accepted"]) and not bool(sel.loc[1, "accepted"])
    assert sel.loc[3, "silhouette"] == sel["silhouette"].max() > sel.loc[3, "placebo_p95"]
    assert best_silhouette(_z(X), [2, 3, 4, 5, 6])[0] == 3


def test_select_k_noise_gives_k1(cfg):
    rng = np.random.default_rng(2)
    placebo = [_z(rng.normal(0, 1, (N, F))) for _ in range(60)]
    sel = select_k(cfg, _z(rng.normal(0, 1, (N, F))), placebo).set_index("k")
    assert bool(sel.loc[1, "accepted"]) and sel["accepted"].sum() == 1          # "tidak ada struktur" = hasil sah
    assert sel["placebo_p95"].nunique() == 1


def test_kmeans_agreement(cfg):
    X, truth = _blobs(3, 10.0)
    labels, ari = kmeans_agreement(cfg, _z(X), ward_labels(_z(X), 3), 3)
    assert ari > 0.95 and set(labels) == {0, 1, 2}
    lab1, ari1 = kmeans_agreement(cfg, X, np.zeros(N, int), 1)
    assert (lab1 == 0).all() and ari1 == 1.0


def test_bootstrap_stability_strong_vs_weak(cfg):
    X, _ = _blobs(3, 12.0)
    rng = np.random.default_rng(3)
    boots = [_z(X + rng.normal(0, 0.5, X.shape)) for _ in range(30)]
    ward = ward_labels(_z(X), 3)
    coassign, clusters = bootstrap_stability(cfg, boots, ward, 3)
    assert len(coassign) == N * N and set(coassign.columns) == {"province_i", "province_j", "share"}
    M = coassign.pivot(index="province_i", columns="province_j", values="share").to_numpy()
    assert np.allclose(np.diag(M), 1) and np.allclose(M, M.T)
    assert (clusters["jaccard"] > 0.95).all() and not clusters["weak"].any()
    assert set(clusters["cluster"]) == {"K1", "K2", "K3"}
    assert list(clusters.columns)[:3] == ["province_id", "method", "k"]
    noisy = [_z(rng.normal(0, 1, (N, F))) for _ in range(30)]               # bootstrap tak berkaitan dengan struktur
    _, weak = bootstrap_stability(cfg, noisy, ward, 3)
    assert weak["jaccard"].max() < 0.6 and weak["weak"].all()


def test_bootstrap_stability_k1_is_trivially_stable(cfg):
    _, clusters = bootstrap_stability(cfg, [np.zeros((N, F))] * 3, np.zeros(N, int), 1, ids=range(101, 101 + N))
    assert (clusters["jaccard"] == 1).all() and clusters["province_id"].iloc[0] == 101


def test_compare_partitions(cfg):
    reg = cfg.regions.set_index("province_id")
    ward_like = pd.Series(reg["het_zone_beras"].to_numpy() - 1, index=reg.index)          # persis zona HET
    out = compare_partitions(cfg, ward_like).set_index("partition")
    assert out.loc["het_zone_beras", "ari"] == 1.0 and out.loc["het_zone_beras", "n_groups"] == 3
    assert out.loc["java_vs_outside", "n_groups"] == 2 and "n_kota_tercile" not in out.index
    n_kota = pd.Series(np.arange(len(reg)) % 5 + 1.0, index=reg.index)
    withk = compare_partitions(cfg, ward_like, n_kota=n_kota).set_index("partition")
    assert withk.loc["n_kota_tercile", "n_groups"] == 3
    trivial = compare_partitions(cfg, pd.Series(0, index=reg.index)).set_index("partition")
    assert trivial["ari"].isna().all() and (trivial["n_groups"] > 1).all()   # k = 1: ARI tidak berlaku (U106)


def _province_rows(cfg, delta_by_unit, rep=0, se=0.05):
    rows = []
    for prefix, com, h in feature_columns(cfg):
        drv = "e" if prefix == "R" else "w"
        for u, d in delta_by_unit.items():
            rows.append({"rep": rep, "level": "province", "unit": str(u), "commodity": com, "driver": drv,
                         "horizon": h, "estimate": d[(prefix, com, h)], "se": se})
    return pd.DataFrame(rows)


def test_feature_columns_follow_config(cfg):
    cols = feature_columns(cfg)
    focus = cfg.commodity_ids("focus")
    assert {c for _, c, _ in cols} == set(focus)
    assert not any(p == "W" and c == "bawang_putih" for p, c, _ in cols)            # tanpa padanan harga dunia
    assert sum(p == "R" for p, _, _ in cols) == 3 * len(focus)


def test_feature_matrix_and_replicates_agree_on_structure(cfg):
    cols = feature_columns(cfg)
    rng = np.random.default_rng(4)
    truth = np.arange(34) % 3
    shift = rng.normal(0, 1, (3, len(cols)))
    deltas = {u + 1: {c: float(shift[truth[u], j] + rng.normal(0, 0.05)) for j, c in enumerate(cols)}
              for u in range(34)}
    rep = _province_rows(cfg, deltas)
    # response_features sintetis (level province): kolom R4.. / W4.. per komoditas
    rf = []
    for u, d in deltas.items():
        for com in cfg.commodity_ids("focus"):
            row = {"level": "province", "unit": str(u), "commodity": com}
            for (p, c, h), v in d.items():
                if c == com:
                    row[f"{p}{h}"] = v
            rf.append(row)
    X = feature_matrix(cfg, pd.DataFrame(rf))
    assert X.shape == (34, len(cols)) and list(X.index) == list(range(1, 35))
    assert np.allclose(X.mean(), 0, atol=1e-9) and np.allclose(X.std(ddof=0), 1)
    assert adjusted_rand_score(truth, ward_labels(X.to_numpy(), 3)) == 1.0
    (Xr,) = replicate_feature_matrices(cfg, rep)
    assert Xr.shape == X.shape and adjusted_rand_score(truth, ward_labels(Xr, 3)) == 1.0
    (raw,) = replicate_feature_matrices(cfg, rep, standardize=False)
    assert raw.std() > 0.3 and not np.allclose(raw.std(axis=0), 1)                   # satuan respons, bukan z-score


def test_replicates_require_se_and_order_by_rep(cfg):
    cols = feature_columns(cfg)
    d = {u: {c: float(u) for c in cols} for u in range(1, 35)}
    a, b = _province_rows(cfg, d, rep=0), _province_rows(cfg, d, rep=1)
    assert len(replicate_feature_matrices(cfg, pd.concat([b, a]))) == 2
    with pytest.raises(KeyError):
        replicate_feature_matrices(cfg, a.drop(columns="se"))
