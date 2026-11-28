"""Halaman 6 -- Laporan lengkap (lampiran teknis sejak D-171; WP-31/WP-33). Isi = results/findings.md apa adanya, dipecah
per bagian `## ` ke dalam tab (D-170) agar ringkasan terbaca lebih dulu; ditambah grafik ketahanan di tab ketahanan."""

import re

import streamlit as st

import pandas as pd

from common import (DRIVER_LABELS, PAGE, STRETCH, commodity_labels, footer, math_text, nav_link, need, note, page_header,
                    picker, plain_names, readable, show_table)
from kagami.viz import plots
from kagami.viz.style import CHECK_LABELS

page_header("Laporan temuan lengkap",
            "Teks lengkap temuan untuk pembaca teknis seperti juri dan peneliti, dengan angka, tingkat bukti, dan "
            "keterbatasannya. Jawaban untuk pembaca umum ada di halaman Hasil penelitian.")
with st.expander("Cara membaca angka di laporan ini"):
    st.markdown("Respons harga ditulis $\\beta_e(h)$ untuk kurs rupiah dan $\\omega(h)$ untuk harga dunia dalam rupiah, pada "
                "minggu ke-$h$. Nilai $-1{,}67$ berarti harga turun sekitar 1,67% untuk setiap 1% pelemahan rupiah. Penerusan "
                "kurs membagi respons harga dengan respons kurs terhadap dirinya sendiri:")
    st.latex(r"PT(h) = \frac{\beta_e(h)}{\gamma(h)}")
    st.markdown("Angka dalam kurung seperti (0,02..0,28) adalah rentang 95%. Rentang yang memuat nol berarti respons belum "
                "bisa dibedakan dari nol. $q$ adalah nilai $p$ yang dikoreksi untuk banyak uji sekaligus. Laporan ini "
                "memisahkan tiga tingkat bukti: uji yang didaftarkan sebelum analisis, analisis kepekaan, dan eksplorasi.")
nav_link(PAGE["data"], "Rumus model dan daftar istilah di halaman Data & metode", ":material/menu_book:")

TIERS = {"1": "Tier 1", "2": "Tier 2", "V": "Validasi"}
CHECKS = {**CHECK_LABELS, "V4_lp_vs_event_study": "proyeksi lokal vs studi peristiwa",
          "V2_case_study_events": "studi kasus 2026 (episode)", "V2_case_study_forecast": "studi kasus 2026 (prediksi)",
          "alternative_exposure_remoteness": "definisi eksposur & keterpencilan alternatif"}

# (judul tab, awalan judul bagian findings.md yang masuk ke tab itu)
GROUPS = [("Ringkasan", ("Ringkasan", "Makna bagi pengguna")),
          ("Per pertanyaan", ("Pertanyaan", "RQ", "Eksplorasi")),
          ("Ketahanan & batas", ("Kalibrasi", "Ketahanan", "Robustness", "Validasi prospektif", "Keterbatasan")),
          ("Data & cara membaca", ("Dataset turunan", "Sumber angka")),
          ("Eksplorasi prediksi (lampiran)", ("Lampiran",))]


def split_findings(md: str) -> tuple[str, str, dict[str, str]]:
    """(paragraf pembuka, sisa pembuka, {judul bagian: isi}) dari findings.md; judul `# ` dibuang (sudah ada judul halaman)."""
    parts = re.split(r"(?m)^## ", md)
    pre = re.sub(r"(?m)\A# .*\n", "", parts[0]).strip()
    lead, _, rest = pre.partition("\n\n")
    secs = {}
    for p in parts[1:]:
        title, _, body = p.partition("\n")
        secs[title.strip()] = body.strip()
    return lead, rest, secs


def robustness_section() -> None:
    got = need("robustness")
    if not got:
        return
    rb = got["robustness"]
    st.markdown("### Ketahanan temuan terhadap pilihan analisis")
    labels = commodity_labels()
    coms = [c for c in labels if c in set(rb["commodity"])]
    if coms and {"driver", "estimate", "ci_low", "ci_high"} <= set(rb.columns):
        c1, c2, c3 = st.columns(3)
        com = picker("Komoditas", coms, "com", format_func=labels.get, default="daging_ayam", container=c1)
        drvs = [d for d in ("e", "w") if d in set(rb.loc[rb["commodity"] == com, "driver"])]
        if drvs:
            drv = picker("Penggerak", drvs, "driver", format_func=DRIVER_LABELS.get, container=c2)
            hs = sorted(int(h) for h in rb.loc[(rb["commodity"] == com) & (rb["driver"] == drv), "horizon"].dropna().unique())
            h = picker("Horizon (minggu)", hs, "h", default=8, container=c3)
            st.plotly_chart(plots.robustness_forest(rb, com, drv, h, name=labels.get(com, com)), **STRETCH)
            note("Tier 1 adalah cek wajib yang kami daftarkan sebelum analisis. Tier 2 adalah cek tambahan dengan varian "
                 "harga, cara agregasi, dan sumber harga lain. Dekomposisi kurs memisahkan komponen dolar global dari "
                 "komponen khusus rupiah.")
    if {"check_id", "tier", "estimate", "ci_low", "ci_high", "baseline_estimate"} <= set(rb.columns):
        ok = rb[["ci_low", "ci_high", "baseline_estimate"]].notna().all(axis=1)
        d = rb[ok].assign(in_ci=lambda x: ((x["baseline_estimate"] >= x["ci_low"])
                                           & (x["baseline_estimate"] <= x["ci_high"])).astype(float),
                          excl0=lambda x: ((x["ci_low"] > 0) | (x["ci_high"] < 0)).astype(float))
        if len(d):
            s = d.groupby(["tier", "check_id"], as_index=False).agg(
                sel=("in_ci", "size"), baseline_di_dalam_interval=("in_ci", "sum"), interval_tanpa_nol=("excl0", "sum"))
            s["porsi"] = (s["baseline_di_dalam_interval"] / s["sel"]).round(3)
            s = pd.DataFrame({"Kelompok": s["tier"].astype(str).map(lambda t: TIERS.get(t, t)),
                              "Cek": s["check_id"].map(lambda c: CHECKS.get(c, c)), "Jumlah sel": s["sel"],
                              "Estimasi utama di dalam rentang cek": s["baseline_di_dalam_interval"].astype(int),
                              "Rentang cek tanpa nol": s["interval_tanpa_nol"].astype(int), "Porsi": s["porsi"]})
            with st.expander("Ringkasan per cek ketahanan dan validasi"):
                show_table(s)
                st.caption("Porsi adalah bagian sel yang estimasi utamanya berada di dalam rentang cek. Validasi pembanding "
                           "proyeksi lokal dengan studi peristiwa lemah karena hampir semua rentang studi peristiwa memuat nol.")
    with st.expander("Tabel ketahanan lengkap"):
        show_table(rb)


fd = need("findings")
if fd:
    # tampilan: tanpa kode internal (D-172), notasi sebagai rumus LaTeX & nama berkas sebagai nama pembaca (D-173);
    # berkas findings.md tidak berubah
    text = math_text(plain_names(readable(fd["findings"])))
    lead, rest, secs = split_findings(text)
    if not secs:
        st.markdown(text)
    else:
        st.markdown(lead)
        tabs = st.tabs([g for g, _ in GROUPS])
        used = set()
        for tab, (name, prefixes) in zip(tabs, GROUPS):
            with tab:
                if name == "Data & cara membaca" and rest:
                    st.markdown(rest)
                for title, body in secs.items():
                    if title.startswith(prefixes) and title not in used:
                        used.add(title)
                        st.markdown(f"## {title}\n\n{body}")
                if name == "Ketahanan & batas":
                    robustness_section()
        other = [t for t in secs if t not in used]
        for title in other:                       # bagian baru di findings.md yang belum dipetakan tetap tampil
            st.markdown(f"## {title}\n\n{secs[title]}")
else:
    robustness_section()

footer("data turunan dari PIHPS, JISDOR, Pink Sheet, FRED, FAOSTAT, BPS, dan Bapanas")
