---
dari: Danen
ke: Ardell, Abi
jenis: KEPUTUSAN
terkait: D-129, U107, D-127, WP-13, WP-16, WP-33, 20261123-0215_danen-ke-semua_positif-palsu.md
status: terbuka
dibuat: 2026-11-23 16:30
tenggat_respon: 2026-11-26
---

# Bootstrap blok menarik β ke nol; artefak tambahan `national_calibrated` dengan inferensi terkalibrasi plasebo

## Ringkasan
Audit `boot_replicates` menemukan bahwa bootstrap blok 13 minggu melemahkan estimasi LP. Rerata replikasi hanya 0,57 / 0,35 / 0,35 kali
estimasi asli pada h 4 / 8 / 12, karena blok lebih pendek dari jendela LP (h + lag + 2 minggu). Persentilnya bergeser ke nol, sehingga
interval resmi `profiles` terlalu konservatif (negatif palsu, bukan positif palsu). Interval resmi praregistrasi tetap dipakai. Sebagai
tambahan ada artefak baru `national_calibrated`: interval dan p untuk β_e & ω nasional yang dikalibrasi terhadap plasebo geser-melingkar
yang sudah ada (cara yang sama dengan E2, D-127). Ini analisis tambahan pasca-G6, bukan DEVIASI PRAREGISTRASI: uji konfirmatori dan
interval resmi tidak berubah.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Kode | `src/evaluation/calibration.py`, `src/pipelines/task3.py` | lokal Danen 2026-11-23 | tes `tests/test_calibration.py` |
| `national_calibrated` | Drive tim `results/task3/national_calibrated.csv` | `task3` 2026-11-23 | 48 baris (10 komoditas × e + 6 × w, h 4/8/12); 13.418 byte |

## Perubahan kontrak
- Artefak/kolom/skema: artefak baru `national_calibrated` (ship). Kolom wajib: commodity, driver, horizon, estimate, se, ci_low, ci_high,
  p_value, q_fdr; tambahan t, crit_placebo, crit, p_placebo, ci_excludes_zero, n_placebo, ci_prereg_low/high, boot_mean, boot_ratio, n_boot.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada (fungsi baru `calibration.national_calibrated`).

## Yang perlu dilakukan penerima
- [ ] Abi: kutip interval resmi `profiles` lebih dulu; `national_calibrated` disebut sebagai "analisis kepekaan inferensi yang dikalibrasi
      terhadap plasebo". Gula β_e(4) wajib diberi catatan "tidak tahan pengecualian Mar–Jun 2020 dan sub-periode pasca April 2021".
- [ ] Abi: tulis pelemahan bootstrap sebagai keterbatasan metode (U107), termasuk interval PT dan provinsi yang ikut terlalu konservatif.
- [ ] Ardell: app halaman 2 boleh menampilkan `national_calibrated` di samping interval resmi (label "terkalibrasi plasebo, analisis tambahan").
      Bila `task1` dijalankan ulang, jalankan juga `task3`.
- [ ] Ardell: `se_boot` meta-regresi (`assoc`) memakai bootstrap yang sama → ikut terlalu lebar; catat saat memperbaiki U106.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_calibration.py
```
Hasil yang diharapkan: lolos; di `national_calibrated`, (p_value < 0,05) sama dengan ci_excludes_zero pada semua baris.

## Angka penting
Keputusan D-129, bukan DEVIASI PRAREGISTRASI (tambahan pasca-G6). Interval dalam Δ log harga per 1 log penggerak.

| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Median `boot_ratio` h 4 / 8 / 12 | 0,57 / 0,35 / 0,35 | `national_calibrated` |
| Sel interval tidak memuat nol (resmi → terkalibrasi) | 3 → 7 dari 48 | `profiles`, `national_calibrated` |
| Daging ayam β_e(4) | −1,16 (−2,10..−0,23), q 0,024 | `national_calibrated` |
| Daging ayam β_e(8) | −1,67 (−2,77..−0,58), q 0,058; resmi −2,62..0,06 | `national_calibrated`, `profiles` |
| Gula β_e(4) | 0,69 (0,25..1,13), q 0,024; tanpa COVID −0,03, pasca 2021-04 −0,03 | `national_calibrated`, `robustness` |
| Minyak goreng ω(4) / ω(8) / ω(12) | 0,16 (0,04..0,28) q 0,092 / 0,21 (0,08..0,34) q 0,024 / 0,31 (0,16..0,46) q 0,024 | `national_calibrated` |
| Telur ω(8) | −0,22 (−0,40..−0,04), q 0,19 | `national_calibrated` |

Kalimat yang lolos rambu klaim: "Dalam analisis kepekaan yang mengkalibrasi interval terhadap 499 plasebo geser-melingkar, kenaikan harga
sawit dunia dalam rupiah berasosiasi dengan kenaikan harga minyak goreng sebesar 0,21 (0,08..0,34) per 1 log pada horizon 8 minggu;
tanda ini bertahan di semua pemeriksaan Tier 1."

## Batasan, risiko, yang belum beres
- Komoditas non-fokus memakai 199 plasebo → ambang dan p lebih kasar (minimum 0,005).
- Hanya β_e & ω nasional h kunci. Interval provinsi, PT, dan wilayah tetap memakai interval resmi (terlalu konservatif, U107).
- `kagami_code.zip` di Drive belum memuat `evaluation/calibration.py`; bundle perlu dibangun ulang sebelum `task3` dijalankan di Colab/Kaggle.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
