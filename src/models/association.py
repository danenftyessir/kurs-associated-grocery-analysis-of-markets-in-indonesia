"""Task 3 -- asosiasi profil respons dengan eksposur & karakteristik provinsi. docs/METHODS.md §M3.

(3a) kendall_exact, level komoditas N = 10 (WP-22); (3b) meta_regression, level provinsi (WP-23);
(3c) fe_interaction, robustness efek tetap komoditas x minggu (WP-24).
"""

from __future__ import annotations

from math import factorial

import numpy as np
import pandas as pd
from scipy import stats

from kagami.utils.config import Config
from kagami.utils.todo import todo

ASSOC_COLUMNS = ["level", "feature", "outcome", "estimate", "ci_low", "ci_high", "p_value", "method",
                 "jackknife_min", "jackknife_max"]
MAX_EXACT_N = 10          # 10! = 3.628.800 permutasi (int8 ~36 MB); di atas itu tidak dihitung eksak


def all_permutations(n: int) -> np.ndarray:
    """WP-22. Semua n! permutasi 0..n-1 sebagai array (n!, n) int8, dibangun dengan penyisipan (tanpa itertools)."""
    if n < 1 or n > MAX_EXACT_N:
        raise ValueError(f"permutasi eksak hanya untuk 1 <= n <= {MAX_EXACT_N} (n = {n})")
    P = np.zeros((1, 1), dtype=np.int8)
    for k in range(1, n):
        m = P.shape[0]
        out = np.empty((m * (k + 1), k + 1), dtype=np.int8)
        for pos in range(k + 1):
            blk = out[pos * m:(pos + 1) * m]
            blk[:, :pos] = P[:, :pos]
            blk[:, pos] = k
            blk[:, pos + 1:] = P[:, pos:]
        P = out
    return P


def _kendall_s(x: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Statistik S Kendall = Σ_{i<j} sign(x_i-x_j)·sign(y_i-y_j) untuk setiap baris Y (n_perm, n)."""
    n = len(x)
    S = np.zeros(Y.shape[0], dtype=np.int32)
    for i in range(n):
        for j in range(i + 1, n):
            sx = np.sign(x[i] - x[j])
            if sx != 0:
                S += (sx * np.sign(Y[:, i] - Y[:, j])).astype(np.int32)
    return S


def kendall_permutation_test(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """WP-22. τ-b Kendall + p permutasi EKSAK (semua n! urutan y; penyebut τ-b invarian → cukup S).

    Return tau, p_two_sided (#{|S*| >= |S|}/n!), p_greater (#{S* >= S}/n!), n, n_perm.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    tau = float(stats.kendalltau(x, y, variant="b").statistic) if n >= 2 else np.nan
    perms = all_permutations(n)
    S_perm = _kendall_s(x, y[perms])
    S_obs = int(_kendall_s(x, y[None, :])[0])
    eps = 1e-9
    return {"tau": tau, "p_two_sided": float(np.mean(np.abs(S_perm) >= abs(S_obs) - eps)),
            "p_greater": float(np.mean(S_perm >= S_obs - eps)), "n": n, "n_perm": factorial(n)}


def kendall_exact(cfg: Config, exposure: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """WP-22. Satu uji praregistrasi (E1, deskriptif): Kendall τ-b antara PT(8) nasional dan import_ratio_direct,
    p permutasi EKSAK (n! permutasi; n = 10 → 3.628.800), + leave-one-commodity-out (jackknife_min/max τ).

    Input : exposure (commodity, import_ratio_direct); features = response_features (level='national', PT8).
            Komoditas dengan nilai kosong dibuang (n dilaporkan).
    Output: satu baris artefak 'assoc' level='commodity', feature='import_ratio_direct', outcome='PT8',
            estimate = τ-b, p_value = p eksak dua sisi; interval = τ ± 1,96·SE jackknife (dipotong ke [-1, 1]).
            Kolom ekstra: n, p_greater (satu sisi, arah E1: impor langsung → PT(8) lebih besar), ci_method.
    Tulis kesimpulan sebagai "di antara 10 komoditas yang diamati".
    """
    nat = features.loc[features["level"] == "national", ["commodity", "PT8"]]
    d = exposure[["commodity", "import_ratio_direct"]].merge(nat, on="commodity", how="inner").dropna()
    d = d.sort_values("commodity").reset_index(drop=True)
    x, y = d["import_ratio_direct"].to_numpy(float), d["PT8"].to_numpy(float)
    res = kendall_permutation_test(x, y)
    n = res["n"]
    loo = np.array([stats.kendalltau(np.delete(x, i), np.delete(y, i), variant="b").statistic for i in range(n)])
    se_j = float(np.sqrt((n - 1) / n * np.sum((loo - loo.mean()) ** 2))) if n > 2 else np.nan
    return pd.DataFrame([{
        "level": "commodity", "feature": "import_ratio_direct", "outcome": "PT8", "estimate": res["tau"],
        "ci_low": max(-1.0, res["tau"] - 1.96 * se_j), "ci_high": min(1.0, res["tau"] + 1.96 * se_j),
        "p_value": res["p_two_sided"], "method": "kendall_tau_b_exact_permutation",
        "jackknife_min": float(np.nanmin(loo)), "jackknife_max": float(np.nanmax(loo)),
        "n": n, "p_greater": res["p_greater"], "ci_method": "jackknife_loco",
    }], columns=ASSOC_COLUMNS + ["n", "p_greater", "ci_method"])


def meta_regression(cfg: Config, profiles: pd.DataFrame, boot: pd.DataFrame,
                    province_features: pd.DataFrame) -> pd.DataFrame:
    """WP-23. Meta-regresi efek acak pada deviasi δ(i,r,h) TANPA susut, maks 3 fitur praregistrasi:
    ln_dist_hub, rice_sufficiency (bila tersedia), n_kota (kontrol desain). H3: koefisien ln_dist_hub pada h=4 < 0
    (satu arah); h=12 dua arah.
    Interval: bootstrap blok mingguan (boot_replicates) DAN SE cluster provinsi CR2 -> laporkan yang lebih lebar.
    Jackknife per provinsi -> jackknife_min/max. -> baris 'assoc' level='province'.
    """
    todo("WP-23")


def fe_interaction(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                   province_features: pd.DataFrame) -> pd.DataFrame:
    """WP-24. (3c) Panel dengan efek tetap komoditas x minggu; koefisien interaksi de x Z(r)
    diidentifikasi hanya dari perbedaan antarprovinsi. -> baris 'assoc' method='fe_interaction'.
    Dipotong pertama bila waktu habis (urutan pemotongan, D-014).
    """
    todo("WP-24")
