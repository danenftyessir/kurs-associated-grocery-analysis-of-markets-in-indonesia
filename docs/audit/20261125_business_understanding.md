# Business Understanding Task 4 Arah (CRISP-DM Fase 1): Nilai C1-tuned bagi TPID

Tanggal: 2026-11-25 · Pelaksana: Danen (dengan agent) · Keputusan: D-154 · Lanjutan [D-153](20261125_crisp_du.md) · Alur:
[`docs/EKSPERIMEN.md`](../EKSPERIMEN.md). Catatan bertanggal (bukan dokumen hidup). Skrip & hasil: [folder lampiran](20261125_business_understanding/).

Protokol [`PROTOKOL.md`](20261125_business_understanding/PROTOKOL.md) (tujuan bisnis, definisi kenaikan material, kriteria S1–S4, aturan
naif) ditulis 21.29 WIB sebelum pengukuran; sha256 `1c99f5c08ff10cb1818fa0b619fb54da5812bc5dfb5c1bfaa3f4a4ebf385861a`
(sama dengan hash saat ditulis). Tidak ada model baru; yang dinilai adalah C1-tuned beku dan empat aturan sederhana.

## 0. Ringkasan

D-153 menyimpulkan macro F1 C1-tuned (± 0,68) dekat batas informasi PIHPS. Fase Business Understanding mengajukan pertanyaan lain:
**apakah model ini berguna untuk keputusan TPID**, yaitu menentukan komoditas mana di provinsinya yang perlu disiapkan instrumennya 4–8
minggu ke depan, dibandingkan dengan membaca tren secara sederhana? Jawabannya: **ya**, dengan batas yang jelas.

| Kriteria (ditetapkan sebelum ukur) | Dev h 4 | Dev h 8 | Test h 4 (dibuka sekali) | Test h 8 |
|---|---|---|---|---|
| S1 daftar pantau provinsi: presisi kenaikan material − aturan naif terbaik (interval > 0) | **lolos** +0,110 (0,055..0,151) | **lolos** +0,067 (0,027..0,129) | **lolos** +0,094 (0,055..0,132) | **lolos** +0,072 (0,034..0,115) |
| S2 peluang terkalibrasi: Brier skill > 0 & ECE ≤ 0,05 | **lolos** 0,133 / 0,035 | gagal tipis: 0,160 / **0,056** | **lolos** 0,170 / 0,010 | **lolos** 0,167 / 0,021 |
| S3 arah saat bergerak material: macro F1 − aturan tanda tren | **lolos** 0,777 vs 0,541 | **lolos** 0,797 vs 0,502 | **lolos** 0,809 vs 0,496 | **lolos** 0,812 vs 0,443 |

Makna bagi TPID (test, evaluasi rolling-origin):
- Untuk setiap provinsi, 2 komoditas dengan peluang naik tertinggi menangkap **41% / 36%** kenaikan material (h 4 / h 8), dengan presisi
  **0,18 / 0,16**: dua kali laju-dasar 0,09. Aturan "ikuti tren 4 minggu" hanya 0,08–0,09, setara menebak.
- Saat harga bergerak material, arah yang ditunjuk model benar dengan macro F1 ± 0,81; aturan tren ± 0,44–0,50.
- Pada 25% prediksi paling yakin per minggu, akurasi arah 0,83 / 0,81 (seluruh baris 0,68).

## 1. Tujuan bisnis & pemahaman situasi (PROTOKOL §1)

- Pengguna: TPID provinsi (dan koordinasi nasional). Keputusan: menyiapkan operasi pasar/SPHP, kerja sama antardaerah, pemantauan stok,
  dan komunikasi untuk 10 komoditas strategis, 4–8 minggu sebelum kenaikan material.
- Pembanding: praktik tanpa model diasumsikan berupa membaca tren sendiri (`R_mom`), tren nasional (`R_nat`), posisi terhadap rata-rata
  13 minggu (`R_rev`), dan pola tahun lalu (`R_seas`). **Asumsi ini belum divalidasi dengan pengguna TPID** (langkah `[HUMAN]`).
- Kenaikan material = y_h ≥ persentil 80 |y_h| komoditas itu di baris latih (aturan `large_move_pct` 80, tanpa informasi masa depan).
  Ambang median (test): beras 1,6% / 2,6%, daging sapi 1,4% / 2,1%, minyak goreng 2,3% / 3,8%, gula 2,7% / 5,0%, telur 8,3% / 11,2%,
  bawang putih 10% / 16%, ayam 12% / 16%, bawang merah 23% / 37%, cabai merah 37% / 57%, cabai rawit 50% / 72% (h 4 / h 8). Jadi "material"
  berarti **tidak biasa untuk komoditas itu**, bukan ambang rupiah atau persen yang sama.

## 2. S1 — Daftar pantau (`hasil/bu_s1_*.csv`)

| Skor | V1 presisi dev h 4 / h 8 | V1 presisi test h 4 / h 8 | V1 recall test | V2 (10% nasional) presisi test |
|---|---|---|---|---|
| C1-tuned | 0,249 / 0,221 | **0,179 / 0,161** | 0,41 / 0,36 | 0,225 / 0,200 |
| `R_mom` tren sendiri | 0,139 / 0,143 | 0,085 / 0,079 | 0,19 / 0,18 | 0,064 / 0,063 |
| `R_nat` tren nasional | 0,136 / 0,155 | 0,091 / 0,089 | 0,21 / 0,20 | 0,108 / 0,108 |
| `R_rev` balik ke rata-rata | 0,111 / 0,119 | 0,113 / 0,121 | 0,26 / 0,27 | 0,135 / 0,146 |
| `R_seas` pola tahun lalu | 0,122 / 0,130 | 0,095 / 0,099 | 0,22 / 0,22 | 0,107 / 0,111 |
| laju-dasar | 0,120 / 0,132 | 0,088 / 0,089 | – | 0,088 / 0,089 |

- Pembanding resmi = aturan naif terbaik di dev (`R_mom` h 4, `R_nat` h 8). Di test, aturan terbaik ternyata `R_rev`. Terhadap `R_rev`,
  C1-tuned tetap unggul +0,066 / +0,040 (angka titik; perbandingan ini tidak ditetapkan sebelumnya, jadi tanpa interval resmi).
- V2 nasional h 8 vs `R_rev` +0,054 (−0,003..0,112): daftar pantau nasional yang besar kurang tegas dibandingkan daftar per provinsi.
- `IW_NAT` (acuan eksploratif, dev saja) hampir sama: V1 0,252 / 0,229.

## 3. S2–S4 (`hasil/bu_s2_*`, `bu_s3_*`, `bu_s4_*`)

- **Kalibrasi**: Brier skill terhadap klimatologi komoditas (porsi naik di baris latih) 0,13–0,17. ECE dev h 8 0,056 sedikit melewati
  ambang 0,05 yang ditetapkan sebelumnya (S2 dev h 8 **gagal**); test 0,010 / 0,021. Peluang C1-tuned dapat dibaca sebagai peluang dengan
  selisih rata-rata ± 1–6 poin persen (ECE 0,010–0,056).
- **Arah saat bergerak material** (± 1.700–2.500 baris per horizon): macro F1 0,78–0,81, sedangkan aturan tanda tren 0,44–0,54. Kelemahan
  model memang ada pada perubahan kecil (D-146/D-147), bukan pada pergerakan yang penting bagi pengguna.
- **Selektif** (test): cakupan 25% → akurasi 0,829 / 0,808; 50% → 0,766 / 0,765; seluruh baris 0,680 / 0,686.

## 4. Batasan & implikasi

- Presisi 0,16–0,18 berarti sekitar 1 dari 6 komoditas yang ditandai benar-benar naik material. Bila setiap tanda diikuti operasi pasar,
  alarm palsu tetap banyak. Daftar pantau lebih cocok sebagai **prioritas pemantauan** daripada pemicu tindakan otomatis.
- Laju-dasar kenaikan material turun dari 0,12–0,13 (dev) ke 0,09 (test), selaras dengan pergeseran rezim 2024+ (D-147). Kriteria tetap lolos.
- Definisi material relatif per komoditas; bila TPID memakai ambang absolut (mis. ≥ 5%), kriteria perlu protokol baru sebelum diukur.
- Klaim (CLAUDE.md §20): ditulis sebagai "dalam evaluasi rolling-origin pseudo-real-time, daftar pantau berbasis pola historis
  menangkap ... kenaikan material dengan presisi ...", bukan "KAGAMI memprediksi kenaikan harga". Klasifier arah tetap eksploratif;
  H5 tidak berubah.
- Implikasi CRISP-DM: tujuan Task 4 arah bagi pengguna terpenuhi oleh C1-tuned tanpa model baru. Langkah berikutnya yang bernilai adalah
  **Evaluation → Knowledge Presentation/Deployment** (menyajikan daftar pantau + batasannya), dan validasi asumsi praktik TPID dengan
  pengguna nyata. Menaikkan macro F1 bukan lagi tujuan utama.

## 5. Reproduksi

`python docs/audit/20261125_business_understanding/scripts/bu.py` (dev) lalu `PART=test ...` (test; aturan naif pembanding dibaca dari
hasil dev). Prediksi = `direction_tuned_preds` C1t (sama dengan `base` D-151). Menjalankan ulang dev setelah penambahan mode test memberi
`bu_criteria.csv` identik byte-per-byte.

## 6. Adendum audit (D-155, 2026-11-25 22.21; protokol `PROTOKOL_AUDIT.md`, sha256 `e50c5c91a629b163eb1a0058b5e0f7b5885b6d7c6fd52991dbc18b83faf8c598`)

Menjawab audit Danen atas D-152–D-154. Bagian 0–5 di atas tidak diubah; koreksi tafsirannya ada di sini. Skrip `scripts/audit.py`,
hasil `hasil/audit_*.csv`.

**Validitas universe S1 (kritis): lolos.** Kandidat ranking = semua provinsi × komoditas yang fitur lag-nya tersedia pada origin, termasuk
baris yang kemudian tidak berubah (y = 0: dev 1.832 / 1.154, test 1.803 / 1.132, dihitung bukan kenaikan material). Satu-satunya
penyaringan berbasis target adalah baris yang targetnya tidak teramati: 2 + 2 baris dev, 0 test. Baris itu kini diikutkan (C1-tuned dilatih
ulang pada origin itu; prediksi baris lain identik, maks |Δp| 0) dan dihitung tidak kena. Presisi tidak berubah (V1-K2 test 0,179 / 0,161).
Ranking hanya memakai skor & fitur pada origin; ambang material dari baris latih.

**Koreksi tafsiran:**
- **Skor ≠ peluang kenaikan material.** Daftar pantau mengurutkan p_up C1-tuned, yaitu peluang *arah naik* bila harga berubah
  (P(naik | y ≠ 0, X)), bukan P(kenaikan material | X). Hasil S1 sah sebagai **kualitas ranking**, bukan sebagai peluang risiko.
  Kalibrasi S2 adalah kalibrasi peluang arah (baris y ≠ 0), bukan kalibrasi peluang kenaikan material.
- **S3 bersyarat**: dihitung pada baris yang *ternyata* bergerak material, jadi menunjukkan kemampuan menentukan arah pada kelompok itu,
  bukan kemampuan mengetahui sebelumnya baris mana yang akan bergerak material.
- **Bukan validasi independen.** Kriteria ditetapkan sebelum ukur, tetapi periode test 2024+ sudah dipakai D-145–D-152. Ditulis sebagai
  "evaluasi eksploratif dengan kriteria yang ditetapkan sebelumnya".
- **Titik akhir, bukan kejadian.** Kenaikan material = perubahan rerata minggu t+h terhadap minggu t. Lonjakan di tengah jendela yang
  kembali turun pada minggu t+h tidak terhitung, jadi ini bukan peringatan kejadian kapan pun dalam 4–8 minggu.
- **Materialitas statistik ≠ materialitas kebijakan.** 58% / 56% alarm test (46% / 40% dev) jatuh pada beras, gula, minyak goreng, daging
  sapi, yang ambang materialnya hanya 1,4–2,7% (h 4). Ambang kebijakan (disepakati pengguna) harus dilaporkan terpisah.

**V1 vs V2 (jumlah alarm berbeda).** Presisi V2-10% lebih tinggi karena alarmnya separuh V1-K2. Pada jumlah alarm sama (V2-setara):

| Test | Alarm/origin | Presisi h 4 / h 8 | Recall h 4 / h 8 | Alarm palsu/origin h 4 / h 8 | Provinsi beralarm/origin |
|---|---|---|---|---|---|
| V1-K1 (1 per provinsi) | 34 | 0,207 / 0,181 | 0,24 / 0,21 | 27 / 28 | 34 |
| V1-K2 (S1) | 68 | 0,179 / 0,161 | 0,41 / 0,36 | 56 / 57 | 34 |
| V1-K3 | 102 | 0,158 / 0,147 | 0,54 / 0,50 | 86 / 87 | 34 |
| V2-10% nasional | 34 | 0,225 / 0,200 | 0,26 / 0,23 | 26 / 27 | 25,7 / 25,6 |
| V2-setara nasional | 68 | 0,188 / 0,169 | 0,43 / 0,38 | 55 / 57 | 32,5 / 32,3 |

Ranking nasional sedikit lebih presisi pada jumlah alarm sama, tetapi meninggalkan ± 1,5 provinsi per minggu tanpa alarm. Kalimat §2
"V2 nasional kurang tegas" merujuk ke interval terhadap aturan naif (V2-10% h 8 memuat nol), bukan presisi. Anggaran K = 1/2/3 adalah
pertukaran presisi–recall; tidak ada K yang dipilih (kapasitas TPID belum diketahui).

**Pembanding.** Pembanding resmi tetap pilihan dev (`R_mom` h 4, `R_nat` h 8). Kepekaan terhadap `R_rev` (terbaik di test) kini dengan
interval: +0,066 (0,033..0,101) / +0,041 (0,003..0,078).

**C1-tuned vs IW_NAT (prediksi D-151, `hasil/audit_disagreement*.csv`).** Arah berbeda pada 12% (h 4) / 7–8% (h 8) baris dev & test.
Di antara yang berbeda (y ≠ 0), test h 4: diperbaiki IW_NAT 721, dirusak 629 (bersih +92); h 8: 425 vs 393 (+32). Kuintil |y| terkecil
test h 4 +33 (166 vs 133). Per komoditas test bersih: telur +42 / +39, cabai merah +42 / +9, beras +9 / +14; negatif bawang putih −19 / −22,
cabai rawit −26 / −18, gula +13 / −25. Keuntungan IW_NAT adalah selisih kecil dari banyak pembalikan arah yang hampir saling meniadakan.

**Kartu K4 (usulan, belum dijalankan): target operasional "risiko kenaikan material".** Problem: TPID butuh P(kenaikan material), bukan
P(naik). Karakteristik data: laju-dasar 9–13%, ambang per komoditas. Hipotesis: klasifier yang dilatih langsung pada z = 1[y ≥ thr]
(semua baris, termasuk y = 0) memberi ranking & peluang yang lebih sesuai daripada p_up. Metode: HGB dengan kolom C1-tuned, label z.
Validasi: precision/recall@K, PR-AUC, Brier & kalibrasi pada z, dibandingkan dengan p_up C1-tuned; materialitas statistik dan kebijakan
dilaporkan terpisah; versi "kejadian kapan pun dalam jendela" sebagai target kedua. Kebocoran: ambang dari baris latih per origin.
Keputusan: hanya dijalankan setelah kebutuhan TPID (anggaran pemantauan, ambang kebijakan, titik akhir vs kejadian) divalidasi pengguna;
periode test 2024+ tidak dipakai untuk memilih, konfirmasi lewat prediksi maju.
