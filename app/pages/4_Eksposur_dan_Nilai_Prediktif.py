"""Halaman 4 -- Faktor yang berkaitan dengan kepekaan (WP-31; D-171). Jalur impor (rasio impor, Kendall), karakteristik
provinsi (meta-regresi; H3), dan respons per periode regulasi HET/HAP (E2). Evaluasi prediksi pindah ke halaman Prediksi
(`pages/9_Prediksi.py`); url_path halaman ini tetap `Eksposur_dan_Nilai_Prediktif`."""

import re

import streamlit as st

from common import (PAGE, STRETCH, commodity_labels, fmt_interval, fmt_num, footer, frame, intervals, lead, load,
                    nav_link, need, note, page_header)
from kagami.viz import plots, style

page_header("Faktor yang berkaitan dengan kepekaan")
CONF = {"high": "tinggi", "medium": "sedang", "low": "rendah"}

got = need("exposure", "response_features", "assoc")
if got:
    labels = commodity_labels()
    assoc = got["assoc"]
    method = (assoc["method"] if "method" in assoc else assoc.get("level")).astype(str)
    ken = assoc[method.str.startswith("kendall")]
    meta = assoc[method.str.startswith("meta_regression")]
    h3 = meta[(meta["commodity"] == "ALL") & (meta["feature"] == "ln_dist_hub") & (meta["horizon"] == 4)] \
        if {"commodity", "feature", "horizon"} <= set(meta.columns) else meta.iloc[0:0]
    prof = load("profiles")
    mg = (prof[(prof["level"] == "national") & (prof["unit"].astype(str) == "ALL") & (prof["driver"] == "w")
               & (prof["commodity"] == "minyak_goreng") & (prof["horizon"] == 4)] if prof is not None else None)
    no_import = len(ken) and ken["p_value"].iloc[0] >= 0.05
    no_dist = len(h3) and h3["p_value"].iloc[0] >= 0.05
    txt = ("Porsi impor dan jarak provinsi ke pusat distribusi tidak menjelaskan perbedaan respons. "
           if no_import and no_dist else "")
    if mg is not None and len(mg) and ((mg["ci_low"] > 0) | (mg["ci_high"] < 0)).iloc[0]:
        txt += ("Hubungan yang konsisten terlihat pada minyak goreng, yang harganya bergerak bersama harga sawit dunia "
                "dalam rupiah.")
    if txt:
        lead(txt)

    st.subheader("Jalur impor dan respons nasional")
    nat = got["response_features"].query("level == 'national'")[["commodity", "PT8", "W8"]]
    expo = got["exposure"].merge(nat, on="commodity", how="left")
    conc = load("concordance")
    if conc is not None and "confidence" in conc:
        expo = expo.merge(conc[["commodity", "confidence"]], on="commodity", how="left")
        expo["confidence"] = expo["confidence"].map(lambda c: CONF.get(c, c))
    expo = expo.assign(commodity=expo["commodity"].map(lambda c: labels.get(c, c)),
                       exposure_path=expo["exposure_path"].map(lambda p: style.PATH_LABELS.get(p, p)),
                       source=expo["source"].astype(str).map(lambda s: re.sub(r"\s*\(U\d+\)", "", s)))
    ren = {"commodity": "Komoditas", "exposure_path": "Jalur", "import_ratio_direct": "Porsi impor",
           "imported_input_ordinal": "Input impor (0–2)", "PT8": "Penerusan kurs", "W8": "Respons harga dunia",
           "confidence": "Keyakinan kode", "source": "Sumber porsi impor"}
    st.dataframe(expo[[c for c in ren if c in expo]].rename(columns=ren), hide_index=True, **STRETCH,
                 column_config={"Porsi impor": st.column_config.NumberColumn(format="percent"),
                                "Penerusan kurs": st.column_config.NumberColumn(format="%.2f"),
                                "Respons harga dunia": st.column_config.NumberColumn(format="%.2f")})
    if len(ken):
        k = ken.iloc[0]
        st.markdown(f"Urutan 10 komoditas menurut porsi impor {'tidak ' if k['p_value'] >= 0.05 else ''}sejalan dengan "
                    f"urutan penerusan kursnya: korelasi peringkat Kendall {fmt_num(k['estimate'], 2)} (rentang "
                    f"{fmt_interval(k['ci_low'], k['ci_high'], 2)}), p uji permutasi eksak {fmt_num(k['p_value'], 2)}.")
    note("Penerusan kurs dan respons harga dunia diukur pada 8 minggu, tingkat nasional. Keyakinan kode menilai pemetaan "
         "komoditas PIHPS ke kode impor dan seri harga dunia. "
         "Porsi impor langsung diukur dari sumber dan tahun yang berbeda per komoditas (kolom terakhir), jadi mutunya tidak "
         "setara. Bawang putih memakai impor BPS/Comtrade dan produksi ATAP karena FAOSTAT tidak memuat bawang putih "
         "kering. Ketergantungan pada pakan impor untuk daging ayam dan telur dicatat di kolom input impor.")

    st.subheader("Karakteristik provinsi")
    if len(h3):
        st.markdown("Kami menguji apakah provinsi yang lebih jauh dari pusat distribusi (Jakarta, Surabaya, Makassar) "
                    "merespons lebih lambat dalam 4 minggu. Hasilnya "
                    + ("tidak mendukung" if h3["p_value"].iloc[0] >= 0.05 else "mendukung")
                    + f" (p satu sisi {fmt_num(h3['p_value'].iloc[0], 2)}).")
    if len(meta):
        hs = sorted({int(x) for x in meta["horizon"].dropna()}) if "horizon" in meta else []
        c1, c2 = st.columns([1, 2])
        h = c1.selectbox("Minggu ke-", hs, index=0) if hs else None
        per = c2.toggle("Tampilkan per komoditas", value=False, key="meta_per")
        m = meta if h is None else meta[meta["horizon"] == h]
        m = m.assign(fitur=m["feature"].map(lambda f: style.FEATURE_LABELS.get(f, f)) if "feature" in m else "",
                     komoditas=m["commodity"].map(lambda c: "Gabungan 10 komoditas" if c == "ALL" else labels.get(c, c)))
        mv = m if per else m[m["commodity"] == "ALL"]
        st.plotly_chart(plots.forest(mv, ["komoditas", "fitur"] if per else ["fitur"],
                                     f"Karakteristik provinsi dan respons {h} minggu"
                                     + ("" if per else ", gabungan 10 komoditas"),
                                     x_title="selisih respons per 1 simpangan baku karakteristik"), **STRETCH)
        with st.expander("Lihat tabel"):
            st.dataframe(frame(m, {
                "Komoditas": lambda d: d["komoditas"], "Karakteristik": lambda d: d["fitur"],
                "Minggu ke-": lambda d: d["horizon"].astype(int), "Estimasi": lambda d: d["estimate"].round(3),
                "Rentang 95%": lambda d: intervals(d["ci_low"], d["ci_high"], 3), "p": lambda d: d["p_value"].round(3),
                "q": lambda d: d["q_fdr"].round(3)}), hide_index=True, **STRETCH)
        note("Ketiga karakteristik adalah proksi. Jarak diukur garis lurus dari ibu kota provinsi ke pusat terdekat; "
             "kecukupan produksi hanya mencakup beras; jumlah kota sampel PIHPS tidak sama dengan tingkat integrasi pasar. "
             "Proksi yang tidak berhubungan dengan respons belum berarti logistik atau produksi tidak penting.")
    fe = assoc[method == "fe_interaction"]
    if len(fe):
        with st.expander("Pemeriksaan tambahan: model efek tetap komoditas × minggu"):
            st.dataframe(frame(fe, {
                "Karakteristik": lambda d: d["feature"].map(lambda f: style.FEATURE_LABELS.get(f, f)),
                "Minggu ke-": lambda d: d["horizon"].astype(int), "Estimasi": lambda d: d["estimate"].round(3),
                "Rentang 95%": lambda d: intervals(d["ci_low"], d["ci_high"], 3), "p": lambda d: d["p_value"].round(3)}),
                hide_index=True, **STRETCH)

    reg = load("regime_profiles")
    if reg is not None and not reg.empty:
        st.subheader("Sekitar perubahan HET dan HAP")
        qmin = reg["q_fdr"].min() if "q_fdr" in reg else float("nan")
        st.markdown("Kami membagi periode setiap komoditas menurut tanggal pemerintah menetapkan atau mengubah harga eceran "
                    "tertinggi (HET) atau harga acuan (HAP), lalu mengukur respons di setiap periode."
                    + (f" Setelah koreksi untuk {len(reg)} perbandingan, tidak ada periode yang responsnya berbeda "
                       f"(q terkecil {fmt_num(qmin, 2)})." if qmin >= 0.05 else ""))
        coms = [c for c in labels if c in set(reg["commodity"])]
        c1, c2, c3 = st.columns(3)
        com = c1.selectbox("Komoditas", coms, format_func=labels.get, key="reg_com")
        drv = c2.selectbox("Dibandingkan dengan", sorted(reg.loc[reg["commodity"] == com, "driver"].unique()),
                           format_func=lambda d: style.DRIVER_LABELS.get(d, d), key="reg_drv")
        hr = c3.selectbox("Minggu ke-", sorted(reg.loc[reg["commodity"] == com, "horizon"].unique()), key="reg_h")
        r = reg[(reg["commodity"] == com) & (reg["driver"] == drv) & (reg["horizon"] == hr)]
        st.plotly_chart(plots.forest(r, ["label"] if "label" in r else ["regime_id"],
                                     f"{labels.get(com, com)}: respons per periode regulasi, {hr} minggu",
                                     x_title=style.AXIS_LABELS.get(drv, "respons")), **STRETCH)
        with st.expander("Lihat tabel"):
            st.dataframe(frame(r, {
                "Periode": lambda d: d["label"], "Mulai": lambda d: d["regime_start"], "Selesai": lambda d: d["regime_end"],
                "Jumlah minggu": lambda d: d["n_weeks"], "Respons": lambda d: d["estimate"].round(2),
                "Rentang 95%": lambda d: intervals(d["ci_low"], d["ci_high"]),
                "Respons seluruh periode": lambda d: d["baseline_estimate"].round(2),
                "p uji acak": lambda d: d["p_placebo"].round(3), "q": lambda d: d["q_fdr"].round(3)}),
                hide_index=True, **STRETCH)
        note("Periode pendek memberi rentang lebar. Rentang ini dikalibrasi dengan data acak karena galat baku biasa terlalu "
             "sempit pada periode pendek. Perbedaan antarperiode, bila ada, tidak membuktikan efek regulasi.")

    nav_link(PAGE["prediksi"], "Lanjut: apakah kurs membantu prediksi harga?", ":material/arrow_forward:")

footer("PIHPS (Bank Indonesia), FAOSTAT, BPS, UN Comtrade, Pink Sheet (Bank Dunia), Bapanas")
