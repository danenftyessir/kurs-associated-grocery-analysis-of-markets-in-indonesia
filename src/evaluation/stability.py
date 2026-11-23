"""Stabilitas klaster: K-Means ARI, ko-asignasi bootstrap, Jaccard per klaster (WP-20). docs/METHODS.md §M2.4."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

from kagami.models.clustering import ward_labels
from kagami.utils.config import Config

CLUSTER_COLUMNS = ["province_id", "method", "k", "cluster", "jaccard", "weak"]


def kmeans_agreement(cfg: Config, X: np.ndarray, ward: np.ndarray, k: int) -> tuple[np.ndarray, float]:
    """WP-20. KMeans(k-means++, n_init=50, random_state=cfg.seed); ARI vs Ward (sklearn.metrics).

    k = 1 -> semua label 0 dan ARI = 1 (partisi trivial identik). n_init = params.clustering.kmeans_restarts.
    """
    X = np.asarray(X, float)
    if k <= 1:
        return np.zeros(len(X), dtype=int), 1.0
    km = KMeans(n_clusters=k, init="k-means++", n_init=int(cfg.params["clustering"]["kmeans_restarts"]),
                random_state=cfg.seed).fit(X)
    return km.labels_, float(adjusted_rand_score(ward, km.labels_))


def _jaccard_max(members: np.ndarray, labels: np.ndarray) -> float:
    """Jaccard maksimum antara himpunan `members` (boolean) dan setiap klaster pada `labels` (Hennig 2007)."""
    best = 0.0
    for c in np.unique(labels):
        other = labels == c
        union = (members | other).sum()
        best = max(best, (members & other).sum() / union if union else 0.0)
    return best


def bootstrap_stability(cfg: Config, X_boot: list[np.ndarray], ward: np.ndarray, k: int,
                        ids: Sequence[int] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WP-20. Klaster ulang tiap replikasi bootstrap Task 1 -> matriks ko-asignasi (artefak 'coassign')
    dan Jaccard maksimum per klaster asli (Hennig 2007); jaccard < 0.6 -> weak=True (artefak 'clusters').

    X_boot: matriks fitur (provinsi x fitur, terstandardisasi) per replikasi; Ward diulang dengan k yang sama.
    coassign: semua pasangan (province_i, province_j) termasuk diagonal, share = porsi replikasi yang menempatkan
    keduanya dalam klaster yang sama. clusters: satu baris per provinsi (method='ward'), cluster = 'K1', 'K2', ...
    (label netral menurut kemunculan pertama), jaccard = rerata atas replikasi dari Jaccard maksimum klaster asli
    provinsi itu, weak = jaccard < params.clustering.jaccard_weak. ids = province_id tiap baris (default 1..n).
    """
    n = len(ward)
    ids = list(range(1, n + 1)) if ids is None else list(ids)
    same = np.zeros((n, n))
    jac = {c: [] for c in np.unique(ward)}
    for Xb in X_boot:
        lab = ward_labels(np.asarray(Xb, float), k)
        same += lab[:, None] == lab[None, :]
        for c in jac:
            jac[c].append(_jaccard_max(ward == c, lab))
    share = same / max(len(X_boot), 1)
    coassign = pd.DataFrame({"province_i": np.repeat(ids, n), "province_j": np.tile(ids, n), "share": share.ravel()})
    weak_below = float(cfg.params["clustering"]["jaccard_weak"])
    stab = {c: float(np.mean(v)) if v else np.nan for c, v in jac.items()}
    clusters = pd.DataFrame({
        "province_id": ids, "method": "ward", "k": k, "cluster": [f"K{int(c) + 1}" for c in ward],
        "jaccard": [stab[c] for c in ward]})
    clusters["weak"] = clusters["jaccard"] < weak_below
    return coassign, clusters[CLUSTER_COLUMNS]


def _ari_row(name: str, labels: pd.Series, groups: pd.Series) -> dict:
    g = groups.reindex(labels.index)
    ok = g.notna()
    ari = float(adjusted_rand_score(labels[ok], g[ok])) if ok.sum() > 1 else np.nan
    return {"partition": name, "ari": ari, "n_groups": int(g[ok].nunique())}


def compare_partitions(cfg: Config, labels: pd.Series, n_kota: pd.Series | None = None) -> pd.DataFrame:
    """WP-20. Interpretasi: ARI klaster vs zona HET beras, Jawa vs luar Jawa, kuantil n_kota
    (cek artefak desain sampling). Label klaster netral K1, K2, ...
    -> artefak 'partition_compare' (partition, ari, n_groups).

    labels: label klaster (index = province_id). n_kota (opsional, index = province_id): jumlah kota sampel PIHPS;
    dibagi menjadi tiga kelompok kuantil (rank-based); tanpa n_kota (U15) baris itu dilewati. Tambahan: 7 wilayah.
    Klaster tunggal (k = 1) -> ari = NaN ("tidak berlaku"), bukan 0 yang terbaca "tidak cocok" (U106).
    """
    reg = cfg.regions.set_index("province_id")
    rows = [_ari_row("het_zone_beras", labels, reg["het_zone_beras"]),
            _ari_row("java_vs_outside", labels, reg["java"]),
            _ari_row("region_7", labels, reg["region"])]
    if n_kota is not None and n_kota.notna().sum() >= 3:
        tercile = pd.qcut(n_kota.rank(method="first"), 3, labels=False)
        rows.append(_ari_row("n_kota_tercile", labels, tercile))
    out = pd.DataFrame(rows, columns=["partition", "ari", "n_groups"])
    if labels.nunique(dropna=True) < 2:
        out["ari"] = np.nan
    return out
