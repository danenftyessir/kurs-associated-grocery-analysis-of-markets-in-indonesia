"""D-158 iterasi 2: koreksi nasional di atas konsensus C1-tuned (META).

Lapisan 1 (per komoditas × minggu t × h, mingguan 2019-01 .. 2023-12): konsensus C1t = rerata p_up OUT-OF-SAMPLE lintas provinsi
(`c1t_weekly.parquet`), L = logit(konsensus). Label z = 1[share_up > 0,5] (provinsi dengan y_h ≠ 0, n ≥ 10). Regresi logistik (C = 1,
fitur distandardisasi, dummy komoditas), walk-forward: refit tiap 4 minggu r pada baris t' + h ≤ r, minimal 52 minggu.
  Q0     : L                                         (kalibrasi konsensus saja; acuan)
  Q_DYN  : L + dinamika konsensus (ΔL 1 & 4 minggu, sd p_up antarprovinsi) + galat nasional terealisasi terakhir (share_up − konsensus
           pada t − h, yang terealisasi tepat pada t) dan rerata 4 galat terakhir
  Q_BR   : L + breadth kota nasional (kb_up_1, kb_up_4, kb_accel, kb_med_4, kb_disp_4, kb_persist)
  Q_ALL  : semua
Lapisan 2 (provinsi): logit p' = logit p_C1t + β · (logit q_v − logit q_0); β satu koefisien, walk-forward (regresi logistik dengan offset)
pada baris provinsi mingguan t' + h ≤ origin (t' ≥ minggu pertama q tersedia). Fungsi dipakai `meta_eval.py`.
→ EXP/meta_q.parquet (commodity, week, horizon, cons, share_up, z, q0, q_dyn, q_br, q_all)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, H, np, pd, table  # noqa: E402

STEP, MIN_WEEKS = 4, 52
EPS = 0.01
KBF = ["kb_up_1", "kb_up_4", "kb_accel", "kb_med_4", "kb_disp_4", "kb_persist"]
SETS = {"q0": ["L"], "q_dyn": ["L", "dL1", "dL4", "cons_sd", "err_last", "err_mean4"], "q_br": ["L"] + KBF,
        "q_all": ["L", "dL1", "dL4", "cons_sd", "err_last", "err_mean4"] + KBF}


def logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def national(h, kb=None):
    W = pd.read_parquet(os.path.join(EXP, "c1t_weekly.parquet"))
    W = W[W["horizon"] == h]
    base = table()[["week", "province_id", "commodity", f"y_{h}"]]
    g = W.groupby(["commodity", "week"])["p_up"]
    nt = pd.DataFrame({"cons": g.mean(), "cons_sd": g.std(), "n_pred": g.size()}).reset_index()
    y = base[f"y_{h}"]
    lab = base.assign(up=(y > 0).astype(float).where(y.notna() & (y != 0))).groupby(["commodity", "week"])["up"].agg(["mean", "count"])
    lab.columns = ["share_up", "n_valid"]
    nt = nt.merge(lab.reset_index(), on=["commodity", "week"], how="left").sort_values(["commodity", "week"]).reset_index(drop=True)
    nt["z"] = np.where(nt["n_valid"] >= 10, (nt["share_up"] > 0.5).astype(float), np.nan)
    nt["L"] = logit(nt["cons"])
    gg = nt.groupby("commodity")
    nt["dL1"] = nt["L"] - gg["L"].shift(1)
    nt["dL4"] = nt["L"] - gg["L"].shift(4)
    err = (nt["share_up"] - nt["cons"]).where(nt["n_valid"] >= 10)
    nt["err_last"] = err.groupby(nt["commodity"]).shift(h)                 # galat minggu t − h, terealisasi pada t
    nt["err_mean4"] = nt.groupby("commodity")["err_last"].transform(lambda s: s.rolling(4, min_periods=2).mean())
    if kb is not None:
        nt = nt.merge(kb[["commodity", "week"] + KBF], on=["commodity", "week"], how="left")
    return nt


def walk_forward(nt, h, cols):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    comm = pd.get_dummies(nt["commodity"]).astype(float).to_numpy()
    X = np.column_stack([nt[cols].to_numpy(float), comm])
    weeks = np.array(sorted(nt["week"].unique()))
    wk = nt["week"].to_numpy()
    ok_tr = nt["z"].notna().to_numpy() & np.isfinite(X).all(1)
    ok_te = np.isfinite(X).all(1)
    out = np.full(len(nt), np.nan)
    for i in range(0, len(weeks), STEP):
        r = weeks[i]
        trm = ok_tr & (wk + np.timedelta64(7 * h, "D") <= r)
        if np.unique(wk[trm]).size < MIN_WEEKS:
            continue
        sc = StandardScaler().fit(X[trm][:, :len(cols)])
        f = lambda A: np.column_stack([sc.transform(A[:, :len(cols)]), A[:, len(cols):]])  # noqa: E731
        m = LogisticRegression(C=1.0, max_iter=2000).fit(f(X[trm]), nt["z"].to_numpy()[trm])
        nxt = weeks[i + STEP] if i + STEP < len(weeks) else weeks[-1] + np.timedelta64(7, "D")
        pm = ok_te & (wk >= r) & (wk < nxt)
        if pm.any():
            out[pm] = m.predict_proba(f(X[pm]))[:, 1]
    return out


def build(kb=None):
    res = []
    for h in H:
        nt = national(h, kb)
        for name, cols in SETS.items():
            if any(c not in nt for c in cols):
                continue
            nt[name] = walk_forward(nt, h, cols)
        res.append(nt.assign(horizon=h))
    return pd.concat(res, ignore_index=True)


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


if __name__ == "__main__":
    kb = None
    kbp = os.path.join(EXP, "kb_national.parquet")
    if os.path.exists(kbp):
        kb = pd.read_parquet(kbp)
    Q = build(kb)
    Q.to_parquet(os.path.join(EXP, "meta_q.parquet"))
    print(Q.groupby("horizon")[[c for c in SETS if c in Q]].describe().round(3).T.to_string())
