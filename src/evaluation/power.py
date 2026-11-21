"""Analisis daya / MDE (WP-09) -- dihitung SEBELUM hasil Task 1 dilihat (gerbang G-power)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from kagami.models.local_projection import build_design, fx_self_response, regressors
from kagami.utils.config import Config


def null_se(design: pd.DataFrame, impulse: str = "de") -> tuple[float, int]:
    """WP-09. SE cluster-minggu koefisien `impulse` di bawah H0 (β = 0), TANPA menghitung β̂.

    û = residual y pada kontrol saja (LP tanpa kurs: tanpa kolom berawalan 'de'/'dw');
    x̃ = residual `impulse` pada kontrol + sisa blok kurs (lag de, dw & lag dw);
    SE = sqrt(c · Σ_minggu (Σ x̃·û)²) / Σ x̃², c = koreksi CR1 G/(G-1)·(n-1)/(n-k) (sama dengan ols_cluster).
    Bentuk skor/LM ini = SE regresi û pada x̃ dengan cluster minggu bila β ≈ 0 (METHODS §M0.6 langkah 2).
    Return (se, n_obs).
    """
    reg = regressors(design)
    fx = [c for c in reg if c.startswith(("de", "dw"))]
    ctrl = [c for c in reg if c not in fx]
    others = ctrl + [c for c in fx if c != impulse]
    y = design["y"].to_numpy(float)
    C, O = design[ctrl].to_numpy(float), design[others].to_numpy(float)
    x = design[impulse].to_numpy(float)
    u = y - C @ np.linalg.lstsq(C, y, rcond=None)[0]
    xt = x - O @ np.linalg.lstsq(O, x, rcond=None)[0]
    codes, uniq = pd.factorize(design["group"])
    s = np.bincount(codes, weights=xt * u)
    n, k, G = len(y), len(others) + 1, len(uniq)
    c = (G / (G - 1)) * ((n - 1) / (n - k)) if G > 1 and n > k else 1.0
    return float(np.sqrt(c * (s @ s)) / (xt @ xt)), n


def asymmetry_null_se(design: pd.DataFrame) -> tuple[float, int]:
    """WP-09. SE cluster-minggu selisih δ = β⁻ - β⁺ (lag 0) di bawah H0 asimetri (δ = 0), TANPA menghitung β̂.

    design: keluaran build_design(..., asymmetric=True). Parametrisasi ulang β⁺·de⁺ + β⁻·de⁻ = β⁺·de + δ·de⁻
    (de = de⁺ + de⁻); lag de⁺/de⁻ tetap bebas. û = residual y pada semua regresor kecuali de⁻ lag 0 (H0: tanpa asimetri,
    respons simetris tetap ada); x̃ = de⁻ residual pada himpunan yang sama; SE bentuk skor + CR1 seperti null_se.
    Uji H2 Wald β⁺(8) = β⁻(8) setara dengan δ = 0 (PREREGISTRATION; D-115). Return (se, n_obs).
    """
    reg = regressors(design)
    others = [c for c in reg if c not in ("de_pos", "de_neg")]
    O = np.column_stack([design[others].to_numpy(float),
                         (design["de_pos"] + design["de_neg"]).to_numpy(float)])
    y, x = design["y"].to_numpy(float), design["de_neg"].to_numpy(float)
    u = y - O @ np.linalg.lstsq(O, y, rcond=None)[0]
    xt = x - O @ np.linalg.lstsq(O, x, rcond=None)[0]
    codes, uniq = pd.factorize(design["group"])
    s = np.bincount(codes, weights=xt * u)
    n, k, G = len(y), O.shape[1] + 1, len(uniq)
    c = (G / (G - 1)) * ((n - 1) / (n - k)) if G > 1 and n > k else 1.0
    return float(np.sqrt(c * (s @ s)) / (xt @ xt)), n


def compute_mde(cfg: Config, panel: pd.DataFrame, region_panel: pd.DataFrame, drivers: pd.DataFrame,
                world: pd.DataFrame | None = None, elig: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-09. -> artefak 'mde'.

    Untuk tiap komoditas, level nasional (panel provinsi eligible, pooled, efek tetap seri) & 7 wilayah (satu LP per
    wilayah dari panel_weekly_region), horizon di params.lp.key_horizons, desain LP Task 1 (build_design, simetris,
    L = params.lp.lags):
    1) SE(β) di bawah H0 dari residual LP TANPA kurs (null_se; β̂ tidak pernah dihitung);
    2) MDE_β = (z_{1-α/2} + z_{power}) · SE  (params.power: mde_alpha, mde_power; ≈ 2,80·SE);
    3) MDE_PT = MDE_β / γ(h), γ dari fx_self_response.
    4) Nasional saja: MDE asimetri δ = β⁻ - β⁺ (asymmetry_null_se pada desain asimetris) -> mde_asym_beta,
       mde_asym_pt = mde_asym_beta / γ(h) (status H2, D-115).
    Kolom: commodity, level, horizon, mde_beta, mde_pt + unit (ALL | wilayah), se_beta, gamma, n_weeks, n_obs,
    se_asym, mde_asym_beta, mde_asym_pt (NaN untuk wilayah).
    Aturan gerbang (D-007, gate_g_power): MDE_PT(8) nasional > mde_threshold_pt8 untuk ketiga
    params.power.mde_commodities -> LP jadi sekunder.
    """
    pw, lp = cfg.params["power"], cfg.params["lp"]
    z = stats.norm.ppf(1 - pw["mde_alpha"] / 2) + stats.norm.ppf(pw["mde_power"])
    L, H = int(lp["lags"]), [int(h) for h in lp["key_horizons"]]
    gamma = {h: fx_self_response(cfg, drivers, h, L) for h in H}
    rows = []
    for com in cfg.commodity_ids():
        for h in H:
            designs = [("national", "ALL", build_design(cfg, panel, drivers, world, com, h, L, elig=elig))]
            reg_d = build_design(cfg, region_panel, drivers, world, com, h, L, unit_col="region",
                                 price_col="log_price_index")
            designs += [("region", u, g.reset_index(drop=True)) for u, g in reg_d.groupby("unit", sort=True)]
            se_a, _ = asymmetry_null_se(build_design(cfg, panel, drivers, world, com, h, L, asymmetric=True,
                                                     elig=elig))
            for level, unit, D in designs:
                se, n = null_se(D)
                asym = level == "national"
                rows.append({"commodity": com, "level": level, "unit": unit, "horizon": h, "se_beta": se,
                             "mde_beta": z * se, "gamma": gamma[h], "mde_pt": z * se / gamma[h],
                             "n_weeks": int(D["week"].nunique()), "n_obs": n,
                             "se_asym": se_a if asym else np.nan,
                             "mde_asym_beta": z * se_a if asym else np.nan,
                             "mde_asym_pt": z * se_a / gamma[h] if asym else np.nan})
    out = pd.DataFrame(rows)
    return out[["commodity", "level", "unit", "horizon", "mde_beta", "mde_pt", "se_beta", "gamma",
                "n_weeks", "n_obs", "se_asym", "mde_asym_beta", "mde_asym_pt"]]


def gate_g_power(cfg: Config, mde: pd.DataFrame) -> dict:
    """WP-09. Keputusan gerbang G-power (D-007) dari artefak 'mde'.

    Return dict: mde_pt8 {komoditas: MDE_PT(8) nasional}, lp_secondary (True bila ketiga params.power.mde_commodities
    > mde_threshold_pt8), threshold, dan (bila kolom mde_asym_pt ada) h2_confirmatory {komoditas: MDE asimetri PT(8)
    nasional <= threshold} untuk semua komoditas -- ambang H2 dibaca dalam satuan PT (keputusan Danen, D-115).
    """
    pw = cfg.params["power"]
    nat = mde[(mde["level"] == "national") & (mde["horizon"] == 8)].set_index("commodity")
    m = nat["mde_pt"]
    vals = {c: float(m.get(c, np.nan)) for c in pw["mde_commodities"]}
    thr = float(pw["mde_threshold_pt8"])
    out = {"mde_pt8": vals, "threshold": thr, "lp_secondary": all(v > thr for v in vals.values())}
    if "mde_asym_pt" in nat.columns:
        out["mde_asym_pt8"] = {c: float(v) for c, v in nat["mde_asym_pt"].items()}
        out["h2_confirmatory"] = {c: bool(v <= thr) for c, v in nat["mde_asym_pt"].items()}
    return out
