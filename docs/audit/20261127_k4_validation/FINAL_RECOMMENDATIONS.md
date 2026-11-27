# Validasi K4 — Rekomendasi akhir

Tanggal 2026-11-27, catatan bertanggal. Dasar: dokumen di folder ini + D-164. `[HUMAN]` = tugas manusia; agent hanya menyiapkan bahan.

STATUS: **PARTIAL**: K4 layak sebagai skor ranking eksploratif; **belum layak diadopsi** untuk penggunaan operasional.

## 1. Yang sudah layak

| Komponen | Alasan | Batas |
|---|---|---|
| Label & target K4-E80 sebagai materialitas statistik | Implementasi sesuai dokumentasi; y/z identik dengan panel; target tak teramati 4 baris, dampak ≤ 0,0004 | Hanya proxy statistik |
| Ranking K4-E80 h 4 | ΔAP > C1-tuned terbukti di dev & test; ≥ C1t di setiap K, rezim, dan 29/34 provinsi; kokoh di P70–P90, bertanda, kejadian | Hanya untuk ambang relatif per komoditas |
| Satu model P80 untuk keluarga target statistik | K4 khusus P70/P90/bertanda tidak lebih baik dari K4-E80 pada targetnya (selisih −0,012..+0,020) | Bukan untuk ambang seragam |
| Ranking h 8 sebagai indikasi | Searah (ΔAP test +0,015, ΔPresisi@K3 test +0,019 dengan interval > 0) | ΔAP tidak terbukti |

## 2. Yang belum layak

| Komponen | Alasan |
|---|---|
| **Penggunaan operasional apa pun** | U109: 0 dari 12 kebutuhan tervalidasi; ambang seragam akan membatalkan K4-E80 |
| Angka peluang h 8 | Ekor atas terlalu yakin di dev dan test; tidak ada kalibrator yang memperbaiki Brier |
| Angka peluang h 4 dalam persen | ECE baik, tetapi model hanya menangkap ± 30% pergeseran laju per minggu; Brier skill test 0,075 kecil. Tampilkan sebagai kategori relatif saja |
| Kalibrator C1–C6 | 0/6 lolos aturan; ECE turun, Brier tidak |
| Pengecualian komoditas bawang | Dipilih dari dev yang sama; perlu prospektif |
| Klaim "peringatan dini" | Presisi test 0,17–0,20; r ≤ 2 tanpa alarm lebih murah |

## 3. Yang harus diperbaiki / dilakukan (urut prioritas)

| # | Tindakan | Siapa / kapan | Mengapa |
|---|---|---|---|
| 1 | **Commit `hasil/k4_forward_preds.csv` + `k4_forward_manifest.json`** (status git: dimodifikasi / belum dilacak). Minggu target pertama (2026-11-23, h 4 origin 2026-10-26) sedang teramati minggu ini | `[HUMAN]` Danen, **hari ini 2026-11-27** | Tanpa commit bertanggal sebelum target, validasi prospektif tidak dapat dibuktikan independen |
| 2 | Wawancara TPID/BI provinsi (3–5) dengan PANDUAN + sisipan R1–R12 | `[HUMAN]` Danen/Abi | Menentukan target, K, r, bentuk tampilan |
| 3 | Skrip evaluasi prospektif yang **menghitung label dari panel baru dengan `thr_*` beku** (kolom `z_*` beku = 0, bukan label); baris tanpa target dikeluarkan dan dilaporkan | Agent, sesudah target h 4 lengkap (2026-12-18) | Mencegah semua alarm terbaca salah |
| 4 | Laporkan presisi@K, AP, reliabilitas kategori pada prediksi maju: K4-E80 vs C1-tuned vs laju-dasar komoditas; uji aturan tampilan bawang di sana | Agent, 2026-12-18 (h 4) dan 2027-01-15 (h 8) | Satu-satunya bukti independen |
| 5 | Bila U109 memilih ambang seragam/kebijakan: protokol baru dari Data Understanding (target kebijakan), bukan memakai ulang K4-E80 | Sesudah #2 | TARGET_SENSITIVITY §3 |
| 6 | Bila U109 memilih kejadian dalam jendela: K4-A80 sebagai kandidat, protokol prospektif terpisah | Sesudah #2 | AP dev 0,353 / 0,359; test h 8 > K4-E80 |
| 7 | Bila angka peluang dibutuhkan (R8): kartu informasi rezim ex-ante (tanggal perubahan HET/HAP sebelum origin), oracle dulu | Sesudah #2 | Ekor h 8 berasal dari pemutusan kebijakan; kalibrator tidak dapat menangkapnya |
| 8 | Perbarui klaim di `results/findings.md`/makalah: peluang K4 h 4 hanya kategori relatif; h 8 tanpa angka; ranking K4 bergantung pada ambang relatif | Sesudah keputusan user (findings beku sesudah 27 Nov kecuali bug) | Konsistensi klaim |

## 4. Kriteria adopsi (semua wajib)

1. U109: R2, R3, R5, R6, R7 berstatus **VALIDATED** (aturan konsensus PANDUAN §7), dan definisi target yang divalidasi cocok dengan target model
   (atau model dilatih ulang untuk target itu dengan protokol baru).
2. Validasi prospektif pada prediksi maju beku (≥ 12 origin di kedua horizon): presisi@K (K dari R6) K4 ≥ C1-tuned **dan** ≥ laju-dasar
   komoditas pada titik estimasi, dan AP K4 > laju-dasar dengan interval > 0. Konfirmasi +0,045 AP pada h 4 butuh lebih banyak origin daripada 12.
   Hasil 12 origin hanya dibaca sebagai penjaga arah, bukan uji, seperti D-152.
3. Bila peluang ditampilkan: Brier kategori/peluang h 4 prospektif < laju-dasar komoditas, dan realisasi kategori "tinggi" > "sedang" > "rendah".
4. Biaya: r yang divalidasi (R7) berada di wilayah di mana daftar lebih murah daripada tanpa alarm (r ≳ 3–5 menurut D-164).
5. Kartu alarm dan tinjauan manusia ([OPERATIONAL_SPECIFICATION.md](OPERATIONAL_SPECIFICATION.md)) disetujui pengguna; tidak ada aksi otomatis.
6. Keputusan adopsi dicatat sebagai D-xxx sebelum K4 masuk `src/` atau app.

## 5. Kriteria penolakan (salah satu cukup)

1. U109 memilih ambang seragam/absolut atau terhadap HET/HAP, dan tidak ada protokol baru → K4-E80 ditolak untuk tujuan itu.
2. Prospektif: presisi@K K4 < laju-dasar komoditas, atau < C1-tuned, pada kedua horizon.
3. R7 menunjukkan r ≤ 2 (alarm palsu sama mahal dengan kenaikan terlewat) → daftar pantau tidak sepadan. Posisikan sebagai pemantauan
   pasif atau hentikan.
4. Kategori risiko tidak monoton pada prospektif (realisasi "tinggi" ≤ "sedang").
5. Rezim baru (perubahan kebijakan besar) membuat presisi bergulir 13 minggu < laju-dasar komoditas (penjaga spesifikasi §8).

## 6. Yang tidak direkomendasikan

- Menyetel ulang K4 atau menambah fitur histori harga untuk mengejar AP (D-156: batas informasi sama).
- Memilih K, τ, kalibrator, atau pengecualian komoditas dari test 2024+ atau dari dev yang sama tanpa prospektif.
- Menampilkan p_up C1-tuned sebagai peluang kenaikan (D-155).
- Memasukkan K4 ke `src/` atau app sebelum kriteria adopsi 1–6.
- Menulis "sistem peringatan dini", "prediksi kenaikan", atau "peluang harga naik X%" (CLAUDE.md §20).

DECISION: **Pertahankan** status D-164: PARTIAL secara teknis, **BLOCKED** operasional. Revisi kecil: peluang h 4 hanya sebagai kategori relatif.
Kalibrasi ekor h 8 dengan kalibrator monoton ditolak sebagai jalan keluar.
