"""Fitur dinamika harga per seri untuk klasifier arah EKSPLORATIF (D-145; bukan bagian praregistrasi).

Ditambahkan ke `features.forecast.feature_table`. Setiap fitur minggu t hanya memakai log harga (dan status sel) s.d. minggu t:
selisih/rolling ke belakang, rerata lintas provinsi pada minggu yang sama, dan perubahan h minggu yang sama 1 & 2 tahun lalu
(p_{t-52+h} − p_{t-52}, sudah terealisasi pada t). Kelompok dipilih lewat ablation pada origin pengembangan (target ≤ 2023),
laporan `docs/audit/20261124_task4_optimasi_arah.md`; `vol` dan `cf` dihitung tetapi tidak dipakai (SELECTED_GROUPS).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

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
SELECTED_GROUPS = ("lag", "rmean", "rstd", "mom", "season", "dev", "comm")   # hasil ablation D-145
SEASONAL = ("yseas_52", "yseas_104")                                         # bergantung horizon → akhiran _h{h}
FFILL_WEEKS = 8                                                              # celah harga terpanjang yang diisi (= max_gap_weeks)


def _run_length(flag: pd.DataFrame) -> pd.DataFrame:
    """Panjang deret True berturut-turut yang berakhir di setiap minggu (per kolom/seri)."""
    f = flag.fillna(False).astype(int)
    return f.apply(lambda c: c.groupby((c == 0).cumsum()).cumsum())


def _by_commodity(df: pd.DataFrame, how: str) -> pd.DataFrame:
    """Statistik lintas seri komoditas yang sama pada minggu yang sama, disebar kembali ke setiap seri."""
    return df.T.groupby(df.columns.get_level_values("commodity")).transform(how).T


def extend_table(table: pd.DataFrame, panel: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    """D-145. `feature_table` + semua kolom GROUPS (musiman per horizon: `yseas_52_h{h}`, `yseas_104_h{h}`).

    Input : `feature_table` (week, kunci seri, commodity, log_p, ...) dan panel (status sel untuk `status_cf_run`; panel
            wilayah tanpa status → kolom itu 0). Output: tabel yang sama dengan kolom fitur tambahan (baris & urutan tetap).
    """
    keys = ["province_id" if "province_id" in table else "region", "commodity"]
    wide = table.pivot(index="week", columns=keys, values="log_p").sort_index()
    pf = wide.ffill(limit=FFILL_WEEKS)
    d1 = pf.diff()
    F: dict[str, pd.DataFrame] = {"dp1_l1": d1.shift(1), "dp1_l2": d1.shift(2), "dp1_l3": d1.shift(3)}
    for k in (13, 26, 52):
        F[f"lag_dp_{k}"] = wide - wide.shift(k)
    F["ewm_dp_4"] = d1.ewm(halflife=4, min_periods=4).mean()
    F["ewm_dp_13"] = d1.ewm(halflife=13, min_periods=8).mean()
    for k in (4, 13, 26, 52):
        F[f"std_dp_{k}"] = d1.rolling(k, min_periods=max(3, k // 2)).std()
    up = (d1 > 0).astype(float).where(d1.notna())
    dn = (d1 < 0).astype(float).where(d1.notna())
    F["up_share_13"] = up.rolling(13, min_periods=6).mean()
    F["dn_share_13"] = dn.rolling(13, min_periods=6).mean()
    F["accel_4"] = (pf - pf.shift(4)) - (pf.shift(4) - pf.shift(8))
    sgn = np.sign(d1)
    last = sgn.replace(0, np.nan).ffill()                          # tanda perubahan terakhir yang bukan nol
    F["run_sign"] = last * _run_length(sgn.eq(last) & sgn.ne(0)).where(d1.notna())
    F["absmean_dp_13"] = d1.abs().rolling(13, min_periods=6).mean()
    F["maxabs_dp_13"] = d1.abs().rolling(13, min_periods=6).max()
    woy = wide.index.isocalendar().week.astype(float).to_numpy()
    for name, fn in (("woy_sin", np.sin), ("woy_cos", np.cos)):
        F[name] = pd.DataFrame(np.repeat(fn(2 * np.pi * woy / 52.18)[:, None], wide.shape[1], 1), wide.index, wide.columns)
    F["dev_ma13"] = pf - pf.rolling(13, min_periods=6).mean()
    F["dev_ma52"] = pf - pf.rolling(52, min_periods=26).mean()
    hi, lo = pf.rolling(52, min_periods=26).max(), pf.rolling(52, min_periods=26).min()
    F["range_pos_52"] = ((pf - lo) / (hi - lo)).where(hi > lo, 0.5)
    F["spatial_dev"] = pf - _by_commodity(pf, "mean")
    F["spatial_dev_chg4"] = F["spatial_dev"] - F["spatial_dev"].shift(4)
    F["cf_age"] = _run_length(d1.eq(0))
    F["zero_share_13"] = d1.eq(0).where(d1.notna()).rolling(13, min_periods=6).mean()
    if "status" in panel and keys[0] in panel:
        st = panel.pivot(index="week", columns=keys, values="status").reindex(index=wide.index, columns=wide.columns)
        F["status_cf_run"] = _run_length(st.eq("carry_forward"))
    else:
        F["status_cf_run"] = pd.DataFrame(0, wide.index, wide.columns)
    for k in (1, 4, 8):
        F[f"nat_dp_{k}"] = _by_commodity(pf - pf.shift(k), "mean")
    d4 = pf - pf.shift(4)
    F["nat_up_share_4"] = _by_commodity((d4 > 0).astype(float).where(d4.notna()), "mean")
    F["nat_std_13"] = _by_commodity(F["std_dp_13"], "mean")
    for h in horizons:
        for lag, name in ((52, "yseas_52"), (104, "yseas_104")):
            F[f"{name}_h{h}"] = pf.shift(lag - h) - pf.shift(lag)
    long = pd.concat({n: f.stack(keys, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + keys
    return table.merge(long.reset_index(), on=["week"] + keys, how="left")


def group_columns(groups: tuple[str, ...] | list[str], horizon: int) -> list[str]:
    """Nama kolom kelompok fitur untuk satu horizon (kolom musiman diberi akhiran `_h{horizon}`)."""
    return [f"{c}_h{horizon}" if c in SEASONAL else c for g in groups for c in GROUPS[g]]
