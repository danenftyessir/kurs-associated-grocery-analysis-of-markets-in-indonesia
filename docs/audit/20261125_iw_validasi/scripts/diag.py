"""D-152 diagnostik pengembangan (PROTOKOL.md §2): IW_NAT_LOO, IW_BREADTH, IW_NAT_NOFRI di atas C1-tuned; tidak membuka test.

Prediksi base / IW_FULL / IW_NAT diambil dari D-151 (EXP/d151_iw_dev_preds.parquet, deterministik, baris sama).
Keluaran: EXP/d152_diag_dev_preds.parquet, hasil/diag_dev_{meta,metrics,paired,per_commodity}.csv.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from evalx import full_metrics, paired_diff, per_commodity  # noqa: E402
from kg import cfg  # noqa: E402
from p_exp import EXP, fit  # noqa: E402
from kagami.features.forecast import origins, split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
DEV_END = pd.Timestamp("2023-12-31")
IW_FULL = ["iw_gap", "iw_return", "iw_range", "iw_vol", "iw_n_days", "iw_last_age"]
LOO = ["iw_gap_nat_loo", "iw_return_nat_loo"]
VARIANTS = {
    "IW_NAT_LOO": IW_FULL + LOO,
    "IW_BREADTH": IW_FULL + LOO + ["iw_up_share_loo", "iw_down_share_loo"],
    "IW_NAT_NOFRI": ["nf_" + c for c in IW_FULL + ["iw_gap_nat", "iw_return_nat"]],
}
_T = {}


def tab():
    if "t" not in _T:
        _T["t"] = pd.read_parquet(os.path.join(EXP, "iw2.parquet"))
    return _T["t"]


def one(h, o):
    train, test = split_origin(cfg, tab(), o, h)
    out, meta = [], []
    for name, extra in VARIANTS.items():
        t0 = time.perf_counter()
        p, _, n_used = fit(train, test, tuned_columns("C1t", h)[0] + extra, None, None, h, cfg.seed)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, variant=name, y_true=test["y"].to_numpy(), p_up=p))
        meta.append({"origin": o, "horizon": h, "variant": name, "n_train": n_used, "sec": time.perf_counter() - t0})
    return pd.concat(out, ignore_index=True), pd.DataFrame(meta)


if __name__ == "__main__":
    from joblib import Parallel, delayed
    weeks = tab()["week"].drop_duplicates()
    jobs = [(h, o) for h in (4, 8) for o in origins(cfg, weeks, h) if o + pd.Timedelta(weeks=h) <= DEV_END]
    t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=2)(delayed(one)(h, o) for h, o in jobs)
    new = pd.concat([r[0] for r in res], ignore_index=True)
    pd.concat([r[1] for r in res], ignore_index=True).to_csv(os.path.join(OUT, "diag_dev_meta.csv"), index=False)
    old = pd.read_parquet(os.path.join(EXP, "d151_iw_dev_preds.parquet"))
    old = old[old["variant"].isin(["base", "IW_FULL", "IW_NAT"])]
    preds = pd.concat([old, new], ignore_index=True)
    preds.to_parquet(os.path.join(EXP, "d152_diag_dev_preds.parquet"))
    print("prediksi selesai", round(time.time() - t0), "dtk", flush=True)

    preds = preds.rename(columns={"p_up": "score"})
    preds = preds[np.isfinite(preds["y_true"])]
    rows, pairs, pcs = [], [], []
    for h in (4, 8):
        ph = preds[preds["horizon"] == h]
        b, nat = ph[ph["variant"] == "base"], ph[ph["variant"] == "IW_NAT"]
        thr = b.loc[b["y_true"] != 0, "y_true"].abs().quantile(0.2)
        small = lambda x: x[(x["y_true"] != 0) & (x["y_true"].abs() <= thr)]  # noqa: E731
        pc_nat = per_commodity(nat, 0.5)
        for v, x in ph.groupby("variant"):
            st = full_metrics(x, 0.5, h)
            rows.append({"variant": v, "horizon": h, **{k: st[k] for k in ("macro_f1", "macro_f1_lo", "macro_f1_hi", "mcc", "roc_auc")},
                         "macro_f1_q1_small": full_metrics(small(x), 0.5, h)["macro_f1"]})
            if v in VARIANTS:
                for ref_name, ref in (("base", b), ("IW_NAT", nat)):
                    d = paired_diff(x, ref, 0.5, 0.5, h)
                    ds = paired_diff(small(x), small(ref), 0.5, 0.5, h)
                    pairs.append({"variant": v, "vs": ref_name, "horizon": h, "diff": d["diff"], "lo": d["lo"], "hi": d["hi"],
                                  "diff_q1_small": ds["diff"], "lo_q1_small": ds["lo"], "hi_q1_small": ds["hi"]})
                pcs += [{"variant": v, "horizon": h, "commodity": c, "diff_vs_IW_NAT": f - pc_nat[c]}
                        for c, f in per_commodity(x, 0.5).items()]
    met, pr, pc = pd.DataFrame(rows), pd.DataFrame(pairs), pd.DataFrame(pcs)
    met.round(4).to_csv(os.path.join(OUT, "diag_dev_metrics.csv"), index=False)
    pr.round(4).to_csv(os.path.join(OUT, "diag_dev_paired.csv"), index=False)
    pc.round(4).to_csv(os.path.join(OUT, "diag_dev_per_commodity.csv"), index=False)
    pd.set_option("display.width", 250)
    print(met.round(4).to_string(index=False))
    print(pr.round(4).to_string(index=False))
    print(pc.pivot_table(index="commodity", columns=["variant", "horizon"], values="diff_vs_IW_NAT").round(3).to_string())
