"""D-142 (eksploratif): PatchTST, TSMixer (± kurs), TimesFM (adapter) pada data sintetis Task 4 — kontrak, tanpa kebocoran,
resume. TimesFM asli tidak diunduh di tes: dipakai forecaster palsu dengan antarmuka `predict_batch` yang sama."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch")

from kagami.features.forecast import feature_table, origins  # noqa: E402
from kagami.models import neural  # noqa: E402
from kagami.models.forecasting import rolling_predictions  # noqa: E402
from kagami.utils.artifacts import ARTIFACTS  # noqa: E402
from synthetic import synthetic_task4_inputs  # noqa: E402


@pytest.fixture(autouse=True)
def small_nets(monkeypatch):
    monkeypatch.setattr(neural, "EPOCHS", 2)
    monkeypatch.setattr(neural, "MAX_WINDOWS", 3000)


@pytest.fixture(scope="module")
def data(cfg):
    d = synthetic_task4_inputs(cfg)
    return d[0], d[1].iloc[:200], d[2]


@pytest.fixture(scope="module")
def arr(cfg, data):
    return neural.series_arrays(feature_table(cfg, *data, [4, 8]), [4, 8])


class FakeTFM:
    """Antarmuka TimesFM3Forecaster.predict_batch: ramalan = nilai terakhir konteks (+ jejak argumen untuk diperiksa)."""

    def __init__(self):
        self.calls = []

    def predict_batch(self, contexts, horizon, past_only_covariates=None):
        self.calls.append((contexts, horizon, past_only_covariates))
        for c in contexts:
            last = pd.Series(c).ffill().iloc[-1]
            yield SimpleNamespace(forecast=np.full(horizon, last + 0.01))


def test_train_windows_never_use_unrealised_targets(cfg, arr):
    oi = 150
    tt, ss, Y = neural._train_index(arr, oi, [4, 8], np.random.default_rng(0))
    assert tt.max() <= oi and np.isfinite(Y).any(axis=1).all()
    assert np.isnan(Y[tt + 8 > oi, 1]).all() and np.isnan(Y[tt + 4 > oi, 0]).all()


@pytest.mark.parametrize("model", list(neural.SEQ_MODELS))
def test_sequence_model_no_lookahead(cfg, arr, model):
    """Mengubah semua nilai sesudah origin (harga, kurs, target) tidak mengubah ramalan pada origin."""
    oi = 150
    s = np.arange(arr["p"].shape[1])
    net, meta = neural.fit_sequence_model(cfg, model, arr, oi, [4, 8], seed=1)
    base = neural.predict_sequence_model(net, meta, arr, np.full(len(s), oi), s)
    assert base.shape == (len(s), 2) and np.isfinite(base).all()
    fut = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in arr.items()}
    fut["y"] = {h: v.copy() for h, v in arr["y"].items()}
    for k in ("p", "p_raw", "de", "dw"):
        fut[k][oi + 1:] += 5.0
    for h in fut["y"]:
        fut["y"][h][oi - h + 1:] += 5.0
    net2, meta2 = neural.fit_sequence_model(cfg, model, fut, oi, [4, 8], seed=1)
    np.testing.assert_allclose(neural.predict_sequence_model(net2, meta2, fut, np.full(len(s), oi), s), base, atol=1e-5)


def test_timesfm_adapter_context_stops_at_origin(cfg, arr):
    fake, oi, s = FakeTFM(), 120, np.arange(5)
    y = neural.predict_timesfm(fake, arr, oi, s, [4, 8], fx=False)
    ctx, H, cov = fake.calls[-1]
    assert H == 8 and all(len(c) == oi + 1 for c in ctx) and cov is None
    np.testing.assert_allclose(y, 0.01, atol=1e-9)                     # ramalan = p_t + 0,01 → y = 0,01
    neural.predict_timesfm(fake, arr, oi, s, [4, 8], fx=True)
    assert all(c.shape == (2, oi + 1) for c in fake.calls[-1][2])     # de & dw, hanya masa lalu


def test_rolling_deep_contract_rows_and_resume(cfg, data):
    models = ["TSMX", "TFM"]
    full = neural.rolling_deep(cfg, *data, models=models, forecaster=FakeTFM())
    assert set(full["model"]) == set(models) and full["y_pred"].notna().all()
    assert set(ARTIFACTS["deep_preds"].columns) <= set(full.columns) and not ARTIFACTS["deep_preds"].ship
    ref = rolling_predictions(cfg, *data, include_m3=False)
    keys = ["origin", "horizon", "province_id", "commodity"]
    a = full[full["model"] == "TSMX"][keys + ["y_true"]].sort_values(keys).reset_index(drop=True)
    b = ref[ref["model"] == "M1"][keys + ["y_true"]].sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b, check_dtype=False)            # baris uji & target = Task 4
    snaps = []
    neural.rolling_deep(cfg, *data, models=models, forecaster=FakeTFM(), checkpoint=snaps.append)
    done = snaps[0]
    resumed = neural.rolling_deep(cfg, *data, models=models, forecaster=FakeTFM(), done=done)
    k = ["model"] + keys
    pd.testing.assert_frame_equal(resumed.sort_values(k).reset_index(drop=True),
                                  full.sort_values(k).reset_index(drop=True), check_dtype=False)
    with pytest.raises(ValueError):
        neural.rolling_deep(cfg, *data, models=["XYZ"])
    assert len(origins(cfg, data[1]["week"], 4)) >= 3
