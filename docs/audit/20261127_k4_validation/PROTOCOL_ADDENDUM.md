# Validasi K4 — Protokol audit (ditulis sebelum analisis, 2026-11-27)

Catatan bertanggal. Berlaku untuk analisis baru di folder ini (`scripts/v_*.py`). Protokol D-164 ([PROTOCOL.md](../20261126_k4_risiko_material/PROTOCOL.md))
tidak diubah. sha256 file ini dan skrip saat beku: `hasil/protocol_sha256.txt`.

## 1. Batas

- **Baca-saja** terhadap D-164: prediksi beku `k4_{dev,test,forward}_preds.parquet` dibaca apa adanya. Tidak ada model K4 yang dilatih ulang,
  tidak ada perubahan di `src/`, label resmi Task 4, C1-tuned, macro F1 resmi, H5, atau file prediksi maju.
- **Test 2024+ tidak dibuka lagi.** Semua analisis baru (kalibrasi, galat, kepekaan) hanya memakai baris dev (origin + h ≤ 2023-12-31).
  Angka test yang dikutip berasal dari file `hasil/k4_test_*` D-164 yang sudah terbit. Pengecualian satu-satunya: audit integritas target
  (§2) menghitung jumlah baris tanpa target dan mencocokkan y/z dengan panel. Itu bukan pengukuran kinerja.
- Tidak ada seleksi model, ambang, K, atau τ. Hasil kalibrasi hanya boleh menghasilkan **kandidat untuk protokol prospektif**, bukan adopsi.

## 2. Audit integritas target (`v_target.py`)

Untuk dev, test, maju: jumlah target tak teramati per bagian × horizon × komoditas; label yang diberikan kode; apakah baris itu ikut latih;
hitung ulang y_h dan z dari artefak `panel_weekly`; universe latih vs evaluasi; status ujung (observed / carry_forward / short) per kelas label.
Bila target tak teramati diberi z = 0, dampaknya dihitung dengan membandingkan dua penanganan (asli vs dikeluarkan), tanpa melatih ulang.

## 3. Audit kalibrasi (`v_calib.py`, dev saja)

**Himpunan evaluasi** = himpunan peluang D-164: origin dev dengan ≥ 6 origin lampau yang targetnya terealisasi. Semua kalibrator dinilai
pada baris identik.

**Kalibrator** (semua walk-forward: di origin o hanya memakai baris origin o' dengan o' + h ≤ o):

| ID | Kalibrator |
|---|---|
| C0 | mentah (K4-E80) |
| C1 | Platt global (= K4-E80-cal D-164) |
| C2 | isotonik global (step function monoton, `out_of_bounds="clip"`) |
| C3 | Platt per komoditas bila komoditas itu punya ≥ 30 positif dan ≥ 30 negatif di masa lalu; selain itu Platt global |
| C4 | geser intersep saja (logit p + a, kemiringan 1) |
| C5 | Platt global pada 13 origin terakhir saja (jendela ± 1 tahun, menangkap pergeseran laju) |
| C6 | campuran laju-dasar: p' = w·p + (1 − w)·CLIM, w ∈ {0; 0,05; …; 1} dipilih dengan Brier minimum di masa lalu |

**Ukuran**: Brier (utama), log loss, ECE 10 bin, intersep & kemiringan kalibrasi (regresi logistik z ~ logit p pada baris evaluasi, deskriptif),
Brier skill vs B-CLIM, ΔBrier vs C0 dengan interval bootstrap blok origin (1.999 replikasi, blok ceil(h/4)+1, seed r = 0..1998 seperti D-164),
q BH atas 6 kalibrator × 2 horizon, reliabilitas ekor (p ≥ 0,6 dan ≥ 0,7), jumlah origin berbeda di setiap bin ekor.

**Aturan** (ditulis sebelum hasil): sebuah kalibrator menjadi **kandidat prospektif** hanya bila di h 8 ΔBrier vs C0 < 0 dengan batas atas interval
< 0 dan q < 0,05, di h 4 ΔBrier ≤ 0 (titik), dan ECE ≤ 0,05 di kedua horizon. Penurunan ECE tanpa penurunan Brier **tidak** cukup (D-163a).
Tidak ada kandidat yang diadopsi; konfirmasi hanya lewat prediksi maju dengan protokol baru.

**Diagnosis penyebab** (deskriptif): komposisi ekor menurut komoditas, origin, tahun; kalibrasi-dalam-besaran per origin (rerata p − laju
terealisasi) vs laju terealisasi; laju latih vs laju terealisasi per origin; rezim ex-ante (tersil momentum harga nasional rerata `nat_dp_4`
pada origin); ukuran sampel efektif kalibrator (jumlah origin, positif di ekor).

## 4. Analisis galat operasional (`v_errors.py`, dev saja)

Kebijakan K = 1, 2, 3, 5 per provinsi (aturan tie D-154, seed 154) dan setara-V2 nasional (2 × jumlah provinsi). Kategori alarm palsu: naik di
bawah ambang, turun, tetap, nyaris (≥ ½ dan ≥ ¾ ambang), lonjakan di tengah jendela yang berbalik (z_any = 1, z = 0), kenaikan sesudah titik
akhir (max_{k=h+1..h+4} kenaikan ≥ ambang). Kategori kenaikan terlewat: peringkat dalam provinsi, harga datar 4 minggu sebelumnya, komoditas
diatur, laju origin rendah. Juga persistensi alarm, jumlah komoditas unik, sebaran alarm antarprovinsi (V2-setara), kinerja menurut tersil rezim
ex-ante dan tersil laju terealisasi.

## 5. Kepekaan definisi target (`v_sensitivity.py`, dev saja + angka test terbit)

P70 / P80 / P90 |y|, P90 y bertanda, kejadian dalam jendela (P80): laju, komposisi positif (porsi komoditas diatur), ambang median dalam persen
dan rupiah per kg (materialitas ekonomi), AP & presisi@K2 K4 vs C1t vs CLIM vs CLIMS. Deskriptif; tidak ada target yang dipilih.
