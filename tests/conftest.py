import importlib.util
import sys
from pathlib import Path

import pytest

# Paket `kagami` = folder src/ (D-024). Tanpa `pip install -e .`, daftarkan nama paket ke folder itu.
_SRC = Path(__file__).resolve().parents[1] / "src"
if importlib.util.find_spec("kagami") is None:
    _spec = importlib.util.spec_from_file_location("kagami", _SRC / "__init__.py",
                                                   submodule_search_locations=[str(_SRC)])
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["kagami"] = _mod
    _spec.loader.exec_module(_mod)

from kagami.utils.config import get_config  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return get_config()


@pytest.fixture(scope="session")
def pihps(cfg):
    from kagami.data.loaders import load_pihps
    if not cfg.source_path("pihps").exists():
        pytest.skip("PIHPS mentah tidak ada (paket juri tanpa data mentah)")
    return load_pihps(cfg)
