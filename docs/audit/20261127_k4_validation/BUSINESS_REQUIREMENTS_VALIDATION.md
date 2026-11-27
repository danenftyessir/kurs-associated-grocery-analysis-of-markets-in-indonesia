# Validasi K4 — Instrumen validasi kebutuhan bisnis (U109)

Tanggal 2026-11-27, catatan bertanggal. Melengkapi [`docs/PANDUAN_WAWANCARA_TPID.md`](../../PANDUAN_WAWANCARA_TPID.md) (alur wawancara A–F,
rambu bicara, lembar catatan) dan [BUSINESS_REQUIREMENTS.md](../20261126_k4_risiko_material/BUSINESS_REQUIREMENTS.md) D-164 (V1–V8).
Wawancara adalah tugas `[HUMAN]`. Agent tidak menghubungi siapa pun. **Tidak ada jawaban TPID di dokumen ini, dan tidak ada yang dikarang.**

STATUS: **BLOCKED** (instrumen siap; 0 dari 12 kebutuhan tervalidasi)

OBJECTIVE: Menyediakan instrumen yang mengubah jawaban pemangku kepentingan menjadi keputusan K4 yang dapat diaudit: target, ambang, kapasitas,
biaya relatif, dan bentuk tampilan.

## 1. Status saat ini

| Kode | Kebutuhan | Asumsi kerja K4 sekarang | Status |
|---|---|---|---|
| R1 | Kenaikan saja atau perubahan dua arah | Kenaikan | NOT VALIDATED |
| R2 | Besar kenaikan yang material | P80 \|y\| riwayat komoditas (statistik) | NOT VALIDATED |
| R3 | Ambang berbeda per komoditas | Ya (relatif terhadap kebiasaan komoditas) | NOT VALIDATED |
| R4 | Persen atau rupiah | Persen (selisih log) | NOT VALIDATED |
| R5 | Titik akhir atau kejadian dalam jendela | Titik akhir; kejadian sebagai pembanding | NOT VALIDATED |
| R6 | Kapasitas pemantauan per provinsi | Tidak dipilih (K = 1/2/3/5 sebagai peta) | NOT VALIDATED |
| R7 | Biaya relatif alarm palsu vs terlewat | Skenario r = 1, 2, 5, 10 | NOT VALIDATED |
| R8 | Peluang absolut atau cukup urutan | Urutan; peluang h 4 eksploratif | NOT VALIDATED |
| R9 | Waktu keputusan (hari, jam, kesegaran data) | Sesudah harga Jumat final; `available_at` Minggu 00.00 | NOT VALIDATED |
| R10 | Tindakan sesudah alarm | Pemeriksaan lebih dalam (bukan intervensi otomatis) | NOT VALIDATED |
| R11 | Penanggung jawab tindak lanjut | Sekretariat TPID provinsi | NOT VALIDATED |
| R12 | Relevansi kenaikan 1–3% pada komoditas diatur | Dihitung material bila ≥ P80 | NOT VALIDATED |

Label status (dipakai di matriks §4):
- **VALIDATED**: konsisten pada ≥ 3 wawancara atau ≥ 2/3 narasumber (aturan PANDUAN §7), tanpa jawaban yang bertentangan.
- **PARTIALLY VALIDATED**: didukung 1–2 narasumber, atau mayoritas setuju tetapi angkanya berbeda jauh (rentang > 2×).
- **NOT VALIDATED**: belum ditanyakan atau belum dijawab.
- **CONFLICTING REQUIREMENTS**: narasumber memberi jawaban yang saling meniadakan (mis. satu butuh K = 1, satu K = 5), atau jawaban bertentangan
  dengan regulasi/praktik yang terdokumentasi. Dilaporkan sebagai rentang; proyek memilih opsi paling konservatif (PANDUAN §7).

## 2. Mengapa setiap pertanyaan penting (bukti dari audit ini)

| Kode | Akibat bila asumsi salah | Bukti |
|---|---|---|
| R2, R3, R4 | Dengan ambang seragam 5% / 10%, skor K4-E80 kalah dari C1-tuned (ΔAP h 8 −0,079 / −0,092, interval < 0). Model harus dilatih ulang | [TARGET_SENSITIVITY_REPORT.md](TARGET_SENSITIVITY_REPORT.md) §3 |
| R12 | 56–67% positif setiap target statistik adalah komoditas diatur; ambang beras P80 = Rp151/kg ≈ 3 tick | TARGET_SENSITIVITY §1–§2 |
| R5 | 25% alarm palsu h 4 naik material ≤ 4 minggu sesudah titik akhir (seri tanpa alarm 12%); target kejadian AP +0,09 di atas C1t | [OPERATIONAL_ERROR_ANALYSIS.md](OPERATIONAL_ERROR_ANALYSIS.md) §2 |
| R6 | K = 1 → 5: presisi 0,33 → 0,20, recall 0,28 → 0,82 (dev h 4) | OPERATIONAL_ERROR_ANALYSIS §1 |
| R7 | r ≤ 2: tidak memantau lebih murah dari daftar apa pun; r ≥ 5: K4 termurah | [RESULTS.md](../20261126_k4_risiko_material/RESULTS.md) §7 |
| R8 | Tidak ada kalibrator yang memperbaiki Brier; ekor h 8 terlalu yakin (p 0,8–0,9 → 28%) | [CALIBRATION_DEEP_AUDIT.md](CALIBRATION_DEEP_AUDIT.md) |
| R9 | Separuh keuntungan intraminggu h 4 berasal dari harga Jumat (D-152); revisi PIHPS belum diketahui (U110) | D-152, D-155 |
| R10, R11 | Menentukan apakah 7–8 alarm palsu dari 10 dapat ditoleransi | OPERATIONAL_ERROR_ANALYSIS §1 |
| R1 | Penurunan tajam (kerugian petani/peternak) tidak dimodelkan sama sekali | – |

## 3. Pertanyaan wawancara (sisipan ke PANDUAN §5)

Urutan mengikuti PANDUAN: B dan C sebelum D, contoh kartu (E) terakhir agar jawaban tidak tergiring. Kode di kolom kanan = kode PANDUAN.

| Kode | Pertanyaan (terbuka dulu, angka sesudahnya) | Jawaban yang dicatat | PANDUAN |
|---|---|---|---|
| R1 | "Selain kenaikan, apakah penurunan harga yang tajam juga perlu diperingatkan? Untuk komoditas apa?" | ya/tidak per komoditas; alasan | B3, D4 |
| R2 | "Kenaikan berapa persen dalam 4 minggu (dan 8 minggu) yang membuat tim mulai bertindak?" Isi tabel PANDUAN §6. Lalu: "Bagaimana dengan beras naik Rp150/kg (± 1%) dalam 4 minggu?" | angka per komoditas × horizon | D4 |
| R3 | "Apakah satu ambang berlaku untuk semua komoditas, atau berbeda? Mengapa?" | seragam / per komoditas / per kelompok | D4 |
| R4 | "Ambang itu dalam persen, rupiah per kg, atau terhadap HET/HAP?" | persen / rupiah / jarak HET-HAP | D4 |
| R5 | Skenario PANDUAN D5: (a) +15% di minggu ke-2 lalu kembali, (b) +5% perlahan sampai minggu ke-4. "Mana yang perlu diperingatkan? Bagaimana bila kenaikan baru datang di minggu ke-6?" | a / b / keduanya; jendela yang relevan | D5 |
| R6 | "Bila setiap minggu ada daftar untuk dicek lebih dalam, berapa komoditas per provinsi yang realistis?" | K (1/2/3/5/lain) | D1 |
| R7 | "Dari 10 yang ditandai, minimal berapa yang harus benar?" Lalu: "Mana lebih merugikan: menyiapkan yang tidak perlu, atau terlambat? Berapa kali lipat?" | presisi minimum; rasio r | D2, D3 |
| R8 | "Apakah angka seperti '40% berisiko' membantu, atau cukup urutan? Bila sistem menyebut 40%, Anda memahaminya sebagai apa?" | angka / urutan / kategori; tafsiran | D6 |
| R9 | "Hari dan jam berapa data dibaca dan keputusan dibuat? Apakah harga Jumat sudah dipakai?" | hari, jam; ya/tidak | C3 |
| R10 | "Bila sebuah komoditas masuk daftar, apa langkah pertama tim? Cek stok, hubungi pedagang, rapat, operasi pasar?" | daftar tindakan berurutan; waktu persiapan | C1, E4 |
| R11 | "Siapa yang menerima daftar dan siapa yang memutuskan tindak lanjutnya?" | peran (bukan nama) | C2 |
| R12 | "Untuk beras, gula, minyak goreng, daging sapi: apakah kenaikan 1–3% dalam sebulan dianggap perlu perhatian, atau baru bila mendekati HET/HAP?" | ya / tidak / tergantung HET-HAP | D4 |

Rambu (PANDUAN §4): jangan menyebut "prediksi" atau "sistem peringatan yang tervalidasi". Sebut presisi historis sesudah narasumber menjawab D2/R7:
"dalam evaluasi historis 2024–2026, sekitar 2 dari 10 komoditas yang ditandai daftar ini memang naik tajam relatif terhadap kebiasaannya".

## 4. Matriks pencatatan (satu baris per kebutuhan × narasumber; diisi pewawancara)

```
| Kode | P01 | P02 | P03 | P04 | P05 | Ringkasan (rentang) | Status | Tanggal | Catatan konflik |
|------|-----|-----|-----|-----|-----|---------------------|--------|---------|-----------------|
| R1   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R2   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R3   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R4   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R5   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R6   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R7   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R8   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R9   |     |     |     |     |     |                     | NOT VALIDATED | | |
| R10  |     |     |     |     |     |                     | NOT VALIDATED | | |
| R11  |     |     |     |     |     |                     | NOT VALIDATED | | |
| R12  |     |     |     |     |     |                     | NOT VALIDATED | | |
```

Tabel ambang R2 per komoditas memakai tabel PANDUAN §6 (satu per narasumber). Ringkasan = median dan rentang per komoditas × horizon.
Narasumber dicatat dengan kode dan peran saja (PANDUAN §3).

Aturan pengisian status:
1. Tiap sel narasumber diisi jawaban apa adanya (kutipan pendek atau angka), bukan tafsiran agent.
2. Status dihitung sesudah semua wawancara, dengan aturan §1. Satu narasumber tidak pernah menghasilkan VALIDATED.
3. Jawaban yang bergantung pada kondisi ("tergantung musim", "kalau dekat HET") dicatat sebagai syarat. Bila kondisinya tidak dapat dihitung dari
   data proyek, status maksimal PARTIALLY VALIDATED.
4. Hasil dirangkum dalam catatan bertanggal `docs/audit/` dan keputusan D-xxx sebelum dipakai mengubah model.

## 5. Dari jawaban ke keputusan K4

| Jawaban (VALIDATED) | Keputusan |
|---|---|
| R2/R3 = relatif per komoditas, besarnya di sekitar P70–P90 | K4-E80 dapat dibawa ke validasi prospektif apa adanya. Satu model P80 mengurutkan P70–P90 sama baiknya (TARGET_SENSITIVITY §2) |
| R2/R3/R4 = seragam (persen atau rupiah) atau terhadap HET/HAP | K4-E80 **tidak dipakai**. Protokol baru dengan target kebijakan dimulai dari Data Understanding |
| R12 = kenaikan 1–3% komoditas diatur tidak relevan | Target per komoditas dengan ambang minimum (lantai) kebijakan; protokol baru |
| R5 = kenaikan kapan pun dalam jendela | K4-A80 menjadi kandidat utama (AP dev 0,353 / 0,359; test h 8 > K4-E80) |
| R6 = K | Laporkan satu titik operasi (presisi/recall pada K itu); jangan menyetel K dari test |
| R7 = r | τ* = 1/(1 + r) bila memakai peluang; bila r ≤ 2, posisikan daftar sebagai pemantauan pasif |
| R8 = urutan | Kalibrasi bukan syarat; tampilkan peringkat + kategori kasar |
| R8 = angka | Hanya h 4; h 8 tidak boleh sampai ada informasi rezim (CALIBRATION_DEEP_AUDIT) |
| R9 = keputusan sebelum Jumat | `available_at` dimajukan; fitur intraminggu dinilai ulang (D-152) |
| R10/R11 | Menentukan isi kartu dan jalur tinjauan manusia ([OPERATIONAL_SPECIFICATION.md](OPERATIONAL_SPECIFICATION.md)) |
| R1 = dua arah penting | Kartu baru untuk penurunan tajam; di luar lingkup K4 |
| Status CONFLICTING pada R2/R6/R7 | Laporkan rentang; pakai opsi paling konservatif (K terkecil, ambang tertinggi); jangan memilih yang paling menguntungkan metrik |

FINDINGS: Instrumen siap. Semua 12 kebutuhan berstatus NOT VALIDATED. Tiga di antaranya (R2/R3/R4) dapat membatalkan pemakaian K4-E80 sama
sekali.

EVIDENCE: Dokumen audit di folder ini; PANDUAN; BUSINESS_REQUIREMENTS D-164.

STATISTICAL VALIDITY: Tidak berlaku (instrumen kualitatif). Aturan konsensus ≥ 3 wawancara dari PANDUAN §7.

BUSINESS IMPLICATION: Tanpa jawaban R2–R7, setiap klaim kegunaan K4 bagi TPID hanya hipotesis.

DECISION: **Pertahankan** status operasional BLOCKED.

BLOCKERS: U109 `[HUMAN]`: 3–5 wawancara TPID/BI provinsi.

NEXT ACTION: Danen/Abi menjadwalkan wawancara dengan PANDUAN + sisipan §3. Hasil dicatat di matriks §4.
