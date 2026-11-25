"""D-152 §3: bekukan prediksi maju C1-tuned (`base`) dan `IW_NAT` (D-151) untuk origin yang labelnya belum terealisasi.

Split = split_origin resmi KECUALI baris uji tidak mensyaratkan target (target belum terealisasi). Dicek dulu pada 2 origin berlabel:
latih identik dengan split_origin, uji (bertarget) identik, dan p_up base = `direction_tuned_preds` C1t.
Keluaran: hasil/forward_preds.csv + hasil/forward_manifest.json (sha256 prediksi, kode, data; waktu pembekuan UTC).
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from p_exp import EXP, fit  # noqa: E402
from kagami.features.forecast import LAG_COLUMNS, split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
WEEK = pd.Timedelta(weeks=1)
IW_NAT = ["iw_gap", "iw_return", "iw_range", "iw_vol", "iw_n_days", "iw_last_age", "iw_gap_nat", "iw_return_nat"]
MODELS = {"base": [], "IW_NAT": IW_NAT}
CODE = ["docs/audit/20261125_pilot_produsen_intraminggu/scripts/iw_build.py",
        "docs/audit/20261125_pilot_produsen_intraminggu/scripts/exp.py",
        "docs/audit/20261125_task4_audit_preprocessing/scripts/p_exp.py",
        "docs/audit/20261125_iw_validasi/scripts/fw_freeze.py",
        "docs/audit/20261125_iw_validasi/scripts/fw_eval.py",
        "src/models/direction.py", "src/features/price_dynamics.py", "src/features/forecast.py"]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def split_forward(table, o, h):
    other = [c for c in table.columns if c.startswith("y_") and c != f"y_{h}"]
    t = table.drop(columns=other).rename(columns={f"y_{h}": "y"}).dropna(subset=LAG_COLUMNS).assign(origin=o, horizon=h)
    train = t[t["y"].notna() & (t["week"] + h * WEEK <= o)].reset_index(drop=True)
    test = t[t["week"] == o].reset_index(drop=True)
    return train, test


def predict(table, o, h):
    train, test = split_forward(table, o, h)
    out = []
    for name, extra in MODELS.items():
        p, _, n_used = fit(train, test, tuned_columns("C1t", h)[0] + extra, None, None, h, cfg.seed)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, model=name, p_up=p, n_train=n_used,
                                                             y_known=test["y"].to_numpy()))
    return pd.concat(out, ignore_index=True)


if __name__ == "__main__":
    tab = pd.read_parquet(os.path.join(EXP, "iw.parquet"))
    last = tab["week"].max()
    # 1. cek split & reproduksi pada origin berlabel
    off = read_artifact(cfg, "direction_tuned_preds")
    off = off[off["model"] == "C1t"]
    for o, h in ((pd.Timestamp("2026-10-05"), 4), (pd.Timestamp("2026-09-07"), 8)):
        tr_a, te_a = split_origin(cfg, tab, o, h)
        tr_b, te_b = split_forward(tab, o, h)
        assert tr_a.equals(tr_b), "latih berbeda"
        assert te_a.equals(te_b[te_b["y"].notna()].reset_index(drop=True)), "uji berbeda"
        p = predict(tab, o, h)
        m = p[p["model"] == "base"].merge(off[(off["origin"] == o) & (off["horizon"] == h)], on=["province_id", "commodity"])
        dmax = float(np.abs(m["p_up_x"] - m["p_up_y"]).max())
        print(f"cek {o.date()} h{h}: latih/uji identik, base vs C1t {len(m)} baris maks |Δp| {dmax:.1e}")
        assert dmax == 0.0
    # 2. origin maju: minggu yang target h-nya belum terealisasi
    jobs = [(last - k * WEEK, h) for h in (4, 8) for k in range(h)]
    preds = pd.concat([predict(tab, o, h) for o, h in sorted(jobs)], ignore_index=True)
    assert preds["y_known"].isna().all(), "ada target yang sudah terealisasi di origin maju"
    preds = preds.drop(columns="y_known")
    preds["pred_up"] = preds["p_up"] > 0.5
    preds["origin"] = preds["origin"].dt.date.astype(str)
    preds = preds[["origin", "horizon", "model", "province_id", "commodity", "p_up", "pred_up", "n_train"]]
    path = os.path.join(OUT, "forward_preds.csv")
    if os.path.exists(path):
        raise SystemExit(f"{path} sudah ada; prediksi beku tidak ditimpa")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        preds.to_csv(fh, index=False, float_format="%.10f")
    daily = read_artifact(cfg, "pihps_daily")
    man = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocol_sha256": sha(os.path.join(HERE, "..", "PROTOKOL.md")),
        "forward_preds_sha256": sha(path),
        "n_rows": int(len(preds)),
        "rows_by_horizon_model": {f"h{h}_{m}": int(n) for (h, m), n in preds.groupby(["horizon", "model"]).size().items()},
        "origins": {f"h{h}": sorted(preds.loc[preds["horizon"] == h, "origin"].unique().tolist()) for h in (4, 8)},
        "data": {"last_panel_week": last.date().isoformat(), "last_daily_date": daily["date"].max().date().isoformat(),
                 "pihps_zip_sha256": sha(cfg.source_path("pihps")), "iw_parquet_rows": int(len(tab))},
        "code_sha256": {c: sha(os.path.join(ROOT, c)) for c in CODE},
        "threshold": 0.5, "seed": int(cfg.seed),
    }
    with open(os.path.join(OUT, "forward_manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)
    print(json.dumps(man, indent=1))
    print(preds.groupby(["horizon", "model"])["pred_up"].agg(["size", "mean"]).round(3).to_string())
