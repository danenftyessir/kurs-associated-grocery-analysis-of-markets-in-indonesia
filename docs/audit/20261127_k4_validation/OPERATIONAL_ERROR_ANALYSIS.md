# Validasi K4 — Analisis galat operasional

Tanggal 2026-11-27, catatan bertanggal. Skrip `scripts/v_errors.py`, keluaran `hasil/err_*.csv`. **Hanya dev** (38 / 37 origin, 34 provinsi).
Angka test dikutip dari file D-164 yang sudah terbit (`../20261126_k4_risiko_material/hasil/k4_test_*`). Semua angka memakai materialitas
statistik (P80 |y|, titik akhir). K dan τ tidak dipilih di sini.

STATUS: **COMPLETE** (deskriptif)

OBJECTIVE: Memahami alarm palsu dan kenaikan yang terlewat. Pertanyaan utamanya: apakah kesalahan itu acak, soal waktu, soal komoditas, atau
soal rezim, dan apa artinya bagi kapasitas pemantauan.

## 1. Kapasitas: presisi@K (`err_policies.csv`)

| h | Skor | K | Alarm / minggu | Presisi | Recall | Benar / minggu | Lift vs laju | Alarm berulang | Komoditas per minggu (pernah) |
|---|---|---|---|---|---|---|---|---|---|
| 4 | **K4-E80** | 1 | 34 | **0,334** | 0,281 | 11,4 | 2,8× | 0,40 | 4,1 (10) |
| 4 | **K4-E80** | 2 | 68 | **0,293** | 0,493 | 19,9 | 2,4× | 0,51 | 6,3 (10) |
| 4 | **K4-E80** | 3 | 102 | **0,249** | 0,629 | 25,4 | 2,1× | 0,57 | 7,8 (10) |
| 4 | **K4-E80** | 5 | 170 | **0,195** | 0,820 | 33,1 | 1,6× | 0,69 | 9,2 (10) |
| 4 | C1-tuned | 2 / 5 | 68 / 170 | 0,249 / 0,180 | 0,419 / 0,756 | 16,9 / 30,5 | 2,1× / 1,5× | 0,41 / 0,66 | 6,1 / 8,9 (10) |
| 4 | laju-dasar | 2 / 5 | 68 / 170 | 0,190 / 0,151 | 0,321 / 0,635 | 12,9 / 25,6 | 1,6× / 1,3× | 0,97 / 0,96 | 2,1 / 5,2 (5 / 8) |
| 8 | **K4-E80** | 1 | 34 | **0,314** | 0,239 | 10,7 | 2,4× | 0,42 | 4,5 (10) |
| 8 | **K4-E80** | 2 | 68 | **0,271** | 0,414 | 18,5 | 2,0× | 0,51 | 6,6 (10) |
| 8 | **K4-E80** | 3 | 102 | **0,251** | 0,575 | 25,6 | 1,9× | 0,59 | 8,1 (10) |
| 8 | **K4-E80** | 5 | 170 | **0,207** | 0,787 | 35,1 | 1,6× | 0,71 | 9,5 (10) |
| 8 | C1-tuned | 2 / 5 | 68 / 170 | 0,221 / 0,191 | 0,337 / 0,726 | 15,1 / 32,4 | 1,7× / 1,4× | 0,43 / 0,69 | 7,0 / 9,5 (10) |
| 8 | laju-dasar | 2 / 5 | 68 / 170 | 0,248 / 0,172 | 0,377 / 0,655 | 16,8 / 29,2 | 1,9× / 1,3× | 0,97 / 0,95 | 2,1 / 5,2 (5 / 8) |

Test (terbit): presisi K4 K1 / K2 / K3 0,252 / 0,202 / 0,176 (h 4) dan 0,191 / 0,174 / 0,165 (h 8). Laju test 0,088 / 0,089 sehingga presisi
lebih rendah dari dev di setiap K.

- Presisi turun pelan sementara recall naik cepat: K = 1 → 5 memotong presisi K4 dari 0,33 ke 0,20, tetapi recall naik dari 0,28 ke 0,82.
- Daftar laju-dasar hampir statis: 95–97% alarm berulang setiap minggu, hanya 2 komoditas per minggu. Presisinya di h 8 (0,248) mendekati K4
  karena selalu menandai daging sapi dan minyak goreng. Daftar seperti itu tidak memberi informasi minggu ke minggu.

## 2. Alarm palsu (K = 2; `err_false_alarms.csv`)

| Kategori | h 4 K4 | h 4 C1t | h 8 K4 | h 8 C1t | Pembanding: seri tanpa alarm yang negatif (h 4 / h 8, K4) |
|---|---|---|---|---|---|
| Jumlah alarm palsu | 1.827 | 1.941 | 1.833 | 1.959 | – |
| Naik tetapi di bawah ambang | 50% | 56% | 53% | 58% | – |
| Harga turun | 34% | 30% | 37% | 34% | – |
| Harga tetap | 16% | 15% | 10% | 8% | – |
| Nyaris: ≥ ½ ambang | 21% | 21% | 20% | 21% | 10% / 12% |
| Nyaris: ≥ ¾ ambang | 10% | 9% | 8% | 9% | – |
| Lonjakan di tengah jendela lalu berbalik | 4,3% | 3,3% | 6,7% | 5,3% | 1,4% / 3,5% |
| Kenaikan material sesudah titik akhir (≤ 4 minggu) | **25%** | 24% | **17%** | 15% | 12% / 8% |
| Dijelaskan waktu (berbalik atau terlambat) | 28% | 26% | 21% | 18% | – |
| Komoditas diatur | 51% | 39% | 48% | 33% | – |
| Pada origin berlaju rendah (tersil bawah) | 43% | 41% | 40% | 38% | – |

- **Waktu kejadian menjelaskan sebagian alarm palsu.** Seperempat alarm palsu h 4 diikuti kenaikan material dalam 4 minggu sesudah titik akhir.
  Pada seri tanpa alarm, laju itu 12%, jadi kira-kira separuhnya adalah sinyal yang datang terlambat. Bila TPID menilai kenaikan dalam jendela
  yang lebih panjang (V3), sebagian alarm ini benar.
- Lonjakan yang berbalik sebelum titik akhir jarang (4–7% alarm palsu). Target kejadian dalam jendela (K4-A80) hanya akan "menyelamatkan" sedikit
  alarm. Ini sesuai dengan D-164: ΔAP K4-A80 − K4-E80 di dev ≈ 0.
- Separuh alarm palsu adalah kenaikan nyata di bawah ambang P80. Klasifikasinya sebagai "palsu" bergantung penuh pada ambang statistik. Dengan
  ambang kebijakan lain, porsi ini akan berubah (§5 TARGET_SENSITIVITY_REPORT).
- 43% alarm palsu h 4 terjadi pada sepertiga origin berlaju rendah (laju terealisasi ± 5%).

## 3. Kenaikan terlewat (K = 2; `err_missed.csv`)

| Kategori | h 4 K4 | h 4 C1t | h 8 K4 | h 8 C1t |
|---|---|---|---|---|
| Jumlah | 778 | 892 | 968 | 1.094 |
| Peringkat 3–4 dalam provinsi (tepat di bawah K) | **50%** | 43% | **49%** | 42% |
| Peringkat ≥ 6 dari 10 | 36% | 42% | 36% | 41% |
| Harga datar 4 minggu sebelumnya | 13% | 12% | 17% | 16% |
| Komoditas diatur | 45% | 56% | 56% | 65% |
| Pada origin berlaju tinggi | 63% | 61% | 65% | 59% |

- Separuh kenaikan terlewat hampir masuk daftar. K = 3 menangkap sebagian besar di antaranya (recall 0,49 → 0,63 h 4) dengan presisi 0,25.
- Sepertiga tidak terlihat sama sekali (peringkat ≥ 6). 13–17% berasal dari harga yang datar 4 minggu sebelumnya, yaitu lonjakan tanpa tanda awal
  dalam histori harga.
- Kenaikan terlewat menumpuk di minggu berlaju tinggi (63–65%), ketika banyak komoditas di satu provinsi naik bersamaan dan K tetap tidak cukup.

## 4. Rezim (`err_by_regime.csv`, K = 2)

| Pembagian origin | Tersil | Laju | Presisi K4 h 4 / h 8 | Presisi C1t h 4 / h 8 | Presisi laju-dasar h 4 / h 8 |
|---|---|---|---|---|---|
| Laju terealisasi (ex-post) | rendah | 0,05 | 0,117 / 0,112 | 0,107 / 0,086 | 0,053 / 0,094 |
| | sedang | 0,11 | 0,319 / 0,270 | 0,259 / 0,158 | 0,183 / 0,188 |
| | tinggi | 0,20–0,23 | 0,446 / 0,421 | 0,381 / 0,405 | 0,335 / **0,445** |
| Momentum nasional ex-ante | turun | 0,12–0,13 | 0,302 / 0,295 | 0,277 / 0,234 | 0,171 / 0,234 |
| | datar | 0,10–0,12 | 0,235 / 0,213 | 0,200 / 0,194 | 0,137 / 0,230 |
| | naik | 0,14 | 0,337 / 0,303 | 0,266 / 0,235 | 0,259 / 0,276 |

- Presisi ditentukan waktu: dari ± 0,11 di minggu tenang ke 0,42–0,45 di minggu berisiko, untuk semua skor. Rezim ex-ante (momentum nasional)
  hanya sedikit membedakan (0,21–0,34). Pengguna tidak dapat tahu sebelumnya minggu mana yang presisinya tinggi.
- K4 ≥ C1-tuned di semua tersil. Di h 8 pada minggu berlaju tinggi, laju-dasar setara K4 (0,445 vs 0,421), karena komoditas diatur naik bersama.

## 5. Komoditas dan provinsi (`err_commodity_coverage.csv`, `err_province_spread.csv`)

| Komoditas (K = 2, K4) | Porsi alarm h 4 / h 8 | Presisi h 4 / h 8 | Recall h 4 / h 8 | Porsi positif h 4 / h 8 |
|---|---|---|---|---|
| minyak goreng | 0,17 / 0,19 | 0,46 / 0,40 | 0,66 / 0,52 | 0,20 / 0,22 |
| beras | 0,16 / 0,15 | 0,37 / 0,45 | 0,61 / 0,56 | 0,17 / 0,19 |
| gula pasir | 0,11 / 0,08 | 0,39 / 0,23 | 0,69 / 0,31 | 0,10 / 0,09 |
| daging sapi | 0,14 / 0,14 | 0,27 / 0,30 | 0,49 / 0,46 | 0,13 / 0,13 |
| cabai rawit | 0,07 / 0,07 | 0,28 / 0,25 | 0,37 / 0,31 | 0,09 / 0,08 |
| telur ayam | 0,07 / 0,06 | 0,21 / 0,36 | 0,28 / 0,48 | 0,08 / 0,07 |
| daging ayam | 0,06 / 0,06 | 0,21 / 0,20 | 0,43 / 0,44 | 0,05 / 0,04 |
| cabai merah | 0,09 / 0,09 | 0,18 / 0,15 | 0,27 / 0,21 | 0,09 / 0,10 |
| bawang merah | 0,08 / 0,07 | 0,15 / **0,03** | 0,30 / 0,06 | 0,06 / 0,05 |
| **bawang putih** | 0,06 / 0,09 | **0,03 / 0,01** | 0,15 / 0,10 | 0,02 / 0,02 |

- Bawang putih dan bawang merah memakai 14% (h 4) / 17% (h 8) alarm dengan presisi 0,01–0,15. Di h 8 hampir semua alarm keduanya salah.
  Ini kandidat aturan tampilan ("tanpa skor yang dapat dipercaya"), bukan aturan seleksi. Pengecualian komoditas harus diuji prospektif
  karena dipilih dari dev ini.
- Cabai merah dan rawit: ambang P80 sangat tinggi (37–71%), presisi 0,15–0,28. Kenaikan cabai yang besar justru sering terlewat
  ([CALIBRATION_DEEP_AUDIT.md](CALIBRATION_DEEP_AUDIT.md) §3, origin 2023-10-09).
- Sebaran antarprovinsi (daftar nasional setara-V2, 68 alarm per minggu tanpa kuota provinsi): K4 presisi 0,305 / 0,286. Rata-rata 1,5 / 1,9
  provinsi per minggu tanpa alarm, maksimum ± 4 alarm untuk satu provinsi. Gini alarm antarprovinsi 0,14. Korelasi jumlah alarm dengan jumlah
  positif per provinsi 0,68 / 0,63, jadi K4 menaruh lebih banyak alarm di provinsi yang lebih sering naik. C1-tuned: korelasi 0,13 / 0,40.
  Kuota tetap per provinsi (V1-K) dan daftar nasional berbeda. Mana yang dipakai adalah keputusan tata kelola TPID (pusat vs daerah).

FINDINGS:
- Alarm palsu bukan derau murni. Separuh adalah kenaikan di bawah ambang statistik, seperempat (h 4) adalah kenaikan yang datang sesudah titik
  akhir. Kenaikan terlewat sebagian besar hanya sedikit di bawah batas K.
- Kesalahan menumpuk pada waktu (minggu berlaju rendah untuk alarm palsu, berlaju tinggi untuk yang terlewat) dan pada dua komoditas bawang.
- Pada setiap K dan rezim, K4 ≥ C1-tuned. Laju-dasar kompetitif hanya di h 8 dan hanya karena daftar statis.

EVIDENCE: `hasil/err_*.csv`; D-164 `k4_ops_policies.csv`, `k4_test_ops_policies.csv`, `k4_errors.csv`.

STATISTICAL VALIDITY: Deskriptif pada dev, tanpa interval per kategori. Kategori "terlambat" memakai 4 minggu sesudah titik akhir (dibatasi ≤
2023-12-31). Porsi pembanding dari seri tanpa alarm membedakan sinyal dari laju alami. Temuan bawang putih/merah dipilih dari data yang sama
sehingga perlu konfirmasi prospektif.

BUSINESS IMPLICATION: 7–8 dari 10 alarm tidak berujung kenaikan material pada titik akhir. Daftar ini hanya cocok sebagai **prioritas pemantauan
yang ditinjau manusia**, bukan pemicu tindakan. Nilainya naik bila TPID menghitung kenaikan dalam jendela yang lebih panjang (V3) atau dapat
menangani K = 3 (V4).

DECISION: **Pertahankan** K4-E80 sebagai skor ranking eksploratif. Tidak ada K atau τ yang dipilih. Pengecualian komoditas bawang **ditunda**
sampai prospektif.

BLOCKERS: U109 (V3 jendela, V4 kapasitas, V5 biaya relatif).

NEXT ACTION: Tampilkan konteks waktu dan alasan alarm di kartu ([OPERATIONAL_SPECIFICATION.md](OPERATIONAL_SPECIFICATION.md)). Uji aturan
tampilan bawang pada prediksi maju.
