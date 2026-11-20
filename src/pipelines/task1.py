"""Task 1 -- profil respons multi-penggerak (proposal §5.2). Notebook: notebooks/01_task1_profiles.ipynb.

BERAT (bootstrap & plasebo 499 replikasi) -> jalankan di Kaggle/Colab.
Panel provinsi dipakai bila `panel_weekly` ada (izin BI / Tingkat C); selain itu versi wilayah (Tingkat B).
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import inference
from kagami.features import response
from kagami.models import deviations, event_study
from kagami.models import local_projection as lp
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("drivers_weekly", "world_prices_weekly", "episodes", "panel_weekly_region", "eligibility")


def run(cfg: Config) -> None:
    require(cfg, *REQUIRES)
    drv, world, eps, region = (read_artifact(cfg, n) for n in
                               ("drivers_weekly", "world_prices_weekly", "episodes", "panel_weekly_region"))
    panel = read_artifact(cfg, "panel_weekly") if exists(cfg, "panel_weekly") else None
    p = cfg.params["inference"]

    parts = [deviations.region_profiles(cfg, region, drv, world)]
    events = [event_study.placebo_bands(cfg, region, eps, level="region")]
    if panel is not None:
        parts += [lp.national_profiles(cfg, panel, drv, world),
                  deviations.province_deviations(cfg, panel, drv, world)]
        events.append(event_study.placebo_bands(cfg, panel, eps, level="national"))
        est = lambda pb, db: lp.national_profiles(cfg, pb, db, world)  # noqa: E731
        reps = inference.joint_bootstrap(cfg, est, panel, drv, p["bootstrap_B"])
        write_artifact(cfg, "boot_replicates", reps)
        write_artifact(cfg, "placebo_stats", inference.circular_placebo(cfg, est, panel, drv, p["placebo_R"]))
        profiles = inference.bootstrap_ci(pd.concat(parts, ignore_index=True), reps)
        profiles = response.shrink_deviations(cfg, profiles)
    else:
        profiles = pd.concat(parts, ignore_index=True)
    write_artifact(cfg, "profiles", profiles)
    write_artifact(cfg, "events", pd.concat(events, ignore_index=True))
    write_artifact(cfg, "response_features", response.response_features(cfg, profiles))
