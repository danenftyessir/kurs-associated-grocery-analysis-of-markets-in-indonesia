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
