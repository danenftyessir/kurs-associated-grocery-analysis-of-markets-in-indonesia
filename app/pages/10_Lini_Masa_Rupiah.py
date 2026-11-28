"""Halaman 10 -- Rupiah dari waktu ke waktu (D-175). Lini masa kurs JISDOR sejak awal periode analisis dengan 13 episode
pelemahan, lalu kipas episode per komoditas (perubahan harga nasional 0–12 minggu sesudah awal episode di atas pita 499
jendela tanpa episode) dan kipas semua komoditas. Hanya membaca artefak `drivers_weekly`, `episodes`, `events`."""

import numpy as np
import pandas as pd
import streamlit as st

from common import (CFG, PAGE, STRETCH, commodity_labels, fmt_num, footer, lead, nav_link, need, note, page_header,
                    picker, show_table)
from kagami.viz import plots
from kagami.viz.style import MONTHS, month_year

page_header("Rupiah dari waktu ke waktu")
H = 8


def _day(t) -> str:
    t = pd.Timestamp(t)
    return f"{t.day} {MONTHS[t.month - 1]} {t.year}"


got = need("drivers_weekly", "episodes", "events")
if got:
    labels = commodity_labels()
    start = pd.Timestamp(CFG.params["period"]["start"])
    dr = got["drivers_weekly"].dropna(subset=["log_e"]).copy()
    dr["week"] = pd.to_datetime(dr["week"])
    rate = np.exp(dr.loc[dr["week"] >= start, "log_e"])
    weeks = dr.loc[dr["week"] >= start, "week"]
    eps = got["episodes"].copy()
    eps["start_week"], eps["end_week"] = pd.to_datetime(eps["start_week"]), pd.to_datetime(eps["end_week"])
    eps["naik"] = 100 * np.expm1(eps["cum_dlog_e"])
    ev = got["events"]

    if len(rate) and len(eps):
        last, first = float(rate.iloc[-1]), float(rate.iloc[0])
        big = eps.loc[eps["naik"].idxmax()]
        weakest = last >= float(rate.max()) - 1e-6
        lead(f"Rupiah berada di Rp{fmt_num(last, 0)} per dolar AS pada {_day(weeks.iloc[-1])}"
             + (", titik terlemahnya sejak 2018. " if weakest else ". ")
             + f"Sejak awal 2018 rupiah melemah {fmt_num(100 * (last / first - 1), 0)}%. Kami menandai {len(eps)} episode "
             f"pelemahan, dengan pelemahan rupiah terbesar {fmt_num(float(big['naik']), 1)}% yang dimulai "
             f"{month_year(big['start_week'])}.")

    opts = [0] + list(eps["episode_id"])
    ep_name = {int(r.episode_id): f"{month_year(r.start_week)}, rupiah melemah {fmt_num(r.naik, 1)}%" for r in eps.itertuples()}
    hl = picker("Sorot satu episode", opts, "ep", format_func=lambda e: "Tidak ada" if e == 0 else ep_name.get(int(e), e),
                default=0, help="Episode yang dipilih ditebalkan di lini masa dan di kipas harga.")
    hl = None if hl == 0 else int(hl)
    st.plotly_chart(plots.fx_drivers(got["drivers_weekly"], eps, start=start, highlight=hl), **STRETCH)
    with st.expander(f"Daftar {len(eps)} episode pelemahan"):
        at = dr.set_index("week")["log_e"]

        def _rate(t):
            s = at[at.index <= t]
            return float(np.exp(s.iloc[-1])) if len(s) else np.nan

        show_table(pd.DataFrame({
            "Mulai": eps["start_week"].map(month_year), "Selesai": eps["end_week"].map(month_year),
            "Pelemahan rupiah (%)": eps["naik"].round(1),
            "Kurs di awal (Rp)": [round(_rate(t - pd.Timedelta(days=7))) for t in eps["start_week"]],
            "Kurs di akhir (Rp)": [round(_rate(t)) for t in eps["end_week"]]}))
        note("Episode dimulai saat rupiah melemah minimal 3% dalam 8 minggu. Pemicu yang berjarak 8 minggu atau kurang digabung "
             "menjadi satu episode.")

    st.markdown("## Harga setelah setiap episode")
    st.markdown("Setiap garis menunjukkan perubahan harga eceran nasional sejak awal satu episode pelemahan rupiah. Pita biru "
                "menunjukkan perubahan harga pada 499 jendela waktu tanpa episode dengan panjang yang sama. Garis yang tetap "
                "di dalam pita berarti harga tidak bergerak lebih jauh dari minggu-minggu biasa.")
    coms = [c for c in labels if c in set(ev.loc[ev["level"] == "national", "commodity"])]
    if coms:
        com = picker("Komoditas", coms, "com", format_func=labels.get)
        name = labels.get(com, com)
        st.plotly_chart(plots.episode_fan(ev, com, eps, name=name, highlight=hl), **STRETCH)
        e8 = ev[(ev["commodity"] == com) & (ev["level"] == "national") & (ev["horizon"] == H)].dropna(subset=["dlog_price"])
        if len(e8):
            inside = int(((e8["dlog_price"] >= e8["placebo_lo"]) & (e8["dlog_price"] <= e8["placebo_hi"])).sum())
            txt = (f"Pada minggu ke-{H}, harga {name.lower()} setelah {inside} dari {len(e8)} episode berada di dalam pita "
                   "jendela tanpa episode.")
            if hl is not None and (e8["episode_id"] == hl).any():
                r = e8[e8["episode_id"] == hl].iloc[0]
                txt += (f" Setelah episode {month_year(eps.set_index('episode_id').loc[hl, 'start_week'])}, harga "
                        f"{name.lower()} berubah {fmt_num(100 * np.expm1(r['dlog_price']), 2, sign=True)}% dalam {H} "
                        f"minggu.")
            st.markdown(txt)
        nat = ev[(ev["level"] == "national") & ev["horizon"].isin(CFG.params["lp"]["key_horizons"])]
        if len(nat) and "placebo_p" in nat:
            k, n = int((nat["placebo_p"] < 0.05).sum()), len(nat)
            note(f"Dari {n} kombinasi episode, komoditas, dan minggu ke-4, 8, atau 12, sebanyak {k} ({fmt_num(100 * k / n, 1)}%) "
                 "memiliki perubahan harga di luar 95% jendela tanpa episode"
                 + (", setara dengan yang diharapkan dari kebetulan (5%). " if k / n <= 0.07 else ". ")
                 + "Studi peristiwa ini deskriptif. Respons rata-rata per komoditas ada di halaman Respons harga.")

        st.markdown("## Semua komoditas sekaligus")
        st.plotly_chart(plots.episode_fan_grid(ev, labels), **STRETCH)
        nav_link(PAGE["respons"], "Lihat respons rata-rata per komoditas", ":material/show_chart:")

footer("JISDOR dan PIHPS (Bank Indonesia)")
