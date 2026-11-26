"""D-157 layar Data Understanding (EKSPERIMEN.md §3) untuk W_NAT, W_LOC, IMP — origin pengembangan saja.

Residual r = 1[y > 0] − p_up C1t resmi (baris y ≠ 0). Korelasi pooled + bootstrap blok origin (fungsi `screen` D-153), mentah dan
**parsial** (fitur diresidualkan per komoditas terhadap nat_dp_1, nat_dp_4, lag_dp_4, dev_ma13 — sinyal yang sudah dipakai C1t).
Populasi: W_NAT pada baris hortikultura (cabai merah, cabai rawit, bawang merah); W_LOC semua baris; IMP baris komoditas keranjang.
Kontrol: `iw_gap` (positif), derau & `dev_ma13` (negatif). q BH per keluarga × horizon. Keluaran hasil/du_wi.csv.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import AUD, H, bh_fdr, np, official_c1t, pd, table  # noqa: E402
import feats_wi as F  # noqa: E402

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
CTRL = ["nat_dp_1", "nat_dp_4", "lag_dp_4", "dev_ma13"]
cw = table("cw")
P = official_c1t("dev")
P = P[P["y_true"] != 0].copy()
P["r"] = (P["y_true"] > 0).astype(float) - P["score"]
cols = sorted(set(F.W_NAT + F.W_LOC + F.IMP + CTRL + ["iw_gap"]))
D = P.merge(cw[["week", "province_id", "commodity"] + cols].rename(columns={"week": "origin"}), on=["origin", "province_id", "commodity"])


def partial(d, x):
    """x diresidualkan per komoditas terhadap CTRL (baris lengkap)."""
    out = pd.Series(np.nan, index=d.index)
    for _, g in d.groupby("commodity"):
        g = g.dropna(subset=[x] + CTRL)
        if len(g) < 50 or g[x].std() == 0:
            continue
        X = np.column_stack([np.ones(len(g)), g[CTRL].to_numpy(float)])
        b, *_ = np.linalg.lstsq(X, g[x].to_numpy(float), rcond=None)
        out.loc[g.index] = g[x].to_numpy(float) - X @ b
    return out


FAMS = {"W_NAT": (F.W_NAT, list(F.HORTI)), "W_LOC": (F.W_LOC, None), "IMP": (F.IMP, list(F.BASKET))}
rows = []
for h in H:
    dh = D[D["horizon"] == h].copy()
    dh["noise"] = np.random.default_rng(157 + h).normal(size=len(dh))
    for c, role in (("iw_gap", "kontrol+"), ("noise", "kontrol-"), ("dev_ma13", "kontrol- (dipakai C1t)")):
        rows.append({"horizon": h, "family": role, "feature": c, "kind": "mentah", **screen(dh, c, h)})
    for fam, (fc, comms) in FAMS.items():
        d = dh if comms is None else dh[dh["commodity"].isin(comms)]
        d = d.copy()
        for c in fc:
            rows.append({"horizon": h, "family": fam, "feature": c, "kind": "mentah", **screen(d, c, h)})
            d[f"{c}__p"] = partial(d, c)
            rows.append({"horizon": h, "family": fam, "feature": c, "kind": "parsial", **screen(d, f"{c}__p", h)})
    print("h", h, "selesai", flush=True)
t = pd.DataFrame(rows)
t["q_bh"] = np.nan
for (h, fam, kind), g in t[~t["family"].str.startswith("kontrol")].groupby(["horizon", "family", "kind"]):
    ok = g["p"].notna()
    t.loc[g.index[ok], "q_bh"] = bh_fdr(g.loc[ok, "p"].to_numpy())
pos = t[(t["feature"] == "iw_gap")].set_index("horizon")["rho"].abs()
t["half_pos"] = t["horizon"].map(pos / 2)
t["pass_h"] = (t["q_bh"] < 0.05) & (t["rho"].abs() >= t["half_pos"])
t.round(4).to_csv(os.path.join(OUT, "du_wi.csv"), index=False)
pd.set_option("display.width", 220)
print(t[t["family"].str.startswith("kontrol")][["horizon", "feature", "rho", "lo", "hi", "p"]].round(4).to_string(index=False))
w = t[~t["family"].str.startswith("kontrol")].pivot_table(index=["family", "feature", "kind"], columns="horizon",
                                                          values=["rho", "lo", "hi", "q_bh", "pass_h"], aggfunc="first")
w["gate"] = w[("pass_h", 4)].astype(bool) & w[("pass_h", 8)].astype(bool)
print(w.round(3).to_string())
print("lolos gerbang (parsial):", [i for i in w.index[w["gate"]] if i[2] == "parsial"])
