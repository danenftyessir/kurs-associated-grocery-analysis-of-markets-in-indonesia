"""Inferensi nasional terkalibrasi plasebo (D-129). Ditulis oleh pipeline task3.

Analisis TAMBAHAN pasca-G6, bukan pengganti: interval praregistrasi di `profiles` (yang lebih lebar dari ±1,96·SE dan
persentil bootstrap blok, METHODS M1.5) tetap interval resmi. Alasan: blok 13 minggu lebih pendek dari jendela LP
(h + lag + 2 minggu), sehingga bootstrap menarik estimasi ke nol makin kuat pada horizon panjang (median boot_ratio nasional
0,57 / 0,35 / 0,35 pada h 4 / 8 / 12) dan persentilnya bergeser ke nol; sebaliknya SE cluster minggu terlalu sempit
(plasebo |t| > 1,96 pada ± 8%). Plasebo geser-melingkar
(placebo_stats) mempertahankan struktur harga dan hanya memutus kaitan waktu penggerak -> dipakai sebagai distribusi null
statistik t, seperti E2 (D-127).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

from kagami.stats.meta import bh_fdr
from kagami.utils.config import Config

DRIVERS = ("e", "w")
KEY = ["commodity", "driver", "horizon"]
COLUMNS = ["commodity", "driver", "horizon", "estimate", "se", "t", "crit_placebo", "crit", "ci_low", "ci_high",
           "p_placebo", "p_value", "q_fdr", "ci_excludes_zero", "n_placebo", "ci_prereg_low", "ci_prereg_high",
           "boot_mean", "boot_ratio", "n_boot"]


def _order_crit(t_null: np.ndarray, alpha: float) -> float:
    """Ambang |t| plasebo yang setara dengan p plasebo < α: |t| > ambang ⇔ (1 + #{|t*| ≥ |t|}) / (1 + R) < α.

    = peringkat ke-k terbesar |t*| dengan k = ceil(α(R + 1)) − 1; R terlalu kecil (k < 1) -> tak terhingga.
    """
    t = np.sort(np.abs(t_null[np.isfinite(t_null)]))[::-1]
    if not len(t):
        return np.nan
    k = math.ceil(alpha * (len(t) + 1) - 1e-9) - 1
    return float(t[k - 1]) if k >= 1 else np.inf


def national_calibrated(cfg: Config, profiles: pd.DataFrame, placebo: pd.DataFrame | None,
                        boot: pd.DataFrame | None = None) -> pd.DataFrame:
    """D-129 (WP-13). β_e & ω nasional pada h kunci dengan interval dan p terkalibrasi plasebo -> artefak
    'national_calibrated'.

    Input : profiles (baris level = national, driver e/w, h ∈ params.lp.key_horizons; kolom se);
            placebo = artefak placebo_stats (baris nasional yang sama; kolom `se` wajib, D-111);
            boot = artefak boot_replicates (opsional; hanya diagnostik pelemahan ke nol).
    Aturan: t = estimate/se; t* = estimate/se replikasi plasebo sel yang sama.
            crit_placebo = ambang statistik urutan (_order_crit); crit = max(z_{1−α/2}, crit_placebo) (tidak pernah lebih
            sempit dari ±1,96·SE); ci = estimate ± crit·se.
            p_placebo = (1 + #{|t*| ≥ |t|}) / (1 + R); p_value = max(p_placebo, p normal dua sisi) sehingga
            p_value < α ⇔ interval tidak memuat nol (pelajaran U106). q_fdr = BH atas semua baris (keluarga 2 penggerak ×
            komoditas × h kunci). Tanpa plasebo: crit = z, p_value = p normal.
            boot_mean = rerata replikasi bootstrap; boot_ratio = boot_mean / estimate (< 1 = ditarik ke nol).
            α = params.power.mde_alpha. ci_prereg_* = interval resmi praregistrasi dari profiles.
            D-163: + baris driver PT (bila profiles punya PT nasional) = baris e diskalakan 1/γ(h) (`_pt_rows`); q baris
            PT = q baris e (keluarga BH tetap 2 penggerak × komoditas × h kunci).
    """
    alpha = float(cfg.params["power"]["mde_alpha"])
    z = float(stats.norm.ppf(1 - alpha / 2))
    H = [int(h) for h in cfg.params["lp"]["key_horizons"]]

    def _nat(df: pd.DataFrame) -> pd.DataFrame:
        return df[(df["level"] == "national") & df["driver"].isin(DRIVERS) & df["horizon"].isin(H)]

    out = (_nat(profiles)[KEY + ["estimate", "se", "ci_low", "ci_high"]]
           .rename(columns={"ci_low": "ci_prereg_low", "ci_high": "ci_prereg_high"}).reset_index(drop=True))
    out["t"] = out["estimate"] / out["se"]

    if placebo is not None and len(placebo):
        if "se" not in placebo.columns:
            raise KeyError("placebo_stats harus membawa kolom `se` (WP-16, D-111)")
        pl = _nat(placebo)
        null = pl[KEY].assign(t_null=(pl["estimate"] / pl["se"]).abs().to_numpy())
        null = null[np.isfinite(null["t_null"])]
        m = out[KEY + ["t"]].merge(null, on=KEY, how="inner")
        m["ge"] = m["t_null"] >= m["t"].abs()
        agg = m.groupby(KEY).agg(n_placebo=("t_null", "size"), n_ge=("ge", "sum"),
                                 crit_placebo=("t_null", lambda s: _order_crit(s.to_numpy(), alpha))).reset_index()
        out = out.merge(agg, on=KEY, how="left")
    else:
        out["n_placebo"], out["n_ge"], out["crit_placebo"] = 0, 0, np.nan
    out["n_placebo"] = out["n_placebo"].fillna(0).astype(int)
    out["p_placebo"] = np.where(out["n_placebo"] > 0, (1 + out["n_ge"].fillna(0)) / (1 + out["n_placebo"]), np.nan)
    out["crit"] = np.fmax(out["crit_placebo"].astype(float), z)                  # NaN (tanpa plasebo) -> z
    out["p_value"] = np.fmax(out["p_placebo"].astype(float), 2 * stats.norm.sf(out["t"].abs()))
    out["ci_low"] = out["estimate"] - out["crit"] * out["se"]
    out["ci_high"] = out["estimate"] + out["crit"] * out["se"]
    out["ci_excludes_zero"] = (out["ci_low"] > 0) | (out["ci_high"] < 0)
    out["q_fdr"] = np.nan
    ok = out["p_value"].notna()
    if ok.any():
        out.loc[ok, "q_fdr"] = bh_fdr(out.loc[ok, "p_value"].to_numpy())

    if boot is not None and len(boot):
        b = _nat(boot).groupby(KEY)["estimate"].agg(boot_mean="mean", n_boot="size").reset_index()
        out = out.merge(b, on=KEY, how="left")
    else:
        out["boot_mean"], out["n_boot"] = np.nan, 0
    out["n_boot"] = out["n_boot"].fillna(0).astype(int)
    out["boot_ratio"] = out["boot_mean"] / out["estimate"]
    out = pd.concat([out[COLUMNS], _pt_rows(profiles, out, boot, H)], ignore_index=True)
    return out[COLUMNS].sort_values(KEY).reset_index(drop=True)


def _pt_rows(profiles: pd.DataFrame, cal: pd.DataFrame, boot: pd.DataFrame | None, H: list[int]) -> pd.DataFrame:
    """D-163 (U107). Baris PT = β_e/γ(h) nasional: inferensi baris e yang sama, diskalakan 1/γ (γ = β_e/PT dari profiles).

    PT = 0 ⇔ β_e = 0, jadi t, crit, p, q, dan status interval identik dengan baris e (keluarga BH 48 sel tidak berubah);
    se & interval dibagi γ (γ(h) presisi tinggi karena respons kurs pada dirinya sendiri; ketidakpastiannya diabaikan).
    ci_prereg_* = interval resmi PT (persentil bootstrap); boot_* dari replikasi PT.
    """
    pt = profiles[(profiles["level"] == "national") & (profiles["driver"] == "PT") & profiles["horizon"].isin(H)]
    e = cal[cal["driver"] == "e"]
    if pt.empty or e.empty:
        return pd.DataFrame(columns=COLUMNS)
    m = e.drop(columns=["driver", "ci_prereg_low", "ci_prereg_high", "boot_mean", "boot_ratio", "n_boot"]).merge(
        pt[["commodity", "horizon", "estimate", "ci_low", "ci_high"]].rename(
            columns={"estimate": "pt", "ci_low": "ci_prereg_low", "ci_high": "ci_prereg_high"}),
        on=["commodity", "horizon"], how="inner")
    gamma = m["estimate"] / m["pt"]
    med = gamma[np.isfinite(gamma) & (gamma != 0)].groupby(m["horizon"]).median()
    gamma = gamma.where(np.isfinite(gamma) & (gamma != 0), m["horizon"].map(med))
    lo, hi = m["ci_low"] / gamma, m["ci_high"] / gamma
    m["ci_low"], m["ci_high"] = np.fmin(lo, hi), np.fmax(lo, hi)
    m["se"] = m["se"] / gamma.abs()
    m["estimate"], m["driver"] = m["pt"], "PT"
    if boot is not None and len(boot):
        b = boot[(boot["level"] == "national") & (boot["driver"] == "PT") & boot["horizon"].isin(H)]
        b = b.groupby(["commodity", "horizon"])["estimate"].agg(boot_mean="mean", n_boot="size").reset_index()
        m = m.merge(b, on=["commodity", "horizon"], how="left")
    else:
        m["boot_mean"], m["n_boot"] = np.nan, 0
    m["n_boot"] = m["n_boot"].fillna(0).astype(int)
    m["boot_ratio"] = m["boot_mean"] / m["estimate"]
    return m[COLUMNS]


PROVINCE_KEY = ["commodity", "driver", "horizon", "unit"]
PROVINCE_COLUMNS = ["commodity", "driver", "horizon", "unit", "estimate", "se", "t", "crit_placebo", "crit", "ci_low",
                    "ci_high", "p_placebo", "p_value", "q_fdr", "ci_excludes_zero", "n_placebo", "estimate_shrunk",
                    "ci_prereg_low", "ci_prereg_high", "boot_mean", "boot_ratio", "n_boot"]


def province_calibrated(cfg: Config, profiles: pd.DataFrame, placebo: pd.DataFrame | None,
                        boot: pd.DataFrame | None = None) -> pd.DataFrame:
    """D-163 (U107). Deviasi provinsi δ (e & w, h kunci) dengan interval & p terkalibrasi plasebo -> artefak
    'province_calibrated' (tambahan; interval praregistrasi di profiles tetap resmi).

    Input : profiles baris level = province, shrunk = False (δ mentah + se; shrunk = True dibawa sebagai estimate_shrunk);
            placebo = placebo_stats baris province (δ mentah di bawah null geser-melingkar, kolom `se` wajib);
            boot = boot_replicates (opsional; boot_ratio = rerata replikasi / δ, diagnostik pelemahan ke nol).
    Aturan: t = δ/se; null = |t*| semua provinsi × replikasi pada sel (komoditas, penggerak, h) yang sama (dipool karena
            provinsi dapat dipertukarkan di bawah null); crit = max(z, statistik urutan setara p < α); ci = δ ± crit·se;
            p_placebo = (1 + #{|t*| ≥ |t|}) / (1 + N); p_value = max(p_placebo, p normal) (p < α ⇔ interval tidak memuat
            nol); q_fdr = BH per sel atas provinsi (keluarga: "provinsi mana yang menyimpang pada komoditas × penggerak × h").
            Tanpa plasebo: crit = z, p normal.
    """
    alpha = float(cfg.params["power"]["mde_alpha"])
    z = float(stats.norm.ppf(1 - alpha / 2))
    H = [int(h) for h in cfg.params["lp"]["key_horizons"]]

    def _prov(df: pd.DataFrame) -> pd.DataFrame:
        d = df[(df["level"] == "province") & df["driver"].isin(DRIVERS) & df["horizon"].isin(H)].copy()
        d["unit"] = d["unit"].astype(str)
        return d

    prov = _prov(profiles)
    if prov.empty:
        return pd.DataFrame(columns=PROVINCE_COLUMNS)
    raw = prov[~prov["shrunk"].astype(bool)] if "shrunk" in prov else prov
    out = (raw[PROVINCE_KEY + ["estimate", "se", "ci_low", "ci_high"]]
           .rename(columns={"ci_low": "ci_prereg_low", "ci_high": "ci_prereg_high"}).reset_index(drop=True))
    if "shrunk" in prov:
        shr = prov[prov["shrunk"].astype(bool)][PROVINCE_KEY + ["estimate"]].rename(columns={"estimate": "estimate_shrunk"})
        out = out.merge(shr, on=PROVINCE_KEY, how="left")
    else:
        out["estimate_shrunk"] = np.nan
    out["t"] = out["estimate"] / out["se"]
    out["crit_placebo"], out["p_placebo"], out["n_placebo"] = np.nan, np.nan, 0
    if placebo is not None and len(placebo):
        if "se" not in placebo.columns:
            raise KeyError("placebo_stats harus membawa kolom `se` (WP-16, D-111)")
        pl = _prov(placebo)
        pl = pl.assign(t_null=(pl["estimate"] / pl["se"]).abs())
        pl = pl[np.isfinite(pl["t_null"])]
        nulls = {k: np.sort(g["t_null"].to_numpy()) for k, g in pl.groupby(KEY)}
        for k, idx in out.groupby(KEY).groups.items():
            t_null = nulls.get(k)
            if t_null is None or not len(t_null):
                continue
            ta = out.loc[idx, "t"].abs().to_numpy()
            n_ge = len(t_null) - np.searchsorted(t_null, ta, side="left")
            out.loc[idx, "p_placebo"] = np.where(np.isfinite(ta), (1 + n_ge) / (1 + len(t_null)), np.nan)
            out.loc[idx, "crit_placebo"] = _order_crit(t_null, alpha)
            out.loc[idx, "n_placebo"] = len(t_null)
    out["crit"] = np.fmax(out["crit_placebo"].astype(float), z)
    out["p_value"] = np.fmax(out["p_placebo"].astype(float), 2 * stats.norm.sf(out["t"].abs()))
    out["ci_low"] = out["estimate"] - out["crit"] * out["se"]
    out["ci_high"] = out["estimate"] + out["crit"] * out["se"]
    out["ci_excludes_zero"] = (out["ci_low"] > 0) | (out["ci_high"] < 0)
    out["q_fdr"] = np.nan
    for _, idx in out.groupby(KEY).groups.items():
        ok = out.loc[idx, "p_value"].notna()
        if ok.any():
            out.loc[ok[ok].index, "q_fdr"] = bh_fdr(out.loc[ok[ok].index, "p_value"].to_numpy())
    if boot is not None and len(boot):
        b = _prov(boot).groupby(PROVINCE_KEY)["estimate"].agg(boot_mean="mean", n_boot="size").reset_index()
        out = out.merge(b, on=PROVINCE_KEY, how="left")
    else:
        out["boot_mean"], out["n_boot"] = np.nan, 0
    out["n_boot"] = out["n_boot"].fillna(0).astype(int)
    out["boot_ratio"] = out["boot_mean"] / out["estimate"]
    out["n_placebo"] = out["n_placebo"].astype(int)
    return out[PROVINCE_COLUMNS].sort_values(PROVINCE_KEY).reset_index(drop=True)
