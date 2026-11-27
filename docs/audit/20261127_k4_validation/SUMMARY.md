# Validasi K4 & Kesiapan Operasional — Ringkasan (2026-11-27)

Catatan bertanggal · Danen (dengan agent) · EKSPLORATIF · baca-saja terhadap D-164. Tidak ada model dilatih ulang. `src/`, C1-tuned, label/macro F1
resmi, H5, dan prediksi K4 beku tidak berubah. Test 2024+ tidak dibuka untuk analisis baru.

Dokumen: [INITIAL_AUDIT](INITIAL_AUDIT.md) · [TARGET_INTEGRITY_AUDIT](TARGET_INTEGRITY_AUDIT.md) ·
[BUSINESS_REQUIREMENTS_VALIDATION](BUSINESS_REQUIREMENTS_VALIDATION.md) · [CALIBRATION_DEEP_AUDIT](CALIBRATION_DEEP_AUDIT.md) ·
[OPERATIONAL_ERROR_ANALYSIS](OPERATIONAL_ERROR_ANALYSIS.md) · [TARGET_SENSITIVITY_REPORT](TARGET_SENSITIVITY_REPORT.md) ·
[OPERATIONAL_SPECIFICATION](OPERATIONAL_SPECIFICATION.md) · [FINAL_RECOMMENDATIONS](FINAL_RECOMMENDATIONS.md) · protokol
[PROTOCOL_ADDENDUM](PROTOCOL_ADDENDUM.md) · skrip `scripts/v_*.py` · hasil `hasil/`.

STATUS: **PARTIAL**. K4-E80 layak sebagai skor ranking risiko eksploratif. **Belum layak diadopsi** untuk penggunaan operasional (BLOCKED, U109).

## Executive summary

1. **Target benar.** Target tak teramati memang diberi z = 0, tetapi hanya di evaluasi dan hanya pada 4 baris dev (0 di test), dan tidak pernah
   ikut latih. Dampak koreksi ≤ 0,0004 AP. y_h dan z identik dengan hitung ulang dari panel. Negatif "harga tetap" adalah kekakuan nyata. Satu
   jebakan: kolom z pada prediksi maju beku bernilai 0 dan **bukan label**.
2. **Kalibrasi h 8 tidak dapat diperbaiki dengan kalibrator.** 0 dari 6 kalibrator walk-forward (Platt, isotonik, per komoditas, intersep, jendela
   pendek, campuran laju-dasar) menurunkan Brier. Platt dan isotonik hanya menurunkan ECE. Ekor p 0,8–0,9 (57 baris, 28% positif) berasal dari
   5 origin, 41 baris dari dua: minyak goreng Jan 2022 (momentum terputus intervensi harga) dan beras Okt 2023 (kenaikan terjadi di cabai, bukan
   beras). Oracle laju per origin (ex-post) memperbaiki Brier 0,007. Itu informasi rezim yang tidak ada di histori harga.
3. **Alarm palsu bukan derau murni.** Pada K = 2, separuh adalah kenaikan di bawah ambang P80, sepertiga penurunan. Pada h 4, 25% alarm palsu naik
   material dalam 4 minggu sesudah titik akhir (seri tanpa alarm 12%). Separuh kenaikan terlewat berada tepat di bawah batas K. Bawang putih dan
   bawang merah memakai 14–17% alarm dengan presisi 0,01–0,15.
4. **Keunggulan K4 bergantung pada definisi target.** Kokoh di semua target statistik (P70–P90, bertanda, kejadian; satu model P80 cukup). Tetapi
   dengan ambang seragam 5% / 10%, skor K4-E80 **kalah** dari C1-tuned (ΔAP h 8 −0,079 / −0,092, interval < 0). Ambang kebijakan TPID dapat
   membatalkan pemakaian K4-E80.
5. **Kebutuhan bisnis: 0 dari 12 tervalidasi.** Instrumen wawancara dan matriks pencatatan (VALIDATED / PARTIALLY / NOT / CONFLICTING) siap.
   Peta jawaban → keputusan model ditulis sebelum jawaban ada.
6. **Spesifikasi operasional** memisahkan ranking, peluang (h 4 kategori relatif saja, h 8 tanpa angka), alarm (K atau τ dipilih pengguna),
   tinjauan manusia, dan keputusan TPID. Sistem tidak pernah memerintahkan intervensi.

## Temuan terpenting

| # | Temuan | Bukti | Dampak |
|---|---|---|---|
| 1 | Label K4 benar; target tak teramati 4 baris, tidak berdampak | `ti_correction_impact.csv` | D-164 tetap |
| 2 | Tidak ada kalibrator yang memperbaiki Brier; ekor h 8 = 5 origin | `cal_candidates.csv`, `cal_tail_composition.csv` | Peluang h 8 tidak ditampilkan; h 4 hanya kategori |
| 3 | Ranking K4 kalah dari C1t pada ambang seragam | `sens_paired.csv` | V1/V8 TPID menentukan apakah K4-E80 dipakai |
| 4 | 25% alarm palsu h 4 = kenaikan yang datang terlambat | `err_false_alarms.csv` | V3 (jendela) mengubah nilai daftar |
| 5 | Prediksi maju beku belum di-commit, target pertama teramati minggu ini | `git status` | `[HUMAN]` commit hari ini |

## Keputusan berikutnya

1. `[HUMAN]` Danen: commit `docs/audit/20261126_k4_risiko_material/hasil/k4_forward_preds.csv` dan `k4_forward_manifest.json` hari ini.
2. `[HUMAN]` Danen/Abi: wawancara TPID (R1–R12).
3. Agent, 2026-12-18 / 2027-01-15: evaluasi prospektif dengan label dari panel baru (bukan kolom z beku).
4. Sesudah jawaban TPID: pilih jalur dari peta BUSINESS_REQUIREMENTS_VALIDATION §5. Ambang seragam → protokol baru. Kejadian → K4-A80.
   Relatif → K4-E80 prospektif.
