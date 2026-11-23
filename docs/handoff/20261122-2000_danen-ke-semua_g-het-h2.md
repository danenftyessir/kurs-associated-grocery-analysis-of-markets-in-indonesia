---
dari: Danen
ke: Semua
jenis: KEPUTUSAN
terkait: D-125, U105, WP-13, WP-18, WP-21, WP-22, WP-23
status: terbuka
dibuat: 2026-11-22 20:00
tenggat_respon: 2026-11-24
---

# Gerbang G-het diputuskan, H2 diuji resmi (artefak baru `asymmetry`), batas deteksi struktur tertanam belum boleh dikutip

## Ringkasan
Output Task 1 Ardell (Drive tim, 2026-11-22) lolos pemeriksaan kontrak. `task2` dan `task3` sudah dijalankan lokal di atasnya.
G-het: H0-Het ditolak untuk telur ayam dan daging ayam saja. Clustering k = 1. Uji Wald H2 sebelumnya belum punya kode, kini
diformalkan (D-125); beras dan daging sapi tidak menunjukkan asimetri. Kurva struktur tertanam terlalu optimistis (U105).

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Hasil Task 2 | `results/task2/*` (lokal Danen) | `task2` 2026-11-22, 650 dtk | belum diunggah ke Drive tim |
| Hasil Task 3 | `results/task3/assoc.csv`, `asymmetry.csv`, `regime_profiles.csv` (lokal Danen) | `task3` 2026-11-22, 635 dtk | belum diunggah ke Drive tim |
| Uji H2 | `src/models/local_projection.py::asymmetry_wald`, `src/evaluation/asymmetry.py` | branch Danen | tes `tests/test_asymmetry.py` |
| Grafik H2 | notebook `03_task3_association` (sel terakhir) | – | forest β⁺ − β⁻ |

## Perubahan kontrak
- Artefak baru `asymmetry` (34 artefak): commodity, horizon, estimate (= β⁺ − β⁻), se, ci_low, ci_high, p_value, confirmatory, reject
  (+ beta_pos, beta_neg, z, mde_asym_beta, boot_ci_low, boot_ci_high, n_boot, p_placebo, n_placebo, n_weeks, n_obs). ship = ya.
- `task3.OPTIONAL` bertambah `placebo_stats` dan `mde`; notebook 03 menariknya otomatis.

## Yang perlu dilakukan penerima
- [ ] Ardell: cek `meta_regression` (WP-23): `p_value` tampaknya dari SE CR2, sedangkan interval = yang lebih lebar dari bootstrap & CR2,
  sehingga p bisa kecil padahal interval memuat nol (contoh cabai rawit, ln_dist_hub, h = 12: p 0,005, interval −1,06..1,13).
  Samakan dasar p dengan interval yang dilaporkan, atau tulis alasannya.
- [ ] Ardell: tampilkan `asymmetry` (h = 8) di halaman 2 aplikasi bersama A8 (opsional).
- [ ] Abi: tulis hasil di bawah dengan rambu §20; jangan mengutip batas deteksi struktur tertanam sampai U105 selesai.

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_asymmetry.py tests/test_heterogeneity.py
```
Hasil yang diharapkan: semua lolos (4 tes H2 + tes heterogenitas).

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| G-het telur ayam (h = 8) | Q 161,7 (p95 null 88,7), p 0,004, q 0,040, I² 0,80 → ditolak | `heterogeneity` |
| G-het daging ayam (h = 8) | Q 132,6 (p95 null 77,5), p 0,010, q 0,050 (tepat di ambang) → ditolak | `heterogeneity` |
| G-het lainnya | gula q 0,067; 7 komoditas q ≥ 0,24 (5 dengan τ² = 0) | `heterogeneity` |
| Clustering | k = 1; silhouette maks 0,184 (k = 3) < p95 plasebo 0,196 | `cluster_selection` |
| H2 beras (konfirmatori) | β⁺ − β⁻ (8) −0,14 (−0,55..0,26), p 0,49 | `asymmetry` |
| H2 daging sapi (konfirmatori) | −0,26 (−0,56..0,04), p 0,089 | `asymmetry` |
| E1 resmi | τ-b −0,045 (jackknife −0,65..0,56), p eksak 0,93 | `assoc` |
| H3 (gabungan, h = 4, ln jarak hub) | 0,007 (−0,022..0,033), p satu sisi 0,80 → tidak didukung | `assoc` |
| Daging ayam β_e(8) | −1,67; bootstrap −2,62..0,06; p plasebo 0,002 | `profiles`, `placebo_stats` |
| Minyak goreng ω(4), ω(12) | 0,16 (0,02..0,28), 0,31 (0,02..0,47) | `profiles` |
| Kalibrasi plasebo nasional | |t| > 1,96 pada 8,1% replikasi (nominal 5%) | `placebo_stats` |

## Batasan, risiko, yang belum beres
- Penolakan daging ayam tepat di ambang q = 0,05: rapuh, tulis apa adanya.
- U105: matriks plasebo untuk struktur tertanam sudah tersusut EB (42% kolom konstan per replikasi), sehingga recovery 1,0 bahkan pada
  δ = 0,1. Perbaikan yang diusulkan: tanam δ pada deviasi plasebo mentah, lalu susut EB & z-score seperti data asli.
- Interval bootstrap dan p plasebo kadang memberi kesan berbeda (daging ayam β_e(8): interval memuat nol, p plasebo 0,002); laporkan
  keduanya.

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
