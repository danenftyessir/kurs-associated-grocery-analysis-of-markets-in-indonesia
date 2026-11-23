"""Utilitas bersama halaman Streamlit. Aplikasi HANYA membaca artefak; tidak ada estimasi saat runtime (D-010)."""

from __future__ import annotations

import importlib.util
import inspect
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
from kagami.utils.io import ArtifactMissing, read_artifact  # noqa: E402

CFG = Config(root=ROOT)
CAUSAL_NOTE = "Asosiasi historis, bukan kausalitas. Bukan ramalan."
# Lebar penuh: Streamlit baru memakai width="stretch" (use_container_width usang & akan dihapus); versi lama hanya
# mengenal use_container_width. Dipilih dari signature agar app jalan di versi mana pun >= 1.35 (pyproject).
STRETCH = ({"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters
           else {"use_container_width": True})


@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame | str | None:
    try:
        return read_artifact(CFG, name)
    except ArtifactMissing:
        return None


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
    return "tidak terdeteksi" if ci_low <= 0 <= ci_high else "terdeteksi"


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
