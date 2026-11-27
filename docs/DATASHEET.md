# Datasheet — Dataset turunan KAGAMI

Dokumen ini menjelaskan **dataset turunan** yang dibangun proyek, dengan format *datasheet for datasets*. Sumber mentah,
format, dan keanehannya ada di [DATASETS.md](DATASETS.md). Kontrak kolom setiap artefak ada di `src/utils/artifacts.py`
(salinan tabelnya: [ARCHITECTURE.md](ARCHITECTURE.md) §5).

## 1. Motivasi

- **Tujuan.** Menyediakan panel harga pangan eceran per provinsi yang dapat dihubungkan, minggu demi minggu dan tanpa kebocoran
  waktu, dengan kurs IDR/USD, harga dunia padanan dalam rupiah, kebijakan harga acuan, eksposur impor, dan karakteristik provinsi.
- **Celah yang diisi.** Sumber publik tersedia terpisah, dengan frekuensi, ejaan provinsi, satuan, dan kode komoditas yang
  berbeda. PIHPS harian tidak menandai minggu tanpa perubahan harga, tidak memisahkan data hilang dari harga kaku, dan memuat
  urutan baris yang tidak dapat diandalkan (D-022). Kurs dan harga dunia tidak memiliki tanggal ketersediaan. Riwayat HET/HAP
  tersebar di peraturan dengan tanggal yang tidak selalu terverifikasi.
- **Pembuat.** Tim KAGAMI (INDONERIS 2026). Dataset turunan kami dibangun dari PIHPS (Bank Indonesia) dan sumber publik lain.

## 2. Komposisi

| Komponen | Isi | Ukuran | Dikirim ke juri |
|---|---|---|---|
| `panel_weekly` | log harga eceran mingguan, 34 provinsi × 10 komoditas × 464 minggu (2018-01-01..2026-11-16), varian representatif beku (D-011), **status sel** (observed / carry_forward / short / missing, D-021), jumlah hari teramati, porsi carry-forward | 157.760 sel | ya (izin BI, D-104) |
| `panel_weekly_region` | indeks log 7 wilayah relatif minggu pertama, rerata dua arah yang tahan perubahan komposisi (D-106) | 32.480 baris | ya |
| `eligibility` | kelayakan setiap seri provinsi × komoditas (aturan hilang, celah, cakupan tahunan) | 340 seri, 337 layak | ya |
| `drivers_weekly` | log JISDOR & perubahan (± depresiasi/apresiasi), Brent, indeks dolar, minggu Idulfitri, bulan; minggu libur fixing diisi (D-025) | 2017-01-02..2026-11-16 | ya |
| `world_prices_weekly` | harga dunia padanan per komoditas dalam rupiah (Pink Sheet × JISDOR bulanan), komposit pakan 0,6 jagung + 0,4 bungkil kedelai, **`available_at`** (hari kerja ke-2 bulan berikutnya) | 3.096 baris | ya |
| `episodes`, `fx_variation` | 13 episode depresiasi (Σ Δlog kurs 8 minggu ≥ 3%) dan variasi kurs per tahun 2018–2026 + total | 13 / 10 baris | ya |
| `concordance` | PIHPS ↔ HS ↔ Pink Sheet ↔ FAOSTAT per komoditas, dengan tingkat keyakinan | 10 baris | ya |
| `exposure` | rasio impor langsung, jalur eksposur, ordinal input impor, sumber setiap angka | 10 baris | ya |
| `regulation` | riwayat HET/HAP/HPP per komoditas × instrumen × zona × periode, dengan **status verifikasi tanggal**; tanggal yang tidak dapat diverifikasi ditandai `unverified`, tidak ditebak | 72 baris | ya |
| `province_features` | jarak ke hub logistik terdekat, kecukupan produksi beras 2025, jumlah kota sampel PIHPS | 34 baris | ya |
| `region_crosswalk`, `province_aliases` | kerangka 34 provinsi, 7 wilayah, zona HET beras, alias ejaan BPS/Bapanas, pemekaran Papua | 34 / 13 baris | ya |

Semua tabel memakai kunci yang sama: `week` (Senin ISO, D-020), `province_id` (1–34, urutan PIHPS), `commodity` (id internal).

## 3. Proses pengumpulan

- Snapshot mentah diambil 2026-11-18..20 dan tidak pernah ditimpa. sha256 setiap file ada di `data/raw/checksums.csv`, dan setiap
  run mencatat sidik jari snapshot (`raw:<12 heks>`) di `logs/`.
- Tabel buatan tim (`regulation`, `concordance`, `jarak_hub`, faktor GKG, `n_kota`) disusun manual dari peraturan, situs resmi, dan
  rilis BPS. Setiap baris memuat sumber atau URL.
- Pemeriksaan kualitas (`stage0_report`): lonjakan satu hari ditandai, tidak dihapus (59 hari); total impor bulanan vs tahunan BPS
  cocok 241/241; tumpang tindih Comtrade–BPS 2023 cocok 14/15 kode; bias PIHPS vs Panel Harga Bapanas dilaporkan.

## 4. Praproses

- **Mingguan.** Harga mingguan = rerata hari teramati. Hari tanpa laporan tidak diisi. Status sel membedakan harga yang tidak
  berubah (carry-forward, kekakuan nyata untuk komoditas diatur: beras 92%) dari data hilang (1,0%).
- **Varian.** Satu varian representatif per komoditas, dipilih dari prefiks nama, bukan urutan baris. Varian dibekukan di G6.
- **As-of.** Harga dunia dan impor bulanan diberi tanggal ketersediaan, sehingga fitur prediksi pada minggu t hanya memakai
  informasi yang sudah terbit pada t. Kebocoran diuji pada setiap origin (D-147, D-152).
- Seluruh praproses dapat diulang: `python -m kagami stage0` (± 27 detik lokal).

## 5. Penggunaan

- **Dipakai untuk.** Analisis asosiasional kepekaan harga terhadap kurs (Task 1–3) dan evaluasi prediksi rolling-origin (Task 4).
- **Cocok untuk.** Studi lain tentang transmisi harga dunia, kebijakan HET/HAP, atau kekakuan harga per provinsi, karena status
  sel dan tanggal regulasi sudah tersedia.
- **Tidak cocok untuk.** Klaim kausal tanpa desain tambahan; analisis di bawah tingkat provinsi (panel kota tidak dikirim, U111);
  nowcasting real-time yang bergantung pada revisi data (vintage PIHPS tidak tersedia, U110).

## 6. Distribusi & hak

- Panel turunan provinsi dan wilayah dikirim atas dasar izin BI yang mencakup redistribusi data turunan (U13, D-104).
- PIHPS mentah, `pihps_daily`, JISDOR, BPS, Comtrade, dan Bapanas tidak dikirim (`redistribute: false`).
- Pink Sheet, FAOSTAT, FRED, dan NASA POWER dikirim sesuai lisensinya. Tabel buatan tim berlisensi CC BY 4.0, kecuali geometri
  provinsi (ODbL, © OpenStreetMap contributors via geoBoundaries).

## 7. Pemeliharaan & keterbatasan

- Kerangka 34 provinsi lama (D-017): provinsi pemekaran Papua digabung ke induknya.
- Pink Sheet merevisi angka historis antarrilis. Snapshot memakai rilis 3 Nov 2026.
- Endpoint unduh PIHPS sama dengan tombol unduh resmi situs (U19, bukti 2026-11-25), tetapi belum dikonfirmasi tertulis oleh BI.
- Pembaruan: jalankan ulang `snapshot` lalu `stage0` pada snapshot baru. Artefak lama tidak ditimpa di `data/raw/`.
