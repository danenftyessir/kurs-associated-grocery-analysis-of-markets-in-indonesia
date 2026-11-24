"""D-141 (eksploratif): klasifier arah C1/C2 dengan fitur & rolling-origin Task 4 pada data sintetis (jawaban diketahui)."""

import numpy as np
import pandas as pd
import pytest

from kagami.features.forecast import feature_table, origins, split_origin
from kagami.models.direction import CLASSIFIERS, fit_predict_proba, rolling_direction
from kagami.tracking.metrics import paired_accuracy_diff, selective_accuracy
from kagami.utils.artifacts import ARTIFACTS
from synthetic import synthetic_task4_inputs

H = 4


@pytest.fixture(scope="module")
def data(cfg):
    return synthetic_task4_inputs(cfg)


@pytest.fixture(scope="module")
def table(cfg, data):
    return feature_table(cfg, *data, [H])


@pytest.fixture(autouse=True)
def fast_hgb(cfg, monkeypatch):
    """HGB lebih ringan untuk tes (logika sama; tes hanya memeriksa arah sinyal, bentuk, dan resume)."""
    monkeypatch.setitem(cfg.params["forecast"]["hgb"], "max_iter", 40)


def _acc(p: pd.Series, y: pd.Series) -> float:
    k = y != 0
    return float(((p[k] > 0.5) == (y[k] > 0)).mean())


def test_fx_classifier_learns_planted_signal(cfg, data, table):
    """Data sintetis: perubahan harga mengikuti kurs berjeda → C2 (+ kurs) lebih akurat dari C1 (tanpa kurs)."""
    accs = {m: [] for m in CLASSIFIERS}
    for o in origins(cfg, data[1]["week"], H)[-4:]:
        train, test = split_origin(cfg, table, o, H)
        for m in CLASSIFIERS:
            p = fit_predict_proba(cfg, m, train, test)
            assert len(p) == len(test) and ((p >= 0) & (p <= 1)).all()
            accs[m].append(_acc(p, test["y"]))
    assert np.mean(accs["C2"]) > np.mean(accs["C1"]) and np.mean(accs["C2"]) > 0.6


def test_guards(cfg, data, table):
    o = origins(cfg, data[1]["week"], H)[-1]
    train, test = split_origin(cfg, table, o, H)
    with pytest.raises(ValueError):
        fit_predict_proba(cfg, "CX", train, test)
    one = train.assign(y=np.abs(train["y"]) + 1e-3)                     # train hanya kelas naik
    assert (fit_predict_proba(cfg, "C1", one, test) == 1.0).all()
    zero = train.assign(y=0.0)                                           # semua y = 0 dibuang → tanpa data latih
    assert (fit_predict_proba(cfg, "C1", zero, test) == 0.5).all()


def test_rolling_direction_shape_and_resume(cfg, data):
    small = (data[0], data[1].iloc[:200], data[2])
    full = rolling_direction(cfg, *small)
    assert set(full["model"]) == set(CLASSIFIERS) and full["p_up"].between(0, 1).all()
    assert set(ARTIFACTS["direction_preds"].columns) <= set(full.columns)
    assert full.groupby(["origin", "horizon", "model"]).size().nunique() == 1
    snaps = []
    rolling_direction(cfg, *small, checkpoint=snaps.append, checkpoint_every=5)
    resumed = rolling_direction(cfg, *small, done=snaps[0])
    keys = ["origin", "horizon", "model", "province_id", "commodity"]
    pd.testing.assert_frame_equal(resumed.sort_values(keys).reset_index(drop=True),
                                  full.sort_values(keys).reset_index(drop=True))
    assert not ARTIFACTS["direction_preds"].ship


def test_paired_diff_and_selective():
    rng = np.random.default_rng(0)
    o = np.repeat(np.arange(30), 50)
    y = rng.normal(0, 1, len(o))
    good, bad = y + rng.normal(0, 0.5, len(o)), rng.normal(0, 1, len(o))
    r = paired_accuracy_diff(y, good, bad, o, block=2, reps=299, seed=1)
    assert r["ci_low"] > 0 and r["acc_a"] > r["acc_b"] and r["n"] == len(o)
    same = paired_accuracy_diff(y, good, good, o, block=2, reps=99)
    assert same["diff"] == 0 and same["ci_low"] == same["ci_high"] == 0
    assert paired_accuracy_diff(y[:10], good[:10], bad[:10], np.zeros(10), block=2) is None
    p = 1 / (1 + np.exp(-2 * good))                                     # keyakinan berkorelasi dengan benar
    rows = selective_accuracy(y, p, o, (1.0, 0.5, 0.25))
    assert [x["coverage"] for x in rows] == pytest.approx([1.0, 0.5, 0.25], abs=0.02)
    assert rows[0]["accuracy"] < rows[1]["accuracy"] < rows[2]["accuracy"]
