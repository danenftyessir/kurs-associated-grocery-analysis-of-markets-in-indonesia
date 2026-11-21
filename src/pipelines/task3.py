"""Task 3 -- asosiasi profil respons (proposal §5.4) + E2 profil per rezim HET/HAP (D-124).
Notebook: notebooks/03_task3_association.ipynb. Ringan."""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import regimes
from kagami.models import association
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("exposure", "response_features", "province_features")
OPTIONAL = ("panel_weekly", "profiles", "boot_replicates", "eligibility", "drivers_weekly",   # 3b & 3c bila panel provinsi ada
            "world_prices_weekly", "regulation")                                            # E2 (D-124)


def run(cfg: Config) -> None:
    require(cfg, *REQUIRES)
    exposure, feats, zf = (read_artifact(cfg, n) for n in REQUIRES)
    parts = [association.kendall_exact(cfg, exposure, feats)]
    if exists(cfg, "panel_weekly"):
        parts.append(association.meta_regression(cfg, read_artifact(cfg, "profiles"),
                                                 read_artifact(cfg, "boot_replicates"), zf))
        elig = read_artifact(cfg, "eligibility") if exists(cfg, "eligibility") else None
        parts.append(association.fe_interaction(cfg, read_artifact(cfg, "panel_weekly"),
                                                read_artifact(cfg, "drivers_weekly"), zf, elig=elig))
        if exists(cfg, "regulation") and exists(cfg, "world_prices_weekly"):     # E2 eksploratif (D-124)
            write_artifact(cfg, "regime_profiles", regimes.regime_profiles(
                cfg, read_artifact(cfg, "panel_weekly"), read_artifact(cfg, "drivers_weekly"),
                read_artifact(cfg, "world_prices_weekly"), read_artifact(cfg, "regulation"), elig=elig))
        else:
            print("[task3] E2 dilewati: artefak regulation atau world_prices_weekly tidak ada")
    else:
        print("[task3] PERINGATAN: panel_weekly tidak ada -> hanya Kendall E1 (tanpa meta-regresi, FE, dan E2). "
              "Di Kaggle/Colab tarik task3.OPTIONAL dari Drive tim.")
    write_artifact(cfg, "assoc", pd.concat(parts, ignore_index=True))
