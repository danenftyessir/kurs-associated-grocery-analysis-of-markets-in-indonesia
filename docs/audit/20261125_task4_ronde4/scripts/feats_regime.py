"""D-148 tahap 3: fitur sadar-rezim, hanya dari informasi yang tersedia pada minggu t → EXP/regime.parquet (= base + kolom baru).

RB (base rate terealisasi, per horizon): porsi label naik (y ≠ 0) dengan minggu label t' ∈ [t − h − K + 1, t − h] (terealisasi pada t):
    rb_c13_h{h}, rb_c26_h{h} (komoditas, 34 provinsi), rb_s26_h{h} (seri).
WK (keseimbangan arah mingguan): porsi Δp mingguan > 0 di antara Δp ≠ 0, 26 minggu s.d. t: wk_up_s26 (seri), wk_up_c13, wk_up_c26
    (komoditas). Berbeda dari `up_share_13` resmi (yang menghitung minggu tanpa perubahan sebagai bukan-naik).
PO (rezim kebijakan konsumen: HET, HAP, HAP_konsumen; in_scope): setiap kejadian punya known_at (tanggal paling awal di teks
    regulasi: ditetapkan / diundangkan / berlaku) dan effective_at (start_date `regulation.csv`). Fitur pada t:
    pol_age (minggu sejak kejadian terakhir yang DIKETAHUI ≤ t; NaN = belum pernah ada kebijakan), pol_n104 (jumlah kejadian
    diketahui dalam 104 minggu), ref_gap (log p_t − log acuan berlaku ≤ t; NaN = belum ada acuan bernilai), ref_chg_last (log
    perubahan acuan pada perubahan terakhir; 0 = acuan pertama), ref_upcoming (log acuan diumumkan − log acuan berlaku untuk
    kejadian known_at ≤ t < effective_at; 0 bila tidak ada; NaN bila tidak ada acuan).
`regime_id` kategori TIDAK dipakai: rezim baru di test tidak pernah muncul di latih (kategori tak dikenal); umurnya diwakili pol_age.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261125_task4_audit_preprocessing", "scripts"))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from p_exp import EXP  # noqa: E402
from kagami.data.loaders import load_regulation_history  # noqa: E402

KEYS = ["province_id", "commodity"]
CONSUMER = ["HET", "HAP", "HAP_konsumen"]
H = [4, 8]


def _ratio(num, den):
    return (num / den).where(den > 0)


def _by_comm(df):
    return df.T.groupby(df.columns.get_level_values("commodity")).transform("sum").T


def base_rate_features(wide, ywide):
    F = {}
    for h, Y in ywide.items():
        up = (Y > 0).astype(float).where(Y.notna() & (Y != 0), 0.0)
        cnt = (Y.notna() & (Y != 0)).astype(float)
        upc, cntc = _by_comm(up), _by_comm(cnt)
        for k in (13, 26):
            F[f"rb_c{k}_h{h}"] = _ratio(upc.rolling(k, min_periods=1).sum(), cntc.rolling(k, min_periods=1).sum()).shift(h)
        F[f"rb_s26_h{h}"] = _ratio(up.rolling(26, min_periods=8).sum(), cnt.rolling(26, min_periods=8).sum()).shift(h)
    d1 = wide.diff()
    up = (d1 > 0).astype(float)
    cnt = (d1.notna() & (d1 != 0)).astype(float)
    F["wk_up_s26"] = _ratio(up.rolling(26, min_periods=8).sum(), cnt.rolling(26, min_periods=8).sum())
    upc, cntc = _by_comm(up), _by_comm(cnt)
    for k in (13, 26):
        F[f"wk_up_c{k}"] = _ratio(upc.rolling(k, min_periods=4).sum(), cntc.rolling(k, min_periods=4).sum())
    return F


def policy_events():
    """Kejadian kebijakan konsumen per (province_id, commodity): known_at, effective_at, log_val (NaN bila tanpa nilai)."""
    r = pd.read_csv(cfg.reference_dir / "regulation.csv")
    r = r[r["in_scope"] & r["instrument"].isin(CONSUMER) & r["start_date"].notna()].copy()
    hist = load_regulation_history(cfg)
    first_date = {}
    for reg, txt in zip(hist["regulation"], hist["signed_or_effective_date"].astype(str)):
        ds = re.findall(r"\d{4}-\d{2}-\d{2}", txt)
        if ds:
            first_date[str(reg).strip()] = min(pd.Timestamp(d) for d in ds)
    r["effective_at"] = pd.to_datetime(r["start_date"])
    r["known_at"] = [min(first_date.get(str(g).strip(), e), e) for g, e in zip(r["regulation"], r["effective_at"])]
    # beras = varian medium: hanya baris yang menyebut medium; rentang "medium dan premium" → nilai bawah (medium).
    # (ronde 2 mengisi rentang dengan value_max_rp → acuan beras sejak 2024-06-02 = batas atas premium; diperbaiki di sini)
    is_beras = r["commodity"].eq("beras")
    r = r[~is_beras | r["commodity_raw"].str.contains("medium", case=False, na=False)].copy()
    is_beras = r["commodity"].eq("beras")
    r["val"] = np.where(is_beras, r["value_rp"].fillna(r["value_min_rp"]), r["value_rp"].fillna(r["value_max_rp"]))
    reg = cfg.regions.set_index("province_id")
    east = reg["region"].isin(["Maluku", "Papua"])
    rows = []
    for _, x in r.iterrows():
        z = str(x["zone"])
        exact = bool(re.fullmatch(r"Zona \d", z))
        for pid in reg.index:
            if x["commodity"] == "beras" and exact and int(z[-1]) != int(reg.loc[pid, "het_zone_beras"]):
                continue
            if "Non-Timur" in z and east[pid]:
                continue
            if "Timur" in z and "Non-Timur" not in z and not east[pid]:
                continue
            rows.append({"province_id": int(pid), "commodity": x["commodity"], "known_at": x["known_at"],
                         "effective_at": x["effective_at"], "val": x["val"], "exact": exact})
    ev = pd.DataFrame(rows)
    # beras: baris zona persis didahulukan, lalu nilai terkecil (medium); lainnya nilai terbesar (atas rentang HAP)
    agg = []
    for (pid, c, eff), g in ev.groupby(["province_id", "commodity", "effective_at"]):
        if c == "beras" and g["exact"].any() and g.loc[g["exact"], "val"].notna().any():
            g = g[g["exact"]]
        v = g["val"].dropna()
        val = (v.min() if c == "beras" else v.max()) if len(v) else np.nan
        agg.append({"province_id": pid, "commodity": c, "effective_at": eff, "known_at": g["known_at"].min(), "log_val": np.log(val) if val == val else np.nan})
    return pd.DataFrame(agg).sort_values(["province_id", "commodity", "effective_at"]).reset_index(drop=True)


def policy_features(wide, ev):
    weeks = wide.index
    names = ["pol_age", "pol_n104", "ref_gap", "ref_chg_last", "ref_upcoming"]
    F = {n: pd.DataFrame(np.nan, index=weeks, columns=wide.columns) for n in names}
    F["pol_n104"][:] = 0.0
    wk = weeks.to_numpy()
    for (pid, c), g in ev.groupby(["province_id", "commodity"]):
        if (pid, c) not in wide.columns:
            continue
        known = g["known_at"].to_numpy("datetime64[ns]")
        eff = g["effective_at"].to_numpy("datetime64[ns]")
        lv = g["log_val"].to_numpy(float)
        age, n104, ref, chg, upc = (np.full(len(wk), np.nan) for _ in range(5))
        for i, t in enumerate(wk):
            kn = known <= t
            if kn.any():
                age[i] = (t - known[kn].max()) / np.timedelta64(7, "D")
            n104[i] = int(((known <= t) & (known > t - np.timedelta64(728, "D"))).sum())
            act = np.flatnonzero((eff <= t) & ~np.isnan(lv))
            if len(act):
                j = act[np.argmax(eff[act])]
                ref[i] = lv[j]
                prev = act[eff[act] < eff[j]]
                chg[i] = lv[j] - lv[prev[np.argmax(eff[prev])]] if len(prev) else 0.0
                pend = np.flatnonzero((known <= t) & (eff > t) & ~np.isnan(lv))
                upc[i] = (lv[pend[np.argmax(eff[pend])]] - lv[j]) if len(pend) else 0.0
        F["pol_age"][(pid, c)] = age
        F["pol_n104"][(pid, c)] = n104
        F["ref_gap"][(pid, c)] = wide[(pid, c)].ffill(limit=8).to_numpy() - ref
        F["ref_chg_last"][(pid, c)] = chg
        F["ref_upcoming"][(pid, c)] = upc
    return F


if __name__ == "__main__":
    base = pd.read_parquet(os.path.join(EXP, "base.parquet"))
    wide = base.pivot(index="week", columns=KEYS, values="log_p").sort_index()
    ywide = {h: base.pivot(index="week", columns=KEYS, values=f"y_{h}").reindex(index=wide.index, columns=wide.columns) for h in H}
    F = base_rate_features(wide, ywide)
    ev = policy_events()
    ev.to_csv(os.path.join(HERE, "..", "hasil", "policy_events.csv"), index=False)
    lead = ev[ev["known_at"] < ev["effective_at"]].drop_duplicates(["commodity", "effective_at"])
    print("kejadian kebijakan (komoditas × tanggal berlaku):", ev.drop_duplicates(["commodity", "effective_at"]).shape[0],
          "| diketahui sebelum berlaku:", len(lead))
    print(lead[["commodity", "known_at", "effective_at"]].to_string(index=False))
    F.update(policy_features(wide, ev))
    long = pd.concat({n: f.stack(KEYS, future_stack=True) for n, f in F.items()}, axis=1)
    long.index.names = ["week"] + KEYS
    out = base.merge(long.reset_index(), on=["week"] + KEYS, how="left")
    assert out[["week"] + KEYS].equals(base[["week"] + KEYS])
    out.to_parquet(os.path.join(EXP, "regime.parquet"))
    dev = out[(out["week"] >= "2020-01-01") & (out["week"] < "2024-01-01")]
    test = out[out["week"] >= "2024-01-01"]
    desc = pd.DataFrame({"na_dev": dev[list(F)].isna().mean(), "na_test": test[list(F)].isna().mean(),
                         "mean_dev": dev[list(F)].mean(), "mean_test": test[list(F)].mean()})
    print(desc.round(3).to_string())
