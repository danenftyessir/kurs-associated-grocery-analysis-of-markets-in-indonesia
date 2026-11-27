# Protokol validasi prospektif (prediksi maju beku D-152, D-158, D-164)

Ditulis 2026-11-27 sebelum satu pun target maju terlihat. Dokumen ini **tidak mengubah** aturan yang sudah dibekukan
([D-152 §3–§4](../20261125_iw_validasi/PROTOKOL.md), [Jalur A §A](../jalur_a_macro_f1/PROTOCOL.md), [K4 §6](../20261126_k4_risiko_material/PROTOCOL.md)).
Isinya hanya prosedur operasional di sekeliling aturan itu. Bagian §5 (K4) adalah **DRAF** yang menunggu persetujuan Danen. Tanpa persetujuan
dan commit sebelum unduhan pertama, K4 tetap BLOCKED.

## 1. Jadwal

Target untuk origin t dan horizon h dianggap lengkap bila snapshot memuat **Jumat minggu t + h** (aturan beku `fw_eval.labels` /
`fw_common.target_ready`).

| Origin | h | Minggu target | Jumat target |
|---|---|---|---|
| 2026-10-26 | 4 | 2026-11-23 | 2026-11-27 |
| 2026-11-02 | 4 | 2026-11-30 | 2026-12-04 |
| 2026-11-09 | 4 | 2026-12-07 | 2026-12-11 |
| 2026-11-16 | 4 | 2026-12-14 | 2026-12-18 |
| 2026-09-28 .. 2026-10-19 | 8 | 2026-11-23 .. 2026-12-14 | 2026-11-27 .. 2026-12-18 |
| 2026-10-26 .. 2026-11-16 | 8 | 2026-12-21 .. 2027-01-11 | 2026-12-25 .. 2027-01-15 |

**Waktu unduh:** paling cepat Minggu 00.00 WIB sesudah Jumat target. Ini batas konservatif `available_at` D-155: jendela revisi PIHPS belum
dipastikan (U110). Uji kecocokan 2026-11-27 tidak menemukan revisi dalam 79 hari, tetapi itu belum membuktikan jendela H+1. Akibatnya jadwal
di brief tugas (28 Nov, 19 Des, 16 Jan, semuanya hari Sabtu) bergeser satu hari.

| Putaran | Unduh & evaluasi paling cepat | Origin bertarget (h 4 / h 8) | Sifat |
|---|---|---|---|
| E1 | **Minggu 2026-11-29** | 1 (10-26) / 1 (09-28) | interim, deskriptif |
| (opsional mingguan) | 2026-12-06, 2026-12-13 | 2–3 / 2–3 | interim |
| E2 | **Minggu 2026-12-20** | 4 (lengkap) / 4 | keputusan h 4 final; h 8 interim |
| E3 | **Minggu 2027-01-17** | 4 / 8 (lengkap) | keputusan h 8 final |

Setiap putaran dicatat di [FORWARD_VALIDATION_RESULTS.md](FORWARD_VALIDATION_RESULTS.md), termasuk putaran yang gagal atau ditunda.

## 2. Prasyarat sebelum unduhan pertama (E1)

1. `integrity_check.py` keluar 0. Artinya versi beku K4 + manifest sudah di-commit apa adanya (INITIAL_AUDIT §2.3).
2. Evaluator maju K4 dan aturan §5 sudah disetujui, sha256-nya dicatat di `hasil/pv_protocol_sha256.txt`, dan semuanya di-commit. Bila tidak,
   E1 tetap dijalankan untuk D-152/D-158, dan K4 dicatat BLOCKED.
3. Bila skrip rincian deskriptif per komoditas/origin dipakai (OPEN_ISSUES PV-3), skrip itu juga dibekukan dan di-commit lebih dulu.

Urutan ini wajib: commit dulu, baru unduh. Commit yang dibuat sesudah snapshot memuat target tidak membuktikan apa pun.

## 3. Prosedur setiap putaran

1. **Integritas:** `python docs/audit/20261127_prospective_validation/scripts/integrity_check.py` → `hasil/integrity_<tanggal>.json`. Gagal →
   berhenti, status INTEGRITY_FAILED untuk keluarga itu.
2. **Unduh snapshot penuh** (format `pihps`, data mentah tidak diubah):
   ```
   python docs/audit/20261125_pilot_grosir/scripts/fetch_pihps.py --price-type 1 --start 2017-03-01 --end <Jumat target terakhir> --out data/raw/bi_pihps/forward/pihps_pasar_tradisional_harian_2017-2026_retrieved_<YYYY-MM-DD>.zip --cache <folder cache baru>
   ```
   - Folder `data/raw/bi_pihps/forward/` **tidak** didaftarkan di `configs/sources.yaml`, supaya input resmi tidak berubah.
   - Skrip menolak menimpa berkas. Pakai folder cache baru agar respons lama tidak terpakai.
   - Catat sha256 zip, `retrieved_at`, jumlah galat (`ERRORS.json`). Galat > 0 → ulangi provinsi/bulan yang gagal. Bila tetap gagal,
     putaran itu BLOCKED.
3. **Kelengkapan** (diperiksa sebelum evaluator jalan, hanya dari cakupan tanggal, tanpa melihat label):
   - Aturan beku hanya meminta tanggal terakhir ≥ Jumat target.
   - Laporkan juga berapa provinsi × komoditas yang terisi pada setiap hari minggu target.
   - Bila hari Jumat masih kosong untuk sebagian besar seri (data belum terbit), **tunda seluruh putaran** dan unduh ulang lebih lambat. Ini
     keputusan waktu, bukan pemilihan baris: aturan baris evaluator tidak diubah. Jangan menebak atau mengisi.
4. **Revisi historis:** jalankan `compat_check.py` dengan jendela diperlebar ke seluruh periode bersama (≤ 2026-11-18). Laporkan jumlah sel
   yang berubah per tanggal dan komoditas. Evaluasi tetap memakai snapshot baru (aturan beku). Bila revisi menyentuh minggu origin maju
   (2026-09-28..11-16), selisih fitur tidak dikoreksi; hal itu dicatat sebagai keterbatasan.
5. **Evaluasi beku:**
   - `python docs/audit/jalur_a_macro_f1/scripts/a_forward_eval.py --pihps-zip <zip>` untuk D-152 + D-158. Skrip ini memverifikasi sha256
     prediksi dan `fw_eval.py` sendiri.
   - Opsional, `python docs/audit/20261125_iw_validasi/scripts/fw_eval.py --pihps-zip <zip>` (D-152 saja; tambahan selisih bootstrap blok
     origin).
   - K4: evaluator maju beku (§5) bila sudah disetujui.
6. **Catat semuanya** di FORWARD_VALIDATION_RESULTS.md: sha256 snapshot, origin yang dinilai, metrik lengkap, penanda, kegagalan.
   Berkas keluaran evaluator (`a_forward_eval_<tanggal>_*.csv`) tidak diubah sesudah ditulis.
7. **Tidak boleh:** membuat ulang prediksi; mengubah threshold, label, fitur, model, atau evaluator sesudah melihat hasil; memilih origin;
   menggabungkan origin dari putaran lain secara selektif.

## 4. Aturan keputusan D-152 / D-158 (salinan aturan beku, tidak diubah)

Sumber: `a_forward_eval.py` (dibekukan 2026-11-26 11.34 UTC). Pembanding untuk `IW_NAT`, `FR_REF`, dan `FR_CITY` = `base` (C1-tuned).
Δ = macro F1 kandidat − base pada semua origin yang targetnya lengkap untuk horizon itu.

| Penanda beku | Syarat | Kategori brief |
|---|---|---|
| GAGAL_MAJU | Δ < −0,08 (h 4) atau Δ < −0,04 (h 8) | FAILED_FORWARD |
| KONSISTEN | Δ ≥ 0 | CONSISTENT |
| TIDAK_TERBUKTI | −MDE ≤ Δ < 0 | NOT_PROVEN |
| (prasyarat gagal) | sha256 / evaluator / snapshot | INTEGRITY_FAILED / BLOCKED |

- KONSISTEN berarti **tidak bertentangan** dengan keuntungan test (+0,0085 / +0,0033), bukan konfirmasi. Untuk mendeteksi keuntungan itu
  dibutuhkan ± 185 / 355 origin berjarak 4 minggu (D-152 §4). Tidak ada keputusan adopsi yang diambil dari data maju (Jalur A §A).
- Putaran interim melaporkan penanda pada origin yang sudah ada, dengan label "interim (n origin)". Keputusan final h 4 di E2 dan h 8 di E3.
- Interval: bootstrap kluster provinsi dari `fw_common.paired` dan bootstrap blok origin dari `fw_eval.paired`. Keduanya deskriptif;
  `fw_eval` menandai `descriptive_only` bila jumlah origin < 2h.
- **C1-tuned (`base`) sendiri** tidak punya aturan maju beku. Macro F1 base dilaporkan **deskriptif** bersama baseline kelas mayoritas pada
  baris yang sama dan nilai test historis 0,677 / 0,680 (yang bukan pembanding statistik). Tidak ada label CONSISTENT/FAILED untuk C1-tuned.

## 5. K4 (D-164) — DRAF, menunggu persetujuan Danen

Disusun sebelum target terlihat. Konstruksinya meniru Jalur A: penjaga kegagalan besar, bukan konfirmasi.

**Label** (PROTOCOL K4 §2; tidak dipilih ulang):
- y_h = `fw_eval.labels` (sama dengan y resmi; selftest 0 beda).
- z_e80 = 1[y_h ≥ `thr_e80` beku di berkas].
- z_a80 = 1[max_{k=1..h}(log p_{t+k} − log p_t) ≥ `thr_e80`], dengan minggu hilang dilewati (PROTOCOL §2: "ambang sama").
- Universe = semua baris di berkas beku. Target yang lengkap tetapi tidak teramati dihitung z = 0 (D-155), dan dilaporkan juga dengan baris
  itu dikeluarkan (deskriptif).
- Label **selalu dihitung ulang dari panel snapshot baru** dengan ambang beku. Kolom `z_*`/`y`/`ymax` di versi mentah `3095ae0` dibuat sebelum
  target terjadi: `z_*` seluruhnya 0 dan `ymax` parsial, jadi kolom itu **tidak boleh** dipakai sebagai label. Versi beku `eb1f10db…` memang
  tidak memuatnya. Temuan yang sama dicatat sesi validasi K4 (D-166, `docs/audit/20261127_k4_validation/TARGET_INTEGRITY_AUDIT.md` §2).

**Ukuran utama:** ΔAP pooled K4-E80 − B-C1t (`k4_e80` vs `c1t`) per horizon.

**Ukuran deskriptif:** AP K4-E80 / B-C1t / B-CLIM / B-CLIMS; presisi@K & recall@K (K = 1/2/3 per provinsi per origin, tie seed 154); Brier,
ECE 10 bin, dan Brier skill vs `clim_e80` untuk `k4_e80_cal`, `c1t_cal`, `k4_e80`; semuanya per komoditas dan per origin. Interval memakai
bootstrap kluster provinsi 1.999 replikasi (seperti `fw_common.paired`).

**Daya:**
- SE ΔAP test (interval K4 `k4_test_paired.csv`, /3,92) = 0,0169 (h 4) dan 0,0235 (h 8), pada 37 / 36 origin berjarak 4 minggu.
- MDE maju = 2,8·SE·√(n_test/n): h 4 ≈ 0,14 (n = 4) .. 0,29 (n = 1); h 8 ≈ 0,14 (n = 8) .. 0,28 (n = 2).
- Pembanding skala: AP test K4-E80 0,237 / 0,206.

**Penanda yang diusulkan:**

| Penanda | Syarat |
|---|---|
| FAILED_FORWARD | ΔAP < −0,14 di horizon itu |
| CONSISTENT | ΔAP ≥ 0 **dan** AP K4-E80 ≥ AP B-CLIMS |
| NOT_PROVEN | selain itu |

**Implementasi:** skrip baru `scripts/k4_forward_eval.py` di folder ini. Skrip mengimpor `fw_eval.labels` (hash diverifikasi seperti
`a_forward_eval.py`) dan fungsi metrik `k4_common` / `k4_eval` tanpa mengubahnya. Ia menolak berjalan bila sha256 berkas ≠ manifest. Uji
mandiri: data sintetis, dan label z pada origin test yang sudah terealisasi harus sama dengan `z_e80` di `k4_test_preds` (baca-saja). sha256
skrip + dokumen ini dicatat dan di-commit sebelum E1.

Status operasional K4 tetap **BLOCKED** (U109) apa pun hasil maju. K4 juga tidak dipakai untuk macro F1.

## 6. Pelaporan

Format setiap putaran: STATUS / SUMMARY / EVIDENCE / VERIFICATION / DECISION / BLOCKERS / NEXT ACTION (lihat FORWARD_VALIDATION_RESULTS.md).
Hasil maju ditulis sebagai "evaluasi prospektif pada n origin mingguan yang tumpang tindih; deskriptif". Hasil maju tidak digabung dengan
test 2024+.
