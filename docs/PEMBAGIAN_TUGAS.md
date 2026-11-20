# Pembagian Tugas — KAGAMI

Tiga anggota, tiga jalur yang berjalan bersamaan. Jalur teknis Danen dan Ardell **tidak saling menunggu**: setiap
konsumen membangun dan menguji kodenya dengan data sintetis yang mengikuti kontrak artefak (`src/utils/artifacts.py`),
lalu menjalankan ulang dengan data asli ketika artefak produsen terbit. Abi tidak menyentuh source code.
Status WP: papan di `docs/WORKPLAN.md` (kolom PIC). Koordinasi asinkron lewat **handoff** (`docs/HANDOFF.md`, file di `docs/handoff/`).

## 1. Peran

| Anggota | Jalur | Inti tanggung jawab | WP |
|---|---|---|---|
| **Danen** | A — Data & ekonometrika inti (jalur kritis) | Tahap 0 sisa, MDE, Task 1 (LP, event study, deviasi, bootstrap, plasebo, EB), robustness, keputusan G6/G-power | WP-06, 08, 09, 10, 11 (keputusan + hash), 13, 14, 15, 16, 17, 28, 29, 30 |
| **Ardell** | B — Data mining, prediksi & produk | Tabel referensi, Task 2 (heterogenitas, clustering, stabilitas, struktur tertanam), Task 3 (asosiasi), Task 4 (rolling-origin), app, paket juri | WP-07, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 31, 32 |
| **Abi** | C — Riset, data manual, makalah, video, administrasi (tanpa kode) | Pengumpulan data manual, verifikasi regulasi & pustaka, naskah praregistrasi, makalah, findings, audit klaim, video, email izin, unggah | WP-11 (naskah), 33, 34, 35 + input data manual untuk WP-07 & WP-10 |

Alasan pembagian: rantai WP-06 → 08 → 09 → 13 → 15 → 16 → 17 bersifat berurutan, jadi dipegang satu orang agar tidak ada
serah-terima di tengah rantai. Ardell memegang semua tahap yang **mengonsumsi** keluaran rantai itu, yang bisa dikembangkan
penuh dengan data sintetis.

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
| `src/features/` | `response.py` | `clustering.py`, `forecast.py` | – |
| `src/models/` | `local_projection.py`, `deviations.py`, `event_study.py` | `clustering.py`, `association.py`, `forecasting.py` | – |
| `src/evaluation/` | `power.py`, `inference.py`, `robustness.py` | `heterogeneity.py`, `stability.py`, `planted.py`, `forecast_eval.py` | – |
| `src/pipelines/` | `stage0.py`, `task1.py`, `robustness.py` | `task2.py`, `task3.py`, `task4.py`, `package.py` | – |
| `src/viz/plots.py` | tambah fungsi untuk nb00/01/05 (aditif) | pemilik file; fungsi untuk app & nb02/03/04 | – |
| `src/stats/` | pemilik (fungsi baru + tes) | boleh menambah fungsi baru (aditif) + tes | – |
| `notebooks/` | `00_stage0_data`, `01_task1_profiles`, `05_robustness` | `02_task2_patterns`, `03_task3_association`, `04_task4_forecast` | – |
| `app/` | – | pemilik | menyediakan teks/copy di `docs/paper/app_copy.md` |
| `configs/params.yaml` | semua bagian kecuali milik Ardell | `clustering`, `association`, `forecast`, `scenario` | – |
| `configs/commodities.yaml` | pemilik | – | – |
| `configs/sources.yaml` | – | pemilik entri sumber manual baru | – |
| `tests/` | tes modul miliknya | tes modul miliknya (+ generator sintetis) | – |
| `data/raw/manual_*/` | – | – | pemilik isi CSV (§6.2) |
| `docs/PREREGISTRATION.md` | keputusan + hash | – | naskah |
| `docs/paper/`, `results/findings.md` | menyediakan angka (lewat artefak) | menyediakan angka (lewat artefak) | pemilik |
| `README.md` | – | – | pemilik (bagian deskripsi & GitHub) |

File bersama (`CLAUDE.md`, `docs/WORKPLAN.md`, `docs/SESSION_LOG.md`, `docs/DECISIONS.md`, `docs/OPEN_ISSUES.md`,
`src/utils/artifacts.py`, `pyproject.toml`): aturan di §7.

## 4. Jadwal per anggota (20–29 Nov 2026)

| Tanggal | Danen (A) | Ardell (B) | Abi (C) |
|---|---|---|---|
| Jum 20 | Prasyarat kolaborasi (§8); **WP-06** episode + `mark_episode_weeks` | **WP-07** kerangka tabel referensi (loader manual, skema, NaN-aman); generator sintetis Task 1 | **WP-35** email izin BI (U13 + U24); cek endpoint PIHPS (U19); mulai data manual (§6.2) |
| Sab 21 | **WP-08** panel wilayah → **terbit P1**; keputusan **G6** (varian, bobot pakan, grup fokus) + hash | **WP-25** fitur as-of (pakai `panel_weekly` & penggerak yang sudah ada) | Naskah **PREREGISTRATION** (G6); data manual: PADG 7/2026 (U3), populasi (U14), n_kota (U15) |
| Min 22 | **WP-09** MDE; **WP-10** QA (pakai tabel pemetaan Bapanas dari Abi bila sudah ada) | **WP-26** model M0–M3 (sintetis → asli setelah P1) | Faktor GKG→beras (U21), verifikasi regulasi JDIH (U6), pemetaan Bapanas (U20); makalah: pendahuluan |
| Sen 23 | **G-power**; **WP-13** LP nasional; **WP-14** event study | **WP-27** evaluasi DM & ablation; run Task 4 penuh di Kaggle → **terbit P4** | Makalah: kajian pustaka + verifikasi rujukan (U12) |
| Sel 24 | **WP-15** deviasi; **WP-16** bootstrap & plasebo (Kaggle); **WP-17** EB & fitur → **terbit P2** | **WP-07** final dengan data manual Abi → **terbit P3**; **WP-18**, **WP-19** (sintetis) | Makalah: dataset & metode (dari METHODS.md), matriks evaluasi; naskah video |
| Rab 25 | Cadangan run Kaggle Task 1; mulai **WP-28** Tier 1 | Run asli **WP-18** (G-het) & **WP-19**; **WP-20**, **WP-21** | Copy app (`docs/paper/app_copy.md`); storyboard video |
| Kam 26 | **WP-28**, **WP-29** validasi (pakai P4) | **WP-22**, **WP-23**, **WP-24** (asli) ; **WP-31** app mulai | Makalah: kerangka hasil & analisis (tabel/gambar yang akan diisi) |
| Jum 27 | **Pembekuan hasil**; **WP-30** opsional; handoff `ANGKA-MAKALAH` ke Abi | **WP-31** app final; Task 2–3 final → **terbit P5** | **WP-33** isi hasil & analisis + `results/findings.md` |
| Sab 28 | Dukungan **G7** (jalan ulang Task 1 versi wilayah) | **WP-32** paket juri + **G7** | **WP-34** audit klaim (G8); rekam video |
| Min 29 | Perbaikan bug saja | Perbaikan bug saja | **Submit**: makalah PDF + zip + video; GitHub publik (opsional) |

Catatan jadwal: G-het bergeser dari 24 ke 25 Nov karena bergantung pada keluaran bootstrap/plasebo Task 1 (P2);
Ardell mengisi 24 Nov dengan WP-07 final dan WP-18/19 versi sintetis sehingga tidak ada hari kosong.

## 5. Titik terbit artefak (bukan titik tunggu)

| Kode | Kapan | Penerbit | Artefak | Konsumen | Sebelum terbit konsumen mengerjakan |
|---|---|---|---|---|---|
| P1 | 21 Nov | Danen | `drivers_weekly`, `episodes`, `fx_variation`, `panel_weekly_region` | Ardell (Task 4) | WP-25/26 dengan `panel_weekly` + `build_national_drivers` di memori, kolom `episode` = 0 sementara |
| P2 | 24 Nov | Danen | `profiles`, `boot_replicates`, `placebo_stats`, `events`, `response_features` | Ardell (Task 2, 3), Danen (robustness) | WP-18–24 dengan generator sintetis berskema sama |
| P3 | 24 Nov | Ardell | `concordance`, `exposure`, `regulation`, `province_features` | Ardell (Task 3), Abi (makalah: dataset) | – (Task 1 tidak membutuhkannya) |
| P4 | 23 Nov | Ardell | `forecast_eval`, `ablation` | Danen (WP-29 validasi V2) | WP-28 Tier 1 lebih dulu |
| P5 | 27 Nov | Danen & Ardell | semua artefak `ship` | Abi (WP-33/34), Ardell (WP-31/32) | Abi menulis bagian makalah yang tidak butuh angka |

Cara terbit: jalankan notebook tahapnya → output disalin ke folder Drive bersama `MyDrive/kagami/` (`results/`,
`data/processed/`, `data/reference/`) atau output notebook Kaggle dibagikan ke anggota lain → tulis 1 baris di
handoff jenis `TERBIT` (`docs/HANDOFF.md`) + versi pendek di chat.

## 6. Rincian jalur Abi (tanpa source code)

### 6.1 Daftar tugas
| Tugas | Keluaran | Tenggat | Untuk |
|---|---|---|---|
| Email permohonan izin penggunaan & redistribusi turunan PIHPS + hosting privat (U13, U24) | email terkirim, tanggal dicatat di OPEN_ISSUES U13 | 20 Nov | semua |
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
| `data/raw/manual_population/populasi_provinsi.csv` | `province_raw, year, population, source_url` (38 provinsi; tahun 2024–2025) | BPS: proyeksi penduduk menurut provinsi |
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
   `results/` (kecuali `findings.md`), `dist/`, cache, kredensial. Tiap anggota teknis bekerja di clone sendiri dan branch sendiri
   (`danen/...`, `ardell/...`), merge ke `main` lewat PR. Bekerja bersamaan di satu folder OneDrive berisiko konflik file.
   **Agent tidak pernah commit/push**; command git siap copas disiapkan agent hanya bila diminta (CLAUDE.md §4.6). Commit, push, PR,
   dan merge dijalankan anggota sendiri. Abi tidak perlu git: kirim file lewat Drive, Danen/Ardell yang meng-commit.
2. **Folder Drive bersama** `MyDrive/kagami/` untuk data mentah dan artefak (tempat terbit P1–P5; juga dipakai Colab).
3. **Kaggle**: dataset privat `kagami-code` & `kagami-raw` dibuat Danen lalu dibagikan ke Ardell sebagai collaborator;
   notebook masing-masing dijalankan di akun sendiri.
4. Ardell & Danen: `pip install -e ".[dev]"`, `pytest` hijau sebelum mulai.

## 9. Definisi selesai per anggota
- **Danen & Ardell:** WP ✅ di papan, `pytest` hijau, CLAUDE.md §9 diperbarui untuk modul sendiri, artefak asli terbit
  (bila WP menghasilkan artefak) + handoff `TERBIT`, entri SESSION_LOG.
- **Abi:** file keluaran ada di lokasi §6, isu terkait di OPEN_ISSUES diperbarui, handoff (`DATA-MANUAL`/`BLOKIR`/dll.) dikirim.
