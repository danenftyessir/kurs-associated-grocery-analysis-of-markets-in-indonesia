"""D-151 keluarga B: panel mingguan harga produsen PIHPS (varian & agregasi resmi, TANPA pengisian) → kelayakan, lead-lag, fitur.

1. `load_pihps(cfg, "pihps_producer")` → `select_variants` → `aggregate_weekly` (minggu tanpa hari teramati = NaN, tidak diisi).
2. Cakupan per komoditas (provinsi berisi, awal riwayat, porsi sel teramati 2019–2026, carry_forward di antara sel berisi,
   median log produsen − log eceran) → hasil/pr_coverage.csv.
3. Lead-lag periode pengembangan (2018–2023): korelasi Δprodusen(t−k) → Δeceran(t), sebaliknya; kesesuaian arah produsen 4 minggu
   vs label eceran h ke depan dibanding momentum eceran → hasil/pr_leadlag.csv.
4. Fitur PROTOKOL.md §3 (hanya informasi s.d. minggu t) → EXP/pr.parquet (= base.parquet + kolom), hasil/pr_features.csv.
5. Kebocoran: produsen & eceran sesudah origin dirusak → fitur ≤ origin identik (2 origin).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.data.loaders import load_pihps  # noqa: E402
from kagami.data.weekly import aggregate_weekly, select_variants  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
KEYS = ["province_id", "commodity"]
FEATS = ["pr_dp_1", "pr_dp_4", "pr_dp_8", "pr_vol_13", "pr_age", "pr_gap", "pr_gap_chg_1", "pr_gap_chg_4", "pr_gap_chg_8",
         "pr_gap_dev52", "pr_nat_dp_1", "pr_nat_dp_4", "pr_nat_dp_8", "pr_nat_up_4", "pr_nat_disp_4", "pr_nat_n"]


def by_comm(df, how):
    g = df.T.groupby(df.columns.get_level_values("commodity"))
    return getattr(g, "transform")(how).T


def build_features(P, R):
    """P, R: minggu × (province_id, commodity) log harga produsen / eceran (NaN = tidak ada). Hanya operasi ke belakang."""
    F = {f"pr_dp_{k}": P - P.shift(k) for k in (1, 4, 8)}
    F["pr_vol_13"] = F["pr_dp_1"].rolling(13, min_periods=6).std()
    idx = pd.DataFrame(np.arange(len(P))[:, None].repeat(P.shape[1], 1), index=P.index, columns=P.columns, dtype=float)
    last = idx.where(P.notna()).ffill()
    F["pr_age"] = (idx - last).clip(upper=52)
    gap = R - P
    F["pr_gap"] = gap
    for k in (1, 4, 8):
        F[f"pr_gap_chg_{k}"] = gap - gap.shift(k)
    F["pr_gap_dev52"] = gap - gap.rolling(52, min_periods=26).mean()
    for k in (1, 4, 8):
        F[f"pr_nat_dp_{k}"] = by_comm(F[f"pr_dp_{k}"], "mean")
    d4 = F["pr_dp_4"]
    F["pr_nat_up_4"] = by_comm((d4 > 0).astype(float).where(d4.notna()), "mean")
    F["pr_nat_disp_4"] = by_comm(d4, "std")
    F["pr_nat_n"] = by_comm(P.notna().astype(float), "sum")
    return F


if __name__ == "__main__":
    raw = load_pihps(cfg, "pihps_producer")
    daily = select_variants(cfg, raw)
    pw = aggregate_weekly(cfg, daily)
    pw.to_parquet(os.path.join(EXP, "pr_panel.parquet"))
    rt = read_artifact(cfg, "panel_weekly")

    # 2. cakupan
    has = pw[pw["status"] != "missing"]
    m = has.merge(rt[["week", "province_id", "commodity", "log_price"]], on=["week"] + KEYS, suffixes=("_pr", "_rt"))
    win = pw[(pw["week"] >= "2019-01-01")]
    cov = pd.DataFrame({
        "provinces_any": has.groupby("commodity")["province_id"].nunique(),
        "first_week": has.groupby("commodity")["week"].min(),
        "share_cells_nonmissing_2019on": win.groupby("commodity")["status"].apply(lambda s: (s != "missing").mean()),
        "share_cf_of_nonmissing": has.groupby("commodity")["status"].apply(lambda s: (s == "carry_forward").mean()),
        "share_observed_of_nonmissing": has.groupby("commodity")["status"].apply(lambda s: (s == "observed").mean()),
        "gap_median_rt_minus_pr": (m["log_price_rt"] - m["log_price_pr"]).groupby(m["commodity"]).median(),
    })
    jul24 = has[(has["week"] >= "2024-07-01") & (has["week"] <= "2024-07-31")]
    cov["provinces_jul2024"] = jul24.groupby("commodity")["province_id"].nunique()
    cov = cov.fillna({"provinces_jul2024": 0})
    cov.to_csv(os.path.join(OUT, "pr_coverage.csv"))
    pd.set_option("display.width", 250)
    print(cov.round(3).to_string())

    P = pw.pivot(index="week", columns=KEYS, values="log_price").sort_index()
    Rp = rt.pivot(index="week", columns=KEYS, values="log_price").reindex(index=P.index, columns=P.columns)
    # 3. lead-lag (pengembangan saja)
    dev = (P.index >= "2018-01-01") & (P.index <= "2023-12-31")
    dP, dR = P.diff(), Rp.diff()
    rows = []
    for c in sorted(set(P.columns.get_level_values("commodity"))):
        cols = [k for k in P.columns if k[1] == c]
        r = {"commodity": c}
        for k in range(0, 5):
            x, y = dP[cols].shift(k)[dev].to_numpy().ravel(), dR[cols][dev].to_numpy().ravel()
            ok = np.isfinite(x) & np.isfinite(y)
            r[f"corr_dpr_lag{k}_drt"] = np.corrcoef(x[ok], y[ok])[0, 1] if ok.sum() > 30 else np.nan
            if k == 0:
                r["n_pairs"] = int(ok.sum())
        for k in (1, 2):
            x, y = dR[cols].shift(k)[dev].to_numpy().ravel(), dP[cols][dev].to_numpy().ravel()
            ok = np.isfinite(x) & np.isfinite(y)
            r[f"corr_drt_lag{k}_dpr"] = np.corrcoef(x[ok], y[ok])[0, 1] if ok.sum() > 30 else np.nan
        for h in (4, 8):
            fut = (Rp[cols].shift(-h) - Rp[cols])[dev].to_numpy().ravel()
            p4 = (P[cols] - P[cols].shift(4))[dev].to_numpy().ravel()
            l4 = (Rp[cols] - Rp[cols].shift(4))[dev].to_numpy().ravel()
            ok = np.isfinite(p4) & np.isfinite(fut) & np.isfinite(l4) & (p4 != 0) & (fut != 0) & (l4 != 0)
            r[f"n_dir_{h}"] = int(ok.sum())
            r[f"dir_agree_pr4_fwd{h}"] = float((np.sign(p4[ok]) == np.sign(fut[ok])).mean()) if ok.any() else np.nan
            r[f"dir_agree_rt4_fwd{h}_same_rows"] = float((np.sign(l4[ok]) == np.sign(fut[ok])).mean()) if ok.any() else np.nan
        rows.append(r)
    ll = pd.DataFrame(rows)
    ll.round(4).to_csv(os.path.join(OUT, "pr_leadlag.csv"), index=False)
    print(ll.round(3).to_string(index=False))

    # 4. fitur
    base = pd.read_parquet(os.path.join(EXP, "base.parquet"))
    weeks = pd.DatetimeIndex(sorted(base["week"].unique()))
    Pw = P.reindex(weeks)
    Rw = base.pivot(index="week", columns=KEYS, values="log_p").reindex(index=weeks, columns=P.columns)
    F = build_features(Pw, Rw)
    long = pd.concat({n: f.stack(KEYS, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + KEYS
    out = base.merge(long.reset_index(), on=["week"] + KEYS, how="left")
    assert out[["week"] + KEYS].equals(base[["week"] + KEYS])
    out.to_parquet(os.path.join(EXP, "pr.parquet"))
    d = out[(out["week"] >= "2019-01-01")]
    desc = pd.DataFrame({"na_share": d[FEATS].isna().mean(), "mean": d[FEATS].mean(), "sd": d[FEATS].std(),
                         "share_zero": (d[FEATS] == 0).mean(), "corr_lag_dp_1": d[FEATS + ["lag_dp_1"]].corr()["lag_dp_1"]})
    desc.round(4).to_csv(os.path.join(OUT, "pr_features.csv"))
    print(desc.round(4).to_string())
    na_c = d.groupby("commodity")[["pr_dp_4", "pr_gap", "pr_nat_dp_4"]].apply(lambda g: g.isna().mean())
    na_c.round(3).to_csv(os.path.join(OUT, "pr_features_na_by_commodity.csv"))
    print(na_c.round(3).to_string())

    # 5. kebocoran
    rng = np.random.default_rng(1512)
    for o in (pd.Timestamp("2022-06-20"), pd.Timestamp("2025-03-24")):
        P2, R2 = Pw.copy(), Rw.copy()
        P2[P2.index > o] += rng.normal(0, 0.5, P2[P2.index > o].shape)
        R2[R2.index > o] += rng.normal(0, 0.5, R2[R2.index > o].shape)
        P2.iloc[(P2.index > o).nonzero()[0][:3], :5] = np.nan      # juga ubah pola kosong sesudah origin
        G = build_features(P2, R2)
        same = all(np.allclose(G[k][G[k].index <= o].to_numpy(float), F[k][F[k].index <= o].to_numpy(float), equal_nan=True)
                   for k in F)
        print("kebocoran", o.date(), "fitur ≤ origin identik:", same)
        assert same
