---
dari: Ardell
ke: Danen
jenis: KEPUTUSAN
terkait: WP-07, WP-25, WP-26, WP-27, D-200, U14, U15, U21, U103
status: terbuka
dibuat: 2026-11-20 20:00
tenggat_respon: 2026-11-21
---

# WP-07, WP-25, WP-26: kode siap; ada tambahan kontrak (aditif) dan 3 hal yang perlu Danen lakukan

## Ringkasan
Kode WP-07 (tabel referensi), WP-25 (fitur as-of Task 4), dan WP-26 (model M0–M3, run penuh belum) sudah selesai dengan tes sintetis dan dicoba pada data asli yang ada di laptop Ardell. Ada tambahan kontrak yang aditif (artefak `forecast_preds`, tiga sumber manual, dua kunci params) dan satu perubahan kecil di `pipelines/stage0.py` (blok tabel tim). Dua kunci params baru harus masuk sebelum hash G6 dibekukan.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `build_concordance/exposure/regulation/province_features` | `src/data/reference.py` | branch `feat/reference-tables` (tabel referensi) dan `feat/forecast-features` (Task 4) | signature bertambah parameter opsional; semua NaN-aman |
| `load_penduduk`, `load_n_kota`, `load_gkg_beras` | `src/data/loaders.py` | idem | file belum ada → tabel kosong berskema |
| 3 sumber baru (`optional: true`) | `configs/sources.yaml` | idem | `penduduk`, `n_kota`, `gkg_beras` (total sumber 23) |
| Blok tabel tim di `stage0.run` | `src/pipelines/stage0.py` | idem | hanya baris pemanggil `reference.*`; PR kecil terpisah bila perlu (PEMBAGIAN_TUGAS §3) |
| Fitur & model Task 4 | `src/features/forecast.py`, `src/models/forecasting.py` | idem | `feature_table`, `split_origin` baru |
| Artefak `forecast_preds` | `data/interim/forecast_preds.parquet`, stage `task4`, `ship=False` | idem | input WP-27; ikut di-push ke Drive oleh notebook 04 (tahan sesi habis) |
| Generator sintetis Task 1 & 4 | `tests/synthetic.py` | idem | berlabel dummy |

## Perubahan kontrak
- Artefak/kolom/skema: aditif — `forecast_preds` (kolom: `origin, horizon, model, region, commodity, y_true, y_pred, large_move`; plus `province_id` bila panel provinsi). Label `model` ∈ `M0, M1, M2, M3, M2_nofx`; `M2_nofx` = M2 tanpa kelompok `fx` (untuk `ablation`: `delta_mae` = MAE(`M2_nofx`) − MAE(`M2`)). `large_move` = |Δe 4 minggu| > persentil ke-`large_move_pct` data latih origin itu.
  `province_features` dan `regulation` mendapat kolom ekstra (`rice_production_ton`, `rice_need_ton`, `dist_hub_km_check`; `commodity_raw`, `in_scope`, `source`, `date_status`, `value_min_rp`, `value_max_rp`); kolom kontrak tidak berubah.
- `configs/*.yaml`: `params.association.import_ratio_years` = [2018, 2023] (baru), `params.forecast.run_m3` = true (baru) — **keduanya perlu masuk sebelum hash G6 (21 Nov)**; `sources.yaml` +3 sumber.
- Fungsi publik yang berubah signature: `reference.build_concordance/build_exposure/build_province_features` (parameter opsional ditambahkan di belakang); `forecasting.rolling_predictions` (parameter `include_m3`, `done`, `checkpoint`). Pemanggil di `stage0.py` dan `task4.py` sudah disesuaikan.

## Yang perlu dilakukan penerima
- [ ] Sebelum membekukan G6: pastikan `association.import_ratio_years` dan `forecast.run_m3` ikut dalam hash `params.yaml`.
- [ ] Unggah CSV penduduk 2025 ke `data/raw/bps_kependudukan/penduduk_provinsi_2025.csv` lalu `python -m kagami drive-push-raw` (U103). Loader `load_penduduk` menebak skema kolom BPS dan menolak total di luar 200–400 juta jiwa; mohon kabari nama kolom aslinya bila loader menolak.
- [ ] Pastikan `drive-push-raw` juga mengunggah `faostat`, `wb_pinksheet`, `manual_geo`, `manual_concordance` (di laptop Ardell folder itu kosong, jadi `build_exposure` pada data asli belum bisa diuji).
- [ ] Untuk WP-27: baca `forecast_preds` lewat `read_artifact(cfg, "forecast_preds")` (label model di atas). Run penuh oleh Ardell setelah P1 (`drivers_weekly` dengan `episode`, `world_prices_weekly`) tersedia.
- [ ] Review blok `reference.*` di `pipelines/stage0.py`.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_reference.py tests/test_forecast.py tests/test_synthetic.py
python -m kagami status
```
Hasil yang diharapkan: semua tes tersebut lulus; `status` menampilkan `penduduk`, `n_kota`, `gkg_beras` sebagai belum ada (opsional) sampai file diunggah.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Baris `regulation` dari 3 sumber | 72 (30 verified, 24 confirmed, 13 partial, 5 unverified) | `regulation` (data asli, belum ditulis ke `data/reference/`) |
| Origin Task 4, h=8, panel provinsi asli | 75 (2021-01-04 .. 2026-09-07) | `panel_weekly` (tanpa harga dunia) |
| Waktu M3 per origin | ≈ 1,5–2 detik | uji lokal |

## Batasan, risiko, yang belum beres
- Belum divalidasi pada data asli: `build_exposure` (butuh FAOSTAT, konkordansi), `dist_hub_km_check` (butuh `jarak_hub`), `rice_sufficiency` (butuh penduduk dan faktor GKG dari Abi); `n_kota` dan `gkg_beras` menunggu Abi (U15, U21).
- Pada data sintetis fitur kurs memperbaiki MAE; pada data asli (tanpa harga dunia) selisih M1 vs M2 sangat kecil — jangan ditafsirkan sebelum run penuh.
- Aturan tabel referensi dicatat di D-200.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
