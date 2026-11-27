# Audit red flag juri — perbaikan poin 4–7, 9, 10 (2026-11-27, D-168)

Baca-saja terhadap artefak resmi. `src/`, `tests/`, `configs/`, dan semua artefak di `results/` (kecuali teks `findings.md`) tidak
berubah. Tidak ada estimasi baru di `results/`; angka baru dihitung dari artefak resmi oleh `scripts/analisis.py` dan disimpan di
`hasil/`.

| Poin | Red flag | Perbaikan | Bukti |
|---|---|---|---|
| 4 | Eksplorasi Task 4 mendominasi dan mengaburkan RQ | `findings.md` disusun ulang: RQ1–RQ5 dan E2 di badan utama; seluruh eksplorasi Task 4 dipindah ke Lampiran A dengan pertanyaan penghubung yang eksplisit; Ringkasan butir 6–7 lama digabung menjadi satu butir eksploratif | `results/findings.md` |
| 5 | Periode uji 2024+ dibuka berulang | Buku besar pembukaan test (D-139/141/142 sebelum split; D-145, D-146, D-147, D-151, D-154, D-164) + Holm atas 10 perbandingan sebagai satu keluarga. Lolos: C1-tuned > TimesFM (0,008 / 0,008), daftar pantau > aturan naif (< 0,001 / 0,004), K4 h 4 (0,045). Gugur: `iw_gap`, `IW_NAT`, K4 h 8 | `hasil/buku_besar_test.csv`; findings A.1 |
| 6 | Kalibrasi pasca-G6 tampak seperti mencari signifikansi | Uji ukuran leave-one-out di bawah null pada 48 sel nasional: positif palsu per sel ±1,96·SE 8,8% (maks 17,6%), terkalibrasi 4,4% (maks 4,8%); replikasi null dengan ≥ 1 temuan BH 17,1% vs 0,5%. Kalibrasi melebarkan interval pada 41/48 sel (median crit 2,28). Data asli 7 sel / 4 temuan BH vs harapan null 2,0 / 0,01. Ringkasan butir 1 kini mengutip interval resmi lebih dulu; klaim yang hanya bergantung pada tingkat 2 disebut eksplisit | `hasil/size_kalibrasi.csv`; findings "Kalibrasi inferensi" |
| 7 | Hasil nol tanpa cerita manfaat | Batas atas dalam Rupiah untuk skenario rupiah melemah 5% (PT resmi, h 4 & 8) dan harga sawit dunia +10% (ω minyak goreng). 6/10 komoditas punya batas atas ≤ 4,7% (± Rp90–940) dalam 8 minggu | `hasil/batas_rupiah.csv`; findings "Makna bagi pengguna" |
| 9 | Kebaruan dataset lemah | `docs/DATASHEET.md` (datasheet for datasets) + bagian "Dataset turunan" di findings: kontribusi = panel terintegrasi dengan status sel, as-of, regulasi bertanggal & berstatus verifikasi | `docs/DATASHEET.md` |
| 10 | Validasi prospektif tak terlihat juri | Bagian "Validasi prospektif" di findings (app hal. 6): tabel prediksi beku + commit + jam, perintah pemeriksaan integritas, jadwal, batas daya | findings; `docs/audit/20261127_prospective_validation/` |

> **Koreksi 2026-11-27 (D-169, review eksternal).** "± Rp90–940" pada poin 7 berarti "sekitar", bukan interval simetris. Yang benar:
> batas atas kenaikan +0,25% s.d. +4,65% (+Rp89 s.d. +Rp938) untuk 6 komoditas; interval tidak simetris (beras −Rp170..+Rp89).
> `findings.md` sudah memakai bentuk ini; teks di atas tidak diubah.

## Catatan metode

- **Batas Rupiah.** Harga acuan = median antarprovinsi dari rerata harga teramati 8 minggu s.d. 2026-11-16 (seri layak).
  Perubahan = exp(PT(h) · ln 1,05) − 1 dengan PT nasional dan interval resmi `profiles`. Ini skenario bersyarat dari pola historis.
- **Ukuran kalibrasi.** Untuk setiap sel, replikasi plasebo r dinilai seperti data asli: p = max((1 + #{replikasi lain ≥ |t_r|}) / n,
  p normal), sesuai aturan D-129. Komoditas non-fokus punya 199 replikasi, komoditas fokus 499. Keluarga BH dinilai pada 199
  replikasi yang memuat ke-48 sel. Ukuran interval resmi tidak dapat diuji, karena butuh bootstrap per replikasi plasebo.
- **Buku besar.** Angka dari DECISIONS. Bila hanya q BH dilaporkan, q dipakai sebagai p (konservatif). Bila hanya interval
  bootstrap, p ≈ pendekatan normal dari lebar interval.
- **Galat skrip yang diperbaiki sebelum dilaporkan.** Versi pertama menghitung sel NaN (komoditas dengan 199 replikasi) sebagai
  "tidak menolak", sehingga memberi 6,6% / 3,0%. Angka di atas adalah versi yang sudah diperbaiki.

Jalankan ulang: `python docs/audit/20261127_redflag_juri/scripts/analisis.py` (± 10 detik).
