"""Snapshot mentah ber-hash (WP-01). Menulis data/raw/checksums.csv.

Kolom `file` relatif terhadap raw_dir. Aturan: file mentah tidak pernah ditimpa. Snapshot baru = file baru (nama memuat tanggal ambil)
+ baris baru di checksums.csv. Tingkat C membandingkan hash unduhan ulang dengan file ini.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from kagami.utils.config import Config
from kagami.utils.io import artifact_path, write_artifact


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def build_checksums(cfg: Config) -> pd.DataFrame:
    """Hash setiap file sumber. retrieved_at = mtime file (waktu unduh lokal) kecuali sudah tercatat."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prev_path = artifact_path(cfg, "checksums")
    prev = pd.read_csv(prev_path) if prev_path.exists() else None
    rows = []
    for key in cfg.sources:
        for f in cfg.source_files(key):
            if not f.exists():
                rows.append(dict(source=key, file=f.relative_to(cfg.raw_dir).as_posix(), bytes=None,
                                 sha256="MISSING", retrieved_at=None, recorded_at=now))
                continue
            rel = f.relative_to(cfg.raw_dir).as_posix()  # relatif raw_dir
            digest = sha256_file(f)
            retrieved = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
            recorded = now
            if prev is not None:
                hit = prev[(prev["file"] == rel) & (prev["sha256"] == digest)]
                if len(hit):  # hash sama -> pertahankan waktu catatan pertama
                    retrieved, recorded = hit.iloc[0]["retrieved_at"], hit.iloc[0]["recorded_at"]
            rows.append(dict(source=key, file=rel, bytes=f.stat().st_size, sha256=digest,
                             retrieved_at=retrieved, recorded_at=recorded))
    return pd.DataFrame(rows)


def run(cfg: Config) -> None:
    df = build_checksums(cfg)
    path = write_artifact(cfg, "checksums", df)
    missing = df[df["sha256"] == "MISSING"]
    print(f"[snapshot] {len(df)} file -> {path}")
    if len(missing):
        print(f"[snapshot] HILANG: {missing['file'].tolist()}")
