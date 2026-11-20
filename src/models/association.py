"""Task 3 -- asosiasi profil respons dengan eksposur & karakteristik provinsi. docs/METHODS.md §M3.

(3a) kendall_exact, level komoditas N = 10 (WP-22); (3b) meta_regression, level provinsi (WP-23);
(3c) fe_interaction, robustness efek tetap komoditas x minggu (WP-24).
"""

from __future__ import annotations

import pandas as pd

from kagami.utils.config import Config
from kagami.utils.todo import todo


def kendall_exact(cfg: Config, exposure: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """WP-22. Satu uji praregistrasi (E1): Kendall τ antara PT(8) dan import_ratio_direct,
    p permutasi EKSAK (10! permutasi), + leave-one-commodity-out (jackknife_min/max).
    -> baris artefak 'assoc' level='commodity'. Tulis kesimpulan sebagai "di antara 10 komoditas yang diamati".
    """
    todo("WP-22")


def meta_regression(cfg: Config, profiles: pd.DataFrame, boot: pd.DataFrame,
                    province_features: pd.DataFrame) -> pd.DataFrame:
    """WP-23. Meta-regresi efek acak pada deviasi δ(i,r,h) TANPA susut, maks 3 fitur praregistrasi:
    ln_dist_hub, rice_sufficiency (bila tersedia), n_kota (kontrol desain). H3: koefisien ln_dist_hub pada h=4 < 0
    (satu arah); h=12 dua arah.
    Interval: bootstrap blok mingguan (boot_replicates) DAN SE cluster provinsi CR2 -> laporkan yang lebih lebar.
    Jackknife per provinsi -> jackknife_min/max. -> baris 'assoc' level='province'.
    """
    todo("WP-23")


def fe_interaction(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                   province_features: pd.DataFrame) -> pd.DataFrame:
    """WP-24. (3c) Panel dengan efek tetap komoditas x minggu; koefisien interaksi de x Z(r)
    diidentifikasi hanya dari perbedaan antarprovinsi. -> baris 'assoc' method='fe_interaction'.
    Dipotong pertama bila waktu habis (urutan pemotongan, D-014).
    """
    todo("WP-24")
