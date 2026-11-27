# Validasi K4 — Spesifikasi operasional (rancangan, belum untuk dipakai)

Tanggal 2026-11-27, catatan bertanggal. Rancangan alur keputusan yang dapat diterjemahkan ke produk **bila** U109 lolos dan validasi prospektif
mendukung. Saat ini status operasional **BLOCKED**: tidak ada bagian dokumen ini yang boleh diterapkan di app atau disajikan ke pengguna sebagai
sistem yang berjalan. Parameter yang bergantung pada kebutuhan pengguna ditandai `[U109:Rx]` (kode di
[BUSINESS_REQUIREMENTS_VALIDATION.md](BUSINESS_REQUIREMENTS_VALIDATION.md)).

STATUS: **PARTIAL** (rancangan lengkap; parameter K, τ, r, ambang belum dapat diisi)

OBJECTIVE: Memisahkan lima fungsi (ranking, peluang, alarm, tinjauan manusia, dukungan keputusan) agar setiap fungsi punya bukti, batas, dan
pemiliknya sendiri, dan agar model tidak pernah memerintahkan intervensi.

## 1. Alur

```
PIHPS harian ──► panel mingguan (Senin ISO; available_at Minggu 00.00, U110)
                    │
                    ▼
  [1] Ranking risiko      K4-E80 h 4 & h 8 → peringkat komoditas per provinsi + daftar nasional
                    │
                    ▼
  [2] Estimasi peluang    h 4 saja: kategori kasar + rasio terhadap laju komoditas; h 8: tanpa angka
                    │
                    ▼
  [3] Pembentukan alarm   kebijakan K per provinsi [U109:R6] atau ambang τ [U109:R7]; aturan tampilan komoditas
                    │
                    ▼
  [4] Tinjauan manusia    analis TPID [U109:R11]: cek riwayat, HET/HAP, kebijakan, pasokan → pantau / abaikan / naikkan
                    │
                    ▼
  [5] Dukungan keputusan  rapat TPID memutuskan tindakan [U109:R10]; sistem hanya mencatat keputusan & hasilnya
```

| Lapis | Masukan | Keluaran | Bukti saat ini | Pemilik keputusan |
|---|---|---|---|---|
| 1 Ranking | panel mingguan, fitur C1-tuned | peringkat 1..10 per provinsi × h | AP h 4 terbukti > C1t dev & test; h 8 searah, tidak terbukti | model (deterministik) |
| 2 Peluang | skor K4 | kategori + rasio vs laju komoditas | h 4 ECE ≤ 0,023 tetapi tidak ada kalibrator yang memperbaiki Brier; h 8 ekor terlalu yakin | model, dengan batas tampilan |
| 3 Alarm | peringkat/peluang + kebijakan | daftar pantau mingguan | presisi@K2 test 0,20 / 0,17 | **pengguna** memilih K atau τ |
| 4 Tinjauan | daftar + konteks | status per alarm | – | analis TPID |
| 5 Keputusan | hasil tinjauan | tindakan & catatan | – | rapat TPID |

## 2. Lapis 1: ranking risiko

- Skor: K4-E80 (HGB, kolom & hyperparameter C1-tuned beku, label P80 \|y\| titik akhir). Bila U109 memilih target lain, skor diganti sesuai
  peta keputusan BUSINESS_REQUIREMENTS_VALIDATION §5. Ambang seragam **tidak** dapat memakai K4-E80 (TARGET_SENSITIVITY §3).
- Dua tampilan:
  - **per provinsi**: 10 komoditas diurutkan, dengan peringkat minggu lalu (persistensi ± 50%);
  - **nasional**: 2 × 34 baris teratas tanpa kuota (K4 memusatkan alarm di provinsi yang sering naik; korelasi alarm–positif 0,68).
  Pilihan kuota provinsi vs daftar nasional = tata kelola pusat–daerah `[U109:R11]`.
- h 4 menjadi tampilan utama karena buktinya lebih kuat. h 8 sebagai kolom pendamping berlabel "indikatif".

## 3. Lapis 2: estimasi peluang

| | h 4 | h 8 |
|---|---|---|
| Angka persen | **tidak** ditampilkan sampai validasi prospektif dan `[U109:R8]` = angka | tidak ditampilkan |
| Kategori | rendah / sedang / tinggi menurut rasio p ÷ laju-dasar komoditas (< 1×, 1–2×, ≥ 2×) | sama, berlabel "indikatif" |
| Catatan wajib | "relatif terhadap kebiasaan komoditas ini; bukan peluang harga naik" | + "peluang tinggi h 8 historis terlalu yakin" |
| Kalibrasi | mentah (tidak ada kalibrator yang memperbaiki Brier) | – |

Alasan memakai rasio terhadap laju komoditas: ranking terbukti lebih baik daripada peluang absolut. Laju terealisasi per minggu bergeser
0,05–0,23 dan model hanya menangkap ± 30% pergeseran itu ([CALIBRATION_DEEP_AUDIT.md](CALIBRATION_DEEP_AUDIT.md) §4). Ambang kategori 1× / 2×
adalah usulan tampilan, bukan hasil seleksi. Ambang itu sendiri perlu diuji prospektif.

## 4. Lapis 3: pembentukan alarm

Dua kebijakan, dipilih pengguna:

| Kebijakan | Cara | Kelebihan | Kekurangan | Parameter |
|---|---|---|---|---|
| Kapasitas tetap | K teratas per provinsi tiap minggu | beban kerja tetap, setiap provinsi punya daftar | memaksa alarm di minggu tenang (presisi ± 0,11) | K `[U109:R6]` |
| Ambang peluang | alarm bila p ≥ τ (h 4) | jumlah alarm mengikuti risiko (sd ± 20–38 per minggu) | 15–22 provinsi tanpa alarm per minggu; bergantung pada kalibrasi | τ = 1/(1 + r) `[U109:R7]` |

Biaya ilustratif (biaya FP + r × FN per minggu, satuan = satu alarm palsu; **skenario, bukan biaya nyata**; D-164 `k4_utility_cost.csv`,
`k4_test_utility_cost.csv`):

| r | Termurah dev h 4 | Termurah test h 4 | Termurah test h 8 | Bacaan |
|---|---|---|---|---|
| 1 | tanpa alarm (40,4) | tanpa alarm (29,8) | tanpa alarm (30,1) | daftar tidak sepadan bila keduanya sama mahal |
| 2 | K4-cal τ 0,33 (79,7) ≈ K4 K1 (80,7) ≈ tanpa alarm (80,8) | C1t-cal τ 0,33 (59,5) ≈ tanpa alarm (59,6) ≈ K4-cal (59,7) | C1t-cal τ 0,33 (59,6) ≈ tanpa alarm (60,2); K4-cal 62,5 | titik impas; tidak ada skor yang unggul |
| 5 | K4-cal τ 0,17 (149,6) ≈ K4 K2 (150,4) | K4-cal τ 0,17 (127,2) / K4 K1 (131,5) | K4-cal τ 0,17 (136,3) / K4 K1 (145,4) vs tanpa alarm 150,4 | daftar bernilai; h 8 tipis |
| 10 | K4-cal τ 0,09 (215,4) / K4 K3 (226,6) | K4-cal τ 0,09 (193,4) / K4 K3 (202,1) | K4-cal τ 0,09 (200,4) / K4 K3 (217,4) | K lebih besar |

(Baris τ dihitung pada himpunan peluang. Bandingkan dalam satu kolom, bukan antarkolom.)

Aturan tambahan yang diusulkan (semua menunggu uji prospektif):
- **Komoditas tanpa skor informatif**: bawang putih (presisi K2 dev 0,03 / 0,01) dan bawang merah h 8 (0,03) ditampilkan dengan label "skor tidak
  informatif untuk komoditas ini". Komoditas ini tidak dikeluarkan diam-diam. Aturan ini dipilih dari dev, jadi harus dikonfirmasi prospektif.
- **Peringkat tepat di bawah batas**: tampilkan peringkat K+1 dan K+2 sebagai "cadangan". Separuh kenaikan terlewat berada di sana
  ([OPERATIONAL_ERROR_ANALYSIS.md](OPERATIONAL_ERROR_ANALYSIS.md) §3).
- **Tidak ada alarm otomatis berupa pesan ke luar**. Daftar hanya tersedia di dasbor untuk ditinjau.

## 5. Lapis 4: tinjauan manusia

Setiap alarm ditinjau analis sebelum masuk rapat. Kartu alarm memuat:

| Bagian | Isi | Mengapa |
|---|---|---|
| Identitas | provinsi, komoditas, horizon, minggu data terakhir, tanggal `available_at` | kesegaran data (U110) |
| Peringkat | peringkat minggu ini & 4 minggu terakhir | persistensi |
| Kategori risiko | rendah/sedang/tinggi (rasio vs laju komoditas) | §3 |
| Rekam jejak historis | presisi & recall komoditas ini di provinsi ini (2024+), dengan n | 7–8 dari 10 alarm tidak berujung kenaikan material |
| Riwayat harga | 12 minggu + ambang materialitas dalam % dan Rp/kg | ambang statistik bisa ± 3 tick (beras) atau Rp29 rb (cabai rawit) |
| Konteks regulasi | HET/HAP berlaku & jarak harga ke acuan; perubahan kebijakan terbaru | ekor terlalu yakin terjadi sesudah intervensi (minyak goreng 2022) |
| Alasan masuk daftar | 2–3 fitur dengan kontribusi terbesar (momentum, deviasi spasial, musim) | analis dapat menilai apakah polanya masih berlaku |
| Yang tidak diketahui sistem | stok, pasokan, cuaca sentra, distribusi antardaerah | U112; harus dicek di luar sistem |

Keputusan analis: **pantau** (tetap di daftar), **abaikan** (dengan alasan), **naikkan ke rapat**. Keputusan dan hasilnya 4/8 minggu kemudian
dicatat untuk evaluasi berikutnya.

**Kapan alarm ditinjau ulang:**
- setiap minggu ketika data baru masuk (peringkat dihitung ulang);
- segera bila harga minggu terakhir direvisi (U110) atau ada perubahan HET/HAP;
- alarm kedaluwarsa sesudah h minggu. Hasilnya dicatat apa pun yang terjadi;
- bila alarm yang sama muncul ≥ 3 minggu berturut-turut tanpa kenaikan, tandai "persisten tanpa realisasi" agar analis tidak terbiasa
  mengabaikannya.

## 6. Lapis 5: dukungan keputusan

- Sistem tidak merekomendasikan instrumen (operasi pasar, SPHP, kerja sama antardaerah). Pilihan tindakan sepenuhnya milik TPID.
- Bahasa (CLAUDE.md §20): "prioritas pemantauan berbasis pola historis harga PIHPS", "risiko kenaikan relatif terhadap kebiasaan komoditas". Hindari
  "prediksi", "peringatan dini tervalidasi", "peluang harga naik X%".

## 7. Menyajikan ketidakpastian

- Selalu tampilkan rekam jejak di samping alarm. Contoh kalimat: "Dalam evaluasi 2024–2026, sekitar 2 dari 10 komoditas yang ditandai dengan cara
  ini naik material dalam 4 minggu."
- Tampilkan laju-dasar komoditas ("biasanya 1 dari 10 minggu") agar kategori risiko dibaca relatif.
- Beri tahu minggu tenang: bila rerata skor nasional berada di tersil bawah historis, tampilkan "minggu dengan risiko nasional rendah; presisi
  historis di minggu seperti ini ± 0,1". Penandanya ex-ante dan lemah (rezim momentum hanya membedakan presisi 0,21–0,34), jadi kalimatnya harus
  hati-hati.
- Tidak menampilkan interval prediksi per alarm. Interval yang dapat dipertanggungjawabkan hanya pada tingkat agregat (presisi per K dengan
  bootstrap origin).

## 8. Pemantauan pascapenerapan (bila suatu saat diterapkan)

| Penjaga | Pemicu | Tindakan |
|---|---|---|
| Presisi bergulir 13 minggu | < laju-dasar komoditas dengan K sama selama 13 minggu | hentikan tampilan, evaluasi ulang |
| Pergeseran laju | laju terealisasi 13 minggu di luar rentang historis dev/test | label "rezim di luar pengalaman model" |
| Kalibrasi kategori | porsi realisasi kategori "tinggi" ≤ kategori "sedang" dua kuartal | hapus kategori, tampilkan peringkat saja |
| Data | minggu tanpa data > 10% seri | tidak menerbitkan daftar minggu itu |
| Kebijakan | perubahan HET/HAP pada komoditas | tandai alarm komoditas itu "pola historis mungkin terputus" |

FINDINGS: Rancangan memisahkan ranking (bukti terkuat) dari peluang (terbatas h 4, kategori) dan dari alarm (parameter milik pengguna). Tinjauan
manusia dan catatan keputusan menjadi bagian sistem, bukan tambahan.

EVIDENCE: Dokumen audit di folder ini; D-164 RESULTS, OPERATIONAL_ANALYSIS, `k4_utility_cost.csv`, `k4_test_utility_cost.csv`.

STATISTICAL VALIDITY: Parameter tampilan (kategori 1× / 2×, aturan bawang, "minggu tenang") adalah usulan, bukan hasil seleksi yang diuji.
Semuanya perlu uji prospektif.

BUSINESS IMPLICATION: Daftar hanya bernilai bila kenaikan terlewat ≥ ± 3–5× lebih mahal daripada pemantauan tambahan. Di h 8 test, keunggulan
atas "tanpa alarm" tipis bahkan pada r = 5.

DECISION: **Revisi** rekomendasi D-164 #4: peluang h 4 tidak ditampilkan sebagai angka, hanya sebagai kategori relatif.

BLOCKERS: U109 (R6, R7, R8, R10, R11), U110 (revisi data), U112 (pasokan untuk tinjauan).

NEXT ACTION: Sesudah U109, isi parameter `[U109:*]`, tulis protokol prospektif, dan uji dengan prediksi maju sebelum menyentuh `src/` atau app.
