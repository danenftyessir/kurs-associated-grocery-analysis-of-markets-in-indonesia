# Protokol D-163a — kalibrasi skor daftar pantau C1-tuned (dibekukan sebelum diukur, 2026-11-26)

Kartu 8 komponen (`docs/EKSPERIMEN.md` §2). Tanpa model atau fitur baru: lapisan kalibrasi pasca-model di atas p_up C1-tuned beku.

| Komponen | Isi |
|---|---|
| Problem | S2 (kalibrasi, D-154) gagal tipis di dev h 8: ECE 0,056 > 0,05 (h 4 0,035; test 0,010 / 0,021). Bila skor ditampilkan sebagai peluang di daftar pantau, peluang harus dapat dibaca apa adanya. |
| Data characteristic | Reliabilitas dev h 8: bin p 0,0–0,1 rerata p 0,074 vs porsi naik 0,206; bin 0,1–0,2 0,151 vs 0,208 → skor rendah terlalu yakin "turun". Laju naik bergeser antarperiode (D-147/D-148). |
| Knowledge discovery | Apakah salah kalibrasi C1-tuned stabil di sepanjang waktu (dapat dipelajari dari origin lampau) atau bergeser per periode? |
| Hypothesis | Pemetaan monoton logit(p) → peluang yang dipelajari walk-forward dari prediksi OOS lampau menurunkan ECE dan Brier tanpa mengubah ranking daftar pantau. |
| Method | Per horizon, di setiap origin o: latih kalibrator pada baris origin o' dengan o' + h ≤ o (target terealisasi) dan y ≠ 0; minimal 6 origin, selain itu identitas. K1 Platt global (logit p' = a + b·logit p); K2 Platt + intersep komoditas (mengubah ranking lintas komoditas); K3 isotonik global (p dipotong ke [0,001; 0,999]). |
| Validation | Dev saja (origin + h ≤ 2023-12-31): ECE 10 bin & Brier pada y ≠ 0 seperti `bu.py`; ΔBrier vs C1-tuned + interval bootstrap blok origin berpasangan (1999 rep); BSS vs klimatologi komoditas; S1 presisi V1 (2 teratas per provinsi, kenaikan material) vs C1-tuned; macro F1 (ambang 0,5) hanya informasi. |
| Leakage control | Kalibrator memakai prediksi OOS origin lampau yang targetnya terealisasi sebelum o; ambang material & klimatologi dari baris latih per origin (sama dengan `bu.py`); p_up C1-tuned = `direction_tuned_preds` resmi (identik dengan `d151_iw_dev_preds` varian base). |
| Decision | Varian diterima bila di dev: ECE ≤ 0,05 di kedua horizon, ΔBrier < 0 di kedua horizon dengan batas atas interval ≤ 0 di ≥ 1 horizon, dan presisi S1 V1 tidak turun > 0,005 (titik). Bila > 1 lolos: urutan K1 → K3 → K2 (paling sederhana). Varian terpilih saja yang dinilai sekali di test 2024+ (bukan validasi independen, D-155). Tidak ada yang lolos → C1-tuned tanpa kalibrasi tetap; ECE 0,056 dilaporkan apa adanya. |
