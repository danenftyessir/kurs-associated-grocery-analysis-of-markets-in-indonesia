"""Tangkapan layar app KAGAMI untuk Bab 4 makalah (PNG). Hanya membaca app yang sedang berjalan.

Prasyarat: app berjalan (mis. `python -m streamlit run app/Home.py --server.port 8511`), Google Chrome, paket `playwright`
(channel="chrome", tanpa mengunduh browser) dan Pillow.

Jalankan dari root project:  python docs/paper/scripts/capture_app_bab45.py http://localhost:8511
Keluaran: docs/paper/figures/bab45/b4_08_app_<halaman>.png dan b4_08_app_ringkas.png (grid 2 × 2).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "paper" / "figures" / "bab45"
PAGES = [("", "ringkasan", "Ringkasan"), ("Cerita_Data", "cerita_data", "Cerita data"),
         ("Kepekaan_Harga_Regional", "respons_harga", "Respons harga"),
         ("Profil_Provinsi", "profil_provinsi", "Profil provinsi"),
         ("Prediksi", "prediksi", "Prediksi"), ("Penjelajah_Skenario", "simulasi", "Simulasi rupiah")]
GRID = ["ringkasan", "cerita_data", "respons_harga", "simulasi"]


def fade_bottom(path: Path, height: int = 260) -> None:
    """Gradasi ke warna latar di tepi bawah: halaman Streamlit lebih panjang dari layar, jadi baris yang terpotong
    tampak sebagai kelanjutan halaman, bukan galat potong."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 20, h - 5))                     # warna latar konten di pojok kanan bawah
    over = Image.new("RGB", (w, height), bg)
    mask = Image.linear_gradient("L").resize((w, height))  # 0 di atas -> 255 di bawah
    im.paste(over, (0, h - height), mask)
    im.save(path)


def capture(base: str) -> dict[str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        for url_path, name, _ in PAGES:
            page.goto(f"{base.rstrip('/')}/{url_path}", wait_until="networkidle", timeout=120_000)
            page.wait_for_selector("[data-testid='stMain']", timeout=60_000)
            for _ in range(80):                       # tunggu skrip Streamlit selesai
                if page.locator("[data-testid='stStatusWidget']").count() == 0:
                    break
                time.sleep(0.5)
            time.sleep(5)                             # grafik plotly selesai digambar
            path = OUT / f"b4_08_app_{name}.png"
            page.screenshot(path=str(path))
            fade_bottom(path)
            paths[name] = path
            print(f"[capture] {path.name}")
        browser.close()
    return paths


def grid(paths: dict[str, Path]) -> None:
    labels = {n: lab for _, n, lab in PAGES}
    ims = [Image.open(paths[n]).convert("RGB") for n in GRID]
    w, h = ims[0].size
    gap, cap = 40, 90
    canvas = Image.new("RGB", (2 * w + gap, 2 * (h + cap) + gap), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
    except OSError:
        font = ImageFont.load_default()
    for i, (n, im) in enumerate(zip(GRID, ims)):
        x, y = (i % 2) * (w + gap), (i // 2) * (h + cap + gap)
        draw.text((x + 8, y + 18), f"({'abcd'[i]}) {labels[n]}", fill=(44, 44, 42), font=font)
        canvas.paste(im, (x, y + cap))
        draw.rectangle([x, y + cap, x + w - 1, y + cap + h - 1], outline=(211, 209, 199), width=3)
    canvas.thumbnail((3600, 3600))
    canvas.save(OUT / "b4_08_app_ringkas.png", dpi=(300, 300))
    print("[capture] b4_08_app_ringkas.png", canvas.size)


if __name__ == "__main__":
    grid(capture(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8511"))
