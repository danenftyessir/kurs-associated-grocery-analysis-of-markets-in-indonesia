---
dari: Danen
ke: Semua
jenis: KEPUTUSAN
terkait: D-124, WP-22, WP-31, WP-33, E2
status: terbuka
dibuat: 2026-11-21 22:30
tenggat_respon: 2026-11-25
---

# E2 (profil respons per rezim HET/HAP) kini diimplementasikan; artefak baru `regime_profiles`

## Ringkasan
Sebelumnya tabel `regulation` tidak dibaca oleh task mana pun, sehingga hipotesis eksploratif E2 belum punya hasil. Kini `task3` menulis
artefak baru `regime_profiles`: β kurs dan ω harga dunia nasional per rezim harga acuan konsumen (HET/HAP), h = 4/8/12 (D-124).
Hasilnya deskriptif, tanpa uji formal.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| Fungsi E2 | `src/evaluation/regimes.py` | `dev` setelah merge branch Danen | `regulation_changes`, `regime_table`, `regime_profiles` |
| Artefak | `results/task3/regime_profiles.csv` | ditulis `python -m kagami task3` | ship = ya; 33 artefak |
| Grafik | notebook `03_task3_association` (sel terakhir) | – | forest h = 8 per komoditas × driver × rezim |

## Perubahan kontrak
- Artefak baru `regime_profiles`: commodity, regime_id, regime_start, regime_end, driver, horizon, estimate, ci_low, ci_high, n_weeks
  (+ label, se, n_obs, baseline_estimate, baseline_in_ci).
- `task3.OPTIONAL` bertambah `world_prices_weekly` dan `regulation`; notebook 03 menariknya otomatis.
- Bukan DEVIASI PRAREGISTRASI (E2 eksploratif, tanpa parameter baru).

## Yang perlu dilakukan penerima
- [ ] Ardell: pertimbangkan menampilkan `regime_profiles` di halaman 4 aplikasi (opsional; `viz.plots.forest` sudah cukup).
- [ ] Abi: di makalah, tulis E2 sebagai eksploratif dan sebutkan batasan tafsir di bawah; jangan menulis "regulasi mengubah respons".

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_regimes.py
```
Hasil yang diharapkan: 3 tes lolos (filter tanggal regulasi, batas rezim, β per rezim pulih pada data sintetis).

## Angka penting
| Besaran | Nilai | Sumber |
|---|---|---|
| Ukuran hasil (data asli lokal, sebelum Task 1 resmi) | 145 baris; 10 komoditas, 3–6 rezim; 4,9 dtk | `regime_profiles` |
| Estimasi sampel penuh di dalam interval rezim | 73% sel | idem |
| Contoh berbeda | bawang putih rezim Perbadan 12/2024 (sejak 2024-09-25) β_e(8) 3,74 (2,40..5,09) vs penuh −0,68 | idem |
| Contoh berbeda | ω(8) telur −1,64 (−2,09..−1,18) dan daging ayam −1,59 (−2,05..−1,13) pada rezim Perbadan 5/2022 (2022-10 .. 2024-06) | idem |

## Batasan, risiko, yang belum beres
- Batas rezim berimpit dengan peristiwa lain (2022: lonjakan harga pangan & pakan dunia), jadi perbedaan antar rezim tidak bisa
  diatribusikan ke regulasi.
- HET minyak goreng mengatur Minyakita/curah, bukan varian Kemasan Bermerk 1 yang dianalisis.
- Rezim 0 adalah "sebelum perubahan pertama di tabel" (tabel regulasi mulai 2020), bukan periode tanpa harga acuan.
- Interval ±1,96·SE cluster minggu (tanpa bootstrap) dan banyak sel → sebagian perbedaan bisa kebetulan; tidak ada koreksi multiplisitas.
- Rezim pendek dilewati otomatis (contoh: relaksasi HET beras April–Juni 2024; HET minyak goreng Maret–Juli 2022).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
