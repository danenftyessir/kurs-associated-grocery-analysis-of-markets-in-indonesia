"""Sinkronisasi artefak dengan folder Google Drive tim (D-100). Lapisan utils; tidak bergantung pada pipelines.

Folder dirujuk lewat ID (`configs/runtime.yaml: drive.folder_id`), jadi sama untuk semua anggota & platform.
Struktur di Drive mencerminkan path artefak relatif out_dir (mis. `results/task1/profiles.parquet`).

- `pull(cfg, names)`  : unduh artefak input dari Drive ke cfg.out_dir (awal notebook / `python -m kagami drive-pull`).
- `push(cfg, stages)` : unggah artefak hasil tahap-tahap itu dari cfg.out_dir ke Drive (akhir notebook / `drive-push`).
- `push_raw(cfg)`     : unggah semua file sumber mentah (configs/sources.yaml) + checksums ke `data/raw/` di Drive;
                        file yang MD5-nya sama dilewati (Danen, `python -m kagami drive-push-raw`).
- `pull_raw(cfg)`     : unduh file sumber mentah yang BELUM ada di cfg.raw_dir (tidak pernah menimpa; notebook 00 /
                        `python -m kagami drive-pull-raw`). D-101.
- Kredensial: Colab = login Google interaktif; Kaggle = Kaggle Secret `KAGAMI_DRIVE_TOKEN`; lokal = file token.
  Token dibuat sekali dengan `python -m kagami drive-auth --client-secret <client_secret.json>`.
- Library Google (`googleapiclient`, `google-auth`) diimpor malas: sudah ada di Kaggle & Colab; lokal `pip install -e ".[drive]"`.
"""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Iterable, Protocol

from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config
from kagami.utils.env import detect_platform
from kagami.utils.io import artifact_path

FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveUnavailable(RuntimeError):
    """Kredensial/library Drive tidak tersedia."""


class DriveClient(Protocol):
    def find(self, parent_id: str, name: str) -> str | None: ...
    def ensure_folder(self, parent_id: str, name: str) -> str: ...
    def upload(self, local: Path, parent_id: str, name: str, existing_id: str | None) -> str: ...
    def download(self, file_id: str, dest: Path) -> None: ...
    def md5(self, file_id: str) -> str | None: ...
    def list(self, parent_id: str) -> list[tuple[str, str]]: ...


class GoogleDriveClient:
    """Pembungkus tipis Drive API v3 (mendukung shared drive)."""

    def __init__(self, service):
        self.s = service

    def find(self, parent_id: str, name: str) -> str | None:
        safe = name.replace("\\", "\\\\").replace("'", "\\'")
        res = self.s.files().list(q=f"'{parent_id}' in parents and name = '{safe}' and trashed = false",
                                  fields="files(id, name)", supportsAllDrives=True,
                                  includeItemsFromAllDrives=True).execute()
        files = res.get("files", [])
        return files[0]["id"] if files else None

    def ensure_folder(self, parent_id: str, name: str) -> str:
        found = self.find(parent_id, name)
        if found:
            return found
        body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
        return self.s.files().create(body=body, fields="id", supportsAllDrives=True).execute()["id"]

    def upload(self, local: Path, parent_id: str, name: str, existing_id: str | None) -> str:
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(str(local), resumable=True)
        if existing_id:
            return self.s.files().update(fileId=existing_id, media_body=media, fields="id",
                                         supportsAllDrives=True).execute()["id"]
        return self.s.files().create(body={"name": name, "parents": [parent_id]}, media_body=media, fields="id",
                                     supportsAllDrives=True).execute()["id"]

    def download(self, file_id: str, dest: Path) -> None:
        from googleapiclient.http import MediaIoBaseDownload
        dest.parent.mkdir(parents=True, exist_ok=True)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, self.s.files().get_media(fileId=file_id, supportsAllDrives=True))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        dest.write_bytes(buf.getvalue())

    def md5(self, file_id: str) -> str | None:
        return self.s.files().get(fileId=file_id, fields="md5Checksum", supportsAllDrives=True).execute().get("md5Checksum")

    def list(self, parent_id: str) -> list[tuple[str, str]]:
        out, token = [], None
        while True:
            res = self.s.files().list(q=f"'{parent_id}' in parents and trashed = false", fields="nextPageToken, files(id, name)",
                                      supportsAllDrives=True, includeItemsFromAllDrives=True, pageToken=token).execute()
            out += [(f["id"], f["name"]) for f in res.get("files", [])]
            token = res.get("nextPageToken")
            if not token:
                return out


# --------------------------------------------------------------------------- kredensial & koneksi
def _token_file(cfg: Config) -> Path:
    return Path(os.environ.get("KAGAMI_DRIVE_TOKEN_FILE") or cfg.runtime["drive"]["token_file"]).expanduser()


def credentials(cfg: Config, platform: str | None = None):
    """Kredensial Google untuk Drive API menurut platform; DriveUnavailable bila tidak ada."""
    platform = platform or detect_platform()
    scopes = cfg.runtime["drive"]["scopes"]
    try:
        if platform == "colab":
            from google.colab import auth  # type: ignore
            import google.auth
            auth.authenticate_user()
            return google.auth.default(scopes=scopes)[0]
        from google.oauth2.credentials import Credentials
        if platform == "kaggle":
            from kaggle_secrets import UserSecretsClient  # type: ignore
            info = json.loads(UserSecretsClient().get_secret(cfg.runtime["drive"]["token_secret"]))
            return Credentials.from_authorized_user_info(info, scopes)
        path = _token_file(cfg)
        if not path.exists():
            raise DriveUnavailable(f"token Drive tidak ada di {path}; jalankan `python -m kagami drive-auth`")
        return Credentials.from_authorized_user_file(str(path), scopes)
    except ImportError as e:
        raise DriveUnavailable(f"library Google belum terpasang ({e.name}); lokal: pip install -e \".[drive]\"") from e
    except DriveUnavailable:
        raise
    except Exception as e:  # secret tidak ada, token kadaluarsa, dsb.
        raise DriveUnavailable(f"kredensial Drive gagal dimuat di {platform}: {e}") from e


def connect(cfg: Config, platform: str | None = None) -> GoogleDriveClient:
    try:
        from googleapiclient.discovery import build
    except ImportError as e:
        raise DriveUnavailable("googleapiclient belum terpasang; lokal: pip install -e \".[drive]\"") from e
    return GoogleDriveClient(build("drive", "v3", credentials=credentials(cfg, platform), cache_discovery=False))


def _client_or_skip(cfg: Config, client: DriveClient | None, strict: bool) -> DriveClient | None:
    if client is not None:
        return client
    try:
        return connect(cfg)
    except DriveUnavailable as e:
        if strict:
            raise
        print(f"[drive] dilewati: {e}")
        return None


def _resolve(client: DriveClient, root_id: str, rel: str, create: bool) -> tuple[str | None, str]:
    """(id folder induk, nama file) untuk path relatif; None bila folder belum ada dan create=False."""
    *dirs, name = Path(rel).parts
    parent = root_id
    for d in dirs:
        parent = client.ensure_folder(parent, d) if create else client.find(parent, d)
        if parent is None:
            return None, name
    return parent, name


# --------------------------------------------------------------------------- operasi utama
def pull(cfg: Config, names: Iterable[str], client: DriveClient | None = None, strict: bool | None = None) -> list[str]:
    """Unduh artefak `names` dari folder Drive tim ke cfg.out_dir. Return daftar path yang diunduh.

    strict (default: True di Kaggle/Colab, False di lokal): bila Drive tidak tersedia -> error / dilewati.
    Artefak yang belum ada di Drive dilaporkan, bukan error (pemeriksaan wajib tetap lewat `utils.io.require`).
    """
    names = list(names)
    strict = detect_platform() != "local" if strict is None else strict
    c = _client_or_skip(cfg, client, strict)
    if c is None or not names:
        return []
    root, got, missing = cfg.runtime["drive"]["folder_id"], [], []
    for n in names:
        rel = ARTIFACTS[n].path
        parent, fname = _resolve(c, root, rel, create=False)
        fid = c.find(parent, fname) if parent else None
        if fid is None:
            missing.append(n)
            continue
        c.download(fid, cfg.out_dir / rel)
        got.append(rel)
    print(f"[drive] pull {len(got)} artefak -> {cfg.out_dir}" + (f"; belum ada di Drive: {missing}" if missing else ""))
    return got


def push(cfg: Config, stages: Iterable[str], client: DriveClient | None = None, strict: bool | None = None) -> list[str]:
    """Unggah semua artefak milik `stages` (registry) yang ada di cfg.out_dir ke folder Drive tim (timpa versi lama)."""
    stages = set(stages)
    strict = detect_platform() != "local" if strict is None else strict
    c = _client_or_skip(cfg, client, strict)
    if c is None:
        return []
    root, sent = cfg.runtime["drive"]["folder_id"], []
    for art in ARTIFACTS.values():
        local = artifact_path(cfg, art.name)
        if art.stage not in stages or not local.exists():
            continue
        parent, fname = _resolve(c, root, art.path, create=True)
        c.upload(local, parent, fname, c.find(parent, fname))
        sent.append(art.path)
    print(f"[drive] push {len(sent)} artefak ({', '.join(sorted(stages))}) -> {cfg.runtime['drive']['folder_url']}")
    return sent


def authorize_local(cfg: Config, client_secret: str | Path) -> Path:
    """Sekali per anggota (lokal): OAuth di browser -> simpan token JSON (isi untuk Kaggle Secret KAGAMI_DRIVE_TOKEN)."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as e:
        raise DriveUnavailable("google-auth-oauthlib belum terpasang; pip install -e \".[drive]\"") from e
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), cfg.runtime["drive"]["scopes"])
    creds = flow.run_local_server(port=0)
    path = _token_file(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
    print(f"[drive] token tersimpan di {path}. Kaggle: Add-ons → Secrets → '{cfg.runtime['drive']['token_secret']}' "
          f"= isi file ini. JANGAN di-commit/dibagikan (akses penuh ke Drive Anda).")
    return path


# --------------------------------------------------------------------------- data mentah (D-101)
RAW_PREFIX = "data/raw"


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def push_raw(cfg: Config, client: DriveClient | None = None, strict: bool | None = None) -> tuple[list[str], list[str]]:
    """Unggah semua file sumber (sources.yaml) + checksums.csv ke `data/raw/` folder Drive tim.

    File yang sudah ada di Drive dengan MD5 sama dilewati. Return (diunggah, dilewati) sebagai path relatif.
    """
    strict = detect_platform() != "local" if strict is None else strict
    c = _client_or_skip(cfg, client, strict)
    if c is None:
        return [], []
    files = {f: f.relative_to(cfg.raw_dir).as_posix() for key in cfg.sources for f in cfg.source_files(key) if f.exists()}
    ck = artifact_path(cfg, "checksums")
    if ck.exists():
        files[ck] = "checksums.csv"
    root, sent, skipped = cfg.runtime["drive"]["folder_id"], [], []
    for local, rel in sorted(files.items(), key=lambda kv: kv[1]):
        parent, fname = _resolve(c, root, f"{RAW_PREFIX}/{rel}", create=True)
        existing = c.find(parent, fname)
        if existing and c.md5(existing) == _md5_file(local):
            skipped.append(rel)
            continue
        c.upload(local, parent, fname, existing)
        sent.append(rel)
    print(f"[drive] push-raw: {len(sent)} diunggah, {len(skipped)} tidak berubah -> {cfg.runtime['drive']['folder_url']}")
    return sent, skipped


def pull_raw(cfg: Config, client: DriveClient | None = None, strict: bool | None = None) -> list[str]:
    """Unduh file sumber mentah yang belum ada di cfg.raw_dir dari `data/raw/` folder Drive tim (tidak menimpa)."""
    strict = detect_platform() != "local" if strict is None else strict
    c = _client_or_skip(cfg, client, strict)
    if c is None:
        return []
    root, got, missing = cfg.runtime["drive"]["folder_id"], [], []
    for key, src in cfg.sources.items():
        parent, name = _resolve(c, root, f"{RAW_PREFIX}/{src['path']}", create=False)
        if "glob" in src:                                   # sumber berupa folder + pola nama file
            folder = c.find(parent, name) if parent else None
            entries = [(i, n) for i, n in (c.list(folder) if folder else []) if fnmatch.fnmatch(n, src["glob"])]
            targets = [(i, cfg.source_path(key) / n) for i, n in entries]
        else:
            fid = c.find(parent, name) if parent else None
            targets = [(fid, cfg.source_path(key))]
        for fid, dest in targets:
            if dest.exists():
                continue
            if fid is None:
                missing.append(key)
                continue
            c.download(fid, dest)
            got.append(dest.relative_to(cfg.raw_dir).as_posix())
    print(f"[drive] pull-raw: {len(got)} file -> {cfg.raw_dir}" + (f"; belum ada di Drive: {sorted(set(missing))}" if missing else ""))
    return got
