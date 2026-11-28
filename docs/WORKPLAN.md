# Rencana Pengerjaan (Work Packages)

Pembagian anggota (Danen, Ardell, Abi), jadwal harian, kepemilikan file, dan titik terbit artefak: [PEMBAGIAN_TUGAS.md](PEMBAGIAN_TUGAS.md). Kolom PIC di papan = penanggung jawab WP.

Satu WP = satu unit kerja yang bisa diselesaikan dalam satu sesi agent. Setiap stub di kode memanggil
`todo("WP-xx")` yang menunjuk ke heading di file ini. Spesifikasi rumus: [METHODS.md](METHODS.md).

**Protokol sesi:** implementasi di lapisan `src/` yang ditunjuk WP (ARCHITECTURE §2); jalankan tahapnya lewat
`python -m kagami <tahap>` (ringan) atau notebook tahapnya di Kaggle/Colab (berat; [NOTEBOOKS.md](NOTEBOOKS.md)).
Pilih WP dengan status ⬜ yang semua dependensinya ✅ → ubah status jadi 🔶 →
implementasi + tes → `pytest` hijau → status ✅ → catat di [SESSION_LOG.md](SESSION_LOG.md) (bagian sendiri) → handoff ke anggota lain bila perlu ([HANDOFF.md](HANDOFF.md)).
Keputusan baru → [DECISIONS.md](DECISIONS.md). Masalah tak terselesaikan → [OPEN_ISSUES.md](OPEN_ISSUES.md).
`[HUMAN]` = butuh tindakan manusia (email, unduh manual berizin, video, unggah); agent hanya menyiapkan.

## Gerbang & tenggat (hari ini: 2026-11-20)

| Gerbang | Tanggal | Syarat lolos | Konsekuensi |
|---|---|---|---|
| G6 praregistrasi | 21 Nov | `params.yaml`, varian (D-011), bobot pakan (D-012), hipotesis di PREREGISTRATION.md dibekukan | Perubahan setelahnya wajib dicatat di DECISIONS sebagai deviasi |
| G-power | 23 Nov | `mde.csv` ada (WP-09) | MDE PT(8) > 0,5 untuk bawang putih, gula, minyak goreng → LP mingguan jadi sekunder; event study + profil harga dunia jadi utama; Task 4 jadi kontribusi DM utama (D-007) |
| G-het | 25 Nov | `heterogeneity.csv` ada (WP-18) | Tidak ada komoditas lolos → laporkan nol + batas deteksi (WP-21); clustering tetap jalan (D-004) |
| Pembekuan hasil | 27 Nov | Semua artefak `ship` ada; `results/` tidak diubah lagi kecuali bug | — |
| G7 uji jalan ulang | 28 Nov | WP-32 lolos di folder bersih | — |
| G8 audit klaim | 28 Nov | WP-34 lolos | — |
| Submit | 29 Nov | PDF makalah + zip + video diunggah `[HUMAN]` | Batas resmi 30 Nov |

## Jalur kritis

```
WP-03 → WP-04 → WP-05/06 → WP-08 → WP-09 (G-power) → WP-13 → WP-15 → WP-16 → WP-17 → WP-18 (G-het) → WP-19..21 → WP-31/33 → WP-32/34
                         ↘ WP-25 → WP-26 → WP-27  (Task 4 paralel)
WP-07 (paralel dengan WP-05) → WP-22/23
```

## Papan status

| WP | Judul | Status | PIC | Bergantung | Tenggat |
|---|---|---|---|---|---|
| WP-00 | Skeleton & dokumen agent | ✅ | – | – | 20 Nov |
| WP-01 | Snapshot & checksum | ✅ | – | – | 20 Nov |
| WP-02 | Loader semua sumber | ✅ | – | – | 20 Nov |
| WP-03 | Varian + agregasi mingguan + status sel | ✅ | – | 02 | 20 Nov |
| WP-04 | Kelayakan seri | ✅ | – | 03 | 20 Nov |
| WP-05 | Penggerak mingguan & harga dunia rupiah | ✅ | – | 02 | 21 Nov |
| WP-06 | Episode depresiasi & tabel variasi kurs | ✅ | Danen | 05 | 21 Nov |
| WP-07 | Tabel buatan tim (concordance, exposure, regulation, province_features) | ✅ | Danen ← Ardell | 02 | 22 Nov |
| WP-08 | Panel 7 wilayah | ✅ | Danen | 04 | 21 Nov |
| WP-09 | MDE / analisis daya (G-power) | ✅ | Danen | 05, 08 | 23 Nov |
| WP-10 | QA silang & laporan Tahap 0 | ✅ | Danen | 03–09 | 23 Nov |
| WP-11 | Praregistrasi & pembekuan (G6) | ✅ | Danen + Abi | – | 21 Nov |
| WP-12 | Mesin statistik bersama | ✅ | – | – | 20 Nov |
| WP-13 | LP nasional + asimetri + PT (`build_design`/`fit_lp` terbit 22 Nov untuk WP-15) | ✅ | Danen | 05, 09 | 23 Nov |
| WP-14 | Event study per episode | ✅ | Danen | 06, 08 | 23 Nov |
| WP-15 | Deviasi provinsi & profil wilayah | ✅ | Danen ← Ardell | 13 | 24 Nov |
| WP-16 | Bootstrap bersama & plasebo | ✅ | Danen ← Ardell | 13, 15 | 24 Nov |
| WP-17 | Penyusutan EB & fitur respons | ✅ | Danen ← Ardell | 16 | 24 Nov |
| WP-18 | Heterogenitas vs plasebo (G-het) | ✅ | Danen | 16 | 25 Nov |
| WP-19 | Clustering & pemilihan k | ✅ | Danen ← Ardell | 17 | 25 Nov |
| WP-20 | Stabilitas & pembanding partisi | ✅ | Danen ← Ardell | 19 | 25 Nov |
| WP-21 | Uji struktur tertanam | ✅ | Danen | 19 | 26 Nov |
| WP-22 | Asosiasi level komoditas (Kendall) | ✅ | Danen | 07, 17 | 25 Nov |
| WP-23 | Meta-regresi provinsi | ✅ | Danen ← Ardell | 07, 16 | 26 Nov |
| WP-24 | Robustness FE komoditas×minggu (3c) | ✅ | Danen ← Ardell | 23 | 26 Nov (dapat dipotong) |
| WP-25 | Fitur Task 4 + as-of join | ✅ | Danen ← Ardell | 05, 08 | 22 Nov |
| WP-26 | Model M0–M3 rolling-origin | ✅ | Danen ← Ardell | 25 | 24 Nov |
| WP-27 | Evaluasi DM & ablation | ✅ | Danen | 26 | 25 Nov |
| WP-28 | Robustness Tier 1 | ✅ | Danen | 13 | 26 Nov |
| WP-29 | Validasi V2 & V4 | ✅ | Danen | 14, 27 | 26 Nov |
| WP-30 | Robustness Tier 2 | ✅ | Danen | 28 | opsional |
| WP-31 | Halaman Streamlit final | ✅ | Danen ← Ardell | 17–29 | 27 Nov |
| WP-32 | Paket juri & uji jalan ulang (G7) | ✅ | Danen ← Ardell | 31 | 28 Nov |
| WP-33 | Temuan & makalah | ✅ | Danen ← Abi | 17–29 | 28 Nov |
| WP-34 | Audit klaim (G8) | ✅ | Danen ← Abi | 31, 33 | 28 Nov |
| WP-35 | Tugas manusia | ⬜ | Danen ← Abi | – | lihat item |
| WP-36 | Log eksekusi & evaluasi terpusat + app hal. 7 | ✅ | Danen | 31 | 24 Nov |

Urutan pemotongan bila waktu habis (D-014): WP-30 → analisis dalam-komoditas & Moran's I → WP-24 → M3 di WP-26.
**Tidak pernah dipotong:** WP-28 (Tier 1), distribusi plasebo (WP-16/18/19), MDE (WP-09).

---

## Tahap 0 — fondasi data
Pipeline `pipelines.stage0` · notebook `00_stage0_data` · ringan (lokal).

### WP-00 — Skeleton & dokumen agent ✅
Paket `kagami`, CLI, registry artefak, app 6 halaman (menampilkan "menunggu hasil"), tes wiring, dokumen `docs/`.
Data mentah dipindah ke `data/raw/<sumber>/` (pemetaan nama: DATASETS.md §Asal file).
v2 (2026-11-20): `src/` berlapis (utils/data/features/models/evaluation/stats/pipelines/viz, D-026) + 6 notebook per tahap
yang jalan di lokal/Kaggle/Colab (`utils/env.py`, `bundle`, D-027). Runbook: NOTEBOOKS.md.

### WP-01 — Snapshot & checksum ✅
`src/data/snapshot.py`. `python -m kagami snapshot` → `data/raw/checksums.csv` (semua file sumber). Jalankan ulang setiap ada snapshot baru.

### WP-02 — Loader semua sumber ✅
`src/data/loaders.py`, registry `LOADERS` = semua kunci `configs/sources.yaml`. Tes: `tests/test_loaders.py` (semua sumber, pemetaan 34 provinsi).

### WP-03 — Varian representatif + agregasi mingguan + status sel ✅
- File: `src/data/weekly.py` (`select_variants`, `aggregate_weekly`, `_aggregate`, `_carry_forward_flags`); tes `tests/test_weekly.py`.
- Output: `pihps_daily` (795.174 baris hari teramati), `panel_weekly` (157.760 = 34 × 10 × 464 minggu, 2018-01-01..2026-11-16; kolom ekstra `cf_share`).
- Selesai:
  - [x] Grid lengkap, status ∈ {observed, carry_forward, short, missing}, prioritas D-021.
  - [x] Tes sintetis (hari kosong, rangkaian identik melintasi hari kosong, minggu 2 hari) + tes data asli.
  - [x] Distribusi status di SESSION_LOG 2026-11-20 sesi 2.
- Bug loader ditemukan & diperbaiki: grup varian kini dari prefiks nama (D-022).
- **Konsumen hilir:** `carry_forward` = penanda informatif, BUKAN filter (U22); kelayakan WP-04 hanya memakai `missing`.

### WP-04 — Kelayakan seri ✅
- File: `src/data/weekly.py::eligibility` → `results/stage0/eligibility.csv`; tes `test_eligibility_*` di `tests/test_weekly.py`.
- Selesai: [x] ambang dari `params.eligibility` (batas inklusif); [x] 340 seri dilaporkan, 337 layak;
  [ ] ringkasan per komoditas di laporan Tahap 0 → dikerjakan di WP-10.
- U2 diputuskan: 99,1% layak dengan start 2018 → tetap 2018 (D-006 FINAL).
- Tidak layak: cabai_rawit Aceh (missing 0,90), Sumbar (1,00), Kepri (0,90). Cabai rawit = 31 provinsi di semua analisis provinsi.
- Hilir: LP/deviasi/clustering hanya memakai seri `eligible`; normalisasi Σ_r δ = 0 untuk cabai rawit atas 31 provinsi;
  matriks clustering 34 × fitur tidak terdampak (cabai rawit bukan komoditas fokus).

### WP-05 — Penggerak mingguan & harga dunia dalam rupiah ✅
- File: `src/data/drivers.py` (`driver_weeks`, `build_national_drivers`, `build_world_prices`, `idulfitri_relative_week`);
  tes `tests/test_drivers.py`.
- Output: `world_prices_weekly` ditulis (3.096 baris = 6 komoditas × 516 minggu; NaN hanya 3 minggu Nov 2026, Pink Sheet belum rilis).
  `drivers_weekly` dihitung tetapi baru ditulis setelah WP-06 menambah kolom `episode` (`mark_episode_weeks`).
- Selesai: [x] `de` = Δ rerata log JISDOR; [x] komposit pakan 0,6/0,4; [x] `available_at` = hari kerja ke-2 bulan berikutnya;
  [x] `idf_rel_week` 11 minggu/tahun untuk 10 Idulfitri (tes); [x] komoditas tanpa padanan tidak punya baris.
- Grid penggerak mulai 2017-01-02 (`period.driver_buffer_weeks` = 52) untuk lag & jendela episode; Task 1–4 memotong ke periode.
- Fakta 2018–2026: sd(de) 0,0082; 259 minggu depresiasi / 200 apresiasi; de maks +0,063 (Mar 2020); corr(de, d_dxy) 0,52;
  5 minggu JISDOR tanpa fixing (semua cuti Lebaran) → level diteruskan (D-025).

### WP-06 — Episode depresiasi & tabel variasi kurs ✅
- File: `src/data/drivers.py::find_episodes`, `mark_episode_weeks`, `fx_variation_table` → `episodes`, `fx_variation`; kolom `episode`
  di `drivers_weekly`. Tes `test_find_episodes_*`, `test_mark_episode_weeks_and_fx_table`, `test_episodes_real_data` (`tests/test_drivers.py`).
- Selesai: [x] daftar episode sejak 2018 memuat 2018, 2020, 2022, 2024–25, 2026; [x] jumlah dicatat di SESSION_LOG 2026-11-20.
- Aturan (D-107): pemicu = Σ de 8 minggu ≥ 0,03; pemicu berjarak ≤ 8 minggu digabung; end_week = pemicu terakhir;
  cum_dlog_e = Σ jendela maksimum. Kolom ekstra: peak_week, n_trigger_weeks, in_period.
- Hasil (`episodes`): **13 episode**, 61 minggu episode: 2018 (3), 2020 (2; Mar–Mei 2020 cum 0,185), 2021, 2022, 2023, 2024 (2),
  2025, 2026 (2). Episode 13 (2026-11-02) bisa terpotong oleh freeze. `fx_variation`: 2018–2026 259 minggu depresiasi /
  200 apresiasi / 5 nol (sama dengan WP-05).
- Hilir: WP-14 memakai `in_period` dan `start_week`; plasebo dari minggu `episode = 0` (± 12 minggu).

### WP-07 — Tabel buatan tim ✅
- File: `src/data/reference.py` → `concordance`, `exposure`, `regulation`, `province_features` di `data/reference/`.
- Selesai bila:
  - [x] concordance: 10 baris, confidence diisi; seri Pink Sheet tervalidasi ada (tes sudah di `test_config`).
  - [x] exposure: `import_ratio_direct` rerata 2018–2023 dari FAOSTAT; bawang putih dari BPS/Comtrade atau ordinal (U5); setiap angka punya `source`.
  - [x] regulation: gabungan 3 sumber regulasi, tanggal tak terverifikasi ditandai `unverified` (U6).
  - [x] province_features: `dist_hub_km` dihitung dari koordinat `region_crosswalk.csv`; `rice_sufficiency` & `n_kota` diisi atau NaN + U14/U15 dicatat.
- U102 (2026-11-23, D-133): tumpang tindih Comtrade vs BPS 2023 → 14/15 kode konkordansi cocok persis (1511 0,944, nilai kecil); `stage0_report` §9.
- Data manual (2026-11-21, D-123, diisi Danen): penduduk 2025, n_kota, faktor GKG→beras → `province_features` lengkap
  (rice_sufficiency 2025 0,001..3,27; n_kota 1..12). `stage0` lokal 27 dtk.
- Input baru (2026-11-20, D-101): `hortikultura_produksi` (produksi bawang putih → rasio impor, U5), `konkordansi_hs` (jembatan Comtrade 2017–2022 → HS8 BPS), `jarak_hub` (cek silang `dist_hub_km`), BPS impor v2 (+bawang putih), regulasi revisi 20 Nov. Loader sudah ada (`src/data/loaders.py`); signature fungsi WP-07 boleh ditambah parameter oleh Ardell (pemilik `reference.py`) + `pipelines/stage0.py` disesuaikan lewat handoff.

### WP-08 — Panel 7 wilayah ✅
- File: `src/data/panel.py` → `panel_weekly_region` (indeks, bukan level Rp; D-015). Tes `tests/test_panel.py`.
- Selesai: [x] 7 wilayah × 10 komoditas × 464 minggu = 32.480 baris; [x] `n_provinces` per minggu; [x] hanya indeks log
  relatif minggu pertama (tanpa level Rp).
- Rerata wilayah tahan perubahan komposisi: dekomposisi dua arah efek provinsi + efek minggu (D-106); identik dengan rerata
  biasa bila semua provinsi teramati (median selisih 0; maks 0,10 log pada minggu komposisi berubah).
- Satu-satunya minggu kosong: 2022-05-02 (Idulfitri 2022) di 5 wilayah → `log_price_index` NaN, `n_provinces` 0 (50 sel).

### WP-09 — MDE / analisis daya (G-power) ✅
- File: `src/evaluation/power.py` (`compute_mde`, `null_se`, `asymmetry_null_se`, `gate_g_power`) → `mde`. Spesifikasi METHODS §M0.6. Tes `tests/test_power.py`.
- Selesai: [x] MDE nasional & 7 wilayah, 10 komoditas, h ∈ {4, 8, 12} (240 baris); [x] angka gerbang di D-007 (pembaruan 2026-11-20).
- SE di bawah H0 dalam bentuk skor (β̂ tidak pernah dihitung; D-107). γ(4/8/12) = 1,44 / 1,32 / 1,03.
- MDE_PT(8) nasional: bawang putih 2,52, gula pasir 0,90, **minyak goreng 0,465** → tidak ketiganya > 0,5 → **LP tetap utama**
  (D-007). **Diputuskan 2026-11-21 (D-115)** dengan config beku G6 (angka sama dengan hitungan 20 Nov).
- MDE asimetri δ = β⁻ − β⁺ (satuan PT, h = 8, nasional; kolom `mde_asym_*`): daging sapi 0,32, beras 0,44 → H2 konfirmatori;
  minyak goreng 1,01, telur 1,51, gula 1,70, daging ayam 2,66, bawang merah 4,66, bawang putih 6,15, cabai merah 7,46, cabai rawit 9,34
  → H2 deskriptif (U8 🟢).
- MDE_PT(8) terkecil: daging sapi 0,13, beras 0,20; terbesar: cabai rawit 3,75, cabai merah 3,00. Wilayah ≈ 1,5–2× nasional.

### WP-10 — QA silang & laporan Tahap 0 ✅
- File: `src/data/qa.py` → `stage0_report` (`results/stage0/stage0_report.md`). Tes `tests/test_qa.py`.
- Selesai: [x] outlier satu hari ditandai: 59 hari (cabai rawit 16, gula 9, cabai merah 8, ...), tidak dihapus (U17). Contoh Papua
  2017-07-03 ada di baris "Beras" level 1, bukan di varian Medium I yang dipakai (datar 14.400) → tidak memengaruhi analisis;
  [x] Σ BPS bulanan = total tahunan: 241/241 HS8 × tahun 2023–2026 rasio 1,000; [x] bias PIHPS vs Bapanas (9 komoditas,
  D-110): median bias_log beras +0,107 (PIHPS lebih tinggi), lainnya |bias| ≤ 0,03; median korelasi Δ bulanan 0,59 (daging sapi)
  s.d. 0,93 (bawang merah); [x] tabel cakupan 8 sumber.
- Laporan juga memuat kelayakan, episode, variasi kurs, MDE, dan keputusan G-power (LP tetap utama).

### WP-11 — Praregistrasi & pembekuan (G6) ✅
- File: `docs/PREREGISTRATION.md`, `configs/*.yaml`. Dibekukan 2026-11-20 23:29 WIB oleh Danen (D-109).
- Selesai: [x] U10 diputuskan; D-011/D-012/D-013 FINAL tanpa perubahan; [x] hipotesis, uji, ambang, k-range, B/R terisi; koreksi
  Holm H5 (`params.forecast.h5_correction`); [x] "Dibekukan pada" berisi tanggal + sha256 kedua config.
- Hilir: perubahan config setelah ini = DEVIASI PRAREGISTRASI di DECISIONS. Ulang `stage0` agar `mde` resmi dihitung di config beku
  (nilainya tidak berubah karena kunci baru tidak dipakai Tahap 0).

## Task 1 — profil respons
Pipeline `pipelines.task1` · notebook `01_task1_profiles` · berat → Kaggle/Colab.

### WP-12 — Mesin statistik bersama ✅
`stats/regression.py` (OLS CR1 cluster, Newey-West, Diebold-Mariano+HLN), `stats/resampling.py`, `stats/meta.py` (DL, REML, EB, BH). Tes `tests/test_stats.py`. Tambah fungsi baru di sini bila dipakai > 1 task.

### WP-13 — LP nasional + asimetri + PT ✅
- File: `src/models/local_projection.py` → baris `profiles` level=national, driver ∈ {e, w, e_pos, e_neg, PT}. Tes `tests/test_local_projection.py`.
- D-129 (2026-11-23, tambahan pasca-G6): `evaluation/calibration.py::national_calibrated` → artefak `national_calibrated` ditulis
  `task3` (0,9 dtk); tes `tests/test_calibration.py`. Interval ±crit·SE terkalibrasi plasebo, p = max(plasebo, normal), q BH atas 48 sel.
  Data asli: 7 sel interval tidak memuat nol (resmi `profiles`: 3); q < 0,05: daging ayam β_e(4) −1,16 (−2,10..−0,23), gula β_e(4)
  0,69 (0,25..1,13), minyak goreng ω(8) 0,21 (0,08..0,34) & ω(12) 0,31 (0,16..0,46); q < 0,1: daging ayam β_e(8) −1,67
  (−2,77..−0,58, q 0,058), minyak goreng ω(4) 0,16 (0,04..0,28, q 0,092). Gula β_e(4) TIDAK tahan Tier 1 (tanpa COVID & Brent
  ekstrem −0,03; pasca 2021-04 −0,03; `robustness`). Median `boot_ratio` 0,57 / 0,35 / 0,35 (h 4 / 8 / 12) = bukti pelemahan bootstrap.
- Fungsi: `build_design` (+ `elig`, `unit_col`, `price_col`), `regressors`, `fit_lp`, `fx_self_response`, `national_profiles`
  (+ `elig`, `horizons`, `commodities`). `task1` meneruskan `eligibility`.
- Spesifikasi: METHODS §M1.1–M1.2.
- Selesai: [x] tes sintetis β diketahui (2,5 SE, termasuk β⁺/β⁻ dan ω); [x] γ(h); [x] `n_weeks`; [x] `national_profiles`: 598 baris
  (PT/e/e_pos/e_neg 130, w 78), n_weeks 447–459; [x] runtime **23 dtk** (< 2 menit); sejak D-118 **± 6 dtk** (hasil identik). PT: se & ci NaN sampai bootstrap (WP-16).
- Hilir (WP-16, Ardell): semula 23 dtk × B 499 ≈ 3,2 jam per run bootstrap nasional; sejak D-118 ± 6 dtk × 499 ≈ 50 menit → pakai `horizons`/`commodities` dan B non-fokus 199
  sesuai aturan > 30 menit, atau paralel `joblib`.
- Catatan awal (SE cluster): daging ayam β_e(8) −1,67 (−2,62..−0,73) negatif → periksa robustness tanpa Mar–Jun 2020 (WP-28).
  Interval resmi `profiles` (bootstrap, 2026-11-22): −2,62..0,06 → memuat nol; kutip yang ini.
- H2 (D-125, 2026-11-22): `asymmetry_wald` (parametrisasi ulang de/de⁺, SE cluster minggu) + `evaluation/asymmetry.py` → artefak
  `asymmetry` ditulis `task3`; tes `tests/test_asymmetry.py`. Data asli h = 8: beras −0,14 (−0,55..0,26) p 0,49; daging sapi −0,26
  (−0,56..0,04) p 0,089 → H2 konfirmatori tidak ditolak. Deskriptif: bawang putih −5,78 (−10,2..−1,3) p 0,011 (MDE 8,1).
- D-127 (2026-11-23): interval laporan `asymmetry` = Wald ∪ persentil bootstrap (Wald di `wald_ci_*`). Beras h8 −0,58..0,47, daging
  sapi −0,88..0,21, bawang putih −10,2..3,1 → tidak ada sel H2 yang intervalnya tidak memuat nol.

### WP-14 — Event study per episode ✅
- File: `src/models/event_study.py` (`event_paths`, `placebo_starts`, `placebo_bands`) → `events` (ditulis `task1`). Tes `tests/test_event_study.py`.
- Selesai: [x] level national (panel provinsi eligible, rerata selisih per provinsi) & region (`panel_weekly_region`);
  [x] 499 jendela plasebo bersama dari minggu di luar [start−12, end+12] episode (D-110); [x] p plasebo per horizon.
- Data asli: 13 episode × 13 h × 10 komoditas = 1.690 baris nasional (0,5 dtk); 100 NaN = episode 13 terpotong freeze.
  Kandidat plasebo hanya **164 minggu unik** (499 ditarik dengan pengembalian) → resolusi p terbatas; sebut di makalah.
  Kolom ekstra `placebo_median` (2026-11-21, untuk WP-29).
  h=8: 10/120 sel p < 0,05.

### WP-15 — Deviasi provinsi & profil wilayah ✅
- Kode 2026-11-21 (Ardell) + `tests/test_deviations.py`.
- File: `src/models/deviations.py`. Selesai bila: [x] Σ_r δ = 0 per (komoditas, horizon) (tes `test_deviations`); [x] profil 7 wilayah jalan dari `panel_weekly_region` saja.
- Data asli: Task 1 P2 (Ardell, 2026-11-22), 14.066 baris provinsi + 4.186 wilayah di `profiles`; ditutup Danen 2026-11-23 (D-130).

### WP-16 — Bootstrap bersama & plasebo ✅
- Kode 2026-11-21 (Ardell, D-201; checkpoint & resume D-204) + `tests/test_inference.py`.
- File: `src/evaluation/inference.py` → `boot_replicates`, `placebo_stats`, CI bootstrap di `profiles`.
- Selesai bila: [x] satu indeks minggu per replikasi dipakai semua seri (tes `test_inference`); [x] plasebo provinsi hanya h ∈ {4, 8, 12}; [x] runtime diukur — ± 7 dtk/replikasi, B=R=499 fokus, 199 non-fokus (`bootstrap_B_nonfocus`).
- Catatan (U107, D-129): blok 13 minggu menarik β ke nol (median rasio 0,57 / 0,35 / 0,35 pada h 4/8/12) → interval resmi konservatif; tambahan `national_calibrated`.
- D-163 (2026-11-26): + baris PT di `national_calibrated` dan artefak `province_calibrated` (task3, 1.623 baris; boot_ratio provinsi median 0,51–0,67;
  sel tidak memuat nol resmi 0–2,4% vs terkalibrasi 5–12%; q global < 0,05 pada 7 deviasi). Laporan `docs/audit/20261126_kelemahan_tercatat.md` §2.

### WP-17 — Penyusutan EB & fitur respons ✅
- Kode 2026-11-21 (Ardell, D-201) + `tests/test_response.py`.
- File: `src/features/response.py` → `profiles` (shrunk=True) + `response_features`.
- Selesai bila: [x] τ² DL dan REML dilaporkan berdampingan (`heterogeneity` statistik `tau2` & `tau2_reml`, D-132); [x] τ² = 0 → semua provinsi = rerata (4 komoditas pada h 8); [x] t_half NaN bila tidak terdeteksi (75% sel).

## Task 2 — pola regional
Pipeline `pipelines.task2` · notebook `02_task2_patterns` · berat → Kaggle/Colab.

### WP-18 — Heterogenitas vs plasebo (G-het) ✅
- File: `src/evaluation/heterogeneity.py` → `heterogeneity`. Tes `tests/test_heterogeneity.py`.
- Selesai bila: [x] Q, τ², I² per komoditas (h=8, driver e, tanpa susut) + ρ̄ (kode, dites sintetis); [x] p plasebo satu sisi + q BH per
  statistik, `reject` hanya untuk Q (H0-Het); [x] jalan pada P2 asli (`task2` lokal 2026-11-22, 14 dtk untuk bagian ini);
  [x] keputusan G-het di DECISIONS (D-125, bagian G-het).
- Hasil (h = 8, driver e): Q ditolak (q BH ≤ 0,05) untuk telur ayam (Q 161,7 vs p95 null 88,7; p 0,004; q 0,040; I² 0,80) dan
  daging ayam (Q 132,6 vs 77,5; p 0,010; q 0,050, tepat di ambang; I² 0,75). Gula pasir p 0,020, q 0,067 (tidak). Lima komoditas
  τ² = 0 (bawang putih, cabai rawit, daging sapi, minyak goreng) sehingga EB menyusutkan semua provinsi ke rerata. ρ̄ 0,094, p 0,20.
- Syarat input (D-111): baris provinsi di `profiles` **dan** `placebo_stats` wajib membawa `se` (SE cluster minggu) → permintaan ke
  Ardell (WP-16), handoff `docs/handoff/20261121-1200_danen-ke-ardell_se-plasebo-tier1.md`.

### WP-19 — Clustering & pemilihan k ✅
- Kode 2026-11-21 (Ardell, D-202) + `tests/test_clustering.py`, `tests/test_task2.py` (task2 end-to-end sintetis).
- File: `src/features/clustering.py`, `src/models/clustering.py` → `cluster_selection`.
- Selesai bila: [x] fitur = R & W h∈{4,8,12} komoditas fokus, tersusut, terstandardisasi; [x] k=1 dilaporkan bila silhouette maks ≤ p95 plasebo (data asli 0,184 < 0,196 → k = 1).

### WP-20 — Stabilitas & pembanding partisi ✅
- Kode 2026-11-21 (Ardell, D-202).
- File: `src/evaluation/stability.py` → `clusters`, `coassign`, `partition_compare`. Selesai bila: [x] ARI Ward vs K-Means; [x] Jaccard per klaster, weak bila < 0,6; [x] ARI vs zona HET, Jawa/luar Jawa, n_kota (k = 1 → NaN "tidak berlaku", D-132).

### WP-21 — Uji struktur tertanam ✅
- File: `src/evaluation/planted.py` → `planted_recovery`. Tes `tests/test_planted.py`. Konvensi D-112, D-126.
- Selesai bila: [x] kurva recovery untuk δ ∈ {0,1..0,5}, k_true ∈ {2,3} (kode, sintetis sejak D-126: derau sd 0,2 dengan SE sesuai
  × 12 fitur → recovery 0 pada δ ≤ 0,3, ≥ 0,9 pada δ 0,5); [x] `detection_limit`; [x] dijalankan pada matriks plasebo asli (`task2` 2026-11-22), tetapi
  recovery 1,0 pada semua δ (0,1..0,5): matriks plasebo 'mentah' sudah tersusut EB (42% kolom konstan per replikasi, median sd
  0,005), jadi δ ditanam setelah penyusutan dan batas deteksi terlalu optimistis (U105); [x] diperbaiki (D-126): tanam pada deviasi
  plasebo mentah (`deviation_matrices`), lalu `shrink_matrix` (identik dengan matriks fitur, selisih 0,0) & z-score; ambang 0,196 = select_k;
  53 dtk lokal; [x] batas deteksi δ = 0,2 untuk k = 2 dan 3 (recovery 0,995 / 0,965; δ 0,1: 0,43 / 0,13) → untuk findings.
- Tafsir: δ = selisih RMS per fitur dalam satuan respons, sama untuk semua fitur, sehingga deteksi didorong fitur yang presisi (W dan
  R gula/daging sapi/minyak goreng, median SE deviasi 0,03–0,16) dan bukan fitur cabai/bawang (SE 0,4–1,2). Tulis: "struktur dengan
  selisih respons rata-rata ≥ 0,2 akan terdeteksi" + catatan ini.
- Penanaman: pusat kelompok = simpleks berorientasi acak; setiap pasangan kelompok berselisih δ (RMS per fitur). Versi awal (geser
  j·δ di semua fitur) membuat 3 kelompok segaris sehingga k = 3 tidak pernah terpilih meski ARI 0,96 → ditolak (D-112).

## Task 3 — asosiasi
Pipeline `pipelines.task3` · notebook `03_task3_association` · ringan.

### WP-22 — Asosiasi level komoditas (Kendall) ✅
- File: `src/models/association.py::kendall_exact` (+ `all_permutations`, `kendall_permutation_test`) → `assoc` level=commodity.
  Tes `tests/test_heterogeneity.py` (dicocokkan dengan brute force 6!).
- Selesai bila: [x] p permutasi eksak (10! = 3.628.800 permutasi int8, ± 5 dtk); [x] leave-one-commodity-out (jackknife_min/max, interval
  τ ± 1,96·SE jackknife); [x] jalan pada P2 (`response_features`) + P3 (`exposure`) asli (`task3` 2026-11-22): τ-b −0,045
  (jackknife −0,65..0,56), p eksak 0,93, sama dengan versi sementara.
- Sementara (2026-11-21, `exposure` asli dari `stage0` + PT(8) titik dari `national_profiles` lokal, sebelum `response_features`):
  τ-b = −0,045 (jackknife −0,65..0,56), p eksak dua sisi 0,93, p satu sisi 0,60, n = 10 → tidak ada asosiasi terdeteksi di antara
  10 komoditas. Rasio impor beras dikoreksi ke beras giling (D-120, DEVIASI PRAREGISTRASI); dengan item lama τ = −0,13.
- E2 eksploratif (D-124, 2026-11-21): `src/evaluation/regimes.py` → artefak `regime_profiles` (ditulis `task3`), tes
  `tests/test_regimes.py`. Data asli lokal: 10 komoditas, 3–6 rezim, 145 baris, 4,9 dtk; estimasi sampel penuh di dalam interval
  rezim pada 73% sel. Contoh berbeda: bawang putih rezim Perbadan 12/2024 β_e(8) 3,74 (2,40..5,09) vs penuh −0,68.
- D-127 (2026-11-23): ±1,96·SE terlalu sempit di rezim pendek (39% sel 52–104 minggu "signifikan"). Interval kini ±crit·SE, crit =
  max(1,96; p95 |t*|) dari 499 plasebo geser-melingkar (median 3,09), + `p_placebo`, `q_fdr`. Sel tidak memuat nol 38 → 15 dari 145;
  q BH minimum 0,145 (tidak ada yang lolos). Terkuat: bawang putih Perbadan 12/2024 β_e(8) 3,74 (1,83..5,65), p plasebo 0,002;
  telur & daging ayam ω(4..12) rezim Perbadan 5/2022 negatif (p plasebo 0,002–0,010). Estimasi penuh di dalam interval rezim 88%.
  `task3` lokal 562 dtk (E2 plasebo ± 9 menit, joblib 12 core).

### WP-23 — Meta-regresi provinsi ✅
- Kode 2026-11-21 (Ardell, D-203) + `tests/test_association.py`.
- File: `src/models/association.py::meta_regression` → `assoc` level=province. Selesai bila: [x] ≤ 3 fitur praregistrasi; [x] interval bootstrap vs CR2, yang lebih lebar dilaporkan; [x] jackknife provinsi.
- U106 (D-132, 2026-11-23): p = max(p CR2, p bootstrap sisi) konsisten dengan interval; `q_fdr` BH. Data asli: 0/88 baris dua sisi p < 0,05 (sebelumnya 11), q min 1,0; H3 gabungan 0,007 (−0,022..0,033), p satu sisi 0,80.

### WP-24 — Robustness FE komoditas×minggu (3c) ✅
- Kode 2026-11-21 (Ardell, D-203).
- File: `src/models/association.py::fe_interaction`. Dapat dipotong (D-014). Data asli: 9 koefisien (3 fitur × h 4/8/12), semua interval memuat nol.

## Task 4 — evaluasi prediktif
Pipeline `pipelines.task4` · notebook `04_task4_forecast` · berat → Kaggle/Colab; paralel dengan Task 1.

### WP-25 — Fitur Task 4 + as-of join ✅
- Kode 2026-11-20 (Ardell): `origins`, `feature_table`, `split_origin`, `build_features`; `tests/test_forecast.py` (tes kebocoran termasuk mengacak data masa depan).
- File: `src/features/forecast.py`. Selesai bila: [x] tes kebocoran: untuk origin acak, tidak ada fitur dengan `available_at` > origin dan tidak ada target dengan t+h > origin di train.

- D-162 (2026-11-26, U108): fitur `episode` = `data.drivers.realtime_episode_flag` (minggu pemicu s.d. t), bukan flag periode penuh;
  6/61 minggu berubah. Tes `test_drivers` (setara deteksi ulang s.d. t) & `test_forecast` (de sesudah t0 tidak mengubah fitur).
### WP-26 — Model M0–M3 rolling-origin ✅
- Kode 2026-11-20 (Ardell); M0–M3 ± 2 dtk/origin untuk M3 pada data asli.
- File: `src/models/forecasting.py` → `data/interim/forecast_preds.parquet`. Selesai bila: [x] origin tiap 4 minggu dari 2021-01-04 (76 origin h 4, 75 h 8); [x] M3 dapat dimatikan via flag bila waktu habis (`forecast.run_m3`).
- D-131 (2026-11-23): diagnostik dummy bulan + Idulfitri (bukan artefak): M2/M1 1,005 / 1,019, H5 Holm 0,56 → kesimpulan sama; M0/M1 0,95 / 0,97.

### WP-27 — Evaluasi DM & ablation ✅
- File: `src/evaluation/forecast_eval.py` (+ `n_nonoverlap`; `stats.meta.holm`) → `forecast_eval`, `ablation`. Tes `tests/test_forecast_eval.py`. D-113.
- Selesai bila: [x] rasio MAE/RMSE vs M1 untuk semua & large_move (per komoditas, wilayah, jalur H5, ALL); [x] DM HAC pada selisih MAE per
  origin; [x] n_origins & n_nonoverlap di setiap baris; [x] H5 (M2, h = 8, large_move, jalur direct_import {bawang putih, gula, daging sapi}
  & imported_input {daging ayam, telur}, DM satu sisi, Holm keluarga 2) — kode, sintetis; [x] jalan pada `forecast_preds` asli (P4, 2026-11-23).
- Data asli (Ardell, Drive 2026-11-22; `evaluate` lokal identik, selisih ≤ 4e-16, 2,4 dtk): 76 origin (h 8: 75, 38 tidak tumpang tindih)
  × 337 seri provinsi × M0..M3 + `M2_nofx`. Rasio MAE M2/M1 semua origin 1,014 (h 4, DM p 0,001) dan 1,017 (h 8, p 0,006) → fitur
  kurs sedikit MEMPERBURUK; M3/M1 1,044 / 1,015. M0 (nol) hampir setara M1 (1,017 / 1,016). Per komoditas M2/M1 h 8: daging sapi
  1,30, gula 1,13, beras 1,11; cabai/bawang merah/minyak goreng ≈ 1. `large_move` hanya 8 origin (p80 |Δe 4 mgg| latih memuat 2020).
  **H5 tidak didukung:** M2/M1 h 8 large_move direct_import 1,12 (p satu sisi 0,95), imported_input 1,12 (0,88), Holm 1,0.
- `M2_nofx` = M2 tanpa kelompok fx = fitur M1 → prediksi identik M1; ablation = −(M2 − M1), bukan informasi tambahan.
- Diagnostik ad hoc (2026-11-23, bukan artefak): M1/M2 ridge gabungan 10 komoditas tanpa identitas komoditas (sesuai proposal).
  Ridge per komoditas: M2/M1 1,011 / 1,018, H5 1,18 / 1,12 (Holm 1,0) → kesimpulan tahan terhadap pooling (D-128).
- Kontrak masukan untuk WP-26 (handoff `docs/handoff/20261121-1300_danen-ke-ardell_kontrak-forecast-preds.md`): kolom origin, horizon, model,
  province_id|region, commodity, y_true, y_pred, large_move; model ablation bernama `M2_nofx`.

## Robustness & validasi
Pipeline `pipelines.robustness` · notebook `05_robustness` · sedang–berat → Kaggle/Colab.

- D-162 (2026-11-26): dijalankan ulang lokal dengan flag episode real-time (task4 2.029 dtk): M2/M1 1,0086 (DM p 0,009) / 1,0125 (p 0,025),
  M3/M1 1,037 / 1,014, H5 1,112 / 1,115 (Holm 1,0); M0/M1/M2_nofx identik → kesimpulan sama. Laporan `docs/audit/20261126_kelemahan_tercatat.md` §1.
### WP-28 — Robustness Tier 1
- File: `src/evaluation/robustness.py::tier1` (+ `fx_decomposition`). Tes `tests/test_robustness.py`. Konvensi teknis D-111.
- Selesai: [x] 6 cek `TIER1` pada h 4/8/12, driver e & w, interval ±1,96·SE cluster; [x] data asli: 382 baris, **21 dtk lokal**.
  Artefak `robustness` ditulis `pipelines.robustness` bersama validasi (WP-29, butuh `forecast_eval`).
- Data asli: d_dxy menjelaskan 27% varians de (b = 0,72). Bulan Brent ekstrem (|Δlog| > 0,25): Mar–Jun 2020, **Mar 2026 (+0,40)**,
  Nov 2026 (bulan parsial). Baseline di dalam interval cek pada 86–100% sel; tidak ada pembalikan tanda yang intervalnya mengecualikan nol.
- Daging ayam β_e(8): baseline −1,67 → tanpa COVID & Brent ekstrem −0,96 (−2,05..0,14); komponen spesifik rupiah −1,89 (−3,02..−0,76);
  pra-2021-04 −1,71, pasca −0,97 (−2,31..0,37); bulanan −0,60 (−1,33..0,13). Negatif tidak hanya karena Mar 2020, tetapi melemah dan
  intervalnya memuat nol tanpa COVID → laporkan apa adanya (asosiasional), bukan sebagai kausal.

### WP-29 — Validasi V2 & V4 ✅
- File: `src/evaluation/robustness.py::validation` (+ `lp_implied_paths`); subset `case_study` di `forecast_eval`; kolom `placebo_median`
  di `events`. Tes `tests/test_robustness.py`. D-114.
- Selesai bila: [x] V4 pada data asli (60 baris validasi, 21 dtk termasuk LP & event study); [x] V2 episode 2026 pada data asli;
  [x] V2 forecast (rasio MAE origin 2026) pada `forecast_eval` asli (P4); [x] artefak `robustness` ditulis `pipelines.robustness` (2026-11-23,
  486 baris: Tier 1 382, validasi 104; 11 dtk lokal). V2 forecast: M2/M1 origin 2026 1,005 (h 4, 10 origin) dan 1,005 (h 8, 9 origin,
  5 tidak tumpang tindih) vs semua origin 1,014 / 1,017; M3/M1 1,045 / 1,017. V4 ulang: 26/30 sel sama.
- Data asli V4 (12 episode lengkap, h 4/8/12): implikasi LP berada di dalam interval rerata kelebihan event pada 26/30 sel (17/18 fokus);
  di luar: bawang putih h4 (tipis), bawang merah h4, cabai merah h4, cabai rawit h12 (kontrol domestik, kelebihan event besar). Kesesuaian
  tanda per episode ± 0,5, korelasi median 0,16 → arah antar-episode tidak konsisten; besaran LP kecil (|·| ≤ 0,04).
  V2 episode 12 (mulai 2026-05-18): 0/30 sel di luar pita plasebo. Episode 13 (2026-11-02) terpotong freeze.
- Versi awal memakai titik tengah pita 2,5–97,5 sebagai pusat null → kelebihan minyak goreng −0,09 dan bawang putih −0,17 (artefak ekor
  null yang miring, mis. lonjakan minyak goreng 2021–22) → diganti median plasebo (D-114).

### WP-30 — Robustness Tier 2 ✅
- File: `src/evaluation/robustness.py::tier2`; input dari `data/panel.py` (`build_variant_panels`, `last_observation_panel`,
  `build_bapanas_panel`), `data/drivers.py::build_world_variants`, `pipelines/robustness.py::tier2_inputs`. Opsional; pertama dipotong.
  Tes `tests/test_robustness.py`, `tests/test_drivers.py`. D-116. CLI `python -m kagami robustness --tier2`.
- Selesai: [x] varian alternatif (11 varian PIHPS + 3 komposit pakan × 2 komoditas); [x] agregasi observasi terakhir; [x] Kendall
  ordinal jalur; [x] outcome Bapanas bulanan; [x] data asli: 187 baris, ±40 dtk lokal (termasuk menyiapkan input dari mentah);
  [x] keterpencilan alternatif (meta-regresi gabungan: km hub linear, ln km Jakarta; 6/6 konsisten dengan baseline); [x] baseline τ dengan `import_ratio_direct` (−0,045).
- Ditulis ke artefak `robustness` 2026-11-23 (`robustness --tier2`, 203 dtk lokal): 679 baris (Tier 2 193; baseline di dalam interval 191/193).
- Data asli (β_e/ω nasional, h 4/8/12): baseline di dalam interval cek pada **184/186 sel**. Dua pengecualian, tanda sama:
  gula Kualitas Premium β_e(4) 0,36 (0,15..0,57) vs Lokal 0,69; Minyak Goreng Curah ω(8) 0,36 (0,26..0,45) vs Kemasan 0,21
  (Curah lebih peka terhadap harga sawit dunia, sesuai dugaan D-023). Daging ayam β_e(8) stabil: komposit jagung −1,79,
  bungkil kedelai −1,64, bobot sama −1,64, observasi terakhir −1,57 (baseline −1,67). Bapanas bulanan 2022–2026 mengikuti PIHPS bulanan
  pada bulan yang sama (42/42 sel). Kendall τ-b PT(8) vs ordinal jalur = −0,03 (−0,75..0,70), p eksak 1,00 → di antara 10 komoditas
  tidak ada asosiasi monoton jalur eksposur dengan PT(8) (deskriptif, E1).

## Produk & submission

### WP-31 — Halaman Streamlit final ✅
- 2026-11-21 (Ardell): halaman 2–4 dan Home diperluas; `tests/test_app_data.py` merender semua halaman dengan artefak sintetis.
- 2026-11-27 (Danen, D-170): app sebagai deliverable produksi untuk juri: router `st.navigation` (Hasil penelitian / Lampiran teknis),
  beranda jawaban-dulu `pages/1_Beranda.py`, lampiran `pages/8_Data_dan_Metode.py`, label terbaca, temuan dalam tab, tema terang serif;
  perbaikan lineage beda ujung baris (21 artefak "tidak sinkron" palsu di app daring).
- 2026-11-27 (Danen, D-171): teks & UX untuk juri dan TPID: jawaban dulu di setiap halaman hasil, kosakata pembaca (% per 1% pelemahan
  rupiah, Rupiah per kg dari harga acuan findings), kode internal & notasi ke lampiran/expander, Daftar istilah; Respons harga 3 pemilih +
  tab; Eksposur dipecah jadi Faktor penjelas + Prediksi (`pages/9_Prediksi.py`); Temuan lengkap → Lampiran "Laporan lengkap".
- 2026-11-28 (Danen, D-172): teks dari berkas (findings.md, laporan Tahap 0, interpretasi log) ditampilkan tanpa kode internal &
  titik koma prosa (`common.readable`; berkas tidak diubah); "Status" → "Kesimpulan"/catatan; angka tabel format Indonesia
  (`show_table`); 3 tumpang tindih grafik desktop + judul terpotong di ponsel diperbaiki (0 di 1280/1024/375 px); bug "h = 5 minggu".
- 2026-11-28 (Danen, D-173): rumus dirender LaTeX (Simulasi, Data & metode, Laporan lengkap 53 rumus); Data & metode ditulis ulang
  (langkah pengolahan, rumus model, pemeriksaan kualitas data menggantikan laporan pipeline mentah); Laporan lengkap dengan panduan
  membaca; Riwayat eksekusi hanya untuk pengembang (`KAGAMI_DEV=1`).
- 2026-11-28 (Danen, D-174): `results/findings.md` ditulis ulang tanpa pola tulisan AI (label tebal, deret angka dalam kurung, titik
  koma, kode); angka diverifikasi sama dengan versi lama; tab app hal. 6 memetakan "Pertanyaan" dan "Ketahanan".
- 2026-11-28 (Danen, D-175): halaman Rupiah dari waktu ke waktu (`pages/10_Lini_Masa_Rupiah.py`) dan Profil provinsi
  (`pages/11_Profil_Provinsi.py`); kipas episode di tab Respons harga; viz `episode_fan`, `episode_fan_grid`, `price_trend`.
- 2026-11-28 (Danen, D-180): audit kata ambigu di teks app; istilah tunggal "kebetulan", "rupiah melemah", "paling banyak";
  penjaga istilah di `test_app_data`.
- 2026-11-28 (Danen, D-179): lima jawaban beranda dibuka dengan hal yang bisa dipakai (batas Rupiah, angka nasional yang berlaku,
  pegangan); hasil nol sebagai batas, bukan vonis "tidak terbukti".
- 2026-11-28 (Danen, D-178): halaman Cerita data (`pages/12_Cerita_Data.py`): peta petak heksagon harga vs respons kurs per komoditas,
  peta kecil 10 komoditas (8 abu-abu, H0-Het tidak ditolak), matriks episode × komoditas; peta heksagon di beranda; viz
  `hex_tile_map`, `hex_tile_grid`, `episode_matrix`; tabel tim `data/reference/province_hex.csv`.
- File: `app/`. Selesai bila: [x] 6 halaman menampilkan artefak nyata; [x] setiap grafik: sumber, satuan, periode, interval, label "asosiasi, bukan kausalitas"; [x] lencana "tidak terdeteksi"; [x] halaman 3 menangani k=1; [x] halaman 5 bendera ekstrapolasi; [x] tanpa login/input data/estimasi runtime.
- 2026-11-23 (Danen, D-130): hal. 2 + `national_calibrated` & H2 `asymmetry`; hal. 4 Kendall sebagai metrik, forest meta-regresi per horizon (bukan campuran skala), E2 `regime_profiles`; hal. 5 status & catatan interval PT; hal. 6 ringkasan robustness; `with_status` (lencana + 3 desimal) dan `STRETCH` (lebar penuh lintas versi Streamlit; `use_container_width` usang). Tes `test_app_data` memuat artefak sintetis baru.
- 2026-11-23 (Danen, D-134, PLAN.md §18): `viz/style.py` (palet tervalidasi, label bahasa pengguna, format angka Indonesia); hal. 2
  peta 7 wilayah / 34 provinsi offline (klik → IRF), default IDR/USD, ringkasan h 4/8/12 + MDE, forest pembanding, pilihan di URL +
  atur ulang, tabel ke expander; hal. 3 angka utama + silhouette vs ambang + batas deteksi; hal. 4 dot plot rasio MAE; hal. 5 jalur
  skenario. Perbaikan: lencana NaN ("terdeteksi" → "interval tidak tersedia"), provinsi satu versi (tersusut EB) & berlabel deviasi.
  P1: V19 asimetri β⁺ vs β⁻ (hal. 2), V18 forest robustness Tier 1/2 vs estimasi utama (hal. 6).
- 2026-11-24 (Danen, D-135): app live https://kagami.streamlit.app kosong di 6 halaman karena `results/*` di-gitignore → 23 artefak
  yang dibaca app (± 1,4 MB, `ship=True`) dibuka di `.gitignore`; hal. 6 menampilkan `findings.md` tanpa menunggu `robustness`.
  Salinan bersih berisi hanya file yang di-track git: 6/6 halaman AppTest tanpa "Menunggu hasil". App live baru terisi setelah di-push.
- 2026-11-24 (Danen, D-136): setelah push app daring masih "Menunggu hasil" karena `common.load` meng-cache `None` dari sebelum artefak
  ada → ketiadaan tidak lagi di-cache, kunci cache memuat mtime & ukuran file; tes regresi di `test_app_data`.

### WP-32 — Paket juri & uji jalan ulang (G7) ✅
- 2026-11-21 (Ardell): `tests/test_package.py` membuktikan isi zip, tidak ada data tanpa hak redistribusi, dan CLI jalan dari folder ekstrak baru.
- File: `src/pipelines/package.py`. Selesai bila: [x] `python -m kagami package` tanpa `--allow-missing`; [x] ekstrak zip di folder baru → `pip install -e .` → `python -m kagami app` jalan (Tingkat A) dan `task4` jalan dari data kirim (Tingkat B); [x] tidak ada file `redistribute: false` di zip (cek daftar isi).
- G7 2026-11-23 (Danen): `dist/kagami_submission.zip` 172 file, 44 MB, tanpa artefak hilang; mentah hanya sumber `redistribute: true` (10 file), tanpa `pihps_daily`. Diekstrak ke folder bersih → venv `--system-site-packages` → `pip install --no-deps -e .`; Tingkat A: 6/6 halaman AppTest; Tingkat B: `task4` 1.128 dtk, `forecast_eval` identik dengan versi resmi (600/600 baris, selisih MAE maks 1e-16).
- G7 ulang 2026-11-24 (Danen, D-135): zip 23 Nov dibuat sebelum desain ulang app (D-134) dan tidak memuat `viz/style.py`, geojson,
  `requirements.txt`. `bundle` (77 file) dan `package` (178 file, 47,6 MB, tanpa artefak hilang) dibangun ulang; zip diekstrak ke folder
  bersih → Tingkat A 6/6 halaman AppTest tanpa exception dan tanpa "Menunggu hasil". Tingkat B tidak diulang (kode analisis tidak berubah).
- G7 ulang 2026-11-24 03.31 (Danen, WP-36): `package` 212 file, 44,6 MB, tanpa artefak hilang (+ `src/tracking/`, app hal. 7, `logs/`
  23 file, docs/TRACKING.md); tanpa `pihps_daily` & PIHPS mentah. Diekstrak ke folder bersih → `tests/test_app.py` 7/7, ketujuh halaman
  tanpa exception & tanpa "Menunggu hasil"; hal. 7 membaca 11 run. `bundle` 85 file.
- Gladi G7 2026-11-26 (Danen, persiapan pembekuan): `package` 300 file, 47,0 MB (60,6 MB terurai), tanpa artefak hilang; mentah hanya 10 sumber
  `redistribute: true` (termasuk NASA POWER); `bundle` 89 file. Diekstrak ke folder bersih dan paket didaftarkan dari `src/` zip (bukan instalasi
  proyek): 7/7 halaman tanpa exception & tanpa "Menunggu hasil", `test_app` + `test_package` + `test_calibration` 19 lolos. Tingkat B tidak diulang
  (task3, task4, robustness baru saja dijalankan ulang dari data turunan yang sama, D-162/D-163).
- Gladi G7 2026-11-28 (Danen, D-176/D-177): `package` 387 file, 48,4 MB, tanpa artefak hilang (+ 62 laporan `docs/audit/**/*.md`, skrip & hasil
  red flag, `docs/paper/`); `bundle` 89 file. Diekstrak ke folder bersih, `kagami` dari `src/` zip: 11/11 halaman tanpa exception & tanpa
  "Menunggu hasil"; `test_app` + `test_app_data` + `test_package` + `test_paper` + `test_wiring` + `test_calibration` 57 lolos, 1 dilewati
  (cek git-ignore, tanpa repo). Tingkat B tidak diulang (kode analisis tidak berubah sejak gladi 26 Nov).

### WP-33 — Temuan & makalah ✅
- 2026-11-23 (D-130): `results/findings.md` ditulis dari artefak (RQ1–RQ5, E2, robustness, keterbatasan, daftar artefak sumber). Makalah PDF ditunda.
- 2026-11-24: `findings.md` + Ringkasan butir 6, bagian "Eksplorasi Task 4" (arah perubahan D-139/D-140, klasifier D-141, model deep &
  TimesFM 3.0 D-142) dan keterbatasan model eksploratif (risiko kontaminasi pralatih TimesFM, lisensi). Versi di Drive tim basi.
- 2026-11-28 (D-177): makalah `docs/paper/kagami_makalah.tex` → `kagami_makalah.pdf` (21 halaman, pdflatex, 8 gambar, 12 tabel,
  55 rujukan terverifikasi). Gambar dari artefak (`docs/paper/scripts/make_figures.py`) dan dari app (`scripts/capture_app.py`);
  angka dari artefak resmi lewat `findings.md` dan analisis red flag (D-168). Naskah video `docs/paper/NASKAH_VIDEO.md`.
  Penjaga `tests/test_paper.py`. Nama anggota diambil dari tabel anggota README. Sisa `[HUMAN]` (WP-35): konfirmasi afiliasi, baca ulang tim, rekam video, unggah.
- Output: `results/findings.md` (dibaca app hal. 6) + makalah PDF sesuai struktur juknis: judul, abstrak, pendahuluan (latar belakang, tujuan & manfaat, batasan), kajian pustaka, solusi usulan (deskripsi, dataset, metode, perbedaan dengan solusi sebelumnya, matriks evaluasi), hasil eksperimen & pengujian, analisis, kesimpulan & saran, daftar pustaka.
- Selesai bila: [x] setiap angka di makalah berasal dari artefak (nama artefak di keterangan tabel/gambar; angka utama dites sama
  dengan `findings.md` dan PDF); [x] rujukan "belum diverifikasi" (U12) dicek atau dihapus (`docs/paper/RUJUKAN.md`).

### WP-34 — Audit klaim (G8) ✅
- 2026-11-23: findings.md, teks app, dan README dipindai terhadap tabel §20 (frasa kausal/prediktif, "pertama", "rentan", "dataset kami", "tervalidasi"); satu pertanyaan halaman 4 dirumuskan ulang. Makalah menunggu.
- 2026-11-27 (D-169, review eksternal): arah DM di app hal. 4, rumus skenario app = findings (eksak), carry_forward = rangkaian harga identik, batas Rupiah asimetris, batas deteksi & proksi dibatasi, waktu origin, rasio biaya K4 = analisis kepekaan, status prototipe riset; tabel §20 + 5 baris (PROJECT_OVERVIEW §6). Sisa: makalah, bibliografi (U12).
- 2026-11-28 (D-177): makalah ditulis mengikuti tabel §20 dan diaudit: frasa terlarang dites otomatis (`tests/test_paper.py`), p DM
  selalu dengan statistik & p satu sisi, hasil nol sebagai batas atas, interval tidak simetris ditulis bawah..atas, kajian pustaka
  "tematik, bukan tinjauan sistematis". Klaim Persada dkk. (2026) dikoreksi dari teks lengkap (bukan bukti penerusan kurs).
- Selesai bila: [x] setiap kalimat temuan di findings.md, makalah, app lolos tabel "Jangan tulis/Tulis" (PROJECT_OVERVIEW §6); [x] setiap angka punya interval; [x] hasil nol ditulis sebagai batas atas.

### WP-35 — Tugas manusia `[HUMAN]`
- [x] **Abi** · Izin BI (U13) — sudah diperoleh (dikonfirmasi Danen 2026-11-20).
- [ ] **Abi** · Konfirmasi jalur unduh PIHPS resmi (U19); bila bukan, laporkan agar Danen mengunduh ulang via fitur resmi.
- [ ] **Abi** · Data manual (PEMBAGIAN_TUGAS §6.2): populasi, n_kota, GKG→beras, verifikasi regulasi, pemetaan Bapanas; PADG 7/2026 (U3).
- [ ] **Danen** · Prasyarat kolaborasi (PEMBAGIAN_TUGAS §8): repo GitHub privat + .gitignore, folder Drive tim (bagikan terbatas + `python -m kagami drive-push-raw`; D-100, D-101), dataset Kaggle
      `kagami-code` (**PRIVAT**, `python -m kagami bundle`; `kagami-raw` opsional), bagikan ke Ardell. Ulangi bundle setiap `src/` berubah.
- [ ] **Danen** · Taruh CSV penduduk 2025 & snapshot kab/kota Panel Harga di lokasi DATASETS.md §Menunggu diunggah (U103).
- [ ] **Danen & Ardell** · Token Drive masing-masing (`drive-auth`) + Kaggle Secret `KAGAMI_DRIVE_TOKEN` (`docs/NOTEBOOKS.md` §Persiapan 2).
- [ ] **Danen/Abi** · Wawancara validasi kebutuhan TPID (U109) dengan `docs/PANDUAN_WAWANCARA_TPID.md`; hasil → catatan `docs/audit/` + D-xxx.
- [ ] **Abi** · Pastikan jendela revisi harga harian PIHPS untuk `available_at` (U110).
- [ ] **Danen** · Konfirmasi nama anggota & afiliasi di blok judul `docs/paper/kagami_makalah.tex`, baca ulang makalah bersama
      tim, kompilasi ulang (`docs/paper/README.md`), putuskan pernyataan bantuan AI (D-177).
- [ ] **Danen** · Commit + push perubahan D-170–D-177 (termasuk `data/processed/drivers_weekly.parquet` & `panel_weekly.parquet`,
      D-176) agar app daring menampilkan halaman Rupiah dari waktu ke waktu & Profil provinsi.
- [ ] **Abi** · Rekam video demonstrasi dengan naskah `docs/paper/NASKAH_VIDEO.md` (± 6–7 menit).
- [ ] **Abi** · Unggah makalah PDF + zip + video ke Google Drive dan form pendaftaran Gelombang 2.

### WP-36 — Log eksekusi & evaluasi terpusat ✅
- 2026-11-24 (Danen, D-137): `src/tracking/` (schemas, metrics berpenjaga, lineage sha256, evaluators per tahap, registry +
  graf dependensi dari REQUIRES, store JSON, logger `@tracked`) dipasang di keenam `pipelines.<tahap>.run`; CLI `evaluate`, `runs`,
  `all` (satu pipeline_id); log ikut `drive.push`/`pull`; app halaman 7 *Evaluasi & Riwayat Eksekusi*; `tests/test_tracking.py`.
  Hasil analisis, `params.yaml`, dan artefak tidak berubah. Matriks tahap × metrik & skema: [TRACKING.md](TRACKING.md).
- Run nyata 2026-11-24 (lokal, satu pipeline_id, out_dir sementara agar `results/` tidak tersentuh): stage0 41,5 dtk, task3 765 dtk,
  robustness (Tier 1 + validasi) 14,6 dtk, task2 120 dtk; semua sukses, run induk benar (task3 ← stage0 + task1, task2 ← task1).
  Cek reproduksi sha256 vs artefak resmi: task2 6/6 & task3 4/4 identik; stage0 14/15 (checksums beda hanya `recorded_at`);
  robustness 486/486 baris Tier 1 + V identik (versi resmi juga memuat Tier 2). Task 1 & 4 (Kaggle/Colab) lewat `evaluate all`.
  Cek integritas: silhouette dihitung ulang = `cluster_selection` (selisih 0), MAE dari `forecast_preds` = `forecast_eval`
  (selisih 8e-17), konsistensi p–interval `national_calibrated` 48/48, meta-regresi 99/99; H2 26/30 (diharapkan, D-127).
- Run end-to-end penuh 2026-11-24 (lokal, `python -m kagami all` + `robustness --tier2`, folder kode bersih dari `kagami_code.zip`,
  out_dir sementara → tidak bisa melanjutkan dari bootstrap/prediksi resmi): run 1 `task1` gagal setelah 5.312 dtk (bootstrap 499 +
  plasebo 499 selesai) di `print` τ² → D-138; run 2 lanjut dari checkpoint: stage0 17,6 dtk, task1 19,4 dtk, task2 93,8 dtk, task3
  524 dtk, task4 431 dtk (M0–M3, 2 h × 76/75 origin), robustness 10,1 dtk (+ Tier 2 53,4 dtk); semua sukses, 0 metrik gagal.
  Reproduksi 35 artefak: 17 identik sha256, 16 sama isi dengan selisih numerik ≤ 3,5e-11 (Task 1 resmi dari Kaggle), checksums
  beda hanya `recorded_at`, findings = laporan manual. Angka kunci sama: MDE 2,52/0,90/0,465, plasebo |t| > 1,96 8,1%, boot_ratio
  0,57/0,35/0,35, H0-Het 2, k = 1, Kendall −0,045 (p 0,93), M2/M1 1,014/1,017 (DM p 0,001/0,006), H5 tidak ditolak. App 7/7
  halaman pada hasil baru; halaman 7 crash saat log lama (detik) bercampur log baru (mikrodetik) → diperbaiki (D-138). Log run ini
  tidak dimasukkan ke `logs/` project: input hash-nya file e2e, jadi artefak resmi akan tampak "basi".
- Diagnostik arah Task 4 (D-139, 2026-11-24): `direction_metrics` + confusion matrix app hal. 7; artefak resmi: akurasi arah 0,543 / 0,557 / 0,573 (M1 / M2 / M3, h 4) dan 0,560 / 0,560 / 0,602 (h 8) vs baseline kelas mayoritas 0,527 / 0,545; F1 makro 0,538 / 0,550 / 0,566 dan 0,551 / 0,549 / 0,594; MCC 0,08–0,19; ROC-AUC 0,567–0,627.
  Log evaluasi-saja baru `task4` ditulis ke `logs/`.
- Audit & perbaikan halaman 7 (D-140, 2026-11-24): penilaian dua lapis, interval bootstrap blok origin metrik arah, tabel per
  segmen, sinkron artefak & status tahap, code hash/dirty, wiring OPTIONAL task2 & robustness + tes; `evaluate all` ulang (7 log
  evaluasi-saja baru). Temuan utama di D-140; laporan audit `docs/audit/20261124_audit_evaluasi_eksekusi.md`.
- Kelengkapan & kestabilan evaluasi (D-144, 2026-11-24): F1 makro h 8 (pada baris berubah, cakupan 0,907): TimesFM 0,623, C2 0,614, C1 0,605, TSMixer 0,604, M3 0,594, M1 0,551; F1 berbobot hampir sama; akurasi bila minggu tanpa perubahan dihitung salah: TimesFM 0,566, M1 0,508. Replikasi 3 seed (h 8): TSMixer MAE/M1 0,966 ± 0,007 (0,959..0,972), akurasi 0,610 ± 0,005; PatchTST 0,972 ± 0,011, 0,583 ± 0,016; TSMixer + kurs 0,995 ± 0,009 (lebih buruk dari TSMixer di ketiga seed). Kepekaan blok bootstrap 2/3/4/6 origin: 17/17 keputusan sama di kedua horizon; DM TimesFM vs M1 p < 0,001 dan M2 vs M1 p 0,006–0,018 untuk lag HAC 1–5. Per tahun origin, keunggulan MAE TimesFM bertahan pada 2026 (0,938) walau lebih kecil dari 2023–2024 (0,876 / 0,834). Robustness Tier 2 dijalankan tercatat: identik sha256 dengan file resmi (679 baris), sekarang sinkron. Audit Lampiran C.8.
- Koreksi multiplisitas (D-143, 2026-11-24): BH per keluarga di penilaian halaman 7 & tabel segmen; `findings.md` dan audit
  (Lampiran C.7) disesuaikan. Lolos BH: MAE TimesFM (± kurs) vs M1 h 4 & 8 (q ≤ 0,004); akurasi arah TimesFM vs M3 h 4 (q 0,015), C2 vs M3 h 4 (q 0,015), C1 vs M1 h 4 & 8 (q ≤ 0,024); akurasi arah vs baseline: semua model baru dan M3 (q ≤ 0,034), M1/M2 tidak. Gugur: TSMX_fx vs TSMX MAE h 4 (p 0,020 → q 0,057); segmen kaku TimesFM (q 0,053) & M2 (q 0,080); segmen lentur M1 (q 0,064). Beda berpasangan 5/30 bertahan; metrik arah vs acuan 123/132; rasio MAE eksploratif 4/14; tabel segmen h 8: 47 lebih baik, 15 lebih buruk dari 190.
- Model deep & foundation EKSPLORATIF (D-142, 2026-11-24): `models.neural` (PatchTST, TSMixer ± kurs, TimesFM 3.0 ± kurs),
  `kagami task4 --deep` → `deep_preds` (run eksekusi tercatat 7.632 dtk, CPU). TimesFM 3.0 zero-shot (TFM) MAE / M1 0,935 (h 4, DM p 0,0001) dan 0,895 (h 8, DM p < 0,001), R² vs ramalan nol 0,19 / 0,25 (M1 0,09 / 0,07), akurasi arah 0,616 / 0,623 (selisih vs baseline 0,049..0,116 / 0,026..0,122), ROC-AUC 0,66 / 0,69; TFM − M3 akurasi arah +0,043 (0,021..0,064) pada h 4, h 8 tidak terbukti. PatchTST & TSMixer: MAE / M1 0,96–1,00 (DM tidak nyata), akurasi arah 0,58–0,61. Fitur kurs tidak membantu: TFM_fx / TFM MAE 1,005 / 1,010 (tidak nyata), TSMX_fx / TSMX 1,041 (h 4, DM p 0,020, lebih buruk) / 1,029; selisih akurasi arah ± 0,01 (memuat nol). Komoditas kaku: semua model deep di bawah baseline arah (TFM −0,073 pada h 8). Catatan kontaminasi: TimesFM 3.0 dilatih ulang Google pada 2026 dengan korpus publik yang tidak diketahui isinya; deret harga pangan Indonesia periode uji 2021–2026 mungkin ikut di dalamnya, jadi keunggulan zero-shot adalah batas atas.
- Optimasi klasifier arah EKSPLORATIF (D-145, 2026-11-24): `features.price_dynamics` + `models.direction` C1t/C2t,
  `kagami task4 --direction-tuned` → `direction_tuned_preds`. Origin pengembangan (target ≤ 2023) untuk seleksi, test origin ≥ 2024:
  C1t macro F1 0,677 / 0,680 vs TimesFM 0,618 / 0,621 (lolos BH); kurs, threshold, kepala TimesFM, TSMixer-tuned tidak menambah.
  Laporan `docs/audit/20261124_task4_optimasi_arah.md`.
- Klasifier arah EKSPLORATIF (D-141, 2026-11-24): `models.direction` C1/C2, `kagami task4 --direction` → `direction_preds`
  (run eksekusi tercatat 1.119 dtk). C2 (+ kurs) akurasi arah 0,598 / 0,617 (h 4 / h 8) vs baseline mayoritas 0,527 / 0,545 (selisih +0,071, interval 0,034..0,108 pada h 8); C1 (tanpa kurs) 0,588 / 0,607; ROC-AUC C2 h 8 0,654 (0,623..0,682); MCC 0,17–0,23. C2 − C1 +0,010 (−0,005..0,024) / +0,009 (−0,007..0,027) → fitur kurs tidak terbukti membantu, konsisten dengan H5; C2 − M3 +0,025 (0,011..0,041) pada h 4, +0,014 (−0,000..0,031) pada h 8; C1 − M1 +0,045 / +0,047 (interval > 0). Komoditas kaku: C2 −0,026 (−0,067..0,024) → tidak lagi lebih buruk dari baseline (M3 −0,058); lentur +0,124. Prediksi selektif C1 h 8: akurasi 0,707 pada cakupan 25%.
- Selesai bila: [x] setiap tahap tercatat (sukses/gagal) dengan metrik relevan atau alasan tidak berlaku; [x] run induk dari hash
  input; [x] log tidak pernah ditimpa; [x] metrik = rumus independen (tes); [x] app hal. 7 lima bagian.
