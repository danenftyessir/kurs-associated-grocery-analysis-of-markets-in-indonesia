# Gabungan Audit KAGAMI — keadaan per 2026-11-27

Tanggal: 2026-11-27 · Disusun: Danen (dengan agent) · Cakupan: seluruh isi `docs/audit/` per 2026-11-27 03.00 WIB, yaitu 20 laporan utama dan
24 dokumen pendukung (protokol, dokumen K4, dokumen Jalur A) bertanggal 2026-11-24 s.d. 2026-11-26, keputusan D-139 s.d. D-165.

Catatan bertanggal, bukan dokumen hidup, dan **tidak menggantikan laporan sumber**. Aturan baca:
- Angka dikutip dari laporan sumber yang ditautkan di setiap bagian. Bila ada perbedaan, **laporan sumber yang berlaku**.
- Bila laporan lama dikoreksi laporan yang lebih baru, yang dicantumkan di sini adalah **versi terkini**, ditandai "(dikoreksi D-xxx)". Daftar
  lengkap koreksi ada di §2.4.
- Semua klasifikasi arah, model deep, K4, dan uji sumber data baru bersifat **EKSPLORATIF**: bukan uji praregistrasi. H5 tetap diuji dari MAE +
  DM pada `forecast_eval`. Hasil bersifat asosiasional dan berasal dari evaluasi rolling-origin pseudo-real-time; bukan ramalan.

Konvensi: "a / b" = h 4 / h 8 minggu kecuali disebut lain · **dev** = origin pengembangan (origin + h ≤ 2023-12-31; 38 / 37 origin; 10.966 /
11.307 baris y ≠ 0) · **test** = origin ≥ 2024-01-01 (37 / 36 origin; dipakai berulang sejak D-145, jadi **bukan data independen**, D-155) ·
interval = 95% bootstrap blok origin berpasangan (1.999 replikasi) kecuali disebut lain · C1t = C1-tuned · Δ = selisih terhadap C1t kecuali
disebut lain · "lolos/gagal" = menurut aturan yang ditulis sebelum run · q = Benjamini–Hochberg dalam keluarga uji laporan itu.

## Daftar isi

0. Ringkasan eksekutif · 1. Peta laporan · 2. Angka yang berlaku sekarang · 3. Evaluasi & pelacakan halaman 7 (D-139–D-144) ·
4. Optimasi klasifikasi arah (D-145, D-146) · 5. Audit preprocessing & kualitas label (D-147, D-156 fase B) · 6. Rezim & kalibrasi temporal
(D-148, D-149) · 7. Sumber data baru & informasi eksternal (D-150–D-152, D-157–D-161, D-165) · 8. CRISP-DM: Data & Business Understanding
(D-153–D-155) · 9. Master macro F1 (D-156) · 10. Penutupan kelemahan tercatat (D-162, D-163, D-163a) · 11. K4 risiko kenaikan material
(D-164) · 12. Jalur A (D-165) · 13. Sintesis: di mana batas skor berada · 14. Aturan metode yang lahir dari audit · 15. Rambu klaim Task 4 ·
16. Prediksi maju beku & jadwal · 17. Pekerjaan terbuka · 18. Registri eksperimen · 19. Indeks lampiran

---

## 0. Ringkasan eksekutif

| # | Pertanyaan | Jawaban terkini | Sumber |
|---|---|---|---|
| 1 | Apakah fitur kurs memperbaiki prediksi (H5)? | **Tidak.** M2/M1 MAE 1,009 (DM p 0,009) / 1,013 (p 0,025), sedikit lebih buruk; H5 large_move 1,112 / 1,115, Holm 1,0 → tidak didukung (dikoreksi D-162; sebelumnya 1,014 / 1,017). Kurs juga tidak menambah akurasi arah di keluarga model mana pun (C2 − C1, C2t − C1t, TSMixer ± kurs, TimesFM ± kurs). | §2.1, §10 |
| 2 | Klasifier arah terbaik? | **C1-tuned** (HGB, 37 fitur dinamika harga + identitas, tanpa kurs): test macro F1 **0,677 / 0,680**, dev 0,656 / 0,676. Tidak terungguli oleh 189 varian yang tercatat di registri (126 ditolak). | §4, §18 |
| 3 | Dari mana kenaikan C1-tuned? | Hampir seluruhnya dari fitur: deviasi terhadap rerata bergerak & antarprovinsi, sinyal nasional komoditas, lag panjang, musiman. Tuning hyperparameter hanya ± +0,01. | §4.2 |
| 4 | Mengapa berhenti di ± 0,68? | Dua bottleneck. (1) Arah **perubahan kecil** hampir tak teramalkan: AUC kuintil \|y\| terkecil 0,60 / 0,56, dan ± ⅓ labelnya rapuh (sub-tick Rp50 / komposisi hari). (2) **Pergeseran base rate per origin** (hari libur, rezim kebijakan) yang baru terlihat sesudah target terealisasi: oracle threshold per origin +0,035 / +0,024, tidak dapat direalisasikan walk-forward. | §9.2, §13 |
| 5 | Ada galat preprocessing atau kebocoran? | **Tidak ditemukan** galat yang mengubah label/fitur. Uji kebocoran 76 origin × 54 kolom = 0 sel berbeda; fitur intraminggu 84/84 lolos; semua fitur sumber baru 0 sel. Satu bug ditemukan dan diperbaiki: flag `episode` (grup kurs) tidak real-time (U108 → D-162). Revisi/vintage PIHPS **tidak dapat diuji** (U110). | §5, §10.1 |
| 6 | Plafon informasi? | Informasi **sempurna** tentang arah nasional per komoditas × minggu hanya memberi 0,756 / 0,782 (headroom +0,105). Target 0,8–0,9 berada di atas plafon itu. | §7.4, §13 |
| 7 | Sinyal baru yang pernah membantu? | Hanya **informasi intraminggu** (posisi harga hari terakhir terhadap rerata minggu, nasional). `IW_NAT` test +0,0085 / +0,0033, q 0,28 / 0,30 (belum terbukti, test tidak bersih). Separuh keuntungan h 4 berasal dari harga Jumat (nowcast level). Konfirmasi hanya lewat prediksi maju (daya rendah). | §7.2 |
| 8 | Sumber data baru? | 28 sumber diaudit/diuji (grosir, produsen, kota PIHPS, cuaca NASA POWER, impor, SIJAGUNG, CFSv2, GDELT, SP2KP, Bapanas, dll.): **tidak ada yang lolos**. Sumber pasokan yang paling masuk akal (SP2KP stok mingguan, Proyeksi Neraca Pangan, luas tanam/EWS) tertutup oleh **akses**, bukan oleh bukti sinyal (U112). | §7 |
| 9 | Nilai bagi TPID? | Daftar pantau 2 komoditas/provinsi dari skor C1-tuned: presisi test 0,179 / 0,161 vs aturan tren 0,08–0,09. **Dikoreksi D-164**: terhadap laju-dasar komoditas, h 4 test +0,082 (0,050..0,120) tetapi h 8 tidak terbukti (dev −0,026, test +0,019). | §8.2, §11 |
| 10 | K4 risiko kenaikan material? | Model yang sama dilatih langsung pada z = 1[y ≥ P80 \|y\|]: **ranking lebih baik** (ΔAP h 4 dev +0,080, test +0,045; h 8 searah, tidak terbukti); peluang h 4 terkalibrasi, h 8 tidak → **PARTIAL**, status operasional **BLOCKED** sampai U109. | §11 |
| 11 | Model deep & foundation? | TimesFM 3.0 zero-shot MAE/M1 0,935 / 0,895 (lolos BH), macro F1 test 0,618 / 0,621, tetapi berstatus **batas atas** (risiko kontaminasi korpus pralatih). PatchTST/TSMixer/TCN/MLP semuanya di bawah boosting. | §3.5, §4 |
| 12 | Kelemahan inferensi Task 1–3? | U107 sebagian ditutup: PT nasional & deviasi provinsi kini punya interval terkalibrasi plasebo (`national_calibrated` baris PT, `province_calibrated`, D-163). 13/33 fitur clustering konstan terbukti inert. | §10.2–§10.3 |
| 13 | Yang masih terbuka | U109 (kebutuhan TPID), U110 (jendela revisi PIHPS), U111 (data kab/kota), U112 (data pasokan). Tiga pembekuan prediksi maju menunggu target (pertama lengkap Jumat 2026-11-27). **Versi beku prediksi maju K4 belum di-commit.** | §16, §17 |

---

## 1. Peta laporan

| # | Tanggal | Laporan | Keputusan | Pertanyaan pokok | Hasil satu baris | Test 2024+ |
|---|---|---|---|---|---|---|
| 1 | 11-24 | [Audit halaman 7](20261124_audit_evaluasi_eksekusi.md) | D-139–D-144 | Apakah halaman Evaluasi & Riwayat Eksekusi jujur dan lengkap? | "ok" ≠ bagus; penilaian dua lapis, interval origin, BH, lineage output ditambahkan | – |
| 2 | 11-24 | [Optimasi arah ronde 1](20261124_task4_optimasi_arah.md) | D-145 | Dapatkah macro F1 arah dinaikkan? | C1-tuned 0,677 / 0,680; kurs tidak membantu | dibuka |
| 3 | 11-25 | [Ronde 2](20261125_task4_ronde2.md) | D-146 | Di mana galat C1-tuned; fitur/model lain? | Galat di perubahan kecil; tidak ada yang lebih baik | 3 kelas saja |
| 4 | 11-25 | [Audit preprocessing](20261125_task4_audit_preprocessing.md) | D-147 | Apakah preprocessing membatasi skor? | Tidak; tick Rp50, label rapuh ≤ ± 0,015; `iw_gap` +0,004 / +0,005 | `iw_gap` sekali |
| 5 | 11-25 | [Ronde 4: rezim & kalibrasi](20261125_task4_ronde4.md) | D-148, D-149 | Fitur sadar-rezim / kalibrasi temporal? | Tidak lolos di split mana pun; drift = bias proporsi | tidak |
| 6 | 11-25 | [Riset sumber hulu](20261125_sumber_data_hulu.md) | – | Sumber grosir/produsen/pasokan/cuaca apa yang ada? | PIHPS pedagang besar & produsen kandidat terkuat | – |
| 7 | 11-25 | [Pilot grosir](20261125_pilot_grosir.md) | D-150 | Apakah harga grosir mendahului eceran? | Tidak; kaku 85–98%; −0,006..+0,001 | tidak |
| 8 | 11-25 | [Pilot produsen & intraminggu](20261125_pilot_produsen_intraminggu.md) ([protokol](20261125_pilot_produsen_intraminggu/PROTOKOL.md)) | D-151 | Harga produsen? Informasi dalam minggu? | Produsen tidak; `IW_NAT` test +0,0085 / +0,0033 belum terbukti | `IW_NAT` sekali |
| 9 | 11-25 | [Validasi IW_NAT](20261125_iw_validasi.md) ([protokol](20261125_iw_validasi/PROTOKOL.md)) | D-152 | Kebocoran, asal sinyal, prediksi maju | 84/84 bersih; sinyal dari provinsi lain; separuh h 4 dari Jumat; prediksi maju beku | tidak |
| 10 | 11-25 | [CRISP-DM Data Understanding](20261125_crisp_du.md) | D-153 | Pola lintas komoditas, clustering seri, graf provinsi? | Ketiganya tidak lolos gerbang Modeling | tidak |
| 11 | 11-25 | [Business Understanding](20261125_business_understanding.md) ([protokol](20261125_business_understanding/PROTOKOL.md), [audit](20261125_business_understanding/PROTOKOL_AUDIT.md)) | D-154, D-155 | Apakah C1-tuned berguna bagi TPID? | S1–S3 lolos; adendum mengoreksi tafsiran | dibuka (S1–S3) |
| 12 | 11-26 | [Master macro F1](20261126_task4_master_f1.md) ([protokol](20261126_task4_master_f1/PROTOKOL.md)) | D-156 | Audit preprocessing + 27 kandidat optimasi | 0/27 lolos; bottleneck = informasi | tidak |
| 13 | 11-26 | [Cuaca sentra & impor](20261126_pilot_cuaca_impor.md) ([protokol](20261126_pilot_cuaca_impor/PROTOKOL.md)) | D-157 | Cuaca NASA POWER, impor bulanan | Tidak membantu; impor memperburuk h 8 | tidak |
| 14 | 11-26 | [National shock nowcasting](20261126_nasional_lokal.md) ([I1](20261126_nasional_lokal/PROTOKOL_I1.md), [I2](20261126_nasional_lokal/PROTOKOL_I2.md)) | D-158 | Breadth 110 kota, model nasional → lokal | Kontribusi kota ≈ 0; konsensus C1t prediktor nasional terbaik | tidak |
| 15 | 11-26 | [Pasokan fisik](20261126_pasokan_fisik.md) | D-159 | SP2KP, FDP, PIBC, GPM, KSA | Tidak ada riwayat dev yang dapat diakses | – |
| 16 | 11-26 | [Sumber baru](20261126_sumber_baru.md) | D-160, D-161 | GDELT, CFSv2, SIJAGUNG/SPORA, DIBI | SIJAGUNG gagal; CFSv2 diuji di Colab, gagal G5 (oracle juga gagal) | – |
| 17 | 11-26 | [Kalibrasi daftar pantau](20261126_kalibrasi_pantau.md) ([protokol](20261126_kalibrasi_pantau/PROTOKOL.md)) | D-163a | Lapisan kalibrasi pada p_up | ECE turun, Brier tidak → ditolak | tidak |
| 18 | 11-26 | [Penutupan kelemahan](20261126_kelemahan_tercatat.md) | D-162, D-163 | U108, U107, fitur konstan, IW_NAT | `episode` real-time; PT & provinsi terkalibrasi; fitur konstan inert | – |
| 19 | 11-26 | [K4 risiko material](20261126_k4_risiko_material/RESULTS.md) (+ 9 dokumen) | D-164 | P(kenaikan material) langsung | PARTIAL; BLOCKED operasional | dibuka sekali |
| 20 | 11-26 | [Jalur A](jalur_a_macro_f1/RESULTS.md) (+ 6 dokumen) | D-165 | Validasi maju, GDELT, pasokan ulang | GDELT gagal G5 (BigQuery sandbox); pasokan terblokir akses | tidak |

Dokumen pendukung K4: [INITIAL_AUDIT](20261126_k4_risiko_material/INITIAL_AUDIT.md), [BUSINESS_REQUIREMENTS](20261126_k4_risiko_material/BUSINESS_REQUIREMENTS.md),
[TARGET_DEFINITION](20261126_k4_risiko_material/TARGET_DEFINITION.md), [DATA_UNDERSTANDING](20261126_k4_risiko_material/DATA_UNDERSTANDING.md),
[PROTOCOL](20261126_k4_risiko_material/PROTOCOL.md), [CALIBRATION_REPORT](20261126_k4_risiko_material/CALIBRATION_REPORT.md),
[OPERATIONAL_ANALYSIS](20261126_k4_risiko_material/OPERATIONAL_ANALYSIS.md), [RECOMMENDATIONS](20261126_k4_risiko_material/RECOMMENDATIONS.md),
[scripts/RUN.md](20261126_k4_risiko_material/scripts/RUN.md). Jalur A: [INITIAL_AUDIT](jalur_a_macro_f1/INITIAL_AUDIT.md),
[PROTOCOL](jalur_a_macro_f1/PROTOCOL.md), [GDELT_FEASIBILITY](jalur_a_macro_f1/GDELT_FEASIBILITY.md), [GDELT_PILOT](jalur_a_macro_f1/GDELT_PILOT.md),
[SUPPLY_SIDE_SOURCE_AUDIT](jalur_a_macro_f1/SUPPLY_SIDE_SOURCE_AUDIT.md), [RECOMMENDATIONS](jalur_a_macro_f1/RECOMMENDATIONS.md).

Alur keputusan: audit evaluasi (D-139–D-144) → optimasi model (D-145–D-146) → audit data (D-147) → rezim (D-148–D-149) → sumber hulu PIHPS
(D-150–D-152) → pergantian ke alur CRISP-DM (D-153–D-155) → audit menyeluruh (D-156) → sumber non-harga (D-157–D-161, D-165) → penutupan
kelemahan (D-162–D-163a) → target bisnis terpisah K4 (D-164).

---

## 2. Angka yang berlaku sekarang

### 2.1 Uji resmi Task 4 (praregistrasi; rolling-origin semua origin 2021-01-04 .. freeze − h)

| Model | MAE / M1 h 4 (DM p) | MAE / M1 h 8 (DM p) | Catatan |
|---|---|---|---|
| M0 (ramalan nol) | 1,017 (0,062) | 1,016 (0,161) | – |
| M1 (ridge, base) | 1 (MAE 0,0736) | 1 (MAE 0,1036) | R² out-of-sample 0,086 / 0,072; MAPE tidak berlaku (y = 0 pada 3.672 / 2.345 baris) |
| **M2** (+ kurs & harga dunia; uji H5) | **1,009 (0,009)** | **1,013 (0,025)** | dikoreksi D-162 (sebelumnya 1,014 / 1,017) → fitur kurs sedikit memperburuk |
| M3 (HGB + identitas) | 1,037 (0,052) | 1,014 (0,53) | dikoreksi D-162 (sebelumnya 1,044 / 1,015) |
| H5: M2/M1 h 8 large_move, impor langsung / input impor | 1,112 / 1,115, Holm 1,0 | – | tidak didukung (8 origin large_move) |
| V2 studi kasus origin 2026 | 1,005 | 1,004 | – |

Angka diagnostik dari 2026-11-24 (sebelum D-162 untuk M2/M3; M1 tidak berubah): `share_fx_improves` 5/20 sel (binomial p 0,041); M2/M1
terburuk pada grup fokus berharga kaku: daging sapi 1,252 / 1,296, gula 1,204 / 1,125, beras 1,137 (h 4). `M2_nofx` identik dengan M1, sehingga
ablation resmi hanya mengulang M2 vs M1.

### 2.2 Klasifikasi arah eksploratif (test, origin ≥ 2024; baris y ≠ 0, cakupan 0,855 / 0,907)

| Model | Keputusan | macro F1 test h 4 / h 8 | Δ vs C1t (interval, q) | Status |
|---|---|---|---|---|
| C1 (HGB base + id) | D-141 | 0,586 / 0,607 | −0,092 (−0,118..−0,065) / −0,067 | pembanding |
| C2 (+ kurs) | D-141, D-162 | 0,581 / 0,614 | – | kurs tidak terbukti membantu |
| TSMixer resmi | D-142 | 0,594 / 0,620 | – | – |
| TimesFM 3.0 zero-shot | D-142 | 0,618 / 0,621 | −0,059 (−0,075..−0,043) / −0,053 (−0,077..−0,027) | batas atas (kontaminasi) |
| TimesFM + threshold dev | D-145 | +0,012 / +0,024 vs TimesFM | lolos BH vs TimesFM | – |
| TimesFM → CatBoost (TFM-head) | D-145 | 0,672 / 0,676 | −0,005 (q 0,44) / +0,002 (q 0,79) | setara C1t; TimesFM tidak menambah informasi |
| TSMixer-tuned (3 seed) | D-145 | 0,580–0,587 / 0,599–0,609 | lebih buruk dari TSMixer resmi | ditolak |
| **C1-tuned** | **D-145** | **0,677 (0,652..0,698) / 0,680 (0,653..0,706)** | – | **model arah terpilih** |
| C2-tuned (+ kurs) | D-145, D-162 | 0,675 / 0,679 | −0,004 (−0,011..0,004) / +0,001 (−0,008..0,011) (D-145) | kurs tidak membantu |
| C1t + `iw_gap` (P04b) | D-147 | 0,681 / 0,684 | +0,004 (q 0,35) / +0,005 (q 0,089) | belum terbukti |
| `IW_NAT` (8 fitur intraminggu) | D-151 | 0,686 / 0,683 | +0,0085 (−0,003..0,024, q 0,28) / +0,0033 (−0,004..0,011, q 0,30) | belum terbukti; test tidak bersih |
| Dua tahap 3 kelas (tetap/naik/turun) | D-146 | 0,625 / 0,606 (macro F1 3 kelas) | tidak sebanding | dilaporkan terpisah |

C1-tuned rinci (test): F1 naik / turun 0,704 / 0,651 dan 0,725 / 0,634; MCC 0,356 / 0,363; ROC-AUC 0,741 / 0,738; PR-AUC 0,742 / 0,755;
sd macro F1 antar-origin 0,084 / 0,074; seed lain 0,680 / 0,679 (h 4) dan 0,677 / 0,683 (h 8). Pada 25% prediksi paling yakin per origin,
akurasi 0,829 / 0,808.

Perbandingan semua origin (halaman 7, D-144; h 8, baris berubah, baseline mayoritas 0,545): macro F1 M1 0,551, M2 0,549, M3 0,594, C1 0,605,
C2 0,614, PatchTST 0,593, TSMixer 0,604, TSMixer + kurs 0,598, TimesFM 0,623, TimesFM + kurs 0,611 (M2, M3, C2 sebelum D-162; sesudah D-162 C2
akurasi 0,620, selisih vs baseline +0,075 (0,038..0,110)).

### 2.3 Nilai bagi pengguna (eksploratif; materialitas statistik P80 |y| per komoditas, titik akhir)

| Ukuran | Dev h 4 / h 8 | Test h 4 / h 8 | Sumber |
|---|---|---|---|
| Laju-dasar kenaikan material | 0,120 / 0,132 | 0,088 / 0,089 | D-154, D-164 |
| Presisi daftar pantau 2/provinsi, skor C1t | 0,249 / 0,221 | 0,179 / 0,161 (recall 0,41 / 0,36) | D-154 |
| Presisi daftar pantau 2/provinsi, skor **K4-E80** | 0,293 / 0,272 | 0,202 / 0,174 (recall 0,46 / 0,39) | D-164 |
| Presisi laju-dasar komoditas (B-CLIM) | 0,190 / **0,248** | 0,097 / 0,143 | D-164 |
| Aturan tren terbaik (`R_mom` / `R_nat`) | 0,139 / 0,155 | 0,085 / 0,089 | D-154 |
| AP K4 / C1t / laju-dasar komoditas | 0,326 / 0,246 / 0,184 · 0,290 / 0,250 / 0,208 | 0,237 / 0,192 / 0,106 · 0,206 / 0,191 / 0,122 | D-164 |
| Arah saat bergerak material (S3, **bersyarat pada hasil**) macro F1 C1t vs aturan tanda tren | 0,777 vs 0,541 · 0,797 vs 0,502 | 0,809 vs 0,496 · 0,812 vs 0,443 | D-154 |
| Brier skill arah (S2) / ECE arah | 0,133 / 0,035 · 0,160 / **0,056** | 0,170 / 0,010 · 0,167 / 0,021 | D-154 |

### 2.4 Daftar koreksi (klaim lama → versi terkini)

| Klaim / angka lama | Dari | Koreksi | Oleh |
|---|---|---|---|
| M2/M1 1,014 / 1,017 (DM p 0,001 / 0,006); M3/M1 1,044 / 1,015 | uji resmi | 1,009 / 1,013 (p 0,009 / 0,025); 1,037 / 1,014; kesimpulan H5 sama | D-162 |
| "C2 lebih akurat dari M3 pada h 4 (+0,025, q 0,015)" | D-141, D-143 | **gugur**: +0,013, q 0,36; beda berpasangan lolos BH 5/30 → 4/30 | D-162 |
| C2 − C1 h 8 +0,009 (−0,007..0,027) | D-141 | +0,012 (−0,004..0,030), tetap tidak terbukti | D-162 |
| "V4: 26/30 sel cocok" sebagai validasi LP vs event study | robustness | kriteria interval yang longgar; **kesamaan tanda 0,508 ≈ koin**, korelasi rerata 0,14 → V4 tidak memvalidasi | audit hal. 7 |
| Tier 1 "baseline dalam interval 95,8%" | robustness | mencerminkan lebar interval (median 0,83), bukan kestabilan; laporkan kesamaan tanda & \|Δ\|/SE | audit hal. 7, D-140 |
| Segmen "M1 lentur lebih baik", "M2 kaku lebih buruk", "TimesFM kaku lebih buruk" | D-140 | tidak lolos BH (q 0,064 / 0,080 / 0,053) → belum terbukti | D-143 |
| `robustness` resmi tidak sinkron dengan run tercatat | D-140 | dijalankan tercatat, sha256 identik (679 baris); dijalankan ulang D-162 (44 baris V2 berubah) | D-144, D-162 |
| Skor daftar pantau = "peluang naik" | D-154 | p_up = P(naik \| y ≠ 0, X), **bukan** P(kenaikan material); S1 = kualitas ranking; S2 = kalibrasi arah | D-155 |
| S3 "model benar saat harga bergerak material" | D-154 | ukuran bersyarat pada hasil; bukan kemampuan mengetahui sebelumnya baris mana yang bergerak | D-155 |
| Test 2024+ sebagai validasi | D-145–D-154 | "evaluasi eksploratif dengan kriteria yang ditetapkan sebelumnya"; bukti independen hanya dari prediksi maju | D-155 |
| "Kenaikan material" tanpa kualifikasi | D-154 | materialitas **statistik** relatif per komoditas (P80 \|y\| latih) ≠ kebijakan; titik akhir ≠ kejadian dalam jendela | D-155 |
| Daftar pantau C1t "dua kali laju-dasar, mengalahkan aturan sederhana" | D-154 | pembanding laju-dasar per komoditas tidak ada; h 8 C1t tidak terbukti di atasnya (dev 0,221 vs 0,248) | D-164 |
| V2 nasional "kurang tegas" | D-154 | merujuk interval vs aturan naif; pada jumlah alarm sama V2 sedikit lebih presisi tetapi ± 1,5 provinsi/minggu tanpa alarm | D-155 |
| K1 "Sequential Pattern Mining" | D-153 | yang dijalankan = screening asosiasi temporal lintas komoditas; tidak membuktikan ketiadaan pola sekuensial lain | D-155 |
| K2 "5 tipe seri" | D-153 | silhouette hampir datar (0,331–0,344 untuk k 2..6): partisi deskriptif, bukan kelompok alami; DB/CH/stabilitas belum dihitung | D-155 |
| K3 graf geografis = hubungan pasokan | D-153 | kedekatan ibu kota hanya proksi; graf korelasi = statistik 2018–2020 | D-155 |
| `available_at` Sabtu 00.00 | D-152 | konservatif Minggu 00.00 sampai jendela revisi PIHPS pasti (U110); nilai fitur tidak berubah | D-155 |
| "Tidak ada kebocoran" (fitur intraminggu) | D-152 | tidak ditemukan look-ahead observasional; kebocoran revisi/vintage belum dapat diverifikasi | D-155 |
| Fitur regulasi ronde 2: acuan beras | D-146 | memakai batas atas premium Rp15.800 sejak 2024-06-02 (hanya test); dev tidak terdampak; diperbaiki di ronde 4 | D-148 |
| CFSv2 BLOCKED (skala) | D-160 | diuji lewat Colab → **REJECTED** (gagal G5, oracle juga gagal) | D-161 |
| GDELT BLOCKED (BigQuery berbayar) | D-160 | diuji lewat BigQuery sandbox tanpa billing → **REJECTED** (gagal G5); U113 ditutup | D-165 |
| Flag `episode` Task 4 dari periode penuh | D-147 | bocor pada 1/76 origin; diganti flag real-time (pemicu s.d. t); 61 → 55 minggu bertanda | D-162 |
| Dua bug skrip audit | D-158, D-164 | `kb_cov`/`kp_n` breadth kota gagal uji penghapusan (533.750 sel) → diperbaiki sebelum hasil dilihat; `fast_ap` K4 (NaN → −inf) → diperbaiki sebelum evaluasi pertama dibaca | D-158, D-164 |

---

## 3. Evaluasi & pelacakan halaman 7 (D-139–D-144)

Sumber: [20261124_audit_evaluasi_eksekusi.md](20261124_audit_evaluasi_eksekusi.md) (audit awal 12 run, Lampiran B tindak lanjut D-140, Lampiran C
audit ulang 23 run, C.7 D-143, C.8 D-144).

### 3.1 Sepuluh kelemahan audit awal dan statusnya sekarang

| # | Kelemahan awal (12 run, 2026-11-24 pagi) | Status terkini |
|---|---|---|
| 1 | Status "ok" berarti *berhasil dihitung*, tetapi dibaca sebagai *bagus*; skor ≈ 0,5 tampil hijau | **Selesai (D-140)**: `tracking.assessment` menilai setiap metrik terhadap acuan eksplisit (peluang, baseline mayoritas, α, rasio 1, p95 plasebo, MDE) → lebih baik / lebih buruk / belum terbukti / sesuai harapan / perlu ditinjau / informasi |
| 2 | Akurasi arah tanpa ketidakpastian (n ≈ 22 ribu baris berkorelasi) | **Selesai (D-140)**: bootstrap blok origin (unit = origin); M1/M2 terbukti tidak berbeda dari baseline mayoritas |
| 3 | Agregat menutupi kegagalan komoditas diatur | **Selesai (D-140)**: tabel segmen (komoditas, jalur, grup H5, kekakuan, tahun origin) |
| 4 | Kurs memperburuk MAE di sapi/gula | Ditampilkan; konsisten dengan H5 tidak didukung |
| 5 | `M2_nofx` ≡ M1 → ablation resmi tidak informatif | **Sebagian**: ablation kurs yang bermakna kini dari C2 − C1, TSMX_fx − TSMX, TFM_fx − TFM; ablation per kelompok fitur M2 belum |
| 6 | Kriteria Tier 1 "baseline dalam interval" terlalu longgar | **Selesai**: lebar interval, kesamaan tanda, porsi terdeteksi, \|Δ\|/SE per tier |
| 7 | Task 1 & Task 4 tidak pernah dieksekusi di bawah pelacakan | **Task 4 selesai**: `forecast_preds`/`forecast_eval`/`ablation` dijalankan ulang tercatat (D-162, 2026-11-26). Task 1 tetap "hanya dievaluasi" (artefak dari Kaggle) |
| 8 | Run `robustness` terakhir ≠ produsen artefak resmi | **Selesai**: `store.artifact_sync` & `stage_states` (D-140); run tercatat identik (D-144); dijalankan ulang (D-162) |
| 9 | `task2` membaca `province_features` tanpa deklarasi | **Selesai**: `task2.OPTIONAL`, `robustness.OPTIONAL` + tes baca-vs-deklarasi |
| 10 | Cacat UI (rerata waktu lintas tahap, "None", label Inggris, default kosong, metrik baru dihitung "berubah") | **Selesai** (kecuali tooltip algoritma → kolom lebar) |

### 3.2 Arti skor "≈ 0,5" (nilai dari audit awal)

| Metrik | Nilai | Acuan | Kesimpulan |
|---|---|---|---|
| Kesamaan tanda LP vs event study (V4) | 0,508 (30 sel), korelasi 0,14 | 0,5 | V4 secara praktis tidak memvalidasi |
| Akurasi arah M1 / M2 | 0,543–0,560 | baseline mayoritas 0,527 / 0,545 | interval selisih memuat nol |
| ROC-AUC M1–M3; MCC | 0,567–0,627; 0,08–0,19 | 0,5; 0 | daya pemisah lemah |
| R² out-of-sample | 0,07–0,09 | 0 | < 10% variasi perubahan 4–8 minggu |
| Porsi interval nasional tidak memuat nol | 0,0625 (3/48) | α 0,05 | setara laju positif palsu (FPR plasebo 0,081) |
| Event study p plasebo < 0,05 | 0,053 (390) | 0,05 | tidak lebih sering dari peluang |
| Silhouette maks clustering | 0,184 | p95 plasebo 0,196 | k = 1 |
| `boot_ratio` median h 4 / 8 / 12 | 0,57 / 0,35 / 0,35 | 1 | bootstrap menarik β ke nol (U107) |

Diagnosis: sd(Δ kurs) mingguan 0,0082 membuat sinyal kurs berada di bawah ambang deteksi hampir di semua sel. Nol yang konsisten (LP, event
study, H2, E1, meta-regresi, clustering, Task 4) sah sebagai hasil **asalkan** ditulis sebagai batas atas disertai MDE.

### 3.3 Akurasi arah per komoditas (h 8, semua origin, 2026-11-24; M2/M3 sebelum D-162)

| Komoditas | M1 | M2 | M3 | Baseline mayoritas | Porsi y = 0 |
|---|---|---|---|---|---|
| beras | 0,555 | 0,570 | 0,558 | **0,678** | 0,23 |
| daging sapi | 0,533 | 0,534 | 0,563 | **0,604** | 0,34 |
| gula pasir | 0,511 | 0,547 | 0,617 | **0,604** | 0,15 |
| minyak goreng | 0,508 | 0,597 | 0,531 | **0,616** | 0,14 |
| bawang putih | 0,486 | 0,463 | 0,640 | 0,520 | 0,02 |
| bawang merah | 0,602 | 0,607 | 0,699 | 0,508 | 0,00 |
| cabai merah | 0,574 | 0,581 | 0,564 | 0,522 | 0,01 |
| cabai rawit | 0,631 | 0,646 | 0,628 | 0,516 | 0,00 |
| daging ayam | 0,603 | 0,547 | 0,591 | 0,511 | 0,01 |
| telur ayam | 0,579 | 0,512 | 0,603 | 0,510 | 0,02 |

Selisih vs baseline mayoritas (bootstrap blok origin): M1 +0,017 (−0,023..0,044) / +0,015 (−0,029..0,053); M2 +0,030 / +0,015 (memuat nol);
M3 +0,046 (0,011..0,072) / +0,057 (0,021..0,088). Komoditas kaku (beras, daging sapi, gula, minyak goreng; carry-forward ≥ 50%), h 8: semua model
di bawah baseline (M1 −0,100; M2, M3, TimesFM tidak lolos BH sesudah D-143).

### 3.4 Pelacakan & lineage (D-140, D-144)

- RunRecord schema 3: `code_sha256`, `git_dirty`, `environment`, `evaluator_version`. Eksekusi dipisah dari evaluasi-saja; artefak yang bukan
  output run eksekusi terakhir ditandai "tidak sinkron".
- 13/33 fitur clustering konstan (τ² = 0) dilaporkan sebagai `n_constant_features` / `effective_dimensions` (20 dimensi efektif). D-163 membuktikan
  kolom itu inert (§10.3).
- Keadaan per 2026-11-26 23.00 (CLAUDE.md §2): log task1 hanya dievaluasi; tahap lain dieksekusi & sinkron.

### 3.5 Model eksploratif yang tampil di halaman 7 (D-141, D-142, D-144; h 8, semua origin)

| Model | MAE / M1 (DM p) | Akurasi | Selisih vs baseline 0,545 | F1 makro | MCC | ROC-AUC |
|---|---|---|---|---|---|---|
| M2 | 1,017 (0,006) → 1,013 (D-162) | 0,560 | −0,024..0,049 | 0,549 | 0,104 | 0,572 |
| M3 | 1,015 (0,49) | 0,602 | 0,021..0,088 | 0,594 | 0,192 | 0,627 |
| C1 (klasifier) | – | 0,607 | – | 0,605 | 0,211 | 0,652 |
| C2 (klasifier + kurs) | – | 0,617 → 0,620 (D-162) | 0,034..0,108 → 0,038..0,110 | 0,614 | 0,227 | 0,654 |
| PatchTST (3 seed) | 0,972 ± 0,011 | 0,583 ± 0,016 | 0,008..0,092 (seed 1) | 0,593 | 0,187 | 0,640 |
| TSMixer (3 seed) | 0,966 ± 0,007 | 0,610 ± 0,005 | 0,017..0,103 | 0,604 | 0,209 | 0,641 |
| TSMixer + kurs (3 seed) | 0,995 ± 0,009 | 0,601 ± 0,004 | 0,004..0,100 | 0,598 | 0,195 | 0,644 |
| **TimesFM 3.0** | **0,895 (< 0,001)** | 0,623 | 0,026..0,122 | 0,623 | 0,257 | 0,690 |
| TimesFM 3.0 + kurs | 0,904 (< 0,001) | 0,613 | 0,007..0,119 | 0,611 | 0,255 | 0,696 |

- h 4: TimesFM MAE/M1 0,935 (DM p 0,0001); R² vs ramalan nol 0,19 / 0,25 (M1 0,09 / 0,07). TFM − M3 akurasi +0,043 (0,021..0,064) pada h 4.
- Ablation kurs: C2 − C1 tidak terbukti; TFM_fx / TFM 1,005 / 1,010 (tidak nyata); TSMX_fx / TSMX 1,041 (h 4, DM p 0,020 → q 0,057 sesudah BH)
  / 1,029. **Kurs tidak menambah akurasi di model mana pun.**
- Kontaminasi TimesFM: dirilis ulang Google 2026 dengan korpus pralatih tak diungkap; per tahun origin keunggulan MAE tetap pada 2026 (0,938)
  walau lebih kecil dari 2023–2024 (0,876 / 0,834) → ditulis sebagai **batas atas**. Uji pada seri yang jarang dipublikasikan belum dilakukan.
- Akurasi termasuk minggu tanpa perubahan (dihitung salah): TimesFM 0,566, M1 0,508. Target F1 0,8–0,9 tidak tercapai (terbaik 0,623).

### 3.6 Koreksi multiplisitas (D-143) dan kestabilan (D-144)

| Keluarga | Uji | "Lebih baik/buruk" sebelum | Bertahan setelah BH |
|---|---|---|---|
| Beda akurasi berpasangan | 30 | 5 | 5 → **4 sesudah D-162** (TFM & TFM_fx vs M3 h 4, C1 vs M1 h 4 & 8; C2 vs M3 h 4 gugur) |
| Metrik arah vs acuan | 132 | ± 125 | 123 (M1 & M2 tetap belum terbukti) |
| Rasio MAE model eksploratif | 14 | 5 | 4 (TFM & TFM_fx vs M1, h 4 & 8) |
| Tabel segmen h 8 | 190 | – | 47 lebih baik, 15 lebih buruk |

D-144: kepekaan blok bootstrap 2/3/4/6 origin → 17/17 keputusan sama di kedua horizon; DM lag HAC 1–5 tidak mengubah keputusan (TimesFM vs M1
p < 0,001; M2 vs M1 p 0,006–0,018 sebelum D-162); replikasi 3 seed menunjukkan selisih antarmodel deep ≤ 0,03 berada dalam rentang seed.

### 3.7 Kelemahan halaman 7 yang belum ditutup (Lampiran C.4)

| # | Kelemahan | Status di laporan audit |
|---|---|---|
| C.4 #1 | Semua run sejak D-140 `git_dirty = True`; code hash berubah antar run | tidak ada laporan audit sesudahnya yang mencatat evaluasi bersih pada satu commit |
| C.4 #3 | Task 1 tidak pernah dieksekusi di bawah pelacakan folder ini | tetap (butuh run Kaggle ± 2 jam); Task 4 sudah (D-162) |
| C.4 #8 | Uji binomial (positif palsu plasebo, `share_fx_improves`, tanda V4) menganggap replikasi independen | keterbatasan tertulis |
| C.4 #11 | `deep_preds` tidak dikirim; TimesFM butuh bobot 1,32 GB berlisensi non-komersial | Tingkat A jalan dari log; Tingkat B/C butuh internet & torch |
| C.4 #12 | Server app lokal 8501 basi | menunggu restart oleh pengguna |

---

## 4. Optimasi klasifikasi arah (D-145, D-146)

Sumber: [ronde 1](20261124_task4_optimasi_arah.md), [ronde 2](20261125_task4_ronde2.md).

### 4.1 Protokol (berlaku untuk semua ronde sesudahnya)

- Label: naik bila y = p_{t+h} − p_t > 0, turun bila < 0; **y = 0 dikeluarkan** dari metrik dan latih klasifier (D-139/D-141). Semua perubahan
  kecil tetap dievaluasi.
- Rolling-origin Task 4: origin tiap 4 minggu sejak 2021-01-04, latih hanya t + h ≤ origin, harga dunia as-of `available_at`.
- Seleksi fitur, hyperparameter, threshold hanya di dev; test dibuka setelah konfigurasi beku. Pembanding = prediksi resmi pada baris identik.
  Mesin eksperimen mereproduksi C1 resmi persis (selisih p_up 0,0).
- Implementasi resmi awal hanya punya 7 fitur base (lag Δp 1/4/8, bulan, minggu relatif Idulfitri, Δ Brent 1/4) + 7 kurs + 2 kategori, tanpa
  informasi level harga, lag panjang, atau sinyal lintas provinsi.

### 4.2 Ablation kelompok fitur (dev; tambah-satu di atas C1 resmi 0,584 / 0,597)

| Kelompok | Isi | Tambah-satu h 4 / h 8 | Hapus-satu dari `all` (rerata) |
|---|---|---|---|
| `dev` | deviasi MA13/MA52, posisi rentang 52 minggu, deviasi spasial & perubahannya | **0,630 / 0,641** | 0,6494 |
| `comm` | Δp rerata nasional komoditas 1/4/8, porsi provinsi naik, sd nasional | **0,631 / 0,645** | 0,6466 |
| `lag` | Δp lag 1–3, 13/26/52 minggu | 0,596 / 0,628 | 0,6564 |
| `rmean` | EWM return (paruh 4, 13) | 0,603 / 0,617 | 0,6575 |
| `season` | minggu-dalam-tahun sin/cos, perubahan h minggu 1 & 2 tahun lalu | 0,588 / 0,610 | 0,6492 |
| `rstd`, `mom` | sd return; porsi naik/turun, akselerasi, run tanda | 0,587–0,588 / 0,596–0,601 | 0,6561 |
| `vol`, `cf` | volatilitas; umur & porsi carry-forward | ≈ C1 | **dibuang** (hapus menaikkan skor) |
| `all` / `all + fx` | – | 0,654 / 0,662 · 0,649 / 0,662 | – |

Set terpilih (aturan ditulis sebelum hasil): lag, rmean, rstd, mom, season, dev, comm = 37 fitur + base + identitas.

### 4.3 C1-tuned dan varian (test, kecuali disebut lain)

- **Hyperparameter** (Optuna TPE 40 trial, seed 20261121, objektif rerata macro F1 dev; 84 menit): lr 0,0281, max_iter 250, max_leaf_nodes 23,
  min_samples_leaf 319, l2 3,85, max_features 0,335, tanpa bobot kelas, tanpa peluruhan waktu. Run semua origin 7,8 menit.
- **Threshold**: untuk klasifier terkalibrasi (C1/C1t) threshold dev tidak menambah (C1t h 8 0,674 vs 0,680 pada 0,5); untuk TimesFM (regresi)
  ambang sedikit negatif +0,012 / +0,024 (lolos BH). Kalibrasi residu historis TimesFM setara dengan menggeser threshold.
- **TFM-head** (TimesFM kedua horizon + fitur rekayasa + OOF C1t → CatBoost, dilatih hanya pada origin lampau): 0,672 / 0,676; jauh di atas
  TimesFM mentah (+0,054 / +0,055) tetapi setara C1t → TimesFM tidak menambah informasi di atas fitur rekayasa.
- **TSMixer-tuned** (10 trial, termasuk kepala BCE): nilai tuning 0,593 turun ke 0,584 saat konfirmasi → kenaikan tuning = derau pelatihan.
- Pemangkasan karena waktu (dicatat PARTIAL di registri): C2-tuned 12/25 trial, grid TFM-head, TSMixer 10 trial.
- Porting ke `src/`: `features/price_dynamics.py`, `models/direction.py` (C1t/C2t), `kagami task4 --direction-tuned` → artefak eksploratif
  `direction_tuned_preds`, identik dengan eksperimen.

Per komoditas (test h 8, macro F1):

| Model | bawang merah | bawang putih | beras | cabai merah | cabai rawit | daging ayam | daging sapi | gula | minyak goreng | telur |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 0,706 | 0,666 | 0,475 | 0,557 | 0,618 | 0,536 | 0,525 | 0,657 | 0,481 | 0,485 |
| TimesFM | **0,771** | 0,575 | 0,544 | 0,678 | 0,688 | 0,641 | 0,525 | 0,513 | 0,515 | 0,584 |
| C1-tuned | 0,740 | 0,657 | 0,530 | **0,681** | **0,705** | **0,661** | 0,560 | **0,735** | 0,531 | 0,643 |
| TFM-head | 0,724 | **0,672** | **0,606** | 0,678 | 0,683 | 0,608 | **0,598** | 0,725 | **0,542** | **0,648** |
| C1-tuned h 4 | 0,732 | 0,696 | 0,666 | 0,609 | 0,677 | 0,639 | 0,609 | 0,746 | 0,582 | 0,662 |

Komoditas diatur/kaku (beras, daging sapi, minyak goreng) tetap paling sulit (0,53–0,61); gula naik paling besar (0,513 → 0,735).

### 4.4 Ronde 2 (D-146): diagnosis galat dan kandidat yang ditolak

- **Galat terkonsentrasi pada perubahan kecil**: kuintil |y| h 8 macro F1 0,565 / 0,644 / 0,686 / 0,684 / 0,786; recall turun 0,37 → 0,86.
  Akurasi per kuintil keyakinan |p − 0,5| 0,55 → 0,83. Kelemahan "turun" = penurunan kecil yang tertebak naik.
- **Drift naik di test**: prediksi naik 0,557 / 0,598 vs aktual 0,524 / 0,545 (dijelaskan D-147: rezim komoditas diatur 2024+).
- Fitur ronde 2 (dev, hyperparameter C1t): regulasi HET/HAP −0,002 / −0,005; spasial (tetangga 1/jarak², hub, wilayah) −0,003 / +0,000;
  kalender (Idulfitri ±26, Natal, Ramadan) +0,000 / −0,006; prior porsi naik 104 minggu −0,004 / **−0,016**; level (MA104, z 52) −0,001 / +0,005;
  semua −0,001 / **−0,016**. Acuan regulasi baru aktif 2022-03 (minyak goreng) s.d. 2024-06/09, sehingga sebagian besar baris dev belum punya acuan.
- Model: LightGBM −0,004 / −0,006; XGBoost −0,006 / −0,004; ensemble rata-rata −0,002 / −0,003; spesialis per kelompok −0,010 / −0,015 (p 0,049).
- Dua tahap 3 kelas (HGB "berubah?" → C1t; τ dev 0,67 / 0,70): test 0,625 (0,608..0,641) / 0,606 (0,580..0,627); F1 tetap 0,62 / 0,53.
- TCN/MLP multi-task (Colab T4, 3 seed, refit tiap 4 origin): MLP tabular −0,019..−0,032; TCN deret −0,042..−0,072; TCN + tabular
  −0,027..−0,048 di dev → test tidak dibuka. Percobaan pertama gagal (GPU penuh → CPU) → dicatat FAILED.
- Kesimpulan: 50+ fitur dari histori harga, 5 jenis model, dan spesialis semuanya berhenti di ± 0,66–0,68 (dev); informasi histori harga jenuh.
  Menaikkan skor dengan membuang perubahan kecil = penyederhanaan label (dilarang).

---

## 5. Audit preprocessing & kualitas label (D-147; D-156 fase B)

Sumber: [audit preprocessing](20261125_task4_audit_preprocessing.md), [master F1 §3](20261126_task4_master_f1.md).

### 5.1 Peta pipeline yang diverifikasi

| Tahap | Fakta | Implikasi |
|---|---|---|
| Mentah | harga provinsi sudah diagregasi BI dari kota sampel (110 kota, 1–12 per provinsi); data per pasar tidak ada | kohort pasar tetap tidak dapat dibuat (P02 BLOCKED); yang dapat diaudit = komposisi **hari** dalam minggu |
| Pembersihan | 0 kunci ganda; 5 harga ≤ 0 dibuang; 0 non-bulat; **100% kelipatan Rp50** | presisi sumber = Rp50 |
| Agregasi | rerata hari kerja teramati per minggu ISO; 5 hari = 86%, 4 hari = 10,5%; 60% minggu punya variasi harga dalam minggu (beras 22%, cabai 94%) | satu definisi kalender |
| Missing | sel `missing` (1%) = NaN, tidak diisi; target & `lag_dp_1/4/8` dari harga **teramati**; ffill ≤ 8 minggu hanya di fitur turunan | p_t, p_{t−1/4/8}, p_{t+h} selalu teramati pada baris yang dipakai |
| carry_forward | status saja; 51–59% label punya ≥ 1 ujung cf; akurasi cf→cf 0,67–0,70 ≈ observed→observed 0,64–0,68 | kekakuan nyata (U22), bukan derau |
| Nol sejati | y = 0: 98,6% / 98,4% ujung cf→cf; hilang selalu NaN, tidak pernah 0 | y = 0 dikeluarkan sesuai definisi resmi |
| Fitur | seluruhnya selisih/rasio log; rolling ke belakang tanpa `center`; HGB tanpa scaler/imputer (NaN asli) | transformasi & standardisasi bukan isu |
| Konsistensi | grid 340 seri × 516 minggu lengkap; 10 komoditas = config; semua `week` Senin; y_h & lag dihitung ulang identik | – |

### 5.2 Tick Rp50, label rapuh, dan batas atas derau

- 1 tick = 0,32% (beras), 0,28% (gula), 0,23% (minyak goreng), 0,17% (telur), 0,035% (daging sapi). Karena label = selisih rerata mingguan,
  perubahan < 1 tick hanya dapat muncul dari komposisi hari.
- Label < 1 tick: 2,4–4,3% baris, akurasi 0,51–0,54 (≈ koin). Label < 2 tick terkonsentrasi di komoditas diatur (test h 4: beras 38%, minyak
  goreng 29%, gula 26%).
- Label yang tandanya berbalik bila hari di-resample (bootstrap hari, ≥ 5% replikasi): 10,9% / 7,7% dev, 12,2% / 8,4% test; akurasi 0,50–0,58.
- Representasi minggu lain: tanda label sama dengan versi median 98%, hari terakhir/pertama 94–96%.
- **Batas atas**: pada label ≥ 10 tick (65–72% baris) akurasi C1t hanya 0,68–0,71; pada label stabil 0,69–0,70. Membuang semua label rapuh hanya
  ± +0,01–0,015 (D-147), ± +0,020 / +0,020 bila label stabil & ≥ 2 tick (D-156). **Celah ke 0,8 bukan artefak data.**
- Autokorelasi lag-1 perubahan mingguan positif untuk 9/10 komoditas (0,15–0,42; ± 0,24 = nilai mekanis rerata 5 hari random walk / efek
  Working); tanda `log(hari terakhir) − log(rerata minggu t)` searah label pada 62,6% / 56,8% baris → asal fitur `iw_gap`.

### 5.3 Outlier, kebocoran, ketersediaan, distribusi sampel

- Outlier: 46 lonjakan QA satu hari dalam periode; |Δlog| > 5 × MAD 4.368 sel (1.646 terkonfirmasi lintas provinsi, 460 kandidat galat data).
  Label yang menyentuhnya ≤ 1,4% dengan akurasi rata-rata → tidak ada koreksi yang dijalankan; tidak ada data yang dihapus.
- **P10 kebocoran** (76 origin × 54 kolom; rusak acak semua data sesudah origin dan hapus baris sesudah origin): **0 kolom, 0 sel, 0 target latih
  berbeda**. Flag `episode` (grup kurs) berbeda pada 1/76 origin (2024-12-02) karena episode berdempetan digabung → U108 → diperbaiki D-162.
  Tiga tes regresi ditambahkan ke `tests/test_direction_tuned.py`.
- Ketersediaan fitur C1t: kosong ≤ 1% di test; `range_pos_52 = 0,5` untuk nilai tak terdefinisi (dampak ≈ 0); `idf_rel_week` NaN = jauh dari
  Idulfitri (79% baris).
- **Seimbang-seri**: gabungan 0,677 / 0,680 vs rerata antarseri 0,657 / 0,651; 12–16% seri test < 0,55; provinsi 0,604..0,729; komoditas
  0,567..0,746.
- **Drift naik = pergeseran rezim komoditas diatur**: kelebihan prediksi naik test beras +0,107 / +0,172, minyak goreng +0,145 / +0,142, daging
  sapi +0,152 / +0,094, telur +0,063 / +0,095; dev beras justru −0,086 / −0,136. Porsi prediksi naik komoditas diatur "tertinggal satu rezim"
  dari aktual per tahun (mis. beras aktual 2021–2026 0,48 / 0,78 / 0,81 / 0,52 / 0,67 / 0,82 vs prediksi 0,33 / 0,55 / 0,80 / 0,70 / 0,86 / 0,95).

### 5.4 Eksperimen preprocessing (dev; C1t, label & baris evaluasi tetap)

| ID | Varian | Δ h 4 (interval) | Δ h 8 (interval) | Keputusan |
|---|---|---|---|---|
| P06a / P06b | buang label LATIH < 1 / < 2 tick | −0,003 / −0,004 | −0,003 / +0,000 | tidak |
| P06c | bobot stabilitas label | −0,004 | −0,003 | tidak |
| P03a | latih hanya ujung `observed` (−52% baris) | **−0,017 (−0,031..−0,002)** | **−0,022 (−0,036..−0,008)** | lebih buruk (carry-forward = informasi) |
| P03b | tanpa ffill + NaN jujur + `n_missing_13` | −0,003 | −0,001 | tidak |
| P04a | fitur dari harga hari terakhir (bukan rerata) | +0,001 | −0,002 | tidak |
| **P04b** | + `iw_gap` & `n_days` | **+0,014 (0,004..0,026)** | +0,002 | buka test → +0,004 (q 0,35) / +0,005 (q 0,089), belum terbukti |
| P08 | normalisasi per seri | −0,008 | **−0,011** | lebih buruk |
| P09 | bobot seimbang per komoditas | −0,000 | **−0,009** | lebih buruk |
| B_win156 (D-156) | latih hanya 156 minggu terakhir | **−0,016 (q 0,032)** | **−0,022 (q 0,003)** | lebih buruk |
| B_recency (D-156) | bobot peluruhan paruh 104 minggu | −0,004 | **−0,009** | tidak membantu |

### 5.5 Temuan baru fase B (D-156)

- **Origin hari libur**: 9 / 9 origin dev dengan > 50% seri 4 hari punya bias porsi naik −0,096 / −0,164 (origin normal +0,004 / +0,048). Di dalam
  origin campuran, bias baris 4 hari ≈ baris 5 hari → **efek kalender pada tingkat origin** (sekitar Idulfitri, 17 Agustus, Imlek, Iduladha),
  bukan artefak komposisi hari.
- Revisi harga PIHPS: tidak dapat diukur (vintage tidak tersedia) → BLOCKED (U110); `available_at` konservatif Minggu 00.00.
- Tiga seri cabai rawit (Aceh, Sumbar, Kepri) tidak pernah masuk baris evaluasi dev.

---

## 6. Rezim & kalibrasi temporal (D-148, D-149)

Sumber: [ronde 4](20261125_task4_ronde4.md).

| Kandidat | Isi | Split resmi (dev ≤ 2023): Δ h 4 / h 8 | Split 2 (dev ≤ 2024, pasca-hoc): Δ h 4 / h 8 |
|---|---|---|---|
| `INT_c_13/26` | intercept per komoditas dari prediksi lampau | −0,018 / −0,011 · **−0,037 / −0,042** | lebih buruk |
| `INT_g_13/26` | intercept global | −0,014..−0,010 / −0,006 | −0,007 / −0,005 |
| `PRI_c_26_0.5` | pergeseran prior per komoditas 26 minggu, a = 0,5 | +0,006 (−0,003..0,017) / +0,008 (−0,005..0,024) — interval memuat 0 | +0,000 / +0,000 |
| `R_RB` | base rate terealisasi 13/26 minggu | +0,001 / −0,005 | +0,001 / −0,003 |
| `R_WK` | keseimbangan arah mingguan | −0,003 / −0,004 | −0,001 / −0,004 |
| `R_PO` | umur kebijakan, jumlah kebijakan 104 minggu, jarak ke acuan, perubahan acuan terakhir | −0,004 / −0,008 | −0,004 / **−0,009** |
| `R_ALL` | semua | −0,003 / −0,009 | −0,003 / −0,011 |

- **Mengapa gagal**: dev ≤ 2023 tidak memuat masalahnya (kelebihan prediksi naik komoditas diatur di dev hanya +0,004 / +0,005; fitur kebijakan
  kosong 72–83% di dev). Koreksi berbasis label tertinggal h minggu sehingga mengejar rezim yang sudah lewat; base rate terealisasi bahkan
  memperkuat kelembaman (+0,02..+0,04 prediksi naik).
- **Split 2 (D-149)**: drift dapat dihilangkan, tetapi bukan pembatas skor. `R_PO` menghapus kelebihan prediksi naik komoditas diatur 2024
  (+0,086 / +0,149 → +0,017 / +0,005) dengan biaya −0,009 macro F1 h 8. Baris yang dibalik `R_PO` benar ± 57% di prediksi base, jadi kelebihan
  "naik" adalah **bias proporsi agregat**, bukan kumpulan baris yang salah.
- Kebijakan bertanggal: dari 28 kejadian (komoditas × tanggal berlaku), hanya 4 yang diketahui sebelum berlaku (selisih 1–4 hari) → fitur
  "diumumkan tetapi belum berlaku" selalu 0 pada resolusi mingguan. Acuan beras zona 2/3 2024 tidak tersedia per zona (U6).
- Keputusan D-148: preprocessing baseline **dibekukan**; `iw_gap` disimpan sebagai varian eksploratif `C1t_iw` (prediksi lokal
  `data/interim/c1t_intraweek_preds.parquet`, tidak di `src/`); job > 1 jam dijalankan di Colab T4 dengan output ke Drive terpusat.

---

## 7. Sumber data baru & informasi eksternal (D-150–D-152, D-157–D-161, D-165)

### 7.1 Tabel induk semua sumber yang diaudit

Gerbang (D-159, D-160, D-165): **G1** riwayat mencakup dev (latih ≥ 2020 + nilai 2021–2023) · **G2** waktu ketersediaan (dan vintage) dapat
ditetapkan · **G3** independen dari harga PIHPS · **G4** cakupan cukup untuk menggerakkan macro F1 keseluruhan · **G5** sinyal arah nasional
**tambahan** di atas konsensus C1t (walk-forward, increment-only; lolos bila ΔAUC ≥ +0,01 di kedua horizon, batas bawah > 0 di ≥ 1 horizon,
q < 0,05).

| Sumber | Keputusan | Diperoleh? | Hasil kunci | Status |
|---|---|---|---|---|
| PIHPS pedagang besar (`pihps_wholesale`, opsional) | D-150 | ya, 34 prov, 3.978 permintaan, 0 galat | kaku (cf 85–98%), bergerak bersama/sesudah eceran; dev −0,006..+0,001 | ditolak |
| PIHPS produsen (`pihps_producer`, opsional) | D-151 | ya, 3.570 permintaan, 0 galat; DKI kosong | tangga mingguan; eceran mendahului produsen; dev −0,006..−0,001 | ditolak |
| Informasi intraminggu (`pihps_daily`) | D-147, D-151, D-152, D-158 | sudah ada | `IW_NAT` dev +0,020 / +0,005; test +0,0085 / +0,0033 (q 0,28 / 0,30) | **belum terbukti; menunggu prediksi maju** |
| PIHPS 110 kota (`pihps_city`, opsional) | D-158 | ya, 12.870 permintaan, 0 galat, 3,9 MB | breadth tidak memprediksi arah nasional; kontribusi kota di atas intraminggu ≈ 0 | ditolak |
| Bapanas panel kab/kota | D-158 | tidak (portal tanpa tabel; SAPA terbatas) | – | BLOCKED (U111) |
| Bapanas panel produsen (GKP, jagung, ayam hidup, dll.) | riset 11-25 | tidak (reCAPTCHA, SAPA "All Rights Reserved") | isi ekonomi paling relevan; bulanan B+1 | BLOCKED |
| NASA POWER cuaca (`nasa_power`, opsional) | D-157 | ya, 34 titik 2016–2026, 3,6 MB | W_NAT −0,003 / −0,003; W_LOC +0,002 / −0,003; koreksi walk-forward −0,003 / −0,005 | ditolak |
| Realisasi impor bulanan (Comtrade + BPS) | D-157 | sudah ada | −0,006 / **−0,015** (q 0,017, lebih buruk) | ditolak |
| SP2KP stok & pasokan mingguan (Kemendag) | D-159, D-165 | tidak: area admin berlogin | data ada (mingguan, ekspor Excel) | BLOCKED (U112) |
| FDP Bapanas | D-159 | baca-saja | log program stabilisasi (39 pengiriman 2026), seri mulai 2024 | ditolak |
| PIBC Cipinang (Food Station) | D-159 | baca-saja | endpoint publik 1 rekaman (Jun 2025); portal tidak diperbarui | BLOCKED |
| GPM Bapanas | D-159 | baca-saja | bulanan 2024+ tanpa tanggal kegiatan; kausalitas terbalik | ditolak |
| KSA BPS (luas panen padi) | D-159 | baca-saja | hanya beras; nilai potensi ditimpa; informasi beras sempurna ≤ +0,007 | ditolak |
| SIJAGUNG (`ditjenpkh_sijagung`, opsional) | D-160 | ya, 2 xlsx 74 KB | baris \|ρ\| ≤ 0,11 (q ≥ 0,65); arah nasional AUC −0,01..−0,21 vs konsensus | ditolak |
| SPORA (harga pakan) | D-160 | tidak: ekspor HTTP 500 (memori PHP server) | – | BLOCKED |
| BNPB DIBI | D-160, D-165 | baca-saja | bencana dominan = cuaca ekstrem (mekanisme tertutup D-161); verifikasi triwulanan | ditolak (prioritas) |
| NOAA CFSv2 prakiraan | D-160, D-161 | ya, lewat Colab: 437/465 minggu | skill prakiraan nyata (hujan 1–28 r 0,42–0,55) tetapi ΔAUC −0,029..+0,006; **oracle cuaca terealisasi juga gagal** | ditolak |
| GDELT GKG Translingual | D-160, D-165 | ya, pilot 48 batch + BigQuery sandbox 313,83 GB | G1–G2 ✓; presisi penyaring 0,72; G5 ΔAUC −0,008..+0,001 (q ≥ 0,46) | ditolak; U113 ditutup |
| GDELT DOC API | D-165 | HTTP 429 menetap | – | BLOCKED |
| Proyeksi Neraca Pangan (Bapanas) | D-165 | tidak: semua dataset *Terbatas*; vintage bulanan baru sejak Sept 2024 | mekanisme baru paling masuk akal | BLOCKED (U112) |
| Luas tanam & EWS hortikultura (Kementan) | D-165 | tidak: tanpa portal publik | mekanisme berbeda dari cuaca (tanam 2,5–4 bulan sebelum panen) | BLOCKED (U112) |
| NDVI satelit | D-165 | butuh akun Earthdata/GEE | prior rendah (digerakkan cuaca) | BLOCKED |
| Tanggal pengumuman HET/HAP | D-165 | sudah ada (`regulation.csv`) | 11 peristiwa di dev → ≤ 3% minggu tersentuh | ditolak (G4) |
| Harga BBM bersubsidi | D-165 | publik | 1 peristiwa di dev | ditolak |
| Google Trends | D-165 | – | tidak reproduktif, reaktif terhadap harga | ditolak |
| Stok Bulog / SPHP / bansos | D-165 | sebagian, terbatas | beras saja (≤ +0,007) | ditolak |
| Gangguan pelabuhan/penyeberangan | D-165 | tidak ada seri terstruktur | tercakup kategori gangguan GDELT | ditolak |
| Info Pangan Jakarta | riset 11-25 | – | eceran satu provinsi | tidak relevan |

### 7.2 Keluarga intraminggu (D-147, D-151, D-152)

- **Fitur** (Senin–Jumat minggu origin t saja): `iw_gap` = log hari terakhir − log rerata minggu; `iw_return`; `iw_range`; `iw_vol`; `iw_n_days`;
  `iw_last_age`; versi nasional `iw_gap_nat`, `iw_return_nat` (rerata provinsi yang teramati). Kosong 1,1%.
- **Dev** (D-151): `IW_REF` (`iw_gap` + `n_days`) +0,014 / +0,002; `IW_FULL` (6) +0,015 / +0,002; **`IW_NAT`** (8) +0,020 (0,003..0,037) /
  +0,005; kuintil |y| terkecil +0,027 / +0,019 (interval > 0). Yang menambah adalah **versi nasional** (perubahan dalam minggu yang serentak).
- **Test sekali** (tidak bersih karena `iw_gap` sudah dilihat di D-147): `IW_NAT` 0,686 / 0,683; ROC-AUC 0,758 / 0,746 vs 0,741 / 0,738.
- **Validasi D-152** (protokol beku, tanpa kandidat baru):

| Uji kebocoran per cutoff (83 origin + 2 data penuh) | Diuji | Lolos |
|---|---|---|
| semua observasi sesudah cutoff dihapus | 84 | 84 |
| harga sesudah cutoff dirusak ×exp(N(0; 0,5)) | 84 | 84 |
| 30% observasi sesudah cutoff dihapus acak | 84 | 84 |
| hanya provinsi lain dirusak (fitur nasional/LOO) | 84 | 84 |
| Jumat minggu origin dirusak → fitur tanpa Jumat tetap | 84 | 84 |
| kontrol positif: Jumat dirusak mengubah `iw_gap` | 84 | 84 |

| Diagnostik dev | Δ vs C1t h 4 / h 8 | Δ vs `IW_NAT` h 4 / h 8 | Bacaan |
|---|---|---|---|
| `IW_NAT_LOO` (tanpa provinsi sendiri; r 0,998 dengan rerata) | +0,024 / +0,006 | +0,005 (0,000..0,009) / +0,001 | sinyal dari provinsi lain; ± 0,005 = derau pelatihan HGB |
| `IW_BREADTH` (porsi provinsi naik/turun) | +0,023 / +0,001 | +0,003 / −0,004 | keserentakan tidak menambah |
| `IW_NAT_NOFRI` (Senin–Kamis) | +0,010 / +0,001 | **−0,010 (−0,018..−0,001)** / −0,004 | separuh keuntungan h 4 dari harga Jumat (nowcast level); kuintil kecil tetap +0,026 |

- Selisih C1t vs IW_NAT (D-155): arah berbeda pada 12% (h 4) / 7–8% (h 8) baris; test h 4 diperbaiki 721 vs dirusak 629 (bersih +92), h 8 425 vs
  393 (+32) → keuntungan adalah selisih kecil dari banyak pembalikan yang hampir saling meniadakan.
- **Daya**: SE selisih test 0,0068 / 0,0037; MDE test 0,019 / 0,010; MDE batch maju 0,08–0,12 / 0,04–0,06; mendeteksi +0,0085 / +0,0033 butuh
  ± 185 / 355 origin berjarak 4 minggu (± 14 / 27 tahun) → validasi maju hanya **penjaga kegagalan besar**.
- Eksplorasi keluarga intraminggu di dev **dihentikan**; test 2024+ tidak dibuka lagi untuk keluarga ini (EKSPERIMEN §4).

### 7.3 Grosir & produsen PIHPS (D-150, D-151)

| Komoditas | cf grosir | log grosir − eceran | corr Δgrosir(t−1)→Δeceran(t) | corr Δeceran(t−1)→Δgrosir(t) | log eceran − produsen | Δprod(t−1)→Δeceran(t) | Δeceran(t−1)→Δprod(t) |
|---|---|---|---|---|---|---|---|
| beras | 0,983 | −0,071 | 0,111 | 0,159 | 0,17 | 0,057 | 0,062 |
| gula pasir | 0,948 | −0,097 | 0,321 | 0,364 | 0,14 | 0,113 | 0,129 |
| minyak goreng | 0,952 | −0,095 | 0,095 | 0,414 | 0,18 | 0,085 | 0,214 |
| daging sapi | 0,928 | −0,060 | −0,063 | 0,193 | 0,09 | −0,011 | 0,021 |
| daging ayam | 0,913 | −0,178 | 0,068 | 0,536 | 0,34 | −0,020 | 0,198 |
| telur ayam | 0,944 | −0,094 | 0,236 | 0,506 | 0,13 | 0,009 | 0,212 |
| bawang merah | 0,938 | −0,241 | 0,366 | 0,528 | 0,41 | 0,047 | 0,214 |
| bawang putih | 0,944 | −0,228 | 0,220 | 0,459 | 0,84 (2 prov) | 0,020 | 0,014 |
| cabai merah | 0,931 | −0,234 | 0,067 | 0,538 | 0,47 | 0,028 | 0,174 |
| cabai rawit | 0,846 | −0,195 | 0,266 | 0,629 | 0,38 | −0,022 | 0,193 |

- Grosir: `W_DP` −0,006 / −0,002; `W_GAP` −0,006 / −0,002; `W_ALL` +0,001 / −0,002 (semua interval memuat 0). Arah grosir 4 minggu sedikit lebih
  cocok dengan arah eceran ke depan untuk komoditas diatur (beras 0,650 vs momentum 0,614), tetapi sudah terwakili momentum & sinyal nasional C1t.
- Produsen: seri = tangga mingguan (88% minggu satu nilai harian; harga berubah 4% hari, 34% hari Senin; lompatan besar: cabai median |Δlog|
  0,22–0,23); cakupan tipis untuk gula (11 prov), minyak goreng (14), bawang putih (2). `PR_DYN` −0,002 / −0,003; `PR_TRANS` −0,003 / −0,004;
  `PR_ALL` −0,001 / −0,006.
- **Jalur "harga hulu PIHPS" untuk arah eceran ditutup.** FAQ PIHPS: 2 pasar per kota, 2 pedagang panel per komoditas; saat bencana data hari itu
  diambil dari hari sebelumnya (sebagian carry-forward adalah isian BI); terbit 13.00 WIB, revisi s.d. hari berikutnya. Tombol "Download" resmi
  mengekspor grid dari endpoint `GetGridDataDaerah` yang sama (bukti untuk U19; konfirmasi akhir `[HUMAN]`).

### 7.4 Ruang (headroom) informasi nasional & cuaca/impor (D-157)

| Informasi sempurna arah nasional per komoditas × origin (LOO) | Δ macro F1 h 4 / h 8 |
|---|---|
| Semua komoditas | **+0,105 / +0,105** |
| Hortikultura saja | +0,049 / +0,042 |
| Kelompok impor | +0,024 / +0,028 |
| Pakan (ayam, telur) | +0,027 / +0,017 |
| Beras saja | +0,002 / +0,007 |

- Fitur cuaca: Σ porsi produksi ATAP × anomali baku (klimatologi DOY ± 10 hari 2016–2020) untuk cabai merah, cabai rawit, bawang merah; lag ≥ 7
  hari; porsi ATAP tahun Y sejak 1 Juli Y+1. Impor: yoy3, mom3, dev12, nilai satuan, `available_at` = akhir bulan + 45 hari. Kebocoran 0 sel.
- Layar DU: `wn_z_tmax_28` ρ parsial +0,136 / +0,174, `wn_z_rain_91` −0,090 / −0,161, bertanda sama di setiap tahun dev, tetapi interval lebar
  (variasi hanya antar 37 origin × 3 komoditas).
- Modeling: W_NAT −0,003 / −0,003; W_LOC +0,002 / −0,003; IMP −0,006 / **−0,015** (beras −0,040 / −0,048, daging sapi −0,051 h 4); koreksi logit
  pasca-hoc W_CAL −0,003 / −0,005 (hortikultura −0,009 / −0,016; Brier juga memburuk). Koefisien suhu bertanda benar tetapi sd sebesar reratanya.
- Pelajaran: korelasi residual pooled untuk sinyal tingkat nasional bersifat in-sample → wajib koreksi walk-forward berparameter kecil (EKSPERIMEN §3).

### 7.5 National shock nowcasting & breadth kota (D-158)

- **Iterasi 1** (rekomendasi Danen): NL1 (tahap 1 HGB share_up nasional) −0,002 / −0,003; NL2 (+ kepengikutan provinsi) −0,003 / +0,003;
  NL_BR −0,000 / +0,001; BR_NAT (9 fitur breadth kota) −0,006 / −0,008; BR_LOC −0,005 / −0,006 → 0/5 lolos.
- **Kelemahan iterasi 1** (analisis agent, dev):
  - W1: 76% / 78% provinsi searah mayoritas nasional terealisasi; prediksi semua provinsi dengan mayoritas sejati → **0,756 / 0,782**. Akurasi arah
    nasional tersirat C1t hanya 0,666 / 0,703 (0,763 / 0,800 saat yakin; 0,568 / 0,605 saat ragu). **Konsensus C1t** (rerata p_up provinsi) adalah
    prediktor arah nasional terbaik: AUC mingguan 0,762 / 0,755 vs model nasional terpisah 0,760 / 0,734, kalibrasi logistik + dummy komoditas
    0,742 / 0,698, kota pemimpin −0,03..−0,04.
  - W2: satu-satunya informasi baru dari kota adalah **kesegaran** (harga akhir minggu); `kb_up_1` turun dari 0,087 ke 0,047 bila dikontrol `iw_gap`.
  - W3: banyak fitur lemah = derau. W4: menyusutkan baris ragu ke konsensus merusak (blending α 0,75 / 0,5 / 0 → 0,653 / 0,646 / 0,625).
- **Iterasi 2**: koreksi nasional increment-only META_FR +0,009 / −0,004, META_CITY +0,010 / −0,005, META_IW (acuan) +0,009 / +0,002; FR_REF
  (C1t + `iw_gap` + `iw_gap_nat`, acuan) **+0,024 (0,008..0,041)** / +0,004; FR_CITY (+ 4 fitur kota) **+0,024 (0,006..0,043) / +0,008
  (0,000..0,015)** lolos aturan, tetapi **FR_CITY − FR_REF = −0,000 / +0,004 (p 0,86 / 0,18)** → kenaikan = keluarga intraminggu yang sudah dikenal,
  angka dev optimistis (seleksi berulang). BR1 −0,001 / −0,001.
- Keputusan: C1t tetap; FR_CITY tidak diadopsi; base/FR_REF/FR_CITY dibekukan sebagai prediksi maju (§16).

### 7.6 Pasokan fisik (D-159) dan audit ulang pasokan (D-165 Workstream C)

- SP2KP: portal publik hanya harga; kode aplikasi memuat rute admin "Stok Mingguan Bapok", "Survey Stock Pasar Induk", "Pasokan Pasar Induk" dan
  ekspor Excel mingguan/bulanan → data ada, mingguan, hanya untuk pengguna berlogin. Tidak dicoba diakses.
- Spesifikasi permintaan resmi (U112): stok & pasokan mingguan per pasar/kab-kota 10 komoditas 2018-01 s.d. sekarang, dengan tanggal periode,
  tanggal input, tanggal verifikasi/penutupan, lokasi, komoditas & varian, stok, pasokan masuk, kode kosong, perubahan cakupan pasar.
- D-165 menambah dua mekanisme yang paling masuk akal: **Proyeksi Neraca Pangan** (Bapanas; ± 30 dataset, semua *Terbatas*; versi "Final" 2022–2023
  ex-post; vintage bulanan sejak Sept 2024) dan **luas tanam & EWS hortikultura** (Kementan; prediksi produksi & surplus/defisit cabai & bawang merah
  3 bulan ke depan; tanpa portal). Keduanya hanya cocok untuk **evaluasi prospektif** bila akses diberikan; tidak ada backfill.
- Rekomendasi: satu surat permintaan data resmi gabungan (SP2KP + Proyeksi Neraca Pangan + luas tanam/EWS), protokol prospektif beku sebelum data
  diterima.

### 7.7 CFSv2 (D-160 → D-161)

- Ekstraksi Colab: run 00Z Jumat minggu t (cadangan Kamis/Rabu), byte-range 56 hari pertama `prate` & `tmax` dari `fileServer` NCEI (± 7 MB per
  variabel per run), dekode JPEG2000 dengan eccodes, 182 sel Gaussian T126 → provinsi; 1.818 dtk; 437/465 minggu (28 HTTP 404, 3 di dev).
  Agregat `20261126_sumber_baru/hasil/cfsv2_province_weekly.csv` (14.858 baris), bukan sumber terdaftar.
- Uji: anomali terhadap klimatologi prakiraan ≤ 2020, nasional tertimbang ATAP, increment-only di atas konsensus C1t (AUC 0,707 / 0,714):

| Set | CFSv2 ΔAUC h 4 | CFSv2 h 8 | Oracle (NASA POWER terealisasi) h 4 | Oracle h 8 |
|---|---|---|---|---|
| R1 hujan hari 1–28 | −0,014 (−0,026..−0,002) | −0,003 | −0,028 | −0,013 |
| R2 hujan hari 29–56 | +0,006 | −0,000 | −0,019 | −0,017 |
| RX hujan 1–56 + harian maks | −0,013 | −0,005 | −0,040 | −0,029 |
| T suhu maks 1–28 & 29–56 | −0,003 | +0,005 | −0,027 | −0,015 |
| ALL (6) | −0,026 | −0,029 | **−0,081** | **−0,071** |

- Kesimpulan: skill prakiraan nyata, tetapi bahkan cuaca **yang benar-benar terjadi** 1–8 minggu ke depan tidak menambah informasi arah nasional →
  kegagalan karena **mekanisme**, bukan skill. Aturan baru: sumber prakiraan diuji oracle-nya dulu sebelum biaya ekstraksi.

### 7.8 GDELT (D-160 → D-165)

- Akses: DOC API HTTP 429 di semua percobaan (jeda s.d. 3,5 jam); berkas GKG 15 menit dapat diunduh; berita berbahasa Indonesia ada di aliran
  **Translingual** (`srclc:ind`), bukan Inggris; seluruh 2019–2023 ± 1,5 TB zip → hanya pilot. BigQuery sandbox (tanpa billing, kuota 1 TiB/bulan).
- Pilot 48 batch acak (409 MB): 130 artikel Indonesia/batch (± 12.500/hari); judul halaman 2019 hanya 0,29 (≥ 0,99 sejak 2020); `DATE` vs tanggal
  terbit di URL median 0, maks 1 hari (G2 ✓).
- Validasi manual 111 kandidat (dari judul/slug): presisi relevan F0 0,23 → F1 (batas kata) 0,27 → **F2d (kata kunci pasokan/kebijakan + dedup
  judul per hari) 0,72**; recall F2 kehilangan 6/24; salah cocok substring 18% ("beras" di *berasal*, "pangan" di *lapangan*); 33% artikel relevan
  hanya "bahan pokok" umum; komoditas relevan terbanyak minyak goreng 9, beras 8 → G3 & G4 sebagian.
- Kueri BigQuery (proyek `kagami-gdelt`, tanpa akun billing; teks kueri diverifikasi sha256 sebelum jalan; job 16,6 dtk, 313,83 GB, biaya 0):
  1.836 hari 2018-12-22..2023-12-31, median 7.811 artikel Indonesia/hari.

| Set praregistrasi | ΔAUC h 4 (interval) | ΔAUC h 8 (interval) | q h 4 / h 8 |
|---|---|---|---|
| V volume | −0,003 (−0,009..+0,001) | −0,003 (−0,006..+0,000) | 0,46 / 0,46 |
| D gangguan | −0,004 (−0,015..+0,003) | −0,000 (−0,003..+0,002) | 0,47 / 0,85 |
| P kebijakan | −0,001 (−0,004..+0,000) | −0,004 (−0,012..+0,002) | 0,46 / 0,58 |
| S stabilisasi + pasokan | +0,001 (−0,007..+0,005) | −0,003 (−0,005..+0,002) | 0,90 / 0,58 |
| ALL | −0,005 (−0,020..+0,005) | −0,008 (−0,016..+0,003) | 0,47 / 0,47 |
| *kontrol positif `iw_gap_nat`* | *+0,015 (−0,002..+0,030)* | *−0,004 (−0,023..+0,008)* | *tidak lolos G5* |

- **GDELT REJECTED**: titik estimasi ≤ 0 di 9/10 sel, jauh di bawah kontrol positif; berita pangan sebagian besar mengikuti harga, peristiwa ex-ante
  (kebijakan dagang) terlalu jarang. **Temuan metode**: layar G5 (MDE ± 0,023 AUC) tidak meloloskan sinyal tambahan terbaik yang pernah diketahui, jadi
  "gagal G5" berarti "tidak lebih kuat dari kesegaran intraminggu", bukan "tanpa informasi". Ambang tidak dilonggarkan.

---

## 8. CRISP-DM: Data & Business Understanding (D-153–D-155)

Sumber: [Data Understanding](20261125_crisp_du.md), [Business Understanding](20261125_business_understanding.md), alur [`docs/EKSPERIMEN.md`](../EKSPERIMEN.md).

### 8.1 Data Understanding tiga arah (dev; residual C1t r = 1[y > 0] − p_up)

Kontrol: positif `iw_gap` ρ 0,132 / 0,099, `iw_return_nat_loo` 0,123 / 0,115; negatif (derau, `lag_dp_4`) ≈ 0.

| Arah | Uji | Hasil | Keputusan |
|---|---|---|---|
| K1 asosiasi temporal lintas komoditas (90 pasangan × 2 skala × 2 h = 360 uji) | momentum 4 minggu A → residual B | 0/360 lolos BH (q min 0,18); beras → minyak goreng kuat 2021–2022 (−0,36) lalu hilang 2023 (+0,06) = co-trend krisis; hanya gula → cabai merah stabil (sesuai peluang) | tidak lanjut Modeling; **bukan** sequential pattern mining (D-155) |
| K2 clustering karakteristik seri (5 fitur 2018–2020, K-Means) | tipe vs skill di luar komoditas | 5 tipe (silhouette 0,344; ARI vs komoditas 0,31): sangat kaku (23), kaku persisten (63), sangat volatil (67), kaku berbalik (53), volatil sedang persisten (132). Setelah diganti **skill** vs laju-dasar, karakteristik tidak menjelaskan galat (p 0,33–0,61); 25–27% seri tidak lebih baik dari laju-dasar in-sample | Knowledge Presentation saja; silhouette datar 0,331–0,344 untuk k 2..6 (D-155) |
| K3 graf antarprovinsi (geografis 3 tetangga; korelasi 2018–2020) | sinyal tetangga − nasional LOO, di-*partial* terhadap `iw_gap`, `iw_return`, nasional | ρ sisa 0,021–0,025 (h 8 q 0,043; h 4 q 0,07–0,11) = ± 1/5 kontrol positif | GNN tidak dijalankan; graf = proksi (D-155) |

### 8.2 Business Understanding (D-154; kriteria ditulis sebelum ukur)

- Pengguna: TPID provinsi. Keputusan: menyiapkan operasi pasar/SPHP, kerja sama antardaerah, pemantauan stok, komunikasi 4–8 minggu sebelum kenaikan
  material. Praktik pembanding (asumsi, **belum divalidasi pengguna**): membaca tren sendiri `R_mom`, tren nasional `R_nat`, posisi terhadap MA13
  `R_rev`, pola tahun lalu `R_seas`.
- Kenaikan material = y_h ≥ P80 |y_h| baris latih komoditas (walk-forward). Ambang median test h 4 / h 8: beras 1,6% / 2,6%, daging sapi 1,4% / 2,1%,
  minyak goreng 2,3% / 3,8%, gula 2,7% / 5,0%, telur 8,3% / 11,2%, bawang putih 10% / 16%, ayam 12% / 16%, bawang merah 23% / 37%, cabai merah 37% / 57%,
  cabai rawit 50% / 72%.

| Kriteria | Dev h 4 | Dev h 8 | Test h 4 | Test h 8 |
|---|---|---|---|---|
| S1 presisi daftar pantau − aturan naif terbaik (dev) | lolos +0,110 (0,055..0,151) | lolos +0,067 (0,027..0,129) | lolos +0,094 (0,055..0,132) | lolos +0,072 (0,034..0,115) |
| S2 Brier skill > 0 & ECE ≤ 0,05 | lolos 0,133 / 0,035 | **gagal tipis** 0,160 / 0,056 | lolos 0,170 / 0,010 | lolos 0,167 / 0,021 |
| S3 arah saat bergerak material vs tanda tren | 0,777 vs 0,541 | 0,797 vs 0,502 | 0,809 vs 0,496 | 0,812 vs 0,443 |
| S4 selektif 25% / 50% (akurasi) | – | – | 0,829 / 0,766 | 0,808 / 0,765 |

Presisi V1-K2 (2 komoditas/provinsi) test: C1t 0,179 / 0,161; `R_mom` 0,085 / 0,079; `R_nat` 0,091 / 0,089; `R_rev` 0,113 / 0,121; `R_seas` 0,095 / 0,099;
acak 0,088 / 0,089. Kepekaan vs `R_rev` (terbaik di test): +0,066 (0,033..0,101) / +0,041 (0,003..0,078). **Pembanding laju-dasar komoditas tidak ada
di D-154 → koreksi D-164 (§11.4).**

### 8.3 Adendum audit D-155 (universe, anggaran, tafsiran)

- **Universe S1 valid**: kandidat = semua seri dengan fitur lag pada origin, termasuk y = 0 (dev 1.832 / 1.154, test 1.803 / 1.132) dan 4 baris dev
  tanpa target (kini ikut, dihitung tidak kena; presisi tidak berubah).
- Anggaran pemantauan (test; tidak ada K yang dipilih):

| Kebijakan | Alarm/origin | Presisi h 4 / h 8 | Recall h 4 / h 8 | Alarm palsu/origin | Provinsi beralarm |
|---|---|---|---|---|---|
| V1-K1 | 34 | 0,207 / 0,181 | 0,24 / 0,21 | 27 / 28 | 34 |
| V1-K2 (S1) | 68 | 0,179 / 0,161 | 0,41 / 0,36 | 56 / 57 | 34 |
| V1-K3 | 102 | 0,158 / 0,147 | 0,54 / 0,50 | 86 / 87 | 34 |
| V2-10% nasional | 34 | 0,225 / 0,200 | 0,26 / 0,23 | 26 / 27 | 25,7 / 25,6 |
| V2-setara nasional | 68 | 0,188 / 0,169 | 0,43 / 0,38 | 55 / 57 | 32,5 / 32,3 |

- 58% / 56% alarm test (46% / 40% dev) jatuh pada beras, gula, minyak goreng, daging sapi, yang ambang materialnya hanya 1,4–2,7% (h 4) →
  materialitas statistik ≠ materialitas kebijakan.
- Usulan kartu K4 "risiko kenaikan material" (dijalankan D-164, §11).

---

## 9. Master macro F1 (D-156)

Sumber: [20261126_task4_master_f1.md](20261126_task4_master_f1.md) (protokol beku; 89 menit main + 5 menit combo; 75 pekerjaan).

### 9.1 Analisis galat C1t (dev)

| h | macro F1 | F1 naik | F1 turun | MCC | AUC | naik aktual / prediksi |
|---|---|---|---|---|---|---|
| 4 | 0,656 (0,627..0,684) | 0,668 | 0,644 | 0,313 | 0,710 | 0,527 / 0,507 |
| 8 | 0,676 (0,641..0,706) | 0,702 | 0,650 | 0,352 | 0,724 | 0,542 / 0,538 |

- **Galat ditentukan waktu, bukan lokasi**: sd macro F1 antarorigin 0,092 / 0,084 (rentang 0,42–0,80; 41–42% origin < 0,6) vs antarprovinsi 0,030 /
  0,018. Origin terburuk = bias base rate satu origin (2022-05-23 h 4: naik aktual 0,60, prediksi 0,11).
- Per komoditas 0,590 (cabai merah h 4) .. 0,739 (telur h 8); bias porsi naik terbesar telur −0,09 / −0,11, gula h 8 +0,11, beras −0,09 / −0,14.

| Kuintil \|y\| (dev) | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| median \|y\| h 4 / h 8 | 0,45% / 0,65% | 1,6% / 2,3% | 3,9% / 5,3% | 8,5% / 11,5% | 24% / 33% |
| macro F1 h 4 / h 8 | 0,573 / 0,553 | 0,636 / 0,643 | 0,666 / 0,676 | 0,704 / 0,755 | 0,697 / 0,747 |
| ROC-AUC h 4 / h 8 | 0,602 / 0,561 | 0,669 / 0,663 | 0,722 / 0,720 | 0,766 / 0,804 | 0,771 / 0,823 |

- FP dan FN berbagi profil: |y| median 2,5–4,2%, keyakinan rendah, label rapuh 10–16%; komoditas diatur 26–35% galat. Kalibrasi: h 8 kurang yakin di
  sekitar 0,5; keduanya terlalu yakin di ekor (p > 0,9 → aktual 0,76–0,78).

### 9.2 Dekomposisi sumber galat

| Sumber | Ukuran h 4 / h 8 | Bacaan |
|---|---|---|
| Threshold global (oracle hindsight) | +0,000 / +0,006 | bukan bottleneck |
| Threshold per komoditas (oracle) | +0,011 / +0,009 | kecil, batas atas |
| **Bias base rate per origin** (oracle threshold per origin) | **+0,035 / +0,024** (per origin × komoditas +0,12 / +0,11, overfit) | terbesar, hanya diketahui sesudahnya |
| Label rapuh (label stabil & ≥ 2 tick, 84% / 89% baris) | +0,020 / +0,020 | batas atas bila semua label rapuh derau |
| **Informasi pada perubahan kecil** | AUC Q1 0,60 / 0,56 vs Q5 0,77 / 0,82; Q1 30% / 21% < 1 tick, 67% / 71% komoditas diatur; F1 label Q1 stabil 0,587 / 0,578 | skor peringkat lemah, bukan threshold |
| Peringkat dalam origin × komoditas | AUC 0,670 / 0,694 vs pooled 0,710 / 0,724 | sebagian AUC pooled = membedakan komoditas/origin |

### 9.3 Kandidat (27, semua ditolak; test tidak dibuka)

| Fase | Kandidat | Δ h 4 | Δ h 8 | Catatan |
|---|---|---|---|---|
| C fitur | A momentum / B volatilitas / C posisi / D1 kualitas panel / D2 cakupan hari / E lintas provinsi LOO / F kalender Iduladha-Natal-Ramadan / G interaksi | −0,006..+0,001 | −0,004..+0,003 | 40 kolom, kebocoran 0 sel (12 origin); tidak ada yang lolos layar DU; konkordansi DU–Modeling 8/8 (tidak ada negatif palsu gerbang) |
| C gabungan | C_COMBO (keluarga dipilih di dev-awal < 2022-07, dinilai dev-akhir) | +0,002 | −0,012 | keluarga dev-awal tidak bertahan |
| C hapus-satu | comm / dev / rmean / season / rstd / lag / mom | −0,020 / −0,004 / −0,006 / −0,008 / −0,003 / +0,002 / −0,001 | −0,014 / −0,008 / −0,006 / −0,004 / −0,005 / −0,001 / +0,001 | `comm` paling penting; set C1t tidak diubah |
| D klasifikasi | threshold walk-forward global / per komoditas / bobot kelas / rerata 5 seed | −0,005 / −0,002 / +0,001 / −0,000 | −0,003 / **−0,020** / −0,006 / +0,002 | threshold masa lalu tidak memperbaiki origin berikutnya |
| B latih | jendela 156 minggu / peluruhan waktu | −0,016 / −0,004 | −0,022 / −0,009 | non-stasioneritas tidak diperbaiki dengan memotong riwayat |
| E model | LightGBM / XGBoost / CatBoost / ExtraTrees / logistik | −0,003 / −0,005 / −0,007 / −0,008 / −0,031 | −0,002 / −0,013 / −0,009 / −0,022 / −0,057 | boosting setara (AUC hampir sama); hubungan non-linear penting |

Aturan "lebih baik secara berarti" (lebih ketat dari EKSPERIMEN §4): + q BH < 0,05; Δ ≥ 0 di ≥ 2 dari 3 tahun dev dan porsi origin Δ > 0 ≥ 0,5 di
kedua horizon; F1 naik & turun tidak turun > 0,01; tidak ada komoditas turun > 0,03 di kedua horizon. Hanya 2/54 sel kuintil-kecil yang
intervalnya > 0 (volatilitas h 8 +0,013; 5 seed h 8 +0,006), tanpa koreksi multiplisitas.

---

## 10. Penutupan kelemahan tercatat (D-162, D-163, D-163a)

Sumber: [20261126_kelemahan_tercatat.md](20261126_kelemahan_tercatat.md), [20261126_kalibrasi_pantau.md](20261126_kalibrasi_pantau.md).

### 10.1 U108 — flag `episode` real-time (D-162, perbaikan bug)

- `data.drivers.realtime_episode_flag`: flag minggu t = 1 bila t sendiri minggu pemicu (Σ de 8 minggu s.d. t ≥ 0,03) = identik dengan deteksi ulang
  hanya dari data s.d. t. 61 → 55 minggu bertanda; 1 origin uji berbeda (2024-12-02). `drivers_weekly.episode` (event study & robustness) tidak berubah.
- Dijalankan ulang tercatat: `forecast_preds`/`forecast_eval`/`ablation` (2.029 dtk), `direction_preds` (1.350 dtk), `direction_tuned_preds` C2t
  (504 dtk), `robustness --tier2` (363 dtk). M0, M1, M2_nofx, C1, C1t identik (≤ 1e-15); M2, M3, C2, C2t berubah di semua origin (koefisien bergeser;
  maks |Δ| ramalan M2 0,030, M3 0,165 log).

| Ukuran | Sebelum | Sesudah |
|---|---|---|
| M2/M1 h 4 / h 8 (DM p) | 1,0145 (0,001) / 1,0166 (0,006) | 1,0086 (0,009) / 1,0125 (0,025) |
| M3/M1 h 4 / h 8 (DM p) | 1,044 (0,031) / 1,015 (0,49) | 1,037 (0,052) / 1,014 (0,53) |
| H5 h 8 large_move impor langsung / input impor (Holm) | 1,120 / 1,118 (1,0) | 1,112 / 1,115 (1,0) |
| V2 origin 2026 | 1,005 / 1,005 | 1,005 / 1,004 |
| C2 macro F1 dev; test | 0,595 / 0,610; 0,591 / 0,612 | 0,585 / 0,615; 0,581 / 0,614 |
| C2t macro F1 dev; test | 0,653 / 0,679; 0,673 / 0,678 | 0,654 / 0,675; 0,675 / 0,679 |
| C2 − C1 h 8 | +0,009 (−0,007..0,027) | +0,012 (−0,004..0,030) |
| Beda berpasangan lolos BH | 5/30 (C2 vs M3 h 4 +0,025, q 0,015) | 4/30 (C2 vs M3 h 4 +0,013, q 0,36) |

### 10.2 U107 — interval terkalibrasi plasebo untuk PT & provinsi (D-163, tambahan pasca-G6)

- **PT nasional** (baris `driver = PT` di `national_calibrated`): interval β_e terkalibrasi / γ(h); p & q sama dengan baris e (keluarga BH 48 sel
  tetap). 3/30 sel tidak memuat nol (resmi 1/30): daging ayam h 4 −0,81 (−1,45..−0,16), h 8 −1,27 (−2,10..−0,44), gula h 4 0,48 (0,18..0,78). Lebar
  median hampir sama (1,59 vs 1,57), tetapi kini berpusat pada estimasi.
- **Deviasi provinsi** (`province_calibrated`, 1.623 baris): null |t*| dipool antarprovinsi per sel, crit median 2,05–2,22; replikasi bootstrap provinsi
  juga tertarik ke nol (boot_ratio 0,51–0,67). Interval resmi memuat nol hampir selalu (0–2,4% sel), ±1,96·SE terlalu longgar (6–17%), terkalibrasi
  5–12%. q BH per sel < 0,05 pada 37 sel (daging ayam β_e 10, gula β_e 11, telur β_e h 8 9, minyak goreng ω 5, beras ω 1); BH global atas 1.623 sel
  menyisakan 7 (daging ayam Maluku, Papua, Kepri; gula Kalbar & Kalteng; minyak goreng ω Maluku Utara). Konsisten dengan G-het. Deskriptif,
  bukan klaim kausal.

### 10.3 Fitur clustering konstan (D-163)

13/33 kolom konstan (τ² = 0 → EB menyusutkan ke rerata). Jarak antarprovinsi identik dengan & tanpa kolom itu; silhouette sama (k* = 3, 0,184 < p95
plasebo 0,196 → k = 1). Pada 40 matriks replikasi plasebo, 553 kolom konstan dan 0 kolom yang derau float-nya membesar. Tidak ada yang perlu dioptimasi.

### 10.4 Kalibrasi skor daftar pantau (D-163a, protokol beku)

| h | Varian | ECE | Brier | ΔBrier (interval) | Presisi S1 | ΔS1 (interval) | macro F1 |
|---|---|---|---|---|---|---|---|
| 4 | C1t | 0,035 | 0,2180 | – | 0,249 | – | 0,656 |
| 4 | K1 Platt global | 0,016 | 0,2189 | +0,0010 | 0,249 | 0 | 0,648 |
| 4 | K2 Platt + intersep komoditas | 0,022 | 0,2241 | +0,0061 (> 0) | 0,260 | +0,011 | 0,632 |
| 4 | K3 isotonik | 0,014 | 0,2205 | +0,0026 | 0,228 | −0,021 (< 0) | 0,651 |
| 8 | C1t | 0,056 | 0,2128 | – | 0,221 | – | 0,676 |
| 8 | K1 | 0,042 | 0,2149 | +0,0021 | 0,221 | 0 | 0,674 |
| 8 | K2 | 0,050 | 0,2267 | +0,0139 (> 0) | 0,268 | **+0,046 (+0,008..+0,098)** | 0,628 |
| 8 | K3 | 0,027 | 0,2145 | +0,0017 | 0,213 | −0,008 | 0,671 |

Tidak ada varian lolos (ECE turun tetapi Brier tidak membaik: galat tersisa = pergeseran laju naik antarperiode). K2 menaikkan presisi pantau h 8
karena mengurutkan komoditas menurut laju naik historisnya → petunjuk bahwa skor ranking dan peluang arah sebaiknya dipisah (→ K4).

---

## 11. K4 risiko kenaikan material (D-164)

Sumber: [RESULTS](20261126_k4_risiko_material/RESULTS.md) dan 9 dokumen pendukung (§1). Protokol beku 18.36 WIB sebelum model dilatih.

### 11.1 Target & kebutuhan

- **z = 1[y_h ≥ thr(o, h, c)]**, thr = P80 |y_h| baris latih komoditas c pada origin o (walk-forward; identik dengan D-154). z = 0 untuk turun, tetap,
  naik di bawah ambang, dan target tak teramati. Target alternatif **kejadian dalam jendela** z_any = 1[max_{k≤h}(log p_{t+k} − log p_t) ≥ thr].
- Ambang median dev h 4 / h 8: beras 1,2% / 2,1% (± 3 / 5 tick), daging sapi 1,6% / 2,2%, minyak goreng 2,4% / 3,9%, gula 3,2% / 6,0%, telur 9,3% /
  12,4%, ayam 13% / 18%, bawang putih 14% / 23%, bawang merah 23% / 36%, cabai merah 37% / 58%, cabai rawit 49% / 71%.
- Karena persentil dari |y| dua arah tetapi target hanya sisi naik, **60% / 64% positif adalah komoditas diatur** (ambang 1,2–3,9%). Ambang seragam
  ilustratif 5% membalik komposisi ke 13% / 19%. Sifat definisi, bukan temuan risiko.
- 8 pertanyaan kebutuhan (kenaikan vs dua arah, ambang material, ambang per komoditas, persen vs rupiah, titik akhir vs kejadian, kapasitas, alarm yang
  dapat ditindaklanjuti, biaya FN:FP) **belum satu pun dijawab pengguna** → validasi V1–V8 (U109; [panduan wawancara](../PANDUAN_WAWANCARA_TPID.md)).

### 11.2 Data Understanding (dev)

- Laju z 0,120 / 0,132; antarkomoditas 0,026 (bawang putih, ± 1 positif per seri) .. 0,240 / 0,293 (minyak goreng); antarprovinsi sd 0,015;
  antarminggu sd 0,072 / 0,084; musim Jun–Agu 0,05–0,09 vs Nov–Apr 0,15–0,19; komoditas diatur 0,17–0,23 vs tidak diatur 0,07–0,08 (2021–2023).
- Label jauh lebih kokoh dari label arah: tidak ada positif < 2 tick; 7,2% / 4,5% positif dalam 1 tick dari ambang (beras 22,5%); arah tak stabil 1,0% / 0,3%.
- Lonjakan yang berbalik sebelum titik akhir: 12% / 21% kejadian (ayam 32–44%, telur 43% h 8, bawang putih 40% h 4).
- Sesudah perubahan HET/HAP konsumen laju justru lebih rendah (0,08 vs 0,12–0,13): kenaikan acuan menyerap kenaikan sebelum tanggal penetapan.

### 11.3 Ranking (AP pooled utama; K4-E80 = HGB kolom & hyperparameter C1t beku, label z, semua baris latih termasuk y = 0)

| Skor | AP dev h 4 / h 8 | AP test h 4 / h 8 | ROC-AUC dev | Presisi@K2 dev | Presisi@K2 test |
|---|---|---|---|---|---|
| **K4-E80** | **0,326 / 0,290** | **0,237 / 0,206** | 0,775 / 0,743 | **0,293 / 0,272** | **0,202 / 0,174** |
| B-C1t (p_up C1t) | 0,246 / 0,250 | 0,192 / 0,191 | 0,711 / 0,696 | 0,249 / 0,221 | 0,179 / 0,161 |
| B-CLIM (laju-dasar komoditas) | 0,184 / 0,208 | 0,106 / 0,122 | 0,606 / 0,615 | 0,190 / 0,248 | 0,097 / 0,143 |
| B-CLIMS (komoditas × bulan) | 0,123 / 0,150 | 0,109 / 0,112 | 0,538 / 0,571 | 0,101 / 0,169 | 0,104 / 0,093 |
| R_nat | 0,153 / 0,157 | 0,091 / 0,082 | 0,603 / 0,582 | 0,136 / – | 0,091 / 0,090 |
| R_rev | 0,109 / 0,128 | 0,123 / 0,121 | 0,445 / 0,481 | 0,111 / – | 0,113 / 0,121 |

| Berpasangan | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| ΔAP K4 − C1t | **+0,080 (0,046..0,103)** q 0,002 | +0,039 (−0,008..0,101) | **+0,045 (0,017..0,083)** q 0,048 | +0,015 (−0,028..0,064) |
| ΔPresisi@K2 K4 − C1t | **+0,044 (0,019..0,067)** | +0,050 (−0,005..0,112) | **+0,023 (0,003..0,047)** | +0,012 (−0,009..0,042) |
| ΔPresisi@K3 K4 − C1t | **+0,027** | **+0,036** | **+0,018** | **+0,019** |
| ΔAP K4 − B-CLIM | **+0,142** | +0,081 | **+0,131** | **+0,084** |
| ΔPresisi@K2 C1t − B-CLIM | +0,058 (−0,014..0,123) | **−0,026** (−0,105..0,031) | **+0,082 (0,050..0,120)** | +0,019 (−0,027..0,081) |

Stabilitas ΔAP per tahun: dev h 4 +0,092 / +0,062 / +0,090, h 8 +0,087 / +0,038 / −0,022; test h 4 −0,011 / +0,051 / +0,096. K4 ≥ C1t (presisi@K2)
di 29 / 34 (h 4) dan 32 / 34 (h 8) provinsi dev, 79% / 73% origin dev. Kepekaan target (ΔAP K4 − C1t pada targetnya sendiri): P70 +0,086 / +0,040,
P90 +0,075 / +0,049, **P90 y bertanda (komposisi seimbang) +0,059 (0,029..0,080) / +0,026** → keunggulan h 4 bukan semata efek komoditas diatur.

### 11.4 Peluang (himpunan origin yang punya kalibrator walk-forward)

| Himpunan | Brier K4 / K4-cal / C1t-cal / CLIM | ECE K4 / K4-cal / C1t-cal | Brier skill K4 vs CLIM | ΔBrier K4 − C1t-cal |
|---|---|---|---|---|
| dev h 4 | 0,0979 / 0,0985 / 0,1042 / 0,1108 | 0,023 / 0,014 / 0,014 | **0,116 (0,052..0,170)** | **−0,0063 (−0,0091..−0,0030)** |
| dev h 8 | 0,1132 / 0,1136 / 0,1165 / 0,1214 | 0,044 / 0,019 / 0,010 | 0,068 (−0,031..0,153) | −0,0033 (−0,0124..+0,0060) |
| test h 4 | 0,0750 / 0,0749 / 0,0774 / 0,0811 | 0,019 / 0,020 / 0,030 | **0,075 (0,039..0,107)** | **−0,0024** |
| test h 8 | 0,0795 / 0,0778 / 0,0797 / 0,0818 | 0,024 / 0,030 / 0,039 | 0,029 (−0,053..0,107) | −0,0002 |

- **Ekor atas h 8 terlalu yakin**: 57 baris dev dengan p 0,8–0,9 hanya 28% naik material; Platt global tidak memperbaikinya.
- Skor arah yang dikalibrasi hampir tidak pernah memberi peluang > 0,4 → tidak dapat menyatakan risiko tinggi.
- p_up mentah dibaca sebagai peluang z: Brier 0,266 / 0,278 (dev), ECE 0,38 (dev) / 0,44–0,46 (test) → **jangan tampilkan p_up sebagai "peluang naik tajam"**.
- Di test rerata peluang K4 0,107 / 0,113 vs laju 0,088 / 0,089 (membawa laju latih dev yang lebih tinggi).

### 11.5 Operasional, utilitas, galat

- K = 2 per provinsi (68 alarm/minggu): benar 19,9 / 18,5 (dev), 13,7 / 11,8 (test) untuk K4 vs 16,9 / 15,1 dan 12,2 / 11,0 untuk C1t; 7–8 dari 10
  alarm tetap tidak berujung kenaikan material. B-CLIM h 8 kompetitif tetapi 93% alarm pada komoditas diatur dan 97% berulang tiap minggu (hanya
  5 komoditas pernah ditandai); K4 51% berulang, 10 komoditas.
- Ambang peluang τ 0,3 (dev h 4): ± 30 alarm/minggu (sd 29), presisi 0,41, 16 provinsi tanpa alarm per minggu; jumlah alarm mengikuti risiko.
- Skenario biaya (satuan = 1 alarm palsu, r = biaya kenaikan terlewat; **bukan biaya nyata**): r = 1–2 → "tanpa alarm" termurah (presisi < 0,5);
  r = 5 → K4 termurah (dev h 4 150 vs C1t 168 vs tanpa alarm 202); r = 10 → K4 K = 3 termurah. Net benefit K4 > C1t-cal > laju-dasar > "pantau
  semua" pada τ 0,10–0,40. **Daftar pantau bukan pemicu tindakan**; bernilai bila kenaikan terlewat ≥ ± 3–5× lebih mahal dari alarm palsu.
- Galat (K = 2): alarm palsu 50–58% kenaikan nyata di bawah ambang, 29–37% penurunan, 10–19% harga tetap; 19–21% "nyaris". Kenaikan terlewat
  13–17% dari harga datar 4 minggu sebelumnya, ± 36% berperingkat ≥ 6 dari 10 di provinsinya. **Presisi ditentukan waktu**: origin berlaju rendah
  (± 3–5%) presisi 0,04–0,12 untuk semua skor, laju tinggi 0,27–0,45; rerata peluang K4 hanya bergerak 0,08 → 0,13 (bottleneck 2 D-156).
- Target kejadian K4-A80: ΔAP vs K4-E80 +0,002 / +0,018 (dev, memuat 0), test h 8 +0,054 (tidak dipakai memilih).

### 11.6 Keputusan & integritas

- **PARTIAL** (R1 ranking & R1b vs naif terbaik lolos; R2 peluang gagal di h 8) · **BLOCKED** untuk penggunaan operasional sampai U109.
  K4 tidak masuk `src/`; C1t, label arah, macro F1 resmi, H5 tidak berubah.
- Integritas: refit B-C1t = artefak resmi (dev 25.259, test 24.616 baris, maks |Δp| 0); universe dev 12.800 / 12.463 (= D-155); perturbasi 6 origin × h
  → 0 perbedaan; uji mandiri 6/6; test dibuka sekali sesudah keputusan dev PARTIAL; BH keluarga F (ΔAP, ΔPresisi@K2, ΔBrier × 2 h).
- Pengungkapan: 5 skrip evaluasi ditulis sesudah pembekuan protokol sebagai implementasi §3–§6; bug `fast_ap` diperbaiki sebelum hasil dibaca;
  ranking pooled varian `-cal` di EXPERIMENT_LOG bukan pembanding ranking (6–7 origin awal tanpa kalibrator); commit `ec6dd19` memuat versi awal
  folder sebelum hasil ada.
- Rekomendasi: (1) validasi TPID; (2) koreksi klaim daftar pantau dengan B-CLIM (dilakukan di `results/findings.md`); (3) validasi prospektif;
  (4) bila disajikan: urutkan dengan K4-E80, peluang hanya h 4; (5) kartu C3 (kalibrasi ekor h 8, target kebijakan, target kejadian) hanya sesudah U109.

---

## 12. Jalur A (D-165)

Sumber: [RESULTS](jalur_a_macro_f1/RESULTS.md). Tiga sesi agent bekerja bersamaan pada 2026-11-26 (Jalur A, D-162/D-163, K4 D-164); Jalur A tidak
menyentuh `src/`, `tests/`, artefak resmi, atau konfigurasi; nomor keputusan dikoordinasikan antarsesi.

- **Workstream A (prospektif)**: prediksi maju D-152 & D-158 utuh (sha256 = manifest; base D-152 = base D-158; 338 seri; 0 NaN); kode yang berubah
  sejak beku hanya `src/features/forecast.py` (D-162, kolom `episode` grup kurs — tidak dipakai C1t/IW_NAT/FR_*). Evaluator gabungan
  `jalur_a_macro_f1/scripts/a_forward_eval.py` dibekukan 11.34 UTC sebelum target ada, dengan penanda **GAGAL_MAJU** bila Δ macro F1 < −0,08 (h 4) /
  < −0,04 (h 8), **KONSISTEN** bila Δ ≥ 0, selain itu **TIDAK_TERBUKTI**. Tidak ada keputusan adopsi dari data maju.
- **Workstream B (GDELT)**: §7.8 → REJECTED.
- **Workstream C (pasokan & kejadian)**: 10 kandidat; tidak ada yang lolos G1–G4 untuk dev (§7.1, §7.6).
- **Workstream D (modeling)**: tidak dijalankan (tidak ada sumber yang lolos G1–G5).
- **Aspirasi F1 0,8–0,9 tidak didukung bukti**: informasi nasional sempurna hanya 0,756 / 0,782.
- Rekomendasi tersisa: evaluasi maju sesudah unduh PIHPS baru (≥ 2026-11-28; ulang 2026-12-19 & 2027-01-16); satu surat permintaan data resmi (U112);
  hentikan optimasi dari histori harga; proyek GCP `kagami-gdelt` boleh dibiarkan (tanpa billing) atau dihapus.

---

## 13. Sintesis: di mana batas skor berada

### 13.1 Tuas yang sudah diuji

| Tuas | Laporan | Kenaikan terbaik (dev, kecuali disebut) | Status |
|---|---|---|---|
| Fitur dinamika harga per seri (deviasi, sinyal nasional, lag panjang, musiman) | D-145 | +0,07..+0,09 vs C1 | sumber kenaikan C1t |
| Tuning hyperparameter HGB | D-145 | ± +0,01 | sudah dipakai C1t |
| Fitur tambahan dari histori harga (ronde 2, 8 keluarga D-156, rezim) | D-146, D-148, D-156 | ≤ +0,003 | jenuh |
| Algoritma lain (LGB, XGB, CatBoost, ExtraTrees, logistik, TSMixer, PatchTST, TCN, MLP, TFM-head) | D-145, D-146, D-156 | ≤ 0 | jenuh |
| Threshold / bobot kelas / kalibrasi | D-145, D-148, D-156, D-163a | ≤ 0 (oracle global ≤ +0,006) | bukan bottleneck |
| Preprocessing (label latih bersih, tanpa ffill, normalisasi, jendela, bobot) | D-147, D-156 | ≤ 0 | beku |
| Kurs & harga dunia | H5, D-141, D-142, D-145, D-162 | ≤ 0 | tidak membantu (konsisten H5) |
| Harga hulu PIHPS (grosir, produsen) | D-150, D-151 | ≤ +0,001 | bergerak bersama/sesudah eceran |
| **Intraminggu** (`iw_gap`, `IW_NAT`, FR_REF) | D-147, D-151, D-152, D-158 | +0,020 / +0,005 dev; test +0,0085 / +0,0033 | **satu-satunya positif; belum terbukti** |
| Breadth 110 kota, model nasional → lokal | D-158 | kontribusi ≈ 0 | – |
| Cuaca terealisasi & prakiraan, impor, pakan, berita | D-157, D-160, D-161, D-165 | ≤ 0 | mekanisme tertutup atau sinyal tidak ada |
| Pasokan fisik & neraca resmi | D-159, D-165 | tidak teruji | **terblokir akses** |

### 13.2 Batas atas yang dihitung

| Batas atas | Nilai | Arti |
|---|---|---|
| Informasi arah nasional sempurna per komoditas × minggu | +0,105 → 0,756 / 0,782 | plafon untuk sinyal nasional apa pun |
| Oracle threshold per origin (hindsight) | +0,035 / +0,024 | bagian base rate yang hanya diketahui sesudahnya |
| Pembersihan semua label rapuh | +0,01..+0,02 | derau pembentukan data (tick, komposisi hari) |
| Oracle threshold global | +0,000 / +0,006 | threshold bukan bottleneck |
| Derau pelatihan HGB (fitur r 0,998) | ± 0,005 | selisih dev sekecil ini bukan perbaikan |
| MDE test (D-151) / MDE layar G5 | 0,019 / 0,010 macro F1; ± 0,023 AUC | efek realistis +0,005..+0,02 tidak dapat dikonfirmasi |

### 13.3 Kesimpulan lintas audit

1. Batas skor arah ± 0,68 adalah **batas informasi** harga PIHPS publik, bukan batas pengolahan: pengolahan ulang histori harga dengan cara apa pun
   memberi perbedaan dalam derau pelatihan.
2. Dua bottleneck yang tersisa (perubahan kecil; base rate per origin) membutuhkan informasi **ex-ante non-harga** tentang arah nasional. Semua
   sumber publik yang terjangkau sudah gagal atau terblokir; sisanya butuh permintaan resmi (U112) dan hanya dapat dievaluasi prospektif.
3. Ukuran manfaat yang lebih dekat dengan keputusan TPID adalah **daftar pantau risiko kenaikan material** (K4), bukan macro F1 arah. Nilainya
   bergantung pada ambang kebijakan, kapasitas, dan rasio biaya yang belum divalidasi (U109).

---

## 14. Aturan metode yang lahir dari audit (ringkas; teks mengikat di [`docs/EKSPERIMEN.md`](../EKSPERIMEN.md))

| Aturan | Asal | Isi singkat |
|---|---|---|
| Kartu 8 komponen | D-153 | problem, karakteristik data, knowledge discovery, hipotesis, metode, validasi, kontrol kebocoran, keputusan — sebelum kode modeling |
| Layar Data Understanding | D-153 | korelasi residual dengan kontrol positif & negatif, *partial* bila kontrol negatif ≠ 0; lanjut bila q < 0,05 di kedua horizon dan ≥ ½ kontrol positif |
| Sinyal tingkat nasional | D-157 | wajib koreksi logit walk-forward berparameter kecil sebelum modeling |
| Kelayakan sumber baru | D-159 | riwayat dev, akses sah tanpa login/CAPTCHA, tanggal ketersediaan, frekuensi ≤ mingguan, skala pasar; gagal → tanpa backfill |
| Layar arah nasional | D-158 | ΔAUC di atas konsensus C1t, increment-only; kalibrasi ulang dengan intersep/dummy historis dilarang |
| Oracle untuk sumber prakiraan | D-161 | uji nilai terealisasi dulu sebelum biaya ekstraksi |
| Daya layar | D-165 | laporkan kontrol positif `iw_gap_nat` & MDE; ambang tidak diubah sesudah data kandidat terlihat |
| Aturan evaluasi tetap | D-145–D-152 | pembanding C1t beku, seleksi dev, test sekali per keluarga, Δ ≥ +0,005 & interval > 0 di ≥ 1 horizon & Δ ≥ 0 di lainnya, protokol di-hash sebelum run |
| Aturan ketat | D-156 | + q BH < 0,05, konsistensi tahun & origin, F1 per kelas & per komoditas tidak mundur |
| Keluarga intraminggu | D-152 | tidak membuka test lagi; konfirmasi hanya prediksi maju |
| Ketepatan target & klaim | D-155 | test bukan independen; universe tanpa penyaringan target; skor ≠ target bisnis; ukuran bersyarat diberi label; materialitas statistik vs kebijakan; titik akhir vs kejadian; daftar pantau pada jumlah alarm sama; kebocoran observasional vs revisi; terminologi metode |
| Pembanding laju-dasar & utilitas | D-164 | laju-dasar komoditas (± bulan) wajib; persistensi alarm; utilitas pada r = 1/2/5/10 dan kurva keputusan |
| Registri terpusat | D-156 | satu baris per varian termasuk yang gagal/diblokir/ditolak |
| Komputasi | D-148 | job > 1 jam → Colab T4, output ke Drive terpusat |
| Split pasca-hoc | D-149 | hasil split yang dipilih sesudah melihat test berlabel "eksploratif pasca-hoc" |

---

## 15. Rambu klaim Task 4 arah (pelengkap CLAUDE.md §20)

| Jangan tulis | Tulis |
|---|---|
| "Model memprediksi arah harga dengan akurasi 68%" | "Dalam evaluasi rolling-origin pseudo-real-time (origin 2024–2026), klasifier arah eksploratif C1-tuned mencapai macro F1 0,677 / 0,680 (interval 0,652..0,698 / 0,653..0,706)" |
| "Fitur kurs memperbaiki prediksi" | "Fitur kurs tidak memperbaiki MAE (M2/M1 1,009 / 1,013) dan tidak terbukti menambah akurasi arah di keluarga model mana pun" |
| "Tervalidasi pada test 2024+" | "Evaluasi eksploratif dengan kriteria yang ditetapkan sebelumnya; bukti independen menunggu prediksi maju beku" |
| "TimesFM mengungguli model lain" | "TimesFM 3.0 zero-shot MAE/M1 0,935 / 0,895; batas atas karena korpus pralatih mungkin memuat periode uji" |
| "IW_NAT lebih baik dari C1-tuned" | "Searah di dev dan test (+0,0085 / +0,0033) tetapi belum terbukti (q 0,28 / 0,30)" |
| "p_up = peluang kenaikan tajam" | "Skor arah P(naik \| harga berubah); peluang kenaikan material hanya dari model yang dilatih pada target itu (K4, h 4)" |
| "Daftar pantau dua kali laju-dasar" | "Presisi 0,18 / 0,16 vs aturan tren 0,08–0,09; terhadap laju-dasar per komoditas, h 4 lebih baik (+0,082, test), h 8 tidak terbukti" |
| "KAGAMI memprediksi risiko kenaikan harga" | "Skor ranking risiko kenaikan material statistik (P80 \|y\| per komoditas, titik akhir), eksploratif; penggunaan operasional menunggu validasi pengguna" |
| "Tidak ada kebocoran" | "Tidak ditemukan look-ahead observasional (uji perturbasi & penghapusan data sesudah origin); efek revisi data historis belum dapat diverifikasi" |
| "Provinsi terbagi menjadi 5 tipe" | "Partisi deskriptif 5 tipe perilaku harga (silhouette 0,33–0,34, hampir datar untuk k 2–6)" |
| "Sequential pattern mining tidak menemukan pola" | "Screening asosiasi temporal lintas komoditas tidak menemukan asosiasi yang stabil pada konfigurasi yang diuji" |
| "Sumber X tidak mengandung informasi" (gagal G5) | "Sumber X tidak menambah informasi arah nasional di atas konsensus model sebesar yang dapat dideteksi layar (MDE ± 0,023 AUC)" |
| "Arah tepat 81% saat harga bergerak besar" tanpa kualifikasi | "Pada baris yang ternyata bergerak material (ukuran bersyarat pada hasil), macro F1 ± 0,81" |

---

## 16. Prediksi maju beku & jadwal

| Pembekuan | Berkas | Baris | Model | sha256 | Di git sebelum target? |
|---|---|---|---|---|---|
| D-152 | `20261125_iw_validasi/hasil/forward_preds.csv` + `forward_manifest.json` | 8.112 | C1t, `IW_NAT` | `28651b2b…` | ya, `ca53742` (2026-11-25 21.41 WIB) |
| D-158 | `20261126_nasional_lokal/hasil/forward_preds_d158.csv` + `forward_manifest_d158.json` | 12.168 | base, FR_REF, FR_CITY | `7586eaed…` | ya, `ec6dd19` (2026-11-26 20.45 WIB) |
| D-164 (K4) | `20261126_k4_risiko_material/hasil/k4_forward_preds.csv` + `k4_forward_manifest.json` | 4.056 | K4-E80, K4-A80, B-C1t, laju-dasar | `eb1f10db…` (beku 2026-11-26 23.16 WIB) | **belum**: commit `3095ae0` (23.15 WIB) memuat versi sebelumnya (sha256 `1b5c84cb…`, susunan kolom berbeda); versi beku termodifikasi dan manifest belum di-track (diperiksa 2026-11-27 dini hari) |

- Origin semua pembekuan: h 4 = 2026-10-26, 11-02, 11-09, 11-16; h 8 = 2026-09-28 .. 2026-11-16 (8 minggu). Minggu data terakhir 2026-11-16
  (Senin–Rabu saja).
- Target lengkap (snapshot memuat Jumat minggu t + h): pertama **2026-11-27** (h 4 origin 10-26, h 8 origin 09-28); semua h 4 pada **2026-12-18**;
  semua h 8 pada **2027-01-15**.
- Evaluator: `20261125_iw_validasi/scripts/fw_eval.py` (D-152; selftest label 156.400 / 155.040 baris, 0 beda), `jalur_a_macro_f1/scripts/a_forward_eval.py`
  (gabungan D-152 + D-158, beku 11.34 UTC), `20261126_k4_risiko_material/scripts/k4_eval.py` (PART baru untuk K4).
- Langkah: unduh snapshot PIHPS baru berformat `pihps` (skrip `20261125_pilot_grosir/scripts/fetch_pihps.py`, pasar tradisional, rentang ≥ 2026-09-01;
  cocokkan nama varian dengan zip resmi) → jalankan evaluator. Daya hanya cukup untuk mendeteksi kegagalan besar.

---

## 17. Pekerjaan terbuka

| Item | Rujukan | Siapa | Tenggat / kapan |
|---|---|---|---|
| Commit versi beku prediksi maju K4 + manifest | D-164, §16 | Danen (git) | **sebelum target pertama lengkap, Jumat 2026-11-27** |
| Commit sisa perubahan sesi 2026-11-26 (dokumen K4, `findings.md`, registri, EKSPERIMEN, DECISIONS, dll.) | CLAUDE.md §2 | Danen (git) | sebelum pembekuan hasil 27 Nov |
| Evaluasi prospektif (D-152, D-158, K4) | §16 | Danen (unduh) + agent | ≥ 2026-11-28; 2026-12-19; 2027-01-16 |
| U109 validasi kebutuhan TPID (V1–V8: ambang kebijakan, dua arah, titik akhir vs kejadian, kapasitas K, rasio biaya, angka peluang vs urutan, waktu keputusan, relevansi kenaikan 1–3% komoditas diatur) | D-154, D-155, D-164 | `[HUMAN]` | sebelum klaim produk / makalah final |
| U110 jendela revisi PIHPS (`available_at`) | D-155 | `[HUMAN]` | – |
| U111 panel kab/kota Bapanas; izin BI untuk data PIHPS per kota | D-158 | `[HUMAN]` | – |
| U112 satu surat permintaan data: SP2KP stok mingguan, Proyeksi Neraca Pangan (semua vintage), luas tanam/EWS hortikultura | D-159, D-165 | `[HUMAN]` | sesudah submit; evaluasi prospektif |
| U19 / U13: status unduh resmi & cakupan izin BI untuk jenis pasar grosir, produsen, kota | D-150, D-151, D-158 | `[HUMAN]` | – |
| Halaman 7: evaluasi bersih pada satu commit (`git_dirty`), restart server 8501 | audit C.4 #1, #12 | Danen | – |
| Lineage Task 1 di bawah pelacakan | audit C.4 #3 | Kaggle run | opsional |
| Ablation per kelompok fitur pada M2 | audit #5 | – | butuh Task 4 ulang; tidak diprioritaskan |
| Tipologi K2: DB/CH, stabilitas bootstrap, algoritma alternatif | D-155 | – | sebelum disajikan sebagai temuan ilmiah |
| Uji kontaminasi TimesFM pada seri yang jarang dipublikasikan | D-144 | – | opsional |
| Kartu K4 C3 (ekor h 8, target kebijakan, target kejadian) | D-164 | – | hanya sesudah U109 |
| Proyek GCP `kagami-gdelt` (tanpa billing): biarkan atau hapus | D-165 | Danen | bebas |
| Bug MANIFEST zip `pihps_city`: kolom `first_date`/`n_dates` bergeser 2 kolom (data harga tidak terpengaruh; berkas mentah tidak diubah) | D-158 | – | catatan; skrip sudah diperbaiki untuk pengambilan berikutnya |
| Salinan `results/findings.md` di Drive tim (versi 2026-11-23) belum memuat temuan D-154 dst. | CLAUDE.md §2 | `[HUMAN]` | sebelum makalah |

---

## 18. Registri eksperimen

[`docs/eksperimen_registry.csv`](../eksperimen_registry.csv) (dibangun `20261126_task4_master_f1/scripts/r_registry.py`; satu baris per varian, termasuk
yang gagal/diblokir/ditolak). Keadaan 2026-11-27: **189 baris** — REJECTED 126, COMPLETE 43, BLOCKED 16, PARTIAL 3, FAILED 1.

| Keputusan | Baris | Keputusan | Baris | Keputusan | Baris |
|---|---|---|---|---|---|
| D-145 | 25 | D-151 | 6 | D-159 | 5 |
| D-146 | 15 | D-152 | 3 | D-160 | 5 |
| D-147 | 10 | D-153 | 3 | D-161 | 10 |
| D-148 | 12 | D-155 | 1 | D-162 | 2 |
| D-149 | 12 | D-156 | 27 | D-163 | 3 |
| D-150 | 3 | D-157 | 4 | D-164 | 5 |
| – | – | D-158 | 16 | D-165 | 22 |

Log rinci terpisah: K4 `20261126_k4_risiko_material/EXPERIMENT_LOG.csv` (ID `K4-*`/`B-*`), Jalur A `jalur_a_macro_f1/EXPERIMENT_LOG.csv` (ID `JA-*`).
PARTIAL = C2-tuned 12/25 trial, TSMixer-tuned 10 trial, TFM-head grid dipangkas; FAILED = TCN Colab percobaan 1 (GPU penuh).

---

## 19. Indeks lampiran (skrip & hasil utama per folder)

| Folder | Skrip utama | Hasil utama |
|---|---|---|
| `20261124_task4_optimasi_arah/` | `scripts/feats.py` (fitur per seri), tuning Optuna, TFM-head | `hasil/final_metrics.json`, `final_paired.csv`, `final_per_commodity.csv` |
| `20261125_task4_ronde2/` | `colab/kagami_d146_tcn.ipynb`, `tcn_mtl.py`, `eval_d146.py` | `hasil/tcn_mlp_dev.csv`; prediksi TCN di Drive `experiments/d146_tcn/out/` |
| `20261125_task4_audit_preprocessing/` | `p01_integrity.py`, `p03_label.py`, `p05_noise.py`, `p09_balance.py`, `p10_leakage.py`, `prep.py`, `p_exp.py`, `p_eval.py` | `p10_leakage.csv`, `p03_*`, `p09_*`, `exp_dev_*`, `exp_test_*` |
| `20261125_task4_ronde4/` | `cal.py`, `feats_regime.py`, `r4_exp.py`, `r4_eval.py`, `r4_eval2.py` | `cal_dev*.csv`, `r4_dev_*`, `r4s2_*`, `policy_events.csv` |
| `20261125_pilot_grosir/` | `fetch_pihps.py`, `ws_build.py`, `ws_exp.py`, `ws_eval.py` | `ws_coverage.csv`, `ws_leadlag.csv`, `ws_dev_*` |
| `20261125_pilot_produsen_intraminggu/` | `iw_build.py`, `pr_build.py`, `exp.py`, `ev.py` | `iw_test_*`, `pr_coverage.csv`, `pr_leadlag.csv`, `pr_dev_*` |
| `20261125_iw_validasi/` | `iw2_build.py`, `diag.py`, `fw_freeze.py`, `fw_eval.py`, `power.py` | `leak_audit.csv`, `diag_dev_*`, `forward_preds.csv`, `forward_manifest.json`, `forward_power.csv` |
| `20261125_crisp_du/` | `du.py`, `du_b.py`, `du_c.py` | `du0_controls.csv`, `du1_*`, `du2_*`, `du3_*` |
| `20261125_business_understanding/` | `bu.py`, `audit.py` | `bu_s1_*` … `bu_s4_*`, `bu_criteria.csv`, `audit_*` |
| `20261126_task4_master_f1/` | `a_errors.py`, `b_audit.py`, `c_feats.py`, `c_leak.py`, `c_du.py`, `m_run.py`, `e_eval.py`, `r_registry.py` | `a_*`, `b_summary.json`, `c_leak.csv`, `c_du.csv`, `e_metrics.csv`, `e_decision.csv`, `registry.csv` |
| `20261126_pilot_cuaca_impor/` | `fetch_power.py`, `feats_wi.py`, `build_wi.py`, `du_wi.py`, `run_wi.py`, `ev_wi.py`, `cal_wi.py` | `headroom.csv`, `wi_leak.csv`, `du_wi.csv`, `ev_*`, `cal_wi*` |
| `20261126_nasional_lokal/` | `fetch_kota.py`, `nl_build.py`, `kb_build.py`, `run_nl.py`, `ev_nl.py`, `diag_national.py`, `meta_build.py`, `fresh_du.py`, `fw_freeze_d158.py` | `ev_nl_br_*`, `ev_fr_city_vs_ref.csv`, `forward_preds_d158.csv`, `forward_manifest_d158.json` |
| `20261126_sumber_baru/` | `fetch_pakan.py`, `sij_du.py`, `cfs_du.py`, `colab/kagami_d160_cfsv2.ipynb` | `cfsv2_province_weekly.csv`, `cfsv2_manifest.csv` |
| `20261126_kelemahan_tercatat/` | skrip pembanding sebelum/sesudah | `u108_preds.csv`, `u108_forecast_eval.csv` |
| `20261126_kalibrasi_pantau/` | `kal.py` | `kal_decision.json` |
| `20261126_k4_risiko_material/` | `k4_common.py`, `k4_du.py`, `k4_run.py`, `k4_leak.py`, `k4_eval.py`, `k4_selftest.py`, `k4_freeze.py`, `k4_log.py` ([RUN.md](20261126_k4_risiko_material/scripts/RUN.md)) | `du_*`, `k4_ranking.csv`, `k4_paired.csv`, `k4_probability.csv`, `k4_reliability.csv`, `k4_ops_*`, `k4_utility_*`, `k4_test_*`, `k4_forward_preds.csv` |
| `jalur_a_macro_f1/` | `a_forward_eval.py`, `b_gkg_sample.py`, `b_manual_eval.py`, `b_bq_daily_counts.sql`, `b_bq_daily_counts_singleline.sql`, `b_gdelt_screen.py`, `r_log.py`; tes `tests/test_gdelt_screen.py` | `b_gkg_sample_*`, `b_manual_labels.csv`, `b_screen_controls.csv`, `gdelt_daily_counts.csv`, `gdelt_bq_manifest.json`, `b_screen_gdelt.csv` |

Data mentah opsional yang lahir dari audit (terdaftar di `configs/sources.yaml`, `redistribute` sesuai sumber): `pihps_wholesale`, `pihps_producer`,
`pihps_city`, `nasa_power`, `ditjenpkh_sijagung`. Agregat CFSv2 dan hitungan GDELT adalah turunan audit, bukan sumber terdaftar.
