"""Baca/tulis artefak dengan validasi kolom sesuai ``kagami.utils.artifacts``.

Tulis selalu ke ``cfg.out_dir``; baca dari lokasi pertama yang memuat artefak di ``cfg.read_dirs``
(output sesi ini -> output tahap sebelumnya -> yang ikut kode). D-027.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from kagami.utils.artifacts import ARTIFACTS, Artifact
from kagami.utils.config import Config


class ArtifactMissing(FileNotFoundError):
    pass


def artifact_path(cfg: Config, name: str) -> Path:
    """Lokasi TULIS artefak."""
    return cfg.out_dir / ARTIFACTS[name].path


def find_artifact(cfg: Config, name: str) -> Path | None:
    """Lokasi BACA artefak (None bila belum ada di mana pun)."""
    for d in cfg.read_dirs:
        p = d / ARTIFACTS[name].path
        if p.exists():
            return p
    return None


def exists(cfg: Config, name: str) -> bool:
    return find_artifact(cfg, name) is not None


def _check_columns(art: Artifact, df: pd.DataFrame) -> None:
    missing = [c for c in art.columns if c not in df.columns]
    if missing:
        raise ValueError(f"Artefak '{art.name}' kehilangan kolom wajib: {missing}")


def write_artifact(cfg: Config, name: str, obj: pd.DataFrame | str) -> Path:
    art = ARTIFACTS[name]
    path = artifact_path(cfg, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".md":
        assert isinstance(obj, str), f"{name} harus teks markdown"
        path.write_text(obj, encoding="utf-8")
        return path
    assert isinstance(obj, pd.DataFrame)
    _check_columns(art, obj)
    if path.suffix == ".parquet":
        obj.to_parquet(path, index=False)
    elif path.suffix == ".csv":
        obj.to_csv(path, index=False)
    else:
        raise ValueError(f"Format tidak dikenal: {path.suffix}")
    return path


def read_artifact(cfg: Config, name: str) -> pd.DataFrame | str:
    art = ARTIFACTS[name]
    path = find_artifact(cfg, name)
    if path is None:
        raise ArtifactMissing(f"{name} belum ada ({art.path}) di {[str(d) for d in cfg.read_dirs]}; "
                              f"dihasilkan oleh {art.stage} / {art.wp}")
    if path.suffix == ".md":
        return path.read_text(encoding="utf-8")
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    _check_columns(art, df)
    return df


def require(cfg: Config, *names: str) -> None:
    """Gagal cepat dengan pesan jelas bila artefak input sebuah tahap belum tersedia (dipakai pipelines/notebook)."""
    missing = [n for n in names if not exists(cfg, n)]
    if missing:
        hint = {n: f"{ARTIFACTS[n].stage}/{ARTIFACTS[n].wp}" for n in missing}
        raise ArtifactMissing(f"Input belum ada: {hint}. Jalankan tahap produsennya atau tambahkan outputnya "
                              f"sebagai input (Kaggle) / pastikan ada di folder Drive (Colab).")
