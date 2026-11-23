# Pembagian Tugas — KAGAMI

Tiga anggota, tiga jalur yang berjalan bersamaan. Jalur teknis Danen dan Ardell **tidak saling menunggu**: setiap
konsumen membangun dan menguji kodenya dengan data sintetis yang mengikuti kontrak artefak (`src/utils/artifacts.py`),
lalu menjalankan ulang dengan data asli ketika artefak produsen terbit. Abi tidak menyentuh source code.
Status WP: papan di `docs/WORKPLAN.md` (kolom PIC). Koordinasi asinkron lewat **handoff** (`docs/HANDOFF.md`, file di `docs/handoff/`).

> **Pengambilalihan 2026-11-23 (D-130).** Danen mengambil alih semua WP dan file jalur B (Ardell) dan jalur C (Abi). Tabel §1–§3
> di bawah adalah pembagian awal (riwayat); sejak tanggal ini pemilik semua file di §3 = Danen, dan handoff terbuka ke Ardell/Abi
> menjadi daftar kerja Danen. Makalah (WP-33 bagian PDF), video, dan unggah submission ditunda; WP-33 bagian `results/findings.md`
> tetap dikerjakan karena artefak `ship` dan dibaca app halaman 6.

## 1. Peran

| Anggota | Jalur | Inti tanggung jawab | WP |
|---|---|---|---|
| **Danen** | A — Tahap 0, estimator nasional, uji & evaluasi, robustness | Tahap 0 sisa (episode, panel wilayah, MDE, QA), Task 1 estimator (LP nasional, event study), Task 2 uji heterogenitas & struktur tertanam, Task 3 Kendall, Task 4 evaluasi DM & ablation, robustness & validasi, keputusan G6/G-power, infra (Drive, Kaggle, CLI) | WP-06, 08, 09, 10, 11 (keputusan + hash), 13, 14, 18, 21, 22, 27, 28, 29, 30 |
| **Ardell** | B — Data mining, inferensi provinsi, prediksi & produk | Tabel referensi, Task 1 sisi provinsi (deviasi, bootstrap & plasebo, EB & fitur respons), Task 2 clustering & stabilitas, Task 3 meta-regresi & FE, Task 4 fitur & model, app, paket juri | WP-07, 15, 16, 17, 19, 20, 23, 24, 25, 26, 31, 32 |
| **Abi** | C — Riset, data manual, makalah, video, administrasi (tanpa kode) | Pengumpulan data manual, verifikasi regulasi & pustaka, naskah praregistrasi, makalah, findings, audit klaim, video, email izin, unggah | WP-11 (naskah), 33, 34, 35 + input data manual untuk WP-07 & WP-10 |

Alasan pembagian (D-105, menggantikan pembagian awal): setiap Task dipegang **berdua**, bukan satu Task per orang, dan beban
kira-kira seimbang (sekitar 19 satuan kerja per orang). Rantai Task 1 dipotong di satu titik yang kontraknya jelas: Danen
memegang estimator nasional (WP-13/14) dan menerbitkan `build_design` + `fit_lp` pada **22 Nov**; Ardell memegang sisi
provinsi (WP-15/16/17) dan menerbitkan P2. Hilirnya bersilang: Danen menguji (WP-18, 21, 22, 27) keluaran yang dibuat Ardell,
dan Ardell membangun (WP-19, 20, 23–26) di atas estimator Danen. Semua serah-terima memakai kontrak artefak + data sintetis, jadi
tidak ada yang menunggu.

| Task | Danen | Ardell |
|---|---|---|
| Tahap 0 | WP-06 episode, 08 panel wilayah, 09 MDE, 10 QA, 11 G6 | WP-07 tabel referensi |
| Task 1 | WP-13 LP nasional, 14 event study | WP-15 deviasi provinsi, 16 bootstrap & plasebo, 17 EB & fitur |
| Task 2 | WP-18 heterogenitas (G-het), 21 struktur tertanam | WP-19 clustering, 20 stabilitas |
| Task 3 | WP-22 Kendall | WP-23 meta-regresi, 24 FE interaksi |
| Task 4 | WP-27 evaluasi DM & ablation | WP-25 fitur as-of, 26 model M0–M3 |
| Robustness / produk | WP-28, 29, 30 | WP-31 app, 32 paket juri |

## 2. Prinsip kerja paralel

1. **Kontrak dulu, data belakangan.** Skema artefak sudah dibekukan di `src/utils/artifacts.py`. Konsumen tidak perlu
   menunggu artefak asli: buat generator data sintetis berskema sama di tes masing-masing.
2. **Data sintetis berlabel "dummy"** tidak boleh masuk makalah, app final, atau `results/` (proposal §9.4).
3. **Titik terbit (§5) bukan titik tunggu.** Sebelum titik terbit, konsumen mengerjakan kode + tes sintetis + WP lain;
   sesudahnya cukup menjalankan ulang tahapnya dengan data asli.
4. **Kepemilikan file tegas (§3).** Jangan mengedit file milik anggota lain; minta perubahan lewat handoff `PERMINTAAN`.
5. **Perubahan kontrak hanya aditif** (tambah kolom/artefak, tidak mengganti/menghapus) dan diumumkan lewat handoff `KEPUTUSAN`.
6. **Tanpa rapat.** Pesan antar anggota = handoff (+ versi pendek di chat); catatan kerja pribadi = bagian sendiri di SESSION_LOG; status = papan WORKPLAN.

## 3. Kepemilikan file

| Area | Danen | Ardell | Abi |
|---|---|---|---|
| `src/data/` | `drivers.py` (episode), `panel.py`, `qa.py` | `reference.py`, tambahan loader sumber manual di `loaders.py` | – |
| `src/features/` | – | `response.py`, `clustering.py`, `forecast.py` | – |
| `src/models/` | `local_projection.py`, `event_study.py`, `association.py::kendall_exact` | `deviations.py`, `clustering.py`, `forecasting.py`, `association.py::meta_regression`/`fe_interaction` | – |
| `src/evaluation/` | `power.py`, `heterogeneity.py`, `planted.py`, `forecast_eval.py`, `robustness.py`, `regimes.py`, `asymmetry.py`, `calibration.py` | `inference.py`, `stability.py` | – |
| `src/pipelines/` | `stage0.py`, `task1.py`, `task3.py`, `robustness.py` | `task2.py`, `task4.py`, `package.py` | – |
| `src/viz/plots.py` | tambah fungsi untuk nb00/01/05 (aditif) | pemilik file; fungsi untuk app & nb02/03/04 | – |
| `src/stats/` | pemilik (fungsi baru + tes) | boleh menambah fungsi baru (aditif) + tes | – |
| `src/utils/`, `src/cli.py`, `configs/runtime.yaml` | pemilik (infra: config, runtime, Drive, CLI) | perubahan lewat handoff `PERMINTAAN` | – |
| `src/tracking/`, `logs/`, `app/pages/7_Evaluasi_Eksekusi.py`, `tests/test_tracking.py` | pemilik (log eksekusi & evaluasi, WP-36, D-137) | evaluator tahap miliknya boleh ditambah (aditif) | – |
| `notebooks/` | `00_stage0_data`, `01_task1_profiles`, `03_task3_association`, `05_robustness` | `02_task2_patterns`, `04_task4_forecast` (Ardell juga menjalankan `01` untuk P2) | – |
| `app/` | – | pemilik | menyediakan teks/copy di `docs/paper/app_copy.md` |
| `configs/params.yaml` | semua bagian kecuali milik Ardell | `clustering`, `association`, `forecast`, `scenario` (parameter `inference` & `shrinkage` dipakai Ardell di WP-16/17 tetapi dibekukan Danen di G6; perubahan lewat handoff `PERMINTAAN`) | – |
| `configs/commodities.yaml` | pemilik | – | – |
| `configs/sources.yaml` | – | pemilik entri sumber manual baru | – |
| `tests/` | tes modul miliknya | tes modul miliknya (+ generator sintetis) | – |
| `data/raw/manual_*/` | – | – | pemilik isi CSV (§6.2) |
| `docs/PREREGISTRATION.md` | keputusan + hash | – | naskah |
| `docs/paper/`, `results/findings.md` | menyediakan angka (lewat artefak) | menyediakan angka (lewat artefak) | pemilik |
| `README.md` | – | – | pemilik (bagian deskripsi & GitHub) |

Satu file yang dipakai dua orang (`association.py`, dan pipeline yang memanggil fungsi pemilik lain) dibagi per **fungsi**: tiap orang
hanya mengubah badan fungsi WP-nya di branch `feat/<fungsi>` sendiri, sehingga merge tidak bentrok. Pemilik pipeline menulis kerangka dan
memanggil fungsi pemilik lain menurut kontrak docstring; blok pemanggil fungsi sendiri boleh ditambahkan pemilik fungsi lewat merge/PR kecil
terpisah (kabari lewat handoff `TERBIT`).

File bersama (`CLAUDE.md`, `docs/WORKPLAN.md`, `docs/SESSION_LOG.md`, `docs/DECISIONS.md`, `docs/OPEN_ISSUES.md`,
`src/utils/artifacts.py`, `pyproject.toml`): aturan di §7.

## 4. Jadwal per anggota (20–29 Nov 2026)

| Tanggal | Danen (A) | Ardell (B) | Abi (C) |
|---|---|---|---|
| Jum 20 | Prasyarat kolaborasi (§8); **WP-06** episode + `mark_episode_weeks` | **WP-07** kerangka tabel referensi (loader manual, skema, NaN-aman); generator sintetis Task 1 (panel provinsi, profil nasional) | **WP-35** email izin BI (U13 + U24); cek endpoint PIHPS (U19); mulai data manual (§6.2) |
| Sab 21 | **WP-08** panel wilayah → **terbit P1**; keputusan **G6** (varian, bobot pakan, grup fokus) + hash | **WP-25** fitur as-of (pakai `panel_weekly` & penggerak yang sudah ada); kerangka **WP-15/16/17** (sintetis) | Naskah **PREREGISTRATION** (G6); data manual: PADG 7/2026 (U3), populasi (U14), n_kota (U15) |
| Min 22 | **WP-09** MDE; **WP-13** `build_design` + `fit_lp` lolos tes → handoff `TERBIT` ke Ardell; generator sintetis Task 4 untuk **WP-27** | **WP-26** model M0–M3 (sintetis → asli setelah P1); **WP-19** clustering (sintetis) | Faktor GKG→beras (U21), verifikasi regulasi JDIH (U6), pemetaan Bapanas (U20); makalah: pendahuluan |
| Sen 23 | **G-power**; **WP-13** LP nasional final; **WP-14** event study; **WP-10** QA | **WP-15** deviasi provinsi (asli, pakai `fit_lp`); run **WP-26** penuh di Kaggle → `forecast_preds` | Makalah: kajian pustaka + verifikasi rujukan (U12) |
| Sel 24 | Mulai **WP-28** Tier 1; **WP-18**, **WP-22** (sintetis) | **WP-16** bootstrap & plasebo (Kaggle); **WP-17** EB & fitur → jalankan `task1` penuh → **terbit P2**; **WP-07** final dengan data manual Abi → **terbit P3** | Makalah: dataset & metode (dari METHODS.md), matriks evaluasi; naskah video |
| Rab 25 | **WP-18** asli (G-het); **WP-22** Kendall asli; **WP-27** evaluasi DM & ablation → **terbit P4** | **WP-19** asli; **WP-20** stabilitas; mulai **WP-23** meta-regresi | Copy app (`docs/paper/app_copy.md`); storyboard video |
| Kam 26 | **WP-21** struktur tertanam; **WP-28**; **WP-29** validasi (pakai P4) | **WP-23**, **WP-24** (asli); **WP-31** app mulai | Makalah: kerangka hasil & analisis (tabel/gambar yang akan diisi) |
| Jum 27 | **Pembekuan hasil**; **WP-30** opsional; handoff `ANGKA-MAKALAH` ke Abi | **WP-31** app final; Task 1–3 final → **terbit P5** | **WP-33** isi hasil & analisis + `results/findings.md` |
| Sab 28 | Dukungan **G7** (jalan ulang Task 1 versi wilayah) | **WP-32** paket juri + **G7** | **WP-34** audit klaim (G8); rekam video |
| Min 29 | Perbaikan bug saja | Perbaikan bug saja | **Submit**: makalah PDF + zip + video; GitHub publik (opsional) |

Catatan jadwal: G-het bergeser dari 24 ke 25 Nov karena bergantung pada keluaran bootstrap/plasebo Task 1 (P2).
Sebelum P2, Danen mengisi 24 Nov dengan WP-28 dan kode WP-18/22 versi sintetis; sebelum `fit_lp` terbit (22 Nov), Ardell
mengisi 21–22 Nov dengan WP-25/26/19 dan kerangka WP-15/16/17 versi sintetis, sehingga tidak ada hari kosong. Bila WP-13
telat, WP-15 tetap dikembangkan dengan sintetis dan dijalankan asli begitu `fit_lp` terbit.

## 5. Titik terbit artefak (bukan titik tunggu)

| Kode | Kapan | Penerbit | Artefak | Konsumen | Sebelum terbit konsumen mengerjakan |
|---|---|---|---|---|---|
| P1 | 21 Nov | Danen | `drivers_weekly`, `episodes`, `fx_variation`, `panel_weekly_region` | Ardell (Task 4, WP-15/16/17) | WP-25/26 dengan `panel_weekly` + `build_national_drivers` di memori, kolom `episode` = 0 sementara; WP-15/16/17 dengan sintetis |
| P2 | 24 Nov | Ardell (jalankan `task1` penuh dengan kode WP-13/14 Danen di `dev`) | `profiles`, `boot_replicates`, `placebo_stats`, `events`, `response_features` | Danen (WP-18, 21, 22, 28), Ardell (Task 2, 3) | WP-18/21/22/28 dan WP-19–24 dengan generator sintetis berskema sama |
| P3 | 24 Nov | Ardell | `concordance`, `exposure`, `regulation`, `province_features` | Danen (WP-22 Kendall), Ardell (WP-23/24), Abi (makalah: dataset) | – (Task 1 tidak membutuhkannya) |
| P4 | 25 Nov | Ardell (`forecast_preds`, 23–24 Nov) → Danen (`forecast_eval`, `ablation`, 25 Nov) | `forecast_eval`, `ablation` | Danen (WP-29 validasi V2), Ardell (app), Abi | WP-27 dengan `forecast_preds` sintetis; WP-28 Tier 1 lebih dulu |
| P5 | 27 Nov | Danen & Ardell | semua artefak `ship` | Abi (WP-33/34), Ardell (WP-31/32) | Abi menulis bagian makalah yang tidak butuh angka |

Serah-terima **kode** (bukan artefak, lewat `dev` + handoff `TERBIT`): Danen → Ardell `build_design` & `fit_lp` (WP-13) paling lambat
22 Nov; Ardell → Danen `ward_labels` & `select_k` (WP-19) paling lambat 23 Nov untuk WP-21; Ardell → Danen `rolling_predictions`
(WP-26) paling lambat 24 Nov untuk WP-27.

Cara terbit: jalankan notebook tahapnya → sel "Simpan ke Drive tim" mengunggah otomatis ke folder Drive tim
(https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D; lokal: `python -m kagami drive-push <tahap>`) → konsumen mengambilnya otomatis di sel "Cek input" →
kirim handoff jenis `TERBIT` (`docs/HANDOFF.md`) + versi pendek di chat.

## 6. Rincian jalur Abi (tanpa source code)

### 6.1 Daftar tugas
| Tugas | Keluaran | Tenggat | Untuk |
|---|---|---|---|
| ~~Email permohonan izin BI (U13, U24)~~ | **selesai**: izin BI sudah diperoleh (2026-11-20) | – | semua |
| Cek apakah endpoint `WebSite/TabelHarga/GetGridDataDaerah` = fitur unduh resmi PIHPS (U19) | catatan + tangkapan layar di OPEN_ISSUES U19 | 21 Nov | Danen |
| Tanggal berlaku & isi PADG No. 7/2026 (U3) | tanggal + sumber di OPEN_ISSUES U3 (Danen memasukkan ke params) | 21 Nov | Danen |
| Data manual §6.2 | CSV di `data/raw/manual_*/` | 22–23 Nov | Ardell (WP-07), Danen (WP-10) |
| Naskah praregistrasi | `docs/PREREGISTRATION.md` bagian naskah | 21 Nov | G6 |
| Bibliografi: lengkapi & verifikasi rujukan "belum diverifikasi" (U12) | `docs/paper/references.md` | 23 Nov | makalah |
| Makalah bagian tanpa angka: judul, abstrak draf, pendahuluan, kajian pustaka, dataset, metode, perbedaan dengan solusi sebelumnya, matriks evaluasi | `docs/paper/makalah.md` | 26 Nov | WP-33 |
| Teks/copy untuk 6 halaman app | `docs/paper/app_copy.md` | 25 Nov | Ardell (WP-31) |
| Naskah & storyboard video demo | `docs/paper/video_script.md` | 25 Nov | video |
| Hasil, analisis, kesimpulan + `results/findings.md` (angka dari artefak P5) | makalah lengkap | 27 Nov | WP-33 |
| Audit klaim (tabel "Jangan tulis / Tulis", CLAUDE.md §20) pada makalah, app, findings | handoff `PERMINTAAN` berisi daftar koreksi | 28 Nov | G8 |
| Rekam video, ekspor PDF makalah, unggah ke Drive & form pendaftaran Gelombang 2 | submission | 28–29 Nov | lomba |

### 6.2 Skema data manual (file baru; jangan menimpa file mentah yang sudah ada)
Isi dengan Excel/Google Sheets lalu simpan sebagai CSV UTF-8. Ardell mendaftarkan file-file ini di `configs/sources.yaml`
dan membuat loader-nya; kode WP-07 harus tetap jalan bila file belum ada (nilai NaN + ditandai).

| File | Kolom | Sumber yang disarankan |
|---|---|---|
| ~~`data/raw/manual_population/populasi_provinsi.csv`~~ | **tidak perlu**: CSV penduduk 2025 BPS sudah diunduh Danen (lokasi `data/raw/bps_kependudukan/`, U14/U103) | – |
| `data/raw/manual_pihps/n_kota.csv` | `province_id, province, n_kota, kota_list, source_url` (34 provinsi) | Situs/FAQ PIHPS: daftar kota sampel |
| `data/raw/manual_conversion/gkg_beras.csv` | `year, factor, source_url, note` | BPS: angka konversi GKG ke beras |
| `data/raw/manual_regulation/regulation_verified.csv` | kolom sama dengan `regulation_history.csv` + `jdih_url, verified_on` | JDIH Bapanas / Kemendag |
| `data/raw/manual_mapping/bapanas_pihps_map.csv` | `commodity_bapanas, commodity, match_quality (exact/close/none), note` | 13 komoditas Bapanas → 10 id KAGAMI |

## 7. Aturan file bersama

| File | Aturan |
|---|---|
| `docs/WORKPLAN.md` | Setiap anggota hanya mengubah baris WP dengan PIC dirinya (status, catatan). |
| `docs/SESSION_LOG.md` | Entri baru di atas **bagian sendiri** (`## Danen` / `## Ardell` / `## Abi`), judul `### 2026-11-21 — Danen: WP-08 ✅`. |
| `docs/handoff/` | Satu file per handoff; pengirim membuat, penerima hanya mengubah `status` & kotak centang (`docs/HANDOFF.md` §6). |
| `docs/DECISIONS.md` | Nomor per anggota agar tidak bentrok: Danen **D-100–D-199**, Ardell **D-200–D-299**, Abi **D-300–D-399**. |
| `docs/OPEN_ISSUES.md` | Isu baru: Danen **U100+**, Ardell **U200+**, Abi **U300+**; isu lama tetap nomornya. |
| `CLAUDE.md` | §9: ubah hanya baris modul milik sendiri. §2: tiap anggota memperbarui baris statusnya. Bagian lain: lewat SESSION_LOG. |
| `src/utils/artifacts.py` | Hanya penambahan (artefak/kolom baru) oleh pemilik produsen; umumkan lewat handoff `KEPUTUSAN`; perbarui ARCHITECTURE §5. |
| `pyproject.toml` | Tambah dependensi/subpaket hanya bila perlu; umumkan lewat handoff `KEPUTUSAN`. |
| `configs/params.yaml` | Bagian milik sendiri (§3). Setelah G6 setiap perubahan = DEVIASI PRAREGISTRASI (DECISIONS). |
| `tests/conftest.py` | Jangan diubah tanpa catatan; fixture baru di file tes masing-masing. |

## 8. Prasyarat kolaborasi (Danen, 20 Nov)
1. **Repo GitHub** sudah ada: `danenftyessir/kurs-associated-grocery-analysis-of-markets-in-indonesia` (branch `main`).
   `.gitignore` mengecualikan data mentah (kecuali `checksums.csv` & `manual_regulation/`), `data/interim/`, `data/processed/`,
   `results/` (kecuali `findings.md`), `dist/`, cache, kredensial. Tiap anggota teknis bekerja di clone sendiri. Branch hanya `main` (stabil), `dev`
   (integrasi), dan `feat/<fungsi>` (fungsi pekerjaannya, maks 3 kata, mis. `feat/reference-tables`; dari `dev`, masuk ke `dev` lewat `git merge --no-ff` lalu push
   atau PR; **tidak dihapus** setelah merge; pesan commit `<tipe>: <deskripsi>` tanpa kode dan tanpa `Co-Authored-By`, mis. `feat: tambah tabel konkordansi`;
   D-108, D-117); `dev` → `main` lewat PR saat stabil (D-103,
   CLAUDE.md §4.6). Tidak ada commit langsung ke `main`/`dev`. Branch `dev` dibuat Danen dari `main` sebelum mulai. Bekerja bersamaan di satu folder OneDrive berisiko konflik file.
   **Agent tidak pernah commit/push**; command git siap copas disiapkan agent hanya bila diminta (CLAUDE.md §4.6). Commit, push, PR,
   dan merge dijalankan anggota sendiri. Abi tidak perlu git: kirim file lewat Drive, Danen/Ardell yang meng-commit.
2. **Folder Drive tim** https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D (D-100): artefak semua tahap (push/pull otomatis) dan `data/raw/` (Danen: `drive-push-raw`;
   anggota: `drive-pull-raw`, D-101). Bagikan **hanya** ke akun Ardell & Abi (Editor), bukan "siapa saja yang punya link" (U24).
   Kaggle butuh token OAuth per anggota sebagai Secret `KAGAMI_DRIVE_TOKEN` (`docs/NOTEBOOKS.md` §Persiapan).
3. **Kaggle**: dataset privat `kagami-code` dibuat Danen lalu dibagikan ke Ardell sebagai collaborator (`kagami-raw` opsional);
   notebook masing-masing dijalankan di akun sendiri.
4. Ardell & Danen: `pip install -e ".[dev]"`, `pytest` hijau sebelum mulai.

## 9. Definisi selesai per anggota
- **Danen & Ardell:** WP ✅ di papan, `pytest` hijau, CLAUDE.md §9 diperbarui untuk modul sendiri, artefak asli terbit
  (bila WP menghasilkan artefak) + handoff `TERBIT`, entri SESSION_LOG.
- **Abi:** file keluaran ada di lokasi §6, isu terkait di OPEN_ISSUES diperbarui, handoff (`DATA-MANUAL`/`BLOKIR`/dll.) dikirim.
