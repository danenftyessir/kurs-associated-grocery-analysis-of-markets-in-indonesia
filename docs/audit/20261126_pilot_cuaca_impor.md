# Pilot Cuaca Sentra Produksi & Realisasi Impor — Task 4 Arah (EKSPLORATIF)

Tanggal: 2026-11-26 · Pelaksana: Danen (dengan agent) · Keputusan: D-157 · Lanjutan [D-156](20261126_task4_master_f1.md) atas usulan
Danen (prioritas: informasi pasokan yang tidak dimiliki histori harga). Catatan bertanggal (bukan dokumen hidup). Protokol + kartu
eksperimen dibekukan sebelum run modeling: [PROTOKOL.md](20261126_pilot_cuaca_impor/PROTOKOL.md) (hash di `hasil/protocol_sha256.txt`;
adendum pasca-hoc §5 di-hash sebelum dijalankan). Skrip & hasil: [folder lampiran](20261126_pilot_cuaca_impor/).

## 0. Ringkasan

| Pertanyaan | Jawaban (origin pengembangan ≤ 2023; test tidak dibuka) |
|---|---|
| Seberapa besar ruangnya? | Informasi **sempurna** tentang arah nasional per komoditas × origin (threshold dari provinsi lain, LOO) → +0,105 / +0,105; hortikultura saja +0,049 / +0,042; impor +0,024 / +0,028; pakan +0,027 / +0,017; beras +0,002 / +0,007 (`hasil/headroom.csv`). Akurasi hortikultura +5 poin ≈ +0,017 keseluruhan; beras +10 poin hanya +0,007 / +0,008 (7–8% baris) |
| Cuaca di sentra (W_NAT, 6 fitur) | −0,003 (−0,015..0,011) / −0,003 (−0,013..0,003); baris hortikultura −0,004 / −0,003 → **tidak membantu** |
| + cuaca provinsi sendiri (W_LOC, 12 fitur) | +0,002 (−0,009..0,013) / −0,003 (−0,014..0,007) → tidak membantu |
| Realisasi impor (IMP, 4 fitur) | −0,006 (−0,017..0,005) / **−0,015 (−0,027..−0,004)**, q 0,017 → **lebih buruk** (beras −0,04 / −0,05, daging sapi −0,05 h 4) |
| Koreksi logit pasca-hoc (W_CAL) | −0,003 / −0,005; hortikultura −0,009 / −0,016; Brier & log-loss juga memburuk → korelasi residual di layar DU tidak tergeneralisasi walk-forward |
| Keputusan | 0 / 3 kandidat (+ 1 pasca-hoc) lolos → **C1-tuned tetap**; test tidak dibuka. Sumber `nasa_power` tetap terdaftar opsional |

## 1. Data

- **NASA POWER** (`nasa_power`, opsional, didaftarkan di `configs/sources.yaml` & `docs/DATASETS.md`): 34 CSV harian 2016-01-01 ..
  2026-11-20, 3,6 MB, 0 nilai hilang; titik = centroid poligon terbesar tiap provinsi (`scripts/fetch_power.py`, `MANIFEST.csv`
  dengan sha256). 2023 tahun terkering di titik Jawa Barat (El Niño).
- **Bobot sentra** = porsi produksi ATAP per provinsi (`hortikultura_produksi`, 2020–2024): stabil, korelasi porsi 2020 vs 2021–2024
  0,95–0,99 (cabai besar, cabai rawit, bawang merah), 0,90–0,95 (bawang putih).
- **Impor** = Comtrade 2017–2022 + BPS 2023-01 .. 2026-09, keranjang dari `commodities.yaml`. Volume beras melonjak 2018 (2,25 juta t),
  2023 (3,06), 2024 (4,52); bawang putih stabil 0,47–0,60 juta t/tahun; pakan (jagung + bungkil) 4,8–7,2 juta t.

## 2. Fitur & kebocoran (`scripts/feats_wi.py`, `build_wi.py`)

| Keluarga | Kolom | Definisi |
|---|---|---|
| W_NAT | `wn_z_rain_28/56/91`, `wn_z_wet_56`, `wn_z_dry_56`, `wn_z_tmax_28` | Σ porsi produksi × anomali baku titik provinsi (klimatologi DOY ± 10 hari, 2016–2020); hanya cabai merah, cabai rawit, bawang merah |
| W_LOC | `wl_*` (6) | anomali yang sama di titik provinsi sendiri, semua komoditas |
| IMP | `im_yoy3`, `im_mom3`, `im_dev12`, `im_uv3` | Σ 3 bulan vs tahun lalu / 3 bulan sebelumnya; bulan terakhir vs rerata 12 bulan; Δ log nilai satuan USD/kg |

As-of: cuaca s.d. Minggu sebelum minggu origin (lag ≥ 7 hari); klimatologi sebelum origin pertama; porsi ATAP tahun Y sejak 1 Juli Y+1
(sebelum 2021-07-01 memakai 2020, diungkap); impor available_at = akhir bulan + 45 hari. Uji kebocoran (`hasil/wi_leak.csv`): 12 origin
2021–2026 × 16 kolom, perturbasi & penghapusan data sesudah cutoff → **0 sel berbeda**.

## 3. Layar Data Understanding (`scripts/du_wi.py` → `hasil/du_wi.csv`)

Kontrol: `iw_gap` ρ 0,132 / 0,099; derau 0,003 / −0,026; `dev_ma13` ≈ 0. Korelasi **parsial** (fitur diresidualkan per komoditas terhadap
`nat_dp_1`, `nat_dp_4`, `lag_dp_4`, `dev_ma13`):

| Fitur | ρ h 4 (interval) | ρ h 8 (interval) | q h 4 / h 8 |
|---|---|---|---|
| `wn_z_tmax_28` | +0,136 (−0,043..0,271) | +0,174 (0,052..0,299) | 0,90 / 0,033 |
| `wn_z_rain_91` | −0,090 (−0,198..0,058) | −0,161 (−0,317..0,014) | 0,90 / 0,23 |
| `wn_z_dry_56` | +0,092 | +0,105 | 0,92 / 0,34 |
| W_LOC terkuat (`wl_z_rain_56`) | −0,045 | −0,049 | 0,035 / 0,059 |
| IMP terkuat (`im_mom3`) | −0,024 | −0,079 | 0,62 / 0,062 |

Tidak ada yang lolos gerbang. W_NAT sebesar atau lebih besar dari kontrol positif, bertanda sesuai mekanisme (panas/kering → kenaikan
diremehkan; basah → sebaliknya) dan **bertanda sama di setiap tahun dev** (tmax +0,11..+0,31; hujan 91 hari −0,06..−0,36), tetapi
intervalnya lebar karena hanya bervariasi antar 37 origin × 3 komoditas. Pengecualian modeling dicatat di kartu W (PROTOKOL §1).

## 4. Modeling (`scripts/run_wi.py`, `ev_wi.py` → `hasil/ev_*.csv`)

`base` = `direction_tuned_preds` C1t persis (25.259 baris, maks |Δp| 0,0). Run 8 menit (6 proses).

| Varian | Δ h 4 (interval) | Δ h 8 (interval) | Sasaran h 4 / h 8 | Δ per tahun h 4 (2021/22/23) | Gagal aturan | Skala Danen |
|---|---|---|---|---|---|---|
| W_NAT | −0,003 (−0,015..0,011) | −0,003 (−0,013..0,003) | −0,004 / −0,003 (horti) | +0,012 / −0,011 / −0,010 | 1, 2, 3 | ≤ 0 |
| W_LOC | +0,002 (−0,009..0,013) | −0,003 (−0,014..0,007) | +0,004 / −0,002 (horti) | +0,012 / −0,004 / −0,003 | 1, 2, 3 | ≤ 0 |
| IMP | −0,006 (−0,017..0,005) | **−0,015 (−0,027..−0,004)** | −0,005 / −0,013 (keranjang) | −0,009 / −0,005 / −0,007 | 1, 2, 3, 4 | ≤ 0 |

Per komoditas (`hasil/ev_per_commodity.csv`): W_NAT cabai rawit +0,013 / +0,005, cabai merah 0,000 / −0,014, bawang merah −0,024 /
−0,001. IMP beras −0,040 / −0,048 dan daging sapi −0,051 / −0,013 (impor beras adalah keputusan kebijakan yang jarang; model
menyesuaikan diri dengan lonjakan 2018 lalu salah membaca 2023).

**Adendum pasca-hoc W_CAL** (`scripts/cal_wi.py` → `hasil/cal_wi*.csv`): logit C1t + β₁·`wn_z_tmax_28` + β₂·`wn_z_rain_91` pada baris
hortikultura, β walk-forward dari ≥ 8 origin riwayat (30 / 28 origin dinilai). Koefisien rerata bertanda sesuai (suhu +0,19 / +0,19;
hujan −0,16 / −0,40), tetapi sd koefisien suhu sebesar reratanya (0,18 / 0,21). Δ macro F1 −0,003 / −0,005 (hortikultura −0,009 / −0,016); Brier hortikultura 0,2291 → 0,2323 / 0,2223 →
0,2267. Korelasi residual pooled di layar DU adalah pola in-sample; koefisien dari origin lampau tidak memperbaiki origin berikutnya.

## 5. Kesimpulan

1. **Ruangnya ada, tetapi di tingkat nasional per komoditas × origin.** Informasi sempurna tentang arah nasional bernilai +0,105; sinyal
   pasokan yang realistis harus menangkap sebagian kecil pergeseran itu sebelum terjadi.
2. **Cuaca di sentra (resolusi provinsi, 0,5°) tidak cukup.** Sinyalnya bertanda benar tetapi lemah dan tidak stabil koefisiennya pada
   ± 30 origin riwayat; dengan HGB maupun koreksi 2 parameter, macro F1 dan kalibrasi tidak membaik. Kemungkinan penyebab: titik
   provinsi ≠ kabupaten sentra; harga hortikultura bergantung pada fase tanam/panen yang tidak teramati; 6 tahun riwayat hanya memuat
   sedikit episode cuaca ekstrem (2019 kering, 2023 El Niño).
3. **Realisasi impor bulanan memperburuk** (h 8 −0,015, lolos BH sebagai lebih buruk). Volume impor adalah keputusan kebijakan yang
   jarang & berlag; tutup jalur ini sebagai fitur.
4. Tidak ada temuan yang mengubah model: **C1-tuned tetap**. Konfirmasi negatif ini menambah bukti D-156 bahwa batas skor adalah
   informasi ex-ante yang belum tersedia di repo (pasokan mingguan per sentra, intervensi bertanggal), bukan pengolahan.
5. **Pelajaran metode** (masuk `docs/EKSPERIMEN.md` §3): untuk sinyal tingkat nasional (konstan antarprovinsi), korelasi residual pooled
   bersifat in-sample dan berdaya rendah; uji DU wajib menyertakan koreksi walk-forward berparameter kecil sebelum modeling.

## 6. Rekomendasi

- Jangan menambah fitur cuaca berbasis titik provinsi lagi. Bila cuaca dikejar ulang, syaratnya: lokasi sentra tingkat kabupaten,
  kalender tanam/panen per komoditas, dan curah hujan resolusi tinggi (mis. CHIRPS 0,05°), dengan hipotesis horizon yang ditulis dulu.
- Tutup fitur realisasi impor bulanan.
- Informasi yang masih masuk akal adalah data pasokan mingguan per sentra dan intervensi bertanggal (operasi pasar, penyaluran SPHP) yang
  harus diminta resmi (`[HUMAN]`); daya ungkitnya terbesar di hortikultura dan kelompok impor/pakan, terkecil di beras.
