"""D-160B/D-161: pemetaan sel grid Gaussian T126 CFSv2 (384 × 190, scan utara → selatan) ke 34 provinsi → cfs_cell_province.json.

Lintang = arcsin titik Gauss–Legendre 190 (lat0 ≈ 89,277 dicek ulang di Colab dengan eccodes), bujur 0,9375° per sel. Sel di dalam poligon
provinsi (`data/reference/indonesia_provinces.geojson`, titik pusat sel) → provinsi; provinsi tanpa sel di dalamnya (kecil) memakai sel terdekat
dari ibu kota. Jalankan dari root project: `python docs/audit/20261126_sumber_baru/colab/build_cell_map.py [path_keluaran]`.
"""
import json
import os
import sys

import numpy as np
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "cfs_cell_province.json")

x, _ = np.polynomial.legendre.leggauss(190)
lats = np.degrees(np.arcsin(x))[::-1]          # utara → selatan (scan 0)
lons = np.arange(384) * 0.9375
print("lat0", round(lats[0], 3), "lat_last", round(lats[-1], 3))
g = json.load(open(os.path.join(HERE, "..", "..", "..", "..", "data", "reference", "indonesia_provinces.geojson"), encoding="utf-8"))
J = np.where((lats > -12) & (lats < 7))[0]
I = np.where((lons > 94) & (lons < 142))[0]
cells = [(j, i, lons[i], lats[j]) for j in J for i in I]
pts = np.array([[c[2], c[3]] for c in cells])
mapping, counts = [], {}
for f in g["features"]:
    pid = f["properties"]["province_id"]
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    inside = np.zeros(len(cells), bool)
    for poly in polys:
        inside |= Path(np.array(poly[0])).contains_points(pts)
    idx = np.where(inside)[0]
    if len(idx) == 0:   # provinsi kecil: sel terdekat dari ibu kota
        lat0, lon0 = f["properties"]["lat"], f["properties"]["lon"]
        idx = [int(np.argmin((pts[:, 0] - lon0) ** 2 + (pts[:, 1] - lat0) ** 2))]
    counts[pid] = len(idx)
    mapping += [[pid, int(cells[k][0]), int(cells[k][1])] for k in idx]
print("cells", len(mapping), "provinces", len(counts), "min/max cells", min(counts.values()), max(counts.values()))
print({k: v for k, v in sorted(counts.items()) if v <= 1})
json.dump({"lat_expected_first": float(lats[0]), "lon_step": 0.9375, "mapping": mapping}, open(OUT, "w"), separators=(",", ":"))
