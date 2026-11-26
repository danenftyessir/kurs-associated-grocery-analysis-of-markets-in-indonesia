"""Fase C (D-156): fitur keluarga baru di atas tabel resmi C1-tuned (`base.parquet`). Baris & urutan tetap; target resmi tidak disentuh.

Semua fitur per seri (provinsi × komoditas) dari log harga mingguan s.d. minggu t (rolling ke belakang, ffill ≤ 8 minggu seperti
`price_dynamics`), statistik lintas provinsi minggu yang sama, atau kalender yang diketahui sebelumnya. Satu-satunya input harian:
`n_days` (sudah ada di base, dari `pihps_daily`). Fungsi `build(base)` murni → dipakai juga oleh uji kebocoran (`c_leak.py`).

Keluarga (nama kolom diawali huruf keluarga):
A momentum   : dp_2, dp_12, accel_8, rev_1_4, up_share_26, dn_share_26
B volatilitas: std_dp_52, absmean_dp_13, maxabs_dp_13 (dihitung resmi tetapi tidak dipakai C1t), vol_ratio_4_26, dir_bal_26, chg_freq_26
C posisi     : z_52, dev_med_26, pct_104, dist_max_52, dist_min_52
D1 kualitas  : cf_age, zero_share_13, status_cf_run (resmi, tidak dipakai C1t), n_missing_13, st0_cf
D2 cakupan   : n_days, n_days_l1 (hari teramati minggu t dan t−1; dari pihps_daily)
E lintas prov: rel_dp_1, rel_dp_4 (vs rerata nasional LOO), loo_dev, rank_dp_4, rank_dev
F kalender   : wk_idadha, wk_natal, wk_ramadan (minggu relatif, jendela ±13), seas_nat_exp_h{h}, seas_ser_exp_h{h} (profil musiman
               ekspansif: rerata Δp h minggu yang DIMULAI pada minggu-ISO yang sama (±1) di tahun-tahun sebelumnya, hanya t' + h ≤ t)
G interaksi  : z_dev13, z_dp4, z_spatial, mom_x_vol
"""
import os

import numpy as np
import pandas as pd

FFILL = 8
H = (4, 8)
# Iduladha & awal Ramadan (kalender Kemenag/SKB; diketahui jauh sebelumnya → tidak ada kebocoran)
IDADHA = ["2017-09-01", "2018-08-22", "2019-08-11", "2020-07-31", "2021-07-20", "2022-07-10", "2023-06-29", "2024-06-17",
          "2025-06-06", "2026-05-27"]
RAMADAN = ["2017-05-27", "2018-05-17", "2019-05-06", "2020-04-24", "2021-04-13", "2022-04-03", "2023-03-23", "2024-03-12",
           "2025-03-01", "2026-02-18"]
NATAL = [f"{y}-12-25" for y in range(2016, 2027)]
FAMILIES = {
    "A": ["dp_2", "dp_12", "accel_8", "rev_1_4", "up_share_26", "dn_share_26"],
    "B": ["std_dp_52", "absmean_dp_13", "maxabs_dp_13", "vol_ratio_4_26", "dir_bal_26", "chg_freq_26"],
    "C": ["z_52", "dev_med_26", "pct_104", "dist_max_52", "dist_min_52"],
    "D1": ["cf_age", "zero_share_13", "status_cf_run", "n_missing_13", "st0_cf"],
    "D2": ["n_days", "n_days_l1"],
    "E": ["rel_dp_1", "rel_dp_4", "loo_dev", "rank_dp_4", "rank_dev"],
    "F": ["wk_idadha", "wk_natal", "wk_ramadan", "seas_nat_exp", "seas_ser_exp"],
    "G": ["z_dev13", "z_dp4", "z_spatial", "mom_x_vol"],
}


def fam_cols(fam, h):
    return [f"{c}_h{h}" if c in ("seas_nat_exp", "seas_ser_exp") else c for c in FAMILIES[fam]]


def _wk_rel(weeks, dates, win=13):
    """Minggu relatif terhadap tanggal kalender terdekat (Senin minggu ISO); di luar ±win → NaN."""
    ev = pd.to_datetime(dates)
    ev = (ev - pd.to_timedelta(ev.dayofweek, unit="D")).to_numpy()
    w = weeks.to_numpy()
    d = (w[:, None] - ev[None, :]) / np.timedelta64(7, "D")
    j = np.abs(d).argmin(1)
    r = d[np.arange(len(w)), j]
    return np.where(np.abs(r) <= win, r, np.nan)


def _comm(df, how):
    return df.T.groupby(df.columns.get_level_values("commodity")).transform(how).T


def _loo_mean(df):
    s = _comm(df.fillna(0), "sum")
    n = _comm(df.notna().astype(float), "sum")
    return (s - df.fillna(0)) / (n - df.notna()).where((n - df.notna()) > 0)


def _seasonal_expanding(pf, h, by_commodity):
    """Profil musiman ekspansif: rerata Δp_h yang dimulai minggu t' dengan |woy(t') − woy(t)| ≤ 1, t' + h ≤ t, di tahun sebelumnya."""
    dh = pf.shift(-h) - pf                      # Δp yang DIMULAI di t' (terealisasi di t' + h)
    if by_commodity:
        dh = _comm(dh, "mean")
    woy = pf.index.isocalendar().week.to_numpy()
    idx = pf.index.to_numpy()
    out = np.full(pf.shape, np.nan)
    V = dh.to_numpy()
    for i, t in enumerate(idx):
        ok = (idx + np.timedelta64(7 * h, "D") <= t) & (np.minimum(np.abs(woy - woy[i]), 52 - np.abs(woy - woy[i])) <= 1)
        ok &= idx < t - np.timedelta64(7 * 26, "D")   # hanya tahun-tahun sebelumnya (bukan minggu-minggu dekat t)
        if ok.sum() >= 2:
            with np.errstate(all="ignore"):
                out[i] = np.nanmean(V[ok], axis=0)
    return pd.DataFrame(out, pf.index, pf.columns)


def build(base):
    """base (week, province_id, commodity, log_p, n_days, status kolom st0, ...) → DataFrame kolom fitur baru (indeks = base.index)."""
    keys = ["province_id", "commodity"]
    wide = base.pivot(index="week", columns=keys, values="log_p").sort_index()
    pf = wide.ffill(limit=FFILL)
    d1 = pf.diff()
    F = {}
    # A momentum
    F["dp_2"] = pf - pf.shift(2)
    F["dp_12"] = pf - pf.shift(12)
    F["accel_8"] = (pf - pf.shift(8)) - (pf.shift(8) - pf.shift(16))
    F["rev_1_4"] = np.sign(d1) * np.sign(pf.shift(1) - pf.shift(5))     # tanda minggu ini vs 4 minggu sebelumnya
    up = (d1 > 0).astype(float).where(d1.notna())
    dn = (d1 < 0).astype(float).where(d1.notna())
    F["up_share_26"] = up.rolling(26, min_periods=13).mean()
    F["dn_share_26"] = dn.rolling(26, min_periods=13).mean()
    # B volatilitas
    std4, std13, std26 = (d1.rolling(k, min_periods=max(3, k // 2)).std() for k in (4, 13, 26))
    F["std_dp_52"] = d1.rolling(52, min_periods=26).std()
    F["absmean_dp_13"] = d1.abs().rolling(13, min_periods=6).mean()
    F["maxabs_dp_13"] = d1.abs().rolling(13, min_periods=6).max()
    F["vol_ratio_4_26"] = (std4 / std26).where(std26 > 0)
    F["dir_bal_26"] = F["up_share_26"] - F["dn_share_26"]
    F["chg_freq_26"] = d1.ne(0).where(d1.notna()).astype(float).rolling(26, min_periods=13).mean()
    # C posisi
    m52, s52 = pf.rolling(52, min_periods=26).mean(), pf.rolling(52, min_periods=26).std()
    F["z_52"] = ((pf - m52) / s52).where(s52 > 0)
    F["dev_med_26"] = pf - pf.rolling(26, min_periods=13).median()
    F["pct_104"] = pf.rolling(104, min_periods=52).rank(pct=True)
    F["dist_max_52"] = pf - pf.rolling(52, min_periods=26).max()
    F["dist_min_52"] = pf - pf.rolling(52, min_periods=26).min()
    # D1 kualitas
    def run_len(flag):
        f = flag.fillna(False).astype(int)
        return f.apply(lambda c: c.groupby((c == 0).cumsum()).cumsum())
    F["cf_age"] = run_len(d1.eq(0))
    F["zero_share_13"] = d1.eq(0).where(d1.notna()).astype(float).rolling(13, min_periods=6).mean()
    st = base.pivot(index="week", columns=keys, values="st0").reindex(index=wide.index, columns=wide.columns)
    F["status_cf_run"] = run_len(st.eq("carry_forward"))
    F["n_missing_13"] = wide.isna().astype(float).rolling(13, min_periods=1).sum()
    F["st0_cf"] = st.eq("carry_forward").astype(float)
    # D2 cakupan harian
    nd = base.pivot(index="week", columns=keys, values="n_days").reindex(index=wide.index, columns=wide.columns)
    F["n_days"], F["n_days_l1"] = nd, nd.shift(1)
    # E lintas provinsi
    d4 = pf - pf.shift(4)
    F["rel_dp_1"] = d1 - _loo_mean(d1)
    F["rel_dp_4"] = d4 - _loo_mean(d4)
    F["loo_dev"] = pf - _loo_mean(pf)
    F["rank_dp_4"] = d4.T.groupby(d4.columns.get_level_values("commodity")).rank(pct=True).T
    sdev = pf - _comm(pf, "mean")
    F["rank_dev"] = sdev.T.groupby(sdev.columns.get_level_values("commodity")).rank(pct=True).T
    # F kalender
    for name, dates in (("wk_idadha", IDADHA), ("wk_natal", NATAL), ("wk_ramadan", RAMADAN)):
        F[name] = pd.DataFrame(np.repeat(_wk_rel(pd.Series(wide.index), dates)[:, None], wide.shape[1], 1), wide.index, wide.columns)
    for h in H:
        F[f"seas_nat_exp_h{h}"] = _seasonal_expanding(pf, h, True)
        F[f"seas_ser_exp_h{h}"] = _seasonal_expanding(pf, h, False)
    # G interaksi/normalisasi
    dev13 = pf - pf.rolling(13, min_periods=6).mean()
    F["z_dev13"] = (dev13 / std13).where(std13 > 0)
    F["z_dp4"] = (d4 / std26).where(std26 > 0)
    sd_sp = _comm(sdev, "std")
    F["z_spatial"] = (sdev / sd_sp).where(sd_sp > 0)
    F["mom_x_vol"] = (d1.ewm(halflife=4, min_periods=4).mean() / std13).where(std13 > 0)

    long = pd.concat({n: f.stack(keys, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + keys
    out = base[["week"] + keys].merge(long.reset_index(), on=["week"] + keys, how="left")
    out.index = base.index
    return out.drop(columns=["week"] + keys)


if __name__ == "__main__":
    import time
    from m_common import EXP, table
    t0 = time.time()
    base = table()
    new = build(base)
    dup = [c for c in new.columns if c in base.columns]
    fam = pd.concat([base.drop(columns=dup), new], axis=1)
    for c in dup:            # kolom resmi yang dihitung ulang harus identik dengan versi resmi
        a, b = base[c].to_numpy(float), new[c].to_numpy(float)
        same = np.allclose(np.nan_to_num(a, nan=-9), np.nan_to_num(b, nan=-9), atol=1e-12)
        print(f"cek {c}: identik dengan resmi = {same}")
        assert same, c
    fam.to_parquet(os.path.join(EXP, "fam.parquet"))
    cols = [c for f in FAMILIES for h in H for c in fam_cols(f, h)]
    na = fam[sorted(set(cols))].isna().mean().round(3)
    print(na.to_string())
    print("fam.parquet", fam.shape, round(time.time() - t0), "dtk")
