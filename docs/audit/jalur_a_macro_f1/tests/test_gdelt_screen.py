"""Tes Jalur A Workstream B (layar GDELT) pada data sintetis: jendela waktu, tanpa kebocoran, kepekaan layar."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import b_gdelt_screen as S  # noqa: E402


def test_week_window_sat_to_fri():
    t = pd.Timestamp("2022-03-14")                                  # Senin
    days = pd.Series(pd.date_range(t - pd.Timedelta(days=2), t + pd.Timedelta(days=4)))
    assert (S.week_of_utc_day(days) == t).all()                     # Sabtu t−2 .. Jumat t+4 → minggu t
    nxt = S.week_of_utc_day(pd.Series([t + pd.Timedelta(days=5)]))  # Sabtu t+5 → minggu berikutnya (sesudah waktu prediksi)
    assert nxt.iloc[0] == t + pd.Timedelta(weeks=1)


def _daily(seed=0, n_days=900):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2019-01-05", periods=n_days, freq="D")
    rows = []
    for g in ["beras", "cabai"]:
        for d in days:
            n = rng.poisson(20)
            rows.append({"day_utc": d, "commodity_group": g, "n_all": n, "n_disrupt": rng.binomial(n, 0.2),
                         "n_policy": rng.binomial(n, 0.2), "n_stabil": rng.binomial(n, 0.1), "n_supply": rng.binomial(n, 0.3),
                         "n_ind_total": 10000})
    return pd.DataFrame(rows)


def test_weekly_features_no_future_dependence():
    d = _daily()
    tot = d[["day_utc", "n_ind_total"]].drop_duplicates("day_utc")
    f1 = S.weekly_features(d, tot)
    cut = pd.Timestamp("2020-06-01")
    d2 = d.copy()
    late = d2["day_utc"] > cut + pd.Timedelta(days=4)                # sesudah Jumat minggu cut
    d2.loc[late, ["n_all", "n_disrupt"]] *= 7
    f2 = S.weekly_features(d2, tot)
    a = f1[f1["week"] <= cut].sort_values(["commodity", "week"]).reset_index(drop=True)
    b = f2[f2["week"] <= cut].sort_values(["commodity", "week"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    assert set(f1["commodity"]) == {"beras", "cabai_merah", "cabai_rawit"}


def _nt(signal, seed=1):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2019-01-07", "2023-12-25", freq="W-MON")
    rows = []
    for c in range(8):
        for w in weeks:
            s = rng.normal()
            cons = 1 / (1 + np.exp(-0.8 * rng.normal()))
            logit = np.log(cons / (1 - cons))
            z = float(rng.random() < 1 / (1 + np.exp(-(logit + signal * s))))
            rows.append({"commodity": f"k{c}", "week": w, "cons": cons, "L": logit, "z": z, "x": s})
    return pd.DataFrame(rows)


def test_screen_detects_strong_signal_and_rejects_noise():
    strong = S.inc_screen(_nt(1.5), ["x"], 4, reps=199)
    noise = S.inc_screen(_nt(0.0), ["x"], 4, reps=199)
    assert strong["d_auc"] > 0.05 and strong["lo"] > 0
    assert abs(noise["d_auc"]) < 0.02


def test_gate_rule():
    res = pd.DataFrame({"set": ["A", "A", "B", "B"], "horizon": [4, 8, 4, 8], "d_auc": [0.02, 0.012, 0.03, 0.005],
                        "lo": [0.001, -0.01, 0.01, -0.01], "q_bh": [0.03, 0.2, 0.01, 0.4]})
    g = S.gate(res)
    assert g == {"A": True, "B": False}                               # B gagal: ΔAUC h 8 < 0,01


def test_bh_matches_reference():
    p = np.array([0.01, 0.04, 0.03, np.nan, 0.2])
    q = S.bh(p)
    assert q[0] == pytest.approx(0.04) and np.isnan(q[3]) and q[4] == pytest.approx(0.2)
