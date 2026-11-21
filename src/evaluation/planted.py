"""Uji pemulihan struktur tertanam (WP-21) -- batas deteksi struktur regional. docs/METHODS.md §M2.5."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, silhouette_score

from kagami.utils.config import Config

K_TRUE = (2, 3)              # jumlah kelompok buatan (proposal §5.3 langkah 5, WORKPLAN WP-21)
RECOVERY_ARI = 0.8           # ambang ARI "ditemukan kembali" (METHODS §M2.5)
DETECTION_RATE = 0.8         # recovery_rate minimum untuk "batas deteksi" (WORKPLAN WP-21)
PLANTED_COLUMNS = ["delta", "k_true", "recovery_rate", "ari_mean"]
_SEED_OFFSET = 2101          # rng = default_rng(seed + 2101)


def _zscore(X: np.ndarray) -> np.ndarray:
    """z-score per kolom; kolom tanpa variasi -> 0 (identik untuk asli, plasebo & tertanam)."""
    X = np.asarray(X, float)
    sd = X.std(axis=0)
    return np.where(sd > 0, (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0), 0.0)


def best_silhouette(X: np.ndarray, ks: list[int], ward: Callable[[np.ndarray, int], np.ndarray]
                    ) -> tuple[int, float]:
    """WP-21. (k*, s*) = argmax/max silhouette Euclidean Ward atas k ∈ ks (k ≥ 2); s* = NaN bila tak terhitung."""
    best_k, best_s = 1, -np.inf
    for k in ks:
        if k < 2 or k >= len(X):
            continue
        lab = ward(X, k)
        if len(np.unique(lab)) < 2:
            continue
        s = silhouette_score(X, lab, metric="euclidean")
        if s > best_s:
            best_k, best_s = k, float(s)
    return (best_k, best_s) if np.isfinite(best_s) else (1, np.nan)


def placebo_threshold(cfg: Config, placebo_std: list[np.ndarray],
                      ward: Callable[[np.ndarray, int], np.ndarray]) -> float:
    """WP-21. Persentil params.clustering.silhouette_placebo_pct dari silhouette MAKSIMUM tiap matriks plasebo
    (terstandardisasi) -- aturan yang sama dengan select_k (METHODS §M2.3)."""
    p = cfg.params["clustering"]
    ks = [int(k) for k in p["k_range"] if int(k) >= 2]
    s = np.array([best_silhouette(X, ks, ward)[1] for X in placebo_std])
    return float(np.nanpercentile(s, float(p["silhouette_placebo_pct"])))


def plant_structure(X_raw: np.ndarray, k_true: int, delta: float, rng: np.random.Generator
                    ) -> tuple[np.ndarray, np.ndarray]:
    """WP-21. Bagi baris (provinsi) acak ke k_true kelompok berukuran hampir sama dan geser tiap kelompok ke pusatnya.

    Pusat kelompok = simpleks beraturan berorientasi acak di ruang F fitur (satuan respons, sebelum standardisasi):
    setiap PASANGAN kelompok berjarak δ·√F, yaitu selisih respons RMS per fitur = δ (D-112). Untuk k = 2 setara
    dengan selisih δ di arah acak; untuk k = 3 kelompok tidak segaris. Return (X tertanam, label benar)."""
    X = np.asarray(X_raw, float)
    n, F = X.shape
    if F < k_true:
        raise ValueError(f"butuh jumlah fitur >= k_true ({F} < {k_true})")
    labels = np.empty(n, dtype=int)
    labels[rng.permutation(n)] = np.arange(n) % k_true
    Q, _ = np.linalg.qr(rng.normal(size=(F, k_true)))          # kolom ortonormal
    centers = delta * np.sqrt(F / 2) * Q.T                     # ||c_i - c_j|| = δ·√F
    return X + centers[labels], labels


def recovery_curve(cfg: Config, placebo_X: list[np.ndarray], *,
                   ward: Callable[[np.ndarray, int], np.ndarray] | None = None,
                   reps: int | None = None) -> pd.DataFrame:
    """WP-21. Batas deteksi struktur regional (METHODS §M2.5, D-112).

    placebo_X: matriks fitur provinsi per replikasi plasebo, BELUM distandardisasi (satuan respons, sama dengan
               feature_matrix sebelum z-score) -- replicate_feature_matrices(..., standardize=False).
    Untuk δ ∈ params.clustering.planted_deltas, k_true ∈ K_TRUE, planted_reps kali: ambil satu matriks plasebo acak,
    tanam kelompok (plant_structure), z-score, lalu jalankan aturan langkah 2-3: k terpilih = argmax silhouette
    Ward bila maks > ambang plasebo (placebo_threshold dari semua matriks plasebo), selain itu k = 1.
    recovery_rate = P(k terpilih == k_true dan ARI >= 0,8); ari_mean = rerata ARI label Ward(k_true) vs label benar
    (ukuran pemisahan, tidak bergantung pada pemilihan k).
    ward : fungsi (X, k) -> label; default models.clustering.ward_labels (WP-19).
    reps : override planted_reps (uji cepat). RNG: seed + 2101.
    Output: artefak 'planted_recovery' + n_reps, k_correct_rate, threshold.
    """
    if ward is None:
        from kagami.models.clustering import ward_labels as ward
    p = cfg.params["clustering"]
    ks = [int(k) for k in p["k_range"] if int(k) >= 2]
    R = int(reps if reps is not None else p["planted_reps"])
    raw = [np.asarray(X, float) for X in placebo_X]
    if not raw:
        raise ValueError("recovery_curve butuh minimal satu matriks plasebo")
    thr = placebo_threshold(cfg, [_zscore(X) for X in raw], ward)
    rng = np.random.default_rng(cfg.seed + _SEED_OFFSET)
    rows = []
    for delta in [float(d) for d in p["planted_deltas"]]:
        for k_true in K_TRUE:
            hit = np.zeros(R, bool)
            kok = np.zeros(R, bool)
            ari = np.zeros(R)
            for r in range(R):
                base = raw[int(rng.integers(len(raw)))]
                Xp, truth = plant_structure(base, k_true, delta, rng)
                Z = _zscore(Xp)
                k_star, s_star = best_silhouette(Z, ks, ward)
                k_sel = k_star if np.isfinite(s_star) and s_star > thr else 1
                ari[r] = adjusted_rand_score(truth, ward(Z, k_true))
                kok[r] = k_sel == k_true
                hit[r] = kok[r] and ari[r] >= RECOVERY_ARI      # k benar -> label terpilih = Ward(k_true)
            rows.append({"delta": delta, "k_true": k_true, "recovery_rate": hit.mean(), "ari_mean": ari.mean(),
                         "n_reps": R, "k_correct_rate": kok.mean(), "threshold": thr})
    return pd.DataFrame(rows, columns=PLANTED_COLUMNS + ["n_reps", "k_correct_rate", "threshold"])


def detection_limit(planted: pd.DataFrame) -> pd.DataFrame:
    """WP-21. δ terkecil dengan recovery_rate >= 0,8 per k_true (NaN bila tidak tercapai) -> "batas deteksi" findings."""
    out = []
    for k, g in planted.groupby("k_true"):
        ok = g.loc[g["recovery_rate"] >= DETECTION_RATE, "delta"]
        out.append({"k_true": k, "delta_min": float(ok.min()) if len(ok) else np.nan})
    return pd.DataFrame(out)
