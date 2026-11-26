# Penutupan kelemahan tercatat: U108, U107, fitur clustering konstan, IW_NAT (D-162, D-163)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-162 (U108), D-163 (U107 & fitur konstan) · Skrip:
`20261126_kelemahan_tercatat/scripts/` · Hasil: `20261126_kelemahan_tercatat/hasil/` · Cadangan artefak lama: scratchpad sesi
(`backup_pre_d162/`, tidak di-commit; versi lama `national_calibrated` juga ada di git).

## 1. U108 — flag `episode` real-time (D-162, perbaikan bug)

**Masalah.** Fitur `episode` (grup fx Task 4: M2, M3, C2, C2t) diambil dari `drivers_weekly.episode` periode penuh: pemicu yang berjarak ≤ 8
minggu digabung, sehingga minggu di antara dua pemicu ditandai 1 sebelum pemicu kedua terjadi. **Perbaikan** (`data.drivers.realtime_episode_flag`,
dipakai `features.forecast`): flag minggu t = 1 bila t sendiri minggu pemicu (Σ de 8 minggu s.d. t ≥ 0,03). Ini identik dengan mendeteksi ulang
episode hanya dari data s.d. t (dites di setiap t). Data asli: 61 → 55 minggu bertanda; 6 minggu berbeda (semua minggu sela di dalam episode
gabungan); 1 origin uji berbeda (2024-12-02, h 4 & 8). `drivers_weekly.episode` (dipakai event study & robustness) tidak berubah.

**Artefak dijalankan ulang** (CLI, tercatat di `logs/`): `forecast_preds` + `forecast_eval` + `ablation` (M0–M3 + M2_nofx), `direction_preds`
(C1/C2), `direction_tuned_preds` (hanya C2t; baris C1t dipertahankan). Perbandingan sebelum/sesudah: §1a (diisi setelah run).

## 2. U107 — interval nasional PT & deviasi provinsi terkalibrasi plasebo (D-163)

Bootstrap blok 13 minggu menarik estimasi ke nol (D-129). Untuk nasional β_e & ω sudah ada `national_calibrated`; PT dan provinsi tadinya
menjadi keterbatasan. Tambahan (bukan pengganti interval praregistrasi):

- **PT nasional** (baris `driver = PT` di `national_calibrated`): PT = β_e/γ(h), jadi interval terkalibrasi = interval β_e terkalibrasi / γ;
  p dan q sama dengan baris e (keluarga BH 48 sel tidak berubah; baris e/w identik dengan versi lama). Hasil: 3/30 sel tidak memuat nol —
  daging ayam h 4 −0,81 (−1,45..−0,16) dan h 8 −1,27 (−2,10..−0,44), gula h 4 0,48 (0,18..0,78) — vs 1/30 pada interval resmi (persentil
  bootstrap). Lebar median hampir sama (1,59 vs 1,57); bedanya interval kini berpusat pada estimasi, tidak tergeser ke nol.
- **Deviasi provinsi** (artefak baru `province_calibrated`, 1.623 baris = provinsi layak × 10 komoditas e / 6 komoditas w × h 4/8/12): null
  |t*| dipool antarprovinsi per sel (6.169–16.966 nilai), crit median 2,05–2,22. Diagnosis: replikasi bootstrap provinsi juga tertarik ke
  nol (median boot_ratio 0,51–0,67); interval resmi provinsi memuat nol hampir selalu (sel tidak memuat nol 0–2,4%, di bawah 5% bahkan di
  bawah null), sedangkan ±1,96·SE terlalu longgar (6–17%). Terkalibrasi: 5–12% sel tidak memuat nol; q BH per sel (34 provinsi) < 0,05 pada
  37 sel — daging ayam β_e h 4/8 (10), gula β_e (11), telur β_e h 8 (9, terutama Jawa negatif & Maluku Utara positif), minyak goreng ω (5),
  beras ω (1). Dengan BH global atas 1.623 sel tersisa 7: daging ayam (Maluku, Papua, Kepulauan Riau), gula (Kalimantan Barat & Tengah),
  minyak goreng ω (Maluku Utara). Konsisten dengan G-het (H0-Het ditolak telur & daging ayam; gula q 0,067). Uji konfirmatori heterogenitas
  tetap H0-Het; tabel ini deskriptif ("provinsi mana yang menyimpang"), bukan klaim kausal.

## 3. 13/33 fitur clustering konstan (D-163, tanpa perubahan kode)

Kolom konstan = komoditas × h dengan τ² = 0 sehingga EB menyusutkan semua provinsi ke rerata. Diuji: jarak antarprovinsi identik dengan dan
tanpa 13 kolom itu; silhouette sama (k* = 3, 0,184 < p95 plasebo 0,196 → k = 1). Karena pembulatan float, sebagian kolom bernilai
konstan ±1 (bukan 0) setelah z-score; tetap konstan, jadi tidak berpengaruh. Pada 40 matriks replikasi plasebo, 553 kolom konstan dan 0
kolom yang derau float-nya diperbesar menjadi pola. Kesimpulan: tidak ada yang perlu dioptimasi; dimensi efektif 20.

## 4. IW_NAT (tidak dapat ditutup sekarang)

Keunggulan test +0,0085 / +0,0033 (q 0,28 / 0,30) hanya dapat dikonfirmasi lewat prediksi maju yang dibekukan D-152/D-158; target lengkap
2027-01-15. Tidak ada tindakan selain memastikan `forward_preds.csv` dan `forward_preds_d158.csv` ikut di-commit.
