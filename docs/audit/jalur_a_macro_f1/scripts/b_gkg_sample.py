"""Jalur A Workstream B2: pilot GDELT GKG 2.1 Translingual — sampel berkas 15 menit periode dev untuk kelayakan & validasi manual.

Bukan sumber fitur (cakupan sampel ± 0,05% batch); tujuannya: (a) volume & sumber berita berbahasa Indonesia, (b) ketersediaan judul,
(c) presisi penyaring kata kunci komoditas/pasokan (validasi manual), (d) lag `DATE` GDELT vs tanggal terbit di URL, (e) duplikasi
sindikasi, (f) ukuran kolom per rekaman → estimasi byte BigQuery.

Desain sampel (ditetapkan sebelum unduh): 48 batch acak, seed 20261126, tanggal seragam 2019-01-01..2023-12-31, jam seragam pada grid
15 menit 00:00–11:45 UTC (07.00–18.45 WIB, jam terbit media Indonesia). Berkas `<ts>.translation.gkg.csv.zip` dari data.gdeltproject.org
(data terbuka GDELT). Berkas mentah disimpan di luar repo (argumen --raw-dir); hanya metadata artikel yang cocok + ringkasan yang disimpan.

Penyaring (D-165 pilot):
  bahasa  : TranslationInfo diawali `srclc:ind`
  komoditas (judul atau slug URL): pola KOMODITAS per id KAGAMI
  pasokan/kebijakan (judul atau slug URL): pola SUPPLY
→ hasil/b_gkg_sample_files.csv (ts, ukuran, sha256, rekaman), hasil/b_gkg_sample_articles.csv (kandidat), hasil/b_gkg_sample_summary.json
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hasil")
COLS = ["GKGRECORDID", "DATE", "SourceCollectionIdentifier", "SourceCommonName", "DocumentIdentifier", "Counts", "V2Counts", "Themes",
        "V2Themes", "Locations", "V2Locations", "Persons", "V2Persons", "Organizations", "V2Organizations", "V2Tone", "Dates", "GCAM",
        "SharingImage", "RelatedImages", "SocialImageEmbeds", "SocialVideoEmbeds", "Quotations", "AllNames", "Amounts", "TranslationInfo",
        "Extras"]
KOMODITAS = {
    "beras": r"beras|padi|gabah",
    "bawang_putih": r"bawang putih",
    "bawang_merah": r"bawang merah",
    "cabai": r"cabai|cabe|cabai rawit|cabai merah",
    "gula_pasir": r"gula pasir|gula kristal|\bgula\b",
    "minyak_goreng": r"minyak goreng|migor|minyakita|\bcpo\b|sawit",
    "daging_sapi": r"daging sapi|sapi impor|sapi bakalan",
    "daging_ayam": r"daging ayam|ayam ras|ayam broiler|live bird",
    "telur_ayam": r"telur ayam|harga telur|\btelur\b",
    "umum": r"sembako|bahan pokok|bapok|pangan|bulog|bapanas|inflasi pangan",
}
SUPPLY = (r"pasokan|stok|panen|gagal panen|impor|ekspor|larangan ekspor|distribusi|banjir|kekeringan|kemarau|el nino|la nina|"
          r"operasi pasar|\bhet\b|\bhap\b|harga eceran tertinggi|kelangkaan|langka|cadangan|produksi|petani|peternak|pakan|subsidi|kuota|"
          r"\bdmo\b|\bdpo\b|gudang|penimbunan|timbun|bencana|longsor|gempa|cuaca|hama|serangan|wabah|flu burung|pmk|kapal|pelabuhan|"
          r"bbm|ongkos angkut|mudik|lebaran|ramadan|natal|tahun baru|stabilisasi|sphp|pasar murah|gerakan pangan murah|neraca")
KPAT = {k: re.compile(v, re.I) for k, v in KOMODITAS.items()}
SPAT = re.compile(SUPPLY, re.I)
DATE_IN_URL = [re.compile(r"/(20\d\d)/(\d\d)/(\d\d)/"), re.compile(r"/(20\d\d)(\d\d)(\d\d)\d*"), re.compile(r"-(20\d\d)(\d\d)(\d\d)")]


def sample_timestamps(n=48, seed=20261126):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2019-01-01", "2023-12-31", freq="D")
    d = days[rng.integers(0, len(days), n)]
    q = rng.integers(0, 48, n)                           # 48 slot 15 menit = 00:00..11:45 UTC
    ts = sorted({(x + pd.Timedelta(minutes=15 * int(k))).strftime("%Y%m%d%H%M%S") for x, k in zip(d, q)})
    return ts


def title_of(extras):
    m = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", extras or "")
    return m.group(1).strip() if m else ""


def slug_text(url):
    u = re.sub(r"^https?://[^/]+", "", url or "")
    u = re.sub(r"\.(html?|php|aspx?)$", "", u)
    return re.sub(r"[-_/+]", " ", u)


def url_date(url):
    for p in DATE_IN_URL:
        m = p.search(url or "")
        if m:
            try:
                return pd.Timestamp(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                continue
    return pd.NaT


def classify(text):
    comms = [k for k, p in KPAT.items() if p.search(text)]
    return comms, bool(SPAT.search(text))


def parse(raw_bytes):
    rows = [r.split("\t") for r in raw_bytes.decode("utf-8", "replace").split("\n") if r]
    return [r for r in rows if len(r) >= 27]


def fetch(ts, raw_dir):
    p = os.path.join(raw_dir, f"{ts}.translation.gkg.csv.zip")
    if not os.path.exists(p):
        time.sleep(1.0)
        req = urllib.request.Request(f"https://data.gdeltproject.org/gdeltv2/{ts}.translation.gkg.csv.zip",
                                     headers={"User-Agent": "research-client"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read()
        except Exception as e:  # berkas tidak ada untuk batch itu (GDELT kadang melewatkan batch)
            return None, str(e)
        open(p, "wb").write(b)
    return p, None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--n", type=int, default=48)
    a = ap.parse_args()
    os.makedirs(a.raw_dir, exist_ok=True)
    files, arts = [], []
    colbytes, nrec_all = collections.Counter(), 0
    for ts in sample_timestamps(a.n):
        p, err = fetch(ts, a.raw_dir)
        if p is None:
            files.append({"ts": ts, "ok": False, "error": err})
            continue
        raw = zipfile.ZipFile(p).read(zipfile.ZipFile(p).namelist()[0])
        rows = parse(raw)
        nrec_all += len(rows)
        for r in rows:
            for i, v in enumerate(r[:27]):
                colbytes[COLS[i]] += len(v.encode("utf-8"))
        ind = [r for r in rows if r[25].startswith("srclc:ind")]
        n_title = sum(1 for r in ind if title_of(r[26]))
        n_match = 0
        for r in ind:
            t = title_of(r[26])
            text = f"{t} {slug_text(r[4])}"
            comms, sup = classify(text)
            if not comms:
                continue
            n_match += 1
            locs = [x.split("#") for x in r[10].split(";") if x]
            adm1 = sorted({x[3] for x in locs if len(x) > 3 and x[2] == "ID" and x[3] not in ("ID", "")})
            arts.append({"ts": ts, "gdelt_date": r[1], "source": r[3], "url": r[4], "title": t, "commodities": ";".join(comms),
                         "supply_kw": sup, "url_date": url_date(r[4]), "id_adm1": ";".join(adm1),
                         "themes_top": ";".join(sorted({x.split(",")[0] for x in r[8].split(";") if x})[:25])})
        files.append({"ts": ts, "ok": True, "bytes_zip": os.path.getsize(p), "sha256_zip": hashlib.sha256(open(p, "rb").read()).hexdigest(),
                      "bytes_raw": len(raw), "n_records": len(rows), "n_ind": len(ind), "n_ind_title": n_title, "n_match_commodity": n_match})
        print(f"[b2] {ts} rekaman {len(rows)} ind {len(ind)} cocok {n_match}", flush=True)
    F = pd.DataFrame(files)
    A = pd.DataFrame(arts)
    F.to_csv(os.path.join(OUT, "b_gkg_sample_files.csv"), index=False)
    A.to_csv(os.path.join(OUT, "b_gkg_sample_articles.csv"), index=False, date_format="%Y-%m-%d")
    ok = F[F["ok"]]
    summ = {"n_batches_sampled": int(len(F)), "n_batches_ok": int(len(ok)), "records": int(ok["n_records"].sum()),
            "records_per_batch_mean": float(ok["n_records"].mean()), "ind_per_batch_mean": float(ok["n_ind"].mean()),
            "ind_per_batch_by_year": ok.assign(y=ok["ts"].str[:4]).groupby("y")["n_ind"].mean().round(1).to_dict(),
            "share_ind_with_title_by_year": ok.assign(y=ok["ts"].str[:4]).groupby("y").apply(
                lambda g: float(g["n_ind_title"].sum() / max(g["n_ind"].sum(), 1)), include_groups=False).round(3).to_dict(),
            "match_per_batch_mean": float(ok["n_match_commodity"].mean()),
            "raw_bytes_per_record": float(ok["bytes_raw"].sum() / ok["n_records"].sum()),
            "col_bytes_per_record": {k: round(v / max(nrec_all, 1), 1) for k, v in colbytes.most_common()},
            "n_candidates": int(len(A)), "n_candidates_supply_kw": int(A["supply_kw"].sum()) if len(A) else 0}
    json.dump(summ, open(os.path.join(OUT, "b_gkg_sample_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))
