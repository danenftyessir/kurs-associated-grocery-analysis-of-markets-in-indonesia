"""Format setiap file docs/handoff/*.md sesuai docs/HANDOFF.md (nama file, frontmatter, bagian wajib)."""

import re
from datetime import datetime
from pathlib import Path

import pytest

HANDOFF_DIR = Path(__file__).resolve().parents[1] / "docs" / "handoff"
FILES = sorted(HANDOFF_DIR.glob("*.md"))
MEMBERS = {"Danen", "Ardell", "Abi"}
JENIS = {"TERBIT", "PERMINTAAN", "SERAH-TERIMA-WP", "DATA-MANUAL", "ANGKA-MAKALAH", "KEPUTUSAN", "BLOKIR", "ONBOARDING"}
STATUS = {"terbuka", "diterima", "selesai", "ditolak"}
KEYS = ("dari", "ke", "jenis", "terkait", "status", "dibuat", "tenggat_respon")
SECTIONS = ("## Ringkasan", "## Yang diserahkan", "## Perubahan kontrak", "## Yang perlu dilakukan penerima",
            "## Cara memverifikasi", "## Angka penting", "## Batasan, risiko, yang belum beres", "## Balasan")
NAME = re.compile(r"^(\d{8})-(\d{4})_(danen|ardell|abi|semua)-ke-(danen|ardell|abi|semua)_[a-z0-9]+(-[a-z0-9]+)*\.md$")


def _frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "frontmatter --- ... --- tidak ada di awal file"
    return {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)}


def test_handoff_dir_exists():
    assert HANDOFF_DIR.is_dir() and FILES, "docs/handoff/ harus ada dan berisi minimal satu handoff"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_handoff_format(path):
    m = NAME.match(path.name)
    assert m, f"nama file tidak sesuai pola YYYYMMDD-HHMM_<dari>-ke-<ke>_<topik>.md: {path.name}"
    text = path.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    missing = [k for k in KEYS if k not in fm]
    assert not missing, f"field wajib hilang: {missing}"

    assert fm["dari"] in MEMBERS and fm["dari"].lower() == m.group(3), "field `dari` tidak cocok dengan nama file"
    ke = {x.strip() for x in fm["ke"].split(",")}
    assert ke == {"Semua"} or ke <= MEMBERS, f"`ke` tidak valid: {fm['ke']}"
    expected_ke = "semua" if (ke == {"Semua"} or len(ke) > 1) else next(iter(ke)).lower()
    assert m.group(4) == expected_ke, f"bagian <ke> nama file harus '{expected_ke}'"
    assert fm["dari"] not in ke, "pengirim tidak boleh menjadi penerima"
    assert fm["jenis"] in JENIS, f"`jenis` tidak valid: {fm['jenis']}"
    assert fm["status"] in STATUS, f"`status` tidak valid: {fm['status']}"

    dibuat = datetime.strptime(fm["dibuat"], "%Y-%m-%d %H:%M")
    assert dibuat.strftime("%Y%m%d-%H%M") == f"{m.group(1)}-{m.group(2)}", "`dibuat` tidak cocok dengan timestamp nama file"
    if fm["tenggat_respon"] != "-":
        assert datetime.strptime(fm["tenggat_respon"], "%Y-%m-%d").date() >= dibuat.date()

    missing_sections = [s for s in SECTIONS if s not in text]
    assert not missing_sections, f"bagian wajib hilang: {missing_sections}"
    todo = text[text.index("## Yang perlu dilakukan penerima"): text.index("## Cara memverifikasi")]
    assert "- [" in todo, "bagian 'Yang perlu dilakukan penerima' harus berisi kotak centang"
    if fm["status"] == "selesai":
        assert "- [ ]" not in todo, "status selesai tetapi masih ada kotak belum dicentang"
