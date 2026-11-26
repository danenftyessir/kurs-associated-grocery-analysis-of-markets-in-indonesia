# Protokol D-158 iterasi 1 — National Shock Nowcasting (Ide A breadth kota + Ide B nasional–lokal), EKSPLORATIF

Ditulis & di-hash sebelum run modeling iterasi 1. Sudah dijalankan sebelum protokol: audit data (Bapanas, PIHPS kota), pembangunan
lapisan nasional `nl_build.py`, layar DU Ide B `nl_du.py` (hasil: AUC arah nasional nat_hat 0,724 / 0,725 vs C1-tuned tersirat 0,733 /
0,752), unduh PIHPS kota (persetujuan Danen 2026-11-26). Tidak ada prediksi model lokal kandidat sebelum protokol ini.

## 1. Kartu

| Komponen | Ide A — breadth pasar tingkat kota | Ide B — nasional → lokal |
|---|---|---|
| Problem | Informasi sempurna arah nasional per komoditas × origin bernilai +0,105 (D-157); C1-tuned sudah menyiratkan arah nasional dengan AUC 0,73 / 0,75 | sama |
| Data characteristic | PIHPS 110 kota harian (rata-rata provinsi = gabungan kota) sejak ± 2017–2018; breadth provinsi lemah (AUC 0,56–0,62) | panel provinsi; label nasional share_up per komoditas × minggu |
| Knowledge discovery | Apakah penyebaran kenaikan antar-kota mendahului arah nasional & provinsi? | Apakah memodelkan komponen nasional terpisah memperbaiki klasifikasi lokal? |
| Hypothesis | Rata-rata provinsi menyembunyikan pergerakan awal di sebagian kota | Model gabungan per baris belum memisahkan komponen nasional dari derau provinsi |
| Method | C1-tuned + fitur breadth kota nasional (BR_NAT) / dalam-provinsi (BR_LOC); lapisan nasional + breadth (NL_BR) | Tahap 1 HGB regresi share_up walk-forward (refit 4 minggu); tahap 2 C1-tuned + nat_hat (NL1) + kepengikutan provinsi (NL2) |
| Validation | Δ berpasangan vs C1-tuned, q BH keluarga iterasi 1, konsistensi tahun/origin, per kelas/komoditas; DU nasional: AUC arah nasional vs C1-tuned tersirat | sama |
| Leakage control | Harga kota minggu t (hari teramati s.d. Jumat, sama dengan harga provinsi); tanpa ffill; perturbasi/penghapusan data sesudah origin | tahap 1 hanya label t' + h ≤ r; kepengikutan dari pasangan terealisasi; uji perturbasi 6 origin (`nl_leak.csv`) |
| Decision | Aturan §3 | Aturan §3; ekspektasi ≈ 0 dicatat sebelum hasil (nat_hat tidak lebih baik dari C1-tuned tersirat) |

## 2. Kandidat (daftar tetap)

Pembanding `base` = C1-tuned (`direction_tuned_preds` persis). Origin pengembangan (origin + h ≤ 2023-12-31), split resmi.

| ID | Kolom tambahan di atas C1t |
|---|---|
| NL1 | `nat_hat_h{h}` |
| NL2 | `nat_hat_h{h}`, `follow_h{h}` |
| BR_NAT | breadth kota nasional per komoditas × minggu: `kb_up_1`, `kb_up_4`, `kb_down_4`, `kb_accel` (kb_up_4 − kb_up_4 4 minggu lalu), `kb_med_4`, `kb_p90_4`, `kb_disp_4` (IQR), `kb_persist` (porsi kota Δp_1 > 0 di t dan t − 1), `kb_cov` (porsi kota valid) |
| BR_LOC | BR_NAT + dalam provinsi: `kp_up_4`, `kp_disp_4` (sd; NaN bila 1 kota), `kp_n`, `kp_rel_up_4` (kp_up_4 − kb_up_4) |
| NL_BR | `nat_hat_br_h{h}` = lapisan nasional yang sama dengan fitur BR_NAT ditambahkan ke tahap 1 |

Harga kota mingguan = rerata hari teramati varian representatif (`commodities.yaml: variant`), Δp_k = log p_t − log p_{t−k} (kedua minggu
teramati; tanpa isi). Hyperparameter C1-tuned & lapisan nasional (`NAT_HGB`) tetap; tidak ada pencarian.

## 3. Aturan (sama dengan D-156 §5)
Δ macro F1 rerata ≥ +0,005, interval > 0 di ≥ 1 horizon, Δ ≥ 0 di lainnya; q BH < 0,05; Δ ≥ 0 di ≥ 2 dari 3 tahun & origin Δ > 0 ≥ 0,5;
F1 naik/turun ≥ −0,01; tidak ada komoditas < −0,03 di kedua horizon. Skala Danen dilaporkan. Test tidak dibuka di D-158: bila ada kandidat
lolos, konfirmasi hanya lewat prediksi maju beku (Danen: test 2024+ bukan test independen).

## 4. Iterasi 2
Sesudah hasil iterasi 1, agent menganalisis kelemahan, menulis protokol iterasi 2 (`PROTOKOL_I2.md`, di-hash sebelum run) dengan kandidat
baru yang ditujukan pada kelemahan itu.
