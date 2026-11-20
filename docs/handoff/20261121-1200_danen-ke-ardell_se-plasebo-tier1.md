---
dari: Danen
ke: Ardell
jenis: PERMINTAAN
terkait: WP-16, WP-18, WP-19, WP-21, WP-22, WP-28, D-111, D-112, 20261120-2353_danen-ke-ardell_lp-event-qa.md
status: terbuka
dibuat: 2026-11-21 12:00
tenggat_respon: 2026-11-24
---

# Kolom `se` wajib di baris provinsi `placebo_stats` + hasil Tier 1

## Ringkasan
Kode WP-18 (heterogenitas vs plasebo) dan WP-22 (Kendall eksak) sudah siap dan dites dengan data sintetis. WP-18 menghitung Q dan τ²
DerSimonian–Laird, jadi butuh SE setiap deviasi provinsi, **termasuk di setiap replikasi plasebo**. Kontrak `placebo_stats` saat ini
tidak memuat `se`. Tolong bawa `se` (SE cluster minggu dari `fit_lp`) sebagai kolom ekstra. WP-28 (Tier 1) sudah jalan pada data asli.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `heterogeneity.heterogeneity_stats`, `placebo_pvalues` | `src/evaluation/heterogeneity.py` | WP-18 | dipanggil `task2` apa adanya |
| `association.kendall_exact` | `src/models/association.py` | WP-22 | dipanggil `task3`; butuh `response_features` (PT8 nasional) + `exposure` |
| `robustness.tier1`, `fx_decomposition` | `src/evaluation/robustness.py` | WP-28 | 382 baris, 21 dtk lokal |
| `planted.recovery_curve` (+ `best_silhouette`, `placebo_threshold`, `detection_limit`) | `src/evaluation/planted.py` | WP-21 | ± 20 dtk untuk 200 replikasi |

## Perubahan kontrak
- Artefak/kolom/skema: **permintaan** kolom ekstra `se` pada baris `level='province'` di `profiles` (tanpa susut) dan `placebo_stats`
  (kolom ekstra boleh menurut `write_artifact`, jadi registry tidak perlu diubah). Tanpa kolom itu `heterogeneity_stats` melempar `KeyError`.
- Driver yang dibaca WP-18: `e`, h = 8, `shrunk == False`; `unit` = province_id.
- `pipelines.robustness.REQUIRES` kini juga memuat `panel_weekly`, `eligibility`, `episodes`; `tier1(cfg, panel, drivers, world, *, elig, ...)`,
  `validation(cfg, profiles, events, episodes, drivers, world, forecast_eval)`.
- `events` (dari `placebo_bands`, ditulis `task1` saat kamu menjalankannya) kini punya kolom ekstra `placebo_median` (D-114); tidak perlu
  perubahan di kodemu.

## Yang perlu dilakukan penerima
- [ ] WP-15/16: sertakan `se` pada baris deviasi provinsi di `profiles` dan di setiap replikasi provinsi `placebo_stats`.
- [ ] WP-17: `response_features` level national memuat `PT8` untuk 10 komoditas (dibaca Kendall).
- [ ] WP-07: `exposure.import_ratio_direct` terisi untuk 10 komoditas (komoditas domestik boleh 0; NaN dibuang dari Kendall).
- [ ] WP-19/`task2.py`: δ tertanam berada dalam satuan respons (D-112), jadi `recovery_curve` butuh matriks plasebo **belum
  distandardisasi**. Usul: `replicate_feature_matrices(cfg, placebo, standardize=True)` dengan opsi `standardize=False`, lalu di
  `task2`: `planted.recovery_curve(cfg, cluster_features.replicate_feature_matrices(cfg, placebo, standardize=False))`.
- [ ] WP-19: `ward_labels(X, k)` mengembalikan label 0..k-1 (dipakai default oleh `recovery_curve`). Agar ambang plasebo identik,
  `select_k` sebaiknya memakai aturan yang sama: silhouette Euclidean Ward maksimum atas k ≥ 2, `np.nanpercentile` pada
  `silhouette_placebo_pct`. Bila kamu ingin memakai ulang `best_silhouette`, pindahkan ke `models/clustering.py` (evaluation boleh
  import models, tidak sebaliknya) dan beri tahu saya agar `planted.py` mengimpornya dari sana.

Solusi sementara peminta: WP-18, WP-21, WP-22 dites dengan generator sintetis berskema sama (`tests/test_heterogeneity.py`,
`tests/test_planted.py`; Ward rujukan scipy disuntikkan lewat argumen `ward`).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_heterogeneity.py tests/test_robustness.py tests/test_planted.py
```
Hasil yang diharapkan: semua lolos.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Daging ayam β_e(8) baseline (SE cluster) | −1,67 (−2,62..−0,73) | `tier1` (lokal Danen) |
| … tanpa Mar–Jun 2020 & bulan Brent ekstrem | −0,96 (−2,05..0,14) | `tier1` |
| … komponen spesifik rupiah (dekomposisi DXY) | −1,89 (−3,02..−0,76) | `tier1` |
| Porsi varians de yang dijelaskan d_dxy | 27% (b = 0,72) | `tier1` |
| Bulan Brent ekstrem yang dibuang | Mar–Jun 2020, Mar 2026, Nov 2026 | `tier1` |

## Batasan, risiko, yang belum beres
- Interval Tier 1 = ±1,96·SE cluster, bukan bootstrap (D-111).
- Artefak `robustness` baru ditulis saat WP-29 dan `forecast_eval` (P4) ada; angka di atas dari jalan lokal.
- Keputusan G-het (25 Nov) menunggu P2 dengan `se`.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
