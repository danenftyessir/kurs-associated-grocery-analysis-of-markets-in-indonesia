"""Clustering provinsi + pemilihan k vs plasebo (WP-19). docs/METHODS.md §M2.2-3.

Clustering SELALU dijalankan (tidak bergantung pada G-het, D-004). Matriks fitur: features/clustering.py.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import silhouette_score

from kagami.utils.config import Config

SELECTION_COLUMNS = ["k", "silhouette", "placebo_p95", "accepted"]


def ward_labels(X: np.ndarray, k: int) -> np.ndarray:
    """WP-19. Ward (Euclidean) via scipy.cluster.hierarchy; k=1 -> semua label 0.

    Label 0..k-1 diberi nomor menurut kemunculan pertama (baris terkecil = 0) agar deterministik.
    """
    X = np.asarray(X, float)
    if k <= 1 or len(X) <= 1:
        return np.zeros(len(X), dtype=int)
    raw = fcluster(linkage(X, method="ward"), t=k, criterion="maxclust")
    _, first = np.unique(raw, return_index=True)
    remap = {c: i for i, c in enumerate(raw[np.sort(first)])}
    return np.array([remap[c] for c in raw], dtype=int)


def best_silhouette(X: np.ndarray, ks: list[int],
                    ward: Callable[[np.ndarray, int], np.ndarray] = ward_labels) -> tuple[int, float]:
    """WP-19. (k*, s*) = argmax/max silhouette Euclidean Ward atas k ∈ ks (k ≥ 2); (1, NaN) bila tak terhitung.

    Aturan yang sama dengan `evaluation.planted.best_silhouette` (ambang plasebo identik)."""
    best_k, best_s = 1, -np.inf
    for k in ks:
        if k < 2 or k >= len(X):
            continue
        lab = ward(X, k)
        if len(np.unique(lab)) < 2:
            continue
        s = float(silhouette_score(X, lab, metric="euclidean"))
        if s > best_s:
            best_k, best_s = k, s
    return (best_k, best_s) if np.isfinite(best_s) else (1, np.nan)


def select_k(cfg: Config, X: np.ndarray, placebo_X: list[np.ndarray]) -> pd.DataFrame:
    """WP-19. k ∈ {2..6}: silhouette data asli vs persentil 95 silhouette MAKSIMUM tiap matriks plasebo.

    accepted = max silhouette asli > p95 plasebo; bila tidak, k=1 ("tidak ada struktur regional terdeteksi").
    -> artefak 'cluster_selection'.
    Satu baris per k (k=1: silhouette NaN, accepted = tidak ada k ≥ 2 yang lolos). `accepted` benar hanya pada
    k* (argmax silhouette) bila s* > p95; placebo_p95 = np.nanpercentile(maks silhouette tiap matriks plasebo,
    params.clustering.silhouette_placebo_pct), sama untuk semua baris. placebo_X sudah distandardisasi seperti X.
    """
    p = cfg.params["clustering"]
    ks = [int(k) for k in p["k_range"] if int(k) >= 2]
    sil = {}
    for k in ks:
        lab = ward_labels(X, k)
        sil[k] = float(silhouette_score(X, lab)) if k < len(X) and len(np.unique(lab)) > 1 else np.nan
    null = np.array([best_silhouette(Xp, ks)[1] for Xp in placebo_X])
    p95 = float(np.nanpercentile(null, float(p["silhouette_placebo_pct"]))) if np.isfinite(null).any() else np.nan
    k_star, s_star = best_silhouette(np.asarray(X, float), ks)
    ok = bool(np.isfinite(s_star) and np.isfinite(p95) and s_star > p95)
    rows = [{"k": 1, "silhouette": np.nan, "placebo_p95": p95, "accepted": not ok}]
    rows += [{"k": k, "silhouette": sil[k], "placebo_p95": p95, "accepted": ok and k == k_star} for k in ks]
    return pd.DataFrame(rows, columns=SELECTION_COLUMNS)
