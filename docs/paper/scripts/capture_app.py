"""Gambar app untuk makalah (WP-33): tangkapan layar halaman Ringkasan dan Profil provinsi, digabung menjadi
`docs/paper/figures/app_layar.pdf`. Hanya membaca app yang sedang berjalan; tidak mengubah artefak.

Prasyarat: app berjalan (mis. `python -m streamlit run app/Home.py --server.port 8511`), Google Chrome terpasang, dan
paket Python `playwright` (memakai Chrome sistem lewat channel="chrome", tanpa mengunduh browser) serta Pillow.

Jalankan dari root project:  python docs/paper/scripts/capture_app.py http://localhost:8511
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "paper" / "figures" / "app_layar.pdf"
PAGES = [("", "beranda"), ("Profil_Provinsi", "profil")]


def capture(base: str, folder: Path) -> list[Path]:
    paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 860}, device_scale_factor=2)
        for url_path, name in PAGES:
            page.goto(f"{base.rstrip('/')}/{url_path}", wait_until="networkidle", timeout=90_000)
            page.wait_for_selector("[data-testid='stMain']", timeout=60_000)
            for _ in range(60):                      # tunggu skrip Streamlit selesai berjalan
                if page.locator("[data-testid='stStatusWidget']").count() == 0:
                    break
                time.sleep(0.5)
            time.sleep(4)                            # grafik plotly selesai digambar
            path = folder / f"{name}.png"
            page.screenshot(path=str(path))
            paths.append(path)
        browser.close()
    return paths


def compose(paths: list[Path]) -> None:
    """Dua tangkapan layar berdampingan (bilah samping dipotong pada gambar kedua), disimpan sebagai PDF raster."""
    left = Image.open(paths[0]).convert("RGB")
    right = Image.open(paths[1]).convert("RGB")
    right = right.crop((560, 0, right.width, right.height))       # tanpa bilah navigasi kiri (sudah tampak di kiri)
    gap = 40
    canvas = Image.new("RGB", (left.width + gap + right.width, max(left.height, right.height)), "white")
    canvas.paste(left, (0, 0))
    canvas.paste(right, (left.width + gap, 0))
    canvas.thumbnail((3000, 3000))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "PDF", resolution=220.0)
    print(f"[capture] {OUT.relative_to(ROOT)} {canvas.size}")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8511"
    with tempfile.TemporaryDirectory() as tmp:
        compose(capture(base_url, Path(tmp)))
