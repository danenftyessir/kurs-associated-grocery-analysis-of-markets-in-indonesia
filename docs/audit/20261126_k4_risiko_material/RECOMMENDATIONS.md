# K4 — Rekomendasi (EKSPLORATIF, D-164)

Tanggal: 2026-11-26. Dasar: [RESULTS.md](RESULTS.md) (keputusan teknis **PARTIAL**: ranking lolos, peluang tidak; status operasional
**BLOCKED** sampai U109). Diurutkan menurut dampak × kelayakan. `[HUMAN]` = tugas manusia; agent hanya menyiapkan bahan.

| # | Tindakan | Dampak | Kelayakan | Siapa / kapan |
|---|---|---|---|---|
| 1 | **Validasi kebutuhan TPID** (U109): ambang kebijakan per komoditas (V1, V8), kapasitas K (V4), toleransi alarm palsu / rasio biaya (V5), titik akhir vs kejadian (V3), angka peluang vs urutan (V6). Panduan [`PANDUAN_WAWANCARA_TPID.md`](../../PANDUAN_WAWANCARA_TPID.md) D1–D6 | Sangat tinggi: definisi target menentukan komposisi positif (P80 \|y\| → 60% komoditas diatur; ambang seragam 5% → 13%); analisis biaya menunjukkan daftar pantau hanya bernilai bila kenaikan terlewat ≥ ± 3× lebih mahal dari alarm palsu | Sedang (3–5 wawancara) | `[HUMAN]` Danen/Abi, sebelum klaim produk |
| 2 | **Koreksi klaim daftar pantau C1-tuned** (`results/findings.md`, makalah): pembanding D-154 tidak memuat laju-dasar komoditas; di dev h 8 laju-dasar (presisi 0,248) di atas C1-tuned (0,221). Tambahkan B-CLIM ke setiap klaim daftar pantau | Tinggi (integritas klaim) | Tinggi (teks) | Sesi ini (findings) + makalah |
| 3 | **Validasi prospektif** prediksi maju beku `hasil/k4_forward_preds.csv` (sha256 di manifest; 12 origin 2026-09-28..11-16): nilai AP & presisi@K2 K4-E80 vs C1-tuned vs B-CLIM sesudah target lengkap (h 4: 2026-12-18; h 8: 2027-01-15) | Tinggi (satu-satunya bukti independen) | Tinggi (skrip `k4_eval.py` dengan PART baru) | Danen, Des 2026–Jan 2027 (di luar jadwal lomba) |
| 4 | Bila daftar pantau disajikan (app/makalah): **urutkan dengan K4-E80**, bukan p_up; peluang hanya untuk h 4 (terkalibrasi, ECE ≤ 0,023), h 8 sebagai urutan saja; label "risiko kenaikan material statistik, eksploratif, bukan ramalan" | Sedang | Sedang (perlu modul `src/` + artefak; belum boleh sebelum #1) | Sesudah #1 |
| 5 | Kartu lanjutan C3 (hanya bila #1 mengonfirmasi target): (a) kalibrasi ekor atas h 8 (p > 0,7 terlalu yakin) dengan kalibrator monoton per kelompok komoditas walk-forward; (b) target kebijakan bila ambang TPID berbeda; (c) target kejadian bila TPID bereaksi pada lonjakan sementara | Sedang | Sedang | Protokol baru, dev saja |
| 6 | Informasi ex-ante untuk pergeseran laju per origin (presisi 0,11 di minggu tenang vs 0,42–0,45 di minggu berisiko; model hanya sebagian mengetahuinya): pengumuman kebijakan bertanggal, pasokan mingguan (U112) | Tinggi bila ada data | Rendah (akses data `[HUMAN]`) | Mengikuti U112/U113 |
| 7 | Jangan menyetel ulang hyperparameter HGB untuk z atau menambah fitur histori harga tanpa hipotesis; D-156 menunjukkan batas informasi yang sama | – (pencegahan) | – | Aturan |

## Yang tidak direkomendasikan

- Mengganti klasifier arah resmi atau macro F1 dengan K4: target berbeda, ukuran berbeda (PROTOCOL; tidak ada klaim macro F1).
- Menampilkan p_up C1-tuned sebagai "peluang naik tajam" (Brier/ECE terhadap z jauh lebih buruk; D-155).
- Model terpisah untuk target kejadian hanya untuk ranking: K4-E80 mengurutkan kejadian sama baiknya dengan K4-A80 (Δ AP +0,002 / +0,018,
  interval memuat 0).
- Memilih K, τ, atau ambang dari test 2024+.
