"""D-157: bangun tabel kerja `cw.parquet` = `base.parquet` (tabel resmi C1-tuned) + fitur W_NAT, W_LOC, IMP; uji kebocoran.

Mode: `python build_wi.py` (bangun + ringkasan) · `python build_wi.py leak` (uji perturbasi & penghapusan sesudah origin, 12 origin).
Keluaran: EXP/cw.parquet, hasil/wi_summary.json, hasil/wi_leak.csv.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, cfg, np, pd, table  # noqa: E402
from kagami.data import loaders as L  # noqa: E402
import feats_wi as F  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
LAG = int(cfg.params["forecast"]["bps_release_lag_days"])


def inputs():
    w = F.read_power(cfg.source_files("nasa_power"))
    hort = L.load_hortikultura(cfg)
    imp = F.monthly_imports(L.load_comtrade(cfg), L.load_bps_import_monthly(cfg))
    return w, hort, imp


def build(tab, w, hort, imp):
    return pd.concat([F.weather_features(tab, w, hort), F.import_features(tab, imp, LAG)], axis=1)


if __name__ == "__main__":
    base = table()
    keys = base[["week", "province_id", "commodity"]]
    w, hort, imp = inputs()
    if len(sys.argv) > 1 and sys.argv[1] == "leak":
        from kagami.features.forecast import origins
        ref = build(keys, w, hort, imp)
        os_ = origins(cfg, base["week"].drop_duplicates(), 4)
        pick = [os_[i] for i in np.linspace(0, len(os_) - 1, 12).astype(int)]
        rng = np.random.default_rng(157)
        rows = []
        for o in pick:
            keep = (keys["week"] <= o).to_numpy()
            wcut = o - pd.Timedelta(days=1)                   # cuaca yang boleh dipakai: ≤ Minggu sebelum minggu origin
            w1 = w.copy()
            fut = w1["date"] > wcut
            w1.loc[fut, "P"] = rng.gamma(0.5, 20, fut.sum())
            w1.loc[fut, "TMAX"] = rng.normal(31, 3, fut.sum())
            i1 = imp.copy()
            avail = i1["month"] + pd.offsets.MonthEnd(0) + pd.Timedelta(days=LAG)
            futi = avail > o + pd.Timedelta(days=5)
            i1.loc[futi, "kg"] = rng.lognormal(18, 2, futi.sum())
            i1.loc[futi, "usd"] = rng.lognormal(18, 2, futi.sum())
            h1 = hort.copy()                                  # ATAP yang belum terbit pada origin (kecuali fallback 2020, diungkap)
            yrs = sorted(hort["year"].unique())
            unpub = [y for y in yrs if pd.Timestamp(f"{y + 1}-07-01") > o and y != F.share_year(o, yrs)]
            fh = h1["year"].isin(unpub)
            h1.loc[fh, "production_ton"] = rng.uniform(0, 1e6, fh.sum())
            f1 = build(keys, w1, h1, i1)
            f2 = build(keys[keep], w[w["date"] <= wcut], hort[~hort["year"].isin(unpub)], imp[~futi])
            for c in ref.columns:
                a = ref.loc[keep, c].to_numpy(float)
                b1, b2 = f1.loc[keep, c].to_numpy(float), f2[c].to_numpy(float)
                d1 = int((~(np.isclose(a, b1, atol=1e-10) | (np.isnan(a) & np.isnan(b1)))).sum())
                d2 = int((~(np.isclose(a, b2, atol=1e-10) | (np.isnan(a) & np.isnan(b2)))).sum())
                rows.append({"origin": o.date(), "column": c, "diff_T1_perturb": d1, "diff_T2_delete": d2})
            print(o.date(), "selesai", flush=True)
        r = pd.DataFrame(rows)
        r.to_csv(os.path.join(OUT, "wi_leak.csv"), index=False)
        print("sel berbeda T1/T2:", int(r["diff_T1_perturb"].sum()), int(r["diff_T2_delete"].sum()))
        print(r[(r["diff_T1_perturb"] > 0) | (r["diff_T2_delete"] > 0)].groupby("column")[["diff_T1_perturb", "diff_T2_delete"]].sum().to_string())
        raise SystemExit(0)
    feat = build(keys, w, hort, imp)
    cw = pd.concat([base, feat], axis=1)
    assert cw[["week", "province_id", "commodity"]].equals(keys)
    cw.to_parquet(os.path.join(EXP, "cw.parquet"))
    dev = cw[cw["week"] <= pd.Timestamp("2023-12-31")]
    summ = {"rows": len(cw), "share_stability_2020_vs": F.share_stability(hort),
            "nan_share_dev": dev[F.W_NAT + F.W_LOC + F.IMP].isna().mean().round(3).to_dict(),
            "wn_by_commodity_dev_mean_sd": dev.groupby("commodity")[F.W_NAT].agg(["mean", "std"]).round(3).dropna(how="all")
            .pipe(lambda d: d.set_axis([f"{a}|{b}" for a, b in d.columns], axis=1)).to_dict(),
            "imports_kg_by_year": imp.assign(y=imp["month"].dt.year).groupby(["commodity", "y"])["kg"].sum().div(1e6).round(1).unstack().to_dict("index")}
    json.dump(summ, open(os.path.join(OUT, "wi_summary.json"), "w"), indent=1, default=str)
    print(json.dumps({k: summ[k] for k in ("share_stability_2020_vs", "nan_share_dev")}, indent=1))
    print(pd.DataFrame(summ["imports_kg_by_year"]).T.to_string())
