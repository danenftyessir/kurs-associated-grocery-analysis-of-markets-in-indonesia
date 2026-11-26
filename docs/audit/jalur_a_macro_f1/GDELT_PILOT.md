# GDELT GKG 2.1 Translingual — Pilot Kecil, Validasi Manual & Layar Gerbang 5 (Workstream B2–B4)

Tanggal: 2026-11-26 · Keputusan: D-165 · Akses & biaya: [GDELT_FEASIBILITY.md](GDELT_FEASIBILITY.md). Origin pengembangan saja; test 2024+ tidak dipakai.

## 1. Desain sampel (B2)

- 48 batch 15 menit acak (seed 20261126): tanggal seragam 2019-01-01..2023-12-31, jam seragam 00:00–11:45 UTC (07.00–18.45 WIB). Ditetapkan di
  [`scripts/b_gkg_sample.py`](scripts/b_gkg_sample.py) sebelum unduh. Diunduh 48 berkas `translation.gkg.csv.zip` (409 MB, sha256 per berkas di
  `hasil/b_gkg_sample_files.csv`) + 2 berkas aliran Inggris dan 2 Translingual untuk probe awal (± 25 MB). Berkas mentah hanya di scratchpad
  lokal (tidak di repo); yang disimpan hanya metadata artikel cocok (`hasil/b_gkg_sample_articles.csv`).
- Penyaring kandidat: `TranslationInfo` diawali `srclc:ind` **dan** judul (`<PAGE_TITLE>`) atau slug URL memuat pola komoditas.

## 2. Volume, judul, sumber (`hasil/b_gkg_sample_summary.json`)

| Ukuran | Nilai |
|---|---|
| Rekaman Translingual per batch | 2.244 (853–4.287) |
| Artikel berbahasa Indonesia per batch | 130 (28–274); per tahun 105 / 161 / 162 / 85 / 120 (2019–2023) |
| Porsi artikel Indonesia dengan `PAGE_TITLE` | 2019 **0,29**; 2020–2023 ≥ 0,99 |
| Kandidat cocok komoditas per batch | 2,3 → ± 222/hari nasional |
| Sumber terbanyak kandidat | tribunnews.com 31, inilah.com 13, pikiran-rakyat.com 12, republika.co.id 9, bisnis.com 7 |

## 3. Validasi manual 111 kandidat (`hasil/b_manual_labels.csv`, `scripts/b_manual_eval.py` → `hasil/b_manual_summary.json`)

Dilabeli agent dari judul/slug URL (isi artikel tidak dibaca; verifikasi manusia disarankan). **R** relevan = pasokan, produksi, panen, bencana
sentra, kebijakan impor/ekspor/harga, distribusi, stabilisasi, stok untuk komoditas KAGAMI/bahan pokok; **P** sebagian = laporan harga
eceran (reaktif), politik/umum, hukum, budidaya jangka panjang, bantuan bermuatan politik; **I** tidak relevan.

| Penyaring | n | R | P | I | Presisi R | Presisi R+P |
|---|---|---|---|---|---|---|
| F0 pola awal (tanpa batas kata) | 111 | 25 | 36 | 50 | 0,23 | 0,55 |
| F1 batas kata, tanpa `sawit`, kecuali "pondok cabe" | 89 | 24 | 34 | 31 | 0,27 | 0,65 |
| F1d = F1 + dedup judul per hari | 80 | 24 | 25 | 31 | 0,30 | 0,61 |
| F2 = F1 + kata kunci pasokan/kebijakan | 28 | 18 | 10 | 0 | 0,64 | 1,00 |
| **F2d** = F2 + dedup | 25 | 18 | 7 | 0 | **0,72** | **1,00** |

- **Salah cocok substring** 18% dari F0 ("beras" di *berasal/berasrama*, "pangan" di *lapangan/Pangandaran/ketimpangan*, "cabe" di *Pondok Cabe*,
  "sawit" untuk berita kebun); F1 menyisakan 1. Sisa I pada F1: resep, gaya hidup, promo ritel, amal sembako.
- **Recall**: F2 kehilangan 6 dari 24 artikel relevan F1 (judul tanpa kata pasokan, mis. "Pasar Jombang jual MinyaKita").
- **Sindikasi/duplikasi**: 10% kandidat F1 adalah judul ganda dalam hari yang sama (galeri foto inilah.com 4× judul sama; Bulog bansos di 2 sumber).
- **Keterkaitan komoditas**: kelompok benar termuat di hasil penyaring pada 100% artikel R/P; 33% R/P hanya "bahan pokok/pangan" umum.
- **Lokasi**: 84% artikel R punya ADM1 Indonesia di `V2Locations`.
- **Waktu**: `DATE` vs tanggal terbit di URL (49 artikel): median 0 hari, maks 1 hari, tidak ada yang negatif.
- **Isi R** (25): stabilisasi 8, kebijakan dagang 5 (larangan ekspor CPO/minyak goreng Apr 2022, rencana ekspor beras), pasokan 3, produksi 2,
  harga hulu 2, lainnya 5. Komoditas R: minyak goreng 9, beras 8, umum 3, daging sapi 2, bawang putih 1, cabai 1, telur 1, gula/ayam/bawang merah 0.
- Volume tersirat setelah F2d: **± 36 artikel relevan/hari** nasional (≈ 250/minggu), sangat tidak merata antarkomoditas dan antarwaktu
  (minyak goreng 2022 mendominasi).

## 4. Fitur (B3) & layar gerbang 5 (B4)

**Fitur** (dibangun dari hitungan BigQuery, [`scripts/b_gdelt_screen.py`](scripts/b_gdelt_screen.py) `weekly_features`): per kelompok komoditas ×
minggu origin t, jumlah artikel dengan `DATE` pada hari UTC Sabtu t−2 .. Jumat t+4 untuk kategori all / disrupt / policy / stabil / supply;
share = n / total artikel Indonesia minggu itu (menetralkan pertumbuhan cakupan GDELT); a = log1p(10⁴·share); anomali z terhadap 52 minggu
sebelumnya (hanya masa lalu, ≥ 26 minggu). Semua hitungan di kueri = judul unik per hari (dedup sindikasi dalam hari; `n_raw` tanpa dedup
hanya diagnostik). Kategori = penyaring F2 per jenis (gangguan, kebijakan, stabilisasi, pasokan). Tidak ada LLM/embedding.
Uji tanpa-kebocoran (`tests/test_gdelt_screen.py`): mengubah hitungan sesudah Jumat minggu origin tidak mengubah fitur ≤ origin; jendela
Sabtu–Jumat diuji eksplisit.

**Layar** (aturan D-158/D-161, ditulis ulang mandiri agar dapat dites): label nasional z = 1[share provinsi naik > 0,5], offset = logit konsensus
C1t OOS mingguan, regresi logistik tanpa intersep walk-forward (refit 4 minggu, t' + h ≤ r, ≥ 52 minggu), minggu dev 2021-01-04 .. 2023-12-31 − h,
ΔAUC dengan bootstrap blok 13 minggu (1.999 rep), q BH. Set praregistrasi: V, D, P, S, ALL ([PROTOCOL.md](PROTOCOL.md) §B4).

**Kalibrasi daya dengan kontrol** (`hasil/b_screen_controls.csv`; dijalankan sebelum data GDELT ada):

| Kontrol | h | AUC konsensus | AUC increment | ΔAUC (interval) | p | Lolos aturan G5? |
|---|---|---|---|---|---|---|
| POS kesegaran `iw_gap_nat` (satu-satunya sinyal tambahan yang pernah membantu; IW_NAT dev +0,020 / +0,005 macro F1) | 4 | 0,762 | 0,777 | **+0,015 (−0,002..+0,030)** | 0,10 | tidak |
| | 8 | 0,756 | 0,751 | −0,004 (−0,023..+0,008) | 0,40 | |
| NEG derau N(0,1) | 4 | 0,762 | 0,762 | +0,000 (−0,001..+0,001) | 1,00 | tidak |
| | 8 | 0,756 | 0,756 | −0,000 (−0,001..+0,001) | 0,81 | |

Konsensus dan kontrol positif mereproduksi D-158 (0,762 → 0,777–0,781). **MDE layar ≈ 2,8 × SE ≈ 0,023 AUC** (SE ± 0,008 di kedua horizon).
Konsekuensi: gerbang G5 (ΔAUC ≥ 0,01 di kedua horizon + batas bawah > 0 + q < 0,05) **menolak sinyal tambahan terbaik yang pernah ditemukan**;
sinyal berita harus lebih kuat dari kesegaran intraminggu untuk lolos. Ambang tidak diubah (larangan melonggarkan); keterbatasan ini dicatat
sebagai temuan metode (EKSPERIMEN §3, D-165).

## 5. Kesimpulan pilot

1. GDELT Translingual **dapat dipakai secara teknis** (G1–G2 ✓): volume berita Indonesia cukup, waktu ketersediaan dapat dibela, lag terbit ≤ 1 hari.
2. **Kualitas penyaring kata kunci cukup bila dibatasi** (presisi relevan 0,72 dengan F2d), tetapi recall turun dan seri per komoditas jarang di luar
   beras & minyak goreng (G4 sebagian). Sebagian isi reaktif terhadap harga (G3 sebagian).
3. **G5 tidak dapat diuji tanpa hitungan lengkap** → BLOCKED `[HUMAN]` (BigQuery sandbox, ± 0,3 TB, gratis). Ekspektasi realistis: lemah, karena
   (a) layar hanya mendeteksi ΔAUC ≳ 0,023, (b) peristiwa ex-ante murni jarang (5 kebijakan dagang dari 111 kandidat), (c) laju berita
   per komoditas rendah untuk 6 dari 9 kelompok.
4. Tidak ada modeling provinsi (aturan: berhenti sebelum modeling bila G5 belum lolos).

## 6. Adendum — Gerbang 5 dijalankan lewat BigQuery sandbox (2026-11-26 23.03 WIB)

Atas persetujuan Danen ("Ya, buat sandbox"): proyek Google Cloud baru `kagami-gdelt` dibuat di akun Danen **tanpa akun billing** (diverifikasi di
halaman Billing: "This project has no billing account"); proyek lain di akun itu tidak disentuh, tawaran free trial tidak diambil.
- **Cek partisi** 2022-03-15 (6,89 MB): 355.253 rekaman GKG, **7.791 Translingual `srclc:ind`** → tabel BigQuery memuat aliran Translingual.
- **Kueri utama** = `scripts/b_bq_daily_counts_singleline.sql` (isi sama dengan versi beku; teks di editor diverifikasi sha256 `aac32302…` sebelum
  dijalankan; komentar kueri memuat sha256 PROTOCOL.md → riwayat job BigQuery menjadi cap waktu pembekuan). Validator 313,83 GB ≤ 600 GB (estimasi
  awal ± 312 GB). Job `kagami-gdelt:US.job_j8RyX5brhwq-4CrzbuHt1QjxHkOB`, 16,6 dtk, 313,83 GB dari kuota gratis 1 TiB/bulan, biaya 0.
- **Hasil** `hasil/gdelt_daily_counts.csv` (15.722 baris, 1.836 hari 2018-12-22..2023-12-31, sha256 di `hasil/gdelt_bq_manifest.json`): median
  7.811 artikel Indonesia/hari (min 241 = gangguan GDELT); judul unik per kelompok 2018-12..2023-12: beras 40.405, minyak goreng 30.484, telur 14.126,
  gula 13.729, cabai 12.965, bawang putih 6.366, daging sapi 4.827, bawang merah 3.297, daging ayam 2.940, umum 75.141.
- **Layar G5** (`b_gdelt_screen.py --tag gdelt`, sha256 skrip & protokol = versi beku; satu kali jalan) → `hasil/b_screen_gdelt.csv`:

| Set | ΔAUC h 4 (interval) | ΔAUC h 8 (interval) | q BH h 4 / h 8 | Lolos G5 |
|---|---|---|---|---|
| V volume | −0,003 (−0,009..+0,001) | −0,003 (−0,006..+0,000) | 0,46 / 0,46 | tidak |
| D gangguan | −0,004 (−0,015..+0,003) | −0,000 (−0,003..+0,002) | 0,47 / 0,85 | tidak |
| P kebijakan | −0,001 (−0,004..+0,000) | −0,004 (−0,012..+0,002) | 0,46 / 0,58 | tidak |
| S stabilisasi + pasokan | +0,001 (−0,007..+0,005) | −0,003 (−0,005..+0,002) | 0,90 / 0,58 | tidak |
| ALL (5 kolom) | −0,005 (−0,020..+0,005) | −0,008 (−0,016..+0,003) | 0,47 / 0,47 | tidak |
| *kontrol POS `iw_gap_nat`* | *+0,015 (−0,002..+0,030)* | *−0,004 (−0,023..+0,008)* | *0,38 / 0,81* | *tidak* |

AUC konsensus C1t 0,762 / 0,756; akurasi arah nasional konsensus 0,698 / 0,694, dengan fitur berita 0,684–0,698 / 0,688–0,694.
**Keputusan: GDELT REJECTED (gagal G5), tanpa modeling provinsi.** Kegagalan ini bukan soal daya: titik estimasi ≤ 0 untuk 9 dari 10 sel dan jauh
di bawah kontrol positif; menambahkan intensitas berita justru sedikit memperburuk AUC walk-forward (derau di atas konsensus). Tafsiran yang
konsisten dengan pilot: berita pangan Indonesia sebagian besar mengikuti harga (laporan harga, stabilisasi sesudah kenaikan) dan peristiwa ex-ante
(kebijakan dagang) terlalu jarang untuk menggerakkan arah nasional mingguan. U113 ditutup.
