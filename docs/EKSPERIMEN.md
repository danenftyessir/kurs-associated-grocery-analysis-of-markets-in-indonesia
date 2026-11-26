# Alur Eksperimen Task 4 (CRISP-DM) & Kartu Eksperimen

Dokumen hidup sejak D-153 (2026-11-25, keputusan Danen). Berlaku untuk setiap eksperimen **eksploratif** Task 4 (arah perubahan harga)
dan analisis serupa. Uji praregistrasi (H5, `forecast_eval`) tidak berubah dan tetap mengikuti `docs/PREREGISTRATION.md`.

Dasar: CRISP-DM (IF4041 Modul 01, hlm. 5) dan proses Knowledge Discovery (Modul 01, hlm. 6). CRISP-DM bersifat iteratif: bila evaluasi
atau pemahaman data menunjukkan masalah, kembali ke fase sebelumnya, bukan menambah model.

## 1. Fase dan wujudnya di proyek ini

| Fase | Pertanyaan | Wujud di KAGAMI |
|---|---|---|
| 1. Business Understanding | Keputusan apa yang dibantu? Apa ukuran berhasil? | Pengguna TPID (menyiapkan instrumen 4/8 minggu sebelum kenaikan material); macro F1 label resmi (perubahan kecil tetap dihitung) **plus** kriteria bisnis D-154: S1 daftar pantau provinsi (presisi kenaikan material vs aturan naif), S2 kalibrasi (Brier skill, ECE ≤ 0,05), S3 arah saat bergerak material; definisi di `docs/audit/20261125_business_understanding/PROTOKOL.md` |
| 2. Data Understanding | Karakteristik & pola apa yang ada di data? Adakah informasi yang belum dipakai model? | Layar DU (§3) di origin pengembangan; karakteristik seri dari data sebelum origin pertama |
| 3. Data Preparation | Pembersihan, integrasi, transformasi, konstruksi fitur, kontrol kebocoran | Preprocessing beku D-148; fitur baru hanya dari informasi ≤ `available_at` origin |
| 4. Exploratory Data Mining (operasional, bukan fase resmi CRISP-DM) | Pola apa yang bisa ditemukan? | Clustering, pattern mining, outlier/rezim, graf; hasilnya pengetahuan, belum tentu fitur |
| 5. Modeling | Apakah hipotesis menaikkan skor di atas pembanding? | Kandidat di atas C1-tuned beku; tanpa tuning ulang hyperparameter/threshold |
| 6. Evaluation | Bukan kebetulan? Bukan kebocoran? | Aturan §4; test dibuka sekali per kandidat |
| 7. Knowledge Presentation | Pola, visual, tafsiran, batasan, keputusan | Laporan bertanggal `docs/audit/`, D-xxx, `findings.md` bila relevan |
| 8. Deployment | Beku & dapat direproduksi | Protokol + sha256, prediksi maju beku (D-152), skrip di lampiran laporan |

## 2. Kartu eksperimen (wajib sebelum implementasi)

Setiap usulan ditulis sebagai kartu di laporan `docs/audit/` **sebelum** kode modeling ditulis. Data Understanding (§3) boleh dijalankan
untuk mengisi kartu.

| Komponen | Pertanyaan wajib |
|---|---|
| Problem | Masalah apa yang ingin diselesaikan? |
| Data characteristic | Karakteristik data apa yang mendasarinya (dengan angka dari DU)? |
| Knowledge discovery | Pola/pengetahuan apa yang ingin ditemukan? |
| Hypothesis | Mengapa metode ini berpotensi membantu? Apa yang belum ditangkap C1-tuned? |
| Method | Algoritma & pendekatan; mengapa cocok dengan karakteristik data |
| Validation | Bagaimana membuktikan bukan kebetulan (pembanding, interval, multiplisitas, stabilitas antarperiode)? |
| Leakage control | Informasi apa yang tersedia pada `available_at` origin; uji kebocoran apa yang dijalankan? |
| Decision | Kapan diterima/ditolak (ditulis sebelum hasil)? |

## 3. Layar Data Understanding (gerbang ke Modeling)

- Hanya origin pengembangan (target ≤ 2023-12-31) atau data sebelum origin pertama (≤ 2020-12-28). Test 2024+ tidak disentuh.
- Ukuran "informasi yang belum dipakai": korelasi residual pembanding (r = 1[y > 0] − p_up, baris y ≠ 0) dengan sinyal kandidat,
  interval bootstrap blok origin, q BH per keluarga uji.
- Wajib menyertakan kontrol: positif (sinyal yang terbukti membantu, mis. `iw_gap`, ρ 0,10–0,13 → dev +0,002..+0,020) dan negatif
  (derau; fitur yang sudah dipakai). Bila kontrol negatif tidak ≈ 0 (model kurang memakai fitur), sinyal kandidat harus di-*partial*-kan
  terhadap fitur terkait sebelum dibaca (contoh D-153 DU-3c).
- Periksa pengganggu sebelum menulis hipotesis: stabilitas antarperiode (co-trend sesaat), kesulitan intrinsik vs kekurangan model (skill
  terhadap laju-dasar), tumpang tindih dengan fitur yang ada.
- Sinyal **tingkat nasional** (konstan antarprovinsi pada komoditas × origin, mis. cuaca sentra, impor): korelasi residual pooled
  bersifat in-sample dan hanya bervariasi antar ± 37 origin. Sebelum Modeling, wajib menyertakan koreksi logit walk-forward berparameter
  kecil (koefisien dari origin lampau saja); D-157: korelasi 0,14–0,17 bertanda stabil tetap memperburuk macro F1 & Brier walk-forward.
- **Kelayakan sumber baru** (D-159, sebelum DU): riwayat mencakup origin dev (≥ 2020 untuk pelatihan + 2021–2023), akses sah tanpa login/CAPTCHA,
  tanggal ketersediaan (rilis/penutupan) dapat ditetapkan, frekuensi ≤ mingguan atau bertanggal, dan skala mengukur pasar (bukan log
  program kecil). Gagal → tidak dimodelkan dan tidak di-backfill; hanya permintaan data atau evaluasi prospektif.
- **Layar arah nasional** (D-158): kandidat yang menargetkan komponen nasional (komoditas × minggu) wajib menunjukkan AUC/akurasi arah
  nasional walk-forward di atas **konsensus C1t** (rerata p_up provinsi OOS, AUC ± 0,75) sebelum modeling provinsi. Koreksi dibuat
  increment-only (offset = logit konsensus); kalibrasi ulang konsensus dengan intersep/dummy komoditas historis dilarang (base rate bergeser).
- **Sumber prakiraan** (D-161, sebelum biaya ekstraksi): uji dulu **oracle** = nilai TERREALISASI variabel yang diprakirakan pada jendela
  prakiraan yang sama (data teramati yang sudah ada, mis. NASA POWER untuk cuaca) dengan layar arah nasional di atas. Prakiraan tidak memuat
  informasi lebih dari realisasinya untuk mekanisme yang sama; oracle gagal → mekanisme tertutup, ekstraksi prakiraan tidak perlu.
- Gerbang (heuristik, dikalibrasi pada kontrol positif): lanjut ke Modeling bila sinyal parsial q < 0,05 di kedua horizon **dan**
  besarnya ≥ ½ kontrol positif. Di bawah itu, keuntungan yang diharapkan di bawah derau pelatihan dev (± 0,005) dan MDE test
  (0,019 / 0,010, D-152), sehingga hasil Modeling tidak dapat diputuskan. Pengecualian harus beralasan pengetahuan, bukan skor.

## 4. Aturan evaluasi yang tetap (D-145–D-152)

- Pembanding = C1-tuned beku (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed resmi, threshold 0,5); label & baris evaluasi resmi; perubahan
  kecil tetap dievaluasi; preprocessing beku (D-148).
- Seleksi hanya di origin pengembangan; test (origin ≥ 2024-01-01) dibuka sekali untuk satu kandidat per keluarga yang lolos: Δ macro F1
  rerata ≥ +0,005, interval berpasangan > 0 di ≥ 1 horizon, Δ ≥ 0 di horizon lain. Test tidak dipakai memilih ulang apa pun.
- Wajib dilaporkan: macro F1 & interval, F1 naik/turun, kuintil |y| terkecil, per komoditas, porsi prediksi naik, q BH, dan kriteria
  bisnis S1–S3 (D-154) terhadap C1-tuned. Kandidat yang menaikkan macro F1 tetapi menurunkan S1–S3 tidak dianggap lebih baik.
- Protokol (kandidat, aturan, kontrol kebocoran) ditulis dan di-hash sebelum run.
- Keluarga intraminggu sudah memakai test 2024+ dua kali; konfirmasinya hanya lewat prediksi maju beku (D-152), yang dayanya hanya cukup
  untuk mendeteksi kegagalan besar.

## 5. Ketepatan target, ukuran, dan klaim (D-155)

- **Test 2024+ bukan data independen** (dipakai D-145–D-154). Hasil test baru ditulis "evaluasi eksploratif dengan kriteria yang ditetapkan
  sebelumnya", bukan "validasi". Bukti independen hanya dari origin yang belum pernah dipakai (prediksi maju beku).
- **Universe ranking/daftar pantau** = semua kandidat yang datanya tersedia pada origin, tanpa penyaringan berdasarkan target (termasuk
  y = 0 dan target yang kemudian tidak teramati, dihitung tidak kena). Ranking hanya memakai informasi ≤ origin.
- **Skor ≠ target bisnis.** p_up = P(naik | y ≠ 0, X). Untuk risiko kenaikan material, latih/kalibrasi pada target terpisah
  z = 1[y ≥ ambang] (semua baris); jangan menyebut p_up "peluang kenaikan material". Kalibrasi hanya berlaku untuk label yang dilatih.
- **Ukuran bersyarat pada hasil** (mis. F1 pada baris yang ternyata bergerak material) tidak menunjukkan kemampuan mengetahui sebelumnya;
  beri label bersyarat.
- **Materialitas statistik** (relatif riwayat komoditas) dan **materialitas kebijakan** (ambang yang disepakati pengguna) dilaporkan
  terpisah. **Titik akhir** (perubahan minggu t + h vs t) berbeda dengan **kejadian dalam jendela** (kapan pun dalam h minggu).
- **Daftar pantau** dibandingkan pada jumlah alarm yang sama; laporkan alarm per origin, presisi, recall, alarm palsu, sebaran provinsi &
  komoditas. Anggaran pemantauan (K) tidak dipilih dari test.
- **Kebocoran**: bedakan look-ahead observasional (dapat diuji dengan perturbasi/penghapusan data sesudah cutoff) dan revisi/vintage (tidak
  dapat diuji tanpa vintage PIHPS). `available_at` konservatif = Minggu 00.00 sampai jendela revisi PIHPS dipastikan (`[HUMAN]`).
- **Terminologi metode**: sebut screening/asosiasi bila bukan algoritma yang dimaksud (mis. screening asosiasi temporal ≠ sequential
  pattern mining); validitas klaster dilaporkan dengan silhouette per k, DB/CH, dan stabilitas, bukan satu angka terbaik.

## 6. Registri eksperimen terpusat (D-156)

- Semua eksperimen Task 4 arah (D-145 dan seterusnya; per 2026-11-26 s.d. D-163), termasuk yang gagal, diblokir, dan ditolak, tercatat satu baris per varian di
  [`docs/eksperimen_registry.csv`](eksperimen_registry.csv): ID, rujukan keputusan, fase, hipotesis, versi data, konfigurasi fitur /
  preprocessing / model / hyperparameter / threshold, origin, macro F1 h 4 & h 8, F1 per kelas (bila ada), Δ vs C1-tuned + interval,
  status, lokasi skrip, keputusan dan alasannya.
- Status: `COMPLETE` (dijalankan penuh; acuan, diadopsi, atau hasil dicatat), `PARTIAL` (dijalankan dengan pemangkasan), `FAILED`
  (eksekusi gagal), `BLOCKED` (tidak dapat dijalankan dengan data/akses yang ada), `REJECTED` (dijalankan, ditolak aturan atau gerbang).
- Eksperimen baru menambah barisnya pada sesi yang sama. Pembangun saat ini: `docs/audit/20261126_task4_master_f1/scripts/r_registry.py`
  (membaca CSV hasil setiap laporan; angka D-145/D-146 disalin dari laporannya).
- Aturan "lebih baik secara berarti" yang dipakai D-156 (lebih ketat dari §4): §4 + q BH < 0,05 di antara kandidat sesi itu, Δ ≥ 0 di
  ≥ 2 dari 3 tahun dev dan porsi origin Δ > 0 ≥ 0,5 di kedua horizon, F1 naik & turun tidak turun > 0,01, tidak ada komoditas turun
  > 0,03 di kedua horizon.
