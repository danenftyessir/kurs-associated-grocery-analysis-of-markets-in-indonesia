"""Tes asap: setiap halaman Streamlit jalan tanpa exception (artefak ada atau belum)."""

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = [APP / "Home.py", *sorted((APP / "pages").glob("*.py"))]


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.stem)
def test_page_runs(page, monkeypatch):
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    at = AppTest.from_file(str(page), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
