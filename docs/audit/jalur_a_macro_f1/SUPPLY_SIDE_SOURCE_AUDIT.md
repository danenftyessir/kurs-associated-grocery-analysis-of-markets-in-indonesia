# Audit Ulang Sumber Pasokan & Kejadian (Workstream C)

Tanggal: 2026-11-26 · Keputusan: D-165 · Lanjutan [D-159](../20261126_pasokan_fisik.md) dan [D-160](../20261126_sumber_baru.md). Pemeriksaan baca-saja
(halaman publik, katalog data, tabel di repo); tidak ada login, tidak ada unduhan berkas sumber. Sumber yang sudah ditolak (SIJAGUNG, SPORA, PIBC,
CFSv2, cuaca NASA POWER, impor BPS bulanan, harga grosir/produsen PIHPS, kota PIHPS) **tidak diulang** karena tidak ada sumber atau mekanisme baru.

Gerbang: G1 riwayat mencakup dev (latih ≥ 2020 + nilai 2021–2023), G2 waktu ketersediaan dapat ditetapkan (termasuk vintage), G3 independen
dari harga yang dipakai C1t, G4 cakupan dapat memengaruhi macro F1 keseluruhan, G5 sinyal arah nasional tambahan walk-forward (layar
[GDELT_PILOT.md](GDELT_PILOT.md) §4). Gagal satu gerbang → tidak dimodelkan.

## 1. Ringkasan

| # | Sumber | Mekanisme | G1 | G2 | G3 | G4 | G5 | Status |
|---|---|---|---|---|---|---|---|---|
| C1 | **SP2KP stok & pasokan mingguan** (Kemendag) | stok pasar → pasokan jangka pendek | ? | ? | ✓ | ✓ (semua komoditas) | – | **BLOCKED** `[HUMAN]` — area admin berlogin; spesifikasi permintaan di D-159 §2 (U112). Tidak berubah |
| C2 | **Proyeksi Neraca Pangan Nasional** (Bapanas; dahulu "Prognosa") | perkiraan resmi ketersediaan − kebutuhan bulanan per komoditas (stok awal, produksi, impor, ekspor, kebutuhan) | ✗ untuk vintage: katalog hanya memuat versi "Tahun 2022 Final", "Tahun 2023 Final (+Revisi 1)", lalu **update bulanan sejak Sept 2024** | ✗ untuk 2021–2023: versi "Final/Revisi" disusun sesudah tahun berjalan (ex-post); ✓ untuk vintage bulanan 2024+ (bertanggal update) | ✓ | ✓ (beras, jagung, bawang, cabai, daging, gula, minyak goreng) | – | **BLOCKED** — semua dataset berstatus *Terbatas*; vintage dev tidak ada (sebagian tabel bulanan 2023 hanya di PDF laporan bulanan Dit. Ketersediaan Pangan). Hanya cocok untuk **evaluasi prospektif** bila akses diberikan |
| C3 | **EWS cabai & bawang merah / luas tanam hortikultura** (Kementan Ditjen Hortikultura) | luas tanam 2,5–4 bulan lalu menentukan panen dalam horizon (mekanisme berbeda dari cuaca yang tertutup di D-161) | ? (EWS sejak ≥ 2020 menurut siaran pers) | ? (tidak ada portal publik; laporan per periode, mis. Feb–Apr 2023, hanya salinan pihak ketiga) | ✓ | sebagian (cabai merah, cabai rawit, bawang merah ≈ 30% baris) | – | **BLOCKED** `[HUMAN]` — permintaan data luas tanam & prakiraan EWS per provinsi per bulan beserta tanggal rilis |
| C4 | **Tanggal pengumuman kebijakan harga** (HET/HAP/HAP konsumen; `data/reference/regulation.csv`) | penyesuaian harga mengantisipasi acuan baru | ✓ | sebagian (tanggal penetapan; tanggal pengumuman ≠ tanggal efektif tidak tercatat) | ✓ | **✗**: 11 peristiwa komoditas di dev (8 pada Okt–Des 2022) → ≤ 3% minggu komoditas tersentuh | – | **REJECTED** (G4; fitur regulasi juga gagal di D-146) |
| C5 | **Perubahan harga BBM bersubsidi** | ongkos angkut | ✓ | ✓ (tanggal pengumuman publik) | ✓ | ✗: 1 peristiwa nasional di dev (3 Sep 2022) | ✗ tidak dapat diuji (n = 1) | **REJECTED** |
| C6 | **BNPB DIBI kejadian bencana** | gangguan produksi/angkut di sentra | ✓ | sebagian (tanggal kejadian saja; verifikasi triwulanan, dampak direvisi) | ✓ | ? | – | **REJECTED** (prioritas): server pulih (HTTP 200, 2026-11-26), tetapi bencana dominan (banjir, longsor, cuaca ekstrem) adalah subset cuaca ekstrem yang mekanismenya tertutup oleh oracle D-161 (hujan terealisasi termasuk hujan harian maks gagal); bencana non-cuaca terlalu jarang |
| C7 | **Google Trends** ("harga cabai", dst.) | perhatian konsumen | ✓ | ✗ (nilai disampel & dinormalisasi ulang per permintaan → tidak reproduktif; akses tidak resmi) | ✗ (bereaksi terhadap harga) | ✓ | – | **REJECTED** |
| C8 | **Indeks vegetasi satelit (NDVI MODIS/Sentinel)** di sentra produksi | kondisi tanaman → panen | ✓ (2000+) | ✓ (komposit 16 hari, lag rilis diketahui) | ✓ | sebagian (padi, hortikultura; piksel campuran) | – | **BLOCKED** `[HUMAN]` (akun NASA Earthdata/Google Earth Engine); prior rendah: sebagian besar variasi kondisi tanaman digerakkan cuaca (D-157, D-161) |
| C9 | **Stok Bulog / realisasi SPHP & bansos beras** | intervensi stabilisasi | sebagian (berita & laporan; data portal *Terbatas*) | sebagian | ✓ | ✗: beras saja; informasi beras sempurna ≤ +0,007 macro F1 (D-157) | – | **REJECTED** (G4) |
| C10 | **Gangguan pelabuhan/penyeberangan** (ASDP, cuaca maritim) | distribusi antarpulau | ✗ (tidak ada seri terstruktur publik) | – | ✓ | ? | – | **REJECTED** (tanpa sumber); peristiwa semacam ini tercakup kategori "gangguan" GDELT (Workstream B) |

**Keputusan Workstream C:** tidak ada sumber baru yang lolos G1–G4 untuk periode pengembangan → **tidak ada modeling**. Dua kandidat dengan
mekanisme baru yang paling masuk akal (C2 Proyeksi Neraca Pangan, C3 luas tanam/EWS hortikultura) tertutup oleh **akses** (status *Terbatas* /
tanpa portal), bukan oleh bukti sinyal.

## 2. Catatan per kandidat

**C2 Proyeksi Neraca Pangan (Bapanas).** Katalog `data.badanpangan.go.id/catalogapplications` (diperiksa 2026-11-26) memuat ± 30 dataset
"Proyeksi Neraca Pangan Nasional" (update bulanan Sept 2024 – Nov 2026; versi "Tahun 2022 Final", "Tahun 2023 Final", "Tahun 2023 Final Revisi 1"),
semuanya berakses **Terbatas**; dataset terkait "Jumlah Stok Pangan" dan "Jumlah Cadangan Pangan Pemerintah Daerah" juga Terbatas. Rilis bulanan
B+1/B+2 dengan tanggal update → G2 dapat dipenuhi **untuk vintage 2024+**. Untuk dev, tabel proyeksi bulanan 2023 hanya ada sebagai lampiran PDF
laporan bulanan Dit. Ketersediaan Pangan (mis. update 10 Jan 2023, update April 2023), tidak lengkap per bulan; 2021–2022 hanya angka
tahunan/final di buletin Kementan. Karena itu tidak dapat dipakai memilih model di dev (pelajaran D-149: fitur yang hanya ada di test tidak dapat
dipilih). Jalur yang sah: permintaan akses (PPID Bapanas) → evaluasi **prospektif** dengan protokol beku, seperti prediksi maju D-152.

**C3 Luas tanam & EWS hortikultura (Kementan).** EWS memprediksi produksi, kebutuhan, dan surplus/defisit cabai & bawang merah 3 bulan ke depan
per provinsi, dengan data dari tingkat kecamatan. Mekanisme ini **berbeda** dari cuaca: D-161 menunjukkan cuaca 1–8 minggu ke depan tidak menambah
informasi, tetapi panen dalam horizon ditentukan keputusan tanam 2,5–4 bulan sebelumnya. Tidak ada seri publik; siaran pers hanya angka nasional
triwulanan. Permintaan data: luas tanam bulanan per provinsi 2018+ & laporan EWS bertanggal.

**C4/C5 Kebijakan & BBM.** Dihitung dari `data/reference/regulation.csv` (`regimes.regulation_changes`): 11 perubahan acuan harga konsumen
komoditas di dev (Perbadan 11/2022 untuk 6 komoditas pada 2022-12-19, Perbadan 5/2022 untuk ayam & telur 2022-10-05, Permendag minyak goreng
3×, Perbadan 7/2023 beras). Peristiwa sejarang ini tidak dapat menggerakkan macro F1 keseluruhan dan tidak dapat diuji walk-forward.

## 3. Rekomendasi Workstream C

1. Permintaan data resmi digabung dalam satu surat (`[HUMAN]`, U112): SP2KP stok mingguan (D-159 §2) + Bapanas Proyeksi Neraca Pangan (semua
   vintage bulanan, tanggal update) + Kementan luas tanam & EWS hortikultura (bulanan per provinsi, tanggal rilis).
2. Untuk sumber yang hanya punya vintage 2024+: protokol prospektif beku (fitur, aturan, hash) sebelum data diterima; tanpa backfill.
3. Tidak melanjutkan C4–C10.
