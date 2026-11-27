"""Halaman 4 -- Eksposur & Nilai Prediktif (WP-31)."""

import streamlit as st

from common import STRETCH, commodity_labels, fmt_num, footer, load, need, page_header, table, with_status
from kagami.viz import plots, style

page_header("Eksposur & prediksi",
            "Lewat jalur apa komoditas ini terpapar, dan apakah fitur kurs memperbaiki prediksi dalam evaluasi historis?")

got = need("exposure", "response_features", "assoc", "forecast_eval", "ablation")
if got:
    st.subheader("Tiga jalur eksposur vs respons nasional")
    nat = got["response_features"].query("level == 'national'")[["commodity", "PT8", "W8"]]
    expo = got["exposure"].merge(nat, on="commodity", how="left")
    conc = load("concordance")
    if conc is not None and "confidence" in conc:
        expo = expo.merge(conc[["commodity", "confidence"]].rename(columns={"confidence": "keyakinan_konkordansi"}),
                          on="commodity", how="left")
    labels = commodity_labels()
    expo = expo.assign(commodity=expo["commodity"].map(lambda c: labels.get(c, c)),
                       exposure_path=expo["exposure_path"].map(lambda p: style.PATH_LABELS.get(p, p)))
    ren = {"commodity": "Komoditas", "exposure_path": "Jalur eksposur", "import_ratio_direct": "Rasio impor langsung",
           "imported_input_ordinal": "Input impor (0–2)", "world_price_link": "Ada harga dunia padanan",
           "PT8": "PT(8) nasional", "W8": "Respons harga dunia (8 mgg)", "keyakinan_konkordansi": "Keyakinan konkordansi",
           "source": "Sumber & tahun rasio impor"}
    st.dataframe(expo[[c for c in ren if c in expo]].rename(columns=ren), hide_index=True, **STRETCH,
                 column_config={"Rasio impor langsung": st.column_config.NumberColumn(format="percent"),
                                "PT(8) nasional": st.column_config.NumberColumn(format="%.2f"),
                                "Respons harga dunia (8 mgg)": st.column_config.NumberColumn(format="%.2f")})
    st.caption("Rasio impor langsung hanya mengukur porsi impor komoditas itu sendiri. Sumber dan tahun pengamatannya berbeda "
               "per komoditas (kolom terakhir); bawang putih memakai impor BPS/Comtrade dan produksi ATAP satu tahun saja, tanpa "
               "ekspor, karena FAOSTAT tidak memuat bawang putih kering. Eksposur lewat input impor (pakan untuk daging ayam & "
               "telur) diukur terpisah di kolom Input impor dan lewat harga dunia komposit jagung–bungkil kedelai. Jadi angka "
               "antarkomoditas tidak setara kualitas dan periodenya. Keyakinan konkordansi = keyakinan pemetaan "
               "PIHPS–HS–Pink Sheet–FAOSTAT.")

    assoc = got["assoc"]
    method = assoc["method"] if "method" in assoc else assoc.get("level")
    ken = assoc[method.astype(str).str.startswith("kendall")]
    if len(ken):
        k = ken.iloc[0]
        st.metric("E1 · Kendall τ-b PT(8) vs rasio impor langsung (N = 10)", f"{k['estimate']:+.3f}",
                  help=f"interval jackknife {k['ci_low']:+.2f} s.d. {k['ci_high']:+.2f}; p permutasi eksak {k['p_value']:.2f}")
    st.caption("N = 10 komoditas: kesimpulan berlaku 'di antara 10 komoditas yang diamati'.")

    st.subheader("Karakteristik provinsi (Task 3)")
    meta = assoc[method.astype(str).str.startswith("meta_regression")]
    if len(meta):
        hs = sorted({int(x) for x in meta["horizon"].dropna()}) if "horizon" in meta else []
        h = st.selectbox("Horizon meta-regresi (minggu)", hs, index=0) if hs else None
        m = meta if h is None else meta[meta["horizon"] == h]
        m = m.assign(fitur=m["feature"].map(lambda f: style.FEATURE_LABELS.get(f, f)) if "feature" in m else "",
                     komoditas=m["commodity"].map(lambda c: "Gabungan 10 komoditas" if c == "ALL" else labels.get(c, c)))
        per = st.toggle("Tampilkan per komoditas", value=False, key="meta_per")
        mv = m if per else m[m["commodity"] == "ALL"]
        lab = ["komoditas", "fitur"] if per else ["fitur"]
        st.plotly_chart(plots.forest(mv, lab, "Meta-regresi efek acak: Δ respons per 1 SD fitur"
                                     + ("" if per else " (gabungan 10 komoditas)")), **STRETCH)
        cols = [c for c in ("komoditas", "fitur", "horizon", "estimate", "ci_low", "ci_high", "p_value", "q_fdr",
                            "jackknife_min", "jackknife_max") if c in m]
        table(m[cols], "Tabel meta-regresi lengkap")
        st.caption("Interval = yang lebih lebar dari CR2 dan bootstrap; p konsisten dengan interval itu; q = BH atas baris "
                   "eksploratif. H3 (ln_dist_hub, h = 4) diuji satu sisi.")
        st.caption("Fitur adalah proksi: `ln_dist_hub` = jarak garis lurus ibu kota provinsi ke hub terdekat (bukan biaya atau "
                   "waktu logistik), `rice_sufficiency` = kecukupan produksi beras saja (bukan pangan lain), `n_kota` = jumlah kota "
                   "sampel PIHPS (bukan tingkat integrasi pasar). Koefisien yang tidak terdeteksi berarti proksi ini tidak "
                   "menjelaskan variasi respons dalam desain ini, bukan bahwa logistik atau produksi tidak penting.")
    fe = assoc[method.astype(str) == "fe_interaction"]
    if len(fe):
        with st.expander("Interaksi efek tetap komoditas×minggu (pemeriksaan kepekaan 3c)"):
            cols = [c for c in ("feature", "horizon", "estimate", "ci_low", "ci_high", "p_value", "n") if c in fe]
            st.dataframe(with_status(fe[cols]), hide_index=True, **STRETCH)

    reg = load("regime_profiles")
    if reg is not None and not reg.empty:
        st.subheader("Respons per rezim HET/HAP (E2, eksploratif)")
        labels = commodity_labels()
        coms = [c for c in labels if c in set(reg["commodity"])]
        c1, c2, c3 = st.columns(3)
        com = c1.selectbox("Komoditas rezim", coms, format_func=labels.get)
        drv = c2.selectbox("Penggerak rezim", sorted(reg.loc[reg["commodity"] == com, "driver"].unique()),
                           format_func=lambda d: style.DRIVER_LABELS.get(d, d))
        hr = c3.selectbox("Horizon rezim", sorted(reg.loc[reg["commodity"] == com, "horizon"].unique()))
        r = reg[(reg["commodity"] == com) & (reg["driver"] == drv) & (reg["horizon"] == hr)]
        lab = [c for c in ("regime_id", "label") if c in r]
        st.plotly_chart(plots.forest(r, lab, f"{labels.get(com, com)} · {style.DRIVER_LABELS.get(drv, drv)} · h = {hr}"),
                        **STRETCH)
        cols = [c for c in ("regime_id", "label", "regime_start", "regime_end", "n_weeks", "estimate", "ci_low",
                            "ci_high", "baseline_estimate", "p_placebo", "q_fdr") if c in r]
        st.dataframe(with_status(r[cols]), hide_index=True, **STRETCH)
        if "q_fdr" in reg:
            st.caption(f"Interval dikalibrasi plasebo geser-melingkar; q BH minimum seluruh tabel "
                       f"{reg['q_fdr'].min():.3f}. Rezim pendek → interval lebar; bukan bukti efek regulasi.")

    st.subheader("Evaluasi bersyarat rolling-origin (Task 4)")
    fe4 = got["forecast_eval"]
    labels = commodity_labels()
    tot = fe4[(fe4["subset"] == "all") & (fe4["model"] == "M2")]
    if "level" in tot:
        tot = tot[tot["level"] == "all"]
    if len(tot):
        cols = st.columns(len(tot))
        for col, r in zip(cols, tot.sort_values("horizon").itertuples()):
            col.metric(f"Rasio MAE M2/M1, h = {r.horizon} minggu", fmt_num(r.mae_ratio_vs_m1, 3),
                       help="< 1 = fitur kurs & harga dunia memperbaiki akurasi; > 1 = memperburuk.")
            dm = style.dm_summary(getattr(r, "dm_stat", float("nan")), r.dm_p, getattr(r, "dm_p_one_sided", None))
            col.caption(f"{dm} · {int(r.n_origins)} origin")
        st.caption("Tanda DM menunjukkan arah (D-169): DM > 0 = M2 lebih akurat dari M1, DM < 0 = kurang akurat. p dua sisi yang "
                   "kecil dengan DM negatif berarti M2 nyata lebih buruk, bukan lebih baik. RQ5/H5 menanyakan perbaikan "
                   "(M2 lebih akurat), sehingga p satu sisi itulah yang relevan untuk klaim perbaikan.")
    for subset in ("all", "large_move"):
        if (fe4["subset"] == subset).any():
            st.plotly_chart(plots.forecast_ratios(fe4, subset, labels=labels), **STRETCH)
    if "h5_p_holm" in fe4:
        table(fe4[fe4["h5_p_holm"].notna()], "H5: grup fokus per jalur eksposur (h = 8, koreksi Holm)", status=False)
    with st.expander("Tabel lengkap evaluasi dan ablation"):
        st.dataframe(fe4, hide_index=True, **STRETCH)
        st.dataframe(got["ablation"], hide_index=True, **STRETCH)
        st.caption("Ablation = MAE M2 tanpa fitur kurs & harga dunia − MAE M2; karena M2 = M1 + fitur itu, nilainya sama "
                   "dengan −(MAE M2 − MAE M1).")
    st.caption("Rasio MAE vs M1 < 1 = lebih akurat dari M1. Evaluasi bersyarat atas pola historis (pseudo-real-time; "
               "vintage revisi tidak tersedia), bukan sistem peramalan.")

footer("Turunan PIHPS, FAOSTAT, BPS, Pink Sheet", "τ-b / Δ respons per SD / rasio MAE", "2018-2026 (Task 4: 2021-2026)")
