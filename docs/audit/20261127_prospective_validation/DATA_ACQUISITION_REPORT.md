# Laporan akuisisi data — permintaan resmi U112

Tanggal: 2026-11-27 · baca-saja (tanpa login, tanpa CAPTCHA, tanpa unduhan berkas sumber) · lanjutan [D-159](../20261126_pasokan_fisik.md)
§2 dan [Jalur A Workstream C](../jalur_a_macro_f1/SUPPLY_SIDE_SOURCE_AUDIT.md).

**STATUS: BLOCKED** (`[HUMAN]`). Ketiga sumber prioritas hanya dapat diperoleh lewat permintaan resmi. Belum ada surat yang terkirim (U112 🔴).

## 1. Sumber yang diperiksa dan statusnya

Tidak ada sumber baru yang diuji sinyalnya di putaran ini. Sumber yang sudah ditolak tidak diulang, karena tidak ada hipotesis atau mekanisme
baru: GDELT (D-165), CFSv2 (D-161), SIJAGUNG/SPORA (D-160), NASA POWER (D-157), impor BPS bulanan (D-157), PIHPS grosir/produsen/kota
(D-150, D-151, D-158), PIBC/FDP/GPM/KSA (D-159), kebijakan/BBM/DIBI/Trends/NDVI/Bulog/pelabuhan (D-165 C4–C10).

| Prioritas | Sumber | Mekanisme baru (belum tertutup) | Status akses 2026-11-26 | Bisa dinilai di dev ≤ 2023? |
|---|---|---|---|---|
| 1 | **SP2KP** stok & pasokan pasar mingguan (Kemendag) | stok/pasokan pasar mendahului harga eceran | area admin berlogin | ya, bila riwayat 2018+ diberikan dengan tanggal penutupan |
| 2 | **Proyeksi Neraca Pangan Nasional** (Bapanas) | perkiraan resmi ketersediaan − kebutuhan bulanan | katalog `data.badanpangan.go.id`: ± 30 dataset, semuanya *Terbatas* | **tidak**: vintage bulanan baru sejak Sept 2024 (2022–2023 hanya versi Final/Revisi) → hanya prospektif |
| 3 | **Luas tanam & EWS hortikultura** (Kementan Ditjen Hortikultura) | luas tanam 2,5–4 bulan sebelumnya menentukan panen dalam horizon, berbeda dari cuaca yang tertutup di D-161 | tanpa portal publik; siaran pers hanya angka nasional | mungkin, bila laporan EWS bertanggal ≥ 2020 tersedia |

## 2. Spesifikasi kebutuhan (untuk surat permintaan)

Kebutuhan yang sama untuk ketiga sumber:

| Atribut | Kebutuhan | Alasan |
|---|---|---|
| Rentang historis | 2018-01 s.d. sekarang (minimal 2020-01) | latih ≥ 2020 + nilai dev 2021–2023 (gerbang G1, EKSPERIMEN §3) |
| `available_at` | tanggal **terbit/penutupan data** per baris atau per rilis, terpisah dari periode pengamatan | tanpa ini fitur tidak dapat dipakai tanpa kebocoran (G2) |
| Periode pengamatan | tanggal/minggu/bulan yang diukur | penyelarasan dengan minggu ISO (D-020) |
| Frekuensi | mingguan (SP2KP), bulanan (Neraca, luas tanam), per laporan (EWS) | – |
| Lokasi & komoditas | per provinsi (ideal kab/kota) untuk 10 komoditas KAGAMI; kode wilayah BPS | pemetaan ke 34 provinsi (`province_aliases.csv`) |
| Riwayat revisi | **semua vintage** (versi pertama terbit + revisi bertanggal), bukan hanya angka final | angka final 2021–2023 adalah backfill → dilarang (D-149, D-159) |
| Cakupan | daftar pasar/kab-kota yang dilaporkan per periode + penanda kosong/tidak tersedia | membedakan nol dari tidak dilaporkan |
| Akses & izin | izin penggunaan untuk penelitian + publikasi agregat turunan | kebijakan data turunan (D-015, §19) |

Rincian per sumber:
- **SP2KP:** tanggal periode, tanggal input surveyor, tanggal verifikasi/penutupan, kode pasar & kab/kota, komoditas & varian, stok (satuan),
  pasokan masuk, keterangan kosong, perubahan cakupan pasar (D-159 §2). Alamat: `sp2kp@kemendag.go.id`.
- **Bapanas Proyeksi Neraca Pangan:** setiap rilis bulanan sejak awal tersedia, dengan tanggal update. Komponennya stok awal, produksi, impor,
  ekspor, kebutuhan, dan neraca per komoditas per bulan proyeksi. Termasuk lampiran PDF bulanan 2021–2023 bila ada. Jalur: PPID Bapanas
  (permohonan informasi publik).
- **Kementan luas tanam & EWS:** luas tanam & panen bulanan per provinsi (cabai merah, cabai rawit, bawang merah, bawang putih) 2018+, dan
  laporan EWS (prediksi produksi, kebutuhan, surplus/defisit 3 bulan) dengan tanggal terbit. Jalur: PPID Kementan / Ditjen Hortikultura.

## 3. Aturan pemakaian bila data diterima

1. Tidak ada backfill. Baris yang `available_at`-nya sesudah origin tidak dipakai untuk origin itu.
2. Lima gerbang (G1–G5) lebih dulu, termasuk oracle (EKSPERIMEN §3, D-161) dan layar arah nasional increment-only vs konsensus C1t. Gagal →
   tidak dimodelkan.
3. Sumber yang hanya punya vintage 2024+ (Neraca Pangan): protokol prospektif beku (fitur, aturan, hash, commit) **sebelum data diterima**,
   seperti prediksi maju D-152. Tidak ada seleksi dari test 2024+.
4. Tidak ada modeling di putaran ini, apa pun isi datanya.

## 4. Draf surat (`[HUMAN]`: kirim dari akun tim; agent tidak mengirim)

> Perihal: Permohonan data untuk penelitian kompetisi data mining (INDONERIS 2026)
>
> Kami tim mahasiswa ITB yang meneliti kepekaan harga pangan eceran per provinsi. Kami memohon akses data [SP2KP stok & pasokan mingguan /
> Proyeksi Neraca Pangan Nasional seluruh rilis bulanan / luas tanam & EWS hortikultura] untuk 10 komoditas (beras, bawang merah, bawang
> putih, cabai merah, cabai rawit, gula pasir, minyak goreng, daging ayam, telur ayam, daging sapi), periode 2018–sekarang, per provinsi.
> Agar analisis tidak memakai informasi yang belum tersedia pada waktunya, kami membutuhkan tanggal terbit/penutupan data setiap rilis dan
> seluruh versi revisi, bukan hanya angka final. Data hanya dipakai untuk penelitian. Publikasi berupa agregat turunan dengan atribusi sumber.
> Kami bersedia mengikuti ketentuan penggunaan yang berlaku.

## 5. Rekomendasi

1. Kirim tiga permintaan (atau satu surat gabungan) secepatnya. Data tidak akan tiba sebelum submit 29 Nov, jadi untuk lomba hasilnya
   ditulis sebagai keterbatasan dan saran.
2. Sesudah lomba: evaluasi Neraca Pangan secara prospektif saja. SP2KP dan EWS dievaluasi dengan dev 2021–2023 hanya bila vintage bertanggal
   diberikan.
3. Tidak membuka kembali sumber yang sudah ditolak tanpa mekanisme baru yang terdokumentasi.
