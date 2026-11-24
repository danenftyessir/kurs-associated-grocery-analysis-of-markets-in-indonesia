# Optimasi Performa Klasifikasi Arah Task 4 (EKSPLORATIF)

Tanggal: 2026-11-24 · Pelaksana: Danen (dengan agent) · Keputusan terkait: D-145 · Status: **COMPLETE** (semua fase)

Catatan bertanggal (bukan dokumen hidup). Eksperimen ini **eksploratif**: tidak mengubah uji praregistrasi (H5 tetap
dari MAE + DM pada `forecast_eval`), tidak mengubah `params.yaml`, `forecast_preds`, `direction_preds`, `deep_preds`, atau
artefak lain. Skrip & konfigurasi lengkap: [folder lampiran](20261124_task4_optimasi_arah/) (`scripts/`, `hasil/`).

> **Pembaruan 2026-11-24 (malam).** Rekomendasi §8 butir 1 dikerjakan: C1-tuned & C2-tuned diporting ke `src/`
> (`features/price_dynamics.py`, `models/direction.py`), dijalankan dengan `python -m kagami task4 --direction-tuned` →
> artefak eksploratif `direction_tuned_preds`. Prediksinya identik dengan eksperimen ini.

## 0. Ringkasan

| Pertanyaan | Jawaban (test final, origin ≥ 2024-01-01) |
|---|---|
| Apakah macro F1 bisa dinaikkan? | **Ya.** C1-tuned: 0,677 (h 4) / 0,680 (h 8) vs C1 resmi 0,586 / 0,607 dan model terbaik resmi TimesFM 0,618 / 0,621. Selisih vs TimesFM +0,059 (0,043..0,075) / +0,053 (0,027..0,077), q BH 0,001. |
| Dari mana kenaikannya? | Hampir seluruhnya dari **fitur** (deviasi harga terhadap rerata bergerak & antarprovinsi, sinyal komoditas nasional, lag panjang, musiman). Tuning hyperparameter hanya ± +0,01 di pengembangan. |
| Fitur kurs? | **Tidak membantu**: C2-tuned − C1-tuned −0,004 (−0,011..0,004) / +0,001 (−0,008..0,011). Konsisten dengan H5. |
| Threshold? | Untuk klasifier, threshold dari pengembangan **tidak** menambah (C1t h 8: 0,674 vs 0,680 pada 0,5). Untuk TimesFM (regresi), threshold sedikit negatif menaikkan +0,012 / +0,024 (lolos BH). |
| TimesFM → CatBoost? | 0,672 / 0,676: jauh di atas TimesFM mentah (+0,054 / +0,055, lolos BH), **tetapi tidak berbeda dari C1-tuned** (−0,005 / +0,002). TimesFM tidak menambah informasi di atas fitur rekayasa. |
| TSMixer-tuned? | Tidak lebih baik dari TSMixer resmi (−0,014 / −0,011, belum terbukti; dengan threshold dev h 8 −0,026, **lebih buruk**, lolos BH). |
| Kebocoran? | Tidak terdeteksi: merusak harga sesudah origin tidak mengubah 37 fitur baru pada minggu ≤ origin (3 origin diuji); latih hanya t + h ≤ origin. |
| Cakupan | Sama untuk semua model & baseline: 0,855 (h 4) / 0,907 (h 8) = porsi baris dengan harga berubah (y ≠ 0). Tidak ada prediksi selektif, tidak ada baris yang dibuang. |

Rekomendasi: bila dipakai, **C1-tuned dengan threshold 0,5** sebagai klasifier arah eksploratif. Hasil tetap
asosiasional/prediktif pseudo-real-time; bukan klaim kausal, tidak mengubah kesimpulan praregistrasi.

## 1. Protokol (ditetapkan sebelum tuning)

- **Label**: naik bila y = p_{t+h} − p_t > 0, turun bila < 0; y = 0 (harga tidak berubah) dikeluarkan dari metrik dan dari
  data latih klasifier (definisi sama dengan D-139/D-141). Cakupan dilaporkan.
- **Rolling-origin** sama dengan Task 4: origin tiap 4 minggu sejak 2021-01-04; latih hanya baris dengan t + h ≤ origin;
  harga dunia as-of `available_at`.
- **Pembagian waktu**: origin pengembangan = origin + h ≤ 2023-12-31 (38 origin h 4, 37 origin h 8); **test final** = origin ≥
  2024-01-01 (37 / 36 origin). Celah di antaranya memastikan tidak ada target pengembangan yang terealisasi di periode test.
  Seleksi fitur, hyperparameter, varian tahap-2, dan threshold **hanya** memakai origin pengembangan.
- **Baseline** = prediksi resmi yang sudah ada (`direction_preds`, `deep_preds`, `forecast_preds`), dievaluasi pada baris test
  yang identik (10.674 baris h 4, 11.007 baris h 8 dengan y ≠ 0).
- **Inferensi**: interval 95% bootstrap blok origin (blok 2 / 3 origin untuk h 4 / 8, 1.999 replikasi); beda berpasangan
  macro F1 pada baris yang sama; p dua sisi bootstrap; **BH dalam satu keluarga 26 perbandingan** (§6).
- Mesin eksperimen mereproduksi C1 resmi persis (selisih p_up 0,0 pada 6 origin).

## 2. Audit implementasi awal (Fase 1)

| Model | Implementasi | Hyperparameter | Keluaran | Threshold |
|---|---|---|---|---|
| C1 / C2 | `models/direction.py`, HGB classifier; C1 = base + id, C2 = + fx | `params.forecast.hgb`: max_iter 300, lr 0,05, max_leaf_nodes 31 (lain default sklearn) | `p_up` | 0,5 |
| PatchTST / TSMixer | `models/neural.py`, global, loss L1 pada y terskala, refit tiap 4 origin | lookback 52, d_model 32, 2 lapis, dropout 0,1, 4 epoch, lr 1e-3, ≤ 40.000 jendela | ŷ (regresi) | tanda ŷ (0) |
| TimesFM 3.0 | zero-shot, konteks log harga s.d. origin | – | ŷ (regresi) | tanda ŷ (0) |

Fitur resmi hanya 7 (base: lag Δp 1/4/8, bulan, minggu relatif Idulfitri, Δ Brent 1/4) + 7 kurs + 2 kategori. Tidak ada
informasi level harga (deviasi dari rerata), lag panjang, atau sinyal lintas provinsi. Tidak ada kebocoran yang ditemukan
pada implementasi resmi (split `t + h ≤ origin`, as-of harga dunia).

## 3. EXP-A1 — Ablation kelompok fitur (Fase 4)

Semua fitur dihitung per seri (provinsi × komoditas) dari log harga s.d. minggu t (`scripts/feats.py`). HGB dengan
hyperparameter resmi, 37–38 origin pengembangan, threshold 0,5.

| Kelompok | Isi | Tambah-satu: F1 h 4 / h 8 | Hapus-satu dari `all`: F1 rata² |
|---|---|---|---|
| (C1 resmi) | base + id | 0,584 / 0,597 | – |
| `lag` | Δp mingguan lag 1–3, Δp 13/26/52 minggu | 0,596 / 0,628 | 0,6564 |
| `rmean` | EWM return (half-life 4, 13) | 0,603 / 0,617 | 0,6575 |
| `rstd` | sd return 4/13/26 | 0,587 / 0,596 | 0,6561 |
| `mom` | porsi minggu naik/turun 13, akselerasi, panjang run tanda | 0,588 / 0,601 | 0,6561 |
| `vol` | sd 52, rerata & maks \|Δp\| 13 | 0,593 / 0,601 | **0,6611 (dibuang)** |
| `season` | minggu-dalam-tahun sin/cos, perubahan h minggu yang sama 1 & 2 tahun lalu | 0,588 / 0,610 | 0,6492 |
| `dev` | deviasi dari MA13/MA52, posisi rentang 52 minggu, deviasi spasial antarprovinsi & perubahannya | **0,630 / 0,641** | 0,6494 |
| `cf` | umur sejak perubahan harga terakhir, porsi minggu tanpa perubahan, run carry-forward | 0,581 / 0,603 | **0,6582 (dibuang)** |
| `comm` | Δp rerata nasional komoditas 1/4/8, porsi provinsi naik, sd nasional | **0,631 / 0,645** | 0,6466 |
| `all` | semua | 0,654 / 0,662 (rata² 0,6579) | – |
| `all + fx` | + kurs & harga dunia | 0,649 / 0,662 (0,6553) | – |

Aturan seleksi (ditetapkan sebelum melihat hasil): buang kelompok yang bila dihapus menaikkan macro F1 rata-rata
pengembangan → `vol` & `cf` dibuang. Set terpilih: lag, rmean, rstd, mom, season, dev, comm (37 fitur + base + id).
Selisih hapus-satu kecil (≤ 0,009), jadi urutan antarkelompok lemah kecuali `dev`, `comm`, `season`.

## 4. Laporan per eksperimen (Fase 2, 3, 5) — angka test final

Format: macro F1 (interval 95%) · F1 naik / turun · MCC · ROC-AUC · cakupan. Threshold "dev" = dipilih dari origin
pengembangan (grid 0,30–0,70 langkah 0,005 untuk probabilitas; 141 kuantil skor untuk regresi).

### EXP-T1 — C1-tuned (HGB, tanpa kurs) · COMPLETE
- **Hyperparameter** (Optuna TPE, 40 trial, seed 20261121; objektif = rerata macro F1 h 4 & 8 pada origin pengembangan
  ganjil; 3 teratas dikonfirmasi pada semua origin pengembangan): lr 0,0281, max_iter 250, max_leaf_nodes 23,
  min_samples_leaf 319, l2 3,85, max_features 0,335, tanpa bobot kelas, tanpa peluruhan waktu. Ruang: lr 0,01–0,2,
  max_iter 100–800, daun 7–63, min_leaf 20–400, l2 1e-3–10, max_features 0,3–1, bobot seimbang ya/tidak, peluruhan 0/1/2/4 th.
- **Fitur**: set terpilih §3 (tanpa kurs). **Threshold**: dev h 4 = 0,50, h 8 = 0,46.
- h 4: **0,677** (0,652..0,698) · 0,704 / 0,651 · MCC 0,356 · AUC 0,741 · PR-AUC 0,742 · cakupan 0,855
- h 8 (thr 0,5): **0,680** (0,653..0,706) · 0,725 / 0,634 · MCC 0,363 · AUC 0,738 · PR-AUC 0,755 · cakupan 0,907;
  thr dev 0,46: 0,674 (0,645..0,702)
- Seed 2 / 3: 0,680 / 0,679 (h 4), 0,677 / 0,683 (h 8) → stabil (± 0,003).
- Ketidakpastian antar-origin: sd macro F1 per origin 0,084 (h 4) / 0,074 (h 8).
- Pengembangan: 0,656 / 0,676 (C1 resmi pada origin sama 0,584 / 0,597).
- **Runtime**: tuning 84 menit (126 dtk/trial), run semua origin 7,8 menit (12 core).

### EXP-T2 — C2-tuned (C1-tuned + kurs & harga dunia) · COMPLETE
- 12 trial (dipangkas dari 25 karena waktu; titik awal = hyperparameter resmi dan hyperparameter C1-tuned). Terpilih =
  hyperparameter C1-tuned persis → C2t − C1t adalah ablation kurs yang bersih.
- h 4: 0,674 (thr dev 0,505) · h 8: 0,675 (thr dev 0,475), 0,677 pada 0,5.
- vs C1-tuned: −0,004 (−0,011..0,004) / +0,001 (−0,008..0,011) → **fitur kurs tidak membantu** (belum terbukti).
- Runtime: tuning 41 menit, run semua origin 10,7 menit.

### EXP-T3 — TSMixer-tuned · COMPLETE (hasil negatif)
- 10 trial (refit tiap 8 origin saat tuning), 2 teratas dikonfirmasi dengan protokol D-142 (refit tiap 4). Ruang: lookback
  26/52/104, d_model 16/32/64, lapis 1–3, dropout 0–0,3, lr 3e-4–3e-3, epoch 4/8, weight decay 1e-5–1e-2, loss L1 atau
  **BCE arah** (kepala klasifikasi).
- Terpilih: lookback 104, d_model 16, 3 lapis, dropout 0,30, lr 0,0029, 8 epoch, wd 0,0092, loss BCE.
- Nilai tuning 0,593 turun menjadi 0,584 saat dikonfirmasi → sebagian besar "kenaikan" adalah derau pelatihan.
- Test, 3 seed (thr 0,5): h 4 0,580 / 0,587 / 0,582; h 8 0,609 / 0,599 / 0,609. TSMixer resmi 0,594 / 0,620.
- vs TSMixer resmi: −0,014 (−0,034..0,009) / −0,011 (−0,040..0,022) belum terbukti; dengan threshold dev h 8 −0,026
  (−0,047..−0,005), **lebih buruk** (lolos BH).
- Runtime: tuning 30 menit + konfirmasi ± 25 menit; test ± 12 menit per seed.

### EXP-TH — Optimasi threshold (Fase 3) · COMPLETE
| Model | thr dev h 4 / h 8 | Δ macro F1 vs thr default (test) |
|---|---|---|
| C1 resmi | 0,480 / 0,425 | −0,004 / −0,014 (belum terbukti) |
| C1-tuned | 0,500 / 0,460 | 0 / −0,005 (belum terbukti) |
| TimesFM | −0,0010 / −0,0042 | **+0,012 (0,007..0,017) / +0,024 (0,013..0,035)**, lolos BH |
| TSMixer resmi | −0,0053 / −0,0106 | −0,010 / −0,013 (deskriptif) |

Threshold menggeser keseimbangan F1 naik/turun; untuk klasifier yang sudah terkalibrasi (C1/C1-tuned) tidak ada keuntungan
yang bertahan di test. TimesFM berbias sedikit turun (ramalan median ≈ datar), jadi ambang sedikit negatif memperbaiki.

### EXP-CAL — Kalibrasi probabilitas TimesFM dari residu historis · COMPLETE
- P(naik | ŷ) = porsi residu historis e (origin o' + h ≤ o, walk-forward, ≥ 8 origin) dengan ŷ + e > 0. Varian global
  dipilih di pengembangan (per komoditas lebih buruk: 0,613 / 0,607 vs global 0,626 / 0,644).
- Test, thr 0,5: 0,626 / 0,643; vs TimesFM mentah +0,010 (0,004..0,017, lolos BH) / +0,018 (−0,000..0,035, belum terbukti).
  Setara dengan menggeser threshold; tidak lebih baik dari threshold dev.

### EXP-H — TimesFM → fusi fitur → CatBoost (Fase 5) · COMPLETE
- Baris tahap-2 = baris origin; fitur = ramalan TimesFM & TimesFM+kovariat untuk **kedua** horizon (zero-shot, konteks s.d.
  origin → out-of-sample), selisih antarhorizon, (B) + fitur rekayasa §3, (C) + probabilitas OOF C1-tuned kedua horizon.
  CatBoost untuk origin o dilatih hanya pada baris origin o' dengan o' + h ≤ o (label terealisasi); butuh ≥ 8 origin
  riwayat. Tidak ada prediksi in-sample.
- Seleksi di pengembangan (28 origin): A (TimesFM saja) P1 0,599 / 0,583, P2 0,595 / 0,572; B P1 0,637 / 0,645;
  **C P1 0,643 / 0,653** (terpilih; depth 4, lr 0,05, 400 iterasi). Grid dipangkas (B & C hanya P1) karena waktu.
- Test: h 4 0,672 (thr dev 0,495) · h 8 0,676 (thr dev 0,535); F1 naik / turun 0,699 / 0,645 dan 0,716 / 0,636;
  MCC 0,346 / 0,353; AUC 0,737 / 0,733; PR-AUC 0,749 / 0,761.
- vs TimesFM mentah: +0,054 (0,036..0,069) / +0,055 (0,032..0,077), lolos BH. vs C1-tuned: −0,005 (−0,017..0,006) /
  +0,002 (−0,014..0,019), belum terbukti.
- Runtime: 6 menit per konfigurasi di pengembangan, ± 25 menit semua origin.

## 5. Per komoditas (test, macro F1; threshold dev bila ada)

| Model | h | bawang merah | bawang putih | beras | cabai merah | cabai rawit | daging ayam | daging sapi | gula | minyak goreng | telur |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 8 | 0,706 | 0,666 | 0,475 | 0,557 | 0,618 | 0,536 | 0,525 | 0,657 | 0,481 | 0,485 |
| TimesFM | 8 | **0,771** | 0,575 | **0,544** | 0,678 | 0,688 | 0,641 | 0,525 | 0,513 | 0,515 | 0,584 |
| C1-tuned | 8 | 0,740 | 0,657 | 0,530 | **0,681** | **0,705** | **0,661** | 0,560 | **0,735** | 0,531 | 0,643 |
| TFM-head | 8 | 0,724 | **0,672** | 0,606 | 0,678 | 0,683 | 0,608 | **0,598** | 0,725 | **0,542** | **0,648** |
| C1-tuned | 4 | 0,732 | 0,696 | 0,666 | 0,609 | 0,677 | 0,639 | 0,609 | 0,746 | 0,582 | 0,662 |

C1-tuned lebih tinggi dari TimesFM pada 9/10 komoditas (h 4) dan 8/10 (h 8). Komoditas diatur/kaku (beras, daging sapi,
minyak goreng) tetap paling sulit (0,53–0,61); gula naik paling besar (0,513 → 0,735 pada h 8). Tabel lengkap:
`hasil/final_per_commodity.csv`.

## 6. Keluarga perbandingan berpasangan (test, BH 26 perbandingan)

| A | B | h 4: Δ (interval) · q | h 8: Δ (interval) · q | Penilaian |
|---|---|---|---|---|
| C1t | C1 | +0,092 (0,065..0,118) · 0,001 | +0,067 (0,047..0,097) · 0,001 | lebih baik |
| C1t | C2 | +0,086 (0,056..0,119) · 0,001 | +0,062 (0,039..0,089) · 0,001 | lebih baik |
| C1t | TFM (thr 0) | +0,059 (0,043..0,075) · 0,001 | +0,053 (0,027..0,077) · 0,001 | lebih baik |
| C1t | TFM (thr dev) | +0,047 (0,030..0,064) · 0,001 | +0,030 (0,000..0,055) · 0,088 | h 4 lebih baik; h 8 belum terbukti |
| C2t | C1t | −0,004 · 0,42 | +0,001 · 0,87 | belum terbukti (kurs tidak membantu) |
| TFM-head | TFM | +0,054 · 0,001 | +0,055 · 0,001 | lebih baik |
| TFM-head | C1t | −0,005 · 0,44 | +0,002 · 0,79 | belum terbukti |
| TFMcal | TFM | +0,010 · 0,005 | +0,018 · 0,093 | h 4 lebih baik |
| TFM thr dev | TFM thr 0 | +0,012 · 0,001 | +0,024 · 0,001 | lebih baik |
| TSMXt | TSMX | −0,014 · 0,30 | −0,011 · 0,70 | belum terbukti |
| TSMXt thr dev | TSMX thr dev | −0,021 · 0,16 | −0,026 · 0,017 | h 8 lebih buruk |
| C1t thr dev | C1t thr 0,5 | 0 · 1,0 | −0,005 · 0,30 | belum terbukti |
| C1 thr dev | C1 thr 0,5 | −0,004 · 0,42 | −0,014 · 0,25 | belum terbukti |

Rincian lengkap (n, p): `hasil/final_paired.csv`; semua metrik (weighted F1, precision/recall per kelas, balanced accuracy,
MCC, ROC-AUC, PR-AUC, cakupan, sd antar-origin): `hasil/final_metrics.json`.

## 7. Batas & catatan kejujuran

- Hasil test hanya 36–37 origin (2024-01 .. 2026-09); interval bootstrap blok mencerminkan ketidakpastian ini.
- Seleksi fitur & tuning memakai origin pengembangan 2021–2023; struktur pasar bisa berubah (mis. regulasi HET 2024+).
  Test final tidak dipakai untuk memilih apa pun; angka test hanya dilihat setelah konfigurasi dibekukan.
- Pemangkasan karena waktu (dicatat): C2-tuned 12 trial, grid CatBoost dipangkas, TSMixer 10 trial.
- Catatan kontaminasi TimesFM (D-142) tetap berlaku: keunggulan zero-shot adalah batas atas.
- Bukan uji praregistrasi. H5 tetap tidak didukung; temuan "kurs tidak membantu" konsisten di sini.
- Optuna 4.5.0 dan CatBoost 1.2.8 dipasang di lingkungan lokal untuk eksperimen ini; bukan dependensi paket `kagami`.

## 8. Rekomendasi eksperimen selanjutnya

1. Bila ingin dipakai di app/makalah: porting C1-tuned ke `src/` sebagai klasifier eksploratif (fitur §3 + hyperparameter
   terpilih) dengan tes kebocoran, sebagai artefak terpisah dari `direction_preds`.
2. Fitur yang paling berguna adalah deviasi & sinyal nasional → eksplorasi lanjutan yang paling murah: deviasi terhadap
   HET/HAP (jarak harga ke harga acuan) untuk komoditas diatur yang masih lemah.
3. Jangan menambah tuning TSMixer/PatchTST: derau seed lebih besar dari kenaikan tuning.
4. TimesFM layak dipakai sebagai fitur hanya bila konteksnya diperpanjang (prediksi mingguan, bukan hanya pada origin) agar
   tahap-2 punya lebih banyak baris latih.
