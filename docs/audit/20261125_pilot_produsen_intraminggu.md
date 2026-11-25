# Pilot Informasi Intraminggu & Harga Produsen PIHPS untuk Task 4 Arah (EKSPLORATIF)

Tanggal: 2026-11-25 · Pelaksana: Danen (dengan agent) · Keputusan: D-151 · Lanjutan [pilot grosir](20261125_pilot_grosir.md),
[audit preprocessing](20261125_task4_audit_preprocessing.md), dan roadmap pasca-D-150 (prioritas 1 = harga produsen, prioritas 2 =
informasi intraminggu). Catatan bertanggal (bukan dokumen hidup). Skrip & hasil: [folder lampiran](20261125_pilot_produsen_intraminggu/).

Protokol [`PROTOKOL.md`](20261125_pilot_produsen_intraminggu/PROTOKOL.md) ditulis 2026-11-25 17:36 sebelum fitur dibangun dan sebelum
ada hasil; sha256 `2a5d5ca02916d4249f1317d5408a3dc826791b207badc2f094a9eb9f862c4bee`. Ringkasnya: C1-tuned beku (kolom, `TUNED_HGB`,
seed, threshold 0,5), label & baris evaluasi resmi, seleksi hanya di origin pengembangan (origin + h ≤ 2023-12-31), daftar kandidat
tetap, aturan lolos D-147–D-150 (Δ macro F1 rerata ≥ +0,005, interval berpasangan > 0 di ≥ 1 horizon, Δ ≥ 0 di horizon lain), satu
kandidat per keluarga membuka test sekali. Semua langkah < 1 jam → lokal.

## 0. Ringkasan

| Pertanyaan | Jawaban |
|---|---|
| Pembanding sah? | Ya: `base` = `direction_tuned_preds` C1t, maks \|Δp\| 0 pada 25.259 baris dev dan 24.616 baris test. Evaluator sama dengan D-147–D-150 (`evalx`). |
| A. Informasi intraminggu membantu? | **Di pengembangan ya**, di test **belum terbukti**. `IW_NAT` (6 fitur intraminggu + 2 rerata nasional) dev +0,020 (0,003..0,037) / +0,005 (−0,003..0,012) → lolos, membuka test: **+0,0085 (−0,003..0,024) / +0,0033 (−0,004..0,011)**, q BH 0,28 / 0,30. Macro F1 test 0,686 / 0,683 vs C1-tuned 0,677 / 0,680. |
| B. Harga produsen PIHPS membantu? | **Tidak.** Data diperoleh (atas persetujuan Danen), tetapi semua varian di bawah C1-tuned di pengembangan (−0,006..−0,001, interval memuat nol) → test tidak dibuka. Produsen tidak mendahului eceran; seri berupa tangga mingguan dengan lompatan besar. |
| Perubahan kecil? | `IW_NAT` menaikkan macro F1 kuintil \|y\| terkecil: dev +0,027 / +0,019 (interval > 0), test +0,018 (0,000..0,036) / +0,005 (−0,011..0,021). Produsen ±0,005 tanpa arah. |
| Model terpilih | **Tidak berubah**: C1-tuned (test 0,677 / 0,680). `IW_NAT` = varian eksploratif terbaik sejauh ini, bukan model utama. |

## 1. Keluarga A — informasi intraminggu (`scripts/iw_build.py`, `exp.py`, `ev.py`)

Fitur dari `pihps_daily` (Senin–Jumat minggu origin t saja): `iw_gap` (log hari terakhir − log rerata minggu; identik dengan D-147),
`iw_return` (log terakhir − log pertama), `iw_range`, `iw_vol` (sd Δlog harian, ≥ 2 perubahan), `iw_n_days`, `iw_last_age`
(4 − hari teramati terakhir); `iw_gap_nat`, `iw_return_nat` (rerata komoditas lintas provinsi yang teramati minggu t). Kosong 1,1%
(minggu tanpa hari teramati); `iw_last_age` = 0 pada 95%. Kebocoran: harga harian sesudah akhir minggu origin dirusak → fitur ≤ origin
identik (2022-06-20, 2025-03-24).

| Varian (dev) | Δ h 4 (interval) | Δ h 8 (interval) | Δ kuintil terkecil h 4 / h 8 | Keputusan |
|---|---|---|---|---|
| `IW_REF` = `iw_gap` + `n_days` (D-147, bukan kandidat) | +0,014 (0,004..0,026) | +0,002 (−0,006..0,008) | +0,028 / +0,008 | acuan |
| `IW_FULL` (6 fitur) | +0,015 (0,005..0,026) | +0,002 (−0,005..0,007) | +0,026 / +0,008 | lolos, tidak dipilih |
| `IW_NAT` (+ 2 nasional) | **+0,020 (0,003..0,037)** | +0,005 (−0,003..0,012) | **+0,027 / +0,019** | **lolos → buka test** |

Fitur tambahan di luar `iw_gap` hampir tidak menambah di tingkat provinsi (`IW_FULL` ≈ `IW_REF`); yang menambah adalah versi nasional
(perubahan dalam-minggu yang serentak di banyak provinsi). Per komoditas dev `IW_NAT`: h 4 −0,011 (minyak goreng) .. +0,043 (cabai rawit),
beras +0,037 / +0,018, daging sapi +0,018 / +0,030.

**Test (dibuka sekali, `IW_NAT` saja; `hasil/iw_test_*.csv`):**

| | macro F1 h 4 | macro F1 h 8 | ROC-AUC h 4 / h 8 | porsi prediksi naik h 4 / h 8 |
|---|---|---|---|---|
| C1-tuned | 0,677 (0,652..0,698) | 0,680 (0,653..0,706) | 0,741 / 0,738 | 0,557 / 0,598 |
| `IW_NAT` | 0,686 (0,661..0,709) | 0,683 (0,658..0,708) | 0,758 / 0,746 | 0,560 / 0,594 |
| Selisih (interval, q BH) | +0,0085 (−0,003..0,024), q 0,28 | +0,0033 (−0,004..0,011), q 0,30 | | |

Per komoditas test: h 4 −0,023 (cabai rawit) .. +0,035 (telur); h 8 −0,020 (gula) .. +0,033 (telur); beras +0,021 / +0,029. Arah
selisih sama dengan pengembangan dan dengan `iw_gap` D-147 (+0,004 / +0,005), tetapi interval memuat nol. Test untuk keluarga ini
**tidak bersih**: `iw_gap` sudah dilihat di test pada D-147, jadi hasil ini bukan konfirmasi independen.

## 2. Keluarga B — harga produsen PIHPS

### 2.1 Pengambilan data
Atas persetujuan Danen (2026-11-25): `scripts/fetch_pihps.py` D-150 dengan `price_type_id=4`, 34 provinsi × 105 bulan (2018-03 ..
2026-11-19) = 3.570 permintaan, 0 galat, 1.837 dtk → `data/raw/bi_pihps/pihps_produsen_harian_2018-2026_retrieved_2026-11-25.zip`
(0,4 MB, 34 CSV + `MANIFEST.csv` + `ERRORS.json` kosong, format sama dengan `pihps`). Didaftarkan sebagai sumber opsional
`pihps_producer` (`redistribute: false`). DKI Jakarta kosong (0 baris); NTT berhenti 2023-12-25; Kepri 2026-10-16; awal 2018-03-26
(Jawa Tengah) .. 2018-10-25. Cakupan izin BI (U13) untuk jenis pasar ini & status unduh resmi (U19) tetap `[HUMAN]`.

### 2.2 Bentuk data (`scripts/pr_build.py` → `hasil/pr_coverage.csv`, `hasil/pr_leadlag.csv`)

| Komoditas | provinsi berisi (Jul 2024) | sel berisi 2019+ | median log eceran − produsen | Δprod(t−1)→Δeceran(t) | Δeceran(t−1)→Δprod(t) | arah prod 4 mgg vs eceran +4 / +8 | momentum eceran (baris sama) |
|---|---|---|---|---|---|---|---|
| beras | 28 (26) | 0,77 | 0,17 | 0,057 | 0,062 | 0,630 / 0,631 | 0,624 / 0,625 |
| gula pasir | 11 (10) | 0,25 | 0,14 | 0,113 | 0,129 | 0,595 / 0,571 | 0,692 / 0,668 |
| minyak goreng | 14 (11) | 0,28 | 0,18 | 0,085 | 0,214 | 0,643 / 0,644 | 0,634 / 0,633 |
| daging sapi | 31 (28) | 0,82 | 0,09 | −0,011 | 0,021 | 0,474 / 0,490 | 0,432 / 0,450 |
| daging ayam | 32 (32) | 0,93 | 0,34 | −0,020 | 0,198 | 0,424 / 0,392 | 0,463 / 0,397 |
| telur ayam | 33 (32) | 0,94 | 0,13 | 0,009 | 0,212 | 0,444 / 0,380 | 0,496 / 0,414 |
| bawang merah | 26 (23) | 0,69 | 0,41 | 0,047 | 0,214 | 0,482 / 0,430 | 0,567 / 0,482 |
| bawang putih | 2 (2) | 0,05 | 0,84 | 0,020 | 0,014 | 0,589 / 0,614 | 0,545 / 0,565 |
| cabai merah | 32 (30) | 0,89 | 0,47 | 0,028 | 0,174 | 0,452 / 0,446 | 0,502 / 0,448 |
| cabai rawit | 30 (28) | 0,82 | 0,38 | −0,022 | 0,193 | 0,443 / 0,448 | 0,450 / 0,417 |

- Seri produsen = **tangga mingguan**: 88% minggu hanya satu nilai harian; harga berubah pada 4% hari (34% di hari Senin); setiap
  perubahan besar (median \|Δlog\| cabai 0,22–0,23, bawang merah 0,14, ayam 0,06, beras/gula/sapi ≈ 0,02). Status mingguan
  carry_forward 99–100% karena nilai diulang tiap hari, bukan karena basi.
- **Tidak mendahului eceran**: korelasi Δeceran(t−1)→Δprodusen(t) untuk komoditas segar (ayam, telur, bawang merah, cabai) 0,17–0,21,
  jauh di atas arah sebaliknya (−0,02..0,05); untuk semua komoditas, Δprodusen(t−1)→Δeceran(t) hanya −0,02..0,11. Kesesuaian arah
  produsen 4 minggu dengan label eceran lebih tinggi dari momentum eceran hanya untuk daging sapi (+0,04), bawang putih (+0,04 / +0,05,
  tetapi n 224) dan marginal untuk beras/minyak goreng (+0,006..+0,011); untuk komoditas segar lebih rendah.
- Fitur (tanpa ffill/interpolasi; `pr_age` = minggu sejak harga produsen terakhir): kosong 36% secara umum, 72–95% untuk gula, minyak
  goreng, bawang putih. Kebocoran: produsen & eceran sesudah origin dirusak (+ pola kosong diubah) → fitur ≤ origin identik.

### 2.3 Pilot (`hasil/pr_dev_*.csv`)

| Varian (dev) | Δ h 4 (interval) | Δ h 8 (interval) | Δ kuintil terkecil h 4 / h 8 | Keputusan |
|---|---|---|---|---|
| `PR_DYN` (Δ produsen 1/4/8, volatilitas, umur) | −0,002 (−0,008..0,006) | −0,003 (−0,006..0,001) | −0,004 / +0,003 | tidak |
| `PR_TRANS` (+ selisih eceran–produsen & perubahannya) | −0,003 (−0,008..0,003) | −0,004 (−0,010..0,001) | −0,005 / +0,002 | tidak |
| `PR_ALL` (+ sinyal nasional produsen) | −0,001 (−0,009..0,007) | −0,006 (−0,015..0,002) | +0,005 / +0,002 | tidak |

Per komoditas ±0,02 tanpa pola (beras `PR_ALL` +0,018 / −0,038; daging sapi `PR_DYN` −0,015 / +0,007). Tidak ada kandidat yang lolos →
**test tidak dibuka**.

## 3. Kesimpulan & arah berikutnya

- Dua sumber hulu PIHPS (grosir D-150, produsen D-151) sudah diuji dengan protokol yang sama: keduanya bergerak bersama atau sesudah
  eceran, dan tidak menambah macro F1 di atas C1-tuned. Jalur "harga hulu PIHPS" untuk prediksi arah eceran dapat ditutup.
- Informasi intraminggu adalah satu-satunya sinyal baru yang konsisten positif (dev dan test searah, juga membantu perubahan kecil),
  tetapi besarnya ± +0,003..+0,009 dan belum lolos BH; tidak cukup untuk mengganti model utama sebelum pembekuan 2026-11-27.
- Skor arah ± 0,68 tampaknya mendekati batas informasi harga PIHPS publik (derau label ± 0,01–0,015, D-147). Tuas tersisa di luar
  PIHPS: pasokan/produksi fisik dan cuaca sentra produksi (prioritas 3 roadmap), tidak realistis sebelum pembekuan.
- Bila `IW_NAT` ingin dikonfirmasi, satu-satunya jalan bersih adalah origin baru yang belum pernah dipakai seleksi (data sesudah
  2026-11-19) dengan konfigurasi persis `IW_NAT`; test 2024+ tidak boleh dipakai lagi untuk keluarga ini.
- `src/` hanya bertambah satu entri `LOADERS` (`pihps_producer`); `params.yaml` dan artefak resmi tidak berubah.
