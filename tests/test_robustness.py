"""WP-28: robustness Tier 1 (sampel jendela, demean ulang, dekomposisi kurs, LP bulanan, semua cek) pada data sintetis."""

import numpy as np
import pandas as pd
import pytest

from kagami.evaluation import robustness as rb
from kagami.models import local_projection as lp
from tests.test_local_projection import _drivers, _panel


def _drv_full(cfg, seed=1):
    d = _drivers(cfg, seed=seed)
    rng = np.random.default_rng(seed + 10)
    d["d_dxy"] = rng.normal(0, 0.006, len(d))
    d["de"] = d["de"] + 0.5 * d["d_dxy"]
    d["de_pos"], d["de_neg"] = d["de"].clip(lower=0), d["de"].clip(upper=0)
    d["log_e"] = 9.5 + d["de"].fillna(0).cumsum()
    d["log_brent"] = 4.2 + d["db"].cumsum()
    return d


def test_window_ok():
    weeks = pd.Series(pd.date_range("2020-01-06", periods=30, freq="W-MON"))
    ex = [(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-03-31"))]
    ok = rb._window_ok(weeks, lags=2, horizon=4, excluded=ex)
    t = pd.DatetimeIndex(weeks)
    start, end = t - pd.Timedelta(weeks=3), t + pd.Timedelta(weeks=4, days=6)
    expect = ~((start <= ex[0][1]) & (end >= ex[0][0]))
    assert (ok == expect).all()
    assert ok[0] and not ok[t.get_loc(pd.Timestamp("2020-03-02"))] and ok[-1]
    assert not ok[t.get_loc(pd.Timestamp("2020-02-03"))]            # t+h masuk Maret
    assert not ok[t.get_loc(pd.Timestamp("2020-04-20"))]            # t-(L+1) masuk Maret


def test_restrict_redemeans(cfg):
    drv = _drv_full(cfg)
    D = lp.build_design(cfg, _panel(cfg, drv, 0.3, 0.3, n_units=4), drv, None, "gula_pasir", 4, 4)
    mask = (D["week"] < pd.Timestamp("2021-04-05")).to_numpy()
    R = rb._restrict(D, mask)
    assert len(R) == mask.sum() and R["week"].max() < pd.Timestamp("2021-04-05")
    assert np.allclose(R.groupby("unit")[["y", "de", "dp_l1"]].mean(), 0)


def test_fx_decomposition(cfg):
    dec = rb.fx_decomposition(cfg, _drv_full(cfg))
    assert abs(dec.attrs["b"] - 0.5) < 0.1
    ok = dec["de"].notna()
    assert np.allclose(dec.loc[ok, "de_global"] + dec.loc[ok, "de_idr"], dec.loc[ok, "de"])
    per = (dec["week"] >= pd.Timestamp(cfg.params["period"]["start"])) & ok
    assert abs(np.corrcoef(dec.loc[per, "de_idr"], dec.loc[per, "d_dxy"])[0, 1]) < 1e-8


def test_tier1_recovers_constant_beta(cfg):
    drv = _drv_full(cfg)
    panel = _panel(cfg, drv, 0.4, 0.4)
    world = pd.DataFrame(columns=["week", "commodity", "log_w_idr", "dw"])
    out = rb.tier1(cfg, panel, drv, world, commodities=["gula_pasir"])
    assert list(out.columns[:9]) == rb.ROBUSTNESS_COLUMNS
    assert set(out["check_id"]) == set(rb.TIER1)
    assert (out["tier"] == 1).all() and out["note"].notna().all()
    assert set(out["horizon"]) == set(cfg.params["lp"]["key_horizons"])
    assert set(out.loc[out["check_id"] == rb.TIER1[4], "driver"]) == {"e_global", "e_idr"}
    assert set(out.loc[out["check_id"] == rb.TIER1[2], "variant"]) == {"pre", "post"}
    assert set(out.loc[out["check_id"] == rb.TIER1[1], "variant"]) == {"L=2", "L=8"}
    assert set(out.loc[out["check_id"] == rb.TIER1[5], "variant"]) == {"h_m=1", "h_m=2", "h_m=3"}
    hv = out[out["check_id"] == rb.TIER1[0]]
    assert len(hv) == 1 and hv["horizon"].iloc[0] == 12
    excl = out[out["check_id"] == rb.TIER1[3]]
    base_n = out.loc[out["check_id"] == rb.TIER1[1], "n_weeks"].max()
    assert (excl["n_weeks"] < base_n).all()


def test_tier1_precise_at_h0(cfg):
    """h=0: derau masa depan nol -> β benar 0,4 dipulihkan di setiap sub-sampel/spesifikasi mingguan."""
    drv = _drv_full(cfg)
    panel = _panel(cfg, drv, 0.4, 0.4)
    world = pd.DataFrame(columns=["week", "commodity", "log_w_idr", "dw"])
    out = rb.tier1(cfg, panel, drv, world, commodities=["gula_pasir"], horizons=[0])
    weekly = out[(out["horizon"] == 0) & (out["check_id"] != rb.TIER1[5])]
    assert len(weekly) == 7
    assert (abs(weekly["estimate"] - 0.4) < 2.5 * weekly["se"]).all()
    assert weekly["baseline_in_ci"].all()
    m = out[out["check_id"] == rb.TIER1[5]].iloc[0]
    assert m["variant"] == "h_m=1" and abs(m["estimate"] - 0.4) < 3 * m["se"]


def test_tier1_detects_covid_only_effect(cfg):
    """β hanya muncul di minggu Mar-Jun 2020 -> baseline > 0, cek tanpa COVID ≈ 0."""
    drv = _drv_full(cfg)
    a, b = (pd.Timestamp(x) for x in cfg.params["calendar"]["exclusions"]["covid"])
    in_c = drv["week"].between(a, b)
    drv.loc[in_c, "de"] = drv.loc[in_c, "de"] * 5
    drv["de_pos"], drv["de_neg"] = drv["de"].clip(lower=0), drv["de"].clip(upper=0)
    drv["log_e"] = 9.5 + drv["de"].fillna(0).cumsum()
    shock = drv[["week"]].assign(de=np.where(in_c, drv["de"], 0.0))
    panel = _panel(cfg, shock.assign(de_pos=shock["de"], de_neg=shock["de"]).assign(
        de_pos=lambda x: x["de"].clip(lower=0), de_neg=lambda x: x["de"].clip(upper=0)), 1.0, 1.0)
    world = pd.DataFrame(columns=["week", "commodity", "log_w_idr", "dw"])
    out = rb.tier1(cfg, panel, drv, world, commodities=["gula_pasir"], horizons=[0])
    r = out[(out["check_id"] == rb.TIER1[3]) & (out["driver"] == "e")].iloc[0]
    assert r["baseline_estimate"] > 0.3
    assert abs(r["estimate"]) < 2.5 * r["se"] and not r["baseline_in_ci"]


@pytest.mark.parametrize("h,expect", [(4, 1), (8, 2), (12, 3)])
def test_monthly_horizon_mapping(h, expect):
    assert max(1, round(h / rb._WEEKS_PER_MONTH)) == expect


# ------------------------------------------------------------------------------------------- WP-29 validasi
def _val_inputs(cfg, beta=0.5, drift=0.002):
    drv = _drv_full(cfg)
    H = max(cfg.params["lp"]["horizons"])
    prof = pd.DataFrame({"level": "national", "unit": "ALL", "commodity": "gula_pasir", "driver": "e",
                         "horizon": range(H + 1), "estimate": beta})
    starts = pd.to_datetime(["2019-03-04", "2021-06-07", "2023-09-04", "2026-05-18"])
    eps = pd.DataFrame({"episode_id": [1, 2, 3, 4], "start_week": starts, "end_week": starts, "in_period": True})
    de = drv.set_index("week")["de"]
    rows = []
    for eid, s in zip(eps["episode_id"], starts):
        cum = de.reindex(pd.date_range(s, periods=H + 1, freq="W-MON")).cumsum().to_numpy()
        for h in range(H + 1):
            rows.append({"episode_id": eid, "level": "national", "unit": "ALL", "commodity": "gula_pasir",
                         "horizon": h, "dlog_price": beta * cum[h] + drift * (h + 1),
                         "placebo_lo": drift * (h + 1) - 0.01, "placebo_hi": drift * (h + 1) + 0.01,
                         "placebo_p": 0.5, "n_placebo": 499})
    world = pd.DataFrame(columns=["week", "commodity", "log_w_idr", "dw"])
    return prof, pd.DataFrame(rows), eps, drv, world


def test_lp_implied_paths_constant_beta(cfg):
    prof, _, eps, drv, world = _val_inputs(cfg)
    imp = rb.lp_implied_paths(cfg, prof, drv, world, eps["start_week"], "gula_pasir")
    de = drv.set_index("week")["de"]
    s = eps["start_week"].iloc[1]
    cum = de.reindex(pd.date_range(s, periods=13, freq="W-MON")).cumsum().to_numpy()
    assert np.allclose(imp[1], 0.5 * cum)


def test_validation_v4_and_v2(cfg):
    prof, events, eps, drv, world = _val_inputs(cfg)
    fe = pd.DataFrame({"horizon": 8, "model": ["M2", "M2", "M1"], "subset": ["case_study", "all", "case_study"],
                       "commodity": "ALL", "region": "ALL", "level": "all", "mae_ratio_vs_m1": [0.9, 0.95, 1.0],
                       "dm_p": [0.2, 0.1, np.nan], "n_origins": [9, 70, 9], "n_nonoverlap": [5, 35, 5]})
    out = rb.validation(cfg, prof, events, eps, drv, world, fe)
    assert list(out.columns[:9]) == rb.ROBUSTNESS_COLUMNS and (out["tier"] == "V").all()
    v4 = out[out.check_id == "V4_lp_vs_event_study"]
    assert set(v4["horizon"]) == set(cfg.params["lp"]["key_horizons"]) and (v4["n_episodes"] == 4).all()
    assert np.allclose(v4["estimate"], v4["baseline_estimate"])          # event = implikasi LP + drift plasebo
    assert (v4["sign_agree"] == 1).all() and (v4["corr"] > 0.999).all()
    v2 = out[out.check_id == "V2_case_study_events"]
    assert set(v2["variant"]) == {"episode_4"} and len(v2) == 3
    assert np.allclose(v2["ci_low"], -0.01) and np.allclose(v2["ci_high"], 0.01)
    v2f = out[out.check_id == "V2_case_study_forecast"]
    assert len(v2f) == 1 and v2f["estimate"].iloc[0] == 0.9 and v2f["baseline_estimate"].iloc[0] == 0.95
    assert "n_origins 9" in v2f["note"].iloc[0]
    assert len(rb.validation(cfg, prof, events, eps, drv, world)) == len(out) - 1   # tanpa forecast_eval


def test_validation_detects_disagreement(cfg):
    prof, events, eps, drv, world = _val_inputs(cfg)
    events["dlog_price"] = (events["placebo_lo"] + events["placebo_hi"]) / 2 - (events["dlog_price"] -
                                                                                (events["placebo_lo"] + events["placebo_hi"]) / 2)
    v4 = rb.validation(cfg, prof, events, eps, drv, world).query("check_id == 'V4_lp_vs_event_study'")
    assert (v4["corr"] < -0.999).all() and (v4["sign_agree"] == 0).all()


def test_validation_uses_placebo_median(cfg):
    """Pusat null = median plasebo bila ada (titik tengah pita peka terhadap ekor null yang miring)."""
    prof, events, eps, drv, world = _val_inputs(cfg)
    events["placebo_median"] = (events["placebo_lo"] + events["placebo_hi"]) / 2
    events["placebo_hi"] = events["placebo_hi"] + 0.5                          # ekor kanan panjang
    v4 = rb.validation(cfg, prof, events, eps, drv, world).query("check_id == 'V4_lp_vs_event_study'")
    assert np.allclose(v4["estimate"], v4["baseline_estimate"])
