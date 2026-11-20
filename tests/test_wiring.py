"""Penjaga skeleton: semua modul terpakai, setiap stub & artefak menunjuk WP yang ada, setiap artefak punya produsen."""

import importlib
import pkgutil
import re
import sys
from pathlib import Path

import kagami
from kagami.utils.artifacts import ARTIFACTS

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
WORKPLAN = (ROOT / "docs" / "WORKPLAN.md").read_text(encoding="utf-8")
WP_IN_PLAN = set(re.findall(r"^#{2,4} (WP-\d{2})\b", WORKPLAN, flags=re.M))


def _all_modules() -> set[str]:
    return {m.name for m in pkgutil.walk_packages(kagami.__path__, "kagami.")}


def _consumer_text() -> str:
    """Teks app/ dan notebooks/ (konsumen selain CLI: viz & runtime)."""
    parts = [p.read_text(encoding="utf-8") for p in (ROOT / "app").rglob("*.py")]
    parts += [p.read_text(encoding="utf-8") for p in (ROOT / "notebooks").glob("*.ipynb")]
    return "\n".join(parts)


def test_every_module_used():
    """Setiap modul terjangkau dari CLI, atau di-import oleh app/notebook."""
    importlib.import_module("kagami.cli")
    text = _consumer_text()
    for m in sorted(re.findall(r"from (kagami\.[\w.]+) import", text)):
        importlib.import_module(m)
    for pkg, names in re.findall(r"from (kagami\.[\w.]+) import ([\w, ]+)", text):
        for n in names.split(","):
            try:                                   # `from kagami.pipelines import task1` = submodul
                importlib.import_module(f"{pkg}.{n.strip()}")
            except ModuleNotFoundError:            # nama fungsi/kelas, bukan modul
                pass
    unused = {m for m in _all_modules() if m not in sys.modules} - {"kagami.__main__"}
    assert not unused, f"Modul tidak dipakai CLI/app/notebook: {sorted(unused)}"


def test_every_viz_function_used():
    from kagami.viz import plots
    text = _consumer_text()
    funcs = [n for n, f in vars(plots).items() if callable(f) and getattr(f, "__module__", "") == plots.__name__]
    unused = [f for f in funcs if f"plots.{f}(" not in text]
    assert not unused, f"Fungsi viz tidak dipakai app/notebook: {unused}"


def test_todo_ids_exist_in_workplan():
    ids = set()
    for f in SRC.rglob("*.py"):
        ids |= set(re.findall(r'todo\("(WP-\d{2})"\)', f.read_text(encoding="utf-8")))
    missing = ids - WP_IN_PLAN
    assert not missing, f"todo() menunjuk WP yang tidak ada di WORKPLAN.md: {sorted(missing)}"


def test_artifact_wps_exist_in_workplan():
    missing = {a.wp for a in ARTIFACTS.values()} - WP_IN_PLAN
    assert not missing, sorted(missing)


def test_every_artifact_has_producer_and_is_documented():
    code = "\n".join(f.read_text(encoding="utf-8") for f in SRC.rglob("*.py"))
    arch = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    for name, art in ARTIFACTS.items():
        if art.stage == "report":   # ditulis manual/agent (WP-33), bukan pipeline
            continue
        assert re.search(rf'write_artifact\(cfg, "{name}"', code), f"{name} tidak pernah ditulis"
    for name in ARTIFACTS:
        assert f"`{name}`" in arch, f"{name} tidak didokumentasikan di ARCHITECTURE.md"


def test_app_pages_present_and_import_common():
    pages = sorted((ROOT / "app" / "pages").glob("*.py"))
    assert len(pages) == 5 and (ROOT / "app" / "Home.py").exists()
    for p in [ROOT / "app" / "Home.py", *pages]:
        assert "from common import" in p.read_text(encoding="utf-8"), p.name
