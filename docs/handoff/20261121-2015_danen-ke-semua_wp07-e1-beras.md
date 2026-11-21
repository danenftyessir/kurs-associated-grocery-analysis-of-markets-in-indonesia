---
dari: Danen
ke: Semua
jenis: KEPUTUSAN
terkait: D-120, WP-07, WP-22, WP-32, WP-33, 20261121-1900_danen-ke-ardell_sinkron-dokumen.md
status: terbuka
dibuat: 2026-11-21 20:15
tenggat_respon: 2026-11-23
---

# WP-07 dijalankan pada data asli; rasio impor beras dikoreksi (DEVIASI D-120); E1 sementara tidak terdeteksi

## Ringkasan
Setelah 6 branch Ardell digabung ke `dev`, Danen menjalankan `stage0` lokal (27 dtk) sehingga tabel WP-07 terbit di `data/reference/`.
Ditemukan salah pemetaan di `configs/commodities.yaml` (beku G6): beras memakai item FAOSTAT "Rice" = **padi**, sehingga rasio impor
beras 1,3·10⁻⁶. Diganti ke "Rice, milled" + "Rice, broken" → **0,033** (DEVIASI PRAREGISTRASI D-120, diputuskan sebelum E1 dihitung).
E1 sementara: τ-b PT(8) vs rasio impor = **−0,045** (jackknife −0,65..0,56), p eksak 0,93, n = 10 → tidak ada asosiasi terdeteksi.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `concordance`, `exposure`, `regulation`, `province_features` | `data/reference/*.csv` | `stage0` 2026-11-21 | 10 / 10 / 72 / 34 baris; tabel tim (ship) |
| Pemetaan FAOSTAT beras | `configs/commodities.yaml` | D-120 | hash baru dicatat di PREREGISTRATION |
| E1 sementara | file ini, `docs/WORKPLAN.md` WP-22 | 2026-11-21 | PT(8) titik dari `national_profiles` lokal |

## Perubahan kontrak
- Artefak/kolom: tidak ada. Nilai `exposure.import_ratio_direct` beras berubah 1,3·10⁻⁶ → 0,033.
- DEVIASI PRAREGISTRASI: D-120 (`commodities.yaml`, item FAOSTAT beras).
- `tests/test_reference.py` (Ardell): literal `"Rice"` di data sintetis diganti konstanta `_RICE = "Rice, milled"` agar cocok dengan config
  (hanya itu; logika tes tidak berubah).

## Yang perlu dilakukan penerima
- [ ] Ardell: periksa perubahan kecil di `tests/test_reference.py` di atas.
- [ ] Ardell: atas instruksi Danen, **semua 7 tes merah sudah diperbaiki Danen langsung di `dev`** (suite 287 lolos, 3 dilewati).
      Butir handoff `20261121-1900_danen-ke-ardell_sinkron-dokumen.md` yang sudah dikerjakan Danen: CLAUDE.md §9 (status ✔ + 11 fungsi
      baru, keterangan dari docstring Ardell), §9.1 (32 artefak), §10.1 (`penduduk`, `n_kota`, `gkg_beras`), §16.1 (11 tes), §2;
      `docs/ARCHITECTURE.md` (`forecast_preds` + daftar tes); papan WORKPLAN WP Ardell ⬜ → 🔶. `tests/test_package.py`:
      (a) `test_missing_ship_artifacts_are_reported_and_blocked` kini membandingkan dengan artefak ship yang tidak ada di `read_dirs`
      (gagal di mesin yang sudah menjalankan `stage0`); (b) `test_extracted_package_runs_cli` memakai `-E` + lingkungan asli tanpa
      `KAGAMI_*` (sebelumnya `-I` + PATH Unix → pandas di user site-packages Windows tidak terlihat). Periksa keterangan §9 dan kedua tes.
- [ ] Ardell: entri DEVIASI untuk `association.import_ratio_years` dan `forecast.run_m3` sudah dicatat Danen sebagai D-121
      (atas instruksi Danen); periksa alasannya. Yang tetap milik Ardell: catatan WP di WORKPLAN (angka & kotak "Selesai bila")
      dan entri D-200 (ordinal `imported_input`, dirujuk di `src/data/reference.py` tetapi belum ada di DECISIONS).
- [ ] Ardell: `rice_sufficiency` dan `n_kota` masih NaN; jalankan ulang `stage0` setelah file manual Abi tersedia.
- [ ] Abi: isi `data/raw/manual_pihps/n_kota.csv` dan `data/raw/manual_conversion/gkg_beras.csv` (skema PEMBAGIAN_TUGAS §6.2), kirim lewat Drive.
- [ ] Abi: untuk makalah, E1 ditulis "di antara 10 komoditas yang diamati" dan sebagai angka **sementara** sampai `assoc` resmi terbit.

## Cara memverifikasi
```powershell
python -m kagami stage0
```
```powershell
python -m pytest -q tests/test_config.py tests/test_reference.py
```
Hasil yang diharapkan: `exposure.csv` beras ≈ 0,033; tes lolos, termasuk `test_faostat_items_exist_and_rice_is_milled`.

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Rasio impor langsung 2018–2023 | bawang putih 0,93; gula 0,37; daging sapi 0,29; bawang merah 0,069; beras 0,033; minyak goreng 0,0005; ayam, telur, cabai ≈ 0 | `exposure` |
| Cek silang beras (neraca BPS) | 0,059 | `exposure.import_ratio_neraca` |
| PT(8) nasional (titik, tanpa interval) | cabai merah 1,04; cabai rawit 0,57; gula 0,50; daging sapi 0,012; beras 0,004; minyak goreng −0,17; telur −0,40; bawang putih −0,51; bawang merah −0,62; daging ayam −1,27 | `national_profiles` lokal |
| E1 Kendall τ-b | −0,045 (−0,65..0,56); p eksak dua sisi 0,93; satu sisi (arah E1) 0,60; n = 10 | `kendall_exact` |
| E1 dengan item beras lama | τ-b −0,13 | pembanding D-120 |
| `regulation` | 72 baris, 5 `unverified` (U6) | `stage0` |

## Batasan, risiko, yang belum beres
- PT(8) di atas belum punya interval (bootstrap WP-16 belum dijalankan pada data asli); E1 resmi memakai `response_features` (P2).
- Rasio bawang putih hanya dari tahun 2021 (lihat kolom `source`); cabai merah & cabai rawit berbagi item FAOSTAT (nilai kembar).
- Kalimat makalah yang aman: "Di antara 10 komoditas yang diamati, besarnya pangsa impor tidak berasosiasi dengan PT(8) nasional
  (τ-b = −0,045; p permutasi eksak 0,93)." Jangan ditulis "impor tidak berpengaruh".

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
