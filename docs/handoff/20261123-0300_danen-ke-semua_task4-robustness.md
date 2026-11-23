---
dari: Danen
ke: Abi, Ardell
jenis: ANGKA-MAKALAH
terkait: WP-27, WP-29, D-128, D-113, D-114
status: terbuka
dibuat: 2026-11-23 03:00
tenggat_respon: 2026-11-26
---

# Task 4 dievaluasi dan robustness lengkap: fitur kurs tidak memperbaiki prediksi, H5 tidak didukung

## Ringkasan
Prediksi Task 4 asli (Ardell) sudah dievaluasi ulang secara lokal dan hasilnya identik dengan versi di Drive. Fitur kurs dan harga dunia
sedikit memperburuk MAE, sehingga H5 tidak didukung. Kesimpulan ini tetap sama walaupun model diganti menjadi ridge per komoditas
(D-128). Artefak `robustness` (Tier 1 + V2 + V4) kini ada; angka di bawah siap dipakai di makalah dan `findings.md`.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `forecast_eval`, `ablation` | Drive tim `results/task4/` (Ardell) + lokal Danen | 2026-11-22 | `evaluate` lokal identik (selisih ≤ 4e-16) |
| `robustness` | Drive tim `results/robustness.csv` | `robustness` 2026-11-23 | 486 baris (Tier 1 382, validasi 104); 130.052 byte |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada.

## Yang perlu dilakukan penerima
- [ ] Abi: tulis Task 4 sebagai "dalam evaluasi bersyarat pseudo-real-time (76 origin 2021–2026), fitur kurs dan harga dunia tidak
      menurunkan MAE; rasio M2/M1 1,014 (h 4) dan 1,017 (h 8)". H5: "tidak didukung" dengan catatan hanya 8 origin pergerakan besar.
- [ ] Abi: jangan menulis "model gagal". Rasio MAE ≈ 1 adalah hasil sah (CLAUDE.md §1.6); M0 (tanpa perubahan) hampir setara M1.
- [ ] Ardell: app halaman 4 cukup membaca `forecast_eval`; pertimbangkan menampilkan bahwa `M2_nofx` identik dengan M1 (ablation = −(M2 − M1)).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_forecast_eval.py tests/test_robustness.py
```
Hasil yang diharapkan: lolos.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Origin (h 4 / h 8) | 76 / 75 (tidak tumpang tindih 76 / 38), 337 seri provinsi | `forecast_eval` |
| M2/M1 MAE semua origin, h 4 | 1,014 (DM p 0,001; M2 lebih buruk) | `forecast_eval` |
| M2/M1 MAE semua origin, h 8 | 1,017 (DM p 0,006) | `forecast_eval` |
| M3/M1 MAE h 4 / h 8 | 1,044 / 1,015 | `forecast_eval` |
| M0/M1 MAE h 4 / h 8 | 1,017 / 1,016 | `forecast_eval` |
| M2/M1 h 8 per komoditas (terburuk) | daging sapi 1,30; gula 1,13; beras 1,11; cabai & bawang merah ≈ 1 | `forecast_eval` |
| H5 direct_import (h 8, large_move) | 1,12, p satu sisi 0,95, Holm 1,0 | `forecast_eval` |
| H5 imported_input | 1,12, p satu sisi 0,88, Holm 1,0 | `forecast_eval` |
| Origin large_move | 8 dari 76 (7 tidak tumpang tindih pada h 8) | `forecast_eval` |
| V2 studi kasus 2026, M2/M1 | 1,005 (h 4, 10 origin); 1,005 (h 8, 9 origin) | `robustness` |
| V4 LP vs event study | implikasi LP di dalam interval event pada 26/30 sel | `robustness` |

## Batasan, risiko, yang belum beres
- M1/M2 adalah satu ridge gabungan 10 komoditas tanpa identitas komoditas (sesuai proposal). Ridge per komoditas sebagai diagnostik
  memberi kesimpulan sama (M2/M1 1,011 / 1,018; H5 1,18 / 1,12), tetapi bukan artefak: boleh disebut sebagai pemeriksaan kepekaan tanpa angka utama.
- Hanya 8 origin large_move → daya uji H5 rendah; tulis sebagai keterbatasan.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
