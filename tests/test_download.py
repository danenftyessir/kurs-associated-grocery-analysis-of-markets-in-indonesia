"""Pencarian tautan unduhan terbaru (U16) tanpa jaringan + konfigurasi sumber http."""

import re

from kagami.data.download import find_link, resolve_url


def test_pinksheet_link_pattern_matches_world_bank_page(cfg):
    src = cfg.sources["pinksheet"]
    html = ('<a href="https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/'
            'CMO-Historical-Data-Monthly.xlsx">Monthly prices</a> <a href="/other.pdf">x</a>')
    assert find_link(html, src["link_pattern"]).endswith("0050012026/related/CMO-Historical-Data-Monthly.xlsx")
    assert find_link("<p>tidak ada</p>", src["link_pattern"]) is None
    assert re.fullmatch(src["link_pattern"], src["url"])            # url cadangan cocok pola yang sama


def test_resolve_url_without_landing_uses_static_url():
    assert resolve_url({"url": "https://example.org/a.csv"}) == "https://example.org/a.csv"
