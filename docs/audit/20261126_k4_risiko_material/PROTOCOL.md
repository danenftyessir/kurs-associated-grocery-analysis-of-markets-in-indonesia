# Protokol K4 — risiko kenaikan harga material (EKSPLORATIF, D-164)

Ditulis 2026-11-26 sesudah Data Understanding (`DATA_UNDERSTANDING.md`, hanya origin pengembangan) dan **sebelum** model K4 mana pun
dilatih. Tidak diubah sesudahnya. sha256 protokol & skrip saat beku: `hasil/protocol_sha256.txt`. Perubahan hanya lewat adendum bertanggal
sebelum pengukuran berikutnya. Jalur ini terpisah dari optimasi macro F1 (D-156, D-165): tidak ada angka K4 yang dibaca sebagai macro F1.

## 1. Kartu eksperimen (EKSPERIMEN §2)

| Komponen | Isi |
|---|---|
| Problem | TPID perlu tahu seri (provinsi × komoditas) mana yang berisiko **naik secara material** 4–8 minggu ke depan. C1-tuned mengestimasi P(naik \| y ≠ 0, X), bukan P(kenaikan material \| X) (D-155). Skor arah dipakai sebagai daftar pantau D-154 tanpa pernah dilatih pada target itu. |
| Data characteristic | DU dev: laju-dasar z 0,120 / 0,132 (h 4 / h 8), sangat beragam antarkomoditas (0,024 bawang putih .. 0,29 minyak goreng); 60% / 64% positif pada 4 komoditas diatur (ambang 1,2–3,9%, ± 3–18 tick); laju bergeser kuat menurut waktu (sd mingguan 0,07 / 0,08; musim Jun–Agu 0,05–0,09 vs Nov–Apr 0,15–0,18); antarprovinsi kecil (0,09–0,15); 12% / 21% kejadian kapan pun adalah lonjakan yang berbalik. |
| Knowledge discovery | Apakah risiko kenaikan material dapat diurutkan & diberi peluang lebih baik oleh model yang dilatih langsung pada z daripada oleh skor arah, aturan naif, atau laju-dasar komoditas? Apa yang membedakan alarm benar dari alarm palsu? |
| Hypothesis | Klasifier pada z (semua baris, termasuk y = 0) belajar magnitudo & kekakuan (y = 0 tidak lagi dibuang), sehingga ranking (AP, presisi@K) dan kalibrasi peluang lebih baik daripada p_up C1-tuned, dan lebih baik dari laju-dasar komoditas yang sudah menangkap komposisi target. |
| Method | HGB dengan kolom & hyperparameter C1-tuned beku (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed 20261121), label z, tanpa bobot kelas, tanpa tuning (hyperparameter tidak dicari ulang untuk target ini; ditulis sebagai keterbatasan). |
| Validation | Rolling-origin resmi (origin tiap 4 minggu, latih t + h ≤ origin), dev saja untuk seleksi; bootstrap blok origin berpasangan; BH pada keluarga uji utama; stabilitas per tahun dev; pembanding C1-tuned, C1-tuned terkalibrasi walk-forward, laju-dasar komoditas (± bulan), 4 aturan naif D-154. |
| Leakage control | Ambang dari baris latih origin itu; label latih hanya jendela yang sudah berakhir ≤ origin (termasuk jendela kejadian); kalibrator dari origin lampau yang targetnya terealisasi; fitur = tabel resmi (sudah diuji D-147/D-156); uji perturbasi target/harga sesudah origin (`k4_leak.py`). |
| Decision | §5 (ditulis sebelum hasil). |

## 2. Target, universe, varian

- **Target utama** (materialitas statistik, proxy): z = 1[y_h ≥ thr(o,h,c)], y_h = log p_{t+h} − log p_t (rerata hari teramati),
  thr = persentil 80 |y_h| baris latih komoditas c pada origin o (week + h ≤ o, y_h & lag tersedia) = aturan D-154. z = 0 untuk turun,
  tetap (y = 0), naik di bawah ambang, dan target tidak teramati (D-155).
- **Universe** origin o: semua seri dengan lag harga tersedia pada o (termasuk y = 0 dan target tak teramati). Baris latih: week + h ≤ o,
  target terealisasi, lag ada; label latih memakai ambang origin o.
- **Target alternatif (Fase E)**: z_any = 1[max_{k=1..h}(log p_{t+k} − log p_t) ≥ thr(o,h,c)] (minggu hilang dilewati; ambang sama).
- Varian (semua HGB sama, hanya label berubah):

| ID | Label | Peran |
|---|---|---|
| **K4-E80** | z (P80 \|y\|) | kandidat utama |
| K4-E80-cal | Platt global walk-forward atas skor K4-E80 → z (ranking tidak berubah) | varian peluang |
| K4-A80 | z_any (P80 \|y\|) | target alternatif, deskriptif |
| K4-E70, K4-E90 | z dengan P70 / P90 \|y\| | kepekaan ambang, deskriptif, bukan seleksi |
| K4-S90 | z dengan P90 y **bertanda** (desil atas kenaikan per komoditas) | kepekaan komposisi target, deskriptif |

- **Pembanding**: B-C1t (p_up C1-tuned; refit harus identik dengan `direction_tuned_preds`), B-C1t-cal (Platt global walk-forward
  logit p_up → z), B-CLIM (porsi z komoditas di baris latih), B-CLIMS (porsi z komoditas × bulan kalender origin di baris latih; < 50
  baris → B-CLIM), aturan naif D-154 `R_mom`, `R_nat`, `R_rev`, `R_seas`. "Naif terbaik" = AP pooled tertinggi di dev di antara B-CLIM,
  B-CLIMS, R_* per horizon (menguntungkan pembanding).
- Platt walk-forward: di origin o dilatih pada baris origin o' dengan o' + h ≤ o; dipakai bila ≥ 6 origin lampau, selain itu tidak
  dievaluasi. **Himpunan peluang** = origin dev yang punya kalibrator; semua perbandingan peluang memakai baris identik.

## 3. Ukuran

- Ranking (semua origin dev): AP / PR-AUC pooled (utama), AP rerata per origin, ROC-AUC, presisi@K & recall@K untuk V1-K (K = 1, 2, 3
  komoditas per provinsi per origin; tie dipecah acak seed 154 seperti D-154) dan V2-setara (2 × jumlah provinsi per origin, nasional).
- Peluang (himpunan peluang): Brier, log loss, ECE 10 bin, Brier skill vs B-CLIM, diagram reliabilitas.
- Operasional: alarm/origin, alarm benar/palsu, risiko terlewat (FN), recall per K, porsi alarm per komoditas, provinsi tanpa alarm
  (kebijakan ambang peluang τ ∈ {0,2; 0,3; 0,4} pada peluang terkalibrasi), persistensi alarm antarorigin.
- Utilitas: kurva keputusan (net benefit, τ 0,05..0,50) dan biaya FP + r·FN untuk r ∈ {1, 2, 5, 10} per kebijakan K — skenario eksplisit,
  bukan biaya nyata.
- Per komoditas, provinsi, origin, tahun dev. Inferensi: bootstrap blok origin berpasangan (blok ceil(h/4)+1, 1.999 replikasi, seed
  r = 0..1998), p dua sisi persentil.

## 4. Kontrol kebocoran & integritas (wajib lolos sebelum hasil dibaca)

1. B-C1t refit = artefak resmi `direction_tuned_preds` C1t pada baris bertarget (maks |Δp| ≤ 1e-9).
2. `k4_leak.py`: untuk 3 origin × 2 horizon, y_h / ymax_h baris dengan week + h > o dan harga mingguan sesudah o dirusak acak →
   ambang, label latih, dan prediksi K4-E80 / K4-A80 identik.
3. Universe dev = 12.800 / 12.463 baris (= 25.259 baris resmi + 4 baris tanpa target, D-155).

## 5. Aturan keputusan (dev; origin + h ≤ 2023-12-31)

- **R1 ranking** (K4-E80 vs B-C1t): ΔAP pooled > 0 dengan interval > 0 di ≥ 1 horizon dan ΔAP ≥ 0 di horizon lain; Δpresisi@K2 (V1)
  ≥ 0 (titik) di kedua horizon; ΔAP ≥ 0 di ≥ 2 dari 3 tahun dev (2021, 2022, 2023) di kedua horizon; q BH < 0,05 untuk horizon yang
  intervalnya > 0 (keluarga F = {ΔAP, Δpresisi@K2, ΔBrier} × {h 4, h 8}, 6 uji).
- **R1b** (vs naif terbaik): AP dan presisi@K2 K4-E80 ≥ naif terbaik (titik) di kedua horizon.
- **R2 peluang**: K4-E80 (mentah) dulu, lalu K4-E80-cal bila mentah gagal: ΔBrier vs B-C1t-cal < 0 dengan batas atas interval < 0 di
  ≥ 1 horizon dan ≤ 0 di horizon lain; ECE ≤ 0,05 di kedua horizon; Brier skill vs B-CLIM > 0 dengan interval > 0 di kedua horizon.
- Keputusan teknis: **ACCEPT** = R1 & R1b & R2 lolos; **PARTIAL** = (R1 & R1b) atau R2 lolos, tidak keduanya; **REJECT** = tidak ada.
  **Status operasional BLOCKED** sampai U109 (ambang kebijakan, kapasitas K, titik akhir vs kejadian) divalidasi, apa pun keputusan teknis.
- Hasil yang gagal tidak dilonggarkan; tidak ada kandidat atau fitur tambahan di sesi ini (Fase C3 hanya rekomendasi).

## 6. Test 2024+ & validasi prospektif

- Test dibuka **sekali** hanya bila keputusan dev ACCEPT atau PARTIAL (`k4_eval.py` menulis `hasil/k4_test_allowed.flag`), untuk varian
  terpilih + semua pembanding dengan definisi sama (naif terbaik dari dev). Ditulis "evaluasi eksploratif dengan kriteria yang ditetapkan
  sebelumnya" (test sudah dipakai D-145–D-154, bukan independen). Test tidak mengubah seleksi; bila Δ utama < 0 (titik) di kedua horizon,
  klaim diturunkan.
- Prediksi maju beku (`PART=forward`): semua origin mingguan dengan lag tersedia dan target belum terealisasi pada minggu data terakhir
  (h 4: 4 origin, h 8: 8 origin), K4-E80, K4-A80, B-C1t, laju-dasar; manifest sha256. Konfirmasi hanya dari prediksi maju ini.

## 7. Reproduksi

Seed 20261121; tabel `base.parquet` (tabel resmi C1-tuned + kolom kualitas label D-147; `KAGAMI_EXP`); numpy 2.3.4, pandas 2.3.3,
scipy 1.16.3, scikit-learn 1.8.0; Python 3.13. Urutan: `k4_du.py` → `k4_run.py` (PART=dev) → `k4_leak.py` → `k4_eval.py` → (bila diizinkan)
`k4_run.py` PART=test → `k4_eval.py` PART=test → `k4_run.py` PART=forward → `k4_log.py`.
