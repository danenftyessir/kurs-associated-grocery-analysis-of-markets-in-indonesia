"""Halaman 1 -- Ringkasan (D-170, D-171): jawaban lebih dulu. Kalimat pembuka dalam Rupiah + grafik batas perubahan harga
per komoditas, lima pertanyaan penelitian beserta jawabannya, dan cara menguji. Semua angka dibaca dari artefak saat
halaman dimuat (harga acuan Rupiah dari tabel batas Rupiah `findings`); tidak ada angka hasil yang ditulis tangan."""

import pandas as pd
import streamlit as st

from common import (CFG, PAGE, STRETCH, commodity_labels, fmt_interval, fmt_num, fmt_rp, footer, load, names_list,
                    nav_link, need, note, reference_prices)
from kagami.viz import plots

st.set_page_config(page_title="KAGAMI · Ringkasan", layout="wide")

X, H = 5, 8          # skenario utama tabel batas Rupiah di findings: rupiah melemah 5%, 8 minggu
WORDS = {1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima"}


def _excludes_zero(lo: pd.Series, hi: pd.Series) -> pd.Series:
    return (lo > 0) | (hi < 0)


def _rq1(nat: pd.DataFrame) -> str:
    e8 = nat[(nat["driver"] == "e") & (nat["horizon"] == H)].dropna(subset=["ci_low", "ci_high"])
    det = e8.loc[_excludes_zero(e8["ci_low"], e8["ci_high"]), "commodity"]
    a = (f"Belum terlihat. Dalam {H} minggu, respons harga terhadap kurs rupiah belum bisa dibedakan dari nol untuk "
         f"ke-{len(e8)} komoditas." if det.empty else
         f"Dalam {H} minggu, respons harga terhadap kurs rupiah terlihat pada {names_list(det)} ({len(det)} dari "
         f"{len(e8)} komoditas).")
    mg = nat[(nat["driver"] == "w") & (nat["commodity"] == "minyak_goreng") & (nat["horizon"] == 4)]
    if len(mg) and _excludes_zero(mg["ci_low"], mg["ci_high"]).iloc[0]:
        r = mg.iloc[0]
        a += (" Hubungan yang paling konsisten ada di minyak goreng: kenaikan harga sawit dunia 1% (dalam rupiah) "
              f"berasosiasi dengan kenaikan harga minyak goreng {fmt_num(r['estimate'], 2)}% dalam 4 minggu "
              f"(rentang {fmt_interval(r['ci_low'], r['ci_high'], 2, pct=True)}).")
    return a


def _rq2(nat: pd.DataFrame) -> str:
    het, sel = load("heterogeneity"), load("cluster_selection")
    q = het[het["statistic"] == "Q"]
    rej = q.loc[q["reject"].fillna(False).astype(bool), "commodity"].tolist()
    k = int(sel.loc[sel["accepted"], "k"].max()) if sel["accepted"].any() else 1
    a = (f"Hanya sedikit. Perbedaan antarprovinsi yang lebih besar dari hasil kurs acak muncul pada {names_list(rej)}."
         if rej else "Tidak terlihat. Tidak ada komoditas yang responsnya berbeda antarprovinsi melebihi hasil kurs acak.")
    return a + (" Provinsi tidak membentuk kelompok dengan pola yang sama, jadi angka nasional per komoditas adalah titik "
                "awal yang wajar." if k == 1 else f" Provinsi membentuk {k} kelompok yang lolos uji data acak.")


def _rq3(nat: pd.DataFrame) -> str:
    asym = load("asymmetry")
    c = asym[asym["confirmatory"].fillna(False).astype(bool) & (asym["horizon"] == H)]
    rej = c["reject"].fillna(False).astype(bool)
    if rej.any():
        return f"Berbeda untuk {names_list(c.loc[rej, 'commodity'])}."
    ps = " dan ".join(fmt_num(p, 2) for p in c["p_value"])
    n = WORDS.get(len(c), str(len(c)))
    return (f"Tidak terlihat beda. Untuk {names_list(c['commodity'])}, {n} komoditas yang datanya cukup presisi untuk diuji "
            f"formal, respons saat rupiah melemah dan saat menguat tidak berbeda nyata (p {ps}).")


def _rq4(nat: pd.DataFrame) -> str:
    assoc = load("assoc")
    ken = assoc[assoc["method"].astype(str).str.startswith("kendall")].iloc[0]
    a = (f"Tidak terbukti. Di antara 10 komoditas, urutan porsi impor tidak sejalan dengan urutan kepekaan (korelasi "
         f"peringkat Kendall {fmt_num(ken['estimate'], 2)}, p {fmt_num(ken['p_value'], 2)}).")
    h3 = assoc[(assoc["method"].astype(str) == "meta_regression_re_one_sided") & (assoc["commodity"] == "ALL")
               & (assoc["feature"] == "ln_dist_hub") & (assoc["horizon"] == 4)]
    if len(h3):
        a += (" Jarak provinsi ke pusat distribusi juga tidak berhubungan dengan respons 4 minggu (p satu sisi "
              f"{fmt_num(h3['p_value'].iloc[0], 2)}).")
    return a


def _rq5(nat: pd.DataFrame) -> str:
    fe = load("forecast_eval")
    m2 = fe[(fe["model"] == "M2") & (fe["subset"] == "all") & (fe["commodity"] == "ALL")]
    if "level" in m2:
        m2 = m2[m2["level"] == "all"]
    m2 = m2.sort_values("horizon")
    if not len(m2):
        raise KeyError("M2")
    chg = " dan ".join(fmt_num(100 * (v - 1), 1, sign=True) + "%" for v in m2["mae_ratio_vs_m1"])
    hs = " dan ".join(str(int(h)) for h in m2["horizon"])
    worse = (m2["mae_ratio_vs_m1"] > 1).all()
    sig = (m2["dm_p"] < 0.05).all() if "dm_p" in m2 else False
    if worse:
        up = " dan ".join(fmt_num(100 * (v - 1), 1) + "%" for v in m2["mae_ratio_vs_m1"])
        return (f"Tidak. Menambahkan kurs dan harga dunia membuat galat prediksi {hs} minggu naik {up}"
                + (", dan uji Diebold–Mariano menyatakan selisih itu nyata." if sig else ", selisih yang tidak nyata."))
    return f"Menambahkan kurs dan harga dunia mengubah galat prediksi {hs} minggu sebesar {chg}."


RQS = [("Seberapa besar harga pangan bergerak saat kurs rupiah berubah?", _rq1, "respons", "Kurva respons per komoditas"),
       ("Apakah kepekaan itu berbeda antarprovinsi?", _rq2, "wilayah", "Uji perbedaan antarprovinsi"),
       ("Apakah dampak rupiah melemah sama dengan saat menguat?", _rq3, "respons", "Respons saat melemah dan menguat"),
       ("Apakah porsi impor dan letak provinsi menjelaskan kepekaan?", _rq4, "faktor", "Jalur impor dan karakteristik provinsi"),
       ("Apakah memantau kurs membantu memprediksi harga?", _rq5, "prediksi", "Evaluasi prediksi")]


def _answers(nat: pd.DataFrame) -> list[tuple[str, str, str, str]]:
    """(pertanyaan, jawaban, halaman, label tautan) per pertanyaan penelitian. Jawaban dihitung dari artefak; artefak atau
    kolom yang belum ada (deploy sebagian, data uji sintetis) → kalimat netral, halaman tetap tampil."""
    out = []
    for question, fn, page, link in RQS:
        try:
            answer = fn(nat)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            answer = "Hasilnya belum tersedia di artefak yang dimuat."
        out.append((question, answer, PAGE[page], link))
    return out


got = need("profiles")
if got:
    labels = commodity_labels()
    prof = got["profiles"]
    nat = prof[(prof["level"] == "national") & (prof["unit"].astype(str) == "ALL")]
    pt = nat[(nat["driver"] == "PT") & (nat["horizon"] == H)].dropna(subset=["ci_low", "ci_high"]).copy()
    for c in ("estimate", "ci_low", "ci_high"):
        pt[c] = plots.scenario_change(pt[c], X)
    pt["komoditas"] = pt["commodity"].map(lambda c: labels.get(c, c))
    small, mid, loose = pt[pt["ci_high"] <= 2], pt[(pt["ci_high"] > 2) & (pt["ci_high"] <= X)], pt[pt["ci_high"] > X]
    prices = reference_prices()
    beras = pt[pt["commodity"] == "beras"]

    if beras.empty:
        title = "Seberapa peka harga pangan eceran terhadap pelemahan rupiah?"
    else:
        hi = float(beras["ci_high"].iloc[0])
        price, per = prices.get("beras", (None, "kg"))
        amount = (f"{fmt_rp(price * hi / 100, sign=False)} per {'kilogram' if per == 'kg' else per}" if price
                  else fmt_num(hi, 2, pct=True))
        title = (f"Pelemahan rupiah {X}% berasosiasi dengan kenaikan harga beras paling tinggi "
                 f'<span class="kg-hl">{amount}</span> dalam {H} minggu.')
    st.markdown(
        f'<div class="kg-hero"><h1 class="kg-title">{title}</h1>'
        '<p class="kg-byline"><b>KAGAMI</b>, Kurs-Associated Grocery Analysis of Markets in Indonesia. Dalam bahasa Jepang, '
        '<i>kagami</i> berarti cermin.</p></div>', unsafe_allow_html=True)

    left, right = st.columns([5, 6], gap="large")
    with left:
        period = CFG.params["period"]
        text = (f"Kami mengukur seberapa jauh harga eceran 10 komoditas pangan di 34 provinsi bergerak bersama kurs rupiah, "
                f"dari {str(period['start'])[:4]} sampai {str(period['freeze'])[:4]}.")
        if len(small):
            text += f" Untuk {names_list(small['commodity'], labels)}, batas kenaikan harganya di bawah 2%."
        if len(mid):
            text += f" Batas {names_list(mid['commodity'], labels)} di bawah {X}%."
        if len(loose):
            text += (f" Rentang untuk {names_list(loose['commodity'], labels)} melebar sampai "
                     f"{fmt_num(loose['ci_high'].max(), 0)}%, terlalu lebar untuk dipakai sebagai batas.")
        st.markdown(f'<p class="kg-lead">{text}</p>', unsafe_allow_html=True)
        note("Batas kenaikan adalah ujung atas rentang 95% dari pola historis tingkat nasional. Harga acuan Rupiah adalah "
             "median antarprovinsi selama 8 minggu sampai 16 November 2026.")
        nav_link(PAGE["simulasi"], "Coba simulasi pelemahan rupiah", ":material/tune:")
        nav_link(PAGE["provinsi"], "Lihat label harga di provinsi Anda", ":material/location_on:")
        nav_link(PAGE["lini_masa"], "Lihat rupiah dan harga sejak 2018", ":material/timeline:")
    with right:
        if len(pt):
            d = pt.assign(width=pt["ci_high"] - pt["ci_low"]).sort_values("width", ascending=False)
            st.plotly_chart(plots.forest(
                d, ["komoditas"], f"Perubahan harga {H} minggu\nsetelah rupiah melemah {X}%",   # kolom sempit
                x_title="perubahan harga eceran nasional (%)", x_range=(-10, 10),
                subtitle="Titik: perkiraan. Garis: rentang 95%. Segitiga: rentang melewati batas grafik."), **STRETCH)

    st.markdown("## Jawaban atas lima pertanyaan penelitian")
    for question, answer, page, link in _answers(nat):
        st.markdown('<div class="kg-rule"></div>', unsafe_allow_html=True)
        q, a = st.columns([2, 5], gap="large")
        q.markdown(f'<p class="kg-rq">{question}</p>', unsafe_allow_html=True)
        with a:
            st.markdown(f'<p class="kg-ans">{answer}</p>', unsafe_allow_html=True)
            nav_link(page, link, ":material/arrow_forward:")
    st.markdown('<div class="kg-rule"></div>', unsafe_allow_html=True)

    st.markdown("## Cara kami menguji")
    el = load("eligibility")
    n_el = f"{int(el['eligible'].sum())} dari {len(el)}" if el is not None else "sebagian besar"
    st.markdown(
        f"Kami meringkas harga harian Bank Indonesia (PIHPS) menjadi harga mingguan. Sebanyak {n_el} seri provinsi dan "
        "komoditas cukup lengkap untuk dianalisis. Hipotesis dan aturan uji kami bekukan pada 20 November 2026, sebelum hasil "
        f"estimasi dilihat. Setiap hasil kami bandingkan dengan {CFG.params['inference']['placebo_R']} versi data yang urutan "
        "waktu kursnya digeser acak. Dengan cara itu hasil nol pun punya ukuran, yaitu efek terkecil yang akan tertangkap "
        "bila efek itu ada.")
    nav_link(PAGE["data"], "Data, metode, dan daftar istilah", ":material/dataset:")
    note("KAGAMI masih prototipe riset. Kami belum menguji bersama TPID ambang kenaikan harga yang perlu ditindaklanjuti, "
         "sehingga aplikasi ini belum siap dipakai sebagai peringatan dini.")

footer("PIHPS dan JISDOR (Bank Indonesia), Pink Sheet (Bank Dunia)")
