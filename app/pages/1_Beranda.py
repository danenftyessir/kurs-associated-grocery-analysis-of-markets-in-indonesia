"""Halaman 1 -- Ringkasan (D-170, D-171): jawaban lebih dulu. Kalimat pembuka dalam Rupiah + grafik batas perubahan harga
per komoditas, lima pertanyaan penelitian beserta jawabannya, dan cara menguji. Semua angka dibaca dari artefak saat
halaman dimuat (harga acuan Rupiah dari tabel batas Rupiah `findings`); tidak ada angka hasil yang ditulis tangan."""

import pandas as pd
import streamlit as st

from common import (CFG, PAGE, STRETCH, commodity_labels, fmt_interval, fmt_num, fmt_rp, footer, global_deviations,
                    het_detected, load, load_hex, names_list, nav_link, need, note, reference_prices, unit_names)
from kagami.viz import plots

st.set_page_config(page_title="KAGAMI · Ringkasan", layout="wide")

X, H = 5, 8          # skenario utama tabel batas Rupiah di findings: rupiah melemah 5%, 8 minggu
WORDS = {1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima"}


def _excludes_zero(lo: pd.Series, hi: pd.Series) -> pd.Series:
    return (lo > 0) | (hi < 0)


# Jawaban dibuka dengan hal yang bisa dipakai pembaca (D-179): hasil nol ditulis sebagai batas atau pegangan, bukan vonis
# "tidak terbukti" atas hipotesis. Isi dan angka tetap sama dengan findings; tidak ada klaim baru.
USABLE_PCT = 2.0      # batas atas skenario ≤ 2% = batas yang cukup sempit untuk dipakai (sama dengan kalimat pembuka beranda)


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else (" dan ".join(items) if len(items) == 2
                                              else ", ".join(items[:-1]) + ", dan " + items[-1])


def _rq1(nat: pd.DataFrame) -> str:
    pt = nat[(nat["driver"] == "PT") & (nat["horizon"] == H)].dropna(subset=["ci_high"]).copy()
    pt["hi"] = plots.scenario_change(pt["ci_high"], X)
    prices = reference_prices()
    labels = commodity_labels()
    use = pt[(pt["hi"] <= USABLE_PCT) & pt["commodity"].isin(prices)]
    use = use.assign(o=use["commodity"].map(list(labels).index)).sort_values("o")      # urutan komoditas tetap
    parts = [f"{fmt_rp(prices[c][0] * h / 100, sign=False)} per {prices[c][1]} untuk {labels.get(c, c).lower()}"
             for c, h in zip(use["commodity"], use["hi"])]
    if parts:
        a = (f"Kecil, setidaknya untuk {WORDS.get(len(parts), len(parts))} komoditas. Bila rupiah melemah {X}%, harga dalam "
             f"{H} minggu naik paling banyak {_join(parts)}. Kenaikan yang melebihi angka itu lebih besar dari yang biasa "
             "menyertai pelemahan rupiah, jadi penyebabnya perlu dicari di pasokan, musim, atau kebijakan.")
    else:
        e8 = nat[(nat["driver"] == "e") & (nat["horizon"] == H)].dropna(subset=["ci_low", "ci_high"])
        det = e8.loc[_excludes_zero(e8["ci_low"], e8["ci_high"]), "commodity"]
        a = (f"Dalam {H} minggu, harga bergerak bersama kurs rupiah pada {names_list(det)}." if len(det) else
             f"Dalam {H} minggu, gerak harga bersama kurs rupiah belum bisa dibedakan dari nol.")
    mg = nat[(nat["driver"] == "w") & (nat["commodity"] == "minyak_goreng") & (nat["horizon"] == 4)]
    if len(mg) and _excludes_zero(mg["ci_low"], mg["ci_high"]).iloc[0]:
        r = mg.iloc[0]
        a += (" Hubungan yang paling jelas ada di minyak goreng. Setiap kali harga sawit dunia dalam rupiah naik 1%, harga "
              f"minyak goreng naik {fmt_num(r['estimate'], 2)}% dalam 4 minggu berikutnya (rentang 95% "
              f"{fmt_interval(r['ci_low'], r['ci_high'], 2, pct=True)}).")
    return a


def _rq2(nat: pd.DataFrame) -> str:
    het, sel = load("heterogeneity"), load("cluster_selection")
    labels = commodity_labels()
    rej = [c for c in labels if c in het_detected(het)]
    n_all = int(het.loc[het["statistic"] == "Q", "commodity"].nunique())
    k = int(sel.loc[sel["accepted"], "k"].max()) if sel["accepted"].any() else 1
    if not rej:
        a = (f"Kepekaan tingkat nasional berlaku juga di setiap provinsi untuk ke-{n_all} komoditas. Perbedaan antarprovinsi "
             "tidak lebih besar dari kebetulan.")
    else:
        a = (f"Untuk {n_all - len(rej)} dari {n_all} komoditas, kepekaan tingkat nasional berlaku juga di setiap provinsi, "
             f"sejauh yang bisa dideteksi data. Perbedaan antarprovinsi yang lebih besar dari kebetulan hanya muncul pada "
             f"{names_list(rej, labels)}.")
        gd = global_deviations(load("province_calibrated"))
        fl = gd[(gd["q_global"] < 0.05) & (gd["driver"] == "e") & (gd["horizon"] == H)]
        if len(fl):
            names = unit_names()
            provs = list(dict.fromkeys(names.get(str(u), str(u)) for u in fl["unit"]))
            com = names_list(list(dict.fromkeys(fl["commodity"])), labels)
            a += f" Untuk {com}, {_join(provs)} paling jelas berbeda dari angka nasional."
    return a + (" Provinsi juga tidak membentuk kelompok dengan pola yang sama, jadi kami tidak menemukan dasar untuk membagi "
                "pemantauan per wilayah."
                if k == 1 else f" Provinsi membentuk {k} kelompok yang melampaui kebetulan.")


def _rq3(nat: pd.DataFrame) -> str:
    asym = load("asymmetry")
    c = asym[asym["confirmatory"].fillna(False).astype(bool) & (asym["horizon"] == H)]
    rej = c["reject"].fillna(False).astype(bool)
    if rej.any():
        return f"Berbeda untuk {names_list(c.loc[rej, 'commodity'])}."
    ps = " dan ".join(fmt_num(p, 2) for p in c["p_value"])
    n = WORDS.get(len(c), str(len(c)))
    return (f"Sejauh yang bisa dideteksi data, tidak ada beda antara respons harga saat rupiah melemah dan saat menguat. Untuk "
            f"{names_list(c['commodity'])}, {n} komoditas yang datanya cukup presisi untuk diuji, selisih kedua respons tidak "
            f"nyata secara statistik (nilai p {ps}, di atas batas 0,05). Untuk komoditas lain data belum cukup untuk "
            "menguji perbedaannya.")


def _rq4(nat: pd.DataFrame) -> str:
    assoc = load("assoc")
    ken = assoc[assoc["method"].astype(str).str.startswith("kendall")].iloc[0]
    a = ("Pilih komoditas pantauan dari kepekaan terukurnya, bukan dari porsi impornya. Di antara 10 komoditas, yang porsi "
         "impornya lebih besar tidak lebih peka terhadap rupiah (korelasi peringkat Kendall "
         f"{fmt_num(ken['estimate'], 2)}, nilai p {fmt_num(ken['p_value'], 2)}).")
    h3 = assoc[(assoc["method"].astype(str) == "meta_regression_re_one_sided") & (assoc["commodity"] == "ALL")
               & (assoc["feature"] == "ln_dist_hub") & (assoc["horizon"] == 4)]
    if len(h3):
        a += (" Provinsi yang jauh dari pusat distribusi (Jakarta, Surabaya, Makassar) juga tidak terbukti kurang peka dalam "
              f"4 minggu (nilai p satu sisi {fmt_num(h3['p_value'].iloc[0], 2)}).")
    return a


def _rq5(nat: pd.DataFrame) -> str:
    fe = load("forecast_eval")
    m2 = fe[(fe["model"] == "M2") & (fe["subset"] == "all") & (fe["commodity"] == "ALL")]
    if "level" in m2:
        m2 = m2[m2["level"] == "all"]
    m2 = m2.sort_values("horizon")
    if not len(m2):
        raise KeyError("M2")
    hs = " dan ".join(str(int(h)) for h in m2["horizon"])
    per = _join([f"{fmt_num(100 * (v - 1), 1)}% untuk {int(h)} minggu" for v, h in zip(m2["mae_ratio_vs_m1"], m2["horizon"])])
    worse = (m2["mae_ratio_vs_m1"] > 1).all()
    sig = (m2["dm_p"] < 0.05).all() if "dm_p" in m2 else False
    base = ("Model dasar kami hanya memakai riwayat harga, musim, dan harga minyak mentah dunia. ")
    if worse:
        return (f"Untuk prediksi {hs} minggu ke depan, riwayat harga lebih berguna daripada kurs. " + base
                + f"Menambahkan kurs dan harga dunia justru membuat rata-rata kesalahan prediksinya naik {per}"
                + (". Uji Diebold–Mariano menyatakan kenaikan itu nyata." if sig else ", kenaikan yang tidak nyata.")
                + " Kurs lebih tepat dipakai untuk memeriksa kenaikan harga yang sudah terjadi, dengan batas di pertanyaan "
                  "pertama, daripada untuk meramal.")
    chg = _join([f"{fmt_num(100 * (v - 1), 1, sign=True)}% untuk {int(h)} minggu"
                 for v, h in zip(m2["mae_ratio_vs_m1"], m2["horizon"])])
    return base + f"Menambahkan kurs dan harga dunia mengubah rata-rata kesalahan prediksinya {chg}."


RQS = [("Seberapa besar harga pangan bergerak saat kurs rupiah berubah?", _rq1, "respons", "Kurva respons per komoditas"),
       ("Apakah kepekaan itu berbeda antarprovinsi?", _rq2, "wilayah", "Uji perbedaan antarprovinsi"),
       ("Apakah dampak rupiah melemah sama dengan saat menguat?", _rq3, "respons", "Respons saat melemah dan menguat"),
       ("Apakah porsi impor dan letak provinsi menjelaskan kepekaan?", _rq4, "faktor", "Jalur impor dan karakteristik provinsi"),
       ("Apakah memantau kurs membantu memprediksi harga?", _rq5, "prediksi", "Evaluasi prediksi")]


def _hex_teaser(prof: pd.DataFrame, labels: dict) -> None:
    """Peta heksagon kecil untuk komoditas pertama yang perbedaan antarprovinsinya terdeteksi (pembuka halaman Cerita data,
    D-178). Tidak tampil bila artefak atau tata letak belum ada."""
    het, hexes = load("heterogeneity"), load_hex()
    if het is None or hexes is None:
        return
    rej = [c for c in labels if c in het_detected(het)]
    d = prof[(prof["level"] == "province") & (prof["driver"] == "e") & (prof["horizon"] == H)]
    if "shrunk" in d:
        d = d[d["shrunk"].fillna(False).astype(bool)]
    if not rej or d.empty:
        return
    c = rej[0]
    v = d[d["commodity"] == c].assign(province_id=lambda x: pd.to_numeric(x["unit"], errors="coerce"))
    v = v.dropna(subset=["province_id"]).astype({"province_id": int}).rename(columns={"estimate": "value"})
    zmax = float(max(v["value"].abs().max(), 0.1))
    st.plotly_chart(plots.hex_tile_map(v[["province_id", "value"]], hexes, f"{labels.get(c, c)}: kepekaan provinsi\ndibanding nasional",
                                       f"Satu heksagon = satu provinsi. Selisih perubahan harga {H} minggu per 1% pelemahan "
                                       "rupiah dari angka nasional.", zmax=zmax, legend="selisih dari nasional", height=340, text="code"), **STRETCH)


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
        period0 = CFG.params["period"]
        title = (f"Bila rupiah melemah {X}%, pola {str(period0['start'])[:4]}–{str(period0['freeze'])[:4]} menunjukkan harga "
                 f'beras naik paling banyak <span class="kg-hl">{amount}</span> dalam {H} minggu.')
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
            text += (f" Bila rupiah melemah {X}%, harga {names_list(small['commodity'], labels)} naik paling banyak 2% dalam "
                     f"{H} minggu.")
        if len(mid):
            text += f" Untuk {names_list(mid['commodity'], labels)}, paling banyak {X}%."
        if len(loose):
            text += (f" Untuk {names_list(loose['commodity'], labels)}, data belum cukup presisi. Batas atasnya mencapai "
                     f"{fmt_num(loose['ci_high'].max(), 0)}%, terlalu lebar untuk dipakai.")
        st.markdown(f'<p class="kg-lead">{text}</p>', unsafe_allow_html=True)
        note("Angka paling banyak adalah ujung atas rentang 95% perkiraan nasional, yaitu rentang yang memuat nilai "
             "sebenarnya dengan keyakinan 95%. Angka Rupiah dihitung dari median harga 34 provinsi selama 8 minggu sampai "
             "16 November 2026. Ini pola historis, bukan ramalan.")
        nav_link(PAGE["simulasi"], "Coba simulasi pelemahan rupiah", ":material/tune:")
        nav_link(PAGE["provinsi"], "Lihat label harga di provinsi Anda", ":material/location_on:")
        nav_link(PAGE["lini_masa"], "Lihat rupiah dan harga sejak 2018", ":material/timeline:")
    with right:
        if len(pt):
            d = pt.assign(width=pt["ci_high"] - pt["ci_low"]).sort_values("width", ascending=False)
            st.plotly_chart(plots.forest(
                d, ["komoditas"], f"Perubahan harga {H} minggu\nsetelah rupiah melemah {X}%",   # kolom sempit
                x_title="perubahan harga nasional (%)", x_range=(-10, 10),
                # baris baru eksplisit: kolom kanan hanya ± 270 px di layar 1024 px; catatan kausal di baris sendiri
                subtitle="Titik: perkiraan. Garis: rentang 95%.\nSegitiga: rentang lewat batas grafik.\n"), **STRETCH)

    st.markdown("## Jawaban atas lima pertanyaan penelitian")
    for question, answer, page, link in _answers(nat):
        st.markdown('<div class="kg-rule"></div>', unsafe_allow_html=True)
        q, a = st.columns([2, 5], gap="large")
        q.markdown(f'<p class="kg-rq">{question}</p>', unsafe_allow_html=True)
        with a:
            st.markdown(f'<p class="kg-ans">{answer}</p>', unsafe_allow_html=True)
            if page == PAGE["wilayah"]:
                _hex_teaser(prof, labels)
                nav_link(PAGE["cerita"], "Lihat peta heksagon semua komoditas", ":material/hexagon:")
            nav_link(page, link, ":material/arrow_forward:")
    st.markdown('<div class="kg-rule"></div>', unsafe_allow_html=True)

    st.markdown("## Cara kami menguji")
    el = load("eligibility")
    n_el = f"{int(el['eligible'].sum())} dari {len(el)}" if el is not None else "sebagian besar"
    st.markdown(
        f"Kami meringkas harga harian Bank Indonesia (PIHPS) menjadi harga mingguan. Sebanyak {n_el} seri provinsi dan "
        "komoditas cukup lengkap untuk dianalisis. Hipotesis dan aturan uji kami bekukan pada 20 November 2026, sebelum hasil "
        f"estimasi dilihat. Setiap hasil kami bandingkan dengan {CFG.params['inference']['placebo_R']} versi data yang urutan "
        "waktu kursnya digeser acak. Perbedaan yang tidak lebih besar dari hasil versi acak itu kami sebut kebetulan. Untuk "
        "hasil nol, kami juga menghitung efek terkecil yang akan tertangkap dengan peluang 80% bila efek itu ada.")
    nav_link(PAGE["data"], "Data, metode, dan daftar istilah", ":material/dataset:")
    note("KAGAMI masih prototipe riset. Kami belum menguji bersama TPID ambang kenaikan harga yang perlu ditindaklanjuti, "
         "sehingga aplikasi ini belum siap dipakai sebagai peringatan dini.")

footer("PIHPS dan JISDOR (Bank Indonesia), Pink Sheet (Bank Dunia)")
