"""Matriks fitur provinsi untuk clustering Task 2 (WP-19). docs/METHODS.md §M2.2."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config
from kagami.utils.todo import todo


def feature_matrix(cfg: Config, response_features: pd.DataFrame) -> pd.DataFrame:
    """WP-19. Matriks 34 provinsi x fitur tersusut: R & W pada h ∈ {4,8,12} untuk komoditas fokus.

    Fitur distandardisasi (z-score per kolom); kolom W hanya untuk komoditas berpadanan.
    """
    todo("WP-19")


def replicate_feature_matrices(cfg: Config, replicates: pd.DataFrame) -> list[np.ndarray]:
    """WP-19. placebo_stats / boot_replicates -> satu matriks fitur provinsi per `rep`
    (fitur & standardisasi identik dengan feature_matrix). Dipakai select_k, planted, stabilitas.
    """
    todo("WP-19")
