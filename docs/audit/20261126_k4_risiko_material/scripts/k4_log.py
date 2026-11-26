"""K4 — registri eksperimen terpisah (EXPERIMENT_LOG.csv) + metrik panjang (hasil/k4_metrics_long.csv).

Satu baris per eksperimen × bagian (dev/test) × horizon × tingkat (ALL, per komoditas); metrik per provinsi & per origin di
hasil/k4_metrics_long.csv. Membaca prediksi EXP/k4_{dev,test}_preds.parquet (+ kalibrasi walk-forward seperti k4_eval.py),
leak_checks.csv, k4_decision.json; baris prediksi maju (forward) tanpa metrik.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k4_common import EXP, H, OUT, np, pd, platt_walkforward, brier, ece, logloss  # noqa: E402
from k4_eval import Origins, fast_ap, fast_auc, flags_k  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FEATS = "tuned_columns('C1t', h): 36 numerik + commodity, region (kategori)"
HGB = "HistGradientBoostingClassifier TUNED_HGB (C1-tuned), seed 20261121, tanpa bobot kelas"
EXPS = [  # id, skor, target, model, fitur, peran
    ("K4-E80", "k4_e80", "z_e80", HGB + "; label z, semua baris latih (termasuk y = 0)", FEATS, "kandidat"),
    ("K4-E80-cal", "k4_e80_cal", "z_e80", "K4-E80 + Platt global walk-forward (≥ 6 origin lampau)", FEATS, "varian peluang"),
    ("K4-A80", "k4_a80", "z_a80", HGB + "; label z_any (kejadian dalam jendela)", FEATS, "target alternatif"),
    ("K4-A80-cal", "k4_a80_cal", "z_a80", "K4-A80 + Platt global walk-forward", FEATS, "target alternatif"),
    ("K4-E70", "k4_e70", "z_e70", HGB + "; label z P70", FEATS, "kepekaan"),
    ("K4-E90", "k4_e90", "z_e90", HGB + "; label z P90", FEATS, "kepekaan"),
    ("K4-S90", "k4_s90", "z_s90", HGB + "; label z P90 y bertanda", FEATS, "kepekaan"),
    ("B-C1t", "c1t", "z_e80", "C1-tuned p_up (arah; latih y ≠ 0), refit = artefak resmi", FEATS, "pembanding"),
    ("B-C1t-cal", "c1t_cal", "z_e80", "C1-tuned p_up + Platt global walk-forward → z", FEATS, "pembanding"),
    ("B-CLIM", "clim_e80", "z_e80", "laju z komoditas di baris latih", "commodity", "pembanding"),
    ("B-CLIMS", "clims_e80", "z_e80", "laju z komoditas × bulan origin di baris latih (< 50 baris → B-CLIM)", "commodity, bulan", "pembanding"),
    ("B-R_mom", "R_mom", "z_e80", "aturan naif D-154: Δ log 4 minggu sendiri", "lag_dp_4", "pembanding"),
    ("B-R_nat", "R_nat", "z_e80", "aturan naif D-154: Δ4 nasional komoditas", "nat_dp_4", "pembanding"),
    ("B-R_rev", "R_rev", "z_e80", "aturan naif D-154: −deviasi MA13", "dev_ma13", "pembanding"),
    ("B-R_seas", "R_seas", "z_e80", "aturan naif D-154: perubahan h minggu tahun lalu", "yseas_52_h", "pembanding"),
    ("B-C1t@any", "c1t", "z_a80", "C1-tuned p_up pada target kejadian", FEATS, "pembanding target alternatif"),
    ("B-K4-E80@any", "k4_e80", "z_a80", "skor K4-E80 pada target kejadian", FEATS, "pembanding target alternatif"),
    ("B-CLIMS@any", "clims_a80", "z_a80", "laju z_any komoditas × bulan", "commodity, bulan", "pembanding target alternatif"),
]
TDEF = {"z_e80": ("titik akhir: y_h ≥ thr", "P80 |y_h| baris latih komoditas, walk-forward per origin"),
        "z_a80": ("kejadian: max_{k≤h}(p_{t+k}−p_t) ≥ thr", "P80 |y_h| baris latih komoditas, walk-forward per origin"),
        "z_e70": ("titik akhir: y_h ≥ thr", "P70 |y_h| walk-forward"), "z_e90": ("titik akhir: y_h ≥ thr", "P90 |y_h| walk-forward"),
        "z_s90": ("titik akhir: y_h ≥ thr", "P90 y_h bertanda walk-forward")}
PROB = {"k4_e80", "k4_e80_cal", "k4_a80", "k4_a80_cal", "k4_e70", "k4_e90", "k4_s90", "c1t", "c1t_cal", "clim_e80", "clims_e80",
        "clims_a80"}


def load(part):
    p = os.path.join(EXP, f"k4_{part}_preds.parquet")
    if not os.path.exists(p):
        return None
    P = pd.read_parquet(os.path.join(EXP, "k4_dev_preds.parquet")).assign(part="dev")
    if part == "test":
        P = pd.concat([P, pd.read_parquet(p).assign(part="test")], ignore_index=True)
    P["R_mom"], P["R_nat"], P["R_rev"], P["R_seas"] = P["lag_dp_4"], P["nat_dp_4"], -P["dev_ma13"], P["yseas_52"]
    out = []
    for h in H:
        d = P[P["horizon"] == h].sort_values(["origin", "province_id", "commodity"]).reset_index(drop=True)
        for s, z, name in (("c1t", "z_e80", "c1t_cal"), ("k4_e80", "z_e80", "k4_e80_cal"), ("k4_a80", "z_a80", "k4_a80_cal")):
            d[name] = platt_walkforward(d, s, z, h)
        out.append(d)
    P = pd.concat(out, ignore_index=True)
    return P[P["part"] == part].reset_index(drop=True)


def metrics(d, s, z, flags=None, prob_mask=None):
    y = d[z].to_numpy(int)
    v = d[s].to_numpy(float)
    r = {"n": len(d), "n_pos": int(y.sum()), "base_rate": float(y.mean()) if len(d) else np.nan,
         "pr_auc": fast_ap(y, v), "roc_auc": fast_auc(y, v)}
    if flags is not None:
        no = d["origin"].nunique()
        for k, f in flags.items():
            hit = (f & (y == 1)).sum()
            r[f"precision_k{k}"] = hit / f.sum() if f.sum() else np.nan
            r[f"recall_k{k}"] = hit / y.sum() if y.sum() else np.nan
            if k == 2:
                r["alerts_per_origin_k2"] = f.sum() / no
                r["false_positives_k2"] = int(f.sum() - hit)
                r["false_negatives_k2"] = int(y.sum() - hit)
    if s in PROB and prob_mask is not None:
        m = prob_mask & np.isfinite(v)
        if m.sum():
            r.update({"brier": brier(y[m], v[m]), "logloss": logloss(y[m], v[m]), "ece": ece(y[m], v[m]), "n_prob": int(m.sum())})
    return r


if __name__ == "__main__":
    leak = pd.read_csv(os.path.join(OUT, "leak_checks.csv"))
    leak_ok = "PASS" if leak["pass"].all() else "FAIL"
    dec = json.load(open(os.path.join(OUT, "k4_decision.json")))
    rows, long = [], []
    for part in ("dev", "test"):
        D = load(part)
        if D is None:
            continue
        dpart = json.load(open(os.path.join(OUT, f"k4{'' if part == 'dev' else '_test'}_decision.json")))
        for h in H:
            d = D[D["horizon"] == h].reset_index(drop=True)
            O = Origins(d, h)
            pmask = (d["c1t_cal"].notna() & d["k4_e80_cal"].notna()).to_numpy()
            pmask_any = (d["k4_a80_cal"].notna()).to_numpy()
            for eid, s, z, model, feats, role in EXPS:
                if s not in d:
                    continue
                fl = {k: flags_k(d, s, k) for k in (1, 2, 3)}
                pm = pmask_any if z == "z_a80" else pmask
                base = {"experiment_id": eid, "part": part, "role": role, "target_definition": TDEF[z][0], "threshold": TDEF[z][1],
                        "horizon": h, "model": model, "features": feats, "leakage_audit": leak_ok}
                if eid == "K4-E80":
                    decision, note = dpart.get("decision_technical"), f"R1 {dpart.get('R1')}, R1b {dpart.get('R1b')}, R2 mentah {dpart.get('R2_raw')}; operasional BLOCKED (U109)"
                elif eid == "K4-E80-cal":
                    decision, note = ("dipilih untuk peluang" if dpart.get("selected_prob_variant") == "k4_e80_cal" else "tidak dipilih"), f"R2 cal {dpart.get('R2_cal')}"
                elif role == "pembanding" or role.startswith("pembanding"):
                    decision, note = "BASELINE", ("naif terbaik dev" if s == dec["best_naive"].get(str(h)) else "")
                else:
                    decision, note = "DESKRIPTIF", "bukan kandidat (PROTOCOL §2); tidak dipilih"
                ap_b = O.boot_ap(d[z].to_numpy(int), d[s].to_numpy(float))
                r = {**base, "level": "ALL", "unit": "ALL", **metrics(d, s, z, fl, pm),
                     "pr_auc_ci": f"{np.nanpercentile(ap_b, 2.5):.4f}..{np.nanpercentile(ap_b, 97.5):.4f}",
                     "decision": decision, "decision_note": note}
                rows.append(r)
                for c, g in d.groupby("commodity"):
                    ii = g.index.to_numpy()
                    rows.append({**base, "level": "commodity", "unit": c,
                                 **metrics(g, s, z, {k: v[ii] for k, v in fl.items()}, pm[ii]), "decision": decision, "decision_note": ""})
                if eid in ("K4-E80", "K4-E80-cal", "B-C1t", "B-C1t-cal", "B-CLIMS", "K4-A80", "B-C1t@any"):
                    for lvl, col in (("province", "province_id"), ("origin", "origin")):
                        for u, g in d.groupby(col):
                            ii = g.index.to_numpy()
                            long.append({"experiment_id": eid, "part": part, "horizon": h, "level": lvl, "unit": str(u)[:10],
                                         **metrics(g, s, z, {k: v[ii] for k, v in fl.items()}, pm[ii])})
            print(part, h, "selesai", flush=True)
    fw = os.path.join(OUT, "k4_forward_manifest.json")
    if os.path.exists(fw):
        m = json.load(open(fw))
        for eid in ("K4-E80", "K4-A80", "B-C1t", "B-CLIMS"):
            rows.append({"experiment_id": eid, "part": "forward", "role": "prediksi maju beku", "level": "ALL", "unit": "ALL",
                         "horizon": "4,8", "leakage_audit": leak_ok, "decision": "BEKU (menunggu target)",
                         "decision_note": f"{m['n_rows']} baris, origin {m['origins']}, sha256 {m['sha256'][:16]}…; target lengkap {m['target_complete_by']}"})
    L = pd.DataFrame(rows)
    first = ["experiment_id", "part", "role", "level", "unit", "horizon", "target_definition", "threshold", "base_rate", "model", "features",
             "n", "n_pos", "pr_auc", "pr_auc_ci", "roc_auc", "precision_k1", "recall_k1", "precision_k2", "recall_k2", "precision_k3",
             "recall_k3", "brier", "logloss", "ece", "n_prob", "alerts_per_origin_k2", "false_positives_k2", "false_negatives_k2",
             "leakage_audit", "decision", "decision_note"]
    L = L[[c for c in first if c in L.columns]]
    L.round(5).to_csv(os.path.join(HERE, "..", "EXPERIMENT_LOG.csv"), index=False)
    pd.DataFrame(long).round(5).to_csv(os.path.join(OUT, "k4_metrics_long.csv"), index=False)
    print(L[L["level"] == "ALL"].drop(columns=["model", "features", "threshold", "target_definition"]).round(4).to_string(index=False))
