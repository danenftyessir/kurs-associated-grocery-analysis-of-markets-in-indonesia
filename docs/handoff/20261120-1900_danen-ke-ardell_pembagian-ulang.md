---
dari: Danen
ke: Ardell
jenis: SERAH-TERIMA-WP
terkait: D-105, WP-15, WP-16, WP-17, WP-18, WP-21, WP-22, WP-27, P2, P4
status: terbuka
dibuat: 2026-11-20 19:00
tenggat_respon: 2026-11-21
---

# Pembagian tugas diubah: tiap Task dipegang Danen dan Ardell berdua

## Ringkasan
Pembagian awal menaruh seluruh Task 1 di Danen dan seluruh Task 2–4 di Ardell. Mulai sekarang (D-105) tiap Task dipegang
berdua dan beban kira-kira seimbang. Tiga WP Task 1 sisi provinsi (WP-15, 16, 17) pindah ke Ardell; empat WP hilir (WP-18, 21, 22, 27)
pindah ke Danen. Semua tetap bisa dikerjakan paralel dengan data sintetis berskema `src/utils/artifacts.py`.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Papan baru (kolom PIC) | `docs/WORKPLAN.md` | branch kerja Danen | WP-15, 16, 17 → Ardell; WP-18, 21, 22, 27 → Danen |
| Pembagian, kepemilikan file, jadwal, titik terbit | `docs/PEMBAGIAN_TUGAS.md` §1, §3, §4, §5 | – | `association.py` dibagi per fungsi; P2 dijalankan Ardell; P4 dipecah |
| Keputusan | `docs/DECISIONS.md` D-105 | – | bukan deviasi praregistrasi |

Daftar akhir:
- **Danen:** WP-06, 08, 09, 10, 11, 13, 14, 18, 21, 22, 27, 28, 29, 30.
- **Ardell:** WP-07, 15, 16, 17, 19, 20, 23, 24, 25, 26, 31, 32.

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada.
- `configs/*.yaml`: tidak ada. Parameter `inference` & `shrinkage` tetap milik Danen (dibekukan di G6); Ardell memakainya di WP-16/17, perubahan lewat `PERMINTAAN`.
- Fungsi publik yang berubah signature: tidak ada. Kepemilikan berubah: `models/deviations.py`, `evaluation/inference.py`, `features/response.py` → Ardell; `evaluation/heterogeneity.py`, `evaluation/planted.py`, `evaluation/forecast_eval.py`, `pipelines/task3.py`, `models/association.py::kendall_exact` → Danen.

## Yang perlu dilakukan penerima
- [ ] Baca PEMBAGIAN_TUGAS §1, §3–§5 versi baru; balas bila ada keberatan (handoff `PERMINTAAN`) paling lambat 21 Nov.
- [ ] 21 Nov: WP-25 (fitur as-of) + kerangka WP-15/16/17 dengan data sintetis (panel provinsi, profil nasional).
- [ ] 22 Nov: WP-26 dan WP-19 (sintetis); tunggu handoff `TERBIT` Danen untuk `build_design` + `fit_lp` (WP-13).
- [ ] 23 Nov: WP-15 dengan data asli memakai `fit_lp`; run WP-26 penuh di Kaggle (`forecast_preds`).
- [ ] 24 Nov: WP-16 + WP-17, jalankan `task1` penuh → terbit P2; WP-07 final → terbit P3. Serahkan `ward_labels` & `select_k` (WP-19) ke Danen paling lambat 23 Nov.
- [ ] Pakai satu branch `feat/<topik>` per WP (D-103); satu file dibagi per fungsi dengan Danen (PEMBAGIAN_TUGAS §3).

## Cara memverifikasi
```powershell
python -m kagami status
```
Hasil yang diharapkan: tidak ada perubahan artefak; hanya dokumen yang berubah. Cek PIC di papan `docs/WORKPLAN.md`.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| WP Danen / Ardell | 14 / 12 | `docs/WORKPLAN.md` |
| Beban perkiraan per orang | ± 19 satuan kerja | D-105 |

## Batasan, risiko, yang belum beres
- Rantai Task 1 (WP-13 → 15 → 16 → 17) kini melewati dua orang; bila WP-13 telat dari 22 Nov, WP-15 tetap jalan dengan sintetis dan dijalankan asli setelah `fit_lp` terbit.
- Handoff onboarding lama (`20261120-1416_danen-ke-semua_onboarding.md`) masih memuat daftar WP pembagian awal; daftar WP di dokumen ini yang berlaku.
- Menunggu konfirmasi Ardell; Abi tidak terdampak.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
