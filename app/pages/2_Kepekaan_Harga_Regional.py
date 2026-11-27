"""Halaman 2 -- Kepekaan Harga Regional (WP-31; tata letak PLAN.md §18: IRF + forest + tabel kembaran)."""

import streamlit as st

from common import (CFG, DRIVER_LABELS, LEVEL_LABELS, STRETCH, commodity_labels, fmt_interval, fmt_num, footer,
                    load, load_geo, need, not_detected_badge, page_header, picker, reset_button, table, unit_names)
from kagami.viz import plots

page_header("Kepekaan harga", "Komoditas mana di wilayah saya yang historisnya paling peka?")

KEYS = ["com", "level", "unit", "driver", "h", "maplv"]


def _map_clicked() -> None:
    """Klik peta → tingkat & unit IRF ikut provinsi/wilayah yang diklik (callback jalan sebelum widget dibuat ulang)."""
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
    maplv = st.session_state.get("pick_maplv", "region")
    unit = CFG.regions.set_index("province_id")["region"].get(int(pid)) if maplv == "region" else str(pid)
    if unit is None:
        return
    st.session_state["pick_level"], st.session_state["pick_unit"] = maplv, str(unit)
    st.query_params["level"], st.query_params["unit"] = maplv, str(unit)


got = need("profiles", "events")
if got:
    prof = got["profiles"]
    if "shrunk" in prof:                                   # provinsi: dua versi per sel (mentah & tersusut EB) →
        pv = prof["level"] == "province"                   # pakai yang tersusut (spec V05) agar satu nilai per h
        if (pv & prof["shrunk"].astype(bool)).any():
            prof = prof[~pv | prof["shrunk"].astype(bool)]
    labels, names = commodity_labels(), unit_names()
    c1, c2, c3 = st.columns(3)
    com = picker("Komoditas", list(labels), "com", format_func=labels.get, container=c1)
    levels = [lv for lv in ("national", "region", "province") if lv in set(prof["level"])]
    level = picker("Tingkat", levels, "level", format_func=LEVEL_LABELS.get, container=c2)
    units = prof.loc[prof["level"] == level, "unit"].astype(str).unique().tolist()
    units = sorted(units, key=lambda u: (0, int(u)) if u.isdigit() else (1, u))
    unit = picker("Unit", units, "unit", format_func=lambda u: names.get(u, u), container=c3)
    drivers = [d for d in ("e", "w", "PT", "e_pos", "e_neg")
               if d in set(prof.loc[(prof["level"] == level) & (prof["commodity"] == com), "driver"])]
    if not drivers:
        st.warning("Tidak ada estimasi untuk komoditas dan tingkat ini.")
        st.stop()
    d1, d2 = st.columns([2, 1])
    driver = picker("Penggerak", drivers, "driver", format_func=DRIVER_LABELS.get, default="e", radio=True,
                    container=d1)
    hs = CFG.params["lp"]["key_horizons"]
    h = picker("Horizon peta & pembanding (minggu)", hs, "h", default=8, radio=True, container=d2)
    reset_button(KEYS)

    geo = load_geo()
    map_drv = driver if driver in ("e", "w") else "e"
    if geo is not None:
        maplv = picker("Peta", [lv for lv in ("region", "province") if lv in levels], "maplv",
                       format_func=LEVEL_LABELS.get, radio=True)
        mv = prof[(prof["level"] == maplv) & (prof["commodity"] == com) & (prof["driver"] == map_drv)
                  & (prof["horizon"] == h)]
        if len(mv):
            flat = mv["estimate"].round(6).nunique() == 1
            sub = (f"{DRIVER_LABELS[map_drv]} · h = {h} · klik {LEVEL_LABELS[maplv].lower()} untuk melihat kurvanya"
                   + (" · semua provinsi = rerata (τ² = 0)" if flat else ""))
            ttl = (f"Di mana respons {labels.get(com, com)} paling besar?" if maplv == "region" else
                   f"Provinsi mana yang menyimpang dari rerata ({labels.get(com, com)})?")
            st.plotly_chart(plots.region_map(geo, mv, maplv, ttl, sub),
                            on_select=_map_clicked, selection_mode="points", key="map_sel", **STRETCH)
            if flat and maplv == "province":
                st.info("τ² = 0: penyusutan empirical Bayes mengembalikan semua provinsi ke rerata nasional. Peta satu warna "
                        "ini hasil yang sah, bukan grafik rusak.")
            st.caption("Warna = estimasi titik tanpa ketidakpastian. Perbedaan antarwilayah tidak lolos uji plasebo untuk "
                       "sebagian besar komoditas dan provinsi tidak membentuk kelompok (halaman Pola regional), jadi warna "
                       "yang berbeda belum tentu perbedaan nyata. "
                       "Geometri provinsi © OpenStreetMap contributors (ODbL), via geoBoundaries. "
                       + ("Peta wilayah mewarnai setiap provinsi dengan nilai wilayahnya. " if maplv == "region"
                          else "Nilai provinsi = deviasi dari rerata lintas provinsi (Σ = 0), tersusut empirical Bayes; "
                               "respons total = nasional + deviasi. ")
                       + "Bandingkan angka lewat forest plot di bawah.")

    sel = prof[(prof["commodity"] == com) & (prof["level"] == level) & (prof["unit"].astype(str) == unit)
               & (prof["driver"] == driver)].sort_values("horizon")
    if sel.empty:
        st.warning("Tidak ada estimasi untuk kombinasi ini.")
    else:
        st.plotly_chart(plots.response_curve(prof, com, level, unit, driver, name=labels.get(com, com),
                                             unit_name=names.get(unit, unit)), **STRETCH)
        mde = load("mde")
        cols = st.columns(3)
        for col, hk in zip(cols, CFG.params["lp"]["key_horizons"]):
            r = sel[sel["horizon"] == hk]
            if r.empty:
                continue
            r = r.iloc[0]
            col.metric(f"h = {hk} minggu", fmt_num(r["estimate"], 3, sign=True),
                       help="Respons kumulatif (Δ log harga per 1 log penggerak).")
            txt = f"{not_detected_badge(r['ci_low'], r['ci_high'])} · interval {fmt_interval(r['ci_low'], r['ci_high'], 3)}"
            if mde is not None and driver in ("e", "PT") and level in ("national", "region"):
                m = mde[(mde["commodity"] == com) & (mde["level"] == level) & (mde["horizon"] == hk)]
                if "unit" in m and level == "region":
                    m = m[m["unit"].astype(str) == unit]
                mcol = "mde_beta" if driver == "e" else "mde_pt"
                if len(m) and mcol in m:
                    txt += f" · batas deteksi (MDE) {fmt_num(m[mcol].iloc[0], 2)}"
            col.caption(txt)
        st.caption("Interval resmi (praregistrasi) = yang lebih lebar dari ±1,96·SE cluster minggu dan persentil bootstrap "
                   "blok 13 minggu; cenderung konservatif. Respons yang interval-nya memuat nol adalah batas atas "
                   "kepekaan, bukan bukti nol.")

        cmp_ = prof[(prof["level"] == level) & (prof["unit"].astype(str) == unit) & (prof["driver"] == driver)
                    & (prof["horizon"] == h)].dropna(subset=["ci_low", "ci_high"]).copy()
        if len(cmp_) > 1:
            cmp_["komoditas"] = cmp_["commodity"].map(lambda c: labels.get(c, c))
            st.plotly_chart(plots.forest(cmp_.sort_values("estimate"), ["komoditas"],
                                         f"Komoditas mana yang paling peka? ({DRIVER_LABELS.get(driver, driver)}, h = {h})",
                                         x_title="respons kumulatif"), **STRETCH)
            table(cmp_[["komoditas", "estimate", "ci_low", "ci_high"]], "Lihat tabel perbandingan")

    cal = load("national_calibrated")
    if cal is not None and not cal.empty:
        c = cal[cal["commodity"] == com]
        cols = [x for x in ("driver", "horizon", "estimate", "ci_prereg_low", "ci_prereg_high", "ci_low", "ci_high",
                            "p_value", "q_fdr", "boot_ratio") if x in c]
        if len(c):
            table(c[cols], "Analisis kepekaan inferensi: interval nasional terkalibrasi plasebo")
        st.caption("Interval terkalibrasi (tambahan, bukan praregistrasi): ±crit·SE dengan crit dari plasebo geser-melingkar; "
                   "q = koreksi BH atas 48 sel; ci_prereg_* = interval resmi yang dipakai grafik.")

    asym = load("asymmetry")
    if asym is not None and not asym.empty:
        a = asym[asym["commodity"] == com]
        cols = [x for x in ("horizon", "beta_pos", "beta_neg", "estimate", "ci_low", "ci_high", "p_value", "p_placebo",
                            "confirmatory", "reject") if x in a]
        if len(a):
            st.plotly_chart(plots.asymmetry_plot(prof, asym, com, name=labels.get(com, com)), **STRETCH)
            table(a[cols], "Lihat tabel H2: β⁺ − β⁻ nasional")
        st.caption("Uji konfirmatori H2 (Wald, h = 8) hanya untuk beras dan daging sapi (lolos gerbang G-power); lainnya "
                   "deskriptif.")

    feats = load("response_features")
    if feats is not None and not feats.empty:
        st.subheader("Peta kepekaan")
        mc1, mc2 = st.columns(2)
        metric = mc1.radio("Ukuran", ["R4", "R8", "R12", "PT8"], index=1, horizontal=True)
        lvls = [x for x in ("region", "province") if x in set(feats["level"])] or ["national"]
        lv = mc2.selectbox("Tingkat peta", lvls, format_func=LEVEL_LABELS.get)
        st.plotly_chart(plots.sensitivity_heatmap(feats, lv, metric, labels=labels, unit_names=names), **STRETCH)
        st.caption("Estimasi titik per sel tanpa interval; pakai untuk orientasi, bukan untuk menyimpulkan wilayah mana yang "
                   "lebih peka (uji heterogenitas di halaman Pola regional).")
        rank = feats[(feats["level"] == "province") & (feats["commodity"] == com)].sort_values("R8", ascending=False)
        if len(rank):
            if rank["R8"].nunique() == 1:
                st.info(f"Varians antarprovinsi τ² = 0 untuk {labels.get(com, com)}: semua provinsi disusutkan ke respons "
                        "rerata (penyusutan empirical Bayes). Perbedaan warna antarprovinsi tidak ada karena data tidak "
                        "mendukungnya.")
            rank = rank.assign(provinsi=rank["unit"].astype(str).map(names))
            table(rank[["provinsi", "R4", "R8", "R12", "t_half"]], "Peringkat provinsi (respons nasional + deviasi tersusut)",
                  status=False)

    ev = got["events"]
    e = ev[ev["commodity"] == com]
    if len(e):
        ren = {"episode_id": "episode", "level": "tingkat", "unit": "unit", "horizon": "h (minggu)",
               "dlog_price": "perubahan log harga", "placebo_lo": "pita plasebo bawah", "placebo_hi": "pita plasebo atas",
               "placebo_p": "p plasebo"}
        e = e.assign(level=e["level"].map(LEVEL_LABELS).fillna(e["level"]),
                     unit=e["unit"].astype(str).map(lambda u: names.get(u, u)))
        table(e[[c for c in ren if c in e]].rename(columns=ren).round(4),
              "Event study per episode depresiasi (vs 499 jendela plasebo)", status=False)

footer("PIHPS (BI), JISDOR (BI), Pink Sheet (Bank Dunia)", "Δ log harga per 1 log penggerak", "2018-2026")
