"""Runtime notebook: deteksi platform (lokal / Kaggle / Colab) dan susun Config dengan lokasi yang tepat (D-027, D-100).

| Platform | root (kode)                         | raw_dir                               | out_dir                         | artifact_dirs |
|----------|-------------------------------------|---------------------------------------|---------------------------------|---------------|
| local    | folder project                      | root/data/raw                         | root                            | (kosong)      |
| kaggle   | dataset kode di /kaggle/input/...   | dataset `bi_pihps/` atau /kaggle/temp/kagami_raw (pull) | /kaggle/working                 | input yang memuat results/ atau data/processed|interim/ (cadangan) |
| colab    | DRIVE_DIR (project disalin ke Drive)| DRIVE_DIR/data/raw atau /content/kagami_raw | runtime.yaml colab.out_dir      | (kosong)      |

Input/output antar tahap disinkronkan dengan folder Drive tim lewat `utils.drive.pull/push` (D-100).
Env var KAGAMI_* tetap menang bila diset (lihat utils/config.py).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config
from kagami.utils.io import find_artifact

KAGGLE_INPUT = Path("/kaggle/input")
KAGGLE_WORKING = Path("/kaggle/working")
DEFAULT_DRIVE_DIR = "/content/drive/MyDrive/kagami"


def detect_platform() -> str:
    """kaggle | colab | local. Penanda khas platform (env var) didahulukan: image Colab juga punya folder /kaggle/input,
    sehingga pemeriksaan folder saja salah mengenali Colab sebagai Kaggle (2026-11-21); folder hanya cadangan."""
    if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        return "kaggle"
    if "google.colab" in sys.modules or os.environ.get("COLAB_RELEASE_TAG"):
        return "colab"
    return "kaggle" if KAGGLE_INPUT.exists() else "local"


def _dirs_upto(base: Path, depth: int) -> list[Path]:
    out, frontier = [], [base]
    for _ in range(depth):
        frontier = [c for d in frontier if d.is_dir() for c in sorted(d.iterdir()) if c.is_dir()]
        out += frontier
    return out


def kaggle_raw_dir(base: Path = KAGGLE_INPUT) -> Path | None:
    """Folder input pertama yang berisi `bi_pihps/` (= isi data/raw yang diunggah sebagai dataset privat)."""
    return next((d for d in _dirs_upto(base, 3) if (d / "bi_pihps").is_dir()), None)


def kaggle_artifact_dirs(base: Path = KAGGLE_INPUT) -> tuple[Path, ...]:
    """Input yang memuat artefak (output notebook tahap sebelumnya yang ditambahkan sebagai input)."""
    marks = ("results", "data/processed", "data/interim")
    return tuple(d for d in _dirs_upto(base, 2) if any((d / m).is_dir() for m in marks))


def init_runtime(platform: str | None = None, drive_dir: str = DEFAULT_DRIVE_DIR, verbose: bool = True) -> Config:
    """Bangun Config untuk platform saat ini. Dipanggil sel kedua setiap notebook."""
    platform = platform or detect_platform()
    if platform == "kaggle":
        KAGGLE_WORKING.mkdir(parents=True, exist_ok=True)
        rt = Config().runtime
        raw = kaggle_raw_dir() or Path(rt["kaggle"]["raw_dir"])          # dataset kagami-raw opsional (D-101)
        cfg = Config(raw_root=_env_or("KAGAMI_RAW_DIR", raw),
                     out_root=_env_or("KAGAMI_OUT_DIR", KAGGLE_WORKING),
                     artifact_dirs=kaggle_artifact_dirs())
    elif platform == "colab":
        d = Path(drive_dir)
        rt = Config().runtime
        work = Path(rt["colab"]["out_dir"])   # dibuat otomatis saat artefak pertama ditulis
        raw = d / "data" / "raw" if (d / "data" / "raw").is_dir() else Path(rt["colab"]["raw_dir"])
        cfg = Config(raw_root=_env_or("KAGAMI_RAW_DIR", raw),
                     out_root=_env_or("KAGAMI_OUT_DIR", work))
    elif platform == "local":
        cfg = Config()
    else:
        raise ValueError(f"platform tidak dikenal: {platform}")
    if verbose:
        print(describe(cfg, platform))
    return cfg


def _env_or(name: str, default: Path | None) -> Path | None:
    v = os.environ.get(name)
    return Path(v) if v else default


def describe(cfg: Config, platform: str) -> str:
    raw_ok = cfg.raw_dir.exists()
    lines = [f"platform     : {platform}",
             f"root (kode)  : {cfg.root}",
             f"raw_dir      : {cfg.raw_dir} {'' if raw_ok else '(TIDAK ADA - tahap yang butuh data mentah akan gagal)'}",
             f"out_dir      : {cfg.out_dir}",
             f"artifact_dirs: {[str(d) for d in cfg.artifact_dirs] or '-'}"]
    return "\n".join(lines)


def artifact_status(cfg: Config, stage: str | None = None) -> pd.DataFrame:
    """Tabel artefak (opsional satu tahap): ada/tidak, lokasi baca, WP produsen. Dipakai notebook & CLI status."""
    rows = []
    for a in ARTIFACTS.values():
        if stage and a.stage != stage:
            continue
        p = find_artifact(cfg, a.name)
        rows.append({"artifact": a.name, "stage": a.stage, "wp": a.wp, "ship": a.ship,
                     "available": p is not None, "location": str(p) if p else ""})
    return pd.DataFrame(rows)
