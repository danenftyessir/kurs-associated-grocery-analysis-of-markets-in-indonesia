"""Sistem tampilan bersama grafik & app (PLAN.md §18.4): palet tervalidasi, label bahasa pengguna, format angka Indonesia.

Palet kategoris = 3 slot pertama palet referensi skill dataviz (lolos validator semua-pasangan di mode terang & gelap:
CVD ΔE terburuk 9,2, normal 24,0). Aqua < 3:1 di permukaan terang → selalu dipasangkan dengan label/tabel.
Warna mengikuti entitas, bukan urutan (mis. M2 selalu biru).
"""

from __future__ import annotations

import math

import plotly.graph_objects as go

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
NEUTRAL = "#898781"                       # pembanding / plasebo / tidak berlaku
BLUE_RAMP = ["#86b6ef", "#3987e5", "#1c5cab", "#104281"]          # ordinal terang → gelap (≥ langkah 250)
# Diverging biru ↔ merah, titik tengah abu-abu netral (tidak ada hue di nol): negatif = biru, positif = merah.
DIVERGING = [[0.0, "#104281"], [0.25, "#5598e7"], [0.5, "#b4b2ab"], [0.75, "#e8736f"], [1.0, "#a32a2b"]]
SEQUENTIAL = [[0.0, "#cde2fb"], [0.5, "#3987e5"], [1.0, "#0d366b"]]
STATUS_COLORS = {"observed": "#104281", "carry_forward": "#6da7ec", "short": "#b7d3f6", "missing": NEUTRAL}
MODEL_COLORS = {"M0": NEUTRAL, "M1": NEUTRAL, "M2": BLUE, "M3": ORANGE, "M2_nofx": NEUTRAL}
SERIES = [BLUE, ORANGE, AQUA]

# Kosakata pembaca (D-171): juri & analis TPID, bukan notasi model. Notasi (β, ω, PT, M1/M2, h) dijelaskan di Daftar
# istilah halaman Data & metode; halaman hasil memakai label di bawah ini.
DRIVER_LABELS = {"e": "Kurs rupiah", "w": "Harga dunia (rupiah)", "e_pos": "Saat rupiah melemah",
                 "e_neg": "Saat rupiah menguat", "PT": "Penerusan kurs"}
UNIT_LABELS = {"e": "% perubahan harga per 1% pelemahan rupiah", "w": "% perubahan harga per 1% kenaikan harga dunia",
               "e_pos": "% perubahan harga per 1% perubahan kurs", "e_neg": "% perubahan harga per 1% perubahan kurs",
               "PT": "porsi pelemahan rupiah yang muncul di harga"}
AXIS_LABELS = {"e": "% per 1% pelemahan rupiah", "w": "% per 1% kenaikan harga dunia", "e_pos": "% per 1% perubahan kurs",
               "e_neg": "% per 1% perubahan kurs", "PT": "penerusan kurs"}
LEVEL_LABELS = {"national": "Nasional", "region": "Wilayah", "province": "Provinsi"}
MODEL_LABELS = {"M0": "Tanpa perubahan", "M1": "Model dasar", "M2": "Dasar + kurs & harga dunia",
                "M3": "Boosting + identitas seri", "M2_nofx": "Dasar (pembanding ablation)"}
SUBSET_LABELS = {"all": "semua titik prediksi", "large_move": "saat kurs bergerak besar", "case_study": "studi kasus 2026"}
CHECK_LABELS = {
    "exclude_covid_and_extreme_brent": "tanpa Mar–Jun 2020 & bulan Brent ekstrem",
    "fx_decomposition_global_dollar_vs_idr_specific": "dekomposisi kurs",
    "horizon_8_vs_12": "horizon 8 vs 12",
    "lags_2_4_8": "jumlah lag",
    "monthly_frequency": "frekuensi bulanan",
    "subperiod_pre_post_2021-04-05": "sub-periode (perubahan metode JISDOR)",
    "alternative_variants": "varian PIHPS alternatif",
    "last_observation_aggregation": "agregasi observasi terakhir",
    "bapanas_outcome": "outcome Panel Harga Bapanas",
}
PATH_LABELS = {"direct_import": "Impor langsung", "imported_input": "Input impor (pakan)", "export_parity": "Paritas ekspor",
               "domestic": "Domestik"}
FEATURE_LABELS = {"ln_dist_hub": "Jarak ke hub logistik (ln km)", "rice_sufficiency": "Kecukupan produksi beras",
                  "n_kota": "Jumlah kota sampel PIHPS"}
CAUSAL_NOTE = "Asosiasi historis, bukan sebab-akibat."
MINUS = "−"


def fmt_num(x: float, digits: int = 2, sign: bool = False, pct: bool = False) -> str:
    """Angka format Indonesia: desimal koma, ribuan titik, tanda minus tipografis; NaN → 'tidak tersedia'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "tidak tersedia"
    s = f"{abs(x):,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    lead = MINUS if x < 0 else ("+" if sign and x > 0 else "")
    return f"{lead}{s}{'%' if pct else ''}"


def fmt_interval(lo: float, hi: float, digits: int = 2, pct: bool = False) -> str:
    """'lo s.d. hi' format Indonesia, atau 'interval tidak tersedia'."""
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (lo, hi)):
        return "interval tidak tersedia"
    return f"{fmt_num(lo, digits, True, pct)} s.d. {fmt_num(hi, digits, True, pct)}"


def detection_status(lo: float, hi: float) -> str:
    """Lencana: 'tidak terdeteksi' bila interval memuat nol; 'interval tidak tersedia' bila NaN."""
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (lo, hi)):
        return "interval tidak tersedia"
    return "tidak terdeteksi" if lo <= 0 <= hi else "terdeteksi"


def dm_summary(stat: float, p_two: float, p_one: float | None = None, model: str = "M2", ref: str = "M1",
               alpha: float = 0.05) -> str:
    """Uji Diebold–Mariano dengan ARAH, bukan hanya p (D-169). Konvensi `stats.regression.diebold_mariano` & artefak
    `forecast_eval`: DM > 0 = `model` lebih akurat dari `ref`, DM < 0 = kurang akurat. p dua sisi menguji "berbeda"; p satu
    sisi menguji "`model` lebih akurat" (arah RQ5/H5). Bila p satu sisi tidak diberikan, diturunkan dari p dua sisi dan tanda
    DM (distribusi simetris, sama dengan `evaluation.forecast_eval`). NaN → 'uji DM tidak tersedia'."""
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (stat, p_two)):
        return "uji DM tidak tersedia"
    if p_one is None or (isinstance(p_one, float) and math.isnan(p_one)):
        p_one = p_two / 2 if stat > 0 else 1 - p_two / 2
    word = "lebih akurat dari" if stat > 0 else ("kurang akurat dari" if stat < 0 else "setara dengan")
    verdict = f"{model} {word} {ref}" if p_two < alpha else f"{model} {word} {ref}, tetapi tidak nyata"
    return (f"DM {fmt_num(stat, 2, sign=True)}: {verdict} (p dua sisi {fmt_num(p_two, 3)}). "
            f"p satu sisi untuk “{model} lebih akurat”: {fmt_num(p_one, 3)}.")


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def finish(fig: go.Figure, title: str, subtitle: str | None = None, x: str | None = None, y: str | None = None,
           height: int | None = None) -> go.Figure:
    """Tata letak seragam: judul = pertanyaan/temuan, subjudul = satuan/catatan, pemisah angka Indonesia,
    grid tipis solid, legenda di atas. Warna latar & font dibiarkan ke tema Streamlit (terang/gelap)."""
    t = {"text": title, "x": 0, "xanchor": "left"}
    lines = 0
    if subtitle:
        rows = []                                      # Plotly tidak membungkus teks: bungkus per kata (± 72 karakter)
        for para in subtitle.split("\n"):
            cur = ""
            for w in para.split():
                if cur and len(cur) + 1 + len(w) > 72:
                    rows.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}" if cur else w
            rows.append(cur)
        lines = len(rows)
        t["subtitle"] = {"text": "<br>".join(rows)}
    fig.update_layout(title=t, separators=",.", hovermode="closest",
                      legend={"orientation": "h", "yanchor": "top", "y": -0.18, "x": 0, "title": None},
                      margin={"t": 60 + 18 * lines, "l": 10, "r": 10, "b": 10})
    if height:
        fig.update_layout(height=height)
    if x is not None:
        fig.update_xaxes(title_text=x)
    if y is not None:
        fig.update_yaxes(title_text=y)
    fig.update_xaxes(showgrid=True, gridwidth=1, zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, zeroline=False)
    return fig
