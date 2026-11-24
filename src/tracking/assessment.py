"""WP-36. Lapis kedua evaluasi (D-140): status hitung (`ok` / `not_applicable` / `failed`) hanya menyatakan metrik
BERHASIL DIHITUNG, bukan bahwa hasilnya baik. Modul ini menambahkan penilaian terhadap acuan yang eksplisit:

- acuan (nilai + jenis): peluang/acak, baseline kelas mayoritas, α (laju positif palsu), rasio 1 (setara M1), ambang
  MDE, p95 plasebo, nol (cek integritas);
- penilaian: better (lebih baik dari acuan, didukung interval/uji), worse (lebih buruk, didukung interval/uji),
  inconclusive (belum terbukti berbeda dari acuan), expected (sesuai harapan metodologis, mis. cek integritas lolos),
  review (perlu ditinjau: menandakan masalah inferensi/data), info (deskriptif, tanpa acuan);
- interpretasi singkat dalam bahasa Indonesia.

Penilaian dihitung saat log DIBACA dari nilai + konteks metrik (juga berlaku untuk log lama); log JSON tidak diubah.
Hanya metrik dengan aturan eksplisit yang dinilai; selebihnya "info". Keputusan "better/worse" hanya diambil bila ada
interval atau uji (bootstrap blok origin, binomial terhadap α, DM); tanpa itu → inconclusive.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

ALPHA = 0.05
LABELS = {"better": "lebih baik dari acuan", "worse": "lebih buruk dari acuan",
          "inconclusive": "belum terbukti berbeda dari acuan", "expected": "sesuai harapan", "review": "perlu ditinjau",
          "info": "informasi", "not_computed": "tidak dihitung"}
COLUMNS = ["reference", "reference_label", "ci_low", "ci_high", "assessment", "interpretation"]


def _num(v: Any) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _r(reference=None, label=None, assessment="info", text="", lo=None, hi=None) -> dict[str, Any]:
    return {"reference": reference, "reference_label": label, "ci_low": lo, "ci_high": hi, "assessment": assessment,
            "interpretation": text}


def _f(x: float | None, d: int = 3) -> str:
    return "–" if x is None else f"{x:.{d}f}".replace(".", ",")


def _ci_vs(v: float, ref: float, ctx: dict, higher_better: bool = True, lo_key="ci_low", hi_key="ci_high"):
    """Penilaian dengan interval di konteks: interval di atas acuan → better (bila higher_better)."""
    lo, hi = _num(ctx.get(lo_key)), _num(ctx.get(hi_key))
    if lo is None or hi is None:
        return "inconclusive", lo, hi, "tanpa interval ketidakpastian (log lama: jalankan `kagami evaluate`)"
    if lo > ref:
        a = "better" if higher_better else "worse"
    elif hi < ref:
        a = "worse" if higher_better else "better"
    else:
        a = "inconclusive"
    return a, lo, hi, f"interval 95% {_f(lo)}..{_f(hi)}"


def _binom_greater(k: int, n: int, p0: float) -> float:
    from scipy.stats import binomtest

    return float(binomtest(k, n, p0, alternative="greater").pvalue)


def _binom_two(k: int, n: int, p0: float) -> float:
    from scipy.stats import binomtest

    return float(binomtest(k, n, p0).pvalue)


def _strength(v: float, cuts: tuple[float, float, float], base: float) -> str:
    x = abs(v - base)
    return "sangat lemah" if x < cuts[0] else "lemah" if x < cuts[1] else "sedang" if x < cuts[2] else "kuat"


# --------------------------------------------------------------------------- aturan per pola nama
def _dir(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    key, met = m.group(1), m.group(2)
    if met == "accuracy":
        ref = _num(peers.get(f"{key}_dir_majority_baseline_accuracy"))
        if ref is None:
            return _r(text="baseline mayoritas tidak tersedia")
        a, lo, hi, note = _ci_vs(v - ref, 0.0, ctx, lo_key="gap_ci_low", hi_key="gap_ci_high")
        note = note.replace("interval 95%", "interval 95% selisih")
        txt = (f"selisih vs selalu menebak kelas mayoritas {'+' if v >= ref else ''}{_f(v - ref)}; {note}")
        if a == "inconclusive":
            txt += " → tidak lebih baik dari menebak arah terbanyak"
        return _r(ref, "baseline kelas mayoritas", a, txt, _num(ctx.get("ci_low")), _num(ctx.get("ci_high")))
    if met in ("balanced_accuracy", "f1_macro"):
        a, lo, hi, note = _ci_vs(v, 0.5, ctx)
        return _r(0.5, "tebakan acak seimbang", a, note, lo, hi)
    if met == "mcc":
        a, lo, hi, note = _ci_vs(v, 0.0, ctx)
        return _r(0.0, "tanpa hubungan", a, f"korelasi arah {_strength(v, (0.1, 0.3, 0.5), 0)}; {note}", lo, hi)
    if met == "roc_auc":
        a, lo, hi, note = _ci_vs(v, 0.5, ctx)
        return _r(0.5, "peluang", a, f"daya pemisah {_strength(v, (0.1, 0.2, 0.3), 0.5)}; {note}", lo, hi)
    if met == "pr_auc":
        ref = _num(ctx.get("share_naik"))
        if ref is None:
            return _r()
        a, lo, hi, note = _ci_vs(v, ref, ctx)
        return _r(ref, "porsi kelas naik (prevalensi)", a, note, lo, hi)
    if met == "majority_baseline_accuracy":
        return _r(text="pembanding: akurasi bila selalu menebak arah terbanyak")
    if met == "recall_turun" and v < 0.5:
        return _r(0.5, "peluang", "info", "kurang dari separuh penurunan harga tertebak")
    return _r()


def _mae_ratio(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    h, model = m.group(1), m.group(2)
    if model == "M1":
        return _r(text="pembanding (= 1)")
    p = _num(peers.get(f"dm_p_h{h}_{model}"))
    p = p if p is not None else _num(ctx.get("dm_p"))
    if model == "M2_nofx" and abs(v - 1) < 1e-12:
        return _r(1.0, "M1", "review", "identik dengan M1: ablation fitur kurs = perbandingan M2 vs M1")
    if p is None:
        return _r(1.0, "M1 (rasio 1)", "inconclusive", "uji DM tidak tersedia")
    if p < ALPHA:
        a = "better" if v < 1 else "worse"
        return _r(1.0, "M1 (rasio 1)", a, f"MAE {'lebih kecil' if v < 1 else 'lebih besar'} dari M1, DM p {_f(p)}")
    return _r(1.0, "M1 (rasio 1)", "inconclusive", f"tidak berbeda nyata dari M1 (DM p {_f(p)})")


def _rate_vs_alpha(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    n = _num(ctx.get("n"))
    if not n:
        return _r(ALPHA, "α (laju positif palsu)", "inconclusive", "n tidak tersedia")
    k = int(round(v * n))
    p = _binom_greater(k, int(n), ALPHA)
    if p < ALPHA:
        return _r(ALPHA, "α (laju positif palsu)", "better",
                  f"{k}/{int(n)} lebih banyak dari yang diharapkan di bawah null (uji binomial p {_f(p)})")
    return _r(ALPHA, "α (laju positif palsu)", "inconclusive",
              f"{k}/{int(n)} ≈ jumlah yang diharapkan dari derau saja ({_f(ALPHA * n, 1)}); uji binomial p {_f(p)}")


def _placebo_fpr(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    n = _num(ctx.get("n"))
    if not n:
        return _r(ALPHA, "α (nominal)")
    p = _binom_two(int(round(v * n)), int(n), ALPHA)
    if p < ALPHA and v > ALPHA:
        return _r(ALPHA, "α (nominal)", "review",
                  f"positif palsu {_f(v * 100, 1)}% > 5%: SE cluster terlalu sempit (± {_f(v / ALPHA, 1)}×); "
                  "interval ±1,96·SE optimistis → pakai interval terkalibrasi plasebo (D-129)")
    return _r(ALPHA, "α (nominal)", "expected", "laju positif palsu sesuai nominal")


def _boot_ratio(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    if v < 0.8:
        return _r(1.0, "rasio 1 (tanpa bias)", "review",
                  f"replikasi bootstrap rata-rata hanya {_f(v * 100, 0)}% estimasi: bootstrap menarik β ke nol, interval "
                  "persentil terlalu konservatif (U107)")
    return _r(1.0, "rasio 1 (tanpa bias)", "expected", "bootstrap tidak bias berarti")


def _silhouette(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    ref = _num(peers.get("placebo_p95_silhouette"))
    if ref is None:
        return _r()
    if v > ref:
        return _r(ref, "p95 silhouette plasebo", "better", "struktur lolos uji plasebo")
    return _r(ref, "p95 silhouette plasebo", "inconclusive",
              "di bawah ambang plasebo: tidak ada struktur regional terdeteksi (k = 1 adalah hasil sah)")


def _margin(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    return (_r(0.0, "p95 plasebo", "better", "struktur lolos uji plasebo") if v > 0 else
            _r(0.0, "p95 plasebo", "inconclusive", "silhouette terbaik di bawah p95 plasebo → k = 1 (hasil sah)"))


def _integrity_zero(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    return (_r(0.0, "0 (cek integritas)", "expected", "hitung ulang = artefak resmi") if abs(v) < 1e-9 else
            _r(0.0, "0 (cek integritas)", "review", "hasil hitung ulang berbeda dari artefak resmi"))


def _consistency(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    if "h2_" in m.group(0):
        return _r(1.0, "1 (p ⇔ interval)", "expected",
                  "ketidakcocokan disengaja: p dari Wald, interval laporan = Wald ∪ bootstrap (D-127)")
    return (_r(1.0, "1 (p ⇔ interval)", "expected", "p < α ⇔ interval tidak memuat nol di semua baris") if v >= 1 - 1e-12
            else _r(1.0, "1 (p ⇔ interval)", "review", "ada baris dengan p dan interval yang bertentangan (U106)"))


def _p_value(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    return (_r(ALPHA, "α", "better", "terdeteksi pada α 0,05") if v < ALPHA else
            _r(ALPHA, "α", "inconclusive", "tidak terdeteksi (batas atas, bukan bukti tidak ada efek)"))


def _mde(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    thr = _num(ctx.get("threshold"))
    if thr is None:
        return _r()
    return (_r(thr, "ambang MDE PT(8)", "better", "daya cukup untuk efek sebesar ambang") if v <= thr else
            _r(thr, "ambang MDE PT(8)", "worse", f"efek di bawah {_f(v, 2)} tidak dapat dideteksi (daya rendah)"))


def _share_half(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    n = _num(ctx.get("n"))
    if not n:
        return _r(0.5, "0,5 (netral)")
    k = int(round(v * n))
    p = _binom_two(k, int(n), 0.5)
    a = ("better" if v > 0.5 else "worse") if p < ALPHA else "inconclusive"
    what = {"share_fx_improves": "sel dengan fitur kurs menurunkan MAE",
            "v4_mean_sign_agree": "sel LP vs event study bertanda sama"}.get(m.group(0), "porsi")
    tail = " → setara lempar koin" if a == "inconclusive" else ""
    return _r(0.5, "0,5 (netral / peluang)", a, f"{k}/{int(n)} {what} (binomial p {_f(p)}){tail}")


def _corr(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    return _r(0.0, "tanpa korelasi", "info", f"korelasi {_strength(v, (0.1, 0.3, 0.5), 0)}")


def _coverage(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    tier = m.group(1)
    w = _num(peers.get(f"median_ci_width_tier_{tier}"))
    det = _num(peers.get(f"share_detected_tier_{tier}"))
    if w is None:
        return _r(text="cakupan tinggi bisa karena interval lebar")
    return _r(None, None, "info", f"lebar interval median {_f(w, 2)}, hanya {_f((det or 0) * 100, 0)}% estimasi cek "
                                  "terdeteksi → cakupan tinggi terutama mencerminkan interval lebar")


def _constant(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    n = _num(peers.get("n_features"))
    if v == 0:
        return _r(0, "0", "expected", "semua fitur bervariasi")
    return _r(0, "0", "review", f"{int(v)} dari {int(n) if n else '?'} fitur konstan (tersusut habis, τ² = 0): "
                               "tidak membawa informasi antarprovinsi")


def _ablation_same(m: re.Match, v: Any, ctx: dict, peers: dict) -> dict:
    return (_r(None, None, "review", "M2_nofx = M1: ablation tidak menambah informasi di luar M2 vs M1") if v is True
            else _r(None, None, "expected", "model ablation berbeda dari M1"))


def _h5(m: re.Match, v: Any, ctx: dict, peers: dict) -> dict:
    return (_r(None, None, "better", "H5 didukung") if v is True else
            _r(None, None, "inconclusive", "H5 tidak didukung: fitur kurs tidak terbukti menurunkan MAE h 8"))


def _q_min(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    return (_r(ALPHA, "q BH 0,05", "better", "minimal satu sel lolos koreksi multiplisitas") if v < ALPHA else
            _r(ALPHA, "q BH 0,05", "inconclusive", "tidak ada sel yang lolos koreksi multiplisitas"))


def _paired(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    a, b = m.group(1), m.group(2)
    res, lo, hi, note = _ci_vs(v, 0.0, ctx)
    verdict = {"better": f"{a} lebih akurat dari {b}", "worse": f"{a} kurang akurat dari {b}",
               "inconclusive": f"{a} tidak terbukti berbeda dari {b}"}[res]
    return _r(0.0, f"selisih nol ({b})", res, f"{verdict}; {note}", lo, hi)


def _mae_pair(m: re.Match, v: float, ctx: dict, peers: dict) -> dict:
    a, b = m.group(1), m.group(2)
    p = _num(ctx.get("dm_p"))
    if p is None:
        return _r(1.0, f"{b} (rasio 1)", "inconclusive", "uji DM tidak tersedia")
    if p < ALPHA:
        return _r(1.0, f"{b} (rasio 1)", "better" if v < 1 else "worse",
                  f"MAE {a} {'lebih kecil' if v < 1 else 'lebih besar'} dari {b}, DM p {_f(p)}")
    return _r(1.0, f"{b} (rasio 1)", "inconclusive", f"MAE {a} tidak berbeda nyata dari {b} (DM p {_f(p)})")


RULES: list[tuple[re.Pattern, Callable[..., dict]]] = [(re.compile(p), f) for p, f in [
    (r"^h\d+_(\w+?)_vs_(\w+)_accuracy_diff$", _paired),
    (r"^mae_ratio_h\d+_(\w+?)_vs_(\w+)$", _mae_pair),
    (r"^(h\d+_[A-Za-z0-9_]+?)_dir_(\w+)$", _dir),
    (r"^mae_ratio_vs_m1_h(\d+)_(\w+)$", _mae_ratio),
    (r"^(share_ci_excludes_zero_national|share_events_placebo_p05)$", _rate_vs_alpha),
    (r"^placebo_false_positive_rate$", _placebo_fpr),
    (r"^boot_ratio_median_h\d+$", _boot_ratio),
    (r"^silhouette_k\d+$", _silhouette),
    (r"^silhouette_margin_vs_placebo$", _margin),
    (r"^(silhouette_recompute|mae_crosscheck)_max_abs_diff$", _integrity_zero),
    (r"^\w+_p_interval_consistency$", _consistency),
    (r"^kendall_p_exact$", _p_value),
    (r"^mde_pt8_\w+$", _mde),
    (r"^(share_fx_improves|v4_mean_sign_agree)$", _share_half),
    (r"^v4_mean_corr$", _corr),
    (r"^share_baseline_in_ci_tier_(\w+)$", _coverage),
    (r"^n_constant_features$", _constant),
    (r"^ablation_model_equals_m1$", _ablation_same),
    (r"^h5_rejected$", _h5),
    (r"^(min_q_fdr_Q|e2_min_q_fdr)$", _q_min),
]]


def assess(name: str, value: Any, context: dict | None = None, peers: dict | None = None) -> dict[str, Any]:
    """Penilaian satu metrik berstatus ok terhadap acuannya. peers = nama → nilai metrik lain dari run yang sama (untuk
    acuan yang berupa metrik lain, mis. baseline mayoritas atau p95 plasebo). Tanpa aturan → info."""
    ctx, peers = context or {}, peers or {}
    for pat, fn in RULES:
        m = pat.match(name)
        if not m:
            continue
        if isinstance(value, bool) or fn in (_ablation_same, _h5):
            return fn(m, value, ctx, peers)
        v = _num(value)
        if v is None:
            return _r()
        try:
            return fn(m, v, ctx, peers)
        except Exception as exc:  # noqa: BLE001 -- penilaian gagal tidak boleh menjatuhkan halaman
            return _r(None, None, "review", f"penilaian gagal: {type(exc).__name__}")
    return _r()


def assess_table(metrics: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan kolom penilaian ke `store.metrics_table` (reference, reference_label, ci_low, ci_high, assessment,
    interpretation). Metrik tidak berlaku / gagal → assessment not_computed."""
    out = metrics.copy()
    if out.empty:
        for c in COLUMNS:
            out[c] = pd.Series(dtype=object)
        return out
    peers = {rid: dict(zip(d["name"], d["value"])) for rid, d in out.groupby("run_id")}
    rows = []
    for r in out.itertuples(index=False):
        if r.status != "ok":
            rows.append(_r(assessment="not_computed", text=r.reason or ""))
            continue
        ctx = json.loads(r.context) if isinstance(r.context, str) else (r.context or {})
        rows.append(assess(r.name, r.value, ctx, peers.get(r.run_id, {})))
    res = pd.concat([out.reset_index(drop=True), pd.DataFrame(rows, columns=COLUMNS)], axis=1)
    return apply_multiplicity(res, peers)


# D-143: keluarga perbandingan yang dikoreksi BH per run. Uji resmi praregistrasi (rasio MAE M0/M2/M3 vs M1 dari
# forecast_eval, H5 dengan Holm sendiri) dan hipotesis tunggal (Kendall, laju vs α) tidak dimasukkan.
FAMILIES = {
    "beda akurasi berpasangan": re.compile(r"_accuracy_diff$"),
    "metrik arah vs acuan": re.compile(r"_dir_(accuracy|balanced_accuracy|f1_macro|mcc|roc_auc|pr_auc)$"),
    "rasio MAE model eksploratif": re.compile(r"^(mae_ratio_vs_m1_h\d+_(?!(M0|M1|M2|M3|M2_nofx)$)\w+"
                                             r"|mae_ratio_h\d+_\w+_vs_\w+)$"),
}
FDR_Q = 0.05


def _family_p(name: str, ctx: dict, peers: dict) -> float | None:
    if name.startswith("mae_ratio"):
        p = _num(ctx.get("dm_p"))
        if p is None:
            m = re.match(r"^mae_ratio_vs_m1_h(\d+)_(\w+)$", name)
            p = _num(peers.get(f"dm_p_h{m.group(1)}_{m.group(2)}")) if m else None
        return p
    return _num(ctx.get("p_boot"))


def apply_multiplicity(table: pd.DataFrame, peers: dict | None = None) -> pd.DataFrame:
    """D-143. Koreksi Benjamini–Hochberg (q < 0,05) per keluarga perbandingan per run: hasil "lebih baik/buruk dari acuan"
    yang q-nya ≥ 0,05 diturunkan menjadi "belum terbukti berbeda" dengan alasan di interpretasi. Kolom baru: family,
    p_value, q_value. Metrik tanpa p (log lama) tetap dinilai tanpa koreksi dan diberi catatan."""
    from kagami.stats.meta import bh_fdr

    out = table.copy()
    out["family"], out["p_value"], out["q_value"] = None, np.nan, np.nan
    if out.empty:
        return out
    peers = peers or {}
    for fam, pat in FAMILIES.items():
        mask = (out["status"] == "ok") & out["name"].map(lambda n: bool(pat.search(n)))
        out.loc[mask, "family"] = fam
        for rid, d in out[mask].groupby("run_id"):
            ps = []
            for i, r in d.iterrows():
                ctx = json.loads(r["context"]) if isinstance(r["context"], str) else (r["context"] or {})
                ps.append((i, _family_p(r["name"], ctx, peers.get(rid, {}))))
            have = [(i, p) for i, p in ps if p is not None]
            if have:
                q = bh_fdr(np.array([p for _, p in have]))
                for (i, p), qi in zip(have, q):
                    out.at[i, "p_value"], out.at[i, "q_value"] = p, float(qi)
                    if out.at[i, "assessment"] in ("better", "worse") and qi >= FDR_Q:
                        out.at[i, "assessment"] = "inconclusive"
                        out.at[i, "interpretation"] = (f"{out.at[i, 'interpretation']}; tidak lolos koreksi BH keluarga "
                                                       f"'{fam}' (q {_f(float(qi))}, {len(have)} uji)")
                    elif out.at[i, "assessment"] in ("better", "worse"):
                        out.at[i, "interpretation"] = f"{out.at[i, 'interpretation']}; lolos BH (q {_f(float(qi))})"
            for i, p in ps:
                if p is None and out.at[i, "assessment"] in ("better", "worse"):
                    out.at[i, "interpretation"] = f"{out.at[i, 'interpretation']}; tanpa koreksi multiplisitas (log lama)"
    return out
