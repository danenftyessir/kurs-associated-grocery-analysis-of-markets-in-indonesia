"""Evaluasi D-146 di Colab: macro F1 per varian TCN/MLP pada origin PENGEMBANGAN (origin + h <= 2023-12-31) vs C1-tuned,
beda berpasangan dengan bootstrap blok origin. Test (origin >= 2024) hanya dicetak untuk varian yang menang di pengembangan."""
import glob, os, sys
import numpy as np, pandas as pd
EXP = sys.argv[1]
OUT = os.path.join(EXP, "out")
KEY = ["origin", "province_id", "commodity"]
DEV_END, TEST_START = pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-01")


def conf(y, s):
    k = y != 0
    up, pu = y[k] > 0, s[k] > 0.5
    return np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float)


def mf1(C):
    tp, fn, fp, tn = C[..., 0], C[..., 1], C[..., 2], C[..., 3]
    return (2 * tp / (2 * tp + fp + fn) + 2 * tn / (2 * tn + fn + fp)) / 2


def paired(a, b, h, reps=1999):
    m = a.merge(b, on=KEY + ["y_true"], suffixes=("_a", "_b"))
    uo = np.array(sorted(m.origin.unique()))
    Ca = np.stack([conf(g.y_true.values, g.p_up_a.values) for _, g in m.groupby("origin")])
    Cb = np.stack([conf(g.y_true.values, g.p_up_b.values) for _, g in m.groupby("origin")])
    B = int(np.ceil(h / 4)) + 1
    rng = np.random.default_rng(0)
    d = []
    for _ in range(reps):
        st = rng.integers(0, len(uo), int(np.ceil(len(uo) / B)))
        idx = np.concatenate([(np.arange(s, s + B) % len(uo)) for s in st])[:len(uo)]
        d.append(mf1(Ca[idx].sum(0)) - mf1(Cb[idx].sum(0)))
    d = np.array(d)
    return mf1(Ca.sum(0)) - mf1(Cb.sum(0)), np.percentile(d, [2.5, 97.5]), min(1, 2 * min((d <= 0).mean(), (d >= 0).mean()) + 1 / reps)


rows = []
for h in (4, 8):
    ref = pd.read_parquet(os.path.join(EXP, f"c1t_h{h}.parquet"))
    for part, sel in (("dev", lambda o: o + pd.Timedelta(weeks=h) <= DEV_END), ("test", lambda o: o >= TEST_START)):
        r = ref[sel(ref.origin)][KEY + ["y_true", "p_up"]]
        rows.append({"h": h, "part": part, "model": "C1t", "macro_f1": float(mf1(conf(r.y_true.values, r.p_up.values)))})
        for f in sorted(glob.glob(os.path.join(OUT, "tcn_preds_*.parquet"))):
            name = os.path.basename(f)[10:-8]
            p = pd.read_parquet(f)
            p = p[(p.horizon == h)][KEY + ["p_up"]].merge(r[KEY + ["y_true"]], on=KEY)
            if p.empty:
                continue
            d, ci, pv = paired(p, r, h)
            rows.append({"h": h, "part": part, "model": name, "n_origins": p.origin.nunique(),
                         "macro_f1": float(mf1(conf(p.y_true.values, p.p_up.values))), "diff_vs_C1t": d,
                         "lo": ci[0], "hi": ci[1], "p": pv})
res = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(res[res.part == "dev"].round(4).to_string(index=False))
win = res[(res.part == "dev") & (res.diff_vs_C1t > 0)][["h", "model"]]
print("\nVarian yang lebih baik dari C1t di pengembangan:", win.values.tolist() or "tidak ada")
t = res[res.part == "test"].merge(win, on=["h", "model"]) if len(win) else pd.DataFrame()
if len(t):
    print(t.round(4).to_string(index=False))
res.to_csv(os.path.join(EXP, "eval_d146.csv"), index=False)
