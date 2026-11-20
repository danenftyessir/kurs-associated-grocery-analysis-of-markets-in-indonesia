# Dokumentasi Dataset

Registry mesin: [`configs/sources.yaml`](../configs/sources.yaml) (path relatif `Config.raw_dir`; lokal = `data/raw/`, Kaggle = dataset privat `kagami-raw`). Loader: `src/data/loaders.py` (`LOADERS`).
Hash & waktu ambil: `data/raw/checksums.csv` (`python -m kagami snapshot`). Fakta di bawah diverifikasi pada snapshot 2026-11-20.

## Ringkasan

| Kunci | Isi | Cakupan terverifikasi | Peran | Kirim mentah? |
|---|---|---|---|---|
| `pihps` | PIHPS harian pasar tradisional, 34 prov × 31 baris (10 komoditas + 21 varian) | 2017-03-28 .. 2026-11-19 | Outcome | Tidak |
| `pihps_v1` | Snapshot PIHPS pra-merge (punya kolom `no`) | sama | QA v1 vs v2 | Tidak |
| `jisdor` | JISDOR IDR/USD harian | 2013-05-20 .. 2026-11-18 (3.269 hari) | Penggerak 1 | Tidak |
| `pinksheet` | Pink Sheet bulanan USD | 1960-01 .. 2026-10 (update 3 Nov 2026) | Penggerak 2 | Ya (CC BY 4.0) |
| `brent` | FRED DCOILBRENTEU harian | 2013-01-02 .. 2026-11-11 | Kontrol | Ya |
| `dollar_index` | FRED DTWEXBGS harian | 2013-01-02 .. 2026-11-13 | Robustness | Ya |
| `faostat_sua` | FAOSTAT SUA Crops & Livestock, Asia | 2010 .. 2023 tahunan | Rasio impor | Ya (CC BY 4.0) |
| `bps_import_monthly` | Impor HS8 bulanan (USD, kg) | 2023-01 .. 2026-09 | Cek silang rasio impor | Tidak |
| `bps_import_annual` | 5 file portal exim BPS, total tahunan HS8 | 2023 .. 2026 (parsial) | QA | Tidak |
| `comtrade_import` | UN Comtrade impor Indonesia HS4/HS6 bulanan | 2017-01 .. 2022-12 | Rasio impor pra-2023 | Tidak |
| `bapanas_panel` | Panel Harga Bapanas, rerata geometrik bulanan provinsi | 2022-01 .. 2026-10, 38 prov | Cek bias / Tier 2 | Tidak |
| `bapanas_het_settings` | Riwayat setting HET/HAP Panel Harga | 2024 .. 2026 | Regulasi | Tidak |
| `padi_2024`, `padi_2025` | BPS luas panen, produktivitas, produksi padi (GKG) per provinsi | 2024, 2025, 38 prov | Kecukupan produksi | Tidak |
| `konsumsi_beras` | Konsumsi beras RT kg/kapita/tahun per provinsi | 2023 .. 2025 | Kecukupan produksi | Tidak |
| `neraca_beras` | Neraca beras nasional (ton) | 2023 .. 2026 | Cek silang impor beras | Tidak |
| `het_hap_current` | Nilai HET/HAP berlaku per komoditas × zona (buatan tim) | status 2026-11-19 | Regulasi | Ya |
| `regulation_history` | Riwayat HET/HAP/HPP (buatan tim) | 2020 .. 2025 | Regulasi (E2) | Ya |

## Detail per sumber (format mentah → keluaran loader)

### PIHPS (`pihps`, `pihps_v1`)
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
  (absen di Babel; Maluku & Papua Barat berhenti 2023/2021) → diganti Kemasan Bermerk 1 (D-023). Varian dengan cakupan 34/34 penuh untuk semua komoditas
  kecuali cabai rawit: lihat tabel di SESSION_LOG 2026-11-20 sesi 2.
- Harga sangat kaku untuk komoditas yang diatur: ≥ 85% minggu beras, daging sapi, gula berisi rangkaian nilai identik ≥ 5 hari (U22).
- Kejanggalan diketahui: spasi di akhir `Cabai Merah Keriting ` (ditangani `norm_name`); lonjakan satu hari
  (Papua, Beras level 1, 2017-07-03: 15.800/29.750 lalu 9.500) → QA WP-10; tanggal 2026-11-19 sebagian kosong.
- Harga provinsi = rerata kota sampel (82 kota, 2 pasar/kota, 2 pedagang/komoditas) → derau berbeda antarprovinsi.

### JISDOR (`jisdor`)
- Excel BI, header di baris 5: `NO, Tanggal ("5/20/2013 12:00:00 AM"), Kurs ("9.760,00")`.
- Loader → `date, idr_per_usd`. Nilai terakhir 18.252 (2026-11-18). Perubahan metodologi 2021-04-05 (V3); PADG 7/2026 (U3).

### Pink Sheet (`pinksheet`)
- Sheet `Monthly Prices`: baris 4 nama seri, baris 5 satuan, data mulai baris 6 dengan kode `YYYYMmm`; "…" = kosong.
- Loader → `month, series, unit, usd_price`; nama dinormalisasi (trim, buang `**`): `Beef **` → `Beef`, `Rice, Thai 5% ` → `Rice, Thai 5%`.
- Seri dipakai: `Rice, Thai 5%` ($/mt), `Sugar, world` ($/kg), `Palm oil` ($/mt), `Maize` ($/mt), `Soybean meal` ($/mt), `Beef` ($/kg).
- URL rilis berubah tiap bulan (U16). Sheet `Mismatch Details` = log perbandingan dari pengunduh, abaikan.

### FRED (`brent`, `dollar_index`)
- CSV `observation_date, <SERIES>`; hari libur kosong (dibuang loader). Loader → `date, value`.

### FAOSTAT SUA (`faostat_sua`)
- Zip bulk Asia; file dipakai `SUA_Crops_Livestock_E_Asia_NOFLAG.csv` (latin1), format lebar `Y2010..Y2023`.
- Loader (filter Indonesia) → `year, item, element, unit, value`. Element relevan: `Production`, `Import quantity`,
  `Export quantity`, `Stock Variation`, `Feed`, `Food supply quantity (tonnes)`.
- **Tidak ada item bawang putih kering** (hanya `Green garlic`) → U5. Bawang merah: `Onions and shallots, dry (excluding dehydrated)`;
  cabai: `Chillies and peppers, green ...`.

### Impor BPS & Comtrade
- `bps_import_monthly`: `hs8_code` (str, jaga nol depan), `month`, `import_value_usd`, `import_netweight_kg`.
  Prefiks HS tersedia: 0102 0201 0202 0207 0407 0703 0709 0904 1005 1006 1511 1517 1701 2304.
- `bps_import_annual` (5 xlsx, nama file = prefiks HS di dalamnya): kolom `Totals` = **USD** (Σ bulanan 2023 / total = 1,000).
- `comtrade_import`: `hs_code` HS4/HS6 (070310 bawang merah, 070320 bawang putih, 070960/090421 cabai), `net_weight_kg`, `cif_usd`.

### Bapanas
- `bapanas_panel`: 13 komoditas Bapanas (nama berbeda dari PIHPS, mis. `Bawang Putih Bonggol`, `Minyakita`, `Gula Konsumsi`)
  → pemetaan ke id internal di WP-10 (U20). Provinsi 38 → `province_id` 34 lewat alias (`D.I Yogyakarta`, pemekaran Papua).
- `bapanas_het_settings`: HET/HAP per zona dengan `start_date/end_date`.

### BPS pangan
- `padi_2024`: CSV dengan 4 baris judul, nama provinsi UPPERCASE. `padi_2025`: header normal. Keduanya 38 provinsi + `INDONESIA`
  (dibuang). Produksi dalam ton GKG (bukan beras) → konversi GKG→beras wajib didokumentasikan di WP-07.
- `konsumsi_beras`: kg/kapita/tahun 2023–2025. Kecukupan produksi butuh **populasi provinsi** (belum ada, U14).
- `neraca_beras`: nasional, 2025 berstatus proyeksi (update 5 Mei 2026).

### Regulasi (buatan tim)
- `het_hap_current` (30 baris) dan `regulation_history` (20 baris): banyak tanggal "tidak terverifikasi" dan sumber berita;
  kolom `verification` wajib dibawa ke `regulation.csv` (U6). Zona HET beras (Kepbadan 299/2025) tercermin di
  `region_crosswalk.csv: het_zone_beras`.

## Tabel referensi buatan tim (`data/reference/`, CC BY 4.0)

| File | Isi | Status |
|---|---|---|
| `region_crosswalk.csv` | 34 provinsi: id PIHPS, wilayah (7), ibu kota + koordinat, zona HET beras, flag Jawa | ✅ dibuat WP-00 (koordinat ibu kota perkiraan ±0,01°; Kalsel = Banjarmasin, Malut = Sofifi) |
| `province_aliases.csv` | Alias nama provinsi BPS/Bapanas + pemekaran Papua → induk | ✅ |
| `concordance.csv`, `exposure.csv`, `regulation.csv`, `province_features.csv` | Hasil WP-07 | ⬜ |

## Asal file (pemetaan nama asli → path baru, dipindah 2026-11-20)

| Nama asli di `data/` | Path sekarang |
|---|---|
| `Informasi Kurs Jisdor.xlsx` | `data/raw/bi_jisdor/jisdor_daily.xlsx` |
| `pihps_..._v2_merged_retrieved_2026-11-18.zip`, `pihps_..._retrieved_2026-11-18.zip` | `data/raw/bi_pihps/` (nama tetap) |
| `CMO-Historical-Data-Monthly.xlsx` | `data/raw/wb_pinksheet/` |
| `DCOILBRENTEU.csv`, `DTWEXBGS.csv` | `data/raw/fred/` |
| `SUA_Crops_Livestock_E_Asia.zip` | `data/raw/faostat/` |
| `bps_import_hs8_monthly_2023_2026.csv` | `data/raw/bps_trade/` |
| `exim_www.bps.go.id_Kamis, 19 November 2026 pukul 00.32.33.xlsx` | `data/raw/bps_trade/exim_annual_0703_0904_1006.xlsx` |
| `... 00.34.59.xlsx` | `data/raw/bps_trade/exim_annual_0201_0202_0703_1517_1701_2304.xlsx` |
| `... 00.36.19.xlsx` | `data/raw/bps_trade/exim_annual_1005_1511_1517.xlsx` |
| `... 00.37.22.xlsx` | `data/raw/bps_trade/exim_annual_0102_0207_0407.xlsx` |
| `... 00.38.01.xlsx` | `data/raw/bps_trade/exim_annual_0407_0709.xlsx` |
| `comtrade_idn_import_HS_monthly_2017_2022.csv` | `data/raw/comtrade/` |
| `panelharga_konsumen_bulanan_provinsi_2022_2026.csv`, `panelharga_setting_het_hap_riwayat.csv` | `data/raw/bapanas/` |
| `Luas Panen, Produksi, dan Produktivitas Padi Menurut Provinsi, 2024.csv` | `data/raw/bps_pangan/padi_provinsi_2024.csv` |
| `Luas Panen, Produktivitas, dan Produksi Padi Menurut Provinsi, 2025.csv` | `data/raw/bps_pangan/padi_provinsi_2025.csv` |
| `beras_konsumsi_rumah_tangga_provinsi_2023_2025.csv`, `neraca_beras_nasional_2023_2026.csv` | `data/raw/bps_pangan/` |
| `het_hpp_draft (2).csv` | `data/raw/manual_regulation/het_hap_current.csv` |
| `regulation_history (1).csv` | `data/raw/manual_regulation/regulation_history.csv` |

## Menambah sumber baru
1. Simpan file di `data/raw/<sumber>/` (jangan timpa file lama). 2. Tambah entri di `configs/sources.yaml`.
3. Tambah loader + entri `LOADERS` + `EXPECTED` di `tests/test_loaders.py`. 4. `python -m kagami snapshot`. 5. Perbarui file ini.
