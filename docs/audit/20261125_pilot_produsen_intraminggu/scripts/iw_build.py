"""D-151 keluarga A: fitur intraminggu dari `pihps_daily` (hari teramati minggu t saja) → EXP/iw.parquet (= base.parquet + kolom).

Fitur (PROTOKOL.md §3): iw_gap, iw_return, iw_range, iw_vol, iw_n_days, iw_last_age; nasional iw_gap_nat, iw_return_nat.
Cek: iw_gap = kolom `iw_gap` D-147 di base.parquet; kebocoran (harga harian sesudah akhir minggu origin dirusak → fitur ≤ origin
identik) pada 2 origin. Keluaran ringkas: hasil/iw_features.csv.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
KEYS = ["province_id", "commodity", "week"]
FEATS = ["iw_gap", "iw_return", "iw_range", "iw_vol", "iw_n_days", "iw_last_age", "iw_gap_nat", "iw_return_nat"]


def build_iw(daily):
    d = daily[["date", "province_id", "commodity", "price"]].copy()
    d["week"] = d["date"] - pd.to_timedelta(d["date"].dt.dayofweek, unit="D")
    d = d.sort_values(["province_id", "commodity", "date"])
    d["lp"] = np.log(d["price"])
    d["dow"] = d["date"].dt.dayofweek
    g = d.groupby(KEYS, sort=False)
    d["dlp"] = g["lp"].diff()                       # Δ log antar hari teramati DALAM minggu yang sama
    g = d.groupby(KEYS, sort=False)
    w = pd.DataFrame({
        "first": g["lp"].first(), "last": g["lp"].last(), "mean_price": g["price"].mean(),
        "mx": g["lp"].max(), "mn": g["lp"].min(), "n": g.size(), "last_dow": g["dow"].last(),
        "vol": g["dlp"].std(ddof=0), "n_chg": g["dlp"].count(),
    })
    f = pd.DataFrame(index=w.index)
    f["iw_gap"] = w["last"] - np.log(w["mean_price"])
    f["iw_return"] = w["last"] - w["first"]
    f["iw_range"] = w["mx"] - w["mn"]
    f["iw_vol"] = w["vol"].where(w["n_chg"] >= 2)
    f["iw_n_days"] = w["n"].astype(float)
    f["iw_last_age"] = (4 - w["last_dow"]).astype(float)
    f = f.reset_index()
    nat = f.groupby(["commodity", "week"])[["iw_gap", "iw_return"]].mean().add_suffix("_nat").reset_index()
    return f.merge(nat, on=["commodity", "week"], how="left")


if __name__ == "__main__":
    base = pd.read_parquet(os.path.join(EXP, "base.parquet"))
    daily = read_artifact(cfg, "pihps_daily")
    F = build_iw(daily)
    out = base.drop(columns=["iw_gap"]).merge(F, on=KEYS, how="left")
    assert out[KEYS].equals(base[KEYS])
    out["iw_n_days"] = out["iw_n_days"].fillna(0.0)
    ok = out["iw_gap"].notna() | base["iw_gap"].notna()
    assert np.allclose(out.loc[ok, "iw_gap"].to_numpy(float), base.loc[ok, "iw_gap"].to_numpy(float), equal_nan=True), "iw_gap ≠ D-147"
    assert (out["iw_n_days"] == base["n_days"]).all(), "n_days ≠ D-147"
    out.to_parquet(os.path.join(EXP, "iw.parquet"))
    d = out[out["week"] >= "2018-07-01"]
    desc = pd.DataFrame({"na_share": d[FEATS].isna().mean(), "mean": d[FEATS].mean(), "sd": d[FEATS].std(),
                         "share_zero": (d[FEATS] == 0).mean()})
    corr = d[FEATS + ["lag_dp_1"]].corr()["lag_dp_1"].rename("corr_lag_dp_1")
    desc = desc.join(corr)
    desc.round(4).to_csv(os.path.join(OUT, "iw_features.csv"))
    pd.set_option("display.width", 200)
    print(desc.round(4).to_string())

    # kebocoran: rusak harga harian sesudah akhir minggu origin → fitur minggu ≤ origin identik
    rng = np.random.default_rng(151)
    for o in (pd.Timestamp("2022-06-20"), pd.Timestamp("2025-03-24")):
        dd = daily.copy()
        fut = dd["date"] > o + pd.Timedelta(days=4)
        dd.loc[fut, "price"] = dd.loc[fut, "price"] * np.exp(rng.normal(0, 0.5, fut.sum()))
        G = build_iw(dd)
        a = F[F["week"] <= o].sort_values(KEYS).reset_index(drop=True)
        b = G[G["week"] <= o].sort_values(KEYS).reset_index(drop=True)
        same = a[KEYS].equals(b[KEYS]) and all(np.allclose(a[c].to_numpy(float), b[c].to_numpy(float), equal_nan=True)
                                               for c in FEATS if c in a)
        print("kebocoran", o.date(), "fitur ≤ origin identik:", same)
        assert same
