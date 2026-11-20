"""Task 4 -- evaluasi prediktif rolling-origin (proposal §5.5). Notebook: notebooks/04_task4_forecast.ipynb.

BERAT (origin x horizon x model, M3 gradient boosting) -> jalankan di Kaggle/Colab. Hanya butuh Tahap 0,
jadi bisa paralel dengan Task 1. Panel provinsi bila ada; selain itu panel 7 wilayah (Tingkat B).
"""

from __future__ import annotations

from kagami.evaluation import forecast_eval
from kagami.models import forecasting
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("panel_weekly_region", "drivers_weekly", "world_prices_weekly")


def run(cfg: Config) -> None:
    require(cfg, *REQUIRES)
    panel_name = "panel_weekly" if exists(cfg, "panel_weekly") else "panel_weekly_region"
    preds = forecasting.rolling_predictions(cfg, read_artifact(cfg, panel_name),
                                            read_artifact(cfg, "drivers_weekly"),
                                            read_artifact(cfg, "world_prices_weekly"))
    out = cfg.out_dir / "data" / "interim" / "forecast_preds.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(out, index=False)
    write_artifact(cfg, "forecast_eval", forecast_eval.evaluate(cfg, preds))
    write_artifact(cfg, "ablation", forecast_eval.ablation(cfg, preds))
