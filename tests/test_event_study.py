"""WP-14: event study per episode vs jendela plasebo."""

import numpy as np
import pandas as pd
import pytest

from kagami.models.event_study import event_paths, placebo_bands, placebo_starts


def _panel(n_weeks=300, n_prov=4, jump_at=150, jump=0.2, seed=0):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2018-01-01", periods=n_weeks, freq="W-MON")
    rows = []
    for r in range(1, n_prov + 1):
        lp = 9 + r / 10 + rng.normal(0, 0.002, n_weeks).cumsum()
        lp[jump_at:] += jump                                         # lonjakan tepat di minggu awal episode
        rows.append(pd.DataFrame({"week": weeks, "province_id": r, "commodity": "gula_pasir", "log_price": lp}))
    return pd.concat(rows, ignore_index=True), weeks


def _eps(weeks, at=150):
    return pd.DataFrame({"episode_id": [1], "start_week": [weeks[at]], "end_week": [weeks[at + 2]],
                         "cum_dlog_e": [0.04], "in_period": [True]})


def test_event_paths_national(cfg):
    panel, weeks = _panel()
    ev = event_paths(cfg, panel, _eps(weeks), "national")
    assert len(ev) == 13 and (ev["unit"] == "ALL").all()
    assert (ev["dlog_price"] > 0.15).all()                           # lonjakan 0,2 terlihat sejak h = 0


def test_event_paths_composition_and_truncation(cfg):
    panel, weeks = _panel(jump=0.0)
    panel.loc[(panel.province_id == 4) & (panel.week == weeks[155]), "log_price"] = np.nan
    ev = event_paths(cfg, panel, _eps(weeks), "national").set_index("horizon")["dlog_price"]
    assert abs(ev.loc[5]) < 0.05                                     # provinsi hilang tidak membuat lompatan level
    late = _eps(weeks, at=295)
    ev2 = event_paths(cfg, panel, late, "national")
    assert ev2["dlog_price"].notna().sum() == 5 and len(ev2) == 13   # horizon di luar panel = NaN, tidak dibuang


def test_placebo_starts_exclude_episode(cfg):
    _, weeks = _panel()
    s = placebo_starts(cfg, weeks, _eps(weeks))
    assert not ((s >= weeks[138]) & (s <= weeks[164])).any()         # [start-12, end+12]
    assert s.min() == weeks[1] and s.max() <= weeks[-13]


def test_placebo_bands(cfg):
    panel, weeks = _panel()
    ev = placebo_bands(cfg, panel, _eps(weeks), "national")
    assert {"placebo_lo", "placebo_hi", "placebo_p", "n_placebo"} <= set(ev.columns)
    assert (ev["n_placebo"] == cfg.params["inference"]["event_placebo_windows"]).all()
    assert (ev["placebo_p"] <= 2 / 500).all()                        # lonjakan 0,2 jauh di luar derau plasebo
    assert (ev["placebo_hi"] < 0.1).all() and (ev["placebo_lo"] > -0.1).all()
    ev0 = placebo_bands(cfg, _panel(jump=0.0)[0], _eps(weeks), "national")
    assert ev0["placebo_p"].median() > 0.05                          # tanpa efek -> p tidak kecil


def test_events_region_real(cfg):
    from kagami.utils.io import exists, read_artifact
    if not (exists(cfg, "panel_weekly_region") and exists(cfg, "episodes")):
        pytest.skip("artefak Tahap 0 belum ada")
    rg, eps = read_artifact(cfg, "panel_weekly_region"), read_artifact(cfg, "episodes")
    ev = placebo_bands(cfg, rg, eps, "region")
    n_eps = int(eps["in_period"].sum())
    assert len(ev) == n_eps * 13 * 7 * 10
    assert ev["placebo_p"].between(0, 1).all() or ev["placebo_p"].isna().any()
    assert (ev.dropna(subset=["placebo_lo"])["placebo_lo"] <= ev.dropna(subset=["placebo_hi"])["placebo_hi"]).all()
