"""D-160C gerbang 5: sinyal SIJAGUNG (stok & pembelian jagung pabrik pakan, nasional bulanan) untuk daging ayam & telur, origin dev.

Fitur nasional bulan m (baris total ekspor), tersedia pada akhir bulan m + 90 hari (ekspor publik 2026-11-26 berakhir Agustus 2026 → lag
± 3 bulan; konservatif): sj_days (kecukupan produksi, hari), sj_stock_yoy (Δ log stok vs 12 bulan), sj_buy_yoy (Δ log volume pembelian vs
12 bulan), sj_price_mom3 (Δ log harga beli 3 bulan), sj_price_yoy. Minggu t memakai bulan terakhir dengan available_at ≤ t.
(a) Korelasi residual C1t (baris ayam & telur, y ≠ 0) mentah & parsial (CTRL D-157) + bootstrap blok origin.
(b) Arah nasional: increment-only σ(L + γ·x) di atas konsensus C1t mingguan OOS (D-158), walk-forward, AUC vs konsensus 2021–2023.
→ hasil/sij_features.csv, hasil/sij_du_rows.csv, hasil/sij_du_national.csv
"""
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_nasional_lokal", "scripts"))
from m_common import AUD, H, bh_fdr, cfg, np, official_c1t, pd, table  # noqa: E402
import meta_build as MB  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
RAW = os.path.join(cfg.raw_dir, "ditjenpkh_pakan")
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
COMMS = ["daging_ayam", "telur_ayam"]
LAG_DAYS = 90
FEATS = ["sj_days", "sj_stock_yoy", "sj_buy_yoy", "sj_price_mom3", "sj_price_yoy"]
CTRL = ["nat_dp_1", "nat_dp_4", "lag_dp_4", "dev_ma13"]


def national_series(fn, a, b):
    vals = list(openpyxl.load_workbook(os.path.join(RAW, fn), read_only=True)["data"].iter_rows(values_only=True))
    years, months = vals[4], vals[5]
    total = [r for r in vals[7:] if r[0] is None and r[1] is None and any(isinstance(x, (int, float)) for x in r[2:])][-1]
    out, y = [], None
    for j in range(2, len(months), 2):
        y = years[j] if years[j] is not None else y
        if months[j] is None or total[j] is None:
            continue
        out.append({"month": pd.Timestamp(year=int(y), month=MONTHS.index(months[j]) + 1, day=1), a: float(total[j]), b: float(total[j + 1])})
    return pd.DataFrame(out)


def features():
    s = national_series("sijagung_stok_2019-01_2026-10.xlsx", "stock", "days")
    p = national_series("sijagung_pembelian_2019-01_2026-10.xlsx", "buy", "price")
    m = s.merge(p, on="month").sort_values("month").reset_index(drop=True)
    m["sj_days"] = m["days"]
    m["sj_stock_yoy"] = np.log(m["stock"]) - np.log(m["stock"].shift(12))
    m["sj_buy_yoy"] = np.log(m["buy"]) - np.log(m["buy"].shift(12))
    m["sj_price_mom3"] = np.log(m["price"]) - np.log(m["price"].shift(3))
    m["sj_price_yoy"] = np.log(m["price"]) - np.log(m["price"].shift(12))
    m["available_at"] = m["month"] + pd.offsets.MonthEnd(0) + pd.Timedelta(days=LAG_DAYS)
    return m


def weekly(m, weeks):
    av = m["available_at"].to_numpy()
    rows = []
    for t in weeks:
        k = int((av <= np.datetime64(t)).sum())
        rows.append({"week": t, **({f: m[f].iloc[k - 1] for f in FEATS} if k else {})})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    m = features()
    m.round(5).to_csv(os.path.join(OUT, "sij_features.csv"), index=False)
    weeks = pd.DatetimeIndex(sorted(table()["week"].unique()))
    W = weekly(m, weeks)
    base = table()
    P = official_c1t("dev")
    P = P[(P["y_true"] != 0) & P["commodity"].isin(COMMS)].copy()
    P["r"] = (P["y_true"] > 0).astype(float) - P["score"]
    D = P.merge(base[["week", "province_id", "commodity"] + CTRL].rename(columns={"week": "origin"}), on=["origin", "province_id", "commodity"])
    D = D.merge(W.rename(columns={"week": "origin"}), on="origin", how="left")
    rows = []
    for h in H:
        d = D[D["horizon"] == h].copy()
        for f in FEATS:
            rows.append({"horizon": h, "feature": f, "kind": "mentah", **screen(d, f, h)})
            g = d.dropna(subset=[f] + CTRL)
            res = pd.Series(np.nan, index=d.index)
            for c, gg in g.groupby("commodity"):
                X = np.column_stack([np.ones(len(gg)), gg[CTRL].to_numpy(float)])
                b, *_ = np.linalg.lstsq(X, gg[f].to_numpy(float), rcond=None)
                res.loc[gg.index] = gg[f].to_numpy(float) - X @ b
            d[f + "__p"] = res
            rows.append({"horizon": h, "feature": f, "kind": "parsial", **screen(d, f + "__p", h)})
    t = pd.DataFrame(rows)
    t["q_bh"] = np.nan
    for (h, k), g in t.groupby(["horizon", "kind"]):
        ok = g["p"].notna()
        t.loc[g.index[ok], "q_bh"] = bh_fdr(g.loc[ok, "p"].to_numpy())
    t.round(4).to_csv(os.path.join(OUT, "sij_du_rows.csv"), index=False)
    nat = []
    for h in H:
        nt = MB.national(h)
        nt = nt[nt["commodity"].isin(COMMS)].merge(W, on="week", how="left").reset_index(drop=True)
        for cols in (["sj_days"], ["sj_stock_yoy", "sj_buy_yoy"], ["sj_price_mom3", "sj_price_yoy"], FEATS):
            X = nt[cols].to_numpy(float)
            wk, wks = nt["week"].to_numpy(), np.array(sorted(nt["week"].unique()))
            ok = np.isfinite(X).all(1) & nt["z"].notna().to_numpy()
            out = np.full(len(nt), np.nan)
            for i in range(0, len(wks), 4):
                r = wks[i]
                trm = ok & (wk + np.timedelta64(7 * h, "D") <= r)
                if np.unique(wk[trm]).size < 52:
                    continue
                mu, sd = X[trm].mean(0), X[trm].std(0)
                Z = (X - mu) / np.where(sd > 0, sd, 1)
                g = MB.fit_offset_logit(Z[trm], nt["z"].to_numpy()[trm], nt["L"].to_numpy()[trm])
                nxt = wks[i + 4] if i + 4 < len(wks) else wks[-1] + np.timedelta64(7, "D")
                pm = np.isfinite(X).all(1) & (wk >= r) & (wk < nxt)
                out[pm] = 1 / (1 + np.exp(-(nt["L"].to_numpy()[pm] + Z[pm] @ g)))
            q = nt.assign(qq=out)
            q = q[q["z"].notna() & q["qq"].notna() & (q["week"] >= pd.Timestamp("2021-01-04")) & (q["week"] + pd.Timedelta(weeks=h) <= pd.Timestamp("2023-12-31"))]
            nat.append({"horizon": h, "features": "+".join(cols), "n": len(q), "auc_cons": roc_auc_score(q["z"], q["cons"]),
                        "auc_inc": roc_auc_score(q["z"], q["qq"]), "acc_cons": float(((q["cons"] > 0.5) == (q["z"] > 0.5)).mean()),
                        "acc_inc": float(((q["qq"] > 0.5) == (q["z"] > 0.5)).mean())})
    n = pd.DataFrame(nat)
    n["d_auc"] = n["auc_inc"] - n["auc_cons"]
    n.round(4).to_csv(os.path.join(OUT, "sij_du_national.csv"), index=False)
    pd.set_option("display.width", 220)
    print(m[["month", "stock", "days", "buy", "price"]].iloc[[0, 24, 48, -1]].to_string(index=False))
    print(t.pivot_table(index=["feature", "kind"], columns="horizon", values=["rho", "lo", "hi", "q_bh"]).round(3).to_string())
    print(n.round(4).to_string(index=False))
