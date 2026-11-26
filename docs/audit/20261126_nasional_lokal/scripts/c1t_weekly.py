"""D-158 infrastruktur iterasi 2: prediksi C1-tuned mingguan OUT-OF-SAMPLE 2019-01 .. 2023-12.

Refit r tiap 4 minggu pada grid origin resmi (2021-01-04 − 26 × 4 minggu = 2019-01-07); model r = C1t (kolom, TUNED_HGB, seed resmi)
dilatih pada baris t + h ≤ r (split resmi) dan memprediksi minggu t ∈ [r, r + 4) untuk semua seri dengan lag lengkap. Pada minggu origin
resmi prediksi = `direction_tuned_preds` C1t (dicek). → EXP/c1t_weekly.parquet (week, province_id, commodity, horizon, p_up)."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import EXP, H, cfg, np, official_c1t, pd, table  # noqa: E402
from m_run import fit_predict  # noqa: E402
from kagami.features.forecast import LAG_COLUMNS, split_origin  # noqa: E402
from kagami.models.direction import tuned_columns  # noqa: E402

START, END = pd.Timestamp("2019-01-07"), pd.Timestamp("2023-12-31")


def one(h, r):
    tab = table()
    train, _ = split_origin(cfg, tab, r, h)
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    te = tab[(tab["week"] >= r) & (tab["week"] < r + pd.Timedelta(weeks=4))].dropna(subset=LAG_COLUMNS)
    p = fit_predict(tr, te, {"cols": tuned_columns("C1t", h)[0]}, r)
    return te[["week", "province_id", "commodity"]].assign(horizon=h, p_up=p, refit=r)


if __name__ == "__main__":
    from joblib import Parallel, delayed
    t0 = time.time()
    refits = list(pd.date_range(START, END, freq="4W-MON"))
    res = Parallel(n_jobs=int(os.environ.get("NJ", 5)), verbose=2)(delayed(one)(h, r) for h in H for r in refits)
    W = pd.concat(res, ignore_index=True)
    W.to_parquet(os.path.join(EXP, "c1t_weekly.parquet"))
    off = official_c1t("dev").rename(columns={"origin": "week"})
    chk = W.merge(off, on=["week", "horizon", "province_id", "commodity"])
    print("refit", len(refits), "baris", len(W), "| cek vs resmi:", len(chk), "baris, maks |Δp|", float(np.abs(chk["p_up"] - chk["score"]).max()),
          round(time.time() - t0), "dtk")
