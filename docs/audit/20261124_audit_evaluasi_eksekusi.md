# Audit Halaman 7 — Evaluasi & Riwayat Eksekusi

Tanggal audit: 2026-11-24 · Halaman: `http://localhost:8501/Evaluasi_Eksekusi` (5 bagian, `?bagian=...`)
Sumber yang diperiksa: tampilan app di browser (viewport 1400×1000), kode `app/pages/7_Evaluasi_Eksekusi.py`,
`src/tracking/` (evaluators, metrics, store, registry), 12 log run + 12 log evaluasi + 1 log pipeline di `logs/`, dan
artefak `results/` serta `data/interim/forecast_preds.parquet` untuk uji silang independen.

Catatan bertanggal (bukan dokumen hidup): angka di sini menggambarkan keadaan `logs/` dan `results/` pada 2026-11-24.

> **Pembaruan 2026-11-24 (sore).** §0–§7 adalah audit awal (12 run) dan dibiarkan apa adanya sebagai jejak. Sesudahnya
> dikerjakan D-140 (perbaikan halaman 7 & pelacakan), D-141 (klasifier arah) dan D-142 (model deep & TimesFM 3.0).
> Keadaan terkini dan kelemahan yang **masih** ada ada di **Lampiran C** (23 run, 6 eksekusi); status tiap temuan awal ada
> di Lampiran B.

---

## 0. Ringkasan eksekutif

Halaman 7 **berfungsi**: 12/12 run berhasil, 0 metrik gagal dihitung, cek integritas lolos (silhouette dihitung ulang
selisih 5,6e-17; MAE dihitung ulang selisih 8,3e-17), tidak ada tahap basi. Kelemahannya ada di tiga lapis:

| # | Kelemahan | Lapis | Bobot |
|---|---|---|---|
| 1 | Banyak skor "≈ 0,5" berarti **setara peluang/acak**, padahal statusnya "ok". Contohnya kesepakatan tanda LP vs event study 0,508, akurasi arah 0,54–0,60, ROC-AUC 0,57–0,63, dan porsi interval nasional yang tidak memuat nol 6,25% (≈ α 5%). Halaman tidak membedakan "berhasil dihitung" dari "hasilnya bagus". | substansi + penyajian | tinggi |
| 2 | Akurasi arah Task 4 dilaporkan dengan n ≈ 22 ribu tanpa ketidakpastian. Bootstrap per origin (76/75 origin) menunjukkan **M1 dan M2 tidak dapat dibedakan dari baseline kelas mayoritas**; hanya M3 yang lebih baik (+1,3..+8,7 poin). | metode evaluasi | tinggi |
| 3 | Per komoditas, akurasi arah untuk **komoditas diatur (beras, daging sapi, gula, minyak goreng) di bawah baseline mayoritas di semua model**. Rata-rata gabungan menutupi hal ini. | substansi | tinggi |
| 4 | Fitur kurs **memperburuk** MAE paling besar justru pada grup fokus impor langsung: daging sapi M2/M1 1,25 (h 4) dan 1,30 (h 8), gula 1,20 dan 1,13. `share_fx_improves` = 0,25. | substansi | tinggi (sudah konsisten dengan H5 tidak didukung) |
| 5 | `M2_nofx` **identik** dengan M1 (MAE, RMSE, confusion matrix sama persis). Ablation hanya mengulang perbandingan M2 vs M1 dan tidak menambah informasi. | desain evaluasi | sedang |
| 6 | Tier 1 robustness "baseline dalam interval" 95,8% tampak kuat, tetapi lebar interval median 0,83 dan hanya 10–19% estimasi cek yang intervalnya tidak memuat nol. Kriteria ini hampir pasti lolos. | metode evaluasi | sedang |
| 7 | Log hanya punya **4 run eksekusi** (stage0, task3, robustness, task2). Task 1 dan Task 4, tahap paling berat, tidak pernah tercatat sebagai eksekusi di `logs/` ini. Log run end-to-end 1,9 jam (2026-11-24) tidak ada di folder ini. | kelengkapan log | sedang |
| 8 | Run `robustness` terakhir (eksekusi, 486 baris, **tanpa Tier 2**) bukan produsen artefak resmi (679 baris, sha `2e5db241b2a6`). Tabel "Status terakhir per tahap" menampilkannya, sedangkan cek "basi" hanya memeriksa input, bukan output. | lineage | sedang |
| 9 | `task2` membaca `province_features` tetapi tidak mendeklarasikannya di `OPTIONAL`. Akibatnya sisi Tahap 0 → Task 2 hilang dari graf, dan notebook 02 tidak menarik file itu dari Drive, sehingga pembanding `n_kota` diam-diam dilewati di cloud. | wiring | sedang |
| 10 | Sejumlah cacat UI: rerata waktu eksekusi lintas tahap tidak bermakna, "None" tampil apa adanya, label status berbahasa Inggris, angka sisi graf tidak terbaca, default Perbandingan run kosong, "hanya metrik yang berubah" menghitung metrik baru sebagai perubahan. | UI | rendah–sedang |

Batas klaim (CLAUDE.md §1.6): hasil nol, k = 1, dan rasio MAE ≈ 1 **sah sebagai hasil penelitian**. Kelemahan nomor 1,
3, dan 4 bukan bug. Kelemahannya ada pada cara halaman menyajikannya: seolah-olah semua "ok" berarti baik, dan tanpa
pembanding peluang/ketidakpastian.

---

## 1. Bagian A — Ringkasan (`?bagian=Ringkasan`)

### 1.1 Isi yang tampil

Kartu metrik (dua baris × 3):

| Kartu | Nilai | Keterangan |
|---|---|---|
| Total run | 12 | eksekusi + evaluasi-saja |
| Berhasil | 12 | |
| Gagal | 0 | |
| Rerata waktu eksekusi | 235.4 dtk | rerata 4 run eksekusi: 41,5 + 765,2 + 14,6 + 120,4 |
| Run eksekusi | 4 | |
| Run terakhir | berhasil | `task4-20261124T001725Z-2da66d` |

Tabel "Status terakhir per tahap":

| Tahap | Run terakhir | Jenis | Status | Mulai (UTC) | Waktu (dtk) | Ringkasan evaluasi |
|---|---|---|---|---|---|---|
| Snapshot · data mentah | snapshot-20261123T200517Z-feaae6 | evaluation | success | 2026-11-23 20:05:17 | None | 3 ok · 0 tidak berlaku · 0 gagal |
| Tahap 0 · fondasi data | stage0-20261123T200517Z-a43730 | evaluation | success | 20:05:17 | None | 21 · 0 · 0 |
| Task 1 · profil respons | task1-20261123T200519Z-82c747 | evaluation | success | 20:05:19 | None | 13 · 1 · 0 |
| Task 2 · pola regional | task2-20261123T201444Z-c1d5fb | execution | success | 20:14:44 | 120.404 | 35 · 8 · 0 |
| Task 3 · asosiasi & uji | task3-20261123T200523Z-08f018 | evaluation | success | 20:05:23 | None | 19 · 0 · 0 |
| Task 4 · evaluasi prediktif | task4-20261124T001725Z-2da66d | evaluation | success | 2026-11-24 00:17:25.305500 | None | 202 · 40 · 0 |
| Robustness & validasi | robustness-20261123T201429Z-1b649e | execution | success | 20:14:29 | 14.565 | 5 · 0 · 0 |

Grafik "Waktu eksekusi per run" berisi 4 titik (stage0 41,5 dtk; task3 765,2 dtk; robustness 14,6 dtk; task2 120,4 dtk).
Subjudulnya: "4 run eksekusi · 8 run evaluasi-saja tanpa waktu eksekusi teramati". Nama tahap hanya muncul saat hover.

Expander "Keluarga metrik yang tidak berlaku" memuat 3 baris: klasifikasi (dipakai hanya untuk diagnostik arah
Task 4, D-139), reduksi dimensi (tidak ada PCA/SVD), dan NLP (tidak ada data teks).

### 1.2 Kelemahan bagian ini

1. **Rerata waktu eksekusi 235,4 dtk tidak bermakna.** Angka itu merata-ratakan tahap yang sangat berbeda (task3
   765 dtk vs robustness 15 dtk) dan tidak memuat Task 1 (bootstrap + plasebo ± 5.312 dtk) maupun Task 4. Waktu per
   tahap lebih informatif.
2. **"Total run 12 / Berhasil 12" memberi kesan lebih banyak yang dijalankan daripada kenyataannya.** 8 dari 12 run
   adalah evaluasi-saja, yaitu membaca artefak lama tanpa menjalankan ulang. Yang benar-benar dieksekusi hanya 4.
3. **Run terakhir per tahap ≠ produsen artefak resmi** (robustness, lihat §6.3).
4. Tampilan: kolom waktu menampilkan `None` (bukan "–" seperti di tempat lain). Nilai `evaluation`/`execution`/`success`
   tidak diterjemahkan, padahal antarmuka berbahasa Indonesia. Format waktu bercampur (dengan/tanpa mikrodetik, `+00:00`).
   Angka memakai titik desimal (`235.4`, `120.404`), tidak konsisten dengan format Indonesia di grafik (`fmt_num`).
5. Titik di grafik tidak berlabel tahap, dan dengan hanya 4 titik grafiknya hampir tidak memberi informasi. Bar per
   tahap (atau tabel) lebih jelas.

---

## 2. Bagian B — Evaluasi per tahap (`?bagian=Evaluasi+per+tahap`)

Struktur: pilih tahap + run → keterangan (jenis, algoritma, dataset `raw:c96ce7572b4c`, commit, platform `local`) →
3 kartu (ok / tidak berlaku / gagal) → filter kelompok → tabel metrik (kelompok, metrik, nilai, status, alasan,
konteks data). Untuk Task 4 ada tambahan tabel arah perubahan + confusion matrix. Lalu tren metrik antar run, dan
expander input/output (sha256, baris, kolom, run produsen). Default yang terbuka: Task 4, run terbaru.

Di bawah ini seluruh metrik run terbaru setiap tahap (status "ok" kecuali ditandai).

### 2.1 Snapshot · data mentah (1 run, evaluasi-saja)

| Metrik | Nilai |
|---|---|
| n_files | 28 |
| n_sources | 24 |
| total_mb | 18,53 |

### 2.2 Tahap 0 · fondasi data (run evaluasi `a43730`; identik dengan run eksekusi `3df742`)

| Kelompok | Metrik | Nilai | Penilaian |
|---|---|---|---|
| kualitas data panel | panel_cells / n_provinces / n_weeks | 157.760 / 34 / 464 | sesuai kontrak |
| | status_share_observed | 0,492 | |
| | status_share_carry_forward | 0,492 | tinggi, tetapi kekakuan harga nyata (U22) |
| | status_share_short / missing | 0,0055 / 0,0103 | |
| | log_price_missing_share | 0,0103 | |
| kelayakan seri | eligible_series / share | 337 / 0,991 | baik |
| penggerak & episode | n_episodes / max_cum_dlog_e | 13 / 0,185 | |
| | sd_de | 0,0082 | variasi kurs mingguan kecil → daya uji rendah |
| | depresiasi / apresiasi (minggu) | 259 / 200 | |
| | world_price_missing_share | 0,0058 | |
| daya statistik (MDE) | mde_pt8 bawang putih / gula / minyak goreng | 2,52 / 0,90 / 0,47 | 2 dari 3 di atas ambang 0,5 |
| | n_mde_pt8_above_threshold | 2 | |
| QA | price_spike_days | 59 | ditandai, tidak dihapus |

### 2.3 Task 1 · profil respons (1 run, evaluasi-saja)

| Metrik | Nilai | Pembanding / arti |
|---|---|---|
| n_estimates national / region / province | 598 / 4.186 / 14.066 | |
| **share_ci_excludes_zero_national** | **0,0625** (3 dari 48) | ≈ α = 0,05 → secara agregat setara dengan yang diharapkan dari derau |
| median_se_national | 0,142 | |
| r2_in_sample | tidak berlaku | LP untuk inferensi koefisien |
| n_placebo_reps / n_bootstrap_reps | 499 / 499 | |
| **placebo_false_positive_rate** | **0,081** (n = 19.452) | harapan 0,05 → SE cluster minggu terlalu sempit ± 1,6× |
| **boot_ratio_median h4 / h8 / h12** | **0,57 / 0,35 / 0,35** | harapan ≈ 1 → bootstrap menarik β ke nol (U107) |
| n_event_episodes | 13 | |
| **share_events_placebo_p05** | **0,053** (n = 390) | ≈ α = 0,05 → event study tidak lebih sering "signifikan" daripada peluang |

### 2.4 Task 2 · pola regional (run eksekusi `c1d5fb` = run evaluasi `0a4cf0`)

| Kelompok | Metrik | Nilai |
|---|---|---|
| heterogenitas | h0_het_rejected | 2 (daging ayam, telur ayam) dari 10 |
| | min_q_fdr_Q | 0,040 |
| pemilihan k | selected_k | 1 |
| | placebo_p95_silhouette | 0,196 |
| | silhouette k2..k6 | 0,167 / 0,184 / 0,178 / 0,145 / 0,144 |
| | silhouette_margin_vs_placebo | −0,012 |
| partisi terpilih | n_clusters / sizes / wcss | 1 / [34] / 680 |
| | silhouette, DB, CH | tidak berlaku (k = 1) |
| | ward_labels_reproduced_ari | 1,0 |
| | min_jaccard / n_weak_clusters | 1,0 / 0 (trivial untuk k = 1) |
| | ari_kmeans_vs_ward | tidak berlaku |
| kandidat k ≥ 2 | DB k2..k6 | 1,84 / 1,58 / 1,43 / 1,62 / 1,57 |
| | CH k2..k6 | 7,71 / 7,11 / 6,49 / 6,10 / 5,76 |
| | silhouette_recompute_max_abs_diff | 5,6e-17 (integritas lolos) |
| | candidate_note | teks catatan (bukan metrik) |
| batas deteksi | detection_delta k2 / k3 | 0,2 / 0,2 |
| pembanding partisi | ari zona HET / Jawa / 7 wilayah / n_kota | tidak berlaku (k = 1) |

Temuan tambahan dari uji silang: **WCSS 680 = 34 × 20, bukan 34 × 33.** Dari 33 fitur clustering, **13 konstan di
semua provinsi** (τ² = 0 → EB menyusutkan semua provinsi ke rerata): R4/R8/R12 bawang putih, R4/R8/R12 minyak goreng,
R8 daging sapi, R12 daging ayam, W4/W12 daging ayam, W8/W12 telur ayam, W4 gula. Jadi 39% dimensi tidak membawa
informasi. Silhouette 0,14–0,18 dihitung di ruang efektif 20 dimensi.

### 2.5 Task 3 · asosiasi & uji (run evaluasi `08f018` = run eksekusi `540ce9`)

| Kelompok | Metrik | Nilai | Arti |
|---|---|---|---|
| E1 & meta-regresi | kendall_tau_b / p eksak | −0,045 / 0,930 | tidak terdeteksi |
| | meta_n_p05 / meta_n_q05 | 0 / 0 | tidak ada asosiasi |
| | meta_p_interval_consistency | 1,0 (0 ketidakcocokan) | perbaikan D-132 bekerja |
| H2 | h2_n_confirmatory / rejected | 2 / 0 | |
| | h2_n_ci_excludes_zero | 0 dari 30 | |
| | **h2_p_interval_consistency** | **0,867 (4 ketidakcocokan)** | p Wald < 0,05 tetapi interval laporan memuat nol (disengaja D-127, tetapi tampil "ok") |
| E2 | e2_n_cells / ci_excludes_zero / min q | 145 / 15 / 0,145 | 10% sel "signifikan" tanpa satu pun lolos BH |
| terkalibrasi | cal_n_cells / ci_excludes_zero / n_q05 | 48 / 7 / 4 | |
| | cal_p_interval_consistency | 1,0 | |

### 2.6 Task 4 · evaluasi prediktif (run terbaru `2da66d`: 202 ok, 40 tidak berlaku)

**Evaluasi rolling-origin resmi (semua seri, semua origin):**

| h | Model | MAE | RMSE | MAE / M1 | DM p |
|---|---|---|---|---|---|
| 4 | M0 | 0,0749 | 0,1481 | 1,017 | 0,062 |
| 4 | M1 | 0,0736 | 0,1415 | 1,000 | – |
| 4 | M2 | 0,0747 | 0,1416 | 1,014 | 0,001 |
| 4 | M2_nofx | 0,0736 | 0,1415 | 1,000 | tidak berlaku |
| 4 | M3 | 0,0768 | 0,1459 | 1,044 | 0,031 |
| 8 | M0 | 0,1053 | 0,1964 | 1,016 | 0,161 |
| 8 | M1 | 0,1036 | 0,1891 | 1,000 | – |
| 8 | M2 | 0,1053 | 0,1890 | 1,017 | 0,006 |
| 8 | M2_nofx | 0,1036 | 0,1891 | 1,000 | tidak berlaku |
| 8 | M3 | 0,1052 | 0,1874 | 1,015 | 0,494 |

h5_rejected = tidak · h5_min_p_holm = 1,0.

**Galat out-of-sample dihitung ulang** (cek MAE vs artefak: selisih maks 8,3e-17):

| Kunci | R² | R² vs ramalan nol |
|---|---|---|
| h4 M0 / M1 / M2 / M3 | −0,0005 / 0,086 / 0,085 / 0,029 | 0 / 0,087 / 0,086 / 0,029 |
| h8 M0 / M1 / M2 / M3 | −0,0014 / 0,072 / 0,072 / 0,088 | 0 / 0,073 / 0,074 / 0,090 |

MAPE tidak berlaku untuk semua model: 3.672 dari 25.612 (h 4) dan 2.345 dari 25.274 (h 8) y_true = 0.

**Arah perubahan (diagnostik D-139; M0 tidak berlaku):**

| Kunci | Akurasi | Baseline mayoritas | Balanced | F1 naik | F1 turun | F1 makro | MCC | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|---|---|
| h4 M1 | 0,543 | 0,527 | 0,539 | 0,589 | 0,486 | 0,538 | 0,079 | 0,567 | 0,577 |
| h4 M2 | 0,557 | 0,527 | 0,552 | 0,606 | 0,494 | 0,550 | 0,105 | 0,575 | 0,583 |
| h4 M3 | 0,573 | 0,527 | 0,568 | 0,623 | 0,509 | 0,566 | 0,138 | 0,587 | 0,595 |
| h8 M1 | 0,560 | 0,545 | 0,552 | 0,614 | 0,488 | 0,551 | 0,106 | 0,569 | 0,589 |
| h8 M2 | 0,560 | 0,545 | 0,551 | 0,620 | 0,479 | 0,549 | 0,104 | 0,572 | 0,591 |
| h8 M3 | 0,602 | 0,545 | 0,594 | 0,651 | 0,537 | 0,594 | 0,192 | 0,627 | 0,643 |

(M2_nofx = M1 persis di setiap kolom.) Recall "turun": 0,456 / 0,457 / 0,467 (h 4) dan 0,462 / 0,445 / 0,507 (h 8).
Confusion matrix default h8 M3: aktual naik → 8.517 benar (68,1%), 3.983 salah; aktual turun → 5.137 salah (49,3%),
5.292 benar (50,7%); n = 22.929, 2.345 perubahan nol dikeluarkan, porsi naik 54,5%.

**Ablation:** share_fx_improves = 0,25 (5 dari 20 sel komoditas × h; hanya cabai merah, cabai rawit, dan minyak goreng
h 8 yang membaik, dengan selisih ≤ 0,0009).

### 2.7 Robustness & validasi

| Metrik | Run eksekusi `1b649e` (terbaru) | Run evaluasi `1c684f` (= artefak resmi) |
|---|---|---|
| n_rows_tier_1 / share_baseline_in_ci_tier_1 | 382 / 0,958 | 382 / 0,958 |
| n_rows_tier_2 / share_baseline_in_ci_tier_2 | **tidak ada** | 193 / 0,990 |
| n_rows_tier_V | 104 | 104 |
| **v4_mean_sign_agree** | **0,508** | 0,508 |
| **v4_mean_corr** | **0,142** | 0,142 |

### 2.8 Kelemahan bagian ini

1. **Status "ok" disalahartikan sebagai "bagus".** Status hanya berarti metrik *berhasil dihitung*. Tidak ada kolom
   pembanding (nilai acuan peluang, α, ambang) atau penilaian (di atas/di bawah acuan). Akibatnya 0,508, 0,0625, dan
   0,053 tampil sama hijaunya dengan cek integritas 5,6e-17.
2. **Tanpa ketidakpastian pada metrik arah** (lihat §6.2). Tabel menampilkan 4 desimal dari n ≈ 22 ribu, padahal
   observasi bertumpuk antar origin dan antar seri.
3. **Agregasi menutupi per komoditas**: tabel arah hanya level ALL (lihat §6.2).
4. **Metrik ganda dan non-metrik:** `silhouette_k2..k6` muncul di dua kelompok; `candidate_note` adalah kalimat yang
   diberi status ok; `M2_nofx` menambah 14 metrik arah dan 5 metrik galat yang identik dengan M1.
5. **Tren metrik antar run** default ke `dm_p_h4_M0` (urutan alfabet) dan hanya memplot 2 run evaluasi-saja dari
   artefak yang sama, sehingga selalu datar. Untuk tahap yang semua runnya membaca artefak identik, tren tidak membawa
   informasi.
6. Format angka tabel `.4g` dengan titik desimal, tidak konsisten dengan format Indonesia di grafik.
7. Untuk Task 1 dan Task 4 tidak ada run eksekusi, sehingga keterangan "waktu eksekusi tidak teramati" selalu muncul.

---

## 3. Bagian C — Perbandingan run (`?bagian=Perbandingan+run`)

### 3.1 Isi

Pilih tahap → pilih ≥ 2 run (pertama = acuan) → tabel metrik + delta (toggle "Hanya metrik yang berubah", default on)
→ "Perbedaan konfigurasi & lingkungan" → "Artefak input/output (sha256)".

Hasil untuk semua tahap yang punya ≥ 2 run:

| Tahap | Run dibandingkan | Metrik berubah | Beda konfigurasi | Artefak berubah |
|---|---|---|---|---|
| Snapshot | hanya 1 run | – | – | – |
| Tahap 0 | a43730 vs 3df742 | 0 dari 21 | tidak ada | output `checksums` (run evaluasi tidak mencatatnya: None vs `55ef1efe8d1c`) |
| Task 1 | hanya 1 run | – | – | – |
| Task 2 | c1d5fb vs 0a4cf0 | 0 dari 35 | tidak ada | input `province_features` hanya tercatat di run eksekusi |
| Task 3 | 08f018 vs 540ce9 | 0 dari 19 | tidak ada | tidak ada (4 output identik) |
| Task 4 | 2da66d vs 12368a | 112 dari 202 | git_commit 6c43a7a1 vs f01ccc37 | tidak ada (3 output identik) |
| Robustness | 1b649e vs 1c684f | 2 (Tier 2 hilang) | tidak ada | output `robustness` `e177d02aecb6` vs `2e5db241b2a6` |

### 3.2 Kelemahan bagian ini

1. **Default tahap = Snapshot, yang hanya punya 1 run** → halaman langsung menampilkan "Pilih minimal dua run".
   Default sebaiknya tahap pertama yang punya ≥ 2 run.
2. **"Hanya metrik yang berubah" menghitung metrik baru sebagai perubahan.** Untuk Task 4, 112 baris "berubah" seluruhnya
   adalah metrik arah D-139 yang belum ada di run lama (NaN vs nilai). Tidak ada satu pun nilai yang benar-benar berubah,
   dan delta-nya NaN. Status "baru"/"hilang" perlu dipisah dari "berubah".
3. **Beda kode tidak terdeteksi.** Perbedaan commit tercatat, tetapi `git_info` tidak mencatat working tree kotor. Saat
   audit ada 13 file termodifikasi yang belum di-commit, jadi commit `6c43a7a1` tidak mewakili kode yang menghasilkan
   metrik.
4. **Lineage tidak konsisten antara run eksekusi dan evaluasi-saja** (Task 2 `province_features`, Tahap 0 `checksums`),
   sehingga perbandingan sha256 memberi sinyal "berubah" palsu.
5. Perbandingan bermakna hanya terjadi pada robustness, dan isinya justru menunjukkan run yang lebih baru *lebih sedikit*
   cakupannya (tanpa Tier 2). Halaman tidak memberi peringatan.

---

## 4. Bagian D — Alur pipeline (`?bagian=Alur+pipeline`)

### 4.1 Isi

Graf 7 simpul (Snapshot → Tahap 0 → Task 1/Task 4 → Task 2/Task 3/Robustness), warna = status run terakhir (semua
"berhasil"), garis penuh = input wajib, titik-titik = opsional, angka = jumlah artefak. Tabel 35 sisi
(produsen, artefak, konsumen, wajib/opsional). Tidak ada peringatan basi (cek `staleness`: 35 input, semua sha cocok).
Tabel `kagami all`: `pipeline-20261123T200100Z-bcc0ba`, success, stage0 → task3 → robustness → task2.

Ringkasan sisi:

| Produsen → Konsumen | Wajib | Opsional |
|---|---|---|
| Snapshot → Tahap 0 | checksums | |
| Tahap 0 → Task 1 | drivers_weekly, world_prices_weekly, episodes, panel_weekly_region, eligibility | panel_weekly |
| Tahap 0 → Task 3 | exposure, province_features | panel_weekly, eligibility, drivers_weekly, world_prices_weekly, regulation, mde |
| Tahap 0 → Task 4 | panel_weekly_region, drivers_weekly, world_prices_weekly | panel_weekly |
| Tahap 0 → Robustness | episodes, panel_weekly, eligibility, drivers_weekly, world_prices_weekly | |
| Task 1 → Task 2 | profiles, response_features, placebo_stats, boot_replicates | |
| Task 1 → Task 3 | response_features | profiles, boot_replicates, placebo_stats |
| Task 1 → Robustness | profiles, events | |
| Task 4 → Robustness | forecast_eval | |

### 4.2 Kelemahan bagian ini

1. **Sisi hilang: Tahap 0 → Task 2 (`province_features`).** `pipelines/task2.py` baris 47–48 membacanya bila ada,
   tetapi tidak ada di `REQUIRES`/`OPTIONAL`. Dampaknya nyata: notebook 02 menarik `REQUIRES + OPTIONAL` dari Drive
   (D-122), jadi di Kaggle/Colab pembanding `n_kota` di `partition_compare` diam-diam dilewati.
2. **Cek "basi" hanya melihat input.** Kasus robustness (output run terakhir ≠ artefak resmi) tidak terdeteksi. Begitu
   pula artefak yang diganti tangan (unduh Drive) setelah run terakhir.
3. **"Berhasil" di graf = status run terakhir, termasuk run evaluasi-saja.** Task 1 dan Task 4 tampil hijau padahal tidak
   pernah dieksekusi di bawah pelacakan di folder ini.
4. **Angka jumlah artefak di sisi tidak terbaca**: font 10 px berwarna sama dengan garis (`S.NEUTRAL`) dan ditimpa garis.
5. Log `kagami all` hanya memuat 4 tahap (tanpa snapshot, task1, task4). Itu bukan run "all" penuh, karena run
   end-to-end lengkap dilakukan di folder lain dan lognya tidak dibawa ke sini.

---

## 5. Bagian E — Riwayat (`?bagian=Riwayat`)

### 5.1 Isi

Filter tahap / status / jenis run → tabel 12 run terbaru di atas, dengan kolom run_id, tahap, mulai (UTC), dataset,
algoritma, status, jenis, waktu eksekusi, ringkasan evaluasi, git_commit, platform, error_type.

| Mulai (UTC) | Run | Jenis | Waktu (dtk) | Ringkasan |
|---|---|---|---|---|
| 2026-11-24 00:17:25 | task4-…-2da66d | evaluation | – | 202 · 40 · 0 |
| 2026-11-23 20:14:44 | task2-…-c1d5fb | execution | 120,4 | 35 · 8 · 0 |
| 20:14:29 | robustness-…-1b649e | execution | 14,6 | 5 · 0 · 0 |
| 20:05:24 | robustness-…-1c684f | evaluation | – | 7 · 0 · 0 |
| 20:05:23 | task4-…-12368a | evaluation | – | 90 · 12 · 0 |
| 20:05:23 | task3-…-08f018 | evaluation | – | 19 · 0 · 0 |
| 20:05:23 | task2-…-0a4cf0 | evaluation | – | 35 · 8 · 0 |
| 20:05:19 | task1-…-82c747 | evaluation | – | 13 · 1 · 0 |
| 20:05:17 | stage0-…-a43730 | evaluation | – | 21 · 0 · 0 |
| 20:05:17 | snapshot-…-feaae6 | evaluation | – | 3 · 0 · 0 |
| 20:01:44 | task3-…-540ce9 | execution | 765,2 | 19 · 0 · 0 |
| 20:01:00 | stage0-…-3df742 | execution | 41,5 | 21 · 0 · 0 |

Semua: dataset `raw:c96ce7572b4c`, platform `local`, error_type kosong; commit `f01ccc37` kecuali run Task 4
terbaru (`6c43a7a1`).

### 5.2 Kelemahan bagian ini

1. Tidak ada riwayat cloud (Kaggle/Colab), sehingga klaim "Task 1 & 4 berikutnya di Kaggle tercatat otomatis" belum
   terbukti.
2. Kolom algoritma terpotong. Tidak ada filter tanggal dan tidak ada tautan dari baris ke bagian Evaluasi.
3. `error_type` selalu kosong: belum pernah ada run gagal yang tercatat, sehingga jalur log galat dan traceback di
   halaman belum teruji pada data nyata (hanya di tes).
4. 2 file log Task 4 terbaru (`logs/runs/task4-20261124T001725Z-2da66d.json` dan pasangannya di `logs/evaluations/`)
   belum di-track git. App daring tidak akan menampilkannya sampai di-commit.

---

## 6. Analisis kelemahan menyeluruh

### 6.1 "Skor masih ≈ 0,5": apa artinya per metrik

| Metrik | Nilai | Acuan peluang / null | Kesimpulan objektif |
|---|---|---|---|
| `v4_mean_sign_agree` (LP vs event study) | 0,508 (n = 30 sel) | 0,5 = lempar koin | Dua metode respons nasional **tidak sepakat soal tanda** lebih sering daripada peluang. Korelasi rerata 0,14 (−0,32 .. 0,89). Validasi V4 secara praktis **gagal memvalidasi**. Yang tercatat "26/30 sel cocok" mengacu pada kriteria interval, bukan tanda. Interval event study sangat lebar sehingga hampir semua "cocok". |
| Akurasi arah M1/M2 | 0,543–0,560 | baseline mayoritas 0,527 / 0,545 | Selisih +1,5..+3 poin. **Bootstrap per origin: interval selisih memuat nol** (M1 h4 −0,016..0,045; M2 h4 −0,008..0,061; M1 h8 −0,023..0,052; M2 h8 −0,019..0,050). Tidak lebih baik dari "selalu tebak naik". |
| Akurasi arah M3 | 0,573 / 0,602 | 0,527 / 0,545 | Satu-satunya yang di atas baseline (selisih +0,013..+0,075 dan +0,026..+0,087). Model ini memakai identitas seri, bukan kurs. |
| Balanced accuracy | 0,539–0,594 | 0,5 | Sedikit di atas acak. Kelas "turun" hampir acak (recall 0,45–0,51). |
| ROC-AUC | 0,567–0,627 | 0,5 | Daya pemisah lemah. Umumnya AUC < 0,7 dianggap lemah. |
| MCC | 0,079–0,192 | 0 | Korelasi lemah antara arah ramalan dan aktual. |
| R² out-of-sample | 0,07–0,09 (M0 ≈ 0) | 0 | Model menjelaskan < 10% variasi perubahan harga 4–8 minggu. |
| MAE M2 / M1 | 1,014 / 1,017 | 1 | Fitur kurs sedikit **memperburuk**, signifikan menurut DM (p 0,001 / 0,006). |
| `share_ci_excludes_zero_national` | 0,0625 (3/48) | 0,05 | Porsi temuan nasional setara laju positif palsu yang diharapkan. Dengan FPR plasebo 0,081, 3 dari 48 bahkan di bawah jumlah positif palsu yang diharapkan (≈ 3,9). |
| `share_events_placebo_p05` | 0,053 (n = 390) | 0,05 | Event study tidak mendeteksi lebih sering daripada peluang. |
| `share_fx_improves` | 0,25 (5/20) | 0,5 bila netral | Fitur kurs membantu di lebih sedikit sel daripada yang diharapkan bila fitur itu netral. |
| Silhouette maks | 0,184 | p95 plasebo 0,196 | Struktur lebih lemah dari 5% matriks acak terbaik → k = 1. |
| `boot_ratio_median` | 0,57 / 0,35 / 0,35 | 1 | Bootstrap merusak estimator (U107), sehingga interval resmi terlalu konservatif. |

**Diagnosis keseluruhan:** dengan sd(de) mingguan hanya 0,0082, sinyal kurs terhadap harga pangan eceran pada data ini
berada di bawah ambang deteksi untuk hampir semua sel. Konsistensinya kuat (LP, event study, H2, E1, meta-regresi,
clustering, dan Task 4 semuanya nol). Untuk penelitian ini, itu temuan yang sah dan dapat dipertahankan **asalkan**
ditulis sebagai batas atas, disertai MDE (CLAUDE.md §20). Yang lemah bukan kesimpulannya, melainkan dua hal:
(a) validasi silang V4 tidak bisa dipakai sebagai bukti kesesuaian metode; (b) diagnostik arah Task 4 berisiko dibaca
sebagai "akurasi 60%" padahal M1/M2 tidak lebih baik dari baseline.

### 6.2 Kelemahan metode evaluasi (lapisan `tracking`)

1. **Akurasi arah tanpa interval dan tanpa unit independen yang benar.** n = 21.940 / 22.929 berasal dari 76 / 75 origin
   × ± 300 seri. Seri dalam satu origin berkorelasi kuat (guncangan nasional yang sama), dan origin h 8 bertumpuk
   (langkah 4 minggu < horizon 8). Bootstrap per origin di atas pun masih optimistis karena origin bertumpuk.
   **Usulan:** tambahkan interval bootstrap blok per origin + selisih vs baseline ke `direction_metrics`, dan tampilkan
   di tabel.
2. **Baseline gabungan menyembunyikan kegagalan per komoditas.** Akurasi arah h 8 per komoditas:

   | Komoditas | M1 | M2 | M3 | Baseline mayoritas | Porsi y = 0 |
   |---|---|---|---|---|---|
   | beras | 0,555 | 0,570 | 0,558 | **0,678** | 0,23 |
   | daging sapi | 0,533 | 0,534 | 0,563 | **0,604** | 0,34 |
   | gula pasir | 0,511 | 0,547 | 0,617 | **0,604** | 0,15 |
   | minyak goreng | 0,508 | 0,597 | 0,531 | **0,616** | 0,14 |
   | bawang putih | **0,486** | **0,463** | 0,640 | 0,520 | 0,02 |
   | bawang merah | 0,602 | 0,607 | 0,699 | 0,508 | 0,00 |
   | cabai merah | 0,574 | 0,581 | 0,564 | 0,522 | 0,01 |
   | cabai rawit | 0,631 | 0,646 | 0,628 | 0,516 | 0,00 |
   | daging ayam | 0,603 | 0,547 | 0,591 | 0,511 | 0,01 |
   | telur ayam | 0,579 | 0,512 | 0,603 | 0,510 | 0,02 |

   Komoditas diatur (HET/HAP) berada di bawah baseline pada semua model, kecuali gula di M3. Bawang putih (impor langsung,
   grup fokus H5) di bawah 0,5 untuk M1 dan M2. Model hanya "menang" pada komoditas hortikultura dan unggas yang tidak
   diatur. **Usulan:** tabel arah per komoditas (atau per jalur H5) dengan baseline per kelompok.
3. **MAE M2/M1 per komoditas** memperlihatkan kerugian terbesar justru di grup fokus H5: daging sapi 1,252 (h 4, DM p <
   0,001) dan 1,296 (h 8), gula 1,204 dan 1,125, beras 1,137 (h 4). Fitur kurs menambah derau pada komoditas berharga kaku
   (carry_forward 85–92%). Ini konsisten dengan D-131 (pengumpulan lintas komoditas) dan perlu disebut di findings
   sebagai mekanisme, bukan sekadar "rasio ≈ 1".
4. **`M2_nofx` ≡ M1** (dicek: `np.allclose` benar di kedua horizon). Kelompok fitur yang di-drop ablation sama persis
   dengan selisih M2 − M1, jadi `ablation.delta_mae` = MAE(M1) − MAE(M2) per sel. Ablation tidak menguji apa pun yang
   baru. **Usulan:** ablation per kelompok fitur (kurs saja, harga dunia saja, episode saja), atau tandai terang-terangan
   di halaman bahwa ablation = M2 vs M1.
5. **Kriteria robustness Tier 1 "baseline dalam interval" terlalu longgar.** Lebar interval median 0,83 (satuan respons
   per log kurs). Hanya 10–19% estimasi cek yang intervalnya tidak memuat nol per jenis cek, dan kesamaan tanda 78–96%.
   Angka 95,8% terutama mencerminkan lebar interval, bukan kestabilan. **Usulan:** laporkan juga kesamaan tanda,
   |Δ estimasi| / SE baseline, dan porsi keputusan (terdeteksi/tidak) yang sama.
6. **`h2_p_interval_consistency` 0,867 berstatus "ok".** Ketidakcocokan memang disengaja (D-127), tetapi halaman
   menampilkannya sama dengan konsistensi 1,0 di tempat lain. Perlu status/penanda "diharapkan".
7. **Tidak ada metrik peramalan berskala**: MAPE tidak berlaku (y = 0), tetapi MASE / sMAPE / skill score vs M0
   per komoditas tidak dihitung. Pinball/coverage juga tidak ada karena Task 4 tidak menghasilkan interval prediksi.
8. **Fitur clustering konstan tidak dilaporkan.** 13/33 kolom nol varians tidak muncul sebagai metrik. Padahal ini
   menjelaskan mengapa silhouette rendah dan mengapa batas deteksi 0,2 dihitung di ruang yang lebih kecil.

### 6.3 Kelemahan pencatatan & lineage

1. **Cakupan eksekusi rendah:** 4/12 run adalah eksekusi; Task 1 dan Task 4 0 eksekusi. Log run end-to-end penuh
   (CLAUDE.md §2: `kagami all` + Tier 2, ± 1,9 jam, 35 artefak tereproduksi) tidak ada di `logs/` ini, sehingga halaman
   tidak bisa menunjukkan bukti reproduksi terkuat yang sebenarnya sudah dimiliki proyek. **Usulan:** salin
   `logs/` dari folder run bersih (tidak menimpa; nama file unik) agar riwayat itu tampil.
2. **Run terakhir ≠ produsen artefak resmi.** `robustness-20261123T201429Z-1b649e` menulis 486 baris (sha
   `e177d02aecb6`, tanpa Tier 2) di lokasi lain. File resmi `results/robustness.csv` (679 baris, sha `2e5db241b2a6`) hanya
   tercatat sebagai output run evaluasi-saja `1c684f`. **Usulan:** cek basi diperluas ke output: run terakhir dianggap
   tidak mewakili bila sha output-nya ≠ file di lokasi baca.
3. **Status kode tidak lengkap:** hanya hash commit, tanpa penanda dirty atau diff hash. Usulan: simpan `git_dirty` dan
   hash `git diff` (tanpa menjalankan git: bandingkan mtime/sha file `src/` dengan index tidak praktis; minimal sha256
   seluruh `src/**/*.py` sebagai `code_hash`).
4. **Deklarasi dependensi tidak lengkap** (`task2` → `province_features`). Usulan: `OPTIONAL = ("province_features",)`
   di `pipelines/task2.py` + tes wiring yang membandingkan `read_artifact`/`exists` di kode pipeline dengan
   `REQUIRES ∪ OPTIONAL`.
5. **Lineage evaluasi-saja tidak setara eksekusi** (input yang dibaca opsional bergantung pada jalur kode evaluator,
   bukan pipeline). Perbandingan sha antar jenis run jadi tidak apel-ke-apel.
6. Semua run `platform local`: jalur cloud (Kaggle Secret, `push_logs`/`pull_logs`) belum pernah menghasilkan log nyata.

### 6.4 Kelemahan UI (ringkas)

| Bagian | Masalah | Usulan |
|---|---|---|
| Ringkasan | rerata waktu lintas tahap; "None"; status Inggris; ISO bercampur; titik tanpa label | waktu per tahap (bar), "–", terjemahkan, format `YYYY-MM-DD HH:MM`, label tahap |
| Ringkasan | "Total/Berhasil 12" tidak memisah evaluasi-saja | kartu "Eksekusi berhasil 4/4" + "Evaluasi-saja 8" |
| Evaluasi | "ok" ≠ baik | kolom "acuan" (0,5 / α / baseline / 1) + penanda di atas/di bawah acuan |
| Evaluasi | arah hanya level ALL, tanpa interval | interval bootstrap origin + tabel per komoditas |
| Evaluasi | tren default `dm_p_h4_M0`, datar | default metrik utama tahap; sembunyikan bila semua run membaca artefak sama |
| Evaluasi | metrik ganda / teks sebagai metrik | buang duplikat silhouette, ubah `candidate_note` jadi caption |
| Perbandingan | default Snapshot (1 run) | default tahap pertama dengan ≥ 2 run |
| Perbandingan | metrik baru dihitung "berubah" | kolom status: baru / hilang / berubah / sama |
| Alur | angka sisi tak terbaca | warna kontras + latar label |
| Alur | basi hanya input; hijau untuk run evaluasi-saja | basi input + output; warna berbeda untuk "belum pernah dieksekusi" |
| Riwayat | algoritma terpotong, tanpa filter tanggal | tooltip/expander, filter rentang waktu |
| Semua | titik desimal di tabel | `fmt_num` (desimal koma) |

---

## 7. Rekomendasi berprioritas

| Prioritas | Tindakan | Alasan | Upaya |
|---|---|---|---|
| P1 | Tambah kolom acuan + penilaian (di atas/di bawah acuan) di tabel metrik | mencegah "0,5 = ok" dibaca sebagai baik | kecil |
| P1 | Interval bootstrap per origin untuk akurasi arah & selisih vs baseline; tampilkan bahwa M1/M2 tidak berbeda dari baseline | klaim jujur sesuai §20 | kecil–sedang |
| P1 | Tulis di findings: V4 tidak memvalidasi (kesamaan tanda 0,51); fitur kurs memperburuk sapi/gula | batas klaim, G8 | kecil |
| P1 | `task2.OPTIONAL = ("province_features",)` + tes wiring baca-vs-deklarasi | bug wiring nyata di cloud | kecil |
| P2 | Bawa log run end-to-end 2026-11-24 ke `logs/` (dan commit 2 log Task 4 baru) | bukti reproduksi tampil di app | kecil (`[HUMAN]` commit) |
| P2 | Cek basi pada output + tandai run yang bukan produsen artefak resmi | kasus robustness | sedang |
| P2 | Arah & MAE per komoditas / per jalur H5 di halaman 7 | agregat menutupi kegagalan komoditas diatur | sedang |
| P2 | Kriteria Tier 1 tambahan (tanda, |Δ|/SE) | 95,8% menyesatkan | kecil |
| P2 | Ganti `M2_nofx` dengan ablation per kelompok fitur atau beri label "= M2 vs M1" | ablation redundan | sedang (Task 4 ulang, Kaggle) |
| P3 | Metrik fitur konstan clustering (13/33), MASE/skill vs M0 | kelengkapan diagnostik | kecil |
| P3 | `code_hash` / dirty flag di RunRecord | reproduksibilitas | kecil |
| P3 | Perbaikan UI di §6.4 | keterbacaan | kecil |

Catatan: semua usulan bersifat diagnostik/penyajian. Mengubah uji praregistrasi (H5, MAE/DM resmi) setelah G6 berarti
DEVIASI PRAREGISTRASI (CLAUDE.md §13). Pembekuan hasil dijadwalkan 27 Nov.

---

## Lampiran A — Cara verifikasi ulang angka audit

- Tabel run & metrik: `tracking.store.runs_table(cfg)` dan `metrics_table(cfg)` (539 baris metrik dari 12 log evaluasi).
- Perbandingan: `tracking.store.compare_runs(cfg, [run_a, run_b])`.
- Bootstrap per origin akurasi arah: resample origin (2.000 replikasi, seed 1) dari `data/interim/forecast_preds.parquet`,
  y_true = 0 dikeluarkan, baseline = kelas mayoritas pada sampel bootstrap yang sama.
- Fitur konstan: `features.clustering.feature_matrix(cfg, response_features)` → kolom dengan std = 0.
- Robustness Tier 1: `results/robustness.csv`, `tier == 1`, lebar `ci_high − ci_low`, tanda `estimate × baseline_estimate`.

---

## Lampiran B — Tindak lanjut 2026-11-24 (D-140; diperbarui setelah D-141 & D-142)

| Temuan audit | Status | Implementasi |
|---|---|---|
| "ok" dibaca sebagai "bagus" (#1) | selesai | `tracking.assessment`: penilaian vs acuan (lebih baik / lebih buruk / belum terbukti berbeda / sesuai harapan / perlu ditinjau / informasi), kolom acuan, interval, interpretasi di halaman 7 |
| Akurasi arah tanpa ketidakpastian (#2) | selesai | `metrics.direction_bootstrap` (blok origin, 999 replikasi): interval untuk akurasi, selisih vs baseline, balanced acc., F1 makro, MCC, ROC-AUC, PR-AUC |
| Agregat menutupi per komoditas (#3) | selesai | `h{h}_dir_by_segment`: per komoditas, jalur eksposur, grup H5, kekakuan harga; tabel + forest di halaman 7 |
| Fitur kurs memperburuk sapi/gula (#4) | ditampilkan + diperluas | MAE / M1 per segmen; dikonfirmasi di model lain (TSMX_fx / TSMX 1,041 pada h 4, DM p 0,020); hasil resmi H5 tidak diubah |
| M2_nofx = M1 (#5) | sebagian | metrik `ablation_model_equals_m1` (perlu ditinjau). Ablation kurs yang bermakna kini ada di model lain: C2 − C1 (D-141), TSMX_fx − TSMX dan TFM_fx − TFM (D-142). Ablation per kelompok fitur pada M2 sendiri masih belum (butuh Task 4 ulang) |
| Kriteria Tier 1 longgar (#6) | selesai | lebar interval median, kesamaan tanda, porsi terdeteksi, \|Δ\|/SE, kesamaan keputusan per tier |
| Log eksekusi Task 1/4 tidak ada (#7) | sebagian | Task 4 kini punya 2 run eksekusi (klasifier 1.119 dtk, model deep 7.632 dtk), tetapi `forecast_preds`/`forecast_eval`/`ablation` resmi tetap hanya dievaluasi → status "sebagian dieksekusi". Task 1 masih "hanya dievaluasi"; log run folder lain sengaja tidak diimpor |
| Run terakhir ≠ produsen artefak (#8) | selesai | `store.artifact_sync` + `stage_states`; kartu & peringatan di Ringkasan, tabel di Alur pipeline |
| `province_features` tidak dideklarasikan (#9) | selesai | `task2.OPTIONAL`, juga `robustness.OPTIONAL` (Tier 2: `pihps_daily`, `exposure`, `province_features`); notebook 02/05 menariknya; `test_pipeline_reads_are_declared` |
| Cacat UI (#10) | selesai | lihat §6.4; semua usulan tabel itu diterapkan kecuali tooltip algoritma (diganti kolom lebar) |
| Dirty flag / code hash (§6.3.3) | selesai | RunRecord `code_sha256`, `git_dirty`, `environment` (schema 2) |
| 13/33 fitur konstan (§6.2.8) | selesai | `n_constant_features`, `effective_dimensions` (perlu ditinjau) |

Angka baru pada artefak resmi (selisih akurasi arah vs baseline mayoritas, interval 95% bootstrap blok origin):

| h | M1 | M2 | M3 |
|---|---|---|---|
| 4 | +0,017 (−0,023..0,044) | +0,030 (−0,007..0,058) | +0,046 (0,011..0,072) |
| 8 | +0,015 (−0,029..0,053) | +0,015 (−0,024..0,049) | +0,057 (0,021..0,088) |

Komoditas kaku (beras, daging sapi, gula, minyak goreng; carry_forward ≥ 50%), h 8: M1 −0,100 (−0,168..−0,037), M2 −0,061
(−0,123..−0,004), M3 −0,057 (−0,094..−0,018); semua lebih buruk dari selalu menebak arah terbanyak. Komoditas lentur: M1 +0,077
(0,008..0,096) dan M3 +0,119 (0,054..0,134) lebih baik; M2 tidak terbukti (−0,016..0,076).


---

## Lampiran C — Audit ulang setelah D-140, D-141, D-142 (2026-11-24, sore)

Sumber: `logs/` (23 run: 6 eksekusi, 17 evaluasi-saja, 0 gagal), `tracking.store.artifact_sync` / `stage_states`,
`tracking.assessment` pada evaluasi terbaru tiap tahap, render 5 bagian halaman 7 dengan `streamlit.testing` (0 exception).
Server 8501 yang lama masih memuat modul versi sebelum D-140 dan perlu di-restart; verifikasi visual dilakukan di server
terpisah (port 8502).

### C.1 Keadaan halaman 7 sekarang

**Ringkasan.** Eksekusi berhasil 6/6 · evaluasi-saja 17 · run gagal 0 · tahap belum dieksekusi 2 (Snapshot, Task 1) ·
artefak tidak sinkron 2 · metrik perlu perhatian 15 (7 "lebih buruk dari acuan", 8 "perlu ditinjau"; lihat C.3).

| Tahap | Status tahap | Eksekusi tercatat |
|---|---|---|
| Snapshot | hanya dievaluasi | – (snapshot dijalankan di dalam stage0) |
| Tahap 0 | dieksekusi | 41,5 dtk |
| Task 1 | hanya dievaluasi | – (artefak resmi dari Kaggle, sebelum pelacakan) |
| Task 2 | dieksekusi | 120,4 dtk |
| Task 3 | dieksekusi | 765,2 dtk |
| Task 4 | sebagian dieksekusi | klasifier arah 1.119 dtk; model deep 7.632 dtk; `forecast_*` resmi hanya dievaluasi |
| Robustness | dieksekusi · output tidak sinkron | 14,6 dtk (486 baris, tanpa Tier 2) vs file resmi 679 baris |

**Sinkron artefak** (37 artefak di registry): 26 sinkron, 8 hanya dievaluasi (5 artefak Task 1, `forecast_preds`,
`forecast_eval`, `ablation`), 2 tidak sinkron (`checksums`: hanya kolom `recorded_at`; `robustness`), 1 tanpa log
(`findings`, laporan manual). Tidak ada input basi.

**Penilaian dua lapis** (evaluasi terbaru tiap tahap):

| Tahap | Lebih baik | Belum terbukti | Lebih buruk | Perlu ditinjau | Sesuai harapan | Informasi | Tidak dihitung |
|---|---|---|---|---|---|---|---|
| Snapshot | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| Tahap 0 | 1 | 0 | 2 | 0 | 0 | 20 | 0 |
| Task 1 | 0 | 2 | 0 | 4 | 0 | 7 | 1 |
| Task 2 | 1 | 6 | 0 | 1 | 1 | 24 | 8 |
| Task 3 | 0 | 2 | 0 | 0 | 3 | 14 | 0 |
| Task 4 | 132 | 47 | 5 | 3 | 1 | 321 | 50 |
| Robustness | 0 | 1 | 0 | 0 | 0 | 16 | 0 |

**Task 4 kini memuat 559 metrik** dalam 7 kelompok: model deep & foundation 248, arah perubahan 140, klasifier arah 66,
galat dihitung ulang 61, evaluasi resmi 40, segmen 2 (tabel), ablation 2.

### C.2 Hasil eksploratif baru yang tampil (h = 8, interval 95% bootstrap blok origin)

| Model | MAE / M1 | Akurasi arah | Selisih vs baseline 0,545 |
|---|---|---|---|
| M2 (uji resmi H5) | 1,017 (DM p 0,006, lebih buruk) | 0,560 | −0,024..0,049 (belum terbukti) |
| M3 | 1,015 (DM p 0,49) | 0,602 | 0,021..0,088 |
| C2 klasifier + kurs | – | 0,617 | 0,034..0,108 |
| TimesFM 3.0 | **0,895 (DM p < 0,001)** | 0,623 | 0,026..0,122 |
| TimesFM 3.0 + kurs | 0,904 (DM p < 0,001) | 0,613 | 0,007..0,119 |
| PatchTST | 0,962 (DM p 0,15) | 0,596 | 0,008..0,092 |
| TSMixer | 0,966 (DM p 0,13) | 0,608 | 0,017..0,103 |
| TSMixer + kurs | 0,994 (DM p 0,84) | 0,601 | 0,004..0,100 |

Ablation kurs pada tiga keluarga model: C2 − C1 +0,009 (−0,007..0,027); TFM_fx / TFM MAE 1,010 (tidak nyata);
TSMX_fx / TSMX 1,029 (h 8) dan 1,041 (h 4, DM p 0,020, lebih buruk). Kurs tidak menambah akurasi di model mana pun.

### C.3 Metrik yang dinilai "lebih buruk" atau "perlu ditinjau"

| Tahap | Metrik | Nilai | Penilaian | Arti |
|---|---|---|---|---|
| Tahap 0 | mde_pt8_bawang_putih / gula_pasir | 2,52 / 0,90 | lebih buruk | daya rendah: efek di bawah MDE tidak terdeteksi |
| Task 1 | placebo_false_positive_rate | 0,081 | perlu ditinjau | SE cluster terlalu sempit (± 1,6×) |
| Task 1 | boot_ratio_median h4 / h8 / h12 | 0,57 / 0,35 / 0,35 | perlu ditinjau | bootstrap menarik β ke nol (U107) |
| Task 2 | n_constant_features | 13 dari 33 | perlu ditinjau | fitur tersusut habis (τ² = 0) |
| Task 4 | mae_ratio_vs_m1 M2 h4 / h8, M3 h4 | 1,014 / 1,017 / 1,044 | lebih buruk | DM p 0,001 / 0,006 / 0,031 |
| Task 4 | mae_ratio TSMX_fx vs TSMX h4 | 1,041 | lebih buruk | DM p 0,020 |
| Task 4 | share_fx_improves | 5/20 | lebih buruk | binomial p 0,041 |
| Task 4 | M2_nofx = M1 (2 metrik + cek) | – | perlu ditinjau | ablation resmi tidak informatif |

Semua ini **sesuai** dengan kesimpulan penelitian (hasil nol, daya rendah, keterbatasan inferensi yang sudah tercatat),
bukan bug baru. Penilaian membuatnya terlihat, bukan memperbaikinya.

### C.4 Kelemahan yang masih ada (objektif)

| # | Kelemahan | Bukti | Dampak | Usulan |
|---|---|---|---|---|
| 1 | **Belum ada run pada kode yang di-commit.** Semua 11 run sejak D-140 bertanda `git_dirty = True`, dan code hash berubah antar run (`24d15fb3…`, `01ff19e6…`, `86435c0e…`, `1b20f73d…`, `534e1aa1…`) karena kode diubah di tengah sesi | kolom working tree & code hash di Riwayat | run tidak bisa dipetakan ke satu commit; perbandingan run mencampur kode berbeda | commit, lalu `python -m kagami evaluate all` sekali lagi agar ada evaluasi bersih pada commit itu |
| 2 | **[DIATASI D-144]** **`robustness` resmi tetap tidak sinkron** (679 baris dari run di luar pelacakan; run tercatat terakhir 486 baris tanpa Tier 2) | Alur pipeline → Sinkron artefak | produsen file resmi tidak tercatat | `python -m kagami robustness --tier2` lokal (± 1 menit), lalu cek apakah isinya identik dengan file resmi sebelum mengganti |
| 3 | **Task 1 dan `forecast_*` Task 4 tidak pernah dieksekusi di bawah pelacakan folder ini** | status "hanya dievaluasi" / "sebagian dieksekusi" | waktu eksekusi & lineage tahap terberat tidak tampil | jalankan di Kaggle dengan `kagami_code.zip` baru lalu `drive-pull` log; atau terima sebagai keterbatasan tertulis |
| 4 | **[DIATASI D-143]** **Perbandingan berganda tanpa koreksi.** 30 perbandingan berpasangan akurasi arah dan 10 rasio MAE model deep dinilai masing-masing pada 95%; 5 dari 30 perbandingan "lebih baik" | Task 4, kelompok klasifier & deep | sekitar 1,5 positif palsu diharapkan dari 30 uji; hasil "lebih baik" yang tipis (mis. C2 − M3 h 4) rapuh | tambahkan q BH atau Holm per keluarga perbandingan di `assessment`; tandai hasil yang tidak lolos koreksi |
| 5 | **[DIATASI D-144]** **Model deep satu seed, tanpa ketidakpastian pelatihan.** PatchTST/TSMixer dilatih sekali per refit (seed tetap) | `models.neural` | selisih kecil antarmodel deep (≤ 0,01 akurasi) bisa berubah dengan seed lain | ulangi dengan 3–5 seed dan laporkan rentangnya (± 25 menit per seed di CPU) |
| 6 | **[SEBAGIAN D-144]** **Risiko kontaminasi TimesFM 3.0.** Dirilis Sep 2026, korpus pralatih tidak diungkap; periode uji 2021–2026 | D-142 | keunggulan MAE 10,5% bisa terlalu optimistis | sudah ditulis sebagai batas atas di findings; uji tambahan: bandingkan pada origin 2026 saja atau seri yang jarang dipublikasikan (provinsi kecil) |
| 7 | **[DIATASI D-144]** **Interval bootstrap blok origin masih bisa optimistis.** Blok 2–3 origin (8–12 minggu); ketergantungan siklus harga bisa lebih panjang | TRACKING.md §5 | interval akurasi arah sedikit terlalu sempit | uji kepekaan blok 4 dan 6 origin; laporkan bila keputusan berubah |
| 8 | **Uji binomial menganggap replikasi independen** (positif palsu plasebo, share_fx_improves, kesamaan tanda V4) | `assessment._rate_vs_alpha`, `_share_half` | p terlalu kecil bila sel berkorelasi | sebut sebagai keterbatasan di interpretasi; untuk V4 pakai bootstrap per episode |
| 9 | **[DIATASI D-144]** **Bagian Task 4 terlalu padat untuk pembaca.** 559 metrik, segmen × 10 model, tabel metrik umum memuat semua | halaman 7 | temuan utama tenggelam | default filter penilaian ke lebih baik / lebih buruk / perlu ditinjau; ringkasan model sebagai tabel pertama |
| 10 | **[SEBAGIAN D-144]** **Log evaluasi-saja menumpuk.** 17 dari 23 run adalah evaluasi-saja (Task 4 punya 7 run), sebagian karena `evaluate` diulang setiap kali evaluator diperbaiki | Riwayat | riwayat sulit dibaca; tren antar run kebanyakan datar | catat versi evaluator di RunRecord; filter Riwayat default hanya run terbaru per tahap + semua eksekusi |
| 11 | **Hasil model deep tidak dapat direproduksi juri tanpa unduhan.** `deep_preds` tidak dikirim; TimesFM perlu bobot 1,32 GB berlisensi non-komersial | D-142 | Tingkat A (app) tetap jalan dari log; Tingkat B/C untuk model deep butuh internet & torch | sebut di README & makalah; log evaluasi (dikirim) cukup untuk menampilkan angka |
| 12 | **Server app lokal 8501 basi.** Proses lama memuat `kagami.tracking` sebelum D-140 → halaman 7 error `artifact_sync` | render 8501 | pengguna melihat error di halaman 7 | restart `python -m kagami app` |

### C.5 Yang sudah teratasi sejak audit awal

- "ok" tidak lagi berarti "bagus": status hitung dan penilaian terpisah; 7 metrik "lebih buruk" dan 8 "perlu ditinjau"
  terlihat di Ringkasan.
- Akurasi arah punya interval dan baseline; M1/M2 terbukti tidak lebih baik dari menebak arah terbanyak, M3 dan
  model-model baru lebih baik.
- Kegagalan per komoditas terlihat: komoditas berharga kaku di bawah baseline arah untuk semua model kecuali C2
  (belum terbukti berbeda).
- Wiring: `task2`/`robustness` mendeklarasikan input opsional; tes menolak pembacaan tanpa deklarasi.
- Eksekusi dipisah dari evaluasi-saja; artefak yang bukan output run eksekusi terakhir ditandai.
- Sidik jari kode (code hash, working tree, versi paket) tercatat di setiap run baru.
- Ablation kurs yang bermakna tersedia lewat tiga keluarga model (klasifier, TSMixer, TimesFM); hasilnya konsisten: kurs
  tidak menambah akurasi.

### C.6 Prioritas berikutnya

| Prioritas | Tindakan | Butir C.4 |
|---|---|---|
| P1 | Restart app 8501; commit; `evaluate all` pada commit bersih — **menunggu Danen** (agent tidak commit, server milik pengguna) | 12, 1 |
| P1 | Koreksi multiplisitas untuk perbandingan berpasangan & rasio MAE model eksploratif — **selesai (D-143, C.7)** | 4 |
| P2 | `robustness --tier2` tercatat, cek identik dengan file resmi | 2 |
| P2 | Ulangi model deep dengan 3–5 seed | 5 |
| P2 | Default filter halaman 7 ke metrik bernilai penilaian; Riwayat default ringkas | 9, 10 |
| P3 | Kepekaan panjang blok bootstrap origin; uji kontaminasi TimesFM pada subset | 7, 6 |

### C.7 Hasil koreksi multiplisitas (D-143)

`tracking.assessment.apply_multiplicity`: Benjamini–Hochberg per keluarga per run, q < 0,05. Tiga keluarga: beda akurasi
berpasangan (p bootstrap blok origin berpasangan), metrik arah vs acuan (akurasi vs baseline, balanced acc., F1 makro, MCC,
ROC-AUC, PR-AUC; p bootstrap), rasio MAE model eksploratif (p DM). Tabel segmen dikoreksi BH di seluruh tabel per horizon.
Uji resmi praregistrasi (rasio M0/M2/M3 vs M1, H5 dengan Holm) tidak dimasukkan. Evaluasi ulang `task4-20261124T070017Z-90ae3f`.

| Keluarga | Uji | Lebih baik / buruk sebelum | Bertahan setelah BH |
|---|---|---|---|
| Beda akurasi berpasangan | 30 | 5 | 5 (TFM & TFM_fx vs M3 h 4, C2 vs M3 h 4, C1 vs M1 h 4 & 8) |
| Metrik arah vs acuan | 132 | ± 125 | 123 (M1 & M2 tetap belum terbukti) |
| Rasio MAE model eksploratif | 14 | 5 | 4 (TFM & TFM_fx vs M1, h 4 & 8) |
| Segmen h 8 | 190 | – | 47 lebih baik, 15 lebih buruk |

Gugur: TSMixer + kurs vs TSMixer MAE h 4 (DM p 0,020 → q 0,057); segmen kaku TimesFM −0,074 (q 0,053) dan M2 −0,062
(q 0,080); segmen lentur M1 +0,077 (q 0,064). Angka segmen di Lampiran B ("M1 lentur lebih baik", "M2 kaku lebih buruk")
berasal dari sebelum koreksi. `results/findings.md` sudah disesuaikan.

Kesimpulan tidak berubah: tidak ada perbandingan "dengan kurs vs tanpa kurs" yang bertahan; keunggulan TimesFM terhadap M1
dan keunggulan model baru terhadap baseline arah tahan koreksi.

### C.8 Tindak lanjut kedua (D-144, 2026-11-24 malam)

Atas tinjauan lanjutan (prioritas P1–P3). Evaluasi `task4-20261124T080520Z-fb990b`; 27 run (8 eksekusi, 19 evaluasi-saja).

| Butir | Status | Hasil |
|---|---|---|
| F1 lengkap per model | selesai | tabel "Perbandingan model" di Task 4 (tampil pertama): F1 makro, F1 berbobot (baru), F1/precision/recall per kelas, balanced acc., MCC, ROC-AUC, PR-AUC, cakupan (baru), akurasi termasuk perubahan nol (baru) |
| Kelas tidak berubah (FLAT) | dijelaskan | F1 dihitung pada baris berubah (cakupan 0,857 h 4 / 0,907 h 8); akurasi bila perubahan nol dihitung salah dilaporkan berdampingan. Kelas FLAT tetap tidak dimodelkan (butuh ambang baru setelah G6) |
| Replikasi seed (C.4 #5) | selesai | 3 seed PatchTST, TSMixer, TSMixer + kurs (`task4 --deep PTST_r2 …`, 2.686 dtk); ringkasan rerata ± sd (min..maks) |
| Robustness (C.4 #2) | selesai | `robustness --tier2` dijalankan tercatat ke folder sementara: sha256 identik dengan file resmi (679 baris) → file resmi tidak diganti, log run diimpor; status kini sinkron |
| Kepekaan blok (C.4 #7) | selesai | blok 2/3/4/6 origin untuk 17 perbandingan per horizon: 100% keputusan sama; DM lag HAC 1/2/3/5 |
| Kontaminasi TimesFM (C.4 #6) | sebagian | segmen "tahun origin" di tabel segmen; 2026: MAE/M1 0,938 (lebih kecil dari 2023–2024). Uji subset seri jarang dipublikasikan belum |
| Task 4 terlalu padat (C.4 #9) | selesai | tabel perbandingan model dulu; diagnostik lanjutan di balik sakelar; filter penilaian default tanpa "informasi" |
| Riwayat & versi evaluator (C.4 #10) | sebagian | tampilan "Terbaru per tahap + semua eksekusi" / "Hanya eksekusi"; `evaluator_version` di RunRecord (schema 3). Log lama tetap ada (tidak pernah dihapus) |
| Commit, run bersih, restart 8501 (C.4 #1, #12) | menunggu Danen | agent tidak commit dan tidak mematikan server milik pengguna |
| Lineage Task 1 & `forecast_*` (C.4 #3) | belum | butuh run Kaggle ± 2 jam + Task 4 resmi; menjalankan ulang lokal akan menulis ulang artefak resmi |
| Uji binomial & independensi (C.4 #8), reproduksi offline (C.4 #11) | belum | dicatat sebagai keterbatasan |

**Tabel klasifikasi arah h = 8** (baris berubah; baseline mayoritas 0,545):

| Model | Akurasi | F1 makro | F1 berbobot | F1 naik | F1 turun | Balanced | MCC | ROC-AUC | PR-AUC | Akurasi termasuk perubahan nol |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 0,560 | 0,551 | 0,557 | 0,614 | 0,488 | 0,552 | 0,106 | 0,569 | 0,589 | 0,508 |
| M2 | 0,560 | 0,549 | 0,556 | 0,620 | 0,479 | 0,551 | 0,104 | 0,572 | 0,591 | 0,508 |
| M3 | 0,602 | 0,594 | 0,599 | 0,651 | 0,537 | 0,594 | 0,192 | 0,627 | 0,643 | 0,546 |
| C1 | 0,607 | 0,605 | 0,608 | 0,634 | 0,576 | 0,606 | 0,211 | 0,652 | 0,679 | 0,551 |
| C2 | 0,617 | 0,614 | 0,617 | 0,648 | 0,579 | 0,614 | 0,227 | 0,654 | 0,678 | 0,559 |
| PatchTST | 0,596 | 0,593 | 0,596 | 0,629 | 0,558 | 0,593 | 0,187 | 0,640 | 0,650 | 0,541 |
| TSMixer | 0,608 | 0,604 | 0,608 | 0,642 | 0,566 | 0,604 | 0,209 | 0,641 | 0,645 | 0,552 |
| TSMixer + kurs | 0,601 | 0,598 | 0,601 | 0,635 | 0,560 | 0,598 | 0,195 | 0,644 | 0,650 | 0,545 |
| TimesFM 3.0 | 0,623 | 0,623 | 0,623 | 0,623 | 0,624 | 0,629 | 0,257 | 0,690 | 0,703 | 0,566 |
| TimesFM 3.0 + kurs | 0,613 | 0,611 | 0,608 | 0,583 | 0,638 | 0,624 | 0,255 | 0,696 | 0,712 | 0,556 |

**Replikasi 3 seed, h = 8** (rerata ± sd, min..maks): PatchTST MAE/M1 0,972 ± 0,011 (0,962..0,984), akurasi 0,583 ± 0,016;
TSMixer 0,966 ± 0,007 (0,959..0,972), 0,610 ± 0,005; TSMixer + kurs 0,995 ± 0,009 (0,986..1,005), 0,601 ± 0,004. Selisih
akurasi antar model deep ≤ 0,03 berada dalam rentang seed; TSMixer + kurs konsisten lebih buruk dari TSMixer pada MAE.

**Penilaian.** Target F1 0,8–0,9 tidak tercapai: F1 makro terbaik 0,623 (TimesFM, h 8). Dengan sd(Δ kurs) mingguan 0,008 dan
46–62% minggu tanpa perubahan pada komoditas yang diatur, plafon prediksi arah pada data ini rendah; menambah model lagi
kemungkinan memberi tambahan kecil. Langkah berikutnya yang paling bernilai tetap reproduksibilitas (C.4 #1, #3).
