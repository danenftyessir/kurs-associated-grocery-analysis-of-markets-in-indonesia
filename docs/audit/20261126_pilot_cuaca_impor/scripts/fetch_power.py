"""D-157: unduh cuaca harian NASA POWER (API titik, tanpa kunci) untuk 34 titik provinsi → data/raw/nasa_power/.

Titik = centroid poligon terbesar tiap provinsi (`data/reference/indonesia_provinces.geojson`), proksi wilayah pertanian (ibu kota
sering di pesisir). Variabel: PRECTOTCORR (hujan terkoreksi, mm/hari), T2M, T2M_MAX (°C). Periode 2016-01-01 .. 2026-11-20 (persetujuan
Danen 2026-11-26: 34 CSV, ± 10 MB). Berkas mentah tidak diubah; MANIFEST.csv mencatat url, sha256, waktu ambil.
Sumber: NASA Langley Research Center (LaRC) POWER Project, didanai NASA Earth Science/Applied Science Program (wajib dicantumkan).
"""
import csv
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "data", "raw", "nasa_power")
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M,T2M_MAX&community=AG"
       "&longitude={lon}&latitude={lat}&start=20160101&end=20261120&format=CSV")


def centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    a /= 2
    return abs(a), cx / (6 * a), cy / (6 * a)


def points():
    g = json.load(open(os.path.join(ROOT, "data", "reference", "indonesia_provinces.geojson"), encoding="utf-8"))
    out = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        area, lon, lat = max(centroid(p[0]) for p in polys)
        out.append((f["properties"]["province_id"], f["properties"]["province"], round(lat, 3), round(lon, 3)))
    return sorted(out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    man_path = os.path.join(OUT, "MANIFEST.csv")
    rows = []
    for pid, name, lat, lon in points():
        fn = f"power_daily_p{pid:02d}.csv"
        path = os.path.join(OUT, fn)
        url = URL.format(lat=lat, lon=lon)
        if not os.path.exists(path):
            req = urllib.request.Request(url, headers={"User-Agent": "kagami-research-client"})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(req, timeout=180) as r:
                        data = r.read()
                    break
                except Exception as e:  # noqa: BLE001
                    print(pid, "gagal", attempt, e, flush=True)
                    time.sleep(10)
            else:
                raise SystemExit(f"gagal unduh provinsi {pid}")
            open(path, "wb").write(data)
            time.sleep(1)
        data = open(path, "rb").read()
        rows.append({"province_id": pid, "province": name, "lat": lat, "lon": lon, "file": fn, "url": url,
                     "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                     "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
        print(pid, name, lat, lon, len(data), flush=True)
    with open(man_path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("total MB", round(sum(r["bytes"] for r in rows) / 1e6, 2))
