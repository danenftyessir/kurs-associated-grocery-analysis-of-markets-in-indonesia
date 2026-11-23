"""Ketidakpastian bersama (bootstrap blok) dan null plasebo geser-melingkar (WP-16). docs/METHODS.md §M1d."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from kagami.stats.resampling import circular_shift, moving_block_indices
from kagami.utils.config import Config

BOOT_OFFSET, PLACEBO_OFFSET = 1601, 1602          # seed = cfg.seed + offset (RNG bootstrap / plasebo)
REP_COLUMNS = ["rep", "level", "unit", "commodity", "driver", "horizon", "estimate"]
KEY = ["level", "unit", "commodity", "driver", "horizon"]
DIFF_OF_LEVEL = {"log_e": "de", "log_brent": "db", "log_dxy": "d_dxy"}     # level penggerak -> selisihnya
PRICE_COLUMNS, UNIT_COLUMNS = ("log_price", "log_price_index"), ("province_id", "region")


def _first(df: pd.DataFrame, options: tuple[str, ...]) -> str:
    return next(c for c in options if c in df.columns)


class _Prepared:
    """Data awal yang dipakai berulang tiap replikasi: panel (selisih log harga), penggerak, dan harga dunia.

    Bootstrap bekerja pada SELISIH (Δp, Δe, Δb, Δw) minggu periode (>= minggu pertama panel) dengan satu vektor
    indeks;
    level dibangun ulang dengan cumsum, sehingga sambungan antarblok tidak membuat lompatan level palsu.
    Buffer penggerak sebelum periode tidak diubah (hanya dipakai untuk lag awal sampel).
    """

    def __init__(self, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None):
        self.d = drivers.sort_values("week").reset_index(drop=True)
        self.pcol, self.ucol = _first(panel, PRICE_COLUMNS), _first(panel, UNIT_COLUMNS)
        self.pos = np.flatnonzero(self.d["week"] >= panel["week"].min())
        self.weeks = self.d["week"].to_numpy()[self.pos]
        wide = panel.pivot(index="week", columns=[self.ucol, "commodity"], values=self.pcol).reindex(self.weeks)
        self.units = wide.columns.get_level_values(0).to_numpy()
        self.coms = wide.columns.get_level_values(1).to_numpy()
        W = wide.to_numpy(dtype=float)
        self.obs = np.isfinite(W)
        self.base = pd.DataFrame(W).bfill().iloc[0].to_numpy()               # level awal tiap seri
        self.dp = np.nan_to_num(np.diff(pd.DataFrame(W).ffill().to_numpy(), axis=0, prepend=np.nan))
        self.world = None
        if world is not None and len(world):
            dw = world.pivot(index="week", columns="commodity", values="dw").reindex(self.d["week"])
            self.world_cols, self.dw = dw.columns.to_numpy(), dw.to_numpy(dtype=float)
            self.world = world

    def n_weeks(self) -> int:
        return len(self.pos)

    def _drivers(self, idx: np.ndarray) -> pd.DataFrame:
        """Penggerak dengan baris periode diganti baris sumber idx; level dibangun ulang dari selisih."""
        d, pos = self.d.copy(), self.pos
        for c in d.columns:
            if c != "week" and c not in DIFF_OF_LEVEL:
                d.iloc[pos, d.columns.get_loc(c)] = self.d[c].to_numpy()[pos][idx]
        for level, diff in DIFF_OF_LEVEL.items():
            if level in d.columns and diff in d.columns:
                start = self.d[level].to_numpy()[pos[0] - 1] if pos[0] > 0 else 0.0
                d.iloc[pos, d.columns.get_loc(level)] = start + np.cumsum(np.nan_to_num(d[diff].to_numpy()[pos]))
        return d

    def draw(self, idx: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
        """(panel_b, drivers_b, world_b) untuk satu vektor indeks minggu `idx` (panjang n_weeks)."""
        W = self.base[None, :] + np.cumsum(self.dp[idx], axis=0)
        W[~self.obs[idx]] = np.nan
        n = W.shape[1]
        panel = pd.DataFrame({"week": np.repeat(self.weeks, n), self.ucol: np.tile(self.units, len(self.weeks)),
                              "commodity": np.tile(self.coms, len(self.weeks)), self.pcol: W.ravel()})
        panel = panel.dropna(subset=[self.pcol]).reset_index(drop=True)
        world = None
        if self.world is not None:
            dw = self.dw.copy()
            dw[self.pos] = dw[self.pos][idx]
            world = pd.DataFrame({"week": np.repeat(self.d["week"].to_numpy(), dw.shape[1]),
                                  "commodity": np.tile(self.world_cols, len(self.d)), "dw": dw.ravel()})
        return panel, self._drivers(idx), world


def _call(estimator: Callable, panel, drivers, world, commodities):
    if world is None:
        return estimator(panel, drivers, commodities=commodities) if commodities else estimator(panel, drivers)
    if commodities:
        return estimator(panel, drivers, world, commodities=commodities)
    return estimator(panel, drivers, world)


def _schedule(cfg: Config, B: int, B_nonfocus: int) -> list[list[str] | None]:
    """Komoditas per replikasi: semua untuk rep <= B_nonfocus, selanjutnya hanya komoditas fokus (None = semua)."""
    focus = cfg.commodity_ids("focus")
    return [None if r < B_nonfocus else focus for r in range(B)]


def _stack(parts: list[pd.DataFrame]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=REP_COLUMNS)
    out = pd.concat(parts, ignore_index=True)
    extra = [c for c in ("se",) if c in out.columns]
    return out[REP_COLUMNS + extra]


def _finished(done: pd.DataFrame | None, n: int) -> tuple[list[pd.DataFrame], set[int]]:
    """Hasil lama (rep < n) yang dipertahankan saat melanjutkan run, dan himpunan rep yang sudah selesai."""
    if done is None or len(done) == 0:
        return [], set()
    kept = done[done["rep"] < n]
    return ([kept] if len(kept) else []), set(int(r) for r in kept["rep"].unique())


def joint_bootstrap(cfg: Config, estimator: Callable[..., pd.DataFrame], panel: pd.DataFrame,
                    drivers: pd.DataFrame, B: int, world: pd.DataFrame | None = None,
                    B_nonfocus: int | None = None, done: pd.DataFrame | None = None,
                    checkpoint: Callable[[pd.DataFrame], None] | None = None,
                    checkpoint_every: int = 25) -> pd.DataFrame:
    """WP-16. B replikasi moving-block (blok 13 minggu) dengan SATU indeks minggu per replikasi
    (stats.resampling.moving_block_indices) yang dipakai untuk semua seri & horizon.

    estimator(panel_b, drivers_b[, world_b][, commodities=...]) -> baris profil.
    -> artefak 'boot_replicates' (rep, level, unit, ...).
    Resampling pada selisih (Δp tiap seri, Δe, Δb, Δw, kalender) di minggu periode; level dibangun ulang
    (lihat _Prepared).
    `world` ikut di-resample dengan indeks yang sama; bila diberikan, estimator menerimanya sebagai argumen ketiga.
    Komputasi: komoditas fokus B=499, lainnya B=params.inference.bootstrap_B_nonfocus (199) -> replikasi setelahnya
    hanya meminta komoditas fokus lewat argumen `commodities`. RNG = cfg.seed + 1601.
    Tahan sesi habis: `done` = hasil run sebelumnya (rep yang sudah ada dilewati; indeks minggu tetap diundi ulang
    dengan seed yang sama sehingga hasil akhir identik dengan run tanpa putus); `checkpoint(hasil)` dipanggil tiap
    `checkpoint_every` replikasi baru.
    """
    p = cfg.params["inference"]
    prep = _Prepared(panel, drivers, world)
    rng = np.random.default_rng(cfg.seed + BOOT_OFFSET)
    sched = _schedule(cfg, B, p["bootstrap_B_nonfocus"] if B_nonfocus is None else B_nonfocus)
    parts, finished = _finished(done, B)
    n_new = 0
    for rep in range(B):
        idx = moving_block_indices(prep.n_weeks(), int(p["block_weeks"]), rng)      # selalu diundi (urutan RNG tetap)
        if rep in finished:
            continue
        pb, db, wb = prep.draw(idx)
        parts.append(_call(estimator, pb, db, wb, sched[rep]).assign(rep=rep))
        n_new += 1
        if (rep + 1) % 25 == 0:
            print(f"[task1] bootstrap {rep + 1}/{B}")
        if checkpoint is not None and n_new % checkpoint_every == 0:
            checkpoint(_stack(parts))
    return _stack(parts)


def _rolled(drivers: pd.DataFrame, world: pd.DataFrame | None, s: int) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    d = drivers.sort_values("week").reset_index(drop=True).copy()
    de = np.roll(d["de"].to_numpy(), s)
    d["de"], d["de_pos"], d["de_neg"] = de, np.clip(de, 0, None), np.clip(de, None, 0)
    d["log_e"] = d["log_e"].to_numpy()[0] + np.cumsum(np.nan_to_num(de))
    w = None
    if world is not None and len(world):
        w = world.sort_values(["commodity", "week"]).reset_index(drop=True).copy()
        w["dw"] = w.groupby("commodity")["dw"].transform(lambda x: np.roll(x.to_numpy(), s))
    return d, w


def circular_placebo(cfg: Config, statistic: Callable[..., pd.DataFrame],
                     panel: pd.DataFrame, drivers: pd.DataFrame, R: int, world: pd.DataFrame | None = None,
                     R_nonfocus: int | None = None, done: pd.DataFrame | None = None,
                     checkpoint: Callable[[pd.DataFrame], None] | None = None,
                     checkpoint_every: int = 25) -> pd.DataFrame:
    """WP-16. Geser de & dw sejauh s >= 52 minggu (np.roll) terhadap harga, hitung ulang profil.

    statistic(panel, drivers_shifted[, world_shifted][, commodities=...]) -> baris profil (nasional + deviasi
    provinsi; provinsi cukup h ∈ params.lp.key_horizons agar ukuran file wajar). -> artefak 'placebo_stats'
    (rep, level, unit, commodity, driver, horizon, estimate; kolom ekstra `se` dibawa bila ada). Q/τ²/silhouette
    plasebo dihitung di Task 2.
    s ∈ [placebo_min_shift_weeks, T - min] (stats.resampling.circular_shift) atas seluruh grid penggerak;
    harga tidak digeser, log_e dibangun ulang dari de yang digeser; de_pos/de_neg diturunkan dari de.
    RNG = cfg.seed + 1602. `done`/`checkpoint` seperti joint_bootstrap (melanjutkan run yang terputus).
    """
    p = cfg.params["inference"]
    rng = np.random.default_rng(cfg.seed + PLACEBO_OFFSET)
    n = len(drivers)
    sched = _schedule(cfg, R, p["bootstrap_B_nonfocus"] if R_nonfocus is None else R_nonfocus)
    parts, finished = _finished(done, R)
    n_new = 0
    for rep in range(R):
        s = circular_shift(n, int(p["placebo_min_shift_weeks"]), rng)               # selalu diundi (urutan RNG tetap)
        if rep in finished:
            continue
        db, wb = _rolled(drivers, world, s)
        parts.append(_call(statistic, panel, db, wb, sched[rep]).assign(rep=rep))
        n_new += 1
        if (rep + 1) % 25 == 0:
            print(f"[task1] plasebo {rep + 1}/{R}")
        if checkpoint is not None and n_new % checkpoint_every == 0:
            checkpoint(_stack(parts))
    return _stack(parts)


def bootstrap_ci(profiles: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """WP-16. Ganti ci_low/ci_high dengan persentil bootstrap bila lebih lebar dari ±1.96·se.

    Persentil 2,5 dan 97,5 estimasi replikasi per (level, unit, commodity, driver, horizon). Baris tanpa replikasi
    tidak berubah; baris tanpa se (PT) memakai persentil saja (METHODS §M1.2). Interval tidak pernah menyempit.
    """
    q = (reps.groupby(KEY)["estimate"].quantile([0.025, 0.975]).unstack().rename(columns={0.025: "_lo", 0.975: "_hi"})
         .reset_index())
    out = profiles.merge(q, on=KEY, how="left")
    out["ci_low"] = np.fmin(out["ci_low"], out["_lo"])          # fmin/fmax: NaN diabaikan, sisi lain yang dipakai
    out["ci_high"] = np.fmax(out["ci_high"], out["_hi"])
    return out.drop(columns=["_lo", "_hi"])
