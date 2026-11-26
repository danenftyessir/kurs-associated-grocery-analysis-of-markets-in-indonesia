# National Shock Nowcasting — Breadth Pasar Kota & Model Nasional–Lokal, 2 Iterasi (Task 4 arah, EKSPLORATIF)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-158 · Lanjutan [D-157](20261126_pilot_cuaca_impor.md) atas
rekomendasi Danen (Ide A breadth pasar, Ide B nasional → lokal) dengan dua iterasi mandiri: iterasi 1 = rekomendasi Danen; iterasi 2 =
perbaikan atas kelemahan yang ditemukan agent. Catatan bertanggal. Protokol dibekukan sebelum modeling setiap iterasi:
[PROTOKOL_I1.md](20261126_nasional_lokal/PROTOKOL_I1.md), [PROTOKOL_I2.md](20261126_nasional_lokal/PROTOKOL_I2.md) (hash & waktu di
`hasil/protocol_sha256.txt`). Skrip & hasil: [folder lampiran](20261126_nasional_lokal/). Origin pengembangan saja (≤ 2023); **test 2024+
tidak dibuka**.

## 0. Ringkasan

| Pertanyaan | Jawaban |
|---|---|
| Data kab/kota Bapanas? | **Tidak dapat dipakai** (BLOCKED): portal tanpa tabel/unduhan, harga tidak termuat saat diperiksa; dataset lewat SAPA (terbatas); di repo hanya panel bulanan provinsi 2022+ (tidak mencakup dev 2021). Pengganti: **PIHPS per kota** (BI) — 110 kota harian sejak 2017-03-27, diunduh dengan persetujuan Danen (12.870 permintaan, 0 galat, 3,9 MB) |
| Iterasi 1 (Ide A + B) | 0 / 5 lolos: NL1 −0,002 / −0,003, NL2 −0,003 / +0,003, NL_BR −0,000 / +0,001, BR_NAT −0,006 / −0,008, BR_LOC −0,005 / −0,006 |
| Kelemahan iterasi 1 | W1 lapisan nasional terpisah kalah dari **konsensus C1-tuned sendiri** (AUC arah nasional 0,724 / 0,725 vs 0,733 / 0,752); kalibrasi ulang dari histori **memperburuk**; W2 breadth Δp mingguan kota tidak memprediksi arah nasional — satu-satunya informasi baru adalah **kesegaran** (harga akhir minggu); W3 banyak fitur lemah = derau; W4 menyusutkan baris ragu ke konsensus merusak |
| Iterasi 2 (perbaikan) | Koreksi nasional increment-only di atas konsensus C1t (META_*) +0,009 / −0,005..+0,002 (tidak lolos). Fitur kesegaran HGB: FR_CITY **+0,024 (0,006..0,043) / +0,008 (0,000..0,015)**, lolos aturan; tetapi FR_REF (tanpa data kota, ≈ IW_NAT) +0,024 / +0,004 → **kontribusi kota −0,000 / +0,004 (belum terbukti)** |
| Kesimpulan | Headroom nasional (+0,105) **tidak** dapat dijangkau dengan informasi turunan harga (provinsi maupun kota); C1-tuned sudah memakai komponen nasional yang tersedia. Satu-satunya kenaikan adalah **keluarga intraminggu yang sudah dikenal** (D-147/D-151; test +0,0085 / +0,0033 belum terbukti). **C1-tuned tetap**; FR_CITY/FR_REF dibekukan sebagai prediksi maju (konfirmasi prospektif) |

## 1. Fase 1 — Audit data

**Panel Harga Bapanas** (diperiksa 2026-11-26 lewat browser, baca-saja): beranda menyediakan pilihan jenis panel, wilayah, Kab/Kota, dan
periode untuk peta status; menu hanya "Peta Status Harga Pangan", tidak ada halaman tabel/unduhan, FAQ kosong, dan harga hari itu tidak
termuat ("Harga Belum Tersedia", galat frontend, tidak ada permintaan data). Riset D-150: unduhan dilindungi reCAPTCHA, dataset hanya via
SAPA (akses terbatas, "All Rights Reserved"). Data Bapanas di repo (`bapanas_panel`) bulanan provinsi 2022-01..2026-10 → tidak bisa
dipakai untuk breadth mingguan kota dan tidak menutup origin dev 2021. Status: **BLOCKED** (permintaan data resmi = `[HUMAN]`).

**PIHPS per kabupaten/kota** (BI): tabel "Berdasarkan Daerah" punya filter Kabupaten/Kota; endpoint resmi `GetGridDataDaerah` menerima
`regency_id` (110 kota = kota sampel PIHPS, harga provinsi = gabungannya). Riwayat diperiksa (Kota Bandung 2018-01, Kab. Tasikmalaya 2021-03
berisi; Maret 2017 kosong untuk Bandung). Diunduh dengan persetujuan Danen (`scripts/fetch_kota.py`, turunan skrip D-150; per kota per bulan,
2–3 paralel, 73 menit, **0 galat**) → `data/raw/bi_pihps/pihps_kota_harian_2017-2026_retrieved_2026-11-26.zip` (3,9 MB), didaftarkan
opsional `pihps_city` + `load_pihps_city`. Cakupan 109–110 kota per komoditas sejak 2017-03-27, rerata 2,6 kota per provinsi. Catatan:
kolom `first_date`/`n_dates` di MANIFEST zip bergeser 2 kolom identitas (bug skrip, sudah diperbaiki untuk pengambilan berikutnya; data harga
tidak terpengaruh; berkas mentah tidak diubah).

## 2. Iterasi 1 — rekomendasi Danen

**Ide B** (`nl_build.py`): tahap 1 HGB regresi share_up nasional (porsi provinsi naik) per komoditas × minggu, fitur = rerata lintas provinsi
kolom C1t + breadth provinsi + dispersi + kalender, walk-forward refit 4 minggu (label t' + h ≤ r); tahap 2 C1t + nat_hat (NL1) + kepengikutan
provinsi 104 minggu (NL2). **Ide A** (`kb_build.py`): breadth 110 kota nasional (porsi naik 1/4 minggu, turun, percepatan, median, p90, IQR,
persistensi, cakupan) dan dalam provinsi; NL_BR = tahap 1 + breadth.

Kebocoran: lapisan nasional 0 sel (6 origin, perturbasi fitur & label belum terealisasi). Breadth kota: uji pertama **gagal** — 533.750 sel
berbeda pada uji penghapusan (`kb_cov` 532.100: penyebut = semua kota sepanjang periode; `kp_n` 1.650: 0 vs kosong untuk provinsi yang kotanya
baru melapor kemudian); uji perturbasi harga 0. Diperbaiki (penyebut = kota yang sudah melapor s.d. t; 0 → kosong), run breadth yang sedang
berjalan dihentikan sebelum hasilnya dilihat, uji ulang **0 sel**, run diulang.

Layar DU (`nl_du.py`, `br_du.py`): AUC arah nasional (komoditas × origin dev, z = share_up > 0,5) — konsensus C1t tersirat (rerata p_up
provinsi) 0,733 / 0,752; nat_hat 0,724 / 0,725 (selisih −0,010 (−0,047..0,025) / −0,026 (−0,061..0,000)); breadth provinsi Δp 4 minggu
0,618 / 0,564; tanda Δp nasional 0,591 / 0,551. Baris: hanya `kb_up_1` (porsi kota naik minggu ini) ρ parsial +0,087 (q 0,005) / +0,064
(q 0,10); fitur dalam-provinsi ≈ 0.

| Kandidat (dev) | Δ h 4 (interval) | Δ h 8 (interval) | q BH h 4 / h 8 | Keputusan |
|---|---|---|---|---|
| NL1 | −0,002 (−0,010..0,007) | −0,003 (−0,016..0,008) | 0,84 / 0,88 | ditolak |
| NL2 | −0,003 (−0,011..0,006) | +0,003 (−0,008..0,013) | 0,84 / 0,88 | ditolak |
| NL_BR | −0,000 (−0,007..0,007) | +0,001 (−0,010..0,010) | 0,96 / 0,98 | ditolak |
| BR_NAT | −0,006 (−0,016..0,005) | −0,008 (−0,016..0,001) | 0,80 / 0,37 | ditolak |
| BR_LOC | −0,005 (−0,015..0,005) | −0,006 (−0,014..0,002) | 0,80 / 0,44 | ditolak |

## 3. Analisis kelemahan iterasi 1 (oleh agent)

`diag_national.py`, `meta_build.py`, `lead_du.py`, `fresh_du.py` (hanya dev; tanpa model kandidat):

1. **Di mana headroom berada.** 76% / 78% provinsi searah mayoritas nasional terealisasi; memprediksi semua provinsi dengan mayoritas sejati
   (LOO) → 0,756 / 0,782. Akurasi arah nasional tersirat C1t hanya **0,666 / 0,703** (0,763 / 0,800 saat konsensus yakin, 0,568 / 0,605 saat
   ragu). Mengganti baris ragu (|p − 0,5| < 0,1) dengan mayoritas sejati → 0,707 / 0,720. Jadi bottleneck = **akurasi arah nasional**, dan
   C1t sendiri sudah prediktor nasional terbaik yang ada.
2. **W1 — lapisan nasional terpisah tidak bisa mengalahkan konsensus.** Mingguan 2021–2023 (AUC konsensus 0,762 / 0,755): kalibrasi logistik
   + dummy komoditas 0,742 / 0,698 (base rate tidak stasioner membuat intersep historis menyesatkan); + dinamika konsensus & galat terakhir
   0,740 / 0,701; increment-only (offset = logit konsensus) dinamika 0,751 / 0,751; breadth 0,759 / 0,734; **kota pemimpin** (K 5/10/20 kota
   dipilih walk-forward per komoditas) −0,03..−0,04 (korelasi indeks–galat nasional hanya 0,03–0,09: hubungan pemimpin–pengikut tidak stabil).
3. **W2 — informasi baru hanya "kesegaran".** `kb_up_1` turun ke 0,047 / 0,038 bila dikontrol `iw_gap` & rerata nasionalnya; breadth
   intraminggu kota (porsi kota yang harga hari terakhirnya di atas rerata minggunya) kuat sendirian (ρ parsial 0,11–0,17) tetapi sebagian
   besar sama dengan keluarga intraminggu (sisa `kp_iw_up` 0,051 (q 0,003) / 0,016). Increment-only nasional dengan kesegaran: AUC h 4
   0,762 → **0,777–0,781**, akurasi 0,698 → 0,709; h 8 tidak naik (0,751).
4. **W3 — derau fitur.** BR_NAT (9 fitur) lebih buruk dari NL_BR (1 fitur ringkasan).
5. **W4 — penyusutan ke konsensus** (ditolak di layar): pada baris |p − 0,5| < 0,05 akurasi sendiri 0,536 / 0,544 > konsensus 0,485 / 0,535;
   blending α = 0,75 / 0,5 / 0 → 0,653 / 0,646 / 0,625 (h 4) — monoton turun.

## 4. Iterasi 2 — perbaikan

Rancangan (PROTOKOL_I2): (a) koreksi nasional **increment-only** di atas konsensus C1t, tanpa intersep/dummy (menjawab W1), dengan fitur
kesegaran (W2), lalu pergeseran logit provinsi β·γ·x (β walk-forward dari baris provinsi mingguan OOS; infrastruktur: prediksi C1t mingguan
OOS 2019–2023 dari 65 refit, sama persis dengan resmi pada origin); (b) fitur kesegaran langsung ke HGB, dengan acuan tanpa data kota; (c)
satu fitur breadth (W3).

| Varian (dev) | Peran | Δ h 4 (interval) | Δ h 8 (interval) | q BH h 4 / h 8 | Aturan §5 |
|---|---|---|---|---|---|
| META_FR | kandidat | +0,009 (−0,005..0,022) | −0,004 (−0,018..0,007) | 0,25 / 0,72 | gagal |
| META_CITY | kandidat | +0,010 (−0,004..0,023) | −0,005 (−0,021..0,006) | 0,25 / 0,72 | gagal |
| META_IW | acuan | +0,009 (−0,003..0,020) | +0,002 (−0,009..0,011) | 0,25 / 0,72 | gagal |
| FR_REF (C1t + iw_gap + iw_gap_nat) | acuan | **+0,024 (0,008..0,041)** | +0,004 (−0,003..0,011) | 0,003 / 0,72 | lolos (acuan) |
| FR_CITY (FR_REF + 4 fitur intraminggu kota) | kandidat | **+0,024 (0,006..0,043)** | **+0,008 (0,000..0,015)** | 0,038 / 0,28 | **lolos** |
| BR1 (kb_up_1) | kandidat | −0,001 (−0,010..0,009) | −0,001 (−0,007..0,005) | 0,92 / 0,72 | gagal |

FR_CITY per tahun h 4 +0,039 / +0,015 / +0,021, origin Δ > 0 63% / 68%; semua komoditas ≥ −0,011. **Tetapi** FR_CITY − FR_REF (kontribusi
data kota): −0,000 (−0,007..0,006) / +0,004 (−0,002..0,010), p 0,86 / 0,18 (`hasil/ev_fr_city_vs_ref.csv`). Kenaikan berasal dari keluarga
intraminggu provinsi yang ditemukan pada periode dev yang sama (D-147 P04b +0,014; D-151 IW_NAT +0,020 / +0,005) dan menyusut di test
(IW_NAT +0,0085 / +0,0033, q 0,28 / 0,30). Angka dev ini karena itu **optimistis** (seleksi berulang pada dev yang sama). Koreksi nasional
META: γ positif (kesegaran naik → arah nasional naik), β h 4 stabil ± 0,60 (sd 0,07), h 8 tidak stabil (0,33–1,34); kenaikan h 4 +0,009
sejalan dengan keuntungan AUC nasional, tetapi lebih kecil dari fitur kesegaran langsung dan tidak terbukti.

## 5. Prediksi maju beku (konfirmasi prospektif)

Sesuai PROTOKOL_I2 §3, kandidat dari keluarga intraminggu hanya dikonfirmasi lewat prediksi maju: `scripts/fw_freeze_d158.py` →
`hasil/forward_preds_d158.csv` (12.168 baris: base, FR_REF, FR_CITY; h 4 origin 2026-10-26..11-16, h 8 2026-09-28..11-16 — sama dengan D-152)
+ `forward_manifest_d158.json` (sha256 prediksi, protokol, kode, data). `base` identik dengan base D-152 (4.056 baris, |Δp| 0,0); FR_REF searah
dengan IW_NAT D-152 pada 97,9% baris (korelasi 0,993). **Perlu di-commit sebelum target terealisasi**; dievaluasi sesudah unduh PIHPS baru.
Daya rendah (D-152: konfirmasi +0,0085 butuh ± 14 tahun origin) → hanya penjaga terhadap kegagalan besar.

## 6. Kesimpulan & rekomendasi

1. **Ide A (breadth kota) tidak menambah informasi nasional.** Harga 110 kota hanya menambah "kesegaran" yang sudah tertangkap oleh fitur
   intraminggu provinsi; pemimpin pasar tidak stabil.
2. **Ide B (nasional → lokal) benar arahnya tetapi C1-tuned sudah melakukannya.** Konsensus provinsi C1t adalah prediktor arah nasional terbaik
   (AUC 0,75–0,76); model nasional terpisah atau kalibrasi ulang kalah karena memakai informasi yang sama dan base rate yang bergeser. Bentuk
   yang benar (increment-only di atas konsensus) bekerja hanya bila ada informasi baru (kesegaran h 4).
3. **Headroom +0,105 tetap ada tetapi butuh informasi ex-ante non-harga** tentang arah nasional (pasokan, intervensi bertanggal) — sejalan
   dengan D-157. Data harga yang lebih rinci tidak cukup.
4. **Keputusan: C1-tuned tetap.** FR_CITY tidak diadopsi (kontribusi kota ≈ 0, menambah ketergantungan data kota yang hanya Tingkat C);
   keluarga intraminggu tetap kandidat yang menunggu konfirmasi maju (D-152 + D-158).
5. **Aturan metode baru** (`docs/EKSPERIMEN.md` §3): kandidat tingkat nasional wajib lolos **layar arah nasional** (AUC/akurasi komoditas ×
   minggu vs konsensus C1t, walk-forward) sebelum modeling provinsi; kalibrasi ulang konsensus dengan intersep historis dilarang (base rate
   tidak stasioner).

## 7. Reproduksi

Urutan: `fetch_kota.py` → `nl_build.py` (+ `leak`) → `nl_du.py` → `run_nl.py` STAGE=nl → `kb_build.py` (+ `leak`) → `br_du.py` → `run_nl.py`
STAGE=br → `ev_nl.py nl br` → `diag_national.py`, `c1t_weekly.py`, `meta_build.py`, `lead_du.py`, `fresh_du.py` → PROTOKOL_I2 → `run_nl.py`
STAGE=i2, `meta_eval.py` → `ev_nl.py i2 i2meta` → `fw_freeze_d158.py`. Tabel kerja di `KAGAMI_EXP`. Runtime: unduh 73 menit; tiap tahap HGB
± 9 menit (5 proses × 2 thread); prediksi C1t mingguan 4,5 menit.
