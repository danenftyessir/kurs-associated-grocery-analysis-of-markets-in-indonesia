"""OLS dengan SE cluster, varians jangka panjang Newey-West, dan uji Diebold-Mariano."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class OLSResult:
    beta: np.ndarray
    se: np.ndarray
    n_obs: int
    n_clusters: int
    resid: np.ndarray


def ols_cluster(y: np.ndarray, X: np.ndarray, groups: np.ndarray) -> OLSResult:
    """OLS dengan SE cluster-robust (CR1, koreksi G/(G-1)·(n-1)/(n-k)).

    Di KAGAMI groups = minggu (proposal §5.2d: inferensi per minggu). Baris dengan NaN di y/X atau grup kosong
    (NaN/NaT/None) dibuang.
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    codes, uniq = pd.factorize(np.asarray(groups))
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1) & (codes >= 0)
    y, X = y[ok], X[ok]
    codes, uniq = pd.factorize(codes[ok])
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    u = y - X @ beta
    G = len(uniq)
    Xu = X * u[:, None]
    scores = np.column_stack([np.bincount(codes, weights=Xu[:, j], minlength=G) for j in range(k)]) if k else \
        np.zeros((G, 0))
    meat = scores.T @ scores
    c = (G / (G - 1)) * ((n - 1) / (n - k)) if G > 1 and n > k else 1.0
    V = c * xtx_inv @ meat @ xtx_inv
    return OLSResult(beta=beta, se=np.sqrt(np.clip(np.diag(V), 0, None)), n_obs=n, n_clusters=G, resid=u)


def newey_west_lrv(x: np.ndarray, lags: int) -> float:
    """Varians jangka panjang Newey-West (kernel Bartlett) dari deret x (rata-rata dikurangkan)."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)] - np.nanmean(x)
    n = len(x)
    lrv = x @ x / n
    for lag in range(1, min(lags, n - 1) + 1):
        w = 1 - lag / (lags + 1)
        lrv += 2 * w * (x[lag:] @ x[:-lag]) / n
    return float(lrv)


def diebold_mariano(e1: np.ndarray, e2: np.ndarray, h: int, loss: str = "abs") -> tuple[float, float]:
    """Uji DM dua sisi (HAC, lag h-1) dengan koreksi Harvey-Leybourne-Newbold.

    e1 = galat model pembanding (mis. M1), e2 = galat model kandidat (mis. M2).
    Statistik > 0 berarti kandidat lebih akurat. Return (stat, p_value).
    """
    f = np.abs if loss == "abs" else np.square
    d = f(np.asarray(e1, float)) - f(np.asarray(e2, float))
    d = d[np.isfinite(d)]
    n = len(d)
    if n < 3:
        return float("nan"), float("nan")
    lrv = newey_west_lrv(d, max(h - 1, 0))
    if lrv <= 0:
        return float("nan"), float("nan")
    dm = d.mean() / np.sqrt(lrv / n)
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = float(dm * hln)
    return stat, float(2 * stats.t.sf(abs(stat), df=n - 1))
