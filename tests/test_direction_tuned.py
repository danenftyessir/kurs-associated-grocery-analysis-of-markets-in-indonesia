"""D-145 (eksploratif): fitur dinamika harga & klasifier arah tuned C1t/C2t pada data sintetis (jawaban diketahui)."""

import numpy as np
import pandas as pd
import pytest

from kagami.features import price_dynamics as pdyn
from kagami.features.forecast import FEATURE_GROUPS, feature_table, origins, split_origin
from kagami.models import direction
from kagami.models.direction import (TUNED_CLASSIFIERS, fit_predict_proba, fit_predict_proba_tuned,
                                     rolling_direction_tuned, tuned_columns)
from kagami.utils.artifacts import ARTIFACTS
from synthetic import synthetic_task4_inputs

HS = [4, 8]
ALL_COLS = [c for g in pdyn.GROUPS for c in pdyn.group_columns([g], 4) + pdyn.group_columns([g], 8)]


@pytest.fixture(scope="module")
def data(cfg):
    return synthetic_task4_inputs(cfg)


@pytest.fixture(scope="module")
def table(cfg, data):
    return pdyn.extend_table(feature_table(cfg, *data, HS), data[0], HS)


@pytest.fixture(autouse=True)
def fast_hgb(monkeypatch):
    """HGB lebih ringan untuk tes (logika sama)."""
    monkeypatch.setitem(direction.TUNED_HGB, "max_iter", 40)
    monkeypatch.setitem(direction.TUNED_HGB, "min_samples_leaf", 20)


def test_no_future_information(cfg, data, table):
    """Merusak harga & status sesudah origin tidak mengubah fitur apa pun pada minggu ≤ origin."""
    panel, drivers, world = data
    base = feature_table(cfg, panel, drivers, world, HS)
    weeks = sorted(base["week"].unique())
    rng = np.random.default_rng(3)
    for o in (weeks[120], weeks[-30]):
        bad = base.copy()
        fut = bad["week"] > o
        bad.loc[fut, "log_p"] += rng.normal(0, 0.5, fut.sum())
        pbad = panel.assign(status=np.where(panel["week"] > o, "missing", panel.get("status", "observed")))
        ext = pdyn.extend_table(bad, pbad, HS)
        ref = pdyn.extend_table(base, panel.assign(status=panel.get("status", "observed")), HS)
        k = ["week", "province_id", "commodity"]
        a = ref[ref["week"] <= o].sort_values(k)[ALL_COLS].to_numpy(float)
        b = ext[ext["week"] <= o].sort_values(k)[ALL_COLS].to_numpy(float)
        np.testing.assert_allclose(a, b, equal_nan=True)


def test_known_feature_values(table):
    t = table.sort_values(["province_id", "commodity", "week"]).reset_index(drop=True)
    g = t[(t["province_id"] == t["province_id"].iloc[0]) & (t["commodity"] == t["commodity"].iloc[0])].reset_index(drop=True)
    p = g["log_p"]
    i = 150
    assert g.loc[i, "lag_dp_13"] == pytest.approx(p[i] - p[i - 13])
    assert g.loc[i, "dp1_l1"] == pytest.approx(p[i - 1] - p[i - 2])
    assert g.loc[i, "dev_ma13"] == pytest.approx(p[i] - p[i - 12:i + 1].mean())
    assert g.loc[i, "yseas_52_h8"] == pytest.approx(p[i - 44] - p[i - 52])       # p_{t-52+h} - p_{t-52}, terealisasi s.d. t
    # deviasi spasial berjumlah nol lintas provinsi per (minggu, komoditas)
    s = t.dropna(subset=["spatial_dev"]).groupby(["week", "commodity"])["spatial_dev"].sum()
    assert np.abs(s).max() < 1e-9
    assert set(pdyn.SELECTED_GROUPS) <= set(pdyn.GROUPS) and not {"vol", "cf"} & set(pdyn.SELECTED_GROUPS)


def test_cf_age_counts_unchanged_weeks():
    weeks = pd.date_range("2020-01-06", periods=12, freq="W-MON")
    lp = np.log([10, 10, 10, 11, 11, 12, 12, 12, 12, 13, 13, 13], dtype=float)
    tab = pd.DataFrame({"week": weeks, "province_id": 1, "commodity": "beras", "log_p": lp})
    out = pdyn.extend_table(tab, pd.DataFrame(), [4])
    assert out["cf_age"].tolist() == [0, 1, 2, 0, 1, 0, 1, 2, 3, 0, 1, 2]
    assert (out["status_cf_run"] == 0).all()                                     # panel tanpa status → 0


def test_tuned_columns_and_guards(cfg, data, table):
    c1, cats = tuned_columns("C1t", 8)
    c2, _ = tuned_columns("C2t", 8)
    assert set(c2) - set(c1) == set(FEATURE_GROUPS["fx"]) and cats == FEATURE_GROUPS["id"]
    assert "yseas_52_h8" in c1 and "yseas_52_h4" not in c1 and len(c1) == len(set(c1))
    with pytest.raises(ValueError):
        tuned_columns("CX", 4)
    o = origins(cfg, data[1]["week"], 4)[-1]
    train, test = split_origin(cfg, table, o, 4)
    assert (fit_predict_proba_tuned(cfg, "C1t", train.assign(y=np.abs(train["y"]) + 1e-3), test, 4) == 1.0).all()
    assert (fit_predict_proba_tuned(cfg, "C1t", train.assign(y=0.0), test, 4) == 0.5).all()


def _mean_reverting_inputs(cfg, data, seed=7):
    """Harga provinsi = tren bersama kecil + deviasi AR(1) (phi 0,85): arah perubahan ke depan dapat diprediksi dari
    deviasi spasial & deviasi terhadap rerata bergerak (fitur dev), tidak dari lag Δp 1/4/8 saja."""
    panel, drivers, world = data
    rng = np.random.default_rng(seed)
    rows = []
    for (r, c), g in panel.groupby(["province_id", "commodity"]):
        u = np.zeros(len(g))
        for t in range(1, len(g)):
            u[t] = 0.85 * u[t - 1] + rng.normal(0, 0.03)
        common = np.cumsum(np.full(len(g), 0.0005))
        rows.append(g.assign(log_price=np.log(10000.0) + common + u))
    return pd.concat(rows, ignore_index=True), drivers, world


def test_tuned_classifier_learns_mean_reversion(cfg):
    panel, drivers, world = _mean_reverting_inputs(cfg, synthetic_task4_inputs(cfg, n_provinces=12))
    base = feature_table(cfg, panel, drivers, world, [4])
    ext = pdyn.extend_table(base, panel, [4])
    acc = {"C1": [], "C1t": []}
    for o in origins(cfg, drivers["week"], 4)[-15:]:
        tr, te = split_origin(cfg, base, o, 4)
        trx, tex = split_origin(cfg, ext, o, 4)
        k = te["y"] != 0
        acc["C1"].append(float(((fit_predict_proba(cfg, "C1", tr, te) > 0.5)[k] == (te["y"] > 0)[k]).mean()))
        pt = fit_predict_proba_tuned(cfg, "C1t", trx, tex, 4)
        acc["C1t"].append(float(((pt > 0.5)[k] == (tex["y"] > 0)[k]).mean()))
    assert np.mean(acc["C1t"]) > np.mean(acc["C1"]) and np.mean(acc["C1t"]) > 0.6


def test_rolling_shape_resume_and_contract(cfg, data):
    small = (data[0], data[1].iloc[:200], data[2])
    full = rolling_direction_tuned(cfg, *small)
    assert set(full["model"]) == set(TUNED_CLASSIFIERS) and full["p_up"].between(0, 1).all()
    assert set(ARTIFACTS["direction_tuned_preds"].columns) <= set(full.columns)
    assert full.groupby(["origin", "horizon", "model"]).size().nunique() == 1
    snaps = []
    rolling_direction_tuned(cfg, *small, checkpoint=snaps.append, checkpoint_every=5)
    resumed = rolling_direction_tuned(cfg, *small, done=snaps[0])
    keys = ["origin", "horizon", "model", "province_id", "commodity"]
    pd.testing.assert_frame_equal(resumed.sort_values(keys).reset_index(drop=True),
                                  full.sort_values(keys).reset_index(drop=True))
    only = rolling_direction_tuned(cfg, *small, models=["C1t"])
    assert set(only["model"]) == {"C1t"}
    assert not ARTIFACTS["direction_tuned_preds"].ship
