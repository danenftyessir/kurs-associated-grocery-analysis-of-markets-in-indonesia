"""Task 3 -- asosiasi profil respons dengan eksposur & karakteristik provinsi. docs/METHODS.md §M3.

(3a) kendall_exact, level komoditas N = 10 (WP-22); (3b) meta_regression, level provinsi (WP-23);
(3c) fe_interaction, robustness efek tetap komoditas x minggu (WP-24).
"""

from __future__ import annotations

from math import factorial

import numpy as np
import pandas as pd
from scipy import stats

from kagami.stats.regression import ols_cluster
from kagami.utils.config import Config

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


META_FEATURES = ("ln_dist_hub", "rice_sufficiency", "n_kota")      # praregistrasi: maks 3 fitur Z(r)
META_EXTRA = ["commodity", "driver", "horizon", "n", "tau2", "se_cr2", "se_boot", "ci_method"]
H3_FEATURE, H3_HORIZON = "ln_dist_hub", 4                           # H3: koefisien jarak pada h = 4 < 0 (satu arah)
POOLED = "ALL"


def _zfeatures(province_features: pd.DataFrame) -> pd.DataFrame:
    """Z(r) z-score per kolom (index province_id); fitur dengan nilai kosong atau tanpa variasi dibuang (U14/U15)."""
    f = province_features.set_index("province_id")
    keep = [c for c in META_FEATURES if c in f and f[c].notna().all() and f[c].std(ddof=0) > 0]
    return (f[keep] - f[keep].mean()) / f[keep].std(ddof=0)


def _sqrt_inv(M: np.ndarray) -> np.ndarray:
    """(M)^{-1/2} untuk matriks simetris semidefinit (eigenvalue kecil dipotong)."""
    w, V = np.linalg.eigh(M)
    return (V * np.where(w > 1e-10, 1.0 / np.sqrt(np.clip(w, 1e-10, None)), 0.0)) @ V.T


def _fit_meta(y: np.ndarray, X: np.ndarray, s2: np.ndarray, groups: np.ndarray) -> dict:
    """Meta-regresi efek acak: τ² momen DerSimonian-Laird terampat, WLS bobot 1/(s²+τ²), SE model dan CR2.

    CR2 (Bell-McCaffrey): residual tiap klaster dikoreksi (I - H_gg)^{-1/2} pada regresi terboboti; df = G - p.
    """
    p, k = X.shape[1], len(y)
    w = 1.0 / s2
    A = np.linalg.pinv(X.T @ (w[:, None] * X))
    beta_fe = A @ (X.T @ (w * y))
    q = float(w @ (y - X @ beta_fe) ** 2)
    c = w.sum() - np.trace(A @ (X.T @ ((w ** 2)[:, None] * X)))
    tau2 = max(0.0, (q - (k - p)) / c) if c > 0 else 0.0
    w = 1.0 / (s2 + tau2)
    Xt, yt = np.sqrt(w)[:, None] * X, np.sqrt(w) * y
    M = np.linalg.pinv(Xt.T @ Xt)
    beta = M @ (Xt.T @ yt)
    resid = yt - Xt @ beta
    meat = np.zeros((p, p))
    for g in np.unique(groups):
        idx = np.flatnonzero(groups == g)
        Xg = Xt[idx]
        adj = _sqrt_inv(np.eye(len(idx)) - Xg @ M @ Xg.T)
        u = Xg.T @ (adj @ resid[idx])
        meat += np.outer(u, u)
    cov = M @ meat @ M
    return {"beta": beta, "se_model": np.sqrt(np.diag(M)), "se_cr2": np.sqrt(np.diag(cov)), "tau2": tau2,
            "df": max(len(np.unique(groups)) - p, 1)}


def _design(delta: pd.DataFrame, Z: pd.DataFrame, pooled: bool) -> tuple:
    """delta: kolom commodity, province_id, estimate, se -> (y, X, s2, groups, nama koefisien).
    pooled = intersep per komoditas."""
    d = delta[delta["province_id"].isin(Z.index) & (delta["se"] > 0) & delta["estimate"].notna()]
    zr = Z.loc[d["province_id"]].to_numpy()
    if pooled:
        dummies = pd.get_dummies(d["commodity"]).to_numpy(float)
        X = np.hstack([dummies, zr])
        names = [f"intercept_{c}" for c in sorted(d["commodity"].unique())] + list(Z.columns)
    else:
        X, names = np.hstack([np.ones((len(d), 1)), zr]), ["intercept"] + list(Z.columns)
    return d["estimate"].to_numpy(float), X, d["se"].to_numpy(float) ** 2, d["province_id"].to_numpy(), names


def _jackknife(delta: pd.DataFrame, Z: pd.DataFrame, pooled: bool, j: int) -> tuple[float, float]:
    out = []
    for prov in delta["province_id"].unique():
        y, X, s2, g, _ = _design(delta[delta["province_id"] != prov], Z.drop(index=prov, errors="ignore"), pooled)
        if len(y) > X.shape[1] + 1:
            out.append(_fit_meta(y, X, s2, g)["beta"][j])
    return (float(np.min(out)), float(np.max(out))) if out else (np.nan, np.nan)


def _boot_coefs(boot: pd.DataFrame, driver: str, h: int, commodities: list[str], Z: pd.DataFrame, pooled: bool,
                col: str) -> np.ndarray:
    """Koefisien `col` pada tiap replikasi bootstrap (regresi ulang dengan δ & se replikasi)."""
    b = boot[(boot["level"] == "province") & (boot["driver"] == driver) & (boot["horizon"] == h)
             & boot["commodity"].isin(commodities)]
    out = []
    for _, g in b.groupby("rep"):
        d = g.assign(province_id=g["unit"].astype(int))
        y, X, s2, grp, names = _design(d, Z, pooled)
        if len(y) > X.shape[1] + 1:
            out.append(_fit_meta(y, X, s2, grp)["beta"][names.index(col)])
    return np.asarray(out)


def meta_regression(cfg: Config, profiles: pd.DataFrame, boot: pd.DataFrame,
                    province_features: pd.DataFrame) -> pd.DataFrame:
    """WP-23. Meta-regresi efek acak pada deviasi δ(i,r,h) TANPA susut, maks 3 fitur praregistrasi:
    ln_dist_hub, rice_sufficiency (bila tersedia), n_kota (kontrol desain). H3: koefisien ln_dist_hub pada h=4 < 0
    (satu arah); h=12 dua arah.
    Interval: bootstrap blok mingguan (boot_replicates) DAN SE cluster provinsi CR2 -> laporkan yang lebih lebar.
    Jackknife per provinsi -> jackknife_min/max. -> baris 'assoc' level='province'.

    Per (komoditas, h ∈ key_horizons) dan gabungan semua komoditas (commodity='ALL', intersep per komoditas, klaster
    = provinsi), driver e. δ_r = b0 + Σ_k b_k·Z_k(r) + u_r + e_r, bobot 1/(s²+τ²), τ² momen DL terampat. Z(r)
    di-z-score (b_k = Δ respons per 1 SD fitur). Fitur dengan nilai kosong dibuang (rice_sufficiency, n_kota sampai
    U14/U15). Interval = yang lebih lebar antara CR2 (t, df = G - p) dan persentil 2,5/97,5 koefisien replikasi
    bootstrap (kosong -> CR2 saja). p_value dua sisi; H3 (ln_dist_hub, h=4) satu sisi H1: b < 0 (method
    '..._one_sided'). Kolom ekstra: commodity, driver, horizon, n, tau2, se_cr2, se_boot, ci_method.
    outcome = 'e_h<h>'.
    """
    Z = _zfeatures(province_features)
    if Z.empty:
        print("[task3] meta-regresi dilewati: tidak ada fitur Z(r) yang lengkap")
        return pd.DataFrame(columns=ASSOC_COLUMNS + META_EXTRA)
    drv, rows = "e", []
    d = profiles[(profiles["level"] == "province") & (profiles["driver"] == drv) & ~profiles["shrunk"].astype(bool)]
    for h in [int(x) for x in cfg.params["lp"]["key_horizons"]]:
        dh = d[d["horizon"] == h].assign(province_id=lambda x: x["unit"].astype(int))
        coms = sorted(dh["commodity"].unique())
        for scope in [POOLED] + coms:
            pooled = scope == POOLED
            sub = dh if pooled else dh[dh["commodity"] == scope]
            y, X, s2, grp, names = _design(sub, Z, pooled)
            if len(y) <= X.shape[1] + 1:
                continue
            fit = _fit_meta(y, X, s2, grp)
            for feat in Z.columns:
                j = names.index(feat)
                est, se = float(fit["beta"][j]), float(fit["se_cr2"][j])
                tcrit = stats.t.ppf(0.975, fit["df"])
                lo, hi = est - tcrit * se, est + tcrit * se
                se_boot, method = np.nan, "cr2"
                if boot is not None and len(boot):
                    cb = _boot_coefs(boot, drv, h, coms if pooled else [scope], Z, pooled, feat)
                    if len(cb) > 1:
                        lo, hi = min(lo, float(np.percentile(cb, 2.5))), max(hi, float(np.percentile(cb, 97.5)))
                        se_boot, method = float(np.std(cb, ddof=1)), "max(cr2, bootstrap)"
                tstat = est / se if se > 0 else np.nan
                one_sided = feat == H3_FEATURE and h == H3_HORIZON
                p = (float(stats.t.cdf(tstat, fit["df"])) if one_sided
                     else float(2 * stats.t.sf(abs(tstat), fit["df"])))
                jmin, jmax = _jackknife(sub, Z, pooled, j)
                rows.append({"level": "province", "feature": feat, "outcome": f"{drv}_h{h}", "estimate": est,
                             "ci_low": lo, "ci_high": hi, "p_value": p,
                             "method": "meta_regression_re" + ("_one_sided" if one_sided else ""),
                             "jackknife_min": jmin, "jackknife_max": jmax, "commodity": scope, "driver": drv,
                             "horizon": h, "n": len(y), "tau2": fit["tau2"], "se_cr2": se, "se_boot": se_boot,
                             "ci_method": method})
    return pd.DataFrame(rows, columns=ASSOC_COLUMNS + META_EXTRA)


def _two_way_demean(df: pd.DataFrame, cols: list[str], g1: list[str], g2: list[str], iters: int = 30) -> pd.DataFrame:
    """Demean dua arah (alternating projection) atas kelompok g1 dan g2 pada panel tak seimbang."""
    out = df[cols].copy()
    for _ in range(iters):
        before = out.to_numpy().copy()
        out = out - out.groupby([df[c] for c in g1]).transform("mean")
        out = out - out.groupby([df[c] for c in g2]).transform("mean")
        if np.nanmax(np.abs(out.to_numpy() - before)) < 1e-10:
            break
    return out


def fe_interaction(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                   province_features: pd.DataFrame, *, elig: pd.DataFrame | None = None,
                   horizons: list[int] | None = None) -> pd.DataFrame:
    """WP-24. (3c) Panel dengan efek tetap komoditas x minggu; koefisien interaksi de x Z(r)
    diidentifikasi hanya dari perbedaan antarprovinsi. -> baris 'assoc' method='fe_interaction'.
    Dipotong pertama bila waktu habis (urutan pemotongan, D-014).

    Spesifikasi ringan: y^(h) = p_{r,t+h} - p_{r,t-1} (log, per komoditas) = α_{komoditas,minggu} +
    α_{komoditas,provinsi} + Σ_k γ_k·(Δe_t × Z_k(r)) + ε; Z(r) di-z-score; efek tetap dua arah (komoditas x
    minggu menyerap efek utama Δe_t); SE cluster per minggu (stats.regression.ols_cluster); h ∈ params.lp.key_horizons;
    `elig` membatasi seri eligible.
    Baris 'assoc' level='province', outcome = 'e_h<h>', interval = estimasi ± 1,96·SE, p normal dua sisi;
    jackknife_min/max NaN (tidak dihitung pada robustness ini). Kolom ekstra: commodity ('ALL'), driver, horizon, n.
    """
    Z = _zfeatures(province_features)
    if Z.empty:
        print("[task3] interaksi FE dilewati: tidak ada fitur Z(r) yang lengkap")
        return pd.DataFrame(columns=ASSOC_COLUMNS + META_EXTRA)
    p = panel[["week", "province_id", "commodity", "log_price"]]
    if elig is not None:
        ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
        p = p.merge(ok, on=["province_id", "commodity"], how="inner")
    p = p[p["province_id"].isin(Z.index)].sort_values(["province_id", "commodity", "week"])
    de = drivers.set_index("week")["de"]
    per = cfg.params["period"]
    rows = []
    for h in [int(x) for x in (horizons if horizons is not None else cfg.params["lp"]["key_horizons"])]:
        g = p.groupby(["province_id", "commodity"])["log_price"]
        d = p.assign(y=g.shift(-h) - g.shift(1), de=p["week"].map(de))
        d = d[(d["week"] >= pd.Timestamp(per["start"])) & d["y"].notna() & d["de"].notna()]
        for feat in Z.columns:
            d[f"x_{feat}"] = d["de"] * d["province_id"].map(Z[feat])
        xcols = [f"x_{f}" for f in Z.columns]
        dm = _two_way_demean(d, ["y"] + xcols, ["commodity", "week"], ["commodity", "province_id"])
        res = ols_cluster(dm["y"].to_numpy(), dm[xcols].to_numpy(), d["week"].to_numpy())
        for j, feat in enumerate(Z.columns):
            est, se = float(res.beta[j]), float(res.se[j])
            rows.append({"level": "province", "feature": feat, "outcome": f"e_h{h}", "estimate": est,
                         "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
                         "p_value": float(2 * stats.norm.sf(abs(est / se))) if se > 0 else np.nan,
                         "method": "fe_interaction", "jackknife_min": np.nan, "jackknife_max": np.nan,
                         "commodity": POOLED, "driver": "e", "horizon": h, "n": int(res.n_obs), "tau2": np.nan,
                         "se_cr2": np.nan, "se_boot": np.nan, "ci_method": "cluster_week"})
    return pd.DataFrame(rows, columns=ASSOC_COLUMNS + META_EXTRA)
