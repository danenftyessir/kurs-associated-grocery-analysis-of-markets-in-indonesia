"""Grafik bersama (plotly) untuk notebook dan app Streamlit. Input = artefak dari utils/artifacts.py.

Aturan tampilan (proposal §7.1): setiap grafik menampilkan interval bila ada, satuan di sumbu, dan catatan
"asosiasi, bukan kausalitas" pada judul grafik respons.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CAUSAL_NOTE = "asosiasi historis, bukan kausalitas"
STATUS_ORDER = ["observed", "carry_forward", "short", "missing"]


def response_curve(profiles: pd.DataFrame, commodity: str, level: str, unit: str, driver: str) -> go.Figure:
    """Kurva respons kumulatif h = 0..12 dengan pita interval (artefak `profiles`)."""
    d = profiles[(profiles["commodity"] == commodity) & (profiles["level"] == level)
                 & (profiles["unit"].astype(str) == str(unit)) & (profiles["driver"] == driver)].sort_values("horizon")
    fig = go.Figure([
        go.Scatter(x=d["horizon"], y=d["ci_high"], line=dict(width=0), showlegend=False, hoverinfo="skip"),
        go.Scatter(x=d["horizon"], y=d["ci_low"], fill="tonexty", line=dict(width=0), name="interval 95%"),
        go.Scatter(x=d["horizon"], y=d["estimate"], mode="lines+markers", name="respons kumulatif"),
    ])
    fig.add_hline(y=0, line_dash="dot")
    fig.update_layout(title=f"{commodity} · {level} {unit} · {driver} ({CAUSAL_NOTE})",
                      xaxis_title="minggu setelah perubahan", yaxis_title="Δ log harga per 1 poin log penggerak")
    return fig


def sensitivity_heatmap(features: pd.DataFrame, level: str, metric: str = "R8") -> go.Figure:
    """Peta kepekaan: respons kumulatif `metric` (R4/R8/R12/W8/PT8) per komoditas x unit pada satu level
    (artefak `response_features`; provinsi/wilayah). Sel kosong = tidak tersedia."""
    m = features[features["level"] == level].pivot(index="commodity", columns="unit", values=metric)
    return px.imshow(m, color_continuous_scale="RdBu_r", color_continuous_midpoint=0, aspect="auto",
                     labels=dict(color=metric), title=f"{metric} per komoditas dan {level} ({CAUSAL_NOTE})")


def cluster_sizes(clusters: pd.DataFrame, method: str = "ward") -> go.Figure:
    """Jumlah provinsi per klaster dengan stabilitas Jaccard (artefak `clusters`); klaster lemah ditandai."""
    d = clusters[clusters["method"] == method].groupby("cluster").agg(
        provinsi=("province_id", "size"), jaccard=("jaccard", "mean"), lemah=("weak", "max")).reset_index()
    return px.bar(d, x="cluster", y="provinsi", color="lemah", hover_data=["jaccard"],
                  title=f"Ukuran & stabilitas klaster ({method}); lemah = Jaccard < ambang")


def fx_drivers(drivers: pd.DataFrame, episodes: pd.DataFrame | None = None) -> go.Figure:
    """Kurs JISDOR mingguan (Rp/USD) dengan arsiran episode depresiasi (artefak `drivers_weekly`, `episodes`)."""
    fig = go.Figure(go.Scatter(x=drivers["week"], y=np.exp(drivers["log_e"]), name="JISDOR (rerata mingguan)"))
    if episodes is not None:
        for r in episodes.itertuples():
            fig.add_vrect(x0=r.start_week, x1=r.end_week, fillcolor="red", opacity=0.15, line_width=0)
    fig.update_layout(xaxis_title="minggu", yaxis_title="Rp per USD", title="IDR/USD dan episode depresiasi ≥ 3%")
    return fig


def status_share(panel_weekly: pd.DataFrame) -> go.Figure:
    """Porsi status sel mingguan per komoditas (artefak `panel_weekly`)."""
    share = (panel_weekly.groupby("commodity")["status"].value_counts(normalize=True)
             .rename("share").reset_index())
    return px.bar(share, x="commodity", y="share", color="status", category_orders={"status": STATUS_ORDER},
                  title="Status sel mingguan (carry_forward = penanda, bukan filter)")


def coassign_heatmap(coassign: pd.DataFrame) -> go.Figure:
    """Matriks ko-asignasi bootstrap (artefak `coassign`)."""
    m = coassign.pivot(index="province_i", columns="province_j", values="share")
    return px.imshow(m, color_continuous_scale="Blues", zmin=0, zmax=1, title="Ko-asignasi bootstrap")


def recovery_curve(planted: pd.DataFrame) -> go.Figure:
    """Kurva pemulihan struktur tertanam = batas deteksi (artefak `planted_recovery`)."""
    fig = px.line(planted, x="delta", y="recovery_rate", color="k_true", markers=True,
                  title="Batas deteksi struktur regional")
    fig.add_hline(y=0.8, line_dash="dot")
    return fig


def forecast_ratios(forecast_eval: pd.DataFrame, subset: str = "all") -> go.Figure:
    """Rasio MAE vs M1 per komoditas & model (artefak `forecast_eval`); < 1 = lebih akurat dari M1."""
    d = forecast_eval[(forecast_eval["subset"] == subset) & (forecast_eval["model"] != "M1")]
    fig = px.bar(d, x="commodity", y="mae_ratio_vs_m1", color="model", barmode="group", facet_row="horizon",
                 title=f"Rasio MAE terhadap M1 ({subset}; evaluasi bersyarat, pseudo-real-time)")
    fig.add_hline(y=1, line_dash="dot")
    return fig


def forest(df: pd.DataFrame, label_cols: list[str], title: str) -> go.Figure:
    """Forest plot estimasi + interval (artefak `assoc`, `robustness`)."""
    d = df.assign(label=df[label_cols].astype(str).agg(" · ".join, axis=1))
    fig = go.Figure(go.Scatter(
        x=d["estimate"], y=d["label"], mode="markers",
        error_x=dict(type="data", symmetric=False, array=d["ci_high"] - d["estimate"],
                     arrayminus=d["estimate"] - d["ci_low"])))
    fig.add_vline(x=0, line_dash="dot")
    fig.update_layout(title=f"{title} ({CAUSAL_NOTE})", height=max(300, 28 * len(d)))
    return fig
