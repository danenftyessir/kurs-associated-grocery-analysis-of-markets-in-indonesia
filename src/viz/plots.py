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
from plotly.subplots import make_subplots

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
                              mode="lines", line=dict(width=0), name="rentang 95%", hoverinfo="skip")]
    traces.append(go.Scatter(
        x=d["horizon"], y=d["estimate"], mode="lines+markers", name="respons",
        line=dict(color=S.BLUE, width=2), marker=dict(size=7, color=S.BLUE),
        customdata=np.c_[d["ci_low"], d["ci_high"]],
        hovertemplate="minggu ke-%{x}<br><b>%{y:.2f}</b><br>rentang 95%: %{customdata[0]:.2f} s.d. %{customdata[1]:.2f}"
                      "<extra></extra>"))
    fig = go.Figure(traces)
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    where = "nasional" if level == "national" else (unit_name or str(unit))
    dev = level == "province"                       # baris provinsi `profiles` = deviasi δ dari rerata (Σ_r δ = 0)
    drv = S.DRIVER_LABELS.get(driver, driver).lower()
    unit_txt = "Selisih dari rata-rata semua provinsi" if dev else S.UNIT_LABELS.get(driver, "respons kumulatif")
    sub = f"{unit_txt}. " + ("Pita biru: rentang 95%. " if has_ci else "Rentang 95% tidak tersedia untuk pilihan ini. ")
    sub += CAUSAL_NOTE
    title = (f"{unit_name or unit}: selisih respons harga {name or commodity} terhadap {drv}" if dev else
             f"{name or commodity}: respons harga {where} terhadap {drv}")
    return S.finish(fig, title, sub, x="minggu setelah perubahan",
                    y="selisih dari rata-rata" if dev else S.AXIS_LABELS.get(driver, "respons kumulatif"))


def sensitivity_heatmap(features: pd.DataFrame, level: str, metric: str = "R8",
                        labels: dict | None = None, unit_names: dict | None = None,
                        metric_label: str | None = None) -> go.Figure:
    """Peta kepekaan: respons kumulatif `metric` (R4/R8/R12/W8/PT8) per komoditas x unit pada satu level
    (artefak `response_features`; provinsi/wilayah). Diverging dengan nol netral; sel kosong = tidak tersedia."""
    m = features[features["level"] == level].pivot(index="commodity", columns="unit", values=metric)
    if labels:
        m.index = [labels.get(c, c) for c in m.index]
    if unit_names:
        m.columns = [unit_names.get(str(u), u) for u in m.columns]
    lim = float(np.nanmax(np.abs(m.to_numpy()))) if m.size and np.isfinite(m.to_numpy()).any() else 1.0
    fig = px.imshow(m, color_continuous_scale=S.DIVERGING, zmin=-lim, zmax=lim, aspect="auto",
                    labels=dict(color="respons", x="", y=""))
    fig.update_traces(hovertemplate="%{y}, %{x}<br><b>%{z:.2f}</b><extra></extra>")
    return S.finish(fig, f"{metric_label or metric} per komoditas dan {S.LEVEL_LABELS.get(level, level).lower()}",
                    "Merah: harga naik saat rupiah melemah. Biru: harga turun. Abu-abu: sekitar nol. Estimasi titik "
                    f"tanpa rentang. {CAUSAL_NOTE}")


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
        hovertemplate=("%{customdata[1]} (%{customdata[2]})<br><b>%{marker.color:.2f}</b><br>rentang 95%: "
                       "%{customdata[3]:.2f} s.d. %{customdata[4]:.2f}<br>%{customdata[5]}<extra></extra>")))
    fig = S.finish(fig, title, f"{subtitle} {CAUSAL_NOTE}" if subtitle else CAUSAL_NOTE, height=430)
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


def fx_drivers(drivers: pd.DataFrame, episodes: pd.DataFrame | None = None, start=None,
               highlight: int | None = None) -> go.Figure:
    """Kurs JISDOR mingguan (Rp per dolar AS) dengan arsiran episode pelemahan (artefak `drivers_weekly`, `episodes`).
    `start` memotong awal seri (mis. awal periode analisis), `highlight` = episode_id yang arsirannya ditebalkan. Penanda
    segitiga di atas tiap episode membawa keterangan saat kursor diarahkan; nilai terakhir diberi label."""
    d = drivers.dropna(subset=["log_e"]).copy()
    d["week"] = pd.to_datetime(d["week"])
    if start is not None:
        d = d[d["week"] >= pd.Timestamp(start)]
    rate = np.exp(d["log_e"])
    fig = go.Figure(go.Scatter(x=d["week"], y=rate, name="Kurs JISDOR (rerata mingguan)", line=dict(color=S.BLUE, width=2),
                               hovertemplate="%{x|%d-%m-%Y}<br>Rp%{y:,.0f} per dolar AS<extra></extra>"))
    n = 0
    if episodes is not None and len(episodes):
        ep = episodes.copy()
        ep["start_week"], ep["end_week"] = pd.to_datetime(ep["start_week"]), pd.to_datetime(ep["end_week"])
        n = len(ep)
        for r in ep.itertuples():
            strong = highlight is not None and r.episode_id == highlight
            fig.add_vrect(x0=r.start_week, x1=r.end_week + pd.Timedelta(days=6), line_width=0,
                          fillcolor=S.rgba(S.ORANGE, 0.5 if strong else 0.2))
        top = float(rate.max()) * 1.015 if len(rate) else 0.0
        fig.add_trace(go.Scatter(
            x=ep["start_week"], y=[top] * n, mode="markers", showlegend=False,
            marker=dict(symbol="triangle-down", size=9, color=S.ORANGE),
            customdata=np.c_[[S.month_year(t) for t in ep["start_week"]],
                             100 * np.expm1(ep["cum_dlog_e"]) if "cum_dlog_e" in ep else np.full(n, np.nan)],
            hovertemplate="Episode %{customdata[0]}<br>rupiah melemah %{customdata[1]:.1f}% dalam 8 minggu<extra></extra>"))
    if len(rate):
        fig.add_trace(go.Scatter(x=[d["week"].iloc[-1]], y=[rate.iloc[-1]], mode="markers", showlegend=False,
                                 marker=dict(size=9, color=S.BLUE, line=dict(color="white", width=2)), hoverinfo="skip"))
    fig.update_yaxes(tickformat=",.0f")
    return S.finish(fig, "Kurs rupiah per dolar AS",
                    f"Arsiran oranye: {n} episode pelemahan, saat rupiah melemah minimal 3% dalam 8 minggu. Arahkan kursor ke "
                    "segitiga untuk melihat besarnya.", x="", y="Rupiah per dolar AS", height=420)


def status_share(panel_weekly: pd.DataFrame, labels: dict | None = None, title: str | None = None) -> go.Figure:
    """Porsi status sel mingguan per komoditas (artefak `panel_weekly`), batang horizontal bertumpuk berlabel pembaca.
    Rangkaian harga identik (carry_forward) bisa berarti harga kaku atau harga hari sebelumnya dari sumber; keduanya tidak
    dapat dibedakan (U22), jadi diwarnai biru muda sebagai penanda, bukan peringatan."""
    share = (panel_weekly.groupby("commodity")["status"].value_counts(normalize=True).rename("share").reset_index())
    share["komoditas"] = share["commodity"].map(lambda c: (labels or {}).get(c, c))
    share["status_label"] = share["status"].map(lambda s: S.STATUS_LABELS.get(s, s))
    order = [S.STATUS_LABELS[s] for s in STATUS_ORDER]
    fig = px.bar(share, y="komoditas", x="share", color="status_label", orientation="h",
                 category_orders={"status_label": order},
                 color_discrete_map={S.STATUS_LABELS[s]: c for s, c in S.STATUS_COLORS.items()},
                 custom_data=["status_label"])
    fig.update_traces(hovertemplate="%{y}: %{customdata[0]} %{x:.0%}<extra></extra>")
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    return S.finish(fig, title or "Kelengkapan data mingguan per komoditas",
                    "Rangkaian harga identik: harga yang sama minimal 5 hari teramati. Penyebabnya tidak bisa dibedakan, "
                    "jadi kami menandainya tanpa membuangnya.", x="porsi minggu", y="",
                    height=max(320, 30 * share["komoditas"].nunique() + 170))


def episode_fan(events: pd.DataFrame, commodity: str, episodes: pd.DataFrame | None = None, name: str | None = None,
                highlight: int | None = None) -> go.Figure:
    """Kipas episode (artefak `events`, tingkat nasional): perubahan harga 0–12 minggu sesudah awal setiap episode pelemahan
    rupiah, satu garis per episode, di atas pita 95% perubahan harga pada 499 jendela waktu tanpa episode. `highlight` =
    episode_id yang ditebalkan biru (digambar paling atas); episode lain abu-abu."""
    d = events[(events["commodity"] == commodity) & (events["level"] == "national")].copy()
    d["pct"] = 100 * np.expm1(d["dlog_price"])
    names = ({} if episodes is None else {r.episode_id: S.month_year(r.start_week) for r in episodes.itertuples()})
    fig = go.Figure()
    if len(d):        # pita = rerata placebo_lo/hi antar-episode per horizon, dalam persen
        b = d.groupby("horizon")[["placebo_lo", "placebo_hi"]].mean().sort_index()
        h, lo, hi = b.index.to_numpy(), 100 * np.expm1(b["placebo_lo"]).to_numpy(), 100 * np.expm1(b["placebo_hi"]).to_numpy()
        fig.add_trace(go.Scatter(x=np.r_[h, h[::-1]], y=np.r_[hi, lo[::-1]], fill="toself", mode="lines",
                                 fillcolor=S.rgba(S.BLUE, 0.16), line=dict(width=0), hoverinfo="skip",
                                 name="Rentang 95% jendela tanpa episode"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=S.NEUTRAL, width=1.5), name="Satu episode"))
    ids = sorted(d["episode_id"].unique(), key=lambda e: e == highlight)
    for eid in ids:
        g = d[d["episode_id"] == eid].sort_values("horizon")
        strong = bool(eid == highlight)
        lab = names.get(eid, f"Episode {eid}")
        fig.add_trace(go.Scatter(
            x=g["horizon"], y=g["pct"], mode="lines", showlegend=strong, name=lab,
            line=dict(color=S.BLUE if strong else S.NEUTRAL, width=3 if strong else 1.3),
            opacity=1.0 if strong or highlight is None else 0.45,
            hovertemplate=f"{lab}<br>minggu ke-%{{x}}: %{{y:+.2f}}%<extra></extra>"))
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    fig.update_xaxes(dtick=2, range=[-0.3, 12.3])
    return S.finish(fig, f"{name or commodity}: harga setelah episode pelemahan rupiah",
                    "Setiap garis adalah satu episode. Pita biru: rentang 95% perubahan harga pada 499 jendela waktu tanpa "
                    f"episode. {CAUSAL_NOTE}", x="minggu sejak awal episode", y="% perubahan harga nasional", height=440)


def episode_fan_grid(events: pd.DataFrame, labels: dict | None = None) -> go.Figure:
    """Kipas episode untuk semua komoditas sekaligus (artefak `events`, nasional): satu panel per komoditas dengan skala
    sendiri. Desktop 5 kolom, ponsel 2 kolom (`style.WRAP`)."""
    d = events[events["level"] == "national"].copy()
    d["pct"] = 100 * np.expm1(d["dlog_price"])
    coms = list(dict.fromkeys(d["commodity"]))
    cols = 2 if S.WRAP.get()[0] else 5
    rows = max(1, -(-len(coms) // cols))
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[(labels or {}).get(c, c) for c in coms],
                        horizontal_spacing=0.05 if cols == 5 else 0.1, vertical_spacing=min(0.2, 0.32 / rows))
    for i, c in enumerate(coms):
        r, k = divmod(i, cols)
        g = d[d["commodity"] == c]
        b = g.groupby("horizon")[["placebo_lo", "placebo_hi"]].mean().sort_index()
        h, lo, hi = b.index.to_numpy(), 100 * np.expm1(b["placebo_lo"]).to_numpy(), 100 * np.expm1(b["placebo_hi"]).to_numpy()
        fig.add_trace(go.Scatter(x=np.r_[h, h[::-1]], y=np.r_[hi, lo[::-1]], fill="toself", mode="lines",
                                 fillcolor=S.rgba(S.BLUE, 0.16), line=dict(width=0), hoverinfo="skip", showlegend=False),
                      row=r + 1, col=k + 1)
        for eid, e in g.groupby("episode_id"):
            e = e.sort_values("horizon")
            fig.add_trace(go.Scatter(x=e["horizon"], y=e["pct"], mode="lines", showlegend=False,
                                     line=dict(color=S.NEUTRAL, width=1), opacity=0.7,
                                     hovertemplate=f"{(labels or {}).get(c, c)}<br>minggu ke-%{{x}}: %{{y:+.1f}}%"
                                                   "<extra></extra>"), row=r + 1, col=k + 1)
    fig.update_xaxes(dtick=4, range=[-0.3, 12.3])
    fig.update_annotations(font_size=12)
    fig = S.finish(fig, "Semua komoditas: harga setelah episode pelemahan",
                   "Setiap panel memakai skala sendiri. Sumbu tegak: % perubahan harga nasional. Sumbu datar: minggu sejak "
                   f"awal episode. Pita biru: rentang 95% jendela tanpa episode. {CAUSAL_NOTE}",
                   height=(230 if cols == 5 else 210) * rows + 150)
    return fig.update_layout(margin_t=fig.layout.margin.t + 30)   # ruang judul panel di bawah subjudul


def price_trend(panel: pd.DataFrame, province_id: int, commodity: str, episodes: pd.DataFrame | None = None,
                name: str | None = None, where: str | None = None, unit: str = "kg") -> go.Figure:
    """Harga eceran mingguan (Rp) sebuah komoditas di satu provinsi dibanding median 34 provinsi (artefak `panel_weekly`),
    dengan arsiran episode pelemahan rupiah. Minggu kosong tidak diisi (garis terputus)."""
    d = panel[panel["commodity"] == commodity].copy()
    d["week"] = pd.to_datetime(d["week"])
    nat = d.groupby("week")["price"].median()
    p = d[d["province_id"] == province_id].set_index("week")["price"].sort_index()
    where = where or str(province_id)
    fig = go.Figure()
    if episodes is not None and len(episodes):
        for r in episodes.itertuples():
            fig.add_vrect(x0=pd.Timestamp(r.start_week), x1=pd.Timestamp(r.end_week) + pd.Timedelta(days=6), line_width=0,
                          fillcolor=S.rgba(S.ORANGE, 0.14))
    fig.add_trace(go.Scatter(x=nat.index, y=nat, mode="lines", name="Median 34 provinsi",
                             line=dict(color=S.NEUTRAL, width=1.5),
                             hovertemplate="%{x|%d-%m-%Y}<br>median Rp%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=p.index, y=p, mode="lines", name=where, line=dict(color=S.BLUE, width=2),
                             hovertemplate="%{x|%d-%m-%Y}<br>" + where + " Rp%{y:,.0f}<extra></extra>"))
    fig.update_yaxes(tickformat=",.0f")
    return S.finish(fig, f"{name or commodity}: harga eceran di {where}",
                    "Arsiran oranye: episode pelemahan rupiah. Harga mingguan dari PIHPS, minggu kosong tidak diisi.",
                    x="", y=f"Rupiah per {unit}", height=400)


HEX_R = 1 / np.sqrt(3)            # heksagon runcing-atas selebar 1 satuan: jarak kolom 1, jarak baris 1,5·R
HEX_MUTED = "#dcdad3"             # komoditas tanpa perbedaan antarprovinsi yang terdeteksi: semua heksagon sama
INK, INK_MUTED = "#1f2328", "#6b6a64"
UP, DOWN = "#a32a2b", "#104281"   # kutub palet divergen: naik / turun
# Label pulau di peta heksagon: wilayah crosswalk → (nama, posisi). Atas untuk pulau di baris utara, bawah untuk Jawa & Nusa Tenggara.
ISLANDS = {"Sumatra": ("Sumatra", "top"), "Kalimantan": ("Kalimantan", "top"), "Sulawesi": ("Sulawesi", "top"),
           "Maluku": ("Maluku", "top"), "Papua": ("Papua", "top"), "Jawa": ("Jawa", "bottom"),
           "Bali-Nusa Tenggara": ("Bali & Nusa Tenggara", "bottom")}


def _hex_centers(hexes: pd.DataFrame) -> pd.DataFrame:
    """Pusat heksagon dari (col, row) offset baris ganjil: x = col + 0,5·(row ganjil), y = −1,5·R·row."""
    h = hexes.copy()
    h["x"] = h["col"] + 0.5 * (h["row"] % 2)
    h["y"] = -1.5 * HEX_R * h["row"]
    return h


def _hex_path(x: float, y: float, shrink: float = 0.94) -> str:
    a = np.deg2rad(np.arange(6) * 60 + 30)
    r = HEX_R * shrink
    return "M " + " L ".join(f"{x + r * np.cos(t):.4f},{y + r * np.sin(t):.4f}" for t in a) + " Z"


def _ink(rgb: str) -> str:
    """Warna teks yang terbaca di atas isian heksagon (rgb(...) atau #hex)."""
    if rgb.startswith("#"):
        v = [int(rgb[i:i + 2], 16) for i in (1, 3, 5)]
    else:
        v = [float(t) for t in rgb[rgb.index("(") + 1:rgb.index(")")].split(",")[:3]]
    return INK if 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2] > 140 else "#ffffff"


def _hex_layer(fig: go.Figure, values: pd.DataFrame, hexes: pd.DataFrame, zmin: float, zmax: float, scale,
               muted: bool, flags: set, ax: str, text: str | None, colorbar: dict | None) -> pd.DataFrame:
    """Gambar 34 heksagon (shape path, dipasang sekaligus) + satu trace teks/penanda untuk keterangan kursor di sumbu `ax`
    ("" = sumbu 1). `text` = kolom tata letak yang ditulis di heksagon (label/code) atau None."""
    from plotly.colors import sample_colorscale

    h = _hex_centers(hexes).merge(values, on="province_id", how="left")
    z = h["value"].to_numpy(dtype=float)
    frac = np.clip((z - zmin) / ((zmax - zmin) or 1.0), 0, 1)
    fills = [HEX_MUTED if muted or np.isnan(v) else sample_colorscale(scale, [f])[0] for v, f in zip(z, frac)]
    shapes = [dict(type="path", path=_hex_path(r.x, r.y), xref=f"x{ax}", yref=f"y{ax}", fillcolor=fill, layer="below",
                   line=dict(color=INK if int(r.province_id) in flags else "#ffffff",
                             width=2.6 if int(r.province_id) in flags else 1))
              for r, fill in zip(h.itertuples(), fills)]
    fig.layout.shapes = tuple(fig.layout.shapes) + tuple(shapes)     # sekaligus: add_shape per heksagon ± 19 dtk di grid
    hover = h["hover"] if "hover" in h else h["code"]
    fig.add_trace(go.Scatter(
        x=h["x"], y=h["y"], mode="text" if text else "markers", text=h[text] if text else None, hovertext=hover,
        textfont=dict(size=10 if text == "label" else 9, color=[_ink(f) for f in fills]),
        marker=dict(size=18, opacity=0), hovertemplate="%{hovertext}<extra></extra>", showlegend=False,
        xaxis=f"x{ax}", yaxis=f"y{ax}"))
    if colorbar is not None:         # skala warna lewat trace kosong (shape tidak punya colorbar)
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=[zmin, zmax], colorscale=scale, cmin=zmin, cmax=zmax, showscale=True,
                                             colorbar=colorbar), xaxis=f"x{ax}", yaxis=f"y{ax}"))
    return h


def _hex_axes(fig: go.Figure, hexes: pd.DataFrame, ax: str = "", islands: bool = False) -> None:
    h = _hex_centers(hexes)
    top, bottom = (0.95, 0.95) if islands else (0.0, 0.0)
    fig.update_layout({f"xaxis{ax}": dict(visible=False, range=[h["x"].min() - 0.65, h["x"].max() + 0.65],
                                          constrain="domain", fixedrange=True),
                       f"yaxis{ax}": dict(visible=False, range=[h["y"].min() - 0.62 - bottom, h["y"].max() + 0.62 + top],
                                          scaleanchor=f"x{ax}", scaleratio=1, constrain="domain", fixedrange=True)})


def _island_labels(fig: go.Figure, h: pd.DataFrame, regions: dict) -> None:
    """Nama pulau di atas (pulau utara) atau di bawah (Jawa, Nusa Tenggara) kelompok heksagonnya, abu-abu kecil."""
    h = h.assign(region=h["province_id"].map(regions))
    y_top, y_bottom = h["y"].max() + 0.85, h["y"].min() - 0.85
    for reg, (name, where) in ISLANDS.items():
        g = h[h["region"] == reg]
        if g.empty:
            continue
        y = y_top if where == "top" else (g["y"].min() - 0.85)
        fig.add_annotation(x=float(g["x"].mean()), y=y if where == "top" else max(y, y_bottom), text=name,
                           showarrow=False, font=dict(size=11, color=INK_MUTED), xanchor="center")


def _callouts(fig: go.Figure, h: pd.DataFrame, items: list[tuple[int, str]]) -> None:
    """Label langsung untuk beberapa provinsi: teks diletakkan di petak kosong terdekat yang cukup lebar, dengan garis
    penunjuk ke heksagonnya (koordinat data, jadi tidak bergeser saat lebar layar berubah)."""
    xs = np.arange(-0.5, h["x"].max() + 1.0, 0.5)
    rows = np.arange(-1, h["row"].max() + 2)
    cand = [(x, -1.5 * HEX_R * r) for r in rows for x in xs]
    occupied = h[["x", "y"]].to_numpy()
    used: list[tuple[float, float]] = []
    for pid, text in items:
        t = h[h["province_id"] == pid]
        if t.empty:
            continue
        tx, ty = float(t["x"].iloc[0]), float(t["y"].iloc[0])
        free = [(x, y) for x, y in cand
                if not ((np.abs(occupied[:, 0] - x) < 1.6) & (np.abs(occupied[:, 1] - y) < 0.6)).any()
                and all(abs(x - ux) > 2.2 or abs(y - uy) > 0.6 for ux, uy in used)
                and h["x"].min() + 1.2 <= x <= h["x"].max() - 1.2 and h["y"].min() - 0.1 <= y <= h["y"].max() + 0.1]
        if not free:
            continue
        x, y = min(free, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)
        used.append((x, y))
        fig.add_annotation(x=tx, y=ty, ax=x, ay=y, axref="x", ayref="y", text=text, showarrow=True, arrowhead=0,
                           arrowwidth=1, arrowcolor=INK_MUTED, standoff=7, font=dict(size=11, color=INK),
                           bgcolor="rgba(255,255,255,0.85)", borderpad=2)


def hex_tile_map(values: pd.DataFrame, hexes: pd.DataFrame, title: str, subtitle: str, zmax: float,
                 legend: str, muted: bool = False, flags: set | None = None, scale=None, zmin: float | None = None,
                 height: int | None = None, regions: dict | None = None, callouts: list | None = None,
                 tickformat: str | None = None, text: str | None = "auto") -> go.Figure:
    """Peta petak heksagon 34 provinsi (tabel referensi `province_hex.csv`): setiap provinsi satu heksagon berukuran sama,
    jadi DKI Jakarta sama terlihatnya dengan Papua. `values` = province_id, value (+ hover). Skala `scale` dari `zmin`
    (default −`zmax`, divergen simetris) ke `zmax`; nilai di luar dipotong ke ujung. `muted` = semua heksagon abu-abu
    (perbedaan tidak terdeteksi, nilai tetap di keterangan kursor); `flags` = provinsi bergaris tebal (lolos uji);
    `regions` (province_id → wilayah crosswalk) menambah nama pulau; `callouts` = [(province_id, teks)] label langsung.
    `text` = "label" (singkatan, butuh lebar penuh), "code" (dua huruf, untuk kolom sempit), None, atau "auto" (label di
    desktop, kode di ponsel). Ponsel tanpa label langsung. Skala warna mendatar di bawah."""
    fig = go.Figure()
    scale = scale or S.DIVERGING
    zmin = -zmax if zmin is None else zmin
    mobile = S.WRAP.get()[0] is not None
    bar = None if muted else dict(orientation="h", x=0, xanchor="left", y=-0.02, yanchor="top", len=0.5 if not mobile else 1,
                                  thickness=10, outlinewidth=0, title=dict(text=legend, side="top"), tickformat=tickformat)
    text = ("code" if mobile else "label") if text == "auto" else text
    h = _hex_layer(fig, values, hexes, zmin, zmax, scale, muted, flags or set(), "", text, bar)
    islands = regions is not None and not mobile           # ponsel: nama pulau bertabrakan → hanya di desktop
    _hex_axes(fig, hexes, islands=islands)
    if islands:
        _island_labels(fig, h, regions)
    if callouts and not mobile:
        _callouts(fig, h, callouts)
    fig = S.finish(fig, title, subtitle, height=height or (500 if not mobile else 330))
    fig.update_layout(margin_b=fig.layout.margin.b + (0 if muted else 64))
    return fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", dragmode=False)


def hex_tile_grid(values: pd.DataFrame, hexes: pd.DataFrame, labels: dict, detected: set, zmax: float,
                  legend: str, flags: pd.DataFrame | None = None) -> go.Figure:
    """Peta heksagon kecil, satu per komoditas (`values` = commodity, province_id, value, hover), skala warna sama untuk
    semua panel. Komoditas di luar `detected` digambar abu-abu (perbedaan antarprovinsi tidak lebih besar dari derau) dan
    diletakkan sesudah yang terdeteksi; `flags` = (commodity, province_id) bergaris tebal. Desktop 5 kolom, ponsel 2.
    Panel terlalu kecil untuk teks, jadi nama provinsi hanya di keterangan kursor."""
    present = [c for c in labels if c in set(values["commodity"])]
    coms = [c for c in present if c in detected] + [c for c in present if c not in detected]   # berwarna di depan
    mobile = S.WRAP.get()[0] is not None
    cols = 2 if mobile else 5
    rows = max(1, -(-len(coms) // cols))
    titles = [f"{labels.get(c, c)}<br><span style='font-size:11px'>"
              f"{'beda terdeteksi' if c in detected else 'tidak terdeteksi'}</span>" for c in coms]
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titles, horizontal_spacing=0.03,
                        vertical_spacing=min(0.3, 0.9 / rows))
    fl = flags if flags is not None else pd.DataFrame(columns=["commodity", "province_id"])
    for i, c in enumerate(coms):
        ax = "" if i == 0 else str(i + 1)
        bar = (dict(orientation="h", x=0, xanchor="left", y=-0.04, yanchor="top", len=0.4 if not mobile else 1,
                    thickness=9, outlinewidth=0, title=dict(text=legend, side="top")) if i == 0 else None)
        _hex_layer(fig, values[values["commodity"] == c], hexes, -zmax, zmax, S.DIVERGING, c not in detected,
                   set(fl.loc[fl["commodity"] == c, "province_id"].astype(int)), ax, None, bar)
        _hex_axes(fig, hexes, ax)
    fig.update_annotations(font_size=12)
    fig = S.finish(fig, "Semua komoditas: kepekaan tiap provinsi dibanding nasional",
                   "Satu heksagon = satu provinsi, skala warna sama untuk semua panel. Label panel: apakah perbedaan "
                   "antarprovinsi terdeteksi. Abu-abu berarti perbedaannya tidak lebih besar dari kebetulan. Garis tebal: tetap berbeda setelah koreksi banyak perbandingan. "
                   f"{CAUSAL_NOTE}",
                   height=(135 if not mobile else 150) * rows + 230)
    return fig.update_layout(margin_t=fig.layout.margin.t + 78, margin_b=fig.layout.margin.b + 58,
                             plot_bgcolor="rgba(0,0,0,0)", dragmode=False)


def episode_matrix(episodes: pd.DataFrame, events: pd.DataFrame, labels: dict | None = None,
                   horizon: int = 8) -> go.Figure:
    """Matriks episode × komoditas (artefak `episodes`, `events`, nasional). Atas: kenaikan kurs per episode (batang satu
    warna, berurutan menurut waktu tetapi berjarak sama agar episode yang berdekatan tidak bertumpuk). Bawah: satu titik per
    komoditas dan episode untuk perubahan harga `horizon` minggu sesudah awal episode: merah = naik melewati rentang 95%
    jendela tanpa episode, biru = turun melewati rentang, abu-abu kecil = di dalam rentang, lingkaran kosong = belum
    teramati. Kolom kanan: jumlah episode di luar rentang per komoditas."""
    lab = labels or {}
    ep = episodes.copy()
    ep["start_week"] = pd.to_datetime(ep["start_week"])
    ep = ep.sort_values("start_week").reset_index(drop=True)
    ep["i"] = np.arange(1, len(ep) + 1)
    ep["pct"] = 100 * np.expm1(ep["cum_dlog_e"])
    ep["tick"] = [S.month_year(t) for t in ep["start_week"]]
    e = events[(events["level"] == "national") & (events["horizon"] == horizon)].dropna(subset=["dlog_price"]).copy()
    coms = [c for c in lab if c in set(e["commodity"])] or list(dict.fromkeys(e["commodity"]))
    e = e[e["commodity"].isin(coms)].merge(ep[["episode_id", "i", "tick"]], on="episode_id")
    e["pct"] = 100 * np.expm1(e["dlog_price"])
    e["state"] = np.select([e["dlog_price"] > e["placebo_hi"], e["dlog_price"] < e["placebo_lo"]], ["up", "down"], "in")
    e["name"] = e["commodity"].map(lambda c: lab.get(c, c))
    names = [lab.get(c, c) for c in coms]
    mobile = S.WRAP.get()[0] is not None
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.26, 0.74], vertical_spacing=0.05)
    fig.add_trace(go.Bar(x=ep["i"], y=ep["pct"], marker=dict(color=S.BLUE_RAMP[1], cornerradius=3), showlegend=False,
                         customdata=np.c_[ep["tick"]], width=0.55,
                         hovertemplate="Episode %{customdata[0]}<br>rupiah melemah %{y:.1f}%<extra></extra>"), row=1, col=1)
    big = ep.loc[ep["pct"].idxmax()] if len(ep) else None
    if big is not None:
        fig.add_annotation(x=big["i"], y=big["pct"], text=f"{S.fmt_num(big['pct'], 1)}%", showarrow=False, yshift=10,
                           font=dict(size=11, color=INK), row=1, col=1)
    styles = {"up": dict(color=UP, size=12, symbol="circle", name="harga naik di luar rentang normal"),
              "down": dict(color=DOWN, size=12, symbol="circle", name="harga turun di luar rentang normal"),
              "in": dict(color="#c9c7bf", size=6, symbol="circle", name="di dalam rentang normal")}
    for st_, s in styles.items():
        g = e[e["state"] == st_]
        fig.add_trace(go.Scatter(
            x=g["i"], y=g["name"], mode="markers", name=s["name"],
            marker=dict(color=s["color"], size=s["size"], line=dict(color="#ffffff", width=1.5)),
            customdata=np.c_[g["tick"], g["pct"]],
            hovertemplate="%{y}, episode %{customdata[0]}<br>" + f"{horizon} minggu kemudian: " + "%{customdata[1]:+.1f}%"
                          + f"<br>{s['name']}<extra></extra>"), row=2, col=1)
    have = set(zip(e["commodity"], e["episode_id"]))
    pend = [(r.i, lab.get(c, c)) for r in ep.itertuples() for c in coms if (c, r.episode_id) not in have]
    if pend:
        fig.add_trace(go.Scatter(x=[p[0] for p in pend], y=[p[1] for p in pend], mode="markers", name="belum teramati",
                                 marker=dict(color="rgba(0,0,0,0)", size=8, line=dict(color=S.NEUTRAL, width=1.2)),
                                 hovertemplate="%{y}<br>harga " + f"{horizon}" + " minggu sesudahnya belum teramati"
                                               "<extra></extra>"), row=2, col=1)
    out = e[e["state"] != "in"].groupby("name").size().reindex(names, fill_value=0)
    n_obs = e.groupby("name").size().reindex(names, fill_value=0)
    if not mobile:                    # jumlah per komoditas di kanan matriks
        fig.add_annotation(x=len(ep) + 0.8, y=1.0, xref="x2", yref="y2 domain", yanchor="bottom", xanchor="left",
                           showarrow=False,
                           text="di luar<br>rentang", font=dict(size=11, color=INK_MUTED))
        for nm in names:
            fig.add_annotation(x=len(ep) + 0.8, y=nm, text=f"{out[nm]} dari {n_obs[nm]}", showarrow=False, xanchor="left",
                               font=dict(size=11, color=INK if out[nm] else INK_MUTED), row=2, col=1)
    fig.update_yaxes(categoryorder="array", categoryarray=names[::-1], showgrid=False, row=2, col=1)
    years = ep["start_week"].dt.year
    ticks = ([str(y) if k == 0 or y != years.iloc[k - 1] else "" for k, y in enumerate(years)] if mobile   # ponsel: tahun
             else [t.replace(" ", "<br>") for t in ep["tick"]])
    fig.update_yaxes(title_text="melemah (%)", rangemode="tozero", row=1, col=1,
                     range=[0, float(ep["pct"].max()) * 1.3 if len(ep) else 1])
    fig.update_xaxes(tickmode="array", tickvals=list(ep["i"]),
                     ticktext=ticks, tickangle=-90 if mobile else 0,
                     range=[0.4, len(ep) + (0.6 if mobile else 2.2)], showgrid=False, row=2, col=1)
    fig.update_xaxes(showgrid=False, row=1, col=1)
    expected = S.fmt_num(len(e) * 0.05, 0)
    fig = S.finish(fig, f"Harga {horizon} minggu setelah setiap episode pelemahan rupiah",
                   f"Batang: seberapa jauh rupiah melemah. Titik: satu per komoditas dan episode. {int(out.sum())} dari "
                   f"{len(e)} titik keluar dari rentang normal, sedangkan kebetulan menghasilkan sekitar {expected}. "
                   f"{CAUSAL_NOTE}",
                   height=620 if not mobile else 660)
    if not mobile:                    # label episode dua baris (bulan, tahun) + legenda di bawahnya
        fig.update_layout(margin_b=fig.layout.margin.b + 70, legend_y=-0.14)
    return fig.update_layout(bargap=0.4)


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
        fig.add_trace(go.Scatter(x=d["delta"], y=d["recovery_rate"], mode="lines+markers", name=f"{k} kelompok buatan",
                                 line=dict(color=color, width=2), marker=dict(size=8, color=color),
                                 hovertemplate="selisih %{x:.1f}<br><b>%{y:.0%}</b> percobaan menemukannya<extra></extra>"))
    fig.add_hline(y=threshold, line_dash="dash", line_color=S.NEUTRAL, line_width=1,
                  annotation_text=f"batas {threshold:.0%}", annotation_position="bottom right")
    fig.update_yaxes(range=[0, 1.05], tickformat=".0%")
    return S.finish(fig, "Perbedaan antarkelompok yang akan tertangkap",
                    "Kami menanam 2 atau 3 kelompok provinsi buatan pada data dengan kurs diacak, lalu menjalankan metode "
                    "yang sama seperti pada data asli.",
                    x="selisih respons antarkelompok yang ditanam (% per 1% kurs)", y="percobaan yang menemukan kelompoknya")


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
        hovertemplate="%{x} kelompok<br>silhouette <b>%{y:.3f}</b><extra></extra>"))
    if np.isfinite(thr):
        fig.add_hline(y=thr, line_dash="dash", line_color=S.NEUTRAL, line_width=1,
                      annotation_text=f"batas data acak {S.fmt_num(thr, 3)}", annotation_position="top left")
    title = ("Tidak ada jumlah kelompok yang melewati batas data acak" if not above.any()
             else "Pengelompokan provinsi melewati batas data acak")
    fig.update_xaxes(dtick=1)
    return S.finish(fig, title, "Titik: skor silhouette terbaik (Ward) untuk 2 sampai 6 kelompok. Garis putus: persentil 95 "
                    "skor yang sama pada data dengan kurs diacak.", x="jumlah kelompok", y="skor silhouette")


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
    fig.for_each_annotation(lambda a: a.update(text=a.text.replace("horizon=", "prediksi ") + " minggu"))
    n = d["n_origins"].dropna() if "n_origins" in d else pd.Series(dtype=float)
    n_txt = (f"{int(n.min())}" if n.min() == n.max() else f"{int(n.min())}–{int(n.max())}") if len(n) else "?"
    fig = S.finish(fig, f"Galat relatif terhadap model dasar, {S.SUBSET_LABELS.get(subset, subset)}",
                   f"Kiri dari garis 1 berarti lebih akurat dari model dasar. {n_txt} titik prediksi, evaluasi "
                   "pseudo-real-time.", x="rasio MAE terhadap model dasar", y="",
                   height=max(320, 34 * d["komoditas"].nunique() + 160))
    return fig.update_layout(margin_t=fig.layout.margin.t + 24)   # ruang judul panel di bawah subjudul (tidak bertumpuk)


def forest(df: pd.DataFrame, label_cols: list[str], title: str, x_title: str | None = None,
           subtitle: str | None = None, x_range: tuple[float, float] | None = None) -> go.Figure:
    """Forest plot estimasi + interval (artefak `assoc`, `robustness`, `profiles`, `regime_profiles`). Titik penuh =
    interval tidak memuat nol, titik kosong = memuat nol (pengkodean kedua selain posisi). `x_range` memotong sumbu agar
    interval sempit tetap terbaca; interval yang melewati batas diberi segitiga di tepi grafik (nilainya di hover)."""
    d = df.assign(label=df[label_cols].astype(str).agg(", ".join, axis=1))
    if S.WRAP.get()[0]:                          # ponsel: label panjang dibungkus agar area plot tidak terlalu sempit
        d["label"] = d["label"].map(lambda v: "<br>".join(S.wrap_lines(v, 18)))
    excl = (d["ci_low"] > 0) | (d["ci_high"] < 0)
    fig = go.Figure(go.Scatter(
        x=d["estimate"], y=d["label"], mode="markers", showlegend=False,
        marker=dict(size=10, color=np.where(excl, S.BLUE, "rgba(0,0,0,0)"), line=dict(color=S.BLUE, width=2),
                    symbol="circle"),
        error_x=dict(type="data", symmetric=False, array=d["ci_high"] - d["estimate"],
                     arrayminus=d["estimate"] - d["ci_low"], color=S.BLUE, thickness=1.5, width=0),
        customdata=np.c_[d["ci_low"], d["ci_high"]],
        hovertemplate="%{y}<br><b>%{x:.2f}</b><br>rentang 95%: %{customdata[0]:.2f} s.d. %{customdata[1]:.2f}<extra></extra>"))
    fig.add_vline(x=0, line_color=S.NEUTRAL, line_width=1)
    if x_range is not None:
        lo, hi = x_range
        fig.update_xaxes(range=[lo, hi])
        for side, edge, sym in ((d["ci_high"] > hi, hi, "triangle-right"), (d["ci_low"] < lo, lo, "triangle-left")):
            g = d[side]
            if len(g):
                fig.add_trace(go.Scatter(
                    x=[edge] * len(g), y=g["label"], mode="markers", showlegend=False, cliponaxis=False,
                    marker=dict(size=9, color=S.BLUE, symbol=sym), customdata=np.c_[g["ci_low"], g["ci_high"]],
                    hovertemplate="%{y}<br>rentang melewati batas grafik: %{customdata[0]:.2f} s.d. %{customdata[1]:.2f}"
                                  "<extra></extra>"))
    sub = subtitle or "Titik penuh: rentang 95% tidak memuat nol. Titik kosong: memuat nol."
    row_px = 30 + 15 * (int(d["label"].str.count("<br>").max()) if len(d) else 0)   # label dibungkus → baris lebih tinggi
    return S.finish(fig, title, f"{sub} {CAUSAL_NOTE}", x=x_title, height=max(300, row_px * len(d) + 120))


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
    comp_names = {"e_global": "komponen dolar global", "e_idr": "komponen khusus rupiah"}
    comp = np.where(d["driver"] != driver, ", " + d["driver"].map(lambda x: comp_names.get(x, x)).astype(str), "")
    d["label"] = d["cek"] + np.where(var != "", ", " + var, "") + comp
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
            hovertemplate="%{y}<br><b>%{x:.2f}</b><br>rentang 95%: %{customdata[0]:.2f} s.d. %{customdata[1]:.2f}"
                          "<br>%{customdata[2]}<extra></extra>"))
    base = d.loc[d["driver"] == driver, "baseline_estimate"].dropna()
    base_txt = "Garis putus: estimasi utama."
    if len(base):                       # nilai di subjudul, bukan anotasi garis: anotasi "top" menimpa baris subjudul
        fig.add_vline(x=float(base.iloc[0]), line_dash="dash", line_color=S.NEUTRAL, line_width=1)
        base_txt = f"Garis putus: estimasi utama ({S.fmt_num(float(base.iloc[0]), 2)})."
    fig.add_vline(x=0, line_color=S.NEUTRAL, line_width=1)
    return S.finish(fig, f"{name or commodity}: respons terhadap {S.DRIVER_LABELS.get(driver, driver).lower()} pada setiap "
                         f"cek ketahanan ({horizon} minggu)",
                    f"Titik kosong: rentang 95% memuat nol. {base_txt} {CAUSAL_NOTE}",
                    x=S.AXIS_LABELS.get(driver, "respons kumulatif"), height=max(320, 26 * len(d) + 160))


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
            hovertemplate="minggu ke-%{customdata[0]}<br><b>%{y:.2f}</b><br>rentang 95%: %{customdata[1]:.2f} s.d. "
                          "%{customdata[2]:.2f}<extra></extra>"))
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    fig.update_xaxes(tickvals=list(range(len(hs))), ticktext=[f"{h} minggu" for h in hs], range=[-0.6, len(hs) - 0.4])
    a = asymmetry[(asymmetry["commodity"] == commodity) & (asymmetry["horizon"] == 8)]
    sub = CAUSAL_NOTE
    if len(a):
        r = a.iloc[0]
        kind = "uji konfirmatori praregistrasi" if bool(r.get("confirmatory", False)) else "deskriptif"
        sub = (f"Selisih 8 minggu (melemah dikurangi menguat): {S.fmt_num(r['estimate'], 2)}, rentang 95% "
               f"{S.fmt_interval(r['ci_low'], r['ci_high'])}, {S.detection_status(r['ci_low'], r['ci_high'])} ({kind}). "
               f"{CAUSAL_NOTE}")
    return S.finish(fig, f"{name or commodity}: respons saat rupiah melemah dan saat menguat", sub,
                    x="", y=S.AXIS_LABELS["e_pos"])


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


def scenario_paths(pt: pd.DataFrame, shocks: list[float], selected: float, title: str | None = None) -> go.Figure:
    """Skenario bersyarat untuk setiap pelemahan x (%): perubahan harga = `scenario_change` (exp(PT(h)·ln(1 + x/100)) − 1;
    baris `profiles` driver PT satu komoditas & unit). Pita hanya untuk x terpilih dan hanya bila interval PT ada; bukan ramalan."""
    d = pt.sort_values("horizon")
    fig = go.Figure()
    if d[["ci_low", "ci_high"]].notna().all(axis=1).any():
        lo, hi = scenario_change(d["ci_low"], selected), scenario_change(d["ci_high"], selected)
        fig.add_trace(go.Scatter(x=d["horizon"], y=np.maximum(lo, hi), mode="lines", line=dict(width=0), showlegend=False,
                                 hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=d["horizon"], y=np.minimum(lo, hi), fill="tonexty",
                                 fillcolor=S.rgba(S.BLUE, 0.15), mode="lines", line=dict(width=0), name=f"rentang 95% ({selected}%)",
                                 hoverinfo="skip"))
    ramp = S.BLUE_RAMP[-len(shocks):] if len(shocks) <= len(S.BLUE_RAMP) else S.BLUE_RAMP
    for color, x in zip(ramp, sorted(shocks)):
        fig.add_trace(go.Scatter(x=d["horizon"], y=scenario_change(d["estimate"], x), mode="lines", name=f"pelemahan {x}%",
                                 line=dict(color=color, width=3 if x == selected else 1.5),
                                 hovertemplate=f"rupiah melemah {x}%<br>minggu ke-%{{x}}<br><b>%{{y:.2f}}%</b><extra></extra>"))
    fig.add_hline(y=0, line_color=S.NEUTRAL, line_width=1)
    has_band = d[["ci_low", "ci_high"]].notna().all(axis=1).any()
    return S.finish(fig, title or "Perubahan harga setelah rupiah melemah",
                    "Skenario bersyarat dari pola historis, bukan ramalan. "
                    + (f"Pita: rentang 95% untuk pelemahan {selected}%." if has_band else "Rentang 95% tidak tersedia."),
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
    d["label"] = [f"{(labels or {}).get(t, t)}, {x:%d %b %H:%M}" for t, x in zip(d["task_id"], d["t"])]
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
        sub += ". Belum ada waktu eksekusi tercatat untuk " + ", ".join(never) + "."
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
    return S.finish(fig, f"{name} antar run ({task_id})", f"{len(good)} nilai dari {len(m)} run",
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
    placed: list[tuple[float, float]] = []
    for r in pairs.itertuples():
        if r.producer == r.consumer:
            continue
        (x0, y0), (x1, y1) = pos[r.producer], pos[r.consumer]
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", showlegend=False, hoverinfo="skip",
                                 line=dict(color=S.NEUTRAL, width=1 + min(r.n, 6) / 2,
                                           dash="solid" if r.required else "dot")))
        # Angka jumlah artefak di antara dua lapisan (x0 + 0.5, x0 + 1.5, ...), bukan di titik tengah: garis yang
        # melompati lapisan punya titik tengah tepat di kolom simpul dan menimpa labelnya. Posisi yang sudah dipakai
        # angka lain dilewati (garis segaris dari simpul yang sama).
        span = max(x1 - x0, 1)
        cands = [k + 0.5 for k in range(int(span))] + [k + f for k in range(int(span)) for f in (0.3, 0.7)]
        lx, ly = x0 + cands[0], y0 + (y1 - y0) * cands[0] / span
        for c in cands:
            cx, cy = x0 + c, y0 + (y1 - y0) * c / span
            if all(abs(cx - px) > 0.18 or abs(cy - py) > 0.45 for px, py in placed):
                lx, ly = cx, cy
                break
        placed.append((lx, ly))
        fig.add_annotation(x=lx, y=ly, text=str(r.n), showarrow=False,   # kontras (D-140)
                           font=dict(size=12, color="#1a1a1a"), bgcolor="#ffffff", bordercolor=S.NEUTRAL,
                           borderpad=2, hovertext=r.artifacts)
    for st_name in dict.fromkeys(status.get(n, "belum ada run") for n in nodes):
        members = [n for n in nodes if status.get(n, "belum ada run") == st_name]
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in members], y=[pos[n][1] for n in members], mode="markers+text",
            name=RUN_STATUS_LABELS.get(st_name, st_name),
            text=[(labels or {}).get(n, n) + (" (basi)" if n in stale else "") for n in members],
            textposition="bottom center", marker=dict(size=26, color=RUN_STATUS_COLORS.get(st_name, S.NEUTRAL),
                                                   line=dict(width=2, color="white")),
            hovertemplate="%{text}<extra></extra>"))
    x_max = max(p[0] for p in pos.values())
    y_abs = max([abs(p[1]) for p in pos.values()] + [0.5])
    fig.update_xaxes(visible=False, range=[-0.7, x_max + 0.7])           # ruang untuk label simpul di tepi
    fig.update_yaxes(visible=False, range=[-y_abs - 0.6, y_abs + 0.4])
    fig = S.finish(fig, "Alur data antar-tahap", "Garis penuh menandai input wajib, garis titik-titik input opsional. "
                   "Angka di garis adalah jumlah artefak, warna simpul adalah status tahap.", height=380)
    fig.update_xaxes(showgrid=False)
    return fig
