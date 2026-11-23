"""D-129: inferensi nasional terkalibrasi plasebo (tambahan; interval praregistrasi di profiles tetap)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from kagami.evaluation.calibration import COLUMNS, national_calibrated
from kagami.stats.meta import bh_fdr

SE = 0.1
R = 199
T_OBS = {("gula_pasir", "e", 8): 2.5,     # |t| > 1,96 tetapi plasebo lebar (sd 1,5) -> tidak lolos
         ("beras", "e", 8): 1.9,          # p plasebo kecil (sd 0,7) tetapi |t| < 1,96 -> tidak lolos (p = max)
         ("beras", "w", 4): 3.0}          # lolos keduanya
NULL_SD = {"beras": 0.7, "gula_pasir": 1.5}


def _cells():
    return [(c, d, h) for c in ("beras", "gula_pasir") for d in ("e", "w") for h in (4, 8, 12)]


def _profiles():
    rows = [{"level": "national", "unit": "ALL", "commodity": c, "driver": d, "horizon": h,
             "estimate": T_OBS.get((c, d, h), 0.5) * SE, "se": SE,
             "ci_low": T_OBS.get((c, d, h), 0.5) * SE - 0.3, "ci_high": T_OBS.get((c, d, h), 0.5) * SE + 0.3}
            for c, d, h in _cells()]
    rows += [{"level": "national", "unit": "ALL", "commodity": "beras", "driver": "e", "horizon": 2,   # bukan h kunci
              "estimate": 0.9, "se": SE, "ci_low": 0.0, "ci_high": 1.0},
             {"level": "national", "unit": "ALL", "commodity": "beras", "driver": "PT", "horizon": 8,  # bukan e/w
              "estimate": 0.9, "se": np.nan, "ci_low": 0.0, "ci_high": 1.0},
             {"level": "province", "unit": "1", "commodity": "beras", "driver": "e", "horizon": 8,
              "estimate": 0.9, "se": SE, "ci_low": 0.0, "ci_high": 1.0}]
    return pd.DataFrame(rows)


def _placebo(seed=5):
    rng = np.random.default_rng(seed)
    rows = []
    for c, d, h in _cells():
        t = rng.normal(0.0, NULL_SD[c], R)
        rows.append(pd.DataFrame({"rep": np.arange(R), "level": "national", "unit": "ALL", "commodity": c,
                                  "driver": d, "horizon": h, "estimate": t * SE, "se": SE}))
    return pd.concat(rows, ignore_index=True)


def test_contract_and_filtering(cfg):
    out = national_calibrated(cfg, _profiles(), _placebo())
    assert list(out.columns) == COLUMNS
    assert len(out) == 12                                               # nasional, e/w, h kunci saja
    assert set(out["horizon"]) == {4, 8, 12} and set(out["driver"]) == {"e", "w"}
    assert (out["n_placebo"] == R).all()


def test_interval_and_p_consistent(cfg):
    out = national_calibrated(cfg, _profiles(), _placebo()).set_index(["commodity", "driver", "horizon"])
    z = stats.norm.ppf(0.975)
    assert (out["crit"] >= z - 1e-12).all()                                       # tidak pernah lebih sempit dari SE
    assert np.allclose(out["ci_high"] - out["ci_low"], 2 * out["crit"] * out["se"])
    assert ((out["p_value"] < 0.05) == out["ci_excludes_zero"]).all()             # p < α ⇔ interval tidak memuat nol
    assert not out.loc[("gula_pasir", "e", 8), "ci_excludes_zero"]                 # plasebo lebar menolak |t| = 2,5
    assert out.loc[("gula_pasir", "e", 8), "crit"] > 2.5
    b = out.loc[("beras", "e", 8)]
    assert b["p_placebo"] < 0.05 and b["p_value"] >= 0.05 and not b["ci_excludes_zero"]
    assert np.isclose(b["crit"], z)                                               # plasebo sempit -> lantai 1,96
    assert out.loc[("beras", "w", 4), "ci_excludes_zero"]
    assert np.allclose(out["q_fdr"], bh_fdr(out["p_value"].to_numpy()))
    assert np.allclose(out["ci_prereg_low"], out["estimate"] - 0.3)              # interval praregistrasi dibawa


def test_crit_is_order_statistic_and_p_placebo_exact(cfg):
    pl = _placebo()
    out = national_calibrated(cfg, _profiles(), pl).set_index(["commodity", "driver", "horizon"])
    g = pl[(pl["commodity"] == "gula_pasir") & (pl["driver"] == "e") & (pl["horizon"] == 8)]
    t_null = np.sort(np.abs(g["estimate"] / g["se"]).to_numpy())[::-1]
    assert np.isclose(out.loc[("gula_pasir", "e", 8), "crit_placebo"], t_null[8])  # R = 199 -> peringkat ke-9 terbesar
    n_ge = int((t_null >= 2.5).sum())
    assert np.isclose(out.loc[("gula_pasir", "e", 8), "p_placebo"], (1 + n_ge) / (1 + R))


def test_boot_ratio_shows_attenuation(cfg):
    prof = _profiles()
    nat = prof[(prof["level"] == "national") & prof["driver"].isin(["e", "w"])]
    boot = pd.concat([nat.assign(rep=r, estimate=0.5 * nat["estimate"] + 0.001 * (r - 24)) for r in range(49)],
                     ignore_index=True)
    out = national_calibrated(cfg, prof, _placebo(), boot)
    assert np.allclose(out["boot_ratio"], 0.5) and (out["n_boot"] == 49).all()


def test_without_placebo_falls_back_to_normal(cfg):
    out = national_calibrated(cfg, _profiles(), None)
    z = stats.norm.ppf(0.975)
    assert np.allclose(out["crit"], z) and (out["n_placebo"] == 0).all() and out["p_placebo"].isna().all()
    assert np.allclose(out["p_value"], 2 * stats.norm.sf((out["estimate"] / out["se"]).abs()))
    assert out["boot_ratio"].isna().all()


def test_placebo_without_se_raises(cfg):
    with pytest.raises(KeyError):
        national_calibrated(cfg, _profiles(), _placebo().drop(columns="se"))
