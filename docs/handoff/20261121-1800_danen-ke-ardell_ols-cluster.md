---
dari: Danen
ke: Ardell
jenis: KEPUTUSAN
terkait: D-119, D-118, WP-12, WP-15, WP-16
status: terbuka
dibuat: 2026-11-21 18:00
tenggat_respon: 2026-11-22
---

# `ols_cluster` diperbaiki: baris dengan grup kosong dibuang, tidak lagi crash

## Ringkasan
Menanggapi update Ardell ("perbaikan `ols_cluster` di macOS menunggu Danen"). Ditemukan regresi dari D-118: bila `groups` berisi
NaN/NaT/None, `pd.factorize` memberi kode −1 dan `np.bincount` melempar `ValueError: 'list' argument must have no negative elements`.
Ini terjadi di semua OS, tidak khusus macOS. Kini baris dengan grup kosong dibuang (sama seperti baris NaN di y/X), D-119.
Hasil LP nasional, Tier 1, dan `mde` tidak berubah.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `ols_cluster` (grup kosong dibuang) | `src/stats/regression.py` | `dev` setelah merge branch Danen | signature sama |
| Tes regresi | `tests/test_stats.py::test_ols_cluster_drops_missing_groups` | idem | grup NaT & NaN |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada. Signature `ols_cluster` tidak berubah; `n_obs` kini tidak menghitung baris grup kosong.
- Bukan DEVIASI PRAREGISTRASI.

## Yang perlu dilakukan penerima
- [ ] Ardell: tarik `dev` terbaru, lalu jalankan ulang kode yang tadinya gagal di macOS.
- [ ] Ardell: bila masih gagal, kirim pesan error lengkap (traceback) + versi numpy/pandas lewat handoff `BLOKIR`; penyebab di mesin
      Ardell belum dikonfirmasi, perbaikan ini menutup penyebab yang paling mungkin.
- [ ] Ardell: dorong branch `feat/...` Ardell ke `origin` dan merge ke `dev` (belum terlihat di remote per 2026-11-21) agar Danen bisa
      menjalankan WP-18/21/22/27 pada kode yang sama.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_stats.py
```
Hasil yang diharapkan: semua lolos, termasuk `test_ols_cluster_drops_missing_groups`.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Suite tes | 190 lolos, 1 dilewati | lokal Windows, 2026-11-21 |
| Perubahan hasil nasional (`profiles`, Tier 1, `mde`) | tidak ada (tidak ada minggu kosong di desain nasional) | D-119 |

## Batasan, risiko, yang belum beres
- Bila kode Ardell (deviasi provinsi, bootstrap) sengaja memberi grup kosong, baris itu kini tidak ikut regresi; periksa `n_obs`.
- Belum diuji di macOS (tidak ada mesin macOS di sisi Danen).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
