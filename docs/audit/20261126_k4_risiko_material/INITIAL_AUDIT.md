# K4 — Audit awal (EKSPLORATIF, D-164)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Catatan bertanggal (bukan dokumen hidup). Indeks folder: [RESULTS.md](RESULTS.md).

## 1. Lingkup & penamaan

- Permintaan: "Task 4 — Material Price Risk Prediction (K4)", yang dalam permintaan disebut **Jalur B**. Di proyek ini "jalur B" sudah
  berarti pembagian kerja Ardell (PEMBAGIAN_TUGAS), jadi folder memakai konvensi laporan bertanggal: `docs/audit/20261126_k4_risiko_material/`
  (bukan `jalur_b_material_risk/`). Isi folder = 10 dokumen yang diminta + `scripts/` + `hasil/`.
- K4 = kartu usulan di adendum D-155 ([20261125_business_understanding.md](../20261125_business_understanding.md) §6). Jalur ini terpisah
  dari optimasi macro F1 klasifikasi arah (D-156; sesi lain D-165 "jalur A"). Label arah resmi, `direction_tuned_preds`, C1-tuned, dan
  keputusan D-145–D-163 tidak diubah.
- Sesi paralel (2026-11-26): D-162/D-163/D-163a (flag episode real-time, kalibrasi PT/provinsi, kalibrasi skor daftar pantau) dan D-165
  (jalur A). K4 tidak menyentuh `src/`, `tests/`, maupun folder mereka; nomor D-164 dikoordinasikan lewat pesan antarsesi.

## 2. Yang sudah ada (dibaca)

| Sumber | Fakta yang dipakai K4 |
|---|---|
| D-154 BU ([PROTOKOL](../20261125_business_understanding/PROTOKOL.md), `bu.py`) | Kenaikan material = y_h ≥ P80 \|y_h\| baris latih komoditas (walk-forward); daftar pantau V1 = 2 komoditas skor tertinggi per provinsi; presisi test 0,179 / 0,161, recall 0,41 / 0,36; laju-dasar dev 0,120 / 0,132 → test 0,088 / 0,089; aturan naif `R_mom`, `R_nat`, `R_rev`, `R_seas`. |
| D-155 adendum | p_up = P(naik \| y ≠ 0, X) ≠ P(kenaikan material \| X); S2 = kalibrasi arah (baris y ≠ 0); S3 bersyarat pada hasil; test 2024+ bukan independen; titik akhir ≠ kejadian; materialitas statistik ≠ kebijakan; 58% / 56% alarm test pada komoditas diatur. |
| D-156 master F1 | C1-tuned tidak dapat diungguli untuk macro F1 dari histori harga yang sama; galat dari informasi perubahan kecil & pergeseran base rate per origin; HGB setara boosting lain. |
| D-147 preprocessing | Harga kelipatan Rp50; label < 1 tick 2,4–4,3%; label tak stabil terhadap resample hari 8–12%; tidak ada kebocoran fitur (76 origin × 54 kolom). |
| EKSPERIMEN §2–§6 | Kartu 8 komponen, layar DU, test sekali, BH, universe ranking tanpa penyaringan target, registri terpusat. |
| D-163a (sesi lain) | Platt global / isotonik pada p_up menurunkan ECE arah tetapi Brier sedikit memburuk; Platt per komoditas menaikkan presisi pantau h 8 (+0,046) — tidak ada yang lolos. |

## 3. Pemeriksaan implementasi baseline

- **C1-tuned** (`src/models/direction.py`): kolom `tuned_columns("C1t", h)` = 36 numerik (lag, EWM, sd, momentum, musiman, deviasi
  MA/spasial, sinyal nasional) + kategori komoditas & wilayah; `TUNED_HGB` (lr 0,028, 250 iterasi, 23 daun, min daun 319, L2 3,85,
  max_features 0,33); **baris latih y = 0 dibuang**; prediksi dibuat untuk semua baris uji bertarget, termasuk y = 0 (25.259 baris dev),
  sehingga skor baris y = 0 berasal dari model yang tidak pernah melihat "tidak berubah".
- **Daftar pantau D-154** (`bu.py`): ambang & klimatologi dari baris latih per origin (benar, tanpa kebocoran); pembanding "laju-dasar"
  di tabel S1 adalah presisi acak (laju positif keseluruhan), **bukan** ranking berdasarkan laju-dasar per komoditas.
- **Tabel kerja**: `base.parquet` (sesi D-151/D-156; tabel resmi C1-tuned + `ticks_h`, `flip_h`, `st0`, `st_h`) disalin ke scratchpad
  K4. Kolom C1-tuned tidak terpengaruh perubahan `src/features/forecast.py` sesi D-162 (yang hanya mengubah `episode`, kolom grup fx).
  Universe dev direkonstruksi: 12.800 / 12.463 baris = 25.259 baris resmi + 4 baris tanpa target (sama dengan D-155).

## 4. Celah yang ditemukan (sebelum modeling)

| Kode | Celah | Dampak | Penanganan di K4 |
|---|---|---|---|
| G1 | Tidak ada model yang dilatih pada z | Skor daftar pantau tidak dioptimalkan untuk target bisnisnya | K4-E80 (HGB pada z, semua baris) |
| G2 | p_up bukan peluang risiko; S2 = kalibrasi arah | Angka peluang di daftar pantau tidak dapat dibaca sebagai risiko | Kalibrasi pada z (Brier, log loss, ECE) + pembanding C1t terkalibrasi walk-forward |
| G3 | Pembanding laju-dasar per komoditas tidak ada di D-154 | DU: laju z per komoditas 0,02–0,29 → aturan "pantau komoditas yang biasanya naik" bisa kuat | B-CLIM & B-CLIMS (± musim) sebagai pembanding wajib |
| G4 | Komposisi target: 60% / 64% positif = 4 komoditas diatur dengan ambang 1,2–3,9% | "Material" didominasi kenaikan kecil yang bersifat struktural (harga diatur jarang turun) | Dilaporkan; kepekaan K4-S90 (desil atas kenaikan bertanda, komposisi seimbang); ambang kebijakan → U109 |
| G5 | Titik akhir vs kejadian dalam jendela | 12% / 21% kejadian adalah lonjakan yang berbalik | K4-A80 (Fase E), deskriptif |
| G6 | Test 2024+ sudah dipakai berkali-kali | Bukan validasi independen | Seleksi dev saja; test sekali bila lolos; prediksi maju beku |
| G7 | Laju-dasar bergeser (dev 0,12–0,13 → test 0,09; sd mingguan 0,07–0,08) | Peluang mentah bisa salah kalibrasi pada periode baru | Kalibrasi walk-forward diuji; dilaporkan sebagai keterbatasan |
| G8 | Hyperparameter C1-tuned dipilih untuk arah | Mungkin bukan optimal untuk z | Tidak dituning ulang (aturan sesi: tidak mengejar skor); dicatat |

## 5. Rencana (urutan yang dijalankan)

BU ([BUSINESS_REQUIREMENTS.md](BUSINESS_REQUIREMENTS.md)) → DU ([DATA_UNDERSTANDING.md](DATA_UNDERSTANDING.md)) → target
([TARGET_DEFINITION.md](TARGET_DEFINITION.md)) → protokol beku ([PROTOCOL.md](PROTOCOL.md), sha256 18.36 WIB) → run dev → uji integritas
& kebocoran → evaluasi ([RESULTS.md](RESULTS.md), [CALIBRATION_REPORT.md](CALIBRATION_REPORT.md),
[OPERATIONAL_ANALYSIS.md](OPERATIONAL_ANALYSIS.md)) → test sekali bila diizinkan → prediksi maju beku → rekomendasi
([RECOMMENDATIONS.md](RECOMMENDATIONS.md)) → registri ([EXPERIMENT_LOG.csv](EXPERIMENT_LOG.csv) + `docs/eksperimen_registry.csv`).
