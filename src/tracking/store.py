"""WP-36. Penyimpanan log JSON: tulis ke `cfg.out_dir/logs/<jenis>/<id>.json` (mode eksklusif → tidak pernah menimpa),
baca dari `logs/` di setiap `cfg.read_dirs` (out_dir → artifact_dirs → root), riwayat, perbandingan, hasil basi.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from kagami.data.snapshot import sha256_file
from kagami.tracking.schemas import EvaluationRecord, RunRecord, metric_from_dict, run_from_dict, to_dict
from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config

LOG_DIR = "logs"
KINDS = ("runs", "evaluations", "errors", "pipelines")


def _json_default(o: Any) -> Any:
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    if isinstance(o, Path):
        return o.as_posix()
    return str(o)


def now_iso() -> str:
    # mikrodetik: beberapa run dalam detik yang sama (evaluate all, tes) tetap terurut benar untuk run terakhir & induk
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def write_record(cfg: Config, kind: str, record_id: str, payload: Any) -> Path:
    """Tulis satu log baru; FileExistsError bila id sudah ada (log lama tidak pernah ditimpa)."""
    if kind not in KINDS:
        raise ValueError(f"jenis log tidak dikenal: {kind}")
    p = cfg.out_dir / LOG_DIR / kind / f"{record_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    data = to_dict(payload) if not isinstance(payload, dict) else payload
    with open(p, "x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=_json_default)
        f.write("\n")
    return p


def log_dirs(cfg: Config) -> list[Path]:
    out, seen = [], set()
    for d in cfg.read_dirs:
        p = (Path(d) / LOG_DIR).resolve()
        if p not in seen and p.is_dir():
            seen.add(p)
            out.append(p)
    return out


def _records(cfg: Config, kind: str) -> dict[str, dict]:
    """id → isi JSON; lokasi baca pertama menang (seperti artefak). File rusak dilewati dengan pesan."""
    out: dict[str, dict] = {}
    for d in log_dirs(cfg):
        for f in sorted((d / kind).glob("*.json")):
            if f.stem in out:
                continue
            try:
                out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[tracking] log {f.name} dilewati: {exc}")
    return out


def load_runs(cfg: Config) -> list[RunRecord]:
    """Semua RunRecord, urut started_at."""
    return sorted((run_from_dict(d) for d in _records(cfg, "runs").values()), key=lambda r: r.started_at)


def load_evaluation(cfg: Config, run_id: str) -> EvaluationRecord | None:
    d = _records(cfg, "evaluations").get(run_id)
    if d is None:
        return None
    return EvaluationRecord(run_id=d["run_id"], task_id=d["task_id"], evaluated_at=d["evaluated_at"],
                            metrics=[metric_from_dict(m) for m in d.get("metrics", [])])


def load_errors(cfg: Config) -> dict[str, dict]:
    return _records(cfg, "errors")


def load_pipelines(cfg: Config) -> dict[str, dict]:
    return _records(cfg, "pipelines")


def runs_table(cfg: Config) -> pd.DataFrame:
    """Riwayat: satu baris per run + ringkasan evaluasi (jumlah metrik ok / tidak berlaku / gagal)."""
    evals = _records(cfg, "evaluations")
    rows = []
    for r in load_runs(cfg):
        ms = evals.get(r.run_id, {}).get("metrics", [])
        cnt = {s: sum(m.get("status") == s for m in ms) for s in ("ok", "not_applicable", "failed")}
        rows.append({"run_id": r.run_id, "task_id": r.task_id, "run_type": r.run_type, "status": r.status,
                     "started_at": r.started_at, "duration_s": r.duration_s, "evaluation_s": r.evaluation_s,
                     "pipeline_id": r.pipeline_id, "dataset_id": r.dataset_id, "platform": r.platform,
                     "git_commit": (r.git_commit or "")[:8] or None, "algorithm": "; ".join(r.algorithms),
                     "n_parents": len(r.parent_run_ids), "n_inputs": len(r.inputs), "n_outputs": len(r.outputs),
                     "metrics_ok": cnt["ok"], "metrics_na": cnt["not_applicable"], "metrics_failed": cnt["failed"],
                     "error_type": r.error_type, "git_dirty": r.git_dirty,
                     "code_sha256": (r.code_sha256 or "")[:12] or None, "evaluator_version": r.evaluator_version,
                     "summary": f"{cnt['ok']} ok · {cnt['not_applicable']} tidak berlaku · {cnt['failed']} gagal"
                     if ms else ("tanpa evaluasi" if r.status == "success" else "run gagal")})
    cols = ["run_id", "task_id", "run_type", "status", "started_at", "duration_s", "evaluation_s", "pipeline_id",
            "dataset_id", "platform", "git_commit", "algorithm", "n_parents", "n_inputs", "n_outputs", "metrics_ok",
            "metrics_na", "metrics_failed", "error_type", "git_dirty", "code_sha256", "evaluator_version", "summary"]
    return pd.DataFrame(rows, columns=cols)


def metrics_table(cfg: Config, run_ids: list[str] | None = None) -> pd.DataFrame:
    """Metrik long: run_id, task_id, group, name, value, status, reason, context (JSON teks)."""
    rows = []
    for rid, d in _records(cfg, "evaluations").items():
        if run_ids is not None and rid not in run_ids:
            continue
        for m in d.get("metrics", []):
            rows.append({"run_id": rid, "task_id": d["task_id"], "evaluated_at": d["evaluated_at"],
                         "group": m["group"], "name": m["name"], "value": m.get("value"), "status": m["status"],
                         "reason": m.get("reason"), "context": json.dumps(m.get("context", {}), ensure_ascii=False)})
    return pd.DataFrame(rows, columns=["run_id", "task_id", "evaluated_at", "group", "name", "value", "status",
                                       "reason", "context"])


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def compare_runs(cfg: Config, run_ids: list[str]) -> dict[str, pd.DataFrame]:
    """Bandingkan run (urutan = urutan argumen; run pertama = acuan).

    metrics: group, name, nilai per run, delta (numerik) terhadap run acuan, status per run.
    params : kunci parameter/argumen yang berbeda antar run. artifacts: sha256 input & output per run (berubah?).
    """
    runs = {r.run_id: r for r in load_runs(cfg)}
    sel = [runs[i] for i in run_ids if i in runs]
    m = metrics_table(cfg, [r.run_id for r in sel])
    if sel and not m.empty:
        val = m.pivot_table(index=["group", "name"], columns="run_id", values="value", aggfunc="first")
        stat = m.pivot_table(index=["group", "name"], columns="run_id", values="status", aggfunc="first")
        val = val.reindex(columns=[r.run_id for r in sel])
        base = sel[0].run_id
        out = val.copy()
        for r in sel[1:]:
            out[f"delta {r.run_id}"] = val[r.run_id].map(_num) - val[base].map(_num)
            out[f"perubahan {r.run_id}"] = [_change(a, b) for a, b in zip(val[base], val[r.run_id])]
        out["status"] = stat.apply(lambda s: "/".join(sorted(set(s.dropna()))), axis=1)
        metrics = out.reset_index()
    else:
        metrics = pd.DataFrame(columns=["group", "name"])
    prm = []
    flat = {r.run_id: {**_flatten(r.params, "params"), **_flatten(r.call_args, "args"),
                       **{f"config.{k}": v[:12] for k, v in r.config_sha256.items()},
                       **{f"env.{k}": v for k, v in (r.environment or {}).items()},
                       "git_commit": (r.git_commit or "")[:8], "git_dirty": r.git_dirty,
                       "code_sha256": (r.code_sha256 or "")[:12] or None, "run_type": r.run_type,
                       "evaluator_version": r.evaluator_version,
                       "dataset_id": r.dataset_id, "platform": r.platform}
            for r in sel}
    for key in sorted({k for d in flat.values() for k in d}):
        vals = [flat[r.run_id].get(key) for r in sel]
        if len({json.dumps(v, sort_keys=True, default=str) for v in vals}) > 1:
            prm.append({"key": key, **{r.run_id: v for r, v in zip(sel, vals)}})
    art = []
    for io in ("inputs", "outputs"):
        names = sorted({a.name for r in sel for a in getattr(r, io)})
        for n in names:
            shas = {r.run_id: next((a.sha256[:12] for a in getattr(r, io) if a.name == n), None) for r in sel}
            art.append({"io": io, "artifact": n, **shas, "changed": len({v for v in shas.values()}) > 1})
    return {"metrics": metrics, "params": pd.DataFrame(prm), "artifacts": pd.DataFrame(art)}


def _missing(v: Any) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v))


def _change(base: Any, other: Any) -> str:
    """sama | berubah | baru (tidak ada di run acuan) | hilang (tidak ada di run pembanding) — metrik baru tidak dihitung
    sebagai perubahan nilai (D-140)."""
    if _missing(base) and _missing(other):
        return "sama"
    if _missing(base):
        return "baru"
    if _missing(other):
        return "hilang"
    a, b = _num(base), _num(other)
    if not (np.isnan(a) or np.isnan(b)):
        return "sama" if np.isclose(a, b, rtol=1e-9, atol=1e-12) else "berubah"
    return "sama" if json.dumps(base, sort_keys=True, default=str) == json.dumps(other, sort_keys=True, default=str) \
        else "berubah"


def _flatten(d: dict, prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in (d or {}).items():
        key = f"{prefix}.{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def latest_runs(cfg: Config, run_type: str | None = None) -> dict[str, RunRecord]:
    """task_id → run terakhir (opsional hanya satu run_type)."""
    out: dict[str, RunRecord] = {}
    for r in load_runs(cfg):
        if run_type is None or r.run_type == run_type:
            out[r.task_id] = r
    return out


def staleness(cfg: Config) -> pd.DataFrame:
    """Untuk run sukses terakhir setiap tahap: input yang file-nya kini berbeda (hulu berubah setelah run itu).

    Kolom: task_id, run_id, artifact, recorded_sha, current_sha, stale (True = hasil tahap ini mungkin basi).
    """
    from kagami.utils.io import find_artifact

    rows = []
    for task, r in latest_runs(cfg).items():
        if r.status != "success":
            continue
        for a in r.inputs:
            p = find_artifact(cfg, a.name) if a.name in ARTIFACTS else None
            cur = sha256_file(p) if p is not None else None
            rows.append({"task_id": task, "run_id": r.run_id, "artifact": a.name, "recorded_sha": a.sha256[:12],
                         "current_sha": cur[:12] if cur else None, "stale": cur is not None and cur != a.sha256})
    return pd.DataFrame(rows, columns=["task_id", "run_id", "artifact", "recorded_sha", "current_sha", "stale"])


SYNC_STATES = ("sinkron", "tidak sinkron", "hanya dievaluasi", "tanpa log")


def artifact_sync(cfg: Config) -> pd.DataFrame:
    """Lineage OUTPUT (D-140): untuk setiap artefak registry yang ada di lokasi baca, apakah file itu benar-benar ditulis
    oleh run eksekusi tercatat. Run terbaru TIDAK dianggap produsen resmi hanya karena paling baru.

    state: sinkron (run eksekusi terakhir yang menulis artefak itu menghasilkan file yang sama dengan file sekarang) |
    tidak sinkron (run eksekusi terakhir menulis versi lain: file sekarang berasal dari luar run itu, mis. unduhan Drive
    atau run di folder lain) | hanya dievaluasi (tidak ada run eksekusi yang menulisnya; hanya run evaluasi-saja yang
    mencatat hash-nya) | tanpa log. Kolom: artifact, stage, current_sha, state, producer_run (run eksekusi dengan output
    = file sekarang), last_execution_run, last_execution_sha, last_execution_rows, current_rows, evaluated_by."""
    from kagami.utils.io import find_artifact

    runs = load_runs(cfg)
    rows = []
    for name, art in ARTIFACTS.items():
        p = find_artifact(cfg, name)
        if p is None:
            continue
        cur = sha256_file(p)
        execs = [(r, a) for r in runs if r.run_type == "execution" and r.status == "success"
                 for a in r.outputs if a.name == name]
        evals = [(r, a) for r in runs if r.run_type == "evaluation" for a in r.outputs if a.name == name]
        producer = next((r.run_id for r, a in reversed(execs) if a.sha256 == cur), None)
        last = execs[-1] if execs else None
        cur_rows = next((a.rows for _, a in reversed(execs + evals) if a.sha256 == cur and a.rows is not None), None)
        if last is not None:
            state = "sinkron" if last[1].sha256 == cur else "tidak sinkron"
        else:
            state = "hanya dievaluasi" if any(a.sha256 == cur for _, a in evals) else "tanpa log"
        rows.append({"artifact": name, "stage": art.stage, "current_sha": cur[:12], "state": state,
                     "producer_run": producer, "last_execution_run": last[0].run_id if last else None,
                     "last_execution_sha": last[1].sha256[:12] if last else None,
                     "last_execution_rows": last[1].rows if last else None, "current_rows": cur_rows,
                     "evaluated_by": next((r.run_id for r, a in reversed(evals) if a.sha256 == cur), None)})
    return pd.DataFrame(rows, columns=["artifact", "stage", "current_sha", "state", "producer_run",
                                       "last_execution_run", "last_execution_sha", "last_execution_rows",
                                       "current_rows", "evaluated_by"])


STAGE_STATES = ("dieksekusi", "sebagian dieksekusi", "dieksekusi · output tidak sinkron", "hanya dievaluasi",
                "eksekusi gagal", "evaluasi gagal", "belum ada run")


def stage_states(cfg: Config, sync: pd.DataFrame | None = None) -> dict[str, str]:
    """Status tahap untuk dashboard (D-140), memisahkan eksekusi dari evaluasi-saja: dieksekusi (run eksekusi terakhir
    sukses & semua output-nya sinkron) | sebagian dieksekusi (ada artefak tahap yang tidak pernah ditulis run eksekusi) |
    dieksekusi · output tidak sinkron | hanya dievaluasi (tidak ada run eksekusi)
    | eksekusi gagal | evaluasi gagal | belum ada run."""
    from kagami.tracking.registry import ORDER

    runs = load_runs(cfg)
    sync = artifact_sync(cfg) if sync is None else sync
    out: dict[str, str] = {}
    for task in ORDER:
        ex = [r for r in runs if r.task_id == task and r.run_type == "execution"]
        ev = [r for r in runs if r.task_id == task and r.run_type == "evaluation"]
        if ex:
            last = ex[-1]
            if last.status != "success":
                out[task] = "eksekusi gagal"
                continue
            # hanya artefak milik tahap ini (stage0 juga menulis `checksums` milik snapshot; isinya sama, hanya kolom
            # waktu `recorded_at` yang berbeda antar folder, jadi tidak menandai stage0)
            names = {a.name for a in last.outputs if a.name in ARTIFACTS and ARTIFACTS[a.name].stage == task}
            bad = sync[sync["artifact"].isin(names) & (sync["state"] == "tidak sinkron")]
            # artefak tahap ini yang tidak pernah ditulis run eksekusi (mis. task4 --direction hanya menulis
            # direction_preds; forecast_* tetap dari Kaggle) → tahap hanya sebagian dieksekusi di bawah pelacakan
            unexec = sync[(sync["stage"] == task) & sync["state"].isin(["hanya dievaluasi", "tanpa log"])]
            out[task] = ("dieksekusi · output tidak sinkron" if len(bad) else
                         "sebagian dieksekusi" if len(unexec) else "dieksekusi")
        elif ev:
            out[task] = "hanya dievaluasi" if ev[-1].status == "success" else "evaluasi gagal"
        else:
            out[task] = "belum ada run"
    return out
