"""Halaman 6 -- Temuan Penelitian (WP-31/WP-33). Isi dari results/findings.md + ringkasan robustness."""

import streamlit as st

from common import DRIVER_LABELS, STRETCH, commodity_labels, footer, need, page_header, picker
from kagami.viz import plots

page_header("Temuan Penelitian", "Apa kesimpulannya?")

fd = need("findings")
if fd:
    st.markdown(fd["findings"])
# Robustness terpisah: temuan tetap tampil walau artefak robustness belum ada (deploy sebagian).
got = need("robustness")
if got:
    rb = got["robustness"]
    st.subheader("Apakah temuan bertahan di setiap cek robustness?")
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
            st.caption("Tier 1 = cek wajib praregistrasi; Tier 2 = cek opsional (varian, agregasi, outcome alternatif). "
                       "Dekomposisi kurs memisahkan komponen dolar global (e_global) dan spesifik rupiah (e_idr).")
    st.subheader("Ringkasan robustness & validasi")
    if {"check_id", "tier", "estimate", "ci_low", "ci_high", "baseline_estimate"} <= set(rb.columns):
        ok = rb[["ci_low", "ci_high", "baseline_estimate"]].notna().all(axis=1)
        d = rb[ok].assign(in_ci=lambda x: ((x["baseline_estimate"] >= x["ci_low"])
                                           & (x["baseline_estimate"] <= x["ci_high"])).astype(float),
                          excl0=lambda x: ((x["ci_low"] > 0) | (x["ci_high"] < 0)).astype(float))
        if len(d):
            s = d.groupby(["tier", "check_id"], as_index=False).agg(
                n_sel=("in_ci", "size"), baseline_di_dalam_interval=("in_ci", "sum"), interval_tanpa_nol=("excl0", "sum"))
            s["porsi"] = s["baseline_di_dalam_interval"] / s["n_sel"]
            st.dataframe(s, hide_index=True, **STRETCH)
        st.caption("Tier 1: estimasi baseline (LP utama) berada di dalam interval cek. V4: implikasi LP di dalam interval "
                   "event study; karena hampir semua interval event memuat nol (kolom interval_tanpa_nol), kecocokan ini "
                   "lemah sebagai validasi. V2 forecast (rasio MAE) tidak punya interval dan dilihat di tabel lengkap.")
    with st.expander("Tabel robustness lengkap"):
        st.dataframe(rb, hide_index=True, **STRETCH)

footer("KAGAMI (turunan PIHPS, JISDOR, Pink Sheet, FRED, FAOSTAT, BPS, Bapanas)", "lihat tiap temuan", "2018-2026")
