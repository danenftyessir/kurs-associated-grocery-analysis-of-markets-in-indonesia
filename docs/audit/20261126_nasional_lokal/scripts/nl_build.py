"""D-158 Ide B: lapisan nasional walk-forward + fitur kepengikutan provinsi → EXP/nl.parquet (base + kolom baru).

Tahap 1 (per komoditas × minggu, per horizon h): target share_up_h = porsi provinsi dengan y_h > 0 di antara y_h ≠ 0. Fitur nasional =
rerata lintas provinsi kolom numerik C1t + breadth provinsi (porsi Δp 1 / 4 minggu > 0) + dispersi Δp 4 minggu + kalender + kode komoditas.
HGB regresi (params tetap NAT_HGB), **walk-forward**: refit tiap 4 minggu r; model r dilatih pada baris nasional t' + h ≤ r dan memprediksi
minggu t ∈ [r, r + 4). Prediksi minggu t → `nat_hat_h{h}` (tersedia pada t, tanpa label masa depan). Minimal 52 minggu latih.
Fitur kepengikutan `follow_h{h}` (lapisan 2, Ide B): porsi minggu t' (t' + h ≤ t, 104 minggu terakhir) dengan tanda y_h provinsi = tanda
rerata nasional y_h (keduanya ≠ 0), per provinsi × komoditas.
Fungsi murni `build(base)` dipakai uji kebocoran (`nl_build.py leak`).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, H, cfg, np, pd, table  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402
from kagami.models.forecasting import _codes  # noqa: E402

NAT_HGB = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0)
STEP, MIN_WEEKS, FOLLOW_WIN = 4, 52, 104
KEY = ["commodity", "week"]


def national_table(base, h):
    num = [c for c in tuned_columns("C1t", h)[0] if c not in ("month", "idf_rel_week", "woy_sin", "woy_cos")]
    g = base.groupby(KEY)
    nat = g[num].mean().add_prefix("m_")
    nat["br_up_1"] = g["lag_dp_1"].apply(lambda s: (s > 0).mean() if s.notna().any() else np.nan)
    nat["br_up_4"] = g["lag_dp_4"].apply(lambda s: (s > 0).mean() if s.notna().any() else np.nan)
    nat["disp_4"] = g["lag_dp_4"].std()
    cal = g[["month", "idf_rel_week", "woy_sin", "woy_cos"]].first()
    y = base[f"y_{h}"]
    nz = base.assign(up=(y > 0).astype(float).where(y.notna() & (y != 0)), yv=y)
    tg = nz.groupby(KEY).agg(share_up=("up", "mean"), n_valid=("up", "count"), y_nat=("yv", "mean"))
    return pd.concat([nat, cal, tg], axis=1).reset_index()


def walk_forward(nt, h):
    from sklearn.ensemble import HistGradientBoostingRegressor
    feats = [c for c in nt.columns if c not in KEY + ["share_up", "n_valid", "y_nat"]]
    X = np.column_stack([nt[feats].to_numpy(float), _codes(cfg, nt, ["commodity"])])
    weeks = np.array(sorted(nt["week"].unique()))
    tr_ok = nt["share_up"].notna().to_numpy() & (nt["n_valid"] >= 10).to_numpy()
    wk = nt["week"].to_numpy()
    out = np.full(len(nt), np.nan)
    for i in range(0, len(weeks), STEP):
        r = weeks[i]
        trm = tr_ok & (wk + np.timedelta64(7 * h, "D") <= r)
        if np.unique(wk[trm]).size < MIN_WEEKS:
            continue
        m = HistGradientBoostingRegressor(**NAT_HGB, categorical_features=[False] * len(feats) + [True], random_state=cfg.seed)
        m.fit(X[trm], nt["share_up"].to_numpy()[trm])
        pm = (wk >= r) & (wk < weeks[min(i + STEP, len(weeks) - 1)] if i + STEP < len(weeks) else wk >= r)
        out[pm] = m.predict(X[pm])
    return np.clip(out, 0, 1)


def follow_rate(base, nt, h):
    y = base[["province_id", "commodity", "week", f"y_{h}"]].rename(columns={f"y_{h}": "y"})
    y = y.merge(nt[["commodity", "week", "y_nat"]], on=KEY, how="left")
    ok = y["y"].notna() & (y["y"] != 0) & y["y_nat"].notna() & (y["y_nat"] != 0)
    y["agree"] = np.where(ok, (np.sign(y["y"]) == np.sign(y["y_nat"])).astype(float), np.nan)
    w = y.pivot(index="week", columns=["province_id", "commodity"], values="agree").sort_index()
    # minggu t memakai pasangan t' dengan t' + h ≤ t → geser h minggu, lalu rerata bergulir 104 minggu
    f = w.shift(h).rolling(FOLLOW_WIN, min_periods=26).mean()
    s = f.stack(["province_id", "commodity"], future_stack=True).rename("f").reset_index()
    return base[["week", "province_id", "commodity"]].merge(s, on=["week", "province_id", "commodity"], how="left")["f"].to_numpy()


def build(base):
    out = pd.DataFrame(index=base.index)
    nats = {}
    for h in H:
        nt = national_table(base, h)
        nt[f"nat_hat_h{h}"] = walk_forward(nt, h)
        nats[h] = nt
        m = base[KEY].merge(nt[KEY + [f"nat_hat_h{h}"]], on=KEY, how="left")
        out[f"nat_hat_h{h}"] = m[f"nat_hat_h{h}"].to_numpy()
        out[f"follow_h{h}"] = follow_rate(base, nt, h)
    return out, nats


if __name__ == "__main__":
    import time
    base = table()
    if len(sys.argv) > 1 and sys.argv[1] == "leak":
        from kagami.features.forecast import origins
        ref, _ = build(base)
        os_ = origins(cfg, base["week"].drop_duplicates(), 8)
        pick = [os_[i] for i in np.linspace(3, len(os_) - 1, 6).astype(int)]
        rng = np.random.default_rng(158)
        rows = []
        num = [c for c in base.columns if base[c].dtype.kind == "f" and c not in ("y_4", "y_8")]
        for o in pick:
            b1 = base.copy()
            fut = (b1["week"] > o).to_numpy()
            b1.loc[fut, num] = rng.normal(0, 1, (fut.sum(), len(num)))
            for h in H:   # label belum terealisasi pada o: t + h > o
                late = (b1["week"] + pd.Timedelta(weeks=h) > o).to_numpy()
                b1.loc[late, f"y_{h}"] = rng.normal(0, 0.1, late.sum())
            f1, _ = build(b1)
            keep = (base["week"] <= o).to_numpy()
            for c in ref.columns:
                a, b = ref.loc[keep, c].to_numpy(float), f1.loc[keep, c].to_numpy(float)
                rows.append({"origin": o.date(), "column": c,
                             "diff": int((~(np.isclose(a, b, atol=1e-9) | (np.isnan(a) & np.isnan(b)))).sum())})
            print(o.date(), "selesai", flush=True)
        r = pd.DataFrame(rows)
        r.to_csv(os.path.join(HERE, "..", "hasil", "nl_leak.csv"), index=False)
        print(r.groupby("column")["diff"].sum().to_string(), "\ntotal sel berbeda:", int(r["diff"].sum()))
        raise SystemExit(0)
    t0 = time.time()
    feat, nats = build(base)
    nl = pd.concat([base, feat], axis=1)
    nl.to_parquet(os.path.join(EXP, "nl.parquet"))
    for h in H:
        nats[h].to_parquet(os.path.join(EXP, f"nat_h{h}.parquet"))
    print(feat.describe().round(3).to_string(), "\n", round(time.time() - t0), "dtk")
