"""WP-36 (D-137): log eksekusi & evaluasi terpusat.

- metrik berpenjaga = rumus numpy independen; syarat tak terpenuhi → not_applicable + alasan (tidak ada nilai karangan)
- logger: run sukses/gagal tercatat, galat dilempar ulang, log tidak pernah ditimpa, panggilan bertingkat = satu run,
  pipeline_id bersama, run induk dari hash input, hasil basi bila input berubah, pencatatan bisa dimatikan
- evaluator pada artefak asli (di-skip bila tidak ada): cek integritas silhouette & MAE dihitung ulang
- halaman app 7 terender dengan log sintetis
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from kagami.tracking import assessment, evaluators, lineage, logger, registry, store
from kagami.tracking.metrics import (clustering_metrics, direction_bootstrap, direction_metrics,
                                     direction_segment_table, feature_health, interval_consistency,
                                     regression_metrics)
from kagami.tracking.schemas import Metric
from kagami.utils.config import Config
from kagami.utils.io import read_artifact, write_artifact

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def _m(ms: list[Metric]) -> dict[str, Metric]:
    return {m.name: m for m in ms}


# --------------------------------------------------------------------------- metrik vs rumus independen
def _blobs(seed=0):
    rng = np.random.default_rng(seed)
    X = np.vstack([rng.normal(0, 1, (12, 3)), rng.normal(6, 1, (10, 3)), rng.normal(-6, 1, (8, 3))])
    lab = np.repeat([0, 1, 2], [12, 10, 8])
    return X, lab


def _silhouette_manual(X, lab):
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    s = []
    for i in range(len(X)):
        same = lab == lab[i]
        if same.sum() == 1:
            s.append(0.0)
            continue
        a = D[i, same & (np.arange(len(X)) != i)].mean()
        b = min(D[i, lab == c].mean() for c in np.unique(lab) if c != lab[i])
        s.append((b - a) / max(a, b))
    return float(np.mean(s))


def _db_ch_manual(X, lab):
    ks = np.unique(lab)
    C = np.vstack([X[lab == k].mean(0) for k in ks])
    S = np.array([np.sqrt(((X[lab == k] - C[i]) ** 2).sum(1)).mean() for i, k in enumerate(ks)])
    M = np.sqrt(((C[:, None] - C[None]) ** 2).sum(-1))
    db = np.mean([max((S[i] + S[j]) / M[i, j] for j in range(len(ks)) if j != i) for i in range(len(ks))])
    g = X.mean(0)
    B = sum((lab == k).sum() * ((C[i] - g) ** 2).sum() for i, k in enumerate(ks))
    W = sum(((X[lab == k] - C[i]) ** 2).sum() for i, k in enumerate(ks))
    n, k = len(X), len(ks)
    return float(db), float(B / (k - 1) / (W / (n - k))), float(W)


def test_clustering_metrics_match_manual_formulas():
    X, lab = _blobs()
    m = _m(clustering_metrics(X, lab))
    db, ch, wcss = _db_ch_manual(X, lab)
    assert m["silhouette"].value == pytest.approx(_silhouette_manual(X, lab), rel=1e-10)
    assert m["davies_bouldin"].value == pytest.approx(db, rel=1e-10)
    assert m["calinski_harabasz"].value == pytest.approx(ch, rel=1e-10)
    assert m["wcss"].value == pytest.approx(wcss, rel=1e-10)
    assert m["n_clusters"].value == 3 and m["cluster_sizes"].value == [12, 10, 8]
    assert m["silhouette"].context["n_samples"] == 30


def test_clustering_metrics_guards():
    X, _ = _blobs()
    one = _m(clustering_metrics(X, np.zeros(len(X), int)))
    for name in ("silhouette", "davies_bouldin", "calinski_harabasz"):
        assert one[name].status == "not_applicable" and "k = 1" in one[name].reason and one[name].value is None
    assert one["wcss"].value == pytest.approx(((X - X.mean(0)) ** 2).sum())     # k = 1: WCSS = total SS
    each = _m(clustering_metrics(X, np.arange(len(X))))
    assert each["silhouette"].status == "not_applicable" and "jumlah sampel" in each["silhouette"].reason
    Xn = X.copy()
    Xn[0, 0] = np.nan
    bad = _m(clustering_metrics(Xn, _blobs()[1]))
    assert bad["silhouette"].status == "failed" and "NaN" in bad["silhouette"].reason


def _auc_manual(pos, score):
    """ROC-AUC = P(skor positif > skor negatif) (Mann–Whitney), seri = 1/2."""
    sp, sn = score[pos], score[~pos]
    return float(((sp[:, None] > sn[None, :]).sum() + 0.5 * (sp[:, None] == sn[None, :]).sum()) / (len(sp) * len(sn)))


def _ap_manual(pos, score):
    """Average precision = Σ (R_k − R_{k−1}) · P_k, urut skor menurun (tanpa seri)."""
    o = np.argsort(-score)
    hit = pos[o]
    tp = np.cumsum(hit)
    prec = tp / np.arange(1, len(hit) + 1)
    return float((prec * hit).sum() / hit.sum())


def test_direction_metrics_match_manual_formulas():
    """D-139: diagnostik arah = rumus confusion manual, AUC Mann–Whitney, AP manual; y_true = 0 dikeluarkan."""
    rng = np.random.default_rng(7)
    y = rng.normal(0.01, 0.05, 400)
    p = 0.4 * y + rng.normal(0, 0.04, 400)
    y[:30] = 0.0                                           # harga tidak berubah → dikeluarkan
    m = _m(direction_metrics(y, p, prefix="h4_M2_"))
    yt, yp = y[30:], p[30:]
    up, pu = yt > 0, yp > 0
    tp, fn, fp, tn = (up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()
    n = len(yt)
    assert m["h4_M2_dir_accuracy"].value == pytest.approx((tp + tn) / n)
    assert m["h4_M2_dir_majority_baseline_accuracy"].value == pytest.approx(max(up.mean(), 1 - up.mean()))
    assert m["h4_M2_dir_precision_naik"].value == pytest.approx(tp / (tp + fp))
    assert m["h4_M2_dir_recall_naik"].value == pytest.approx(tp / (tp + fn))
    f1u, f1d = 2 * tp / (2 * tp + fp + fn), 2 * tn / (2 * tn + fn + fp)
    assert m["h4_M2_dir_f1_naik"].value == pytest.approx(f1u)
    assert m["h4_M2_dir_f1_turun"].value == pytest.approx(f1d)
    assert m["h4_M2_dir_f1_macro"].value == pytest.approx((f1u + f1d) / 2)
    assert m["h4_M2_dir_balanced_accuracy"].value == pytest.approx((tp / (tp + fn) + tn / (tn + fp)) / 2)
    mcc = (tp * tn - fp * fn) / np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    assert m["h4_M2_dir_mcc"].value == pytest.approx(mcc)
    assert m["h4_M2_dir_roc_auc"].value == pytest.approx(_auc_manual(up, yp))
    assert m["h4_M2_dir_pr_auc"].value == pytest.approx(_ap_manual(up, yp))
    assert m["h4_M2_dir_confusion"].value == [[tp, fn], [fp, tn]]
    ctx = m["h4_M2_dir_accuracy"].context
    assert ctx["n"] == n and ctx["n_no_change_excluded"] == 30 and ctx["n_pred_no_direction_excluded"] == 0
    assert m["h4_M2_dir_accuracy"].value > m["h4_M2_dir_majority_baseline_accuracy"].value   # ada sinyal arah


def test_direction_metrics_guards():
    rng = np.random.default_rng(3)
    y = rng.normal(0, 0.05, 100)
    m0 = _m(direction_metrics(y, np.zeros_like(y)))                     # M0: ramalan nol → tanpa arah
    assert all(v.status == "not_applicable" and "tidak memberi arah" in v.reason for v in m0.values())
    up = _m(direction_metrics(np.abs(y) + 0.01, y))                      # aktual hanya naik
    assert up["dir_accuracy"].status == "ok"
    for k in ("dir_balanced_accuracy", "dir_mcc", "dir_roc_auc", "dir_pr_auc", "dir_recall_turun", "dir_f1_macro"):
        assert up[k].status == "not_applicable", k
    p = y.copy()
    p[:4] = 0.0                                                          # ramalan tanpa arah dikeluarkan & dicatat
    mp = _m(direction_metrics(y, p))
    assert mp["dir_accuracy"].context["n_pred_no_direction_excluded"] == 4 and mp["dir_accuracy"].context["n"] == 96
    assert _m(direction_metrics(y, y[:-1]))["dir_accuracy"].status == "failed"


def test_regression_metrics_match_manual_and_mape_guard():
    rng = np.random.default_rng(1)
    y = rng.normal(0.02, 0.1, 200)
    p = y + rng.normal(0, 0.05, 200)
    m = _m(regression_metrics(y, p))
    e = y - p
    assert m["mae"].value == pytest.approx(np.abs(e).mean())
    assert m["mse"].value == pytest.approx((e ** 2).mean())
    assert m["rmse"].value == pytest.approx(np.sqrt((e ** 2).mean()))
    assert m["r2"].value == pytest.approx(1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum())
    assert m["r2_oos_vs_zero"].value == pytest.approx(1 - (e ** 2).sum() / (y ** 2).sum())
    assert m["mape"].value == pytest.approx(np.mean(np.abs(e / y)) * 100)
    y0 = y.copy()
    y0[:5] = 0.0                                          # harga tidak berubah → selisih log 0
    m0 = _m(regression_metrics(y0, p))
    assert m0["mape"].status == "not_applicable" and "5 dari 200" in m0["mape"].reason
    zero = _m(regression_metrics(y, np.zeros_like(y)))
    assert zero["r2_oos_vs_zero"].value == pytest.approx(0.0)      # ramalan nol = pembanding
    yn = y.copy()
    yn[:3] = np.nan
    mn = _m(regression_metrics(yn, p))
    assert mn["mae"].context["n_dropped_nan"] == 3 and mn["mae"].context["n"] == 197
    assert _m(regression_metrics(y[:1], p[:1]))["mae"].status == "not_applicable"
    assert _m(regression_metrics(y, p[:-1]))["mae"].status == "failed"


def test_interval_consistency_and_metric_contract():
    df = pd.DataFrame({"p_value": [0.01, 0.5, 0.01, 0.3], "ci_low": [0.1, -0.2, -0.1, -0.5],
                       "ci_high": [0.4, 0.3, 0.2, 0.5]})
    m = _m(interval_consistency(df, "g"))
    assert m["p_interval_consistency"].value == pytest.approx(0.75)
    assert m["p_interval_consistency_mismatches"].value == 1
    with pytest.raises(ValueError):
        Metric("x", "g", None, "not_applicable")          # status ≠ ok wajib beralasan


# --------------------------------------------------------------------------- logger & lineage
@pytest.fixture
def tcfg(tmp_path, monkeypatch):
    """Root kode sementara (salinan configs/) agar log & artefak tidak menyentuh folder project."""
    root = tmp_path / "code"
    shutil.copytree(ROOT / "configs", root / "configs")
    shutil.copytree(ROOT / "data" / "reference", root / "data" / "reference")
    monkeypatch.delenv("KAGAMI_TRACKING", raising=False)
    return Config(root=root, out_root=tmp_path / "out", raw_root=tmp_path / "raw")


def _eps(v=0.12):
    return pd.DataFrame({"episode_id": [1], "start_week": ["2020-03-02"], "end_week": ["2020-04-27"], "cum_dlog_e": [v]})


def _fxv(sd=0.008):
    return pd.DataFrame({"period": ["total"], "n_dep_weeks": [10], "n_app_weeks": [8], "mean_dep": [0.004],
                         "mean_app": [-0.003], "sd_de": [sd]})


def _producer(cfg, v=0.12):
    write_artifact(cfg, "episodes", _eps(v))


def _consumer(cfg, scale=1.0):
    e = read_artifact(cfg, "episodes")
    write_artifact(cfg, "fx_variation", _fxv(float(e["cum_dlog_e"].iloc[0]) * scale))


def _forecast_producer(cfg):
    rng = np.random.default_rng(11)
    y = rng.normal(0, 0.05, 120)
    rows = [pd.DataFrame({"origin": pd.Timestamp("2024-01-01"), "horizon": 4, "model": mo, "region": "Jawa",
                          "commodity": "beras", "y_true": y, "y_pred": pred, "large_move": False})
            for mo, pred in (("M0", np.zeros_like(y)), ("M2", 0.5 * y + rng.normal(0, 0.03, 120)))]
    write_artifact(cfg, "forecast_preds", pd.concat(rows, ignore_index=True))


def test_run_success_writes_separate_logs_and_lineage(tcfg):
    logger.run_tracked(tcfg, "stage0", _producer)
    logger.run_tracked(tcfg, "task1", _consumer, scale=2.0)
    runs = store.load_runs(tcfg)
    assert [r.task_id for r in runs] == ["stage0", "task1"]
    prod, cons = runs
    assert prod.status == cons.status == "success" and prod.run_type == "execution"
    assert prod.duration_s is not None and prod.duration_s >= 0
    assert [a.name for a in prod.outputs] == ["episodes"] and prod.outputs[0].rows == 1
    assert [a.name for a in cons.inputs] == ["episodes"]
    assert cons.inputs[0].sha256 == prod.outputs[0].sha256
    assert cons.inputs[0].producer_run_id == prod.run_id and cons.parent_run_ids == [prod.run_id]
    assert cons.call_args == {"scale": 2.0}
    assert "params.yaml" in cons.config_sha256 and cons.params["seed"] == tcfg.seed
    logs = tcfg.out_dir / "logs"
    assert (logs / "runs" / f"{cons.run_id}.json").exists()
    assert (logs / "evaluations" / f"{cons.run_id}.json").exists()           # evaluasi terpisah dari metadata
    assert not (logs / "errors").exists()
    raw = (logs / "runs" / f"{cons.run_id}.json").read_text(encoding="utf-8")
    assert str(tcfg.out_dir) not in raw and str(Path.home()) not in raw       # tanpa path absolut


def test_failed_run_logged_and_reraised(tcfg):
    def boom(cfg):
        write_artifact(cfg, "episodes", _eps())
        raise RuntimeError("galat tertanam")

    with pytest.raises(RuntimeError, match="galat tertanam"):
        logger.run_tracked(tcfg, "stage0", boom)
    (run,) = store.load_runs(tcfg)
    assert run.status == "failed" and run.error_type == "RuntimeError"
    assert [a.name for a in run.outputs] == ["episodes"]                     # output parsial tetap tercatat
    err = store.load_errors(tcfg)[run.run_id]
    assert "galat tertanam" in err["message"] and "RuntimeError" in err["traceback"]
    assert store.load_evaluation(tcfg, run.run_id) is None                   # evaluasi dilewati saat gagal
    assert store.runs_table(tcfg).iloc[0]["summary"] == "run gagal"


def test_logs_never_overwritten(tcfg):
    logger.run_tracked(tcfg, "stage0", _producer)
    logger.run_tracked(tcfg, "stage0", _producer, v=0.2)
    assert len({r.run_id for r in store.load_runs(tcfg)}) == 2
    with pytest.raises(FileExistsError):
        store.write_record(tcfg, "pipelines", "x", {"a": 1})
        store.write_record(tcfg, "pipelines", "x", {"a": 2})


def test_nested_and_pipeline_and_disable(tcfg, monkeypatch):
    @logger.tracked("task1")
    def inner(cfg):
        _consumer(cfg)

    @logger.tracked("stage0")
    def outer(cfg):
        _producer(cfg)
        inner(cfg)                                                            # bertingkat → bagian run luar

    with logger.pipeline(tcfg) as pid:
        outer(tcfg)
        inner(tcfg)
    runs = store.load_runs(tcfg)
    assert [r.task_id for r in runs] == ["stage0", "task1"]
    assert {r.pipeline_id for r in runs} == {pid}
    p = store.load_pipelines(tcfg)[pid]
    assert p["status"] == "success" and [r["task_id"] for r in p["runs"]] == ["stage0", "task1"]
    assert inner.task_id == "task1" and inner.__name__ == "inner"
    monkeypatch.setenv("KAGAMI_TRACKING", "0")
    inner(tcfg)
    assert len(store.load_runs(tcfg)) == 2


def test_staleness_and_compare(tcfg):
    logger.run_tracked(tcfg, "stage0", _producer)
    logger.run_tracked(tcfg, "task1", _consumer)
    assert not store.staleness(tcfg)["stale"].any()
    logger.run_tracked(tcfg, "stage0", _producer, v=0.3)                     # hulu berubah, task1 belum diulang
    st_ = store.staleness(tcfg)
    assert st_.loc[st_["task_id"] == "task1", "stale"].all()
    logger.run_tracked(tcfg, "task1", _consumer)
    t1 = [r.run_id for r in store.load_runs(tcfg) if r.task_id == "task1"]
    cmp = store.compare_runs(tcfg, t1)
    art = cmp["artifacts"].set_index(["io", "artifact"])
    assert bool(art.loc[("inputs", "episodes"), "changed"]) and bool(art.loc[("outputs", "fx_variation"), "changed"])
    assert not store.staleness(tcfg)["stale"].any()


def test_evaluate_existing_has_no_execution_time(tcfg):
    write_artifact(tcfg, "episodes", _eps())
    rec = logger.evaluate_existing(tcfg, "stage0")
    assert rec.run_type == "evaluation" and rec.duration_s is None and rec.evaluation_s is not None
    ev = _m(store.load_evaluation(tcfg, rec.run_id).metrics)
    assert ev["n_episodes"].value == 1
    assert ev["panel_cells"].status == "not_applicable" and "panel_weekly" in ev["panel_cells"].reason


def test_run_plots_accept_mixed_timestamp_formats():
    """Regresi D-138: log lama (detik) + log baru (mikrodetik) → pd.to_datetime tanpa format crash di halaman 7."""
    from kagami.viz import plots

    runs = pd.DataFrame({"run_id": ["a", "b", "c"], "task_id": ["task2"] * 3, "run_type": ["execution"] * 3,
                         "status": ["success", "success", "failed"], "duration_s": [10.0, 12.0, 3.0],
                         "started_at": ["2026-11-23T20:05:24+00:00", "2026-11-23T22:10:34.977692+00:00",
                                        "2026-11-24T01:00:00.000001+00:00"]})
    metrics = pd.DataFrame({"run_id": ["a", "b"], "task_id": ["task2"] * 2, "name": ["selected_k"] * 2,
                            "value": [1, 1], "status": ["ok", "ok"], "reason": [None, None]})
    assert len(plots.run_durations(runs).data) == 2
    fig = plots.metric_trend(metrics, runs, "task2", "selected_k")
    assert list(pd.to_datetime(fig.data[0].x).year) == [2026, 2026]


def test_dependency_edges_follow_requires():
    e = pd.DataFrame(registry.dependency_edges())
    pairs = set(zip(e["producer"], e["consumer"]))
    assert {("stage0", "task1"), ("task1", "task2"), ("task1", "task3"), ("stage0", "task4"),
            ("task4", "robustness"), ("snapshot", "stage0")} <= pairs
    assert ("task2", "task3") not in pairs and not any(p == "task2" for p, _ in pairs)   # task2 = daun (tidak linear)
    assert set(registry.TASKS) == set(evaluators.EVALUATORS)


def test_raw_snapshot_id_ignores_timestamps():
    ck = pd.DataFrame({"source": ["a", "b"], "file": ["a/1.csv", "b/2.csv"], "bytes": [1, 2], "sha256": ["x" * 64, "y" * 64],
                       "retrieved_at": ["t1", "t2"], "recorded_at": ["t3", "t4"]})
    later = ck.assign(recorded_at=["t9", "t9"]).iloc[::-1]                  # ditulis ulang, urutan lain
    assert lineage.raw_snapshot_id(ck) == lineage.raw_snapshot_id(later)
    assert lineage.raw_snapshot_id(ck) != lineage.raw_snapshot_id(ck.assign(sha256=["z" * 64, "y" * 64]))


def test_git_info_reads_head(tmp_path):
    g = tmp_path / ".git" / "refs" / "heads"
    g.mkdir(parents=True)
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/dev\n")
    (g / "dev").write_text("a" * 40 + "\n")
    assert lineage.git_info(tmp_path) == ("a" * 40, "dev")
    assert lineage.git_info(tmp_path / "x") == (None, None)


def test_drive_logs_roundtrip(tcfg, tmp_path):
    from test_drive import FakeDrive

    from kagami.utils import drive

    logger.run_tracked(tcfg, "stage0", _producer)
    fake = FakeDrive(tcfg.runtime["drive"]["folder_id"])
    sent = drive.push_logs(tcfg, client=fake)
    assert len(sent) == 2 and drive.push_logs(tcfg, client=fake) == []        # unik per run: tidak diunggah ulang
    other = Config(root=tcfg.root, out_root=tmp_path / "other", raw_root=tcfg.raw_root)
    got = drive.pull_logs(other, client=fake)
    assert sorted(got) == sorted(sent)
    assert [r.run_id for r in store.load_runs(other)] == [r.run_id for r in store.load_runs(tcfg)]


# --------------------------------------------------------------------------- evaluator pada artefak asli
def _real(cfg, *names):
    from kagami.utils.io import exists

    missing = [n for n in names if not exists(cfg, n)]
    if missing:
        pytest.skip(f"artefak asli tidak ada: {missing}")


def test_task2_evaluator_reproduces_silhouette(cfg):
    _real(cfg, "cluster_selection", "clusters", "response_features")
    m = _m(evaluators.evaluate_task2(cfg))
    assert m["silhouette_recompute_max_abs_diff"].value < 1e-12
    assert m["ward_labels_reproduced_ari"].value == pytest.approx(1.0)
    if m["selected_k"].value == 1:
        assert m["silhouette"].status == "not_applicable"
    assert all(x.status != "failed" for x in m.values()), [x for x in m.values() if x.status == "failed"]


def test_task4_evaluator_recomputes_mae(cfg):
    _real(cfg, "forecast_eval", "forecast_preds")
    m = _m(evaluators.evaluate_task4(cfg))
    assert m["mae_crosscheck_max_abs_diff"].value < 1e-9
    assert m["h8_M0_r2_oos_vs_zero"].value == pytest.approx(0.0)
    assert m["h8_M2_mape"].status == "not_applicable"


def test_all_evaluators_run_on_real_artifacts(cfg):
    _real(cfg, "profiles", "forecast_eval", "assoc", "robustness")
    for task in registry.ORDER:
        ms = evaluators.evaluate(cfg, task)
        assert ms and all(x.status != "failed" for x in ms), (task, [x for x in ms if x.status == "failed"])
        assert all(x.reason for x in ms if x.status != "ok")


# --------------------------------------------------------------------------- app
def test_page_renders_with_synthetic_logs(tcfg, monkeypatch):
    from streamlit.testing.v1 import AppTest

    logger.run_tracked(tcfg, "stage0", _producer)
    logger.run_tracked(tcfg, "task1", _consumer)
    logger.run_tracked(tcfg, "task1", _consumer, scale=3.0)
    with pytest.raises(RuntimeError):
        logger.run_tracked(tcfg, "task2", lambda c: (_ for _ in ()).throw(RuntimeError("x")))
    logger.run_tracked(tcfg, "task4", _forecast_producer)
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    import common                                                             # noqa: E402 -- modul app

    monkeypatch.setattr(common, "CFG", tcfg)        # hanya log sintetis (bukan logs/ project)
    try:
        at = AppTest.from_file(str(APP / "pages" / "7_Evaluasi_Eksekusi.py"), default_timeout=90).run()
        assert not at.exception, [e.value for e in at.exception]
        vals = {m.label: m.value for m in at.metric}
        assert vals["Eksekusi berhasil"] == "4/5" and vals["Run gagal"] == "1" and vals["Evaluasi-saja"] == "0"
        assert not [i.value for i in at.info if "Belum ada log" in i.value]
        for section in ("Evaluasi per tahap", "Perbandingan run", "Alur pipeline", "Riwayat"):
            at.radio(key="pick_bagian").set_value(section).run()
            assert not at.exception, (section, [e.value for e in at.exception])
        at.radio(key="pick_bagian").set_value("Perbandingan run").run()
        at.selectbox(key="cmp_task").set_value("task1").run()            # dua run task1 → tabel perbandingan
        assert not at.exception and len(at.dataframe) >= 2
        at.radio(key="pick_bagian").set_value("Evaluasi per tahap").run()
        at.selectbox(key="eval_task").set_value("task2").run()           # run gagal → pesan galat + traceback
        assert any("Run gagal" in e.value for e in at.error)
        at.selectbox(key="eval_task").set_value("task4").run()           # ringkasan model dulu (D-144)
        assert not at.exception, [e.value for e in at.exception]
        assert any("Perbandingan model" in h.value for h in at.subheader)
        assert not any("Arah perubahan" in h.value for h in at.subheader)  # diagnostik lanjutan tersembunyi
        at.toggle(key="adv_task4").set_value(True).run()                 # diagnostik arah: tabel + confusion matrix
        assert not at.exception, [e.value for e in at.exception]
        assert any("Arah perubahan" in h.value for h in at.subheader)
        assert at.selectbox(key="eval_conf_task4").value == "h4_M2"
    finally:
        sys.modules.pop("common", None)
    assert json.loads((tcfg.out_dir / "logs" / "runs" / f"{store.load_runs(tcfg)[0].run_id}.json")
                      .read_text(encoding="utf-8"))["schema_version"] == 3


# --------------------------------------------------------------------------- D-140: interval, segmen, penilaian, lineage output
def _dir_panel(signal: float, n_origins=40, n_series=30, seed=3):
    """Panel ramalan sintetis: origin × seri, y bersama (guncangan nasional) + idiosinkratik; ramalan = signal·y + derau."""
    rng = np.random.default_rng(seed)
    rows = []
    for o in range(n_origins):
        common = rng.normal(0.01, 0.03)
        y = common + rng.normal(0, 0.03, n_series)
        rows.append(pd.DataFrame({"origin": o, "series": np.arange(n_series), "y_true": y,
                                  "y_pred": signal * y + rng.normal(0, 0.03, n_series)}))
    return pd.concat(rows, ignore_index=True)


def test_direction_bootstrap_detects_signal_and_respects_dependence():
    strong, noise = _dir_panel(1.0), _dir_panel(0.0)
    b = direction_bootstrap(strong["y_true"], strong["y_pred"], strong["origin"], block=2, reps=299, seed=1)
    assert b["n_origins"] == 40 and b["accuracy_gap"][0] > 0 and b["roc_auc"][0] > 0.5
    b0 = direction_bootstrap(noise["y_true"], noise["y_pred"], noise["origin"], block=2, reps=299, seed=1)
    assert b0["accuracy_gap"][0] < 0 < b0["accuracy_gap"][1] or b0["accuracy_gap"][1] <= 0   # tanpa sinyal: tak > baseline
    assert b0["roc_auc"][0] < 0.5 < b0["roc_auc"][1]
    # blok ≥ n origin → setiap replikasi = sampel asli: AUC/AP berbobot = sklearn
    from sklearn.metrics import average_precision_score, roc_auc_score

    d = strong[strong["y_true"] != 0]
    full = direction_bootstrap(d["y_true"], d["y_pred"], d["origin"], block=40, reps=5, seed=0)
    up = d["y_true"] > 0
    assert full["roc_auc"][0] == pytest.approx(roc_auc_score(up, d["y_pred"]), abs=1e-9)
    assert full["pr_auc"][0] == pytest.approx(average_precision_score(up, d["y_pred"]), abs=1e-9)
    assert direction_bootstrap([0.1, -0.1], [0.1, 0.2], [0, 1], block=2) is None              # < 3 origin


def test_direction_segment_table_per_segment():
    a, b = _dir_panel(1.0, seed=4), _dir_panel(0.0, seed=5)
    df = pd.concat([a.assign(commodity="kuat"), b.assign(commodity="acak")], ignore_index=True)
    df = pd.concat([df.assign(model="M1"), df.assign(model="M2", y_pred=df["y_pred"] * 2)], ignore_index=True)
    segs = {"komoditas": {c: (df["commodity"] == c).to_numpy() for c in ("kuat", "acak")}}
    rows = pd.DataFrame(direction_segment_table(df, segs, ["M1", "M2"], block=2, reps=199, seed=2))
    assert len(rows) == 4 and set(rows["segment"]) == {"kuat", "acak"}
    assert (rows.loc[rows["model"] == "M1", "mae_ratio_vs_m1"] == 1).all()
    assert rows.loc[(rows["segment"] == "kuat") & (rows["model"] == "M1"), "assessment"].iloc[0] == "better"
    assert rows.loc[(rows["segment"] == "acak") & (rows["model"] == "M1"), "assessment"].iloc[0] != "better"
    assert (rows["gap_ci_low"] <= rows["accuracy_gap"]).all() and (rows["accuracy_gap"] <= rows["gap_ci_high"]).all()


def test_feature_health_counts_constant_columns():
    X = pd.DataFrame({"a": [1.0, 2, 3, 4], "b": [0.0] * 4, "c": [2.0, 4, 6, 8.1], "d": [5.0] * 4})
    fh = feature_health(X)
    assert fh["n_constant"] == 2 and fh["constant_features"] == ["b", "d"] and fh["effective_dimensions"] == 2
    assert fh["n_redundant_pairs"] == 1


def test_assessment_rules_two_layers():
    peers = {"h8_M2_dir_majority_baseline_accuracy": 0.545, "dm_p_h8_M2": 0.006, "placebo_p95_silhouette": 0.196}
    acc = assessment.assess("h8_M2_dir_accuracy", 0.56, {"gap_ci_low": -0.02, "gap_ci_high": 0.05}, peers)
    assert acc["assessment"] == "inconclusive" and acc["reference"] == 0.545
    acc2 = assessment.assess("h8_M2_dir_accuracy", 0.60, {"gap_ci_low": 0.02, "gap_ci_high": 0.08}, peers)
    assert acc2["assessment"] == "better"
    assert assessment.assess("h8_M2_dir_roc_auc", 0.57, {"ci_low": 0.54, "ci_high": 0.6})["assessment"] == "better"
    assert assessment.assess("h8_M2_dir_accuracy", 0.56, {}, peers)["assessment"] == "inconclusive"   # tanpa interval
    assert assessment.assess("mae_ratio_vs_m1_h8_M2", 1.017, {}, peers)["assessment"] == "worse"
    assert assessment.assess("mae_ratio_vs_m1_h8_M3", 1.015, {}, {"dm_p_h8_M3": 0.49})["assessment"] == "inconclusive"
    # 3/48 ≈ α · 48 → tidak berbeda dari laju positif palsu; 20/48 jelas di atas
    assert assessment.assess("share_ci_excludes_zero_national", 3 / 48, {"n": 48})["assessment"] == "inconclusive"
    assert assessment.assess("share_ci_excludes_zero_national", 20 / 48, {"n": 48})["assessment"] == "better"
    assert assessment.assess("placebo_false_positive_rate", 0.081, {"n": 19452})["assessment"] == "review"
    assert assessment.assess("v4_mean_sign_agree", 0.508, {"n": 30})["assessment"] == "inconclusive"
    assert assessment.assess("silhouette_k3", 0.184, {}, peers)["assessment"] == "inconclusive"
    assert assessment.assess("silhouette_recompute_max_abs_diff", 5e-17)["assessment"] == "expected"
    assert assessment.assess("h2_p_interval_consistency", 0.87)["assessment"] == "expected"
    assert assessment.assess("n_files", 28)["assessment"] == "info"
    m = pd.DataFrame({"run_id": ["r", "r"], "task_id": ["task4"] * 2, "group": ["g"] * 2,
                      "name": ["h8_M2_dir_majority_baseline_accuracy", "x"], "value": [0.545, None],
                      "status": ["ok", "not_applicable"], "reason": [None, "alasan"], "context": ["{}", "{}"]})
    out = assessment.assess_table(m)
    assert list(out["assessment"]) == ["info", "not_computed"] and set(assessment.COLUMNS) <= set(out.columns)


def test_compare_classifies_new_metrics_and_fingerprint(tcfg):
    logger.run_tracked(tcfg, "stage0", _producer)
    logger.run_tracked(tcfg, "stage0", _producer, v=0.4)
    ids = [r.run_id for r in store.load_runs(tcfg)]
    rec = store.load_runs(tcfg)[0]
    assert rec.code_sha256 and len(rec.code_sha256) == 64 and rec.environment["python"]
    assert rec.git_dirty is None                                               # root sementara bukan repo git
    cmp = store.compare_runs(tcfg, ids)["metrics"].set_index("name")
    assert cmp.loc["max_cum_dlog_e", f"perubahan {ids[1]}"] == "berubah"
    assert cmp.loc["n_episodes", f"perubahan {ids[1]}"] == "sama"
    assert store._change(None, 1.0) == "baru" and store._change(1.0, None) == "hilang"


def test_code_hash_changes_with_code(tmp_path):
    (tmp_path / "src").mkdir()
    f = tmp_path / "src" / "a.py"
    f.write_text("x = 1\n", encoding="utf-8")
    h1 = lineage.code_hash(tmp_path)
    assert h1 == lineage.code_hash(tmp_path)
    f.write_text("x = 2\n", encoding="utf-8")
    assert lineage.code_hash(tmp_path) != h1
    assert lineage.code_hash(tmp_path / "kosong") is None


def test_artifact_sync_and_stage_states(tcfg):
    logger.run_tracked(tcfg, "stage0", _producer)
    s = store.artifact_sync(tcfg).set_index("artifact")
    assert s.loc["episodes", "state"] == "sinkron"
    # tabel referensi stage0 di data/reference (disalin ke root sementara) tidak ditulis run ini → sebagian dieksekusi
    assert (s.loc[s["stage"] == "stage0", "state"] == "tanpa log").any()
    assert store.stage_states(tcfg)["stage0"] == "sebagian dieksekusi"
    write_artifact(tcfg, "episodes", _eps(0.5))                               # diganti di luar run (mis. unduhan Drive)
    s = store.artifact_sync(tcfg).set_index("artifact")
    assert s.loc["episodes", "state"] == "tidak sinkron" and s.loc["episodes", "producer_run"] is None
    assert store.stage_states(tcfg)["stage0"] == "dieksekusi · output tidak sinkron"
    write_artifact(tcfg, "fx_variation", _fxv())
    logger.evaluate_existing(tcfg, "task1")
    st_ = store.stage_states(tcfg)
    assert st_["task1"] == "hanya dievaluasi" and st_["task4"] == "belum ada run"


def test_task4_classifier_evaluator_synthetic(tcfg):
    """D-141: bagian klasifier eksploratif — metrik arah C1/C2, beda berpasangan vs C1/M3/M1, prediksi selektif, segmen."""
    rng = np.random.default_rng(5)
    rows, cls = [], []
    for o in pd.date_range("2024-01-01", periods=12, freq="28D"):
        y = rng.normal(0.005, 0.03, 40)
        base = {"origin": o, "horizon": 4, "province_id": np.arange(40) % 34 + 1, "region": "Jawa",
                "commodity": np.where(np.arange(40) < 20, "beras", "cabai_rawit"), "y_true": y, "large_move": False}
        for mo, pr in (("M1", 0.3 * y + rng.normal(0, 0.03, 40)), ("M3", 0.8 * y + rng.normal(0, 0.02, 40))):
            rows.append(pd.DataFrame({**base, "model": mo, "y_pred": pr}))
        for mo, noise in (("C1", 0.06), ("C2", 0.01)):
            cls.append(pd.DataFrame({**base, "model": mo,
                                     "p_up": 1 / (1 + np.exp(-(y + rng.normal(0, noise, 40)) / 0.03))}))
    write_artifact(tcfg, "forecast_preds", pd.concat(rows, ignore_index=True))
    write_artifact(tcfg, "direction_preds", pd.concat(cls, ignore_index=True))
    ms = _m(evaluators.evaluate_task4(tcfg))
    assert all(x.status != "failed" for x in ms.values()), [x for x in ms.values() if x.status == "failed"]
    assert ms["h4_C2_dir_accuracy"].value > ms["h4_C1_dir_accuracy"].value
    diff = ms["h4_C2_vs_C1_accuracy_diff"]
    assert diff.status == "ok" and diff.context["ci_low"] > 0
    assert {"h4_C2_vs_M3_accuracy_diff", "h4_C1_vs_M1_accuracy_diff", "h4_C2_selective"} <= set(ms)
    seg = pd.DataFrame(ms["h4_dir_by_segment"].value)
    assert {"C1", "C2", "M1", "M3"} <= set(seg["model"]) and seg.loc[seg["model"] == "C2", "mae"].isna().all()
    a = assessment.assess("h4_C2_vs_C1_accuracy_diff", diff.value, diff.context)
    assert a["assessment"] == "better"


def test_task4_deep_evaluator_synthetic(tcfg):
    """D-142: bagian model deep — regresi & arah per model, rasio MAE vs M1 + DM pada baris sama, beda TSMX_fx − TSMX."""
    rng = np.random.default_rng(9)
    rows, deep = [], []
    for o in pd.date_range("2024-01-01", periods=14, freq="28D"):
        y = rng.normal(0.005, 0.03, 40)
        base = {"origin": o, "horizon": 8, "province_id": np.arange(40) % 34 + 1, "region": "Jawa",
                "commodity": "beras", "y_true": y, "large_move": False}
        for mo, pr in (("M1", 0.2 * y + rng.normal(0, 0.03, 40)), ("M3", 0.5 * y + rng.normal(0, 0.02, 40))):
            rows.append(pd.DataFrame({**base, "model": mo, "y_pred": pr}))
        for mo, pr in (("TSMX", 0.2 * y + rng.normal(0, 0.03, 40)), ("TSMX_fx", 0.9 * y + rng.normal(0, 0.005, 40))):
            deep.append(pd.DataFrame({**base, "model": mo, "y_pred": pr}))
    write_artifact(tcfg, "forecast_preds", pd.concat(rows, ignore_index=True))
    write_artifact(tcfg, "deep_preds", pd.concat(deep, ignore_index=True))
    ms = _m(evaluators.evaluate_task4(tcfg))
    assert all(x.status != "failed" for x in ms.values()), [x for x in ms.values() if x.status == "failed"]
    assert {"h8_TSMX_fx_mae", "h8_TSMX_fx_dir_accuracy", "mae_ratio_vs_m1_h8_TSMX_fx", "dm_p_h8_TSMX_fx",
            "mae_ratio_h8_TSMX_fx_vs_TSMX", "h8_TSMX_fx_vs_TSMX_accuracy_diff", "h8_TSMX_fx_vs_M3_accuracy_diff"} <= set(ms)
    r = ms["mae_ratio_h8_TSMX_fx_vs_TSMX"]
    assert r.value < 1 and assessment.assess(r.name, r.value, r.context)["assessment"] == "better"
    m1 = ms["mae_ratio_vs_m1_h8_TSMX_fx"]
    assert assessment.assess(m1.name, m1.value, m1.context, {"dm_p_h8_TSMX_fx": ms["dm_p_h8_TSMX_fx"].value})[
        "assessment"] == "better"
    seg = pd.DataFrame(ms["h8_dir_by_segment"].value)
    assert {"TSMX", "TSMX_fx"} <= set(seg["model"]) and seg.loc[seg["model"] == "TSMX_fx", "mae"].notna().all()


def test_bootstrap_p_and_bh_multiplicity():
    """D-143: p bootstrap konsisten dengan interval persentil; hasil yang tidak lolos BH diturunkan ke inconclusive."""
    from kagami.tracking.metrics import bootstrap_p

    rng = np.random.default_rng(3)
    far, near = rng.normal(0.05, 0.01, 999), rng.normal(0.01, 0.01, 999)
    assert bootstrap_p(far, 0.0) < 0.01 and bootstrap_p(near, 0.0) > 0.05 and bootstrap_p([], 0.0) is None
    lo, hi = np.percentile(near, [2.5, 97.5])
    assert (lo > 0 or hi < 0) == (bootstrap_p(near, 0.0) < 0.05)
    ctx = lambda p, lo, hi: json.dumps({"ci_low": lo, "ci_high": hi, "p_boot": p})   # noqa: E731
    rows = [{"run_id": "r", "task_id": "task4", "group": "g", "name": f"h8_X{i}_vs_Y_accuracy_diff", "value": 0.02,
             "status": "ok", "reason": None, "context": ctx(p, 0.001, 0.04)} for i, p in enumerate([0.001, 0.04, 0.045])]
    rows += [{"run_id": "r", "task_id": "task4", "group": "g", "name": f"h8_Z{i}_vs_Y_accuracy_diff", "value": 0.0,
              "status": "ok", "reason": None, "context": ctx(0.9, -0.02, 0.02)} for i in range(7)]
    out = assessment.assess_table(pd.DataFrame(rows)).set_index("name")
    assert out.loc["h8_X0_vs_Y_accuracy_diff", "assessment"] == "better"          # q = 0,01
    assert out.loc["h8_X1_vs_Y_accuracy_diff", "assessment"] == "inconclusive"    # p 0,04 → q 0,15
    assert "tidak lolos koreksi BH" in out.loc["h8_X1_vs_Y_accuracy_diff", "interpretation"]
    assert out["family"].eq("beda akurasi berpasangan").all() and out["q_value"].notna().all()
    off = assessment.assess_table(pd.DataFrame([{"run_id": "r", "task_id": "task4", "group": "g",
                                                 "name": "mae_ratio_vs_m1_h8_M2", "value": 1.02, "status": "ok",
                                                 "reason": None, "context": "{}"}]))
    assert off["family"].isna().all()                                             # uji resmi tidak dikoreksi


def test_direction_metrics_weighted_f1_and_coverage():
    """D-144: F1 berbobot = rerata F1 kelas berbobot jumlah aktual; akurasi termasuk perubahan nol; cakupan."""
    rng = np.random.default_rng(8)
    y = rng.normal(0.01, 0.05, 300)
    p = 0.5 * y + rng.normal(0, 0.04, 300)
    y[:50] = 0.0
    m = _m(direction_metrics(y, p))
    yt, yp = y[50:], p[50:]
    up, pu = yt > 0, yp > 0
    tp, fn, fp, tn = (up & pu).sum(), (up & ~pu).sum(), (~up & pu).sum(), (~up & ~pu).sum()
    f1u, f1d = 2 * tp / (2 * tp + fp + fn), 2 * tn / (2 * tn + fn + fp)
    assert m["dir_f1_weighted"].value == pytest.approx((up.sum() * f1u + (~up).sum() * f1d) / len(yt))
    assert m["dir_accuracy_incl_no_change"].value == pytest.approx((tp + tn) / 300)
    assert m["dir_coverage"].value == pytest.approx(250 / 300)
