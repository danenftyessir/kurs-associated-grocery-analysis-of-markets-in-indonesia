# Protokol D-156 — Audit preprocessing & optimasi macro F1 Task 4 (arah, EKSPLORATIF)

Ditulis dan di-hash **sebelum** run modeling (`scripts/m_run.py`). Pengecualian yang diungkap: satu pekerjaan uji asap (h 8, origin
2023-10-09) dijalankan sebelum protokol ini untuk memeriksa mesin; yang dilihat hanya waktu per varian dan kecocokan `base` dengan
`direction_tuned_preds` C1t (selisih p_up 0,0), bukan metrik kandidat.

## 1. Data & pembagian waktu
- Tabel: `base.parquet` (tabel resmi C1-tuned + kolom kualitas label D-147) + keluarga fitur baru `scripts/c_feats.py` → `fam.parquet`.
  Baris, urutan, dan target identik dengan tabel resmi; kolom resmi yang dihitung ulang identik (dicek di `c_feats.py`).
- Origin pengembangan: origin + h ≤ 2023-12-31 (38 origin h 4, 37 origin h 8). Split resmi `split_origin` (latih t + h ≤ origin).
- **Test (origin ≥ 2024-01-01) tidak dibuka** untuk seleksi apa pun. Satu-satunya pengecualian §6.
- Label & baris evaluasi resmi: tanda y = log p_{t+h} − log p_t, y = 0 dikeluarkan dari metrik dan latih; semua perubahan kecil tetap.

## 2. Pembanding
C1-tuned beku: `tuned_columns("C1t", h)`, `TUNED_HGB`, seed 20261121, threshold 0,5. Varian `base` di setiap pekerjaan harus
mereproduksi `direction_tuned_preds` C1t persis (diperiksa di evaluasi).

## 3. Kandidat (daftar tetap; tidak ada pencarian hyperparameter)

| ID | Fase | Isi |
|---|---|---|
| B_recency | B | bobot latih peluruhan waktu, paruh 104 minggu |
| B_win156 | B | latih hanya 156 minggu terakhir sebelum origin |
| C_A … C_G | C | C1t + satu keluarga fitur baru (A momentum, B volatilitas, C posisi harga, D1 kualitas data panel, D2 cakupan hari dari `pihps_daily`, E lintas provinsi LOO/rank, F kalender Iduladha/Natal/Ramadan + profil musiman ekspansif, G interaksi/normalisasi); isi kolom di docstring `c_feats.py` |
| C_rm_<kelompok> | C | C1t tanpa satu kelompok terpilih (lag, rmean, rstd, mom, season, dev, comm) — seleksi fitur |
| C_COMBO | C | C1t + gabungan keluarga yang dipilih **hanya** dari origin dev-awal (origin < 2022-07-01): keluarga dengan Δ rerata (h 4, h 8) > 0 di dev-awal; dinilai **hanya** di origin dev-akhir (≥ 2022-07-01) |
| D_cw | D | bobot kelas seimbang |
| D_seed5 | D | rerata probabilitas 5 seed HGB (seed resmi + 0..4) |
| D_thr_wf | D | threshold global per horizon, walk-forward: pada origin o dipilih (grid 0,30–0,70, langkah 0,005) dari prediksi `base` origin dev o' dengan o' + h ≤ o (≥ 4 origin, selain itu 0,5) |
| D_thr_wf_comm | D | seperti D_thr_wf per komoditas (≥ 300 baris terealisasi, selain itu threshold global walk-forward) |
| E_lgb, E_xgb | E | LightGBM/XGBoost dengan konfigurasi dipetakan dari TUNED_HGB (lr 0,0281, 250 pohon, 23 daun, l2 3,85, kolom 0,335; min daun 319 / min_child_weight 80) |
| E_cat | E | CatBoost 500 iterasi, lr 0,05, depth 6, l2 3, kategori native |
| E_et | E | ExtraTrees 300 pohon, min daun 50, max_features 0,33 (imputasi median + indikator, one-hot) |
| E_lr | E | regresi logistik C 0,1 (imputasi median + indikator, standardisasi, one-hot) — diagnostik |

Kalibrasi probabilitas monoton (Platt/isotonik) dengan threshold 0,5 setara dengan memilih threshold → dicakup D_thr_wf; tidak dijalankan
terpisah. Hyperparameter HGB sudah dicari di D-145 (Optuna 40 trial); tidak diulang.

## 4. Metrik (per kandidat, per horizon)
macro F1 + interval bootstrap blok origin (1.999); F1 naik/turun; MCC; ROC-AUC; porsi prediksi naik; rerata & sd macro F1 per origin;
Δ berpasangan vs `base` (interval, p); Δ per tahun origin (2021, 2022, 2023); porsi origin dengan Δ > 0; Δ kuintil |y| terkecil (ambang
dari `base`); Δ per komoditas; q BH dalam keluarga semua kandidat D-156 per horizon.

## 5. Aturan "lebih baik secara berarti" (semua harus terpenuhi)
1. Δ macro F1 rerata (h 4, h 8) ≥ +0,005; interval berpasangan > 0 di ≥ 1 horizon; Δ ≥ 0 di horizon lain (aturan EKSPERIMEN §4).
2. q BH < 0,05 pada horizon dengan interval > 0.
3. Konsisten: Δ ≥ 0 di ≥ 2 dari 3 tahun dev pada kedua horizon, dan porsi origin Δ > 0 ≥ 0,5 pada kedua horizon.
4. Tidak ada kemunduran tersembunyi: Δ F1 naik dan Δ F1 turun ≥ −0,01 di kedua horizon; tidak ada komoditas dengan Δ < −0,03 di kedua horizon.
5. Kebocoran: fitur baru lolos `c_leak.py` (0 sel berbeda); threshold walk-forward hanya memakai label terealisasi.
6. D_seed5 dinilai sebagai pengurangan varians (tidak mengubah informasi); E_lr hanya diagnostik (tidak dapat dipilih).

## 6. Pembukaan test
Hanya bila ≥ 1 kandidat memenuhi §5: satu kandidat (Δ rerata terbesar; seri → kolom paling sedikit) dievaluasi sekali pada origin
≥ 2024-01-01, dilaporkan sebagai "evaluasi eksploratif dengan kriteria tetap" (test bukan data independen, D-155), bersama kriteria bisnis
S1–S3 (D-154). Pengecualian: kandidat yang memakai data harian (`C_D2`, atau C_COMBO yang memuat D2) tidak membuka test karena keluarga
data harian sudah memakai test dua kali (EKSPERIMEN §4); konfirmasinya hanya lewat prediksi maju. Bila tidak ada yang lolos, test tidak
dibuka dan kesimpulan ditulis apa adanya.

## 7. Kontrol kebocoran & reproduksi
- Fitur baru: perturbasi & penghapusan data sesudah origin pada 12 origin 2021–2026 → 0 sel berbeda (`hasil/c_leak.csv`).
- Latih hanya t + h ≤ origin; C_COMBO dipilih dan dinilai pada origin dev yang terpisah; threshold walk-forward.
- Seed resmi 20261121; numpy 2.3, pandas 2.3, scikit-learn 1.8.0, LightGBM 4.6.0, XGBoost 3.0.5, CatBoost 1.2.8, Python 3.13.7.
- Layar DU (`hasil/c_du.csv`): tidak ada fitur baru yang lolos gerbang EKSPERIMEN §3. Ablation keluarga tetap dijalankan atas permintaan
  eksplisit (master task) dan untuk menguji apakah gerbang DU memprediksi hasil Modeling; ini pengecualian yang dicatat, bukan pelonggaran aturan.
