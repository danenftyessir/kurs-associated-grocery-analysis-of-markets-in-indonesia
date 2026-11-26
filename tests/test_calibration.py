"""D-129: inferensi nasional terkalibrasi plasebo (tambahan; interval praregistrasi di profiles tetap)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from kagami.evaluation.calibration import COLUMNS, PROVINCE_COLUMNS, national_calibrated, province_calibrated
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
    ew = out[out["driver"].isin(["e", "w"])]
    assert len(ew) == 12                                                # nasional, e/w, h kunci saja
    assert set(ew["horizon"]) == {4, 8, 12}
    assert set(out["driver"]) == {"e", "w", "PT"} and len(out) == 13    # D-163: PT hanya bila profiles punya PT nasional
    assert (out["n_placebo"] == R).all()


def test_interval_and_p_consistent(cfg):
    out = national_calibrated(cfg, _profiles(), _placebo())
    out = out[out["driver"] != "PT"].set_index(["commodity", "driver", "horizon"])
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
    out = out[out["driver"] != "PT"]
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


def test_pt_rows_rescale_e_inference(cfg):
    """D-163 (U107): baris PT = baris e yang diskalakan 1/γ; p, q, crit, dan status interval sama dengan baris e."""
    prof = _profiles()
    e8 = T_OBS[("beras", "e", 8)] * SE
    gamma = e8 / 0.9                                                   # profiles: PT beras h 8 = 0,9
    out = national_calibrated(cfg, prof, _placebo()).set_index(["commodity", "driver", "horizon"])
    e, pt = out.loc[("beras", "e", 8)], out.loc[("beras", "PT", 8)]
    assert np.isclose(pt["estimate"], 0.9) and np.isclose(pt["se"], e["se"] / gamma)
    assert np.isclose(pt["ci_low"], e["ci_low"] / gamma) and np.isclose(pt["ci_high"], e["ci_high"] / gamma)
    for c in ("crit", "p_value", "q_fdr", "ci_excludes_zero", "p_placebo"):
        assert pt[c] == e[c]
    assert np.isclose(pt["ci_prereg_low"], 0.0) and np.isclose(pt["ci_prereg_high"], 1.0)


def _province_inputs(seed=11, n_prov=34, null_sd=1.4, planted=6.0):
    """δ provinsi: satu provinsi tertanam (|t| = planted), lainnya derau; plasebo t* ~ N(0, null_sd) (SE terlalu sempit)."""
    rng = np.random.default_rng(seed)
    rows, pl = [], []
    for d in ("e", "w"):
        for h in (4, 8, 12):
            t = rng.normal(0, 1.0, n_prov)
            if (d, h) == ("e", 8):
                t[0] = planted
            for i in range(n_prov):
                for shr in (False, True):
                    rows.append({"level": "province", "unit": str(i + 1), "commodity": "telur_ayam", "driver": d,
                                 "horizon": h, "estimate": t[i] * SE * (0.5 if shr else 1.0), "se": SE,
                                 "ci_low": t[i] * SE - 0.5, "ci_high": t[i] * SE + 0.5, "shrunk": shr})
            tn = rng.normal(0, null_sd, (R, n_prov))
            pl.append(pd.DataFrame({"rep": np.repeat(np.arange(R), n_prov), "level": "province",
                                    "unit": np.tile(np.arange(1, n_prov + 1), R), "commodity": "telur_ayam",
                                    "driver": d, "horizon": h, "estimate": tn.ravel() * SE, "se": SE}))
    rows.append({"level": "national", "unit": "ALL", "commodity": "telur_ayam", "driver": "e", "horizon": 8,
                 "estimate": 1.0, "se": SE, "ci_low": 0.0, "ci_high": 2.0, "shrunk": False})
    return pd.DataFrame(rows), pd.concat(pl, ignore_index=True)


def test_province_calibrated_contract_and_null(cfg):
    prof, pl = _province_inputs()
    out = province_calibrated(cfg, prof, pl)
    assert list(out.columns) == PROVINCE_COLUMNS
    assert len(out) == 2 * 3 * 34 and (out["n_placebo"] == R * 34).all()          # provinsi, e/w, h kunci, δ mentah
    assert ((out["p_value"] < 0.05) == out["ci_excludes_zero"]).all()
    assert (out["crit"] > 1.96 * 1.2).all()                                        # null lebih lebar dari N(0,1)
    g = pl[(pl["driver"] == "e") & (pl["horizon"] == 8)]
    t_null = np.sort(np.abs(g["estimate"] / g["se"]).to_numpy())[::-1]
    k = int(np.ceil(0.05 * (len(t_null) + 1) - 1e-9)) - 1
    row = out[(out["driver"] == "e") & (out["horizon"] == 8)].set_index("unit")
    assert np.isclose(row["crit_placebo"].iloc[0], t_null[k - 1])
    assert np.isclose(row.loc["1", "p_placebo"], (1 + (t_null >= 6.0).sum()) / (1 + len(t_null)))
    assert row.loc["1", "ci_excludes_zero"] and row.loc["1", "q_fdr"] < 0.05       # provinsi tertanam terdeteksi
    assert np.isclose(row.loc["1", "estimate_shrunk"], 0.5 * row.loc["1", "estimate"])
    assert out["ci_excludes_zero"].mean() < 0.05                                   # derau: SE terlalu sempit dikoreksi
    q = row["q_fdr"].to_numpy()
    assert np.allclose(np.sort(q), np.sort(bh_fdr(row["p_value"].to_numpy())))     # BH per sel atas provinsi


def test_province_calibrated_without_placebo_and_boot(cfg):
    prof, pl = _province_inputs()
    out = province_calibrated(cfg, prof, None)
    assert np.allclose(out["crit"], stats.norm.ppf(0.975)) and out["p_placebo"].isna().all()
    raw = prof[(prof["level"] == "province") & ~prof["shrunk"]]
    boot = pd.concat([raw.assign(rep=r, estimate=0.4 * raw["estimate"]) for r in range(9)], ignore_index=True)
    out = province_calibrated(cfg, prof, pl, boot)
    assert np.allclose(out["boot_ratio"], 0.4) and (out["n_boot"] == 9).all()
    with pytest.raises(KeyError):
        province_calibrated(cfg, prof, pl.drop(columns="se"))
