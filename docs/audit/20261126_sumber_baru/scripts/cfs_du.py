"""D-160B gerbang 5: prakiraan operasional NOAA CFSv2 (hujan & suhu maks 1–56 hari) untuk hortikultura, origin dev.

Protokol dibekukan SEBELUM hasil ekstraksi Colab dilihat (2026-11-26).

Input  : hasil/cfsv2_province_weekly.csv (notebook colab/kagami_d160_cfsv2.ipynb): per minggu t (Senin) run 00Z Jumat t (cadangan
         Kamis, Rabu) → per provinsi r_1_28, r_29_56, r_1_56 (jumlah hujan mm), rmax_1_28 (hujan harian maks), tx_1_28, tx_29_56 (rerata
         suhu maks °C). Run Jumat 00Z terbit ± 6–8 jam kemudian, sebelum available_at harga minggu t (Minggu 00.00 WIB = Sabtu 17Z, D-155).
Anomali: hujan log1p; per provinsi z = (x − μ)/σ terhadap klimatologi PRAKIRAAN dari run init ≤ 2020-12-31 dengan jarak hari-dalam-tahun
         init ≤ 14 hari (seluruhnya sebelum origin pertama 2021-01-04).
Fitur  : nasional tertimbang produksi `cn_*` = Σ_r porsi ATAP × z_r (aturan D-157: porsi tahun Y tersedia 1 Juli Y+1, sebelum itu porsi
         2020, diungkap) untuk cabai merah, cabai rawit, bawang merah; lokal `cl_*` = z provinsi sendiri.
(a) Skill prakiraan: korelasi z CFSv2 vs z hujan/suhu TERREALISASI NASA POWER pada jendela yang sama (hari 1–28 / 29–56 setelah init).
(b) GERBANG 5 (keputusan): arah nasional increment-only σ(L + γ·x), L = logit konsensus C1t OOS mingguan (D-158), walk-forward refit
    tiap 4 minggu (t' + h ≤ r, ≥ 52 minggu), dinilai minggu 2021-01-04 .. 2023-12-31 − h. Set: R1 [r_1_28], R2 [r_29_56],
    RX [r_1_56, rmax_1_28], T [tx_1_28, tx_29_56], ALL (6). ΔAUC = AUC(inc) − AUC(konsensus), interval & p bootstrap blok minggu
    (13 minggu, 1999 rep), q BH atas 10 uji (5 set × 2 h).
    LOLOS bila satu set yang sama: ΔAUC ≥ +0,01 pada kedua horizon, batas bawah interval > 0 pada ≥ 1 horizon, dan q < 0,05.
(c) ORACLE (bukan kandidat; memakai masa depan): set sama dari cuaca TERREALISASI NASA POWER pada jendela prakiraan → batas atas
    mekanisme "cuaca 1–8 minggu ke depan". Bila oracle tidak lolos ambang yang sama, kegagalan CFSv2 bukan soal skill prakiraan.
Mutu: run dengan < 56 hari lengkap (4 pesan 6-jam) → variabel itu NaN untuk run tsb (jumlah hujan bias rendah); jumlahnya di cfs_leak.json.
(d) Baris provinsi (deskriptif): korelasi residual C1t mentah & parsial (CTRL D-157) dengan cl_* / cn_*.
→ hasil/cfs_features.csv, cfs_skill.csv, cfs_du_national.csv, cfs_du_rows.csv, cfs_leak.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_nasional_lokal", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_pilot_cuaca_impor", "scripts"))
from m_common import AUD, H, bh_fdr, cfg, moving_block_indices, np, official_c1t, pd, table  # noqa: E402
import meta_build as MB  # noqa: E402
import feats_wi as F  # noqa: E402
from kagami.data import loaders as LD  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

OUT = os.environ.get("CFS_OUT", os.path.join(HERE, "..", "hasil"))          # override hanya untuk uji kode sintetis
CSV = os.environ.get("CFS_CSV", os.path.join(HERE, "..", "hasil", "cfsv2_province_weekly.csv"))
BASE_END = pd.Timestamp("2020-12-31")
EVAL_START, DEV_END = pd.Timestamp("2021-01-04"), pd.Timestamp("2023-12-31")
V = ["r_1_28", "r_29_56", "r_1_56", "rmax_1_28", "tx_1_28", "tx_29_56"]
RAIN = {"r_1_28", "r_29_56", "r_1_56", "rmax_1_28"}
SETS = {"R1": ["r_1_28"], "R2": ["r_29_56"], "RX": ["r_1_56", "rmax_1_28"], "T": ["tx_1_28", "tx_29_56"], "ALL": V}
COMMS = list(F.HORTI)
CTRL = ["nat_dp_1", "nat_dp_4", "lag_dp_4", "dev_ma13"]
BLOCK, REPS = 13, 1999


def anomalies(df, value_cols, date_col="init"):
    """Per provinsi: z terhadap klimatologi baris date ≤ BASE_END, jarak DOY ≤ 14 hari (melingkar)."""
    out = df.copy()
    doy = out[date_col].dt.dayofyear.to_numpy()
    for v in value_cols:
        x = out[v].to_numpy(float)
        x = np.log1p(np.clip(x, 0, None)) if v in RAIN else x
        z = np.full(len(out), np.nan)
        for pid, idx in out.groupby("province_id").indices.items():
            base = idx[(out[date_col].to_numpy()[idx] <= np.datetime64(BASE_END))]
            bd, bx = doy[base], x[base]
            for i in idx:
                dist = np.abs(bd - doy[i])
                dist = np.minimum(dist, 366 - dist)
                sel = bx[(dist <= 14) & np.isfinite(bx)]
                if sel.size >= 5 and sel.std() > 0:
                    z[i] = (x[i] - sel.mean()) / sel.std()
        out["z_" + v] = z
    return out


def national(zdf, prefix, hort):
    """Nasional tertimbang produksi ATAP (aturan D-157) → commodity, week, <prefix>_<v>."""
    sh = F.production_shares(hort)
    years = sorted(sh["year"].unique())
    rows = []
    for c, atap in F.HORTI.items():
        for wk, g in zdf.groupby("week"):
            s = sh[(sh["commodity_atap"] == atap) & (sh["year"] == F.share_year(wk, years))].set_index("province_id")["share"]
            w = s.reindex(g["province_id"]).fillna(0.0).to_numpy()
            r = {"commodity": c, "week": wk}
            for v in V:
                z = g["z_" + v].to_numpy(float)
                ok = np.isfinite(z) & (w > 0)
                r[f"{prefix}_{v}"] = float((z[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


def realized(cfs):
    """NASA POWER terealisasi pada jendela prakiraan setiap run (hari 1–28 / 29–56 / 1–56 setelah tanggal init)."""
    w = F.read_power(cfg.source_files("nasa_power"))
    P = w.pivot(index="date", columns="province_id", values="P").sort_index()
    T = w.pivot(index="date", columns="province_id", values="TMAX").reindex(P.index)
    runs = cfs[["week", "init", "province_id"]].copy()
    out = {v: np.full(len(runs), np.nan) for v in V}
    dates = P.index
    for k, (ini, pid) in enumerate(zip(runs["init"], runs["province_id"])):
        a = dates.searchsorted(ini)                       # hari 1 = tanggal init (run 00Z mencakup hari itu)
        if a + 56 > len(dates) or pid not in P.columns:
            continue
        p, t = P[pid].to_numpy(), T[pid].to_numpy()
        seg_p, seg_t = p[a:a + 56], t[a:a + 56]
        if np.isnan(seg_p).any():
            continue
        out["r_1_28"][k], out["r_29_56"][k], out["r_1_56"][k] = seg_p[:28].sum(), seg_p[28:].sum(), seg_p.sum()
        out["rmax_1_28"][k] = seg_p[:28].max()
        out["tx_1_28"][k], out["tx_29_56"][k] = np.nanmean(seg_t[:28]), np.nanmean(seg_t[28:])
    return runs.assign(**out)


def inc_screen(nt, cols, h):
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
    q = q[q["z"].notna() & q["qq"].notna() & (q["week"] >= EVAL_START) & (q["week"] + pd.Timedelta(weeks=h) <= DEV_END)].reset_index(drop=True)
    y, c, p = q["z"].to_numpy(), q["cons"].to_numpy(), q["qq"].to_numpy()
    uw, inv = np.unique(q["week"].to_numpy(), return_inverse=True)
    rows_of = [np.flatnonzero(inv == j) for j in range(len(uw))]
    d = np.full(REPS, np.nan)
    for b in range(REPS):
        idx = np.concatenate([rows_of[j] for j in moving_block_indices(len(uw), BLOCK, np.random.default_rng(20261126 + b))])
        if np.unique(y[idx]).size == 2:
            d[b] = roc_auc_score(y[idx], p[idx]) - roc_auc_score(y[idx], c[idx])
    lo, hi = np.nanpercentile(d, [2.5, 97.5])
    pv = float(min(1.0, 2 * min(np.nanmean(d <= 0), np.nanmean(d >= 0)) + 1 / REPS))
    a_c, a_i = roc_auc_score(y, c), roc_auc_score(y, p)
    return {"n": len(q), "n_weeks": len(uw), "auc_cons": a_c, "auc_inc": a_i, "d_auc": a_i - a_c, "lo": lo, "hi": hi, "p": pv,
            "acc_cons": float(((c > 0.5) == (y > 0.5)).mean()), "acc_inc": float(((p > 0.5) == (y > 0.5)).mean())}


if __name__ == "__main__":
    cfs = pd.read_csv(CSV, parse_dates=["week"])
    cfs = cfs[cfs["init"].notna()].copy()
    cfs["init"] = pd.to_datetime(cfs["init"].str[:10])
    off = (cfs["init"] - cfs["week"]).dt.days
    leak = {"rows": int(len(cfs)), "weeks": int(cfs["week"].nunique()), "init_offset_days": off.value_counts().sort_index().to_dict(),
            "max_offset_ok": bool(off.max() <= 4), "min_offset_ok": bool(off.min() >= 2),
            "base_runs": int(cfs.loc[cfs["init"] <= BASE_END, "week"].nunique()),
            "days_prate_complete_min": int(cfs["days_prate_complete"].min()), "days_tmax_complete_min": int(cfs["days_tmax_complete"].min())}
    assert leak["max_offset_ok"] and leak["min_offset_ok"], leak
    # mutu data (ditetapkan sebelum hasil dilihat): hari tanpa 4 pesan 6-jam membuat jumlah hujan bias rendah → variabel run itu NaN
    bad_p, bad_t = cfs["days_prate_complete"] < 56, cfs["days_tmax_complete"] < 56
    cfs.loc[bad_p, ["r_1_28", "r_29_56", "r_1_56", "rmax_1_28"]] = np.nan
    cfs.loc[bad_t, ["tx_1_28", "tx_29_56"]] = np.nan
    leak.update({"runs_prate_incomplete": int(cfs.loc[bad_p, "week"].nunique()), "runs_tmax_incomplete": int(cfs.loc[bad_t, "week"].nunique())})
    hort = LD.load_hortikultura(cfg)
    Z = anomalies(cfs, V)
    rz = anomalies(realized(cfs), V)
    nat = national(Z, "cn", hort)
    ora = national(rz, "on", hort)
    feats = Z[["week", "init", "province_id"] + ["z_" + v for v in V]]
    feats.round(4).to_csv(os.path.join(OUT, "cfs_features.csv"), index=False)
    # (a) skill
    sk = []
    m = Z.merge(rz[["week", "province_id"] + ["z_" + v for v in V]], on=["week", "province_id"], suffixes=("_f", "_o"))
    for v in V:
        per = m.groupby("province_id").apply(lambda g: g[f"z_{v}_f"].corr(g[f"z_{v}_o"]), include_groups=False)
        nn = nat.merge(ora, on=["commodity", "week"])
        sk.append({"var": v, "prov_corr_median": float(per.median()), "prov_corr_min": float(per.min()), "prov_corr_max": float(per.max()),
                   **{f"nat_corr_{c}": float(g[f"cn_{v}"].corr(g[f"on_{v}"])) for c, g in nn.groupby("commodity")}})
    sk = pd.DataFrame(sk)
    sk.round(3).to_csv(os.path.join(OUT, "cfs_skill.csv"), index=False)
    # (b) + (c) arah nasional
    res = []
    for h in H:
        nt = MB.national(h)
        nt = nt[nt["commodity"].isin(COMMS)].merge(nat, on=["commodity", "week"], how="left").merge(ora, on=["commodity", "week"], how="left")
        nt = nt.reset_index(drop=True)
        for name, cols in SETS.items():
            res.append({"horizon": h, "kind": "CFSv2", "set": name, **inc_screen(nt, [f"cn_{c}" for c in cols], h)})
            res.append({"horizon": h, "kind": "ORACLE", "set": name, **inc_screen(nt, [f"on_{c}" for c in cols], h)})
    n = pd.DataFrame(res)
    n["q_bh"] = np.nan
    for k, g in n.groupby("kind"):
        n.loc[g.index, "q_bh"] = bh_fdr(g["p"].to_numpy())
    piv = n.pivot_table(index=["kind", "set"], columns="horizon", values=["d_auc", "lo", "q_bh"])
    n["gate_pass_set"] = n.apply(lambda r: bool((piv.loc[(r["kind"], r["set"]), ("d_auc", 4)] >= 0.01) & (piv.loc[(r["kind"], r["set"]), ("d_auc", 8)] >= 0.01)
                                                & ((piv.loc[(r["kind"], r["set"]), ("lo", 4)] > 0) | (piv.loc[(r["kind"], r["set"]), ("lo", 8)] > 0))
                                                & ((piv.loc[(r["kind"], r["set"]), ("q_bh", 4)] < 0.05) | (piv.loc[(r["kind"], r["set"]), ("q_bh", 8)] < 0.05))), axis=1)
    n.round(4).to_csv(os.path.join(OUT, "cfs_du_national.csv"), index=False)
    # (d) baris provinsi
    base = table()
    P = official_c1t("dev")
    P = P[(P["y_true"] != 0) & P["commodity"].isin(COMMS)].copy()
    P["r"] = (P["y_true"] > 0).astype(float) - P["score"]
    D = P.merge(base[["week", "province_id", "commodity"] + CTRL].rename(columns={"week": "origin"}), on=["origin", "province_id", "commodity"])
    D = D.merge(Z[["week", "province_id"] + ["z_" + v for v in V]].rename(columns={"week": "origin", **{"z_" + v: "cl_" + v for v in V}}),
                on=["origin", "province_id"], how="left")
    D = D.merge(nat.rename(columns={"week": "origin"}), on=["origin", "commodity"], how="left")
    rows = []
    for h in H:
        d = D[D["horizon"] == h].copy()
        for f in [f"cl_{v}" for v in V] + [f"cn_{v}" for v in V]:
            rows.append({"horizon": h, "feature": f, "kind": "mentah", **screen(d, f, h)})
            g = d.dropna(subset=[f] + CTRL)
            res_ = pd.Series(np.nan, index=d.index)
            for c, gg in g.groupby("commodity"):
                X = np.column_stack([np.ones(len(gg)), gg[CTRL].to_numpy(float)])
                b, *_ = np.linalg.lstsq(X, gg[f].to_numpy(float), rcond=None)
                res_.loc[gg.index] = gg[f].to_numpy(float) - X @ b
            d[f + "__p"] = res_
            rows.append({"horizon": h, "feature": f, "kind": "parsial", **screen(d, f + "__p", h)})
    t = pd.DataFrame(rows)
    t["q_bh"] = np.nan
    for _, g in t.groupby(["horizon", "kind"]):
        ok = g["p"].notna()
        t.loc[g.index[ok], "q_bh"] = bh_fdr(g.loc[ok, "p"].to_numpy())
    t.round(4).to_csv(os.path.join(OUT, "cfs_du_rows.csv"), index=False)
    json.dump(leak, open(os.path.join(OUT, "cfs_leak.json"), "w"), indent=1, default=str)
    pd.set_option("display.width", 220)
    print(json.dumps(leak, default=str))
    print(sk.round(3).to_string(index=False))
    print(n[["horizon", "kind", "set", "n", "auc_cons", "auc_inc", "d_auc", "lo", "hi", "q_bh", "acc_cons", "acc_inc", "gate_pass_set"]].round(4).to_string(index=False))
    print(t.pivot_table(index=["feature", "kind"], columns="horizon", values=["rho", "q_bh"]).round(3).to_string())
