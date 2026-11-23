"""WP-10: QA silang & laporan Tahap 0."""

import numpy as np
import pandas as pd
import pytest

from kagami.data.qa import (BAPANAS_TO_PIHPS, check_bapanas_bias, check_import_totals, check_trade_overlap,
                            coverage_table, flag_price_outliers, stage0_report)


def test_flag_price_outliers():
    dates = pd.bdate_range("2017-06-26", periods=8)
    price = [9500, 9500, 9500, 29750, 9500, 9500, 20000, 20000]       # lonjakan berbalik + perubahan level permanen
    d = pd.DataFrame({"date": dates, "province_id": 34, "commodity": "beras", "variant": "x", "price": price})
    f = flag_price_outliers(d)
    assert list(f["date"]) == [dates[3]]                              # level permanen (hari 6) tidak ditandai
    assert np.isclose(f.loc[0, "dlog_prev"], np.log(29750 / 9500))
    assert len(d) == 8                                                 # tidak menghapus


def test_check_import_totals():
    m = pd.DataFrame({"month": pd.to_datetime(["2023-01-01", "2023-02-01", "2024-01-01", "2024-02-01"]),
                      "hs8_code": "07032010", "import_value_usd": [100.0, 50.0, 10.0, 10.0]})
    a = pd.DataFrame({"hs8_code": "07032010", "year": [2023, 2024], "total": [150.0, 30.0]})
    r = check_import_totals(m, a).set_index("year")
    assert r.loc[2023, "ok"] and not r.loc[2024, "ok"] and np.isclose(r.loc[2024, "ratio"], 20 / 30)


def test_check_bapanas_bias():
    weeks = pd.date_range("2022-01-03", periods=60, freq="W-MON")
    lp = np.log(10000) + 0.01 * np.arange(60)
    w = pd.DataFrame({"week": weeks, "province_id": 1, "commodity": "gula_pasir", "log_price": lp})
    months = w["week"].dt.to_period("M").dt.to_timestamp()
    mm = w.assign(month=months).groupby("month")["log_price"].mean()
    b = pd.DataFrame({"month": mm.index, "commodity_bapanas": "Gula Konsumsi", "province_id": 1,
                      "price_geomean": np.exp(mm.values) / 1.1})
    b = pd.concat([b, b.assign(commodity_bapanas="Minyakita")])       # tidak dipetakan -> diabaikan
    r = check_bapanas_bias(w, b)
    assert list(r["commodity"]) == ["gula_pasir"]
    assert np.isclose(r.loc[0, "bias_log"], np.log(1.1)) and r.loc[0, "corr_dlog"] > 0.99
    assert "Minyakita" not in BAPANAS_TO_PIHPS


def test_stage0_report_sections(cfg):
    cov = coverage_table({"x": (pd.DataFrame({"d": pd.to_datetime(["2020-01-01", "2021-05-01"])}), "d")})
    assert cov.loc[0, "n_rows"] == 2 and str(cov.loc[0, "end"]) == "2021-05-01"
    eps = pd.DataFrame({"episode_id": [1], "start_week": [pd.Timestamp("2020-03-09")]})
    md = stage0_report(cfg, {"coverage": cov, "episodes": eps})
    assert md.startswith("# Laporan Tahap 0") and "## 1. Cakupan" in md and "2020-03-09 |" in md
    assert "00:00:00" not in md and "## 5." not in md                 # bagian tanpa data dilewati


def test_stage0_report_real(cfg):
    from kagami.utils.io import exists, find_artifact
    if not exists(cfg, "stage0_report"):
        pytest.skip("stage0_report belum ada")
    md = find_artifact(cfg, "stage0_report").read_text(encoding="utf-8")
    for sec in ("Cakupan", "Kelayakan", "Episode", "Variasi kurs", "MDE", "lonjakan", "impor", "Bapanas"):
        assert sec in md


def test_check_trade_overlap_synthetic():
    """U102: Σ HS8 BPS yang dipetakan vs Σ Comtrade pada bulan bersama; bulan di luar irisan diabaikan."""
    months = pd.date_range("2022-11-01", "2023-03-01", freq="MS")
    ct = pd.DataFrame({"month": list(months[:3]) * 2, "hs_code": ["0703"] * 3 + ["1006"] * 3,
                       "primary_value_usd": [10.0, 20.0, 30.0, 100.0, 100.0, 100.0],
                       "net_weight_kg": [1.0, 2.0, 3.0, 10.0, 10.0, 10.0]})            # Nov 2022 .. Jan 2023
    bps = pd.DataFrame({"month": [months[1], months[2], months[1], months[2], months[1], months[3]],
                        "hs8_code": ["07031011", "07031019", "10063099", "10063099", "99999999", "07031011"],
                        "import_value_usd": [20.0, 30.0, 90.0, 90.0, 5.0, 999.0],
                        "import_netweight_kg": [2.0, 3.0, 9.0, 9.0, 1.0, 1.0]})       # Des 2022 .. Feb 2023
    conc = pd.DataFrame({"comtrade_code": ["0703", "1006", "0709"],
                         "bps_hs8_codes_in_file": ["07031011; 07031019", "10063099", "07096010"]})
    out = check_trade_overlap(ct, bps, conc).set_index("comtrade_code")
    assert out.loc["0703", "ratio_value"] == pytest.approx(1.0) and out.loc["0703", "ok"]       # irisan Des–Jan
    assert out.loc["0703", "comtrade_usd"] == 50.0 and out.loc["0703", "n_months_bps"] == 2
    assert out.loc["1006", "ratio_value"] == pytest.approx(0.9) and not out.loc["1006", "ok"]   # 10% hilang
    assert out.loc["0709", "ok"] and np.isnan(out.loc["0709", "ratio_value"])                    # keduanya nol
    none = check_trade_overlap(ct.assign(month=ct["month"] - pd.DateOffset(years=3)), bps, conc)
    assert none.empty


def test_check_trade_overlap_real(cfg):
    if not cfg.source_path("comtrade_import_2023").exists() or not cfg.source_path("bps_import_monthly").exists():
        pytest.skip("mentah Comtrade 2023 / BPS tidak ada")
    from kagami.data import loaders
    out = check_trade_overlap(loaders.load_comtrade(cfg, "comtrade_import_2023"), loaders.load_bps_import_monthly(cfg),
                              loaders.load_konkordansi_hs(cfg)).set_index("comtrade_code")
    assert len(out) == 15 and out["ok"].sum() >= 14
    assert out.loc["070320", "ok"] and out.loc["070320", "ratio_value"] == pytest.approx(1.0, abs=1e-3)   # bawang putih
