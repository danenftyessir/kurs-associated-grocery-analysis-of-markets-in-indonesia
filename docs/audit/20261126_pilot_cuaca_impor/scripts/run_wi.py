"""D-157: run rolling-origin base / W_NAT / W_LOC / IMP pada origin pengembangan (PROTOKOL.md §2). Checkpoint EXP/d157/h<h>_<origin>.parquet."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, H, cfg, dev_origins, np, pd, table  # noqa: E402
from m_run import fit_predict  # noqa: E402
from kagami.features.forecast import split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402
import feats_wi as F  # noqa: E402


def variants(h):
    b = tuned_columns("C1t", h)[0]
    return {"base": {"cols": b}, "W_NAT": {"cols": b + F.W_NAT}, "W_LOC": {"cols": b + F.W_NAT + F.W_LOC},
            "IMP": {"cols": b + F.IMP}}


def job(h, o):
    path = os.path.join(EXP, "d157", f"h{h}_{o.date()}.parquet")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return path
    train, test = split_origin(cfg, table("cw"), o, h)
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    out = []
    for name, spec in variants(h).items():
        t0 = time.perf_counter()
        p = fit_predict(tr, test, spec, o)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, variant=name, y_true=test["y"].to_numpy(),
                                                             score=p, sec=time.perf_counter() - t0))
    pd.concat(out, ignore_index=True).to_parquet(path)
    return path


if __name__ == "__main__":
    from joblib import Parallel, delayed
    jobs = [(h, o) for h in H for o in dev_origins(h)]
    t0 = time.time()
    Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=5)(delayed(job)(h, o) for h, o in jobs)
    print("selesai", round(time.time() - t0), "dtk", flush=True)
