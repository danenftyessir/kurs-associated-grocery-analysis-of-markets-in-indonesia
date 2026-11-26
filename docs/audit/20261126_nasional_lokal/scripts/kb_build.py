"""D-158 Ide A: fitur breadth pasar tingkat kota dari PIHPS 110 kota (PROTOKOL_I1 §2) + lapisan nasional dengan breadth (NL_BR).

Mode: `python kb_build.py` → EXP/br.parquet (= nl.parquet + kb_*, kp_*, nat_hat_br_h*) + hasil/kb_summary.json
      `python kb_build.py leak` → hasil/kb_leak.csv (perturbasi & penghapusan harga kota sesudah minggu origin, 6 origin)
"""
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import EXP, H, cfg, np, pd, table  # noqa: E402
from kagami.data.loaders import norm_name  # noqa: E402
import nl_build as NB  # noqa: E402

ZIP = os.path.join(cfg.raw_dir, "bi_pihps", "pihps_kota_harian_2017-2026_retrieved_2026-11-26.zip")
KB = ["kb_up_1", "kb_up_4", "kb_down_4", "kb_accel", "kb_med_4", "kb_p90_4", "kb_disp_4", "kb_persist", "kb_cov"]
KP = ["kp_up_4", "kp_disp_4", "kp_n", "kp_rel_up_4"]


def read_city_daily():
    """zip kota → long: date, province_id, regency_id, commodity, price (varian representatif saja, harga > 0)."""
    want = {norm_name(v["variant"]).lower(): c for c, v in cfg.commodities.items()}
    out = []
    with zipfile.ZipFile(ZIP) as z:
        for n in z.namelist():
            if not n.startswith("pihps_kota"):
                continue
            d = pd.read_csv(io.BytesIO(z.read(n)))
            d = d[d["level"] == 2]
            d["commodity"] = d["commodity"].map(lambda s: want.get(norm_name(str(s)).lower()))
            d = d.dropna(subset=["commodity"])
            long = d.melt(id_vars=["province_id", "regency_id", "commodity"], value_vars=[c for c in d.columns if c[:2] in ("20",)],
                          var_name="date", value_name="price").dropna(subset=["price"])
            out.append(long[long["price"] > 0])
    r = pd.concat(out, ignore_index=True)
    r["date"] = pd.to_datetime(r["date"])
    return r


def city_features(daily, weeks):
    """long harian → DataFrame (commodity, week) KB + DataFrame (province_id, commodity, week) KP."""
    daily = daily.copy()
    daily["week"] = daily["date"] - pd.to_timedelta(daily["date"].dt.dayofweek, unit="D")
    wk = daily.groupby(["commodity", "regency_id", "province_id", "week"])["price"].mean().reset_index()
    kb_rows, kp_rows = [], []
    for c, g in wk.groupby("commodity"):
        L = np.log(g.pivot(index="week", columns="regency_id", values="price").reindex(weeks))
        prov = g.drop_duplicates("regency_id").set_index("regency_id")["province_id"].reindex(L.columns)
        d1, d4 = L - L.shift(1), L - L.shift(4)
        v1, v4 = d1.notna().sum(1), d4.notna().sum(1)
        kb = pd.DataFrame(index=weeks)
        kb["kb_up_1"] = (d1 > 0).sum(1) / v1.where(v1 > 0)
        kb["kb_up_4"] = (d4 > 0).sum(1) / v4.where(v4 > 0)
        kb["kb_down_4"] = (d4 < 0).sum(1) / v4.where(v4 > 0)
        kb["kb_accel"] = kb["kb_up_4"] - kb["kb_up_4"].shift(4)
        kb["kb_med_4"] = d4.median(1)
        kb["kb_p90_4"] = d4.quantile(0.9, axis=1)
        kb["kb_disp_4"] = d4.quantile(0.75, axis=1) - d4.quantile(0.25, axis=1)
        both = d1.notna() & d1.shift(1).notna()
        kb["kb_persist"] = ((d1 > 0) & (d1.shift(1) > 0)).sum(1) / both.sum(1).where(both.sum(1) > 0)
        seen = L.notna().cummax().sum(1)                                   # kota yang sudah pernah melapor s.d. minggu t
        kb["kb_cov"] = v4 / seen.where(seen > 0)                          # (perbaikan kebocoran 2026-11-26: penyebut dulu = semua kota sepanjang periode)
        kb_rows.append(kb.assign(commodity=c).rename_axis("week").reset_index())
        for p, cols in prov.groupby(prov).groups.items():
            dd = d4[list(cols)]
            n = dd.notna().sum(1)
            kp = pd.DataFrame({"week": weeks, "province_id": int(p), "commodity": c,
                               "kp_up_4": ((dd > 0).sum(1) / n.where(n > 0)).to_numpy(),
                               "kp_disp_4": dd.std(1).where(n >= 2).to_numpy(), "kp_n": n.where(n > 0).to_numpy()})   # 0 → NaN (perbaikan kebocoran)
            kp_rows.append(kp)
    KBf = pd.concat(kb_rows, ignore_index=True)
    KPf = pd.concat(kp_rows, ignore_index=True)
    KPf = KPf.merge(KBf[["commodity", "week", "kb_up_4"]], on=["commodity", "week"], how="left")
    KPf["kp_rel_up_4"] = KPf["kp_up_4"] - KPf["kb_up_4"]
    return KBf, KPf.drop(columns=["kb_up_4"])


def attach(base_keys, KBf, KPf):
    m = base_keys.merge(KBf, on=["commodity", "week"], how="left").merge(KPf, on=["province_id", "commodity", "week"], how="left")
    m.index = base_keys.index
    return m[KB + KP]


if __name__ == "__main__":
    import time
    t0 = time.time()
    nl = table("nl")
    keys = nl[["week", "province_id", "commodity"]]
    weeks = pd.DatetimeIndex(sorted(nl["week"].unique()))
    daily = read_city_daily()
    if len(sys.argv) > 1 and sys.argv[1] == "leak":
        from kagami.features.forecast import origins
        KB0, KP0 = city_features(daily, weeks)
        ref = attach(keys, KB0, KP0)
        os_ = origins(cfg, nl["week"].drop_duplicates(), 4)
        rng = np.random.default_rng(1581)
        rows = []
        for o in [os_[i] for i in np.linspace(0, len(os_) - 1, 6).astype(int)]:
            cut = o + pd.Timedelta(days=6)                         # data minggu origin (Sen–Jum) boleh dipakai
            d1 = daily.copy()
            fut = d1["date"] > cut
            d1.loc[fut, "price"] = rng.uniform(1000, 100000, fut.sum())
            f1 = attach(keys, *city_features(d1, weeks))
            f2 = attach(keys, *city_features(daily[~fut], weeks))
            keep = (keys["week"] <= o).to_numpy()
            for c in ref.columns:
                a = ref.loc[keep, c].to_numpy(float)
                for tag, f in (("T1", f1), ("T2", f2)):
                    b = f.loc[keep, c].to_numpy(float)
                    rows.append({"origin": o.date(), "column": c, "test": tag,
                                 "diff": int((~(np.isclose(a, b, atol=1e-10) | (np.isnan(a) & np.isnan(b)))).sum())})
            print(o.date(), flush=True)
        r = pd.DataFrame(rows)
        r.to_csv(os.path.join(HERE, "..", "hasil", "kb_leak.csv"), index=False)
        print("total sel berbeda:", int(r["diff"].sum()))
        raise SystemExit(0)
    KBf, KPf = city_features(daily, weeks)
    KBf.to_parquet(os.path.join(EXP, "kb_national.parquet"))                 # dipakai meta_build (iterasi 2)
    br = pd.concat([nl, attach(keys, KBf, KPf)], axis=1)
    for h in H:                                                    # NL_BR: lapisan nasional + breadth kota
        nt = NB.national_table(table(), h).merge(KBf, on=["commodity", "week"], how="left")
        nt[f"nat_hat_br_h{h}"] = NB.walk_forward(nt, h)
        nt.to_parquet(os.path.join(EXP, f"natbr_h{h}.parquet"))
        br = br.merge(nt[["commodity", "week", f"nat_hat_br_h{h}"]], on=["commodity", "week"], how="left")
    assert br[["week", "province_id", "commodity"]].equals(keys.reset_index(drop=True))
    br.to_parquet(os.path.join(EXP, "br.parquet"))
    cov = daily.groupby("commodity").agg(n_city=("regency_id", "nunique"), first=("date", "min"), last=("date", "max"))
    dev = br[br["week"] <= pd.Timestamp("2023-12-31")]
    summ = {"daily_rows": len(daily), "coverage": cov.astype(str).to_dict("index"),
            "kb_nan_dev": dev[KB].isna().mean().round(3).to_dict(), "kp_nan_dev": dev[KP].isna().mean().round(3).to_dict(),
            "kp_n_dev_mean": float(dev["kp_n"].mean())}
    json.dump(summ, open(os.path.join(HERE, "..", "hasil", "kb_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1), "\n", round(time.time() - t0), "dtk")
