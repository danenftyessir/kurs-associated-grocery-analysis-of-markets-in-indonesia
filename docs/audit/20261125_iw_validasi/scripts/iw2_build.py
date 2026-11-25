"""D-152: fitur diagnostik intraminggu (LOO, keserentakan, tanpa Jumat) + audit kebocoran SEMUA origin (PROTOKOL.md §1).

Fitur D-151 (`build_iw`, dibekukan) dipakai apa adanya; tambahan:
- iw_gap_nat_loo, iw_return_nat_loo: rerata provinsi LAIN yang teramati minggu t (baris dengan observasi sendiri, seperti D-151).
- iw_up_share_loo, iw_down_share_loo: porsi provinsi lain dengan iw_return > 0 / < 0.
- nf_*: 8 kolom IW_NAT dari Senin–Kamis saja (available_at = t + 4 hari); nf_iw_last_age = 3 − hari terakhir.
Keluaran: EXP/iw2.parquet (= iw.parquet D-151 + kolom), hasil/leak_audit.csv, hasil/leak_summary.json.

Audit per cutoff c = available_at(origin) (Sabtu 00:00; nf: Jumat 00:00), jendela data [origin − 13 mgg, origin + 26 mgg] (kebocoran =
ketergantungan pada data sesudah c; memotong masa lalu identik di kedua sisi tidak menyembunyikannya; 2 origin juga diuji data penuh):
(a) hapus semua sesudah c, (b) rusak harga sesudah c, (c) hapus 30% acak sesudah c, (d) rusak hanya provinsi lain (fitur provinsi p),
(e) rusak Jumat minggu origin → nf_* minggu ≤ origin identik. Kontrol positif: (e) juga harus MENGUBAH iw_* non-nf minggu origin.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_pilot_produsen_intraminggu", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from iw_build import FEATS as D151_FEATS, build_iw  # noqa: E402
from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.features.forecast import origins  # noqa: E402
from kagami.utils.io import read_artifact  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
os.makedirs(OUT, exist_ok=True)
KEYS = ["province_id", "commodity", "week"]
NEW = ["iw_gap_nat_loo", "iw_return_nat_loo", "iw_up_share_loo", "iw_down_share_loo"]
NF = ["nf_" + c for c in D151_FEATS]
ALL = D151_FEATS + NEW + NF
NAT_LIKE = ["iw_gap_nat", "iw_return_nat"] + NEW + ["nf_iw_gap_nat", "nf_iw_return_nat"]
WEEK = pd.Timedelta(weeks=1)


def build_all(daily):
    F = build_iw(daily)
    g = F.groupby(["commodity", "week"])
    for src, dst in (("iw_gap", "iw_gap_nat_loo"), ("iw_return", "iw_return_nat_loo")):
        s, n = g[src].transform("sum"), g[src].transform("count")
        own = F[src].notna()
        F[dst] = ((s - F[src].fillna(0)) / (n - own.astype(int))).where((n - own.astype(int)) > 0)
    obs = F["iw_return"].notna()
    for sign, dst in ((1, "iw_up_share_loo"), (-1, "iw_down_share_loo")):
        ind = (np.sign(F["iw_return"]) == sign).astype(float).where(obs)
        s, n = ind.groupby([F["commodity"], F["week"]]).transform("sum"), obs.groupby([F["commodity"], F["week"]]).transform("sum")
        own = ind.fillna(0)
        F[dst] = ((s - own) / (n - obs.astype(int))).where((n - obs.astype(int)) > 0)
    nf = build_iw(daily[daily["date"].dt.dayofweek <= 3])
    nf["iw_last_age"] = nf["iw_last_age"] - 1.0
    nf = nf.rename(columns={c: "nf_" + c for c in D151_FEATS})
    return F.merge(nf, on=KEYS, how="outer")


def same(a, b, cols, upto, prov=None):
    a, b = a[a["week"] <= upto], b[b["week"] <= upto]
    if prov is not None:
        a, b = a[a["province_id"] == prov], b[b["province_id"] == prov]
    m = a.merge(b, on=KEYS, how="outer", suffixes=("_a", "_b"), indicator=True)
    if (m["_merge"] != "both").any():
        return False, int((m["_merge"] != "both").sum())
    bad = 0
    for c in cols:
        x, y = m[c + "_a"].to_numpy(float), m[c + "_b"].to_numpy(float)
        bad += int((~(np.isclose(x, y, rtol=0, atol=1e-12) | (np.isnan(x) & np.isnan(y)))).sum())
    return bad == 0, bad


def audit(daily, o, rng, full=False):
    cut, cut_nf = o + pd.Timedelta(days=5), o + pd.Timedelta(days=4)
    d = daily if full else daily[(daily["date"] >= o - 13 * WEEK) & (daily["date"] < o + 26 * WEEK)]
    ref = build_all(d)
    res = {"origin": o.date().isoformat(), "full": full, "n_rows_window": len(d)}
    fut = d["date"] >= cut
    res["n_future_rows"] = int(fut.sum())
    if fut.any():
        ok, bad = same(ref, build_all(d[~fut]), ALL, o)
        res["a_delete_ok"], res["a_bad"] = ok, bad
        d2 = d.copy()
        d2.loc[fut, "price"] = d2.loc[fut, "price"] * np.exp(rng.normal(0, 0.5, fut.sum()))
        ok, bad = same(ref, build_all(d2), ALL, o)
        res["b_perturb_ok"], res["b_bad"] = ok, bad
        drop = fut & (rng.random(len(d)) < 0.3)
        ok, bad = same(ref, build_all(d[~drop]), ALL, o)
        res["c_missing_ok"], res["c_bad"] = ok, bad
        p = int(rng.choice(d["province_id"].unique()))
        oth = fut & (d["province_id"] != p)
        d4 = d.copy()
        d4.loc[oth, "price"] = d4.loc[oth, "price"] * np.exp(rng.normal(0, 0.5, oth.sum()))
        ok, bad = same(ref, build_all(d4), NAT_LIKE, o, prov=p)
        res["d_other_prov_ok"], res["d_bad"], res["d_province"] = ok, bad, p
    fri = d["date"] == o + pd.Timedelta(days=4)
    res["n_friday_rows"] = int(fri.sum())
    if fri.any():
        d5 = d.copy()
        d5.loc[fri, "price"] = d5.loc[fri, "price"] * np.exp(rng.normal(0, 0.5, fri.sum()))
        r5 = build_all(d5)
        ok, bad = same(ref, r5, NF, o)
        res["e_nofri_ok"], res["e_bad"] = ok, bad
        ok_ctrl, bad_ctrl = same(ref, r5, ["iw_gap", "iw_gap_nat"], o)
        res["e_control_detects"] = (not ok_ctrl) and bad_ctrl > 0
    assert (d["date"] - d["date"].dt.dayofweek * pd.Timedelta(days=1) + pd.Timedelta(days=5) >= d["date"] + pd.Timedelta(days=1)).all()
    return res


if __name__ == "__main__":
    t0 = time.time()
    daily = read_artifact(cfg, "pihps_daily")
    F = build_all(daily)
    iw = pd.read_parquet(os.path.join(EXP, "iw.parquet"))
    out = iw.merge(F[KEYS + NEW + NF], on=KEYS, how="left")
    assert out[KEYS].equals(iw[KEYS])
    chk = iw[KEYS + D151_FEATS].merge(F[KEYS + D151_FEATS], on=KEYS, how="left", suffixes=("", "_new"))
    for c in D151_FEATS:   # fitur D-151 tidak berubah
        if c == "iw_n_days":
            continue
        assert np.allclose(chk[c].to_numpy(float), chk[c + "_new"].to_numpy(float), equal_nan=True), c
    out.to_parquet(os.path.join(EXP, "iw2.parquet"))
    d = out[out["week"] >= "2018-07-01"]
    desc = pd.DataFrame({"na_share": d[NEW + NF].isna().mean(), "mean": d[NEW + NF].mean(), "sd": d[NEW + NF].std()})
    desc["corr_with_d151"] = [np.nan] * 4 + [d[[c, c[3:]]].corr().iloc[0, 1] for c in NF]
    desc.round(4).to_csv(os.path.join(OUT, "iw2_features.csv"))
    print(desc.round(4).to_string())
    print("loo vs nat corr:", round(d[["iw_gap_nat", "iw_gap_nat_loo"]].corr().iloc[0, 1], 4),
          round(d[["iw_return_nat", "iw_return_nat_loo"]].corr().iloc[0, 1], 4), f"{time.time() - t0:.0f} dtk", flush=True)

    weeks = iw["week"].drop_duplicates().sort_values()
    grid = sorted(set(origins(cfg, weeks, 4)) | set(origins(cfg, weeks, 8)))
    last = weeks.max()
    fwd = [last - k * WEEK for k in range(8)]
    all_o = sorted(set(grid) | set(fwd))
    rng = np.random.default_rng(152)
    rows = [audit(daily, pd.Timestamp(o), rng) for o in all_o]
    rows += [audit(daily, pd.Timestamp(o), rng, full=True) for o in (pd.Timestamp("2022-06-20"), pd.Timestamp("2025-03-24"))]
    A = pd.DataFrame(rows)
    A.to_csv(os.path.join(OUT, "leak_audit.csv"), index=False)
    okcols = [c for c in A.columns if c.endswith("_ok")]
    summ = {"n_origins": int(len(all_o)), "n_grid": len(grid), "n_forward": len(fwd), "full_data_checks": 2,
            **{c: {"tested": int(A[c].notna().sum()), "passed": int((A[c] == True).sum())} for c in okcols},  # noqa: E712
            "e_control_detects": {"tested": int(A["e_control_detects"].notna().sum()), "passed": int((A["e_control_detects"] == True).sum())},  # noqa: E712
            "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "leak_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summ, fh, indent=1)
    print(json.dumps(summ, indent=1))
    fails = A[(A[okcols] == False).any(axis=1)]  # noqa: E712
    assert fails.empty, fails
