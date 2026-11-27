# Validasi K4 — Audit awal

Tanggal 2026-11-27 · Pelaksana: Danen (dengan agent) · catatan bertanggal. Indeks folder: [SUMMARY.md](SUMMARY.md). Protokol analisis baru:
[PROTOCOL_ADDENDUM.md](PROTOCOL_ADDENDUM.md) (ditulis dan di-hash sebelum analisis kalibrasi).

STATUS: **COMPLETE**

OBJECTIVE: Mencatat kondisi K4-E80 sebelum validasi, memeriksa implementasi target, dan menyusun daftar masalah yang diaudit di dokumen lain.

## 1. Kondisi K4 saat ini (D-164, tidak diubah)

| Metrik | h 4 | h 8 | Sumber |
|---|---|---|---|
| AP dev / test | 0,326 / 0,237 | 0,290 / 0,206 | `k4_ranking.csv`, `k4_test_ranking.csv` |
| ROC-AUC dev | 0,775 | 0,743 | `k4_ranking.csv` |
| Presisi@K2 dev / test | 0,293 / 0,202 | 0,272 / 0,174 | idem |
| Brier test / ECE test | 0,0750 / 0,019 | 0,0795 / 0,024 | `k4_test_probability.csv` |
| ΔAP test vs C1-tuned | +0,045 (0,017..0,083), q 0,048 | +0,015 (−0,028..0,064) | `k4_test_paired.csv` |
| Keputusan | ranking PARTIAL; peluang hanya h 4; operasional BLOCKED (U109) | | RESULTS.md D-164 |

Angka di atas dicocokkan dengan file hasil D-164 dan tidak dihitung ulang dengan cara lain. Prediksi beku dibaca dari
`k4_{dev,test,forward}_preds.parquet` (folder kerja sesi D-164). `k4_forward_preds.csv` di disk cocok dengan manifest (sha256 `eb1f10db…`).

## 2. Pemeriksaan implementasi target (ringkas; rinci di [TARGET_INTEGRITY_AUDIT.md](TARGET_INTEGRITY_AUDIT.md))

| Pertanyaan | Jawaban |
|---|---|
| Target tak teramati diberi z = 0? | Ya, di evaluasi saja (`split_k4`: `np.isfinite(v) & (v >= th)`). Tidak di latih: baris latih wajib target terealisasi |
| Berapa baris? | dev 2 + 2, test 0, maju semua (belum terjadi) |
| Dampak bila dikeluarkan | ΔAP ≤ 0,0004, presisi@K2 ≤ 0,0004, Brier 0 |
| y_h dan z = harga teramati? | Ya. Hitung ulang dari `panel_weekly`: maks \|Δy\| 0, 0 label berbeda |
| Universe latih vs evaluasi | Beda hanya (a) target tak teramati di evaluasi, (b) C1-tuned tanpa y = 0. Keduanya disengaja |
| Kebocoran | Tidak ada temuan baru; uji perturbasi D-164 tetap berlaku |

## 3. Daftar masalah yang diaudit

| # | Masalah | Dokumen | Hasil singkat |
|---|---|---|---|
| M1 | Penanganan target tak teramati | TARGET_INTEGRITY_AUDIT | Sesuai dokumentasi; dampak ≈ 0; jebakan kolom z pada prediksi maju |
| M2 | Delapan kebutuhan TPID + 4 tambahan belum dijawab | [BUSINESS_REQUIREMENTS_VALIDATION.md](BUSINESS_REQUIREMENTS_VALIDATION.md) | Instrumen siap; 0/12 tervalidasi |
| M3 | Ekor atas h 8 terlalu yakin; Platt tidak memperbaiki | [CALIBRATION_DEEP_AUDIT.md](CALIBRATION_DEEP_AUDIT.md) | 0/6 kalibrator memperbaiki Brier; ekor = 5 origin, rezim kebijakan & salah alokasi komoditas |
| M4 | 7–8 dari 10 alarm tidak berujung kenaikan material | [OPERATIONAL_ERROR_ANALYSIS.md](OPERATIONAL_ERROR_ANALYSIS.md) | Separuh = naik di bawah ambang; 25% (h 4) naik sesudah titik akhir; terlewat separuh di peringkat K+1..K+2 |
| M5 | P80 belum tentu ambang kebijakan | [TARGET_SENSITIVITY_REPORT.md](TARGET_SENSITIVITY_REPORT.md) | Kokoh di P70–P90/bertanda/kejadian; kalah dari C1t pada ambang seragam 5%/10% |
| M6 | Belum ada kerangka keputusan produk | [OPERATIONAL_SPECIFICATION.md](OPERATIONAL_SPECIFICATION.md) | Lima lapis; peluang hanya kategori h 4; parameter milik pengguna |
| M7 | Prediksi maju beku belum di-commit, target pertama mulai teramati minggu ini | [FINAL_RECOMMENDATIONS.md](FINAL_RECOMMENDATIONS.md) #1 | `[HUMAN]` commit hari ini |

## 4. Batas sesi ini

Tidak ada model yang dilatih ulang. Tidak ada perubahan pada `src/`, C1-tuned, label/macro F1 resmi, H5, prediksi K4 beku, atau hasil D-164.
Test 2024+ tidak dibuka untuk analisis baru (kalibrasi, galat, kepekaan hanya dev).

FINDINGS: Implementasi target K4 sesuai dokumentasi. Masalah yang tersisa ada pada kalibrasi h 8, kecocokan definisi target dengan kebutuhan
pengguna, dan tata kelola alarm, bukan pada label.

EVIDENCE: `hasil/ti_*.csv`; file D-164 di `../20261126_k4_risiko_material/hasil/`.

STATISTICAL VALIDITY: Audit implementasi bersifat pencocokan persis.

BUSINESS IMPLICATION: Masalah terbesar K4 adalah kecocokan dengan kebutuhan, bukan kebenaran label.

DECISION: **Lanjut** ke audit M2–M6.

BLOCKERS: U109.

NEXT ACTION: Lihat dokumen per masalah.
