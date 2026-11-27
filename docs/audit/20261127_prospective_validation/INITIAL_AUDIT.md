# Audit awal validasi prospektif — prediksi maju beku & evaluator

Tanggal: 2026-11-27 (04.00–05.00 WIB) · Danen (agent) · baca-saja; tidak ada target maju yang dibaca, tidak ada prediksi yang dibuat ulang.
Lanjutan [gabungan audit](../20261127_gabungan_audit.md) §16–§17, [D-152](../20261125_iw_validasi/PROTOKOL.md), [D-158](../20261126_nasional_lokal/PROTOKOL_I2.md),
[Jalur A](../jalur_a_macro_f1/PROTOCOL.md), dan [K4](../20261126_k4_risiko_material/PROTOCOL.md).

**STATUS: PARTIAL.** D-152 dan D-158 utuh dan siap dievaluasi. K4 (D-164) masih punya dua penghambat sebelum target pertama boleh dibuka
(§2.3, §3.3).

## 1. Peta keluarga prediksi

Catatan istilah: di brief tugas, D-158 disebut "National-to-local / IW_NAT". `IW_NAT` adalah kandidat **D-152**. D-158 membekukan `FR_REF` (acuan
≈ `IW_NAT`) dan `FR_CITY` (diagnostik breadth kota). Dokumen ini memakai penamaan dari keputusan aslinya.

| Keluarga | Berkas beku | Baris | Model | Origin | Dibekukan | Manifest |
|---|---|---|---|---|---|---|
| D-152 intraminggu | [`forward_preds.csv`](../20261125_iw_validasi/hasil/forward_preds.csv) | 8.112 | `base` (C1-tuned), `IW_NAT` | h 4: 2026-10-26..11-16 (4); h 8: 2026-09-28..11-16 (8) | 2026-11-25 12.09 UTC | [`forward_manifest.json`](../20261125_iw_validasi/hasil/forward_manifest.json) |
| D-158 nasional–lokal | [`forward_preds_d158.csv`](../20261126_nasional_lokal/hasil/forward_preds_d158.csv) | 12.168 | `base`, `FR_REF`, `FR_CITY` | sama | 2026-11-26 00.26 UTC | [`forward_manifest_d158.json`](../20261126_nasional_lokal/hasil/forward_manifest_d158.json) |
| D-164 K4 risiko material | [`k4_forward_preds.csv`](../20261126_k4_risiko_material/hasil/k4_forward_preds.csv) | 4.056 | K4-E80, K4-A80 (mentah & `_cal`), B-C1t (`c1t`, `c1t_cal`), laju-dasar (`clim_e80`, `clims_e80`, `clims_a80`) | sama | 2026-11-26 23.16 WIB | [`k4_forward_manifest.json`](../20261126_k4_risiko_material/hasil/k4_forward_manifest.json) |

Ketiganya dilatih pada snapshot PIHPS yang sama: `pihps_pasar_tradisional_harian_2017-2026_v2_merged_retrieved_2026-11-18.zip`
(sha256 `bfc7f343…`, tanggal terakhir 2026-11-18, minggu panel terakhir 2026-11-16). 338 seri, `p_up` 0,081..0,947, tanpa NaN, tanpa kunci
ganda (audit Jalur A, [`a_forward_audit.json`](../jalur_a_macro_f1/hasil/a_forward_audit.json)).

## 2. Status pembekuan (diperiksa ulang 2026-11-27)

Alat: [`scripts/integrity_check.py`](scripts/integrity_check.py) → [`hasil/integrity_2026-11-27.json`](hasil/integrity_2026-11-27.json). Kode keluar 1 (K4 gagal).

| Pemeriksaan | D-152 | D-158 | D-164 K4 |
|---|---|---|---|
| sha256 berkas = manifest | ✓ `28651b2b…` | ✓ `7586eaed…` | ✓ `eb1f10db…` |
| Jumlah baris = manifest | ✓ 8.112 | ✓ 12.168 | ✓ 4.056 |
| Berkas di-track git | ✓ | ✓ | ✓ (tetapi versi lain, lihat §2.3) |
| Isi di HEAD = versi beku | ✓ (`ca53742`, 2026-11-25 21.41 WIB) | ✓ (`ec6dd19`, 2026-11-26 20.45 WIB) | **✗**: HEAD `3095ae0` memuat sha256 `1b5c84cb…` |
| Manifest di-track & bersih | ✓ | ✓ | **✗** belum di-track |
| Commit sebelum target pertama lengkap (Jumat 2026-11-27) | ✓ | ✓ | **belum** |
| Ujung baris berkas beku | CRLF (blob git LF) | CRLF (blob git LF) | LF |

### 2.1 D-152 & D-158: utuh
Prediksi, manifest, dan evaluator tidak berubah sejak dibekukan. Base D-152 identik dengan base D-158 (diperiksa oleh `fw_common.load_frozen`).

### 2.2 Temuan: hash beku D-152/D-158 bergantung pada ujung baris (risiko reproduksi, bukan pelanggaran integritas)
`fw_freeze.py` dan `fw_freeze_d158.py` menulis CSV dengan `pandas.to_csv` bawaan di Windows, sehingga hasilnya CRLF. sha256 di manifest adalah
hash byte CRLF. Git menyimpan blob LF (`core.autocrlf=true`, `git ls-files --eol`: `i/lf w/crlf`). Isinya terbukti sama:
sha256(blob HEAD diubah ke CRLF) = hash manifest untuk kedua berkas.
- Di checkout ini verifikasi lolos. Pada clone dengan `core.autocrlf=false/input` (Linux, Kaggle, Colab), berkas akan LF, lalu
  `a_forward_eval.py` → `load_frozen(verify=True)` berhenti dengan "prediksi berubah" walaupun isinya identik.
- Rekomendasi (tidak dijalankan; manifest dan evaluator beku tidak diubah): jalankan evaluasi maju di checkout Windows ini. Bila harus di
  tempat lain, verifikasi dulu dengan `integrity_check.py` (yang memeriksa versi CRLF dari blob), lalu konversi salinan berkas ke CRLF sebelum
  `a_forward_eval.py` dijalankan. Catat tindakan ini di laporan hasil.

### 2.3 D-164 K4: isi versi beku sah, tetapi belum di-commit
- Commit `3095ae0` (2026-11-26 23.15.49 WIB) memuat **keluaran mentah** `k4_run.py PART=forward`: 40 kolom, sha256 `1b5c84cb…`. Kolom
  `y`/`has_target` kosong; `ymax` hanya parsial untuk minggu ≤ 2026-11-16.
- 18 detik kemudian (23.16.07) `k4_freeze.py` menimpa berkas yang sama dengan **versi beku**: 15 kolom, ditambah peluang terkalibrasi
  `k4_e80_cal`, `k4_a80_cal`, `c1t_cal`, LF, sha256 `eb1f10db…`. Lalu ia menulis `k4_forward_manifest.json`. Tidak satu pun dari keduanya
  di-commit.
- Verifikasi isi (baca-saja, [`scripts/k4_refreeze_check.py`](scripts/k4_refreeze_check.py)):
  - 7 kolom mentah di versi beku = kolom yang sama di versi HEAD (dibulatkan 6 desimal), dengan selisih maksimum 0, kunci 4.056/4.056 cocok,
    dan wilayah sama.
  - Logika `k4_freeze.py` dijalankan ulang di memori dari parquet kerja sesi K4: `k4_forward_preds.parquet` 22.55,
    `k4_dev_preds.parquet` 18.58, `k4_test_preds.parquet` 23.15, semuanya sebelum pembekuan. Hasilnya sha256 `eb1f10db…` = berkas beku.
  - Jadi isi versi beku adalah fungsi deterministik dari prediksi yang dibuat sebelum target ada.
- **Yang masih kurang:** bukti waktu publik (commit) bahwa versi `eb1f10db…` ada sebelum target terlihat. Tindakan `[HUMAN]`: commit
  `hasil/k4_forward_preds.csv` dan `hasil/k4_forward_manifest.json` apa adanya, **sebelum** snapshot PIHPS yang memuat 2026-11-27 diunduh.
  Agent tidak boleh commit (CLAUDE.md §4.6).

## 3. Evaluator

| Evaluator | Cakupan | Hash beku | Status sekarang | Uji |
|---|---|---|---|---|
| [`fw_eval.py`](../20261125_iw_validasi/scripts/fw_eval.py) (D-152) | definisi label (`labels`), metrik dasar base vs `IW_NAT`, selisih berpasangan bootstrap blok origin | manifest D-152 `1949795c…` | ✓ sama | `--selftest` 2026-11-27: label snapshot sekarang = `y_4`/`y_8` resmi, 156.400 / 155.040 baris, 0 beda |
| [`a_forward_eval.py`](../jalur_a_macro_f1/scripts/a_forward_eval.py) + [`fw_common.py`](../jalur_a_macro_f1/scripts/fw_common.py) (Jalur A) | gabungan D-152 + D-158: macro F1, F1/presisi/recall per kelas, MCC, ROC-AUC, Brier, ECE, porsi naik, kuintil \|y\| terkecil; Δ vs base + interval bootstrap kluster provinsi; penanda KONSISTEN / TIDAK_TERBUKTI / GAGAL_MAJU | [`a_protocol_sha256.txt`](../jalur_a_macro_f1/hasil/a_protocol_sha256.txt) 2026-11-26 11.34 UTC | ✓ sama | `docs/audit/jalur_a_macro_f1/tests/test_forward_eval.py` 7/7 lolos |
| [`k4_eval.py`](../20261126_k4_risiko_material/scripts/k4_eval.py) (K4) | hanya `PART=dev` / `PART=test`, dan membaca parquet di folder kerja sementara | tidak ada (sama dengan HEAD) | **tidak mencakup prediksi maju** | – |

### 3.1 Celah evaluator D-152/D-158 (tidak menghalangi)
`a_forward_eval.py` melaporkan metrik per horizon × model, bukan per komoditas/origin, dan tidak menulis confusion matrix. Brief tugas meminta
rincian itu. Rincian per komoditas/origin hanya bersifat **deskriptif** dan tidak mengubah penanda. Bila dibuat, harus berupa skrip terpisah yang
dibekukan sebelum target dibuka, mengimpor `fw_eval.labels` dan `fw_common` tanpa mengubahnya. Saat audit ini belum dibuat (lihat
[OPEN_ISSUES.md](OPEN_ISSUES.md) PV-3).

### 3.2 `src/features/forecast.py` berubah sesudah pembekuan D-152/D-158
Penyebabnya perbaikan D-162 (U108, flag `episode` real-time). `episode` hanya ada di grup `fx`, dan C1-tuned/`IW_NAT`/FR_* tidak memakai grup
`fx` (C1/C1t identik setelah run ulang D-162). Perubahan ini tidak menyentuh berkas beku dan tidak dipakai evaluator. Dampaknya hanya pada
reproduksi ulang prediksi, yang memang tidak boleh dilakukan.

### 3.3 Penghambat K4: tidak ada evaluator maju beku dan tidak ada aturan keputusan maju
PROTOCOL K4 §6 hanya menyatakan "konfirmasi hanya dari prediksi maju ini". [RECOMMENDATIONS.md](../20261126_k4_risiko_material/RECOMMENDATIONS.md)
#3 merencanakan "`k4_eval.py` dengan PART baru", tetapi PART itu belum dibuat dan **ambang keputusannya belum ditetapkan**. Menetapkan ambang
adalah pilihan penelitian, jadi diajukan ke Danen di [FORWARD_VALIDATION_PROTOCOL.md](FORWARD_VALIDATION_PROTOCOL.md) §5 (DRAF). Draf itu harus
disetujui dan dibekukan (sha256 + commit) sebelum snapshot yang memuat 2026-11-27 diunduh. Tanpa itu, status K4 = **BLOCKED**.

## 4. Mekanisme snapshot PIHPS

- Mekanisme yang ada: [`fetch_pihps.py`](../20261125_pilot_grosir/scripts/fetch_pihps.py) (endpoint grid PIHPS = data yang diekspor tombol
  Download resmi, U19; dipakai D-150/D-151). Formatnya sama dengan `pihps`, dan skrip menolak menimpa berkas.
- Uji kecocokan 2026-11-27 04.25 WIB (`--price-type 1`, jendela **2026-09-01..2026-11-18**, jadi tidak ada tanggal target maju yang terbaca):
  - 102 permintaan, 0 galat.
  - Setelah `load_pihps` + `select_variants` resmi: 19.103 baris, semuanya ada di kedua sisi, dan **19.103 harga identik**.
  - Bukti: [`hasil/compat_pihps_pt1_2026-11-27.json`](hasil/compat_pihps_pt1_2026-11-27.json), [`scripts/compat_check.py`](scripts/compat_check.py).
  - Artinya: mekanisme dapat dipakai untuk label maju, dan tidak ada revisi pada 79 hari yang sudah ada di snapshot beku (termasuk
    2026-11-18, diambil ulang 9 hari kemudian). Ini bukti parsial untuk U110, bukan pengamatan jendela H+1.
- Zip hasil unduhan uji hanya ada di scratchpad sesi (PIHPS mentah tidak boleh didistribusikan) dan tidak dipakai untuk apa pun selain uji ini.

## 5. Keterbatasan yang diketahui

- **Origin 2026-11-16 dibuat dari minggu parsial.** Snapshot beku berakhir Rabu 2026-11-18 (2026-11-19 sebagian kosong), jadi fitur minggu
  origin terakhir memakai ≤ 3 hari. Label maju memakai rerata minggu penuh dari snapshot baru. Ini bukan kebocoran, tetapi kondisi informasinya
  berbeda dari origin lain. Hasil origin ini dilaporkan terpisah secara deskriptif.
- **Origin mingguan saling tumpang tindih.** 4 origin h 4 ≈ 1 jendela independen; 8 origin h 8 ≈ 2. Daya hanya cukup untuk menandai
  kegagalan besar (D-152 §4; Jalur A §A).
- **Test 2024+ bukan validasi independen** (D-155). Hasil maju tidak boleh disamakan dengan hasil test historis.

## 6. Dependensi

| # | Dependensi | Pemilik | Batas |
|---|---|---|---|
| 1 | Commit versi beku K4 (`k4_forward_preds.csv` sha256 `eb1f10db…` + `k4_forward_manifest.json`) | Danen (git) | sebelum unduh snapshot yang memuat 2026-11-27 |
| 2 | Persetujuan, pembekuan, dan commit evaluator + aturan maju K4 (draf §5 protokol) | Danen (keputusan), agent (implementasi) | sama |
| 3 | Checkout Windows dengan `core.autocrlf=true` (atau konversi CRLF yang tercatat) untuk `a_forward_eval.py` | Danen | tiap evaluasi |
| 4 | Akses internet ke endpoint PIHPS (BI) | – | tiap evaluasi |
| 5 | Folder kerja parquet K4 (scratchpad sesi K4) | – | hanya untuk reproduksi pembekuan; **tidak** dibutuhkan evaluator maju |
