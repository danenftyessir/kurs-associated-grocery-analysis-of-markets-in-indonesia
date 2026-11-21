"""Generator data sintetis berskema artefak Task 1 (bukan tes; dipakai tes WP-15/16/17/19-24).

SEMUA keluaran berlabel dummy (`df.attrs["dummy"] = True`): tidak boleh masuk makalah, app final, atau results/
(PEMBAGIAN_TUGAS §2.2).
Jawaban yang ditanam dikembalikan bersama data agar estimator bisa diuji pemulihannya.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config

HORIZONS = range(13)


def _dummy(df: pd.DataFrame) -> pd.DataFrame:
    df.attrs["dummy"] = True
    return df


def synthetic_task1_panel(cfg: Config, n_weeks: int = 300, commodities: list[str] | None = None,
                          beta: dict[str, float] | None = None, delta: dict[int, float] | None = None,
                          noise: float = 0.002, seed: int = 0,
                          n_provinces: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """-> (panel_weekly, drivers, truth) dengan model dp(i,r,t) = (beta_i + delta_r) * de_t + eps.

    panel_weekly: kolom artefak (week, province_id, commodity, price, log_price, n_days, status), 34 provinsi.
    drivers: week, de (iid N(0, 0,008)), de_pos, de_neg, episode = 0.
    truth: {"beta": {komoditas: b}, "delta": {province_id: d}} dengan Σ delta = 0 (deviasi lintas provinsi).
    Respons kumulatif y^(h) = p_{t+h} - p_{t-1} terhadap de_t = beta + delta untuk semua h (langkah seketika).
    """
    rng = np.random.default_rng(cfg.seed + 7001)
    commodities = commodities or list(cfg.commodities)[:3]
    provinces = cfg.regions["province_id"].astype(int).tolist()[:n_provinces]
    beta = beta or {c: 0.1 * (k + 1) for k, c in enumerate(commodities)}
    if delta is None:
        raw = rng.normal(0, 0.05, len(provinces))
        delta = dict(zip(provinces, raw - raw.mean()))
    weeks = pd.date_range("2018-01-01", periods=n_weeks, freq="W-MON")
    de = rng.normal(0, 0.008, n_weeks)
    drivers = pd.DataFrame({"week": weeks, "de": de, "de_pos": np.clip(de, 0, None),
                            "de_neg": np.clip(de, None, 0), "episode": 0})
    rows = []
    rng = np.random.default_rng(seed)
    for c in commodities:
        for r in provinces:
            dp = (beta[c] + delta[r]) * de + rng.normal(0, noise, n_weeks)
            logp = np.log(10000.0) + np.cumsum(dp)
            rows.append(pd.DataFrame({"week": weeks, "province_id": r, "commodity": c, "price": np.exp(logp),
                                      "log_price": logp, "n_days": 5, "status": "observed"}))
    panel = pd.concat(rows, ignore_index=True)
    return _dummy(panel), _dummy(drivers), {"beta": beta, "delta": delta}


def synthetic_national_profiles(cfg: Config, commodities: list[str] | None = None, tau: float = 3.0,
                                seed: int = 0) -> pd.DataFrame:
    """Artefak `profiles` level=national: respons e & w menuju beta_c (1 - exp(-h/tau)), PT = beta/gamma, SE kecil.

    beta_c = 0,05 * (indeks komoditas + 1) untuk e; 0,5 * itu untuk w; gamma = 1; interval = estimate ± 1,96 se.
    """
    rng = np.random.default_rng(cfg.seed + 7002 + seed)
    commodities = commodities or list(cfg.commodities)
    rows = []
    for k, c in enumerate(commodities):
        for driver, scale in (("e", 0.05), ("w", 0.025), ("e_pos", 0.05), ("e_neg", 0.05)):
            for h in HORIZONS:
                est = scale * (k + 1) * (1 - np.exp(-h / tau))
                se = 0.01 + 0.002 * h + abs(rng.normal(0, 0.0005))
                rows.append(("national", "ALL", c, driver, h, est, se, est - 1.96 * se, est + 1.96 * se, 450, False))
        for h in HORIZONS:
            est = 0.05 * (k + 1) * (1 - np.exp(-h / tau))              # PT = beta / gamma, gamma = 1
            rows.append(("national", "ALL", c, "PT", h, est, 0.02, est - 0.0392, est + 0.0392, 450, False))
    cols = ["level", "unit", "commodity", "driver", "horizon", "estimate", "se", "ci_low", "ci_high",
            "n_weeks", "shrunk"]
    return _dummy(pd.DataFrame(rows, columns=cols))


def synthetic_task4_inputs(cfg: Config, n_weeks: int = 260, lag: int = 5, beta: float = 0.5, noise: float = 0.002,
                           n_provinces: int = 6, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """-> (panel_weekly, drivers_weekly, world_prices_weekly) dummy untuk Task 4.

    Harga bereaksi terhadap kurs dengan jeda: dp_t = beta * de_{t-lag} + eps, sehingga perubahan 4 minggu ke depan
    dapat diprediksi dari de lampau (fitur kurs M2 menurunkan MAE vs M1). Harga dunia: komoditas pertama, bulanan,
    available_at = hari ke-2 bulan berikutnya (as-of).
    """
    panel, drv, _ = synthetic_task1_panel(cfg, n_weeks=n_weeks, commodities=list(cfg.commodities)[:2],
                                          n_provinces=n_provinces, noise=noise, seed=seed)
    rng = np.random.default_rng(seed + 1)
    weeks = drv["week"]
    de = drv["de"].to_numpy()
    shared = beta * np.concatenate([np.zeros(lag), de[:-lag]])
    rows = []
    for (r, c), g in panel.groupby(["province_id", "commodity"]):
        dp = shared + rng.normal(0, noise, len(g))
        logp = np.log(10000.0) + np.cumsum(dp)
        rows.append(g.assign(log_price=logp, price=np.exp(logp)))
    panel = _dummy(pd.concat(rows, ignore_index=True))
    brent = np.log(80.0) + np.cumsum(rng.normal(0, 0.02, n_weeks))
    drivers = drv.assign(log_e=np.log(15000.0) + np.cumsum(de), log_brent=brent,
                         month=weeks.dt.month, idf_rel_week=np.nan)
    month = weeks.dt.to_period("M").dt.to_timestamp()
    first = list(cfg.commodities)[0]
    level = pd.Series(np.cumsum(rng.normal(0, 0.01, month.nunique())), index=month.unique())
    world = pd.DataFrame({"week": weeks, "commodity": first, "log_w_idr": month.map(level) + np.log(15000.0),
                          "available_at": month.map(lambda m: m + pd.offsets.MonthBegin(1) + pd.Timedelta(days=1))})
    world["dw"] = world["log_w_idr"].diff()
    return panel, _dummy(drivers), _dummy(world)
