# Jalur A — Hasil: Macro F1 Task 4 Arah & Intelijen Eksternal (D-165, EKSPLORATIF)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Catatan bertanggal. Dokumen pendukung: [INITIAL_AUDIT.md](INITIAL_AUDIT.md),
[PROTOCOL.md](PROTOCOL.md), [GDELT_FEASIBILITY.md](GDELT_FEASIBILITY.md), [GDELT_PILOT.md](GDELT_PILOT.md),
[SUPPLY_SIDE_SOURCE_AUDIT.md](SUPPLY_SIDE_SOURCE_AUDIT.md), [EXPERIMENT_LOG.csv](EXPERIMENT_LOG.csv), [RECOMMENDATIONS.md](RECOMMENDATIONS.md).

## Executive Summary

- **Tidak ada kandidat baru yang menaikkan macro F1 di atas C1-tuned; C1-tuned tetap** (dev 0,656 / 0,676, diverifikasi ulang; test 0,677 / 0,680).
  Test 2024+ tidak dibuka.
- **Workstream A (prospektif)**: prediksi maju D-152 & D-158 utuh (hash cocok, base identik, 338 seri, 0 NaN). Belum ada target terealisasi
  (pertama lengkap Jumat 2026-11-27; semua h 4 pada 2026-12-18, semua h 8 pada 2027-01-15). Evaluator gabungan dibekukan sebelum target ada.
  Kedua pembekuan ada di riwayat git sebelum target pertama: D-152 `ca53742` (2026-11-25 21.41 WIB), D-158 `ec6dd19` (2026-11-26 20.45 WIB).
- **Workstream B (GDELT)**: DOC API tertutup (HTTP 429 menetap). Berkas GKG Translingual layak secara teknis (G1–G2 ✓: ± 12.500 artikel berbahasa
  Indonesia/hari; lag `DATE` ≤ 1 hari). Validasi manual 111 artikel: presisi relevan 0,23 dengan pola naif → **0,72** dengan penyaring F2d. Cakupan
  per komoditas tipis di luar beras & minyak goreng (G4 sebagian), sebagian berita reaktif terhadap harga (G3 sebagian). **G5 diuji lewat BigQuery sandbox** (proyek baru tanpa
  billing, 313,83 GB, biaya 0; adendum 2026-11-26 23.03 WIB): kelima set berita memberi ΔAUC arah nasional −0,008..+0,001 (q ≥ 0,46) di atas
  konsensus C1t → **GDELT REJECTED**, tanpa modeling provinsi.
- **Temuan metode**: layar gerbang 5 (ΔAUC arah nasional di atas konsensus C1t) **tidak meloloskan kontrol positif** (kesegaran nasional, satu-satunya
  sinyal tambahan yang pernah membantu: ΔAUC +0,015, −0,002..+0,030). MDE layar ± 0,023 AUC → sumber baru harus lebih kuat dari sinyal terbaik
  yang diketahui. Ambang tidak dilonggarkan.
- **Workstream C (pasokan & kejadian)**: 10 kandidat dinilai; tidak ada yang lolos G1–G4 untuk dev. Dua mekanisme baru yang paling masuk akal
  tertutup oleh **akses**: Proyeksi Neraca Pangan Bapanas (Terbatas; vintage baru sejak Sept 2024) dan luas tanam/EWS hortikultura Kementan.
- **Aspirasi F1 0,8–0,9 tidak didukung bukti**: memprediksi setiap provinsi dengan arah mayoritas nasional yang **sebenarnya** (informasi nasional
  sempurna) hanya memberi 0,756 / 0,782 (D-158 §3); sisa celah adalah variasi lokal.

## Current Bottlenecks

1. **Informasi arah nasional per komoditas × minggu** (D-157/D-158): konsensus C1t sudah prediktor terbaik dari data harga (AUC 0,76); headroom
   +0,105 macro F1 hanya dapat dijangkau dengan informasi ex-ante non-harga, dan semua sumber yang terjangkau publik sudah gagal atau terblokir.
2. **Akses data pasokan** (U112): SP2KP, Proyeksi Neraca Pangan, luas tanam/EWS ada tetapi tertutup/terbatas; vintage dev tidak tersedia.
3. **Daya statistik**: layar G5 (MDE ± 0,023 AUC) dan validasi maju (MDE 0,04–0,12 macro F1) hanya mendeteksi efek besar; efek realistis
   (+0,005..+0,02) tidak dapat dikonfirmasi dalam horizon proyek.
4. **Perubahan kecil & base rate per origin** (D-156): tetap; tidak disentuh ulang (tanpa hipotesis baru).

## Experiments Executed

| ID | Hipotesis | Hasil | Keputusan |
|---|---|---|---|
| JA-A01 | Prediksi maju IW_NAT/FR_REF tidak gagal besar | audit lolos; 0 target terealisasi; evaluator beku | BLOCKED (waktu) |
| JA-B01 | DOC API cukup untuk pilot | 429 di 4 percobaan (jeda s.d. 3,5 jam) | BLOCKED |
| JA-B02 | GKG Translingual mencakup berita pangan Indonesia 2019–2023 | 48 batch: 130 artikel Indonesia/batch; judul 2019 0,29, 2020+ ≥ 0,99; ± 222 kandidat/hari | G1–G2 ✓, G3–G4 sebagian |
| JA-B03 | Penyaring kata kunci memisahkan berita pasokan | presisi R 0,23 → 0,72 (F2d); recall −6/24; duplikasi 10% | penyaring F2d dipakai |
| JA-B04 | Layar G5 peka terhadap sinyal yang diketahui | POS +0,015 (−0,002..+0,030) h 4, −0,004 h 8; NEG ≈ 0 | kalibrasi: MDE ± 0,023 |
| JA-B05 | Intensitas berita pasokan/kebijakan (5 set praregistrasi) menambah arah nasional di atas konsensus C1t | BigQuery 1.836 hari; ΔAUC h 4 −0,005..+0,001, h 8 −0,008..−0,000; semua interval memuat 0 atau < 0; q ≥ 0,46 | **REJECTED** (G5) |

## Experiments Rejected

| ID | Kandidat | Alasan berbasis bukti |
|---|---|---|
| JA-C4 | Tanggal pengumuman HET/HAP | 11 peristiwa komoditas di dev (G4); fitur regulasi gagal D-146 |
| JA-C5 | Perubahan harga BBM | 1 peristiwa di dev (G4/G5 tidak dapat diuji) |
| JA-C6 | BNPB DIBI | bencana dominan = cuaca ekstrem; oracle cuaca terealisasi gagal (D-161); G2 sebagian |
| JA-C7 | Google Trends | tidak reproduktif (G2), reaktif terhadap harga (G3) |
| JA-C9 | Stok Bulog / SPHP / bansos beras | beras saja; informasi beras sempurna ≤ +0,007 (G4) |
| JA-C10 | Gangguan pelabuhan/penyeberangan | tidak ada seri terstruktur; tercakup kategori GDELT |
| (tidak diulang) | SIJAGUNG, SPORA, PIBC, CFSv2, NASA POWER, impor BPS, grosir/produsen/kota PIHPS, threshold, bobot, model lain | sudah ditolak D-150–D-161 tanpa mekanisme baru |

| JA-B05 | GDELT (berita Indonesia, 5 set) | gagal G5: ΔAUC ≤ +0,001 di semua sel kecuali satu, jauh di bawah kontrol positif; berita sebagian besar reaktif terhadap harga |

Terblokir (tidak ditolak): JA-C1 SP2KP, JA-C2 Proyeksi Neraca Pangan, JA-C3 EWS/luas tanam, JA-C8 NDVI.

## Performance Comparison (macro F1; tidak ada kandidat baru yang dievaluasi pada label resmi)

| Model | Dev h 4 / h 8 | Test h 4 / h 8 | Δ vs C1-tuned | Status |
|---|---|---|---|---|
| **C1-tuned** (pembanding) | **0,656 / 0,676** | 0,677 / 0,680 | – | tetap |
| IW_NAT (D-151/D-152) | 0,676 / 0,681 | 0,686 / 0,683 | test +0,0085 (−0,003..0,024) / +0,0033 (−0,004..0,011), q 0,28 / 0,30 | belum terbukti; menunggu data maju |
| FR_REF / FR_CITY (D-158) | +0,024 / +0,004 dan +0,024 / +0,008 (dev) | tidak dibuka | kontribusi kota ≈ 0 | keluarga intraminggu; menunggu data maju |
| GDELT (set V/D/P/S/ALL) | ΔAUC nasional h 4 −0,005..+0,001 / h 8 −0,008..−0,000 | – | – | gagal G5 (REJECTED); macro F1 tidak dihitung (aturan: berhenti sebelum modeling) |
| Layar nasional, kontrol POS | ΔAUC nasional +0,015 / −0,004 | – | – | tidak lolos G5 (temuan daya) |

## Data Leakage and Reproducibility

| Kontrol | Hasil |
|---|---|
| Prediksi maju | sha256 = manifest (D-152 `28651b2b…`, commit `ca53742`; D-158 `7586eaed…`, commit `ec6dd19` 2026-11-26 20.45 WIB); base D-152 = base D-158 (|Δp| 0); kode yang berubah sejak beku hanya `src/features/forecast.py` (D-162, kolom `episode` grup fx — tidak dipakai C1t/IW_NAT/FR_*) |
| Label prospektif | `fw_eval.labels` D-152 (hash diverifikasi sebelum dipakai); selftest pada snapshot sekarang 156.400 / 155.040 baris, 0 beda |
| GDELT waktu | hanya `DATE` batch GDELT (UTC), jendela Sabtu t−2 .. Jumat t+4 < `available_at` Minggu 00.00 WIB; anomali dari 52 minggu lalu; tes sintetis: perubahan sesudah Jumat t tidak mengubah fitur ≤ t |
| Layar G5 | konsensus C1t OOS mingguan (D-158), label nasional t' + h ≤ r; reproduksi angka D-158 (0,762 / 0,777) |
| Test 2024+ | tidak dibaca |
| Reproduksi | `hasil/a_protocol_sha256.txt` (evaluator A, 11.34 UTC), `hasil/protocol_sha256.txt` (protokol & skrip B, 15.16 UTC; versi paket; sha256 tabel kerja `c1t_weekly`, `fresh`); 12 tes `tests/` lolos (`python -m pytest -q docs/audit/jalur_a_macro_f1/tests`); berkas GKG mentah tidak disimpan, dapat diunduh ulang dari daftar `b_gkg_sample_files.csv` (sha256) |
| GDELT BigQuery | rekaman Translingual ada (cek partisi 7.791/hari); teks kueri di editor = berkas beku (sha256 `aac32302…`); hash protokol di komentar job; skrip & protokol layar = versi beku (sha256 `3c57533e…`, `e6b46d95…`); hasil + job ID di `hasil/gdelt_bq_manifest.json` |
| Belum dapat diuji | revisi/vintage PIHPS (U110) |

## Remaining Opportunities (urut potensi × kelayakan)

1. **Validasi maju** IW_NAT/FR_REF — tanpa biaya; hanya penjaga kegagalan besar.
2. **Data pasokan resmi** (SP2KP stok mingguan, Proyeksi Neraca Pangan, luas tanam/EWS) — mekanisme paling masuk akal untuk informasi nasional
   ex-ante, tetapi butuh surat permintaan dan hanya dapat dievaluasi prospektif.
3. Ukuran keberhasilan berbasis kebutuhan TPID (S1–S3, K4; sesi D-164) — bukan macro F1.

## Final Decision

**REJECT** untuk semua hipotesis yang dapat diuji: GDELT (satu-satunya sumber independen yang lolos G1–G2) gagal G5 dengan titik estimasi ≤ 0,
dan enam kandidat pasokan/kejadian ditolak dengan bukti. Tidak ada ACCEPT. Yang tersisa **BLOCKED**: sumber pasokan berakses terbatas (SP2KP,
Proyeksi Neraca Pangan, luas tanam/EWS, NDVI; `[HUMAN]`) dan validasi prospektif (target pertama 2026-11-27). **C1-tuned tetap**; tidak ada
artefak resmi atau keputusan resmi yang berubah.

## Next Actions

Lihat [RECOMMENDATIONS.md](RECOMMENDATIONS.md).
