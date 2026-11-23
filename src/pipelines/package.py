"""Paket zip (WP-32 dan runtime notebook, D-027).

- submission()  : zip juri berbasis allowlist + flag `ship` & `redistribute` (proposal §7.2).
- code_bundle() : kode + configs + tabel referensi + notebook -> diunggah sebagai dataset Kaggle `kagami-code`
                  atau disalin ke Google Drive (Colab). Tanpa data mentah dan tanpa artefak.
- raw_bundle()  : isi cfg.raw_dir -> dataset Kaggle PRIVAT `kagami-raw`. JANGAN dipublikasikan (hak data BI/BPS).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config

CODE_GLOBS = ("pyproject.toml", "requirements.txt", "README.md", "configs/*.yaml", "src/**/*.py", "data/reference/*.csv",
              "data/reference/*.geojson", "notebooks/*.ipynb")
SUBMISSION_GLOBS = CODE_GLOBS + ("app/**/*.py", ".streamlit/config.toml", "tests/**/*.py", "docs/*.md",
                                 "logs/*/*.json")   # log eksekusi & evaluasi (WP-36): app hal. 7 terisi di Tingkat A


def _code_files(cfg: Config, globs: tuple[str, ...]) -> dict[Path, str]:
    files = {}
    for pattern in globs:
        for p in cfg.root.glob(pattern):
            if p.is_file() and "__pycache__" not in p.parts:
                files[p] = p.relative_to(cfg.root).as_posix()
    return files


def _write_zip(dest: Path, files: dict[Path, str]) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arc in sorted(files.items(), key=lambda kv: kv[1]):
            zf.write(src, arc)
    return dest


def collect_submission(cfg: Config) -> tuple[dict[Path, str], list[str]]:
    """File zip juri + daftar artefak ship=True yang belum ada (harus kosong saat G7)."""
    files = _code_files(cfg, SUBMISSION_GLOBS)
    missing = []
    for art in ARTIFACTS.values():
        if not art.ship:
            continue
        p = next((d / art.path for d in cfg.read_dirs if (d / art.path).exists()), None)
        if p is None:
            missing.append(art.name)
        else:
            files[p] = art.path
    for key, src in cfg.sources.items():          # mentah yang boleh diredistribusi (CC BY 4.0 / domain publik)
        if src["redistribute"]:
            for f in cfg.source_files(key):
                if f.exists():
                    files[f] = "data/raw/" + f.relative_to(cfg.raw_dir).as_posix()
    return files, missing


def submission(cfg: Config, allow_missing: bool = False) -> Path:
    files, missing = collect_submission(cfg)
    if missing and not allow_missing:
        raise SystemExit(f"[package] artefak ship belum ada: {missing}. Jalankan pipeline atau --allow-missing.")
    dest = _write_zip(cfg.out_dir / "dist" / "kagami_submission.zip", files)
    print(f"[package] {len(files)} file -> {dest}; hilang: {missing or '-'}")
    return dest


def code_bundle(cfg: Config) -> Path:
    files = _code_files(cfg, CODE_GLOBS)
    dest = _write_zip(cfg.out_dir / "dist" / "kagami_code.zip", files)
    print(f"[bundle] kode: {len(files)} file -> {dest}  (unggah sebagai dataset Kaggle 'kagami-code')")
    return dest


def raw_bundle(cfg: Config) -> Path:
    files = {f: f.relative_to(cfg.raw_dir).as_posix()
             for key in cfg.sources for f in cfg.source_files(key) if f.exists()}
    ck = cfg.out_dir / ARTIFACTS["checksums"].path
    if ck.exists():
        files[ck] = "checksums.csv"
    dest = _write_zip(cfg.out_dir / "dist" / "kagami_raw_PRIVATE.zip", files)
    print(f"[bundle] mentah: {len(files)} file -> {dest}  (dataset Kaggle PRIVAT 'kagami-raw'; jangan publik)")
    return dest
