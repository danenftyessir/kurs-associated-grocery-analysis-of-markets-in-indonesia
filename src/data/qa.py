"""QA Tahap 0 + laporan (WP-10). Semua cek silang antar sumber ada di sini."""

from __future__ import annotations

import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config


def flag_price_outliers(daily: pd.DataFrame) -> pd.DataFrame:
    """WP-10. Tandai lonjakan satu hari (mis. Papua 2017-07-03 beras: 29.750 lalu 9.500).

    Aturan default: |Δlog| > 0.5 terhadap hari sebelum DAN sesudah berbalik -> flag (tidak dihapus otomatis).
    """
    todo("WP-10")


def check_import_totals(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    """WP-10. Σ bulanan BPS vs total tahunan portal (tentukan satuan 'Totals': USD atau kg)."""
    todo("WP-10")


def check_bapanas_bias(weekly: pd.DataFrame, bapanas: pd.DataFrame) -> pd.DataFrame:
    """WP-10. Rerata bulanan PIHPS vs Panel Harga Bapanas per provinsi x komoditas (2022-2026): bias & korelasi Δ."""
    todo("WP-10")


def stage0_report(cfg: Config, sections: dict[str, pd.DataFrame]) -> str:
    """WP-10. Markdown -> artefak 'stage0_report': cakupan per sumber, kelayakan, episode, variasi kurs, MDE, QA."""
    todo("WP-10")
