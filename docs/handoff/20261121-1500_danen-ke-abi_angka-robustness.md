---
dari: Danen
ke: Abi
jenis: ANGKA-MAKALAH
terkait: WP-28, WP-29, WP-30, WP-33, D-111, D-114, D-116
status: terbuka
dibuat: 2026-11-21 15:00
tenggat_respon: 2026-11-25
---

# Angka robustness & validasi (Tier 1, V2/V4, Tier 2) untuk bagian "Hasil eksperimen & pengujian"

## Ringkasan
Robustness Tier 1, validasi V2/V4, dan Tier 2 sudah dijalankan pada data asli (LP nasional, 10 komoditas, h = 4/8/12). Hasil utama
**tidak bergantung** pada pilihan lag, varian harga, cara agregasi mingguan, atau sumber harga (PIHPS vs Panel Harga Bapanas).
Yang peka: asosiasi daging ayam melemah tanpa Mar–Jun 2020 & bulan Brent ekstrem. Angka ini **sementara**: interval = ±1,96·SE
cluster minggu (bootstrap WP-16 belum ada) dan artefak `robustness` baru ditulis setelah `profiles`/`forecast_eval` Ardell terbit.
Pakai untuk menyusun draf; angka final menyusul lewat handoff `TERBIT`.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Tabel angka & kalimat makalah | file ini | 2026-11-21 | dari kode `evaluation.robustness` di `dev` |
| Metode robustness | `docs/METHODS.md` §M5 | – | untuk subbagian metode/matriks evaluasi |
| Keputusan teknis | `docs/DECISIONS.md` D-111, D-114, D-116 | – | rujukan bila juri bertanya rincian |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- Tidak ada DEVIASI PRAREGISTRASI (Tier 1 = cek wajib praregistrasi; Tier 2 = cek opsional yang disebut tanpa rincian, D-116).

## Yang perlu dilakukan penerima
- [ ] Abi: susun subbagian robustness & validasi di makalah dari tabel dan kalimat di bawah (semua sudah sesuai rambu CLAUDE.md §20).
- [ ] Abi: tandai angka di draf sebagai "sementara" sampai handoff `TERBIT` artefak `robustness` (interval bisa melebar setelah bootstrap).
- [ ] Abi: jangan menulis Kendall ordinal (Tier 2) sebagai hasil E1; E1 resmi memakai rasio impor (WP-22, menunggu tabel `exposure`).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_robustness.py
```
Hasil yang diharapkan: semua lolos. Angka data asli dihasilkan ulang dengan `python -m kagami robustness --tier2` setelah input tahap
1 dan 4 tersedia (Kaggle/lokal dengan data mentah).

## Angka penting
Satuan β/ω: perubahan log harga eceran per 1 poin log penggerak (β = 1 berarti depresiasi 1% berasosiasi dengan kenaikan harga 1%).
Interval 95% = ±1,96·SE cluster minggu (sementara).

**A. Baseline nasional h = 8 (konteks)** — sumber: `profiles` (LP nasional, dihitung ulang lokal)

| Komoditas | β_e(8) kurs | ω(8) harga dunia rupiah |
|---|---|---|
| beras | 0,005 (−0,17..0,18) | 0,064 (−0,01..0,14) |
| bawang putih | −0,68 (−2,93..1,58) | – |
| gula pasir | 0,66 (−0,12..1,44) | −0,004 (−0,22..0,21) |
| minyak goreng | −0,23 (−0,58..0,12) | **0,21 (0,08..0,34)** |
| daging ayam | **−1,67 (−2,62..−0,73)** | −0,26 (−0,55..0,03) |
| telur ayam | −0,53 (−1,11..0,05) | **−0,22 (−0,40..−0,04)** |
| daging sapi | 0,016 (−0,10..0,13) | −0,004 (−0,05..0,04) |
| bawang merah | −0,81 (−2,52..0,89) | – |
| cabai merah | 1,37 (−1,26..4,00) | – |
| cabai rawit | 0,76 (−2,63..4,14) | – |

**B. Tier 1 (6 cek wajib; 382 baris)** — sumber: `robustness` tier 1

| Cek | Sel | Baseline di dalam interval cek | Pembalikan tanda dengan interval tanpa nol |
|---|---|---|---|
| lag 2 / 8 (vs 4) | 96 | 100% | 0 |
| dekomposisi kurs (dolar global vs spesifik rupiah) | 78 | 100% | 0 |
| frekuensi bulanan | 48 | 98% | 0 |
| h 12 vs h 8 | 16 | 94% | 0 |
| tanpa Mar–Jun 2020 & bulan Brent ekstrem | 48 | 94% | 0 |
| sub-periode sebelum/sesudah 2021-04-05 | 96 | 89% | 0 |

Daging ayam β_e(8): baseline −1,67 (−2,62..−0,73); tanpa COVID & Brent ekstrem −0,96 (−2,05..0,14); komponen spesifik rupiah
−1,89 (−3,02..−0,76); komponen dolar global −1,35 (−3,04..0,34); sebelum 2021-04 −1,71 (−2,81..−0,60), sesudah −0,97 (−2,32..0,37);
bulanan −0,60 (−1,33..0,13). Komponen dolar global menjelaskan 27% variasi Δ kurs mingguan (b = 0,72).

**C. Validasi** — sumber: `robustness` tier V

| Validasi | Hasil |
|---|---|
| V4: respons LP yang diimplikasikan vs rerata kelebihan respons 12 episode (di atas median plasebo) | di dalam interval 26/30 sel (komoditas fokus 17/18); kesesuaian tanda per episode rata-rata 0,51 |
| V2: episode 2026-05-18..2026-07-06 (Σ Δlog kurs 0,051) | 30/30 sel (10 komoditas × h 4/8/12) di dalam pita plasebo 95% |

**D. Tier 2 (opsional; 187 baris)** — sumber: `robustness` tier 2

| Cek | Hasil |
|---|---|
| 11 varian PIHPS lain + 3 komposit harga pakan | baseline di dalam interval 94/96 sel |
| harga mingguan = hari teramati terakhir | 48/48 sel |
| outcome Panel Harga Bapanas bulanan 2022–2026 vs PIHPS bulanan bulan yang sama | 42/42 sel |
| pengecualian | gula Kualitas Premium β_e(4) 0,36 (0,15..0,57) vs Lokal 0,69; Minyak Goreng Curah ω(8) 0,36 (0,26..0,45) vs Kemasan 0,21 |
| daging ayam β_e(8) per komposit pakan | jagung −1,79; bungkil kedelai −1,64; bobot sama −1,64; observasi terakhir −1,57 (baseline −1,67) |

**Kalimat untuk makalah** (sudah sesuai rambu klaim):
1. "Estimasi respons nasional tidak bergantung pada panjang lag: pada lag 2 dan 8 minggu, estimasi utama selalu berada di dalam
   interval 95% spesifikasi alternatif (96 dari 96 sel), tanpa pembalikan tanda yang intervalnya mengecualikan nol."
2. "Asosiasi negatif antara IDR/USD dan harga daging ayam pada horizon 8 minggu (β = −1,67; interval 95% −2,62 hingga −0,73) melemah
   bila Maret–Juni 2020 dan bulan dengan perubahan harga Brent ekstrem dikeluarkan (−0,96; −2,05 hingga 0,14), tetapi tetap ada pada
   komponen kurs yang spesifik rupiah (−1,89; −3,02 hingga −0,76). Hasil ini bersifat asosiasional; kami tidak mengamati rantai pasok."
3. "Respons yang diimplikasikan local projections berada di dalam interval rerata respons 12 episode depresiasi pada 26 dari 30 sel
   (17 dari 18 untuk komoditas fokus), sehingga kedua pendekatan konsisten pada tingkat rerata; pada tingkat episode tunggal, tanda
   keduanya hanya sama pada sekitar separuh episode."
4. "Pada episode depresiasi Mei–Juli 2026, perubahan harga 10 komoditas pada 4, 8, dan 12 minggu tidak terdeteksi di atas variasi
   normal (30 dari 30 sel di dalam pita plasebo 95%)."
5. "Hasil tidak berubah bila harga dihitung dari varian lain dalam komoditas yang sama, dari hari teramati terakhir tiap minggu, atau dari
   Panel Harga Bapanas (baseline di dalam interval pada 184 dari 186 sel). Minyak goreng curah menunjukkan asosiasi dengan harga sawit
   dunia yang lebih besar (0,36; 0,26 hingga 0,45) daripada minyak goreng kemasan (0,21; 0,08 hingga 0,34)."

Grafik: `viz.plots.forest(rob, ["check_id", "commodity", "horizon"], ...)` (notebook 05) untuk forest plot robustness.

## Batasan, risiko, yang belum beres
- Interval sementara (SE cluster); PT(8) belum punya interval sampai bootstrap WP-16 (Ardell).
- V2 forecast (rasio MAE Task 4 origin 2026) menunggu `forecast_eval` (P4).
- Tier 2: keterpencilan alternatif menunggu meta-regresi WP-23; baseline τ dengan rasio impor menunggu `exposure` WP-07.
- Arah negatif daging ayam berlawanan dengan dugaan jalur input impor; jangan ditafsirkan sebagai "pelemahan rupiah menurunkan harga".
  Tulis apa adanya sebagai asosiasi dan sebutkan kepekaannya terhadap periode 2020.
- Kendall τ-b PT(8) vs urutan jalur eksposur = −0,03 (−0,75..0,70), p eksak 1,00 adalah cek robustness, bukan hasil E1.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
