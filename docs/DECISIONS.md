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
