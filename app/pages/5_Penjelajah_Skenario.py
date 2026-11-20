"""Halaman 5 -- Penjelajah Skenario Bersyarat (WP-31). PT(h)·x dengan interval; bukan ramalan."""

import streamlit as st

from common import CFG, commodity_labels, footer, need, page_header

page_header("Penjelajah Skenario Bersyarat",
            "Bila rupiah melemah x% dalam h minggu, berapa perubahan harga yang konsisten dengan pola historis?")

got = need("profiles", "episodes")
if got:
    prof = got["profiles"].query("driver == 'PT'")
    labels = commodity_labels()
    c1, c2, c3, c4 = st.columns(4)
    com = c1.selectbox("Komoditas", list(labels), format_func=labels.get)
    unit = c2.selectbox("Unit", sorted(prof.loc[prof["commodity"] == com, "unit"].astype(str).unique()))
    x = c3.select_slider("Pelemahan rupiah (%)", options=CFG.params["scenario"]["shocks_pct"])
    h = c4.selectbox("Horizon (minggu)", CFG.params["lp"]["key_horizons"], index=1)
    row = prof[(prof["commodity"] == com) & (prof["unit"].astype(str) == unit) & (prof["horizon"] == h)]
    if row.empty:
        st.warning("PT(h) tidak tersedia untuk pilihan ini.")
    else:
        r = row.iloc[0]
        st.metric(f"Perubahan harga konsisten dengan pola historis (h = {h})",
                  f"{r['estimate'] * x:+.2f}%", help=f"interval: {r['ci_low'] * x:+.2f}% s.d. {r['ci_high'] * x:+.2f}%")
        max_hist = 100 * got["episodes"]["cum_dlog_e"].max()
        if x > max_hist:
            st.error(f"Ekstrapolasi: x = {x}% melebihi depresiasi kumulatif historis terbesar ({max_hist:.1f}%).")
    st.caption("Skenario bersyarat berdasarkan pola historis, bukan ramalan.")

footer("Turunan PIHPS (BI), JISDOR (BI)", "% perubahan harga", "2018-2026")
