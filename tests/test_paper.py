"""Penjaga makalah (WP-33, D-177): bagian wajib juknis INDONERIS §2c, sitasi = definisi = daftar pustaka, rambu klaim CLAUDE.md
§20, angka utama sama dengan results/findings.md, gambar yang dirujuk ada, dan PDF tidak basi terhadap sumbernya."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "paper"
TEX = PAPER / "kagami_makalah.tex"
PDF = PAPER / "kagami_makalah.pdf"

pytestmark = pytest.mark.skipif(not TEX.exists(), reason="sumber makalah tidak ada")

# Angka utama yang wajib sama di makalah, results/findings.md, dan PDF (ditulis literal di ketiganya)
HEADLINE = ["1,009", "1,013", "0,996", "0,987", "161,7", "132,6", "0,184", "0,196", "0,094", "99,5", "96,5", "Rp89",
            "Rp938", "4,65", "0,677", "0,680", "16.392", "150.525", "8,8", "17,1", "0,935", "0,895"]


def _strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def _body() -> str:
    s = _strip_comments(TEX.read_text(encoding="utf-8"))
    return s[s.index(r"\begin{document}"):]


def _main_text() -> str:
    """Isi sebelum daftar pustaka (judul rujukan berbahasa Inggris tidak ikut rambu klaim)."""
    b = _body()
    return b[:b.index(r"\section*{Daftar Pustaka}")]


def test_required_sections_present():
    """Juknis §2c: judul, abstrak, pendahuluan (latar belakang, tujuan & manfaat, batasan), kajian pustaka, solusi usulan
    (deskripsi, dataset, metode, perbedaan, matriks evaluasi), hasil, analisis, kesimpulan & saran, daftar pustaka."""
    b = _body()
    assert "KAGAMI:" in b and r"\textbf{Abstrak.}" in b and r"\textbf{Kata kunci:}" in b
    order = [r"\section{Pendahuluan}", r"\subsection{Latar belakang}", r"\subsection{Tujuan dan manfaat}",
             r"\subsection{Batasan}", r"\section{Kajian Pustaka}", r"\section{Solusi Usulan}",
             r"\subsection{Deskripsi solusi}", r"\subsection{Dataset}", r"\subsection{Metode}",
             r"\subsection{Perbedaan dengan solusi sebelumnya}", r"\subsection{Matriks evaluasi}",
             r"\section{Hasil Eksperimen dan Pengujian}", r"\section{Analisis}", r"\section{Kesimpulan dan Saran}",
             r"\subsection{Kesimpulan}", r"\subsection{Saran}", r"\section*{Daftar Pustaka}"]
    pos = [b.find(s) for s in order]
    missing = [s for s, p in zip(order, pos) if p < 0]
    assert not missing, f"bagian wajib hilang: {missing}"
    assert pos == sorted(pos), "urutan bagian tidak sesuai juknis"


def test_citations_match_bibliography():
    """Setiap \\citep/\\citet punya \\defref dan butir daftar pustaka; tidak ada rujukan yang didefinisikan tanpa dikutip."""
    tex = _strip_comments(TEX.read_text(encoding="utf-8"))
    cited = {k.strip() for grp in re.findall(r"\\cite[pt]\{([^}]*)\}", _body()) for k in grp.split(",")}
    defined = set(re.findall(r"\\defref\{([^}]*)\}", tex))
    listed = set(re.findall(r"\\refitem\{([^}]*)\}", tex))
    assert cited, "tidak ada sitasi"
    assert cited <= defined, f"dikutip tanpa \\defref: {sorted(cited - defined)}"
    assert defined == listed, f"\\defref ≠ daftar pustaka: {sorted(defined ^ listed)}"
    assert listed <= cited, f"ada di daftar pustaka tetapi tidak dikutip: {sorted(listed - cited)}"
    assert "citealp" not in tex and "\\cite{" not in tex          # tanpa natbib (tidak terpasang di MiKTeX tim)


def test_claim_rules():
    """CLAUDE.md §20: bahasa asosiasional, tanpa klaim 'pertama', tanpa '±' sebagai 'sekitar', kajian bukan SLR."""
    text = _main_text().lower()
    forbidden = ["penelitian pertama", "menyebabkan", "memprediksi kenaikan", "sistem peringatan dini",
                 "tinjauan pustaka sistematis", "systematic literature review", "tidak ada pengaruh kurs",
                 "kerentanan provinsi", "±"]
    found = [f for f in forbidden if f in text]
    assert not found, f"frasa terlarang (CLAUDE.md §20): {found}"
    assert not re.search(r"dataset kami(?! turunan)", text)
    assert "asosiasional" in text and "prototipe riset" in text and "bukan tinjauan sistematis" in text
    assert "pseudo-real-time" in text and "batas atas" in text
    # p uji DM ditulis bersama statistik DM (arahnya) dan p satu sisi untuk hipotesis berarah (CLAUDE.md §20, D-169)
    assert "dm $-2,70$" in text and "$p$ satu sisi" in text


def test_headline_numbers_match_findings():
    findings = (ROOT / "results" / "findings.md").read_text(encoding="utf-8")
    body = _body()
    missing_paper = [n for n in HEADLINE if n not in body]
    missing_findings = [n for n in HEADLINE if n not in findings]
    assert not missing_paper, f"angka utama tidak ada di makalah: {missing_paper}"
    assert not missing_findings, f"angka utama makalah tidak ada di findings.md: {missing_findings}"


def test_figures_exist():
    refs = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]*)\}", _body())
    assert len(refs) >= 7
    missing = [r for r in refs if not (PAPER / r).exists()]
    assert not missing, f"gambar tidak ada: {missing}"
    labels = set(re.findall(r"\\label\{((?:fig|tab|eq|sec):[^}]*)\}", _body()))
    used = set(re.findall(r"\\ref\{([^}]*)\}", _body()))
    assert used <= labels, f"\\ref tanpa \\label: {sorted(used - labels)}"
    unused = {lab for lab in labels if lab.startswith(("fig:", "tab:"))} - used
    assert not unused, f"gambar/tabel tidak pernah dirujuk di teks: {sorted(unused)}"


def test_pdf_present_and_current():
    """PDF ada dan memuat angka utama yang sama dengan sumber (menangkap PDF basi sesudah .tex diubah)."""
    assert PDF.exists() and PDF.stat().st_size > 200_000, "kagami_makalah.pdf belum dikompilasi"
    fitz = pytest.importorskip("fitz")
    doc = fitz.open(PDF)
    text = " ".join(page.get_text() for page in doc).replace("\u2212", "-")
    assert doc.page_count >= 15
    missing = [n for n in HEADLINE if n.replace("\u2212", "-") not in text]
    assert not missing, f"PDF basi atau tidak lengkap, angka tidak ditemukan: {missing}"
    assert "Daftar Pustaka" in text and "Matriks evaluasi" in text
