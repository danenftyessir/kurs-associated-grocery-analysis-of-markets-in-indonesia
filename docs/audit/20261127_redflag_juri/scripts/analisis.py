"""Audit red flag juri (2026-11-27, D-168). Baca-saja: hanya membaca artefak resmi, tidak menulis ke results/.

Bagian A (poin 7) : batas atas respons harga dalam Rupiah per kg untuk skenario pelemahan rupiah 5% (PT nasional resmi)
                    dan kenaikan harga sawit dunia 10% (ω minyak goreng resmi).
Bagian B (poin 6) : uji ukuran (size) interval terkalibrasi plasebo D-129 secara leave-one-out: setiap replikasi plasebo
                    diperlakukan sebagai "data asli" dan dinilai dengan ambang dari 498 replikasi lainnya. Bandingkan
                    dengan ±1,96·SE. Juga hitung berapa sel data asli yang tidak memuat nol menurut tiap metode.

Jalankan dari root project:  python docs/audit/20261127_redflag_juri/scripts/analisis.py
Output: docs/audit/20261127_redflag_juri/hasil/{batas_rupiah.csv, size_kalibrasi.csv, ringkasan.txt}
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("kagami", ROOT / "src/__init__.py", submodule_search_locations=[str(ROOT / "src")])
mod = importlib.util.module_from_spec(spec)
sys.modules["kagami"] = mod
spec.loader.exec_module(mod)

from kagami.stats.meta import bh_fdr  # noqa: E402
from kagami.utils.config import Config  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "hasil"
OUT.mkdir(exist_ok=True)
cfg = Config(root=ROOT)
lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    lines.append(s)


# ---------------------------------------------------------------- A. batas atas dalam Rupiah
prof = read_artifact(cfg, "profiles")
panel = read_artifact(cfg, "panel_weekly")
elig = read_artifact(cfg, "eligibility")

last = panel["week"].max()
recent = panel[(panel["week"] > last - pd.Timedelta(weeks=8)) & (panel["status"] == "observed")]
recent = recent.merge(elig[elig["eligible"]][["province_id", "commodity"]], on=["province_id", "commodity"])
# harga acuan = median antarprovinsi dari rerata 8 minggu terakhir yang teramati (Rp/kg; telur Rp/kg; minyak Rp/liter)
price = recent.groupby(["commodity", "province_id"])["price"].mean().groupby("commodity").median().rename("price_rp")

nat = prof[(prof["level"] == "national") & prof["horizon"].isin([4, 8])]
x_fx = math.log(1.05)       # rupiah melemah 5% (IDR/USD naik 5%)
x_w = math.log(1.10)        # harga sawit dunia dalam rupiah naik 10%
rows = []
for (c, h), g in nat.groupby(["commodity", "horizon"]):
    if c not in price.index:
        continue
    p0 = float(price[c])
    for drv, x, scen in (("PT", x_fx, "rupiah melemah 5%"), ("w", x_w, "harga dunia rupiah naik 10%")):
        r = g[g["driver"] == drv]
        if r.empty or (drv == "w" and c != "minyak_goreng"):
            continue
        r = r.iloc[0]
        pct = lambda b: (math.exp(b * x) - 1) * 100  # noqa: E731
        rows.append(dict(commodity=c, horizon=int(h), scenario=scen, driver=drv, price_rp=round(p0),
                         estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"],
                         pct_est=pct(r["estimate"]), pct_low=pct(r["ci_low"]), pct_high=pct(r["ci_high"]),
                         rp_est=p0 * pct(r["estimate"]) / 100, rp_low=p0 * pct(r["ci_low"]) / 100,
                         rp_high=p0 * pct(r["ci_high"]) / 100,
                         ci_includes_zero=bool(r["ci_low"] <= 0 <= r["ci_high"])))
bounds = pd.DataFrame(rows).sort_values(["scenario", "horizon", "commodity"])
bounds.to_csv(OUT / "batas_rupiah.csv", index=False, float_format="%.4f")
say(f"[A] minggu harga acuan: 8 minggu s.d. {last.date()} (teramati, seri layak); skenario log(1,05) & log(1,10)")
for _, r in bounds[bounds["horizon"] == 8].iterrows():
    say(f"  {r.commodity:14s} h8 {r.scenario:28s} harga {r.price_rp:>8,.0f}  est {r.pct_est:+6.2f}% "
        f"({r.pct_low:+6.2f}..{r.pct_high:+6.2f}%)  Rp {r.rp_est:+8,.0f} ({r.rp_low:+8,.0f}..{r.rp_high:+8,.0f})")

# ---------------------------------------------------------------- B. ukuran interval terkalibrasi (leave-one-out)
alpha = float(cfg.params["power"]["mde_alpha"])
z = float(stats.norm.ppf(1 - alpha / 2))
H = [int(h) for h in cfg.params["lp"]["key_horizons"]]
pl = read_artifact(cfg, "placebo_stats")
pl = pl[(pl["level"] == "national") & pl["driver"].isin(["e", "w"]) & pl["horizon"].isin(H)].copy()
pl["t"] = (pl["estimate"] / pl["se"]).abs()
T = pl.pivot_table(index="rep", columns=["commodity", "driver", "horizon"], values="t")   # rep × 48 sel
T = T.dropna(axis=1, how="all")
R, K = T.shape                                      # komoditas non-fokus hanya R = 199 (bootstrap_B_nonfocus)
n_rep = T.notna().sum()


def loo_p(col: np.ndarray) -> np.ndarray:
    """p plasebo LOO tiap replikasi pada replikasi yang ada (n): (1 + #{lainnya ≥ |t_r|}) / n, lalu max dengan p normal
    (aturan D-129). NaN tetap NaN."""
    out = np.full(len(col), np.nan)
    ok = np.isfinite(col)
    v = col[ok]
    s = np.sort(v)
    n_ge_all = len(s) - np.searchsorted(s, v, side="left")      # termasuk dirinya
    out[ok] = np.fmax((1 + (n_ge_all - 1)) / len(v), 2 * stats.norm.sf(v))
    return out


P_cal = np.column_stack([loo_p(T.iloc[:, j].to_numpy()) for j in range(K)])
P_naive = 2 * stats.norm.sf(T.to_numpy())                     # NaN tetap NaN


def rate(P: np.ndarray) -> np.ndarray:
    """Porsi p < α per sel di antara replikasi yang ada (NaN tidak dihitung sebagai tidak menolak)."""
    return np.array([np.mean(c[np.isfinite(c)] < alpha) for c in P.T])


fp_cal, fp_naive = rate(P_cal), rate(P_naive)
full = np.isfinite(P_naive).all(axis=1)                       # replikasi dengan ke-48 sel (rep < 199)


def family(P: np.ndarray) -> tuple[float, float, float]:
    """Per replikasi lengkap: BH atas 48 sel -> (porsi replikasi dengan ≥ 1 temuan q < α, rerata temuan, rerata p < α)."""
    disc, n_q, n_p = [], [], []
    for row in P[full]:
        q = bh_fdr(row)
        disc.append((q < alpha).any())
        n_q.append((q < alpha).sum())
        n_p.append((row < alpha).sum())
    return float(np.mean(disc)), float(np.mean(n_q)), float(np.mean(n_p))


fw_cal, nq_cal, np_cal = family(P_cal)
fw_naive, nq_naive, np_naive = family(P_naive)

cal = read_artifact(cfg, "national_calibrated")
cal = cal[cal["driver"].isin(["e", "w"])]
real = prof[(prof["level"] == "national") & prof["driver"].isin(["e", "w"]) & prof["horizon"].isin(H)].copy()
real["naive_excl"] = (real["estimate"] - z * real["se"] > 0) | (real["estimate"] + z * real["se"] < 0)
real["prereg_excl"] = (real["ci_low"] > 0) | (real["ci_high"] < 0)
n_wider = int((cal["crit_placebo"] > z).sum())

size = pd.DataFrame({
    "metode": ["±1,96·SE cluster minggu", "terkalibrasi plasebo (D-129)", "resmi praregistrasi (SE ∪ bootstrap)"],
    "fp_per_sel_null_rerata": [fp_naive.mean(), fp_cal.mean(), np.nan],
    "fp_per_sel_null_maks": [fp_naive.max(), fp_cal.max(), np.nan],
    "null_rerata_sel_p_lt_alpha_dari_48": [np_naive, np_cal, np.nan],
    "null_porsi_rep_ada_temuan_BH": [fw_naive, fw_cal, np.nan],
    "null_rerata_temuan_BH": [nq_naive, nq_cal, np.nan],
    "asli_sel_tidak_memuat_nol_dari_48": [int(real["naive_excl"].sum()), int(cal["ci_excludes_zero"].sum()),
                                          int(real["prereg_excl"].sum())],
    "asli_temuan_BH_q_lt_alpha": [int((bh_fdr(2 * stats.norm.sf((real["estimate"] / real["se"]).abs().to_numpy()))
                                       < alpha).sum()), int((cal["q_fdr"] < alpha).sum()), np.nan],
})
size.to_csv(OUT / "size_kalibrasi.csv", index=False, float_format="%.4f")
say()
say(f"[B] {K} sel nasional (e & w, h {H}); replikasi per sel {n_rep.min()}–{n_rep.max()}; keluarga BH pada {int(full.sum())} replikasi lengkap; LOO = ambang dari replikasi lainnya")
say(size.to_string(index=False))
say(f"  sel dengan ambang plasebo > 1,96 (kalibrasi MELEBARKAN interval vs ±1,96·SE): {n_wider} dari {len(cal)}; "
    f"median crit {cal['crit'].median():.2f}, maks {cal['crit'].max():.2f}")
# ---------------------------------------------------------------- C. buku besar pembukaan test 2024+ (poin 5)
# Angka dari docs/DECISIONS.md (bukan dihitung ulang). p: bila hanya q BH dilaporkan, q dipakai sebagai p (konservatif,
# karena p ≤ q); bila hanya interval bootstrap, p ≈ 2Φ(−|est|/se) dengan se = (hi − lo)/3,92 (pendekatan normal).
def p_from_ci(est: float, lo: float, hi: float) -> float:
    return float(2 * stats.norm.sf(abs(est) / ((hi - lo) / (2 * z))))


ledger = pd.DataFrame([
    ("D-145", "C1-tuned − TimesFM, macro F1 h 4", 0.059, 0.001, "q"),
    ("D-145", "C1-tuned − TimesFM, macro F1 h 8", 0.053, 0.001, "q"),
    ("D-147", "iw_gap − C1-tuned, macro F1 h 4", 0.004, 0.35, "q"),
    ("D-147", "iw_gap − C1-tuned, macro F1 h 8", 0.005, 0.089, "q"),
    ("D-151", "IW_NAT − C1-tuned, macro F1 h 4", 0.0085, 0.28, "q"),
    ("D-151", "IW_NAT − C1-tuned, macro F1 h 8", 0.0033, 0.30, "q"),
    ("D-154", "presisi daftar pantau C1-tuned − aturan naif h 4", 0.094, p_from_ci(0.094, 0.055, 0.132), "ci"),
    ("D-154", "presisi daftar pantau C1-tuned − aturan naif h 8", 0.072, p_from_ci(0.072, 0.034, 0.115), "ci"),
    ("D-164", "AP K4-E80 − C1-tuned h 4", 0.045, p_from_ci(0.045, 0.017, 0.083), "ci"),
    ("D-164", "AP K4-E80 − C1-tuned h 8", 0.015, 0.5, "ci memuat 0"),
], columns=["keputusan", "perbandingan", "selisih", "p", "sumber_p"])
m = len(ledger)
order = np.argsort(ledger["p"].to_numpy())
holm = np.empty(m)
run = 0.0
for rank, i in enumerate(order):
    run = max(run, min(1.0, (m - rank) * ledger["p"].iloc[i]))
    holm[i] = run
ledger["p_holm_semua_pembukaan"] = holm
ledger["lolos_holm"] = holm < alpha
ledger.to_csv(OUT / "buku_besar_test.csv", index=False, float_format="%.6f")
say()
say(f"[C] {m} perbandingan pada test 2024+ dari 5 pembukaan berkomparasi (D-145, D-147, D-151, D-154, D-164); Holm satu keluarga")
say(ledger.to_string(index=False))

(OUT / "ringkasan.txt").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
