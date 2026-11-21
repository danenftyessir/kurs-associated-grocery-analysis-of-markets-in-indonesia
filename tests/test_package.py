"""WP-32: paket juri lengkap, tidak membocorkan data tanpa hak redistribusi, dan dapat dijalankan dari folder baru."""

import os
import subprocess
import sys
import zipfile

import pandas as pd

from kagami.pipelines import package
from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config
from kagami.utils.io import exists, write_artifact

SNIPPET = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('kagami', 'src/__init__.py', submodule_search_locations=['src'])\n"
    "mod = importlib.util.module_from_spec(spec); sys.modules['kagami'] = mod; spec.loader.exec_module(mod)\n"
    "from kagami.cli import main\nmain(['status'])\n")


def _cfg(cfg, tmp_path):
    raw = tmp_path / "raw"
    for key, src in cfg.sources.items():                       # satu file palsu per sumber (isi sumber glob diabaikan)
        f = raw / src["path"]
        if "glob" in src:
            f = f / src["glob"].replace("*", "x")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("dummy", encoding="utf-8")
    return Config(root=cfg.root, raw_root=raw, out_root=tmp_path / "out")


def test_submission_contents_and_data_rights(cfg, tmp_path):
    c = _cfg(cfg, tmp_path)
    write_artifact(c, "episodes", pd.DataFrame({"episode_id": [1], "start_week": ["2020-03-02"],
                                                "end_week": ["2020-04-27"], "cum_dlog_e": [0.12]}))
    zpath = package.submission(c, allow_missing=True)
    names = set(zipfile.ZipFile(zpath).namelist())
    assert {"pyproject.toml", "README.md", "configs/params.yaml", "src/__init__.py", "src/cli.py",
            "app/Home.py", "app/common.py", "tests/conftest.py", "results/stage0/episodes.csv"} <= names
    assert any(n.startswith("notebooks/") for n in names) and any(n.startswith("data/reference/") for n in names)
    raw_in_zip = {n for n in names if n.startswith("data/raw/")}
    allowed = {"data/raw/" + p.relative_to(c.raw_dir).as_posix()
               for key, s in cfg.sources.items() if s["redistribute"] for p in c.source_files(key)}
    allowed.add("data/raw/checksums.csv")                       # artefak `checksums` (ship) memang di folder mentah
    assert raw_in_zip <= allowed, f"data tanpa hak redistribusi ikut: {sorted(raw_in_zip - allowed)}"
    assert not any("bi_pihps" in n or "bi_jisdor" in n or "pihps_daily" in n or n.startswith("data/interim/")
                   for n in names)
    assert not any(n.startswith(("docs/handoff", "docs/arsip", "docs/spec", ".git", "dist/")) for n in names)
    assert not any(n.endswith((".pyc", ".json")) and "token" in n for n in names)


def test_missing_ship_artifacts_are_reported_and_blocked(cfg, tmp_path):
    c = _cfg(cfg, tmp_path)
    _, missing = package.collect_submission(c)
    ship = {a.name for a in ARTIFACTS.values() if a.ship} - {"checksums"}      # checksums ikut kode (ada di repo)
    # root = folder kode asli; di mesin yang sudah menjalankan tahap (mis. stage0 / tabel data/reference) sebagian artefak
    # ship sudah ada di root dan sah ikut zip -> yang wajib dilaporkan hilang = artefak ship yang tidak ada di read_dirs.
    assert set(missing) == {n for n in ship if not exists(c, n)}
    if not missing:
        return
    try:
        package.submission(c)
    except SystemExit as e:
        assert "artefak ship belum ada" in str(e)
    else:
        raise AssertionError("submission tanpa --allow-missing harus berhenti")


def test_extracted_package_runs_cli(cfg, tmp_path):
    c = _cfg(cfg, tmp_path)
    zpath = package.submission(c, allow_missing=True)
    out = tmp_path / "fresh"
    zipfile.ZipFile(zpath).extractall(out)
    # -E (abaikan PYTHONPATH dll.) + lingkungan asli tanpa KAGAMI_*: kagami diambil dari folder hasil ekstrak (SNIPPET),
    # pustaka pihak ketiga tetap terlihat walau terpasang di user site-packages (Windows butuh APPDATA).
    env = {k: v for k, v in os.environ.items() if not k.startswith("KAGAMI_")} | {"KAGAMI_RAW_DIR": str(tmp_path / "none")}
    r = subprocess.run([sys.executable, "-E", "-c", SNIPPET], cwd=out, capture_output=True, text=True, timeout=120,
                       env=env)
    assert r.returncode == 0, r.stderr[-800:]
    assert "episodes" in r.stdout or "artefak" in r.stdout.lower()
