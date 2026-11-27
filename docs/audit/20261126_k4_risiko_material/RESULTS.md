# K4 — Prediksi Risiko Kenaikan Harga Material: Laporan Hasil (EKSPLORATIF, D-164)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Catatan bertanggal (bukan dokumen hidup). Jalur terpisah dari optimasi macro F1
(D-156, D-165): **tidak ada angka di sini yang berarti macro F1 resmi berubah**. Protokol beku sebelum model dilatih:
[PROTOCOL.md](PROTOCOL.md) (sha256 `7625c391…`, 18.36 WIB, `hasil/protocol_sha256.txt`). Dokumen pendukung: [INITIAL_AUDIT](INITIAL_AUDIT.md) ·
[BUSINESS_REQUIREMENTS](BUSINESS_REQUIREMENTS.md) · [TARGET_DEFINITION](TARGET_DEFINITION.md) · [DATA_UNDERSTANDING](DATA_UNDERSTANDING.md) ·
[CALIBRATION_REPORT](CALIBRATION_REPORT.md) · [OPERATIONAL_ANALYSIS](OPERATIONAL_ANALYSIS.md) · [RECOMMENDATIONS](RECOMMENDATIONS.md) ·
[EXPERIMENT_LOG.csv](EXPERIMENT_LOG.csv) · skrip [`scripts/`](scripts/RUN.md) · hasil `hasil/`.

## Executive Summary

**Pertanyaan.** Seberapa besar kemungkinan suatu komoditas di suatu provinsi naik secara material dalam 4–8 minggu? C1-tuned menjawab
P(naik | harga berubah), bukan P(kenaikan material). K4 melatih klasifier yang sama (kolom & hyperparameter C1-tuned beku) langsung pada target
z = 1[y_h ≥ P80 |y_h| komoditas], memakai semua baris termasuk harga tetap.

**Hasil (rolling-origin pseudo-real-time; seleksi di dev ≤ 2023, test 2024+ dibuka sekali):**

| | h 4 dev | h 4 test | h 8 dev | h 8 test |
|---|---|---|---|---|
| Laju-dasar kenaikan material | 0,120 | 0,088 | 0,132 | 0,089 |
| AP (PR-AUC) K4 / C1-tuned / laju-dasar komoditas | **0,326** / 0,246 / 0,184 | **0,237** / 0,192 / 0,106 | **0,290** / 0,250 / 0,208 | **0,206** / 0,191 / 0,122 |
| ΔAP K4 − C1-tuned (interval 95%) | **+0,080 (0,046..0,103)** | **+0,045 (0,017..0,083)** | +0,039 (−0,008..0,101) | +0,015 (−0,028..0,064) |
| Presisi daftar pantau 2/provinsi K4 / C1-tuned | **0,293** / 0,249 | **0,202** / 0,179 | **0,272** / 0,221 | **0,174** / 0,161 |
| Kenaikan material tertangkap (recall K = 2) K4 / C1-tuned | 0,49 / 0,42 | 0,46 / 0,41 | 0,41 / 0,34 | 0,39 / 0,36 |
| Brier K4 − C1-tuned terkalibrasi (interval) | **−0,0063 (−0,0091..−0,0030)** | **−0,0024 (−0,0045..−0,0005)** | −0,0033 (−0,0124..+0,0060) | −0,0002 (−0,0040..+0,0025) |
| ECE K4 | 0,023 | 0,019 | 0,044 | 0,024 |

- **Ranking: lebih baik.** K4 mengurutkan risiko kenaikan material lebih baik daripada skor arah C1-tuned, laju-dasar komoditas, dan empat aturan
  naif, terbukti di h 4 (dev & test) dan searah tetapi tidak terbukti di h 8.
- **Peluang: hanya h 4.** Peluang K4 h 4 terkalibrasi (ECE ≤ 0,023) dan lebih baik dari skor arah yang dikalibrasi. Di h 8 keunggulannya tidak
  terbukti dan peluang > 0,7 terlalu yakin.
- **Keputusan teknis: PARTIAL** (R1 & R1b lolos, R2 gagal di h 8). **Status operasional: BLOCKED** sampai ambang kebijakan, kapasitas pemantauan,
  dan titik akhir vs kejadian divalidasi TPID (U109). Prediksi maju beku untuk konfirmasi prospektif.
- Temuan samping yang mengoreksi D-154: daftar pantau C1-tuned tidak pernah dibandingkan dengan **laju-dasar komoditas**. Di h 8 keunggulannya
  atas laju-dasar tidak terbukti (dev −0,026, test +0,019, interval memuat 0); di h 4 test +0,082 (0,050..0,120).
- Bagi pengguna: daftar pantau K4 menangkap ± 3 (dev) / ± 1–1,5 (test) kenaikan material lebih banyak per minggu (34 provinsi, 68 alarm) daripada
  C1-tuned dengan alarm sama, tetapi 7–8 dari 10 alarm tetap tidak berujung kenaikan material. Analisis biaya menunjukkan daftar pantau apa pun hanya bernilai bila
  kenaikan yang terlewat ≥ ± 3–5× lebih mahal daripada alarm palsu.

## 1. Business Understanding

Pengguna & keputusan: TPID menyiapkan instrumen 4–8 minggu sebelum kenaikan material ([BUSINESS_REQUIREMENTS.md](BUSINESS_REQUIREMENTS.md)).
Dari 8 pertanyaan kebutuhan, **tidak ada yang sudah dijawab pengguna**. Asumsi kerja: kenaikan (bukan dua arah), materialitas statistik relatif
per komoditas, persen, titik akhir (kejadian kapan pun dievaluasi terpisah), K tidak dipilih, rasio biaya sebagai skenario. Apakah definisi
"kenaikan material" sesuai kebutuhan TPID **belum dapat dinyatakan**: DU menunjukkan definisi statistik ini membuat 60% kenaikan material berupa
kenaikan 1–4% pada komoditas diatur, yang belum tentu relevan secara kebijakan (V8).

## 2. Data Understanding ([DATA_UNDERSTANDING.md](DATA_UNDERSTANDING.md))

- Universe dev 12.800 / 12.463 baris (= 25.259 baris resmi + 4 tanpa target), test 12.477 / 12.139; tidak ada baris yang dibuang.
- Laju z dev 0,120 / 0,132, test 0,088 / 0,089; antarkomoditas 0,02 (bawang putih) .. 0,29 (minyak goreng); antarprovinsi sd 0,015; antarminggu
  sd 0,07–0,08; musim Jun–Agu 0,05–0,09 vs Nov–Apr 0,15–0,19; komoditas diatur naik sejak 2021, tidak diatur turun.
- Label kokoh: tidak ada positif < 2 tick; 7% / 4% positif dalam 1 tick dari ambang (beras 22%); 12% / 21% kejadian kapan pun adalah lonjakan yang
  berbalik.
- Ambang walk-forward bergeser (bawang putih 19,8% → 11,9%; minyak goreng 1,3% → 2,6% pada h 4 sepanjang dev).

## 3. Target Definition ([TARGET_DEFINITION.md](TARGET_DEFINITION.md))

| | Materialitas statistik (dipakai) | Materialitas kebijakan |
|---|---|---|
| Definisi | y_h ≥ P80 \|y_h\| baris latih komoditas pada origin | ambang yang memicu tindakan TPID |
| Status | proxy eksploratif; P70/P90 & P90 bertanda sebagai kepekaan | **belum ada** (V1, U109); tidak dikarang |
| Akibat | 60% / 64% positif = komoditas diatur (ambang 1,2–3,9%) | ambang seragam 5% (ilustratif) → 13% / 19% |

Target utama = titik akhir (y_{t+h} − y_t); target kejadian = max_{k≤h} kenaikan ≥ ambang yang sama (Fase E, terpisah).

## 4. Modeling

| ID | Peran | Model | Label / skor |
|---|---|---|---|
| **K4-E80** | kandidat | HGB `TUNED_HGB`, kolom `tuned_columns("C1t", h)`, seed 20261121, semua baris latih | z (P80 \|y\|) |
| K4-E80-cal | varian peluang | K4-E80 + Platt global walk-forward | – |
| K4-A80 | target alternatif | sama | z_any (kejadian) |
| K4-E70 / E90 / S90 | kepekaan | sama | P70 / P90 \|y\| / P90 y bertanda |
| B-C1t, B-C1t-cal | pembanding | p_up C1-tuned (refit = artefak resmi, maks \|Δp\| 0), ± Platt walk-forward → z | – |
| B-CLIM, B-CLIMS | pembanding | laju z komoditas (× bulan) di baris latih | – |
| R_mom, R_nat, R_rev, R_seas | pembanding | aturan naif D-154 | – |

Alasan: kolom & hyperparameter C1-tuned sudah dipilih di dev dan HGB setara boosting lain (D-156); satu-satunya perubahan adalah **label** dan
**baris latih** (y = 0 ikut), sehingga selisih terhadap C1-tuned dapat dibaca sebagai efek "melatih pada target bisnis". Tidak ada tuning ulang,
fitur baru, atau ensemble (protokol).

## 5. Evaluation

### 5.1 Ranking (`hasil/k4_ranking.csv`, `k4_paired.csv`; test `k4_test_*`)

| Skor | AP dev h 4 / h 8 | AP test h 4 / h 8 | ROC-AUC dev h 4 / h 8 | Presisi@K1 / K2 / K3 dev h 4 | Presisi@K2 test h 4 / h 8 |
|---|---|---|---|---|---|
| **K4-E80** | **0,326 / 0,290** | **0,237 / 0,206** | **0,775 / 0,743** | **0,334 / 0,293 / 0,249** | **0,202 / 0,174** |
| B-C1t | 0,246 / 0,250 | 0,192 / 0,191 | 0,711 / 0,696 | 0,266 / 0,249 / 0,222 | 0,179 / 0,161 |
| B-CLIM | 0,184 / 0,208 | 0,106 / 0,122 | 0,606 / 0,615 | 0,227 / 0,190 / 0,187 | 0,097 / 0,143 |
| B-CLIMS | 0,123 / 0,150 | 0,109 / 0,112 | 0,538 / 0,571 | 0,098 / 0,101 / 0,120 | 0,104 / 0,093 |
| R_nat (terbaik naif tren dev) | 0,153 / 0,157 | 0,091 / 0,082 | 0,603 / 0,582 | 0,125 / 0,136 / 0,158 | 0,091 / 0,090 |
| R_rev | 0,109 / 0,128 | 0,123 / 0,121 | 0,445 / 0,481 | 0,119 / 0,111 / 0,104 | 0,113 / 0,121 |

| Perbandingan berpasangan (interval 95%, bootstrap blok origin) | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| ΔAP K4 − C1t | **+0,080 (0,046..0,103)** q 0,002 | +0,039 (−0,008..0,101) q 0,119 | **+0,045 (0,017..0,083)** q 0,048 | +0,015 (−0,028..0,064) |
| ΔAP rerata per origin K4 − C1t | **+0,070 (0,033..0,101)** | **+0,061 (0,012..0,123)** | **+0,040 (0,015..0,080)** | +0,029 (−0,009..0,064) |
| ΔPresisi@K2 K4 − C1t | **+0,044 (0,019..0,067)** q 0,002 | +0,050 (−0,005..0,112) q 0,111 | **+0,023 (0,003..0,047)** q 0,048 | +0,012 (−0,009..0,042) |
| ΔPresisi@K3 K4 − C1t | **+0,027 (0,012..0,044)** | **+0,036 (0,008..0,069)** | **+0,018 (0,009..0,031)** | **+0,019 (0,004..0,037)** |
| ΔAP K4 − B-CLIM (naif terbaik dev) | **+0,142 (0,054..0,203)** | +0,081 (−0,053..0,183) | **+0,131 (0,093..0,177)** | **+0,084 (0,027..0,177)** |
| ΔPresisi@K2 K4 − B-CLIM | **+0,103 (0,035..0,162)** | +0,024 (−0,069..0,099) | **+0,105 (0,070..0,149)** | +0,031 (−0,005..0,093) |
| ΔPresisi@K2 C1t − B-CLIM | +0,058 (−0,014..0,123) | **−0,026** (−0,105..0,031) | **+0,082 (0,050..0,120)** | +0,019 (−0,027..0,081) |

Stabilitas ΔAP K4 − C1t per tahun: dev 2021 / 2022 / 2023 h 4 +0,092 / +0,062 / +0,090, h 8 +0,087 / +0,038 / −0,022; test 2024 / 2025 / 2026 h 4
−0,011 / +0,051 / +0,096, h 8 +0,014 / +0,028 / +0,009. Antarprovinsi K4 ≥ C1t (presisi@K2) di 29 / 34 (h 4) dan 32 / 34 (h 8) provinsi dev; antarorigin di
79% / 73% origin dev.

### 5.2 Peluang ([CALIBRATION_REPORT.md](CALIBRATION_REPORT.md))

| Himpunan peluang | Brier K4 / K4-cal / C1t-cal / CLIM | ECE K4 / K4-cal / C1t-cal | Brier skill K4 vs CLIM (interval) |
|---|---|---|---|
| dev h 4 (32 origin) | **0,0979** / 0,0985 / 0,1042 / 0,1108 | 0,023 / **0,014** / 0,014 | **0,116 (0,052..0,170)** |
| dev h 8 (30 origin) | **0,1132** / 0,1136 / 0,1165 / 0,1214 | 0,044 / 0,019 / **0,010** | 0,068 (−0,031..0,153) |
| test h 4 (37 origin) | 0,0750 / **0,0749** / 0,0774 / 0,0811 | **0,019** / 0,020 / 0,030 | **0,075 (0,039..0,107)** |
| test h 8 (36 origin) | 0,0795 / **0,0778** / 0,0797 / 0,0818 | **0,024** / 0,030 / 0,039 | 0,029 (−0,053..0,107) |

Di test, rerata peluang K4 0,107 / 0,113 vs laju 0,088 / 0,089: model membawa laju latih dev yang lebih tinggi (pergeseran rezim D-154). Skor arah
yang dikalibrasi hampir tidak pernah memberi peluang > 0,4: ia tidak dapat menyatakan risiko tinggi.

### 5.3 Volume alarm & per seri ([OPERATIONAL_ANALYSIS.md](OPERATIONAL_ANALYSIS.md))

K = 2 per provinsi = 68 alarm/minggu; benar 19,9 / 18,5 (dev), 13,7 / 11,8 (test) untuk K4 vs 16,9 / 15,1 dan 12,2 / 11,0 untuk C1-tuned. Kebijakan
ambang peluang τ = 0,3 (h 4 dev): 30 alarm/minggu rata-rata (sd 29), presisi 0,41, 16 provinsi tanpa alarm per minggu. Per komoditas, K4 lebih baik
untuk ayam, daging sapi, beras (test), telur (dev h 4); C1-tuned lebih baik untuk cabai merah h 8, cabai rawit (test), dan gula h 8. Bawang putih tidak
dapat diurutkan oleh skor mana pun (AP ≈ laju 0,03).

### 5.4 Target kejadian kapan pun (Fase E)

| z_any (laju dev 0,137 / 0,168; test 0,102 / 0,124) | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| AP K4-A80 / K4-E80 / C1t | 0,353 / 0,350 / 0,259 | 0,359 / 0,341 / 0,286 | 0,287 / 0,268 / 0,209 | 0,314 / 0,261 / 0,236 |
| ΔAP K4-A80 − K4-E80 | +0,002 (−0,019..0,025) | +0,018 (−0,012..0,049) | +0,018 (−0,015..0,051) | **+0,054 (0,017..0,077)** |
| ΔBrier K4-A80 − C1t-cal-any | **−0,0074 (−0,0106..−0,0036)** | −0,0083 (−0,0188..0,0006) | **−0,0044** | **−0,0060** |

Model kejadian khusus tidak memperbaiki ranking di dev (seleksi); di test h 8 ia lebih baik (+0,054), tetapi angka itu tidak dipakai memilih.
Target kejadian relevan bila TPID bereaksi pada lonjakan sementara (V3); keputusan tidak diambil tanpa jawaban pengguna.

### 5.5 Kepekaan definisi target (deskriptif, bukan seleksi)

| ΔAP K4 − C1t pada targetnya sendiri | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| P70 \|y\| (laju 0,17 / 0,18) | **+0,086** | **+0,040** | +0,028 (−0,004..0,062) | +0,002 |
| P90 \|y\| (laju 0,07 / 0,08) | **+0,075** | **+0,049** | **+0,065** | +0,017 |
| **P90 y bertanda** (komposisi seimbang, laju ± 0,10 / 0,07) | **+0,059 (0,029..0,080)** | +0,026 (−0,022..0,097) | **+0,052 (0,021..0,086)** | +0,025 (−0,008..0,061) |

Keunggulan ranking K4 **tidak hanya berasal dari komoditas diatur**: pada target dengan komposisi seimbang (K4-S90) pola h 4 sama (terbukti di dev &
test), h 8 searah tetapi tidak terbukti.

## 6. Error Analysis (K = 2; dev, test serupa)

- **Alarm palsu**: ± 50–58% kenaikan nyata di bawah ambang, 29–37% penurunan, 10–19% harga tetap; 19–21% "nyaris" (≥ ½ ambang). K4 memusatkan alarm
  pada komoditas diatur (51% alarm palsu dev h 4 vs 39% C1t).
- **Risiko terlewat**: 13–17% muncul dari harga datar 4 minggu sebelumnya (lonjakan tanpa tanda), ± 35% berada di peringkat ≥ 6 dari 10 di provinsinya
  (tak tertangkap K kecil apa pun).
- **Waktu menentukan presisi**: origin berlaju rendah (± 3–5%) presisi 0,04–0,12 untuk semua skor, laju tinggi 0,27–0,45. Rerata peluang K4 hanya bergerak
  0,08 → 0,13; model tidak tahu sebelumnya minggu mana yang berisiko secara nasional (bottleneck 2 D-156).
- **Ekor atas h 8 terlalu yakin**: p 0,8–0,9 → 28% naik material (dev).
- K4 dan C1t berbagi ± 45% alarm (Jaccard 0,39–0,46); K4 menangkap 254 / 306 kenaikan yang dilewatkan C1t, sebaliknya 140 / 180 (dev).

## 7. Business Utility

Skenario biaya (satuan = satu alarm palsu; r = biaya kenaikan terlewat; bukan biaya nyata):
- r = 1–2: **tidak memantau lebih murah** daripada daftar pantau apa pun (presisi < 0,5). Ini batas penting: daftar pantau bukan pemicu tindakan.
- r = 5: K4 termurah (dev h 4 150 vs C1t 168 vs tanpa alarm 202; test h 4 132 vs 141 vs 149). r = 10: K4 K = 3 termurah (dev 227 vs 257; test 202 vs 222).
- Kurva keputusan: net benefit K4 > C1t terkalibrasi > laju-dasar > "pantau semua" pada τ 0,10–0,40 (dev). Bila TPID memakai peluang, τ = 1/(1+r).
- Implikasi: K4 menaikkan nilai daftar pantau **bila** risiko terlewat jauh lebih mahal daripada pemantauan tambahan, dan paling berguna pada h 4.
  Pilihan K/τ menunggu V4–V5.

## 8. Limitations

- **Materialitas statistik, bukan kebijakan**; 60% positif adalah kenaikan kecil komoditas diatur. Hasil dapat berubah total dengan ambang TPID.
- **Test 2024+ bukan independen** (dipakai D-145–D-155); ditulis "evaluasi eksploratif dengan kriteria yang ditetapkan sebelumnya". Bukti independen
  hanya dari prediksi maju beku (`hasil/k4_forward_preds.csv`, 4.056 baris, sha256 `eb1f10db…`, target lengkap 2027-01-15).
- Pseudo-real-time: vintage revisi PIHPS tidak tersedia (U110); `available_at` konservatif Minggu 00.00.
- Hyperparameter tidak dituning untuk z (dipinjam dari C1-tuned); himpunan peluang mengecualikan 6–7 origin awal dev.
- Laju-dasar bergeser (dev 0,12–0,13 → test 0,09): peluang mentah terlalu tinggi di test (0,107 vs 0,088), kalibrasi walk-forward global tidak
  menangkap pergeseran per origin.
- Hanya 10 komoditas, 34 provinsi; bawang putih (± 1 positif per seri) tidak dapat dinilai bermakna. Hasil asosiasional; bukan ramalan.

## 9. Final Decision

**PARTIAL** (teknis, dev; konsisten di test) — **BLOCKED** untuk penggunaan operasional.
- Diterima secara eksploratif: K4-E80 sebagai **skor ranking risiko kenaikan material statistik** (R1, R1b lolos; test searah, h 4 terbukti).
- Ditolak: peluang K4 h 8 sebagai angka (R2 gagal; ekor atas terlalu yakin). Peluang h 4 memenuhi syarat R2 per horizon tetapi aturan R2 butuh
  kedua horizon.
- Tidak berubah: C1-tuned, label arah, macro F1 resmi (0,677 / 0,680), H5. K4 tidak masuk `src/` sebelum U109 dan validasi prospektif.

## 10. Next Actions (rincian [RECOMMENDATIONS.md](RECOMMENDATIONS.md))

1. `[HUMAN]` Validasi TPID (U109; V1–V8): ambang kebijakan, K, rasio biaya, titik akhir vs kejadian.
2. Koreksi klaim daftar pantau D-154 dengan pembanding laju-dasar komoditas (findings & makalah) — dilakukan di sesi ini.
3. Nilai prediksi maju beku saat target lengkap (h 4 2026-12-18; h 8 2027-01-15).
4. Bila dipakai: daftar pantau diurutkan K4-E80; peluang hanya h 4; label eksploratif.
5. Kartu C3 hanya sesudah (1): kalibrasi ekor h 8, target kebijakan, target kejadian.

## 11. Integritas, kebocoran, reproduksi

| Kontrol | Hasil |
|---|---|
| C1-tuned refit = artefak resmi | dev 25.259 & test 24.616 baris bertarget, maks \|Δp\| 0,0 |
| Universe dev | 12.800 / 12.463 (= D-155) |
| Perturbasi data sesudah origin (6 origin × h; y_h, harga, M_h) | 0 perbedaan ambang, laju-dasar, prediksi (`hasil/leak_checks.csv`) |
| Uji mandiri (`scripts/k4_selftest.py`) | 6/6 lolos (AP/AUC = sklearn, ambang tanpa masa depan, target kejadian, Platt walk-forward, flag K) |
| Test | dibuka sekali sesudah keputusan dev PARTIAL (`hasil/k4_test_allowed.flag`); tidak memilih apa pun |
| Multiplisitas | BH pada keluarga F (ΔAP, ΔPresisi@K2, ΔBrier × 2 horizon) |

Pengungkapan: (a) `k4_eval.py`, `k4_leak.py`, `k4_log.py`, `k4_freeze.py`, `k4_selftest.py` ditulis sesudah pembekuan sebagai implementasi §3–§6;
(b) uji mandiri menemukan bug `fast_ap` (skor NaN → −inf memecah kelompok kembar; memengaruhi aturan naif ber-NaN) dan diperbaiki **sebelum** hasil
evaluasi pertama dibaca; (c) evaluasi dev dijalankan ulang hanya untuk menghapus baris duplikat tabel operasional (keputusan identik); (d) ukuran
ranking pooled varian `-cal` di EXPERIMENT_LOG memasukkan 6–7 origin awal tanpa kalibrator (NaN = peringkat terbawah), jadi bukan pembanding ranking
(Platt monoton tidak mengubah urutan dalam origin); (e) sesi
terhenti 19.00–22.10, dan commit `ec6dd19` (oleh user) memuat versi awal folder ini sebelum hasil ada. Runtime: dev 21 menit, test 40 menit,
maju 20 menit (5 / 2 proses), evaluasi ± 9 menit per bagian. Reproduksi: [scripts/RUN.md](scripts/RUN.md).
