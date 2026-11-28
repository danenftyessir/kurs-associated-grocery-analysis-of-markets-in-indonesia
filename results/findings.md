# Temuan KAGAMI

Laporan ini merangkum temuan dari dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia): harga eceran mingguan
10 komoditas di 34 provinsi, 2018-01-01 sampai pembekuan 2026-11-21. Sebanyak 337 dari 340 seri layak dianalisis. Semua hasil
bersifat asosiasional. KAGAMI tidak meramal kurs dan tidak mengamati rantai pasok. Respons yang tidak terdeteksi kami baca sebagai
batas atas kepekaan. KAGAMI masih prototipe riset untuk mendukung keputusan, dan kebutuhan penggunanya (TPID) belum kami validasi,
sehingga belum siap dipakai sebagai peringatan dini.

### Cara membaca angka

Respons harga ditulis $\beta_e(h)$, yaitu perubahan kumulatif log harga eceran $h$ minggu setelah log kurs rupiah per dolar AS
naik 1. Angkanya kira-kira sama dengan persen perubahan harga untuk setiap 1% pelemahan rupiah. Model mengendalikan lag
perubahan harga, harga Brent, musim bulanan, minggu sekitar Idulfitri, dan efek tetap seri. $\omega(h)$ adalah respons yang sama
terhadap harga dunia padanan dalam rupiah. Penerusan kurs dihitung sebagai $PT(h) = \beta_e(h)/\gamma(h)$, dengan $\gamma(h)$
respons kurs terhadap dirinya sendiri. Angka dalam kurung seperti (0,02..0,28) adalah interval 95%.

Nama hipotesis mengikuti praregistrasi. H0-Het menguji perbedaan respons antarprovinsi, H2 asimetri antara pelemahan dan
penguatan rupiah, H3 keterpencilan provinsi, dan H5 nilai prediktif kurs. E1 (porsi impor) dan E2 (periode HET/HAP) deskriptif.

### Tiga tingkat bukti

Setiap angka di laporan ini termasuk salah satu dari tiga tingkat bukti, dan kami selalu menyebut tingkatnya.

| Tingkat | Isi | Status |
|---|---|---|
| 1. Praregistrasi | Uji konfirmatori H0-Het, H2, H3, dan H5, serta analisis deskriptif E1 dan E2 yang sudah didaftarkan. Interval **resmi** adalah yang lebih lebar antara $\pm 1{,}96 \cdot SE$ cluster minggu dan persentil bootstrap blok 13 minggu | Dibekukan di gerbang G6 (2026-11-20), sebelum estimasi $\beta$ dilihat |
| 2. Kepekaan inferensi | Interval **terkalibrasi plasebo** | Ditambahkan sesudah G6. Ukurannya kami uji di bawah null (bagian Kalibrasi inferensi) |
| 3. Eksploratif | Semua model dan klasifier arah Task 4 sesudah praregistrasi (Lampiran A) | Tidak menguji hipotesis. Periode uji 2024+ sudah dipakai berulang |

Bukti out-of-sample yang bersih untuk tingkat 3 hanya bisa datang dari validasi prospektif, yang sedang berjalan.

## Ringkasan

1. Di antara 10 komoditas yang diamati, respons nasional harga eceran terhadap kurs rupiah sebagian besar tidak terdeteksi.
   Asosiasi yang paling konsisten ada pada minyak goreng dan harga sawit dunia dalam rupiah. Menurut interval resmi,
   $\omega(4)$ = 0,16 (0,02..0,28) dan $\omega(12)$ = 0,31 (0,02..0,47), sedangkan $\omega(8)$ = 0,21 (−0,01..0,36) masih memuat
   nol. Tandanya positif di semua pemeriksaan Tier 1.
2. Respons yang berbeda antarprovinsi melebihi derau hanya pada telur ayam (q 0,04) dan daging ayam (q 0,050, tepat di ambang).
   Provinsi tidak membentuk kelompok (k = 1). Untuk struktur buatan yang kami uji, yaitu 2–3 kelompok provinsi berukuran hampir
   sama, selisih respons RMS ≥ 0,2 per fitur terdeteksi pada ≥ 96% replikasi. Bentuk struktur lain belum diuji.
3. Kami tidak menemukan asimetri antara pelemahan dan penguatan rupiah. Uji konfirmatori H2 untuk beras dan daging sapi tidak
   menolak hipotesis nol.
4. Di antara 10 komoditas, rasio impor langsung tidak berasosiasi monoton dengan PT(8) ($\tau_b$ −0,045, p eksak 0,93).
   Keterpencilan provinsi juga tidak berasosiasi dengan respons 4 minggu (h = 4), sehingga H3 tidak didukung.
5. Dalam evaluasi bersyarat pseudo-real-time pada 76 origin 2021–2026, fitur kurs dan harga dunia tidak menurunkan MAE prediksi
   4 dan 8 minggu. MAE justru sedikit naik: rasio M2/M1 1,009 dan 1,013, dengan statistik DM −2,70 dan −2,29 (p dua sisi 0,009 dan
   0,025). Untuk hipotesis "M2 lebih akurat", p satu sisi 0,996 dan 0,987. H5 tidak didukung.
6. Hasil nol tetap memberi batas yang berguna bagi TPID. Untuk 6 dari 10 komoditas, yaitu beras, daging sapi, daging ayam, minyak
   goreng, telur, dan gula dengan batas yang lebih longgar, kenaikan harga eceran nasional 8 minggu yang berasosiasi dengan
   pelemahan rupiah 5% dan melebihi batas atas interval 95% dapat dikesampingkan. Batas atas itu +0,25% sampai +4,65%, atau +Rp89
   sampai +Rp938 per kg atau liter, tergantung komoditas. Intervalnya tidak simetris, dan batas bawahnya ada di tabel bagian
   berikut. Lonjakan yang lebih besar dari batas atas tidak konsisten dengan asosiasi kurs historis dan perlu ditelusuri ke faktor
   lain. Untuk cabai dan bawang, data tidak cukup presisi untuk memberi batas yang berguna.
7. Analisis eksploratif di Lampiran A, yang tidak menguji hipotesis, menunjukkan bahwa pola harga sendiri lebih informatif
   daripada kurs. Klasifier arah berbasis dinamika harga dapat menyusun daftar pantau komoditas per provinsi yang memuat kenaikan
   harga material sekitar dua kali laju-dasar. Fitur kurs tidak menambah akurasi pada model mana pun.

### Jawaban sementara atas pertanyaan pemandu

Dalam sampel 10 komoditas, estimasi respons nasional berbeda-beda antarkomoditas, dari −1,67 (daging ayam) sampai 1,37 (cabai
merah) pada h = 8, dengan sebagian besar interval memuat nol. Heterogenitas antarprovinsi yang melampaui distribusi plasebo hanya
terdeteksi pada telur ayam dan daging ayam, dan provinsi tidak membentuk kelompok (k = 1). Kami tidak melakukan dekomposisi
varians formal, jadi temuan ini belum membuktikan bahwa komoditas lebih menentukan daripada lokasi. Yang kami amati adalah variasi
titik estimasi antarkomoditas dan heterogenitas provinsi yang jarang terdeteksi, dengan daya deteksi yang berbeda.

## Makna bagi pengguna: batas atas dalam Rupiah

Hasil nol tetap berguna bila diterjemahkan ke batas atas dalam Rupiah. Tabel berikut memakai PT(8) nasional dengan interval
**resmi**. Harga acuan adalah median antarprovinsi dari rerata harga teramati 8 minggu sampai 2026-11-16.

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

Angka ini skenario bersyarat dari pola historis, bukan ramalan. Rumusnya: perubahan = $\exp(PT(8) \cdot \ln 1{,}05) - 1$.
Sumber: `profiles` dan `panel_weekly`. Perhitungannya, termasuk untuk h = 4, ada di `docs/audit/20261127_redflag_juri/`.

### Cara memakai tabel ini

Misalkan harga beras naik Rp500/kg dalam 8 minggu setelah rupiah melemah 5%. Bagian yang konsisten dengan asosiasi kurs historis
paling banyak sekitar +Rp89/kg, yaitu batas atas interval 95%. Interval lengkapnya −Rp170..+Rp89/kg dan tidak simetris. Sisa
kenaikan yang tidak dijelaskan asosiasi kurs perlu ditelusuri ke faktor lain, seperti pasokan, musim, kebijakan, atau faktor yang
tidak teramati. Hasil nol tidak mengidentifikasi penyebab lain itu. Angka ini hanya mengarahkan penelusuran.

### Harga dunia untuk minyak goreng

Kenaikan harga sawit dunia dalam rupiah sebesar 10% berasosiasi dengan kenaikan harga minyak goreng kemasan +1,5% (+0,2..+2,7%)
pada h = 4, atau sekitar +Rp350/liter (+Rp37..+Rp620). Interval resmi ini tidak memuat nol. Pada h = 8 asosiasinya +2,0%
(−0,1..+3,5%). Untuk minyak goreng, TPID lebih tepat memantau harga sawit dunia dalam rupiah daripada kurs itu sendiri.

Angka di bagian ini berlaku nasional. Di tingkat provinsi, variasi di atas derau hanya terdeteksi pada telur dan daging ayam.

## Pertanyaan 1 — Respons nasional per komoditas

| Komoditas | Jalur | $\beta_e(8)$ resmi | PT(8) resmi | $\omega(8)$ resmi |
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

Satuan: perubahan log harga per 1 perubahan log penggerak, kira-kira persen per 1%. Sumber: `profiles` (nasional).

### Batas atas yang dapat dikesampingkan

Untuk beras, penerusan PT(8) di atas 0,11 dapat dikesampingkan, dan untuk daging sapi di atas 0,13. Interval cabai dan bawang
sangat lebar (MDE PT(8) 1,84–3,75), sehingga hasil nol untuk komoditas itu hampir tidak informatif.

### Minyak goreng dan harga sawit dunia

| $\omega(h)$ | Estimasi | Interval resmi | Interval terkalibrasi plasebo (tingkat 2) | q |
|---|---|---|---|---|
| h = 4 | 0,16 | 0,02..0,28 | 0,04..0,28 | 0,092 |
| h = 8 | 0,21 | −0,01..0,36 | 0,08..0,34 | 0,024 |
| h = 12 | 0,31 | 0,02..0,47 | 0,16..0,46 | 0,024 |

Pada h = 8, semua cek Tier 1 memberi interval di atas nol. Asosiasinya lebih kecil sebelum April 2021, yaitu 0,07 (0,03..0,10),
dibanding sesudahnya, yaitu 0,22 (0,06..0,37).

### Daging ayam dan kurs rupiah

Kenaikan kurs rupiah per dolar AS berasosiasi dengan penurunan harga daging ayam. Arah ini berlawanan dengan dugaan jalur input
impor, dan asosiasinya tidak tahan semua pemeriksaan.

| Respons | Estimasi | Interval resmi | Interval terkalibrasi plasebo | q |
|---|---|---|---|---|
| $\beta_e(4)$ | −1,16 | −1,86..−0,00 | −2,10..−0,23 | 0,024 |
| $\beta_e(8)$ | −1,67 | −2,61..0,05 | −2,77..−0,58 | 0,058 |

Tanpa Mar–Jun 2020 dan bulan Brent ekstrem, estimasinya menjadi −0,96 (−2,05..0,14), dan pada frekuensi bulanan −0,60
(−1,33..0,13). Komponen kurs yang spesifik rupiah memberi −1,89 (−3,02..−0,76), jadi asosiasinya tidak semata mengikuti
pergerakan dolar global.

### Gula pada 4 minggu

Kami tidak menafsirkan $\beta_e(4)$ gula sebagai temuan. Estimasi 0,69 lolos kalibrasi plasebo (0,25..1,13, q 0,024), tetapi
berubah menjadi −0,03 tanpa Mar–Jun 2020 dan −0,03 sesudah April 2021 (`robustness`).

### Studi peristiwa

Dari 390 sel nasional (13 episode × 10 komoditas × h 4/8/12), 19 sel (4,9%) memiliki p plasebo < 0,05. Jumlah ini setara dengan
yang diharapkan dari kebetulan. Tidak ada respons episode yang dapat dibedakan dari jendela plasebo.

## Pertanyaan 2 — Komoditas atau lokasi?

| Komoditas | Q | $\tau^2$ | $I^2$ | p plasebo | q BH |
|---|---|---|---|---|---|
| Telur ayam | 161,7 | 0,226 | 0,80 | 0,004 | 0,040 |
| Daging ayam | 132,6 | 0,456 | 0,75 | 0,010 | 0,050 |
| Gula pasir | 81,0 | 0,031 | 0,59 | 0,020 | 0,067 |
| Bawang merah | 92,5 | 0,592 | 0,64 | 0,095 | 0,238 |
| Cabai merah | 57,8 | 1,013 | 0,43 | 0,265 | 0,530 |
| Beras | 39,7 | 0,002 | 0,17 | 0,380 | 0,633 |
| Bawang putih, cabai rawit, daging sapi, minyak goreng | 18,5–31,3 | 0 | 0 | 0,64–0,98 | 0,92–0,98 |

Uji H0-Het pada h = 8 terhadap kurs rupiah, 34 provinsi (cabai rawit 31). Sumber: `heterogeneity`.

H0-Het ditolak untuk telur ayam dan daging ayam. Penolakan daging ayam tepat di ambang: 5 dari 499 plasebo melampaui Q asli,
dengan galat Monte Carlo p sekitar 0,004. Karena itu kami menyebutnya penolakan rapuh. Korelasi rata-rata deviasi provinsi
antarkomoditas $\bar\rho$ = 0,094 (p plasebo 0,198).

Untuk empat komoditas $\tau^2$ = 0, sehingga semua provinsi disusutkan ke respons nasional. Ini hasil yang sah. Sebagai
pemeriksaan, $\tau^2$ REML memberi angka yang sejalan: telur ayam 0,283, daging ayam 0,676, gula 0,031, dan nol (atau < 0,001)
untuk empat komoditas yang sama.

### Pengelompokan provinsi

Silhouette Ward maksimum 0,184 (k = 3) berada di bawah persentil 95 plasebo, yaitu 0,196. Jadi k = 1 dan tidak ada struktur
regional yang terdeteksi. Perbandingan dengan zona HET, Jawa dan luar Jawa, kuantil jumlah kota sampel, dan 7 wilayah tidak
berlaku karena k = 1 (`partition_compare`).

### Batas deteksi

Struktur buatan dengan selisih respons RMS 0,2 per fitur kami temukan kembali pada 99,5% (k = 2) dan 96,5% (k = 3) replikasi.
Selisih 0,1 hanya tertangkap pada 43% dan 13% replikasi (`planted_recovery`). Dalam struktur buatan itu, provinsi dibagi acak ke
2–3 kelompok berukuran hampir sama, dan pusat kelompok berbentuk simpleks berorientasi acak sehingga selisihnya tersebar di semua
fitur. Struktur ditanam pada deviasi plasebo, lalu diproses persis seperti data asli.

Struktur berbentuk ini dengan selisih ≥ 0,2 dapat dikesampingkan. Bentuk lain belum diuji dan bisa lolos dari deteksi walaupun
selisihnya ≥ 0,2, misalnya kelompok kecil atau tidak seimbang, gradien geografis, atau perbedaan pada sebagian komoditas saja.

### Arti bagi pengguna

Tanpa kelompok provinsi yang terdeteksi, belum ada dasar untuk peta tipologi kepekaan regional. Profil nasional per komoditas
adalah titik awal yang wajar di semua provinsi, kecuali untuk telur dan daging ayam.

## Pertanyaan 3 — Pelemahan dibanding penguatan rupiah

| Komoditas | Status | $\beta^{+} - \beta^{-}$ (8) | p Wald | p plasebo |
|---|---|---|---|---|
| Beras | konfirmatori | −0,14 (−0,58..0,47) | 0,49 | 0,62 |
| Daging sapi | konfirmatori | −0,26 (−0,88..0,21) | 0,089 | 0,28 |
| Bawang putih | deskriptif | −5,78 (−10,23..3,14) | 0,011 | 0,022 |
| 7 komoditas lain | deskriptif | semua interval memuat nol | 0,11–0,87 | 0,16–0,88 |

Sumber: `asymmetry`. Interval yang dilaporkan adalah gabungan interval Wald dan persentil bootstrap.

H2 tidak ditolak untuk beras dan daging sapi, dua komoditas yang MDE asimetri PT(8)-nya ≤ 0,5 (0,44 dan 0,32). Asimetri PT(8) di
atas 0,44 untuk beras dan di atas 0,32 untuk daging sapi akan terdeteksi dengan daya 80%. Bawang putih punya p plasebo 0,022,
tetapi nilai ini tidak bertahan koreksi atas 10 uji deskriptif, jadi kami tidak menyebutnya asimetri.

## Pertanyaan 4 — Karakteristik yang berasosiasi dengan respons

### Porsi impor

Di antara 10 komoditas yang diamati, korelasi peringkat Kendall $\tau_b$ antara PT(8) dan rasio impor langsung adalah −0,045
(jackknife −0,65..0,56), dengan p permutasi eksak 0,93 (`assoc`). Ini analisis deskriptif E1.

Mutu rasio impor tidak setara antarkomoditas. Sebagian besar berasal dari FAOSTAT 2018–2023, sedangkan telur dan cabai memakai
tahun yang lebih sedikit. Bawang putih memakai impor BPS dan Comtrade serta produksi ATAP satu tahun (2021) tanpa ekspor, karena
FAOSTAT tidak memuat bawang putih kering (`exposure`, kolom `source`). Rasio ini hanya mengukur impor langsung. Daging ayam dan
telur hampir tanpa impor langsung, tetapi terpapar lewat pakan, dan paparan itu ditangkap oleh harga dunia komposit jagung dan
bungkil kedelai.

### Keterpencilan provinsi

Untuk H3, koefisien $\ln(1 + \text{jarak ke hub terdekat})$ pada respons h = 4, gabungan 10 komoditas dan 337 seri, adalah
0,007 (−0,022..0,033) per 1 SD jarak, dengan p satu sisi 0,80. H3 tidak didukung. Asosiasi negatif di atas 0,022 per 1 SD dapat
dikesampingkan. Per komoditas, tidak ada interval yang tidak memuat nol (`assoc`).

### Meta-regresi eksploratif

Kami menghitung 88 koefisien dua sisi untuk jarak ke hub, kecukupan produksi beras, dan jumlah kota sampel, pada 10 komoditas dan
gabungannya, untuk h 4/8/12. Tidak ada interval yang tidak memuat nol, dan q BH minimum 1,0. Intervalnya adalah yang lebih lebar
dari SE CR2 dan bootstrap, dan p dihitung konsisten dengan interval itu.

### Arti proksi

`ln_dist_hub` mengukur jarak garis lurus dari ibu kota provinsi ke hub terdekat. Ukuran ini tidak mencakup biaya atau waktu
logistik. `rice_sufficiency` hanya mencakup kecukupan produksi beras. `n_kota` adalah jumlah kota sampel PIHPS per provinsi
menurut daftar kota di situs PIHPS (2026-11-21, 110 kota) dan tidak sama dengan tingkat integrasi pasar. FAQ PIHPS menyebut 82 kota
sampel IHK, dan selisihnya belum dikonfirmasi BI. Koefisien yang tidak terdeteksi berarti proksi ini tidak menjelaskan variasi
respons dalam desain ini. Logistik, produksi, dan cakupan pasar tetap bisa berperan.

### Interaksi efek tetap

Sembilan koefisien $\Delta e \times Z(r)$ untuk jarak ke hub, kecukupan beras, dan jumlah kota sampel pada h 4/8/12 memiliki
interval yang memuat nol. Yang terbesar ada pada jarak ke hub untuk h = 8: 0,16 (−0,00..0,33).

## Pertanyaan 5 — Nilai prediktif kurs (Task 4)

| Model dibanding M1 | MAE h = 4 | MAE h = 8 |
|---|---|---|
| M0 (tanpa perubahan) | 1,017 (DM −1,90, p 0,062) | 1,016 (DM −1,41, p 0,16) |
| M2 (+ kurs, harga dunia, episode) | 1,009 (DM −2,70, p 0,009) | 1,013 (DM −2,29, p 0,025) |
| M3 (gradient boosting + identitas) | 1,037 (DM −1,98, p 0,052) | 1,014 (DM −0,63, p 0,53) |

Evaluasi memakai 76 origin (75 untuk h = 8, dengan 38 yang tidak tumpang tindih) dan 337 seri provinsi. Rasio di atas 1 berarti
kurang akurat dari M1. DM negatif juga berarti kurang akurat dari M1, dengan p dua sisi. Jadi p kecil dengan DM negatif berarti
lebih buruk secara nyata. Sumber: `forecast_eval`, dijalankan ulang 2026-11-26 dengan penanda episode real-time (sebelumnya M2
1,014 / 1,017).

Dalam evaluasi bersyarat pseudo-real-time ini, fitur kurs dan harga dunia tidak menurunkan MAE. Pada agregat, M2 sedikit tetapi
nyata lebih buruk dari M1 di kedua horizon (MAE +0,9% dan +1,3%). Untuk hipotesis "M2 lebih akurat", p satu sisi 0,996 dan 0,987.
Pada h = 8, rasio M2/M1 terburuk ada pada daging sapi (1,26), gula (1,10), dan beras (1,08), sedangkan cabai dan bawang merah
berada di sekitar 1.

Uji H5 pada h = 8 untuk origin dengan pergerakan kurs besar memberi rasio 1,11 untuk impor langsung (p satu sisi 0,93) dan 1,12
untuk input impor (0,86), dengan p Holm 1,0. H5 tidak didukung. Hanya ada 8 origin dengan pergerakan besar (7 tidak tumpang
tindih), sehingga daya ujinya rendah.

Pada studi kasus 2026, rasio M2/M1 adalah 1,005 pada h = 4 (10 origin) dan 1,004 pada h = 8 (9 origin) (`robustness`).

Model tanpa perubahan (M0) lebih akurat daripada M1 pada h = 4 untuk komoditas yang harganya diatur atau kaku: daging sapi 0,78,
beras 0,82, gula 0,85, minyak goreng 0,89, dan bawang putih 0,93.

Bagian ini menjawab pertanyaan 5. Lampiran A membahas pertanyaan lanjutan yang berbeda, yaitu informasi apa yang membantu
memprioritaskan pemantauan bila kurs tidak membantu. Lampiran itu tidak mengubah jawaban di sini.

## Eksplorasi E2 — Respons per periode HET/HAP

Kami membagi periode setiap komoditas menurut tanggal penetapan atau perubahan HET/HAP, lalu mengukur respons di setiap periode.
Hasilnya 145 sel: 10 komoditas, 3–6 rezim, h 4/8/12, terhadap kurs dan harga dunia. Interval dikalibrasi terhadap 499 plasebo
geser-melingkar. Sebanyak 15 sel memiliki interval yang tidak memuat nol, tetapi q BH minimum 0,145, sehingga tidak ada perbedaan
antarrezim yang tahan koreksi multiplisitas.

Pola terkuat yang kami catat secara eksploratif ada pada bawang putih di rezim Perbadan 12/2024, dengan $\beta_e(8)$ 3,74
(interval 1,83..5,65 dalam 98 minggu), sedangkan sampel penuh memberi −0,68. Pola kedua ada pada telur ayam di rezim Perbadan
5/2022, dengan $\omega(4)$ −0,89 (interval −1,47..−0,31 dalam 78 minggu). Sumber: `regime_profiles`.

## Kalibrasi inferensi (tingkat 2, analisis kepekaan sesudah G6)

### Mengapa kalibrasi diperlukan

Kami menemukan dua masalah inferensi sesudah praregistrasi, dengan arah yang berlawanan. Pertama, bootstrap blok 13 minggu lebih
pendek dari jendela proyeksi lokal (h + 6 minggu). Akibatnya rerata replikasi hanya 0,57 / 0,35 / 0,35 kali estimasi (median,
h 4 / 8 / 12), dan interval resmi **terlalu lebar**. Kedua, SE cluster minggu **terlalu sempit**. Di bawah plasebo, |t| > 1,96
terjadi pada 8,8% replikasi per sel nasional (maksimum 17,6%), padahal seharusnya 5%.

Kalibrasi plasebo memakai 499 replikasi geser-melingkar sebagai distribusi null statistik t. Replikasi ini mempertahankan struktur
harga dan memutus kaitan waktu dengan penggerak. Intervalnya menjadi estimasi $\pm\, \mathrm{crit} \cdot SE$, dengan
$\mathrm{crit} = \max(1{,}96;\ \text{kuantil plasebo})$.

### Uji ukuran di bawah null

Kami memperlakukan setiap replikasi plasebo sebagai data asli dan menilainya dengan ambang dari replikasi lainnya
(leave-one-out), pada 48 sel nasional: $\beta_e$ dan $\omega$ untuk h 4/8/12. Komoditas fokus memakai 499 replikasi dan
komoditas lain 199. Keluarga BH dinilai pada 199 replikasi yang memuat ke-48 sel.

| Metode | Positif palsu per sel di bawah null | Replikasi null dengan ≥ 1 temuan BH | Data asli: sel tidak memuat nol (dari 48) | Data asli: temuan BH q < 0,05 |
|---|---|---|---|---|
| $\pm 1{,}96 \cdot SE$ cluster minggu | 8,8% (maks 17,6%) | 17,1% | 9 | 5 |
| Terkalibrasi plasebo | 4,4% (maks 4,8%) | 0,5% | 7 | 4 |
| Resmi praregistrasi | tidak dapat diuji (butuh bootstrap per replikasi) | – | 3 | – |

Sumber: `placebo_stats`, `profiles`, `national_calibrated`, dan `docs/audit/20261127_redflag_juri/`.

Kalibrasi tidak memilih metode yang paling banyak memberi hasil signifikan. Ambangnya lebih ketat daripada 1,96 pada 41 dari 48
sel (median crit 2,28, maksimum 2,74), dan ukurannya di bawah null tidak melebihi 5% (4,4%). Di bawah null kami mengharapkan
rata-rata 2,0 sel dan 0,01 temuan BH, sedangkan data asli memberi 7 sel dan 4 temuan.

Dua klaim **hanya** bergantung pada tingkat 2: daging ayam $\beta_e(8)$ (q 0,058) dan minyak goreng $\omega(8)$ (q 0,024). Klaim
lain sudah didukung interval resmi, yaitu minyak goreng $\omega(4)$ dan $\omega(12)$, serta daging ayam $\beta_e(4)$ dengan batas
atas −0,00 yang tepat di ambang.

Kalibrasi yang sama tersedia untuk PT nasional dan untuk deviasi provinsi (`province_calibrated`). Pada PT nasional, 3 dari 30 sel
tidak memuat nol, dibanding 1 pada interval resmi. Interval resmi provinsi hampir selalu memuat nol (hanya 0–2,4% sel yang tidak),
interval $\pm 1{,}96 \cdot SE$ terlalu longgar (6–17%), dan versi terkalibrasi 5–12%. Dengan koreksi BH atas seluruh 1.623 sel
provinsi, 7 deviasi bertahan, yaitu pada daging ayam (Maluku, Papua, Kepulauan Riau), gula (Kalimantan Barat, Kalimantan Tengah),
dan respons minyak goreng terhadap harga dunia (Maluku Utara). Hasil ini deskriptif dan sejalan dengan uji heterogenitas.

## Ketahanan & validasi

### Tier 1

Estimasi utama berada di dalam interval cek pada 366 dari 382 sel (`robustness`).

| Cek Tier 1 | Sel cocok |
|---|---|
| Jumlah lag 2/4/8 | 96/96 |
| Dekomposisi dolar global dan komponen spesifik rupiah | 78/78 |
| Frekuensi bulanan | 47/48 |
| h 8 dibanding 12 | 15/16 |
| Tanpa Mar–Jun 2020 dan bulan Brent ekstrem | 45/48 |
| Sub-periode sebelum dan sesudah 2021-04-05 | 85/96 |

Dari 16 pengecualian, 10 ada pada gula dan minyak goreng karena besarannya berbeda antar sub-periode, dan 3 pada daging ayam.

### Tier 2

Estimasi utama berada di dalam interval cek pada 191 dari 193 sel.

| Cek Tier 2 | Sel cocok |
|---|---|
| Varian PIHPS lain dan komposit pakan alternatif | 94/96 |
| Harga mingguan dari observasi terakhir | 48/48 |
| Panel Harga Bapanas bulanan | 42/42 |
| Keterpencilan alternatif: km ke hub tanpa log, dan km ke Jakarta saja | 6/6 |
| Ordinal jalur eksposur | 1/1 |

Untuk ordinal jalur eksposur, $\tau_b$ −0,03 (−0,75..0,70). Dua pengecualian punya tanda yang sama dengan estimasi utama: Gula
Kualitas Premium $\beta_e(4)$ 0,36 (0,15..0,57) dibanding 0,69, dan Minyak Goreng Curah $\omega(8)$ 0,36 (0,26..0,45) dibanding
kemasan 0,21. Minyak goreng curah lebih peka terhadap harga sawit dunia dalam rupiah.

### Proyeksi lokal dibanding studi peristiwa

Implikasi proyeksi lokal berada di dalam interval studi peristiwa pada 26 dari 30 sel. Namun hanya 2 dari 30 interval studi
peristiwa yang tidak memuat nol, dan kesamaan tanda antar episode 0,51. Karena itu kecocokan ini lemah sebagai validasi.

## Validasi prospektif (sedang berjalan)

Periode uji 2024+ sudah dipakai berulang dalam eksplorasi (Lampiran A). Bukti out-of-sample yang bersih hanya bisa datang dari
prediksi untuk minggu yang belum terjadi. Kami sudah membekukan prediksi berikut.

| Prediksi beku | Di-commit (sebelum target pertama 2026-11-27) |
|---|---|
| C1-tuned & `IW_NAT`, 12 origin 2026-09-28..11-16, 8.112 baris | `ca53742`, 2026-11-25 21.41 WIB |
| C1-tuned, `FR_REF`, `FR_CITY` | `ec6dd19`, 2026-11-26 20.45 WIB |
| K4 risiko kenaikan material | `044873c`, 2026-11-27 09.53 WIB |
| Aturan & evaluator maju K4 (ambang gagal ditetapkan dari MDE) | `8c7677a`, 2026-11-27 10.28 WIB |

### Cara memeriksa

Pemeriksaan ini membutuhkan clone repository git proyek, karena zip juri tidak memuat riwayat git maupun folder `docs/audit/`.
Perintah `python -X utf8 docs/audit/20261127_prospective_validation/scripts/integrity_check.py` memeriksa bahwa sha256 setiap
berkas prediksi dan evaluator sama dengan manifest dan dengan commit sebelum target ada. Perintah ini keluar dengan kode 0 bila
semua utuh. Hasil terakhir pada 2026-11-27 18.20 WIB: semua pemeriksaan wajib lolos.

Di Windows, opsi `-X utf8` diperlukan bila keluaran tidak menuju konsol UTF-8. Tanpa opsi itu, skrip berhenti dengan galat cetak
(keluar 1) walaupun semua pemeriksaan lolos. Skripnya ikut dibekukan, jadi tidak kami ubah. Hash dua prediksi beku pertama
dihitung pada berkas CRLF, sehingga verifikasi byte membutuhkan checkout dengan `core.autocrlf=true`.

### Jadwal dan daya

Putaran interim berlangsung ≥ 2026-11-29 (1 origin per horizon), lalu 2026-12-20 (h = 4 lengkap) dan 2027-01-17 (h = 8
lengkap), sesudah masa penjurian. Hasil interim tidak kami baca sebagai konfirmasi.

Data maju hanya dapat menandai kegagalan besar, yaitu Δ macro F1 < −0,08 / −0,04 atau ΔAP K4 < −0,14. Keuntungan kecil pada
periode uji 2024+ tidak dapat dikonfirmasi dengan 4–8 origin mingguan yang tumpang tindih. Prediksi maju hanya diperlukan untuk
tingkat 3. Hasil tingkat 1 (praregistrasi) tidak membutuhkannya.

## Dataset turunan

Kontribusi data proyek ini adalah panel turunan yang terintegrasi dan terdokumentasi. Isinya:

- harga eceran mingguan 34 provinsi × 10 komoditas × 464 minggu, dengan status setiap sel (teramati, rangkaian harga identik atau
  carry-forward, pendek, hilang)
- harga dunia padanan dalam rupiah beserta tanggal ketersediaannya (as-of)
- daftar 13 episode depresiasi
- tabel buatan tim: konkordansi PIHPS–HS–Pink Sheet–FAOSTAT, rasio impor per komoditas, riwayat HET/HAP bertanggal dan berstatus
  verifikasi, serta fitur provinsi (keterpencilan, kecukupan beras, jumlah kota sampel).

Rincian, hak redistribusi, dan keterbatasannya ada di `docs/DATASHEET.md`.

## Keterbatasan

### Inferensi

Interval resmi cenderung terlalu lebar karena bootstrap menarik $\beta$ ke nol, sedangkan $\pm 1{,}96 \cdot SE$ terlalu sempit
(lihat Kalibrasi inferensi). Karena SE cluster terlalu sempit, MDE untuk komoditas volatil seperti cabai, bawang merah, dan telur
cenderung optimistis.

### Model dasar Task 4

Evaluasi Task 4 bersifat pseudo-real-time karena vintage revisi data tidak tersedia. M1 adalah satu regresi ridge untuk 10
komoditas tanpa identitas komoditas, dengan bulan sebagai angka 1–12. Dua pemeriksaan kepekaan memberi kesimpulan yang sama:
ridge per komoditas, dan ridge dengan dummy bulan serta dummy minggu sekitar Idulfitri (M2/M1 1,005 pada h = 4 dan 1,019 pada
h = 8, dengan H5 Holm 0,56). Pada pemeriksaan kedua, M1 makin tertinggal dari model tanpa perubahan (M0/M1 0,95 dan 0,97). Jadi
keterbatasan utama model dasar ada pada pengumpulan lintas komoditas, dan penyandian musim tidak mengubahnya.

### Waktu origin Task 4

Origin diberi label Senin minggu ISO t, tetapi fitur harga eceran dan kurs memakai pengamatan sampai Jumat minggu itu. Waktu
keputusan yang konsisten adalah sesudah minggu t lengkap dan jendela revisi PIHPS lewat, yaitu Minggu 00.00. FAQ PIHPS menyebut
revisi berlaku "sampai dengan hari berikutnya". Harga dunia hanya dipakai bila `available_at` ≤ Senin minggu t, sehingga rilis
Pink Sheet pada Selasa–Jumat minggu origin baru terpakai pada minggu berikutnya. Aturan ini lebih konservatif dari waktu keputusan
dan tidak menimbulkan kebocoran.

`available_at` mengasumsikan hari kerja ke-2 bulan berikutnya, yang cocok dengan rilis 3 Nov 2026. Nilainya berasal dari rilis
3 Nov 2026 yang memuat revisi historis, jadi belum tentu sama dengan nilai yang tersedia saat itu. Cutoff yang seragam hanya boleh
diuji lewat protokol baru yang dibekukan lebih dulu, dan model beku tidak diubah.

### Eksplorasi Task 4

Lampiran A menjelaskan keterbatasan eksplorasi: periode uji 2024+ dipakai berulang, TimesFM mungkin pernah melihat data uji, dan
kebutuhan pengguna belum divalidasi.

### Harga diatur dan rangkaian harga identik

Banyak minggu pada komoditas yang diatur berstatus carry-forward: beras 92%, daging sapi 90%, gula 85%, dan minyak goreng 87% sel.
Status ini menandai minggu yang mayoritas hari teramatinya termasuk rangkaian harga identik ≥ 5 hari. Data tidak bisa membedakan
penyebabnya: harga memang tidak berubah, pedagang melaporkan nilai yang sama, atau sumber memakai harga hari sebelumnya ketika
pasar tidak beroperasi (FAQ PIHPS). Konsentrasinya pada komoditas yang diatur konsisten dengan kekakuan harga, tetapi tidak
membuktikannya. Status ini terpisah dari data hilang (1,0% sel tanpa pengamatan) dan tidak kami pakai untuk menyaring data.
Minggu tanpa perubahan membatasi respons yang dapat teramati.

### Cakupan

Kesimpulan berlaku untuk 10 komoditas, 34 provinsi dalam kerangka lama, dan periode 2018–2026.

## Lampiran A — Eksplorasi Task 4 (tingkat 3, sesudah praregistrasi)

Lampiran ini berisi analisis tambahan sesudah praregistrasi. Isinya tidak menggantikan uji H5 dan tidak menjawab pertanyaan
penelitian yang didaftarkan. Pertanyaannya: bila kurs tidak membantu memprediksi, informasi apa yang membantu TPID memprioritaskan
pemantauan? Semua angka berasal dari evaluasi bersyarat pseudo-real-time dengan origin dan baris uji yang sama dengan M0–M3.
Interval 95% berasal dari bootstrap blok origin, karena seri dalam satu origin berbagi guncangan nasional. Perbandingan dikoreksi
Benjamini–Hochberg per keluarga, dan hasil yang tidak lolos koreksi kami tulis "tidak terbukti".

### A.1 Pemakaian periode uji 2024+

Periode 2024+ bukan data uji yang bersih. Analisis awal sudah menilai seluruh 2021–2026 sebelum pemisahan pengembangan dan uji
dibuat. Sesudah itu, periode uji dibuka lagi untuk lima perbandingan dan satu laporan deskriptif.

| Yang dinilai | Selisih h = 4 / h = 8 | p Holm atas 10 perbandingan |
|---|---|---|
| C1-tuned − TimesFM, macro F1 | +0,059 / +0,053 | 0,008 / 0,008 |
| target 3 kelas (deskriptif, tanpa pembanding) | macro F1 0,625 / 0,606 | – |
| `iw_gap` − C1-tuned, macro F1 | +0,004 / +0,005 | 1,0 / 0,45 |
| `IW_NAT` − C1-tuned, macro F1 | +0,0085 / +0,0033 | 1,0 / 1,0 |
| presisi daftar pantau C1-tuned − aturan naif | +0,094 / +0,072 | < 0,001 / 0,004 |
| average precision K4 − C1-tuned | +0,045 / +0,015 | 0,045 / 1,0 |

Nilai p berasal dari q BH yang dilaporkan (konservatif, p ≤ q) atau dari interval bootstrap dengan pendekatan normal. Rinciannya
ada di `docs/audit/20261127_redflag_juri/hasil/buku_besar_test.csv`.

Seleksi model, fitur, hyperparameter, dan threshold selalu kami lakukan pada origin pengembangan (target ≤ 2023). Pemilihan
keluarga fitur tetap dipengaruhi eksplorasi seluruh periode sebelumnya, jadi angka 2024+ adalah evaluasi eksploratif yang belum
out-of-sample.

Bila kesepuluh perbandingan diperlakukan sebagai satu keluarga, yang tetap lolos Holm hanya C1-tuned > TimesFM, daftar pantau >
aturan naif pada kedua horizon, dan K4 pada h = 4 (tipis, p Holm 0,045). Kandidat lain yang hanya diuji di origin pengembangan
tidak pernah membuka periode uji. Semuanya, termasuk yang gagal, tercatat dalam 195 baris di `docs/eksperimen_registry.csv`.

### A.2 Arah perubahan dari ramalan regresi dan klasifier langsung

Akurasi arah M1 dan M2 tidak berbeda dari strategi selalu menebak arah terbanyak. Selisihnya pada h = 8: M1 +0,015
(−0,029..0,053) dan M2 +0,022 (−0,019..0,054). M3 berada di atas baseline dengan selisih +0,058 (0,024..0,091). Pada komoditas
yang harganya kaku, yaitu beras, daging sapi, gula, dan minyak goreng dengan ≥ 50% minggu tanpa perubahan, M1 berada di bawah
baseline (−0,100, q 0,013). Selisih M3 (−0,054, q 0,077) dan M2 (−0,053, q 0,17) tidak lolos koreksi.

Klasifier yang dilatih langsung untuk arah naik atau turun (HistGradientBoostingClassifier) dengan fitur yang sama mencapai akurasi
arah h = 8 sebesar 0,620 dengan fitur kurs (C2) dan 0,607 tanpa fitur kurs (C1). Keduanya di atas baseline 0,545 (selisih C2
+0,075, interval 0,038..0,110). Fitur kurs tidak terbukti menambah akurasi: C2 − C1 +0,012 (−0,004..0,030).

### A.3 Model deep learning dan foundation model

| Model | MAE / M1, h = 4 | MAE / M1, h = 8 | Akurasi arah h = 8 |
|---|---|---|---|
| TimesFM 3.0 zero-shot | 0,935 (DM p < 0,001) | 0,895 (DM p < 0,001) | 0,623 |
| TimesFM 3.0 + kovariat kurs & harga dunia | 0,939 (DM p 0,001) | 0,904 (DM p < 0,001) | 0,613 |
| PatchTST | 0,998 (DM p 0,92) | 0,962 (DM p 0,15) | 0,596 |
| TSMixer | 0,995 (DM p 0,77) | 0,966 (DM p 0,13) | 0,608 |
| TSMixer + kurs & harga dunia | 1,036 (DM p 0,16) | 0,994 (DM p 0,84) | 0,601 |

Rasio di bawah 1 berarti lebih akurat dari M1. Nilai p DM dua sisi, dan arahnya mengikuti rasio. Baseline akurasi arah h = 8
adalah 0,545.

TimesFM 3.0 tanpa pelatihan pada data kami menurunkan MAE terhadap M1 sebesar 6,5% (h = 4) dan 10,5% (h = 8). Porsi variasi
perubahan harga yang terjelaskan naik dari 0,07 menjadi 0,25 (h = 8). TimesFM 3.0 dirilis September 2026 dan dilatih pada korpus
deret waktu publik yang isinya tidak kami ketahui. Bila deret harga pangan Indonesia 2021–2026 ikut di dalamnya, keunggulan ini
adalah batas atas. Keunggulannya lebih kecil pada origin 2026 (MAE/M1 0,938, dibanding 0,876 pada 2023 dan 0,834 pada 2024), yang
konsisten dengan kemungkinan itu tetapi tidak membuktikannya. Bobot modelnya (1,32 GB) berlisensi non-komersial dan tidak ikut
paket juri.

Kurs dan harga dunia tetap tidak menambah akurasi. TimesFM dengan kovariat kurs dibanding tanpa kovariat memberi rasio MAE 1,005
(h = 4) dan 1,010 (h = 8), keduanya tidak nyata. TSMixer dengan kanal kurs dibanding tanpa kanal kurs memberi 1,041 pada h = 4
(DM p 0,020, tidak lolos BH, q 0,057) dan 1,029 pada h = 8. Hasil ini sejalan dengan H5.

Pada komoditas berharga kaku, PatchTST dan TSMixer, dengan maupun tanpa kurs, berada di bawah baseline arah (q 0,018–0,049 pada
h = 8). Selisih TimesFM −0,074 tidak lolos koreksi (q 0,053). Tidak ada model yang lebih baik dari menebak arah terbanyak untuk
kelompok ini.

Pada h = 8, F1 makro tertinggi dicapai TimesFM (0,623), lalu klasifier C2 (0,617), C1 (0,605), TSMixer (0,604), dan M3 (0,596),
dibanding M1 0,551. Semua dihitung pada baris dengan perubahan harga ≠ 0 (cakupan 90,7%). Bila minggu tanpa perubahan dihitung
salah, akurasi TimesFM 0,566 dan M1 0,508. Kemampuan memisahkan naik dan turun masih lemah (ROC-AUC ≤ 0,70, MCC ≤ 0,26).

Hasil ini stabil. Pada tiga seed PatchTST dan TSMixer, rentang akurasi arah ≤ 0,03 dan rentang MAE/M1 ≤ 0,02. TSMixer dengan kurs
lebih buruk dari TSMixer di ketiga seed: MAE/M1 rerata 0,995 (simpangan baku 0,009) dibanding 0,966 (simpangan baku 0,007) pada
h = 8. Keputusan "lebih baik", "tidak terbukti", atau "lebih buruk" sama untuk panjang blok bootstrap 2, 3, 4, dan 6 origin. DM
TimesFM terhadap M1 tetap p < 0,001 untuk lag HAC 1–5.

Perbandingan yang lolos koreksi BH ada tiga. MAE TimesFM, dengan maupun tanpa kurs, lebih kecil dari M1 pada h = 4 dan 8
(q ≤ 0,004). Akurasi arah TimesFM, dengan maupun tanpa kurs, lebih tinggi dari M3 pada h = 4 (+0,041 dan +0,045, q 0,020).
Akurasi arah C1 lebih tinggi dari M1 pada h = 4 dan 8 (+0,045 dan +0,047, q ≤ 0,030). C2 dibanding M3 pada h = 4 tidak lagi lolos
setelah penanda episode real-time diperbaiki (+0,013, q 0,36). Tidak ada perbandingan dengan kurs dibanding tanpa kurs yang lolos.

### A.4 Klasifier arah teroptimasi (C1-tuned) dan daftar pantau

Kami memilih klasifier arah dengan fitur dinamika harga per seri hanya pada origin pengembangan. Fiturnya meliputi lag panjang,
momentum, volatilitas, musiman, deviasi dari rata-rata bergerak dan dari provinsi lain, serta sinyal nasional komoditas. Pada
origin ≥ 2024 (37 / 36 origin), F1 makronya 0,677 (0,652..0,698) pada h = 4 dan 0,680 (0,653..0,706) pada h = 8, di atas
TimesFM pada origin yang sama (+0,059 dan +0,053). Versi dengan fitur kurs tidak menambah akurasi.

Sumber informasi lain yang kami uji di origin pengembangan juga tidak memberi perbaikan yang terbukti: harga pedagang besar dan
produsen PIHPS, harga dalam-minggu, 27 kandidat fitur/threshold/bobot/algoritma, cuaca sentra produksi dan realisasi impor, harga
110 kota, prakiraan cuaca NOAA CFSv2, dan intensitas berita GDELT. Galat yang tersisa terutama ada pada perubahan harga kecil dan
pergeseran porsi kenaikan antarperiode.

Bagi pengguna seperti TPID, pertanyaannya adalah komoditas mana di provinsinya yang perlu diprioritaskan 4–8 minggu ke depan. Kami
menetapkan kriteria berikut sebelum pengukuran.

| Istilah | Definisi |
|---|---|
| Kenaikan material | Perubahan rerata harga minggu t + h terhadap minggu t yang termasuk 20% perubahan terbesar komoditas itu pada data latih, misalnya ≥ 1,6% untuk beras dan ≥ 50% untuk cabai rawit pada h = 4. Definisi ini statistik dan diukur di titik akhir horizon. Ambang kebijakan TPID dan kenaikan yang terjadi di tengah horizon tidak tercakup |
| Daftar pantau | 2 komoditas per provinsi per minggu dengan skor tertinggi, dari semua komoditas yang datanya tersedia saat itu. Skornya peluang arah naik, belum peluang kenaikan material, sehingga hasil ini menilai kualitas urutan prioritas |
| Pembanding | Empat aturan tanpa model: tren 4 minggu provinsi, tren nasional, posisi terhadap rata-rata 13 minggu, dan pola periode yang sama tahun lalu. Aturan terbaik di origin pengembangan menjadi pembanding resmi |

| Origin ≥ 2024 (evaluasi eksploratif, kriteria ditetapkan sebelumnya) | h = 4 | h = 8 |
|---|---|---|
| Presisi daftar pantau C1-tuned | 0,18 (0,13..0,23) | 0,16 (0,11..0,21) |
| Aturan sederhana pembanding | 0,085 (tren provinsi) | 0,089 (tren nasional) |
| Selisih | +0,094 (0,055..0,132) | +0,072 (0,034..0,115) |
| Laju-dasar kenaikan material | 0,088 | 0,089 |
| Porsi kenaikan material yang tertangkap | 0,41 | 0,36 |
| F1 makro arah pada baris yang ternyata bergerak material (aturan tanda tren) | 0,81 (0,50) | 0,81 (0,44) |
| Kalibrasi peluang arah: Brier skill terhadap klimatologi komoditas / ECE | 0,17 / 0,010 | 0,17 / 0,021 |

Daftar pantau berbasis pola historis memuat kenaikan material sekitar dua kali lebih sering daripada pilihan acak (2,0× dan
1,8×), sedangkan aturan tren sederhana tidak lebih baik dari acak. Pada periode uji, aturan terbaik justru "kembali ke rata-rata"
(0,11 dan 0,12). Sebagai analisis kepekaan, C1-tuned tetap di atas aturan itu: +0,066 (0,033..0,101) dan +0,041 (0,003..0,078).

Kami juga membandingkan dengan aturan "pantau komoditas yang paling sering naik material di masa lalu" (laju-dasar komoditas).
Pada h = 4 daftar C1-tuned lebih presisi: 0,18 dibanding 0,10 (selisih +0,082, interval 0,050..0,120). Pada h = 8 keunggulannya
tidak terbukti (+0,019, interval −0,027..0,081, dan −0,026 di pengembangan). Aturan laju-dasar hampir selalu menandai beras, gula,
minyak goreng, atau daging sapi yang sama setiap minggu.

Sekitar 1 dari 6 komoditas yang ditandai benar-benar naik material. Daftar ini cocok untuk memprioritaskan pemantauan dan
pemeriksaan data harga, stok, dan informasi pendukung. Intervensi otomatis membutuhkan bukti yang lebih kuat. Dengan anggaran 1,
2, atau 3 komoditas per provinsi, presisinya 0,21 / 0,18 / 0,16 dan recall 0,24 / 0,41 / 0,54 (h = 4).

Sekitar 57% alarm jatuh pada beras, gula, minyak goreng, dan daging sapi, yang ambang material statistiknya hanya 1,4–2,7%
(h = 4). Prioritas kebijakan TPID mungkin berbeda, jadi materialitas kebijakan perlu ditetapkan bersama pengguna.

Dua ukuran di tabel bersifat bersyarat. Arah pada baris material dihitung pada baris yang ternyata bergerak material, dan
kalibrasi menilai peluang arah, belum peluang kenaikan material. Kelemahan klasifier ada pada perubahan kecil (F1 makro kuintil
|perubahan| terkecil sekitar 0,57). Pada 25% prediksi paling yakin setiap minggu, akurasi arah 0,83 (h = 4) dan 0,81 (h = 8).

Di origin pengembangan, kriteria yang sama lolos (selisih presisi +0,110 dan +0,067), kecuali kalibrasi h = 8 yang gagal tipis
(ECE 0,056 > 0,05). Kalibrasi ulang walk-forward menurunkan ECE di bawah 0,05 tetapi tidak memperbaiki Brier, sehingga tidak kami
pakai.

### A.5 Risiko kenaikan material sebagai target tersendiri (K4)

Kami melatih klasifier dengan fitur dan hyperparameter C1-tuned langsung pada target kenaikan material (definisi di atas), memakai
semua minggu termasuk yang harganya tidak berubah. Kriteria ditetapkan sebelum pengukuran. Pada origin ≥ 2024, klasifier ini
mengurutkan risiko lebih baik daripada skor arah pada h = 4: average precision 0,24 dibanding 0,19 (selisih +0,045, interval
0,017..0,083), dan presisi daftar pantau 2 komoditas per provinsi 0,20 dibanding 0,18 (+0,023, interval 0,003..0,047). Peluangnya
terkalibrasi (ECE 0,02).

Pada h = 8 arahnya sama (+0,015 dan +0,012), tetapi intervalnya memuat nol dan peluang tinggi terlalu yakin. Kami menilainya
PARTIAL: urutannya dipakai secara eksploratif, angka peluang h = 8 tidak. Pada ambang seragam 5% dan 10%, skor ini kalah dari
C1-tuned, sehingga pilihan model bergantung pada ambang yang dipakai pengguna.

### A.6 Keterbatasan eksplorasi

Periode uji 2024+ dipakai berulang (A.1). Hanya validasi prospektif yang memberi bukti out-of-sample bersih.

Kebutuhan TPID belum kami validasi dengan pengguna, yaitu jumlah komoditas yang dapat dipantau, toleransi alarm palsu, ambang
kenaikan yang relevan, dan waktu persiapan. Belum ada bukti bahwa daftar ini memperbaiki keputusan operasional. Kami membuat
analisis kepekaan rasio biaya dengan skenario r = 1, 2, 5, 10. Angka ini tidak mewakili biaya nyata atau nilai harapan yang
tervalidasi. Hasilnya, daftar pantau dengan presisi di bawah 0,5 hanya lebih bernilai daripada tanpa alarm bila kenaikan yang
terlewat sekitar 3–5 kali lebih mahal daripada pemeriksaan yang tidak perlu. Nilai keputusan yang sebenarnya membutuhkan biaya dan
peluang yang tervalidasi, sedangkan peluang K4 pada h = 8 belum terkalibrasi. Penggunaan operasional menunggu ambang kebijakan dan
kapasitas pemantauan dari pengguna.

Pemeriksaan kebocoran membuktikan fitur tidak membaca observasi masa depan. Efek revisi data PIHPS (H+1) tidak dapat diuji karena
data vintage tidak tersedia. Kenaikan material bersifat relatif per komoditas dan diukur di titik akhir horizon.

## Sumber angka

| Bagian | Berkas hasil |
|---|---|
| Tahap 0 | `eligibility`, `episodes`, `mde` |
| Task 1 | `profiles`, `events`, `placebo_stats` |
| Task 2 | `heterogeneity`, `cluster_selection`, `partition_compare`, `planted_recovery` |
| Task 3 | `assoc`, `asymmetry`, `regime_profiles`, `national_calibrated`, `province_calibrated` |
| Task 4 | `forecast_eval` |
| Ketahanan | `robustness` |

Batas Rupiah, uji ukuran kalibrasi, dan buku besar periode uji dihitung di `docs/audit/20261127_redflag_juri/` dari artefak resmi,
tanpa menulis ke `results/`. Lampiran A memakai `forecast_preds`, `direction_preds`, `deep_preds`, dan log evaluasi Task 4 di
`logs/evaluations/`. `direction_tuned_preds` tidak dikirim dan dapat dibangun ulang dengan
`python -m kagami task4 --direction-tuned`. Definisi dan kriteria Lampiran A tercatat di `docs/DECISIONS.md`. Validasi prospektif
ada di `docs/audit/20261127_prospective_validation/`. Rambu klaim mengikuti CLAUDE.md §20. Folder `docs/audit/` berisi laporan,
skrip, dan hasil analisis tambahan, dan hanya ada di repository git proyek.
