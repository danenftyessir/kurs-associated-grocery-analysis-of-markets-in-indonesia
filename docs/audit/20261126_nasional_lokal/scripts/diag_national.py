"""D-158 diagnosis kelemahan iterasi 1 (origin pengembangan, prediksi resmi C1t; tanpa model baru).

Dekomposisi macro F1 per horizon:
  C1t                       : prediksi baris resmi (p > 0,5)
  mayoritas_c1t             : setiap provinsi = arah mayoritas tersirat C1t (rerata p_up lintas provinsi > 0,5) → nilai komponen nasional C1t
  mayoritas_benar_LOO       : setiap provinsi = arah mayoritas realisasi provinsi LAIN (oracle) → nilai komponen nasional sempurna
  C1t_dikoreksi_oracle      : C1t dengan arah mayoritas realisasi menggantikan baris yang bertentangan hanya bila |p − 0,5| < q
Juga: porsi baris yang searah mayoritas realisasi (homogenitas), akurasi arah nasional C1t tersirat per komoditas & tahun,
dan korelasi antara kesalahan arah nasional C1t dengan |rerata p − 0,5| (kepercayaan). → hasil/diag_national.csv, diag_national_comm.csv
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import H, mf1, np, official_c1t, pd  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
P = official_c1t("dev")
P = P[P["y_true"] != 0].copy()
rows, crow = [], []
for h in H:
    d = P[P["horizon"] == h].copy()
    d["up"] = (d["y_true"] > 0).astype(int)
    g = d.groupby(["origin", "commodity"])
    d["c1t_nat"] = g["score"].transform("mean")
    s_up, n = g["up"].transform("sum"), g["up"].transform("count")
    d["loo_share"] = (s_up - d["up"]) / (n - 1).where(n > 1)
    d["maj_true"] = (d["loo_share"] > 0.5).astype(float)
    d.loc[d["loo_share"] == 0.5, "maj_true"] = (d["score"] > 0.5).astype(float)
    d["maj_c1t"] = (d["c1t_nat"] > 0.5).astype(float)
    base = mf1(d["y_true"], d["score"])
    res = {"horizon": h, "C1t": base, "mayoritas_c1t": mf1(d["y_true"], d["maj_c1t"]), "mayoritas_benar_LOO": mf1(d["y_true"], d["maj_true"]),
           "homogenitas_searah_mayoritas": float((d["up"] == d["maj_true"]).mean()),
           "akurasi_arah_nasional_c1t": float((d.drop_duplicates(["origin", "commodity"]).pipe(lambda x: (x["c1t_nat"] > 0.5) == (g["up"].mean().reindex(pd.MultiIndex.from_frame(x[["origin", "commodity"]])).to_numpy() > 0.5))).mean()),
           "porsi_baris_c1t_beda_dengan_mayoritas_c1t": float(((d["score"] > 0.5) != (d["maj_c1t"] > 0.5)).mean())}
    for q in (0.05, 0.1, 0.2):
        fix = np.where((d["score"] - 0.5).abs() < q, d["maj_true"], (d["score"] > 0.5).astype(float))
        res[f"C1t_oracle_mayoritas_bila_ragu_{q}"] = mf1(d["y_true"], fix)
    rows.append(res)
    # per komoditas & tahun: akurasi arah nasional C1t tersirat
    nat = g.agg(share=("up", "mean"), c1t_nat=("score", "mean")).reset_index()
    nat["z"], nat["zhat"] = nat["share"] > 0.5, nat["c1t_nat"] > 0.5
    nat["year"] = nat["origin"].dt.year
    nat["conf"] = (nat["c1t_nat"] - 0.5).abs()
    for c, x in nat.groupby("commodity"):
        crow.append({"horizon": h, "commodity": c, "acc_nasional": (x["z"] == x["zhat"]).mean(), "share_up_mean": x["share"].mean(),
                     "konsensus_mean": (x["share"] - 0.5).abs().mean() * 2})
    crow.append({"horizon": h, "commodity": "SEMUA", "acc_nasional": (nat["z"] == nat["zhat"]).mean(),
                 "acc_nasional_conf_atas": (nat[nat["conf"] > nat["conf"].median()]["z"] == nat[nat["conf"] > nat["conf"].median()]["zhat"]).mean(),
                 "acc_nasional_conf_bawah": (nat[nat["conf"] <= nat["conf"].median()]["z"] == nat[nat["conf"] <= nat["conf"].median()]["zhat"]).mean(),
                 **{f"acc_{y}": (x["z"] == x["zhat"]).mean() for y, x in nat.groupby("year")}})
pd.DataFrame(rows).round(4).to_csv(os.path.join(OUT, "diag_national.csv"), index=False)
pd.DataFrame(crow).round(4).to_csv(os.path.join(OUT, "diag_national_comm.csv"), index=False)
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(4).T.to_string())
print(pd.DataFrame(crow).round(3).to_string(index=False))
