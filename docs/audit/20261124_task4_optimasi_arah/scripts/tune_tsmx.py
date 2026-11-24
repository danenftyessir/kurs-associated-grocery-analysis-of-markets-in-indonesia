"""Optuna untuk TSMixer arah (loss L1 regresi atau BCE arah). Objektif: rerata macro F1 h 4 & 8 pada origin
pengembangan (refit tiap 8 origin saat tuning). Test final tidak disentuh."""
import sys, json, time; sys.path.insert(0, r"<EXP_DIR>")
import torch; torch.set_num_threads(12)
import tsmx
from engine import origin_list, macro_f1, DEV_END
import optuna, numpy as np, pandas as pd
from kg import cfg
n_trials = int(sys.argv[1])
tsmx.arrays()
dev = {h: origin_list(h, "dev") for h in (4, 8)}
ords = sorted(set(dev[4]) | set(dev[8]))
log = open(r"<EXP_DIR>/tune_tsmx.jsonl", "a")
def evaluate(hp, refit, seed):
    r = tsmx.rolling(hp, ords, seed, refit=refit)
    thr = 0.5 if hp.get("loss") == "bce" else 0.0
    f = {h: macro_f1(*r[(r.horizon == h) & r.origin.isin(dev[h])][["y_true", "score"]].T.values, thr) for h in (4, 8)}
    return f, r
def objective(t):
    hp = {"lookback": t.suggest_categorical("lookback", [26, 52, 104]), "d_model": t.suggest_categorical("d_model", [16, 32, 64]),
          "n_layers": t.suggest_int("n_layers", 1, 3), "dropout": t.suggest_float("dropout", 0.0, 0.3),
          "lr": t.suggest_float("lr", 3e-4, 3e-3, log=True), "epochs": t.suggest_categorical("epochs", [4, 8]),
          "weight_decay": t.suggest_float("weight_decay", 1e-5, 1e-2, log=True), "loss": t.suggest_categorical("loss", ["l1", "bce"])}
    t0 = time.time()
    f, _ = evaluate(hp, 8, cfg.seed + 4201)
    log.write(json.dumps({"trial": t.number, "hp": hp, "f1_h4": f[4], "f1_h8": f[8], "sec": time.time() - t0}) + "\n"); log.flush()
    return (f[4] + f[8]) / 2
st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=20261121, n_startup_trials=6))
st.enqueue_trial({"lookback": 52, "d_model": 32, "n_layers": 2, "dropout": 0.1, "lr": 1e-3, "epochs": 4, "weight_decay": 1e-5, "loss": "l1"})
st.enqueue_trial({"lookback": 52, "d_model": 32, "n_layers": 2, "dropout": 0.1, "lr": 1e-3, "epochs": 4, "weight_decay": 1e-5, "loss": "bce"})
optuna.logging.set_verbosity(optuna.logging.WARNING)
st.optimize(objective, n_trials=n_trials)
top = sorted(st.trials, key=lambda t: -(t.value or -1))[:2]
conf = []
for t in top:   # konfirmasi dengan refit tiap 4 origin (= protokol D-142)
    f, r = evaluate(t.params, 4, cfg.seed + 4201)
    r.to_parquet(fr"<EXP_DIR>/preds/tune_tsmx_t{t.number}_dev.parquet")
    conf.append({"trial": t.number, "params": t.params, "tune": t.value, "dev_f1_h4": f[4], "dev_f1_h8": f[8], "dev_mean": (f[4] + f[8]) / 2})
    print(json.dumps(conf[-1]), flush=True)
best = max(conf, key=lambda c: c["dev_mean"])
json.dump({"best": best, "confirm": conf, "n_trials": n_trials}, open(r"<EXP_DIR>/best_tsmx.json", "w"), indent=1)
print("BEST", json.dumps(best))
