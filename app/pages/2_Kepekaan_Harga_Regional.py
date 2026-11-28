"""Halaman 2 -- Respons harga terhadap kurs (WP-31; D-171). Kalimat jawaban → satu kurva respons (nasional atau 7 wilayah)
dengan kalimat cara membaca → tab: semua komoditas, saat melemah vs menguat, peta provinsi, episode pelemahan."""

import numpy as np
import pandas as pd
import streamlit as st

from common import (CFG, DRIVER_LABELS, PAGE, STRETCH, area_level, area_options, commodity_labels, fmt_interval,
                    fmt_num, footer, lead, load, load_geo, names_list, nav_link, need, not_detected_badge, note,
                    page_header, picker, show_table, unit_names, verdicts)
from kagami.viz import plots
from kagami.viz.style import AXIS_LABELS

page_header("Respons harga terhadap kurs")

H = 8
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
METRICS = {"R4":"Respons 4 minggu", "R8": "Respons 8 minggu", "R12": "Respons 12 minggu", "PT8": "Penerusan kurs 8 minggu"}


def _pct(x: pd.Series) -> pd.Series:
    return 100 * np.expm1(x)


def _map_clicked() -> None:
    """Klik titik peta → kurva di atas pindah ke wilayah provinsi yang diklik (callback jalan sebelum widget dibuat ulang)."""
    ev = st.session_state.get("map_sel")
    pts = (ev or {}).get("selection", {}).get("points", []) if isinstance(ev, dict) else getattr(
        getattr(ev, "selection", None), "points", [])
    reg = CFG.regions
    pid = None
    for p in pts:                                     # titik ibu kota provinsi (trace terakhir peta)
        cd = p.get("customdata")
        if cd:
            pid = cd[0]
        elif p.get("x") is not None:
            hit = reg[(reg["lon"].sub(p["x"]).abs() < 1e-6) & (reg["lat"].sub(p["y"]).abs() < 1e-6)]
            pid = hit["province_id"].iloc[0] if len(hit) else None
        if pid is not None:
            break
    if pid is None:
        return
    region = reg.set_index("province_id")["region"].get(int(pid))
    if region:
        st.session_state["pick_area"] = st.query_params["area"] = str(region)


got = need("profiles", "events")
if got:
    prof = got["profiles"]
    if "shrunk" in prof:                                   # provinsi: dua versi per sel (mentah & tersusut EB) →
        pv = prof["level"] == "province"                   # pakai yang tersusut (spec V05) agar satu nilai per h
        if (pv & prof["shrunk"].astype(bool)).any():
            prof = prof[~pv | prof["shrunk"].astype(bool)]
    labels, names = commodity_labels(), unit_names()
    nat = prof[(prof["level"] == "national") & (prof["unit"].astype(str) == "ALL")]
    e8 = nat[(nat["driver"] == "e") & (nat["horizon"] == H)].dropna(subset=["ci_low", "ci_high"])
    det = e8.loc[(e8["ci_low"] > 0) | (e8["ci_high"] < 0), "commodity"]
    if len(e8):
        lead((f"Dalam {H} minggu, respons harga eceran nasional terhadap kurs rupiah belum bisa dibedakan dari nol pada "
              f"ke-{len(e8)} komoditas. " if det.empty else
              f"Dalam {H} minggu, respons harga eceran nasional terhadap kurs rupiah terlihat pada {names_list(det, labels)}. ")
             + "Lebar rentang di grafik menunjukkan seberapa besar respons yang masih sejalan dengan data.")

    c1, c2, c3 = st.columns([1.1, 1.1, 1.5])
    com = picker("Komoditas", list(labels), "com", format_func=labels.get, container=c1)
    areas = area_options(prof, com)
    if not areas:
        st.warning("Belum ada estimasi untuk komoditas ini.")
        st.stop()
    area = picker("Wilayah", areas, "area", format_func=lambda u: names.get(u, u), default="ALL", container=c2)
    level = area_level(area)
    here = prof[(prof["commodity"] == com) & (prof["level"] == level) & (prof["unit"].astype(str) == area)]
    drivers = [d for d in ("e", "w") if d in set(here["driver"])]
    if not drivers:
        st.warning("Belum ada estimasi untuk pilihan ini.")
        st.stop()
    driver = picker("Dibandingkan dengan", drivers, "driver", format_func=DRIVER_LABELS.get, radio=True, container=c3)
    name, where = labels.get(com, com), names.get(area, area)
    sel = here[here["driver"] == driver].sort_values("horizon")

    st.plotly_chart(plots.response_curve(prof, com, level, area, driver, name=name, unit_name=where), **STRETCH)
    r8 = sel[sel["horizon"] == H]
    mde = load("mde")

    def _mde(hk: int) -> float:
        if mde is None or driver != "e":
            return float("nan")
        m = mde[(mde["commodity"] == com) & (mde["level"] == level) & (mde["horizon"] == hk)]
        if "unit" in m and level == "region":
            m = m[m["unit"].astype(str) == area]
        return float(m["mde_beta"].iloc[0]) if len(m) and "mde_beta" in m else float("nan")

    if len(r8):
        r = r8.iloc[0]
        cause = "rupiah melemah 1%" if driver == "e" else "harga dunia (dalam rupiah) naik 1%"
        txt = (f"Delapan minggu setelah {cause}, harga {name.lower()} {'nasional' if level == 'national' else 'di ' + where} "
               f"berubah {fmt_num(r['estimate'], 2, sign=True)}% (rentang 95%: "
               f"{fmt_interval(r['ci_low'], r['ci_high'], 2, pct=True)}). ")
        status = not_detected_badge(r["ci_low"], r["ci_high"])
        txt += {"tidak terdeteksi": "Rentang ini memuat nol, jadi responsnya belum bisa dibedakan dari tanpa respons. ",
                "terdeteksi": "Rentang ini tidak memuat nol. "}.get(status, "")
        m8 = _mde(H)
        if np.isfinite(m8):
            txt += f"Efek terkecil yang dapat dideteksi pada horizon ini sekitar {fmt_num(m8, 2)}%."
        st.markdown(txt)
    rows = []
    for hk in CFG.params["lp"]["key_horizons"]:
        r = sel[sel["horizon"] == hk]
        if len(r):
            r = r.iloc[0]
            rows.append({"Minggu ke-": hk, "Perkiraan (%)": round(r["estimate"], 2),
                         "Rentang 95% (%)": fmt_interval(r["ci_low"], r["ci_high"], 2),
                         "Kesimpulan": verdicts([r["ci_low"]], [r["ci_high"]])[0],
                         "Efek terkecil yang dapat dideteksi (%)": round(_mde(hk), 2)})
    if rows:
        with st.expander("Angka minggu ke-4, 8, dan 12"):
            show_table(pd.DataFrame(rows).dropna(axis=1, how="all"))
            note("Kami mengambil rentang 95% resmi dari yang lebih lebar antara galat baku dan bootstrap blok 13 minggu, "
                 "sesuai praregistrasi. Rentang ini cenderung lebar.")

    tab_all, tab_asym, tab_map, tab_ep = st.tabs(["Semua komoditas", "Saat melemah vs menguat", "Peta provinsi",
                                                  "Episode pelemahan rupiah"])

    with tab_all:
        h = picker("Minggu ke-", CFG.params["lp"]["key_horizons"], "h", default=H, radio=True)
        cmp_ = prof[(prof["level"] == level) & (prof["unit"].astype(str) == area) & (prof["driver"] == driver)
                    & (prof["horizon"] == h)].dropna(subset=["ci_low", "ci_high"]).copy()
        if len(cmp_) > 1:
            cmp_["komoditas"] = cmp_["commodity"].map(lambda c: labels.get(c, c))
            st.plotly_chart(plots.forest(
                cmp_.sort_values("estimate"), ["komoditas"],
                f"Respons {h} minggu terhadap {DRIVER_LABELS[driver].lower()}, semua komoditas ({where.lower() if area == 'ALL' else where})",
                x_title=AXIS_LABELS[driver]), **STRETCH)
            verd = verdicts(cmp_["ci_low"], cmp_["ci_high"])
            n_zero = verd.count("belum terlihat")
            if n_zero == len(verd):
                note(f"Pada {h} minggu, rentang 95% semua komoditas memuat nol. Artinya data belum bisa membedakan respons "
                     "setiap komoditas dari tanpa respons. Ujung kanan rentang tetap berguna: kenaikan harga yang lebih "
                     "besar dari angka itu tidak sejalan dengan data.")
            elif n_zero:
                note(f"Rentang 95% memuat nol pada {n_zero} dari {len(verd)} komoditas (titik kosong). Untuk komoditas itu, "
                     "data belum bisa membedakan respons dari tanpa respons.")
            tab = pd.DataFrame({"Komoditas": cmp_["komoditas"], "Perkiraan (%)": cmp_["estimate"].round(2),
                                "Rentang 95% (%)": [fmt_interval(a, b, 2) for a, b in zip(cmp_["ci_low"], cmp_["ci_high"])]})
            if len(set(verd)) > 1:
                tab["Kesimpulan"] = verd
            with st.expander("Lihat tabel"):
                show_table(tab)
        cal = load("national_calibrated")
        if cal is not None and not cal.empty and level == "national":
            c = cal[(cal["driver"] == driver) & (cal["horizon"] == h)]
            if len(c):
                with st.expander("Rentang alternatif dari kalibrasi data acak (analisis tambahan)"):
                    show = pd.DataFrame({
                        "Komoditas": c["commodity"].map(lambda x: labels.get(x, x)),
                        "Perkiraan (%)": c["estimate"].round(2),
                        "Rentang resmi (%)": [fmt_interval(a, b, 2) for a, b in zip(c["ci_prereg_low"], c["ci_prereg_high"])],
                        "Rentang terkalibrasi (%)": [fmt_interval(a, b, 2) for a, b in zip(c["ci_low"], c["ci_high"])],
                        "Kesimpulan terkalibrasi": verdicts(c["ci_low"], c["ci_high"]),
                        "p": c["p_value"].round(3), "q (koreksi 48 uji)": c["q_fdr"].round(3)})
                    show_table(show)
                    note("Semua grafik memakai rentang resmi. Bootstrap blok menarik estimasi ke arah nol, sehingga rentang "
                         "resmi terlalu lebar. Rentang terkalibrasi memakai sebaran hasil 499 data acak sebagai pembanding. "
                         "Kami melaporkannya sebagai analisis tambahan sesudah praregistrasi.")

    with tab_asym:
        asym = load("asymmetry")
        if asym is not None and not asym.empty and (asym["commodity"] == com).any():
            st.plotly_chart(plots.asymmetry_plot(prof, asym, com, name=name), **STRETCH)
            conf = asym.loc[asym["confirmatory"].fillna(False).astype(bool), "commodity"].unique()
            note(f"Uji formal yang kami daftarkan sebelum analisis hanya untuk {names_list(conf, labels)}, karena hanya "
                 "datanya yang cukup presisi untuk mendeteksi selisih yang berarti. Komoditas lain ditampilkan sebagai "
                 "gambaran.")
            a = asym[asym["commodity"] == com].sort_values("horizon")
            with st.expander("Lihat tabel"):
                show_table(pd.DataFrame({
                    "Minggu ke-": a["horizon"], "Saat melemah (%)": a["beta_pos"].round(2),
                    "Saat menguat (%)": a["beta_neg"].round(2), "Selisih (%)": a["estimate"].round(2),
                    "Rentang 95% selisih": [fmt_interval(x, y, 2) for x, y in zip(a["ci_low"], a["ci_high"])],
                    "p (uji Wald)": a["p_value"].round(3),
                    "Kesimpulan": verdicts(a["ci_low"], a["ci_high"], pos="lebih besar saat melemah",
                                           neg="lebih besar saat menguat", zero="belum terlihat beda")}))
        else:
            st.caption("Belum ada uji untuk komoditas ini.")

    with tab_map:
        geo = load_geo()
        m1, m2 = st.columns([2, 1])
        maplv = picker("Tampilkan", ["region", "province"], "maplv",
                       format_func={"region": "7 wilayah", "province": "34 provinsi"}.get, radio=True, container=m1)
        mh = picker("Minggu ke-", CFG.params["lp"]["key_horizons"], "maph", default=H, radio=True, container=m2)
        if geo is not None:
            mv = prof[(prof["level"] == maplv) & (prof["commodity"] == com) & (prof["driver"] == driver)
                      & (prof["horizon"] == mh)]
            if len(mv):
                flat = mv["estimate"].round(6).nunique() == 1
                ttl = (f"{name}: respons {mh} minggu per wilayah" if maplv == "region" else
                       f"{name}: selisih respons provinsi dari rata-rata, {mh} minggu")
                st.plotly_chart(plots.region_map(geo, mv, maplv, ttl, "Klik titik untuk menampilkan kurva wilayahnya."),
                                on_select=_map_clicked, selection_mode="points", key="map_sel", **STRETCH)
                txt = ("Warna adalah perkiraan titik tanpa rentang. Untuk sebagian besar komoditas, perbedaan antarwilayah "
                       "tidak melebihi kebetulan, jadi warna yang berbeda belum tentu perbedaan nyata. ")
                if maplv == "province":
                    txt += ("Nilai provinsi adalah selisih dari rata-rata semua provinsi, sesudah ditarik ke arah rata-rata, "
                            "makin kuat bila data provinsinya kurang presisi, agar provinsi dengan data sedikit tidak tampak "
                            "ekstrem. ")
                    if flat:
                        txt += f"Untuk {name.lower()}, data tidak cukup untuk membedakan provinsi, jadi semua sama. "
                note(txt + "Geometri provinsi © OpenStreetMap contributors (ODbL), via geoBoundaries.")
        feats = load("response_features")
        if feats is not None and not feats.empty:
            f1, f2 = st.columns(2)
            metric = f1.radio("Ukuran", list(METRICS), index=1, horizontal=True, format_func=METRICS.get)
            lvls = [x for x in ("region", "province") if x in set(feats["level"])] or ["national"]
            lv = f2.radio("Tingkat", lvls, horizontal=True, format_func={"region": "7 wilayah", "province": "34 provinsi",
                                                                          "national": "Nasional"}.get)
            st.plotly_chart(plots.sensitivity_heatmap(feats, lv, metric, labels=labels, unit_names=names,
                                                      metric_label=METRICS[metric]), **STRETCH)
            rank = feats[(feats["level"] == "province") & (feats["commodity"] == com)].sort_values("R8", ascending=False)
            if len(rank):
                with st.expander(f"Peringkat provinsi untuk {name.lower()}"):
                    show_table(pd.DataFrame({
                        "Provinsi": rank["unit"].astype(str).map(names), "Respons 4 minggu (%)": rank["R4"].round(2),
                        "Respons 8 minggu (%)": rank["R8"].round(2), "Respons 12 minggu (%)": rank["R12"].round(2),
                        "Minggu sampai separuh respons": rank["t_half"].round(1)}))
                    note("Respons provinsi = respons nasional ditambah selisih provinsi yang sudah ditarik ke arah rata-rata.")

    with tab_ep:
        ev, eps = got["events"], load("episodes")
        e = ev[(ev["commodity"] == com) & (ev["level"] == "national") & (ev["horizon"] == H)]
        n_ep = len(eps) if eps is not None else e["episode_id"].nunique()
        if (ev["commodity"] == com).any():
            st.plotly_chart(plots.episode_fan(ev, com, eps, name=name), **STRETCH)
        note(f"Kami menandai {n_ep} episode pelemahan rupiah (rupiah melemah minimal 3% dalam 8 minggu) dan membandingkan "
             "perubahan harga sesudahnya dengan 499 jendela waktu tanpa episode. Lini masa kurs dan kipas semua komoditas ada "
             "di halaman Rupiah dari waktu ke waktu.")
        nav_link(PAGE["lini_masa"], "Buka lini masa rupiah", ":material/timeline:")
        if len(e):
            show = e.copy()
            if eps is not None:
                show = show.merge(eps[["episode_id", "start_week", "cum_dlog_e"]], on="episode_id", how="left")
                t = pd.to_datetime(show["start_week"])
                show["Mulai"] = [f"{MONTHS[d.month - 1]} {d.year}" for d in t]
                show["Pelemahan rupiah (%)"] = _pct(show["cum_dlog_e"]).round(1)
            show["Perubahan harga (%)"] = _pct(show["dlog_price"]).round(2)
            show["Rentang 95% data acak (%)"] = [f"{fmt_num(a, 2, sign=True)} s.d. {fmt_num(b, 2, sign=True)}"
                                                 for a, b in zip(_pct(show["placebo_lo"]), _pct(show["placebo_hi"]))]
            show["p"] = show["placebo_p"].round(3)
            cols = [c for c in ("Mulai", "Pelemahan rupiah (%)", "Perubahan harga (%)", "Rentang 95% data acak (%)", "p")
                    if c in show]
            with st.expander(f"Angka minggu ke-{H} per episode"):
                show_table(show[cols])

footer("PIHPS dan JISDOR (Bank Indonesia), Pink Sheet (Bank Dunia)")
