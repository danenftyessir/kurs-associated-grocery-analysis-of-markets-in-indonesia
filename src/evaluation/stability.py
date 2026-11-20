"""Stabilitas klaster: K-Means ARI, ko-asignasi bootstrap, Jaccard per klaster (WP-20). docs/METHODS.md §M2.4."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config


def kmeans_agreement(cfg: Config, X: np.ndarray, ward: np.ndarray, k: int) -> tuple[np.ndarray, float]:
    """WP-20. KMeans(k-means++, n_init=50, random_state=cfg.seed); ARI vs Ward (sklearn.metrics)."""
    todo("WP-20")


def bootstrap_stability(cfg: Config, X_boot: list[np.ndarray], ward: np.ndarray,
                        k: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WP-20. Klaster ulang tiap replikasi bootstrap Task 1 -> matriks ko-asignasi (artefak 'coassign')
    dan Jaccard maksimum per klaster asli (Hennig 2007); jaccard < 0.6 -> weak=True (artefak 'clusters').
    """
    todo("WP-20")


def compare_partitions(cfg: Config, labels: pd.Series) -> pd.DataFrame:
    """WP-20. Interpretasi: ARI klaster vs zona HET beras, Jawa vs luar Jawa, kuantil n_kota
    (cek artefak desain sampling). Label klaster netral K1, K2, ...
    -> artefak 'partition_compare' (partition, ari, n_groups).
    """
    todo("WP-20")
