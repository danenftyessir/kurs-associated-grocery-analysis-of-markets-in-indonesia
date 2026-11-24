"""WP-36. Metrik generik berpenjaga. Setiap fungsi mengembalikan list[Metric]; metrik yang syaratnya tidak terpenuhi
diberi status `not_applicable` + alasan, galat hitung = `failed` + alasan. Tidak ada nilai yang dikarang (D-137).

Penjaga:
- clustering: silhouette / Davies-Bouldin / Calinski-Harabasz hanya bila 2 ≤ k ≤ n − 1 dan matriks tanpa NaN.
- regresi: pasangan NaN dibuang (jumlahnya dicatat); MAPE tidak berlaku bila ada |y| < eps (pembagian nol).
- konsistensi p–interval: p < α ⇔ interval tidak memuat nol (pelajaran U106).
- arah perubahan (D-139): hanya pasangan y_true ≠ 0 dan y_pred ≠ 0; MCC/AUC/balanced accuracy tidak berlaku bila satu kelas.
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


DIRECTION_CLASSES = ("naik", "turun")


def direction_metrics(y_true, y_pred, group: str = "arah perubahan", prefix: str = "", **context: Any) -> list[Metric]:
    """Diagnostik klasifikasi arah dari ramalan regresi (D-139): kelas = tanda y (naik > 0, turun < 0).

    Dikeluarkan (jumlahnya dicatat di konteks): y_true = 0 (harga tidak berubah, ± 9–15% target Task 4; kelas "tetap" butuh
    ambang toleransi yang tidak ada di praregistrasi, dan ramalan regresi hampir tidak pernah tepat 0) dan y_pred = 0
    (ramalan tanpa arah). Model yang semua ramalannya 0 (M0) → tidak berlaku.
    Metrik: accuracy, akurasi baseline kelas mayoritas (pembanding), balanced accuracy, precision/recall/F1 per kelas,
    F1 makro, MCC, ROC-AUC & PR-AUC (skor = y_pred, positif = naik), confusion matrix [[naik→naik, naik→turun],
    [turun→naik, turun→turun]] (baris = aktual, kolom = ramalan).
    """
    from sklearn.metrics import average_precision_score, roc_auc_score

    yt = np.asarray(y_true, float)
    yp = np.asarray(y_pred, float)
    names = ["accuracy", "majority_baseline_accuracy", "balanced_accuracy", "precision_naik", "recall_naik", "f1_naik",
             "precision_turun", "recall_turun", "f1_turun", "f1_macro", "mcc", "f1_weighted", "accuracy_incl_no_change",
             "coverage", "roc_auc", "pr_auc", "confusion"]
    full = [f"{prefix}dir_{n}" for n in names]
    if yt.shape != yp.shape:
        return [failed(full[0], group, f"panjang y_true {yt.shape} ≠ y_pred {yp.shape}", **context)]
    fin = np.isfinite(yt) & np.isfinite(yp)
    t_zero, p_zero = np.abs(yt) < MAPE_EPS, yp == 0
    keep = fin & ~t_zero & ~p_zero
    ctx = {"n": int(keep.sum()), "n_no_change_excluded": int((fin & t_zero).sum()),
           "n_pred_no_direction_excluded": int((fin & ~t_zero & p_zero).sum()), **context}
    if fin.any() and (p_zero[fin]).all():
        return [na(m, group, "model tidak memberi arah (semua ramalan = 0, mis. M0)", **ctx) for m in full]
    yt, yp = yt[keep], yp[keep]
    if len(yt) < 2:
        return [na(m, group, "kurang dari 2 pasangan dengan perubahan harga dan ramalan berarah", **ctx) for m in full]
    up_t, up_p = yt > 0, yp > 0
    tp = int((up_t & up_p).sum())      # naik → naik
    fn = int((up_t & ~up_p).sum())     # naik → turun
    fp = int((~up_t & up_p).sum())     # turun → naik
    tn = int((~up_t & ~up_p).sum())    # turun → turun
    n, n_up, n_dn = len(yt), tp + fn, fp + tn
    ctx["share_naik"] = round(n_up / n, 4)

    def ratio(a: int, b: int) -> float:
        return a / b if b else float("nan")

    vals = {"accuracy": (tp + tn) / n, "majority_baseline_accuracy": max(n_up, n_dn) / n,
            "precision_naik": ratio(tp, tp + fp), "recall_naik": ratio(tp, n_up), "f1_naik": ratio(2 * tp, 2 * tp + fp + fn),
            "precision_turun": ratio(tn, tn + fn), "recall_turun": ratio(tn, n_dn),
            "f1_turun": ratio(2 * tn, 2 * tn + fn + fp)}
    vals["balanced_accuracy"] = (vals["recall_naik"] + vals["recall_turun"]) / 2
    vals["f1_macro"] = (vals["f1_naik"] + vals["f1_turun"]) / 2
    den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    vals["mcc"] = (tp * tn - fp * fn) / den if den > 0 else float("nan")
    # D-144: F1 berbobot proporsi kelas; akurasi bila perubahan nol dihitung sebagai salah (ramalan selalu berarah);
    # cakupan = porsi baris berhingga yang masuk evaluasi arah (F1 & akurasi di atas hanya untuk baris ini)
    vals["f1_weighted"] = (n_up * vals["f1_naik"] + n_dn * vals["f1_turun"]) / n
    vals["accuracy_incl_no_change"] = (tp + tn) / (n + ctx["n_no_change_excluded"])
    vals["coverage"] = n / int(fin.sum()) if fin.sum() else float("nan")
    one_class = n_up == 0 or n_dn == 0
    if one_class:   # metrik dua-kelas & metrik kelas yang tidak ada di y_true tidak bermakna (F1 = 0 bukan informasi)
        absent = "turun" if n_dn == 0 else "naik"
        for k in ("balanced_accuracy", "f1_macro", "f1_weighted", "mcc", f"precision_{absent}", f"recall_{absent}",
                  f"f1_{absent}"):
            vals[k] = float("nan")
    out = []
    for key in names[:-3]:
        v = vals[key]
        out.append(ok(f"{prefix}dir_{key}", float(v), group, **ctx) if math.isfinite(v) else
                   na(f"{prefix}dir_{key}", group, "y_true hanya memuat satu arah" if one_class else
                      "penyebut nol (kelas tidak pernah diramalkan)", **ctx))
    if one_class:
        out += [na(f"{prefix}dir_{k}", group, "y_true hanya memuat satu arah", **ctx) for k in ("roc_auc", "pr_auc")]
    else:
        out += [ok(f"{prefix}dir_roc_auc", float(roc_auc_score(up_t, yp)), group, **ctx),
                ok(f"{prefix}dir_pr_auc", float(average_precision_score(up_t, yp)), group, **ctx)]
    out.append(ok(f"{prefix}dir_confusion", [[tp, fn], [fp, tn]], group, labels=list(DIRECTION_CLASSES),
                  layout="baris = aktual (naik, turun), kolom = ramalan (naik, turun)", **ctx))
    return out


DIR_BOOT_REPS = 999          # replikasi bootstrap blok origin untuk interval metrik arah (D-140; bukan parameter analisis)


def _confusion_stats(S: np.ndarray) -> dict[str, np.ndarray]:
    """Statistik arah dari jumlah confusion S[..., 4] = (tp, fn, fp, tn) (baris = replikasi bootstrap)."""
    tp, fn, fp, tn = (np.asarray(S[..., i], float) for i in range(4))
    n, n_up, n_dn = tp + fn + fp + tn, tp + fn, fp + tn
    with np.errstate(divide="ignore", invalid="ignore"):
        acc = (tp + tn) / n
        base = np.maximum(n_up, n_dn) / n
        rec_up, rec_dn = tp / n_up, tn / n_dn
        f1_up, f1_dn = 2 * tp / (2 * tp + fp + fn), 2 * tn / (2 * tn + fn + fp)
        mcc = (tp * tn - fp * fn) / np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return {"accuracy": acc, "majority_baseline_accuracy": base, "accuracy_gap": acc - base,
            "balanced_accuracy": (rec_up + rec_dn) / 2, "f1_macro": (f1_up + f1_dn) / 2, "mcc": mcc,
            "recall_naik": rec_up, "recall_turun": rec_dn}


def _pct_ci(v: np.ndarray) -> tuple[float, float] | None:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else None


def bootstrap_p(v: np.ndarray, ref: float) -> float | None:
    """p dua sisi bootstrap persentil terhadap nilai acuan (D-143): 2·min(P*(stat ≤ ref), P*(stat ≥ ref)) dengan koreksi
    +1/(B+1); konsisten dengan interval persentil 95% (interval tidak memuat acuan ⇔ p < 0,05, kurang lebih)."""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if not len(v) or ref is None or not np.isfinite(ref):
        return None
    b = len(v)
    lo, hi = (np.sum(v <= ref) + 1) / (b + 1), (np.sum(v >= ref) + 1) / (b + 1)
    return float(min(1.0, 2 * min(lo, hi)))


def origin_block_indices(n_origins: int, block: int, reps: int, rng: np.random.Generator) -> np.ndarray:
    """Matriks indeks (reps × n_origins) bootstrap blok bergerak atas origin berurutan (Künsch). Blok menjaga
    ketergantungan origin yang bertumpuk (h > langkah origin); semua seri dalam satu origin ikut terambil bersama."""
    from kagami.stats.resampling import moving_block_indices

    return np.vstack([moving_block_indices(n_origins, block, rng) for _ in range(reps)])


def _direction_cells(yt: np.ndarray, yp: np.ndarray) -> np.ndarray:
    up_t, up_p = yt > 0, yp > 0
    return np.stack([up_t & up_p, up_t & ~up_p, ~up_t & up_p, ~up_t & ~up_p], axis=1).astype(float)


def direction_bootstrap(y_true, y_pred, origin, block: int, reps: int = DIR_BOOT_REPS, seed: int = 0,
                        ranking: bool = True) -> dict[str, Any] | None:
    """Interval 95% persentil metrik arah dengan bootstrap blok origin (D-140): accuracy, selisih accuracy − baseline kelas
    mayoritas (baseline dihitung ulang pada sampel bootstrap yang sama), balanced accuracy, F1 makro, MCC, dan (ranking)
    ROC-AUC & PR-AUC. Eksklusi sama dengan `direction_metrics` (y_true = 0 dan y_pred = 0 dibuang).

    Unit resampling = origin, bukan baris: seri dalam satu origin berbagi guncangan nasional, jadi n baris melebih-lebihkan
    informasi. Hasil: dict nama → (lo, hi) + n_origins, block, reps; None bila < 3 origin, satu kelas, atau M0.
    """
    yt, yp, o = np.asarray(y_true, float), np.asarray(y_pred, float), np.asarray(origin)
    keep = np.isfinite(yt) & np.isfinite(yp) & (np.abs(yt) >= MAPE_EPS) & (yp != 0)
    yt, yp, o = yt[keep], yp[keep], o[keep]
    uo, inv = np.unique(o, return_inverse=True)
    up_t = yt > 0
    if len(uo) < 3 or up_t.all() or (~up_t).all():
        return None
    C = np.zeros((len(uo), 4))
    np.add.at(C, inv, _direction_cells(yt, yp))
    idx = origin_block_indices(len(uo), block, reps, np.random.default_rng(seed))
    stats = _confusion_stats(C[idx].sum(axis=1))
    out: dict[str, Any] = {"n_origins": int(len(uo)), "block": int(block), "reps": int(reps)}
    refs = {"accuracy_gap": 0.0, "balanced_accuracy": 0.5, "f1_macro": 0.5, "mcc": 0.0}
    for k in ("accuracy", "accuracy_gap", "balanced_accuracy", "f1_macro", "mcc"):
        out[k] = _pct_ci(stats[k])
        if k in refs:
            out[f"{k}_p"] = bootstrap_p(stats[k], refs[k])
    if ranking:
        # Urutan skor global dihitung sekali; replikasi = bobot frekuensi origin (berapa kali origin terambil), jadi
        # AUC & AP berbobot dihitung dengan cumsum tanpa mengurutkan ulang (setara mengulang baris sesuai bobot).
        order = np.argsort(-yp, kind="stable")
        pos_sorted, inv_sorted = up_t[order], inv[order]
        aucs, aps = [], []
        for r in idx:
            w = np.bincount(r, minlength=len(uo))[inv_sorted].astype(float)
            wp, wn = w * pos_sorted, w * ~pos_sorted
            P, N = wp.sum(), wn.sum()
            if P == 0 or N == 0:
                continue
            ctp, cfp = np.cumsum(wp), np.cumsum(wn)
            aucs.append(float(np.sum(wp * (N - cfp)) / (P * N)))       # P(skor positif > skor negatif), tanpa ikatan
            prec = ctp / np.maximum(ctp + cfp, 1e-12)
            aps.append(float(np.sum(prec * wp) / P))
        out["roc_auc"], out["pr_auc"] = _pct_ci(np.array(aucs)), _pct_ci(np.array(aps))
        out["roc_auc_p"] = bootstrap_p(np.array(aucs), 0.5)
        out["pr_auc_p"] = bootstrap_p(np.array(aps), float(up_t.mean()))
    return out


def direction_segment_table(df: pd.DataFrame, segments: dict[str, dict[str, Any]], models: list[str], block: int,
                            reps: int = DIR_BOOT_REPS, seed: int = 0,
                            no_mae: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    """Metrik arah & MAE per segmen (D-140). df = forecast_preds satu horizon (origin, model, y_true, y_pred, ...);
    segments = {jenis segmen: {nama: mask boolean sepanjang df}}. Per (segmen, model): n, accuracy, baseline mayoritas,
    selisih + interval bootstrap blok origin, balanced accuracy (+ interval), F1 makro, recall naik/turun, MCC, MAE,
    MAE / MAE M1. Penilaian: interval selisih di atas nol = better, di bawah nol = worse, selain itu inconclusive.
    Satu matriks indeks bootstrap per segmen dipakai bersama semua model (perbandingan berpasangan)."""
    rows: list[dict[str, Any]] = []
    for seg_type, segs in segments.items():
        for seg, mask in segs.items():
            d = df[np.asarray(mask, bool)]
            uo = np.sort(d["origin"].unique()) if len(d) else np.array([])
            if len(uo) < 3:
                continue
            idx = origin_block_indices(len(uo), block, reps, np.random.default_rng(seed))
            seg_rows = []
            for model in models:
                dm = d[d["model"] == model]
                if dm.empty:
                    continue
                row: dict[str, Any] = {"segment_type": seg_type, "segment": seg, "model": model,
                                       "mae": float((dm["y_true"] - dm["y_pred"]).abs().mean())}
                dk = dm[(dm["y_true"].abs() >= MAPE_EPS) & (dm["y_pred"] != 0)]
                if dk.empty:
                    seg_rows.append({**row, "n": 0, "assessment": "info"})
                    continue
                C = np.zeros((len(uo), 4))
                np.add.at(C, np.searchsorted(uo, dk["origin"].to_numpy()),
                          _direction_cells(dk["y_true"].to_numpy(float), dk["y_pred"].to_numpy(float)))
                point = _confusion_stats(C.sum(axis=0))
                boot = _confusion_stats(C[idx].sum(axis=1))
                gap, bal = _pct_ci(boot["accuracy_gap"]) or (None, None), _pct_ci(boot["balanced_accuracy"]) or (None, None)
                gap_p = bootstrap_p(boot["accuracy_gap"], 0.0)
                seg_rows.append({**row, "n": int(len(dk)), "n_origins": int(len(uo)),
                                 **{k: float(point[k]) for k in ("accuracy", "majority_baseline_accuracy",
                                                                 "accuracy_gap", "balanced_accuracy", "f1_macro",
                                                                 "recall_naik", "recall_turun", "mcc")},
                                 "gap_ci_low": gap[0], "gap_ci_high": gap[1], "balanced_ci_low": bal[0],
                                 "balanced_ci_high": bal[1],
                                 "gap_p": gap_p})
            m1 = next((r["mae"] for r in seg_rows if r["model"] == "M1"), None)
            for r in seg_rows:
                if r["model"] in no_mae:          # skor klasifier (p − 0,5), bukan ramalan perubahan harga
                    r["mae"] = None
                r["mae_ratio_vs_m1"] = r["mae"] / m1 if m1 and r["mae"] is not None else None
            rows += seg_rows
    # D-143: BH di seluruh tabel (semua segmen × model satu horizon); "better/worse" hanya bila q < 0,05
    from kagami.stats.meta import bh_fdr

    idx = [i for i, r in enumerate(rows) if r.get("gap_p") is not None]
    q = bh_fdr(np.array([rows[i]["gap_p"] for i in idx])) if idx else np.array([])
    for i, qi in zip(idx, q):
        r = rows[i]
        r["gap_q"] = float(qi)
        r["assessment"] = ("better" if qi < 0.05 and r["accuracy_gap"] > 0 else
                           "worse" if qi < 0.05 and r["accuracy_gap"] < 0 else "inconclusive")
    for r in rows:
        r.setdefault("assessment", "inconclusive")
    return [{k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in r.items()} for r in rows]


def paired_accuracy_diff(y_true, score_a, score_b, origin, block: int, reps: int = DIR_BOOT_REPS,
                         seed: int = 0) -> dict[str, Any] | None:
    """Selisih akurasi arah A − B pada baris yang SAMA (y_true ≠ 0, kedua skor berarah) dengan interval 95% bootstrap blok
    origin berpasangan (D-141). Tanda skor = arah ramalan. None bila < 3 origin."""
    yt, a, b = (np.asarray(v, float) for v in (y_true, score_a, score_b))
    o = np.asarray(origin)
    keep = np.isfinite(yt) & np.isfinite(a) & np.isfinite(b) & (np.abs(yt) >= MAPE_EPS) & (a != 0) & (b != 0)
    yt, a, b, o = yt[keep], a[keep], b[keep], o[keep]
    uo, inv = np.unique(o, return_inverse=True)
    if len(uo) < 3:
        return None
    C = np.zeros((len(uo), 3))
    np.add.at(C, inv, np.column_stack([(a > 0) == (yt > 0), (b > 0) == (yt > 0), np.ones_like(yt)]).astype(float))
    S = C[origin_block_indices(len(uo), block, reps, np.random.default_rng(seed))].sum(axis=1)
    dist = (S[:, 0] - S[:, 1]) / S[:, 2]
    lo, hi = _pct_ci(dist)
    tot = C.sum(axis=0)
    return {"diff": float((tot[0] - tot[1]) / tot[2]), "ci_low": lo, "ci_high": hi, "p": bootstrap_p(dist, 0.0),
            "acc_a": float(tot[0] / tot[2]), "acc_b": float(tot[1] / tot[2]), "n": int(tot[2]), "n_origins": int(len(uo))}


def selective_accuracy(y_true, p_up, origin, coverages: tuple[float, ...]) -> list[dict[str, Any]]:
    """Prediksi selektif (D-141): di setiap origin hanya q teratas baris dengan keyakinan |p − 0,5| terbesar yang
    diramalkan (ambang per origin → tanpa informasi lintas waktu). Per cakupan q: cakupan nyata, n, akurasi, baseline
    kelas mayoritas pada baris terpilih, F1 makro. Akurasi tinggi pada cakupan kecil tidak berarti model bagus untuk
    semua kasus: selalu baca bersama cakupannya."""
    d = pd.DataFrame({"y": np.asarray(y_true, float), "p": np.asarray(p_up, float), "o": np.asarray(origin)})
    d = d[np.isfinite(d["y"]) & np.isfinite(d["p"]) & (d["y"].abs() >= MAPE_EPS)].copy()
    if d.empty:
        return []
    d["conf"] = (d["p"] - 0.5).abs()
    d["rank"] = d.groupby("o")["conf"].rank(method="first", ascending=False, pct=True)
    out = []
    for q in coverages:
        s = d[d["rank"] <= q]
        up_t, up_p = (s["y"] > 0).to_numpy(), (s["p"] > 0.5).to_numpy()
        st = _confusion_stats(np.array([(up_t & up_p).sum(), (up_t & ~up_p).sum(), (~up_t & up_p).sum(),
                                        (~up_t & ~up_p).sum()], float))
        out.append({"target_coverage": q, "coverage": round(len(s) / len(d), 4), "n": int(len(s)),
                    **{k: float(st[k]) for k in ("accuracy", "majority_baseline_accuracy", "accuracy_gap", "f1_macro")}})
    return [{k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in r.items()} for r in out]


def feature_health(X: pd.DataFrame, near_zero: float = 1e-8) -> dict[str, Any]:
    """Kesehatan matriks fitur (D-140): jumlah fitur, fitur konstan (std ≤ near_zero, mis. tersusut habis oleh EB saat
    τ² = 0), sel kosong, dimensi efektif (fitur yang bervariasi), pasangan fitur redundan |r| ≥ 0,95."""
    X = pd.DataFrame(X)
    sd = X.std(ddof=0)
    const = sorted(str(c) for c in sd.index[sd <= near_zero])
    var = X.loc[:, sd > near_zero]
    corr = var.corr().abs().to_numpy() if var.shape[1] > 1 else np.zeros((0, 0))
    return {"n_features": int(X.shape[1]), "n_constant": len(const), "constant_features": const,
            "n_missing": int(X.isna().sum().sum()), "effective_dimensions": int(var.shape[1]),
            "n_redundant_pairs": int((np.triu(corr, 1) >= 0.95).sum()) if corr.size else 0}


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
