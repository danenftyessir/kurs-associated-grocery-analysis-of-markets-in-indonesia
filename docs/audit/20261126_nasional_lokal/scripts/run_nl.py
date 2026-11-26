"""D-158: run rolling-origin kandidat pada origin pengembangan. Env STAGE = nl (tabel nl: base, NL1, NL2) | br (tabel br: base, BR_NAT,
BR_LOC, NL_BR) | i2 (tabel i2: kandidat iterasi 2, lihat PROTOKOL_I2.md). Checkpoint EXP/d158/<STAGE>/h<h>_<origin>.parquet."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import EXP, H, cfg, dev_origins, np, pd, table  # noqa: E402
from m_run import fit_predict  # noqa: E402
from kagami.features.forecast import split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402

KB = ["kb_up_1", "kb_up_4", "kb_down_4", "kb_accel", "kb_med_4", "kb_p90_4", "kb_disp_4", "kb_persist", "kb_cov"]
KP = ["kp_up_4", "kp_disp_4", "kp_n", "kp_rel_up_4"]
STAGE = os.environ.get("STAGE", "nl")
TAB = {"nl": "nl", "br": "br", "i2": "fresh"}[STAGE]


def variants(h):
    b = tuned_columns("C1t", h)[0]
    if STAGE == "nl":
        return {"base": {"cols": b}, "NL1": {"cols": b + [f"nat_hat_h{h}"]}, "NL2": {"cols": b + [f"nat_hat_h{h}", f"follow_h{h}"]}}
    if STAGE == "br":
        return {"base": {"cols": b}, "BR_NAT": {"cols": b + KB}, "BR_LOC": {"cols": b + KB + KP},
                "NL_BR": {"cols": b + [f"nat_hat_br_h{h}"]}}
    import i2_spec
    return i2_spec.variants(h, b)


def job(h, o):
    path = os.path.join(EXP, "d158", STAGE, f"h{h}_{o.date()}.parquet")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return path
    train, test = split_origin(cfg, table(TAB), o, h)
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    out = []
    for name, spec in variants(h).items():
        t0 = time.perf_counter()
        p = spec["fn"](tr, test, h, o) if "fn" in spec else fit_predict(tr, test, spec, o)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, variant=name, y_true=test["y"].to_numpy(),
                                                             score=p, sec=time.perf_counter() - t0))
    pd.concat(out, ignore_index=True).to_parquet(path)
    return path


if __name__ == "__main__":
    from joblib import Parallel, delayed
    jobs = [(h, o) for h in H for o in dev_origins(h)]
    t0 = time.time()
    Parallel(n_jobs=int(os.environ.get("NJ", 5)), verbose=2)(delayed(job)(h, o) for h, o in jobs)
    print(STAGE, "selesai", round(time.time() - t0), "dtk", flush=True)
