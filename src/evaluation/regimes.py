"""E2 (eksploratif): profil respons per rezim HET/HAP (PREREGISTRATION §2, D-124). docs/METHODS.md §M3.

Rezim = selang di antara tanggal penetapan/perubahan harga acuan konsumen (HET, HAP, HAP konsumen) yang terverifikasi
untuk satu komoditas. Per rezim, LP nasional (spesifikasi utama) diestimasi ulang hanya pada observasi yang seluruh
jendela datanya berada di dalam rezim (aturan sub-sampel Tier 1, D-111). Eksploratif. Interval dikalibrasi plasebo
geser-melingkar karena SE cluster minggu terlalu sempit pada rezim pendek (D-127).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from joblib import Parallel, delayed, effective_n_jobs

from kagami.evaluation.inference import _rolled
from kagami.evaluation.robustness import _restrict, _window_ok
from kagami.models import local_projection as lp
from kagami.stats.meta import bh_fdr
from kagami.stats.resampling import circular_shift
from kagami.utils.config import Config

CONSUMER_INSTRUMENTS = ("HET", "HAP", "HAP_konsumen")   # harga acuan di tingkat konsumen (bukan HAP produsen)
REGIME_COLUMNS = ["commodity", "regime_id", "regime_start", "regime_end", "driver", "horizon", "estimate",
                  "ci_low", "ci_high", "n_weeks"]
_EXTRA = ["label", "se", "n_obs", "baseline_estimate", "baseline_in_ci", "crit", "p_placebo", "q_fdr", "n_placebo"]
_KEY = ["commodity", "regime_id", "driver", "horizon"]
_PLACEBO_OFFSET = 2401      # rng = default_rng(seed + 2401): pergeseran plasebo E2 (CLAUDE.md §15)
_Z = 1.96


def regulation_changes(cfg: Config, regulation: pd.DataFrame) -> pd.DataFrame:
    """Tanggal penetapan/perubahan harga acuan konsumen per komoditas -> commodity, change_date, regulation.

    Baris dipakai bila: in_scope, instrument ∈ CONSUMER_INSTRUMENTS, start_date ada, verification ≠ 'unverified'
    (setting panel Bapanas dan relaksasi tanpa dasar tertulis tidak menjadi batas rezim), dan tanggal berada di
    params.period (start .. freeze). Beberapa baris pada tanggal yang sama digabung (nama regulasi dipisah '; ').
    """
    per = cfg.params["period"]
    r = regulation.copy()
    r["start_date"] = pd.to_datetime(r["start_date"], errors="coerce")
    ok = (r["in_scope"].astype(str).str.lower().isin(["true", "1"])
          & r["instrument"].isin(CONSUMER_INSTRUMENTS)
          & r["start_date"].notna()
          & (r["verification"].astype(str) != "unverified")
          & r["start_date"].between(pd.Timestamp(per["start"]), pd.Timestamp(per["freeze"])))
    r = r.loc[ok]
    out = (r.groupby(["commodity", "start_date"])["regulation"]
           .agg(lambda s: "; ".join(dict.fromkeys(str(x) for x in s)))
           .reset_index().rename(columns={"start_date": "change_date"}))
    return out.sort_values(["commodity", "change_date"]).reset_index(drop=True)


def regime_table(cfg: Config, changes: pd.DataFrame) -> pd.DataFrame:
    """Rezim per komoditas dari tanggal perubahan -> commodity, regime_id, regime_start, regime_end, label.

    Rezim 0 = params.period.start .. sehari sebelum perubahan pertama (label "sebelum <regulasi pertama>"; rezim ini
    belum tentu tanpa harga acuan karena tabel regulasi baru mencakup 2020+); rezim k = tanggal perubahan ke-k ..
    sehari sebelum perubahan berikutnya (atau params.period.freeze).
    """
    per = cfg.params["period"]
    start, freeze = pd.Timestamp(per["start"]), pd.Timestamp(per["freeze"])
    rows = []
    for com, g in changes.groupby("commodity", sort=True):
        dates = list(g["change_date"])
        regs = list(g["regulation"])
        starts = [start, *dates]
        ends = [d - pd.Timedelta(days=1) for d in dates] + [freeze]
        labels = [f"sebelum {regs[0]}", *regs]
        for k, (a, b, lab) in enumerate(zip(starts, ends, labels)):
            if b >= a:
                rows.append({"commodity": com, "regime_id": k, "regime_start": a, "regime_end": b, "label": lab})
    return pd.DataFrame(rows, columns=["commodity", "regime_id", "regime_start", "regime_end", "label"])


def _fit_regimes(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None,
                 regimes: pd.DataFrame, coms: list[str], H: list[int], L: int, elig: pd.DataFrame | None,
                 baseline: bool = True) -> list[dict]:
    """Estimasi LP nasional per (komoditas, h, rezim) -> baris estimate/se (+ baseline sampel penuh bila diminta)."""
    rows: list[dict] = []
    for com in coms:
        reg = regimes[regimes["commodity"] == com]
        for h in H:
            D = lp.build_design(cfg, panel, drivers, world, com, h, L, elig=elig)
            base = ({r.driver: r.estimate for r in lp.fit_lp(cfg, D).itertuples(index=False)} if baseline else {})
            k = len(lp.regressors(D))
            for g in reg.itertuples(index=False):
                ex = [(pd.Timestamp.min, g.regime_start - pd.Timedelta(days=1)),
                      (g.regime_end + pd.Timedelta(days=1), pd.Timestamp.max)]
                mask = _window_ok(D["week"], L, h, ex)
                if D.loc[mask, "week"].nunique() <= k:
                    continue
                for r in lp.fit_lp(cfg, _restrict(D, mask)).itertuples(index=False):
                    if r.driver not in ("e", "w"):
                        continue
                    rows.append({"commodity": com, "regime_id": g.regime_id, "regime_start": g.regime_start,
                                 "regime_end": g.regime_end, "label": g.label, "driver": r.driver, "horizon": h,
                                 "estimate": r.estimate, "se": r.se, "n_weeks": r.n_weeks, "n_obs": r.n_obs,
                                 "baseline_estimate": base.get(r.driver, np.nan)})
    return rows


def _placebo_t(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None,
               regimes: pd.DataFrame, coms: list[str], H: list[int], L: int, elig: pd.DataFrame | None,
               shifts: list[int]) -> pd.DataFrame:
    """t* = estimate/se per rezim di bawah null untuk beberapa pergeseran de & dw (satu tugas paralel)."""
    parts = []
    for s in shifts:
        db, wb = _rolled(drivers, world, int(s))
        rows = _fit_regimes(cfg, panel, db, wb, regimes, coms, H, L, elig, baseline=False)
        if rows:
            r = pd.DataFrame(rows)
            parts.append(r[_KEY].assign(t=r["estimate"] / r["se"]))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=[*_KEY, "t"])


def regime_profiles(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None,
                    regulation: pd.DataFrame, *, elig: pd.DataFrame | None = None,
                    commodities: list[str] | None = None, horizons: list[int] | None = None,
                    placebo_R: int | None = None, n_jobs: int = -1) -> pd.DataFrame:
    """E2. β_e(h) dan ω(h) nasional per rezim HET/HAP -> artefak 'regime_profiles'.

    h = params.lp.key_horizons; L = params.lp.lags. Observasi minggu t masuk rezim bila jendela datanya [t-(L+1), t+h]
    seluruhnya di dalam rezim (robustness._window_ok). Rezim yang jumlah minggunya tidak melebihi jumlah regresor
    dilewati. baseline_estimate = estimasi sampel penuh; baseline_in_ci = estimasi penuh di dalam interval rezim.
    Interval (D-127): estimate ± crit·se, crit = max(1,96; persentil 95 |t*|), t* = estimate/se rezim yang sama di bawah
    R = params.inference.placebo_R geser-melingkar de & dw (≥ placebo_min_shift_weeks; inference._rolled; RNG =
    cfg.seed + 2401). p_placebo = (1 + #|t*| ≥ |t|)/(1 + n_placebo); q_fdr = BH atas semua baris artefak (deskriptif).
    placebo_R = 0 -> crit = 1,96, p/q NaN. n_jobs diteruskan ke joblib.
    """
    pl = cfg.params["lp"]
    L = int(pl["lags"])
    H = [int(h) for h in (horizons if horizons is not None else pl["key_horizons"])]
    regimes = regime_table(cfg, regulation_changes(cfg, regulation))
    present = set(panel["commodity"].unique())
    coms = [c for c in (commodities or cfg.commodity_ids()) if c in present and c in set(regimes["commodity"])]
    out = pd.DataFrame(_fit_regimes(cfg, panel, drivers, world, regimes, coms, H, L, elig),
                       columns=[c for c in REGIME_COLUMNS + _EXTRA if c not in
                                ("ci_low", "ci_high", "baseline_in_ci", "crit", "p_placebo", "q_fdr", "n_placebo")])
    pinf = cfg.params["inference"]
    R = int(pinf["placebo_R"] if placebo_R is None else placebo_R)
    out["crit"], out["p_placebo"], out["n_placebo"] = _Z, np.nan, 0
    if R > 0 and len(out):
        rng = np.random.default_rng(cfg.seed + _PLACEBO_OFFSET)
        shifts = [circular_shift(len(drivers), int(pinf["placebo_min_shift_weeks"]), rng) for _ in range(R)]
        n_chunks = min(R, 4 * effective_n_jobs(n_jobs))            # beberapa geser per tugas: kirim panel sekali per tugas
        chunks = [list(c) for c in np.array_split(np.asarray(shifts), n_chunks) if len(c)]
        print(f"[task3] E2 plasebo: {R} geser, {len(chunks)} tugas")
        null = pd.concat(Parallel(n_jobs=n_jobs)(delayed(_placebo_t)(cfg, panel, drivers, world, regimes, coms, H, L,
                                                                     elig, c) for c in chunks), ignore_index=True)
        null = null[np.isfinite(null["t"].astype(float))]
        t_obs = (out["estimate"] / out["se"]).abs()
        m = out[_KEY].assign(_t=t_obs.to_numpy()).merge(null, on=_KEY, how="left")
        m["ge"] = m["t"].abs() >= m["_t"]
        agg = m.groupby(_KEY).agg(n_placebo=("t", "count"), n_ge=("ge", "sum"),
                                  crit=("t", lambda s: float(np.nanquantile(s.abs(), 0.95)) if s.notna().any()
                                        else np.nan)).reset_index()
        out = out.drop(columns=["crit", "p_placebo", "n_placebo"]).merge(agg, on=_KEY, how="left")
        out["crit"] = np.fmax(out["crit"], _Z)
        out["p_placebo"] = np.where(out["n_placebo"] > 0, (1 + out["n_ge"]) / (1 + out["n_placebo"]), np.nan)
        out = out.drop(columns="n_ge")
    out["ci_low"] = out["estimate"] - out["crit"] * out["se"]
    out["ci_high"] = out["estimate"] + out["crit"] * out["se"]
    be, lo, hi = out["baseline_estimate"], out["ci_low"], out["ci_high"]
    out["baseline_in_ci"] = np.where(np.isfinite(be) & np.isfinite(lo), (lo <= be) & (be <= hi), np.nan)
    ok = out["p_placebo"].notna()
    out["q_fdr"] = np.nan
    if ok.any():
        out.loc[ok, "q_fdr"] = bh_fdr(out.loc[ok, "p_placebo"].to_numpy())
    out["n_placebo"] = out["n_placebo"].fillna(0).astype(int)
    out = out[REGIME_COLUMNS + _EXTRA]
    return out.sort_values(["commodity", "driver", "horizon", "regime_id"]).reset_index(drop=True)
