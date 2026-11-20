# Log Keputusan (ADR ringkas)

Format: **D-nnn — judul** · status (FINAL / PROVISIONAL / DIGANTI oleh D-xxx) · tanggal · sumber.
Keputusan baru ditambahkan di bawah; jangan hapus yang lama, ubah statusnya. Deviasi setelah G6 (21 Nov) wajib diberi label **DEVIASI PRAREGISTRASI**.

### D-001 — Paket Python `kagami` (src layout) + CLI per tahap · FINAL · 2026-11-20
Satu perintah per tahap (`python -m kagami <stage>`), satu orkestrator `run.py` per tahap. Juri butuh "satu perintah";
agent butuh titik masuk yang jelas per WP.

### D-002 — Data mentah diorganisasi per sumber di `data/raw/<sumber>/` · FINAL · 2026-11-20
File asli dipindah (bukan disalin) dan sebagian diganti nama agar bebas spasi/koma; pemetaan di DATASETS.md §Asal file.
Isi file tidak diubah (hash di checksums.csv).

### D-003 — Registry artefak sebagai kontrak antar-tahap · FINAL · 2026-11-20
`artifacts.py` = path + kolom wajib + WP produsen + flag `ship`. `io.write_artifact` memvalidasi kolom. App & tahap
berikutnya hanya bergantung pada kontrak ini, sehingga WP bisa dikerjakan terpisah oleh sesi berbeda.

### D-004 — Clustering selalu dijalankan, dinilai terhadap plasebo · FINAL · proposal v4 §5.3
Kontribusi data mining tidak boleh bergantung pada lolosnya G-het. k = 1 adalah hasil sah.

### D-005 — Inferensi berbasis minggu · FINAL · proposal v4 §4.4, §5.2d
IDR/USD identik untuk semua provinsi pada minggu yang sama → SE cluster per minggu; bootstrap/plasebo per minggu;
jumlah observasi efektif dilaporkan sebagai jumlah minggu. Driscoll–Kraay tidak dipakai (under-coverage).

### D-006 — Periode mulai 2018-01-01 · FINAL · 2026-11-20 (WP-04)
337/340 seri (99,1%) layak dengan start 2018, ≥ ambang keputusan 80%. Start 2020 juga memberi 337/340, jadi fallback
tidak memberi manfaat. Grid: 464 minggu, 2018-01-01 .. 2026-11-16.

### D-007 — Aturan gerbang G-power · FINAL (ambang) · proposal v4 §9.1
MDE PT(8) nasional > 0,5 untuk ketiga {bawang putih, gula pasir, minyak goreng} → LP mingguan sekunder; event study +
profil harga dunia rupiah utama; Task 4 kontribusi DM utama. Angka MDE aktual ditambahkan di sini saat WP-09 selesai.

### D-008 — PIHPS v2_merged sebagai sumber kanonik · FINAL · 2026-11-20
v2 punya MANIFEST (sha256 + endpoint + retrieved_at) dan tanpa kolom `no`. v1 disimpan hanya untuk QA konsistensi (WP-10).

### D-009 — Mesin statistik numpy/scipy sendiri, tanpa statsmodels/linearmodels · FINAL · 2026-11-20
Bootstrap/plasebo 499 replikasi × ratusan regresi butuh OLS tervektorisasi; dependensi juri lebih sedikit
(statsmodels tidak terpasang di lingkungan saat ini). Implementasi + tes di `stats/`.

### D-010 — App Streamlit hanya membaca artefak · FINAL · proposal v4 §7
Tidak ada login, input data pengguna, atau estimasi saat runtime. Artefak belum ada → label "Menunggu hasil (WP-xx)".

### D-011 — Varian representatif · PROVISIONAL sampai G6 · 2026-11-20
Beras → Medium I; Bawang Putih/Merah → Ukuran Sedang; Gula → Lokal; Minyak Goreng → ~~Curah~~ Kemasan Bermerk 1 (D-023); Daging Ayam → Ras Segar;
Telur → Ras Segar; Daging Sapi → Kualitas 1; Cabai Merah → Keriting; Cabai Rawit → Merah.
Aturan: varian yang paling dekat dengan acuan HET/HAP dan konsumsi massal, dengan cakupan tertinggi.
Risiko: Minyak Goreng Curah cakupan 0,92 dan relevansi menurun setelah Minyakita (U18) — alternatif `Minyak Goreng Kemasan Bermerk 1`.

### D-012 — Komposit harga dunia pakan = 0,6·log Maize + 0,4·log Soybean meal · PROVISIONAL sampai G6 · 2026-11-20
Untuk daging ayam & telur (jalur input impor). Bobot mendekati komposisi pakan broiler jagung:bungkil kedelai.
Robustness: bobot 0,5/0,5 dan masing-masing tunggal (Tier 2).

### D-013 — Komoditas fokus = 6 komoditas PIHPS dalam 5 grup konfirmatori · PROVISIONAL sampai G6 · 2026-11-20
Proposal menyebut "5 komoditas fokus: bawang putih, gula, minyak goreng, daging ayam/telur (pakan impor), daging sapi".
Ditafsirkan: daging ayam dan telur = satu grup `pakan` untuk koreksi multiplisitas H5, tetapi diestimasi terpisah.
Kontrol domestik: bawang merah, cabai merah, cabai rawit. Lainnya: beras.

### D-014 — Urutan pemotongan lingkup · FINAL · proposal v4 §9.3
Tier 2 → analisis dalam-komoditas & Moran's I → Task 3c (WP-24) → M3 (WP-26). Tidak pernah dipotong: Tier 1, plasebo, MDE.

### D-015 — Kebijakan kirim data turunan · FINAL · 2026-11-20
Dikirim: panel 7 wilayah sebagai **indeks log** (relatif minggu pertama), penggerak mingguan sebagai log & perubahan log,
seluruh hasil estimasi, tabel buatan tim, sumber CC BY. Tidak dikirim: PIHPS/JISDOR/BPS/Bapanas mentah, panel provinsi
(kecuali izin BI, U13).

### D-016 — Harga dunia bulanan → mingguan menurut bulan observasi · FINAL · proposal v4 §6.5
Task 1–3: setiap minggu memakai nilai bulan kalender minggu tersebut (deskriptif). Task 4: as-of `available_at`.
Minggu yang melintasi dua bulan memakai bulan dari hari Senin.

### D-017 — Kerangka 34 provinsi lama · FINAL · proposal v4 §4.3
Papua Selatan/Tengah/Pegunungan → Papua; Papua Barat Daya → Papua Barat (`province_aliases.csv`).

### D-018 — Keterpencilan = ln(1 + jarak great-circle ibu kota ke hub terdekat) · FINAL · 2026-11-20
Hub: Jakarta, Surabaya, Makassar (proposal §5.4). Koordinat di `region_crosswalk.csv`. `ln(1+km)` agar provinsi hub (jarak 0) terdefinisi.

### D-019 — Kolom `Totals` file exim tahunan BPS = USD · FINAL · 2026-11-20
Diverifikasi: Σ `import_value_usd` bulanan 2023 / `Totals` 2023 = 1,000 untuk semua HS8 yang beririsan.

### D-020 — Label minggu = Senin ISO · FINAL · 2026-11-20
`utils.dates.week_start` dipakai semua modul untuk join.

### D-021 — Prioritas status sel mingguan · FINAL · 2026-11-20 (WP-03)
missing > carry_forward (cf_share > 0,5) > short (n_days ≤ 2) > observed. `cf_share` disimpan agar status bisa dihitung
ulang dengan aturan lain. Rangkaian identik dihitung atas hari TERAMATI (hari kosong tidak memutus rangkaian) dan pada
seluruh riwayat sebelum dipotong ke `period.start`. `pihps_daily` hanya memuat hari teramati dengan harga > 0.

### D-022 — Grup varian PIHPS dari prefiks nama, bukan urutan baris · FINAL · 2026-11-20 (WP-03)
File v2 "merged" menaruh varian hasil penggabungan di akhir file (Aceh, Riau, Kepri, Lampung, Bali, Gorontalo, Sulsel),
sehingga `ffill` dari baris level-1 menempelkannya ke komoditas yang salah (mis. Cabai Rawit Merah → Gula Pasir).
Semua nama varian diawali nama komoditas level-1-nya; loader kini memakai prefiks dan error bila tidak cocok.
Tes regresi: `test_pihps_variant_groups_by_prefix`.

### D-023 — Varian minyak goreng = Kemasan Bermerk 1 · FINAL (keputusan user) · 2026-11-20
Curah tidak tersedia di Babel dan berhenti di Maluku (2023) & Papua Barat (2021); Kemasan Bermerk 1 tersedia di 34/34 provinsi
(cakupan 0,998). Efek di panel: minggu `missing` minyak goreng 7,1% → 0,2%. Konsekuensi: harga kemasan lebih kaku
(87% minggu `carry_forward` vs 74% Curah), sehingga respons terhadap harga sawit dunia bisa lebih kecil/lambat — tulis ini
saat menafsirkan PT/W minyak goreng. Curah dipakai di robustness Tier 2 `alternative_variants` (WP-30) pada provinsi yang tersedia.

### D-024 — Isi paket langsung di `src/` · FINAL (keputusan user) · 2026-11-20
User memindahkan isi `src/kagami/` ke `src/`. Nama import tetap `kagami` lewat `package-dir = {kagami = "src"}`
di pyproject (daftar `packages` eksplisit). Tanpa instalasi, `tests/conftest.py` dan `app/common.py` mendaftarkan
`kagami` → `src/`. `PYTHONPATH=src` tidak lagi dipakai (akan mengekspos `stage0`, `config`, dst. sebagai modul top-level).
Diverifikasi: pytest 55/55 tanpa instalasi; `pip install -e .` + `python -m kagami status/stage0` di venv bersih.

### D-025 — Konstruksi penggerak mingguan · FINAL · 2026-11-20 (WP-05)
1. Minggu tanpa fixing/observasi → level log diteruskan (Δ = 0 minggu itu, perubahan masuk minggu berikutnya), ditandai `*_filled`.
   Alternatif (NaN) akan membuang 2 minggu × 5 Lebaran dari LP; robustness Tier 1 "exclude" dapat membuang minggu bertanda.
2. Harga dunia rupiah memakai rerata JISDOR BULANAN (METHODS §M0.4), jadi `dw` hanya berubah di minggu pertama bulan baru;
   docstring lama yang menyebut "komponen kurs mingguan" dikoreksi. Ini menjaga `de` dan `dw` terpisah secara empiris.
3. Grid penggerak mulai `period.start` − 52 minggu (`params.period.driver_buffer_weeks`) untuk lag dan jendela episode.

### D-026 — `src/` berlapis: utils / data / features / models / evaluation / stats / pipelines / viz · FINAL (permintaan user) · 2026-11-20
Menggantikan tata letak per-task (stage0/, task1..4/). Modul dipindah tanpa mengubah isi; `pipelines/<tahap>.py`
menjaga urutan per task (satu modul = satu notebook = satu perintah CLI) dan satu-satunya pemanggil `write_artifact`.
Pemetaan lama → baru: stage0/{loaders,snapshot,download,weekly,drivers,reference,panel,qa} → data/; stage0/power → evaluation/;
task1/lp → models/local_projection; task1/{deviations,event_study} → models/; task1/inference → evaluation/; task1/features →
features/response; task2/clustering → features/clustering (matriks) + models/clustering (Ward, pilih k); task2/{heterogeneity,
stability,planted} → evaluation/; task3/{commodity,province} → models/association; task4/features → features/forecast;
task4/models → models/forecasting; task4/evaluation → evaluation/forecast_eval; robustness → evaluation/robustness (cek) +
pipelines/robustness (run); package → pipelines/package; config/io/artifacts/_todo → utils/; week_start → utils/dates.

### D-027 — Notebook per tahap yang jalan di lokal/Kaggle/Colab · FINAL (permintaan user) · 2026-11-20
Perangkat lokal tidak kuat untuk bootstrap/plasebo 499 replikasi dan rolling-origin. `Config` memisahkan root (kode),
raw_dir (mentah; `sources.yaml` kini relatif raw_dir), out_dir (tulis) dan artifact_dirs (baca output tahap sebelumnya);
`utils/env.init_runtime` mengisinya per platform. Sel setup notebook menemukan kode tanpa `pip install`.
Distribusi: `python -m kagami bundle [--raw]` → dataset Kaggle `kagami-code` + `kagami-raw` (PRIVAT) atau Google Drive.
Notebook tidak berisi logika; diverifikasi ujung-ke-ujung (bundle diekstrak → notebook 00 jalan dengan raw & output terpisah).
`checksums.csv` kolom `file` kini relatif raw_dir (dimigrasi, waktu catatan dipertahankan).

### D-028 — Nama proyek: KAGAMI (Kurs-Associated Grocery Analysis of Markets in Indonesia) · FINAL (keputusan user) · 2026-11-20
Menggantikan "RupiahPass". Kagami (鏡) = cermin: apakah harga pangan mencerminkan rupiah, dan di mana pantulannya paling kuat.
Kepanjangan memakai kata "Associated" agar sesuai sifat temuan yang asosiasional (rambu klaim). Penggantian menyeluruh:
nama tampilan (README, app, dokumen), paket Python & CLI (`rupiahpass` → `kagami`, `python -m kagami`), env var
(`RUPIAHPASS_*` → `KAGAMI_*`), zip (`kagami_code.zip`, `kagami_raw_PRIVATE.zip`, `kagami_submission.zip`), dataset Kaggle
(`kagami-code`, `kagami-raw`), folder Drive (`MyDrive/kagami`). Entri log/keputusan lama juga ikut diganti; nama lama yang
tersisa hanya di nama file PDF proposal (dokumen asli, tidak diubah).
Revisi 2026-11-20 (user): huruf A kedua = **Analysis** (semula "Atlas") agar sama dengan nama repo GitHub
`danenftyessir/kurs-associated-grocery-analysis-of-markets-in-indonesia`.

### D-100 — Output & input notebook lewat folder Google Drive tim (Drive API) · FINAL (permintaan user) · 2026-11-20 · Danen
Menggantikan unduh manual / "Add Input → Notebook Output" (D-027). Folder tim dirujuk lewat ID di `configs/runtime.yaml`
(https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D). `src/utils/drive.py`: `pull` (input tahap → out_dir) di awal notebook, `push` (artefak tahap → Drive, timpa versi
lama) di akhir; CLI `drive-pull`, `drive-push`, `drive-auth`. Struktur di Drive = path artefak. Alasan Drive API (bukan mount):
Kaggle tidak bisa me-mount Drive, dan path mount folder bersama berbeda per anggota di Colab; ID folder sama untuk semua.
Kredensial: Colab login interaktif; Kaggle Secret `KAGAMI_DRIVE_TOKEN` (token OAuth akun anggota; service account tidak
dipakai karena tidak punya kuota penyimpanan di My Drive); lokal file token. Colab kini menulis ke `/content/kagami_out`
lalu push. Library Google = dependensi opsional `[drive]` (sudah ada di Kaggle/Colab). Folder wajib dibagikan terbatas (U24).

### D-101 — Data mentah di folder Drive tim + alokasi dataset 20 Nov · FINAL (permintaan user) · 2026-11-20 · Danen
Semua data mentah (sources.yaml) + `checksums.csv` disimpan di `data/raw/` folder Drive tim (https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D) dengan path sama seperti
lokal. `utils.drive.push_raw` (Danen; MD5 sama dilewati) dan `utils.drive.pull_raw` (anggota; hanya file yang belum ada, tidak
pernah menimpa); CLI `drive-push-raw` / `drive-pull-raw`; notebook 00 memanggil `pull_raw`. Kaggle: dataset `kagami-raw` jadi
opsional (fallback `/kaggle/temp/kagami_raw`); Colab: fallback `/content/kagami_raw` bila `DRIVE_DIR/data/raw` tidak ada.
Alokasi dataset baru (inventaris 20 Nov): BPS impor bulanan v2 (`bps_trade/`, +bawang putih), revisi regulasi
(`manual_regulation/*_2026-11-20.csv`), `manual_geo/` (jarak hub), `manual_concordance/` (konkordansi HS),
`kementan_hortikultura/` (produksi ATAP). Versi lama → `data/raw/_superseded/` (tidak dipakai, tidak diunggah). Lokasi untuk file
yang belum diunggah: `bps_kependudukan/penduduk_provinsi_2025.csv`, `bapanas/panelharga_konsumen_kabkota_snapshot_2026-10.csv`.
