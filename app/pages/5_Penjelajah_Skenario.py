"""Halaman 5 -- Simulasi pelemahan rupiah (WP-31; D-169, D-171). Perubahan harga = exp(PT(h)·ln(1 + x/100)) − 1 (sama
dengan tabel batas Rupiah findings, `viz.plots.scenario_change`); dalam Rupiah memakai harga acuan nasional findings. Pita
hanya bila interval PT ada (nasional); skenario bersyarat, bukan ramalan."""

import streamlit as st

from common import (CFG, STRETCH, area_level, area_options, commodity_labels, fmt_interval, fmt_num, fmt_rp, footer,
                    need, not_detected_badge, note, page_header, picker, reference_prices, unit_names)
from kagami.viz import plots

page_header("Simulasi pelemahan rupiah",
            "Pilih komoditas dan besar pelemahan rupiah. Angka yang muncul adalah rentang perubahan harga yang sejalan "
            "dengan pola 2018–2026.")

got = need("profiles", "episodes")
if got:
    prof = got["profiles"].query("driver == 'PT'")
    labels, names, prices = commodity_labels(), unit_names(), reference_prices()
    shocks = CFG.params["scenario"]["shocks_pct"]
    c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.2, 1])
    com = picker("Komoditas", list(labels), "com", format_func=labels.get, container=c1)
    areas = area_options(prof, com)
    if not areas:
        st.warning("Belum ada estimasi penerusan kurs untuk komoditas ini.")
        st.stop()
    area = picker("Wilayah", areas, "area", format_func=lambda u: names.get(u, u), default="ALL", container=c2)
    level = area_level(area)
    x = c3.select_slider("Rupiah melemah", options=shocks, value=shocks[len(shocks) // 2], format_func=lambda v: f"{v}%")
    h = picker("Minggu ke-", CFG.params["lp"]["key_horizons"], "h", default=8, container=c4)

    name, where = labels.get(com, com), names.get(area, area)
    pt = prof[(prof["commodity"] == com) & (prof["level"] == level) & (prof["unit"].astype(str) == area)]
    row = pt[pt["horizon"] == h]
    if row.empty:
        st.warning("Belum ada estimasi untuk pilihan ini.")
    else:
        r = row.iloc[0]
        status = not_detected_badge(r["ci_low"], r["ci_high"])
        est, lo, hi = (plots.scenario_change(r[c], x) for c in ("estimate", "ci_low", "ci_high"))
        st.markdown(f'<p class="kg-result">Rupiah melemah {x}%: harga {name.lower()} '
                    f'{"nasional" if level == "national" else "di " + where} dalam {h} minggu berubah '
                    f'<span class="kg-hl">{fmt_num(est, 2, True, True)}</span></p>', unsafe_allow_html=True)
        if status == "interval tidak tersedia":
            st.markdown("Untuk tingkat wilayah kami belum punya rentang 95%, jadi angka ini hanya perkiraan titik.")
        else:
            txt = f"Rentang 95%: {fmt_interval(lo, hi, 2, pct=True)}"
            price, per = prices.get(com, (None, None))
            if price and level == "national":
                txt += (f", atau {fmt_rp(price * lo / 100)} s.d. {fmt_rp(price * hi / 100)} per {per} dari harga acuan "
                        f"{fmt_rp(price, sign=False)}")
            txt += "."
            if status == "tidak terdeteksi":
                txt += " Rentang ini memuat nol, jadi arah perubahannya belum bisa ditentukan dari data."
            st.markdown(txt)
        max_hist = 100 * got["episodes"]["cum_dlog_e"].max()
        if x > max_hist:
            st.warning(f"Pelemahan {x}% lebih besar dari episode terbesar dalam data ({fmt_num(max_hist, 1)}%). Hasil ini "
                       "di luar pengalaman historis.")
        st.plotly_chart(plots.scenario_paths(pt, shocks, x, title=f"{name}: perubahan harga setelah rupiah melemah"),
                        **STRETCH)
        with st.expander("Cara menghitung"):
            st.latex(r"\Delta\text{harga}\ (\%) = 100\left[\exp\big(PT(h)\cdot\ln(1 + x/100)\big) - 1\right]")
            st.markdown("Di sini $x$ adalah besar pelemahan rupiah dalam persen, dan $PT(h)$ penerusan kurs pada minggu ke-$h$, "
                        "yaitu respons harga dibagi respons kurs terhadap dirinya sendiri. Rumus ini sama dengan tabel batas "
                        "Rupiah di laporan lengkap. Rentang $PT$ berasal dari bootstrap blok 13 minggu, yang menarik estimasi "
                        "ke arah nol pada horizon panjang, sehingga rentangnya cenderung lebar.")
            note("Angka Rupiah dihitung dari median harga 34 provinsi, memakai rata-rata harga teramati 8 minggu sampai "
                 "16 November 2026. Angka Rupiah hanya tersedia untuk tingkat nasional.")

footer("PIHPS dan JISDOR (Bank Indonesia)")
