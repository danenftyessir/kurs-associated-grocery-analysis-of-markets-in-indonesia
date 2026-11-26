-- Jalur A Workstream B (D-165): hitungan harian artikel GDELT GKG 2.1 berbahasa Indonesia per kelompok komoditas & kategori.
-- BELUM DIJALANKAN. Butuh proyek Google Cloud (BigQuery sandbox: tanpa kartu kredit, kuota 1 TiB kueri/bulan) — [HUMAN].
-- Wajib dry-run dulu:   bq query --use_legacy_sql=false --dry_run < b_bq_daily_counts.sql
-- Jalankan dengan batas: bq query --use_legacy_sql=false --maximum_bytes_billed=600000000000 --format=csv --max_rows=200000 \
--                          < b_bq_daily_counts.sql > gdelt_daily_counts.csv
-- (di konsol: Query settings → Advanced → Maximum bytes billed = 600 GB; konsol menampilkan "This query will process X" sebelum Run)
-- Kolom yang dipindai (biaya = ukuran kolom × semua partisi 2018-12-22..2023-12-31, WHERE tidak mengurangi biaya):
--   DATE, TranslationInfo, SourceCommonName, DocumentIdentifier, Extras. TIDAK memakai GCAM/V2Themes/V2Locations (kolom terbesar).
-- Estimasi (hasil/b_gkg_sample_summary.json + volume per batch): lihat GDELT_FEASIBILITY.md §4. Kalau dry-run > 600 GB → jangan jalankan.
-- Pola komoditas = varian F1 pilot B2 (batas kata, tanpa `sawit`, kecuali "pondok cabe"; hasil/b_manual_summary.json): presisi relevan
-- 0,27 (+ kata kunci pasokan/kebijakan & dedup 0,72). Kolom n_disrupt/n_policy/n_stabil/n_supply = varian F2 per kategori.
-- Waktu: DATE = stempel batch 15 menit saat GDELT pertama memproses dokumen (UTC), BUKAN tanggal kejadian di artikel.

DECLARE start_ts TIMESTAMP DEFAULT TIMESTAMP('2018-12-22');
DECLARE end_ts   TIMESTAMP DEFAULT TIMESTAMP('2024-01-01');

WITH base AS (
  SELECT
    DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING))) AS day_utc,
    SourceCommonName AS src,
    LOWER(CONCAT(
      IFNULL(REGEXP_EXTRACT(Extras, r'<PAGE_TITLE>(.*?)</PAGE_TITLE>'), ''), ' ',
      REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(DocumentIdentifier, r'^https?://[^/]+', ''), r'\.(html?|php|aspx?)$', ''),
                     r'[-_/+]', ' '))) AS txt,
    LOWER(IFNULL(REGEXP_EXTRACT(Extras, r'<PAGE_TITLE>(.*?)</PAGE_TITLE>'), DocumentIdentifier)) AS title_key
  FROM `gdelt-bq.gdeltv2.gkg_partitioned`
  WHERE _PARTITIONTIME >= start_ts AND _PARTITIONTIME < end_ts
    AND STARTS_WITH(TranslationInfo, 'srclc:ind')
),
totals AS (
  SELECT day_utc, COUNT(*) AS n_ind_total FROM base GROUP BY day_utc
),
pats AS (
  SELECT * FROM UNNEST([
    STRUCT('beras' AS commodity_group, r'\bberas\b|\bpadi\b|\bgabah\b' AS pat),
    ('bawang_putih', r'\bbawang putih\b'),
    ('bawang_merah', r'\bbawang merah\b'),
    ('cabai', r'\bcabai\b|\bcabe\b'),
    ('gula_pasir', r'\bgula pasir\b|\bgula kristal\b|\bgula\b'),
    ('minyak_goreng', r'\bminyak goreng\b|\bmigor\b|\bminyakita\b|\bcpo\b'),
    ('daging_sapi', r'\bdaging sapi\b|\bsapi impor\b|\bsapi bakalan\b'),
    ('daging_ayam', r'\bdaging ayam\b|\bayam ras\b|\bayam broiler\b|\blive bird\b'),
    ('telur_ayam', r'\btelur ayam\b|\bharga telur\b|\btelur\b'),
    ('umum', r'\bsembako\b|\bbahan pokok\b|\bbapok\b|\bpangan\b|\bbulog\b|\bbapanas\b')   -- tidak dipakai set praregistrasi
  ])
),
hits AS (
  SELECT b.day_utc, p.commodity_group, b.src, b.title_key,
    REGEXP_CONTAINS(b.txt, r'gagal panen|banjir|kekeringan|kemarau|el nino|hama|wabah|flu burung|\bpmk\b|longsor|gempa|cuaca|kelangkaan|langka|penimbunan|timbun') AS k_disrupt,
    REGEXP_CONTAINS(b.txt, r'impor|ekspor|larangan|kuota|\bhet\b|\bhap\b|harga eceran tertinggi|\bdmo\b|\bdpo\b|subsidi|neraca|regulasi|permendag|perbadan') AS k_policy,
    REGEXP_CONTAINS(b.txt, r'operasi pasar|\bsphp\b|pasar murah|pangan murah|stabilisasi|cadangan|bulog|bapanas|intervensi') AS k_stabil,
    REGEXP_CONTAINS(b.txt, r'pasokan|stok|panen|produksi|distribusi|gudang|petani|peternak|pakan|kapal|pelabuhan|angkut|pengiriman') AS k_supply,
    REGEXP_CONTAINS(b.txt, r'harga') AS k_price
  FROM base b JOIN pats p ON REGEXP_CONTAINS(b.txt, p.pat) AND NOT REGEXP_CONTAINS(b.txt, r'pondok cabe')
)
SELECT h.day_utc, h.commodity_group,
  COUNT(*) AS n_raw,                                                   -- tanpa dedup (diagnostik sindikasi)
  COUNT(DISTINCT h.title_key) AS n_all,                                -- semua hitungan di bawah = judul unik per hari (dedup pilot B2)
  COUNT(DISTINCT IF(k_disrupt, h.title_key, NULL)) AS n_disrupt,
  COUNT(DISTINCT IF(k_policy, h.title_key, NULL)) AS n_policy,
  COUNT(DISTINCT IF(k_stabil, h.title_key, NULL)) AS n_stabil,
  COUNT(DISTINCT IF(k_supply, h.title_key, NULL)) AS n_supply,
  COUNT(DISTINCT IF(k_price AND NOT (k_disrupt OR k_policy OR k_stabil OR k_supply), h.title_key, NULL)) AS n_price_only,
  COUNT(DISTINCT h.src) AS n_sources,
  ANY_VALUE(t.n_ind_total) AS n_ind_total
FROM hits h JOIN totals t USING (day_utc)
GROUP BY h.day_utc, h.commodity_group
ORDER BY h.day_utc, h.commodity_group;
-- Keluaran ± 1.835 hari × 9 kelompok ≈ 16.500 baris (< 2 MB CSV). `n_ind_total` per hari diulang di setiap baris; skrip
-- b_gdelt_screen.py memisahkannya (--totals boleh berkas yang sama setelah drop_duplicates day_utc).
