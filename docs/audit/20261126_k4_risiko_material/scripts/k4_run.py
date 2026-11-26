"""K4 Fase C — rolling-origin: C1-tuned (refit, harus = artefak resmi) + klasifier risiko kenaikan material (PROTOCOL.md §2).

Per (h, origin): satu split, enam fit HGB dengan kolom & hyperparameter C1-tuned (`tuned_columns("C1t", h)`, `TUNED_HGB`, seed resmi):
  c1t     : arah naik, latih baris y ≠ 0 (identik `direction_tuned_preds` C1t)
  k4_e80  : z = 1[y_h ≥ P80 |y_h| latih komoditas], semua baris latih (termasuk y = 0)  ← kandidat utama
  k4_a80  : z_any = 1[max_{k≤h} (p_{t+k} − p_t) ≥ P80 |y_h|]                          ← target alternatif (Fase E)
  k4_e70, k4_e90 : ambang P70 / P90 |y_h| (kepekaan)
  k4_s90  : ambang P90 y_h bertanda (kenaikan desil atas per komoditas; komposisi seimbang) (kepekaan)
Universe uji = semua seri dengan lag tersedia pada origin (target hilang → z = 0). Baseline laju-dasar (CLIM, CLIMS) dari baris latih.
PART=dev (origin + h ≤ 2023-12-31) | test (origin ≥ 2024-01-01; hanya bila PROTOCOL §6 mengizinkan) | forward (origin dengan target
belum terealisasi pada minggu data terakhir; prediksi beku). Keluaran EXP/k4_{PART}_preds.parquet + hasil/k4_{PART}_meta.csv.
"""
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k4_common import (DEV_END, EXP, H, K, OUT, add_event, cfg, origin_list, pd, np, split_k4, table)  # noqa: E402
from kagami.models.direction import TUNED_HGB, tuned_columns  # noqa: E402
from kagami.models.forecasting import _codes  # noqa: E402

CATS = ["commodity", "region"]
NAIVE_COLS = ["lag_dp_4", "nat_dp_4", "dev_ma13"]
TARGETS = {  # nama → (target, pct, mode)
    "k4_e80": ("end", 80, "abs"), "k4_a80": ("any", 80, "abs"),
    "k4_e70": ("end", 70, "abs"), "k4_e90": ("end", 90, "abs"), "k4_s90": ("end", 90, "signed"),
}
_TAB = {}


def tab():
    if "t" not in _TAB:
        _TAB["t"] = add_event(table())
    return _TAB["t"]


def hgb(train_X, label, test_X, n_num, seed):
    from sklearn.ensemble import HistGradientBoostingClassifier
    if label.min() == label.max():
        return np.full(len(test_X), float(label.mean()))
    m = HistGradientBoostingClassifier(**TUNED_HGB, categorical_features=[False] * n_num + [True] * len(CATS), random_state=seed)
    m.fit(train_X, label)
    return m.predict_proba(test_X)[:, list(m.classes_).index(1)]


def design(tr, te, h):
    cols, _ = tuned_columns("C1t", h)
    num = [c for c in cols if tr[c].notna().any()]
    Xtr = np.column_stack([tr[num].astype(float).to_numpy(), _codes(cfg, tr, CATS)])
    Xte = np.column_stack([te[num].astype(float).to_numpy(), _codes(cfg, te, CATS)])
    return Xtr, Xte, len(num)


def split_any(t, o, h, target, pct, mode):
    if mode == "abs":
        return split_k4(t, o, h, target, pct)
    # signed: ambang = persentil pct y_h (bertanda) baris latih komoditas
    tr, te, _ = split_k4(t, o, h, target, pct)
    thr = tr.groupby("commodity")["y"].apply(lambda s: np.nanpercentile(s, pct))
    for d in (tr, te):
        d["thr"] = d["commodity"].map(thr).to_numpy(float)
        v = d["y"].to_numpy(float)
        d["z"] = (np.isfinite(v) & (v >= d["thr"].to_numpy())).astype(int)
    return tr, te, thr


def one(h, o, seed):
    t0 = time.perf_counter()
    t = tab()
    tr, te, thr = split_k4(t, o, h, "end", 80)
    out = te[K + ["region", "y", f"ymax_{h}", "has_target", "thr", "z", "log_p"] + NAIVE_COLS + [f"yseas_52_h{h}"]].copy()
    out = out.rename(columns={f"ymax_{h}": "ymax", f"yseas_52_h{h}": "yseas_52", "thr": "thr_e80", "z": "z_e80"})
    out["month"] = pd.Timestamp(o).month
    meta = {"origin": o, "horizon": h, "n_train": len(tr), "n_test": len(te)}
    # C1-tuned (arah; baris latih y ≠ 0)
    trn = tr[tr["y"] != 0]
    Xtr, Xte, nn = design(trn, te, h)
    out["c1t"] = hgb(Xtr, (trn["y"] > 0).astype(int).to_numpy(), Xte, nn, seed)
    meta["n_train_c1t"] = len(trn)
    for name, (target, pct, mode) in TARGETS.items():
        a, b, th = split_any(t, o, h, target, pct, mode)
        Xa, Xb, nn = design(a, b, h)
        key = name.replace("k4_", "")
        out[f"z_{key}"] = b["z"].to_numpy()
        out[f"thr_{key}"] = b["thr"].to_numpy()
        out[name] = hgb(Xa, a["z"].to_numpy(), Xb, nn, seed)
        clim = a.groupby("commodity")["z"].mean()
        out[f"clim_{key}"] = b["commodity"].map(clim).to_numpy(float)
        # laju-dasar komoditas × bulan kalender origin (baris latih bulan sama; < 50 baris → laju komoditas)
        am = a[a["week"].dt.month == pd.Timestamp(o).month]
        cm = am.groupby("commodity")["z"].agg(["mean", "size"])
        cs = b["commodity"].map(cm["mean"].where(cm["size"] >= 50)).to_numpy(float)
        out[f"clims_{key}"] = np.where(np.isfinite(cs), cs, out[f"clim_{key}"].to_numpy())
        meta[f"n_train_{key}"] = len(a)
        meta[f"train_rate_{key}"] = float(a["z"].mean())
    meta["sec"] = time.perf_counter() - t0
    return out.assign(origin=o, horizon=h), meta


def forward_origins(h):
    last = tab().loc[tab()["log_p"].notna(), "week"].max()
    weeks = sorted(tab().loc[tab()["week"] <= last, "week"].unique())
    return [pd.Timestamp(w) for w in weeks if pd.Timestamp(w) + pd.Timedelta(weeks=h) > last][-h:]


if __name__ == "__main__":
    from joblib import Parallel, delayed
    part = os.environ.get("PART", "dev")
    if part == "test" and not os.path.exists(os.path.join(OUT, "k4_test_allowed.flag")):
        raise SystemExit("test 2024+ hanya dibuka bila PROTOCOL §6 terpenuhi (k4_eval.py menulis hasil/k4_test_allowed.flag)")
    if part == "forward":
        jobs = [(h, o) for h in H for o in forward_origins(h)]
    else:
        jobs = [(h, o) for h in H for o in origin_list(h, part)]
    print(part, "pekerjaan", len(jobs), flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJ", 5)), verbose=5)(delayed(one)(h, o, cfg.seed) for h, o in jobs)
    preds = pd.concat([r[0] for r in res], ignore_index=True)
    meta = pd.DataFrame([r[1] for r in res])
    preds.to_parquet(os.path.join(EXP, f"k4_{part}_preds.parquet"))
    meta.to_csv(os.path.join(OUT, f"k4_{part}_meta.csv"), index=False)
    if part == "forward":
        preds.to_csv(os.path.join(OUT, "k4_forward_preds.csv"), index=False)
    print("selesai", round(time.time() - t0), "dtk", preds.shape)
