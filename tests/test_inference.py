"""WP-16: bootstrap blok bersama, plasebo geser-melingkar, dan interval gabungan."""

import numpy as np
import pandas as pd
import pytest

from kagami.data.drivers import driver_weeks
from kagami.evaluation import inference
from kagami.evaluation.inference import _Prepared, bootstrap_ci, circular_placebo, joint_bootstrap
from kagami.models.local_projection import national_profiles

COM = "gula_pasir"


def _drivers(cfg, seed=1, sd=0.01):
    rng = np.random.default_rng(seed)
    weeks = driver_weeks(cfg)
    de = rng.normal(0, sd, len(weeks))
    de[0] = np.nan
    d = pd.DataFrame({"week": weeks, "de": de})
    d["de_pos"], d["de_neg"] = d["de"].clip(lower=0), d["de"].clip(upper=0)
    d["log_e"] = 9.5 + np.nan_to_num(de).cumsum()
    d["db"] = rng.normal(0, 0.03, len(weeks))
    d["log_brent"] = 4.4 + np.nan_to_num(d["db"].to_numpy()).cumsum()
    d["month"] = weeks.month
    d["idf_rel_week"] = np.nan
    return d


def _panel(cfg, drv, beta=0.4, n_units=4, seed=2, miss=True):
    rng = np.random.default_rng(seed)
    weeks = drv["week"][drv["week"] >= pd.Timestamp(cfg.params["period"]["start"])]
    cum = np.nan_to_num(drv.set_index("week").loc[weeks, "de"].to_numpy()).cumsum()
    rows = []
    for u in range(1, n_units + 1):
        lp = 8 + u / 10 + beta * cum + rng.normal(0, 0.01, len(weeks)).cumsum() * 0.3
        if miss and u == 2:
            lp[50:55] = np.nan
        rows.append(pd.DataFrame({"week": weeks, "province_id": u, "commodity": COM, "log_price": lp}))
    return pd.concat(rows, ignore_index=True)


def _world(drv, seed=3):
    return pd.DataFrame({"week": drv["week"], "commodity": COM, "dw": np.random.default_rng(seed).normal(0, 0.01, len(drv))})


def test_one_index_shared_by_prices_drivers_and_world(cfg):
    """De acak unik -> indeks sumber dipulihkan dari de_b; Δp dan dw harus berasal dari minggu sumber yang SAMA."""
    drv, world = _drivers(cfg), _world(_drivers(cfg))
    panel = _panel(cfg, drv, miss=False)
    prep = _Prepared(panel, drv, world)
    rng = np.random.default_rng(0)
    idx = inference.moving_block_indices(prep.n_weeks(), 13, rng)
    pb, db, wb = prep.draw(idx)
    pos = prep.pos
    # penggerak: baris periode = baris sumber idx; buffer tidak berubah
    de_src = drv["de"].to_numpy()
    assert np.allclose(db["de"].to_numpy()[pos], de_src[pos][idx], equal_nan=True)
    assert np.allclose(db["de"].to_numpy()[:pos[0]], de_src[:pos[0]], equal_nan=True)
    # harga: Δp seri u pada minggu t = Δp sumber di minggu idx[t]
    s1 = pb[pb["province_id"] == 1].sort_values("week")["log_price"].to_numpy()
    src = panel[panel["province_id"] == 1].sort_values("week")["log_price"].to_numpy()
    assert np.allclose(np.diff(s1), np.diff(src, prepend=src[0])[idx][1:])
    # harga dunia: dw periode = dw sumber di idx yang sama
    w = wb[wb["commodity"] == COM].sort_values("week")["dw"].to_numpy()
    assert np.allclose(w[pos], world["dw"].to_numpy()[pos][idx])
    # level penggerak dibangun ulang dari de baru (tanpa lompatan di sambungan blok)
    assert np.allclose(np.diff(db["log_e"].to_numpy()[pos]), np.nan_to_num(db["de"].to_numpy()[pos])[1:])


def test_block_structure_and_missing_pattern(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, miss=True)
    prep = _Prepared(panel, drv, None)
    idx = inference.moving_block_indices(prep.n_weeks(), 13, np.random.default_rng(1))
    runs = np.diff(idx) != 1
    assert runs.sum() <= int(np.ceil(prep.n_weeks() / 13))                      # sambungan hanya di batas blok
    pb, _, wb = prep.draw(idx)
    assert wb is None and pb["log_price"].notna().all()
    obs = panel.pivot(index="week", columns="province_id", values="log_price").notna().to_numpy()
    got = pb.pivot(index="week", columns="province_id", values="log_price").reindex(prep.weeks).notna().to_numpy()
    assert (got == obs[idx]).all()                                              # pola data hilang ikut di-resample


def test_joint_bootstrap_shape_seed_and_focus_schedule(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv)
    seen = []

    def est(pb, db, commodities=None):
        seen.append(commodities)
        return national_profiles(cfg, pb, db, None, horizons=[4], commodities=[COM])

    a = joint_bootstrap(cfg, est, panel, drv, 4, B_nonfocus=2)
    b = joint_bootstrap(cfg, est, panel, drv, 4, B_nonfocus=2)
    assert set(a["rep"]) == {0, 1, 2, 3} and {"level", "unit", "commodity", "driver", "horizon", "estimate"} <= set(a.columns)
    assert a["estimate"].equals(b["estimate"])                                   # seed tetap
    assert seen[:2] == [None, None] and all(c == cfg.commodity_ids("focus") for c in seen[2:4])
    e = a[a["driver"] == "e"].groupby("rep")["estimate"].first()
    assert e.std() > 0 and abs(e.mean() - 0.4) < 0.2                             # replikasi bervariasi di sekitar β


def test_joint_bootstrap_passes_resampled_world(cfg):
    drv = _drivers(cfg)
    panel, world = _panel(cfg, drv), _world(drv)
    got = []

    def est(pb, db, wb, commodities=None):
        got.append(wb)
        return national_profiles(cfg, pb, db, wb, horizons=[4], commodities=[COM])

    out = joint_bootstrap(cfg, est, panel, drv, 2, world=world)
    assert len(got) == 2 and not got[0]["dw"].equals(world["dw"]) and set(out["driver"]) >= {"e", "w"}


def test_circular_placebo_rolls_drivers_not_prices(cfg):
    drv, world = _drivers(cfg), _world(_drivers(cfg))
    panel = _panel(cfg, drv)
    seen = []

    def stat(p, d, w, commodities=None):
        seen.append((p, d, w))
        return national_profiles(cfg, p, d, w, horizons=[4], commodities=[COM])

    out = circular_placebo(cfg, stat, panel, drv, 3, world=world)
    assert set(out["rep"]) == {0, 1, 2}
    n, min_shift = len(drv), cfg.params["inference"]["placebo_min_shift_weeks"]
    for p, d, w in seen:
        assert p is panel                                                       # harga tidak digeser
        shifts = [s for s in range(min_shift, n - min_shift + 1)
                  if np.allclose(d["de"].to_numpy(), np.roll(drv["de"].to_numpy(), s), equal_nan=True)]
        assert len(shifts) == 1                                                  # tepat satu pergeseran yang sah
        assert np.allclose(d["de_pos"], np.clip(d["de"], 0, None), equal_nan=True)
        assert np.isclose(w["dw"].sum(), world["dw"].sum())                      # dw digeser, bukan diubah nilainya


def test_placebo_null_is_centered_below_true_effect(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, beta=0.5)
    stat = lambda p, d, commodities=None: national_profiles(cfg, p, d, None, horizons=[8], commodities=[COM])   # noqa: E731
    null = circular_placebo(cfg, stat, panel, drv, 12)
    actual = national_profiles(cfg, panel, drv, None, horizons=[8], commodities=[COM]).query("driver == 'e'")["estimate"].iloc[0]
    null_e = null[null["driver"] == "e"]["estimate"]
    assert abs(actual - 0.5) < 0.2                                             # efek sebenarnya terdeteksi
    assert null_e.abs().mean() < 0.25 and (null_e < actual - 0.15).mean() > 0.8   # null berpusat dekat nol


def _profile(unit, est, se, driver="e"):
    return {"level": "province", "unit": unit, "commodity": COM, "driver": driver, "horizon": 8, "estimate": est,
            "se": se, "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se, "n_weeks": 400, "shrunk": False}


def test_bootstrap_ci_widens_only(cfg):
    prof = pd.DataFrame([_profile("1", 0.0, 0.1), _profile("2", 0.0, 0.1), _profile("3", 0.0, 0.1),
                         _profile("4", 0.0, np.nan, driver="PT")])
    rng = np.random.default_rng(0)
    base = dict(level="province", commodity=COM, horizon=8)
    reps = pd.concat([
        pd.DataFrame({**base, "unit": "1", "driver": "e", "rep": range(500), "estimate": rng.normal(0, 0.3, 500)}),    # lebih lebar
        pd.DataFrame({**base, "unit": "2", "driver": "e", "rep": range(500), "estimate": rng.normal(0, 0.02, 500)}),   # lebih sempit
        pd.DataFrame({**base, "unit": "4", "driver": "PT", "rep": range(500), "estimate": rng.normal(1, 0.2, 500)}),   # se NaN
    ])
    out = bootstrap_ci(prof, reps).set_index("unit")
    assert out.loc["1", "ci_low"] < -0.4 and out.loc["1", "ci_high"] > 0.4          # melebar ke persentil
    assert np.isclose(out.loc["2", "ci_low"], -0.196) and np.isclose(out.loc["2", "ci_high"], 0.196)   # tidak menyempit
    assert np.isclose(out.loc["3", "ci_low"], -0.196)                                # tanpa replikasi: tetap
    assert 0.5 < out.loc["4", "ci_low"] < 0.8 and 1.2 < out.loc["4", "ci_high"] < 1.5     # PT: persentil saja
    assert list(out.columns) == [c for c in prof.columns if c != "unit"]


def _resume_check(cfg, fn):
    """Run penuh == run yang dilanjutkan dari checkpoint pertama (indeks/RNG sama), tanpa mengulang rep selesai."""
    drv = _drivers(cfg)
    panel = _panel(cfg, drv)
    calls = []

    def est(pb, db, commodities=None):
        calls.append(1)
        return national_profiles(cfg, pb, db, None, horizons=[4], commodities=[COM])

    full = fn(cfg, est, panel, drv, 4)
    snaps = []
    fn(cfg, est, panel, drv, 4, checkpoint=snaps.append, checkpoint_every=2)
    assert len(snaps) == 2 and snaps[0]["rep"].nunique() == 2 
    calls.clear()
    resumed = fn(cfg, est, panel, drv, 4, done=snaps[0])
    assert len(calls) == 2
    keys = ["rep", "level", "unit", "commodity", "driver", "horizon"]
    pd.testing.assert_frame_equal(resumed.sort_values(keys).reset_index(drop=True),
                                  full.sort_values(keys).reset_index(drop=True))


def test_bootstrap_resume_equals_full_run(cfg):
    _resume_check(cfg, joint_bootstrap)


def test_placebo_resume_equals_full_run(cfg):
    _resume_check(cfg, circular_placebo)
