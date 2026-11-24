import sys, json; sys.path.insert(0, r"<EXP_DIR>")
from engine import *
from feats import GROUPS
from sklearn.metrics import roc_auc_score
G = list(GROUPS)
configs = {"C1_base": ([], False)}
for g in G: configs[f"+{g}"] = ([g], False)
configs["all"] = (G, False)
for g in G: configs[f"all-{g}"] = ([x for x in G if x != g], False)
configs["all+fx"] = (G, True)
out = []
for name, (gs, fx) in configs.items():
    row = {"config": name}
    for h in (4, 8):
        with Timer() as t:
            r = run(h, "dev", feature_cols(gs, h, fx), n_jobs=12)
        r.to_parquet(fr"<EXP_DIR>/preds/abl_{name}_h{h}.parquet")
        k = r.y_true != 0
        row[f"f1_h{h}"] = macro_f1(r.y_true, r.p_up)
        row[f"auc_h{h}"] = roc_auc_score(r.y_true[k] > 0, r.p_up[k])
        row[f"sec_h{h}"] = round(t.s, 1)
    row["f1_mean"] = (row["f1_h4"] + row["f1_h8"]) / 2
    out.append(row); print(json.dumps(row), flush=True)
    pd.DataFrame(out).to_csv(r"<EXP_DIR>/ablation.csv", index=False)
