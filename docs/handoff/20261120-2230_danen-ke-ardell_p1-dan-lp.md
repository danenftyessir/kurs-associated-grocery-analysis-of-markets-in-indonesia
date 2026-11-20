---
dari: Danen
ke: Ardell
jenis: TERBIT
terkait: WP-06, WP-08, WP-09, WP-13, P1, D-106, D-107
status: terbuka
dibuat: 2026-11-20 22:30
tenggat_respon: 2026-11-22
---

# P1 (episode, penggerak, panel wilayah) + `build_design`/`fit_lp` siap

## Ringkasan
Artefak P1 sudah dihasilkan dari data asli, sehari lebih awal dari jadwal: `drivers_weekly` dengan kolom `episode`,
`episodes`, `fx_variation`, dan `panel_weekly_region`. Kode LP (`build_design`, `fit_lp`, `fx_self_response`) juga sudah lolos
tes sintetis, dua hari lebih awal dari jadwal 22 Nov. WP-15/16/17 dan WP-25/26 bisa berpindah dari sintetis ke data asli.
Artefak masih lokal di mesin Danen dan kode belum di-commit. Danen akan mengunggah artefak ke Drive tim dan mendorong kode ke `feat/`.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `drivers_weekly` | lokal Danen → Drive tim `data/processed/` (menyusul) | WP-05 + WP-06 | 516 minggu (2017-01-02..2026-11-16), kolom `episode` 0/1 |
| `episodes` | lokal → Drive `results/stage0/` (menyusul) | WP-06 | 13 episode; kolom ekstra `peak_week`, `n_trigger_weeks`, `in_period` |
| `fx_variation` | lokal → Drive `results/stage0/` (menyusul) | WP-06 | per tahun 2018–2026 + `total` |
| `panel_weekly_region` | lokal → Drive `data/processed/` (menyusul) | WP-08 | 32.480 baris = 7 × 10 × 464 minggu; indeks log |
| `mde` | lokal → Drive `results/stage0/` (menyusul) | WP-09 | 240 baris; SEMENTARA sampai G6 |
| `src/models/local_projection.py` | branch `feat/episode-panel-mde` → PR ke `dev` | WP-13 sebagian | `build_design`, `regressors`, `fit_lp`, `fx_self_response` |

## Perubahan kontrak
- Artefak/kolom/skema: aditif. `episodes` + `peak_week`, `n_trigger_weeks`, `in_period`; `fx_variation` + `n_weeks`, `n_zero_weeks`,
  `max_de`, `min_de`, `n_episode_weeks`; `mde` + `unit` (`ALL` atau nama wilayah), `se_beta`, `gamma`, `n_weeks`, `n_obs`.
- `configs/*.yaml`: tidak ada.
- Fungsi publik yang berubah signature (aditif, keyword-only, pemanggil lama tetap jalan):
  `local_projection.build_design(..., *, elig=None, unit_col=None, price_col=None)`;
  `power.compute_mde(cfg, panel, region_panel, drivers, world=None, elig=None)`. Fungsi baru: `local_projection.regressors`,
  `power.null_se`, `power.gate_g_power`.

## Yang perlu dilakukan penerima
- [ ] Setelah Danen mengunggah ke Drive: `python -m kagami drive-pull stage0` (atau unduh manual), lalu jalankan ulang kode
  WP-25/26 dengan `drivers_weekly` asli (kolom `episode` bukan 0 lagi).
- [ ] WP-15 `region_profiles`: panggil `build_design(cfg, region_panel, drv, world, com, h, L, unit_col="region",
  price_col="log_price_index")` lalu `fit_lp` per wilayah (contoh pola: `power.compute_mde`).
- [ ] WP-15 `province_deviations`: kirim panel deviasi dengan kolom `dev` (terdeteksi otomatis) atau sebut `price_col`;
  sertakan `elig=` agar hanya seri eligible yang dipakai (cabai rawit 31 provinsi).
- [ ] Konvensi nama regresor (D-107): blok kurs berawalan `de`/`dw`, kontrol `dp_l*`, `db_l*`, `idf_*`, `month_*`. Jangan
  menamai ulang kolom ini, karena `power.null_se` bergantung padanya.
- [ ] Jangan menjalankan `fit_lp` pada data asli untuk level nasional sampai MDE resmi selesai setelah G6. Profil wilayah
  dan deviasi provinsi juga ikut aturan "MDE sebelum β" (CLAUDE.md §24).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_local_projection.py tests/test_panel.py tests/test_power.py tests/test_drivers.py
```
Hasil yang diharapkan: semua lolos; `python -m kagami status` menunjukkan `episodes`, `drivers_weekly`, `fx_variation`,
`panel_weekly_region`, `mde` tersedia.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Jumlah episode depresiasi 2018–2026 | 13 (61 minggu) | `episodes` |
| Episode terbesar | Mar–Mei 2020, Σ de maks 0,185 | `episodes` |
| Minggu depresiasi / apresiasi / nol 2018–2026 | 259 / 200 / 5 | `fx_variation` |
| γ(4), γ(8), γ(12) | 1,44 / 1,32 / 1,03 | `mde` (kolom `gamma`) |
| MDE_PT(8) nasional bawang putih / gula / minyak goreng | 2,52 / 0,90 / 0,465 | `mde` |
| Minggu wilayah kosong | 2022-05-02 (Idulfitri) di 5 wilayah → NaN | `panel_weekly_region` |

## Batasan, risiko, yang belum beres
- MDE dihitung dengan params sebelum G6 (21 Nov). Hasil gerbang sementara: LP tetap utama, karena minyak goreng 0,465 < 0,5.
  Minyak goreng dekat ambang, jadi perubahan varian/lag di G6 bisa membalik keputusan. Keputusan resmi G-power ada di 23 Nov.
- `national_profiles` (WP-13) belum ada. Bootstrap WP-16 yang memanggilnya masih menunggu.
- Episode 13 (2026-11-02) bisa terpotong oleh freeze.
- Pembaruan 2026-11-20 22:50: kelima artefak di tabel "Yang diserahkan" sudah ada di Drive tim (`data/processed/`,
  `results/stage0/`), jadi kotak pertama bisa langsung dikerjakan. Kode masih menunggu commit Danen.
- `stage0` kini menjalankan tabel WP-07 paling akhir, sehingga stub WP-07 tidak lagi menahan artefak Danen. Signature fungsi
  `reference.py` tidak berubah.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
