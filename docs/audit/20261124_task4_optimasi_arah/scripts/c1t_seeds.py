import sys, json; sys.path.insert(0, r"<EXP_DIR>")
from engine import *
b = json.load(open(r"<EXP_DIR>/best_C1t.json"))
for s in (2, 3):
    for h in (4, 8):
        r = run(h, "test", feature_cols(b["groups"], h, b["fx"]), params=b["best"]["params"], n_jobs=12, seed=cfg.seed + 1000 * (s - 1))
        r.to_parquet(fr"<EXP_DIR>/preds/final_C1t_s{s}_h{h}.parquet"); print("seed", s, h, len(r), flush=True)
