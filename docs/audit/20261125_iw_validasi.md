# Validasi `IW_NAT`: Kebocoran Semua Origin, Diagnostik Lintas Provinsi, dan Pembekuan Prediksi Maju (EKSPLORATIF)

Tanggal: 2026-11-25 · Pelaksana: Danen (dengan agent) · Keputusan: D-152 · Lanjutan [D-151](20261125_pilot_produsen_intraminggu.md),
menjawab tinjauan pasca-D-151 (LOO, kebocoran semua origin, `available_at`, validasi maju). Catatan bertanggal (bukan dokumen hidup).
Skrip & hasil: [folder lampiran](20261125_iw_validasi/).

Protokol [`PROTOKOL.md`](20261125_iw_validasi/PROTOKOL.md) ditulis 18.50 WIB sebelum run apa pun di ronde ini; sha256
`3ec33d0f93b3f745b6f9c8abd664cbd6a6a23fb2ca1bfb1e8be762bb0ed0cf83`. Prinsip: **tidak ada kandidat baru**; `IW_NAT` dibekukan apa adanya,
semua varian baru hanya diagnostik di origin pengembangan, test 2024+ tidak dibuka.

## 0. Ringkasan

| Pertanyaan | Jawaban |
|---|---|
| Ada kebocoran pada fitur intraminggu? | **Tidak.** 83 origin (76 rolling + 8 maju, 1 sama) + 2 uji data penuh: hapus semua data sesudah cutoff, rusak harga sesudah cutoff, hapus 30% acak (pola kosong), rusak hanya provinsi lain → fitur ≤ origin identik di 84/84 uji yang berlaku. Kontrol positif (rusak Jumat minggu origin) terdeteksi 84/84. |
| Sinyal nasional berasal dari provinsi lain? | **Ya.** LOO (tanpa provinsi sendiri) berkorelasi 0,998 dengan rerata D-151 dan sama baiknya: `IW_NAT_LOO` − `IW_NAT` +0,005 (0,000..0,009) / +0,001 (−0,004..0,007) di dev. |
| Keserentakan arah menambah? | Tidak: `IW_BREADTH` − `IW_NAT` +0,003 / −0,004 (interval memuat nol). |
| Bergantung pada harga Jumat? | **Sebagian besar, untuk h 4**: tanpa Jumat −0,010 (−0,018..−0,001) vs `IW_NAT` (gagal ambang −0,005 yang ditetapkan); h 8 −0,004. Keuntungan h 4 vs C1-tuned turun dari +0,020 ke +0,010; keuntungan kuintil perubahan terkecil tetap (+0,026). |
| Prediksi maju dibekukan? | **Ya**: 8.112 prediksi (C1-tuned & `IW_NAT`, 338 seri × 4 origin h 4 + 8 origin h 8, origin 2026-09-28 .. 11-16 yang targetnya belum terealisasi), sha256 `28651b2b…`, dibekukan 2026-11-25 12.09 UTC; skrip evaluasi beku, uji label = target resmi (0 beda dari 311.440 baris). |
| Bisakah validasi maju mengonfirmasi `IW_NAT`? | **Praktis tidak.** MDE batch maju ± 0,08–0,12 (h 4) dan 0,04–0,06 (h 8); untuk mendeteksi selisih titik D-151 (+0,0085 / +0,0033) dibutuhkan ± 185 / 355 origin berjarak 4 minggu (± 14 / 27 tahun). Validasi maju hanya dapat mendeteksi kegagalan besar. |
| Model terpilih | **Tidak berubah**: C1-tuned. `IW_NAT` tetap varian eksploratif beku. |

## 1. Waktu ketersediaan & kebocoran (`scripts/iw2_build.py` → `hasil/leak_audit.csv`, `hasil/leak_summary.json`)

- Aturan eksplisit: fitur minggu t memakai hari teramati Senin–Jumat minggu t; PIHPS dapat direvisi s.d. H+1, jadi
  `available_at(t)` = Sabtu 00.00 (t + 5 hari) dan prediksi dianggap dibuat saat itu. Fitur C1-tuned resmi (rerata minggu t) memakai hari
  yang sama, jadi varian intraminggu tidak memperluas asumsi waktu; ia hanya memberi bobot lebih ke hari terakhir.
- Audit per cutoff, jendela data [origin − 13, origin + 26 minggu] (kebocoran = ketergantungan pada data sesudah cutoff; memotong masa lalu
  identik di kedua sisi tidak menyembunyikannya) + 2 origin data penuh. Fitur yang diuji: 8 kolom D-151, LOO, keserentakan, dan 8 kolom
  tanpa Jumat.

| Uji | Diuji | Lolos |
|---|---|---|
| (a) semua observasi sesudah cutoff dihapus | 84 | 84 |
| (b) harga sesudah cutoff dirusak (×exp(N(0; 0,5))) | 84 | 84 |
| (c) 30% observasi sesudah cutoff dihapus acak | 84 | 84 |
| (d) hanya provinsi lain dirusak → fitur nasional/LOO provinsi yang dinilai | 84 | 84 |
| (e) Jumat minggu origin dirusak → fitur tanpa Jumat tidak berubah | 84 | 84 |
| kontrol positif: (e) mengubah `iw_gap` minggu origin | 84 | 84 |

Origin 2026-11-16 tidak punya data sesudah cutoff maupun hari Jumat, jadi (a)–(e) tidak berlaku. Yang **tidak** dapat diuji adalah revisi
data sesudah cutoff: snapshot PIHPS memuat nilai akhir dan vintage tidak tersedia. Ini berlaku sama untuk C1-tuned; hanya prediksi maju
(§3) yang memakai data sebagaimana tersedia saat itu. Audit dijalankan sebagai skrip ber-assert, bukan pytest, karena fitur intraminggu
tidak ada di `src/`; bila kelak dipromosikan ke `src/features`, audit ini menjadi tes.

## 2. Diagnostik pengembangan (`scripts/diag.py` → `hasil/diag_dev_*.csv`)

| Varian (dev) | macro F1 h 4 / h 8 | Δ vs C1-tuned h 4 | Δ vs C1-tuned h 8 | Δ vs `IW_NAT` h 4 | Δ vs `IW_NAT` h 8 |
|---|---|---|---|---|---|
| C1-tuned | 0,656 / 0,676 | – | – | – | – |
| `IW_NAT` (D-151) | 0,676 / 0,681 | +0,020 (0,003..0,037) | +0,005 (−0,003..0,012) | – | – |
| `IW_NAT_LOO` | 0,680 / 0,682 | +0,024 (0,006..0,043) | +0,006 (−0,001..0,013) | +0,005 (0,000..0,009) | +0,001 (−0,004..0,007) |
| `IW_BREADTH` | 0,679 / 0,677 | +0,023 (0,007..0,039) | +0,001 (−0,009..0,008) | +0,003 (−0,004..0,009) | −0,004 (−0,011..0,002) |
| `IW_NAT_NOFRI` | 0,666 / 0,677 | +0,010 (−0,002..0,024) | +0,001 (−0,007..0,007) | **−0,010 (−0,018..−0,001)** | −0,004 (−0,010..0,001) |

- **Lintas provinsi nyata**: LOO memberi hasil yang sama atau sedikit lebih baik. Kontribusi provinsi sendiri di rerata nasional
  (1/34) tidak menjelaskan keuntungan. Selisih LOO − `IW_NAT` (+0,005) dari fitur yang berkorelasi 0,998 juga menunjukkan besarnya derau
  pelatihan HGB (± 0,005); selisih sekecil ini tidak boleh dibaca sebagai perbaikan. Sesuai protokol, LOO tidak menggantikan `IW_NAT`.
- **Ketergantungan pada Jumat**: separuh keuntungan h 4 hilang tanpa harga Jumat, sedangkan keuntungan di kuintil |y| terkecil tetap
  (+0,026, interval 0,012..0,043). Tafsiran: sebagian besar sinyal adalah *nowcast* level harga terkini. Label diukur dari rerata minggu t,
  yang tertinggal ± 2 hari dari harga hari terakhir, jadi harga terakhir (terutama secara nasional) memberi tahu ke mana rerata berikutnya
  bergeser. Informasi ini sah pada `available_at` Sabtu. Bila prediksi operasional harus dibuat sebelum harga Jumat final, perkirakan
  hanya ± separuh keuntungan h 4.
- Kuintil terkecil (dev): `IW_NAT_LOO` +0,031 / +0,009, `IW_BREADTH` +0,029 / +0,008, tanpa Jumat +0,026 / +0,008 vs C1-tuned.

## 3. Pembekuan prediksi maju (`scripts/fw_freeze.py`, `scripts/fw_eval.py` → `hasil/forward_preds.csv`, `hasil/forward_manifest.json`)

- Cek sebelum pembekuan: split maju = `split_origin` resmi pada 2 origin berlabel (latih & uji identik) dan p_up C1-tuned = artefak
  `direction_tuned_preds` C1t (maks |Δp| 0). `fw_eval.py --selftest`: label dari snapshot sekarang = y_4 / y_8 resmi (156.400 / 155.040 baris,
  0 beda).
- Origin maju (target belum terealisasi pada snapshot dengan hari terakhir 2026-11-18): h 4 2026-10-26, 11-02, 11-09, 11-16; h 8 2026-09-28 ..
  11-16. Minggu 2026-11-16 hanya Senin–Rabu, sesuai yang benar-benar tersedia. Hash kode di manifest sama dengan protokol.
- Isi: 8.112 baris; prediksi naik 62–84% (h 4) dan 71–87% (h 8), selaras dengan kecenderungan naik 2024+ (D-147). C1-tuned dan `IW_NAT`
  sepakat arah pada 95,3% baris, jadi selisih keduanya hanya ditentukan ± 5% baris.
- Target lengkap (snapshot memuat Jumat minggu t + h): origin pertama 2026-11-27 (h 4 10-26, h 8 09-28); semua h 4 pada 2026-12-18;
  semua h 8 pada 2027-01-15. Evaluasi: unduh snapshot PIHPS baru berformat `pihps` lalu `python fw_eval.py --pihps-zip <zip>`.
  **Agar pembekuan dapat diverifikasi, `forward_preds.csv` + manifest perlu di-commit sebelum 2026-11-27.**

## 4. Daya validasi maju (`scripts/power.py` → `hasil/forward_power.csv`)

SE selisih berpasangan dari interval test D-151: 0,0068 (h 4, 37 origin) / 0,0037 (h 8, 36 origin).

| | h 4 | h 8 |
|---|---|---|
| MDE test D-151 (α 0,05, daya 0,8) | 0,019 | 0,010 |
| MDE batch maju (setara 1–2 origin berjarak 4 minggu) | 0,08–0,12 | 0,04–0,06 |
| Origin berjarak 4 minggu untuk mendeteksi +0,0085 / +0,0033 | ± 185 (± 14 tahun) | ± 355 (± 27 tahun) |

Validasi maju tetap layak sebagai **penjaga** (kegagalan besar `IW_NAT` pada periode baru akan terlihat), tetapi bukan jalan untuk
"membuktikan" keuntungan sebesar ini. Keputusan memakai `IW_NAT` di luar eksperimen harus berupa pertimbangan biaya (ketergantungan pada
data harian, 8 kolom, keuntungan yang bergantung pada harga Jumat) terhadap keuntungan kecil yang konsisten arahnya, bukan menunggu
signifikansi.

## 5. Kesimpulan

- `IW_NAT` bersih dari kebocoran pada semua origin, sinyal nasionalnya berasal dari provinsi lain, dan separuh keuntungan h 4 berasal
  dari harga Jumat (nowcast level terkini). Tetap varian eksploratif beku; C1-tuned tetap model terpilih untuk makalah dan app.
- Eksplorasi keluarga intraminggu di origin pengembangan dihentikan (sudah dipakai di D-147, D-151, dan D-152, dan test 2024+ dua kali;
  selisih yang tersisa ≤ derau pelatihan). Prediksi maju beku menjadi satu-satunya bukti baru yang sah, dengan daya yang hanya cukup untuk mendeteksi kegagalan besar.
- Jalur jangka panjang roadmap (cuaca sentra produksi, pasokan fisik) tidak berubah dan di luar jangkauan sebelum pembekuan.

## 6. Adendum audit (D-155, 2026-11-25)

Koreksi tafsiran atas audit Danen; bagian di atas tidak diubah.
- **Dua jenis kebocoran.** Audit §1 membuktikan tidak ada *look-ahead observasional* (fitur tidak membaca observasi sesudah cutoff, 84/84).
  *Kebocoran revisi/vintage* (nilai historis yang dipakai adalah nilai revisi yang baru tersedia sesudah waktu prediksi) tidak dapat diuji
  karena PIHPS tidak menyediakan vintage. Kalimat yang tepat: tidak ditemukan kebocoran akibat observasi masa depan pada fitur yang diuji;
  efek revisi data historis belum dapat diverifikasi.
- **`available_at` Sabtu 00.00 mungkin terlalu awal.** Bila harga Jumat masih dapat direvisi sepanjang Sabtu (H+1), batas aman adalah
  Minggu 00.00. Perubahan ini tidak mengubah nilai fitur (semua dari Senin–Jumat), hanya waktu prediksi yang dinyatakan, dan berlaku sama
  untuk C1-tuned. Jendela revisi PIHPS perlu dipastikan dari dokumentasi BI atau pengamatan stempel waktu (`[HUMAN]`).
- **Selisih C1-tuned vs IW_NAT** dirinci di adendum D-154 (`20261125_business_understanding.md` §6): IW_NAT membalik arah pada 12% / 7–8%
  baris; perbaikan dan perusakan hampir seimbang (test h 4 721 vs 629). Pada prediksi maju kesepakatan 95,3% (batch berbeda, origin
  terbaru).
