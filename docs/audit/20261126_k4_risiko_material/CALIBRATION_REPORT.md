# K4 — Laporan kalibrasi peluang risiko kenaikan material (EKSPLORATIF, D-164)

Tanggal: 2026-11-26. `scripts/k4_eval.py` → `hasil/k4_probability.csv`, `k4_reliability.csv`, `k4_paired.csv` (dev);
`k4_test_*` (test). Aturan R2 di [PROTOCOL.md](PROTOCOL.md) §5.

## 1. Apa yang dikalibrasi

Target z = kenaikan material titik akhir (P80 |y|). Peluang dinilai pada **himpunan peluang**: origin dev yang punya kalibrator walk-forward
(≥ 6 origin lampau yang targetnya terealisasi): 32 / 30 origin, 10.778 / 10.104 baris (h 4 / h 8), semua skor pada baris identik.

| Skor | Asal peluang |
|---|---|
| K4-E80 | HGB dilatih langsung pada z (semua baris latih, termasuk y = 0) |
| K4-E80-cal | K4-E80 + Platt global walk-forward (a + b·logit p) |
| B-C1t-cal | p_up C1-tuned + Platt global walk-forward → z (cara "tidak langsung" yang adil) |
| B-CLIM / B-CLIMS | porsi z komoditas (× bulan origin) di baris latih |
| p_up C1-tuned mentah | **bukan peluang z**; dilaporkan hanya untuk menunjukkan salah tafsirnya (registri) |

## 2. Hasil dev

| h | Skor | Brier | Log loss | ECE | Brier skill vs B-CLIM (interval) |
|---|---|---|---|---|---|
| 4 | K4-E80 | **0,0979** | **0,328** | 0,023 | **0,116 (0,052..0,170)** |
| 4 | K4-E80-cal | 0,0985 | 0,331 | **0,014** | 0,111 (0,055..0,159) |
| 4 | B-C1t-cal | 0,1042 | 0,354 | 0,014 | 0,060 (0,015..0,099) |
| 4 | B-CLIM | 0,1108 | 0,379 | 0,018 | 0 |
| 4 | B-CLIMS | 0,1171 | 0,411 | 0,067 | −0,057 (−0,084..−0,020) |
| 8 | K4-E80 | **0,1132** | 0,379 | 0,044 | 0,068 (−0,031..0,153) |
| 8 | K4-E80-cal | 0,1136 | **0,374** | 0,019 | 0,065 (−0,020..0,128) |
| 8 | B-C1t-cal | 0,1165 | 0,387 | **0,010** | 0,041 (−0,025..0,085) |
| 8 | B-CLIM | 0,1214 | 0,407 | 0,027 | 0 |
| 8 | B-CLIMS | 0,1274 | 0,453 | 0,081 | −0,050 (−0,103..0,011) |

Perbandingan berpasangan (bootstrap blok origin, 1.999 replikasi):

| h | Pasangan | ΔBrier (interval) | q BH (keluarga F) |
|---|---|---|---|
| 4 | K4-E80 − B-C1t-cal | **−0,0063 (−0,0091..−0,0030)** | 0,002 |
| 4 | K4-E80-cal − B-C1t-cal | −0,0057 (−0,0082..−0,0029) | 0,002 |
| 8 | K4-E80 − B-C1t-cal | −0,0033 (−0,0124..+0,0060) | 0,447 |
| 8 | K4-E80-cal − B-C1t-cal | −0,0029 (−0,0094..+0,0042) | 0,391 |
| 4 / 8 | K4-E80 − B-CLIMS | −0,019 (−0,029..−0,009) / −0,014 (−0,023..−0,003) | – |

**R2 tidak lolos.** Di h 4 semua syarat terpenuhi (Brier lebih baik dengan interval < 0, ECE 0,023, Brier skill > 0 dengan interval > 0).
Di h 8 Brier tetap lebih rendah, tetapi intervalnya memuat 0, dan Brier skill terhadap laju-dasar komoditas memuat 0 (batas bawah
−0,031 mentah / −0,020 terkalibrasi). Kalibrasi Platt menurunkan ECE h 8 dari 0,044 ke 0,019 tanpa memperbaiki Brier.

## 3. Diagram reliabilitas (dev, `k4_reliability.csv`; rerata p → frekuensi teramati, n)

| Bin p | h 4 K4-E80 | h 4 K4-E80-cal | h 4 B-C1t-cal | h 8 K4-E80 | h 8 K4-E80-cal | h 8 B-C1t-cal |
|---|---|---|---|---|---|---|
| 0,0–0,1 | 0,044 → 0,059 (7.038) | 0,052 → 0,055 | 0,061 → 0,065 | 0,042 → 0,078 (6.701) | 0,059 → 0,068 | 0,065 → 0,069 |
| 0,1–0,2 | 0,141 → 0,165 | 0,140 → 0,154 | 0,143 → 0,128 | 0,141 → 0,190 | 0,141 → 0,160 | 0,144 → 0,161 |
| 0,2–0,3 | 0,243 → 0,301 | 0,243 → 0,297 | 0,243 → 0,294 | 0,241 → 0,286 | 0,240 → 0,233 | 0,240 → 0,242 |
| 0,3–0,4 | 0,346 → 0,348 | 0,346 → 0,321 | 0,335 → 0,339 | 0,347 → 0,357 | 0,343 → 0,372 | 0,336 → 0,294 |
| 0,4–0,5 | 0,447 → 0,369 | 0,449 → 0,381 | 0,431 → 0,359 (64) | 0,445 → 0,408 | 0,445 → 0,549 | 0,422 → 0,444 (36) |
| 0,5–0,6 | 0,546 → 0,507 (140) | 0,545 → 0,561 | – (5) | 0,550 → 0,516 (126) | 0,551 → 0,510 | – |
| 0,6–0,7 | 0,648 → 0,509 (108) | 0,647 → 0,475 | – | 0,643 → 0,465 (101) | 0,636 → 0,369 | – |
| 0,7–0,8 | 0,752 → 0,652 (46) | 0,737 → 0,357 (14) | – | 0,747 → 0,529 (87) | 0,744 → 0,226 (31) | – |
| 0,8–0,9 | 0,809 → 0,714 (7) | 0,826 → 0,846 (26) | – | **0,835 → 0,281 (57)** | 0,848 → 0,125 (16) | – |

Bacaan:
- **B-C1t-cal tidak dapat menyatakan risiko tinggi**: peluangnya hampir tidak pernah > 0,4 (69 / 37 baris). Skor arah, sekalipun dikalibrasi, hanya
  memisahkan risiko rendah dan sedang. Inilah alasan utama K4 unggul dalam presisi@K dan net benefit pada τ ≥ 0,2.
- **K4-E80 terlalu yakin di ekor atas h 8**: 57 baris dengan p 0,8–0,9 hanya 28% yang naik material. Platt global tidak memperbaikinya (memang
  tidak dapat memperbaiki bentuk lokal). Di ekor bawah K4 sedikit terlalu rendah (0,042 vs 0,078 di h 8).
- Penyebab yang konsisten dengan DU: laju z per origin bergeser ± 0,07–0,085 dari laju latih, dan origin dengan banyak peluang tinggi adalah
  origin yang lajunya tidak terjadi (lihat [OPERATIONAL_ANALYSIS.md](OPERATIONAL_ANALYSIS.md) §4).

## 4. p_up C1-tuned bukan peluang kenaikan material

Bila p_up mentah dibaca sebagai peluang z, Brier dan ECE jauh lebih buruk (lihat baris `B-C1t` di [EXPERIMENT_LOG.csv](EXPERIMENT_LOG.csv)):
rerata p_up ± 0,5 sedangkan laju z 0,13–0,14. Ini menegaskan koreksi D-155: angka p_up tidak boleh ditampilkan sebagai "peluang naik tajam".

## 5. Test 2024+ (evaluasi eksploratif, dibuka sekali)

Lihat [RESULTS.md](RESULTS.md) §5. Ringkasnya dicatat di sana karena R2 tidak lolos di dev, jadi tidak ada varian peluang yang dipilih; angka
peluang test bersifat deskriptif.

## 6. Kesimpulan kalibrasi

- Untuk h 4, peluang K4-E80 (mentah atau Platt) adalah peluang risiko kenaikan material terbaik yang diuji di dev: lebih baik dari skor arah
  terkalibrasi dan dari laju-dasar komoditas, dengan ECE ≤ 0,023.
- Untuk h 8, keunggulan tidak terbukti, dan peluang tinggi tidak dapat dipercaya (ekor atas terlalu yakin). Peluang h 8 tidak layak ditampilkan
  sebagai angka; paling jauh sebagai urutan.
- Kalibrasi walk-forward global (Platt) memperbaiki ECE, bukan Brier, sama dengan temuan D-163a untuk skor arah. Pergeseran laju-dasar antarorigin
  adalah batas kalibrasi dari histori harga saja.
