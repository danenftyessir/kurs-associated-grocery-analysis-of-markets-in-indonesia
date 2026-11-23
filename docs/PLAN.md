
# KAGAMI — Visualization Specification & Streamlit Implementation Plan

**Project:** KAGAMI
**Program:** INDONERIS 2026
**Dokumen:** Visualization Specification v1.0
**Tanggal:** 23 November 2026
**Basis:** Proposal v4 dan materi IF4061 Interactive Visualization, Holistic Dashboard, Map Visualization, dan Visual Data Mining.

---

# 1. Tujuan dan Ruang Lingkup

## 1.1 Tujuan Visualisasi

KAGAMI merupakan platform eksplorasi hasil penelitian yang mengukur seberapa besar dan seberapa cepat harga pangan eceran bergerak bersama perubahan nilai tukar rupiah dan harga komoditas dunia dalam rupiah.

Visualisasi harus membantu pengguna:

1. Memahami kualitas, cakupan, dan keterbatasan data.
2. Mengetahui profil respons harga terhadap perubahan kurs.
3. Membandingkan kepekaan harga antarwilayah dan komoditas.
4. Mengidentifikasi pola respons regional dan kestabilan clustering.
5. Memahami hubungan antara jalur eksposur dan respons harga.
6. Mengevaluasi nilai prediktif informasi kurs.
7. Mengeksplorasi skenario perubahan kurs berdasarkan pola historis.

## 1.2 Prinsip Utama

Seluruh implementasi harus mengikuti prinsip berikut.

| Prinsip               | Ketentuan                                                        |
| --------------------- | ---------------------------------------------------------------- |
| Analytical-first      | Setiap grafik harus mempunyai tujuan analitis yang jelas.        |
| Evidence-based        | Semua nilai harus berasal dari hasil pipeline penelitian.        |
| Uncertainty-aware     | Ketidakpastian estimasi harus terlihat, bukan disembunyikan.     |
| Reproducible          | Grafik membaca hasil analisis yang sudah dibekukan.              |
| Interactive           | Pengguna dapat melakukan filter, seleksi, dan drill-down.        |
| Honest interpretation | Hasil nol, tidak terdeteksi, dan tidak stabil tetap ditampilkan. |
| Consistent            | Satuan, warna, legenda, dan format angka konsisten.              |

## 1.3 Batasan Produk

Aplikasi bukan:

- Sistem peramalan kurs.
- Sistem peramalan harga pangan secara operasional.
- Sistem pengukuran dampak kausal depresiasi.
- Sistem pemantauan rantai pasok.
- Sistem estimasi ekonometrika secara real-time.

Aplikasi merupakan alat eksplorasi hasil penelitian yang telah dihitung sebelumnya.

Pipeline berjalan secara offline. Streamlit hanya membaca hasil yang telah disimpan.

---

# 2. Arsitektur Informasi Visualisasi

## 2.1 Struktur Halaman

Struktur halaman mengikuti enam halaman yang sudah ditetapkan pada Proposal v4.

| ID  | Halaman                       | Pertanyaan utama                                                                   |
| --- | ----------------------------- | ---------------------------------------------------------------------------------- |
| P01 | Ringkasan & Status Data       | Seberapa dapat dipercaya data yang digunakan?                                      |
| P02 | Kepekaan Harga Regional       | Komoditas dan wilayah mana yang paling peka?                                       |
| P03 | Pola Respons                  | Apakah terdapat kelompok provinsi dengan pola respons serupa?                      |
| P04 | Eksposur & Nilai Prediktif    | Lewat jalur apa komoditas terpapar dan apakah kurs membantu prediksi?              |
| P05 | Penjelajah Skenario Bersyarat | Bagaimana perubahan harga yang konsisten dengan pola historis jika rupiah melemah? |
| P06 | Temuan Penelitian             | Apa kesimpulan dan keterbatasan penelitian?                                        |

## 2.2 Hierarki Informasi

Setiap halaman menggunakan struktur:

1. Overview: indikator dan ringkasan utama.
2. Analysis: visualisasi utama yang menjawab pertanyaan pengguna.
3. Exploration: filter, perbandingan, dan detail.
4. Interpretation: penjelasan temuan dan keterbatasan.

Jumlah visualisasi utama dalam satu tampilan dibatasi sekitar 3–4. Visualisasi tambahan dapat ditempatkan pada tab atau bagian detail.

## 2.3 Navigasi Global

Filter global yang direkomendasikan:

- Komoditas.
- Kelompok wilayah.
- Provinsi.
- Penggerak respons.
- Horizon analisis.

Tidak semua filter harus tersedia di setiap halaman. Filter hanya muncul jika relevan dengan analisis yang sedang ditampilkan.

---

# 3. Design System untuk Visualisasi

## 3.1 Prinsip Warna

Warna harus memiliki makna yang konsisten.

| Penggunaan        | Aturan                                  |
| ----------------- | --------------------------------------- |
| Respons positif   | Warna pada sisi positif palet diverging |
| Respons negatif   | Warna pada sisi negatif palet diverging |
| Nol               | Titik tengah netral                     |
| Nilai berurutan   | Palet sequential                        |
| Identitas cluster | Palet kategoris                         |
| Ketidakpastian    | Area transparan                         |
| Plasebo           | Abu-abu                                 |
| Data hilang       | Abu-abu netral dengan pola atau label   |
| Status peringatan | Warna peringatan yang konsisten         |

Hindari penggunaan rainbow palette untuk data numerik berurutan.

## 3.2 Tipografi dan Format

- Judul grafik menjelaskan informasi yang ditampilkan.
- Subjudul menjelaskan konteks pengukuran.
- Angka menggunakan format Indonesia.
- Persentase menggunakan satuan yang konsisten.
- Nilai koefisien tidak boleh kehilangan tanda negatif.
- Interval estimasi ditampilkan dengan presisi yang cukup.
- Jangan menggunakan terlalu banyak angka desimal.

## 3.3 Standar Setiap Grafik

Setiap grafik wajib mempunyai:

1. Judul.
2. Deskripsi singkat.
3. Label sumbu.
4. Satuan.
5. Legenda jika diperlukan.
6. Tooltip.
7. Sumber data.
8. Periode data.
9. Informasi ketidakpastian jika tersedia.
10. Keterangan bahwa hasil bersifat asosiasional, bukan kausalitas.

---

# 4. Visualization Specification — P01 Ringkasan & Status Data

## 4.1 Tujuan

Memperlihatkan kualitas fondasi data sebelum pengguna membaca hasil analisis.

## 4.2 Komponen Utama

### V01 — Coverage Heatmap

**Prioritas:** P1 / Wajib

**Pertanyaan:** Seberapa lengkap data komoditas dan wilayah selama periode penelitian?

**Tipe:** Categorical heatmap.

**Data:**

- Komoditas.
- Provinsi atau kelompok wilayah.
- Minggu observasi.
- `status_sel`.

**Encoding:**

| Elemen | Variabel                  |
| ------ | ------------------------- |
| X      | Periode waktu             |
| Y      | Seri komoditas × wilayah |
| Warna  | Status observasi          |

**Kategori status:**

- Observed.
- Carry-forward.
- Short week.
- Missing.

**Interaksi:**

- Hover untuk melihat tanggal dan status.
- Filter komoditas.
- Filter wilayah.
- Zoom pada rentang waktu.
- Klik seri untuk melihat detail.

**Tooltip:**

- Komoditas.
- Wilayah.
- Tanggal.
- Status observasi.
- Nilai harga jika tersedia.

**Kondisi khusus:**

- Seri yang tidak memenuhi kriteria kelayakan tetap dapat dilihat dengan penanda.
- Jangan mengubah missing menjadi nol.
- Jangan menyamakan carry-forward dengan observasi baru.

### V02 — Data Quality Summary

**Prioritas:** P1 / Wajib

**Tipe:** KPI dan bar chart.

**Indikator:**

- Jumlah seri yang layak.
- Jumlah seri yang tidak layak.
- Persentase missing.
- Jumlah minggu efektif.
- Kesegaran sumber data.
- Status concordance.

**Bar chart tambahan:**

X: sumber data.

Y: jumlah atau proporsi observasi yang tersedia.

Tujuan: membantu pengguna mengetahui sumber mana yang menjadi batas utama penelitian.

### V03 — MDE Summary

**Prioritas:** P1 / Wajib

**Tipe:** Horizontal dot plot atau bar chart.

**Data:**

- Komoditas.
- MDE.
- Kelompok wilayah.
- Horizon pengukuran.

**Tujuan:**

Menunjukkan batas respons terkecil yang masih dapat dideteksi oleh desain penelitian.

**Interpretasi:**

MDE yang besar berarti desain kurang mampu mendeteksi respons kecil. Jangan mengartikan hasil yang tidak signifikan sebagai bukti bahwa respons pasti nol.

---

# 5. Visualization Specification — P02 Kepekaan Harga Regional

Halaman ini menjadi halaman utama KAGAMI.

## 5.1 V04 — Impulse Response Function (IRF)

**Prioritas:** P0 / Visualisasi identitas produk.

**Pertanyaan:** Bagaimana harga pangan bergerak setelah perubahan kurs atau harga dunia dalam rupiah?

**Tipe:** Line chart with confidence band.

**Data:**

- `profiles.parquet`.
- Horizon 0–12.
- Koefisien respons.
- Bootstrap confidence interval.
- Komoditas.
- Kelompok wilayah.
- Penggerak.

**Encoding:**

| Elemen          | Variabel             |
| --------------- | -------------------- |
| X               | Horizon 0–12 minggu |
| Y               | Respons kumulatif    |
| Garis utama     | Estimasi respons     |
| Area transparan | Interval bootstrap   |
| Garis referensi | Nol                  |

**Penggerak yang tersedia:**

1. IDR/USD.
2. Harga dunia dalam rupiah.

**Interaksi:**

- Pilih komoditas.
- Pilih kelompok wilayah.
- Pilih provinsi jika estimasi tersedia.
- Pilih penggerak.
- Pilih horizon tampilan.
- Hover untuk melihat koefisien dan interval.

**Tooltip:**

- Komoditas.
- Wilayah.
- Horizon.
- Koefisien.
- Lower confidence bound.
- Upper confidence bound.
- Status deteksi.
- MDE.

**Interpretasi otomatis:**

Contoh jika interval mencakup nol:

"Respons belum terdeteksi secara statistik pada horizon yang dipilih. Besaran respons yang lebih kecil dari batas deteksi masih mungkin ada."

**Aturan:**

- Jangan mengganti nilai tidak signifikan dengan nol.
- Jangan menyembunyikan interval.
- Jangan menampilkan prediksi sebagai hasil IRF.
- Tampilkan satuan perubahan secara jelas.

## 5.2 V05 — Choropleth Map Indonesia

**Prioritas:** P0 / Visualisasi utama regional.

**Pertanyaan:** Bagaimana distribusi kepekaan harga antarwilayah?

**Tipe:** Choropleth map.

**Data:**

- Estimasi respons tujuh kelompok wilayah untuk tampilan utama.
- Deviasi provinsi yang telah melalui empirical Bayes shrinkage untuk detail 34 provinsi.

**Encoding:**

| Elemen   | Variabel                          |
| -------- | --------------------------------- |
| Geometri | Provinsi Indonesia                |
| Warna    | Besaran respons                   |
| Tooltip  | Nilai estimasi dan ketidakpastian |

**Pilihan nilai:**

- PT(8).
- R4.
- R8.
- R12.
- W8.
- W12.

**Interaksi:**

- Klik provinsi.
- Hover wilayah.
- Pilih komoditas.
- Pilih penggerak.
- Pilih horizon.

**Tooltip:**

- Nama wilayah.
- Nilai respons.
- Interval estimasi.
- Status deteksi.
- Jumlah kota sampel.
- Jumlah minggu efektif.

**Skala warna:**

- Sequential untuk nilai satu arah.
- Diverging dengan titik tengah nol untuk respons positif dan negatif.

**Kondisi khusus:**

Jika τ² mendekati nol, tampilkan penjelasan bahwa deviasi provinsi kembali ke rata-rata nasional setelah penyusutan empirical Bayes.

Jangan membuat perbedaan warna artifisial ketika estimasi tidak menunjukkan perbedaan regional.

## 5.3 V06 — Forest Plot

**Prioritas:** P0 / Wajib.

**Pertanyaan:** Komoditas atau wilayah mana yang mempunyai estimasi respons terbesar?

**Tipe:** Horizontal dot-and-whisker plot.

**Data:**

- Estimasi respons.
- Interval bootstrap.
- Komoditas atau provinsi.
- Horizon.

**Encoding:**

| Elemen           | Variabel               |
| ---------------- | ---------------------- |
| X                | Nilai estimasi         |
| Y                | Komoditas atau wilayah |
| Titik            | Estimasi               |
| Garis horizontal | Interval               |
| Garis vertikal   | Nol                    |

**Interaksi:**

- Sort berdasarkan estimasi.
- Filter wilayah.
- Filter komoditas.
- Pilih horizon.
- Hover untuk interval.

**Kegunaan:**

Melengkapi choropleth map. Peta memperlihatkan pola geografis, sedangkan forest plot memudahkan perbandingan angka.

## 5.4 V07 — Event Study with Placebo Band

**Prioritas:** P1 / Sangat direkomendasikan.

**Pertanyaan:** Bagaimana perubahan harga setelah episode depresiasi kumulatif minimal 3% dibandingkan jendela plasebo?

**Tipe:** Line chart with placebo distribution.

**Data:**

- `events.parquet`.
- Perubahan harga setelah episode.
- 499 jendela plasebo.
- Horizon 0–12 minggu.

**Encoding:**

- Garis utama: perubahan aktual.
- Area: distribusi atau interval plasebo.
- Sumbu X: minggu setelah episode.
- Sumbu Y: perubahan harga kumulatif.

**Interaksi:**

- Pilih episode.
- Pilih komoditas.
- Pilih wilayah.
- Bandingkan episode.

**Kondisi khusus:**

- Episode yang tidak mempunyai outcome lengkap tidak ditampilkan sebagai hasil lengkap.
- Perbedaan aktual dengan plasebo tidak boleh otomatis diartikan sebagai hubungan kausal.

---

# 6. Visualization Specification — P03 Pola Respons

Halaman ini berfokus pada data mining dan validasi struktur regional.

## 6.1 V08 — Cluster Map

**Prioritas:** P0 / Wajib.

**Pertanyaan:** Apakah provinsi membentuk kelompok berdasarkan kesamaan profil respons?

**Tipe:** Categorical choropleth.

**Data:**

- `clusters.parquet`.
- Identitas provinsi.
- Identitas cluster.
- Jaccard per cluster.
- ARI.

**Encoding:**

- Geometri: provinsi.
- Warna: identitas cluster.
- Tooltip: anggota dan karakteristik cluster.

**Interaksi:**

- Pilih k.
- Klik cluster.
- Lihat daftar provinsi.
- Bandingkan karakteristik cluster.

**Aturan:**

- Gunakan label netral K1, K2, dan seterusnya.
- Jangan menggunakan label seperti wilayah paling rentan jika hasil tidak mendukung.
- Jika k = 1, tampilkan peta satu warna dan pesan "Tidak ada struktur regional terdeteksi".

## 6.2 V09 — Dendrogram

**Prioritas:** P1 / Pengayaan.

**Pertanyaan:** Bagaimana hubungan kemiripan antarprovinsi?

**Tipe:** Hierarchical clustering dendrogram.

**Data:**

- Matriks profil respons 34 provinsi.
- Jarak Euclidean.
- Hasil Ward linkage.

**Encoding:**

- Sumbu X: provinsi.
- Sumbu Y: jarak penggabungan.
- Cabang: struktur hierarki.

**Interaksi:**

- Hover cabang.
- Pilih jumlah cluster.
- Tampilkan cut-off.
- Sorot anggota cluster.

**Catatan:**

Dendrogram harus berasal dari hasil Ward hierarchical clustering, bukan dibuat dari hasil K-Means.

## 6.3 V10 — Co-assignment Heatmap

**Prioritas:** P0 / Wajib.

**Pertanyaan:** Seberapa konsisten dua provinsi masuk ke cluster yang sama?

**Tipe:** Symmetric heatmap.

**Data:**

- `coassign.parquet`.
- 34 provinsi.
- 499 replikasi bootstrap.

**Encoding:**

| Elemen | Variabel               |
| ------ | ---------------------- |
| X      | Provinsi               |
| Y      | Provinsi               |
| Warna  | Proporsi co-assignment |

**Interpretasi:**

- Mendekati 1: sering masuk kelompok sama.
- Mendekati 0: jarang masuk kelompok sama.

**Interaksi:**

- Hover pasangan provinsi.
- Urutkan berdasarkan dendrogram.
- Pilih provinsi untuk menyoroti baris dan kolom.
- Pilih cluster.

**Catatan:**

Gunakan urutan provinsi yang sama pada kedua sumbu agar blok kemiripan mudah terlihat.

## 6.4 V11 — Silhouette vs Placebo Plot

**Prioritas:** P0 / Wajib.

**Pertanyaan:** Apakah clustering pada data asli mempunyai struktur yang lebih kuat dibandingkan null placebo?

**Tipe:** Comparison plot.

**Data:**

- Silhouette maksimum untuk k = 1–6.
- Distribusi silhouette plasebo.
- Persentil ke-95 distribusi plasebo.

**Encoding:**

- X: jumlah cluster.
- Y: silhouette score.
- Box plot atau violin plot: distribusi plasebo.
- Titik: hasil data asli.
- Garis: batas persentil ke-95.

**Aturan keputusan:**

Struktur diterima jika silhouette maksimum data asli melewati persentil ke-95 silhouette maksimum plasebo.

Jika tidak, laporkan k = 1.

**Kondisi khusus:**

Jangan memaksa sistem menampilkan jumlah cluster yang lebih besar hanya karena pengguna memilih k.

## 6.5 V12 — Structure Recovery Curve

**Prioritas:** P2 / Opsional.

**Pertanyaan:** Seberapa kecil perbedaan respons regional yang masih dapat dideteksi oleh pipeline?

**Tipe:** Line chart.

**Data:**

- Besaran struktur tertanam 0,1–0,5.
- Frekuensi keberhasilan recovery.
- Hasil replikasi.

**Encoding:**

- X: besar struktur tertanam.
- Y: proporsi recovery.
- Garis: kemampuan deteksi.

**Tujuan:**

Memperlihatkan keterbatasan deteksi clustering, bukan hanya hasil clustering akhirnya.

---

# 7. Visualization Specification — P04 Eksposur & Nilai Prediktif

Halaman ini terdiri atas dua subbagian: Exposure Analysis dan Predictive Evaluation.

## 7.1 V13 — Exposure Scatter Plot

**Prioritas:** P1 / Wajib.

**Pertanyaan:** Apakah komoditas dengan rasio impor lebih besar cenderung memiliki pass-through lebih besar?

**Tipe:** Labeled scatter plot.

**Data:**

- `exposure.csv`.
- PT(8).
- W8.
- Interval estimasi.
- Rasio impor langsung.

**Encoding:**

- X: rasio impor.
- Y: PT(8).
- Titik: komoditas.
- Label: nama komoditas.
- Whisker: interval jika tersedia.

**Interaksi:**

- Hover komoditas.
- Sorot komoditas.
- Pilih indikator.
- Tampilkan Kendall tau.

**Statistik pendamping:**

- Kendall tau.
- Exact permutation p-value.
- Leave-one-commodity-out.

**Batas interpretasi:**

Jumlah komoditas N = 10. Hasil merupakan asosiasi dan tidak boleh digeneralisasikan sebagai hubungan kausal.

## 7.2 V14 — Provincial Exposure Scatter Plot

**Prioritas:** P1 / Pendukung.

**Pertanyaan:** Apakah karakteristik provinsi berasosiasi dengan deviasi respons?

**Tipe:** Scatter plot with regression interval.

**Variabel X:**

- Log jarak ibu kota ke hub terdekat.
- Kecukupan produksi jika tersedia.
- Jumlah kota sampel sebagai kontrol.

**Variabel Y:**

- Deviasi respons provinsi.

**Interaksi:**

- Pilih karakteristik.
- Pilih horizon 4 atau 12.
- Hover provinsi.
- Tampilkan interval.

**Statistik pendamping:**

- Koefisien meta-regresi.
- Interval.
- Jackknife per provinsi.

Jangan mengisi nilai kecukupan produksi untuk komoditas yang datanya tidak tersedia.

## 7.3 V15 — MAE Ratio Plot

**Prioritas:** P0 / Wajib.

**Pertanyaan:** Apakah penambahan informasi kurs dan harga dunia memperbaiki prediksi out-of-sample?

**Tipe:** Dot plot atau grouped bar chart.

**Data:**

- `forecast_eval.csv`.
- MAE.
- RMSE.
- Model.
- Komoditas.
- Kelompok wilayah.
- Horizon.

**Model:**

- M0: Naive.
- M1: Ridge baseline.
- M2: Ridge + kurs dan harga dunia dalam rupiah.
- M3: HistGradientBoosting dengan fitur M2 dan identitas komoditas serta wilayah.

**Encoding:**

| Elemen          | Variabel            |
| --------------- | ------------------- |
| X               | Rasio MAE atau RMSE |
| Y               | Model               |
| Garis referensi | 1,00                |
| Warna           | Model               |

**Rumus:**

MAE ratio = MAE model tambahan / MAE M1.

Interpretasi:

- Di bawah 1: lebih baik.
- Sama dengan 1: tidak berubah.
- Di atas 1: lebih buruk.

**Filter:**

- Semua origin.
- Origin dengan pergerakan kurs besar.
- Horizon 4 minggu.
- Horizon 8 minggu.
- Komoditas.
- Kelompok wilayah.

**Statistik pendamping:**

- Diebold-Mariano HAC.
- Jumlah origin.
- Jumlah jendela tidak tumpang tindih.

## 7.4 V16 — Feature Ablation Heatmap

**Prioritas:** P1 / Wajib.

**Pertanyaan:** Seberapa penting fitur kurs dalam performa model?

**Tipe:** Heatmap.

**Data:**

- Hasil ablation.
- Per komoditas.
- Per kelompok wilayah.
- Perubahan MAE.

**Rumus:**

ΔMAE = MAE model tanpa fitur - MAE model lengkap.

**Interpretasi:**

- Positif: penghilangan fitur memperburuk performa.
- Nol: tidak ada perubahan.
- Negatif: model tanpa fitur justru lebih baik.

**Encoding:**

- X: kelompok wilayah atau komoditas.
- Y: kelompok fitur.
- Warna: ΔMAE.

Jangan menyamakan feature ablation dengan causal feature importance.

---

# 8. Visualization Specification — P05 Penjelajah Skenario Bersyarat

## 8.1 V17 — Scenario Response Chart

**Prioritas:** P0 / Fitur interaktif utama.

**Pertanyaan:** Jika rupiah melemah sebesar persentase tertentu, berapa perubahan harga yang konsisten dengan profil respons historis?

**Tipe:** Multi-line chart with confidence band.

**Data:**

- Profil respons PT(h).
- Bootstrap interval.
- Komoditas.
- Wilayah.
- Horizon.

**Rumus:**

Perubahan harga bersyarat pada horizon h:

ΔP(h) = PT(h) × X

Dengan X adalah besarnya perubahan kurs yang dipilih.

**Skenario awal:**

- Depresiasi 1%.
- Depresiasi 3%.
- Depresiasi 5%.

**Kontrol:**

- Komoditas.
- Kelompok wilayah.
- Provinsi jika estimasi tersedia.
- Besar perubahan kurs.
- Horizon.

**Encoding:**

- X: horizon 0–12.
- Y: perubahan harga bersyarat.
- Garis: skenario.
- Area: interval estimasi.

**Output tambahan:**

- Nilai pada horizon 4.
- Nilai pada horizon 8.
- Nilai pada horizon 12.
- Status deteksi.
- Peringatan ekstrapolasi.

**Pengaman wajib:**

Tampilkan label:

"SKENARIO BERSYARAT — BUKAN RAMALAN."

Jangan menampilkan hasil sebagai prediksi harga aktual.

Jika respons tidak terdeteksi, tampilkan keterbatasan estimasi dan batas deteksi.

---

# 9. P06 Temuan Penelitian

Halaman ini bukan tempat menampilkan semua grafik kembali.

Fungsinya menyampaikan temuan yang sudah dibuktikan oleh hasil analisis.

## Komponen

### 9.1 Executive Findings

Ringkasan:

- Temuan respons kurs.
- Temuan respons harga dunia.
- Temuan heterogenitas.
- Temuan clustering.
- Temuan eksposur.
- Temuan nilai prediktif.

### 9.2 Evidence-linked Findings

Setiap temuan harus memiliki:

- Pernyataan.
- Angka pendukung.
- Visualisasi sumber.
- Interval atau ukuran ketidakpastian.
- Keterbatasan.

### 9.3 Methodological Limitations

Tampilkan keterbatasan yang relevan:

- Informasi kurs efektif hanya sekitar 460 minggu.
- Sinyal kurs didominasi beberapa episode besar.
- Harga provinsi merupakan agregat kota sampel.
- Data carry-forward.
- Observasional dan bukan kausal.
- Potensi keterbatasan deteksi heterogenitas.

### 9.4 Interpretation Rules

Gunakan bahasa:

- "Berasosiasi dengan".
- "Terlihat pola".
- "Respons terdeteksi".
- "Respons belum terdeteksi".
- "Tidak ditemukan struktur regional yang cukup kuat".
- "Performa prediktif meningkat/menurun".

Hindari:

- "Kurs menyebabkan harga naik".
- "Harga pasti akan naik".
- "Provinsi ini paling rentan" jika estimasi tidak mendukung.
- "Tidak ada efek" hanya karena hasil tidak signifikan.

---

# 10. Interactive Visualization Specification

## 10.1 Interactive Visualization Mantra

Implementasi mengikuti:

1. Overview First.
2. Zoom and Filter.
3. Details-on-Demand.

## 10.2 Interaksi Global

| ID  | Interaksi       | Fungsi                            |
| --- | --------------- | --------------------------------- |
| I01 | Global filter   | Filter komoditas dan wilayah      |
| I02 | Hover tooltip   | Melihat detail nilai              |
| I03 | Click-to-filter | Memilih wilayah atau cluster      |
| I04 | Brushing        | Menyorot kelompok titik           |
| I05 | Drill-down      | Nasional → 7 wilayah → provinsi |
| I06 | Reset           | Mengembalikan filter              |
| I07 | Cross-filtering | Menyinkronkan grafik terkait      |

## 10.3 Hubungan Antarvisualisasi

Contoh:

1. Pengguna memilih bawang putih.
2. Peta memperlihatkan estimasi respons wilayah.
3. Pengguna memilih Sulawesi.
4. IRF memperbarui hasil wilayah tersebut.
5. Forest plot menampilkan pembanding.
6. Detail estimasi menampilkan interval dan status deteksi.

Interaksi hanya diterapkan jika unit analisis dan definisi variabel memang kompatibel.

---

# 11. Data Contract untuk Visualisasi

Setiap grafik harus mempunyai kontrak data agar tidak mengambil data langsung dari notebook atau menghitung ulang model.

| File                            | Penggunaan                              |
| ------------------------------- | --------------------------------------- |
| `panel_weekly.parquet`        | Data observasi utama jika izin tersedia |
| `panel_weekly_region.parquet` | Data agregat tujuh wilayah              |
| `profiles.parquet`            | Profil respons dan interval             |
| `boot_replicates.parquet`     | Replikasi bootstrap                     |
| `placebo_stats.parquet`       | Distribusi plasebo                      |
| `events.parquet`              | Event study                             |
| `clusters.parquet`            | Hasil clustering                        |
| `coassign.parquet`            | Matriks co-assignment                   |
| `assoc.csv`                   | Asosiasi eksposur                       |
| `forecast_eval.csv`           | Evaluasi prediktif                      |
| `robustness.csv`              | Hasil robustness                        |
| `exposure.csv`                | Jalur eksposur komoditas                |
| `concordance.csv`             | Pemetaan komoditas                      |
| `regulation.csv`              | Informasi regulasi                      |
| `checksums.csv`               | Integritas snapshot                     |

## 11.1 Prinsip Data Contract

- Setiap dataset mempunyai schema.
- Setiap dataset mempunyai identifier yang konsisten.
- Setiap nilai estimasi mempunyai satuan.
- Interval mempunyai lower dan upper bound.
- Data missing dibedakan dari nol.
- Hasil bootstrap dan placebo tidak dihitung ulang di Streamlit.
- Semua grafik membaca output hasil pipeline yang telah dibekukan.

## 11.2 Rekomendasi Schema Tambahan

Untuk memudahkan visualisasi, standardisasi kolom berikut jika belum tersedia:

**profiles.parquet**

- commodity_id
- region_id
- province_id
- driver
- horizon
- estimate
- ci_lower
- ci_upper
- mde
- detection_status

**clusters.parquet**

- province_id
- cluster_id
- selected_k
- silhouette
- jaccard
- ari
- cluster_status

**coassign.parquet**

- province_i
- province_j
- coassignment_probability

**forecast_eval.csv**

- commodity_id
- region_id
- horizon
- model
- mae
- rmse
- mae_ratio
- rmse_ratio
- origin_count
- non_overlapping_window_count

**events.parquet**

- event_id
- commodity_id
- region_id
- horizon
- actual_response
- placebo_lower
- placebo_upper

Kolom di atas merupakan rekomendasi kontrak aplikasi. Nama dan definisi final harus disesuaikan dengan artefak hasil pipeline yang benar-benar dihasilkan.

---

# 12. Arsitektur Implementasi Streamlit

## 12.1 Prinsip Arsitektur

Pisahkan tiga lapisan:

1. Data layer.
2. Visualization layer.
3. Application layer.

Streamlit tidak bertugas menjalankan analisis ekonometrika atau machine learning.

## 12.2 Struktur Direktori TAMBAHAN yang Direkomendasikan

```text
datmin/
│
├── app/
│   ├── main.py
│   │
│   ├── pages/
│   │   ├── 01_overview.py
│   │   ├── 02_regional_sensitivity.py
│   │   ├── 03_response_patterns.py
│   │   ├── 04_exposure_prediction.py
│   │   ├── 05_scenario_explorer.py
│   │   └── 06_research_findings.py
│   │
│   ├── components/
│   │   ├── kpi.py
│   │   ├── filters.py
│   │   ├── tooltips.py
│   │   ├── interpretation.py
│   │   ├── status_badges.py
│   │   └── chart_containers.py
│   │
│   ├── visualizations/
│   │   ├── coverage.py
│   │   ├── irf.py
│   │   ├── choropleth.py
│   │   ├── forest_plot.py
│   │   ├── event_study.py
│   │   ├── cluster_map.py
│   │   ├── dendrogram.py
│   │   ├── coassignment.py
│   │   ├── silhouette.py
│   │   ├── exposure.py
│   │   ├── prediction.py
│   │   └── scenario.py
│   │
│   ├── services/
│   │   ├── data_loader.py
│   │   ├── filters.py
│   │   ├── selectors.py
│   │   └── interpretation.py
│   │
│   ├── config/
│   │   ├── chart_config.py
│   │   ├── colors.py
│   │   └── labels.py
│   │
│   └── utils/
│       ├── formatting.py
│       ├── validation.py
│       └── metadata.py
│
├── data/
│   └── processed/
│
├── assets/
│   ├── maps/
│   └── icons/
│
├── tests/
│   ├── test_data_contracts.py
│   ├── test_visualizations.py
│   ├── test_filters.py
│   └── test_interpretation.py
│
├── requirements.txt
└── README.md
```

Struktur ini merupakan usulan organisasi aplikasi, bukan keharusan untuk mengubah seluruh struktur repository yang sudah ada.

## 12.3 Teknologi

| Kebutuhan                | Rekomendasi             |
| ------------------------ | ----------------------- |
| Application framework    | Streamlit               |
| Interactive charts       | Plotly                  |
| Geographic maps          | Plotly / GeoPandas      |
| Statistical charts       | Plotly                  |
| Data processing          | Pandas / Polars         |
| Data storage             | Parquet                 |
| Clustering visualization | SciPy / Plotly          |
| Statistical formatting   | Custom Python utilities |

Utamakan satu library visualisasi utama agar interaksi, tooltip, tema, dan format grafik konsisten.

---

# 13. Implementation Roadmap

## Phase 0 — Data Contract Audit

Tujuan:
Memastikan seluruh output penelitian tersedia dan dapat digunakan.

Checklist:

- [ ] Audit seluruh output Parquet dan CSV.
- [ ] Periksa nama kolom.
- [ ] Periksa tipe data.
- [ ] Periksa nilai missing.
- [ ] Periksa interval estimasi.
- [ ] Periksa identifier wilayah dan komoditas.
- [ ] Pastikan hasil bootstrap tersedia.
- [ ] Pastikan hasil placebo tersedia.
- [ ] Pastikan hasil clustering tersedia.
- [ ] Pastikan hasil evaluasi prediktif tersedia.

Deliverable: Data Contract Specification.

## Phase 1 — Design System

Checklist:

- [ ] Menentukan warna utama.
- [ ] Menentukan warna status.
- [ ] Menentukan warna respons positif dan negatif.
- [ ] Menentukan tipografi.
- [ ] Menentukan format angka.
- [ ] Menentukan komponen tooltip.
- [ ] Menentukan komponen interpretasi.
- [ ] Menentukan navigasi.
- [ ] Menentukan layout dasar.

Deliverable: UI Design System.

## Phase 2 — Core Dashboard

Checklist:

- [ ] Membuat navigasi enam halaman.
- [ ] Membuat global filter.
- [ ] Membuat komponen KPI.
- [ ] Membuat data loader.
- [ ] Membuat caching.
- [ ] Membuat chart container.
- [ ] Membuat empty state.
- [ ] Membuat loading state.
- [ ] Membuat error state.

Deliverable: Streamlit application skeleton.

## Phase 3 — Core Visualizations

Prioritas:

1. Coverage Heatmap.
2. Impulse Response Function.
3. Choropleth Map.
4. Forest Plot.
5. Cluster Map.
6. Co-assignment Heatmap.
7. MAE Ratio Plot.
8. Scenario Response Chart.

Deliverable: Core analytical dashboard.

## Phase 4 — Advanced Visualizations

Checklist:

- [ ] Event Study.
- [ ] Dendrogram.
- [ ] Silhouette vs Placebo.
- [ ] Exposure Scatter Plot.
- [ ] Provincial Exposure Scatter Plot.
- [ ] Feature Ablation Heatmap.
- [ ] Structure Recovery Curve.

Deliverable: Advanced exploration dashboard.

## Phase 5 — Interaction and Interpretation

Checklist:

- [ ] Cross-filtering.
- [ ] Click-to-filter.
- [ ] Hover tooltip.
- [ ] Drill-down.
- [ ] Reset filters.
- [ ] Interpretasi otomatis.
- [ ] Penanganan k = 1.
- [ ] Penanganan respons tidak terdeteksi.
- [ ] Penanganan interval yang mencakup nol.
- [ ] Penanganan ekstrapolasi skenario.

Deliverable: Interactive analytical application.

## Phase 6 — Validation and Quality Assurance

Checklist:

- [ ] Bandingkan nilai grafik dengan file sumber.
- [ ] Verifikasi seluruh interval.
- [ ] Verifikasi format angka.
- [ ] Verifikasi filter.
- [ ] Verifikasi hubungan antarvisualisasi.
- [ ] Verifikasi kasus missing.
- [ ] Verifikasi hasil tidak signifikan.
- [ ] Verifikasi clustering k = 1.
- [ ] Verifikasi skenario bersyarat.
- [ ] Uji aplikasi tanpa koneksi internet.
- [ ] Uji jalan ulang pada lingkungan bersih.

Deliverable: Final Streamlit application.

---

# 14. Acceptance Criteria

Visualisasi dinyatakan selesai apabila memenuhi kriteria berikut.

| Kategori        | Acceptance Criteria                                            |
| --------------- | -------------------------------------------------------------- |
| Correctness     | Nilai sama dengan sumber hasil analisis                        |
| Uncertainty     | Interval ditampilkan ketika tersedia                           |
| Interpretation  | Tidak menghasilkan klaim yang tidak didukung                   |
| Interaction     | Filter bekerja sesuai unit analisis                            |
| Performance     | Tidak menjalankan ulang model saat pengguna mengganti filter   |
| Reliability     | Missing dan hasil kosong ditangani                             |
| Consistency     | Warna, satuan, dan format seragam                              |
| Reproducibility | Aplikasi dapat berjalan dari artefak yang disertakan           |
| Offline support | Tidak bergantung pada koneksi internet untuk menampilkan hasil |
| Data rights     | Tidak mendistribusikan data mentah tanpa izin                  |

---

# 15. Visualisasi yang Tidak Direkomendasikan

| Visualisasi                        | Keputusan            | Alasan                                          |
| ---------------------------------- | -------------------- | ----------------------------------------------- |
| Pie chart                          | Hindari              | Tidak menjawab pertanyaan utama                 |
| Gauge chart                        | Hindari              | Tidak sesuai untuk ketidakpastian estimasi      |
| 3D bar chart                       | Hindari              | Sulit dibandingkan                              |
| Rainbow choropleth                 | Hindari              | Skala berurutan tidak jelas                     |
| Dual-axis chart                    | Hindari              | Berpotensi menyesatkan                          |
| Terlalu banyak garis IRF           | Hindari              | Menurunkan keterbacaan                          |
| 3D clustering sebagai visual utama | Hindari              | Proyeksi dapat menyembunyikan struktur          |
| Radar chart                        | Tidak diprioritaskan | Sulit membandingkan banyak profil secara akurat |

---

# 16. Referensi dan Landasan Desain

## 16.1 Materi IF4061

1. Interactive Visualization:

   - Overview First, Zoom and Filter, Details-on-Demand.
   - Data Manipulation Loop.
   - Exploration and Navigation Loop.
   - Problem Solving Loop.
2. Holistic Dashboard:

   - Struktur informasi top-down.
   - Pemilihan chart.
   - Hierarki visual.
   - Pembatasan jumlah visualisasi.
   - Organisasi layout.
3. Map Visualization:

   - Color Symbols.
   - Proportional Symbols.
   - Sequential Color Scheme.
   - Diverging Scheme.
   - Quantiles.
   - Equal Intervals.
   - Natural Breaks.
4. Visual Data Mining:

   - Clustering.
   - Dimensionality problems.
   - OPTICS.
   - Vector Quantization.
   - Visualisasi hasil clustering.

## 16.2 Referensi Tambahan

- Datawrapper: Choropleth Map Guidelines — https://www.datawrapper.de/blog/choroplethmaps
- Office for National Statistics: Showing Uncertainty in Charts — https://service-manual.ons.gov.uk/data-visualisation/guidance/showing-uncertainty-in-charts
- European Data Visualisation Guide — https://data.europa.eu/apps/data-visualisation-guide/error-bars-and-the-cone-of-uncertainty
- Iglesias, Zseby & Zimek: Clustering Refinement — https://link.springer.com/article/10.1007/s41060-021-00275-z

---

# 17. Keputusan Akhir Desain

KAGAMI harus dibangun sebagai analytical dashboard yang memiliki tiga identitas utama:

**1. Econometric Exploration**

IRF, confidence bands, forest plot, dan event study menjelaskan profil respons harga.

**2. Regional Pattern Discovery**

Choropleth, dendrogram, co-assignment heatmap, dan silhouette comparison menjelaskan pola regional serta validitas clustering.

**3. Predictive and Scenario Evaluation**

Exposure scatter, MAE ratio, feature ablation, dan scenario response menjelaskan nilai prediktif dan implikasi bersyarat dari hasil penelitian.

## Prioritas Final

| Tingkat | Komponen                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------- |
| P0      | IRF, Choropleth, Forest Plot, Cluster Map, Co-assignment Heatmap, Silhouette vs Placebo, MAE Ratio, Scenario Response         |
| P1      | Coverage Heatmap, Data Quality, MDE Summary, Event Study, Dendrogram, Exposure Scatter, Provincial Exposure, Feature Ablation |
| P2      | Structure Recovery Curve dan visualisasi eksploratif tambahan                                                                 |

**Keputusan desain utama:**

Jangan membangun Streamlit sebagai kumpulan grafik yang tidak saling berhubungan. Bangun sebagai satu alur eksplorasi penelitian:

Data Quality → Econometric Evidence → Regional Pattern → Exposure & Predictive Value → Conditional Scenario → Research Findings.

Dengan demikian, setiap visualisasi mempunyai alasan keberadaan, sumber data, fungsi analitis, dan hubungan yang jelas dengan pertanyaan penelitian KAGAMI.

**Dokumen ini menjadi acuan utama desain dan implementasi visualisasi KA. Setiap perubahan terhadap grafik, variabel, atau interpretasi harus tetap konsisten dengan metodologi dan hasil penelitian pada Proposal v4.**
