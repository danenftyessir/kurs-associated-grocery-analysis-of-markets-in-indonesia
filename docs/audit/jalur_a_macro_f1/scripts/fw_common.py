"""Jalur A Workstream A — bersama: lokasi prediksi maju beku (D-152, D-158), hash, metrik arah & probabilitas.

Fungsi metrik di sini murni (numpy/pandas) agar dapat dites tanpa data asli (`tests/test_forward_eval.py`).
Label & baris evaluasi mengikuti definisi resmi D-139/D-141: y = log p_{t+h} − log p_t, y = 0 dikeluarkan, naik = y > 0,
prediksi naik = p_up > 0,5.
"""
import hashlib
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(AUD, "..", ".."))
OUT = os.path.join(HERE, "..", "hasil")

FROZEN = {
    "D-152": {"preds": os.path.join(AUD, "20261125_iw_validasi", "hasil", "forward_preds.csv"),
              "manifest": os.path.join(AUD, "20261125_iw_validasi", "hasil", "forward_manifest.json"),
              "models": ["base", "IW_NAT"]},
    "D-158": {"preds": os.path.join(AUD, "20261126_nasional_lokal", "hasil", "forward_preds_d158.csv"),
              "manifest": os.path.join(AUD, "20261126_nasional_lokal", "hasil", "forward_manifest_d158.json"),
              "models": ["base", "FR_REF", "FR_CITY"]},
}
KEY = ["origin", "horizon", "province_id", "commodity"]
CANDIDATES = ["IW_NAT", "FR_REF", "FR_CITY"]        # FR_CITY hanya pembanding diagnostik (kontribusi kota ≈ 0, D-158)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_frozen(verify=True):
    """Gabungan prediksi beku → origin, horizon, model, province_id, commodity, p_up, source. Hash diverifikasi terhadap manifest."""
    import json
    parts = []
    for src, f in FROZEN.items():
        man = json.load(open(f["manifest"], encoding="utf-8"))
        if verify:
            got = sha256(f["preds"])
            if got != man["forward_preds_sha256"]:
                raise SystemExit(f"{src}: sha256 prediksi {got[:12]}… ≠ manifest {man['forward_preds_sha256'][:12]}… — prediksi berubah")
        d = pd.read_csv(f["preds"], parse_dates=["origin"])
        parts.append(d.assign(source=src))
    d = pd.concat(parts, ignore_index=True)
    base = d[d["model"] == "base"]
    # base D-152 dan D-158 harus identik (C1-tuned yang sama); simpan satu salinan
    b2 = base[base["source"] == "D-152"].merge(base[base["source"] == "D-158"], on=KEY, suffixes=("_a", "_b"))
    if verify and (len(b2) != (base["source"] == "D-152").sum() or np.abs(b2["p_up_a"] - b2["p_up_b"]).max() > 0):
        raise SystemExit("base D-152 ≠ base D-158")
    d = d[~((d["model"] == "base") & (d["source"] == "D-158"))]
    return d[KEY[:2] + ["model"] + KEY[2:] + ["p_up", "source"]].reset_index(drop=True)


def confusion(up, pred_up):
    up, pu = np.asarray(up, bool), np.asarray(pred_up, bool)
    return np.array([(up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()], float)


def class_stats(C):
    tp, fn, fp, tn = C
    with np.errstate(divide="ignore", invalid="ignore"):
        f1u, f1d = 2 * tp / (2 * tp + fp + fn), 2 * tn / (2 * tn + fn + fp)
        den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        return {"macro_f1": (f1u + f1d) / 2, "f1_up": f1u, "f1_down": f1d, "prec_up": tp / (tp + fp), "rec_up": tp / (tp + fn),
                "prec_down": tn / (tn + fn), "rec_down": tn / (tn + fp), "mcc": (tp * tn - fp * fn) / den if den > 0 else np.nan}


def auc(y, s):
    """ROC-AUC lewat statistik Mann–Whitney (ties = ½); NaN bila satu kelas."""
    y, s = np.asarray(y, bool), np.asarray(s, float)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(s).rank(method="average").to_numpy()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def brier(y, p):
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def ece(y, p, bins=10):
    """Expected calibration error, bin lebar sama [0, 1]."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    k = np.clip((p * bins).astype(int), 0, bins - 1)
    tot = 0.0
    for b in range(bins):
        m = k == b
        if m.any():
            tot += m.sum() * abs(p[m].mean() - y[m].mean())
    return float(tot / len(y))


def metrics(d):
    """d: kolom y, p_up. Hanya baris y ≠ 0 (definisi resmi)."""
    nz = d[np.isfinite(d["y"]) & (d["y"] != 0)]
    up = nz["y"].to_numpy() > 0
    p = nz["p_up"].to_numpy(float)
    st = class_stats(confusion(up, p > 0.5))
    st.update({"roc_auc": auc(up, p), "brier": brier(up, p), "ece": ece(up, p), "n": int(len(nz)),
               "share_up_true": float(up.mean()) if len(up) else np.nan, "share_up_pred": float((p > 0.5).mean()) if len(p) else np.nan})
    return st


def paired(a, b, cluster="province_id", reps=1999, seed=20261126):
    """Selisih a − b (macro F1, AUC, Brier) pada baris yang sama, interval bootstrap kluster (default provinsi).

    Prediksi maju hanya punya 1–8 origin, jadi bootstrap origin tidak informatif; bootstrap provinsi mengabaikan korelasi waktu dan
    korelasi antarprovinsi dalam satu origin → interval bersifat deskriptif (lebih sempit dari ketidakpastian sebenarnya).
    """
    m = a.merge(b[["origin", "horizon", "province_id", "commodity", "p_up"]], on=["origin", "horizon", "province_id", "commodity"],
                suffixes=("_a", "_b"))
    m = m[np.isfinite(m["y"]) & (m["y"] != 0)].reset_index(drop=True)
    up = m["y"].to_numpy() > 0
    pa, pb = m["p_up_a"].to_numpy(float), m["p_up_b"].to_numpy(float)

    def stat(ix):
        ca, cb = confusion(up[ix], pa[ix] > 0.5), confusion(up[ix], pb[ix] > 0.5)
        return (class_stats(ca)["macro_f1"] - class_stats(cb)["macro_f1"], auc(up[ix], pa[ix]) - auc(up[ix], pb[ix]),
                brier(up[ix], pa[ix]) - brier(up[ix], pb[ix]))

    full = stat(np.arange(len(m)))
    groups = m.groupby(cluster).indices
    keys = list(groups)
    rng = np.random.default_rng(seed)
    boot = np.full((reps, 3), np.nan)
    for r in range(reps):
        pick = rng.integers(0, len(keys), len(keys))
        ix = np.concatenate([groups[keys[j]] for j in pick])
        boot[r] = stat(ix)
    lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
    return {"n": int(len(m)), "n_origins": int(m["origin"].nunique()), "n_clusters": len(keys),
            "d_macro_f1": full[0], "d_macro_f1_lo": lo[0], "d_macro_f1_hi": hi[0],
            "d_auc": full[1], "d_auc_lo": lo[1], "d_auc_hi": hi[1],
            "d_brier": full[2], "d_brier_lo": lo[2], "d_brier_hi": hi[2],
            "flip_share": float(((pa > 0.5) != (pb > 0.5)).mean())}


def target_ready(origin, h, last_date):
    """Target lengkap bila snapshot memuat Jumat minggu origin + h (aturan D-152 fw_eval.py)."""
    return pd.Timestamp(origin) + pd.Timedelta(weeks=h) + pd.Timedelta(days=4) <= pd.Timestamp(last_date)
