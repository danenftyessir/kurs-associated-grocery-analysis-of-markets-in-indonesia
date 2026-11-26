"""Uji mandiri skrip K4 pada data sintetis (tanpa data asli; jalankan: python k4_selftest.py).

1. fast_ap / fast_auc = sklearn (termasuk skor kembar & NaN).
2. thresholds(): hanya baris dengan week + h ≤ origin; mengubah y masa depan tidak mengubah ambang.
3. split_k4(): label latih memakai ambang origin; target hilang di uji → z = 0, has_target False.
4. add_event(): ymax = max_{k≤h}(p_{t+k} − p_t) dengan minggu hilang dilewati.
5. platt_walkforward(): origin dengan < 6 origin lampau terealisasi → NaN; label sesudah origin tidak memengaruhi peluang.
6. top_flags(k=2): tepat 2 per (origin, provinsi), skor tertinggi.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import k4_common as kc  # noqa: E402
from k4_eval import fast_ap, fast_auc  # noqa: E402
from kagami.features.forecast import LAG_COLUMNS  # noqa: E402


def synth(seed=0, n_weeks=120, n_prov=3, comms=("a", "b")):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2019-01-07", periods=n_weeks, freq="7D")
    rows = []
    for p in range(1, n_prov + 1):
        for c in comms:
            lp = np.cumsum(rng.normal(0, 0.03 if c == "a" else 0.1, n_weeks)) + 9
            for i, w in enumerate(weeks):
                rows.append({"week": w, "province_id": p, "commodity": c, "log_p": lp[i]})
    t = pd.DataFrame(rows).sort_values(["province_id", "commodity", "week"]).reset_index(drop=True)
    g = t.groupby(["province_id", "commodity"])["log_p"]
    for h in kc.H:
        t[f"y_{h}"] = g.shift(-h) - t["log_p"]
    for c in LAG_COLUMNS:
        t[c] = g.diff(int(c.split("_")[-1]))
    return t


def test_ap_auc():
    from sklearn.metrics import average_precision_score, roc_auc_score
    rng = np.random.default_rng(1)
    y = (rng.random(500) < 0.15).astype(int)
    for s in (rng.random(500), np.round(rng.random(500), 1), (y + rng.normal(0, 1, 500)).round(0)):
        assert abs(fast_ap(y, s) - average_precision_score(y, s)) < 1e-12
        assert abs(fast_auc(y, s) - roc_auc_score(y, s)) < 1e-12
    s = rng.random(500)
    s[:20] = np.nan
    assert abs(fast_ap(y, s) - average_precision_score(y, np.where(np.isnan(s), -1e18, s))) < 1e-12


def test_thresholds_no_future():
    t = synth()
    o = t["week"].iloc[80]
    for h in kc.H:
        a = kc.thresholds(t, o, h)
        u = t.copy()
        fut = u["week"] + pd.Timedelta(weeks=h) > o
        u.loc[fut, f"y_{h}"] = 5.0
        b = kc.thresholds(u, o, h)
        assert np.allclose(a.to_numpy(), b.to_numpy())
        tr = t[(t["week"] + pd.Timedelta(weeks=h) <= o) & t[f"y_{h}"].notna() & t[LAG_COLUMNS].notna().all(1)]
        exp = tr.groupby("commodity")[f"y_{h}"].apply(lambda s: np.percentile(s.abs(), 80))
        assert np.allclose(a.to_numpy(), exp.to_numpy())


def test_split_labels_and_missing():
    t = synth()
    o = t["week"].iloc[90]
    t.loc[(t["week"] == o) & (t["province_id"] == 1), "y_4"] = np.nan
    tr, te, thr = kc.split_k4(t, o, 4)
    assert (tr["week"] + pd.Timedelta(weeks=4) <= o).all()
    assert ((tr["y"] >= tr["commodity"].map(thr)).astype(int) == tr["z"]).all()
    miss = te[te["province_id"] == 1]
    assert (~miss["has_target"]).all() and (miss["z"] == 0).all()


def test_event_max():
    weeks = pd.date_range("2020-01-06", periods=12, freq="7D")
    lp = pd.DataFrame({(1, "a"): [0, 0.1, 0.5, np.nan, 0.2, 0.0, 0, 0, 0, 0, 0, 0]}, index=weeks, dtype=float)
    lp.columns = pd.MultiIndex.from_tuples(lp.columns, names=["province_id", "commodity"])
    kc._T["lp"] = lp
    tab = pd.DataFrame({"week": weeks, "province_id": 1, "commodity": "a"})
    out = kc.add_event(tab)
    r = out.set_index("week")
    assert np.isclose(r.loc[weeks[0], "ymax_4"], 0.5)          # max(0.1, 0.5, NaN dilewati, 0.2)
    assert np.isclose(r.loc[weeks[2], "ymax_4"], -0.3)         # dari 0.5: (NaN, 0.2, 0, 0) → −0.3
    assert np.isclose(r.loc[weeks[0], "ymax_8"], 0.5)
    assert np.isnan(r.loc[weeks[3], "ymax_4"])                 # p_t hilang
    kc._T.pop("lp")


def test_platt_walkforward():
    rng = np.random.default_rng(3)
    origins = pd.date_range("2021-01-04", periods=14, freq="28D")
    d = pd.DataFrame({"origin": np.repeat(origins, 200), "s": rng.random(14 * 200)})
    d["z"] = (rng.random(len(d)) < d["s"] * 0.4).astype(int)
    p = kc.platt_walkforward(d, "s", "z", h=4)
    first_ok = d.loc[p.notna(), "origin"].min()
    assert first_ok == origins[6]                               # ≥ 6 origin lampau dengan o' + 4 minggu ≤ o
    u = d.copy()
    last = u["origin"] == origins[-1]
    u.loc[last, "z"] = 1 - u.loc[last, "z"]                     # label origin terakhir tidak boleh dipakai di origin itu
    q = kc.platt_walkforward(u, "s", "z", h=4)
    assert np.allclose(p[last], q[last])
    p8 = kc.platt_walkforward(d, "s", "z", h=8)
    assert d.loc[p8.notna(), "origin"].min() == origins[7]


def test_top_flags():
    rng = np.random.default_rng(4)
    d = pd.DataFrame({"origin": np.repeat([1, 2], 30), "province_id": np.tile(np.repeat([1, 2, 3], 10), 2), "s": rng.random(60)})
    f = kc.top_flags(d, "s", ["origin", "province_id"], k=2)
    assert (d.assign(f=f).groupby(["origin", "province_id"])["f"].sum() == 2).all()
    top = d.assign(f=f).sort_values("s", ascending=False).groupby(["origin", "province_id"]).head(2)
    assert top["f"].all()


if __name__ == "__main__":
    for fn in [v for k, v in dict(globals()).items() if k.startswith("test_")]:
        fn()
        print("lolos", fn.__name__)
