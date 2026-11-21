"""WP-25/26: fitur as-of tanpa kebocoran + model M0-M3 pada data sintetis (jawaban diketahui)."""

import numpy as np
import pandas as pd
import pytest

from kagami.features.forecast import FEATURE_GROUPS, build_features, feature_table, origins, split_origin
from kagami.models.forecasting import ABLATION_MODEL, fit_predict, rolling_predictions
from synthetic import synthetic_task4_inputs

H = 4


@pytest.fixture(scope="module")
def data(cfg):
    return synthetic_task4_inputs(cfg)


@pytest.fixture(scope="module")
def table(cfg, data):
    return feature_table(cfg, *data, [H])


def test_origins_step_and_end(cfg, data):
    weeks = data[1]["week"]
    o = origins(cfg, weeks, H)
    p = cfg.params["forecast"]
    assert o[0] == pd.Timestamp(p["first_origin"]) and len(o) > 5
    assert all(b - a == pd.Timedelta(weeks=p["origin_step_weeks"]) for a, b in zip(o, o[1:]))
    assert o[-1] + pd.Timedelta(weeks=H) <= weeks.max()


def test_no_leakage_train_and_test(cfg, data, table):
    rng = np.random.default_rng(1)
    for o in rng.choice(origins(cfg, data[1]["week"], H), 5, replace=False):
        train, test = split_origin(cfg, table, o, H)
        assert len(train) and len(test)
        assert (train["week"] + pd.Timedelta(weeks=H) <= o).all()       # outcome train sudah terealisasi pada origin
        assert (test["week"] == o).all()
        for df in (train, test):                                          # as-of harga dunia
            known = df["world_available_at"].dropna()
            assert (known <= df.loc[known.index, "week"]).all()


def test_features_ignore_the_future(cfg, data):
    """Mengacak semua data setelah minggu t0 tidak boleh mengubah fitur pada minggu <= t0."""
    panel, drivers, world = data
    t0 = pd.Timestamp("2021-06-07")
    rng = np.random.default_rng(2)
    p2, d2, w2 = panel.copy(), drivers.copy(), world.copy()
    p2.loc[p2["week"] > t0, "log_price"] += rng.normal(0, 1, (p2["week"] > t0).sum())
    d2.loc[d2["week"] > t0, ["log_e", "log_brent"]] += 5.0
    w2.loc[w2["week"] > t0, "log_w_idr"] += 5.0
    a = feature_table(cfg, panel, drivers, world, [H])
    b = feature_table(cfg, p2, d2, w2, [H])
    cols = [c for c in a.columns if not c.startswith("y_")]
    # harga dunia as-of: baris dengan available_at > t0 hanya bisa dipakai setelah t0, jadi minggu <= t0 tidak berubah
    pd.testing.assert_frame_equal(a.loc[a["week"] <= t0, cols].reset_index(drop=True),
                                  b.loc[b["week"] <= t0, cols].reset_index(drop=True))


def test_target_definition(cfg, data, table):
    panel = data[0]
    s = panel[(panel["province_id"] == 1) & (panel["commodity"] == "beras")].set_index("week")["log_price"]
    is_row = (table["province_id"] == 1) & (table["commodity"] == "beras") & (table["week"] == s.index[20])
    row = table[is_row].iloc[0]
    assert np.isclose(row["y_4"], s.iloc[24] - s.iloc[20])
    assert np.isclose(row["lag_dp_4"], s.iloc[20] - s.iloc[16])


def test_build_features_matches_split(cfg, data, table):
    o = origins(cfg, data[1]["week"], H)[3]
    tr, te = build_features(cfg, *data, o, H)
    tr2, te2 = split_origin(cfg, table, o, H)
    assert len(tr) == len(tr2) and len(te) == len(te2) and set(te["origin"]) == {o}


def test_models_fx_improves_and_ablation_equals_m1(cfg, data, table):
    o = origins(cfg, data[1]["week"], H)[-3]
    train, test = split_origin(cfg, table, o, H)
    p0 = fit_predict(cfg, "M0", train, test)
    p1, p2 = fit_predict(cfg, "M1", train, test), fit_predict(cfg, "M2", train, test)
    p3 = fit_predict(cfg, "M3", train, test)
    assert (p0 == 0).all() and len(p3) == len(test) and np.isfinite(p3).all()
    mae = lambda p: float(np.abs(test["y"] - p).mean())          # noqa: E731
    assert mae(p2) < 0.8 * mae(p1)                                 # kurs berjeda memang prediktif
    np.testing.assert_allclose(fit_predict(cfg, "M2", train, test, drop_groups=("fx",)), p1)
    with pytest.raises(ValueError):
        fit_predict(cfg, "MX", train, test)
    assert set(FEATURE_GROUPS) == {"base", "fx", "id"}


def test_rolling_predictions_shape_and_flag(cfg, data):
    small = (data[0], data[1].iloc[:200], data[2])
    preds = rolling_predictions(cfg, *small, include_m3=False)
    assert set(preds["model"]) == {"M0", "M1", "M2", ABLATION_MODEL}
    contract = {"origin", "horizon", "model", "province_id", "region", "commodity", "y_true", "y_pred", "large_move"}
    assert contract <= set(preds.columns)
    assert preds["large_move"].dtype == bool and preds["y_pred"].notna().all()
    assert set(preds["horizon"]) == set(cfg.params["forecast"]["horizons"])
    assert preds.groupby(["origin", "horizon", "model"]).size().nunique() == 1     # semua model: baris sama


def test_resume_and_checkpoint(cfg, data):
    small = (data[0], data[1].iloc[:200], data[2])
    full = rolling_predictions(cfg, *small, include_m3=False)
    snaps = []
    part = rolling_predictions(cfg, *small, include_m3=False, checkpoint=snaps.append, checkpoint_every=5)
    assert len(snaps) >= 1 and len(snaps[0]) < len(part)                       # checkpoint berisi hasil parsial
    # sesi mati di tengah: lanjutkan dari checkpoint pertama -> hasil sama dengan run penuh, tanpa mengulang origin selesai
    resumed = rolling_predictions(cfg, *small, include_m3=False, done=snaps[0])
    keys = ["origin", "horizon", "model", "province_id", "commodity"]
    pd.testing.assert_frame_equal(resumed.sort_values(keys).reset_index(drop=True),
                                  full.sort_values(keys).reset_index(drop=True))
    assert not resumed.duplicated(keys).any()


def test_forecast_preds_is_artifact_not_shipped():
    from kagami.utils.artifacts import ARTIFACTS
    a = ARTIFACTS["forecast_preds"]
    assert a.stage == "task4" and a.ship is False and {"origin", "horizon", "model", "y_pred"} <= set(a.columns)
