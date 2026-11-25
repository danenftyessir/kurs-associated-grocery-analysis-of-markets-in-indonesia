# Log Sesi (catatan kerja per anggota)

Satu bagian per anggota; **tambahkan entri baru di paling atas bagian MILIK SENDIRI** (bukan di atas file) agar tidak
bentrok saat merge antar-branch. Maksimal ~10 baris per sesi: WP yang dikerjakan, status akhir, angka penting, file yang
diubah, yang belum selesai/diblokir. Pesan ke anggota lain (artefak terbit, permintaan, blokir) → **handoff** di
`docs/handoff/` (format `docs/HANDOFF.md`), bukan di sini. Jangan duplikasi DECISIONS/OPEN_ISSUES — tautkan ID-nya.

---

## Danen

### 2026-11-25 — Danen: WP-36 ✅ (Business Understanding Task 4 arah, D-154)
- Protokol beku sebelum ukur: pengguna TPID, kenaikan material (p80 |y| komoditas di baris latih), kriteria S1 daftar pantau, S2 kalibrasi,
  S3 arah saat bergerak material, 4 aturan naif. Tanpa model baru; C1-tuned dinilai dev lalu test sekali.
- Test: daftar pantau provinsi presisi 0,18 / 0,16 (laju-dasar 0,09; aturan tren 0,08–0,09), recall 0,41 / 0,36; Brier skill 0,17;
  macro F1 saat bergerak material 0,81. S1–S3 lolos di test; dev S2 h 8 gagal tipis (ECE 0,056).
- Laporan `docs/audit/20261125_business_understanding.md`; S1–S3 jadi ukuran wajib di `docs/EKSPERIMEN.md`.
- `results/findings.md`: Ringkasan butir 7 + subbagian C1-tuned & daftar pantau + Keterbatasan + sumber angka; app hal. 6 dites.
  Belum: commit/push (app daring), unggah `findings.md` ke Drive tim, validasi asumsi praktik TPID.

### 2026-11-25 — Danen: WP-36 ✅ (alur CRISP-DM + Data Understanding tiga arah, D-153)
- Dokumen hidup `docs/EKSPERIMEN.md`: fase CRISP-DM di proyek, kartu 8 komponen, layar DU dengan kontrol, gerbang ke Modeling.
- DU dev (tanpa model/test): lintas komoditas 0/360 lolos BH (co-trend 2021–2022); 5 tipe seri tetapi tidak menjelaskan skill di luar
  komoditas; informasi tetangga setelah partial ρ 0,021–0,025 → ketiganya tidak lolos gerbang; laporan `docs/audit/20261125_crisp_du.md`.
- Berikutnya (CRISP-DM): Business Understanding. Belum: commit.

### 2026-11-25 — Danen: WP-36 ✅ (validasi `IW_NAT`, D-152)
- Protokol beku sebelum run; tanpa kandidat baru. Audit kebocoran intraminggu 83 origin + 2 data penuh: 84/84 lolos, kontrol positif 84/84.
- Dev: LOO ≈ rerata nasional (+0,005 / +0,001 vs `IW_NAT`); keserentakan tidak menambah; tanpa Jumat −0,010 h 4 (separuh keuntungan).
- Prediksi maju C1-tuned & `IW_NAT` dibekukan (12 origin, 8.112 baris, sha256 di manifest); evaluasi beku, uji label 0 beda.
- Daya: konfirmasi butuh ± 185 / 355 origin → validasi maju hanya penjaga. Belum: commit `forward_preds.csv` + manifest sebelum 27 Nov.

### 2026-11-25 — Danen: WP-36 ✅ (pilot intraminggu & harga produsen PIHPS, D-151)
- Protokol dibekukan sebelum run (sha256 di laporan); pembanding = `direction_tuned_preds` C1t persis (maks |Δp| 0).
- Intraminggu (`pihps_daily`): `IW_NAT` lolos dev (+0,020 / +0,005) → test +0,0085 / +0,0033, q 0,28 / 0,30 → belum terbukti.
- Unduh `pihps_producer` (3.570 permintaan, 0 galat, 0,4 MB) → sumber opsional + `LOADERS` + tes; tangga mingguan, eceran mendahului;
  C1-tuned + fitur produsen −0,006..−0,001 di dev → test tidak dibuka. C1-tuned tetap.
- Laporan `docs/audit/20261125_pilot_produsen_intraminggu.md`. Zip produsen & grosir diunggah ke Drive tim `data/raw/bi_pihps/` lewat
  Chrome (ukuran byte identik; `checksums.csv` tidak diubah agar lineage stage0 tidak basi sebelum pembekuan). Belum: commit.

### 2026-11-25 — Danen: WP-36 ✅ (pilot harga pedagang besar PIHPS, D-150)
- Unduh `pihps_wholesale` (34 provinsi, 3.978 permintaan per bulan, 0 galat, 0,9 MB) → sumber opsional + entri `LOADERS` + tes loader.
- Grosir kaku (carry_forward 85–98%), tidak mendahului eceran; C1-tuned + fitur grosir −0,006..+0,001 di pengembangan → test tidak dibuka.
- Laporan `docs/audit/20261125_pilot_grosir.md`; C1-tuned tetap. Belum: commit; unggah berkas mentah baru ke Drive tim (`drive-push-raw`).

### 2026-11-25 — Danen: WP-36 🔶 (riset sumber data hulu Task 4)
- Baca-saja di situs: PIHPS Pedagang Besar sejak 2018-01, 31–34 provinsi, varian sama dengan eceran; Produsen sejak 2018-06/09,
  cakupan tidak lengkap (gula 10, minyak 11, bawang putih 2 provinsi). Bapanas produsen = akses terbatas (SAPA). NASA POWER terbuka.
- Bukti U19: tombol Download resmi PIHPS = `exportToExcel` grid dari endpoint yang sama. Laporan `docs/audit/20261125_sumber_data_hulu.md`.
- Belum: unduh & pilot pedagang besar (butuh persetujuan Danen); izin BI untuk jenis pasar ini dipastikan `[HUMAN]`.

### 2026-11-25 — Danen: WP-36 ✅ (split dev s.d. 2024 untuk tuas rezim, D-149)
- Dev = origin + h ≤ 2024-12-31, test ≥ 2025 (pasca-hoc, aturan sama): 8 kalibrasi + 4 kelompok fitur rezim → tidak ada yang lolos.
- Fitur kebijakan menghapus drift naik komoditas diatur 2024 (+0,086 / +0,149 → +0,017 / +0,005) tanpa menaikkan macro F1.
- Laporan `docs/audit/20261125_task4_ronde4.md` §4; C1-tuned tetap. Belum: commit.

### 2026-11-25 — Danen: WP-36 ✅ (ronde 4 Task 4 arah: rezim & kalibrasi temporal, D-148)
- Preprocessing baseline dibekukan; `iw_gap` disimpan sebagai `C1t_iw` (prediksi lokal di `data/interim/`, tidak di `src/`).
- Kalibrasi temporal (intercept / pergeseran prior) dan fitur sadar-rezim: tidak lolos origin pengembangan; drift baru muncul 2024+.
- Galat fitur regulasi ronde 2: acuan beras premium sejak 2024-06 (hanya test). U108 = koreksi `episode` real-time.
- Laporan `docs/audit/20261125_task4_ronde4.md`. Aturan baru: job > 1 jam → Chrome → Colab T4, output ke Drive terpusat.
- Belum: commit; data produsen/grosir (sumber baru) menunggu keputusan.

### 2026-11-25 — Danen: WP-36 ✅ (audit preprocessing Task 4 arah, D-147)
- Audit mentah → agregasi → missing → fitur → label → dataset dengan C1-tuned tetap; label evaluasi & `src/` tidak berubah.
- Tick Rp50 di semua harga harian; label < 1 tick 2,4–4,3%, tak stabil 8–12% (akurasi ≈ 0,5); label ≥ 10 tick tetap 0,68–0,71.
- Kebocoran 76 origin × 54 kolom = 0 sel; flag `episode` bocor 1/76 origin (M2/C2 saja). Drift naik = rezim komoditas diatur 2024+.
- 10 varian preprocessing (dev): hanya `iw_gap` lolos → test +0,004 / +0,005, belum terbukti (q 0,35 / 0,089); C1-tuned tetap.
- 3 tes kebocoran baru di `tests/test_direction_tuned.py`; laporan `docs/audit/20261125_task4_audit_preprocessing.md`.
- Belum: commit.

### 2026-11-25 — Danen: WP-36 ✅ (optimasi arah Task 4 ronde 2, D-146)
- Diagnosis arah (kesalahan di perubahan kecil), fitur regulasi/spasial/kalender/prior/level, LightGBM/XGBoost/ensemble, spesialis
  komoditas, dua tahap 3 kelas; semua dipilih di origin pengembangan → tidak ada yang mengalahkan C1-tuned.
- 3 kelas test: macro F1 0,625 / 0,606. TCN/MLP multi-task di Colab T4 (akun danendrashafia1967, 9 run): semua −0,02..−0,07 vs C1-tuned.
- Laporan `docs/audit/20261125_task4_ronde2.md`; `src/` tidak berubah.
- Belum: commit.

### 2026-11-24 — Danen: WP-36 ✅ (optimasi klasifikasi arah Task 4 eksploratif, D-145)
- Fitur per seri (8 kelompok, ablation), Optuna HGB (C1t 40 trial, C2t 12), TSMixer (10 trial, L1/BCE), threshold dari origin
  pengembangan, kalibrasi residu TimesFM, kepala CatBoost TimesFM; test final origin ≥ 2024 tidak dipakai memilih apa pun.
- C1-tuned macro F1 test 0,677 / 0,680 vs TimesFM 0,618 / 0,621 (lolos BH); kurs tidak membantu; TSMixer-tuned tidak lebih baik.
- Laporan + skrip + konfigurasi di `docs/audit/20261124_task4_optimasi_arah.md`; `src/` & artefak tidak berubah.
- Porting: `features/price_dynamics.py`, C1t/C2t di `models/direction.py`, `task4 --direction-tuned` → `direction_tuned_preds`,
  `tests/test_direction_tuned.py` (6 tes); prediksi identik dengan eksperimen.
- Belum: commit, bundle Kaggle/Drive dibangun ulang.

### 2026-11-24 — Danen: WP-36 ✅ (kelengkapan klasifikasi, seed, kepekaan blok, D-144)
- F1 berbobot/cakupan/akurasi termasuk nol; replikasi 3 seed model deep; kepekaan blok 2/3/4/6 & lag DM; segmen tahun origin;
  tabel perbandingan model Task 4 + sakelar diagnostik; Riwayat ringkas; `evaluator_version` (schema 3); 2 tes baru.
- Robustness Tier 2 tercatat identik dengan file resmi → sinkron. F1 makro terbaik 0,623 (TimesFM h 8); target 0,8 tidak tercapai.
- Belum: commit, `evaluate all` bersih, restart 8501, lineage Task 1 & forecast resmi (Kaggle).

### 2026-11-24 — Danen: WP-36 ✅ (koreksi multiplisitas, D-143)
- `metrics.bootstrap_p`, p di direction_bootstrap/paired_accuracy_diff/tabel segmen (+ BH), `assessment.apply_multiplicity`,
  kolom q (BH) di halaman 7, 1 tes baru; `evaluate task4` ulang.
- Gugur: TSMX_fx vs TSMX h 4 (q 0,057), segmen kaku TimesFM/M2, lentur M1. findings.md & audit Lampiran C.7 disesuaikan.
- Belum: restart app 8501, commit, `evaluate all` pada commit bersih (P1 sisa, Danen).

### 2026-11-24 — Danen: WP-33 🔶 (findings: eksplorasi Task 4)
- `results/findings.md`: Ringkasan butir 6, bagian "Eksplorasi Task 4" (D-139–D-142), keterbatasan model eksploratif.
- Belum: commit/push, unggah findings.md baru ke Drive tim `results/`, makalah.

### 2026-11-24 — Danen: WP-36 ✅ (model deep & foundation eksploratif, D-142)
- `models.neural`: PatchTST, TSMixer (± kurs), TimesFM 3.0 zero-shot (± kovariat kurs); `task4.run_deep` + `--deep`, artefak
  `deep_preds`, evaluator (MAE/M1 + DM, arah + interval, beda berpasangan), tabel di halaman 7, `tests/test_neural.py` + 1 tes.
- Unduhan disetujui Danen: timesfm 3.0.2 + bobot TimesFM 3.0 (1,32 GB, non-komersial); Chronos-2 tidak.
- Data asli: TFM MAE/M1 0,895 (h 8, DM p < 0,001), arah 0,62; kurs tidak membantu (TFM_fx ≈ TFM, TSMX_fx ≥ TSMX).
- Belum: commit/push; findings.md belum memuat D-141/D-142; risiko kontaminasi pralatih TimesFM dicatat.

### 2026-11-24 — Danen: WP-36 ✅ (klasifier arah eksploratif, D-141)
- `models.direction` (HGB classifier C1 tanpa kurs, C2 + kurs), `task4.run_direction` + `--direction`, artefak `direction_preds`,
  evaluator beda berpasangan + prediksi selektif, bagian baru di halaman 7, `tests/test_direction.py` + 1 tes evaluator.
- Data asli: C2 0,617 vs baseline 0,545 (h 8, interval selisih 0,034..0,108); C2 − C1 tidak terbukti (+0,009); C1 − M1 +0,047.
- Belum: commit/push; findings.md belum memuat hasil eksploratif ini; model DL ditolak sebelum pembekuan (D-141).

### 2026-11-24 — Danen: WP-36 ✅ (audit halaman 7 + evaluasi dua lapis, D-140)
- Audit 5 bagian halaman 7 → `docs/audit/20261124_audit_evaluasi_eksekusi.md`; lalu `tracking.assessment` (penilaian vs acuan),
  `metrics.direction_bootstrap`/`direction_segment_table`/`feature_health`, `store.artifact_sync`/`stage_states`, `lineage.code_hash`/
  `git_dirty`, halaman 7 ditulis ulang (5 bagian), wiring `task2`/`robustness` OPTIONAL + notebook 02/05, 8 tes baru.
- Data asli: M1/M2 arah tidak berbeda dari baseline mayoritas; M3 di atas; komoditas kaku di bawah baseline semua model; 13/33
  fitur clustering konstan; robustness resmi bukan output run eksekusi terakhir. `evaluate all` ulang → 7 log baru.
- Belum: commit/push, restart server app 8501 (modul lama ter-cache), unggah ulang `kagami_code.zip`; usulan model DL ditunda.

### 2026-11-24 — Danen: WP-36 ✅ (diagnostik klasifikasi arah Task 4, D-139)
- `tracking.metrics.direction_metrics` (accuracy, baseline mayoritas, balanced acc., precision/recall/F1 per kelas, F1 makro, MCC,
  ROC-AUC, PR-AUC, confusion) di `evaluate_task4`; `viz.plots.confusion_matrix` + tabel di app hal. 7; 2 tes rumus manual + penjaga.
- Artefak resmi: akurasi arah 0,543 / 0,557 / 0,573 (M1 / M2 / M3, h 4) dan 0,560 / 0,560 / 0,602 (h 8) vs baseline kelas mayoritas 0,527 / 0,545; F1 makro 0,538 / 0,550 / 0,566 dan 0,551 / 0,549 / 0,594; MCC 0,08–0,19; ROC-AUC 0,567–0,627.
- Log evaluasi-saja `task4` baru di `logs/`. Belum: commit/push, unggah ulang `kagami_code.zip`.

### 2026-11-24 — Danen: WP-36 ✅ (run end-to-end penuh semua tahap)
- `kagami all` + `robustness --tier2` lokal dari folder kode bersih (out_dir sementara): semua tahap sukses setelah 2 perbaikan.
- Bug 1 (D-138): `task1` gagal setelah bootstrap + plasebo (5.312 dtk) karena `print` τ² ke stdout cp1252; `cli._utf8_stdio`.
  Checkpoint membuat run ulang melanjutkan (task1 19 dtk). Bug 2 (D-138): halaman 7 crash pada format waktu log campuran.
- Reproduksi 35 artefak: 17 identik sha256, 16 selisih ≤ 3,5e-11, angka kunci semua sama; app 7/7; pytest 357 lolos.
- Belum: commit/push (cli.py, viz/plots.py, 2 tes, dokumen), unggah ulang `kagami_code.zip` ke Drive & Kaggle.

### 2026-11-24 — Danen: WP-36 ✅ (log eksekusi & evaluasi terpusat)
- Audit + desain dilaporkan dulu, lalu `src/tracking/` (schemas, metrics berpenjaga, lineage sha256, evaluators per tahap, registry +
  DAG dari REQUIRES, store JSON tidak ditimpa, logger `@tracked`), hook pengamat `utils.io`, CLI `evaluate`/`runs`, log ikut Drive &
  zip juri, app hal. 7, `tests/test_tracking.py`, docs/TRACKING.md, D-137. Hasil analisis & params tidak berubah.
- Run nyata (pipeline_id tunggal, out_dir sementara): stage0 41,5 dtk, task3 765 dtk, robustness 14,6 dtk, task2 120 dtk; task2 6/6 &
  task3 4/4 output identik sha256 dengan artefak resmi; `evaluate all` untuk 7 tahap (Task 1 & 4 tanpa waktu eksekusi teramati).
- Bug ditemukan & diperbaiki di sesi: dataset_id ikut menghitung `recorded_at` checksums (11 log sesi ini dikoreksi, ditandai di
  `note`); pilihan run halaman 7 terbawa antar tahap; grafik plotly kosong di `st.tabs` tersembunyi → pemilih bagian.
- `bundle` ulang: `dist/kagami_code.zip` 85 file (+ `src/tracking/`), `evaluate task2 task4` jalan dari folder ekstrak bersih.
- Belum: commit/push (log masuk app daring setelahnya), unggah zip ke Drive/Kaggle `[HUMAN]`.
- `package` ulang 03.31: 212 file 44,6 MB (+ logs, tracking); dari folder ekstrak bersih 7/7 halaman tanpa "Menunggu hasil".

### 2026-11-24 — Danen: analisis progres + perbaikan deploy app (D-135), G7 ulang
- Analisis: semua WP analisis ✅; app live kagami.streamlit.app kosong (6 halaman "Menunggu hasil"); zip `dist/` basi (sebelum D-134).
  Rawan dikutip berlebihan: daging ayam β_e bertanda terbalik & tidak tahan Tier 1; 4/90 sel nasional ≈ harapan null; G-het daging ayam
  tepat q 0,050; V4 kesamaan tanda 0,51; Task 4 M0 < M1 untuk 5/10 komoditas, `M2_nofx` = M1, large_move 8 origin.
- `.gitignore` membuka 23 artefak yang dibaca app (± 1,4 MB, ship=True); hal. 6 `findings` terpisah dari `robustness`; `package.CODE_GLOBS`
  + `requirements.txt`. Salinan bersih (file git saja) & zip juri baru: 6/6 halaman AppTest tanpa exception/"Menunggu hasil".
- `bundle` 77 file, `package` 178 file 47,6 MB tanpa artefak hilang. Belum: push ke GitHub (app live baru terisi setelahnya),
  unggah ulang `kagami_code.zip` ke Drive, rapikan 24 handoff berstatus terbuka.
- Setelah push (PR #6) app daring masih "Menunggu hasil": `common.load` meng-cache `None` dan Cloud tidak me-restart proses (direproduksi
  lokal) → D-136: ketiadaan tidak di-cache, kunci cache path + mtime + ukuran; tes regresi gagal di versi lama, lolos di versi baru.

### 2026-11-23 — Danen: eksekusi PLAN.md §18 (app, D-134)
- `src/viz/style.py` baru; `plots` + `region_map`, `silhouette_threshold`, `scenario_paths`; halaman 2–5 ditata ulang; `app/common.py`
  + `picker`/`reset_button`/`table`/`load_geo`/`unit_names`; tes `test_viz` (+4).
- `data/reference/indonesia_provinces.geojson` (geoBoundaries ODbL, 34 prov, 98 KB; unduh disetujui Danen); `package` membawa
  `*.geojson` & `.streamlit/config.toml` (telemetri mati).
- Bug: lencana NaN "terdeteksi"; kurva provinsi mencampur δ mentah & tersusut; `go.Choropleth` tidak offline (CDN topojson).
- Verifikasi browser data asli: hal. 2–5, mode gelap & terang, lebar 375 px. Klik mouse peta belum dicoba manusia.
- P1: `plots.robustness_forest` (V18, hal. 6) & `plots.asymmetry_plot` (V19, hal. 2) + tes; angka cocok dengan §2 (daging ayam,
  beras). Berikutnya: V07/V13 sebagai grafik, `python -m kagami bundle` + unggah ulang `kagami_code.zip`.

### 2026-11-23 — Danen: evaluasi desain spec visualisasi (PLAN.md §18), tanpa ubah kode
- PLAN.md §18: spec v1.0 dicocokkan dengan artefak asli, app berjalan, validator palet, heuristik UX; prioritas baru §18.7.
- Temuan: `coassign` semua 1,0 (k = 1) → V10 kosong; interval PT hanya nasional; `cluster_selection` satu p95 (0,196); tidak ada artefak linkage (V09 dihapus); ablation satu kelompok fitur (V16 digabung ke V15).
- Palet bawaan Streamlit & Plotly gagal validator; usulan 3 slot lolos. Peta: geoBoundaries IDN ADM1 (34 unit, ODbL) dengan uji offline.
- Konflik merge commit "gabungkan perubahan remote ke dev" (04fc5ec) ter-commit dengan penanda di 4 file (13 blok): CLAUDE.md, ARCHITECTURE,
  DECISIONS, WORKPLAN (papan WP terduplikasi) → `test_docs_sync` gagal 2 tes. Diselesaikan: status = sisi lokal (pasca D-130); D-200..D-204
  Ardell dipertahankan; daftar tes ARCHITECTURE digabung (+ task1); baris WP Ardell yang masih berlaku (D-201..D-204, file tes) disisipkan.
- Berikutnya: keputusan §18.9 (unit peta, geometri, kerjakan sebelum 27 Nov atau tidak).

### 2026-11-23 — Danen: U102 ✅ (uji tumpang tindih konkordansi HS, D-133), U24 ditutup
- Comtrade 2023 (15 kode, 160 baris) dari API publik UN Comtrade (izin Danen) → `data/raw/comtrade/comtrade_idn_import_HS_monthly_2023.csv`, sumber `comtrade_import_2023` (optional).
- `qa.check_trade_overlap` + tes (sintetis & asli) + `stage0_report` §9; `stage0` 44 dtk, artefak lain identik, checksums +1 baris.
- Hasil: 14/15 kode cocok persis (bawang putih 070320 USD 648,6 juta di kedua sumber); 1511 0,944 (nilai kecil).
- U24 ditutup atas keputusan Danen (akses link diterima). Command git untuk push yang ditolak disiapkan (lewat `feat/`).

### 2026-11-23 — Danen: ambil alih jalur B & C (D-130); U106, findings, app, Tier 2, diagnostik M1
- D-130: Danen pegang semua WP; makalah/video ditunda. Papan: WP-07/15–17/19/20/23–26/30/31 ✅ (bukti artefak asli + tes).
- U106 (D-132): p meta-regresi konsisten interval (11 → 0/88 p < 0,05), `q_fdr`, ARI NaN saat k = 1, τ² REML di `heterogeneity`; `task2` 164 dtk, `task3` 705 dtk (artefak lain identik).
- `results/findings.md` dari artefak; app hal. 2/4/5/6 diperluas (`national_calibrated`, H2, E2, Kendall, robustness), `STRETCH` ganti `use_container_width`.
- WP-30: `robustness --tier2` 203 dtk, 679 baris (Tier 2 191/193 dalam interval; keterpencilan alternatif konsisten H3).
- D-131: diagnostik dummy musim Task 4 → M2/M1 1,005 / 1,019, H5 Holm 0,56 (sama); M0/M1 0,95 / 0,97.
- WP-32 ✅: paket 172 file tanpa artefak hilang; G7 di folder bersih: app 6/6, `task4` 1.128 dtk identik resmi (selisih 1e-16). Bundle 74 file.
- pytest 317 lolos. Diunggah lewat Chrome (ganti file): `heterogeneity`, `partition_compare`, `assoc`, `robustness`, `findings.md` (baru),
  `kagami_code.zip` (`MyDrive/kagami/`). Berikutnya: U24 `[HUMAN]`, commit, makalah/video bila dilanjutkan.

### 2026-11-23 — Danen: audit progres + inferensi nasional terkalibrasi plasebo (D-129, U107)
- Audit artefak asli: bootstrap blok 13 minggu menarik β ke nol (median rasio replikasi/estimasi 0,57 / 0,35 / 0,35 pada h 4/8/12) → interval resmi terlalu konservatif.
- `evaluation/calibration.py::national_calibrated` + `tests/test_calibration.py`; artefak baru `national_calibrated` dari `task3` (0,9 dtk).
- Data asli: 7/48 sel tidak memuat nol (resmi 3); q < 0,05 daging ayam β_e(4), gula β_e(4) (tidak tahan Tier 1), minyak goreng ω(8), ω(12).
- Temuan lain (laporan ke user): event study 19/390 sel p < 0,05 (= kebetulan); M1 Task 4 memakai `month` numerik & `idf_rel_week` diisi median (milik Ardell); `M2_nofx` identik M1; Tier 2 tidak ada di `robustness` Drive.
- Handoff KEPUTUSAN ke Semua. `national_calibrated` diunggah ke Drive tim `results/task3/` (Chrome, 13 KB). Belum: handoff musiman M1 ke Ardell; bundle kode.
- Temuan Drive: folder `data` & `results/task3` "siapa saja yang memiliki link dapat mengedit" → U24 🔴 `[HUMAN]`.
- Berikutnya: WP-30 (`robustness --tier2` + keterpencilan alternatif).

### 2026-11-23 — Danen: WP-27 ✅ & WP-29 ✅ (Task 4 asli, robustness ditulis)
- `forecast_preds`/`forecast_eval`/`ablation` diunduh dari Drive (Chrome); `evaluate` + `ablation` lokal identik (≤ 4e-16).
- M2/M1 MAE 1,014 / 1,017 (h 4 / 8), DM p 0,001 / 0,006; H5 tidak didukung (1,12, Holm 1,0; large_move 8 origin). M0 ≈ M1.
- Diagnostik ridge per komoditas (scratch): kesimpulan sama → D-128. `M2_nofx` identik M1.
- `robustness` lokal 11 dtk, 486 baris; V2 forecast M2/M1 origin 2026 1,005; V4 26/30.
- `robustness` diunggah ke Drive tim `results/` (130.052 byte, cocok).
- Berikutnya: WP-30.

### 2026-11-23 — Danen: audit positif palsu, E2 & H2 dikalibrasi (D-127)
- Audit artefak asli Task 1–3: positif palsu dari SE cluster sempit (E2, H2, β daging ayam) dan p `assoc` vs interval (milik Ardell).
- `evaluation/regimes.py`: interval ±crit·SE, crit dari 499 plasebo geser-melingkar (joblib), `p_placebo`, `q_fdr`; `asymmetry.py`: interval laporan = Wald ∪ bootstrap.
- Tes: `test_regimes.py::test_regime_placebo_calibration`, interval laporan di `test_asymmetry.py`. `task3` lokal 562 dtk.
- E2: sel tidak memuat nol 38 → 15 dari 145, q min 0,145; H2: 0 sel (bawang putih h8 −10,2..3,1). `assoc` tidak berubah.
- U106 + handoff PERMINTAAN ke Ardell (p meta-regresi, ARI k = 1); handoff KEPUTUSAN ke Semua.
- `asymmetry` & `regime_profiles` diunggah sebagai versi baru (ID tetap, ukuran cocok); `kagami_code.zip` di `MyDrive/kagami/`, belum diekstrak.
- Berikutnya: tarik Task 4 → WP-27 → `robustness` (belum ada di lokal) → WP-29.

### 2026-11-22 — Danen: WP-21 ✅ struktur tertanam diperbaiki (D-126, U105)
- `planted.deviation_matrices` + `shrink_matrix`; `recovery_curve` menanam pada deviasi plasebo mentah lalu susut EB & z-score; `task2` diperbarui.
- Tes: EB penanaman = EB matriks fitur; regresi U105 (tanam setelah susut memulihkan δ 0,1, versi baru tidak). Derau sintetis 0,2.
- Data asli: batas deteksi δ = 0,2 (k = 2 dan 3; recovery 0,995 / 0,965), δ 0,1 = 0,43 / 0,13; ambang 0,196; 53 dtk.

### 2026-11-22 — Danen: analisis Task 1 asli, WP-18 ✅ (G-het), WP-22 ✅, H2 diformalkan (D-125)
- Lima artefak Task 1 dari Drive tim (Ardell) → `results/task1/`: kontrak lengkap, B = R = 499 (non-fokus 199), `se` di `placebo_stats`.
- `task2` lokal 650 dtk: G-het menolak telur ayam (q 0,040) & daging ayam (q 0,050); k = 1 (silhouette 0,184 < p95 0,196).
- H2 belum punya kode → `asymmetry_wald` + `evaluation/asymmetry.py` + `tests/test_asymmetry.py`; `task3` (635 dtk) menulis `asymmetry`.
- Temuan: struktur tertanam ditanam setelah penyusutan EB → recovery 1,0 sejak δ = 0,1 (U105, menunggu keputusan).

### 2026-11-21 — Danen: E2 profil per rezim HET/HAP (D-124)
- `src/evaluation/regimes.py` (regulation_changes, regime_table, regime_profiles) + `tests/test_regimes.py`; artefak baru `regime_profiles` dari `task3`.
- Data asli: 145 baris (10 komoditas, 3–6 rezim, h 4/8/12, e & w), 4,9 dtk; estimasi penuh di dalam interval rezim 73% sel.
- Notebook 03 + forest plot E2. Peta dataset → task: `regulation` sebelumnya tidak dipakai; `concordance` hanya dokumentasi.

### 2026-11-21 — Danen: data manual WP-07 (D-123)
- Penduduk 2025 dari tabel BPS (38 prov → 34), n_kota dari situs PIHPS (110 kota), faktor GKG→beras 0,5762 dari rilis BPS 2 Feb 2026.
- `stage0` ulang: `province_features` lengkap (rice_sufficiency 0,001..3,27; n_kota 1..12). Suite 290 lolos. U14/U15/U21 🟢.
- Ketiga file + `checksums.csv` (versi baru) diunggah ke `data/raw/` Drive tim lewat Chrome. Sisa: snapshot Panel Harga kab/kota (opsional).

### 2026-11-21 — Danen: merge 6 branch Ardell, stage0 + WP-07 lokal, E1 sementara, D-120
- Merge `feat/reference-tables` .. `feat/app-package` ke dev (0 konflik); simulasi: 276 lolos, 6 gagal (dokumen/paket, handoff PERMINTAAN ke Ardell).
- `stage0` lokal 27 dtk: concordance 10, exposure 10, regulation 72 (5 unverified), province_features 34 (populasi/n_kota NaN).
- Bug pemetaan: FAOSTAT "Rice" = padi → rasio beras 1e-6; diganti beras giling + patah (D-120, DEVIASI) → 0,033.
- E1 sementara (PT(8) titik nasional): τ-b −0,045 (−0,65..0,56), p eksak 0,93 → tidak terdeteksi. Resmi menunggu `response_features` (P2).
- Atas instruksi Danen, 7 tes merah pasca-merge diperbaiki langsung (dokumen sinkron untuk modul Ardell, 2 tes test_package); suite 287 lolos.
- D-121: DEVIASI untuk kunci params Ardell (`import_ratio_years` [2018, 2023], `run_m3`); hash params baru di PREREGISTRATION.
- D-122: notebook 01/03/04 kini menarik `panel_weekly` (sebelumnya Task 1 di Colab diam-diam hanya versi wilayah). Task 1 ± 7 dtk/replikasi.

### 2026-11-21 — Danen: perbaikan `ols_cluster` grup kosong (D-119)
- Laporan Ardell: perbaikan `ols_cluster` (macOS) menunggu Danen. Ditemukan regresi D-118: grup NaN/NaT → bincount crash.
- `stats.regression.ols_cluster` membuang baris grup kosong; tes regresi di test_stats.py; suite 190 lolos; hasil nasional tidak berubah.
- Handoff KEPUTUSAN ke Ardell (minta pesan error asli bila masalah macOS berbeda).

### 2026-11-21 — Danen: LP cepat untuk bootstrap (D-118)
- `local_projection`: desain dibangun sekali per komoditas × spesifikasi (`_design_parts`/`_design_arrays`, numpy); `ols_cluster` pakai bincount.
- Hasil identik (profiles 598 baris selisih 0; Tier 1 ≤ 2e-12; mde ≤ 2e-15). `national_profiles` 28,7 → 5,9 dtk; Tier 1 21 → 17,5 dtk.
- Bootstrap WP-16 Ardell ± 50 menit untuk B 499 (sebelumnya ± 3,2 jam). Handoff KEPUTUSAN ke Ardell. Tes baru di test_local_projection.py.

### 2026-11-21 — Danen: WP-30 🔶 (robustness Tier 2)
- `robustness.tier2` + input `panel.build_variant_panels`/`last_observation_panel`/`build_bapanas_panel`, `drivers.build_world_variants`,
  `pipelines.robustness.tier2_inputs`; tes di test_robustness.py & test_drivers.py. D-116.
- Data asli: 187 baris, ±40 dtk; baseline di dalam interval 184/186 sel (gula Premium β_e(4) 0,36 vs 0,69; Curah ω(8) 0,36 vs 0,21).
- Kendall PT(8) vs ordinal jalur τ −0,03 (p 1,00). Bapanas bulanan = PIHPS bulanan (42/42).
- Belum: keterpencilan alternatif (WP-23) & baseline τ import_ratio_direct (WP-07). Artefak `robustness` menunggu P2/P4.
- Handoff ANGKA-MAKALAH ke Abi (Tier 1, V2/V4, Tier 2; sementara): docs/handoff/20261121-1500_danen-ke-abi_angka-robustness.md.
- Aturan D-117: pesan commit/PR tanpa Co-Authored-By (CLAUDE.md §4.6).

### 2026-11-21 — Danen: gerbang G-power diputuskan (D-115)
- `mde` dihitung ulang (stage0): kolom lama identik; LP tetap utama (bawang putih 2,52, gula 0,90, minyak goreng 0,465).
- MDE asimetri ditambahkan (`power.asymmetry_null_se`, kolom `mde_asym_*`); ambang H2 satuan PT (keputusan Danen).
- H2 konfirmatori: beras 0,44, daging sapi 0,32; 8 komoditas lain deskriptif. U8 🟢. `stage0_report` memuat status H2.
- Config beku utuh (hash konten LF = PREREGISTRATION; beda di disk karena autocrlf).
- Handoff KEPUTUSAN ke semua: docs/handoff/20261121-1400_danen-ke-semua_g-power.md.
- `mde` (versi 2, menimpa) dan `stage0_report` diunggah ke Drive tim `results/stage0/` lewat Chrome; bundle kode dibangun ulang.

### 2026-11-21 — Danen: WP-29 🔶 (validasi V2 & V4)
- `robustness.validation` + `lp_implied_paths`; `evaluate` kini punya subset `case_study` (origin 2026); `events` + `placebo_median`.
- V4 data asli: implikasi LP di dalam interval kelebihan event 26/30 sel (17/18 fokus); tanda per episode ± 0,5 → arah antar-episode tidak konsisten.
- V2 episode 12 (2026-05-18): 0/30 sel di luar pita plasebo. V2-forecast menunggu P4.
- Bug desain ditemukan pada data asli: titik tengah pita plasebo bias oleh ekor (minyak goreng −0,09) → median (D-114).
- Pipeline robustness: REQUIRES + episodes. Berikutnya: G-power 23 Nov → WP-18/21/22/27/29 asli.

### 2026-11-21 — Danen: WP-27 🔶 (evaluasi DM & ablation, sintetis)
- `forecast_eval.evaluate/ablation/n_nonoverlap` + `stats.meta.holm`; sel ALL/komoditas/wilayah/jalur H5, subset all & large_move.
- DM pada MAE per origin (HAC lag ceil(h/4)−1); H5 = M2, h 8, large_move, 2 jalur, DM satu sisi + Holm (D-113).
- Bug ditemukan tes: p NaN membuat keluarga Holm menyusut → kini dihitung 1. α H5 dari PREREGISTRATION (tak ada kunci beku).
- Tes baru: test_forecast_eval (+ holm). Handoff ke Ardell: kontrak `forecast_preds` (model `M2_nofx`, large_move).
- Berikutnya: G-power 23 Nov → WP-29 (V4 data asli) → WP-18/21/22/27 asli.

### 2026-11-21 — Danen: WP-21 🔶 (struktur tertanam, sintetis)
- `planted.recovery_curve` + `best_silhouette`, `placebo_threshold`, `plant_structure`, `detection_limit`; Ward bisa disuntikkan (WP-19 masih stub).
- δ = selisih respons RMS per fitur antar pasangan kelompok (simpleks acak), ditanam sebelum z-score (D-112). Versi j·δ segaris ditolak: k = 3 tak pernah terpilih.
- Sintetis (derau 0,3, 12 fitur): recovery δ 0,5 = 0,85 (k=2) / 0,90 (k=3); 200 replikasi ± 20 dtk. Tes baru: test_planted.
- Handoff ke Ardell diperluas: `task2` meneruskan matriks plasebo mentah ke `recovery_curve`.
- Berikutnya: G-power 23 Nov → WP-18/21/22 asli (P2/P3/WP-19) → WP-27 (P4) → WP-29.

### 2026-11-21 — Danen: WP-28 ✅, WP-18 🔶, WP-22 🔶 (kode sintetis)
- WP-28 `robustness.tier1` + `fx_decomposition`: 6 cek × h 4/8/12 × driver e/w; data asli 382 baris, 21 dtk. Pipeline robustness kini membaca panel & eligibility.
- Daging ayam β_e(8): tanpa COVID & Brent ekstrem −0,96 (−2,05..0,14); komponen spesifik rupiah −1,89 (−3,02..−0,76) → bukan semata COVID.
- Aturan Brent ekstrem membuang juga Mar 2026 (+0,40) dan Nov 2026 (parsial); d_dxy menjelaskan 27% varians de.
- WP-18 `heterogeneity_stats/placebo_pvalues` dan WP-22 `kendall_exact` (+ `all_permutations`, `kendall_permutation_test`, 10! eksak) dites sintetis.
- D-111 (konvensi teknis). Tes baru: test_robustness, test_heterogeneity. Handoff ke Ardell: `se` wajib di placebo_stats provinsi.
- Berikutnya: G-power 23 Nov → WP-21 (sintetis) → WP-18/22 asli (P2/P3) → WP-27 (P4) → WP-29.

### 2026-11-20 — Danen: WP-13 ✅, WP-14 ✅, WP-10 ✅
- WP-13 `national_profiles` (+ elig/horizons/commodities): 598 baris, 23 dtk; task1 meneruskan eligibility. Catatan: daging ayam β_e(8) −1,67 (SE cluster) → cek tanpa 2020.
- WP-14 `event_paths/placebo_starts/placebo_bands`: 1.690 baris nasional; kandidat plasebo 164 minggu unik (D-110).
- WP-10 `qa.*` + `coverage_table` → `stage0_report`: 59 lonjakan ditandai; impor 241/241 cocok; bias Bapanas beras +0,107 log. U17, U20 🟢.
- stage0 ulang dengan config beku: `mde` sama (G-power: LP tetap utama). stage0 kini berhenti di WP-07 (Ardell).
- Konflik autostash setelah merge (5 dokumen) dipulihkan dari stash@{0}; isi = versi hasil merge + aturan git + G6.
- Tes baru: test_event_study, test_qa. Handoff: docs/handoff/20261120-2353_danen-ke-ardell_lp-event-qa.md.

### 2026-11-20 — Danen: WP-11 ✅ (G6, praregistrasi beku)
- Keputusan G6 (Danen): varian D-011, pakan 0,6/0,4 D-012, 5 grup fokus D-013 → FINAL tanpa perubahan; H5 koreksi Holm (`params.forecast.h5_correction`, D-109).
- Beku 2026-11-20 23:29 WIB; sha256 params 67e08398…, commodities 883eee0a… (PREREGISTRATION §5). β Task 1 belum dilihat.
- U10 🟢. Berikutnya: ulang stage0 (setelah `git pull --autostash`) → national_profiles → WP-14 → WP-10.

### 2026-11-20 — Danen: WP-06 ✅, WP-08 ✅, WP-09 ✅ (sementara), WP-13 🔶
- WP-06 `drivers.find_episodes/mark_episode_weeks/fx_variation_table`: 13 episode (2018 ×3, 2020 ×2, 2021, 2022, 2023, 2024 ×2, 2025, 2026 ×2), 61 minggu; 259/200/5 minggu dep/app/nol.
- WP-08 `panel.build_region_panel` (dua arah, tahan komposisi, D-106): 32.480 baris; minggu 2022-05-02 kosong di 5 wilayah.
- WP-13 sebagian: `build_design`, `regressors`, `fit_lp`, `fx_self_response` (D-107); β data asli belum dilihat. γ(4/8/12) = 1,44/1,32/1,03.
- WP-09 `power.compute_mde/null_se/gate_g_power`: MDE_PT(8) nasional bawang putih 2,52, gula 0,90, minyak goreng 0,465 → LP tetap utama (sementara, sebelum G6; D-007).
- stage0: tabel WP-07 dipindah ke akhir; kini berhenti di WP-10. Tes baru: test_panel, test_local_projection, test_power (+ episode di test_drivers).
- Handoff: docs/handoff/20261120-2230_danen-ke-ardell_p1-dan-lp.md. P1 + mde diunggah ke Drive tim lewat Chrome (data/processed: drivers_weekly, panel_weekly_region; results/stage0: episodes, fx_variation, mde). Belum: commit kode.
- Nama branch kini `feat/<fungsi>` maks 3 kata, pesan commit tanpa kode (D-108; CLAUDE §4.6, PEMBAGIAN §8, HANDOFF); branch sesi ini `feat/episode-panel-mde`.
- Aturan git diperbarui (D-108): commit `<tipe>: <deskripsi>`, merge `--no-ff` ke dev, branch `feat/` tidak dihapus; CLAUDE §4.6, DECISIONS, PEMBAGIAN §8, HANDOFF §6.
- Berikutnya: G6 (WP-11) → ulang stage0 → `national_profiles` → WP-14 → WP-10 → G-power 23 Nov.

### 2026-11-20 — Danen: data mentah & artefak Tahap 0 diunggah ke Drive tim
- Lewat Chrome Danen (token Drive belum ada, U100): struktur `data/raw/<13 sumber>/`, `data/interim/`, `data/processed/`, `results/stage0/`.
- Terunggah: 23/24 file mentah + checksums.csv; pihps_daily, panel_weekly, world_prices_weekly, eligibility. Folder dikonfirmasi dibagikan terbatas (U24).
- `faostat/SUA_Crops_Livestock_E_Asia.zip` (14 MB > batas unggah ekstensi) diseret manual oleh Danen; dicek ada di Drive → 24/24 lengkap.
- Handoff: docs/handoff/20261120-2010_danen-ke-semua_data-di-drive.md. CLAUDE.md §2 diperbarui.

### 2026-11-20 — Danen: pembagian tugas ulang Danen–Ardell (D-105)
- Tiap Task dipegang berdua: Danen WP-06, 08, 09, 10, 11, 13, 14, 18, 21, 22, 27, 28, 29, 30; Ardell WP-07, 15, 16, 17, 19, 20, 23, 24, 25, 26, 31, 32.
- Diperbarui: PEMBAGIAN_TUGAS §1/§3/§4/§5, papan WORKPLAN (PIC WP-15–18, 21, 22, 27), CLAUDE.md §2/§21, DECISIONS D-105.
- Handoff: docs/handoff/20261120-1900_danen-ke-ardell_pembagian-ulang.md. Belum: Ardell mengonfirmasi (status terbuka).

### 2026-11-20 — Danen: panel provinsi ikut paket juri (D-104)
- Izin BI mencakup redistribusi turunan → `panel_weekly` ship=True (artifacts.py); docstring panel/deviations/task1 diperbarui.
- ARCHITECTURE §5–6 (Tingkat B kini lengkap di tingkat provinsi), CLAUDE §2/§8.4/§19/§21/§22, README hak data, U13, D-015 → D-104.

### 2026-11-20 — Danen: izin BI aman (U13)
- U13 🟢: izin BI diperoleh (konfirmasi Danen). Tugas email Abi dicoret (WORKPLAN WP-35, PEMBAGIAN §6.1, handoff onboarding).
- Cakupan izin untuk redistribusi `panel_weekly` (panel provinsi) ke juri belum dicatat → `ship` tetap False sampai dikonfirmasi.

### 2026-11-20 — Danen: verifikasi Pink Sheet (U101, U16)
- Unduh resmi: rilis 3 Nov 2026 identik byte-per-byte dengan file tim (SHA-256 3c8d9d8d…); `Mismatch Details` bagian file resmi → U101 🟢.
- URL di sources.yaml ternyata rilis Jan 2025 (selisih ≤0,005 = revisi historis WB, sempat salah dikira file disusun ulang).
  download kini mencari tautan terbaru di halaman Commodity Markets (`landing_url`/`link_pattern`) → U16 🟢; tests/test_download.py.
- Bug: Python Windows tanpa CA → download pakai certifi (SSL tetap diverifikasi). _redownload dibersihkan.

### 2026-11-20 — Danen: aturan branch (D-103)
- Branch hanya `main` (stabil), `dev` (integrasi), `feat/<topik>` (dari dev, PR ke dev); dev → main lewat PR. Ganti aturan danen/…/ardell/….
- CLAUDE.md §4.1/§4.6/§21, PEMBAGIAN_TUGAS §8, HANDOFF (contoh branch), handoff onboarding (Ardell: feat/wp07-reference-tables).
- Branch `dev` belum ada di remote (baru `main`): dibuat Danen.

### 2026-11-20 — Danen: pihps_v1 dipensiunkan (D-102)
- Zip PIHPS pra-merge → data/raw/_superseded/bi_pihps/; dicabut dari sources.yaml, LOADERS, tes, qa.compare_pihps_versions, stage0, WP-10.
- U104 ditutup. Sumber terdaftar: 20 (24 file).

### 2026-11-20 — Danen: data mentah ke Drive tim + dataset baru (D-101)
- utils.drive.push_raw/pull_raw + CLI drive-push-raw/drive-pull-raw; notebook 00 memanggil pull_raw; Kaggle/Colab punya fallback raw_dir.
- Inventaris 20 Nov: BPS impor v2 (+bawang putih), revisi regulasi 20 Nov, + jarak_hub, konkordansi_hs, hortikultura_produksi
  (loader + tes). Versi lama → data/raw/_superseded/; inventaris xlsx → docs/arsip/. checksums: 25 file.
- Isu baru U101 (Pink Sheet), U102 (overlap Comtrade–BPS), U103 (unggah penduduk & kab/kota), U104 (pihps_v1). U5/U6/U14 diperbarui.
- Handoff: docs/handoff/20261120-1617_danen-ke-semua_data-mentah-drive.md. Belum: drive-push-raw sungguhan (butuh token Danen).

### 2026-11-20 — Danen: output notebook langsung ke Drive tim (D-100)
- src/utils/drive.py (pull/push/credentials/connect/authorize_local) + configs/runtime.yaml (folder ID 15T5ry1V…) + CLI drive-pull/push/auth;
  extra opsional `[drive]`; .gitignore menolak client_secret*.json & drive_token*.json. Colab menulis ke /content/kagami_out lalu push.
- 6 notebook: drive.pull(cfg, <tahap>.REQUIRES) sebelum cek input, drive.push setelah run; teks "unduh manual" diganti.
- tests/test_drive.py (Drive palsu) + tes notebook/runtime diperbarui. Dokumen disinkronkan (NOTEBOOKS ditulis ulang, ARCHITECTURE,
  CLAUDE §2/§4/§5/§7.3/§9/§16/§17/§21/§22, README, PEMBAGIAN, HANDOFF, WORKPLAN, onboarding). U100 baru: token Drive Kaggle [HUMAN].
- Belum diuji ke Drive sungguhan (butuh token/login); lokal tanpa library Google → pesan jelas.

### 2026-11-20 — Danen: dokumen selalu mutakhir + git hanya bila diminta
- CLAUDE.md §3.4: matriks jenis perubahan → dokumen wajib diperbarui; aturan menulis anti-basi; catatan bertanggal = jejak sejarah.
- tests/test_docs_sync.py (12 cek): tautan/path, papan WP vs todo(), §2 Selesai vs papan, ID D-/U-, params.*, sumber, komoditas,
  notebook, subpaket+pyproject, daftar tes. Audit awal: hanya aturan git yang perlu diubah.
- Aturan git: agent tetap tidak commit/push; command siap copas hanya bila user meminta (CLAUDE §3.3/§4.6/§24, HANDOFF, PEMBAGIAN).

### 2026-11-20 — Danen: format handoff
- docs/HANDOFF.md: 8 jenis handoff, nama file, template, field wajib, versi pendek chat, siklus status, peran agent.
- Handoff pertama: docs/handoff/20261120-1416_danen-ke-semua_onboarding.md (Ardell & Abi). tests/test_handoff.py (diuji 7 mutasi).
- SESSION_LOG dipecah per anggota (entri di bagian sendiri) agar tidak konflik merge; CLAUDE.md §3, PEMBAGIAN_TUGAS, WORKPLAN diperbarui.

### 2026-11-20 — Danen: kepanjangan KAGAMI final
- KAGAMI = Kurs-Associated Grocery Analysis of Markets in Indonesia (bukan "Atlas"), mengikuti nama repo GitHub. D-028 direvisi; 8 file diperbarui.

### 2026-11-20 — Danen: aturan git + .gitignore
- Repo git sudah di-init user (remote origin = kurs-associated-grocery-analysis-of-markets-in-indonesia). Agent DILARANG commit/push/add
  dan perintah git yang mengubah state; hanya command siap copas (CLAUDE.md §4.6, PEMBAGIAN_TUGAS §8).
- .gitignore: data/raw/* (kecuali checksums.csv, manual_regulation/), data/interim/, data/processed/, results/* (kecuali findings.md),
  dist/, cache, kaggle.json/.env, file Windows. Diverifikasi dengan git check-ignore.

### 2026-11-20 — Danen: pembagian tugas tim
- docs/PEMBAGIAN_TUGAS.md: Danen jalur A (WP-06, 08–11, 13–17, 28–30), Ardell jalur B (WP-07, 18–27, 31–32), Abi jalur C non-teknis
  (WP-11 naskah, 33–35, data manual). Kepemilikan file, jadwal 20–29 Nov, titik terbit P1–P5, skema CSV data manual, aturan file bersama.
- WORKPLAN: kolom PIC; G-het & WP-18 bergeser ke 25 Nov (butuh P2). CLAUDE.md §3.0: agent tanya nama anggota, hanya file milik sendiri.
- Penomoran baru: D-100+/U100+ Danen, D-200+/U200+ Ardell, D-300+/U300+ Abi.

### 2026-11-20 — Sesi 9: ganti nama RupiahPass → KAGAMI (D-028)
- KAGAMI = Kurs-Associated Grocery Analysis of Markets in Indonesia (鏡, cermin). 73 file diganti: paket/CLI `kagami`, env `KAGAMI_*`,
  zip & dataset Kaggle `kagami-*`, Drive `MyDrive/kagami`, notebook, tes, app, dokumen. PDF proposal tidak diganti namanya.
- Judul README/OVERVIEW/CLAUDE/app/pyproject memuat kepanjangan. Bila paket lama `rupiahpass` pernah di-install editable, uninstall.
- Berikutnya: WP-06 (menunggu persetujuan user); G6 besok (WP-11).

### 2026-11-20 — Sesi 8: CLAUDE.md diperluas
- CLAUDE.md ditulis ulang jadi buku pegangan ~1.000 baris (26 bagian: konteks, protokol, lingkungan, lapisan, runtime, artefak,
  inventaris fungsi, data, desain, metode, gerbang, resep WP, konvensi, tes, notebook, app, hak data, klaim, D/U, jebakan, template).
- §9 inventaris dijaga `tests/test_claude_md.py` (heading per modul, fungsi publik, status ✔/⬜ WP sesuai todo()); diuji mutasi.
- `params.weekly.min_obs_days` dihapus (tak terpakai). DECISIONS & OPEN_ISSUES diurutkan menurut nomor. pytest 77/77.
- Berikutnya: WP-06 (masih ditunda sampai user setuju); G6 besok (WP-11).

### 2026-11-20 — Sesi 7: skeleton v2 — src berlapis + notebook (D-026, D-027)
- Atas permintaan user: `src/` → utils/data/features/models/evaluation/stats/pipelines/viz; 6 notebook (`notebooks/00..05`).
- Runtime: `Config` raw_dir/out_dir/artifact_dirs + `utils/env.init_runtime` (lokal/Kaggle/Colab); `bundle [--raw]`; runbook docs/NOTEBOOKS.md.
- viz/plots.py dipakai app & notebook. Tes baru: runtime, notebooks (sel setup identik + jalan lokal), viz; wiring mencakup app/notebook.
- E2E: zip kode diekstrak → notebook 00 jalan dengan raw & output di folder terpisah, berhenti di WP-06 sesuai harapan.
- WP-06 ditunda atas permintaan user. Berikutnya: lanjut WP-06 bila user setuju; `[HUMAN]` setup Kaggle/Drive (WP-35).

### 2026-11-20 — Sesi 6: WP-05 ✅
- `build_national_drivers`, `build_world_prices` + 4 tes sintetis (`tests/test_drivers.py`); `world_prices_weekly` ditulis.
- `drivers_weekly` belum ditulis: kolom `episode` menunggu WP-06 (`mark_episode_weeks` stub baru, dipanggil di `stage0/run.py`).
- Fakta: lihat WP-05 di WORKPLAN (sd de 0,0082; 5 minggu Lebaran diisi; Pink Sheet s.d. Okt 2026). D-025 dicatat; param baru `period.driver_buffer_weeks`.
- Berikutnya: WP-06 (episode + fx_variation + mark_episode_weeks) → WP-08.

### 2026-11-20 — Sesi 5: tata letak src/ (D-024)
- User memindahkan isi paket ke `src/`. Disesuaikan: pyproject `package-dir`, alias tanpa-instalasi di `tests/conftest.py` & `app/common.py`,
  path di CLAUDE/ARCHITECTURE/DATASETS/test_wiring; folder kosong `src/kagami/` dihapus (menutupi paket).
- pytest 55/55 tanpa instalasi; editable install + CLI diverifikasi di venv sementara. CLI di mesin user butuh `pip install -e .` sekali.

### 2026-11-20 — Sesi 4: WP-04 ✅
- `eligibility` diimplementasi + 2 tes sintetis (celah 8 vs 9, cakupan tahunan, share, hanya `missing` dihitung); `results/stage0/eligibility.csv` ditulis.
- 337/340 seri layak (99,1%); tidak ada seri layak yang dekat ambang. Tidak layak: cabai_rawit prov 1, 3, 5 → cabai rawit = 31 provinsi.
- U2 & U23 ditutup; D-006 FINAL (start 2018; start 2020 tidak menambah seri layak).
- `stage0` sekarang berhenti di WP-05. Berikutnya: WP-05 (penggerak) → WP-06 (episode) → WP-08 (panel wilayah); WP-07 & WP-25 paralel; WP-11 (G6) besok.

### 2026-11-20 — Sesi 3: U18 diputuskan
- Varian minyak goreng → Kemasan Bermerk 1 atas keputusan user (D-023). `pihps_daily` (800.642) & `panel_weekly` dibangun ulang.
- Status sel sekarang: observed 49,2% · carry_forward 49,2% · missing 1,0% · short 0,6%. Minyak goreng: missing 0,2%, carry_forward 87%.
- Seri > 5% minggu kosong tinggal cabai_rawit prov 1/3/5 (U23). Varian lain di D-011 tetap PROVISIONAL sampai G6 (WP-11).

### 2026-11-20 — Sesi 2: WP-03 ✅
- `select_variants` + `aggregate_weekly` diimplementasi; `pihps_daily` (795.174 hari) & `panel_weekly` (157.760 sel, 464 minggu) ditulis.
- Status sel: observed 49,9% · carry_forward 47,9% · missing 1,7% · short 0,6%. carry_forward per komoditas: beras 0,92, daging sapi 0,90,
  gula 0,85, minyak goreng 0,74, telur 0,43, bawang putih 0,39, bawang merah 0,22, daging ayam 0,21, cabai merah 0,08, cabai rawit 0,07 (U22).
- Seri > 5% minggu kosong: cabai_rawit prov 1/3/5 (0,90/1,00/0,90); minyak_goreng prov 9/31/34 (1,00/0,67/0,66) → U18, U23.
- BUG loader diperbaiki (D-022): varian di akhir file v2 salah grup; sebelum fix, cabai rawit & minyak goreng tampak hilang di lebih banyak provinsi.
- Cakupan varian (provinsi dengan ≥ 80% minggu): Minyak Goreng Kemasan Bermerk 1 & 2 = 34/34, Curah 31/34; Cabai Rawit Hijau 31/34, Merah 31/34;
  Gula Lokal 34 vs Premium 32; Beras Medium I 34; Daging Sapi Kualitas 1 34 vs 2 32.
- Berikutnya: WP-11 harus memutuskan U18 (rekomendasi: Kemasan Bermerk 1) sebelum WP-04; lalu WP-04 → WP-05/06 → WP-08.

### 2026-11-20 — Sesi 1: skeleton (WP-00, WP-01, WP-02, WP-12)
- Paket `kagami` + CLI + registry 31 artefak + app 6 halaman (menampilkan "menunggu hasil") + 4 file tes.
- Data mentah dipindah ke `data/raw/<sumber>/` (D-002); `checksums.csv` dibuat (22 file).
- Diimplementasi & dites: snapshot, download, 18 loader, stats engine (OLS cluster, NW, DM, block bootstrap, circular shift, DL/REML/EB/BH).
- Fakta data: PIHPS 34 prov × 10 komoditas × 21 varian, 2017-03-28..2026-11-19; cakupan 2018–19 ≈ 0,87–0,95 (U2 hampir pasti aman);
  JISDOR s.d. 2026-11-18 (18.252); Pink Sheet s.d. 2026-10; FAOSTAT SUA tanpa bawang putih kering (U5); exim `Totals` = USD (D-019).
- Isu baru: U14 populasi provinsi, U15 n_kota, U18 minyak goreng curah, U19 endpoint PIHPS vs "unduh resmi", U20 pemetaan Bapanas, U21 GKG→beras.
- Berikutnya: WP-03 → WP-04 → WP-05/06 → WP-08 → WP-09 (G-power 23 Nov); WP-07 & WP-25 paralel; WP-11 sebelum 21 Nov.

---

## Ardell

### 2026-11-21 — Ardell: persiapan Colab notebook 01 & 04 (checkpoint Task 1, uji end-to-end)
- Setelah merge Danen (`dev`): `joint_bootstrap`/`circular_placebo` + `task1.run` punya checkpoint & resume ke Drive (D-204); `tests/test_task1.py` menjalankan `task1.run` end-to-end pada artefak sintetis. Error SVD macOS belum tertutup oleh D-119 → handoff `20261121-2100_ardell-ke-danen_svd-macos.md` (tidak menghalangi Colab/Linux).
- Handoff Danen `ols-cluster` dan `sinkron-dokumen` ditutup (dokumen §9, artefak, tes, D-121 sudah dikerjakan Danen di `dev`).

### 2026-11-21 — Ardell: WP-31, WP-32 🔶 (app dan paket juri: persiapan sebelum artefak final)
- `src/viz/plots.py` (+`sensitivity_heatmap`, `cluster_sizes`), halaman 2/3/4 dan Home diperluas; `tests/test_app_data.py` (semua halaman dengan artefak sintetis berskema kontrak) dan `tests/test_package.py` (isi zip, hak data, CLI dari folder ekstrak).
- `tests/test_wiring.py`: `kagami.utils.todo` dikecualikan dari tes modul terpakai (semua stub sudah terimplementasi, pembantu itu tak dipakai lagi) — dicatat di handoff untuk Danen.
- Sisa: artefak nyata, teks app dari Abi, findings, `package` tanpa `--allow-missing` dan uji jalan ulang G7 (28 Nov).

### 2026-11-21 — Ardell: WP-23, WP-24 🔶 (meta-regresi provinsi, interaksi FE)
- `models/association.py::meta_regression/fe_interaction` + `tests/test_association.py`; `pipelines/task3.py` meneruskan `elig`. Koefisien tertanam dipulihkan; CR2 ≈ SE model pada data homoskedastis; bootstrap hanya melebarkan interval.
- Data asli: `fe_interaction` 0,3 dtk pada 154 ribu baris (hanya ln_dist_hub; penduduk & n_kota belum ada), belum ditafsirkan. D-203.
- Berikutnya: WP-31 (app) → WP-32 (paket juri); run penuh P2/P3 setelah data Drive.

### 2026-11-21 — Ardell: WP-19, WP-20 🔶 (clustering, pilih k, stabilitas, pembanding partisi)
- `features/clustering.py`, `models/clustering.py`, `evaluation/stability.py`, `pipelines/task2.py` (menyesuaikan: matriks plasebo mentah untuk planted, baris K-Means, n_kota dari `province_features`); `tests/test_clustering.py`, `tests/test_task2.py` (end-to-end sintetis).
- Kalibrasi: tanpa struktur, positif palsu seleksi k 1 dari 12 seed (≈ 5%); dengan struktur tertanam 3 kelompok → k = 3, ARI > 0,9, tidak ada klaster lemah. D-202. `response.shrink_deviations(check_reml=False)` untuk replikasi.
- Berikutnya: WP-23 → WP-24 → WP-31 → WP-32.

### 2026-11-21 — Ardell: WP-15, WP-16, WP-17 🔶 (deviasi provinsi, bootstrap & plasebo, EB & fitur respons)
- `models/deviations.py`, `evaluation/inference.py`, `features/response.py` + `tests/test_deviations.py`, `test_inference.py`, `test_response.py`; `pipelines/task1.py` menyesuaikan pemanggil (est menerima harga dunia, elig ke deviasi, provinsi h kunci dalam replikasi).
- Data asli (tanpa harga dunia, B = 3): nasional + provinsi 2,6 dtk/replikasi; deviasi provinsi 1.011 baris 0,6 dtk, Σ δ = 0, cabai rawit 31 provinsi; R8 nasional beras 0,084 = profil Danen.
- Temuan: `np.linalg.pinv(X'X)` di `stats.ols_cluster` gagal ("SVD did not converge") pada satu desain bootstrap di macOS (numpy 2.3.5 & 2.5.5, matriks rank penuh, cond 60); `pinv(hermitian=True)` benar. Diminta ke Danen lewat handoff; uji lokal memakai workaround di skrip sementara. D-201.
- Berikutnya: WP-19 → WP-20; run penuh task1 (Kaggle) setelah `world_prices_weekly` tersedia → P2.

### 2026-11-20 — Ardell: ketahanan sesi Task 4 + handoff ke Danen
- Catatan Danen (mekanik kerja): `forecast_preds` kini artefak `task4` (`ship=False`) yang di-push ke Drive; `rolling_predictions` punya `checkpoint`/`done` (run ulang melanjutkan); `task4.run` menyimpan tiap 10 origin.
- Inventaris dataset (docs/arsip) +2 butir `Belum Lengkap` (n_kota, faktor GKG). Handoff: docs/handoff/20261120-2000_ardell-ke-danen_wp07-wp25-26-kontrak.md.

### 2026-11-20 — Ardell: WP-25 ✅, WP-26 🔶 (fitur as-of + model M0–M3 rolling-origin)
- `src/features/forecast.py` (`origins`, `feature_table`, `split_origin`, `build_features`) dan `src/models/forecasting.py` (`fit_predict`, `rolling_predictions`, model `M2_nofx` untuk ablation); `params.forecast.run_m3`.
- `tests/test_forecast.py` + `synthetic_task4_inputs` di `tests/synthetic.py`. Uji kebocoran: train t+h ≤ origin, `available_at` ≤ minggu fitur, fitur minggu ≤ t0 tidak berubah saat data setelah t0 diacak.
- Data asli (tanpa harga dunia): 75 origin h=8; M3 ≈ 1,5–2 dtk per origin. Run penuh menunggu `world_prices_weekly` & `drivers_weekly` (P1).
- Label model untuk WP-27 (Danen): `M0`, `M1`, `M2`, `M3`, `M2_nofx`; kolom `province_id` (bila panel provinsi), `region`, `commodity`, `y_true`, `y_pred`, `large_move`.

### 2026-11-20 — Ardell: WP-07 🔶 (tabel referensi: kode + tes sintetis) + generator sintetis Task 1
- `src/data/reference.py`: `build_concordance/exposure/regulation/province_features` + `parse_regulation_dates`, `classify_verification`; `loaders.py`: `load_penduduk/n_kota/gkg_beras` (NaN-aman); `sources.yaml` +3 sumber `optional`; `params.association.import_ratio_years`; `stage0` memanggil dengan input baru.
- Tes: `tests/test_reference.py`, `tests/test_synthetic.py` + `tests/synthetic.py` (panel provinsi & profil nasional dummy, jawaban tertanam); `test_loaders`/`test_config` disesuaikan.
- Data asli: regulation = 72 baris dari 3 sumber (30 verified, 24 confirmed, 13 partial, 5 unverified); dist_hub_km dari koordinat crosswalk.
- Belum divalidasi pada data asli: FAOSTAT, konkordansi, jarak_hub, penduduk belum ada lokal (butuh `drive-pull-raw`, U100); `n_kota` & `gkg_beras` menunggu Abi (U15, U21). D-200.
- Berikutnya: WP-25 → kerangka WP-15/16/17 (sintetis); final WP-07 + P3 24 Nov.

---

## Abi

(belum ada entri; Abi tanpa git → entri ditulis di chat/Drive, disalin Danen/Ardell saat commit)
