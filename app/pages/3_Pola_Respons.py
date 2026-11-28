"""Halaman 3 -- Perbedaan antarprovinsi (WP-31; D-171). Kalimat jawaban → komoditas dengan perbedaan antarprovinsi (vs data
acak) → apakah provinsi membentuk kelompok (silhouette vs batas data acak) → batas deteksi struktur tertanam."""

import pandas as pd
import streamlit as st

from common import (STRETCH, commodity_labels, fmt_num, footer, lead, load, names_list, need, note, page_header, show_table,
                    table, unit_names)
from kagami.evaluation.planted import DETECTION_RATE, detection_limit
from kagami.viz import plots

page_header("Perbedaan antarprovinsi")

got = need("heterogeneity", "cluster_selection", "clusters", "coassign", "planted_recovery")
if got:
    labels = commodity_labels()
    sel, planted, het = got["cluster_selection"], got["planted_recovery"], got["heterogeneity"]
    k_star = int(sel.loc[sel["accepted"], "k"].max()) if sel["accepted"].any() else 1
    det = detection_limit(planted)["delta_min"].dropna()
    q = het[(het["statistic"] == "Q")] if "statistic" in het else het
    rej = q[q["reject"].fillna(False).astype(bool)] if "reject" in q else q.iloc[0:0]
    lead((("Provinsi tidak membentuk kelompok dengan pola respons yang sama. " if k_star == 1 else
           f"Provinsi membentuk {k_star} kelompok yang lolos uji data acak. ")
          + (f"Perbedaan antarprovinsi yang lebih besar dari hasil kurs acak hanya muncul pada {names_list(rej['commodity'], labels)}."
             if len(rej) else "Tidak ada komoditas yang responsnya berbeda antarprovinsi melebihi hasil kurs acak.")))

    st.subheader("Komoditas dengan respons berbeda antarprovinsi")
    if {"statistic", "value", "commodity"} <= set(het.columns) and {"p_placebo", "q_fdr", "reject"} <= set(q.columns):
        qq = q.set_index("commodity").sort_values("q_fdr")
        tab = pd.DataFrame({"Komoditas": [labels.get(c, c) for c in qq.index],
                            "p uji acak": qq["p_placebo"].round(3).to_numpy(),
                            "Setelah koreksi 10 uji (q)": qq["q_fdr"].round(3).to_numpy(),
                            "Hasil": ["berbeda antarprovinsi" if r else "tidak terlihat"
                                      for r in qq["reject"].fillna(False).astype(bool)]})
        show_table(tab)
        note("Untuk setiap komoditas kami mengukur keragaman respons 8 minggu antarprovinsi, lalu membandingkannya dengan "
             "499 versi data yang urutan waktu kursnya digeser acak. p adalah porsi data acak yang keragamannya sama besar "
             "atau lebih besar. q mengoreksi p karena 10 komoditas diuji sekaligus (Benjamini–Hochberg). Kami menyebut "
             "respons berbeda antarprovinsi bila q paling tinggi 0,05.")
        wide = het.pivot_table(index="commodity", columns="statistic", values="value", aggfunc="first").reindex(qq.index)
        with st.expander("Statistik uji lengkap"):
            show_table(pd.DataFrame({"Komoditas": [labels.get(c, c) for c in qq.index],
                                     "Q (Cochran)": wide.get("Q"), "τ² (varians antarprovinsi)": wide.get("tau2"),
                                     "I²": wide.get("I2")}).round(3))
            note("τ² = 0 berarti data tidak cukup untuk membedakan provinsi, sehingga semua provinsi ditampilkan sama "
                 "dengan rata-rata nasional.")
    else:
        table(het, "Uji perbedaan antarprovinsi per komoditas", status=False)

    st.subheader("Pengelompokan provinsi")
    st.markdown("Kami mencoba mengelompokkan 34 provinsi menjadi 2 sampai 6 kelompok berdasarkan pola responsnya. Hasil "
                "pengelompokan hanya diterima bila kualitasnya melewati hasil terbaik dari data acak."
                + (" Tidak ada yang melewati batas itu." if k_star == 1 else ""))
    st.plotly_chart(plots.silhouette_threshold(sel), **STRETCH)

    st.subheader("Seberapa besar perbedaan yang akan tertangkap")
    if len(planted):
        p = planted.set_index(["delta", "k_true"])["recovery_rate"]
        lim = fmt_num(det.max(), 1) if len(det) else None
        low = [f"{fmt_num(100 * v, 0)}%" for (dl, _), v in p.items() if round(dl, 2) == 0.1]
        txt = ("Metode ini menemukan kelompok bila selisih responsnya cukup besar. Bila provinsi terbagi menjadi 2 atau 3 "
               "kelompok berukuran mirip yang "
               f"responsnya berselisih minimal {lim}% per 1% pelemahan rupiah, metode ini menemukannya pada sedikitnya "
               f"{fmt_num(100 * DETECTION_RATE, 0)}% percobaan." if lim else "")
        if low:
            txt += f" Selisih 0,1% hanya tertangkap pada {' dan '.join(low)} percobaan."
        st.markdown(txt)
    st.plotly_chart(plots.recovery_curve(planted, threshold=DETECTION_RATE), **STRETCH)
    note("Batas ini hanya berlaku untuk bentuk yang kami uji: 2 atau 3 kelompok berukuran hampir sama. Kelompok kecil, gradien "
         "geografis, atau perbedaan yang hanya muncul pada sebagian komoditas belum diuji.")
    keep = {"delta": "Selisih respons (%)", "k_true": "Jumlah kelompok buatan",
            "recovery_rate": "Porsi percobaan yang menemukan", "ari_mean": "Kemiripan dengan kelompok asli (ARI)"}
    table(planted[[c for c in keep if c in planted]].rename(columns=keep), "Lihat tabel", status=False)

    if k_star > 1:
        cl = got["clusters"]
        st.subheader("Kelompok provinsi")
        st.plotly_chart(plots.cluster_sizes(cl), **STRETCH)
        if cl.loc[cl["method"] == "ward", "weak"].any():
            st.warning("Ada kelompok dengan stabilitas rendah. Kelompok itu belum layak dibaca sebagai tipe kepekaan.")
        names = unit_names()
        ward = cl[cl["method"] == "ward"].assign(provinsi=lambda d: d["province_id"].astype(str).map(names))
        table(ward[["cluster", "provinsi", "jaccard", "weak"]].sort_values(["cluster", "provinsi"]).rename(
            columns={"cluster": "Kelompok", "provinsi": "Provinsi", "jaccard": "Stabilitas (Jaccard)", "weak": "Lemah"}),
              "Anggota kelompok", status=False)
        st.plotly_chart(plots.coassign_heatmap(got["coassign"]), **STRETCH)
        pc = load("partition_compare")
        if pc is not None:
            table(pc, "Kesesuaian dengan pembagian wilayah lain (ARI: 0 tidak berhubungan, 1 identik)", status=False)

footer("PIHPS (Bank Indonesia) dan JISDOR (Bank Indonesia)")
