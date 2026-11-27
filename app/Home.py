"""Titik masuk app KAGAMI: python -m kagami app  (atau streamlit run app/Home.py).

Navigasi berkelompok (D-170): "Hasil penelitian" untuk juri dan pengguna di atas, "Lampiran teknis" (data, metode, riwayat
eksekusi) di bawah. url_path halaman lama dipertahankan agar tautan app daring tetap berlaku. Isi beranda ada di
pages/1_Beranda.py; berkas ini hanya memasang tema tambahan dan menu.
"""

import streamlit as st

from common import inject_style

st.set_page_config(page_title="KAGAMI", page_icon=":material/insights:", layout="wide")
inject_style()

PAGES = {
    "Hasil penelitian": [
        st.Page("pages/1_Beranda.py", title="Beranda", icon=":material/home:", default=True),
        st.Page("pages/2_Kepekaan_Harga_Regional.py", title="Kepekaan harga", icon=":material/show_chart:",
                url_path="Kepekaan_Harga_Regional"),
        st.Page("pages/3_Pola_Respons.py", title="Pola regional", icon=":material/map:", url_path="Pola_Respons"),
        st.Page("pages/4_Eksposur_dan_Nilai_Prediktif.py", title="Eksposur & prediksi", icon=":material/query_stats:",
                url_path="Eksposur_dan_Nilai_Prediktif"),
        st.Page("pages/5_Penjelajah_Skenario.py", title="Skenario rupiah", icon=":material/tune:",
                url_path="Penjelajah_Skenario"),
        st.Page("pages/6_Temuan_Penelitian.py", title="Temuan lengkap", icon=":material/article:",
                url_path="Temuan_Penelitian"),
    ],
    "Lampiran teknis": [
        st.Page("pages/8_Data_dan_Metode.py", title="Data & metode", icon=":material/dataset:", url_path="Data_dan_Metode"),
        st.Page("pages/7_Evaluasi_Eksekusi.py", title="Riwayat eksekusi", icon=":material/history:",
                url_path="Evaluasi_Eksekusi"),
    ],
}

st.navigation(PAGES).run()
