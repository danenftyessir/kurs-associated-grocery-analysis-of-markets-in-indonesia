"""Halaman 3 -- Pola Respons (WP-31; PLAN.md §18: keputusan k vs plasebo + batas deteksi sebagai isi utama)."""

import streamlit as st

from common import STRETCH, commodity_labels, fmt_num, footer, load, need, page_header, table, unit_names
from kagami.evaluation.planted import DETECTION_RATE, detection_limit
from kagami.viz import plots

page_header("Pola Respons", "Apakah ada kelompok provinsi dengan pola serupa?")

got = need("heterogeneity", "cluster_selection", "clusters", "coassign", "planted_recovery")
if got:
    labels = commodity_labels()
    sel, planted, het = got["cluster_selection"], got["planted_recovery"], got["heterogeneity"]
    k_star = int(sel.loc[sel["accepted"], "k"].max()) if sel["accepted"].any() else 1
    det = detection_limit(planted)["delta_min"].dropna()
    q = het[(het["statistic"] == "Q")] if "statistic" in het else het
    rej = q[q["reject"].fillna(False).astype(bool)] if "reject" in q else q.iloc[0:0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Jumlah kelompok provinsi", f"k = {k_star}",
              help="k > 1 hanya diterima bila silhouette maksimum melewati persentil 95 plasebo.")
    c2.metric("Batas deteksi struktur", f"δ = {fmt_num(det.max(), 1)}" if len(det) else "tidak tercapai",
              help="Selisih respons terkecil (RMS per fitur) yang terdeteksi ≥ 80% bila ditanam pada derau plasebo, untuk "
                   "struktur sintetis 2–3 kelompok berukuran hampir sama dengan pusat berbentuk simpleks.")
    c3.metric("Komoditas dengan heterogenitas provinsi", f"{len(rej)} dari {q['commodity'].nunique()}",
              help="H0-Het ditolak (Q vs plasebo, q BH ≤ 0,05) pada h = 8.")
    if len(rej):
        st.caption("Heterogenitas terdeteksi: " + ", ".join(labels.get(c, c) for c in rej["commodity"]) +
                   ". Variasi antarprovinsi ada untuk komoditas ini, tetapi tidak membentuk kelompok provinsi bersama.")

    st.plotly_chart(plots.silhouette_threshold(sel), **STRETCH)
    if k_star == 1:
        st.info("k = 1: tidak ada struktur regional yang terdeteksi. Ini batas atas, bukan bukti bahwa provinsi seragam: "
                "struktur dengan selisih respons di bawah batas deteksi di bawah masih mungkin ada. Batas deteksi hanya berlaku "
                "untuk bentuk struktur yang diuji (2–3 kelompok berukuran hampir sama, pusat simpleks); bentuk lain, seperti "
                "kelompok kecil, gradien geografis, atau perbedaan pada sebagian komoditas saja, belum diuji.")
    st.plotly_chart(plots.recovery_curve(planted, threshold=DETECTION_RATE), **STRETCH)
    table(planted, "Lihat tabel batas deteksi", status=False)
    table(het, "Uji heterogenitas per komoditas (vs plasebo)", status=False)

    if k_star > 1:
        cl = got["clusters"]
        st.subheader("Klaster provinsi")
        st.plotly_chart(plots.cluster_sizes(cl), **STRETCH)
        if cl.loc[cl["method"] == "ward", "weak"].any():
            st.warning("Ada klaster dengan stabilitas rendah (pola lemah): jangan ditafsirkan sebagai tipe kepekaan.")
        names = unit_names()
        ward = cl[cl["method"] == "ward"].assign(provinsi=lambda d: d["province_id"].astype(str).map(names))
        table(ward[["cluster", "provinsi", "jaccard", "weak"]].sort_values(["cluster", "provinsi"]),
              "Anggota klaster", status=False)
        st.plotly_chart(plots.coassign_heatmap(got["coassign"]), **STRETCH)
        pc = load("partition_compare")
        if pc is not None:
            table(pc, "Kesesuaian klaster dengan pembagian lain (ARI; 0 = tak berhubungan, 1 = identik)", status=False)

footer("Turunan PIHPS (BI)", "fitur respons terstandardisasi", "2018-2026")
