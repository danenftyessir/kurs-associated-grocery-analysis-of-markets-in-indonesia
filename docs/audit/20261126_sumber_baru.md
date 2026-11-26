# Source Feasibility & Signal Discovery — GDELT, CFSv2, SIJAGUNG/SPORA, BNPB DIBI (D-160, Task 4 arah)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-160 (adendum CFSv2: D-161, §3) · Lanjutan [D-159](20261126_pasokan_fisik.md) atas rancangan Danen:
D-160 adalah **kelayakan sumber & penemuan sinyal**, bukan ronde optimasi model. Lima gerbang Danen: (1) riwayat mencakup origin dev,
(2) waktu ketersediaan dapat ditetapkan, (3) independen dari harga PIHPS, (4) cakupan cukup untuk macro F1 keseluruhan, (5) sinyal arah nasional
**tambahan** di atas konsensus C1-tuned (walk-forward, D-158). Pemeriksaan baca-saja + unduhan yang disetujui Danen (CFSv2 subset, SIJAGUNG/SPORA,
DIBI). Tidak ada modeling provinsi; test 2024+ tidak dipakai. Skrip & hasil: [folder lampiran](20261126_sumber_baru/).

## 0. Ringkasan gerbang

| Sumber | G1 riwayat | G2 ketersediaan | G3 independen | G4 cakupan | G5 sinyal nasional tambahan | Status |
|---|---|---|---|---|---|---|
| **GDELT GKG 2.1** | ✓ arsip 15 menit (v2 sejak 2015) | ✓ `DATE` = batch 15 menit pertama tercatat | ✓ | ? cakupan berita pasokan pangan Indonesia belum terverifikasi | **tidak teruji**: 2018–2023 ≈ 210.000 berkas GKG (± 3 MB zip per 15 menit sekarang) = skala terabyte; jalur praktis hanya BigQuery `gdelt-bq` (akun Google Cloud berbayar) | **BLOCKED** `[HUMAN]` (U113) |
| **NOAA CFSv2 operasional** | ✓ seri waktu per inisialisasi di THREDDS NCEI 2017–2026 (katalog NCEI 2011+) | ✓ inisialisasi 4×/hari, prakiraan tidak direvisi | ✓ | sebagian: hortikultura (32–34% baris), grid ± 1° | **tidak teruji**: layanan subset rusak (NetcdfSubset HTTP 404, OPeNDAP 403 dari backend S3); hanya berkas penuh 42,6 MB per variabel per run → ± 8 GB (byte-range 56 hari pertama) s.d. ± 37 GB untuk run mingguan 2018–2026 (2 variabel) + dekoder GRIB2 (eccodes, belum terpasang) — di luar cakupan unduhan yang disetujui | **BLOCKED** (skala; butuh persetujuan baru / Colab) → diuji lewat Colab di D-161 (§3): G5 gagal, **REJECTED** |
| **SIJAGUNG** (stok & pembelian jagung pabrik pakan) | ✓ 2019-01..2026-08 bulanan, 14 wilayah | sebagian: tabel publik tertinggal ± 3 bulan, tanpa tanggal rilis per nilai → akhir bulan + 90 hari | ✓ | ayam + telur (22–23% baris) | **gagal**: baris |ρ| ≤ 0,11 (q ≥ 0,65); arah nasional increment-only AUC −0,01..−0,21 vs konsensus | **REJECTED** |
| **SPORA** (harga pakan) | ✓ pilihan 2019–2026 | ? | ✓ | ayam + telur | ekspor publik gagal (HTTP 500, memori PHP server habis) untuk rentang penuh **dan** per tahun | **BLOCKED** |
| **BNPB DIBI** | ✓ kejadian per kab/kota per hari 2008+ | sebagian: hanya tanggal kejadian; verifikasi triwulanan; dampak (sawah, jalan) direvisi | ✓ | bergantung lokasi | **tidak teruji**: server tidak tersedia (HTTP 521) saat uji; API dataset tidak diakses (bukan jalur publik) | **BLOCKED** (sementara) |

**Keputusan:** tidak ada sumber yang lolos kelima gerbang → **tidak ada modeling; C1-tuned tetap.** Satu sumber diuji penuh (SIJAGUNG) dan gagal.
Dua kandidat tetap terbuka tetapi butuh keputusan biaya/akses: CFSv2 (unduhan 8–37 GB + eccodes, cocok sebagai job Colab) dan GDELT (BigQuery
dengan batas biaya, `[HUMAN]`). DIBI dapat dicoba ulang bila servernya pulih (hanya hitungan kejadian dengan lag konservatif).

## 1. Temuan per sumber

**GDELT (D-160A).** `lastupdate.txt` 2026-11-26: berkas GKG 15 menit 3,08 MB zip (export 53 KB, mentions 66 KB). GKG `DATE` adalah stempel batch
15 menit saat dokumen pertama diproses → gerbang 2 terpenuhi bila memakai `DATE`, bukan tanggal kejadian di artikel. Isi tematik (tema, lokasi,
sumber) relevan untuk klasifikasi peristiwa pasokan, tetapi volume 2018–2023 tidak praktis diunduh lokal; BigQuery butuh akun berbayar (memindai
kolom tema & lokasi 6 tahun kemungkinan melampaui kuota gratis 1 TB/bulan). Cakupan media lokal Indonesia dan kualitas klasifikasi peristiwa belum
dapat diuji tanpa data. Saran pilot (bila disetujui): kueri BigQuery dengan batas biaya, filter lokasi Indonesia + tema pangan/pertanian/bencana/
transportasi, hitungan harian per komoditas, sampel 100 artikel diperiksa manual sebelum fitur dibuat.

**CFSv2 (D-160B).** THREDDS `model-cfs_v2_for_ts/<tahun>/<bulan>/<hari>/<run>/` berisi 90+ variabel per run (mis. `prate.01.YYYYMMDDHH.daily.grb2`
42,6 MB, `tmax` 34,7 MB, `soilm4` 37,6 MB; last-modified 2024-04-26 = pengarsipan ulang, isi prakiraan tidak berubah). Layanan yang diiklankan
(NetcdfSubset, OPeNDAP) tidak berfungsi; `fileServer` berfungsi dan mendukung byte-range. Catatan mekanisme (risiko sebelum biaya): hujan/suhu
yang **diprakirakan untuk 4–8 minggu ke depan** sebagian besar memengaruhi panen **sesudah** horizon (siklus cabai/bawang 2,5–4 bulan), kecuali
kejadian ekstrem (banjir saat panen, gangguan angkut); cuaca teramati masa lalu yang lebih relevan untuk pasokan dalam horizon sudah gagal di D-157.
Ekspektasi awal rendah; layak diuji hanya bila biaya ekstraksi diterima.

**SIJAGUNG/SPORA (D-160C).** Portal publik `simpakan.ditjenpkh.pertanian.go.id`: SIJAGUNG (pembelian, stok, kecukupan produksi, proyeksi; sejak
2019) dan SPORA (harga & produksi pakan; sejak 2019) dengan tombol Export. SIJAGUNG diunduh (`fetch_pakan.py`, 2 xlsx, 74 KB, MANIFEST sha256)
dan didaftarkan opsional `ditjenpkh_sijagung` + `load_sijagung`. Nasional 92 bulan: stok 0,37–1,35 juta t, kecukupan 25–66 hari, pembelian
0,25–0,87 juta t/bulan, harga Rp3.879–8.215/kg. Uji gerbang 5 (`sij_du.py`, ayam & telur, origin dev): korelasi residual C1t parsial
−0,09..+0,07 (semua q ≥ 0,75); arah nasional increment-only (offset konsensus C1t, walk-forward): AUC 0,709 vs 0,724 (h 4, kecukupan) hingga
0,561 vs 0,770 (h 8, semua fitur) → **tidak ada sinyal tambahan**. SPORA export: halaman galat PHP "Allowed memory size … exhausted" untuk semua
rentang (halaman galat tidak disimpan).

**BNPB DIBI (D-160D).** `dibi.bnpb.go.id` (Apache Superset): > 50.000 kejadian sejak 1815, filter provinsi (38) / kabupaten (513) / kategori /
tahun / bulan, tampilan harian & tabular, unduhan per grafik. Tanggal kejadian ada; waktu laporan pertama tidak terlihat; rapat verifikasi
triwulanan (mis. TW2 2025) dan atribut dampak direvisi → hanya hitungan kejadian (banjir/longsor/cuaca ekstrem) dengan lag konservatif yang
dapat dibela. Saat uji gerbang 5 server mengembalikan HTTP 521; tidak dicoba ulang berulang-ulang.

## 2. Rekomendasi

1. Tutup SIJAGUNG (dan SPORA kecuali export diperbaiki) sebagai fitur Task 4.
2. Bila ingin melanjutkan: (a) **CFSv2 di Colab** — unduh `prate` & `tmax` run mingguan 2018–2026 dengan byte-range 56 hari pertama (± 8 GB),
   dekode dengan eccodes, simpan subset Indonesia ± 50 MB ke Drive; uji gerbang 5 seperti D-158 (hortikultura, bobot produksi ATAP); (b) **GDELT via
   BigQuery** dengan batas biaya — `[HUMAN]` membuat proyek GCP; (c) DIBI dicoba ulang bila server pulih.
3. Ketiganya tetap tunduk pada gerbang 5 (konsensus C1t) sebelum modeling provinsi; ekspektasi CFSv2 rendah (mekanisme), GDELT tidak diketahui.

## 3. Adendum D-161 — CFSv2 diuji lewat Colab (2026-11-26)

Atas persetujuan Danen (rekomendasi 2a). **Ekstraksi** (`colab/kagami_d160_cfsv2.ipynb`, dibangun `colab/build_notebook.py`; pemetaan sel grid
Gaussian T126 → provinsi `colab/build_cell_map.py` → `colab/cfs_cell_province.json`, 182 sel, 10 provinsi kecil memakai sel terdekat ibu kota):
untuk setiap minggu t (Senin 2017-12-25 .. 2026-11-16) run 00Z hari Jumat minggu t (cadangan Kamis, Rabu), byte-range 56 hari pertama `prate` &
`tmax` dari `fileServer` NCEI (± 7 MB per variabel per run; GRIB2 tidak disimpan), dekode JPEG2000 dengan eccodes, rerata sel per provinsi.
Cek grid di Colab: lat0 89,277 (= pemetaan), 224 pesan, jam terakhir 1.344. Mount Drive gagal (menunggu popup OAuth) → output disimpan di
runtime lalu diunduh. Hasil 1.818 dtk: **437/465 minggu** (28 tanpa run = HTTP 404 pada ketiga hari; hanya 3 di periode dev: 2022-06-27,
2023-05-22, 2023-06-19; sisanya 2024-04 .. 2026); 13 run `prate` / 15 run `tmax` hanya 45 hari lengkap (2 di dev) → variabel itu NaN (aturan
mutu ditetapkan sebelum hasil dibaca). Agregat `20261126_sumber_baru/hasil/cfsv2_province_weekly.csv` (14.858 baris) dan `cfsv2_manifest.csv`
(sha256 byte yang dibaca per run); seri harian per provinsi (`cfsv2_parts.zip`, 5,9 MB) tidak di-commit. Bukan sumber terdaftar
(`sources.yaml`): turunan audit yang dapat dibangun ulang dari notebook. **G2:** init Jumat 00Z pada 429 minggu, Kamis 7, Rabu 1 → terbit
sebelum Minggu 00.00 WIB (`available_at` harga minggu t, D-155).

**Uji** (`scripts/cfs_du.py`, protokol dibekukan sebelum ekstraksi selesai; kode diuji dulu pada data sintetis): anomali terhadap
klimatologi *prakiraan* init ≤ 2020-12-31 (± 14 hari), nasional tertimbang produksi ATAP (aturan D-157) untuk cabai merah, cabai rawit,
bawang merah; arah nasional increment-only di atas konsensus C1t, walk-forward, minggu 2021–2023; lolos bila satu set ΔAUC ≥ +0,01 di kedua
horizon, batas bawah interval > 0 di ≥ 1 horizon, q < 0,05. **Oracle** = set yang sama dari cuaca TERREALISASI NASA POWER pada jendela
prakiraan (bukan kandidat; batas atas mekanisme).

Skill prakiraan nyata: korelasi anomali CFSv2 vs terealisasi (nasional tertimbang produksi) hujan hari 1–28 0,42–0,55, hari 29–56 0,25–0,37,
suhu maks hari 1–28 0,58–0,61 (median per provinsi 0,38 / 0,23 / 0,34).

| Set (ΔAUC vs konsensus, interval bootstrap blok 13 minggu) | CFSv2 h 4 | CFSv2 h 8 | Oracle h 4 | Oracle h 8 |
|---|---|---|---|---|
| R1 hujan hari 1–28 | −0,014 (−0,026..−0,002) | −0,003 (−0,014..+0,015) | −0,028 (−0,063..+0,002) | −0,013 (−0,047..+0,021) |
| R2 hujan hari 29–56 | +0,006 (−0,022..+0,058) | −0,000 (−0,024..+0,045) | −0,019 (−0,050..+0,003) | −0,017 (−0,039..+0,001) |
| RX hujan 1–56 + hujan harian maks | −0,013 (−0,037..+0,021) | −0,005 (−0,027..+0,032) | −0,040 (−0,088..−0,001) | −0,029 (−0,068..+0,015) |
| T suhu maks 1–28 & 29–56 | −0,003 (−0,028..+0,031) | +0,005 (−0,041..+0,044) | −0,027 (−0,068..+0,001) | −0,015 (−0,036..−0,001) |
| ALL (6) | −0,026 (−0,062..+0,040) | −0,029 (−0,088..+0,027) | −0,081 (−0,141..−0,012) | −0,071 (−0,120..−0,005) |

AUC konsensus 0,707 (h 4) / 0,714 (h 8); q BH ≥ 0,105 untuk semua sel CFSv2 dan oracle. Baris provinsi (deskriptif): hujan nasional hari
1–56 / 29–56 berkorelasi dengan residual C1t ρ 0,13–0,16 mentah (q ≥ 0,22) dan 0,12–0,14 parsial (q ≥ 0,27); fitur lokal |ρ| ≤ 0,10. Korelasi
pooled sebesar ini adalah jenis yang di D-157 tetap memperburuk skor walk-forward (`docs/EKSPERIMEN.md` §3).

**Keputusan D-161:** CFSv2 gagal gerbang 5 → **REJECTED, tanpa modeling; C1-tuned tetap.** Oracle juga gagal: bahkan cuaca yang benar-benar
terjadi 1–8 minggu ke depan di sentra hortikultura tidak menambah informasi arah nasional di atas konsensus C1t, jadi kegagalan bukan soal skill
prakiraan (yang nyata) melainkan mekanisme (konsisten dengan catatan §1 dan D-157). U113 tinggal GDELT. Aturan baru `docs/EKSPERIMEN.md` §3:
sumber prakiraan diuji oracle-nya dulu sebelum biaya ekstraksi. Batasan: model increment-only linear; hanya 3 komoditas hortikultura (G4);
klimatologi prakiraan hanya 3 tahun (157 run); NASA POWER sebagai oracle punya galatnya sendiri.
