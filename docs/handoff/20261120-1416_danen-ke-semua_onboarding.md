---
dari: Danen
ke: Ardell, Abi
jenis: ONBOARDING
terkait: WP-00, WP-35
status: terbuka
dibuat: 2026-11-20 14:16
tenggat_respon: 2026-11-21
---

# Skeleton KAGAMI siap — langkah pertama Ardell & Abi

## Ringkasan
Skeleton proyek KAGAMI (kode berlapis, 6 notebook, dokumen agent, tes) sudah selesai; WP-00 s.d. WP-05 dan WP-12 ✅.
Ardell mulai jalur B (WP-07, WP-25) dan Abi mulai jalur C (email BI, cek endpoint PIHPS, data manual, naskah praregistrasi).

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Kode + dokumen | repo `danenftyessir/kurs-associated-grocery-analysis-of-markets-in-indonesia`, branch `main` | commit import skeleton (setelah di-push Danen) | data mentah tidak ada di repo (`.gitignore`) |
| Data mentah | Drive bersama `MyDrive/kagami/data/raw/` | snapshot 2026-11-18/19, hash di `data/raw/checksums.csv` | disiapkan Danen (PEMBAGIAN_TUGAS §8) |
| Artefak yang sudah ada | Drive `MyDrive/kagami/` (`data/interim/`, `data/processed/`, `results/stage0/`) | dibuat dari kode di atas | `pihps_daily`, `panel_weekly`, `eligibility`, `world_prices_weekly` |
| Pembagian tugas & jadwal | `docs/PEMBAGIAN_TUGAS.md` | – | PIC per WP juga ada di papan `docs/WORKPLAN.md` |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada (kontrak awal; lihat `src/utils/artifacts.py` & `docs/ARCHITECTURE.md` §5).
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature: tidak ada.

## Yang perlu dilakukan penerima

**Ardell**
- [ ] Clone repo, buat branch `ardell/setup`, jalankan `pip install -e ".[dev]"` lalu `pytest` (79 passed per 2026-11-20 14:16; tes loader di-skip bila data mentah belum disalin).
- [ ] Salin `MyDrive/kagami/data/raw/` ke `data/raw/` di clone (tidak di-commit), lalu `python -m kagami status`.
- [ ] Baca `CLAUDE.md` (§0, §3.0, §4.6, §6, §9), `docs/PEMBAGIAN_TUGAS.md`, heading WP-07 & WP-25 di `docs/WORKPLAN.md`.
- [ ] Mulai WP-07 (tabel referensi, NaN-aman bila CSV manual Abi belum ada) dan WP-25 (fitur as-of dengan data sintetis/`panel_weekly`).

**Abi**
- [ ] Baca `docs/PEMBAGIAN_TUGAS.md` §6 (daftar tugas & skema CSV data manual) dan `docs/PROJECT_OVERVIEW.md`.
- [ ] Kirim email permohonan izin ke BI (U13, sekaligus tanyakan hosting privat U24); catat tanggal kirim lewat handoff `KEPUTUSAN`/`BLOKIR` atau chat.
- [ ] Cek apakah endpoint `WebSite/TabelHarga/GetGridDataDaerah` = fitur unduh resmi PIHPS (U19); laporkan ke Danen.
- [ ] Mulai data manual §6.2 (prioritas: PADG 7/2026 untuk U3, populasi provinsi, n_kota) dan naskah praregistrasi (G6 = 21 Nov).

## Cara memverifikasi
```powershell
python -m kagami status
```
Hasil yang diharapkan: 18 sumber mentah bertanda `[x]`; artefak `checksums`, `pihps_daily`, `panel_weekly`, `eligibility`,
`world_prices_weekly` bertanda `[x]` bila folder artefak dari Drive ikut disalin.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Sel panel mingguan | 157.760 (34 provinsi × 10 komoditas × 464 minggu) | `panel_weekly` |
| Seri layak | 337/340 (tidak layak: cabai rawit Aceh, Sumbar, Kepri) | `eligibility` |
| Periode | 2018-01-01 s.d. 2026-11-16 (minggu ISO) | `panel_weekly` |

## Batasan, risiko, yang belum beres
- WP-06 (episode) belum dikerjakan, sehingga `drivers_weekly` belum ada; Ardell memakai penggerak di memori dengan `episode = 0` sementara sampai P1 (21 Nov).
- Varian, bobot pakan, dan grup fokus masih PROVISIONAL sampai G6 (D-011, D-012, D-013); minyak goreng sudah FINAL (D-023).
- Agent tidak boleh commit/push; semua command git dijalankan anggota sendiri (CLAUDE.md §4.6).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
