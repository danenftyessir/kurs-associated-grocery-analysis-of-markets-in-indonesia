# Temuan KAGAMI

*Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia): harga eceran mingguan 10 komoditas di 34 provinsi,
2018-01-01 s.d. pembekuan 2026-11-21 (337 dari 340 seri layak). Semua hasil bersifat asosiasional: KAGAMI tidak meramal
kurs dan tidak mengamati rantai pasok. Respons yang tidak terdeteksi dibaca sebagai batas atas kepekaan, bukan kegagalan.*

**Cara membaca angka.** β_e(h) adalah perubahan kumulatif log harga eceran h minggu setelah kenaikan 1 log IDR/USD
(kira-kira persen perubahan harga per 1% pelemahan rupiah), setelah mengendalikan lag perubahan harga, harga Brent,
musiman bulanan, minggu sekitar Idulfitri, dan efek tetap seri. ω(h) sama untuk harga dunia padanan dalam rupiah.
PT(h) = β_e(h)/γ(h), dengan γ(h) respons kurs terhadap dirinya sendiri. Interval 95% **resmi** (praregistrasi) adalah
yang lebih lebar dari ±1,96·SE cluster minggu dan persentil bootstrap blok 13 minggu. Interval **terkalibrasi plasebo**
adalah analisis kepekaan tambahan (lihat Keterbatasan).

## Ringkasan

1. Di antara 10 komoditas yang diamati, respons nasional harga eceran terhadap IDR/USD sebagian besar tidak terdeteksi.
   Asosiasi yang paling konsisten adalah harga minyak goreng dengan harga sawit dunia dalam rupiah: ω(8) = 0,21
   (interval terkalibrasi 0,08..0,34; interval resmi −0,01..0,36), dengan tanda positif di semua pemeriksaan Tier 1.
2. Variasi respons antarprovinsi melebihi derau hanya untuk telur ayam (q 0,04) dan daging ayam (q 0,050, tepat di
   ambang). Tidak ada struktur regional yang terdeteksi (k = 1); struktur dengan selisih respons RMS ≥ 0,2 per fitur
   akan terdeteksi (recovery ≥ 0,96).
3. Tidak ada asimetri depresiasi–apresiasi yang terdeteksi; uji konfirmatori H2 untuk beras dan daging sapi tidak menolak.
4. Di antara 10 komoditas, rasio impor langsung tidak berasosiasi monoton dengan PT(8) (τ-b −0,045, p eksak 0,93), dan
   keterpencilan provinsi tidak berasosiasi dengan respons h = 4 (H3 tidak didukung).
5. Dalam evaluasi bersyarat pseudo-real-time (76 origin 2021–2026), fitur kurs dan harga dunia tidak menurunkan MAE
   prediksi 4 dan 8 minggu (rasio M2/M1 1,014 dan 1,017); H5 tidak didukung.
6. Eksploratif (bukan praregistrasi): foundation model TimesFM 3.0 tanpa pelatihan pada data kami menurunkan MAE terhadap
   M1 sebesar 10,5% pada h = 8 (DM p < 0,001), tetapi menambahkan kurs dan harga dunia ke TimesFM maupun TSMixer tidak
   menambah akurasi. Hasil ini memperkuat temuan 5: pola harga lebih informatif daripada kurs.

**Jawaban sementara atas pertanyaan pemandu.** Perbedaan kepekaan lebih banyak tampak antarkomoditas daripada antarlokasi:
estimasi nasional berkisar dari −1,67 (daging ayam) sampai 1,37 (cabai merah) pada h = 8, sedangkan variasi antarprovinsi
di atas derau hanya terdeteksi pada dua komoditas jalur pakan. Karena sebagian besar interval nasional memuat nol, ini
adalah pola deskriptif, bukan peringkat kepekaan yang pasti.

## RQ1 — Respons nasional per komoditas

| Komoditas | Jalur | β_e(8) resmi | PT(8) resmi | ω(8) resmi |
|---|---|---|---|---|
| Beras | impor langsung | 0,01 (−0,25..0,18) | 0,00 (−0,21..0,11) | 0,06 (−0,03..0,14) |
| Bawang putih | impor langsung | −0,68 (−2,93..2,41) | −0,51 (−1,77..1,55) | – |
| Gula pasir | impor langsung | 0,66 (−0,27..1,44) | 0,50 (−0,25..0,93) | −0,00 (−0,26..0,21) |
| Daging sapi | impor langsung | 0,02 (−0,14..0,17) | 0,01 (−0,12..0,13) | −0,00 (−0,05..0,08) |
| Daging ayam | input impor | −1,67 (−2,61..0,05) | −1,27 (−1,78..0,05) | −0,26 (−0,55..0,36) |
| Telur ayam | input impor | −0,53 (−1,21..0,49) | −0,40 (−0,99..0,37) | −0,22 (−0,40..0,26) |
| Minyak goreng | paritas ekspor | −0,23 (−0,58..0,38) | −0,17 (−0,50..0,29) | 0,21 (−0,01..0,36) |
| Bawang merah | domestik | −0,81 (−2,52..2,66) | −0,62 (−1,93..2,31) | – |
| Cabai merah | domestik | 1,37 (−2,91..4,63) | 1,04 (−2,21..3,55) | – |
| Cabai rawit | domestik | 0,76 (−4,83..4,14) | 0,57 (−4,18..3,06) | – |

Satuan: Δ log harga per 1 log penggerak. Sumber: `profiles` (nasional).

- **Batas atas.** Untuk beras, pass-through PT(8) di atas 0,11 dapat dikesampingkan; untuk daging sapi di atas 0,13.
  Untuk cabai dan bawang, interval sangat lebar (MDE PT(8) 1,84–3,75), sehingga hasil nol hampir tidak informatif.
- **Minyak goreng & harga sawit dunia.** ω(4) 0,16 (resmi 0,02..0,28), ω(8) 0,21 (−0,01..0,36), ω(12) 0,31 (0,02..0,47).
  Terkalibrasi plasebo: 0,16 (0,04..0,28, q 0,092), 0,21 (0,08..0,34, q 0,024), 0,31 (0,16..0,46, q 0,024). Pada h = 8
  semua cek Tier 1 memberi interval di atas nol; asosiasinya lebih kecil sebelum April 2021 (0,07, 0,03..0,10) daripada
  sesudahnya (0,22, 0,06..0,37).
- **Daging ayam & IDR/USD.** Kenaikan IDR/USD berasosiasi dengan penurunan harga daging ayam: β_e(4) −1,16 (resmi
  −1,86..−0,00; terkalibrasi −2,10..−0,23, q 0,024), β_e(8) −1,67 (resmi −2,61..0,05; terkalibrasi −2,77..−0,58, q 0,058).
  Arah ini berlawanan dengan dugaan jalur input impor dan tidak tahan pemeriksaan: tanpa Mar–Jun 2020 dan bulan Brent
  ekstrem −0,96 (−2,05..0,14), frekuensi bulanan −0,60 (−1,33..0,13). Komponen kurs yang spesifik rupiah −1,89
  (−3,02..−0,76) menunjukkan asosiasinya bukan semata pergerakan dolar global.
- **Gula β_e(4) tidak ditafsirkan sebagai temuan.** Walaupun 0,69 lolos kalibrasi plasebo (0,25..1,13, q 0,024),
  estimasinya −0,03 tanpa Mar–Jun 2020 dan −0,03 sesudah April 2021 (`robustness`).
- **Event study.** Dari 390 sel nasional (13 episode × 10 komoditas × h 4/8/12), 19 (4,9%) memiliki p plasebo < 0,05,
  setara dengan yang diharapkan dari kebetulan. Tidak ada respons episode yang dapat dibedakan dari jendela plasebo.

## RQ2 — Komoditas atau lokasi?

| Komoditas | Q | τ² | I² | p plasebo | q BH |
|---|---|---|---|---|---|
| Telur ayam | 161,7 | 0,226 | 0,80 | 0,004 | 0,040 |
| Daging ayam | 132,6 | 0,456 | 0,75 | 0,010 | 0,050 |
| Gula pasir | 81,0 | 0,031 | 0,59 | 0,020 | 0,067 |
| Bawang merah | 92,5 | 0,592 | 0,64 | 0,095 | 0,238 |
| Cabai merah | 57,8 | 1,013 | 0,43 | 0,265 | 0,530 |
| Beras | 39,7 | 0,002 | 0,17 | 0,380 | 0,633 |
| Bawang putih, cabai rawit, daging sapi, minyak goreng | 18,5–31,3 | 0 | 0 | 0,64–0,98 | 0,92–0,98 |

H0-Het pada h = 8, penggerak IDR/USD, 34 provinsi (cabai rawit 31). Sumber: `heterogeneity`.

- H0-Het ditolak untuk telur ayam dan daging ayam. Penolakan daging ayam tepat di ambang (5 dari 499 plasebo melampaui
  Q asli), sehingga peka terhadap galat Monte Carlo. Korelasi deviasi provinsi rata-rata antarkomoditas ρ̄ = 0,094
  (p plasebo 0,198).
- Untuk empat komoditas τ² = 0: semua provinsi disusutkan ke respons nasional (temuan sah, bukan galat). τ² REML sebagai
  cek memberi angka sejalan: telur ayam 0,283, daging ayam 0,676, gula 0,031; nol (atau < 0,001) untuk empat komoditas yang sama.
- **Clustering.** Silhouette Ward maksimum 0,184 (k = 3) di bawah persentil 95 plasebo 0,196, sehingga k = 1: tidak ada
  struktur regional yang terdeteksi. Perbandingan dengan zona HET, Jawa/luar Jawa, kuantil n_kota, dan 7 wilayah tidak
  berlaku karena k = 1 (`partition_compare`).
- **Batas deteksi.** Struktur tertanam dengan selisih respons RMS 0,2 per fitur dipulihkan pada 99,5% (k = 2) dan 96,5%
  (k = 3) replikasi; selisih 0,1 hanya 43% dan 13% (`planted_recovery`). Struktur regional dengan selisih ≥ 0,2 dapat
  dikesampingkan.

## RQ3 — Depresiasi vs apresiasi

| Komoditas | Status | β⁺ − β⁻ (8) | p Wald | p plasebo |
|---|---|---|---|---|
| Beras | konfirmatori | −0,14 (−0,58..0,47) | 0,49 | 0,62 |
| Daging sapi | konfirmatori | −0,26 (−0,88..0,21) | 0,089 | 0,28 |
| Bawang putih | deskriptif | −5,78 (−10,23..3,14) | 0,011 | 0,022 |
| 7 komoditas lain | deskriptif | semua interval memuat nol | 0,11–0,87 | 0,16–0,88 |

Sumber: `asymmetry` (interval laporan = Wald ∪ persentil bootstrap).

- H2 tidak ditolak untuk beras dan daging sapi (satu-satunya komoditas dengan MDE asimetri PT(8) ≤ 0,5: 0,44 dan 0,32).
  Asimetri PT(8) di atas 0,44 (beras) dan 0,32 (daging sapi) akan terdeteksi dengan daya 80%.
- Bawang putih p plasebo 0,022 tidak bertahan koreksi atas 10 uji deskriptif; tidak ditulis sebagai asimetri.

## RQ4 — Karakteristik yang berasosiasi dengan respons

- **E1.** Di antara 10 komoditas yang diamati, τ-b Kendall antara PT(8) dan rasio impor langsung −0,045 (jackknife
  −0,65..0,56), p permutasi eksak 0,93 (`assoc`).
- **H3 (keterpencilan).** Koefisien ln(1 + jarak ke hub terdekat) pada respons h = 4, gabungan 10 komoditas, 337 seri:
  0,007 (−0,022..0,033) per 1 SD jarak, p satu sisi 0,80 → tidak didukung. Asosiasi negatif di atas 0,022 per 1 SD dapat
  dikesampingkan. Per komoditas, tidak ada interval yang tidak memuat nol (`assoc`).
- **Meta-regresi eksploratif.** Dari 88 koefisien dua sisi (jarak hub, kecukupan produksi beras, n_kota; 10 komoditas dan
  gabungan; h 4/8/12), tidak ada yang intervalnya tidak memuat nol; q BH minimum 1,0. Interval = yang lebih lebar dari
  SE CR2 dan bootstrap, dan p dihitung konsisten dengan interval itu.
- **Interaksi efek tetap (3c).** Sembilan koefisien Δe × Z(r) (jarak hub, kecukupan beras, n_kota; h 4/8/12) memiliki
  interval yang memuat nol; terbesar ln_dist_hub h = 8, 0,16 (−0,00..0,33).

## RQ5 — Nilai prediktif kurs (Task 4)

| Model vs M1 | MAE h = 4 | MAE h = 8 |
|---|---|---|
| M0 (tanpa perubahan) | 1,017 | 1,016 |
| M2 (+ kurs, harga dunia, episode) | 1,014 (DM p 0,001) | 1,017 (DM p 0,006) |
| M3 (gradient boosting + identitas) | 1,044 (DM p 0,031) | 1,015 (DM p 0,49) |

76 origin (h 4; 75 pada h 8, 38 tidak tumpang tindih), 337 seri provinsi. Rasio > 1 = kurang akurat dari M1.
Sumber: `forecast_eval`.

- Dalam evaluasi bersyarat pseudo-real-time, fitur kurs dan harga dunia tidak menurunkan MAE. Pada h = 8 rasio M2/M1
  terburuk untuk daging sapi 1,30, gula 1,13, dan beras 1,11; untuk cabai dan bawang merah ≈ 1.
- **H5** (h = 8, origin pergerakan kurs besar): impor langsung 1,12 (p satu sisi 0,95) dan input impor 1,12 (0,88),
  Holm 1,0 → tidak didukung. Hanya 8 origin pergerakan besar (7 tidak tumpang tindih), sehingga daya uji rendah.
- **Studi kasus 2026 (V2).** Rasio M2/M1 1,005 pada h = 4 (10 origin) dan h = 8 (9 origin) (`robustness`).
- Model tanpa perubahan (M0) lebih akurat daripada M1 untuk komoditas yang harganya diatur atau kaku: daging sapi 0,78,
  beras 0,82, gula 0,85, minyak goreng 0,89, bawang putih 0,93 (h = 4).

## Eksplorasi Task 4 — Arah perubahan dan model lanjutan

*Analisis tambahan setelah praregistrasi (D-139 s.d. D-142). Tidak menggantikan uji H5; semua angka dari evaluasi
bersyarat pseudo-real-time dengan origin dan baris uji yang sama dengan M0–M3. Interval 95% dari bootstrap blok origin
(unit = origin, karena seri dalam satu origin berbagi guncangan nasional). Perbandingan eksploratif dikoreksi
Benjamini–Hochberg per keluarga (q < 0,05; D-143); hasil yang tidak lolos koreksi ditulis "tidak terbukti".*

**Arah perubahan harga (naik/turun) dari ramalan regresi.** Akurasi arah M1 dan M2 tidak berbeda dari selalu menebak
arah terbanyak: selisih h = 8 M1 +0,015 (−0,029..0,053), M2 +0,015 (−0,024..0,049). M3 di atas baseline: +0,057
(0,021..0,088). Pada komoditas yang harganya kaku (beras, daging sapi, gula, minyak goreng; ≥ 50% minggu tanpa perubahan),
M1 dan M3 berada di bawah baseline (M1 −0,100, q 0,011; M3 −0,058, q 0,011); M2 (−0,062) tidak lolos koreksi (q 0,080).

**Klasifier arah langsung (HistGradientBoostingClassifier).** Dilatih langsung untuk naik/turun dengan fitur yang sama,
akurasi arah h = 8 0,617 dengan fitur kurs (C2) dan 0,607 tanpa (C1), di atas baseline 0,545 (selisih C2 +0,071,
0,034..0,108). Fitur kurs tidak terbukti menambah akurasi: C2 − C1 +0,009 (−0,007..0,027).

**Model deep learning dan foundation model.**

| Model | MAE / M1, h = 4 | MAE / M1, h = 8 | Akurasi arah h = 8 |
|---|---|---|---|
| TimesFM 3.0 zero-shot | 0,935 (DM p < 0,001) | 0,895 (DM p < 0,001) | 0,623 |
| TimesFM 3.0 + kovariat kurs & harga dunia | 0,939 (DM p 0,001) | 0,904 (DM p < 0,001) | 0,613 |
| PatchTST | 0,998 (DM p 0,92) | 0,962 (DM p 0,15) | 0,596 |
| TSMixer | 0,995 (DM p 0,77) | 0,966 (DM p 0,13) | 0,608 |
| TSMixer + kurs & harga dunia | 1,036 (DM p 0,16) | 0,994 (DM p 0,84) | 0,601 |

Rasio < 1 = lebih akurat dari M1. Baseline akurasi arah h = 8 = 0,545.

- Dalam evaluasi bersyarat pseudo-real-time, TimesFM 3.0 tanpa pelatihan pada data kami menurunkan MAE terhadap M1 sebesar
  6,5% (h = 4) dan 10,5% (h = 8); porsi variasi perubahan harga yang terjelaskan naik dari 0,07 menjadi 0,25 (h = 8).
- Kurs dan harga dunia tetap tidak menambah akurasi: TimesFM dengan kovariat kurs vs tanpa, rasio MAE 1,005 (h = 4) dan
  1,010 (h = 8), keduanya tidak nyata; TSMixer dengan kanal kurs vs tanpa 1,041 (h = 4, DM p 0,020, tetapi tidak lolos koreksi
  BH, q 0,057) dan 1,029 (h = 8). Ini sejalan dengan H5: perbaikan akurasi datang dari pola harga itu sendiri, bukan dari kurs.
- Pada komoditas berharga kaku, PatchTST dan TSMixer (± kurs) berada di bawah baseline arah (q 0,018–0,049 pada h = 8);
  TimesFM −0,074 tidak lolos koreksi (q 0,053). Tidak ada model yang lebih baik dari menebak arah terbanyak untuk kelompok ini.
- **Kualitas klasifikasi arah (h = 8).** F1 makro tertinggi TimesFM 0,623, lalu klasifier C2 0,614, C1 0,605, TSMixer 0,604
  dan M3 0,594 (M1 0,551); F1 berbobot hampir sama karena kelas naik/turun seimbang (54,5% naik). Semua angka ini dihitung pada
  baris dengan perubahan harga ≠ 0 (cakupan 90,7%); bila minggu tanpa perubahan dihitung salah, akurasi TimesFM 0,566 dan M1
  0,508. Kemampuan memisahkan naik/turun masih lemah (ROC-AUC ≤ 0,70, MCC ≤ 0,26).
- **Kestabilan.** Tiga seed pelatihan PatchTST/TSMixer pada origin yang sama: rentang akurasi arah ≤ 0,03 dan MAE/M1 ≤ 0,02;
  TSMixer + kurs lebih buruk dari TSMixer di ketiga seed (MAE/M1 0,995 ± 0,009 vs 0,966 ± 0,007, h = 8). Semua keputusan
  "lebih baik / tidak terbukti / lebih buruk" sama untuk panjang blok bootstrap 2, 3, 4, dan 6 origin; uji DM TimesFM vs M1
  tetap p < 0,001 untuk lag HAC 1–5. Pada origin 2026, rasio MAE TimesFM/M1 0,938 (2023: 0,876; 2024: 0,834).
- Perbandingan yang lolos koreksi BH: MAE TimesFM (± kurs) vs M1 pada h = 4 dan 8 (q ≤ 0,004); akurasi arah TimesFM (± kurs)
  vs M3 pada h = 4 (+0,043 dan +0,047, q 0,015); klasifier C2 vs M3 pada h = 4 (+0,025, q 0,015); C1 vs M1 pada h = 4 dan 8
  (+0,045 dan +0,047, q ≤ 0,024). Tidak ada perbandingan "dengan kurs vs tanpa kurs" yang lolos.

## Eksplorasi E2 — Respons per rezim HET/HAP

145 sel (10 komoditas, 3–6 rezim, h 4/8/12, IDR/USD & harga dunia). Interval dikalibrasi terhadap 499 plasebo
geser-melingkar; 15 sel intervalnya tidak memuat nol, tetapi q BH minimum 0,145: tidak ada perbedaan antarrezim yang tahan
koreksi multiplisitas. Pola terkuat (eksploratif): bawang putih pada rezim Perbadan 12/2024, β_e(8) 3,74 (1,83..5,65;
98 minggu; sampel penuh −0,68), dan telur ayam pada rezim Perbadan 5/2022, ω(4) −0,89 (−1,47..−0,31; 78 minggu)
(`regime_profiles`).

## Robustness & validasi

- **Tier 1.** Estimasi baseline berada di dalam interval cek pada 366 dari 382 sel: lag 2/4/8 96/96, dekomposisi dolar
  global vs spesifik rupiah 78/78, frekuensi bulanan 47/48, h 8 vs 12 15/16, tanpa Mar–Jun 2020 & bulan Brent ekstrem 45/48,
  sub-periode sebelum/sesudah 2021-04-05 85/96 (`robustness`). Dari 16 pengecualian, 10 pada gula dan minyak goreng
  (besaran berbeda antar sub-periode) dan 3 pada daging ayam.
- **Tier 2.** Baseline berada di dalam interval cek pada 191 dari 193 sel: varian PIHPS lain dan komposit pakan
  alternatif 94/96, harga mingguan = observasi terakhir 48/48, Panel Harga Bapanas bulanan 42/42, keterpencilan alternatif
  (km ke hub tanpa log; km ke Jakarta saja) 6/6, dan ordinal jalur eksposur 1/1 (τ-b −0,03, −0,75..0,70). Dua pengecualian
  bertanda sama: Gula Kualitas Premium β_e(4) 0,36 (0,15..0,57) vs 0,69, dan Minyak Goreng Curah ω(8) 0,36 (0,26..0,45) vs
  kemasan 0,21 — minyak goreng curah lebih peka terhadap harga sawit dunia dalam rupiah.
- **V4 (LP vs event study).** Implikasi LP berada di dalam interval event pada 26 dari 30 sel, tetapi hanya 2 dari 30
  interval event yang tidak memuat nol dan kesamaan tanda antar episode 0,51; kecocokan ini lemah sebagai validasi.

## Keterbatasan

- **Bootstrap blok menarik estimasi ke nol.** Blok 13 minggu lebih pendek dari jendela LP (h + 6 minggu), sehingga rerata
  replikasi hanya 0,57 / 0,35 / 0,35 kali estimasi (median, h 4 / 8 / 12). Interval resmi (termasuk PT dan provinsi)
  karena itu cenderung terlalu lebar. Untuk β_e dan ω nasional, analisis kepekaan dengan interval terkalibrasi plasebo
  disediakan (`national_calibrated`); interval resmi tetap dikutip lebih dulu.
- **SE cluster minggu sedikit terlalu sempit.** Di bawah plasebo |t| > 1,96 terjadi pada 8,1% replikasi nasional, sehingga
  MDE untuk komoditas volatil (cabai, bawang merah, telur) cenderung optimistis.
- **Task 4.** Evaluasi pseudo-real-time (vintage revisi tidak tersedia). M1 adalah satu ridge untuk 10 komoditas tanpa
  identitas komoditas (bulan sebagai angka 1–12). Dua pemeriksaan kepekaan memberi kesimpulan yang sama: ridge per komoditas,
  dan ridge dengan dummy bulan + dummy minggu sekitar Idulfitri (M2/M1 1,005 pada h = 4 dan 1,019 pada h = 8; H5 Holm 0,56).
  Pada pemeriksaan kedua, M1 makin tertinggal dari model tanpa perubahan (M0/M1 0,95 dan 0,97), sehingga keterbatasan utama
  baseline adalah pengumpulan lintas komoditas, bukan penyandian musim.
- **Model eksploratif Task 4.** Model deep dan TimesFM ditambahkan setelah praregistrasi dan tidak menguji H5. Hiperparameter
  model deep ditetapkan sebelum melihat hasil dan tidak dituning; model dilatih ulang tiap 16 minggu dari data sampai origin.
  TimesFM 3.0 dirilis September 2026 dan dilatih pada korpus deret waktu publik yang isinya tidak kami ketahui; bila deret
  harga pangan Indonesia periode 2021–2026 ikut di dalamnya, keunggulannya dalam evaluasi ini adalah batas atas. Keunggulan
  yang lebih kecil pada origin 2026 (MAE/M1 0,938) konsisten dengan kemungkinan itu, tetapi tidak membuktikannya. Bobot TimesFM
  (1,32 GB) memakai lisensi non-komersial dan tidak ikut paket juri.
- **Harga diatur.** Banyak minggu tanpa perubahan harga untuk komoditas yang diatur (beras 92%, daging sapi 90%, gula 85%,
  minyak goreng 87% sel carry-forward); ini kekakuan harga nyata, bukan data hilang, dan membatasi respons yang teramati.
- **Cakupan.** Kesimpulan berlaku untuk 10 komoditas, 34 provinsi (kerangka lama), dan periode 2018–2026.

## Sumber angka

`eligibility`, `episodes`, `mde` (Tahap 0); `profiles`, `events` (Task 1); `heterogeneity`, `cluster_selection`,
`partition_compare`, `planted_recovery` (Task 2); `assoc`, `asymmetry`, `regime_profiles`, `national_calibrated`
(Task 3); `forecast_eval` (Task 4); `robustness`. Eksplorasi Task 4: `forecast_preds`, `direction_preds`, `deep_preds` dan
log evaluasi Task 4 di `logs/evaluations/` (app halaman 7). Rambu klaim: CLAUDE.md §20.
