"""K4 PROTOCOL §4 — integritas & kebocoran.

(1) B-C1t refit (k4_dev_preds) = artefak resmi `direction_tuned_preds` C1t pada baris bertarget.
(2) Perturbasi: untuk 3 origin × 2 horizon, harga mingguan panel sesudah origin dan y_h tabel dengan week + h > origin diganti acak
    → ambang, laju-dasar, dan prediksi C1t / K4-E80 / K4-A80 / kepekaan harus identik (label latih & ambang hanya dari jendela ≤ origin).
(3) Ukuran universe dev. Keluaran hasil/leak_checks.csv.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k4_common as kc  # noqa: E402
import k4_run as kr  # noqa: E402
from k4_common import EXP, H, OUT, cfg, origin_list, pd, np  # noqa: E402

COLS = ["c1t", "k4_e80", "k4_a80", "k4_e70", "k4_e90", "k4_s90", "thr_e80", "thr_a80", "thr_s90", "clim_e80", "clim_a80", "clims_e80"]

if __name__ == "__main__":
    rows = []
    # (1) refit C1t = resmi
    from kagami.utils.io import read_artifact
    P = pd.read_parquet(os.path.join(EXP, "k4_dev_preds.parquet"))
    off = read_artifact(cfg, "direction_tuned_preds")
    off = off[off["model"] == "C1t"][["origin", "horizon", "province_id", "commodity", "p_up", "y_true"]]
    m = P.merge(off, on=["origin", "horizon", "province_id", "commodity"], how="left")
    bt = m[m["has_target"]]
    rows.append({"check": "c1t_refit_equals_official", "n": len(bt), "n_unmatched": int(bt["p_up"].isna().sum()),
                 "max_abs_diff": float((bt["c1t"] - bt["p_up"]).abs().max()), "y_equal": bool(np.allclose(bt["y"], bt["y_true"])),
                 "pass": bool(bt["p_up"].notna().all() and (bt["c1t"] - bt["p_up"]).abs().max() <= 1e-9)})
    rows.append({"check": "universe_dev", "n": int(len(P)), "detail": P.groupby("horizon").size().to_dict(),
                 "n_without_target": int((~P["has_target"]).sum()),
                 "pass": bool(P.groupby("horizon").size().to_dict() == {4: 12800, 8: 12463})})
    # (2) perturbasi masa depan
    clean_tab = kr.tab().copy()
    lp_clean = kc.panel_logp().copy()
    rng = np.random.default_rng(cfg.seed + 6401)
    for h in H:
        ol = origin_list(h, "dev")
        for o in (ol[6], ol[len(ol) // 2], ol[-1]):
            kc._T["lp"] = lp_clean
            kr._TAB["t"] = clean_tab
            a, _ = kr.one(h, o, cfg.seed)
            lp = lp_clean.copy()
            fut = lp.index > o
            lp.loc[fut] = lp.loc[fut].to_numpy() + rng.normal(0, 0.3, lp.loc[fut].shape)
            kc._T["lp"] = lp
            t = kc.add_event(kc.table())
            for hh in H:
                bad = (t["week"] + pd.Timedelta(weeks=hh) > o) & t[f"y_{hh}"].notna()
                t.loc[bad, f"y_{hh}"] = rng.normal(0, 0.3, int(bad.sum()))
            kr._TAB["t"] = t
            b, _ = kr.one(h, o, cfg.seed)
            changed_future = int(((t["week"] + pd.Timedelta(weeks=h) > o) & (t[f"ymax_{h}"] != clean_tab[f"ymax_{h}"])
                                  & t[f"ymax_{h}"].notna()).sum())
            diff = max(float(np.nanmax(np.abs(a[c].to_numpy(float) - b[c].to_numpy(float)))) for c in COLS)
            rows.append({"check": "perturb_future", "horizon": h, "origin": o.date(), "n": len(a), "max_abs_diff": diff,
                         "n_future_ymax_changed": changed_future, "pass": bool(diff == 0.0 and changed_future > 0)})
            print(rows[-1], flush=True)
    kc._T["lp"] = lp_clean
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "leak_checks.csv"), index=False)
    print(R.to_string(index=False))
    assert R["pass"].all(), "integritas/kebocoran GAGAL"
