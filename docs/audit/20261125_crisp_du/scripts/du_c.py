"""D-153 DU-3c: sinyal tetangga intraminggu setelah dikurangi bagian yang dijelaskan iw_gap & iw_return sendiri + rerata nasional LOO
(OLS per horizon pada baris dev) → layar terhadap residual base dan IW_NAT. Kontrol: iw_gap sendiri yang di-partial-kan harus ≈ 0."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import pandas as pd

from du import EXP, K, finish, screen  # noqa: E402
import du_b  # noqa: E402,F401  (memastikan berkas du1b/du2b/du3b ada lebih dulu bila dijalankan berurutan)

tab = pd.read_parquet(os.path.join(EXP, "iw2.parquet"))
preds = pd.read_parquet(os.path.join(EXP, "d151_iw_dev_preds.parquet"))
preds = preds[np.isfinite(preds["y_true"]) & (preds["y_true"] != 0)].copy()
preds["r"] = (preds["y_true"] > 0).astype(float) - preds["p_up"]
import du as du_mod  # noqa: E402
reg = du_mod.cfg.regions.set_index("province_id")
ids = reg.index.astype(int).tolist()
dist = np.array([[du_mod.haversine_km(reg.loc[a, "lat"], reg.loc[a, "lon"], reg.loc[b, "lat"], reg.loc[b, "lon"]) for b in ids] for a in ids])
geo = {a: [ids[j] for j in np.argsort(dist[i])[1:4]] for i, a in enumerate(ids)}
Wc = tab.pivot_table(index=["week", "commodity"], columns="province_id", values="iw_gap")
tot, cnt = Wc.sum(axis=1), Wc.notna().sum(axis=1)
vals = {p: Wc[[q for q in geo[p] if q in Wc.columns]].mean(axis=1) - (tot - Wc[p].fillna(0)) / (cnt - Wc[p].notna().astype(int)) for p in Wc.columns}
nb = pd.DataFrame(vals).stack().rename_axis(["origin", "commodity", "province_id"]).rename("nb_geo").reset_index()
own = tab[["week"] + K + ["iw_gap", "iw_return", "iw_gap_nat_loo", "iw_return_nat_loo"]].rename(columns={"week": "origin"})
rows = []
for ref in ("base", "IW_NAT"):
    for h in (4, 8):
        d = preds[(preds["variant"] == ref) & (preds["horizon"] == h)].merge(nb, on=["origin", "commodity", "province_id"]).merge(own, on=["origin"] + K)
        d = d.dropna(subset=["nb_geo", "iw_gap", "iw_return", "iw_gap_nat_loo", "iw_return_nat_loo"])
        X = np.column_stack([np.ones(len(d)), d[["iw_gap", "iw_return", "iw_gap_nat_loo", "iw_return_nat_loo"]].to_numpy()])
        d["nb_perp"] = d["nb_geo"] - X @ np.linalg.lstsq(X, d["nb_geo"].to_numpy(), rcond=None)[0]
        Xo = np.column_stack([np.ones(len(d)), d[["iw_return", "iw_gap_nat_loo", "iw_return_nat_loo", "nb_geo"]].to_numpy()])
        d["own_perp"] = d["iw_gap"] - Xo @ np.linalg.lstsq(Xo, d["iw_gap"].to_numpy(), rcond=None)[0]
        r2 = 1 - d["nb_perp"].var() / d["nb_geo"].var()
        rows.append({"du": "DU-3c", "role": "kandidat", "signal": "tetangga geo − nasional iw_gap ⊥ intraminggu sendiri+nasional",
                     "residual_of": ref, "horizon": h, "share_explained_by_own": r2, **screen(d, "nb_perp", h)})
        rows.append({"du": "DU-3c", "role": "kontrol-", "signal": "iw_gap sendiri ⊥ lainnya", "residual_of": ref, "horizon": h,
                     "share_explained_by_own": np.nan, **screen(d, "own_perp", h)})
T = finish(rows, "du3c_graph_partial")
pd.set_option("display.width", 250)
print(T.round(4).to_string(index=False))
