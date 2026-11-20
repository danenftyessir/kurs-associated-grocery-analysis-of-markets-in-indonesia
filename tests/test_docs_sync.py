"""Dokumen hidup (README.md, CLAUDE.md, docs/*.md) tidak boleh kadaluarsa terhadap kode, config, dan dokumen lain.

Catatan bertanggal (SESSION_LOG, DECISIONS, docs/handoff/) dikecualikan dari cek path/ID karena merupakan jejak sejarah.
Protokol manusia/agent: CLAUDE.md §3.4.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = {"SESSION_LOG.md", "DECISIONS.md"}
LIVE_DOCS = [ROOT / "README.md", ROOT / "CLAUDE.md"] + sorted(
    p for p in (ROOT / "docs").glob("*.md") if p.name not in HISTORICAL)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _live_text() -> str:
    return "\n".join(_read(p) for p in LIVE_DOCS)


# --------------------------------------------------------------------------- tautan & path
def test_markdown_links_resolve():
    broken = []
    for doc in LIVE_DOCS:
        for target in re.findall(r"\]\(([^)\s]+)\)", _read(doc)):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = re.sub(r"[#:].*$", "", target)
            if path and not (doc.parent / path).exists():
                broken.append(f"{doc.relative_to(ROOT)} → {target}")
    assert not broken, "Tautan rusak:\n" + "\n".join(broken)


def test_code_paths_exist():
    pattern = re.compile(r"`((?:src|tests|notebooks|configs|app|docs)/[^`\s<>*]+?\.(?:py|ipynb|yaml|md))(?:::[\w.]+)?`")
    missing = []
    for doc in LIVE_DOCS:
        for rel in pattern.findall(_read(doc)):
            if "..." in rel or rel.startswith("docs/paper/"):        # placeholder / keluaran Abi yang belum dibuat
                continue
            if not (ROOT / rel).exists():
                missing.append(f"{doc.relative_to(ROOT)} → {rel}")
    assert not missing, "Path di dokumen tidak ada di repo:\n" + "\n".join(missing)


# --------------------------------------------------------------------------- WORKPLAN vs kode vs CLAUDE §2
def _board() -> dict[str, str]:
    return dict(re.findall(r"^\| (WP-\d{2}) \| .*? \| (✅|⬜|🔶) \|", _read(ROOT / "docs" / "WORKPLAN.md"), re.M))


def _stub_wps() -> set[str]:
    return {wp for f in (ROOT / "src").rglob("*.py") for wp in re.findall(r'todo\("(WP-\d{2})"\)', _read(f))}


def test_workplan_board_matches_headings():
    headings = set(re.findall(r"^### (WP-\d{2})\b", _read(ROOT / "docs" / "WORKPLAN.md"), re.M))
    assert set(_board()) == headings, f"papan vs heading WP berbeda: {sorted(set(_board()) ^ headings)}"


def test_workplan_status_matches_stubs():
    board, stubs = _board(), _stub_wps()
    done_but_stub = sorted(wp for wp in stubs if board.get(wp) == "✅")
    assert not done_but_stub, f"WP ✅ di papan tetapi masih ada todo() di src/: {done_but_stub}"


def test_claude_status_lists_done_wps():
    text = _read(ROOT / "CLAUDE.md")
    m = re.search(r"- \*\*Selesai:\*\*(.*?)(?=\n- \*\*)", text, re.S)
    assert m, "CLAUDE.md §2 harus punya baris '- **Selesai:** ...'"
    listed = set(re.findall(r"WP-\d{2}", m.group(1)))
    done = {wp for wp, s in _board().items() if s == "✅"}
    assert listed == done, f"CLAUDE.md §2 'Selesai' tidak sama dengan papan ✅: lebih {sorted(listed - done)}, kurang {sorted(done - listed)}"


# --------------------------------------------------------------------------- ID keputusan & isu
def test_decision_and_issue_ids_exist():
    decisions = set(re.findall(r"^### (D-\d{3})", _read(ROOT / "docs" / "DECISIONS.md"), re.M))
    issues = set(re.findall(r"^\| (U\d+) \|", _read(ROOT / "docs" / "OPEN_ISSUES.md"), re.M))
    text = _live_text()
    bad_d = sorted({d for d in re.findall(r"\b(D-0\d{2})\b", text)} - decisions)
    bad_u = sorted({u for u in re.findall(r"\b(U\d{1,2})\b", text)} - issues)
    assert not bad_d, f"D-ID dirujuk tetapi tidak ada di DECISIONS.md: {bad_d}"
    assert not bad_u, f"U-ID dirujuk tetapi tidak ada di OPEN_ISSUES.md: {bad_u}"


# --------------------------------------------------------------------------- config
def test_params_keys_referenced_exist():
    params = yaml.safe_load(_read(ROOT / "configs" / "params.yaml"))
    text = _live_text() + "\n".join(_read(f) for f in (ROOT / "src").rglob("*.py"))
    bad = set()
    for ref in re.findall(r"\bparams\.([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)", text):
        if ref.split(".")[0] in {"yaml", "x"}:
            continue
        node = params
        for part in ref.split("."):
            if not isinstance(node, dict) or part not in node:
                bad.add(ref)
                break
            node = node[part]
    assert not bad, f"Kunci params.* dirujuk tetapi tidak ada di configs/params.yaml: {sorted(bad)}"


def test_sources_documented():
    keys = yaml.safe_load(_read(ROOT / "configs" / "sources.yaml"))
    datasets, claude = _read(ROOT / "docs" / "DATASETS.md"), _read(ROOT / "CLAUDE.md")
    missing = [k for k in keys if f"`{k}`" not in datasets or f"`{k}`" not in claude]
    assert not missing, f"Sumber di sources.yaml belum didokumentasikan di DATASETS.md / CLAUDE.md §10.1: {missing}"


def test_commodity_table_matches_config():
    com = yaml.safe_load(_read(ROOT / "configs" / "commodities.yaml"))
    text = _read(ROOT / "CLAUDE.md")
    wrong = []
    for cid, spec in com.items():
        row = re.search(rf"^\| {cid} \| (.*)$", text, re.M)
        if not row or spec["variant"] not in row.group(1) or spec["role"] not in row.group(1):
            wrong.append(cid)
    assert not wrong, f"CLAUDE.md §11.1 tidak sesuai configs/commodities.yaml untuk: {wrong}"


# --------------------------------------------------------------------------- struktur repo
def test_notebooks_documented():
    stems = {p.stem for p in (ROOT / "notebooks").glob("*.ipynb")}
    for doc in ("docs/NOTEBOOKS.md", "docs/ARCHITECTURE.md"):
        missing = [s for s in stems if s not in _read(ROOT / doc)]
        assert not missing, f"{doc} tidak menyebut notebook: {missing}"


def test_subpackages_documented():
    pkgs = {p.parent.name for p in (ROOT / "src").glob("*/__init__.py")}
    arch, claude = _read(ROOT / "docs" / "ARCHITECTURE.md"), _read(ROOT / "CLAUDE.md")
    missing = [p for p in pkgs if f"  {p}/" not in arch or f"`{p}`" not in claude]
    assert not missing, f"Subpaket src/ belum didokumentasikan di ARCHITECTURE §2 / CLAUDE §6: {missing}"
    declared = re.findall(r'"kagami\.(\w+)"', _read(ROOT / "pyproject.toml"))
    assert set(declared) == pkgs, f"pyproject packages tidak sama dengan subpaket src/: {sorted(set(declared) ^ pkgs)}"


def test_tests_documented():
    names = {p.stem for p in (ROOT / "tests").glob("test_*.py")}
    claude = _read(ROOT / "CLAUDE.md")
    arch_line = next(l for l in _read(ROOT / "docs" / "ARCHITECTURE.md").splitlines() if l.startswith("tests/"))
    missing_claude = [n for n in names if f"{n}.py" not in claude]
    missing_arch = [n for n in names if n.removeprefix("test_") not in arch_line]
    assert not missing_claude, f"CLAUDE.md §16.1 belum menyebut: {missing_claude}"
    assert not missing_arch, f"ARCHITECTURE §2 (baris tests/) belum menyebut: {missing_arch}"
