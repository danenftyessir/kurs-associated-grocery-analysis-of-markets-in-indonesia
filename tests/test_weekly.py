"""WP-03: pemilihan varian dan agregasi mingguan + kode status."""

import numpy as np
import pandas as pd
import pytest

from kagami.data.weekly import _aggregate, aggregate_weekly, eligibility, select_variants
from kagami.utils.dates import week_start


def _series(rows):
    return pd.DataFrame([{"date": pd.Timestamp(d), "province_id": 1, "commodity": "x", "price": float(p)}
                         for d, p in rows])


@pytest.fixture
def synthetic():
    rows = [
        # W1 2024-01-01: 5 hari berbeda -> observed
        ("2024-01-01", 100), ("2024-01-02", 101), ("2024-01-03", 102), ("2024-01-04", 103), ("2024-01-05", 104),
        # W2: 2 hari -> short
        ("2024-01-08", 110), ("2024-01-09", 111),
        # W3: kosong -> missing
        # W4: 5 hari identik -> carry_forward
        ("2024-01-22", 120), ("2024-01-23", 120), ("2024-01-24", 120), ("2024-01-25", 120), ("2024-01-26", 120),
        # W5: rangkaian W4 berlanjut 2 hari lalu berubah -> cf_share 0,4 -> observed
        ("2024-01-29", 120), ("2024-01-30", 120), ("2024-01-31", 121), ("2024-02-01", 122), ("2024-02-02", 123),
        # W6 (2 hari) + W7 (3 hari): rangkaian 5 identik melintasi hari kosong -> carry_forward mengalahkan short
        ("2024-02-05", 130), ("2024-02-06", 130),
        ("2024-02-14", 130), ("2024-02-15", 130), ("2024-02-16", 130),
    ]
    weeks = pd.date_range("2024-01-01", "2024-02-12", freq="W-MON")
    return _aggregate(_series(rows), weeks, provinces=[1, 2], commodities=["x"], run_days=5, short_days=2,
                      last_date=pd.Timestamp("2024-02-18"))


def test_status_codes(synthetic):
    s = synthetic[synthetic["province_id"] == 1].set_index("week")["status"]
    assert s.tolist() == ["observed", "short", "missing", "carry_forward", "observed", "carry_forward",
                          "carry_forward"]


def test_values_and_grid(synthetic):
    p1 = synthetic[synthetic["province_id"] == 1].set_index("week")
    assert p1.loc["2024-01-01", "price"] == 102 and p1.loc["2024-01-01", "n_days"] == 5
    assert np.isclose(p1.loc["2024-01-29", "cf_share"], 0.4)
    assert np.isclose(p1.loc["2024-01-01", "log_price"], np.log(102))
    assert np.isnan(p1.loc["2024-01-15", "price"])
    p2 = synthetic[synthetic["province_id"] == 2]
    assert len(p2) == 7 and (p2["status"] == "missing").all()       # provinsi tanpa data tetap ada di grid


def test_week_start_is_monday():
    w = week_start(pd.Series(pd.to_datetime(["2026-11-21", "2026-11-16", "2018-01-07"])))
    assert w.tolist() == [pd.Timestamp("2026-11-16"), pd.Timestamp("2026-11-16"), pd.Timestamp("2018-01-01")]


def test_select_variants_real(cfg, pihps):
    daily = select_variants(cfg, pihps)
    assert set(daily["commodity"]) == set(cfg.commodities)
    assert daily["province_id"].nunique() == 34
    assert daily["price"].gt(0).all() and daily["price"].notna().all()
    assert daily.groupby("commodity")["variant"].nunique().eq(1).all()


def test_select_variants_missing_raises(cfg, pihps):
    with pytest.raises(ValueError, match="gula_pasir"):
        select_variants(cfg, pihps[pihps["item"] != "Gula Pasir Lokal"])


def test_aggregate_weekly_real_grid(cfg, pihps):
    wk = aggregate_weekly(cfg, select_variants(cfg, pihps))
    n_weeks = wk["week"].nunique()
    assert len(wk) == 34 * 10 * n_weeks
    assert wk["week"].min() == pd.Timestamp("2018-01-01") and wk["week"].max() == pd.Timestamp("2026-11-16")
    assert set(wk["status"]) <= {"observed", "carry_forward", "short", "missing"}
    assert (wk["price"].isna() == (wk["status"] == "missing")).all()


# ----------------------------------------------------------------------------- WP-04
def _panel(missing_by_series):
    """Grid 104 minggu (2024-2025); missing_by_series: {commodity: indeks minggu kosong}."""
    weeks = pd.date_range("2024-01-01", periods=104, freq="W-MON")
    rows = []
    for com, miss in missing_by_series.items():
        for i, w in enumerate(weeks):
            rows.append({"week": w, "province_id": 1, "commodity": com,
                         "status": "missing" if i in miss else "observed"})
    return pd.DataFrame(rows)


def test_eligibility_rules(cfg):
    y2025 = set(range(53, 104, 3))      # 2024 punya 53 Senin -> 2025 = indeks 53..103 (51 minggu); 17 kosong -> 0,667
    el = eligibility(cfg, _panel({
        "full": set(),
        "gap9": set(range(10, 19)),                     # celah 9 minggu -> tidak layak
        "gap8": set(range(10, 18)),                     # celah 8 minggu -> layak (batas inklusif)
        "year": y2025,                                  # share 0,17 & celah 1, tapi tahun 2025 < 0,70
        "share": set(range(0, 104, 4)),                 # share 0,25 > 0,20, celah 1
    })).set_index("commodity")
    assert el["eligible"].to_dict() == {"full": True, "gap9": False, "gap8": True, "year": False, "share": False}
    assert el.loc["gap9", "max_gap_weeks"] == 9 and el.loc["full", "max_gap_weeks"] == 0
    assert el.loc["year", "max_gap_weeks"] == 1
    assert np.isclose(el.loc["year", "min_year_coverage"], 1 - len(y2025) / 51)
    assert np.isclose(el.loc["share", "missing_share"], 0.25)


def test_eligibility_counts_only_missing(cfg):
    p = _panel({"x": set()})
    p.loc[::2, "status"] = "carry_forward"
    p.loc[1::4, "status"] = "short"
    assert eligibility(cfg, p)["eligible"].item()
