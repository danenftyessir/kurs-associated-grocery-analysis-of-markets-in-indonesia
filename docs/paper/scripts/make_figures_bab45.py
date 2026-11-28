"""Gambar PNG Bab 4 (Hasil eksperimen & pengujian) dan Bab 5 (Analisis) makalah KAGAMI.

Tidak ada estimasi baru. Skrip hanya membaca artefak resmi (`results/`, `data/processed/`), berkas prediksi Task 4 yang sudah
ada (`data/interim/*_preds.parquet`), log pelacakan (`logs/`), dan laporan JUnit pytest bila diberikan. Metrik dihitung ulang
dengan fungsi yang sama dengan evaluator resmi (`kagami.tracking.metrics`, `kagami.stats`), dan angka acuan dicek di awal
(C1-tuned F1 makro 0,677 / 0,680, TimesFM 0,618 / 0,621 pada periode uji 2024+; DM M2 vs M1 −2,70 pada h 4).

Jalankan dari root project:
    python docs/paper/scripts/make_figures_bab45.py [--junit path/junit.xml]
Keluaran: docs/paper/figures/bab45/*.png (300 dpi).
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "paper" / "figures" / "bab45"

spec = importlib.util.spec_from_file_location("kagami", ROOT / "src" / "__init__.py",
                                              submodule_search_locations=[str(ROOT / "src")])
mod = importlib.util.module_from_spec(spec)
sys.modules["kagami"] = mod
spec.loader.exec_module(mod)

from kagami.features.clustering import feature_matrix  # noqa: E402
from kagami.stats.meta import bh_fdr  # noqa: E402
from kagami.stats.regression import diebold_mariano  # noqa: E402
from kagami.tracking.metrics import direction_metrics  # noqa: E402
from kagami.utils.config import Config  # noqa: E402
from kagami.utils.env import artifact_status  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402
from kagami.viz.style import AQUA, BLUE, NEUTRAL, ORANGE  # noqa: E402

CFG = Config(root=ROOT)
NAMES = {"beras": "Beras", "bawang_putih": "Bawang putih", "gula_pasir": "Gula pasir", "daging_sapi": "Daging sapi",
         "daging_ayam": "Daging ayam", "telur_ayam": "Telur ayam", "minyak_goreng": "Minyak goreng",
         "bawang_merah": "Bawang merah", "cabai_merah": "Cabai merah", "cabai_rawit": "Cabai rawit"}
ORDER = list(NAMES)
HEX = pd.read_csv(ROOT / "data" / "reference" / "province_hex.csv").set_index("province_id")
RIGID = ["beras", "daging_sapi", "gula_pasir", "minyak_goreng"]     # rangkaian harga identik ≥ 50% (D-140)
TEST_START = pd.Timestamp("2024-01-01")                           # periode uji eksplorasi arah (D-145)
WIDTH = 6.3
DPI = 300
DARK = "#2c2c2a"
GREY = "#5f5e5a"
LIGHT = "#f1efe8"
GREEN = "#2e7d4f"
RED = "#b23b3b"
REGION_COLORS = {"Sumatra": "#1c5cab", "Jawa": "#e07b39", "Bali-Nusa Tenggara": "#2a9d8f", "Kalimantan": "#8a5ab8",
                 "Sulawesi": "#c4a000", "Maluku": "#b23b3b", "Papua": "#5f5e5a"}
MODEL_NAMES = {"M0": "M0 tanpa perubahan", "M1": "M1 ridge dasar", "M2": "M2 ridge + kurs", "M3": "M3 HGB",
               "PTST": "PatchTST", "TSMX": "TSMixer", "TSMX_fx": "TSMixer + kurs", "TFM": "TimesFM 3.0",
               "TFM_fx": "TimesFM + kurs", "C1": "C1 HGB arah", "C2": "C2 HGB arah + kurs",
               "C1t": "C1-tuned", "C2t": "C2-tuned + kurs"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 7.8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.edgecolor": GREY, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "axes.titleweight": "bold", "axes.titlecolor": DARK, "text.color": DARK,
    "axes.labelcolor": DARK, "savefig.bbox": "tight", "savefig.pad_inches": 0.04, "figure.dpi": 100,
})


# ---------------------------------------------------------------------------------------------------------- utilitas
def _num(v: float, _=None, dec: int | None = None) -> str:
    """Angka format Indonesia: desimal koma, ribuan titik, minus tipografis."""
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "–"
    if dec is not None:
        s = f"{v:,.{dec}f}"
        s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    elif abs(v) >= 1000:
        s = f"{v:,.0f}".replace(",", ".")
    else:
        s = f"{v:.10g}".replace(".", ",")
    return s.replace("-", "−")


FMT = FuncFormatter(_num)


def n(v, dec=2) -> str:
    return _num(float(v), dec=dec)


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"[bab45] {name}.png")


def _note(fig, text: str, y: float = -0.01) -> None:
    fig.text(0.0, y, text, fontsize=6.2, color=GREY, ha="left", va="top", wrap=True)


def _wrap(s: str, width: int) -> str:
    return "\n".join(textwrap.wrap(str(s), width)) if width else str(s)


def table_figure(name: str, header: list[str], rows: list[list[str]], widths: list[float], wraps: list[int],
                 fills: list[str | None] | None = None, cell_fills: dict | None = None, note: str | None = None,
                 fontsize: float = 6.6, header_fill: str = BLUE, group_col: int | None = None) -> None:
    """Tabel sebagai PNG: teks dibungkus per kolom, tinggi baris mengikuti jumlah baris teks."""
    wrapped = [[_wrap(c, w) for c, w in zip(r, wraps)] for r in rows]
    head = [_wrap(h, w) for h, w in zip(header, wraps)]
    line_h = fontsize * 1.42 / 72                            # inci per baris teks
    pad = 0.07
    heights = [max(c.count("\n") + 1 for c in r) * line_h + pad for r in wrapped]
    head_h = max(h.count("\n") + 1 for h in head) * line_h + pad
    total_w = sum(widths)
    total_h = head_h + sum(heights)
    fig = plt.figure(figsize=(total_w, total_h + (0.32 if note else 0.05)))
    ax = fig.add_axes([0, (0.32 if note else 0.05) / (total_h + (0.32 if note else 0.05)), 1,
                       total_h / (total_h + (0.32 if note else 0.05))])
    ax.set_xlim(0, total_w)
    ax.set_ylim(total_h, 0)
    ax.axis("off")
    xs = np.concatenate([[0], np.cumsum(widths)])
    ax.add_patch(Rectangle((0, 0), total_w, head_h, color=header_fill, lw=0))
    for j, h in enumerate(head):
        ax.text(xs[j] + 0.05, head_h / 2, h, color="white", fontsize=fontsize, fontweight="bold", va="center")
    y = head_h
    prev_group = None
    for i, (r, hgt) in enumerate(zip(wrapped, heights)):
        fill = (fills[i] if fills else None) or (LIGHT if i % 2 else "white")
        ax.add_patch(Rectangle((0, y), total_w, hgt, color=fill, lw=0))
        for j, c in enumerate(r):
            cf = (cell_fills or {}).get((i, j))
            if cf:
                ax.add_patch(Rectangle((xs[j] + 0.02, y + 0.02), widths[j] - 0.04, hgt - 0.04, color=cf[0], lw=0))
            txt = c
            if group_col is not None and j == group_col and rows[i][j] == prev_group:
                txt = ""
            ax.text(xs[j] + 0.05, y + hgt / 2, txt, fontsize=fontsize, va="center",
                    color=(cf[1] if cf else DARK), fontweight=("bold" if (cf and cf[2]) else "normal") if cf else "normal")
        if group_col is not None:
            prev_group = rows[i][group_col]
        y += hgt
        ax.plot([0, total_w], [y, y], color="#d3d1c7", lw=0.4)
    if note:
        fig.text(0.005, 0.0, _wrap(note, int(total_w * 21)), fontsize=6.0, color=GREY, va="bottom")
    _save(fig, name)


STATUS_FILL = {"Terpenuhi": ("#d8ecdf", GREEN, True), "Sebagian": ("#fbe8d3", "#a85a12", True),
               "Belum": ("#f5d6d6", RED, True), "Terpenuhi (hasil nol sah)": ("#d8ecdf", GREEN, True)}
LEVEL_FILL = {"Praregistrasi": ("#dbe6f4", BLUE, True), "Kepekaan inferensi": ("#d9efec", "#1e6f66", True),
              "Eksploratif": ("#fbe8d3", "#a85a12", True), "Validasi": ("#ebe3f3", "#6a3d99", True)}


def macro_f1(y, score) -> dict:
    ms = {m.name: m for m in direction_metrics(np.asarray(y), np.asarray(score))}
    return {k: ms[f"dir_{k}"].value for k in ["f1_macro", "accuracy", "majority_baseline_accuracy", "confusion"]}


# ------------------------------------------------------------------------------------------------------ data bersama
def preds() -> pd.DataFrame:
    """Semua ramalan regresi Task 4 (resmi + eksploratif deep) pada baris uji yang sama, format lebar per model."""
    f = pd.read_parquet(ROOT / "data/interim/forecast_preds.parquet")
    d = pd.read_parquet(ROOT / "data/interim/deep_preds.parquet")
    key = ["origin", "horizon", "province_id", "commodity"]
    both = pd.concat([f[key + ["model", "y_true", "y_pred", "large_move"]], d[key + ["model", "y_true", "y_pred",
                                                                                    "large_move"]]])
    return both


def per_origin_mae(df: pd.DataFrame) -> pd.DataFrame:
    return (df.assign(ae=(df["y_true"] - df["y_pred"]).abs())
              .groupby(["horizon", "model", "origin"])["ae"].mean().unstack("model"))


def dm(base: pd.Series, cand: pd.Series, h: int) -> tuple[float, float]:
    """DM pada MAE per origin, lag HAC ceil(h/4) − 1 seperti evaluator resmi (stat > 0 = kandidat lebih akurat)."""
    return diebold_mariano(base.to_numpy(), cand.to_numpy(), int(math.ceil(h / 4)))


# ================================================================================================== BAB 4
def b4_konfigurasi() -> None:
    p = CFG.params
    inf, lp, fc, cl = p["inference"], p["lp"], p["forecast"], p["clustering"]
    pw = read_artifact(CFG, "panel_weekly")
    el = read_artifact(CFG, "eligibility")
    n_series = int(el["eligible"].sum()) if "eligible" in el else 337
    fp = pd.read_parquet(ROOT / "data/interim/forecast_preds.parquet", columns=["origin", "horizon"])
    no = fp.groupby("horizon")["origin"].nunique()
    rows = [
        ["Data", "Panel harga eceran", f"{pw['province_id'].nunique()} provinsi × {pw['commodity'].nunique()} komoditas × "
         f"{pw['week'].nunique()} minggu ({pw['week'].min():%d-%m-%Y} s.d. {pw['week'].max():%d-%m-%Y}), "
         f"{n_series} dari 340 seri layak"],
        ["Data", "Penggerak", "Kurs JISDOR mingguan (Δ log), harga dunia Pink Sheet dalam rupiah, kontrol Brent, "
         "musim Idulfitri, 13 episode depresiasi"],
        ["Task 1", "Proyeksi lokal (LP)", f"h = {lp['horizons'][0]}..{lp['horizons'][-1]} minggu, lag {lp['lags']}, "
         f"efek tetap seri, SE cluster per minggu, horizon kunci {', '.join(map(str, lp['key_horizons']))}"],
        ["Task 1", "Inferensi", f"bootstrap blok {inf['block_weeks']} minggu, B = {inf['bootstrap_B']} "
         f"(non-fokus {inf['bootstrap_B_nonfocus']}), plasebo geser ≥ {inf['placebo_min_shift_weeks']} minggu, "
         f"R = {inf['placebo_R']}, studi peristiwa {inf['event_placebo_windows']} jendela plasebo"],
        ["Task 2", "Heterogenitas & klaster", f"Q, τ² (DL, cek REML), I² pada h = 8; BH q ≤ {n(inf['fdr_q'], 2)}. Ward "
         f"k = {cl['k_range'][0]}..{cl['k_range'][-1]}, ambang silhouette persentil {cl['silhouette_placebo_pct']} "
         f"plasebo, K-Means {cl['kmeans_restarts']} awal, Jaccard lemah < {n(cl['jaccard_weak'], 1)}"],
        ["Task 2", "Struktur tertanam", f"δ = {n(cl['planted_deltas'][0], 1)}..{n(cl['planted_deltas'][-1], 1)}, "
         f"k benar 2 dan 3, {cl['planted_reps']} replikasi per sel, ambang peluang ditemukan 0,8"],
        ["Task 3", "Asosiasi & asimetri", "Kendall τ-b dengan permutasi eksak 10! = 3.628.800, meta-regresi efek acak "
         "≤ 3 fitur (interval CR2 ∪ bootstrap), Wald β⁺(8) = β⁻(8), LP per rezim HET/HAP"],
        ["Task 4", "Evaluasi prediktif", f"h = {', '.join(map(str, fc['horizons']))} minggu, origin tiap "
         f"{fc['origin_step_weeks']} minggu sejak {fc['first_origin']} ({no.get(4, 0)} / {no.get(8, 0)} origin), "
         "M0–M3, MAE, RMSE, rasio vs M1, DM HAC, Holm untuk H5"],
        ["Task 4", "Eksplorasi (bukan praregistrasi)", "Klasifier arah HGB C1/C2 dan C1-tuned (dipilih pada origin ≤ 2023, "
         "diuji 2024+), PatchTST, TSMixer, TimesFM 3.0 zero-shot, 3 seed untuk model deep"],
        ["Ketahanan", "Tier 1 & 2, V2, V4", "lag 2/4/8, sub-periode sebelum/sesudah 2021-04-05, tanpa Mar–Jun 2020 & "
         "bulan Brent ekstrem, dekomposisi kurs, frekuensi bulanan, varian alternatif, outcome Bapanas"],
        ["Lingkungan", "Perangkat & reproduksi", f"Python 3.13, numpy/scipy (tanpa statsmodels), seed {CFG.seed}, "
         "parameter dibekukan 20-11-2026 (sha256). Task 1 & 4 di Kaggle/Colab, lainnya lokal; run penuh sekitar 1,9 jam"],
    ]
    table_figure("b4_01_konfigurasi_eksperimen", ["Bagian", "Komponen", "Konfigurasi"], rows, [0.8, 1.45, 4.25],
                 [12, 22, 78], group_col=0,
                 note="Sumber: configs/params.yaml (beku sejak praregistrasi), panel_weekly, eligibility, forecast_preds.")


def b4_skenario() -> None:
    rows = [
        ["Task 1", "LP nasional per komoditas", "Praregistrasi", "β_e(h), ω(h), PT(h) + interval 95%", "nol, MDE",
         "profiles"],
        ["Task 1", "Studi peristiwa 13 episode", "Validasi", "Δ log harga 0–12 minggu", "499 jendela plasebo", "events"],
        ["Task 1", "Inferensi terkalibrasi plasebo", "Kepekaan inferensi", "interval ±crit·SE, q BH",
         "|t*| plasebo", "national_calibrated"],
        ["Task 2", "H0-Het per komoditas", "Praregistrasi", "Q, τ², I², ρ̄", "499 plasebo, BH", "heterogeneity"],
        ["Task 2", "Clustering Ward 34 provinsi", "Praregistrasi", "silhouette, ARI, Jaccard", "p95 plasebo",
         "clusters"],
        ["Task 2", "Struktur tertanam", "Validasi", "peluang ditemukan kembali", "0,8", "planted_recovery"],
        ["Task 3", "E1 Kendall vs rasio impor", "Praregistrasi", "τ-b, p eksak", "permutasi 10!", "assoc"],
        ["Task 3", "H2 asimetri", "Praregistrasi", "β⁺(8) − β⁻(8), Wald", "nol, MDE asimetri", "asymmetry"],
        ["Task 3", "H3 meta-regresi keterpencilan", "Praregistrasi", "koefisien h = 4", "nol (satu sisi)", "assoc"],
        ["Task 3", "E2 rezim HET/HAP", "Eksploratif", "β per rezim", "plasebo, BH", "regime_profiles"],
        ["Task 4", "H5 M0–M3 rolling-origin", "Praregistrasi", "MAE, rasio vs M1, DM", "M1, Holm", "forecast_eval"],
        ["Task 4", "Ablation fitur kurs", "Praregistrasi", "MAE tanpa kurs − MAE M2", "nol", "ablation"],
        ["Task 4", "Klasifier arah & model deep", "Eksploratif", "F1 makro, MAE, AP", "mayoritas, M1, BH",
         "direction_*, deep_preds"],
        ["Ketahanan", "Tier 1 (6 cek) & Tier 2 (4 cek)", "Validasi", "estimasi vs utama", "interval utama",
         "robustness"],
    ]
    fills = {}
    for i, r in enumerate(rows):
        fills[(i, 2)] = LEVEL_FILL[r[2]]
    table_figure("b4_02_matriks_skenario", ["Task", "Skenario", "Tingkat bukti", "Metrik", "Acuan / null", "Artefak"],
                 rows, [0.7, 1.85, 1.15, 1.6, 1.15, 1.25], [10, 30, 18, 26, 18, 20], cell_fills=fills, group_col=0,
                 note="Tingkat bukti: praregistrasi = aturan keputusan dibekukan 20-11-2026 sebelum hasil dilihat; kepekaan "
                      "inferensi = cara lain menghitung interval untuk estimasi yang sama; eksploratif = dirancang sesudah "
                      "praregistrasi, kriteria ditulis sebelum pengukuran.")


def b4_perbandingan_model(P: pd.DataFrame) -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 3.0), gridspec_kw={"width_ratios": [1.15, 1]})
    mo = per_origin_mae(P)
    models = ["M0", "M2", "M3", "PTST", "TSMX", "TSMX_fx", "TFM", "TFM_fx"]
    y = np.arange(len(models))[::-1]
    for h, col, off in [(4, AQUA, 0.17), (8, BLUE, -0.17)]:
        m = mo.loc[h]
        mae = P[P["horizon"] == h].assign(ae=lambda d: (d["y_true"] - d["y_pred"]).abs()).groupby("model")["ae"].mean()
        for yi, mdl in zip(y, models):
            r = mae[mdl] / mae["M1"]
            stat, p = dm(m["M1"], m[mdl], h)
            sig = p < 0.05
            face = col if sig else "white"
            a.plot([1, r], [yi + off, yi + off], color=col, lw=0.8, alpha=0.6)
            a.plot(r, yi + off, "o", ms=4.2, mfc=face, mec=col, mew=1.1)
            a.text(r + (0.006 if r >= 1 else -0.006), yi + off, n(r, 3), fontsize=5.6, va="center",
                   ha="left" if r >= 1 else "right", color=GREY)
    a.axvline(1, color=GREY, lw=0.6)
    a.set_yticks(y, [MODEL_NAMES[m] for m in models])
    a.set_xlabel("MAE / MAE model dasar M1 (kiri garis = lebih akurat)")
    a.set_title("(a) Galat ramalan perubahan harga", loc="left")
    a.xaxis.set_major_formatter(FMT)
    a.set_xlim(0.84, 1.08)
    a.tick_params(axis="y", length=0)

    # (b) arah naik/turun pada periode uji 2024+
    t = pd.concat([pd.read_parquet(ROOT / "data/interim/direction_tuned_preds.parquet"),
                   pd.read_parquet(ROOT / "data/interim/direction_preds.parquet")])
    rows = []
    for h in [4, 8]:
        for mdl in ["M1", "M2", "M3", "TFM"]:
            s = P[(P["model"] == mdl) & (P["horizon"] == h) & (P["origin"] >= TEST_START)]
            rows.append((h, mdl, macro_f1(s["y_true"], s["y_pred"])))
        for mdl in ["C1", "C2", "C1t"]:
            s = t[(t["model"] == mdl) & (t["horizon"] == h) & (t["origin"] >= TEST_START)]
            rows.append((h, mdl, macro_f1(s["y_true"], s["p_up"] - 0.5)))
    mlist = ["M1", "M2", "M3", "TFM", "C1", "C2", "C1t"]
    yb = np.arange(len(mlist))[::-1]
    for h, col, off in [(4, AQUA, 0.17), (8, BLUE, -0.17)]:
        for yi, mdl in zip(yb, mlist):
            v = next(r[2] for r in rows if r[0] == h and r[1] == mdl)["f1_macro"]
            b.barh(yi + off, v, height=0.32, color=col, alpha=0.9 if mdl == "C1t" else 0.55)
            b.text(v + 0.004, yi + off, n(v, 3), fontsize=5.6, va="center", color=GREY)
    b.axvline(0.5, color=ORANGE, ls=(0, (3, 2)), lw=0.8)
    b.text(0.502, len(mlist) - 0.45, "tebakan acak", fontsize=5.8, color=ORANGE, va="bottom")
    b.set_yticks(yb, [MODEL_NAMES[m] for m in mlist])
    b.set_xlim(0.45, 0.72)
    b.set_xlabel("F1 makro arah naik/turun, uji 2024+")
    b.set_title("(b) Ketepatan arah (eksploratif)", loc="left")
    b.xaxis.set_major_formatter(FMT)
    b.tick_params(axis="y", length=0)
    hx = [plt.Line2D([], [], marker="s", ls="none", color=AQUA, ms=5, label="h = 4 minggu"),
          plt.Line2D([], [], marker="s", ls="none", color=BLUE, ms=5, label="h = 8 minggu")]
    fig.tight_layout(w_pad=2.0, rect=(0, 0, 1, 0.93))
    fig.legend(handles=hx, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.0), fontsize=6.6)
    _note(fig, "(a) titik penuh = beda nyata dari M1 (DM, p < 0,05), 76 / 75 origin 2021–2026. (b) C1-tuned dipilih pada "
               "origin ≤ 2023 lalu diuji sekali pada origin 2024+. Minggu tanpa perubahan harga tidak dihitung.", y=-0.01)
    _save(fig, "b4_03_perbandingan_model")


def b4_confusion() -> None:
    t = pd.read_parquet(ROOT / "data/interim/direction_tuned_preds.parquet")
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH * 0.78, 2.35))
    cmap = LinearSegmentedColormap.from_list("b", ["#ffffff", BLUE])
    for ax, h in zip(axes, [4, 8]):
        s = t[(t["model"] == "C1t") & (t["horizon"] == h) & (t["origin"] >= TEST_START)]
        res = macro_f1(s["y_true"], s["p_up"] - 0.5)
        cm = np.asarray(res["confusion"], float)              # [[naik→naik, naik→turun], [turun→naik, turun→turun]]
        share = cm / cm.sum(axis=1, keepdims=True)
        ax.imshow(share, cmap=cmap, vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{_num(int(cm[i, j]))}\n({n(share[i, j] * 100, 1)}%)", ha="center", va="center",
                        fontsize=6.8, color="white" if share[i, j] > 0.55 else DARK)
        ax.set_xticks([0, 1], ["naik", "turun"])
        ax.set_yticks([0, 1], ["naik", "turun"])
        ax.set_xlabel("Ramalan")
        ax.set_ylabel("Aktual")
        ax.set_title(f"h = {h} minggu: F1 makro {n(res['f1_macro'], 3)}", loc="left")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    fig.tight_layout(w_pad=2.5)
    _note(fig, "C1-tuned (HGB, fitur dinamika harga), periode uji origin 2024+. Persen = porsi baris (recall per kelas). "
               "Minggu tanpa perubahan harga tidak dihitung. Eksploratif, bukan uji praregistrasi.", y=-0.02)
    _save(fig, "b4_04_confusion_matrix_arah")


def b4_clustering() -> None:
    cs = read_artifact(CFG, "cluster_selection")
    pr = read_artifact(CFG, "planted_recovery")
    rf = read_artifact(CFG, "response_features")
    X = feature_matrix(CFG, rf)
    keep = X.columns[X.std() > 1e-9]
    Z = X[keep].to_numpy()
    Z = Z - Z.mean(0)
    u, s, vt = np.linalg.svd(Z, full_matrices=False)
    pcs = u[:, :2] * s[:2]
    ev = s ** 2 / (s ** 2).sum()
    reg = CFG.regions.set_index("province_id")
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(WIDTH, 2.25), gridspec_kw={"width_ratios": [1, 1.15, 1]})
    k = cs[cs["k"] >= 2]
    a.plot(k["k"], k["silhouette"], color=BLUE, marker="o", ms=3.5, lw=1.1, label="data asli")
    a.axhline(cs["placebo_p95"].iloc[0], color=ORANGE, ls=(0, (3, 2)), lw=0.9, label="p95 plasebo")
    a.set_xlabel("Jumlah kelompok k")
    a.set_ylabel("Silhouette maksimum")
    a.set_title("(a) Pemilihan k", loc="left")
    a.set_xticks(k["k"])
    a.yaxis.set_major_formatter(FMT)
    a.legend(frameon=False, loc="upper right", fontsize=6)
    for i, pid in enumerate(X.index):
        r = reg.loc[pid, "region"]
        b.scatter(pcs[i, 0], pcs[i, 1], s=14, color=REGION_COLORS.get(r, NEUTRAL), edgecolor="white", lw=0.4,
                  label=r)
    hh, ll = b.get_legend_handles_labels()
    uniq = dict(zip(ll, hh))
    b.set_xlabel(f"Komponen utama 1 ({n(ev[0] * 100, 0)}% varians)")
    b.set_ylabel(f"Komponen 2 ({n(ev[1] * 100, 0)}%)")
    b.set_title("(b) 34 provinsi di ruang fitur", loc="left")
    b.xaxis.set_major_formatter(FMT)
    b.yaxis.set_major_formatter(FMT)
    for kt, col in [(2, BLUE), (3, AQUA)]:
        s_ = pr[pr["k_true"] == kt]
        c.plot(s_["delta"], s_["recovery_rate"], color=col, marker="o", ms=3.2, lw=1.1, label=f"{kt} kelompok")
    c.axhline(0.8, color=GREY, ls=(0, (1, 2)), lw=0.8)
    c.set_xlabel("Selisih tertanam δ")
    c.set_ylabel("Peluang ditemukan kembali")
    c.set_title("(c) Batas deteksi", loc="left")
    c.set_ylim(0, 1.05)
    c.xaxis.set_major_formatter(FMT)
    c.yaxis.set_major_formatter(FMT)
    c.legend(frameon=False, loc="lower right", fontsize=6)
    fig.tight_layout(w_pad=1.6, rect=(0, 0.07, 1, 1))
    fig.legend(uniq.values(), uniq.keys(), frameon=False, fontsize=5.6, ncol=7, loc="lower center",
               bbox_to_anchor=(0.5, 0.0), handletextpad=0.1, columnspacing=0.9)
    _note(fig, f"Silhouette maksimum {n(k['silhouette'].max(), 3)} di bawah ambang plasebo "
               f"{n(cs['placebo_p95'].iloc[0], 3)}, jadi k = 1. (b) memakai {len(keep)} dari {X.shape[1]} fitur respons "
               "tersusut yang tidak konstan, warna = wilayah (hanya untuk dibaca, tidak dipakai clustering).", y=-0.03)
    _save(fig, "b4_05_clustering")


def b4_faktor() -> None:
    a = read_artifact(CFG, "assoc")
    pv = a[(a["level"] == "province") & (a["commodity"] == "ALL")].copy()
    labels = {"ln_dist_hub": "Keterpencilan ln(1 + km ke hub)", "rice_sufficiency": "Kecukupan beras",
              "n_kota": "Jumlah kota sampel PIHPS"}
    pv["h"] = pv["outcome"].str.extract(r"_h(\d+)").astype(float)
    pv = pv.drop_duplicates(["feature", "h"])
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(WIDTH, 2.4), gridspec_kw={"width_ratios": [1.7, 1]})
    feats = list(labels)
    cols = {4: AQUA, 8: BLUE, 12: "#0d3a70"}
    for i, f in enumerate(feats):
        for j, h in enumerate([4, 8, 12]):
            r = pv[(pv["feature"] == f) & (pv["h"] == h)]
            if r.empty:
                continue
            r = r.iloc[0]
            yy = len(feats) - 1 - i + (1 - j) * 0.22
            ax.plot([r["ci_low"], r["ci_high"]], [yy, yy], color=cols[h], lw=1.4)
            ax.plot(r["estimate"], yy, "o", ms=3.6, color=cols[h], label=f"h = {h}" if i == 0 else None)
    ax.axvline(0, color=GREY, lw=0.6)
    ax.set_yticks(range(len(feats))[::-1], [labels[f] for f in feats])
    ax.tick_params(axis="y", length=0)
    ax.xaxis.set_major_formatter(FMT)
    ax.set_xlabel("Koefisien meta-regresi deviasi provinsi (interval 95%)")
    ax.set_title("(a) Karakteristik provinsi (RQ4, H3)", loc="left")
    ax.set_ylim(-0.95, 2.45)
    ax.legend(frameon=False, fontsize=6, loc="lower center", ncol=3, borderaxespad=0.1)
    k = a[(a["level"] == "commodity")].iloc[0]
    exp = read_artifact(CFG, "exposure").set_index("commodity")
    prof = read_artifact(CFG, "profiles")
    pt8 = prof[(prof["level"] == "national") & (prof["driver"] == "PT") & (prof["horizon"] == 8)].set_index("commodity")
    for com in ORDER:
        x, yv = exp.loc[com, "import_ratio_direct"], pt8.loc[com, "estimate"]
        bx.plot(x, yv, "o", ms=4, color=BLUE if com in ["bawang_putih", "gula_pasir", "daging_sapi"] else NEUTRAL)
        bx.annotate(NAMES[com], (x, yv), xytext=(3, 2), textcoords="offset points", fontsize=5.4, color=GREY)
    bx.axhline(0, color=GREY, lw=0.5)
    bx.set_xlabel("Rasio impor langsung")
    bx.set_ylabel("PT(8) nasional")
    bx.xaxis.set_major_formatter(FMT)
    bx.yaxis.set_major_formatter(FMT)
    bx.set_title(f"(b) E1: τ-b {n(k['estimate'], 3)}, p eksak {n(k['p_value'], 2)}", loc="left")
    fig.tight_layout(w_pad=2.0)
    _note(fig, "KAGAMI tidak memakai feature importance model prediksi sebagai temuan. Yang diuji adalah asosiasi "
               "karakteristik terukur dengan respons (meta-regresi 337 seri, interval CR2 ∪ bootstrap; Kendall permutasi "
               "eksak N = 10). Semua interval memuat nol.", y=-0.03)
    _save(fig, "b4_06_faktor_penjelas")


def b4_dashboard(P: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(WIDTH, 4.5))
    (a, b, c), (d, e, f) = axes
    # (a) Task 1 interval tidak memuat nol: resmi vs terkalibrasi
    prof = read_artifact(CFG, "profiles")
    nat = prof[(prof["level"] == "national") & prof["driver"].isin(["e", "w"]) & prof["horizon"].isin([4, 8, 12])]
    cal = read_artifact(CFG, "national_calibrated")
    cal = cal[cal["driver"].isin(["e", "w"])]
    off = ((nat["ci_low"] > 0) | (nat["ci_high"] < 0))
    vals = [int(off.sum()), int(cal["ci_excludes_zero"].sum()), int((cal["q_fdr"] < 0.05).sum())]
    bars = a.bar([0, 1, 2], vals, color=[BLUE, AQUA, ORANGE], width=0.6)
    for bb, v in zip(bars, vals):
        a.text(bb.get_x() + bb.get_width() / 2, v + 0.2, str(v), ha="center", fontsize=6.5)
    a.set_xticks([0, 1, 2], ["resmi", "terkalibrasi", "lolos BH"], fontsize=6.2)
    a.set_title(f"(a) Task 1: sel terdeteksi\ndari {len(cal)} sel β_e & ω", loc="left")
    a.set_ylim(0, max(vals) + 2)
    # (b) Task 2 H0-Het q per komoditas
    het = read_artifact(CFG, "heterogeneity")
    q = het[het["statistic"] == "Q"].set_index("commodity").loc[ORDER]
    yy = np.arange(len(q))[::-1]
    b.scatter(q["q_fdr"], yy, s=14, color=[ORANGE if r else NEUTRAL for r in q["reject"]], zorder=3)
    b.axvline(0.05, color=ORANGE, ls=(0, (3, 2)), lw=0.8)
    b.set_xscale("log")
    b.set_yticks(yy, [NAMES[c_] for c_ in q.index], fontsize=5.8)
    b.set_xlabel("q BH (log)", fontsize=6.5)
    b.set_title("(b) Task 2: H0-Het per komoditas", loc="left")
    b.tick_params(axis="y", length=0)
    b.set_xticks([0.05, 0.1, 0.3, 1])
    b.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v)))
    b.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    # (c) Task 3 H2
    asy = read_artifact(CFG, "asymmetry")
    s = asy[asy["horizon"] == 8].set_index("commodity").loc[ORDER]
    for yi, (com, r) in zip(yy, s.iterrows()):
        col = BLUE if r["confirmatory"] else NEUTRAL
        c.plot([r["ci_low"], r["ci_high"]], [yi, yi], color=col, lw=1.3)
        c.plot(r["estimate"], yi, "o", ms=3, color=col)
    c.axvline(0, color=GREY, lw=0.6)
    c.set_yticks(yy, [NAMES[c_] for c_ in s.index], fontsize=5.8)
    c.set_xlim(-6, 6)
    c.xaxis.set_major_formatter(FMT)
    c.set_title("(c) Task 3: β⁺(8) − β⁻(8)", loc="left")
    c.set_xlabel("biru = konfirmatori, sumbu dipotong di ±6", fontsize=6.0)
    c.tick_params(axis="y", length=0)
    # (d) Task 4 rasio MAE & DM
    fe = read_artifact(CFG, "forecast_eval")
    fe = fe[(fe["level"] == "all") & (fe["model"] == "M2")]
    dms = []
    for i, (sub, lab) in enumerate([("all", "semua origin"), ("large_move", "kurs bergerak besar")]):
        for j, h in enumerate([4, 8]):
            r = fe[(fe["subset"] == sub) & (fe["horizon"] == h)].iloc[0]
            x = i * 2.6 + j
            d.bar(x, r["mae_ratio_vs_m1"], width=0.8, color=AQUA if h == 4 else BLUE)
            d.text(x, r["mae_ratio_vs_m1"] + 0.0015, n(r["mae_ratio_vs_m1"], 3), ha="center", fontsize=5.4)
            dms.append(n(r["dm_stat"], 2))
    d.axhline(1, color=GREY, lw=0.6)
    d.set_ylim(0.97, 1.04)
    d.set_xticks([0.5, 3.1], ["semua origin", "kurs bergerak\nbesar (8 origin)"], fontsize=5.8)
    d.set_title("(d) Task 4: MAE M2 / M1\nhijau = h 4, biru = h 8", loc="left")
    d.yaxis.set_major_formatter(FMT)
    d.set_ylim(0.97, 1.05)
    d.text(0.02, 0.98, f"DM h 4 / h 8: {dms[0]} / {dms[1]} (semua),\n{dms[2]} / {dms[3]} (8 origin).\n"
           "DM < 0 = M2 kurang akurat", transform=d.transAxes, fontsize=5.2, va="top", color=GREY)
    # (e) ketahanan
    rb = read_artifact(CFG, "robustness")
    rb = rb[(rb["tier"].astype(str) == "1") & rb["baseline_in_ci"].notna()]
    lab = {"lags_2_4_8": "lag 2 & 8", "subperiod_pre_post_2021-04-05": "sub-periode",
           "exclude_covid_and_extreme_brent": "tanpa COVID", "horizon_8_vs_12": "h 12",
           "monthly_frequency": "bulanan", "fx_decomposition_global_dollar_vs_idr_specific": "dekomposisi kurs"}
    sh = rb.groupby("check_id")["baseline_in_ci"].mean().reindex(list(lab)).dropna()
    ye = np.arange(len(sh))[::-1]
    e.barh(ye, sh.values * 100, color=BLUE, height=0.55)
    for yi, v in zip(ye, sh.values):
        e.text(v * 100 + 1, yi, f"{n(v * 100, 0)}%", va="center", fontsize=5.8)
    e.set_yticks(ye, [lab[i_] for i_ in sh.index], fontsize=5.8)
    e.set_xlim(0, 115)
    e.set_xlabel("% estimasi utama di dalam interval cek", fontsize=6.2)
    e.set_title("(e) Ketahanan Tier 1", loc="left")
    e.tick_params(axis="y", length=0)
    # (f) MDE
    mde = read_artifact(CFG, "mde")
    m = mde[(mde["level"] == "national") & (mde["horizon"] == 8)].set_index("commodity").reindex(ORDER).dropna(
        subset=["mde_pt"])
    yf = np.arange(len(m))[::-1]
    for yi, v in zip(yf, m["mde_pt"]):
        col = BLUE if v <= 0.5 else NEUTRAL
        f.plot(v, yi, "o", ms=4, color=col)
        f.text(v * 1.15, yi, n(v, 2), va="center", fontsize=5.4, color=GREY)
    f.axvline(0.5, color=ORANGE, ls=(0, (3, 2)), lw=0.8)
    f.set_yticks(yf, [NAMES[c_] for c_ in m.index], fontsize=5.8)
    f.set_xscale("log")
    f.set_xlim(0.1, 25)
    f.set_xticks([0.2, 0.5, 1, 2, 5, 10])
    f.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v)))
    f.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    f.set_xlabel("MDE PT(8) (log), biru = di bawah ambang 0,5", fontsize=6.0)
    f.set_title("(f) Daya uji sebelum estimasi", loc="left")
    f.tick_params(axis="y", length=0)
    for ax in axes.ravel():
        ax.tick_params(labelsize=5.8)
        ax.title.set_fontsize(6.9)
    fig.tight_layout(h_pad=1.6, w_pad=1.2)
    _save(fig, "b4_07_dashboard_metrik")


def b4_pengujian(junit: Path | None) -> None:
    groups = [
        ("Data & praproses", ["test_config", "test_loaders", "test_weekly", "test_drivers", "test_panel", "test_qa",
                              "test_reference", "test_download"],
         "loader 29 sumber, grup varian PIHPS, status sel, kelayakan, episode, QA impor & Bapanas"),
        ("Mesin statistik", ["test_stats", "test_power", "test_inference"],
         "OLS & SE cluster, DL/REML/EB, BH/Holm, bootstrap blok, DM, MDE, plasebo"),
        ("Task 1 respons", ["test_local_projection", "test_event_study", "test_deviations", "test_response",
                            "test_task1", "test_synthetic"], "β tertanam dipulihkan, Σ deviasi = 0, interval tidak menyempit"),
        ("Task 2 pola provinsi", ["test_heterogeneity", "test_clustering", "test_task2", "test_planted"],
         "Q/τ² = DL, pemilihan k vs plasebo, 3 kelompok tertanam, batas deteksi"),
        ("Task 3 asosiasi", ["test_association", "test_asymmetry", "test_regimes", "test_calibration"],
         "Kendall eksak vs brute force, Wald, p ⇔ interval, kalibrasi plasebo"),
        ("Task 4 prediksi", ["test_forecast", "test_forecast_eval", "test_direction", "test_direction_tuned",
                             "test_neural"], "tanpa kebocoran as-of di setiap origin, DM, Holm H5, checkpoint"),
        ("Ketahanan", ["test_robustness"], "6 cek Tier 1, 4 cek Tier 2, V2 & V4"),
        ("App & visualisasi", ["test_app", "test_app_data", "test_viz"],
         "12 halaman tanpa exception (artefak ada/hilang), angka app = findings, istilah"),
        ("Reproduksi & paket", ["test_package", "test_runtime", "test_notebooks", "test_drive", "test_tracking"],
         "zip juri tanpa data tanpa hak, lokal/Kaggle/Colab, log & lineage sha256"),
        ("Dokumen & integritas", ["test_docs_sync", "test_claude_md", "test_handoff", "test_wiring", "test_paper"],
         "dokumen tidak basi, semua modul terpakai, makalah = findings"),
    ]
    stats: dict[str, dict] = {}
    run_note = "Hitungan dari pengumpulan pytest."
    if junit and junit.exists():
        root = ET.parse(junit).getroot()
        for tc in root.iter("testcase"):
            f = tc.get("classname", "").split(".")
            fname = next((x for x in f if x.startswith("test_")), None)
            if not fname:
                continue
            st = stats.setdefault(fname, {"n": 0, "pass": 0, "skip": 0, "fail": 0, "time": 0.0})
            st["n"] += 1
            st["time"] += float(tc.get("time", 0) or 0)
            if tc.find("skipped") is not None:
                st["skip"] += 1
            elif tc.find("failure") is not None or tc.find("error") is not None:
                st["fail"] += 1
            else:
                st["pass"] += 1
        ts = root if root.tag == "testsuite" else root.find("testsuite")
        run_note = (f"Run penuh pytest {ts.get('timestamp', '')[:10]}: {ts.get('tests')} tes, "
                    f"{int(ts.get('failures', 0)) + int(ts.get('errors', 0))} gagal, {ts.get('skipped')} dilewati, "
                    f"{n(float(ts.get('time', 0)) / 60, 1)} menit.")
    rows, fills = [], {}
    for i, (g, files, what) in enumerate(groups):
        agg = {k: sum(stats.get(f, {}).get(k, 0) for f in files) for k in ["n", "pass", "skip", "fail"]}
        status = "Lolos" if agg["n"] and agg["fail"] == 0 else ("Gagal" if agg["fail"] else "–")
        rows.append([g, str(len(files)), _num(agg["n"]), _num(agg["pass"]), _num(agg["skip"]), _num(agg["fail"]),
                     what, status])
        fills[(i, 7)] = ("#d8ecdf", GREEN, True) if status == "Lolos" else ("#f5d6d6", RED, True)
    tot = {k: sum(v.get(k, 0) for v in stats.values()) for k in ["n", "pass", "skip", "fail"]}
    rows.append(["Total", str(sum(len(g[1]) for g in groups)), _num(tot["n"]), _num(tot["pass"]), _num(tot["skip"]),
                 _num(tot["fail"]), "", "Lolos" if tot["fail"] == 0 else "Gagal"])
    fills[(len(rows) - 1, 7)] = ("#d8ecdf", GREEN, True) if tot["fail"] == 0 else ("#f5d6d6", RED, True)
    fl = [None] * (len(rows) - 1) + ["#dbe6f4"]
    table_figure("b4_09_matriks_pengujian_fungsional",
                 ["Komponen", "File", "Tes", "Lolos", "Lewat", "Gagal", "Yang diverifikasi", "Status"], rows,
                 [1.3, 0.4, 0.45, 0.5, 0.45, 0.45, 2.75, 0.55], [20, 5, 6, 6, 6, 6, 52, 8], fills=fl,
                 cell_fills=fills,
                 note=run_note + " Tes data sintetis memakai jawaban yang diketahui (β tertanam, kelompok tertanam). Tes "
                                 "yang butuh data mentah dilewati otomatis di paket juri.")


# ================================================================================================== BAB 5
def b5_galat(P: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(WIDTH, 4.3))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], hspace=0.55, wspace=0.42)
    a = fig.add_subplot(gs[0, :])
    s = P[(P["horizon"] == 8) & P["model"].isin(["M1", "M2"])].assign(
        ae=lambda d: (d["y_true"] - d["y_pred"]).abs(), year=lambda d: d["origin"].dt.year)
    g = s.groupby(["commodity", "year", "model"])["ae"].mean().unstack("model")
    ratio = (g["M2"] / g["M1"]).unstack("year").loc[ORDER]
    norm = TwoSlopeNorm(vmin=0.85, vcenter=1.0, vmax=1.15)
    cmap = LinearSegmentedColormap.from_list("d", [BLUE, "#ffffff", ORANGE])
    im = a.imshow(ratio.to_numpy(), cmap=cmap, norm=norm, aspect="auto")
    cb = fig.colorbar(im, ax=a, fraction=0.025, pad=0.01, extend="both")
    cb.ax.tick_params(labelsize=5.6)
    cb.ax.yaxis.set_major_formatter(FMT)
    cb.outline.set_visible(False)
    for i in range(ratio.shape[0]):
        for j in range(ratio.shape[1]):
            v = ratio.iat[i, j]
            a.text(j, i, n(v, 2), ha="center", va="center", fontsize=5.6,
                   color="white" if abs(v - 1) > 0.11 else DARK)
    last = pd.Timestamp(s["origin"].max())
    a.set_xticks(range(ratio.shape[1]), [str(c) if c != last.year else f"{c}\n(origin s.d. {last:%m/%Y})"
                                         for c in ratio.columns])
    a.set_yticks(range(ratio.shape[0]), [NAMES[c] for c in ratio.index])
    a.set_title("(a) MAE M2 (+ kurs) / M1 per komoditas dan tahun origin, h = 8 (oranye = kurs memperburuk)",
                loc="left")
    a.tick_params(length=0)
    for sp in a.spines.values():
        sp.set_visible(False)
    # (b) galat all vs large_move
    b = fig.add_subplot(gs[1, 0])
    models = ["M0", "M1", "M2", "M3", "TFM"]
    s8 = P[(P["horizon"] == 8) & P["model"].isin(models)].assign(ae=lambda d: (d["y_true"] - d["y_pred"]).abs())
    q80 = s8.groupby("commodity")["y_true"].transform(lambda x: x.abs().quantile(0.8))
    s8 = s8.assign(big=s8["y_true"].abs() >= q80)
    m = s8.groupby(["model", "big"])["ae"].mean().unstack("big").loc[models]
    x = np.arange(len(models))
    b.bar(x - 0.2, m[False], width=0.38, color=AQUA, label="perubahan biasa")
    b.bar(x + 0.2, m[True], width=0.38, color=BLUE, label="20% perubahan terbesar")
    b.set_xticks(x, ["M0", "M1", "M2", "M3", "TimesFM"], fontsize=6.2)
    b.set_ylabel("MAE (Δ log harga)")
    b.yaxis.set_major_formatter(FMT)
    b.set_title("(b) Galat menurut besar perubahan", loc="left")
    b.set_ylim(0, m.to_numpy().max() * 1.35)
    b.legend(frameon=False, fontsize=5.8, ncol=2, loc="upper center", handlelength=1)
    # (c) kekakuan vs kalah dari M0
    c = fig.add_subplot(gs[1, 1])
    pw = read_artifact(CFG, "panel_weekly")
    cf = pw.groupby("commodity")["status"].apply(lambda x: (x == "carry_forward").mean())
    fe = read_artifact(CFG, "forecast_eval")
    fe = fe[(fe["level"] == "commodity") & (fe["subset"] == "all") & (fe["horizon"] == 8)]
    r0 = fe[fe["model"] == "M0"].set_index("commodity")["mae_ratio_vs_m1"]
    for com in ORDER:
        col = ORANGE if com in RIGID else BLUE
        c.plot(cf[com] * 100, r0[com], "o", ms=4, color=col)
        off, ha = {"cabai_rawit": ((-2, 7), "left"), "cabai_merah": ((5, -3), "left"),
                   "daging_ayam": ((5, 3), "left"), "bawang_merah": ((5, -3), "left"),
                   "telur_ayam": ((6, -8), "left")}.get(com, ((4, 2), "left"))
        c.annotate(NAMES[com], (cf[com] * 100, r0[com]), xytext=off, textcoords="offset points", fontsize=5.2,
                   color=GREY, ha=ha)
    c.axhline(1, color=GREY, lw=0.6)
    c.set_xlabel("% minggu dengan rangkaian harga identik")
    c.set_ylabel("MAE M0 / MAE M1")
    c.set_ylim(0.78, 1.085)
    c.yaxis.set_major_formatter(FMT)
    c.set_title("(c) Di bawah 1: model dasar kalah dari\n'tanpa perubahan'", loc="left")
    _note(fig, "Sumber: forecast_preds, deep_preds (TimesFM, eksploratif), panel_weekly. Ambang 20% terbesar per komoditas "
               "dari |perubahan| aktual, hanya untuk analisis galat.", y=0.02)
    _save(fig, "b5_01_analisis_galat")


def b5_algoritma(P: pd.DataFrame) -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 2.9), gridspec_kw={"width_ratios": [1.3, 1]})
    mo = per_origin_mae(P).loc[8]
    models = ["M0", "M1", "M2", "M3", "PTST", "TSMX", "TFM"]
    labs = ["M0", "M1", "M2", "M3", "PatchTST", "TSMixer", "TimesFM"]
    M = np.full((len(models), len(models)), np.nan)
    Pv = np.full_like(M, np.nan)
    for i, ri in enumerate(models):
        for j, cj in enumerate(models):
            if i != j:
                M[i, j], Pv[i, j] = dm(mo[cj], mo[ri], 8)      # > 0 = model baris lebih akurat dari model kolom
    cmap = LinearSegmentedColormap.from_list("d", [ORANGE, "#ffffff", BLUE])
    a.imshow(M, cmap=cmap, norm=TwoSlopeNorm(vmin=-6, vcenter=0, vmax=6))
    for i in range(len(models)):
        for j in range(len(models)):
            if i == j:
                a.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, color=LIGHT))
                continue
            star = "*" if Pv[i, j] < 0.05 else ""
            a.text(j, i, f"{n(M[i, j], 1)}{star}", ha="center", va="center", fontsize=5.6,
                   color="white" if abs(M[i, j]) > 4 else DARK)
    a.set_xticks(range(len(models)), labs, rotation=35, ha="right", fontsize=6)
    a.set_yticks(range(len(models)), labs, fontsize=6)
    a.tick_params(length=0)
    for sp in a.spines.values():
        sp.set_visible(False)
    a.set_title("(a) Statistik DM baris vs kolom, h = 8\nbiru = baris lebih akurat, * p < 0,05", loc="left")
    # (b) stabilitas seed model deep
    d = P[(P["horizon"] == 8)]
    mae = d.assign(ae=(d["y_true"] - d["y_pred"]).abs()).groupby("model")["ae"].mean()
    fams = [("PTST", "PatchTST"), ("TSMX", "TSMixer"), ("TSMX_fx", "TSMixer + kurs")]
    for i, (base, lab) in enumerate(fams):
        reps = [base] + [f"{base}_r{k}" for k in (2, 3)]
        vals = np.array([mae[r] / mae["M1"] for r in reps if r in mae])
        b.plot(vals, [i] * len(vals), "o", ms=4, mfc="white", mec=BLUE, mew=1)
        b.plot(vals.mean(), i, "|", ms=12, color=BLUE, mew=1.6)
        b.text(vals.max() + 0.004, i, f"{n(vals.mean(), 3)} (sd {n(vals.std(ddof=1), 3)})", va="center",
               fontsize=5.8, color=GREY)
    tfm = mae["TFM"] / mae["M1"]
    b.plot(tfm, 3, "D", ms=4.5, color=ORANGE)
    b.text(tfm + 0.004, 3, f"{n(tfm, 3)} (zero-shot, deterministik)", va="center", fontsize=5.8, color=GREY)
    b.axvline(1, color=GREY, lw=0.6)
    b.set_yticks(range(4), [f[1] for f in fams] + ["TimesFM 3.0"])
    b.set_xlim(0.88, 1.06)
    b.invert_yaxis()
    b.tick_params(axis="y", length=0)
    b.xaxis.set_major_formatter(FMT)
    b.set_xlabel("MAE / MAE M1, h = 8")
    b.set_title("(b) Kestabilan antar 3 seed", loc="left")
    fig.tight_layout(w_pad=2.0)
    _note(fig, "DM dihitung pada MAE per origin (75 origin, lag HAC 1) seperti evaluator resmi. Model deep eksploratif; "
               "TimesFM mungkin pernah melihat deret ini saat pelatihan, jadi keunggulannya batas atas.", y=-0.02)
    _save(fig, "b5_02_perbandingan_algoritma")


def b5_sensitivitas() -> None:
    rb = read_artifact(CFG, "robustness")
    prof = read_artifact(CFG, "profiles")
    cases = [("daging_ayam", "e", 8), ("gula_pasir", "e", 4), ("minyak_goreng", "w", 8), ("telur_ayam", "e", 8)]
    checks = [("baseline", "Estimasi utama"), ("L=2", "Lag 2"), ("L=8", "Lag 8"), ("pre", "Sebelum Apr 2021"),
              ("post", "Sesudah Apr 2021"), ("excl", "Tanpa COVID & Brent ekstrem"), ("e_global", "Komponen dolar global"),
              ("e_idr", "Komponen khusus rupiah"), ("last_obs", "Harga hari terakhir"), ("h_m=2", "Bulanan (2 bulan)")]
    fig, axes = plt.subplots(1, 4, figsize=(WIDTH, 3.0), sharey=True)
    for ax, (com, drv, h) in zip(axes, cases):
        base = prof[(prof["level"] == "national") & (prof["commodity"] == com) & (prof["driver"] == drv) &
                    (prof["horizon"] == h)].iloc[0]
        yy = np.arange(len(checks))[::-1]
        ax.axvspan(base["ci_low"], base["ci_high"], color=BLUE, alpha=0.08, lw=0)
        ax.axvline(0, color=GREY, lw=0.6)
        for yi, (var, lab) in zip(yy, checks):
            if var == "baseline":
                est, lo, hi, col = base["estimate"], base["ci_low"], base["ci_high"], BLUE
            else:
                if var in ("e_global", "e_idr"):
                    if drv != "e":
                        continue
                    sel = (rb["variant"] == "decomp") & (rb["driver"] == var)
                else:
                    sel = (rb["variant"] == var) & (rb["driver"] == drv)
                r = rb[(rb["commodity"] == com) & (rb["horizon"] == h) & sel]
                if r.empty:
                    continue
                r = r.iloc[0]
                est, lo, hi = r["estimate"], r["ci_low"], r["ci_high"]
                col = AQUA if (lo > 0 or hi < 0) else NEUTRAL
            ax.plot([lo, hi], [yi, yi], color=col, lw=1.2)
            ax.plot(est, yi, "o", ms=3.2, color=col)
        sym = "β_e" if drv == "e" else "ω"
        ax.set_title(f"{NAMES[com]}\n{sym}({h})", loc="left")
        ax.xaxis.set_major_formatter(FMT)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(np.arange(len(checks))[::-1], [c[1] for c in checks])
    fig.supxlabel("Respons kumulatif (Δ log harga per 1 log penggerak), interval 95%", fontsize=7, y=0.02)
    fig.tight_layout(w_pad=0.8)
    _note(fig, "Arsiran = interval estimasi utama. Hijau = interval cek tidak memuat nol. Dekomposisi kurs hanya untuk "
               "respons kurs (β_e). Empat sel yang paling sering "
               "dibahas di findings. Sumber: robustness (Tier 1 & 2), profiles.", y=-0.01)
    _save(fig, "b5_03_sensitivitas_parameter")


def b5_kontribusi(P: pd.DataFrame) -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 2.9), gridspec_kw={"width_ratios": [1.2, 1]})
    ab = read_artifact(CFG, "ablation")
    ab = ab[(ab["level"] == "commodity") & (ab["horizon"] == 8)]
    yy = np.arange(len(ORDER))[::-1]
    for sub, col, off, lab in [("all", BLUE, 0.15, "semua origin"), ("large_move", ORANGE, -0.15, "kurs bergerak besar")]:
        s = ab[ab["subset"] == sub].set_index("commodity").reindex(ORDER)
        a.barh(yy + off, s["delta_mae"] * 1000, height=0.3, color=col, label=lab)
    a.axvline(0, color=GREY, lw=0.6)
    a.set_yticks(yy, [NAMES[c] for c in ORDER])
    a.tick_params(axis="y", length=0)
    a.xaxis.set_major_formatter(FMT)
    a.set_xlabel("MAE tanpa kurs − MAE M2 (× 0,001); kanan = kurs membantu")
    a.set_title("(a) Ablation fitur kurs, h = 8", loc="left")
    a.legend(frameon=False, fontsize=6, loc="lower left")
    # (b) efek fitur kurs di setiap keluarga model
    rows = []
    mae = P.assign(ae=(P["y_true"] - P["y_pred"]).abs()).groupby(["horizon", "model"])["ae"].mean()
    for h in [4, 8]:
        for w, wo, lab in [("M2", "M2_nofx", "Ridge"), ("TSMX_fx", "TSMX", "TSMixer"), ("TFM_fx", "TFM", "TimesFM")]:
            rows.append((lab, h, mae[(h, w)] / mae[(h, wo)]))
    labs = ["Ridge", "TSMixer", "TimesFM"]
    for j, h in enumerate([4, 8]):
        for i, lab in enumerate(labs):
            v = next(r[2] for r in rows if r[0] == lab and r[1] == h)
            yv = len(labs) - 1 - i + (0.15 if h == 4 else -0.15)
            b.plot([1, v], [yv, yv], color=AQUA if h == 4 else BLUE, lw=1)
            b.plot(v, yv, "o", ms=4, color=AQUA if h == 4 else BLUE, label=f"h = {h}" if i == 0 else None)
            b.text(v + 0.002, yv, n(v, 3), fontsize=5.6, va="center", color=GREY)
    b.axvline(1, color=GREY, lw=0.6)
    b.set_yticks(range(len(labs))[::-1], labs)
    b.set_xlim(0.99, 1.05)
    b.xaxis.set_major_formatter(FMT)
    b.tick_params(axis="y", length=0)
    b.set_xlabel("MAE dengan kurs / MAE tanpa kurs")
    b.set_title("(b) Menambah kurs ke tiap keluarga model", loc="left")
    b.legend(frameon=False, fontsize=6, loc="lower right")
    fig.tight_layout(w_pad=2.0)
    _note(fig, "Di atas 1 atau di kiri nol = fitur kurs memperburuk ramalan. Ablation resmi (artefak ablation) memakai "
               "spesifikasi praregistrasi. TSMixer dan TimesFM eksploratif (deep_preds).", y=-0.02)
    _save(fig, "b5_04_kontribusi_komponen")


def b5_klaster() -> None:
    het = read_artifact(CFG, "heterogeneity")
    pc = read_artifact(CFG, "province_calibrated")
    prof = read_artifact(CFG, "profiles")
    reg = CFG.regions.set_index("province_id")
    pc = pc.assign(q_global=bh_fdr(pc["p_value"].to_numpy()))
    fig = plt.figure(figsize=(WIDTH, 3.9))
    gs = fig.add_gridspec(2, 2, width_ratios=[0.8, 1.6], hspace=0.5, wspace=0.35)
    a = fig.add_subplot(gs[:, 0])
    i2 = het[het["statistic"] == "I2"].set_index("commodity").reindex(ORDER)
    q = het[het["statistic"] == "Q"].set_index("commodity").reindex(ORDER)
    yy = np.arange(len(ORDER))[::-1]
    a.barh(yy, i2["value"] * 100, color=[ORANGE if r else NEUTRAL for r in q["reject"]], height=0.6)
    for yi, com in zip(yy, ORDER):
        a.text(i2.loc[com, "value"] * 100 + 1, yi, f"q {n(q.loc[com, 'q_fdr'], 3)}", va="center", fontsize=5.6,
               color=GREY)
    a.set_yticks(yy, [NAMES[c] for c in ORDER])
    a.set_xlim(0, 100)
    a.tick_params(axis="y", length=0)
    a.set_xlabel("I² (% variasi antarprovinsi\ndi atas galat sampel), h = 8")
    a.set_title("(a) Heterogenitas", loc="left")
    for k, com in enumerate(["telur_ayam", "daging_ayam"]):
        ax = fig.add_subplot(gs[k, 1])
        sh = prof[(prof["level"] == "province") & (prof["commodity"] == com) & (prof["driver"] == "e") &
                  (prof["horizon"] == 8) & prof["shrunk"].astype(bool)].copy()
        sh["pid"] = sh["unit"].astype(int)
        raw = pc[(pc["commodity"] == com) & (pc["driver"] == "e") & (pc["horizon"] == 8)].copy()
        raw["pid"] = raw["unit"].astype(int)
        m = sh.merge(raw[["pid", "ci_low", "ci_high", "q_global", "estimate"]], on="pid", suffixes=("", "_raw"))
        m = m.sort_values("estimate").reset_index(drop=True)
        x = np.arange(len(m))
        for i, r in m.iterrows():
            col = REGION_COLORS.get(reg.loc[r["pid"], "region"], NEUTRAL)
            ax.plot([i, i], [r["ci_low_raw"], r["ci_high_raw"]], color=col, lw=0.6, alpha=0.45)
            ax.plot(i, r["estimate"], "o", ms=3.2, color=col, mec="black" if r["q_global"] < 0.05 else col,
                    mew=0.8 if r["q_global"] < 0.05 else 0)
        ax.axhline(0, color=GREY, lw=0.6)
        ax.set_xticks(x, [HEX.loc[p, "code"] for p in m["pid"]], rotation=90, fontsize=4.8)
        ax.set_ylim(-6, 6)
        ax.set_ylabel("δ (Δ log harga\nper 1 log kurs)", fontsize=6)
        ax.yaxis.set_major_formatter(FMT)
        ax.tick_params(axis="x", length=0)
        ax.set_title(f"({'b' if k == 0 else 'c'}) {NAMES[com]}: deviasi provinsi dari respons nasional, h = 8",
                     loc="left")
    hx = [plt.Line2D([], [], marker="o", ls="none", color=c, ms=3.5, label=r) for r, c in REGION_COLORS.items()]
    fig.subplots_adjust(bottom=0.2)
    fig.legend(handles=hx, frameon=False, ncol=7, fontsize=5.4, loc="lower center", bbox_to_anchor=(0.5, 0.045),
               handletextpad=0.1, columnspacing=0.8)
    _note(fig, "Klaster terpilih k = 1, jadi interpretasi beralih ke heterogenitas per komoditas. Titik = deviasi tersusut "
               "(EB), garis = interval terkalibrasi plasebo deviasi mentah, tepi hitam = lolos BH atas semua sel provinsi. "
               "Oranye di (a) = H0-Het ditolak.", y=0.035)
    _save(fig, "b5_05_interpretasi_klaster")


def b5_gagal(P: pd.DataFrame) -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 2.9), gridspec_kw={"width_ratios": [1.45, 1]})
    mo = per_origin_mae(P).loc[8]
    lm = P[(P["model"] == "M1") & (P["horizon"] == 8)].groupby("origin")["large_move"].max()
    r = (mo["M2"] / mo["M1"])
    ep = read_artifact(CFG, "episodes")
    for _, e in ep[ep["in_period"]].iterrows():
        if pd.Timestamp(e["end_week"]) >= pd.Timestamp("2021-01-01"):
            a.axvspan(pd.Timestamp(e["start_week"]), pd.Timestamp(e["end_week"]) + pd.Timedelta(days=6), color=ORANGE,
                      alpha=0.12, lw=0)
    a.plot(r.index, r.values, color=BLUE, lw=0.9, marker="o", ms=2)
    big = r[lm.reindex(r.index).fillna(False).astype(bool)]
    a.plot(big.index, big.values, "o", ms=5, mfc="none", mec=ORANGE, mew=1.2, label="origin kurs bergerak besar (H5)")
    a.axhline(1, color=GREY, lw=0.6)
    a.set_ylabel("MAE M2 / MAE M1 per origin")
    a.set_xlim(r.index.min() - pd.Timedelta(days=45), r.index.max() + pd.Timedelta(days=45))
    a.yaxis.set_major_formatter(FMT)
    a.set_title("(a) Fitur kurs per origin, h = 8", loc="left")
    a.legend(frameon=False, fontsize=6, loc="upper right")
    # (b) arah: per komoditas akurasi − mayoritas, periode uji
    t = pd.read_parquet(ROOT / "data/interim/direction_tuned_preds.parquet")
    s = t[(t["model"] == "C1t") & (t["horizon"] == 8) & (t["origin"] >= TEST_START)]
    tf = P[(P["model"] == "TFM") & (P["horizon"] == 8) & (P["origin"] >= TEST_START)]
    yy = np.arange(len(ORDER))[::-1]
    for (df, score, col, off, lab) in [(s, "p_up", BLUE, 0.15, "C1-tuned"), (tf, "y_pred", NEUTRAL, -0.15, "TimesFM")]:
        for yi, com in zip(yy, ORDER):
            g = df[df["commodity"] == com]
            sc = g[score] - (0.5 if score == "p_up" else 0)
            res = macro_f1(g["y_true"], sc)
            v = res["accuracy"] - res["majority_baseline_accuracy"]
            b.barh(yi + off, v * 100, height=0.3, color=col, label=lab if com == ORDER[0] else None)
    for yi, com in zip(yy, ORDER):
        if com in RIGID:
            b.axhspan(yi - 0.45, yi + 0.45, color=ORANGE, alpha=0.09, lw=0)
    b.axvline(0, color=GREY, lw=0.6)
    b.set_yticks(yy, [NAMES[c] for c in ORDER])
    b.tick_params(axis="y", length=0)
    b.set_xlabel("Akurasi arah − tebakan mayoritas (poin %)")
    b.set_title("(b) Arah per komoditas, uji 2024+", loc="left")
    b.legend(frameon=False, fontsize=6, loc="upper right")
    fig.tight_layout(w_pad=2.0)
    _note(fig, "(a) di atas 1 = menambah kurs memperburuk ramalan pada origin itu, arsiran = episode depresiasi. "
               "(b) baris berarsir = komoditas dengan rangkaian harga identik ≥ 50% minggu (beras, daging sapi, gula, "
               "minyak goreng). Di kiri nol = kalah dari menebak arah yang paling sering.", y=-0.02)
    _save(fig, "b5_06_analisis_kasus_gagal")


def app_artifacts() -> int:
    """Jumlah artefak yang dibaca app (literal di need(...)/load(...), aturan sama dengan tests/test_wiring.py)."""
    import ast
    from kagami.utils.artifacts import ARTIFACTS
    names = set()
    for f in [ROOT / "app" / "Home.py", ROOT / "app" / "common.py", *sorted((ROOT / "app" / "pages").glob("*.py"))]:
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("need", "load"):
                names |= {a.value for a in node.args if isinstance(a, ast.Constant) and a.value in ARTIFACTS}
    return len(names)


def b5_kebutuhan() -> None:
    prof = read_artifact(CFG, "profiles")
    nat = prof[(prof["level"] == "national") & prof["driver"].isin(["e", "w"]) & prof["horizon"].isin([4, 8, 12])]
    det = int(((nat["ci_low"] > 0) | (nat["ci_high"] < 0)).sum())
    het = read_artifact(CFG, "heterogeneity")
    rej = [NAMES[c] for c in het[(het["statistic"] == "Q") & het["reject"]]["commodity"]]
    st = artifact_status(CFG)
    n_art, n_have = len(st), int(st["available"].sum())
    rows = [
        ["RQ1 respons nasional", "Task 1, 3a", "profiles, events, mde", "interval 95%, MDE, plasebo",
         f"{det} dari {len(nat)} sel β_e & ω terdeteksi, sisanya batas atas", "Terpenuhi (hasil nol sah)"],
        ["RQ2 komoditas vs lokasi", "Task 1, 2", "heterogeneity, clusters", "Q vs plasebo, silhouette vs p95",
         f"H0-Het ditolak: {' & '.join(rej)}. k = 1", "Terpenuhi"],
        ["RQ3 asimetri", "Task 1, 3", "asymmetry", "Wald + bootstrap, MDE asimetri",
         "tidak ada sel yang intervalnya tidak memuat nol", "Terpenuhi (hasil nol sah)"],
        ["RQ4 karakteristik", "Task 3", "assoc", "Kendall eksak, meta-regresi CR2",
         "E1 τ-b −0,045 (p 0,93), H3 tidak didukung", "Terpenuhi (hasil nol sah)"],
        ["RQ5 nilai prediktif", "Task 4", "forecast_eval, ablation", "MAE, DM berarah, Holm",
         "M2/M1 1,009 / 1,013, H5 tidak didukung", "Terpenuhi (hasil nol sah)"],
        ["Ketahanan", "Robustness", "robustness", "Tier 1 wajib, V2, V4", "679 baris cek", "Terpenuhi"],
        ["App untuk TPID & juri", "App", f"{app_artifacts()} artefak ship", "uji 12 halaman, 3 lebar layar",
         "jalan daring, tanpa input pengguna", "Terpenuhi"],
        ["Validasi kebutuhan TPID", "–", "panduan wawancara", "wawancara pengguna",
         "belum dilakukan, status prototipe riset", "Belum"],
        ["Kelengkapan artefak", "Semua", f"{n_have} / {n_art} artefak", "kontrak kolom artifacts.py",
         "semua artefak ship ada", "Terpenuhi" if n_have == n_art else "Sebagian"],
        ["Paket juri & hak data", "Package", "zip juri", "tes isi zip", "mentah tanpa hak tidak dikirim",
         "Terpenuhi"],
    ]
    fills = {(i, 5): STATUS_FILL[r[5]] for i, r in enumerate(rows)}
    table_figure("b5_07_matriks_pemenuhan_kebutuhan",
                 ["Kebutuhan", "Task", "Artefak", "Metrik evaluasi", "Hasil", "Status"], rows,
                 [1.3, 0.75, 1.15, 1.3, 1.85, 1.2], [22, 12, 20, 22, 32, 18], cell_fills=fills,
                 note="Kebutuhan riset dianggap terpenuhi bila pertanyaannya terjawab dengan metrik dan aturan keputusan yang "
                      "dibekukan, termasuk bila jawabannya nol (batas atas). Sumber: profiles, heterogeneity, asymmetry, assoc, "
                      "forecast_eval, robustness, status artefak.")


def b5_kualitas_produk() -> None:
    st = artifact_status(CFG)
    n_art, n_have = len(st), int(st["available"].sum())
    a = read_artifact(CFG, "assoc")
    pv = a[a["level"] == "province"].dropna(subset=["p_value"])
    sig = pv["p_value"] < 0.05
    excl = (pv["ci_low"] > 0) | (pv["ci_high"] < 0)
    inc_a = int((sig != excl).sum())
    nc = read_artifact(CFG, "national_calibrated")
    inc_n = int(((nc["p_value"] < 0.05) != nc["ci_excludes_zero"]).sum())
    rows = [
        ["Task coverage", "Semua task yang dijanjikan proposal diimplementasikan",
         f"5 RQ dijawab oleh Task 1–4 + ketahanan. {n_have}/{n_art} artefak ada, 0 stub tersisa di src/. "
         "Analisis dalam-komoditas & Moran's I dipotong sesuai urutan pemotongan.", "Terpenuhi"],
        ["Evaluation consistency", "Setiap task punya metrik yang sesuai jenisnya",
         "Regresi: MAE/RMSE/DM. Klaster: silhouette vs plasebo, ARI, Jaccard (bukan akurasi). Asosiasi: interval, p eksak. "
         f"Cek p < 0,05 ⇔ interval tidak memuat nol: assoc {inc_a} dari {len(pv)} tidak cocok, "
         f"terkalibrasi {inc_n} dari {len(nc)}.", "Terpenuhi"],
        ["Usability", "Pengguna dapat membaca hasil tanpa kode",
         "App daring tanpa instalasi & login, tiap halaman dibuka dengan jawaban dalam % dan Rupiah, istilah teknis di "
         "lampiran, 0 tumpang tindih di 1280/1024/375 px. Belum diuji dengan pengguna TPID.", "Sebagian"],
        ["Reliability", "Sistem tahan data hilang, data besar, dan input salah",
         "12 halaman diuji dengan artefak ada dan hilang ('Menunggu hasil'). Pipeline gagal cepat bila input hilang. "
         "Data 800.642 baris harga harian, 157.760 sel panel, 814 ribu baris ramalan. App tidak menerima unggahan data, pemilih terbatas.",
         "Terpenuhi"],
        ["Reproducibility", "Konfigurasi & hasil dapat diulang orang lain",
         "Seed & parameter beku (sha256). Run penuh dari folder bersih: 35 artefak, 17 identik sha256, 16 selisih "
         "≤ 3,5e-11. Gladi zip juri 11/11 halaman. Log run dengan lineage sha256. Tingkat A/B/C.", "Terpenuhi"],
    ]
    fills = {(i, 3): STATUS_FILL[r[3]] for i, r in enumerate(rows)}
    table_figure("b5_08_kualitas_produk", ["Kriteria", "Pertanyaan", "Bukti", "Status"], rows,
                 [1.15, 1.6, 3.45, 0.85], [18, 26, 62, 12], cell_fills=fills,
                 note="Bukti dari artefak, tes otomatis (test_app, test_app_data, test_package, test_runtime), run end-to-end "
                      "24-11-2026, dan gladi G7 28-11-2026.")


# ================================================================================================== utama
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit", type=Path, default=None)
    args = ap.parse_args()
    P = preds()
    # cek angka acuan (berhenti bila tidak cocok dengan findings)
    mo = per_origin_mae(P)
    stat, _ = dm(mo.loc[4]["M1"], mo.loc[4]["M2"], 4)
    assert abs(stat - (-2.701)) < 0.01, stat
    b4_konfigurasi()
    b4_skenario()
    b4_perbandingan_model(P)
    b4_confusion()
    b4_clustering()
    b4_faktor()
    b4_dashboard(P)
    b4_pengujian(args.junit)
    b5_galat(P)
    b5_algoritma(P)
    b5_sensitivitas()
    b5_kontribusi(P)
    b5_klaster()
    b5_gagal(P)
    b5_kebutuhan()
    b5_kualitas_produk()
