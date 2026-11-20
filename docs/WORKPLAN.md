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
| WP-07 | Tabel buatan tim (concordance, exposure, regulation, province_features) | ⬜ | Ardell | 02 | 22 Nov |
| WP-08 | Panel 7 wilayah | ✅ | Danen | 04 | 21 Nov |
| WP-09 | MDE / analisis daya (G-power) | ✅ | Danen | 05, 08 | 23 Nov |
| WP-10 | QA silang & laporan Tahap 0 | ⬜ | Danen | 03–09 | 23 Nov |
| WP-11 | Praregistrasi & pembekuan (G6) | ⬜ | Danen + Abi | – | 21 Nov |
| WP-12 | Mesin statistik bersama | ✅ | – | – | 20 Nov |
| WP-13 | LP nasional + asimetri + PT (`build_design`/`fit_lp` terbit 22 Nov untuk WP-15) | 🔶 | Danen | 05, 09 | 23 Nov |
| WP-14 | Event study per episode | ⬜ | Danen | 06, 08 | 23 Nov |
| WP-15 | Deviasi provinsi & profil wilayah | ⬜ | Ardell | 13 | 24 Nov |
| WP-16 | Bootstrap bersama & plasebo | ⬜ | Ardell | 13, 15 | 24 Nov |
| WP-17 | Penyusutan EB & fitur respons | ⬜ | Ardell | 16 | 24 Nov |
| WP-18 | Heterogenitas vs plasebo (G-het) | ⬜ | Danen | 16 | 25 Nov |
| WP-19 | Clustering & pemilihan k | ⬜ | Ardell | 17 | 25 Nov |
| WP-20 | Stabilitas & pembanding partisi | ⬜ | Ardell | 19 | 25 Nov |
| WP-21 | Uji struktur tertanam | ⬜ | Danen | 19 | 26 Nov |
| WP-22 | Asosiasi level komoditas (Kendall) | ⬜ | Danen | 07, 17 | 25 Nov |
| WP-23 | Meta-regresi provinsi | ⬜ | Ardell | 07, 16 | 26 Nov |
| WP-24 | Robustness FE komoditas×minggu (3c) | ⬜ | Ardell | 23 | 26 Nov (dapat dipotong) |
| WP-25 | Fitur Task 4 + as-of join | ⬜ | Ardell | 05, 08 | 22 Nov |
| WP-26 | Model M0–M3 rolling-origin | ⬜ | Ardell | 25 | 24 Nov |
| WP-27 | Evaluasi DM & ablation | ⬜ | Danen | 26 | 25 Nov |
| WP-28 | Robustness Tier 1 | ⬜ | Danen | 13 | 26 Nov |
| WP-29 | Validasi V2 & V4 | ⬜ | Danen | 14, 27 | 26 Nov |
| WP-30 | Robustness Tier 2 | ⬜ | Danen | 28 | opsional |
| WP-31 | Halaman Streamlit final | ⬜ | Ardell | 17–29 | 27 Nov |
| WP-32 | Paket juri & uji jalan ulang (G7) | ⬜ | Ardell | 31 | 28 Nov |
| WP-33 | Temuan & makalah | ⬜ | Abi | 17–29 | 28 Nov |
| WP-34 | Audit klaim (G8) | ⬜ | Abi | 31, 33 | 28 Nov |
| WP-35 | Tugas manusia | ⬜ | Abi (+ Danen: bundle & Kaggle) | – | lihat item |

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

### WP-07 — Tabel buatan tim
- File: `src/data/reference.py` → `concordance`, `exposure`, `regulation`, `province_features` di `data/reference/`.
- Selesai bila:
  - [ ] concordance: 10 baris, confidence diisi; seri Pink Sheet tervalidasi ada (tes sudah di `test_config`).
  - [ ] exposure: `import_ratio_direct` rerata 2018–2023 dari FAOSTAT; bawang putih dari BPS/Comtrade atau ordinal (U5); setiap angka punya `source`.
  - [ ] regulation: gabungan 3 sumber regulasi, tanggal tak terverifikasi ditandai `unverified` (U6).
  - [ ] province_features: `dist_hub_km` dihitung dari koordinat `region_crosswalk.csv`; `rice_sufficiency` & `n_kota` diisi atau NaN + U14/U15 dicatat.
- Input baru (2026-11-20, D-101): `hortikultura_produksi` (produksi bawang putih → rasio impor, U5), `konkordansi_hs` (jembatan Comtrade 2017–2022 → HS8 BPS), `jarak_hub` (cek silang `dist_hub_km`), BPS impor v2 (+bawang putih), regulasi revisi 20 Nov. Loader sudah ada (`src/data/loaders.py`); signature fungsi WP-07 boleh ditambah parameter oleh Ardell (pemilik `reference.py`) + `pipelines/stage0.py` disesuaikan lewat handoff.

### WP-08 — Panel 7 wilayah ✅
- File: `src/data/panel.py` → `panel_weekly_region` (indeks, bukan level Rp; D-015). Tes `tests/test_panel.py`.
- Selesai: [x] 7 wilayah × 10 komoditas × 464 minggu = 32.480 baris; [x] `n_provinces` per minggu; [x] hanya indeks log
  relatif minggu pertama (tanpa level Rp).
- Rerata wilayah tahan perubahan komposisi: dekomposisi dua arah efek provinsi + efek minggu (D-106); identik dengan rerata
  biasa bila semua provinsi teramati (median selisih 0; maks 0,10 log pada minggu komposisi berubah).
- Satu-satunya minggu kosong: 2022-05-02 (Idulfitri 2022) di 5 wilayah → `log_price_index` NaN, `n_provinces` 0 (50 sel).

### WP-09 — MDE / analisis daya (G-power) ✅
- File: `src/evaluation/power.py` (`compute_mde`, `null_se`, `gate_g_power`) → `mde`. Spesifikasi METHODS §M0.6. Tes `tests/test_power.py`.
- Selesai: [x] MDE nasional & 7 wilayah, 10 komoditas, h ∈ {4, 8, 12} (240 baris); [x] angka gerbang di D-007 (pembaruan 2026-11-20).
- SE di bawah H0 dalam bentuk skor (β̂ tidak pernah dihitung; D-107). γ(4/8/12) = 1,44 / 1,32 / 1,03.
- MDE_PT(8) nasional: bawang putih 2,52, gula pasir 0,90, **minyak goreng 0,465** → tidak ketiganya > 0,5 → **LP tetap utama**
  (D-007). Hasil SEMENTARA: params belum dibekukan (G6 21 Nov) → jalankan ulang `stage0` setelah G6 dan putuskan G-power 23 Nov.
  Minyak goreng dekat ambang: perubahan varian/lag di G6 bisa membalik keputusan.
- MDE_PT(8) terkecil: daging sapi 0,13, beras 0,20; terbesar: cabai rawit 3,75, cabai merah 3,00. Wilayah ≈ 1,5–2× nasional.

### WP-10 — QA silang & laporan Tahap 0
- File: `src/data/qa.py` → `stage0_report`.
- Selesai bila: [ ] outlier satu hari ditandai (contoh: Papua beras 2017-07-03); [ ] Σ BPS bulanan = total tahunan (satuan USD, sudah dicek: rasio 1,000 untuk 2023); [ ] bias PIHPS vs Panel Harga Bapanas; [ ] tabel cakupan per sumber.

### WP-11 — Praregistrasi & pembekuan (G6)
- File: `docs/PREREGISTRATION.md` (draf sudah ada), `configs/*.yaml`.
- Selesai bila: [ ] U10 diputuskan (varian), D-011/D-012 diubah dari PROVISIONAL ke FINAL; [ ] semua hipotesis, uji, ambang, k-range, B/R terisi; [ ] baris "Dibekukan pada" diisi tanggal + sha256 `configs/params.yaml` & `configs/commodities.yaml`.

## Task 1 — profil respons
Pipeline `pipelines.task1` · notebook `01_task1_profiles` · berat → Kaggle/Colab.

### WP-12 — Mesin statistik bersama ✅
`stats/regression.py` (OLS CR1 cluster, Newey-West, Diebold-Mariano+HLN), `stats/resampling.py`, `stats/meta.py` (DL, REML, EB, BH). Tes `tests/test_stats.py`. Tambah fungsi baru di sini bila dipakai > 1 task.

### WP-13 — LP nasional + asimetri + PT 🔶
- File: `src/models/local_projection.py` → baris `profiles` level=national, driver ∈ {e, w, e_pos, e_neg, PT}.
- Sudah (2026-11-20, tes `tests/test_local_projection.py`): `build_design` (+ `elig`, `unit_col`, `price_col` untuk panel provinsi,
  wilayah, deviasi), `regressors`, `fit_lp`, `fx_self_response`. Belum: `national_profiles`. β pada data asli BELUM dilihat.
- Spesifikasi: METHODS §M1.1–M1.2.
- Selesai bila: [x] tes pada data sintetis dengan β diketahui (dipulihkan dalam 2,5 SE, termasuk β⁺/β⁻ dan ω); [x] γ(h) dari LP kurs pada dirinya; [x] `n_weeks` dilaporkan (`fit_lp`); [ ] `national_profiles`; [ ] runtime 10 komoditas × 13 horizon < 2 menit.

### WP-14 — Event study per episode
- File: `src/models/event_study.py` → `events`. Selesai bila: [ ] level national & region; [ ] 499 jendela plasebo dari minggu tanpa episode; [ ] p plasebo per horizon.

### WP-15 — Deviasi provinsi & profil wilayah
- File: `src/models/deviations.py`. Selesai bila: [ ] Σ_r δ = 0 per (komoditas, horizon) (tes); [ ] profil 7 wilayah jalan dari `panel_weekly_region` saja.

### WP-16 — Bootstrap bersama & plasebo
- File: `src/evaluation/inference.py` → `boot_replicates`, `placebo_stats`, CI bootstrap di `profiles`.
- Selesai bila: [ ] satu indeks minggu per replikasi dipakai semua seri; [ ] plasebo provinsi hanya h ∈ {4, 8, 12}; [ ] runtime diukur — bila > 30 menit, B=R=199 untuk non-fokus (`bootstrap_B_nonfocus`) + catat D-.

### WP-17 — Penyusutan EB & fitur respons
- File: `src/features/response.py` → `profiles` (shrunk=True) + `response_features`.
- Selesai bila: [ ] τ² DL dan REML dilaporkan berdampingan; [ ] τ² = 0 → semua provinsi = rerata (bukan error); [ ] t_half NaN bila tidak terdeteksi.

## Task 2 — pola regional
Pipeline `pipelines.task2` · notebook `02_task2_patterns` · berat → Kaggle/Colab.

### WP-18 — Heterogenitas vs plasebo (G-het)
- File: `src/evaluation/heterogeneity.py` → `heterogeneity`. Selesai bila: [ ] Q, τ², I² per komoditas (h=8) + ρ̄; [ ] p plasebo + q FDR antar-10 komoditas; [ ] keputusan G-het di DECISIONS.

### WP-19 — Clustering & pemilihan k
- File: `src/features/clustering.py`, `src/models/clustering.py` → `cluster_selection`.
- Selesai bila: [ ] fitur = R & W h∈{4,8,12} komoditas fokus, tersusut, terstandardisasi; [ ] k=1 dilaporkan bila silhouette maks ≤ p95 plasebo.

### WP-20 — Stabilitas & pembanding partisi
- File: `src/evaluation/stability.py` → `clusters`, `coassign`, `partition_compare`. Selesai bila: [ ] ARI Ward vs K-Means; [ ] Jaccard per klaster, weak bila < 0,6; [ ] ARI vs zona HET, Jawa/luar Jawa, n_kota.

### WP-21 — Uji struktur tertanam
- File: `src/evaluation/planted.py` → `planted_recovery`. Selesai bila: [ ] kurva recovery untuk δ ∈ {0,1..0,5}, k_true ∈ {2,3}; [ ] δ minimum dengan recovery ≥ 0,8 dicatat sebagai "batas deteksi" di findings.

## Task 3 — asosiasi
Pipeline `pipelines.task3` · notebook `03_task3_association` · ringan.

### WP-22 — Asosiasi level komoditas (Kendall)
- File: `src/models/association.py::kendall_exact` → `assoc` level=commodity. Selesai bila: [ ] p permutasi eksak (10! = 3.628.800, vektorisasi/itertools); [ ] leave-one-commodity-out.

### WP-23 — Meta-regresi provinsi
- File: `src/models/association.py::meta_regression` → `assoc` level=province. Selesai bila: [ ] ≤ 3 fitur praregistrasi; [ ] interval bootstrap vs CR2, yang lebih lebar dilaporkan; [ ] jackknife provinsi.

### WP-24 — Robustness FE komoditas×minggu (3c)
- File: `src/models/association.py::fe_interaction`. Dapat dipotong (D-014).

## Task 4 — evaluasi prediktif
Pipeline `pipelines.task4` · notebook `04_task4_forecast` · berat → Kaggle/Colab; paralel dengan Task 1.

### WP-25 — Fitur Task 4 + as-of join
- File: `src/features/forecast.py`. Selesai bila: [ ] tes kebocoran: untuk origin acak, tidak ada fitur dengan `available_at` > origin dan tidak ada target dengan t+h > origin di train.

### WP-26 — Model M0–M3 rolling-origin
- File: `src/models/forecasting.py` → `data/interim/forecast_preds.parquet`. Selesai bila: [ ] origin tiap 4 minggu dari 2021-01-04; [ ] M3 dapat dimatikan via flag bila waktu habis.

### WP-27 — Evaluasi DM & ablation
- File: `src/evaluation/forecast_eval.py` → `forecast_eval`, `ablation`. Selesai bila: [ ] rasio MAE/RMSE vs M1 untuk semua & large_move; [ ] DM HAC; [ ] n_origins & n_nonoverlap di setiap baris; [ ] H5 dijawab untuk grup fokus.

## Robustness & validasi
Pipeline `pipelines.robustness` · notebook `05_robustness` · sedang–berat → Kaggle/Colab.

### WP-28 — Robustness Tier 1
- File: `src/evaluation/robustness.py::tier1`. Semua 6 cek di `TIER1`. Tidak boleh dipotong.

### WP-29 — Validasi V2 & V4
- File: `src/evaluation/robustness.py::validation`. V2 studi kasus 2026 (origin terakhir h=8 ≈ akhir Sep 2026), V4 LP vs event study.

### WP-30 — Robustness Tier 2
- File: `src/evaluation/robustness.py::tier2`. Opsional; pertama dipotong.

## Produk & submission

### WP-31 — Halaman Streamlit final
- File: `app/`. Selesai bila: [ ] 6 halaman menampilkan artefak nyata; [ ] setiap grafik: sumber, satuan, periode, interval, label "asosiasi, bukan kausalitas"; [ ] lencana "tidak terdeteksi"; [ ] halaman 3 menangani k=1; [ ] halaman 5 bendera ekstrapolasi; [ ] tanpa login/input data/estimasi runtime.

### WP-32 — Paket juri & uji jalan ulang (G7)
- File: `src/pipelines/package.py`. Selesai bila: [ ] `python -m kagami package` tanpa `--allow-missing`; [ ] ekstrak zip di folder baru → `pip install -e .` → `python -m kagami app` jalan (Tingkat A) dan `task4` jalan dari data kirim (Tingkat B); [ ] tidak ada file `redistribute: false` di zip (cek daftar isi).

### WP-33 — Temuan & makalah
- Output: `results/findings.md` (dibaca app hal. 6) + makalah PDF sesuai struktur juknis: judul, abstrak, pendahuluan (latar belakang, tujuan & manfaat, batasan), kajian pustaka, solusi usulan (deskripsi, dataset, metode, perbedaan dengan solusi sebelumnya, matriks evaluasi), hasil eksperimen & pengujian, analisis, kesimpulan & saran, daftar pustaka.
- Selesai bila: [ ] setiap angka di makalah berasal dari artefak (sebutkan nama artefak di komentar sumber); [ ] rujukan "belum diverifikasi" (U12) dicek atau dihapus.

### WP-34 — Audit klaim (G8)
- Selesai bila: [ ] setiap kalimat temuan di findings.md, makalah, app lolos tabel "Jangan tulis/Tulis" (PROJECT_OVERVIEW §6); [ ] setiap angka punya interval; [ ] hasil nol ditulis sebagai batas atas.

### WP-35 — Tugas manusia `[HUMAN]`
- [x] **Abi** · Izin BI (U13) — sudah diperoleh (dikonfirmasi Danen 2026-11-20).
- [ ] **Abi** · Konfirmasi jalur unduh PIHPS resmi (U19); bila bukan, laporkan agar Danen mengunduh ulang via fitur resmi.
- [ ] **Abi** · Data manual (PEMBAGIAN_TUGAS §6.2): populasi, n_kota, GKG→beras, verifikasi regulasi, pemetaan Bapanas; PADG 7/2026 (U3).
- [ ] **Danen** · Prasyarat kolaborasi (PEMBAGIAN_TUGAS §8): repo GitHub privat + .gitignore, folder Drive tim (bagikan terbatas + `python -m kagami drive-push-raw`; D-100, D-101), dataset Kaggle
      `kagami-code` (**PRIVAT**, `python -m kagami bundle`; `kagami-raw` opsional), bagikan ke Ardell. Ulangi bundle setiap `src/` berubah.
- [ ] **Danen** · Taruh CSV penduduk 2025 & snapshot kab/kota Panel Harga di lokasi DATASETS.md §Menunggu diunggah (U103).
- [ ] **Danen & Ardell** · Token Drive masing-masing (`drive-auth`) + Kaggle Secret `KAGAMI_DRIVE_TOKEN` (`docs/NOTEBOOKS.md` §Persiapan 2).
- [ ] **Abi** · Rekam video demonstrasi (alur: masalah → app 6 halaman → Tingkat A/B).
- [ ] **Abi** · Unggah makalah PDF + zip + video ke Google Drive dan form pendaftaran Gelombang 2.
