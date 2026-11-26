"""K4 PROTOCOL §6 — bekukan prediksi maju (origin dengan target belum terealisasi) + manifest sha256.

Membaca EXP/k4_forward_preds.parquet (k4_run.py PART=forward). Bila prediksi test ada, peluang terkalibrasi walk-forward (Platt global)
untuk origin maju dilatih pada semua prediksi OOS dev + test yang targetnya sudah terealisasi sebelum origin itu.
Keluaran hasil/k4_forward_preds.csv (kolom inti, target kosong) + hasil/k4_forward_manifest.json.
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k4_common import EXP, H, OUT, np, pd, platt_walkforward  # noqa: E402

KEEP = ["origin", "horizon", "province_id", "commodity", "region", "thr_e80", "c1t", "k4_e80", "k4_a80", "clim_e80", "clims_e80",
        "clims_a80"]

if __name__ == "__main__":
    F = pd.read_parquet(os.path.join(EXP, "k4_forward_preds.parquet")).assign(part="forward")
    hist = [pd.read_parquet(os.path.join(EXP, f"k4_{p}_preds.parquet")).assign(part=p) for p in ("dev", "test")
            if os.path.exists(os.path.join(EXP, f"k4_{p}_preds.parquet"))]
    out = []
    for h in H:
        f = F[F["horizon"] == h]
        d = pd.concat([x[x["horizon"] == h] for x in hist] + [f], ignore_index=True).sort_values(["origin", "province_id", "commodity"])
        d = d.reset_index(drop=True)
        d["k4_e80_cal"] = platt_walkforward(d, "k4_e80", "z_e80", h)
        d["k4_a80_cal"] = platt_walkforward(d, "k4_a80", "z_a80", h)
        d["c1t_cal"] = platt_walkforward(d, "c1t", "z_e80", h)
        out.append(d[d["part"] == "forward"])
    F = pd.concat(out, ignore_index=True)
    assert not F["has_target"].any(), "origin maju harus tanpa target terealisasi"
    cols = KEEP + ["k4_e80_cal", "k4_a80_cal", "c1t_cal"]
    csv = os.path.join(OUT, "k4_forward_preds.csv")
    F[cols].sort_values(["horizon", "origin", "province_id", "commodity"]).round(6).to_csv(csv, index=False, lineterminator="\n")
    sha = hashlib.sha256(open(csv, "rb").read()).hexdigest()
    last = pd.Timestamp(F["origin"].max())
    man = {"frozen_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "file": "hasil/k4_forward_preds.csv", "sha256": sha, "n_rows": int(len(F)),
           "origins": {int(h): [str(o.date()) for o in sorted(F.loc[F["horizon"] == h, "origin"].unique())] for h in H},
           "last_data_week": str(last.date()),
           "target_complete_by": str((last + pd.Timedelta(weeks=max(H)) + pd.Timedelta(days=4)).date()),
           "calibration_history": [x["part"].iloc[0] for x in hist],
           "note": "Peluang K4 mentah & terkalibrasi walk-forward; target z_e80 / z_a80 dinilai sesudah minggu t + h teramati, "
                   "ambang thr_e80 dibekukan di file ini. Konfirmasi prospektif hanya dari file ini (PROTOCOL §6)."}
    json.dump(man, open(os.path.join(OUT, "k4_forward_manifest.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(man, indent=1))
