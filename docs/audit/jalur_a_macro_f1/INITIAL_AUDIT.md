# Jalur A — Audit Awal: Macro F1 Task 4 Arah & Intelijen Eksternal

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-165 · Catatan bertanggal. Folder ini memuat seluruh pekerjaan Jalur A;
hasil audit sebelumnya (D-145–D-163a) tidak ditimpa.

## 1. Kondisi repositori saat audit dimulai (2026-11-26 18.19 WIB)

- Branch `dev`, commit terakhir `ca53742` (2026-11-25 21.41 WIB). Pohon kerja memuat perubahan belum di-commit dari sesi lain:
  D-162 (flag `episode` real-time, `src/data/drivers.py`, `src/features/forecast.py`), D-163 (inferensi provinsi terkalibrasi plasebo,
  `src/evaluation/calibration.py`), D-163a (kalibrasi daftar pantau, `docs/audit/20261126_kalibrasi_pantau/`).
- **Tiga sesi agent berjalan bersamaan di folder yang sama**: sesi ini (Jalur A), sesi kalibrasi/rerun task3–task4 (D-162/D-163),
  dan sesi K4 risiko kenaikan material (D-164, `docs/audit/20261126_k4_risiko_material/`). Akibatnya: (a) sesi ini tidak menyentuh
  `src/`, `tests/`, artefak resmi, atau konfigurasi; (b) artefak Task 4 hanya dibaca dan dicek silang; (c) nomor keputusan dikoordinasikan
  (D-164 = K4, **D-165 = Jalur A**); (d) dokumen bersama diedit di akhir dengan Edit tepat-string.
- Tabel kerja D-156–D-158 (`base.parquet`, `c1t_weekly.parquet`, `fresh.parquet`) tersedia di folder `KAGAMI_EXP` sesi D-156
  (scratchpad lokal); dipakai baca-saja.

## 2. Baseline yang diverifikasi ulang

| Komponen | Nilai | Bukti |
|---|---|---|
| C1-tuned (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed 20261121, threshold 0,5) | dev macro F1 **0,656 / 0,676** | dihitung ulang dari artefak `direction_tuned_preds` C1t: 10.966 / 11.307 baris y ≠ 0, 38 / 37 origin (sama dengan D-156) |
| Test 2024+ | 0,677 / 0,680 (D-145) | tidak dibaca ulang (test tidak dibuka di Jalur A) |
| Artefak `direction_tuned_preds` | 50.886 baris C1t + 50.886 C2t | perubahan `episode` D-162 tidak menyentuh C1t (grup `fx` tidak dipakai C1t) |
| Definisi label (D-139/D-141) | tanda log p_{t+h} − log p_t, y = 0 dikeluarkan | `fw_eval.py --selftest` D-152 dijalankan ulang: 156.400 / 155.040 baris cocok, 0 beda |

## 3. Pekerjaan terbuka yang relevan (dari D-147–D-163a)

| Item | Status sebelum Jalur A | Jalur A |
|---|---|---|
| Prediksi maju beku D-152 (C1t, IW_NAT) | di-commit `ca53742`; target belum terealisasi | Workstream A: audit + evaluator beku |
| Prediksi maju beku D-158 (C1t, FR_REF, FR_CITY) | **belum di-commit** saat audit awal (di-commit Danen `ec6dd19`, 2026-11-26 20.45 WIB) | Workstream A: audit |
| GDELT (U113) | BLOCKED (skala TB / BigQuery berbayar), cakupan berita Indonesia belum diuji | Workstream B |
| Pasokan fisik (U112: SP2KP, PIBC, FDP, GPM) | BLOCKED / REJECTED (D-159) | Workstream C: audit ulang + kandidat baru |
| CFSv2, SIJAGUNG, SPORA, cuaca NASA POWER, impor BPS | REJECTED (D-157, D-160, D-161) | tidak diulang (tanpa mekanisme baru) |
| DIBI BNPB | BLOCKED sementara (HTTP 521, D-160) | Workstream C: dinilai ulang |

## 4. Diagnosis yang menjadi dasar (ringkasan D-156–D-158, tidak diulang)

1. Galat terbesar = **waktu** (sd antarorigin 0,08–0,09 vs antarprovinsi 0,02–0,03): pergeseran base rate per origin hanya terlihat sesudah
   target terealisasi (oracle threshold per origin +0,035 / +0,024).
2. Arah perubahan kecil hampir tak teramalkan dari histori harga (AUC kuintil |y| terkecil 0,60 / 0,56; ± ⅓ label rapuh).
3. **Konsensus C1t** (rerata p_up provinsi) adalah prediktor arah nasional terbaik dari informasi harga (AUC mingguan 0,762 / 0,755); headroom
   informasi nasional sempurna +0,105 macro F1 (D-157).
4. Satu-satunya informasi tambahan yang pernah membantu adalah **kesegaran intraminggu** (IW_NAT/FR_REF; test +0,0085 / +0,0033, belum terbukti).

## 5. Hipotesis Jalur A (ditetapkan sebelum data GDELT penuh)

- **HA1 (Workstream A).** Keuntungan IW_NAT/FR_REF di dev/test tidak berbalik menjadi kerugian besar pada origin yang belum pernah dipakai.
  Hanya dapat diuji sebagai penjaga (MDE batch maju 0,08–0,12 / 0,04–0,06, D-152).
- **HB1 (Workstream B).** Berita berbahasa Indonesia tentang gangguan pasokan, kebijakan dagang/harga, dan intervensi stabilisasi memuat
  informasi arah nasional per komoditas yang belum ada di konsensus C1t, karena sebagian peristiwa (larangan ekspor, kuota impor, gagal panen,
  distribusi MinyaKita/SPHP) diumumkan **sebelum** dampaknya pada harga eceran rata-rata provinsi.
  Risiko yang diketahui: sebagian besar berita pangan bereaksi terhadap harga (G3).
- **HC1 (Workstream C).** Ada sumber pasokan/kejadian bertanggal yang mekanismenya berbeda dari PIHPS dan cuaca (yang sudah tertutup, D-161):
  proyeksi neraca pangan resmi, data tanam (luas tanam) hortikultura, pengumuman kebijakan, kejadian bencana non-cuaca.

## 6. Urutan kerja

Workstream A → B → C → D (D hanya bila suatu sumber lolos kelima gerbang). Protokol: [PROTOCOL.md](PROTOCOL.md). Log: [EXPERIMENT_LOG.csv](EXPERIMENT_LOG.csv).
