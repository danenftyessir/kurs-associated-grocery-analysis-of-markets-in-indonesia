# Temuan KAGAMI

*Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia): harga eceran mingguan 10 komoditas di 34 provinsi,
2018-01-01 s.d. pembekuan 2026-11-21 (337 dari 340 seri layak). Semua hasil bersifat asosiasional: KAGAMI tidak meramal
kurs dan tidak mengamati rantai pasok. Respons yang tidak terdeteksi dibaca sebagai batas atas kepekaan, bukan kegagalan.*

**Cara membaca angka.** β_e(h) adalah perubahan kumulatif log harga eceran h minggu setelah kenaikan 1 log IDR/USD
(kira-kira persen perubahan harga per 1% pelemahan rupiah), setelah mengendalikan lag perubahan harga, harga Brent,
musiman bulanan, minggu sekitar Idulfitri, dan efek tetap seri. ω(h) sama untuk harga dunia padanan dalam rupiah.
PT(h) = β_e(h)/γ(h), dengan γ(h) respons kurs terhadap dirinya sendiri.

**Tiga tingkat bukti.** Setiap angka di dokumen ini termasuk salah satu tingkat berikut, dan tingkatnya selalu disebut.

| Tingkat | Isi | Status |
|---|---|---|
| 1. Praregistrasi | H0-Het, H2, H3, H5 (konfirmatori); E1, E2 (deskriptif/eksploratif yang sudah didaftarkan); interval **resmi** = yang lebih lebar dari ±1,96·SE cluster minggu dan persentil bootstrap blok 13 minggu | dibekukan di G6 (2026-11-20), sebelum β dilihat |
| 2. Kepekaan inferensi | interval **terkalibrasi plasebo** (D-129, D-163) | tambahan sesudah G6; ukurannya diuji di bawah null (bagian Kalibrasi inferensi) |
| 3. Eksploratif | semua model dan klasifier arah Task 4 sesudah praregistrasi (Lampiran A) | tidak menguji hipotesis; periode uji 2024+ sudah dipakai berulang |

Satu-satunya bukti out-of-sample yang bersih untuk tingkat 3 adalah validasi prospektif yang sedang berjalan.

## Ringkasan

1. Di antara 10 komoditas yang diamati, respons nasional harga eceran terhadap IDR/USD sebagian besar tidak terdeteksi.
   Asosiasi yang paling konsisten adalah harga minyak goreng dengan harga sawit dunia dalam rupiah. Menurut interval resmi:
   ω(4) = 0,16 (0,02..0,28) dan ω(12) = 0,31 (0,02..0,47); ω(8) = 0,21 (−0,01..0,36). Tandanya positif di semua pemeriksaan Tier 1.
2. Variasi respons antarprovinsi melebihi derau hanya untuk telur ayam (q 0,04) dan daging ayam (q 0,050, tepat di
   ambang). Tidak ada struktur regional yang terdeteksi (k = 1). Struktur dengan selisih respons RMS ≥ 0,2 per fitur
   akan terdeteksi (recovery ≥ 0,96).
3. Tidak ada asimetri depresiasi–apresiasi yang terdeteksi. Uji konfirmatori H2 untuk beras dan daging sapi tidak menolak.
4. Di antara 10 komoditas, rasio impor langsung tidak berasosiasi monoton dengan PT(8) (τ-b −0,045, p eksak 0,93), dan
   keterpencilan provinsi tidak berasosiasi dengan respons h = 4 (H3 tidak didukung).
5. Dalam evaluasi bersyarat pseudo-real-time (76 origin 2021–2026), fitur kurs dan harga dunia tidak menurunkan MAE
   prediksi 4 dan 8 minggu (rasio M2/M1 1,009 dan 1,013). H5 tidak didukung.
6. **Arti hasil nol bagi TPID.** Untuk 6 dari 10 komoditas (beras, gula, daging sapi, minyak goreng, daging ayam, telur),
   kenaikan harga eceran nasional di atas 0,3–4,7% (± Rp90–940 per kg/liter) dalam 8 minggu yang berasosiasi dengan pelemahan
   rupiah 5% dapat dikesampingkan. Lonjakan harga yang lebih besar dari itu pada komoditas tersebut sulit dijelaskan oleh kurs.
   Untuk cabai dan bawang, data tidak cukup presisi untuk menarik batas yang berguna.
7. Eksploratif (Lampiran A, bukan uji hipotesis): pola harga sendiri lebih informatif daripada kurs. Klasifier arah berbasis
   dinamika harga dapat menyusun daftar pantau komoditas per provinsi yang memuat kenaikan harga material sekitar dua kali
   laju-dasar. Fitur kurs tidak menambah akurasi pada model mana pun.

**Jawaban sementara atas pertanyaan pemandu.** Perbedaan kepekaan lebih banyak tampak antarkomoditas daripada antarlokasi.
Estimasi nasional berkisar dari −1,67 (daging ayam) sampai 1,37 (cabai merah) pada h = 8, sedangkan variasi antarprovinsi
di atas derau hanya terdeteksi pada dua komoditas jalur pakan. Karena sebagian besar interval nasional memuat nol, ini
adalah pola deskriptif, bukan peringkat kepekaan yang pasti.

## Makna bagi pengguna: batas atas dalam Rupiah

Hasil nol tetap informatif bila diterjemahkan ke batas atas yang dapat dipakai pengguna. Tabel berikut memakai PT(8) nasional
dengan interval **resmi** dan harga acuan = median antarprovinsi dari rerata harga teramati 8 minggu s.d. 2026-11-16.

| Komoditas | Harga acuan (Rp) | Rupiah melemah 5%: perubahan harga h = 8 | Dalam Rupiah | Batas atas berguna? |
|---|---|---|---|---|
| Beras (kg) | 16.392 | +0,02% (−1,04..+0,55%) | +3 (−170..+89) | ya |
| Daging sapi (kg) | 150.525 | +0,06% (−0,58..+0,62%) | +91 (−872..+938) | ya |
| Daging ayam (kg) | 38.260 | −5,99% (−8,31..+0,25%) | −2.294 (−3.178..+95) | ya |
| Minyak goreng (liter) | 23.140 | −0,85% (−2,41..+1,42%) | −196 (−557..+328) | ya |
| Telur ayam (kg) | 29.462 | −1,95% (−4,69..+1,82%) | −575 (−1.383..+537) | ya |
| Gula pasir (kg) | 19.372 | +2,47% (−1,19..+4,65%) | +479 (−231..+900) | sedang |
| Bawang putih (kg) | 36.784 | −2,47% (−8,29..+7,83%) | −910 (−3.051..+2.881) | tidak |
| Bawang merah (kg) | 37.942 | −2,97% (−8,97..+11,95%) | −1.125 (−3.404..+4.532) | tidak |
| Cabai merah (kg) | 79.642 | +5,19% (−10,22..+18,91%) | +4.133 (−8.143..+15.061) | tidak |
| Cabai rawit (kg) | 89.660 | +2,84% (−18,44..+16,09%) | +2.545 (−16.532..+14.424) | tidak |

Skenario bersyarat berdasarkan pola historis, bukan ramalan: perubahan = exp(PT(8) · ln 1,05) − 1. Sumber: `profiles`,
`panel_weekly`; perhitungan di `docs/audit/20261127_redflag_juri/` (termasuk h = 4).

- **Cara pakai.** Bila harga beras di suatu provinsi naik Rp500/kg dalam 8 minggu setelah rupiah melemah 5%, data historis
  menunjukkan bagian yang konsisten dengan kurs paling banyak ± Rp90. Sisanya lebih mungkin berasal dari faktor lain (pasokan,
  musim, kebijakan). Ini mengarahkan penelusuran penyebab, bukan menyimpulkannya.
- **Harga dunia.** Kenaikan harga sawit dunia dalam rupiah 10% berasosiasi dengan kenaikan harga minyak goreng kemasan +1,5%
  (+0,2..+2,7%) atau ± Rp350/liter (Rp37..620) pada h = 4 (interval resmi tidak memuat nol), dan +2,0% (−0,1..+3,5%) pada h = 8.
  Bagi TPID, harga sawit dunia dalam rupiah lebih relevan dipantau daripada kurs itu sendiri untuk minyak goreng.
- **Batas.** Angka ini nasional. Untuk provinsi, variasi di atas derau hanya terdeteksi pada telur dan daging ayam.

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
- **Minyak goreng & harga sawit dunia.** Interval resmi: ω(4) 0,16 (0,02..0,28), ω(8) 0,21 (−0,01..0,36), ω(12) 0,31
  (0,02..0,47). Terkalibrasi plasebo (tingkat 2): 0,16 (0,04..0,28, q 0,092), 0,21 (0,08..0,34, q 0,024), 0,31 (0,16..0,46,
  q 0,024). Pada h = 8 semua cek Tier 1 memberi interval di atas nol. Asosiasinya lebih kecil sebelum April 2021 (0,07,
  0,03..0,10) daripada sesudahnya (0,22, 0,06..0,37).
- **Daging ayam & IDR/USD.** Kenaikan IDR/USD berasosiasi dengan penurunan harga daging ayam: β_e(4) −1,16 (resmi
  −1,86..−0,00; terkalibrasi −2,10..−0,23, q 0,024), β_e(8) −1,67 (resmi −2,61..0,05; terkalibrasi −2,77..−0,58, q 0,058).
  Arah ini berlawanan dengan dugaan jalur input impor dan tidak tahan semua pemeriksaan: tanpa Mar–Jun 2020 dan bulan Brent
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
  Q asli; galat Monte Carlo p ± 0,004), sehingga ditulis sebagai penolakan rapuh. Korelasi deviasi provinsi rata-rata
  antarkomoditas ρ̄ = 0,094 (p plasebo 0,198).
- Untuk empat komoditas τ² = 0: semua provinsi disusutkan ke respons nasional (temuan sah, bukan galat). τ² REML sebagai
  cek memberi angka sejalan: telur ayam 0,283, daging ayam 0,676, gula 0,031; nol (atau < 0,001) untuk empat komoditas yang sama.
- **Clustering.** Silhouette Ward maksimum 0,184 (k = 3) di bawah persentil 95 plasebo 0,196, sehingga k = 1: tidak ada
  struktur regional yang terdeteksi. Perbandingan dengan zona HET, Jawa/luar Jawa, kuantil n_kota, dan 7 wilayah tidak
  berlaku karena k = 1 (`partition_compare`).
- **Batas deteksi.** Struktur tertanam dengan selisih respons RMS 0,2 per fitur dipulihkan pada 99,5% (k = 2) dan 96,5%
  (k = 3) replikasi; selisih 0,1 hanya 43% dan 13% (`planted_recovery`). Struktur regional dengan selisih ≥ 0,2 dapat
  dikesampingkan.
- **Arti bagi pengguna.** Tidak adanya kelompok provinsi berarti satu profil kepekaan nasional per komoditas cukup sebagai
  titik awal di semua provinsi, kecuali telur dan daging ayam.

## RQ3 — Depresiasi vs apresiasi

| Komoditas | Status | β⁺ − β⁻ (8) | p Wald | p plasebo |
|---|---|---|---|---|
| Beras | konfirmatori | −0,14 (−0,58..0,47) | 0,49 | 0,62 |
| Daging sapi | konfirmatori | −0,26 (−0,88..0,21) | 0,089 | 0,28 |
| Bawang putih | deskriptif | −5,78 (−10,23..3,14) | 0,011 | 0,022 |
| 7 komoditas lain | deskriptif | semua interval memuat nol | 0,11–0,87 | 0,16–0,88 |

Sumber: `asymmetry` (interval laporan = Wald ∪ persentil bootstrap).

- H2 tidak ditolak untuk beras dan daging sapi, satu-satunya komoditas dengan MDE asimetri PT(8) ≤ 0,5 (0,44 dan 0,32).
  Asimetri PT(8) di atas 0,44 (beras) dan 0,32 (daging sapi) akan terdeteksi dengan daya 80%.
- Bawang putih p plasebo 0,022 tidak bertahan koreksi atas 10 uji deskriptif, jadi tidak ditulis sebagai asimetri.

## RQ4 — Karakteristik yang berasosiasi dengan respons

- **E1.** Di antara 10 komoditas yang diamati, τ-b Kendall antara PT(8) dan rasio impor langsung −0,045 (jackknife
  −0,65..0,56), p permutasi eksak 0,93 (`assoc`).
- **H3 (keterpencilan).** Koefisien ln(1 + jarak ke hub terdekat) pada respons h = 4, gabungan 10 komoditas, 337 seri:
  0,007 (−0,022..0,033) per 1 SD jarak, p satu sisi 0,80, jadi tidak didukung. Asosiasi negatif di atas 0,022 per 1 SD dapat
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
| M2 (+ kurs, harga dunia, episode) | 1,009 (DM p 0,009) | 1,013 (DM p 0,025) |
| M3 (gradient boosting + identitas) | 1,037 (DM p 0,052) | 1,014 (DM p 0,53) |

76 origin (h 4; 75 pada h 8, 38 tidak tumpang tindih), 337 seri provinsi. Rasio > 1 = kurang akurat dari M1.
Sumber: `forecast_eval` (dijalankan ulang 2026-11-26 dengan flag `episode` real-time, D-162; sebelumnya M2 1,014 / 1,017).

- Dalam evaluasi bersyarat pseudo-real-time, fitur kurs dan harga dunia tidak menurunkan MAE. Pada h = 8 rasio M2/M1
  terburuk untuk daging sapi 1,26, gula 1,10, dan beras 1,08; untuk cabai dan bawang merah ≈ 1.
- **H5** (h = 8, origin pergerakan kurs besar): impor langsung 1,11 (p satu sisi 0,93) dan input impor 1,12 (0,86),
  Holm 1,0, jadi tidak didukung. Hanya 8 origin pergerakan besar (7 tidak tumpang tindih), sehingga daya uji rendah.
- **Studi kasus 2026 (V2).** Rasio M2/M1 1,005 pada h = 4 (10 origin) dan 1,004 pada h = 8 (9 origin) (`robustness`).
- Model tanpa perubahan (M0) lebih akurat daripada M1 untuk komoditas yang harganya diatur atau kaku: daging sapi 0,78,
  beras 0,82, gula 0,85, minyak goreng 0,89, bawang putih 0,93 (h = 4).
- **RQ5 terjawab di sini.** Lampiran A menjawab pertanyaan lanjutan yang berbeda: bila kurs tidak membantu, informasi apa yang
  membantu memprioritaskan pemantauan? Lampiran itu tidak mengubah jawaban RQ5.

## Eksplorasi E2 — Respons per rezim HET/HAP

145 sel (10 komoditas, 3–6 rezim, h 4/8/12, IDR/USD & harga dunia). Interval dikalibrasi terhadap 499 plasebo
geser-melingkar; 15 sel intervalnya tidak memuat nol, tetapi q BH minimum 0,145: tidak ada perbedaan antarrezim yang tahan
koreksi multiplisitas. Pola terkuat (eksploratif): bawang putih pada rezim Perbadan 12/2024, β_e(8) 3,74 (1,83..5,65;
98 minggu; sampel penuh −0,68), dan telur ayam pada rezim Perbadan 5/2022, ω(4) −0,89 (−1,47..−0,31; 78 minggu)
(`regime_profiles`).

## Kalibrasi inferensi (tingkat 2, analisis kepekaan sesudah G6)

**Mengapa ada.** Dua masalah inferensi ditemukan sesudah praregistrasi, dan arahnya berlawanan:
(1) bootstrap blok 13 minggu lebih pendek dari jendela LP (h + 6 minggu), sehingga rerata replikasi hanya 0,57 / 0,35 / 0,35
kali estimasi (median, h 4 / 8 / 12) dan interval resmi **terlalu lebar**; (2) SE cluster minggu **terlalu sempit**: di bawah
plasebo |t| > 1,96 terjadi pada 8,8% replikasi per sel nasional (maksimum 17,6%), bukan 5%. Kalibrasi plasebo memakai 499 replikasi
geser-melingkar (struktur harga dipertahankan, kaitan waktu penggerak diputus) sebagai distribusi null statistik t, lalu
interval = estimasi ± crit·SE dengan crit = max(1,96, kuantil plasebo).

**Uji ukuran di bawah null (leave-one-out).** Setiap replikasi plasebo diperlakukan sebagai "data asli" dan dinilai dengan
ambang dari replikasi lainnya, pada 48 sel nasional (β_e & ω, h 4/8/12; 499 replikasi untuk komoditas fokus, 199 untuk
lainnya; keluarga BH dinilai pada 199 replikasi yang memuat ke-48 sel).

| Metode | Positif palsu per sel di bawah null | Replikasi null dengan ≥ 1 temuan BH | Data asli: sel tidak memuat nol (dari 48) | Data asli: temuan BH q < 0,05 |
|---|---|---|---|---|
| ±1,96·SE cluster minggu | 8,8% (maks 17,6%) | 17,1% | 9 | 5 |
| Terkalibrasi plasebo | 4,4% (maks 4,8%) | 0,5% | 7 | 4 |
| Resmi praregistrasi | tidak dapat diuji (butuh bootstrap per replikasi) | – | 3 | – |

Sumber: `placebo_stats`, `profiles`, `national_calibrated`; `docs/audit/20261127_redflag_juri/`.

- Kalibrasi tidak memilih metode yang paling banyak memberi hasil signifikan. Kalibrasi lebih ketat dari ±1,96·SE (ambang lebih
  lebar pada 41 dari 48 sel; median crit 2,28, maksimum 2,74) dan ukurannya di bawah null tidak melebihi 5% (4,4%). Di bawah null,
  rata-rata 2,0 sel dan 0,01 temuan BH diharapkan; data asli memberi 7 sel dan 4 temuan.
- Klaim yang **hanya** bergantung pada tingkat 2: daging ayam β_e(8) (q 0,058) dan minyak goreng ω(8) (q 0,024). Klaim yang
  sudah didukung interval resmi: minyak goreng ω(4) dan ω(12), daging ayam β_e(4) (batas atas −0,00, di ambang).
- Hal yang sama tersedia untuk PT nasional (3 dari 30 sel tidak memuat nol; resmi 1) dan deviasi provinsi
  (`province_calibrated`). Interval resmi provinsi hampir selalu memuat nol (0–2,4% sel), ±1,96·SE terlalu longgar (6–17%),
  versi terkalibrasi 5–12%. Dengan koreksi BH atas seluruh 1.623 sel provinsi, 7 deviasi bertahan: daging ayam (Maluku, Papua,
  Kepulauan Riau), gula (Kalimantan Barat, Kalimantan Tengah), dan respons minyak goreng terhadap harga dunia (Maluku Utara).
  Ini deskriptif dan sejalan dengan uji heterogenitas (D-163).

## Robustness & validasi

- **Tier 1.** Estimasi baseline berada di dalam interval cek pada 366 dari 382 sel: lag 2/4/8 96/96, dekomposisi dolar
  global vs spesifik rupiah 78/78, frekuensi bulanan 47/48, h 8 vs 12 15/16, tanpa Mar–Jun 2020 & bulan Brent ekstrem 45/48,
  sub-periode sebelum/sesudah 2021-04-05 85/96 (`robustness`). Dari 16 pengecualian, 10 pada gula dan minyak goreng
  (besaran berbeda antar sub-periode) dan 3 pada daging ayam.
- **Tier 2.** Baseline berada di dalam interval cek pada 191 dari 193 sel: varian PIHPS lain dan komposit pakan
  alternatif 94/96, harga mingguan = observasi terakhir 48/48, Panel Harga Bapanas bulanan 42/42, keterpencilan alternatif
  (km ke hub tanpa log; km ke Jakarta saja) 6/6, dan ordinal jalur eksposur 1/1 (τ-b −0,03, −0,75..0,70). Dua pengecualian
  bertanda sama: Gula Kualitas Premium β_e(4) 0,36 (0,15..0,57) vs 0,69, dan Minyak Goreng Curah ω(8) 0,36 (0,26..0,45) vs
  kemasan 0,21. Minyak goreng curah lebih peka terhadap harga sawit dunia dalam rupiah.
- **V4 (LP vs event study).** Implikasi LP berada di dalam interval event pada 26 dari 30 sel, tetapi hanya 2 dari 30
  interval event yang tidak memuat nol dan kesamaan tanda antar episode 0,51; kecocokan ini lemah sebagai validasi.

## Validasi prospektif (sedang berjalan)

Karena periode uji 2024+ sudah dipakai berulang dalam eksplorasi (Lampiran A), satu-satunya cara memperoleh bukti
out-of-sample yang bersih adalah memprediksi minggu yang belum terjadi. Ini yang sudah dilakukan:

| Prediksi beku | Isi | Di-commit (sebelum target pertama 2026-11-27) |
|---|---|---|
| D-152 | C1-tuned & `IW_NAT`, 12 origin 2026-09-28..11-16, 8.112 baris | `ca53742`, 2026-11-25 21.41 WIB |
| D-158 | C1-tuned, `FR_REF`, `FR_CITY` | `ec6dd19`, 2026-11-26 20.45 WIB |
| D-164 | K4 risiko kenaikan material | `044873c`, 2026-11-27 09.53 WIB |
| D-167 | aturan & evaluator maju K4 (ambang gagal ditetapkan dari MDE) | `8c7677a`, 2026-11-27 10.28 WIB |

- **Yang dapat diperiksa juri sekarang.** `python docs/audit/20261127_prospective_validation/scripts/integrity_check.py`
  memeriksa bahwa sha256 setiap berkas prediksi dan evaluator sama dengan manifest dan dengan commit sebelum target ada (keluar 0
  bila utuh; hasil 2026-11-27: semua pemeriksaan wajib lolos). Hash D-152/D-158 dihitung pada berkas CRLF, sehingga verifikasi
  byte butuh checkout dengan `core.autocrlf=true`.
- **Jadwal.** Putaran interim ≥ 2026-11-29 (1 origin per horizon), lalu 2026-12-20 (h = 4 lengkap) dan 2027-01-17 (h = 8 lengkap),
  sesudah masa penjurian. Hasil interim tidak dibaca sebagai konfirmasi.
- **Daya.** Data maju hanya dapat menandai kegagalan besar (Δ macro F1 < −0,08 / −0,04; ΔAP K4 < −0,14). Keuntungan kecil
  pada periode uji 2024+ tidak dapat dikonfirmasi dengan 4–8 origin mingguan yang tumpang tindih.
- Prediksi maju hanya untuk tingkat 3. Hasil tingkat 1 (praregistrasi) tidak membutuhkannya.

## Dataset turunan

Kontribusi data proyek ini bukan sumber baru, melainkan panel turunan yang terintegrasi dan terdokumentasi: harga eceran
mingguan 34 provinsi × 10 komoditas × 464 minggu dengan status setiap sel (teramati, carry-forward, pendek, hilang), harga dunia
padanan dalam rupiah dengan tanggal ketersediaan (as-of), daftar 13 episode depresiasi, serta tabel buatan tim: konkordansi
PIHPS–HS–Pink Sheet–FAOSTAT, rasio impor per komoditas, riwayat HET/HAP bertanggal dan berstatus verifikasi, dan fitur provinsi
(keterpencilan, kecukupan beras, jumlah kota sampel). Rincian, hak redistribusi, dan keterbatasan: `docs/DATASHEET.md`.

## Keterbatasan

- **Inferensi.** Interval resmi cenderung terlalu lebar (bootstrap menarik β ke nol) dan ±1,96·SE terlalu sempit; lihat bagian
  Kalibrasi inferensi. Karena SE cluster terlalu sempit, MDE untuk komoditas volatil (cabai, bawang merah, telur) cenderung
  optimistis.
- **Task 4.** Evaluasi pseudo-real-time (vintage revisi tidak tersedia). M1 adalah satu ridge untuk 10 komoditas tanpa
  identitas komoditas (bulan sebagai angka 1–12). Dua pemeriksaan kepekaan memberi kesimpulan yang sama: ridge per komoditas,
  dan ridge dengan dummy bulan + dummy minggu sekitar Idulfitri (M2/M1 1,005 pada h = 4 dan 1,019 pada h = 8; H5 Holm 0,56).
  Pada pemeriksaan kedua, M1 makin tertinggal dari model tanpa perubahan (M0/M1 0,95 dan 0,97), sehingga keterbatasan utama
  baseline adalah pengumpulan lintas komoditas, bukan penyandian musim.
- **Eksplorasi Task 4.** Lihat Lampiran A: periode uji 2024+ dipakai berulang, TimesFM mungkin terkontaminasi data uji, dan
  kebutuhan pengguna belum divalidasi.
- **Harga diatur.** Banyak minggu tanpa perubahan harga untuk komoditas yang diatur (beras 92%, daging sapi 90%, gula 85%,
  minyak goreng 87% sel carry-forward). Ini kekakuan harga nyata, bukan data hilang, dan membatasi respons yang teramati.
- **Cakupan.** Kesimpulan berlaku untuk 10 komoditas, 34 provinsi (kerangka lama), dan periode 2018–2026.

## Lampiran A — Eksplorasi Task 4 (tingkat 3, sesudah praregistrasi)

*Analisis tambahan sesudah praregistrasi (D-139 s.d. D-167). Tidak menggantikan uji H5 dan tidak menjawab RQ yang
didaftarkan. Pertanyaannya: bila kurs tidak membantu memprediksi, informasi apa yang membantu TPID memprioritaskan pemantauan?
Semua angka berasal dari evaluasi bersyarat pseudo-real-time dengan origin dan baris uji yang sama dengan M0–M3. Interval 95%
dari bootstrap blok origin (unit = origin, karena seri dalam satu origin berbagi guncangan nasional). Perbandingan dikoreksi
Benjamini–Hochberg per keluarga (D-143); hasil yang tidak lolos koreksi ditulis "tidak terbukti".*

### A.1 Pemakaian periode uji 2024+

Periode 2024+ bukan data uji yang bersih. Origin 2024+ sudah terlihat sebelum pemisahan pengembangan/uji dibuat (D-139, D-141,
D-142 menilai seluruh 2021–2026), lalu dibuka lagi untuk lima perbandingan dan satu laporan deskriptif:

| Pembukaan | Yang dinilai | Selisih h = 4 / h = 8 | p Holm atas 10 perbandingan |
|---|---|---|---|
| D-145 | C1-tuned − TimesFM, macro F1 | +0,059 / +0,053 | 0,008 / 0,008 |
| D-146 | target 3 kelas (deskriptif, tanpa pembanding) | macro F1 0,625 / 0,606 | – |
| D-147 | `iw_gap` − C1-tuned, macro F1 | +0,004 / +0,005 | 1,0 / 0,45 |
| D-151 | `IW_NAT` − C1-tuned, macro F1 | +0,0085 / +0,0033 | 1,0 / 1,0 |
| D-154 | presisi daftar pantau C1-tuned − aturan naif | +0,094 / +0,072 | < 0,001 / 0,004 |
| D-164 | average precision K4 − C1-tuned | +0,045 / +0,015 | 0,045 / 1,0 |

p dari q BH yang dilaporkan (konservatif, p ≤ q) atau dari interval bootstrap (pendekatan normal);
`docs/audit/20261127_redflag_juri/hasil/buku_besar_test.csv`.

- Seleksi model, fitur, hyperparameter, dan threshold selalu dilakukan pada origin pengembangan (target ≤ 2023). Pemilihan keluarga
  fitur tetap dipengaruhi eksplorasi seluruh periode sebelumnya, jadi angka 2024+ adalah evaluasi eksploratif, bukan out-of-sample.
- Bila kesepuluh perbandingan diperlakukan sebagai satu keluarga, yang tetap lolos Holm hanyalah C1-tuned > TimesFM, daftar pantau
  > aturan naif (kedua horizon), dan K4 pada h = 4 (tipis, p Holm 0,045). Kandidat lain yang diuji hanya di origin pengembangan
  (195 baris di `docs/eksperimen_registry.csv`, termasuk semua yang gagal) tidak pernah membuka periode uji.

### A.2 Arah perubahan dari ramalan regresi dan klasifier langsung

**Ramalan regresi.** Akurasi arah M1 dan M2 tidak berbeda dari selalu menebak arah terbanyak: selisih h = 8 M1 +0,015
(−0,029..0,053), M2 +0,022 (−0,019..0,054). M3 di atas baseline: +0,058 (0,024..0,091). Pada komoditas yang harganya kaku (beras,
daging sapi, gula, minyak goreng; ≥ 50% minggu tanpa perubahan), M1 berada di bawah baseline (−0,100, q 0,013); M3 (−0,054,
q 0,077) dan M2 (−0,053, q 0,17) tidak lolos koreksi.

**Klasifier arah langsung (HistGradientBoostingClassifier).** Dilatih langsung untuk naik/turun dengan fitur yang sama: akurasi
arah h = 8 0,620 dengan fitur kurs (C2) dan 0,607 tanpa (C1), di atas baseline 0,545 (selisih C2 +0,075, 0,038..0,110). Fitur kurs
tidak terbukti menambah akurasi: C2 − C1 +0,012 (−0,004..0,030).

### A.3 Model deep learning dan foundation model

| Model | MAE / M1, h = 4 | MAE / M1, h = 8 | Akurasi arah h = 8 |
|---|---|---|---|
| TimesFM 3.0 zero-shot | 0,935 (DM p < 0,001) | 0,895 (DM p < 0,001) | 0,623 |
| TimesFM 3.0 + kovariat kurs & harga dunia | 0,939 (DM p 0,001) | 0,904 (DM p < 0,001) | 0,613 |
| PatchTST | 0,998 (DM p 0,92) | 0,962 (DM p 0,15) | 0,596 |
| TSMixer | 0,995 (DM p 0,77) | 0,966 (DM p 0,13) | 0,608 |
| TSMixer + kurs & harga dunia | 1,036 (DM p 0,16) | 0,994 (DM p 0,84) | 0,601 |

Rasio < 1 = lebih akurat dari M1. Baseline akurasi arah h = 8 = 0,545.

- TimesFM 3.0 tanpa pelatihan pada data kami menurunkan MAE terhadap M1 sebesar 6,5% (h = 4) dan 10,5% (h = 8); porsi variasi
  perubahan harga yang terjelaskan naik dari 0,07 menjadi 0,25 (h = 8). TimesFM 3.0 dirilis September 2026 dan dilatih pada
  korpus deret waktu publik yang isinya tidak kami ketahui. Bila deret harga pangan Indonesia 2021–2026 ikut di dalamnya,
  keunggulan ini adalah batas atas. Keunggulan yang lebih kecil pada origin 2026 (MAE/M1 0,938; 2023: 0,876; 2024: 0,834) konsisten
  dengan kemungkinan itu, tetapi tidak membuktikannya. Bobotnya (1,32 GB) berlisensi non-komersial dan tidak ikut paket juri.
- Kurs dan harga dunia tetap tidak menambah akurasi: TimesFM dengan kovariat kurs vs tanpa, rasio MAE 1,005 (h = 4) dan 1,010
  (h = 8), keduanya tidak nyata; TSMixer dengan kanal kurs vs tanpa 1,041 (h = 4, DM p 0,020, tidak lolos BH, q 0,057) dan 1,029
  (h = 8). Hasil ini sejalan dengan H5.
- Pada komoditas berharga kaku, PatchTST dan TSMixer (± kurs) berada di bawah baseline arah (q 0,018–0,049 pada h = 8);
  TimesFM −0,074 tidak lolos koreksi (q 0,053). Tidak ada model yang lebih baik dari menebak arah terbanyak untuk kelompok ini.
- **Kualitas klasifikasi arah (h = 8).** F1 makro tertinggi TimesFM 0,623, lalu klasifier C2 0,617, C1 0,605, TSMixer 0,604
  dan M3 0,596 (M1 0,551). Semua dihitung pada baris dengan perubahan harga ≠ 0 (cakupan 90,7%); bila minggu tanpa perubahan
  dihitung salah, akurasi TimesFM 0,566 dan M1 0,508. Kemampuan memisahkan naik/turun masih lemah (ROC-AUC ≤ 0,70, MCC ≤ 0,26).
- **Kestabilan.** Tiga seed PatchTST/TSMixer: rentang akurasi arah ≤ 0,03 dan MAE/M1 ≤ 0,02; TSMixer + kurs lebih buruk dari
  TSMixer di ketiga seed (MAE/M1 0,995 ± 0,009 vs 0,966 ± 0,007, h = 8). Keputusan "lebih baik / tidak terbukti / lebih buruk" sama
  untuk panjang blok bootstrap 2, 3, 4, dan 6 origin; DM TimesFM vs M1 tetap p < 0,001 untuk lag HAC 1–5.
- Perbandingan yang lolos koreksi BH: MAE TimesFM (± kurs) vs M1 pada h = 4 dan 8 (q ≤ 0,004); akurasi arah TimesFM (± kurs) vs M3
  pada h = 4 (+0,041 dan +0,045, q 0,020); C1 vs M1 pada h = 4 dan 8 (+0,045 dan +0,047, q ≤ 0,030). C2 vs M3 pada h = 4 tidak lagi
  lolos setelah perbaikan flag episode real-time (+0,013, q 0,36; D-162). Tidak ada perbandingan "dengan kurs vs tanpa kurs" yang lolos.

### A.4 Klasifier arah teroptimasi (C1-tuned) dan daftar pantau

Klasifier arah dengan fitur dinamika harga per seri (lag panjang, momentum, volatilitas, musiman, deviasi dari rata-rata
bergerak dan dari provinsi lain, sinyal nasional komoditas) dipilih hanya pada origin pengembangan, lalu dinilai pada origin
≥ 2024 (37 / 36 origin): F1 makro 0,677 (0,652..0,698) pada h = 4 dan 0,680 (0,653..0,706) pada h = 8, di atas TimesFM pada origin
yang sama (+0,059 dan +0,053). Versi dengan fitur kurs tidak menambah. Sumber informasi lain yang diuji di origin pengembangan
tidak memberi perbaikan yang terbukti: harga pedagang besar dan produsen PIHPS, harga dalam-minggu (D-150–D-152), 27 kandidat
fitur/threshold/bobot/algoritma (D-156), cuaca sentra produksi dan realisasi impor (D-157), harga 110 kota (D-158), prakiraan
cuaca NOAA CFSv2 (D-161), dan intensitas berita GDELT (D-165). Galat yang tersisa terutama pada perubahan harga kecil dan
pergeseran porsi kenaikan antarperiode.

Bagi pengguna seperti TPID, pertanyaannya adalah komoditas mana di provinsinya yang perlu diprioritaskan 4–8 minggu ke depan.
Kriteria ditetapkan sebelum pengukuran. *Kenaikan material* = perubahan rerata harga minggu t + h terhadap minggu t yang termasuk
20% perubahan terbesar komoditas itu pada data latih (mis. ≥ 1,6% untuk beras dan ≥ 50% untuk cabai rawit pada h = 4). Ini
materialitas statistik di titik akhir horizon, bukan ambang kebijakan dan bukan kejadian kapan pun dalam 4–8 minggu. *Daftar
pantau* = 2 komoditas per provinsi per minggu dengan skor tertinggi, dari semua komoditas yang datanya tersedia saat itu.
Skornya adalah peluang arah naik, bukan peluang kenaikan material, sehingga hasil ini menilai kualitas urutan prioritas.
*Pembanding* = empat aturan tanpa model (tren 4 minggu provinsi, tren nasional, posisi terhadap rata-rata 13 minggu, pola periode
yang sama tahun lalu); yang terbaik di pengembangan menjadi pembanding resmi.

| Origin ≥ 2024 (evaluasi eksploratif, kriteria ditetapkan sebelumnya) | h = 4 | h = 8 |
|---|---|---|
| Presisi daftar pantau C1-tuned | 0,18 (0,13..0,23) | 0,16 (0,11..0,21) |
| Aturan sederhana pembanding | 0,085 (tren provinsi) | 0,089 (tren nasional) |
| Selisih | +0,094 (0,055..0,132) | +0,072 (0,034..0,115) |
| Laju-dasar kenaikan material | 0,088 | 0,089 |
| Porsi kenaikan material yang tertangkap | 0,41 | 0,36 |
| F1 makro arah pada baris yang ternyata bergerak material (aturan tanda tren) | 0,81 (0,50) | 0,81 (0,44) |
| Kalibrasi peluang arah: Brier skill terhadap klimatologi komoditas / ECE | 0,17 / 0,010 | 0,17 / 0,021 |

- Daftar pantau berbasis pola historis memuat kenaikan material sekitar dua kali lebih sering daripada pilihan acak (2,0× / 1,8×),
  sedangkan aturan tren sederhana tidak lebih baik dari acak. Pada periode uji, aturan terbaik justru "kembali ke rata-rata"
  (0,11 / 0,12); C1-tuned tetap di atasnya sebagai analisis kepekaan: +0,066 (0,033..0,101) / +0,041 (0,003..0,078).
- Pembanding "pantau komoditas yang paling sering naik material di masa lalu" (laju-dasar komoditas): pada h = 4 daftar C1-tuned
  lebih presisi (0,18 vs 0,10; +0,082, 0,050..0,120). Pada h = 8 keunggulannya tidak terbukti (+0,019, −0,027..0,081; pengembangan
  −0,026). Aturan itu hampir selalu menandai beras, gula, minyak goreng, atau daging sapi yang sama setiap minggu (D-164).
- Sekitar 1 dari 6 komoditas yang ditandai benar-benar naik material. Daftar ini cocok untuk memprioritaskan pemantauan dan
  pemeriksaan (data harga, stok, informasi pendukung), bukan memicu intervensi otomatis. Anggaran 1 / 2 / 3 komoditas per provinsi
  memberi presisi 0,21 / 0,18 / 0,16 dan recall 0,24 / 0,41 / 0,54 (h = 4).
- Sekitar 57% alarm jatuh pada beras, gula, minyak goreng, dan daging sapi, yang ambang material statistiknya hanya 1,4–2,7%
  (h = 4). Prioritas kebijakan TPID mungkin berbeda; materialitas kebijakan perlu ditetapkan bersama pengguna.
- Arah pada baris material dan kalibrasi adalah ukuran bersyarat: yang pertama dihitung pada baris yang *ternyata* bergerak
  material, yang kedua mengkalibrasi peluang arah, bukan peluang kenaikan material. Kelemahan klasifier ada pada perubahan kecil
  (F1 makro kuintil |perubahan| terkecil ± 0,57). Pada 25% prediksi paling yakin setiap minggu, akurasi arah 0,83 (h = 4) dan
  0,81 (h = 8).
- Di origin pengembangan kriteria yang sama lolos (selisih presisi +0,110 / +0,067), kecuali kalibrasi h = 8 yang gagal tipis
  (ECE 0,056 > 0,05). Kalibrasi ulang walk-forward menurunkan ECE di bawah 0,05 tetapi tidak memperbaiki Brier, sehingga tidak
  dipakai (D-163).

### A.5 Risiko kenaikan material sebagai target tersendiri (K4, D-164)

Klasifier dengan fitur & hyperparameter C1-tuned dilatih langsung pada target "kenaikan material" (definisi di atas, semua minggu
termasuk yang harganya tidak berubah). Kriteria ditetapkan sebelum pengukuran. Pada origin ≥ 2024 klasifier ini mengurutkan risiko
lebih baik daripada skor arah pada h = 4: average precision 0,24 vs 0,19 (selisih +0,045, 0,017..0,083) dan presisi daftar pantau
2 komoditas per provinsi 0,20 vs 0,18 (+0,023, 0,003..0,047). Peluangnya terkalibrasi (ECE 0,02). Pada h = 8 arahnya sama (+0,015
dan +0,012), tetapi interval memuat nol dan peluang tinggi terlalu yakin. Keputusan: PARTIAL (urutan dipakai secara eksploratif,
angka peluang h = 8 tidak). Pada ambang seragam 5% / 10% skor ini kalah dari C1-tuned (D-166), sehingga pilihan model bergantung
pada ambang yang dipakai pengguna.

### A.6 Keterbatasan eksplorasi

- Periode uji 2024+ dipakai berulang (A.1); hanya validasi prospektif yang memberi bukti out-of-sample bersih.
- Kebutuhan TPID (jumlah komoditas yang dapat dipantau, toleransi alarm palsu, ambang kenaikan yang relevan, waktu persiapan)
  belum divalidasi dengan pengguna (U109); belum ada bukti bahwa daftar ini memperbaiki keputusan operasional. Dengan presisi di
  bawah 0,5, daftar pantau apa pun hanya bernilai bila kenaikan yang terlewat jauh lebih mahal daripada pemeriksaan yang tidak
  perlu (≥ ± 3–5×). Penggunaan operasional menunggu ambang kebijakan dan kapasitas pemantauan dari pengguna.
- Pemeriksaan kebocoran membuktikan fitur tidak membaca observasi masa depan, tetapi efek revisi data PIHPS (H+1) tidak dapat
  diuji karena data vintage tidak tersedia. "Material" relatif per komoditas dan diukur di titik akhir horizon.

## Sumber angka

`eligibility`, `episodes`, `mde` (Tahap 0); `profiles`, `events`, `placebo_stats` (Task 1); `heterogeneity`, `cluster_selection`,
`partition_compare`, `planted_recovery` (Task 2); `assoc`, `asymmetry`, `regime_profiles`, `national_calibrated`, `province_calibrated`
(Task 3); `forecast_eval` (Task 4); `robustness`. Batas Rupiah, uji ukuran kalibrasi, dan buku besar periode uji:
`docs/audit/20261127_redflag_juri/` (membaca artefak resmi, tidak menulis ke `results/`). Lampiran A: `forecast_preds`,
`direction_preds`, `deep_preds`, log evaluasi Task 4 di `logs/evaluations/` (app halaman 7), `direction_tuned_preds` (tidak dikirim;
dibangun ulang dengan `python -m kagami task4 --direction-tuned`), definisi & kriteria di D-145, D-154, D-164 (`docs/DECISIONS.md`).
Validasi prospektif: `docs/audit/20261127_prospective_validation/`. Rambu klaim: CLAUDE.md §20.
