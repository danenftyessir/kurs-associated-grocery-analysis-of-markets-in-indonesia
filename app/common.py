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

from kagami.stats.meta import bh_fdr  # noqa: E402
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
        "riwayat": "pages/7_Evaluasi_Eksekusi.py", "data": "pages/8_Data_dan_Metode.py", "prediksi": "pages/9_Prediksi.py",
        "lini_masa": "pages/10_Lini_Masa_Rupiah.py", "provinsi": "pages/11_Profil_Provinsi.py",
        "cerita": "pages/12_Cerita_Data.py"}


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


_MOBILE_UA = re.compile(r"Mobi|Android|iPhone|iPad")


def chart_wrap() -> None:
    """Browser ponsel (User-Agent) → judul grafik dibungkus 34 karakter, subjudul 50; selain itu judul satu baris,
    subjudul 72 karakter. Berlaku untuk thread skrip sesi ini saja (`viz.style.WRAP`, D-172)."""
    try:
        ua = st.context.headers.get("User-Agent", "") or ""
    except Exception:  # noqa: BLE001 - di luar server (tes) tidak ada header
        ua = ""
    S.set_wrap(*((34, 50) if _MOBILE_UA.search(ua) else (None, 72)))


def page_header(title: str, lead_text: str | None = None) -> None:
    """Konfigurasi halaman + judul. Kalimat pembuka (jawaban halaman) bisa diberikan di sini atau, bila dihitung dari
    artefak, lewat `lead()` setelah artefak dimuat."""
    chart_wrap()
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


# Kode internal keputusan/isu/paket kerja (D-129, U109, WP-31). Teks yang ditampilkan apa adanya dari berkas (findings.md,
# laporan Tahap 0, catatan sumber, interpretasi log) dibersihkan saat tampil; isi berkas tidak berubah (D-172).
_CODE = r"(?:D-\d{3}[a-z]?|U\d{1,3}|WP-\d{2}(?:/(?:WP-)?\d{2})?)"
_CODES = rf"{_CODE}(?:[ \t]*(?:,|;|/|dan|s\.d\.|–)[ \t]*\n?[ \t]*{_CODE})*"
# Kalimat yang memakai kode sebagai subjek: ganti dengan frasa, bukan dihapus.
_CODE_SUBJECTS = [(re.compile(r"\(D-139, D-141,\s*D-142 menilai"), "(eksplorasi awal menilai")]


def _drop_code_columns(md: str) -> str:
    """Tabel markdown yang satu kolomnya hanya berisi kode (mis. kolom "Pembukaan": D-145, D-146, ...) → kolom dibuang."""
    lines, out, i = md.split("\n"), [], 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            j += 1
        rows = [ln.strip().strip("|").split("|") for ln in lines[i:j]]
        body = rows[2:]
        drop = {c for c in range(len(rows[0])) if body and all(
            c < len(r) and re.fullmatch(rf"\s*(?:{_CODES})?\s*", r[c]) for r in body)
            and any(re.search(_CODE, r[c]) for r in body if c < len(r))}
        if drop:
            out.extend("|" + "|".join(x for k, x in enumerate(r) if k not in drop) + "|" for r in rows)
        else:
            out.extend(lines[i:j])
        i = j
    return "\n".join(out)


def plain_text(text: str) -> str:
    """Buang kode internal dari teks tampilan: "(D-129)" dan "(D-139 s.d. D-167)" hilang, "(USD, D-019)" → "(USD)",
    "(D-155; FAQ ...)" → "(FAQ ...)", "real-time, D-162; ..." → "real-time; ...", kolom tabel berisi kode dibuang, sisa kode
    lepas dibuang."""
    s = str(text)
    for pat, rep in _CODE_SUBJECTS:
        s = pat.sub(rep, s)
    s = _drop_code_columns(s)
    s = re.sub(rf"[ \t]*\({_CODES}\)", "", s)
    s = re.sub(rf"[ \t]*[,;][ \t]*{_CODES}(?=[ \t]*\))", "", s)
    s = re.sub(rf"\({_CODES}[ \t]*[,;:][ \t]*", "(", s)
    s = re.sub(rf"[ \t]*,[ \t]*{_CODES}(?=[ \t]*[;,.])", "", s)
    return re.sub(rf"[ \t]*\b{_CODES}\b", "", s)


_NEXT_WORD = re.compile(r"[ \t]*\n?[ \t]*([A-Za-zÀ-ÿ]{2,})\b")


def soften_semicolons(md: str) -> str:
    """Titik koma yang memisahkan dua klausa prosa → titik + huruf kapital (di luar kurung) atau koma (di dalam kurung).
    Titik koma di antara angka berdesimal koma ("DM −1,90; p 0,062"), di tabel, di blok kode, atau sebelum simbol/kode
    dibiarkan karena di sana titik koma mencegah salah baca angka (D-172)."""
    out, depth, tick, fence, table = [], 0, False, False, False
    i, n = 0, len(md)
    while i < n:
        ch = md[i]
        if i == 0 or md[i - 1] == "\n":
            j = md.find("\n", i)
            line = md[i: n if j < 0 else j].lstrip()
            table = line.startswith("|")
            fence = (not fence) if line.startswith("```") else fence
            if not line:
                depth, tick = 0, False
        if table or fence:
            out.append(ch)
            i += 1
            continue
        if ch == "`":
            tick = not tick
        elif not tick and ch == "(":
            depth += 1
        elif not tick and ch == ")":
            depth = max(0, depth - 1)
        elif not tick and ch == ";":
            m = _NEXT_WORD.match(md, i + 1)
            prev = md[i - 1] if i else ""
            if m and depth == 0:
                w = m.group(1)
                out.append("." + md[i + 1: m.start(1)] + w[0].upper() + w[1:])
                i = m.end(1)
                continue
            if m and prev.isalpha():
                out.append(",")
                i += 1
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def readable(md: str) -> str:
    """Teks berkas untuk tampilan: tanpa kode internal, titik koma prosa dilunakkan."""
    return soften_semicolons(plain_text(md))


# Notasi di findings.md → LaTeX inline ($...$, dirender KaTeX oleh st.markdown) agar rumus terbaca sebagai rumus (D-173).
# Urutan penting: rumus utuh lebih dulu, lalu simbol tunggal. Teks di dalam `kode` atau $...$ tidak disentuh.
_MATH_RULES = [
    (r"PT\(h\) = β_e\(h\)/γ\(h\)", lambda m: r"$PT(h) = \beta_e(h)/\gamma(h)$"),
    (r"exp\(PT\((\w+)\) · ln 1,05\) − 1", lambda m: rf"$\exp(PT({m.group(1)}) \cdot \ln 1{{,}}05) - 1$"),
    (r"estimasi ± crit·SE", lambda m: r"estimasi $\pm\, \mathrm{crit} \cdot SE$"),
    (r"crit = max\(1,96, kuantil plasebo\)", lambda m: r"$\mathrm{crit} = \max(1{,}96;\ \text{kuantil plasebo})$"),
    (r"±1,96·SE", lambda m: r"$\pm 1{,}96 \cdot SE$"),
    (r"ln\(1 \+ jarak ke hub terdekat\)", lambda m: r"$\ln(1 + \text{jarak ke hub terdekat})$"),
    (r"Δe × Z\(r\)", lambda m: r"$\Delta e \times Z(r)$"),
    (r"β⁺ − β⁻", lambda m: r"$\beta^{+} - \beta^{-}$"),
    (r"τ-b", lambda m: r"$\tau_b$"),
    (r"β_e & ω", lambda m: r"$\beta_e$ dan $\omega$"),
    (r"β_e\((\w+)\)", lambda m: rf"$\beta_e({m.group(1)})$"),
    (r"ω\((\w+)\)", lambda m: rf"$\omega({m.group(1)})$"),
    (r"γ\((\w+)\)", lambda m: rf"$\gamma({m.group(1)})$"),
    (r"τ²", lambda m: r"$\tau^2$"),
    (r"(?<![\w])I²", lambda m: r"$I^2$"),
    (r"(?<![\w])β(?![\w⁺⁻(])", lambda m: r"$\beta$"),
    (r"(?<![\w])ω(?![\w(])", lambda m: r"$\omega$"),
]
_PROTECT = re.compile(r"(`[^`\n]*`|\$[^$\n]+\$)")


def math_text(md: str) -> str:
    """Notasi statistik di teks berkas → LaTeX inline: PT(h) = β_e(h)/γ(h), ±1,96·SE, exp(PT(8) · ln 1,05) − 1, β_e(4),
    ω(8), τ², I², β. Teks dalam `kode` dan rumus $...$ yang sudah ada dibiarkan."""
    for pat, rep in _MATH_RULES:
        parts = _PROTECT.split(md)
        md = "".join(p if i % 2 else re.sub(pat, rep, p) for i, p in enumerate(parts))
    return md


# Nama berkas hasil & kolom di findings.md (`profiles`, `rice_sufficiency`, ...) → nama yang dimengerti pembaca (D-173).
PLAIN_NAMES = {
    "profiles": "profil respons", "robustness": "uji ketahanan", "assoc": "uji asosiasi", "asymmetry": "uji asimetri",
    "regime_profiles": "respons per periode regulasi", "province_calibrated": "deviasi provinsi terkalibrasi",
    "national_calibrated": "rentang nasional terkalibrasi", "planted_recovery": "uji struktur buatan",
    "placebo_stats": "hasil data acak", "partition_compare": "perbandingan pengelompokan",
    "heterogeneity": "uji keragaman antarprovinsi", "cluster_selection": "pemilihan jumlah kelompok",
    "forecast_eval": "evaluasi prediksi", "forecast_preds": "prediksi per titik", "panel_weekly": "panel harga mingguan",
    "mde": "efek terkecil yang dapat dideteksi", "exposure": "tabel eksposur impor", "events": "studi peristiwa",
    "episodes": "episode pelemahan rupiah", "eligibility": "kelayakan seri", "direction_preds": "prediksi arah",
    "direction_tuned_preds": "prediksi arah teroptimasi", "deep_preds": "prediksi model deep learning",
    "rice_sufficiency": "kecukupan produksi beras", "n_kota": "jumlah kota sampel PIHPS",
    "ln_dist_hub": "jarak ke hub logistik (ln km)", "source": "kolom sumber", "available_at": "waktu data tersedia",
    "episode": "penanda episode",
}


def plain_names(md: str) -> str:
    """`nama_berkas` atau `nama_kolom` yang dikenal → nama pembaca tanpa format kode. Path, perintah, dan hash tetap kode."""
    return re.sub(r"`([^`\n]+)`", lambda m: PLAIN_NAMES.get(m.group(1), m.group(0)), md)


def verdicts(lo, hi, pos: str = "naik", neg: str = "turun", zero: str = "belum terlihat") -> list[str]:
    """Kesimpulan per baris dari rentang 95%: `pos` bila seluruh rentang di atas nol, `neg` bila di bawah nol, `zero`
    bila memuat nol (respons belum bisa dibedakan dari tanpa respons)."""
    out = []
    for a, b in zip(lo, hi):
        out.append("rentang tidak tersedia" if pd.isna(a) or pd.isna(b) else pos if a > 0 else neg if b < 0 else zero)
    return out


def fmt_frame(df: pd.DataFrame, digits: dict | None = None) -> pd.DataFrame:
    """Salinan tabel dengan angka format Indonesia (desimal koma, ribuan titik, minus tipografis) dan ya/tidak untuk
    boolean. Desimal per kolom dari `digits`, selain itu dibaca dari angkanya (paling banyak 3)."""
    out = df.copy()
    for c in out.columns:
        s = out[c]
        if pd.api.types.is_bool_dtype(s):
            out[c] = s.map({True: "ya", False: "tidak"})
        elif pd.api.types.is_float_dtype(s):
            d = (digits or {}).get(c)
            if d is None:
                v = s.dropna().to_numpy(dtype=float)
                d = next((k for k in range(4) if len(v) and (abs(v - v.round(k)) < 1e-9).all()), 3 if len(v) else 2)
            out[c] = [fmt_num(float(x), d) if pd.notna(x) else "–" for x in s]
        elif pd.api.types.is_integer_dtype(s):
            out[c] = ["–" if pd.isna(x) else fmt_num(float(x), 0) if abs(x) >= 10000 else str(int(x)) for x in s]
    return out


def show_table(df: pd.DataFrame, digits: dict | None = None, **kw) -> None:
    """`st.dataframe` lebar penuh tanpa indeks dengan angka format Indonesia (`fmt_frame`)."""
    st.dataframe(fmt_frame(df, digits), hide_index=True, **STRETCH, **kw)


# Lapisan tampilan bersama (D-170, D-171): tema dasar di .streamlit/config.toml (kertas terang, judul serif, biru palet
# viz.style); CSS ini hanya menambah yang tidak bisa diatur tema.
STYLE = """
<style>
::selection { background: rgba(42, 120, 214, .18); }
[data-testid="stMainBlockContainer"] { padding-top: 2.75rem; max-width: 1160px; }
.katex-display { overflow-x: auto; overflow-y: hidden; padding: .25rem 0; }
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
.kg-tags { display: grid; grid-template-columns: repeat(auto-fill, minmax(232px, 1fr)); gap: 12px; margin: .5rem 0 1rem; }
.kg-tag { border: 1px solid rgba(31, 35, 40, .14); border-radius: 10px; padding: .85rem .95rem .8rem; background: #fff; }
.kg-tag-name { font-size: .86rem; margin: 0; opacity: .78; }
.kg-tag-price { font-family: "Source Serif Pro", "Source Serif 4", Georgia, serif; font-size: 1.6rem; font-weight: 600;
  line-height: 1.2; margin: .1rem 0 .1rem; font-variant-numeric: tabular-nums lining-nums; }
.kg-tag-meta { font-size: .8rem; opacity: .7; margin: 0 0 .55rem; }
.kg-tag-bar { display: block; width: 100%; height: 20px; }
.kg-tag-range { display: flex; justify-content: space-between; font-size: .8rem; font-variant-numeric: tabular-nums;
  margin: .1rem 0 0; }
.kg-tag-flag { font-size: .78rem; line-height: 1.35; margin: .5rem 0 0; padding: .3rem .5rem; border-radius: 6px;
  background: #faeeda; color: #633806; }
.kg-tag-muted { font-size: .8rem; opacity: .7; margin: .4rem 0 0; }
</style>
"""


def inject_style() -> None:
    """Pasang CSS bersama dan lebar bungkus judul grafik (dipanggil router app/Home.py sekali per run; berlaku untuk
    semua halaman, termasuk Ringkasan yang tidak memakai `page_header`)."""
    chart_wrap()
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
    """Tabel kembaran grafik (aksesibel) di dalam expander, angka format Indonesia."""
    with st.expander(label):
        show_table(with_status(df) if status else df)


def with_status(df: pd.DataFrame, lo: str = "ci_low", hi: str = "ci_high") -> pd.DataFrame:
    """Tambah kolom Kesimpulan (naik / turun / belum terlihat dari rentang 95%) untuk tabel estimasi; angka 3 desimal."""
    if df.empty or lo not in df or hi not in df:
        return df
    out = df.assign(Kesimpulan=verdicts(df[lo], df[hi]))
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


@st.cache_data(show_spinner=False)
def load_hex() -> pd.DataFrame | None:
    """Tata letak petak heksagon 34 provinsi (tabel referensi tim `province_hex.csv`: kode ISO 3166-2, kolom, baris)."""
    p = CFG.reference_dir / "province_hex.csv"
    return pd.read_csv(p) if p.exists() else None


def global_deviations(pc: pd.DataFrame | None) -> pd.DataFrame:
    """Deviasi provinsi `province_calibrated` + q_global = koreksi BH atas SELURUH sel (konsisten dengan findings: 7
    deviasi lolos). Penyajian atas p yang tersimpan, bukan estimasi ulang (D-175)."""
    if pc is None or not isinstance(pc, pd.DataFrame) or pc.empty or "p_value" not in pc:
        return pd.DataFrame(columns=["commodity", "driver", "horizon", "unit", "estimate", "q_global"])
    return pc.assign(q_global=bh_fdr(pc["p_value"].to_numpy(dtype=float)))


def het_detected(het: pd.DataFrame | None) -> set[str]:
    """Komoditas yang perbedaan respons antarprovinsinya lolos uji plasebo (statistik Q di artefak `heterogeneity`):
    kolom `reject` bila ada, selain itu q BH ≤ `inference.fdr_q`."""
    if het is None or not isinstance(het, pd.DataFrame) or het.empty:
        return set()
    q = het[het["statistic"] == "Q"]
    rej = (q["reject"].fillna(False).astype(bool) if "reject" in q
           else q["q_fdr"] <= CFG.params["inference"]["fdr_q"])
    return set(q.loc[rej, "commodity"])
