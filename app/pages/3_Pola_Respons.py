"""Halaman 3 -- Pola Respons (WP-31)."""

import streamlit as st

from common import CFG, STRETCH, footer, load, need, page_header
from kagami.viz import plots

page_header("Pola Respons", "Apakah ada kelompok provinsi dengan pola serupa?")

got = need("heterogeneity", "cluster_selection", "clusters", "coassign", "planted_recovery")
if got:
    st.subheader("Uji heterogenitas (vs plasebo)")
    st.dataframe(got["heterogeneity"], hide_index=True, **STRETCH)

    sel = got["cluster_selection"]
    st.subheader("Pemilihan k terhadap plasebo")
    st.dataframe(sel, hide_index=True, **STRETCH)
    if not sel["accepted"].any():
        st.warning("k = 1: tidak ada struktur regional yang terdeteksi. Lihat batas deteksi di bawah.")
    else:
        cl = got["clusters"]
        st.plotly_chart(plots.cluster_sizes(cl), **STRETCH)
        if cl.loc[cl["method"] == "ward", "weak"].any():
            st.warning("Ada klaster dengan stabilitas rendah (pola lemah): jangan ditafsirkan sebagai tipe kepekaan.")
        names = CFG.regions.set_index("province_id")["province"]
        ward = cl[cl["method"] == "ward"].assign(provinsi=lambda d: d["province_id"].map(names))
        st.dataframe(ward[["cluster", "provinsi", "jaccard", "weak"]].sort_values(["cluster", "provinsi"]),
                     hide_index=True, **STRETCH)
        st.plotly_chart(plots.coassign_heatmap(got["coassign"]), **STRETCH)
        pc = load("partition_compare")
        if pc is not None:
            st.markdown("**Kesesuaian klaster dengan pembagian lain (ARI; 0 = tak berhubungan, 1 = identik)**")
            st.dataframe(pc, hide_index=True, **STRETCH)

    st.subheader("Batas deteksi (uji struktur tertanam)")
    st.plotly_chart(plots.recovery_curve(got["planted_recovery"]), **STRETCH)

footer("Turunan PIHPS (BI)", "fitur respons terstandardisasi", "2018-2026")
