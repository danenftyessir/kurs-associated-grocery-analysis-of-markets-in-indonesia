# Business Understanding Task 4 arah (CRISP-DM fase 1) — tujuan, kriteria keberhasilan, rencana ukur

Ditulis 2026-11-25 sebelum pengukuran apa pun di fase ini; tidak diubah sesudahnya (sha256 di laporan). D-154, lanjutan D-153.

## 1. Tujuan bisnis

- **Pengguna**: TPID provinsi (dan koordinasi nasional BI/Kemendagri). Keputusan yang dibantu: menyiapkan instrumen pengendalian harga
  (operasi pasar/SPHP, kerja sama antardaerah, pemantauan stok, komunikasi) **4–8 minggu** sebelum kenaikan harga yang material, untuk
  10 komoditas strategis di wilayahnya.
- **Kebutuhan**: (a) daftar pantau, yaitu komoditas mana di provinsi saya yang paling mungkin naik secara material; (b) peluang yang dapat
  dipercaya (terkalibrasi); (c) arah yang benar saat harga memang bergerak besar.
- **Biaya kesalahan**: alarm palsu menghabiskan sumber daya & kredibilitas; kenaikan yang terlewat merugikan daya beli. Keduanya penting,
  sehingga ukuran presisi daftar pantau dan recall kenaikan material dilaporkan berdampingan.
- **Praktik pembanding (asumsi, belum divalidasi dengan pengguna)**: tanpa model, analis TPID membaca tren harga terbaru, tren nasional,
  posisi harga terhadap rata-rata beberapa minggu, dan pola musim tahun lalu. Model hanya bernilai bila mengalahkan aturan sederhana ini.
- **Batas klaim** (CLAUDE.md §20): keluaran ditulis sebagai sinyal peringatan dini berbasis pola historis dalam evaluasi rolling-origin,
  bukan ramalan; klasifier arah tetap eksploratif (H5 praregistrasi tidak berubah).

## 2. Tujuan data mining & kriteria keberhasilan (ditetapkan sebelum pengukuran)

Definisi **kenaikan material** (tanpa informasi masa depan, mengikuti aturan `large_move` = persentil `params.forecast.large_move_pct`
80): untuk origin o, horizon h, komoditas c, ambang `thr(o,h,c)` = persentil 80 dari |y_h| pada baris latih komoditas c (minggu + h ≤ o).
Kenaikan material: y_h ≥ thr. Pergerakan material: |y_h| ≥ thr. Label resmi & metrik utama tidak berubah.

| Kode | Tujuan DM | Ukuran | Kriteria berhasil (dev) |
|---|---|---|---|
| G0 | Arah (pembanding resmi) | macro F1 label resmi | dilaporkan; tidak menjadi gerbang (sudah D-145) |
| S1 | Daftar pantau provinsi (utama) | V1: tiap origin & provinsi, 2 komoditas skor tertinggi → presisi kenaikan material | presisi C1-tuned − aturan naif terbaik > 0 dengan interval berpasangan > 0 di **kedua** horizon |
| S1b | Daftar pantau nasional | V2: 10% seri skor tertinggi per origin → presisi & recall kenaikan material | dilaporkan (pendukung) |
| S2 | Peluang terkalibrasi | Brier skill terhadap klimatologi (porsi naik komoditas di baris latih origin) pada baris y ≠ 0; ECE 10 bin | Brier skill > 0 dengan interval > 0 **dan** ECE ≤ 0,05 di kedua horizon |
| S3 | Arah saat bergerak material | macro F1 pada baris \|y\| ≥ thr | C1-tuned > aturan tanda momentum (naik bila Δ4 > 0; Δ4 = 0 → naik) dengan interval > 0 di kedua horizon |
| S4 | Prediksi selektif | akurasi pada cakupan 25% / 50% paling yakin per origin | dilaporkan |

Aturan naif (skor dihitung dari informasi ≤ origin, tie dipecah acak dengan seed tetap): `R_mom` = Δ log 4 minggu sendiri (`lag_dp_4`);
`R_nat` = Δ4 nasional komoditas (`nat_dp_4`); `R_rev` = −deviasi dari MA 13 minggu (`dev_ma13`); `R_seas` = perubahan h minggu pada
periode yang sama tahun lalu (`yseas_52_h{h}`). "Aturan naif terbaik" = presisi tertinggi di dev (menguntungkan pembanding, konservatif).
Skor model = p_up C1-tuned (`direction_tuned_preds` C1t, sama dengan D-151 `base`). `IW_NAT` dilaporkan sebagai acuan eksploratif.

## 3. Rencana ukur & evaluasi

- Hanya origin pengembangan (target ≤ 2023-12-31). Inferensi: bootstrap blok origin berpasangan (blok ceil(h/4)+1, 1.999 replikasi).
- Test 2024+ dibuka **sekali**, hanya bila S1 lolos di dev, untuk C1-tuned dan aturan naif yang sama tanpa perubahan apa pun.
- Hasil yang tidak lolos tidak dilonggarkan kriterianya; kriteria dapat diubah hanya lewat protokol baru sebelum pengukuran berikutnya.
- Kondisi akhir fase: bila S1–S3 lolos → nilai bisnis C1-tuned dapat dinyatakan sebagai "daftar pantau yang mengalahkan aturan
  sederhana"; bila tidak → kebutuhan bisnis tidak terpenuhi dengan informasi PIHPS saat ini, dan hal itu dilaporkan sebagai batasan.
