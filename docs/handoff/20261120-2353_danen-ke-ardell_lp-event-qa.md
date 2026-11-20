---
dari: Danen
ke: Ardell
jenis: TERBIT
terkait: WP-10, WP-11, WP-13, WP-14, D-109, D-110, 20261120-2230_danen-ke-ardell_p1-dan-lp.md
status: terbuka
dibuat: 2026-11-20 23:53
tenggat_respon: 2026-11-22
---

# G6 beku, LP nasional & event study siap, laporan Tahap 0

## Ringkasan
Praregistrasi sudah beku sejak 2026-11-20 23:29 WIB (D-109). Varian, bobot pakan, dan 5 grup fokus tidak berubah; H5 memakai
koreksi Holm. `national_profiles` (WP-13) dan event study (WP-14) siap dipanggil `task1`, sehingga WP-16 bisa langsung memakai
estimator nasional yang asli. `stage0` sekarang hanya tertahan di tabel WP-07 milikmu.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `local_projection.national_profiles` | `src/models/local_projection.py` (menyusul di `dev`) | WP-13 | 598 baris, 23 dtk untuk 10 komoditas × 13 h × 2 spesifikasi |
| `event_study.event_paths`, `placebo_starts`, `placebo_bands` | `src/models/event_study.py` (menyusul di `dev`) | WP-14 | dipanggil `task1` untuk level national & region |
| `stage0_report` | lokal Danen `results/stage0/stage0_report.md` | WP-10 | cakupan, kelayakan, episode, MDE, QA |
| Config beku | `configs/params.yaml`, `configs/commodities.yaml` | G6 | sha256 di `docs/PREREGISTRATION.md` §5 |

## Perubahan kontrak
- Artefak/kolom/skema: aditif. `events` + `n_placebo`; baris `profiles` nasional + `n_obs`.
- `configs/*.yaml`: `forecast.h5_correction: holm` (baru, G6). Config kini beku, jadi setiap perubahan dicatat sebagai DEVIASI PRAREGISTRASI.
- Fungsi publik yang berubah signature (aditif, keyword-only): `national_profiles(..., *, elig=None, horizons=None, commodities=None)`;
  `event_paths/placebo_bands(..., *, elig=None)`. `task1` sudah meneruskan `elig`.

## Yang perlu dilakukan penerima
- [ ] WP-16 `joint_bootstrap`: estimator `lp.national_profiles(cfg, pb, db, world, elig=elig)` butuh ± 23 dtk per replikasi, jadi
  B = 499 menghabiskan ± 3,2 jam. Sesuai aturan > 30 menit, pakai B = 199 untuk non-fokus (`bootstrap_B_nonfocus`) lewat argumen
  `commodities`, dan/atau paralelkan dengan `joblib`. Catat sebagai D-2xx.
- [ ] WP-16 `circular_placebo`: panggil `national_profiles(..., horizons=cfg.params["lp"]["key_horizons"])`, cukup h 4/8/12.
- [ ] WP-16 `bootstrap_ci`: baris PT memiliki se/ci NaN. Interval PT hanya dari persentil rasio replikasi (METHODS §M1.2).
- [ ] WP-25/26: `params.forecast.h5_correction` dipakai di evaluasi H5 (WP-27, Danen); tidak perlu diubah di kodemu.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_local_projection.py tests/test_event_study.py tests/test_qa.py
```
Hasil yang diharapkan: semua lolos. `python -m kagami stage0` berhenti di `NotImplementedYet: WP-07`.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| MDE_PT(8) nasional bawang putih / gula / minyak goreng | 2,52 / 0,90 / 0,465 → LP tetap utama | `mde` |
| Runtime `national_profiles` | 23 dtk | – |
| Kandidat awal plasebo event study | 164 minggu unik | `events` (via `placebo_starts`) |
| Lonjakan satu hari ditandai | 59 hari | `stage0_report` |
| Total impor BPS bulanan vs tahunan | 241/241 cocok (rasio 1,000) | `stage0_report` |

## Batasan, risiko, yang belum beres
- Daging ayam β_e(8) = −1,67 (SE cluster, −2,62 s.d. −0,73), negatif. Jangan ditafsirkan sebelum cek robustness tanpa Mar–Jun 2020 (WP-28).
- Kode baru belum ada di `dev`; Danen akan commit dan merge ke `dev` (branch `feat/`).
- `stage0_report` belum diunggah ke Drive tim.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
