"""Clustering provinsi + pemilihan k vs plasebo (WP-19). docs/METHODS.md §M2.2-3.

Clustering SELALU dijalankan (tidak bergantung pada G-het, D-004). Matriks fitur: features/clustering.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config
from kagami.utils.todo import todo


def ward_labels(X: np.ndarray, k: int) -> np.ndarray:
    """WP-19. Ward (Euclidean) via scipy.cluster.hierarchy; k=1 -> semua label 0."""
    todo("WP-19")


def select_k(cfg: Config, X: np.ndarray, placebo_X: list[np.ndarray]) -> pd.DataFrame:
    """WP-19. k ∈ {2..6}: silhouette data asli vs persentil 95 silhouette MAKSIMUM tiap matriks plasebo.

    accepted = max silhouette asli > p95 plasebo; bila tidak, k=1 ("tidak ada struktur regional terdeteksi").
    -> artefak 'cluster_selection'.
    """
    todo("WP-19")
