# Protokol D-151 — pilot informasi intraminggu & harga produsen PIHPS (Task 4 arah, EKSPLORATIF)

Ditulis 2026-11-25 17:37 WIB, **sebelum** fitur dibangun dan sebelum ada hasil. Berkas ini tidak diubah sesudahnya; sha256-nya
dicatat di laporan. Lanjutan D-145–D-150; bukan uji praregistrasi (H5 tetap dari MAE + DM).

## 1. Yang dibekukan (tidak diubah oleh eksperimen ini)

- Pembanding `base` = C1-tuned: kolom `tuned_columns("C1t", h)`, `TUNED_HGB`, `random_state = cfg.seed`, threshold 0,5.
  Sebelum eksperimen, `base` dicek mereproduksi `direction_tuned_preds` (C1t) pada baris yang sama.
- Label: tanda y_h resmi (log rerata hari teramati minggu t+h − minggu t); y = 0 dikeluarkan. Baris evaluasi = baris rolling-origin
  Task 4 (`split_origin`, latih t + h ≤ origin). Tidak ada varian yang mengubah label, baris evaluasi, penyaring latih, atau bobot.
- Preprocessing beku (D-148). Artefak resmi, `params.yaml`, dan model di `src/` tidak berubah.

## 2. Pembagian origin

- Seleksi hanya di origin **pengembangan**: origin + h ≤ 2023-12-31.
- Test final (origin ≥ 2024-01-01) dibuka **sekali** dan hanya untuk kandidat yang lolos §4. Split D-149 (dev s.d. 2024) tidak dipakai
  untuk seleksi.
- Keluarga A memuat `iw_gap`, yang sudah dilihat di test pada D-147 (+0,004 / +0,005). Hasil test keluarga A ditandai
  "test sudah pernah dilihat untuk fitur sejenis" dan tidak boleh dibaca sebagai konfirmasi bersih.

## 3. Kandidat (daftar tetap)

Semua fitur hanya memakai informasi s.d. akhir minggu origin t (Senin–Jumat minggu t dan sebelumnya).

**Keluarga A — informasi intraminggu** (dari `pihps_daily`, hari teramati minggu t):
`iw_gap` = log harga hari terakhir − log rerata minggu; `iw_return` = log hari terakhir − log hari pertama; `iw_range` = log maks −
log min; `iw_vol` = sd (ddof 0) Δlog harian dalam minggu (≥ 2 perubahan, selain itu NaN); `iw_n_days` = jumlah hari teramati;
`iw_last_age` = 4 − hari-dalam-minggu hari teramati terakhir (0 = Jumat). Minggu tanpa hari teramati → NaN (n_days 0).

| Varian | Kolom tambahan di atas C1-tuned | Peran |
|---|---|---|
| `IW_REF` | `iw_gap`, `iw_n_days` | acuan D-147 (sudah dibuka di test) — **bukan kandidat** |
| `IW_FULL` | 6 fitur di atas | kandidat |
| `IW_NAT` | `IW_FULL` + `iw_gap_nat`, `iw_return_nat` (rerata komoditas lintas provinsi yang teramati minggu t) | kandidat |

**Keluarga B — harga produsen PIHPS** (`price_type_id=4`, varian representatif & agregasi mingguan resmi `select_variants` +
`aggregate_weekly`; **tanpa** ffill atau interpolasi; minggu tanpa harga produsen = NaN):

| Varian | Kolom tambahan di atas C1-tuned |
|---|---|
| `PR_DYN` | `pr_dp_1`, `pr_dp_4`, `pr_dp_8` (Δ log produsen; NaN bila salah satu ujung kosong), `pr_vol_13` (sd Δ1 13 minggu, ≥ 6 nilai), `pr_age` (minggu sejak harga produsen teramati terakhir, maks 52) |
| `PR_TRANS` | `PR_DYN` + `pr_gap` (log eceran − log produsen), `pr_gap_chg_1/4/8`, `pr_gap_dev52` (`pr_gap` − rerata 52 minggu, ≥ 26 nilai) |
| `PR_ALL` | `PR_TRANS` + `pr_nat_dp_1/4/8` (rerata lintas provinsi teramati), `pr_nat_up_4` (porsi provinsi pr_dp_4 > 0), `pr_nat_disp_4` (sd lintas provinsi pr_dp_4), `pr_nat_n` (jumlah provinsi teramati minggu t) |

Tidak ada kombinasi lintas keluarga di ronde ini. Tidak ada tuning hyperparameter atau threshold.

## 4. Aturan keputusan (sama dengan D-147–D-150)

Kandidat lolos pengembangan bila: (a) Δ macro F1 rerata (h 4, h 8) vs `base` ≥ +0,005; (b) interval bootstrap blok origin berpasangan
(1.999 replikasi) > 0 di ≥ 1 horizon; (c) Δ ≥ 0 di horizon lain. Per keluarga, paling banyak **satu** kandidat membuka test: yang lolos
dengan Δ rerata dev terbesar (seri → lebih sedikit kolom). Hasil test dilaporkan dengan q BH atas semua kandidat yang dibuka × horizon,
dan tidak dipakai untuk memilih ulang apa pun.

Wajib dilaporkan untuk setiap varian (bukan gerbang): Δ macro F1 pada kuintil |y| terkecil (ambang kuintil dari `base` per horizon)
beserta n, Δ per komoditas, dan porsi prediksi naik. Bila Δ kuintil terkecil < −0,01 di kedua horizon, kandidat ditandai walaupun lolos.

## 5. Pemeriksaan wajib sebelum pilot

- Kebocoran: data harian/produsen dan eceran sesudah origin dirusak → semua fitur ≤ origin identik (≥ 2 origin, satu dev, satu test).
- Kelayakan produsen: cakupan per komoditas (provinsi, porsi minggu teramati, carry_forward), awal riwayat, lead-lag pada periode
  pengembangan (korelasi Δprodusen(t−k) → Δeceran(t) vs sebaliknya). Keterbatasan yang dicatat: PIHPS dapat direvisi s.d. H+1 dan
  vintage tidak tersedia, jadi evaluasi tetap pseudo-real-time; cakupan izin BI (U13) & status unduh resmi (U19) tetap `[HUMAN]`.
