# Hasil validasi prospektif

Satu entri per putaran yang **benar-benar dijalankan**, terbaru di atas. Aturan dan prosedur: [FORWARD_VALIDATION_PROTOCOL.md](FORWARD_VALIDATION_PROTOCOL.md).
Angka di sini adalah evaluasi prospektif pada origin mingguan yang tumpang tindih, deskriptif, dan tidak digabung dengan test 2024+.

## Ringkasan status per keluarga

| Keluarga | Pembanding | h 4 | h 8 | Diperbarui |
|---|---|---|---|---|
| D-152 `IW_NAT` | base (C1-tuned) | BLOCKED: belum ada target lengkap | BLOCKED: belum ada target lengkap | 2026-11-27 |
| D-158 `FR_REF`, `FR_CITY` | base | BLOCKED: belum ada target lengkap | BLOCKED: belum ada target lengkap | 2026-11-27 |
| D-164 K4-E80 | B-C1t, B-CLIMS | BLOCKED: versi beku belum di-commit, evaluator maju belum ada | sama | 2026-11-27 |
| C1-tuned (`base`) | – (deskriptif, tanpa aturan beku) | – | – | – |

---

## Putaran 0 — 2026-11-27 (audit pra-target; tanpa evaluasi)

**STATUS:** BLOCKED (tidak ada evaluasi; belum ada target lengkap)

**SUMMARY:**
- Integritas ketiga pembekuan diaudit, evaluator beku diuji, dan mekanisme unduh PIHPS eceran diuji pada jendela yang tidak memuat target.
- Tidak ada label maju yang dihitung atau dilihat.
- Snapshot yang ada berakhir 2026-11-18. Target pertama membutuhkan data s.d. Jumat 2026-11-27 (`a_forward_audit.json`: 0 target siap).

**EVIDENCE:**
- [`hasil/integrity_2026-11-27.json`](hasil/integrity_2026-11-27.json):
  - D-152 `28651b2b…` = manifest = HEAD `ca53742` (CRLF).
  - D-158 `7586eaed…` = manifest = HEAD `ec6dd19` (CRLF).
  - K4 `eb1f10db…` = manifest, tetapi ≠ HEAD `3095ae0` (`1b5c84cb…`), dan manifest tidak di-track.
- Evaluator:
  - `fw_eval.py` `1949795c…` = manifest D-152.
  - `a_forward_eval.py` `e7e69221…` dan `fw_common.py` `46c72d83…` = `a_protocol_sha256.txt`.
- [`hasil/compat_pihps_pt1_2026-11-27.json`](hasil/compat_pihps_pt1_2026-11-27.json): 19.103 / 19.103 harga identik pada 2026-09-01..11-18,
  zip uji `cbc59e29…`.

**VERIFICATION:**
- `fw_eval.py --selftest`: 156.400 / 155.040 baris, 0 beda dari `y_4`/`y_8` resmi.
- `pytest docs/audit/jalur_a_macro_f1/tests/test_forward_eval.py`: 7 lolos.
- Rekonstruksi pembekuan K4 di memori: sha256 = berkas beku.

**DECISION:** Belum ada keputusan validasi (BLOCKED, menunggu target). Tidak ada INTEGRITY_FAILED: isi semua berkas beku terbukti sesuai
manifest. Kekurangan K4 adalah bukti waktu (commit), bukan isi.

**BLOCKERS:**
1. Commit versi beku K4 + manifest (`[HUMAN]`).
2. Persetujuan dan pembekuan evaluator + aturan maju K4 (protokol §5).
3. Snapshot yang memuat 2026-11-27, paling cepat Minggu 2026-11-29.

**NEXT ACTION:**
1. Danen commit K4 dan memutuskan draf §5 sebelum 2026-11-29.
2. Putaran E1 pada **2026-11-29** (origin 10-26 h 4 dan 09-28 h 8).

<!-- Template putaran berikutnya:
## Putaran E<n> — YYYY-MM-DD (snapshot s.d. YYYY-MM-DD)
**STATUS:** COMPLETE / PARTIAL / BLOCKED / FAILED
**SUMMARY:** origin bertarget per horizon; apa yang dijalankan.
**EVIDENCE:** sha256 snapshot + retrieved_at + galat; integrity_<tgl>.json; berkas a_forward_eval_<tgl>_{metrics,paired}.csv; revisi historis.
**VERIFICATION:** integrity exit 0; kelengkapan Jumat; cek silang base D-152 = D-158.
Tabel metrik per horizon × model: macro F1, F1/presisi/recall naik & turun, MCC, ROC-AUC, Brier, ECE, porsi naik aktual/prediksi, macro F1 kuintil kecil, n, n_origin.
Tabel selisih vs base: Δ macro F1 (interval kluster provinsi; interval blok origin fw_eval), Δ AUC, Δ Brier, flip_share, penanda beku.
Analisis galat: per komoditas, per origin (origin 2026-11-16 terpisah), confusion matrix (deskriptif).
**DECISION:** penanda beku per keluarga × horizon (interim / final).
**BLOCKERS:** ...
**NEXT ACTION:** ... (tanggal)
-->
