---
dari: Danen
ke: Ardell
jenis: PERMINTAAN
terkait: WP-23, WP-20, D-127, 20261122-2000_danen-ke-semua_g-het-h2.md
status: selesai
dibuat: 2026-11-23 02:00
tenggat_respon: 2026-11-25
---

# Dua perbaikan kecil sebelum pembekuan hasil: p-value meta-regresi dan ARI saat k = 1

## Ringkasan
Audit artefak asli (22 Nov) menemukan dua angka yang bisa terbaca sebagai temuan padahal bukan. (1) p-value meta-regresi di `assoc`
lebih sempit dari intervalnya sendiri, sehingga 11 baris p < 0,05 memiliki interval yang memuat nol. (2) `partition_compare` menulis
ARI = 0,0 untuk semua partisi karena k = 1; angka itu trivial dan terbaca "tidak cocok dengan zona HET". Keduanya file milikmu.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Temuan p-value | `src/models/association.py::meta_regression` baris ± 215–227 | `dev` 2026-11-22 | p dari `se_cr2`; interval = max(CR2, bootstrap) |
| Temuan ARI | `src/evaluation/stability.py::compare_partitions` | `dev` 2026-11-22 | label k = 1 → ARI 0 untuk partisi apa pun |
| Artefak yang terdampak | `results/task3/assoc.csv`, `results/task2/partition_compare.csv` | Drive tim 2026-11-22 | perlu ditulis ulang setelah perbaikan |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada (nilai `p_value` dan `ari` berubah). Usulan aditif opsional: kolom `q_fdr` di baris provinsi `assoc`.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada.

## Yang perlu dilakukan penerima
- [x] `meta_regression`: hitung `p_value` dari SE yang konsisten dengan interval, yaitu `max(se_cr2, se_boot)` (t dengan df yang sama),
      atau dari bootstrap. Syarat: p < 0,05 ⇔ interval tidak memuat nol (kecuali baris H3 satu sisi). Tambah tes regresinya.
- [x] Opsional: `q_fdr` BH atas baris `level = province` non-H3 (± 99 uji eksploratif tanpa koreksi saat ini).
- [x] `compare_partitions`: bila label klaster hanya satu kelompok, tulis `ari = NaN` (bukan 0) dan biarkan app/findings menampilkan
      "tidak berlaku (k = 1)". Tambah tes.
- [x] Jalankan ulang `task2` & `task3` lalu unggah `assoc` dan `partition_compare` ke Drive tim. `task3` kini juga menulis ulang
      `asymmetry` & `regime_profiles` versi D-127 (± 9 menit tambahan untuk plasebo E2, paralel joblib).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_association.py tests/test_clustering.py
```
Hasil yang diharapkan: lolos; di `assoc` tidak ada baris `meta_regression_re` dengan p < 0,05 yang intervalnya memuat nol.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Baris meta-regresi p < 0,05 tetapi interval memuat nol | 11 dari 109 | `assoc` (22 Nov) |
| Contoh | gula `n_kota` h8: p 0,010, interval −0,11..0,04 | `assoc` |
| Rasio `se_boot / se_cr2` | ± 1,5–6 | `assoc` |
| ARI semua partisi | 0,0 (k = 1) | `partition_compare` |

## Batasan, risiko, yang belum beres
- Sampai diperbaiki, Abi jangan mengutip p-value meta-regresi provinsi; pakai intervalnya saja.
- H3 (baris `meta_regression_re_one_sided`) tetap p 0,80 → tidak didukung; arah kesimpulan tidak berubah.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.

Ditindaklanjuti Danen 2026-11-23 setelah pengambilalihan jalur B (D-130, D-132): p = max(p CR2, p bootstrap sisi), `q_fdr`,
ARI NaN saat k = 1; `task2` & `task3` dijalankan ulang (0/88 baris p < 0,05).
