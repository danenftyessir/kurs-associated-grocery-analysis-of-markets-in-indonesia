"""Kepala klasifikasi tahap-2: ramalan walk-forward TimesFM (+ fitur) → CatBoost.

Baris tahap-2 hanya ada pada origin (tiap 4 minggu); ramalan TimesFM pada origin o' memakai konteks s.d. o' saja
(zero-shot, tidak pernah dilatih pada data kami) → out-of-sample. Untuk origin o, CatBoost dilatih pada baris origin o'
dengan o' + h <= o (label sudah terealisasi pada o), lalu memprediksi baris origin o. Tidak ada prediksi in-sample.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402

HERE = os.path.dirname(__file__)
ROOT_INTERIM = os.path.join(cfg.root, "data", "interim")
KEY = ["origin", "province_id", "commodity"]


def base_frame(h, oof: dict | None = None):
    """Satu baris per (origin, seri) dengan label y_h, ramalan model deep (kedua horizon), fitur ext pada minggu origin."""
    dp = pd.read_parquet(os.path.join(ROOT_INTERIM, "deep_preds.parquet"))
    dp = dp[dp["model"].isin(["TFM", "TFM_fx", "PTST", "TSMX"])]
    wide = dp.pivot_table(index=KEY, columns=["model", "horizon"], values="y_pred", aggfunc="first")
    wide.columns = [f"{m.lower()}_{h_}" for m, h_ in wide.columns]
    wide = wide.reset_index()
    ext = pd.read_parquet(os.path.join(HERE, "ext.parquet")).rename(columns={"week": "origin"})
    df = ext.merge(wide, on=KEY, how="inner")
    df["y_true"] = df[f"y_{h}"]
    if oof:
        for name, frame in oof.items():
            df = df.merge(frame[KEY + ["p_up"]].rename(columns={"p_up": name}), on=KEY, how="left")
    df["tfm_gap"] = df["tfm_8"] - df["tfm_4"]
    df["tfm_fx_diff"] = df.get("tfm_fx_8", np.nan) - df.get("tfm_8", np.nan)
    return df[np.isfinite(df["y_true"])].reset_index(drop=True)


def fit_predict(train, test, cols, cats, params, seed):
    from catboost import CatBoostClassifier
    tr = train[train["y_true"] != 0]
    up = (tr["y_true"] > 0).astype(int).to_numpy()
    m = CatBoostClassifier(iterations=int(params.get("iterations", 500)), depth=int(params.get("depth", 6)),
                           learning_rate=float(params.get("learning_rate", 0.05)),
                           l2_leaf_reg=float(params.get("l2_leaf_reg", 3.0)), random_seed=seed, verbose=0,
                           thread_count=int(params.get("threads", 4)), allow_writing_files=False)
    Xtr, Xte = tr[cols + cats].copy(), test[cols + cats].copy()
    for c in cats:
        Xtr[c], Xte[c] = Xtr[c].astype(str), Xte[c].astype(str)
    m.fit(Xtr, up, cat_features=list(range(len(cols), len(cols) + len(cats))))
    return m.predict_proba(Xte)[:, 1]


def one(df, o, h, cols, cats, params, seed, min_origins):
    hist = df[df["origin"] + pd.Timedelta(weeks=h) <= o]
    if hist["origin"].nunique() < min_origins:
        return None
    test = df[df["origin"] == o]
    if test.empty:
        return None
    p = fit_predict(hist, test, cols, cats, params, seed)
    return test[KEY + ["region", "y_true"]].assign(horizon=h, p_up=p)


def run(df, h, eval_origins, cols, cats=("commodity", "region"), params=None, seed=None, min_origins=8, n_jobs=3):
    from joblib import Parallel, delayed
    params = params or {}
    seed = cfg.seed if seed is None else seed
    res = Parallel(n_jobs=n_jobs)(delayed(one)(df, o, h, cols, list(cats), params, seed, min_origins)
                                  for o in eval_origins)
    res = [r for r in res if r is not None]
    return pd.concat(res, ignore_index=True) if res else pd.DataFrame()


def residual_calibrated(h, eval_origins, model="TFM", by_commodity=True, min_origins=8):
    """Kalibrasi probabilitas dari ramalan regresi: P(naik | ŷ) = porsi residu historis e (origin o' + h <= o) dengan
    ŷ + e > 0, per komoditas. Residu dari origin yang sudah terealisasi saja (walk-forward)."""
    dp = pd.read_parquet(os.path.join(ROOT_INTERIM, "deep_preds.parquet"))
    d = dp[(dp["model"] == model) & (dp["horizon"] == h)].copy()
    d["e"] = d["y_true"] - d["y_pred"]
    out = []
    for o in eval_origins:
        hist = d[d["origin"] + pd.Timedelta(weeks=h) <= o]
        if hist["origin"].nunique() < min_origins:
            continue
        test = d[d["origin"] == o].copy()
        groups = test.groupby("commodity") if by_commodity else [(None, test)]
        for c, t in groups:
            e = np.sort((hist[hist["commodity"] == c] if by_commodity else hist)["e"].to_numpy())
            # P(y > 0) = P(e > -ŷ) = 1 - ECDF(-ŷ)
            p = 1 - np.searchsorted(e, -t["y_pred"].to_numpy(), side="right") / len(e)
            out.append(t.assign(p_up=p))
    return pd.concat(out, ignore_index=True)
