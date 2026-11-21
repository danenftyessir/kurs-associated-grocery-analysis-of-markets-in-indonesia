"""Metrik, uji Diebold-Mariano, ablation (WP-27). docs/METHODS.md §M4.

Kontrak masukan (WP-26, `data/interim/forecast_preds.parquet`): origin, horizon, model, province_id ATAU region, commodity,
y_true, y_pred, large_move. Model = MODELS (M0..M3) + ABLATION_MODEL (M2 tanpa kelompok fitur 'fx').
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from kagami.stats.meta import holm
from kagami.stats.regression import diebold_mariano
from kagami.utils.config import Config

ABLATION_MODEL = "M2_nofx"                       # nama model ablation di forecast_preds (kontrak dengan WP-26)
BENCHMARK = "M1"
H5_PATHS = ("direct_import", "imported_input")   # keluarga H5 (PREREGISTRATION; Holm, D-109)
H5_MODEL, H5_HORIZON, H5_SUBSET = "M2", 8, "large_move"
H5_ALPHA = 0.05                                  # α keluarga H5 (PREREGISTRATION §H5; tidak ada kunci di params beku)
EVAL_COLUMNS = ["horizon", "model", "subset", "commodity", "region", "mae", "rmse", "mae_ratio_vs_m1",
                "rmse_ratio_vs_m1", "dm_stat", "dm_p", "n_origins", "n_nonoverlap"]
ABLATION_COLUMNS = ["horizon", "commodity", "region", "mae_full", "mae_without_fx", "delta_mae"]


# ------------------------------------------------------------------------------------------- bantuan
def n_nonoverlap(origins, horizon_weeks: int) -> int:
    """WP-27. Jumlah origin tak tumpang tindih: pilih rakus dari origin terurut dengan jarak >= h minggu."""
    o = pd.DatetimeIndex(pd.unique(pd.Series(origins))).sort_values()
    n, last = 0, None
    for t in o:
        if last is None or (t - last) >= pd.Timedelta(weeks=horizon_weeks):
            n, last = n + 1, t
    return n


def _with_region(cfg: Config, preds: pd.DataFrame) -> pd.DataFrame:
    if "region" in preds.columns:
        return preds
    reg = cfg.regions[["province_id", "region"]]
    return preds.merge(reg, on="province_id", how="left")


def _cells(cfg: Config, df: pd.DataFrame) -> list[tuple[str, str, str, pd.Series]]:
    """Sel evaluasi: (level, commodity, region, mask). level ∈ all | commodity | region | path (H5: komoditas fokus
    per jalur eksposur, label commodity = nama jalur)."""
    out = [("all", "ALL", "ALL", pd.Series(True, index=df.index))]
    for c in sorted(df["commodity"].unique()):
        out.append(("commodity", c, "ALL", df["commodity"] == c))
    for r in sorted(df["region"].dropna().unique()):
        out.append(("region", "ALL", r, df["region"] == r))
    com = cfg.commodities
    for path in H5_PATHS:
        members = [c for c, v in com.items() if v["role"] == "focus" and v["exposure_path"] == path]
        out.append(("path", path, "ALL", df["commodity"].isin(members)))
    return out


def _subsets(cfg: Config, d: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    """Subset origin: all; large_move; case_study = origin di tahun kalender freeze (V2 studi kasus; forecast_preds
    hanya memuat origin dengan outcome lengkap, origin <= freeze - h)."""
    year = pd.Timestamp(cfg.params["period"]["freeze"]).year
    return [("all", d), ("large_move", d[d["large_move"].astype(bool)]),
            ("case_study", d[pd.to_datetime(d["origin"]).dt.year == year])]


def _per_origin_abs(d: pd.DataFrame) -> pd.Series:
    return d.assign(ae=(d["y_true"] - d["y_pred"]).abs()).groupby("origin")["ae"].mean()


def _dm(bench: pd.DataFrame, cand: pd.DataFrame, h: int, step: int) -> tuple[float, float]:
    """DM pada selisih MAE per origin (rerata lintas seri), HAC lag = ceil(h/step) - 1 (origin tumpang tindih) + HLN."""
    a, b = _per_origin_abs(bench), _per_origin_abs(cand)
    j = pd.concat([a.rename("b"), b.rename("c")], axis=1).dropna()
    if len(j) < 3:
        return np.nan, np.nan
    return diebold_mariano(j["b"].to_numpy(), j["c"].to_numpy(), h=math.ceil(h / step), loss="abs")


# ------------------------------------------------------------------------------------------- evaluasi
def evaluate(cfg: Config, preds: pd.DataFrame) -> pd.DataFrame:
    """WP-27. MAE/RMSE per (horizon, model, subset ∈ {all, large_move, case_study}, commodity|ALL|jalur, region|ALL);
    rasio vs M1; DM HAC vs M1 pada deret selisih MAE per origin (stats.regression.diebold_mariano, HAC lag
    ceil(h/origin_step) - 1 karena origin tiap 4 minggu tumpang tindih untuk h = 8; HLN); dm_stat > 0 = lebih akurat
    dari M1. n_origins dan n_nonoverlap (origin berjarak >= h) SELALU dilaporkan. -> artefak 'forecast_eval'.

    Kolom ekstra: level (all | commodity | region | path), n_obs, dm_p_one_sided (H1: lebih akurat dari M1),
    h5_p_holm & h5_reject (hanya baris H5: model M2, h = 8, subset large_move, level path, keluarga = 2 jalur
    {direct_import, imported_input}, p tak terdefinisi = 1 agar ukuran keluarga tetap, dengan koreksi params.forecast.h5_correction pada α keluarga H5_ALPHA = 0,05).
    """
    p = cfg.params["forecast"]
    step = int(p["origin_step_weeks"])
    df = _with_region(cfg, preds)
    rows = []
    for h, dh in df.groupby("horizon", sort=True):
        for subset, ds in _subsets(cfg, dh):
            for level, com, reg, mask in _cells(cfg, ds):
                d = ds[mask.reindex(ds.index, fill_value=False)]
                if d.empty:
                    continue
                bench = d[d["model"] == BENCHMARK]
                e_b = (bench["y_true"] - bench["y_pred"]) if len(bench) else None
                mae_b = float(e_b.abs().mean()) if e_b is not None else np.nan
                rmse_b = float(np.sqrt((e_b ** 2).mean())) if e_b is not None else np.nan
                for model, dm_ in d.groupby("model", sort=True):
                    e = dm_["y_true"] - dm_["y_pred"]
                    mae, rmse = float(e.abs().mean()), float(np.sqrt((e ** 2).mean()))
                    stat, pv = (np.nan, np.nan) if model == BENCHMARK or bench.empty else _dm(bench, dm_, int(h), step)
                    rows.append({"horizon": int(h), "model": model, "subset": subset, "commodity": com, "region": reg,
                                 "level": level, "mae": mae, "rmse": rmse,
                                 "mae_ratio_vs_m1": mae / mae_b if mae_b > 0 else np.nan,
                                 "rmse_ratio_vs_m1": rmse / rmse_b if rmse_b > 0 else np.nan,
                                 "dm_stat": stat, "dm_p": pv,
                                 "dm_p_one_sided": (pv / 2 if stat > 0 else 1 - pv / 2) if np.isfinite(pv) else np.nan,
                                 "n_origins": int(dm_["origin"].nunique()),
                                 "n_nonoverlap": n_nonoverlap(dm_["origin"], int(h)), "n_obs": int(len(dm_))})
    out = pd.DataFrame(rows, columns=EVAL_COLUMNS + ["level", "n_obs", "dm_p_one_sided"])
    out["h5_p_holm"], out["h5_reject"] = np.nan, False
    h5 = ((out["level"] == "path") & (out["model"] == H5_MODEL) & (out["horizon"] == H5_HORIZON)
          & (out["subset"] == H5_SUBSET))
    if h5.any():
        if p["h5_correction"] != "holm":
            raise ValueError(f"koreksi H5 tidak dikenal: {p['h5_correction']}")
        # ukuran keluarga tetap = jumlah jalur H5: p tak terdefinisi dihitung 1 (konservatif), bukan dikeluarkan
        out.loc[h5, "h5_p_holm"] = holm(out.loc[h5, "dm_p_one_sided"].fillna(1.0).to_numpy())
        out.loc[h5, "h5_reject"] = out.loc[h5, "h5_p_holm"] <= H5_ALPHA
    return out


def ablation(cfg: Config, preds: pd.DataFrame) -> pd.DataFrame:
    """WP-27. delta_mae = MAE(M2 tanpa fx) - MAE(M2) per horizon × (komoditas|ALL|jalur) × (wilayah|ALL);
    delta > 0 = fitur kurs & harga dunia menurunkan galat. -> artefak 'ablation'.

    Hanya pasangan (origin, seri) yang ada di kedua model. Kolom ekstra: subset (all | large_move | case_study), level,
    n_origins.
    """
    df = _with_region(cfg, preds)
    unit = "province_id" if "province_id" in df.columns else "region"
    key = ["origin", "horizon", unit, "commodity"]
    full = df[df["model"] == H5_MODEL]
    nofx = df[df["model"] == ABLATION_MODEL]
    if full.empty or nofx.empty:
        raise ValueError(f"ablation butuh model {H5_MODEL} dan {ABLATION_MODEL} di forecast_preds")
    keep = [*key, "y_true", "y_pred", "large_move"] + (["region"] if unit != "region" else [])
    m = full[keep].merge(nofx[[*key, "y_pred"]].rename(columns={"y_pred": "y_nofx"}), on=key, how="inner")
    rows = []
    for h, dh in m.groupby("horizon", sort=True):
        for subset, ds in _subsets(cfg, dh):
            for level, com, reg, mask in _cells(cfg, ds):
                d = ds[mask.reindex(ds.index, fill_value=False)]
                if d.empty:
                    continue
                a = float((d["y_true"] - d["y_pred"]).abs().mean())
                b = float((d["y_true"] - d["y_nofx"]).abs().mean())
                rows.append({"horizon": int(h), "commodity": com, "region": reg, "mae_full": a, "mae_without_fx": b,
                             "delta_mae": b - a, "subset": subset, "level": level,
                             "n_origins": int(d["origin"].nunique())})
    return pd.DataFrame(rows, columns=ABLATION_COLUMNS + ["subset", "level", "n_origins"])
