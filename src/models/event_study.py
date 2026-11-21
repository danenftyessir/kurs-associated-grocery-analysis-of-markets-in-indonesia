"""Event study per episode depresiasi (WP-14). docs/METHODS.md §M1.3."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from kagami.utils.config import Config
from kagami.stats.resampling import placebo_windows

_RNG_OFFSET = 1401   # offset RNG khusus placebo_bands (CLAUDE.md §15)
_EXCLUDE_WEEKS = 12  # minggu di sekitar episode yang tidak boleh jadi awal plasebo (METHODS §M1.3)


def _wide(panel: pd.DataFrame, elig: pd.DataFrame | None) -> tuple[dict[str, pd.DataFrame], str]:
    """Panel -> {komoditas: matriks minggu x unit log harga} pada grid mingguan lengkap."""
    if "region" in panel.columns and "province_id" not in panel.columns:
        unit, price = "region", "log_price_index"
    else:
        unit, price = "province_id", "log_price"
        if elig is not None:
            ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
            panel = panel.merge(ok, on=["province_id", "commodity"], how="inner")
    weeks = pd.date_range(panel["week"].min(), panel["week"].max(), freq="W-MON")
    out = {}
    for com, g in panel.groupby("commodity", sort=False):
        out[com] = g.pivot_table(index="week", columns=unit, values=price, aggfunc="first").reindex(weeks)
    return out, unit


def _paths(P: pd.DataFrame, starts: pd.DatetimeIndex, H: int) -> np.ndarray:
    """Δ log harga p(s+h) - p(s-1), h = 0..H -> array (start, h, unit); NaN bila di luar panel."""
    pos = P.index.get_indexer(starts)
    X = P.to_numpy(float)
    n = len(X)
    out = np.full((len(starts), H + 1, X.shape[1]), np.nan)
    for i, s in enumerate(pos):
        if s < 1:
            continue
        hi = min(H, n - 1 - s)
        if hi < 0:
            continue
        out[i, : hi + 1] = X[s : s + hi + 1] - X[s - 1]
    return out


def _aggregate(paths: np.ndarray, units: pd.Index, level: str) -> tuple[np.ndarray, list]:
    """National: rerata lintas unit (yang teramati di kedua minggu) -> unit 'ALL'; region: per unit."""
    if level == "national":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)   # unit kosong di suatu minggu -> NaN
            return np.nanmean(paths, axis=2)[:, :, None], ["ALL"]
    return paths, list(units)


def _episodes_in_panel(episodes: pd.DataFrame) -> pd.DataFrame:
    eps = episodes.copy()
    eps["start_week"] = pd.to_datetime(eps["start_week"])
    eps["end_week"] = pd.to_datetime(eps["end_week"])
    if "in_period" in eps.columns:
        eps = eps[eps["in_period"].astype(bool)]
    return eps.reset_index(drop=True)


def event_paths(cfg: Config, panel: pd.DataFrame, episodes: pd.DataFrame, level: str, *,
                elig: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-14. Perubahan log harga 0..12 minggu setelah start_week tiap episode (level national|region).

    dlog_price(h) = p(start_week + h) - p(start_week - 1), h = 0..max(params.lp.horizons) (METHODS §M1.3).
    panel   : panel_weekly (provinsi; level='national') atau panel_weekly_region (level='region').
    National = rerata lintas provinsi eligible dari selisih per provinsi (hanya provinsi teramati di kedua minggu,
    sehingga tahan perubahan komposisi). Hanya episode `in_period`. Horizon di luar panel -> NaN (tidak dibuang).
    -> episode_id, level, unit, commodity, horizon, dlog_price.
    """
    H = int(max(cfg.params["lp"]["horizons"]))
    eps = _episodes_in_panel(episodes)
    wide, _ = _wide(panel, elig)
    starts = pd.DatetimeIndex(eps["start_week"])
    frames = []
    for com in [c for c in cfg.commodity_ids() if c in wide]:
        P = wide[com]
        arr, units = _aggregate(_paths(P, starts, H), P.columns, level)
        e_i, h_i, u_i = np.meshgrid(np.arange(len(starts)), np.arange(H + 1), np.arange(len(units)), indexing="ij")
        frames.append(pd.DataFrame({"episode_id": eps["episode_id"].to_numpy()[e_i.ravel()], "level": level,
                                    "unit": np.asarray(units, dtype=object)[u_i.ravel()], "commodity": com,
                                    "horizon": h_i.ravel(), "dlog_price": arr.ravel()}))
    cols = ["episode_id", "level", "unit", "commodity", "horizon", "dlog_price"]
    return pd.concat(frames, ignore_index=True)[cols] if frames else pd.DataFrame(columns=cols)


def placebo_starts(cfg: Config, weeks: pd.DatetimeIndex, episodes: pd.DataFrame) -> pd.DatetimeIndex:
    """WP-14. Kandidat awal plasebo: minggu panel dengan s-1 dan s+H di dalam panel, di luar [start-12, end+12]
    setiap episode (semua episode, termasuk yang di luar periode)."""
    H = int(max(cfg.params["lp"]["horizons"]))
    ok = np.zeros(len(weeks), bool)
    ok[1 : max(len(weeks) - H, 1)] = True
    pad = pd.Timedelta(weeks=_EXCLUDE_WEEKS)
    for s, e in zip(pd.to_datetime(episodes["start_week"]), pd.to_datetime(episodes["end_week"])):
        ok &= ~((weeks >= s - pad) & (weeks <= e + pad))
    return weeks[ok]


def placebo_bands(cfg: Config, panel: pd.DataFrame, episodes: pd.DataFrame, level: str, *,
                  elig: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-14. 499 jendela plasebo dari minggu tanpa episode (stats.resampling.placebo_windows).

    -> placebo_lo/hi (persentil 2.5/97.5) dan placebo_p (proporsi |plasebo| >= |aktual|) per horizon.
    Gabung dengan event_paths -> artefak 'events'.
    Satu set awal plasebo (params.inference.event_placebo_windows, RNG seed + 1401) dipakai bersama untuk semua
    komoditas & unit. placebo_p = (1 + #|plasebo| >= |aktual|) / (1 + n_plasebo_valid) (METHODS §M1.3).
    Kolom ekstra: n_placebo, placebo_median (pusat null; dipakai validasi V2/V4, D-114).
    """
    H = int(max(cfg.params["lp"]["horizons"]))
    n = int(cfg.params["inference"]["event_placebo_windows"])
    actual = event_paths(cfg, panel, episodes, level, elig=elig)
    wide, _ = _wide(panel, elig)
    any_P = next(iter(wide.values()))
    rng = np.random.default_rng(cfg.seed + _RNG_OFFSET)
    starts = pd.DatetimeIndex(placebo_windows(placebo_starts(cfg, any_P.index, episodes).to_numpy(), n, rng))
    bands = []
    for com, P in wide.items():
        arr, units = _aggregate(_paths(P, starts, H), P.columns, level)        # (n, h, unit)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            lo, med, hi = np.nanpercentile(arr, [2.5, 50, 97.5], axis=0)
        h_i, u_i = np.meshgrid(np.arange(H + 1), np.arange(len(units)), indexing="ij")
        b = pd.DataFrame({"unit": np.asarray(units, dtype=object)[u_i.ravel()], "commodity": com,
                          "horizon": h_i.ravel(), "placebo_lo": lo.ravel(), "placebo_hi": hi.ravel(),
                          "placebo_median": med.ravel()})
        b["_null"] = [arr[:, h, u] for h, u in zip(h_i.ravel(), u_i.ravel())]
        bands.append(b)
    out = actual.merge(pd.concat(bands, ignore_index=True), on=["unit", "commodity", "horizon"], how="left")

    def p_value(row) -> tuple[float, int]:
        null = row["_null"]
        null = null[np.isfinite(null)]
        if not np.isfinite(row["dlog_price"]) or len(null) == 0:
            return np.nan, len(null)
        return (1 + np.sum(np.abs(null) >= abs(row["dlog_price"]))) / (1 + len(null)), len(null)

    pv = out.apply(p_value, axis=1, result_type="expand")
    out["placebo_p"], out["n_placebo"] = pv[0], pv[1].astype(int)
    return out[["episode_id", "level", "unit", "commodity", "horizon", "dlog_price", "placebo_lo", "placebo_hi",
                "placebo_p", "n_placebo", "placebo_median"]]
