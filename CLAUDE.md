# Instruksi agent — KAGAMI (INDONERIS 2026)

**KAGAMI** = *Kurs-Associated Grocery Analysis of Markets in Indonesia* (鏡, cermin). Nama lama: RupiahPass
(masih muncul di nama file PDF proposal saja; jangan dipakai di teks baru — D-028).

Dokumen ini adalah buku pegangan operasional untuk setiap sesi agent. Isinya: konteks, protokol kerja, peta kode,
aturan, data, metode ringkas, jebakan yang sudah ditemukan, dan template. Bagian §9 (inventaris fungsi) dijaga oleh
`tests/test_claude_md.py`: setiap kali sebuah stub diimplementasikan atau fungsi publik ditambah/dihapus, perbarui §9.

---

## 0. Cara memakai dokumen ini

### 0.1 Urutan baca di awal sesi
1. §2 (status saat ini), handoff terbuka untuk anggota sesi ini di `docs/handoff/`, dan entri teratas bagian anggota
   itu di `docs/SESSION_LOG.md`.
2. Papan status di `docs/WORKPLAN.md` → pilih WP.
3. Heading WP di WORKPLAN + bagian `docs/METHODS.md` yang dirujuk WP itu.
4. §9 (inventaris) untuk tahu fungsi mana yang harus diisi dan kontrak input/outputnya.
5. Bagian lain dokumen ini bila relevan (data §10, konvensi §15, jebakan §23).

### 0.2 Sumber kebenaran per topik (bila ada konflik, sumber di kolom kanan menang)

| Topik | Sumber kebenaran |
|---|---|
| Desain penelitian (RQ, hipotesis, metode, lingkup) | `docs/spec/Proposal v4 — RupiahPass ... .pdf` (nama file lama, jangan diganti) → diringkas di `docs/PROJECT_OVERVIEW.md` |
| Aturan lomba | `docs/spec/Juknis Data Mining Indoneris 2026.pdf` |
| Rumus & parameter metode | `docs/METHODS.md` + `configs/params.yaml` |
| Status & urutan pekerjaan | `docs/WORKPLAN.md` (papan status) |
| Kontrak artefak (path, kolom wajib, ship) | `src/utils/artifacts.py` (tabel di `docs/ARCHITECTURE.md` §5 adalah salinannya) |
| Data mentah (format, cakupan, keanehan) | `docs/DATASETS.md` + `configs/sources.yaml` |
| Dataset turunan (isi, praproses, hak, keterbatasan; datasheet) | `docs/DATASHEET.md` (D-168) |
| Keputusan yang sudah diambil | `docs/DECISIONS.md` |
| Masalah terbuka & risiko | `docs/OPEN_ISSUES.md` |
| Langkah Kaggle/Colab | `docs/NOTEBOOKS.md` |
| Pembagian anggota, kepemilikan file, jadwal, titik terbit | `docs/PEMBAGIAN_TUGAS.md` |
| Hipotesis yang dibekukan | `docs/PREREGISTRATION.md` (beku setelah G6) |
| Riwayat sesi (per anggota) | `docs/SESSION_LOG.md` |
| Pesan antar anggota (serah-terima) | `docs/handoff/*.md`, format `docs/HANDOFF.md` |
| Log eksekusi & evaluasi (skema, matriks tahap × metrik) | `docs/TRACKING.md` + `src/tracking/` |
| Alur eksperimen eksploratif Task 4 (CRISP-DM, kartu 8 komponen, layar DU, aturan evaluasi) | `docs/EKSPERIMEN.md` (D-153) |
| Registri eksperimen Task 4 arah (semua varian D-145+, termasuk gagal/ditolak) | `docs/eksperimen_registry.csv` (D-156; `docs/EKSPERIMEN.md` §6) |
| Validasi kebutuhan pengguna TPID (wawancara `[HUMAN]`, U109) | `docs/PANDUAN_WAWANCARA_TPID.md` |

CLAUDE.md meringkas semua di atas agar agent bisa bekerja tanpa membuka semuanya; bila ringkasan di sini bertentangan
dengan sumber kebenaran, ikuti sumber kebenaran lalu perbaiki CLAUDE.md.

---

## 1. Konteks project

### 1.1 Lomba
- Lomba Data Mining INDONERIS 2026, tema "Realizing Impactful Innovation through Creative and Sustainable Technology".
- Gelombang 2: batas 30 Nov 2026. Target submit **29 Nov 2026**. Penjurian 1–10 Des, pengumuman 15 Des.
- Submission: (1) makalah PDF, (2) zip project berisi dataset + kode + library yang bisa dijalankan juri, (3) video demo.
- Struktur makalah wajib (juknis): judul; abstrak; pendahuluan (latar belakang, tujuan & manfaat, batasan); kajian
  pustaka; solusi usulan (deskripsi, dataset, metode, perbedaan dengan solusi sebelumnya, matriks evaluasi); hasil
  eksperimen & pengujian; analisis; kesimpulan & saran; daftar pustaka.
- Bobot penilaian: keaslian 20%, kebaruan dataset 15%, ketepatan metode 10%, manfaat 20%, kelengkapan projek 20%,
  kelengkapan laporan 15%.
- Konten wajib orisinal dan tidak melanggar hak cipta → kebijakan data turunan (D-015) dan larangan mengirim data mentah
  tanpa hak redistribusi.

### 1.2 Pertanyaan pemandu
Apakah kepekaan harga pangan eceran terhadap rupiah lebih ditentukan oleh **komoditasnya** atau oleh **lokasinya**?

Konteks: rupiah melemah sepanjang 2026 (JISDOR 18.250 pada 16 Nov 2026; nilai terakhir di data 18.252 pada 18 Nov).
Bukti agregat menunjukkan pass-through kurs ke inflasi pangan Indonesia tidak terdeteksi (Unuvar 2026: −0,012, SE 0,150,
interval −0,306..0,281, terendah dari 17 negara berkembang). Persada dkk. (2026) = heterogenitas harga beras antarprovinsi, bukan
estimasi pass-through; Hidayah & Askar (2026) tidak terverifikasi, jangan dikutip (D-177). Nol agregat bisa menyembunyikan
komoditas/provinsi yang peka.
Pembingkaian tema: ketahanan harga pangan (SDG 2) — TPID tahu komoditas mana yang historisnya paling peka di
wilayahnya dan kapan responsnya muncul.

### 1.3 Jalur transmisi (dasar pemilihan komoditas & penggerak)
1. Impor langsung — bawang putih, gula, daging sapi.
2. Input impor — jagung & bungkil kedelai untuk pakan → daging ayam, telur.
3. Paritas ekspor — minyak sawit → minyak goreng.
Jalur 2–3 bekerja lewat harga dunia dalam rupiah → penggerak kedua `w` = harga dunia padanan × JISDOR.

### 1.4 Pertanyaan penelitian → task → keluaran

| RQ | Pertanyaan | Task | Artefak utama |
|---|---|---|---|
| RQ1 | Besar & kecepatan respons nasional per komoditas terhadap IDR/USD dan harga dunia rupiah; beda menurut jalur eksposur | 1, 3a | `profiles`, `events`, `mde`, `assoc` |
| RQ2 | Porsi variasi dari komoditas vs provinsi; apakah provinsi membentuk kelompok stabil | 1, 2 | `heterogeneity`, `clusters`, `coassign` |
| RQ3 | Asimetri depresiasi vs apresiasi + perbedaan terkecil yang terdeteksi | 1 | `profiles` (e_pos/e_neg), `response_features.A8`, `mde` |
| RQ4 | Karakteristik terukur yang berasosiasi dengan perbedaan respons | 3 | `assoc` |
| RQ5 | Apakah fitur kurs & harga dunia memperbaiki prediksi 4 & 8 minggu out-of-sample | 4 | `forecast_eval`, `ablation` |

### 1.5 Hipotesis (dibekukan di G6, 21 Nov; detail `docs/PREREGISTRATION.md`)

| Kode | Isi | Uji | Jenis |
|---|---|---|---|
| H0-Het | ≥ 1 komoditas: variasi respons antarprovinsi pada h=8 > noise (τ² > 0) | Q vs plasebo; BH FDR antar 10 | konfirmatori |
| H2 | Respons depresiasi ≠ apresiasi (level komoditas, arah bebas) | Wald β⁺(8)=β⁻(8), SE cluster minggu (`asymmetry`, D-125) | konfirmatori bila MDE ≤ 0,5; selain itu deskriptif |
| H3 | Provinsi lebih terpencil → respons h=4 lebih kecil; h=12 arah bebas | meta-regresi efek acak | konfirmatori (waktu) |
| H5 | Jalur impor langsung & input impor: fitur kurs menurunkan MAE h=8 pada origin pergerakan kurs besar | rasio MAE + DM HAC | konfirmatori grup fokus |
| E1 | Impor langsung → PT(8) lebih besar dari domestik | Kendall τ, permutasi eksak N=10 | deskriptif |
| E2 | Respons sekitar perubahan HET/HAP berbeda | LP per rezim HET/HAP + forest (D-124) | eksploratif |
| E3 | Frekuensi perubahan harga tinggi → respons lebih cepat | kovariat meta-regresi | eksploratif |

### 1.6 Batas klaim (berlaku untuk SEMUA teks keluaran: makalah, app, findings, komentar grafik)
Hasil asosiasional; tidak meramal kurs; tidak mengamati rantai pasok. Respons tak terdeteksi = batas atas kepekaan,
bukan kegagalan. k = 1, asosiasi nol, rasio MAE ≈ 1 adalah hasil sah. Tabel "Jangan tulis / Tulis": §20.

---

## 2. Status saat ini (perbarui setiap akhir sesi)

Tanggal acuan: 2026-11-28. Papan lengkap: `docs/WORKPLAN.md`.

- **Selesai:** WP-00 (skeleton v2: src berlapis + 6 notebook), WP-01 (snapshot), WP-02 (loader semua sumber), WP-03 (panel mingguan),
  WP-04 (kelayakan: 337/340 layak), WP-05 (penggerak & harga dunia rupiah), WP-06 (13 episode), WP-08 (panel 7 wilayah),
  WP-09 (MDE), WP-10 (QA & `stage0_report`), WP-11 (G6: praregistrasi beku 2026-11-20 23:29, D-109), WP-12 (mesin statistik),
  WP-13 (LP nasional; 6 dtk untuk 10 komoditas × 13 h × 2 spesifikasi sejak D-118, sebelumnya 23–29 dtk), WP-14 (event study), WP-18 (G-het pada Task 1 asli, 2026-11-22), WP-21 (struktur tertanam, D-126), WP-22 (Kendall E1 resmi),
  WP-27 (evaluasi Task 4 asli, 2026-11-23), WP-28 (Tier 1; artefak `robustness` ditulis bersama validasi, 11 dtk), WP-29 (V2 & V4),
  WP-30 (Tier 2 di artefak `robustness`, 2026-11-23), dan WP jalur B yang ditutup Danen 2026-11-23 (D-130): WP-07, WP-15, WP-16,
  WP-17, WP-19, WP-20, WP-23, WP-24, WP-25, WP-26, WP-31 (app), WP-32 (paket juri; G7 lolos 2026-11-23, Tingkat A & B),
  WP-36 (log eksekusi & evaluasi terpusat `src/tracking/` + app hal. 7, 2026-11-24, D-137), WP-33 (makalah
  `docs/paper/kagami_makalah.pdf`, 2026-11-28, D-177), WP-34 (G8 audit klaim findings, app, makalah, 2026-11-28).
- **Sedang (🔶):** tidak ada. WP-35 (tugas manusia) ⬜: konfirmasi nama & afiliasi penulis, baca ulang makalah, video, commit/push, unggah.
- **Artefak yang sudah ada (lokal):** `checksums`, `pihps_daily`, `panel_weekly`, `eligibility`, `world_prices_weekly`,
  `episodes`, `drivers_weekly`, `fx_variation`, `panel_weekly_region`, `mde`, `stage0_report`, Task 1–3, Task 4 (`forecast_preds`,
  `forecast_eval`, `ablation`; diunduh dari Drive 2026-11-23), `robustness` (lokal 2026-11-23; di Drive tim `results/` 2026-11-23). Tahap 0 di Drive tim
  (P1 diunggah 2026-11-20; `mde` versi G-power + `stage0_report` 2026-11-21, lewat browser).
  Task 1 (P2) & Task 4 diunggah Ardell 2026-11-22; Task 2 (6 artefak, `planted_recovery` versi D-126) & Task 3 (`assoc`,
  `asymmetry`, `regime_profiles`) dijalankan lokal Danen dan diunggah ke `results/task2/`, `results/task3/` Drive tim 2026-11-22.
  `national_calibrated` (D-129) di Drive tim `results/task3/` 2026-11-23 (13 KB, lewat Chrome). Versi 2026-11-23 18.56–18.59 lewat
  Chrome (ganti file, ID tetap): `heterogeneity` & `partition_compare` (`results/task2/`), `assoc` (`results/task3/`), `robustness`
  (679 baris) & `findings.md` baru (`results/`), `kagami_code.zip` 74 file (`MyDrive/kagami/`; folder hasil ekstrak 21 Nov di sana basi).
- **G-power (D-007, diputuskan 2026-11-21, D-115):** MDE_PT(8) bawang putih 2,52, gula 0,90, minyak goreng 0,465 → **LP tetap
  utama**. H2 (asimetri) konfirmatori hanya untuk **beras** (MDE asimetri PT(8) 0,44) dan **daging sapi** (0,32); 8 komoditas lain
  deskriptif (1,0–9,3). Pengumuman: handoff `docs/handoff/20261121-1400_danen-ke-semua_g-power.md`.
- **WP-07 dijalankan lokal 2026-11-21** (`stage0`, kode Ardell): `exposure` rasio impor bawang putih 0,93, gula 0,37, daging sapi 0,29,
  bawang merah 0,069, beras 0,033 (D-120), lainnya ≈ 0. E1 sementara (PT(8) titik): τ-b −0,045, p eksak 0,93 → tidak terdeteksi.
- **Task 1 asli (P2, Ardell, Drive 2026-11-22; dianalisis lokal):** B = R = 499 (non-fokus 199), `se` ada di `placebo_stats`.
  Interval bootstrap rata-rata 1,4× ±1,96·SE; plasebo nasional |t| > 1,96 pada 8,1% replikasi (SE cluster sedikit terlalu sempit).
  Daging ayam β_e(8) −1,67 (bootstrap −2,62..0,06; p plasebo 0,002); minyak goreng ω(4) 0,16 (0,02..0,28), ω(12) 0,31 (0,02..0,47).
- **G-het (2026-11-22):** H0-Het ditolak untuk **telur ayam** (Q 161,7, q 0,04) dan **daging ayam** (Q 132,6, q 0,050, tepat di
  ambang); gula q 0,067; 7 lainnya tidak (4 dengan τ² = 0: bawang putih, cabai rawit, daging sapi, minyak goreng; koreksi
  2026-11-23, sebelumnya tertulis 5). Clustering k = 1 (silhouette maks 0,184 < p95 plasebo 0,196).
  Batas deteksi struktur tertanam (D-126): δ = 0,2 (selisih RMS per fitur) untuk k = 2 dan 3 (recovery 0,995 / 0,965); δ = 0,1
  hanya 0,43 / 0,13. Didorong fitur yang presisi (W, R gula/sapi/minyak; median SE deviasi 0,03–0,16).
- **H2 (D-125, interval laporan D-127 = Wald ∪ bootstrap):** beras β⁺ − β⁻ (8) −0,14 (−0,58..0,47), p Wald 0,49; daging sapi −0,26
  (−0,88..0,21), p 0,089 → tidak ditolak. Tidak ada sel H2 (10 komoditas × h 4/8/12) yang intervalnya tidak memuat nol; bawang putih
  h8 −5,78 (−10,2..3,1) walau p Wald 0,011 → jangan ditulis sebagai asimetri. E1 resmi τ-b −0,045, p eksak 0,93. H3 (h = 4, gabungan) 0,007 (−0,022..0,033), p satu sisi 0,80 → tidak didukung.
- **Catatan β:** daging ayam β_e(8) = −1,67; interval resmi `profiles` (−2,62..0,06) memuat nol (±1,96·SE −2,62..−0,73 terlalu sempit,
  jangan dikutip); h = 4 −1,16 (−1,86..−0,001) di ambang. Tier 1 (WP-28, interval SE): tanpa Mar–Jun 2020 &
  bulan Brent ekstrem −0,96 (−2,05..0,14), komponen spesifik rupiah −1,89 (−3,02..−0,76) → bukan semata COVID; tulis asosiasional.
  Aturan Brent ekstrem juga membuang Mar 2026 (+0,40 log) dan Nov 2026 (bulan parsial) (D-111).
- **Bootstrap blok menarik β ke nol (U107, D-129, 2026-11-23):** median rasio replikasi / estimasi 0,57 / 0,35 / 0,35 (h 4 / 8 / 12) →
  interval resmi terlalu konservatif. Tambahan `national_calibrated` (±crit·SE plasebo, p = max(plasebo, normal), q BH 48 sel): 7 sel
  tidak memuat nol (resmi 3); q < 0,05 daging ayam β_e(4) −1,16 (−2,10..−0,23), gula β_e(4) 0,69 (0,25..1,13; TIDAK tahan Tier 1),
  minyak goreng ω(8) 0,21 (0,08..0,34), ω(12) 0,31 (0,16..0,46); q < 0,1 daging ayam β_e(8) −1,67 (−2,77..−0,58). Interval resmi dikutip
  lebih dulu; versi terkalibrasi = analisis kepekaan inferensi.
- **E2 (D-127, 2026-11-23):** interval rezim dikalibrasi plasebo (R 499; crit median 3,09, maks 7,05). Sel yang tidak memuat nol turun
  38 → 15 dari 145; tidak ada yang lolos BH (q min 0,145) → E2 ditulis "tidak ada perbedaan antarrezim yang tahan koreksi
  multiplisitas". `assoc`: p meta-regresi tidak konsisten dengan interval (11 baris) dan ARI k = 1 → handoff ke Ardell (U106).
  `asymmetry` & `regime_profiles` versi D-127 di Drive tim 2026-11-23 (versi baru, ID file sama); `kagami_code.zip` 2026-11-23 di
  `MyDrive/kagami/` Danen, perlu diekstrak di Colab sebelum notebook dijalankan (NOTEBOOKS.md §1).
- **Tim (D-130, 2026-11-23):** Danen mengambil alih semua WP & file jalur B (Ardell: WP-07, 15–17, 19, 20, 23–26, 31, 32) dan
  jalur C (Abi: WP-33–35). Makalah PDF, video, dan unggah ditunda; fokus penyelesaian project (U106, `findings.md`, app, audit klaim,
  paket G7, bundle). Pembagian awal D-105 tetap tercatat di PEMBAGIAN_TUGAS §1–§3 sebagai riwayat.
- **Task 4 (WP-27, 2026-11-23; dijalankan ulang 2026-11-26 dengan flag episode real-time, D-162):** M2/M1 MAE 1,009 (h 4) / 1,013 (h 8),
  DM p 0,009 / 0,025 (sebelumnya 1,014 / 1,017) → fitur kurs tidak memperbaiki prediksi; H5 tidak didukung (M2/M1 h 8 large_move 1,11 / 1,12,
  Holm 1,0; hanya 8 origin large_move). Tahan terhadap ridge per komoditas (D-128). `robustness`: V2 forecast M2/M1 origin 2026 1,005 / 1,004;
  V4 26/30 sel cocok.
- **App daring & G7 ulang (D-135, 2026-11-24):** https://kagami.streamlit.app membaca artefak dari repo; 23 artefak yang dibaca app
  (± 1,4 MB, `ship=True`) kini di-track git (`.gitignore`), jadi artefak yang berubah harus ikut di-commit. `dist/` dibangun ulang
  (`bundle` 77 file, `package` 178 file 47,6 MB); Tingkat A 6/6 halaman dari zip baru. App live terisi setelah perubahan ini di-push.
- **Log eksekusi & evaluasi (WP-36, D-137, 2026-11-24):** `logs/` berisi 27 run per 2026-11-24 (19 evaluasi-saja artefak resmi, termasuk 11 dengan penilaian & interval D-140, + 8 eksekusi nyata
  stage0/task3/robustness/task2, dataset `raw:c96ce7572b4c`); hasil eksekusi task2 & task3 identik sha256 dengan artefak resmi.
  App hal. 7 membaca `logs/`; log ikut commit (app daring) dan zip juri. Task 1 & 4 berikutnya di Kaggle tercatat otomatis bila
  `kagami_code.zip` diperbarui.
- **Run end-to-end penuh (2026-11-24, lokal, folder kode bersih):** `kagami all` + `robustness --tier2` sukses (setelah D-138; Task 1
  bootstrap + plasebo 5.312 dtk, total ± 1,9 jam); 35 artefak tereproduksi (17 identik sha256, 16 selisih ≤ 3,5e-11, checksums beda
  `recorded_at`); app 7/7 halaman; pytest 357 lolos (359 setelah D-139). Rincian di WORKPLAN WP-36.
- **Penilaian dua lapis & lineage output (D-140, 2026-11-24):** audit halaman 7 (`docs/audit/20261124_audit_evaluasi_eksekusi.md`) →
  `tracking.assessment` (status hitung ≠ penilaian vs acuan), interval bootstrap blok origin untuk metrik arah, tabel arah per
  segmen, `artifact_sync`/`stage_states` (eksekusi dipisah dari evaluasi-saja), `code_sha256`/`git_dirty` (schema 2), wiring
  `task2.OPTIONAL` (province_features) & `robustness.OPTIONAL` (Tier 2) + tes baca-vs-deklarasi. Temuan: akurasi arah M1/M2 tidak
  berbeda dari baseline mayoritas (interval selisih memuat nol), M3 di atas (+0,021..0,088 h 8); komoditas kaku (carry-forward ≥ 50%:
  beras, daging sapi, gula, minyak goreng) di bawah baseline untuk semua model; 13/33 fitur clustering konstan; `robustness`
  resmi (679 baris) bukan output run eksekusi terakhir (486 baris). Hasil analisis & artefak tidak berubah.
- **Kelengkapan & kestabilan evaluasi (D-144, 2026-11-24):** F1 makro h 8 (pada baris berubah, cakupan 0,907): TimesFM 0,623, C2 0,614, C1 0,605, TSMixer 0,604, M3 0,594, M1 0,551; F1 berbobot hampir sama; akurasi bila minggu tanpa perubahan dihitung salah: TimesFM 0,566, M1 0,508. Replikasi 3 seed (h 8): TSMixer MAE/M1 0,966 ± 0,007 (0,959..0,972), akurasi 0,610 ± 0,005; PatchTST 0,972 ± 0,011, 0,583 ± 0,016; TSMixer + kurs 0,995 ± 0,009 (lebih buruk dari TSMixer di ketiga seed). Kepekaan blok bootstrap 2/3/4/6 origin: 17/17 keputusan sama di kedua horizon; DM TimesFM vs M1 p < 0,001 dan M2 vs M1 p 0,006–0,018 untuk lag HAC 1–5. Per tahun origin, keunggulan MAE TimesFM bertahan pada 2026 (0,938) walau lebih kecil dari 2023–2024 (0,876 / 0,834). Robustness Tier 2 dijalankan tercatat: identik sha256 dengan file resmi (679 baris), sekarang sinkron.
- **Koreksi multiplisitas (D-143, 2026-11-24):** Lolos BH: MAE TimesFM (± kurs) vs M1 h 4 & 8 (q ≤ 0,004); akurasi arah TimesFM vs M3 h 4 (q 0,015), C2 vs M3 h 4 (q 0,015), C1 vs M1 h 4 & 8 (q ≤ 0,024); akurasi arah vs baseline: semua model baru dan M3 (q ≤ 0,034), M1/M2 tidak. Gugur: TSMX_fx vs TSMX MAE h 4 (p 0,020 → q 0,057); segmen kaku TimesFM (q 0,053) & M2 (q 0,080); segmen lentur M1 (q 0,064). Beda berpasangan 5/30 bertahan; metrik arah vs acuan 123/132; rasio MAE eksploratif 4/14; tabel segmen h 8: 47 lebih baik, 15 lebih buruk dari 190.
- **Ronde 4 Task 4 arah EKSPLORATIF (D-148, 2026-11-25):** preprocessing baseline dibekukan; `iw_gap` disimpan sebagai varian
  `C1t_iw` (tidak di `src/`). Fitur sadar-rezim (base rate terealisasi 13/26 minggu, arah mingguan, umur kebijakan, jarak ke acuan) dan
  kalibrasi temporal (intercept, pergeseran prior) tidak lolos origin pengembangan (terbaik prior 26 minggu +0,006 / +0,008, interval
  memuat nol): drift komoditas diatur baru muncul 2024+ sehingga tidak bisa dipilih dari dev ≤ 2023. Fitur regulasi ronde 2 ternyata
  memakai acuan beras premium sejak 2024-06 (hanya test). Job > 1 jam → Colab T4, output ke Drive terpusat. Laporan
  `docs/audit/20261125_task4_ronde4.md`.
- **Split dev s.d. 2024 (D-149, 2026-11-25, pasca-hoc eksploratif):** kalibrasi & fitur rezim diuji ulang dengan dev origin + h ≤
  2024-12-31: tidak ada yang lolos (test 2025+ tidak dibuka). Fitur kebijakan menghapus drift naik komoditas diatur 2024 (+0,086 /
  +0,149 → +0,017 / +0,005) tanpa menaikkan macro F1 → drift = bias proporsi, bukan pembatas skor. C1-tuned tetap; tuas berikutnya
  hanya data baru (produsen/grosir, pasokan).
- **Riset sumber data hulu (2026-11-25, baca-saja):** kandidat terkuat PIHPS Pedagang Besar (`price_type_id=3`, sejak 2018-01, 31–34
  provinsi, varian sama dengan eceran); Produsen (`=4`) cakupan tidak lengkap; Bapanas produsen akses terbatas (SAPA); NASA POWER
  terbuka. Bukti U19: tombol Download resmi PIHPS mengekspor grid dari endpoint yang sama. Laporan `docs/audit/20261125_sumber_data_hulu.md`.
- **Pilot pedagang besar (D-150, 2026-11-25):** `pihps_wholesale` diunduh (34 provinsi, 3.978 permintaan, 0 galat) dan didaftarkan
  opsional; sangat kaku (carry_forward 85–98%), tidak mendahului eceran; C1-tuned + fitur grosir −0,006..+0,001 di pengembangan → tidak
  lolos, test tidak dibuka, C1-tuned tetap. Laporan `docs/audit/20261125_pilot_grosir.md`.
- **Pilot intraminggu & produsen (D-151, 2026-11-25):** protokol beku sebelum run. Intraminggu (`pihps_daily`, + rerata nasional)
  `IW_NAT` lolos dev (+0,020 / +0,005) → test 0,686 / 0,683 vs C1-tuned 0,677 / 0,680 (+0,0085 / +0,0033, q 0,28 / 0,30, belum
  terbukti; test tidak bersih karena `iw_gap` D-147). `pihps_producer` diunduh (3.570 permintaan, 0 galat; DKI kosong) dan didaftarkan
  opsional: tangga mingguan, eceran mendahului produsen; fitur produsen −0,006..−0,001 di dev → test tidak dibuka. C1-tuned tetap.
  Laporan `docs/audit/20261125_pilot_produsen_intraminggu.md`.
- **Validasi `IW_NAT` (D-152, 2026-11-25):** tanpa kandidat baru. Kebocoran fitur intraminggu diuji di 83 origin + 2 data penuh (84/84
  lolos, kontrol positif terdeteksi); `available_at` = Sabtu (revisi H+1). Dev: LOO ≈ rerata nasional (+0,005 / +0,001) → sinyal dari provinsi
  lain; tanpa Jumat −0,010 (h 4) → separuh keuntungan h 4 = nowcast harga terkini. Prediksi maju C1-tuned & `IW_NAT` dibekukan (12 origin
  2026-09-28..11-16, 8.112 baris, `docs/audit/20261125_iw_validasi/hasil/forward_preds.csv` + manifest; perlu di-commit sebelum 27 Nov; target
  lengkap 2026-11-27..2027-01-15). Daya: konfirmasi +0,0085 butuh ± 14 tahun origin → validasi maju hanya penjaga. Laporan
  `docs/audit/20261125_iw_validasi.md`.
- **Alur CRISP-DM Task 4 (D-153, 2026-11-25):** eksperimen eksploratif wajib kartu 8 komponen + layar Data Understanding sebelum
  modeling (`docs/EKSPERIMEN.md`). DU dev untuk pola sekuensial lintas komoditas (0/360 lolos BH; pasangan terkuat = co-trend 2021–2022),
  clustering seri (5 tipe, silhouette 0,34, tidak menjelaskan skill di luar komoditas), dan graf provinsi (informasi tetangga ρ 0,021–0,025
  setelah partial, ± 1/5 kontrol positif): ketiganya tidak lolos gerbang Modeling; tipologi 5 tipe dipakai sebagai pengetahuan. Laporan
  `docs/audit/20261125_crisp_du.md`.
- **Business Understanding Task 4 arah (D-154, 2026-11-25):** kriteria bisnis ditetapkan sebelum ukur: S1 daftar pantau provinsi
  (presisi kenaikan material vs aturan naif), S2 kalibrasi, S3 arah saat bergerak material. C1-tuned (tanpa model baru), test dibuka sekali:
  daftar pantau 2 komoditas/provinsi presisi 0,18 / 0,16 vs laju-dasar 0,09 dan aturan tren 0,08–0,09 (recall 0,41 / 0,36); Brier skill
  0,17, ECE 0,01–0,02; macro F1 saat bergerak material 0,81 vs 0,44–0,50. Dev S2 h 8 gagal tipis (ECE 0,056). Nilai Task 4 arah bagi TPID =
  daftar pantau prioritas, bukan macro F1. Laporan `docs/audit/20261125_business_understanding.md`. Masuk `results/findings.md`
  (Ringkasan butir 7, subbagian C1-tuned & daftar pantau, Keterbatasan) 2026-11-25; app daring baru menampilkannya setelah di-push,
  salinan `findings.md` di Drive tim (2026-11-23) belum diperbarui.
- **Audit D-152–D-154 (D-155, 2026-11-25):** universe ranking S1 sah (y = 0 ikut; 4 baris dev tanpa target kini ikut; presisi tetap). V1 vs
  V2 dibandingkan pada jumlah alarm sama; anggaran K = 1/2/3 dilaporkan, tidak dipilih; 57% alarm test pada komoditas diatur. Klaim
  dikoreksi di `findings.md` & adendum laporan: p_up ≠ peluang kenaikan material, test 2024+ bukan validasi independen, titik akhir ≠
  kejadian, materialitas statistik ≠ kebijakan, K1 = screening (bukan SPM), tipologi klaster deskriptif (silhouette datar), `available_at`
  konservatif Minggu 00.00. Aturan permanen `docs/EKSPERIMEN.md` §5. Berikutnya: validasi kebutuhan TPID (`[HUMAN]`, U109; panduan
  `docs/PANDUAN_WAWANCARA_TPID.md`), jendela revisi PIHPS (U110), commit prediksi maju.
- **Kelemahan tercatat ditutup (D-162, D-163, 2026-11-26):** U108 — fitur `episode` Task 4 kini real-time (`data.drivers.realtime_episode_flag`);
  task4 (M0–M3), `--direction` (C1/C2), C2t, dan robustness dijalankan ulang lokal (tercatat): M2/M1 1,009 (DM p 0,009) / 1,013 (p 0,025), H5 1,11 /
  1,12 (Holm 1,0), C1/C1t/M0/M1 identik, C2 − C1 h 8 +0,012 (−0,004..0,030); klaim "C2 > M3 h 4" gugur. U107 — baris PT di `national_calibrated`
  (3/30 sel tidak memuat nol, resmi 1) & artefak baru `province_calibrated` (1.623 baris; resmi 0–2,4% sel tidak memuat nol vs terkalibrasi
  5–12%; BH global: 7 deviasi). Kalibrasi skor daftar pantau (D-163a, protokol beku): ECE turun tetapi Brier tidak → ditolak, test tidak dibuka.
  13/33 fitur clustering konstan terbukti inert. Laporan `docs/audit/20261126_kelemahan_tercatat.md`, `docs/audit/20261126_kalibrasi_pantau.md`.
- **K4 risiko kenaikan material (D-164, 2026-11-26, EKSPLORATIF):** HGB C1-tuned beku dilatih langsung pada z = 1[y_h ≥ P80 |y_h| latih komoditas]
  (semua baris, termasuk y = 0; materialitas statistik, bukan kebijakan). Dev: AP 0,326 / 0,290 vs C1-tuned 0,246 / 0,250 (ΔAP h 4 +0,080, 0,046..0,103),
  presisi daftar pantau 2/provinsi 0,293 / 0,272 vs 0,249 / 0,221; peluang h 4 terkalibrasi (ECE 0,023, Brier < C1-tuned terkalibrasi), h 8 tidak terbukti
  → **PARTIAL**, operasional **BLOCKED** (U109). Test sekali: ΔAP +0,045 (0,017..0,083) / +0,015 (memuat 0). Koreksi D-154: pembanding laju-dasar
  komoditas wajib (h 8 C1-tuned tidak terbukti di atasnya; EKSPERIMEN §5). Prediksi maju beku `docs/audit/20261126_k4_risiko_material/hasil/k4_forward_preds.csv`
  (perlu di-commit sebelum target 2026-12-18 / 2027-01-15). `src/` tidak berubah. Laporan `docs/audit/20261126_k4_risiko_material/RESULTS.md`.
- **Validasi K4 (D-166, 2026-11-27, EKSPLORATIF, baca-saja):** target benar (target tak teramati z = 0 hanya di evaluasi, 4 baris dev, ΔAP ≤ 0,0004; kolom z
  prediksi maju = 0, **bukan label**: evaluasi maju menghitung label dari panel baru dengan `thr_*` beku). 0/6 kalibrator walk-forward memperbaiki Brier; ekor h 8
  = 5 origin (rezim kebijakan & salah alokasi komoditas). Pada ambang seragam 5% / 10% skor K4-E80 kalah dari C1-tuned (ΔAP h 8 −0,079 / −0,092) → ambang TPID
  menentukan apakah K4-E80 dipakai. Peluang h 4 hanya kategori relatif, h 8 tanpa angka; instrumen U109 R1–R12. Operasional tetap BLOCKED. Laporan
  `docs/audit/20261127_k4_validation/SUMMARY.md`.
- **CFSv2 lewat Colab (D-161, 2026-11-26):** prakiraan operasional NOAA CFSv2 (run 00Z Jumat minggu t, hujan & suhu maks hari 1–56) diekstrak
  di Colab: 437/465 minggu (28 HTTP 404, 3 di dev), agregat provinsi di `docs/audit/20261126_sumber_baru/hasil/` (bukan sumber terdaftar). Skill vs
  NASA POWER nyata (hujan 1–28 r 0,42–0,55), tetapi arah nasional increment-only vs konsensus C1t ΔAUC −0,029..+0,006 (q ≥ 0,105) → gagal gerbang 5;
  oracle cuaca terealisasi −0,013..−0,081 → mekanisme tertutup. C1-tuned tetap; U113 tinggal GDELT; aturan oracle dulu (EKSPERIMEN §3).
  Laporan `docs/audit/20261126_sumber_baru.md` §3.
- **Jalur A macro F1 & intelijen eksternal (D-165, 2026-11-26, EKSPLORATIF):** prediksi maju D-152/D-158 utuh (hash = manifest), 0 target terealisasi
  (pertama 2026-11-27); evaluator gabungan dibekukan; kedua pembekuan di git sebelum target (`ca53742`, `ec6dd19`). GDELT: DOC API 429 menetap; pilot 48 batch GKG
  Translingual lolos G1–G2 (± 12.500 artikel Indonesia/hari; presisi penyaring 0,72); G5 lewat BigQuery sandbox `kagami-gdelt` (tanpa billing,
  313,83 GB, 23.03 WIB): ΔAUC arah nasional −0,008..+0,001 (q ≥ 0,46) → GDELT REJECTED, U113 ditutup.
  Layar G5 tidak meloloskan kontrol positif `iw_gap_nat` (ΔAUC +0,015, MDE ± 0,023; EKSPERIMEN §3). Pasokan: Proyeksi Neraca Pangan Bapanas &
  luas tanam/EWS Kementan BLOCKED akses (U112); 6 kandidat lain ditolak. Tanpa modeling, test tidak dibuka, C1-tuned tetap.
  Laporan `docs/audit/jalur_a_macro_f1/RESULTS.md`.
- **Kelayakan sumber & penemuan sinyal (D-160, 2026-11-26):** GDELT & CFSv2 lolos gerbang riwayat/ketersediaan/independensi tetapi terblokir
  skala akses (TB / BigQuery; subset NCEI rusak, 8–37 GB + eccodes) → U113; SIJAGUNG (opsional `ditjenpkh_sijagung`, 2019–2026) gagal sinyal
  nasional (AUC −0,01..−0,21 vs konsensus C1t); SPORA export rusak; DIBI server mati saat uji → tanpa modeling, C1-tuned tetap. Laporan
  `docs/audit/20261126_sumber_baru.md`.
- **Audit kelayakan pasokan fisik (D-159, 2026-11-26):** SP2KP stok mingguan hanya di area admin berlogin (U112); FDP = log program
  stabilisasi 2024+ (39 pengiriman 2026); PIBC publik 1 rekaman (Jun 2025); GPM bulanan 2024+ tanpa tanggal; KSA hanya beras (headroom ≤
  +0,007) → tidak ada yang lolos syarat dev, tanpa modeling, C1-tuned tetap. Laporan `docs/audit/20261126_pasokan_fisik.md`.
- **National Shock Nowcasting Task 4 arah (D-158, 2026-11-26, EKSPLORATIF, 2 iterasi):** sumber baru `pihps_city` (110 kota PIHPS harian
  sejak 2017-03-27, opsional); Bapanas kab/kota tidak dapat diakses (U111). Iterasi 1 (breadth kota, lapisan nasional → lokal) Δ −0,008..+0,003;
  konsensus C1t sendiri prediktor arah nasional terbaik (AUC ± 0,75). Iterasi 2: koreksi nasional increment-only +0,009 / ≤ +0,002 (gagal);
  FR_CITY +0,024 / +0,008 lolos aturan tetapi = keluarga intraminggu (tanpa kota +0,024 / +0,004; kontribusi kota ≈ 0) → C1-tuned tetap;
  prediksi maju base/FR_REF/FR_CITY dibekukan (`docs/audit/20261126_nasional_lokal/hasil/forward_preds_d158.csv`, perlu di-commit).
- **Pilot cuaca sentra & impor Task 4 arah (D-157, 2026-11-26, EKSPLORATIF):** sumber baru `nasa_power` (opsional, 34 titik harian
  2016–2026). Informasi sempurna arah nasional per komoditas × origin bernilai +0,105 (hortikultura +0,049 / +0,042). Cuaca tertimbang
  produksi ATAP −0,003 / −0,003, + cuaca lokal +0,002 / −0,003, impor bulanan −0,006 / −0,015 (lebih buruk), koreksi logit walk-forward
  −0,003 / −0,005 → C1-tuned tetap; test tidak dibuka. Laporan `docs/audit/20261126_pilot_cuaca_impor.md`.
- **Audit & optimasi macro F1 Task 4 arah (D-156, 2026-11-26, EKSPLORATIF):** protokol beku sebelum run, seleksi hanya dev ≤ 2023, test
  tidak dibuka. 27 kandidat baru (8 keluarga fitur 40 kolom: momentum, volatilitas, posisi, kualitas data, cakupan hari, lintas provinsi LOO,
  kalender Iduladha/Natal/Ramadan, interaksi; hapus-satu; gabungan bersarang; jendela/peluruhan latih; threshold walk-forward; bobot kelas;
  5 seed; LightGBM/XGBoost/CatBoost/ExtraTrees/logistik) → 0 lolos; Δ −0,057..+0,003, C1-tuned tetap. Galat = informasi pada perubahan kecil
  (AUC kuintil terkecil 0,60 / 0,56) + pergeseran base rate per origin (oracle threshold global hanya +0,006). Tidak ada galat preprocessing
  baru; bias origin hari libur = efek kalender. Registri hidup `docs/eksperimen_registry.csv` (117 baris). Laporan
  `docs/audit/20261126_task4_master_f1.md`.
- **Audit preprocessing Task 4 arah EKSPLORATIF (D-147, 2026-11-25):** tidak ada kesalahan preprocessing yang mengubah label/fitur
  (target dari harga teramati tanpa isi; kebocoran 76 origin × 54 kolom × perturbasi/penghapusan masa depan = 0 sel berbeda).
  Harga harian PIHPS seluruhnya kelipatan Rp50 (tick 0,32% beras); label < 1 tick 2,4–4,3% dan label tak stabil terhadap resample
  hari 8–12% → akurasi ≈ 0,5, tetapi label ≥ 10 tick pun hanya 0,68–0,71 → derau data ± 0,01–0,015 dari celah skor. Flag `episode`
  (M2/C2) bocor pada 1/76 origin (dicatat, tidak diperbaiki). Drift naik = rezim komoditas diatur 2024+. 10 varian preprocessing
  (C1-tuned tetap, dev): pembersihan label latih, tanpa ffill, fitur hari terakhir ≈ 0; latih ujung `observed` saja −0,02; hanya
  `iw_gap` (hari terakhir vs rerata minggu origin) lolos → test +0,004 / +0,005, belum terbukti (q 0,35 / 0,089); C1-tuned tetap.
  Laporan `docs/audit/20261125_task4_audit_preprocessing.md`.
- **Optimasi arah ronde 2 EKSPLORATIF (D-146, 2026-11-25):** fitur regulasi HET/HAP, spasial, kalender, prior, level; LightGBM/XGBoost/
  ensemble; spesialis komoditas → tidak ada yang mengalahkan C1-tuned di pengembangan. Kesalahan arah terkonsentrasi pada perubahan
  kecil (kuintil |y| terkecil macro F1 0,57). Target 3 kelas test 0,625 / 0,606. TCN/MLP multi-task (Colab T4, 3 seed): −0,02..−0,07 vs C1-tuned
  di pengembangan; prediksi di Drive `KAGAMI/experiments/d146_tcn/out/`. Laporan `docs/audit/20261125_task4_ronde2.md`.
- **Optimasi klasifikasi arah EKSPLORATIF (D-145, 2026-11-24):** fitur per seri (deviasi MA/spasial, sinyal nasional, lag panjang,
  musiman) + Optuna HGB, dipilih di origin pengembangan (target ≤ 2023), dinilai di test final origin ≥ 2024: C1-tuned macro F1
  0,677 / 0,680 (h 4 / 8) vs TimesFM 0,618 / 0,621 (lolos BH); kurs, threshold, kepala TimesFM-CatBoost, TSMixer-tuned tidak
  menambah. Di `src/`: `features.price_dynamics` + `models.direction` C1t/C2t, `kagami task4 --direction-tuned` →
  `direction_tuned_preds` (identik dengan eksperimen); laporan `docs/audit/20261124_task4_optimasi_arah.md`; uji resmi tidak berubah.
- **Model deep & foundation EKSPLORATIF (D-142, 2026-11-24):** `kagami task4 --deep` → `deep_preds` (PatchTST, TSMixer ± kurs,
  TimesFM 3.0 zero-shot ± kurs; butuh extra `[deep]`, bobot TimesFM 1,32 GB non-komersial). TimesFM 3.0 zero-shot (TFM) MAE / M1 0,935 (h 4, DM p 0,0001) dan 0,895 (h 8, DM p < 0,001), R² vs ramalan nol 0,19 / 0,25 (M1 0,09 / 0,07), akurasi arah 0,616 / 0,623 (selisih vs baseline 0,049..0,116 / 0,026..0,122), ROC-AUC 0,66 / 0,69; TFM − M3 akurasi arah +0,043 (0,021..0,064) pada h 4, h 8 tidak terbukti. PatchTST & TSMixer: MAE / M1 0,96–1,00 (DM tidak nyata), akurasi arah 0,58–0,61. Fitur kurs tidak membantu: TFM_fx / TFM MAE 1,005 / 1,010 (tidak nyata), TSMX_fx / TSMX 1,041 (h 4, DM p 0,020, lebih buruk) / 1,029; selisih akurasi arah ± 0,01 (memuat nol). Komoditas kaku: semua model deep di bawah baseline arah (TFM −0,073 pada h 8). Catatan kontaminasi: TimesFM 3.0 dilatih ulang Google pada 2026 dengan korpus publik yang tidak diketahui isinya; deret harga pangan Indonesia periode uji 2021–2026 mungkin ikut di dalamnya, jadi keunggulan zero-shot adalah batas atas.
- **Klasifier arah EKSPLORATIF (D-141, 2026-11-24):** `kagami task4 --direction` → `direction_preds` (HGB classifier, fitur &
  rolling-origin Task 4; C1 tanpa kurs, C2 + kurs). C2 (+ kurs) akurasi arah 0,598 / 0,617 (h 4 / h 8) vs baseline mayoritas 0,527 / 0,545 (selisih +0,071, interval 0,034..0,108 pada h 8); C1 (tanpa kurs) 0,588 / 0,607; ROC-AUC C2 h 8 0,654 (0,623..0,682); MCC 0,17–0,23. C2 − C1 +0,010 (−0,005..0,024) / +0,009 (−0,007..0,027) → fitur kurs tidak terbukti membantu, konsisten dengan H5; C2 − M3 +0,025 (0,011..0,041) pada h 4, +0,014 (−0,000..0,031) pada h 8; C1 − M1 +0,045 / +0,047 (interval > 0). Komoditas kaku: C2 −0,026 (−0,067..0,024) → tidak lagi lebih buruk dari baseline (M3 −0,058); lentur +0,124. Prediksi selektif C1 h 8: akurasi 0,707 pada cakupan 25%. Bukan uji praregistrasi; H5 tetap dari MAE + DM.
- **Diagnostik arah Task 4 (D-139, 2026-11-24):** log evaluasi Task 4 memuat metrik klasifikasi arah (naik/turun) dari ramalan regresi;
  akurasi arah 0,543 / 0,557 / 0,573 (M1 / M2 / M3, h 4) dan 0,560 / 0,560 / 0,602 (h 8) vs baseline kelas mayoritas 0,527 / 0,545; F1 makro 0,538 / 0,550 / 0,566 dan 0,551 / 0,549 / 0,594; MCC 0,08–0,19; ROC-AUC 0,567–0,627. Bukan uji: M2 tidak lebih baik dari M1 pada h 8; kesimpulan H5 tetap. App hal. 7 menampilkan tabel + confusion matrix.
- **Siap pembekuan hasil (2026-11-26 23.00):** 39/39 artefak ada (semua `ship`); `checksums` cocok sha256 dengan 28 file mentah (39 file sumber
  eksploratif opsional sengaja di luar lineage stage0); log: task1 hanya dievaluasi (dari Kaggle), tahap lain dieksekusi & sinkron. `dist/kagami_code.zip`
  dibangun ulang (89 file) dan `dist/kagami_submission.zip` (300 file, 47,0 MB; mentah hanya 10 sumber `redistribute: true`, tanpa `pihps_daily`).
  Gladi G7 dari folder ekstrak bersih (paket didaftarkan dari `src/` zip): 7/7 halaman tanpa exception & tanpa "Menunggu hasil", tes app/package/calibration lolos.
- **Audit validasi prospektif (2026-11-27, `docs/audit/20261127_prospective_validation/`):** D-152 & D-158 utuh (sha256 = manifest = commit pra-target;
  hash beku = byte CRLF → verifikasi butuh `core.autocrlf=true`); evaluator beku tidak berubah. K4: versi beku `eb1f10db…` di-commit `044873c`
  (2026-11-27 09.53 WIB); aturan & evaluator maju K4 disetujui dan dibekukan (D-167, `scripts/k4_forward_eval.py`, hash di `hasil/pv_protocol_sha256.txt`,
  di-commit `8c7677a` 10.28 WIB). Unduh PIHPS eceran = snapshot beku (0 revisi). Putaran evaluasi ≥ 2026-11-29 (Minggu, D-155), 2026-12-20, 2027-01-17;
  cek dulu `python -X utf8 docs/audit/20261127_prospective_validation/scripts/integrity_check.py` (harus keluar 0; tanpa `-X utf8` skrip
  beku ini crash cp1252 saat keluaran ke pipa/berkas, D-169).
- **Makalah & kekurangan tersisa (D-176, D-177, 2026-11-28):** analisis kekurangan teknis & substansi. Makalah PDF dibuat:
  `docs/paper/kagami_makalah.tex` → `.pdf` (21 halaman; pdflatex `--disable-installer` karena MiKTeX AutoInstall "tanya"; 8 gambar dari
  artefak/app lewat `docs/paper/scripts/`; 55 rujukan terverifikasi Crossref/arXiv/halaman resmi di `docs/paper/RUJUKAN.md`, U12 🟢;
  naskah video `docs/paper/NASKAH_VIDEO.md`; penjaga `tests/test_paper.py`). Koreksi substansi: Persada dkk. (2026) bukan bukti
  pass-through lemah (teks lengkap), Hidayah & Askar (2026) tidak terverifikasi → tidak dikutip. Teknis: `drivers_weekly` &
  `panel_weekly` dibaca halaman 10/11 tetapi di-ignore git → kini di-track (app daring tidak lagi "Menunggu hasil" sesudah push; tes
  `test_wiring.test_app_artifacts_not_gitignored`); zip juri + laporan `docs/audit/**/*.md`, skrip & hasil red flag, dan `docs/paper/`;
  judul grafik beranda terpotong di 1280 px → `viz.style.finish` menerima `\n` di judul desktop. Dua server Streamlit di port 8501
  (satu basi) → pemeriksaan app memakai `kagami-app-8511` di `.claude/launch.json`. Angka artefak tidak berubah. pytest 428 lolos;
  `dist/` dibangun ulang (`package` 387 file 48,4 MB, `bundle` 89 file); gladi G7 dari folder bersih: 11/11 halaman tanpa exception & tanpa
  "Menunggu hasil".
- **Halaman baru dari riset UX (D-175, 2026-11-28):** "Rupiah dari waktu ke waktu" (`pages/10_Lini_Masa_Rupiah.py`: lini masa JISDOR
  + 13 episode, kipas episode per komoditas & semua komoditas) dan "Profil provinsi" (`pages/11_Profil_Provinsi.py`: label harga 10
  komoditas dengan rentang Rupiah, tren harga vs median, kelengkapan data, deviasi lolos BH global = 7 seperti findings). Tab episode di
  Respons harga kini kipas episode. Viz baru `episode_fan`, `episode_fan_grid`, `price_trend`; `fx_drivers` & `status_share` berlabel
  pembaca. Artefak yang tadinya tidak tampil: `drivers_weekly`, `panel_weekly`, `province_calibrated`. 0 tumpang tindih di 1280/1024/375 px.
- **findings.md ditulis ulang (D-174, 2026-11-28):** semua bagian tanpa label tebal + penjelasan, deret angka dalam kurung, titik koma
  prosa, kode, dan "±"; subjudul + paragraf berpelaku, tabel untuk angka padat, notasi LaTeX di berkas. "RQ1–5" → "Pertanyaan 1–5",
  "Robustness" → "Ketahanan" (tab app hal. 6 ikut). Angka tetap: setiap angka lama ada di versi baru (kecuali kode & 1,05 dalam rumus);
  tabel batas Rupiah identik. Pengecualian pembekuan `results/` 27 Nov, teks saja.
- **Lampiran untuk semua pembaca (D-173, 2026-11-28):** rumus dirender KaTeX (`st.latex`, `$...$`): Simulasi, Data & metode (persamaan LP,
  PT, skenario, MDE, simbol daftar istilah), Laporan lengkap lewat `common.math_text` (53 rumus, 0 galat). Data & metode ditulis ulang:
  langkah pengolahan berbahasa biasa + "Rumus model", "Pemeriksaan kualitas data" dari laporan Tahap 0 (kalimat + tabel berlabel)
  menggantikan laporan pipeline mentah. Laporan lengkap: panduan membaca + nama berkas jadi nama pembaca (`plain_names`). Riwayat
  eksekusi keluar dari menu (hanya `KAGAMI_DEV=1`); log & `kagami runs` tetap. Menu: "Hasil penelitian" + "Lampiran".
- **App tanpa kode & bebas tumpang tindih (D-172, 2026-11-28):** pindaian teks tampil 9 halaman: kode (U17, D-019, …) berasal dari
  laporan Tahap 0, `findings.md`, keterangan Riwayat eksekusi, dan catatan sumber `exposure` → ditampilkan lewat `common.readable`
  (kode dibuang, titik koma antarklausa jadi titik/koma; titik koma di antara angka berdesimal koma dibiarkan; `findings.md` 85 → 44).
  Berkas `findings.md` & laporan Tahap 0 tidak diubah. Kolom "Status" seragam "tidak terdeteksi" → "Kesimpulan" (naik/turun/belum
  terlihat) atau dibuang + catatan bila semua baris sama; angka tabel format Indonesia (`show_table`). Pemeriksa tumpang tindih otomatis
  (teks SVG plotly + elemen Streamlit) di 1280/1024/375 px: 3 tumpang tindih desktop diperbaiki (anotasi ketahanan, angka graf pipeline,
  judul panel rasio galat) + judul terpotong di ponsel (bungkus per thread lewat User-Agent, `viz.style.WRAP`) → 0 di ketiga ukuran.
  Bug pemilih "h = 5 minggu" (metrik H5) di Riwayat eksekusi diperbaiki. Angka artefak tidak berubah. App daring baru berubah sesudah push.
- **Teks & UX app (D-171, 2026-11-27):** pola tulisan AI dibedah di semua halaman (label tebal + penjelasan, pasangan negasi defensif,
  kode internal U109/H2/β/M2/PT(8) di halaman hasil, notasi di kalimat awam, rantai "·", caption "Pertanyaan pengguna"). Setiap halaman hasil
  kini dibuka dengan jawaban yang dihitung dari artefak; angka dalam "% per 1% pelemahan rupiah" dan Rupiah per kg (harga acuan tabel
  batas Rupiah findings: beranda "paling tinggi Rp89 per kilogram" beras); kosakata tunggal di `viz.style`; Daftar istilah di Data & metode.
  Respons harga: 3 pemilih + tab (dulu 6 pemilih, 12 blok). Eksposur dipecah → Faktor penjelas (hal. 4) + Prediksi (hal. 9 baru). Temuan lengkap
  → Lampiran teknis "Laporan lengkap" (findings.md tidak diubah). Angka artefak tidak berubah. App daring baru berubah sesudah push.
- **App produksi untuk juri (D-170, 2026-11-27):** app daring ditelusuri halaman per halaman. Menu kini berkelompok: "Hasil penelitian"
  (Beranda baru: kalimat jawaban + grafik batas perubahan harga 10 komoditas untuk rupiah −5%, lima RQ dengan jawaban dari artefak) dan
  "Lampiran teknis" (Data & metode, Riwayat eksekusi). Dari beranda dipindah: tabel 29 sumber mentah, MDE kolom mentah, status artefak dengan
  path server, laporan Tahap 0. Label terbaca di hal. 2–4, temuan dalam tab, tema terang serif. Bug: `artifact_sync`/`staleness` menganggap
  beda ujung baris sebagai beda isi → app daring menampilkan 21 artefak "tidak sinkron" palsu; diperbaiki (simulasi checkout LF: 0).
  Streamlit minimum 1.57. App daring baru berubah sesudah push.
- **Tanggapan review eksternal (D-169, 2026-11-27):** klaim reviewer diverifikasi dulu terhadap kode & artefak. App hal. 4 kini menampilkan
  arah DM (`viz.style.dm_summary`: M2/M1 1,009 / 1,013, DM −2,70 / −2,29 → M2 nyata lebih buruk, p satu sisi keunggulan M2 0,996 / 0,987);
  hal. 5 memakai rumus eksak exp(PT·ln(1 + x/100)) − 1 (`viz.plots.scenario_change`) = tabel batas Rupiah findings (linear lama menyimpang
  di ekor). `findings.md` (teks saja): batas Rupiah asimetris (+Rp89..+Rp938, bukan "± Rp90–940"), carry_forward = rangkaian harga identik
  (FAQ PIHPS: harga hari sebelumnya dipakai saat pasar tutup), batas deteksi hanya untuk struktur yang diuji, arti proksi & kualitas rasio
  impor, waktu origin (label Senin, informasi s.d. Jumat, keputusan Minggu 00.00, harga dunia ≤ Senin = konservatif), rasio biaya K4 =
  analisis kepekaan, posisi = prototipe riset (juga beranda app & README). Status PV-2b di dokumen audit disinkronkan. Angka artefak tidak berubah.
  pytest 402 lolos; `dist/` dibangun ulang (bundle 89 file, package 301 file 47,0 MB); gladi G7 dari folder bersih (`kagami` dari `src/` zip, bukan
  instalasi editable): 7/7 halaman ok. Zip juri tidak memuat `docs/audit/` maupun riwayat git (findings menyebutnya); menyertakan laporan audit ke
  zip belum diputuskan.
- **Perbaikan red flag juri (D-168, 2026-11-27):** `results/findings.md` disusun menurut tiga tingkat bukti (praregistrasi / kepekaan
  inferensi / eksploratif): eksplorasi Task 4 di Lampiran A, dan bagian baru Makna bagi pengguna (batas atas Rupiah), Kalibrasi inferensi,
  Validasi prospektif, Dataset turunan. Ukuran kalibrasi D-129 di bawah null (leave-one-out, 48 sel): 4,4% per sel vs ±1,96·SE 8,8%;
  ≥ 1 temuan BH palsu 0,5% vs 17,1%. Holm atas 10 perbandingan test 2024+: lolos C1-tuned > TimesFM, daftar pantau > aturan naif, K4 h 4.
  Baru `docs/DATASHEET.md`. Angka artefak tidak berubah; `docs/audit/20261127_redflag_juri/`.
- **Berikutnya — Danen (semua jalur):** konfirmasi nama anggota & afiliasi di blok judul makalah, baca ulang bersama tim, kompilasi
  ulang (`docs/paper/README.md`); commit perubahan D-169–D-177 (termasuk `data/processed/drivers_weekly.parquet` & `panel_weekly.parquet`)
  lalu push lewat `feat/` agar app daring memuat halaman baru; unggah `dist/kagami_code.zip` ke `MyDrive/kagami/` & dataset Kaggle
  `kagami-code` dan `results/findings.md` ke Drive tim (`[HUMAN]`); video dengan `docs/paper/NASKAH_VIDEO.md`; unggah makalah + zip + video
  (WP-35). Sesudah 27 Nov `results/` hanya berubah karena bug. Config beku sejak G6 → perubahan = DEVIASI PRAREGISTRASI.
- **Izin BI (U13):** diperoleh 2026-11-20, mencakup redistribusi data turunan → `panel_weekly` ikut paket juri (D-104).
- **Menunggu manusia (WP-35):** cek endpoint PIHPS resmi (U19), setup Kaggle + token Drive per anggota (U100),
  video, unggah.
- **Isi Drive tim (2026-11-20, diunggah lewat browser):** `data/raw/` lengkap 24 file + `checksums.csv`,
  artefak `pihps_daily`, `panel_weekly`, `world_prices_weekly`, `eligibility`, P1 (`drivers_weekly`, `episodes`, `fx_variation`,
  `panel_weekly_region`), `mde` dan `stage0_report` (versi 2026-11-21). Akses umum folder "siapa saja yang memiliki link
  dapat mengedit" diterima Danen 2026-11-23 (U24 🟢). 2026-11-25 (Chrome): + zip opsional `pihps_wholesale` & `pihps_producer` di
  `data/raw/bi_pihps/` (ukuran byte identik dengan lokal); `checksums.csv` belum memuat keduanya (sengaja, lineage stage0).
- **Data baru 2026-11-20 (D-101):** BPS impor v2 (+bawang putih), revisi regulasi, `jarak_hub`, `konkordansi_hs`,
  `hortikultura_produksi` — input WP-07 (Ardell). Versi lama di `data/raw/_superseded/`.
- **Pertukaran artefak & data mentah:** folder Drive tim https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D lewat `utils.drive` (D-100).
- `python -m kagami stage0` menulis semua artefak Tahap 0 termasuk tabel WP-07 (lokal 27 dtk, dijalankan Danen 2026-11-21); tidak ada stub tersisa di `src/`.

---

## 3. Protokol sesi

### 3.0 Siapa yang sedang bekerja (tim 3 orang)
Proyek dikerjakan tiga anggota (detail `docs/PEMBAGIAN_TUGAS.md`): **Danen** (jalur A), **Ardell** (jalur B), **Abi** (jalur C,
non-teknis). User sesi ini bisa salah satu dari mereka; bila belum jelas, **tanyakan nama** sebelum mengubah file.
- **Sejak 2026-11-23 (D-130) Danen memegang semua WP dan file jalur A, B, dan C.** Bila user = Danen, aturan kepemilikan di bawah tidak
  membatasi; handoff terbuka ke Ardell/Abi adalah daftar kerja Danen. Aturan di bawah tetap berlaku bila Ardell/Abi kembali bekerja.
- Kerjakan hanya WP dengan PIC anggota itu (kolom PIC di papan WORKPLAN) dan hanya file miliknya (PEMBAGIAN_TUGAS §3).
  Perubahan pada file milik anggota lain → buat handoff `PERMINTAAN` (docs/HANDOFF.md), jangan diedit.
- Untuk Abi: jangan mengubah `src/`, `tests/`, `app/`, `configs/`, `notebooks/`; bantu riset, data manual (CSV di
  `data/raw/manual_*/` sesuai skema §6.2), makalah di `docs/paper/`, `results/findings.md`, audit klaim, administrasi.
- Konsumen artefak tahap lain (mis. Ardell untuk Task 2/3/4) tidak menunggu: kembangkan dengan data sintetis berskema
  `src/utils/artifacts.py` (label "dummy", tidak boleh masuk hasil), jalankan ulang dengan data asli saat artefak terbit (P1–P5).
- Penomoran baru: keputusan Danen D-100+, Ardell D-200+, Abi D-300+; isu Danen U100+, Ardell U200+, Abi U300+.
- Entri SESSION_LOG ditulis di bagian anggota sendiri. Pesan ke anggota lain (artefak terbit, permintaan, keputusan,
  blokir, angka untuk makalah) → file handoff di `docs/handoff/` sesuai `docs/HANDOFF.md` + versi pendek untuk chat.

### 3.1 Mulai
1. Baca §2, lalu **handoff terbuka** untuk anggota ini: file `docs/handoff/*.md` dengan `ke` = nama anggota atau `Semua`
   dan `status` ≠ `selesai`. Ringkas untuk user dan tawarkan tindak lanjutnya. Lalu entri teratas bagian anggota itu di
   SESSION_LOG.
2. `python -m kagami status` (atau tanpa instalasi: lihat §4.4) untuk melihat sumber & artefak.
3. Pilih satu WP: status ⬜, semua dependensi ✅, atau yang diminta user. Jangan mengerjakan WP yang user minta ditunda.
4. Ubah status WP di papan WORKPLAN menjadi 🔶.
5. Daftarkan langkah kerja di task list aplikasi (bukan di teks pesan).

### 3.2 Selama bekerja
- Eksperimen eksploratif Task 4 (D-153): tulis kartu 8 komponen dan jalankan layar Data Understanding (`docs/EKSPERIMEN.md` §2–§3)
  sebelum menulis kode modeling; jangan mengusulkan model/fitur baru tanpa kartu yang lolos gerbang.
- Baca kode stub WP itu (docstring = spesifikasi kontrak). Jangan mengubah signature yang dipanggil `pipelines/` tanpa
  memperbarui pemanggilnya dan dokumen.
- Tulis tes dulu atau bersamaan: data sintetis dengan jawaban yang diketahui (§16).
- Jalankan pada data asli bila tersedia; catat angka penting (jumlah baris, distribusi, nilai ekstrem).
- Temuan yang mengubah desain → laporkan ke user dan minta keputusan bila menyangkut pilihan penelitian (varian,
  ambang, cakupan). Pilihan teknis murni boleh diputuskan sendiri dan dicatat sebagai D-xxx.
- Bila menemukan bug di kode lama, perbaiki + tambah tes regresi + catat D-xxx (contoh: D-022).
- Bila file berubah di disk tanpa sebab (OneDrive, user, sesi lain), **jangan** langsung membalikkan; laporkan dan tanya
  (contoh nyata: user memindah isi `src/kagami/` ke `src/`, menjadi D-024).

### 3.3 Selesai
0. **Sinkronkan dokumen** menurut §3.4 untuk SETIAP perubahan sesi ini (kode, config, data, keputusan, proses).
1. `pytest` hijau (seluruh suite; ± 8–9 menit di mesin Danen, didominasi tes data asli) — termasuk `tests/test_docs_sync.py` yang menolak dokumen basi.
2. Status WP ✅ di papan + perbarui bagian WP (angka penting, catatan hilir).
3. Perbarui §2 dan §9 dokumen ini (fungsi yang kini ✔).
4. Entri baru di atas **bagian anggota sendiri** di `docs/SESSION_LOG.md` (template §26.1).
4a. Bila pekerjaan memengaruhi anggota lain (artefak terbit, permintaan, keputusan, blokir, angka makalah): buat handoff
    `docs/handoff/YYYYMMDD-HHMM_<dari>-ke-<ke>_<topik>.md` dari template `docs/HANDOFF.md` §3 + versi pendek chat (§5).
    Handoff yang sudah ditindaklanjuti: ubah `status` (diterima/selesai) dan centang kotaknya.
5. Keputusan → `docs/DECISIONS.md` (template §26.2). Isu → `docs/OPEN_ISSUES.md` (template §26.3).
6. Bila `src/` berubah: ingatkan user bahwa bundle Kaggle/Drive perlu diperbarui (`python -m kagami bundle`).
7. Tutup turn dengan ringkasan + pertanyaan langkah berikutnya (tanpa command git kecuali diminta, §4.6).

### 3.4 Sinkronisasi dokumen (wajib; dokumen tidak boleh kadaluarsa)
Dokumen hidup (`README.md`, `CLAUDE.md`, `docs/*.md` selain catatan bertanggal) harus selalu menggambarkan keadaan
**saat ini**. Perbarui dokumen pada sesi yang sama dengan perubahannya — tidak ditunda ke sesi lain atau ke anggota lain.

| Jenis perubahan | Dokumen yang wajib diperbarui |
|---|---|
| Implementasi/stub WP berubah status | `docs/WORKPLAN.md` (papan + heading WP), CLAUDE.md §2 (daftar Selesai) & §9 (✔/⬜) |
| Fungsi publik baru/hapus/ganti nama/signature | CLAUDE.md §9; docstring; `docs/ARCHITECTURE.md` §2 bila modul baru |
| Modul/subpaket/folder baru atau dipindah | `docs/ARCHITECTURE.md` §2, CLAUDE.md §5–§6 & §9, `pyproject.toml` (packages), PEMBAGIAN_TUGAS §3 (pemilik) |
| Artefak/kolom baru | `src/utils/artifacts.py` + `docs/ARCHITECTURE.md` §5 + CLAUDE.md §8/§9.1 (jumlah artefak) + handoff `KEPUTUSAN` |
| `configs/params.yaml` berubah | CLAUDE.md §11.3, `docs/METHODS.md` bila rumus/ambang, PREREGISTRATION (setelah G6: DEVIASI di DECISIONS) |
| `configs/commodities.yaml` berubah | CLAUDE.md §11.1, `docs/PROJECT_OVERVIEW.md` §5 bila lingkup, DECISIONS |
| Sumber data baru/berubah | `configs/sources.yaml`, `docs/DATASETS.md`, CLAUDE.md §10, `tests/test_loaders.py` |
| Fakta data baru (cakupan, keanehan, angka) | `docs/DATASETS.md`, CLAUDE.md §10.2–§10.3; heading WP terkait |
| Keputusan | `docs/DECISIONS.md` + CLAUDE.md §21; dokumen yang isinya berubah karena keputusan itu |
| Isu baru/selesai | `docs/OPEN_ISSUES.md` + CLAUDE.md §22 |
| Metode/rumus | `docs/METHODS.md`, CLAUDE.md §12, docstring stub |
| Jadwal/gerbang/PIC | `docs/WORKPLAN.md`, `docs/PEMBAGIAN_TUGAS.md` §4, CLAUDE.md §13 |
| Notebook/runtime/cloud | `docs/NOTEBOOKS.md`, `docs/ARCHITECTURE.md` §3, CLAUDE.md §7 & §17 |
| Perintah CLI/cara menjalankan | `README.md`, `docs/ARCHITECTURE.md` §4, CLAUDE.md §4.4 |
| Aturan proses/tim (git, handoff, kepemilikan) | CLAUDE.md §3–§4, `docs/PEMBAGIAN_TUGAS.md`, `docs/HANDOFF.md` |
| Tes baru | CLAUDE.md §16.1, `docs/ARCHITECTURE.md` §2 (daftar tests) |
| Jebakan/bug baru ditemukan | CLAUDE.md §23 (+ D-xxx bila mengubah desain) |

Aturan menulis agar tidak cepat basi:
- Jangan menulis angka yang berubah sendiri di dokumen hidup (jumlah tes lolos, "kemarin", "minggu depan"); tulis tanggal
  absolut. Angka hasil data boleh, dengan nama artefak sumbernya.
- Satu fakta punya satu sumber kebenaran (§0.2); dokumen lain cukup merujuk atau meringkas. Bila meringkas, perbarui
  ringkasannya bersamaan.
- Catatan bertanggal — `docs/SESSION_LOG.md`, `docs/DECISIONS.md` (isi entri lama), `docs/handoff/*.md` — adalah jejak
  sejarah: jangan menulis ulang isinya. Keputusan yang berubah → entri baru / status `DIGANTI oleh D-xxx`.
- Penjaga otomatis: `tests/test_docs_sync.py` (tautan & path, papan WP vs stub, §2 vs papan, ID D-/U-, kunci `params.*`,
  sumber data, komoditas, notebook, subpaket), `tests/test_claude_md.py` (§9), `tests/test_wiring.py` (artefak di
  ARCHITECTURE), `tests/test_handoff.py` (format handoff). Tes hijau ≠ dokumen lengkap: matriks di atas tetap wajib.

---

## 4. Lingkungan & perkakas

### 4.1 Mesin user
- Windows 11, Python 3.13.7. Shell tool agent = **Git Bash** (sintaks POSIX); perintah yang diberikan ke user ditulis
  dalam blok `powershell`.
- Folder project ada di **OneDrive**: `C:\Users\HYPE R Series\OneDrive - Institut Teknologi Bandung\Documents\ITB\Competition\datmin`.
  Path mengandung spasi → selalu beri tanda kutip. OneDrive bisa menyinkronkan/mengubah file; perlakukan perubahan tak
  terduga sebagai disengaja sampai dikonfirmasi.
- Folder ini repo git (`main`, remote `origin` = github.com/danenftyessir/kurs-associated-grocery-analysis-of-markets-in-indonesia).
  **Agent dilarang commit/push** — lihat §4.6. Branch hanya `main`, `dev`, `feat/<fungsi>`; pesan commit `<tipe>: <deskripsi>` (§4.6, D-103, D-108).
- Perangkat lokal terbatas: tahap berat (task1, task2, task4, robustness) dijalankan di Kaggle/Colab (§17).

### 4.2 Paket terpasang
numpy 2.3, pandas 2.3, scipy 1.16, scikit-learn 1.8, torch 2.12 (CPU) & timesfm 3.0.2 (opsional `[deep]`, D-142; bobot TimesFM 3.0 di cache Hugging Face), pyarrow 24, openpyxl 3.1, pyyaml 6, streamlit 1.57, plotly 6.7,
matplotlib 3.10, pytest 9.1, nbformat 5.10, joblib 1.5 (dependensi eksplisit sejak D-127). Opsional `[drive]` (google-api-python-client, google-auth,
google-auth-oauthlib) untuk `drive-pull/push/auth` di lokal; belum terpasang di mesin Danen, sudah ada di Kaggle/Colab. **Tidak ada** statsmodels/linearmodels (D-009) — jangan
menambahkannya; pakai `src/stats/`.

### 4.3 Struktur paket (D-024)
Isi paket `kagami` ada **langsung di `src/`** (bukan `src/kagami/`). Import tetap `from kagami.x import ...`.
`pyproject.toml` memetakan `package-dir = {kagami = "src"}` dengan daftar `packages` eksplisit → subpaket baru di
`src/` wajib ditambahkan ke daftar itu. Jangan tambahkan `src` ke `PYTHONPATH` (modul `data`, `utils`, ... akan
terbaca sebagai modul top-level) dan jangan membuat folder `src/kagami/` (akan menutupi paket).

### 4.4 Menjalankan kode
- Dengan instalasi (sekali): `pip install -e ".[dev]"` lalu `python -m kagami <cmd>`.
- Tanpa instalasi: `pytest` dan app sudah punya alias (`tests/conftest.py`, `app/common.py`). Skrip ad-hoc:

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location("kagami", "src/__init__.py", submodule_search_locations=["src"])
mod = importlib.util.module_from_spec(spec); sys.modules["kagami"] = mod; spec.loader.exec_module(mod)
from kagami.utils.config import get_config
cfg = get_config()
```

  (jalankan dari root project). CLI tanpa instalasi: tambahkan `from kagami.cli import main; main(["status"])`.
- Hasil cloud ke lokal: `python -m kagami drive-pull all` (butuh token, §7.3). Hasil lokal ke tim: `drive-push <tahap>`.
- Data mentah dari Drive tim: `python -m kagami drive-pull-raw` (tidak menimpa). Danen memperbarui: `drive-push-raw`.
- Log eksekusi (WP-36, D-137): setiap `pipelines.<tahap>.run` tercatat otomatis di `out_dir/logs/`; `python -m kagami evaluate
  [TAHAP|all]` mengevaluasi artefak yang ada tanpa menjalankan ulang; `python -m kagami runs` = riwayat + hasil basi.
  Matikan dengan env `KAGAMI_TRACKING=0`. Halaman app Riwayat eksekusi hanya tampil dengan env `KAGAMI_DEV=1` (D-173).

### 4.5 Jebakan perkakas yang sudah terjadi
- `Path.write_text` di Windows menulis **CRLF**. Semua file teks project sudah dinormalkan ke LF; saat mengedit lewat
  skrip Python, pakai `p.write_bytes(text.encode("utf-8"))` atau `open(p, "w", newline="\n")`, atau gunakan tool Edit/Write.
- Heredoc bash berisi tanda kutip tunggal/backtick dalam jumlah banyak bisa gagal ("unexpected EOF"). Untuk dokumen
  panjang pakai tool Write; untuk skrip, tulis file ke scratchpad lalu jalankan.
- Tool Write menolak menimpa file yang belum dibaca di sesi ini → Read dulu (cukup beberapa baris).
- `pdftotext` tersedia (`/mingw64/bin/pdftotext`) untuk membaca PDF di `docs/`; hasilnya bukan UTF-8 murni.
- File sementara → direktori scratchpad sesi, bukan folder project.
- Output tes lambat: `tests/test_loaders.py` (~25 dtk) dan `tests/test_app.py` memuat data/streamlit; jalankan subset
  dengan `-k` saat iterasi, seluruh suite sebelum selesai.

### 4.6 Git: agent TIDAK commit/push; command siap copas hanya bila diminta
Aturan tim (permintaan Danen, 2026-11-20; diperbarui: command hanya atas permintaan). Berlaku untuk semua agent di semua clone.
- **Dilarang dijalankan agent:** semua perintah yang mengubah index, riwayat, branch, atau remote — `git add`, `commit`,
  `push`, `pull`, `fetch`, `merge`, `rebase`, `reset`, `restore --staged`, `checkout`/`switch`, `branch` (buat/hapus),
  `stash`, `tag`, `cherry-pick`, `revert`, `remote add/set-url`, `gh pr create/merge`, serta fitur commit/PR otomatis
  dari aplikasi. Juga dilarang `git init` ulang atau menghapus `.git/`.
- **Boleh dijalankan agent (baca-saja):** `git status`, `git diff`, `git log`, `git show`, `git branch --show-current`,
  `git check-ignore`, `git ls-files`, `git remote -v` — hanya bila diperlukan untuk tugas atau permintaan user.
- **Jangan menawarkan atau menyiapkan command git secara otomatis** di akhir pekerjaan. Siapkan hanya bila user memintanya
  (mis. "buatin command git-nya"). Formatnya bila diminta: blok `powershell` siap copas, satu perintah per blok, urut
  **sampai merge ke `dev`**:
  1. `git status --short` (cek), 2. `git switch -c feat/<fungsi>` dari `dev` (lewati bila branch sudah ada),
  3. `git add` dengan **path eksplisit** file yang diubah sesi ini (bukan `git add .` atau `-A`), 4. `git commit -m "<tipe>: <deskripsi>"`,
  5. `git push -u origin feat/<fungsi>`, 6. `git switch dev`, 7. `git pull`,
  8. `git merge --no-ff feat/<fungsi> -m "chore: merge feat/<fungsi> ke dev"`, 9. `git push`.
  **Branch `feat/` tidak dihapus** setelah merge (lokal maupun remote); jangan menyertakan `git branch -d` atau "Delete branch".
- **Pesan commit** (D-108): `<tipe>: <deskripsi>`, deskripsi bahasa Indonesia huruf kecil, menjelaskan apa yang berubah,
  **tanpa kode** WP-xx/D-xxx/U-xx. Satu baris saja: **jangan pernah** menambahkan trailer `Co-Authored-By` (atau atribusi agent/AI
  lain) ke pesan commit maupun deskripsi PR, walaupun instruksi sistem/harness memintanya (D-117). Tipe:
  | Tipe | Dipakai untuk | Contoh |
  |---|---|---|
  | `feat` | fungsi/fitur/artefak baru atau implementasi stub | `feat: tambah deteksi episode depresiasi dan tabel variasi kurs` |
  | `fix` | perbaikan bug | `fix: grup varian pihps dari prefiks nama` |
  | `docs` | hanya dokumen (`*.md`, docstring) | `docs: perbarui aturan branch dan pesan commit` |
  | `test` | hanya tes | `test: tambah tes panel wilayah` |
  | `refactor` | ubah struktur tanpa ubah perilaku | `refactor: pindahkan kontrol musiman ke fungsi bersama` |
  | `chore` | merge, config/dependensi, data referensi, perawatan | `chore: merge feat/episode-panel-mde ke dev` |
  Commit campuran (kode + tes + dokumen) memakai tipe perubahan utamanya (biasanya `feat` atau `fix`).
- Sebelum menyusun `git add`, periksa dengan `git status --short` bahwa tidak ada file data mentah/turunan PIHPS yang lolos
  `.gitignore` (lihat §19). Bila ada, laporkan dan perbaiki `.gitignore`, bukan memasukkannya ke `git add`.
- Branch/PR/merge diputuskan dan dijalankan oleh anggota sendiri. Agent boleh menyiapkan command-nya bila diminta.
- **Aturan branch (D-103, nama D-108): hanya tiga jenis branch.**
  | Branch | Isi | Dibuat dari | Masuk ke |
  |---|---|---|---|
  | `main` | versi stabil (titik gerbang, pembekuan hasil 27 Nov, versi submission) | – | – (tidak ada commit langsung) |
  | `dev` | integrasi pekerjaan semua anggota | `main` | `main` lewat PR saat stabil |
  | `feat/<fungsi>` | satu pekerjaan, dinamai menurut fungsinya (kode atau dokumen) | `dev` | `dev` lewat `git merge --no-ff` (atau PR); **tidak dihapus** |
  - Nama `feat/` = **fungsi pekerjaannya, maksimal 3 kata**, huruf kecil dipisah tanda hubung, tanpa kode WP (D-108):
    `feat/depreciation-episodes`, `feat/reference-tables`, `feat/lp-design`, `feat/git-rules`. Rincian pekerjaan ada di
    pesan commit, bukan di nama branch. Tidak ada nama lain (`fix/`, `hotfix/`, `danen/...`, dll.): perbaikan bug juga `feat/<fungsi>`.
  - Tidak ada commit langsung ke `main` atau `dev`: `dev` hanya menerima merge dari `feat/` (merge `--no-ff` lalu push, atau PR);
    `main` hanya menerima merge dari `dev` saat stabil. Satu `feat/` dikerjakan satu anggota.
  - Abi tidak memakai git (berkas lewat Drive; Danen/Ardell yang meng-commit di `feat/` mereka).
  - Agent tetap tidak membuat branch/commit/push/merge/PR; bila user meminta command, gunakan skema ini.

---

## 5. Peta repo

```
datmin/
├── CLAUDE.md                 dokumen ini
├── README.md                 ringkasan untuk manusia/juri (cara jalan, hak data)
├── .gitignore                mentah/turunan PIHPS/results tidak di-track (kecuali checksums, manual_regulation, findings.md, 23 artefak app D-135)
├── pyproject.toml            dependensi, package-dir, daftar packages, pytest
├── configs/
│   ├── params.yaml           SEMUA angka analisis (dibekukan di G6)
│   ├── commodities.yaml      10 komoditas: varian, peran, jalur eksposur, padanan Pink Sheet, HS, FAOSTAT
│   ├── sources.yaml          29 sumber mentah (9 opsional): path relatif raw_dir, lisensi, redistribute, retrieval, availability
│   └── runtime.yaml          folder Drive tim (ID), kredensial Drive, folder kerja Colab (bukan parameter analisis)
├── data/
│   ├── raw/<sumber>/         snapshot mentah (TIDAK pernah ditimpa; salinan di Drive tim, D-101); raw/checksums.csv
│   ├── raw/_superseded/      versi lama yang digantikan (tidak dipakai, tidak diunggah)
│   ├── reference/            tabel buatan tim: region_crosswalk.csv, province_aliases.csv (+ hasil WP-07)
│   ├── interim/              pihps_daily.parquet, forecast_preds.parquet (boleh dihapus)
│   └── processed/            panel_weekly, panel_weekly_region, drivers_weekly, world_prices_weekly
├── results/                  stage0/, task1/, task2/, task3/, task4/, robustness.csv, findings.md
├── logs/                     log pelacakan JSON (WP-36): runs/, evaluations/, errors/, pipelines/ — tidak pernah ditimpa
├── notebooks/                00_stage0_data … 05_robustness (.ipynb, tanpa output)
├── src/                      paket kagami (§6, §9)
├── app/                      Streamlit: Home.py (router st.navigation), pages/1..11 (8 hasil + 2 lampiran + 1 pengembang), common.py
├── tests/                    §16
├── docs/                     proposal & juknis (PDF) + dokumen kerja (§0.2); docs/arsip/ = inventaris dataset xlsx (arsip)
│   ├── handoff/              satu file per serah-terima antar anggota (format docs/HANDOFF.md, dites)
│   ├── audit/                laporan audit & eksperimen bertanggal (teks .md ikut zip juri, D-176)
│   └── paper/                makalah lomba: kagami_makalah.tex/.pdf, figures/, scripts/, RUJUKAN.md, NASKAH_VIDEO.md (D-177)
└── dist/                     (dibuat oleh bundle/package; boleh dihapus)
```

---

## 6. Arsitektur lapisan (D-026)

```
utils  ←───────────── dipakai semua lapisan
stats  ←───────────── dipakai features/models/evaluation
data → features → models → evaluation → pipelines → (cli, notebooks) ; viz ← (app, notebooks)
tracking ← pipelines (dekorator), cli, app (membaca log)
```

| Lapisan | Tanggung jawab | Boleh import | Tidak boleh |
|---|---|---|---|
| `utils` | config, runtime, registry artefak, I/O, tanggal, stub | stdlib, pandas, yaml | import lapisan lain |
| `stats` | fungsi statistik murni (numpy/scipy) | numpy, scipy, pandas | baca/tulis file, Config |
| `data` | baca mentah, bersihkan, agregasi mingguan, penggerak, tabel referensi, QA | utils | estimasi model, write_artifact |
| `features` | turunan siap model (fitur respons, matriks clustering, fitur as-of) | utils, stats, data (fungsi murni) | baca file mentah |
| `models` | estimator: LP, deviasi, event study, clustering, asosiasi, peramalan | utils, stats, features | write_artifact |
| `evaluation` | inferensi, uji, metrik, MDE, robustness | utils, stats, features, models | write_artifact |
| `pipelines` | urutan langkah, `require` input, `write_artifact` | semua lapisan | logika analisis |
| `viz` | grafik plotly dari artefak | pandas, plotly | menghitung estimasi |
| `tracking` | log eksekusi & evaluasi: run ID, lineage sha256, metrik berpenjaga per tahap (WP-36, D-137) | utils, data.snapshot, features/models/evaluation (hanya membaca ulang artefak) | mengubah artefak; import pipelines di tingkat modul |

Aturan praktis:
- Fungsi lapisan bawah menerima & mengembalikan DataFrame/ndarray; yang membaca/menulis artefak hanya `pipelines/`.
  Pengecualian yang disengaja: `data/snapshot.run` dan `data/download.run` (operasi file mentah, dipanggil CLI).
- Satu fungsi yang dipakai ≥ 2 task dan bersifat statistik murni → pindahkan ke `stats/` + tes.
- Grafik baru → `viz/plots.py` dan harus dipakai app atau notebook (tes menolak fungsi viz yatim).
- Modul baru wajib terjangkau dari CLI atau di-import app/notebook (tes `test_every_module_used`).

---

## 7. Config & runtime (D-027)

### 7.1 `Config` (`src/utils/config.py`, dataclass frozen)

| Atribut / properti | Arti | Default lokal |
|---|---|---|
| `root` | folder kode (berisi `configs/params.yaml`) | dicari naik dari file config.py; env `KAGAMI_ROOT` |
| `raw_root` → `raw_dir` | folder data mentah; `sources.yaml: path` relatif ke sini | `root/data/raw`; env `KAGAMI_RAW_DIR` |
| `out_root` → `out_dir` | folder TULIS artefak | `root`; env `KAGAMI_OUT_DIR` |
| `artifact_dirs` | folder BACA tambahan (output tahap sebelumnya) | kosong; env `KAGAMI_ARTIFACT_DIRS` (pemisah `os.pathsep`) |
| `read_dirs` | urutan baca: out_dir → artifact_dirs → root | – |
| `reference_dir` | `root/data/reference` (tabel tim yang ikut kode) | – |
| `params`, `commodities`, `sources`, `runtime` | isi YAML (cached) | – |
| `regions`, `province_aliases` | CSV referensi (cached) | – |
| `source_path(key)` | `raw_dir / sources[key].path` | – |
| `source_files(key)` | daftar file konkret (mengurai `glob`) | – |
| `commodity_ids(role)` | id komoditas, opsional filter peran | – |
| `seed` | `params.seed` | 20261121 |
| `path(rel)` | `root / rel` (untuk configs/app, BUKAN artefak) | – |

### 7.2 Runtime per platform (`src/utils/env.py::init_runtime`)

| Platform | Deteksi | root | raw_dir | out_dir | artifact_dirs |
|---|---|---|---|---|---|
| local | default | folder project | `data/raw` | folder project | – |
| kaggle | env `KAGGLE_KERNEL_RUN_TYPE` atau `/kaggle/input` ada | dataset `kagami-code` | dataset `kagami-raw` bila dilampirkan (folder berisi `bi_pihps/`, kedalaman ≤ 3), selain itu `/kaggle/temp/kagami_raw` (pull dari Drive) | `/kaggle/working` | input yang memuat `results/`, `data/processed/` atau `data/interim/` (cadangan) |
| colab | `google.colab` ter-import / env `COLAB_RELEASE_TAG` | `DRIVE_DIR` | `DRIVE_DIR/data/raw` bila ada, selain itu `/content/kagami_raw` (pull dari Drive) | `/content/kagami_out` (`runtime.yaml`) | – |

`DRIVE_DIR` default `/content/drive/MyDrive/kagami` (kode & mentah). Env `KAGAMI_*` selalu menang.

### 7.3 Folder Drive tim (D-100)
- Semua artefak antar tahap/anggota disimpan di folder Drive tim https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D (ID di `configs/runtime.yaml`),
  dengan struktur = path artefak (`results/task1/profiles.parquet`, `data/processed/...`).
- Data mentah di `data/raw/` folder itu (D-101): `utils.drive.push_raw` (MD5 sama dilewati) / `pull_raw` (hanya file yang
  belum ada, tidak menimpa); CLI `drive-push-raw` / `drive-pull-raw`; notebook 00 memanggil `pull_raw`.
- `utils.drive.pull(cfg, names)` → unduh ke `cfg.out_dir`; `utils.drive.push(cfg, stages)` → unggah semua artefak milik tahap
  itu (timpa versi lama). Notebook memanggil keduanya; lokal lewat CLI `drive-pull` / `drive-push`.
- Kredensial: Colab login Google interaktif; Kaggle Secret `KAGAMI_DRIVE_TOKEN` (token OAuth akun anggota, Internet ON);
  lokal `~/.kagami/drive_token.json` (env `KAGAMI_DRIVE_TOKEN_FILE`) dari `python -m kagami drive-auth --client-secret F`.
- Default `strict`: Kaggle/Colab gagal keras bila Drive tak tersedia; lokal dilewati dengan pesan.
- Agent tidak boleh membuat/mengisi token, login ke akun Google/Kaggle user, atau mengubah izin berbagi folder — `[HUMAN]`.
- Token & `client_secret*.json` tidak pernah di-commit (`.gitignore`). Folder dibagikan terbatas ke akun anggota (U24).

### 7.3 Aturan
- Kode tahap TIDAK PERNAH menulis ke `raw_dir` atau `root`; semua tulisan lewat `write_artifact` → `out_dir`.
  (`download` menulis ke `out_dir/data/raw/_redownload/`.)
- Jangan memakai `cfg.path(...)` untuk artefak; pakai `utils.io`.
- Jangan hard-code `/kaggle/...` atau `/content/...` di luar `utils/env.py`.

---

## 8. Artefak & I/O

### 8.1 API (`src/utils/io.py`)
- `write_artifact(cfg, name, df_or_md)` → tulis ke `cfg.out_dir / ARTIFACTS[name].path`; validasi kolom wajib
  (kolom ekstra boleh). Parquet/CSV/MD menurut ekstensi.
- `read_artifact(cfg, name)` → baca dari lokasi pertama di `read_dirs`; validasi kolom; `ArtifactMissing` bila tak ada.
- `find_artifact`, `exists`, `artifact_path` (lokasi tulis), `require(cfg, *names)` (gagal cepat dengan petunjuk).
- `utils.env.artifact_status(cfg, stage=None)` → tabel ada/lokasi/WP (dipakai CLI `status` dan notebook).

### 8.2 Menambah/mengubah artefak (checklist)
1. Tambah/ubah entri di `src/utils/artifacts.py` (name, path relatif out_dir, stage, wp, kolom wajib, ship, deskripsi).
2. Tulis dari `pipelines/<tahap>.py` dengan `write_artifact(cfg, "<name>", ...)` (tes memeriksa pola ini).
3. Perbarui tabel `docs/ARCHITECTURE.md` §5 (tes memeriksa setiap nama artefak tercantum dengan backtick).
4. Bila dibaca tahap lain: tambahkan ke `REQUIRES` pipeline konsumen.
5. Bila dikirim ke juri (`ship=True`): pastikan tidak bisa merekonstruksi data mentah tanpa hak (D-015).
6. Bila dipakai app: tambahkan ke `need(...)` halaman terkait.

### 8.3 Konvensi kolom
- `week`: Timestamp Senin minggu ISO (`utils.dates.week_start`). Semua join antar sumber memakai ini (D-020).
- `commodity`: id internal snake_case (`beras`, `bawang_putih`, …), bukan nama PIHPS.
- `province_id`: int 1–34 (kerangka 34 provinsi lama, urutan PIHPS); `region`: 7 nilai di `region_crosswalk.csv`.
- `level` ∈ {national, region, province}; `unit` = `ALL` / nama wilayah / province_id (disimpan sebagai string bila campur).
- `driver` ∈ {e, w, e_pos, e_neg, PT}. Respons dalam Δ log harga per 1 poin log penggerak.
- Harga dalam log natural; perubahan = selisih log.
- Interval: `ci_low`, `ci_high` (95%). Setiap estimasi yang dilaporkan wajib punya interval.

### 8.4 Kebijakan `ship` (dikirim ke juri)
- Tidak dikirim: `pihps_daily`, semua mentah dengan `redistribute: false`. `panel_weekly` (panel provinsi mingguan) DIKIRIM:
  izin BI mencakup redistribusi data turunan (U13, D-104).
- Dikirim: panel 7 wilayah sebagai **indeks log** (relatif minggu pertama), penggerak sebagai log/perubahan log,
  semua hasil estimasi, tabel tim, sumber CC BY (Pink Sheet, FAOSTAT, FRED, tabel regulasi tim).

---

## 9. Inventaris modul & fungsi (dijaga `tests/test_claude_md.py`)

Format baris: `` - `nama` · ✔ · keterangan `` (sudah diimplementasi) atau `` - `nama` · ⬜ WP-xx · keterangan `` (stub).
Semua fungsi publik top-level (tanpa awalan `_`) di setiap modul `src/` wajib tercantum dengan status yang benar.
Saat mengimplementasikan stub: ganti `⬜ WP-xx` menjadi `✔` dan perbarui keterangan bila kontrak berubah.

### 9.1 Infrastruktur

#### src/cli.py
- `status` · ✔ · cetak sumber mentah (ada/tidak) dan artefak (ada, lokasi, WP, ship).
- `runs` · ✔ · riwayat run tercatat (`logs/`) + input yang berubah setelah run terakhir tiap tahap (WP-36).
- `main` · ✔ · argparse: status, snapshot, download, stage0..robustness, all (satu pipeline_id), evaluate [TAHAP|all], runs,
  package, bundle [--raw], app, drive-pull [TAHAP|all] (+ log), drive-push TAHAP, drive-push-raw, drive-pull-raw,
  drive-auth --client-secret.

#### src/utils/config.py
- `get_config` · ✔ · `Config()` dengan default + env var.

#### src/utils/env.py
- `detect_platform` · ✔ · "kaggle" | "colab" | "local".
- `kaggle_raw_dir` · ✔ · cari folder input berisi `bi_pihps/`.
- `kaggle_artifact_dirs` · ✔ · cari input yang memuat results/ atau data/processed|interim/.
- `init_runtime` · ✔ · bangun Config per platform; cetak ringkasan lokasi.
- `describe` · ✔ · teks ringkasan lokasi (root, raw, out, artifact_dirs).
- `artifact_status` · ✔ · DataFrame artefak: available, location, wp, ship (opsional per stage).

#### src/utils/io.py
- `artifact_path` · ✔ · lokasi tulis.
- `find_artifact` · ✔ · lokasi baca pertama atau None.
- `exists` · ✔ · artefak ada di salah satu read_dirs.
- `write_artifact` · ✔ · tulis + validasi kolom.
- `read_artifact` · ✔ · baca + validasi kolom; `ArtifactMissing`.
- `require` · ✔ · gagal cepat bila input tahap belum ada.
- `add_observer` · ✔ · daftarkan pengamat fn(event, name, path) setelah setiap read/write artefak (lineage WP-36; galat pengamat ditelan).
- `remove_observer` · ✔ · lepas pengamat.

#### src/utils/drive.py
(kelas `GoogleDriveClient` = pembungkus Drive API v3; `DriveClient` = protokol untuk tes; `DriveUnavailable`)
- `credentials` · ✔ · kredensial Google per platform (Colab login, Kaggle Secret, file token lokal).
- `connect` · ✔ · bangun klien Drive API v3; `DriveUnavailable` bila library/kredensial tidak ada.
- `pull` · ✔ · unduh artefak `names` dari folder Drive tim ke out_dir; laporkan yang belum ada di Drive.
- `push` · ✔ · unggah artefak milik `stages` dari out_dir ke folder Drive tim (path dicerminkan, timpa versi lama).
- `authorize_local` · ✔ · OAuth di browser → simpan token JSON (isi untuk Kaggle Secret).
- `push_raw` · ✔ · unggah semua file sumber + checksums ke `data/raw/` Drive tim; MD5 sama dilewati (D-101).
- `pull_raw` · ✔ · unduh file sumber yang belum ada di raw_dir (termasuk sumber glob); tidak pernah menimpa (D-101).
- `push_logs` · ✔ · unggah log pelacakan baru `logs/<jenis>/<id>.json` ke Drive tim (dipanggil `push`; tidak menimpa, WP-36).
- `pull_logs` · ✔ · unduh log yang belum ada di out_dir/logs (dipanggil `pull`; lineage lintas platform, WP-36).

#### src/utils/dates.py
- `week_start` · ✔ · tanggal → Senin minggu ISO (normalize).

#### src/utils/todo.py
- `todo` · ✔ · lempar `NotImplementedYet("WP-xx ...")`.

#### src/utils/artifacts.py
(Tidak ada fungsi publik; berisi dataclass `Artifact` dan dict `ARTIFACTS` — 39 artefak (`province_calibrated` D-163); `direction_preds` (D-141), `direction_tuned_preds` (D-145) & `deep_preds` (D-142) eksploratif.)

### 9.2 Lapisan data

#### src/data/loaders.py
- `norm_name` · ✔ · trim + spasi tunggal (mis. "Cabai Merah Keriting " → tanpa spasi akhir).
- `province_lookup` · ✔ · NAMA UPPER → province_id (crosswalk + alias + pemekaran).
- `map_province` · ✔ · Series nama → Int64 province_id (NaN bila tak dikenal, mis. "INDONESIA").
- `load_jisdor` · ✔ · → date, idr_per_usd (parse "9.760,00").
- `load_pihps` · ✔ · zip 34 CSV lebar → long: date, province_id, province, level, commodity_group, item, price; grup varian dari prefiks nama (D-022).
- `load_sijagung` · ✔ · → month, report (stok|pembelian), region, measure, value; ekspor SIJAGUNG bulanan per wilayah (opsional, audit D-160).
- `load_pihps_city` · ✔ · → date, province_id, province, regency_id, regency, level, commodity_group, item, price; zip 110 kota PIHPS (opsional, pilot D-158).
- `load_pihps_manifest` · ✔ · MANIFEST.csv di zip v2 atau None.
- `load_pinksheet` · ✔ · sheet "Monthly Prices" → month, series (dinormalisasi, tanpa `**`), unit, usd_price.
- `load_fred` · ✔ · key brent|dollar_index → date, value (hari libur dibuang).
- `load_faostat_sua` · ✔ · SUA Asia NOFLAG, filter Indonesia → year, item, element, unit, value.
- `load_bps_import_monthly` · ✔ · → month, hs8_code (str), hs_description, import_value_usd, import_netweight_kg.
- `load_bps_import_annual` · ✔ · 5 xlsx exim → hs8_code, hs_description, year, total (USD, D-019), file.
- `load_comtrade` · ✔ · key `comtrade_import` (2017–2022) | `comtrade_import_2023` (QA U102) → month, hs_code, hs_description, net_weight_kg, cif_usd, primary_value_usd.
- `load_bapanas_panel` · ✔ · → month, commodity_bapanas, province_id, province, price_geomean, status_map, ref_price.
- `load_bapanas_het_settings` · ✔ · → commodity_bapanas, type, zone, price, start_date, end_date.
- `load_padi` · ✔ · tahun 2024|2025 → year, province_raw, province_id, harvest_ha, productivity_ku_ha, production_ton_gkg.
- `load_konsumsi_beras` · ✔ · → province_raw, province_id, year, kg_per_capita_year.
- `load_neraca_beras` · ✔ · kolom asli neraca beras nasional.
- `load_het_hap_current` · ✔ · kolom asli tabel HET/HAP berlaku.
- `load_regulation_history` · ✔ · kolom asli riwayat regulasi.
- `load_jarak_hub` · ✔ · → province_raw, province_id, capital, lat, lon, km_jakarta/surabaya/makassar, nearest_hub, dist_hub_km, ln1p_dist_hub (38 prov).
- `load_konkordansi_hs` · ✔ · konkordansi Comtrade → HS8 BPS, kode sebagai string, kolom asli.
- `load_hortikultura` · ✔ · → commodity_atap, province_raw, province_id, year, production_ton, note (baris nasional dibuang).
- `load_penduduk` · ✔ · → province_raw, province_id, year, population (jiwa); satuan dari nama kolom, total dijaga 200–400 juta; file opsional (U14).
- `load_n_kota` · ✔ · → province_id, province, n_kota, kota_list, source_url (isi manual Abi; opsional, U15).
- `load_gkg_beras` · ✔ · → year, factor, source_url, note: faktor GKG → beras (isi manual Abi; opsional, U21).
- `load_nasa_power` · ✔ · → date, province_id, precip_mm, t2m, t2m_max dari 34 CSV harian NASA POWER (opsional, pilot D-157).

#### src/data/snapshot.py
- `sha256_file` · ✔ · hash file bertahap.
- `build_checksums` · ✔ · hash semua `source_files`; kolom `file` relatif raw_dir; pertahankan waktu catatan bila hash sama.
- `run` · ✔ · tulis artefak `checksums`.

#### src/data/download.py
- `find_link` · ✔ · tautan pertama di HTML yang cocok pola (dites tanpa jaringan).
- `resolve_url` · ✔ · tautan terbaru dari `landing_url`+`link_pattern` bila ada, selain itu `url` (U16).
- `download` · ✔ · sumber http → `out_dir/data/raw/_redownload/<key>/` (SSL via certifi) + bandingkan hash; manual → instruksi.
- `run` · ✔ · semua sumber atau daftar kunci.

#### src/data/weekly.py
- `select_variants` · ✔ · varian representatif per komoditas → pihps_daily (hanya hari teramati, harga > 0); error bila varian tak ada.
- `aggregate_weekly` · ✔ · grid 34×10×minggu; price = rerata hari teramati; status (D-021); kolom ekstra cf_share.
- `eligibility` · ✔ · missing_share ≤ 0,20, max_gap_weeks ≤ 8, min_year_coverage ≥ 0,70; hanya `missing` dihitung kosong.

#### src/data/drivers.py
- `driver_weeks` · ✔ · grid minggu penggerak: start − 52 minggu .. minggu freeze.
- `idulfitri_relative_week` · ✔ · minggu relatif Idulfitri terdekat dalam jendela [−6, 4], selain itu NaN.
- `build_national_drivers` · ✔ · log_e, de, de_pos, de_neg, log_brent, db, log_dxy, d_dxy, month, idf_rel_week, *_filled (tanpa episode).
- `build_world_prices` · ✔ · komposit Pink Sheet per komoditas, log_w_idr = log_w_usd + rerata log JISDOR bulanan; dw; available_at.
- `build_world_variants` · ✔ · Tier 2: komposit harga dunia alternatif untuk komoditas ≥ 2 seri (bobot sama, seri tunggal; D-012).
- `realtime_episode_flag` · ✔ · D-162 (U108): flag episode real-time = minggu pemicu (Σ de 8 minggu s.d. t ≥ ambang) → fitur `episode` Task 4.
- `mark_episode_weeks` · ✔ · tambah kolom `episode` (0/1) ke drivers dari tabel episodes.
- `find_episodes` · ✔ · Σ de 8 minggu ≥ 0,03; pemicu berjarak ≤ 8 minggu digabung → episode_id, start_week, end_week, cum_dlog_e (+ peak_week, n_trigger_weeks, in_period; D-107).
- `fx_variation_table` · ✔ · per tahun 2018.. + total: n_dep/app/zero_weeks, mean_dep/app, sd_de, max/min, n_episode_weeks.

#### src/data/reference.py
- `haversine_km` · ✔ · jarak great-circle (km).
- `build_concordance` · ✔ · 10 baris PIHPS–HS–Pink Sheet–FAOSTAT + confidence high/medium/low; seri/item yang tak ada di data → error.
- `build_exposure` · ✔ · rasio impor langsung FAOSTAT rerata `association.import_ratio_years` (bawang putih via BPS/Comtrade + ATAP), ordinal input impor, link harga dunia, source, import_ratio_neraca (D-120).
- `parse_regulation_dates` · ✔ · teks tanggal → (start, end, date_status); tidak menebak tanggal.
- `classify_verification` · ✔ · teks verifikasi → verified | partial | confirmed | unverified.
- `build_regulation` · ✔ · gabung 3 sumber regulasi per (komoditas, instrumen, zona, periode); tanggal tak terverifikasi → verification='unverified'.
- `build_province_features` · ✔ · dist_hub_km, ln_dist_hub = ln(1+km), rice_sufficiency (NaN sampai penduduk & GKG ada, U14/U21), n_kota (U15), cek jarak_hub.

#### src/data/panel.py
- `build_region_panel` · ✔ · rerata log provinsi eligible per wilayah (dua arah, tahan komposisi; D-106) → indeks relatif minggu pertama + n_provinces.
- `build_variant_panels` · ✔ · Tier 2: panel mingguan + kelayakan setiap varian PIHPS non-representatif (11 varian, termasuk Minyak Goreng Curah).
- `last_observation_panel` · ✔ · Tier 2: harga mingguan = hari teramati terakhir (dari `pihps_daily`).
- `build_bapanas_panel` · ✔ · Tier 2: Panel Harga Bapanas bulanan → week (awal bulan), province_id, commodity, log_price (pemetaan `BAPANAS_TO_PIHPS`).

#### src/data/qa.py
- `flag_price_outliers` · ✔ · lonjakan satu hari |Δlog| > 0,5 yang berbalik (ditandai, tidak dihapus); data asli 59 hari.
- `check_import_totals` · ✔ · Σ BPS bulanan vs total tahunan (USD) per HS8 × tahun; data asli 241/241 cocok.
- `check_trade_overlap` · ✔ · U102: Σ Comtrade per kode konkordansi vs Σ HS8 BPS terpetakan pada bulan bersama (rasio nilai/kg, korelasi bulanan, ok ±1%); data asli 2023 14/15 cocok (D-133).
- `check_bapanas_bias` · ✔ · rerata bulanan PIHPS vs Panel Harga Bapanas (pemetaan `BAPANAS_TO_PIHPS`, D-110): bias_log, corr_dlog.
- `coverage_table` · ✔ · cakupan per sumber (n_rows, start, end).
- `stage0_report` · ✔ · markdown laporan Tahap 0 (cakupan, kelayakan, episode, variasi kurs, MDE + G-power, QA).

### 9.3 Lapisan features

#### src/features/response.py
- `shrink_deviations` · ✔ · τ² DL (+REML cek) per (komoditas, driver, h); tambah baris province shrunk=True; τ² = 0 → semua μ.
- `response_features` · ✔ · R4/R8/R12, W4/W8/W12, PT8, t_half, A8 per (level, unit, commodity); provinsi = nasional + δ tersusut.

#### src/features/clustering.py
- `feature_columns` · ✔ · daftar fitur (R semua komoditas fokus, W yang berpadanan harga dunia) × feature_horizons.
- `feature_matrix` · ✔ · 34 provinsi × (R & W pada h 4/8/12 komoditas fokus), tersusut, z-score (opsi satuan respons).
- `replicate_feature_matrices` · ✔ · satu matriks per rep dari placebo_stats / boot_replicates (EB per rep, butuh `se`).

#### src/features/forecast.py
(konstanta `FEATURE_GROUPS`: base / fx / id)
- `origins` · ✔ · origin tiap 4 minggu 2021-01-04 .. minggu data terakhir − h.
- `feature_table` · ✔ · tabel fitur semua (minggu × seri) + target `y_<h>`; harga dunia as-of `available_at` (kolom audit).
- `split_origin` · ✔ · (train, test) satu origin dari feature_table: train t + h ≤ origin, test t = origin.
- `build_features` · ✔ · (train, test) per origin; as-of join `available_at`; target p_{t+h} − p_t.

#### src/features/price_dynamics.py
(konstanta `GROUPS` 9 kelompok fitur, `SELECTED_GROUPS` 7 hasil ablation; EKSPLORATIF D-145)
- `extend_table` · ✔ · feature_table + fitur dinamika harga per seri dari log harga s.d. t (lag panjang, EWM, sd, momentum, musiman `_h{h}`, deviasi MA/rentang/spasial, umur carry-forward, sinyal nasional komoditas).
- `group_columns` · ✔ · nama kolom kelompok untuk satu horizon (kolom musiman berakhiran `_h{h}`).

### 9.4 Lapisan models

#### src/models/local_projection.py
- `build_design` · ✔ · y^{(h)} dan regresor (blok kurs `de*`/`dw*` + lag, `dp_l*`, `db_l0..4`, `idf_*`, `month_*`), within-transform per seri; opsi `elig`, `unit_col`, `price_col` (D-107).
- `regressors` · ✔ · nama kolom regresor sebuah desain.
- `fit_lp` · ✔ · OLS + SE cluster per minggu (`stats.regression.ols_cluster`) → driver, estimate, se, n_weeks, n_obs, n_clusters.
- `fx_self_response` · ✔ · γ(h) untuk PT = β/γ (γ(0) = 1; data asli γ(4/8/12) = 1,44/1,32/1,03).
- `asymmetry_wald` · ✔ · H2: Wald β⁺ = β⁻ nasional, SE cluster minggu, lewat parametrisasi ulang (de, de⁺) → beta_pos, beta_neg, estimate = β⁺ − β⁻, se (D-125).
- `national_profiles` · ✔ · loop komoditas × h × {simetris, asimetris} → profiles level=national (e, w, e_pos, e_neg, PT; se/ci PT = NaN sampai bootstrap); opsi `elig`, `horizons`, `commodities`; desain dibangun sekali per spesifikasi (D-118, ± 6 dtk).

#### src/models/deviations.py
- `demean_cross_section` · ✔ · log harga − rerata lintas provinsi teramati per (minggu, komoditas).
- `province_deviations` · ✔ · δ(i,r,h) per provinsi dengan desain LP nasional (`_design_parts`), Σ_r δ = 0; driver e, w.
- `region_profiles` · ✔ · profil 7 wilayah dari panel_weekly_region lewat `national_profiles` per wilayah (Tingkat B).

#### src/models/event_study.py
- `event_paths` · ✔ · Δ log harga p(s+h) − p(s−1), h 0..12, episode `in_period`; nasional = rerata selisih per provinsi eligible.
- `placebo_starts` · ✔ · kandidat awal plasebo di luar [start−12, end+12] setiap episode (data asli: 164 minggu).
- `placebo_bands` · ✔ · 499 jendela plasebo bersama (seed + 1401) → placebo_lo/hi/p, n_placebo, placebo_median; gabung jadi artefak events.

#### src/models/clustering.py
- `ward_labels` · ✔ · Ward Euclidean; k=1 → semua 0; label menurut kemunculan pertama.
- `best_silhouette` · ✔ · (k*, s*) silhouette Ward maksimum atas k ≥ 2 (aturan sama dengan evaluation.planted).
- `select_k` · ✔ · silhouette maks asli vs p95 plasebo → cluster_selection; tidak lolos → k = 1.

#### src/models/association.py
- `all_permutations` · ✔ · semua n! permutasi (int8, n ≤ 10) tanpa itertools.
- `kendall_permutation_test` · ✔ · τ-b + p permutasi eksak dua sisi & satu sisi (statistik S).
- `kendall_exact` · ✔ · E1: τ-b PT(8) nasional vs import_ratio_direct, p eksak 10!, interval jackknife LOCO → assoc level=commodity.
- `meta_regression` · ✔ · meta-regresi efek acak δ ~ Z(r) (≤ 3 fitur); interval max(bootstrap, CR2); p = max(p CR2, p bootstrap sisi) konsisten dengan interval, `p_boot`, `q_fdr` BH (D-132); jackknife provinsi; H3 h=4.
- `fe_interaction` · ✔ · FE komoditas×minggu + komoditas×provinsi, interaksi Δe × Z(r), SE cluster minggu (dapat dipotong).

#### src/models/forecasting.py
(konstanta `MODELS` = M0..M3)
- `fit_predict` · ✔ · M0 nol, M1 ridge base (alpha CV waktu), M2 + fx, M3 HGB + id; drop_groups untuk ablation.
- `rolling_predictions` · ✔ · loop horizon × origin × model (+ `M2_nofx`) → artefak `forecast_preds`; `run_m3`; lanjut dari checkpoint.

#### src/models/direction.py
(konstanta `CLASSIFIERS` = C1 base+id, C2 base+fx+id; EKSPLORATIF D-141, bukan uji praregistrasi; `TUNED_CLASSIFIERS` C1t/C2t + `TUNED_HGB`, D-145)
- `fit_predict_proba` · ✔ · HistGradientBoostingClassifier (params.forecast.hgb) dilatih langsung untuk arah naik/turun (y = 0 dibuang) → probabilitas naik.
- `rolling_direction` · ✔ · loop horizon × origin × klasifier dengan rolling-origin Task 4 → artefak `direction_preds`; lanjut dari checkpoint.
- `tuned_columns` · ✔ · D-145: (kolom numerik, kategori) C1t (base + `price_dynamics.SELECTED_GROUPS`) / C2t (+ fx) per horizon.
- `fit_predict_proba_tuned` · ✔ · D-145: HGB dengan `TUNED_HGB` (Optuna pada origin pengembangan, dibekukan) → probabilitas naik.
- `rolling_direction_tuned` · ✔ · D-145: rolling-origin Task 4 untuk C1t/C2t pada tabel + fitur dinamika → artefak `direction_tuned_preds`; lanjut dari checkpoint.

#### src/models/neural.py
(konstanta `SEQ_MODELS` PTST/TSMX/TSMX_fx, `FOUNDATION_MODELS` TFM/TFM_fx, hiperparameter tetap; EKSPLORATIF D-142; butuh torch, TFM butuh `timesfm` 3.x)
- `split_replicate` · ✔ · nama replikasi seed `<model>_r<k>` → (model dasar, k); hanya model deep yang dilatih (D-144).
- `series_arrays` · ✔ · feature_table → matriks minggu × seri (log harga ffill, de, dw as-of, target y_h, kode komoditas).
- `fit_sequence_model` · ✔ · latih PatchTST / TSMixer (± kurs) global dengan loss L1 pada jendela yang target-nya terealisasi s.d. origin.
- `predict_sequence_model` · ✔ · ramalan y_h (h 4 & 8) untuk pasangan (origin, seri).
- `load_timesfm` · ✔ · muat TimesFM 3.0 (google/timesfm-3.0-pytorch, CPU); None bila paket tidak ada.
- `predict_timesfm` · ✔ · zero-shot: konteks log harga s.d. origin (± kovariat masa lalu de & dw) → y_h = ramalan − p_t.
- `rolling_deep` · ✔ · rolling-origin Task 4 (baris uji sama), refit model deep tiap `REFIT_EVERY` origin → artefak `deep_preds`; lanjut dari checkpoint.

### 9.5 Lapisan evaluation

#### src/evaluation/power.py
- `asymmetry_null_se` · ✔ · SE δ = β⁻ − β⁺ di bawah H0 asimetri (bentuk skor, tanpa β̂; D-115).
- `compute_mde` · ✔ · MDE β & PT dari residual LP tanpa kurs, nasional & 7 wilayah, h 4/8/12 (+ unit, se_beta, gamma, n_weeks, n_obs; nasional + se_asym, mde_asym_beta, mde_asym_pt).
- `null_se` · ✔ · SE cluster-minggu di bawah H0 (bentuk skor; β̂ tidak dihitung; D-107).
- `gate_g_power` · ✔ · keputusan gerbang D-007 dari artefak mde + h2_confirmatory per komoditas (MDE asimetri PT(8) ≤ 0,5).

#### src/evaluation/inference.py
- `joint_bootstrap` · ✔ · moving-block 13 minggu, satu indeks per replikasi untuk semua seri (selisih di-resample, level dibangun ulang); `done`/`checkpoint` untuk melanjutkan run (D-204).
- `circular_placebo` · ✔ · geser de & dw ≥ 52 minggu; profil nasional + provinsi (h kunci) di bawah null, `se` dibawa; `done`/`checkpoint` seperti bootstrap.
- `bootstrap_ci` · ✔ · CI = yang lebih lebar dari ±1,96·SE dan persentil bootstrap (PT: persentil saja).

#### src/evaluation/heterogeneity.py
- `heterogeneity_stats` · ✔ · Q, τ² (DL) & `tau2_reml`, I² (tanpa susut) per komoditas (h=8, driver e) + ρ̄ lintas komoditas; butuh kolom `se` (juga di placebo_stats).
- `placebo_pvalues` · ✔ · p plasebo satu sisi (1+#≥)/(1+R) + q BH per statistik; `reject` = Q dengan q ≤ fdr_q → artefak heterogeneity.

#### src/evaluation/stability.py
- `kmeans_agreement` · ✔ · K-Means (n_init=50) + ARI vs Ward; k = 1 → ARI 1.
- `bootstrap_stability` · ✔ · ko-asignasi + Jaccard per klaster (weak < 0,6); label netral K1, K2, ….
- `compare_partitions` · ✔ · ARI vs zona HET, Jawa/luar Jawa, kuantil n_kota (dilewati bila tak ada), 7 wilayah; klaster tunggal (k = 1) → ari NaN (D-132).

#### src/evaluation/planted.py
- `deviation_matrices` · ✔ · placebo_stats → per rep (D, S): deviasi provinsi MENTAH & se, kolom = fitur clustering (D-126).
- `shrink_matrix` · ✔ · EB per kolom (DL + eb_shrink) seperti shrink_deviations, sel kosong = rerata kolom (sama dengan features.clustering).
- `best_silhouette` · ✔ · (k*, s*) silhouette Euclidean Ward maksimum atas k ≥ 2.
- `placebo_threshold` · ✔ · p95 silhouette maksimum matriks plasebo terstandardisasi (aturan select_k).
- `plant_structure` · ✔ · k_true kelompok acak, pusat simpleks berorientasi acak, selisih RMS per fitur = δ (D-112).
- `recovery_curve` · ✔ · δ 0,1..0,5 × k_true 2/3 × planted_reps: tanam pada deviasi plasebo mentah → susut EB → z-score → pilih k vs ambang plasebo (diproses sama) → recovery_rate, ari_mean (+ n_reps, k_correct_rate, threshold); ward bisa disuntikkan (D-126).
- `detection_limit` · ✔ · δ terkecil dengan recovery ≥ 0,8 per k_true (batas deteksi untuk findings).

#### src/evaluation/forecast_eval.py
- `n_nonoverlap` · ✔ · jumlah origin berjarak ≥ h minggu (pilih rakus).
- `evaluate` · ✔ · MAE/RMSE per horizon × model × subset × (komoditas|wilayah|jalur H5|ALL), rasio vs M1, DM HAC pada selisih MAE per origin (lag ceil(h/4)−1), n_origins, n_nonoverlap; H5 Holm (keluarga 2 jalur, p NaN = 1).
- `ablation` · ✔ · MAE(`M2_nofx`) − MAE(M2) per sel yang sama, subset all/large_move.

#### src/evaluation/asymmetry.py
(konstanta `H2_HORIZON` = 8, `COLUMNS`)
- `asymmetry_tests` · ✔ · H2: Wald (uji utama) + status konfirmatori gerbang G-power + persentil bootstrap & p plasebo selisih β⁺ − β⁻ ; ci_low/high = yang lebih lebar dari Wald & bootstrap (Wald di wald_ci_*, D-127) → artefak `asymmetry` (D-125).

#### src/evaluation/calibration.py
(konstanta `DRIVERS` = e, w; `KEY`, `COLUMNS`, `PROVINCE_KEY`, `PROVINCE_COLUMNS`)
- `national_calibrated` · ✔ · β_e & ω nasional h kunci: crit = max(z, statistik urutan |t*| plasebo setara p < α), interval ±crit·SE, p = max(p plasebo, p normal) (p < α ⇔ interval tidak memuat nol), q BH, interval praregistrasi & boot_ratio dibawa → artefak `national_calibrated` (tambahan, D-129); + baris PT = baris e / γ(h), p & q sama (D-163).
- `province_calibrated` · ✔ · D-163 (U107): deviasi provinsi δ mentah (e & w, h kunci), null |t*| dipool antarprovinsi per sel, interval ±crit·SE, p = max(plasebo, normal), q BH per sel atas provinsi, δ tersusut & boot_ratio dibawa → artefak `province_calibrated`.

#### src/evaluation/regimes.py
(konstanta `CONSUMER_INSTRUMENTS` = HET, HAP, HAP_konsumen)
- `regulation_changes` · ✔ · tanggal penetapan/perubahan harga acuan konsumen per komoditas (in_scope, bertanggal, bukan unverified, dalam periode).
- `regime_table` · ✔ · rezim per komoditas: awal periode .. sebelum perubahan pertama, lalu antar perubahan s.d. freeze.
- `regime_profiles` · ✔ · E2: β_e & ω nasional per rezim (h kunci; jendela data utuh dalam rezim); interval ±crit·SE, crit = max(1,96; p95 |t*| plasebo geser-melingkar), + p_placebo, q_fdr (paralel joblib) → artefak `regime_profiles` (D-124, D-127).

#### src/evaluation/robustness.py
(konstanta `TIER1` 6 cek, `TIER2` 4 cek)
- `fx_decomposition` · ✔ · de = a + b·d_dxy + ε → de_global (fitted) & de_idr (ε); attrs a, b, r2.
- `tier1` · ✔ · 6 cek wajib vs baseline (h 4/8/12, driver e & w; sub-sampel lewat jendela [t−L−1, t+h]; LP bulanan); 21 dtk lokal.
- `lp_implied_paths` · ✔ · respons LP nasional terimplikasi per jendela: Σ β_e(h−j)·de + Σ ω(h−j)·dw.
- `validation` · ✔ · V4 (kelebihan event di atas median plasebo vs implikasi LP, per komoditas × h kunci) + V2 (episode tahun freeze; rasio MAE Task 4 subset case_study bila forecast_eval ada).
- `tier2` · ✔ · opsional (dipotong pertama): varian & komposit harga dunia alternatif, agregasi observasi terakhir, Kendall dengan ordinal jalur (`PATH_ORDINAL`) + baseline τ `import_ratio_direct`, keterpencilan alternatif (`REMOTENESS_ALTERNATIVES`, meta-regresi gabungan CR2), outcome Bapanas bulanan; setiap cek jalan bila inputnya ada (D-116).

### 9.6 Mesin statistik (WP-12, semua ✔ dan dites di `tests/test_stats.py`)

#### src/stats/regression.py
- `ols_cluster` · ✔ · OLS + SE cluster CR1; buang baris NaN di y/X dan baris dengan grup kosong (D-119); return OLSResult(beta, se, n_obs, n_clusters, resid).
- `newey_west_lrv` · ✔ · varians jangka panjang kernel Bartlett.
- `diebold_mariano` · ✔ · DM dua sisi HAC (lag h−1) + koreksi HLN; stat > 0 = kandidat lebih akurat.

#### src/stats/resampling.py
- `moving_block_indices` · ✔ · indeks minggu dari blok berurutan (Künsch).
- `circular_shift` · ✔ · pergeseran s ∈ [min_shift, n − min_shift].
- `placebo_windows` · ✔ · sampel awal jendela plasebo dari kandidat.

#### src/stats/meta.py
- `dersimonian_laird` · ✔ · HetResult(mu, tau2, Q, I2, k).
- `reml_tau2` · ✔ · τ² REML (Fisher scoring).
- `eb_shrink` · ✔ · μ + τ²/(τ²+s²)·(est − μ); τ²=0 → semua μ.
- `bh_fdr` · ✔ · q-value Benjamini–Hochberg.
- `holm` · ✔ · p terkoreksi Holm step-down (NaN dikeluarkan dari keluarga; pemanggil yang menentukan pengisian).

### 9.7 Pipelines (orkestrasi; satu modul = satu notebook = satu perintah CLI)

#### src/pipelines/stage0.py
- `run` · ✔ · snapshot → varian → panel → kelayakan → penggerak → harga dunia → episode → tabel tim → panel wilayah → MDE → QA.

#### src/pipelines/task1.py
- `run` · ✔ · REQUIRES drivers/world/episodes/region/eligibility; profil wilayah + (bila panel provinsi) nasional, deviasi, bootstrap, plasebo, EB.

#### src/pipelines/task2.py
- `run` · ✔ · heterogenitas vs plasebo → matriks fitur → pilih k → Ward → stabilitas → partisi → struktur tertanam.

#### src/pipelines/task3.py
- `run` · ✔ · Kendall (selalu) + meta-regresi, FE, H2 `asymmetry`, dan E2 `regime_profiles` (bila panel provinsi; E2 juga butuh `regulation` & harga dunia).

#### src/pipelines/task4.py
- `run` · ✔ · rolling_predictions → forecast_preds.parquet → evaluate + ablation.
- `run_direction` · ✔ · EKSPLORATIF (D-141): klasifier arah C1/C2 → `direction_preds` (`kagami task4 --direction`); uji resmi tidak berubah.
- `run_direction_tuned` · ✔ · EKSPLORATIF (D-145): klasifier arah tuned C1t/C2t → `direction_tuned_preds` (`kagami task4 --direction-tuned [C1t C2t]`).
- `run_deep` · ✔ · EKSPLORATIF (D-142): PatchTST, TSMixer ± kurs, TimesFM 3.0 ± kurs → `deep_preds` (`kagami task4 --deep [model ..]`).

#### src/pipelines/robustness.py
- `run` · ✔ · tier1 + validation (+ tier2 bila diminta).
- `tier2_inputs` · ✔ · siapkan input Tier 2 dari data mentah & artefak (`pihps_daily`, `exposure`, `province_features` + `ln_km_jakarta`); sumber yang tidak ada dilewati.

#### src/pipelines/package.py
- `collect_submission` · ✔ · file zip juri + daftar artefak ship yang hilang.
- `submission` · ✔ · `dist/kagami_submission.zip` (gagal bila ada artefak ship hilang, kecuali allow_missing).
- `code_bundle` · ✔ · `dist/kagami_code.zip` (kode, configs, data/reference, notebook) untuk Kaggle/Colab.
- `raw_bundle` · ✔ · `dist/kagami_raw_PRIVATE.zip` (isi raw_dir + checksums) untuk dataset Kaggle PRIVAT.

### 9.8 Viz

#### src/viz/plots.py
- `response_curve` · ✔ · kurva respons h 0..12 + pita interval; tanpa interval → tanpa pita; provinsi berlabel deviasi (app hal. 2, nb01).
- `region_map` · ✔ · peta Indonesia 7 wilayah / 34 provinsi dari `data/reference/indonesia_provinces.geojson`, sumbu kartesius (offline, tanpa topojson CDN), titik ibu kota = target klik (app hal. 2, D-134).
- `silhouette_threshold` · ✔ · silhouette maksimum per k vs ambang p95 plasebo, keputusan k (app hal. 3).
- `robustness_forest` · ✔ · V18: estimasi tiap cek Tier 1/2 vs estimasi utama per komoditas × penggerak × h; e ikut komponen dolar global / khusus rupiah; nilai estimasi utama di subjudul (bukan anotasi garis, D-172) (app hal. 6).
- `asymmetry_plot` · ✔ · V19: β⁺ (`e_pos`) vs β⁻ (`e_neg`) nasional per h kunci + uji selisih H2 di subjudul (app hal. 2).
- `scenario_change` · ✔ · perubahan harga (%) = 100·(exp(PT·ln(1 + x/100)) − 1) untuk pelemahan x%; rumus tabel batas Rupiah findings (app hal. 5, D-169).
- `scenario_paths` · ✔ · jalur skenario `scenario_change` untuk x ∈ shocks_pct, pita hanya bila interval ada; judul opsional (app hal. 5).
- `fx_drivers` · ✔ · kurs JISDOR mingguan (Rp per dolar AS) + arsiran episode, segitiga berketerangan, sorotan satu episode, `start` memotong awal (app hal. 10, nb00).
- `status_share` · ✔ · kelengkapan data mingguan per komoditas, batang horizontal berlabel pembaca (teramati, rangkaian harga identik, ...) (app hal. 11, nb00).
- `episode_fan` · ✔ · D-175: kipas episode nasional, satu garis per episode 0–12 minggu di atas pita 95% jendela tanpa episode (rerata placebo_lo/hi), sorotan satu episode (app hal. 2 & 10).
- `episode_fan_grid` · ✔ · D-175: kipas episode semua komoditas, panel berskala sendiri, 5 kolom desktop / 2 kolom ponsel (app hal. 10).
- `price_trend` · ✔ · D-175: harga eceran mingguan provinsi vs median 34 provinsi + arsiran episode, sumbu Rupiah (app hal. 11).
- `coassign_heatmap` · ✔ · matriks ko-asignasi (app hal. 3, nb02).
- `recovery_curve` · ✔ · batas deteksi struktur tertanam (app hal. 3, nb02).
- `forecast_ratios` · ✔ · rasio MAE vs M1 per horizon (panel); margin atas + ruang judul panel (app hal. 9, nb04).
- `forest` · ✔ · forest plot estimasi + interval; `x_range` memotong sumbu dengan segitiga tepi untuk rentang yang melewati batas; ponsel: label dibungkus & baris lebih tinggi (app beranda, hal. 2/4; nb03, nb05).
- `sensitivity_heatmap` · ✔ · peta kepekaan respons kumulatif per komoditas × unit dari `response_features`; `metric_label` untuk judul (app hal. 2).
- `cluster_sizes` · ✔ · jumlah provinsi per klaster + stabilitas Jaccard, klaster lemah ditandai (app hal. 3).
- `run_durations` · ✔ · batang waktu eksekusi per run eksekusi berlabel tahap, warna = status; tahap tanpa eksekusi di subjudul (app hal. 7).
- `metric_trend` · ✔ · satu metrik antar run sebuah tahap; tidak berlaku/gagal ditandai (app hal. 7).
- `pipeline_graph` · ✔ · graf dependensi tahap dari REQUIRES/OPTIONAL, warna = status tahap (eksekusi vs evaluasi-saja, output tidak sinkron), tanda basi; angka jumlah artefak di antara lapisan, tidak di kolom simpul (D-172) (app hal. 7).
- `confusion_matrix` · ✔ · confusion matrix arah perubahan Task 4 (baris = aktual, warna = porsi baris) dari log evaluasi (app hal. 7, D-139).

#### src/viz/style.py
(konstanta palet `BLUE`/`ORANGE`/`AQUA`/`NEUTRAL`, `DIVERGING`, `SEQUENTIAL`, `STATUS_COLORS`, `MODEL_COLORS`; label `DRIVER_LABELS`,
`LEVEL_LABELS`, `MODEL_LABELS`, `SUBSET_LABELS`, `CHECK_LABELS`, `PATH_LABELS`, `FEATURE_LABELS` (D-170), `UNIT_LABELS`, `AXIS_LABELS` (D-171:
kosakata pembaca, mis. "Kurs rupiah", "% per 1% pelemahan rupiah", "Model dasar"); D-134. Bukan fungsi grafik → tidak diwajibkan dipanggil app/notebook.)
- `month_year` · ✔ · tanggal → "Mar 2020" (bulan Indonesia singkat, konstanta `MONTHS`); NaT → "tidak tersedia".
- `fmt_num` · ✔ · angka format Indonesia (desimal koma, ribuan titik, minus tipografis); NaN → "tidak tersedia".
- `dm_summary` · ✔ · kalimat uji DM dengan arah: tanda DM, "lebih/kurang akurat", p dua sisi, p satu sisi untuk "model lebih akurat"; nama model bisa diganti (app hal. 9, D-169, D-171).
- `fmt_interval` · ✔ · "lo s.d. hi" format Indonesia atau "interval tidak tersedia".
- `detection_status` · ✔ · lencana terdeteksi / tidak terdeteksi / interval tidak tersedia (NaN).
- `rgba` · ✔ · hex → rgba() untuk pita transparan.
- `set_wrap` · ✔ · D-172: lebar bungkus (judul, subjudul) grafik untuk thread skrip ini (`WRAP` ContextVar; app: ponsel 34/50, desktop None/72).
- `wrap_lines` · ✔ · bungkus teks per kata menjadi baris ≤ lebar karakter (`\n` = baris baru).
- `finish` · ✔ · tata letak seragam: judul (satu baris, kecuali `\n` eksplisit untuk grafik kolom sempit, D-176; ponsel dibungkus), subjudul dibungkus per kata (desktop 72 karakter), pemisah angka Indonesia, legenda di bawah plot (ponsel: dikunci di dasar wadah, judul sumbu dibungkus, tinggi + selisih margin).

### 9.9 Pelacakan eksekusi & log evaluasi (WP-36, D-137; rincian `docs/TRACKING.md`)

#### src/tracking/schemas.py
(dataclass `ArtifactRef`, `Metric` (status ok | not_applicable | failed; selain ok wajib `reason`), `RunRecord`, `ErrorRecord`,
`EvaluationRecord`; `SCHEMA_VERSION`)
- `to_dict` · ✔ · dataclass → dict siap JSON.
- `run_from_dict` · ✔ · dict JSON → RunRecord (kunci tak dikenal diabaikan).
- `metric_from_dict` · ✔ · dict JSON → Metric.

#### src/tracking/metrics.py
- `ok` · ✔ · Metric berhasil; NaN/inf otomatis `failed`.
- `na` · ✔ · Metric `not_applicable` + alasan.
- `failed` · ✔ · Metric `failed` + alasan.
- `clustering_metrics` · ✔ · n_clusters, ukuran, WCSS, silhouette/DB/CH hanya bila 2 ≤ k ≤ n − 1 dan tanpa NaN.
- `regression_metrics` · ✔ · MAE, MSE, RMSE, R², R² vs ramalan nol, MAPE (tidak berlaku bila ada y = 0); pasangan NaN dibuang & dicatat.
- `direction_metrics` · ✔ · diagnostik arah (D-139): tanda ramalan regresi vs tanda y → accuracy, baseline mayoritas, balanced acc.,
  precision/recall/F1 naik & turun, F1 makro, MCC, ROC-AUC, PR-AUC, confusion; y = 0 / ramalan = 0 dikeluarkan & dicatat; M0 / satu kelas → tidak berlaku.
- `data_profile` · ✔ · baris, kolom, sel kosong, memori (MB) sebuah DataFrame.
- `interval_consistency` · ✔ · porsi baris dengan p < α ⇔ interval tidak memuat nol + jumlah ketidakcocokan.
- `share` · ✔ · porsi True (NaN dibuang).
- `bootstrap_p` · ✔ · p dua sisi bootstrap persentil terhadap nilai acuan (konsisten dengan interval persentil; D-143).
- `origin_block_indices` · ✔ · matriks indeks bootstrap blok bergerak atas origin berurutan (D-140).
- `direction_bootstrap` · ✔ · interval 95% metrik arah (akurasi, selisih vs baseline mayoritas, balanced acc., F1 makro, MCC, ROC-AUC, PR-AUC) dengan bootstrap blok origin; unit = origin, bukan baris (D-140).
- `direction_segment_table` · ✔ · metrik arah + MAE per segmen (komoditas, jalur, grup H5, kekakuan harga) × model, selisih vs baseline dengan interval & penilaian (D-140).
- `paired_accuracy_diff` · ✔ · selisih akurasi arah A − B pada baris yang sama + interval bootstrap blok origin berpasangan (D-141).
- `selective_accuracy` · ✔ · prediksi selektif: per origin hanya baris paling yakin |p − 0,5| (cakupan q) → cakupan, akurasi, baseline, F1 makro (D-141).
- `feature_health` · ✔ · fitur konstan (tersusut habis), dimensi efektif, sel kosong, pasangan redundan |r| ≥ 0,95 (D-140).

#### src/tracking/lineage.py
(kelas `Recorder` = pengamat io: input di-hash saat dibaca, output di akhir run)
- `location_label` · ✔ · out_dir | artifact_dir | root | other (path absolut tidak dicatat).
- `artifact_ref` · ✔ · ArtifactRef: sha256, bytes, (output) baris/kolom/sel kosong/memori.
- `producer_index` · ✔ · sha256 → run sukses terakhir yang menulis file itu.
- `link_parents` · ✔ · isi producer_run_id input → daftar run induk.
- `raw_snapshot_id` · ✔ · `raw:<12 heks>` dari pasangan (file, sha256) checksums; kolom waktu tidak ikut.
- `dataset_id` · ✔ · `raw_snapshot_id` / warisan induk / `in:<hash input>`.
- `config_hashes` · ✔ · sha256 params.yaml & commodities.yaml.
- `git_info` · ✔ · (commit, branch) dari .git tanpa menjalankan git.
- `peak_rss_mb` · ✔ · memori puncak proses (psutil/resource; None bila tak ada).
- `python_version` · ✔ · versi Python.
- `code_hash` · ✔ · sha256 isi `src/**/*.py`, `app/**/*.py`, `configs/*.yaml` (path relatif) → sidik jari kode (D-140).
- `git_dirty` · ✔ · kode/config berubah tanpa commit (`git status --porcelain`, baca-saja); None tanpa repo/git.
- `environment_versions` · ✔ · versi Python, numpy, pandas, scipy, scikit-learn.

#### src/tracking/registry.py
(`TaskSpec`, `TASKS` 7 tahap, `ORDER`, `NOT_APPLICABLE_FAMILIES`)
- `task_params` · ✔ · bagian params.yaml relevan tahap + seed.
- `stage_requires` · ✔ · REQUIRES/OPTIONAL setiap pipeline (impor lokal).
- `dependency_edges` · ✔ · sisi produsen → konsumen per artefak (wajib/opsional) + snapshot → stage0.
- `stage_outputs` · ✔ · artefak registry milik tahap.

#### src/tracking/store.py
- `now_iso` · ✔ · waktu UTC ISO (mikrodetik, agar run dalam detik yang sama tetap terurut).
- `write_record` · ✔ · tulis `out_dir/logs/<jenis>/<id>.json` mode eksklusif (FileExistsError bila ada; tidak menimpa).
- `log_dirs` · ✔ · folder `logs/` di setiap read_dirs.
- `load_runs` · ✔ · semua RunRecord urut waktu (lokasi baca pertama menang).
- `load_evaluation` · ✔ · EvaluationRecord sebuah run atau None.
- `load_errors` · ✔ · log galat per run.
- `load_pipelines` · ✔ · ringkasan `kagami all`.
- `runs_table` · ✔ · riwayat satu baris per run + ringkasan evaluasi.
- `metrics_table` · ✔ · metrik long (run, tahap, kelompok, nama, nilai, status, alasan, konteks).
- `compare_runs` · ✔ · metrik + delta vs run acuan, beda parameter/lingkungan, sha256 input/output per run.
- `latest_runs` · ✔ · run terakhir per tahap.
- `staleness` · ✔ · input run terakhir yang file-nya kini berbeda (hasil basi); beda ujung baris CRLF ↔ LF saja tidak dihitung (D-170).
- `artifact_sync` · ✔ · lineage OUTPUT: setiap artefak = hasil run eksekusi terakhir (sinkron) / versi lain (tidak sinkron) / hanya dievaluasi / tanpa log (D-140); hash teks dibandingkan juga dalam versi LF & CRLF (checkout git di Linux, D-170).
- `stage_states` · ✔ · status tahap: dieksekusi / output tidak sinkron / hanya dievaluasi / gagal / belum ada run (D-140).

#### src/tracking/assessment.py
(`LABELS`, `COLUMNS`, `RULES`; lapis kedua D-140: status hitung ≠ kualitas hasil)
- `assess` · ✔ · penilaian satu metrik terhadap acuan eksplisit (peluang, baseline mayoritas, α + uji binomial, rasio 1 + DM, p95 plasebo, ambang MDE, nol integritas) → better / worse / inconclusive / expected / review / info + interpretasi.
- `assess_table` · ✔ · tambah kolom reference, reference_label, ci_low, ci_high, assessment, interpretation ke metrics_table (dihitung saat dibaca; berlaku juga untuk log lama), lalu `apply_multiplicity`.
- `apply_multiplicity` · ✔ · BH per keluarga per run (beda berpasangan, metrik arah vs acuan, rasio MAE eksploratif): q ≥ 0,05 → belum terbukti; kolom family, p_value, q_value (D-143).

#### src/tracking/evaluators.py
(`EVALUATORS`; hanya membaca artefak; artefak hilang → not_applicable + alasan; galat bagian → failed)
- `evaluate_snapshot` · ✔ · jumlah file, sumber, MB.
- `evaluate_stage0` · ✔ · porsi status sel, kelayakan, episode, sd(de), MDE PT(8), lonjakan QA.
- `evaluate_task1` · ✔ · jumlah estimasi, porsi interval tidak memuat nol, positif palsu plasebo, boot_ratio, event study; R² = tidak berlaku.
- `evaluate_task2` · ✔ · H0-Het, silhouette per k vs p95, validitas partisi terpilih, DB/CH kandidat, cek silhouette dihitung ulang, batas deteksi, ARI.
- `evaluate_task3` · ✔ · Kendall, meta-regresi, H2, E2, terkalibrasi + konsistensi p–interval.
- `evaluate_task4` · ✔ · MAE/RMSE/rasio/DM resmi, galat dihitung ulang dari forecast_preds (cek silang MAE), diagnostik arah (D-139) + interval bootstrap blok origin & tabel per segmen (D-140), ablation + cek M2_nofx = M1.
- `evaluate_robustness` · ✔ · baris per tier, porsi baseline dalam interval, V4.
- `evaluate` · ✔ · dispatcher per tahap (tahap tanpa evaluator → not_applicable).

#### src/tracking/logger.py
- `enabled` · ✔ · False bila env `KAGAMI_TRACKING` = 0/false/no/off.
- `new_id` · ✔ · `<prefix>-YYYYmmddTHHMMSSZ-<6 heks>`.
- `run_tracked` · ✔ · jalankan fungsi tahap sebagai run tercatat; gagal → log galat lalu exception dilempar ulang; bertingkat = satu run.
- `tracked` · ✔ · dekorator `pipelines.<tahap>.run`.
- `pipeline` · ✔ · konteks satu pipeline_id (`kagami all`) → logs/pipelines.
- `evaluate_existing` · ✔ · evaluasi artefak yang ada tanpa menjalankan ulang (duration_s = None).

---

## 10. Data

### 10.1 Sumber (rincian: `docs/DATASETS.md`)

| Kunci | Isi | Cakupan | Peran | Redistribusi |
|---|---|---|---|---|
| `pihps` | PIHPS v2 merged, 34 prov × 31 baris (10 komoditas + 21 varian), harian | 2017-03-28..2026-11-19 | outcome | tidak |
| `pihps_wholesale` | PIHPS pedagang besar (grosir) harian, format sama dengan `pihps` (`optional`, pilot D-150) | 2017-03..2026-11-19 | fitur eksploratif Task 4 | tidak |
| `pihps_producer` | PIHPS harga produsen harian (`price_type_id=4`), format sama dengan `pihps` (`optional`, pilot D-151; cakupan provinsi tidak lengkap) | 2018-03..2026-11-19 | fitur eksploratif Task 4 | tidak |
| `ditjenpkh_sijagung` | SIJAGUNG stok & pembelian jagung pabrik pakan per wilayah, bulanan (`optional`, audit D-160) | 2019-01..2026-08 | audit sinyal ayam/telur (gagal) | tidak |
| `pihps_city` | PIHPS harian per kabupaten/kota, 110 kota (`optional`, pilot D-158) | 2017-03-27..2026-11-25 | fitur eksploratif Task 4 (breadth pasar) | tidak |
| `nasa_power` | NASA POWER cuaca harian (hujan, suhu) di centroid 34 provinsi (`optional`, pilot D-157) | 2016-01-01..2026-11-20 | fitur eksploratif Task 4 (cuaca sentra) | ya (atribusi) |
| `jisdor` | JISDOR harian | 2013-05-20..2026-11-18 | penggerak 1 | tidak |
| `pinksheet` | World Bank CMO bulanan USD | 1960-01..2026-10 | penggerak 2 | ya (CC BY) |
| `brent` | FRED DCOILBRENTEU | 2013..2026-11-11 | kontrol | ya |
| `dollar_index` | FRED DTWEXBGS | 2013..2026-11-13 | robustness | ya |
| `faostat_sua` | FAOSTAT SUA Asia | 2010..2023 | rasio impor | ya (CC BY) |
| `bps_import_monthly` | impor HS8 bulanan **v2** (111 kode, +bawang putih 070320) | 2023-01..2026-09 | cek silang | tidak |
| `bps_import_annual` | 5 xlsx exim tahunan (Totals = USD) | 2023..2026 | QA | tidak |
| `comtrade_import` | UN Comtrade HS4/HS6 bulanan (tanpa kedelai 1201) | 2017-01..2022-12 | rasio impor pra-2023 | tidak |
| `comtrade_import_2023` | UN Comtrade bulanan 15 kode konkordansi (API publik preview, diambil 2026-11-23, `optional`) | 2023-01..2023-12 | QA tumpang tindih konkordansi (U102) | tidak |
| `konkordansi_hs` | Comtrade HS2017/2022 → HS8 BPS + keyakinan (buatan tim) | statis | jembatan impor (WP-07) | ya |
| `bapanas_panel` | Panel Harga Bapanas bulanan, 38 prov | 2022-01..2026-10 | cek bias / Tier 2 | tidak |
| `bapanas_het_settings` | riwayat setting HET/HAP | 2024..2026 | regulasi | tidak |
| `padi_2024`, `padi_2025` | produksi padi GKG per provinsi (38) | 2024, 2025 | kecukupan beras | tidak |
| `konsumsi_beras` | konsumsi beras RT kg/kap/tahun | 2023..2025 | kecukupan beras | tidak |
| `neraca_beras` | neraca beras nasional | 2023..2026 | cek silang | tidak |
| `het_hap_current` | HET/HAP berlaku (buatan tim; revisi 20 Nov, 30 baris) | per 2026-11-19 | regulasi | ya |
| `regulation_history` | riwayat HET/HAP/HPP (buatan tim; revisi 20 Nov, 23 baris) | 2020..2025 | regulasi (E2) | ya |
| `hortikultura_produksi` | produksi bawang merah/putih, cabai besar/rawit per provinsi (ATAP Kementan) | 2020..2024 | rasio impor bawang putih, kecukupan | tidak |
| `jarak_hub` | jarak ibu kota ke Jakarta/Surabaya/Makassar (buatan tim, 38 prov) | statis | cek silang dist_hub_km | ya |
| `penduduk` | penduduk provinsi 2025 BPS (`optional`, tabel BPS diperbarui 2 Mei 2025, D-123) | 2025 | kebutuhan beras → rice_sufficiency (U14) | tidak |
| `n_kota` | kota sampel pasar tradisional PIHPS per provinsi (situs PIHPS 2026-11-21, `optional`) | 34 prov, 110 kota | n_kota (U15) | ya |
| `gkg_beras` | faktor konversi GKG → beras untuk konsumsi pangan (rilis BPS, `optional`) | 2024, 2025 | rice_sufficiency (U21) | ya |

Menunggu diunggah (opsional, U103): `bapanas/panelharga_konsumen_kabkota_snapshot_2026-10.csv`. Versi lama: `data/raw/_superseded/` (DATASETS.md).

### 10.2 Fakta data yang sudah diverifikasi
- Panel mingguan: 157.760 sel = 34 × 10 × 464 minggu (2018-01-01..2026-11-16). `pihps_daily` 800.642 hari teramati.
- Status sel: observed 49,2% · carry_forward 49,2% · missing 1,0% · short 0,6%.
- `carry_forward` sangat tinggi untuk komoditas diatur (beras 92%, daging sapi 90%, gula 85%, minyak goreng kemasan 87%)
  → bukan artefak kode; jangan dipakai sebagai filter (U22). Status ini = rangkaian harga teramati identik ≥ 5 hari, bukan bukti
  kekakuan: FAQ PIHPS menyatakan harga hari sebelumnya dipakai saat pasar tidak beroperasi, dan keduanya tidak dapat dibedakan (D-169).
- FAQ PIHPS (dibaca 2026-11-27): pencacahan Senin–Jumat 09.00–11.00 WIB, terbit 13.00 WIB, revisi "sampai dengan hari berikutnya" (U110),
  2 pasar/kota, 2 pedagang/komoditas, 82 kota sampel IHK; daftar kota situs PIHPS & `pihps_city` = 110 kota (dipakai `n_kota`).
- Kelayakan: 337/340 layak. Tidak layak: cabai_rawit Aceh (1), Sumbar (3), Kepri (5) → cabai rawit dianalisis 31 provinsi.
- Penggerak 2018–2026: sd(de) 0,0082; 259 minggu depresiasi / 200 apresiasi; de maks +0,063 (Mar 2020);
  corr(de, d_dxy) 0,52; 5 minggu tanpa fixing JISDOR (semua cuti Lebaran) diisi level sebelumnya (D-025).
- Episode (`episodes`): 13 episode 2018–2026, 61 minggu; terbesar Mar–Mei 2020 (Σ 0,185). `panel_weekly_region` 32.480 baris;
  minggu 2022-05-02 (Idulfitri) kosong di 5 wilayah → NaN.
- `world_prices_weekly`: 3.096 baris (6 komoditas × 516 minggu); NaN hanya 3 minggu Nov 2026 (Pink Sheet Nov belum rilis).
- FAOSTAT SUA tidak memuat bawang putih kering (hanya "Green garlic") → U5; pengganti: `hortikultura_produksi` + impor 070320.
- `hortikultura_produksi`: total nasional cocok; 148/152 nilai 2023 sama dengan BPS (4 selisih pembulatan); ATAP berhenti 2024.
- Konkordansi HS: perubahan HS2017→HS2022 hanya 0709.59. Uji tumpang tindih Comtrade vs BPS 2023 (U102, D-133): 14/15 kode cocok persis (rasio nilai 1,000, korelasi bulanan 1,000; termasuk bawang putih 070320 USD 648,6 juta); 1511 minyak sawit 0,944 (USD 1,2 juta, subpos HS8 tidak lengkap, tidak dipakai rasio impor).
- Pink Sheet tim = rilis resmi 3 Nov 2026 (identik byte-per-byte; `Mismatch Details` bagian file resmi; U101 🟢).
  World Bank merevisi angka historis antar rilis → catat tanggal rilis setiap snapshot.
- Snapshot PIHPS pra-merge (`pihps_v1`) dipensiunkan ke `data/raw/_superseded/bi_pihps/` (D-102): inventaris tim menandainya rusak.
- Kolom `Totals` exim tahunan BPS = USD (Σ bulanan 2023 / Totals = 1,000) → D-019.
- Bapanas memakai ejaan "D.I Yogyakarta" (alias sudah ada).

### 10.3 Keanehan mentah yang harus selalu diingat
- PIHPS v2 menaruh varian hasil merge di **akhir file** (Aceh, Riau, Kepri, Lampung, Bali, Gorontalo, Sulsel) →
  jangan pernah menentukan grup dari urutan baris (D-022).
- "Cabai Merah Keriting " ber-spasi akhir → selalu `norm_name`.
- Lonjakan satu hari (contoh: Papua, Beras level 1, 2017-07-03: 29.750 lalu 9.500) → WP-10 menandai, tidak menghapus.
- Tanggal 2026-11-19 di PIHPS sebagian kosong.
- Pink Sheet: nama seri ber-spasi/`**` ("Beef **", "Rice, Thai 5% "), "…" = kosong; sheet "Mismatch Details" abaikan.
- JISDOR Excel: header di baris 5, angka format Indonesia "9.760,00", tanggal "5/20/2013 12:00:00 AM".
- BPS padi 2024: 4 baris judul + nama UPPERCASE; 2025 header normal; keduanya 38 provinsi + "INDONESIA"; produksi GKG.
- Bapanas 38 provinsi → pemetaan ke 34 lewat `province_aliases.csv` (pemekaran Papua → induk).
- Endpoint PIHPS di MANIFEST: `WebSite/TabelHarga/GetGridDataDaerah` → status "unduh resmi" belum dipastikan (U19).

### 10.4 Tabel buatan tim (`data/reference/`, CC BY 4.0)
- `region_crosswalk.csv`: province_id, province, region (7), capital, lat, lon, het_zone_beras (1/2/3), java.
  Kalsel = Banjarmasin, Malut = Sofifi; koordinat ±0,01°.
- `province_aliases.csv`: alias ejaan BPS/Bapanas + pemekaran Papua.
- `indonesia_provinces.geojson` (D-134): geometri 34 provinsi untuk peta app, 98 KB; **ODbL** (© OpenStreetMap contributors via
  geoBoundaries), bukan CC BY. Ikut zip juri & bundle (`package.CODE_GLOBS`).
- Hasil WP-07 (`stage0`, 2026-11-21): `concordance.csv`, `exposure.csv`, `regulation.csv`, `province_features.csv`
  (rice_sufficiency 2025: 0,001 DKI .. 3,27 Sulsel; n_kota 1..12; |r| antar fitur Z(r) ≤ 0,34).

### 10.5 Asal file
File mentah dipindah 2026-11-20 dari `data/` ke `data/raw/<sumber>/` (sebagian diganti nama); pemetaan nama asli ada
di `docs/DATASETS.md` §Asal file. Isi file tidak pernah diubah (hash di checksums.csv).

---

## 11. Desain analisis ringkas

### 11.1 Komoditas (`configs/commodities.yaml`)

| id | Varian representatif | Peran | Grup fokus | Jalur | Padanan Pink Sheet | HS |
|---|---|---|---|---|---|---|
| beras | Beras Kualitas Medium I | other | – | direct_import | Rice, Thai 5% | 1006 |
| bawang_putih | Bawang Putih Ukuran Sedang | focus | bawang_putih | direct_import | – | 070320 |
| gula_pasir | Gula Pasir Lokal | focus | gula_pasir | direct_import | Sugar, world | 1701 |
| minyak_goreng | Minyak Goreng Kemasan Bermerk 1 (D-023) | focus | minyak_goreng | export_parity | Palm oil | 1511, 1517 |
| daging_ayam | Daging Ayam Ras Segar | focus | pakan | imported_input | 0,6 Maize + 0,4 Soybean meal | 0207, 1005, 2304 |
| telur_ayam | Telur Ayam Ras Segar | focus | pakan | imported_input | 0,6 Maize + 0,4 Soybean meal | 0407, 1005, 2304 |
| daging_sapi | Daging Sapi Kualitas 1 | focus | daging_sapi | direct_import | Beef | 0102, 0201, 0202 |
| bawang_merah | Bawang Merah Ukuran Sedang | control | – | domestic | – | 070310 |
| cabai_merah | Cabai Merah Keriting | control | – | domestic | – | 070960, 090421 |
| cabai_rawit | Cabai Rawit Merah | control | – | domestic | – | 070960, 090421 |

Varian, bobot pakan, dan grup fokus FINAL sejak G6 2026-11-20 (D-011, D-012, D-013, D-109; minyak goreng D-023).

### 11.2 Wilayah
34 provinsi lama (urutan & id PIHPS). 7 kelompok: Sumatra (1–10), Jawa (11–16), Bali–Nusa Tenggara (17–19),
Kalimantan (20–24), Sulawesi (25–30), Maluku (31–32), Papua (33–34). Hub keterpencilan: DKI Jakarta, Jawa Timur
(Surabaya), Sulawesi Selatan (Makassar). Zona HET beras (Kepbadan 299/2025): 1 = Jawa, Lampung, Sumsel, Bali, NTB,
Sulawesi; 2 = Sumatra lain, NTT, Kalimantan; 3 = Maluku, Papua.

### 11.3 Parameter kunci (`configs/params.yaml`; jangan disalin sebagai konstanta di kode)

| Kunci | Nilai |
|---|---|
| seed | 20261121 |
| period.start / start_fallback / freeze / driver_buffer_weeks | 2018-01-01 / 2020-01-06 / 2026-11-21 / 52 |
| calendar.idulfitri | 2017-06-25, 2018-06-15, 2019-06-05, 2020-05-24, 2021-05-13, 2022-05-02, 2023-04-22, 2024-04-10, 2025-03-31, 2026-03-20 |
| calendar.idulfitri_window | [−6, 4] |
| calendar.breaks | jisdor_method_change 2021-04-05; padg_7_2026 null (U3) |
| calendar.exclusions | covid 2020-03-01..2020-06-30; brent_extreme_abs_monthly_logchg 0,25 |
| weekly | short_week_days 2; carry_forward_run_days 5 |
| eligibility | max_missing_share 0,20; max_gap_weeks 8; min_year_coverage 0,70 |
| episodes | cum_depreciation 0,03; window_weeks 8 |
| lp | horizons 0..12; lags 4; lags_robust [2,4,8]; key_horizons [4,8,12] |
| inference | bootstrap_B 499; bootstrap_B_nonfocus 199; block_weeks 13; placebo_R 499; placebo_min_shift_weeks 52; event_placebo_windows 499; fdr_q 0,05 |
| shrinkage | tau2_method DL; tau2_check REML |
| power | α 0,05; power 0,80; mde_threshold_pt8 0,5; mde_commodities [bawang_putih, gula_pasir, minyak_goreng] |
| clustering | k_range 1..6; feature_horizons [4,8,12]; silhouette_placebo_pct 95; kmeans_restarts 50; jaccard_weak 0,6; planted_deltas 0,1..0,5; planted_reps 200 |
| association | hubs [DKI Jakarta, Jawa Timur, Sulawesi Selatan]; max_features 3; import_ratio_years [2018, 2023] (D-121) |
| forecast | horizons [4,8]; first_origin 2021-01-04; origin_step_weeks 4; large_move_pct 80; ridge_alphas [0.1,1,10,100]; feature_changes_weeks [1,4,8]; hgb {max_iter 300, lr 0,05, max_leaf_nodes 31}; bps_release_lag_days 45; h5_correction holm; run_m3 true (D-121) |
| scenario | shocks_pct [1,3,5] |

### 11.4 Notasi
i komoditas, r provinsi, t minggu ISO, h horizon 0..12. p = log harga; y^{(h)} = p_{t+h} − p_{t−1};
e = log JISDOR rerata mingguan; de = Δe; w = log harga dunia padanan dalam rupiah; dw = Δw; b = log Brent.
β(i,h) respons kurs; ω(i,h) respons harga dunia; γ(h) respons kurs pada dirinya; PT = β/γ; δ(i,r,h) deviasi provinsi;
τ² varians antar-provinsi; I² porsi variasi; ρ̄ rerata korelasi deviasi antar komoditas.

---

## 12. Metode per task (ringkas; rumus lengkap `docs/METHODS.md`)

### Tahap 0 (notebook 00, ringan)
- WP-06 episode: Σ de 8 minggu ≥ 3%, gabung tumpang tindih; daftar episode harus memuat 2018, 2020, 2022, 2024–25,
  2026 bila ada; catat jumlahnya. Lalu `mark_episode_weeks` → kolom `episode` → baru `drivers_weekly` bisa ditulis.
- WP-07 tabel tim: input baru `hortikultura_produksi`, `konkordansi_hs`, `jarak_hub` (D-101); setiap angka punya `source`; tanggal regulasi tak terverifikasi tetap `unverified`; populasi provinsi
  belum ada (U14) → `rice_sufficiency` NaN bila tak terselesaikan; konversi GKG→beras didokumentasikan (U21).
- WP-08 panel wilayah: hanya seri eligible; indeks log relatif minggu pertama (bukan Rp).
- WP-09 MDE: SEBELUM melihat β; MDE_β = 2,80·SE; MDE_PT = MDE_β/γ; tulis keputusan G-power di D-007.
- WP-10 QA: outlier, total impor, bias Bapanas (pemetaan komoditas U20), laporan markdown.

### Task 1 (notebook 01, berat)
- LP dengan lag-augmentation (L = 4), efek tetap seri, SE cluster per **minggu**; asimetri via de⁺/de⁻.
- Event study per episode vs 499 jendela plasebo dari minggu tanpa episode.
- Deviasi provinsi: harga dikurangi rerata lintas provinsi per minggu; Σ_r δ = 0.
- Bootstrap: blok 13 minggu, B = 499, SATU vektor indeks minggu per replikasi dipakai ke harga & penggerak semua seri.
- Plasebo: np.roll de & dw sejauh ≥ 52 minggu; R = 499; provinsi cukup h ∈ {4,8,12}.
- EB: τ² DL (REML cek); τ² = 0 → semua provinsi = rerata (temuan sah).
- Target runtime: LP nasional 10 komoditas × 13 h < 2 menit; ukur bootstrap; bila > 30 menit, B = R = 199 untuk non-fokus + D-xxx.

### Task 2 (notebook 02, berat)
- H0-Het: Q, τ², I² per komoditas pada h = 8 vs distribusi plasebo; FDR BH antar 10.
- Clustering SELALU jalan (D-004): Ward pada 34 × fitur tersusut; k ∈ {2..6}; diterima bila silhouette maks > p95 plasebo,
  selain itu k = 1 ("tidak ada struktur regional terdeteksi").
- Stabilitas: K-Means ARI, ko-asignasi bootstrap, Jaccard < 0,6 → "pola lemah"; label netral K1, K2, …
- Struktur tertanam: δ 0,1–0,5 ditanam pada noise plasebo; recovery = P(k benar ∧ ARI ≥ 0,8) → batas deteksi.

### Task 3 (notebook 03, ringan)
- 3a Kendall τ PT(8) vs rasio impor (N = 10), p permutasi eksak (10! = 3.628.800), LOCO; kesimpulan "di antara 10 komoditas".
- 3b meta-regresi ≤ 3 fitur praregistrasi; interval = lebih lebar dari bootstrap blok dan CR2; jackknife provinsi.
- 3c FE komoditas×minggu, interaksi Δe × Z(r) (dapat dipotong).
- H2 (uji ringan berbasis panel, ditulis `task3`): Wald β⁺(8) = β⁻(8), SE cluster minggu → `asymmetry` (D-125).
- E2 (eksploratif): LP nasional per rezim HET/HAP (antar tanggal penetapan harga acuan konsumen) → `regime_profiles` (D-124);
  interval dikalibrasi plasebo (SE cluster rezim pendek terlalu sempit, D-127).
- Inferensi nasional terkalibrasi plasebo (tambahan, D-129): `national_calibrated` dari `profiles` + `placebo_stats` (+ `boot_replicates`
  untuk `boot_ratio`); interval resmi `profiles` tidak berubah.

### Task 4 (notebook 04, berat; paralel dengan Task 1)
- Target p_{t+h} − p_t, h ∈ {4, 8}; origin tiap 4 minggu sejak 2021-01-04 s.d. freeze − h.
- Train hanya baris dengan t + h ≤ origin; join harga dunia memakai `available_at` (as-of); tidak ada split acak.
- M0 nol; M1 ridge (lag Δp, musiman, Brent); M2 + kurs & harga dunia (1/4/8 minggu) + episode; M3 HGB + identitas.
- Metrik: MAE, RMSE, rasio vs M1 (semua origin & large_move > p80 latih), DM HAC; selalu laporkan n_origins & n_nonoverlap.
- Sebut "pseudo-real-time" (vintage revisi tidak tersedia).

### Robustness (notebook 05)
Tier 1 wajib: h 8 vs 12; lag 2/4/8; sub-periode sebelum/sesudah 2021-04-05 (V3); tanpa Mar–Jun 2020 & bulan Brent
ekstrem; dekomposisi de = komponen dolar global + spesifik rupiah; frekuensi bulanan. Validasi V2 (studi kasus 2026,
hanya origin dengan outcome lengkap) & V4 (LP vs event study). Tier 2 opsional (varian alternatif termasuk Minyak Goreng
Curah, agregasi observasi terakhir, definisi alternatif, outcome Bapanas).

### Pencegahan kebocoran (semua task)
Task 1–3 deskriptif: data bulanan diselaraskan menurut periode observasi. Task 4: as-of; Pink Sheet tersedia hari kerja
ke-2 bulan berikutnya; impor BPS +45 hari. Target Task 3 dari estimasi periode penuh → hanya deskriptif.

---

## 13. Gerbang, jadwal, pemotongan

| Gerbang | Tanggal | Syarat | Konsekuensi |
|---|---|---|---|
| G6 praregistrasi | 21 Nov | params, varian, bobot pakan, grup fokus, hipotesis beku + sha256 config di PREREGISTRATION | perubahan setelahnya = DEVIASI PRAREGISTRASI |
| G-power | 23 Nov | `mde.csv` | MDE PT(8) > 0,5 untuk bawang putih, gula, minyak goreng → LP sekunder; event study + harga dunia utama; Task 4 kontribusi DM utama |
| G-het | 25 Nov | `heterogeneity.csv` | tak ada yang lolos → nol + batas deteksi; clustering tetap jalan |
| Pembekuan hasil | 27 Nov | semua artefak ship ada | `results/` tidak diubah kecuali bug |
| G7 jalan ulang | 28 Nov | zip diekstrak di folder bersih → app & task4 jalan | – |
| G8 audit klaim | 28 Nov | semua teks lolos §20 | – |
| Submit | 29 Nov | `[HUMAN]` unggah | batas resmi 30 Nov |

Urutan pemotongan bila waktu habis (D-014): Tier 2 → analisis dalam-komoditas & Moran's I → Task 3c → M3.
**Tidak pernah dipotong:** Tier 1, distribusi plasebo, MDE.

Jalur kritis: WP-06 → WP-08 → WP-09 → WP-13 → WP-15 → WP-16 → WP-17 → WP-18 → WP-19..21 → WP-31/33 → WP-32/34.
Paralel: WP-07 (→ WP-22/23), WP-25 → WP-26 → WP-27, WP-11 sebelum 21 Nov.

---

## 14. Resep mengimplementasikan sebuah WP

1. **Baca kontrak:** docstring stub (input, output, kolom), heading WP di WORKPLAN, bagian METHODS, entri artefak di
   `utils/artifacts.py`, dan pemanggilnya di `pipelines/<tahap>.py`.
2. **Tes dulu:** buat/ubah `tests/test_<topik>.py` dengan data sintetis yang jawabannya diketahui (lihat §16.3).
3. **Implementasi** di modul lapisan yang sesuai. Ganti seluruh badan fungsi (hapus `todo(...)`); hapus import `todo`
   bila modul tak lagi punya stub. Hapus komentar `# noqa: F401 (WP-xx)` pada import yang kini benar-benar dipakai.
4. **Parameter** dari `cfg.params[...]`; bila butuh parameter baru, tambahkan ke `params.yaml` dengan komentar
   (setelah G6 = deviasi praregistrasi, catat di DECISIONS).
5. **Jalankan** tahapnya: ringan → `python -m kagami <tahap>` lokal; berat → uji dengan subset kecil lokal
   (mis. B = 9, satu komoditas) lalu jalankan penuh di Kaggle/Colab.
6. **Periksa hasil** pada data asli: bentuk, NaN, rentang nilai, angka penting; catat di bagian WP dan SESSION_LOG.
7. **Dokumentasi:** §2 & §9 CLAUDE.md, papan WORKPLAN, DECISIONS/OPEN_ISSUES bila ada.
8. **pytest** penuh.

Template fungsi:

```python
def nama_fungsi(cfg: Config, df: pd.DataFrame) -> pd.DataFrame:
    """WP-xx. Satu kalimat tujuan.

    Input : kolom yang dibutuhkan dari artefak X.
    Output: kolom keluaran (sesuai utils/artifacts.py: <artefak>).
    Aturan: parameter dari cfg.params["..."]; keputusan terkait D-xxx.
    """
    p = cfg.params["bagian"]
    rng = np.random.default_rng(cfg.seed + OFFSET)   # offset unik per fungsi, catat di docstring
    ...
    return out[[...kolom kontrak...]]
```

---

## 15. Konvensi kode

- Python ≥ 3.10, `from __future__ import annotations`, type hints pada fungsi publik.
- Docstring berbahasa Indonesia, diawali "WP-xx." untuk fungsi milik WP; jelaskan input/output/aturan.
- Nama kolom & id: snake_case Inggris/Indonesia sesuai kontrak artefak; jangan menamai ulang kolom kontrak.
- Tidak ada angka analisis di kode (ambang, horizon, B, R, tanggal) — semua dari `params.yaml`/`commodities.yaml`.
  Konstanta struktural (mis. urutan status, nama tier) boleh sebagai konstanta modul.
- pandas: hindari chained assignment (pakai `.copy()` setelah filter lalu assign); `groupby(...).agg` bernama;
  vektorisasi, hindari loop baris; join selalu pada `week`/`province_id`/`commodity`.
- RNG: `np.random.default_rng(cfg.seed + offset)`; offset berbeda per fungsi/tahap dan dicatat; jangan `np.random.seed`.
- Komputasi berat: vektorisasi numpy; paralel dengan `joblib` (tersedia di Kaggle/Colab) bila perlu; ukur waktu.
- Cetak progres singkat dengan prefiks `[tahap]` (contoh `[snapshot] <n> file -> ...`); tidak perlu logging framework.
- Error eksplisit lebih baik daripada hasil diam-diam salah (contoh: `select_variants` raise bila varian tidak ada).
- Jangan menghapus data diam-diam: tandai (flag/status) dan laporkan.
- File teks: UTF-8, LF.

---

## 16. Pengujian

### 16.1 File tes

| File | Menguji |
|---|---|
| `tests/conftest.py` | alias `kagami` → `src/` tanpa instalasi; fixture `cfg`, `pihps` (skip bila mentah tak ada) |
| `test_config.py` | desain komoditas (10; peran 6/3/1; 5 grup fokus), wilayah (34, 7, hub, zona), sumber ada, varian ada di PIHPS, seri Pink Sheet ada |
| `test_loaders.py` | loader semua sumber pada data asli + kolom; BPS v2 memuat bawang putih; bentuk PIHPS; grup varian dari prefiks (regresi D-022); nama provinsi terpetakan 34 |
| `test_stats.py` | OLS & SE cluster (grup kosong dibuang), DL/REML/EB, BH (Holm di test_forecast_eval), block bootstrap, circular shift, DM |
| `test_weekly.py` | status sel sintetis, grid, week_start, select_variants (asli & error), aggregate asli, aturan kelayakan |
| `test_drivers.py` | grid penggerak, de & pengisian minggu libur, jendela Idulfitri, harga dunia (komposit, dw bulanan, available_at) & komposit alternatif Tier 2, episode (gabung, berdempetan, data asli) & tabel variasi kurs; flag episode real-time = deteksi ulang s.d. t & kebocoran penggabungan pemicu (D-162) |
| `test_panel.py` | panel 7 wilayah: indeks minggu pertama, tanpa lompatan saat komposisi berubah, hanya eligible, data asli |
| `test_local_projection.py` | desain LP (nama kolom, within, sampel, y manual), β/β⁺/β⁻/ω sintetis dipulihkan, filter eligible, γ(h), jalur cepat national_profiles = loop build_design |
| `test_power.py` | SE skor H0 = SE cluster bila β = 0, skala derau, SE asimetri = SE Wald selisih bila β⁺ = β⁻, gerbang G-power & H2, MDE data asli |
| `test_event_study.py` | jalur event (lonjakan terlihat, tahan komposisi, horizon terpotong = NaN), kandidat plasebo, p plasebo, wilayah data asli |
| `test_qa.py` | lonjakan satu hari vs perubahan level, total impor, bias Bapanas & pemetaan, tumpang tindih Comtrade–BPS (sintetis & asli), laporan Tahap 0 |
| `test_robustness.py` | Tier 1: jendela sampel, demean ulang sub-sampel, dekomposisi kurs, semua cek ada, β pulih (h=0), efek khusus COVID terdeteksi; validasi: implikasi LP, V4 cocok/berlawanan, V2 episode & forecast, pusat median plasebo; Tier 2: panel varian/observasi terakhir/Bapanas, β pulih, Kendall ordinal, komposit harga dunia, keterpencilan alternatif |
| `test_forecast_eval.py` | n_nonoverlap, Holm, kontrak forecast_eval, rasio M1 = 1, DM mendeteksi sinyal kurs, H5 (keluarga tetap 2), panel wilayah, ablation |
| `test_planted.py` | struktur tertanam: simpleks δ·√F, z-score, silhouette, ambang plasebo ≈ 5% lolos, kurva naik & dapat diulang, batas deteksi, EB penanaman = EB matriks fitur, regresi U105 (tanam sebelum susut) |
| `test_asymmetry.py` | H2: Wald = spesifikasi asimetris LP, selisih tertanam terdeteksi, data simetris jarang ditolak, status konfirmatori/bootstrap/plasebo, interval laporan = Wald ∪ bootstrap |
| `test_calibration.py` | D-129: kontrak & filter (nasional, e/w, h kunci), crit ≥ z, p < α ⇔ interval tidak memuat nol, crit = statistik urutan & p plasebo eksak, q BH, boot_ratio, tanpa plasebo → normal, `se` wajib; D-163: baris PT = baris e / γ (p, q, crit sama), provinsi terkalibrasi (null dipool, provinsi tertanam terdeteksi, derau ≤ 5%, q BH per sel, boot_ratio) |
| `test_regimes.py` | E2: tanggal perubahan regulasi (filter & gabung), batas rezim, β per rezim pulih pada data sintetis, kalibrasi plasebo (crit ≥ 1,96, p plasebo, q BH, dapat diulang) |
| `test_heterogeneity.py` | Q/τ²/I² = DL, τ² REML berdampingan, ρ̄, wajib `se`, p plasebo & BH (sintetis); permutasi n!, Kendall eksak vs brute force, E1 10 komoditas |
| `test_reference.py` | WP-07: concordance & confidence, rasio impor FAOSTAT (jendela tahun) & bawang putih dari perdagangan, tanggal & verifikasi regulasi, fitur provinsi |
| `test_deviations.py` | WP-15: demean lintas provinsi, δ tertanam dipulihkan & Σ_r δ = 0, profil wilayah |
| `test_inference.py` | WP-16: satu indeks blok per replikasi, plasebo geser ≥ 52 minggu (β ≈ 0), CI tidak menyempit |
| `test_response.py` | WP-17: penyusutan EB (τ² = 0 → μ), fitur respons R/W/PT8/t_half/A8 |
| `test_clustering.py` | WP-19/20: matriks fitur, Ward, pilih k vs plasebo, K-Means ARI, Jaccard, pembanding partisi (k = 1 → ARI NaN) |
| `test_task2.py` | Task 2 end-to-end pada profil provinsi sintetis dengan 3 kelompok tertanam |
| `test_association.py` | WP-23/24: meta-regresi & interaksi FE memulihkan koefisien tertanam; p ⇔ interval laporan & q BH (U106), p bootstrap sisi = persentil |
| `test_forecast.py` | WP-25/26: tanpa kebocoran as-of (termasuk de sesudah t0 → flag `episode` real-time sama, D-162), origin, model M0–M3 & M2_nofx, checkpoint |
| `test_direction.py` | D-141 (eksploratif): klasifier C2 (+ kurs) memulihkan sinyal kurs tertanam lebih baik dari C1, penjaga (satu kelas, y = 0, model tak dikenal), bentuk & resume rolling_direction, beda akurasi berpasangan, prediksi selektif |
| `test_direction_tuned.py` | D-145 (eksploratif): fitur dinamika harga tanpa informasi sesudah origin (harga & status masa depan dirusak → fitur ≤ origin sama), D-147: penghapusan data sesudah origin di SETIAP origin h 4 & 8 → seluruh matriks fitur + target terealisasi identik, harga dunia tersembunyi sampai `available_at`, label belum terealisasi tidak mengubah prediksi, nilai fitur yang diketahui (lag, MA, musiman, deviasi spasial Σ = 0, umur carry-forward), kolom & penjaga C1t/C2t, C1t memulihkan mean-reversion tertanam lebih baik dari C1, bentuk & resume `rolling_direction_tuned` |
| `test_neural.py` | D-142 (eksploratif): jendela latih tanpa target belum terealisasi, PatchTST/TSMixer tidak memakai data sesudah origin (ubah masa depan → ramalan sama), adapter TimesFM hanya konteks s.d. origin (forecaster palsu), baris uji = Task 4, resume |
| `test_task1.py` | `task1.run` end-to-end pada artefak sintetis (B/R kecil): semua artefak tahap tertulis, interval tidak menyempit, tiga level |
| `test_synthetic.py` | generator sintetis Task 1 (`tests/synthetic.py`): skema = kontrak artefak, jawaban tertanam pulih |
| `test_app_data.py` | halaman Streamlit terender dengan artefak sintetis berskema kontrak, termasuk `national_calibrated`, `asymmetry`, `regime_profiles` (WP-31); `load` tidak meng-cache artefak hilang & membaca versi baru (D-136); harga acuan Rupiah = tabel batas Rupiah findings, beranda beras +Rp89, `fmt_rp`, `names_list` (D-171); D-172: `plain_text` membuang kode (kurung, kolom tabel, rentang "s.d."), `soften_semicolons` membiarkan titik koma antarangka/tabel/kode, `verdicts`, `fmt_frame` format Indonesia, literal string halaman app tanpa kode D-/U-/WP- & titik koma; D-173: `math_text` notasi → LaTeX (kode & rumus yang ada dibiarkan), `plain_names`; D-175: artefak sintetis `drivers_weekly`, `panel_weekly`, `province_calibrated` untuk halaman lini masa & profil provinsi |
| `test_package.py` | WP-32: isi zip juri, tanpa data tanpa hak redistribusi, artefak ship hilang dilaporkan, CLI jalan dari folder baru; D-176: laporan `docs/audit/**/*.md` ikut, data audit hanya dari red flag, makalah ikut bila sudah dikompilasi |
| `test_paper.py` | D-177: makalah memuat semua bagian wajib juknis §2c berurutan, sitasi = `\defref` = daftar pustaka, frasa terlarang §20 tidak ada, angka utama sama di makalah, `findings.md`, dan PDF (PDF tidak basi), gambar yang dirujuk ada, setiap gambar/tabel dirujuk di teks |
| `test_runtime.py` | lokasi default, tulis out/baca artefak tahap sebelumnya, override raw, deteksi Kaggle, layout Colab, stdout CLI cp1252 (regresi D-138) |
| `test_notebooks.py` | satu notebook per tahap, valid, sel 0–1 identik, tanpa output, sel setup jalan lokal |
| `test_viz.py` | semua fungsi viz membangun figure dari artefak sintetis; tanpa interval → tanpa pita; format angka & lencana (regresi NaN); peta tanpa subplot geo (offline) & nilai wilayah ke provinsi; V18 hanya Tier 1/2 + komponen dekomposisi; V19 subjudul H2; geometri referensi = 34 provinsi crosswalk; D-169: skenario = transformasi log eksak (bukan PT·x) & angka app = tabel batas Rupiah findings (artefak `profiles`), kalimat DM memuat arah (p kecil + DM negatif = lebih buruk) & nama model bisa diganti, subjudul skenario berlabel "bukan ramalan" (D-171); D-172: grafik ketahanan tanpa anotasi garis & tanpa rantai "·", bungkus judul/subjudul/sumbu di ponsel & legenda di dasar wadah (desktop tetap), angka graf pipeline tidak di kolom simpul; D-175: lini masa kurs (sorotan, label episode), kipas episode (pita + garis per episode, sorotan di atas), kipas semua komoditas 5/2 kolom, tren harga provinsi vs median, kelengkapan data berlabel, `month_year`; D-176: judul desktop dengan `\n` → dua baris + ruang atas 24 px |
| `test_app.py` | 7 halaman Streamlit jalan tanpa exception (artefak ada/belum) |
| `test_wiring.py` | modul terpakai (CLI/app/notebook), fungsi viz terpakai, todo → WP ada, artefak WP ada, artefak punya produsen & terdokumentasi, halaman app (11 halaman, D-175, semua terdaftar di router `app/Home.py`, D-170, D-171), artefak yang dibaca pipeline dideklarasikan REQUIRES/OPTIONAL (D-140), artefak yang dibaca app (`need`/`load`) ship=True dan tidak di-ignore git (D-176; dilewati tanpa repo git) |
| `test_claude_md.py` | §9 dokumen ini sinkron dengan kode (fungsi publik & status stub) |
| `test_handoff.py` | format setiap `docs/handoff/*.md`: nama file, frontmatter, bagian wajib, status vs kotak centang |
| `test_drive.py` | sinkron Drive dengan Drive palsu di memori: path dicerminkan, timpa bukan duplikat, pull ke anggota lain, hanya tahap diminta, lokal tanpa token dilewati, push/pull data mentah bolak-balik (MD5, glob, tidak menimpa) |
| `test_download.py` | resolusi tautan unduhan terbaru (pola Pink Sheet) & url cadangan, tanpa jaringan |
| `test_tracking.py` | WP-36: metrik clustering/regresi = rumus numpy independen, penjaga not_applicable (k = 1, k = n, NaN, y = 0), run sukses/gagal & galat dilempar ulang, log tidak ditimpa, bertingkat & pipeline_id, run induk dari hash, hasil basi & perbandingan, evaluasi-saja, graf DAG, git, log Drive bolak-balik, cek integritas silhouette & MAE pada artefak asli, halaman app 7, grafik run dengan format waktu campuran (D-138), metrik arah = rumus confusion/AUC/AP manual + penjaga (D-139); D-143: p bootstrap ⇔ interval & penurunan penilaian yang tidak lolos BH; D-144: F1 berbobot/cakupan/akurasi termasuk nol, ringkasan Task 4 & sakelar diagnostik; D-140: interval bootstrap origin mendeteksi sinyal & AUC/AP = sklearn, tabel segmen, kesehatan fitur, aturan penilaian, perubahan sama/berubah/baru/hilang, code hash, sinkron artefak & status tahap; D-170: beda ujung baris saja tetap sinkron & tidak basi, perubahan isi tetap terdeteksi |
| `test_docs_sync.py` | dokumen hidup tidak basi: tautan & path ada, papan WP vs stub, §2 vs papan, ID D-/U- ada, kunci `params.*` ada, sumber/komoditas/notebook/subpaket/tes terdokumentasi (§3.4) |

### 16.2 Menjalankan
- Semua: `python -m pytest -q` (± 2–9 menit; 387 tes pada 2026-11-24). Subset: `python -m pytest -q tests/test_weekly.py -k eligibility`.
- Tes yang butuh mentah di-skip otomatis bila mentah tidak ada (paket juri).

### 16.3 Pola tes yang disarankan
- Data sintetis kecil dengan jawaban pasti (contoh: `tests/test_weekly.py::synthetic`, `tests/test_drivers.py::_daily`).
- Untuk estimator: bangkitkan data dari model diketahui (β benar) → cek dipulihkan dalam ±2 SE.
- Untuk inferensi: cek properti (panjang indeks, rentang shift, satu indeks per replikasi).
- Untuk kebocoran (Task 4): untuk origin acak, assert tidak ada `available_at` > origin dan tidak ada target t+h > origin di train.
- Satu tes pada data asli per artefak (bentuk, NaN wajar), di-skip bila mentah tidak ada.
- Perhatikan kalender: 2024 punya 53 hari Senin (pelajaran dari tes kelayakan).

---

## 17. Notebook & cloud

- Enam notebook di `notebooks/`, satu per tahap. Struktur: markdown pengantar → sel 0 setup (identik) → sel 1
  `init_runtime` (identik) → `drive.pull` + cek input (`require`) → `pipelines.<tahap>.run(cfg)` → `drive.push` →
  diagnostik `viz.plots`. Tes memastikan setiap notebook punya pull & push untuk tahapnya.
- Logika analisis TIDAK boleh ditulis di notebook. Kebutuhan baru → fungsi di `src/` (+ viz bila grafik).
- Simpan notebook **tanpa output**. Sel 0–1 harus identik di semua notebook (tes). Bila mengubah sel 0/1, ubah keenamnya.
- Mengedit notebook: pakai `nbformat` (baca → ubah `cell.source` → tulis) atau tool NotebookEdit; jangan edit JSON manual.
- Beban: 00 & 03 ringan (lokal); 01, 02, 04 berat; 05 sedang–berat → Kaggle/Colab.
- Urutan: 00 → (01 ∥ 04) → 02, 03 → 05. Input diambil dari folder Drive tim (§7.3), bukan dari output notebook lain;
  notebook menarik `REQUIRES` + `OPTIONAL` (panel provinsi, D-122). 01 ± 1,5–2 jam (± 7 dtk/replikasi, tanpa checkpoint).
- Distribusi kode/data: `python -m kagami bundle [--raw]` → `dist/kagami_code.zip`,
  `dist/kagami_raw_PRIVATE.zip`. Dataset Kaggle `kagami-code` (**PRIVAT**; `kagami-raw` opsional karena data mentah di Drive tim) atau Google Drive
  `MyDrive/kagami/`. Pengunggahan = tugas `[HUMAN]`; agent tidak masuk ke akun Kaggle/Google user.
- Hasil cloud ke project lokal: `python -m kagami drive-pull all` (tanpa salin manual).
- Langkah rinci: `docs/NOTEBOOKS.md`.

---

## 18. App Streamlit

- `app/Home.py` = router `st.navigation` (D-170, D-171, D-173, D-175): bagian "Hasil penelitian" = `pages/1_Beranda.py` Ringkasan
  (default), `pages/10_Lini_Masa_Rupiah.py` Rupiah dari waktu ke waktu (lini masa kurs, kipas episode), 2 Respons harga,
  `pages/11_Profil_Provinsi.py` Profil provinsi (label harga, tren, kelengkapan, deviasi lolos BH global), 3 Perbedaan
  antarprovinsi, 4 Faktor penjelas, `pages/9_Prediksi.py` Prediksi (url_path `Prediksi`), 5 Simulasi rupiah; bagian "Lampiran" = `pages/8_Data_dan_Metode.py` (sumber, langkah pengolahan + rumus model, kelengkapan,
  pemeriksaan kualitas data, MDE, daftar istilah bersimbol, reproduksi) dan 6 Laporan lengkap (findings.md, notasi dirender LaTeX).
  `pages/7_Evaluasi_Eksekusi.py` (Riwayat eksekusi, WP-36: membaca `logs/`) = alat pengembang, hanya di menu bila env `KAGAMI_DEV=1`.
  `url_path` halaman lama dipertahankan. Halaman baru wajib didaftarkan di router (`test_wiring`). Jalankan `python -m kagami app`.
  Tema di `.streamlit/config.toml` (kertas terang, judul serif, biru tua `#1c5cab`, toolbar minimal).
- `common.py`: alias paket, `CFG`, `PAGE` (path halaman untuk tautan), `load` (cache per versi file; ketiadaan tidak di-cache, D-136),
  `need` (label "Menunggu hasil (WP-xx)"), `page_header(judul, kalimat pembuka)`, `lead` (jawaban halaman), `note` (catatan cara
  membaca), `footer(sumber, periode)`, `not_detected_badge`, `commodity_labels`, `names_list`, `unit_names`, `load_geo`, `picker`
  (pilihan disimpan di URL `?key=`), `area_options`/`area_level` (nasional + 7 wilayah), `reset_button`, `table`, `frame` (tabel
  berlabel pembaca; kolom yang tidak ada dilewati), `intervals`, `fmt_rp`, `reference_prices` (harga acuan Rupiah dari tabel batas
  Rupiah findings), `inject_style` (CSS bersama + `chart_wrap`; dipanggil router), `nav_link` (`st.page_link` dengan cadangan teks di
  luar router); D-172: `plain_text`/`soften_semicolons`/`readable` (teks dari berkas tanpa kode & titik koma prosa; berkas tidak diubah),
  `verdicts` (naik/turun/belum terlihat dari rentang 95%), `fmt_frame`/`show_table` (angka tabel format Indonesia), `chart_wrap`
  (User-Agent ponsel → bungkus judul grafik); D-173: `math_text` (notasi teks berkas → LaTeX inline), `plain_names` (nama berkas
  hasil/kolom → nama pembaca), `PLAIN_NAMES`. Rumus baru ditulis LaTeX (`st.latex` / `$...$`), bukan teks seperti exp(...).
- Juri & TPID (D-170, D-171): yang tampil di bagian hasil hanya jawaban dan bukti; kode internal (nama kolom mentah, `None`, ID
  keputusan/isu, H2/E1/RQ, Tier, M1/M2, β/ω/τ², PT(8), "origin", "plasebo", path server, status lineage) masuk lampiran teknis atau
  expander teknis. Setiap halaman hasil dibuka dengan jawabannya (`lead`, dihitung dari artefak); angka dalam "% per 1% pelemahan
  rupiah" atau Rupiah; tanpa label tebal + penjelasan, pasangan negasi defensif, atau rantai "·". Beranda menghitung semua angkanya
  dari artefak (tidak ada angka hasil tertulis tangan). D-172: tanpa kode D-/U-/WP- dan tanpa titik koma di teks halaman (dites); tabel
  lewat `show_table`; kolom kesimpulan hanya bila barisnya berbeda; grafik baru dicek tumpang tindihnya di 1280/1024/375 px.
- Tampilan (D-134, PLAN.md §18): warna/label/format angka dari `viz.style` (jangan hex atau kode mentah seperti `e_neg` di halaman);
  peta di sumbu kartesius, jangan `go.Choropleth`/`choropleth_map` (mengunduh topojson/tile → gagal offline). Baris provinsi
  `profiles` = deviasi δ, dua versi per sel → pakai `shrunk = True` dan labeli "deviasi".
- Aturan (D-010, proposal §7.1): hanya membaca artefak; tidak ada login, input data pengguna, atau estimasi runtime.
  Setiap grafik: sumber, satuan, periode, rentang 95%, label "asosiasi historis, bukan sebab-akibat" (satu kali per grafik + footer).
  "Tidak terdeteksi" bila rentang memuat nol. Halaman 3 menangani k = 1 (batas deteksi hanya untuk struktur yang diuji). Halaman 9:
  setiap p DM ditampilkan dengan tanda/arah (`viz.style.dm_summary`, D-169). Halaman 5: exp(PT(h)·ln(1 + x/100)) − 1
  (`viz.plots.scenario_change`, sama dengan tabel batas Rupiah findings; bukan PT·x; rumus di expander "Cara menghitung"), x ∈ {1,3,5}%,
  Rupiah dari harga acuan nasional, bendera ekstrapolasi, label "skenario bersyarat, bukan ramalan". Halaman 6 membaca
  `results/findings.md`. Beranda menyebut status sebagai kalimat biasa: prototipe riset, belum siap sebagai peringatan dini (U109).
- Grafik memakai `viz.plots`; jangan menulis plotly inline di halaman bila grafiknya juga berguna di notebook.

---

## 19. Hak data & paket juri

- Mentah dengan `redistribute: false` (PIHPS, JISDOR, BPS, Comtrade, Bapanas, BPS pangan) tidak boleh masuk zip juri.
- Zip juri (`python -m kagami package`): kode, configs, app, tes, docs/*.md, data/reference, artefak `ship=True`,
  mentah `redistribute: true`, log `logs/*/*.json` (WP-36; tanpa data mentah, path relatif), laporan `docs/audit/**/*.md` + skrip & hasil
  red flag (D-176), dan makalah `docs/paper/` (PDF, .tex, gambar, skrip gambar, D-177). Gagal bila artefak ship belum ada (kecuali `--allow-missing`).
- Dataset Kaggle mentah wajib **privat**; jangan membagikan tautan (U24). Izin BI (U13) mencakup redistribusi data turunan: `panel_weekly` ikut paket (D-104); PIHPS mentah & `pihps_daily` tidak.
- Saat menyebut data: "Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia)", bukan "dataset kami".
- Tiga tingkat reproduksi: A app dari results; B semua tahap dari data turunan yang dikirim (panel provinsi + wilayah, D-104);
  C unduh ulang mentah.

---

## 20. Rambu klaim & bahasa

| Jangan tulis | Tulis |
|---|---|
| "Penelitian pertama tentang ..." | "Sejauh penelusuran kami, belum ada studi yang ...; studi terdekat adalah ..." |
| "Pelemahan rupiah menyebabkan harga X naik" | "Kenaikan IDR/USD berasosiasi dengan kenaikan harga X sebesar ... (interval ...), setelah mengendalikan ..." |
| "KAGAMI memprediksi kenaikan harga" | "Skenario bersyarat berdasarkan pola historis"; "dalam evaluasi rolling-origin, fitur kurs menurunkan MAE sebesar ..." |
| "Komoditas impor lebih rentan" | "Di antara 10 komoditas yang diamati, komoditas A dan B menunjukkan PT(8) lebih besar" |
| "Provinsi terbagi menjadi k tipe kepekaan" (tanpa uji null) | "Provinsi membentuk k kelompok yang lolos uji plasebo dengan stabilitas Jaccard ..." / "tidak ada struktur regional yang terdeteksi; struktur dengan selisih ≥ ... akan terdeteksi" |
| "Faktor terpenting adalah ..." | "Karakteristik yang berasosiasi paling kuat adalah ... (β = ..., interval ...)" |
| "Model tervalidasi pada episode 2026" | "Dalam evaluasi bersyarat lintas episode 2021–2026, ...; studi kasus 2026 menunjukkan ..." |
| "Tidak ada pengaruh kurs" | "Pengaruh di atas X dapat dikesampingkan pada horizon 8 minggu" |
| "Kerentanan provinsi" | "Kepekaan harga eceran terhadap kurs" |
| "Dataset kami" (PIHPS mentah) | "Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia)" |
| "Komoditas lebih menentukan daripada lokasi" | "Dalam sampel 10 komoditas, estimasi respons bervariasi antarkomoditas, sedangkan heterogenitas provinsi di atas plasebo hanya terdeteksi pada telur & daging ayam" (bukan dekomposisi varians formal) |
| "Sisanya berasal dari faktor lain" (dari hasil nol) | "Bagian yang tidak dijelaskan asosiasi kurs dalam model perlu ditelusuri ke faktor lain (pasokan, musim, kebijakan, faktor tak teramati)" |
| "DM p = 0,009" tanpa arah | "DM = −2,70: M2 kurang akurat dari M1 (p dua sisi 0,009; p satu sisi untuk keunggulan M2 0,996)" |
| "Sistem peringatan dini" / "nilai ekonomi daftar pantau" | "Prototipe riset & analitik pendukung keputusan"; tabel rasio biaya = "analisis kepekaan, bukan nilai harapan tervalidasi" |
| "Tinjauan pustaka sistematis" (tanpa protokol PRISMA) | "Kajian pustaka tematik"; rujukan yang hanya dari cuplikan pencarian dicek full-text dulu (U12) |

Tambahan: setiap angka disertai interval & satuan; hasil nol ditulis sebagai batas atas; Task 4 disebut "evaluasi
bersyarat, pseudo-real-time"; E1 ditulis "di antara 10 komoditas yang diamati"; rujukan "belum diverifikasi" (U12)
tidak boleh dikutip sebelum dicek. Jangan memakai "±" untuk "sekitar" di teks untuk juri (terbaca interval simetris; D-169);
interval asimetris ditulis batas bawah..batas atas. `carry_forward` = "rangkaian harga identik", bukan "kekakuan harga" atau "imputasi".
Teks app untuk juri/TPID (D-171): kalimat aktif dengan pelaku ("kami"); jawaban dulu; tanpa label tebal + penjelasan, pasangan negasi
defensif ("bukan X dan bukan Y"), daftar tiga dalam kurung, judul klaim pembelaan, atau kode internal; p tidak ditulis sebagai peluang
hipotesis benar. D-172: kalimat app tanpa titik koma (pecah jadi dua kalimat); titik koma hanya boleh memisahkan angka berdesimal koma
("DM −1,90; p 0,062"); kolom berisi nilai yang sama untuk semua baris diganti satu kalimat penjelas.

---

## 21. Ringkasan keputusan (lengkap: `docs/DECISIONS.md`)

| ID | Keputusan | Status |
|---|---|---|
| D-001 | Paket Python + CLI per tahap | FINAL |
| D-002 | Mentah di `data/raw/<sumber>/`, nama dirapikan, isi tak diubah | FINAL |
| D-003 | Registry artefak = kontrak antar tahap | FINAL |
| D-004 | Clustering selalu jalan, dinilai vs plasebo | FINAL |
| D-005 | Inferensi berbasis minggu (cluster minggu) | FINAL |
| D-006 | Periode mulai 2018-01-01 (337/340 layak) | FINAL |
| D-007 | Aturan G-power (MDE PT(8) > 0,5) | FINAL; diputuskan D-115: LP tetap utama |
| D-008 | PIHPS v2_merged kanonik (bagian "v1 untuk QA" diganti D-102) | FINAL |
| D-009 | Mesin statistik numpy/scipy sendiri | FINAL |
| D-010 | App hanya membaca artefak | FINAL |
| D-011 | Varian representatif | FINAL (G6) |
| D-012 | Komposit pakan 0,6 Maize + 0,4 Soybean meal | FINAL (G6) |
| D-013 | 6 komoditas fokus dalam 5 grup (ayam+telur = pakan) | FINAL (G6) |
| D-014 | Urutan pemotongan lingkup | FINAL |
| D-015 | Kebijakan kirim data turunan (bagian panel provinsi diganti D-104) | FINAL |
| D-016 | Harga dunia bulanan → mingguan menurut bulan hari Senin | FINAL |
| D-017 | Kerangka 34 provinsi lama | FINAL |
| D-018 | Keterpencilan = ln(1 + km ke hub terdekat) | FINAL |
| D-019 | exim `Totals` = USD | FINAL |
| D-020 | Label minggu = Senin ISO | FINAL |
| D-021 | Prioritas status sel: missing > carry_forward > short > observed | FINAL |
| D-022 | Grup varian PIHPS dari prefiks nama | FINAL |
| D-023 | Minyak goreng = Kemasan Bermerk 1 (keputusan user) | FINAL |
| D-024 | Isi paket langsung di `src/` (keputusan user) | FINAL |
| D-025 | Konstruksi penggerak: isi minggu libur, JISDOR bulanan untuk w, buffer 52 minggu | FINAL |
| D-026 | `src/` berlapis (permintaan user) | FINAL |
| D-027 | Notebook per tahap lokal/Kaggle/Colab (permintaan user) | FINAL |
| D-028 | Nama proyek KAGAMI; paket/CLI `kagami` (keputusan user) | FINAL |
| D-100 | Input/output notebook lewat folder Drive tim (Drive API: pull/push) | FINAL |
| D-101 | Data mentah di Drive tim (push_raw/pull_raw) + alokasi dataset 20 Nov + `_superseded/` | FINAL |
| D-102 | `pihps_v1` dipensiunkan; QA v1 vs v2 dihapus dari WP-10 | FINAL |
| D-103 | Branch hanya `main`, `dev`, `feat/...` (bagian nama, pesan commit, merge & hapus branch diganti D-108) | FINAL |
| D-104 | Panel provinsi `panel_weekly` ikut paket juri (izin BI mencakup redistribusi turunan) | FINAL |
| D-105 | Pembagian tugas Danen–Ardell ulang: tiap Task dipegang berdua, beban seimbang | FINAL; sisa proyek diganti D-130 |
| D-130 | Danen mengambil alih jalur B & C; makalah, video, unggah ditunda; fokus penyelesaian project | FINAL |
| D-106 | Panel wilayah: rerata dua arah tahan perubahan komposisi | FINAL |
| D-107 | Konvensi episode, desain LP (`build_design`), SE MDE bentuk skor di bawah H0 | FINAL (teknis) |
| D-108 | Branch `feat/<fungsi>` maks 3 kata; commit `<tipe>: <deskripsi>` tanpa kode; merge `--no-ff` ke dev; branch tidak dihapus | FINAL |
| D-117 | Pesan commit & PR tanpa `Co-Authored-By`/atribusi AI (permintaan user) | FINAL |
| D-118 | LP cepat: bagian desain tanpa horizon dibangun sekali, numpy per horizon; hasil identik; `national_profiles` ± 6 dtk | FINAL (teknis) |
| D-119 | `ols_cluster` membuang baris dengan grup kosong (NaT/NaN) alih-alih crash (regresi D-118) | FINAL (teknis) |
| D-177 | Makalah lomba `docs/paper/` (LaTeX → PDF, gambar dari artefak & app), 55 rujukan diverifikasi (U12), klaim Persada dikoreksi, Hidayah & Askar tidak dikutip, naskah video | FINAL |
| D-176 | `drivers_weekly` & `panel_weekly` di-track git (dibaca app hal. 10/11), laporan audit & makalah ikut zip juri, judul grafik beranda dua baris | FINAL (teknis) |
| D-175 | Halaman Rupiah dari waktu ke waktu (lini masa kurs + kipas episode) & Profil provinsi (label harga, tren, kelengkapan, deviasi lolos BH global); kipas episode di Respons harga | FINAL (teknis) |
| D-174 | `results/findings.md` ditulis ulang tanpa pola tulisan AI (teks saja, setiap angka lama dipertahankan; tabel batas Rupiah identik; "Pertanyaan 1–5", "Ketahanan & validasi") | FINAL |
| D-173 | Lampiran untuk semua pembaca: rumus dirender LaTeX (KaTeX), Data & metode ditulis ulang (pemeriksaan kualitas data menggantikan laporan pipeline mentah), Laporan lengkap dengan panduan membaca & nama pembaca, Riwayat eksekusi hanya untuk pengembang (`KAGAMI_DEV=1`) | FINAL (teknis) |
| D-172 | App tanpa kode internal & titik koma prosa (teks berkas dibersihkan saat tampil, berkas tidak diubah), "Status" → "Kesimpulan" / catatan, angka tabel format Indonesia, grafik tanpa tumpang tindih di 1280/1024/375 px (bungkus per thread untuk ponsel) | FINAL (teknis) |
| D-171 | Teks & UX app untuk juri dan TPID: jawaban dulu per halaman, kosakata pembaca (% per 1%, Rupiah), kode & notasi ke lampiran/expander, Daftar istilah, Respons harga 3 pemilih + tab, Eksposur dipecah jadi Faktor penjelas + Prediksi, Laporan lengkap ke lampiran | FINAL (teknis) |
| D-170 | App untuk juri: navigasi berkelompok (hasil vs lampiran teknis), beranda jawaban-dulu dari artefak, isi teknis dipindah ke lampiran, label terbaca, tema terang serif; sinkron lineage mengabaikan beda ujung baris (21 artefak "tidak sinkron" palsu di app daring) | FINAL (teknis) |
| D-169 | Tanggapan review eksternal: arah DM di app, skenario eksak = findings, carry_forward = rangkaian harga identik (FAQ PIHPS), batas Rupiah asimetris, batas deteksi & proksi dibatasi, waktu origin didokumentasikan, status PV-2b & `integrity_check` (`-X utf8`) disinkronkan; angka artefak tidak berubah | FINAL (teknis) |
| D-168 | Temuan disajikan menurut tiga tingkat bukti; uji ukuran kalibrasi plasebo (4,4% vs ±1,96·SE 8,8%), batas atas Rupiah, buku besar periode uji 2024+ (Holm 10 perbandingan), `docs/DATASHEET.md`; angka artefak tidak berubah | FINAL (teknis) |
| D-167 | Aturan & evaluator validasi maju K4 dibekukan pra-target (label dari panel baru, ΔAP < −0,14 = gagal; CONSISTENT bila ΔAP ≥ 0 & AP ≥ B-CLIMS); `scripts/k4_forward_eval.py` | FINAL · eksploratif |
| D-166 | Validasi K4 (baca-saja): target benar; 0/6 kalibrator memperbaiki Brier (ekor h 8 = 5 origin, informasi rezim); ranking K4-E80 kalah dari C1-tuned pada ambang seragam 5%/10%; peluang h 4 hanya kategori; operasional BLOCKED | FINAL · eksploratif |
| D-165 | Jalur A: prediksi maju diaudit & evaluator dibekukan; GDELT lolos G1–G2 tetapi gagal G5 (BigQuery sandbox, ΔAUC ≤ +0,001); layar G5 tidak meloloskan kontrol positif (MDE ± 0,023); sumber pasokan baru terblokir akses; C1-tuned tetap | FINAL · eksploratif |
| D-164 | K4 risiko kenaikan material (target z P80 \|y\|, semua baris): ranking lebih baik dari C1-tuned & laju-dasar komoditas (h 4 terbukti dev & test), peluang h 8 gagal → PARTIAL, operasional BLOCKED (U109); pembanding laju-dasar komoditas wajib untuk klaim daftar pantau | FINAL · eksploratif |
| D-163 | Kelemahan tercatat: PT & provinsi terkalibrasi plasebo (`province_calibrated`, U107); kalibrasi skor daftar pantau ditolak (D-163a); fitur clustering konstan inert | FINAL · tambahan pasca-G6 / eksploratif |
| D-162 | U108: flag `episode` Task 4 real-time; M2/M3/C2/C2t & robustness V2 dijalankan ulang, kesimpulan H5 tetap | FINAL (teknis) |
| D-161 | NOAA CFSv2 lewat Colab (437 run): skill prakiraan nyata tetapi gagal gerbang 5; oracle cuaca terealisasi juga gagal → mekanisme tertutup; sumber prakiraan diuji oracle-nya dulu | FINAL · eksploratif |
| D-160 | Kelayakan sumber & penemuan sinyal (GDELT, CFSv2, SIJAGUNG/SPORA, DIBI): tidak ada yang lolos lima gerbang; SIJAGUNG gagal sinyal nasional | FINAL · eksploratif |
| D-159 | Audit kelayakan pasokan fisik (SP2KP, FDP, PIBC, GPM, KSA): tidak ada riwayat dev yang dapat diakses; tanpa modeling; aturan kelayakan sumber (EKSPERIMEN §3) | FINAL · eksploratif |
| D-158 | National Shock Nowcasting (breadth 110 kota + nasional–lokal, 2 iterasi): tidak ada perbaikan di luar keluarga intraminggu; layar arah nasional vs konsensus C1t wajib | FINAL · eksploratif |
| D-157 | Pilot cuaca sentra (NASA POWER) & impor bulanan Task 4 arah tidak membantu; sinyal nasional wajib diuji walk-forward (EKSPERIMEN §3) | FINAL · eksploratif |
| D-156 | Audit preprocessing & optimasi macro F1 Task 4 arah: 27 kandidat (fitur, threshold, bobot, model) tidak mengungguli C1-tuned; registri `docs/eksperimen_registry.csv` | FINAL · eksploratif |
| D-155 | Audit D-152–D-154: universe S1 valid; koreksi klaim (skor arah ≠ peluang kenaikan material, test 2024+ bukan independen, titik akhir, materialitas statistik vs kebijakan); aturan `docs/EKSPERIMEN.md` §5 | FINAL · eksploratif |
| D-154 | Business Understanding Task 4 arah: kriteria bisnis S1–S3 (daftar pantau, kalibrasi, arah saat bergerak material) di samping macro F1; C1-tuned lolos di test | FINAL · eksploratif |
| D-153 | Alur eksperimen Task 4 = CRISP-DM + kartu 8 komponen (`docs/EKSPERIMEN.md`); DU pola sekuensial / clustering / graf tidak lolos gerbang Modeling | FINAL · eksploratif |
| D-152 | Validasi `IW_NAT`: kebocoran 84/84 lolos, LOO = rerata nasional, separuh keuntungan h 4 dari harga Jumat, prediksi maju beku (12 origin); daya tidak cukup untuk konfirmasi; C1-tuned tetap | FINAL · eksploratif |
| D-151 | Pilot intraminggu & harga produsen PIHPS (`pihps_producer`, opsional): produsen tidak membantu (dev −0,006..−0,001); `IW_NAT` test +0,0085 / +0,0033 belum terbukti; C1-tuned tetap | FINAL · eksploratif |
| D-150 | Pilot harga pedagang besar PIHPS (`pihps_wholesale`, opsional): kaku, tidak mendahului eceran, tidak menaikkan macro F1 C1-tuned | FINAL · eksploratif |
| D-149 | Split dev s.d. 2024 (pasca-hoc): kalibrasi & fitur rezim tetap tidak lolos; fitur kebijakan hapus drift tanpa menaikkan macro F1 | FINAL · eksploratif |
| D-148 | Roadmap pasca-audit: preprocessing beku, `iw_gap` eksploratif terpisah, fitur rezim & kalibrasi temporal tidak lolos dev (drift baru 2024+), koreksi `episode` = U108, job > 1 jam di Colab T4 | FINAL · eksploratif |
| D-147 | Audit preprocessing Task 4 arah eksploratif (tick Rp50, label rapuh, agregasi hari, kebocoran semua origin, seimbang-seri, eksperimen preprocessing dengan C1-tuned tetap); label & `src/` tidak berubah | FINAL · eksploratif |
| D-146 | Optimasi arah ronde 2 eksploratif (diagnosis perubahan kecil, fitur fundamental/spasial/kalender, LightGBM/XGBoost, spesialis, 3 kelas, TCN/MLP GPU); tidak ada yang mengalahkan C1-tuned | FINAL · eksploratif |
| D-145 | Optimasi klasifikasi arah Task 4 eksploratif (fitur per seri, Optuna, threshold dev, kepala TimesFM–CatBoost); origin pengembangan ≤ 2023 vs test ≥ 2024; C1-tuned 0,677 / 0,680 | FINAL · eksploratif |
| D-144 | F1 berbobot/cakupan/akurasi termasuk nol, replikasi seed model deep (`_r<k>`), kepekaan blok & lag DM, segmen tahun origin, ringkasan Task 4 di halaman 7, `evaluator_version`; robustness Tier 2 tercatat identik | FINAL (teknis) |
| D-143 | Koreksi BH per keluarga untuk perbandingan eksploratif di penilaian halaman 7 & tabel segmen (p bootstrap persentil / DM); uji resmi tidak dikoreksi | FINAL (teknis) |
| D-142 | Model deep & foundation EKSPLORATIF untuk Task 4 (PatchTST, TSMixer ± kurs, TimesFM 3.0 zero-shot ± kovariat kurs) → `deep_preds`; atas keputusan Danen 2026-11-24 sebelum pembekuan; Chronos-2 tidak diunduh | FINAL · eksploratif |
| D-141 | Klasifier arah EKSPLORATIF (HGB classifier C1 tanpa kurs / C2 + kurs, rolling-origin Task 4) → `direction_preds`; dibandingkan berpasangan dengan C1, M3, M1 + prediksi selektif; bukan uji praregistrasi | FINAL · eksploratif |
| D-140 | Evaluasi dua lapis (status hitung vs penilaian terhadap acuan), interval bootstrap blok origin metrik arah, tabel per segmen, lineage output & status tahap, sidik jari kode; wiring OPTIONAL task2/robustness | FINAL (teknis) |
| D-139 | Diagnostik klasifikasi arah perubahan Task 4 (accuracy, F1, MCC, AUC, confusion) di log evaluasi & app hal. 7; bukan uji praregistrasi | FINAL (teknis) |
| D-138 | CLI memaksa stdout UTF-8 (crash cp1252 saat output diarahkan ke file); grafik hal. 7 parse waktu ISO8601 campuran | FINAL (teknis) |
| D-137 | Log eksekusi & evaluasi terpusat `src/tracking/` + `logs/` (JSON per run, tidak ditimpa), lineage sha256, metrik berpenjaga, app hal. 7; hasil analisis & params tidak berubah | FINAL (teknis) |
| D-136 | App: artefak yang belum ada tidak di-cache; kunci cache = path + mtime + ukuran (app daring tetap kosong setelah push) | FINAL (teknis) |
| D-135 | Deploy app: 23 artefak yang dibaca app (± 1,4 MB, ship=True) di-track git; hal. 6 tidak menunggu robustness; `requirements.txt` di paket | FINAL (teknis) |
| D-134 | Tampilan app (PLAN.md §18): palet tervalidasi `viz/style.py`, peta Indonesia offline (geoBoundaries ODbL, sumbu kartesius), provinsi = deviasi tersusut | FINAL (teknis) |
| D-133 | U102: tumpang tindih konkordansi HS diuji pada 2023 (Comtrade API publik vs BPS bulanan) → 14/15 kode cocok persis | FINAL (teknis) |
| D-132 | U106: p meta-regresi = max(CR2, bootstrap sisi) konsisten interval + q BH; ARI NaN saat k = 1; τ² REML di `heterogeneity` | FINAL (teknis) |
| D-131 | Task 4: diagnostik dummy bulan + Idulfitri (M2/M1 1,005 / 1,019, H5 Holm 0,56) → kesimpulan sama; praregistrasi tetap resmi | FINAL (teknis) |
| D-129 | Bootstrap blok menarik β ke nol → tambahan `national_calibrated` (±crit·SE plasebo, p = max(plasebo, normal), q BH); interval resmi tetap | FINAL · tambahan pasca-G6 |
| D-128 | H5/Task 4 tetap ridge gabungan praregistrasi; ridge per komoditas hanya diagnostik (kesimpulan sama) | FINAL (teknis) |
| D-127 | E2: interval rezim ±crit·SE dengan crit dari plasebo geser-melingkar (+ p plasebo, q BH); H2: interval laporan = Wald ∪ bootstrap | FINAL (teknis) |
| D-126 | Struktur tertanam: δ ditanam pada deviasi plasebo mentah, lalu susut EB & z-score seperti data asli (perbaikan U105) | FINAL (teknis) |
| D-125 | H2: Wald β⁺ = β⁻ lewat parametrisasi ulang, ditulis `task3` sebagai `asymmetry` (+ pembanding bootstrap & plasebo); hasil G-het | FINAL (teknis) |
| D-124 | E2: rezim = antar tanggal HET/HAP konsumen terverifikasi; LP nasional per rezim (jendela utuh), deskriptif → `regime_profiles` | FINAL (teknis) |
| D-123 | Data manual WP-07: penduduk 2025 (tabel BPS), n_kota (situs PIHPS, 110 kota), faktor GKG→beras 0,5762 (beras untuk pangan) | FINAL |
| D-122 | Notebook menarik `OPTIONAL` (panel provinsi) dari Drive; pipeline memperingatkan bila jatuh ke versi wilayah | FINAL (teknis) |
| D-121 | Kunci `association.import_ratio_years` [2018, 2023] & `forecast.run_m3` (sakelar D-014) ditambahkan setelah G6 | FINAL · DEVIASI PRAREGISTRASI |
| D-120 | Item FAOSTAT beras = "Rice, milled" + "Rice, broken" (bukan "Rice" = padi); rasio impor 0,033 | FINAL · DEVIASI PRAREGISTRASI |
| D-109 | Pembekuan G6 (varian, pakan, grup fokus tanpa perubahan) + koreksi Holm H5 | FINAL |
| D-110 | QA & event study: pemetaan Bapanas, ambang lonjakan di kode QA, jalur event tahan komposisi, plasebo bersama | FINAL (teknis) |
| D-111 | Tier 1 (jendela sampel, bulanan, dekomposisi), heterogenitas (`se` wajib, p satu sisi, BH per statistik), Kendall (τ-b, p eksak, interval jackknife) | FINAL (teknis) |
| D-116 | Robustness Tier 2: varian non-representatif dengan kelayakan sendiri, komposit pakan alternatif, observasi terakhir, ordinal jalur 2/1/0, outcome Bapanas bulanan vs PIHPS bulan sama | FINAL (teknis) |
| D-115 | Gerbang G-power resmi: LP tetap utama; MDE asimetri (satuan PT) → H2 konfirmatori beras & daging sapi (keputusan Danen) | FINAL |
| D-114 | Validasi V2/V4: kelebihan event di atas median plasebo vs implikasi LP (superposisi impuls), V2 = episode & origin tahun freeze, `placebo_median` di events | FINAL (teknis) |
| D-113 | Evaluasi Task 4: DM pada MAE per origin (HAC lag ceil(h/4)−1), sel jalur H5, keluarga Holm tetap 2 (p NaN = 1), α H5 dari PREREGISTRATION, model ablation `M2_nofx` | FINAL (teknis) |
| D-112 | Struktur tertanam: δ = selisih respons RMS per fitur antar setiap pasangan kelompok (simpleks acak), ditanam sebelum z-score pada matriks plasebo mentah | FINAL (teknis) |

---

## 22. Ringkasan isu terbuka (lengkap: `docs/OPEN_ISSUES.md`)

| ID | Isu | Status |
|---|---|---|
| U3 | Tanggal & isi PADG 7/2026 → `params.calendar.breaks.padg_7_2026` (tidak dipakai kode; dokumentasi saja) | 🟡 |
| U4 | Periode impor BPS terbaru (s.d. 2026-09 tersedia) | 🟡 |
| U5 | FAOSTAT tanpa bawang putih kering → `hortikultura_produksi` + impor BPS v2/Comtrade 070320 | 🟡 |
| U6 | Regulasi direvisi 20 Nov; sisa: HET Minyakita, tanggal Perbadan 4/5/6/2024, Kepbadan 299/2025, HET beras premium | 🟡 |
| U7 | Ketentuan BPS & FRED → mentah tidak dikirim | 🟡 |
| U8 | Kelayakan uji asimetri: H2 konfirmatori beras & daging sapi, lainnya deskriptif (D-115) | 🟢 |
| U9 | Daya deteksi heterogenitas provinsi: G-het menolak untuk telur & daging ayam (2026-11-22) | 🟡 |
| U10 | Varian representatif dibekukan di G6 | 🟢 |
| U11 | Kecukupan produksi hanya beras | 🟡 |
| U12 | Bibliografi makalah: 55 rujukan diverifikasi Crossref/arXiv/halaman resmi, klaim kuantitatif dicek teks lengkap (D-177, `docs/paper/RUJUKAN.md`) | 🟢 |
| U13 | Izin BI diperoleh 2026-11-20, mencakup redistribusi data turunan (panel provinsi dikirim, D-104) | 🟢 |
| U14 | Populasi provinsi 2025 (tabel BPS, D-123) | 🟢 |
| U15 | `n_kota` per provinsi (situs PIHPS, 110 kota, D-123) | 🟢 |
| U16 | URL Pink Sheet berubah per rilis → `download` resolusi otomatis dari halaman World Bank | 🟢 |
| U17 | Lonjakan harga satu hari: 59 hari ditandai, tidak dihapus | 🟢 |
| U19 | Endpoint PIHPS vs "unduh resmi" | 🔴 `[HUMAN]` |
| U20 | Pemetaan komoditas Bapanas → PIHPS (9 pasangan; Minyakita dikecualikan) | 🟢 |
| U21 | Konversi GKG → beras 0,5762 (rilis BPS, D-123) | 🟢 |
| U22 | `carry_forward` tinggi = rangkaian harga identik (kekakuan atau harga hari sebelumnya dari sumber, tidak dapat dibedakan; D-169); bukan filter | 🟡 |
| U24 | Hosting mentah di Kaggle privat / Drive; akses umum folder Drive tim "siapa saja yang memiliki link" diterima Danen 2026-11-23 (tautan hanya ke anggota) | 🟢 |
| U100 | Kredensial Drive untuk Kaggle (OAuth client + token per anggota) | 🔴 `[HUMAN]` |
| U101 | Keaslian Pink Sheet: identik dengan rilis resmi 3 Nov 2026 | 🟢 |
| U102 | Uji tumpang tindih Comtrade vs BPS → dijalankan pada 2023 (Comtrade API publik, D-133): 14/15 kode cocok persis | 🟢 |
| U103 | Penduduk 2025, n_kota, gkg_beras di data/raw lokal & Drive tim (2026-11-21); sisa snapshot kab/kota (opsional) | 🟡 |
| U104 | `pihps_v1` dipensiunkan ke `_superseded/` (D-102) | 🟢 |
| U105 | Struktur tertanam kini ditanam sebelum penyusutan EB (D-126); batas deteksi δ = 0,2 | 🟢 |
| U106 | p meta-regresi `assoc` tidak konsisten dengan interval (11 baris) & ARI 0 saat k = 1 → diperbaiki D-132 (0/88 baris p < 0,05; ARI NaN) | 🟢 |
| U107 | Bootstrap blok 13 minggu menarik β ke nol (rasio 0,57 / 0,35 / 0,35 pada h 4 / 8 / 12) → interval resmi terlalu konservatif; nasional diatasi D-129, PT & provinsi D-163 (`province_calibrated`); sisa sisi bootstrap H2 & `se_boot` meta-regresi (keterbatasan) | 🟡 |
| U108 | Flag `episode` (grup fx: M2/M3/C2/C2t) memakai informasi sesudah origin → diperbaiki real-time & Task 4 fx dijalankan ulang 2026-11-26 (D-162) | 🟢 |
| U109 | Kebutuhan TPID (kapasitas, toleransi alarm palsu, ambang kebijakan, titik akhir vs kejadian, waktu keputusan) belum divalidasi; panduan `docs/PANDUAN_WAWANCARA_TPID.md`; K4 dijalankan dengan proxy statistik (D-164), penggunaan operasional BLOCKED sampai isu ini selesai; instrumen R1–R12 + matriks status (D-166) | 🔴 `[HUMAN]` |
| U110 | Jendela revisi harga harian PIHPS belum dipastikan → `available_at` konservatif Minggu 00.00 (D-155); FAQ PIHPS: revisi s.d. hari berikutnya (hari kalender/kerja tidak disebut, D-169) | 🔴 `[HUMAN]` |
| U111 | Panel kab/kota Bapanas tidak dapat diakses (SAPA); izin BI untuk data PIHPS per kota belum dipastikan (D-158) | 🔴 `[HUMAN]` |
| U112 | Stok & pasokan SP2KP (mingguan, admin Kemendag) & riwayat PIBC/FDP/GPM tidak tersedia publik → permintaan resmi (D-159); + Proyeksi Neraca Pangan Bapanas & luas tanam/EWS Kementan (D-165) | 🔴 `[HUMAN]` |
| U113 | Sumber non-harga GDELT & CFSv2 diuji sinyalnya: CFSv2 gagal gerbang 5 (D-161); GDELT gagal gerbang 5 lewat BigQuery sandbox (D-165) | 🟢 |
Selesai: U1, U2, U18, U23.

---

## 23. Jebakan & pelajaran yang sudah ditemukan

1. **Urutan baris PIHPS v2 tidak bisa dipercaya** — varian hasil merge di akhir file; `ffill` grup salah menempelkan
   (Cabai Rawit Merah → Gula Pasir). Sebelum diperbaiki, cabai rawit & minyak goreng tampak hilang di banyak provinsi.
   Pelajaran: selalu validasi asumsi struktur file mentah dengan tes pada SEMUA file.
2. **"Data hilang" bisa artefak kode** — periksa loader sebelum menyimpulkan cakupan data buruk.
3. **carry_forward ≠ data jelek** — rangkaian harga identik panjang wajar untuk komoditas diatur.
4. **2024 punya 53 hari Senin** — tes yang mengasumsikan 52 minggu/tahun salah.
5. **Minggu Lebaran tanpa fixing JISDOR** — 5 minggu; tanpa pengisian, LP kehilangan 2 minggu per kejadian.
6. **Spasi akhir pada nama varian** dan ejaan provinsi berbeda antar sumber ("D.I Yogyakarta", "KEP. RIAU").
7. **Pink Sheet seri kosong/nol** — `np.log` pada kolom tak terpakai memicu warning; batasi ke seri yang dibutuhkan.
8. **dw bulanan vs de mingguan** — memakai JISDOR mingguan untuk w membuat dw ≈ de di dalam bulan (kolinear).
9. **Perubahan struktur oleh user** — isi `src/kagami/` dipindah ke `src/`; folder kosong yang tersisa menutupi
   paket sebagai namespace package. Jangan membalikkan perubahan user tanpa bertanya.
10. **CRLF dari `write_text` di Windows** dan heredoc bash yang rapuh (§4.5).
11. **Tes vs data asli**: kegagalan tes bisa karena asumsi tes keliru (bulan sintetis mulai Februari, NaN baris pertama);
    periksa dulu sebelum mengubah kode.
13. **Python Windows tanpa CA lokal** → `CERTIFICATE_VERIFY_FAILED` saat unduh; `download` memakai bundel `certifi`
    (verifikasi SSL tetap aktif; jangan pernah mematikannya).
14. **Membandingkan dengan rilis yang salah** memberi kesimpulan salah (selisih pembulatan dikira file rekayasa); selalu
    cocokkan tanggal rilis/versi sebelum menilai keaslian.
12. **`find_spec` pada nama fungsi** melempar `ModuleNotFoundError` (dipakai di tes wiring dengan try/except).
16. **Item FAOSTAT "Rice" = padi (gabah)**: impor ≈ 0 → rasio impor beras 10⁻⁶. Impor beras ada di "Rice, milled" /
    "Rice, broken" (D-120). Periksa satuan & tahap olah setiap item FAOSTAT sebelum dipakai sebagai eksposur.
17. **Tes yang mengandalkan artefak "belum ada" di root project** gagal begitu hasil asli diunduh ke `results/` (contoh
    `test_runtime`, 2026-11-22). Pakai root kode sementara (`tmp_path` + salinan `configs/`), bukan folder project.
18. **Struktur tertanam harus melewati pemrosesan yang sama dengan data asli**: δ yang ditanam setelah penyusutan EB terdeteksi
    hampir pasti karena derau plasebo tersusut ≈ 0 (U105, diperbaiki D-126).
15. **`pd.factorize` memberi kode −1 untuk NaN/NaT** → `np.bincount` crash, `np.add.at` diam-diam memasukkan ke grup
    terakhir. Buang baris grup kosong sebelum agregasi per grup (D-119).
19. **SE cluster minggu tidak bisa dipercaya pada sub-sampel pendek**: semua regresor LP bervariasi per minggu, jadi rezim ± 70
    minggu dengan ± 40 regresor hampir tanpa derajat bebas; di E2 39% sel rezim 52–104 minggu tampak "signifikan" dengan ±1,96·SE.
    Kalibrasi dengan plasebo (D-127) dan selalu periksa p < 0,05 ⇔ interval tidak memuat nol bila p dan interval dari SE berbeda
    (`assoc` meta-regresi, 2026-11-23).
20. **Bootstrap blok yang lebih pendek dari jendela estimator melemahkan estimasi**: blok 13 minggu vs jendela LP h + L + 2 (14 minggu
    pada h 8) → hampir setiap jendela memotong batas blok, rerata replikasi hanya 0,35–0,57× estimasi, persentil bergeser ke nol
    (U107, D-129). Selalu bandingkan rerata replikasi dengan estimasi asli (`boot_ratio`) sebelum memakai persentil bootstrap.
21. **Streamlit `use_container_width` usang** (dijadwalkan dihapus): app memakai `common.STRETCH` (`width="stretch"` bila
    tersedia, selain itu `use_container_width=True`) agar jalan di versi lama maupun baru; jangan menulis `use_container_width` lagi.
22. **Dummy musim yang dikumpulkan lintas komoditas memperburuk ramalan komoditas diatur** (D-131): M1 dengan dummy bulan +
    Idulfitri kalah dari model tanpa perubahan (beras M0/M1 0,39). Masalah baseline Task 4 adalah pengumpulan tanpa identitas komoditas.
23. **Plotly geo tidak offline & lilitan GeoJSON terbalik** (D-134): subplot `geo` (`go.Choropleth`) selalu mengunduh
    `cdn.plot.ly/un/world_110m.json` walau `visible=False`; d3-geo membutuhkan cincin luar searah jarum jam (kebalikan RFC 7946),
    kalau tidak poligon terbaca sebagai "dunia minus provinsi" (peta jadi kotak penuh). Klik titik baru memicu seleksi
    `st.plotly_chart(on_select=...)` bila `clickmode="event+select"`.
24. **`nan <= 0` bernilai False**: lencana "interval memuat nol" yang ditulis `lo <= 0 <= hi` memberi "terdeteksi" untuk interval NaN.
    Selalu periksa NaN dulu (`viz.style.detection_status`).
25. **Penanda konflik merge ikut ter-commit** (commit 04fc5ec, 4 dokumen): `test_docs_sync` menangkapnya lewat papan WP ganda; cari
    `^<<<<<<< ` di seluruh repo setelah setiap merge.
26. **`st.cache_data` ikut menyimpan hasil "tidak ada"** (D-136): Streamlit Cloud menarik commit baru tanpa me-restart proses, jadi
    `None` yang di-cache sebelum artefak di-push bertahan dan app tetap "Menunggu hasil". Jangan meng-cache ketiadaan; masukkan mtime
    file ke kunci cache. Untuk deploy yang sudah tercemar: "Reboot app" di dasbor Streamlit Cloud.
27. **stdout cp1252 di Windows** (D-138): output CLI yang diarahkan ke file (`python -m kagami all > log`) memakai cp1252, jadi
    `print` berisi τ²/β/≥ crash, dalam kasus nyata setelah 88 menit bootstrap Task 1. `cli.main` kini memaksa UTF-8; skrip ad-hoc
    yang memanggil pipeline tanpa CLI → set `PYTHONIOENCODING=utf-8`. Sama untuk skrip beku validasi prospektif: `integrity_check.py`
    keluar 1 (crash cetak "→") walaupun semua pemeriksaan lolos → jalankan `python -X utf8 …` (D-169); jangan ubah skrip beku.
28. **p tanpa arah menyesatkan** (D-169): DM p dua sisi 0,009 untuk M2 dibaca "M2 lebih baik", padahal DM −2,70 (M2 lebih buruk). Selalu
    tampilkan tanda statistik & p satu sisi untuk hipotesis berarah (`viz.style.dm_summary`).
29. **"±" sebagai "sekitar"** (D-169): "± Rp90" dibaca interval simetris oleh reviewer (interval asli −170..+89). Di teks juri tulis
    "sekitar" atau batas bawah..batas atas.
31. **Hash CRLF vs checkout Linux** (D-170): artefak CSV/MD ditulis CRLF di Windows dan hash-nya dicatat begitu; git menyimpan LF, jadi di
    Streamlit Cloud/clone Linux semua artefak teks tampak "tidak sinkron" (21 di app daring) walau isinya identik. Bandingkan hash dalam
    varian LF & CRLF (`tracking.store`); jangan menyimpulkan lineage rusak dari hash teks lintas OS.
32. **Teks plotly bertumpuk tidak tertangkap tes** (D-172): anotasi `add_vline(annotation_position="top")` masuk margin atas dan menimpa
    subjudul; titik tengah garis yang melompati lapisan jatuh tepat di kolom simpul; judul panel `facet_col` & legenda berposisi pecahan
    tinggi plot menabrak teks lain di layar sempit; Plotly tidak membungkus judul sehingga terpotong di ponsel. Periksa di browser: kotak
    setiap `text` SVG beririsan atau keluar bingkai (tab & expander dibuka) di 1280/1024/375 px. `st.dataframe` digambar di kanvas.
30. **Dua rumus untuk angka yang sama** (D-169): app memakai PT·x, findings exp(PT·ln(1 + x)) − 1 → angka berbeda di ekor. Satu fungsi
    (`viz.plots.scenario_change`) + tes yang mencocokkan angka app dengan tabel findings.
33. **Artefak app di folder yang di-ignore git** (D-176): halaman baru membaca `data/processed/` yang seluruhnya di-ignore, sehingga app
    daring (membaca repo) akan "Menunggu hasil" walaupun lokal normal. Setiap artefak baru di `need(...)`/`load(...)` harus ikut git
    (`test_wiring.test_app_artifacts_not_gitignored`).
34. **MiKTeX menggantung tanpa pesan** (D-177): AutoInstall "tanya" memunculkan dialog GUI untuk paket yang belum terpasang, dan
    `kpsewhich`/`pdflatex` dari shell agent diam menunggu. Selalu `pdflatex --disable-installer`; cek paket dengan `find` di folder
    MiKTeX, bukan `kpsewhich`. Tidak terpasang: `natbib`, `multirow`, `unicode-math`, `placeins`, `threeparttable`.
35. **Float LaTeX `[t]` yang terlalu tinggi menahan semua gambar sesudahnya** (D-177): gambar > `\topfraction` tanpa opsi `p` tidak pernah
    bisa ditempatkan, lalu seluruh antrean gambar tumpah sesudah daftar pustaka. Pakai `[!tbp]`, pecah gambar tinggi, dan periksa halaman
    PDF hasil render, bukan hanya log.
36. **Dua server Streamlit di port yang sama** (D-176): di Windows proses kedua tetap bisa mengikat port 8501, sehingga permintaan bisa
    dilayani server lama dengan kode basi. Cek `netstat -ano | grep :8501`; untuk pemeriksaan pakai `kagami-app-8511`.

---

## 24. Larangan

- Mengubah/menimpa file di `data/raw/` atau menulis ke `raw_dir`.
- Angka analisis tersembunyi di kode; mengubah `params.yaml` setelah G6 tanpa catatan deviasi.
- Logika analisis di notebook atau app; estimasi saat runtime di app.
- Split acak per baris; memakai informasi masa depan di Task 4.
- Menghapus data diam-diam; mencampur varian berbeda dalam satu seri.
- Melihat β Task 1 sebelum MDE (WP-09) selesai.
- Memasang statsmodels/linearmodels; menambah dependensi tanpa alasan dan tanpa memperbarui pyproject.
- Mengirim data mentah tanpa hak ke zip juri; membuat dataset Kaggle mentah publik.
- Klaim kausal/prediktif (§20).
- Mengerjakan tugas `[HUMAN]` (email, login akun Kaggle/Google, unggah, video) — siapkan bahannya saja.
- Menjalankan perintah git yang mengubah index/riwayat/branch/remote (commit, push, add, dll.); command copas hanya bila diminta (§4.6).
- `git init` ulang, membuat folder `src/kagami/`, menambah `src` ke PYTHONPATH.
- Membalikkan perubahan file yang dibuat user/OneDrive tanpa bertanya.

---

## 25. Glosarium

| Istilah | Arti |
|---|---|
| PIHPS | Pusat Informasi Harga Pangan Strategis (Bank Indonesia) — harga eceran harian per provinsi |
| JISDOR | Jakarta Interbank Spot Dollar Rate (BI) — kurs IDR/USD harian |
| Pink Sheet / CMO | World Bank Commodity Price Data — harga dunia bulanan USD |
| HET / HAP / HPP | Harga Eceran Tertinggi / Harga Acuan Pembelian-Penjualan / Harga Pembelian Pemerintah |
| TPID | Tim Pengendalian Inflasi Daerah (pengguna sasaran) |
| LP | local projections (Jordà 2005) |
| PT | rasio pass-through β/γ |
| MDE | minimum detectable effect (α 0,05, power 0,80) |
| EB | penyusutan empirical Bayes |
| DL / REML | estimator τ² DerSimonian–Laird / restricted maximum likelihood |
| BH / FDR | Benjamini–Hochberg false discovery rate |
| ARI | adjusted Rand index |
| DM / HAC / HLN | uji Diebold–Mariano / varians tahan heteroskedastisitas-autokorelasi / koreksi Harvey–Leybourne–Newbold |
| CR1 / CR2 | koreksi SE cluster (CR2 = Bell–McCaffrey, untuk cluster sedikit) |
| GKG | gabah kering giling |
| Tingkat A/B/C | tingkat reproduksi juri (app / data turunan / unduh ulang) |
| G6, G-power, G-het, G7, G8 | gerbang keputusan (§13) |
| WP | work package di `docs/WORKPLAN.md` |
| `[HUMAN]` | tugas yang harus dilakukan manusia |

---

## 26. Template

### 26.1 Entri SESSION_LOG (di atas bagian anggota sendiri, ≤ 10 baris; handoff: `docs/HANDOFF.md`)
```
## YYYY-MM-DD — <Nama>: WP-xx ✅/🔶 (judul singkat)
- Yang diimplementasi + file utama + tes baru.
- Artefak ditulis (jumlah baris) + angka penting dari data asli.
- Bug/temuan + D-xxx / U-xx terkait.
- Belum selesai / diblokir oleh apa.
- Berikutnya: WP-.. → WP-..
```

### 26.2 Entri DECISIONS
```
### D-<nnn> — Judul keputusan · FINAL|PROVISIONAL|DIGANTI oleh D-<mmm> · YYYY-MM-DD (WP-xx) · <Nama>
(nomor baru: Danen D-100+, Ardell D-200+, Abi D-300+)
Apa yang diputuskan, alternatif yang ditolak dan alasannya, bukti (angka), dampak hilir.
(Setelah G6, tambahkan label DEVIASI PRAREGISTRASI bila mengubah hal yang dibekukan.)
```

### 26.3 Baris OPEN_ISSUES
```
| U<n> | Isu | Default sementara | Tenggat | WP | 🔴/🟡/🟢 + catatan resolusi bertanggal |
(nomor baru: Danen U100+, Ardell U200+, Abi U300+)
```

### 26.4 Ringkasan akhir turn ke user
Apa yang berubah (file, artefak), angka penting, temuan yang butuh keputusan user, yang belum diverifikasi,
lalu satu pertanyaan langkah berikutnya.
