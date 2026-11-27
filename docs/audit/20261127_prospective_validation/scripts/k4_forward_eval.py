"""K4 (D-164) — evaluasi prediksi maju beku SESUDAH target terealisasi. Aturan: FORWARD_VALIDATION_PROTOCOL.md §5 (disetujui Danen
2026-11-27, sebelum target pertama terlihat). Dibekukan bersama protokol (hasil/pv_protocol_sha256.txt). Tidak boleh diubah sesudah
snapshot yang memuat target diunduh.

Pemakaian (dari root project):
  python docs/audit/20261127_prospective_validation/scripts/k4_forward_eval.py --selftest                # sintetis, tanpa data
  KAGAMI_EXP=<exp K4> python .../k4_forward_eval.py --check-test                                        # label vs k4_test_preds (baca-saja)
  python .../k4_forward_eval.py --pihps-zip <snapshot PIHPS baru>                                       # evaluasi maju

Aturan beku:
- Prediksi: hasil/k4_forward_preds.csv K4 (sha256 diverifikasi terhadap manifest; gagal → berhenti). Tidak dilatih ulang.
- Label dihitung dari panel snapshot baru, TIDAK dari kolom z_* (kolom itu dibuat sebelum target terjadi; D-166):
  y_h = `fw_eval.labels` D-152 (hash diverifikasi); ymax_h = max_{k=1..h}(log p_{t+k} − log p_t) dari panel yang sama (minggu hilang
  dilewati; = `k4_common.add_event`); z_e80 = 1[y_h ≥ thr_e80 beku]; z_a80 = 1[ymax_h ≥ thr_e80 beku] (PROTOCOL K4 §2: ambang sama).
  Target tidak teramati pada origin lengkap → z = 0 (D-155); dilaporkan juga tanpa baris itu (deskriptif).
- Origin dinilai bila snapshot memuat Jumat minggu origin + h (aturan `fw_eval`), semua baris berkas beku pada origin itu.
- Metrik: `k4_eval.ranking` (AP pooled, AP rerata per origin, ROC-AUC, presisi/recall@K1–3 per provinsi, V2-setara; tie seed 154) untuk
  k4_e80, c1t, clim_e80, clims_e80 (z_e80) dan k4_a80, c1t, clims_a80 (z_a80); Brier, ECE 10 bin, Brier skill vs clim_e80 untuk
  k4_e80_cal, c1t_cal, k4_e80. Δ (k4_e80 − c1t, k4_e80 − clims_e80) + interval bootstrap kluster provinsi 1.999 rep (deskriptif).
- Penanda (per horizon, target utama z_e80): FAILED_FORWARD bila ΔAP(k4_e80 − c1t) < −0,14; CONSISTENT bila ΔAP ≥ 0 dan
  AP(k4_e80) ≥ AP(clims_e80); selain itu NOT_PROVEN. Interim bila origin horizon itu belum lengkap semua.
→ hasil/k4_forward_eval_<tanggal data terakhir>_{ranking,probability,paired,per_commodity,per_origin}.csv + _decision.json
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "..", "hasil")
K4 = os.path.join(AUD, "20261126_k4_risiko_material")
FROZEN = os.path.join(K4, "hasil", "k4_forward_preds.csv")
MANIFEST = os.path.join(K4, "hasil", "k4_forward_manifest.json")
FW_EVAL = os.path.join(AUD, "20261125_iw_validasi", "scripts", "fw_eval.py")
D152_MANIFEST = os.path.join(AUD, "20261125_iw_validasi", "hasil", "forward_manifest.json")
# dependensi metrik K4 (sha256 versi HEAD 3095ae0 / protocol_sha256.txt K4); berubah → berhenti
DEP_SHA = {os.path.join(K4, "scripts", "k4_eval.py"): "34560839639899bfef96faa561a0632383b53b240073e4c71ae2d15d720bf91c",
           os.path.join(K4, "scripts", "k4_common.py"): "d9a1852bdf80f01aa3240b3332071e53d5386e9449d9a7020c535cd8f1b21489"}
H = (4, 8)
FAIL_AP = {4: 0.14, 8: 0.14}
REPS = 1999
SEED = 20261127
KEY = ["origin", "province_id", "commodity"]
RANK_E = ["k4_e80", "c1t", "clim_e80", "clims_e80"]
RANK_A = ["k4_a80", "c1t", "clims_a80"]
PROB = ["k4_e80_cal", "c1t_cal", "k4_e80"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def same_content(path, frozen):
    """sha256 byte = beku, atau sama sesudah hanya ujung baris dinormalkan (checkout git `core.autocrlf` mengubah LF ↔ CRLF).
    Isi selain ujung baris tetap harus identik byte demi byte."""
    raw = open(path, "rb").read()
    lf = raw.replace(b"\r\n", b"\n")
    for how, b in (("byte", raw), ("lf", lf), ("crlf", lf.replace(b"\n", b"\r\n"))):
        if hashlib.sha256(b).hexdigest() == frozen:
            return how
    return None


def verify_inputs():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    how = same_content(FROZEN, man["sha256"])
    if how is None:
        raise SystemExit(f"k4_forward_preds.csv sha256 {sha256(FROZEN)[:12]}… ≠ manifest {man['sha256'][:12]}… — prediksi berubah, berhenti")
    if how != "byte":
        print(f"[k4_forward_eval] k4_forward_preds.csv cocok manifest sesudah normalisasi ujung baris ({how})")
    d152 = json.load(open(D152_MANIFEST, encoding="utf-8"))
    if same_content(FW_EVAL, d152["code_sha256"]["docs/audit/20261125_iw_validasi/scripts/fw_eval.py"]) is None:
        raise SystemExit("fw_eval.py (definisi label D-152) berubah sejak pembekuan — berhenti")
    for p, s in DEP_SHA.items():
        if same_content(p, s) is None:
            raise SystemExit(f"{os.path.basename(p)} berubah sejak dibekukan — berhenti")
    return man


def _k4():
    """Impor fungsi metrik K4 (k4_eval/k4_common) tanpa mengubahnya; k4_common mengatur sys.path & alias kagami."""
    sys.path.insert(0, os.path.join(K4, "scripts"))
    import k4_common as C  # noqa: E402
    import k4_eval as E  # noqa: E402
    return C, E


# ---------------------------------------------------------------- label
def panel_wide(zip_path):
    """Matriks minggu × (province_id, commodity) log harga mingguan dari snapshot — langkah yang sama dengan `fw_eval.labels`."""
    import types
    sys.path.insert(0, os.path.dirname(FW_EVAL))
    import fw_eval as F  # noqa: E402
    import pandas as pd
    shim = types.SimpleNamespace(source_path=lambda key: zip_path)
    daily = F.select_variants(F.cfg, F.load_pihps(shim, "pihps"))
    last = daily["date"].max()
    wp = F.cfg.params["weekly"]
    start = F.week_start(pd.Series([pd.Timestamp(F.cfg.params["period"]["start"])])).iloc[0]
    weeks = pd.date_range(start, F.week_start(pd.Series([last])).iloc[0], freq="W-MON")
    pw = F._aggregate(daily, weeks, F.cfg.regions["province_id"].astype(int).tolist(), list(F.cfg.commodities),
                      run_days=wp["carry_forward_run_days"], short_days=wp["short_week_days"], last_date=last)
    return pw.pivot(index="week", columns=["province_id", "commodity"], values="log_price").sort_index(), last


def targets_from_wide(wide, last, horizons=H):
    """→ origin, province_id, commodity, horizon, y, ymax, complete (ymax = k4_common.add_event pada panel ini)."""
    import numpy as np
    import pandas as pd
    idx = pd.date_range(wide.index.min(), wide.index.max() + pd.Timedelta(weeks=max(horizons)), freq="7D")
    lp = wide.reindex(idx)
    out = []
    for h in horizons:
        y = (lp.shift(-h) - lp)
        steps = np.stack([(lp.shift(-k) - lp).to_numpy() for k in range(1, h + 1)], 0)
        with np.errstate(all="ignore"):
            mx = np.where(np.isnan(steps).all(0), np.nan, np.nanmax(np.where(np.isnan(steps), -np.inf, steps), 0))
        mx = pd.DataFrame(mx, index=lp.index, columns=lp.columns)
        t = pd.DataFrame({"y": y.stack(["province_id", "commodity"], future_stack=True),
                          "ymax": mx.stack(["province_id", "commodity"], future_stack=True)}).reset_index()
        t = t.rename(columns={t.columns[0]: "origin"})
        t["complete"] = t["origin"] + pd.Timedelta(weeks=h) + pd.Timedelta(days=4) <= last
        out.append(t.assign(horizon=h))
    return pd.concat(out, ignore_index=True)


def label(preds, tg):
    """Prediksi beku + target → baris origin lengkap dengan z_e80, z_a80 (target tak teramati → 0) dan has_target."""
    import numpy as np
    d = preds.merge(tg, on=KEY + ["horizon"], how="left")
    done = d.groupby(["horizon", "origin"])["complete"].transform(lambda s: bool(s.fillna(False).all()))
    d = d[done].copy()
    d["has_target"] = np.isfinite(d["y"])
    d["z_e80"] = (d["has_target"] & (d["y"] >= d["thr_e80"])).astype(int)
    d["z_a80"] = (np.isfinite(d["ymax"]) & (d["ymax"] >= d["thr_e80"])).astype(int)
    return d.sort_values(["horizon"] + KEY).reset_index(drop=True)


# ---------------------------------------------------------------- metrik
def prob_metrics(C, d, s):
    import numpy as np
    m = np.isfinite(d[s]) & np.isfinite(d["clim_e80"])
    y, p, pc = d.loc[m, "z_e80"].to_numpy(float), d.loc[m, s].to_numpy(float), d.loc[m, "clim_e80"].to_numpy(float)
    b, bc = C.brier(y, p), C.brier(y, pc)
    return {"score": s, "n": int(m.sum()), "base_rate": float(y.mean()) if len(y) else np.nan, "mean_p": float(p.mean()) if len(p) else np.nan,
            "brier": b, "brier_clim": bc, "brier_skill": 1 - b / bc if bc > 0 else np.nan, "ece": C.ece(y, p) if len(y) else np.nan}


def paired_boot(E, d, a, b, z, reps=REPS, seed=SEED):
    """Δ AP & Δ Brier (a − b) + interval bootstrap kluster provinsi (deskriptif: mengabaikan korelasi waktu)."""
    import numpy as np
    y = d[z].to_numpy(int)
    sa, sb = d[a].to_numpy(float), d[b].to_numpy(float)
    full = E.fast_ap(y, sa) - E.fast_ap(y, sb)
    groups = d.groupby("province_id").indices
    keys = list(groups)
    rng = np.random.default_rng(seed)
    bd = np.full(reps, np.nan)
    for r in range(reps):
        ix = np.concatenate([groups[keys[j]] for j in rng.integers(0, len(keys), len(keys))])
        bd[r] = E.fast_ap(y[ix], sa[ix]) - E.fast_ap(y[ix], sb[ix])
    lo, hi = np.nanpercentile(bd, [2.5, 97.5])
    return {"a": a, "b": b, "target": z, "metric": "ap", "value_a": E.fast_ap(y, sa), "value_b": E.fast_ap(y, sb), "diff": full,
            "lo": float(lo), "hi": float(hi), "n": int(len(d)), "n_pos": int(y.sum()), "n_origins": int(d["origin"].nunique()),
            "n_clusters": len(keys)}


def flag(d_ap, ap_k4, ap_clims, h):
    if d_ap < -FAIL_AP[h]:
        return "FAILED_FORWARD"
    if d_ap >= 0 and ap_k4 >= ap_clims:
        return "CONSISTENT"
    return "NOT_PROVEN"


def evaluate(C, E, d, n_frozen_origins):
    """d = label(...). → dict tabel + keputusan per horizon."""
    import numpy as np
    import pandas as pd
    if d.empty:
        raise SystemExit("belum ada origin dengan target lengkap pada snapshot ini — evaluasi ditunda")
    rank, prob, pair, pc, po, dec = [], [], [], [], [], {}
    for h, dh in d.groupby("horizon"):
        h = int(h)
        dh = dh.sort_values(KEY).reset_index(drop=True)
        for variant, x in (("all", dh), ("observed_only", dh[dh["has_target"]].reset_index(drop=True))):
            for s in RANK_E:
                rank.append({"horizon": h, "rows": variant, **E.ranking(x, s, "z_e80")})
            for s in RANK_A:
                rank.append({"horizon": h, "rows": variant, **E.ranking(x, s, "z_a80")})
        for s in PROB:
            prob.append({"horizon": h, **prob_metrics(C, dh, s)})
        p1 = paired_boot(E, dh, "k4_e80", "c1t", "z_e80")
        p2 = paired_boot(E, dh, "k4_e80", "clims_e80", "z_e80")
        p3 = paired_boot(E, dh, "k4_a80", "c1t", "z_a80")
        pair += [{"horizon": h, **p} for p in (p1, p2, p3)]
        for c, g in dh.groupby("commodity"):
            y = g["z_e80"].to_numpy(int)
            pc.append({"horizon": h, "commodity": c, "n": len(g), "n_pos": int(y.sum()),
                       **{f"ap_{s}": E.fast_ap(y, g[s].to_numpy(float)) for s in RANK_E},
                       "mean_k4_e80_cal": float(g["k4_e80_cal"].mean())})
        for o, g in dh.groupby("origin"):
            y = g["z_e80"].to_numpy(int)
            fk = E.flags_k(g.reset_index(drop=True), "k4_e80", 2)
            fc = E.flags_k(g.reset_index(drop=True), "c1t", 2)
            po.append({"horizon": h, "origin": o, "n": len(g), "base_rate": float(y.mean()),
                       "partial_origin_week": bool(o == pd.Timestamp("2026-11-16")),
                       **{f"ap_{s}": E.fast_ap(y, g[s].to_numpy(float)) for s in RANK_E},
                       "prec_k2_k4_e80": float(y[fk].mean()), "prec_k2_c1t": float(y[fc].mean())})
        n_orig = int(dh["origin"].nunique())
        dec[h] = {"flag": flag(p1["diff"], p1["value_a"], p2["value_b"], h), "d_ap_vs_c1t": p1["diff"],
                  "d_ap_vs_c1t_ci": [p1["lo"], p1["hi"]], "ap_k4_e80": p1["value_a"], "ap_c1t": p1["value_b"],
                  "ap_clims_e80": p2["value_b"], "n_origins": n_orig, "n_origins_frozen": n_frozen_origins[h],
                  "interim": n_orig < n_frozen_origins[h], "fail_threshold": -FAIL_AP[h]}
    return {"ranking": pd.DataFrame(rank), "probability": pd.DataFrame(prob), "paired": pd.DataFrame(pair),
            "per_commodity": pd.DataFrame(pc), "per_origin": pd.DataFrame(po)}, dec


# ---------------------------------------------------------------- uji mandiri
def selftest():
    import numpy as np
    import pandas as pd
    from sklearn.metrics import average_precision_score
    C, E = _k4()
    rng = np.random.default_rng(0)
    weeks = pd.date_range("2026-08-03", periods=30, freq="7D")
    cols = pd.MultiIndex.from_product([range(1, 7), ["beras", "cabai_merah"]], names=["province_id", "commodity"])
    wide = pd.DataFrame(np.cumsum(rng.normal(0, 0.03, (len(weeks), len(cols))), 0), index=weeks, columns=cols)
    wide.iloc[12, 0] = np.nan                                   # minggu hilang
    last = weeks[-1] + pd.Timedelta(days=4)
    tg = targets_from_wide(wide, last)
    # (1) y & ymax manual
    o, h = weeks[10], 4
    r = tg[(tg.origin == o) & (tg.horizon == h) & (tg.province_id == 1) & (tg.commodity == "beras")].iloc[0]
    ser = wide[(1, "beras")]
    assert np.isclose(r.y, ser[weeks[14]] - ser[weeks[10]])
    exp_max = np.nanmax([ser[weeks[10 + k]] - ser[weeks[10]] for k in range(1, 5)])
    assert np.isclose(r.ymax, exp_max), "ymax harus melewati minggu hilang"
    # (2) kelengkapan = Jumat minggu t + h
    assert not tg[(tg.origin == weeks[-1]) & (tg.horizon == 4)]["complete"].any()
    assert tg[(tg.origin == weeks[-5]) & (tg.horizon == 4)]["complete"].all()
    # (3) label: z dari panel & thr beku, bukan kolom z lama
    pr = tg[tg.origin.isin(weeks[8:12])][["origin", "horizon", "province_id", "commodity"]].copy()
    pr["thr_e80"] = 0.02
    pr["z_e80"] = 0                                             # kolom z beku yang salah (semua 0) harus diabaikan
    for s in RANK_E + RANK_A[:1] + RANK_A[2:] + PROB:
        pr[s] = rng.random(len(pr))
    d = label(pr.drop(columns=["z_e80"]), tg)
    yy = d["y"].to_numpy()
    assert (d["z_e80"].to_numpy() == (np.isfinite(yy) & (yy >= 0.02))).all() and d["z_e80"].sum() > 0
    # (4) AP = sklearn; penanda
    y = d["z_e80"].to_numpy(int)
    assert abs(E.fast_ap(y, d["k4_e80"].to_numpy()) - average_precision_score(y, d["k4_e80"])) < 1e-12
    assert flag(-0.15, 0.2, 0.1, 4) == "FAILED_FORWARD" and flag(0.0, 0.2, 0.2, 8) == "CONSISTENT"
    assert flag(0.01, 0.1, 0.2, 4) == "NOT_PROVEN" and flag(-0.05, 0.3, 0.1, 8) == "NOT_PROVEN"
    tabs, dec = evaluate(C, E, d, {4: 4, 8: 4})
    assert set(dec) == {4, 8} and all(len(t) for t in tabs.values())
    print("selftest lolos:", {h: v["flag"] for h, v in dec.items()})


def check_test(zip_path):
    """Baca-saja: label dari snapshot beku pada origin test K4 = z_e80/z_a80 di k4_test_preds; AP = k4_test_ranking.csv."""
    import numpy as np
    import pandas as pd
    C, E = _k4()
    T = pd.read_parquet(os.path.join(C.EXP, "k4_test_preds.parquet"))
    wide, last = panel_wide(zip_path)
    tg = targets_from_wide(wide, last)
    sys.path.insert(0, os.path.dirname(FW_EVAL))
    import fw_eval as F  # noqa: E402
    yref, _ = F.labels(zip_path)
    m = tg.merge(yref, on=KEY + ["horizon"], suffixes=("", "_fw"))
    same = np.isclose(m["y"], m["y_fw"], atol=1e-12) | (m["y"].isna() & m["y_fw"].isna())
    print(f"y panel_wide = fw_eval.labels: {int(same.sum())}/{len(m)}; complete sama: {(m['complete'] == m['complete_fw']).all()}")
    assert same.all()
    d = label(T.drop(columns=["z_e80", "z_a80", "y", "ymax", "has_target"]), tg)
    chk = d.merge(T[KEY + ["horizon", "z_e80", "z_a80"]], on=KEY + ["horizon"], suffixes=("", "_ref"))
    for z in ("z_e80", "z_a80"):
        print(f"{z}: {int((chk[z] == chk[z + '_ref']).sum())}/{len(chk)} sama")
        assert (chk[z] == chk[z + "_ref"]).all()
    R = pd.read_csv(os.path.join(C.OUT, "k4_test_ranking.csv"))
    for h in H:
        x = d[d["horizon"] == h].sort_values(KEY).reset_index(drop=True)
        for s in ("k4_e80", "c1t", "clims_e80"):
            mine = E.ranking(x, s, "z_e80")
            ref = R[(R.horizon == h) & (R.score == s) & (R.target == "z_e80")].iloc[0]
            for m in ("ap", "roc_auc", "prec_k1", "prec_k2", "prec_k3", "prec_v2eq"):
                print(f"h{h} {s} {m}: {mine[m]:.6f} vs k4_test_ranking {ref[m]:.5f}")
                assert abs(mine[m] - ref[m]) <= 5e-6, "CSV dibulatkan 5 desimal"
    print("check-test lolos; data terakhir", last.date())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pihps-zip")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check-test", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        sys.exit(0)
    man = verify_inputs()
    if a.check_test:
        _C, _ = _k4()
        check_test(a.pihps_zip or str(_C.cfg.source_path("pihps")))
        sys.exit(0)
    if not a.pihps_zip:
        raise SystemExit("--pihps-zip wajib")
    import pandas as pd
    C, E = _k4()
    preds = pd.read_csv(FROZEN, parse_dates=["origin"])
    n_frozen = {int(h): len(v) for h, v in man["origins"].items()}
    wide, last = panel_wide(a.pihps_zip)
    d = label(preds, targets_from_wide(wide, last))
    print(f"data terakhir {last.date()}; origin lengkap " + ", ".join(f"h{h}: {d[d.horizon == h].origin.nunique()}" for h in H))
    tabs, dec = evaluate(C, E, d, n_frozen)
    tag = last.date()
    os.makedirs(OUT, exist_ok=True)
    for k, t in tabs.items():
        t.to_csv(os.path.join(OUT, f"k4_forward_eval_{tag}_{k}.csv"), index=False, lineterminator="\n")
    dec_out = {"data_last_date": str(tag), "pihps_zip_sha256": sha256(a.pihps_zip), "preds_sha256": man["sha256"],
               "decision": {str(h): v for h, v in dec.items()}}
    with open(os.path.join(OUT, f"k4_forward_eval_{tag}_decision.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dec_out, fh, indent=1, default=str)
    pd.set_option("display.width", 220)
    print(tabs["paired"].round(4).to_string(index=False))
    print(json.dumps(dec_out["decision"], indent=1, default=str))
