# Pekerjaan terbuka — validasi prospektif

Isu lokal folder ini (PV-n). Isu proyek tetap di [`docs/OPEN_ISSUES.md`](../../OPEN_ISSUES.md) (U109, U110, U112).

| ID | Pekerjaan | Pemilik | Batas | Status |
|---|---|---|---|---|
| PV-1 | Commit `20261126_k4_risiko_material/hasil/k4_forward_preds.csv` (sha256 `eb1f10db…`, LF) + `k4_forward_manifest.json` apa adanya. Sesudahnya `integrity_check.py` harus keluar 0 | Danen (git, `[HUMAN]`) | sebelum unduh snapshot yang memuat 2026-11-27 (≤ 2026-11-29) | 🔴 |
| PV-2 | Putuskan draf aturan maju K4 (protokol §5). Bila disetujui: tulis `scripts/k4_forward_eval.py` + uji mandiri, catat sha256 di `hasil/pv_protocol_sha256.txt`, commit | Danen (keputusan) → agent | sama dengan PV-1 | 🔴 menunggu keputusan |
| PV-3 | (Opsional) skrip rincian deskriptif D-152/D-158 per komoditas/origin + confusion matrix, mengimpor `fw_eval.labels`/`fw_common` tanpa mengubahnya; beku + commit sebelum E1 | agent, bila diminta | sebelum E1 | 🟡 |
| PV-4 | Hash beku D-152/D-158 = byte CRLF; blob git LF. Evaluasi di checkout Windows ini (`core.autocrlf=true`) atau catat konversi CRLF | Danen | setiap putaran | 🟡 tercatat (INITIAL_AUDIT §2.2) |
| PV-5 | Putaran E1: unduh snapshot penuh ≥ 2026-11-29 00.00 WIB, integritas, revisi historis, `a_forward_eval.py` | agent + Danen (koneksi) | 2026-11-29 | ⬜ |
| PV-6 | Putaran E2 (semua h 4 lengkap): keputusan final h 4 | sama | 2026-12-20 | ⬜ |
| PV-7 | Putaran E3 (semua h 8 lengkap): keputusan final h 8 + ringkasan | sama | 2027-01-17 | ⬜ |
| PV-8 | Kirim permintaan data resmi SP2KP, Bapanas Proyeksi Neraca Pangan, Kementan luas tanam/EWS (DATA_ACQUISITION_REPORT §4) | Danen/Abi (`[HUMAN]`) | secepatnya; tidak menghalangi lomba | 🔴 (= U112) |
| PV-9 | U110 jendela revisi: uji kecocokan menunjukkan 0 revisi dalam 79 hari. Pengamatan H+1 langsung masih perlu, mis. unduh hari Sabtu lalu ulang hari Minggu pada putaran E1, dan bandingkan Jumat target | agent (E1) | 2026-11-29 | 🟡 |

Dependensi manusia: PV-1, PV-2 (keputusan), PV-8, dan koneksi internet di setiap putaran. Agent tidak commit, tidak mengirim surat, tidak
login.

Catatan untuk PV-9: unduhan pengecekan revisi hari Sabtu hanya boleh dibuka sesudah unduhan Minggu dievaluasi, atau dipakai hanya untuk
perbandingan tanggal (tanpa label). Dengan begitu pilihan snapshot tidak dipengaruhi hasil.
