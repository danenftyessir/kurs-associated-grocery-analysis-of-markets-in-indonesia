---
dari: Danen
ke: Semua
jenis: KEPUTUSAN
terkait: D-126, U105, WP-21, 20261122-2000_danen-ke-semua_g-het-h2.md
status: terbuka
dibuat: 2026-11-22 21:00
tenggat_respon: 2026-11-24
---

# Batas deteksi struktur regional kini sah: δ = 0,2 (U105 selesai)

## Ringkasan
Uji struktur tertanam sebelumnya menanam kelompok buatan pada matriks plasebo yang sudah tersusut EB, sehingga δ = 0,1 pun selalu
terdeteksi. Kini δ ditanam pada deviasi plasebo mentah, lalu disusutkan dan di-z-score persis seperti data asli (D-126). Hasilnya,
struktur dengan selisih respons ≥ 0,2 per fitur akan terdeteksi; δ = 0,1 tidak.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Kode | `src/evaluation/planted.py` (`deviation_matrices`, `shrink_matrix`, `recovery_curve`) | branch Danen | tes `tests/test_planted.py` |
| Pemanggil | `src/pipelines/task2.py` (baris terakhir, milik Ardell) | branch Danen | satu baris diganti; atas izin Danen sebagai PIC WP-21 |
| Artefak | `results/task2/planted_recovery.csv` (lokal Danen) | `task2` 2026-11-22 | belum diunggah ke Drive tim |

## Perubahan kontrak
- `planted.recovery_curve(cfg, placebo_dev)` kini menerima daftar pasangan (D, S) dari `planted.deviation_matrices(cfg, placebo_stats)`,
  bukan matriks hasil `replicate_feature_matrices(..., standardize=False)`. Kolom artefak `planted_recovery` tidak berubah.

## Yang perlu dilakukan penerima
- [ ] Ardell: tinjau satu baris perubahan di `src/pipelines/task2.py` dan docstring `replicate_feature_matrices` (`src/features/clustering.py`).
- [ ] Abi: tulis batas deteksi dengan catatan tafsir di bawah; jangan memakai angka recovery dari handoff 20261122-2000.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_planted.py tests/test_task2.py
```
Hasil yang diharapkan: semua lolos, termasuk tes regresi U105.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Recovery δ = 0,1 (k = 2 / 3) | 0,43 / 0,13 | `planted_recovery` |
| Recovery δ = 0,2 (k = 2 / 3) | 0,995 / 0,965 | `planted_recovery` |
| Batas deteksi (recovery ≥ 0,8) | δ = 0,2 untuk k = 2 dan 3 | `planted_recovery` |
| Ambang silhouette plasebo | 0,196 (sama dengan `cluster_selection`) | `planted_recovery` |

## Batasan, risiko, yang belum beres
- δ adalah selisih respons RMS per fitur yang sama untuk semua fitur. Deteksi didorong fitur yang presisi (W dan R gula, daging sapi,
  minyak goreng; median SE deviasi 0,03–0,16). Struktur yang hanya ada di cabai/bawang (SE 0,4–1,2) butuh selisih jauh lebih besar.
- Kalimat yang disarankan: "Tidak ada struktur regional yang terdeteksi (k = 1); struktur dengan selisih respons rata-rata ≥ 0,2 per
  fitur akan terdeteksi dengan peluang ≥ 0,96."

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
