"""D-150 pilot: C1-tuned (hyperparameter & kolom resmi) + fitur pedagang besar PIHPS, rolling-origin Task 4.

Protokol sama dengan D-147 (`p_exp.py`): seleksi hanya di origin pengembangan; label evaluasi resmi; aturan buka test: Δ macro F1
rerata (h 4, h 8) ≥ +0,005, interval berpasangan > 0 di ≥ 1 horizon, Δ ≥ 0 di horizon lain. Tabel: EXP/ws.parquet (ws_build.py).
Env: PART=dev|test|dev2x|test2 (D-149: dev2x = origin dengan 2023-12-31 < origin + h ≤ 2024-12-31, melengkapi dev split 2;
test2 = origin ≥ 2025-01-01), ONLY=varian1,varian2 (base selalu ikut), NJ (proses), OMP_NUM_THREADS.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import pandas as pd

from p_exp import EXP, fit  # noqa: E402
from kg import cfg  # noqa: E402
from kagami.features.forecast import origins, split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
DEV_END, TEST_START = pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-01")
H = [4, 8]
DP = ["ws_dp_1", "ws_dp_4", "ws_dp_8", "ws_nat_dp_4"]
GAP = ["ws_gap", "ws_gap_dev52", "ws_rel_4"]
VARIANTS = {"base": [], "W_DP": DP, "W_GAP": GAP, "W_ALL": DP + GAP}
_T = {}


def tab():
    if "t" not in _T:
        _T["t"] = pd.read_parquet(os.path.join(EXP, "ws.parquet"))
    return _T["t"]


def one(h, o, names):
    train, test = split_origin(cfg, tab(), o, h)
    out, meta = [], []
    for name in names:
        t0 = time.perf_counter()
        cols = tuned_columns("C1t", h)[0] + [c.format(h=h) for c in VARIANTS[name]]
        p, n_all, n_used = fit(train, test, cols, None, None, h, cfg.seed)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, variant=name, y_true=test["y"].to_numpy(), p_up=p))
        meta.append({"origin": o, "horizon": h, "variant": name, "n_train": n_used, "sec": time.perf_counter() - t0})
    return pd.concat(out, ignore_index=True), pd.DataFrame(meta)


if __name__ == "__main__":
    from joblib import Parallel, delayed
    part = os.environ.get("PART", "dev")
    only = [v for v in os.environ.get("ONLY", "").split(",") if v]
    names = ["base"] + only if only else list(VARIANTS)
    weeks = tab()["week"].drop_duplicates()
    if part == "dev":
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h) if o + pd.Timedelta(weeks=h) <= DEV_END]
    elif part == "dev2x":
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h)
                if DEV_END < o + pd.Timedelta(weeks=h) <= pd.Timestamp("2024-12-31")]
    elif part == "test2":
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h) if o >= pd.Timestamp("2025-01-01")]
    else:
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h) if o >= TEST_START]
    print(part, "pekerjaan", len(jobs), "varian", names)
    t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=5)(delayed(one)(h, o, names) for h, o in jobs)
    pd.concat([r[0] for r in res], ignore_index=True).to_parquet(os.path.join(EXP, f"ws_{part}_preds.parquet"))
    pd.concat([r[1] for r in res], ignore_index=True).to_csv(os.path.join(OUT, f"ws_{part}_meta.csv"), index=False)
    print("selesai", round(time.time() - t0), "dtk")
