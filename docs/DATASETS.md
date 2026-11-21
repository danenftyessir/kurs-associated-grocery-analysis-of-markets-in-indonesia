# Dokumentasi Dataset

Registry mesin: [`configs/sources.yaml`](../configs/sources.yaml) (path relatif `Config.raw_dir`; lokal = `data/raw/`).
Loader: `src/data/loaders.py` (`LOADERS`). Hash & waktu ambil: `data/raw/checksums.csv` (`python -m kagami snapshot`).
Fakta di bawah diverifikasi pada snapshot 2026-11-20 (24 file). Inventaris tim versi spreadsheet:
`docs/arsip/Inventaris Dataset (20 Nov 2026).xlsx` (arsip; dokumen ini yang berlaku).

## Distribusi ke anggota (D-101)
Semua data mentah ada di folder Drive tim, subfolder `data/raw/` dengan path yang sama seperti lokal
(https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D). Tidak perlu kirim manual:
- Danen (pemilik snapshot) mengunggah/memperbarui: `python -m kagami drive-push-raw` (file dengan MD5 sama dilewati).
- Anggota lain mengambil: `python -m kagami drive-pull-raw` (hanya file yang belum ada; tidak pernah menimpa).
- Notebook 00 memanggil `drive.pull_raw` otomatis; di Kaggle dataset `kagami-raw` jadi opsional.
- Folder dibagikan **hanya** ke akun anggota tim (data tanpa hak redistribusi, U24). Kredensial: `docs/NOTEBOOKS.md`.

## Ringkasan

| Kunci | Isi | Cakupan terverifikasi | Peran | Kirim mentah? |
|---|---|---|---|---|
| `pihps` | PIHPS harian pasar tradisional, 34 prov × 31 baris (10 komoditas + 21 varian) | 2017-03-28 .. 2026-11-19 | Outcome | Tidak |
| `jisdor` | JISDOR IDR/USD harian | 2013-05-20 .. 2026-11-18 (3.269 hari) | Penggerak 1 | Tidak |
| `pinksheet` | Pink Sheet bulanan USD | 1960-01 .. 2026-10 (update 3 Nov 2026) | Penggerak 2 | Ya (CC BY 4.0) |
| `brent` | FRED DCOILBRENTEU harian | 2013-01-02 .. 2026-11-11 | Kontrol | Ya |
| `dollar_index` | FRED DTWEXBGS harian | 2013-01-02 .. 2026-11-13 | Robustness | Ya |
| `faostat_sua` | FAOSTAT SUA Crops & Livestock, Asia | 2010 .. 2023 tahunan | Rasio impor | Ya (CC BY 4.0) |
| `bps_import_monthly` | Impor HS8 bulanan (USD, kg), **v2**: 111 kode HS8 termasuk bawang putih 070320 | 2023-01 .. 2026-09 (2.845 baris) | Cek silang rasio impor | Tidak |
| `bps_import_annual` | 5 file portal exim BPS, total tahunan HS8 | 2023 .. 2026 (parsial) | QA | Tidak |
| `comtrade_import` | UN Comtrade impor Indonesia HS4/HS6 bulanan (15 kode; tanpa kedelai 1201) | 2017-01 .. 2022-12 | Rasio impor pra-2023 | Tidak |
| `konkordansi_hs` | Pemetaan 15 kode Comtrade (HS2017/HS2022) → HS8 BPS + keyakinan + rasio nilai 2022 vs 2023 (buatan tim) | statis | Jembatan impor 2017–2026 (WP-07) | Ya |
| `bapanas_panel` | Panel Harga Bapanas, rerata geometrik bulanan provinsi | 2022-01 .. 2026-10, 38 prov | Cek bias / Tier 2 | Tidak |
| `bapanas_het_settings` | Riwayat setting HET/HAP Panel Harga | 2024 .. 2026 | Regulasi | Tidak |
| `padi_2024`, `padi_2025` | BPS luas panen, produktivitas, produksi padi (GKG) per provinsi | 2024, 2025, 38 prov | Kecukupan produksi | Tidak |
| `konsumsi_beras` | Konsumsi beras RT kg/kapita/tahun per provinsi | 2023 .. 2025 | Kecukupan produksi | Tidak |
| `neraca_beras` | Neraca beras nasional (ton) | 2023 .. 2026 | Cek silang impor beras | Tidak |
| `hortikultura_produksi` | Produksi bawang merah, bawang putih, cabai besar, cabai rawit per provinsi (ATAP 2024 Kementan) | 2020 .. 2024, 38 prov | Rasio impor bawang putih (U5), kecukupan produksi (U11) | Tidak |
| `penduduk` | Penduduk provinsi 2025 BPS (`optional`; disalin dari tabel BPS 2026-11-21, D-123) | 2025, 38 prov | Kebutuhan beras → `rice_sufficiency` (U14) | Tidak |
| `n_kota` | Kota sampel pasar tradisional PIHPS per provinsi (situs PIHPS 2026-11-21, `optional`, D-123) | 34 prov, 110 kota | `n_kota` (U15) | Ya |
| `gkg_beras` | Faktor konversi GKG → beras untuk konsumsi pangan per tahun (rilis BPS, `optional`, D-123) | 2024, 2025 | `rice_sufficiency` (U21) | Ya |
| `jarak_hub` | Jarak garis lurus ibu kota ke Jakarta/Surabaya/Makassar + ln jarak (buatan tim) | statis, 38 prov | Cek silang `dist_hub_km` (WP-07) | Ya |
| `het_hap_current` | Nilai HET/HAP berlaku per komoditas × zona (buatan tim; revisi 2026-11-20) | 30 baris, status 2026-11-19 | Regulasi | Ya |
| `regulation_history` | Riwayat HET/HAP/HPP (buatan tim; revisi 2026-11-20) | 23 baris, 2020 .. 2025 | Regulasi (E2) | Ya |

### Menunggu diunggah (lokasi sudah dialokasikan; daftarkan di `sources.yaml` setelah file ada)

| Kunci (rencana) | File | Lokasi | Peran | Status |
|---|---|---|---|---|
| `bapanas_kabkota` | `panelharga_konsumen_kabkota_snapshot_2026-10.csv` (497 kab/kota, 5.885 baris) | `data/raw/bapanas/` | Opsional: heterogenitas dalam provinsi / bias rerata kota PIHPS | sudah diunduh Danen ke Downloads |

### Versi lama (tidak dipakai; `data/raw/_superseded/`, tidak diunggah ke Drive)
| File | Digantikan oleh | Alasan |
|---|---|---|
| `_superseded/bi_pihps/pihps_pasar_tradisional_harian_2017-2026_retrieved_2026-11-18.zip` | `bi_pihps/..._v2_merged_...zip` | snapshot pra-merge, ditandai rusak di inventaris (D-102) |
| `_superseded/bps_trade/bps_import_hs8_monthly_2023_2026.csv` | `bps_trade/bps_import_hs8_monthly_2023_2026_v2.csv` | v1 hanya 16 baris bawang putih 070320 (v2: 59) |
| `_superseded/manual_regulation/het_hap_current_2026-11-19.csv` | `manual_regulation/het_hap_current_2026-11-20.csv` | tanggal, nomor, URL sumber diperbarui |
| `_superseded/manual_regulation/regulation_history_2026-11-19.csv` | `manual_regulation/regulation_history_2026-11-20.csv` | 20 → 23 baris; nomor BN & URL diperbarui |

Menghapus permanen file lama adalah keputusan Danen (inventaris tim: "Hapus file lama atau rusak").

## Detail per sumber (format mentah → keluaran loader)

### PIHPS (`pihps`)
- Zip berisi 34 CSV `pihps_provNN_<Nama>.csv` (+ `MANIFEST.csv`, `ERRORS.json` kosong di v2). Format lebar: kolom
  `province_id, province, level, commodity, <tanggal...>`. Baris level 1 = komoditas, level 2 = varian di bawahnya.
- MANIFEST v2: endpoint `WebSite/TabelHarga/GetGridDataDaerah`, `price_type=1 (Pasar Tradisional)`, harian,
  retrieved_at 2026-11-18T17:54Z, sha256 per file. **Lihat U19**: apakah ini "fitur unduh resmi" menurut proposal v4.
- Loader → `date, province_id, province, level, commodity_group, item, price` (float Rp; NaN = tidak teramati).
- 10 komoditas level-1: Beras, Daging Ayam, Daging Sapi, Telur Ayam, Bawang Merah, Bawang Putih, Cabai Merah,
  Cabai Rawit, Minyak Goreng, Gula Pasir. 21 varian (lihat `commodities.yaml` untuk varian representatif).
- **Urutan baris tidak bisa diandalkan:** file v2 "merged" menaruh varian hasil penggabungan di akhir file. Grup varian
  ditentukan dari prefiks nama (D-022).
- Cakupan mingguan 2018-01..2026-11 (porsi minggu dengan ≥ 1 hari teramati, rerata provinsi): varian representatif 0,998,
  kecuali Cabai Rawit Merah 0,944 (absen di Sumbar; Aceh & Kepri ~90% kosong, U23). Minyak Goreng Curah 0,957
  (absen di Babel; Maluku & Papua Barat berhenti 2023/2021) → diganti Kemasan Bermerk 1 (D-023).
- Harga sangat kaku untuk komoditas yang diatur: ≥ 85% minggu beras, daging sapi, gula berisi rangkaian nilai identik ≥ 5 hari (U22).
- Kejanggalan diketahui: spasi di akhir `Cabai Merah Keriting ` (ditangani `norm_name`); lonjakan satu hari
  (Papua, Beras level 1, 2017-07-03: 15.800/29.750 lalu 9.500) → QA WP-10; tanggal 2026-11-19 sebagian kosong.
- Minggu 2022-05-02 (Idulfitri 2022): tidak ada provinsi teramati di Sumatra, Jawa, Bali–NT, Sulawesi, Maluku → sel wilayah
  NaN di `panel_weekly_region` (WP-08).
- Snapshot pra-merge (`pihps_pasar_tradisional_harian_2017-2026_retrieved_2026-11-18.zip`) dipensiunkan ke
  `data/raw/_superseded/bi_pihps/` (D-102): inventaris tim menandainya rusak; tidak dipakai, tidak diunggah ke Drive.
- Harga provinsi = rerata kota sampel (82 kota, 2 pasar/kota, 2 pedagang/komoditas) → derau berbeda antarprovinsi.

### JISDOR (`jisdor`)
- Excel BI, header di baris 5: `NO, Tanggal ("5/20/2013 12:00:00 AM"), Kurs ("9.760,00")`.
- Loader → `date, idr_per_usd`. Nilai terakhir 18.252 (2026-11-18). Perubahan metodologi 2021-04-05 (V3); PADG 7/2026 (U3).
- Episode depresiasi (Σ de 8 minggu ≥ 3%, `episodes`, WP-06): 13 episode 2018–2026 (2018 ×3, 2020 ×2, 2021, 2022, 2023,
  2024 ×2, 2025, 2026 ×2), 61 minggu; terbesar Mar–Mei 2020 (Σ maks 0,185).

### Pink Sheet (`pinksheet`)
- Sheet `Monthly Prices`: baris 4 nama seri, baris 5 satuan, data mulai baris 6 dengan kode `YYYYMmm`; "…" = kosong.
- Loader → `month, series, unit, usd_price`; nama dinormalisasi (trim, buang `**`): `Beef **` → `Beef`, `Rice, Thai 5% ` → `Rice, Thai 5%`.
- Seri dipakai: `Rice, Thai 5%` ($/mt), `Sugar, world` ($/kg), `Palm oil` ($/mt), `Maize` ($/mt), `Soybean meal` ($/mt), `Beef` ($/kg).
- **Keaslian terverifikasi 2026-11-20 (U101 🟢):** rilis resmi terbaru di worldbank.org ("Updated on November 03, 2026")
  identik byte-per-byte dengan file tim (SHA-256 `3c8d9d8d…`); lembar `Mismatch Details` memang bagian file resmi.
  Loader hanya membaca `Monthly Prices`. Rilis lama (Jan 2025) berbeda ≤ 0,005 pada data historis → World Bank merevisi
  angka lama antar rilis; selalu catat tanggal rilis.
- URL berubah tiap rilis (U16): `python -m kagami download pinksheet` mencari tautan terbaru di
  https://www.worldbank.org/en/research/commodity-markets (`landing_url` + `link_pattern` di sources.yaml).

### FRED (`brent`, `dollar_index`)
- CSV `observation_date, <SERIES>`; hari libur kosong (dibuang loader). Loader → `date, value`.

### FAOSTAT SUA (`faostat_sua`)
- Zip bulk Asia; file dipakai `SUA_Crops_Livestock_E_Asia_NOFLAG.csv` (latin1), format lebar `Y2010..Y2023`.
- Loader (filter Indonesia) → `year, item, element, unit, value`. Element relevan: `Production`, `Import quantity`,
  `Export quantity`, `Stock Variation`, `Feed`, `Food supply quantity (tonnes)`.
- **Tidak ada item bawang putih kering** (hanya `Green garlic`) → U5; pengganti: produksi `hortikultura_produksi` +
  impor BPS/Comtrade pos 070320. Bawang merah: `Onions and shallots, dry (excluding dehydrated)`; cabai: `Chillies and peppers, green ...`.

### Impor BPS & Comtrade
- `bps_import_monthly` (v2): `hs8_code` (str, jaga nol depan), `month`, `import_value_usd`, `import_netweight_kg`.
  111 kode HS8; prefiks: 0102 0201 0202 0207 0407 0703 0709 0904 1005 1006 1511 1517 1701 2304. Total tahunan cocok
  dengan pivot portal BPS.
- `bps_import_annual` (5 xlsx, nama file = prefiks HS di dalamnya): kolom `Totals` = **USD** (Σ bulanan 2023 / total = 1,000).
  Inventaris tim hanya mencantumkan 3 dari 5 file (00.32.33, 00.34.59, 00.38.01); kelima file tetap terdaftar.
- `comtrade_import`: `hs_code` HS4/HS6 (070310 bawang merah, 070320 bawang putih, 070960/090421 cabai), `net_weight_kg`,
  `cif_usd`. Kedelai HS 1201 tidak ada (celah 2017–2022 bila kedelai dipakai).
- `konkordansi_hs`: 15 baris; kolom `comtrade_code` (str), `bps_hs8_prefix` (str), `bps_hs8_codes_in_file`,
  `keyakinan_pemetaan`, `comtrade_2022_usd_total`, `bps_2023_usd_total`, `rasio_bps2023_per_comtrade2022`, `catatan`.
  Perubahan HS2017→HS2022 hanya 0709.59 (dari transkripsi sekunder). Uji tumpang tindih Comtrade vs BPS Apr–Des 2022 belum
  bisa dijalankan karena server ekspor-impor BPS error (U102).

### Bapanas
- `bapanas_panel`: 13 komoditas Bapanas (nama berbeda dari PIHPS, mis. `Bawang Putih Bonggol`, `Minyakita`, `Gula Konsumsi`)
  → pemetaan ke id internal di WP-10 (U20). Provinsi 38 → `province_id` 34 lewat alias (`D.I Yogyakarta`, pemekaran Papua).
- `bapanas_het_settings`: HET/HAP per zona dengan `start_date/end_date`.
- Panel kab/kota bulanan penuh butuh ~28 ribu panggilan API (16–20 jam); yang ada hanya snapshot Okt 2026 (menunggu diunggah).

### BPS pangan & hortikultura
- `padi_2024`: CSV dengan 4 baris judul, nama provinsi UPPERCASE. `padi_2025`: header normal. Keduanya 38 provinsi + `INDONESIA`
  (dibuang). Produksi dalam ton GKG (bukan beras) → konversi GKG→beras wajib didokumentasikan di WP-07 (U21).
- `konsumsi_beras`: kg/kapita/tahun 2023–2025. Kecukupan produksi butuh **populasi provinsi** (CSV 2025 menunggu diunggah, U14).
- `neraca_beras`: nasional, 2025 berstatus proyeksi (update 5 Mei 2026).
- `hortikultura_produksi`: 780 baris (4 komoditas × 39 baris provinsi/nasional × 5 tahun). Loader → `commodity_atap`
  (`bawang_merah`, `bawang_putih`, `cabai_besar_group`, `cabai_rawit`), `province_raw`, `province_id`, `year`,
  `production_ton`, `note`; baris nasional dibuang; "-" di sumber = tanpa data. Total nasional cocok; 148/152 nilai 2023 sama
  dengan BPS (4 selisih pembulatan). ATAP berhenti di 2024.

### Geografi (buatan tim)
- `jarak_hub`: 38 provinsi; loader → `province_raw, province_id, capital, lat, lon, km_jakarta, km_surabaya, km_makassar,
  nearest_hub, dist_hub_km, ln1p_dist_hub`. Koordinat ibu kota perkiraan; `ln_jarak_km` kosong untuk 3 provinsi hub (pakai
  `ln1p_dist_hub`, D-018). Pemekaran Papua dipetakan ke induk sehingga `province_id` 33/34 berulang (WP-07 memilih ibu kota induk).

### Sumber manual WP-07 (`optional`, boleh belum ada)
- `penduduk` (`bps_kependudukan/penduduk_provinsi_2025.csv`): skema CSV BPS belum dipastikan; loader mencari kolom provinsi + satu kolom numerik,
  membaca satuan dari nama kolom ('ribu'/'juta') dan menolak total di luar 200–400 juta jiwa. File 2026-11-21: salinan tabel BPS
  "Penduduk, Laju Pertumbuhan Penduduk, … Menurut Provinsi, 2025" (diperbarui 2 Mei 2025, berbasis proyeksi sebelum SUPAS 2025),
  kolom `Provinsi`, `Jumlah Penduduk 2025 (Ribu)`; 38 provinsi → 34 (pemekaran Papua ke induk), total 284,44 juta jiwa.
- `n_kota` (`manual_pihps/n_kota.csv`): `province_id, province, n_kota, kota_list, source_url` (PEMBAGIAN_TUGAS §6.2). Isi 2026-11-21
  dari daftar kabupaten/kota pasar tradisional di situs PIHPS (`GetRefRegency`, price_type_id = 1): 110 kota, 1 (DKI, DIY, Bengkulu,
  Maluku Utara) sampai 12 (Jawa Tengah). `province_id` dipetakan dari nama (nomor provinsi situs PIHPS berbeda dari kerangka proyek).
  Daftar ini kondisi 2026; jumlah kota sampel per provinsi di awal periode (2018) bisa berbeda.
- `gkg_beras` (`manual_conversion/gkg_beras.csv`): `year, factor, source_url, note`. Faktor 0,5762 untuk 2024 dan 2025 = produksi beras
  untuk konsumsi pangan penduduk / produksi padi GKG (30,62/53,14 dan 34,69/60,21 juta t, rilis BPS 2 Feb 2026, angka tetap 2025);
  setara rantai BPS 0,9318 (GKG diolah) × 0,6402 (rendemen SKGB 2018) × 0,9667 (beras untuk pangan) = 0,5767.
- File belum ada → loader mengembalikan tabel kosong berskema; hasil WP-07 terkait NaN dan pesan `[reference]` dicetak.

### Regulasi (buatan tim)
- `het_hap_current` (30 baris) dan `regulation_history` (23 baris), revisi 2026-11-20 dengan tanggal, nomor BN, dan URL
  sumber diperbarui; sebagian masih "sebagian terverifikasi". Kolom `verification` wajib dibawa ke `regulation.csv` (U6).
  Zona HET beras (Kepbadan 299/2025) tercermin di `region_crosswalk.csv: het_zone_beras`.
- Belum terselesaikan (U6): sumber HET Minyakita Rp15.700 (Kepmendag 1028/2024 vs Permendag 18/2024, status JDIH
  "tidak berlaku" vs berita 26 Okt 2026); tanggal diundangkan Perbadan 4, 5, 6/2024; teks Kepbadan 299/2025; nomor & tanggal
  regulasi HET beras premium.

## Tabel referensi buatan tim (`data/reference/`, CC BY 4.0)

| File | Isi | Status |
|---|---|---|
| `region_crosswalk.csv` | 34 provinsi: id PIHPS, wilayah (7), ibu kota + koordinat, zona HET beras, flag Jawa | ✅ dibuat WP-00 (koordinat ibu kota perkiraan ±0,01°; Kalsel = Banjarmasin, Malut = Sofifi) |
| `province_aliases.csv` | Alias nama provinsi BPS/Bapanas + pemekaran Papua → induk | ✅ |
| `concordance.csv`, `exposure.csv`, `regulation.csv`, `province_features.csv` | Hasil WP-07 | 🔶 kode selesai 2026-11-20; ditulis `stage0` setelah data mentah lengkap; final 24 Nov |

## Asal file (pemetaan nama asli → path baru)

| Nama asli di `data/` | Path sekarang | Dipindah |
|---|---|---|
| `Informasi Kurs Jisdor.xlsx` | `data/raw/bi_jisdor/jisdor_daily.xlsx` | 2026-11-20 |
| `pihps_..._v2_merged_retrieved_2026-11-18.zip` | `data/raw/bi_pihps/` (nama tetap) | 2026-11-20 |
| `pihps_..._retrieved_2026-11-18.zip` (pra-merge) | `data/raw/_superseded/bi_pihps/` (D-102) | 2026-11-20 |
| `CMO-Historical-Data-Monthly.xlsx` | `data/raw/wb_pinksheet/` | 2026-11-20 |
| `DCOILBRENTEU.csv`, `DTWEXBGS.csv` | `data/raw/fred/` | 2026-11-20 |
| `SUA_Crops_Livestock_E_Asia.zip` | `data/raw/faostat/` | 2026-11-20 |
| `bps_import_hs8_monthly_2023_2026.csv` | `data/raw/_superseded/bps_trade/` (digantikan v2) | 2026-11-20 |
| `bps_import_hs8_monthly_2023_2026_v2.csv` | `data/raw/bps_trade/` | 2026-11-20 |
| `exim_www.bps.go.id_Kamis, 19 November 2026 pukul 00.32.33.xlsx` | `data/raw/bps_trade/exim_annual_0703_0904_1006.xlsx` | 2026-11-20 |
| `... 00.34.59.xlsx` | `data/raw/bps_trade/exim_annual_0201_0202_0703_1517_1701_2304.xlsx` | 2026-11-20 |
| `... 00.36.19.xlsx` | `data/raw/bps_trade/exim_annual_1005_1511_1517.xlsx` | 2026-11-20 |
| `... 00.37.22.xlsx` | `data/raw/bps_trade/exim_annual_0102_0207_0407.xlsx` | 2026-11-20 |
| `... 00.38.01.xlsx` | `data/raw/bps_trade/exim_annual_0407_0709.xlsx` | 2026-11-20 |
| `comtrade_idn_import_HS_monthly_2017_2022.csv` | `data/raw/comtrade/` | 2026-11-20 |
| `konkordansi_hs_comtrade_bps_2017_2026.csv` | `data/raw/manual_concordance/` | 2026-11-20 |
| `panelharga_konsumen_bulanan_provinsi_2022_2026.csv`, `panelharga_setting_het_hap_riwayat.csv` | `data/raw/bapanas/` | 2026-11-20 |
| `Luas Panen, Produksi, dan Produktivitas Padi Menurut Provinsi, 2024.csv` | `data/raw/bps_pangan/padi_provinsi_2024.csv` | 2026-11-20 |
| `Luas Panen, Produktivitas, dan Produksi Padi Menurut Provinsi, 2025.csv` | `data/raw/bps_pangan/padi_provinsi_2025.csv` | 2026-11-20 |
| `beras_konsumsi_rumah_tangga_provinsi_2023_2025.csv`, `neraca_beras_nasional_2023_2026.csv` | `data/raw/bps_pangan/` | 2026-11-20 |
| `produksi_hortikultura_provinsi_2020_2024_atap2024.csv` | `data/raw/kementan_hortikultura/` | 2026-11-20 |
| `jarak_ibukota_provinsi_ke_hub_38prov.csv` | `data/raw/manual_geo/` | 2026-11-20 |
| `het_hpp_draft (2).csv` (versi 19 Nov) | `data/raw/_superseded/manual_regulation/het_hap_current_2026-11-19.csv` | 2026-11-20 |
| `het_hpp_draft.csv` (revisi 20 Nov) | `data/raw/manual_regulation/het_hap_current_2026-11-20.csv` | 2026-11-20 |
| `regulation_history (1).csv` (versi 19 Nov) | `data/raw/_superseded/manual_regulation/regulation_history_2026-11-19.csv` | 2026-11-20 |
| `regulation_history.csv` (revisi 20 Nov) | `data/raw/manual_regulation/regulation_history_2026-11-20.csv` | 2026-11-20 |
| `Inventaris Dataset RupiahPass (20 Nov 2026) (1).xlsx` | `docs/arsip/Inventaris Dataset (20 Nov 2026).xlsx` | 2026-11-20 |

## Menambah atau memperbarui sumber
1. Simpan file di `data/raw/<sumber>/` (jangan timpa file lama; versi baru = nama baru, versi lama → `data/raw/_superseded/`).
2. Tambah/ubah entri di `configs/sources.yaml`. 3. Tambah loader + entri `LOADERS` + `EXPECTED` di `tests/test_loaders.py`.
4. `python -m kagami snapshot`. 5. `python -m kagami drive-push-raw` agar anggota lain bisa `drive-pull-raw`.
6. Perbarui file ini dan CLAUDE.md §10 (§3.4).
