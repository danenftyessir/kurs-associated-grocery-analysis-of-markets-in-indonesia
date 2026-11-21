"""Matriks fitur provinsi untuk clustering Task 2 (WP-19). docs/METHODS.md §M2.2."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.features.response import shrink_deviations
from kagami.utils.config import Config

REP_KEYS = ["level", "unit", "commodity", "driver", "horizon"]


def _zscore(X: np.ndarray) -> np.ndarray:
    """z-score per kolom; kolom tanpa variasi -> 0 (sama dengan evaluation.planted)."""
    X = np.asarray(X, float)
    sd = X.std(axis=0)
    return np.where(sd > 0, (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0), 0.0)


def feature_columns(cfg: Config) -> list[tuple[str, str, int]]:
    """(awalan R|W, komoditas, horizon) fitur clustering: R untuk semua komoditas fokus, W hanya yang berpadanan harga
    dunia (commodities.yaml: pinksheet), pada params.clustering.feature_horizons."""
    hs = [int(h) for h in cfg.params["clustering"]["feature_horizons"]]
    cols = []
    for com in cfg.commodity_ids("focus"):
        cols += [("R", com, h) for h in hs]
        if cfg.commodities[com]["pinksheet"]:
            cols += [("W", com, h) for h in hs]
    return cols


def _name(col: tuple[str, str, int]) -> str:
    return f"{col[0]}{col[2]}_{col[1]}"


def _finish(X: pd.DataFrame, standardize: bool) -> pd.DataFrame:
    X = X.fillna(X.mean())                                   # sel kosong -> rerata kolom (0 setelah z-score)
    X = X.fillna(0.0)
    return pd.DataFrame(_zscore(X.to_numpy()), index=X.index, columns=X.columns) if standardize else X


def feature_matrix(cfg: Config, response_features: pd.DataFrame, standardize: bool = True) -> pd.DataFrame:
    """WP-19. Matriks 34 provinsi x fitur tersusut: R & W pada h ∈ {4,8,12} untuk komoditas fokus.

    Fitur distandardisasi (z-score per kolom); kolom W hanya untuk komoditas berpadanan.
    Sumber = `response_features` level province (respons nasional + δ tersusut, WP-17); index = province_id,
    kolom `R<h>_<komoditas>` / `W<h>_<komoditas>`. Sel kosong diisi rerata kolom. standardize=False -> satuan respons.
    """
    f = response_features[response_features["level"] == "province"]
    f = f.assign(province_id=f["unit"].astype(int))
    data = {}
    for prefix, com, h in feature_columns(cfg):
        col, g = f"{prefix}{h}", f[f["commodity"] == com]
        data[_name((prefix, com, h))] = g.set_index("province_id")[col] if col in g else pd.Series(dtype=float)
    return _finish(pd.DataFrame(data).sort_index(), standardize)


def _rep_matrix(cfg: Config, g: pd.DataFrame, standardize: bool) -> pd.DataFrame:
    """Satu matriks fitur dari baris provinsi satu replikasi: δ tersusut (EB) per (komoditas, driver, h)."""
    g = shrink_deviations(cfg, g.assign(shrunk=False), check_reml=False)
    sh = g[g["shrunk"].astype(bool)]
    sh = sh.assign(province_id=sh["unit"].astype(int))
    data = {}
    for prefix, com, h in feature_columns(cfg):
        drv = "e" if prefix == "R" else "w"
        cell = sh[(sh["commodity"] == com) & (sh["driver"] == drv) & (sh["horizon"] == h)]
        data[_name((prefix, com, h))] = cell.set_index("province_id")["estimate"]
    return _finish(pd.DataFrame(data).sort_index(), standardize)


def replicate_feature_matrices(cfg: Config, replicates: pd.DataFrame, standardize: bool = True) -> list[np.ndarray]:
    """WP-19. placebo_stats / boot_replicates -> satu matriks fitur provinsi per `rep`
    (fitur & standardisasi identik dengan feature_matrix). Dipakai select_k, planted, stabilitas.

    Baris level='province' dengan kolom `se` wajib (D-111; dibawa WP-16). Tiap replikasi disusutkan EB seperti data
    asli (hanya deviasi δ; komponen nasional konstan antar provinsi sehingga hilang setelah z-score).
    standardize=False (untuk planted.recovery_curve, D-112) mengembalikan satuan respons. Urutan = rep menaik;
    baris = province_id menaik.
    """
    prov = replicates[replicates["level"] == "province"]
    if "se" not in prov.columns:
        raise KeyError("replikasi provinsi harus membawa kolom `se` (WP-16, D-111)")
    cols = [_name(c) for c in feature_columns(cfg)]
    out = []
    for _, g in prov.groupby("rep", sort=True):
        out.append(_rep_matrix(cfg, g[REP_KEYS + ["estimate", "se"]], standardize).reindex(columns=cols).to_numpy())
    return out
