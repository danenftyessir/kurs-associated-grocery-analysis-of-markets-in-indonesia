---
dari: Danen
ke: Ardell
jenis: KEPUTUSAN
terkait: D-118, WP-13, WP-16, WP-28
status: terbuka
dibuat: 2026-11-21 15:30
tenggat_respon: 2026-11-23
---

# LP nasional kini ± 6 dtk (hasil identik) → bootstrap WP-16 ± 50 menit untuk B = 499

## Ringkasan
`lp.national_profiles` dipercepat dari ± 23–29 dtk menjadi **± 6 dtk** per panggilan, tanpa mengubah satu angka pun (D-118).
Bootstrap & plasebo WP-16 yang memanggil `national_profiles` per replikasi kini ± 50 menit untuk B = 499 (sebelumnya ± 3,2 jam
dari handoff `20261120-2353_danen-ke-ardell_lp-event-qa.md`). Aturan "bila > 30 menit, B = R = 199 untuk non-fokus" tetap berlaku,
tetapi dengan runtime ini B = 499 untuk komoditas fokus sudah realistis dalam satu sesi Kaggle.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `national_profiles`, `build_design` (API sama) | `src/models/local_projection.py` | `dev` setelah merge branch Danen | desain tanpa horizon dibangun sekali per spesifikasi |
| `ols_cluster` (skor cluster via bincount) | `src/stats/regression.py` | idem | hasil sama |
| Bundle Kaggle | `dist/kagami_code.zip` | 2026-11-21 | Danen unggah ulang ke dataset `kagami-code` |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada. Signature `build_design`, `fit_lp`, `national_profiles` tidak berubah.
- Bukan DEVIASI PRAREGISTRASI (implementasi numerik; hasil identik).

## Yang perlu dilakukan penerima
- [ ] Ardell: tarik `dev` terbaru sebelum mengukur runtime WP-16; perkiraan baru ± 6 dtk × B per run bootstrap nasional.
- [ ] Ardell: bila WP-15 butuh LP per provinsi/deviasi, pakai `build_design` (kini ± 0,05 dtk per komoditas × horizon) atau minta
      Danen menambah jalur cepat serupa untuk banyak horizon (handoff `PERMINTAAN`).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_local_projection.py
```
Hasil yang diharapkan: semua lolos, termasuk `test_national_profiles_fast_path_equals_design_loop` (jalur cepat = loop
`build_design` + `fit_lp`, toleransi 1e-10).

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Runtime `national_profiles` (10 komoditas × 13 h × 2 spesifikasi, lokal) | 28,7 → 5,9 dtk | profil cProfile 2026-11-21 |
| Selisih hasil data asli (598 baris profiles) | estimasi 0, SE 0 | perbandingan sebelum/sesudah |
| Tier 1 / `mde` | selisih ≤ 2·10⁻¹² / ≤ 2·10⁻¹⁵ | idem |
| Perkiraan bootstrap B = 499 | ± 50 menit (lokal; Kaggle serupa) | 5,9 dtk × 499 |

## Batasan, risiko, yang belum beres
- Waktu di Kaggle bisa berbeda dari laptop; ukur dengan B kecil (mis. 9) dulu.
- Resampling blok di `joint_bootstrap` sendiri (pembentukan panel per replikasi) belum termasuk perkiraan ini.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
