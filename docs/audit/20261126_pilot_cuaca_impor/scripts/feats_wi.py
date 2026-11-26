"""D-157: fitur cuaca sentra produksi (W) dan realisasi impor (I) untuk Task 4 arah. Fungsi murni (dipakai juga uji kebocoran).

Cuaca (`nasa_power`): per titik provinsi, jumlah/hitungan bergulir harian → anomali baku terhadap klimatologi DOY ± 10 hari periode
2016-01-01 .. 2020-12-31 (seluruhnya sebelum origin pertama 2021-01-04). Nilai minggu t = nilai pada **Minggu sebelum minggu t** (cutoff
= Senin t − 1 hari; lag ≥ 7 hari terhadap ketersediaan harga minggu t).
  z_rain_28 / z_rain_56 / z_rain_91 : anomali baku jumlah hujan 28 / 56 / 91 hari
  z_wet_56  : anomali baku jumlah hari hujan ≥ persentil 95 harian baseline titik itu, 56 hari
  z_dry_56  : anomali baku jumlah hari hujan < 1 mm, 56 hari
  z_tmax_28 : anomali baku rerata suhu maksimum 28 hari
W_NAT (6 kolom `wn_*`): Σ_r porsi produksi komoditas c di provinsi r × anomali titik r, untuk cabai merah (ATAP cabai_besar_group),
cabai rawit, bawang merah; komoditas lain NaN. Porsi produksi tahun Y (ATAP `hortikultura_produksi`) dianggap tersedia 1 Juli Y+1;
minggu sebelum 2021-07-01 memakai porsi 2020 (tahun paling awal di repo; look-ahead struktural yang diungkap, lihat `share_stability`).
W_LOC (6 kolom `wl_*`): anomali titik provinsi sendiri, semua komoditas.

Impor (`comtrade_import` 2017-01..2022-12 HS4/HS6 + `bps_import_monthly` 2023-01..2026-09 HS8; prefiks kode dari commodities.yaml):
keranjang beras 1006; bawang putih 070320; gula 1701; daging sapi 0102+0201+0202; daging ayam & telur = pakan 1005+2304; bawang merah
070310; cabai merah & rawit 070960+090421; minyak goreng dikecualikan (jalur paritas ekspor). Bulan tanpa catatan = 0.
available_at(bulan m) = akhir bulan m + `forecast.bps_release_lag_days` (45). Minggu t memakai bulan terakhir dengan available_at ≤
Senin t + 5 hari (Sabtu minggu t). Kolom `im_*`: yoy3 (log Σ3 bulan − log Σ3 bulan sama tahun lalu), mom3 (Σ3 terakhir vs Σ3 sebelumnya),
dev12 (bulan terakhir vs rerata 12 bulan sebelumnya), uv3 (Δ log nilai satuan USD/kg 3 bulan vs 3 bulan sebelumnya).
"""
import numpy as np
import pandas as pd

BASE_END = pd.Timestamp("2020-12-31")
HORTI = {"cabai_merah": "cabai_besar_group", "cabai_rawit": "cabai_rawit", "bawang_merah": "bawang_merah"}
BASKET = {"beras": ["1006"], "bawang_putih": ["070320"], "gula_pasir": ["1701"], "daging_sapi": ["0102", "0201", "0202"],
          "daging_ayam": ["1005", "2304"], "telur_ayam": ["1005", "2304"], "bawang_merah": ["070310"],
          "cabai_merah": ["070960", "090421"], "cabai_rawit": ["070960", "090421"]}
WCOLS = ["z_rain_28", "z_rain_56", "z_rain_91", "z_wet_56", "z_dry_56", "z_tmax_28"]
W_NAT = [f"wn_{c}" for c in WCOLS]
W_LOC = [f"wl_{c}" for c in WCOLS]
IMP = ["im_yoy3", "im_mom3", "im_dev12", "im_uv3"]


def read_power(files):
    """Daftar path CSV NASA POWER → long: date, province_id, P, T2M, TMAX."""
    import io
    import re
    out = []
    for f in files:
        pid = int(re.search(r"p(\d+)\.csv$", str(f)).group(1))
        body = open(f, encoding="utf-8").read().split("-END HEADER-")[1]
        d = pd.read_csv(io.StringIO(body)).replace(-999, np.nan)
        d["date"] = pd.to_datetime(d["YEAR"].astype(str), format="%Y") + pd.to_timedelta(d["DOY"] - 1, unit="D")
        out.append(pd.DataFrame({"date": d["date"], "province_id": pid, "P": d["PRECTOTCORR"], "TMAX": d["T2M_MAX"]}))
    return pd.concat(out, ignore_index=True)


def _zscore(S, base_mask, doy):
    """Anomali baku per kolom terhadap klimatologi DOY ± 10 hari pada baris baseline."""
    V = S.to_numpy(float)
    mu, sd = np.full((367, V.shape[1]), np.nan), np.full((367, V.shape[1]), np.nan)
    bd, bv = doy[base_mask], V[base_mask]
    for k in range(1, 367):
        dist = np.minimum(np.abs(bd - k), 366 - np.abs(bd - k))
        sel = bv[dist <= 10]
        with np.errstate(all="ignore"):
            mu[k], sd[k] = np.nanmean(sel, 0), np.nanstd(sel, 0)
    Z = (V - mu[doy]) / np.where(sd[doy] > 0, sd[doy], np.nan)
    return pd.DataFrame(Z, S.index, S.columns)


def weather_point_features(w):
    """long harian → dict nama → DataFrame (tanggal × provinsi) anomali baku per titik."""
    P = w.pivot(index="date", columns="province_id", values="P").sort_index()
    T = w.pivot(index="date", columns="province_id", values="TMAX").reindex(P.index)
    doy = P.index.dayofyear.to_numpy()
    base = (P.index <= BASE_END)
    p95 = P[base].quantile(0.95)
    F = {"z_rain_28": P.rolling(28, min_periods=28).sum(), "z_rain_56": P.rolling(56, min_periods=56).sum(),
         "z_rain_91": P.rolling(91, min_periods=91).sum(),
         "z_wet_56": P.ge(p95, axis=1).astype(float).where(P.notna()).rolling(56, min_periods=56).sum(),
         "z_dry_56": P.lt(1.0).astype(float).where(P.notna()).rolling(56, min_periods=56).sum(),
         "z_tmax_28": T.rolling(28, min_periods=28).mean()}
    return {k: _zscore(v, base, doy) for k, v in F.items()}


def production_shares(hort):
    """ATAP → porsi produksi per (komoditas ATAP, tahun, province_id)."""
    h = hort.dropna(subset=["province_id"]).groupby(["commodity_atap", "year", "province_id"])["production_ton"].sum().reset_index()
    h["share"] = h["production_ton"] / h.groupby(["commodity_atap", "year"])["production_ton"].transform("sum")
    return h


def share_year(week, years):
    """Tahun ATAP terakhir yang tersedia (1 Juli Y+1 ≤ minggu); bila belum ada → tahun paling awal (diungkap)."""
    ok = [y for y in years if pd.Timestamp(f"{y + 1}-07-01") <= week]
    return max(ok) if ok else min(years)


def weather_features(table, w, hort):
    """table (week, province_id, commodity) → DataFrame wn_* (W_NAT) & wl_* (W_LOC), indeks = table.index."""
    Z = weather_point_features(w)
    weeks = pd.DatetimeIndex(sorted(table["week"].unique()))
    cut = weeks - pd.Timedelta(days=1)
    Zw = {k: v.reindex(cut).set_axis(weeks) for k, v in Z.items()}          # nilai pada Minggu sebelum minggu t
    sh = production_shares(hort)
    years = sorted(sh["year"].unique())
    out = pd.DataFrame(index=table.index)
    # W_LOC
    for k in WCOLS:
        long = Zw[k].stack().rename(k).reset_index().rename(columns={"level_0": "week"})
        long.columns = ["week", "province_id", k]
        m = table[["week", "province_id"]].merge(long, on=["week", "province_id"], how="left")
        out[f"wl_{k}"] = m[k].to_numpy()
    # W_NAT
    nat = []
    for c, atap in HORTI.items():
        for yr in years:
            s = sh[(sh["commodity_atap"] == atap) & (sh["year"] == yr)].set_index("province_id")["share"]
            wk = [t for t in weeks if share_year(t, years) == yr]
            if not wk:
                continue
            row = {"week": wk, "commodity": c}
            for k in WCOLS:
                M = Zw[k].loc[wk, :]
                wv = s.reindex(M.columns).fillna(0.0).to_numpy()
                row[f"wn_{k}"] = (M.to_numpy() * wv).sum(1) / wv.sum()
            nat.append(pd.DataFrame(row))
    nat = pd.concat(nat, ignore_index=True)
    m = table[["week", "commodity"]].merge(nat, on=["week", "commodity"], how="left")
    for k in W_NAT:
        out[k] = m[k].to_numpy()
    return out


def monthly_imports(comtrade, bps):
    """→ month, commodity, kg, usd (keranjang BASKET)."""
    rows = []
    for c, codes in BASKET.items():
        a = comtrade[comtrade["hs_code"].str.startswith(tuple(codes))].groupby("month")[["net_weight_kg", "cif_usd"]].sum()
        b = bps[bps["hs8_code"].str.startswith(tuple(codes))].groupby("month")[["import_netweight_kg", "import_value_usd"]].sum()
        b.columns = ["net_weight_kg", "cif_usd"]
        s = pd.concat([a, b]).groupby(level=0).sum()
        s = s.reindex(pd.date_range("2017-01-01", "2026-09-01", freq="MS"), fill_value=0.0)
        rows.append(pd.DataFrame({"month": s.index, "commodity": c, "kg": s["net_weight_kg"].to_numpy(), "usd": s["cif_usd"].to_numpy()}))
    return pd.concat(rows, ignore_index=True)


def import_features(table, imp, lag_days=45):
    weeks = pd.DatetimeIndex(sorted(table["week"].unique()))
    imp = imp.copy()
    imp["available_at"] = imp["month"] + pd.offsets.MonthEnd(0) + pd.Timedelta(days=lag_days)
    rows = []
    for c, g in imp.groupby("commodity"):
        g = g.sort_values("month").reset_index(drop=True)
        kg, usd, av = g["kg"].to_numpy(), g["usd"].to_numpy(), g["available_at"].to_numpy()
        for t in weeks:
            n = int((av <= (t + pd.Timedelta(days=5)).to_datetime64()).sum())   # bulan tersedia (urut)
            r = {"week": t, "commodity": c}
            if n >= 18:
                k3, p3, y3 = kg[n - 3:n].sum(), kg[n - 6:n - 3].sum(), kg[n - 15:n - 12].sum()
                r["im_yoy3"] = np.log1p(k3) - np.log1p(y3)
                r["im_mom3"] = np.log1p(k3) - np.log1p(p3)
                r["im_dev12"] = np.log1p(kg[n - 1]) - np.log1p(kg[n - 13:n - 1].mean())
                uv = (usd[n - 3:n].sum() / k3) if k3 > 0 else np.nan
                uvp = (usd[n - 6:n - 3].sum() / p3) if p3 > 0 else np.nan
                r["im_uv3"] = np.log(uv) - np.log(uvp) if uv > 0 and uvp > 0 else np.nan
            rows.append(r)
    f = pd.DataFrame(rows)
    m = table[["week", "commodity"]].merge(f, on=["week", "commodity"], how="left")
    out = pd.DataFrame(index=table.index)
    for k in IMP:
        out[k] = m[k].to_numpy() if k in m else np.nan
    return out


def share_stability(hort):
    """Korelasi porsi produksi provinsi 2020 vs tahun lain per komoditas ATAP (pembenaran bobot struktural)."""
    sh = production_shares(hort)
    p = sh.pivot_table(index=["commodity_atap", "province_id"], columns="year", values="share").fillna(0)
    return {c: {int(y): float(np.corrcoef(g[2020], g[y])[0, 1]) for y in g.columns if y != 2020} for c, g in p.groupby(level=0)}
