import sys, time; sys.path.insert(0, r"<EXP_DIR>")
from kg import *
import numpy as np, pandas as pd
from feats2 import extend2, GROUPS2, cols2
ext = pd.read_parquet(r"<EXP_DIR>/ext.parquet")
t0 = time.time(); e2 = extend2(cfg, ext); print(e2.shape, round(time.time() - t0, 1))
e2.to_parquet(r"<EXP_DIR>/ext2.parquet")
cols = cols2(list(GROUPS2), 4) + cols2(["prior"], 8)
print(e2[cols].describe().T[["count", "mean", "std", "min", "max"]].round(3).to_string())
print(e2[e2.reg_active == 1].groupby("commodity").week.min())
# uji kebocoran: rusak harga sesudah origin
rng = np.random.default_rng(1)
for o in [pd.Timestamp("2022-06-20"), pd.Timestamp("2025-03-24")]:
    bad = ext.copy(); f = bad.week > o
    bad.loc[f, "log_p"] += rng.normal(0, 0.5, f.sum())
    b2 = extend2(cfg, bad)
    k = ["week", "province_id", "commodity"]
    a = e2[e2.week <= o].sort_values(k)[cols].to_numpy(float); b = b2[b2.week <= o].sort_values(k)[cols].to_numpy(float)
    print(o.date(), "fitur s.d. origin identik:", np.allclose(np.nan_to_num(a, nan=-9e9), np.nan_to_num(b, nan=-9e9)))
