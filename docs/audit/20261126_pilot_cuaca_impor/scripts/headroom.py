"""D-157 §0: ukuran ruang perbaikan (origin dev, prediksi resmi C1t). (a) informasi nasional sempurna per komoditas × origin: threshold
terbaik dari provinsi LAIN pada origin & komoditas sama (leave-one-out) → batas atas sinyal guncangan nasional apa pun; (b) dampak
macro F1 keseluruhan bila akurasi satu kelompok komoditas naik 5 / 10 poin (perbaikan acak prediksi salah, seed tetap).
Keluaran hasil/headroom.csv."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
from m_common import mf1, np, official_c1t, pd  # noqa: E402

GRP = {"cabai_merah": "hortikultura", "cabai_rawit": "hortikultura", "bawang_merah": "hortikultura", "beras": "beras",
       "bawang_putih": "impor", "gula_pasir": "impor", "daging_sapi": "impor", "daging_ayam": "pakan", "telur_ayam": "pakan",
       "minyak_goreng": "sawit"}
GRID = np.round(np.arange(0.2, 0.801, 0.01), 2)
P = official_c1t("dev")
P = P[P["y_true"] != 0].copy()
P["grp"] = P["commodity"].map(GRP)
rows = []
rng = np.random.default_rng(1)
for h in (4, 8):
    d = P[P["horizon"] == h].reset_index(drop=True)
    base = mf1(d["y_true"], d["score"])
    up, s = (d["y_true"] > 0).to_numpy(), d["score"].to_numpy()
    pred = np.zeros(len(d), bool)
    for _, idx in d.groupby(["origin", "commodity"]).indices.items():
        C = (s[idx][:, None] > GRID[None, :]) == up[idx][:, None]
        tot = C.sum(0)
        for j, i in enumerate(idx):
            sc = tot - C[j]
            best = GRID[sc >= sc.max()]
            pred[i] = s[i] > best[np.argmin(np.abs(best - 0.5))]
    rows.append({"horizon": h, "measure": "info_nasional_sempurna_semua", "group": "semua", "delta": mf1(d["y_true"], pred.astype(float)) - base})
    for g in ("hortikultura", "impor", "pakan", "beras", "sawit"):
        m = (d["grp"] == g).to_numpy()
        p3 = np.where(m, pred, s > 0.5).astype(float)
        rows.append({"horizon": h, "measure": "info_nasional_sempurna_satu_grup", "group": g, "delta": mf1(d["y_true"], p3) - base,
                     "share_rows": m.mean()})
        for gain in (0.05, 0.10):
            pr = s > 0.5
            wrong = np.where(m & (pr != up))[0]
            fix = rng.choice(wrong, min(int(gain * m.sum()), len(wrong)), replace=False)
            p2 = pr.copy()
            p2[fix] = up[fix]
            rows.append({"horizon": h, "measure": f"akurasi_grup_+{int(gain * 100)}poin", "group": g,
                         "delta": mf1(d["y_true"], p2.astype(float)) - base, "share_rows": m.mean()})
t = pd.DataFrame(rows)
t.round(4).to_csv(os.path.join(HERE, "..", "hasil", "headroom.csv"), index=False)
print(t.round(4).to_string(index=False))
