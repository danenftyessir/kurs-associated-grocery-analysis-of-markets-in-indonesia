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
Pembaruan 2026-11-20 (WP-09, Danen; params SEBELUM G6): MDE_PT(8) nasional bawang putih 2,52, gula pasir 0,90, minyak goreng
0,465 → syarat "ketiganya > 0,5" TIDAK terpenuhi → LP tetap utama. Sementara: dihitung ulang setelah G6 (21 Nov), keputusan
resmi di gerbang G-power 23 Nov (`power.gate_g_power` pada `mde.csv`).

### D-008 — PIHPS v2_merged sebagai sumber kanonik · FINAL (bagian QA v1 diganti oleh D-102) · 2026-11-20
v2 punya MANIFEST (sha256 + endpoint + retrieved_at) dan tanpa kolom `no`. v1 disimpan hanya untuk QA konsistensi (WP-10).

### D-009 — Mesin statistik numpy/scipy sendiri, tanpa statsmodels/linearmodels · FINAL · 2026-11-20
Bootstrap/plasebo 499 replikasi × ratusan regresi butuh OLS tervektorisasi; dependensi juri lebih sedikit
(statsmodels tidak terpasang di lingkungan saat ini). Implementasi + tes di `stats/`.

### D-010 — App Streamlit hanya membaca artefak · FINAL · proposal v4 §7
Tidak ada login, input data pengguna, atau estimasi saat runtime. Artefak belum ada → label "Menunggu hasil (WP-xx)".

### D-011 — Varian representatif · FINAL (G6, 2026-11-20) · 2026-11-20
Beras → Medium I; Bawang Putih/Merah → Ukuran Sedang; Gula → Lokal; Minyak Goreng → ~~Curah~~ Kemasan Bermerk 1 (D-023); Daging Ayam → Ras Segar;
Telur → Ras Segar; Daging Sapi → Kualitas 1; Cabai Merah → Keriting; Cabai Rawit → Merah.
Aturan: varian yang paling dekat dengan acuan HET/HAP dan konsumsi massal, dengan cakupan tertinggi.
Risiko: Minyak Goreng Curah cakupan 0,92 dan relevansi menurun setelah Minyakita (U18) — alternatif `Minyak Goreng Kemasan Bermerk 1`.

### D-012 — Komposit harga dunia pakan = 0,6·log Maize + 0,4·log Soybean meal · FINAL (G6, 2026-11-20) · 2026-11-20
Untuk daging ayam & telur (jalur input impor). Bobot mendekati komposisi pakan broiler jagung:bungkil kedelai.
Robustness: bobot 0,5/0,5 dan masing-masing tunggal (Tier 2).

### D-013 — Komoditas fokus = 6 komoditas PIHPS dalam 5 grup konfirmatori · FINAL (G6, 2026-11-20) · 2026-11-20
Proposal menyebut "5 komoditas fokus: bawang putih, gula, minyak goreng, daging ayam/telur (pakan impor), daging sapi".
Ditafsirkan: daging ayam dan telur = satu grup `pakan` untuk koreksi multiplisitas H5, tetapi diestimasi terpisah.
Kontrol domestik: bawang merah, cabai merah, cabai rawit. Lainnya: beras.

### D-014 — Urutan pemotongan lingkup · FINAL · proposal v4 §9.3
Tier 2 → analisis dalam-komoditas & Moran's I → Task 3c (WP-24) → M3 (WP-26). Tidak pernah dipotong: Tier 1, plasebo, MDE.

### D-015 — Kebijakan kirim data turunan · FINAL (bagian panel provinsi diganti oleh D-104) · 2026-11-20
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

### D-102 — Snapshot PIHPS pra-merge (`pihps_v1`) dipensiunkan · FINAL (keputusan user) · 2026-11-20 · Danen
Inventaris tim (20 Nov) menandai zip PIHPS tanpa `v2_merged` sebagai rusak. File dipindah ke `data/raw/_superseded/bi_pihps/`
(tidak dihapus), dicabut dari `sources.yaml`, `LOADERS`, dan tes; `qa.compare_pihps_versions` dan cek "v1 vs v2" WP-10 dihapus.
`v2_merged` tetap satu-satunya sumber PIHPS (D-008). Tidak diunggah ke Drive tim.

### D-103 — Aturan branch: hanya `main`, `dev`, `feat/<topik>` · FINAL (permintaan user; bagian nama, pesan commit, merge & hapus branch DIGANTI oleh D-108) · 2026-11-20 · Danen
`main` = versi stabil (gerbang, pembekuan, submission; tanpa commit langsung). `dev` = integrasi, dibuat dari `main`, masuk ke
`main` lewat PR saat stabil. `feat/<topik>` = satu WP/topik (kode atau dokumen), dibuat dari `dev`, PR ke `dev`, lalu dihapus;
nama huruf kecil berawalan kode WP bila ada (mis. `feat/wp06-episode`). Tidak ada jenis branch lain (termasuk `fix/`, `hotfix/`,
branch per anggota). Menggantikan aturan branch per anggota (`danen/...`, `ardell/...`) di PEMBAGIAN_TUGAS §8 versi awal.
Agent tetap tidak menjalankan git yang mengubah state (CLAUDE.md §4.6).

### D-104 — Panel provinsi mingguan ikut paket juri · FINAL (keputusan user) · 2026-11-20 · Danen
Izin BI (U13) diperoleh dan mencakup redistribusi data turunan (dikonfirmasi Danen). `panel_weekly` (harga mingguan provinsi ×
komoditas + status sel) kini `ship=True`, sehingga juri dapat menjalankan ulang Task 1–4 & robustness di tingkat provinsi
(Tingkat B lengkap) tanpa unduh ulang. Tetap tidak dikirim: PIHPS mentah dan `pihps_daily` (harga harian per varian, setara
mentah). Penyebutan di makalah/README: "dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia), atas izin BI".
Menggantikan bagian "panel provinsi tidak dikirim" di D-015.

### D-105 — Pembagian tugas Danen–Ardell: tiap Task dipegang berdua · FINAL (permintaan user) · 2026-11-20 · Danen
Pembagian awal menaruh seluruh Task 1 + robustness di Danen dan seluruh Task 2–4 + app + paket juri di Ardell, sehingga Danen
menjadi leher botol jalur kritis dan Ardell menunggu keluaran Task 1. Pembagian baru memotong tiap Task: Danen = WP-06, 08, 09, 10, 11,
13, 14, 18, 21, 22, 27, 28, 29, 30; Ardell = WP-07, 15, 16, 17, 19, 20, 23, 24, 25, 26, 31, 32 (beban ± 19 satuan kerja per orang).
Rantai Task 1 dipotong di `fit_lp`/`build_design` (WP-13, terbit 22 Nov); P2 dijalankan Ardell dengan kode Danen di `dev`; P4 dipecah
(`forecast_preds` oleh Ardell, `forecast_eval`/`ablation` oleh Danen, 25 Nov). Alternatif ditolak: satu orang memegang seluruh rantai
WP-13→17 (leher botol) dan satu Task per orang (Task 1 selalu mendahului yang lain). Risiko: dua serah-terima di rantai Task 1;
dimitigasi dengan data sintetis berskema `artifacts.py` dan tenggat kode 22–24 Nov (PEMBAGIAN_TUGAS §4–5). Bukan deviasi praregistrasi
(tidak mengubah hipotesis atau parameter). Dampak dokumen: PEMBAGIAN_TUGAS §1, §3, §4, §5; papan WORKPLAN (kolom PIC); CLAUDE.md §2.

### D-106 — Panel wilayah: rerata tahan perubahan komposisi (dekomposisi dua arah) · FINAL · 2026-11-20 (WP-08) · Danen
`panel_weekly_region` = rerata log harga provinsi eligible per wilayah. Rerata biasa melompat bila satu provinsi `missing` pada suatu
minggu (wilayah 2 provinsi: lompatan = setengah selisih level; pada data asli sampai 0,10 log). Dipilih: per (wilayah, komoditas)
p(r,t) = a_r + l_t diestimasi dengan alternating projection; rerata wilayah = l_t + rerata a_r, lalu dikurangi minggu pertama.
Identik dengan rerata biasa bila semua provinsi teramati (median selisih 0). Ditolak: rerata biasa (lompatan palsu masuk LP
wilayah) dan indeks berantai (celah satu minggu menghilangkan perubahan provinsi itu). Minggu tanpa provinsi teramati → NaN
(hanya 2022-05-02, Idulfitri). Murni teknis; bukan deviasi praregistrasi.

### D-107 — Konvensi episode, desain LP, dan SE MDE · FINAL (teknis) · 2026-11-20 (WP-06, WP-09, WP-13) · Danen
(1) Episode (METHODS §M0.5): pemicu berjarak ≤ `episodes.window_weeks` minggu digabung (jendela tumpang tindih atau berdempetan);
end_week = pemicu terakhir; cum_dlog_e = Σ jendela maksimum; seluruh grid penggerak (buffer 2017) dipakai, `in_period` menandai
start ≥ period.start. (2) Desain LP (`build_design`): blok kurs berawalan `de`/`dw` (impuls + lag 1..L), kontrol `dp_l*`,
`db_l0..4`, `idf_*`, `month_2..12`; asimetris memakai lag de⁺ dan de⁻ masing-masing; efek tetap seri via within-transform setelah
baris NaN dibuang; sampel period.start..freeze. γ(h) memakai kontrol yang sama tanpa Δp & dw. (3) SE MDE (METHODS §M0.6 langkah 2):
bentuk skor di bawah H0, yaitu residual LP tanpa kurs × de yang dibersihkan dari kontrol + sisa blok kurs, cluster minggu, koreksi CR1.
Setara SE regresi residual pada de bila β ≈ 0 (tes: selisih < 5%) dan β̂ tidak pernah dihitung, sehingga aturan "MDE sebelum
melihat β" terjamin. Ditolak: rumus analitik sd(resid)/(sd(de)·√T) (mengabaikan korelasi residual antarprovinsi dalam minggu).

### D-108 — Nama branch menurut fungsi (maks 3 kata) & pesan commit tanpa kode · FINAL (permintaan user) · 2026-11-20 · Danen
Menggantikan bagian penamaan D-103 (`feat/wp06-episode`) dan aturan "pesan commit diawali kode WP" (CLAUDE.md §4.6). Kode WP
sulit dilacak orang: satu WP berisi beberapa fungsi dan satu fungsi bisa disentuh beberapa WP. Kini `feat/<fungsi>` = apa yang
dikerjakan branch itu, maksimal 3 kata, huruf kecil dengan tanda hubung (mis. `feat/depreciation-episodes`, `feat/reference-tables`).
Pesan commit dalam bahasa Indonesia menjelaskan perubahan tanpa kode WP-xx/D-xxx/U-xx. Ditolak: nama fungsi Python persis
(terlalu panjang bila satu PR berisi beberapa fungsi). Jenis branch (`main`, `dev`, `feat/`) dan aturan PR D-103 tidak berubah.
Branch pertama dengan aturan ini: `feat/episode-panel-mde`.
Pembaruan 2026-11-20 (permintaan user): (1) pesan commit berformat `<tipe>: <deskripsi>` dengan tipe `feat`, `fix`, `docs`,
`test`, `refactor`, `chore` (tabel di CLAUDE.md §4.6), deskripsi bahasa Indonesia huruf kecil tanpa kode; (2) `feat/` masuk ke
`dev` lewat `git merge --no-ff` lalu push (PR tetap boleh), pesan merge `chore: merge feat/<fungsi> ke dev`; command git yang
disiapkan agent selalu berakhir dengan merge ke `dev`; (3) branch `feat/` TIDAK dihapus setelah merge (lokal maupun remote),
agar riwayat per pekerjaan tetap bisa dilacak. Menggantikan "PR ke `dev`, lalu dihapus" di D-103.

### D-109 — Pembekuan G6 & koreksi Holm untuk H5 · FINAL (keputusan user) · 2026-11-20 (WP-11) · Danen
Danen membekukan praregistrasi pada 2026-11-20 23:29 WIB, sehari sebelum tenggat G6: varian D-011, bobot pakan D-012 (0,6/0,4),
dan 5 grup fokus D-013 menjadi FINAL tanpa perubahan. H5 diuji pada dua grup jalur {direct_import, imported_input}, dengan
α keluarga 0,05 dan koreksi Holm (`params.forecast.h5_correction: holm`). Proposal tidak menyebut koreksi ini. Ditolak: tanpa koreksi
(positif palsu lebih tinggi). sha256 params `67e0839820d7…`, commodities `883eee0a30cf…` (lengkap di PREREGISTRATION §5).
β Task 1 belum dilihat. MDE (D-007) dihitung sebelum pembekuan dengan nilai config yang sama, kecuali kunci `h5_correction`
dan komentar. Setiap perubahan setelah ini = DEVIASI PRAREGISTRASI.

### D-110 — QA Tahap 0 & event study: konvensi teknis · FINAL (teknis) · 2026-11-20 (WP-10, WP-14) · Danen
(1) Pemetaan Panel Harga Bapanas → PIHPS (U20) di `qa.BAPANAS_TO_PIHPS`: 9 pasangan yang setara. Beras Premium, Kedelai, dan Cabai
Merah Besar dikecualikan karena di luar 10 komoditas. Minyakita juga dikecualikan karena minyak goreng program pemerintah, bukan
Kemasan Bermerk 1. Pemetaan disimpan di kode QA, bukan di `commodities.yaml`, agar config beku G6 tidak berubah (hanya dipakai QA).
(2) Ambang lonjakan satu hari |Δlog| > 0,5 berbalik (U17) disimpan sebagai konstanta modul QA, bukan di `params.yaml`, dengan alasan
yang sama. Ambang ini hanya menandai dan tidak memengaruhi estimasi. (3) Event study nasional = rerata lintas provinsi dari selisih per
provinsi (provinsi yang teramati di kedua minggu), agar tahan perubahan komposisi seperti D-106; level wilayah memakai
`panel_weekly_region`. (4) Plasebo event study: satu set 499 awal (seed + 1401, dengan pengembalian) dipakai bersama semua komoditas
dan unit. Kandidat = minggu di luar [start−12, end+12] setiap episode, dengan s−1 dan s+12 di dalam panel. Pada data asli hanya
164 minggu unik, jadi resolusi p terbatas dan dinyatakan sebagai batasan. (5) PT di `national_profiles`: se & ci NaN sampai bootstrap
(METHODS §M1.2, tanpa delta method). Bukan deviasi praregistrasi: tidak mengubah hipotesis, uji, atau parameter beku.

### D-111 — Robustness Tier 1, heterogenitas, Kendall: konvensi teknis · FINAL (teknis) · 2026-11-21 (WP-28, WP-18, WP-22) · Danen
(1) Tier 1 memakai sub-sampel berbasis jendela: observasi minggu t dipakai hanya bila seluruh jendela datanya
[t−(L+1) minggu, t+h minggu] (p_{t−1}, lag Δp & lag penggerak s.d. p_{t+h}) berada di dalam sub-periode (pra/pasca 2021-04-05) atau
tidak beririsan dengan periode yang dibuang (COVID dan bulan Brent ekstrem). Ditolak: memotong hanya menurut t (y dan lag masih
membawa minggu yang dibuang). Desain sampel penuh di-demean ulang per seri pada sub-sampel (setara within-transform pada sub-sampel).
(2) Bulan Brent ekstrem = |Δ log rerata bulanan Brent| > `brent_extreme_abs_monthly_logchg`. Pada data asli: Mar–Jun 2020, Mar 2026
(+0,40) dan Nov 2026 (−0,27, bulan parsial s.d. 11 Nov). Aturan beku diterapkan apa adanya; Nov 2026 hampir tidak berdampak karena
jendela t+h di sana sudah melewati freeze. (3) Frekuensi bulanan (tidak dirinci di proposal): rerata log mingguan per bulan kalender,
h_bulan = round(h·12/52) → 1/2/3, L_bulan = max(1, round(L·12/52)) = 1, kontrol Idulfitri = rerata bulanan dummy mingguan, SE cluster
bulan. (4) Dekomposisi de = a + b·d_dxy + ε: kedua komponen masuk satu LP (driver e_global, e_idr); data asli b = 0,72, R² 0,27.
(5) Interval Tier 1 = ±1,96·SE cluster; bootstrap tidak diulang per cek (biaya); dinyatakan di makalah. (6) Heterogenitas (WP-18):
driver e, deviasi tanpa susut; baris provinsi `profiles` dan `placebo_stats` wajib membawa `se` (kolom ekstra; permintaan ke WP-16);
p plasebo satu sisi atas; BH per statistik; `reject` hanya untuk Q (statistik H0-Het yang dibekukan). ρ̄ melewati pasangan komoditas
dengan < 3 provinsi bersama. (7) Kendall (WP-22): τ-b (rasio impor punya ties nol); `p_value` = p eksak dua sisi atas semua n!
urutan, `p_greater` = satu sisi arah E1; interval = τ ± 1,96·SE jackknife LOCO (dipotong ke [−1, 1]). Bukan deviasi praregistrasi.

### D-112 — Uji struktur tertanam: definisi δ dan input mentah · FINAL (teknis) · 2026-11-21 (WP-21) · Danen
Proposal: "kelompok provinsi buatan dengan selisih respons 0,1–0,5 ditambahkan ke noise plasebo". (1) δ dibaca dalam satuan respons
(Δlog harga per log penggerak), jadi struktur ditanam pada matriks fitur plasebo **sebelum** z-score; `recovery_curve` menerima
matriks plasebo mentah dan menstandardisasi sendiri (z-score per kolom, sama dengan `feature_matrix`). (2) Pusat k_true kelompok =
simpleks beraturan berorientasi acak: setiap pasangan kelompok berjarak δ·√F (selisih RMS per fitur = δ). Ditolak: geser kelompok j
sebesar j·δ di semua fitur. Pada tes sintetis (derau sd 0,3, 12 fitur, δ = 0,5) cara itu memberi ARI 0,96 di k = 3 tetapi k = 3 tidak
pernah terpilih karena tiga kelompok segaris (silhouette lebih suka k = 2), sehingga batas deteksi k = 3 menjadi artefak geometri.
(3) Ambang = persentil `silhouette_placebo_pct` dari silhouette maksimum (Ward, Euclidean, k ∈ k_range ≥ 2) semua matriks plasebo,
dihitung sekali; aturan pemilihan k sama dengan `select_k` (WP-19). (4) ARI ≥ 0,8 dan k_true ∈ {2, 3} = konstanta modul (METHODS
§M2.5, WORKPLAN), bukan parameter baru. RNG seed + 2101. Bukan deviasi praregistrasi (δ, reps, persentil tidak berubah).

### D-113 — Evaluasi Task 4: DM, sel H5, keluarga Holm · FINAL (teknis) · 2026-11-21 (WP-27) · Danen
(1) DM dihitung pada deret MAE per origin (rerata galat absolut lintas seri dalam sel), bukan pada galat per baris: galat antar seri
dalam satu origin berkorelasi kuat sehingga perlakuan per baris membuat SE terlalu kecil. Horizon dalam satuan origin = ceil(h/4) → HAC
lag 0 (h = 4) dan 1 (h = 8), sesuai METHODS ("lag h−1 dalam satuan origin yang tumpang tindih"), + HLN. (2) Sel evaluasi: ALL,
per komoditas, per wilayah, dan per jalur H5. Jalur = komoditas `role: focus` dengan exposure_path direct_import {bawang putih, gula,
daging sapi} atau imported_input {daging ayam, telur}; beras (direct_import, role other) tidak masuk. (3) H5: p DM satu sisi (H1: M2
lebih akurat dari M1), Holm atas keluarga tetap 2 jalur. Bila p satu jalur tak terdefinisi (mis. prediksi identik), p dihitung 1
agar keluarga tidak menyusut (menyusut = koreksi lebih longgar; ditemukan oleh tes). (4) α keluarga 0,05 diambil dari PREREGISTRATION
sebagai konstanta modul (`H5_ALPHA`) karena tidak ada kuncinya di `params.yaml` beku (`power.mde_alpha` untuk MDE). (5) Model ablation di
`forecast_preds` bernama `M2_nofx` (kontrak dengan WP-26). Bukan deviasi praregistrasi.

### D-114 — Validasi V2 & V4: konvensi teknis · FINAL (teknis) · 2026-11-21 (WP-29, WP-14, WP-27) · Danen
(1) V4 membandingkan, per komoditas × h ∈ key_horizons, kelebihan respons episode (dlog_price nasional − median plasebo) dengan
respons yang diimplikasikan LP nasional: Σ_{j=0..h} β_e(h−j)·de_{s+j} + Σ_j ω(h−j)·dw_{s+j} (superposisi impuls mingguan dari LP linear,
memakai penggerak yang benar-benar terjadi di jendela episode). Ditolak: membandingkan langsung dengan β(h)·cum_dlog_e episode (episode
punya panjang dan pola de berbeda, dan cum_dlog_e dihitung pada jendela pemicu, bukan jendela event). (2) Pusat null = median plasebo
(kolom baru `events.placebo_median`, aditif). Ditolak: titik tengah pita 2,5–97,5: pada data asli memberi kelebihan minyak goreng −0,09
dan bawang putih −0,17 dengan interval sempit karena ekor null miring (lonjakan 2021–22), artefak bukan sinyal. (3) Interval V4 =
rerata ± 1,96·sd/√n antar episode; ringkasan kesesuaian: porsi tanda sama dan korelasi antar episode. (4) V2 = episode yang mulai di
tahun kalender freeze dengan outcome lengkap (interval = pita plasebo relatif median) dan subset origin `case_study` (tahun freeze) di
`forecast_eval` (rasio MAE vs M1, deskriptif; ci NaN, DM p dan n_origins di note). Task 4 hanya punya h 4/8 (params beku), jadi h = 12
V2 hanya dari sisi episode. (5) Baris validasi memakai tier = 'V'. Bukan deviasi praregistrasi.

### D-115 — Gerbang G-power resmi + status H2 · FINAL · 2026-11-21 (WP-09, G-power) · Danen
(1) G-power (D-007) diputuskan dari `mde` yang dihitung ulang dengan config beku G6 (sha256 konten LF sama dengan PREREGISTRATION §5;
hash di disk berbeda hanya karena `core.autocrlf`): MDE_PT(8) nasional bawang putih 2,52, gula pasir 0,90, minyak goreng 0,465. Syarat
"ketiganya > 0,5" tidak terpenuhi → **LP mingguan tetap analisis utama**; event study & profil harga dunia pendamping; Task 4 tetap
menjawab H5. (2) PREREGISTRATION menetapkan H2 konfirmatori hanya bila "MDE asimetri ≤ 0,5 (ditentukan di G-power)", tetapi MDE
asimetri belum dihitung di WP-09. Ditambahkan `power.asymmetry_null_se` dan kolom `mde_asym_beta/mde_asym_pt` (nasional) di `mde`:
SE selisih δ = β⁻ − β⁺ pada h dalam bentuk skor di bawah H0 asimetri, sehingga estimasi β̂⁺/β̂⁻ tidak dipakai. (3) **Keputusan Danen:**
ambang 0,5 dibaca dalam **satuan PT** (MDE_asym/γ(8)), sama dengan satuan ambang G-power yang dibekukan (`mde_threshold_pt8`).
Alternatif ditolak: satuan β (lebih konservatif); perbedaan hanya pada beras (0,59 dalam β, 0,44 dalam PT). Hasil (PT(8)): daging
sapi 0,32 dan beras 0,44 → **H2 konfirmatori**; minyak goreng 1,01, telur 1,51, gula 1,70, daging ayam 2,66, bawang merah 4,66,
bawang putih 6,15, cabai merah 7,46, cabai rawit 9,34 → H2 deskriptif. Ini pelaksanaan aturan praregistrasi (bukan deviasi);
penafsiran satuan dicatat terbuka di makalah. U8 🟢.

### D-116 — Implementasi robustness Tier 2 · FINAL (teknis) · 2026-11-21 (WP-30) · Danen
PREREGISTRATION/METHODS hanya menyebut empat cek Tier 2 tanpa rincian; implementasi: (1) **varian alternatif** = SEMUA varian level-2
PIHPS lain dalam grup komoditas yang sama (11: beras 5, minyak goreng 2 termasuk Curah, gula, daging sapi, cabai merah, cabai rawit 1),
masing-masing dengan agregasi mingguan & kelayakan sendiri; ditambah komposit harga dunia pakan bobot sama 0,5/0,5 dan seri tunggal
(D-012). Alternatif ditolak: memilih satu varian per komoditas (pilihan tambahan yang tidak dibekukan). (2) **Observasi terakhir** =
harga hari teramati terakhir per minggu ISO, kelayakan panel utama. (3) **Eksposur alternatif** = pengodean ordinal jalur
(langsung 2, input impor & paritas ekspor 1, domestik 0; `PATH_ORDINAL`) dalam Kendall τ-b eksak seperti E1; keterpencilan alternatif
butuh meta-regresi (WP-23) dan ditambahkan setelah fungsi itu ada. (4) **Outcome Bapanas** = LP bulanan (konstruksi Tier 1 bulanan)
pada Panel Harga Bapanas 2022–2026; baseline = LP bulanan PIHPS pada bulan yang sama (bukan periode penuh), agar beda hanya dari sumber.
Tier 2 deskriptif, interval ±1,96·SE cluster, tidak masuk koreksi multiplisitas. Bukan DEVIASI PRAREGISTRASI (cek opsional yang
disebut tanpa spesifikasi). Input dibangun dari data mentah (`pipelines.robustness.tier2_inputs`) → hanya bisa dijalankan dengan raw_dir.
Hasil data asli: baseline di dalam interval 184/186 sel; pengecualian gula Premium β_e(4) dan Minyak Goreng Curah ω(8) (tanda sama).

### D-117 — Pesan commit tanpa Co-Authored-By · FINAL (permintaan user) · 2026-11-21 · Danen
Pesan commit dan deskripsi PR tidak boleh memuat trailer `Co-Authored-By` atau atribusi agent/AI lain; pesan commit cukup satu
baris `<tipe>: <deskripsi>` (D-108). Berlaku untuk command git yang disiapkan agent, walaupun instruksi sistem/harness meminta
atribusi. Pemicu: commit lokal `feat/robustness-tier2` sempat dibuat dengan trailer co-author dari command yang disiapkan agent;
diperbaiki dengan `git commit --amend` sebelum push.

### D-118 — LP cepat tanpa mengubah hasil · FINAL (teknis) · 2026-11-21 (WP-13, untuk WP-16) · Danen
Profil runtime `national_profiles` (28,7 dtk lokal): 22 dtk di `build_design`, yang membangun ulang pivot harga, blok kurs, kontrol,
dan DataFrame untuk setiap komoditas × horizon × spesifikasi (260 kali), padahal regresor tidak bergantung pada horizon. Kini
`_design_parts` (pivot, Δp, blok kurs, kontrol) dibangun sekali per komoditas × spesifikasi; `_design_arrays` menyusun y^{(h)},
membuang baris NaN dalam periode, dan within-transform per unit dengan numpy (matriks regresor di-cache); `build_design` memakai
jalur yang sama (API & kolom tidak berubah). `stats.ols_cluster`: skor cluster dengan `np.bincount` menggantikan `np.add.at`.
Hasil identik pada data asli: `national_profiles` selisih estimasi 0 dan SE 0 (598 baris); Tier 1 selisih ≤ 2·10⁻¹²; `mde` ≤ 2·10⁻¹⁵.
Runtime `national_profiles` 28,7 → **5,9 dtk**; Tier 1 21 → 17,5 dtk. Dampak: bootstrap/plasebo WP-16 (Ardell) yang memanggil
`national_profiles` per replikasi ± 50 menit untuk B = 499 (sebelumnya ± 3,2 jam). Tes `test_national_profiles_fast_path_equals_design_loop`,
`test_build_design_y_matches_manual`.

### D-119 — `ols_cluster` membuang baris dengan grup kosong · FINAL (teknis) · 2026-11-21 (WP-12) · Danen
Sejak D-118 skor cluster dihitung dengan `np.bincount` pada kode `pd.factorize`; kode −1 (grup NaN/NaT/None) membuat bincount
melempar `ValueError` ("must have no negative elements"). Sebelum D-118, `np.add.at` dengan indeks −1 diam-diam menambahkan
baris itu ke cluster terakhir (SE sedikit salah). Kini baris dengan grup kosong dibuang bersama baris NaN di y/X, lalu kode
cluster difaktorkan ulang. Hasil LP nasional, Tier 1, dan `mde` tidak berubah (desain nasional tidak punya minggu kosong).
Dilaporkan Ardell sebagai masalah `ols_cluster` (di macOS); penyebab persisnya di mesin Ardell belum dikonfirmasi.
Tes `test_ols_cluster_drops_missing_groups`.

### D-120 — Item FAOSTAT beras = beras giling · FINAL · DEVIASI PRAREGISTRASI · 2026-11-21 (WP-07, WP-22) · Danen
`configs/commodities.yaml` (beku G6) memetakan beras ke item FAOSTAT SUA "Rice", yang di SUA adalah **padi/gabah**: produksi
54–59 juta t, impor 6–229 t per tahun → `import_ratio_direct` beras 1,3·10⁻⁶ (hasil `stage0` pertama, 2026-11-21). Impor beras
Indonesia tercatat di "Rice, milled" (1,85 juta t 2018; 2,72 juta t 2023) dan "Rice, broken" (± 0,35 juta t/th). Diganti menjadi
["Rice, milled", "Rice, broken"] → rasio 2018–2023 = **0,033** (cek silang neraca BPS 0,059). Alternatif ditolak: neraca BPS
(sumber & metode berbeda dari 9 komoditas lain); membiarkan "Rice" (salah pemetaan, bukan pilihan analisis). Keputusan diambil
sebelum E1 dihitung. Dampak: urutan beras pada E1 naik dari ke-7 menjadi ke-5; τ-b E1 sementara −0,045 (p 0,93) vs −0,13 dengan item
lama — kesimpulan sama (tidak terdeteksi). sha256 `commodities.yaml` (LF) sesudahnya `f88184eb…011813` (dicatat di kepala PREREGISTRATION).
Tes `tests/test_config.py::test_faostat_items_exist_and_rice_is_milled`; `tests/test_reference.py` memakai item yang sama.

### D-121 — Dua kunci `params.yaml` baru dari WP-07/WP-26 · FINAL · DEVIASI PRAREGISTRASI · 2026-11-21 (WP-07, WP-22, WP-26) · Danen
Dicatat Danen atas nama Ardell (bagian `association` & `forecast` milik Ardell, PEMBAGIAN_TUGAS §3). Kedua kunci ditambahkan Ardell
pada commit 2026-11-21 16:19, setelah pembekuan G6 (2026-11-20 23:29), tanpa entri deviasi.
1. `association.import_ratio_years: [2018, 2023]` — jendela rerata tahunan `exposure.import_ratio_direct` (impor / (produksi + impor
   − ekspor), FAOSTAT SUA) yang dipakai E1 (WP-22). Praregistrasi menyebut "rasio impor langsung" tanpa jendela tahun. Pilihan:
   awal = awal periode outcome (`period.start` 2018-01-01); akhir = tahun FAOSTAT SUA terakhir (2023). Item yang tidak terisi di
   tahun tertentu memakai tahun yang ada (telur 2018–2022 tiga tahun bernilai, cabai 2018–2022; tercatat di kolom `source`).
   Alternatif ditolak: satu tahun terakhir (lebih bising, impor beras naik tajam 2023); seluruh 2010–2023 (di luar periode
   outcome). Jendela ditetapkan di kode sebelum E1 dihitung pada data asli (E1 pertama kali dihitung 2026-11-21 malam, D-120).
2. `forecast.run_m3: true` — sakelar operasional untuk urutan pemotongan D-014 (M3 dipotong terakhir). Nilai `true` = analisis
   praregistrasi tidak berubah; mengubah ke `false` = pemotongan lingkup yang wajib dicatat sebagai keputusan baru.
Dampak: tidak ada perubahan hipotesis atau uji; hash `params.yaml` berubah (dicatat di kepala PREREGISTRATION).

### D-122 — Notebook menarik input opsional (`panel_weekly`) dari Drive tim · FINAL (teknis) · 2026-11-21 (WP-13, WP-16, WP-23, WP-26) · Danen
`task1`, `task3`, `task4` memakai panel provinsi `panel_weekly` hanya bila sudah ada (`exists`), tetapi notebook hanya menarik
`REQUIRES` dari Drive tim. Di Colab/Kaggle (out_dir kosong) tahap itu diam-diam jatuh ke versi 7 wilayah: Task 1 tanpa profil
nasional, deviasi provinsi, bootstrap, dan plasebo (lalu Task 2 gagal karena `placebo_stats` tidak ada); Task 3 tanpa meta-regresi
& FE; Task 4 per wilayah. Kini setiap pipeline itu punya `OPTIONAL` (task1/task4: `panel_weekly`; task3: `panel_weekly`, `profiles`,
`boot_replicates`, `eligibility`, `drivers_weekly`) yang ditarik notebook, dan pipeline mencetak PERINGATAN bila panel provinsi
tidak ada. Tes `test_notebooks.py` memastikan notebook menarik `OPTIONAL`. CLI `drive-pull <tahap>` juga menarik
`REQUIRES` + `OPTIONAL` (`cli.PIPELINE_REQUIRES`).

### D-123 — Data manual WP-07: penduduk, n_kota, faktor GKG→beras · FINAL · 2026-11-21 (WP-07, WP-23) · Danen
Diisi Danen (atas permintaan Danen; semula tugas Abi/U103) agar ketiga fitur Z(r) praregistrasi H3 tersedia sebelum Task 3.
1. **Penduduk 2025** (`data/raw/bps_kependudukan/penduduk_provinsi_2025.csv`): salinan kolom jumlah penduduk dari tabel BPS "Penduduk, Laju
   Pertumbuhan Penduduk, … Menurut Provinsi, 2025" (diperbarui 2 Mei 2025; 38 provinsi, ribu jiwa, total 284.438,8 ribu). Angka ini
   berbasis proyeksi sebelum hasil SUPAS 2025 terbit; dipakai karena tahun 2025 cocok dengan produksi padi & konsumsi 2025. Ditolak:
   proyeksi 2010–2035 (basis SP2010, selisih besar), tabel SUPAS 2025 (belum ada per provinsi dalam bentuk yang sama saat diakses).
2. **n_kota** (`data/raw/manual_pihps/n_kota.csv`): jumlah kabupaten/kota pasar tradisional per provinsi dari referensi situs PIHPS
   (`GetRefRegency`, price_type_id = 1, diakses 2026-11-21): 110 kota, 1–12 per provinsi. Kondisi 2026, bukan riwayat 2018–2026.
3. **Faktor GKG→beras** (`data/raw/manual_conversion/gkg_beras.csv`): 0,5762 untuk 2024 dan 2025 = produksi beras untuk konsumsi pangan
   penduduk / produksi padi GKG dari rilis BPS 2 Feb 2026 (34,69/60,21; 30,62/53,14). Dipilih faktor "beras untuk pangan" (bukan
   rendemen 0,6402 saja) karena penyebut `rice_sufficiency` = konsumsi beras rumah tangga; rantai BPS 0,9318 × 0,6402 × 0,9667 = 0,5767
   (selisih karena pembulatan rilis).
Hasil `province_features` 2025: rice_sufficiency 0,001 (DKI) .. 3,27 (Sulsel); korelasi antar fitur |r| ≤ 0,34. Bukan DEVIASI
PRAREGISTRASI (data input untuk fitur yang sudah dipraregistrasi; tidak ada parameter `params.yaml`/`commodities.yaml` yang berubah).

### D-124 — E2 diimplementasikan sebagai LP per rezim HET/HAP · FINAL (teknis) · 2026-11-21 (WP-22, E2) · Danen
PREREGISTRATION mencatat E2 sebagai "Profil respons per rezim HET/HAP" (eksploratif) tanpa rincian; hingga 2026-11-21 tidak ada kode yang
membaca artefak `regulation`. Implementasi (`src/evaluation/regimes.py`, ditulis `task3` sebagai artefak baru `regime_profiles`, 33 artefak):
(1) batas rezim = tanggal penetapan/perubahan harga acuan **konsumen** (HET, HAP, HAP konsumen; HAP produsen tidak) di `regulation` yang
in_scope, bertanggal, `verification` ≠ `unverified` (setting panel Bapanas & relaksasi tanpa dasar tertulis tidak dipakai), dalam periode;
(2) rezim 0 = awal periode sampai sebelum perubahan pertama di tabel (bukan berarti tanpa harga acuan: tabel regulasi mulai 2020);
(3) per rezim, LP nasional spesifikasi utama pada h kunci, hanya observasi yang jendela datanya [t−(L+1), t+h] utuh di dalam rezim (aturan
sub-sampel Tier 1, D-111), driver e & w; rezim dengan minggu ≤ jumlah regresor dilewati (SE tidak teridentifikasi); interval ±1,96·SE cluster
minggu, pembanding = estimasi sampel penuh. Ditolak: jendela ±W minggu di sekitar perubahan (butuh parameter W baru setelah G6) dan interaksi
Δe × dummy rezim dalam satu regresi (memaksa kontrol sama antar rezim). Tidak ada uji formal atau koreksi multiplisitas; bukan DEVIASI
PRAREGISTRASI (E2 eksploratif, tanpa parameter baru). Data asli 2026-11-21: 145 baris, 73% sel estimasi penuh di dalam interval rezim.
Batasan tafsir: batas rezim berimpit dengan peristiwa lain (2022: lonjakan harga pangan & pakan dunia), dan HET minyak goreng mengatur
Minyakita/curah, bukan varian Kemasan Bermerk 1 yang dianalisis.

### D-125 — Uji H2 diformalkan + hasil gerbang G-het · FINAL (teknis) · 2026-11-22 (WP-13, WP-18) · Danen
(1) H2. Hingga 2026-11-22 tidak ada kode yang menjalankan uji Wald H2 (hanya MDE-nya, D-115). Kini `local_projection.asymmetry_wald`
memakai spesifikasi asimetris yang sama dengan `national_profiles` dan parametrisasi ulang β⁺·de⁺ + β⁻·de⁻ = β⁻·de + (β⁺ − β⁻)·de⁺
(lag de⁺/de⁻ bebas): koefisien de⁺ = β⁺ − β⁻ (tanda sama dengan A8), SE cluster minggu CR1-nya = SE Wald satu restriksi; z normal dua
sisi, α = `power.mde_alpha` (0,05, sama dengan PREREGISTRATION). `evaluation/asymmetry.asymmetry_tests` menambahkan status konfirmatori
(h = 8 dan lolos gerbang G-power H2), `reject`, MDE asimetri, persentil bootstrap dan p plasebo dua sisi dari selisih per replikasi
(pembanding, bukan pengganti). Ditulis `task3` sebagai artefak baru `asymmetry` (34 artefak) karena hanya butuh panel + replikasi Task 1
yang sudah terbit; menjalankan ulang `task1` (± 2 jam) tidak perlu. Ditolak: Wald dari kovarians bootstrap (praregistrasi menyebut SE
cluster minggu). Bukan DEVIASI PRAREGISTRASI.
Hasil (data asli, h = 8): beras −0,14 (−0,55..0,26) p 0,49; daging sapi −0,26 (−0,56..0,04) p 0,089 → H2 konfirmatori tidak ditolak.
(2) G-het (gerbang 25 Nov, diputuskan 22 Nov dari `task2` lokal pada Task 1 asli Ardell): H0-Het ditolak untuk telur ayam (q 0,040) dan
daging ayam (q 0,050, tepat di ambang fdr_q → rapuh, tulis apa adanya); 8 komoditas lain tidak terdeteksi. Clustering tetap jalan (D-004):
k = 1. Batas deteksi struktur tertanam belum boleh dikutip (U105).

### D-167 — Aturan & evaluator validasi maju K4 dibekukan sebelum target pertama: ΔAP(K4-E80 − C1-tuned) < −0,14 = FAILED_FORWARD · FINAL · eksploratif · 2026-11-27 (WP-36) · Danen
Disetujui Danen 2026-11-27, sebelum snapshot apa pun yang memuat target maju (Jumat 2026-11-27) diunduh. PROTOCOL K4 §6 hanya menyatakan
"konfirmasi hanya dari prediksi maju" tanpa ambang. `docs/audit/20261127_prospective_validation/FORWARD_VALIDATION_PROTOCOL.md` §5 menetapkannya.
- **Label:** dari panel snapshot baru dengan `thr_e80` beku. Kolom z_* tidak dipakai (D-166). Target tak teramati → z = 0 (D-155).
- **Penanda per horizon:**
  - FAILED_FORWARD bila ΔAP pooled < −0,14. Ambang ini = MDE maju dari SE ΔAP test (0,0169 / 0,0235) · 2,8 · √(n_test/n_maju).
  - CONSISTENT bila ΔAP ≥ 0 dan AP ≥ B-CLIMS.
  - NOT_PROVEN di antaranya.
- **Interval:** bootstrap kluster provinsi, deskriptif.
- **Ditolak:**
  - Uji konfirmasi, karena daya tidak cukup: 4 / 8 origin mingguan yang tumpang tindih.
  - Ambang lebih ketat, karena bertentangan dengan MDE.
- **Evaluator:** `scripts/k4_forward_eval.py`.
  - Berhenti bila hash prediksi, `fw_eval.py`, `k4_eval.py`, atau `k4_common.py` berubah. Hash boleh cocok sesudah hanya ujung baris
    dinormalkan.
  - Uji: `--check-test` mereproduksi z_e80/z_a80 pipeline K4 24.616/24.616, dan AP/AUC/presisi@K = `k4_test_ranking.csv`.
  - Pada snapshot 2026-11-18: 0 origin lengkap, jadi ditunda.
- **Hash:** `hasil/pv_protocol_sha256.txt`. Belum di-commit pada saat ditulis. Operasional K4 tetap BLOCKED (U109).

### D-166 — Validasi K4: target benar, kalibrator walk-forward ditolak, ranking bergantung pada ambang relatif, peluang h 4 hanya kategori; operasional tetap BLOCKED · FINAL · eksploratif · 2026-11-27 (WP-36) · Danen
Atas permintaan Danen (validasi & kesiapan operasional K4; laporan `docs/audit/20261127_k4_validation/SUMMARY.md`; baca-saja terhadap D-164: tidak ada
model dilatih ulang, test 2024+ tidak dibuka untuk analisis baru; protokol `PROTOCOL_ADDENDUM.md` di-hash sebelum analisis kalibrasi). (1) Target: target
tak teramati memang diberi z = 0, tetapi hanya di evaluasi (latih wajib target terealisasi) dan hanya 2 + 2 baris dev, 0 test; dikeluarkan → ΔAP ≤ 0,0004;
y_h & z identik dengan hitung ulang dari `panel_weekly`; negatif y = 0 = dua ujung carry-forward (98%). Kolom z di prediksi maju beku bernilai 0 dan bukan
label. (2) Kalibrasi (dev): 0/6 kalibrator walk-forward (Platt, isotonik, per komoditas, intersep, 13 origin terakhir, campuran laju-dasar) menurunkan
Brier; ekor h 8 p 0,8–0,9 = 57 baris dari 5 origin (41 dari 2: minyak goreng 2022-01, beras 2023-10); oracle laju per origin ex-post −0,0073 → yang hilang
adalah informasi rezim, bukan bentuk kalibrasi. Rekomendasi D-164 #5a (kalibrator ekor per kelompok) dicabut. (3) Galat (dev, K = 2): 25% alarm palsu h 4
naik material ≤ 4 minggu sesudah titik akhir (seri tanpa alarm 12%); separuh kenaikan terlewat di peringkat K+1..K+2; bawang putih/merah 14–17% alarm
dengan presisi 0,01–0,15. (4) Kepekaan: satu model P80 mengurutkan P70–P90/bertanda/kejadian sama baiknya dengan model khusus, tetapi pada ambang seragam
5% / 10% skor K4-E80 kalah dari C1-tuned (ΔAP h 8 −0,079 / −0,092, interval < 0) → ambang kebijakan TPID dapat membatalkan K4-E80. (5) Instrumen
U109 R1–R12 + matriks status; spesifikasi operasional lima lapis (peluang h 4 hanya kategori relatif terhadap laju komoditas, h 8 tanpa angka). Hasil D-164,
`src/`, C1-tuned, macro F1, H5 tidak berubah. Kriteria adopsi/penolakan di `FINAL_RECOMMENDATIONS.md`.

### D-165 — Jalur A macro F1 & intelijen eksternal: prediksi maju diaudit & evaluator dibekukan, GDELT lolos G1–G2 tetapi G5 terblokir BigQuery, sumber pasokan baru terblokir akses; C1-tuned tetap · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Atas permintaan Danen (empat workstream; laporan `docs/audit/jalur_a_macro_f1/`; nomor dikoordinasikan dengan sesi paralel D-162–D-164).
(A) Prediksi maju D-152 (C1t, IW_NAT) & D-158 (C1t, FR_REF, FR_CITY): sha256 = manifest, base identik, 338 seri, 0 NaN; kode yang berubah sejak beku
hanya `forecast.py` (D-162, kolom `episode` grup fx, tidak dipakai keluarga ini). 0 target terealisasi (pertama 2026-11-27; semua h 4 2026-12-18, h 8
2027-01-15). Evaluator gabungan (`a_forward_eval.py`; macro F1, F1 per kelas, AUC, Brier, ECE, Δ vs base + bootstrap provinsi; penanda GAGAL_MAJU
bila Δ < −MDE D-152) dibekukan sebelum target ada. Kedua pembekuan ada di git sebelum target pertama (D-152 `ca53742`, D-158 `ec6dd19`
2026-11-26 20.45 WIB). (B) GDELT: DOC API HTTP 429 menetap (4 percobaan s.d. 3,5 jam);
berkas GKG Translingual dapat diakses: pilot 48 batch acak 2019–2023 (409 MB, di luar repo) → ± 130 artikel berbahasa Indonesia per batch, judul
≥ 99% sejak 2020 (2019: 29%), lag `DATE` vs terbit ≤ 1 hari. Validasi manual 111 kandidat (judul/URL): presisi relevan 0,23 (pola naif; 18% salah
cocok substring) → 0,72 (batas kata + kata kunci pasokan/kebijakan + dedup); G3 & G4 sebagian (berita harga reaktif; cakupan tipis selain beras &
minyak goreng). G5 butuh hitungan lengkap: BigQuery sandbox tanpa billing, estimasi ± 0,3 TB < kuota 1 TiB → **BLOCKED `[HUMAN]`**; kueri, layar, dan
tes dibekukan. Kalibrasi layar G5: kontrol positif kesegaran `iw_gap_nat` ΔAUC +0,015 (−0,002..+0,030) h 4, −0,004 h 8 → tidak lolos; kontrol
negatif ≈ 0; MDE ± 0,023 AUC. Ambang tidak diubah; dicatat di `docs/EKSPERIMEN.md` §3. (C) 10 kandidat pasokan & kejadian: tidak ada yang lolos
G1–G4 untuk dev. Proyeksi Neraca Pangan Bapanas (dataset *Terbatas*, vintage bulanan sejak Sept 2024) dan luas tanam/EWS hortikultura Kementan
(tanpa seri publik) BLOCKED akses → digabung ke permintaan U112; HET/HAP (11 peristiwa dev), BBM (1), DIBI (mekanisme cuaca tertutup D-161),
Google Trends, Bulog/SPHP, pelabuhan ditolak. (D) Tanpa modeling; test 2024+ tidak dibuka. Log `EXPERIMENT_LOG.csv` (24 baris) + registri hidup.
Ditolak: DOC API berulang (blokir menetap), unduh arsip GKG lengkap (± 1,5 TB), LLM/embedding sebelum G5 terbukti.
**Adendum 2026-11-26 23.03 WIB (persetujuan Danen "Ya, buat sandbox"):** proyek Google Cloud `kagami-gdelt` tanpa akun billing; cek partisi
2022-03-15 → 7.791 rekaman Translingual `srclc:ind`; kueri beku (teks di editor = berkas, sha256 diverifikasi; hash protokol di komentar job)
313,83 GB, biaya 0, 15.722 baris harian 2018-12-22..2023-12-31 (`hasil/gdelt_daily_counts.csv` + manifest). Layar G5 satu kali (skrip & protokol =
versi beku): ΔAUC arah nasional di atas konsensus C1t −0,005..+0,001 (h 4) dan −0,008..−0,000 (h 8) untuk set V/D/P/S/ALL, q ≥ 0,46 → **GDELT
REJECTED**, tanpa modeling provinsi; U113 ditutup. Titik estimasi ≤ 0 dan jauh di bawah kontrol positif → kegagalan bukan karena daya layar.

### D-164 — K4 risiko kenaikan harga material: klasifier pada target z mengungguli skor arah untuk ranking (h 4 terbukti), peluang h 8 tidak; PARTIAL, operasional BLOCKED · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Atas permintaan Danen (kartu K4 adendum D-155; laporan `docs/audit/20261126_k4_risiko_material/RESULTS.md`; jalur terpisah dari macro F1, nomor
dikoordinasikan dengan sesi D-162/D-163/D-165). Target materialitas statistik (proxy; materialitas kebijakan belum ada, U109): z = 1[y_h ≥ P80 |y_h|
baris latih komoditas, walk-forward], semua baris (y = 0 dan target hilang = 0). DU dev: laju z 0,120 / 0,132, per komoditas 0,02–0,29, 60% / 64% positif
pada 4 komoditas diatur (ambang 1,2–3,9%), laju per minggu sd 0,07–0,08 (musim Jun–Agu 0,05–0,09 vs Nov–Apr 0,15–0,19), antarprovinsi sd 0,015.
Protokol dibekukan sebelum model (sha256 `7625c391…`): K4-E80 = HGB `TUNED_HGB` pada kolom C1-tuned dengan label z; pembanding C1-tuned (refit =
artefak, maks |Δp| 0), C1-tuned + Platt walk-forward, laju-dasar komoditas (± bulan), 4 aturan naif D-154. Kebocoran: perturbasi sesudah origin 0 beda
(6 origin × h). Dev: ΔAP vs C1-tuned +0,080 (0,046..0,103, q 0,002) / +0,039 (−0,008..0,101); Δpresisi daftar pantau 2/provinsi +0,044 (0,019..0,067) /
+0,050 (−0,005..0,112); di atas laju-dasar komoditas (naif terbaik) → R1, R1b lolos. Brier h 4 −0,0063 (interval < 0), ECE 0,023; h 8 ΔBrier & Brier skill
memuat 0 dan ekor atas terlalu yakin (p 0,8–0,9 → 28%) → R2 gagal → **PARTIAL**. Test 2024+ dibuka sekali (bukan independen): ΔAP +0,045 (0,017..0,083) /
+0,015 (−0,028..0,064), presisi 0,202 vs 0,179 / 0,174 vs 0,161, Brier h 4 −0,0024 (interval < 0). Kepekaan: keunggulan h 4 bertahan pada target berkomposisi
seimbang (P90 y bertanda); target kejadian kapan pun (laju 0,137 / 0,168; 12% / 21% lonjakan berbalik) diurutkan K4-E80 hampir sama baiknya dengan model
khususnya di dev. Biaya skenario: daftar pantau apa pun kalah dari "tanpa alarm" bila biaya kenaikan terlewat ≤ 2× alarm palsu. **Koreksi D-154**: daftar
pantau C1-tuned tidak pernah dibandingkan dengan laju-dasar komoditas; di h 8 keunggulannya atas pembanding itu tidak terbukti (dev −0,026, test +0,019,
interval memuat 0) → aturan baru `docs/EKSPERIMEN.md` §5. Prediksi maju beku 4.056 baris (12 origin 2026-09-28..11-16, sha256 `eb1f10db…`). C1-tuned, label
arah, macro F1, H5, dan `src/` tidak berubah; K4 tidak dipromosikan sebelum U109 & validasi prospektif. Ditolak: tuning ulang untuk z, fitur baru,
ensemble (protokol), memilih K/τ/ambang dari test.

### D-163 — Kelemahan tercatat: interval PT & provinsi terkalibrasi plasebo (U107), kalibrasi skor daftar pantau ditolak, fitur clustering konstan inert · FINAL · tambahan pasca-G6 / eksploratif · 2026-11-26 (WP-36) · Danen
Atas permintaan Danen menutup kelemahan yang tercatat. (1) U107: `evaluation.calibration` diperluas — baris PT di `national_calibrated` =
interval β_e terkalibrasi / γ(h) (p & q baris e; e/w identik dengan versi lama) dan artefak baru `province_calibrated` (task3, 1.623 baris;
null |t*| dipool antarprovinsi per sel; q BH per sel). Hasil: PT 3/30 sel tidak memuat nol (resmi 1); bootstrap juga menarik deviasi provinsi ke
nol (median boot_ratio 0,51–0,67), interval resmi provinsi tidak memuat nol hanya 0–2,4% (di bawah 5% bahkan di bawah null), terkalibrasi
5–12%; BH global 1.623 sel: 7 deviasi (daging ayam Maluku/Papua/Kepulauan Riau, gula Kalimantan Barat/Tengah, minyak goreng ω Maluku Utara).
Interval resmi tetap dikutip lebih dulu; tabel provinsi deskriptif (H0-Het tetap uji konfirmatori). Ditolak: mengganti bootstrap resmi (deviasi
praregistrasi, butuh Task 1 ulang ± 2 jam). (2) D-163a kalibrasi walk-forward skor daftar pantau C1-tuned (protokol beku sha256 e0b50c8f…):
K1 Platt / K3 isotonik menurunkan ECE dev ke ≤ 0,05 tetapi Brier tidak membaik (+0,001..+0,003); K2 (intersep komoditas) menaikkan presisi
daftar pantau h 8 +0,046 (0,008..0,098) tetapi Brier +0,014 → tidak ada yang lolos, test tidak dibuka, C1-tuned tanpa kalibrasi tetap (petunjuk
K2 diteruskan ke kartu K4). (3) 13/33 fitur clustering konstan (τ² = 0): jarak & silhouette identik dengan/tanpa kolom itu; 0 kolom derau
float-jadi-pola pada 40 replikasi plasebo → tidak ada perubahan kode. Laporan `docs/audit/20261126_kelemahan_tercatat.md` §2–§3,
`docs/audit/20261126_kalibrasi_pantau.md`.

### D-162 — U108: flag `episode` Task 4 real-time (perbaikan bug) & Task 4 fx dijalankan ulang · FINAL (teknis) · 2026-11-26 (WP-25) · Danen
Fitur `episode` grup fx (M2, M3, C2, C2t) kini `data.drivers.realtime_episode_flag` = minggu pemicu (Σ de 8 minggu s.d. t ≥ 0,03), identik dengan
deteksi ulang episode dari data s.d. t (dites); flag periode penuh menandai minggu sela di antara pemicu yang digabung sebelum pemicu kedua
terjadi (6 dari 61 minggu; 1 origin uji 2024-12-02). `drivers_weekly.episode` (event study, robustness) tidak berubah. Dijalankan ulang (tercatat):
`forecast_preds`/`forecast_eval`/`ablation`, `direction_preds`, C2t di `direction_tuned_preds`, `robustness` (44 baris V2). M2/M1 1,0145 / 1,0166
→ 1,0086 (DM p 0,009) / 1,0125 (p 0,025); H5 1,112 / 1,115 (Holm 1,0); C2 − C1 h 8 +0,012 (−0,004..0,030); C1/C1t/M0/M1 identik → kesimpulan
H5 & fitur kurs tetap; klaim eksploratif "C2 > M3 pada h 4" gugur (q 0,36). Perbaikan bug sebelum pembekuan hasil, bukan deviasi
praregistrasi (fitur tetap "episode", kini memenuhi aturan as-of). Laporan `docs/audit/20261126_kelemahan_tercatat.md` §1.

### D-161 — NOAA CFSv2 diuji lewat Colab: skill prakiraan nyata tetapi gagal gerbang 5; oracle cuaca terealisasi juga gagal → mekanisme tertutup · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Lanjutan D-160 atas persetujuan Danen ("Ya, lewat Colab"). Ekstraksi di Colab (`docs/audit/20261126_sumber_baru/colab/`): run 00Z Jumat
minggu t (cadangan Kamis/Rabu; terbit sebelum `available_at` Minggu 00.00, D-155), byte-range 56 hari pertama `prate` & `tmax` dari fileServer
NCEI, dekode eccodes, rerata 182 sel grid per provinsi → 437/465 minggu 2017-12..2026-11 (28 tanpa run, HTTP 404; 3 di dev), 1.818 dtk.
Mount Drive gagal (popup OAuth) → hasil diunduh dari runtime. Agregat provinsi mingguan disimpan sebagai hasil audit (bukan sumber terdaftar).
Uji `cfs_du.py` (protokol dibekukan sebelum hasil): anomali terhadap klimatologi prakiraan init ≤ 2020, nasional tertimbang produksi ATAP untuk
cabai merah/rawit & bawang merah, arah nasional increment-only di atas konsensus C1t walk-forward 2021–2023. Skill CFSv2 vs NASA POWER
terealisasi nyata (hujan hari 1–28 r 0,42–0,55; suhu maks 0,58–0,61), tetapi ΔAUC −0,029..+0,006 (q ≥ 0,105; hujan 1–28 h 4 −0,014, interval
< 0) → gerbang 5 gagal. Oracle (cuaca terealisasi pada jendela prakiraan) −0,013..−0,081 → informasi cuaca 1–8 minggu ke depan tidak
menambah arah nasional di atas konsensus; kegagalan bukan soal skill prakiraan. **REJECTED, tanpa modeling; C1-tuned tetap.** U113 tinggal
GDELT. Aturan baru `docs/EKSPERIMEN.md` §3: sumber prakiraan diuji oracle-nya dulu. Laporan `docs/audit/20261126_sumber_baru.md` §3.

### D-160 — Kelayakan sumber & penemuan sinyal (GDELT, CFSv2, SIJAGUNG/SPORA, BNPB DIBI): tidak ada yang lolos lima gerbang; SIJAGUNG gagal sinyal; tanpa modeling · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Atas rancangan Danen (D-160 = kelayakan sumber, bukan optimasi). Gerbang: riwayat dev, ketersediaan, independensi, cakupan, sinyal arah nasional
tambahan di atas konsensus C1t (walk-forward, D-158). GDELT: G1–G3 ✓ (DATE batch 15 menit), G4/G5 tidak teruji karena skala TB → BigQuery berbayar
(U113). CFSv2: arsip seri waktu per run 2017–2026 di THREDDS NCEI, G1–G3 ✓, tetapi NetcdfSubset 404 & OPeNDAP 403; hanya berkas penuh 42,6 MB per
variabel per run (± 8–37 GB untuk run mingguan 2018–2026 + eccodes) → di luar persetujuan; ekspektasi rendah karena prakiraan 4–8 minggu terutama
memengaruhi panen sesudah horizon. SIJAGUNG diunduh (persetujuan Danen) & didaftarkan opsional `ditjenpkh_sijagung` + `load_sijagung`
(2019-01..2026-08, lag publik ± 3 bulan → +90 hari): G5 gagal (residual |ρ| ≤ 0,11, q ≥ 0,65; AUC nasional increment-only −0,01..−0,21 vs
konsensus untuk ayam & telur). SPORA export HTTP 500 (memori server). DIBI: tanggal kejadian saja, verifikasi triwulanan; server HTTP 521 saat uji.
**C1-tuned tetap.** Laporan `docs/audit/20261126_sumber_baru.md`.

### D-159 — Audit kelayakan data pasokan fisik & stok pasar (SP2KP, FDP, PIBC, GPM, KSA): tidak ada yang memenuhi syarat periode pengembangan; tanpa modeling · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Fase 1 rancangan Danen "Physical Supply & Market Inventory Intelligence", baca-saja (tanpa unduhan, tanpa login). SP2KP: portal publik hanya
harga; stok/pasokan **mingguan** ada di modul admin berlogin (Stok Mingguan Bapok, Survey Stock Pasar Induk, ekspor Excel) → BLOCKED, permintaan
resmi (U112). FDP: log program stabilisasi (39 pengiriman Jan–Okt 2026, 0,3–50 t), seri 2024+, bulanan B+1 → bukan ukuran arus pasokan. PIBC:
endpoint publik stok/masuk/keluar masing-masing 1 rekaman (01 Jun 2025), portal tidak diperbarui → BLOCKED. GPM: jumlah kegiatan per kab/kota ×
bulan 2024+, tanpa tanggal, vintage tarikan, kausalitas terbalik → kosong di dev. KSA: luas panen padi bulanan (realisasi 2018+), prakiraan
historis tertimpa; hanya beras (headroom ≤ +0,007). Sesuai syarat berhenti Danen: tidak ada backfill, test tidak dipakai, **tidak ada
modeling; C1-tuned tetap**. Spesifikasi permintaan data SP2KP (2018+, tanggal input/verifikasi/penutupan, stok & pasokan per pasar) di
`docs/audit/20261126_pasokan_fisik.md` §2; aturan kelayakan sumber di `docs/EKSPERIMEN.md` §3.

### D-158 — National Shock Nowcasting (breadth 110 kota PIHPS + model nasional–lokal), 2 iterasi: tidak ada perbaikan di luar keluarga intraminggu; C1-tuned tetap · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Atas rekomendasi Danen (Ide A breadth pasar, Ide B nasional → lokal) dengan dua iterasi mandiri; protokol tiap iterasi di-hash sebelum
modeling (`docs/audit/20261126_nasional_lokal/PROTOKOL_I1.md`, `PROTOKOL_I2.md`); dev ≤ 2023, test tidak dibuka. Audit data: panel kab/kota
Bapanas tidak dapat dipakai (portal tanpa unduhan/riwayat, SAPA terbatas → U111); pengganti PIHPS per kota diunduh atas persetujuan Danen
(`pihps_city` opsional: 110 kota harian sejak 2017-03-27, 12.870 permintaan, 0 galat, 3,9 MB, `load_pihps_city`). Iterasi 1 (Δ macro F1
h 4 / h 8): NL1 −0,002 / −0,003, NL2 −0,003 / +0,003, NL_BR −0,000 / +0,001, BR_NAT −0,006 / −0,008, BR_LOC −0,005 / −0,006 → 0 lolos. Uji
kebocoran breadth menangkap look-ahead cakupan (`kb_cov` penyebut seluruh periode, `kp_n` 0 vs kosong; 533.750 sel) → diperbaiki sebelum
hasil dilihat, uji ulang 0 sel. Kelemahan: konsensus C1t sendiri prediktor arah nasional terbaik (AUC 0,733 / 0,752 vs lapisan nasional
0,724 / 0,725); kalibrasi ulang dengan intersep historis memperburuk (base rate bergeser); kota pemimpin tidak stabil; satu-satunya informasi
baru = kesegaran (AUC nasional h 4 0,762 → 0,777–0,781 dengan increment-only). Iterasi 2: META (increment-only + β walk-forward) +0,009 /
−0,005..+0,002 (gagal); FR_CITY +0,024 (0,006..0,043) / +0,008 (0,000..0,015) lolos aturan tetapi FR_REF (tanpa kota, ≈ IW_NAT) +0,024 /
+0,004 → kontribusi kota −0,000 / +0,004 (belum terbukti) → **tidak diadopsi; C1-tuned tetap**. Prediksi maju beku base/FR_REF/FR_CITY
(`hasil/forward_preds_d158.csv`, 12.168 baris; base identik D-152). Aturan baru EKSPERIMEN §3: kandidat tingkat nasional wajib lolos layar
arah nasional vs konsensus C1t; kalibrasi ulang konsensus dengan intersep historis dilarang. Laporan `docs/audit/20261126_nasional_lokal.md`.

### D-157 — Pilot cuaca sentra produksi (NASA POWER) & realisasi impor bulanan untuk Task 4 arah: tidak membantu; C1-tuned tetap · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Atas usulan & persetujuan Danen (unduh NASA POWER 34 CSV, 3,6 MB; sumber baru `nasa_power` opsional, `redistribute: true` dengan
atribusi). Protokol + kartu eksperimen dibekukan sebelum modeling (`docs/audit/20261126_pilot_cuaca_impor/PROTOKOL.md`); dev ≤ 2023, test
tidak dibuka. Ruang: informasi sempurna arah nasional per komoditas × origin +0,105 (hortikultura saja +0,049 / +0,042; beras ≤ +0,007).
Fitur: W_NAT 6 anomali cuaca tertimbang porsi produksi ATAP (cabai merah, cabai rawit, bawang merah), W_LOC + titik provinsi, IMP 4 fitur
impor bulanan (Comtrade + BPS, rilis +45 hari); kebocoran 0 sel (12 origin). DU: W_NAT ρ parsial suhu maks +0,14 / +0,17, hujan 91 hari
−0,09 / −0,16 (tanda stabil tiap tahun, interval lebar); tidak lolos gerbang. Modeling (Δ macro F1 h 4 / h 8): W_NAT −0,003 / −0,003,
W_LOC +0,002 / −0,003, IMP −0,006 / −0,015 (lebih buruk, q 0,017); pasca-hoc koreksi logit walk-forward W_CAL −0,003 / −0,005 dengan Brier
memburuk. 0 lolos → C1-tuned tetap; tutup fitur impor bulanan & cuaca titik provinsi. Aturan baru `docs/EKSPERIMEN.md` §3: sinyal tingkat
nasional wajib diuji dengan koreksi walk-forward berparameter kecil sebelum modeling. Laporan `docs/audit/20261126_pilot_cuaca_impor.md`;
`src/` & artefak tidak berubah.

### D-156 — Audit preprocessing & optimasi macro F1 Task 4 arah: 27 kandidat baru, tidak ada yang mengungguli C1-tuned; registri eksperimen terpusat · FINAL · eksploratif · 2026-11-26 (WP-36) · Danen
Atas master task Danen (audit preprocessing + optimasi macro F1 tanpa mengubah label). Protokol dibekukan & di-hash sebelum run
(`docs/audit/20261126_task4_master_f1/PROTOKOL.md`, sha256 `f3b01357…`); seleksi hanya origin dev (≤ 2023), test 2024+ tidak dibuka.
Fase A (galat C1-tuned dev): oracle threshold global hindsight +0,000 / +0,006, per origin +0,035 / +0,024; AUC kuintil |y| terkecil
0,60 / 0,56 vs terbesar 0,77 / 0,82 → galat = informasi pada perubahan kecil + pergeseran base rate per origin, bukan threshold/model.
Fase B: tidak ada galat preprocessing baru (grid, nol sejati 98,6% cf→cf, penyelarasan waktu persis); bias origin hari libur (−0,10 / −0,16
porsi naik) adalah efek kalender origin, bukan komposisi hari. Kandidat (Δ macro F1 h 4 / h 8 vs C1-tuned): 8 keluarga fitur baru (40 kolom,
kebocoran 0 sel, tidak ada yang lolos layar DU) −0,006..+0,003; gabungan bersarang (pilih dev-awal, nilai dev-akhir) +0,002 / −0,012;
hapus-satu: `comm` −0,020 / −0,014, `lag` & `mom` ≈ 0; jendela 156 minggu −0,016 / −0,022; peluruhan −0,004 / −0,009; threshold walk-forward
−0,005 / −0,003 (per komoditas −0,002 / −0,020); bobot kelas +0,001 / −0,006; 5 seed +0,000 / +0,002; LightGBM −0,003 / −0,002, XGBoost
−0,005 / −0,013, CatBoost −0,007 / −0,009, ExtraTrees −0,008 / −0,022, logistik −0,031 / −0,057. 0/27 lolos aturan (Δ ≥ +0,005, interval
> 0, q BH, konsistensi tahun & origin, tanpa kemunduran per kelas/komoditas) → **C1-tuned tetap**, test tidak dibuka, S1–S3 tidak dihitung
ulang. Gerbang DU konkordan (8 gagal DU = 8 gagal Modeling). Baru: registri hidup `docs/eksperimen_registry.csv` (117 baris D-145–D-156;
aturan `docs/EKSPERIMEN.md` §6). Ditolak: menyederhanakan set fitur (tanpa keuntungan), tuning ulang (sudah Optuna D-145). Laporan
`docs/audit/20261126_task4_master_f1.md`; artefak & `src/` tidak berubah.

### D-155 — Audit D-152–D-154: universe S1 valid; koreksi klaim (skor arah ≠ peluang kenaikan material, test bukan independen, titik akhir, materialitas statistik vs kebijakan) · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Menjawab audit Danen. Protokol audit ditulis sebelum hitung (`docs/audit/20261125_business_understanding/PROTOKOL_AUDIT.md`). Universe
ranking S1 sah: baris y = 0 sudah kandidat; satu-satunya penyaringan berbasis target (target tak teramati) hanya 4 baris dev, 0 test, kini
diikutkan → presisi tidak berubah. V1 vs V2: presisi V2-10% lebih tinggi karena alarmnya separuh; pada jumlah alarm sama V2 ≈ V1
(0,188 vs 0,179) tetapi ± 1,5 provinsi/minggu tanpa alarm. Anggaran K = 1/2/3: presisi 0,21/0,18/0,16, recall 0,24/0,41/0,54 (test h 4);
K tidak dipilih. Kepekaan vs `R_rev` dengan interval +0,066 (0,033..0,101) / +0,041 (0,003..0,078). 57% alarm test pada 4 komoditas
diatur (ambang statistik 1,4–2,7%). IW_NAT membalik arah 12% / 7–8% baris, perbaikan ≈ perusakan (test h 4 721 vs 629). Koreksi tafsiran
dan aturan baru di `docs/EKSPERIMEN.md` §5 dan `results/findings.md`; adendum di laporan D-152, D-153, D-154 (isi lama tidak diubah):
p_up ≠ P(kenaikan material); S2 = kalibrasi arah; S3 bersyarat; test 2024+ bukan validasi independen; titik akhir ≠ kejadian dalam jendela;
K1 = screening asosiasi temporal (bukan sequential pattern mining); silhouette datar k = 2..6 (tipologi deskriptif); graf geografis =
proksi; `available_at` konservatif Minggu 00.00; kebocoran revisi tidak teruji. Usulan K4 (target risiko kenaikan material) ditunda sampai
kebutuhan TPID divalidasi (`[HUMAN]`).

### D-154 — Business Understanding Task 4 arah: kriteria bisnis S1–S3 di samping macro F1; C1-tuned memenuhi sebagai daftar pantau TPID · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Fase CRISP-DM 1 atas pilihan Danen. Protokol ditulis sebelum ukur (`docs/audit/20261125_business_understanding/PROTOKOL.md`, sha256
dicatat): pengguna TPID; kenaikan material = y_h ≥ persentil 80 |y_h| komoditas di baris latih (aturan `large_move_pct`, tanpa info masa
depan); S1 daftar pantau provinsi (2 komoditas teratas per provinsi) presisi > aturan naif terbaik (tren sendiri/nasional, balik ke
rata-rata, pola tahun lalu) dengan interval > 0; S2 Brier skill > 0 & ECE ≤ 0,05; S3 macro F1 saat bergerak material > aturan tanda tren.
Dev: S1 lolos (+0,110 / +0,067), S3 lolos, S2 gagal tipis h 8 (ECE 0,056). Test dibuka sekali (C1-tuned + aturan naif dari dev): S1–S3
lolos di kedua horizon; daftar pantau presisi 0,18 / 0,16 (laju-dasar 0,09), recall 0,41 / 0,36; arah saat bergerak material macro F1
0,81. Tidak ada model baru; label & macro F1 resmi tetap. Kriteria S1–S3 menjadi ukuran wajib di samping macro F1 (`docs/EKSPERIMEN.md`).
Batasan: asumsi praktik TPID belum divalidasi pengguna (`[HUMAN]`); "material" relatif per komoditas. Laporan
`docs/audit/20261125_business_understanding.md`.

### D-153 — Alur eksperimen Task 4 berbasis CRISP-DM + kartu 8 komponen; Data Understanding tiga arah tidak lolos gerbang Modeling · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Keputusan Danen: pengembangan Task 4 tidak lagi "fitur → model → skor → ulang", tetapi mengikuti CRISP-DM (IF4041 Modul 01) dengan kartu
eksperimen 8 komponen (problem, karakteristik data, pengetahuan, hipotesis, metode, validasi, kontrol kebocoran, keputusan) sebelum
implementasi; aturan di dokumen hidup `docs/EKSPERIMEN.md`, termasuk layar Data Understanding dengan kontrol positif/negatif dan gerbang
ke Modeling. Fokus berikutnya: pola sekuensial, clustering, graf. Data Understanding (dev saja, tanpa model baru): K1 lintas komoditas
0/360 lolos BH, pasangan terkuat = co-trend 2021–2022; K2 5 tipe seri (silhouette 0,34, ARI vs komoditas 0,31) tetapi tidak menjelaskan
skill di luar komoditas; K3 informasi tetangga di luar intraminggu sendiri + nasional ρ 0,021–0,025 (± 1/5 kontrol positif). Ketiganya
tidak lolos gerbang Modeling; K2 dilanjutkan hanya sebagai Knowledge Presentation (tipologi). C1-tuned, label, origin pengembangan
≤ 2023, dan perlindungan test 2024+ tetap. Langkah CRISP-DM berikutnya: Business Understanding (ukuran keberhasilan bagi TPID di dekat
batas informasi). Laporan `docs/audit/20261125_crisp_du.md`.

### D-152 — Validasi `IW_NAT`: kebocoran semua origin, diagnostik LOO/Jumat, prediksi maju beku; bukan kandidat baru · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Tindak lanjut tinjauan pasca-D-151. Protokol ditulis sebelum run (`docs/audit/20261125_iw_validasi/PROTOKOL.md`, sha256 dicatat): tidak ada
kandidat baru, `IW_NAT` beku, diagnostik hanya di origin pengembangan, test 2024+ tidak dibuka. `available_at` fitur minggu t = Sabtu
(Jumat + revisi H+1). Audit kebocoran 83 origin + 2 data penuh (hapus/rusak/hapus acak sesudah cutoff, rusak hanya provinsi lain, Jumat
untuk varian tanpa Jumat): 84/84 lolos, kontrol positif 84/84. Diagnostik dev: LOO = rerata D-151 (r 0,998; +0,005 / +0,001 vs `IW_NAT`) →
sinyal nasional dari provinsi lain; keserentakan arah tidak menambah; tanpa Jumat −0,010 (h 4) → separuh keuntungan h 4 = nowcast harga
terkini. Prediksi maju C1-tuned & `IW_NAT` dibekukan untuk 12 origin yang targetnya belum terealisasi (8.112 baris, sha256 di manifest;
evaluasi beku, label = target resmi). Daya: MDE batch maju 0,04–0,12; mendeteksi +0,0085 / +0,0033 butuh ± 185 / 355 origin (± 14 / 27
tahun) → validasi maju hanya penjaga kegagalan besar, bukan jalan konfirmasi. C1-tuned tetap; eksplorasi keluarga intraminggu di
pengembangan dihentikan. Ditolak: menjadikan LOO/keserentakan kandidat (selisih ≤ derau pelatihan, overfitting pengembangan). Laporan
`docs/audit/20261125_iw_validasi.md`.

### D-151 — Pilot informasi intraminggu & harga produsen PIHPS untuk Task 4 arah: produsen tidak membantu, `IW_NAT` belum terbukti · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Tindak lanjut roadmap pasca-D-150 (prioritas 1 harga produsen, prioritas 2 intraminggu). Protokol ditulis sebelum run
(`docs/audit/20261125_pilot_produsen_intraminggu/PROTOKOL.md`, sha256 dicatat): C1-tuned beku, label & baris resmi, seleksi di origin
pengembangan, aturan lolos D-147, satu kandidat per keluarga membuka test sekali. Pembanding = `direction_tuned_preds` C1t persis.
(A) Intraminggu dari `pihps_daily` (gap/return/rentang/volatilitas/jumlah hari/umur hari terakhir + rerata nasional): `IW_NAT` lolos
dev (+0,020 / +0,005) → test +0,0085 (−0,003..0,024) / +0,0033 (−0,004..0,011), q BH 0,28 / 0,30 → belum terbukti; test keluarga ini
tidak bersih (`iw_gap` dilihat di D-147). (B) Atas persetujuan Danen, `pihps_producer` diunduh (`price_type_id=4`, 3.570 permintaan,
0 galat, 0,4 MB; DKI kosong) dan didaftarkan `optional` (`redistribute: false`): seri tangga mingguan dengan lompatan besar, eceran
mendahului produsen; semua varian −0,006..−0,001 di dev → test tidak dibuka. C1-tuned tetap model terpilih; `IW_NAT` dicatat sebagai
varian eksploratif terbaik. Ditolak: memakai test 2024+ lagi untuk keluarga intraminggu (konfirmasi hanya pada origin baru). Laporan
`docs/audit/20261125_pilot_produsen_intraminggu.md`.

### D-150 — Pilot harga pedagang besar PIHPS untuk Task 4 arah: sumber opsional `pihps_wholesale`, tidak menambah daya prediksi · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Atas persetujuan Danen (unduh & pilot). Data diambil lewat endpoint grid yang sama dengan tombol "Download" resmi
(`price_type_id=3`, per bulan per provinsi, 3.978 permintaan, 0 galat) → zip berformat `pihps` di `data/raw/bi_pihps/`, didaftarkan
`optional` (`redistribute: false`), loader = `load_pihps(cfg, "pihps_wholesale")`. Fakta: carry_forward 85–98% sel mingguan; grosir
median 6–24% di bawah eceran; tidak mendahului eceran (korelasi Δeceran(t−1)→Δgrosir(t) ≥ arah sebaliknya). Pilot C1-tuned + fitur
grosir (Δ grosir 1/4/8, rerata nasional, selisih grosir–eceran & deviasinya, Δ relatif) dengan protokol D-147: tidak ada yang lolos
pengembangan (−0,006..+0,001), test tidak dibuka. C1-tuned tetap; data grosir disimpan untuk analisis margin deskriptif, tidak dipakai
model/artefak resmi. Ditolak: memasukkan grosir ke fitur resmi; mengakali reCAPTCHA Bapanas untuk harga produsen (jalur sah = SAPA,
`[HUMAN]`). Laporan `docs/audit/20261125_pilot_grosir.md`.

### D-149 — Split pengembangan s.d. 2024 untuk tuas sadar-rezim Task 4 arah (pasca-hoc eksploratif) · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Atas keputusan Danen setelah D-148 (drift baru muncul 2024+, tidak terpilih dari dev ≤ 2023). Ditetapkan sebelum run: pengembangan =
origin + h ≤ 2024-12-31 (52 / 51 origin), test = origin ≥ 2025-01-01, kandidat (8 kalibrasi temporal, 4 kelompok fitur rezim) dan
aturan buka test sama dengan D-147/D-148. Berlabel pasca-hoc karena hasil test 2024 sudah pernah dilihat. Hasil: tidak ada kandidat
lolos (terbaik kalibrasi prior 26 minggu +0,000 / +0,000; fitur rezim −0,011..+0,001) → test 2025+ tidak dibuka. Pada origin dev
2024, fitur kebijakan (`R_PO`) menghapus kelebihan prediksi naik komoditas diatur (+0,086 / +0,149 → +0,017 / +0,005) tanpa menaikkan
macro F1 (−0,002 / −0,010): baris yang dibalik sebelumnya benar ± 57%, jadi drift = bias proporsi, bukan pembatas skor; kalibrasi
berbasis label terealisasi memperburuk 2024 (tertinggal h minggu). C1-tuned tetap; tuas berikutnya = informasi baru (produsen/grosir,
pasokan). Laporan `docs/audit/20261125_task4_ronde4.md` §4. `src/`, `params.yaml`, artefak tidak berubah.

### D-148 — Roadmap pasca-audit Task 4 arah: preprocessing beku, `iw_gap` eksploratif, uji rezim & kalibrasi temporal · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Atas keputusan Danen setelah D-147. (1) Preprocessing baseline **dibekukan** (rerata hari teramati, target dari harga teramati, fitur
C1-tuned, tanpa normalisasi tambahan, carry_forward dipertahankan). (2) `iw_gap` disimpan sebagai varian eksploratif terpisah `C1t_iw`
(skrip audit D-147, prediksi lokal `data/interim/c1t_intraweek_preds.parquet`); tidak mengganti C1-tuned dan tidak diporting ke `src/`.
(3) Fitur sadar-rezim (base rate terealisasi 13/26 minggu, keseimbangan arah mingguan, umur kebijakan, jarak ke acuan; tanggal
diketahui vs berlaku dicatat) dan (4) kalibrasi probabilitas temporal (intercept dari prediksi lampau, koreksi pergeseran prior) diuji
dengan protokol D-147 (seleksi di origin pengembangan, C1-tuned tetap): tidak ada yang lolos aturan buka test; terbaik prior 26
minggu a = 0,5 +0,006 / +0,008 (interval memuat nol), fitur rezim −0,009..+0,001. Penyebab struktural: drift komoditas diatur baru
muncul 2024+ (dev kelebihan prediksi naik +0,004 / +0,005; fitur kebijakan kosong 72–83% di dev) sehingga tidak dapat dipilih dari
origin ≤ 2023. Ditemukan galat di fitur regulasi eksperimen ronde 2 (D-146): acuan beras sejak 2024-06-02 = batas atas premium
Rp15.800 (rentang diisi `value_max_rp`); hanya periode test, seleksi D-146 tidak terdampak; diperbaiki di fitur ronde ini.
(5) Data produsen/grosir/pasokan dan (6–7) benchmark/ensemble menunggu sumber baru. Koreksi flag `episode` real-time = U108 (saat
pipeline fx dijalankan ulang); `range_pos_52` tidak diprioritaskan. Job > 1 jam dijalankan di Colab T4 dengan output ke folder Drive
terpusat (`1m2gJk7kYQn4n5Gkn81xfRPbGReQWgYht`). Laporan `docs/audit/20261125_task4_ronde4.md`. `src/`, `params.yaml`, artefak tidak
berubah. C1-tuned tetap model arah terpilih.

### D-147 — Audit preprocessing Task 4 (klasifikasi arah) EKSPLORATIF: label, agregasi, kebocoran, seimbang-seri · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Atas permintaan Danen (audit ulang mentah → agregasi → missing → fitur → label → dataset sebelum menambah model/fitur). Evaluator
tetap C1-tuned; label evaluasi resmi tidak diubah; seleksi hanya di origin pengembangan. Laporan & skrip:
`docs/audit/20261125_task4_audit_preprocessing.md`. Tidak mengubah `src/`, `params.yaml`, atau artefak; 3 tes regresi kebocoran baru.
Temuan: (1) tidak ada kesalahan preprocessing yang mengubah label/fitur: 0 duplikat, target dari harga teramati tanpa isi, uji
perturbasi & penghapusan masa depan pada 76 origin × 54 kolom = 0 sel berbeda; (2) harga harian PIHPS seluruhnya kelipatan Rp50 (tick
0,32% beras, 0,28% gula, 0,23% minyak goreng); label < 1 tick 2,4–4,3% dan label yang berbalik bila hari di-resample 8–12% → akurasi
≈ 0,5, tetapi pada label ≥ 10 tick akurasi tetap 0,68–0,71 → derau pembentukan data hanya ± 0,01–0,015 dari celah skor;
(3) autokorelasi lag-1 Δ mingguan positif (efek rerata 5 hari), sebagian perubahan label sudah terjadi di dalam minggu origin;
(4) flag `episode` (grup fx, M2/C2) memakai informasi sesudah origin pada 1/76 origin (penggabungan episode berdempetan) → dicatat,
tidak diperbaiki (bias menguntungkan M2; H5 tetap tidak didukung); `range_pos_52` mengisi 0,5 untuk nilai tak terdefinisi;
(5) drift naik = pergeseran rezim komoditas diatur 2024+, bukan dominasi seri.
Eksperimen (10 varian, origin pengembangan, aturan buka test ditetapkan sebelum run): membuang label latih < 1 / < 2 tick, bobot
stabilitas, tanpa ffill, fitur dari harga hari terakhir ≈ 0; latih hanya ujung `observed` −0,017 / −0,022, normalisasi per seri dan
bobot seimbang komoditas lebih buruk di h 8; hanya `iw_gap` (log hari terakhir − log rerata minggu origin) + `n_days` lolos
(+0,014 h 4 dev) → test +0,004 (−0,005..0,013) / +0,005 (0,000..0,011), q BH 0,35 / 0,089 = belum terbukti. C1-tuned tetap model
terpilih; `iw_gap` tidak diporting. Ditolak: *fixed-market cohort* (data per pasar tidak ada di repo), mengubah label evaluasi atau
membuang perubahan kecil dari evaluasi.

### D-146 — Optimasi arah Task 4 ronde 2 EKSPLORATIF (diagnosis, fitur fundamental, model lain, 3 kelas) · FINAL · eksploratif · 2026-11-25 (WP-36) · Danen
Atas permintaan Danen (target 0,8–0,9, enam masalah A–F). Protokol sama dengan D-145: seleksi hanya di origin pengembangan (target
≤ 2023); test origin ≥ 2024 tidak dipakai memilih apa pun. Laporan & skrip: `docs/audit/20261125_task4_ronde2.md`. Tidak mengubah
`src/`, `params.yaml`, atau artefak.
Hasil: (1) kesalahan arah terkonsentrasi pada perubahan kecil (kuintil |y| terkecil macro F1 0,57; terbesar 0,74–0,79) dan drift naik;
(2) fitur regulasi HET/HAP, spasial (tetangga & hub), kalender, level ≈ 0; prior historis & gabungan −0,016 pada h 8 (interval < 0);
(3) LightGBM/XGBoost/ensemble −0,002..−0,006, spesialis per kelompok komoditas −0,010 / −0,015 → C1-tuned tetap model terpilih;
(4) target 3 kelas (tahap 1 "berubah?" + C1-tuned, τ dari pengembangan 0,67 / 0,70): test macro F1 0,625 / 0,606, dilaporkan terpisah
dari skor biner; (5) TCN multi-task & MLP (Colab T4, 3 varian × 3 seed): semua lebih buruk dari C1-tuned di pengembangan
(TCN deret −0,04..−0,07, TCN + tabular −0,03..−0,05, MLP −0,02..−0,03) → test tidak dibuka; prediksi di Drive tim
`KAGAMI/experiments/d146_tcn/out/`. Ditolak: ambang |y| untuk membuang perubahan kecil (penyederhanaan label), memilih fitur dari test.
LightGBM 4.6.0 & XGBoost 3.0.5 hanya di lingkungan lokal (bukan dependensi paket).

### D-145 — Optimasi klasifikasi arah Task 4 EKSPLORATIF (fitur, Optuna, threshold, kepala TimesFM) · FINAL · eksploratif · 2026-11-24 (WP-36) · Danen
Atas permintaan Danen (prioritas macro F1 arah h 4 & 8). Protokol ditetapkan sebelum tuning: origin pengembangan = origin + h ≤
2023-12-31 (38 / 37), test final = origin ≥ 2024-01-01 (37 / 36), tidak dipakai untuk memilih fitur, hyperparameter, varian, atau
threshold; baseline = prediksi resmi pada baris test identik; bootstrap blok origin + BH 26 perbandingan. Laporan, skrip, dan
konfigurasi: `docs/audit/20261124_task4_optimasi_arah.md`. Tidak mengubah `src/`, `params.yaml`, artefak, atau uji praregistrasi.
Diputuskan: (1) 8 kelompok fitur per seri dari log harga s.d. t (lag panjang, EWM, sd, momentum, musiman, deviasi MA/rentang/spasial,
umur carry-forward, sinyal nasional komoditas), ablation di pengembangan → `vol` & `cf` dibuang; (2) C1-tuned = HGB Optuna TPE 40
trial (lr 0,028, 250 iterasi, 23 daun, min_leaf 319, l2 3,85, max_features 0,335); (3) C2-tuned = sama + kurs (12 trial); (4) TSMixer
Optuna 10 trial termasuk loss BCE arah; (5) threshold dari pengembangan; kalibrasi residu walk-forward TimesFM; (6) kepala CatBoost
dari ramalan TimesFM walk-forward (+ fitur + OOF C1-tuned), dilatih hanya pada origin o' + h ≤ o. Ditolak: tuning pada semua origin
(bocor ke test), threshold walk-forward dari periode test, prediksi selektif sebagai skor utama (mengecilkan cakupan).
Uji kebocoran: merusak harga sesudah origin tidak mengubah 37 fitur baru pada minggu ≤ origin. Optuna 4.5.0 & CatBoost 1.2.8 hanya
di lingkungan lokal (bukan dependensi paket).
Hasil (test final): C1-tuned macro F1 0,677 / 0,680 (h 4 / 8; seed 2–3 ± 0,003) vs C1 0,586 / 0,607, TimesFM 0,618 / 0,621 →
+0,059 (0,043..0,075) / +0,053 (0,027..0,077) vs TimesFM, q 0,001; MCC 0,36, ROC-AUC 0,74, cakupan 0,855 / 0,907 (sama untuk semua).
Kurs tidak membantu (C2t − C1t −0,004 / +0,001); threshold dev tidak menambah untuk klasifier, +0,012 / +0,024 untuk TimesFM;
kepala TimesFM 0,672 / 0,676 = setara C1-tuned (−0,005 / +0,002); TSMixer-tuned tidak lebih baik dari resmi (h 8 thr dev −0,026,
lolos BH). Kenaikan hampir seluruhnya dari fitur (deviasi & sinyal nasional), bukan hyperparameter. Bukan uji praregistrasi;
H5 tetap tidak didukung.
Porting (hari yang sama, atas keputusan Danen): `features/price_dynamics.py` (fitur), `models/direction.py` (`TUNED_HGB`,
C1t/C2t, `rolling_direction_tuned`), `pipelines/task4.run_direction_tuned`, CLI `task4 --direction-tuned`, artefak eksploratif
`direction_tuned_preds` (tidak dikirim, 38 artefak), tes `tests/test_direction_tuned.py`. Hyperparameter sebagai konstanta modul
(bukan `params.yaml`, beku sejak G6). Prediksi identik dengan eksperimen (selisih p 0,0).

### D-144 — Kelengkapan klasifikasi, replikasi seed, kepekaan blok, ringkasan Task 4 · FINAL (teknis) · 2026-11-24 (WP-36) · Danen
Atas tinjauan lanjutan audit (Lampiran C). Diputuskan: (1) `direction_metrics` menambah F1 berbobot, cakupan, dan akurasi
termasuk perubahan nol (kelas FLAT tetap tidak dimodelkan: butuh ambang baru setelah G6); (2) replikasi seed model deep lewat
nama `<model>_r<k>` (seed + 1000·(k−1), origin & jadwal refit sama), diringkas `h{h}_seed_replication`, dikeluarkan dari metrik
utama & segmen; (3) `h{h}_block_sensitivity` (blok 2/3/4/6 origin, lag DM 1/2/3/5) + porsi keputusan stabil; (4) segmen
"tahun origin" (cek kontaminasi TimesFM); (5) halaman 7: tabel perbandingan model Task 4 tampil pertama, diagnostik lanjutan
di balik sakelar, filter penilaian default tanpa "informasi", Riwayat mode "terbaru per tahap + eksekusi"; (6) RunRecord
`evaluator_version` (schema 3); (7) robustness Tier 2 dijalankan tercatat ke folder sementara, identik sha256 → log diimpor,
file resmi tidak diganti. Ditolak: kelas FLAT dengan ambang (deviasi praregistrasi), 5 seed (3 cukup untuk menunjukkan rentang;
± 45 menit per 2 seed di CPU), menghapus log evaluasi lama (log tidak pernah ditimpa/dihapus, D-137).
Hasil: F1 makro h 8 (pada baris berubah, cakupan 0,907): TimesFM 0,623, C2 0,614, C1 0,605, TSMixer 0,604, M3 0,594, M1 0,551; F1 berbobot hampir sama; akurasi bila minggu tanpa perubahan dihitung salah: TimesFM 0,566, M1 0,508. Replikasi 3 seed (h 8): TSMixer MAE/M1 0,966 ± 0,007 (0,959..0,972), akurasi 0,610 ± 0,005; PatchTST 0,972 ± 0,011, 0,583 ± 0,016; TSMixer + kurs 0,995 ± 0,009 (lebih buruk dari TSMixer di ketiga seed). Kepekaan blok bootstrap 2/3/4/6 origin: 17/17 keputusan sama di kedua horizon; DM TimesFM vs M1 p < 0,001 dan M2 vs M1 p 0,006–0,018 untuk lag HAC 1–5. Per tahun origin, keunggulan MAE TimesFM bertahan pada 2026 (0,938) walau lebih kecil dari 2023–2024 (0,876 / 0,834). Robustness Tier 2 dijalankan tercatat: identik sha256 dengan file resmi (679 baris), sekarang sinkron.

### D-143 — Koreksi multiplisitas BH untuk perbandingan eksploratif di penilaian halaman 7 · FINAL (teknis) · 2026-11-24 (WP-36) · Danen
Dari audit ulang (Lampiran C, butir 4): 30 beda akurasi berpasangan, 132 metrik arah vs acuan, dan 14 rasio MAE model
eksploratif dinilai masing-masing pada 95%. Diputuskan: p bootstrap persentil dua sisi (`metrics.bootstrap_p`, konsisten dengan
interval persentil) untuk metrik arah dan beda berpasangan, p DM untuk rasio MAE; `assessment.apply_multiplicity` menerapkan
Benjamini–Hochberg per keluarga per run (q < 0,05 = `inference.fdr_q`), hasil yang tidak lolos diturunkan ke "belum terbukti
berbeda" dengan alasan; tabel segmen dikoreksi BH di seluruh tabel per horizon. Uji resmi praregistrasi (M0/M2/M3 vs M1,
H5 Holm) dan hipotesis tunggal tidak dimasukkan (sudah punya aturan inferensi sendiri). Ditolak: Holm (terlalu konservatif
untuk diagnostik ratusan sel yang saling berkorelasi; BH konsisten dengan kebijakan FDR proyek), satu keluarga gabungan
(mencampur pertanyaan berbeda). Hasil: Lolos BH: MAE TimesFM (± kurs) vs M1 h 4 & 8 (q ≤ 0,004); akurasi arah TimesFM vs M3 h 4 (q 0,015), C2 vs M3 h 4 (q 0,015), C1 vs M1 h 4 & 8 (q ≤ 0,024); akurasi arah vs baseline: semua model baru dan M3 (q ≤ 0,034), M1/M2 tidak. Gugur: TSMX_fx vs TSMX MAE h 4 (p 0,020 → q 0,057); segmen kaku TimesFM (q 0,053) & M2 (q 0,080); segmen lentur M1 (q 0,064). Beda berpasangan 5/30 bertahan; metrik arah vs acuan 123/132; rasio MAE eksploratif 4/14; tabel segmen h 8: 47 lebih baik, 15 lebih buruk dari 190.

### D-142 — Model deep learning & foundation EKSPLORATIF untuk Task 4 · FINAL · eksploratif · 2026-11-24 (WP-36) · Danen
Danen memutuskan (2026-11-24) model ditambahkan sekarang, tidak menunggu pembekuan 27 Nov; D-141 yang menolaknya sebelum
pembekuan diganti untuk bagian ini. Unduhan disetujui Danen: paket `timesfm` 3.0.2 (PyPI) + bobot google/timesfm-3.0-pytorch
(1,32 GB, TimesFM Non-Commercial License v1.0, diterima Danen); Chronos-2 TIDAK diunduh (tidak disetujui). Diputuskan:
`models.neural` dengan PatchTST, TSMixer, TSMixer + kanal kurs & harga dunia as-of (ablation kurs), TimesFM 3.0 zero-shot dan
TimesFM + kovariat masa lalu kurs & harga dunia. Target, origin, dan baris uji identik dengan M0–M3 (`split_origin`), jadi MAE,
DM, dan metrik arah sebanding. Model deep dilatih global (embedding komoditas) dengan loss L1, refit tiap 4 origin (16 minggu),
jendela latih hanya dengan target terealisasi s.d. origin; hiperparameter ditetapkan sebelum melihat hasil (lookback 52, d 32,
2 lapis, 4 epoch, ≤ 40.000 jendela), sebagai konstanta modul eksploratif, BUKAN `params.yaml` (beku G6, sha256 di
PREREGISTRATION). Tes: mengubah data sesudah origin tidak mengubah ramalan (tanpa kebocoran). Artefak `deep_preds` (tidak
dikirim), `kagami task4 --deep`, extra `[deep]` di pyproject (torch, timesfm). Uji resmi H5 tetap M2 vs M1.
Ditolak: TimesFM sebagai pengganti uji H5 (bukan praregistrasi; tidak menguji fitur kurs), fine-tuning TimesFM (CPU, tanpa GPU),
menyertakan bobot di zip juri (1,32 GB, lisensi non-komersial; juri mengunduh sendiri).
Hasil (run lokal CPU 2026-11-24, 7.632 dtk): TimesFM 3.0 zero-shot (TFM) MAE / M1 0,935 (h 4, DM p 0,0001) dan 0,895 (h 8, DM p < 0,001), R² vs ramalan nol 0,19 / 0,25 (M1 0,09 / 0,07), akurasi arah 0,616 / 0,623 (selisih vs baseline 0,049..0,116 / 0,026..0,122), ROC-AUC 0,66 / 0,69; TFM − M3 akurasi arah +0,043 (0,021..0,064) pada h 4, h 8 tidak terbukti. PatchTST & TSMixer: MAE / M1 0,96–1,00 (DM tidak nyata), akurasi arah 0,58–0,61. Fitur kurs tidak membantu: TFM_fx / TFM MAE 1,005 / 1,010 (tidak nyata), TSMX_fx / TSMX 1,041 (h 4, DM p 0,020, lebih buruk) / 1,029; selisih akurasi arah ± 0,01 (memuat nol). Komoditas kaku: semua model deep di bawah baseline arah (TFM −0,073 pada h 8). Catatan kontaminasi: TimesFM 3.0 dilatih ulang Google pada 2026 dengan korpus publik yang tidak diketahui isinya; deret harga pangan Indonesia periode uji 2021–2026 mungkin ikut di dalamnya, jadi keunggulan zero-shot adalah batas atas.

### D-141 — Klasifier arah EKSPLORATIF (HGB classifier, rolling-origin Task 4) · FINAL · eksploratif · 2026-11-24 (WP-36) · Danen
Atas permintaan Danen setelah D-140 menunjukkan ramalan regresi M1/M2 tidak lebih baik dari menebak arah terbanyak. Diputuskan:
`models.direction` dengan HistGradientBoostingClassifier (sudah ada di scikit-learn, tanpa dependensi baru; hiperparameter =
params.forecast.hgb, sama dengan M3 → tidak ada angka analisis baru) dilatih langsung untuk arah naik/turun (baris y = 0 dibuang),
fitur & rolling-origin identik dengan Task 4 (`features.forecast.split_origin`, latih t + h ≤ origin, harga dunia as-of). Dua
varian: C1 (base + id) dan C2 (base + fx + id = fitur M3) sehingga C2 − C1 = ablation kurs pada klasifier. Artefak baru
`direction_preds` (tidak dikirim), `pipelines.task4.run_direction` / `kagami task4 --direction`; evaluasi di `evaluate_task4`
(metrik arah + interval bootstrap blok origin, beda berpasangan C2 vs C1, C2 vs M3, C1 vs M1, prediksi selektif per origin,
tabel per segmen). EKSPLORATIF: tidak menggantikan uji H5 (MAE + DM) dan tidak ditulis sebagai hasil konfirmatori.
Ditolak: model deep learning / foundation model (TimesFM, Chronos-2, PatchTST) sebelum pembekuan 27 Nov (dependensi `torch`,
unduhan bobot model, GPU, zip juri tidak bisa memuat bobot; tidak menjawab H5), kelas "tetap" dengan ambang (angka baru setelah
G6), memilih ambang probabilitas di luar 0,5 dari data uji (bocor).
Hasil (run lokal 2026-11-24, 1.119 dtk): C2 (+ kurs) akurasi arah 0,598 / 0,617 (h 4 / h 8) vs baseline mayoritas 0,527 / 0,545 (selisih +0,071, interval 0,034..0,108 pada h 8); C1 (tanpa kurs) 0,588 / 0,607; ROC-AUC C2 h 8 0,654 (0,623..0,682); MCC 0,17–0,23. C2 − C1 +0,010 (−0,005..0,024) / +0,009 (−0,007..0,027) → fitur kurs tidak terbukti membantu, konsisten dengan H5; C2 − M3 +0,025 (0,011..0,041) pada h 4, +0,014 (−0,000..0,031) pada h 8; C1 − M1 +0,045 / +0,047 (interval > 0). Komoditas kaku: C2 −0,026 (−0,067..0,024) → tidak lagi lebih buruk dari baseline (M3 −0,058); lentur +0,124. Prediksi selektif C1 h 8: akurasi 0,707 pada cakupan 25%.

### D-140 — Evaluasi dua lapis, interval bootstrap metrik arah, lineage output, sidik jari kode · FINAL (teknis) · 2026-11-24 (WP-36) · Danen
Dari audit halaman 7 (`docs/audit/20261124_audit_evaluasi_eksekusi.md`) dan rekomendasi tindak lanjutnya. Diputuskan (hanya lapisan
`tracking`, app, wiring; hasil analisis, `params.yaml`, dan artefak tidak berubah):
(1) status hitung (`ok`) dipisah dari penilaian terhadap acuan eksplisit (`tracking.assessment`, dihitung saat log dibaca);
(2) interval 95% metrik arah Task 4 dari bootstrap blok origin (unit = origin; blok ceil(h/4) + 1; 999 replikasi; seed + 3901) +
tabel per segmen (komoditas, jalur eksposur, grup H5, kekakuan harga = carry_forward ≥ 50%); (3) lineage output: `artifact_sync`
dan `stage_states` memisahkan eksekusi dari evaluasi-saja dan menandai artefak yang bukan output run eksekusi terakhir;
(4) RunRecord `code_sha256`, `git_dirty`, `environment` (schema 2; log lama tetap terbaca); (5) `task2.OPTIONAL = (province_features,)`,
`robustness.OPTIONAL = (pihps_daily, exposure, province_features)` + notebook 02/05 menariknya + tes baca-vs-deklarasi (bug nyata:
di cloud pembanding n_kota dan sebagian Tier 2 diam-diam dilewati); (6) kesehatan fitur clustering, kriteria robustness tambahan
(lebar interval, kesamaan tanda, |Δ|/SE, kesamaan keputusan), cek ablation = M1; metrik ganda/teks dibuang.
Ditolak: menulis penilaian ke log JSON (penilaian harus bisa diperbaiki tanpa menulis ulang log), bootstrap per baris (n baris
melebih-lebihkan informasi), ablation per kelompok fitur atau model baru (butuh Task 4 ulang di Kaggle & eksploratif setelah
pembekuan), mengimpor log run end-to-end folder lain (artefak resmi akan tampak tidak sinkron).
Hasil pada artefak resmi: selisih akurasi arah vs baseline mayoritas h 8 M1 +0,015 (−0,029..0,053), M2 +0,015 (−0,024..0,049),
M3 +0,057 (0,021..0,088); h 4 M3 +0,046 (0,011..0,072), M1/M2 memuat nol. Komoditas kaku: semua model di bawah baseline (M2 h 8
−0,061, −0,123..−0,004). ROC-AUC M1 h 8 0,569 (0,535..0,608): di atas acak tetapi tidak lebih berguna dari menebak arah terbanyak.
share_fx_improves 5/20 (binomial p 0,041). 13/33 fitur clustering konstan. `robustness` resmi (679 baris) bukan output run
eksekusi terakhir (486 baris, tanpa Tier 2). Diagnostik, bukan uji praregistrasi.

### D-139 — Diagnostik klasifikasi arah perubahan Task 4 di log evaluasi · FINAL (teknis) · 2026-11-24 (WP-36) · Danen
Atas permintaan Danen (metrik seperti F1). Proyek tidak punya tugas klasifikasi berlabel, jadi keluarga klasifikasi tetap "tidak
berlaku" untuk tahap 0–3 dan robustness. Satu turunan yang bermakna: arah perubahan harga dari ramalan regresi Task 4. Diputuskan:
`tracking.metrics.direction_metrics` (kelas = tanda y; y = 0 dan ramalan = 0 dikeluarkan + dicatat; baseline kelas mayoritas;
penjaga satu kelas & M0), dipanggil `evaluate_task4` per horizon × model, ditampilkan di app hal. 7 (tabel + `viz.plots.confusion_matrix`).
Ditolak: kelas "tetap" dengan ambang |Δlog| (angka analisis baru setelah G6), menguji selisih akurasi antar model (observasi bertumpuk
& berkorelasi; uji resmi = DM pada MAE), F1 untuk clustering Task 2 (tanpa ground truth; struktur tertanam sudah memakai ARI & recovery).
Hasil pada artefak resmi: akurasi arah 0,543 / 0,557 / 0,573 (M1 / M2 / M3, h 4) dan 0,560 / 0,560 / 0,602 (h 8) vs baseline kelas mayoritas 0,527 / 0,545; F1 makro 0,538 / 0,550 / 0,566 dan 0,551 / 0,549 / 0,594; MCC 0,08–0,19; ROC-AUC 0,567–0,627. M3 terbaik pada arah walau MAE-nya lebih besar dari M1 pada h 4; M2 ≈ M1 pada h 8 → kesimpulan H5
tidak berubah. Diagnostik, bukan uji praregistrasi; hasil analisis & artefak tidak berubah.

### D-138 — CLI memaksa stdout/stderr UTF-8 (crash cp1252 saat output diarahkan ke file di Windows) · FINAL (teknis) · 2026-11-24 (WP-36) · Danen
Ditemukan saat run end-to-end lokal semua tahap (`python -m kagami all > log`, folder kode bersih, 2026-11-24): `task1` gagal setelah
bootstrap & plasebo selesai (5.312 dtk) di `print` τ² `features.response.shrink_deviations`, karena stdout yang diarahkan ke file di
Windows memakai cp1252. Kaggle/Colab memakai UTF-8, jadi tidak pernah muncul di sana. Diputuskan: `cli.main` memanggil `_utf8_stdio`
(reconfigure UTF-8, errors=replace) sebelum apa pun; tes regresi `test_runtime::test_cli_stdout_redirected_cp1252_does_not_crash`.
Ditolak: mengganti semua simbol non-ASCII di pesan progres (banyak modul, mudah terulang). Log tracking mencatat kegagalan
dengan benar (`logs/errors/`); checkpoint `boot_replicates`/`placebo_stats` membuat run ulang melanjutkan tanpa mengulang replikasi.
Pada run yang sama ditemukan bug kedua: `viz.plots.run_durations`/`metric_trend` memakai `pd.to_datetime` tanpa format, sehingga
halaman 7 crash bila log lama (`started_at` tanpa mikrodetik) bercampur log baru (dengan mikrodetik, sejak D-137). Diperbaiki dengan
`format="ISO8601", utc=True` + tes `test_tracking::test_run_plots_accept_mixed_timestamp_formats`.
Hasil analisis tidak berubah.

### D-137 — Log eksekusi & evaluasi terpusat (`src/tracking/`, `logs/`, app hal. 7) · FINAL (teknis) · 2026-11-24 (WP-36) · Danen
Atas permintaan Danen: setiap eksekusi tahap harus menghasilkan log evaluasi terstruktur yang dapat ditelusuri dan dibandingkan.
Diputuskan: subpaket baru `kagami.tracking` (bukan di `evaluation/`, yang berisi evaluasi statistik penelitian) dengan dekorator
`@tracked` di keenam `pipelines.<tahap>.run`, sehingga CLI dan notebook tercatat tanpa perubahan sel. Lineage lewat pengamat baca/tulis
di `utils.io` (input di-hash saat dibaca). Run induk = run yang menulis file dengan hash sama, jadi dependensi mengikuti data
nyata (DAG dari REQUIRES, tidak linear). Log JSON per run di `out_dir/logs/{runs,evaluations,errors,pipelines}/` ditulis eksklusif
(tidak ditimpa), path relatif, tanpa nama host/pengguna, di-track git agar app daring membacanya, ikut zip juri (`logs/*/*.json`), dan ikut `drive.push`/`pull`.
Evaluator hanya membaca artefak. Metrik generik berpenjaga memberi `not_applicable` + alasan (silhouette/DB/CH saat k = 1, MAPE saat
y = 0, R² LP). Klasifikasi, reduksi dimensi, dan NLP dinyatakan tidak berlaku untuk proyek. Hitung ulang hanya sebagai cek integritas
(silhouette per k, MAE). Ditolak: logging framework / MLflow (dependensi baru, server, tidak offline di paket juri); menulis log
di dalam artefak registry (mengubah kontrak & hash artefak); mengubah sel notebook (dekorator cukup). Hasil analisis, `params.yaml`,
dan artefak tidak berubah; bukan deviasi praregistrasi. Rincian: docs/TRACKING.md.

### D-136 — App: artefak yang belum ada tidak di-cache; kunci cache memuat waktu ubah file · FINAL (teknis) · 2026-11-24 (WP-31) · Danen
Setelah D-135 di-push dan di-merge ke `main`, app daring tetap "Menunggu hasil" untuk artefak yang baru ditambahkan (halaman 6 versi baru
sudah jalan, tetapi `robustness` dianggap belum ada). Penyebab: `common.load` dibungkus `@st.cache_data` dan ikut menyimpan `None`;
Streamlit Cloud menarik commit baru tanpa me-restart proses, sehingga `None` lama bertahan (direproduksi lokal dengan AppTest: file
ditambahkan di proses yang sama → tetap "Menunggu hasil"). Diputuskan: `load` mencari lokasi file (`find_artifact`) tanpa cache dan
mengembalikan `None` bila tidak ada; pembacaan di-cache dengan kunci (nama, path, mtime_ns, ukuran), jadi versi artefak baru juga
langsung terbaca. Tes regresi `test_app_data::test_load_does_not_cache_missing` (gagal pada versi lama). Ditolak: `ttl` pada cache
(tetap basi selama ttl). Untuk deploy yang sudah berjalan, sekali "Reboot app" di Streamlit Cloud mengosongkan cache lama.

### D-135 — Deploy app: artefak yang dibaca app di-track git; halaman 6 tidak menunggu robustness · FINAL (teknis) · 2026-11-24 (WP-31, WP-32) · Danen
App di Streamlit Community Cloud (kagami.streamlit.app) kosong di keenam halaman ("Menunggu hasil") karena `.gitignore` mengabaikan
`results/*` kecuali `findings.md`; Cloud hanya melihat isi repo. Diputuskan: `.gitignore` membuka 23 artefak yang dibaca app (± 1,4 MB;
semuanya `ship=True`, boleh dikirim menurut D-104): `results/stage0/{eligibility,episodes,mde,stage0_report}`, `results/task1/{profiles,
events,response_features}`, seluruh `results/task2/` & `results/task3/`, `results/task4/{forecast_eval,ablation}`, `results/robustness.csv`.
Tetap tidak di-track: `boot_replicates` & `placebo_stats` (14 MB, tidak dibaca app), `fx_variation`, `data/processed/`, `data/interim/`.
Halaman 6 kini memuat `findings` dan `robustness` terpisah (sebelumnya `findings.md` yang ada di repo pun tidak tampil tanpa
`robustness`). `package.CODE_GLOBS` + `requirements.txt` (dibaca Cloud). Ditolak: mengunduh artefak dari Drive saat app jalan (butuh
kredensial & jaringan; melanggar D-010 hanya-baca-artefak lokal), Git LFS (tidak perlu untuk 1,4 MB). Konsekuensi: setiap kali artefak
yang dibaca app berubah, versi baru ikut di-commit agar app live sama dengan Drive tim. Tidak mengubah hasil.

### D-134 — Tampilan app: palet tervalidasi, peta Indonesia offline, provinsi = deviasi tersusut · FINAL (teknis) · 2026-11-23 (WP-31) · Danen
Eksekusi PLAN.md §18 (evaluasi desain spec visualisasi). (1) Modul `viz/style.py`: palet kategoris 3 slot (biru/oranye/aqua, lolos
validator dataviz semua-pasangan; palet bawaan Streamlit & Plotly gagal: CVD ΔE 5,8, kontras < 3:1), diverging biru↔merah dengan
titik tengah abu-abu (mengganti `RdBu_r` bertitik tengah putih), warna mengikuti entitas (M2 biru, M3 oranye, M0/M1 abu-abu),
label bahasa pengguna, format angka Indonesia (`separators=",."`, minus tipografis). (2) Peta: geometri geoBoundaries IDN ADM1
(34 unit, ODbL, keputusan Danen: unit utama 7 wilayah) disederhanakan ke `data/reference/indonesia_provinces.geojson` (98 KB).
Digambar di sumbu kartesius (`fill="toself"` + titik ibu kota), bukan `go.Choropleth`: subplot geo Plotly mengunduh
`cdn.plot.ly/un/world_110m.json` walau `visible=False` (terbukti di browser) → gagal saat G7 offline. Peta wilayah = provinsi diwarnai
nilai wilayahnya (tanpa shapely/dissolve). `package` kini menyertakan `data/reference/*.geojson` dan `.streamlit/config.toml`
(telemetri Streamlit dimatikan). (3) Baris provinsi `profiles` = deviasi δ (Σ_r δ = 0) dalam dua versi per sel (mentah &
`shrunk`); app memakai versi tersusut EB dan melabelinya "deviasi", bukan "respons" (sebelumnya kurva mencampur dua versi).
(4) Lencana status: interval NaN (PT wilayah) → "interval tidak tersedia" (sebelumnya "terdeteksi" karena `nan <= 0` False).
Ditolak: Mapbox/`choropleth_map` (tile daring), GeoPandas (dependensi baru), dendrogram & heatmap ablation (PLAN.md §18.7).
Tidak mengubah artefak atau hasil; bukan deviasi praregistrasi.

### D-133 — U102: uji tumpang tindih konkordansi HS dijalankan pada 2023 dengan Comtrade API publik · FINAL (teknis) · 2026-11-23 (WP-07, WP-10) · Danen
Rumusan awal (Comtrade vs BPS Apr–Des 2022) butuh portal ekspor-impor BPS yang error. Diganti tahun 2023: BPS bulanan HS8 sudah ada lokal,
Comtrade 2023 diambil dari API publik preview UN Comtrade (izin Danen; 15 kode, 160 baris, skema sama dengan `comtrade_import`) sebagai snapshot
baru `comtrade_import_2023` (`optional`, tidak dikirim). Nomenklatur keduanya HS2022/BTKI 2022, jadi pemetaan yang diuji sama dengan sambungan
2017–2022 ↔ 2023+ (perubahan HS2017→HS2022 hanya 0709.59, tidak dipakai). Fungsi `qa.check_trade_overlap` + `stage0_report` §9. Hasil: 14/15 kode cocok persis (rasio nilai 1,000, korelasi bulanan 1,000; termasuk bawang putih 070320 USD 648,6 juta); 1511 minyak sawit 0,944 (USD 1,2 juta, subpos HS8 tidak lengkap, tidak dipakai rasio impor); kg gula 1,115 (nilai 1,000; berat Comtrade diestimasi). Kesimpulan: konkordansi lengkap untuk kode yang dipakai rasio impor;
rasio lama BPS 2023 / Comtrade 2022 mencerminkan perubahan antartahun.

### D-132 — U106 diperbaiki: p meta-regresi konsisten dengan interval laporan; ARI NaN saat k = 1; τ² REML dilaporkan · FINAL (teknis) · 2026-11-23 (WP-23, WP-20, WP-17) · Danen
(1) `meta_regression`: p dua sisi = max(p CR2, p_boot), p_boot = 2 × porsi replikasi di sisi nol yang berlawanan dengan estimasi,
dibaca dari fungsi kuantil interpolasi linear yang sama dengan persentil interval → p < 0,05 ⇔ interval laporan (CR2 ∪ bootstrap)
tidak memuat nol (tes `test_boot_side_p_matches_percentile_interval` pada 200 sampel acak). H3 satu sisi: max(p CR2 satu sisi, porsi
replikasi ≥ 0). Kolom aditif `p_boot`, `q_fdr` (BH atas baris dua sisi). Data asli: baris p < 0,05 turun 11 → 0 dari 88; q minimum 1,0;
H3 gabungan tetap p 0,80. (2) `compare_partitions`: klaster tunggal → ari NaN ("tidak berlaku"), bukan 0. (3) `heterogeneity_stats`
menambah statistik `tau2_reml` berdampingan dengan τ² DL (kotak WP-17); uji H0-Het tetap Q, BH per statistik sehingga q lain tidak
berubah. Ditolak: p dari bootstrap saja (membuang CR2 yang praregistrasi). Bukan DEVIASI: interval tidak berubah.

### D-131 — Task 4: diagnostik penyandian musiman M1 (dummy bulan + Idulfitri); hasil praregistrasi tetap resmi · FINAL (teknis) · 2026-11-23 (WP-26, WP-27) · Danen
Temuan audit: M1/M2 memasukkan `month` sebagai angka 1–12 dan `idf_rel_week` yang kosong di luar jendela [−6, 4] diisi median latih.
Keputusan Danen: hasil praregistrasi tetap resmi (mengganti model setelah melihat H5 = jalur bercabang); diagnostik ad hoc (skrip
scratch, bukan artefak) mengulang M0/M1/M2 ridge pada origin, fitur, dan alpha-CV yang sama dengan 11 dummy bulan + 11 dummy minggu
relatif Idulfitri. Cek reproduksi M1 resmi origin pertama: selisih maks 4e-17. Hasil: M2/M1 1,005 (h 4, DM p 0,53) dan 1,019 (h 8,
p 0,077); H5 h 8 large_move impor langsung 0,90, input impor 0,99, Holm 0,56 → kesimpulan sama (fitur kurs tidak memperbaiki MAE, H5
tidak didukung). M0/M1 turun ke 0,95 / 0,97 (beras 0,39, daging sapi 0,38): dummy musim yang dikumpulkan lintas komoditas tanpa identitas
komoditas memperburuk komoditas yang diatur. Kesimpulan: keterbatasan baseline adalah pengumpulan lintas komoditas (D-128), bukan
penyandian musim; ditulis di findings sebagai pemeriksaan kepekaan.

### D-130 — Danen mengambil alih jalur B (Ardell) dan C (Abi); makalah & video ditunda · FINAL · 2026-11-23 · Danen
Keputusan Danen (2026-11-23): semua WP dan file milik Ardell (WP-07, 15–17, 19, 20, 23–26, 31, 32) dan Abi (WP-33, 34, 35) dikerjakan
Danen. Fokus sampai pembekuan hasil: penyelesaian project (perbaikan U106, `results/findings.md`, app, audit klaim teks app & findings,
paket juri G7, bundle). Makalah PDF, video, dan unggah submission ditunda. Dampak: kolom PIC di papan WORKPLAN = "Danen ← Ardell/Abi";
aturan kepemilikan file (PEMBAGIAN_TUGAS §3, CLAUDE.md §3.0) tidak lagi membatasi Danen; handoff terbuka ke Ardell/Abi menjadi daftar kerja
Danen (isinya tidak ditulis ulang). Mengganti D-105 untuk sisa proyek.

### D-129 — Inferensi nasional terkalibrasi plasebo sebagai tambahan (bootstrap blok menarik β ke nol) · FINAL · 2026-11-23 (WP-13) · Danen
TAMBAHAN PASCA-G6, tidak praregistrasi; bukan deviasi karena interval resmi `profiles` (METHODS M1.5) dan semua uji konfirmatori tidak
berubah. Temuan: blok 13 minggu lebih pendek dari jendela LP (h + L + 2 = 14 minggu pada h 8), sehingga hampir setiap jendela memotong
batas blok dan kaitan penggerak–harga masa depan terputus. Rerata replikasi bootstrap / estimasi nasional (median `boot_ratio`) 0,57 /
0,35 / 0,35 pada h 4 / 8 / 12; contoh daging ayam β_e(8) −1,67 vs rerata replikasi −1,17 → persentil −2,62..0,06. Interval resmi jadi
konservatif berlebih (negatif palsu), sedangkan SE cluster minggu sendiri terlalu sempit (plasebo nasional |t| > 1,96 pada 8,1%).
Diputuskan (keputusan Danen): artefak baru `national_calibrated` (`evaluation/calibration.py`, ditulis `task3`) dengan statistik t
dikalibrasi terhadap plasebo geser-melingkar yang sudah ada (`placebo_stats`, sel yang sama), mengikuti D-127: crit = max(z, statistik
urutan |t*| yang setara p plasebo < α), interval ±crit·SE; p = max(p plasebo, p normal) agar p < α ⇔ interval tidak memuat nol
(pelajaran U106); q BH atas 48 sel. Ditolak: (a) mengganti interval resmi = deviasi setelah melihat hasil; (b) bootstrap dengan blok
lebih panjang/bootstrap dasar = perlu jalan ulang Task 1 (± 2 jam) dan blok tetap memotong jendela h 12; bootstrap dasar justru
memberi 14/48 sel karena distribusinya tidak terpusat. Hasil: 7 sel interval tidak memuat nol (resmi 3), 4 lolos q < 0,05 (daging ayam
β_e(4), gula β_e(4), minyak goreng ω(8), ω(12)). Penulisan: interval resmi tetap dikutip lebih dulu; `national_calibrated` sebagai analisis
kepekaan inferensi; gula β_e(4) wajib disertai catatan tidak tahan Tier 1. U107.

### D-128 — Task 4: spesifikasi ridge gabungan dipertahankan; ridge per komoditas sebagai diagnostik · FINAL (teknis) · 2026-11-23 (WP-27) · Danen
Evaluasi `forecast_preds` asli: M2/M1 MAE 1,014 (h 4) dan 1,017 (h 8), terburuk pada komoditas diatur (daging sapi 1,30, gula 1,13, beras
1,11 pada h 8); H5 tidak didukung (1,12 kedua jalur, Holm 1,0). M1 dan M2 adalah satu ridge untuk 10 komoditas × 337 seri tanpa identitas
komoditas (sesuai proposal: identitas baru di M3), sehingga koefisien kurs adalah rerata lintas komoditas. Diagnostik ad hoc ridge per
komoditas pada origin dan fitur yang sama: M2/M1 1,011 / 1,018, H5 1,18 / 1,12, Holm 1,0 → kesimpulan tidak berubah. Diputuskan: hasil
praregistrasi (ridge gabungan) tetap utama; mengganti model setelah melihat hasil H5 akan menjadi jalur bercabang. Diagnostik tidak menjadi
artefak; boleh disebut di makalah sebagai pemeriksaan kepekaan tanpa angka utama. Catatan: `M2_nofx` = fitur M1 → ablation = −(M2 − M1).

### D-127 — Kalibrasi plasebo untuk interval E2 dan interval laporan H2 · FINAL (teknis) · 2026-11-23 (WP-22, WP-13) · Danen
Audit artefak asli menemukan positif palsu dari SE cluster minggu yang terlalu sempit. (1) E2 `regime_profiles`: semua regresor LP
bervariasi per minggu, jadi rezim ± 70 minggu dengan ± 40 regresor hampir tanpa derajat bebas. 26% sel (39% pada rezim 52–104 minggu)
tampak tidak memuat nol dengan ±1,96·SE, dan tandanya berbalik antar rezim. Perbaikan: interval = estimasi ± crit·SE, crit =
max(1,96; persentil 95 |t*|), t* = estimasi/SE rezim yang sama di bawah R = `inference.placebo_R` (499) geser-melingkar de & dw
(`inference._rolled`, ≥ 52 minggu, RNG seed + 2401). Ditambah `p_placebo` (1 + #|t*| ≥ |t|)/(1 + R) dan `q_fdr` BH atas semua baris
(deskriptif). Paralel joblib (kini dependensi eksplisit di pyproject; ± 9 menit lokal). Ditolak: panjang rezim minimum (butuh kunci
params baru = DEVIASI, dan tidak memperbaiki SE) serta t dengan df = G − k (koreksi terlalu kecil: crit median plasebo 3,09).
(2) H2 `asymmetry`: `ci_low/ci_high` kini = yang lebih lebar dari Wald dan persentil bootstrap (aturan `inference.bootstrap_ci`, yang
sudah dipakai `profiles`), karena plasebo nasional |t| > 1,96 pada 8,1% replikasi. Interval Wald tetap di `wald_ci_low/high`; uji
konfirmatori dan p tetap Wald seperti praregistrasi → bukan DEVIASI PRAREGISTRASI. Kolom aditif `ci_excludes_zero`.
Hasil data asli: E2 sel tidak memuat nol 38 → 15 dari 145, q min 0,145; H2 0 sel tidak memuat nol (bawang putih h8 −10,2..3,1).

### D-126 — Struktur tertanam ditanam sebelum penyusutan EB (perbaikan U105) · FINAL (teknis) · 2026-11-22 (WP-21) · Danen
Versi D-112 menanam δ pada matriks plasebo "mentah" yang ternyata sudah tersusut EB per replikasi (`replicate_feature_matrices(...,
standardize=False)`). Pada data asli 42% kolom konstan per replikasi (τ² = 0) dan median sd 0,005, sehingga δ = 0,1 pun dipulihkan 100%:
batas deteksi terlalu optimistis. Perbaikan: `planted.deviation_matrices` mengambil deviasi provinsi MENTAH dan SE per replikasi plasebo;
δ ditanam di sana, lalu `planted.shrink_matrix` (τ² DL + eb_shrink per kolom, sama persis dengan matriks fitur data asli; selisih 0,0 pada
data asli) dan z-score; ambang plasebo dihitung dari replikasi yang diproses sama (0,196 = ambang `select_k`). Parameter (δ grid, k_true,
200 replikasi, ARI 0,8) tidak berubah → bukan DEVIASI PRAREGISTRASI. Ditolak: menanam setelah z-score (mengabaikan EB) dan memperluas
grid δ (parameter beku). Hasil data asli: recovery δ 0,1 = 0,43 (k = 2) / 0,13 (k = 3); δ 0,2 = 0,995 / 0,965; δ ≥ 0,3 = 1,0 → batas
deteksi δ = 0,2. Karena δ seragam per fitur, deteksi didorong fitur yang presisi (W dan R gula/daging sapi/minyak goreng).
Tes sintetis disesuaikan ke derau sd 0,2 (dengan sd 0,3 recovery δ 0,5 hanya 0,45 karena EB mengenolkan kolom τ² = 0).
### D-204 — Checkpoint & resume bootstrap/plasebo Task 1 · FINAL (teknis) · 2026-11-21 (WP-16) · Ardell
`joint_bootstrap` dan `circular_placebo` menerima `done` (hasil run sebelumnya) dan `checkpoint` (dipanggil tiap 25 replikasi baru). Indeks minggu/pergeseran tetap diundi ulang dengan seed yang sama untuk SEMUA replikasi dan hanya rep belum selesai yang dihitung, sehingga hasil run yang dilanjutkan identik dengan run tanpa putus (tes). `task1.run` menarik `boot_replicates`/`placebo_stats` dari Drive tim, melanjutkan bila ada, dan menyimpan checkpoint + push tiap 25 replikasi (menjawab `01` ± 1,5–2 jam tanpa checkpoint). Peringatan: artefak parsial lama dari konfigurasi/kode berbeda harus dihapus. Tidak mengubah hasil; bukan deviasi praregistrasi.

### D-203 — Meta-regresi provinsi dan interaksi FE: konvensi teknis · FINAL (teknis) · 2026-11-21 (WP-23, WP-24) · Ardell
(1) Meta-regresi per (komoditas, h ∈ key_horizons) dan gabungan (commodity='ALL', intersep per komoditas, klaster = provinsi) pada δ tanpa susut, driver e; τ² = momen DerSimonian-Laird terampat, bobot 1/(s²+τ²). Z(r) di-z-score (koefisien = Δ respons per 1 SD fitur); fitur dengan nilai kosong dibuang (rice_sufficiency, n_kota sampai U14/U15). (2) SE = CR2 Bell–McCaffrey pada regresi terboboti (df = G − p, t); interval akhir = yang lebih lebar antara CR2 dan persentil 2,5/97,5 koefisien dari regresi ulang tiap replikasi `boot_replicates` (δ dan se replikasi). Jackknife = lepas satu provinsi. (3) H3 (ln_dist_hub, h = 4): p satu sisi H1 b < 0; semua baris lain dua sisi. (4) Interaksi FE: y^(h) pada FE komoditas×minggu dan komoditas×provinsi (alternating projection), regresor Δe_t × Z(r), SE cluster minggu; jackknife tidak dihitung; ringan dan dapat dipotong (D-014). Bukan deviasi praregistrasi.

### D-202 — Clustering provinsi, stabilitas, dan pembanding partisi: konvensi teknis · FINAL (teknis) · 2026-11-21 (WP-19, WP-20) · Ardell
(1) Fitur = R (semua komoditas fokus) dan W (hanya yang berpadanan harga dunia) pada `clustering.feature_horizons`, dari `response_features` provinsi (respons nasional + δ tersusut); sel kosong diisi rerata kolom lalu z-score per kolom (kolom konstan → 0). (2) Matriks replikasi memakai δ tersusut EB per replikasi (komponen nasional konstan antar provinsi, hilang setelah z-score) dan membutuhkan kolom `se`; `standardize=False` untuk uji struktur tertanam (D-112). (3) `select_k` memakai aturan yang sama dengan `planted.best_silhouette` (Ward Euclidean, k ≥ 2, `np.nanpercentile` pada `silhouette_placebo_pct`); satu baris per k plus baris k=1 (`accepted` = tidak ada k ≥ 2 lolos). (4) Ward: label dinomori menurut kemunculan pertama agar deterministik. (5) Stabilitas: ko-asignasi penuh 34×34; Jaccard klaster asli = rerata atas replikasi dari Jaccard maksimum terhadap klaster replikasi (Hennig 2007); weak < `jaccard_weak`; K-Means ditulis sebagai method='kmeans' (jaccard NaN) dengan ARI vs Ward. (6) Pembanding partisi: zona HET beras, Jawa/luar Jawa, 7 wilayah (tambahan), dan tersil n_kota bila ada (U15). Positif palsu seleksi k ≈ 5% menurut persentil (uji: 1 dari 12 seed pada data tanpa struktur). Bukan deviasi praregistrasi.

### D-201 — Bootstrap, plasebo, EB, dan fitur respons: konvensi teknis · FINAL (teknis) · 2026-11-21 (WP-15, WP-16, WP-17) · Ardell
(1) Deviasi provinsi diestimasi per provinsi (satu unit) pada harga ter-demean lintas provinsi eligible, memakai desain LP nasional lewat `lp._design_parts/_design_arrays/_fit_arrays`; driver e dan w; normalisasi Σ_r δ = 0 dengan mengurangi rerata lintas provinsi. (2) Bootstrap blok meresampel SELISIH (Δp tiap seri, Δe, Δb, Δw) dan kalender di minggu periode dengan satu vektor indeks; level dibangun ulang dengan cumsum (meresampel level membuat lompatan palsu di sambungan blok); buffer penggerak sebelum periode tetap. `world` ikut di-resample dengan indeks yang sama (estimator menerima `world_b`; sebelumnya closure memakai harga dunia asli). Estimator replikasi = nasional + deviasi provinsi pada `key_horizons`. (3) Jadwal komoditas: replikasi ≤ `bootstrap_B_nonfocus` memakai semua komoditas, sesudahnya hanya komoditas fokus (aturan runtime > 30 menit). RNG seed + 1601 (bootstrap), + 1602 (plasebo). (4) Plasebo: np.roll de & dw atas seluruh grid penggerak (s ∈ [52, T−52]), harga tidak digeser, log_e dan de_pos/de_neg diturunkan ulang. (5) CI bootstrap = persentil 2,5/97,5 per sel; CI = yang lebih lebar, tidak pernah menyempit; PT hanya persentil. (6) EB: se tersusut = sqrt(w·s² + (1−w)²·Var(μ)); τ² DL vs REML dicetak sebagai cek. (7) Fitur respons: provinsi = respons nasional + δ tersusut (se gabungan tanpa kovarians); t_half = h terkecil dengan respons ≥ 50% maksimum bila CI di h maksimum tidak memuat nol. Bukan deviasi praregistrasi.

### D-200 — Aturan tabel referensi WP-07 · FINAL · 2026-11-20 (WP-07) · Ardell
(1) `imported_input_ordinal`: jalur `imported_input` = 2, selain itu 0; nilai 1 belum dipakai (tidak ada dasar data untuk "rendah"). (2) Rasio impor FAOSTAT
= rerata tahunan impor/(produksi+impor−ekspor) pada `association.import_ratio_years` [2018, 2023], kuantitas item dijumlahkan dulu; bawang putih tanpa FAOSTAT
memakai impor BPS/Comtrade / (produksi ATAP + impor), ekspor diabaikan. (3) `confidence` concordance: high = padanan langsung; medium = komposit Pink Sheet
atau item FAOSTAT dipakai >1 komoditas; low = tanpa padanan. (4) Regulasi: `end_date` hanya dari rentang eksplisit (tidak disimpulkan dari regulasi pengganti);
`verification` ∈ verified/partial/confirmed/unverified, tanggal tak terverifikasi = unverified; baris Bapanas hanya yang bertanggal & belum tercakup tabel tim,
selalu unverified (jendela setting panel, bukan tanggal hukum); daftar komoditas dalam satu regulasi dipecah per komoditas (nilai NaN). (5) `rice_sufficiency` memakai
tahun terbaru yang ada di padi, konsumsi, penduduk, dan faktor GKG; NaN bila penduduk/faktor belum ada. Alternatif ditolak: menebak tanggal berlaku dari regulasi
pengganti dan titik tengah untuk rentang HAP (menyembunyikan ketidakpastian). Tambahan `params.association.import_ratio_years` sebelum G6.
