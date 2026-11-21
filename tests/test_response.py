"""WP-17: penyusutan EB deviasi provinsi dan fitur respons pada profil sintetis dengan jawaban diketahui."""

import numpy as np
import pandas as pd

from kagami.features.response import FEATURE_COLUMNS, response_features, shrink_deviations

COM = "gula_pasir"


def _row(level, unit, driver, h, est, se, shrunk=False):
    return {"level": level, "unit": unit, "commodity": COM, "driver": driver, "horizon": h, "estimate": est, "se": se,
            "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se, "n_weeks": 400, "shrunk": shrunk}


def _provinces(deltas, ses, h=8, driver="e"):
    return [_row("province", str(i), driver, h, d, s) for i, (d, s) in enumerate(zip(deltas, ses), start=1)]


def test_shrink_pulls_noisy_provinces_to_mean(cfg):
    deltas = np.array([-0.5, -0.2, 0.0, 0.2, 0.5])
    ses = np.array([0.05, 0.05, 0.05, 0.4, 0.4])                    # provinsi 4-5: derau besar -> susut kuat
    out = shrink_deviations(cfg, pd.DataFrame(_provinces(deltas, ses)))
    raw, sh = out[~out["shrunk"]], out[out["shrunk"]].set_index("unit")
    assert len(raw) == 5 and len(sh) == 5 and set(sh["level"]) == {"province"}
    s = sh["estimate"].to_numpy()
    assert abs(s[4]) < abs(deltas[4]) and abs(s[3]) < abs(deltas[3])
    assert abs(s[0] - deltas[0]) < abs(s[4] - deltas[4])            # yang presisi tetap dekat estimasi asli
    assert (sh["se"] > 0).all() and np.allclose(sh["ci_high"] - sh["estimate"], 1.96 * sh["se"])


def test_shrink_tau2_zero_collapses_to_mean(cfg):
    deltas = np.array([0.01, -0.01, 0.0, 0.005, -0.005])            # beda jauh lebih kecil dari se -> τ² = 0
    out = shrink_deviations(cfg, pd.DataFrame(_provinces(deltas, np.full(5, 0.3))))
    sh = out[out["shrunk"]]["estimate"].to_numpy()
    assert np.allclose(sh, sh[0])                                    # semua = μ (temuan sah)


def test_shrink_skips_small_cells_and_keeps_other_levels(cfg):
    rows = _provinces([0.1], [0.1]) + [_row("national", "ALL", "e", 8, 0.3, 0.1)] + _provinces([0.2, -0.2], [0.1, 0.1], h=4)
    out = shrink_deviations(cfg, pd.DataFrame(rows))
    assert out["shrunk"].sum() == 2 and (out.loc[out["shrunk"], "horizon"] == 4).all()      # sel dengan 1 provinsi dilewati
    assert (out["level"] == "national").sum() == 1


def _curve(driver, level, unit, est_by_h, se=0.05):
    return [_row(level, unit, driver, h, est, se) for h, est in est_by_h.items()]


def test_response_features_national_values_and_t_half(cfg):
    e = {h: 0.1 * min(h, 8) for h in range(13)}                      # naik sampai h=8 lalu datar: maks 0,8 -> t_half = 4
    rows = (_curve("e", "national", "ALL", e) + _curve("w", "national", "ALL", {h: 0.05 * h for h in range(13)})
            + _curve("PT", "national", "ALL", {h: 0.5 * h for h in range(13)})
            + _curve("e_pos", "national", "ALL", {8: 0.9}) + _curve("e_neg", "national", "ALL", {8: 0.3}))
    f = response_features(cfg, pd.DataFrame(rows)).set_index(["level", "unit", "commodity"])
    r = f.loc[("national", "ALL", COM)]
    assert list(f.reset_index().columns) == FEATURE_COLUMNS
    assert np.isclose(r["R4"], 0.4) and np.isclose(r["R8"], 0.8) and np.isclose(r["R12"], 0.8)
    assert np.isclose(r["W4"], 0.2) and np.isclose(r["W12"], 0.6) and np.isclose(r["PT8"], 4.0)
    assert np.isclose(r["A8"], 0.6) and r["t_half"] == 4


def test_t_half_nan_when_interval_covers_zero_and_handles_negative(cfg):
    flat = _curve("e", "national", "ALL", {h: 0.01 * h for h in range(13)}, se=0.5)          # CI memuat nol
    f = response_features(cfg, pd.DataFrame(flat)).iloc[0]
    assert np.isnan(f["t_half"]) and np.isnan(f["W4"]) and np.isnan(f["PT8"])
    neg = _curve("e", "national", "ALL", {h: -0.1 * min(h, 6) for h in range(13)})            # respons negatif
    assert response_features(cfg, pd.DataFrame(neg)).iloc[0]["t_half"] == 3


def test_province_features_use_national_plus_shrunk_delta(cfg):
    nat = (_curve("e", "national", "ALL", {4: 0.4, 8: 0.8, 12: 0.8}) + _curve("PT", "national", "ALL", {8: 0.4}))
    prov = _provinces([0.3, -0.3, 0.1, -0.1], [0.05] * 4, h=8) + _provinces([0.3, -0.3, 0.1, -0.1], [0.05] * 4, h=4)
    prof = shrink_deviations(cfg, pd.DataFrame(nat + prov))
    f = response_features(cfg, prof).set_index(["level", "unit", "commodity"])
    sh = prof[prof["shrunk"] & (prof["horizon"] == 8)].set_index("unit")["estimate"]
    for u in ("1", "2", "3", "4"):
        r = f.loc[("province", u, COM)]
        assert np.isclose(r["R8"], 0.8 + sh[u]) and np.isclose(r["PT8"], r["R8"] / 2.0)      # γ(8) = 0,8 / 0,4 = 2
        assert np.isnan(r["A8"])
    assert (f.loc[("national", "ALL", COM), "R8"] == 0.8)


def test_response_features_without_shrunk_rows_ignores_provinces(cfg):
    rows = _curve("e", "national", "ALL", {4: 0.4, 8: 0.8, 12: 0.8}) + _provinces([0.3, -0.3], [0.05, 0.05])
    f = response_features(cfg, pd.DataFrame(rows))
    assert set(f["level"]) == {"national"}                           # deviasi mentah tidak dipakai sebagai respons
