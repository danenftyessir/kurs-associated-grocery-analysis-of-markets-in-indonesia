"""Jalur A: bangun EXPERIMENT_LOG.csv (satu baris per eksperimen × horizon bila relevan) dari hasil/ — skema permintaan Danen 2026-11-26.
Juga dibaca `20261126_task4_master_f1/scripts/r_registry.py` untuk registri hidup (`docs/eksperimen_registry.csv`).
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..")
H = os.path.join(BASE, "hasil")
COLS = ["experiment_id", "workstream", "hypothesis", "data_source", "availability_timestamp", "feature_family", "preprocessing", "model",
        "horizon", "macro_f1", "f1_up", "f1_down", "roc_auc", "precision_recall", "mcc", "brier_ece", "delta_vs_c1t", "confidence_interval",
        "bh_q", "leakage_audit", "decision", "reason", "script"]
NA = "n/a"
rows = []


def add(**k):
    r = {c: k.get(c, NA) for c in COLS}
    rows.append(r)


fa = json.load(open(os.path.join(H, "a_forward_audit.json"), encoding="utf-8"))
add(experiment_id="JA-A01", workstream="A prospektif",
    hypothesis="IW_NAT / FR_REF tidak gagal besar vs C1-tuned pada origin yang belum pernah dipakai",
    data_source=f"prediksi beku D-152 (sha256 28651b2b…, commit {fa['sources']['D-152']['git_first_commit']}) + D-158 (sha256 7586eaed…, "
                f"commit {fa['sources']['D-158']['git_first_commit']}); PIHPS snapshot berikutnya",
    availability_timestamp="origin 2026-09-28..11-16; target lengkap Jumat t+h: pertama 2026-11-27, semua h4 2026-12-18, semua h8 2027-01-15",
    feature_family="C1t; C1t + intraminggu nasional (IW_NAT, FR_REF); + kota (FR_CITY)", preprocessing="beku D-148", model="HGB TUNED_HGB seed 20261121",
    horizon="4;8", leakage_audit="PASS (hash cocok manifest; base D-152 = D-158; label = definisi resmi, selftest 0 beda)",
    decision="BLOCKED", reason=f"0 target terealisasi pada snapshot {fa['snapshot_last_date']}; evaluator beku (a_protocol_sha256.txt); "
                               "MDE batch 0,08–0,12 / 0,04–0,06 → hanya penjaga kegagalan besar",
    script="scripts/a_forward_audit.py; scripts/a_forward_eval.py")
add(experiment_id="JA-B01", workstream="B GDELT", hypothesis="DOC 2.0 API cukup untuk pilot & hitungan mingguan tanpa biaya",
    data_source="api.gdeltproject.org DOC 2.0", availability_timestamp=NA, decision="BLOCKED",
    reason="HTTP 429 pada 4 percobaan 11.21–15.10 UTC (jeda 100 dtk–3,5 jam); laporan publik Nov 2026 sama", leakage_audit=NA,
    script="(probe manual)")
s = json.load(open(os.path.join(H, "b_gkg_sample_summary.json"), encoding="utf-8"))
m = json.load(open(os.path.join(H, "b_manual_summary.json"), encoding="utf-8"))
add(experiment_id="JA-B02", workstream="B GDELT", hypothesis="GKG Translingual memuat berita pangan Indonesia yang cukup, bertanggal, untuk 2019–2023 (G1–G4)",
    data_source="GDELT GKG 2.1 translation.gkg 48 batch acak 2019–2023 (409 MB, sha256 di b_gkg_sample_files.csv)",
    availability_timestamp="DATE = batch 15 menit GDELT (UTC); lag vs terbit median 0, maks 1 hari",
    feature_family="hitungan artikel per komoditas/kategori", preprocessing="srclc:ind; judul/slug URL; batas kata; dedup judul/hari",
    model=NA, horizon=NA, decision="ACCEPT (G1, G2) / PARTIAL (G3, G4)",
    reason=f"{s['ind_per_batch_mean']:.0f} artikel Indonesia/batch; judul 2019 {s['share_ind_with_title_by_year']['2019']:.2f}, 2020+ ≥ 0,99; "
           f"± {m['implied_per_day_F2d_R']:.0f} relevan/hari; 33% R/P hanya 'bahan pokok'; komoditas selain beras & minyak goreng jarang",
    leakage_audit="PASS (DATE GDELT, bukan tanggal peristiwa)", script="scripts/b_gkg_sample.py")
add(experiment_id="JA-B03", workstream="B GDELT", hypothesis="penyaring kata kunci memisahkan berita pasokan/kebijakan dari derau",
    data_source="111 kandidat JA-B02, label manual (agent, judul/URL)", preprocessing="F0 / F1 / F2 / F2d",
    precision_recall=f"presisi R F0 {m['F0']['precision_R']:.2f}, F1 {m['F1']['precision_R']:.2f}, F2d {m['F2d']['precision_R']:.2f}; "
                     f"R+P F2d {m['F2d']['precision_RP']:.2f}; F2 kehilangan {m['relevant_lost_by_F2']}/24 R",
    decision="ACCEPT (penyaring F2d dipakai di kueri)", reason="salah cocok substring 18% (berasal, lapangan, Pondok Cabe); duplikasi 10%; kaitan komoditas 100%",
    leakage_audit=NA, script="scripts/b_manual_eval.py")
c = pd.read_csv(os.path.join(H, "b_screen_controls.csv"))
for _, r in c.iterrows():
    add(experiment_id=f"JA-B04-{r['set']}-h{int(r['horizon'])}", workstream="B GDELT (kalibrasi layar G5)",
        hypothesis="kontrol positif (kesegaran nasional) terdeteksi; kontrol negatif tidak" if r["set"] == "POS" else "derau tidak terdeteksi",
        data_source="konsensus C1t OOS mingguan (D-158 c1t_weekly) + iw_gap_nat (fresh.parquet)",
        availability_timestamp="harga Senin–Jumat minggu t (available_at Minggu 00.00)", feature_family="iw_gap_nat" if r["set"] == "POS" else "N(0,1)",
        model="increment-only logit offset konsensus, walk-forward 4 minggu", horizon=int(r["horizon"]),
        roc_auc=f"nasional {r['auc_cons']:.4f} → {r['auc_inc']:.4f}", delta_vs_c1t=f"ΔAUC {r['d_auc']:+.4f}",
        confidence_interval=f"{r['lo']:+.4f}..{r['hi']:+.4f}", bh_q=f"{r['q_bh']:.3f}", leakage_audit="PASS (fitur ≤ t; label t' + h ≤ r)",
        decision="ACCEPT (kalibrasi)" if r["set"] == "NEG" else "REJECT (gerbang G5) — temuan daya",
        reason="MDE layar ± 0,023 AUC: sinyal tambahan terbaik yang diketahui tidak lolos G5" if r["set"] == "POS" else "≈ 0 sesuai harapan",
        script="scripts/b_gdelt_screen.py --tag controls")
_G = os.path.join(H, "b_screen_gdelt.csv")
G = pd.read_csv(_G) if os.path.exists(_G) else None
for sset in ["V", "D", "P", "S", "ALL"]:
    kw = dict(workstream="B GDELT (G5)", hypothesis="intensitas berita pasokan/kebijakan menambah arah nasional di atas konsensus C1t",
              data_source="BigQuery gdelt-bq.gdeltv2.gkg_partitioned 2018-12-22..2023-12-31 (job kagami-gdelt:US.job_j8RyX5brhwq-4CrzbuHt1QjxHkOB, "
                          "313,83 GB, sandbox tanpa billing)",
              availability_timestamp="DATE UTC Sabtu t−2 .. Jumat t+4", feature_family=f"set {sset}",
              preprocessing="share vs total Indonesia; z vs 52 minggu lalu; judul unik per hari",
              model="increment-only logit offset konsensus, walk-forward", leakage_audit="PASS (tes sintetis jendela & masa depan; hanya DATE GDELT)",
              script="scripts/b_bq_daily_counts_singleline.sql; scripts/b_gdelt_screen.py --tag gdelt")
    if G is None:
        add(experiment_id=f"JA-B05-{sset}", horizon="4;8", decision="BLOCKED", reason="butuh proyek BigQuery sandbox [HUMAN]; protokol & kueri beku", **kw)
        continue
    g = G[(G["kind"] == "gdelt") & (G["set"] == sset)].set_index("horizon")
    a, b = g.loc[4], g.loc[8]
    add(experiment_id=f"JA-B05-{sset}", horizon="4;8", roc_auc=f"nasional h4 {a['auc_cons']:.4f} → {a['auc_inc']:.4f}; h8 {b['auc_cons']:.4f} → {b['auc_inc']:.4f}",
        delta_vs_c1t=f"ΔAUC h4 {a['d_auc']:+.4f}; h8 {b['d_auc']:+.4f}", confidence_interval=f"h4 {a['lo']:+.4f}..{a['hi']:+.4f}; h8 {b['lo']:+.4f}..{b['hi']:+.4f}",
        bh_q=f"{a['q_bh']:.3f}; {b['q_bh']:.3f}", decision="REJECT (gerbang G5)",
        reason="tidak ada set yang memenuhi ΔAUC ≥ +0,01 di kedua horizon; semua di bawah kontrol positif (+0,015) → tanpa modeling provinsi", **kw)
for cid, name, dec, why in [
        ("C1", "SP2KP stok & pasokan mingguan", "BLOCKED", "area admin berlogin (U112), tidak berubah sejak D-159"),
        ("C2", "Bapanas Proyeksi Neraca Pangan", "BLOCKED", "semua dataset Terbatas; vintage bulanan baru sejak Sept 2024; 2022–2023 hanya Final/Revisi (ex-post) → G1/G2 gagal untuk dev"),
        ("C3", "Kementan EWS & luas tanam hortikultura", "BLOCKED", "tidak ada seri publik; mekanisme tanam→panen berbeda dari cuaca"),
        ("C4", "tanggal pengumuman HET/HAP", "REJECT", "G4: 11 peristiwa komoditas di dev; D-146 fitur regulasi gagal"),
        ("C5", "perubahan harga BBM", "REJECT", "G4/G5: 1 peristiwa di dev"),
        ("C6", "BNPB DIBI", "REJECT", "server pulih, tetapi bencana dominan = cuaca ekstrem (oracle D-161 gagal); G2 sebagian"),
        ("C7", "Google Trends", "REJECT", "G2 (sampel & normalisasi ulang, tidak reproduktif) & G3 (reaktif)"),
        ("C8", "NDVI satelit sentra", "BLOCKED", "akun Earthdata/GEE [HUMAN]; prior rendah (digerakkan cuaca)"),
        ("C9", "stok Bulog / SPHP / bansos beras", "REJECT", "G4: beras saja, headroom ≤ +0,007"),
        ("C10", "gangguan pelabuhan/penyeberangan", "REJECT", "tidak ada seri terstruktur; tercakup kategori gangguan GDELT")]:
    add(experiment_id=f"JA-{cid}", workstream="C pasokan & kejadian", hypothesis=f"{name} mendahului arah harga nasional", data_source=name,
        decision=dec, reason=why, leakage_audit=NA, script="SUPPLY_SIDE_SOURCE_AUDIT.md")
add(experiment_id="JA-D01", workstream="D modeling", hypothesis="sumber yang lolos G1–G5 menaikkan macro F1 di atas C1-tuned",
    model="HGB TUNED_HGB + satu keluarga fitur", horizon="4;8", decision="BLOCKED",
    reason="tidak ada sumber yang lolos G1–G5 (GDELT gagal G5; sumber pasokan terblokir akses); test 2024+ tidak dibuka; C1-tuned tetap",
    leakage_audit=NA, script=NA)
pd.DataFrame(rows, columns=COLS).to_csv(os.path.join(BASE, "EXPERIMENT_LOG.csv"), index=False, lineterminator="\n")
print(len(rows), "baris → EXPERIMENT_LOG.csv")
