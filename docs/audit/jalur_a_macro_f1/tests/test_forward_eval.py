"""Tes Jalur A Workstream A (evaluator prediksi maju) pada data sintetis. Jalankan:
    python -m pytest -q docs/audit/jalur_a_macro_f1/tests
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import fw_common as C  # noqa: E402
from a_forward_eval import evaluate  # noqa: E402


def _synth(n_origin=2, n_prov=34, comms=("beras", "cabai_merah"), h=4, seed=0, complete=True):
    rng = np.random.default_rng(seed)
    rows = []
    for o in pd.date_range("2026-10-05", periods=n_origin, freq="7D"):
        for p in range(1, n_prov + 1):
            for c in comms:
                y = rng.normal(0, 0.05)
                if rng.random() < 0.1:
                    y = 0.0
                pb = 1 / (1 + np.exp(-8 * y + rng.normal(0, 1)))
                for m, pu in (("base", pb), ("IW_NAT", pb), ("FR_REF", np.clip(pb + 0.2, 0, 1)), ("FR_CITY", 1 - pb)):
                    rows.append({"origin": o, "horizon": h, "model": m, "province_id": p, "commodity": c, "p_up": pu, "y": y,
                                 "complete": complete})
    return pd.DataFrame(rows)


def test_metrics_match_sklearn():
    from sklearn.metrics import brier_score_loss, f1_score, matthews_corrcoef, roc_auc_score
    rng = np.random.default_rng(1)
    y = rng.normal(size=500)
    y[:20] = 0
    p = rng.random(500)
    st = C.metrics(pd.DataFrame({"y": y, "p_up": p}))
    nz = y != 0
    up, pu = y[nz] > 0, p[nz] > 0.5
    assert st["n"] == nz.sum()
    assert st["macro_f1"] == pytest.approx(f1_score(up, pu, average="macro"))
    assert st["mcc"] == pytest.approx(matthews_corrcoef(up, pu))
    assert st["roc_auc"] == pytest.approx(roc_auc_score(up, p[nz]))
    assert st["brier"] == pytest.approx(brier_score_loss(up, p[nz]))


def test_auc_ties_and_ece():
    assert C.auc([1, 0, 1, 0], [0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.5)
    assert np.isnan(C.auc([1, 1], [0.2, 0.3]))
    # bin 0,9 berisi 10 prediksi 0,95 dengan 9 benar → |0,95 − 0,9| = 0,05; bin 0,0 berisi 10 prediksi 0,05 dengan 0 benar → 0,05
    y = np.r_[np.ones(9), 0, np.zeros(10)]
    p = np.r_[np.full(10, 0.95), np.full(10, 0.05)]
    assert C.ece(y, p) == pytest.approx(0.05)


def test_paired_identical_is_zero():
    d = _synth()
    a = d[d["model"] == "IW_NAT"]
    b = d[d["model"] == "base"]
    pr = C.paired(a, b, reps=99)
    assert pr["d_macro_f1"] == 0 and pr["d_auc"] == 0 and pr["d_brier"] == 0 and pr["flip_share"] == 0
    assert pr["n_clusters"] == 34


def test_evaluate_flags_and_filters():
    d = _synth()
    met, pai = evaluate(d)
    assert set(met["model"]) == {"base", "IW_NAT", "FR_REF", "FR_CITY"}
    n_nz = int(((d["model"] == "base") & (d["y"] != 0)).sum())
    assert int(met.loc[met["model"] == "base", "n"].iloc[0]) == n_nz        # y = 0 dikeluarkan
    f = pai.set_index("model")["flag"]
    assert f["IW_NAT"] == "KONSISTEN"                                        # identik dengan base
    assert f["FR_CITY"] == "GAGAL_MAJU"                                      # skor dibalik → jauh lebih buruk
    # target belum lengkap → ditolak
    with pytest.raises(SystemExit):
        evaluate(_synth(complete=False))


def test_evaluate_ignores_incomplete_rows():
    d = _synth(n_origin=2)
    first = d["origin"].min()
    d.loc[d["origin"] == first, "complete"] = False
    met, _ = evaluate(d)
    assert (met["n_origins"] == 1).all()


def test_load_frozen_detects_tamper(tmp_path, monkeypatch):
    import json
    d = _synth(n_origin=1)
    src = d[d["model"].isin(["base", "IW_NAT"])].drop(columns=["y", "complete"])
    src2 = d[d["model"].isin(["base", "FR_REF", "FR_CITY"])].drop(columns=["y", "complete"])
    frozen = {}
    for name, df in (("D-152", src), ("D-158", src2)):
        p = tmp_path / f"{name}.csv"
        df.to_csv(p, index=False)
        man = tmp_path / f"{name}.json"
        json.dump({"forward_preds_sha256": C.sha256(p)}, open(man, "w"))
        frozen[name] = {"preds": str(p), "manifest": str(man), "models": []}
    monkeypatch.setattr(C, "FROZEN", frozen)
    out = C.load_frozen()
    assert (out["model"] == "base").sum() == (src["model"] == "base").sum()      # base satu salinan
    with open(frozen["D-158"]["preds"], "a") as f:
        f.write("2026-10-05,4,FR_REF,1,beras,0.5\n")
    with pytest.raises(SystemExit):
        C.load_frozen()


def test_target_ready_rule():
    assert not C.target_ready("2026-10-26", 4, "2026-11-26")
    assert C.target_ready("2026-10-26", 4, "2026-11-27")
    assert not C.target_ready("2026-09-28", 8, "2026-11-26")
