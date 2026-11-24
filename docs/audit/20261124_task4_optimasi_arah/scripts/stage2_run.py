"""Fase 5: TimesFM → fusi fitur → CatBoost. Varian & parameter dipilih di origin pengembangan; lalu semua origin."""
import sys, json; sys.path.insert(0, r"<EXP_DIR>")
import numpy as np, pandas as pd
import stage2
from engine import origin_list, macro_f1, feature_cols, Timer
from feats import cols_for
SEL = ["lag", "rmean", "rstd", "mom", "season", "dev", "comm"]
oof = {}
for hh in (4, 8):
    f = pd.read_parquet(fr"<EXP_DIR>/preds/final_C1t_h{hh}.parquet")
    oof[f"c1t_{hh}"] = f
TFM = ["tfm_4", "tfm_8", "tfm_fx_4", "tfm_fx_8", "tfm_gap", "tfm_fx_diff"]
variants = {"A_tfm": lambda h: TFM, "B_tfm_feat": lambda h: TFM + ["lag_dp_1", "lag_dp_4", "lag_dp_8"] + cols_for(SEL, h),
            "C_tfm_feat_c1t": lambda h: TFM + ["lag_dp_1", "lag_dp_4", "lag_dp_8"] + cols_for(SEL, h) + ["c1t_4", "c1t_8"]}
params = {"P1": {"depth": 4, "learning_rate": 0.05, "iterations": 400}, "P2": {"depth": 6, "learning_rate": 0.05, "iterations": 500},
          "P3": {"depth": 6, "learning_rate": 0.03, "iterations": 800, "l2_leaf_reg": 10}}
frames = {h: stage2.base_frame(h, oof) for h in (4, 8)}
log = open(r"<EXP_DIR>/stage2_dev.jsonl", "a")
import json as _j
res = [_j.loads(l) for l in open(r"<EXP_DIR>/stage2_dev.jsonl")]   # A_tfm P1/P2 sudah dijalankan
for v, colf in variants.items():
    for pn, p in params.items():
        if v == "A_tfm" or pn != "P1":   # grid dipangkas (waktu): B & C hanya P1 (P1 > P2 pada A)
            continue
        f = {}
        with Timer() as t:
            for h in (4, 8):
                r = stage2.run(frames[h], h, origin_list(h, "dev"), colf(h), params=p, n_jobs=3)
                f[h] = macro_f1(r.y_true, r.p_up); n_o = r.origin.nunique()
        row = {"variant": v, "params": pn, "f1_h4": f[4], "f1_h8": f[8], "mean": (f[4] + f[8]) / 2, "n_dev_origins": n_o, "sec": t.s}
        res.append(row); log.write(json.dumps(row) + "\n"); log.flush(); print(json.dumps(row), flush=True)
# pembanding pada origin pengembangan yang SAMA (≥ 8 origin riwayat): C1t & TFM
best = max(res, key=lambda r: r["mean"])
json.dump(best, open(r"<EXP_DIR>/best_stage2.json", "w"))
print("BEST", best, flush=True)
for h in (4, 8):
    r = stage2.run(frames[h], h, origin_list(h, "all"), variants[best["variant"]](h), params=params[best["params"]], n_jobs=3)
    r.to_parquet(fr"<EXP_DIR>/preds/final_TFMhead_h{h}.parquet"); print("final", h, len(r), r.origin.nunique(), flush=True)
