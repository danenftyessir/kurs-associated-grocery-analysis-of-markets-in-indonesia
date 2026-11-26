# Protokol D-158 iterasi 2 — perbaikan atas kelemahan iterasi 1 (EKSPLORATIF)

Ditulis & di-hash sesudah hasil iterasi 1 (`hasil/ev_nl_br_*.csv`: NL1, NL2, NL_BR, BR_NAT, BR_LOC semua Δ −0,008..+0,003, 0 lolos) dan
sesudah layar DU iterasi 2 (`hasil/diag_national.csv`, `lead_du.csv`, `fresh_du.csv`, layar nasional increment-only), sebelum run modeling
iterasi 2. Tidak ada prediksi kandidat iterasi 2 sebelum protokol ini.

## 1. Kelemahan iterasi 1 (bukti)

| ID | Kelemahan | Bukti |
|---|---|---|
| W1 | Lapisan nasional terpisah lebih lemah dari konsensus C1-tuned sendiri; kalibrasi ulang dari histori merusak (base rate tidak stasioner) | AUC arah nasional: konsensus C1t 0,762 / 0,755 (mingguan 2021–2023) vs nat_hat HGB 0,760 / 0,734, kalibrasi logistik + dummy komoditas 0,742 / 0,698, increment dinamika 0,751 / 0,751, kota pemimpin 0,73 / 0,72 |
| W2 | Satu-satunya informasi baru adalah kesegaran (harga akhir minggu); breadth Δp mingguan kota tidak memprediksi arah nasional | `kb_up_1` ρ parsial +0,087 / +0,064 tetapi turun ke 0,047 / 0,038 bila dikontrol keluarga intraminggu; increment-only dengan breadth intraminggu: AUC nasional h 4 0,762 → 0,777–0,781, akurasi 0,698 → 0,709; h 8 tidak naik |
| W3 | Banyak fitur lemah ke HGB menambah derau | BR_NAT (9 fitur) −0,006 / −0,008, BR_LOC −0,005 / −0,006 |
| W4 | Penyusutan baris ragu ke konsensus tidak membantu | akurasi baris |p − 0,5| < 0,05: sendiri 0,536 / 0,544 vs konsensus 0,485 / 0,535; blending α < 1 menurunkan macro F1 monoton |

## 2. Kandidat iterasi 2 (daftar tetap)

| ID | Peran | Isi | Menjawab |
|---|---|---|---|
| META_FR | kandidat | koreksi nasional increment-only di atas konsensus C1t: q = σ(L + γ·x), x = [kb_iw_med, kb_iw_up, iw_gap_nat] terstandar; γ walk-forward (refit 4 minggu, ≥ 52 minggu, baris t' + h ≤ r, tanpa intersep/dummy); lalu logit p' = logit p_C1t + β·(γ·x) per provinsi, β walk-forward (regresi logistik offset) pada baris provinsi mingguan OOS t' + h ≤ origin | W1, W2 |
| META_CITY | kandidat | sama, x = [kb_iw_med, kb_iw_up] (kota saja) | W2 (kontribusi kota) |
| META_IW | acuan | sama, x = [iw_gap_nat] (keluarga intraminggu provinsi) | pembanding |
| FR_CITY | kandidat | C1t + iw_gap + iw_gap_nat + kb_iw_up, kb_iw_med, kp_iw_up, kp_iw_med (HGB) | W2 |
| FR_REF | acuan | C1t + iw_gap + iw_gap_nat (HGB) | pembanding FR_CITY |
| BR1 | kandidat | C1t + kb_up_1 saja (HGB) | W3 |

Definisi kota (`fresh_du.py`): iwc = log harga hari teramati terakhir minggu t − log rerata minggu t per kota; kb_iw_up / kb_iw_med = porsi
iwc > 0 / median iwc lintas kota nasional; kp_* = sama di kota provinsi itu; iw_gap_nat = rerata iw_gap provinsi (komoditas × minggu).
Harga s.d. Jumat minggu t (ketersediaan sama dengan harga provinsi). Hyperparameter tetap; tidak ada pencarian.

## 3. Aturan
Sama dengan PROTOKOL_I1 §3 (D-156 §5); q BH dalam keluarga 6 varian iterasi 2. Keluarga intraminggu sudah memakai test dua kali → test
tidak dibuka; bila kandidat lolos, konfirmasi hanya lewat prediksi maju beku. Acuan (META_IW, FR_REF) tidak dapat dipilih.
Kebocoran: fitur kota lolos perturbasi/penghapusan (`kb_leak.csv` setelah perbaikan; fitur intraminggu kota memakai hari s.d. Jumat minggu t
yang sama dengan `iw_gap`); γ & β hanya dari label terealisasi.
