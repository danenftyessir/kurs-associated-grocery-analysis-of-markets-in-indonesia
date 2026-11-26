"""D-156: registri eksperimen terpusat Task 4 klasifikasi arah (D-145 … D-156) → hasil/registry.csv.

Satu baris = satu eksperimen/varian. Angka D-145/D-146 disalin dari laporan bertanggal (tabel dev); D-147–D-152 dibaca dari CSV hasil
masing-masing; D-156 dari e_metrics.csv & e_decision.csv. Δ = macro F1 varian − pembanding pada baris & origin dev yang sama
(origin + h ≤ 2023-12-31), kecuali dicatat. Status: COMPLETE (dijalankan penuh, dipakai sebagai acuan/diadopsi atau hasil dicatat),
PARTIAL (dijalankan dengan pemangkasan), FAILED (eksekusi gagal), BLOCKED (tidak dapat dijalankan), REJECTED (dijalankan, ditolak aturan/gerbang).
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "..", "hasil")
DATA = "PIHPS v2 + penggerak (raw:c96ce7572b4c); tabel resmi feature_table + price_dynamics.extend_table"
DEV = "dev: origin + h ≤ 2023-12-31 (38 / 37 origin)"
C1T = "HGB TUNED_HGB (lr 0,0281, 250 iter, 23 daun, min_leaf 319, l2 3,85, max_features 0,335), seed 20261121"
rows = []


def add(eid, dec, phase, hyp, feat, prep, model, thr, f4=np.nan, f8=np.nan, d4=np.nan, d8=np.nan, ci4="", ci8="", status="REJECTED",
        decision="", rationale="", repro="", hp="", data=DATA, origins=DEV, cls=""):
    rows.append({"experiment_id": eid, "decision_ref": dec, "phase": phase, "hypothesis": hyp, "data_version": data,
                 "feature_config": feat, "preprocessing_config": prep, "model_config": model, "hyperparameters": hp,
                 "threshold": thr, "dev_origins": origins, "macro_f1_h4": f4, "macro_f1_h8": f8, "per_class_f1": cls,
                 "delta_vs_c1t_h4": d4, "delta_vs_c1t_h8": d8, "ci_h4": ci4, "ci_h8": ci8, "status": status,
                 "reproducibility": repro, "decision": decision, "rationale": rationale})


def ci(lo, hi):
    return f"{lo:+.4f}..{hi:+.4f}"


R1 = "docs/audit/20261124_task4_optimasi_arah/scripts (ablation.py, tune_hgb.py, final_*.py)"
# ---------------- D-145 (ronde 1) — pembanding Δ = vs C1 resmi untuk ablation; dev
abl = pd.read_csv(os.path.join(AUD, "20261124_task4_optimasi_arah", "hasil", "ablation.csv"))
c1 = abl.set_index("config").loc["C1_base"]
for _, r in abl[abl["config"] != "C1_base"].iterrows():
    dropped = r["config"] in ("+vol", "+cf", "all-vol", "all-cf")
    add(f"D145-A1{r['config']}", "D-145", "C fitur", "kelompok fitur harga menambah informasi di atas C1 resmi",
        r["config"], "resmi", "HGB params.forecast.hgb", "0,5", r["f1_h4"], r["f1_h8"],
        r["f1_h4"] - c1["f1_h4"], r["f1_h8"] - c1["f1_h8"], status="REJECTED" if dropped else "COMPLETE",
        decision="kelompok dibuang (vol, cf)" if dropped else "ablation seleksi (kelompok dipertahankan)",
        rationale="Δ vs C1 resmi (bukan vs C1t); aturan hapus-satu dari 'all' → buang vol & cf", repro=R1)
add("D145-T1 C1-tuned", "D-145", "D/E optimasi", "fitur terpilih + Optuna HGB", "base + lag, rmean, rstd, mom, season, dev, comm + id",
    "resmi", "HGB", "0,5 (thr dev 0,50 / 0,46 tidak menambah)", 0.656, 0.676, 0, 0, status="COMPLETE", decision="BASELINE (C1-tuned)",
    rationale="test 0,677 / 0,680; seed 2/3 ± 0,003", hp=C1T + "; Optuna TPE 40 trial (ruang: lr, iter, daun, min_leaf, l2, max_features, bobot seimbang, peluruhan 0/1/2/4 th)", repro=R1)
add("D145-T2 C2-tuned", "D-145", "C fitur", "fitur kurs & harga dunia menambah", "C1t + fx", "resmi", "HGB (hp C1t)", "dev 0,505 / 0,475",
    status="PARTIAL", decision="ditolak", rationale="12 dari 25 trial (waktu); test Δ −0,004 / +0,001 (belum terbukti) → kurs tidak membantu", repro=R1)
add("D145-T3 TSMixer-tuned", "D-145", "E model", "TSMixer dengan tuning/BCE lebih baik", "deret harga", "resmi", "TSMixer", "0 / dev",
    status="PARTIAL", decision="ditolak", rationale="10 trial; test −0,014 / −0,011 vs TSMixer resmi; jauh di bawah C1t", repro=R1)
add("D145-TH threshold", "D-145", "D threshold", "threshold dari dev menaikkan F1", "C1t", "resmi", "HGB", "dev 0,50 / 0,46", status="REJECTED",
    decision="ditolak", rationale="C1t: test Δ 0 / −0,005 (belum terbukti)", repro=R1)
add("D145-H TFM-head", "D-145", "E model", "TimesFM → fitur → CatBoost menambah informasi", "TimesFM ramalan + fitur + OOF C1t",
    "resmi", "CatBoost depth 4, lr 0,05, 400 iter", "dev", 0.643, 0.653, status="PARTIAL", decision="ditolak",
    rationale="grid dipangkas; dev 28 origin; test vs C1t −0,005 / +0,002 (belum terbukti)", repro=R1)
# ---------------- D-146 (ronde 2)
R2 = "docs/audit/20261125_task4_ronde2/scripts (ablation2.py, models2.py), colab/"
a2 = pd.read_csv(os.path.join(AUD, "20261125_task4_ronde2", "hasil", "ablation2.csv"))
for _, r in a2[a2["config"] != "S"].iterrows():
    add(f"D146-{r['config']}", "D-146", "C fitur", "fitur regulasi/spasial/kalender/prior/level menambah", r["config"], "resmi",
        "HGB (hp C1t)", "0,5", r["f1_h4"], r["f1_h8"], r["d_h4"], r["d_h8"], ci(r["lo_h4"], r["hi_h4"]), ci(r["lo_h8"], r["hi_h8"]),
        decision="ditolak", rationale="Δ ≤ 0 atau interval memuat 0; prior & all2 memperburuk h 8", repro=R2)
for m, d4, d8 in (("LightGBM default", -0.0044, -0.006), ("XGBoost default", -0.0058, -0.004), ("ensemble HGB+LGB+XGB", -0.0021, -0.003),
                  ("spesialis kelompok komoditas", -0.0095, -0.015)):
    add(f"D146-{m}", "D-146", "E model", "model lain/spesialis lebih baik", "C1t", "resmi", m, "0,5", d4=d4, d8=d8,
        decision="ditolak", rationale="belum terbukti / lebih buruk (spesialis h 8 p 0,049)", repro=R2)
add("D146-tiga kelas", "D-146", "D target", "target 3 kelas (tetap/naik/turun)", "C1t + cf + vol", "resmi", "dua tahap HGB", "τ dev 0,67 / 0,70",
    status="COMPLETE", decision="dilaporkan terpisah", rationale="target berbeda (dilarang menggantikan label resmi); test 0,625 / 0,606", repro=R2)
tcn = pd.read_csv(os.path.join(AUD, "20261125_task4_ronde2", "hasil", "tcn_mlp_dev.csv"))
for m, g in tcn[tcn["model"] != "C1t"].assign(base=lambda d: d["model"].str.rsplit("_r", n=1).str[0]).groupby("base"):
    a, b = g[g["h"] == 4], g[g["h"] == 8]
    add(f"D146-{m} (3 seed)", "D-146", "E model", "TCN/MLP multi-task menangkap pola deret", "jendela 104 minggu ± tabular", "resmi",
        f"{m} Colab T4", "0,5", a["macro_f1_dev"].mean(), b["macro_f1_dev"].mean(), a["diff_vs_C1t"].mean(), b["diff_vs_C1t"].mean(),
        decision="ditolak", rationale="semua seed di bawah C1t", repro=R2)
add("D146-TCN percobaan 1", "D-146", "E model", "TCN di GPU", "-", "-", "TCN", "-", status="FAILED", decision="diulang",
    rationale="GPU Colab penuh → tersambung ke CPU; dihentikan dan diulang di akun lain", repro=R2)
# ---------------- D-147 (audit preprocessing)
R3 = "docs/audit/20261125_task4_audit_preprocessing/scripts (prep.py, p_exp.py, p_eval.py)"
px = pd.read_csv(os.path.join(AUD, "20261125_task4_audit_preprocessing", "hasil", "exp_dev_paired.csv")).pivot(index="variant", columns="horizon")
for v, r in px.iterrows():
    add(f"D147-{v}", "D-147", "B preprocessing", "perlakuan preprocessing/label latih memperbaiki generalisasi", v, v, "HGB C1t", "0,5",
        d4=r[("diff", 4)], d8=r[("diff", 8)], ci4=ci(r[("lo", 4)], r[("hi", 4)]), ci8=ci(r[("lo", 8)], r[("hi", 8)]),
        status="COMPLETE" if v == "P04_intraweek" else "REJECTED",
        decision="buka test: +0,004 / +0,005 (q 0,35 / 0,089), tidak diadopsi" if v == "P04_intraweek" else "ditolak", repro=R3)
add("D147-P02 agregasi pasar", "D-147", "B preprocessing", "kohort pasar tetap mengurangi derau komposisi", "-", "kohort pasar", "-", "-",
    status="BLOCKED", decision="tidak dapat dijalankan", rationale="data per pasar/kota tidak ada di repo")
# ---------------- D-148 / D-149
R4 = "docs/audit/20261125_task4_ronde4/scripts"
for f, dec, tag in (("r4_dev_paired.csv", "D-148", "dev ≤ 2023"), ("r4s2_dev_paired.csv", "D-149", "dev ≤ 2024 (pasca-hoc)")):
    t = pd.read_csv(os.path.join(AUD, "20261125_task4_ronde4", "hasil", f)).pivot(index="variant", columns="horizon")
    for v, r in t.iterrows():
        add(f"{dec}-{v}", dec, "C fitur", "fitur sadar-rezim (base rate terealisasi, umur kebijakan, jarak acuan) mengatasi drift", v, "resmi",
            "HGB C1t", "0,5", d4=r[("diff", 4)], d8=r[("diff", 8)], ci4=ci(r[("lo", 4)], r[("hi", 4)]), ci8=ci(r[("lo", 8)], r[("hi", 8)]),
            origins=tag, decision="ditolak", rationale="tidak lolos origin pengembangan", repro=R4)
for f, dec, tag in (("cal_dev_paired.csv", "D-148", "dev ≤ 2023"), ("cal_dev_paired_s2.csv", "D-149", "dev ≤ 2024 (pasca-hoc)")):
    t = pd.read_csv(os.path.join(AUD, "20261125_task4_ronde4", "hasil", f)).pivot(index="config", columns="horizon")
    for v, r in t.iterrows():
        add(f"{dec}-cal-{v}", dec, "D kalibrasi", "kalibrasi temporal (intercept/prior) mengoreksi drift base rate", "C1t", "resmi",
            "HGB C1t + kalibrasi walk-forward", "0,5 setelah kalibrasi", d4=r[("diff", 4)], d8=r[("diff", 8)],
            ci4=ci(r[("lo", 4)], r[("hi", 4)]), ci8=ci(r[("lo", 8)], r[("hi", 8)]), origins=tag, decision="ditolak", repro=R4)
# ---------------- D-150 / D-151 / D-152
for fam, path, dec, hyp, R in (
        ("W", ("20261125_pilot_grosir", "ws_dev_paired.csv"), "D-150", "harga pedagang besar mendahului eceran", "docs/audit/20261125_pilot_grosir"),
        ("IW", ("20261125_pilot_produsen_intraminggu", "iw_dev_paired.csv"), "D-151", "posisi harga dalam minggu origin", "docs/audit/20261125_pilot_produsen_intraminggu"),
        ("PR", ("20261125_pilot_produsen_intraminggu", "pr_dev_paired.csv"), "D-151", "harga produsen mendahului eceran", "docs/audit/20261125_pilot_produsen_intraminggu")):
    t = pd.read_csv(os.path.join(AUD, path[0], "hasil", path[1])).pivot(index="variant", columns="horizon")
    for v, r in t.iterrows():
        st, dc = "REJECTED", "ditolak"
        if v == "IW_NAT":
            st, dc = "COMPLETE", "buka test: +0,0085 / +0,0033 (q 0,28 / 0,30), belum terbukti; tidak diadopsi; prediksi maju beku (D-152)"
        elif v == "IW_REF":
            st, dc = "COMPLETE", "referensi (bukan kandidat)"
        add(f"{dec}-{v}", dec, "C fitur", hyp, v, "resmi + data harian/hulu", "HGB C1t", "0,5", d4=r[("diff", 4)], d8=r[("diff", 8)],
            ci4=ci(r[("lo", 4)], r[("hi", 4)]), ci8=ci(r[("lo", 8)], r[("hi", 8)]), status=st, decision=dc, repro=R)
dg = pd.read_csv(os.path.join(AUD, "20261125_iw_validasi", "hasil", "diag_dev_paired.csv"))
dg = dg[dg["vs"] == "base"].pivot(index="variant", columns="horizon")
for v, r in dg.iterrows():
    add(f"D-152-{v}", "D-152", "C diagnostik", "dari mana sinyal intraminggu berasal", v, "resmi + harian", "HGB C1t", "0,5",
        d4=r[("diff", 4)], d8=r[("diff", 8)], ci4=ci(r[("lo", 4)], r[("hi", 4)]), ci8=ci(r[("lo", 8)], r[("hi", 8)]), status="COMPLETE",
        decision="diagnostik", rationale="LOO ≈ rerata nasional; tanpa Jumat −0,010 h 4", repro="docs/audit/20261125_iw_validasi/scripts")
for v, txt in (("DU-1 pola lintas komoditas", "0/360 lolos BH"), ("DU-2 clustering seri", "tidak menjelaskan skill di luar komoditas"),
               ("DU-3 graf provinsi", "ρ parsial 0,021–0,025 ≈ 1/5 kontrol positif")):
    add(f"D-153-{v}", "D-153", "C layar DU", "sumber informasi baru", v, "-", "tanpa model", "-", status="REJECTED",
        decision="tidak lolos gerbang DU", rationale=txt, repro="docs/audit/20261125_crisp_du/scripts")
add("U110 vintage revisi PIHPS", "D-155", "B preprocessing", "revisi harga harian memengaruhi fitur/label", "-", "vintage", "-", "-",
    status="BLOCKED", decision="tidak dapat diuji", rationale="vintage revisi PIHPS tidak tersedia; available_at konservatif Minggu 00.00 ([HUMAN] U110)")

# ---------------- D-156
D156 = "docs/audit/20261126_task4_master_f1/scripts (c_feats.py, m_run.py, e_eval.py)"
M = pd.read_csv(os.path.join(OUT, "e_metrics.csv"))
dec = pd.read_csv(os.path.join(OUT, "e_decision.csv"), index_col=0)
HYP = {"B_recency": "bobot peluruhan 104 minggu menyesuaikan drift", "B_win156": "jendela latih 3 tahun menyesuaikan drift",
       "C_A": "momentum tambahan (Δ 2/12 minggu, akselerasi 8, reversal, persistensi 26)", "C_B": "volatilitas & frekuensi perubahan",
       "C_C": "posisi harga (z-score, median, persentil, jarak maks/min)", "C_D1": "kualitas data panel (umur carry-forward, minggu hilang)",
       "C_D2": "cakupan hari teramati (pihps_daily)", "C_E": "lintas provinsi LOO, rank", "C_F": "kalender Iduladha/Natal/Ramadan + musiman ekspansif",
       "C_G": "interaksi/normalisasi volatilitas", "D_cw": "bobot kelas seimbang", "D_seed5": "rerata 5 seed mengurangi varians",
       "D_thr_wf": "threshold global walk-forward", "D_thr_wf_comm": "threshold per komoditas walk-forward",
       "E_lgb": "LightGBM (konfigurasi dipetakan)", "E_xgb": "XGBoost (konfigurasi dipetakan)", "E_cat": "CatBoost", "E_et": "ExtraTrees",
       "E_lr": "regresi logistik (diagnostik)", "C_COMBO": "gabungan keluarga terpilih di dev-awal"}
for v, g in M[(M["variant"] != "base") & ~M["variant"].str.endswith("_biased")].groupby("variant"):
    a, b = g[g["horizon"] == 4].iloc[0], g[g["horizon"] == 8].iloc[0]
    hyp = HYP.get(v, f"hapus kelompok {v.replace('C_rm_', '')} dari C1t (seleksi fitur)" if v.startswith("C_rm_") else v)
    d = dec.loc[v]
    passed = bool(d["pass_all"])
    fails = [k for k in ("r1_effect", "r2_bh", "r3_consistent", "r4_no_hidden", "selectable") if not bool(d[k])]
    add(f"D156-{v}", "D-156", {"B": "B preprocessing", "C": "C fitur", "D": "D klasifikasi", "E": "E model"}[v[0]], hyp, v,
        "resmi (tabel fam.parquet)" if not v.startswith("B_") else v, "HGB C1t" if not v.startswith("E_") else v, "walk-forward" if v.startswith("D_thr") else "0,5",
        a["macro_f1"], b["macro_f1"], a["diff"], b["diff"], ci(a["lo"], a["hi"]), ci(b["lo"], b["hi"]),
        status="COMPLETE" if passed else "REJECTED", decision="lolos §5" if passed else "ditolak (" + ", ".join(fails) + ")",
        rationale=f"q BH {a['q_bh']:.3f} / {b['q_bh']:.3f}; origin Δ>0 {a['share_origins_pos']:.2f} / {b['share_origins_pos']:.2f}; Δ kuintil kecil {a['d_q1_small']:+.3f} / {b['d_q1_small']:+.3f}",
        cls=f"naik {a['f1_up']:.3f}/{b['f1_up']:.3f}; turun {a['f1_down']:.3f}/{b['f1_down']:.3f}", repro=D156,
        origins="dev-akhir (origin ≥ 2022-07-01)" if v == "C_COMBO" else DEV,
        hp=C1T if not v.startswith("E_") else "lihat PROTOKOL §3")
# ---------------- D-157 (pilot cuaca sentra & impor)
P157 = os.path.join(AUD, "20261126_pilot_cuaca_impor", "hasil")
if os.path.exists(os.path.join(P157, "ev_metrics.csv")):
    D157 = "docs/audit/20261126_pilot_cuaca_impor/scripts (fetch_power.py, feats_wi.py, build_wi.py, run_wi.py, ev_wi.py, cal_wi.py)"
    em = pd.read_csv(os.path.join(P157, "ev_metrics.csv"))
    ed = pd.read_csv(os.path.join(P157, "ev_decision.csv"), index_col=0)
    hyp = {"W_NAT": "anomali cuaca di sentra produksi (tertimbang porsi produksi ATAP) mendahului arah harga hortikultura",
           "W_LOC": "W_NAT + cuaca titik provinsi sendiri", "IMP": "realisasi impor bulanan (rilis +45 hari) memberi sinyal pasokan"}
    for v in ("W_NAT", "W_LOC", "IMP"):
        g = em[(em["variant"] == v) & (em["scope"] == "semua")]
        s = em[(em["variant"] == v) & (em["scope"] == "sasaran")]
        a, b = g[g["horizon"] == 4].iloc[0], g[g["horizon"] == 8].iloc[0]
        sa, sb = s[s["horizon"] == 4].iloc[0], s[s["horizon"] == 8].iloc[0]
        fails = [k for k in ("r1", "r2", "r3", "r4") if not bool(ed.loc[v, k])]
        add(f"D157-{v}", "D-157", "C fitur (sumber baru)", hyp[v], v, "resmi + nasa_power" if v != "IMP" else "resmi + comtrade/bps impor",
            "HGB C1t", "0,5", a["macro_f1"], b["macro_f1"], a["diff"], b["diff"], ci(a["lo"], a["hi"]), ci(b["lo"], b["hi"]),
            decision="ditolak (" + ", ".join(fails) + ")", hp=C1T, repro=D157,
            rationale=f"kelompok sasaran Δ {sa['diff']:+.4f} / {sb['diff']:+.4f}; q BH {a['q_bh']:.3f} / {b['q_bh']:.3f}; layar DU tidak lolos",
            cls=f"naik {a['f1_up']:.3f}/{b['f1_up']:.3f}; turun {a['f1_down']:.3f}/{b['f1_down']:.3f}")
    cw_ = pd.read_csv(os.path.join(P157, "cal_wi.csv"))
    c4, c8 = (cw_[(cw_["scope"] == "semua") & (cw_["horizon"] == h)].iloc[0] for h in (4, 8))
    add("D157-W_CAL (pasca-hoc)", "D-157", "D kalibrasi", "koreksi logit tahap-2 walk-forward dengan anomali suhu maks & hujan 91 hari",
        "C1t + 2 koefisien", "resmi + nasa_power", "HGB C1t + logit offset", "0,5", c4["macro_f1"], c8["macro_f1"], c4["diff"], c8["diff"],
        ci(c4["lo"], c4["hi"]), ci(c8["lo"], c8["hi"]), decision="ditolak", repro=D157, origins="dev, origin dengan ≥ 8 origin riwayat (30 / 28)",
        rationale="pasca-hoc (dipilih dari DU dev); koefisien bertanda sesuai tetapi tidak stabil; hortikultura −0,009 / −0,016")
# ---------------- D-158 (National Shock Nowcasting: breadth kota + nasional–lokal, 2 iterasi)
P158 = os.path.join(AUD, "20261126_nasional_lokal", "hasil")
if os.path.exists(os.path.join(P158, "ev_i2_i2meta_metrics.csv")):
    D158 = "docs/audit/20261126_nasional_lokal/scripts"
    HYP158 = {"NL1": "lapisan nasional walk-forward (share_up) sebagai fitur C1t", "NL2": "NL1 + kepengikutan provinsi terhadap arah nasional",
              "NL_BR": "lapisan nasional dengan breadth kota", "BR_NAT": "breadth pasar 110 kota nasional (9 fitur)",
              "BR_LOC": "BR_NAT + breadth kota dalam provinsi", "FR_REF": "acuan: intraminggu provinsi + rerata nasionalnya (≈ IW_NAT)",
              "FR_CITY": "FR_REF + breadth intraminggu 110 kota", "BR1": "kb_up_1 saja (parsimoni)",
              "META_FR": "koreksi nasional increment-only di atas konsensus C1t (intraminggu kota + nasional)",
              "META_CITY": "koreksi nasional increment-only (intraminggu kota saja)", "META_IW": "acuan: koreksi nasional increment-only (iw_gap_nat)"}
    for f, it in (("ev_nl_br", "iterasi 1"), ("ev_i2_i2meta", "iterasi 2")):
        em = pd.read_csv(os.path.join(P158, f"{f}_metrics.csv"))
        ed = pd.read_csv(os.path.join(P158, f"{f}_decision.csv"), index_col=0)
        for v, g in em.groupby("variant"):
            a, b = g[g["horizon"] == 4].iloc[0], g[g["horizon"] == 8].iloc[0]
            ref = v in ("FR_REF", "META_IW")
            passed = bool(ed.loc[v, "pass_all"])
            fails = [k for k in ("r1", "r2", "r3", "r4") if not bool(ed.loc[v, k])]
            dec = ("acuan (tidak dapat dipilih); lolos aturan" if passed else "acuan") if ref else (
                "lolos aturan; TIDAK diadopsi: kenaikan = keluarga intraminggu (FR_CITY − FR_REF −0,000 / +0,004, belum terbukti); prediksi maju beku"
                if passed else "ditolak (" + ", ".join(fails) + ")")
            add(f"D158-{v}", "D-158", f"{it} — " + ("B nasional–lokal" if v.startswith(("NL", "META")) else "A breadth/kesegaran kota"),
                HYP158.get(v, v), v, "resmi + pihps_city" if not v.startswith("NL") or v == "NL_BR" else "resmi",
                "HGB C1t" if not v.startswith("META") else "C1t + koreksi logit 2 lapis", "0,5", a["macro_f1"], b["macro_f1"], a["diff"], b["diff"],
                ci(a["lo"], a["hi"]), ci(b["lo"], b["hi"]), status="COMPLETE" if (passed or ref) else "REJECTED", decision=dec, repro=D158,
                rationale=f"q BH {a['q_bh']:.3f} / {b['q_bh']:.3f}; origin Δ>0 {a['share_origins_pos']:.2f} / {b['share_origins_pos']:.2f}"
                + ("; dijalankan ulang sesudah perbaikan kebocoran cakupan (kb_cov, kp_n)" if v in ("BR_NAT", "BR_LOC", "NL_BR") else ""),
                cls=f"naik {a['f1_up']:.3f}/{b['f1_up']:.3f}; turun {a['f1_down']:.3f}/{b['f1_down']:.3f}")
    for v, txt in (("kalibrasi ulang konsensus nasional (+ dummy komoditas)", "AUC arah nasional 0,742 / 0,698 vs konsensus C1t 0,762 / 0,755 (lebih buruk)"),
                   ("increment dinamika konsensus & galat terakhir", "AUC 0,751 / 0,751 vs 0,762 / 0,755"),
                   ("kota pemimpin (K 5/10/20, walk-forward)", "AUC −0,03..−0,04 vs konsensus; korelasi indeks–galat 0,03–0,09"),
                   ("penyusutan baris ragu ke konsensus C1t", "akurasi baris ragu sendiri 0,536 / 0,544 > konsensus 0,485 / 0,535; macro F1 turun monoton")):
        add(f"D158-DU-{v}", "D-158", "layar DU iterasi 2", "memperbaiki arah nasional di atas konsensus C1t", v, "-", "tanpa model provinsi", "-",
            status="REJECTED", decision="tidak lolos layar DU (tidak dimodelkan)", rationale=txt, repro=D158, origins="dev 2021–2023 (mingguan)")
    add("D158-Bapanas panel kab/kota", "D-158", "audit data", "panel harga kab/kota Bapanas untuk breadth", "-", "-", "-", "-",
        status="BLOCKED", decision="tidak dapat dipakai", repro="docs/audit/20261126_nasional_lokal.md §1",
        rationale="portal tanpa unduhan/riwayat (harga tidak termuat 2026-11-26); dataset via SAPA (akses terbatas); repo hanya panel bulanan provinsi 2022+")
# ---------------- D-159 (audit kelayakan pasokan fisik; tanpa modeling)
for v, st, txt in (
        ("SP2KP stok/pasokan pasar", "BLOCKED", "stok mingguan hanya di area admin berlogin; riwayat & tanggal penutupan tidak diketahui → permintaan resmi U112"),
        ("FDP arus distribusi", "REJECTED", "log program stabilisasi (39 pengiriman 2026, 0,3–50 t); seri 2024+; bulanan B+1"),
        ("PIBC stok/masuk/keluar Cipinang", "BLOCKED", "endpoint publik 1 rekaman (01 Jun 2025); portal tidak diperbarui; data internal Food Station"),
        ("GPM intervensi per kab/kota", "REJECTED", "bulanan tanpa tanggal kegiatan, 2024+, vintage tarikan; kausalitas terbalik; kosong di seluruh dev"),
        ("KSA luas panen padi", "REJECTED", "hanya beras (informasi sempurna ≤ +0,007); prakiraan historis tidak tersimpan (ditimpa)")):
    add(f"D159-{v}", "D-159", "audit data (fase 1)", "kuantitas pasokan/stok mendahului harga", v, "-", "-", "-", status=st,
        decision="tidak dimodelkan (syarat berhenti)", rationale=txt, repro="docs/audit/20261126_pasokan_fisik.md", origins="-")
# ---------------- D-160 (kelayakan sumber & penemuan sinyal; tanpa modeling provinsi)
for v, st, txt in (
        ("GDELT GKG (berita gangguan pasokan)", "BLOCKED", "G1–G3 ✓; G4/G5 tidak teruji: ± 210 ribu berkas GKG 2018–2023 (skala TB) atau BigQuery berbayar [HUMAN] (U113)"),
        ("NOAA CFSv2 prakiraan operasional", "BLOCKED", "G1–G3 ✓; layanan subset rusak (NCSS 404, OPeNDAP 403); berkas penuh 42,6 MB/variabel/run → 8–37 GB + eccodes, di luar cakupan persetujuan"),
        ("SIJAGUNG stok & pembelian jagung pabrik pakan", "REJECTED", "G5 gagal: residual |ρ| ≤ 0,11 (q ≥ 0,65); AUC arah nasional increment-only −0,01..−0,21 vs konsensus C1t (ayam & telur)"),
        ("SPORA harga pakan", "BLOCKED", "ekspor publik HTTP 500 (memori server) untuk semua rentang"),
        ("BNPB DIBI kejadian bencana", "BLOCKED", "G2 sebagian (tanggal kejadian saja, verifikasi triwulanan); G5 tidak teruji: server HTTP 521 saat uji")):
    add(f"D160-{v}", "D-160", "kelayakan sumber & sinyal", "informasi non-harga yang mendahului arah nasional", v, "-",
        "increment-only di atas konsensus C1t (G5)" if v.startswith("SIJAGUNG") else "-", "-", status=st,
        decision="tidak dimodelkan", rationale=txt, repro="docs/audit/20261126_sumber_baru.md", origins="dev 2021–2023 (mingguan)")
# ---------------- D-161 (CFSv2 lewat Colab: gerbang 5 + oracle cuaca terealisasi; tanpa modeling provinsi)
_N = pd.read_csv(os.path.join(AUD, "20261126_sumber_baru", "hasil", "cfs_du_national.csv"))
for kind, st, dec_ in (("CFSv2", "REJECTED", "tidak dimodelkan (G5 gagal)"), ("ORACLE", "COMPLETE", "diagnostik batas atas; bukan kandidat")):
    for sset, g in _N[_N["kind"] == kind].groupby("set", sort=False):
        a, b = g.set_index("horizon").loc[4], g.set_index("horizon").loc[8]
        add(f"D161-{kind}-{sset}", "D-161", "kelayakan sumber & sinyal (G5)",
            "prakiraan cuaca 1–8 minggu di sentra hortikultura menambah arah nasional di atas konsensus C1t" if kind == "CFSv2"
            else "cuaca TERREALISASI pada jendela prakiraan (oracle) menambah arah nasional di atas konsensus C1t",
            f"{'cn' if kind == 'CFSv2' else 'on'}_* set {sset} (nasional tertimbang produksi ATAP; cabai merah/rawit, bawang merah)",
            "anomali vs klimatologi init ≤ 2020-12-31 (± 14 hari)", "increment-only offset logit konsensus C1t, walk-forward 4 minggu", "-",
            ci4=f"ΔAUC {a['d_auc']:+.4f} ({a['lo']:+.4f}..{a['hi']:+.4f})", ci8=f"ΔAUC {b['d_auc']:+.4f} ({b['lo']:+.4f}..{b['hi']:+.4f})",
            status=st, decision=dec_, rationale=f"AUC konsensus {a['auc_cons']:.3f}/{b['auc_cons']:.3f}; q BH {a['q_bh']:.3f}/{b['q_bh']:.3f}; aturan G5 tidak terpenuhi",
            repro="docs/audit/20261126_sumber_baru/scripts/cfs_du.py; colab/kagami_d160_cfsv2.ipynb", origins="minggu 2021-01-04 .. 2023-12-31 − h (mingguan)",
            data="NOAA CFSv2 operasional (437 run 00Z Jumat/Kamis/Rabu) + NASA POWER" if kind == "ORACLE" else "NOAA CFSv2 operasional (437 run 00Z Jumat/Kamis/Rabu)")
# ---------------- D-163a (kalibrasi walk-forward skor daftar pantau C1-tuned; pasca-model, tanpa fitur baru)
_K = pd.read_csv(os.path.join(AUD, "20261126_kalibrasi_pantau", "hasil", "kal_dev.csv"))
_KDESC = {"K1": "Platt global per horizon", "K2": "Platt + intersep komoditas", "K3": "isotonik global per horizon"}
for kind, desc in _KDESC.items():
    a, b = _K[(_K["variant"] == kind) & (_K["horizon"] == 4)].iloc[0], _K[(_K["variant"] == kind) & (_K["horizon"] == 8)].iloc[0]
    add(f"D163a-{kind}", "D-163", "kalibrasi pasca-model (S2)", "kalibrasi walk-forward menurunkan ECE & Brier tanpa merusak daftar pantau",
        "C1-tuned beku (p_up)", "-", f"{desc} atas logit p_up; latih origin o' + h <= o, y != 0, >= 6 origin", "0,5 (informasi)",
        f4=a["macro_f1_05"], f8=b["macro_f1_05"], d4=a["macro_f1_05"] - 0.656, d8=b["macro_f1_05"] - 0.676,
        ci4=f"ECE {a['ece']:.3f}; ΔBrier {a['d_brier']:+.4f} ({a['d_brier_lo']:+.4f}..{a['d_brier_hi']:+.4f}); ΔS1 {a['d_s1_prec']:+.3f}",
        ci8=f"ECE {b['ece']:.3f}; ΔBrier {b['d_brier']:+.4f} ({b['d_brier_lo']:+.4f}..{b['d_brier_hi']:+.4f}); ΔS1 {b['d_s1_prec']:+.3f} ({b['d_s1_lo']:+.3f}..{b['d_s1_hi']:+.3f})",
        status="REJECTED", decision="tidak dipakai (aturan protokol: ECE ≤ 0,05 & ΔBrier < 0 & S1 tidak turun)",
        rationale="ECE turun tetapi Brier tidak membaik (pergeseran laju naik antarperiode tidak dapat dipelajari dari origin lampau)"
                  + ("; K2 menaikkan presisi daftar pantau h 8 tetapi memperburuk peluang — petunjuk untuk kartu K4 (U109)" if kind == "K2" else ""),
        repro="docs/audit/20261126_kalibrasi_pantau/scripts/kal.py (PROTOKOL.md sha256 e0b50c8f…)")
R = pd.DataFrame(rows)
for c in ("macro_f1_h4", "macro_f1_h8", "delta_vs_c1t_h4", "delta_vs_c1t_h8"):
    R[c] = R[c].astype(float).round(4)
R[R["decision_ref"] <= "D-156"].to_csv(os.path.join(OUT, "registry.csv"), index=False)   # salinan bertanggal D-156 (117 baris)
LIVE = os.path.abspath(os.path.join(AUD, "..", "eksperimen_registry.csv"))     # registri hidup (EKSPERIMEN.md §6)
R.to_csv(LIVE, index=False, lineterminator="\n")
print(R["status"].value_counts().to_string())
print(len(R), "baris →", os.path.join(OUT, "registry.csv"), "dan", LIVE)
