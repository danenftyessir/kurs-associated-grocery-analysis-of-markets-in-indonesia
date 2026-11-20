---
dari: Danen
ke: Ardell, Abi
jenis: KEPUTUSAN
terkait: D-101, WP-07, U5, U14, U103, U104
status: terbuka
dibuat: 2026-11-20 16:17
tenggat_respon: 2026-11-21
---

# Data mentah pindah ke Drive tim + 3 dataset baru untuk WP-07

## Ringkasan
Semua data mentah kini didistribusikan lewat `data/raw/` di folder Drive tim (D-101): tidak perlu minta/kirim manual.
Masuk juga dataset baru (BPS impor v2 dengan bawang putih, revisi regulasi, jarak ke hub, konkordansi HS, produksi
hortikultura) yang menjadi input WP-07; tugas pengumpulan populasi manual Abi gugur.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Semua data mentah (21 sumber) + `checksums.csv` | folder Drive tim `data/raw/` | snapshot 2026-11-20 (25 file) | tersedia setelah Danen menjalankan `python -m kagami drive-push-raw` |
| `bps_import_monthly` v2 | `data/raw/bps_trade/bps_import_hs8_monthly_2023_2026_v2.csv` | 2026-11-20 | 111 kode HS8; 59 baris bawang putih 070320 (v1: 16) |
| `het_hap_current`, `regulation_history` | `data/raw/manual_regulation/*_2026-11-20.csv` | revisi 2026-11-20 | 30 & 23 baris; nomor BN & URL diperbarui |
| `hortikultura_produksi` (baru) | `data/raw/kementan_hortikultura/` | ATAP 2024 | produksi bawang merah/putih, cabai besar/rawit per provinsi 2020–2024 |
| `konkordansi_hs` (baru) | `data/raw/manual_concordance/` | 2026-11-20 | 15 kode Comtrade → HS8 BPS + keyakinan |
| `jarak_hub` (baru) | `data/raw/manual_geo/` | 2026-11-20 | 38 provinsi, jarak ke Jakarta/Surabaya/Makassar |
| Loader & tes | `src/data/loaders.py` (`load_hortikultura`, `load_konkordansi_hs`, `load_jarak_hub`), `tests/test_loaders.py` | – | semua lolos |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- `configs/*.yaml`: `sources.yaml` +3 sumber baru, 3 path diganti ke versi baru; `runtime.yaml` + `kaggle.raw_dir`, `colab.raw_dir`.
- Fungsi publik yang berubah signature: tidak ada. Fungsi baru: `utils.drive.push_raw`, `utils.drive.pull_raw`; CLI `drive-push-raw`, `drive-pull-raw`.

## Yang perlu dilakukan penerima

**Ardell**
- [ ] Setelah token Drive siap: `python -m kagami drive-pull-raw` (hanya mengunduh file yang belum ada).
- [ ] WP-07: pakai `hortikultura_produksi` untuk rasio impor bawang putih (U5), `konkordansi_hs` untuk menyambung impor Comtrade 2017–2022 ke HS8 BPS, `jarak_hub` sebagai cek silang `dist_hub_km`. Tambah parameter fungsi di `reference.py` bila perlu, lalu kirim handoff `PERMINTAAN` ke Danen untuk menyesuaikan `pipelines/stage0.py`.

**Abi**
- [ ] Coret pengumpulan populasi provinsi (PEMBAGIAN_TUGAS §6.2): CSV penduduk 2025 BPS sudah diunduh Danen (U14/U103).
- [ ] Lanjutkan verifikasi regulasi yang tersisa (U6): sumber HET Minyakita Rp15.700, tanggal diundangkan Perbadan 4/5/6/2024, teks Kepbadan 299/2025, nomor & tanggal HET beras premium.

## Cara memverifikasi
```powershell
python -m kagami drive-pull-raw
```
Hasil yang diharapkan: pesan `[drive] pull-raw: N file -> ...data\raw`; lalu `python -m kagami status` menampilkan 21 sumber bertanda `[x]`.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Sumber mentah terdaftar | 21 (25 file) | `checksums` |
| Baris bawang putih 070320 di impor BPS bulanan | 59 (v1: 16) | `bps_import_monthly` |
| Produksi hortikultura | 780 baris, 2020–2024 | `hortikultura_produksi` |

## Batasan, risiko, yang belum beres
- Data baru ada di Drive setelah Danen menjalankan `drive-push-raw` dengan token (U100); sebelum itu, hanya di laptop Danen.
- Menunggu Danen: unggah CSV penduduk 2025 & snapshot kab/kota Panel Harga ke lokasi yang sudah dialokasikan (U103); cek keaslian Pink Sheet (U101); keputusan `pihps_v1` yang ditandai "rusak" (U104).
- Uji tumpang tindih Comtrade vs BPS 2022 belum bisa (server BPS error, U102): pakai kolom `keyakinan_pemetaan` dan nyatakan sebagai batasan.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
