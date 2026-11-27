"""Halaman 8 -- Lampiran teknis: Data & metode (D-170, D-171). Sumber, kelayakan seri, efek terkecil yang dapat dideteksi,
daftar istilah (notasi yang dipakai laporan lengkap), dan reproduksi; tanpa path server dan tanpa kode internal."""

import re

import pandas as pd
import streamlit as st

from common import CFG, STRETCH, commodity_labels, footer, load, need, note, page_header, unit_names
from kagami.utils.env import artifact_status

page_header("Data & metode",
            "Dari mana datanya, seberapa lengkap, seberapa kecil efek yang bisa terdeteksi, dan arti istilah yang dipakai "
            "di laporan lengkap.")
labels, names = commodity_labels(), unit_names()

GLOSSARY = [
    ("Respons harga (β, ω)", "Perubahan harga eceran kumulatif dalam persen setelah kurs rupiah (β) atau harga dunia dalam "
     "rupiah (ω) naik 1%, diukur dari minggu ke-0 sampai ke-12."),
    ("Penerusan kurs (PT)", "Respons harga dibagi respons kurs terhadap dirinya sendiri. PT 0,5 berarti separuh pelemahan "
     "rupiah muncul di harga eceran."),
    ("Minggu ke-h (horizon)", "Jarak waktu dari perubahan kurs ke harga yang diukur."),
    ("Rentang 95%", "Interval kepercayaan 95%. Rentang yang memuat nol berarti respons belum bisa dibedakan dari nol; ujung "
     "atasnya dibaca sebagai batas kenaikan."),
    ("Data acak (plasebo)", "Versi data yang urutan waktu kursnya digeser acak minimal 52 minggu, 499 kali. Hasil asli "
     "dibandingkan dengan sebaran hasil data acak."),
    ("p", "Peluang mendapat hasil sebesar yang diamati, atau lebih besar, bila sebenarnya tidak ada hubungan."),
    ("q (Benjamini–Hochberg)", "p yang dikoreksi karena banyak uji dilakukan sekaligus."),
    ("Efek terkecil yang dapat dideteksi (MDE)", "Efek yang akan terdeteksi dengan peluang 80% pada taraf 5%. Kami "
     "menghitungnya sebelum melihat hasil."),
    ("Praregistrasi", "Hipotesis, parameter, dan aturan uji yang kami bekukan pada 20 November 2026, sebelum estimasi dilihat. "
     "Uji konfirmatori mengikuti praregistrasi; hasil eksploratif tidak menguji hipotesis."),
    ("Empirical Bayes", "Penyusutan estimasi provinsi ke arah rata-rata sesuai tingkat derau datanya, agar provinsi dengan data "
     "berisik tidak tampak ekstrem."),
    ("τ², I², Q", "Ukuran keragaman respons antarprovinsi. τ² = 0 berarti data tidak cukup untuk membedakan provinsi."),
    ("Silhouette", "Skor kualitas pengelompokan, dari −1 sampai 1. Makin tinggi, makin jelas pemisahan kelompoknya."),
    ("Titik prediksi (origin)", "Tanggal model membuat prediksi, hanya dengan data sebelum tanggal itu."),
    ("Rasio MAE", "Galat absolut rata-rata sebuah model dibagi galat model dasar. Di bawah 1 berarti lebih akurat."),
    ("Uji Diebold–Mariano (DM)", "Uji beda akurasi dua model prediksi. DM negatif berarti model pembanding kurang akurat dari "
     "model dasar."),
    ("M0, M1, M2, M3", "M0 tanpa perubahan; M1 model dasar (regresi ridge); M2 model dasar ditambah kurs dan harga dunia; M3 "
     "gradient boosting dengan identitas seri."),
    ("Pseudo-real-time", "Evaluasi dengan versi data terakhir karena riwayat revisi data tidak tersedia."),
    ("Rangkaian harga identik", "Harga harian yang sama selama minimal 5 hari teramati (status carry_forward). Bisa berarti harga "
     "kaku atau harga hari sebelumnya yang dipakai saat pasar tutup; keduanya tidak bisa dibedakan."),
    ("HET, HAP", "Harga eceran tertinggi dan harga acuan pembelian atau penjualan yang ditetapkan pemerintah."),
    ("PIHPS, JISDOR, Pink Sheet", "Harga pangan harian per provinsi (Bank Indonesia), kurs rupiah terhadap dolar AS harian "
     "(Bank Indonesia), dan harga komoditas dunia bulanan (Bank Dunia)."),
    ("TPID", "Tim Pengendalian Inflasi Daerah, pengguna sasaran KAGAMI."),
]


def _clean(text: str) -> str:
    """Buang kode internal (D-xxx, notasi e_t/w_it) dari teks sumber di configs/sources.yaml untuk tampilan."""
    text = re.sub(r"\s*\((?:e_t|w_it|U\d+)\)", "", str(text))
    return re.sub(r"\s*\bD-\d+\b", "", text).strip()


st.markdown("## Sumber data")
rows = [{"Sumber": v.get("publisher", k), "Peran": _clean(v.get("role", "")), "Cakupan": v.get("coverage", ""),
         "Lisensi": v.get("license", ""), "Ikut paket juri": bool(v.get("redistribute", False)),
         "key": k, "opsional": bool(v.get("optional", False))} for k, v in CFG.sources.items()]
src = pd.DataFrame(rows)
ck = load("checksums")
if ck is not None and {"source", "retrieved_at"} <= set(ck.columns):
    src = src.merge(ck.groupby("source", as_index=False)["retrieved_at"].max().rename(
        columns={"source": "key", "retrieved_at": "Diambil"}), on="key", how="left")
cols = [c for c in ("Sumber", "Peran", "Cakupan", "Lisensi", "Diambil", "Ikut paket juri") if c in src]
st.dataframe(src.loc[~src["opsional"], cols], hide_index=True, **STRETCH)
note("Data mentah tanpa hak redistribusi tidak ikut paket juri. Paket berisi dataset turunan (izin Bank Indonesia mencakup "
     "redistribusi data turunan) dan sumber berlisensi terbuka.")
with st.expander("Sumber tambahan untuk eksplorasi prediksi (tidak dipakai uji utama)"):
    st.dataframe(src.loc[src["opsional"], cols], hide_index=True, **STRETCH)

got = need("eligibility", "mde")
if got:
    st.markdown("## Kelengkapan seri")
    el = got["eligibility"]
    c1, c2 = st.columns([1, 3])
    c1.metric("Seri provinsi × komoditas yang layak", f"{int(el['eligible'].sum())} / {len(el)}")
    per = (el.groupby("commodity", as_index=False).agg(seri=("eligible", "size"), layak=("eligible", "sum"))
           .assign(Komoditas=lambda d: d["commodity"].map(labels))
           .rename(columns={"seri": "Seri", "layak": "Layak"})[["Komoditas", "Seri", "Layak"]])
    c2.dataframe(per, hide_index=True, **STRETCH)
    note("Sebuah seri layak bila minggu tanpa pengamatan paling banyak 20%, tidak ada celah lebih dari 8 minggu, dan setiap "
         "tahun minimal 70% minggunya teramati. Seri yang tidak layak tetap dilaporkan.")

    st.markdown("## Efek terkecil yang dapat dideteksi")
    mde = got["mde"].copy()
    mde["Komoditas"] = mde["commodity"].map(labels)
    if "unit" in mde:
        mde["Wilayah"] = mde["unit"].astype(str).map(lambda u: names.get(u, u))
    show = {"Komoditas": "Komoditas", "horizon": "Minggu ke-", "mde_beta": "Respons terhadap kurs (%)",
            "mde_pt": "Penerusan kurs", "mde_asym_pt": "Selisih melemah vs menguat (penerusan kurs)"}
    nat = mde[mde["level"] == "national"]
    st.dataframe(nat[[c for c in show if c in nat]].rename(columns=show).round(2), hide_index=True, **STRETCH)
    note("Kami menghitung angka ini sebelum melihat hasil estimasi. Contoh: bila efek terkecil untuk penerusan kurs adalah 0,5, "
         "penerusan di bawah setengah pelemahan rupiah tidak dapat dibedakan dari nol.")
    reg = mde[mde["level"] == "region"]
    if len(reg):
        with st.expander("Per wilayah"):
            cols_r = {"Komoditas": "Komoditas", "Wilayah": "Wilayah", **{k: v for k, v in show.items() if k != "Komoditas"}}
            st.dataframe(reg[[c for c in cols_r if c in reg]].rename(columns=cols_r).round(2), hide_index=True, **STRETCH)

st.markdown("## Daftar istilah")
st.dataframe(pd.DataFrame(GLOSSARY, columns=["Istilah", "Arti"]), hide_index=True, **STRETCH,
             column_config={"Arti": st.column_config.TextColumn(width="large")})

st.markdown("## Reproduksi")
st.markdown(
    "Juri dapat mereproduksi hasil pada tiga tingkat:\n\n"
    "1. Menjalankan aplikasi ini dari hasil yang dikirim.\n"
    "2. Menjalankan semua tahap analisis dari dataset turunan yang dikirim (`python -m kagami all`).\n"
    "3. Mengunduh ulang data mentah dari sumbernya.\n\n"
    "Langkah lengkapnya ada di README bagian 10. Setiap tahap mencatat log eksekusi dengan sidik jari data dan kode; lihat "
    "halaman Riwayat eksekusi.")
stat = artifact_status(CFG)
n_ok = int(stat["available"].sum()) if "available" in stat else 0
st.metric("Hasil analisis yang tersedia", f"{n_ok} / {len(stat)}")
with st.expander("Daftar hasil analisis"):
    keep = {"artifact": "Nama", "stage": "Tahap", "ship": "Ikut paket juri", "available": "Tersedia"}
    st.dataframe(stat[[c for c in keep if c in stat]].rename(columns=keep), hide_index=True, **STRETCH)
report = load("stage0_report")
if report:
    with st.expander("Laporan pemeriksaan data (Tahap 0)"):
        st.markdown(report)

footer("Bank Indonesia (JISDOR, PIHPS), Bank Dunia, FRED, FAOSTAT, BPS, Bapanas")
