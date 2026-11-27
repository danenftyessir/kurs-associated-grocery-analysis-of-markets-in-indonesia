# Validasi K4 — Audit integritas target

Tanggal 2026-11-27, catatan bertanggal. Skrip `scripts/v_target.py` (baca-saja), keluaran `hasil/ti_*.csv`. Protokol: [PROTOCOL_ADDENDUM.md](PROTOCOL_ADDENDUM.md) §2.

STATUS: **COMPLETE**

OBJECTIVE: Memastikan bahwa label z K4-E80 dibentuk seperti yang didokumentasikan. Fokus utamanya target yang tidak teramati: apakah benar
diberi label negatif, ikut latih atau tidak, dan seberapa besar dampaknya bila penanganannya dikoreksi.

## 1. Kode yang membentuk label

`scripts/k4_common.py::split_k4` (D-164):

```python
train = t[(t["week"] + h <= o) & np.isfinite(t[src])]          # latih: hanya target terealisasi
test  = t[t["week"] == o]                                        # evaluasi: semua seri dengan lag pada o
d["z"] = (np.isfinite(v) & (v >= th)).astype(int)                # NaN → 0
```

- **Latih:** baris tanpa target dibuang. Tidak ada target tak teramati yang masuk latih sebagai negatif.
- **Evaluasi:** baris tanpa target ikut universe dengan z = 0, sesuai dokumentasi D-155 dan TARGET_DEFINITION §5. Jadi label negatif untuk
  target tak teramati **benar-benar diterapkan di kode**, tetapi hanya di evaluasi.
- Ambang `thresholds()` memakai baris latih yang sama (y_h dan lag tersedia, week + h ≤ o). Dihitung ulang untuk 3 origin × 2 horizon × 2 bagian:
  selisih maksimum 0.

## 2. Jumlah target tak teramati (`ti_missing_totals.csv`, `ti_missing_rows.csv`)

| Bagian | h 4: baris / tanpa target | h 8: baris / tanpa target | Sebab |
|---|---|---|---|
| dev | 12.800 / **2** | 12.463 / **2** | minggu t + h berstatus `missing` di panel (4 baris, semua komoditas diatur) |
| test | 12.477 / **0** | 12.139 / **0** | – |
| maju (beku) | 1.352 / 1.352 | 2.704 / 2.704 | target belum terjadi (wajar) |

- Per komoditas (`ti_missing_by_commodity.csv`): keempat baris dev ada pada komoditas diatur, ≤ 1 baris per komoditas × horizon. Tidak ada
  konsentrasi per horizon.
- **Jebakan untuk validasi prospektif:** file prediksi maju berisi kolom `z_e80`, `z_a80`, dan lainnya yang seluruhnya 0 karena target belum
  terealisasi. Kolom itu **bukan label**. Evaluasi maju harus menghitung label dari panel baru dengan ambang `thr_*` yang beku. Kalau kolom z beku
  yang dipakai, semua alarm akan terbaca salah.

## 3. Label negatif: apakah benar teramati? (`ti_recompute_checks.csv`, `ti_label_quality.csv`)

y_h dan z di prediksi beku dihitung ulang dari artefak `panel_weekly` (log harga teramati, minggu `missing` = NaN, tanpa isi):

| Cek | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| Pola NaN y sama | ya | ya | ya | ya |
| Maks \|Δy\| | 0 | 0 | 0 | 0 |
| z berbeda | 0 | 0 | 0 | 0 |

Status ujung (t dan t + h) per kelas label, dev h 4 (h 8 dan test serupa):

| Kelas | n | ≥ 1 ujung carry-forward | Kedua ujung carry-forward | Ujung `short` | Porsi komoditas diatur |
|---|---|---|---|---|---|
| positif | 1.535 | 62% | 32% | 0% | 60% |
| naik di bawah ambang | 4.246 | 51% | 28% | 0% | 27% |
| turun | 5.185 | 49% | 27% | 0% | 27% |
| tetap (y = 0) | 1.832 | 100% | 98% | 0% | 92% |
| tanpa target | 2 | – | – | – | 100% |

- Semua negatif kecuali 4 baris berasal dari dua harga yang teramati. Negatif "tetap" hampir seluruhnya dua ujung carry-forward pada komoditas
  diatur. Ini kekakuan harga nyata (U22), bukan data hilang yang disamarkan.
- Ujung berstatus `short` (≤ 2 hari teramati) ≈ 0% di semua kelas. Label yang lemah karena sedikit hari tidak menjadi masalah di K4.
- Label noise yang tersisa adalah sifat target, bukan galat: 7% / 4% positif berada dalam 1 tick dari ambang (DU D-164).

## 4. Universe latih vs evaluasi (`ti_universe_summary.csv`, `ti_universe_per_origin.csv`)

| | dev h 4 | dev h 8 | test h 4 | test h 8 |
|---|---|---|---|---|
| Seri di grid per origin | 340 | 340 | 340 | 340 |
| Seri dengan harga di origin (rerata) | 337,0 | 337,0 | 337,3 | 337,3 |
| Seri di universe (harga + 3 lag) | 336,8 | 336,8 | 337,2 | 337,2 |
| Seri berharga tetapi tanpa lag (tanpa skor), total | 5 | 5 | 2 | 2 |
| Baris latih dibuang karena target hilang (origin terakhir) | 334 dari 97.785 | 337 dari 95.089 | 334 dari 149.037 | 337 dari 146.333 |
| Baris latih y = 0 (origin terakhir) | 15.001 | 9.981 | 22.426 | 14.820 |

- Tiga seri cabai rawit yang tidak layak (Aceh, Sumbar, Kepri) tidak punya harga dan tidak pernah masuk universe. Ini konsisten dengan kelayakan
  Tahap 0.
- Beda universe latih vs evaluasi hanya dua hal, keduanya disengaja: (a) target tak teramati ikut evaluasi sebagai negatif (4 baris dev, 0 test);
  (b) C1-tuned dilatih tanpa y = 0, K4 dengan y = 0. Baris latih yang dibuang karena target hilang hanya 0,2–0,3% dan merupakan minggu `missing`.
- Tidak ada kebocoran baru. Uji perturbasi D-164 (`leak_checks.csv`, 6 origin × h) tetap berlaku karena skrip latih tidak berubah.

## 5. Dampak penanganan yang dikoreksi (`ti_correction_impact.csv`)

Koreksi = baris tanpa target dikeluarkan dari evaluasi (bukan dihitung z = 0). Tidak ada model yang dilatih ulang, karena baris itu memang tidak
ikut latih.

| | dev h 4 asli → koreksi | dev h 8 asli → koreksi | test |
|---|---|---|---|
| Baris berubah | 2 | 2 | 0 |
| Laju positif | 0,1199 → 0,1199 | 0,1325 → 0,1325 | identik |
| AP K4-E80 | 0,3261 → 0,3261 | 0,2897 → 0,2901 | identik |
| Presisi@K2 K4-E80 | 0,293 → 0,293 | 0,2715 → 0,2719 | identik |
| AP C1t / B-CLIM | identik / 0,1845 → 0,1848 | identik / 0,2083 → 0,2086 | identik |
| Brier / ECE K4-E80 (semua baris dev) | 0,0938 / 0,0186 identik | 0,1083 / 0,0416 → 0,0415 | identik |

FINDINGS:
- Target tak teramati memang diberi z = 0, tetapi hanya di evaluasi dan hanya pada 4 baris dev (0 di test). Baris itu tidak ikut latih.
- Dampak koreksi ≤ 0,0004 pada AP dan presisi@K2. Tidak ada keputusan D-164 yang berubah.
- y_h dan z identik dengan hitungan ulang dari panel. Label negatif berasal dari harga teramati. y = 0 adalah kekakuan nyata.
- Risiko nyata ada di masa depan, bukan di hasil sekarang: kolom z pada prediksi maju beku bernilai 0 dan tidak boleh dipakai sebagai label.

EVIDENCE: `hasil/ti_*.csv`; kode `split_k4` di `../20261126_k4_risiko_material/scripts/k4_common.py`.

STATISTICAL VALIDITY: Kuat. Pemeriksaannya bersifat aritmetika (pencocokan persis), bukan inferensi.

BUSINESS IMPLICATION: Tidak ada. Label K4 dapat dipercaya sebagai materialitas statistik. Apakah definisinya sesuai kebutuhan TPID adalah soal
lain (U109, [BUSINESS_REQUIREMENTS_VALIDATION.md](BUSINESS_REQUIREMENTS_VALIDATION.md)).

DECISION: **Pertahankan** penanganan D-164. Hasil resmi tidak diubah. Untuk penerapan berikutnya, baris tanpa target lebih baik dikeluarkan
dari evaluasi dan jumlahnya dilaporkan (aturan untuk protokol baru, bukan revisi D-164).

BLOCKERS: Tidak ada.

NEXT ACTION: Skrip evaluasi prospektif harus menghitung label dari panel terbaru dengan ambang beku. Kolom z beku diabaikan
([FINAL_RECOMMENDATIONS.md](FINAL_RECOMMENDATIONS.md) #3).
