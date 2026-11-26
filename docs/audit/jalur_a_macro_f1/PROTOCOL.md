# Protokol Jalur A — Macro F1 Task 4 Arah & Intelijen Eksternal (D-165, EKSPLORATIF)

Ditulis 2026-11-26. Hash protokol & skrip: `hasil/protocol_sha256.txt`; evaluator prediksi maju dibekukan lebih awal (`hasil/a_protocol_sha256.txt`,
11.34 UTC, sebelum target pertama lengkap). Aturan umum mengikuti `docs/EKSPERIMEN.md` §2–§6; bila bertentangan, aturan yang lebih ketat berlaku.

## 0. Batasan tetap

- Pembanding = C1-tuned beku (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed 20261121, threshold 0,5); label & baris evaluasi resmi D-139/D-141
  (y = 0 dikeluarkan, perubahan kecil tetap dihitung); preprocessing beku D-148.
- Seleksi hanya origin pengembangan (target ≤ 2023-12-31). Test 2024+ **tidak dibuka** di Jalur A.
- Artefak resmi (`direction_tuned_preds`, `forecast_preds`, `direction_preds`), `src/`, `configs/` tidak diubah. Prediksi maju beku tidak diubah.
- Tanpa biaya: tidak ada proyek/billing cloud yang dibuat oleh agent; kueri BigQuery hanya dijalankan pengguna dengan batas byte.

## A. Validasi prospektif (prediksi maju D-152 + D-158)

- Model: base (C1-tuned), IW_NAT (kandidat), FR_REF (acuan ≈ IW_NAT), FR_CITY (diagnostik). Sumber, hash, dan label: [`scripts/a_forward_eval.py`](scripts/a_forward_eval.py).
- Evaluasi hanya bila snapshot PIHPS baru memuat Jumat minggu origin + h; label dari `fw_eval.labels` D-152 (hash diverifikasi).
- Metrik per horizon & model: macro F1, F1/presisi/recall per kelas, MCC, ROC-AUC, Brier, ECE, porsi naik, macro F1 kuintil |y| terkecil.
  Selisih vs base: macro F1, AUC, Brier + interval bootstrap kluster provinsi (deskriptif).
- Penanda (ditetapkan sebelum target): **GAGAL_MAJU** bila Δ macro F1 < −0,08 (h 4) / < −0,04 (h 8) = MDE batch maju D-152; **KONSISTEN** bila
  Δ ≥ 0; **TIDAK_TERBUKTI** di antaranya. Tidak ada keputusan adopsi dari data maju (daya: ± 14 / 27 tahun origin untuk +0,0085 / +0,0033).

## B. GDELT

- **B1–B3** kelayakan & pilot: sampel 48 batch acak (desain di `scripts/b_gkg_sample.py`), validasi manual, penyaring F2d (batas kata + kata kunci
  pasokan/kebijakan + dedup judul per hari). Penyaring ditetapkan dari pilot (data dev, tanpa melihat target harga).
- **B4 layar G5** ([`scripts/b_gdelt_screen.py`](scripts/b_gdelt_screen.py)), dijalankan sekali pada hitungan BigQuery lengkap:
  - Fitur per kelompok komoditas × minggu origin t: hitungan judul unik per hari, `DATE` UTC Sabtu t−2 .. Jumat t+4; share terhadap total
    artikel Indonesia; z anomali vs 52 minggu lalu (≥ 26 minggu). Pemetaan cabai → cabai merah & cabai rawit; kelompok `umum` tidak dipakai.
  - **Set praregistrasi (5)**: V [z_all], D [z_disrupt], P [z_policy], S [z_stabil, z_supply], ALL [5 kolom]. Tidak ada set lain, tidak ada
    pemilihan lag/jendela sesudah melihat hasil.
  - Uji: increment-only di atas logit konsensus C1t OOS mingguan, regresi logistik tanpa intersep, walk-forward refit 4 minggu (t' + h ≤ r,
    ≥ 52 minggu), minggu dev 2021-01-04 .. 2023-12-31 − h; ΔAUC, bootstrap blok 13 minggu (1.999 rep), q BH atas 10 uji (5 set × 2 h).
  - **LOLOS** bila satu set: ΔAUC ≥ +0,01 di kedua horizon, batas bawah > 0 di ≥ 1 horizon, q < 0,05 di ≥ 1 horizon (aturan D-161).
  - Kontrol wajib dilaporkan bersama: POS `iw_gap_nat`, NEG derau. Kalibrasi yang sudah dijalankan: POS ΔAUC +0,015 (−0,002..+0,030) h 4,
    −0,004 h 8 → tidak lolos; MDE ± 0,023. Keterbatasan daya ini **tidak** dipakai untuk melonggarkan ambang.
- **Kebocoran**: hanya `DATE` GDELT (bukan tanggal peristiwa), jendela berakhir sebelum `available_at` harga; anomali hanya dari minggu lalu;
  tes `tests/test_gdelt_screen.py` (jendela & ketergantungan masa depan).

## C. Sumber pasokan & kejadian

Lima gerbang (G1–G5) seperti [SUPPLY_SIDE_SOURCE_AUDIT.md](SUPPLY_SIDE_SOURCE_AUDIT.md); gagal satu gerbang → tidak dimodelkan, tanpa backfill.

## D. Modeling (hanya bila suatu sumber lolos G1–G5)

- Satu keluarga fitur per sumber, ditambahkan ke kolom C1t; HGB dengan `TUNED_HGB` tetap (tanpa tuning ulang), seed resmi, threshold 0,5.
- Aturan lolos = `docs/EKSPERIMEN.md` §4 + aturan ketat D-156 §6 (q BH < 0,05, Δ ≥ 0 di ≥ 2 dari 3 tahun dev, porsi origin Δ > 0 ≥ 0,5 di kedua
  horizon, F1 per kelas tidak turun > 0,01, tidak ada komoditas turun > 0,03 di kedua horizon) + kriteria bisnis S1–S3 tidak memburuk.
- Laporan: agregat, per komoditas, per provinsi, per origin, kuintil |y|; uji kebocoran perturbasi/penghapusan sesudah origin.
- Test 2024+ hanya dibuka sekali untuk satu kandidat yang lolos; tanpa pemilihan ulang.

## E. Urutan & pengungkapan

1. Evaluator A dibekukan (11.34 UTC) sebelum target ada. 2. Probe & pilot GDELT (B2) dijalankan sebelum protokol ini ditulis; pilot hanya
   memakai data berita, tanpa target harga. 3. Kontrol layar (POS/NEG) dijalankan sebelum protokol ini ditulis untuk kalibrasi daya; aturan
   gerbang disalin apa adanya dari D-161 (`cfs_du.py`), tidak dipilih dari hasil kontrol. 4. Set B4 ditetapkan di sini sebelum data GDELT lengkap ada.
