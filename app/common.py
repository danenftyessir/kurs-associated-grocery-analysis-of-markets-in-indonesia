"""Utilitas bersama halaman Streamlit. Aplikasi HANYA membaca artefak; tidak ada estimasi saat runtime (D-010)."""

from __future__ import annotations

import importlib.util
import inspect
import json
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
CAUSAL_NOTE = "Asosiasi historis, bukan kausalitas. Bukan ramalan."
DRIVER_LABELS, LEVEL_LABELS, MODEL_LABELS = S.DRIVER_LABELS, S.LEVEL_LABELS, S.MODEL_LABELS
fmt_num, fmt_interval = S.fmt_num, S.fmt_interval
# Lebar penuh: Streamlit baru memakai width="stretch" (use_container_width usang & akan dihapus); versi lama hanya
# mengenal use_container_width. Dipilih dari signature agar app jalan di versi mana pun >= 1.35 (pyproject).
STRETCH = ({"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters
           else {"use_container_width": True})


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


def page_header(title: str, question: str) -> None:
    st.set_page_config(page_title=f"KAGAMI · {title}", layout="wide")
    st.title(title)
    st.caption(f"Pertanyaan pengguna: {question}")


def footer(sources: str, unit: str, period: str) -> None:
    st.caption(f"Sumber: {sources} · Satuan: {unit} · Periode: {period} · {CAUSAL_NOTE}")


def not_detected_badge(ci_low: float, ci_high: float) -> str:
    """'tidak terdeteksi' bila interval memuat nol; 'interval tidak tersedia' bila NaN (mis. PT wilayah)."""
    return S.detection_status(ci_low, ci_high)


def unit_names() -> dict[str, str]:
    """unit (province_id sebagai string / nama wilayah / ALL) → nama tampilan."""
    names = {str(k): v for k, v in CFG.regions.set_index("province_id")["province"].items()}
    return {**names, "ALL": "Nasional"}


def picker(label: str, options: list, key: str, format_func=str, default=None, container=None, radio: bool = False):
    """Selectbox/radio yang pilihannya disimpan di URL (`?key=nilai`) agar tampilan bisa dibagikan (PLAN.md §18.5)."""
    c = container or st
    opts = list(options)
    want = st.query_params.get(key)
    match = [o for o in opts if str(o) == want]
    idx = opts.index(match[0]) if match else (opts.index(default) if default in opts else 0)
    widget = c.radio if radio else c.selectbox
    kw = {"horizontal": True} if radio else {}
    val = widget(label, opts, index=idx, format_func=format_func, key=f"pick_{key}", **kw)
    st.query_params[key] = str(val)
    return val


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


def commodity_labels() -> dict[str, str]:
    return {k: v["pihps_name"] for k, v in CFG.commodities.items()}
