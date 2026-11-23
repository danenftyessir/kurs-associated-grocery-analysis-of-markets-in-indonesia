"""Setiap fungsi viz menghasilkan figure dari artefak sintetis berkolom sesuai kontrak."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from kagami.viz import plots, style


def test_all_plots_build():
    h = np.arange(13)
    prof = pd.DataFrame({"commodity": "gula_pasir", "level": "national", "unit": "ALL", "driver": "e",
                         "horizon": h, "estimate": h * 0.01, "ci_low": h * 0.01 - 0.02, "ci_high": h * 0.01 + 0.02})
    weeks = pd.date_range("2020-01-06", periods=10, freq="W-MON")
    drv = pd.DataFrame({"week": weeks, "log_e": np.log(15000) + np.arange(10) * 0.001})
    eps = pd.DataFrame({"start_week": [weeks[2]], "end_week": [weeks[5]]})
    panel = pd.DataFrame({"commodity": ["a", "a", "b"], "status": ["observed", "missing", "carry_forward"]})
    co = pd.DataFrame({"province_i": [1, 1, 2, 2], "province_j": [1, 2, 1, 2], "share": [1, .3, .3, 1]})
    pr = pd.DataFrame({"delta": [.1, .2, .1, .2], "k_true": [2, 2, 3, 3], "recovery_rate": [.2, .9, .1, .7]})
    fe = pd.DataFrame({"subset": "all", "model": ["M1", "M2", "M3"], "commodity": "gula_pasir", "horizon": 8,
                       "mae_ratio_vs_m1": [1, .95, 1.02]})
    rob = pd.DataFrame({"check_id": ["a", "b"], "commodity": "x", "horizon": 8, "estimate": [.1, .2],
                        "ci_low": [0, .1], "ci_high": [.2, .3]})
    sel = pd.DataFrame({"k": [1, 2, 3], "silhouette": [np.nan, .17, .18], "placebo_p95": .196,
                        "accepted": [True, False, False]})
    pt = prof.assign(driver="PT")
    figs = [plots.response_curve(prof, "gula_pasir", "national", "ALL", "e"), plots.fx_drivers(drv, eps),
            plots.status_share(panel), plots.coassign_heatmap(co), plots.recovery_curve(pr),
            plots.forecast_ratios(fe), plots.forest(rob, ["check_id", "horizon"], "uji"),
            plots.silhouette_threshold(sel), plots.scenario_paths(pt, [1, 3, 5], 3)]
    assert all(isinstance(f, go.Figure) for f in figs)


def test_curve_without_interval_has_no_band():
    """PT wilayah tanpa interval: tidak ada pita karangan, subjudul menyebut interval tidak tersedia."""
    h = np.arange(13)
    prof = pd.DataFrame({"commodity": "beras", "level": "region", "unit": "Jawa", "driver": "PT", "horizon": h,
                         "estimate": h * 0.01, "ci_low": np.nan, "ci_high": np.nan})
    fig = plots.response_curve(prof, "beras", "region", "Jawa", "PT")
    assert not any(getattr(t, "fill", None) == "tonexty" for t in fig.data)
    assert "Interval tidak tersedia" in fig.layout.title.subtitle.text
    assert not any(getattr(t, "fill", None) == "tonexty" for t in plots.scenario_paths(prof, [1, 3, 5], 3).data)


def test_style_format_and_status():
    assert style.fmt_num(-1234.5, 1) == "−1.234,5"
    assert style.fmt_num(0.0123, 2, sign=True, pct=True) == "+0,01%"
    assert style.fmt_num(float("nan")) == "tidak tersedia"
    assert style.fmt_interval(-0.1, 0.2) == "−0,10 s.d. +0,20"
    assert style.detection_status(-0.1, 0.2) == "tidak terdeteksi"
    assert style.detection_status(0.1, 0.2) == "terdeteksi"
    assert style.detection_status(float("nan"), float("nan")) == "interval tidak tersedia"   # regresi: dulu "terdeteksi"


def test_region_map_offline_and_region_values():
    """Peta tanpa subplot geo (tidak mengunduh topojson CDN, G7 offline); nilai wilayah dipakai provinsinya."""
    sq = lambda x0: [[[[x0, 0], [x0 + 1, 0], [x0 + 1, 1], [x0, 1], [x0, 0]]]]
    geo = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"province_id": i, "province": f"P{i}", "region": r, "lat": .5, "lon": i + .5},
         "geometry": {"type": "MultiPolygon", "coordinates": sq(i)}} for i, r in ((1, "A"), (2, "A"), (3, "B"))]}
    vals = pd.DataFrame({"unit": ["A", "B"], "estimate": [0.2, -0.1], "ci_low": [0.1, -0.3], "ci_high": [0.3, 0.1]})
    fig = plots.region_map(geo, vals, "region", "uji")
    assert not any(t.type in ("choropleth", "scattergeo") for t in fig.data)
    pts = fig.data[-1]
    assert list(np.round(pts.marker.color, 3)) == [0.2, 0.2, -0.1]
    assert pts.customdata[2][5] == "tidak terdeteksi"


def test_reference_geometry_matches_crosswalk(cfg):
    import json
    p = cfg.reference_dir / "indonesia_provinces.geojson"
    g = json.loads(p.read_text(encoding="utf-8"))
    ids = {f["properties"]["province_id"] for f in g["features"]}
    assert ids == set(cfg.regions["province_id"]) and len(ids) == 34
    assert "OpenStreetMap" in g["attribution"]


def test_robustness_and_asymmetry_plots():
    """V18: cek Tier 1/2 komoditas-driver-horizon terpilih (+ komponen dekomposisi untuk e), Tier V dibuang;
    V19: β⁺ & β⁻ per horizon dengan selisih H2 di subjudul."""
    rob = pd.DataFrame({
        "check_id": ["lags_2_4_8", "fx_decomposition_global_dollar_vs_idr_specific", "alternative_variants",
                     "V4_lp_vs_event_study", "lags_2_4_8"],
        "tier": [1, 1, 2, "V", 1], "commodity": "daging_ayam", "horizon": 8,
        "driver": ["e", "e_idr", "e", "e", "w"], "variant": ["L=2", "", "curah", "", "L=2"],
        "estimate": [-1.5, -1.9, -1.2, -1.0, .3], "ci_low": [-2.5, -3.0, -2.0, -2., -.1],
        "ci_high": [-.5, -.8, .1, 0., .7], "baseline_estimate": -1.67, "note": "x"})
    fig = plots.robustness_forest(rob, "daging_ayam", "e", 8)
    labels = [y for t in fig.data for y in t.y if y is not None]
    assert len(labels) == 3 and any("e_idr" in lb for lb in labels) and [t.name for t in fig.data if t.showlegend is not False] == ["Tier 1", "Tier 2"]
    h = np.array([4, 8, 12])
    prof = pd.DataFrame({"commodity": "beras", "level": "national", "unit": "ALL", "horizon": np.tile(h, 2),
                         "driver": np.repeat(["e_pos", "e_neg"], 3), "estimate": [.1, .2, .3, .0, .1, .1],
                         "ci_low": -.2, "ci_high": .5})
    asym = pd.DataFrame({"commodity": "beras", "horizon": h, "estimate": [.1, -.14, .2], "ci_low": [-.3, -.58, -.1],
                         "ci_high": [.4, .47, .5], "confirmatory": [False, True, False]})
    fig = plots.asymmetry_plot(prof, asym, "beras", "Beras")
    assert len(fig.data) == 2 and "uji konfirmatori" in fig.layout.title.subtitle.text
    assert "tidak terdeteksi" in fig.layout.title.subtitle.text
