"""Halaman 4 -- Eksposur & Nilai Prediktif (WP-31)."""

import streamlit as st

from common import footer, need, page_header
from kagami.viz import plots

page_header("Eksposur & Nilai Prediktif",
            "Lewat jalur apa komoditas ini terpapar, dan apakah kurs membantu memprediksi harganya?")

got = need("exposure", "response_features", "assoc", "forecast_eval", "ablation")
if got:
    st.subheader("Tiga jalur eksposur vs respons nasional")
    nat = got["response_features"].query("level == 'national'")[["commodity", "PT8", "W8"]]
    st.dataframe(got["exposure"].merge(nat, on="commodity", how="left"), hide_index=True, use_container_width=True)
    st.caption("N = 10 komoditas: kesimpulan berlaku 'di antara 10 komoditas yang diamati'.")

    st.subheader("Asosiasi (Task 3)")
    assoc = got["assoc"]
    label = [c for c in ("level", "feature", "outcome", "commodity") if c in assoc]
    st.plotly_chart(plots.forest(assoc, label, "Koefisien asosiasi"), use_container_width=True)
    st.dataframe(assoc, hide_index=True, use_container_width=True)

    st.subheader("Evaluasi bersyarat rolling-origin (Task 4)")
    fe = got["forecast_eval"]
    for subset in ("all", "large_move"):
        if (fe["subset"] == subset).any():
            st.plotly_chart(plots.forecast_ratios(fe, subset), use_container_width=True)
    if "h5_p_holm" in fe:
        st.markdown("**H5 (grup fokus per jalur eksposur, h = 8, koreksi Holm)**")
        st.dataframe(fe[fe["h5_p_holm"].notna()], hide_index=True, use_container_width=True)
    with st.expander("Tabel lengkap evaluasi dan ablation"):
        st.dataframe(fe, hide_index=True, use_container_width=True)
        st.dataframe(got["ablation"], hide_index=True, use_container_width=True)
    st.caption("Evaluasi bersyarat atas pola historis (pseudo-real-time), bukan sistem peramalan.")

footer("Turunan PIHPS, FAOSTAT, BPS, Pink Sheet", "rasio / MAE log", "2021-2026 (Task 4)")
