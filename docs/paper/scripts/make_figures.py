"""Gambar makalah KAGAMI (WP-33) dari artefak resmi. Tidak ada estimasi baru: skrip ini hanya membaca artefak
`results/`, `data/processed/`, dan hasil analisis red flag (`docs/audit/20261127_redflag_juri/hasil/batas_rupiah.csv`,
dihitung dari artefak `profiles` & `panel_weekly`), lalu menulis PDF vektor ke `docs/paper/figures/`.

Jalankan dari root project:  python docs/paper/scripts/make_figures.py   (± 10 detik, tanpa instalasi paket)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "paper" / "figures"

spec = importlib.util.spec_from_file_location("kagami", ROOT / "src" / "__init__.py",
                                              submodule_search_locations=[str(ROOT / "src")])
mod = importlib.util.module_from_spec(spec)
sys.modules["kagami"] = mod
spec.loader.exec_module(mod)

from kagami.utils.config import Config  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402
from kagami.viz.style import AQUA, BLUE, NEUTRAL, ORANGE, PATH_LABELS  # noqa: E402

CFG = Config(root=ROOT)
NAMES = {"beras": "Beras", "bawang_putih": "Bawang putih", "gula_pasir": "Gula pasir", "daging_sapi": "Daging sapi",
         "daging_ayam": "Daging ayam", "telur_ayam": "Telur ayam", "minyak_goreng": "Minyak goreng",
         "bawang_merah": "Bawang merah", "cabai_merah": "Cabai merah", "cabai_rawit": "Cabai rawit"}
ORDER = list(NAMES)                       # urut jalur eksposur: impor langsung, input impor, paritas ekspor, domestik
WIDTH = 6.3                               # lebar teks A4 dengan margin 2,5 cm (inci)
DARK = "#2c2c2a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 7.8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.edgecolor": "#5f5e5a", "axes.linewidth": 0.6, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "axes.titleweight": "bold", "axes.titlecolor": DARK, "text.color": DARK,
    "axes.labelcolor": DARK, "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def _num(v: float, _=None) -> str:
    """Angka sumbu format Indonesia: desimal koma, ribuan titik, minus tipografis."""
    if abs(v) >= 1000:
        s = f"{v:,.0f}".replace(",", ".")
    else:
        s = f"{v:.10g}".replace(".", ",")
    return s.replace("-", "−")


FMT = FuncFormatter(_num)


def _path(com: str) -> str:
    return PATH_LABELS[CFG.commodities[com]["exposure_path"]]


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print(f"[figures] {name}.pdf")


def fig_kurs() -> None:
    """Gambar 1: kurs JISDOR mingguan dan 13 episode depresiasi."""
    d = read_artifact(CFG, "drivers_weekly")
    ep = read_artifact(CFG, "episodes")
    d = d[d["week"] >= "2018-01-01"].copy()
    d["rp"] = np.exp(d["log_e"])
    fig, ax = plt.subplots(figsize=(WIDTH, 2.25))
    for _, e in ep[ep["in_period"]].iterrows():
        ax.axvspan(pd.Timestamp(e["start_week"]), pd.Timestamp(e["end_week"]) + pd.Timedelta(days=6),
                   color=ORANGE, alpha=0.18, lw=0)
    ax.plot(d["week"], d["rp"], color=BLUE, lw=1.1)
    big = ep.loc[ep["cum_dlog_e"].idxmax()]
    ax.annotate(f"Mar–Mei 2020\nΣ Δlog kurs {_num(round(big['cum_dlog_e'], 3))}",
                xy=(pd.Timestamp(big["peak_week"]), d.loc[d["week"] == pd.Timestamp(big["peak_week"]), "rp"].max()),
                xytext=(pd.Timestamp("2021-01-01"), 16400), fontsize=6.6, color=DARK,
                arrowprops=dict(arrowstyle="-", color=NEUTRAL, lw=0.6))
    last = d.iloc[-1]
    ax.annotate(f"{_num(round(last['rp']))}", xy=(last["week"], last["rp"]), xytext=(4, -2),
                textcoords="offset points", fontsize=6.6, color=BLUE, va="center")
    ax.set_ylabel("Rupiah per dolar AS")
    ax.yaxis.set_major_formatter(FMT)
    ax.set_xlim(pd.Timestamp("2018-01-01"), d["week"].max() + pd.Timedelta(days=60))
    ax.text(0.01, 0.97, "Arsiran = episode depresiasi (Σ Δlog kurs 8 minggu ≥ 0,03; 13 episode)",
            transform=ax.transAxes, fontsize=6.6, va="top", color="#5f5e5a")
    _save(fig, "kurs_episode")


def _small_multiples(driver: str, coms: list[str], ncols: int, name: str, height: float, ylabel: str) -> None:
    p = read_artifact(CFG, "profiles")
    p = p[(p["level"] == "national") & (p["driver"] == driver)]
    nrows = int(np.ceil(len(coms) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(WIDTH, height), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, com in zip(axes, coms):
        s = p[p["commodity"] == com].sort_values("horizon")
        ax.fill_between(s["horizon"], s["ci_low"], s["ci_high"], color=BLUE, alpha=0.18, lw=0)
        ax.plot(s["horizon"], s["estimate"], color=BLUE, lw=1.1, marker="o", ms=1.8)
        ax.axhline(0, color="#5f5e5a", lw=0.6)
        detected = (s["ci_low"] > 0) | (s["ci_high"] < 0)
        if detected.any():
            ax.plot(s.loc[detected, "horizon"], s.loc[detected, "estimate"], ls="none", marker="o", ms=3.2,
                    mfc=ORANGE, mec=ORANGE)
        ax.set_title(NAMES[com], loc="left", pad=8)
        ax.text(0, 1.0, _path(com), transform=ax.transAxes, fontsize=6.1, color="#5f5e5a", va="bottom")
        ax.set_xticks([0, 4, 8, 12])
        ax.yaxis.set_major_formatter(FMT)
        ax.tick_params(length=2)
    for ax in axes[len(coms):]:
        ax.axis("off")
    fig.supxlabel("Minggu sesudah perubahan penggerak (h)", fontsize=7.5, y=0.0)
    fig.supylabel(ylabel, fontsize=7.5, x=0.0)
    fig.subplots_adjust(wspace=0.42, hspace=0.62, left=0.075, right=0.995, top=0.9, bottom=0.12)
    _save(fig, name)


def fig_respons() -> None:
    """Gambar 3: respons kumulatif nasional terhadap kurs (β_e) dan harga dunia rupiah (ω), interval resmi."""
    _small_multiples("e", ORDER, 5, "respons_kurs", 3.7, "Δ log harga per 1 log kurs (≈ % per 1%)")
    _small_multiples("w", ["beras", "gula_pasir", "daging_sapi", "daging_ayam", "telur_ayam", "minyak_goreng"], 3,
                     "respons_dunia", 3.3, "Δ log harga per 1 log harga dunia rupiah")


def fig_batas() -> None:
    """Gambar 4: perubahan harga nasional 8 minggu untuk rupiah melemah 5% (PT(8) resmi), dalam % dan batas atas Rp."""
    b = pd.read_csv(ROOT / "docs" / "audit" / "20261127_redflag_juri" / "hasil" / "batas_rupiah.csv")
    b = b[(b["scenario"] == "rupiah melemah 5%") & (b["horizon"] == 8)].set_index("commodity")
    order = ["beras", "daging_sapi", "daging_ayam", "minyak_goreng", "telur_ayam", "gula_pasir", "bawang_putih",
             "bawang_merah", "cabai_merah", "cabai_rawit"]
    b = b.loc[order]
    fig, ax = plt.subplots(figsize=(WIDTH, 2.7))
    y = np.arange(len(b))[::-1]
    for yi, (com, r) in zip(y, b.iterrows()):
        useful = r["pct_high"] <= 5.0
        col = BLUE if useful else NEUTRAL
        ax.plot([r["pct_low"], r["pct_high"]], [yi, yi], color=col, lw=2.2, solid_capstyle="round", alpha=0.85)
        ax.plot(r["pct_est"], yi, "o", color="white", mec=col, mew=1.2, ms=4)
        ax.text(21.5, yi, f"maks {'+' if r['rp_high'] >= 0 else '−'}Rp{_num(round(abs(r['rp_high'])))}",
                va="center", fontsize=6.6, color=col if useful else "#5f5e5a")
    ax.axvline(0, color="#5f5e5a", lw=0.6)
    ax.axvline(5, color=ORANGE, lw=0.7, ls=(0, (3, 2)))
    ax.text(5.3, y[0] + 0.55, "batas berguna ≤ 5%", fontsize=6.3, color=ORANGE, va="bottom")
    ax.set_yticks(y, [NAMES[c] for c in b.index])
    ax.set_xlim(-20, 20)
    ax.set_ylim(-0.7, len(b) - 0.2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v) + "%"))
    ax.set_xlabel("Perubahan harga eceran nasional 8 minggu sesudah rupiah melemah 5% (interval 95% resmi)")
    ax.text(21.5, len(b) - 0.15, "batas atas, per kg/liter", fontsize=6.3, color="#5f5e5a", va="bottom")
    ax.tick_params(axis="y", length=0)
    _save(fig, "batas_rupiah")


def fig_regional() -> None:
    """Gambar 5: (a) silhouette Ward per k vs p95 plasebo; (b) batas deteksi struktur tertanam."""
    cs = read_artifact(CFG, "cluster_selection")
    pr = read_artifact(CFG, "planted_recovery")
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDTH, 2.25))
    c = cs[cs["k"] >= 2]
    a.plot(c["k"], c["silhouette"], color=BLUE, marker="o", ms=3.5, lw=1.1, label="data asli")
    a.axhline(cs["placebo_p95"].iloc[0], color=ORANGE, ls=(0, (3, 2)), lw=0.9, label="persentil 95 plasebo")
    a.set_xlabel("Jumlah kelompok k")
    a.set_ylabel("Silhouette maksimum")
    a.set_title("(a) Pemilihan k terhadap plasebo", loc="left")
    a.set_xticks(c["k"])
    a.yaxis.set_major_formatter(FMT)
    a.legend(frameon=False, loc="lower left")
    for k_true, col in [(2, BLUE), (3, AQUA)]:
        s = pr[pr["k_true"] == k_true]
        b.plot(s["delta"], s["recovery_rate"], color=col, marker="o", ms=3.5, lw=1.1, label=f"{k_true} kelompok")
    b.axhline(0.8, color="#5f5e5a", ls=(0, (1, 2)), lw=0.8)
    b.text(0.5, 0.78, "ambang 0,8", fontsize=6.3, color="#5f5e5a", ha="right", va="top")
    b.set_xlabel("Selisih respons tertanam δ (RMS per fitur)")
    b.set_ylabel("Peluang ditemukan kembali")
    b.set_title("(b) Batas deteksi struktur tertanam", loc="left")
    b.xaxis.set_major_formatter(FMT)
    b.yaxis.set_major_formatter(FMT)
    b.set_ylim(0, 1.05)
    b.legend(frameon=False, loc="lower right")
    fig.tight_layout(w_pad=2.5)
    _save(fig, "struktur_regional")


def fig_prediksi() -> None:
    """Gambar 6: rasio MAE terhadap M1 per komoditas (semua origin): M2 (+ kurs & harga dunia) dan M0 (tanpa perubahan)."""
    fe = read_artifact(CFG, "forecast_eval")
    fe = fe[(fe["level"] == "commodity") & (fe["subset"] == "all")]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.6), sharey=True)
    for ax, h in zip(axes, [4, 8]):
        s = fe[fe["horizon"] == h].pivot_table(index="commodity", columns="model", values="mae_ratio_vs_m1")
        s = s.loc[ORDER[::-1]]
        y = np.arange(len(s))
        ax.axvline(1, color="#5f5e5a", lw=0.6)
        ax.plot(s["M0"], y, "o", mfc="white", mec=NEUTRAL, mew=1.0, ms=4, label="M0: tanpa perubahan")
        ax.plot(s["M2"], y, "o", color=BLUE, ms=4, label="M2: + kurs & harga dunia")
        ax.set_yticks(y, [NAMES[c] for c in s.index])
        ax.set_title(f"h = {h} minggu", loc="left")
        ax.xaxis.set_major_formatter(FMT)
        ax.set_xlabel("MAE / MAE model dasar M1")
        ax.tick_params(axis="y", length=0)
    h1, l1 = axes[0].get_legend_handles_labels()
    fig.legend(h1, l1, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.55, 1.07), fontsize=6.6)
    fig.text(0.99, -0.02, "Di kanan garis 1 = kurang akurat dari M1. 76/75 origin 2021–2026, 337 seri provinsi.",
             ha="right", fontsize=6.3, color="#5f5e5a")
    fig.tight_layout(w_pad=1.5)
    _save(fig, "prediksi_mae")


if __name__ == "__main__":
    fig_kurs()
    fig_respons()
    fig_batas()
    fig_regional()
    fig_prediksi()
