"""D-160C: ekspor publik SIJAGUNG (stok & pembelian jagung pabrik pakan per wilayah) dan SPORA (harga pakan), bulanan 2019-01..2026-10.

Persetujuan Danen 2026-11-26. Memakai tautan "Export" yang tersedia di halaman publik (GET, parameter sama dengan formulir halaman).
Berkas mentah tidak diubah → data/raw/ditjenpkh_pakan/ + MANIFEST.csv (url, sha256, content-type, waktu ambil).
"""
import csv
import hashlib
import os
import time
from datetime import datetime, timezone

import certifi
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "data", "raw", "ditjenpkh_pakan")
BASE = "https://simpakan.ditjenpkh.pertanian.go.id"
RANGE = {"bulan_awal": 1, "tahun_awal": 2019, "bulan_akhir": 10, "tahun_akhir": 2026}
JOBS = [
    ("sijagung_stok", "/sijagung/backend/web/site/data-stok-export", "LandingStok", {}, RANGE),
    ("sijagung_pembelian", "/sijagung/backend/web/site/data-pembelian-export", "LandingPembelian", {}, RANGE),
]
# SPORA: rentang 8 tahun membuat server kehabisan memori (HTTP 500, "Allowed memory size ... exhausted") → per tahun
for y in range(2019, 2027):
    rng = {"bulan_awal": 1, "tahun_awal": y, "bulan_akhir": 10 if y == 2026 else 12, "tahun_akhir": y}
    for nm, ex in (("broiler_BR2", {"jenis_ternak": 2, "jenis_pakan": 11}), ("layer_P3", {"jenis_ternak": 1, "jenis_pakan": 4}),
                   ("konsentrat_layer_KP3", {"jenis_ternak": 1, "jenis_pakan": 8})):
        JOBS.append((f"spora_harga_{nm}_{y}", "/spora/backend/web/site/data-harga-export", "LandingHarga", ex, rng))
EXT = {"spreadsheet": "xlsx", "excel": "xls", "csv": "csv", "html": "html", "pdf": "pdf"}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, path, form, extra, rng in JOBS:
        if any(f.startswith(name + "_") or f.startswith(name + ".") for f in os.listdir(OUT)):
            print(name, "sudah ada, dilewati", flush=True)
            continue
        params = {f"{form}[{k}]": v for k, v in {**extra, **rng}.items()}
        r = requests.get(BASE + path, params=params, headers={"User-Agent": "kagami-research-client"}, verify=certifi.where(), timeout=300)
        ct = r.headers.get("Content-Type", "")
        ext = next((e for k, e in EXT.items() if k in ct), "bin")
        fn = f"{name}_{rng['tahun_awal']}-{rng['bulan_awal']:02d}_{rng['tahun_akhir']}-{rng['bulan_akhir']:02d}.{ext}"
        if r.status_code != 200:
            print(name, "GAGAL", r.status_code, flush=True)
            rows.append({"file": "", "status": r.status_code, "content_type": ct, "bytes": len(r.content), "url": r.url, "sha256": "",
                         "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
            continue
        with open(os.path.join(OUT, fn), "wb") as fh:
            fh.write(r.content)
        rows.append({"file": fn, "status": r.status_code, "content_type": ct, "bytes": len(r.content), "url": r.url,
                     "sha256": hashlib.sha256(r.content).hexdigest(), "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
        print(name, r.status_code, ct, len(r.content), flush=True)
        time.sleep(1)
    with open(os.path.join(OUT, "MANIFEST.csv"), "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
