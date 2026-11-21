---
dari: Danen
ke: Ardell, Abi
jenis: KEPUTUSAN
terkait: D-007, D-115, U8, WP-09, WP-13, G-power
status: terbuka
dibuat: 2026-11-21 14:00
tenggat_respon: 2026-11-23
---

# Gerbang G-power: LP tetap utama; H2 konfirmatori untuk beras & daging sapi

## Ringkasan
Gerbang G-power (jadwal 23 Nov) sudah diputuskan lebih awal dari `mde` yang dihitung dengan config beku G6. **LP mingguan tetap
analisis utama**, karena syarat "MDE PT(8) > 0,5 untuk ketiga komoditas uji" tidak terpenuhi (minyak goreng 0,465). Status uji
asimetri H2 juga sudah ditetapkan: **konfirmatori untuk beras dan daging sapi**, deskriptif untuk 8 komoditas lain.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `mde` (+ kolom `se_asym`, `mde_asym_beta`, `mde_asym_pt`) | `results/stage0/mde.csv` (lokal Danen) | 2026-11-21 | kolom lama identik dengan versi 20 Nov |
| `stage0_report` (+ tabel status H2) | `results/stage0/stage0_report.md` (lokal Danen) | 2026-11-21 | belum di Drive tim |
| Keputusan | `docs/DECISIONS.md` D-115 | – | menutup D-007 dan U8 |

## Perubahan kontrak
- Artefak/kolom/skema: `mde` + kolom ekstra `se_asym`, `mde_asym_beta`, `mde_asym_pt` (hanya baris nasional; NaN untuk wilayah).
  Kolom wajib tidak berubah.
- `power.gate_g_power` kini juga mengembalikan `h2_confirmatory` per komoditas.
- Bukan DEVIASI PRAREGISTRASI: aturan G-power dan H2 dijalankan sesuai PREREGISTRATION; satu-satunya penafsiran (ambang H2 dalam
  satuan PT) dicatat terbuka di D-115.

## Yang perlu dilakukan penerima
- [ ] Ardell: tidak ada perubahan kode. WP-15/16/17 tetap memakai LP sebagai estimator utama (tidak beralih ke event study).
- [ ] Ardell: app halaman 2/6, tampilkan β⁺/β⁻ beras & daging sapi sebagai uji H2; komoditas lain dengan label "deskriptif".
- [ ] Abi: makalah bagian metode & matriks evaluasi, pakai angka dan kalimat di bawah (sudah sesuai rambu klaim CLAUDE.md §20).

## Cara memverifikasi
```powershell
python -m pytest -q tests/test_power.py
```
Hasil yang diharapkan: semua lolos. `results/stage0/stage0_report.md` bagian 5 memuat "LP tetap UTAMA" dan "H2 konfirmatori: beras, daging_sapi".

## Angka penting
| Besaran (nasional, h = 8, α 0,05, power 0,80) | Nilai | Sumber artefak |
|---|---|---|
| MDE PT(8) bawang putih / gula pasir / minyak goreng | 2,52 / 0,90 / 0,465 | `mde` |
| MDE PT(8) terkecil / terbesar | daging sapi 0,13, beras 0,20 / cabai rawit 3,75 | `mde` |
| MDE asimetri PT(8) (β⁻ − β⁺): daging sapi / beras | 0,32 / 0,44 → H2 konfirmatori | `mde` |
| MDE asimetri PT(8) komoditas lain | minyak goreng 1,01 … cabai rawit 9,34 → H2 deskriptif | `mde` |
| γ(4/8/12) respons kurs pada dirinya | 1,44 / 1,32 / 1,03 | `mde` (kolom gamma) |

Kalimat untuk makalah: "Analisis daya sebelum estimasi menunjukkan selisih pass-through 8 minggu sebesar 0,465 (minyak goreng)
hingga 2,52 (bawang putih) adalah yang terkecil yang dapat terdeteksi pada α 0,05 dan power 0,80. Karena tidak ketiga komoditas uji
melewati ambang 0,5, local projections mingguan tetap menjadi analisis utama. Uji asimetri depresiasi–apresiasi diperlakukan
konfirmatori hanya untuk beras dan daging sapi, yang MDE asimetrinya di bawah 0,5; untuk komoditas lain hasilnya deskriptif."

## Batasan, risiko, yang belum beres
- Ambang H2 dibaca dalam satuan PT. Dalam satuan β, beras (0,59) menjadi deskriptif. Penafsiran ini disebut di makalah.
- MDE besar untuk bawang putih dan cabai: respons tak terdeteksi di komoditas itu adalah batas atas, bukan bukti nol.
- `mde` dan `stage0_report` versi 21 Nov belum diunggah ke Drive tim (Danen: `python -m kagami drive-push stage0` setelah token U100 ada,
  atau unggah lewat browser).

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
