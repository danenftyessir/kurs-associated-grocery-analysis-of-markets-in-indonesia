---
dari: Ardell
ke: Danen
jenis: PERMINTAAN
terkait: D-119, WP-16, 20261121-1800_danen-ke-ardell_ols-cluster.md
status: terbuka
dibuat: 2026-11-21 21:00
tenggat_respon: 2026-11-23
---

# D-119 tidak menutup error SVD di macOS: `pinv(X'X)` gagal pada satu desain bootstrap

## Ringkasan
Setelah menarik `dev` (termasuk D-119), error `numpy.linalg.LinAlgError: SVD did not converge` di `stats.regression.ols_cluster` masih muncul pada
data asli di macOS (Apple silicon). Penyebabnya bukan grup kosong: matriks desain berrank penuh dan terkondisi baik. Tidak menghalangi run di Colab/Kaggle (Linux),
jadi ini bukan blokir; permintaan ini untuk kekokohan lintas platform.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Kasus gagal | bootstrap `joint_bootstrap` replikasi ke-3 (seed `cfg.seed + 1601`), daging sapi, provinsi 19, h = 12, `province_deviations` | `dev` 2026-11-21 | n = 441, X: 441 × 36, rank 36, cond(X) = 60, y dan X semuanya finite |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada. Usulan perubahan isi saja di `ols_cluster`.

## Yang perlu dilakukan penerima
- [ ] `src/stats/regression.py::ols_cluster`: ganti `np.linalg.pinv(X.T @ X)` dengan `np.linalg.pinv(X.T @ X, hermitian=True)` (matriks simetris → eigh).
      Pada kasus di atas versi hermitian memberi hasil yang sama dengan `np.linalg.lstsq` (allclose), sedangkan `np.linalg.pinv` dan `scipy.linalg.pinv` gagal.
- [ ] Bila perlu bukti: numpy 2.3.5 dan 2.5.5, scipy 1.18.1, pandas 3.1.1, Python 3.13, macOS (Darwin 24.3, arm64). Gagal di kedua versi numpy.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_stats.py tests/test_inference.py
```
Hasil yang diharapkan: semua lolos pada semua OS.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Waktu 1 replikasi bootstrap (nasional + provinsi h kunci, tanpa harga dunia) | 2,6 dtk | lokal macOS |

## Batasan, risiko, yang belum beres
- Hanya terjadi di macOS pada satu desain dari beberapa ribu; Linux/Windows mungkin tidak terpengaruh.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
