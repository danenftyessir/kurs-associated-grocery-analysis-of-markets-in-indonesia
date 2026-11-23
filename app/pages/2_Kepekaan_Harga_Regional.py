"""Halaman 2 -- Kepekaan Harga Regional (WP-31)."""

import streamlit as st

from common import STRETCH, commodity_labels, footer, load, need, not_detected_badge, page_header, with_status
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
    driver = st.radio("Penggerak", sorted(prof["driver"].unique()), horizontal=True,
                      help="e = IDR/USD, w = harga dunia padanan dalam rupiah, e_pos/e_neg = depresiasi/apresiasi, "
                           "PT = rasio pass-through β/γ")
    d = prof[(prof["commodity"] == com) & (prof["level"] == level) & (prof["unit"].astype(str) == unit)
             & (prof["driver"] == driver)].sort_values("horizon")
    if d.empty:
        st.warning("Tidak ada estimasi untuk kombinasi ini.")
    else:
        st.plotly_chart(plots.response_curve(prof, com, level, unit, driver), **STRETCH)
        h8 = d[d["horizon"] == 8]
        if len(h8):
            st.markdown(f"**Status h = 8:** {not_detected_badge(h8['ci_low'].iloc[0], h8['ci_high'].iloc[0])}")
        st.caption("Interval resmi (praregistrasi): yang lebih lebar dari ±1,96·SE cluster minggu dan persentil bootstrap "
                   "blok 13 minggu. Bootstrap ini menarik estimasi ke nol pada horizon panjang, sehingga interval resmi "
                   "cenderung terlalu lebar (konservatif).")

    cal = load("national_calibrated")
    if cal is not None and not cal.empty:
        st.subheader("Inferensi nasional terkalibrasi plasebo (analisis tambahan)")
        c = cal[cal["commodity"] == com]
        if c.empty:
            st.info("Tidak ada baris terkalibrasi untuk komoditas ini.")
        else:
            cols = [x for x in ("driver", "horizon", "estimate", "ci_prereg_low", "ci_prereg_high", "ci_low", "ci_high",
                                "p_value", "q_fdr", "boot_ratio") if x in c]
            st.dataframe(with_status(c[cols]), hide_index=True, **STRETCH)
        st.caption("Interval ±crit·SE dengan crit dari 499 plasebo geser-melingkar (199 untuk komoditas non-fokus); "
                   "p = max(p plasebo, p normal); q = koreksi BH atas 48 sel. ci_prereg_* = interval resmi. "
                   "boot_ratio < 1 = rerata replikasi bootstrap lebih dekat ke nol daripada estimasi.")

    asym = load("asymmetry")
    if asym is not None and not asym.empty:
        st.subheader("Depresiasi vs apresiasi (H2)")
        a = asym[asym["commodity"] == com]
        cols = [x for x in ("horizon", "beta_pos", "beta_neg", "estimate", "ci_low", "ci_high", "p_value", "p_placebo",
                            "confirmatory", "reject") if x in a]
        st.dataframe(with_status(a[cols]), hide_index=True, **STRETCH)
        st.caption("estimate = β⁺ − β⁻ nasional. Uji konfirmatori (Wald, h = 8) hanya untuk komoditas yang lolos gerbang "
                   "G-power (MDE asimetri PT(8) ≤ 0,5: beras dan daging sapi); lainnya deskriptif.")

    feats = load("response_features")
    if feats is not None and not feats.empty:
        st.subheader("Peta kepekaan")
        metric = st.radio("Ukuran", ["R4", "R8", "R12", "PT8"], index=1, horizontal=True)
        lv = st.selectbox("Peta level", [x for x in ("region", "province") if x in set(feats["level"])] or ["national"])
        st.plotly_chart(plots.sensitivity_heatmap(feats, lv, metric), **STRETCH)
        rank = feats[(feats["level"] == "province") & (feats["commodity"] == com)].sort_values("R8", ascending=False)
        if len(rank):
            st.markdown("**Peringkat provinsi (R8, respons nasional + deviasi tersusut)**")
            st.dataframe(rank[["unit", "R4", "R8", "R12", "t_half"]], hide_index=True, **STRETCH)
            if rank["R8"].nunique() == 1:
                st.info("Varians antarprovinsi τ² = 0 untuk komoditas ini: semua provinsi disusutkan ke respons rerata.")
            st.caption("Respons yang interval-nya memuat nol adalah batas atas kepekaan, bukan bukti nol.")
    st.subheader("Event study per episode depresiasi")
    ev = got["events"]
    st.dataframe(ev[ev["commodity"] == com], hide_index=True, **STRETCH)
    st.caption("dlog_price dibandingkan dengan 499 jendela plasebo tanpa episode (placebo_lo/hi = persentil 2,5/97,5).")

footer("PIHPS (BI), JISDOR (BI), Pink Sheet (Bank Dunia)", "Δ log harga per 1 log penggerak", "2018-2026")
