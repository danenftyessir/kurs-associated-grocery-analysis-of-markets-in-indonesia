"""WP-36. Skema log eksekusi & evaluasi (JSON). Tiga jenis file terpisah per run (D-137):

- logs/runs/<run_id>.json         RunRecord      : metadata eksekusi (status, waktu, lineage, parameter)
- logs/evaluations/<run_id>.json  EvaluationRecord: daftar Metric (nilai + status + alasan + konteks data)
- logs/errors/<run_id>.json       ErrorRecord    : hanya bila run gagal (tipe, pesan, traceback)
- logs/pipelines/<pipeline_id>.json : ringkasan satu `kagami all` (urutan run & status)

Path di dalam log selalu relatif (path artefak registry + label lokasi), tanpa nama host/pengguna.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any

SCHEMA_VERSION = 1
STATUSES = ("success", "failed")
RUN_TYPES = ("execution", "evaluation")          # evaluation = evaluasi artefak yang ada tanpa menjalankan ulang
METRIC_STATUSES = ("ok", "not_applicable", "failed")


@dataclass
class ArtifactRef:
    name: str
    path: str                                    # relatif out_dir/root (registry), bukan path absolut
    location: str                                # out_dir | artifact_dir | root
    sha256: str
    bytes: int
    rows: int | None = None
    columns: int | None = None
    missing_cells: int | None = None
    memory_mb: float | None = None
    producer_run_id: str | None = None           # hanya input: run yang menulis file dengan hash yang sama


@dataclass
class Metric:
    name: str
    group: str
    value: Any = None                            # angka / teks / list (mis. ukuran klaster); None bila tidak ok
    status: str = "ok"
    reason: str | None = None                    # wajib bila status != ok
    context: dict[str, Any] = field(default_factory=dict)   # artefak sumber, subset, n, catatan

    def __post_init__(self) -> None:
        if self.status not in METRIC_STATUSES:
            raise ValueError(f"status metrik tidak dikenal: {self.status}")
        if self.status != "ok" and not self.reason:
            raise ValueError(f"metrik {self.name} berstatus {self.status} wajib punya alasan")


@dataclass
class RunRecord:
    run_id: str
    task_id: str
    run_type: str
    status: str
    started_at: str
    finished_at: str | None = None
    duration_s: float | None = None              # None untuk run_type evaluation (eksekusi tidak diamati)
    evaluation_s: float | None = None
    pipeline_id: str | None = None
    parent_run_ids: list[str] = field(default_factory=list)
    dataset_id: str | None = None
    platform: str | None = None
    python: str | None = None
    git_commit: str | None = None
    git_branch: str | None = None
    config_sha256: dict[str, str] = field(default_factory=dict)
    kind: str | None = None
    algorithms: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    call_args: dict[str, Any] = field(default_factory=dict)
    inputs: list[ArtifactRef] = field(default_factory=list)
    outputs: list[ArtifactRef] = field(default_factory=list)
    peak_rss_mb: float | None = None
    error_type: str | None = None
    note: str | None = None
    schema_version: int = SCHEMA_VERSION


@dataclass
class ErrorRecord:
    run_id: str
    task_id: str
    at: str
    error_type: str
    message: str
    traceback: str


@dataclass
class EvaluationRecord:
    run_id: str
    task_id: str
    evaluated_at: str
    metrics: list[Metric] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


def to_dict(obj: Any) -> dict[str, Any]:
    """Dataclass → dict siap JSON."""
    return asdict(obj)


def run_from_dict(d: dict[str, Any]) -> RunRecord:
    """dict JSON → RunRecord (kunci yang tidak dikenal diabaikan agar log versi lain tetap terbaca)."""
    known = {f.name for f in fields(RunRecord)}
    kw = {k: v for k, v in d.items() if k in known}
    for key in ("inputs", "outputs"):
        kw[key] = [ArtifactRef(**{k: v for k, v in a.items() if k in {f.name for f in fields(ArtifactRef)}})
                   for a in kw.get(key, [])]
    return RunRecord(**kw)


def metric_from_dict(d: dict[str, Any]) -> Metric:
    known = {f.name for f in fields(Metric)}
    return Metric(**{k: v for k, v in d.items() if k in known})
