"""Halaman 8 -- Lampiran: Data & metode (D-170, D-171, D-173). Untuk semua pembaca: sumber data, cara mengolah (rumus model
dirender LaTeX), kelengkapan seri, pemeriksaan kualitas data (dihitung dari laporan Tahap 0, tabel berlabel pembaca), efek
terkecil yang dapat dideteksi, daftar istilah (simbol LaTeX), dan cara mereproduksi. Tanpa kode internal, nama kolom mentah,
laporan pipeline mentah, atau path server."""

import math
import re

import pandas as pd
import streamlit as st

from common import (CFG, commodity_labels, fmt_num, footer, load, need, note, page_header, plain_text, show_table,
                    unit_names)
from kagami.utils.env import artifact_status

page_header("Data & metode",
            "Dari mana datanya, bagaimana kami mengolahnya, seberapa kecil efek yang bisa terdeteksi, dan arti istilah yang "
            "dipakai di aplikasi ini.")
labels, names = commodity_labels(), unit_names()

# (istilah, arti); `$...$` dirender sebagai rumus oleh st.markdown.
GLOSSARY = [
    ("Respons harga ($\\beta$, $\\omega$)", "Perubahan harga eceran kumulatif, dalam persen, setelah kurs rupiah ($\\beta$) "
     "atau harga dunia dalam rupiah ($\\omega$) naik 1%. Diukur dari minggu ke-0 sampai ke-12."),
    ("Penerusan kurs ($PT$)", "Respons harga dibagi respons kurs terhadap dirinya sendiri, $PT(h) = \\beta(h)/\\gamma(h)$. "
     "$PT = 0{,}5$ berarti separuh pelemahan rupiah muncul di harga eceran."),
    ("Minggu ke-$h$", "Jarak waktu dari perubahan kurs ke harga yang diukur."),
    ("Rentang 95%", "Interval kepercayaan 95%. Rentang yang memuat nol berarti respons belum bisa dibedakan dari nol. Ujung "
     "atasnya kami baca sebagai batas kenaikan."),
    ("Data acak (plasebo)", "Versi data yang urutan waktu kursnya digeser acak minimal 52 minggu, 499 kali. Hasil asli "
     "dibandingkan dengan sebaran hasil data acak."),
    ("$p$", "Peluang mendapat hasil sebesar yang diamati, atau lebih besar, bila sebenarnya tidak ada hubungan."),
    ("$q$ (Benjamini–Hochberg)", "Nilai $p$ yang dikoreksi karena banyak uji dilakukan sekaligus."),
    ("Efek terkecil yang dapat dideteksi (MDE)", "Efek yang akan terdeteksi dengan peluang 80% pada taraf 5%. Kami "
     "menghitungnya sebelum melihat hasil."),
    ("Praregistrasi", "Hipotesis, parameter, dan aturan uji yang kami bekukan pada 20 November 2026, sebelum estimasi dilihat. "
     "Uji konfirmatori mengikuti praregistrasi, sedangkan hasil eksploratif tidak menguji hipotesis."),
    ("Kode hipotesis", "Nama hipotesis di praregistrasi. H0-Het: respons berbeda antarprovinsi. H2: respons saat rupiah melemah "
     "berbeda dari saat menguat. H3: provinsi yang lebih jauh merespons lebih kecil dalam 4 minggu. H5: kurs memperbaiki "
     "prediksi saat kurs bergerak besar. E1 dan E2 deskriptif, tentang porsi impor dan periode HET/HAP."),
    ("Proyeksi lokal (LP)", "Metode regresi yang mengukur respons harga pada setiap minggu ke-$h$ secara terpisah."),
    ("Tier 1, Tier 2", "Cek ketahanan. Tier 1 wajib dan didaftarkan sebelum analisis, Tier 2 tambahan."),
    ("Empirical Bayes", "Penyusutan estimasi provinsi ke arah rata-rata sesuai tingkat derau datanya, agar provinsi dengan data "
     "berisik tidak tampak ekstrem."),
    ("$\\tau^2$, $I^2$, $Q$", "Ukuran keragaman respons antarprovinsi. $\\tau^2 = 0$ berarti data tidak cukup untuk membedakan "
     "provinsi."),
    ("Silhouette", "Skor kualitas pengelompokan, dari −1 sampai 1. Makin tinggi, makin jelas pemisahan kelompoknya."),
    ("Titik prediksi (origin)", "Tanggal model membuat prediksi, hanya dengan data sebelum tanggal itu."),
    ("Rasio MAE", "Galat absolut rata-rata sebuah model dibagi galat model dasar. Di bawah 1 berarti lebih akurat."),
    ("Uji Diebold–Mariano (DM)", "Uji beda akurasi dua model prediksi. DM negatif berarti model pembanding kurang akurat dari "
     "model dasar."),
    ("M0, M1, M2, M3", "Model prediksi. M0 menebak tanpa perubahan, M1 model dasar (regresi ridge), M2 model dasar ditambah "
     "kurs dan harga dunia, M3 gradient boosting dengan identitas seri."),
    ("C1-tuned, K4", "Model eksploratif di laporan lengkap. C1-tuned menebak arah harga (naik atau turun), K4 menilai risiko "
     "kenaikan besar. Keduanya tidak menguji hipotesis."),
    ("Pseudo-real-time", "Evaluasi dengan versi data terakhir karena riwayat revisi data tidak tersedia."),
    ("Rangkaian harga identik", "Harga harian yang sama selama minimal 5 hari teramati. Bisa berarti harga kaku atau harga hari "
     "sebelumnya yang dipakai saat pasar tutup. Keduanya tidak bisa dibedakan."),
    ("HET, HAP", "Harga eceran tertinggi dan harga acuan pembelian atau penjualan yang ditetapkan pemerintah."),
    ("PIHPS, JISDOR, Pink Sheet", "Harga pangan harian per provinsi (Bank Indonesia), kurs rupiah terhadap dolar AS harian "
     "(Bank Indonesia), dan harga komoditas dunia bulanan (Bank Dunia)."),
    ("TPID", "Tim Pengendalian Inflasi Daerah, pengguna sasaran KAGAMI."),
]

SOURCE_NAMES = {"pihps (varian representatif)": "PIHPS harian (varian representatif)", "jisdor": "JISDOR",
                "pinksheet": "Pink Sheet Bank Dunia", "brent": "Harga minyak Brent (FRED)",
                "dollar_index": "Indeks dolar AS (FRED)", "bps_import_monthly": "Impor bulanan BPS",
                "comtrade_import": "Impor UN Comtrade", "bapanas_panel": "Panel Harga Bapanas"}


def _clean(text: str) -> str:
    """Teks sumber di configs/sources.yaml untuk tampilan: tanpa kode internal dan notasi e_t/w_it, titik koma → koma."""
    text = re.sub(r"\s*\((?:e_t|w_it)\)", "", plain_text(text))
    return text.replace("; ", ", ").replace(" .. ", " s.d. ").strip()


def _sections(md: str) -> dict[str, str]:
    """Laporan Tahap 0 → {nomor bagian: isi} dari judul `## n. ...`."""
    out = {}
    for part in re.split(r"(?m)^## ", md)[1:]:
        title, _, body = part.partition("\n")
        out[title.split(".")[0].strip()] = body
    return out


def _table(body: str) -> pd.DataFrame:
    """Tabel markdown pertama di sebuah bagian → DataFrame (angka dikonversi bila bisa)."""
    rows = [ln.strip().strip("|").split("|") for ln in body.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 3:
        return pd.DataFrame()
    df = pd.DataFrame([[c.strip() for c in r] for r in rows[2:]], columns=[c.strip() for c in rows[0]])
    for c in df.columns:
        num = pd.to_numeric(df[c].str.replace("–", "", regex=False), errors="coerce")
        if num.notna().sum() == df[c].ne("–").sum() and num.notna().any():
            df[c] = num
    return df


def quality_checks(report: str) -> None:
    """Pemeriksaan kualitas data dari laporan Tahap 0: satu kalimat per pemeriksaan (angka dihitung dari tabel laporan),
    tabel berlabel pembaca di expander. Bagian yang tidak ada dilewati."""
    sec = _sections(report)
    lines, tables = [], []
    cov = _table(sec.get("1", ""))
    if {"source", "n_rows", "start", "end"} <= set(cov.columns):
        lines.append(f"Kami memakai {len(cov)} sumber utama. Data harga eceran PIHPS berisi "
                     f"{fmt_num(float(cov['n_rows'].iloc[0]), 0)} harga harian teramati (provinsi × komoditas × hari).")
        tables.append(("Cakupan per sumber", pd.DataFrame({
            "Sumber": cov["source"].map(lambda s: SOURCE_NAMES.get(s, s)), "Jumlah baris": cov["n_rows"].astype(int),
            "Awal": cov["start"], "Akhir": cov["end"]})))
    spk = _table(sec.get("6", ""))
    if {"commodity", "n_flagged"} <= set(spk.columns):
        lines.append(f"Kami menandai {int(spk['n_flagged'].sum())} hari dengan lonjakan harga satu hari, yaitu harga yang "
                     f"melonjak lebih dari {fmt_num(100 * (math.exp(0.5) - 1), 0)}% lalu kembali keesokan harinya. Hari itu "
                     "tetap ada di data.")
        tables.append(("Lonjakan harga satu hari", pd.DataFrame({
            "Komoditas": spk["commodity"].map(lambda c: labels.get(c, c)), "Hari ditandai": spk["n_flagged"].astype(int)})))
    imp = _table(sec.get("7", ""))
    if {"year", "n_hs8", "n_ok"} <= set(imp.columns):
        lines.append(f"Jumlah impor bulanan BPS sama dengan total tahunannya untuk {int(imp['n_ok'].sum())} dari "
                     f"{int(imp['n_hs8'].sum())} pasangan kode barang dan tahun.")
        tables.append(("Impor bulanan BPS dibandingkan dengan total tahunan", pd.DataFrame({
            "Tahun": imp["year"].astype(int), "Kode barang": imp["n_hs8"].astype(int), "Cocok": imp["n_ok"].astype(int)})))
    bap = _table(sec.get("8", ""))
    if {"commodity", "median_bias_log", "median_corr_dlog"} <= set(bap.columns):
        gap = 100 * (bap["median_bias_log"].map(math.exp) - 1)
        top = bap.loc[gap.abs().idxmax(), "commodity"]
        lines.append(f"Perubahan harga bulanan PIHPS bergerak searah dengan Panel Harga Bapanas (korelasi median "
                     f"{fmt_num(bap['median_corr_dlog'].min(), 2)} sampai {fmt_num(bap['median_corr_dlog'].max(), 2)}). "
                     f"Selisih tingkat harga terbesar ada pada {labels.get(top, top).lower()} "
                     f"({fmt_num(gap.abs().max(), 1)}%). Minyak goreng tidak dibandingkan karena varian kedua sumber berbeda.")
        tables.append(("PIHPS dibandingkan dengan Panel Harga Bapanas, 2022 sampai 2026", pd.DataFrame({
            "Komoditas": bap["commodity"].map(lambda c: labels.get(c, c)),
            "Provinsi": bap["n_prov"].astype(int) if "n_prov" in bap else None,
            "Selisih harga PIHPS terhadap Bapanas (%)": gap.round(1),
            "Korelasi perubahan bulanan": bap["median_corr_dlog"].round(2)})))
    hs = _table(sec.get("9", ""))
    if {"comtrade_code", "ok"} <= set(hs.columns):
        ok = hs["ok"].astype(str).eq("True")
        bad = list(hs.loc[~ok, "comtrade_code"].astype(str))
        txt = (f"{int(ok.sum())} dari {len(hs)} kode impor UN Comtrade cocok dengan jumlah kode BPS padanannya pada bulan "
               "yang sama, dengan selisih nilai paling banyak 1%.")
        if bad == ["1511"]:
            txt += (" Satu-satunya yang tidak cocok adalah minyak sawit (HS 1511), karena rincian BPS-nya tidak lengkap. "
                    "Kode ini tidak kami pakai untuk porsi impor.")
        lines.append(txt)
    if lines:
        st.markdown("\n".join(f"- {x}" for x in lines))
    if tables:
        with st.expander("Tabel pemeriksaan"):
            for title, df in tables:
                st.caption(title)
                show_table(df.dropna(axis=1, how="all"))


st.markdown("## Sumber data")
rows = [{"Sumber": v.get("publisher", k), "Peran": _clean(v.get("role", "")), "Cakupan": _clean(v.get("coverage", "")),
         "Lisensi": v.get("license", ""), "Ikut paket juri": bool(v.get("redistribute", False)),
         "key": k, "opsional": bool(v.get("optional", False))} for k, v in CFG.sources.items()]
src = pd.DataFrame(rows)
ck = load("checksums")
if ck is not None and {"source", "retrieved_at"} <= set(ck.columns):
    got_at = ck.groupby("source", as_index=False)["retrieved_at"].max()
    got_at["retrieved_at"] = got_at["retrieved_at"].astype(str).str[:10]
    src = src.merge(got_at.rename(columns={"source": "key", "retrieved_at": "Diambil"}), on="key", how="left")
cols = [c for c in ("Sumber", "Peran", "Cakupan", "Lisensi", "Diambil", "Ikut paket juri") if c in src]
show_table(src.loc[~src["opsional"], cols])
note("Data mentah tanpa hak redistribusi tidak ikut paket juri. Paket berisi dataset turunan (izin Bank Indonesia mencakup "
     "redistribusi data turunan) dan sumber berlisensi terbuka.")
with st.expander("Sumber tambahan untuk eksplorasi prediksi (tidak dipakai uji utama)"):
    show_table(src.loc[src["opsional"], cols])

st.markdown("## Cara kami mengolah data")
el = load("eligibility")
n_el = f"{int(el['eligible'].sum())} dari {len(el)}" if el is not None and "eligible" in el else "sebagian besar"
st.markdown(
    "1. Kami merata-ratakan harga harian PIHPS per minggu (Senin sampai Minggu) untuk 10 komoditas di 34 provinsi, dari "
    f"Januari 2018 sampai November 2026. Sebanyak {n_el} seri provinsi dan komoditas cukup lengkap untuk dianalisis.\n"
    "2. Kurs rupiah memakai JISDOR harian yang dirata-ratakan per minggu. Harga dunia memakai Pink Sheet Bank Dunia (bulanan, "
    "dalam dolar AS) yang kami konversi ke rupiah dengan rata-rata JISDOR bulan yang sama.\n"
    "3. Untuk setiap minggu ke-$h$ (0 sampai 12), kami mengukur seberapa jauh harga bergerak setelah kurs berubah. Kami "
    "mengendalikan pergerakan harga sebelumnya, harga minyak Brent, musim bulanan, dan minggu sekitar Idulfitri. Metode ini "
    "disebut proyeksi lokal.\n"
    "4. Setiap hasil kami bandingkan dengan 499 versi data yang urutan waktu kursnya digeser acak minimal 52 minggu. Respons "
    "yang tidak melampaui sebaran data acak tidak kami sebut temuan.\n"
    "5. Hipotesis, parameter, dan aturan uji kami bekukan pada 20 November 2026, sebelum estimasi dilihat.")
with st.expander("Rumus model"):
    st.markdown("Respons harga diukur dengan regresi berikut untuk setiap minggu ke-$h$:")
    st.latex(r"\begin{aligned} p_{s,t+h} - p_{s,t-1} = {}& \alpha_s + \beta(h)\,\Delta e_t + \omega(h)\,\Delta w_t \\"
             r" &+ \sum_{l=1}^{4}\big(\phi_l\,\Delta p_{s,t-l} + \psi_l\,\Delta e_{t-l} + \chi_l\,\Delta w_{t-l}\big) \\"
             r" &+ \sum_{l=0}^{4}\pi_l\,\Delta b_{t-l} + S(t) + u_{s,t+h} \end{aligned}")
    st.markdown(
        "- $p_{s,t}$ adalah log harga eceran seri $s$ (satu provinsi dan satu komoditas) pada minggu $t$.\n"
        "- $\\Delta e_t$ adalah perubahan log kurs rupiah per dolar AS, $\\Delta w_t$ perubahan log harga dunia dalam rupiah, "
        "dan $\\Delta b_t$ perubahan log harga minyak Brent.\n"
        "- $\\alpha_s$ menyerap perbedaan tingkat harga antarseri. $S(t)$ menyerap musim bulanan dan minggu sekitar Idulfitri.\n"
        "- $\\beta(h)$ adalah respons harga terhadap kurs. Karena keduanya dalam log, $\\beta(h) = 0{,}10$ berarti harga naik "
        "sekitar 0,10% untuk setiap 1% pelemahan rupiah. Galat baku dikelompokkan per minggu.")
    st.markdown("Penerusan kurs membagi respons harga dengan respons kurs terhadap dirinya sendiri, $\\gamma(h)$:")
    st.latex(r"PT(h) = \frac{\beta(h)}{\gamma(h)}")
    st.markdown("Halaman Simulasi rupiah dan batas Rupiah di laporan lengkap mengubah penerusan kurs menjadi perubahan "
                "harga untuk pelemahan rupiah sebesar $x$ persen:")
    st.latex(r"\Delta\text{harga}\ (\%) = 100\left[\exp\big(PT(h)\cdot\ln(1 + x/100)\big) - 1\right]")

got = need("eligibility", "mde")
if got:
    st.markdown("## Kelengkapan seri")
    el = got["eligibility"]
    c1, c2 = st.columns([1, 3])
    c1.metric("Seri provinsi × komoditas yang layak", f"{int(el['eligible'].sum())} / {len(el)}")
    per = (el.groupby("commodity", as_index=False).agg(seri=("eligible", "size"), layak=("eligible", "sum"))
           .assign(Komoditas=lambda d: d["commodity"].map(labels))
           .rename(columns={"seri": "Seri", "layak": "Layak"})[["Komoditas", "Seri", "Layak"]])
    with c2:
        show_table(per)
    note("Sebuah seri layak bila minggu tanpa pengamatan paling banyak 20%, tidak ada celah lebih dari 8 minggu, dan setiap "
         "tahun minimal 70% minggunya teramati. Seri yang tidak layak tetap dilaporkan.")

    report = load("stage0_report")
    if isinstance(report, str) and report.strip():
        st.markdown("## Pemeriksaan kualitas data")
        quality_checks(report)

    st.markdown("## Efek terkecil yang dapat dideteksi")
    mde = got["mde"].copy()
    mde["Komoditas"] = mde["commodity"].map(labels)
    if "unit" in mde:
        mde["Wilayah"] = mde["unit"].astype(str).map(lambda u: names.get(u, u))
    show = {"Komoditas": "Komoditas", "horizon": "Minggu ke-", "mde_beta": "Respons terhadap kurs (%)",
            "mde_pt": "Penerusan kurs", "mde_asym_pt": "Selisih melemah vs menguat (penerusan kurs)"}
    nat = mde[mde["level"] == "national"]
    show_table(nat[[c for c in show if c in nat]].rename(columns=show).round(2))
    note("Kami menghitung angka ini sebelum melihat hasil estimasi. Contoh: bila efek terkecil untuk penerusan kurs adalah 0,5, "
         "penerusan di bawah setengah pelemahan rupiah tidak dapat dibedakan dari nol.")
    st.latex(r"\text{MDE} = \left(z_{0{,}975} + z_{0{,}80}\right)\cdot SE \approx 2{,}80\cdot SE")
    reg = mde[mde["level"] == "region"]
    if len(reg):
        with st.expander("Per wilayah"):
            cols_r = {"Komoditas": "Komoditas", "Wilayah": "Wilayah", **{k: v for k, v in show.items() if k != "Komoditas"}}
            show_table(reg[[c for c in cols_r if c in reg]].rename(columns=cols_r).round(2))

st.markdown("## Daftar istilah")
st.markdown("| Istilah | Arti |\n|---|---|\n" + "\n".join(f"| {t} | {a} |" for t, a in GLOSSARY))

st.markdown("## Reproduksi")
stat = artifact_status(CFG)
n_ok = int(stat["available"].sum()) if "available" in stat else 0
st.markdown(
    "Juri dapat mereproduksi hasil pada tiga tingkat:\n\n"
    "1. Menjalankan aplikasi ini dari hasil yang dikirim.\n"
    "2. Menjalankan semua tahap analisis dari dataset turunan yang dikirim (`python -m kagami all`).\n"
    "3. Mengunduh ulang data mentah dari sumbernya.\n\n"
    f"Paket juri memuat {n_ok} dari {len(stat)} hasil analisis. Setiap tahap analisis juga mencatat log eksekusi berisi "
    "sidik jari data masukan, kode, dan hasil. Log itu ada di folder `logs/` paket juri dan bisa dibaca dengan perintah "
    "`python -m kagami runs`. Langkah lengkapnya ada di README bagian 10.")

footer("Bank Indonesia (JISDOR, PIHPS), Bank Dunia, FRED, FAOSTAT, BPS, Bapanas")
