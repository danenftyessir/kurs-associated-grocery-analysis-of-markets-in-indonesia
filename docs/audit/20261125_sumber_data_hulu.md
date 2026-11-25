# Riset Sumber Data Hulu untuk Task 4 Arah (harga grosir/produsen, pasokan, cuaca)

Tanggal: 2026-11-25 · Pelaksana: Danen (dengan agent) · Lanjutan D-149 (tuas berikutnya = informasi yang mendahului harga eceran).
Catatan bertanggal (bukan dokumen hidup). Riset hanya **membaca** halaman situs; tidak ada berkas yang diunduh dan tidak ada yang
ditambahkan ke `data/raw/` atau `configs/sources.yaml`.

## 0. Ringkasan

| Sumber | Isi | Frekuensi & cakupan (diverifikasi) | Akses & hak | Kecocokan Task 4 |
|---|---|---|---|---|
| **PIHPS Pedagang Besar** (BI, `price_type_id=3`) | harga grosir 10 komoditas, **21 varian sama persis** dengan eceran | harian hari kerja, **sejak 2018-01**; 31–34 provinsi per varian representatif (Jan 2018: 32–33; Jul 2024: 31–34) | situs BI, tombol "Download" resmi; penerbit & format sama dengan `pihps`; izin BI (U13) perlu dipastikan mencakup jenis pasar ini | **Tertinggi**: drop-in (loader & agregasi mingguan yang sama), as-of sama (13.00 WIB hari yang sama, revisi s.d. H+1) |
| **PIHPS Produsen** (BI, `price_type_id=4`) | harga tingkat produsen, nama varian sama | harian, **mulai pertengahan 2018** (penuh 2018-09); provinsi Jul 2024: ayam 32, telur 32, cabai merah 30, cabai rawit 28, daging sapi 28, beras 26, bawang merah 23, minyak 11, gula 10, bawang putih 2 | sama dengan di atas | Sedang: cakupan tidak lengkap untuk gula/minyak/bawang putih; metodologi produsen tidak dijelaskan di FAQ |
| Panel Harga Bapanas — produsen | GKP petani, GKG & beras di penggilingan, jagung pipilan (input pakan), ayam & sapi hidup, telur peternak, cabai/bawang petani, gula di pabrik | harian di situs; dataset bulanan provinsi rilis B+1 | **akses terbatas** (hanya via aplikasi SAPA; "All Rights Reserved"); situs tanpa menu unduh, dilindungi reCAPTCHA | Isi ekonomi paling relevan, tetapi tidak dapat diperoleh secara sah sebelum pembekuan 27 Nov; bulanan B+1 terlalu kasar untuk h 4/8 |
| NASA POWER (cuaca) | curah hujan & suhu harian per koordinat | harian sejak 1981; titik = koordinat ibu kota provinsi yang sudah ada di `region_crosswalk.csv` | terbuka, tanpa kunci API, tanpa batasan pakai (diminta mencantumkan sumber); data dapat direvisi | Sedang–rendah: relevan untuk cabai/bawang (sudah paling baik diprediksi); titik ibu kota ≠ sentra produksi |
| Pasokan beras Pasar Induk Cipinang | stok, pemasukan, pengeluaran harian | hanya Jakarta; angka hanya ditemukan di berita (mis. stok 47.449 ton pada 26 Apr 2026) | tidak ditemukan sumber terbuka berriwayat | Tidak layak sekarang |
| Info Pangan Jakarta | harga eceran pasar di Jakarta | harian, satu provinsi | situs Pemprov | Tidak menambah (eceran, satu provinsi) |

**Rekomendasi:** pilot **PIHPS Pedagang Besar** lebih dulu (dan Produsen sebagai varian kedua), karena satu-satunya sumber hulu
yang (a) mencakup 34 provinsi × 10 komoditas sejak 2018, (b) memakai format, kalender, dan as-of yang sama dengan outcome, dan
(c) dapat diambil lewat fitur unduh resmi situs. Perlu persetujuan Danen sebelum mengunduh (lihat §4).

## 1. PIHPS Pedagang Besar & Produsen (diverifikasi di situs BI)

- Halaman `TabelHarga/PedagangBesarDaerah` menampilkan daftar komoditas & varian yang sama dengan pasar tradisional (Beras 6
  kualitas, Daging Ayam Ras Segar, Daging Sapi Kualitas 1/2, Telur, Bawang Merah/Putih Ukuran Sedang, Cabai Merah Besar/Keriting,
  Cabai Rawit Hijau/Merah, Minyak Goreng Curah/Kemasan Bermerk 1/2, Gula Pasir Kualitas Premium/Lokal) dan 34 provinsi.
- Data grid dimuat dari `WebSite/TabelHarga/GetGridDataDaerah?price_type_id=3` (pedagang besar) / `=4` (produsen) / `=1`
  (pasar tradisional, sumber `pihps` saat ini) dan `GetGridDataKomoditas` (semua provinsi untuk satu varian).
- **Bukti untuk U19:** tombol "Download" (`#btnDownload`, `onclick="Export()"`) menjalankan
  `$("#grid1").dxDataGrid("instance").exportToExcel(false)`, yaitu ekspor sisi-klien dari grid yang datanya berasal dari endpoint
  `GetGridDataDaerah` yang sama. Isi unduhan resmi = respons endpoint untuk filter yang sama. Konfirmasi akhir tetap `[HUMAN]`.
- Cakupan varian representatif (jumlah provinsi berisi nilai, 1–5 Jul 2024): pedagang besar beras 34, ayam 33, daging sapi 32,
  telur 34, bawang merah 34, bawang putih 34, cabai merah keriting 34, cabai rawit merah 31, minyak goreng kemasan 1 34, gula lokal
  33; produsen 26 / 32 / 28 / 32 / 23 / 2 / 30 / 28 / 11 / 10.
- Awal riwayat: pedagang besar sudah terisi 2018-01-02 (nasional & 32–33 provinsi); produsen kosong Mar 2018, 21 varian berisi
  Jun 2018, 31 Sep 2018.
- Pola nilai: deret nasional pedagang besar 17–25 Nov 2026 identik antarhari untuk banyak varian (kekakuan/carry-forward seperti
  eceran) → perlu kode status yang sama (D-021).
- FAQ PIHPS (metodologi hanya untuk pasar tradisional): 2 pasar utama per kota, 2 pedagang tetap (panel) per komoditas, ± 82
  kota IHK; pedagang diganti hanya bila tidak aktif; "apabila terjadi bencana ... data hari tersebut akan diambil dari data pada
  hari sebelumnya" (sebagian carry-forward adalah isian BI); data terbit 13.00 WIB dan dapat direvisi s.d. hari berikutnya. Fakta
  ini melengkapi audit D-147: komposisi pasar dirancang tetap (panel), sehingga perubahan komposisi hanya terjadi saat pedagang
  diganti.

**Belum diuji: apakah grosir mendahului eceran.** Pemeriksaan sekilas tingkat nasional (permintaan 2 tahun per jenis pasar, laporan
harian dan mingguan) tidak selesai setelah beberapa menit di server BI sehingga dihentikan agar tidak membebani server. Uji lead-lag
dan nilai prediktif menjadi bagian pilot (§4) dengan permintaan per provinsi dan rentang pendek. Endpoint juga menyediakan
`tipe_laporan` 1 = harian, 4 = mingguan, 5 = bulanan, 6 = grafis.

## 2. Panel Harga Bapanas

- Level produsen di beranda (25 Nov 2026): GKP tingkat petani Rp7.313, GKG penggilingan Rp8.577, beras medium/premium penggilingan
  Rp13.540/14.935, jagung pipilan kering Rp6.462, kedelai lokal, bawang merah, cabai merah keriting/besar, cabai rawit merah, sapi
  hidup, ayam ras pedaging hidup Rp22.270, telur ayam ras, gula konsumsi di petani/pabrik gula. Isi ini paling dekat dengan jalur
  transmisi proposal (jagung = input pakan untuk ayam/telur).
- Situs produksi tidak lagi punya menu unduh dan memakai reCAPTCHA; dataset "Rata-rata Harga Pangan Bulanan Tingkat Produsen
  Provinsi" (data.badanpangan.go.id, juga data.go.id) berstatus **akses terbatas**, rilis B+1, hanya lewat aplikasi SAPA, "All
  Rights Reserved". Mengakali reCAPTCHA tidak dilakukan. Jalur sah = permintaan data resmi (SAPA) oleh anggota tim `[HUMAN]`.

## 3. Pasokan & cuaca

- NASA POWER: API terbuka tanpa kunci, harian sejak 1981, permintaan pencantuman sumber; data dapat diganti versi yang lebih baik
  (vintage → pseudo-real-time). Titik = ibu kota provinsi (sudah ada lat/lon di `region_crosswalk.csv`); sentra produksi tidak
  tersedia di repo.
- Pasokan beras Cipinang (Food Station): angka hanya muncul di berita (stok ± 40–47 ribu ton, arus ± 1.500–2.500 ton/hari); tidak
  ditemukan sumber terbuka dengan riwayat harian. Info Pangan Jakarta hanya harga eceran Jakarta.

## 4. Usulan pilot (butuh persetujuan sebelum mengunduh)

1. **Unduh** PIHPS pedagang besar (dan produsen) 2017-03 .. 2026-11, 34 provinsi, lewat fitur unduh resmi / endpoint yang sama dengan
   snapshot `pihps` (perkiraan ± 2 × 34 berkas CSV, beberapa MB; satu permintaan per provinsi per rentang). Catat MANIFEST (sha256,
   tanggal ambil) seperti `pihps`.
2. Daftarkan sumber baru di `configs/sources.yaml` (`redistribute: false`, as-of = hari yang sama 13.00, revisi H+1) + loader
   (format sama → `load_pihps(key=...)`), agregasi mingguan & status sel yang sama (D-021).
3. Fitur (hanya s.d. minggu t): selisih log grosir − eceran (margin) dan perubahannya 1/4 minggu, Δ log grosir 1/4/8 minggu, deviasi
   spasial grosir; untuk produsen sama.
4. Evaluasi dengan protokol D-147–D-149 (C1-tuned tetap, seleksi di origin pengembangan, aturan buka test yang sama); split
   resmi (dev ≤ 2023) sebagai utama.
5. Perkiraan durasi: unduh ± 10–20 menit (tergantung server BI; permintaan 2 tahun nasional > 45 detik), fitur + run dev ± 15 menit
   lokal (< 1 jam, tidak perlu Colab).
