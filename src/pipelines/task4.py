"""Task 4 -- evaluasi prediktif rolling-origin (proposal §5.5). Notebook: notebooks/04_task4_forecast.ipynb.

BERAT (origin x horizon x model, M3 gradient boosting) -> jalankan di Kaggle/Colab. Hanya butuh Tahap 0,
jadi bisa paralel dengan Task 1. Panel provinsi bila ada; selain itu panel 7 wilayah (Tingkat B).
Tahan sesi habis: prediksi disimpan sebagai artefak `forecast_preds` tiap beberapa origin dan di-push ke Drive tim;
menjalankan ulang melanjutkan dari origin yang belum selesai.
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import forecast_eval
from kagami.models import forecasting
from kagami.utils import drive
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("panel_weekly_region", "drivers_weekly", "world_prices_weekly")
OPTIONAL = ("panel_weekly",)   # panel provinsi bila ada (selain itu 7 wilayah, Tingkat B); notebook menariknya juga


def run(cfg: Config) -> None:
    require(cfg, *REQUIRES)
    panel_name = "panel_weekly" if exists(cfg, "panel_weekly") else "panel_weekly_region"
    if panel_name == "panel_weekly_region":
        print("[task4] PERINGATAN: panel_weekly tidak ada -> prediksi per 7 wilayah, bukan per provinsi. "
              "Di Kaggle/Colab tarik task4.OPTIONAL dari Drive tim.")

    def save(preds: pd.DataFrame) -> None:                       # checkpoint: tulis artefak + push ke Drive tim
        write_artifact(cfg, "forecast_preds", preds)
        drive.push(cfg, stages=("task4",))

    drive.pull(cfg, ("forecast_preds",))                         # lanjutkan run sebelumnya bila ada di Drive
    done = read_artifact(cfg, "forecast_preds") if exists(cfg, "forecast_preds") else None
    preds = forecasting.rolling_predictions(cfg, read_artifact(cfg, panel_name),
                                            read_artifact(cfg, "drivers_weekly"),
                                            read_artifact(cfg, "world_prices_weekly"),
                                            done=done, checkpoint=save)
    write_artifact(cfg, "forecast_preds", preds)
    write_artifact(cfg, "forecast_eval", forecast_eval.evaluate(cfg, preds))
    write_artifact(cfg, "ablation", forecast_eval.ablation(cfg, preds))
