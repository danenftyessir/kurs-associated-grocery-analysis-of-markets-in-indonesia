# K4 — Data Understanding (Fase B, EKSPLORATIF, D-164)

Tanggal: 2026-11-26. `scripts/k4_du.py` → `hasil/du_*.csv`, `du_summary.json` (± 6 menit). **Hanya data s.d. 2023-12-31**: universe
evaluasi = origin dev resmi (38 / 37 origin, 2021-01-04 .. origin + h ≤ 2023-12-31); analisis waktu B3 memakai setiap minggu 2018-07-02 ..
2023-12-31 − h dengan ambang walk-forward per minggu. Test 2024+ tidak dibaca (laju test 0,088 / 0,089 dikutip dari D-154).

Universe dev: 12.800 / 12.463 baris (h 4 / h 8) = 25.259 baris resmi + 4 tanpa target (sama dengan D-155). Kontrol: M_h ≥ y_h di semua baris.

## B1. Distribusi target (P80 |y|, `du_b1_distribution.csv`)

| Komoditas | n (h 4) | naik material | naik non-material | turun | tetap | laju z h 4 / h 8 | ambang median h 4 (Rp) | positif per seri (h 4) |
|---|---|---|---|---|---|---|---|---|
| beras | 1.292 | 258 | 273 | 240 | 521 | 0,200 / 0,244 | 1,2% (Rp151) | 7,6 |
| daging sapi | 1.292 | 196 | 213 | 314 | 569 | 0,152 / 0,176 | 1,6% (Rp2.073) | 5,8 |
| gula pasir | 1.292 | 156 | 396 | 385 | 355 | 0,121 / 0,122 | 3,2% (Rp453) | 4,6 |
| minyak goreng | 1.286 | 309 | 252 | 484 | 239 | 0,240 / 0,293 | 2,4% (Rp521) | 9,1 |
| telur ayam | 1.292 | 129 | 502 | 643 | 18 | 0,100 / 0,094 | 9,3% (Rp2.607) | 3,8 |
| daging ayam | 1.292 | 72 | 587 | 596 | 37 | 0,056 / 0,054 | 13,4% (Rp4.832) | 2,1 |
| bawang putih | 1.292 | 34 | 598 | 603 | 57 | **0,026 / 0,024** | 13,8% (Rp4.522) | **1,0** |
| bawang merah | 1.292 | 97 | 516 | 663 | 16 | 0,075 / 0,064 | 22,8% (Rp7.892) | 2,9 |
| cabai merah | 1.292 | 145 | 471 | 661 | 15 | 0,112 / 0,134 | 37,2% (Rp16.600) | 4,3 |
| cabai rawit | 1.178 | 139 | 438 | 596 | 5 | 0,118 / 0,119 | 49,3% (Rp28.883) | 4,5 |
| **Semua** | 12.800 | 1.535 | 4.246 | 5.185 | 1.832 | **0,120 / 0,132** | – | 4,6 |

- Kelas positif jarang (12–13%) dan **sangat timpang antarkomoditas** (0,02–0,29). Bawang putih hanya 34 / 30 positif di dev (± 1 per seri),
  ayam 72 / 68: terlalu sedikit untuk model per komoditas atau per seri → model gabungan dengan identitas komoditas.
- Persentil perubahan h 4 (p5 / median / p95): beras −1,2% / 0 / +4,2%; minyak goreng −6,2% / 0 / +9,5%; cabai rawit −42% / −0,7% / +76%.
  Perubahan nominal median 0 untuk komoditas diatur; p95 Rp545 (beras) .. Rp36.390 (cabai rawit).

## B2. Ambang walk-forward (`du_b2_thresholds.csv`)

| | P70 | **P80** | P90 |
|---|---|---|---|
| Laju z h 4 / h 8 | 0,171 / 0,183 | **0,120 / 0,132** | 0,066 / 0,078 |
| Laju z_any h 4 / h 8 | 0,198 / 0,235 | 0,137 / 0,168 | 0,075 / 0,099 |
| Positif terkecil (komoditas) | bawang putih 111 / 101 | bawang putih 34 / 30 | bawang putih **5 / 1** |

- P90 membuat bawang putih praktis tanpa positif → tidak dipakai sebagai utama; hanya kepekaan (K4-E90).
- Ambang bergeser sepanjang dev: bawang putih h 4 19,8% (origin pertama) → 11,9% (terakhir), gula 4,2% → 2,8%, minyak goreng 1,3% → 2,6%. Ambang
  walk-forward menyerap perubahan rezim volatilitas secara lambat (jendela ekspansif sejak 2017).

## B3. Waktu, musim, kebijakan, lokasi (`du_b3_*.csv`)

| Dimensi | h 4 | h 8 |
|---|---|---|
| Per tahun 2018 / 2019 / 2020 / 2021 / 2022 / 2023 | 0,076 / 0,138 / 0,126 / 0,122 / 0,117 / 0,118 | 0,071 / 0,167 / 0,126 / 0,133 / 0,131 / 0,125 |
| Bulan origin terendah (Jul) / tertinggi | 0,051 / 0,163 (Apr, Nov) | 0,053 / 0,185 (Nov) |
| Komoditas diatur 2021 / 2022 / 2023 | 0,199 / 0,172 / 0,168 | 0,232 / 0,203 / 0,190 |
| Tidak diatur 2021 / 2022 / 2023 | 0,070 / 0,079 / 0,083 | 0,065 / 0,082 / 0,080 |
| ≤ 13 minggu sesudah perubahan HET/HAP konsumen vs lainnya | 0,082 vs 0,122 | 0,078 vs 0,133 |
| Antarprovinsi (min .. maks, sd) | 0,087 .. 0,149 (sd 0,015) | 0,096 .. 0,160 (sd 0,017) |
| Laju mingguan: sd; p10–p90 | 0,072; 0,04–0,22 | 0,084; 0,04–0,26 |
| Laju per origin evaluasi (min .. maks) | 0,030 .. 0,282 | 0,024 .. 0,344 |
| Laju latih yang diketahui pada origin − laju terealisasi: rerata (sd) | +0,011 (0,072) | +0,018 (0,085) |

- **Pergeseran waktu jauh lebih besar dari perbedaan lokasi**: sd laju mingguan 0,07–0,08 vs sd antarprovinsi 0,015 (sama dengan pola galat
  arah D-156: ditentukan waktu, bukan lokasi). Laju latih (yang diketahui) meleset ± 0,07–0,085 dari laju terealisasi per origin.
- **Musim kuat**: Jun–Agu 0,05–0,09 vs Nov–Apr 0,15–0,19 → pembanding laju-dasar komoditas × bulan (B-CLIMS) wajib.
- Komoditas diatur naik sejak 2021 (0,17–0,23) sedangkan tidak diatur turun (0,07–0,08); laju test 2024+ 0,09 (D-154) → **laju historis tidak
  dapat dianggap tetap**; kalibrasi peluang mentah akan bergeser.
- Sesudah perubahan harga acuan konsumen laju justru lebih rendah (0,08 vs 0,12–0,13): kenaikan HET/HAP yang ditetapkan menyerap kenaikan sebelum
  tanggal penetapan (deskriptif; tidak dipakai sebagai fitur).
- Autokorelasi laju mingguan pada lag h: 0,48 (h 4), 0,20 (h 8) → laju terakhir yang terealisasi hanya sebagian memprediksi laju origin berikutnya.

## B4. Kualitas label (`du_b4_*.csv`)

| Ukuran | h 4 | h 8 |
|---|---|---|
| Positif < 2 tick Rp50 | 0% | 0% |
| Positif < 5 tick | 5,5% | 0,4% |
| Ambang dalam tick (median semua baris) | 63 | 89 |
| Positif dalam ± 1 tick dari ambang (label berbalik dengan 1 tick) | 7,2% (beras 22,5%, gula 8,3%, minyak 8,1%) | 4,5% (beras 12,7%) |
| Arah positif tak stabil terhadap resample hari (flip ≥ 5%) | 1,0% | 0,3% |
| Positif dengan ≥ 1 ujung carry-forward | 62% (vs 58% semua baris) | 64% (vs 58%) |
| Target tidak teramati | 2 | 2 |
| Kejadian kapan pun (z_any) / titik akhir (z) | 0,137 / 0,120 | 0,168 / 0,132 |
| Lonjakan yang berbalik (z_any = 1, z = 0) / z_any | 12% (ayam 32%, bawang putih 40%) | 21% (telur 43%, ayam 44%, cabai rawit 28%) |

- Label kenaikan material **jauh lebih kokoh** daripada label arah: masalah sub-tick & komposisi hari (D-147: 8–12% arah tak stabil) hampir
  hilang karena ambang jauh di atas 1 tick, kecuali pada beras (± 3 tick; 22% positif berada dalam 1 tick dari ambang).
- Carry-forward tidak dibuang (kekakuan nyata). Tidak ada baris yang dihapus dari evaluasi.

## Implikasi untuk modeling (masuk kartu PROTOCOL §1)

1. Pembanding laju-dasar per komoditas (± bulan) wajib: komposisi target menjamin aturan "pantau komoditas yang biasanya naik" sudah kuat.
2. Model gabungan dengan identitas komoditas; tidak ada model per seri (± 4–5 positif per seri).
3. Kalibrasi diuji walk-forward; laju bergeser kuat antarorigin, jadi peluang mentah diharapkan meleset di origin ekstrem.
4. Komposisi P80 |y| didominasi komoditas diatur → kepekaan K4-S90 (desil atas kenaikan bertanda) agar terlihat apakah keunggulan model hanya
   berasal dari komoditas diatur.
5. Target kejadian berbeda nyata untuk ayam, telur, bawang putih (lonjakan berbalik 30–44%) → relevan bila TPID bereaksi pada lonjakan sementara.
