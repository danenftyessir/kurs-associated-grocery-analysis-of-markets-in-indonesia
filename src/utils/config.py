"""Konfigurasi terpusat: lokasi (kode, data mentah, output) + isi configs/*.yaml + tabel referensi tim.

Tiga lokasi dipisah agar pipeline jalan sama di lokal, Kaggle, dan Colab (D-027):
- root     : kode + configs/ + data/reference/ buatan tim (read-only di Kaggle).
- raw_dir  : sumber mentah; path di configs/sources.yaml relatif terhadap folder ini.
- out_dir  : tempat MENULIS artefak (path di utils/artifacts.py relatif terhadap folder ini).
- artifact_dirs : lokasi BACA tambahan untuk artefak tahap sebelumnya (mis. output notebook lain di Kaggle).
Lokal: raw_dir = root/data/raw, out_dir = root. Override: env KAGAMI_ROOT / _RAW_DIR / _OUT_DIR /
_ARTIFACT_DIRS (dipisah os.pathsep), atau `kagami.utils.env.init_runtime`.
Semua modul mengambil parameter dari sini; jangan hard-code angka analisis di modul lain.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def _find_root() -> Path:
    env = os.environ.get("KAGAMI_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "configs" / "params.yaml").exists():
            return parent
    raise FileNotFoundError("Root project tidak ditemukan (configs/params.yaml). Set KAGAMI_ROOT.")


def _env_path(name: str) -> Path | None:
    v = os.environ.get(name)
    return Path(v).resolve() if v else None


def _env_paths(name: str) -> tuple[Path, ...]:
    v = os.environ.get(name, "")
    return tuple(Path(p).resolve() for p in v.split(os.pathsep) if p)


@dataclass(frozen=True)
class Config:
    root: Path = field(default_factory=_find_root)
    raw_root: Path | None = field(default_factory=lambda: _env_path("KAGAMI_RAW_DIR"))
    out_root: Path | None = field(default_factory=lambda: _env_path("KAGAMI_OUT_DIR"))
    artifact_dirs: tuple[Path, ...] = field(default_factory=lambda: _env_paths("KAGAMI_ARTIFACT_DIRS"))

    # ---- lokasi -------------------------------------------------------------
    @property
    def configs_dir(self) -> Path:
        return self.root / "configs"

    @property
    def raw_dir(self) -> Path:
        return self.raw_root or self.root / "data" / "raw"

    @property
    def out_dir(self) -> Path:
        return self.out_root or self.root

    @property
    def reference_dir(self) -> Path:
        """Tabel buatan tim yang ikut kode (region_crosswalk, province_aliases)."""
        return self.root / "data" / "reference"

    @property
    def read_dirs(self) -> tuple[Path, ...]:
        """Urutan pencarian artefak: output sesi ini -> artefak tahap sebelumnya -> yang ikut kode."""
        seen, out = set(), []
        for d in (self.out_dir, *self.artifact_dirs, self.root):
            if d not in seen:
                seen.add(d)
                out.append(d)
        return tuple(out)

    def path(self, rel: str | Path) -> Path:
        """Path relatif terhadap root kode (configs, app, dsb.)."""
        return self.root / rel

    # ---- yaml ---------------------------------------------------------------
    def _yaml(self, name: str) -> dict[str, Any]:
        with open(self.configs_dir / name, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @cached_property
    def params(self) -> dict[str, Any]:
        return self._yaml("params.yaml")

    @cached_property
    def commodities(self) -> dict[str, dict[str, Any]]:
        return self._yaml("commodities.yaml")

    @cached_property
    def sources(self) -> dict[str, dict[str, Any]]:
        return self._yaml("sources.yaml")

    # ---- tabel referensi buatan tim ----------------------------------------
    @cached_property
    def regions(self) -> pd.DataFrame:
        return pd.read_csv(self.reference_dir / "region_crosswalk.csv")

    @cached_property
    def province_aliases(self) -> pd.DataFrame:
        return pd.read_csv(self.reference_dir / "province_aliases.csv")

    # ---- sumber mentah ------------------------------------------------------
    def source_path(self, key: str) -> Path:
        return self.raw_dir / self.sources[key]["path"]

    def source_files(self, key: str) -> list[Path]:
        """File konkret sebuah sumber (mengurai `glob` bila ada)."""
        src, p = self.sources[key], self.source_path(key)
        return sorted(p.glob(src["glob"])) if "glob" in src else [p]

    def commodity_ids(self, role: str | None = None) -> list[str]:
        return [k for k, v in self.commodities.items() if role is None or v["role"] == role]

    @property
    def seed(self) -> int:
        return int(self.params["seed"])


def get_config() -> Config:
    return Config()
