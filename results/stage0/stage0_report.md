# Laporan Tahap 0 — KAGAMI

Periode 2018-01-01 .. 2026-11-21. Dibangun oleh `pipelines.stage0`; angka di bawah berasal dari artefak Tahap 0. Hasil bersifat asosiasional.

## 1. Cakupan per sumber

| source | n_rows | start | end |
|---|---|---|---|
| pihps (varian representatif) | 800642 | 2017-03-29 | 2026-11-18 |
| jisdor | 3269 | 2013-05-20 | 2026-11-18 |
| pinksheet | 50518 | 1960-01-01 | 2026-10-01 |
| brent | 3517 | 2013-01-02 | 2026-11-11 |
| dollar_index | 3454 | 2013-01-02 | 2026-11-13 |
| bps_import_monthly | 2845 | 2023-01-01 | 2026-09-01 |
| comtrade_import | 961 | 2017-01-01 | 2022-12-01 |
| bapanas_panel | 24599 | 2022-01-01 | 2026-10-01 |

## 2. Kelayakan seri

337/340 seri layak.

| commodity | n_series | n_eligible | max_missing |
|---|---|---|---|
| bawang_merah | 34 | 34 | 0.004 |
| bawang_putih | 34 | 34 | 0.004 |
| beras | 34 | 34 | 0.004 |
| cabai_merah | 34 | 34 | 0.004 |
| cabai_rawit | 34 | 31 | 1.000 |
| daging_ayam | 34 | 34 | 0.004 |
| daging_sapi | 34 | 34 | 0.004 |
| gula_pasir | 34 | 34 | 0.004 |
| minyak_goreng | 34 | 34 | 0.006 |
| telur_ayam | 34 | 34 | 0.004 |

## 3. Episode depresiasi (Σ de 8 minggu ≥ 3%)

| episode_id | start_week | end_week | cum_dlog_e | peak_week | n_trigger_weeks | in_period |
|---|---|---|---|---|---|---|
| 1 | 2018-03-12 | 2018-03-19 | 0.033 | 2018-03-19 | 2 | True |
| 2 | 2018-05-21 | 2018-05-21 | 0.031 | 2018-05-21 | 1 | True |
| 3 | 2018-07-23 | 2018-10-22 | 0.041 | 2018-10-01 | 10 | True |
| 4 | 2020-03-09 | 2020-05-04 | 0.185 | 2020-03-23 | 9 | True |
| 5 | 2020-08-03 | 2020-08-17 | 0.043 | 2020-08-17 | 3 | True |
| 6 | 2021-03-29 | 2021-04-12 | 0.044 | 2021-04-12 | 3 | True |
| 7 | 2022-10-10 | 2022-11-21 | 0.050 | 2022-10-31 | 7 | True |
| 8 | 2023-10-16 | 2023-10-30 | 0.042 | 2023-10-23 | 3 | True |
| 9 | 2024-04-15 | 2024-04-29 | 0.037 | 2024-04-15 | 3 | True |
| 10 | 2024-11-11 | 2024-12-16 | 0.046 | 2024-11-18 | 4 | True |
| 11 | 2025-04-14 | 2025-04-14 | 0.031 | 2025-04-14 | 1 | True |
| 12 | 2026-05-18 | 2026-07-06 | 0.051 | 2026-06-01 | 8 | True |
| 13 | 2026-11-02 | 2026-11-02 | 0.030 | 2026-11-02 | 1 | True |

## 4. Variasi kurs per tahun

| period | n_dep_weeks | n_app_weeks | mean_dep | mean_app | sd_de | n_weeks | n_zero_weeks | max_de | min_de | n_episode_weeks |
|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | 28 | 24 | 0.0064 | -0.0049 | 0.0076 | 53 | 1 | 0.0154 | -0.0275 | 17 |
| 2019 | 24 | 27 | 0.0043 | -0.0052 | 0.0064 | 52 | 1 | 0.0128 | -0.0251 | 0 |
| 2020 | 26 | 26 | 0.0107 | -0.0100 | 0.0172 | 52 | 0 | 0.0628 | -0.0406 | 12 |
| 2021 | 26 | 26 | 0.0046 | -0.0043 | 0.0058 | 52 | 0 | 0.0136 | -0.0141 | 3 |
| 2022 | 32 | 19 | 0.0045 | -0.0026 | 0.0048 | 52 | 1 | 0.0163 | -0.0077 | 7 |
| 2023 | 28 | 24 | 0.0048 | -0.0062 | 0.0069 | 52 | 0 | 0.0113 | -0.0221 | 3 |
| 2024 | 31 | 21 | 0.0056 | -0.0060 | 0.0076 | 53 | 1 | 0.0225 | -0.0171 | 9 |
| 2025 | 31 | 20 | 0.0037 | -0.0041 | 0.0052 | 52 | 1 | 0.0155 | -0.0129 | 1 |
| 2026 | 33 | 13 | 0.0047 | -0.0052 | 0.0053 | 46 | 0 | 0.0123 | -0.0143 | 9 |
| total | 259 | 200 | 0.0054 | -0.0055 | 0.0082 | 464 | 5 | 0.0628 | -0.0406 | 61 |

## 5. MDE (sebelum β dilihat)

MDE_PT nasional (α 0,05, power 0,80):

| commodity | MDE_PT(h=4) | MDE_PT(h=8) | MDE_PT(h=12) |
|---|---|---|---|
| bawang_merah | 1.412 | 1.836 | 2.571 |
| bawang_putih | 1.583 | 2.524 | 3.950 |
| beras | 0.111 | 0.195 | 0.334 |
| cabai_merah | 2.178 | 2.999 | 4.548 |
| cabai_rawit | 2.738 | 3.748 | 5.389 |
| daging_ayam | 0.790 | 1.062 | 1.345 |
| daging_sapi | 0.087 | 0.130 | 0.169 |
| gula_pasir | 0.485 | 0.899 | 1.531 |
| minyak_goreng | 0.271 | 0.465 | 0.773 |
| telur_ayam | 0.477 | 0.684 | 0.850 |

| commodity | mde_pt8 | threshold |
|---|---|---|
| bawang_putih | 2.524 | 0.500 |
| gula_pasir | 0.899 | 0.500 |
| minyak_goreng | 0.465 | 0.500 |

Gerbang G-power (D-007): LP tetap UTAMA (syarat: ketiga komoditas > 0.5).

MDE asimetri β⁻ − β⁺ (satuan PT, h = 8, nasional; D-115): H2 konfirmatori bila ≤ ambang, selain itu deskriptif.

| commodity | mde_asym_pt8 | h2_confirmatory |
|---|---|---|
| beras | 0.444 | True |
| bawang_putih | 6.145 | False |
| gula_pasir | 1.696 | False |
| minyak_goreng | 1.012 | False |
| daging_ayam | 2.657 | False |
| telur_ayam | 1.508 | False |
| daging_sapi | 0.321 | True |
| bawang_merah | 4.659 | False |
| cabai_merah | 7.457 | False |
| cabai_rawit | 9.337 | False |

H2 konfirmatori: beras, daging_sapi.

## 6. QA: lonjakan harga satu hari (ditandai, tidak dihapus; U17)

59 hari ditandai (|Δlog| > 0.5 ke hari sebelum dan berbalik ke hari sesudah).

| commodity | n_flagged |
|---|---|
| bawang_merah | 2 |
| bawang_putih | 5 |
| beras | 2 |
| cabai_merah | 8 |
| cabai_rawit | 16 |
| daging_ayam | 7 |
| daging_sapi | 6 |
| gula_pasir | 9 |
| minyak_goreng | 1 |
| telur_ayam | 3 |

## 7. QA: Σ impor BPS bulanan vs total tahunan (USD, D-019)

| year | n_hs8 | n_ok | ratio_total |
|---|---|---|---|
| 2023 | 58 | 58 | 1.0000 |
| 2024 | 60 | 60 | 1.0000 |
| 2025 | 63 | 63 | 1.0000 |
| 2026 | 60 | 60 | 1.0000 |

## 8. QA: PIHPS vs Panel Harga Bapanas (bulanan, 2022–2026)

bias_log = rerata log(PIHPS/Bapanas); corr_dlog = korelasi perubahan log bulanan. Minyak goreng tidak dibandingkan (Minyakita ≠ Kemasan Bermerk 1; U20).

| commodity | n_prov | median_bias_log | median_corr_dlog |
|---|---|---|---|
| bawang_merah | 34 | 0.032 | 0.926 |
| bawang_putih | 34 | 0.013 | 0.830 |
| beras | 34 | 0.107 | 0.646 |
| cabai_merah | 34 | 0.026 | 0.912 |
| cabai_rawit | 33 | 0.016 | 0.919 |
| daging_ayam | 34 | -0.032 | 0.797 |
| daging_sapi | 34 | 0.016 | 0.588 |
| gula_pasir | 34 | 0.002 | 0.773 |
| telur_ayam | 34 | 0.005 | 0.867 |

## 9. QA: konkordansi HS — Comtrade vs BPS pada bulan yang sama (U102)

14/15 kode konkordansi cocok (|rasio nilai - 1| <= 1% atau keduanya tanpa impor). Rasio = jumlah HS8 BPS yang dipetakan / jumlah Comtrade (CIF USD).

| comtrade_code | n_bps_codes | n_months_comtrade | n_months_bps | comtrade_usd | bps_usd | ratio_value | ratio_kg | corr_month | ok |
|---|---|---|---|---|---|---|---|---|---|
| 0102 | 4 | 12 | 12 | 352287882.000 | 352287882.000 | 1.000 | 1.000 | 1.000 | True |
| 0201 | 2 | 11 | 11 | 43186368.000 | 43186368.000 | 1.000 | 1.000 | 1.000 | True |
| 0202 | 3 | 12 | 12 | 791091257.000 | 791091257.000 | 1.000 | 1.000 | 1.000 | True |
| 0207 | 7 | 8 | 8 | 77468.000 | 77468.000 | 1.000 | 1.000 | 1.000 | True |
| 0407 | 5 | 10 | 10 | 166123.000 | 166123.000 | 1.000 | 1.000 | 1.000 | True |
| 070310 | 4 | 12 | 12 | 94592395.000 | 94592395.000 | 1.000 | 1.000 | 1.000 | True |
| 070320 | 2 | 11 | 11 | 648586485.000 | 648586485.000 | 1.000 | 1.000 | 1.000 | True |
| 070960 | 2 | 0 | 0 | 0.000 | 0.000 | – | – | – | True |
| 090421 | 2 | 12 | 12 | 85619247.000 | 85619247.000 | 1.000 | 1.000 | 1.000 | True |
| 1005 | 4 | 12 | 12 | 367689953.000 | 367689953.000 | 1.000 | 1.000 | 1.000 | True |
| 1006 | 13 | 12 | 12 | 1789023884.000 | 1789023884.000 | 1.000 | 1.000 | 1.000 | True |
| 1511 | 9 | 12 | 12 | 1273735.000 | 1202358.000 | 0.944 | 0.953 | 0.983 | False |
| 1517 | 18 | 12 | 12 | 39424675.000 | 39424675.000 | 1.000 | 1.000 | 1.000 | True |
| 1701 | 6 | 12 | 12 | 2881115490.000 | 2881115490.000 | 1.000 | 1.115 | 1.000 | True |
| 2304 | 4 | 12 | 12 | 3018466760.000 | 3018466760.000 | 1.000 | 1.000 | 1.000 | True |
