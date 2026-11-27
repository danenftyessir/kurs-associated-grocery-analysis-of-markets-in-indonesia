"""Bersama untuk validasi K4 (2026-11-27, EKSPLORATIF, baca-saja terhadap artefak D-164).

Memakai `k4_common` D-164 apa adanya (ambang, split, metrik). Prediksi beku dibaca dari KAGAMI_EXP sesi D-164
(`k4_{dev,test,forward}_preds.parquet`); tidak ada model yang dilatih ulang di modul ini. Keluaran ke `../hasil/`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))
K4S = os.path.join(AUD, "20261126_k4_risiko_material", "scripts")
if K4S not in sys.path:
    sys.path.insert(0, K4S)

from k4_common import (EXP, H, REGULATED, boot_idx, brier, ece, logit, np, pd, reliability, table, top_flags)  # noqa: E402,F401
from k4_eval import fast_ap, fast_auc  # noqa: E402,F401

VOUT = os.path.abspath(os.path.join(HERE, "..", "hasil"))
os.makedirs(VOUT, exist_ok=True)
SEED = 154
DEV_LAST_YEAR = 2023


def preds(part):
    d = pd.read_parquet(os.path.join(EXP, f"k4_{part}_preds.parquet"))
    return d.sort_values(["horizon", "origin", "province_id", "commodity"]).reset_index(drop=True)


def flags_k(d, score, k):
    return top_flags(d, score, ["origin", "province_id"], k=k, seed=SEED).to_numpy()


def save(df, name):
    df.to_csv(os.path.join(VOUT, name), index=False, float_format="%.5g")
    return df
