"""Halaman 9 -- Kurs dan prediksi harga (Task 4, WP-27/31; D-171, dipisah dari halaman Faktor). Evaluasi bersyarat
rolling-origin: galat model dasar + kurs & harga dunia terhadap model dasar, uji Diebold–Mariano dengan arah (D-169), H5."""

import streamlit as st

from common import (MODEL_LABELS, PAGE, STRETCH, commodity_labels, fmt_num, footer, frame, lead, nav_link, need, note,
                    page_header, show_table)
from kagami.viz import plots, style

page_header("Kurs dan prediksi harga")
COLS = {"horizon": "Prediksi (minggu)", "model": "Model", "subset": "Titik prediksi", "commodity": "Komoditas",
        "region": "Wilayah", "level": "Tingkat", "mae": "MAE", "rmse": "RMSE", "mae_ratio_vs_m1": "MAE / model dasar",
        "rmse_ratio_vs_m1": "RMSE / model dasar", "dm_stat": "DM", "dm_p": "p", "dm_p_one_sided": "p satu sisi",
        "n_origins": "Jumlah titik", "n_nonoverlap": "Titik tidak tumpang tindih", "n_obs": "Jumlah baris",
        "h5_p_holm": "p Holm", "h5_reject": "Ditolak", "mae_full": "MAE dengan kurs",
        "mae_without_fx": "MAE tanpa fitur kurs", "delta_mae": "Selisih MAE"}

got = need("forecast_eval", "ablation")
if got:
    fe4, labels = got["forecast_eval"], commodity_labels()
    tot = fe4[(fe4["subset"] == "all") & (fe4["model"] == "M2") & (fe4["commodity"] == "ALL")]
    if "level" in tot:
        tot = tot[tot["level"] == "all"]
    tot = tot.sort_values("horizon")
    if len(tot):
        chg = " dan ".join(fmt_num(100 * (v - 1), 1, sign=True) + "%" for v in tot["mae_ratio_vs_m1"])
        hs = " dan ".join(str(int(h)) for h in tot["horizon"])
        worse, sig = (tot["mae_ratio_vs_m1"] > 1).all(), (tot["dm_p"] < 0.05).all()
        up = " dan ".join(fmt_num(100 * (v - 1), 1) + "%" for v in tot["mae_ratio_vs_m1"])
        lead((f"Menambahkan kurs dan harga dunia tidak membuat prediksi harga {hs} minggu lebih akurat. Galat rata-ratanya "
              f"justru naik {up}" + (", dan uji Diebold–Mariano menyatakan selisih itu nyata." if sig else ".")) if worse
             else f"Menambahkan kurs dan harga dunia mengubah galat prediksi {hs} minggu sebesar {chg}.")
    n = int(tot["n_origins"].max()) if len(tot) and "n_origins" in tot else None
    st.markdown("Kami melatih model hanya dengan data sebelum setiap titik prediksi, lalu memprediksi perubahan harga 4 dan "
                f"8 minggu ke depan{f' pada {n} titik prediksi' if n else ''}, setiap 4 minggu sejak Januari 2021. Model "
                "dasar memakai pola harga sendiri, musim, dan harga minyak Brent. Model pembanding menambahkan kurs rupiah "
                "dan harga dunia dalam rupiah. Kami memakai versi data terakhir karena riwayat revisi PIHPS tidak tersedia, "
                "jadi evaluasi ini pseudo-real-time.")

    if len(tot):
        cols = st.columns(len(tot))
        for col, r in zip(cols, tot.itertuples()):
            col.metric(f"Prediksi {int(r.horizon)} minggu", fmt_num(100 * (r.mae_ratio_vs_m1 - 1), 1, sign=True) + "%",
                       help="Perubahan galat absolut rata-rata (MAE) setelah kurs dan harga dunia ditambahkan ke model "
                            "dasar. Positif berarti prediksi lebih buruk.")
            col.caption(style.dm_summary(getattr(r, "dm_stat", float("nan")), r.dm_p,
                                         getattr(r, "dm_p_one_sided", None), model="model dengan kurs",
                                         ref="model dasar"))
        note("Tanda statistik DM menunjukkan arah: negatif berarti model dengan kurs kurang akurat. Pertanyaan penelitian "
             "menanyakan perbaikan, jadi p satu sisi yang relevan untuk klaim bahwa kurs membantu.")

    for subset in ("all", "large_move"):
        if (fe4["subset"] == subset).any():
            st.plotly_chart(plots.forecast_ratios(fe4, subset, labels=labels), **STRETCH)

    h5 = fe4[fe4["h5_p_holm"].notna()] if "h5_p_holm" in fe4 else fe4.iloc[0:0]
    if len(h5):
        st.subheader("Komoditas impor saat kurs bergerak besar")
        show_table(frame(h5, {
            "Kelompok": lambda d: d["commodity"].map(lambda c: style.PATH_LABELS.get(c, labels.get(c, c))),
            "Prediksi (minggu)": lambda d: d["horizon"].astype(int),
            "Galat relatif terhadap model dasar": lambda d: d["mae_ratio_vs_m1"].round(3),
            "DM": lambda d: d["dm_stat"].round(2), "p": lambda d: d["dm_p"].round(3),
            "p setelah koreksi Holm": lambda d: d["h5_p_holm"].round(3),
            "Titik prediksi": lambda d: d["n_origins"].astype(int)}))
        note("Uji ini kami daftarkan sebelum analisis: untuk komoditas impor langsung dan komoditas berbasis pakan impor, "
             "apakah kurs membantu prediksi 8 minggu saat kurs bergerak besar. Titik prediksi seperti itu sedikit, jadi "
             "daya ujinya lemah.")

    with st.expander("Tabel evaluasi lengkap"):
        full = fe4.assign(model=fe4["model"].map(lambda m: MODEL_LABELS.get(m, m)),
                          subset=fe4["subset"].map(lambda x: style.SUBSET_LABELS.get(x, x)),
                          commodity=fe4["commodity"].map(lambda c: "Semua komoditas" if c == "ALL"
                                                         else style.PATH_LABELS.get(c, labels.get(c, c))))
        show_table(full.rename(columns=COLS))
        ab = got["ablation"]
        if "commodity" in ab:
            ab = ab.assign(commodity=ab["commodity"].map(lambda c: "Semua komoditas" if c == "ALL"
                                                         else style.PATH_LABELS.get(c, labels.get(c, c))))
        if "subset" in ab:
            ab = ab.assign(subset=ab["subset"].map(lambda x: style.SUBSET_LABELS.get(x, x)))
        show_table(ab.rename(columns=COLS))
        note("Ablation adalah galat model dengan kurs tanpa fitur kurs dikurangi galat model dengan kurs. Nilai positif "
             "berarti fitur kurs mengurangi galat.")
    note("Eksplorasi lain sesudah praregistrasi, seperti klasifikasi arah harga dan model deep learning, ada di Laporan "
         "lengkap, Lampiran A. Hasilnya eksploratif dan tidak menguji hipotesis.")
    nav_link(PAGE["laporan"], "Buka laporan lengkap", ":material/article:")

footer("PIHPS (Bank Indonesia), JISDOR (Bank Indonesia), Pink Sheet (Bank Dunia), FRED", "Januari 2021 sampai November 2026")
