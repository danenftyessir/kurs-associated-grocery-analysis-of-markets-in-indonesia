"""Meta-analisis: Q, τ² (DerSimonian-Laird, REML), I², penyusutan empirical Bayes, FDR."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class HetResult:
    mu: float
    tau2: float
    Q: float
    I2: float
    k: int


def dersimonian_laird(est: np.ndarray, var: np.ndarray) -> HetResult:
    est, var = np.asarray(est, float), np.asarray(var, float)
    ok = np.isfinite(est) & np.isfinite(var) & (var > 0)
    est, var = est[ok], var[ok]
    k = len(est)
    w = 1 / var
    mu_fe = (w @ est) / w.sum()
    Q = float(w @ (est - mu_fe) ** 2)
    c = w.sum() - (w @ w) / w.sum()
    tau2 = max(0.0, (Q - (k - 1)) / c) if c > 0 else 0.0
    w_re = 1 / (var + tau2)
    mu = float((w_re @ est) / w_re.sum())
    I2 = max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0
    return HetResult(mu=mu, tau2=float(tau2), Q=Q, I2=float(I2), k=k)


def reml_tau2(est: np.ndarray, var: np.ndarray, tol: float = 1e-10, max_iter: int = 200) -> float:
    """τ² REML lewat iterasi Fisher scoring (cek terhadap DL, proposal §5.2e)."""
    est, var = np.asarray(est, float), np.asarray(var, float)
    ok = np.isfinite(est) & np.isfinite(var) & (var > 0)
    est, var = est[ok], var[ok]
    tau2 = dersimonian_laird(est, var).tau2
    for _ in range(max_iter):
        w = 1 / (var + tau2)
        mu = (w @ est) / w.sum()
        r = est - mu
        num = (w ** 2) @ (r ** 2 - var) + (w ** 2).sum() / w.sum()
        new = max(0.0, float(num / (w ** 2).sum()))
        if abs(new - tau2) < tol:
            return new
        tau2 = new
    return tau2


def eb_shrink(est: np.ndarray, var: np.ndarray, mu: float, tau2: float) -> np.ndarray:
    """Penyusutan ke mu dengan bobot τ²/(τ²+s²). τ²=0 -> semua kembali ke mu (temuan, bukan kegagalan)."""
    est, var = np.asarray(est, float), np.asarray(var, float)
    w = tau2 / (tau2 + var) if tau2 > 0 else np.zeros_like(est)
    return mu + w * (est - mu)


def bh_fdr(p: np.ndarray) -> np.ndarray:
    """q-value Benjamini-Hochberg."""
    p = np.asarray(p, float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(q, 0, 1)
    return out
