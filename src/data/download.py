"""Pengunduh ulang sumber mentah (Tingkat C, proposal §7.3).

- retrieval == http   : diunduh ke data/raw/_redownload/<key>/ lalu hash dibandingkan dengan checksums.csv.
- retrieval == manual : dicetak instruksi (URL + nama file tujuan); tidak ada scraping endpoint tidak resmi.
File snapshot tim tidak pernah ditimpa (raw_dir bisa read-only, mis. Kaggle).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

from kagami.utils.config import Config
from kagami.utils.io import artifact_path
from kagami.data.snapshot import sha256_file


def download(cfg: Config, key: str) -> Path | None:
    src = cfg.sources[key]
    if src["retrieval"] != "http":
        print(f"[download] {key}: unduh manual dari {src['url'] or '(lihat docs/DATASETS.md)'} "
              f"-> simpan sebagai snapshot baru di {(cfg.raw_dir / src['path']).parent}/ lalu jalankan `snapshot`.")
        return None
    dest_dir = cfg.out_dir / "data" / "raw" / "_redownload" / key
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / Path(src["path"]).name
    req = urllib.request.Request(src["url"], headers={"User-Agent": "kagami-research"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    _compare(cfg, key, dest)
    return dest


def _compare(cfg: Config, key: str, new_file: Path) -> None:
    ck = artifact_path(cfg, "checksums")
    if not ck.exists():
        print(f"[download] {key}: checksums.csv belum ada; jalankan `snapshot` dulu.")
        return
    prev = pd.read_csv(ck)
    old = prev.loc[prev["source"] == key, "sha256"]
    new = sha256_file(new_file)
    same = (not old.empty) and new == old.iloc[0]
    print(f"[download] {key}: {'IDENTIK' if same else 'BERBEDA (revisi sumber? catat di docs/DATASETS.md)'} "
          f"sha256={new[:12]}...")


def run(cfg: Config, sources: list[str] | None = None) -> None:
    for key in sources or list(cfg.sources):
        download(cfg, key)
