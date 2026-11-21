---
dari: Danen
ke: Ardell, Abi
jenis: TERBIT
terkait: D-100, D-101, U24, U100, 20261120-1617_danen-ke-semua_data-mentah-drive.md
status: terbuka
dibuat: 2026-11-20 20:10
tenggat_respon: 2026-11-21
---

# Data mentah & artefak Tahap 0 sudah ada di Drive tim

## Ringkasan
Folder Drive tim kini berisi `data/raw/` (23 dari 24 file sumber + `checksums.csv`) dan empat artefak Tahap 0. Struktur
folder sama dengan path di repo, jadi `drive-pull-raw` / `drive-pull` dan notebook bisa langsung membacanya. Satu file
belum ada: zip FAOSTAT (14 MB), diunggah manual oleh Danen.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Data mentah 13 folder sumber + `checksums.csv` | Drive tim `data/raw/<sumber>/` | snapshot 2026-11-20 | 23/24 file; isi sama dengan `checksums.csv` |
| `faostat/SUA_Crops_Livestock_E_Asia.zip` | Drive tim `data/raw/faostat/` | – | BELUM ada; Danen menyeretnya manual |
| `pihps_daily` | Drive tim `data/interim/pihps_daily.parquet` | WP-03 | tidak dikirim ke juri |
| `panel_weekly`, `world_prices_weekly` | Drive tim `data/processed/` | WP-03, WP-05 | 157.760 sel; 3.096 baris |
| `eligibility` | Drive tim `results/stage0/eligibility.csv` | WP-04 | 337/340 layak |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada.

## Yang perlu dilakukan penerima

**Ardell**
- [ ] Setelah token Drive siap (U100): `python -m kagami drive-pull-raw` lalu `python -m kagami drive-pull stage0`.
- [ ] Sebelum token siap: buka folder Drive tim di browser dan unduh `data/` secara manual ke folder project.

**Abi**
- [ ] Pastikan bisa membuka folder Drive tim dengan akun Anda (dibagikan terbatas, bukan lewat tautan publik).

## Cara memverifikasi
```powershell
python -m kagami drive-pull-raw
```
Hasil yang diharapkan: file yang belum ada terunduh ke `data\raw`; lalu `python -m kagami status` menampilkan 20 sumber
bertanda `[x]` (setelah zip FAOSTAT diunggah Danen).

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| File mentah di Drive | 23 dari 24 + `checksums.csv` | `checksums` |
| Artefak Tahap 0 di Drive | 4 | `pihps_daily`, `panel_weekly`, `world_prices_weekly`, `eligibility` |

## Batasan, risiko, yang belum beres
- Diunggah lewat antarmuka web Google Drive, bukan `drive-push-raw` (token belum ada, U100). Saat token siap, `drive-push-raw`
  akan melewati file dengan MD5 sama, jadi tidak ada duplikat.
- `drivers_weekly` belum ada (menunggu WP-06).
- Pembaruan 2026-11-20 20:45: zip FAOSTAT sudah diunggah Danen ke `data/raw/faostat/` → data mentah di Drive lengkap 24/24.
- Folder Drive tim harus tetap dibagikan terbatas ke akun anggota (U24).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
