# GDELT GKG 2.1 — Audit Akses & Kelayakan (Workstream B1, B5)

Tanggal: 2026-11-26 · Keputusan: D-165 · Lanjutan D-160 (U113). Pilot data: [GDELT_PILOT.md](GDELT_PILOT.md).

## 1. Jalur akses yang diperiksa

| Jalur | Hasil pemeriksaan 2026-11-26 | Status |
|---|---|---|
| **DOC 2.0 API** (`api.gdeltproject.org/api/v2/doc/doc`, gratis, tanpa kunci; mode `timelinevolraw`/`artlist`, data sejak 2017) | HTTP 429 "Please limit requests to one every 5 seconds" pada **semua** percobaan: 11.21, 11.27 (jeda 100 dtk), 11.41 (jeda 600 dtk), 15.10 UTC (jeda ± 3,5 jam). Laporan publik November 2026 menyebut hal sama dari jaringan berbeda walau jarak permintaan 20–120 dtk; GDELT mengarahkan pengguna ke dataset lain. | **BLOCKED** (tidak dapat diandalkan; tidak dicoba lagi) |
| **Berkas GKG mentah 15 menit** (`data.gdeltproject.org/gdeltv2/<ts>.gkg.csv.zip` dan `<ts>.translation.gkg.csv.zip`) | Dapat diakses (HTTP 200, tanpa login). Berita **berbahasa Indonesia ada di aliran Translingual** (`srclc:ind`), bukan aliran Inggris (aliran Inggris pada 2 batch sampel: 0 sumber Indonesia). Ukuran batch Translingual dev 3,5–15,7 MB zip (rerata 8,5 MB); seluruh 2019–2023 ≈ 175.000 batch ≈ 1,5 TB zip untuk Translingual saja | layak untuk **sampel** (pilot); tidak layak untuk fitur mingguan lengkap |
| **BigQuery** `gdelt-bq.gdeltv2.gkg_partitioned` (partisi harian `_PARTITIONTIME`) | Butuh proyek Google Cloud. **BigQuery sandbox**: tanpa kartu kredit/billing, kuota 1 TiB kueri per bulan, terkunci sebelum biaya muncul. Pembuatan proyek & persetujuan ketentuan Google Cloud = tindakan akun pengguna. | **dipakai 2026-11-26** (proyek `kagami-gdelt`, tanpa billing; §5) |

## 2. Gerbang G1–G4 (bukti pilot 48 batch, [GDELT_PILOT.md](GDELT_PILOT.md))

| Gerbang | Bukti | Status |
|---|---|---|
| G1 riwayat | 48/48 batch acak 2019-01..2023-12 tersedia; 85–162 artikel berbahasa Indonesia per batch (rerata 130 → ± 12.500/hari) | ✓ |
| G2 ketersediaan | `DATE` = stempel batch 15 menit saat GDELT memproses dokumen (UTC), bukan tanggal peristiwa. Lag `DATE` vs tanggal terbit di URL: median 0 hari, maks 1 hari (49 artikel bertanggal URL). GKG tidak direvisi (append-only). Jendela fitur minggu t = hari UTC Sabtu t−2 .. Jumat t+4 (berakhir Sabtu 06.59 WIB < `available_at` Minggu 00.00 WIB) | ✓ |
| G3 independen dari PIHPS | Sumber berbeda (media). Tetapi sebagian isi **reaktif** terhadap harga: laporan harga eceran 14% dari artikel relevan/sebagian; intervensi stabilisasi (8 dari 25 artikel relevan) umumnya menyusul kenaikan harga. Peristiwa ex-ante murni (kebijakan dagang, gangguan pasokan, produksi) ± 40% dari relevan | sebagian |
| G4 cakupan | Setelah penyaring terbaik (F2d): ± 36 artikel relevan/hari nasional; terkonsentrasi pada minyak goreng (2022), beras, dan "bahan pokok" umum (33% artikel relevan/sebagian tanpa komoditas spesifik). Komoditas lain (bawang putih, gula, ayam, telur, cabai) 0–2 artikel relevan dalam sampel → seri mingguan per komoditas akan jarang. Judul halaman hanya 29% pada 2019 (≥ 99% sejak 2020) → 2019 bergantung pada slug URL | sebagian |
| G5 sinyal nasional tambahan | Diuji 2026-11-26 lewat BigQuery sandbox (adendum [GDELT_PILOT.md](GDELT_PILOT.md) §6): ΔAUC −0,008..+0,001 untuk 5 set × 2 horizon, q ≥ 0,46 | **✗ REJECTED** |

## 3. Kontrol biaya (B5)

- Tidak ada proyek, billing, atau kueri berbayar yang dibuat/dijalankan. Tidak ada kredensial yang dipakai.
- Paket siap jalan: [`scripts/b_bq_daily_counts.sql`](scripts/b_bq_daily_counts.sql) (hitungan harian per kelompok komoditas & kategori, satu kali
  pindai), [`scripts/b_gdelt_screen.py`](scripts/b_gdelt_screen.py) (layar G5), tes [`tests/test_gdelt_screen.py`](tests/test_gdelt_screen.py).

## 4. Estimasi byte BigQuery (sebelum dry-run)

Biaya BigQuery = ukuran kolom yang direferensikan × semua partisi dalam rentang; WHERE tidak mengurangi byte. Kueri hanya memakai `DATE`,
`TranslationInfo`, `SourceCommonName`, `DocumentIdentifier`, `Extras` (tanpa `GCAM` 8,9 KB/rekaman, `V2Themes` 1,2 KB, `V2Locations` 0,4 KB).

| Komponen | Nilai | Sumber |
|---|---|---|
| Byte logis per rekaman (5 kolom; STRING = panjang + 2) | Translingual ± 550 B; Inggris ± 400 B | `hasil/b_gkg_sample_summary.json` (48 batch) + 2 batch Inggris |
| Rekaman per hari | Translingual ± 215.000; Inggris ± 129.000 | rerata batch × 96 |
| Rentang partisi | 2018-12-22 .. 2023-12-31 (1.836 hari) | 52 minggu sebelum origin dev pertama (anomali) s.d. akhir dev |
| **Estimasi pindai** | **± 0,31 TB (0,28 TiB)**; rentang wajar 0,15–0,45 TiB | < kuota sandbox 1 TiB/bulan |
| Pembanding: semua kolom | ± 7,7 TB | alasan tidak memakai `SELECT *` |

Ketidakpastian yang harus ditutup dengan dry-run (gratis, tidak memindai): (a) apakah `gkg_partitioned` memuat rekaman Translingual (diharapkan
ya: skema memiliki `TranslationInfo`) — cek dengan kueri satu partisi `WHERE _PARTITIONTIME = TIMESTAMP('2022-03-15') AND
STARTS_WITH(TranslationInfo,'srclc:ind')` (± 15 MB); (b) ukuran sebenarnya per tahun.

## 5. Langkah persetujuan (`[HUMAN]`, Danen) — dijalankan 2026-11-26

Status: Danen masuk ke akun Google di panel browser dan menyetujui pembuatan sandbox; agent membuat proyek `kagami-gdelt` (tanpa billing),
menjalankan cek partisi (6,89 MB) dan kueri utama (313,83 GB, estimasi validator sebelum jalan). Opsi *Maximum bytes billed* tidak tampil di
tata letak panel sempit; sebagai gantinya dipastikan proyek tidak terhubung ke akun billing (biaya mustahil, kuota sandbox menjadi batas).
Langkah asli:

1. Masuk ke Google Cloud console dengan akun sendiri → BigQuery → aktifkan **sandbox** (tanpa billing). Agent tidak membuat akun/proyek dan
   tidak menerima ketentuan atas nama pengguna.
2. Jalankan kueri cek satu partisi (§4a). Bila jumlah rekaman `srclc:ind` ≈ 10.000–15.000/hari → lanjut.
3. Tempel `b_bq_daily_counts.sql`, set *Maximum bytes billed* = 600 GB, lihat estimasi "This query will process …". **Jalankan hanya bila ≤ 600 GB.**
4. Simpan hasil (± 18.000 baris, < 2 MB) sebagai CSV → `docs/audit/jalur_a_macro_f1/hasil/gdelt_daily_counts.csv` (atau Drive tim).
5. Agent menjalankan `python b_gdelt_screen.py --daily hasil/gdelt_daily_counts.csv --tag gdelt` (protokol beku, [PROTOCOL.md](PROTOCOL.md) §B4).

Lisensi: data GDELT terbuka untuk penelitian (wajib sitasi); hitungan agregat boleh disimpan di repo, isi artikel tidak.
