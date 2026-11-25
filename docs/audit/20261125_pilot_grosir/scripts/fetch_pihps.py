"""Ambil PIHPS harian per provinsi untuk satu jenis pasar (default 3 = Pedagang Besar) → zip berformat sama dengan snapshot `pihps`.

Sumber: endpoint grid situs PIHPS (`WebSite/TabelHarga/GetGridDataDaerah`) = data yang diekspor tombol "Download" resmi tabel
(`exportToExcel` grid; lihat docs/audit/20261125_sumber_data_hulu.md, U19). Permintaan per bulan per provinsi (biaya server naik
tajam dengan panjang rentang: 1 bulan ± 1 dtk, 1 tahun ± 62 dtk), 3 paralel, jeda kecil, coba ulang 3×; cache per (provinsi, bulan)
agar dapat dilanjutkan. Keluaran: zip berisi pihps_provNN_<Nama>.csv (province_id, province, level, commodity, <tanggal ISO>...),
MANIFEST.csv (sha256 per berkas, endpoint, price_type, retrieved_at), ERRORS.json.

Pemakaian: python fetch_pihps.py --price-type 3 --out data/raw/bi_pihps/<nama>.zip [--start 2017-03-01 --end 2026-11-19]
"""
import argparse
import hashlib
import io
import json
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import certifi
import pandas as pd
import requests

BASE = "https://www.bi.go.id/hargapangan/WebSite/TabelHarga/"
HEADERS = {"User-Agent": "Mozilla/5.0 (research client)", "X-Requested-With": "XMLHttpRequest"}
PRICE_TYPES = {1: "Pasar Tradisional", 2: "Pasar Modern", 3: "Pedagang Besar", 4: "Produsen"}


def get(endpoint, params, tries=3):
    for k in range(tries):
        try:
            r = requests.get(BASE + endpoint, params=params, headers=HEADERS, verify=certifi.where(), timeout=300)
            r.raise_for_status()
            return r.json()["data"]
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


def month_ranges(start, end):
    s = pd.Timestamp(start).to_period("M")
    for p in pd.period_range(s, pd.Timestamp(end).to_period("M"), freq="M"):
        a = max(p.start_time, pd.Timestamp(start))
        b = min(p.end_time.normalize(), pd.Timestamp(end))
        yield a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")


def fetch_one(pt, pid, a, b, cache):
    f = os.path.join(cache, f"p{pt}_{pid:02d}_{a}.json")
    if os.path.exists(f):
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    data = get("GetGridDataDaerah", dict(price_type_id=pt, comcat_id="", province_id=pid, regency_id="", market_id="",
                                         tipe_laporan=1, start_date=a, end_date=b))
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    time.sleep(0.2)
    return data


def to_wide(pid, name, chunks):
    order, vals = [], {}
    for rows in chunks:
        for r in rows:
            key = (int(r["level"]), r["name"])
            if key not in vals:
                order.append(key)
                vals[key] = {}
            for k, v in r.items():
                if "/" in k:
                    d = datetime.strptime(k, "%d/%m/%Y").strftime("%Y-%m-%d")
                    s = str(v).replace(",", "").strip()
                    vals[key][d] = float(s) if s not in ("", "-", "None", "null") else None
    dates = sorted({d for v in vals.values() for d in v})
    rows = [{"province_id": pid, "province": name, "level": lv, "commodity": nm, **{d: vals[(lv, nm)].get(d) for d in dates}}
            for lv, nm in order]
    return pd.DataFrame(rows, columns=["province_id", "province", "level", "commodity"] + dates)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price-type", type=int, default=3)
    ap.add_argument("--start", default="2017-03-01")
    ap.add_argument("--end", default="2026-11-19")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=os.path.join(os.environ.get("TEMP", "."), "pihps_cache"))
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    provs = get("GetRefProvince", {})
    months = list(month_ranges(a.start, a.end))
    jobs = [(p["id"], p["name"], s, e) for p in provs for s, e in months]
    print(f"[fetch] price_type={a.price_type} provinsi={len(provs)} bulan={len(months)} permintaan={len(jobs)}", flush=True)
    res, errors, t0 = {}, [], time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        fut = {ex.submit(fetch_one, a.price_type, pid, s, e, a.cache): (pid, s) for pid, _, s, e in jobs}
        for i, f in enumerate(as_completed(fut), 1):
            pid, s = fut[f]
            try:
                res[(pid, s)] = f.result()
            except Exception as e:  # noqa: BLE001
                errors.append({"province_id": pid, "start": s, "error": str(e)[:200]})
            if i % 200 == 0:
                print(f"[fetch] {i}/{len(jobs)} {time.time() - t0:.0f} dtk, galat {len(errors)}", flush=True)
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    buf, manifest = io.BytesIO(), []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in provs:
            pid, name = p["id"], p["name"]
            chunks = [res[(pid, s)] for s, _ in months if (pid, s) in res]
            df = to_wide(pid, name, chunks)
            fname = f"pihps_prov{pid:02d}_{name.replace(' ', '_')}.csv"
            raw = df.to_csv(index=False).encode("utf-8")
            z.writestr(fname, raw)
            dcols = [c for c in df.columns[4:] if df[c].notna().any()]
            manifest.append({"file": fname, "rows": len(df), "n_dates": len(dcols), "first_date": dcols[0] if dcols else None,
                             "last_date": dcols[-1] if dcols else None, "bytes": len(raw),
                             "file_sha256": hashlib.sha256(raw).hexdigest(), "source": "PIHPS Nasional (BI)",
                             "endpoint": "WebSite/TabelHarga/GetGridDataDaerah",
                             "price_type": f"{a.price_type} ({PRICE_TYPES[a.price_type]})", "report_type": "tipe_laporan=1 (harian)",
                             "retrieved_at": retrieved, "n_requests": len(chunks)})
        z.writestr("MANIFEST.csv", pd.DataFrame(manifest).to_csv(index=False))
        z.writestr("ERRORS.json", json.dumps(errors, indent=1))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} sudah ada; tidak menimpa data mentah")
    with open(a.out, "wb") as fh:
        fh.write(buf.getvalue())
    print(f"[fetch] selesai {time.time() - t0:.0f} dtk → {a.out} ({len(buf.getvalue()) / 1e6:.1f} MB), galat {len(errors)}", flush=True)


if __name__ == "__main__":
    main()
