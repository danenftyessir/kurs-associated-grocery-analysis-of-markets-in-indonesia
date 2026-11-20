"""Halaman 1 -- Ringkasan & Status Data. Jalankan: python -m kagami app  (atau streamlit run app/Home.py)."""

import pandas as pd
import streamlit as st

from common import CFG, footer, load, need, page_header

page_header("Ringkasan & Status Data", "Seberapa bisa dipercaya datanya?")

st.markdown(
    """
**KAGAMI** (*Kurs-Associated Grocery Analysis of Markets in Indonesia*; *kagami* = cermin) mengukur seberapa besar dan seberapa cepat harga eceran 10 komoditas pangan PIHPS di setiap
provinsi bergerak bersama IDR/USD dan harga dunia dalam rupiah, lalu menguji apakah perbedaannya bersumber
dari komoditas atau dari lokasi.

| Kode | Pertanyaan |
|---|---|
| RQ1 | Besar & kecepatan respons nasional per komoditas, menurut jalur eksposur |
| RQ2 | Porsi variasi dari komoditas vs provinsi; apakah provinsi membentuk kelompok stabil |
| RQ3 | Asimetri depresiasi vs apresiasi + batas deteksi |
| RQ4 | Karakteristik terukur yang berasosiasi dengan perbedaan respons |
| RQ5 | Apakah fitur kurs memperbaiki prediksi 4 & 8 minggu (out-of-sample) |
"""
)

st.subheader("Kesegaran sumber")
src = pd.DataFrame([{"sumber": k, "peran": v["role"], "cakupan": v["coverage"], "lisensi": v["license"]}
                    for k, v in CFG.sources.items()])
ck = load("checksums")
if ck is not None:
    src = src.merge(ck.groupby("source", as_index=False)["retrieved_at"].max(), left_on="sumber",
                    right_on="source", how="left").drop(columns="source")
    src["retrieved_at"] = src["retrieved_at"].fillna("menunggu rilis")
st.dataframe(src, hide_index=True, use_container_width=True)

st.subheader("Kelayakan seri & daya statistik")
got = need("eligibility", "mde")
if got:
    el = got["eligibility"]
    st.metric("Seri layak", f"{int(el['eligible'].sum())} / {len(el)}")
    st.dataframe(got["mde"], hide_index=True, use_container_width=True)
report = load("stage0_report")
if report:
    with st.expander("Laporan Tahap 0"):
        st.markdown(report)

footer("BI (JISDOR, PIHPS), Bank Dunia, FRED, FAOSTAT, BPS, Bapanas", "lihat tabel", "2018-01 s.d. pembekuan 2026-11-21")
