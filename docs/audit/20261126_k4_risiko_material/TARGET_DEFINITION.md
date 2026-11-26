# K4 — Definisi target (EKSPLORATIF, D-164)

Tanggal: 2026-11-26. Ditetapkan sesudah DU dev dan sebelum modeling; bagian yang mengikat ada di [PROTOCOL.md](PROTOCOL.md) §2.
Kode: `scripts/k4_common.py` (`thresholds`, `split_k4`, `add_event`).

## 1. Pertanyaan

C1-tuned menjawab P(naik | y ≠ 0, X). K4 menjawab **P(kenaikan material | X)** untuk setiap seri (provinsi × komoditas) pada origin o, horizon
h ∈ {4, 8} minggu, memakai hanya informasi ≤ o.

## 2. Target utama: titik akhir, materialitas statistik

- y_h(t) = log p_{t+h} − log p_t, p = rerata hari teramati minggu itu (panel resmi; minggu hilang → NaN). Sama dengan target Task 4 resmi.
- thr(o, h, c) = persentil 80 dari |y_h| pada baris latih komoditas c: minggu t dengan t + h ≤ o, y_h dan lag harga tersedia. Dihitung ulang
  di setiap origin (walk-forward), **tidak pernah** dari seluruh dataset. Identik dengan ambang D-154 (`bu.py`).
- **z = 1[y_h ≥ thr]**. z = 0 untuk: turun, tetap (y = 0), naik di bawah ambang, dan target yang kemudian tidak teramati (D-155).
- Label baris latih memakai ambang origin o (satu ambang per komoditas per origin).

Contoh ambang (median origin dev, h 4 / h 8): beras 1,2% / 2,1% (± Rp150 / Rp255, ± 3 / 5 tick), daging sapi 1,6% / 2,2%, minyak goreng
2,4% / 3,9%, gula 3,2% / 6,0%, telur 9,3% / 12,4%, ayam 13% / 18%, bawang putih 14% / 23%, bawang merah 23% / 36%, cabai merah 37% / 58%,
cabai rawit 49% / 71%.

## 3. Mengapa P80 |y| menghasilkan target yang tidak seimbang antarkomoditas

Persentil diambil dari |y| (dua arah), sedangkan target hanya sisi naik. Untuk komoditas yang harganya simetris (cabai, bawang), separuh
pergerakan besar adalah penurunan → laju z ± 0,06–0,13. Untuk komoditas diatur (beras, daging sapi, gula, minyak goreng) harga hampir tidak
jarang turun dan 19–44% baris h 4 tidak berubah (beras 40%, daging sapi 44%, gula 27%, minyak goreng 19%) → hampir semua pergerakan besar adalah kenaikan kecil → laju z 0,12–0,29 dan ambang hanya beberapa
tick. Hasilnya: **60% / 64% kenaikan material (h 4 / h 8) adalah komoditas diatur**. Ini sifat definisi, bukan temuan tentang risiko.

| Definisi (DU dev) | Laju z h 4 / h 8 | Porsi positif komoditas diatur | Catatan |
|---|---|---|---|
| **P80 \|y\|** (utama) | 0,120 / 0,132 | 0,60 / 0,64 | aturan D-154 |
| P70 \|y\| | 0,171 / 0,183 | – | kepekaan |
| P90 \|y\| | 0,066 / 0,078 | – | bawang putih hanya 5 / 1 positif → tidak stabil |
| P90 y bertanda (K4-S90) | ± 0,10 per komoditas (desil atas kenaikan) | seimbang menurut konstruksi | kepekaan komposisi |
| Seragam ≥ 5% (ilustratif) | – | 0,13 / 0,19 | **bukan ambang TPID**; hanya menunjukkan bahwa komposisi berbalik ke hortikultura |
| Seragam ≥ 10% (ilustratif) | – | – | beras & daging sapi ≈ 0,005 |

## 4. Target alternatif: kejadian dalam jendela (Fase E)

- M_h(t) = max_{k=1..h} (log p_{t+k} − log p_t) atas minggu yang teramati (minggu hilang dilewati; semua hilang → NaN).
- **z_any = 1[M_h ≥ thr(o,h,c)]** dengan ambang yang sama dengan target utama (agar dapat dibandingkan; z_any ≥ z selalu).
- Laju dev 0,137 / 0,168; 12% / 21% kejadian adalah lonjakan yang kembali di bawah ambang pada minggu t + h ("berbalik"). Semua z = 1 juga z_any = 1.
- Baris latih hanya jendela yang sudah berakhir: t + h ≤ o. Tidak digabung dengan target utama; dievaluasi terpisah.

## 5. Kasus tepi

| Kasus | Perlakuan |
|---|---|
| y = 0 (harga identik; 14% / 9% semua baris, 19–44% baris komoditas diatur h 4) | z = 0; tetap di universe dan di baris latih K4 (beda dengan C1-tuned yang membuangnya) |
| Target tidak teramati (2 + 2 baris dev) | z = 0 di evaluasi (dihitung tidak kena); tidak ikut latih |
| Kenaikan tepat di sekitar ambang | Dihitung apa adanya; kepekaan: 7% / 4% positif berada dalam 1 tick dari ambang (beras 22% / 13%) |
| Tick Rp50 | Tidak ada positif < 2 tick (ambang median 63 / 89 tick keseluruhan; beras 3 / 5 tick) |
| Carry-forward di ujung | Tidak dibuang (kekakuan nyata, U22); 62% / 64% positif punya ≥ 1 ujung carry-forward |

## 6. Kontrol kebocoran target

Ambang dari baris latih saja; label latih = jendela yang berakhir ≤ origin (termasuk M_h); laju-dasar pembanding dari baris latih; kalibrator
dari origin lampau yang targetnya sudah terealisasi. Diuji dengan perturbasi data sesudah origin (`scripts/k4_leak.py`, PROTOCOL §4).
