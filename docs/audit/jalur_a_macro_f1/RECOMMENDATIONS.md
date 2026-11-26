# Jalur A — Rekomendasi (urut potensi dampak × kelayakan × biaya)

Tanggal: 2026-11-26 · Keputusan: D-165. Dasar: [RESULTS.md](RESULTS.md).

| # | Tindakan | Siapa | Biaya | Kapan | Mengapa |
|---|---|---|---|---|---|
| 1 | **Commit** sisa folder `docs/audit/jalur_a_macro_f1/` (laporan .md, `EXPERIMENT_LOG.csv`, `hasil/protocol_sha256.txt`, `scripts/r_log.py`, perubahan SQL & layar sesudah `ec6dd19`, hasil GDELT `hasil/gdelt_*` & `b_screen_gdelt.csv`) | Danen (git) | 0 | **sebelum Jumat 2026-11-27** | prediksi maju D-152 (`ca53742`) & D-158 (`ec6dd19`) sudah di riwayat git; protokol B4 beku tercatat di komentar job BigQuery (23.03 WIB) tetapi versi akhir kueri/layar & hasilnya belum di git |
| 2 | Unduh snapshot PIHPS baru (format `pihps`, skrip `20261125_pilot_grosir/scripts/fetch_pihps.py --price-type 1 --start 2026-09-01 --end <hari ini>`, pasar tradisional; rentang ini cukup karena origin maju ≥ 2026-09-28; cocokkan dulu nama varian dengan zip `pihps` resmi) lalu `python docs/audit/jalur_a_macro_f1/scripts/a_forward_eval.py --pihps-zip <zip>` | Danen (persetujuan unduh) + agent | ± 1 jam unduh | ≥ 2026-11-28; ulang 2026-12-19 & 2027-01-16 | menandai kegagalan besar IW_NAT/FR_REF (GAGAL_MAJU) pada origin baru; bukan konfirmasi keuntungan |
| 3 | ~~BigQuery sandbox → layar G5 GDELT~~ **selesai 2026-11-26**: GDELT gagal G5 (ΔAUC −0,008..+0,001) → ditutup | – | 0 (sandbox, 313,83 GB) | – | proyek `kagami-gdelt` boleh dibiarkan (tanpa billing, tanpa biaya) atau dihapus Danen di Google Cloud console bila tidak dipakai lagi |
| 4 | Satu surat permintaan data resmi: SP2KP stok & pasokan mingguan (D-159 §2), **Bapanas Proyeksi Neraca Pangan** (semua vintage bulanan + tanggal update), **Kementan luas tanam & EWS hortikultura** (bulanan per provinsi, tanggal rilis) | Danen / tim (`[HUMAN]`, U112) | waktu tunggu instansi | sesudah submit | mekanisme ex-ante yang paling masuk akal untuk headroom nasional (+0,105); hanya evaluasi prospektif bila vintage dev tidak ada |
| 5 | ~~Keputusan ambang G5 sebelum data GDELT~~ tidak relevan lagi: GDELT gagal dengan titik estimasi ≤ 0, jadi ambang yang lebih longgar pun tidak akan meloloskannya. Untuk sumber berikutnya: tetap laporkan kontrol positif & MDE layar (EKSPERIMEN §3) | Danen | 0 | sebelum uji sumber berikutnya | menghindari penyesuaian ambang pasca-hoc |
| 6 | Hentikan optimasi dari histori harga (fitur, threshold, bobot, model, kalibrasi) | – | – | – | D-145–D-163a: tidak ada perbedaan > derau pelatihan; aspirasi 0,8–0,9 di atas batas informasi nasional sempurna (0,756 / 0,782) |
| 7 | Validasi kebutuhan TPID (U109) dan target risiko material (K4, sesi D-164) sebagai ukuran manfaat utama | Danen / tim | wawancara | sebelum makalah final | macro F1 arah bukan ukuran yang paling dekat dengan keputusan TPID |

Yang **tidak** direkomendasikan: mengulang SIJAGUNG, SPORA, PIBC, CFSv2, cuaca terealisasi, impor bulanan, harga grosir/produsen/kota; membuka
test 2024+ untuk kandidat keluarga intraminggu lagi; LLM/embedding atau fitur berita lain dari GDELT (hitungan kata kunci gagal G5 dengan
titik estimasi ≤ 0; tanpa mekanisme baru, varian berita lain tidak dijalankan).
