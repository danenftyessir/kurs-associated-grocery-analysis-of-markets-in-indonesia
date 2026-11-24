"""Mesin eksperimen Task 4 arah: rolling-origin (train t + h <= origin), origin pengembangan vs test final."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.features.forecast import FEATURE_GROUPS, origins, split_origin  # noqa: E402
from feats import cols_for  # noqa: E402

HERE = os.path.dirname(__file__)
DEV_END = pd.Timestamp("2023-12-31")      # origin pengembangan: origin + h <= DEV_END (target terealisasi dalam 2023)
TEST_START = pd.Timestamp("2024-01-01")   # test final: origin >= TEST_START (tidak dipakai untuk memilih apa pun)
BASE = FEATURE_GROUPS["base"]
FX = FEATURE_GROUPS["fx"]
CATS = ["commodity", "region"]
_TAB = {}


def table():
    if "t" not in _TAB:
        _TAB["t"] = pd.read_parquet(os.path.join(HERE, os.environ.get("KAGAMI_EXT", "ext.parquet")))
    return _TAB["t"]


def origin_list(h, part):
    os_ = origins(cfg, table()["week"].drop_duplicates(), h)
    if part == "dev":
        return [o for o in os_ if o + pd.Timedelta(weeks=h) <= DEV_END]
    if part == "test":
        return [o for o in os_ if o >= TEST_START]
    return os_


def feature_cols(groups, h, fx=False):
    return BASE + (FX if fx else []) + cols_for(groups, h)


def codes(df, cats):
    out = []
    for c in cats:
        levels = sorted(table()[c].dropna().unique())
        out.append(pd.Categorical(df[c], categories=levels).codes.astype(float))
    return np.column_stack(out) if out else np.empty((len(df), 0))


def xy(df, cols, cats):
    X = np.column_stack([df[cols].astype(float).to_numpy(), codes(df, cats)])
    return X


def fit_hgb(train, test, cols, cats, params, seed):
    from sklearn.ensemble import HistGradientBoostingClassifier
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    if params.get("recent_years"):
        tr = tr[tr["week"] > tr["week"].max() - pd.Timedelta(weeks=int(52 * params["recent_years"]))]
    num = [c for c in cols if tr[c].notna().any()]
    up = (tr["y"] > 0).to_numpy()
    w = None
    if params.get("balanced"):
        w = np.where(up, 0.5 / up.mean(), 0.5 / (1 - up.mean()))
    if params.get("decay_years"):
        age = (tr["week"].max() - tr["week"]).dt.days.to_numpy() / 365.25
        dw = 0.5 ** (age / float(params["decay_years"]))
        w = dw if w is None else w * dw
    m = HistGradientBoostingClassifier(
        max_iter=int(params.get("max_iter", 300)), learning_rate=float(params.get("learning_rate", 0.05)),
        max_leaf_nodes=int(params.get("max_leaf_nodes", 31)), min_samples_leaf=int(params.get("min_samples_leaf", 20)),
        l2_regularization=float(params.get("l2_regularization", 0.0)), max_features=float(params.get("max_features", 1.0)),
        max_depth=params.get("max_depth"), categorical_features=[False] * len(num) + [True] * len(cats),
        random_state=seed)
    m.fit(xy(tr, num, cats), up, sample_weight=w)
    return m.predict_proba(xy(test, num, cats))[:, 1]


def one(o, h, cols, cats, params, seed):
    train, test = split_origin(cfg, table(), o, h)
    if train.empty or test.empty:
        return None
    p = fit_hgb(train, test, cols, cats, params, seed)
    return test[["province_id", "region", "commodity"]].assign(origin=o, horizon=h, y_true=test["y"].to_numpy(), p_up=p)


def run(h, part, cols, cats=CATS, params=None, n_jobs=6, seed=None, origins_=None):
    from joblib import Parallel, delayed
    params = params or {}
    seed = cfg.seed if seed is None else seed
    os_ = origins_ if origins_ is not None else origin_list(h, part)
    res = Parallel(n_jobs=n_jobs)(delayed(one)(o, h, cols, cats, params, seed) for o in os_)
    return pd.concat([r for r in res if r is not None], ignore_index=True)


# ------------------------------------------------------------------ metrik
def confusion(y, s, thr):
    k = np.isfinite(y) & np.isfinite(s) & (y != 0)
    up, pu = y[k] > 0, s[k] > thr
    return np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float)


def stats_from(C):
    tp, fn, fp, tn = (C[..., i] for i in range(4))
    with np.errstate(divide="ignore", invalid="ignore"):
        f1u, f1d = 2 * tp / (2 * tp + fp + fn), 2 * tn / (2 * tn + fn + fp)
        n = tp + fn + fp + tn
        return {"macro_f1": (f1u + f1d) / 2, "f1_up": f1u, "f1_down": f1d,
                "prec_up": tp / (tp + fp), "rec_up": tp / (tp + fn), "prec_down": tn / (tn + fn), "rec_down": tn / (tn + fp),
                "bal_acc": (tp / (tp + fn) + tn / (tn + fp)) / 2, "acc": (tp + tn) / n,
                "weighted_f1": ((tp + fn) * f1u + (fp + tn) * f1d) / n,
                "mcc": (tp * tn - fp * fn) / np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))}


def macro_f1(y, s, thr=0.5):
    return float(stats_from(confusion(np.asarray(y, float), np.asarray(s, float), thr))["macro_f1"])


def best_threshold(y, s, grid):
    vals = [macro_f1(y, s, t) for t in grid]
    i = int(np.nanargmax(vals))
    return float(grid[i]), float(vals[i])


class Timer:
    def __enter__(self):
        self.t = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.s = time.perf_counter() - self.t
