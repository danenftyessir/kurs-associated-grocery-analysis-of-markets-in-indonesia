"""Halaman 2 -- Kepekaan Harga Regional (WP-31)."""

import streamlit as st

from common import commodity_labels, footer, load, need, not_detected_badge, page_header
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
    feats = load("response_features")
    if feats is not None and not feats.empty:
        st.subheader("Peta kepekaan")
        metric = st.radio("Ukuran", ["R4", "R8", "R12", "PT8"], index=1, horizontal=True)
        lv = st.selectbox("Peta level", [x for x in ("region", "province") if x in set(feats["level"])] or ["national"])
        st.plotly_chart(plots.sensitivity_heatmap(feats, lv, metric), use_container_width=True)
        rank = feats[(feats["level"] == "province") & (feats["commodity"] == com)].sort_values("R8", ascending=False)
        if len(rank):
            st.markdown("**Peringkat provinsi (R8, respons nasional + deviasi tersusut)**")
            st.dataframe(rank[["unit", "R4", "R8", "R12", "t_half"]], hide_index=True, use_container_width=True)
            st.caption("Respons yang interval-nya memuat nol adalah batas atas kepekaan, bukan bukti nol.")
    st.subheader("Event study per episode depresiasi")
    ev = got["events"]
    st.dataframe(ev[ev["commodity"] == com], hide_index=True, use_container_width=True)

footer("PIHPS (BI), JISDOR (BI), Pink Sheet (Bank Dunia)", "log poin", "2018-2026")
