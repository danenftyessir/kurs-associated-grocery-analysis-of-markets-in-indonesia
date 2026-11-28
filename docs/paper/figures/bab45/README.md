# Gambar Bab 4 & Bab 5 (PNG, 300 dpi)

Dibuat oleh `docs/paper/scripts/make_figures_bab45.py` (grafik & tabel dari artefak) dan
`docs/paper/scripts/capture_app_bab45.py` (tangkapan layar app). Tidak ada estimasi baru. Tiga gambar Task 4 arah dan model
deep memakai prediksi eksploratif dan wajib diberi label "eksploratif" di keterangan.

## Bab 4 — Hasil Eksperimen dan Pengujian

| Berkas | Visualisasi template | Saran keterangan |
|---|---|---|
| `b4_01_konfigurasi_eksperimen.png` | Experimental Configuration Table | Konfigurasi eksperimen per task, dibekukan sejak praregistrasi 20-11-2026. |
| `b4_02_matriks_skenario.png` | Experimental Scenario Matrix | Skenario eksperimen menurut task dan tingkat bukti (praregistrasi, validasi, kepekaan inferensi, eksploratif). |
| `b4_03_perbandingan_model.png` | Model / Algorithm Performance Comparison | (a) Rasio MAE terhadap M1 untuk model resmi dan model deep. (b) F1 makro arah naik/turun pada periode uji 2024+ (eksploratif). |
| `b4_04_confusion_matrix_arah.png` | Confusion Matrix (hanya untuk task arah) | Confusion matrix C1-tuned pada periode uji 2024+. Eksploratif, bukan uji praregistrasi. |
| `b4_05_clustering.png` | Clustering Visualization | (a) Silhouette Ward di bawah ambang plasebo, sehingga k = 1. (b) 34 provinsi di dua komponen utama. (c) Batas deteksi struktur tertanam. |
| `b4_06_faktor_penjelas.png` | Feature Importance (diganti) | Asosiasi karakteristik provinsi (meta-regresi) dan rasio impor (Kendall) dengan respons. Semua interval memuat nol. |
| `b4_07_dashboard_metrik.png` | Evaluation Metrics Dashboard | Ringkasan metrik evaluasi setiap task: deteksi, H0-Het, asimetri, rasio MAE & DM, ketahanan, MDE. |
| `b4_08_app_ringkas.png` (+ 6 berkas per halaman) | Screenshot aplikasi | Tampilan app KAGAMI: Ringkasan, Cerita data, Respons harga, Simulasi rupiah. |
| `b4_09_matriks_pengujian_fungsional.png` | Functional Testing Matrix | Pengujian otomatis per komponen (pytest), jumlah tes lolos/dilewati/gagal. |

## Bab 5 — Analisis Hasil

| Berkas | Visualisasi template | Saran keterangan |
|---|---|---|
| `b5_01_analisis_galat.png` | Error Analysis | Galat Task 4 per komoditas × tahun, menurut besar perubahan, dan menurut porsi rangkaian harga identik. |
| `b5_02_perbandingan_algoritma.png` | Algorithm Comparison Analysis | Uji DM berpasangan antarmodel (h = 8) dan kestabilan model deep antar 3 seed. |
| `b5_03_sensitivitas_parameter.png` | Parameter Sensitivity Analysis | Estimasi utama vs cek ketahanan (lag, sub-periode, tanpa COVID, dekomposisi kurs, agregasi, frekuensi) untuk empat sel kunci. |
| `b5_04_kontribusi_komponen.png` | Feature / Component Contribution | Ablation fitur kurs per komoditas dan efek menambah kurs di tiga keluarga model. |
| `b5_05_interpretasi_klaster.png` | Cluster Interpretation (k = 1) | Heterogenitas per komoditas dan deviasi provinsi untuk telur ayam & daging ayam. |
| `b5_06_analisis_kasus_gagal.png` | Failure Case Analysis | Origin tempat fitur kurs memperburuk ramalan, dan komoditas tempat prediksi arah kalah dari tebakan mayoritas. |
| `b5_07_matriks_pemenuhan_kebutuhan.png` | Requirement Fulfillment Matrix | Pemenuhan kebutuhan riset & produk, termasuk hasil nol yang sah dan validasi TPID yang belum dilakukan. |
| `b5_08_kualitas_produk.png` | (tambahan) Kualitas produk | Task coverage, evaluation consistency, usability, reliability, reproducibility dengan bukti. |
