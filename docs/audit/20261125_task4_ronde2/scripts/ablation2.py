import os, sys, json; sys.path.insert(0, r"<EXP_DIR>")
os.environ["KAGAMI_EXT"] = "ext2.parquet"
from engine import *
from feats import cols_for
from feats2 import GROUPS2, cols2
import evalx
SEL = ["lag", "rmean", "rstd", "mom", "season", "dev", "comm"]
P = json.load(open(r"<EXP_DIR>/best_C1t.json"))["best"]["params"]
def cols(h, g2): return BASE + cols_for(SEL, h) + cols2(g2, h)
configs = {"S": []}
for g in GROUPS2: configs[f"S+{g}"] = [g]
configs["S+all2"] = list(GROUPS2)
out, preds = [], {}
for name, g2 in configs.items():
    row = {"config": name}
    for h in (4, 8):
        with Timer() as t:
            r = run(h, "dev", cols(h, g2), params=P, n_jobs=12)
        r.to_parquet(fr"<EXP_DIR>/preds/abl2_{name}_h{h}.parquet"); preds[(name, h)] = r.rename(columns={"p_up": "score"})
        row[f"f1_h{h}"] = macro_f1(r.y_true, r.p_up); row[f"sec_h{h}"] = round(t.s)
        if name != "S":
            d = evalx.paired_diff(preds[(name, h)], preds[("S", h)], 0.5, 0.5, h)
            row[f"d_h{h}"], row[f"lo_h{h}"], row[f"hi_h{h}"], row[f"p_h{h}"] = d["diff"], d["lo"], d["hi"], d["p"]
    row["f1_mean"] = (row["f1_h4"] + row["f1_h8"]) / 2
    out.append(row); print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    pd.DataFrame(out).to_csv(r"<EXP_DIR>/ablation2.csv", index=False)
