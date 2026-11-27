# Validasi K4 — Audit kalibrasi mendalam

Tanggal 2026-11-27, catatan bertanggal. Skrip `scripts/v_calib.py`, keluaran `hasil/cal_*.csv`. Aturan ditulis sebelum dijalankan:
[PROTOCOL_ADDENDUM.md](PROTOCOL_ADDENDUM.md) §3 (sha256 di `hasil/protocol_sha256.txt`). **Hanya dev.** Test tidak dibuka. Angka test yang
dikutip berasal dari `../20261126_k4_risiko_material/hasil/k4_test_*` yang sudah terbit.

STATUS: **COMPLETE** (diagnosis) · **FAILED** (tidak ada kalibrator yang memperbaiki Brier)

OBJECTIVE: Mencari tahu mengapa peluang K4-E80 h 8 terlalu yakin di ekor atas, dan apakah ada kalibrator walk-forward yang memperbaiki
**Brier**, bukan hanya ECE.

## 1. Himpunan dan kalibrator

Himpunan peluang D-164: dev h 4 32 origin / 10.778 baris, h 8 30 origin / 10.104 baris. Semua kalibrator dinilai pada baris identik dan
hanya memakai origin yang targetnya sudah terealisasi (o' + h ≤ o).

| ID | Kalibrator |
|---|---|
| C0 | mentah K4-E80 |
| C1 | Platt global (= K4-E80-cal D-164) |
| C2 | isotonik global |
| C3 | Platt per komoditas (≥ 30 positif & 30 negatif lampau; selain itu global) |
| C4 | geser intersep saja |
| C5 | Platt pada 13 origin terakhir |
| C6 | campuran p dan laju-dasar komoditas, bobot dari masa lalu |
| ORACLE | geser intersep per origin pada origin itu sendiri (**ex-post**, batas atas, tidak dapat dipakai) |

## 2. Hasil (`cal_metrics.csv`, `cal_paired_vs_raw.csv`, `cal_candidates.csv`)

| h | Kalibrator | Brier | ΔBrier vs C0 (interval 95%) | q BH | Log loss | ECE | Kemiringan | Brier skill vs CLIM (interval) |
|---|---|---|---|---|---|---|---|---|
| 4 | **C0 mentah** | **0,0979** | – | – | **0,328** | 0,023 | 0,86 | **0,116 (0,052..0,170)** |
| 4 | C1 Platt | 0,0985 | +0,0006 (−0,0006..0,0014) | 0,55 | 0,331 | 0,014 | 0,95 | 0,111 |
| 4 | C2 isotonik | 0,0994 | +0,0015 (−0,0008..0,0033) | 0,44 | 0,339 | **0,011** | 0,84 | 0,103 |
| 4 | C3 per komoditas | 0,1008 | +0,0029 (−0,0008..0,0074) | 0,38 | 0,338 | 0,021 | 0,76 | 0,090 |
| 4 | C4 intersep | 0,0990 | +0,0011 (0,0002..0,0019) | 0,072 | 0,331 | 0,023 | 0,83 | 0,106 |
| 4 | C5 Platt 13 origin | 0,0991 | +0,0012 (−0,0006..0,0027) | 0,38 | 0,332 | 0,014 | 0,92 | 0,105 |
| 4 | C6 campur laju-dasar | 0,0984 | +0,0004 (−0,0011..0,0020) | 0,77 | 0,331 | 0,017 | 1,10 | 0,112 |
| 4 | ORACLE (ex-post) | 0,0924 | −0,0055 (−0,0101..−0,0020) | – | 0,304 | 0,016 | 0,97 | 0,166 |
| 8 | **C0 mentah** | **0,1132** | – | – | 0,379 | 0,044 | **0,66** | 0,068 (−0,031..0,153) |
| 8 | C1 Platt | 0,1135 | +0,0003 (−0,0029..0,0038) | 0,77 | **0,374** | **0,019** | 0,83 | 0,065 |
| 8 | C2 isotonik | 0,1161 | +0,0029 (−0,0017..0,0089) | 0,38 | 0,424 | 0,034 | 0,39 | 0,044 |
| 8 | C3 per komoditas | 0,1198 | +0,0066 (−0,0086..0,0191) | 0,55 | 0,394 | 0,046 | 0,55 | 0,013 |
| 8 | C4 intersep | 0,1156 | +0,0024 (0,0006..0,0044) | 0,072 | 0,382 | 0,041 | 0,61 | 0,048 |
| 8 | C5 Platt 13 origin | 0,1161 | +0,0029 (−0,0013..0,0066) | 0,38 | 0,387 | 0,026 | 0,66 | 0,044 |
| 8 | C6 campur laju-dasar | 0,1136 | +0,0004 (−0,0035..0,0047) | 0,88 | 0,375 | 0,034 | 1,04 | 0,064 |
| 8 | ORACLE (ex-post) | 0,1059 | −0,0073 (−0,0115..−0,0030) | – | 0,343 | 0,028 | 0,77 | 0,127 |

**Aturan kandidat** (h 8 ΔBrier < 0 dengan batas atas < 0 dan q < 0,05; h 4 ΔBrier ≤ 0; ECE ≤ 0,05): **0 dari 6 lolos.** Tidak ada kalibrator
walk-forward yang menurunkan Brier di horizon mana pun. Platt (C1) dan isotonik (C2) menurunkan ECE (h 8 0,044 → 0,019; h 4 0,023 → 0,011)
dengan Brier sedikit lebih buruk. Ini pola yang sama dengan D-163a: **ECE turun ≠ peluang lebih baik.** Kalibrasi per komoditas (C3) paling
buruk: sampel per komoditas per origin terlalu kecil dan laju komoditas bergeser.

## 3. Ekor atas h 8 (`cal_reliability.csv`, `cal_tail_composition.csv`)

| Bin p (h 8, mentah) | n | Origin berbeda | Rerata p | Teramati |
|---|---|---|---|---|
| 0,5–0,6 | 126 | 19 | 0,550 | 0,516 |
| 0,6–0,7 | 101 | 15 | 0,643 | 0,465 |
| 0,7–0,8 | 87 | 8 | 0,747 | 0,529 |
| **0,8–0,9** | **57** | **5** | 0,835 | **0,281** |

- **Sampel efektif ekor atas adalah jumlah origin, bukan jumlah baris.** Ke-57 baris p ≥ 0,8 berasal dari 5 origin, dan 41 di antaranya dari dua
  origin: 2023-10-09 (22 baris, 9% positif) dan 2022-01-03 (19 baris, 16%). Komoditasnya beras 20, minyak goreng 28, telur 8, bawang putih 1.
- Dua mekanisme yang berbeda:
  - **2022-01-03, minyak goreng (rezim kebijakan).** Sesudah lonjakan akhir 2021, model memberi p 0,76. Harga kemudian turun (median y −7%).
    Masa ini bertepatan dengan intervensi harga minyak goreng 2022 (tabel regulasi tim mencatat HET 16 Mar 2022). Pola momentum terputus oleh
    kebijakan, sesuatu yang tidak dapat dilihat dari histori harga.
  - **2023-10-09, beras (salah alokasi dalam origin).** Laju origin justru tinggi (0,28), tetapi kenaikannya terjadi di cabai (laju 0,64–0,74,
    p 0,09–0,11) dan gula. Beras mendapat p 0,77 dari momentum +3,3% dan naik +1,4%, di bawah ambang 2,4%. Masalahnya bukan laju nasional yang
    salah, tetapi komoditas mana yang naik.
- Momentum nasional ex-ante ikut menjelaskan pola ini (`cal_by_regime.csv`). Pada origin dengan momentum naik (tersil atas), baris p ≥ 0,6 di h 8
  hanya 35% positif (164 baris). Pada momentum datar 84% (31 baris), turun 50% (50 baris). Model mengekstrapolasi momentum pada komoditas
  diatur.
- Di test (terbit, D-164), ekor h 8 tetap terlalu yakin: bin 0,5–0,6 teramati 0,27 (187 baris), 0,6–0,7 0,36 (67). Masalahnya bukan kebetulan dev.

## 4. Pergeseran laju antarorigin (`cal_per_origin.csv`, `cal_origin_shift_stats.csv`)

| | h 4 | h 8 |
|---|---|---|
| sd laju terealisasi per origin | 0,072 | 0,085 |
| sd rerata p K4 per origin | 0,047 | 0,053 |
| Korelasi rerata p vs laju terealisasi | 0,43 | 0,48 |
| Kemiringan rerata p terhadap laju | 0,29 | 0,30 |
| \|laju latih − laju terealisasi\| rerata | 0,058 | 0,067 |

- Model hanya menangkap ± 30% variasi laju antarorigin. Di minggu tenang peluangnya terlalu tinggi, di minggu berisiko terlalu rendah. Ekor
  atasnya justru terlalu tinggi pada origin dan komoditas tertentu.
- Oracle intersep per origin (ex-post) memperbaiki Brier 0,0055 / 0,0073 dengan interval < 0. Itu besarnya informasi yang hilang. Kalibrator
  walk-forward tidak dapat memulihkannya karena laju origin berikutnya tidak dapat diketahui dari laju origin lampau (C4, C5 lebih buruk).
  Batas ini sama dengan bottleneck 2 D-156 dan hasil D-148/D-149.
- Per komoditas (`cal_by_commodity.csv`, h 8): beras rerata p 0,17 vs laju 0,29 (terlalu rendah rata-rata, terlalu tinggi di ekor), minyak goreng
  0,17 vs 0,26, bawang putih 0,09 vs 0,03 (19 baris p ≥ 0,6, semuanya negatif). Kalibrasi per komoditas tidak menolong karena galatnya bergantung
  pada origin, bukan tetap per komoditas.

## 5. Penyebab yang diperiksa (protokol §3)

| # | Penyebab | Bukti | Peran |
|---|---|---|---|
| 1 | Pergeseran laju antarperiode | dev 0,12–0,13 → test 0,09; rerata p test 0,107 / 0,113 | Utama untuk kalibrasi-dalam-besaran (test) |
| 2 | Distribusi komoditas | ekor h 8 = beras, minyak goreng, telur; bawang putih selalu negatif | Penting; C3 tidak memperbaiki |
| 3 | Distribusi origin | 57 baris ekor dari 5 origin, 41 dari 2 | **Utama untuk ekor atas** |
| 4 | Rezim harga | momentum naik → ekor 35% positif; minyak goreng 2022 = intervensi kebijakan | Utama, tidak teramati dari harga |
| 5 | Ekor atas tidak stabil | kemiringan h 8 0,66 (terlalu menyebar) vs h 4 0,86 | Ya |
| 6 | Sampel kalibrator | ekor < 10 origin; per komoditas < 30 positif lampau di awal | Membatasi C2, C3 |
| 7 | Kesesuaian walk-forward | jendela pendek (C5) lebih buruk dari global (C1); oracle jauh lebih baik | Laju berikutnya tidak dapat diprediksi dari laju lampau |

FINDINGS:
- Peluang mentah K4-E80 adalah peluang terbaik yang diuji. Tidak ada kalibrator walk-forward yang menurunkan Brier.
- Masalah ekor h 8 berasal dari sedikit origin dengan pemutusan rezim (kebijakan) dan salah alokasi komoditas, bukan dari bentuk global
  peluang. Karena itu Platt atau isotonik tidak dapat memperbaikinya.
- Batas atas perbaikan (oracle laju per origin) nyata tetapi butuh informasi ex-ante tentang rezim atau kebijakan yang tidak ada di histori harga.

EVIDENCE: `hasil/cal_*.csv`; D-164 `k4_reliability.csv`, `k4_test_reliability.csv`.

STATISTICAL VALIDITY: Interval bootstrap blok origin (1.999 replikasi). Diagnosis ekor bertumpu pada 5–8 origin, jadi deskriptif. Tidak ada
yang dapat digeneralisasi ke rezim mendatang tanpa validasi prospektif. Kemiringan kalibrasi adalah ringkasan ex-post.

BUSINESS IMPLICATION: Angka peluang h 8 tidak boleh ditampilkan sebagai angka, termasuk sesudah kalibrasi. Peluang h 4 boleh ditampilkan
sebagai rentang kasar (rendah / sedang / tinggi), bukan persen presisi, sampai validasi prospektif selesai. Peluang ≥ 0,6 perlu catatan
"pada komoditas diatur, momentum bisa terputus oleh kebijakan".

DECISION: **Tolak** semua kalibrator C1–C6 sebagai pengganti peluang mentah. **Pertahankan** C0 (h 4 saja) sebagai peluang eksploratif.
**Revisi** rekomendasi D-164 #5a: "kalibrasi ekor h 8 per kelompok komoditas" tidak didukung. Yang dibutuhkan adalah informasi rezim ex-ante.

BLOCKERS: Informasi kebijakan bertanggal dan pasokan (U112) belum tersedia. U109: apakah TPID butuh angka peluang (V6) belum diketahui.

NEXT ACTION: (1) Bila V6 = cukup urutan, kalibrasi bukan syarat. (2) Bila angka dibutuhkan, kartu baru hanya dengan informasi rezim ex-ante
(tanggal kebijakan HET/HAP sebelum origin), dinilai oracle-dulu (EKSPERIMEN §3). (3) Nilai reliabilitas pada prediksi maju beku saat target
lengkap.
