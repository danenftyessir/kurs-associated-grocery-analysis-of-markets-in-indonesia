"""Dekomposisi heterogenitas vs plasebo (WP-18) -- gerbang G-het. docs/METHODS.md §M2.1."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.stats.meta import bh_fdr, dersimonian_laird
from kagami.utils.config import Config

HET_STATISTICS = ("Q", "tau2", "I2")
PRIMARY_STATISTIC = "Q"          # H0-Het (PREREGISTRATION): Q per komoditas vs plasebo, BH antar komoditas
HETEROGENEITY_COLUMNS = ["commodity", "horizon", "statistic", "value", "p_placebo", "q_fdr"]


def _deviations(profiles: pd.DataFrame, horizon: int, driver: str) -> pd.DataFrame:
    d = profiles.loc[(profiles["level"] == "province") & (profiles["horizon"] == horizon)
                     & (profiles["driver"] == driver)]
    if "shrunk" in d.columns:
        d = d.loc[~d["shrunk"].astype(bool)]
    if "se" not in d.columns:
        raise KeyError("baris deviasi provinsi butuh kolom 'se' (SE cluster minggu) untuk Q/τ²; "
                       "placebo_stats provinsi wajib membawa 'se' (WP-16)")
    return d


def heterogeneity_stats(profiles: pd.DataFrame, horizon: int = 8, driver: str = "e") -> pd.DataFrame:
    """WP-18. Per komoditas dari δ(i,r,h) TANPA susut: Q, tau2, I2 (stats.meta.dersimonian_laird);
    lintas komoditas: rho_bar = rerata korelasi Pearson vektor deviasi provinsi antar pasangan komoditas
    (provinsi yang ada di kedua komoditas; pasangan dengan < 3 provinsi bersama dilewati).

    Input : baris level='province' (unit = province_id), driver, horizon, estimate, se (+ shrunk bila ada → hanya False).
            Bisa dipakai pada profiles asli maupun satu replikasi placebo_stats (yang harus membawa 'se').
    Output: commodity ('ALL' untuk rho_bar), horizon, statistic ∈ {Q, tau2, I2, rho_bar}, value, n_provinces.
    """
    d = _deviations(profiles, horizon, driver)
    rows = []
    for com, g in d.groupby("commodity", sort=True):
        r = dersimonian_laird(g["estimate"].to_numpy(float), g["se"].to_numpy(float) ** 2)
        for stat, val in (("Q", r.Q), ("tau2", r.tau2), ("I2", r.I2)):
            rows.append({"commodity": com, "horizon": horizon, "statistic": stat, "value": val,
                         "n_provinces": r.k})
    W = d.pivot_table(index="unit", columns="commodity", values="estimate", aggfunc="first")
    cors = []
    cols = list(W.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pair = W[[cols[i], cols[j]]].dropna()
            if len(pair) >= 3 and pair.std().gt(0).all():
                cors.append(np.corrcoef(pair.iloc[:, 0], pair.iloc[:, 1])[0, 1])
    rows.append({"commodity": "ALL", "horizon": horizon, "statistic": "rho_bar",
                 "value": float(np.mean(cors)) if cors else np.nan, "n_provinces": int(W.shape[0])})
    return pd.DataFrame(rows, columns=["commodity", "horizon", "statistic", "value", "n_provinces"])


def placebo_pvalues(cfg: Config, observed: pd.DataFrame, placebo: pd.DataFrame) -> pd.DataFrame:
    """WP-18. p_placebo = (1 + #{plasebo >= aktual}) / (1 + R) per (komoditas, horizon, statistik), satu sisi atas;
    q_fdr = BH antar komoditas per statistik (H0-Het memakai statistik Q, params.inference.fdr_q).

    observed: keluaran heterogeneity_stats pada data asli; placebo: keluaran yang sama per replikasi + kolom rep.
    R = jumlah replikasi plasebo dengan nilai terhingga untuk sel itu (dilaporkan di kolom n_placebo).
    Output: artefak 'heterogeneity' (+ n_provinces, n_placebo, reject = q_fdr <= fdr_q untuk statistik Q).
    """
    key = ["commodity", "horizon", "statistic"]
    null = placebo[key + ["value"]].rename(columns={"value": "null"})
    m = observed.merge(null, on=key, how="left")
    m["ge"] = (m["null"] >= m["value"]) & np.isfinite(m["null"])
    m["fin"] = np.isfinite(m["null"])
    agg = m.groupby(key, sort=False).agg(n_ge=("ge", "sum"), n_placebo=("fin", "sum")).reset_index()
    out = observed.merge(agg, on=key, how="left")
    out["n_placebo"] = out["n_placebo"].fillna(0).astype(int)
    out["p_placebo"] = np.where(out["n_placebo"] > 0, (1 + out["n_ge"]) / (1 + out["n_placebo"]), np.nan)
    out.loc[~np.isfinite(out["value"]), "p_placebo"] = np.nan
    out["q_fdr"] = np.nan
    for stat, g in out.groupby("statistic"):
        ok = g["p_placebo"].notna()
        if ok.any():
            out.loc[g.index[ok], "q_fdr"] = bh_fdr(g.loc[ok, "p_placebo"].to_numpy())
    fdr_q = float(cfg.params["inference"]["fdr_q"])
    out["reject"] = (out["statistic"] == PRIMARY_STATISTIC) & (out["q_fdr"] <= fdr_q)
    extra = [c for c in ("n_provinces", "n_placebo", "reject") if c in out.columns]
    return out[HETEROGENEITY_COLUMNS + extra]
