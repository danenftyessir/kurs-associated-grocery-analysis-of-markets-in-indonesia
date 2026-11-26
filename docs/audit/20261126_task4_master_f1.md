# Audit Preprocessing & Optimasi Macro F1 Task 4 — Klasifikasi Arah (EKSPLORATIF)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-156 · Lanjutan D-145–D-155. Catatan bertanggal (bukan dokumen
hidup). Protokol dibekukan sebelum run modeling: [PROTOKOL.md](20261126_task4_master_f1/PROTOKOL.md) (sha256 `f3b01357…`, waktu beku &
hash skrip di `hasil/protocol_sha256.txt`). Skrip & hasil: [folder lampiran](20261126_task4_master_f1/) (`scripts/`, `hasil/`). Registri
eksperimen terpusat: [`docs/eksperimen_registry.csv`](../eksperimen_registry.csv) (salinan bertanggal `hasil/registry.csv`).

Pertanyaan: dapatkah macro F1 klasifikasi arah dinaikkan di atas C1-tuned (0,677 / 0,680 test; 0,656 / 0,676 dev) tanpa mengubah label
resmi, tanpa membuang perubahan kecil, dengan seleksi hanya di origin pengembangan? Dari mana sisa galat berasal?

## 0. Ringkasan

| Pertanyaan | Jawaban (origin pengembangan; test 2024+ tidak dibuka) |
|---|---|
| Ada kandidat yang lebih baik dari C1-tuned secara berarti? | **Tidak.** 27 kandidat baru (2 preprocessing latih, 8 keluarga fitur, 7 hapus-satu, 1 gabungan bersarang, 4 klasifikasi, 5 model) → 0 lolos aturan §5 PROTOKOL. Terbaik: rerata 5 seed +0,000 / +0,002 (interval memuat 0). Konfigurasi terpilih **tetap C1-tuned**; test tidak dibuka. |
| Preprocessing bermasalah? | **Tidak ditemukan galat** yang mengubah label/fitur (D-147 + B01–B07 baru). Revisi harga PIHPS tidak dapat diuji (BLOCKED, U110). Jendela latih pendek & bobot waktu memperburuk (−0,016 / −0,022; −0,004 / −0,009). |
| Asal galat perubahan kecil (0,57 vs 0,78–0,80 saat bergerak material) | **Informasi**, bukan threshold atau model: AUC kuintil terkecil 0,60 / 0,56 (kuintil terbesar 0,77 / 0,82); label Q1 yang stabil pun 0,58–0,59; ± ⅓ Q1 adalah label rapuh/sub-tick. Threshold global oracle hindsight hanya +0,000 / +0,006. |
| Fitur baru (40 kolom, 8 keluarga) | Semua lolos uji kebocoran (0 sel); tidak ada yang lolos layar DU; ablation Δ −0,006..+0,003; gabungan dipilih di dev-awal: dev-akhir +0,002 / −0,012. Hapus-satu: `comm` (−0,020 / −0,014), `dev`, `rmean`, `season` penting; `lag` & `mom` ≈ 0. |
| Threshold, bobot kelas, kalibrasi | Threshold walk-forward global −0,005 / −0,003 (menukar F1 turun dengan F1 naik); per komoditas −0,002 / **−0,020**; bobot kelas +0,001 / −0,006. Kalibrasi monoton + 0,5 = threshold. |
| Model lain (fitur sama) | LightGBM −0,003 / −0,002, XGBoost −0,005 / −0,013, CatBoost −0,007 / −0,009, ExtraTrees −0,008 / −0,022, regresi logistik −0,031 / −0,057. HGB C1-tuned tetap terbaik. |
| Bottleneck yang tersisa | (1) arah perubahan kecil hampir tak teramalkan dari histori harga (± ⅓ di antaranya derau tick/komposisi hari); (2) pergeseran base rate per origin (hari libur, rezim kebijakan) yang baru diketahui sesudah target terealisasi (oracle per origin +0,035 / +0,024, tidak dapat direalisasikan walk-forward). |

**Rekomendasi eksplisit:** tidak ada model baru yang secara berarti mengungguli C1-tuned. Pertahankan C1-tuned (threshold 0,5) sebagai klasifier
arah eksploratif. Jangan menambah tuning/fitur dari histori harga yang sama; tuas yang masih masuk akal adalah informasi baru yang
mendahului harga (pasokan mingguan, pengumuman kebijakan bertanggal) dan validasi kebutuhan TPID (U109) agar ukuran keberhasilan
tidak hanya macro F1.

## 1. Protokol & pemenuhan batasan

| Batasan master task | Pemenuhan |
|---|---|
| 1–3. Label resmi, semua perubahan bukan nol, target tidak didefinisikan ulang | Label = tanda log p_{t+h} − log p_t; y = 0 dikeluarkan (definisi resmi D-139/D-141); tidak ada varian yang mengubah baris atau label evaluasi |
| 4. Observasi sulit tidak dibuang | Penyaring hanya pada baris LATIH bila dideklarasikan (B_win156); baris evaluasi identik untuk semua varian (diperiksa: `n` sama) |
| 5–6. Seleksi hanya origin ≤ 2023; test 2024+ tertutup | Semua fit & seleksi pada 38 / 37 origin dev; prediksi resmi dibaca lewat `official_c1t("dev")` yang menolak `part="test"`; test dibuka hanya lewat aturan PROTOKOL §6 |
| 7. C1-tuned pembanding wajib | Varian `base` setiap pekerjaan = `direction_tuned_preds` C1t persis (25.259 baris dev termasuk y = 0, maks \|Δp\| 0,0) |
| 8. IW_NAT bukan baseline baru | Tidak dijalankan ulang; dicatat di registri dengan status D-151/D-152 |
| 9. Leakage-safe di setiap origin | Fitur baru: perturbasi & penghapusan data sesudah origin, 12 origin 2021–2026 × 40 kolom → 0 sel berbeda; latih t + h ≤ origin; threshold walk-forward hanya label terealisasi; C_COMBO dipilih di dev-awal, dinilai di dev-akhir |
| 10. Reproduksi | Seed 20261121; versi paket di PROTOKOL §7; skrip ber-hash; checkpoint per (horizon, origin) |

Pengecualian yang diungkap: (a) satu pekerjaan uji asap (h 8, origin 2023-10-09) dijalankan sebelum protokol dibekukan (dilihat hanya
waktu & kecocokan `base`); (b) layar Data Understanding (EKSPERIMEN §3) tidak meloloskan satu pun fitur baru, tetapi ablation keluarga tetap
dijalankan karena diminta eksplisit dan untuk menguji apakah gerbang DU memprediksi hasil Modeling (§4.3); (c) `e_eval.py` dan
`r_registry.py` ditulis sesudah pembekuan, sebagai implementasi aturan §4–§5 yang sudah tertulis.

## 2. Fase A — Analisis galat C1-tuned (origin pengembangan)

`scripts/a_errors.py` → `hasil/a_*.csv`. Sumber: artefak resmi `direction_tuned_preds` (C1t, threshold 0,5), 10.966 / 11.307 baris
y ≠ 0 (h 4 / h 8), 38 / 37 origin. Test tidak dibaca (diagnosis test sudah ada di D-146/D-147).

### 2.1 Keseluruhan & per kelas

| h | macro F1 (interval) | F1 naik (interval) | F1 turun (interval) | P / R naik | P / R turun | MCC | AUC | naik aktual / prediksi |
|---|---|---|---|---|---|---|---|---|
| 4 | 0,656 (0,627..0,684) | 0,668 (0,614..0,713) | 0,644 (0,588..0,692) | 0,681 / 0,655 | 0,631 / 0,658 | 0,313 | 0,710 | 0,527 / 0,507 |
| 8 | 0,676 (0,641..0,706) | 0,702 (0,626..0,760) | 0,650 (0,579..0,712) | 0,704 / 0,699 | 0,647 / 0,653 | 0,352 | 0,724 | 0,542 / 0,538 |

Confusion (TP / FN / FP / TN): h 4 3.784 / 1.997 / 1.771 / 3.414; h 8 4.283 / 1.843 / 1.797 / 3.384. Di dev, galat kedua arah seimbang
(drift naik baru muncul di test 2024+, D-147).

### 2.2 Per origin, komoditas, provinsi

- **Per origin** (`a_per_origin.csv`): rerata macro F1 0,614 / 0,622, sd 0,092 / 0,084, rentang 0,42–0,79 / 0,48–0,80; 42% / 41% origin
  < 0,6. Per tahun: 2021 0,596 / 0,619, 2022 0,607 / 0,593, 2023 0,643 / 0,659. Origin terburuk didominasi **bias base rate satu origin**:
  2022-05-23 (h 4: naik aktual 0,60, prediksi 0,11), 2021-12-06 (0,82 vs 0,68), 2022-11-07 h 8 (0,82 vs 0,99), 2022-04-25 h 8 (0,55 vs 0,30).
- **Per komoditas** (`a_per_commodity.csv`): 0,590 (cabai merah h 4) .. 0,739 (telur h 8). Bias porsi naik terbesar: telur h 4 −0,09 /
  h 8 −0,11; gula h 8 +0,11; beras −0,09 / −0,14.
- **Per provinsi** (`a_per_province.csv`): 0,589..0,718 (h 4), 0,641..0,734 (h 8); sd antarprovinsi 0,030 / 0,018 — jauh lebih kecil
  dari sd antarorigin → galat ditentukan **waktu**, bukan lokasi.

### 2.3 Besar perubahan, volatilitas, kualitas data

| Kuintil \|y\| (dev) | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| median \|y\| h 4 / h 8 | 0,45% / 0,65% | 1,6% / 2,3% | 3,9% / 5,3% | 8,5% / 11,5% | 24% / 33% |
| macro F1 h 4 | 0,573 | 0,636 | 0,666 | 0,704 | 0,697 |
| macro F1 h 8 | 0,553 | 0,643 | 0,676 | 0,755 | 0,747 |
| ROC-AUC h 4 / h 8 | 0,602 / 0,561 | 0,669 / 0,663 | 0,722 / 0,720 | 0,766 / 0,804 | 0,771 / 0,823 |

Pada baris yang bergerak material (|y| ≥ persentil 80 latih per komoditas, D-154 S3, **bersyarat pada hasil**) macro F1 dev 0,777 / 0,797.
Volatilitas ex-ante (sd Δp 13 minggu, `a_by_volatility.csv`): h 4 menurun 0,683 (V1 paling tenang) → 0,620 (V5); h 8 datar 0,65–0,68.
Kualitas data (`a_by_quality.csv`): ujung `carry_forward` vs `observed` sama (0,658 vs 0,652; 0,665 vs 0,679); umur carry-forward > 8 minggu
tidak lebih sulit (0,66–0,77, n kecil). **Minggu origin dengan 4 hari teramati** (21% baris): prediksi naik 0,38 / 0,34 vs aktual
0,47 / 0,50 — ditelusuri di §3 (B05): efek kalender origin, bukan komposisi hari.

### 2.4 FP vs FN, kalibrasi

`a_fp_fn.csv`: FP (turun → tertebak naik) dan FN berbagi profil yang sama: median |y| 2,5–4,2% (vs 3,9–6,9% pada yang benar), keyakinan
|p − 0,5| 0,15–0,18 (vs 0,19–0,23), label rapuh (flip ≥ 5%) 10–16% (vs 5–11%). Komoditas diatur 26–35% dari galat. Kalibrasi
(`a_calibration.csv`): h 4 baik di tengah (p 0,3–0,8: selisih ≤ 0,06); h 8 kurang yakin di sekitar 0,5 (p 0,45 / 0,55 → aktual 0,52 /
0,65, sesuai oracle threshold 0,46); keduanya terlalu yakin di ekor (p > 0,9: aktual 0,76–0,78; p < 0,1: 0,21–0,31).

### 2.5 Dari mana galat berasal (dekomposisi, `a_decomposition.csv`)

| Sumber | Ukuran (h 4 / h 8) | Bacaan |
|---|---|---|
| **Threshold global** | oracle hindsight terbaik 0,656 / 0,682 (thr 0,50 / 0,46) → +0,000 / +0,006 | batas atas keuntungan threshold tunggal ≈ 0 |
| Threshold per komoditas | oracle +0,011 / +0,009 | kecil, dan itu batas atas hindsight |
| **Bias base rate per origin** | oracle threshold per origin +0,035 / +0,024; per origin × komoditas +0,12 / +0,11 (overfit, ± 30 baris/sel) | bagian terbesar galat yang "bisa dikoreksi" adalah pergeseran porsi naik per origin, yang hanya diketahui sesudahnya |
| **Label rapuh** (D-147) | label stabil & ≥ 2 tick (84% / 89% baris): 0,676 / 0,696 → +0,020 / +0,020 | batas atas bila semua label rapuh dianggap derau |
| **Informasi pada perubahan kecil** | AUC Q1 0,60 / 0,56 vs Q5 0,77 / 0,82; Q1: 30% / 21% < 1 tick, 35% / 27% label rapuh, 67% / 71% komoditas diatur; F1 pada label Q1 yang **stabil** pun hanya 0,587 / 0,578 | perubahan kecil sulit karena skor peringkat lemah, bukan karena threshold; sebagian (± ⅓) derau pembentukan label |
| Peringkat dalam origin × komoditas | AUC rerata 0,670 / 0,694 vs pooled 0,710 / 0,724 | sebagian AUC pooled berasal dari membedakan komoditas/origin, bukan seri dalam satu komoditas |

**Kesimpulan Fase A.** Galat dominan berasal dari (1) **informasi yang tidak cukup** untuk membedakan arah perubahan kecil (AUC ≈ 0,56–0,60
pada kuintil terkecil, termasuk label yang stabil), dan (2) **pergeseran base rate per origin** (origin hari libur & periode kebijakan) yang
tidak dapat diketahui sebelum target terealisasi. Threshold global dan perilaku kalibrasi bukan sumber utama (oracle ≤ +0,006).
Preprocessing tidak terbukti menjadi sumber (§3). Kontribusi pilihan model diuji di §6.

## 3. Fase B — Audit preprocessing

Peta pipeline lengkap & audit P01–P10 ada di [D-147](20261125_task4_audit_preprocessing.md) §1–§5 (tidak diulang). Di sini: item yang
diminta master task, bukti baru (`scripts/b_audit.py` → `hasil/b_summary.json`, `b03_*.csv`, `b05_origin_days.csv`), dan ablation latih
baru (`B_*`, run §4).

| Item | Bukti | Akar | Dampak pada data latih | Koreksi | Kebocoran | Ablation (dev Δ macro F1 h 4 / h 8) |
|---|---|---|---|---|---|---|
| Duplikat & grid | 0 kunci ganda; grid 340 seri × 516 minggu lengkap (B01) | – | – | tidak perlu | – | – |
| Seri tidak layak | 3 seri cabai rawit (Aceh, Sumbar, Kepri) tidak pernah masuk baris evaluasi dev (B02) | lag/target kosong | ikut latih bila baris lengkap | tidak perlu | – | – |
| Nilai hilang | `missing` (1%) = NaN, tidak diisi di panel; target & lag dari harga teramati; ffill ≤ 8 minggu hanya di fitur turunan (D-147) | desain | baris tanpa target/lag dibuang: 118 / 115 target & 120 / 117 lag dari 12.920 / 12.580 slot origin dev (≤ 1%) | – | – | P03b tanpa ffill −0,003 / −0,001 (D-147) |
| Carry-forward | status saja; ujung cf akurasi sama dengan observed (§2.3) | kekakuan harga nyata (U22) | 51–59% label punya ≥ 1 ujung cf | tidak dibuang | – | P03a latih ujung observed saja **−0,017 / −0,022** (D-147) |
| Nol sejati vs hilang | y = 0: 98,6% / 98,4% ujung cf→cf (harga identik), 0,5% observed→observed; hilang selalu NaN, tidak pernah 0 (B03) | – | y = 0 dikeluarkan dari latih & metrik (definisi resmi; cakupan 0,855 / 0,907) | – | – | 3 kelas D-146 (target lain) |
| Revisi harga & ketersediaan | vintage PIHPS tidak tersedia (U110) | – | tidak dapat diukur | `available_at` konservatif Minggu 00.00 | revisi tidak teruji | **BLOCKED** |
| Outlier | 46 lonjakan QA, 460 kandidat galat; ≤ 1,4% label tersentuh, akurasi sama (D-147 P05) | – | kecil | flag saja | – | tidak dijalankan (dampak ≤ 1,4%) |
| Penyelarasan waktu | y_h & lag_dp_1/4/8 dihitung ulang dari log_p: selisih maks 0,0, pola NaN sama; semua `week` Senin (B04) | – | – | – | – | – |
| Log vs persen | semua fitur & target selisih log (D-147 P07) | – | – | – | – | – |
| Batas jendela rolling & urutan fitur | rolling ke belakang tanpa `center`; 6 kolom resmi dihitung ulang identik; perturbasi masa depan 0 sel (D-147 P10 + §4.2) | – | – | – | 0 sel | – |
| Konsistensi komoditas/provinsi | 10 komoditas = config, 34 provinsi, wilayah unik per provinsi, 0 kosong (B06) | – | – | – | – | – |
| **Minggu origin pendek (hari libur)** | 9 / 9 origin dev dengan > 50% seri 4 hari: bias porsi naik −0,096 / −0,164 vs +0,004 / +0,048 origin normal; **di dalam origin campuran bias baris 4 hari hampir sama dengan baris 5 hari** (h 4 −0,12 vs −0,12; h 8 −0,17 vs −0,11); hari hilang tersebar Sen–Jum (B05, B07) | efek kalender/rezim pada origin (sekitar Idulfitri, 17 Agustus, Imlek, Iduladha), **bukan** artefak komposisi hari | 45 minggu 4 hari di 2017–2023 | fitur cakupan & kalender diuji (C_D2, C_F) | – | lihat §4.4 |
| Jendela latih | latih ekspansif 2017-01.. origin | non-stasioneritas (drift rezim) | – | B_win156 (156 minggu terakhir; baris latih rerata 43.331 vs 62.573) | – | **−0,016 (−0,027..−0,007) / −0,022 (−0,036..−0,010)**, q 0,032 / 0,003 → lebih buruk |
| Bobot waktu | semua baris latih berbobot sama | non-stasioneritas | – | B_recency (paruh 104 minggu); Optuna D-145 sudah memilih tanpa peluruhan | – | −0,004 (−0,013..0,005) / **−0,009 (−0,017..−0,001)** → tidak membantu |

**Kesimpulan Fase B.** Tidak ada galat preprocessing yang mengubah label atau fitur. Satu-satunya pola sistematis baru (bias origin
hari libur) adalah efek kalender pada tingkat origin; komposisi hari di dalam minggu tidak menjelaskannya.

## 4. Fase C — Rekayasa fitur

### 4.1 Spesifikasi (`scripts/c_feats.py`; p = log harga mingguan ffill ≤ 8 minggu, Δ = selisih log, semua jendela ke belakang)

| Keluarga | Kolom | Definisi (nilai pada minggu t) | Sudah ada di C1t? |
|---|---|---|---|
| A momentum | dp_2, dp_12, accel_8, rev_1_4, up_share_26, dn_share_26 | p_t − p_{t−2}; p_t − p_{t−12}; (p_t − p_{t−8}) − (p_{t−8} − p_{t−16}); sign(Δp_t)·sign(p_{t−1} − p_{t−5}); porsi minggu naik/turun 26 | lag 1–3/4/8/13/26/52, accel_4, up/dn_share_13, run_sign |
| B volatilitas | std_dp_52, absmean_dp_13, maxabs_dp_13, vol_ratio_4_26, dir_bal_26, chg_freq_26 | sd Δp 52; rerata & maks \|Δp\| 13; sd4/sd26; up_share_26 − dn_share_26; porsi minggu Δp ≠ 0 (26) | std 4/13/26 |
| C posisi harga | z_52, dev_med_26, pct_104, dist_max_52, dist_min_52 | (p − rerata52)/sd52; p − median 26; persentil p dalam 104 minggu; p − maks52; p − min52 | dev_ma13/52, range_pos_52 |
| D1 kualitas panel | cf_age, zero_share_13, status_cf_run, n_missing_13, st0_cf | minggu sejak Δp ≠ 0; porsi Δp = 0 (13); run status carry_forward; jumlah minggu hilang (13); status t = carry_forward | – (cf dibuang D-145) |
| D2 cakupan harian | n_days, n_days_l1 | hari teramati minggu t, t − 1 (`pihps_daily`) | – |
| E lintas provinsi | rel_dp_1, rel_dp_4, loo_dev, rank_dp_4, rank_dev | Δp provinsi − rerata nasional **tanpa provinsi itu** (1, 4); p − rerata LOO; persentil Δp_4 & deviasi spasial di antara provinsi komoditas sama | spatial_dev (termasuk diri), nat_dp |
| F kalender | wk_idadha, wk_natal, wk_ramadan, seas_nat_exp_h, seas_ser_exp_h | minggu relatif Iduladha/Natal/awal Ramadan (±13, tanggal resmi diketahui sebelumnya); rerata Δp_h nasional / seri yang **dimulai** pada minggu-ISO ±1 di tahun-tahun sebelumnya (t' + h ≤ t, t' < t − 26) | bulan, idf_rel_week, woy sin/cos, yseas 52/104 |
| G interaksi | z_dev13, z_dp4, z_spatial, mom_x_vol | dev_ma13/sd13; Δp_4/sd26; deviasi spasial / sd lintas provinsi; EWM Δp (paruh 4)/sd13 | – |

Kontrol: 7 kolom resmi yang dihitung ulang oleh pembangun (`std_dp_52`, `absmean_dp_13`, `maxabs_dp_13`, `cf_age`, `zero_share_13`,
`status_cf_run`, `n_days`) identik dengan tabel resmi → konvensi sama. Kosong 11–21% (pemanasan 2017), kalender 48% (di luar ±13).

### 4.2 Kebocoran (`scripts/c_leak.py` → `hasil/c_leak.csv`)
12 origin (2021-01-04 .. 2026-10-05) × 40 kolom: (T1) log_p, status, n_days sesudah origin dirusak acak; (T2) baris sesudah origin
dihapus → **0 sel berbeda** pada minggu ≤ origin di kedua uji.

### 4.3 Layar Data Understanding (`scripts/c_du.py` → `hasil/c_du.csv`) & konkordansi dengan Modeling

Kontrol: `iw_gap` ρ 0,132 / 0,099 (q ≈ 0); derau −0,018 / 0,003; `dev_ma13` (dipakai C1t) −0,006 / 0,015 → kontrol negatif ≈ 0.
Tidak ada fitur baru yang lolos (q < 0,05 di kedua horizon dan |ρ| ≥ ½ kontrol positif). Terkuat hanya di h 8: `wk_idadha` −0,125
(q 0,043), `z_52` 0,116, `dn_share_26` −0,111 / `dir_bal_26` 0,111 (q 0,043), `dist_max_52` 0,085 (q 0,019). Konkordansi
(`hasil/e_du_concordance.csv`): 8 keluarga gagal DU, 8 keluarga gagal Modeling (|Δ| ≤ 0,006) → **gerbang DU tidak menghasilkan negatif
palsu** di sesi ini; korelasi residual pooled sebesar 0,10–0,12 tanpa konsistensi dua horizon tidak cukup untuk keuntungan macro F1.

### 4.4 Ablation keluarga (tambah-satu di atas C1t; `hasil/e_metrics.csv`)

| ID | Δ h 4 (interval) | Δ h 8 (interval) | Δ F1 naik / turun h 8 | Δ kuintil kecil h 4 / h 8 | origin Δ>0 h 4 / h 8 | Gagal aturan |
|---|---|---|---|---|---|---|
| C_A momentum | −0,001 (−0,006..0,005) | −0,003 (−0,008..0,001) | −0,004 / −0,002 | −0,003 / +0,006 | 0,45 / 0,38 | 1, 2, 3 |
| C_B volatilitas | +0,001 (−0,009..0,010) | −0,001 (−0,006..0,004) | −0,003 / +0,001 | +0,004 / **+0,013 (0,004..)** | 0,50 / 0,49 | 1, 2, 3 |
| C_C posisi | −0,006 (−0,014..0,001) | +0,003 (−0,004..0,009) | −0,004 / +0,009 | −0,001 / +0,007 | 0,39 / 0,57 | 1, 2, 3 |
| C_D1 kualitas | −0,002 (−0,008..0,005) | +0,001 (−0,006..0,006) | −0,001 / +0,002 | +0,001 / +0,004 | 0,39 / 0,54 | 1, 2, 3 |
| C_D2 cakupan hari | −0,000 (−0,008..0,008) | −0,002 (−0,009..0,004) | −0,003 / −0,002 | +0,006 / +0,000 | 0,42 / 0,51 | 1, 2, 3 |
| C_E lintas provinsi | +0,001 (−0,004..0,007) | −0,004 (−0,009..−0,001) | −0,006 / −0,003 | +0,004 / −0,000 | 0,53 / 0,43 | 1, 2, 3 |
| C_F kalender | +0,001 (−0,009..0,008) | −0,002 (−0,012..0,007) | −0,003 / −0,000 | +0,007 / +0,012 | 0,39 / 0,49 | 1, 2, 3 |
| C_G interaksi | +0,001 (−0,004..0,008) | −0,003 (−0,010..0,003) | −0,005 / −0,001 | −0,005 / +0,004 | 0,53 / 0,49 | 1, 2, 3 |
| C_COMBO (B, C, D1, D2, F, G dipilih di dev-awal; dinilai dev-akhir, 18 / 17 origin) | +0,002 (−0,011..0,011) | −0,012 (−0,033..0,002) | −0,022 / −0,003 | +0,002 / +0,000 | 0,44 / 0,59 | 1, 2, 3, 4 |

Seleksi gabungan di dev-awal (`hasil/e_combo_selection.json`): keluarga dengan Δ rerata > 0 sebelum 2022-07 tidak bertahan sesudahnya
(dengan seluruh dev, yang bias seleksi: +0,005 / −0,003). Satu sinyal sub-kelompok: volatilitas (C_B) menaikkan kuintil |y| terkecil h 8
+0,013 (0,004..0,021) tetapi tidak keseluruhan. Hanya 2 dari 54 sel kuintil-kecil yang intervalnya > 0 (C_B h 8 dan D_seed5 h 8
+0,006, 0,001..0,012), tanpa koreksi multiplisitas → tidak diadopsi.

### 4.5 Seleksi fitur (hapus-satu kelompok C1t)

| Dihapus | Δ h 4 (interval) | Δ h 8 (interval) | Bacaan |
|---|---|---|---|
| comm (sinyal nasional) | **−0,020 (−0,034..−0,008)** q 0,032 | **−0,014 (−0,026..−0,001)** | paling penting |
| dev (deviasi MA/spasial) | −0,004 (−0,012..0,004) | **−0,008 (−0,012..−0,003)** q 0,003 | penting h 8 |
| rmean (EWM) | −0,006 (−0,011..0,000) | −0,006 (−0,014..−0,000) | berguna |
| season | −0,008 (−0,021..0,004) | −0,004 (−0,016..0,008) | berguna, tidak pasti |
| rstd | −0,003 (−0,010..0,006) | −0,005 (−0,012..0,003) | kecil |
| lag (lag panjang) | +0,002 (−0,005..0,009) | −0,001 (−0,008..0,011) | ≈ 0 |
| mom | −0,001 (−0,008..0,006) | +0,001 (−0,006..0,005) | ≈ 0 |

Tidak ada kelompok yang bila dibuang menaikkan skor secara berarti → set fitur C1t tidak diubah (menyederhanakan `lag`/`mom` tidak
memberi keuntungan, hanya mengubah artefak resmi).

## 5. Fase D — Optimasi klasifikasi

| ID | Δ h 4 (interval) | Δ h 8 (interval) | Catatan |
|---|---|---|---|
| D_thr_wf (threshold global walk-forward; rerata 0,488 / 0,455) | −0,005 (−0,012..0,000) | −0,003 (−0,015..0,008) | menaikkan prediksi naik (0,52 / 0,59); F1 turun −0,011 / **−0,022** → gagal aturan 4 |
| D_thr_wf_comm (per komoditas) | −0,002 (−0,010..0,006) | **−0,020 (−0,034..−0,008)** q 0,003 | overfit base rate komoditas |
| D_cw (bobot kelas seimbang) | +0,001 (−0,006..0,008) | −0,006 (−0,016..0,002) | kelas sudah hampir seimbang (0,53 / 0,54 naik) |
| D_seed5 (rerata 5 seed) | −0,000 (−0,004..0,005) | +0,002 (−0,002..0,005) | pengurangan varians kecil; kuintil kecil h 8 +0,006 (0,001..) |
| B_recency, B_win156 | §3 | §3 | lebih buruk |
| Kalibrasi Platt/isotonik | – | – | monoton + 0,5 = memilih threshold → dicakup D_thr_wf; kalibrasi temporal D-148 sudah ditolak |
| Hyperparameter | – | – | Optuna 40 trial D-145 (ruang termasuk bobot kelas & peluruhan); tidak diulang (larangan pencarian tanpa arah) |
| Fitur interaksi | C_G §4.4 | | ≈ 0 |

Threshold walk-forward memilih nilai dari origin terdahulu; karena porsi naik berubah antarorigin (§2.5), threshold masa lalu tidak
memperbaiki origin berikutnya. Ini konsisten dengan oracle: keuntungan threshold hanya ada bila diketahui sesudahnya.

## 6. Fase E — Perbandingan model (fitur & baris C1t, konfigurasi tetap)

| Model | macro F1 h 4 / h 8 | Δ h 4 (interval) | Δ h 8 (interval) | AUC h 4 / h 8 | Waktu/fit (dtk, 2 thread) |
|---|---|---|---|---|---|
| **HGB C1-tuned** | **0,656 / 0,676** | – | – | 0,710 / 0,724 | 13 |
| LightGBM (dipetakan) | 0,653 / 0,674 | −0,003 (−0,012..0,006) | −0,002 (−0,009..0,007) | 0,710 / 0,725 | 5 |
| XGBoost (dipetakan) | 0,651 / 0,664 | −0,005 (−0,013..0,002) | −0,013 (−0,027..−0,002) | 0,706 / 0,723 | 8 |
| CatBoost | 0,649 / 0,667 | −0,007 (−0,019..0,003) | −0,009 (−0,018..−0,001) | 0,707 / 0,723 | 98 |
| ExtraTrees | 0,648 / 0,654 | −0,008 (−0,029..0,013) | −0,022 (−0,054..0,001) | 0,700 / 0,709 | 49 |
| Regresi logistik (diagnostik) | 0,625 / 0,619 | **−0,031 (−0,051..−0,009)** | **−0,057 (−0,085..−0,033)** | 0,669 / 0,672 | 2 |

Bacaan: boosting pohon apa pun berada dalam ± 0,01 dari HGB (AUC hampir sama) → batas skor bukan pilihan algoritma; hubungan non-linear
penting (regresi logistik −0,03..−0,06). D-146 (LightGBM/XGBoost default, ensemble, spesialis) dan D-145/D-146 (TSMixer, PatchTST,
TimesFM-head, TCN/MLP) memberi kesimpulan sama. Tidak ada model yang dilanjutkan ke tuning (aturan master task: hanya yang menunjukkan
perbaikan berarti).

## 7. Registri eksperimen

[`docs/eksperimen_registry.csv`](../eksperimen_registry.csv) (117 baris, D-145 … D-156; dibangun `scripts/r_registry.py`): COMPLETE 24
(acuan, diagnostik, atau hasil dicatat termasuk dua pembukaan test yang belum terbukti), PARTIAL 3 (C2-tuned 12/25 trial, TSMixer-tuned
10 trial, TimesFM-head grid dipangkas), FAILED 1 (TCN Colab percobaan 1: GPU penuh), BLOCKED 2 (agregasi per pasar; vintage revisi
PIHPS), REJECTED 87 (termasuk 27/27 kandidat D-156). Setiap baris: hipotesis, versi data, konfigurasi fitur/preprocessing/model/
hyperparameter/threshold, origin, macro F1, Δ vs pembanding + interval, status, skrip, keputusan & alasan. Aturan pemeliharaan:
`docs/EKSPERIMEN.md` §6.

## 8. Konfigurasi terpilih (pengembangan) & test

**C1-tuned tidak berubah**: kolom `tuned_columns("C1t", h)`, `TUNED_HGB`, seed 20261121, threshold 0,5, preprocessing beku (D-148). Tidak
ada kandidat yang memenuhi §5 PROTOKOL (`hasil/e_decision.csv`: 0 / 27), jadi **test 2024+ tidak dibuka** dan kriteria bisnis S1–S3 tidak
dihitung ulang. Angka test yang berlaku tetap 0,677 / 0,680 (D-145).

## 9. Kebocoran & reproduksi

| Kontrol | Hasil |
|---|---|
| Split | `split_origin` resmi: latih t + h ≤ origin, uji t = origin; baris uji identik untuk semua varian (n sama per horizon) |
| Pembanding | `base` = artefak resmi C1t, 25.259 baris dev, maks \|Δp\| 0,0 (`e_eval.py`, assert) |
| Fitur baru | 0 sel berbeda pada perturbasi & penghapusan masa depan, 12 origin × 40 kolom |
| Threshold | walk-forward: hanya prediksi origin o' dengan o' + h ≤ o (label terealisasi) |
| Seleksi gabungan | dipilih di origin < 2022-07-01, dinilai di origin ≥ 2022-07-01 |
| Test | tidak dibaca (`official_c1t("test")` sengaja gagal) |
| Revisi data | tidak teruji (vintage PIHPS tidak ada; U110) |
| Reproduksi | `PROTOKOL.md` + `hasil/protocol_sha256.txt` (hash skrip saat beku); seed 20261121; versi paket PROTOKOL §7; urutan: `c_feats.py` → `c_leak.py` → `c_du.py` → `m_run.py` (STAGE=main) → `e_eval.py` (SELECT_COMBO=1) → `m_run.py` (STAGE=combo, COMBO_FAMS=B,C,D1,D2,F,G) → `e_eval.py` → `r_registry.py`; tabel kerja di `KAGAMI_EXP` (dibangun ulang dari `20261125_task4_audit_preprocessing/scripts/prep.py`). Runtime: 89 menit main (6 proses × 2 thread, 75 pekerjaan) + 5 menit combo |

## 10. Kesimpulan & bottleneck

1. **C1-tuned tidak dapat diungguli secara berarti** dengan preprocessing, fitur, threshold, bobot, atau algoritma lain dari informasi yang
   sama. Semua putaran sesudah D-145 (D-146–D-151, D-156) berhenti di ≈ 0,66 / 0,68 dev; semua perbedaan baru dalam ± 0,006 kecuali yang
   memperburuk.
2. **Bottleneck 1 — informasi pada perubahan kecil.** Kuintil |y| terkecil (median 0,45% / 0,65%) punya AUC 0,60 / 0,56; ± ⅓ di antaranya
   label rapuh/sub-tick (batas atas pembersihan +0,02). Sisa celah adalah ketidakpastian intrinsik arah perubahan kecil dari histori harga.
3. **Bottleneck 2 — pergeseran base rate per origin** (origin hari libur −0,10 / −0,16; rezim kebijakan komoditas diatur). Hanya terlihat
   sesudah target terealisasi; threshold/kalibrasi walk-forward tidak menangkapnya (D-148, D_thr_wf). Informasi yang dibutuhkan bersifat
   **ex-ante** (pengumuman kebijakan bertanggal, pasokan mingguan), bukan pengolahan ulang histori harga.
4. **Bukan bottleneck**: preprocessing (tidak ada galat), threshold global (oracle ≤ +0,006), pilihan algoritma (boosting setara), seri
   tidak layak, keseimbangan kelas.
5. Klaim tetap: hasil eksploratif, pseudo-real-time, bukan uji praregistrasi (H5 tetap dari `forecast_eval`).
