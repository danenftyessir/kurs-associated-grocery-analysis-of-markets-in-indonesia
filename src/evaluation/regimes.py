"""E2 (eksploratif): profil respons per rezim HET/HAP (PREREGISTRATION §2, D-124). docs/METHODS.md §M3.

Rezim = selang di antara tanggal penetapan/perubahan harga acuan konsumen (HET, HAP, HAP konsumen) yang terverifikasi
untuk satu komoditas. Per rezim, LP nasional (spesifikasi utama) diestimasi ulang hanya pada observasi yang seluruh
jendela datanya berada di dalam rezim (aturan sub-sampel Tier 1, D-111). Deskriptif: tidak ada uji formal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.evaluation.robustness import _restrict, _window_ok
from kagami.models import local_projection as lp
from kagami.utils.config import Config

CONSUMER_INSTRUMENTS = ("HET", "HAP", "HAP_konsumen")   # harga acuan di tingkat konsumen (bukan HAP produsen)
REGIME_COLUMNS = ["commodity", "regime_id", "regime_start", "regime_end", "driver", "horizon", "estimate",
                  "ci_low", "ci_high", "n_weeks"]
_EXTRA = ["label", "se", "n_obs", "baseline_estimate", "baseline_in_ci"]


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


def regime_profiles(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None,
                    regulation: pd.DataFrame, *, elig: pd.DataFrame | None = None,
                    commodities: list[str] | None = None, horizons: list[int] | None = None) -> pd.DataFrame:
    """E2. β_e(h) dan ω(h) nasional per rezim HET/HAP -> artefak 'regime_profiles'.

    h = params.lp.key_horizons; L = params.lp.lags; interval = estimate ± 1,96·SE cluster minggu. Observasi minggu t
    masuk rezim bila jendela datanya [t-(L+1), t+h] seluruhnya di dalam rezim (robustness._window_ok). Rezim yang
    jumlah minggunya tidak melebihi jumlah regresor dilewati (SE tidak teridentifikasi). baseline_estimate = estimasi
    sampel penuh; baseline_in_ci = estimasi penuh berada di dalam interval rezim.
    """
    pl = cfg.params["lp"]
    L = int(pl["lags"])
    H = [int(h) for h in (horizons if horizons is not None else pl["key_horizons"])]
    regimes = regime_table(cfg, regulation_changes(cfg, regulation))
    present = set(panel["commodity"].unique())
    coms = [c for c in (commodities or cfg.commodity_ids()) if c in present and c in set(regimes["commodity"])]
    rows: list[dict] = []
    for com in coms:
        reg = regimes[regimes["commodity"] == com]
        for h in H:
            D = lp.build_design(cfg, panel, drivers, world, com, h, L, elig=elig)
            base = {r.driver: r.estimate for r in lp.fit_lp(cfg, D).itertuples(index=False)}
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
                    lo, hi = r.estimate - 1.96 * r.se, r.estimate + 1.96 * r.se
                    be = base.get(r.driver, np.nan)
                    rows.append({"commodity": com, "regime_id": g.regime_id, "regime_start": g.regime_start,
                                 "regime_end": g.regime_end, "label": g.label, "driver": r.driver, "horizon": h,
                                 "estimate": r.estimate, "se": r.se, "ci_low": lo, "ci_high": hi,
                                 "n_weeks": r.n_weeks, "n_obs": r.n_obs, "baseline_estimate": be,
                                 "baseline_in_ci": bool(lo <= be <= hi) if np.isfinite(be) and np.isfinite(lo) else np.nan})
    out = pd.DataFrame(rows, columns=REGIME_COLUMNS + _EXTRA)
    return out.sort_values(["commodity", "driver", "horizon", "regime_id"]).reset_index(drop=True)
