"""Halaman 2 -- Kepekaan Harga Regional (WP-31)."""

import streamlit as st

from common import commodity_labels, footer, need, not_detected_badge, page_header
from kagami.viz import plots

page_header("Kepekaan Harga Regional", "Komoditas mana di wilayah saya yang historisnya paling peka?")

got = need("profiles", "events")
if got:
    prof = got["profiles"]
    labels = commodity_labels()
    c1, c2, c3 = st.columns(3)
    com = c1.selectbox("Komoditas", list(labels), format_func=labels.get)
    level = c2.selectbox("Level", sorted(prof["level"].unique()))
    unit = c3.selectbox("Unit", sorted(prof.loc[prof["level"] == level, "unit"].astype(str).unique()))
    driver = st.radio("Penggerak", sorted(prof["driver"].unique()), horizontal=True)
    d = prof[(prof["commodity"] == com) & (prof["level"] == level) & (prof["unit"].astype(str) == unit)
             & (prof["driver"] == driver)].sort_values("horizon")
    if d.empty:
        st.warning("Tidak ada estimasi untuk kombinasi ini.")
    else:
        st.plotly_chart(plots.response_curve(prof, com, level, unit, driver), use_container_width=True)
        h8 = d[d["horizon"] == 8]
        if len(h8):
            st.markdown(f"**Status h = 8:** {not_detected_badge(h8['ci_low'].iloc[0], h8['ci_high'].iloc[0])}")
    st.subheader("Event study per episode depresiasi")
    ev = got["events"]
    st.dataframe(ev[ev["commodity"] == com], hide_index=True, use_container_width=True)

footer("PIHPS (BI), JISDOR (BI), Pink Sheet (Bank Dunia)", "log poin", "2018-2026")
