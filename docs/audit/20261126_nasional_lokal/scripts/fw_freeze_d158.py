"""D-158 (PROTOKOL_I2 §3): bekukan prediksi maju base (C1t), FR_REF, FR_CITY untuk origin yang target h-nya belum terealisasi di panel
(origin sama dengan D-152: minggu panel terakhir − k minggu, k < h). Split = split resmi tetapi baris uji tidak mensyaratkan target; dicek
pada 2 origin berlabel (latih/uji identik dengan split_origin, base = direction_tuned_preds C1t). Prediksi hanya memakai fitur ≤ origin
dan label t + h ≤ origin. → hasil/forward_preds_d158.csv + hasil/forward_manifest_d158.json (sha256 prediksi, protokol, kode, data)."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import cfg, np, pd, table  # noqa: E402
from m_run import fit_predict  # noqa: E402
from kagami.features.forecast import LAG_COLUMNS, split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402
import i2_spec  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
WEEK = pd.Timedelta(weeks=1)
MODELS = ("base", "FR_REF", "FR_CITY")
CODE = ["docs/audit/20261126_nasional_lokal/scripts/fresh_du.py", "docs/audit/20261126_nasional_lokal/scripts/kb_build.py",
        "docs/audit/20261126_nasional_lokal/scripts/i2_spec.py", "docs/audit/20261126_nasional_lokal/scripts/fw_freeze_d158.py",
        "docs/audit/20261126_task4_master_f1/scripts/m_run.py", "src/models/direction.py", "src/features/price_dynamics.py",
        "src/features/forecast.py"]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def split_forward(tab, o, h):
    other = [c for c in tab.columns if c.startswith("y_") and c != f"y_{h}"]
    t = tab.drop(columns=other).rename(columns={f"y_{h}": "y"}).dropna(subset=LAG_COLUMNS).assign(origin=o, horizon=h)
    return t[t["y"].notna() & (t["week"] + h * WEEK <= o)].reset_index(drop=True), t[t["week"] == o].reset_index(drop=True)


def predict(tab, o, h):
    train, test = split_forward(tab, o, h)
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    V = i2_spec.variants(h, tuned_columns("C1t", h)[0])
    out = []
    for name in MODELS:
        p = fit_predict(tr, test, V[name], o)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, model=name, p_up=p, n_train=len(tr),
                                                             y_known=test["y"].to_numpy()))
    return pd.concat(out, ignore_index=True)


if __name__ == "__main__":
    tab = table("fresh")
    last = tab["week"].max()
    off = read_artifact(cfg, "direction_tuned_preds")
    off = off[off["model"] == "C1t"]
    for o, h in ((pd.Timestamp("2026-10-05"), 4), (pd.Timestamp("2026-09-07"), 8)):
        tr_a, te_a = split_origin(cfg, tab, o, h)
        tr_b, te_b = split_forward(tab, o, h)
        assert tr_a.equals(tr_b) and te_a.equals(te_b[te_b["y"].notna()].reset_index(drop=True))
        p = predict(tab, o, h)
        m = p[p["model"] == "base"].merge(off[(off["origin"] == o) & (off["horizon"] == h)], on=["province_id", "commodity"])
        dmax = float(np.abs(m["p_up_x"] - m["p_up_y"]).max())
        print(f"cek {o.date()} h{h}: latih/uji identik, base vs C1t {len(m)} baris maks |Δp| {dmax:.1e}", flush=True)
        assert dmax == 0.0
    jobs = [(last - k * WEEK, h) for h in (4, 8) for k in range(h)]
    preds = pd.concat([predict(tab, o, h) for o, h in sorted(jobs)], ignore_index=True)
    assert preds["y_known"].isna().all(), "ada target terealisasi di origin maju"
    preds = preds.drop(columns="y_known")
    preds["pred_up"] = preds["p_up"] > 0.5
    preds["origin"] = preds["origin"].dt.date.astype(str)
    preds = preds[["origin", "horizon", "model", "province_id", "commodity", "p_up", "pred_up", "n_train"]]
    path = os.path.join(OUT, "forward_preds_d158.csv")
    if os.path.exists(path):
        raise SystemExit(f"{path} sudah ada; prediksi beku tidak ditimpa")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        preds.to_csv(fh, index=False, float_format="%.10f")
    man = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "protocol_sha256": {"PROTOKOL_I1.md": sha(os.path.join(HERE, "..", "PROTOKOL_I1.md")),
                               "PROTOKOL_I2.md": sha(os.path.join(HERE, "..", "PROTOKOL_I2.md"))},
           "forward_preds_sha256": sha(path), "n_rows": int(len(preds)),
           "rows_by_horizon_model": {f"h{h}_{m}": int(n) for (h, m), n in preds.groupby(["horizon", "model"]).size().items()},
           "origins": {f"h{h}": sorted(preds.loc[preds["horizon"] == h, "origin"].unique().tolist()) for h in (4, 8)},
           "data": {"last_panel_week": last.date().isoformat(), "pihps_zip_sha256": sha(cfg.source_path("pihps")),
                    "pihps_city_zip_sha256": sha(cfg.source_path("pihps_city")), "fresh_rows": int(len(tab))},
           "code_sha256": {c: sha(os.path.join(ROOT, c)) for c in CODE}, "threshold": 0.5, "seed": int(cfg.seed),
           "catatan": "Evaluasi hanya sesudah semua target terealisasi (unduh PIHPS baru); bandingkan dengan forward_preds.csv D-152 (base & IW_NAT)."}
    with open(os.path.join(OUT, "forward_manifest_d158.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)
    print(json.dumps({k: man[k] for k in ("frozen_at_utc", "n_rows", "rows_by_horizon_model", "origins")}, indent=1))
    print(preds.groupby(["horizon", "model"])["pred_up"].agg(["size", "mean"]).round(3).to_string())
