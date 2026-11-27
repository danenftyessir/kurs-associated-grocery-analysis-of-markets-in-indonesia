# Ringkasan — validasi prospektif & akuisisi data (2026-11-27)

**STATUS: PARTIAL.** Audit integritas, protokol, dan evaluator K4 selesai. Belum ada evaluasi maju karena belum ada target yang lengkap.
Sisa satu tindakan sebelum 2026-11-29: commit pembekuan evaluator (PV-2b). Diperbarui 2026-11-27 10.20 WIB.

## Kesimpulan eksekutif

1. **D-152 (`IW_NAT`) dan D-158 (`FR_REF`, `FR_CITY`) utuh.** sha256 prediksi = manifest = commit sebelum target ada (`ca53742`,
   `ec6dd19`). Evaluator beku (`fw_eval.py`, `a_forward_eval.py`, `fw_common.py`) tidak berubah, uji mandiri label 0 beda, dan tes evaluator
   7/7 lolos.
2. **K4 (D-164): beku dan di-commit; evaluator maju siap.**
   - Berkas beku `eb1f10db…` dapat direkonstruksi persis dari prediksi yang dibuat sebelum target ada.
   - Danen meng-commit versi beku + manifest di `044873c` (2026-11-27 09.53 WIB), sebelum target terlihat.
   - Aturan maju disetujui (D-167). `scripts/k4_forward_eval.py` mereproduksi label dan metrik pipeline K4 pada origin test historis
     (24.616/24.616 label; AP/AUC/presisi@K sama).
   - Commit evaluator ini masih menunggu (PV-2b).
3. **Mekanisme unduh PIHPS eceran siap.** Uji pada jendela tanpa target menunjukkan 19.103 / 19.103 harga identik dengan snapshot beku dan
   0 revisi.
4. **Risiko reproduksi:** hash beku D-152/D-158 adalah hash byte CRLF. Verifikasi hanya lolos di checkout dengan `core.autocrlf=true`.
5. **Daya rendah.** Data maju hanya dapat menandai kegagalan besar: Δ macro F1 < −0,08 / −0,04, dan untuk K4 ΔAP < ± −0,14. Keuntungan kecil
   dari test 2024+ tidak dapat dikonfirmasi, dan hasil maju tidak boleh disamakan dengan test.
6. **Akuisisi data:** SP2KP, Neraca Pangan Bapanas, dan luas tanam/EWS Kementan hanya tersedia lewat permintaan resmi. Spesifikasi dan draf
   surat sudah siap. Tidak ada modeling dan tidak ada backfill.

## Status per jalur

| Jalur | Keputusan saat ini | Dasar | Keputusan final |
|---|---|---|---|
| D-152 intraminggu (`IW_NAT` vs C1-tuned) | **BLOCKED** (belum ada target lengkap) | 0 target siap pada snapshot 2026-11-18 | h 4: 2026-12-20; h 8: 2027-01-17 |
| D-158 (`FR_REF`, `FR_CITY` vs C1-tuned) | **BLOCKED** (idem) | idem | idem |
| D-164 K4-E80 | **BLOCKED** (belum ada target lengkap; evaluator D-167 menunggu commit) | INITIAL_AUDIT §2.3, protokol §5 | h 4 2026-12-20, h 8 2027-01-17 |
| C1-tuned | deskriptif saja (tidak ada aturan maju beku) | protokol §4 | – |
| Akuisisi data U112 | **BLOCKED** `[HUMAN]` | akses terbatas / berlogin | – |
| Operasional K4 / daftar pantau | **BLOCKED** (U109) | D-154, D-164 | – |

Tidak ada INTEGRITY_FAILED: tidak satu pun berkas beku yang isinya berbeda dari manifest.

## Rekomendasi keputusan (untuk Danen)

1. ~~Commit versi beku K4 + manifest (PV-1)~~: selesai, `044873c`.
2. ~~Putuskan aturan maju K4~~: disetujui (D-167). **Sebelum 2026-11-29:** commit `FORWARD_VALIDATION_PROTOCOL.md`,
   `scripts/k4_forward_eval.py`, `scripts/integrity_check.py`, dan `hasil/pv_protocol_sha256.txt` apa adanya (PV-2b). Sesudahnya
   `integrity_check.py` harus keluar 0.
3. **2026-11-29:** putaran E1 (1 origin per horizon, interim). E2 pada 2026-12-20, E3 pada 2027-01-17.
4. **Makalah (submit 29 Nov):** tulis validasi maju sebagai "prediksi maju dibekukan dan di-commit sebelum target ada; evaluasi berjalan
   s.d. Januari 2027". Jangan menulis hasil maju apa pun sebagai konfirmasi.
5. Kirim permintaan data resmi (PV-8 / U112).

Dokumen: [INITIAL_AUDIT](INITIAL_AUDIT.md) · [FORWARD_VALIDATION_PROTOCOL](FORWARD_VALIDATION_PROTOCOL.md) ·
[FORWARD_VALIDATION_RESULTS](FORWARD_VALIDATION_RESULTS.md) · [DATA_ACQUISITION_REPORT](DATA_ACQUISITION_REPORT.md) · [OPEN_ISSUES](OPEN_ISSUES.md)
