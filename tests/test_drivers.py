"""WP-05: penggerak nasional mingguan & harga dunia dalam rupiah."""

import numpy as np
import pandas as pd
import pytest

from kagami.data.drivers import build_national_drivers, build_world_prices, driver_weeks


@pytest.fixture(scope="module")
def weeks(cfg):
    return driver_weeks(cfg)


def _daily(weeks, value_of_week, drop_week=None):
    days = pd.bdate_range(weeks[0], weeks[-1] + pd.Timedelta(days=4))
    wk = days - pd.to_timedelta(days.weekday, unit="D")
    idx = weeks.get_indexer(wk)
    df = pd.DataFrame({"date": days, "v": [value_of_week(i) for i in idx]})
    if drop_week is not None:
        df = df[wk != weeks[drop_week]]
    return df


def test_grid_has_buffer(cfg, weeks):
    assert weeks[0] == pd.Timestamp("2017-01-02")            # 52 minggu sebelum 2018-01-01
    assert weeks[-1] == pd.Timestamp("2026-11-16")
    assert (weeks.weekday == 0).all()


def test_national_drivers(cfg, weeks):
    j = _daily(weeks, lambda i: 10000 * np.exp(0.001 * i), drop_week=10).rename(columns={"v": "idr_per_usd"})
    b = _daily(weeks, lambda i: 80 * np.exp(-0.002 * i)).rename(columns={"v": "value"})
    x = _daily(weeks, lambda i: 100.0).rename(columns={"v": "value"})
    d = build_national_drivers(cfg, j, b, x).set_index("week")
    assert np.allclose(d["de"].iloc[1:10], 0.001)
    assert d["e_filled"].iloc[10] and d["de"].iloc[10] == 0          # minggu libur: level diteruskan
    assert np.isclose(d["de"].iloc[11], 0.002)                      # perubahan terkumpul di minggu berikutnya
    assert np.isnan(d["de"].iloc[0])                                 # minggu pertama grid: belum ada Δ
    assert (d["de_pos"].iloc[1:] >= 0).all() and (d["de_neg"].iloc[1:] == 0).all()
    assert np.allclose(d["db"].iloc[1:], -0.002) and np.allclose(d["d_dxy"].iloc[1:], 0)
    assert (d["month"] == d.index.month).all()


def test_idulfitri_window(cfg, weeks):
    x = _daily(weeks, lambda i: 100.0)
    d = build_national_drivers(cfg, x.rename(columns={"v": "idr_per_usd"}), x.rename(columns={"v": "value"}),
                               x.rename(columns={"v": "value"})).set_index("week")["idf_rel_week"]
    assert d.loc["2024-04-08"] == 0                                 # Idulfitri 2024-04-10 (Rabu)
    assert d.loc["2024-02-26"] == -6 and d.loc["2024-05-06"] == 4
    assert np.isnan(d.loc["2024-02-19"]) and np.isnan(d.loc["2024-05-13"])
    per_year = d.dropna().groupby(d.dropna().index.year).size()
    assert (per_year == 11).all() and len(per_year) == 10          # 2017..2026


def test_world_prices(cfg, weeks):
    months = pd.date_range(weeks[0].to_period("M").to_timestamp(), weeks[-1], freq="MS")
    k = np.arange(len(months))
    series = {"Palm oil": 1000 * np.exp(0.01 * k), "Maize": np.full(len(k), 200.0),
              "Soybean meal": np.full(len(k), 400.0), "Rice, Thai 5%": np.full(len(k), 500.0),
              "Sugar, world": np.full(len(k), 0.4), "Beef": np.full(len(k), 5.0)}
    ps = pd.concat([pd.DataFrame({"month": months, "series": s, "usd_price": v}) for s, v in series.items()])
    ps = ps[~((ps["series"] == "Beef") & (ps["month"] == "2024-03-01"))]          # komponen kosong
    j = _daily(weeks, lambda i: 15000.0).rename(columns={"v": "idr_per_usd"})
    w = build_world_prices(cfg, ps, j)

    with_peer = {c for c, v in cfg.commodities.items() if v["pinksheet"]}
    assert set(w["commodity"]) == with_peer and "bawang_putih" not in with_peer
    mg = w[w["commodity"] == "minyak_goreng"].set_index("week")
    m_idx = mg["month"].map({m: i for i, m in enumerate(months)})
    assert np.allclose(mg["log_w_idr"], np.log(1000) + 0.01 * m_idx + np.log(15000))
    new_month = mg["month"].ne(mg["month"].shift())
    assert (mg.loc[~new_month, "dw"] == 0).all() and np.allclose(mg.loc[new_month, "dw"].iloc[1:], 0.01)
    ay = w[w["commodity"] == "daging_ayam"]
    assert np.allclose(ay["log_w_usd"], 0.6 * np.log(200) + 0.4 * np.log(400))
    sapi = w[w["commodity"] == "daging_sapi"].set_index("week")
    assert sapi.loc["2024-03-04":"2024-03-25", "log_w_usd"].isna().all()
    avail = mg.groupby("month")["available_at"].first()
    assert avail[pd.Timestamp("2024-03-01")] == pd.Timestamp("2024-04-02")
    assert avail[pd.Timestamp("2024-08-01")] == pd.Timestamp("2024-09-03")   # 1 Sep = Minggu
