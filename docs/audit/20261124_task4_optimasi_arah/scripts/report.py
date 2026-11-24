"""Laporan akhir: semua kandidat & baseline pada baris test final yang sama; threshold dipilih HANYA dari origin pengembangan."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

import evalx  # noqa: E402
from engine import DEV_END, TEST_START, best_threshold, origin_list  # noqa: E402

HERE = os.path.dirname(__file__)
P = os.path.join(HERE, "preds")
INT = os.path.join(evalx.cfg.root, "data", "interim")
KEY = ["origin", "province_id", "commodity"]


def official():
    dp = pd.read_parquet(os.path.join(INT, "direction_preds.parquet")).assign(score=lambda d: d.p_up)
    dd = pd.read_parquet(os.path.join(INT, "deep_preds.parquet")).rename(columns={"y_pred": "score"})
    fp = pd.read_parquet(os.path.join(INT, "forecast_preds.parquet")).rename(columns={"y_pred": "score"})
    out = {}
    for src, models, kind in ((dp, ["C1", "C2"], "prob"), (fp, ["M1", "M3"], "reg"),
                              (dd, ["PTST", "TSMX", "TFM", "TFM_fx"], "reg")):
        for m in models:
            for h in (4, 8):
                out[(m, h)] = (src[(src.model == m) & (src.horizon == h)][KEY + ["y_true", "score"]], kind)
    return out


def load_new(spec):
    """spec: nama → (pola file per h, jenis 'prob'|'reg', kolom skor)."""
    out = {}
    for name, (pat, kind, col) in spec.items():
        for h in (4, 8):
            f = os.path.join(P, pat.format(h=h))
            if os.path.exists(f):
                d = pd.read_parquet(f)
                if "horizon" in d:
                    d = d[d.horizon == h]
                out[(name, h)] = (d.rename(columns={col: "score"})[KEY + ["y_true", "score"]], kind)
    return out


def dev_threshold(d, kind, h):
    dev = d[d.origin.isin(origin_list(h, "dev"))]
    if dev.empty:
        return np.nan
    grid = np.round(np.arange(0.30, 0.701, 0.005), 3) if kind == "prob" else np.unique(
        np.round(np.quantile(dev.score.dropna(), np.linspace(0.15, 0.85, 141)), 6))
    return best_threshold(dev.y_true.to_numpy(float), dev.score.to_numpy(float), grid)[0]


def main(spec, comparisons, out_md, out_json):
    models = {**official(), **load_new(spec)}
    test_keys = {h: models[("C1", h)][0].query("origin >= @TEST_START")[KEY] for h in (4, 8)}
    rows, frames, thr = [], {}, {}
    for (m, h), (d, kind) in models.items():
        t = d.merge(test_keys[h], on=KEY)
        frames[(m, h)] = t
        default = 0.5 if kind == "prob" else 0.0
        thr[(m, h)] = {"default": default, "dev": dev_threshold(d, kind, h)}
        for tk in ("default", "dev"):
            th = thr[(m, h)][tk]
            if not np.isfinite(th) or (tk == "dev" and th == default):
                continue
            st = evalx.full_metrics(t, th, h)
            rows.append({"model": m, "h": h, "threshold": tk, "thr": th, **st,
                         "per_commodity": evalx.per_commodity(t, th)})
    res = pd.DataFrame(rows)
    comp = []
    for (a, ta), (b, tb) in comparisons:
        for h in (4, 8):
            if (a, h) not in frames or (b, h) not in frames:
                continue
            tha, thb = thr[(a, h)][ta], thr[(b, h)][tb]
            if not (np.isfinite(tha) and np.isfinite(thb)):
                continue
            r = evalx.paired_diff(frames[(a, h)], frames[(b, h)], tha, thb, h)
            comp.append({"a": f"{a}@{ta}", "b": f"{b}@{tb}", "h": h, **r})
    comp = pd.DataFrame(comp)
    if len(comp):
        comp["q_bh"] = evalx.bh(comp["p"])
        comp["assessment"] = np.where((comp.q_bh < 0.05) & (comp["diff"] > 0), "lebih baik (lolos BH)",
                                      np.where((comp.q_bh < 0.05) & (comp["diff"] < 0), "lebih buruk (lolos BH)",
                                               "belum terbukti"))
    res.to_json(out_json.replace(".json", "_metrics.json"), orient="records", indent=1)
    comp.to_csv(out_json.replace(".json", "_paired.csv"), index=False)
    json.dump({f"{m}|{h}": v for (m, h), v in thr.items()}, open(out_json, "w"), indent=1)
    cols = ["model", "h", "threshold", "thr", "macro_f1", "macro_f1_lo", "macro_f1_hi", "weighted_f1", "f1_up", "f1_down",
            "prec_up", "rec_up", "prec_down", "rec_down", "bal_acc", "mcc", "roc_auc", "pr_auc", "coverage",
            "share_pred_up", "n", "n_origins", "origin_f1_sd"]
    with open(out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write(res[cols].sort_values(["h", "macro_f1"], ascending=[True, False]).round(4).to_string(index=False))
        f.write("\n\n")
        f.write(comp.round(4).to_string(index=False) if len(comp) else "")
    return res, comp
