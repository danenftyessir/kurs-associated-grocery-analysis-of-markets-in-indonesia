"""Layar Data Understanding (EKSPERIMEN.md §3, D-153) untuk fitur keluarga baru D-156, hanya origin pengembangan.

Residual r = 1[y > 0] − p_up C1t resmi (baris y ≠ 0). Korelasi pooled residual–fitur pada origin, interval & p bootstrap blok origin
(fungsi `screen` D-153), q BH dalam keluarga semua fitur baru (per horizon). Kontrol positif `iw_gap`, negatif derau & `dev_ma13`.
Gerbang: q < 0,05 di kedua horizon dan |ρ| ≥ ½ |ρ kontrol positif| di kedua horizon. Keluaran hasil/c_du.csv.
"""
import os
import sys

from c_feats import FAMILIES, fam_cols
from m_common import AUD, H, OUT, bh_fdr, np, official_c1t, pd, table

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

fam = table("fam")
P = official_c1t("dev")
P = P[P["y_true"] != 0].copy()
P["r"] = (P["y_true"] > 0).astype(float) - P["score"]
rows = []
for h in H:
    feats = {c: f for f in FAMILIES for c in fam_cols(f, h)}
    cols = sorted(set(feats) | {"iw_gap", "dev_ma13"})
    d = P[P["horizon"] == h].merge(fam[["week", "province_id", "commodity"] + cols].rename(columns={"week": "origin"}),
                                   on=["origin", "province_id", "commodity"], how="left")
    d["noise"] = np.random.default_rng(156 + h).normal(size=len(d))
    for c, role in [("iw_gap", "kontrol+"), ("noise", "kontrol-"), ("dev_ma13", "kontrol- (dipakai C1t)")] + [(c, feats[c]) for c in feats]:
        rows.append({"horizon": h, "feature": c.replace(f"_h{h}", ""), "family": role, **screen(d, c, h)})
    print("h", h, "selesai", flush=True)
t = pd.DataFrame(rows)
t["q_bh"] = np.nan
for h in H:
    m = (t["horizon"] == h) & ~t["family"].str.startswith("kontrol") & t["p"].notna()
    t.loc[m, "q_bh"] = bh_fdr(t.loc[m, "p"].to_numpy())
pos = t[t["feature"] == "iw_gap"].set_index("horizon")["rho"].abs()
t["half_pos"] = t["horizon"].map(pos / 2)
t["pass_h"] = (t["q_bh"] < 0.05) & (t["rho"].abs() >= t["half_pos"])
w = t[~t["family"].str.startswith("kontrol")].pivot_table(index=["family", "feature"], columns="horizon", values=["rho", "q_bh", "pass_h"], aggfunc="first")
w["gate"] = w[("pass_h", 4)].astype(bool) & w[("pass_h", 8)].astype(bool)
t.round(4).to_csv(os.path.join(OUT, "c_du.csv"), index=False)
pd.set_option("display.width", 220)
print(t[t["family"].str.startswith("kontrol")][["horizon", "feature", "rho", "lo", "hi", "p"]].round(4).to_string(index=False))
print(w.round(4).to_string())
print("fitur lolos gerbang:", w.index[w["gate"]].tolist())
