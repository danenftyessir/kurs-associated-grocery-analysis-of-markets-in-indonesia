"""Task 3 -- asosiasi profil respons (proposal §5.4). Notebook: notebooks/03_task3_association.ipynb. Ringan."""

from __future__ import annotations

import pandas as pd

from kagami.models import association
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("exposure", "response_features", "province_features")


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
    write_artifact(cfg, "assoc", pd.concat(parts, ignore_index=True))
