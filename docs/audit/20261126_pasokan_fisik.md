# Audit Kelayakan Data Pasokan Fisik & Stok Pasar (D-159, Fase 1) — Task 4 arah

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-159 · Lanjutan [D-158](20261126_nasional_lokal.md) atas rancangan
Danen "Physical Supply & Market Inventory Intelligence". Catatan bertanggal. Hanya **Fase 1 (audit kelayakan)**: semua pemeriksaan baca-saja
lewat browser (halaman publik dan endpoint publik yang dipakai halaman itu sendiri, beberapa permintaan kecil); tidak ada berkas yang
diunduh, tidak ada login, tidak ada area admin yang dibuka. Syarat berhenti Danen berlaku: sumber tanpa riwayat periode pengembangan tidak
di-backfill dan test 2024+ tidak dipakai memilih apa pun.

## 0. Ringkasan

| Sumber | Isi yang benar-benar tersedia | Riwayat dev 2021–2023? | Akses | As-of / vintage | Status |
|---|---|---|---|---|---|
| **SP2KP stok/pasokan** (Kemendag) | Portal publik hanya harga (tabulasi harga per kab/kota + HET, rerata nasional). Modul stok ada di **area admin berlogin**: "Stok Mingguan Bapok", "Survey Stock Pasar Induk", "Pasokan Pasar Induk", ekspor Excel stok mingguan/bulanan | Tidak diketahui | **Tertutup** (login) | Mingguan (bukan harian); tanggal input/verifikasi/penutupan tidak terlihat | **BLOCKED** → permintaan data resmi `[HUMAN]` (U112) |
| **FDP** (Bapanas, Fasilitasi Distribusi Pangan) | 2026: **39 pengiriman** Jan–Okt, 0,3–50 ton per pengiriman; kolom tanggal, komoditas, asal–tujuan, volume | Tidak: seri tahunan mulai 2024 | Terbuka | Bulanan, rilis B+1; versi diterbitkan ulang tiap bulan (dibuat 2026-11-09) | **REJECTED**: log program stabilisasi, bukan ukuran arus pasokan pasar (skala ribuan kali lebih kecil dari konsumsi) |
| **PIBC** (Food Station, Pasar Induk Beras Cipinang) | Endpoint publik stok, beras masuk, beras keluar: **masing-masing 1 rekaman (01 Jun 2025)**; harga 16 rekaman (Jun 2025) | Tidak | Terbuka (portal) | Portal tidak diperbarui sejak Juni 2025 | **BLOCKED**: tanpa riwayat; data internal Food Station hanya via permintaan |
| **GPM** (Bapanas, Gerakan Pangan Murah) | Jumlah pelaksanaan per kab/kota × **bulan** (2026: 2.514 baris), jenis GPM | Tidak: dataset 2024+ (2023 hanya di laporan tahunan PDF) | Terbuka | Bulanan B+1, tanpa tanggal kegiatan; "tarikan data 9 November 2026" (dapat berubah); risiko kausalitas terbalik | **REJECTED** untuk dev (fitur kosong di seluruh dev → tidak dapat dipilih, pelajaran D-149) |
| **KSA** (BPS, luas panen padi bulanan) | Tabel dinamis luas panen per provinsi per bulan (pilihan tahun 2025–2026 pada tabel ini; KSA sejak 2018), termasuk angka potensi bulan mendatang | Sebagian (2018+ untuk realisasi) | Terbuka | Nilai ditimpa (vintage potensi tidak tersimpan) → hanya realisasi berlag yang dapat dipakai | **REJECTED** (nilai rendah): hanya beras; informasi beras sempurna pun hanya +0,002 / +0,007 macro F1 (D-157) |

**Keputusan:** tidak ada sumber yang lolos syarat kelayakan untuk origin pengembangan → **tidak ada modeling di D-159**; C1-tuned tetap.
Jalur yang masih masuk akal hanya **SP2KP stok mingguan** lewat permintaan resmi (spesifikasi §2); bila datanya diperoleh dengan riwayat
≥ 2020, uji mengikuti D-156 §5; bila riwayatnya 2024+, hanya evaluasi prospektif dengan protokol beku.

## 1. Temuan per sumber

**SP2KP.** Beranda & menu Data & Informasi (Wilayah, Komoditas, Tabulasi Harga) memanggil `api-sp2kp.kemendag.go.id/report/api/...`
(rerata harga provinsi, HET/HA, seri HNT) — semuanya harga. Kode aplikasi publik memuat rute admin `/admin/transaksi-stok-mingguan-bapok`,
`/admin/transaksi-pasokan`, `/admin/transaksi-pasokan-normal` dan ekspor `stok/export-excel-bapok-minggu` / `-bulan`, label "Survey Stock
Pasar Induk", "Laporan Stock Pasar Induk", "Stock Mingguan Barang Pokok". Artinya data stok **ada**, berfrekuensi **mingguan**, dan hanya untuk
pengguna berlogin. Tidak dicoba diakses.

**FDP.** Deskripsi resmi: volume yang "dimobilisasi melalui Fasilitasi Distribusi Pangan … sebagai upaya stabilisasi"; interpretasi metadata:
"semakin banyak volume … semakin banyak upaya stabilisasi". Produsen data Direktorat Stabilisasi Pasokan dan Harga Pangan. Isi 2026 = 39 baris
(beras, cabai rawit, minyak goreng, sapi hidup, telur, gula) dengan volume 300–50.000 kg. Ini variabel **intervensi** yang jarang, bukan arus
pasokan; tidak ada data 2021–2023.

**PIBC.** `pibc.foodstation.co.id/rice-stock-data`, `/rice-source-data`, `/rice-delivery-data` (endpoint DataTables yang dipakai halaman)
mengembalikan `recordsTotal = 1` untuk rentang 2017–2026 (rekaman 01 Jun 2025: stok awal 45.680 t, masuk 192, keluar 234, akhir 45.638);
`/rice-price-data` 16 rekaman Juni 2025. Angka stok yang beredar di berita (mis. 47.449 t pada 26 Apr 2026) berasal dari catatan internal
Food Station, bukan seri publik.

**GPM.** Seri "GPM Pusat" & "GPM Daerah" bulanan per kab/kota sejak 2024 (unit "kali"), rilis B+1; 2026 berisi 2.514 baris Jan–Okt. Tidak
ada tanggal kegiatan → tidak dapat ditempatkan dalam minggu; jumlah kegiatan cenderung naik **sesudah** harga naik (kausalitas terbalik).

**KSA.** Tabel BPS "Luas Panen Padi Menurut Provinsi (Bulanan)" (diperbarui 24 Nov 2026) memuat bulan berjalan s.d. Desember 2026 (angka potensi)
dan menimpa nilai lama; tabel ini hanya menawarkan 2025–2026 (riwayat 2018–2023 tersebar di tabel/rilis lain dan portal provinsi, mis. Jabar).
Untuk origin historis hanya realisasi bulan lalu yang dapat direkonstruksi, bukan prakiraan yang diketahui saat itu.

## 2. Spesifikasi permintaan data (untuk `[HUMAN]`, U112)

SP2KP (Kemendag, `sp2kp@kemendag.go.id`): stok & pasokan mingguan per pasar/kab-kota untuk 10 komoditas KAGAMI, **2018-01 s.d. sekarang**,
dengan kolom: tanggal periode, tanggal input surveyor, tanggal verifikasi/penutupan data, lokasi pasar (kode kab/kota), komoditas & varian,
stok (satuan), pasokan masuk, keterangan kosong/tidak tersedia; plus perubahan cakupan pasar dari waktu ke waktu. Syarat pakai: tanggal
penutupan data agar `available_at` dapat ditetapkan; lisensi turunan agregat.
Opsional: Food Station (stok/masuk/keluar harian PIBC 2018+), Bapanas (data operasional FDP/GPM dengan tanggal kegiatan, 2022+).

## 3. Rancangan bila data diperoleh (bukan protokol beku)

Fitur hanya kuantitas (stok mingguan, Δ stok 1/4 minggu, porsi pasar kosong, pasokan masuk relatif normal, dispersi stok antarwilayah) tanpa
fitur harga baru; layar DU dengan koreksi walk-forward (EKSPERIMEN §3) **dan** layar arah nasional vs konsensus C1t (D-158); modeling satu
keluarga; aturan D-156 §5; riwayat < origin dev → hanya evaluasi prospektif.
