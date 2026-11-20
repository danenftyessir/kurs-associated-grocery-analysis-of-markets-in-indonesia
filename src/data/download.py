"""Pengunduh ulang sumber mentah (Tingkat C, proposal §7.3).

- retrieval == http   : diunduh ke data/raw/_redownload/<key>/ lalu hash dibandingkan dengan checksums.csv.
                        Bila sumber punya `landing_url` + `link_pattern` (mis. Pink Sheet, URL berubah tiap rilis),
                        tautan terbaru dicari di halaman itu; `url` dipakai bila tidak ditemukan.
- retrieval == manual : dicetak instruksi (URL + nama file tujuan); tidak ada scraping endpoint tidak resmi.
File snapshot tim tidak pernah ditimpa (raw_dir bisa read-only, mis. Kaggle).
"""

from __future__ import annotations

import re
import ssl
import urllib.request
from pathlib import Path

import pandas as pd

from kagami.utils.config import Config
from kagami.utils.io import artifact_path
from kagami.data.snapshot import sha256_file


def _ssl_context() -> ssl.SSLContext:
    """Verifikasi SSL tetap aktif; pakai bundel CA certifi bila ada (Python Windows sering tanpa CA lokal)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": "kagami-research"})


def find_link(html: str, pattern: str) -> str | None:
    """Tautan pertama di `html` yang cocok `pattern` (dipisah agar bisa dites tanpa jaringan)."""
    m = re.search(pattern, html)
    return m.group(0) if m else None


def resolve_url(src: dict) -> str:
    """URL unduhan: tautan terbaru dari `landing_url` bila ada pola, selain itu `url` statis."""
    if src.get("landing_url") and src.get("link_pattern"):
        try:
            with urllib.request.urlopen(_request(src["landing_url"]), timeout=60, context=_ssl_context()) as r:
                found = find_link(r.read().decode("utf-8", "replace"), src["link_pattern"])
            if found:
                return found
            print(f"[download] tautan tidak ditemukan di {src['landing_url']}; pakai url cadangan")
        except OSError as e:
            print(f"[download] gagal membuka {src['landing_url']} ({e}); pakai url cadangan")
    return src["url"]


def download(cfg: Config, key: str) -> Path | None:
    src = cfg.sources[key]
    if src["retrieval"] != "http":
        print(f"[download] {key}: unduh manual dari {src['url'] or '(lihat docs/DATASETS.md)'} "
              f"-> simpan sebagai snapshot baru di {(cfg.raw_dir / src['path']).parent}/ lalu jalankan `snapshot`.")
        return None
    dest_dir = cfg.out_dir / "data" / "raw" / "_redownload" / key
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / Path(src["path"]).name
    url = resolve_url(src)
    with urllib.request.urlopen(_request(url), timeout=120, context=_ssl_context()) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(f"[download] {key}: {url}")
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
