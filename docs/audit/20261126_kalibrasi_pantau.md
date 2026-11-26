# Kalibrasi skor daftar pantau C1-tuned (D-163a, Task 4 arah, EKSPLORATIF)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-163 · Protokol: [PROTOKOL.md](20261126_kalibrasi_pantau/PROTOKOL.md)
(sha256 `e0b50c8f…c521`, dibekukan 11:17 UTC sebelum diukur) · Skrip: `20261126_kalibrasi_pantau/scripts/kal.py` · Hasil: `20261126_kalibrasi_pantau/hasil/`.

## 1. Pertanyaan

Kriteria S2 (kalibrasi, D-154) gagal tipis di dev h 8: ECE 0,056 > 0,05. Apakah lapisan kalibrasi pasca-model yang dipelajari
walk-forward dari prediksi OOS lampau memperbaiki peluang C1-tuned tanpa merusak daftar pantau? Tanpa model atau fitur baru; p_up
C1-tuned = `direction_tuned_preds` resmi (identik dengan `d151_iw_dev_preds` varian base, selisih maks 0).

## 2. Hasil dev (origin + h ≤ 2023-12-31; kalibrator aktif pada 84% / 81% baris, origin awal = identitas)

| h | Varian | ECE | Brier | ΔBrier vs C1t (interval) | Presisi S1 V1 | ΔS1 (interval) | macro F1 (0,5) |
|---|---|---|---|---|---|---|---|
| 4 | C1t | 0,035 | 0,2180 | – | 0,249 | – | 0,656 |
| 4 | K1 Platt global | 0,016 | 0,2189 | +0,0010 (−0,0027..+0,0050) | 0,249 | 0 (ranking sama) | 0,648 |
| 4 | K2 Platt + intersep komoditas | 0,022 | 0,2241 | +0,0061 (+0,0015..+0,0114) | 0,260 | +0,011 (−0,022..+0,043) | 0,632 |
| 4 | K3 isotonik global | 0,014 | 0,2205 | +0,0026 (−0,0008..+0,0062) | 0,228 | −0,021 (−0,037..−0,005) | 0,651 |
| 8 | C1t | **0,056** | 0,2128 | – | 0,221 | – | 0,676 |
| 8 | K1 | 0,042 | 0,2149 | +0,0021 (−0,0037..+0,0075) | 0,221 | 0 | 0,674 |
| 8 | K2 | 0,050 | 0,2267 | +0,0139 (+0,0065..+0,0224) | 0,268 | **+0,046 (+0,008..+0,098)** | 0,628 |
| 8 | K3 | 0,027 | 0,2145 | +0,0017 (−0,0038..+0,0069) | 0,213 | −0,008 (−0,017..+0,002) | 0,671 |

Keputusan protokol (ECE ≤ 0,05 kedua horizon **dan** ΔBrier < 0 kedua horizon **dan** S1 tidak turun > 0,005): **tidak ada varian lolos**
(`hasil/kal_decision.json`) → C1-tuned tanpa kalibrasi tetap; test 2024+ tidak dibuka.

## 3. Tafsiran

- Salah kalibrasi C1-tuned h 8 berbentuk terlalu yakin di kedua ujung (bin p ≈ 0,07: porsi naik 0,21; bin p ≈ 0,92: 0,78) dan terlalu rendah
  di tengah (p ≈ 0,55: 0,65). Kalibrasi global memampatkan skor sehingga ECE pooled turun di bawah 0,05, tetapi Brier tidak membaik:
  galat peluang yang tersisa adalah pergeseran laju naik antarperiode (D-147/D-148), yang tidak dapat dipelajari dari origin lampau.
  ECE di bawah ambang tanpa Brier yang lebih baik hanya memindahkan galat antarbin, jadi tidak dipakai.
- K2 (intersep per komoditas) menaikkan presisi daftar pantau h 8 (+0,046, interval > 0) karena mengubah urutan komoditas di dalam
  provinsi menurut laju naik historis masing-masing, tetapi peluangnya memburuk (Brier +0,014, macro F1 −0,048). Ini **petunjuk** bahwa
  skor ranking daftar pantau dan peluang arah sebaiknya dipisah (sejalan dengan kartu K4 "risiko kenaikan material" D-155), bukan hasil
  yang lolos: tidak ditetapkan sebagai sasaran sebelum diukur, h 4 tidak terbukti, dan K4 tetap menunggu validasi kebutuhan TPID (U109).
- Peluang C1-tuned tetap dapat dibaca dengan selisih rata-rata ± 1–6 poin persen (ECE 0,010–0,056 dev/test, D-154). Untuk tampilan
  daftar pantau, yang dipakai adalah urutan (S1), bukan nilai peluang absolut.
