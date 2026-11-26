# K4 — Kebutuhan bisnis (Fase A, EKSPLORATIF, D-164)

Tanggal: 2026-11-26. Ditulis sebelum modeling. Sumber asumsi: D-154 PROTOKOL §1, adendum D-155, panduan wawancara
[`docs/PANDUAN_WAWANCARA_TPID.md`](../../PANDUAN_WAWANCARA_TPID.md) (asumsi A1–A11). **Belum ada satu pun jawaban pengguna TPID** (U109
`[HUMAN]`). Semua hasil K4 di folder ini memakai materialitas statistik sebagai proxy dan berstatus eksploratif.

## 1. Pengguna & keputusan

TPID provinsi (dan koordinasi nasional) memutuskan instrumen pengendalian harga (operasi pasar/SPHP, kerja sama antardaerah, pemantauan stok,
komunikasi) untuk 10 komoditas strategis. Keluaran K4 yang dibayangkan: **daftar pantau mingguan** per provinsi yang mengurutkan komoditas
menurut risiko kenaikan material 4 / 8 minggu ke depan, disertai **peluang** yang dapat dibaca apa adanya. Batas klaim (CLAUDE.md §20):
skor berbasis pola historis harga PIHPS dalam evaluasi rolling-origin pseudo-real-time, bukan ramalan dan bukan pemicu tindakan otomatis.

## 2. Delapan pertanyaan kebutuhan

| # | Pertanyaan | Status | Asumsi kerja di K4 | Dasar / bukti | Konsekuensi bila asumsi salah | Validasi (panduan) |
|---|---|---|---|---|---|---|
| 1 | Kenaikan material atau perubahan ekstrem dua arah? | Belum divalidasi | Kenaikan (risiko daya beli & inflasi pangan); penurunan tajam di luar lingkup | TPID dibentuk untuk pengendalian inflasi; instrumen (SPHP, operasi pasar) menahan kenaikan | Bila penurunan tajam juga penting (mis. harga petani/peternak), target dua arah perlu kartu baru | A1, B3, D4 |
| 2 | Berapa kenaikan yang material bagi kebijakan? | **Tidak diketahui** | Proxy statistik: ≥ P80 \|y\| riwayat komoditas (D-154) | Tidak ada ambang resmi yang dapat dirujuk; HET/HAP adalah batas level, bukan ambang perubahan | DU: proxy memberi ambang 1,2% (beras) .. 49% (cabai rawit) per 4 minggu; ambang kebijakan bisa jauh berbeda | A6, D4 |
| 3 | Ambang sama untuk semua komoditas? | Belum divalidasi | Berbeda per komoditas (relatif terhadap kebiasaannya) | Volatilitas komoditas berbeda 30–40× | Ambang seragam (mis. 5%) membalik komposisi: positif komoditas diatur turun dari 60% ke 13% (DU) | A6, D4 |
| 4 | Persentase atau nominal rupiah? | Belum divalidasi | Persentase (selisih log) | Konvensi semua analisis proyek | Ambang rupiah membuat komoditas mahal (daging sapi Rp133 rb/kg) lebih sering material | A6, D4 |
| 5 | Titik akhir horizon atau kejadian kapan pun? | Belum divalidasi | Utama titik akhir (D-154); kejadian kapan pun dievaluasi terpisah (Fase E) | 12% / 21% kejadian adalah lonjakan yang berbalik sebelum titik akhir (DU) | Bila TPID bereaksi pada lonjakan sementara, target kejadian lebih relevan | A7, D5 |
| 6 | Berapa komoditas yang dapat dipantau per minggu? | Belum divalidasi | Tidak dipilih; K = 1/2/3 per provinsi sebagai pertukaran | D-154/D-155 | Kapasitas menentukan titik operasi presisi–recall | A4, D1 |
| 7 | Berapa alarm yang dapat ditindaklanjuti? | Belum divalidasi | Dianalisis lewat kebijakan K dan ambang peluang τ | – | Bila hanya sedikit, presisi pada K kecil lebih penting daripada AP | A4, A5, D1, D2 |
| 8 | Konsekuensi alarm palsu vs risiko terlewat? | Belum divalidasi | Skenario rasio biaya FN : FP = 1, 2, 5, 10 (bukan biaya nyata) | D-154 PROTOKOL §1: keduanya penting | Rasio biaya menentukan τ optimal (τ* = 1/(1+r)) dan K | A5, D2, D3 |

## 3. Materialitas statistik vs kebijakan

| | Materialitas statistik (dipakai) | Materialitas kebijakan (belum ada) |
|---|---|---|
| Definisi | y_h ≥ persentil 80 \|y_h\| baris latih komoditas pada origin (walk-forward) | Ambang kenaikan yang memicu tindakan TPID (per komoditas, %, rupiah, atau terhadap HET/HAP) |
| Sumber | Data PIHPS sendiri | Pengguna (wawancara, regulasi, praktik TPID) |
| Sifat | Relatif terhadap kebiasaan komoditas; berubah dengan riwayat | Tetap/diputuskan; dapat berbeda antarprovinsi |
| Status di K4 | Semua angka K4 | Tidak dikarang; DU hanya menunjukkan skenario ilustratif ambang seragam 5% / 10% untuk memperlihatkan kepekaan komposisi |

Persentil 80 **bukan** keputusan TPID. Hasil K4 yang lolos tetap berstatus eksploratif dan **BLOCKED untuk penggunaan operasional** sampai
ambang kebijakan, kapasitas pemantauan, dan pilihan titik akhir/kejadian divalidasi.

## 4. Kebutuhan validasi manusia (`[HUMAN]`, U109)

| Kode | Yang perlu dipastikan | Dampak pada K4 | Pertanyaan panduan |
|---|---|---|---|
| V1 | Ambang kenaikan yang memicu tindakan, per komoditas (persen/rupiah/relatif HET) | Ganti z statistik dengan z kebijakan; latih ulang (protokol baru) | D4, B4 |
| V2 | Kenaikan saja atau dua arah | Bentuk target | B3, D4 |
| V3 | Titik akhir vs kejadian dalam jendela; panjang jendela (4 / 8 minggu) | Pilih K4-E80 atau K4-A80; horizon | D5, C1 |
| V4 | Kapasitas pemantauan per minggu (K) | Titik operasi | D1 |
| V5 | Toleransi alarm palsu / rasio biaya FN:FP | τ optimal & K | D2, D3 |
| V6 | Angka peluang dipakai atau cukup urutan | Perlu kalibrasi atau tidak | D6 (A9) |
| V7 | Hari & jam keputusan (kesegaran data) | `available_at` (U110) | C3 |
| V8 | Komoditas diatur: apakah kenaikan 1–3% (beberapa tick) relevan secara kebijakan | Apakah 60% positif proxy statistik bermakna | D4 |

## 5. Aturan keputusan bila jawaban TPID datang

| Jawaban | Tindakan |
|---|---|
| Ambang kebijakan ≈ proxy statistik (relatif per komoditas) | Hasil K4-E80 dapat dibawa ke uji prospektif apa adanya |
| Ambang seragam/absolut (mis. ≥ 5%) | Protokol baru: z kebijakan; DU menunjukkan komposisi berbalik ke hortikultura → evaluasi ulang dari awal |
| Lonjakan sementara penting | Kartu lanjutan untuk K4-A80 (target kejadian) |
| Hanya urutan yang dipakai | Kalibrasi tidak menjadi syarat; fokus presisi@K |
| Kapasitas K diketahui | Laporkan satu titik operasi; τ dari rasio biaya |
