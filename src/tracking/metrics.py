"""WP-36. Metrik generik berpenjaga. Setiap fungsi mengembalikan list[Metric]; metrik yang syaratnya tidak terpenuhi
diberi status `not_applicable` + alasan, galat hitung = `failed` + alasan. Tidak ada nilai yang dikarang (D-137).

Penjaga:
- clustering: silhouette / Davies-Bouldin / Calinski-Harabasz hanya bila 2 ≤ k ≤ n − 1 dan matriks tanpa NaN.
- regresi: pasangan NaN dibuang (jumlahnya dicatat); MAPE tidak berlaku bila ada |y| < eps (pembagian nol).
- konsistensi p–interval: p < α ⇔ interval tidak memuat nol (pelajaran U106).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score

from kagami.tracking.schemas import Metric

MAPE_EPS = 1e-12


def ok(name: str, value: Any, group: str, **context: Any) -> Metric:
    """Metrik berhasil; nilai NaN/inf otomatis menjadi `failed` (bukan angka yang dilaporkan)."""
    if isinstance(value, (float, np.floating)) and not math.isfinite(float(value)):
        return Metric(name, group, None, "failed", "nilai tidak terhingga / NaN", context)
    if isinstance(value, np.generic):
        value = value.item()
    return Metric(name, group, value, "ok", None, context)


def na(name: str, group: str, reason: str, **context: Any) -> Metric:
    return Metric(name, group, None, "not_applicable", reason, context)


def failed(name: str, group: str, reason: str, **context: Any) -> Metric:
    return Metric(name, group, None, "failed", reason, context)


def clustering_metrics(X: np.ndarray, labels: np.ndarray, group: str = "clustering", **context: Any) -> list[Metric]:
    """Validitas internal satu partisi: n_clusters, ukuran klaster, WCSS (inertia Ward/K-Means), silhouette,
    Davies-Bouldin, Calinski-Harabasz (Euclidean). Konteks dicatat di setiap metrik."""
    X = np.asarray(X, float)
    labels = np.asarray(labels)
    ctx = {"n_samples": int(len(X)), "n_features": int(X.shape[1]) if X.ndim == 2 else None, **context}
    if X.ndim != 2 or len(X) != len(labels):
        return [failed("n_clusters", group, "bentuk matriks dan label tidak cocok", **ctx)]
    uniq, sizes = np.unique(labels, return_counts=True)
    k, n = len(uniq), len(X)
    out = [ok("n_clusters", int(k), group, **ctx), ok("cluster_sizes", [int(s) for s in sizes], group, **ctx)]
    if np.isnan(X).any():
        reason = "matriks fitur memuat NaN"
        return out + [failed(m, group, reason, **ctx) for m in ("wcss", "silhouette", "davies_bouldin",
                                                                  "calinski_harabasz")]
    centers = np.vstack([X[labels == u].mean(axis=0) for u in uniq])
    wcss = float(sum(((X[labels == u] - centers[i]) ** 2).sum() for i, u in enumerate(uniq)))
    out.append(ok("wcss", wcss, group, **ctx))
    if k < 2:
        reason = "k = 1: silhouette/DB/CH tidak terdefinisi untuk satu klaster"
    elif k > n - 1:
        reason = f"k = {k} ≥ jumlah sampel {n}: setiap titik klaster sendiri"
    else:
        reason = None
    if reason:
        return out + [na(m, group, reason, **ctx) for m in ("silhouette", "davies_bouldin", "calinski_harabasz")]
    for name, fn in (("silhouette", lambda: silhouette_score(X, labels, metric="euclidean")),
                     ("davies_bouldin", lambda: davies_bouldin_score(X, labels)),
                     ("calinski_harabasz", lambda: calinski_harabasz_score(X, labels))):
        try:
            out.append(ok(name, float(fn()), group, **ctx))
        except Exception as exc:  # noqa: BLE001
            out.append(failed(name, group, f"{type(exc).__name__}: {exc}", **ctx))
    return out


def regression_metrics(y_true, y_pred, group: str = "regression", prefix: str = "", **context: Any) -> list[Metric]:
    """MAE, MSE, RMSE, R² (terhadap rerata y uji), R² out-of-sample terhadap ramalan nol (1 − SSE/Σy²), MAPE.

    Dipakai hanya pada pasangan (y_true, y_pred) out-of-sample yang sudah dipisah oleh pemanggil.
    """
    yt = np.asarray(y_true, float)
    yp = np.asarray(y_pred, float)
    if yt.shape != yp.shape:
        return [failed(f"{prefix}mae", group, f"panjang y_true {yt.shape} ≠ y_pred {yp.shape}", **context)]
    keep = np.isfinite(yt) & np.isfinite(yp)
    ctx = {"n": int(keep.sum()), "n_dropped_nan": int((~keep).sum()), **context}
    yt, yp = yt[keep], yp[keep]
    names = ("mae", "mse", "rmse", "r2", "r2_oos_vs_zero", "mape")
    if len(yt) < 2:
        return [na(prefix + m, group, "kurang dari 2 pasangan teramati", **ctx) for m in names]
    e = yt - yp
    mse = float(np.mean(e ** 2))
    sst = float(np.sum((yt - yt.mean()) ** 2))
    s0 = float(np.sum(yt ** 2))
    out = [ok(prefix + "mae", float(np.mean(np.abs(e))), group, **ctx), ok(prefix + "mse", mse, group, **ctx),
           ok(prefix + "rmse", math.sqrt(mse), group, **ctx)]
    out.append(ok(prefix + "r2", 1 - float(np.sum(e ** 2)) / sst, group, **ctx) if sst > 0 else
               na(prefix + "r2", group, "varians y_true nol", **ctx))
    out.append(ok(prefix + "r2_oos_vs_zero", 1 - float(np.sum(e ** 2)) / s0, group, **ctx) if s0 > 0 else
               na(prefix + "r2_oos_vs_zero", group, "semua y_true nol", **ctx))
    n_zero = int((np.abs(yt) < MAPE_EPS).sum())
    if n_zero:
        out.append(na(prefix + "mape", group, f"{n_zero} dari {len(yt)} y_true = 0 (selisih log tanpa perubahan harga) "
                      "→ persentase galat tak terdefinisi", **ctx))
    else:
        out.append(ok(prefix + "mape", float(np.mean(np.abs(e / yt))) * 100, group, **ctx))
    return out


def data_profile(df: pd.DataFrame) -> dict[str, Any]:
    """Ukuran dataset untuk ArtifactRef: baris, kolom, sel kosong, memori (MB)."""
    return {"rows": int(len(df)), "columns": int(df.shape[1]), "missing_cells": int(df.isna().sum().sum()),
            "memory_mb": round(float(df.memory_usage(deep=True).sum()) / 2 ** 20, 3)}


def interval_consistency(df: pd.DataFrame, group: str, p_col: str = "p_value", lo: str = "ci_low", hi: str = "ci_high",
                         alpha: float = 0.05, name: str = "p_interval_consistency", **context: Any) -> list[Metric]:
    """Porsi baris dengan (p < α) ⇔ (interval tidak memuat nol) + jumlah yang tidak konsisten."""
    if df is None or df.empty or not {p_col, lo, hi} <= set(df.columns):
        return [na(name, group, f"kolom {p_col}/{lo}/{hi} tidak tersedia", **context)]
    d = df[[p_col, lo, hi]].dropna()
    if d.empty:
        return [na(name, group, "semua baris memuat NaN pada p atau interval", **context)]
    sig = d[p_col] < alpha
    excl = (d[lo] > 0) | (d[hi] < 0)
    agree = sig == excl
    ctx = {"n": int(len(d)), "alpha": alpha, **context}
    return [ok(name, float(agree.mean()), group, **ctx), ok(name + "_mismatches", int((~agree).sum()), group, **ctx)]


def share(mask: pd.Series) -> float:
    """Porsi True dari Series boolean (NaN dibuang); NaN bila kosong."""
    m = mask.dropna()
    return float(m.mean()) if len(m) else float("nan")
