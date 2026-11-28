"""Halaman 11 -- Profil provinsi (D-175). Untuk satu provinsi: label harga 10 komoditas (harga terkini PIHPS, perubahan
setahun, rentang Rupiah untuk rupiah melemah x% = skenario PT(8) nasional resmi × harga provinsi), tren harga dibanding
median 34 provinsi, kelengkapan data, dan deviasi provinsi yang lolos koreksi BH global atas seluruh sel
`province_calibrated` (sama dengan findings: 7 deviasi). Deviasi lain tidak terdeteksi, jadi label memakai respons nasional.
Hanya membaca artefak; koreksi BH atas p yang tersimpan adalah penyajian, bukan estimasi ulang."""

import html

import numpy as np
import pandas as pd
import streamlit as st

from common import (CFG, PAGE, STRETCH, commodity_labels, fmt_num, fmt_rp, footer, lead, load, names_list, nav_link,
                    need, note, page_header, picker, reference_prices, show_table, unit_names)
from kagami.stats.meta import bh_fdr
from kagami.viz import plots
from kagami.viz.style import MONTHS

page_header("Profil provinsi")
H = 8
HIGH_PCT = 5.0          # batas atas skenario > 5% = batas tidak berguna (bawang, cabai), sama dengan tabel batas Rupiah findings


def _day(t) -> str:
    t = pd.Timestamp(t)
    return f"{t.day} {MONTHS[t.month - 1]} {t.year}"


def _bar(lo: float, hi: float) -> str:
    """Batang rentang Rupiah (SVG): garis abu-abu = skala simetris, biru = rentang, garis tegak = nol."""
    m = max(abs(lo), abs(hi), 1.0) * 1.15
    x = lambda v: 100 + v / m * 94
    return (f'<svg class="kg-tag-bar" viewBox="0 0 200 20" preserveAspectRatio="none" role="img" '
            f'aria-label="rentang {fmt_rp(lo)} sampai {fmt_rp(hi)}">'
            '<line x1="6" x2="194" y1="10" y2="10" stroke="#e1e0d9" stroke-width="6" stroke-linecap="round"/>'
            f'<line x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="10" y2="10" stroke="#2a78d6" stroke-width="6" '
            'stroke-linecap="round"/><line x1="100" x2="100" y1="2" y2="18" stroke="#5f5e5a" stroke-width="1.5"/></svg>')


def _deviations(pc: pd.DataFrame | None) -> pd.DataFrame:
    """Deviasi provinsi yang lolos koreksi BH global atas seluruh sel (konsisten dengan findings)."""
    if pc is None or pc.empty or "p_value" not in pc:
        return pd.DataFrame(columns=["commodity", "driver", "horizon", "unit", "estimate", "q_global"])
    pc = pc.assign(q_global=bh_fdr(pc["p_value"].to_numpy(dtype=float)))
    return pc


got = need("panel_weekly", "eligibility", "profiles")
if got:
    labels, names = commodity_labels(), unit_names()
    reg = CFG.regions.sort_values("province_id")
    c1, c2 = st.columns([2, 1])
    pid = picker("Provinsi", list(reg["province_id"]), "prov", format_func=lambda p: names.get(str(p), str(p)),
                 default=11, container=c1)
    shocks = CFG.params["scenario"]["shocks_pct"]
    x = picker("Rupiah melemah", shocks, "x", format_func=lambda v: f"{v}%", default=max(shocks), radio=True, container=c2)
    prov = names.get(str(pid), str(pid))

    panel = got["panel_weekly"]
    pw = panel[panel["province_id"] == pid].copy()
    pw["week"] = pd.to_datetime(pw["week"])
    el = got["eligibility"]
    elig = el[el["province_id"] == pid].set_index("commodity")["eligible"].astype(bool)
    prof = got["profiles"]
    pt = prof[(prof["level"] == "national") & (prof["unit"].astype(str) == "ALL") & (prof["driver"] == "PT")
              & (prof["horizon"] == H)].set_index("commodity")
    units = {c: u for c, (_, u) in reference_prices().items()}
    allpc = _deviations(load("province_calibrated"))
    dev = allpc[(allpc["unit"].astype(str) == str(pid)) & (allpc["q_global"] < 0.05)]

    coms = [c for c in labels if c in set(pw["commodity"])]
    n_ok = int(sum(bool(elig.get(c, False)) for c in coms))
    dev_coms = list(dict.fromkeys(dev["commodity"]))
    lead(f"Data harga {prov} cukup lengkap untuk {n_ok} dari {len(coms)} komoditas. "
         + (f"Respons harga di {prov} berbeda dari nasional pada {names_list(dev_coms, labels)}. Komoditas lain mengikuti "
            "respons nasional." if dev_coms else
            f"Respons harga di {prov} tidak berbeda dari nasional, jadi rentang di bawah memakai respons nasional."))

    cards = []
    for c in coms:
        s = pw[pw["commodity"] == c].dropna(subset=["price"]).sort_values("week")
        unit = units.get(c, "kg")
        head = f'<div class="kg-tag-name">{html.escape(labels.get(c, c))}, per {unit}</div>'
        if s.empty:
            cards.append(f'<div class="kg-tag">{head}<div class="kg-tag-muted">Belum ada harga teramati.</div></div>')
            continue
        last = s.iloc[-1]
        price, wk = float(last["price"]), last["week"]
        prev = s[s["week"] <= wk - pd.Timedelta(days=364)].tail(1)
        meta = f"Harga {_day(wk)}"
        if len(prev):
            chg = 100 * (price / float(prev["price"].iloc[0]) - 1)
            meta += f", {'naik' if chg >= 0 else 'turun'} {fmt_num(abs(chg), 1)}% dari setahun sebelumnya"
        body = f'{head}<div class="kg-tag-price">Rp{fmt_num(price, 0)}</div><div class="kg-tag-meta">{meta}</div>'
        if not bool(elig.get(c, False)):
            body += '<div class="kg-tag-muted">Data provinsi ini kurang lengkap untuk komoditas ini, jadi rentang tidak dihitung.</div>'
        elif c in pt.index and pd.notna(pt.loc[c, "ci_low"]):
            lo_p, hi_p = (plots.scenario_change(float(pt.loc[c, k]), x) for k in ("ci_low", "ci_high"))
            lo, hi = price * lo_p / 100, price * hi_p / 100
            body += (_bar(lo, hi) + f'<div class="kg-tag-range"><span>{fmt_rp(lo)}</span><span>{fmt_rp(hi)}</span></div>')
            if hi_p > HIGH_PCT:
                body += '<div class="kg-tag-muted">Rentang lebar karena data nasional komoditas ini kurang presisi.</div>'
        for r in dev[dev["commodity"] == c].itertuples():
            drv = "kurs" if r.driver == "e" else "harga dunia"
            body += (f'<div class="kg-tag-flag">Respons terhadap {drv} pada minggu ke-{int(r.horizon)} '
                     f'{"lebih tinggi" if r.estimate > 0 else "lebih rendah"} dari nasional '
                     f'({fmt_num(r.estimate, 2, sign=True)}).</div>')
        cards.append(f'<div class="kg-tag">{body}</div>')
    st.markdown(f'<div class="kg-tags">{"".join(cards)}</div>', unsafe_allow_html=True)
    note(f"Rentang biru adalah perubahan harga {H} minggu yang sejalan dengan pelemahan rupiah {x}% menurut pola historis "
         f"nasional, dihitung dari penerusan kurs nasional resmi dan harga terkini di {prov}. Ini skenario bersyarat, bukan "
         "ramalan. Kenaikan yang lebih besar dari ujung kanan rentang tidak sejalan dengan pola kurs historis dan perlu "
         "ditelusuri ke faktor lain, seperti pasokan, musim, atau kebijakan.")

    st.markdown("## Tren harga")
    if coms:
        com = picker("Komoditas", coms, "com", format_func=labels.get)
        st.plotly_chart(plots.price_trend(panel, pid, com, load("episodes"), name=labels.get(com, com), where=prov,
                                          unit=units.get(com, "kg")), **STRETCH)

    st.markdown("## Kelengkapan data")
    st.plotly_chart(plots.status_share(pw, labels, title=f"Kelengkapan data mingguan di {prov}"), **STRETCH)

    if not allpc.empty:
        rows = allpc[(allpc["unit"].astype(str) == str(pid)) & (allpc["horizon"] == H)].copy()
        if len(rows):
            with st.expander(f"Rincian perbedaan dari nasional, minggu ke-{H}"):
                show_table(pd.DataFrame({
                    "Komoditas": rows["commodity"].map(lambda c: labels.get(c, c)),
                    "Dibandingkan dengan": rows["driver"].map({"e": "kurs rupiah", "w": "harga dunia"}),
                    "Selisih dari nasional": rows["estimate"].round(2),
                    "Rentang 95% terkalibrasi": [f"{fmt_num(a, 2, sign=True)} s.d. {fmt_num(b, 2, sign=True)}"
                                                 for a, b in zip(rows["ci_low"], rows["ci_high"])],
                    "q (koreksi semua sel)": rows["q_global"].round(3),
                    "Kesimpulan": np.where(rows["q_global"] < 0.05, "berbeda dari nasional", "sama dengan nasional")}))
                note(f"Kami mengoreksi nilai p untuk semua {len(allpc)} kombinasi provinsi, komoditas, penggerak, dan minggu "
                     "sekaligus. Hanya selisih dengan q di bawah 0,05 yang kami sebut berbeda dari nasional.")
    nav_link(PAGE["wilayah"], "Lihat perbedaan antarprovinsi untuk semua komoditas", ":material/map:")

footer("PIHPS dan JISDOR (Bank Indonesia)")
