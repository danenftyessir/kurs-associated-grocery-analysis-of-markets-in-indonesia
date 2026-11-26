"""Kartu daftar pantau contoh untuk wawancara TPID (U109; PANDUAN_WAWANCARA_TPID.md §3).

Aturan minggu contoh (ditetapkan sebelum melihat hasil): origin evaluasi resmi Task 4 terakhir yang Senin–Jumat-nya seluruhnya di
tahun 2025. Skor = p_up C1-tuned (`direction_tuned_preds`, model C1t). Daftar pantau = 2 skor tertinggi per provinsi (V1-K2, D-154).
"Naik tajam" = y_h ≥ persentil `large_move_pct` |y_h| komoditas pada baris latih (minggu + h ≤ origin, harga minggu t, t−1, t−4, t−8
teramati, sama dengan aturan D-154). Data harga = `panel_weekly` (data turunan; redistribusi diizinkan, D-104).
Keluaran: kartu/kartu_daftar_pantau.html (template.html + data JSON).
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

WEEK = pd.Timedelta(weeks=1)
PCT = cfg.params["forecast"]["large_move_pct"]
OUT = os.path.join(HERE, "kartu_daftar_pantau.html")
HIST_PREC = os.path.join(HERE, "..", "hasil", "bu_s1_watchlist_test.csv")


def r6(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 6)


if __name__ == "__main__":
    preds = read_artifact(cfg, "direction_tuned_preds")
    preds = preds[preds["model"] == "C1t"].copy()
    panel = read_artifact(cfg, "panel_weekly")
    o4 = sorted(preds.loc[preds["horizon"] == 4, "origin"].unique())
    origin = max(o for o in o4 if pd.Timestamp(o).year == 2025 and (pd.Timestamp(o) + pd.Timedelta(days=4)).year == 2025)
    origin = pd.Timestamp(origin)
    assert origin in set(preds.loc[preds["horizon"] == 8, "origin"])
    print("minggu contoh:", origin.date())

    wide = panel.pivot(index="week", columns=["province_id", "commodity"], values="log_price").sort_index()
    price = panel.pivot(index="week", columns=["province_id", "commodity"], values="price").sort_index()
    lag_ok = wide.notna() & wide.shift(1).notna() & wide.shift(4).notna() & wide.shift(8).notna()
    regions = cfg.regions.set_index("province_id")
    hist_prec = pd.read_csv(HIST_PREC).query("view == 'V1_prov_top2' and score == 'model'").set_index("horizon")["precision"]
    t_idx = wide.index.get_loc(origin)
    chg4_all = wide.iloc[t_idx] - wide.iloc[t_idx - 4]
    nat4 = chg4_all.groupby(level="commodity").mean()

    def week_list(o, h):
        """Daftar pantau V1-K2 satu origin: ambang dari baris latih, peringkat p_up per provinsi."""
        y = wide.shift(-h) - wide
        train = (y.index + h * WEEK) <= o
        Y = y[train].where(lag_ok[train])
        thr = {c: np.nanpercentile(np.abs(Y.xs(c, axis=1, level="commodity").to_numpy()), PCT) for c in cfg.commodities}
        p = preds[(preds["origin"] == o) & (preds["horizon"] == h)].copy()
        p = p.sort_values(["province_id", "p_up", "commodity"], ascending=[True, False, True])
        p["rank"] = p.groupby("province_id").cumcount() + 1
        p["thr"] = p["commodity"].map(thr)
        p["sharp"] = p["y_true"] >= p["thr"]
        return p, thr

    horizons, per_h = {}, {}
    for h in (4, 8):
        weekly = []
        for o in sorted(preds.loc[(preds["horizon"] == h) & (preds["origin"] >= "2024-01-01"), "origin"].unique()):
            q, _ = week_list(pd.Timestamp(o), h)
            t2 = q[q["rank"] <= 2]
            weekly.append((pd.Timestamp(o), int(t2["sharp"].sum()), len(t2)))
        W = pd.DataFrame(weekly, columns=["origin", "hits", "n"])
        pooled = W["hits"].sum() / W["n"].sum()
        assert abs(pooled - hist_prec.loc[h]) < 6e-4, (pooled, hist_prec.loc[h])   # sama dengan D-154 (presisi V1-K2 test)
        wp = W["hits"] / W["n"]
        p, thr = week_list(origin, h)
        top = p[p["rank"] <= 2]
        horizons[f"h{h}"] = {"flagged": int(len(top)), "hits": int(top["sharp"].sum()), "provinces": int(p["province_id"].nunique()),
                             "candidates": int(len(p)), "all_hits": int(p["sharp"].sum()), "hist_precision": float(pooled),
                             "weekly_min": float(wp.min()), "weekly_median": float(wp.median()), "weekly_max": float(wp.max()),
                             "weekly_n": int(len(W)), "weekly_higher": int((wp > top["sharp"].mean()).sum()),
                             "thr_pct": {c: r6(np.expm1(v)) for c, v in thr.items()}}
        print(f"h{h}: presisi gabungan 2024+ {pooled:.4f} (D-154 {hist_prec.loc[h]:.4f}); mingguan min {wp.min():.3f} median "
              f"{wp.median():.3f} maks {wp.max():.3f}; minggu contoh {top['sharp'].mean():.3f}, lebih rendah dari "
              f"{int((wp > top['sharp'].mean()).sum())} dari {len(W)} minggu")
        per_h[h] = p
        print(f"h{h}: kandidat {len(p)}, ditandai {len(top)}, naik tajam {int(top['sharp'].sum())} (presisi {top['sharp'].mean():.3f}); "
              f"ambang (%) " + ", ".join(f"{c} {100 * np.expm1(v):.1f}" for c, v in thr.items()))

    provinces = []
    for pid in sorted(per_h[4]["province_id"].unique()):
        entry = {"id": int(pid), "name": str(regions.loc[pid, "province"]), "region": str(regions.loc[pid, "region"])}
        for h in (4, 8):
            rows = []
            for _, r in per_h[h][per_h[h]["province_id"] == pid].iterrows():
                key = (pid, r["commodity"])
                hist = price[key].iloc[t_idx - 12:t_idx + 1].tolist()
                after = price[key].iloc[t_idx + 1:t_idx + 1 + h].tolist()
                lp = wide[key]
                win = price[key].iloc[t_idx - 12:t_idx + 1]
                rows.append({
                    "commodity": r["commodity"], "label": cfg.commodities[r["commodity"]]["pihps_name"],
                    "unit": cfg.commodities[r["commodity"]]["unit"], "rank": int(r["rank"]), "p_up": r6(r["p_up"]),
                    "price": r6(price[key].iloc[t_idx]), "hist": [r6(v) for v in hist], "after": [r6(v) for v in after],
                    "chg4": r6(np.expm1(lp.iloc[t_idx] - lp.iloc[t_idx - 4])), "nat4": r6(np.expm1(nat4[r["commodity"]])),
                    "pos13": r6(price[key].iloc[t_idx] / win.mean() - 1),
                    "out": {"y": r6(np.expm1(r["y_true"])), "thr": r6(np.expm1(r["thr"])), "sharp": bool(r["sharp"])},
                })
            entry[f"h{h}"] = sorted(rows, key=lambda d: d["rank"])
        provinces.append(entry)

    data = {"origin": origin.date().isoformat(), "origin_end": (origin + pd.Timedelta(days=4)).date().isoformat(),
            "generated": date.today().isoformat(), "default_province": "Jawa Tengah", "horizons": horizons, "provinces": provinces}
    with open(os.path.join(HERE, "template.html"), encoding="utf-8") as fh:
        tpl = fh.read()
    assert "/*__DATA__*/null" in tpl
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print("tulis", OUT, f"{len(html) / 1024:.0f} KB; provinsi {len(provinces)}; contoh:", provinces[0]["name"], provinces[0]["h4"][0]["label"])
