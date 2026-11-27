# Validasi K4 — Kepekaan definisi target

Tanggal 2026-11-27, catatan bertanggal. Skrip `scripts/v_sensitivity.py`, keluaran `hasil/sens_*.csv` (dev). Kolom test dikutip dari
`../20261126_k4_risiko_material/hasil/k4_test_paired.csv` (sudah terbit). Deskriptif: **tidak ada target yang dipilih atau diadopsi.**

STATUS: **COMPLETE** (deskriptif)

OBJECTIVE: Memeriksa apakah keunggulan ranking K4 bertahan bila definisi "kenaikan material" berubah, dan apa yang terjadi bila TPID memakai
ambang yang bukan statistik.

## 1. Tiga jenis materialitas

| Jenis | Definisi | Status di KAGAMI |
|---|---|---|
| **Statistik** | Kenaikan yang tidak biasa bagi komoditas itu: y_h ≥ persentil P \|y_h\| riwayat komoditas (walk-forward) | Dipakai semua angka K4 (P80); P70 / P90 / P90 bertanda = kepekaan |
| **Ekonomi** | Kenaikan yang berarti bagi rumah tangga atau inflasi: rupiah per kg, bobot dalam IHK, persen seragam | Tidak dipakai; §3 hanya ilustrasi seragam 5% / 10% dan ambang P80 dalam rupiah |
| **Kebijakan** | Ambang yang memicu tindakan TPID (persen, rupiah, atau jarak ke HET/HAP) | **Belum ada** (U109 V1, V8); tidak dikarang |

Ambang P80 dalam rupiah per kg (median origin dev, `sens_composition.csv`). Di h 4: beras Rp151 (1,2%), gula Rp453 (3,2%), minyak goreng Rp521
(2,4%), daging sapi Rp2.073 (1,6%), telur Rp2.607 (9,3%), bawang putih Rp4.522 (13,8%), daging ayam Rp4.832 (13,4%), bawang merah Rp7.892 (22,8%),
cabai merah Rp16.600 (37,2%), cabai rawit Rp28.883 (49,3%). Untuk beras, ambang statistik setara ± 3 tick PIHPS. Untuk cabai rawit setara
kenaikan Rp29 ribu per kg. Rentang ini menunjukkan mengapa ambang statistik dan ekonomi bisa sangat berbeda.

## 2. Target statistik alternatif (dev; Δ = K4 yang dilatih pada target itu − pembanding, interval 95% bootstrap blok origin)

| Target | Laju h 4 / h 8 | Porsi positif komoditas diatur | Positif minimum per komoditas | AP K4-own h 4 / h 8 | ΔAP vs C1t h 4 / h 8 | ΔAP vs laju-dasar h 4 / h 8 | ΔAP K4-own − K4-E80 h 4 / h 8 |
|---|---|---|---|---|---|---|---|
| P70 \|y\| | 0,171 / 0,183 | 0,56 / 0,59 | 111 / 101 | 0,393 / 0,361 | **+0,086** / **+0,040** | **+0,163** / **+0,123** | +0,001 / −0,001 |
| **P80 \|y\|** (utama) | 0,120 / 0,132 | 0,60 / 0,64 | 34 / 30 | 0,326 / 0,290 | **+0,080** / +0,039 (−0,008..0,101) | **+0,142** / +0,081 (−0,053..0,183) | – |
| P90 \|y\| | 0,066 / 0,078 | 0,65 / 0,67 | **5 / 1** | 0,236 / 0,213 | **+0,075** / **+0,049** | +0,092 (−0,010..0,139) / +0,014 (−0,155..0,128) | +0,005 / +0,020 |
| P90 y bertanda | 0,110 / 0,119 | 0,58 / 0,61 | 43 / 37 | 0,292 / 0,261 | **+0,059** / +0,026 (−0,022..0,097) | **+0,145** / **+0,091** | −0,012 / +0,001 |
| Kejadian dalam jendela (P80) | 0,137 / 0,168 | 0,58 / 0,58 | 56 / 44 | 0,353 / 0,359 | **+0,094** / **+0,073** | **+0,185** / **+0,156** | +0,002 / +0,018 |

Test (terbit D-164) untuk ΔAP K4-own − C1t h 4 / h 8: P70 +0,028 / +0,002, P80 **+0,045** / +0,015, P90 **+0,065** / +0,017, P90 bertanda
**+0,052** / +0,025, kejadian **+0,078** / **+0,079**. Kejadian vs K4-E80 di test: +0,018 / **+0,054** (0,017..0,077).

- **Di antara target statistik, keunggulan K4 atas C1-tuned bertahan pada setiap ambang di h 4** (dev dan test). Di h 8 searah, terbukti di dev
  untuk P70, P90, dan kejadian.
- **Satu model P80 cukup untuk seluruh keluarga target statistik**: K4 yang dilatih khusus pada P70 / P90 / bertanda mengurutkan targetnya sendiri
  sama baiknya dengan K4-E80 (selisih −0,012..+0,020, semua interval memuat 0 di dev). Mengganti ambang P antara 70 dan 90 tidak butuh model baru.
- **P90 tidak stabil**: bawang putih punya 1–5 positif di seluruh dev, dan keunggulan atas laju-dasar hilang (interval lebar). P90 tidak layak
  dipakai tanpa data lebih panjang.
- Komposisi positif tetap didominasi komoditas diatur (56–67%) untuk setiap target statistik, termasuk bertanda. Ini sifat persentil per komoditas
  pada komoditas yang hampir tidak pernah turun.
- Target kejadian memberi AP tertinggi dan selisih terbesar terhadap C1-tuned. Di test h 8 model khusus kejadian juga lebih baik dari K4-E80. Bila
  TPID bereaksi pada kenaikan kapan pun dalam jendela (V3), target ini lebih relevan. Keputusannya tetap menunggu jawaban pengguna.

## 3. Target ilustratif bukan statistik (seragam ≥ 5% / ≥ 10%; **tidak ada model khusus**, skor yang ada dibaca ulang)

| Target (dev) | Laju h 4 / h 8 | Porsi positif komoditas diatur | AP K4-E80 / C1t / laju-dasar h 4 | AP K4-E80 / C1t / laju-dasar h 8 | ΔAP K4-E80 − C1t h 4 / h 8 |
|---|---|---|---|---|---|
| Seragam ≥ 5% | 0,199 / 0,260 | **0,13 / 0,19** | 0,302 / **0,331** / 0,161 | 0,384 / **0,463** / 0,219 | −0,029 (−0,049..0,000) / **−0,079 (−0,117..−0,032)** |
| Seragam ≥ 10% | 0,121 / 0,168 | **0,06 / 0,12** | 0,173 / **0,191** / 0,093 | 0,243 / **0,335** / 0,139 | −0,017 (−0,041..0,016) / **−0,092 (−0,135..−0,040)** |

- **Keunggulan K4-E80 bergantung pada definisi target.** Dengan ambang seragam, komposisi positif berbalik ke hortikultura (81–94% positif bukan
  komoditas diatur). Skor K4-E80 lalu kalah dari skor arah C1-tuned, terbukti di h 8. Penyebabnya, K4-E80 belajar bahwa kenaikan 1–3% beras atau
  minyak goreng adalah "material".
- Implikasinya: bila TPID memilih ambang ekonomi atau kebijakan yang seragam, **K4-E80 tidak dapat dipakai ulang**. Dibutuhkan model yang dilatih pada
  target kebijakan itu, dengan protokol dan validasi baru.

FINDINGS:
- Ranking K4 kokoh di seluruh keluarga target statistik (P70–P90, bertanda, kejadian). Model P80 tunggal cukup untuk semuanya.
- Ranking K4 **tidak** kokoh terhadap ambang seragam bukan-statistik. Di sana skor arah C1-tuned lebih baik.
- P80 hanya proxy. Nilainya bagi TPID bergantung pada V1, V3, V8.

EVIDENCE: `hasil/sens_targets.csv`, `sens_paired.csv`, `sens_composition.csv`; D-164 `k4_paired.csv`, `k4_test_paired.csv`.

STATISTICAL VALIDITY: Interval bootstrap blok origin (1.999 replikasi). Target ilustratif dievaluasi tanpa model khusus, jadi selisihnya
adalah "seberapa baik skor yang ada untuk target lain", bukan batas atas yang dapat dicapai. Tidak ada koreksi multiplisitas: tabel ini deskriptif.

BUSINESS IMPLICATION: Keputusan TPID tentang materialitas mengubah model yang tepat. Untuk ambang relatif per komoditas, K4-E80 sudah cocok. Untuk
ambang seragam (persen atau rupiah) diperlukan model baru. Untuk kenaikan kapan pun dalam jendela, K4-A80 lebih tepat.

DECISION: **Pertahankan** P80 titik akhir sebagai proxy eksploratif. **Tidak mengadopsi** target alternatif sebelum V1/V3/V8 dijawab.

BLOCKERS: U109 (V1 ambang kebijakan, V3 titik akhir vs jendela, V8 relevansi kenaikan kecil komoditas diatur).

NEXT ACTION: Pemetaan jawaban ke model ada di [BUSINESS_REQUIREMENTS_VALIDATION.md](BUSINESS_REQUIREMENTS_VALIDATION.md) §5.
