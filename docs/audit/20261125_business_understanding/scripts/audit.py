"""D-155 audit S1 (PROTOKOL_AUDIT.md): universe ranking penuh, V1-K vs V2, anggaran pemantauan, selisih C1-tuned vs IW_NAT.

Keluaran hasil/: audit_universe.csv, audit_watchlist.csv, audit_s1_paired.csv, audit_commodity_share.csv, audit_disagreement*.csv.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_iw_validasi", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from bu import NAIVE, PCT, boot_idx, top_flags  # noqa: E402
from fw_freeze import split_forward  # noqa: E402
from kg import cfg  # noqa: E402
from p_exp import EXP, fit  # noqa: E402
from kagami.features.forecast import LAG_COLUMNS  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
K = ["province_id", "commodity"]
PRESPEC = {4: "R_mom", 8: "R_nat"}
REGULATED = ["beras", "daging_sapi", "gula_pasir", "minyak_goreng"]


def universe(tab, preds, part, h):
    """Kandidat penuh per origin + p_up C1-tuned (diisi ulang untuk baris tanpa target)."""
    p = preds[(preds["variant"] == "base") & (preds["horizon"] == h)]
    out, n_refit, maxdiff = [], 0, 0.0
    tt = tab[["week", "commodity", f"y_{h}"] + LAG_COLUMNS].dropna(subset=[f"y_{h}"] + LAG_COLUMNS)
    for o in sorted(p["origin"].unique()):
        train, test = split_forward(tab, o, h)
        u = test.merge(p[p["origin"] == o][K + ["p_up"]], on=K, how="left")
        if u["p_up"].isna().any():
            pr, _, _ = fit(train, test, tuned_columns("C1t", h)[0], None, None, h, cfg.seed)
            chk = u["p_up"].notna()
            maxdiff = max(maxdiff, float(np.abs(pr[chk.to_numpy()] - u.loc[chk, "p_up"]).max()))
            u["p_up"] = pr
            n_refit += int((~chk).sum())
        tr = tt[tt["week"] + pd.Timedelta(weeks=h) <= o]
        thr = tr.groupby("commodity")[f"y_{h}"].apply(lambda s: np.nanpercentile(s.abs(), PCT))
        u["thr"] = u["commodity"].map(thr)
        u["observed"] = u["y"].notna()
        u["mat_up"] = (u["y"] >= u["thr"]) & u["observed"]
        u["origin"] = o
        out.append(u)
    U = pd.concat(out, ignore_index=True)
    return U, n_refit, maxdiff


def policy_flags(U, score, view):
    if view.startswith("V1-K"):
        return top_flags(U, score, ["origin", "province_id"], k=int(view[-1]), seed=154)
    if view == "V2-10%":
        return top_flags(U, score, ["origin"], frac=0.10, seed=154)
    # V2-setara: N per origin = jumlah alarm V1-K2 pada origin itu
    n = top_flags(U, score, ["origin", "province_id"], k=2, seed=154).groupby(U["origin"]).sum()
    s = U[score].fillna(-np.inf).to_numpy()
    tieb = np.random.default_rng(154).random(len(U))
    order = np.lexsort((tieb, -s))
    rank = pd.Series(np.empty(len(U)), index=U.index)
    rank.iloc[order] = U.iloc[order].groupby("origin").cumcount().to_numpy()
    return rank < U["origin"].map(n).to_numpy()


if __name__ == "__main__":
    tab = pd.read_parquet(os.path.join(EXP, "iw2.parquet"))
    uni_rows, wl_rows, pair_rows, share_rows = [], [], [], []
    for part in ("dev", "test"):
        preds = pd.read_parquet(os.path.join(EXP, f"d151_iw_{part}_preds.parquet"))
        for h in (4, 8):
            U, n_refit, maxdiff = universe(tab, preds, part, h)
            U["s_model"] = U["p_up"]
            for name, f in NAIVE.items():
                U["s_" + name] = f(U, h).to_numpy()
            uni_rows.append({"part": part, "horizon": h, "n_origins": U["origin"].nunique(), "candidates": len(U),
                             "y_zero": int((U["y"] == 0).sum()), "target_missing": int((~U["observed"]).sum()),
                             "refit_rows": n_refit, "refit_maxdiff_on_existing": maxdiff, "base_rate_mat_up": U.loc[U["observed"], "mat_up"].mean()})
            uo = np.sort(U["origin"].unique())
            idx = boot_idx(len(uo), h)
            per = {}
            for view in ("V1-K1", "V1-K2", "V1-K3", "V2-10%", "V2-setara"):
                for sc in ["model"] + list(NAIVE):
                    fl = policy_flags(U, "s_" + sc, view)
                    d = U.assign(fl=fl.to_numpy(), hit=fl.to_numpy() & U["mat_up"].to_numpy(), fl_obs=fl.to_numpy() & U["observed"].to_numpy())
                    g = d.groupby("origin")
                    c = pd.DataFrame({"n": g["fl"].sum(), "hit": g["hit"].sum(), "n_obs": g["fl_obs"].sum(), "pos": g["mat_up"].sum(),
                                      "prov": d[d["fl"]].groupby("origin")["province_id"].nunique()}).reindex(uo).fillna(0)
                    per[(view, sc)] = c
                    wl_rows.append({"part": part, "horizon": h, "view": view, "score": sc,
                                    "alarms_per_origin": c["n"].mean(), "precision": c["hit"].sum() / c["n"].sum(),
                                    "precision_excl_missing": c["hit"].sum() / c["n_obs"].sum(), "recall": c["hit"].sum() / c["pos"].sum(),
                                    "false_alarms_per_origin": (c["n"] - c["hit"]).mean(), "provinces_with_alarm": c["prov"].mean()})
                    if sc == "model":
                        sh = d[d["fl"]].groupby("commodity").size() / d["fl"].sum()
                        share_rows += [{"part": part, "horizon": h, "view": view, "commodity": k, "alarm_share": v} for k, v in sh.items()]
            for comp, role in ((PRESPEC[h], "S1 resmi (pembanding pilihan dev)"), ("R_rev", "kepekaan")):
                a, z = per[("V1-K2", "model")], per[("V1-K2", comp)]
                da = a["hit"].to_numpy()[idx].sum(1) / a["n"].to_numpy()[idx].sum(1) - z["hit"].to_numpy()[idx].sum(1) / z["n"].to_numpy()[idx].sum(1)
                pair_rows.append({"part": part, "horizon": h, "vs": comp, "role": role,
                                  "diff": a["hit"].sum() / a["n"].sum() - z["hit"].sum() / z["n"].sum(),
                                  "lo": np.percentile(da, 2.5), "hi": np.percentile(da, 97.5)})
    pd.DataFrame(uni_rows).round(6).to_csv(os.path.join(OUT, "audit_universe.csv"), index=False)
    W = pd.DataFrame(wl_rows)
    W.round(4).to_csv(os.path.join(OUT, "audit_watchlist.csv"), index=False)
    P = pd.DataFrame(pair_rows)
    P.round(4).to_csv(os.path.join(OUT, "audit_s1_paired.csv"), index=False)
    S = pd.DataFrame(share_rows)
    S.round(4).to_csv(os.path.join(OUT, "audit_commodity_share.csv"), index=False)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(uni_rows).to_string(index=False))
    print(W[W["score"] == "model"].round(3).to_string(index=False))
    print(P.round(4).to_string(index=False))
    print(S[S["view"].isin(["V1-K2", "V2-setara"])].pivot_table(index="commodity", columns=["part", "horizon", "view"], values="alarm_share").round(2).to_string())

    # selisih C1-tuned vs IW_NAT (prediksi D-151)
    rows, rows_c, rows_q = [], [], []
    for part in ("dev", "test"):
        preds = pd.read_parquet(os.path.join(EXP, f"d151_iw_{part}_preds.parquet"))
        preds = preds[np.isfinite(preds["y_true"])]
        for h in (4, 8):
            b = preds[(preds["variant"] == "base") & (preds["horizon"] == h)]
            w = preds[(preds["variant"] == "IW_NAT") & (preds["horizon"] == h)]
            m = b.merge(w[["origin"] + K + ["p_up"]], on=["origin"] + K, suffixes=("_c1", "_iw"))
            m["pc1"], m["piw"] = m["p_up_c1"] > 0.5, m["p_up_iw"] > 0.5
            m["differ"] = m["pc1"] != m["piw"]
            nz = m[m["y_true"] != 0].copy()
            up = nz["y_true"] > 0
            nz["fixed"] = nz["differ"] & (nz["piw"] == up)
            nz["broken"] = nz["differ"] & (nz["pc1"] == up)
            q = pd.qcut(nz["y_true"].abs(), 5, labels=["Q1 terkecil", "Q2", "Q3", "Q4", "Q5 terbesar"])
            rows.append({"part": part, "horizon": h, "rows": len(m), "differ": int(m["differ"].sum()), "differ_share": m["differ"].mean(),
                         "differ_y0": int((m["differ"] & (m["y_true"] == 0)).sum()), "fixed": int(nz["fixed"].sum()), "broken": int(nz["broken"].sum()),
                         "net": int(nz["fixed"].sum() - nz["broken"].sum()), "iw_more_up_when_differ": float(nz.loc[nz["differ"], "piw"].mean())})
            for c, g in nz.groupby("commodity"):
                rows_c.append({"part": part, "horizon": h, "commodity": c, "differ": int(g["differ"].sum()), "fixed": int(g["fixed"].sum()),
                               "broken": int(g["broken"].sum())})
            for qq, g in nz.groupby(q, observed=True):
                rows_q.append({"part": part, "horizon": h, "abs_y_quintile": qq, "differ": int(g["differ"].sum()), "fixed": int(g["fixed"].sum()),
                               "broken": int(g["broken"].sum())})
    D1, D2, D3 = pd.DataFrame(rows), pd.DataFrame(rows_c), pd.DataFrame(rows_q)
    D1.round(4).to_csv(os.path.join(OUT, "audit_disagreement.csv"), index=False)
    D2.to_csv(os.path.join(OUT, "audit_disagreement_commodity.csv"), index=False)
    D3.to_csv(os.path.join(OUT, "audit_disagreement_quintile.csv"), index=False)
    print(D1.round(3).to_string(index=False))
    print(D3.pivot_table(index="abs_y_quintile", columns=["part", "horizon"], values=["fixed", "broken"], observed=True).to_string())
    print(D2.assign(net=D2["fixed"] - D2["broken"]).pivot_table(index="commodity", columns=["part", "horizon"], values="net").to_string())
