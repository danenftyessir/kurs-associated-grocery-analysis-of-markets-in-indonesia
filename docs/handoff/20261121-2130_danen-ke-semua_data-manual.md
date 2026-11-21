---
dari: Danen
ke: Semua
jenis: DATA-MANUAL
terkait: D-123, U14, U15, U21, U103, WP-07, WP-23
status: terbuka
dibuat: 2026-11-21 21:30
tenggat_respon: 2026-11-23
---

# Data manual WP-07 sudah lengkap: penduduk 2025, n_kota, faktor GKG→beras

## Ringkasan
Danen sudah mengisi ketiga data manual yang dibutuhkan fitur provinsi Z(r) untuk H3 (D-123), jadi Abi tidak perlu lagi mengisi `n_kota.csv`
dan `gkg_beras.csv`. Setelah `stage0` dijalankan ulang, `province_features` kini lengkap untuk 34 provinsi: keterpencilan, kecukupan beras
2025, dan jumlah kota sampel PIHPS.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Penduduk 2025 per provinsi | `data/raw/bps_kependudukan/penduduk_provinsi_2025.csv` | tabel BPS diperbarui 2 Mei 2025 | 38 provinsi, ribu jiwa, total 284.438,8 ribu |
| Kota sampel PIHPS | `data/raw/manual_pihps/n_kota.csv` | situs PIHPS, diakses 2026-11-21 | 110 kota, 1–12 per provinsi, beserta daftar nama kota |
| Faktor GKG→beras | `data/raw/manual_conversion/gkg_beras.csv` | rilis BPS 2 Feb 2026 | 0,5762 untuk 2024 dan 2025 |
| Fitur provinsi | `data/reference/province_features.csv` | `stage0` 2026-11-21 | rice_sufficiency 0,001 (DKI) .. 3,27 (Sulsel) |

## Perubahan kontrak
- Artefak/kolom: tidak ada. Kolom `rice_sufficiency`, `n_kota`, `rice_production_ton`, `rice_need_ton` di `province_features` kini terisi.
- Bukan DEVIASI PRAREGISTRASI (data input untuk fitur yang sudah dipraregistrasi).

## Yang perlu dilakukan penerima
- [ ] Abi: tidak perlu mengisi `n_kota.csv` dan `gkg_beras.csv` lagi; untuk makalah bagian dataset, sumber dan definisinya ada di
      `docs/DATASETS.md` §Sumber manual WP-07 dan D-123.
- [ ] Ardell: jalankan Task 3 (meta-regresi WP-23) dengan `province_features` versi ini; ketiga fitur praregistrasi sudah tersedia.
- [x] Danen: unggah ketiga file `data/raw/` di atas ke folder `data/raw/` Drive tim (belum ada token Drive lokal) agar anggota lain
      dan notebook mendapatkannya lewat `drive-pull-raw`.

## Cara memverifikasi
```powershell
python -m kagami stage0
```
Hasil yang diharapkan: pesan `[reference] rice_sufficiency tahun 2025, faktor GKG->beras 0.5762`, tanpa pesan NaN untuk populasi atau n_kota.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Penduduk Indonesia 2025 | 284,44 juta jiwa | tabel BPS, D-123 |
| Kota sampel pasar tradisional PIHPS | 110 (Jawa Tengah 12; DKI, DIY, Bengkulu, Maluku Utara 1) | `n_kota.csv` |
| Faktor GKG→beras untuk konsumsi pangan | 0,5762 (rantai BPS 0,9318 × 0,6402 × 0,9667 = 0,5767) | rilis BPS 2 Feb 2026 |
| Kecukupan beras 2025 | 0,001 (DKI) .. 3,27 (Sulsel); median ± 0,85 | `province_features` |
| Korelasi antar fitur Z(r) | \|r\| ≤ 0,34 | `province_features` |

## Batasan, risiko, yang belum beres
- Penduduk 2025 berbasis proyeksi BPS sebelum hasil SUPAS 2025; bila tabel SUPAS per provinsi dipakai, angkanya bisa sedikit berbeda.
- Daftar kota PIHPS adalah kondisi 2026; jumlah kota sampel pada awal periode (2018) bisa berbeda.
- Kebutuhan beras dihitung dari konsumsi rumah tangga saja (tanpa konsumsi di luar rumah tangga), sehingga kecukupan cenderung lebih tinggi.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
