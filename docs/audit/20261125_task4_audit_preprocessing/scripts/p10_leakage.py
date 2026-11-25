"""P10: uji kebocoran menyeluruh pada SEMUA origin Task 4 (h 4 & 8), seluruh matriks fitur (resmi + dinamika harga D-145).

Untuk setiap origin o:
  T1 perturbasi : log harga, status, penggerak (minggu > o) dan harga dunia (available_at > o) dirusak acak;
  T2 penghapusan: semua baris itu dihapus;
→ tabel dibangun ulang (`feature_table` + `price_dynamics.extend_table`) dan dibandingkan dengan tabel penuh:
  semua kolom non-target pada minggu ≤ o harus identik (NaN = NaN); target y_h pada minggu t + h ≤ o harus identik
  (itulah baris latih origin o).
  T3 episode     : flag `episode` (fitur grup fx) dibandingkan dengan flag yang dihitung ulang hanya dari de s.d. o.
Keluaran: hasil/p10_leakage.csv (satu baris per origin × uji).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from kg import cfg, load  # noqa: E402
from kagami.data.drivers import find_episodes, mark_episode_weeks  # noqa: E402
from kagami.features import price_dynamics  # noqa: E402
from kagami.features.forecast import feature_table, origins  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "hasil")
H = [4, 8]
KEYS = ["week", "province_id", "commodity"]


def build(panel, drivers, world):
    return price_dynamics.extend_table(feature_table(cfg, panel, drivers, world, H), panel, H)


def compare(full, other, o):
    feat = [c for c in full.columns if not c.startswith("y_") and c not in KEYS and c != "region"]
    a = full[full["week"] <= o].set_index(KEYS).sort_index()
    b = other[other["week"] <= o].set_index(KEYS).sort_index()
    if not a.index.equals(b.index):
        return {"rows_equal": False, "n_feat_cols_diff": -1, "n_cells_diff": -1, "target_diff": -1}
    bad_cols, n_bad = [], 0
    for c in feat:
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) or pd.api.types.is_datetime64_any_dtype(x):
            xv, yv = x.to_numpy(), y.to_numpy()
            if pd.api.types.is_datetime64_any_dtype(x):
                eq = (xv == yv) | (pd.isna(xv) & pd.isna(yv))
            else:
                xv, yv = xv.astype(float), yv.astype(float)
                eq = (xv == yv) | (np.isnan(xv) & np.isnan(yv))
        else:
            eq = (x.astype(str).to_numpy() == y.astype(str).to_numpy())
        if not eq.all():
            bad_cols.append(c)
            n_bad += int((~eq).sum())
    tdiff = 0
    for h in H:
        m = a.index.get_level_values("week") + pd.Timedelta(weeks=h) <= o
        xv, yv = a.loc[m, f"y_{h}"].to_numpy(float), b.loc[m, f"y_{h}"].to_numpy(float)
        tdiff += int((~((xv == yv) | (np.isnan(xv) & np.isnan(yv)))).sum())
    return {"rows_equal": True, "n_feat_cols": len(feat), "n_feat_cols_diff": len(bad_cols), "n_cells_diff": n_bad,
            "target_diff": tdiff, "bad_cols": ",".join(bad_cols[:10])}


def one(o, full, panel, drivers, world):
    rng = np.random.default_rng(int(o.value // 10**9) % 2**31)
    res = []
    # T1 perturbasi
    p1 = panel.copy()
    f = p1["week"] > o
    p1.loc[f, "log_price"] = p1.loc[f, "log_price"] + rng.normal(0, 0.5, f.sum())
    p1.loc[f, "price"] = np.exp(p1.loc[f, "log_price"])
    p1.loc[f, "status"] = rng.choice(["observed", "carry_forward", "short", "missing"], f.sum())
    d1 = drivers.copy()
    g = d1["week"] > o
    for c in ("log_e", "log_brent", "de", "db", "episode"):
        if c in d1:
            d1.loc[g, c] = d1.loc[g, c] + (rng.integers(0, 2, g.sum()) if c == "episode" else rng.normal(0, 0.3, g.sum()))
    w1 = world.copy()
    k = w1["available_at"] > o
    w1.loc[k, "log_w_idr"] = w1.loc[k, "log_w_idr"] + rng.normal(0, 0.5, k.sum())
    res.append({"origin": o, "test": "T1_perturb", **compare(full, build(p1, d1, w1), o)})
    # T2 penghapusan
    res.append({"origin": o, "test": "T2_delete",
                **compare(full, build(panel[panel["week"] <= o], drivers[drivers["week"] <= o],
                                      world[world["available_at"] <= o]), o)})
    # T3 flag episode real-time
    d_o = drivers[drivers["week"] <= o]
    rt = mark_episode_weeks(d_o.drop(columns="episode"), find_episodes(cfg, d_o)).set_index("week")["episode"]
    off = drivers.set_index("week")["episode"].reindex(rt.index)
    diff_weeks = rt.index[(rt != off).to_numpy()]
    res.append({"origin": o, "test": "T3_episode_flag", "rows_equal": True, "n_cells_diff": len(diff_weeks),
                "origin_flag_official": int(off.loc[o]), "origin_flag_realtime": int(rt.loc[o]),
                "bad_cols": ",".join(str(w.date()) for w in diff_weeks[-5:])})
    return res


if __name__ == "__main__":
    panel, drivers, world = load()
    t0 = time.time()
    full = build(panel, drivers, world)
    print("tabel penuh", full.shape, round(time.time() - t0, 1), "dtk")
    os_ = sorted(set(origins(cfg, full["week"].drop_duplicates(), 4)) | set(origins(cfg, full["week"].drop_duplicates(), 8)))
    print("origin", len(os_))
    res = Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=5)(delayed(one)(o, full, panel, drivers, world) for o in os_)
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv(os.path.join(OUT, "p10_leakage.csv"), index=False)
    print(df.groupby("test")[["n_feat_cols_diff", "n_cells_diff", "target_diff"]].agg(["sum", "max"]).to_string())
    t3 = df[df.test == "T3_episode_flag"]
    print("origin dengan flag episode resmi ≠ real-time pada minggu origin:",
          int((t3.origin_flag_official != t3.origin_flag_realtime).sum()), "dari", len(t3))
    print("total", round(time.time() - t0, 1), "dtk")
