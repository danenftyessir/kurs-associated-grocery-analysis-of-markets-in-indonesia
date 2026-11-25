"""D-148 tahap 4: kalibrasi probabilitas temporal sadar-rezim pada prediksi C1-tuned resmi (`direction_tuned_preds`, C1t).

Tidak melatih ulang model. Untuk setiap (h, origin o) probabilitas mentah p disesuaikan di skala logit hanya dengan informasi yang
sudah terealisasi pada o:
- INT_c_K : intercept per komoditas b_c (MAP, prior N(0; 0,5²)) dari prediksi origin lampau o' (o' + h ≤ o, o' > o − h − K) vs
            label terealisasinya; K ∈ {13, 26} minggu.
- INT_g_K : intercept global yang sama.
- PRI_c_K_a: koreksi pergeseran prior (label shift): logit p' = logit p + a·[logit π_baru_c − logit π_latih_c]; π_baru_c = porsi naik
            label komoditas c (semua provinsi, y ≠ 0) dengan minggu label t ∈ (o − h − K, o − h]; π_latih_c = porsi naik baris latih
            komoditas c (t + h ≤ o, sejak 2018); a ∈ {0,5; 1}.
Threshold tetap 0,5 untuk semua (tidak ada threshold per komoditas). Seleksi: konfigurasi dengan macro F1 rerata (h 4, h 8)
tertinggi di origin PENGEMBANGAN; aturan buka test sama dengan D-147 (Δ rerata ≥ +0,005, interval > 0 di ≥ 1 horizon, Δ ≥ 0
di horizon lain). Test hanya dihitung untuk konfigurasi terpilih yang lolos.
Keluaran: hasil/cal_dev.csv, hasil/cal_selected.json, (bila lolos) hasil/cal_test.csv, hasil/cal_test_commodity.csv.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from evalx import full_metrics, paired_diff  # noqa: E402
from p_exp import EXP  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
# SPLIT=1 (D-148): dev origin + h ≤ 2023-12-31, test ≥ 2024. SPLIT=2 (D-149, pasca-hoc eksploratif): dev origin + h ≤ 2024-12-31,
# test ≥ 2025-01-01, ditetapkan sebelum run ulang karena drift komoditas diatur baru muncul 2024+.
SPLIT = os.environ.get("SPLIT", "1")
DEV_END, TEST_START = ((pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-01")) if SPLIT == "1"
                       else (pd.Timestamp("2024-12-31"), pd.Timestamp("2025-01-01")))
SUF = "" if SPLIT == "1" else "_s2"
REGULATED = ["beras", "minyak_goreng", "daging_sapi", "gula_pasir"]
EPS = 1e-4


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sig(z):
    return 1 / (1 + np.exp(-z))


def map_intercept(z, y, sd=0.5, it=25):
    """argmin_b Σ logloss(y, σ(z + b)) + b²/(2 sd²) (Newton)."""
    b = 0.0
    for _ in range(it):
        p = sig(z + b)
        g = (p - y).sum() + b / sd**2
        H = (p * (1 - p)).sum() + 1 / sd**2
        b -= g / H
    return b


pred = pd.read_parquet(os.path.join("data", "interim", "direction_tuned_preds.parquet"))
pred = pred[pred["model"] == "C1t"].copy()
pred["z"] = logit(pred["p_up"].to_numpy())
lab = pd.read_parquet(os.path.join(EXP, "base.parquet"), columns=["week", "province_id", "commodity", "y_4", "y_8"])
lab = lab[lab["week"] >= pd.Timestamp("2018-01-01")]

CONFIGS = ["NONE"] + [f"INT_c_{k}" for k in (13, 26)] + [f"INT_g_{k}" for k in (13, 26)] + \
          [f"PRI_c_{k}_{a}" for k in (13, 26) for a in (0.5, 1.0)]
rows = []
for h in (4, 8):
    ph = pred[pred["horizon"] == h]
    yl = lab[["week", "commodity", f"y_{h}"]].rename(columns={f"y_{h}": "y"}).dropna()
    yl = yl[yl["y"] != 0]
    for o, test in ph.groupby("origin"):
        test = test.copy()
        past = ph[(ph["origin"] + pd.Timedelta(weeks=h) <= o) & (ph["y_true"] != 0) & ph["y_true"].notna()]
        train_lab = yl[yl["week"] + pd.Timedelta(weeks=h) <= o]
        pi_old = train_lab.groupby("commodity")["y"].apply(lambda s: (s > 0).mean())
        for cf in CONFIGS:
            z = test["z"].to_numpy().copy()
            if cf.startswith("INT"):
                _, scope, k = cf.split("_")
                pk = past[past["origin"] > o - pd.Timedelta(weeks=h + int(k))]
                if pk["origin"].nunique() >= 2:
                    if scope == "g":
                        z = z + map_intercept(pk["z"].to_numpy(), (pk["y_true"] > 0).to_numpy(float))
                    else:
                        for c, g in pk.groupby("commodity"):
                            m = (test["commodity"] == c).to_numpy()
                            z[m] = z[m] + map_intercept(g["z"].to_numpy(), (g["y_true"] > 0).to_numpy(float))
            elif cf.startswith("PRI"):
                _, _, k, a = cf.split("_")
                rec = train_lab[train_lab["week"] > o - pd.Timedelta(weeks=h + int(k))]
                pi_new = rec.groupby("commodity")["y"].apply(lambda s: (s > 0).mean())
                shift = (logit(pi_new.reindex(pi_old.index).to_numpy()) - logit(pi_old.to_numpy()))
                sh = pd.Series(shift, index=pi_old.index).fillna(0.0)
                z = z + float(a) * test["commodity"].map(sh).fillna(0.0).to_numpy()
            rows.append(test[["origin", "horizon", "province_id", "commodity", "y_true"]].assign(config=cf, score=sig(z)))
adj = pd.concat(rows, ignore_index=True)
adj["part"] = np.where(adj["origin"] >= TEST_START, "test",
                       np.where(adj["origin"] + pd.to_timedelta(adj["horizon"] * 7, unit="D") <= DEV_END, "dev", "gap"))
adj.to_parquet(os.path.join(EXP, f"cal_all{SUF}.parquet"))


def extra(x):
    """Metrik tambahan: Brier, log loss, kelebihan prediksi naik komoditas diatur, recall naik."""
    nz = x[(x["y_true"] != 0) & x["y_true"].notna()]
    y = (nz["y_true"] > 0).to_numpy(float)
    p = nz["score"].to_numpy()
    reg = nz[nz["commodity"].isin(REGULATED)]
    return {"brier": float(np.mean((p - y) ** 2)), "logloss": float(-np.mean(y * np.log(np.clip(p, EPS, 1)) + (1 - y) * np.log(np.clip(1 - p, EPS, 1)))),
            "excess_up_regulated": float((reg["score"] > 0.5).mean() - (reg["y_true"] > 0).mean()),
            "excess_up_all": float((p > 0.5).mean() - y.mean()), "rec_up": float(((p > 0.5) & (y == 1)).sum() / max(y.sum(), 1))}


dev = adj[adj["part"] == "dev"]
res, pairs = [], []
for h in (4, 8):
    base = dev[(dev["config"] == "NONE") & (dev["horizon"] == h)]
    for cf in CONFIGS:
        x = dev[(dev["config"] == cf) & (dev["horizon"] == h)]
        st = full_metrics(x, 0.5, h)
        res.append({"config": cf, "horizon": h, **{k: st[k] for k in ("macro_f1", "macro_f1_lo", "macro_f1_hi", "f1_up", "f1_down", "mcc", "share_pred_up")}, **extra(x)})
        if cf != "NONE":
            pairs.append({"config": cf, "horizon": h, **paired_diff(x, base, 0.5, 0.5, h)})
r = pd.DataFrame(res)
pr = pd.DataFrame(pairs)
if SPLIT == "2":
    d24 = dev[dev["origin"] + pd.to_timedelta(dev["horizon"] * 7, unit="D") > pd.Timestamp("2023-12-31")]   # origin dev baru (split 2)
    diag = []
    for h in (4, 8):
        b24 = d24[(d24["config"] == "NONE") & (d24["horizon"] == h)]
        for cf in CONFIGS[1:]:
            x = d24[(d24["config"] == cf) & (d24["horizon"] == h)]
            diag.append({"config": cf, "horizon": h, **paired_diff(x, b24, 0.5, 0.5, h), **extra(x)})
    pd.DataFrame(diag).round(4).to_csv(os.path.join(OUT, "cal_dev2024_diag_s2.csv"), index=False)
    print("diagnostik origin dev 2024 (target terealisasi 2024):")
    print(pd.DataFrame(diag).round(4).to_string(index=False))
r.round(4).to_csv(os.path.join(OUT, f"cal_dev{SUF}.csv"), index=False)
pr.round(4).to_csv(os.path.join(OUT, f"cal_dev_paired{SUF}.csv"), index=False)
pd.set_option("display.width", 250)
print(r.round(3).to_string(index=False))
print(pr.round(4).to_string(index=False))
piv = pr.pivot(index="config", columns="horizon", values=["diff", "lo", "hi"])
piv["mean"] = (piv[("diff", 4)] + piv[("diff", 8)]) / 2
best = piv["mean"].idxmax()
d4, d8 = piv.loc[best, ("diff", 4)], piv.loc[best, ("diff", 8)]
ok = bool(piv.loc[best, "mean"].item() >= 0.005 and (piv.loc[best, ("lo", 4)] > 0 or piv.loc[best, ("lo", 8)] > 0) and min(d4, d8) >= 0)
sel = {"selected": best, "dev_diff_h4": float(d4), "dev_diff_h8": float(d8), "open_test": ok}
print(sel)
if ok:
    te = adj[adj["part"] == "test"]
    tres, tpairs, comm = [], [], []
    for h in (4, 8):
        b = te[(te["config"] == "NONE") & (te["horizon"] == h)]
        x = te[(te["config"] == best) & (te["horizon"] == h)]
        for name, d in (("NONE", b), (best, x)):
            st = full_metrics(d, 0.5, h)
            tres.append({"config": name, "horizon": h, **{k: st[k] for k in ("macro_f1", "macro_f1_lo", "macro_f1_hi", "f1_up", "f1_down", "mcc", "share_pred_up", "rec_up", "rec_down")}, **extra(d)})
            for c, g in d[d["y_true"] != 0].groupby("commodity"):
                comm.append({"config": name, "horizon": h, "commodity": c, "pred_up": float((g["score"] > 0.5).mean()),
                             "actual_up": float((g["y_true"] > 0).mean()), "macro_f1": full_metrics(g, 0.5, h)["macro_f1"]})
        tpairs.append({"config": best, "horizon": h, **paired_diff(x, b, 0.5, 0.5, h)})
    pd.DataFrame(tres).round(4).to_csv(os.path.join(OUT, f"cal_test{SUF}.csv"), index=False)
    pd.DataFrame(tpairs).round(4).to_csv(os.path.join(OUT, f"cal_test_paired{SUF}.csv"), index=False)
    pd.DataFrame(comm).round(4).to_csv(os.path.join(OUT, f"cal_test_commodity{SUF}.csv"), index=False)
    print(pd.DataFrame(tres).round(3).to_string(index=False))
    print(pd.DataFrame(tpairs).round(4).to_string(index=False))
    sel["test"] = tpairs
with open(os.path.join(OUT, f"cal_selected{SUF}.json"), "w", encoding="utf-8") as f:
    json.dump(sel, f, indent=1, default=str)
