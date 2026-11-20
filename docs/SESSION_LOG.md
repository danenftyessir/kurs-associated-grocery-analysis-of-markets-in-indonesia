# Log Sesi (catatan kerja per anggota)

Satu bagian per anggota; **tambahkan entri baru di paling atas bagian MILIK SENDIRI** (bukan di atas file) agar tidak
bentrok saat merge antar-branch. Maksimal ~10 baris per sesi: WP yang dikerjakan, status akhir, angka penting, file yang
diubah, yang belum selesai/diblokir. Pesan ke anggota lain (artefak terbit, permintaan, blokir) → **handoff** di
`docs/handoff/` (format `docs/HANDOFF.md`), bukan di sini. Jangan duplikasi DECISIONS/OPEN_ISSUES — tautkan ID-nya.

---

## Danen

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

(belum ada entri)

---

## Abi

(belum ada entri; Abi tanpa git → entri ditulis di chat/Drive, disalin Danen/Ardell saat commit)
