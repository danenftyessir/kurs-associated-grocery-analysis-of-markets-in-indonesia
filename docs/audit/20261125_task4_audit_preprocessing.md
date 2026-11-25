# Audit Preprocessing Task 4 — Klasifikasi Arah (EKSPLORATIF)

Tanggal: 2026-11-25 · Pelaksana: Danen (dengan agent) · Keputusan: D-147 · Lanjutan dari [ronde 1](20261124_task4_optimasi_arah.md)
(D-145) dan [ronde 2](20261125_task4_ronde2.md) (D-146). Catatan bertanggal (bukan dokumen hidup). Skrip & hasil:
[folder lampiran](20261125_task4_audit_preprocessing/) (`scripts/`, `hasil/`).

Pertanyaan audit: apakah preprocessing (mentah → pembersihan → agregasi → resampling → missing → fitur → label → dataset → latih)
menghasilkan representasi yang cukup konsisten untuk membedakan perubahan harga nyata dari derau pengukuran, agregasi, atau
pembentukan data, terutama pada perubahan kecil (kuintil |y| terkecil macro F1 0,57 di ronde 2)?

Evaluator tetap: **C1-tuned** (fitur `tuned_columns("C1t", h)`, `TUNED_HGB`, seed resmi). Label evaluasi = label resmi; tidak ada
varian yang mengubah baris atau label evaluasi. Seleksi hanya di origin pengembangan (origin + h ≤ 2023-12-31); test (origin ≥ 2024)
hanya dipakai untuk diagnosis deskriptif (§2–§4), tidak untuk memilih.

## 0. Ringkasan

| Pertanyaan | Jawaban |
|---|---|
| Ada kesalahan preprocessing yang mengubah label atau fitur? | **Tidak ditemukan.** 0 duplikat, 0 harga non-bulat; target memakai harga TERAMATI (tanpa ffill/interpolasi); uji kebocoran menyeluruh (76 origin × 54 kolom × perturbasi & penghapusan masa depan) 0 sel berbeda. |
| Temuan kecil | (1) flag `episode` (grup fx; dipakai M2/C2, **tidak** dipakai C1-tuned) memakai informasi sesudah origin pada 1/76 origin (2024-12-02) karena episode berdempetan digabung; (2) `range_pos_52` mengisi 0,5 saat jendela belum penuh atau harga hilang (kosong dikodekan sebagai angka). |
| Apakah perubahan kecil = derau pembentukan data? | **Sebagian kecil.** Semua harga harian PIHPS kelipatan **Rp50**; 1 tick = 0,32% beras, 0,28% gula, 0,23% minyak goreng. Label < 1 tick (hanya mungkin dari komposisi hari dalam minggu) 2,4–4,3% baris, akurasi 0,51–0,54; label yang berbalik bila hari di-resample 8–12%, akurasi 0,50–0,58. |
| Apakah itu batas skor? | **Tidak.** Pada label ≥ 10 tick (65–72% baris) akurasi C1-tuned hanya 0,68–0,71; pada label stabil 0,69–0,70. Membuang semua label rapuh menaikkan skor ≈ +0,01–0,015 saja. Celah ke 0,8 bukan artefak data. |
| Asal drift naik | **Pergeseran rezim komoditas diatur**, bukan ketidakseimbangan sampel: prediksi naik berlebih di test beras +0,11/+0,17, minyak goreng +0,15/+0,14, daging sapi +0,15/+0,09 (dev beras justru −0,09/−0,14). |
| Skor gabungan vs seimbang-seri | Gabungan 0,677/0,680 vs rerata antarseri 0,657/0,651; 12–16% seri test < 0,55. |
| Eksperimen preprocessing (dev, C1-tuned tetap) | Membersihkan label latih, tanpa ffill, fitur hari terakhir: ≈ 0. Latih hanya ujung `observed` −0,017 / −0,022, normalisasi per seri dan bobot komoditas lebih buruk di h 8. Hanya **informasi dalam-minggu** (`iw_gap`) yang membantu di dev (+0,014 h 4); di test +0,004 / +0,005, belum terbukti setelah BH. |
| Model terpilih | **Tidak berubah**: C1-tuned (test 0,677 / 0,680). |

## 1. Peta pipeline aktual (dan koreksi asumsi proposal)

| Tahap | Implementasi | Fakta yang diverifikasi | Implikasi |
|---|---|---|---|
| Raw | `data/loaders.load_pihps`: zip 34 CSV lebar, level 2 = varian | harga **provinsi** yang sudah diagregasi BI dari pasar di kota sampel (`n_kota` 1–12, 110 kota); data per pasar tidak ada di repo | P02 *fixed-market cohort* **tidak bisa** dibuat; komposisi pasar tidak teramati. Yang bisa diaudit: komposisi HARI dalam minggu |
| Cleaning | `weekly.select_variants`: varian representatif, buang NaN & harga ≤ 0 | 1.644.287 sel terisi; 0 kunci duplikat; 5 harga ≤ 0 (dibuang); 0 non-bulat; 100% kelipatan Rp50 | Presisi sumber = Rp50 |
| Agregasi & resampling | `weekly.aggregate_weekly`: rerata hari kerja teramati per minggu ISO (label Senin), grid lengkap, status D-021 | hanya Senin–Jumat (masing-masing ± 20%); n hari 5 = 86%, 4 = 10,5%; 60% minggu punya variasi harga di dalam minggu (beras 22%, cabai 94%) | Satu definisi kalender untuk semua sumber; tidak ada imputasi |
| Missing | sel `missing` (1%) = NaN, tidak pernah diisi di panel | target `y_h = log_price_{t+h} − log_price_t` dari panel TANPA isi; baris dengan target atau `lag_dp_1/4/8` kosong dibuang (`split_origin`) | p_t, p_{t−1}, p_{t−4}, p_{t−8}, p_{t+h} selalu teramati pada baris yang dipakai. `ffill(limit 8)` hanya di fitur turunan (`price_dynamics`) |
| carry_forward | status saja (`cf_share > 0,5`); bukan imputasi kita | 51–59% label punya ≥ 1 ujung carry_forward; akurasi cf→cf 0,67–0,70 ≈ observed→observed 0,64–0,68 | Tidak ada bukti ujung carry_forward merusak label (U22 tetap) |
| Label | biner naik/turun, y = 0 dikeluarkan | cakupan 0,855 / 0,907 | Target tidak diubah di audit ini |
| Fitur | `forecast.feature_table` + `price_dynamics.extend_table` | semua dalam selisih/rasio log (tidak ada level rupiah); per seri lewat pivot (satu kolom = satu seri); rolling ke belakang, tanpa `center`; rerata lintas provinsi minggu yang sama | P07 (rupiah vs persen vs log return) sudah terjawab: seluruhnya log |
| Per-fold | HGB tanpa scaler/imputer (NaN asli); binning & validasi early-stopping dihitung di dalam setiap `fit` dari baris latih origin itu; kode kategori dari config (tetap, tidak dipelajari) | — | P08 standardisasi global tidak relevan untuk C1-tuned; normalisasi per seri diuji (§5) |
| Ketersediaan | harga dunia as-of `available_at`; JISDOR/Brent minggu yang sama; flag `episode` dari `find_episodes` periode penuh | lihat §4 | — |

## 2. Presisi harga, agregasi hari, dan pembentukan label (P03, P04, P06)

`scripts/p01_integrity.py`, `scripts/p03_label.py` → `hasil/p01_integrity.json`, `hasil/p03_*.csv`.

**Tick Rp50.** Seluruh harga harian (10 komoditas) habis dibagi 50; hanya ± 50% yang habis dibagi 100. Ukuran tick relatif (test,
median harga awal): beras 0,32%, gula 0,28%, minyak goreng 0,23%, telur 0,17%, daging ayam 0,13%, bawang putih 0,12%, bawang merah
0,12%, cabai merah 0,10%, cabai rawit 0,08%, daging sapi 0,035%. Perubahan harian median: beras/gula Rp100 (2 tick), minyak goreng
Rp150. Karena label = selisih rerata mingguan, 43% harga mingguan tidak lagi kelipatan Rp50; perubahan **di bawah 1 tick** hanya
bisa muncul dari komposisi hari (mis. 4 hari Rp15.000 + 1 hari Rp15.050).

**Label rapuh** (C1-tuned, baris y ≠ 0):

| Kelompok \|Δ rerata mingguan\| | dev h 4: n · akurasi · F1 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| < 1 tick | 421 · 0,537 · 0,534 | 270 · 0,511 · 0,511 | 454 · 0,542 · 0,518 | 269 · 0,509 · 0,463 |
| 1–2 tick | 559 · 0,599 · 0,598 | 432 · 0,549 · 0,548 | 623 · 0,604 · 0,584 | 476 · 0,555 · 0,507 |
| 2–3 | 491 · 0,593 · 0,590 | 418 · 0,584 · 0,582 | 571 · 0,676 · 0,656 | 448 · 0,650 · 0,610 |
| 3–5 | 706 · 0,623 · 0,614 | 635 · 0,584 · 0,576 | 792 · 0,645 · 0,633 | 762 · 0,643 · 0,602 |
| 5–10 | 1.133 · 0,641 · 0,637 | 1.076 · 0,631 · 0,617 | 1.295 · 0,638 · 0,627 | 1.256 · 0,668 · 0,650 |
| ≥ 10 | 7.656 · 0,677 · 0,677 | 8.476 · 0,708 · 0,706 | 6.939 · 0,707 · 0,707 | 7.796 · 0,710 · 0,707 |

Label < 2 tick terkonsentrasi di komoditas diatur (test h 4): beras 38%, minyak goreng 29%, gula 26%, telur 8,5%; lainnya ≤ 5%.

**Kepekaan terhadap agregasi hari → minggu.** (a) Bootstrap hari teramati di dalam minggu t dan t + h (B = 200): label yang tandanya
berbalik ≥ 5% replikasi = 10,9% / 7,7% (dev h 4 / h 8), 12,2% / 8,4% (test); akurasi pada label itu 0,50–0,58 vs 0,67–0,70 pada
label stabil. (b) Representasi lain minggu: tanda label sama dengan versi **median** hari 98%, **hari terakhir** 94–96%, hari pertama
94–96%. (c) Pada kuintil |y| terkecil, label tidak stabil hanya 28–38%: kuintil itu bukan sebagian besar derau agregasi.

**Batas atas yang bisa dijelaskan oleh pembentukan data.** Macro F1 pada label stabil (flip < 5%): 0,670 / 0,691 (dev), 0,693 /
0,690 (test); pada label ≥ 2 tick: 0,664 / 0,685, 0,690 / 0,692. Bahkan bila semua label rapuh dianggap derau murni, skor hanya naik
± 0,01–0,015. Hipotesis "kesulitan perubahan kecil berasal dari derau pengukuran" **benar untuk label < 2 tick** (akurasi ≈ koin)
tetapi **bukan penjelasan utama celah ke 0,8**.

**Derau transien vs efek agregasi.** Autokorelasi lag-1 perubahan log mingguan per seri **positif** untuk 9/10 komoditas (0,15–0,42;
daging sapi −0,13). Derau pengukuran i.i.d. akan memberi nilai negatif; ± 0,24 adalah nilai mekanis dari merata-ratakan 5 hari
random walk (efek Working, (m² − 1)/(2(2m² + 1)) untuk m = 5). Artinya sebagian perubahan label sudah terjadi DI DALAM minggu origin:
tanda `log(harga hari terakhir) − log(rerata minggu t)` searah dengan label pada 62,6% (h 4) / 56,8% (h 8) baris yang nilainya ≠ 0,
lebih tinggi dari tanda perubahan minggu lalu (58,0% / 52,7%). Fitur resmi hanya dari rerata mingguan sehingga tidak melihat
informasi ini → diuji sebagai P04 (§5). Hanya daging sapi yang menunjukkan pola berbalik (konsisten dengan derau/pembulatan).
Estimasi σ derau dari intersep rasio varians (`hasil/p06_noise.csv`, kolom `noise_dominated_*` di `p05_p06_summary.json`) **tidak
dipakai**: intersepnya negatif untuk 5 komoditas dan untuk cabai/ayam/telur didorong siklus harga, bukan derau pengukuran.

## 3. Outlier (P05)

`scripts/p05_noise.py` → `hasil/p05_outliers.csv`, `hasil/p05_p06_summary.json`. Tidak ada data yang dihapus atau di-clip.

- Lonjakan satu hari QA (|Δlog| > 0,5 berbalik, `qa.flag_price_outliers`): 46 hari dalam periode; ikut rerata mingguan.
- Perubahan mingguan |Δlog| > 5 × MAD seri: 4.368 sel (2,8%) → 1.646 terkonfirmasi lintas provinsi (≥ 1/3 provinsi lain searah:
  kejadian pasar), 460 terisolasi & berbalik ≥ 70% dalam ≤ 2 minggu (kandidat galat data), 2.262 terisolasi tanpa berbalik.
- Label yang ujungnya menyentuh minggu lonjakan QA atau kandidat galat: 1,3–1,4% (dev), 0,7–0,8% (test); akurasi 0,59–0,68, tidak
  berbeda dari rata-rata → penanganan outlier tidak dapat mengubah skor secara berarti; eksperimen koreksi tidak dijalankan.

## 4. Kebocoran, ketersediaan fitur, dan distribusi sampel (P09, P10)

**P10 — uji menyeluruh** (`scripts/p10_leakage.py` → `hasil/p10_leakage.csv`). Untuk 76 origin (gabungan h 4 & 8), tabel resmi +
dinamika harga (54 kolom non-target) dibangun ulang setelah (T1) merusak acak semua harga, status, penggerak (minggu > o) dan harga
dunia (available_at > o), dan (T2) menghapus semua baris itu. Hasil: **0 kolom, 0 sel, 0 target latih berbeda** di semua origin.
(T3) flag `episode` dibandingkan dengan flag yang dihitung ulang hanya dari de s.d. origin: berbeda pada **1/76 origin**
(2024-12-02: resmi 1, real-time 0) karena `find_episodes` menggabungkan pemicu yang berjarak ≤ 8 minggu (minggu di antara dua pemicu
ditandai setelah pemicu kedua diketahui). Dampak: hanya model dengan grup fx (M2, C2, C2t; H5 resmi memakai M2). Bias ini
menguntungkan M2, dan M2 tetap tidak lebih baik dari M1, jadi kesimpulan H5 tidak berubah; tidak diperbaiki (artefak resmi beku).
Tiga tes regresi ditambahkan di `tests/test_direction_tuned.py` (data sintetis, setiap origin): penghapusan masa depan → seluruh
matriks + target terealisasi identik; harga dunia tersembunyi sampai `available_at`; label belum terealisasi tidak mengubah prediksi.

**Ketersediaan fitur** (`scripts/p09_balance.py` → `hasil/feature_availability.csv`): semua fitur C1-tuned kosong ≤ 1% di test;
di dev kosongnya karena pemanasan jendela di awal periode (lag 52 minggu 18%, musiman 104 minggu 34%) dan harga hilang. Kasus
yang perlu dicatat:

| Fitur | Pengodean kosong | Catatan |
|---|---|---|
| `range_pos_52` | 0,5 bila jendela 52 minggu belum penuh, harga hilang, atau rentang datar | "tak terdefinisi" & "datar" digabung dengan nilai tengah numerik → diuji di P03 (§5) |
| `idf_rel_week` | NaN di luar jendela [−6, 4] (79% baris) | NaN = "jauh dari Idulfitri" (bukan galat); HGB memberi cabang tersendiri |
| `dw_*` | NaN untuk komoditas tanpa padanan harga dunia (40%) | tidak berlaku; tidak dipakai C1-tuned |
| `reg_*` (ronde 2) | NaN sebelum regulasi berlaku + `reg_active` 0/1 | kosong 89% di baris dev, 99,4% di antaranya "belum berlaku", 0,65% harga hilang → tidak dapat dinilai di dev (keterbatasan cakupan, bukan pengodean). Tanggal berlaku = start_date (konservatif terhadap tanggal pengumuman) |

**P09 — seimbang-seri** (`hasil/p09_balance.csv`, `p09_series_*.csv`, `p09_drift.csv`):

| | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| macro F1 gabungan | 0,656 | 0,676 | 0,677 | 0,680 |
| rerata / median antarseri (337–338 seri) | 0,651 / 0,652 | 0,663 / 0,674 | 0,657 / 0,663 | 0,651 / 0,666 |
| p10 / p90 antarseri | 0,525 / 0,766 | 0,556 / 0,782 | 0,535 / 0,783 | 0,492 / 0,777 |
| porsi seri < 0,55 | 14,5% | 9,5% | 12,4% | 16,0% |
| provinsi min..maks | 0,589..0,718 | 0,641..0,734 | 0,604..0,728 | 0,606..0,729 |
| komoditas min..maks | 0,590..0,732 | 0,615..0,739 | 0,582..0,746 | 0,567..0,745 |

Sampel per seri seimbang secara konstruksi (36–38 baris uji per seri; grid lengkap). Di data latih, komoditas kaku punya lebih sedikit
baris y ≠ 0 (beras 7,8%, daging sapi 7,1% vs ± 11% lainnya). Drift naik (prediksi naik 56–60% vs aktual 52–55%) **tidak** berasal dari
dominasi seri: ia terkonsentrasi di komoditas diatur pada periode test (kelebihan prediksi naik beras +0,107 / +0,172, minyak goreng
+0,145 / +0,142, daging sapi +0,152 / +0,094, telur +0,063 / +0,095), sedangkan pada dev arahnya negatif untuk beras (−0,086 /
−0,136) dan telur. Porsi naik aktual turun dari dev ke test (beras 0,69–0,70 → 0,62–0,65), sedangkan minyak goreng naik (0,54–0,56 →
0,66–0,70): pergeseran rezim harga acuan 2024+, yang tidak bisa dipilih dari origin ≤ 2023.

Per tahun origin (h 8, `hasil/p09_up_share_by_year_h8.csv`), porsi prediksi naik komoditas diatur **tertinggal satu rezim** dari
aktual: beras aktual 0,48 / 0,78 / 0,81 / 0,52 / 0,67 / 0,82 (2021–2026) vs prediksi 0,33 / 0,55 / 0,80 / 0,70 / 0,86 / 0,95;
minyak goreng aktual 0,92 / 0,39 / 0,33 / 0,68 / 0,66 / 0,77 vs prediksi 0,81 / 0,42 / 0,52 / 0,73 / 0,88 / 0,96. Ini base rate yang
tidak stasioner (kebijakan harga acuan), bukan galat preprocessing.

## 5. Eksperimen preprocessing (origin pengembangan)

`scripts/prep.py` (tabel varian; baris & target identik dengan tabel resmi), `scripts/p_exp.py` (run), `scripts/p_eval.py` (metrik
& beda berpasangan bootstrap blok origin, 1.999 replikasi) → `hasil/exp_dev_*.csv`. Varian `base` mereproduksi `direction_tuned_preds`
C1t persis (selisih p_up 0,0). Semua varian memakai hyperparameter, kolom C1-tuned, dan label evaluasi yang sama; yang berubah hanya
fitur, bobot latih, atau penyaring baris LATIH. 38 / 37 origin, 10.966 / 11.307 baris uji (h 4 / h 8), cakupan sama.

Aturan buka test (ditetapkan sebelum run): Δ macro F1 rerata (h 4, h 8) ≥ +0,005, interval berpasangan > 0 di ≥ 1 horizon, Δ ≥ 0 di
horizon lain.

| ID | Varian | Baris latih dipakai | Δ macro F1 h 4 (interval) | Δ h 8 (interval) | Δ kuintil \|y\| terkecil h 4 / h 8 | Keputusan |
|---|---|---|---|---|---|---|
| — | `base` (C1-tuned) | 62.573 (rata²) | 0,656 | 0,676 | 0,573 / 0,553 | acuan |
| P06a | buang label latih < 1 tick | −3,1% | −0,003 (−0,010..0,005) | −0,003 (−0,009..0,003) | −0,001 / +0,001 | tidak |
| P06b | buang label latih < 2 tick | −8,1% | −0,004 (−0,011..0,004) | +0,000 (−0,007..0,006) | −0,004 / −0,000 | tidak |
| P06c | bobot stabilitas label (1 − 2·flip bootstrap hari) | 100% | −0,004 (−0,010..0,003) | −0,003 (−0,009..0,002) | +0,002 / +0,001 | tidak |
| P03a | latih hanya ujung `observed` (tanpa carry_forward/short) | −51,9% | **−0,017 (−0,031..−0,002)** | **−0,022 (−0,036..−0,008)** | −0,042 / −0,034 | lebih buruk |
| P03b | fitur tanpa ffill + `range_pos_52` NaN jujur + `n_missing_13` | 100% | −0,003 (−0,009..0,003) | −0,001 (−0,007..0,005) | +0,004 / −0,001 | tidak |
| P04a | fitur dari harga hari teramati TERAKHIR (bukan rerata) | 100% | +0,001 (−0,010..0,011) | −0,002 (−0,010..0,007) | +0,008 / +0,011 | tidak |
| P04b | + informasi dalam-minggu: `iw_gap` = log hari terakhir − log rerata minggu t, `n_days` | 100% | **+0,014 (0,004..0,026)** | +0,002 (−0,006..0,008) | **+0,028 (0,019..0,040)** / +0,008 (−0,001..0,017) | **buka test** |
| P08 | normalisasi per seri (fitur return ÷ sd Δp 52 minggu ke belakang) | 100% | −0,008 (−0,016..0,000) | **−0,011 (−0,020..−0,004)** | −0,003 / +0,002 | lebih buruk |
| P09 | bobot seimbang per komoditas | 100% | −0,000 (−0,007..0,005) | **−0,009 (−0,015..−0,004)** | −0,002 / +0,001 | lebih buruk |

Runtime: ± 12 dtk per fit HGB (2 thread), 25,6 menit untuk 750 fit (6 proses). P01 (integritas), P02 (agregasi pasar), P05 (outlier),
P07 (representasi) dan P10 (kebocoran) dijawab tanpa eksperimen model (§1–§4): tidak ada galat yang perlu dikoreksi, data per pasar
tidak ada, outlier menyentuh ≤ 1,4% label, fitur sudah seluruhnya log, kebocoran 0.

Bacaan: (1) membersihkan label LATIH yang rapuh tidak membantu → HGB sudah tahan terhadap 3–8% label berderau; (2) membuang ujung
carry_forward merusak (komoditas diatur kehilangan sebagian besar contoh) → carry_forward adalah informasi, bukan derau (konsisten
dengan U22); (3) rerata mingguan membuang informasi yang tersedia pada origin: posisi harga hari terakhir terhadap rerata minggu.
Menggantinya dengan harga hari terakhir saja tidak membantu (target tetap rerata), tetapi menambahkan selisihnya membantu tepat di
perubahan kecil, tempat kesalahan terkonsentrasi.

**Test final, hanya P04b** (`PART=test ONLY=P04_intraweek`, → `hasil/exp_test_*.csv`; `base` test = `direction_tuned_preds` persis):

| | macro F1 base | macro F1 P04b | Δ (interval) · p | Δ kuintil terkecil | F1 naik / turun P04b | MCC |
|---|---|---|---|---|---|---|
| h 4 (37 origin, 10.674 baris) | 0,677 | 0,681 | +0,004 (−0,005..0,013) · 0,35 | +0,013 (−0,008..0,030) | 0,708 / 0,654 | 0,364 (base 0,356) |
| h 8 (36 origin, 11.007 baris) | 0,680 | 0,684 | +0,005 (0,000..0,011) · 0,045 | +0,006 (−0,008..0,019) | 0,728 / 0,640 | 0,372 (base 0,363) |

BH atas 2 horizon: q 0,35 / 0,089 → **belum terbukti**. Arah sama dengan pengembangan, besarnya ± +0,005; kenaikan h 4 di
pengembangan (+0,014) tidak bertahan. Tidak ada keputusan lain yang diambil dari test.

## 6. Kesimpulan & rekomendasi

1. **Preprocessing bukan sumber utama batas skor.** Tidak ditemukan galat yang mengubah label atau fitur; target dibentuk dari harga
   teramati; tidak ada kebocoran di 76 origin. Pembentukan data (tick Rp50, komposisi hari dalam minggu) membuat 6–10% label
   (< 2 tick) mendekati koin, tetapi menjelaskan paling banyak ± 0,01–0,015 macro F1. Pada label besar dan stabil, C1-tuned tetap
   ± 0,69–0,71: celah ke 0,8 adalah kesulitan memprediksi arah harga dari informasi yang ada, bukan representasi data.
2. **Laporkan kepekaan label di samping skor utama, jangan ganti labelnya.** Skor utama tetap pada label resmi; tambahkan macro F1
   per kelompok tick dan pada label stabil (tabel §2) agar pembaca melihat bahwa kelompok < 1 tick tidak dapat diprediksi dengan
   presisi sumber Rp50.
3. **Satu-satunya celah representasi**: rerata mingguan membuang posisi harga hari terakhir terhadap rerata minggu origin. Menambahkan
   `iw_gap` memberi ± +0,005 di test (belum terbukti). Tidak diadopsi sebagai model utama; bila ingin dipakai, cukup sebagai varian
   eksploratif C1-tuned (butuh `pihps_daily` di pipeline Task 4, yang tidak ikut paket juri → hanya Tingkat C).
4. **Drift naik adalah base rate yang tidak stasioner** pada komoditas diatur (prediksi tertinggal satu rezim). Ini bukan masalah
   preprocessing. Bila dikejar, tuasnya adalah informasi rezim bertanggal (pengumuman HET/HAP) atau base rate jendela pendek, dan
   harus dipilih di origin pengembangan; prior 104 minggu ronde 2 sudah terbukti memperburuk h 8.
5. **Temuan kecil di pipeline resmi**: flag `episode` sebaiknya dihitung real-time (pemicu s.d. t) bila Task 4 resmi dijalankan
   ulang; dampaknya 1/76 origin dan hanya model grup fx, jadi kesimpulan H5 tidak berubah. `range_pos_52 = 0,5` untuk nilai tak
   terdefinisi tidak berdampak (P03b ≈ 0) dan tidak perlu diubah.
6. **Yang tidak bisa diaudit dengan data repo**: komposisi pasar di dalam provinsi (P02). Butuh data PIHPS per pasar/kota (sumber baru:
   lisensi, `sources.yaml`, as-of), dan hasil §2 menunjukkan manfaat maksimalnya terbatas pada kelompok label kecil.

| ID | Eksperimen / audit | Status |
|---|---|---|
| P01 | Integritas & duplikasi | COMPLETE — 0 duplikat, 5 harga ≤ 0 dibuang, 0 non-bulat |
| P02 | Agregasi pasar (mean/median/kohort tetap) | TIDAK BISA — data per pasar tidak ada; diganti audit agregasi hari (P04) |
| P03 | Missing (tanpa ffill, ujung observed saja) | COMPLETE — target tanpa isi; P03a lebih buruk, P03b ≈ 0 |
| P04 | Resampling / representasi minggu | COMPLETE — label sama 94–98% antar representasi; P04a ≈ 0; P04b +0,005 test (belum terbukti) |
| P05 | Outlier | COMPLETE — flag saja; ≤ 1,4% label tersentuh, akurasi sama |
| P06 | Presisi harga (tick) & pembersihan label latih | COMPLETE — tick Rp50; label rapuh 4–12%; pembersihan latih ≈ 0 |
| P07 | Transformasi (rupiah / persen / log) | COMPLETE (audit kode) — semua fitur log |
| P08 | Normalisasi per seri | COMPLETE — lebih buruk h 8 |
| P09 | Distribusi sampel & seimbang-seri | COMPLETE — drift = rezim; bobot komoditas lebih buruk h 8 |
| P10 | Isolasi temporal semua origin | COMPLETE — 0 sel berbeda; flag `episode` 1/76 origin; 3 tes regresi |
