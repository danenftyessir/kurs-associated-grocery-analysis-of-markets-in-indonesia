"""Halaman 6 -- Temuan Penelitian (WP-31/WP-33). Isi dari results/findings.md + ringkasan robustness."""

import streamlit as st

from common import STRETCH, footer, need, page_header

page_header("Temuan Penelitian", "Apa kesimpulannya?")

got = need("findings", "robustness")
if got:
    st.markdown(got["findings"])
    rb = got["robustness"]
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
