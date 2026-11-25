"""D-154 Business Understanding: ukur kriteria S1–S4 PROTOKOL.md untuk C1-tuned vs aturan naif, origin pengembangan saja.

Keluaran hasil/: bu_thresholds.csv, bu_s1_watchlist.csv, bu_s1_paired.csv, bu_s2_calibration.csv, bu_s3_material_moves.csv,
bu_s4_selective.csv, bu_criteria.csv.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261124_task4_optimasi_arah", "scripts"))
import numpy as np
import pandas as pd

from engine import stats_from  # noqa: E402
from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.features.forecast import LAG_COLUMNS  # noqa: E402
from kagami.stats.resampling import moving_block_indices  # noqa: E402
from kagami.tracking.metrics import selective_accuracy  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
REPS = 1999
PCT = cfg.params["forecast"]["large_move_pct"]
K = ["province_id", "commodity"]
NAIVE = {"R_mom": lambda d, h: d["lag_dp_4"], "R_nat": lambda d, h: d["nat_dp_4"],
         "R_rev": lambda d, h: -d["dev_ma13"], "R_seas": lambda d, h: d[f"yseas_52_h{h}"]}


def block(h):
    return int(np.ceil(h / 4)) + 1


def boot_idx(n, h):
    return np.vstack([moving_block_indices(n, block(h), np.random.default_rng(r)) for r in range(REPS)])


def top_flags(d, score, group, k=None, frac=None, seed=0):
    """Tandai baris skor tertinggi per grup; NaN = paling bawah; tie dipecah acak (seed tetap)."""
    s = d[score].fillna(-np.inf).to_numpy()
    tieb = np.random.default_rng(seed).random(len(d))
    order = np.lexsort((tieb, -s))
    rank = pd.Series(np.empty(len(d)), index=d.index)
    tmp = d.iloc[order]
    rank.iloc[order] = tmp.groupby(group).cumcount().to_numpy()
    if k is not None:
        return rank < k
    n = d.groupby(group)[score].transform("size")
    return rank < np.ceil(frac * n)


PART = os.environ.get("PART", "dev")          # test: dibuka sekali (PROTOKOL §3), hanya C1-tuned + aturan naif, naif terbaik dari dev
VARIANTS = ["base", "IW_NAT"] if PART == "dev" else ["base"]
SFX = "" if PART == "dev" else "_test"

if __name__ == "__main__":
    tab = pd.read_parquet(os.path.join(EXP, "iw2.parquet"))
    preds = pd.read_parquet(os.path.join(EXP, f"d151_iw_{PART}_preds.parquet"))
    preds = preds[preds["variant"].isin(VARIANTS) & np.isfinite(preds["y_true"])]
    if PART == "test":
        assert (preds["origin"] >= "2024-01-01").all()
        dev_best = pd.read_csv(os.path.join(OUT, "bu_s1_paired.csv")).drop_duplicates(["horizon", "view"]).set_index(["horizon", "view"])["vs_best_naive"]
    feats = tab[["week"] + K + ["lag_dp_4", "nat_dp_4", "dev_ma13", "yseas_52_h4", "yseas_52_h8"]].rename(columns={"week": "origin"})
    rows_thr, parts = [], []
    for h in (4, 8):
        t = tab[["week", "commodity", f"y_{h}"] + LAG_COLUMNS].dropna(subset=[f"y_{h}"] + LAG_COLUMNS)
        for o in sorted(preds.loc[preds["horizon"] == h, "origin"].unique()):
            tr = t[t["week"] + pd.Timedelta(weeks=h) <= o]
            g = tr.groupby("commodity")[f"y_{h}"]
            thr = g.apply(lambda s: np.nanpercentile(s.abs(), PCT))
            clim = tr[tr[f"y_{h}"] != 0].groupby("commodity")[f"y_{h}"].apply(lambda s: (s > 0).mean())
            rows_thr.append(pd.DataFrame({"origin": o, "horizon": h, "commodity": thr.index, "thr": thr.values,
                                          "clim_up": clim.reindex(thr.index).values}))
    TH = pd.concat(rows_thr, ignore_index=True)
    TH.groupby(["horizon", "commodity"])["thr"].median().unstack(0).apply(np.expm1).round(4).to_csv(os.path.join(OUT, f"bu_thresholds{SFX}.csv"))
    D = preds.merge(feats, on=["origin"] + K, how="left").merge(TH, on=["origin", "horizon", "commodity"], how="left")
    D["mat_up"] = D["y_true"] >= D["thr"]
    D["mat_move"] = D["y_true"].abs() >= D["thr"]
    print("ambang kenaikan material (median, %):\n", TH.groupby(["horizon", "commodity"])["thr"].median().unstack(0).apply(np.expm1).mul(100).round(1).to_string())
    print("porsi kenaikan material:", D[D["variant"] == "base"].groupby("horizon")["mat_up"].mean().round(4).to_dict(), flush=True)

    # S1 / S1b: daftar pantau
    s1_rows, pair_rows, crit = [], [], []
    for h in (4, 8):
        b = D[(D["variant"] == "base") & (D["horizon"] == h)].copy()
        b["s_model"] = b["p_up"]
        if "IW_NAT" in VARIANTS:
            nat = D[(D["variant"] == "IW_NAT") & (D["horizon"] == h)].set_index(["origin"] + K)["p_up"]
            b["s_IW_NAT"] = nat.reindex(pd.MultiIndex.from_frame(b[["origin"] + K])).to_numpy()
        for name, f in NAIVE.items():
            b["s_" + name] = f(b, h).to_numpy()
        uo = np.sort(b["origin"].unique())
        idx = boot_idx(len(uo), h)
        per = {}
        models = ["model", "IW_NAT"] if "IW_NAT" in VARIANTS else ["model"]
        for sc in models + list(NAIVE):
            for view, kw in (("V1_prov_top2", {"k": 2, "group": ["origin", "province_id"]}), ("V2_nat_top10pct", {"frac": 0.10, "group": ["origin"]})):
                fl = top_flags(b, "s_" + sc, kw["group"], k=kw.get("k"), frac=kw.get("frac"), seed=154)
                g = b.assign(fl=fl, hit=fl & b["mat_up"]).groupby("origin")
                c = pd.DataFrame({"n": g["fl"].sum(), "hit": g["hit"].sum(), "pos": g["mat_up"].sum()}).reindex(uo)
                per[(sc, view)] = c
                bp = c["hit"].to_numpy()[idx].sum(1) / c["n"].to_numpy()[idx].sum(1)
                s1_rows.append({"horizon": h, "view": view, "score": sc, "precision": c["hit"].sum() / c["n"].sum(),
                                "prec_lo": np.percentile(bp, 2.5), "prec_hi": np.percentile(bp, 97.5),
                                "recall": c["hit"].sum() / c["pos"].sum(), "base_rate": b["mat_up"].mean(), "n_flagged": int(c["n"].sum())})
        S1h = pd.DataFrame([r for r in s1_rows if r["horizon"] == h])
        for view in ("V1_prov_top2", "V2_nat_top10pct"):
            if PART == "dev":
                best = S1h[(S1h["view"] == view) & S1h["score"].isin(NAIVE)].sort_values("precision").iloc[-1]["score"]
            else:
                best = dev_best.loc[(h, view)]
            for sc in models:
                a, z = per[(sc, view)], per[(best, view)]
                da = a["hit"].to_numpy()[idx].sum(1) / a["n"].to_numpy()[idx].sum(1) - z["hit"].to_numpy()[idx].sum(1) / z["n"].to_numpy()[idx].sum(1)
                diff = a["hit"].sum() / a["n"].sum() - z["hit"].sum() / z["n"].sum()
                pair_rows.append({"horizon": h, "view": view, "score": sc, "vs_best_naive": best, "diff": diff,
                                  "lo": np.percentile(da, 2.5), "hi": np.percentile(da, 97.5)})
    S1 = pd.DataFrame(s1_rows)
    P1 = pd.DataFrame(pair_rows)
    S1.round(4).to_csv(os.path.join(OUT, f"bu_s1_watchlist{SFX}.csv"), index=False)
    P1.round(4).to_csv(os.path.join(OUT, f"bu_s1_paired{SFX}.csv"), index=False)
    pd.set_option("display.width", 220)
    print(S1.round(3).to_string(index=False))
    print(P1.round(4).to_string(index=False), flush=True)

    # S2: kalibrasi (y ≠ 0)
    s2 = []
    for h in (4, 8):
        for v in VARIANTS:
            d = D[(D["variant"] == v) & (D["horizon"] == h) & (D["y_true"] != 0)].dropna(subset=["clim_up"])
            y = (d["y_true"] > 0).astype(float)
            bm, bc = (d["p_up"] - y) ** 2, (d["clim_up"] - y) ** 2
            uo, inv = np.unique(d["origin"].to_numpy(), return_inverse=True)
            Sm, Sc = np.zeros(len(uo)), np.zeros(len(uo))
            np.add.at(Sm, inv, bm.to_numpy())
            np.add.at(Sc, inv, bc.to_numpy())
            idx = boot_idx(len(uo), h)
            bss_b = 1 - Sm[idx].sum(1) / Sc[idx].sum(1)
            bins = np.clip((d["p_up"] * 10).astype(int), 0, 9)
            cal = pd.DataFrame({"b": bins, "p": d["p_up"], "y": y}).groupby("b").agg(p=("p", "mean"), y=("y", "mean"), n=("y", "size"))
            ece = float((cal["n"] * (cal["p"] - cal["y"]).abs()).sum() / cal["n"].sum())
            s2.append({"horizon": h, "model": v, "brier": bm.mean(), "brier_clim": bc.mean(), "bss": 1 - Sm.sum() / Sc.sum(),
                       "bss_lo": np.percentile(bss_b, 2.5), "bss_hi": np.percentile(bss_b, 97.5), "ece": ece, "n": len(d)})
            cal.assign(horizon=h, model=v).to_csv(os.path.join(OUT, f"bu_s2_reliability_{v}_h{h}{SFX}.csv"))
    S2 = pd.DataFrame(s2)
    S2.round(4).to_csv(os.path.join(OUT, f"bu_s2_calibration{SFX}.csv"), index=False)
    print(S2.round(4).to_string(index=False), flush=True)

    # S3: arah saat bergerak material
    s3 = []
    for h in (4, 8):
        for v in VARIANTS:
            d = D[(D["variant"] == v) & (D["horizon"] == h) & D["mat_move"] & (D["y_true"] != 0)]
            up = (d["y_true"] > 0).to_numpy()
            uo, inv = np.unique(d["origin"].to_numpy(), return_inverse=True)
            out = {}
            for name, pu in (("model", d["p_up"].to_numpy() > 0.5), ("R_mom_sign", ~(d["lag_dp_4"].to_numpy() < 0))):
                cells = np.stack([up & pu, up & ~pu, ~up & pu, ~up & ~pu], 1).astype(float)
                C = np.zeros((len(uo), 4))
                np.add.at(C, inv, cells)
                out[name] = C
            idx = boot_idx(len(uo), h)
            fm, fr = stats_from(out["model"].sum(0))["macro_f1"], stats_from(out["R_mom_sign"].sum(0))["macro_f1"]
            db = stats_from(out["model"][idx].sum(1))["macro_f1"] - stats_from(out["R_mom_sign"][idx].sum(1))["macro_f1"]
            s3.append({"horizon": h, "model": v, "macro_f1_model": float(fm), "macro_f1_mom_sign": float(fr), "diff": float(fm - fr),
                       "lo": float(np.nanpercentile(db, 2.5)), "hi": float(np.nanpercentile(db, 97.5)), "n": len(d)})
    S3 = pd.DataFrame(s3)
    S3.round(4).to_csv(os.path.join(OUT, f"bu_s3_material_moves{SFX}.csv"), index=False)
    print(S3.round(4).to_string(index=False), flush=True)

    # S4: selektif
    s4 = []
    for h in (4, 8):
        for v in VARIANTS:
            d = D[(D["variant"] == v) & (D["horizon"] == h)]
            for r in selective_accuracy(d["y_true"], d["p_up"], d["origin"], (0.25, 0.5, 1.0)):
                s4.append({"horizon": h, "model": v, **r})
    S4 = pd.DataFrame(s4)
    S4.round(4).to_csv(os.path.join(OUT, f"bu_s4_selective{SFX}.csv"), index=False)
    print(S4.round(4).to_string(index=False))

    # kriteria
    crit = []
    for h in (4, 8):
        p = P1[(P1["horizon"] == h) & (P1["view"] == "V1_prov_top2") & (P1["score"] == "model")].iloc[0]
        s2r = S2[(S2["horizon"] == h) & (S2["model"] == "base")].iloc[0]
        s3r = S3[(S3["horizon"] == h) & (S3["model"] == "base")].iloc[0]
        crit.append({"horizon": h, "S1_pass": bool(p["diff"] > 0 and p["lo"] > 0), "S1_diff": p["diff"], "S1_lo": p["lo"],
                     "S2_pass": bool(s2r["bss"] > 0 and s2r["bss_lo"] > 0 and s2r["ece"] <= 0.05), "S2_bss": s2r["bss"], "S2_ece": s2r["ece"],
                     "S3_pass": bool(s3r["diff"] > 0 and s3r["lo"] > 0), "S3_diff": s3r["diff"], "S3_lo": s3r["lo"]})
    CR = pd.DataFrame(crit)
    CR.round(4).to_csv(os.path.join(OUT, f"bu_criteria{SFX}.csv"), index=False)
    print(CR.round(4).to_string(index=False))
