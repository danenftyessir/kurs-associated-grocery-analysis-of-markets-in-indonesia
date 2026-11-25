"""P05 (outlier) + P06 (ketidakpastian pengukuran) pada data mingguan resmi; tidak mengubah data.

P05: (1) lonjakan satu hari QA (|Δlog| > 0,5 berbalik, `qa.flag_price_outliers`); (2) perubahan mingguan ekstrem
     |Δlog| > 5 × MAD seri; diklasifikasikan "terkonfirmasi lintas provinsi" bila ≥ 1/3 provinsi lain komoditas sama bergerak
     searah ≥ setengah besarnya pada minggu itu, "berbalik" bila ≥ 70% berbalik dalam ≤ 2 minggu; isolated & berbalik =
     kandidat galat data. Dihitung berapa label C1-tuned yang ujungnya menyentuh minggu tersebut + akurasinya.
P06: derau transien per komoditas dari rasio varians: Var(p_{t+k} − p_t) ≈ k·σ²_s + 2σ²_n (k = 1..12, dalam seri) →
     σ_n; label "didominasi derau" bila |y| < √2·σ_n (selisih derau dua ujung 1 SD). Akurasi C1-tuned di sana.
Keluaran: hasil/p05_outliers.csv, hasil/p06_noise.csv, hasil/p05_p06_summary.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.data.qa import flag_price_outliers  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

HERE = os.path.dirname(__file__)
from p_exp import EXP  # noqa: E402  (data per baris turunan PIHPS disimpan di luar repo)
OUT = os.path.join(HERE, "..", "hasil")
summ = {}

daily = read_artifact(cfg, "pihps_daily")
spk = flag_price_outliers(daily)
spk["week"] = spk["date"] - pd.to_timedelta(spk["date"].dt.dayofweek, unit="D")
spk = spk[spk["date"] >= pd.Timestamp(cfg.params["period"]["start"])]
summ["qa_spike_days_in_period"] = int(len(spk))

panel = read_artifact(cfg, "panel_weekly")
wide = panel.pivot(index="week", columns=["province_id", "commodity"], values="log_price").sort_index()
d = wide.diff()
mad = (d - d.median()).abs().median()
z = (d - d.median()) / (1.4826 * mad.replace(0, np.nan))
ext = z.abs() > 5
# konfirmasi lintas provinsi
recs = []
for (pid, c) in d.columns:
    wk = ext.index[ext[(pid, c)].to_numpy()]
    if not len(wk):
        continue
    others = d.loc[wk, [k for k in d.columns if k[1] == c and k[0] != pid]]
    own = d.loc[wk, (pid, c)]
    same = (np.sign(others).eq(np.sign(own), axis=0) & others.abs().ge(own.abs() * 0.5, axis=0)).sum(1)
    n_oth = others.notna().sum(1)
    pos = d.index.get_indexer(wk)
    rev = []
    for i, w in zip(pos, wk):
        nxt = d[(pid, c)].iloc[i + 1:i + 3].sum()
        rev.append(bool(np.sign(nxt) == -np.sign(own.loc[w]) and abs(nxt) >= 0.7 * abs(own.loc[w])))
    for w, s, n, r in zip(wk, same.to_numpy(), n_oth.to_numpy(), rev):
        recs.append({"week": w, "province_id": pid, "commodity": c, "dlog": float(own.loc[w]), "z": float(z.loc[w, (pid, c)]),
                     "confirmed": bool(n > 0 and s / n >= 1 / 3), "reverts": r})
out = pd.DataFrame(recs)
out["class"] = np.where(out["confirmed"], "kejadian pasar (terkonfirmasi lintas provinsi)",
                        np.where(out["reverts"], "kandidat galat (terisolasi & berbalik)", "terisolasi, tidak berbalik"))
out = out[out["week"] >= pd.Timestamp(cfg.params["period"]["start"])]
out.to_csv(os.path.join(OUT, "p05_outliers.csv"), index=False)
summ["weekly_extreme_moves"] = out["class"].value_counts().to_dict()
summ["weekly_extreme_share_of_cells"] = float(len(out) / d.notna().sum().sum())

lab = pd.read_parquet(os.path.join(EXP, "label_audit.parquet"))
lab = lab[lab["part"].isin(["dev", "test"])]
cand = out[out["class"].str.startswith("kandidat")]
flag_weeks = set()
for _, r in pd.concat([spk[["province_id", "commodity", "week"]], cand[["province_id", "commodity", "week"]]]).iterrows():
    w = pd.Timestamp(r["week"])
    for k in (0, 1):   # minggu lonjakan & minggu sesudahnya (perubahan masuk & keluar)
        flag_weeks.add((int(r["province_id"]), r["commodity"], w + pd.Timedelta(weeks=k)))
hit = [((p, c, a) in flag_weeks) or ((p, c, b) in flag_weeks)
       for p, c, a, b in zip(lab["province_id"], lab["commodity"], lab["t0"], lab["t1"])]
lab = lab.assign(hit=hit)
summ["labels_touching_outlier_weeks"] = {f"{p}_h{h}": {"n": int(x["hit"].sum()), "share": float(x["hit"].mean()),
                                                          "acc": float(x.loc[x["hit"], "correct"].mean()) if x["hit"].any() else None}
                                         for (p, h), x in lab.groupby(["part", "horizon"])}

# P06 rasio varians
rows = []
for c in sorted(panel["commodity"].unique()):
    W = wide.xs(c, axis=1, level="commodity")
    ks = np.arange(1, 13)
    v = []
    for k in ks:
        y = (W.shift(-k) - W)
        y = y - y.mean()                       # dalam seri
        v.append(np.nanmean(y.to_numpy() ** 2))
    b, a = np.polyfit(ks, v, 1)
    s2n = max(a / 2, 0.0)
    d1 = W.diff()
    ac1 = np.nanmean([d1[col].autocorr(1) for col in d1.columns])
    rows.append({"commodity": c, "sigma_noise_pct": np.sqrt(s2n) * 100, "sigma_signal_week_pct": np.sqrt(max(b, 0)) * 100,
                 "noise_share_var_h4": 2 * s2n / (4 * b + 2 * s2n), "noise_share_var_h8": 2 * s2n / (8 * b + 2 * s2n),
                 "acf1_weekly_dlog": ac1})
nz = pd.DataFrame(rows)
lab = lab.merge(nz[["commodity", "sigma_noise_pct"]], on="commodity")
lab["noise_dom"] = lab["y_true"].abs() * 100 < np.sqrt(2) * lab["sigma_noise_pct"]
for (p, h), x in lab.groupby(["part", "horizon"]):
    summ[f"noise_dominated_{p}_h{h}"] = {"share": float(x["noise_dom"].mean()),
                                         "acc_noise_dom": float(x.loc[x["noise_dom"], "correct"].mean()),
                                         "acc_rest": float(x.loc[~x["noise_dom"], "correct"].mean())}
nzc = lab.groupby(["part", "horizon", "commodity"]).agg(noise_dom=("noise_dom", "mean"),
                                                         acc_noise_dom=("correct", lambda s: s[lab.loc[s.index, "noise_dom"]].mean()))
nz.round(4).to_csv(os.path.join(OUT, "p06_noise.csv"), index=False)
nzc.round(4).reset_index().to_csv(os.path.join(OUT, "p06_noise_by_commodity.csv"), index=False)
with open(os.path.join(OUT, "p05_p06_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summ, f, indent=1, default=str)
print(json.dumps(summ, indent=1, default=str))
print(nz.round(3).to_string(index=False))
print(nzc.reset_index().query("part == 'test'").round(3).to_string(index=False))
