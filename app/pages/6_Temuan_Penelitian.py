"""Halaman 6 -- Temuan Penelitian (WP-31/WP-33). Isi dari results/findings.md (ditulis setelah G8)."""

import streamlit as st

from common import footer, need, page_header

page_header("Temuan Penelitian", "Apa kesimpulannya?")

got = need("findings", "robustness")
if got:
    st.markdown(got["findings"])
    with st.expander("Robustness & validasi"):
        st.dataframe(got["robustness"], hide_index=True, use_container_width=True)

footer("KAGAMI", "-", "2018-2026")
