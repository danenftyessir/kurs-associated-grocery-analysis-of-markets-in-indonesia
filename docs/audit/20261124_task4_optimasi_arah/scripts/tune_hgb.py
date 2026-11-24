"""Optuna TPE untuk klasifier HGB (C1/C2-tuned). Objektif: rerata macro F1 (ambang 0,5) h 4 & 8 pada origin
pengembangan GANJIL; 3 trial teratas dikonfirmasi pada SEMUA origin pengembangan. Origin test final tidak disentuh."""
import sys, json; sys.path.insert(0, r"<EXP_DIR>")
from engine import *
import optuna
name, groups, fx, n_trials = sys.argv[1], sys.argv[2].split(",") if sys.argv[2] else [], sys.argv[3] == "fx", int(sys.argv[4])
odd = {h: origin_list(h, "dev")[1::2] for h in (4, 8)}
log = open(fr"<EXP_DIR>/tune_{name}.jsonl", "a")
def space(t):
    return {"learning_rate": t.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_iter": t.suggest_int("max_iter", 100, 800, step=50),
            "max_leaf_nodes": t.suggest_int("max_leaf_nodes", 7, 63),
            "min_samples_leaf": t.suggest_int("min_samples_leaf", 20, 400, log=True),
            "l2_regularization": t.suggest_float("l2_regularization", 1e-3, 10, log=True),
            "max_features": t.suggest_float("max_features", 0.3, 1.0),
            "balanced": t.suggest_categorical("balanced", [False, True]),
            "decay_years": t.suggest_categorical("decay_years", [0, 1, 2, 4])}
def objective(t):
    p = space(t)
    with Timer() as tm:
        f = {h: macro_f1(*run(h, None, feature_cols(groups, h, fx), params=p, n_jobs=12, origins_=odd[h])[["y_true", "p_up"]].T.values) for h in (4, 8)}
    t.set_user_attr("f1", f)
    log.write(json.dumps({"trial": t.number, "params": p, "f1_h4": f[4], "f1_h8": f[8], "sec": tm.s}) + "\n"); log.flush()
    return (f[4] + f[8]) / 2
st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=20261121, n_startup_trials=10))
st.enqueue_trial({"learning_rate": 0.05, "max_iter": 300, "max_leaf_nodes": 31, "min_samples_leaf": 20, "l2_regularization": 1e-3,
                  "max_features": 1.0, "balanced": False, "decay_years": 0})   # titik awal = hyperparameter resmi
if len(sys.argv) > 5:   # titik awal tambahan (mis. hyperparameter terbaik C1t)
    st.enqueue_trial(json.load(open(sys.argv[5]))["best"]["params"])
optuna.logging.set_verbosity(optuna.logging.WARNING)
st.optimize(objective, n_trials=n_trials)
top = sorted(st.trials, key=lambda t: -(t.value or -1))[:3]
conf = []
for t in top:
    p = {**t.params}
    res = {h: run(h, "dev", feature_cols(groups, h, fx), params=p, n_jobs=12) for h in (4, 8)}
    f = {h: macro_f1(res[h].y_true, res[h].p_up) for h in (4, 8)}
    conf.append({"trial": t.number, "params": p, "odd": t.value, "dev_f1_h4": f[4], "dev_f1_h8": f[8], "dev_mean": (f[4] + f[8]) / 2})
    for h in (4, 8): res[h].to_parquet(fr"<EXP_DIR>/preds/tune_{name}_t{t.number}_h{h}.parquet")
    print(json.dumps(conf[-1]), flush=True)
best = max(conf, key=lambda c: c["dev_mean"])
json.dump({"name": name, "groups": groups, "fx": fx, "best": best, "confirm": conf, "n_trials": n_trials}, open(fr"<EXP_DIR>/best_{name}.json", "w"), indent=1)
print("BEST", json.dumps(best))
