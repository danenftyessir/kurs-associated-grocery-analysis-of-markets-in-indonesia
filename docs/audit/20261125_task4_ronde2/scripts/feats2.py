"""Fitur ronde 2 (eksperimen D-146): regulasi (selisih HET/HAP), spasial (tetangga & hub), kalender, prior historis,
level relatif. Semua per (minggu, provinsi, komoditas) hanya dari informasi s.d. minggu t."""
import numpy as np
import pandas as pd

KEYS = ["province_id", "commodity"]
GROUPS2 = {
    "reg": ["reg_gap", "reg_active", "reg_weeks_since_change", "reg_change_52"],
    "spat": ["nb_dp_4", "nb_dev", "hub_dev", "reg_dp_4", "region_dev"],
    "cal": ["idf_weeks", "xmas_weeks", "ramadan"],
    "prior": ["hist_up_rate", "hist_zero_rate", "comm_hist_up_rate"],
    "level": ["dev_ma104", "z_52"],
}
HORIZON_SPECIFIC = {"hist_up_rate", "hist_zero_rate", "comm_hist_up_rate"}


def _ref_table(cfg, regions):
    """Harga acuan konsumen per (komoditas, provinsi, tanggal mulai): HET beras medium per zona, HET minyak goreng,
    HAP/HAP_konsumen lain (nilai atas rentang). Tanggal = start_date (berlaku = diketahui)."""
    r = pd.read_csv(cfg.reference_dir / "regulation.csv")
    r = r[r.in_scope & r.instrument.isin(["HET", "HAP", "HAP_konsumen"]) & r.start_date.notna()].copy()
    r["val"] = r.value_rp.fillna(r.value_max_rp)
    r = r[r.val.notna()]
    r["start"] = pd.to_datetime(r.start_date)
    rows = []
    zone_of = regions.set_index("province_id")["het_zone_beras"]
    east = regions.set_index("province_id")["region"].isin(["Maluku", "Papua"])
    for _, x in r.iterrows():
        for pid in regions.province_id:
            z = str(x.zone)
            if x.commodity == "beras":
                # HET medium: nilai terkecil per (zona, tanggal) = medium (premium lebih tinggi)
                if z.startswith("Zona") and z[-1].isdigit() and int(z[-1]) != int(zone_of[pid]):
                    continue
            elif "Timur" in z and not east[pid]:
                continue
            elif "Non-Timur" in z and east[pid]:
                continue
            rows.append({"province_id": pid, "commodity": x.commodity, "start": x.start, "val": x.val})
    t = pd.DataFrame(rows)
    # beras: medium = minimum nilai pada tanggal yang sama; komoditas lain: nilai terbesar pada tanggal yang sama
    t = t.groupby(["province_id", "commodity", "start"]).val.agg(lambda v: v.min()).reset_index()
    return t.sort_values("start")


def extend2(cfg, ext, horizons=(4, 8)):
    regions = cfg.regions
    wide = ext.pivot(index="week", columns=KEYS, values="log_p").sort_index()
    pf = wide.ffill(limit=8)
    weeks = wide.index
    F = {}
    # ---------------- regulasi
    ref = _ref_table(cfg, regions)
    refw = pd.DataFrame(np.nan, index=weeks, columns=wide.columns)
    for (pid, c), g in ref.groupby(["province_id", "commodity"]):
        if (pid, c) not in refw.columns:
            continue
        s = pd.Series(np.log(g.val.values), index=g.start.values)
        s = s[~s.index.duplicated(keep="last")]
        refw[(pid, c)] = s.reindex(weeks.union(s.index)).sort_index().ffill().reindex(weeks).values
    F["reg_gap"] = pf - refw
    F["reg_active"] = refw.notna().astype(float)
    chg = refw.diff().fillna(0).ne(0) & refw.notna()
    last_chg = pd.DataFrame(np.where(chg | (refw.notna() & refw.shift().isna()), np.arange(len(weeks))[:, None], np.nan),
                            index=weeks, columns=wide.columns).ffill()
    F["reg_weeks_since_change"] = (np.arange(len(weeks))[:, None] - last_chg).where(refw.notna())
    F["reg_change_52"] = (refw - refw.shift(52)).where(refw.notna())
    # ---------------- spasial
    reg = regions.set_index("province_id")
    lat, lon = reg.lat.to_dict(), reg.lon.to_dict()
    pids = sorted(reg.index)
    D = np.array([[np.hypot(lat[a] - lat[b], (lon[a] - lon[b]) * np.cos(np.radians((lat[a] + lat[b]) / 2))) for b in pids] for a in pids])
    W = np.where(D > 0, 1 / np.maximum(D, 0.5) ** 2, 0.0)
    hubs = {"DKI JAKARTA": None}
    hub_names = cfg.params["association"]["hubs"]
    name_to_id = {str(n).upper(): i for i, n in reg.province.items()}
    hub_ids = [name_to_id[h.upper()] for h in hub_names]
    nearest_hub = {a: min(hub_ids, key=lambda h: D[pids.index(a), pids.index(h)]) for a in pids}
    d4 = pf - pf.shift(4)
    nb_dp, nb_lv, hub_lv = (pd.DataFrame(np.nan, index=weeks, columns=wide.columns) for _ in range(3))
    for c in wide.columns.get_level_values("commodity").unique():
        cols = [x for x in wide.columns if x[1] == c]
        ids = [x[0] for x in cols]
        Wc = W[np.ix_([pids.index(i) for i in ids], [pids.index(i) for i in ids])]
        for M, out in ((d4[cols], nb_dp), (pf[cols], nb_lv)):
            V = M.to_numpy()
            ok = np.isfinite(V)
            num = np.nan_to_num(V) @ Wc.T
            den = ok.astype(float) @ Wc.T
            out[cols] = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
        for i, col in zip(ids, cols):
            hc = (nearest_hub[i], c)
            hub_lv[col] = pf[hc] if hc in pf.columns and nearest_hub[i] != i else np.nan
    F["nb_dp_4"] = nb_dp
    F["nb_dev"] = pf - nb_lv
    F["hub_dev"] = pf - hub_lv
    rg = pd.Series({x: reg.region[x[0]] for x in wide.columns})
    grp = [rg[x] + "|" + x[1] for x in wide.columns]
    F["reg_dp_4"] = d4.T.groupby(grp).transform("mean").T
    F["region_dev"] = pf - pf.T.groupby(grp).transform("mean").T
    # ---------------- kalender (jarak bertanda ke tanggal tetap/terjadwal — diketahui di muka)
    idf = pd.to_datetime(cfg.params["calendar"]["idulfitri"])
    wk = np.array([(idf - w).days / 7 for w in weeks])                                 # minggu menuju tiap Idulfitri
    nearest = np.array([r[np.argmin(np.abs(r))] for r in wk])
    xmas = np.array([((pd.Timestamp(w.year, 12, 25) - w).days / 7) for w in weeks])
    xmas = np.where(xmas < -26, xmas + 52.18, xmas)
    rep = lambda v: pd.DataFrame(np.repeat(np.asarray(v, float)[:, None], wide.shape[1], 1), weeks, wide.columns)  # noqa: E731
    F["idf_weeks"] = rep(np.clip(nearest, -26, 26))
    F["xmas_weeks"] = rep(np.clip(xmas, -26, 26))
    F["ramadan"] = rep((nearest > 0) & (nearest <= 4.5))
    # ---------------- level
    F["dev_ma104"] = pf - pf.rolling(104, min_periods=52).mean()
    F["z_52"] = (pf - pf.rolling(52, min_periods=26).mean()) / pf.diff().rolling(52, min_periods=26).std()
    # ---------------- prior historis per horizon (hanya perubahan yang sudah terealisasi pada t: t' + h <= t)
    for h in horizons:
        yh = (pf.shift(-h) - pf).shift(h)               # pada baris t: p_t − p_{t−h} (terealisasi)
        up = (yh > 0).astype(float).where(yh.notna())
        zero = (yh == 0).astype(float).where(yh.notna())
        F[f"hist_up_rate_h{h}"] = up.rolling(104, min_periods=26).mean()
        F[f"hist_zero_rate_h{h}"] = zero.rolling(104, min_periods=26).mean()
        F[f"comm_hist_up_rate_h{h}"] = F[f"hist_up_rate_h{h}"].T.groupby(wide.columns.get_level_values("commodity")).transform("mean").T
    long = pd.concat({n: f.stack(KEYS, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + KEYS
    return ext.merge(long.reset_index(), on=["week"] + KEYS, how="left")


def cols2(groups, h):
    return [f"{c}_h{h}" if c in HORIZON_SPECIFIC else c for g in groups for c in GROUPS2[g]]
