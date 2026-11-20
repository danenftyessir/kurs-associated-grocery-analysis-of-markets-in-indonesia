"""Halaman 4 -- Eksposur & Nilai Prediktif (WP-31)."""

import streamlit as st

from common import footer, need, page_header

page_header("Eksposur & Nilai Prediktif",
            "Lewat jalur apa komoditas ini terpapar, dan apakah kurs membantu memprediksi harganya?")

got = need("exposure", "response_features", "assoc", "forecast_eval", "ablation")
if got:
    st.subheader("Tiga jalur eksposur vs respons nasional")
    nat = got["response_features"].query("level == 'national'")[["commodity", "PT8", "W8"]]
    st.dataframe(got["exposure"].merge(nat, on="commodity", how="left"), hide_index=True, use_container_width=True)
    st.caption("N = 10 komoditas: kesimpulan berlaku 'di antara 10 komoditas yang diamati'.")

    st.subheader("Asosiasi (Task 3)")
    st.dataframe(got["assoc"], hide_index=True, use_container_width=True)

    st.subheader("Evaluasi bersyarat rolling-origin (Task 4)")
    st.dataframe(got["forecast_eval"], hide_index=True, use_container_width=True)
    st.dataframe(got["ablation"], hide_index=True, use_container_width=True)
    st.caption("Evaluasi bersyarat atas pola historis (pseudo-real-time), bukan sistem peramalan.")

footer("Turunan PIHPS, FAOSTAT, BPS, Pink Sheet", "rasio / MAE log", "2021-2026 (Task 4)")
