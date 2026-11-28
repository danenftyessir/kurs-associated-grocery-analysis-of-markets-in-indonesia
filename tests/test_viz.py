"""Setiap fungsi viz menghasilkan figure dari artefak sintetis berkolom sesuai kontrak."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

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
    assert "Rentang 95% tidak tersedia" in fig.layout.title.subtitle.text
    assert not any(getattr(t, "fill", None) == "tonexty" for t in plots.scenario_paths(prof, [1, 3, 5], 3).data)


def test_scenario_change_is_exact_log_transform():
    """D-169: skenario = 100·(exp(PT·ln(1 + x/100)) − 1), rumus tabel batas Rupiah findings; bukan pendekatan linear PT·x."""
    assert plots.scenario_change(1.0, 5) == pytest.approx(5.0)
    assert plots.scenario_change(0.0, 3) == 0.0
    assert plots.scenario_change(0.5, 5) == pytest.approx(100 * (1.05 ** 0.5 - 1))
    assert plots.scenario_change(-4.18, 5) == pytest.approx(-18.44, abs=0.01)      # linear: −20,9
    assert np.isnan(plots.scenario_change(float("nan"), 5))
    arr = plots.scenario_change(pd.Series([-1.0, 0.0, 2.0]), 3)
    assert isinstance(arr, np.ndarray) and np.all(np.diff(arr) > 0)                 # naik monoton dalam PT (x > 0)
    h = np.arange(13)
    pt = pd.DataFrame({"horizon": h, "estimate": h * 0.1, "ci_low": h * 0.1 - 0.5, "ci_high": h * 0.1 + 0.5})
    fig = plots.scenario_paths(pt, [1, 3, 5], 5)
    lines = {t.name: np.asarray(t.y, float) for t in fig.data if (t.name or "").startswith("pelemahan")}
    assert np.allclose(lines["pelemahan 5%"], 100 * (1.05 ** (h * 0.1) - 1))
    band = [np.asarray(t.y, float) for t in fig.data if getattr(t, "fill", None) == "tonexty"]
    assert len(band) == 1 and np.allclose(band[0], 100 * (1.05 ** (h * 0.1 - 0.5) - 1))
    assert "bukan ramalan" in fig.layout.title.subtitle.text.replace("<br>", " ")   # label skenario bersyarat (§18)


def test_scenario_matches_findings_rupiah_table(cfg):
    """App hal. 5 = tabel batas Rupiah `results/findings.md` (PT(8) nasional resmi, rupiah melemah 5%)."""
    from kagami.utils.io import exists, read_artifact
    if not exists(cfg, "profiles"):
        pytest.skip("artefak profiles belum ada")
    prof = read_artifact(cfg, "profiles")
    row = prof[(prof["driver"] == "PT") & (prof["level"] == "national") & (prof["horizon"] == 8)].set_index("commodity")
    want = {"beras": (0.02, -1.04, 0.55), "daging_ayam": (-5.99, -8.31, 0.25), "cabai_rawit": (2.84, -18.44, 16.09)}
    for com, vals in want.items():
        got = [plots.scenario_change(row.loc[com, c], 5) for c in ("estimate", "ci_low", "ci_high")]
        assert got == pytest.approx(list(vals), abs=0.006), com


def test_dm_summary_reports_direction():
    """D-169: p kecil dengan DM negatif = M2 nyata LEBIH BURUK dari M1; app tidak boleh hanya menampilkan p."""
    s = style.dm_summary(-2.7012888, 0.0085354, 0.9957323)              # forecast_eval M2 h = 4
    assert "DM −2,70" in s and "M2 kurang akurat dari M1" in s and "tidak nyata" not in s
    assert "p dua sisi 0,009" in s and "“M2 lebih akurat”: 0,996" in s
    s = style.dm_summary(1.0, 0.1)                                      # p satu sisi diturunkan dari p dua sisi
    assert "M2 lebih akurat dari M1, tetapi tidak nyata" in s and "“M2 lebih akurat”: 0,050" in s
    assert "“M2 lebih akurat”: 0,950" in style.dm_summary(-1.0, 0.1)
    assert "model dengan kurs kurang akurat dari model dasar" in style.dm_summary(-2.7, 0.009, model="model dengan kurs",
                                                                                 ref="model dasar")
    assert style.dm_summary(float("nan"), 0.5) == "uji DM tidak tersedia"


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
    assert len(labels) == 3 and any("komponen khusus rupiah" in lb for lb in labels) and [t.name for t in fig.data if t.showlegend is not False] == ["Tier 1", "Tier 2"]
    assert not any("·" in lb for lb in labels) and not fig.layout.annotations      # D-172: tanpa rantai "·", tanpa anotasi garis
    assert "estimasi utama (−1,67)" in fig.layout.title.subtitle.text.replace("<br>", " ")
    h = np.array([4, 8, 12])
    prof = pd.DataFrame({"commodity": "beras", "level": "national", "unit": "ALL", "horizon": np.tile(h, 2),
                         "driver": np.repeat(["e_pos", "e_neg"], 3), "estimate": [.1, .2, .3, .0, .1, .1],
                         "ci_low": -.2, "ci_high": .5})
    asym = pd.DataFrame({"commodity": "beras", "horizon": h, "estimate": [.1, -.14, .2], "ci_low": [-.3, -.58, -.1],
                         "ci_high": [.4, .47, .5], "confirmatory": [False, True, False]})
    fig = plots.asymmetry_plot(prof, asym, "beras", "Beras")
    assert len(fig.data) == 2 and "uji konfirmatori" in fig.layout.title.subtitle.text
    assert "tidak terdeteksi" in fig.layout.title.subtitle.text


def test_chart_text_wraps_on_phone_and_keeps_desktop_layout():
    """D-172: di ponsel (`style.set_wrap(34, 50)`) judul, subjudul, dan judul sumbu dibungkus dan legenda dikunci di dasar
    wadah; di desktop judul satu baris dan legenda di bawah plot seperti sebelumnya. Grafik pipeline: angka jumlah
    artefak tidak jatuh di kolom simpul (dulu menimpa label "Task 1")."""
    title = "Respons 8 minggu terhadap kurs rupiah, semua komoditas (nasional)"
    sub = "Titik penuh: rentang 95% tidak memuat nol. Titik kosong: memuat nol. Asosiasi historis, bukan sebab-akibat."
    fig = go.Figure(go.Scatter(x=[1, 2], y=[1, 2], name="pelemahan 1%"))
    desk = style.finish(go.Figure(fig), title, sub, x="% per 1% pelemahan rupiah")
    assert "<br>" not in desk.layout.title.text and desk.layout.legend.y == -0.22
    tok = style.WRAP.set((34, 50))
    try:
        ph = style.finish(go.Figure(fig), title, sub, x="% per 1% pelemahan rupiah")
    finally:
        style.WRAP.reset(tok)
    assert all(len(r) <= 34 for r in ph.layout.title.text.split("<br>")) and ph.layout.title.text.count("<br>") >= 1
    assert all(len(r) <= 50 for r in ph.layout.title.subtitle.text.split("<br>"))
    assert "<br>" in ph.layout.xaxis.title.text and ph.layout.legend.yref == "container"
    assert ph.layout.margin.t > desk.layout.margin.t and ph.layout.margin.b > desk.layout.margin.b
    assert style.wrap_lines("satu dua tiga", 8) == ["satu dua", "tiga"]
    # D-176: grafik kolom sempit (beranda) memecah judul desktop dengan "\n" → dua baris + ruang atas; tanpa "\n" tetap
    two = style.finish(go.Figure(fig), "Perubahan harga 8 minggu\nsetelah rupiah melemah 5%", sub)
    assert two.layout.title.text == "Perubahan harga 8 minggu<br>setelah rupiah melemah 5%"
    assert two.layout.margin.t == desk.layout.margin.t + 24
    edges = pd.DataFrame({"producer": ["stage0", "stage0", "stage0", "task1"], "consumer": ["task1", "task3", "task2", "task2"],
                          "artifact": ["a", "b", "c", "d"], "required": True})
    g = plots.pipeline_graph(edges, {})
    node_x = {round(v, 6) for t in g.data if t.mode == "markers+text" for v in t.x}
    assert not any(round(a.x, 6) in node_x for a in g.layout.annotations)


def test_timeline_episode_fan_and_province_charts():
    """D-175: lini masa kurs (episode berlabel bulan, sorotan), kipas episode (pita data acak + satu garis per episode, sorotan
    digambar paling atas), kipas semua komoditas (5 kolom desktop, 2 kolom ponsel), tren harga provinsi vs median, kelengkapan
    data berlabel pembaca."""
    weeks = pd.date_range("2018-01-01", periods=60, freq="W-MON")
    drv = pd.DataFrame({"week": weeks, "log_e": np.log(14000 + np.arange(60))})
    eps = pd.DataFrame({"episode_id": [1, 2], "start_week": [weeks[5], weeks[30]], "end_week": [weeks[8], weeks[32]],
                        "cum_dlog_e": [0.04, 0.18]})
    fig = plots.fx_drivers(drv, eps, start="2018-02-01", highlight=2)
    assert len(fig.layout.shapes) == 2 and fig.layout.shapes[1].fillcolor != fig.layout.shapes[0].fillcolor
    assert pd.Timestamp(fig.data[0].x[0]) >= pd.Timestamp("2018-02-01") and fig.data[1].customdata[1][0] == "Jul 2018"
    ev = pd.DataFrame([{"episode_id": e, "level": "national", "unit": "ALL", "commodity": c, "horizon": h,
                        "dlog_price": 0.002 * h * e, "placebo_lo": -0.01, "placebo_hi": 0.01, "placebo_p": 0.4}
                       for c in ("beras", "gula_pasir", "telur_ayam") for e in (1, 2) for h in range(13)])
    fan = plots.episode_fan(ev, "beras", eps, name="Beras", highlight=1)
    lines = [t for t in fan.data if t.mode == "lines" and t.x is not None and t.x[0] is not None and t.fill != "toself"]
    assert fan.data[0].fill == "toself" and len(lines) == 2 and lines[-1].name == "Feb 2018" and lines[-1].line.width == 3
    grid = plots.episode_fan_grid(ev, {"beras": "Beras"})
    assert [a.text for a in grid.layout.annotations][:1] == ["Beras"] and grid.layout.xaxis3 is not None
    tok = style.WRAP.set((34, 50))
    try:
        assert plots.episode_fan_grid(ev).layout.xaxis3.domain[0] < 0.5          # ponsel: 2 kolom, panel ke-3 di kiri
    finally:
        style.WRAP.reset(tok)
    pan = pd.DataFrame([{"week": w, "province_id": p, "commodity": "beras", "price": 10000 + p * 100 + i,
                         "status": "observed"} for p in (1, 2, 3) for i, w in enumerate(weeks)])
    tr = plots.price_trend(pan, 2, "beras", eps, name="Beras", where="Riau")
    assert [t.name for t in tr.data] == ["Median 34 provinsi", "Riau"] and tr.data[0].y[0] == 10200
    sh = plots.status_share(pan.assign(status=["observed", "carry_forward"] * 90), {"beras": "Beras"})
    assert {t.name for t in sh.data} == {"teramati", "rangkaian harga identik"} and list(sh.data[0].y) == ["Beras"]
    assert style.month_year("2020-03-02") == "Mar 2020" and style.month_year(None) == "tidak tersedia"


def _hexes(cfg) -> pd.DataFrame:
    return pd.read_csv(cfg.reference_dir / "province_hex.csv")


def test_hex_layout_covers_crosswalk(cfg):
    """D-178: tata letak heksagon = 34 provinsi crosswalk, kode ISO & singkatan unik, tanpa dua provinsi di petak yang
    sama, barat → timur (Aceh paling kiri, Papua paling kanan)."""
    h = _hexes(cfg)
    assert sorted(h["province_id"]) == sorted(cfg.regions["province_id"]) and h["code"].is_unique and h["label"].is_unique
    assert not h.duplicated(["col", "row"]).any() and h["label"].str.len().max() <= 7
    x = h["col"] + 0.5 * (h["row"] % 2)
    assert x[h["province_id"] == 1].iloc[0] == x.min() and x[h["province_id"] == 33].iloc[0] == x.max()


def test_hex_tile_map_colors_labels_and_callouts(cfg):
    """D-178: satu heksagon per provinsi (shape), skala warna `zmin`..`zmax`, `muted` = semua abu-abu tanpa skala warna,
    `flags` bergaris tebal, singkatan provinsi di desktop dan kode di ponsel, nama pulau & label langsung hanya di desktop."""
    h = _hexes(cfg)
    regions = dict(zip(cfg.regions["province_id"], cfg.regions["region"]))
    v = pd.DataFrame({"province_id": h["province_id"], "value": np.linspace(10_000, 50_000, len(h))})
    v["hover"] = [f"prov {p}" for p in v["province_id"]]
    fig = plots.hex_tile_map(v, h, "judul", "sub", zmin=10_000, zmax=50_000, scale=style.SEQUENTIAL, legend="Rp",
                             flags={5}, regions=regions, callouts=[(33, "Papua Rp50.000"), (1, "Aceh Rp10.000")])
    assert len(fig.layout.shapes) == 34 and len({s.fillcolor for s in fig.layout.shapes}) > 10
    assert sum(s.line.width > 2 for s in fig.layout.shapes) == 1 and fig.layout.yaxis.scaleanchor == "x"
    bar = [t for t in fig.data if getattr(t.marker, "showscale", False)]
    assert bar and bar[0].marker.colorbar.orientation == "h" and bar[0].marker.cmin == 10_000
    assert list(fig.data[0].text)[:2] == ["Aceh", "Sumut"] and list(fig.data[0].hovertext)[:1] == ["prov 1"]
    notes = [a.text for a in fig.layout.annotations]
    assert {"Sumatra", "Papua", "Jawa"} <= set(notes) and "Papua Rp50.000" in notes and "Aceh Rp10.000" in notes
    arrows = [a for a in fig.layout.annotations if a.showarrow]
    occupied = {(round(x, 2), round(y, 2)) for x, y in zip(fig.data[0].x, fig.data[0].y)}
    assert all((round(a.ax, 2), round(a.ay, 2)) not in occupied for a in arrows)      # label di petak kosong
    muted = plots.hex_tile_map(v.assign(value=0.1), h, "judul", "sub", zmax=1.0, legend="x", muted=True)
    assert {s.fillcolor for s in muted.layout.shapes} == {plots.HEX_MUTED}
    assert not any(getattr(t.marker, "showscale", False) for t in muted.data)
    tok = style.WRAP.set((34, 50))
    try:
        phone = plots.hex_tile_map(v, h, "judul", "sub", zmin=10_000, zmax=50_000, legend="Rp", regions=regions,
                                   callouts=[(33, "Papua")])
        assert list(phone.data[0].text)[:1] == ["AC"] and not phone.layout.annotations
    finally:
        style.WRAP.reset(tok)
    narrow = plots.hex_tile_map(v, h, "judul", "sub", zmin=10_000, zmax=50_000, legend="Rp", text="code")
    assert list(narrow.data[0].text)[:1] == ["AC"]


def test_hex_tile_grid_detected_first_and_muted(cfg):
    """D-178: komoditas terdeteksi di panel pertama dan berwarna, sisanya abu-abu; desktop 5 kolom; grid dibangun cepat
    (shape sekaligus)."""
    import time
    h = _hexes(cfg)
    rows = [{"commodity": c, "province_id": p, "value": (i - 17) / 17}
            for c in ("beras", "telur_ayam", "gula_pasir") for i, p in enumerate(h["province_id"])]
    vals = pd.DataFrame(rows)
    t0 = time.perf_counter()
    fig = plots.hex_tile_grid(vals, h, {"beras": "Beras", "telur_ayam": "Telur", "gula_pasir": "Gula"}, {"telur_ayam"},
                              1.0, "x", pd.DataFrame({"commodity": ["telur_ayam"], "province_id": [3]}))
    assert time.perf_counter() - t0 < 5
    assert fig.layout.annotations[0].text.startswith("Telur") and len(fig.layout.shapes) == 3 * 34
    assert fig.layout.xaxis3.domain[0] > 0.3                                            # satu baris, 5 kolom
    first = [s for s in fig.layout.shapes if s.xref == "x"]
    rest = [s for s in fig.layout.shapes if s.xref == "x2"]
    assert len({s.fillcolor for s in first}) > 5 and {s.fillcolor for s in rest} == {plots.HEX_MUTED}
    assert sum(s.line.width > 2 for s in first) == 1


def test_episode_matrix_states_and_pending():
    """D-178: satu titik per komoditas × episode; merah = naik melewati rentang plasebo, biru = turun, abu-abu = di dalam,
    lingkaran kosong = belum teramati (bukan "di dalam"); episode berjarak sama, kolom kanan = jumlah di luar rentang."""
    eps = pd.DataFrame({"episode_id": [1, 2, 3], "start_week": pd.to_datetime(["2018-03-12", "2020-03-02", "2026-11-02"]),
                        "end_week": pd.to_datetime(["2018-03-19", "2020-04-27", "2026-11-09"]),
                        "cum_dlog_e": [0.03, 0.18, 0.04]})
    ev = pd.DataFrame({"episode_id": [1, 1, 2, 2], "level": "national", "unit": "ALL", "horizon": 8,
                       "commodity": ["beras", "gula_pasir"] * 2, "dlog_price": [0.05, 0.0, -0.05, 0.0],
                       "placebo_lo": -0.02, "placebo_hi": 0.02})
    fig = plots.episode_matrix(eps, ev, {"beras": "Beras", "gula_pasir": "Gula Pasir"})
    by = {t.name: t for t in fig.data if t.name}
    assert list(by["harga naik di luar rentang normal"].x) == [1] and list(by["harga turun di luar rentang normal"].x) == [2]
    assert len(by["di dalam rentang normal"].x) == 2 and list(by["belum teramati"].x) == [3, 3]
    assert list(fig.data[0].x) == [1, 2, 3] and fig.data[0].type == "bar"
    assert "2 dari 2" in [a.text for a in fig.layout.annotations]                          # beras: naik + turun
    assert "+5,1" not in by["harga naik di luar rentang normal"].hovertemplate                         # angka lewat customdata
    tok = style.WRAP.set((34, 50))
    try:
        ph = plots.episode_matrix(eps, ev)
        assert list(ph.layout.xaxis2.ticktext) == ["2018", "2020", "2026"] and ph.layout.xaxis2.tickangle == -90
    finally:
        style.WRAP.reset(tok)
