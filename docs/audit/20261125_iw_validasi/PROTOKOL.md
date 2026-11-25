# Protokol D-152 — validasi `IW_NAT`: kebocoran semua origin, diagnostik lintas provinsi, pembekuan prediksi maju (EKSPLORATIF)

Ditulis 2026-11-25 sebelum run apa pun di ronde ini; tidak diubah sesudahnya (sha256 di laporan). Lanjutan D-151.

## 0. Prinsip

- **Tidak ada kandidat baru di ronde ini.** `IW_NAT` (D-151) dibekukan apa adanya sebagai satu-satunya kandidat eksploratif; C1-tuned
  tetap model terpilih. Semua varian baru di §2 adalah **diagnostik**: dinilai di origin pengembangan saja, tidak membuka test, dan tidak
  dapat menggantikan `IW_NAT` (mencegah overfitting pengembangan yang makin berat sejak D-145).
- Test 2024+ tidak dibuka lagi untuk keluarga intraminggu.

## 1. Waktu ketersediaan (`available_at`) & kebocoran

Aturan eksplisit: fitur minggu t memakai hari teramati Senin–Jumat minggu t; PIHPS dapat direvisi s.d. H+1, jadi
`available_at(t) = t + 5 hari` (Sabtu 00:00, sesudah revisi H+1 harga Jumat). Prediksi untuk origin t dianggap dibuat pada
`available_at(t)`. Varian diagnostik "tanpa Jumat" memakai `available_at(t) = t + 4 hari` (Jumat 00:00 → hanya Senin–Kamis).
Fitur C1-tuned resmi (rerata minggu t) memakai hari yang sama; varian intraminggu tidak memperluas asumsi waktu, hanya memberi bobot
lebih ke hari terakhir.

Audit kebocoran fitur intraminggu (`iw_*`, nasional, LOO, keserentakan, tanpa Jumat) untuk **setiap** origin rolling Task 4
(h 4 & 8, pengembangan + test) dan setiap origin maju (§3): dengan cutoff = `available_at(origin)`,
(a) semua observasi harian sesudah cutoff dihapus; (b) harga harian sesudah cutoff dirusak (×exp(N(0; 0,5))); (c) 30% observasi
sesudah cutoff dihapus acak (pola kosong berubah); (d) hanya provinsi LAIN (bukan provinsi yang dinilai) yang dirusak sesudah cutoff
— untuk fitur nasional/LOO/keserentakan; (e) varian tanpa Jumat: harga Jumat minggu origin dirusak. Lolos = fitur semua minggu ≤ origin
identik (NaN sama). Revisi data sesudah cutoff tidak dapat diuji (vintage PIHPS tidak ada) → keterbatasan tercatat; hanya prediksi maju
(§3) yang memakai data sebagaimana tersedia saat itu.

## 2. Diagnostik pengembangan (origin + h ≤ 2023-12-31; tidak membuka test)

Pembanding: `base` (C1-tuned), `IW_FULL`, `IW_NAT` dari prediksi D-151 (deterministik, baris sama).

| Diagnostik | Kolom di atas C1-tuned | Pertanyaan |
|---|---|---|
| `IW_NAT_LOO` | `IW_FULL` + `iw_gap_nat_loo`, `iw_return_nat_loo` (rerata provinsi lain yang teramati minggu t) | Apakah keuntungan `IW_NAT` berasal dari provinsi lain, bukan dari provinsi sendiri di dalam rerata? |
| `IW_BREADTH` | `IW_NAT_LOO` + `iw_up_share_loo`, `iw_down_share_loo` (porsi provinsi lain dengan `iw_return` > 0 / < 0) | Apakah keserentakan arah antarprovinsi menambah di atas rerata? |
| `IW_NAT_NOFRI` | 8 kolom `IW_NAT` dihitung dari Senin–Kamis saja (`iw_last_age` = 3 − hari terakhir) | Seberapa besar keuntungan bergantung pada harga Jumat (hari paling rawan revisi)? |

Dilaporkan: Δ macro F1 vs `base` dan vs `IW_NAT` (interval bootstrap blok origin berpasangan 1.999), kuintil |y| terkecil, per
komoditas. Penafsiran yang ditetapkan sebelum run: `IW_NAT_LOO` − `IW_NAT` ≥ −0,005 di kedua horizon → keuntungan nasional dianggap
berasal dari provinsi lain; `IW_NAT_NOFRI` − `IW_NAT` ≥ −0,005 → tidak bergantung pada Jumat.

## 3. Pembekuan prediksi maju (forward validation)

- Model beku: `base` = C1-tuned (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed resmi, threshold 0,5) dan `IW_NAT` persis D-151
  (`iw_build.py` sha256 5be4fc7d…, `exp.py` 49bb90ea…, `p_exp.py` d98b4154…, `src/models/direction.py` 1f4e8512…,
  `src/features/price_dynamics.py` 40cb8ecd…, `src/features/forecast.py` 95cdb3c9…).
- Origin maju = semua minggu yang labelnya belum terealisasi pada snapshot sekarang (minggu data terakhir 2026-11-16):
  h 4: 2026-10-26, 11-02, 11-09, 11-16; h 8: 2026-09-28 .. 2026-11-16 (8 minggu). Latih t + h ≤ origin (sama dengan rolling Task 4).
  Origin ini tidak pernah dipakai untuk seleksi dan labelnya belum diketahui siapa pun di proyek.
- Prediksi (`p_up` per provinsi × komoditas × origin × h × model) disimpan sebelum target terealisasi dengan sha256 dicatat.
- Evaluasi (skrip dibekukan bersama prediksi): label = tanda Δ log rerata hari teramati minggu t+h − minggu t dari snapshot PIHPS baru
  (`select_variants` + `aggregate_weekly` resmi, y = 0 dikeluarkan); metrik macro F1, F1 naik/turun, MCC, ROC-AUC, macro F1 kuintil
  |y| terkecil; selisih berpasangan `IW_NAT` − `base`. Penilaian: dengan ≤ 8 origin mingguan, uji hanya bersifat deskriptif; daya
  dihitung di §4 dan keputusan "terkonfirmasi" hanya bila interval kumulatif origin maju (blok h minggu) tidak memuat nol.

## 4. Daya uji maju

Dari interval berpasangan test D-151 (37 / 36 origin berjarak 4 minggu) dihitung SE selisih per horizon, lalu MDE (α 0,05 dua sisi,
daya 0,80; MDE = 2,8·SE·√(n_test / n)) untuk n origin berjarak 4 minggu, dan jumlah origin yang dibutuhkan untuk mendeteksi selisih
titik D-151 (+0,0085 / +0,0033). Hasil ini menentukan apakah validasi maju realistis untuk mengonfirmasi `IW_NAT`.
