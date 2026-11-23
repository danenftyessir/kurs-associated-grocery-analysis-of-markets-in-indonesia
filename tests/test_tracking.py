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

from kagami.tracking import evaluators, lineage, logger, registry, store
from kagami.tracking.metrics import clustering_metrics, interval_consistency, regression_metrics
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
    monkeypatch.syspath_prepend(str(APP))
    sys.modules.pop("common", None)
    import common                                                             # noqa: E402 -- modul app

    monkeypatch.setattr(common, "CFG", tcfg)        # hanya log sintetis (bukan logs/ project)
    try:
        at = AppTest.from_file(str(APP / "pages" / "7_Evaluasi_Eksekusi.py"), default_timeout=90).run()
        assert not at.exception, [e.value for e in at.exception]
        vals = {m.label: m.value for m in at.metric}
        assert vals["Total run"] == "4" and vals["Gagal"] == "1"
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
    finally:
        sys.modules.pop("common", None)
    assert json.loads((tcfg.out_dir / "logs" / "runs" / f"{store.load_runs(tcfg)[0].run_id}.json")
                      .read_text(encoding="utf-8"))["schema_version"] == 1
