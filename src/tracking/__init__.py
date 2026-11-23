"""Pelacakan eksekusi & log evaluasi terpusat (WP-36, D-137).

Lapisan lintas-tahap yang hanya MENCATAT: run ID, status, waktu, lineage artefak (sha256 input/output → run induk),
dan metrik evaluasi per tahap yang dihitung dari artefak yang sudah ditulis. Tidak mengubah hasil analisis.

- `schemas`    : dataclass RunRecord, ArtifactRef, Metric, ErrorRecord, EvaluationRecord.
- `metrics`    : metrik generik berpenjaga (clustering, regresi, profil data, konsistensi p–interval).
- `lineage`    : hash artefak, perekam baca/tulis, pencarian run induk, identitas dataset.
- `evaluators` : evaluator spesifik per tahap (membaca artefak; metrik tak berlaku = not_applicable + alasan).
- `registry`   : spesifikasi tahap (jenis, algoritma, parameter relevan) + graf dependensi dari REQUIRES pipeline.
- `store`      : simpan/baca log JSON (tidak pernah menimpa), riwayat, perbandingan run, deteksi hasil basi.
- `logger`     : `tracked(task)` (dekorator pipeline), `run_tracked`, `pipeline` (satu ID untuk `kagami all`),
                 `evaluate_existing` (evaluasi artefak yang ada tanpa menjalankan ulang).
"""
