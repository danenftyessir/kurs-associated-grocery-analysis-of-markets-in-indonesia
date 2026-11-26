"""D-157 adendum (PROTOKOL §5, pasca-hoc): koreksi logit tahap-2 walk-forward W_CAL pada baris hortikultura → hasil/cal_wi.csv."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import H, official_c1t, np, pd, table  # noqa: E402
from e_eval import compare  # noqa: E402
import feats_wi as F  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
X = ["wn_z_tmax_28", "wn_z_rain_91"]


def fit_offset_logit(Z, y, off, iters=25, ridge=1e-6):
    """Regresi logistik tanpa intersep dengan offset (Newton)."""
    b = np.zeros(Z.shape[1])
    for _ in range(iters):
        eta = off + Z @ b
        p = 1 / (1 + np.exp(-eta))
        g = Z.T @ (y - p) - ridge * b
        Hm = (Z * (p * (1 - p))[:, None]).T @ Z + ridge * np.eye(len(b))
        step = np.linalg.solve(Hm, g)
        b += step
        if np.abs(step).max() < 1e-8:
            break
    return b


cw = table("cw")
P = official_c1t("dev").merge(cw[["week", "province_id", "commodity"] + X].rename(columns={"week": "origin"}),
                              on=["origin", "province_id", "commodity"], how="left")
eps = 1e-6
P["logit"] = np.log(np.clip(P["score"], eps, 1 - eps) / np.clip(1 - P["score"], eps, 1 - eps))
rows, coefs = [], []
for h in H:
    d = P[P["horizon"] == h].copy()
    d["score_cal"] = d["score"]
    horti = d["commodity"].isin(list(F.HORTI))
    origins_ = sorted(d["origin"].unique())
    used = []
    for o in origins_:
        prior = d[horti & (d["origin"] + pd.Timedelta(weeks=h) <= o) & (d["y_true"] != 0)].dropna(subset=X)
        if prior["origin"].nunique() < 8:
            continue
        b = fit_offset_logit(prior[X].to_numpy(float), (prior["y_true"] > 0).to_numpy(float), prior["logit"].to_numpy(float))
        m = horti & (d["origin"] == o) & d[X].notna().all(axis=1)
        d.loc[m, "score_cal"] = 1 / (1 + np.exp(-(d.loc[m, "logit"] + d.loc[m, X].to_numpy(float) @ b)))
        coefs.append({"horizon": h, "origin": o, "b_tmax28": b[0], "b_rain91": b[1], "n_prior": len(prior)})
        used.append(o)
    e = d[d["origin"].isin(used)]
    base, cal = e.assign(score=e["score"]), e.assign(score=e["score_cal"])
    for scope, sel in (("semua", slice(None)), ("hortikultura", e["commodity"].isin(list(F.HORTI)))):
        r, _ = compare(cal[sel] if scope != "semua" else cal, base[sel] if scope != "semua" else base, h)
        bb, cc = (base[sel] if scope != "semua" else base), (cal[sel] if scope != "semua" else cal)
        nzm = bb["y_true"] != 0
        yy = (bb.loc[nzm, "y_true"] > 0).to_numpy(float)
        prob = {"base": np.clip(bb.loc[nzm, "score"].to_numpy(float), eps, 1 - eps), "cal": np.clip(cc.loc[nzm, "score"].to_numpy(float), eps, 1 - eps)}
        brier = {k: float(np.mean((v - yy) ** 2)) for k, v in prob.items()}
        logl = {k: float(-np.mean(yy * np.log(v) + (1 - yy) * np.log(1 - v))) for k, v in prob.items()}
        rows.append({"variant": "W_CAL", "horizon": h, "scope": scope, "n_origins_eval": len(used), **r,
                     "brier_base": brier["base"], "brier_cal": brier["cal"], "logloss_base": logl["base"], "logloss_cal": logl["cal"]})
t = pd.DataFrame(rows)
t.round(4).to_csv(os.path.join(OUT, "cal_wi.csv"), index=False)
c = pd.DataFrame(coefs)
c.round(4).to_csv(os.path.join(OUT, "cal_wi_coef.csv"), index=False)
pd.set_option("display.width", 220)
print(t[["variant", "horizon", "scope", "n_origins_eval", "macro_f1", "diff", "lo", "hi", "p", "d_f1_up", "d_f1_down", "share_origins_pos",
         "d_2021", "d_2022", "d_2023", "brier_base", "brier_cal", "logloss_base", "logloss_cal"]].round(4).to_string(index=False))
print(c.groupby("horizon")[["b_tmax28", "b_rain91"]].describe().round(3).T.to_string())
