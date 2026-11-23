# Log eksekusi & evaluasi terpusat (WP-36, D-137)

Setiap eksekusi tahap menghasilkan log terstruktur yang bisa ditelusuri dan dibandingkan dengan eksekusi lain, tanpa mengubah
hasil analisis. Kode: [`src/tracking/`](../src/tracking/). Dashboard: app halaman 7 *Evaluasi & Riwayat Eksekusi*.

## 1. Arsitektur

```
pipelines/<tahap>.run  ──@tracked("<tahap>")──►  tracking.logger.run_tracked
                                                  ├─ utils.io.add_observer → lineage.Recorder (sha256 input saat dibaca,
                                                  │                          output di akhir run)
                                                  ├─ jalankan tahap (hasil & exception diteruskan apa adanya)
                                                  ├─ lineage: run induk (hash input = hash output run lain), dataset_id,
                                                  │           git commit, sha256 params.yaml, memori puncak
                                                  ├─ sukses → evaluators.evaluate(<tahap>) → logs/evaluations/<run>.json
                                                  ├─ gagal  → logs/errors/<run>.json (tipe, pesan, traceback), lalu raise
                                                  └─ logs/runs/<run>.json (metadata eksekusi)
kagami all             ──tracking.pipeline──►     logs/pipelines/<pipeline>.json (urutan run + status)
kagami evaluate TAHAP  ──evaluate_existing──►     run_type = evaluation (artefak yang ada; waktu eksekusi tidak teramati)
app hal. 7             ──tracking.store──►        hanya membaca logs/ (D-010)
drive.push / pull      ──push_logs / pull_logs──► logs/ di Drive tim (lineage lintas lokal/Kaggle/Colab)
```

- **Terpusat & reusable.** Satu antarmuka (`@tracked`, `run_tracked`) dipakai keenam pipeline lewat CLI maupun notebook (sel
  notebook tidak berubah). Evaluator per tahap (`tracking.evaluators`) memakai metrik generik berpenjaga yang sama (`tracking.metrics`).
- **Tidak menduplikasi evaluasi.** Metrik yang sudah dihitung tahap (MAE, DM, silhouette vs plasebo, q BH, …) dibaca dari
  artefaknya. Hitung ulang hanya dipakai sebagai cek integritas: silhouette per k dari `response_features`, MAE dari
  `forecast_preds`.
- **Terpisah.** Metadata eksekusi (`runs/`), hasil evaluasi (`evaluations/`), dan galat (`errors/`) ada di file berbeda dengan
  ID run yang sama.
- **Tidak pernah ditimpa.** ID = `<tahap>-YYYYmmddTHHMMSSZ-<6 heks acak>`, ditulis dengan mode eksklusif (`open(..., "x")`).
- **Tetap jalan saat gagal.** Exception tahap dicatat lalu dilempar ulang. Galat saat menulis log hanya dicetak, tidak menutupi
  hasil atau galat tahap. Panggilan bertingkat, misalnya `stage0` yang memanggil `snapshot.run`, tetap satu run.
- **Privasi.** Path dicatat relatif (path registry + label `out_dir`/`artifact_dir`/`root`). Nama host dan nama pengguna tidak dicatat.
- **Nonaktif:** env `KAGAMI_TRACKING=0`.

## 2. Skema (`tracking.schemas`, `schema_version` 1)

| File | Isi |
|---|---|
| `logs/runs/<run_id>.json` | run_id, task_id, run_type (execution / evaluation), status (success / failed), started_at, finished_at (UTC), duration_s (None untuk evaluasi-saja), evaluation_s, pipeline_id, parent_run_ids, dataset_id, platform, python, git_commit, git_branch, config_sha256 (params.yaml, commodities.yaml), kind, algorithms, params (bagian params.yaml relevan + seed), call_args, inputs & outputs (ArtifactRef), peak_rss_mb, error_type, note |
| ArtifactRef | name, path, location, sha256, bytes, rows, columns, missing_cells, memory_mb (profil hanya untuk output), producer_run_id (input) |
| `logs/evaluations/<run_id>.json` | daftar Metric: name, group, value, status (ok / not_applicable / failed), reason (wajib bila bukan ok), context (artefak sumber, subset, n, catatan) |
| `logs/errors/<run_id>.json` | error_type, message, traceback |
| `logs/pipelines/<pipeline_id>.json` | started_at, finished_at, status, runs [{run_id, task_id, status}] |

**Dataset ID** = `raw:<12 heks>` dari pasangan (file, sha256) di `checksums.csv`. Kolom waktu tidak ikut dihitung, jadi snapshot
mentah yang sama menghasilkan ID yang sama walaupun `checksums.csv` ditulis ulang di folder lain. Bila snapshot tidak ada,
ID diwarisi dari run induk, atau `in:<hash input>`.

**Run induk.** Setiap input di-hash saat dibaca. Run induk adalah run sukses terakhir yang menulis file dengan sha256 sama.
Hubungan antar-tahap karena itu mengikuti data yang benar-benar dipakai.

**Hasil basi.** `store.staleness` dan `kagami runs` menandai tahap yang file inputnya sekarang berbeda dari yang dibaca run
terakhirnya. Artinya ada perubahan di hulu setelah tahap itu dijalankan.

## 3. Dependensi antar-tahap (dari REQUIRES/OPTIONAL, bukan linear)

```
snapshot → stage0 ─┬→ task1 ─┬→ task2              (daun: output tidak dibaca tahap lain)
                   │         ├→ task3 ← stage0 (exposure, province_features, regulation, …)
                   └→ task4 ─┴→ robustness ← task1 + stage0
```

`tracking.registry.dependency_edges()` membangunnya dari modul pipeline. Tes `test_dependency_edges_follow_requires` memastikan
task2 adalah daun dan task3 tidak bergantung pada task2.

## 4. Matriks tahap × metrik

Semua tahap juga mencatat metrik umum: waktu eksekusi, status, ukuran dataset per output (baris, kolom, sel kosong, memori),
memori puncak proses, algoritma, parameter, dataset ID, dan waktu. Sumber metrik selalu artefak yang disebut di `context.artifact`.

| Tahap | Jenis | Metrik (sumber) | Tidak berlaku (alasan dicatat) |
|---|---|---|---|
| snapshot | data | n_files, n_sources, total_mb (`checksums`) | – |
| stage0 | rekayasa data + daya | panel_cells, n_provinces, n_weeks, status_share_{observed, carry_forward, short, missing}, log_price_missing_share (`panel_weekly`); eligible_series/share (`eligibility`); n_episodes, max_cum_dlog_e, sd_de, n_depreciation/appreciation_weeks, world_price_missing_share; mde_pt8_* + n_mde_pt8_above_threshold (`mde`); price_spike_days (`pihps_daily` → `qa.flag_price_outliers`) | metrik ML (tidak ada model) |
| task1 | estimasi & inferensi | n_estimates_{national, region, province}, share_ci_excludes_zero_national, median_se_national (`profiles`); placebo_false_positive_rate (\|t\| > 1,96 di bawah null, harapan 0,05), n_placebo_reps (`placebo_stats`); boot_ratio_median_h{4,8,12}, n_bootstrap_reps (`boot_replicates`); n_event_episodes, share_events_placebo_p05 (`events`) | r2_in_sample: LP inferensial, residual tidak disimpan |
| task2 | clustering | h0_het_rejected, min_q_fdr_Q; selected_k, placebo_p95_silhouette, silhouette_k{2..6}, silhouette_margin_vs_placebo; partisi terpilih: n_clusters, cluster_sizes, wcss, silhouette/DB/CH, ward_labels_reproduced_ari, min_jaccard, n_weak_clusters, ari_kmeans_vs_ward; kandidat k ≥ 2: silhouette/davies_bouldin/calinski_harabasz_k{2..6} + silhouette_recompute_max_abs_diff; detection_delta_k{2,3}; ari_<partisi> | silhouette/DB/CH partisi terpilih & ARI saat k = 1 |
| task3 | asosiasi & uji | kendall_tau_b, kendall_p_exact, meta_n_p05, meta_n_q05; h2_n_confirmatory, h2_confirmatory_rejected, h2_n_ci_excludes_zero; e2_n_cells, e2_n_ci_excludes_zero, e2_min_q_fdr; cal_n_cells, cal_n_ci_excludes_zero, cal_n_q05; *_p_interval_consistency (+ mismatches) | – |
| task4 | regresi (peramalan) | resmi (`forecast_eval`): mae/rmse/mae_ratio_vs_m1/dm_p per h × model, h5_rejected, h5_min_p_holm; dihitung ulang (`forecast_preds`): h{h}_{model}_{mae, mse, rmse, r2, r2_oos_vs_zero}, mae_crosscheck_max_abs_diff; share_fx_improves (`ablation`) | mape: ± 9% y_true = 0 (selisih log tanpa perubahan harga); dm_p M2_nofx = M1 |
| robustness | robustness | n_rows_tier_{1,2,V}, share_baseline_in_ci_tier_{1,2}, v4_mean_sign_agree, v4_mean_corr (`robustness`) | – |

**Keluarga yang tidak berlaku untuk seluruh proyek** (`registry.NOT_APPLICABLE_FAMILIES`, ditampilkan di app):

| Keluarga | Alasan |
|---|---|
| Klasifikasi (accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix) | tidak ada tahap klasifikasi berlabel; klaster Task 2 tidak punya ground truth |
| Reduksi dimensi (explained variance, reconstruction error) | tidak ada PCA/SVD/embedding |
| NLP (BLEU, ROUGE, perplexity, vocabulary, OOV) | tidak ada data teks yang dimodelkan |

## 5. Integritas evaluasi

- **Silhouette, DB, CH** hanya dihitung bila 2 ≤ k ≤ n − 1 dan matriks tanpa NaN. Partisi terpilih saat ini k = 1, jadi ketiganya
  tidak berlaku. Untuk kandidat k ≥ 2 ketiganya hanya deskriptif. Pemilihan k tetap memakai aturan plasebo (D-004).
- **Konsistensi p–interval** (p < α ⇔ interval tidak memuat nol) dicatat untuk meta-regresi, H2, dan inferensi terkalibrasi.
  Pada H2, ketidakcocokan memang diharapkan karena p berasal dari Wald dan interval laporan = Wald ∪ bootstrap (D-127). Catatan ini
  ada di konteks metriknya.
- **Peramalan:** hanya galat out-of-sample dari evaluasi rolling-origin yang dipakai (latih t + h ≤ origin, as-of `available_at`;
  `features.forecast.split_origin`). Tidak ada split acak dan tidak ada metrik dalam-sampel. MAE yang dihitung ulang harus sama dengan
  `forecast_eval` (cek silang).
- **Nilai yang tidak bisa dihitung** berstatus `not_applicable` atau `failed` dengan alasan, tidak pernah diisi nilai pengganti.
  NaN/inf otomatis menjadi `failed`.

## 6. Penggunaan

```
python -m kagami task3                 # tahap apa pun → logs/runs, logs/evaluations (atau logs/errors)
python -m kagami evaluate all          # evaluasi artefak yang ada (mis. hasil Kaggle) tanpa menjalankan ulang
python -m kagami runs                  # riwayat + hasil basi
python -m kagami app                   # halaman 7: ringkasan, metrik per tahap, perbandingan, alur pipeline, riwayat
```

Notebook tidak perlu diubah: `pipelines.<tahap>.run` sudah bertanda `@tracked`. `drive.push` mengunggah log baru, dan `drive.pull`
menarik log anggota lain.

## 7. Keterbatasan

- Run yang terjadi sebelum WP-36 (Task 1 dan Task 4 di Kaggle/Colab) hanya punya log evaluasi-saja, tanpa waktu eksekusi teramati.
  Lineage-nya lengkap sejak run berikutnya.
- `peak_rss_mb` adalah puncak proses sampai akhir run. Pada `kagami all` nilainya kumulatif antar tahap, bukan per tahap.
- Hash file parquet bisa berbeda antar versi pyarrow walaupun isinya sama. Bandingkan isi tabel bila perlu memastikan reproduksi.
- Log yang di-commit ikut terbaca app daring. Log dari Kaggle baru terlihat di app setelah `drive-pull` dan commit.
