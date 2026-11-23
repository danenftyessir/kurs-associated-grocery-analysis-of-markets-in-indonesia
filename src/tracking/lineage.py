"""WP-36. Lineage artefak: sha256 input/output setiap run, perekam baca/tulis (pengamat `utils.io`), pencarian run
induk lewat kecocokan hash, identitas dataset, versi config, commit git, memori puncak.

Run induk = run sukses terakhir yang MENULIS file dengan sha256 yang sama dengan input yang dibaca run ini. Karena itu
hubungan antar-tahap mengikuti data yang benar-benar dipakai (bukan urutan waktu), juga lintas lokal/Kaggle/Colab
selama log ikut ditarik (drive.pull_logs).
"""

from __future__ import annotations

import hashlib
import platform as _platform
import sys
from pathlib import Path

import pandas as pd

from kagami.data.snapshot import sha256_file
from kagami.tracking.metrics import data_profile
from kagami.tracking.schemas import ArtifactRef, RunRecord
from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config


def location_label(cfg: Config, path: Path) -> str:
    """out_dir | artifact_dir | root | other (label saja; path absolut tidak pernah dicatat)."""
    p = Path(path).resolve()
    for label, dirs in (("out_dir", [cfg.out_dir]), ("artifact_dir", list(cfg.artifact_dirs)), ("root", [cfg.root])):
        for d in dirs:
            try:
                p.relative_to(Path(d).resolve())
                return label
            except ValueError:
                continue
    return "other"


def artifact_ref(cfg: Config, name: str, path: Path, profile: bool = True, sha256: str | None = None,
                 size: int | None = None) -> ArtifactRef:
    """ArtifactRef untuk satu file artefak: hash, ukuran, dan (tabel, bila profile) baris/kolom/sel kosong/memori.
    sha256/size boleh diberikan (hash saat dibaca, sebelum file mungkin ditulis ulang oleh run yang sama)."""
    path = Path(path)
    ref = ArtifactRef(name=name, path=ARTIFACTS[name].path if name in ARTIFACTS else path.name,
                      location=location_label(cfg, path), sha256=sha256 or sha256_file(path),
                      bytes=size if size is not None else path.stat().st_size)
    if profile and path.suffix in (".parquet", ".csv"):
        try:
            df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
            for k, v in data_profile(df).items():
                setattr(ref, k, v)
        except Exception as exc:  # noqa: BLE001 -- profil gagal tidak menggagalkan log
            print(f"[tracking] profil {name} gagal: {exc}")
    return ref


class Recorder:
    """Pengamat `utils.io`: catat artefak yang dibaca (di-hash SAAT dibaca, karena run yang sama bisa menulisnya ulang,
    mis. checkpoint bootstrap Task 1) dan yang ditulis (di-hash di akhir run)."""

    def __init__(self) -> None:
        self.reads: dict[str, tuple[Path, str, int]] = {}
        self.writes: dict[str, Path] = {}

    def observe(self, event: str, name: str, path: Path) -> None:
        path = Path(path)
        if event == "read" and name not in self.writes and name not in self.reads:
            self.reads[name] = (path, sha256_file(path), path.stat().st_size)
        elif event == "write":
            self.writes[name] = path


def producer_index(runs: list[RunRecord]) -> dict[str, str]:
    """sha256 → run_id run sukses TERAKHIR (menurut started_at) yang mencantumkan file itu sebagai output."""
    idx: dict[str, tuple[str, str]] = {}
    for r in runs:
        if r.status != "success":
            continue
        for a in r.outputs:
            prev = idx.get(a.sha256)
            if prev is None or r.started_at > prev[0]:
                idx[a.sha256] = (r.started_at, r.run_id)
    return {sha: rid for sha, (_, rid) in idx.items()}


def link_parents(inputs: list[ArtifactRef], runs: list[RunRecord], exclude: str | None = None) -> list[str]:
    """Isi producer_run_id setiap input; kembalikan daftar run induk unik (urutan kemunculan)."""
    idx = producer_index([r for r in runs if r.run_id != exclude])
    parents: list[str] = []
    for a in inputs:
        a.producer_run_id = idx.get(a.sha256)
        if a.producer_run_id and a.producer_run_id not in parents:
            parents.append(a.producer_run_id)
    return parents


def raw_snapshot_id(checksums: pd.DataFrame) -> str:
    """`raw:<12 heks>` dari pasangan (file, sha256) snapshot mentah saja: kolom waktu (`recorded_at`, `retrieved_at`) tidak
    ikut, jadi snapshot yang isinya sama memberi ID sama walau checksums.csv ditulis ulang di folder lain."""
    pairs = sorted(f"{f}\t{h}" for f, h in zip(checksums["file"].astype(str), checksums["sha256"].astype(str)))
    return "raw:" + hashlib.sha256("\n".join(pairs).encode()).hexdigest()[:12]


def dataset_id(cfg: Config, inputs: list[ArtifactRef], parent_runs: list[RunRecord]) -> str:
    """Identitas dataset: snapshot mentah (`checksums`, isi file saja) bila ada; selain itu warisan run induk; selain itu
    hash input."""
    from kagami.utils.io import find_artifact   # impor lokal: hindari siklus saat io memuat pengamat

    ck = find_artifact(cfg, "checksums")
    if ck is not None:
        return raw_snapshot_id(pd.read_csv(ck))
    for r in parent_runs:
        if r.dataset_id:
            return r.dataset_id
    if inputs:
        h = hashlib.sha256("".join(sorted(a.sha256 for a in inputs)).encode()).hexdigest()
        return "in:" + h[:12]
    return "unknown"


def config_hashes(cfg: Config) -> dict[str, str]:
    """sha256 file config analisis (params.yaml dibekukan di G6; pembanding dengan PREREGISTRATION)."""
    out = {}
    for name in ("params.yaml", "commodities.yaml"):
        p = cfg.configs_dir / name
        if p.exists():
            out[name] = sha256_file(p)
    return out


def git_info(root: Path) -> tuple[str | None, str | None]:
    """(commit, branch) dari folder .git tanpa menjalankan git; (None, None) di Kaggle/Colab tanpa repo."""
    g = Path(root) / ".git"
    head = g / "HEAD"
    if not head.is_file():
        return None, None
    txt = head.read_text(encoding="utf-8").strip()
    if not txt.startswith("ref:"):
        return txt[:40], None
    ref = txt.split(" ", 1)[1].strip()
    branch = ref.rsplit("/", 1)[-1]
    f = g / ref
    if f.is_file():
        return f.read_text(encoding="utf-8").strip()[:40], branch
    packed = g / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line.endswith(" " + ref):
                return line.split(" ", 1)[0][:40], branch
    return None, branch


def peak_rss_mb() -> float | None:
    """Memori puncak proses (MB) sampai saat ini: psutil (Windows peak_wset) atau resource (Linux); None bila tak ada."""
    try:
        import psutil

        mi = psutil.Process().memory_info()
        peak = getattr(mi, "peak_wset", None)
        if peak:
            return round(peak / 2 ** 20, 1)
    except Exception:  # noqa: BLE001
        pass
    try:
        import resource

        kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round((kb / 2 ** 20 if sys.platform == "darwin" else kb / 2 ** 10), 1)
    except Exception:  # noqa: BLE001
        return None


def python_version() -> str:
    return _platform.python_version()
