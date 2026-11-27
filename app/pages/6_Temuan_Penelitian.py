"""Halaman 6 -- Laporan lengkap (lampiran teknis sejak D-171; WP-31/WP-33). Isi = results/findings.md apa adanya, dipecah
per bagian `## ` ke dalam tab (D-170) agar ringkasan terbaca lebih dulu; ditambah grafik ketahanan di tab ketahanan."""

import re

import streamlit as st

from common import DRIVER_LABELS, PAGE, STRETCH, commodity_labels, footer, nav_link, need, note, page_header, picker
from kagami.viz import plots

page_header("Laporan temuan lengkap",
            "Teks lengkap temuan yang ikut dalam paket juri, dengan angka, tingkat bukti, dan keterbatasannya. Dokumen ini "
            "memakai notasi statistik; artinya ada di Daftar istilah.")
nav_link(PAGE["data"], "Daftar istilah di halaman Data & metode", ":material/menu_book:")

# (judul tab, awalan judul bagian findings.md yang masuk ke tab itu)
GROUPS = [("Ringkasan", ("Ringkasan", "Makna bagi pengguna")),
          ("Per pertanyaan", ("RQ", "Eksplorasi")),
          ("Ketahanan & batas", ("Kalibrasi", "Robustness", "Validasi prospektif", "Keterbatasan")),
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
            note("Tier 1 adalah cek wajib yang kami daftarkan sebelum analisis. Tier 2 adalah cek tambahan: varian harga, "
                 "cara agregasi, dan sumber harga lain. Dekomposisi kurs memisahkan komponen dolar global dari komponen "
                 "khusus rupiah.")
    if {"check_id", "tier", "estimate", "ci_low", "ci_high", "baseline_estimate"} <= set(rb.columns):
        ok = rb[["ci_low", "ci_high", "baseline_estimate"]].notna().all(axis=1)
        d = rb[ok].assign(in_ci=lambda x: ((x["baseline_estimate"] >= x["ci_low"])
                                           & (x["baseline_estimate"] <= x["ci_high"])).astype(float),
                          excl0=lambda x: ((x["ci_low"] > 0) | (x["ci_high"] < 0)).astype(float))
        if len(d):
            s = d.groupby(["tier", "check_id"], as_index=False).agg(
                sel=("in_ci", "size"), baseline_di_dalam_interval=("in_ci", "sum"), interval_tanpa_nol=("excl0", "sum"))
            s["porsi"] = (s["baseline_di_dalam_interval"] / s["sel"]).round(3)
            with st.expander("Ringkasan per cek ketahanan dan validasi"):
                st.dataframe(s, hide_index=True, **STRETCH)
                st.caption("Porsi = sel yang estimasi utamanya berada di dalam interval cek. V4 (LP vs event study) lemah sebagai "
                           "validasi karena hampir semua interval event memuat nol.")
    with st.expander("Tabel ketahanan lengkap"):
        st.dataframe(rb, hide_index=True, **STRETCH)


fd = need("findings")
if fd:
    lead, rest, secs = split_findings(fd["findings"])
    if not secs:
        st.markdown(fd["findings"])
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
