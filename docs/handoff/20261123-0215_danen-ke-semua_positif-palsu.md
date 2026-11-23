---
dari: Danen
ke: Ardell, Abi
jenis: KEPUTUSAN
terkait: D-127, U106, WP-22, WP-13, 20261122-2000_danen-ke-semua_g-het-h2.md, 20261123-0200_danen-ke-ardell_assoc-p-ari.md
status: terbuka
dibuat: 2026-11-23 02:15
tenggat_respon: 2026-11-25
---

# Interval E2 dan H2 dikalibrasi: sebagian besar "temuan" rezim dan asimetri gugur

## Ringkasan
SE cluster minggu terlalu sempit, terutama pada sub-sampel pendek. Interval E2 (`regime_profiles`) kini dikalibrasi dengan 499 plasebo
geser-melingkar, dan interval laporan H2 (`asymmetry`) kini memakai yang lebih lebar antara Wald dan bootstrap (D-127). Akibatnya: tidak ada
perbedaan antarrezim yang lolos koreksi multiplisitas, dan tidak ada asimetri yang intervalnya tidak memuat nol. Angka di handoff
20261122-2000 untuk bawang putih (asimetri) dan E2 tidak berlaku lagi.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Kode | `src/evaluation/regimes.py`, `src/evaluation/asymmetry.py` | lokal Danen 2026-11-23 | tes `tests/test_regimes.py`, `tests/test_asymmetry.py` |
| `regime_profiles` | Drive tim `results/task3/` (versi baru, ID file sama) | `task3` 2026-11-23 | kolom aditif `crit`, `p_placebo`, `q_fdr`, `n_placebo`; 35.392 byte |
| `asymmetry` | Drive tim `results/task3/` (versi baru, ID file sama) | `task3` 2026-11-23 | kolom aditif `wald_ci_low`, `wald_ci_high`, `ci_excludes_zero`; 9.109 byte |
| Bundle kode | `MyDrive/kagami/kagami_code.zip` (Danen) | 2026-11-23, 73 file | belum diekstrak; lihat NOTEBOOKS.md §1 |

## Perubahan kontrak
- Artefak/kolom/skema: aditif (lihat tabel). Kolom wajib tidak berubah; `ci_low/ci_high` kedua artefak kini lebih lebar.
- `configs/*.yaml`: tidak ada. `pyproject.toml`: `joblib>=1.3` menjadi dependensi eksplisit (sudah ikut scikit-learn).
- Fungsi publik yang berubah signature: `regimes.regime_profiles(..., placebo_R=None, n_jobs=-1)` (argumen opsional baru).

## Yang perlu dilakukan penerima
- [ ] Abi: tulis E2 sebagai "tidak ada perbedaan respons antarrezim HET/HAP yang tahan koreksi multiplisitas (q BH minimum 0,145)";
      pola terkuat boleh disebut sebagai eksploratif dengan interval dan p plasebo-nya (tabel di bawah).
- [ ] Abi: H2 ditulis "tidak terdeteksi" untuk semua komoditas; jangan menulis asimetri bawang putih. Daging ayam β_e(8): kutip interval
      resmi −2,62..0,06 (memuat nol), bukan −2,62..−0,73.
- [ ] Ardell: setelah perbaikan U106, jalankan `task3` dan unggah `assoc`, `asymmetry`, `regime_profiles` ke Drive tim (atau minta Danen).
- [ ] Ardell: app/viz yang menampilkan `asymmetry` atau `regime_profiles` cukup membaca `ci_low/ci_high`; tidak perlu perubahan kode.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_regimes.py tests/test_asymmetry.py
```
Hasil yang diharapkan: lolos; di `regime_profiles` lebar interval / (2·se) = `crit` ≥ 1,96.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| E2 sel tidak memuat nol (lama → baru) | 38 → 15 dari 145 | `regime_profiles` |
| E2 crit plasebo (median, maks) | 3,09; 7,05 | `regime_profiles` |
| E2 q BH minimum | 0,145 | `regime_profiles` |
| E2 terkuat: bawang putih, Perbadan 12/2024, β_e(8) | 3,74 (1,83..5,65), p plasebo 0,002, 98 minggu; sampel penuh −0,68 | `regime_profiles` |
| E2: telur ayam, Perbadan 5/2022, ω(4) | −0,89 (−1,47..−0,31), p plasebo 0,002, 78 minggu | `regime_profiles` |
| H2 beras h8 | −0,14 (−0,58..0,47), p Wald 0,49 | `asymmetry` |
| H2 daging sapi h8 | −0,26 (−0,88..0,21), p Wald 0,089 | `asymmetry` |
| H2 bawang putih h8 (deskriptif) | −5,78 (−10,2..3,1), p Wald 0,011, p plasebo 0,022 | `asymmetry` |
| Daging ayam β_e(8) | −1,67 (−2,62..0,06) | `profiles` |

## Batasan, risiko, yang belum beres
- Uji konfirmatori H2 tetap Wald sesuai praregistrasi; hanya interval laporan yang melebar. Kesimpulan konfirmatori tidak berubah.
- p plasebo E2 granular (1/500) dan rezim yang berdekatan berbagi minggu; q BH dilaporkan sebagai deskriptif.
- Meta-regresi provinsi (`assoc`) belum diperbaiki (U106, milik Ardell): sampai itu, kutip interval saja.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
