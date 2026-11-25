"""D-150 pilot: panel mingguan pedagang besar (varian & aturan agregasi SAMA dengan panel resmi) → uji lead-lag & fitur grosir.

1. `load_pihps(cfg, "pihps_wholesale")` → `select_variants` → `aggregate_weekly` (rerata hari teramati, status D-021).
2. Cakupan & kelayakan seri grosir; selisih level grosir − eceran.
3. Lead-lag per komoditas (dalam seri, 2018–2023 = periode pengembangan saja): korelasi Δlog grosir minggu t−k dengan Δlog eceran
   minggu t (k = 0..4) dan sebaliknya; kesesuaian arah perubahan grosir 4 minggu terakhir dengan arah label eceran h minggu ke depan.
4. Fitur (hanya informasi s.d. minggu t; ffill grosir ≤ 8 minggu seperti price_dynamics):
   ws_dp_1/4/8 (Δ log grosir), ws_nat_dp_4 (rerata komoditas lintas provinsi), ws_gap (log grosir − log eceran),
   ws_gap_dev52 (ws_gap − rerata 52 minggu ke belakang), ws_rel_4 (Δ4 grosir − Δ4 eceran).
→ EXP/ws.parquet (= base.parquet + kolom fitur), hasil/ws_coverage.csv, hasil/ws_leadlag.csv.
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
from kagami.data.weekly import aggregate_weekly, eligibility, select_variants  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
KEYS = ["province_id", "commodity"]
FEATS = ["ws_dp_1", "ws_dp_4", "ws_dp_8", "ws_nat_dp_4", "ws_gap", "ws_gap_dev52", "ws_rel_4"]


def by_comm_mean(df):
    return df.T.groupby(df.columns.get_level_values("commodity")).transform("mean").T


if __name__ == "__main__":
    raw = load_pihps(cfg, "pihps_wholesale")
    daily = select_variants(cfg, raw)
    ws = aggregate_weekly(cfg, daily)
    ws.to_parquet(os.path.join(EXP, "ws_panel.parquet"))
    el = eligibility(cfg, ws)
    rt = read_artifact(cfg, "panel_weekly")
    cov = (ws.groupby("commodity")["status"].value_counts(normalize=True).unstack().fillna(0)
           .join(el.groupby("commodity")["eligible"].sum().rename("eligible_series")))
    m = ws.merge(rt[["week", "province_id", "commodity", "log_price"]], on=["week"] + KEYS, suffixes=("_ws", "_rt"))
    gap = (m["log_price_ws"] - m["log_price_rt"]).groupby(m["commodity"])
    cov = cov.join(gap.median().rename("gap_median")).join(gap.apply(lambda s: (s < 0).mean()).rename("share_ws_below_rt"))
    cov.round(4).to_csv(os.path.join(OUT, "ws_coverage.csv"))
    print(cov.round(3).to_string())

    W = ws.pivot(index="week", columns=KEYS, values="log_price").sort_index()
    R = rt.pivot(index="week", columns=KEYS, values="log_price").reindex(index=W.index, columns=W.columns)
    # lead-lag pada periode pengembangan saja (2018-01 .. 2023-12)
    dev = (W.index >= "2018-01-01") & (W.index <= "2023-12-31")
    dW, dR = W.diff(), R.diff()
    rows = []
    for c in sorted(set(W.columns.get_level_values("commodity"))):
        cols = [k for k in W.columns if k[1] == c]
        r = {"commodity": c}
        for k in range(0, 5):
            x, y = dW[cols].shift(k)[dev].to_numpy().ravel(), dR[cols][dev].to_numpy().ravel()
            ok = np.isfinite(x) & np.isfinite(y)
            r[f"corr_dws_lag{k}_drt"] = np.corrcoef(x[ok], y[ok])[0, 1]
        for k in (1, 2):
            x, y = dR[cols].shift(k)[dev].to_numpy().ravel(), dW[cols][dev].to_numpy().ravel()
            ok = np.isfinite(x) & np.isfinite(y)
            r[f"corr_drt_lag{k}_dws"] = np.corrcoef(x[ok], y[ok])[0, 1]
        for h in (4, 8):
            g4 = (W[cols] - W[cols].shift(4))[dev].to_numpy().ravel()
            fut = (R[cols].shift(-h) - R[cols])[dev].to_numpy().ravel()
            ok = np.isfinite(g4) & np.isfinite(fut) & (g4 != 0) & (fut != 0)
            r[f"dir_agree_ws4_vs_rt_fwd{h}"] = float((np.sign(g4[ok]) == np.sign(fut[ok])).mean())
            l4 = (R[cols] - R[cols].shift(4))[dev].to_numpy().ravel()
            ok2 = np.isfinite(l4) & np.isfinite(fut) & (l4 != 0) & (fut != 0)
            r[f"dir_agree_rt4_vs_rt_fwd{h}"] = float((np.sign(l4[ok2]) == np.sign(fut[ok2])).mean())
            gp = (W[cols] - R[cols])
            gd = (gp - gp.rolling(52, min_periods=26).mean())[dev].to_numpy().ravel()
            ok3 = np.isfinite(gd) & np.isfinite(fut) & (gd != 0) & (fut != 0)
            r[f"dir_agree_gapdev_vs_rt_fwd{h}"] = float((np.sign(gd[ok3]) == np.sign(fut[ok3])).mean())
        rows.append(r)
    ll = pd.DataFrame(rows)
    ll.round(4).to_csv(os.path.join(OUT, "ws_leadlag.csv"), index=False)
    pd.set_option("display.width", 250)
    print(ll.round(3).to_string(index=False))

    # fitur
    base = pd.read_parquet(os.path.join(EXP, "base.parquet"))
    weeks = pd.DatetimeIndex(sorted(base["week"].unique()))
    Wf = W.reindex(weeks).ffill(limit=8)
    Rf = base.pivot(index="week", columns=KEYS, values="log_p").reindex(index=weeks, columns=W.columns).ffill(limit=8)
    F = {"ws_dp_1": Wf.diff(), "ws_dp_4": Wf - Wf.shift(4), "ws_dp_8": Wf - Wf.shift(8)}
    F["ws_nat_dp_4"] = by_comm_mean(F["ws_dp_4"])
    F["ws_gap"] = Wf - Rf
    F["ws_gap_dev52"] = F["ws_gap"] - F["ws_gap"].rolling(52, min_periods=26).mean()
    F["ws_rel_4"] = F["ws_dp_4"] - (Rf - Rf.shift(4))
    long = pd.concat({n: f.stack(KEYS, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + KEYS
    out = base.merge(long.reset_index(), on=["week"] + KEYS, how="left")
    assert out[["week"] + KEYS].equals(base[["week"] + KEYS])
    out.to_parquet(os.path.join(EXP, "ws.parquet"))
    d = out[(out["week"] >= "2018-07-01")]
    print(pd.DataFrame({"na_share": d[FEATS].isna().mean(), "mean": d[FEATS].mean(), "sd": d[FEATS].std()}).round(4).to_string())

    # uji kebocoran fitur grosir: rusak grosir & eceran sesudah origin → fitur ≤ origin identik
    rng = np.random.default_rng(5)
    for o in (pd.Timestamp("2022-06-20"), pd.Timestamp("2025-03-24")):
        W2, R2 = Wf.copy(), Rf.copy()
        W2[W2.index > o] += rng.normal(0, 0.5, W2[W2.index > o].shape)
        R2[R2.index > o] += rng.normal(0, 0.5, R2[R2.index > o].shape)
        G = {"ws_dp_4": W2 - W2.shift(4), "ws_gap": W2 - R2}
        G["ws_gap_dev52"] = G["ws_gap"] - G["ws_gap"].rolling(52, min_periods=26).mean()
        same = all(np.allclose(np.nan_to_num(G[k][G[k].index <= o].to_numpy(), nan=-9), np.nan_to_num(F[k][F[k].index <= o].to_numpy(), nan=-9))
                   for k in G)
        print("kebocoran", o.date(), "fitur ≤ origin identik:", same)
