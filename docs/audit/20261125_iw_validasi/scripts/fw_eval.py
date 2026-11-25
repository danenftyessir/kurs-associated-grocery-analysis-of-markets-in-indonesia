"""D-152 §3: evaluasi prediksi maju beku (hasil/forward_preds.csv) setelah target terealisasi. Dibekukan bersama prediksi.

Pemakaian:
  python fw_eval.py --selftest                       # label dari snapshot sekarang = y_4 / y_8 resmi pada origin berlabel
  python fw_eval.py --pihps-zip <snapshot PIHPS baru> # evaluasi; snapshot baru diunduh dengan format `pihps` yang sama

Label = tanda (log rerata hari teramati minggu t+h − minggu t) dari snapshot baru, aggregate resmi (`select_variants` + agregasi
`weekly` dengan grid diperpanjang s.d. minggu data terakhir), tanpa pengisian; y = 0 dikeluarkan. Target dianggap terealisasi bila
snapshot memuat hari Jumat minggu t+h. Selisih berpasangan IW_NAT − base: bootstrap blok origin mingguan (blok = h, dibatasi n);
dengan < 2h origin hasil hanya deskriptif (lihat daya di laporan D-152).
"""
import argparse
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from engine import stats_from  # noqa: E402
from evalx import origin_conf  # noqa: E402
from kg import cfg  # noqa: E402
from kagami.data.loaders import load_pihps  # noqa: E402
from kagami.data.weekly import _aggregate, select_variants  # noqa: E402
from kagami.stats.resampling import moving_block_indices  # noqa: E402
from kagami.utils.dates import week_start  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
KEY = ["origin", "province_id", "commodity"]
REPS = 1999


def labels(zip_path, horizons=(4, 8)):
    shim = types.SimpleNamespace(source_path=lambda key: zip_path)
    daily = select_variants(cfg, load_pihps(shim, "pihps"))
    last = daily["date"].max()
    wp = cfg.params["weekly"]
    start = week_start(pd.Series([pd.Timestamp(cfg.params["period"]["start"])])).iloc[0]
    weeks = pd.date_range(start, week_start(pd.Series([last])).iloc[0], freq="W-MON")
    pw = _aggregate(daily, weeks, cfg.regions["province_id"].astype(int).tolist(), list(cfg.commodities),
                    run_days=wp["carry_forward_run_days"], short_days=wp["short_week_days"], last_date=last)
    wide = pw.pivot(index="week", columns=["province_id", "commodity"], values="log_price").sort_index()
    out = []
    for h in horizons:
        y = (wide.shift(-h) - wide).stack(["province_id", "commodity"], future_stack=True).rename("y").reset_index()
        y["complete"] = y["week"] + pd.Timedelta(weeks=h) + pd.Timedelta(days=4) <= last
        out.append(y.assign(horizon=h))
    return pd.concat(out, ignore_index=True).rename(columns={"week": "origin"}), last


def metrics(d):
    nz = d[d["y"] != 0]
    up, pu = nz["y"] > 0, nz["p_up"] > 0.5
    C = np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float)
    st = {k: float(v) for k, v in stats_from(C).items() if k in ("macro_f1", "f1_up", "f1_down", "mcc")}
    st["roc_auc"] = float(roc_auc_score(up, nz["p_up"])) if up.nunique() == 2 else np.nan
    st["n"] = int(len(nz))
    return st


def paired(a, b, h):
    m = a[KEY + ["y", "p_up"]].merge(b[KEY + ["p_up"]], on=KEY, suffixes=("_a", "_b"))
    ua, Ca = origin_conf(m.rename(columns={"y": "y_true", "p_up_a": "score"}), 0.5)
    _, Cb = origin_conf(m.rename(columns={"y": "y_true", "p_up_b": "score"}), 0.5)
    diff = float(stats_from(Ca.sum(0))["macro_f1"] - stats_from(Cb.sum(0))["macro_f1"])
    n, blk = len(ua), max(1, min(h, len(ua)))
    idx = np.vstack([moving_block_indices(n, blk, np.random.default_rng(r)) for r in range(REPS)])
    da = stats_from(Ca[idx].sum(1))["macro_f1"] - stats_from(Cb[idx].sum(1))["macro_f1"]
    lo, hi = np.nanpercentile(da, [2.5, 97.5])
    return {"diff": diff, "lo": float(lo), "hi": float(hi), "n_origins": n, "descriptive_only": n < 2 * h}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pihps-zip")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
        from p_exp import EXP
        y, last = labels(str(cfg.source_path("pihps")))
        base = pd.read_parquet(os.path.join(EXP, "base.parquet"), columns=["week", "province_id", "commodity", "y_4", "y_8"])
        for h in (4, 8):
            m = base.rename(columns={"week": "origin"}).merge(y[y["horizon"] == h], on=KEY, how="inner")
            m = m[m["origin"] <= m["origin"].max() - pd.Timedelta(weeks=h)]
            ok = np.isclose(m[f"y_{h}"], m["y"], atol=1e-12) | (m[f"y_{h}"].isna() & m["y"].isna())
            print(f"selftest h{h}: {len(m)} baris, cocok {ok.mean():.6f}, beda {int((~ok).sum())}")
            assert ok.all()
        print("selftest lolos; data terakhir", last.date())
        sys.exit(0)
    preds = pd.read_csv(os.path.join(OUT, "forward_preds.csv"), parse_dates=["origin"])
    y, last = labels(a.pihps_zip)
    d = preds.merge(y, on=KEY + ["horizon"], how="left")
    d = d[d["complete"].fillna(False) & np.isfinite(d["y"])]
    print(f"data terakhir {last.date()}; baris bertarget {len(d)} dari {len(preds)}")
    rows, pairs = [], []
    for h, dh in d.groupby("horizon"):
        b = dh[dh["model"] == "base"]
        thr = b.loc[b["y"] != 0, "y"].abs().quantile(0.2)
        for mname, x in dh.groupby("model"):
            sm = x[(x["y"] != 0) & (x["y"].abs() <= thr)]
            rows.append({"horizon": h, "model": mname, **metrics(x), "macro_f1_q1_small": metrics(sm)["macro_f1"]})
        nat = dh[dh["model"] == "IW_NAT"]
        pairs.append({"horizon": h, **paired(nat, b, h)})
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    print(pd.DataFrame(pairs).round(4).to_string(index=False))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"forward_eval_metrics_{last.date()}.csv"), index=False)
    pd.DataFrame(pairs).to_csv(os.path.join(OUT, f"forward_eval_paired_{last.date()}.csv"), index=False)
