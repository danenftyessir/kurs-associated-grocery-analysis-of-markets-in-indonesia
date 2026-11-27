"""Halaman 8 -- Lampiran teknis: Data & metode (D-170). Isi teknis yang dulu ada di beranda (sumber, kelayakan, daya
deteksi, laporan Tahap 0, status artefak) dalam bahasa pembaca, tanpa path server dan tanpa kode internal."""

import pandas as pd
import streamlit as st

from common import CFG, LEVEL_LABELS, STRETCH, commodity_labels, footer, load, need, page_header, unit_names
from kagami.utils.env import artifact_status

page_header("Data & metode", "Dari mana datanya, seberapa layak, dan seberapa kecil efek yang bisa terdeteksi?")
labels, names = commodity_labels(), unit_names()

st.markdown("## Sumber data")
rows = [{"sumber": k, "penerbit": v.get("publisher", ""), "peran": v.get("role", ""), "cakupan": v.get("coverage", ""),
         "lisensi": v.get("license", ""), "ikut zip juri": bool(v.get("redistribute", False)),
         "opsional": bool(v.get("optional", False))} for k, v in CFG.sources.items()]
src = pd.DataFrame(rows)
ck = load("checksums")
if ck is not None and {"source", "retrieved_at"} <= set(ck.columns):
    src = src.merge(ck.groupby("source", as_index=False)["retrieved_at"].max().rename(
        columns={"source": "sumber", "retrieved_at": "diambil"}), on="sumber", how="left")
cols = [c for c in ("penerbit", "peran", "cakupan", "lisensi", "diambil", "ikut zip juri") if c in src]
st.dataframe(src.loc[~src["opsional"], cols], hide_index=True, **STRETCH)
st.caption("Data mentah tanpa hak redistribusi tidak ikut zip juri; yang dikirim adalah dataset turunan (izin BI mencakup "
           "redistribusi data turunan) dan sumber berlisensi terbuka.")
with st.expander("Sumber tambahan untuk eksplorasi prediksi (opsional, tidak dipakai uji utama)"):
    st.dataframe(src.loc[src["opsional"], cols], hide_index=True, **STRETCH)

got = need("eligibility", "mde")
if got:
    st.markdown("## Kelayakan seri")
    el = got["eligibility"]
    c1, c2 = st.columns([1, 3])
    c1.metric("Seri provinsi × komoditas layak", f"{int(el['eligible'].sum())} / {len(el)}")
    per = (el.groupby("commodity", as_index=False).agg(seri=("eligible", "size"), layak=("eligible", "sum"))
           .assign(komoditas=lambda d: d["commodity"].map(labels))[["komoditas", "seri", "layak"]])
    c2.dataframe(per, hide_index=True, **STRETCH)
    st.caption("Layak = porsi minggu tanpa pengamatan ≤ 20%, tidak ada celah > 8 minggu, dan setiap tahun ≥ 70% minggu "
               "teramati. Seri yang tidak layak tetap dilaporkan, tidak dibuang diam-diam.")

    st.markdown("## Seberapa kecil efek yang bisa terdeteksi (MDE)")
    mde = got["mde"].copy()
    mde["komoditas"] = mde["commodity"].map(labels)
    mde["tingkat"] = mde["level"].map(LEVEL_LABELS)
    if "unit" in mde:
        mde["unit"] = mde["unit"].astype(str).map(lambda u: names.get(u, u))
    show = {"komoditas": "Komoditas", "horizon": "h (minggu)", "mde_beta": "MDE respons kurs (β)",
            "mde_pt": "MDE rasio pass-through", "mde_asym_pt": "MDE asimetri (PT)"}
    nat = mde[mde["level"] == "national"]
    st.dataframe(nat[[c for c in show if c in nat]].rename(columns=show).round(3), hide_index=True, **STRETCH)
    st.caption("MDE = efek terkecil yang terdeteksi dengan α 0,05 dan daya 80%, dihitung sebelum estimasi dilihat. Contoh: "
               "MDE PT 0,5 berarti pass-through di bawah setengah tidak dapat dibedakan dari nol.")
    reg = mde[mde["level"] == "region"]
    if len(reg):
        with st.expander("MDE per wilayah"):
            cols_r = {"komoditas": "Komoditas", "unit": "Wilayah", **{k: v for k, v in show.items() if k != "komoditas"}}
            st.dataframe(reg[[c for c in cols_r if c in reg]].rename(columns=cols_r).round(3), hide_index=True, **STRETCH)

st.markdown("## Reproduksi")
st.markdown(
    "Tiga tingkat reproduksi: **A**, aplikasi ini dari hasil yang dikirim; **B**, semua tahap dari dataset turunan yang "
    "dikirim (`python -m kagami all`); **C**, unduh ulang data mentah dari sumbernya. Langkah lengkap ada di README §10. "
    "Setiap tahap mencatat log eksekusi dengan sidik jari data dan kode; lihat halaman Riwayat eksekusi.")
stat = artifact_status(CFG)
n_ok = int(stat["available"].sum()) if "available" in stat else 0
st.metric("Artefak hasil tersedia", f"{n_ok} / {len(stat)}")
with st.expander("Daftar artefak hasil"):
    keep = {"artifact": "artefak", "stage": "tahap", "wp": "paket kerja", "ship": "ikut zip juri", "available": "tersedia"}
    st.dataframe(stat[[c for c in keep if c in stat]].rename(columns=keep), hide_index=True, **STRETCH)
report = load("stage0_report")
if report:
    with st.expander("Laporan pemeriksaan data (Tahap 0)"):
        st.markdown(report)

footer("BI (JISDOR, PIHPS), Bank Dunia, FRED, FAOSTAT, BPS, Bapanas", "lihat tabel", "2018-01 s.d. pembekuan 2026-11-21")
