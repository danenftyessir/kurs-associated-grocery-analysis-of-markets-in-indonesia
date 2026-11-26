"""Uji kebocoran fitur keluarga baru (D-156): untuk setiap origin uji, (T1) rusak acak log_p/status/n_days minggu > origin dan
(T2) hapus baris minggu > origin, bangun ulang fitur, bandingkan semua kolom pada minggu ≤ origin. Harus 0 sel berbeda.
Origin uji = 12 origin tersebar 2021–2026 (fitur saja, tanpa label/prediksi). Keluaran hasil/c_leak.csv.
"""
import os

import numpy as np
import pandas as pd

from c_feats import build
from m_common import OUT, cfg, table
from kagami.features.forecast import origins

base = table()[["week", "province_id", "commodity", "log_p", "st0", "n_days"]].copy()
ref = build(base)
os_ = origins(cfg, base["week"].drop_duplicates(), 4)
pick = [os_[i] for i in np.linspace(0, len(os_) - 1, 12).astype(int)]
rng = np.random.default_rng(156)
rows = []
for o in pick:
    keep = base["week"] <= o
    t1 = base.copy()
    fut = ~keep
    t1.loc[fut, "log_p"] = rng.normal(9, 1, fut.sum())
    t1.loc[fut, "st0"] = rng.choice(["observed", "carry_forward", "missing"], fut.sum())
    t1.loc[fut, "n_days"] = rng.integers(0, 6, fut.sum())
    f1 = build(t1)
    t2 = base[keep].copy()
    f2 = build(t2)
    for c in ref.columns:
        a = ref.loc[keep, c].to_numpy(float)
        b1 = f1.loc[keep, c].to_numpy(float)
        b2 = f2[c].to_numpy(float)
        d1 = int((~(np.isclose(a, b1, atol=1e-12) | (np.isnan(a) & np.isnan(b1)))).sum())
        d2 = int((~(np.isclose(a, b2, atol=1e-12) | (np.isnan(a) & np.isnan(b2)))).sum())
        rows.append({"origin": o.date(), "column": c, "diff_T1_perturb": d1, "diff_T2_delete": d2})
    print(o.date(), "selesai", flush=True)
r = pd.DataFrame(rows)
r.to_csv(os.path.join(OUT, "c_leak.csv"), index=False)
bad = r[(r["diff_T1_perturb"] > 0) | (r["diff_T2_delete"] > 0)]
print("origin:", len(pick), "kolom:", r["column"].nunique(), "sel berbeda T1/T2:", int(r["diff_T1_perturb"].sum()), int(r["diff_T2_delete"].sum()))
print(bad.groupby("column")[["diff_T1_perturb", "diff_T2_delete"]].sum().to_string() if len(bad) else "0 kolom bocor")
