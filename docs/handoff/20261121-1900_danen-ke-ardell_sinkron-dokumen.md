---
dari: Danen
ke: Ardell
jenis: PERMINTAAN
terkait: WP-07, WP-15, WP-16, WP-17, WP-19, WP-20, WP-23, WP-24, WP-25, WP-26, WP-31, WP-32
status: selesai
dibuat: 2026-11-21 19:00
tenggat_respon: 2026-11-22
---

# Enam branch Ardell digabung ke `dev`: kode lolos, tetapi 6 tes dokumen/paket merah

## Ringkasan
Danen menggabungkan `feat/reference-tables`, `feat/forecast-features`, `feat/task1-inference`, `feat/task2-clustering`,
`feat/task3-association`, dan `feat/app-package` ke `dev` (urut, `--no-ff`, tanpa konflik git). Simulasi gabungan di Windows:
**276 tes lolos, 3 dilewati, 6 gagal** (2 lainnya gagal hanya karena variabel lingkungan uji Danen). Semua tes fungsional Ardell
lolos; yang gagal adalah penjaga sinkronisasi dokumen (CLAUDE.md §3.4) dan satu tes paket yang tidak portabel.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Hasil merge 6 branch Ardell | `dev` | setelah merge 2026-11-21 | termasuk perbaikan `ols_cluster` D-119 dari Danen |
| Daftar tes gagal | file ini | 2026-11-21 | dari `python -m pytest -q` pada pohon gabungan |

## Perubahan kontrak
- Tidak ada perubahan dari Danen. Artefak baru dari Ardell: `forecast_preds` (32 artefak).
- **Perlu dicatat Ardell:** dua kunci baru di `configs/params.yaml` setelah G6 (`association.import_ratio_years: [2018, 2023]`,
  `forecast.run_m3: true`) belum punya entri DEVIASI PRAREGISTRASI di `docs/DECISIONS.md` (PEMBAGIAN_TUGAS §5).
  `import_ratio_years` ikut menentukan `exposure.import_ratio_direct` → hasil E1 (WP-22), jadi alasannya perlu tertulis.

## Yang perlu dilakukan penerima
- [x] Ardell: CLAUDE.md §9 untuk modul sendiri: tandai ✔ fungsi yang sudah diimplementasi (`build_concordance`, `build_exposure`, …)
      dan tambahkan fungsi publik baru: `load_penduduk`, `load_n_kota`, `load_gkg_beras`, `parse_regulation_dates`,
      `classify_verification`, `feature_columns`, `feature_table`, `split_origin`, `models.clustering.best_silhouette`,
      `sensitivity_heatmap`, `cluster_sizes` (`tests/test_claude_md.py::test_functions_and_status_match`).
- [x] Ardell: jumlah artefak di CLAUDE.md §9.1 → 32 (`test_artifact_count_stated`).
- [x] Ardell: `forecast_preds` di tabel `docs/ARCHITECTURE.md` §5 (`test_wiring.py::test_every_artifact_has_producer_and_is_documented`).
- [x] Ardell: sumber `penduduk` dan `gkg_beras` di `docs/DATASETS.md` dan CLAUDE.md §10.1 (`test_docs_sync.py::test_sources_documented`).
- [x] Ardell: 11 file tes baru di CLAUDE.md §16.1 (`test_synthetic`, `test_forecast`, `test_response`, `test_inference`, `test_task2`,
      `test_deviations`, `test_package`, `test_app_data`, `test_clustering`, `test_association`, `test_reference`) (`test_tests_documented`).
- [x] Ardell: `tests/test_package.py::test_extracted_package_runs_cli` gagal di Windows Danen: subprocess `python -I` dengan
      `env={"PATH": "/usr/bin:/bin", ...}` tidak melihat pandas yang terpasang di user site-packages
      (`%APPDATA%\Python\Python313\site-packages`) → `ModuleNotFoundError: No module named 'pandas'`. Usul: teruskan `os.environ`
      (timpa hanya `KAGAMI_*`) dan buang `-I`, atau lewati tes bila pandas tidak terlihat dari interpreter terisolasi.
- [x] Ardell: entri DEVIASI PRAREGISTRASI untuk dua kunci `params.yaml` di atas (D-200+), status WP di papan `docs/WORKPLAN.md`
      dan baris Ardell di CLAUDE.md §2.
- [x] Ardell: setelah `dev` terbaru ditarik, jalankan ulang kode yang tadinya gagal di macOS dengan `ols_cluster` (handoff
      `20261121-1800_danen-ke-ardell_ols-cluster.md`).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_claude_md.py tests/test_docs_sync.py tests/test_wiring.py tests/test_package.py
```
Hasil yang diharapkan: semua lolos, lalu seluruh suite (`python -m pytest -q`) hijau.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Tes pada pohon gabungan (Windows, data mentah lokal) | 276 lolos, 3 dilewati, 6 gagal (dokumen 5, paket 1) | simulasi merge Danen 2026-11-21 |
| Konflik git `dev` ← `feat/app-package` | 0 | `git merge-tree` |

## Batasan, risiko, yang belum beres
- Sampai daftar di atas selesai, `dev` merah pada 6 tes; jangan dibekukan ke `main`.
- Danen belum memeriksa isi metode (bootstrap, clustering, meta-regresi, model Task 4) baris per baris; ini hanya pemeriksaan
  integrasi dan tes.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
