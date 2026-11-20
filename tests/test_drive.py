"""D-100: sinkronisasi artefak dengan folder Drive tim (pakai Drive palsu di memori; tanpa jaringan/library Google)."""

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from kagami.utils import drive
from kagami.utils.config import Config
from kagami.utils.io import read_artifact, write_artifact


class FakeDrive:
    """Implementasi DriveClient di memori: id -> (parent, name, folder?, bytes)."""

    def __init__(self, root_id: str):
        self.nodes = {root_id: (None, "root", True, b"")}
        self.uploads = 0

    def _new_id(self) -> str:
        return f"id{len(self.nodes)}"

    def find(self, parent_id, name):
        hits = [i for i, (p, n, _, _) in self.nodes.items() if p == parent_id and n == name]
        return hits[0] if hits else None

    def ensure_folder(self, parent_id, name):
        found = self.find(parent_id, name)
        if found:
            return found
        i = self._new_id()
        self.nodes[i] = (parent_id, name, True, b"")
        return i

    def upload(self, local: Path, parent_id, name, existing_id):
        self.uploads += 1
        i = existing_id or self._new_id()
        self.nodes[i] = (parent_id, name, False, local.read_bytes())
        return i

    def download(self, file_id, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.nodes[file_id][3])

    def md5(self, file_id):
        return hashlib.md5(self.nodes[file_id][3]).hexdigest()

    def list(self, parent_id):
        return [(i, n) for i, (p, n, _, _) in self.nodes.items() if p == parent_id]

    def files_named(self, name):
        return [i for i, (_, n, folder, _) in self.nodes.items() if n == name and not folder]


def _episodes(v=0.12):
    return pd.DataFrame({"episode_id": [1], "start_week": ["2020-03-02"], "end_week": ["2020-04-27"],
                         "cum_dlog_e": [v]})


@pytest.fixture
def fake(cfg):
    return FakeDrive(cfg.runtime["drive"]["folder_id"])


def test_runtime_config_has_team_folder(cfg):
    d = cfg.runtime["drive"]
    assert d["folder_id"] == "15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D" and d["folder_id"] in d["folder_url"]
    assert d["token_secret"] and d["scopes"]


def test_push_mirrors_paths_and_overwrites(cfg, fake, tmp_path):
    producer = Config(root=cfg.root, out_root=tmp_path / "danen")
    write_artifact(producer, "episodes", _episodes(0.12))
    sent = drive.push(producer, ["stage0"], client=fake)
    assert sent == ["results/stage0/episodes.csv"]
    folders = [n for _, n, f, _ in fake.nodes.values() if f]
    assert {"results", "stage0"} <= set(folders)
    write_artifact(producer, "episodes", _episodes(0.20))
    drive.push(producer, ["stage0"], client=fake)
    assert len(fake.files_named("episodes.csv")) == 1 and fake.uploads == 2        # ditimpa, bukan duplikat


def test_pull_into_other_member_out_dir(cfg, fake, tmp_path):
    producer = Config(root=cfg.root, out_root=tmp_path / "danen")
    write_artifact(producer, "episodes", _episodes(0.15))
    drive.push(producer, ["stage0"], client=fake)
    consumer = Config(root=cfg.root, out_root=tmp_path / "ardell")
    got = drive.pull(consumer, ["episodes", "profiles"], client=fake)                # profiles belum ada di Drive
    assert got == ["results/stage0/episodes.csv"]
    assert read_artifact(consumer, "episodes")["cum_dlog_e"].item() == 0.15


def test_push_only_requested_stages(cfg, fake, tmp_path):
    c = Config(root=cfg.root, out_root=tmp_path)
    write_artifact(c, "episodes", _episodes())
    assert drive.push(c, ["task1"], client=fake) == []


def test_local_without_credentials_is_skipped(cfg, tmp_path, monkeypatch):
    monkeypatch.setenv("KAGAMI_DRIVE_TOKEN_FILE", str(tmp_path / "tidak_ada.json"))
    c = Config(root=cfg.root, out_root=tmp_path)
    assert drive.pull(c, ["episodes"], strict=False) == []
    assert drive.push(c, ["stage0"], strict=False) == []
    with pytest.raises(drive.DriveUnavailable):
        drive.pull(c, ["episodes"], strict=True)


# --------------------------------------------------------------------------- data mentah (D-101)
def _raw_files(c: Config) -> dict[str, bytes]:
    return {f.relative_to(c.raw_dir).as_posix(): f.read_bytes()
            for key in c.sources for f in c.source_files(key) if f.exists()}


def test_push_raw_then_pull_raw_roundtrip(cfg, fake, tmp_path):
    if not cfg.source_path("pihps").exists():
        pytest.skip("data mentah tidak ada")
    sent, skipped = drive.push_raw(cfg, client=fake)
    expected = _raw_files(cfg)
    assert set(sent) >= set(expected) and not skipped
    sent2, skipped2 = drive.push_raw(cfg, client=fake)                 # tidak berubah -> semua dilewati
    assert sent2 == [] and set(skipped2) == set(sent)
    member = Config(root=cfg.root, raw_root=tmp_path / "raw", out_root=tmp_path / "out")
    got = drive.pull_raw(member, client=fake)
    assert set(got) == set(expected)                                    # termasuk sumber glob (exim tahunan)
    assert _raw_files(member) == expected                               # isi identik byte-per-byte
    assert any(rel.startswith("bps_trade/exim_annual_") for rel in got)


def test_pull_raw_never_overwrites(cfg, fake, tmp_path):
    src = Config(root=cfg.root, raw_root=tmp_path / "src_raw", out_root=tmp_path / "o1")
    f = src.source_path("brent")
    f.parent.mkdir(parents=True)
    f.write_text("observation_date,DCOILBRENTEU\n2020-01-01,60\n")
    drive.push_raw(src, client=fake)
    member = Config(root=cfg.root, raw_root=tmp_path / "member_raw", out_root=tmp_path / "o2")
    mine = member.source_path("brent"); mine.parent.mkdir(parents=True); mine.write_text("milik anggota")
    assert drive.pull_raw(member, client=fake) == []
    assert mine.read_text() == "milik anggota"
