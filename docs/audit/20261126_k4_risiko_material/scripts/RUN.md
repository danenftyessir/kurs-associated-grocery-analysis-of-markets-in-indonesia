# Reproduksi K4 (D-164)

Dari root project (Git Bash; PowerShell: `$env:NAMA = "nilai"`). Tanpa instalasi paket (alias `kagami` lewat `kg.py`).

| Langkah | Perintah | Waktu (mesin Danen, 5 proses × 2 thread) | Keluaran |
|---|---|---|---|
| 0 | `KAGAMI_EXP=<folder> python docs/audit/20261125_task4_audit_preprocessing/scripts/prep.py` (bila `base.parquet` belum ada) | ± 15 menit | `<EXP>/base.parquet` |
| 1 | `python docs/audit/20261126_k4_risiko_material/scripts/k4_selftest.py` | < 1 menit | uji mandiri (data sintetis) |
| 2 | `python .../scripts/k4_du.py` | ± 6 menit | `hasil/du_*.csv`, `du_summary.json` |
| 3 | `PART=dev NJ=5 python .../scripts/k4_run.py` | ± 25 menit (75 pekerjaan × 6 fit HGB) | `<EXP>/k4_dev_preds.parquet`, `hasil/k4_dev_meta.csv` |
| 4 | `python .../scripts/k4_leak.py` | ± 3 menit | `hasil/leak_checks.csv` (harus semua `pass`) |
| 5 | `PART=dev python .../scripts/k4_eval.py` | ± 10 menit | `hasil/k4_*.csv`, `k4_decision.json`, (`k4_test_allowed.flag`) |
| 6 | `PART=test python .../scripts/k4_run.py` lalu `PART=test python .../scripts/k4_eval.py` | hanya bila flag ada | `hasil/k4_test_*` |
| 7 | `PART=forward python .../scripts/k4_run.py` lalu `python .../scripts/k4_freeze.py` | ± 4 menit | `hasil/k4_forward_preds.csv` + manifest sha256 |
| 8 | `python .../scripts/k4_log.py` | ± 5 menit | `EXPERIMENT_LOG.csv`, `hasil/k4_metrics_long.csv` |

Konfigurasi: seed 20261121 (`params.yaml`), `large_move_pct` 80, `TUNED_HGB` & `tuned_columns("C1t", h)` dari `src/models/direction.py`,
bootstrap 1.999 replikasi blok origin ceil(h/4)+1, Platt walk-forward ≥ 6 origin lampau, tie-break daftar pantau seed 154. Versi: Python 3.13,
numpy 2.3.4, pandas 2.3.3, scipy 1.16.3, scikit-learn 1.8.0. `KAGAMI_EXP` default = scratchpad sesi K4 (hapus-able; bangun ulang langkah 0).
Hash protokol & skrip saat beku: `hasil/protocol_sha256.txt`.
