"""WP-15: deviasi provinsi & profil wilayah pada data sintetis dengan δ dan β diketahui."""

import numpy as np
import pandas as pd

from kagami.data.drivers import driver_weeks
from kagami.models.deviations import demean_cross_section, province_deviations, region_profiles
from kagami.models.local_projection import PROFILE_COLUMNS, national_profiles

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
    d["month"] = weeks.month
    d["idf_rel_week"] = np.nan
    return d


def _panel(cfg, drv, beta, delta, noise=0.003, seed=2):
    """Harga provinsi u: p_u = base + (beta + delta_u) * kumulatif de + jalan acak kecil; Σ delta = 0."""
    rng = np.random.default_rng(seed)
    weeks = drv["week"][drv["week"] >= pd.Timestamp(cfg.params["period"]["start"])]
    cum = np.nan_to_num(drv.set_index("week").loc[weeks, "de"].to_numpy()).cumsum()
    rows = []
    for u, d in enumerate(delta, start=1):
        lp = 8 + u / 10 + (beta + d) * cum + rng.normal(0, noise, len(weeks)).cumsum() * 0.3
        rows.append(pd.DataFrame({"week": weeks, "province_id": u, "commodity": COM, "log_price": lp}))
    return pd.concat(rows, ignore_index=True)


def test_demean_removes_cross_section_mean(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.3, [-0.2, 0.0, 0.2])
    dev = demean_cross_section(panel)
    assert list(dev.columns) == ["week", "province_id", "commodity", "dev"]
    assert np.allclose(dev.groupby("week")["dev"].sum(), 0)
    one = panel[(panel["week"] == panel["week"].iloc[5])].set_index("province_id")["log_price"]
    got = dev[dev["week"] == panel["week"].iloc[5]].set_index("province_id")["dev"]
    assert np.allclose(got, one - one.mean())


def test_demean_skips_missing_and_respects_eligibility(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.3, [-0.2, 0.0, 0.2])
    t = panel["week"].iloc[10]
    panel.loc[(panel["week"] == t) & (panel["province_id"] == 3), "log_price"] = np.nan
    dev = demean_cross_section(panel)
    d = dev[dev["week"] == t].set_index("province_id")["dev"]
    assert np.isnan(d[3]) and np.isclose(d[1] + d[2], 0)                 # rerata hanya atas provinsi teramati
    elig = pd.DataFrame({"province_id": [1, 2, 3], "commodity": COM, "eligible": [True, True, False]})
    assert set(demean_cross_section(panel, elig)["province_id"]) == {1, 2}


def test_province_deviations_recover_planted_delta(cfg):
    delta = np.array([-0.3, -0.1, 0.0, 0.1, 0.3])
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.4, delta)
    out = province_deviations(cfg, panel, drv, None, horizons=[4, 8], commodities=[COM])
    assert list(out.columns[:len(PROFILE_COLUMNS)]) == PROFILE_COLUMNS
    assert set(out["level"]) == {"province"} and set(out["driver"]) == {"e"}      # world None -> tanpa w
    assert set(out["unit"]) == {"1", "2", "3", "4", "5"} and not out["shrunk"].any()
    for h, g in out.groupby("horizon"):
        g = g.set_index("unit").loc[[str(i) for i in range(1, 6)]]
        assert abs(g["estimate"].sum()) < 1e-12                                   # Σ_r δ = 0
        assert np.all(np.abs(g["estimate"].to_numpy() - delta) < 3 * g["se"].to_numpy() + 0.03)
        assert (g["se"] > 0).all() and (g["n_weeks"] > 400).all()
        assert np.allclose(g["ci_high"] - g["estimate"], 1.96 * g["se"])


def test_province_deviations_respect_eligibility_and_world(cfg):
    drv = _drivers(cfg)
    panel = _panel(cfg, drv, 0.4, [-0.2, 0.0, 0.2])
    world = pd.DataFrame({"week": drv["week"], "commodity": COM,
                          "dw": np.random.default_rng(5).normal(0, 0.01, len(drv))})
    elig = pd.DataFrame({"province_id": [1, 2, 3], "commodity": COM, "eligible": [True, True, False]})
    out = province_deviations(cfg, panel, drv, world, elig=elig, horizons=[4], commodities=[COM])
    assert set(out["unit"]) == {"1", "2"} and set(out["driver"]) == {"e", "w"}
    assert np.allclose(out.groupby("driver")["estimate"].sum(), 0)


def test_region_profiles_match_national_on_single_region(cfg):
    drv = _drivers(cfg)
    base = _panel(cfg, drv, 0.4, [0.0])
    reg = pd.concat([base.assign(region="Jawa", log_price_index=base["log_price"]),
                     _panel(cfg, drv, 0.1, [0.0], seed=9).assign(region="Papua")], ignore_index=True)
    reg["log_price_index"] = reg["log_price_index"].fillna(reg["log_price"])
    out = region_profiles(cfg, reg, drv, None, horizons=[4, 8], commodities=[COM])
    assert set(out["level"]) == {"region"} and set(out["unit"]) == {"Jawa", "Papua"}
    assert {"e", "e_pos", "e_neg", "PT"} <= set(out["driver"])
    e = out[(out["driver"] == "e") & (out["horizon"] == 8)].set_index("unit")
    assert abs(e.loc["Jawa", "estimate"] - 0.4) < 3 * e.loc["Jawa", "se"] + 0.03
    assert abs(e.loc["Papua", "estimate"] - 0.1) < 3 * e.loc["Papua", "se"] + 0.03
    nat = national_profiles(cfg, base, drv, None, horizons=[4, 8], commodities=[COM])
    a = out[out["unit"] == "Jawa"].set_index(["commodity", "driver", "horizon"])["estimate"]
    b = nat.set_index(["commodity", "driver", "horizon"])["estimate"]
    assert np.allclose(a.loc[b.index], b)                       # satu wilayah = LP nasional pada deret itu
