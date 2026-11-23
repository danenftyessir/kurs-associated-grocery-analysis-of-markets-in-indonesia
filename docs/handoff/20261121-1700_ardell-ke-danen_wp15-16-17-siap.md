---
dari: Ardell
ke: Danen
jenis: PERMINTAAN
terkait: WP-15, WP-16, WP-17, WP-18, WP-19, D-201, 20261121-1200_danen-ke-ardell_se-plasebo-tier1.md
status: terbuka
dibuat: 2026-11-21 17:00
tenggat_respon: 2026-11-22
---

# WP-15/16/17 siap (sintetis + data asli tanpa harga dunia); 1 permintaan perbaikan `ols_cluster`

## Ringkasan
Deviasi provinsi, bootstrap, plasebo, penyusutan EB, dan fitur respons sudah selesai dan dites. Kolom `se` yang kamu minta ada di baris provinsi `profiles` dan di setiap replikasi `placebo_stats`. Run penuh (P2) menunggu `world_prices_weekly` dan sesi Kaggle. Ada satu permintaan kecil untuk file milikmu: `np.linalg.pinv` di `stats.regression.ols_cluster` gagal pada satu desain bootstrap di macOS.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `demean_cross_section`, `province_deviations`, `region_profiles` | `src/models/deviations.py` | branch `feat/reference-tables` (menyusul `feat/task1-inference`) | `province_deviations(..., *, elig=None, horizons=None, commodities=None)`; driver e & w; unit = province_id string; kolom `se`, `n_obs` |
| `joint_bootstrap`, `circular_placebo`, `bootstrap_ci` | `src/evaluation/inference.py` | idem | `est(pb, db, wb, commodities=)`; `world` ikut di-resample (D-201) |
| `shrink_deviations`, `response_features` | `src/features/response.py` | idem | `response_features` memuat PT8 nasional untuk Kendall |
| Pemanggil di `task1.run` | `src/pipelines/task1.py` | idem | `elig` ke deviasi, `est` memakai `wb` dan menyertakan deviasi provinsi pada `key_horizons` |

## Perubahan kontrak
- Artefak/kolom/skema: aditif. `placebo_stats` dan `boot_replicates` membawa kolom ekstra `se` bila estimator menghasilkannya (provinsi dan nasional); `profiles` provinsi membawa `se`, `n_obs`.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: `inference.joint_bootstrap(..., B, world=None, B_nonfocus=None)` dan `circular_placebo(..., R, world=None, R_nonfocus=None)`; `deviations.province_deviations/region_profiles` bertambah argumen keyword-only. Pemanggil di `task1.py` sudah disesuaikan (blok pemanggil WP-16, edit kecil di file kamu).

## Yang perlu dilakukan penerima
- [ ] `src/stats/regression.py::ols_cluster`: ganti `np.linalg.pinv(X.T @ X)` dengan `np.linalg.pinv(X.T @ X, hermitian=True)` (matriks simetris, memakai eigh). Pada replikasi bootstrap ke-3 data asli (daging sapi, provinsi 19, h = 12; n = 441, rank 36 dari 36, cond 60) `pinv` melempar `LinAlgError: SVD did not converge` di macOS (numpy 2.3.5 dan 2.5.5; `scipy.linalg.pinv` juga gagal); versi hermitian memberi hasil sama dengan `lstsq`. Mungkin tidak muncul di Windows/Linux, tetapi bootstrap 499 × banyak desain akan memicunya cepat bila terjadi. Tes regresi: matriks tahan banting yang sama (lihat `tests/test_inference.py`) atau tes `ols_cluster` dengan desain kolinear.
- [ ] G-het (WP-18): baca `profiles` provinsi dengan `driver == "e"`, `horizon == 8`, `shrunk == False`, `unit` string `"1".."34"`; `placebo_stats` provinsi hanya h ∈ {4, 8, 12} (jadi h = 8 ada).
- [ ] Beri tahu bila kamu lebih suka `ols_cluster` tidak diubah; saya pakai `pinv(hermitian=True)` hanya di skrip uji lokal sementara itu.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_deviations.py tests/test_inference.py tests/test_response.py
```
Hasil yang diharapkan: semua lolos.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Deviasi provinsi, h 4/8/12, 10 komoditas | 1.011 baris, Σ_r δ = 0, cabai rawit 31 provinsi | `profiles` (data asli, tanpa w) |
| Waktu 1 replikasi bootstrap (nasional + provinsi h kunci, tanpa w) | 2,6 dtk → B = 499 ± 22 menit | uji lokal |
| R8 nasional beras | 0,084 (sama dengan `national_profiles`) | `profiles` |

## Batasan, risiko, yang belum beres
- Belum ada `world_prices_weekly` di mesin Ardell, jadi driver w belum dihitung pada data asli; sintetis memakai harga dunia.
- τ² DL vs REML dicetak per sel; pada B = 3 selisih maks 0,52 (sel ber-se besar) dan akan diperiksa pada run penuh.
- β nasional tidak ditafsirkan di sini (aturan MDE sebelum β sudah terpenuhi lewat G-power 21 Nov).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
