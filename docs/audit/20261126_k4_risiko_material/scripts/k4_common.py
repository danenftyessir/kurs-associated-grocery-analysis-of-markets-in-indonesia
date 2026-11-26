"""Bersama untuk K4 — risiko kenaikan harga material (EKSPLORATIF, D-164): path, tabel, origin, target, metrik.

EXP = folder tabel kerja (env KAGAMI_EXP; default scratchpad sesi K4). `base.parquet` = tabel resmi C1-tuned (`feature_table` +
`price_dynamics.extend_table`) + kolom kualitas label D-147 (ticks_h, flip_h, st0, st_h); dibangun ulang dengan
`docs/audit/20261125_task4_audit_preprocessing/scripts/prep.py` (set KAGAMI_EXP lebih dulu).

Target K4 (TARGET_DEFINITION.md):
- endpoint  z = 1[y_h >= thr(o,h,c)], y_h = log p_{t+h} - log p_t (rerata hari teramati, NaN bila minggu hilang);
- kejadian  z_any = 1[max_{k=1..h} (log p_{t+k} - log p_t) >= thr(o,h,c)] (minggu hilang dilewati);
- thr(o,h,c) = persentil PCT |y_h| baris latih komoditas c (week + h <= origin, y_h & lag tersedia) = aturan D-154.
Universe origin o = semua seri dengan lag harga tersedia pada o (termasuk y = 0 dan target tak teramati → z = 0; D-155).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))
os.environ.setdefault("KAGAMI_EXP", r"C:\Users\HYPERS~1\AppData\Local\Temp\claude\2939a692ee05a2e7\3211c2aa-ec43-4cff-bf30-3daec2de270b\scratchpad\exp")
EXP = os.environ["KAGAMI_EXP"]
for d in ("20261124_task4_optimasi_arah", "20261125_task4_audit_preprocessing"):
    p = os.path.join(AUD, d, "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from kg import cfg  # noqa: E402,F401  (os.chdir ke root project + alias paket kagami)
from kagami.features.forecast import LAG_COLUMNS, origins  # noqa: E402
from kagami.stats.resampling import moving_block_indices  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
DEV_END, TEST_START = pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-01")
H = (4, 8)
K = ["province_id", "commodity"]
KEYS = K + ["week"]
PCT = float(cfg.params["forecast"]["large_move_pct"])         # 80 (proxy materialitas statistik utama)
REGULATED = ("beras", "daging_sapi", "gula_pasir", "minyak_goreng")
REPS = 1999
TICK = 50.0
_T = {}


def table():
    if "t" not in _T:
        _T["t"] = pd.read_parquet(os.path.join(EXP, "base.parquet"))
    return _T["t"]


def panel_logp():
    """Matriks minggu × seri log harga mingguan TERAMATI (NaN bila hilang), dari artefak panel_weekly."""
    if "lp" not in _T:
        from kagami.utils.io import read_artifact
        p = read_artifact(cfg, "panel_weekly")
        _T["lp"] = p.pivot(index="week", columns=["province_id", "commodity"], values="log_price").sort_index()
    return _T["lp"]


def add_event(tab):
    """Tambah kolom ymax_h = max_{k=1..h} (log p_{t+k} - log p_t) (NaN bila p_t atau semua p_{t+k} hilang)."""
    lp = panel_logp()
    idx = pd.date_range(lp.index.min(), tab["week"].max() + pd.Timedelta(weeks=max(H)), freq="7D")
    lp = lp.reindex(idx)
    out = tab.copy()
    for h in H:
        steps = np.stack([(lp.shift(-k) - lp).to_numpy() for k in range(1, h + 1)], 0)
        with np.errstate(all="ignore"):
            mx = np.where(np.isnan(steps).all(0), np.nan, np.nanmax(np.where(np.isnan(steps), -np.inf, steps), 0))
        mx = pd.DataFrame(mx, index=lp.index, columns=lp.columns).stack(["province_id", "commodity"], future_stack=True)
        mx = mx.rename(f"ymax_{h}").reset_index().rename(columns={"level_0": "week"})
        out = out.drop(columns=[f"ymax_{h}"], errors="ignore").merge(mx, on=["week"] + K, how="left")
    return out


def origin_list(h, part, weeks=None):
    w = table()["week"].drop_duplicates() if weeks is None else weeks
    os_ = origins(cfg, w, h)
    if part == "dev":
        return [o for o in os_ if o + pd.Timedelta(weeks=h) <= DEV_END]
    if part == "test":
        return [o for o in os_ if o >= TEST_START]
    raise ValueError(part)


def thresholds(tab, o, h, pct=PCT):
    """Ambang walk-forward per komoditas: persentil pct |y_h| baris latih (week + h <= o, y_h & lag ada)."""
    tr = tab[(tab["week"] + pd.Timedelta(weeks=h) <= o)]
    tr = tr[np.isfinite(tr[f"y_{h}"]) & tr[LAG_COLUMNS].notna().all(1)]
    return tr.groupby("commodity")[f"y_{h}"].apply(lambda s: np.nanpercentile(s.abs(), pct))


def split_k4(tab, o, h, target="end", pct=PCT):
    """(train, test, thr) untuk origin o. Train: week + h <= o, lag ada, target terealisasi; test: week == o, lag ada.

    Kolom `y` = y_h (NaN boleh di test), `z` = label target (test: NaN target → 0, D-155), `has_target`.
    target: "end" (titik akhir) | "any" (kejadian dalam jendela, butuh kolom ymax_h)."""
    thr = thresholds(tab, o, h, pct)
    src = f"y_{h}" if target == "end" else f"ymax_{h}"
    t = tab[tab[LAG_COLUMNS].notna().all(1)]
    train = t[(t["week"] + pd.Timedelta(weeks=h) <= o) & np.isfinite(t[src])].copy()
    test = t[t["week"] == o].copy()
    for d in (train, test):
        th = d["commodity"].map(thr).to_numpy(float)
        v = d[src].to_numpy(float)
        d["thr"] = th
        d["y"] = d[f"y_{h}"].to_numpy(float)
        d["has_target"] = np.isfinite(v)
        d["z"] = (np.isfinite(v) & (v >= th)).astype(int)
    return train.reset_index(drop=True), test.reset_index(drop=True), thr


# ---------------------------------------------------------------- metrik
def block(h):
    return int(np.ceil(h / 4)) + 1


def boot_idx(n, h, reps=REPS, seed0=0):
    return np.vstack([moving_block_indices(n, block(h), np.random.default_rng(seed0 + r)) for r in range(reps)])


def top_flags(d, score, group, k=None, frac=None, n=None, seed=154):
    """Tandai baris skor tertinggi per grup (aturan D-154: NaN paling bawah, tie dipecah acak dengan seed tetap).
    k = per grup; frac = porsi grup; n = Series jumlah per grup (mis. setara V1-K2)."""
    s = d[score].fillna(-np.inf).to_numpy()
    tieb = np.random.default_rng(seed).random(len(d))
    order = np.lexsort((tieb, -s))
    rank = pd.Series(np.empty(len(d)), index=d.index)
    tmp = d.iloc[order]
    rank.iloc[order] = tmp.groupby(group).cumcount().to_numpy()
    if k is not None:
        return rank < k
    if frac is not None:
        m = d.groupby(group)[score].transform("size")
        return rank < np.ceil(frac * m)
    return rank < d["origin"].map(n).to_numpy()          # n: Series jumlah alarm per origin (group = ["origin"])


def ap(y, s):
    from sklearn.metrics import average_precision_score
    y = np.asarray(y, int)
    return float(average_precision_score(y, s)) if 0 < y.sum() < len(y) else np.nan


def auc(y, s):
    from sklearn.metrics import roc_auc_score
    y = np.asarray(y, int)
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else np.nan


def brier(y, p):
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def logloss(y, p, eps=1e-6):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def reliability(y, p, bins=10):
    p = np.asarray(p, float)
    b = np.clip((p * bins).astype(int), 0, bins - 1)
    return pd.DataFrame({"b": b, "p": p, "y": np.asarray(y, float)}).groupby("b").agg(p=("p", "mean"), y=("y", "mean"),
                                                                                         n=("y", "size"))


def ece(y, p, bins=10):
    c = reliability(y, p, bins)
    return float((c["n"] * (c["p"] - c["y"]).abs()).sum() / c["n"].sum())


def logit(p, eps=1e-4):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p / (1 - p))


def platt_walkforward(df, score, target="z", h=4, min_origins=6):
    """Kalibrasi Platt global walk-forward: di origin o, latih logit P = a + b·logit(score) pada baris origin o' dengan
    o' + h <= o (label terealisasi). < min_origins origin lampau → None (tidak dievaluasi untuk peluang)."""
    from sklearn.linear_model import LogisticRegression
    out = pd.Series(np.nan, index=df.index)
    uo = np.sort(df["origin"].unique())
    for o in uo:
        past = df[df["origin"] + pd.Timedelta(weeks=h) <= o]
        if past["origin"].nunique() < min_origins or past[target].nunique() < 2:
            continue
        m = LogisticRegression(C=1e6, max_iter=1000).fit(logit(past[score])[:, None], past[target])
        cur = df["origin"] == o
        out[cur] = m.predict_proba(logit(df.loc[cur, score])[:, None])[:, 1]
    return out
