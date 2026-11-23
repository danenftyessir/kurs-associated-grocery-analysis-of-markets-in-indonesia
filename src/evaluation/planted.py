"""Uji pemulihan struktur tertanam (WP-21) -- batas deteksi struktur regional. docs/METHODS.md §M2 langkah 5."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, silhouette_score

from kagami.features.clustering import feature_columns
from kagami.stats.meta import dersimonian_laird, eb_shrink
from kagami.utils.config import Config

K_TRUE = (2, 3)              # jumlah kelompok buatan (proposal §5.3 langkah 5, WORKPLAN WP-21)
RECOVERY_ARI = 0.8           # ambang ARI "ditemukan kembali" (METHODS §M2 langkah 5)
DETECTION_RATE = 0.8         # recovery_rate minimum untuk "batas deteksi" (WORKPLAN WP-21)
PLANTED_COLUMNS = ["delta", "k_true", "recovery_rate", "ari_mean"]
_SEED_OFFSET = 2101          # rng = default_rng(seed + 2101)
_DRIVER = {"R": "e", "W": "w"}


def _zscore(X: np.ndarray) -> np.ndarray:
    """z-score per kolom; kolom tanpa variasi -> 0 (identik untuk asli, plasebo & tertanam)."""
    X = np.asarray(X, float)
    sd = X.std(axis=0)
    return np.where(sd > 0, (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0), 0.0)


def deviation_matrices(cfg: Config, replicates: pd.DataFrame) -> list[tuple[np.ndarray, np.ndarray]]:
    """WP-21. placebo_stats -> per `rep` pasangan (D, S): deviasi provinsi MENTAH (belum tersusut) dan SE-nya.

    Baris = province_id 1..34 (urutan menaik, provinsi tanpa nilai = NaN), kolom = features.clustering.feature_columns
    (R -> driver e, W -> driver w, h di params.clustering.feature_horizons). Kolom `se` wajib (D-111)."""
    prov = replicates[replicates["level"] == "province"]
    if "se" not in prov.columns:
        raise KeyError("replikasi provinsi harus membawa kolom `se` (WP-16, D-111)")
    keys = pd.MultiIndex.from_tuples([(com, _DRIVER[prefix], int(h)) for prefix, com, h in feature_columns(cfg)])
    prov = prov.assign(pid=prov["unit"].astype(int), horizon=prov["horizon"].astype(int))
    ids = sorted(prov["pid"].unique())
    out = []
    for _, g in prov.groupby("rep", sort=True):
        w = g.pivot_table(index="pid", columns=["commodity", "driver", "horizon"], values=["estimate", "se"],
                          aggfunc="first")
        D = w["estimate"].reindex(index=ids, columns=keys).to_numpy(float)
        S = w["se"].reindex(index=ids, columns=keys).to_numpy(float)
        out.append((D, S))
    return out


def shrink_matrix(D: np.ndarray, S: np.ndarray) -> np.ndarray:
    """WP-21. Penyusutan EB per kolom seperti features.response.shrink_deviations (τ² DL, eb_shrink; sel tanpa se > 0
    atau kolom dengan < 2 provinsi valid dilewati), lalu sel kosong = rerata kolom (0 bila kolom kosong), seperti
    features.clustering. Hasil dalam satuan respons, siap di-z-score."""
    D, S = np.asarray(D, float), np.asarray(S, float)
    X = np.full_like(D, np.nan)
    for j in range(D.shape[1]):
        ok = np.isfinite(D[:, j]) & np.isfinite(S[:, j]) & (S[:, j] > 0)
        if ok.sum() < 2:
            continue
        est, var = D[ok, j], S[ok, j] ** 2
        het = dersimonian_laird(est, var)
        X[ok, j] = eb_shrink(est, var, het.mu, het.tau2)
    fin = np.isfinite(X)
    n = fin.sum(axis=0)
    mean = np.where(n > 0, np.where(fin, X, 0.0).sum(axis=0) / np.maximum(n, 1), 0.0)
    return np.where(fin, X, mean)


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
    (terstandardisasi) -- aturan yang sama dengan select_k (METHODS §M2 langkah 3)."""
    p = cfg.params["clustering"]
    ks = [int(k) for k in p["k_range"] if int(k) >= 2]
    s = np.array([best_silhouette(X, ks, ward)[1] for X in placebo_std])
    return float(np.nanpercentile(s, float(p["silhouette_placebo_pct"])))


def plant_structure(X_raw: np.ndarray, k_true: int, delta: float, rng: np.random.Generator
                    ) -> tuple[np.ndarray, np.ndarray]:
    """WP-21. Bagi baris (provinsi) acak ke k_true kelompok berukuran hampir sama dan geser tiap kelompok ke pusatnya.

    Pusat kelompok = simpleks beraturan berorientasi acak di ruang F fitur (satuan respons, sebelum penyusutan &
    standardisasi): setiap PASANGAN kelompok berjarak δ·√F, yaitu selisih respons RMS per fitur = δ (D-112). Untuk
    k = 2 setara dengan selisih δ di arah acak; untuk k = 3 kelompok tidak segaris. Return (X tertanam, label benar)."""
    X = np.asarray(X_raw, float)
    n, F = X.shape
    if F < k_true:
        raise ValueError(f"butuh jumlah fitur >= k_true ({F} < {k_true})")
    labels = np.empty(n, dtype=int)
    labels[rng.permutation(n)] = np.arange(n) % k_true
    Q, _ = np.linalg.qr(rng.normal(size=(F, k_true)))          # kolom ortonormal
    centers = delta * np.sqrt(F / 2) * Q.T                     # ||c_i - c_j|| = δ·√F
    return X + centers[labels], labels


def recovery_curve(cfg: Config, placebo_dev: list[tuple[np.ndarray, np.ndarray]], *,
                   ward: Callable[[np.ndarray, int], np.ndarray] | None = None,
                   reps: int | None = None) -> pd.DataFrame:
    """WP-21. Batas deteksi struktur regional (METHODS §M2 langkah 5, D-112, D-126).

    placebo_dev: per replikasi plasebo pasangan (D, S) = deviasi provinsi MENTAH & SE-nya (deviation_matrices).
    Untuk δ ∈ params.clustering.planted_deltas, k_true ∈ K_TRUE, planted_reps kali: ambil satu replikasi plasebo acak,
    tanam kelompok pada D (plant_structure), lalu proses PERSIS seperti data asli: susut EB per kolom dengan S
    (shrink_matrix), z-score, aturan langkah 2-3: k terpilih = argmax silhouette Ward bila maks > ambang plasebo
    (placebo_threshold dari semua replikasi plasebo yang diproses sama tanpa penanaman), selain itu k = 1.
    Menanam SETELAH penyusutan (versi sebelum D-126) membuat derau plasebo ≈ 0 pada kolom τ² = 0 sehingga δ kecil pun
    terdeteksi (U105).
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
    dev = [(np.asarray(D, float), np.asarray(S, float)) for D, S in placebo_dev]
    if not dev:
        raise ValueError("recovery_curve butuh minimal satu replikasi plasebo")
    thr = placebo_threshold(cfg, [_zscore(shrink_matrix(D, S)) for D, S in dev], ward)
    rng = np.random.default_rng(cfg.seed + _SEED_OFFSET)
    rows = []
    for delta in [float(d) for d in p["planted_deltas"]]:
        for k_true in K_TRUE:
            hit = np.zeros(R, bool)
            kok = np.zeros(R, bool)
            ari = np.zeros(R)
            for r in range(R):
                D, S = dev[int(rng.integers(len(dev)))]
                Dp, truth = plant_structure(D, k_true, delta, rng)
                Z = _zscore(shrink_matrix(Dp, S))
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
