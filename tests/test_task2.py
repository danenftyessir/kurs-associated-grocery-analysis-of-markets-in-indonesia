"""Task 2 end-to-end pada artefak sintetis (profil provinsi dummy dengan 3 kelompok tertanam)."""

import numpy as np
import pandas as pd
import pytest

from kagami.features.response import response_features, shrink_deviations
from kagami.features.clustering import feature_columns
from kagami.pipelines import task2
from kagami.utils.config import Config
from kagami.utils.io import read_artifact, write_artifact

HS = (4, 8, 12)


def _profiles(cfg, rng, truth, groups_shift, se=0.05, rep=None):
    rows = []
    for com in cfg.commodity_ids("focus"):
        drivers = ["e"] + (["w"] if cfg.commodities[com]["pinksheet"] else [])
        for drv in drivers:
            for h in HS:
                shift = groups_shift[(com, drv, h)]
                est = shift[truth] + rng.normal(0, se, 34)
                est = est - est.mean()
                for u in range(34):
                    row = {"level": "province", "unit": str(u + 1), "commodity": com, "driver": drv, "horizon": h,
                           "estimate": float(est[u]), "se": se, "ci_low": est[u] - 1.96 * se,
                           "ci_high": est[u] + 1.96 * se,
                           "n_weeks": 400, "shrunk": False}
                    rows.append({**row, "rep": rep} if rep is not None else row)
    return pd.DataFrame(rows)


def _national(cfg):
    rows = []
    for com in cfg.commodity_ids("focus"):
        for drv in ["e", "w", "PT"]:
            for h in range(13):
                rows.append({"level": "national", "unit": "ALL", "commodity": com, "driver": drv, "horizon": h,
                             "estimate": 0.05 * h, "se": 0.02, "ci_low": 0.05 * h - 0.04, "ci_high": 0.05 * h + 0.04,
                             "n_weeks": 450, "shrunk": False})
    return pd.DataFrame(rows)


@pytest.mark.parametrize("structure", ["planted", "none"])
def test_task2_run(cfg, tmp_path, monkeypatch, structure):
    c = Config(root=cfg.root, out_root=tmp_path)
    monkeypatch.setitem(c.params["clustering"], "planted_reps", 6)
    monkeypatch.setitem(c.params["clustering"], "planted_deltas", [0.3, 0.5])
    rng = np.random.default_rng(1)          # tanpa struktur pun ± 5% seed memberi positif palsu (ambang p95)
    truth = np.arange(34) % 3
    keys = [(c, "e" if p == "R" else "w", h) for p, c, h in feature_columns(cfg)]
    sep = 1.0 if structure == "planted" else 0.0
    shift = {k: sep * rng.normal(0, 1, 3) for k in keys}
    prof = shrink_deviations(cfg, pd.concat([_national(cfg), _profiles(cfg, rng, truth, shift)], ignore_index=True))
    write_artifact(c, "profiles", prof)
    write_artifact(c, "response_features", response_features(cfg, prof))
    zero = {k: np.zeros(3) for k in keys}
    placebo = pd.concat([_profiles(cfg, rng, rng.integers(0, 3, 34), zero, rep=r) for r in range(60)])
    boot = pd.concat([_profiles(cfg, rng, truth, shift, rep=r) for r in range(6)])
    for df in (placebo, boot):
        df["unit"] = df["unit"].astype(str)
    write_artifact(c, "placebo_stats", placebo.drop(columns=["ci_low", "ci_high", "n_weeks", "shrunk"]))
    write_artifact(c, "boot_replicates", boot.drop(columns=["ci_low", "ci_high", "n_weeks", "shrunk"]))
    task2.run(c)

    sel = read_artifact(c, "cluster_selection")
    clusters, coassign = read_artifact(c, "clusters"), read_artifact(c, "coassign")
    ward = clusters[clusters["method"] == "ward"].set_index("province_id")
    km = clusters[clusters["method"] == "kmeans"]
    assert set(clusters["method"]) == {"ward", "kmeans"} and len(ward) == 34 and len(km) == 34
    assert len(coassign) == 34 * 34 and "ari_kmeans" in clusters
    assert {"partition", "ari", "n_groups"} <= set(read_artifact(c, "partition_compare").columns)
    rec = read_artifact(c, "planted_recovery")
    assert set(rec["k_true"]) == {2, 3} and set(rec["delta"]) == {0.3, 0.5}
    if structure == "planted":
        assert sel["accepted"].any() and not bool(sel.set_index("k").loc[1, "accepted"])
        from sklearn.metrics import adjusted_rand_score
        lab = ward.loc[range(1, 35), "cluster"]
        assert adjusted_rand_score(truth, lab) > 0.9 and not ward["weak"].any()
    else:
        assert bool(sel.set_index("k").loc[1, "accepted"]) and ward["cluster"].nunique() == 1
