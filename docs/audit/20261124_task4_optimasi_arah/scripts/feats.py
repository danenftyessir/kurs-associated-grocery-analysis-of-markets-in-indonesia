"""Fitur tambahan Task 4 (eksperimen). Semua fitur minggu t hanya memakai log harga s.d. t (shift/rolling ke belakang)."""
import numpy as np
import pandas as pd

KEYS = ["province_id", "commodity"]
GROUPS = {
    "lag": ["dp1_l1", "dp1_l2", "dp1_l3", "lag_dp_13", "lag_dp_26", "lag_dp_52"],
    "rmean": ["ewm_dp_4", "ewm_dp_13"],
    "rstd": ["std_dp_4", "std_dp_13", "std_dp_26"],
    "mom": ["up_share_13", "dn_share_13", "accel_4", "run_sign"],
    "vol": ["std_dp_52", "absmean_dp_13", "maxabs_dp_13"],
    "season": ["woy_sin", "woy_cos", "yseas_52", "yseas_104"],
    "dev": ["dev_ma13", "dev_ma52", "range_pos_52", "spatial_dev", "spatial_dev_chg4"],
    "cf": ["cf_age", "zero_share_13", "status_cf_run"],
    "comm": ["nat_dp_1", "nat_dp_4", "nat_dp_8", "nat_up_share_4", "nat_std_13"],
}


def _run_length(flag: pd.DataFrame) -> pd.DataFrame:
    """Panjang deret True berturut-turut yang berakhir di setiap baris (per kolom)."""
    f = flag.fillna(False).astype(int)
    return f.apply(lambda c: c.groupby((c == 0).cumsum()).cumsum())


def extend(tab: pd.DataFrame, panel: pd.DataFrame, horizons=(4, 8)) -> pd.DataFrame:
    wide = tab.pivot(index="week", columns=KEYS, values="log_p").sort_index()
    pf = wide.ffill(limit=8)
    d1 = pf.diff()
    F = {}
    F["dp1_l1"], F["dp1_l2"], F["dp1_l3"] = d1.shift(1), d1.shift(2), d1.shift(3)
    for k in (13, 26, 52):
        F[f"lag_dp_{k}"] = wide - wide.shift(k)
    F["ewm_dp_4"] = d1.ewm(halflife=4, min_periods=4).mean()
    F["ewm_dp_13"] = d1.ewm(halflife=13, min_periods=8).mean()
    for k in (4, 13, 26, 52):
        F[f"std_dp_{k}"] = d1.rolling(k, min_periods=max(3, k // 2)).std()
    up, dn = (d1 > 0).astype(float).where(d1.notna()), (d1 < 0).astype(float).where(d1.notna())
    F["up_share_13"] = up.rolling(13, min_periods=6).mean()
    F["dn_share_13"] = dn.rolling(13, min_periods=6).mean()
    F["accel_4"] = (pf - pf.shift(4)) - (pf.shift(4) - pf.shift(8))
    sgn = np.sign(d1)
    nz = sgn.replace(0, np.nan).ffill()                       # tanda perubahan terakhir yang bukan nol
    F["run_sign"] = nz * _run_length(sgn.eq(nz) & sgn.ne(0)).where(d1.notna())
    F["absmean_dp_13"] = d1.abs().rolling(13, min_periods=6).mean()
    F["maxabs_dp_13"] = d1.abs().rolling(13, min_periods=6).max()
    woy = wide.index.isocalendar().week.astype(float).to_numpy()
    F["woy_sin"] = pd.DataFrame(np.repeat(np.sin(2 * np.pi * woy / 52.18)[:, None], wide.shape[1], 1), wide.index, wide.columns)
    F["woy_cos"] = pd.DataFrame(np.repeat(np.cos(2 * np.pi * woy / 52.18)[:, None], wide.shape[1], 1), wide.index, wide.columns)
    F["dev_ma13"] = pf - pf.rolling(13, min_periods=6).mean()
    F["dev_ma52"] = pf - pf.rolling(52, min_periods=26).mean()
    mx, mn = pf.rolling(52, min_periods=26).max(), pf.rolling(52, min_periods=26).min()
    F["range_pos_52"] = ((pf - mn) / (mx - mn)).where(mx > mn, 0.5)
    com = wide.columns.get_level_values("commodity")
    cs_mean = pf.T.groupby(com).transform("mean").T               # rerata lintas provinsi per komoditas, minggu t
    F["spatial_dev"] = pf - cs_mean
    F["spatial_dev_chg4"] = F["spatial_dev"] - F["spatial_dev"].shift(4)
    zero = d1.eq(0).where(d1.notna())
    F["cf_age"] = _run_length(d1.eq(0))
    F["zero_share_13"] = zero.rolling(13, min_periods=6).mean()
    st = panel.pivot(index="week", columns=KEYS, values="status").reindex(index=wide.index, columns=wide.columns)
    F["status_cf_run"] = _run_length(st.eq("carry_forward"))
    for k in (1, 4, 8):
        dk = pf - pf.shift(k)
        F[f"nat_dp_{k}"] = dk.T.groupby(com).transform("mean").T
    F["nat_up_share_4"] = ((pf - pf.shift(4)) > 0).astype(float).where((pf - pf.shift(4)).notna()).T.groupby(com).transform("mean").T
    F["nat_std_13"] = F["std_dp_13"].T.groupby(com).transform("mean").T
    F["rel_dp_4"] = (pf - pf.shift(4)) - F["nat_dp_4"]
    long = pd.concat({n: f.stack(KEYS, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + KEYS
    out = tab.merge(long.reset_index(), on=["week"] + KEYS, how="left")
    # musiman per horizon: perubahan h minggu yang sama 1 dan 2 tahun lalu (p_{t-52+h} - p_{t-52}; terealisasi s.d. t)
    for h in horizons:
        for lagw, name in ((52, "yseas_52"), (104, "yseas_104")):
            v = (pf.shift(lagw - h) - pf.shift(lagw)).stack(KEYS, future_stack=True).rename(f"{name}_h{h}")
            v.index.names = ["week"] + KEYS
            out = out.merge(v.reset_index(), on=["week"] + KEYS, how="left")
    return out


def cols_for(groups, h):
    out = []
    for g in groups:
        for c in GROUPS[g]:
            out.append(f"{c}_h{h}" if c.startswith("yseas") else c)
    return out
