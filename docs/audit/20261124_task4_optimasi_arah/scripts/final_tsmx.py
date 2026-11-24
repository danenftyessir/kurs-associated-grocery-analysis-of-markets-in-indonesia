import sys, json; sys.path.insert(0, r"<EXP_DIR>")
import torch; torch.set_num_threads(12)
import tsmx
from engine import origin_list
from kg import cfg
b = json.load(open(r"<EXP_DIR>/best_tsmx.json"))["best"]
tsmx.arrays()
ords = sorted(set(origin_list(4, "test")) | set(origin_list(8, "test")))
for rep in (1, 2, 3):
    r = tsmx.rolling(b["params"], ords, cfg.seed + 4201 + 1000 * (rep - 1), refit=4)
    dev = __import__("pandas").read_parquet(fr"<EXP_DIR>/preds/tune_tsmx_t{b['trial']}_dev.parquet") if rep == 1 else None
    out = r if dev is None else __import__("pandas").concat([dev, r], ignore_index=True)
    for h in (4, 8):
        out[out.horizon == h].to_parquet(fr"<EXP_DIR>/preds/final_TSMXt_r{rep}_h{h}.parquet")
    print("final rep", rep, len(r), flush=True)
