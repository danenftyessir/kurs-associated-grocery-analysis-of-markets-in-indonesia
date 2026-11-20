"""Resampling berbasis minggu: moving-block bootstrap dan plasebo geser-melingkar.

Semua fungsi mengembalikan INDEKS minggu, sehingga satu draw dipakai bersama untuk semua
provinsi, komoditas, dan horizon (korelasi silang terjaga -- proposal §5.2d).
"""

from __future__ import annotations

import numpy as np


def moving_block_indices(n_weeks: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Indeks minggu panjang n_weeks dari blok berurutan sepanjang `block` (Künsch 1989)."""
    if block >= n_weeks:
        return np.arange(n_weeks)
    n_blocks = int(np.ceil(n_weeks / block))
    starts = rng.integers(0, n_weeks - block + 1, size=n_blocks)
    idx = (starts[:, None] + np.arange(block)[None, :]).ravel()
    return idx[:n_weeks]


def circular_shift(n_weeks: int, min_shift: int, rng: np.random.Generator) -> int:
    """Pergeseran s ∈ [min_shift, n_weeks - min_shift] untuk np.roll(penggerak, s) terhadap harga."""
    if n_weeks <= 2 * min_shift:
        raise ValueError(f"Seri terlalu pendek ({n_weeks}) untuk pergeseran minimum {min_shift}")
    return int(rng.integers(min_shift, n_weeks - min_shift + 1))


def placebo_windows(candidate_starts: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Pilih n awal jendela plasebo (dengan pengembalian) dari minggu tanpa episode."""
    candidate_starts = np.asarray(candidate_starts)
    if len(candidate_starts) == 0:
        raise ValueError("Tidak ada minggu kandidat plasebo")
    return rng.choice(candidate_starts, size=n, replace=True)
