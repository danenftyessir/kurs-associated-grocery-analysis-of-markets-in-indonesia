# Panduan Wawancara Validasi Kebutuhan TPID (Task 4 — daftar pantau)

Draf 2026-11-25 (U109, D-155). Wawancara adalah tugas `[HUMAN]`: agent tidak menghubungi siapa pun. Panduan ini dipakai pewawancara
(Danen/Abi) untuk memvalidasi asumsi Business Understanding sebelum keputusan produk dan eksperimen berikutnya.

## 1. Tujuan

Memeriksa apakah asumsi D-154/D-155 tentang kebutuhan TPID benar, sebelum:
- memilih anggaran pemantauan (berapa komoditas per provinsi per minggu, K);
- menetapkan **materialitas kebijakan** (ambang kenaikan yang relevan bagi pengguna), terpisah dari materialitas statistik;
- memilih target **titik akhir** (perubahan minggu t + h vs t) atau **kejadian dalam jendela** (kenaikan kapan pun dalam 4–8 minggu);
- menjalankan kartu K4 (target "risiko kenaikan material" dengan peluang terkalibrasi);
- menyajikan daftar pantau di app atau makalah.

Sisipan pertanyaan K4 (12 kebutuhan R1–R12, matriks status, peta jawaban → keputusan model): `docs/audit/20261127_k4_validation/BUSINESS_REQUIREMENTS_VALIDATION.md` (D-166).

Wawancara ini bukan penjualan produk dan bukan uji kegunaan final. Tujuannya mendengar cara kerja pengguna, bukan meyakinkan mereka.

## 2. Asumsi yang diuji

| Kode | Asumsi saat ini | Pertanyaan kunci | Keputusan proyek yang bergantung |
|---|---|---|---|
| A1 | TPID menyiapkan operasi pasar/SPHP, kerja sama antardaerah, pemantauan stok, komunikasi | Instrumen apa yang benar-benar dipakai? | Bentuk keluaran & narasi manfaat |
| A2 | Waktu persiapan 4–8 minggu relevan | Berapa minggu dibutuhkan untuk menyiapkan instrumen? | Horizon h (4 / 8) |
| A3 | Tanpa model, analis membaca tren, rata-rata, dan pola musim | Bagaimana komoditas bermasalah dikenali sekarang? | Aturan pembanding (S1) |
| A4 | Setiap provinsi dapat memantau ± 2 komoditas per minggu | Berapa komoditas yang realistis ditindaklanjuti? | K utama (1 / 2 / 3) |
| A5 | Alarm palsu dan kenaikan terlewat sama-sama penting | Berapa toleransi alarm palsu; mana yang lebih merugikan? | Presisi minimum; rasio biaya |
| A6 | "Material" = tidak biasa bagi komoditas itu (statistik) | Kenaikan berapa persen / rupiah yang memicu tindakan? | Ambang kebijakan per komoditas |
| A7 | Yang penting adalah perubahan di titik akhir horizon | Apakah lonjakan sementara di tengah jendela perlu diperingatkan? | Target titik akhir vs kejadian |
| A8 | Data minggu berjalan dipakai sesudah Jumat final | Kapan dalam seminggu data dibaca dan keputusan dibuat? | `available_at`, nilai fitur intraminggu |
| A9 | Urutan prioritas cukup; peluang membantu bila terkalibrasi | Angka peluang dipakai atau cukup daftar? | Perlu K4 atau tidak |
| A10 | Informasi tambahan dibutuhkan sebelum bertindak | Data apa yang dicek sebelum bertindak? | Prioritas sumber data baru |
| A11 | Tingkat provinsi & 10 komoditas strategis cukup | Perlu kab/kota atau komoditas lain? | Cakupan |

## 3. Peserta & logistik

- **Jumlah**: 3–5 wawancara, beragam wilayah (Jawa, Sumatra/Kalimantan, Indonesia Timur) dan peran: sekretariat TPID (biro
  perekonomian pemprov), kantor perwakilan BI provinsi (anggota TPID), dinas perdagangan/ketahanan pangan. Koordinasi nasional opsional.
- **Format**: 45–60 menit, daring atau luring, satu pewawancara dan satu pencatat.
- **Bahan**: (1) ringkasan proyek satu halaman; (2) satu **contoh kartu daftar pantau** dari minggu historis 2025 untuk provinsi
  narasumber (2 komoditas teratas, skor, riwayat harga 12 minggu, apa yang kemudian terjadi), diberi label "contoh dari evaluasi
  historis, bukan ramalan". Sudah dibuat untuk ke-34 provinsi (pilih provinsi narasumber; hasil disembunyikan sampai tombol
  "Tampilkan yang terjadi"): `docs/audit/20261125_business_understanding/kartu/kartu_daftar_pantau.html`, dibangun ulang dengan
  `kartu/kartu.py`, juga diterbitkan sebagai halaman privat Claude (bagikan dulu ke pewawancara lewat menu Share). Minggu contoh
  (1–5 Des 2025) dipilih dengan aturan tetap sebelum hasil dilihat dan ternyata minggu lemah: presisi 0,07 (h 4) dan 0,01 (h 8),
  padahal presisi mingguan 2024–2026 berkisar 0,00–0,60 (median 0,13). Pakai ini untuk D2: nilai daftar terlihat dari banyak minggu,
  bukan satu minggu.
- **Persetujuan**: jelaskan bahwa ini riset untuk lomba data mining, minta izin mencatat/merekam, catat hanya peran dan provinsi,
  tawarkan ringkasan hasil.

## 4. Rambu bicara (wajib, CLAUDE.md §20)

| Jangan katakan | Katakan |
|---|---|
| "KAGAMI memprediksi kenaikan harga" | "daftar prioritas pemantauan berbasis pola historis harga PIHPS" |
| "sistem peringatan dini yang sudah tervalidasi" | "prototipe riset; dalam evaluasi historis 2024–2026 sekitar 1 dari 6 komoditas yang ditandai memang naik tajam relatif terhadap kebiasaannya" |
| "peluang 70% harga naik tajam" | "skor arah naik; belum berupa peluang kenaikan tajam" |
| "dataset kami" (untuk PIHPS) | "data turunan yang kami bangun dari PIHPS (Bank Indonesia)" |
| "TPID X mendukung/menyetujui" | (jangan menyatakan dukungan institusi) |

Ajukan pertanyaan terbuka **sebelum** menunjukkan contoh kartu, agar jawaban tentang praktik dan kebutuhan tidak tergiring prototipe.

## 5. Alur wawancara (± 55 menit)

**A. Pembukaan (5 menit).** Perkenalan, tujuan, persetujuan, peran narasumber dalam TPID.

**B. Praktik saat ini (12 menit; A3, A8)**
- B1. Bagaimana tim Anda tahu ada komoditas yang perlu perhatian? Data apa yang dipakai (PIHPS, Panel Harga Bapanas, laporan pasar
  daerah, Bulog, lainnya)?
- B2. Seberapa sering harga dipantau? Kapan rapat atau keputusan rutin dilakukan?
- B3. Ceritakan satu kejadian kenaikan harga terakhir yang Anda tangani: kapan terdeteksi, kapan bertindak, apa tindakannya, apakah
  terasa terlambat?
- B4. Adakah aturan praktis (mis. naik X% dari minggu lalu, mendekati HET/HAP, menjelang hari besar)?

**C. Keputusan & waktu (10 menit; A1, A2, A8)**
- C1. Instrumen apa yang biasa dipakai, dan berapa minggu yang dibutuhkan untuk menyiapkannya?
- C2. Siapa yang memutuskan, dan informasi apa yang harus ada di meja saat itu?
- C3. Hari dan jam berapa dalam seminggu data dibaca dan keputusan dibuat? Apakah harga Jumat sudah dipakai, atau keputusan dibuat
  lebih awal?

**D. Kebutuhan dalam angka (13 menit; A4–A7, A9).** Catat angka, bukan hanya kesan.
- D1. **Kapasitas**: bila setiap minggu ada daftar komoditas untuk dicek lebih dalam, berapa yang realistis ditindaklanjuti tim
  Anda? (1 / 2 / 3 / 5 / lainnya)
- D2. **Toleransi alarm palsu**: dari 10 komoditas yang ditandai, minimal berapa yang harus benar-benar naik tajam agar daftar dianggap
  berguna? (Sesudah dijawab, sampaikan bahwa evaluasi historis saat ini ± 2 dari 10, lalu tanyakan apakah itu masih berguna untuk
  pemantauan.)
- D3. **Biaya relatif**: mana yang lebih merugikan, yaitu menyiapkan sesuatu yang ternyata tidak perlu, atau terlambat menangani kenaikan?
  Kira-kira berapa kali lipat?
- D4. **Ambang kebijakan**: isi tabel §6. Kenaikan berapa persen dalam 4 minggu (dan dalam 8 minggu) yang membuat Anda mulai bertindak,
  per komoditas? Atau acuan lain: HET/HAP, rupiah per kg?
- D5. **Titik akhir vs kejadian**: dua skenario untuk 4 minggu ke depan. (a) Harga naik 15% di minggu ke-2 lalu kembali normal di minggu
  ke-4. (b) Harga naik perlahan sampai +5% di minggu ke-4. Mana yang perlu diperingatkan? Keduanya?
- D6. **Peluang vs urutan**: apakah angka peluang (mis. 70%) membantu, atau cukup urutan prioritas? Bila sistem menyebut 70%, Anda
  memahaminya sebagai apa?

**E. Contoh kartu (10 menit; A9–A11)**
- E1. Apa yang langsung dipahami? Apa yang membingungkan?
- E2. Informasi apa yang kurang untuk bertindak (stok, pasokan antardaerah, cuaca sentra, harga produsen, alasan masuk daftar)?
- E3. Apakah tingkat provinsi cukup, atau perlu kab/kota? Ada komoditas lain yang penting?
- E4. Dalam rapat atau proses apa daftar seperti ini akan dipakai?

**F. Penutup (5 menit).** Hal lain yang perlu kami ketahui? Boleh dihubungi lagi? Siapa lagi yang sebaiknya kami tanyai?

## 6. Lembar catatan (satu per wawancara)

```
Kode narasumber: P__      Peran: ______________      Wilayah (boleh disamarkan): ______      Tanggal: ________      Media: ______
Persetujuan rekam: ya / tidak

A1 Instrumen yang dipakai: ____________________________________________
A2 Waktu persiapan (minggu): ____
A3 Cara mengenali komoditas bermasalah / sumber data: _____________________________
A4 Kapasitas tindak lanjut per minggu (K): ____
A5 Minimal benar dari 10 alarm: ____   Lebih merugikan: alarm palsu / terlambat   Rasio kira-kira: ____ ×
A6 Ambang tindakan (isi tabel di bawah)
A7 Skenario yang perlu diperingatkan: (a) / (b) / keduanya   Alasan: ______________
A8 Hari & jam baca data / keputusan: ____________   Harga Jumat dipakai? ya / tidak
A9 Peluang dipakai? ya / cukup urutan   Arti "70%" menurut narasumber: ______________
A10 Informasi tambahan sebelum bertindak: ________________________________
A11 Perlu kab/kota? ya / tidak   Komoditas tambahan: ______________
Kutipan penting (tanpa nama): ______________________________________________
Tindak lanjut: ____________________________________________________________
```

| Komoditas | Ambang tindakan 4 minggu (% atau acuan) | Ambang 8 minggu | Catatan (HET/HAP, musim) |
|---|---|---|---|
| Beras | | | |
| Gula pasir | | | |
| Minyak goreng | | | |
| Daging sapi | | | |
| Daging ayam | | | |
| Telur ayam | | | |
| Bawang merah | | | |
| Bawang putih | | | |
| Cabai merah | | | |
| Cabai rawit | | | |

## 7. Dari jawaban ke keputusan proyek

Sebuah jawaban dianggap temuan bila konsisten pada ≥ 3 wawancara atau ≥ 2/3 narasumber. Bila jawaban berbeda-beda, laporkan rentangnya
dan pilih opsi yang paling konservatif. Hasil dirangkum dalam catatan bertanggal `docs/audit/` + D-xxx sebelum dipakai.

| Temuan | Keputusan |
|---|---|
| Kapasitas umum K = k | K = k menjadi kebijakan utama di laporan & app (presisi/recall dari tabel D-155) |
| Presisi minimum yang diminta > 0,16–0,18 | Daftar diposisikan sebagai prioritas pemantauan saja, atau butuh informasi baru (pasokan/cuaca); K tidak diturunkan sepihak demi presisi |
| Ambang tindakan absolut / HET-HAP | Protokol baru "materialitas kebijakan": S1 dihitung ulang dengan ambang pengguna, di pengembangan dulu |
| Lonjakan sementara (skenario a) penting | Target "kejadian dalam jendela" ditambahkan (K4 varian 2) |
| Angka peluang dibutuhkan | Kartu K4 (target risiko kenaikan material + kalibrasi) layak dijalankan |
| Keputusan dibuat sebelum harga Jumat final | `available_at` dimajukan; nilai fitur intraminggu ≈ separuh (varian tanpa Jumat, D-152) |
| Informasi verifikasi yang diminta | Urutan prioritas sumber data baru (pasokan fisik, cuaca sentra produksi) |
| Perlu kab/kota atau komoditas lain | Dicatat sebagai batasan cakupan; tidak dikerjakan sebelum pembekuan |

## 8. Etika & data

- Catatan disimpan di folder Drive tim yang dibagikan terbatas; laporan hanya menyebut kode narasumber, peran, dan wilayah umum.
- Jangan membagikan data mentah PIHPS; contoh kartu dibuat dari data turunan.
- Wawancara tidak berarti dukungan institusi; jangan menulis "TPID X menyetujui" di makalah atau app.
