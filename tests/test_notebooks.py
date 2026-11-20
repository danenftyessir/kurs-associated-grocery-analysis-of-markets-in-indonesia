"""Notebook per tahap: struktur konsisten, sel setup identik, terhubung ke pipeline yang benar, setup jalan lokal."""

import importlib
import os
import re
from pathlib import Path

import nbformat
import pytest

from kagami.cli import PIPELINE

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"
NOTEBOOKS = sorted(NB_DIR.glob("*.ipynb"))


def _code(nb):
    return [c.source for c in nb.cells if c.cell_type == "code"]


def test_one_notebook_per_stage():
    stages = []
    for p in NOTEBOOKS:
        m = re.search(r"from kagami\.pipelines import (\w+)\n\1\.run\(cfg", "\n".join(_code(nbformat.read(p, 4))))
        assert m, f"{p.name}: tidak memanggil pipelines.<tahap>.run(cfg)"
        stages.append(m.group(1))
    assert sorted(stages) == sorted(PIPELINE), stages


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_notebook_valid_and_consistent(path):
    nb = nbformat.read(path, 4)
    nbformat.validate(nb)
    first = _code(nbformat.read(NOTEBOOKS[0], 4))[:2]
    assert _code(nb)[:2] == first, "sel setup & init harus identik di semua notebook"
    assert all(not c.get("outputs") for c in nb.cells if c.cell_type == "code"), "simpan notebook tanpa output"
    for mod in re.findall(r"from (kagami\.[\w.]+) import", "\n".join(_code(nb))):
        importlib.import_module(mod)


def test_setup_cells_run_locally(monkeypatch):
    """Sel 0 (bootstrap) + sel 1 (init_runtime) jalan dari folder notebooks/ dan memberi runtime lokal."""
    monkeypatch.chdir(NB_DIR)
    for v in ("KAGAMI_RAW_DIR", "KAGAMI_OUT_DIR", "KAGAMI_ARTIFACT_DIRS"):
        monkeypatch.delenv(v, raising=False)
    if os.path.exists("/kaggle/input"):
        pytest.skip("dijalankan di Kaggle")
    ns: dict = {}
    setup, init = _code(nbformat.read(NOTEBOOKS[0], 4))[:2]
    exec(setup, ns)
    exec(init, ns)
    cfg = ns["cfg"]
    assert ns["ROOT"] == NB_DIR.parent and cfg.out_dir == NB_DIR.parent
