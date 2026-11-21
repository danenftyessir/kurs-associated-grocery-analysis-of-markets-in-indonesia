"""WP-13 (sebagian): build_design, fit_lp, fx_self_response pada data sintetis dengan β diketahui."""

import numpy as np
import pandas as pd
import pytest

from kagami.data.drivers import driver_weeks
from kagami.models.local_projection import build_design, fit_lp, fx_self_response, national_profiles, regressors


def _drivers(cfg, seed=1, sd=0.01):
    rng = np.random.default_rng(seed)
    weeks = driver_weeks(cfg)
    de = rng.normal(0, sd, len(weeks))
    de[0] = np.nan
    d = pd.DataFrame({"week": weeks, "de": de})
    d["log_e"] = 9.5 + np.nan_to_num(de).cumsum()
    d["de_pos"], d["de_neg"] = d["de"].clip(lower=0), d["de"].clip(upper=0)
    d["db"] = rng.normal(0, 0.03, len(weeks))
    d["month"] = weeks.month
    d["idf_rel_week"] = np.nan
    return d


def _panel(cfg, drv, b_pos, b_neg, n_units=20, noise=0.01, seed=2, w=None, b_w=0.0):
    rng = np.random.default_rng(seed)
    weeks = drv["week"][drv["week"] >= pd.Timestamp(cfg.params["period"]["start"])]
    d = drv.set_index("week").loc[weeks]
    common = b_pos * d["de_pos"].cumsum() + b_neg * d["de_neg"].cumsum()
    if w is not None:
        common = common + b_w * w.set_index("week").loc[weeks, "dw"].fillna(0).cumsum()
    rows = []
    for u in range(1, n_units + 1):
        lp = 8 + u / 10 + common.to_numpy() + rng.normal(0, noise, len(weeks)).cumsum() * 0.3
        rows.append(pd.DataFrame({"week": weeks, "province_id": u, "commodity": "gula_pasir", "log_price": lp}))
    return pd.concat(rows, ignore_index=True)


def test_design_shape_and_names(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.3, 0.3, n_units=3)
    D = build_design(cfg, panel, drv, None, "gula_pasir", 4, 4)
    reg = regressors(D)
    assert reg[:5] == ["de", "de_l1", "de_l2", "de_l3", "de_l4"]
    assert {"dp_l1", "dp_l4", "db_l0", "db_l4", "month_12"} <= set(reg) and "month_1" not in reg
    assert not any(c.startswith("dw") for c in reg)               # world None -> tanpa dw
    assert D.attrs["n_dropped"] > 0                                # awal (lag Δp) & akhir (t+h) sampel
    assert np.allclose(D.groupby("unit")[["y", "de"]].mean(), 0)  # within-transform per seri
    assert (D["group"] == D["week"]).all()
    assert D["week"].max() <= pd.Timestamp(cfg.params["period"]["freeze"]) - pd.Timedelta(weeks=4)


def test_fit_lp_recovers_beta(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.4, 0.4)
    for h in (0, 4, 8):
        r = fit_lp(cfg, build_design(cfg, panel, drv, None, "gula_pasir", h, 4)).set_index("driver")
        assert abs(r.loc["e", "estimate"] - 0.4) < 2.5 * r.loc["e", "se"]
        assert r.loc["e", "n_weeks"] > 400


def test_fit_lp_asymmetric_and_world(cfg):
    drv = _drivers(cfg)
    rng = np.random.default_rng(5)
    w = pd.DataFrame({"week": drv["week"], "commodity": "gula_pasir", "dw": rng.normal(0, 0.03, len(drv))})
    panel = _panel(cfg, drv, 0.6, 0.1, w=w, b_w=0.2)
    r = fit_lp(cfg, build_design(cfg, panel, drv, w, "gula_pasir", 0, 4, asymmetric=True)).set_index("driver")
    assert set(r.index) == {"e_pos", "e_neg", "w"}
    for drv_name, b in (("e_pos", 0.6), ("e_neg", 0.1), ("w", 0.2)):
        assert abs(r.loc[drv_name, "estimate"] - b) < 2.5 * r.loc[drv_name, "se"]


def test_design_eligibility_filter(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.3, 0.3, n_units=4)
    elig = pd.DataFrame({"province_id": [1, 2, 3, 4], "commodity": "gula_pasir", "eligible": [1, 1, 0, 1]})
    D = build_design(cfg, panel, drv, None, "gula_pasir", 0, 4, elig=elig)
    assert set(D["unit"]) == {1, 2, 4}


def test_fx_self_response(cfg):
    drv = _drivers(cfg)
    assert np.isclose(fx_self_response(cfg, drv, 0, 4), 1.0)        # γ(0) = 1 menurut konstruksi
    assert abs(fx_self_response(cfg, drv, 8, 4) - 1.0) < 0.3         # de iid -> γ(h) ≈ 1


def test_fx_self_response_real(cfg):
    from kagami.utils.io import exists, read_artifact
    if not exists(cfg, "drivers_weekly"):
        pytest.skip("drivers_weekly belum ada")
    drv = read_artifact(cfg, "drivers_weekly")
    g = [fx_self_response(cfg, drv, h, cfg.params["lp"]["lags"]) for h in cfg.params["lp"]["key_horizons"]]
    assert all(np.isfinite(g)) and all(0.2 < x < 3 for x in g)


def test_national_profiles_synthetic(cfg):
    from kagami.models.local_projection import PROFILE_COLUMNS, national_profiles
    drv = _drivers(cfg, seed=21)
    rng = np.random.default_rng(22)
    w = pd.DataFrame({"week": drv["week"], "commodity": "gula_pasir", "dw": rng.normal(0, 0.03, len(drv))})
    panel = _panel(cfg, drv, 0.5, 0.2, n_units=10, w=w, b_w=0.3)
    prof = national_profiles(cfg, panel, drv, w, horizons=[0, 4])
    assert list(prof.columns[:len(PROFILE_COLUMNS)]) == PROFILE_COLUMNS
    assert set(prof["commodity"]) == {"gula_pasir"}                   # komoditas tanpa data dilewati
    assert (prof["level"] == "national").all() and (prof["unit"] == "ALL").all() and not prof["shrunk"].any()
    counts = prof.groupby("horizon")["driver"].apply(sorted).to_dict()
    assert counts[0] == ["PT", "e", "e_neg", "e_pos", "w"]             # w hanya dari spesifikasi simetris
    p0 = prof[prof["horizon"] == 0].set_index("driver")
    assert np.isclose(p0.loc["PT", "estimate"], p0.loc["e", "estimate"])   # γ(0) = 1
    assert np.isnan(p0.loc["PT", "se"]) and np.isnan(p0.loc["PT", "ci_low"])  # interval PT dari bootstrap
    for d, b in (("e_pos", 0.5), ("e_neg", 0.2), ("w", 0.3)):
        assert p0.loc[d, "ci_low"] - 0.5 * (p0.loc[d, "ci_high"] - p0.loc[d, "ci_low"]) < b \
            < p0.loc[d, "ci_high"] + 0.5 * (p0.loc[d, "ci_high"] - p0.loc[d, "ci_low"])
    assert np.allclose(p0["ci_high"].dropna() - p0["estimate"].dropna().loc[p0["ci_high"].dropna().index],
                       1.96 * p0["se"].dropna())


def test_national_profiles_fast_path_equals_design_loop(cfg):
    """Jalur cepat (desain dibangun sekali per spesifikasi, D-118) = build_design + fit_lp per horizon."""
    drv = _drivers(cfg, seed=31)
    rng = np.random.default_rng(32)
    w = drv[["week"]].assign(commodity="gula_pasir", dw=rng.normal(0, 0.02, len(drv)))
    w["log_w_idr"] = w["dw"].cumsum()
    panel = _panel(cfg, drv, 0.5, 0.2, n_units=6, w=w, b_w=0.3)
    panel = panel.drop(index=panel.sample(frac=0.05, random_state=1).index)        # minggu hilang acak
    prof = national_profiles(cfg, panel, drv, w, horizons=[0, 3, 8])
    L = int(cfg.params["lp"]["lags"])
    for h in (0, 3, 8):
        for asym in (False, True):
            f = fit_lp(cfg, build_design(cfg, panel, drv, w, "gula_pasir", h, L, asym)).set_index("driver")
            for d in f.index:
                if asym and d == "w":
                    continue
                r = prof[(prof.horizon == h) & (prof.driver == d)].iloc[0]
                assert np.isclose(r["estimate"], f.loc[d, "estimate"], rtol=1e-10, atol=1e-12)
                assert np.isclose(r["se"], f.loc[d, "se"], rtol=1e-10, atol=1e-12)
                assert r["n_obs"] == f.loc[d, "n_obs"] and r["n_weeks"] == f.loc[d, "n_weeks"]


def test_build_design_y_matches_manual(cfg):
    """y^{(h)} = p_{t+h} - p_{t-1} per unit sebelum within-transform; baris NaN dibuang."""
    drv = _drivers(cfg, seed=41)
    panel = _panel(cfg, drv, 0.3, 0.3, n_units=2)
    h, L = 5, int(cfg.params["lp"]["lags"])
    D = build_design(cfg, panel, drv, None, "gula_pasir", h, L)
    u1 = panel[panel.province_id == 1].set_index("week")["log_price"]
    raw = (u1.shift(-h) - u1.shift(1)).reindex(D.loc[D.unit == 1, "week"]).to_numpy()
    assert np.allclose(D.loc[D.unit == 1, "y"].to_numpy(), raw - raw.mean())
