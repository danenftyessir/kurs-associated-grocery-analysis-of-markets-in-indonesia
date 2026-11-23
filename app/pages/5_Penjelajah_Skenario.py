"""Halaman 5 -- Penjelajah Skenario Bersyarat (WP-31). PT(h)·x; pita hanya bila interval PT ada (nasional); bukan ramalan."""

import streamlit as st

from common import (CFG, LEVEL_LABELS, STRETCH, commodity_labels, fmt_interval, fmt_num, footer, need,
                    not_detected_badge, page_header, picker, unit_names)
from kagami.viz import plots

page_header("Penjelajah Skenario Bersyarat",
            "Bila rupiah melemah x% dalam h minggu, berapa perubahan harga yang konsisten dengan pola historis?")

got = need("profiles", "episodes")
if got:
    prof = got["profiles"].query("driver == 'PT'")
    labels, names = commodity_labels(), unit_names()
    shocks = CFG.params["scenario"]["shocks_pct"]
    c1, c2, c3 = st.columns(3)
    com = picker("Komoditas", list(labels), "com", format_func=labels.get, container=c1)
    levels = [lv for lv in ("national", "region") if lv in set(prof.loc[prof["commodity"] == com, "level"])]
    if not levels:
        st.warning("PT(h) tidak tersedia untuk komoditas ini.")
        st.stop()
    level = picker("Tingkat", levels, "level", format_func=LEVEL_LABELS.get, container=c2)
    units = sorted(prof.loc[(prof["commodity"] == com) & (prof["level"] == level), "unit"].astype(str).unique())
    unit = picker("Unit", units, "unit", format_func=lambda u: names.get(u, u), container=c3)
    c4, c5 = st.columns(2)
    x = c4.select_slider("Pelemahan rupiah (%)", options=shocks, value=shocks[len(shocks) // 2])
    h = picker("Horizon ringkasan (minggu)", CFG.params["lp"]["key_horizons"], "h", default=8, container=c5)

    pt = prof[(prof["commodity"] == com) & (prof["level"] == level) & (prof["unit"].astype(str) == unit)]
    row = pt[pt["horizon"] == h]
    if row.empty:
        st.warning("PT(h) tidak tersedia untuk pilihan ini.")
    else:
        r = row.iloc[0]
        status = not_detected_badge(r["ci_low"], r["ci_high"])
        st.metric(f"Perubahan harga konsisten dengan pola historis (h = {h})", fmt_num(r["estimate"] * x, 2, True, True))
        st.markdown(f"Interval 95%: **{fmt_interval(r['ci_low'] * x, r['ci_high'] * x, 2, pct=True)}** · "
                    f"status: **{status}**")
        if status == "interval tidak tersedia":
            st.warning("Interval PT hanya tersedia di tingkat nasional (persentil bootstrap rasio). Angka wilayah ini adalah "
                       "titik estimasi tanpa ukuran ketidakpastian: jangan dibaca sebagai perubahan yang pasti.")
        elif status == "tidak terdeteksi":
            st.info("Interval memuat nol: angka di atas adalah batas kepekaan yang konsisten dengan data, bukan prediksi arah.")
        max_hist = 100 * got["episodes"]["cum_dlog_e"].max()
        if x > max_hist:
            st.error(f"Ekstrapolasi: x = {x}% melebihi depresiasi kumulatif historis terbesar ({fmt_num(max_hist, 1)}%).")
        st.plotly_chart(plots.scenario_paths(pt, shocks, x), **STRETCH)
        st.caption("Interval PT dari persentil bootstrap blok; bootstrap ini menarik estimasi ke nol pada horizon panjang, "
                   "sehingga interval cenderung lebar (konservatif).")
    st.caption("Skenario bersyarat berdasarkan pola historis, bukan ramalan.")

footer("Turunan PIHPS (BI), JISDOR (BI)", "% perubahan harga", "2018-2026")
