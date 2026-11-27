"""Halaman 1 -- Beranda (D-170): jawaban lebih dulu. Kalimat pembuka + grafik batas perubahan harga per komoditas,
lima pertanyaan penelitian beserta jawabannya, dan dasar kepercayaan. Semua angka dibaca dari artefak saat halaman
dimuat; tidak ada angka hasil yang ditulis tangan di halaman ini."""

import pandas as pd
import streamlit as st

from common import CFG, STRETCH, commodity_labels, fmt_interval, fmt_num, footer, load, nav_link, need
from kagami.viz import plots

st.set_page_config(page_title="KAGAMI · Beranda", layout="wide")

X, H = 5, 8          # skenario utama tabel batas Rupiah di findings: rupiah melemah 5%, horizon 8 minggu
PAGE = {"kepekaan": "pages/2_Kepekaan_Harga_Regional.py", "regional": "pages/3_Pola_Respons.py",
        "eksposur": "pages/4_Eksposur_dan_Nilai_Prediktif.py", "skenario": "pages/5_Penjelajah_Skenario.py",
        "temuan": "pages/6_Temuan_Penelitian.py", "data": "pages/8_Data_dan_Metode.py"}


def _excludes_zero(lo: pd.Series, hi: pd.Series) -> pd.Series:
    return (lo > 0) | (hi < 0)


def _names(coms, labels) -> str:
    items = [labels.get(c, c).lower() for c in coms]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " dan " + items[-1] if items else "tidak ada komoditas"


def _rq1(nat: pd.DataFrame, labels: dict) -> str:
    e8 = nat[(nat["driver"] == "e") & (nat["horizon"] == H)].dropna(subset=["ci_low", "ci_high"])
    n_det = int(_excludes_zero(e8["ci_low"], e8["ci_high"]).sum())
    a = f"Respons nasional terhadap IDR/USD terdeteksi pada {n_det} dari {len(e8)} komoditas (h = {H}, interval resmi). "
    mg = nat[(nat["driver"] == "w") & (nat["commodity"] == "minyak_goreng") & (nat["horizon"] == 4)]
    if len(mg):
        r = mg.iloc[0]
        a += (f"Yang paling konsisten: minyak goreng dengan harga sawit dunia dalam rupiah, ω(4) = "
              f"{fmt_num(r['estimate'], 2)} ({fmt_interval(r['ci_low'], r['ci_high'], 2)}).")
    return a


def _rq2(nat: pd.DataFrame, labels: dict) -> str:
    het, sel = load("heterogeneity"), load("cluster_selection")
    q = het[het["statistic"] == "Q"]
    rej = q.loc[q["reject"].fillna(False).astype(bool), "commodity"].tolist()
    k = int(sel.loc[sel["accepted"], "k"].max()) if sel["accepted"].any() else 1
    return (f"Variasi antarprovinsi melampaui plasebo hanya untuk {_names(rej, labels)}. "
            + ("Provinsi tidak membentuk kelompok (k = 1), jadi profil nasional per komoditas adalah titik awal yang wajar."
               if k == 1 else f"Provinsi membentuk {k} kelompok yang lolos uji plasebo."))


def _rq3(nat: pd.DataFrame, labels: dict) -> str:
    asym = load("asymmetry")
    c = asym[asym["confirmatory"].fillna(False).astype(bool) & (asym["horizon"] == H)]
    rej = c["reject"].fillna(False).astype(bool)
    if rej.any():
        return f"Asimetri terdeteksi pada uji konfirmatori untuk {_names(c.loc[rej, 'commodity'], labels)}."
    ps = " dan ".join(fmt_num(p, 2) for p in c["p_value"])
    return (f"Tidak ada asimetri depresiasi–apresiasi yang terdeteksi. Uji konfirmatori untuk "
            f"{_names(c['commodity'], labels)} tidak menolak (p Wald {ps}).")


def _rq4(nat: pd.DataFrame, labels: dict) -> str:
    assoc = load("assoc")
    ken = assoc[assoc["method"].astype(str).str.startswith("kendall")].iloc[0]
    a = (f"Di antara 10 komoditas, rasio impor langsung tidak berasosiasi monoton dengan pass-through "
         f"(τ-b {fmt_num(ken['estimate'], 3)}, p eksak {fmt_num(ken['p_value'], 2)}).")
    h3 = assoc[(assoc["method"].astype(str) == "meta_regression_re_one_sided") & (assoc["commodity"] == "ALL")
               & (assoc["feature"] == "ln_dist_hub") & (assoc["horizon"] == 4)]
    if len(h3):
        a += f" Keterpencilan provinsi juga tidak (H3, p satu sisi {fmt_num(h3['p_value'].iloc[0], 2)})."
    return a


def _rq5(nat: pd.DataFrame, labels: dict) -> str:
    fe = load("forecast_eval")
    m2 = fe[(fe["model"] == "M2") & (fe["subset"] == "all") & (fe["commodity"] == "ALL")]
    if "level" in m2:
        m2 = m2[m2["level"] == "all"]
    m2 = m2.sort_values("horizon")
    ratios = " dan ".join(fmt_num(v, 3) for v in m2["mae_ratio_vs_m1"])
    if not len(m2):
        raise KeyError("M2")
    if (m2["mae_ratio_vs_m1"] > 1).all():
        dms = " dan ".join(fmt_num(v, 2, sign=True) for v in m2["dm_stat"])
        return ("Menambahkan kurs dan harga dunia tidak memperbaiki prediksi 4 dan 8 minggu: MAE justru sedikit lebih "
                f"buruk (rasio {ratios}; statistik DM {dms}).")
    return f"Rasio MAE model dengan kurs & harga dunia terhadap model dasar: {ratios} (lihat uji DM di halaman evaluasi)."


RQS = [("RQ1", "Seberapa besar dan secepat apa harga merespons kurs?", _rq1, "kepekaan", "Kurva respons"),
       ("RQ2", "Lebih ditentukan komoditas atau lokasi?", _rq2, "regional", "Pola regional"),
       ("RQ3", "Apakah depresiasi dan apresiasi berbeda dampaknya?", _rq3, "kepekaan", "Asimetri"),
       ("RQ4", "Karakteristik apa yang berasosiasi dengan kepekaan?", _rq4, "eksposur", "Eksposur"),
       ("RQ5", "Apakah memantau kurs membantu memprediksi harga?", _rq5, "eksposur", "Prediksi")]


def _answers(nat: pd.DataFrame, labels: dict) -> list[tuple[str, str, str, str, str]]:
    """(kode, pertanyaan, jawaban, halaman, label tautan) per RQ. Jawaban dihitung dari artefak; artefak atau kolom yang
    belum ada (deploy sebagian, data uji sintetis) → kalimat netral, halaman tetap tampil."""
    out = []
    for code, question, fn, page, link in RQS:
        try:
            answer = fn(nat, labels)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            answer = "Hasilnya belum tersedia di artefak yang dimuat; lihat halaman terkait."
        out.append((code, question, answer, PAGE[page], link))
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
    tight = pt[pt["ci_high"] <= X]
    loose = pt[pt["ci_high"] > X]
    beras = pt[pt["commodity"] == "beras"]
    period = CFG.params["period"]
    years = f"{str(period['start'])[:4]}–{str(period['freeze'])[:4]}"

    title = ("Seberapa peka harga pangan eceran terhadap pelemahan rupiah?" if beras.empty else
             f"Saat rupiah melemah {X}%, pola historis menempatkan kenaikan harga beras paling banyak "
             f'<span class="kg-hl">{fmt_num(beras["ci_high"].iloc[0], 2, pct=True)}</span> dalam {H} minggu.')
    lead = (f"KAGAMI memetakan seberapa besar harga eceran 10 komoditas pangan di 34 provinsi bergerak bersama kurs IDR/USD "
            f"dan harga dunia dalam rupiah, {years}. Untuk {len(tight)} dari {len(pt)} komoditas, batas atas kenaikan harga "
            f"yang konsisten dengan pelemahan rupiah {X}% berada di bawah {X}%. Untuk {_names(loose['commodity'], labels)}, "
            "harganya terlalu bergejolak untuk memberi batas yang berguna. Asosiasi yang paling konsisten justru antara "
            "minyak goreng dan harga sawit dunia dalam rupiah.")

    st.markdown(
        f'<div class="kg-hero"><h1 class="kg-title">{title}</h1>'
        '<p class="kg-byline"><b>KAGAMI</b> · Kurs-Associated Grocery Analysis of Markets in Indonesia · '
        '<i>kagami</i> = cermin</p></div>', unsafe_allow_html=True)
    left, right = st.columns([5, 6], gap="large")
    with left:
        st.markdown(
            f'<p class="kg-lead">{lead}</p>'
            '<p class="kg-qual">Batas atas = ujung atas interval 95% resmi dari rasio pass-through nasional; perubahan = '
            f'exp(PT({H}) × ln 1,05) − 1. Skenario bersyarat dari pola historis, bukan ramalan; asosiasi, bukan kausalitas.</p>',
            unsafe_allow_html=True)
        nav_link(PAGE["skenario"], "Coba skenario sendiri", ":material/tune:")
        nav_link(PAGE["temuan"], "Baca temuan lengkap", ":material/article:")
    with right:
        if len(pt):
            d = pt.assign(width=pt["ci_high"] - pt["ci_low"]).sort_values("width", ascending=False)
            st.plotly_chart(plots.forest(
                d, ["komoditas"], f"Rupiah melemah {X}%: perubahan harga {H} minggu",
                x_title="perubahan harga eceran nasional (%)",
                subtitle="Titik = estimasi · garis = interval 95% resmi · paling presisi di atas"), **STRETCH)

    st.markdown("## Lima pertanyaan, lima jawaban")
    for code, question, answer, page, link in _answers(nat, labels):
        st.markdown('<div class="kg-rule"></div>', unsafe_allow_html=True)
        q, a, go = st.columns([3, 6, 1.6], gap="medium")
        q.markdown(f'<p class="kg-rq">{question} <span class="kg-code">{code}</span></p>', unsafe_allow_html=True)
        a.markdown(f'<p class="kg-ans">{answer}</p>', unsafe_allow_html=True)
        with go:
            nav_link(page, link, ":material/arrow_forward:")
    st.markdown('<div class="kg-rule"></div>', unsafe_allow_html=True)

    st.markdown("## Mengapa angka ini bisa dipegang")
    el = load("eligibility")
    n_el = f"{int(el['eligible'].sum())} dari {len(el)}" if el is not None else "–"
    st.markdown(
        f"Panel mingguan dibangun dari harga harian PIHPS (Bank Indonesia); **{n_el} seri** provinsi × komoditas layak "
        "dianalisis. Hipotesis, parameter, dan aturan keputusan **dibekukan 20 November 2026 sebelum estimasi dilihat**. "
        f"Setiap uji dibandingkan dengan **{CFG.params['inference']['placebo_R']} replikasi plasebo** yang memutus kaitan "
        "waktu antara kurs dan harga, sehingga hasil nol pun punya ukuran: selisih terkecil yang akan terdeteksi bila ada. "
        "Aplikasi ini hanya membaca hasil yang sudah dihitung.")
    nav_link(PAGE["data"], "Data, metode & reproduksi", ":material/dataset:")
    st.info("**Status produk.** KAGAMI adalah prototipe riset dan analitik pendukung keputusan: aplikasi ini menyajikan pola "
            "historis beserta ketidakpastiannya. KAGAMI bukan sistem peringatan dini dan bukan rekomendasi operasi pasar, "
            "karena kebutuhan pengguna (ambang kenaikan, kapasitas pemantauan, toleransi alarm palsu) belum divalidasi "
            "dengan TPID (U109).")

footer("Turunan PIHPS & JISDOR (BI), Pink Sheet (Bank Dunia)", "% perubahan harga eceran nasional",
       "2018-01 s.d. pembekuan 2026-11-21")
