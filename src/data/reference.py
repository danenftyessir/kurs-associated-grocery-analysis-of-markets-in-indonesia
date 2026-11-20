"""Tabel buatan tim (WP-07): concordance, exposure, regulation, province_features.

Semua tabel ini CC BY 4.0 dan ikut zip juri. Spesifikasi: docs/METHODS.md §M0, docs/DATASETS.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Jarak great-circle (km). Dipakai untuk dist_hub_km."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def build_concordance(cfg: Config) -> pd.DataFrame:
    """WP-07. Dari configs/commodities.yaml + cek keberadaan seri Pink Sheet/item FAOSTAT/HS di data.

    confidence: high (padanan langsung) | medium (komposit/proksi) | low (tidak ada padanan).
    """
    todo("WP-07")


def build_exposure(cfg: Config, faostat: pd.DataFrame, bps_monthly: pd.DataFrame,
                   comtrade: pd.DataFrame, neraca_beras: pd.DataFrame) -> pd.DataFrame:
    """WP-07. Profil tiga jalur per komoditas.

    import_ratio_direct = impor / (produksi + impor - ekspor) rerata 2018-2023 (FAOSTAT SUA);
    bawang putih tidak ada di SUA -> pakai BPS/Comtrade + sumber produksi lain, atau kelas ordinal (U5).
    imported_input_ordinal: 0 tidak ada, 1 rendah, 2 tinggi (pakan jagung/bungkil kedelai untuk ayam & telur).
    world_price_link: ada/tidak padanan Pink Sheet. source: catat asal setiap angka.
    """
    todo("WP-07")


def build_regulation(cfg: Config, het_current: pd.DataFrame, history: pd.DataFrame,
                     bapanas_settings: pd.DataFrame) -> pd.DataFrame:
    """WP-07. Gabung riwayat HET/HAP/HPP -> satu baris per (komoditas, instrumen, zona, periode berlaku).

    Tanggal 'tidak terverifikasi' dipertahankan dengan verification='unverified' (jangan ditebak).
    Dipakai untuk E2 (respons di sekitar perubahan HET/HAP) dan penandaan minggu.
    """
    todo("WP-07")


def build_province_features(cfg: Config, padi: pd.DataFrame, konsumsi: pd.DataFrame) -> pd.DataFrame:
    """WP-07. Z(r) untuk Task 3b.

    dist_hub_km = jarak ibu kota ke hub terdekat (params.association.hubs; koordinat di region_crosswalk.csv;
                  provinsi hub sendiri -> jarak 0, pakai ln(1 + km)).
    rice_sufficiency = produksi beras / kebutuhan beras provinsi; BUTUH populasi provinsi (U11, belum ada).
                       Pemekaran Papua dijumlahkan ke induk sebelum rasio.
    n_kota = jumlah kota sampel PIHPS per provinsi (sumber: FAQ PIHPS; isi manual, U11).
    """
    todo("WP-07")
