"""Jalur A Workstream B4: layar gerbang 5 (sinyal arah nasional TAMBAHAN di atas konsensus C1-tuned) untuk fitur berita GDELT.

Protokol: PROTOCOL.md §B4 (dibekukan sebelum data GDELT penuh tersedia). Origin pengembangan saja; test 2024+ tidak dipakai.

Masukan GDELT (keluaran kueri BigQuery `b_bq_daily_counts.sql`, CSV):
  daily  : day_utc, commodity_group, n_all, n_disrupt, n_policy, n_stabil, n_supply, n_price_only, n_distinct_title, n_sources
  totals : day_utc, n_ind_total (semua artikel berbahasa Indonesia hari itu; penyebut agar pertumbuhan cakupan GDELT tidak terbaca sinyal)
Minggu origin t (Senin): artikel dengan DATE GDELT (UTC) pada hari Sabtu t−2 .. Jumat t+4 (7 hari). Jumat 23.59 UTC = Sabtu 06.59 WIB, sebelum
`available_at` konservatif harga minggu t (Minggu 00.00 WIB, D-155) → tanpa informasi sesudah waktu prediksi.
Fitur per kelompok k: share_k = n_k / n_ind_total; a_k = log1p(1e4 · share_k); anomali z_k = (a_k(t) − rerata a_k(t−52..t−1)) / sd
(hanya masa lalu, ≥ 26 minggu); kelompok komoditas GDELT dipetakan ke id KAGAMI (cabai → cabai_merah & cabai_rawit).
Set (ditetapkan sebelum data): V [z_all], D [z_disrupt], P [z_policy], S [z_stabil, z_supply], ALL [5 kolom].
Kontrol: POS = iw_gap_nat (kesegaran nasional, D-152/D-158: AUC nasional h 4 naik ± 0,015), NEG = derau N(0,1) seed tetap.

Layar (sama dengan D-158/D-161 `cfs_du.py`): z = 1[share_up > 0,5] (provinsi y_h ≠ 0, n ≥ 10); L = logit konsensus C1t OOS mingguan;
increment-only σ(L + γ·x), regresi logistik offset tanpa intersep, walk-forward refit tiap 4 minggu (t' + h ≤ r, ≥ 52 minggu latih),
dinilai minggu 2021-01-04 .. 2023-12-31 − h. ΔAUC = AUC(inc) − AUC(konsensus), interval & p bootstrap blok minggu (13, 1999 rep).
LOLOS bila satu set yang sama: ΔAUC ≥ +0,01 di kedua horizon, batas bawah > 0 di ≥ 1 horizon, q BH < 0,05 (atas set GDELT × 2 h).
→ hasil/b_screen_<tag>.csv
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hasil")
EVAL_START, DEV_END = pd.Timestamp("2021-01-04"), pd.Timestamp("2023-12-31")
BLOCK, REPS, STEP, MIN_WEEKS = 13, 1999, 4, 52
GROUP_TO_KAGAMI = {"beras": ["beras"], "bawang_putih": ["bawang_putih"], "bawang_merah": ["bawang_merah"],
                   "cabai": ["cabai_merah", "cabai_rawit"], "gula_pasir": ["gula_pasir"], "minyak_goreng": ["minyak_goreng"],
                   "daging_sapi": ["daging_sapi"], "daging_ayam": ["daging_ayam"], "telur_ayam": ["telur_ayam"]}
KINDS = ["all", "disrupt", "policy", "stabil", "supply"]
SETS = {"V": ["z_all"], "D": ["z_disrupt"], "P": ["z_policy"], "S": ["z_stabil", "z_supply"], "ALL": [f"z_{k}" for k in KINDS]}


def week_of_utc_day(day):
    """Hari UTC → minggu origin (Senin) yang jendelanya Sabtu t−2 .. Jumat t+4 memuat hari itu."""
    day = pd.to_datetime(day)
    return (day + pd.Timedelta(days=2)) - pd.to_timedelta((day + pd.Timedelta(days=2)).dt.dayofweek, unit="D")


def weekly_features(daily, totals, min_hist=26):
    d = daily.copy()
    d["week"] = week_of_utc_day(d["day_utc"])
    t = totals.copy()
    t["week"] = week_of_utc_day(t["day_utc"])
    tw = t.groupby("week")["n_ind_total"].sum()
    cols = [f"n_{k}" for k in KINDS]
    w = d.groupby(["commodity_group", "week"])[cols].sum()
    groups = w.index.get_level_values(0).unique()
    full = pd.MultiIndex.from_product([groups, tw.index], names=["commodity_group", "week"])
    w = w.reindex(full, fill_value=0).reset_index()
    w = w.merge(tw.rename("n_tot").reset_index(), on="week")
    out = []
    for g, x in w.sort_values("week").groupby("commodity_group"):
        x = x.copy()
        for k in KINDS:
            a = np.log1p(1e4 * x[f"n_{k}"] / x["n_tot"].where(x["n_tot"] > 0))
            mu = a.shift(1).rolling(52, min_periods=min_hist).mean()
            sd = a.shift(1).rolling(52, min_periods=min_hist).std()
            x[f"z_{k}"] = (a - mu) / sd.where(sd > 0)
        for c in GROUP_TO_KAGAMI.get(g, []):
            out.append(x.assign(commodity=c))
    return pd.concat(out, ignore_index=True)[["commodity", "week"] + [f"z_{k}" for k in KINDS] + cols + ["n_tot"]]


def fit_offset_logit(Z, y, off, iters=30):
    b = np.zeros(Z.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(off + Z @ b)))
        Hm = (Z * (p * (1 - p))[:, None]).T @ Z + 1e-6 * np.eye(len(b))
        step = np.linalg.solve(Hm, Z.T @ (y - p) - 1e-6 * b)
        b += step
        if np.abs(step).max() < 1e-9:
            break
    return b


def auc(y, s):
    y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(np.asarray(s, float)).rank(method="average").to_numpy()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def block_indices(n, block, rng):
    k = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block + 1, 1), k)
    return np.concatenate([np.arange(s, min(s + block, n)) for s in starts])[:n]


def inc_screen(nt, cols, h, eval_start=EVAL_START, dev_end=DEV_END, reps=REPS, seed=20261126):
    """nt: commodity, week, z (0/1/NaN), L (logit konsensus), cons, + cols. Increment-only walk-forward → ringkasan ΔAUC."""
    nt = nt.sort_values(["week", "commodity"]).reset_index(drop=True)
    X = nt[cols].to_numpy(float)
    wk, wks = nt["week"].to_numpy(), np.array(sorted(nt["week"].unique()))
    yv, Lv = nt["z"].to_numpy(float), nt["L"].to_numpy(float)
    ok = np.isfinite(X).all(1) & np.isfinite(yv)
    out = np.full(len(nt), np.nan)
    for i in range(0, len(wks), STEP):
        r = wks[i]
        trm = ok & (wk + np.timedelta64(7 * h, "D") <= r)
        if np.unique(wk[trm]).size < MIN_WEEKS:
            continue
        mu, sd = X[trm].mean(0), X[trm].std(0)
        Z = (X - mu) / np.where(sd > 0, sd, 1)
        g = fit_offset_logit(Z[trm], yv[trm], Lv[trm])
        nxt = wks[i + STEP] if i + STEP < len(wks) else wks[-1] + np.timedelta64(7, "D")
        pm = np.isfinite(X).all(1) & (wk >= r) & (wk < nxt)
        out[pm] = 1 / (1 + np.exp(-(Lv[pm] + Z[pm] @ g)))
    q = nt.assign(qq=out)
    q = q[q["z"].notna() & q["qq"].notna() & (q["week"] >= eval_start) & (q["week"] + pd.Timedelta(weeks=h) <= dev_end)]
    q = q.reset_index(drop=True)
    if q.empty or q["z"].nunique() < 2:
        return {"n": len(q), "n_weeks": 0, "auc_cons": np.nan, "auc_inc": np.nan, "d_auc": np.nan, "lo": np.nan, "hi": np.nan, "p": np.nan}
    y, c, p = q["z"].to_numpy(), q["cons"].to_numpy(), q["qq"].to_numpy()
    uw, inv = np.unique(q["week"].to_numpy(), return_inverse=True)
    rows_of = [np.flatnonzero(inv == j) for j in range(len(uw))]
    d = np.full(reps, np.nan)
    for b in range(reps):
        idx = np.concatenate([rows_of[j] for j in block_indices(len(uw), BLOCK, np.random.default_rng(seed + b))])
        if np.unique(y[idx]).size == 2:
            d[b] = auc(y[idx], p[idx]) - auc(y[idx], c[idx])
    lo, hi = np.nanpercentile(d, [2.5, 97.5])
    pv = float(min(1.0, 2 * min(np.nanmean(d <= 0), np.nanmean(d >= 0)) + 1 / reps))
    a_c, a_i = auc(y, c), auc(y, p)
    return {"n": int(len(q)), "n_weeks": int(len(uw)), "auc_cons": a_c, "auc_inc": a_i, "d_auc": a_i - a_c, "lo": float(lo),
            "hi": float(hi), "p": pv, "acc_cons": float(((c > 0.5) == (y > 0.5)).mean()), "acc_inc": float(((p > 0.5) == (y > 0.5)).mean())}


def bh(p):
    p = np.asarray(p, float)
    n = np.isfinite(p).sum()
    q = np.full(len(p), np.nan)
    if n == 0:
        return q
    idx = np.flatnonzero(np.isfinite(p))
    o = idx[np.argsort(p[idx])]
    v = p[o] * n / np.arange(1, n + 1)
    v = np.minimum.accumulate(v[::-1])[::-1]
    q[o] = np.minimum(v, 1)
    return q


def gate(res):
    """Aturan LOLOS per set (kedua horizon)."""
    out = {}
    for s, g in res.groupby("set"):
        g = g.set_index("horizon")
        if not {4, 8} <= set(g.index):
            out[s] = False
            continue
        out[s] = bool((g.loc[4, "d_auc"] >= 0.01) and (g.loc[8, "d_auc"] >= 0.01) and ((g.loc[4, "lo"] > 0) or (g.loc[8, "lo"] > 0))
                      and ((g.loc[4, "q_bh"] < 0.05) or (g.loc[8, "q_bh"] < 0.05)))
    return out


def national_table(h, exp):
    """Konsensus C1t OOS mingguan (D-158 `c1t_weekly.parquet`) + label nasional dari tabel resmi (`base.parquet`)."""
    W = pd.read_parquet(os.path.join(exp, "c1t_weekly.parquet"))
    W = W[W["horizon"] == h]
    base = pd.read_parquet(os.path.join(exp, "base.parquet"), columns=["week", "province_id", "commodity", f"y_{h}"])
    g = W.groupby(["commodity", "week"])["p_up"]
    nt = pd.DataFrame({"cons": g.mean()}).reset_index()
    y = base[f"y_{h}"]
    lab = base.assign(up=(y > 0).astype(float).where(y.notna() & (y != 0))).groupby(["commodity", "week"])["up"].agg(["mean", "count"])
    lab.columns = ["share_up", "n_valid"]
    nt = nt.merge(lab.reset_index(), on=["commodity", "week"], how="left")
    nt["z"] = np.where(nt["n_valid"] >= 10, (nt["share_up"] > 0.5).astype(float), np.nan)
    pc = np.clip(nt["cons"].to_numpy(float), 0.01, 0.99)
    nt["L"] = np.log(pc / (1 - pc))
    return nt


def controls(exp, seed=20261127):
    f = pd.read_parquet(os.path.join(exp, "fresh.parquet"), columns=["week", "commodity", "iw_gap_nat"])
    pos = f.groupby(["commodity", "week"])["iw_gap_nat"].first().rename("ctrl_pos").reset_index()
    rng = np.random.default_rng(seed)
    pos["ctrl_neg"] = rng.normal(size=len(pos))
    return pos


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default=os.environ.get("KAGAMI_EXP"))
    ap.add_argument("--daily")
    ap.add_argument("--totals")
    ap.add_argument("--tag", default="controls")
    ap.add_argument("--reps", type=int, default=REPS)
    a = ap.parse_args()
    ctl = controls(a.exp)
    feats = None
    if a.daily:
        daily = pd.read_csv(a.daily)
        totals = pd.read_csv(a.totals) if a.totals else daily[["day_utc", "n_ind_total"]].drop_duplicates("day_utc")
        feats = weekly_features(daily, totals)
    rows = []
    for h in (4, 8):
        nt = national_table(h, a.exp).merge(ctl, on=["commodity", "week"], how="left")
        if feats is not None:
            nt = nt.merge(feats, on=["commodity", "week"], how="left")
        for name, cols in {"POS": ["ctrl_pos"], "NEG": ["ctrl_neg"]}.items():
            rows.append({"horizon": h, "kind": "control", "set": name, **inc_screen(nt, cols, h, reps=a.reps)})
        if feats is not None:
            for name, cols in SETS.items():
                rows.append({"horizon": h, "kind": "gdelt", "set": name, **inc_screen(nt, cols, h, reps=a.reps)})
    res = pd.DataFrame(rows)
    res["q_bh"] = np.nan
    for k, g in res.groupby("kind"):
        res.loc[g.index, "q_bh"] = bh(g["p"].to_numpy())
    passed = {}
    for k, g in res.groupby("kind"):
        passed.update({f"{k}:{s}": v for s, v in gate(g).items()})
    res["gate_pass_set"] = [passed.get(f"{k}:{s}", False) for k, s in zip(res["kind"], res["set"])]
    res.round(4).to_csv(os.path.join(OUT, f"b_screen_{a.tag}.csv"), index=False)
    pd.set_option("display.width", 220)
    print(res.round(4).to_string(index=False))
