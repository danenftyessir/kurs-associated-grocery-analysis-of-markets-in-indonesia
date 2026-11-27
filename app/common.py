"""Utilitas bersama halaman Streamlit. Aplikasi HANYA membaca artefak; tidak ada estimasi saat runtime (D-010)."""

from __future__ import annotations

import importlib.util
import inspect
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if importlib.util.find_spec("kagami") is None:  # jalan tanpa `pip install -e .`: paket = folder src/ (D-024)
    _spec = importlib.util.spec_from_file_location("kagami", ROOT / "src" / "__init__.py",
                                                   submodule_search_locations=[str(ROOT / "src")])
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["kagami"] = _mod
    _spec.loader.exec_module(_mod)

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from kagami.utils.artifacts import ARTIFACTS  # noqa: E402
from kagami.utils.config import Config  # noqa: E402
from kagami.utils.io import ArtifactMissing, find_artifact, read_artifact  # noqa: E402
from kagami.viz import style as S  # noqa: E402

CFG = Config(root=ROOT)
CAUSAL_NOTE = S.CAUSAL_NOTE
DRIVER_LABELS, LEVEL_LABELS, MODEL_LABELS = S.DRIVER_LABELS, S.LEVEL_LABELS, S.MODEL_LABELS
fmt_num, fmt_interval = S.fmt_num, S.fmt_interval
# Lebar penuh: Streamlit baru memakai width="stretch" (use_container_width usang & akan dihapus); versi lama hanya
# mengenal use_container_width. Dipilih dari signature agar tetap aman bila versi berubah (pyproject: >= 1.57, D-170).
STRETCH = ({"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters
           else {"use_container_width": True})
# Path halaman (relatif app/) untuk tautan antarhalaman; router di app/Home.py.
PAGE = {"ringkasan": "pages/1_Beranda.py", "respons": "pages/2_Kepekaan_Harga_Regional.py",
        "wilayah": "pages/3_Pola_Respons.py", "faktor": "pages/4_Eksposur_dan_Nilai_Prediktif.py",
        "simulasi": "pages/5_Penjelajah_Skenario.py", "laporan": "pages/6_Temuan_Penelitian.py",
        "riwayat": "pages/7_Evaluasi_Eksekusi.py", "data": "pages/8_Data_dan_Metode.py", "prediksi": "pages/9_Prediksi.py"}


@st.cache_data(show_spinner=False)
def _read(name: str, path: str, stamp: tuple[int, int]) -> pd.DataFrame | str:
    # path & stamp (mtime_ns, size) hanya kunci cache: versi file baru (git pull di Streamlit Cloud) = entri baru.
    return read_artifact(CFG, name)


def load(name: str) -> pd.DataFrame | str | None:
    """Artefak atau None bila belum ada. Ketiadaan TIDAK di-cache (D-135): Streamlit Cloud menarik commit baru tanpa
    me-restart proses, jadi None yang di-cache sebelum artefak di-push akan bertahan sampai app di-reboot."""
    p = find_artifact(CFG, name)
    if p is None:
        return None
    st_ = p.stat()
    try:
        return _read(name, str(p), (st_.st_mtime_ns, st_.st_size))
    except ArtifactMissing:
        return None


@st.cache_data(show_spinner=False)
def load_geo() -> dict | None:
    """Geometri 34 provinsi (tabel referensi tim; © OpenStreetMap contributors, ODbL, via geoBoundaries). None bila tak ada."""
    p = CFG.reference_dir / "indonesia_provinces.geojson"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def need(*names: str) -> dict[str, pd.DataFrame] | None:
    """Muat artefak; bila ada yang belum tersedia tampilkan label 'menunggu hasil' dan kembalikan None."""
    out = {n: load(n) for n in names}
    missing = [n for n, v in out.items() if v is None]
    if missing:
        st.info("Menunggu hasil: " + ", ".join(f"`{n}` ({ARTIFACTS[n].wp})" for n in missing))
        return None
    return out


def page_header(title: str, lead_text: str | None = None) -> None:
    """Konfigurasi halaman + judul. Kalimat pembuka (jawaban halaman) bisa diberikan di sini atau, bila dihitung dari
    artefak, lewat `lead()` setelah artefak dimuat."""
    st.set_page_config(page_title=f"KAGAMI · {title}", layout="wide")
    st.title(title)
    if lead_text:
        lead(lead_text)


def lead(text: str) -> None:
    """Paragraf pembuka halaman: jawaban lebih dulu, kalimat biasa (D-171)."""
    st.markdown(f'<p class="kg-lead">{text}</p>', unsafe_allow_html=True)


def note(text: str) -> None:
    """Catatan kecil di bawah grafik/tabel (cara membaca, batas). Satu atau dua kalimat."""
    st.markdown(f'<p class="kg-note">{text}</p>', unsafe_allow_html=True)


# Lapisan tampilan bersama (D-170, D-171): tema dasar di .streamlit/config.toml (kertas terang, judul serif, biru palet
# viz.style); CSS ini hanya menambah yang tidak bisa diatur tema.
STYLE = """
<style>
::selection { background: rgba(42, 120, 214, .18); }
[data-testid="stMainBlockContainer"] { padding-top: 2.75rem; max-width: 1160px; }
[data-testid="stMetricValue"], [data-testid="stDataFrame"], .kg-num { font-variant-numeric: tabular-nums; }
h1 { letter-spacing: -0.015em; }
[data-testid="stMarkdownContainer"] > p, [data-testid="stMarkdownContainer"] > ol { max-width: 74ch; }
.kg-hero { padding: .25rem 0 .5rem; }
.kg-hero h1.kg-title { font-size: clamp(1.9rem, 3vw, 2.75rem); line-height: 1.14; letter-spacing: -0.02em;
  font-weight: 600; max-width: 31ch; margin: 0 0 .9rem; padding: 0; text-wrap: balance; }
.kg-title .kg-hl { color: #1c5cab; white-space: nowrap; }
.kg-byline { font-size: .92rem; margin: 0 0 1.6rem; opacity: .72; }
.kg-lead { font-size: 1.12rem; line-height: 1.6; max-width: 68ch; margin: 0 0 1.25rem; text-wrap: pretty; }
.kg-note { font-size: .86rem; line-height: 1.5; max-width: 76ch; opacity: .74; margin: .25rem 0 1rem; }
.kg-result { font-family: "Source Serif Pro", "Source Serif 4", Georgia, serif; font-size: 1.35rem; line-height: 1.35;
  font-weight: 600; max-width: 40ch; margin: .25rem 0 .4rem; }
.kg-result .kg-hl { color: #1c5cab; }
.kg-rq { font-family: "Source Serif Pro", "Source Serif 4", Georgia, serif; font-weight: 600; font-size: 1.05rem;
  line-height: 1.35; margin: 0; }
.kg-ans { font-size: 1rem; line-height: 1.58; margin: 0 0 .1rem; max-width: 66ch; }
.kg-rule { border-top: 1px solid rgba(31, 35, 40, .12); margin: 1rem 0; }
</style>
"""


def inject_style() -> None:
    """Pasang CSS bersama (dipanggil router app/Home.py sekali per run; berlaku untuk semua halaman)."""
    st.markdown(STYLE, unsafe_allow_html=True)


def nav_link(page: str, label: str, icon: str | None = None) -> None:
    """Tautan ke halaman lain lewat `st.page_link` (path relatif app/, mis. "pages/3_Pola_Respons.py"). Di luar router
    `st.navigation` (tes asap menjalankan halaman sendiri-sendiri) `st.page_link` tidak bisa menemukan halaman → teks biasa."""
    try:
        st.page_link(page, label=label, icon=icon)
    except Exception:  # noqa: BLE001 - hanya cadangan tampilan
        st.caption(label)


def footer(sources: str, period: str = "Januari 2018 sampai November 2026") -> None:
    st.caption(f"Sumber: {sources}. Periode: {period}. {CAUSAL_NOTE}")


def not_detected_badge(ci_low: float, ci_high: float) -> str:
    """'tidak terdeteksi' bila interval memuat nol; 'interval tidak tersedia' bila NaN (mis. PT wilayah)."""
    return S.detection_status(ci_low, ci_high)


def unit_names() -> dict[str, str]:
    """unit (province_id sebagai string / nama wilayah / ALL) → nama tampilan."""
    names = {str(k): v for k, v in CFG.regions.set_index("province_id")["province"].items()}
    return {**names, "ALL": "Nasional"}


def picker(label: str, options: list, key: str, format_func=str, default=None, container=None, radio: bool = False,
           help: str | None = None):
    """Selectbox/radio yang pilihannya disimpan di URL (`?key=nilai`) agar tampilan bisa dibagikan (PLAN.md §18.5)."""
    c = container or st
    opts = list(options)
    want = st.query_params.get(key)
    match = [o for o in opts if str(o) == want]
    idx = opts.index(match[0]) if match else (opts.index(default) if default in opts else 0)
    widget = c.radio if radio else c.selectbox
    kw = {"horizontal": True} if radio else {}
    val = widget(label, opts, index=idx, format_func=format_func, key=f"pick_{key}", help=help, **kw)
    st.query_params[key] = str(val)
    return val


def area_options(prof: pd.DataFrame, commodity: str | None = None) -> list[str]:
    """Pilihan wilayah untuk kurva respons: 'ALL' (nasional) lalu 7 wilayah yang punya estimasi. Provinsi tidak ikut:
    baris provinsi `profiles` adalah selisih dari rata-rata, ditampilkan di peta."""
    d = prof if commodity is None else prof[prof["commodity"] == commodity]
    regions = [r for r in CFG.regions["region"].drop_duplicates() if r in set(d.loc[d["level"] == "region", "unit"].astype(str))]
    return (["ALL"] if (d["level"] == "national").any() else []) + regions


def area_level(area: str) -> str:
    return "national" if area == "ALL" else "region"


def reset_button(keys: list[str]) -> None:
    """Kembalikan semua pilihan halaman ke default (hapus parameter URL & state widget)."""
    if st.button("Atur ulang pilihan"):
        for k in keys:
            st.query_params.pop(k, None)
            st.session_state.pop(f"pick_{k}", None)
        st.rerun()


def table(df: pd.DataFrame, label: str = "Lihat tabel", status: bool = True) -> None:
    """Tabel kembaran grafik (aksesibel) di dalam expander."""
    with st.expander(label):
        st.dataframe(with_status(df) if status else df, hide_index=True, **STRETCH)


def with_status(df: pd.DataFrame, lo: str = "ci_low", hi: str = "ci_high") -> pd.DataFrame:
    """Tambah kolom `status` (lencana 'tidak terdeteksi' bila interval memuat nol) untuk tabel estimasi; angka 3 desimal."""
    if df.empty or lo not in df or hi not in df:
        return df
    out = df.assign(status=[not_detected_badge(a, b) for a, b in zip(df[lo], df[hi])])
    num = out.select_dtypes("float").columns
    out[num] = out[num].round(3)
    return out


def frame(d: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """Tabel tampilan berlabel pembaca: {label: fungsi(d) -> kolom}. Kolom yang sumbernya tidak ada (artefak sebagian atau
    data uji sintetis) dilewati, bukan membuat halaman gagal."""
    out = {}
    for label, fn in spec.items():
        try:
            out[label] = list(fn(d))
        except (KeyError, AttributeError, TypeError, ValueError):
            continue
    return pd.DataFrame(out)


def intervals(lo: pd.Series, hi: pd.Series, digits: int = 2) -> list[str]:
    return [fmt_interval(a, b, digits) for a, b in zip(lo, hi)]


def commodity_labels() -> dict[str, str]:
    return {k: v["pihps_name"] for k, v in CFG.commodities.items()}


def names_list(coms, labels: dict | None = None) -> str:
    """'a', 'a dan b', 'a, b, dan c' dengan nama komoditas huruf kecil."""
    labels = labels or commodity_labels()
    items = [labels.get(c, c).lower() for c in coms]
    if not items:
        return "tidak ada komoditas"
    return items[0] if len(items) == 1 else (" dan ".join(items) if len(items) == 2
                                              else ", ".join(items[:-1]) + ", dan " + items[-1])


def fmt_rp(x: float, sign: bool = True) -> str:
    """Rupiah format Indonesia tanpa desimal: +Rp89, −Rp1.170."""
    if x is None or pd.isna(x):
        return "tidak tersedia"
    lead_ = S.MINUS if x < 0 else ("+" if sign and x > 0 else "")
    return f"{lead_}Rp{fmt_num(abs(x), 0)}"


_PRICE_ROW = re.compile(r"^\|\s*([^|(]+?)\s*\((kg|liter)\)\s*\|\s*([\d.]+)\s*\|")


def reference_prices() -> dict[str, tuple[float, str]]:
    """Harga acuan nasional per komoditas → (Rp, satuan) dari tabel batas Rupiah `results/findings.md` (median antarprovinsi
    dari rerata harga teramati 8 minggu s.d. 2026-11-16; satu sumber dengan findings, D-168). {} bila tabel tak ada."""
    md = load("findings")
    if not isinstance(md, str):
        return {}
    by_name = {v.lower(): k for k, v in commodity_labels().items()}
    out = {}
    for line in md.splitlines():
        m = _PRICE_ROW.match(line)
        if m and m.group(1).lower() in by_name:
            out[by_name[m.group(1).lower()]] = (float(m.group(3).replace(".", "")), m.group(2))
    return out
