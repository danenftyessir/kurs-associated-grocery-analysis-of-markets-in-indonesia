"""WP-36. Antarmuka pencatatan terpusat (D-137).

- `tracked(task_id)`   : dekorator untuk `pipelines.<tahap>.run` → setiap eksekusi lewat CLI atau notebook tercatat.
- `run_tracked`         : jalankan fungsi tahap sambil merekam lineage, waktu, memori, status; gagal → log galat lalu
                          exception dilempar ulang (pipeline tetap gagal seperti biasa).
- `pipeline(cfg)`       : konteks satu `pipeline_id` untuk beberapa tahap (`kagami all`).
- `evaluate_existing`   : evaluasi artefak tahap yang sudah ada tanpa menjalankan ulang (run_type = evaluation;
                          waktu eksekusi tidak teramati → duration_s None).

Pencatatan tidak boleh mengganggu analisis: galat saat menulis log hanya dicetak. Nonaktifkan dengan env
`KAGAMI_TRACKING=0`. Panggilan bertingkat (tahap di dalam tahap) tidak membuat run baru.
"""

from __future__ import annotations

import functools
import os
import secrets
import time
import traceback
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from kagami.tracking import evaluators, lineage, registry, store
from kagami.tracking.schemas import ErrorRecord, EvaluationRecord, RunRecord
from kagami.utils.config import Config
from kagami.utils.env import detect_platform
from kagami.utils.io import add_observer, find_artifact, remove_observer

_STATE: dict[str, Any] = {"active": None, "pipeline_id": None, "pipeline_runs": None}


def enabled() -> bool:
    return os.environ.get("KAGAMI_TRACKING", "1").strip().lower() not in ("0", "false", "no", "off")


def new_id(prefix: str) -> str:
    """ID unik & terurut waktu: <prefix>-YYYYmmddTHHMMSSZ-<6 heks acak>."""
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"


def _jsonable(v: Any) -> Any:
    return v if isinstance(v, (str, int, float, bool, type(None))) else repr(v)


def _base_record(cfg: Config, task_id: str, run_type: str) -> RunRecord:
    spec = registry.TASKS.get(task_id)
    commit, branch = lineage.git_info(cfg.root)
    return RunRecord(run_id=new_id(task_id), task_id=task_id, run_type=run_type, status="success",
                     started_at=store.now_iso(), pipeline_id=_STATE["pipeline_id"], platform=detect_platform(),
                     python=lineage.python_version(), git_commit=commit, git_branch=branch,
                     config_sha256=lineage.config_hashes(cfg), kind=spec.kind if spec else None,
                     algorithms=list(spec.algorithms) if spec else [], params=registry.task_params(cfg, task_id))


def _finish(cfg: Config, rec: RunRecord, inputs: dict, outputs: dict, error: BaseException | None,
            tb: str | None) -> None:
    """Hash input/output, run induk, dataset, simpan run + (galat | evaluasi). Tidak pernah melempar.

    inputs: nama → Path atau (Path, sha256, bytes) yang di-hash saat dibaca."""
    try:
        rec.inputs = []
        for n, v in inputs.items():
            path, sha, size = v if isinstance(v, tuple) else (v, None, None)
            if sha is not None or path.exists():
                rec.inputs.append(lineage.artifact_ref(cfg, n, path, profile=False, sha256=sha, size=size))
        rec.outputs = [lineage.artifact_ref(cfg, n, p) for n, p in outputs.items() if p.exists()]
        runs = store.load_runs(cfg)
        rec.parent_run_ids = lineage.link_parents(rec.inputs, runs, exclude=rec.run_id)
        parents = [r for r in runs if r.run_id in rec.parent_run_ids]
        rec.dataset_id = lineage.dataset_id(cfg, rec.inputs, parents)
        rec.peak_rss_mb = lineage.peak_rss_mb()
        if error is not None:
            rec.status, rec.error_type = "failed", type(error).__name__
            store.write_record(cfg, "errors", rec.run_id, ErrorRecord(
                run_id=rec.run_id, task_id=rec.task_id, at=store.now_iso(), error_type=type(error).__name__,
                message=str(error), traceback=tb or ""))
        else:
            t0 = time.perf_counter()
            metrics = evaluators.evaluate(cfg, rec.task_id)
            rec.evaluation_s = round(time.perf_counter() - t0, 3)
            store.write_record(cfg, "evaluations", rec.run_id, EvaluationRecord(
                run_id=rec.run_id, task_id=rec.task_id, evaluated_at=store.now_iso(), metrics=metrics))
        path = store.write_record(cfg, "runs", rec.run_id, rec)
        if _STATE["pipeline_runs"] is not None:
            _STATE["pipeline_runs"].append({"run_id": rec.run_id, "task_id": rec.task_id, "status": rec.status})
        dur = f"{rec.duration_s:.1f} dtk" if rec.duration_s is not None else "evaluasi saja"
        print(f"[tracking] {rec.task_id} {rec.status} ({dur}) -> {path.relative_to(cfg.out_dir).as_posix()}")
    except Exception as exc:  # noqa: BLE001 -- log gagal tidak boleh menutupi hasil/galat tahap
        print(f"[tracking] PERINGATAN: log {rec.run_id} gagal ditulis: {type(exc).__name__}: {exc}")


def run_tracked(cfg: Config, task_id: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Jalankan fn(cfg, *args, **kwargs) sebagai satu run tercatat; nilai balik & exception fn diteruskan apa adanya."""
    if not enabled() or _STATE["active"] is not None:
        return fn(cfg, *args, **kwargs)
    rec = _base_record(cfg, task_id, "execution")
    rec.call_args = {k: _jsonable(v) for k, v in kwargs.items()}
    rec.call_args.update({f"arg{i}": _jsonable(v) for i, v in enumerate(args)})
    recorder = lineage.Recorder()
    add_observer(recorder.observe)
    _STATE["active"] = rec.run_id
    t0 = time.perf_counter()
    error, tb = None, None
    try:
        return fn(cfg, *args, **kwargs)
    except BaseException as exc:
        error, tb = exc, traceback.format_exc()
        raise
    finally:
        remove_observer(recorder.observe)
        _STATE["active"] = None
        rec.duration_s = round(time.perf_counter() - t0, 3)
        rec.finished_at = store.now_iso()
        _finish(cfg, rec, recorder.reads, recorder.writes, error, tb)


def tracked(task_id: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Dekorator `run(cfg, ...)` sebuah pipeline → setiap pemanggilan menjadi run tercatat."""
    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(cfg: Config, *args: Any, **kwargs: Any) -> Any:
            return run_tracked(cfg, task_id, fn, *args, **kwargs)
        wrapper.task_id = task_id   # type: ignore[attr-defined]
        return wrapper
    return deco


@contextmanager
def pipeline(cfg: Config) -> Iterator[str]:
    """Semua run di dalam blok berbagi satu pipeline_id; ringkasan ditulis ke logs/pipelines/<id>.json."""
    pid = new_id("pipeline")
    _STATE["pipeline_id"], _STATE["pipeline_runs"] = pid, []
    started, status = store.now_iso(), "success"
    try:
        yield pid
    except BaseException:
        status = "failed"
        raise
    finally:
        runs = _STATE["pipeline_runs"] or []
        _STATE["pipeline_id"], _STATE["pipeline_runs"] = None, None
        if enabled():
            try:
                store.write_record(cfg, "pipelines", pid, {"pipeline_id": pid, "started_at": started,
                                                           "finished_at": store.now_iso(), "status": status,
                                                           "runs": runs})
            except Exception as exc:  # noqa: BLE001
                print(f"[tracking] PERINGATAN: log pipeline {pid} gagal ditulis: {exc}")


def evaluate_existing(cfg: Config, task_id: str, note: str | None = None) -> RunRecord:
    """Evaluasi artefak tahap yang sudah ada TANPA menjalankan ulang. Input = REQUIRES + OPTIONAL yang ada, output =
    artefak registry tahap itu yang ada; duration_s = None (eksekusinya tidak diamati pelacakan)."""
    rec = _base_record(cfg, task_id, "evaluation")
    rec.note = note or "evaluasi artefak yang ada; waktu eksekusi tidak teramati (dijalankan sebelum/di luar pelacakan)"
    req = registry.stage_requires().get(task_id, {"required": (), "optional": ()})
    inputs = {n: p for n in (*req["required"], *req["optional"]) if (p := find_artifact(cfg, n)) is not None}
    outputs = {n: p for n in registry.stage_outputs(task_id) if (p := find_artifact(cfg, n)) is not None}
    rec.finished_at = store.now_iso()
    _finish(cfg, rec, inputs, outputs, None, None)
    return rec
