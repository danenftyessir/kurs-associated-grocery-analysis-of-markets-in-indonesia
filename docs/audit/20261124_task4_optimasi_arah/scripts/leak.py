import sys; sys.path.insert(0, r"<EXP_DIR>")
from kg import *
import numpy as np, pandas as pd
from feats import extend, GROUPS
from engine import feature_cols
from kagami.features.forecast import split_origin
pw, dr, wd = load()
tab = pd.read_parquet(r"<EXP_DIR>/tab.parquet")
base = extend(tab, pw)
rng = np.random.default_rng(1)
for o in [pd.Timestamp("2022-06-06"), pd.Timestamp("2024-07-15"), pd.Timestamp("2026-01-05")]:
    t2 = tab.copy(); fut = t2.week > o
    t2.loc[fut, "log_p"] = t2.loc[fut, "log_p"] + rng.normal(0, 0.5, fut.sum())   # rusak semua harga sesudah origin
    pw2 = pw.copy(); pw2.loc[pw2.week > o, "status"] = "missing"
    e2 = extend(t2, pw2)
    cols = sorted(set(feature_cols(list(GROUPS), 4) + feature_cols(list(GROUPS), 8) + ["dev_ma13"]) - {"lag_dp_1","lag_dp_4","lag_dp_8","month","idf_rel_week","db_1","db_4"})
    a = base[base.week <= o].sort_values(["week","province_id","commodity"])[cols].to_numpy(float)
    b = e2[e2.week <= o].sort_values(["week","province_id","commodity"])[cols].to_numpy(float)
    same = np.allclose(np.nan_to_num(a, nan=-9e9), np.nan_to_num(b, nan=-9e9))
    for h in (4, 8):
        tr, te = split_origin(cfg, base, o, h)
        assert (tr.week + pd.Timedelta(weeks=h) <= o).all() and (te.week == o).all()
    print(o.date(), "fitur s.d. origin identik:", same, "| kolom diuji:", len(cols))
