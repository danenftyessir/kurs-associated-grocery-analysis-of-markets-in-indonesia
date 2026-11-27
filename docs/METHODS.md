# Spesifikasi Metode (acuan implementasi)

Sumber: Proposal v4 §5–6. Semua angka parameter ada di `configs/params.yaml` (kunci ditulis `params.x.y`).
Notasi: komoditas *i*, provinsi *r*, minggu ISO *t*, horizon *h* = 0..12.

## M0 — Tahap 0

### M0.1 Agregasi mingguan (WP-03)
- Varian representatif per komoditas: `commodities.yaml: variant` (U10).
- `price(i,r,t)` = rerata harga hari kerja **teramati** dalam minggu ISO *t*; `p = log(price)`.
- Status sel: `missing` (0 hari teramati), `short` (≤ `params.weekly.short_week_days`), `carry_forward`
  (mayoritas hari teramati adalah bagian rangkaian nilai identik ≥ `params.weekly.carry_forward_run_days` hari kerja),
  selain itu `observed`. Status tidak menghapus nilai; dipakai untuk robustness & filter. `carry_forward` menandai rangkaian
  harga identik, bukan imputasi: harga yang tidak berubah dan harga hari sebelumnya yang dipakai sumber saat pasar tidak beroperasi
  (FAQ PIHPS) tidak dapat dibedakan (U22, D-169).

### M0.2 Kelayakan (WP-04)
Seri layak bila: porsi minggu `missing` ≤ 0,20; tidak ada celah > 8 minggu berturut-turut; setiap tahun kalender
dalam periode terisi ≥ 70% minggu.

### M0.3 Penggerak nasional (WP-05)
- `log_e(t)` = rerata log JISDOR harian dalam minggu *t*; `de = Δ log_e`. `de_pos = max(de,0)`, `de_neg = min(de,0)`.
- `db` = Δ rerata log Brent mingguan; `d_dxy` = Δ rerata log DTWEXBGS mingguan.
- Minggu tanpa observasi (cuti Lebaran untuk JISDOR) → level minggu sebelumnya diteruskan, Δ = 0, perubahan terkumpul di
  minggu berikutnya; ditandai `e_filled`/`brent_filled`/`dxy_filled` (D-025). Grid mulai 52 minggu sebelum `period.start`.
- Musiman `S(t)`: dummy minggu relatif Idulfitri −6..+4 (`params.calendar.idulfitri`) + dummy bulan.

### M0.4 Harga dunia dalam rupiah (WP-05)
- `log_w_usd(i,m)` = Σ_k bobot_k · log harga Pink Sheet seri k bulan *m* (`commodities.yaml: pinksheet`).
- Task 1–3 (deskriptif, selaras periode observasi): `log_w_idr(i,t) = log_w_usd(i, bulan(t)) + log_e_bulan(bulan(t))`,
  dengan `log_e_bulan` rerata log JISDOR bulan tersebut. `dw = Δ log_w_idr` mingguan → nol di dalam bulan, berubah pada
  minggu pertama bulan baru (bulan = bulan hari Senin). Akibatnya `de` (mingguan) dan `dw` (bulanan) tidak kolinear sempurna (D-025).
- Task 4 (as-of): nilai bulan *m* baru boleh dipakai sejak `available_at` = hari kerja ke-2 bulan *m+1* (asumsi jadwal rilis,
  cocok dengan rilis 3 Nov 2026; tanggal rilis aktual per bulan tidak dipakai). Nilainya dari rilis 3 Nov 2026 yang memuat revisi
  historis (bukan vintage real-time).
- Komoditas tanpa padanan (bawang putih, bawang merah, cabai merah, cabai rawit) → tanpa `w`; model hanya penggerak kurs.

### M0.5 Episode (WP-06)
Minggu *t* memicu episode bila Σ_{s=t−7..t} de_s ≥ 0,03. Rangkaian pemicu yang berdempetan/tumpang tindih digabung.
`start_week` = minggu pertama pemicu; `cum_dlog_e` = depresiasi kumulatif maksimum dalam episode.
Implementasi (D-107): pemicu berjarak ≤ 8 minggu digabung; `end_week` = pemicu terakhir; minggu `start_week..end_week` → `episode = 1`.
`fx_variation`: per tahun 2018..2026 + total, minggu de > 0 / de < 0 / de = 0, rerata, sd, ekstrem.

### M0.6 MDE (WP-09, sebelum melihat β)
1. LP tanpa kurs (lag Δp, db, S(t)) per komoditas & horizon → residual.
2. SE_β ≈ SE dari regresi residual pada `de` dengan cluster per minggu (atau rumus analitik
   sd(resid)/(sd(de)·√T_eff); dokumentasikan yang dipakai). **Dipakai (D-107):** bentuk skor di bawah H0 —
   SE = √(c·Σ_t(Σ_r x̃·û)²)/Σx̃², û = residual LP tanpa kurs, x̃ = de dibersihkan dari kontrol + lag de + dw; c = CR1.
   Nasional = panel provinsi eligible pooled; wilayah = satu LP per wilayah dari `panel_weekly_region`.
3. MDE_β = (z_{0,975} + z_{0,80}) · SE_β ≈ 2,80 · SE_β; MDE_PT(h) = MDE_β(h) / γ(h).
4. Gerbang: MDE_PT(8) > 0,5 untuk ketiga {bawang putih, gula pasir, minyak goreng} → D-007 berlaku.
5. MDE asimetri (H2, D-115): parametrisasi β⁺·de⁺ + β⁻·de⁻ = β⁺·de + δ·de⁻; SE(δ) bentuk skor di bawah δ = 0 (û = residual y pada
   semua regresor kecuali de⁻ lag 0); MDE_asym = 2,80·SE(δ), satuan PT = /γ(h). H2 konfirmatori bila MDE_asym PT(8) nasional ≤ 0,5.

### M0.7 Panel 7 wilayah (WP-08)
Seri eligible saja. Per (wilayah, komoditas): p(r,t) = a_r + l_t (alternating projection; tahan perubahan komposisi, D-106);
rerata wilayah m(t) = l_t + rerata a_r; `log_price_index` = m(t) − m(minggu pertama). `n_provinces` = provinsi teramati minggu t.

## M1 — Task 1 profil respons

### M1.1 LP nasional (WP-13)

$$
y^{(h)}_{i,r,t} = \alpha_{i,r,h} + \beta_{i,h}\,\Delta e_t + \omega_{i,h}\,\Delta w_{i,t}
+ \sum_{l=1}^{L}\big(\phi_{i,l,h}\Delta p_{i,r,t-l} + \psi_{i,l,h}\Delta e_{t-l} + \chi_{i,l,h}\Delta w_{i,t-l}\big)
+ \sum_{l=0}^{4}\pi_{i,l,h}\Delta b_{t-l} + S_{i,h}(t) + u_{i,r,t+h}
$$

- $y^{(h)}_{i,r,t} = p_{i,r,t+h} - p_{i,r,t-1}$; L = `params.lp.lags` (4; robustness 2/8).
- $\alpha_{i,r,h}$: efek tetap seri (within-transform per seri).
- SE: cluster per **minggu** (`stats.regression.ols_cluster`, groups = week) — Almuzara & Sancibrián (2026).
- Asimetri: ganti $\beta\Delta e$ dengan $\beta^+\Delta e^+ + \beta^-\Delta e^-$. H2: Wald $\beta^+(8)=\beta^-(8)$.
- H2 dihitung (D-125) dengan parametrisasi ulang $\beta^+\Delta e^+ + \beta^-\Delta e^- = \beta^-\Delta e + (\beta^+-\beta^-)\Delta e^+$
  (lag $\Delta e^\pm$ tetap bebas): koefisien $\Delta e^+$ = selisih, SE cluster minggu-nya = SE Wald; $z$ normal dua sisi, α = 0,05,
  konfirmatori hanya pada komoditas yang lolos gerbang G-power H2 (D-115). Pembanding: persentil bootstrap blok dan p plasebo
  dua sisi dari selisih per replikasi. Interval yang dilaporkan (`ci_low/ci_high`) = yang lebih lebar dari Wald dan persentil
  bootstrap (aturan §M1.2, D-127; SE cluster sedikit terlalu sempit di plasebo); interval Wald tetap di `wald_ci_*` dan uji
  konfirmatori tetap Wald. Artefak `asymmetry` (ditulis `task3` karena ringan).
- Jumlah observasi efektif dilaporkan sebagai jumlah minggu (`n_weeks`), bukan baris.

### M1.2 Rasio pass-through
γ(h) = respons kumulatif $e_{t+h} - e_{t-1}$ terhadap $\Delta e_t$ (LP kurs pada dirinya, lag sama).
PT(i,h) = β(i,h) / γ(h). Interval PT dari bootstrap (rasio replikasi), bukan delta method.

### M1.3 Event study (WP-14)
Untuk setiap episode: Δ log harga dari `start_week−1` ke `start_week+h`, h = 0..12, level nasional (rerata provinsi
eligible) dan 7 wilayah. Null: 499 jendela dengan awal acak dari minggu yang tidak berada dalam episode (± 12 minggu).
Laporkan persentil 2,5/97,5 dan p = (1 + #|plasebo| ≥ |aktual|)/(1 + 499).
Implementasi (D-110): nasional = rerata lintas provinsi eligible dari selisih per provinsi (hanya provinsi teramati di s−1 dan
s+h); satu set 499 awal plasebo (dengan pengembalian) dipakai bersama semua komoditas & unit; kandidat = minggu dengan s−1 dan
s+12 di panel, di luar [start−12, end+12] setiap episode. Episode yang terpotong freeze → horizon NaN, tidak dibuang.

### M1.4 Deviasi provinsi (WP-15)
$\tilde p_{i,r,t} = p_{i,r,t} - \frac{1}{|R_t|}\sum_{r'} p_{i,r',t}$ (guncangan nasional terhapus).
Estimasi spesifikasi M1.1 pada $\tilde p$ per provinsi → δ(i,r,h); normalisasi Σ_r δ(i,r,h) = 0.
Profil 7 wilayah: spesifikasi M1.1 pada `panel_weekly_region`.

### M1.5 Inferensi bersama (WP-16)
- Moving-block bootstrap: blok 13 minggu, B = 499. Satu vektor indeks minggu per replikasi diterapkan ke harga
  **dan** penggerak semua seri (korelasi antarprovinsi, antarkomoditas, antarhorizon terjaga).
- Plasebo geser-melingkar: `de` dan `dw` di-`np.roll` sejauh s ∈ [52, T−52] terhadap harga; R = 499.
- CI final = yang lebih lebar antara ±1,96·SE cluster dan persentil bootstrap.
- Tambahan pasca-G6 (D-129, tidak praregistrasi; CI final di atas tetap resmi): blok 13 minggu lebih pendek dari jendela LP
  (h + L + 2 minggu), sehingga replikasi bootstrap menarik β ke nol makin kuat pada horizon panjang (median rasio rerata replikasi /
  estimasi nasional 0,57 / 0,35 / 0,35 pada h 4 / 8 / 12) dan persentilnya bergeser ke nol. Artefak `national_calibrated`
  (`evaluation/calibration.py`, ditulis `task3`): β_e & ω nasional pada h kunci dengan $t^* = \hat\beta^*/\widehat{se}^*$ dari
  plasebo geser-melingkar sel yang sama; crit = max($z_{0,975}$, statistik urutan |t*| yang setara p plasebo < 0,05);
  interval $\hat\beta \pm \text{crit}\cdot\widehat{se}$; p = max(p plasebo, p normal) sehingga p < 0,05 ⇔ interval tidak memuat nol;
  q BH atas 48 sel (10 komoditas × e + 6 × w, h 4/8/12).
- Perluasan D-163 (U107, tambahan): (a) baris PT di `national_calibrated` = interval β_e terkalibrasi / γ(h) (PT = 0 ⇔ β_e = 0, jadi p & q
  baris e; ketidakpastian γ diabaikan karena presisi tinggi); (b) artefak `province_calibrated`: deviasi provinsi mentah δ(i,r,h), e & w,
  h kunci; null = |t*| semua provinsi × replikasi plasebo pada sel (i, driver, h) yang sama (provinsi dapat dipertukarkan di bawah null);
  crit, interval, dan p seperti di atas; q BH per sel atas provinsi. Deskriptif; uji heterogenitas konfirmatori tetap H0-Het (M2 butir 1).

### M1.6 Penyusutan EB (WP-17)
Per (i, driver, h): τ² DerSimonian–Laird dari δ(i,r,h) dan s²(i,r,h) (REML sebagai cek).
δ̂^EB = μ + τ²/(τ²+s²)·(δ − μ). τ² = 0 → semua provinsi = μ (dilaporkan sebagai temuan).

### M1.7 Fitur respons (WP-17)
R4/R8/R12 = β kumulatif kurs (provinsi: β nasional + δ tersusut); W4/W8/W12 = ω kumulatif; PT8;
t_half = h terkecil dengan respons ≥ 50% maksimum (hanya bila CI tidak memuat nol di h maksimum);
A8 = β⁺(8) − β⁻(8) (level komoditas).

## M2 — Task 2 pola regional

1. **Heterogenitas (WP-18):** per komoditas pada δ(i,r,8) tanpa susut: Q, τ², I² (DL). Lintas komoditas:
   ρ̄ = rerata korelasi Pearson vektor deviasi provinsi antar pasangan komoditas. Setiap statistik dibandingkan
   dengan distribusi dari `placebo_stats` (p satu sisi atas, (1 + #{null ≥ aktual})/(1 + R)); H0-Het: statistik Q, FDR BH
   q ≤ 0,05 antar 10 komoditas (BH dihitung per statistik). Bobot DL butuh `se` deviasi di `profiles` dan `placebo_stats`.
2. **Clustering (WP-19):** matriks 34 × F (R & W pada h = 4, 8, 12, komoditas fokus, tersusut), z-score per kolom;
   Ward (Euclidean). Rata-rata komoditas sudah dikeluarkan sehingga identitas komoditas tidak menggerakkan klaster.
3. **Pemilihan k (WP-19):** k ∈ {2..6}; s* = maks silhouette data asli. Untuk tiap replikasi plasebo hitung
   maks silhouette yang sama → p95. Terima struktur bila s* > p95, k = argmax; bila tidak, k = 1.
4. **Stabilitas (WP-20):** K-Means (k-means++, n_init = 50) → ARI vs Ward. Ulang Ward pada setiap replikasi bootstrap →
   matriks ko-asignasi; Jaccard maksimum per klaster asli (Hennig 2007); < 0,6 → "pola lemah".
5. **Struktur tertanam (WP-21):** ambil satu replikasi plasebo berupa deviasi provinsi MENTAH δ dan SE-nya (belum tersusut),
   bagi provinsi ke k_true kelompok acak, geser tiap kelompok ke pusat simpleks berorientasi acak sehingga setiap pasangan kelompok
   berselisih δ ∈ {0,1..0,5} (RMS per fitur; jarak pusat δ·√F, D-112); lalu proses persis seperti data asli: susut EB per kolom
   (τ² DL dengan SE replikasi), z-score, langkah 2–3 dengan ambang p95 dari semua replikasi plasebo yang diproses sama (D-126);
   recovery = P(k terpilih = k_true ∧ ARI ≥ 0,8). Batas deteksi = δ terkecil dengan recovery ≥ 0,8 (NaN bila tak tercapai di grid).
   Menanam setelah penyusutan keliru: kolom dengan τ² = 0 menjadi konstan sehingga δ kecil pun terdeteksi (U105).
6. **Interpretasi (WP-20):** label netral K1, K2, …; ARI vs zona HET beras, Jawa/luar Jawa, kuantil n_kota.

## M3 — Task 3 asosiasi

- **3a (WP-22):** Kendall τ-b antara PT(8) nasional dan `import_ratio_direct` (rerata tahunan 2018–2023,
  `association.import_ratio_years`, D-121; beras = beras giling, D-120) (N = 10), p permutasi eksak dua sisi (+ satu sisi
  arah E1); leave-one-commodity-out → jackknife_min/max dan interval τ ± 1,96·SE jackknife. Tabel jalur eksposur vs PT(8), W8 (+ interval).
- **3b (WP-23):** meta-regresi efek acak δ(i,r,h) ~ Z(r) (≤ 3 fitur: ln jarak ke hub terdekat
  {Jakarta, Surabaya, Makassar}, kecukupan produksi bila ada, n_kota), bobot 1/(s²+τ²). Interval: bootstrap blok mingguan
  & CR2 cluster provinsi → yang lebih lebar. Jackknife per provinsi. H3: koef. jarak pada h = 4 < 0 (satu arah);
  h = 12 dua arah.
- **3c (WP-24):** panel dengan FE komoditas×minggu; interaksi Δe × Z(r).
- **E2 (eksploratif, D-124):** profil respons per rezim HET/HAP. Batas rezim = tanggal penetapan/perubahan harga acuan konsumen
  (HET, HAP, HAP konsumen) di `regulation` yang in_scope, bertanggal, dan tidak `unverified`, di dalam periode; rezim 0 = awal periode
  sampai sebelum perubahan pertama di tabel. Per rezim: LP nasional spesifikasi utama (h kunci, L = 4) hanya pada observasi yang
  jendela datanya [t−(L+1), t+h] utuh di dalam rezim (aturan sub-sampel Tier 1); rezim dengan jumlah minggu ≤ jumlah regresor
  dilewati. Interval = estimasi ± crit·SE cluster minggu dengan crit = max(1,96; persentil 95 |t*|), t* = estimasi/SE rezim yang
  sama di bawah R = `inference.placebo_R` geser-melingkar de & dw (≥ `inference.placebo_min_shift_weeks`; D-127, karena dengan
  ± 70 minggu dan ± 40 regresor SE cluster jauh terlalu sempit). p plasebo (1 + #|t*| ≥ |t|)/(1 + R) dan q BH atas semua baris
  dilaporkan sebagai deskriptif; dibandingkan dengan estimasi sampel penuh. Artefak `regime_profiles`, grafik forest di notebook 03.

## M4 — Task 4 evaluasi prediktif (WP-25..27)

- Target: $p_{t+h} - p_t$, h ∈ {4, 8}, per seri (provinsi atau wilayah).
- Origin: setiap 4 minggu, 2021-01-04 .. (freeze − h). Train: hanya baris dengan t + h ≤ origin. As-of join `available_at`.
- Waktu keputusan (D-169, didokumentasikan; model tidak berubah): origin t = label Senin minggu ISO t, tetapi harga eceran (rerata
  hari kerja teramati) dan kurs/Brent (rerata harian) memakai pengamatan s.d. Jumat minggu t. Prediksi secara konseptual dibuat
  sesudah minggu t lengkap dan jendela revisi PIHPS H+1 lewat = Minggu 00.00 (D-155). Harga dunia memakai `available_at` ≤ Senin
  minggu t (`merge_asof` pada label minggu), jadi rilis Selasa–Jumat minggu t baru terpakai minggu berikutnya: lebih konservatif
  dari waktu keputusan, bukan kebocoran. Cutoff yang seragam hanya lewat eksperimen baru dengan protokol beku.
- M0: prediksi 0. M1: Ridge (lag Δp 1/4/8, bulan, Idulfitri, db 1/4). M2: M1 + {de, dw} perubahan 1/4/8 minggu + episode (flag real-time: minggu t pemicu, Σ de 8 minggu s.d. t ≥ 0,03; D-162).
  M3: HistGradientBoostingRegressor dengan fitur M2 + identitas komoditas & wilayah.
- Metrik: MAE, RMSE, rasio M2/M1 dan M3/M1 (semua origin; origin dengan |Δe 4 minggu| > p80 data latih).
  DM dengan HAC (lag h−1 dalam satuan origin yang tumpang tindih) + koreksi HLN; DM > 0 = kandidat lebih akurat dari M1, DM < 0 =
  kurang akurat, sehingga setiap p DM dilaporkan bersama tanda/arahnya (D-169). Implementasi (D-113): deret = MAE per origin
  (rerata lintas seri dalam sel), h dalam satuan origin = ceil(h/4) → HAC lag 0 (h = 4) dan 1 (h = 8).
  H5: model M2, h = 8, origin large_move, sel jalur = komoditas fokus direct_import {bawang putih, gula, daging sapi} dan
  imported_input {daging ayam, telur}; p DM satu sisi (M2 lebih akurat); Holm atas 2 jalur (p tak terdefinisi = 1), α 0,05.
- Ablation: MAE(M2 tanpa fx) − MAE(M2) per komoditas & wilayah.
- Selalu laporkan n_origins dan n_nonoverlap. Sebut "pseudo-real-time" (vintage revisi tidak tersedia).

## M5 — Robustness & validasi (WP-28..30)

Tier 1 (wajib): h 8 vs 12; lag 2/4/8; sub-periode sebelum/sesudah 2021-04-05 (= V3); tanpa Mar–Jun 2020 dan bulan
|Δlog Brent| > 0,25; dekomposisi de = a + b·d_dxy + ε (komponen dolar global = fitted, spesifik rupiah = ε);
frekuensi bulanan. Tier 2 (opsional): varian alternatif; agregasi observasi terakhir; definisi eksposur/keterpencilan
alternatif; Panel Harga Bapanas sebagai outcome.
Implementasi Tier 1 (D-111): sub-sampel = observasi minggu t yang seluruh jendela datanya [t−(L+1), t+h] berada di dalam
sub-periode / tidak beririsan dengan periode yang dibuang; desain di-demean ulang per seri. Bulan Brent ekstrem = |Δ log rerata
bulanan Brent| > ambang. Dekomposisi: kedua komponen masuk satu LP. Bulanan: log harga = rerata log mingguan per bulan,
h_bulan = round(h·12/52), L_bulan = max(1, round(L·12/52)), kontrol Idulfitri = rerata bulanan dummy mingguan, SE cluster bulan.
Interval Tier 1 = ±1,96·SE cluster (bootstrap tidak diulang per cek).
Implementasi Tier 2 (D-116; deskriptif, LP nasional h kunci, driver e & w): (a) setiap varian level-2 PIHPS non-representatif dalam grup
yang sama, agregasi & kelayakan sendiri; komposit pakan bobot sama dan seri tunggal (D-012); (b) harga mingguan = hari teramati terakhir;
(c) Kendall τ-b eksak PT(8) vs ordinal jalur (impor langsung 2, input impor & paritas ekspor 1, domestik 0), baseline = τ dengan
import_ratio_direct; keterpencilan alternatif lewat meta-regresi (WP-23); (d) Panel Harga Bapanas bulanan sebagai outcome (LP bulanan
seperti Tier 1), baseline = LP bulanan PIHPS pada bulan yang sama. Butuh data mentah → tidak termasuk reproduksi Tingkat B.
V4 (D-114): kelebihan event = dlog_price − median plasebo (nasional); implikasi LP untuk jendela berawal s =
Σ_{j=0..h} β_e(h−j)·de_{s+j} + Σ_j ω(h−j)·dw_{s+j}; per komoditas × h kunci: rerata kelebihan (± 1,96·sd/√n antar episode) vs rerata
implikasi, porsi tanda sama, korelasi antar episode. V2: episode yang mulai di tahun freeze (kelebihan vs pita plasebo relatif median)
dan subset origin `case_study` (tahun freeze) di `forecast_eval`.
V2: studi kasus 2026 hanya origin dengan outcome lengkap (h=8 → origin terakhir ≈ akhir Sep 2026). V4: LP vs event study.

## Pencegahan kebocoran (wajib)
- Task 1–3 deskriptif: data bulanan diselaraskan menurut periode observasi (bukan real-time).
- Task 4: as-of join; Pink Sheet tersedia hari kerja ke-2 bulan berikutnya; impor BPS +45 hari (`params.forecast.bps_release_lag_days`).
- Tidak ada pembagian acak per baris. Target Task 3 dari estimasi periode penuh → hanya deskriptif.
