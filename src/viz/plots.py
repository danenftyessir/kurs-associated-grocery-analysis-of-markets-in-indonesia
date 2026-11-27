"""Grafik bersama (plotly) untuk notebook dan app Streamlit. Input = artefak dari utils/artifacts.py.

Aturan tampilan (proposal §7.1, PLAN.md §18): setiap grafik menampilkan interval bila ada (pita/whisker tipis, tidak
mengalahkan estimasi), satuan di sumbu, judul berbahasa pengguna, dan catatan "asosiasi, bukan kausalitas" sebagai
subjudul grafik respons. Warna & label dari `viz.style` (palet tervalidasi; warna mengikuti entitas).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from kagami.viz import style as S

CAUSAL_NOTE = S.CAUSAL_NOTE
STATUS_ORDER = ["observed", "carry_forward", "short", "missing"]


def response_curve(profiles: pd.DataFrame, commodity: str, level: str, unit: str, driver: str,
                   name: str | None = None, unit_name: str | None = None) -> go.Figure:
    """Kurva respons kumulatif h = 0..12 dengan pita interval 95% resmi (artefak `profiles`). Tanpa interval
    (mis. PT wilayah) → garis saja + keterangan 'interval tidak tersedia', tidak ada pita karangan."""
    d = profiles[(profiles["commodity"] == commodity) & (profiles["level"] == level)
                 & (profiles["unit"].astype(str) == str(unit)) & (profiles["driver"] == driver)].sort_values("horizon")
    has_ci = d[["ci_low", "ci_high"]].notna().all(axis=1).any()
    traces = []
    if has_ci:
        traces += [go.Scatter(x=d["horizon"], y=d["ci_high"], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"),
                   go.Scatter(x=d["horizon"], y=d["ci_low"], fill="tonexty", fillcolor=S.rgba(S.BLUE, 0.18),
                              mode="lines", line=dict(width=0), name="interval 95%", hoverinfo="skip")]
    traces.append(go.Scatter(
        x=d["horizon"], y=d["estimate"], mode="lines+markers", name="respons kumulatif",
        line=dict(color=S.BLUE, width=2), marker=dict(size=7, color=S.BLUE),
        customdata=np.c_[d["ci_low"], d["ci_high"]],
        hovertemplate="h = %{x} minggu<br><b>%{y:.3f}</b><br>interval %{customdata[0]:.3f} s.d. %{customdata[1]:.3f}"
                      "<extra></extra>"))
    fig = go.Figure(traces)
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    where = S.LEVEL_LABELS.get(level, level) + ("" if level == "national" else f" · {unit_name or unit}")
    dev = level == "province"                       # baris provinsi `profiles` = deviasi δ dari rerata (Σ_r δ = 0)
    sub = (f"{where} · {'deviasi dari rerata lintas provinsi' if dev else 'Δ log harga per 1 log penggerak'} · "
           f"{CAUSAL_NOTE}")
    if not has_ci:
        sub += " Interval tidak tersedia untuk pilihan ini."
    what = "Deviasi respons" if dev else "Respons harga"
    return S.finish(fig, f"{what} {name or commodity} terhadap {S.DRIVER_LABELS.get(driver, driver)}", sub,
                    x="minggu setelah perubahan penggerak", y="deviasi kumulatif" if dev else "respons kumulatif")


def sensitivity_heatmap(features: pd.DataFrame, level: str, metric: str = "R8",
                        labels: dict | None = None, unit_names: dict | None = None) -> go.Figure:
    """Peta kepekaan: respons kumulatif `metric` (R4/R8/R12/W8/PT8) per komoditas x unit pada satu level
    (artefak `response_features`; provinsi/wilayah). Diverging dengan nol netral; sel kosong = tidak tersedia."""
    m = features[features["level"] == level].pivot(index="commodity", columns="unit", values=metric)
    if labels:
        m.index = [labels.get(c, c) for c in m.index]
    if unit_names:
        m.columns = [unit_names.get(str(u), u) for u in m.columns]
    lim = float(np.nanmax(np.abs(m.to_numpy()))) if m.size and np.isfinite(m.to_numpy()).any() else 1.0
    fig = px.imshow(m, color_continuous_scale=S.DIVERGING, zmin=-lim, zmax=lim, aspect="auto",
                    labels=dict(color=metric, x="", y=""))
    fig.update_traces(hovertemplate="%{y} · %{x}<br><b>%{z:.3f}</b><extra></extra>")
    return S.finish(fig, f"{metric} per komoditas dan {S.LEVEL_LABELS.get(level, level).lower()}",
                    f"Merah = harga naik bersama depresiasi, biru = turun, abu-abu = sekitar nol · {CAUSAL_NOTE}")


def region_map(geo: dict, values: pd.DataFrame, level: str, title: str, subtitle: str = "") -> go.Figure:
    """Peta kepekaan Indonesia (geometri `data/reference/indonesia_provinces.geojson`, 34 provinsi). `values`: kolom
    unit (nama wilayah atau province_id), estimate, ci_low, ci_high. level='region' → setiap provinsi diwarnai nilai
    wilayahnya (7 wilayah, tanpa dissolve geometri); level='province' → nilai per provinsi. Diverging, nol netral.

    Digambar di sumbu kartesius (poligon `fill="toself"` + titik ibu kota sebagai target hover/klik & skala warna),
    BUKAN subplot `geo`: subplot geo Plotly selalu mengunduh topojson dari cdn.plot.ly (gagal offline, G7)."""
    from plotly.colors import sample_colorscale

    props = pd.DataFrame([f["properties"] for f in geo["features"]])
    v = values.assign(unit=values["unit"].astype(str))
    key = "region" if level == "region" else "province_id"
    d = props.assign(unit=props[key].astype(str)).merge(v[["unit", "estimate", "ci_low", "ci_high"]], on="unit",
                                                        how="left").set_index("province_id")
    lim = float(np.nanmax(np.abs(d["estimate"]))) if d["estimate"].notna().any() else 1.0
    lim = lim or 1.0
    fig = go.Figure()
    for f in geo["features"]:
        pid = f["properties"]["province_id"]
        val = d.at[pid, "estimate"]
        color = (sample_colorscale(S.DIVERGING, [(val + lim) / (2 * lim)])[0] if np.isfinite(val)
                 else S.rgba(S.NEUTRAL, 0.25))
        xs, ys = [], []
        for poly in f["geometry"]["coordinates"]:
            for ring in poly[:1]:                       # cincin luar; lubang diabaikan (skala nasional)
                xs += [p[0] for p in ring] + [None]
                ys += [p[1] for p in ring] + [None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor=color,
                                 line=dict(color="rgba(255,255,255,0.55)", width=0.6), hoverinfo="skip",
                                 showlegend=False))
    d = d.reset_index()
    status = [S.detection_status(a, b) for a, b in zip(d["ci_low"], d["ci_high"])]
    fig.add_trace(go.Scatter(
        x=d["lon"], y=d["lat"], mode="markers", showlegend=False, name="provinsi",
        marker=dict(size=11, color=d["estimate"], colorscale=S.DIVERGING, cmin=-lim, cmax=lim,
                    line=dict(color="rgba(255,255,255,0.9)", width=1.2),
                    colorbar=dict(title="respons", thickness=12, len=0.7)),
        customdata=np.c_[d["province_id"], d["province"], d["region"], d["ci_low"], d["ci_high"], status],
        hovertemplate=("%{customdata[1]} (%{customdata[2]})<br><b>%{marker.color:.3f}</b><br>interval "
                       "%{customdata[3]:.3f} s.d. %{customdata[4]:.3f}<br>%{customdata[5]}<extra></extra>")))
    fig = S.finish(fig, title, f"{subtitle} · {CAUSAL_NOTE}" if subtitle else CAUSAL_NOTE, height=430)
    fig.update_xaxes(visible=False, fixedrange=True, showgrid=False)
    fig.update_yaxes(visible=False, fixedrange=True, showgrid=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(margin={"t": 80, "l": 0, "r": 0, "b": 0}, plot_bgcolor="rgba(0,0,0,0)",
                      clickmode="event+select")         # klik titik = seleksi (dipakai st.plotly_chart on_select)
    return fig


def cluster_sizes(clusters: pd.DataFrame, method: str = "ward") -> go.Figure:
    """Jumlah provinsi per klaster dengan stabilitas Jaccard (artefak `clusters`); klaster lemah ditandai."""
    d = clusters[clusters["method"] == method].groupby("cluster").agg(
        provinsi=("province_id", "size"), jaccard=("jaccard", "mean"), lemah=("weak", "max")).reset_index()
    d["stabilitas"] = np.where(d["lemah"], "lemah (Jaccard < ambang)", "stabil")
    fig = px.bar(d, x="cluster", y="provinsi", color="stabilitas", hover_data=["jaccard"],
                 color_discrete_map={"stabil": S.BLUE, "lemah (Jaccard < ambang)": S.NEUTRAL})
    return S.finish(fig, f"Ukuran & stabilitas klaster ({method})", x="klaster", y="jumlah provinsi")


def fx_drivers(drivers: pd.DataFrame, episodes: pd.DataFrame | None = None) -> go.Figure:
    """Kurs JISDOR mingguan (Rp/USD) dengan arsiran episode depresiasi (artefak `drivers_weekly`, `episodes`)."""
    fig = go.Figure(go.Scatter(x=drivers["week"], y=np.exp(drivers["log_e"]), name="JISDOR (rerata mingguan)",
                               line=dict(color=S.BLUE, width=2)))
    if episodes is not None:
        for r in episodes.itertuples():
            fig.add_vrect(x0=r.start_week, x1=r.end_week, fillcolor=S.rgba(S.ORANGE, 0.18), line_width=0)
    return S.finish(fig, "IDR/USD dan episode depresiasi ≥ 3%", "Arsiran = episode (Σ Δlog kurs 8 minggu ≥ 0,03)",
                    x="minggu", y="Rp per USD")


def status_share(panel_weekly: pd.DataFrame) -> go.Figure:
    """Porsi status sel mingguan per komoditas (artefak `panel_weekly`). carry_forward = rangkaian harga teramati identik
    (kekakuan harga atau harga hari sebelumnya dari sumber; tidak dapat dibedakan, U22), bukan peringatan → biru muda."""
    share = (panel_weekly.groupby("commodity")["status"].value_counts(normalize=True)
             .rename("share").reset_index())
    fig = px.bar(share, x="commodity", y="share", color="status", category_orders={"status": STATUS_ORDER},
                 color_discrete_map=S.STATUS_COLORS)
    return S.finish(fig, "Status sel mingguan per komoditas",
                    "carry_forward = rangkaian harga identik ≥ 5 hari teramati (penanda, bukan filter)",
                    x="", y="porsi sel")


def coassign_heatmap(coassign: pd.DataFrame) -> go.Figure:
    """Matriks ko-asignasi bootstrap (artefak `coassign`)."""
    m = coassign.pivot(index="province_i", columns="province_j", values="share")
    fig = px.imshow(m, color_continuous_scale=S.SEQUENTIAL, zmin=0, zmax=1, labels=dict(color="porsi"))
    return S.finish(fig, "Ko-asignasi bootstrap", "Porsi replikasi dua provinsi berada di klaster yang sama")


def recovery_curve(planted: pd.DataFrame, threshold: float = 0.8) -> go.Figure:
    """Kurva pemulihan struktur tertanam = batas deteksi (artefak `planted_recovery`); garis ambang = `threshold`
    (pemanggil meneruskan `evaluation.planted.DETECTION_RATE`)."""
    fig = go.Figure()
    for color, (k, d) in zip(S.SERIES, planted.sort_values("delta").groupby("k_true")):
        fig.add_trace(go.Scatter(x=d["delta"], y=d["recovery_rate"], mode="lines+markers", name=f"{k} kelompok tertanam",
                                 line=dict(color=color, width=2), marker=dict(size=8, color=color),
                                 hovertemplate="δ = %{x:.1f}<br><b>%{y:.0%}</b> terdeteksi<extra></extra>"))
    fig.add_hline(y=threshold, line_dash="dash", line_color=S.NEUTRAL, line_width=1,
                  annotation_text=f"ambang deteksi {threshold:.0%}", annotation_position="bottom right")
    fig.update_yaxes(range=[0, 1.05], tickformat=".0%")
    return S.finish(fig, "Seberapa besar struktur regional yang akan terdeteksi?",
                    "Struktur dengan selisih respons ≥ δ ditanam pada derau plasebo, lalu diproses seperti data asli",
                    x="selisih respons tertanam δ (RMS per fitur)", y="porsi struktur terdeteksi")


def silhouette_threshold(selection: pd.DataFrame) -> go.Figure:
    """Silhouette maksimum Ward per k vs ambang p95 plasebo (artefak `cluster_selection`); k diterima hanya bila
    melewati ambang, selain itu k = 1."""
    d = selection[selection["k"] >= 2].dropna(subset=["silhouette"])
    thr = float(selection["placebo_p95"].dropna().iloc[0]) if selection["placebo_p95"].notna().any() else np.nan
    above = d["silhouette"] > thr
    fig = go.Figure(go.Scatter(
        x=d["k"], y=d["silhouette"], mode="markers+text", text=[S.fmt_num(v, 3) for v in d["silhouette"]],
        textposition="top center", name="data asli",
        marker=dict(size=12, color=np.where(above, S.ORANGE, S.BLUE)),
        hovertemplate="k = %{x}<br>silhouette <b>%{y:.3f}</b><extra></extra>"))
    if np.isfinite(thr):
        fig.add_hline(y=thr, line_dash="dash", line_color=S.NEUTRAL, line_width=1,
                      annotation_text=f"p95 plasebo {S.fmt_num(thr, 3)}", annotation_position="top left")
    title = ("Tidak ada k yang melewati ambang plasebo → k = 1" if not above.any()
             else "Struktur regional melewati ambang plasebo")
    fig.update_xaxes(dtick=1)
    return S.finish(fig, title, "Silhouette maksimum Ward per k vs persentil 95 silhouette maksimum pada data plasebo",
                    x="jumlah klaster k", y="silhouette")


def forecast_ratios(forecast_eval: pd.DataFrame, subset: str = "all", labels: dict | None = None) -> go.Figure:
    """Rasio MAE vs M1 per komoditas & model (artefak `forecast_eval`); < 1 = lebih akurat dari M1. Dot plot,
    satu panel per horizon; warna & simbol mengikuti model."""
    d = forecast_eval[(forecast_eval["subset"] == subset) & forecast_eval["model"].isin(["M0", "M2", "M3"])].copy()
    if "level" in d and (d["level"] == "commodity").any():
        d = d[d["level"] == "commodity"]
    d["komoditas"] = d["commodity"].map(lambda c: (labels or {}).get(c, c))
    d["model_label"] = d["model"].map(S.MODEL_LABELS)
    fig = px.scatter(d, x="mae_ratio_vs_m1", y="komoditas", color="model_label", symbol="model_label",
                     facet_col="horizon", hover_data=[c for c in ("n_origins", "dm_stat", "dm_p") if c in d],
                     color_discrete_map={S.MODEL_LABELS[m]: S.MODEL_COLORS[m] for m in ("M0", "M2", "M3")})
    fig.update_traces(marker=dict(size=10))
    fig.add_vline(x=1, line_color=S.NEUTRAL, line_width=1)
    fig.for_each_annotation(lambda a: a.update(text=a.text.replace("horizon=", "h = ") + " minggu"))
    n = d["n_origins"].dropna() if "n_origins" in d else pd.Series(dtype=float)
    n_txt = (f"{int(n.min())}" if n.min() == n.max() else f"{int(n.min())}–{int(n.max())}") if len(n) else "?"
    return S.finish(fig, f"Rasio MAE terhadap M1 · {S.SUBSET_LABELS.get(subset, subset)}",
                    f"Kiri dari 1 = lebih akurat dari M1 · {n_txt} origin · evaluasi bersyarat, pseudo-real-time",
                    x="rasio MAE vs M1", y="", height=max(320, 34 * d["komoditas"].nunique() + 140))


def forest(df: pd.DataFrame, label_cols: list[str], title: str, x_title: str | None = None,
           subtitle: str | None = None) -> go.Figure:
    """Forest plot estimasi + interval (artefak `assoc`, `robustness`, `profiles`, `regime_profiles`). Titik penuh =
    interval tidak memuat nol, titik kosong = memuat nol (pengkodean kedua selain posisi)."""
    d = df.assign(label=df[label_cols].astype(str).agg(" · ".join, axis=1))
    excl = (d["ci_low"] > 0) | (d["ci_high"] < 0)
    fig = go.Figure(go.Scatter(
        x=d["estimate"], y=d["label"], mode="markers", showlegend=False,
        marker=dict(size=10, color=np.where(excl, S.BLUE, "rgba(0,0,0,0)"), line=dict(color=S.BLUE, width=2),
                    symbol="circle"),
        error_x=dict(type="data", symmetric=False, array=d["ci_high"] - d["estimate"],
                     arrayminus=d["estimate"] - d["ci_low"], color=S.BLUE, thickness=1.5, width=0),
        customdata=np.c_[d["ci_low"], d["ci_high"]],
        hovertemplate="%{y}<br><b>%{x:.3f}</b><br>interval %{customdata[0]:.3f} s.d. %{customdata[1]:.3f}<extra></extra>"))
    fig.add_vline(x=0, line_color=S.NEUTRAL, line_width=1)
    sub = subtitle or "Titik penuh = interval 95% tidak memuat nol; titik kosong = memuat nol"
    return S.finish(fig, title, f"{sub} · {CAUSAL_NOTE}", x=x_title, height=max(300, 30 * len(d) + 120))


def robustness_forest(robustness: pd.DataFrame, commodity: str, driver: str, horizon: int,
                      name: str | None = None) -> go.Figure:
    """V18: estimasi setiap cek robustness (Tier 1 & 2, artefak `robustness`) vs estimasi utama untuk satu komoditas,
    penggerak, dan horizon. Driver e juga memuat komponen dekomposisi kurs (e_global, e_idr). Warna = tier; titik kosong =
    interval memuat nol; garis putus = estimasi utama."""
    drivers = [driver] + (["e_global", "e_idr"] if driver == "e" else [])
    d = robustness[(robustness["commodity"] == commodity) & (robustness["horizon"] == horizon)
                   & robustness["driver"].isin(drivers) & robustness["tier"].astype(str).isin(["1", "2"])
                   & robustness["estimate"].notna()].copy()
    d["cek"] = d["check_id"].map(lambda c: S.CHECK_LABELS.get(c, c))
    var = d["variant"].fillna("").astype(str) if "variant" in d else ""
    comp = np.where(d["driver"] != driver, " · " + d["driver"].astype(str), "")
    d["label"] = d["cek"] + np.where(var != "", " · " + var, "") + comp
    d = d.sort_values(["tier", "cek", "label"], ascending=[False, True, True])
    fig = go.Figure()
    for tier, color in (("1", S.BLUE), ("2", S.ORANGE)):
        g = d[d["tier"].astype(str) == tier]
        if g.empty:
            continue
        has = g[["ci_low", "ci_high"]].notna().all(axis=1)
        excl = has & ((g["ci_low"] > 0) | (g["ci_high"] < 0))
        sym = "circle" if tier == "1" else "square"
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=f"Tier {tier}",   # entri legenda (selalu penuh)
                                 marker=dict(size=10, color=color, symbol=sym)))
        fig.add_trace(go.Scatter(
            x=g["estimate"], y=g["label"], mode="markers", name=f"Tier {tier}", showlegend=False,
            marker=dict(size=10, color=np.where(excl, color, "rgba(0,0,0,0)"), line=dict(color=color, width=2),
                        symbol=sym),
            error_x=dict(type="data", symmetric=False, array=(g["ci_high"] - g["estimate"]).fillna(0),
                         arrayminus=(g["estimate"] - g["ci_low"]).fillna(0), color=color, thickness=1.5, width=0),
            customdata=np.c_[g["ci_low"], g["ci_high"], g["note"].fillna("")],
            hovertemplate="%{y}<br><b>%{x:.3f}</b><br>interval %{customdata[0]:.3f} s.d. %{customdata[1]:.3f}"
                          "<br>%{customdata[2]}<extra></extra>"))
    base = d.loc[d["driver"] == driver, "baseline_estimate"].dropna()
    if len(base):
        fig.add_vline(x=float(base.iloc[0]), line_dash="dash", line_color=S.NEUTRAL, line_width=1,
                      annotation_text=f"estimasi utama {S.fmt_num(float(base.iloc[0]), 3)}",
                      annotation_position="top")
    fig.add_vline(x=0, line_color=S.NEUTRAL, line_width=1)
    return S.finish(fig, f"Apakah respons {name or commodity} bertahan di setiap cek? ({S.DRIVER_LABELS.get(driver, driver)}, "
                         f"h = {horizon})",
                    f"Titik kosong = interval memuat nol · garis putus = estimasi utama · {CAUSAL_NOTE}",
                    x="respons kumulatif", height=max(320, 26 * len(d) + 160))


def asymmetry_plot(profiles: pd.DataFrame, asymmetry: pd.DataFrame, commodity: str,
                   name: str | None = None) -> go.Figure:
    """V19: respons nasional terhadap depresiasi (β⁺, `e_pos`) vs apresiasi (β⁻, `e_neg`) per horizon kunci dengan interval
    masing-masing (artefak `profiles`); hasil uji selisih β⁺ − β⁻ (artefak `asymmetry`) di subjudul."""
    hs = sorted(asymmetry.loc[asymmetry["commodity"] == commodity, "horizon"].unique()) or [4, 8, 12]
    d = profiles[(profiles["commodity"] == commodity) & (profiles["level"] == "national")
                 & profiles["driver"].isin(["e_pos", "e_neg"]) & profiles["horizon"].isin(hs)]
    fig = go.Figure()
    for drv, color, shift, sym in (("e_pos", S.ORANGE, -0.12, "circle"), ("e_neg", S.BLUE, 0.12, "diamond")):
        g = d[d["driver"] == drv].sort_values("horizon")
        xs = [hs.index(h) + shift for h in g["horizon"]]
        fig.add_trace(go.Scatter(
            x=xs, y=g["estimate"], mode="markers", name=S.DRIVER_LABELS[drv],
            marker=dict(size=11, color=color, symbol=sym),
            error_y=dict(type="data", symmetric=False, array=g["ci_high"] - g["estimate"],
                         arrayminus=g["estimate"] - g["ci_low"], color=color, thickness=1.5, width=0),
            customdata=np.c_[g["horizon"], g["ci_low"], g["ci_high"]],
            hovertemplate="h = %{customdata[0]}<br><b>%{y:.3f}</b><br>interval %{customdata[1]:.3f} s.d. "
                          "%{customdata[2]:.3f}<extra></extra>"))
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    fig.update_xaxes(tickvals=list(range(len(hs))), ticktext=[f"h = {h}" for h in hs], range=[-0.6, len(hs) - 0.4])
    a = asymmetry[(asymmetry["commodity"] == commodity) & (asymmetry["horizon"] == 8)]
    sub = CAUSAL_NOTE
    if len(a):
        r = a.iloc[0]
        kind = "uji konfirmatori" if bool(r.get("confirmatory", False)) else "deskriptif"
        sub = (f"h = 8: β⁺ − β⁻ = {S.fmt_num(r['estimate'], 2)} (interval {S.fmt_interval(r['ci_low'], r['ci_high'])}), "
               f"{S.detection_status(r['ci_low'], r['ci_high'])} · {kind} · {CAUSAL_NOTE}")
    return S.finish(fig, f"Apakah {name or commodity} bereaksi berbeda saat rupiah melemah vs menguat?", sub,
                    x="minggu setelah perubahan kurs", y="respons kumulatif")


def scenario_change(pt, shock_pct: float):
    """Perubahan harga (%) yang konsisten dengan PT(h) untuk pelemahan rupiah x% (D-169): 100·(exp(PT·ln(1 + x/100)) − 1).
    PT = Δlog harga per 1 Δlog kurs, jadi pelemahan x% = Δlog kurs ln(1 + x/100), lalu hasilnya dikembalikan ke persen. Rumus
    yang sama dipakai tabel batas Rupiah di `results/findings.md` (`docs/audit/20261127_redflag_juri/`). Pendekatan linear PT·x
    (app sebelum D-169) menyimpang di ekor, mis. PT −4,18 dan x = 5: −20,9% vs −18,4%. Skalar → float; array/Series → ndarray;
    NaN tetap NaN. Untuk x > 0 fungsi ini naik monoton dalam PT, jadi batas interval PT dipetakan langsung."""
    c = np.log1p(shock_pct / 100.0)
    if np.ndim(pt) == 0:
        return float(100.0 * np.expm1(float(pt) * c))
    return 100.0 * np.expm1(np.asarray(pt, dtype=float) * c)


def scenario_paths(pt: pd.DataFrame, shocks: list[float], selected: float) -> go.Figure:
    """Skenario bersyarat untuk setiap pelemahan x (%): perubahan harga = `scenario_change` (exp(PT(h)·ln(1 + x/100)) − 1;
    baris `profiles` driver PT satu komoditas & unit). Pita hanya untuk x terpilih dan hanya bila interval PT ada; bukan ramalan."""
    d = pt.sort_values("horizon")
    fig = go.Figure()
    if d[["ci_low", "ci_high"]].notna().all(axis=1).any():
        lo, hi = scenario_change(d["ci_low"], selected), scenario_change(d["ci_high"], selected)
        fig.add_trace(go.Scatter(x=d["horizon"], y=np.maximum(lo, hi), mode="lines", line=dict(width=0), showlegend=False,
                                 hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=d["horizon"], y=np.minimum(lo, hi), fill="tonexty",
                                 fillcolor=S.rgba(S.BLUE, 0.15), mode="lines", line=dict(width=0), name=f"interval ({selected}%)",
                                 hoverinfo="skip"))
    ramp = S.BLUE_RAMP[-len(shocks):] if len(shocks) <= len(S.BLUE_RAMP) else S.BLUE_RAMP
    for color, x in zip(ramp, sorted(shocks)):
        fig.add_trace(go.Scatter(x=d["horizon"], y=scenario_change(d["estimate"], x), mode="lines", name=f"pelemahan {x}%",
                                 line=dict(color=color, width=3 if x == selected else 1.5),
                                 hovertemplate=f"x = {x}%<br>h = %{{x}}<br><b>%{{y:.2f}}%</b><extra></extra>"))
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    return S.finish(fig, "Perubahan harga yang konsisten dengan pola historis",
                    # tanpa " · " di dalam rumus: S.finish memecah subjudul pada pemisah itu
                    "SKENARIO BERSYARAT, BUKAN RAMALAN · perubahan = exp(PT(h)×ln(1 + x/100)) − 1",
                    x="minggu setelah pelemahan", y="perubahan harga (%)")


# --------------------------------------------------------------------------- log eksekusi & evaluasi (WP-36, app hal. 7)
RUN_STATUS_COLORS = {"success": S.BLUE, "failed": S.ORANGE, "belum ada run": S.NEUTRAL,
                     # status tahap (D-140: eksekusi dipisah dari evaluasi-saja; output tidak sinkron ditandai)
                     "dieksekusi": S.BLUE, "sebagian dieksekusi": "#5f97dc", "dieksekusi · output tidak sinkron": "#b58b00", "hanya dievaluasi": "#9cc3f0",
                     "eksekusi gagal": S.ORANGE, "evaluasi gagal": S.ORANGE}
RUN_STATUS_LABELS = {"success": "berhasil", "failed": "gagal", "belum ada run": "belum ada run"}


def run_durations(runs: pd.DataFrame, labels: dict[str, str] | None = None) -> go.Figure:
    """Waktu eksekusi per run eksekusi (tabel `tracking.store.runs_table`) sebagai batang horizontal berlabel tahap +
    waktu mulai, warna = status (D-140: bukan rerata lintas tahap). Run evaluasi-saja tidak punya waktu eksekusi
    teramati → tidak digambar; tahap yang belum pernah dieksekusi disebut di subjudul."""
    d = runs[runs["duration_s"].notna()].copy()
    # format="ISO8601": log lama tanpa mikrodetik bercampur log baru dengan mikrodetik (D-138)
    d["t"] = pd.to_datetime(d["started_at"], format="ISO8601", utc=True)
    d = d.sort_values("t")
    d["label"] = [f"{(labels or {}).get(t, t)} · {x:%d %b %H:%M}" for t, x in zip(d["task_id"], d["t"])]
    never = [(labels or {}).get(t, t) for t in dict.fromkeys(runs["task_id"]) if t not in set(d["task_id"])]
    fig = go.Figure()
    for status, g in d.groupby("status"):
        fig.add_trace(go.Bar(
            x=g["duration_s"], y=g["label"], orientation="h", name=RUN_STATUS_LABELS.get(status, status),
            marker_color=RUN_STATUS_COLORS.get(status, S.NEUTRAL), customdata=g["run_id"],
            text=[S.fmt_num(v, 1) + " dtk" for v in g["duration_s"]], textposition="outside",
            hovertemplate="%{y}<br>%{customdata}<br><b>%{x:.1f} dtk</b><extra></extra>"))
    fig.update_yaxes(categoryorder="array", categoryarray=list(d["label"]))
    sub = f"{len(d)} run eksekusi"
    if never:
        sub += " · belum ada waktu eksekusi tercatat: " + ", ".join(never)
    return S.finish(fig, "Waktu eksekusi per run", sub, x="detik", height=max(260, 40 * len(d) + 140))


def metric_trend(metrics: pd.DataFrame, runs: pd.DataFrame, task_id: str, name: str) -> go.Figure:
    """Nilai satu metrik numerik di setiap run sebuah tahap (urut waktu mulai); run dengan status metrik ≠ ok
    digambar sebagai penanda abu-abu di sumbu bawah agar ketiadaan nilai tetap terlihat."""
    m = metrics[(metrics["task_id"] == task_id) & (metrics["name"] == name)].merge(
        runs[["run_id", "started_at", "run_type"]], on="run_id", how="left").sort_values("started_at")
    m["x"] = pd.to_datetime(m["started_at"], format="ISO8601", utc=True)
    m["v"] = pd.to_numeric(m["value"], errors="coerce")
    good = m[(m["status"] == "ok") & m["v"].notna()]
    bad = m[~m.index.isin(good.index)]
    fig = go.Figure(go.Scatter(x=good["x"], y=good["v"], mode="lines+markers", name="nilai",
                               line=dict(color=S.BLUE, width=2), marker=dict(size=9), customdata=good["run_id"],
                               hovertemplate="%{customdata}<br><b>%{y:.4g}</b><extra></extra>"))
    if len(bad):
        fig.add_trace(go.Scatter(x=bad["x"], y=[good["v"].min() if len(good) else 0] * len(bad), mode="markers",
                                 name="tidak berlaku / gagal", marker=dict(symbol="x", size=9, color=S.NEUTRAL),
                                 customdata=bad["reason"], hovertemplate="%{customdata}<extra></extra>"))
    return S.finish(fig, f"{name} antar run · {task_id}", f"{len(good)} nilai dari {len(m)} run",
                    x="waktu mulai run (UTC)", y=name)


def confusion_matrix(cm: list[list[int]], labels: list[str], title: str, subtitle: str = "") -> go.Figure:
    """Confusion matrix (baris = aktual, kolom = ramalan) dari metrik `dir_confusion` log evaluasi Task 4 (D-139).
    Warna = porsi baris (recall per kelas aktual), teks = jumlah + porsi baris."""
    m = np.asarray(cm, float)
    rows = m.sum(axis=1, keepdims=True)
    frac = np.divide(m, rows, out=np.zeros_like(m), where=rows > 0)
    text = [[f"{int(m[i, j]):,}".replace(",", ".") + f"<br>{frac[i, j] * 100:.1f}%".replace(".", ",")
             for j in range(m.shape[1])] for i in range(m.shape[0])]
    xs, ys = [f"ramalan {lab}" for lab in labels], [f"aktual {lab}" for lab in labels]
    fig = go.Figure(go.Heatmap(z=frac, x=xs, y=ys, text=text, colorscale=S.SEQUENTIAL, zmin=0, zmax=1,
                               colorbar=dict(title="porsi baris", tickformat=".0%"),
                               hovertemplate="%{y} → %{x}<br>%{text}<extra></extra>"))
    for i in range(m.shape[0]):          # teks per sel: putih di sel gelap, gelap di sel terang (kontras)
        for j in range(m.shape[1]):
            fig.add_annotation(x=xs[j], y=ys[i], text=text[i][j], showarrow=False,
                               font=dict(size=14, color="#ffffff" if frac[i, j] >= 0.5 else "#0d366b"))
    fig.update_yaxes(autorange="reversed")
    return S.finish(fig, title, subtitle)


def pipeline_graph(edges: pd.DataFrame, status: dict[str, str], stale: set[str] | None = None,
                   labels: dict[str, str] | None = None) -> go.Figure:
    """Graf dependensi antar-tahap dari REQUIRES/OPTIONAL (`tracking.registry.dependency_edges`). Lapisan = jalur
    terpanjang dari sumber; garis penuh = input wajib, putus-putus = opsional; warna simpul = status tahap
    (`tracking.store.stage_states`: dieksekusi / output tidak sinkron / hanya dievaluasi / gagal; status run lama
    success/failed tetap diterima); tahap yang inputnya berubah setelah run terakhir diberi tanda "basi"."""
    stale = stale or set()
    nodes = list(dict.fromkeys([*edges["producer"], *edges["consumer"]]))
    pairs = edges.groupby(["producer", "consumer"], as_index=False).agg(required=("required", "any"),
                                                                        n=("artifact", "size"),
                                                                        artifacts=("artifact", lambda s: ", ".join(s)))
    layer = {n: 0 for n in nodes}
    for _ in nodes:                                  # relaksasi jalur terpanjang (graf kecil, tanpa siklus)
        for r in pairs.itertuples():
            if r.producer != r.consumer:
                layer[r.consumer] = max(layer[r.consumer], layer[r.producer] + 1)
    pos = {}
    for lv in sorted(set(layer.values())):
        members = [n for n in nodes if layer[n] == lv]
        for i, n in enumerate(members):
            pos[n] = (lv, (len(members) - 1) / 2 - i)
    fig = go.Figure()
    for r in pairs.itertuples():
        if r.producer == r.consumer:
            continue
        (x0, y0), (x1, y1) = pos[r.producer], pos[r.consumer]
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", showlegend=False, hoverinfo="skip",
                                 line=dict(color=S.NEUTRAL, width=1 + min(r.n, 6) / 2,
                                           dash="solid" if r.required else "dot")))
        fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=str(r.n), showarrow=False,   # kontras (D-140)
                           font=dict(size=12, color="#1a1a1a"), bgcolor="#ffffff", bordercolor=S.NEUTRAL,
                           borderpad=2, hovertext=r.artifacts)
    for st_name in dict.fromkeys(status.get(n, "belum ada run") for n in nodes):
        members = [n for n in nodes if status.get(n, "belum ada run") == st_name]
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in members], y=[pos[n][1] for n in members], mode="markers+text",
            name=RUN_STATUS_LABELS.get(st_name, st_name),
            text=[(labels or {}).get(n, n) + (" · basi" if n in stale else "") for n in members],
            textposition="bottom center", marker=dict(size=26, color=RUN_STATUS_COLORS.get(st_name, S.NEUTRAL),
                                                   line=dict(width=2, color="white")),
            hovertemplate="%{text}<extra></extra>"))
    x_max = max(p[0] for p in pos.values())
    y_abs = max([abs(p[1]) for p in pos.values()] + [0.5])
    fig.update_xaxes(visible=False, range=[-0.7, x_max + 0.7])           # ruang untuk label simpul di tepi
    fig.update_yaxes(visible=False, range=[-y_abs - 0.6, y_abs + 0.4])
    fig = S.finish(fig, "Alur data antar-tahap", "garis penuh = input wajib · titik-titik = input opsional · angka = "
                   "jumlah artefak · warna = status tahap (eksekusi dipisah dari evaluasi-saja)", height=380)
    fig.update_xaxes(showgrid=False)
    return fig
