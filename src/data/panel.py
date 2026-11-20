"""Panel 7 wilayah (WP-08) -- peta utama 7 wilayah; ikut paket juri bersama panel provinsi (D-104)."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config


def build_region_panel(cfg: Config, weekly: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """WP-08. -> artefak 'panel_weekly_region'.

    Hanya seri eligible. Per (week, region, commodity): rerata log harga provinsi (bobot sama),
    lalu dinormalkan: log_price_index = rerata - nilai minggu pertama seri (indeks, bukan level Rp,
    agar tidak merekonstruksi data mentah PIHPS). n_provinces = jumlah provinsi yang teramati minggu itu.
    """
    todo("WP-08")
