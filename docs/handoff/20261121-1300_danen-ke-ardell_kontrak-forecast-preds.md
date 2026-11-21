---
dari: Danen
ke: Ardell
jenis: PERMINTAAN
terkait: WP-26, WP-27, D-113
status: diterima
dibuat: 2026-11-21 13:00
tenggat_respon: 2026-11-24
---

# Kontrak `forecast_preds` untuk evaluasi DM & ablation (WP-27)

## Ringkasan
`forecast_eval.evaluate` dan `ablation` (WP-27) sudah jadi dan dites dengan prediksi sintetis. `task4` memanggilnya apa adanya
setelah `rolling_predictions` (WP-26, milikmu). Agar langsung jalan pada P4, `forecast_preds` perlu mengikuti kontrak di bawah,
terutama nama model ablation `M2_nofx`.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `forecast_eval.evaluate`, `ablation`, `n_nonoverlap` | `src/evaluation/forecast_eval.py` | WP-27 | dipanggil `task4` tanpa perubahan |
| `stats.meta.holm` | `src/stats/meta.py` | WP-27 | koreksi H5 |
| Generator prediksi sintetis | `tests/test_forecast_eval.py::_preds` | – | boleh dipakai untuk tes WP-26 |

## Perubahan kontrak
- Artefak/kolom/skema: `forecast_eval` + kolom ekstra `level`, `n_obs`, `dm_p_one_sided`, `h5_p_holm`, `h5_reject`;
  `ablation` + `subset`, `level`, `n_origins`. Baris jalur H5 memakai `commodity` = `direct_import` / `imported_input`.
- **Permintaan:** `forecast_preds` berisi kolom `origin`, `horizon`, `model`, `province_id` (atau `region` untuk panel wilayah),
  `commodity`, `y_true`, `y_pred`, `large_move` (bool per baris, sama untuk semua seri dalam satu origin × horizon).
- **Permintaan:** model ∈ {M0, M1, M2, M3} + ablation bernama persis `M2_nofx` (M2 tanpa kelompok `fx`). Tanpa `M2_nofx`,
  `ablation` melempar `ValueError`.

## Yang perlu dilakukan penerima
- [x] WP-26: `rolling_predictions` menghasilkan kolom & nama model di atas.
- [x] WP-26: `large_move` = |Δe 4 minggu| di origin > persentil `forecast.large_move_pct` data latih (sudah di docstring).
- [ ] Bila nama/kolom lain lebih cocok untukmu, balas lewat handoff; saya sesuaikan `forecast_eval` (konstanta `ABLATION_MODEL`).

Solusi sementara peminta: WP-27 dites dengan generator sintetis berskema sama (`tests/test_forecast_eval.py`).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_forecast_eval.py
```
Hasil yang diharapkan: semua lolos.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| HAC lag DM (origin tiap 4 minggu) | h = 4 → 0, h = 8 → 1 | – (D-113) |
| Keluarga H5 | 2 jalur, Holm, α 0,05; p tak terdefinisi = 1 | – (D-113) |

## Batasan, risiko, yang belum beres
- Belum dijalankan pada prediksi asli; H5 dijawab setelah P4.
- DM memakai MAE per origin (rerata lintas seri), bukan galat per baris (D-113).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
