"""Titik masuk app KAGAMI: python -m kagami app  (atau streamlit run app/Home.py).

Navigasi berkelompok (D-170, D-171, D-173): "Hasil penelitian" (satu pertanyaan per halaman, bahasa pembaca) di atas,
"Lampiran" (laporan lengkap untuk pembaca teknis, data & metode dengan rumus dan daftar istilah) di bawah. Riwayat eksekusi
adalah alat pengembang: hanya tampil bila env KAGAMI_DEV=1 (log tetap ikut paket juri, dibaca `python -m kagami runs`).
url_path halaman lama dipertahankan agar tautan app daring tetap berlaku. Berkas ini hanya memasang tema tambahan dan menu.
"""

import os

import streamlit as st

from common import inject_style

st.set_page_config(page_title="KAGAMI", page_icon=":material/insights:", layout="wide")
inject_style()

PAGES = {
    "Hasil penelitian": [
        st.Page("pages/1_Beranda.py", title="Ringkasan", icon=":material/home:", default=True),
        st.Page("pages/10_Lini_Masa_Rupiah.py", title="Rupiah dari waktu ke waktu", icon=":material/timeline:",
                url_path="Lini_Masa_Rupiah"),
        st.Page("pages/2_Kepekaan_Harga_Regional.py", title="Respons harga", icon=":material/show_chart:",
                url_path="Kepekaan_Harga_Regional"),
        st.Page("pages/11_Profil_Provinsi.py", title="Profil provinsi", icon=":material/location_on:",
                url_path="Profil_Provinsi"),
        st.Page("pages/3_Pola_Respons.py", title="Perbedaan antarprovinsi", icon=":material/map:", url_path="Pola_Respons"),
        st.Page("pages/4_Eksposur_dan_Nilai_Prediktif.py", title="Faktor penjelas", icon=":material/account_tree:",
                url_path="Eksposur_dan_Nilai_Prediktif"),
        st.Page("pages/9_Prediksi.py", title="Prediksi", icon=":material/query_stats:", url_path="Prediksi"),
        st.Page("pages/5_Penjelajah_Skenario.py", title="Simulasi rupiah", icon=":material/tune:",
                url_path="Penjelajah_Skenario"),
    ],
    "Lampiran": [
        st.Page("pages/8_Data_dan_Metode.py", title="Data & metode", icon=":material/dataset:", url_path="Data_dan_Metode"),
        st.Page("pages/6_Temuan_Penelitian.py", title="Laporan lengkap", icon=":material/article:",
                url_path="Temuan_Penelitian"),
    ],
}
if os.environ.get("KAGAMI_DEV", "").strip().lower() in {"1", "true", "yes", "on"}:   # alat pengembang (D-173)
    PAGES["Pengembang"] = [st.Page("pages/7_Evaluasi_Eksekusi.py", title="Riwayat eksekusi", icon=":material/history:",
                                   url_path="Evaluasi_Eksekusi")]

st.navigation(PAGES).run()
