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
    return out[COLUMNS].sort_values(KEY).reset_index(drop=True)
