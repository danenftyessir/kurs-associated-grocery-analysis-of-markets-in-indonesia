# Isu Terbuka & Risiko

Status: 🔴 terbuka · 🟡 default sementara dipakai · 🟢 selesai. Tutup isu dengan menulis resolusi + tanggal, lalu tambah D-xxx bila mengubah desain.

## Isu (U1–U13 dari proposal v4 §9.2, U14+ ditemukan saat skeleton)

| # | Isu | Default sementara | Tenggat | WP | Status |
|---|---|---|---|---|---|
| U1 | Juknis INDONERIS 2026 | Mengikuti juknis resmi (docs/Juknis...pdf) | – | – | 🟢 |
| U2 | Cakupan PIHPS 2018–2019 | Mulai 2020 bila tidak tersedia | 20 Nov | WP-04 | 🟢 2026-11-20: 337/340 seri layak sejak 2018 → mulai 2018 (D-006) |
| U3 | Tanggal berlaku & isi PADG No. 7/2026 | Tandai minggu sekitar perubahan; robustness tanpa minggu itu | 21 Nov | WP-05, WP-28 | 🔴 isi `params.calendar.breaks.padg_7_2026` |
| U4 | Periode impor BPS terbaru | FAOSTAT sumber utama rasio impor | 21 Nov | WP-07 | 🟡 BPS bulanan s.d. 2026-09 tersedia |
| U5 | FAOSTAT untuk bawang putih, bawang merah, cabai | Kelas ordinal bila tidak tersedia | 21 Nov | WP-07 | 🟡 Bawang merah & cabai ada; **bawang putih kering tidak ada** → BPS/Comtrade (impor) + sumber produksi lain, atau ordinal |
| U6 | Kompilasi regulasi HET/HAP/HPP | Beras, minyak goreng, gula saja | 22 Nov | WP-07 | 🟡 Draf 2 tabel ada; banyak tanggal belum terverifikasi dari JDIH |
| U7 | Ketentuan penggunaan data BPS & FRED | Data mentah tidak disertakan | 22 Nov | WP-32 | 🟡 `redistribute` di sources.yaml |
| U8 | Kelayakan uji asimetri | Deskriptif bila MDE > 0,5 | 23 Nov | WP-09, WP-13 | 🔴 |
| U9 | Daya deteksi heterogenitas provinsi | Laporkan nol + batas deteksi | 24 Nov | WP-18, WP-21 | 🔴 |
| U10 | Varian representatif per komoditas | Aturan tertulis, dibekukan di G6 | 20 Nov | WP-11 | 🟡 D-011 PROVISIONAL |
| U11 | Data kecukupan produksi per provinsi | Hanya beras; fitur dikeluarkan untuk komoditas lain | 22 Nov | WP-07 | 🟡 produksi padi & konsumsi ada; lihat U14 |
| U12 | Bibliografi belum lengkap | Tandai sampai dicek | 25 Nov | WP-33 | 🔴 (Ibrahim & Nghiem nama lengkap; studi DM PIHPS; Diebold–Mariano) |
| U13 | Jawaban BI atas permohonan izin | Paket memakai data turunan agregat | 27 Nov | WP-35 | 🔴 email belum tercatat terkirim |
| U14 | Populasi provinsi untuk kecukupan beras | `rice_sufficiency` = NaN dan fitur dikeluarkan | 22 Nov | WP-07 | 🔴 butuh tabel BPS proyeksi penduduk per provinsi (38 → 34) |
| U15 | `n_kota` (kota sampel PIHPS per provinsi) | Isi manual dari FAQ/daftar kota PIHPS | 22 Nov | WP-07 | 🔴 |
| U16 | URL Pink Sheet berubah per rilis | `download` gagal → unduh manual dari halaman Commodity Markets | – | WP-32 | 🟡 |
| U17 | Lonjakan harga satu hari di PIHPS | Ditandai, tidak dihapus otomatis | 23 Nov | WP-10 | 🔴 |
| U18 | Minyak Goreng Curah tidak ada di Babel, ~66% minggu kosong di Maluku & Papua Barat (berhenti 2023/2021); relevansi turun pasca-Minyakita | Tetap Curah; Kemasan Bermerk 1 sebagai robustness | 21 Nov | WP-11 | 🟢 2026-11-20: diganti ke Kemasan Bermerk 1, Curah jadi robustness Tier 2 (D-023) |
| U19 | Snapshot PIHPS diambil via endpoint `WebSite/TabelHarga/GetGridDataDaerah` (MANIFEST v2) | Proposal v4 mensyaratkan "fitur unduh resmi" | 21 Nov | WP-35 | 🔴 `[HUMAN]` pastikan endpoint ini = fitur unduh resmi situs; bila tidak, unduh ulang via fitur resmi dan bandingkan hash |
| U20 | Pemetaan 13 komoditas Bapanas → 10 komoditas PIHPS | Hanya pasangan yang jelas (mis. Minyakita ≠ Minyak Goreng Curah) | 23 Nov | WP-10 | 🔴 |
| U21 | Produksi padi dalam GKG, bukan beras | Konversi GKG→beras (faktor resmi BPS) didokumentasikan | 22 Nov | WP-07 | 🔴 |
| U22 | `carry_forward` (≥ 5 hari identik) = 47,9% sel minggu; beras 92%, daging sapi 90%, gula 85%, minyak goreng 74% | Penanda informatif saja; tidak dipakai sebagai filter | 21 Nov | WP-04, WP-28 | 🟡 Kemungkinan besar kekakuan harga nyata (komoditas diatur), bukan pasar tutup. Robustness: hanya minggu `observed` untuk komoditas volatil. Pertimbangkan ambang lebih panjang (mis. 20 hari) di G6 bila status ini mau dipakai |
| U23 | Cabai Rawit Merah tidak ada di Sumbar; ~90% minggu kosong di Aceh & Kepri | Seri tidak layak (WP-04), tidak dicampur varian lain | 21 Nov | WP-04, WP-11 | 🟢 2026-11-20: 3 seri ditandai tidak layak di `eligibility.csv`; cabai rawit dianalisis atas 31 provinsi. Hijau tidak lebih baik (31/34) → tetap Merah |
| U24 | Menyimpan PIHPS/JISDOR/BPS mentah di dataset Kaggle privat / Google Drive pribadi untuk komputasi | Hanya privat, tidak dibagikan; bukan redistribusi | 21 Nov | WP-35 | 🟡 cek ketentuan PIHPS/BI saat mengirim email izin (U13); bila dilarang, jalankan Task 1–2 dari `panel_weekly_region` saja di cloud |

## Risiko (proposal v4 §9.3)

| Risiko | Prob. | Dampak | Mitigasi | Fallback |
|---|---|---|---|---|
| Respons kurs tak terbedakan dari nol | Tinggi | Sedang | Event study, penggerak harga dunia rupiah, 7 wilayah, MDE | Laporkan batas atas; Task 4 & uji struktur tertanam sebagai kontribusi DM |
| G-het gagal | Tinggi | Sedang | Clustering tetap jalan & dinilai vs plasebo | k = 1 + batas deteksi |
| Hak data PIHPS tidak jelas | Tinggi | Sedang | Unduhan resmi, izin tertulis | Data turunan agregat; Panel Harga Bapanas cadangan |
| Data 2018–2019 tidak tersedia | ~~Sedang~~ Tertutup | Tinggi | Cek hari pertama | Tidak terjadi (U2 🟢) |
| Bootstrap/plasebo terlalu lama | Sedang | Sedang | Vektorisasi; fokus dulu | B = R = 199 untuk non-fokus |
| Streamlit tidak stabil | Sedang | Tinggi | Parquet, tanpa estimasi runtime | Halaman 3 & 5 jadi tabel |
