"""Task 4 -- evaluasi prediktif rolling-origin (proposal §5.5). Notebook: notebooks/04_task4_forecast.ipynb.

BERAT (origin x horizon x model, M3 gradient boosting) -> jalankan di Kaggle/Colab. Hanya butuh Tahap 0,
jadi bisa paralel dengan Task 1. Panel provinsi bila ada; selain itu panel 7 wilayah (Tingkat B).
Tahan sesi habis: prediksi disimpan sebagai artefak `forecast_preds` tiap beberapa origin dan di-push ke Drive tim;
menjalankan ulang melanjutkan dari origin yang belum selesai.
"""

from __future__ import annotations

import pandas as pd

from kagami.evaluation import forecast_eval
from kagami.models import direction, forecasting, neural
from kagami.utils import drive
from kagami.tracking.logger import tracked
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact, require, write_artifact

REQUIRES = ("panel_weekly_region", "drivers_weekly", "world_prices_weekly")
OPTIONAL = ("panel_weekly",)   # panel provinsi bila ada (selain itu 7 wilayah, Tingkat B); notebook menariknya juga


@tracked("task4")   # log eksekusi & evaluasi terpusat (WP-36, D-137)
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


@tracked("task4")
def run_direction(cfg: Config) -> None:
    """EKSPLORATIF (D-141): klasifier arah C1/C2 dengan rolling-origin & fitur yang sama -> artefak `direction_preds`.
    Tidak mengubah `forecast_preds`/`forecast_eval`/`ablation` (uji resmi H5). CLI: `python -m kagami task4 --direction`."""
    require(cfg, *REQUIRES)
    panel_name = "panel_weekly" if exists(cfg, "panel_weekly") else "panel_weekly_region"
    done = read_artifact(cfg, "direction_preds") if exists(cfg, "direction_preds") else None
    preds = direction.rolling_direction(cfg, read_artifact(cfg, panel_name), read_artifact(cfg, "drivers_weekly"),
                                        read_artifact(cfg, "world_prices_weekly"), done=done,
                                        checkpoint=lambda d: write_artifact(cfg, "direction_preds", d))
    write_artifact(cfg, "direction_preds", preds)


@tracked("task4")
def run_direction_tuned(cfg: Config, models: tuple[str, ...] | None = None) -> None:
    """EKSPLORATIF (D-145): klasifier arah tuned C1t (+ fitur dinamika harga) / C2t (+ kurs), rolling-origin sama
    -> artefak `direction_tuned_preds`. `direction_preds` & uji resmi tidak berubah.
    CLI: `python -m kagami task4 --direction-tuned [C1t C2t]` (± 10–15 menit per model, CPU)."""
    require(cfg, *REQUIRES)
    panel_name = "panel_weekly" if exists(cfg, "panel_weekly") else "panel_weekly_region"
    done = read_artifact(cfg, "direction_tuned_preds") if exists(cfg, "direction_tuned_preds") else None
    preds = direction.rolling_direction_tuned(cfg, read_artifact(cfg, panel_name), read_artifact(cfg, "drivers_weekly"),
                                              read_artifact(cfg, "world_prices_weekly"),
                                              models=list(models) if models else None, done=done,
                                              checkpoint=lambda d: write_artifact(cfg, "direction_tuned_preds", d))
    write_artifact(cfg, "direction_tuned_preds", preds)


@tracked("task4")
def run_deep(cfg: Config, models: tuple[str, ...] | None = None) -> None:
    """EKSPLORATIF (D-142): PatchTST, TSMixer (± kurs), TimesFM 3.0 zero-shot (± kurs) dengan origin & baris uji Task 4
    -> artefak `deep_preds`. Uji resmi H5 tidak berubah. CLI: `python -m kagami task4 --deep [PTST TSMX TSMX_fx TFM TFM_fx]`.
    Butuh PyTorch; TFM butuh paket `timesfm` 3.x + bobot google/timesfm-3.0-pytorch (lisensi non-komersial)."""
    require(cfg, *REQUIRES)
    panel_name = "panel_weekly" if exists(cfg, "panel_weekly") else "panel_weekly_region"
    done = read_artifact(cfg, "deep_preds") if exists(cfg, "deep_preds") else None
    preds = neural.rolling_deep(cfg, read_artifact(cfg, panel_name), read_artifact(cfg, "drivers_weekly"),
                                read_artifact(cfg, "world_prices_weekly"), models=list(models) if models else None,
                                done=done, checkpoint=lambda d: write_artifact(cfg, "deep_preds", d))
    write_artifact(cfg, "deep_preds", preds)
