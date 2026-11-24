"""Task 2 -- penemuan pola regional (proposal §5.3). Notebook: notebooks/02_task2_patterns.ipynb.

BERAT (uji struktur tertanam: δ x k_true x planted_reps) -> jalankan di Kaggle/Colab.
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import heterogeneity, planted, stability
from kagami.features import clustering as cluster_features
from kagami.models import clustering
from kagami.tracking.logger import tracked
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("profiles", "response_features", "placebo_stats", "boot_replicates")
OPTIONAL = ("province_features",)   # pembanding partisi n_kota (D-140); notebook menariknya juga


@tracked("task2")   # log eksekusi & evaluasi terpusat (WP-36, D-137)
def run(cfg: Config) -> None:
    require(cfg, *REQUIRES)
    profiles, feats, placebo, boot = (read_artifact(cfg, n) for n in REQUIRES)

    obs = heterogeneity.heterogeneity_stats(profiles, horizon=8)
    null = pd.concat([heterogeneity.heterogeneity_stats(g, horizon=8).assign(rep=r)
                      for r, g in placebo.groupby("rep")], ignore_index=True)
    write_artifact(cfg, "heterogeneity", heterogeneity.placebo_pvalues(cfg, obs, null))

    X = cluster_features.feature_matrix(cfg, feats)
    Xp = cluster_features.replicate_feature_matrices(cfg, placebo)
    sel = clustering.select_k(cfg, X.to_numpy(), Xp)
    write_artifact(cfg, "cluster_selection", sel)
    k = int(sel.loc[sel["accepted"], "k"].iloc[0]) if sel["accepted"].any() else 1

    ward = clustering.ward_labels(X.to_numpy(), k)
    km_labels, ari = stability.kmeans_agreement(cfg, X.to_numpy(), ward, k)
    coassign, clusters = stability.bootstrap_stability(
        cfg, cluster_features.replicate_feature_matrices(cfg, boot), ward, k, ids=list(X.index))
    kmeans = pd.DataFrame({"province_id": list(X.index), "method": "kmeans", "k": k,
                           "cluster": [f"K{int(c) + 1}" for c in km_labels], "jaccard": float("nan"), "weak": False})
    clusters = pd.concat([clusters, kmeans], ignore_index=True)
    clusters["ari_kmeans"] = ari
    write_artifact(cfg, "clusters", clusters)
    write_artifact(cfg, "coassign", coassign)
    n_kota = None
    if exists(cfg, "province_features"):
        n_kota = read_artifact(cfg, "province_features").set_index("province_id")["n_kota"]
    write_artifact(cfg, "partition_compare",
                   stability.compare_partitions(cfg, pd.Series(ward, index=X.index), n_kota=n_kota))
    # δ ditanam pada deviasi plasebo MENTAH, lalu susut EB & z-score seperti data asli (D-126)
    write_artifact(cfg, "planted_recovery", planted.recovery_curve(cfg, planted.deviation_matrices(cfg, placebo)))
