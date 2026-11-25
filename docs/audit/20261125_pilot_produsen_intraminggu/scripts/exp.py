"""D-151: C1-tuned (kolom & hyperparameter resmi) + fitur keluarga A (intraminggu) / B (produsen), rolling-origin Task 4.

Protokol: ../PROTOKOL.md (seleksi hanya di origin pengembangan, label resmi, aturan buka test tetap).
Env: FAM=iw|pr (tabel EXP/<FAM>.parquet), PART=dev|test, ONLY=varian1,varian2 (base selalu ikut), NJ, OMP_NUM_THREADS.
Keluaran: EXP/d151_<FAM>_<PART>_preds.parquet, hasil/<FAM>_<PART>_meta.csv.
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
IW_FULL = ["iw_gap", "iw_return", "iw_range", "iw_vol", "iw_n_days", "iw_last_age"]
PR_DYN = ["pr_dp_1", "pr_dp_4", "pr_dp_8", "pr_vol_13", "pr_age"]
PR_GAP = ["pr_gap", "pr_gap_chg_1", "pr_gap_chg_4", "pr_gap_chg_8", "pr_gap_dev52"]
PR_NAT = ["pr_nat_dp_1", "pr_nat_dp_4", "pr_nat_dp_8", "pr_nat_up_4", "pr_nat_disp_4", "pr_nat_n"]
FAMILIES = {
    "iw": {"base": [], "IW_REF": ["iw_gap", "iw_n_days"], "IW_FULL": IW_FULL,
           "IW_NAT": IW_FULL + ["iw_gap_nat", "iw_return_nat"]},
    "pr": {"base": [], "PR_DYN": PR_DYN, "PR_TRANS": PR_DYN + PR_GAP, "PR_ALL": PR_DYN + PR_GAP + PR_NAT},
}
FAM = os.environ.get("FAM", "iw")
VARIANTS = FAMILIES[FAM]
_T = {}


def tab():
    if "t" not in _T:
        _T["t"] = pd.read_parquet(os.path.join(EXP, f"{FAM}.parquet"))
    return _T["t"]


def one(h, o, names):
    train, test = split_origin(cfg, tab(), o, h)
    out, meta = [], []
    for name in names:
        t0 = time.perf_counter()
        cols = tuned_columns("C1t", h)[0] + VARIANTS[name]
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
    elif part == "test":
        jobs = [(h, o) for h in H for o in origins(cfg, weeks, h) if o >= TEST_START]
    else:
        raise SystemExit(f"PART tidak dikenal: {part}")
    print(FAM, part, "pekerjaan", len(jobs), "varian", names, flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=2)(delayed(one)(h, o, names) for h, o in jobs)
    pd.concat([r[0] for r in res], ignore_index=True).to_parquet(os.path.join(EXP, f"d151_{FAM}_{part}_preds.parquet"))
    pd.concat([r[1] for r in res], ignore_index=True).to_csv(os.path.join(OUT, f"{FAM}_{part}_meta.csv"), index=False)
    print("selesai", round(time.time() - t0), "dtk", flush=True)
