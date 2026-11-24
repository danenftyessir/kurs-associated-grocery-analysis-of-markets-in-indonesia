"""Ronde 2: LightGBM/XGBoost, spesialis per kelompok komoditas, dua tahap (berubah? → arah). Rolling-origin sama."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from engine import CATS, cfg, codes, table  # noqa: F401
from kagami.features.forecast import split_origin

GROUPS_COMM = {"regulated": ["beras", "daging_sapi", "minyak_goreng", "gula_pasir"],
               "volatile": ["cabai_merah", "cabai_rawit", "bawang_merah"],
               "other": ["bawang_putih", "daging_ayam", "telur_ayam"]}
LGB = {"n_estimators": 400, "learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 200, "colsample_bytree": 0.5,
       "subsample": 0.8, "subsample_freq": 1, "reg_lambda": 3.0}
XGB = {"n_estimators": 400, "learning_rate": 0.03, "max_depth": 6, "min_child_weight": 20, "colsample_bytree": 0.5,
       "subsample": 0.8, "reg_lambda": 3.0}


def _xy(df, cols, cats):
    X = df[cols].astype(float).copy()
    for c in cats:
        X[c] = pd.Categorical(df[c], categories=sorted(table()[c].dropna().unique()))
    return X


def fit_proba(kind, tr, te, cols, cats, params, seed, target="up"):
    """kind: hgb | lgb | xgb. target: up (latih y ≠ 0, label y > 0) | change (latih semua, label y ≠ 0)."""
    tr = tr[np.isfinite(tr["y"].to_numpy(float))]
    if target == "up":
        tr = tr[tr["y"] != 0]
        lab = (tr["y"] > 0).to_numpy().astype(int)
    else:
        lab = (tr["y"] != 0).to_numpy().astype(int)
    num = [c for c in cols if tr[c].notna().any()]
    if lab.min() == lab.max():
        return np.full(len(te), float(lab.mean()))
    if kind == "hgb":
        from sklearn.ensemble import HistGradientBoostingClassifier
        Xtr = np.column_stack([tr[num].astype(float).to_numpy(), codes(tr, cats)])
        Xte = np.column_stack([te[num].astype(float).to_numpy(), codes(te, cats)])
        m = HistGradientBoostingClassifier(**params, categorical_features=[False] * len(num) + [True] * len(cats),
                                           random_state=seed)
        m.fit(Xtr, lab)
        return m.predict_proba(Xte)[:, 1]
    if kind == "lgb":
        import lightgbm as lgb
        m = lgb.LGBMClassifier(**{**LGB, **params}, random_state=seed, verbose=-1, n_jobs=2)
        m.fit(_xy(tr, num, cats), lab)
        return m.predict_proba(_xy(te, num, cats))[:, 1]
    if kind == "xgb":
        import xgboost as xgb
        m = xgb.XGBClassifier(**{**XGB, **params}, random_state=seed, enable_categorical=True, tree_method="hist",
                              n_jobs=2, max_cat_to_onehot=1)
        m.fit(_xy(tr, num, cats), lab)
        return m.predict_proba(_xy(te, num, cats))[:, 1]
    raise ValueError(kind)


def one(o, h, spec, seed):
    """spec: dict nama → (kind, cols, cats, params, target, commodity_group|None)."""
    train, test = split_origin(cfg, table(), o, h)
    if train.empty or test.empty:
        return None
    out = test[["province_id", "region", "commodity"]].assign(origin=o, horizon=h, y_true=test["y"].to_numpy())
    for name, (kind, cols, cats, params, target, grp) in spec.items():
        if grp is None:
            out[name] = fit_proba(kind, train, test, cols, cats, params, seed, target)
        else:   # spesialis: satu model per kelompok komoditas
            p = np.full(len(test), np.nan)
            for g, comms in GROUPS_COMM.items():
                mt, me = train["commodity"].isin(comms).to_numpy(), test["commodity"].isin(comms).to_numpy()
                if me.any():
                    p[me] = fit_proba(kind, train[mt], test[me], cols, cats, params, seed, target)
            out[name] = p
    return out


def run_spec(h, origins_, spec, n_jobs=6, seed=None):
    from joblib import Parallel, delayed
    seed = cfg.seed if seed is None else seed
    res = Parallel(n_jobs=n_jobs)(delayed(one)(o, h, spec, seed) for o in origins_)
    return pd.concat([r for r in res if r is not None], ignore_index=True)


def three_class(y, p_change, p_up, tau):
    """Prediksi tiga kelas: tetap bila P(berubah) < tau, selain itu naik/turun dari p_up. → (macro F1 3 kelas, F1 per kelas)."""
    true = np.where(y == 0, 0, np.where(y > 0, 1, -1))
    pred = np.where(p_change < tau, 0, np.where(p_up > 0.5, 1, -1))
    f = {}
    for c, nm in ((1, "naik"), (-1, "turun"), (0, "tetap")):
        tp = ((pred == c) & (true == c)).sum()
        fp = ((pred == c) & (true != c)).sum()
        fn = ((pred != c) & (true == c)).sum()
        f[nm] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else np.nan
    return float(np.nanmean(list(f.values()))), f
