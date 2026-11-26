"""Jalur A Workstream A: evaluasi gabungan prediksi maju beku (D-152 + D-158) SETELAH target terealisasi. Dibekukan sebelum target
pertama lengkap (Jumat 2026-11-27); hash skrip ini dicatat di hasil/a_protocol_sha256.txt.

Pemakaian:
  python a_forward_eval.py --pihps-zip <snapshot PIHPS baru>   # format `pihps` (zip 34 CSV, sama dengan pengambilan D-150/D-151)

Aturan (tidak boleh diubah sesudah target terlihat):
- Prediksi tidak diubah dan tidak dilatih ulang; sha256 prediksi & skrip label D-152 diverifikasi terhadap manifest (gagal → berhenti).
- Label = `fw_eval.labels` D-152 (beku): tanda log rerata hari teramati minggu t+h − minggu t dari snapshot baru, agregasi resmi,
  y = 0 dikeluarkan; target dipakai hanya bila snapshot memuat Jumat minggu t+h.
- Model: base (= C1-tuned), IW_NAT (kandidat D-152), FR_REF (acuan D-158, ≈ IW_NAT), FR_CITY (diagnostik D-158).
- Metrik per horizon & model: macro F1, F1/presisi/recall naik & turun, MCC, ROC-AUC, Brier, ECE (10 bin), porsi naik aktual/prediksi,
  macro F1 kuintil |y| terkecil (ambang dari base). Selisih vs base: macro F1, AUC, Brier dengan interval bootstrap kluster provinsi
  (deskriptif; 1–8 origin → tidak ada inferensi waktu). D-152 menghitung MDE batch maju 0,08–0,12 (h 4) / 0,04–0,06 (h 8):
  hasil hanya dapat menandai KEGAGALAN BESAR (Δ macro F1 < −MDE), bukan mengonfirmasi keuntungan +0,0085 / +0,0033.
- Penanda kegagalan besar (ditetapkan sebelum hasil): kandidat ditandai GAGAL_MAJU bila Δ macro F1 vs base < −0,08 (h 4) atau < −0,04
  (h 8) pada gabungan origin yang tersedia horizon itu. Selain itu: KONSISTEN (Δ ≥ 0) atau TIDAK_TERBUKTI (−MDE ≤ Δ < 0).
→ hasil/a_forward_eval_<tanggal data terakhir>_{metrics,paired}.csv
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fw_common import AUD, FROZEN, OUT, load_frozen, metrics, np, paired, pd, sha256  # noqa: E402

FAIL_MDE = {4: 0.08, 8: 0.04}


def evaluate(d):
    """d: prediksi beku + y (+ complete). → (metrics, paired) DataFrame. Hanya baris dengan target lengkap & y teramati."""
    d = d[d["complete"].fillna(False).astype(bool) & np.isfinite(d["y"])]
    if d.empty:
        raise SystemExit("belum ada target lengkap pada snapshot ini — evaluasi ditunda")
    rows, pairs = [], []
    for h, dh in d.groupby("horizon"):
        b = dh[dh["model"] == "base"]
        thr = b.loc[b["y"] != 0, "y"].abs().quantile(0.2)
        for m, x in dh.groupby("model"):
            sm = x[(x["y"] != 0) & (x["y"].abs() <= thr)]
            rows.append({"horizon": int(h), "model": m, "n_origins": int(x["origin"].nunique()), **metrics(x),
                         "macro_f1_q1_small": metrics(sm)["macro_f1"] if len(sm) else np.nan})
        for m in ["IW_NAT", "FR_REF", "FR_CITY"]:
            a = dh[dh["model"] == m]
            if a.empty:
                continue
            pr = paired(a, b)
            dlt = pr["d_macro_f1"]
            pr["flag"] = "GAGAL_MAJU" if dlt < -FAIL_MDE[int(h)] else ("KONSISTEN" if dlt >= 0 else "TIDAK_TERBUKTI")
            pairs.append({"horizon": int(h), "model": m, "vs": "base", **pr})
    return pd.DataFrame(rows), pd.DataFrame(pairs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pihps-zip", required=True)
    a = ap.parse_args()
    man = json.load(open(FROZEN["D-152"]["manifest"], encoding="utf-8"))
    lab_path = os.path.join(AUD, "20261125_iw_validasi", "scripts", "fw_eval.py")
    key = "docs/audit/20261125_iw_validasi/scripts/fw_eval.py"
    if sha256(lab_path) != man["code_sha256"][key]:
        raise SystemExit("fw_eval.py (definisi label D-152) berubah sejak pembekuan — berhenti")
    sys.path.insert(0, os.path.dirname(lab_path))
    from fw_eval import labels  # noqa: E402
    preds = load_frozen(verify=True)
    y, last = labels(a.pihps_zip)
    d = preds.merge(y, on=["origin", "province_id", "commodity", "horizon"], how="left")
    print(f"data terakhir {last.date()}; baris bertarget lengkap {int((d['complete'].fillna(False) & np.isfinite(d['y'])).sum())} dari {len(preds)}")
    met, pai = evaluate(d)
    pd.set_option("display.width", 220)
    print(met.round(4).to_string(index=False))
    print(pai.round(4).to_string(index=False))
    tag = last.date()
    met.to_csv(os.path.join(OUT, f"a_forward_eval_{tag}_metrics.csv"), index=False)
    pai.to_csv(os.path.join(OUT, f"a_forward_eval_{tag}_paired.csv"), index=False)
