"""CLAUDE.md §9 (inventaris modul & fungsi) harus sinkron dengan kode.

Untuk setiap modul `src/**.py` (kecuali __init__/__main__): ada heading `#### src/<path>`; setiap fungsi publik top-level
tercantum sebagai `` - `nama` · ✔ · ... `` atau `` - `nama` · ⬜ WP-xx · ... ``; ⬜ WP-xx bila dan hanya bila badan
fungsi memanggil todo("WP-xx") dengan WP yang sama; tidak ada fungsi fiktif.
"""

import ast
import re
from pathlib import Path

from kagami.utils.artifacts import ARTIFACTS

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
SECTION = TEXT[TEXT.index("## 9. Inventaris"): TEXT.index("\n## 10. ")]
ENTRY = re.compile(r"^- `(\w+)` · (✔|⬜ (WP-\d{2})) · ", re.M)


def _documented() -> dict[str, dict[str, str]]:
    out, current = {}, None
    for line in SECTION.splitlines():
        if line.startswith("#### src/"):
            current = line[5:].strip()
            out[current] = {}
        elif current and (m := ENTRY.match(line)):
            out[current][m.group(1)] = m.group(3) or "done"
    return out


def _in_code() -> dict[str, dict[str, str]]:
    out = {}
    for f in sorted((ROOT / "src").rglob("*.py")):
        if "__pycache__" in f.parts or f.name in ("__init__.py", "__main__.py"):
            continue
        src = f.read_text(encoding="utf-8")
        funcs = {}
        for node in ast.parse(src).body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                m = re.search(r'todo\("(WP-\d{2})"\)', ast.get_source_segment(src, node))
                funcs[node.name] = m.group(1) if m else "done"
        out[f.relative_to(ROOT).as_posix()] = funcs
    return out


def test_every_module_has_heading():
    missing = set(_in_code()) - set(_documented())
    extra = set(_documented()) - set(_in_code())
    assert not missing, f"Modul tanpa heading di CLAUDE.md §9: {sorted(missing)}"
    assert not extra, f"Heading CLAUDE.md §9 untuk modul yang tidak ada: {sorted(extra)}"


def test_functions_and_status_match():
    doc, code = _documented(), _in_code()
    problems = []
    for mod, funcs in code.items():
        for name, status in funcs.items():
            got = doc.get(mod, {}).get(name)
            if got is None:
                problems.append(f"{mod}::{name} tidak tercantum")
            elif got != status:
                problems.append(f"{mod}::{name} tertulis {got}, di kode {status}")
        for name in set(doc.get(mod, {})) - set(funcs):
            problems.append(f"{mod}::{name} tercantum tetapi tidak ada di kode")
    assert not problems, "CLAUDE.md §9 basi:\n" + "\n".join(problems)


def test_artifact_count_stated():
    assert f"{len(ARTIFACTS)} artefak" in SECTION, f"perbarui jumlah artefak ({len(ARTIFACTS)}) di §9.1"
