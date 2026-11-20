"""Utilitas tanggal bersama."""

from __future__ import annotations

import pandas as pd


def week_start(dates: pd.Series) -> pd.Series:
    """Label minggu ISO = tanggal Senin (Timestamp). Dipakai SEMUA modul agar join konsisten."""
    d = pd.to_datetime(dates)
    return (d - pd.to_timedelta(d.dt.weekday, unit="D")).dt.normalize()
