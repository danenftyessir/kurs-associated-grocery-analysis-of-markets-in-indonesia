# Pemakaian: KAGAMI_EXP=<folder exp sesi K4> python k4_refreeze_check.py <root>/docs/audit/20261126_k4_risiko_material/scripts <berkas k4_forward_preds.csv>
# Baca-saja: tidak menulis ke hasil/; hasil 2026-11-27: sha256 ulang = berkas = eb1f10db... (lihat INITIAL_AUDIT.md §2.3).
"""Verifikasi baca-saja: jalankan ulang logika k4_freeze.py ke memori (tanpa menulis ke hasil/), bandingkan dengan file beku."""
import hashlib, io, os, sys
sys.path.insert(0, sys.argv[1])
import k4_freeze as KF  # hanya konstanta KEEP; blok __main__ tidak jalan
from k4_common import EXP, H, pd, platt_walkforward
F = pd.read_parquet(os.path.join(EXP, "k4_forward_preds.parquet")).assign(part="forward")
hist = [pd.read_parquet(os.path.join(EXP, f"k4_{p}_preds.parquet")).assign(part=p) for p in ("dev", "test")]
out = []
for h in H:
    f = F[F["horizon"] == h]
    d = pd.concat([x[x["horizon"] == h] for x in hist] + [f], ignore_index=True).sort_values(["origin", "province_id", "commodity"]).reset_index(drop=True)
    d["k4_e80_cal"] = platt_walkforward(d, "k4_e80", "z_e80", h)
    d["k4_a80_cal"] = platt_walkforward(d, "k4_a80", "z_a80", h)
    d["c1t_cal"] = platt_walkforward(d, "c1t", "z_e80", h)
    out.append(d[d["part"] == "forward"])
F = pd.concat(out, ignore_index=True)
cols = KF.KEEP + ["k4_e80_cal", "k4_a80_cal", "c1t_cal"]
buf = io.StringIO()
F[cols].sort_values(["horizon", "origin", "province_id", "commodity"]).round(6).to_csv(buf, index=False, lineterminator="\n")
sha = hashlib.sha256(buf.getvalue().encode()).hexdigest()
print("sha256 ulang :", sha)
print("sha256 berkas:", hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest())
