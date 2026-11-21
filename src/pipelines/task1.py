"""Task 1 -- profil respons multi-penggerak (proposal §5.2). Notebook: notebooks/01_task1_profiles.ipynb.

BERAT (bootstrap & plasebo 499 replikasi) -> jalankan di Kaggle/Colab.
Panel provinsi dipakai bila `panel_weekly` ada (ikut paket juri, D-104); selain itu versi wilayah.
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import inference
from kagami.features import response
from kagami.models import deviations, event_study
from kagami.models import local_projection as lp
from kagami.utils import drive
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("drivers_weekly", "world_prices_weekly", "episodes", "panel_weekly_region", "eligibility")
OPTIONAL = ("panel_weekly",)   # dipakai bila ada (profil nasional, provinsi, bootstrap, plasebo); notebook menariknya juga


def run(cfg: Config) -> None:
    require(cfg, *REQUIRES)
    drv, world, eps, region, elig = (read_artifact(cfg, n) for n in
                                     ("drivers_weekly", "world_prices_weekly", "episodes", "panel_weekly_region",
                                      "eligibility"))
    panel = read_artifact(cfg, "panel_weekly") if exists(cfg, "panel_weekly") else None
    if panel is None:
        print("[task1] PERINGATAN: panel_weekly tidak ada -> hanya profil 7 wilayah (tanpa nasional, provinsi, bootstrap, "
              "plasebo). Di Kaggle/Colab tarik task1.OPTIONAL dari Drive tim.")
    p = cfg.params["inference"]

    parts = [deviations.region_profiles(cfg, region, drv, world)]
    events = [event_study.placebo_bands(cfg, region, eps, level="region")]
    if panel is not None:
        parts += [lp.national_profiles(cfg, panel, drv, world, elig=elig),
                  deviations.province_deviations(cfg, panel, drv, world, elig=elig)]
        events.append(event_study.placebo_bands(cfg, panel, eps, level="national", elig=elig))
        key_h = [int(h) for h in cfg.params["lp"]["key_horizons"]]

        def est(pb, db, wb, commodities=None):       # profil nasional + deviasi provinsi (h kunci) per replikasi
            return pd.concat([lp.national_profiles(cfg, pb, db, wb, elig=elig, commodities=commodities),
                              deviations.province_deviations(cfg, pb, db, wb, elig=elig, horizons=key_h,
                                                             commodities=commodities)], ignore_index=True)

        def saver(name):
            def save(df: pd.DataFrame) -> None:
                write_artifact(cfg, name, df)
                drive.push(cfg, stages=("task1",))
            return save

        drive.pull(cfg, ("boot_replicates", "placebo_stats"))  
        old = {n: read_artifact(cfg, n) if exists(cfg, n) else None for n in ("boot_replicates", "placebo_stats")}
        reps = inference.joint_bootstrap(cfg, est, panel, drv, p["bootstrap_B"], world=world,
                                         done=old["boot_replicates"], checkpoint=saver("boot_replicates"))
        write_artifact(cfg, "boot_replicates", reps)
        write_artifact(cfg, "placebo_stats",
                       inference.circular_placebo(cfg, est, panel, drv, p["placebo_R"], world=world,
                                                  done=old["placebo_stats"], checkpoint=saver("placebo_stats")))
        profiles = inference.bootstrap_ci(pd.concat(parts, ignore_index=True), reps)
        profiles = response.shrink_deviations(cfg, profiles)
    else:
        profiles = pd.concat(parts, ignore_index=True)
    write_artifact(cfg, "profiles", profiles)
    write_artifact(cfg, "events", pd.concat(events, ignore_index=True))
    write_artifact(cfg, "response_features", response.response_features(cfg, profiles))
