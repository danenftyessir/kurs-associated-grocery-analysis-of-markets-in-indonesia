"""H2 -- asimetri respons depresiasi vs apresiasi (PREREGISTRATION H2; D-115, D-125). Ditulis oleh pipeline task3."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from kagami.evaluation.power import gate_g_power
from kagami.utils.config import Config

H2_HORIZON = 8          # horizon uji H2 yang dibekukan di PREREGISTRATION (struktural, bukan parameter)

COLUMNS = ["commodity", "horizon", "beta_pos", "beta_neg", "estimate", "se", "ci_low", "ci_high", "z", "p_value",
           "confirmatory", "reject", "mde_asym_beta", "boot_ci_low", "boot_ci_high", "n_boot", "p_placebo",
           "n_placebo", "n_weeks", "n_obs", "wald_ci_low", "wald_ci_high", "ci_excludes_zero"]


def _replicate_diff(reps: pd.DataFrame | None) -> pd.DataFrame:
    """β⁺ − β⁻ nasional per (rep, komoditas, horizon) dari boot_replicates / placebo_stats."""
    if reps is None or not len(reps):
        return pd.DataFrame(columns=["rep", "commodity", "horizon", "diff"])
    r = reps[(reps["level"] == "national") & reps["driver"].isin(["e_pos", "e_neg"])]
    w = r.pivot_table(index=["rep", "commodity", "horizon"], columns="driver", values="estimate", aggfunc="first")
    if not {"e_pos", "e_neg"} <= set(w.columns):
        return pd.DataFrame(columns=["rep", "commodity", "horizon", "diff"])
    return (w["e_pos"] - w["e_neg"]).rename("diff").dropna().reset_index()


def asymmetry_tests(cfg: Config, wald: pd.DataFrame, boot: pd.DataFrame | None = None,
                    placebo: pd.DataFrame | None = None, mde: pd.DataFrame | None = None) -> pd.DataFrame:
    """H2 (WP-13). -> artefak 'asymmetry'.

    Input : wald = models.local_projection.asymmetry_wald (estimate = β⁺ − β⁻, se cluster minggu);
            boot/placebo = artefak boot_replicates / placebo_stats (baris nasional e_pos & e_neg; opsional);
            mde = artefak mde (opsional; status konfirmatori dari gate_g_power, D-115).
    Uji utama (praregistrasi): Wald z = estimate/se, p dua sisi normal (interval Wald ±1,96·se di wald_ci_low/high),
    α = params.power.mde_alpha. confirmatory = horizon == 8 dan MDE asimetri PT(8) ≤ ambang (h2_confirmatory);
    reject = confirmatory dan p ≤ α. Komoditas/horizon lain tetap dilaporkan sebagai deskriptif (reject = False).
    Pembanding (tidak menggantikan uji utama): persentil 2,5/97,5 selisih bootstrap blok; p plasebo dua sisi
    (1 + #|d*| ≥ |d|)/(1 + R) dari selisih di bawah geser-melingkar.
    Interval laporan ci_low/ci_high = yang lebih lebar dari Wald dan persentil bootstrap (aturan inference.bootstrap_ci;
    SE cluster terlalu sempit di plasebo, D-127); ci_excludes_zero dihitung dari interval laporan ini.
    """
    alpha = float(cfg.params["power"]["mde_alpha"])
    out = wald.copy()
    out["z"] = out["estimate"] / out["se"]
    out["p_value"] = 2 * stats.norm.sf(out["z"].abs())
    out["ci_low"] = out["estimate"] - 1.96 * out["se"]
    out["ci_high"] = out["estimate"] + 1.96 * out["se"]

    conf, mde_b = {}, {}
    if mde is not None and len(mde):
        conf = gate_g_power(cfg, mde).get("h2_confirmatory", {})
        nat = mde[(mde["level"] == "national") & (mde["horizon"] == H2_HORIZON)]
        if "mde_asym_beta" in nat.columns:
            mde_b = dict(zip(nat["commodity"], nat["mde_asym_beta"]))
    out["confirmatory"] = (out["horizon"] == H2_HORIZON) & out["commodity"].map(lambda c: bool(conf.get(c, False)))
    out["reject"] = out["confirmatory"] & (out["p_value"] <= alpha)
    out["mde_asym_beta"] = np.where(out["horizon"] == H2_HORIZON, out["commodity"].map(mde_b), np.nan)

    key = ["commodity", "horizon"]
    b = _replicate_diff(boot).groupby(key)["diff"].agg(
        boot_ci_low=lambda s: s.quantile(0.025), boot_ci_high=lambda s: s.quantile(0.975), n_boot="size")
    out = out.merge(b.reset_index(), on=key, how="left")
    pl = _replicate_diff(placebo).merge(out[key + ["estimate"]], on=key, how="inner")
    if len(pl):
        pl["ge"] = pl["diff"].abs() >= pl["estimate"].abs()
        g = pl.groupby(key).agg(n_ge=("ge", "sum"), n_placebo=("ge", "size")).reset_index()
        g["p_placebo"] = (1 + g["n_ge"]) / (1 + g["n_placebo"])
        out = out.merge(g[key + ["p_placebo", "n_placebo"]], on=key, how="left")
    else:
        out["p_placebo"], out["n_placebo"] = np.nan, np.nan
    out["n_boot"] = out["n_boot"].fillna(0).astype(int)
    out["n_placebo"] = out["n_placebo"].fillna(0).astype(int)
    out["wald_ci_low"], out["wald_ci_high"] = out["ci_low"], out["ci_high"]
    for c in ("boot_ci_low", "boot_ci_high"):                         # merge kosong -> dtype object
        out[c] = pd.to_numeric(out[c], errors="coerce").astype(float)
    out["ci_low"] = np.fmin(out["ci_low"], out["boot_ci_low"])        # fmin/fmax: tanpa bootstrap -> Wald saja
    out["ci_high"] = np.fmax(out["ci_high"], out["boot_ci_high"])
    out["ci_excludes_zero"] = (out["ci_low"] > 0) | (out["ci_high"] < 0)
    return out[COLUMNS]
