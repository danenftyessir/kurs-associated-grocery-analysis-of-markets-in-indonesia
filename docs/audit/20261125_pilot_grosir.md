# Pilot Harga Pedagang Besar PIHPS untuk Task 4 Arah (EKSPLORATIF)

Tanggal: 2026-11-25 · Pelaksana: Danen (dengan agent) · Keputusan: D-150 · Lanjutan [riset sumber data hulu](20261125_sumber_data_hulu.md)
dan [ronde 4](20261125_task4_ronde4.md). Catatan bertanggal (bukan dokumen hidup). Skrip & hasil: [folder lampiran](20261125_pilot_grosir/).

Pertanyaan: apakah harga pedagang besar (grosir) PIHPS memberi informasi arah harga eceran 4/8 minggu ke depan di atas C1-tuned?
Protokol sama dengan D-147–D-149: C1-tuned tetap (kolom & hyperparameter resmi), label resmi, seleksi di origin pengembangan
(origin + h ≤ 2023-12-31), aturan buka test ditetapkan sebelum run (Δ macro F1 rerata ≥ +0,005, interval > 0 di ≥ 1 horizon,
Δ ≥ 0 di horizon lain). Semua langkah < 1 jam → lokal.

## 0. Ringkasan

| Pertanyaan | Jawaban |
|---|---|
| Data diperoleh? | **Ya**, atas persetujuan Danen: `data/raw/bi_pihps/pihps_pedagang_besar_harian_2017-2026_retrieved_2026-11-25.zip` (0,9 MB, 34 provinsi, 3.978 permintaan per bulan, 0 galat, ± 30 menit; format & MANIFEST sama dengan `pihps`). Didaftarkan sebagai sumber opsional `pihps_wholesale`. |
| Seperti apa datanya? | Sangat kaku: 85–98% sel mingguan carry_forward (observed 1–6%); grosir median 6–24% di bawah eceran. |
| Apakah grosir mendahului eceran? | **Tidak secara umum** (periode pengembangan): korelasi Δgrosir(t−1)→Δeceran(t) 0,07–0,37 vs Δeceran(t−1)→Δgrosir(t) 0,16–0,63; keduanya bergerak bersama. Untuk komoditas diatur, arah grosir 4 minggu cocok dengan arah eceran ke depan sedikit lebih sering dari momentum eceran (beras 0,650 vs 0,614; gula 0,701 vs 0,663; minyak goreng 0,636 vs 0,619; daging sapi 0,496 vs 0,441). |
| Menaikkan macro F1 C1-tuned? | **Tidak** (dev): semua fitur +0,001 / −0,002; perubahan grosir −0,006 / −0,002; selisih grosir–eceran −0,006 / −0,002; semua interval memuat nol → test tidak dibuka. Per komoditas ±0,02 tanpa pola (beras +0,009 di kedua horizon). |
| Model terpilih | **Tidak berubah**: C1-tuned (test 0,677 / 0,680). |

## 1. Pengambilan data

- Skrip `scripts/fetch_pihps.py`: endpoint `GetGridDataDaerah` (`price_type_id=3`, `tipe_laporan=1`) = data yang diekspor tombol
  "Download" resmi tabel pedagang besar; per provinsi per bulan karena biaya server naik tajam dengan panjang rentang (1 bulan ± 1 dtk,
  1 kuartal ± 7 dtk, 1 tahun ± 62 dtk); 3 permintaan paralel, jeda 0,2 dtk, coba ulang 3×, cache per (provinsi, bulan) di luar repo.
- Hasil: 34 CSV (25–31 baris, 2.384–2.448 hari, awal 2017-07..09, akhir 2026-11-19), `MANIFEST.csv` (sha256 per berkas, endpoint,
  price_type, retrieved_at 2026-11-25), `ERRORS.json` kosong. Berkas baru; tidak ada data mentah yang ditimpa.
- Pendaftaran: `configs/sources.yaml` (`pihps_wholesale`, `optional: true`, `redistribute: false`), `LOADERS` (memakai ulang
  `load_pihps`), `tests/test_loaders.py`, `docs/DATASETS.md`, CLAUDE.md §10.1. Cakupan izin BI (U13) untuk jenis pasar ini dan
  status unduh resmi (U19) tetap `[HUMAN]`.

## 2. Panel & lead-lag (`scripts/ws_build.py` → `hasil/ws_coverage.csv`, `hasil/ws_leadlag.csv`)

Panel mingguan dengan `select_variants` + `aggregate_weekly` resmi (varian representatif sama).

| Komoditas | carry_forward | seri layak | median log grosir − eceran | corr Δgrosir(t−1), Δeceran(t) | corr Δeceran(t−1), Δgrosir(t) | arah grosir 4 mgg vs eceran +4 / +8 | arah eceran 4 mgg vs eceran +4 / +8 |
|---|---|---|---|---|---|---|---|
| beras | 0,983 | 34 | −0,071 | 0,111 | 0,159 | 0,650 / 0,634 | 0,614 / 0,605 |
| gula pasir | 0,948 | 33 | −0,097 | 0,321 | 0,364 | 0,701 / 0,688 | 0,663 / 0,647 |
| minyak goreng | 0,952 | 29 | −0,095 | 0,095 | 0,414 | 0,636 / 0,621 | 0,619 / 0,614 |
| daging sapi | 0,928 | 32 | −0,060 | −0,063 | 0,193 | 0,496 / 0,509 | 0,441 / 0,437 |
| daging ayam | 0,913 | 33 | −0,178 | 0,068 | 0,536 | 0,463 / 0,404 | 0,475 / 0,412 |
| telur ayam | 0,944 | 34 | −0,094 | 0,236 | 0,506 | 0,495 / 0,431 | 0,497 / 0,429 |
| bawang merah | 0,938 | 33 | −0,241 | 0,366 | 0,528 | 0,570 / 0,498 | 0,572 / 0,500 |
| bawang putih | 0,944 | 34 | −0,228 | 0,220 | 0,459 | 0,592 / 0,575 | 0,571 / 0,559 |
| cabai merah | 0,931 | 33 | −0,234 | 0,067 | 0,538 | 0,490 / 0,455 | 0,496 / 0,447 |
| cabai rawit | 0,846 | 29 | −0,195 | 0,266 | 0,629 | 0,445 / 0,418 | 0,453 / 0,411 |

Korelasi kontemporer Δgrosir–Δeceran 0,20–0,62. Uji kebocoran fitur grosir (merusak grosir & eceran sesudah origin, 2 origin): fitur
≤ origin identik.

## 3. Pilot C1-tuned + fitur grosir (`scripts/ws_exp.py`, `scripts/ws_eval.py` → `hasil/ws_dev_*.csv`)

Fitur (hanya s.d. minggu t; grosir di-ffill ≤ 8 minggu seperti `price_dynamics`): `ws_dp_1/4/8` (Δ log grosir), `ws_nat_dp_4`
(rerata komoditas lintas provinsi), `ws_gap` (log grosir − log eceran), `ws_gap_dev52` (`ws_gap` − rerata 52 minggu), `ws_rel_4`
(Δ4 grosir − Δ4 eceran). 528 dtk lokal; `base` = C1-tuned resmi.

| Varian | Δ macro F1 dev h 4 (interval) | Δ h 8 (interval) | Keputusan |
|---|---|---|---|
| `W_DP` perubahan grosir | −0,006 (−0,011..0,001) | −0,002 (−0,010..0,005) | tidak |
| `W_GAP` selisih grosir–eceran | −0,006 (−0,013..0,001) | −0,002 (−0,008..0,005) | tidak |
| `W_ALL` semua | +0,001 (−0,006..0,009) | −0,002 (−0,011..0,005) | tidak |

Per komoditas (`hasil/ws_dev_per_commodity.csv`, `W_ALL` − base): h 4 −0,021 (daging sapi) .. +0,016 (cabai rawit); h 8 −0,015 ..
+0,010; beras +0,009 di kedua horizon, gula 0,000 / −0,011, minyak goreng −0,013 / +0,003. Tidak ada kandidat yang lolos → **test
tidak dibuka**.

## 4. Kesimpulan

- Harga grosir PIHPS hampir selalu bergerak bersama atau sesudah eceran dan sangat kaku; sinyal arah yang tampak pada komoditas diatur
  sudah terwakili oleh fitur momentum eceran & sinyal nasional C1-tuned. Sumber ini **tidak** menambah daya prediksi arah.
- Dengan ini, tuas yang tersisa untuk menaikkan skor arah adalah informasi yang benar-benar mendahului eceran: harga tingkat petani/
  penggilingan/peternak (Panel Harga Bapanas, akses terbatas via SAPA, `[HUMAN]`) atau pasokan fisik; keduanya tidak realistis
  sebelum pembekuan hasil 2026-11-27.
- Data grosir tetap tersimpan sebagai sumber opsional (berguna untuk analisis margin/transmisi deskriptif), tidak dipakai model atau
  artefak resmi. `src/` hanya bertambah satu entri `LOADERS`; `params.yaml` dan artefak tidak berubah.
