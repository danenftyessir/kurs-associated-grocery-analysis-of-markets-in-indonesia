# KAGAMI — Overview Project

**KAGAMI** = *Kurs-Associated Grocery Analysis of Markets in Indonesia*. Kagami (鏡, bahasa Jepang) = cermin: apakah harga pangan
eceran mencerminkan rupiah, dan apakah pantulannya ditentukan oleh komoditas atau lokasi? Nama sebelumnya: RupiahPass (D-028).

Lomba Data Mining INDONERIS 2026 (Gelombang 2, batas 30 Nov 2026; target submit 29 Nov). Sumber kebenaran desain:
`docs/Proposal v4 — RupiahPass ... .pdf` (nama lama proyek di judul proposal). Aturan lomba: `docs/Juknis Data Mining Indoneris 2026.pdf`.

## 1. Pertanyaan pemandu
Apakah kepekaan harga pangan eceran terhadap rupiah lebih ditentukan oleh **komoditasnya** atau oleh **lokasinya**?

Konteks: rupiah melemah sepanjang 2026 (JISDOR 18.250 pada 16 Nov 2026). Bukti agregat: pass-through kurs ke harga
pangan Indonesia lemah/tidak terdeteksi (Unuvar 2026: −0,012, SE 0,150; Persada dkk. 2026; Hidayah & Askar 2026).
Nol agregat bisa menyembunyikan komoditas/provinsi yang peka. Tema lomba dibingkai sebagai **ketahanan harga pangan (SDG 2)**:
TPID bisa tahu komoditas mana yang historisnya paling peka di wilayahnya dan kapan responsnya muncul.

## 2. Jalur transmisi (dasar pemilihan penggerak & komoditas)
1. **Impor langsung** — bawang putih, gula, daging sapi.
2. **Input impor** — jagung & bungkil kedelai untuk pakan → daging ayam, telur.
3. **Paritas ekspor** — minyak sawit → minyak goreng.
Jalur 2–3 bekerja lewat harga dunia dalam rupiah → penggerak kedua *w* = harga dunia padanan × JISDOR.

## 3. Pertanyaan penelitian

| Kode | Pertanyaan | Task | Keluaran |
|---|---|---|---|
| RQ1 | Seberapa besar & cepat harga eceran 10 komoditas bergerak bersama IDR/USD dan harga dunia rupiah (nasional), dan bedanya menurut jalur eksposur? | 1, 3a | Kurva respons h=0–12 + interval; MDE; event study per episode; tabel jalur eksposur |
| RQ2 | Porsi variasi respons dari komoditas, provinsi, interaksi; apakah provinsi membentuk kelompok stabil? | 1, 2 | τ², I², ρ̄ + p plasebo; klaster (atau k=1) + stabilitas |
| RQ3 | Apakah respons depresiasi ≠ apresiasi (level komoditas), dan perbedaan terkecil yang terdeteksi? | 1 | Tabel asimetri + MDE |
| RQ4 | Karakteristik terukur apa (jalur eksposur; keterpencilan & kecukupan produksi provinsi) yang berasosiasi dengan perbedaan respons? | 3 | Koefisien + interval; jackknife |
| RQ5 | Apakah fitur kurs & harga dunia rupiah memperbaiki prediksi perubahan harga 4 & 8 minggu out-of-sample, untuk komoditas/wilayah mana? | 4 | Rasio MAE dengan vs tanpa fitur kurs; ablation |

## 4. Hipotesis (dibekukan di G6, 21 Nov — detail di PREREGISTRATION.md)

| Kode | Hipotesis | Uji | Jenis |
|---|---|---|---|
| H0-Het | Dalam ≥ 1 komoditas, variasi respons antarprovinsi pada h=8 > yang dihasilkan noise (τ² > 0) | Q per komoditas vs plasebo; FDR antar-10 | Konfirmatori |
| H2 | Respons depresiasi ≠ apresiasi di level komoditas (arah tidak ditentukan) | Wald β⁺(8)=β⁻(8), SE cluster minggu | Konfirmatori bila MDE ≤ 0,5; selain itu deskriptif |
| H3 | Provinsi lebih terpencil → respons awal (h=4) lebih kecil; arah h=12 tidak ditentukan | Meta-regresi efek acak: δ(4) < 0 satu arah; δ(12) dua arah | Konfirmatori (waktu); eksploratif (besaran) |
| H5 | Komoditas jalur impor langsung & input impor: fitur kurs + harga dunia menurunkan MAE prediksi 8 minggu pada origin dengan pergerakan kurs besar | Rasio MAE + DM (HAC) per kelompok | Konfirmatori untuk grup fokus |
| E1 | Jalur impor langsung → PT(8) lebih besar daripada komoditas domestik | Kendall τ PT(8) vs rasio impor, p permutasi eksak (N=10) | Deskriptif |
| E2 | Respons di sekitar perubahan HET/HAP (beras, minyak goreng, gula) berbeda dari periode tanpa perubahan | Deskripsi grafis per rezim | Eksploratif |
| E3 | Seri dengan frekuensi perubahan harga lebih tinggi merespons lebih cepat | Kovariat dalam meta-regresi | Eksploratif |

## 5. Lingkup

| Keputusan | Pilihan |
|---|---|
| Komoditas fokus | Bawang putih, gula pasir, minyak goreng, daging ayam + telur (grup pakan), daging sapi |
| Kontrol domestik | Bawang merah, cabai merah, cabai rawit |
| Lainnya | Beras (dilaporkan lengkap, tanpa uji konfirmatori tambahan) |
| Wilayah | 34 provinsi lama (pemekaran Papua → induk); 7 kelompok: Sumatra, Jawa, Bali–Nusa Tenggara, Kalimantan, Sulawesi, Maluku, Papua |
| Periode | Minggu pertama Jan 2018 s.d. pembekuan 21 Nov 2026 (fallback 2020) — mencakup episode 2018, 2020, 2022, 2024–25, 2026 |
| Frekuensi | Mingguan ISO; bulanan sebagai robustness |
| Unit efektif | ~340 seri × ~460 minggu ≈ 156 ribu baris, tetapi informasi kurs = ~460 minggu → inferensi per minggu |

## 6. Batas & rambu klaim (WAJIB untuk makalah, app, findings)
Hasil bersifat **asosiasional**, tidak meramal kurs, tidak mengamati rantai pasok. Respons tak terdeteksi = **batas atas kepekaan**,
bukan kegagalan. k = 1, asosiasi nol, rasio MAE ≈ 1 adalah hasil sah.
Tidak dapat dijawab: biaya pengadaan importir, market power, mata uang invoice, siklus persediaan, rantai distributor, efek kausal kurs.

| Jangan tulis | Tulis |
|---|---|
| "Penelitian pertama tentang ..." | "Sejauh penelusuran kami, belum ada studi yang ...; studi terdekat adalah ..." |
| "Pelemahan rupiah menyebabkan harga X naik" | "Kenaikan IDR/USD berasosiasi dengan kenaikan harga X sebesar ... (interval ...), setelah mengendalikan ..." |
| "KAGAMI memprediksi kenaikan harga" | "Skenario bersyarat berdasarkan pola historis"; "dalam evaluasi rolling-origin, fitur kurs menurunkan MAE sebesar ..." |
| "Komoditas impor lebih rentan" | "Di antara 10 komoditas yang diamati, komoditas A dan B menunjukkan PT(8) lebih besar" |
| "Provinsi terbagi menjadi k tipe kepekaan" (tanpa uji null) | "Provinsi membentuk k kelompok yang lolos uji plasebo dengan stabilitas Jaccard ..." atau "tidak ada struktur regional yang terdeteksi; struktur dengan selisih ≥ ... akan terdeteksi" |
| "Faktor terpenting adalah ..." | "Karakteristik yang berasosiasi paling kuat adalah ... (β = ..., interval ...)" |
| "Model tervalidasi pada episode 2026" | "Dalam evaluasi bersyarat lintas episode 2021–2026, ...; studi kasus 2026 menunjukkan ..." |
| "Tidak ada pengaruh kurs" | "Pengaruh di atas X dapat dikesampingkan pada horizon 8 minggu" |
| "Kerentanan provinsi" | "Kepekaan harga eceran terhadap kurs" |
| "Dataset kami" (untuk PIHPS mentah) | "Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia)" |

## 7. Kriteria keberhasilan (proposal §6.1) & penilaian juri

| Kategori | Kriteria | Dicek di |
|---|---|---|
| Teknis | Pipeline jalan dari data turunan sampai Streamlit di laptop bersih dengan satu perintah; 10 komoditas diproses atau pengecualian didokumentasikan | WP-32 (G7) |
| Metodologi | Setiap estimasi punya interval & MDE; inferensi berbasis minggu; distribusi plasebo untuk setiap statistik heterogenitas & klaster; Tier 1 dilaporkan | WP-09, 16, 18, 28 |
| Data mining | Clustering dinilai vs plasebo & stabilitas bootstrap; uji struktur tertanam; Task 4 rasio MAE & ablation per komoditas | WP-19–21, 27 |
| Interpretasi | Setiap temuan punya kalimat asosiasional untuk analis TPID; setiap grafik menampilkan interval | WP-34 (G8) |

Bobot juri (juknis): keaslian 20%, kebaruan dataset 15%, ketepatan metode 10%, manfaat 20%, kelengkapan projek 20%,
kelengkapan laporan 15%. Submission: makalah PDF, zip project (dataset + kode + library yang bisa dijalankan juri), video demo.
Konten wajib orisinal dan tidak melanggar hak cipta → alasan kebijakan data turunan (D-015).

## 8. Produk
- Paket juri: kode, `configs/`, `data/reference/` (CC BY 4.0), `data/processed/` turunan, `results/`, app, README dengan
  tiga tingkat reproduksi (ARCHITECTURE §5) dan catatan hak data.
- Streamlit 6 halaman: (1) Ringkasan & Status Data, (2) Kepekaan Harga Regional, (3) Pola Respons,
  (4) Eksposur & Nilai Prediktif, (5) Penjelajah Skenario Bersyarat, (6) Temuan Penelitian.
