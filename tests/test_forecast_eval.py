"""WP-27: evaluasi rolling-origin (MAE/RMSE, DM HAC, H5 Holm, ablation) pada prediksi sintetis (dummy, bukan hasil)."""

import numpy as np
import pandas as pd
import pytest

from kagami.evaluation import forecast_eval as fe
from kagami.stats.meta import holm


def _preds(cfg, n_prov=6, seed=0):
    """y_true = sinyal kurs + derau. M2 & M3 melihat sinyal hanya untuk komoditas fokus impor langsung;
    M1 & M2_nofx tidak melihat sinyal; M0 = 0."""
    rng = np.random.default_rng(seed)
    p = cfg.params["forecast"]
    o = pd.date_range(p["first_origin"], "2026-08-31", freq=f"{p['origin_step_weeks']}W-MON")
    com = cfg.commodities
    direct = [c for c, v in com.items() if v["role"] == "focus" and v["exposure_path"] == "direct_import"]
    rows = []
    for h in p["horizons"]:
        sig = rng.normal(0, 0.03, len(o))
        large = np.abs(sig) > np.quantile(np.abs(sig), 0.5)
        for c in com:
            beta = 1.0 if c in direct else 0.0
            for r in range(1, n_prov + 1):
                y = beta * sig + rng.normal(0, 0.01, len(o))
                base = rng.normal(0, 0.002, len(o))
                preds = {"M0": np.zeros(len(o)), "M1": base, "M2_nofx": base + rng.normal(0, 0.001, len(o)),
                         "M2": base + beta * sig, "M3": base + beta * sig * 0.9}
                for m, yp in preds.items():
                    rows.append(pd.DataFrame({"origin": o, "horizon": h, "model": m, "province_id": r, "commodity": c,
                                              "y_true": y, "y_pred": yp, "large_move": large}))
    return pd.concat(rows, ignore_index=True)


def test_n_nonoverlap():
    o = pd.date_range("2021-01-04", periods=10, freq="4W-MON")
    assert fe.n_nonoverlap(o, 4) == 10
    assert fe.n_nonoverlap(o, 8) == 5
    assert fe.n_nonoverlap(list(o) + list(o), 8) == 5               # origin berulang (banyak seri) dihitung sekali


def test_holm():
    q = holm(np.array([0.01, 0.04, np.nan, 0.03]))
    assert q[0] == pytest.approx(0.03) and q[3] == pytest.approx(0.06) and q[1] == pytest.approx(0.06)
    assert np.isnan(q[2])


def test_evaluate_contract_and_counts(cfg):
    preds = _preds(cfg)
    out = fe.evaluate(cfg, preds)
    assert list(out.columns[:13]) == fe.EVAL_COLUMNS
    assert set(out["subset"]) == {"all", "large_move", "case_study"}
    cs = out[(out.level == "all") & (out.subset == "case_study") & (out.model == "M1")]
    year = pd.Timestamp(cfg.params["period"]["freeze"]).year
    assert (cs["n_origins"] == (pd.to_datetime(preds["origin"].unique()).year == year).sum()).all()
    assert {"all", "commodity", "region", "path"} == set(out["level"])
    assert set(out.loc[out.level == "region", "region"]) <= set(cfg.regions["region"])
    allrow = out[(out.level == "all") & (out.subset == "all")]
    n_o = preds["origin"].nunique()
    assert (allrow["n_origins"] == n_o).all()
    assert (allrow.loc[allrow.horizon == 8, "n_nonoverlap"] == (n_o + 1) // 2).all()
    assert (allrow.loc[allrow.horizon == 4, "n_nonoverlap"] == n_o).all()
    m1 = out[out.model == "M1"]
    assert np.allclose(m1["mae_ratio_vs_m1"], 1) and m1["dm_stat"].isna().all()
    assert out["n_origins"].notna().all() and out["n_nonoverlap"].notna().all()


def test_evaluate_dm_and_h5(cfg):
    out = fe.evaluate(cfg, _preds(cfg))
    gula = out[(out.commodity == "gula_pasir") & (out.model == "M2") & (out.horizon == 8) & (out.subset == "all")].iloc[0]
    assert gula["mae_ratio_vs_m1"] < 0.6 and gula["dm_stat"] > 0 and gula["dm_p"] < 0.01
    dom = out[(out.commodity == "bawang_merah") & (out.horizon == 8) & (out.subset == "all")].set_index("model")
    assert np.isnan(dom.loc["M2", "dm_stat"])                        # prediksi identik dengan M1 -> DM tak terdefinisi
    assert abs(dom.loc["M2_nofx", "mae_ratio_vs_m1"] - 1) < 0.05 and dom.loc["M2_nofx", "dm_p"] > 0.01
    h5 = out[out["h5_p_holm"].notna()].set_index("commodity")
    assert set(h5.index) == set(fe.H5_PATHS) and (h5["model"] == "M2").all()
    assert (h5["horizon"] == 8).all() and (h5["subset"] == "large_move").all()
    assert h5.loc["direct_import", "h5_reject"] and not h5.loc["imported_input", "h5_reject"]
    assert (h5["h5_p_holm"] >= h5["dm_p_one_sided"].fillna(1.0) - 1e-12).all()
    assert h5.loc["imported_input", "h5_p_holm"] == 1.0                # p tak terdefinisi = 1, keluarga tetap 2
    assert h5.loc["direct_import", "h5_p_holm"] == pytest.approx(2 * h5.loc["direct_import", "dm_p_one_sided"])
    assert out.loc[out["h5_p_holm"].isna(), "h5_reject"].eq(False).all()


def test_evaluate_region_panel(cfg):
    """Panel 7 wilayah (Tingkat B): kolom region langsung, tanpa province_id."""
    preds = _preds(cfg, n_prov=2)
    reg = cfg.regions.set_index("province_id")["region"]
    preds = preds.assign(region=preds["province_id"].map(reg)).drop(columns="province_id")
    out = fe.evaluate(cfg, preds)
    assert set(out.loc[out.level == "region", "region"]) == set(preds["region"])
    ab = fe.ablation(cfg, preds)
    assert len(ab) > 0


def test_ablation(cfg):
    ab = fe.ablation(cfg, _preds(cfg))
    assert list(ab.columns[:6]) == fe.ABLATION_COLUMNS
    a = ab[(ab.subset == "all") & (ab.region == "ALL")].set_index(["horizon", "commodity"])
    assert a.loc[(8, "gula_pasir"), "delta_mae"] > 0.005
    assert abs(a.loc[(8, "bawang_merah"), "delta_mae"]) < 0.001
    assert a.loc[(8, "direct_import"), "delta_mae"] > 0
    with pytest.raises(ValueError):
        fe.ablation(cfg, _preds(cfg, n_prov=1).query("model != 'M2_nofx'"))
