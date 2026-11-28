"""Halaman 12 -- Cerita data (D-178). Grafik editorial dalam satu halaman: (1) untuk satu komoditas, peta petak heksagon
34 provinsi harga terkini (skala satu warna dalam Rupiah) dan selisih respons kurs dari nasional (skala divergen); (2) peta
heksagon kecil 10 komoditas dengan skala sama; (3) matriks episode × komoditas (perubahan harga 8 minggu sesudah tiap
episode pelemahan rupiah dibanding rentang jendela tanpa episode). Heksagon berukuran sama agar provinsi kecil sama terlihatnya
dengan provinsi luas. Komoditas yang perbedaan antarprovinsinya tidak lolos uji plasebo (`heterogeneity`) digambar abu-abu;
garis tebal = deviasi yang lolos koreksi BH atas semua sel `province_calibrated` (sama dengan findings). Hanya membaca
artefak `profiles`, `heterogeneity`, `panel_weekly`, `episodes`, `events` (+ `province_calibrated`)."""

import numpy as np
import pandas as pd
import streamlit as st

from common import (CFG, PAGE, STRETCH, commodity_labels, fmt_num, footer, global_deviations, het_detected,
                    lead, load, load_hex, names_list, nav_link, need, note, page_header, picker, reference_prices,
                    unit_names)
from kagami.viz import plots
from kagami.viz.style import month_year

page_header("Cerita data")
H = 8
RECENT_WEEKS = 8           # harga terkini = harga teramati terakhir dalam 8 minggu terakhir panel
LEAD_COMMODITY = "beras"   # contoh harga di kalimat pembuka: pangan pokok yang dikenal semua pembaca


def _latest_prices(panel: pd.DataFrame, commodity: str) -> pd.DataFrame:
    d = panel[(panel["commodity"] == commodity)].dropna(subset=["price"]).copy()
    d["week"] = pd.to_datetime(d["week"])
    if d.empty:
        return pd.DataFrame(columns=["province_id", "price", "week"])
    d = d[d["week"] > d["week"].max() - pd.Timedelta(weeks=RECENT_WEEKS)]
    return d.sort_values("week").groupby("province_id", as_index=False).last()[["province_id", "price", "week"]]


def _move(v: float) -> str:
    """Perubahan dalam kata: "naik 0,05%", "turun 1,67%", "tidak berubah"."""
    if v is None or np.isnan(v):
        return "tidak tersedia"
    return "tidak berubah" if abs(v) < 0.005 else f"{'naik' if v > 0 else 'turun'} {fmt_num(abs(v), 2)}%"


def _join(items: list[str]) -> str:
    """Daftar nama diri tanpa mengubah huruf: 'a', 'a dan b', 'a, b, dan c'."""
    return items[0] if len(items) == 1 else (" dan ".join(items) if len(items) == 2
                                              else ", ".join(items[:-1]) + ", dan " + items[-1])


got = need("profiles", "heterogeneity", "panel_weekly", "episodes", "events")
hexes = load_hex()
if got and hexes is not None:
    labels, names = commodity_labels(), unit_names()
    short = dict(zip(hexes["province_id"], hexes["label"])) if "label" in hexes else {}
    regions = dict(zip(CFG.regions["province_id"], CFG.regions["region"]))
    units = {c: u for c, (_, u) in reference_prices().items()}
    prof, het = got["profiles"], got["heterogeneity"]
    detected = het_detected(het)
    dev = prof[(prof["level"] == "province") & (prof["driver"] == "e") & (prof["horizon"] == H)]
    if "shrunk" in dev:
        dev = dev[dev["shrunk"].fillna(False).astype(bool)]
    dev = dev.assign(province_id=pd.to_numeric(dev["unit"], errors="coerce")).dropna(subset=["province_id"])
    dev["province_id"] = dev["province_id"].astype(int)
    nat = prof[(prof["level"] == "national") & (prof["unit"].astype(str) == "ALL") & (prof["driver"] == "e")
               & (prof["horizon"] == H)].set_index("commodity")
    det_vals = dev.loc[dev["commodity"].isin(detected), "estimate"].abs()
    zmax = float(np.ceil(10 * det_vals.max()) / 10) if len(det_vals) else 1.0
    gd = global_deviations(load("province_calibrated"))
    flags = gd[(gd["q_global"] < 0.05) & (gd["driver"] == "e") & (gd["horizon"] == H)].copy()
    flags["province_id"] = pd.to_numeric(flags["unit"], errors="coerce")
    flags = flags.dropna(subset=["province_id"]).astype({"province_id": int})
    coms = [c for c in labels if c in set(dev["commodity"])]
    det_list = [c for c in coms if c in detected]

    lp0 = _latest_prices(got["panel_weekly"], LEAD_COMMODITY)
    text = "Harga eceran pangan berbeda jauh antarprovinsi."
    if len(lp0) >= 2:
        hi0, lo0 = lp0.loc[lp0["price"].idxmax()], lp0.loc[lp0["price"].idxmin()]
        text = (f"Harga eceran pangan berbeda jauh antarprovinsi. Beras termahal ada di "
                f"{names.get(str(int(hi0['province_id'])), '')} (Rp{fmt_num(float(hi0['price']), 0)} per kg) dan termurah di "
                f"{names.get(str(int(lo0['province_id'])), '')} (Rp{fmt_num(float(lo0['price']), 0)} per kg).")
    text += (f" Sebaliknya, perbedaan kepekaan harga terhadap rupiah antarprovinsi hanya terdeteksi pada "
             f"{names_list(det_list, labels)}." if det_list else
             " Sebaliknya, perbedaan kepekaan harga terhadap rupiah antarprovinsi tidak terdeteksi pada komoditas mana pun.")
    lead(text)

    st.markdown("## Harga berbeda jauh, kepekaan terhadap rupiah jarang berbeda")
    st.markdown(f"Kepekaan di halaman ini adalah perubahan harga (%) dalam {H} minggu setiap kali rupiah melemah 1%. Setiap "
                "heksagon adalah satu provinsi dengan ukuran yang sama, jadi DKI Jakarta sama terlihatnya dengan Papua. "
                "Susunannya mengikuti letak geografis secara kasar, dari Aceh di barat sampai Papua di timur.")
    default = det_list[0] if det_list else (coms[0] if coms else None)
    if default is not None:
        com = picker("Komoditas", coms, "com", format_func=labels.get, default=default)
        name, unit = labels.get(com, com), units.get(com, "kg")
        lp = _latest_prices(got["panel_weekly"], com)
        med = float(lp["price"].median()) if len(lp) else np.nan
        pv = lp.assign(value=lp["price"])
        pv["hover"] = [f"{names.get(str(p), p)}<br>Rp{fmt_num(v, 0)} per {unit}, {fmt_num(100 * (v / med - 1), 1, sign=True)}% "
                       "dari median" for p, v in zip(pv["province_id"], pv["price"])]
        call_p = []
        if len(lp):
            for r in (lp.loc[lp["price"].idxmax()], lp.loc[lp["price"].idxmin()]):
                pid = int(r["province_id"])
                call_p.append((pid, f"{short.get(pid, names.get(str(pid), pid))} Rp{fmt_num(float(r['price']), 0)}"))
        lo_p, hi_p = (float(lp["price"].quantile(q)) for q in (0.02, 0.98)) if len(lp) else (0.0, 1.0)
        st.plotly_chart(plots.hex_tile_map(
            pv, hexes, f"{name}: harga eceran terkini per {unit}",
            f"Harga teramati terakhir dalam {RECENT_WEEKS} minggu terakhir. Makin gelap makin mahal. Median 34 provinsi "
            f"Rp{fmt_num(med, 0)}.", zmin=lo_p, zmax=hi_p, scale=plots.S.SEQUENTIAL, legend=f"Rupiah per {unit}",
            tickformat=",.0f", regions=regions, callouts=call_p), **STRETCH)

        muted = com not in detected
        dv = dev[dev["commodity"] == com][["province_id", "estimate"]].rename(columns={"estimate": "value"})
        n_val = float(nat["estimate"].get(com, np.nan))
        n_zero = com in nat.index and nat.loc[com, "ci_low"] <= 0 <= nat.loc[com, "ci_high"]
        dv["hover"] = [f"{names.get(str(p), p)}<br>selisih dari nasional {fmt_num(v, 2, sign=True)} poin persen" for p, v in
                       zip(dv["province_id"], dv["value"])]
        fl = flags[flags["commodity"] == com][["province_id"]].merge(dv[["province_id", "value"]], on="province_id",
                                                                       how="left")
        call_r = [(int(p), f"{short.get(int(p), p)} {fmt_num(v, 2, sign=True)}") for p, v in zip(fl["province_id"], fl["value"])]
        st.plotly_chart(plots.hex_tile_map(
            dv, hexes, f"{name}: kepekaan tiap provinsi dibanding nasional",
            ("Semua provinsi diwarnai sama karena perbedaannya tidak lebih besar dari kebetulan. Angka per provinsi ada di "
             "keterangan kursor." if muted else
             "Selisih kepekaan provinsi dari angka nasional, dalam poin persen. Merah: harga naik lebih banyak atau turun "
             "lebih sedikit dari nasional saat rupiah melemah. Biru: sebaliknya. Garis tebal: tetap berbeda setelah koreksi "
             "banyak perbandingan."),
            zmax=zmax, legend="selisih dari nasional (poin persen)", muted=muted, regions=regions,
            flags=set(fl["province_id"]), callouts=call_r, height=None if not muted else 440), **STRETCH)
        if com in nat.index:
            lo, hi = float(nat.loc[com, "ci_low"]), float(nat.loc[com, "ci_high"])
            txt = (f"Secara nasional, harga {name.lower()} {_move(n_val)} setiap kali rupiah melemah 1%, dalam {H} minggu. "
                   f"Rentang 95%-nya dari {_move(lo)} sampai {_move(hi)}"
                   + (", jadi belum bisa dibedakan dari nol. " if n_zero else ". "))
        else:
            txt = ""
        if muted:
            txt += "Tidak ada provinsi yang kepekaannya berbeda dari angka nasional melebihi kebetulan."
        else:
            txt += ("Perbedaan antarprovinsi lebih besar dari kebetulan. "
                    + (f"{_join([names.get(str(p), str(p)) for p in fl['province_id']])} tetap berbeda dari nasional setelah "
                       "kami memperhitungkan banyaknya provinsi dan komoditas yang dibandingkan sekaligus." if len(fl) else
                       "Tetapi setelah kami memperhitungkan banyaknya provinsi dan komoditas yang dibandingkan sekaligus, tidak "
                       "ada satu provinsi pun yang tetap berbeda dari nasional."))
        st.markdown(txt)
        note("Angka per provinsi di peta sudah ditarik ke arah angka nasional, makin kuat bila data provinsinya kurang presisi, "
             "supaya provinsi dengan data sedikit tidak tampak ekstrem.")

    st.markdown("## Sepuluh komoditas, delapan tanpa perbedaan antarprovinsi yang terdeteksi")
    vals = dev[["commodity", "province_id", "estimate"]].rename(columns={"estimate": "value"})
    vals["hover"] = [f"{labels.get(c, c)}, {names.get(str(p), p)}<br>selisih dari nasional {fmt_num(v, 2, sign=True)} poin "
                     "persen" for c, p, v in zip(vals["commodity"], vals["province_id"], vals["value"])]
    st.plotly_chart(plots.hex_tile_grid(vals, hexes, {c: labels[c] for c in coms}, detected, zmax,
                                        "selisih dari nasional (poin persen)", flags[["commodity", "province_id"]]), **STRETCH)
    n_gray = len([c for c in coms if c not in detected])
    note(f"Untuk {n_gray} komoditas yang abu-abu, kepekaan nasional berlaku untuk semua provinsi sejauh yang bisa dideteksi "
         "data. Perbedaan yang lebih kecil dari batas deteksi tetap mungkin ada.")
    nav_link(PAGE["wilayah"], "Uji perbedaan antarprovinsi", ":material/map:")

    st.markdown("## Apa yang terjadi pada harga setelah rupiah melemah")
    eps, ev = got["episodes"], got["events"]
    n_win = CFG.params["inference"]["event_placebo_windows"]
    st.markdown(f"Kami membandingkan perubahan harga {H} minggu sesudah setiap episode pelemahan rupiah dengan rentang normal, "
                f"yaitu rentang 95% perubahan harga pada {n_win} periode tanpa episode dengan panjang yang sama.")
    st.plotly_chart(plots.episode_matrix(eps, ev, labels, horizon=H), **STRETCH)
    e8 = ev[(ev["level"] == "national") & (ev["horizon"] == H)].dropna(subset=["dlog_price"])
    pending = int((~eps["episode_id"].isin(e8["episode_id"])).sum())
    if len(e8):
        up = e8["dlog_price"] > e8["placebo_hi"]
        down = e8["dlog_price"] < e8["placebo_lo"]
        out = up | down
        per_com = e8.assign(out=out, up=up, down=down).groupby("commodity")[["out", "up", "down"]].sum()
        per_com = per_com.sort_values("out", ascending=False)
        epi = eps.set_index("episode_id")
        big_id = epi["cum_dlog_e"].idxmax()
        big_out = int(out[e8["episode_id"] == big_id].sum())
        expected = 0.05 * len(e8)
        txt = (f"Dari {len(e8)} pasangan episode dan komoditas, harga naik di luar rentang normal {int(up.sum())} kali dan "
               f"turun di luar rentang {int(down.sum())} kali. Bila tidak ada hubungan apa pun, sekitar {fmt_num(expected, 0)} "
               "kejadian seperti ini muncul karena kebetulan.")
        if out.sum() > expected:
            txt += (" Jumlahnya lebih banyak dari itu"
                    + (", tetapi lebih banyak yang turun daripada yang naik. Jadi pelemahan rupiah tidak diikuti kenaikan "
                       "harga yang seragam." if down.sum() > up.sum() else "."))
        txt += (f" Episode terbesar dimulai {month_year(epi.loc[big_id, 'start_week'])} saat rupiah melemah "
                f"{fmt_num(100 * np.expm1(float(epi.loc[big_id, 'cum_dlog_e'])), 1)}%, dan hanya {big_out} komoditas yang "
                "harganya keluar dari rentang normal sesudahnya.")
        if len(per_com) and per_com["out"].iloc[0] > 0:
            r = per_com.iloc[0]
            txt += (f" Komoditas yang paling sering keluar dari rentang adalah {labels.get(per_com.index[0], '').lower()}, "
                    f"{int(r['out'])} kali ({int(r['up'])} kali naik dan {int(r['down'])} kali turun).")
        if pending:
            txt += (f" Untuk episode terakhir, harga {H} minggu sesudahnya belum teramati." if pending == 1 else
                    f" Untuk {pending} episode terakhir, harga {H} minggu sesudahnya belum teramati.")
        st.markdown(txt)
    note("Episode disusun menurut waktu dengan jarak yang sama, jadi jarak antarkolom tidak menunjukkan lama waktu.")
    nav_link(PAGE["lini_masa"], "Lihat kurs dan kipas harga per episode", ":material/timeline:")
    nav_link(PAGE["provinsi"], "Lihat label harga di provinsi Anda", ":material/location_on:")
elif got:
    st.info("Tata letak heksagon provinsi belum tersedia.")

footer("PIHPS dan JISDOR (Bank Indonesia)")
