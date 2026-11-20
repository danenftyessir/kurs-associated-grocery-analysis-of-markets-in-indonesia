"""Local projections dengan lag-augmentation (WP-13). Persamaan: docs/METHODS.md §M1."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config
from kagami.stats.regression import ols_cluster  # noqa: F401  (dipakai implementasi WP-13)


def build_design(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                 commodity: str, horizon: int, lags: int, asymmetric: bool = False) -> pd.DataFrame:
    """WP-13. Susun y^{(h)} = p_{t+h} - p_{t-1} dan regresor untuk satu komoditas & horizon.

    Regresor: de (atau de_pos & de_neg bila asymmetric), dw (bila komoditas punya padanan), lag 1..L dari
    Δp, de, dw; db lag 0..4; dummy Idulfitri relatif + dummy bulan; efek tetap seri (α_{i,r,h}) via demeaning.
    Kolom wajib keluaran: week, unit, y, regresor..., group (= week, untuk cluster).
    Hanya seri eligible; baris dengan y atau regresor NaN dibuang DAN dihitung (laporkan n_weeks).
    """
    todo("WP-13")


def fit_lp(cfg: Config, design: pd.DataFrame) -> pd.DataFrame:
    """WP-13. OLS + SE cluster per minggu (stats.regression.ols_cluster). -> driver, estimate, se, n_weeks."""
    todo("WP-13")


def fx_self_response(cfg: Config, drivers: pd.DataFrame, horizon: int, lags: int) -> float:
    """WP-13. γ(h): respons kumulatif log kurs terhadap de-nya sendiri (LP e_{t+h}-e_{t-1} pada de_t + lag).

    Dipakai untuk PT(i,h) = β(i,h)/γ(h) (proposal §5.2a).
    """
    todo("WP-13")


def national_profiles(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                      world: pd.DataFrame) -> pd.DataFrame:
    """WP-13. Loop komoditas x horizon 0..12 x {simetris, asimetris} -> baris artefak 'profiles' level='national'.

    driver ∈ {e, w, e_pos, e_neg, PT}. ci = estimate ± 1.96·se (interval bootstrap ditambahkan WP-16).
    """
    todo("WP-13")
