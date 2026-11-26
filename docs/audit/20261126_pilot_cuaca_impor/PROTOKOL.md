# Protokol D-157 — Pilot cuaca sentra produksi & realisasi impor (Task 4 arah, EKSPLORATIF)

Ditulis dan di-hash **sebelum** run modeling (`scripts/run_wi.py`). Sudah dijalankan sebelum protokol: unduh NASA POWER (persetujuan
Danen 2026-11-26), pembangunan fitur (`build_wi.py`), uji kebocoran (`hasil/wi_leak.csv`, 0 sel), layar DU (`hasil/du_wi.csv`). Tidak
ada prediksi model kandidat yang dibuat sebelum protokol ini.

## 1. Kartu eksperimen (EKSPERIMEN.md §2)

### Kartu W — cuaca di sentra produksi hortikultura

| Komponen | Isi |
|---|---|
| Problem | Galat C1-tuned terbesar yang dapat dikoreksi adalah pergeseran arah per komoditas × origin (informasi nasional sempurna: +0,105; hortikultura saja +0,042–0,049, D-157 §0); hortikultura = 32–34% baris dan macro F1 terendah (cabai merah 0,59 h 4) |
| Data characteristic | Cuaca harian NASA POWER 2016–2026 di 34 titik; porsi produksi ATAP stabil (r ≥ 0,95 antar 2020–2024); 2023 kering (El Niño). DU dev: anomali suhu maks 28 hari ρ parsial +0,14 / +0,17, hujan 91 hari −0,09 / −0,16, interval lebar (variasi hanya antarorigin) |
| Knowledge discovery | Apakah anomali cuaca di provinsi penghasil mendahului arah harga eceran 4–8 minggu kemudian di seluruh provinsi? |
| Hypothesis | Cuaca panas/kering atau basah ekstrem di sentra menurunkan pasokan panen berikutnya; informasi ini tidak ada di histori harga sampai harga bergerak |
| Method | C1-tuned + 6 fitur nasional tertimbang produksi (W_NAT); varian kedua + 6 fitur titik provinsi sendiri (W_LOC). Hyperparameter C1-tuned tetap |
| Validation | Δ berpasangan vs C1-tuned (bootstrap blok origin), q BH, konsistensi tahun & origin, kemunduran per kelas/komoditas; ukuran pada baris hortikultura dilaporkan terpisah |
| Leakage control | Cuaca s.d. Minggu sebelum minggu origin (lag ≥ 7 hari); klimatologi 2016–2020 (sebelum origin pertama); porsi ATAP tahun Y dipakai sejak 1 Juli Y+1, sebelum 2021-07-01 memakai 2020 (diungkap, porsi stabil); uji perturbasi & penghapusan 12 origin → 0 sel |
| Decision | Aturan §3 (ditulis sebelum hasil). Gerbang DU tidak lolos; pengecualian beralasan pengetahuan: sinyal tingkat nasional hanya bervariasi antar 37 origin × 3 komoditas sehingga layar korelasi baris (dikalibrasi pada `iw_gap` tingkat baris) berdaya rendah; besarnya ≥ kontrol positif |

### Kartu I — realisasi impor bulanan

| Komponen | Isi |
|---|---|
| Problem | Komoditas impor (bawang putih, gula, daging sapi) & pakan = 48–50% baris; kurs & harga dunia tidak membantu (C2-tuned) |
| Data characteristic | Comtrade 2017–2022 + BPS 2023–2026 bulanan (cocok persis 2023, D-133); impor beras melonjak 2018, 2023, 2024 (kebijakan) |
| Knowledge discovery | Apakah volume/nilai satuan impor yang sudah terbit memberi sinyal pasokan sebelum harga eceran bergerak? |
| Hypothesis | Lonjakan/kekeringan impor menambah/mengurangi pasokan pasar dalam 1–3 bulan |
| Method | C1-tuned + 4 fitur (yoy3, mom3, dev12, uv3) per keranjang komoditas |
| Validation | Sama dengan kartu W; ukuran pada baris komoditas keranjang dilaporkan terpisah |
| Leakage control | available_at = akhir bulan + 45 hari (`bps_release_lag_days`); minggu t memakai bulan dengan available_at ≤ Sabtu minggu t; uji perturbasi & penghapusan 12 origin → 0 sel |
| Decision | Aturan §3. DU ≈ 0 (|ρ| ≤ 0,08) → dijalankan karena disetujui eksplisit; ekspektasi ≈ 0 dicatat sebelum hasil |

## 2. Kandidat & pembanding
`base` = C1-tuned (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed 20261121, threshold 0,5; harus = `direction_tuned_preds` persis).
`W_NAT` = base + `wn_*` (6); `W_LOC` = base + `wn_*` + `wl_*` (12); `IMP` = base + `im_*` (4). Origin pengembangan (origin + h ≤
2023-12-31), split resmi, label & baris evaluasi resmi. Gabungan W + I hanya bila keduanya lolos (tidak di sesi ini).

## 3. Aturan keputusan (sama dengan D-156 §5)
Δ macro F1 rerata (h 4, h 8) ≥ +0,005, interval > 0 di ≥ 1 horizon, Δ ≥ 0 di horizon lain; q BH < 0,05 (keluarga 3 kandidat per
horizon); Δ ≥ 0 di ≥ 2 dari 3 tahun dev & porsi origin Δ > 0 ≥ 0,5 di kedua horizon; Δ F1 naik/turun ≥ −0,01; tidak ada komoditas
< −0,03 di kedua horizon. Skala prioritas Danen (+0,005–0,010 menarik, +0,010–0,020 layak, > +0,020 besar) dilaporkan berdampingan.

## 4. Test
Hanya bila kandidat lolos §3: satu kandidat per keluarga (W, I) dibuka sekali di origin ≥ 2024-01-01, dilaporkan sebagai evaluasi
eksploratif dengan kriteria tetap (test bukan data independen, D-155) bersama S1–S3. Bila tidak ada yang lolos, test tidak dibuka.

## 5. Adendum pasca-hoc (ditulis sesudah hasil §2 dan sebelum run adendum)
Hasil §2: tidak ada kandidat yang lolos. Residual C1-tuned berkorelasi stabil dengan `wn_z_tmax_28` (+) dan `wn_z_rain_91` (−) di setiap
tahun dev, tetapi HGB tidak memanfaatkannya. Uji satu-satunya (pasca-hoc, dipilih dengan melihat DU dev → bias seleksi diungkap):
`W_CAL` = koreksi logit tahap-2 pada baris hortikultura: logit p' = logit p_C1t + β₁·wn_z_tmax_28 + β₂·wn_z_rain_91 (tanpa intersep),
β diestimasi walk-forward (regresi logistik dengan offset) dari prediksi `base` origin dev o' dengan o' + h ≤ o, minimal 8 origin;
origin sebelumnya & komoditas lain = base. Dinilai pada origin yang punya koreksi, aturan §3. Tidak membuka test apa pun hasilnya
(pasca-hoc); bila lolos → hanya prediksi maju.
