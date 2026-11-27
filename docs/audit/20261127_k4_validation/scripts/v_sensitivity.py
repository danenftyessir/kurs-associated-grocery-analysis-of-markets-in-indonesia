"""Kepekaan definisi target K4 (dev saja; PROTOCOL_ADDENDUM §5). Deskriptif: tidak ada target yang dipilih.

Untuk P70 / P80 / P90 |y|, P90 y bertanda, kejadian dalam jendela P80, dan target ilustratif seragam 5% / 10% (tanpa model khusus):
laju, komposisi positif, ambang median (persen & rupiah/kg), AP & presisi@K2 skor yang ada, Δ terhadap C1t & CLIM (bootstrap blok origin).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v_common import H, REGULATED, fast_ap, flags_k, np, pd, preds, save  # noqa: E402
from k4_eval import Origins, paired  # noqa: E402

OWN = {"z_e70": "e70", "z_e80": "e80", "z_e90": "e90", "z_s90": "s90", "z_a80": "a80"}


def main():
    D = preds("dev")
    ROWS, PAIRS, COMP = [], [], []
    for h in H:
        d = D[D["horizon"] == h].reset_index(drop=True)
        d["z_u05"] = (d["y"] >= np.log(1.05)).fillna(False).astype(int)
        d["z_u10"] = (d["y"] >= np.log(1.10)).fillna(False).astype(int)
        price = np.exp(d["log_p"])
        O = Origins(d, h)
        for z in ("z_e70", "z_e80", "z_e90", "z_s90", "z_a80", "z_u05", "z_u10"):
            key = OWN.get(z)
            y = d[z].to_numpy(int)
            r = {"horizon": h, "target": z, "base_rate": y.mean(), "n_pos": int(y.sum()),
                 "pos_share_regulated": float(d.loc[y == 1, "commodity"].isin(REGULATED).mean()),
                 "min_pos_per_commodity": int(d.groupby("commodity")[z].sum().min())}
            scores = ["k4_e80", "c1t", "clim_e80"] + ([f"k4_{key}", f"clim_{key}", f"clims_{key}"] if key and key != "e80" else ["clims_e80"])
            for s in dict.fromkeys(scores):
                r[f"ap_{s}"] = fast_ap(y, d[s].to_numpy(float))
                f = flags_k(d, s, 2)
                r[f"prec_k2_{s}"] = (f & (y == 1)).sum() / f.sum()
            ROWS.append(r)
            if key:
                thr = d[f"thr_{key}"]
                for c, g in d.assign(rp=price * (np.exp(thr) - 1), thr=thr).groupby("commodity"):
                    COMP.append({"horizon": h, "target": z, "commodity": c, "base_rate": g[z].mean(),
                                 "pos_share": g[z].sum() / max(y.sum(), 1), "thr_pct_median": 100 * (np.exp(g["thr"].median()) - 1),
                                 "thr_rp_per_kg_median": g["rp"].median()})
                own = f"k4_{key}"
                PAIRS += paired(O, own, "c1t", z, ("ap", "prec_k2"))
                PAIRS += paired(O, own, f"clim_{key}", z, ("ap", "prec_k2"))
                if own != "k4_e80":
                    PAIRS += paired(O, own, "k4_e80", z, ("ap", "prec_k2"))
            else:
                PAIRS += paired(O, "k4_e80", "c1t", z, ("ap", "prec_k2"))
                PAIRS += paired(O, "k4_e80", "clim_e80", z, ("ap", "prec_k2"))
        for c, g in d.groupby("commodity"):
            for z in ("z_u05", "z_u10"):
                COMP.append({"horizon": h, "target": z, "commodity": c, "base_rate": g[z].mean(),
                             "pos_share": g[z].sum() / max(d[z].sum(), 1), "thr_pct_median": 5.0 if z == "z_u05" else 10.0,
                             "thr_rp_per_kg_median": float((np.exp(g["log_p"]) * (1.05 if z == "z_u05" else 1.10) - np.exp(g["log_p"])).median())})
    R, P, C = save(pd.DataFrame(ROWS), "sens_targets.csv"), save(pd.DataFrame(PAIRS), "sens_paired.csv"), save(pd.DataFrame(COMP), "sens_composition.csv")
    pd.set_option("display.width", 260)
    print(R.round(3).T.to_string())
    print(P.round(4).to_string(index=False))
    print(C[C["target"].isin(["z_e80", "z_u05"])].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
