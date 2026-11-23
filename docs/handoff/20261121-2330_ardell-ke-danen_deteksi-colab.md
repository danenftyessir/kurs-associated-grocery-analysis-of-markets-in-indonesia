---
dari: Ardell
ke: Danen
jenis: KEPUTUSAN
terkait: D-027, D-100, WP-32
status: terbuka
dibuat: 2026-11-21 23:30
tenggat_respon: 2026-11-23
---

# Colab terdeteksi sebagai Kaggle: `detect_platform` dibetulkan (edit kecil di file milik Danen)

## Ringkasan
Saat notebook 01 dijalankan di Colab, `drive.pull` gagal dengan `ModuleNotFoundError: No module named 'kaggle_secrets'`. Penyebabnya `detect_platform`
mengembalikan "kaggle" bila folder `/kaggle/input` ada, dan image Colab ternyata punya folder itu. Karena blokir untuk run Colab, saya mengubah
satu fungsi di `src/utils/env.py` (file milikmu) dan menambah tes regresi; tolong tinjau.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `detect_platform` | `src/utils/env.py` | branch `feat/task1-checkpoint` | urutan: env Kaggle → penanda Colab → folder `/kaggle/input` (cadangan) |
| Tes regresi | `tests/test_runtime.py::test_colab_not_mistaken_for_kaggle_when_kaggle_input_exists` | idem | tiga kasus: Colab menang, folder saja → Kaggle, env Kaggle menang |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada (hanya urutan pemeriksaan).

## Yang perlu dilakukan penerima
- [ ] Tinjau perubahan `detect_platform`; unggah ulang `kagami_code.zip` ke dataset Kaggle `kagami-code` bila Kaggle dipakai (perilaku Kaggle tidak berubah).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_runtime.py
```
Hasil yang diharapkan: semua lolos.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Gejala | `ModuleNotFoundError: kaggle_secrets` di Colab pada `drive.pull` | log Colab Ardell, 2026-11-21 |

## Batasan, risiko, yang belum beres
- Tidak diuji di Kaggle sungguhan; di Kaggle `KAGGLE_KERNEL_RUN_TYPE` diset sehingga urutan baru tidak mengubah hasil.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
