"""Halaman Streamlit dengan artefak sintetis berskema kontrak: setiap halaman terender tanpa exception (WP-31)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config
from kagami.utils.io import write_artifact

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = [APP / "Home.py", *sorted((APP / "pages").glob("*.py"))]
COMS = ["bawang_putih", "gula_pasir", "daging_ayam"]
REGIONS = ["Sumatra", "Jawa"]


def _profiles():
    rows = []
    for com in COMS:
        for level, units in (("national", ["ALL"]), ("region", REGIONS), ("province", ["1", "2", "3"])):
            for drv in ("e", "w", "PT"):
                for h in range(13):
                    est = 0.05 * h
                    rows.append({"level": level, "unit": units[0] if len(units) == 1 else units[h % len(units)],
                                 "commodity": com, "driver": drv, "horizon": h, "estimate": est, "se": 0.02,
                                 "ci_low": est - 0.04, "ci_high": est + 0.04, "n_weeks": 400, "shrunk": False})
    return pd.DataFrame(rows).drop_duplicates(["level", "unit", "commodity", "driver", "horizon"])


def _features():
    rows = [{"level": lv, "unit": u, "commodity": c, "R4": .1, "R8": .2, "R12": .3, "W4": .0, "W8": .1, "W12": .1,
             "PT8": .5, "t_half": 4.0, "A8": np.nan}
            for c in COMS for lv, u in (("national", "ALL"), ("region", "Jawa"), ("province", "1"), ("province", "2"))]
    return pd.DataFrame(rows)


def _weekly():
    """drivers_weekly & panel_weekly sintetis 2018–2019 untuk halaman lini masa rupiah dan profil provinsi (D-175)."""
    weeks = pd.date_range("2018-01-01", periods=104, freq="W-MON")
    drv = pd.DataFrame({"week": weeks, "log_e": np.log(13500 + 10 * np.arange(104)), "de": 0.001, "de_pos": 0.001,
                        "de_neg": 0.0, "log_brent": 4.0, "db": 0.0, "log_dxy": 4.6, "d_dxy": 0.0,
                        "month": weeks.month, "idf_rel_week": np.nan, "episode": 0})
    rows = [{"week": w, "province_id": p, "commodity": c, "price": 10000 + 5 * i + 100 * p, "n_days": 5,
             "status": "observed" if i % 5 else "carry_forward"}
            for p in (1, 2, 3) for c in COMS for i, w in enumerate(weeks)]
    pan = pd.DataFrame(rows).assign(log_price=lambda d: np.log(d["price"]))
    return drv, pan


def _artifacts():
    prof = _profiles()
    ids = [1, 2, 3]
    drv, pan = _weekly()
    return {
        "drivers_weekly": drv, "panel_weekly": pan,
        "province_calibrated": pd.DataFrame({
            "commodity": COMS[0], "driver": "e", "horizon": 8, "unit": ids, "estimate": [.5, -.1, .0], "se": .1,
            "ci_low": [.3, -.3, -.2], "ci_high": [.7, .1, .2], "p_value": [1e-6, .4, .9], "q_fdr": [1e-5, .6, .9]}),
        "profiles": prof, "response_features": _features(),
        "events": pd.DataFrame({"episode_id": 1, "level": "national", "unit": "ALL", "commodity": COMS[0],
                                "horizon": range(13), "dlog_price": 0.001 * np.arange(13), "placebo_lo": -0.02,
                                "placebo_hi": 0.02, "placebo_p": 0.3}),
        "episodes": pd.DataFrame({"episode_id": [1], "start_week": ["2020-03-02"], "end_week": ["2020-04-27"],
                                  "cum_dlog_e": [0.12]}),
        "heterogeneity": pd.DataFrame({"commodity": COMS, "horizon": 8, "statistic": "Q", "value": [10., 20., 30.],
                                       "p_placebo": [.5, .1, .01], "q_fdr": [.5, .15, .03]}),
        "cluster_selection": pd.DataFrame({"k": [1, 2], "silhouette": [np.nan, .1], "placebo_p95": [.2, .2],
                                           "accepted": [True, False]}),
        "clusters": pd.DataFrame({"province_id": ids * 2, "method": ["ward"] * 3 + ["kmeans"] * 3, "k": 2,
                                  "cluster": ["K1", "K1", "K2"] * 2, "jaccard": [.9, .9, .5] + [np.nan] * 3,
                                  "weak": [False, False, True] + [False] * 3}),
        "coassign": pd.DataFrame({"province_i": np.repeat(ids, 3), "province_j": np.tile(ids, 3), "share": 1.0}),
        "partition_compare": pd.DataFrame({"partition": ["het_zone_beras"], "ari": [.1], "n_groups": [3]}),
        "national_calibrated": pd.DataFrame({
            "commodity": COMS[0], "driver": ["e", "e", "w"], "horizon": [4, 8, 8], "estimate": [.2, .3, .1],
            "se": .1, "ci_low": [-.05, .02, -.1], "ci_high": [.45, .58, .3], "p_value": [.1, .03, .4],
            "q_fdr": [.2, .09, .4], "ci_prereg_low": [-.1, -.05, -.15], "ci_prereg_high": [.5, .6, .35],
            "boot_ratio": [.6, .4, .5]}),
        "asymmetry": pd.DataFrame({"commodity": COMS[0], "horizon": [4, 8], "beta_pos": [.3, .4],
                                   "beta_neg": [.1, .2], "estimate": [.2, .2], "se": .1, "ci_low": [-.1, -.05],
                                   "ci_high": [.5, .45], "p_value": [.05, .04], "confirmatory": [False, True],
                                   "reject": [False, True], "p_placebo": [.1, .06]}),
        "regime_profiles": pd.DataFrame({"commodity": COMS[0], "regime_id": [1, 2], "regime_start": ["2018-01-01",
                                         "2022-01-03"], "regime_end": ["2021-12-27", "2026-11-16"], "driver": "e",
                                         "horizon": 8, "estimate": [.1, .3], "ci_low": [-.2, .0], "ci_high": [.4, .6],
                                         "n_weeks": [200, 250], "label": ["awal", "Perbadan 5/2022"],
                                         "q_fdr": [.5, .3]}),
        "planted_recovery": pd.DataFrame({"delta": [.1, .5], "k_true": [2, 2], "recovery_rate": [.1, .9],
                                          "ari_mean": [.2, .9]}),
        "exposure": pd.DataFrame({"commodity": COMS, "exposure_path": ["direct_import"] * 3,
                                  "import_ratio_direct": [.9, .5, .01], "imported_input_ordinal": [0, 0, 2],
                                  "world_price_link": [False, True, True], "source": "dummy"}),
        "assoc": pd.DataFrame({"level": ["province"], "feature": ["ln_dist_hub"], "outcome": ["e_h4"],
                               "estimate": [-.1], "ci_low": [-.2], "ci_high": [.0], "p_value": [.04],
                               "method": ["meta_regression_re_one_sided"], "jackknife_min": [-.15],
                               "jackknife_max": [-.05], "commodity": ["ALL"]}),
        "forecast_eval": pd.DataFrame({"horizon": [8, 8], "model": ["M2", "M3"], "subset": ["all", "all"],
                                       "commodity": [COMS[0]] * 2, "region": ["ALL"] * 2, "mae": [.1, .1],
                                       "rmse": [.1, .1], "mae_ratio_vs_m1": [.9, 1.0], "rmse_ratio_vs_m1": [.9, 1.0],
                                       "dm_stat": [1., 0.], "dm_p": [.1, .5], "n_origins": [60, 60],
                                       "n_nonoverlap": [30, 30], "h5_p_holm": [.2, np.nan]}),
        "ablation": pd.DataFrame({"horizon": [8], "commodity": [COMS[0]], "region": ["ALL"], "mae_full": [.1],
                                  "mae_without_fx": [.11], "delta_mae": [.01]}),
        "findings": "# Temuan\n\nDummy.", "robustness": pd.DataFrame({
            "check_id": ["T1"], "tier": [1], "commodity": [COMS[0]], "horizon": [8], "estimate": [.1],
            "ci_low": [0.], "ci_high": [.2], "baseline_estimate": [.1], "note": ["dummy"], "driver": ["e"],
            "variant": ["L=2"]}),
        "eligibility": pd.DataFrame({"province_id": [1, 11], "commodity": [COMS[0]] * 2, "missing_share": [0.] * 2,
                                     "max_gap_weeks": [0] * 2, "min_year_coverage": [1.] * 2, "eligible": [True] * 2}),
        "mde": pd.DataFrame({"commodity": COMS, "level": "national", "horizon": 8, "mde_beta": .1, "mde_pt": .2}),
    }


@pytest.fixture
def with_artifacts(tmp_path, monkeypatch, cfg):
    c = Config(root=cfg.root, out_root=tmp_path)
    for name, df in _artifacts().items():
        write_artifact(c, name, df)
    monkeypatch.setenv("KAGAMI_OUT_DIR", str(tmp_path))
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    st.cache_data.clear()
    yield tmp_path
    sys.modules.pop("common", None)
    st.cache_data.clear()


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.stem)
def test_page_runs_with_data(page, with_artifacts):
    at = AppTest.from_file(str(page), default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    waiting = [i.value for i in at.info if "Menunggu hasil" in i.value]
    assert page.stem in ("Home",) or not waiting, waiting              # semua artefak halaman ini tersedia


def test_load_does_not_cache_missing(tmp_path, monkeypatch):
    """Regresi D-135: artefak yang muncul setelah proses app jalan (git pull Streamlit Cloud) harus terbaca, begitu juga versi barunya."""
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    st.cache_data.clear()
    import common
    c = Config(root=tmp_path, out_root=tmp_path)
    monkeypatch.setattr(common, "CFG", c)
    assert common.load("episodes") is None
    ep = _artifacts()["episodes"]
    write_artifact(c, "episodes", ep)
    assert len(common.load("episodes")) == 1
    write_artifact(c, "episodes", pd.concat([ep, ep.assign(episode_id=2)]))
    assert len(common.load("episodes")) == 2
    sys.modules.pop("common", None)
    st.cache_data.clear()


def test_reference_prices_match_findings_rupiah_table(monkeypatch, cfg):
    """D-171: harga acuan Rupiah app = tabel batas Rupiah `results/findings.md` (satu sumber); beras +Rp89 pada PT(8) resmi."""
    from kagami.utils.io import exists
    if not exists(cfg, "findings") or not exists(cfg, "profiles"):
        pytest.skip("findings/profiles belum ada")
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    st.cache_data.clear()
    import common
    from kagami.utils.io import read_artifact
    from kagami.viz import plots
    prices = common.reference_prices()
    assert set(prices) == set(cfg.commodities) and prices["beras"] == (16392.0, "kg") and prices["minyak_goreng"][1] == "liter"
    prof = read_artifact(cfg, "profiles")
    r = prof[(prof["level"] == "national") & (prof["unit"].astype(str) == "ALL") & (prof["driver"] == "PT")
             & (prof["commodity"] == "beras") & (prof["horizon"] == 8)].iloc[0]
    assert common.fmt_rp(prices["beras"][0] * plots.scenario_change(r["ci_high"], 5) / 100) == "+Rp89"
    assert common.fmt_rp(-1170.4) == "−Rp1.170" and common.fmt_rp(float("nan")) == "tidak tersedia"
    assert common.names_list(["beras"]) == "beras" and common.names_list(["beras", "gula_pasir", "telur_ayam"]) ==         "beras, gula pasir, dan telur ayam"
    sys.modules.pop("common", None)
    st.cache_data.clear()


def _common(monkeypatch):
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    import common
    return common


def test_plain_text_removes_internal_codes(monkeypatch):
    """D-172: kode keputusan/isu (D-xxx, Uxx, WP-xx) tidak tampil; kalimat & tabel tetap utuh."""
    c = _common(monkeypatch)
    assert c.plain_text("lonjakan (ditandai, tidak dihapus; U17)") == "lonjakan (ditandai, tidak dihapus)"
    assert c.plain_text("total tahunan (USD, D-019) cocok") == "total tahunan (USD) cocok"
    assert c.plain_text("divalidasi (U109).") == "divalidasi."
    assert c.plain_text("praregistrasi (D-139 s.d. D-167). Lalu") == "praregistrasi. Lalu"
    assert c.plain_text("harga dalam-minggu (D-150–D-152), 27") == "harga dalam-minggu, 27"
    assert c.plain_text("00.00 (D-155; FAQ PIHPS: revisi)") == "00.00 (FAQ PIHPS: revisi)"
    assert c.plain_text("real-time, D-162; sebelumnya") == "real-time; sebelumnya"
    tab = "| Pembukaan | Yang dinilai |\n|---|---|\n| D-145 | C1-tuned |\n| D-146 | 3 kelas |"
    assert c.plain_text(tab) == "| Yang dinilai |\n|---|\n| C1-tuned |\n| 3 kelas |"
    assert c.plain_text("tanpa kode M2/M1 1,009 (h 4)") == "tanpa kode M2/M1 1,009 (h 4)"


def test_soften_semicolons_keeps_number_separators(monkeypatch):
    """D-172: titik koma antarklausa → titik (di luar kurung) atau koma (di dalam kurung); titik koma di antara angka
    berdesimal koma, di tabel, dan di kode dibiarkan."""
    c = _common(monkeypatch)
    assert c.soften_semicolons("tidak simetris; batas bawah ada di tabel.") == "tidak simetris. Batas bawah ada di tabel."
    assert c.soften_semicolons("(km tanpa log; km ke Jakarta)") == "(km tanpa log, km ke Jakarta)"
    assert c.soften_semicolons("(DM −1,90; p 0,062)") == "(DM −1,90; p 0,062)"
    assert c.soften_semicolons("| a; b | c |") == "| a; b | c |"
    assert c.soften_semicolons("`x; y` dan nol; q 0,04") == "`x; y` dan nol; q 0,04"


def test_verdicts_and_indonesian_table_format(monkeypatch):
    """D-172: kesimpulan dari rentang 95% & angka tabel berformat Indonesia (bukan 0.01 berdesimal titik)."""
    c = _common(monkeypatch)
    assert c.verdicts([0.1, -0.5, -0.2, float("nan")], [0.3, -0.1, 0.4, 1.0]) == [
        "naik", "turun", "belum terlihat", "rentang tidak tersedia"]
    out = c.fmt_frame(pd.DataFrame({"a": [0.01, -1.67], "p": [0.123, 0.5], "n": [157760, 34], "ok": [True, False],
                                    "s": ["x", "y"]}), digits={"p": 3})
    assert list(out["a"]) == ["0,01", "−1,67"] and list(out["p"]) == ["0,123", "0,500"]
    assert list(out["n"]) == ["157.760", "34"] and list(out["ok"]) == ["ya", "tidak"] and list(out["s"]) == ["x", "y"]


def test_math_text_renders_notation_and_plain_names(monkeypatch):
    """D-173: notasi findings.md → LaTeX inline (dirender KaTeX), nama berkas/kolom → nama pembaca; kode lain tetap."""
    c = _common(monkeypatch)
    assert c.math_text("PT(h) = β_e(h)/γ(h), dengan γ(h)") == r"$PT(h) = \beta_e(h)/\gamma(h)$, dengan $\gamma(h)$"
    assert c.math_text("ω(4) = 0,16 dan ±1,96·SE") == r"$\omega(4)$ = 0,16 dan $\pm 1{,}96 \cdot SE$"
    assert c.math_text("perubahan = exp(PT(8) · ln 1,05) − 1") == r"perubahan = $\exp(PT(8) \cdot \ln 1{,}05) - 1$"
    assert c.math_text("τ² = 0, τ-b −0,045, menarik β ke nol") == r"$\tau^2$ = 0, $\tau_b$ −0,045, menarik $\beta$ ke nol"
    assert c.math_text("`β_e(4)` tetap") == "`β_e(4)` tetap"
    assert c.plain_names("Sumber: `profiles`, `panel_weekly`; `ca53742`") == "Sumber: profil respons, panel harga mingguan; `ca53742`"


def test_app_text_has_no_internal_codes_or_semicolons():
    """D-172: teks yang ditulis di halaman app (literal string di luar docstring/komentar) tanpa kode D-/U-/WP- dan tanpa
    titik koma. Teks dari berkas (findings.md, laporan Tahap 0) dibersihkan saat tampil lewat `common.readable`."""
    import ast
    import re
    code = re.compile(r"\b(?:D-\d{3}[a-z]?|U\d{2,3}|WP-\d{2})\b")
    bad = []
    for path in sorted((APP / "pages").glob("*.py")) + [APP / "Home.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docs = {id(n.body[0].value) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs                     and n.value.strip() != ";":            # pemisah untuk split/replace, bukan teks tampilan
                if code.search(n.value) or "; " in n.value:
                    bad.append(f"{path.name}:{n.lineno}: {n.value[:70]}")
    assert not bad, "\n".join(bad)


def test_every_artifact_in_registry():
    assert {"profiles", "clusters", "assoc"} <= set(ARTIFACTS)
