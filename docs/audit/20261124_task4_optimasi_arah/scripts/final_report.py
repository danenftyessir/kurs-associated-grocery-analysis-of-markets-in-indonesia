import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

import evalx
import report

S = os.path.dirname(__file__)
spec = {"C1t": ("final_C1t_h{h}.parquet", "prob", "p_up"), "C2t": ("final_C2t_h{h}.parquet", "prob", "p_up"),
        "TFMhead": ("final_TFMhead_h{h}.parquet", "prob", "p_up"), "TFMcal": ("tfmcal_h{h}.parquet", "prob", "p_up")}
for r in (1, 2, 3):
    if os.path.exists(os.path.join(S, "preds", f"final_TSMXt_r{r}_h8.parquet")):
        import json
        loss = json.load(open(os.path.join(S, "best_tsmx.json")))["best"]["params"]["loss"]
        spec[f"TSMXt_r{r}" if r > 1 else "TSMXt"] = (f"final_TSMXt_r{r}_h{{h}}.parquet",
                                                    "prob" if loss == "bce" else "reg", "score")
for r in (2, 3):
    if os.path.exists(os.path.join(S, "preds", f"final_C1t_s{r}_h8.parquet")):
        spec[f"C1t_s{r}"] = (f"final_C1t_s{r}_h{{h}}.parquet", "prob", "p_up")
D, Z = "dev", "default"
comps = [(("C1t", D), ("C1", Z)), (("C1t", D), ("C2", Z)), (("C1t", D), ("TFM", Z)), (("C1t", D), ("TFM", D)),
         (("C1t", D), ("C1t", Z)), (("C2t", D), ("C1t", D)), (("TFMhead", D), ("TFM", Z)), (("TFMhead", D), ("C1t", D)),
         (("TFMcal", D), ("TFM", Z)), (("TFM", D), ("TFM", Z)), (("TSMXt", "default"), ("TSMX", Z)),
         (("TSMXt", D), ("TSMX", D)), (("C1", D), ("C1", Z))]
res, comp = report.main(spec, comps, os.path.join(S, "final.md"), os.path.join(S, "final.json"))

# per komoditas (ambang dev), model kunci
keyrows = res[(res.threshold.isin(["dev", "default"]))]
pick = {}
for _, r in keyrows.iterrows():
    k = (r.model, r.h)
    if k not in pick or r.threshold == "dev":
        pick[k] = r
pc = pd.DataFrame({f"{m}|h{h}": r.per_commodity for (m, h), r in pick.items()
                   if m in ("C1", "C2", "M3", "TFM", "TSMX", "C1t", "TFMhead", "TSMXt")}).T
pc.round(3).to_csv(os.path.join(S, "final_per_commodity.csv"))
print(pc.round(3).to_string())
print(comp.round(4).to_string(index=False))
