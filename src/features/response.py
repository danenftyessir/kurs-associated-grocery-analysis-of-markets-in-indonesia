"""Penyusutan EB deviasi provinsi + ekstraksi fitur respons (WP-17). docs/METHODS.md §M1e-f."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.stats.meta import dersimonian_laird, eb_shrink, reml_tau2
from kagami.utils.config import Config

CELL = ["commodity", "driver", "horizon"]
FEATURE_HORIZONS = (4, 8, 12)
FEATURE_COLUMNS = ["level", "unit", "commodity", "R4", "R8", "R12", "W4", "W8", "W12", "PT8", "t_half", "A8"]
HALF = 0.5                                   # t_half: respons >= 50% dari maksimum


def shrink_deviations(cfg: Config, profiles: pd.DataFrame, *, check_reml: bool = True) -> pd.DataFrame:
    """WP-17. Per (komoditas, driver, horizon): τ² DL (stats.meta.dersimonian_laird; REML sebagai cek),
    estimasi tersusut = stats.meta.eb_shrink. Tambah baris level='province', shrunk=True.

    Sel dengan < 2 provinsi ber-se > 0 dilewati. τ² = 0 -> semua provinsi = μ (temuan sah, bukan kegagalan).
    se tersusut = sqrt(w·s² + (1-w)²·Var(μ)), w = τ²/(τ²+s²) (galat posterior + ketidakpastian μ);
    ci = estimasi ± 1,96·se. Baris asli (shrunk=False) dipertahankan. Selisih τ² DL vs REML dicetak sebagai cek
    (`check_reml=False` melewati cek dan cetakan, dipakai per replikasi bootstrap/plasebo).
    """
    prov = profiles[(profiles["level"] == "province") & ~profiles["shrunk"].astype(bool)]
    rows, gap = [], []
    for _, g in prov.groupby(CELL):
        g = g[np.isfinite(g["estimate"]) & np.isfinite(g["se"]) & (g["se"] > 0)]
        if len(g) < 2:
            continue
        est, var = g["estimate"].to_numpy(), g["se"].to_numpy() ** 2
        het = dersimonian_laird(est, var)
        if check_reml:
            gap.append(abs(het.tau2 - reml_tau2(est, var)))
        shrunk = eb_shrink(est, var, het.mu, het.tau2)
        w = het.tau2 / (het.tau2 + var) if het.tau2 > 0 else np.zeros_like(var)
        var_mu = 1.0 / np.sum(1.0 / (var + het.tau2))
        se = np.sqrt(w * var + (1 - w) ** 2 * var_mu)
        rows.append(g.assign(estimate=shrunk, se=se, ci_low=shrunk - 1.96 * se, ci_high=shrunk + 1.96 * se,
                             shrunk=True))
    if gap:
        print(f"[task1] EB: {len(gap)} sel, selisih τ² DL vs REML maks {max(gap):.4g}")
    return pd.concat([profiles, *rows], ignore_index=True) if rows else profiles


CURVE = ["level", "unit", "commodity", "horizon", "estimate", "se", "ci_low", "ci_high"]


def _curves(profiles: pd.DataFrame, driver: str) -> pd.DataFrame:
    """Kurva respons satu driver untuk semua level. Provinsi = respons nasional + δ tersusut (baris shrunk=True),
    se = sqrt(se_nasional² + se_δ²) (kovarians diabaikan), ci = estimasi ± 1,96·se; level lain apa adanya."""
    d = profiles[profiles["driver"] == driver]
    base = d[d["level"] != "province"]
    parts = [base[CURVE]]
    prov = d[(d["level"] == "province") & d["shrunk"].astype(bool)]
    nat = base[base["level"] == "national"][["commodity", "horizon", "estimate", "se"]]
    if len(prov) and len(nat):
        m = prov.merge(nat, on=["commodity", "horizon"], suffixes=("", "_nat"))
        m["estimate"] = m["estimate"] + m["estimate_nat"]
        m["se"] = np.sqrt(m["se"] ** 2 + m["se_nat"] ** 2)
        m["ci_low"], m["ci_high"] = m["estimate"] - 1.96 * m["se"], m["estimate"] + 1.96 * m["se"]
        parts.append(m[CURVE])
    return pd.concat(parts, ignore_index=True)


def _wide(curves: pd.DataFrame, h: int) -> pd.Series:
    c = curves[curves["horizon"] == h].drop_duplicates(["level", "unit", "commodity"])
    return c.set_index(["level", "unit", "commodity"])["estimate"]


def _t_half(curves: pd.DataFrame) -> pd.Series:
    """h terkecil dengan respons kurs >= 50% maksimum (searah tanda respons maksimum); NaN bila interval di h maksimum
    memuat nol."""
    out = {}
    for key, g in curves.dropna(subset=["estimate"]).groupby(["level", "unit", "commodity"]):
        top = g.loc[g["estimate"].abs().idxmax()]
        if not (top["ci_low"] > 0 or top["ci_high"] < 0):
            out[key] = np.nan
            continue
        sign = np.sign(top["estimate"])
        out[key] = float(g.loc[sign * g["estimate"] >= HALF * sign * top["estimate"], "horizon"].min())
    return pd.Series(out, dtype=float)


def response_features(cfg: Config, profiles: pd.DataFrame) -> pd.DataFrame:
    """WP-17. -> artefak 'response_features'.

    R4,R8,R12 = respons kurs kumulatif; W4,W8,W12 = respons harga dunia rupiah; PT8 = β(8)/γ(8);
    t_half = horizon pertama respons >= 50% maksimum (NaN bila interval memuat nol di horizon maksimum);
    A8 = β+(8) - β-(8) (level komoditas saja).
    Satu baris per (level, unit, commodity). Provinsi (hanya bila baris shrunk=True ada): R/W = respons nasional + δ
    tersusut, PT8 = R8/γ(8) dengan γ(8) = β_nasional(8)/PT_nasional(8) (NaN bila salah satunya 0),
    t_half dari kurva itu, A8 NaN. Nasional dan wilayah memakai estimasi LP apa adanya.
    """
    e, w = _curves(profiles, "e"), _curves(profiles, "w")
    feat = pd.DataFrame({**{f"R{h}": _wide(e, h) for h in FEATURE_HORIZONS},
                         **{f"W{h}": _wide(w, h) for h in FEATURE_HORIZONS}})
    nonprov = profiles[profiles["level"] != "province"]
    idx = ["level", "unit", "commodity"]
    h8 = nonprov[nonprov["horizon"] == 8]
    pt = h8[h8["driver"] == "PT"].set_index(idx)["estimate"]
    feat["PT8"] = pt.reindex(feat.index)
    pos = h8[h8["driver"] == "e_pos"].set_index(idx)["estimate"]
    neg = h8[h8["driver"] == "e_neg"].set_index(idx)["estimate"]
    feat["A8"] = (pos - neg).reindex(feat.index)
    nat = profiles[(profiles["level"] == "national") & (profiles["horizon"] == 8)]
    b8 = nat[nat["driver"] == "e"].set_index("commodity")["estimate"]
    pt8 = nat[nat["driver"] == "PT"].set_index("commodity")["estimate"]
    gamma = (b8 / pt8).where((b8 != 0) & (pt8 != 0))
    is_prov = feat.index.get_level_values("level") == "province"
    if is_prov.any():
        com = feat.index.get_level_values("commodity")[is_prov]
        feat.loc[is_prov, "PT8"] = feat.loc[is_prov, "R8"].to_numpy() / gamma.reindex(com).to_numpy()
    feat["t_half"] = _t_half(e).reindex(feat.index)
    out = feat.reset_index()
    return out[FEATURE_COLUMNS].sort_values(["level", "unit", "commodity"]).reset_index(drop=True)
