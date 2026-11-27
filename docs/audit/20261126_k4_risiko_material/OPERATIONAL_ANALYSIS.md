# K4 — Analisis operasional, utilitas, dan galat (EKSPLORATIF, D-164)

Tanggal: 2026-11-26. `scripts/k4_eval.py` → `hasil/k4_ops_*.csv`, `k4_utility_*.csv`, `k4_errors.csv`, `k4_per_*.csv` (dev; test
berawalan `k4_test_`). Semua angka memakai materialitas statistik (P80 |y|, titik akhir). Kapasitas K dan rasio biaya **tidak dipilih**:
keduanya keputusan pengguna (U109). Angka di bawah adalah peta pertukaran, bukan rekomendasi operasional.

## 1. Kebijakan kapasitas tetap K per provinsi (dev, 34 provinsi × 38 / 37 origin)

| h | Skor | K | Alarm / origin | Benar / origin | Palsu / origin | Terlewat / origin | Presisi | Recall | Porsi alarm komoditas diatur | Alarm berulang dari origin sebelumnya |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | **K4-E80** | 1 | 34 | 11,4 | 22,6 | 29,0 | **0,334** | 0,281 | 0,66 | 0,40 |
| 4 | **K4-E80** | 2 | 68 | 19,9 | 48,1 | 20,5 | **0,293** | 0,493 | 0,58 | 0,51 |
| 4 | **K4-E80** | 3 | 102 | 25,4 | 76,6 | 15,0 | **0,249** | 0,629 | 0,54 | 0,57 |
| 4 | B-C1t | 2 | 68 | 16,9 | 51,1 | 23,5 | 0,249 | 0,419 | 0,46 | 0,41 |
| 4 | B-CLIM | 2 | 68 | 12,9 | 55,1 | 27,4 | 0,190 | 0,320 | 0,92 | 0,97 |
| 4 | B-CLIMS | 2 | 68 | 6,8 | 61,2 | 33,6 | 0,101 | 0,169 | 0,35 | 0,40 |
| 8 | **K4-E80** | 1 | 34 | 10,7 | 23,3 | 33,9 | **0,314** | 0,239 | 0,61 | 0,42 |
| 8 | **K4-E80** | 2 | 68 | 18,5 | 49,5 | 26,2 | **0,272** | 0,414 | 0,56 | 0,51 |
| 8 | **K4-E80** | 3 | 102 | 25,6 | 76,4 | 19,0 | **0,252** | 0,575 | 0,54 | 0,59 |
| 8 | B-C1t | 2 | 68 | 15,1 | 52,9 | 29,6 | 0,221 | 0,337 | 0,40 | 0,43 |
| 8 | B-CLIM | 2 | 68 | 16,8 | 51,2 | 27,8 | 0,248 | 0,377 | 0,93 | 0,97 |
| 8 | B-CLIMS | 2 | 68 | 11,5 | 56,5 | 33,1 | 0,169 | 0,258 | 0,38 | 0,44 |

- Pada setiap K dan kedua horizon, K4-E80 punya presisi & recall tertinggi. Pada K = 2, K4 menangkap ± 3 kenaikan material lebih banyak per
  minggu daripada C1-tuned (19,9 vs 16,9; 18,5 vs 15,1) dengan jumlah alarm sama.
- **B-CLIM adalah pembanding yang sulit di h 8**: presisi 0,248 di atas C1-tuned (0,221), tetapi hampir selalu menandai komoditas yang sama
  (93% alarm pada komoditas diatur, 97% alarm berulang tiap minggu; hanya 5 komoditas pernah ditandai). Daftar seperti itu tidak memberi
  informasi baru dari minggu ke minggu. K4 mendekati presisi itu dengan daftar yang berganti (51% berulang) dan mencakup 10 komoditas.
- Menambah musim (B-CLIMS) justru memperburuk: laju historis per bulan tidak bertahan (DU B3: laju bergeser antartahun).

## 2. Kebijakan ambang peluang τ (himpunan peluang dev; alarm bila p ≥ τ)

| h | Skor | τ | Alarm / origin (sd) | Presisi | Recall | Provinsi tanpa alarm / origin | Origin tanpa alarm |
|---|---|---|---|---|---|---|---|
| 4 | K4-E80 | 0,2 | 55,7 (37,6) | 0,361 | 0,467 | 8,5 | 0 / 32 |
| 4 | K4-E80 | 0,3 | 29,9 (28,8) | 0,412 | 0,286 | 16,0 | 5 / 32 |
| 4 | K4-E80 | 0,4 | 16,3 (20,8) | 0,465 | 0,176 | 22,0 | 7 / 32 |
| 4 | B-C1t-cal | 0,3 | 16,1 (26,6) | 0,340 | 0,127 | 25,1 | 14 / 32 |
| 8 | K4-E80 | 0,2 | 53,6 (36,9) | 0,358 | 0,401 | 10,1 | 0 / 30 |
| 8 | K4-E80 | 0,3 | 30,5 (26,9) | 0,413 | 0,263 | 15,5 | 4 / 30 |
| 8 | K4-E80 | 0,4 | 18,5 (21,4) | 0,449 | 0,173 | 20,8 | 7 / 30 |
| 8 | B-C1t-cal | 0,3 | 13,7 (22,7) | 0,309 | 0,088 | 25,3 | 12 / 30 |

- Dengan ambang peluang, jumlah alarm **berubah mengikuti risiko** (sd antarorigin ± 20–38 alarm): minggu tenang hampir tanpa alarm, minggu
  berisiko banyak alarm. Presisi naik ke 0,41–0,47 pada τ 0,3–0,4, tetapi 15–22 provinsi per minggu tidak mendapat alarm.
- Kapasitas tetap (K) menjamin setiap provinsi punya daftar, tetapi memaksa alarm di minggu tenang (presisi turun ke ± 0,11 pada origin
  berlaju rendah, §4). Pilihan antara keduanya adalah keputusan pengguna (V4–V6).

## 3. Utilitas: skenario biaya dan kurva keputusan (dev)

Biaya per origin = alarm palsu + r × kenaikan terlewat (satuan = biaya satu alarm palsu; **skenario, bukan biaya nyata**).

| h | Kebijakan | r = 1 | r = 2 | r = 5 | r = 10 |
|---|---|---|---|---|---|
| 4 | tanpa alarm | **40,4** | 80,8 | 202,0 | 403,9 |
| 4 | K4-E80 K = 1 / 2 / 3 | 51,7 / 68,6 / 91,6 | **80,7** / 89,0 / 106,6 | 167,8 / **150,4** / 151,6 | 312,9 / 252,8 / **226,6** |
| 4 | B-C1t K = 1 / 2 / 3 | 56,3 / 74,6 / 97,2 | 87,7 / 98,0 / 115,0 | 181,8 / 168,4 / 168,3 | 338,7 / 285,8 / 257,3 |
| 4 | K4-E80-cal τ = 1/(1+r) | 42,2 | 79,7 | 149,6 | 215,4 |
| 4 | B-C1t-cal τ = 1/(1+r) | 43,2 | 85,2 | 169,8 | 248,9 |
| 8 | tanpa alarm | **44,6** | 89,2 | 223,1 | 446,2 |
| 8 | K4-E80 K = 1 / 2 / 3 | 57,3 / 75,7 / 95,3 | 91,2 / 101,9 / 114,3 | 193,1 / 180,4 / **171,2** | 362,8 / 311,2 / **266,1** |
| 8 | B-C1t K = 1 / 2 / 3 | 62,9 / 82,5 / 102,7 | 99,6 / 112,1 / 125,4 | 209,9 / 200,8 / 193,4 | 393,7 / 348,6 / 306,8 |
| 8 | K4-E80-cal τ = 1/(1+r) | 49,5 | **89,3** | 183,3 | 239,7 |

(himpunan τ = origin dengan kalibrator; angka "tanpa alarm" dan K dihitung pada semua origin dev, jadi hanya urutan dalam satu baris yang
sebanding persis.)

- **Bila kenaikan terlewat tidak lebih mahal dari alarm palsu (r ≤ 2), daftar pantau apa pun tidak lebih baik dari tidak memantau**: presisi
  < 0,5 berarti setiap alarm rata-rata lebih banyak salah daripada benar. Nilai daftar muncul bila kenaikan terlewat ≥ ± 3× lebih mahal.
- Untuk r ≥ 5, K4 memberi biaya terendah di setiap K, dan kebijakan τ = 1/(1+r) pada peluang K4 terkalibrasi menyamai atau mengalahkan K tetap.
- Kurva keputusan (net benefit, `k4_utility_netbenefit.csv`): K4 (mentah/terkalibrasi) di atas B-C1t-cal, laju-dasar, dan "pantau semua" pada
  τ 0,10–0,40 di kedua horizon (mis. h 4 τ 0,2: 0,033 vs 0,023 vs 0); di h 8 τ ≥ 0,45 net benefit K4 ≈ 0 atau negatif (ekor atas terlalu yakin).

## 4. Analisis galat (dev, kebijakan K = 2)

| | h 4 K4-E80 | h 4 B-C1t | h 8 K4-E80 | h 8 B-C1t |
|---|---|---|---|---|
| Alarm palsu (total) | 1.827 | 1.941 | 1.833 | 1.959 |
| — harga turun | 34% | 30% | 37% | 34% |
| — harga tetap (y = 0) | 16% | 15% | 10% | 8% |
| — naik tetapi di bawah ambang | 50% | 56% | 53% | 58% |
| — nyaris (≥ ½ ambang) | 21% | 21% | 20% | 21% |
| — komoditas diatur | 51% | 39% | 48% | 33% |
| Kenaikan terlewat (total) | 778 | 892 | 968 | 1.094 |
| — komoditas diatur | 45% | 56% | 56% | 65% |
| — harga datar 4 minggu sebelumnya | 13% | 12% | 17% | 16% |
| — peringkat ≥ 6 dari 10 di provinsinya | 36% | 42% | 36% | 41% |

| Laju z origin (tersil) | Laju rerata | Presisi K4 h 4 | Presisi C1t h 4 | Presisi K4 h 8 | Presisi C1t h 8 |
|---|---|---|---|---|---|
| rendah | 0,05 | 0,116 | 0,108 | 0,112 | 0,086 |
| sedang | 0,11 | 0,319 | 0,259 | 0,270 | 0,158 |
| tinggi | 0,20–0,23 | 0,446 | 0,381 | 0,421 | 0,405 |

- Separuh alarm palsu adalah kenaikan yang **nyata tetapi belum mencapai ambang**; sepertiga adalah penurunan. Alarm palsu "harga tetap" naik
  sedikit di K4 (komoditas diatur yang tidak bergerak).
- Kenaikan terlewat yang tetap sulit: 13–17% muncul dari harga yang datar 4 minggu sebelumnya (lonjakan tanpa tanda awal), ± 36% berada di
  peringkat bawah (≥ 6 dari 10) → tidak tertangkap oleh K kecil apa pun.
- **Presisi ditentukan waktu**: origin berlaju rendah (± 5%) memberi presisi ± 0,11 untuk semua skor; laju tinggi 0,40–0,45. Rerata peluang K4 hanya bergerak
  0,08 → 0,12–0,14 antartersil, sedangkan laju terealisasi 0,05 → 0,20–0,23 → model **hanya sebagian mengetahui sebelumnya** minggu mana yang berisiko tinggi
  secara nasional (sama dengan bottleneck 2 D-156: pergeseran base rate per origin).
- Antarprovinsi: presisi K4 K = 2 0,21–0,37 (h 4), ≥ C1-tuned di 29 / 34 (h 4) dan 32 / 34 provinsi (h 8). Antarorigin: K4 ≥ C1-tuned
  di 79% / 73% origin.
- Per komoditas (AP dalam komoditas): K4 lebih baik untuk ayam (0,24 vs 0,17; 0,29 vs 0,20), daging sapi, cabai rawit h 4, telur h 4; C1-tuned lebih
  baik untuk cabai merah dan gula h 8. Bawang putih & bawang merah h 8 tidak dapat diurutkan oleh skor mana pun (AP ≈ laju-dasar 0,02–0,06).

## 5. Sebaran alarm per komoditas (K = 2, porsi alarm; dev)

| Komoditas | h 4 K4 | h 4 C1t | h 4 CLIM | h 8 K4 | h 8 C1t | h 8 CLIM |
|---|---|---|---|---|---|---|
| beras | 0,16 | 0,12 | 0,04 | 0,15 | 0,08 | 0,11 |
| minyak goreng | 0,17 | 0,12 | 0,38 | 0,19 | 0,08 | 0,32 |
| daging sapi | 0,14 | 0,06 | 0,50 | 0,14 | 0,06 | 0,50 |
| gula pasir | 0,11 | 0,15 | 0,00 | 0,08 | 0,18 | 0,00 |
| telur ayam | 0,07 | 0,07 | 0,08 | 0,06 | 0,08 | 0,07 |
| cabai merah / rawit | 0,09 / 0,07 | 0,10 / 0,08 | – | 0,09 / 0,07 | 0,12 / 0,10 | – |
| bawang merah / putih | 0,08 / 0,06 | 0,12 / 0,09 | – | 0,07 / 0,09 | 0,12 / 0,09 | – |
| daging ayam | 0,06 | 0,09 | – | 0,06 | 0,10 | – |

K4 memusatkan 58% / 56% alarm pada komoditas diatur (C1-tuned 46% / 40%): sebagian keunggulan presisinya berasal dari komposisi target P80 |y|
(DU B1). Kepekaan K4-S90 (komposisi seimbang) menguji apakah keunggulan bertahan tanpa efek itu: [RESULTS.md](RESULTS.md) §6.

## 6. Test 2024+ (evaluasi eksploratif, dibuka sekali; `hasil/k4_test_ops_*.csv`, `k4_test_utility_*.csv`, `k4_test_errors.csv`)

| h | Skor | K = 1 presisi / recall | K = 2 presisi / recall (benar / origin) | K = 3 presisi / recall | Porsi alarm diatur K = 2 | Berulang K = 2 |
|---|---|---|---|---|---|---|
| 4 | **K4-E80** | **0,252** / 0,288 | **0,202** / 0,460 (13,7) | **0,176** / 0,603 | 0,52 | 0,46 |
| 4 | B-C1t | 0,208 / 0,237 | 0,179 / 0,408 (12,2) | 0,158 / 0,542 | 0,58 | 0,46 |
| 4 | B-CLIM | 0,107 / 0,122 | 0,097 / 0,220 (6,6) | 0,107 / 0,367 | 1,00 | 0,99 |
| 8 | **K4-E80** | **0,191** / 0,216 | **0,174** / 0,392 (11,8) | **0,165** / 0,560 | 0,61 | 0,53 |
| 8 | B-C1t | 0,181 / 0,205 | 0,161 / 0,365 (11,0) | 0,147 / 0,498 | 0,56 | 0,51 |
| 8 | B-CLIM | 0,158 / 0,179 | 0,143 / 0,322 (9,7) | 0,115 / 0,390 | 1,00 | 0,92 |

- Di test, laju-dasar komoditas lemah di h 4 (0,097; komoditas diatur lebih jarang naik sesudah 2024) dan tetap kompetitif di h 8 (0,143 vs C1-tuned
  0,161). K4 tertinggi di setiap K dan horizon.
- Ambang peluang τ (test): K4 τ 0,3 → 19,6 / 27,2 alarm per minggu, presisi 0,32 / 0,24; C1-tuned terkalibrasi τ 0,3 → 11,7 / 12,1 alarm, presisi
  0,27 / 0,30. Presisi τ lebih rendah dari dev karena peluang K4 terlalu tinggi di test (laju turun).
- Biaya (test): r = 1–2 tanpa alarm termurah (29,8 / 59,6 per origin h 4); r = 5 K4 K = 1 termurah (131,5 vs C1-tuned 140,6 vs tanpa alarm 148,9); r = 10 K4
  K = 3 termurah (202,1 vs 222,4). Titik impas bergeser ke r lebih tinggi daripada dev karena laju lebih rendah.
- Galat test serupa dev: alarm palsu 53–58% kenaikan di bawah ambang, 29–34% penurunan; risiko terlewat 13–15% dari harga datar; origin berlaju rendah
  (± 3%) presisi 0,04–0,08 untuk semua skor.
