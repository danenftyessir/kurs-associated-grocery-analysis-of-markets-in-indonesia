"""D-160B: tulis notebook Colab `kagami_d160_cfsv2.ipynb` (ekstraksi prakiraan operasional CFSv2 → agregat provinsi mingguan).

Notebook: pasang eccodes, (opsional) mount Drive, untuk setiap minggu t (Senin 2017-12-25 .. 2026-11-16) ambil run 00Z hari Jumat minggu t (cadangan
Kamis, Rabu — tersedia sebelum Minggu 00.00 = available_at harga minggu t, D-155), byte-range 56 hari pertama `prate` & `tmax` dari
fileServer THREDDS NCEI (layanan subset rusak), dekode JPEG2000 dengan eccodes, rerata sel grid per provinsi (pemetaan
`cfs_cell_province.json`), simpan agregat per run (checkpoint di OUT) → CSV gabungan + zip parts + unduh (files.download).
"""
import json
import os

import nbformat

HERE = os.path.dirname(os.path.abspath(__file__))
MAPPING = json.load(open(os.path.join(HERE, "cfs_cell_province.json"), encoding="utf-8"))

SETUP = "!pip -q install eccodes requests\n"
CODE = r'''
import os, json, struct, time, hashlib, datetime as dt
import numpy as np, pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import eccodes
# Run 2026-11-26: drive.mount gagal (timeout menunggu popup OAuth) -> output lokal /content, hasil diambil lewat files.download (sel terakhir).
USE_DRIVE = False
if USE_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    ROOT = '/content/drive/MyDrive/KAGAMI' if os.path.isdir('/content/drive/MyDrive/KAGAMI') else '/content/drive/MyDrive'
else:
    ROOT = '/content'
OUT = os.path.join(ROOT, 'experiments', 'd160_cfsv2'); PARTS = os.path.join(OUT, 'parts')
os.makedirs(PARTS, exist_ok=True); print('OUT', OUT)

MAP = json.loads(MAPPING_JSON)
LAT_EXPECTED_FIRST = MAP['lat_expected_first']
CELLS = np.array(MAP['mapping'])               # [province_id, j, i]
PIDS = sorted(set(CELLS[:, 0].tolist()))
BASE = 'https://www.ncei.noaa.gov/thredds/fileServer/model-cfs_v2_for_ts'
DAYS, STEP_H = 56, 6
NEED_H = DAYS * 24
S = requests.Session(); S.headers.update({'User-Agent': 'kagami-research-client'})

def url(day, var):
    s = day.strftime('%Y%m%d')
    return f"{BASE}/{s[:4]}/{s[:6]}/{s}/{s}00/{var}.01.{s}00.daily.grb2"

def fhour(msg):
    L1 = struct.unpack('>I', msg[16:20])[0]; p = 16 + L1
    while p < len(msg) - 4:
        sl = struct.unpack('>I', msg[p:p+4])[0]; sn = msg[p+4]
        if sn == 4:
            unit = msg[p+17]; v = struct.unpack('>I', msg[p+18:p+22])[0]
            return v * {0: 1/60, 1: 1, 2: 24}.get(unit, 1)
        p += sl
    return None

def fetch_msgs(u):
    buf, start, chunk = b'', 0, 9_500_000
    msgs, off = [], 0
    while True:
        r = S.get(u, headers={'Range': f'bytes={start}-{start + chunk - 1}'}, timeout=300)
        if r.status_code not in (200, 206):
            raise RuntimeError(f'HTTP {r.status_code}')
        buf += r.content; start += len(r.content)
        while off + 16 <= len(buf):
            L = struct.unpack('>Q', buf[off+8:off+16])[0]
            if off + L > len(buf): break
            m = buf[off:off+L]; h = fhour(m)
            msgs.append((h, m)); off += L
            if h is not None and h >= NEED_H:
                return msgs, buf[:off]
        if len(r.content) < chunk:
            return msgs, buf[:off]
        chunk = 3_000_000

def decode(msgs, kind):
    daily = np.full((DAYS, 190, 384), np.nan, np.float32); cnt = np.zeros(DAYS)
    for h, m in msgs:
        if h is None or h <= 0 or h > NEED_H: continue
        d = int((h - 1) // 24)
        gid = eccodes.codes_new_from_message(bytes(m))
        try:
            v = eccodes.codes_get_values(gid).reshape(190, 384).astype(np.float32)
        finally:
            eccodes.codes_release(gid)
        if kind == 'prate':
            daily[d] = np.nan_to_num(daily[d]) + v * 86400 / 4      # mm/hari: rerata 4 laju 6 jam
        else:
            daily[d] = v - 273.15 if cnt[d] == 0 else np.fmax(daily[d], v - 273.15)
        cnt[d] += 1
    return daily, cnt

def province_means(daily):
    out = np.full((len(PIDS), DAYS), np.nan)
    for k, pid in enumerate(PIDS):
        c = CELLS[CELLS[:, 0] == pid]
        out[k] = np.nanmean(daily[:, c[:, 1], c[:, 2]], axis=1)
    return out

def check_grid(m):
    gid = eccodes.codes_new_from_message(bytes(m))
    try:
        lat = eccodes.codes_get_array(gid, 'latitudes').reshape(190, 384)[:, 0]
    finally:
        eccodes.codes_release(gid)
    assert abs(lat[0] - LAT_EXPECTED_FIRST) < 0.01, lat[:3]
    return float(lat[0])

def one_week(week):
    part = os.path.join(PARTS, f"{week.date()}.json")
    if os.path.exists(part):
        return 'skip'
    rec = {'week': str(week.date())}
    for off_days in (4, 3, 2):                              # Jumat, Kamis, Rabu 00Z
        day = week + pd.Timedelta(days=off_days)
        try:
            res = {}
            for var in ('prate', 'tmax'):
                msgs, raw = fetch_msgs(url(day, var))
                res[var] = (msgs, raw)
            rec['init'] = day.strftime('%Y-%m-%dT00')
            break
        except Exception as e:
            rec[f'err_{off_days}'] = str(e)[:120]
    else:
        json.dump(rec, open(part, 'w')); return 'missing'
    P, cp = decode(res['prate'][0], 'prate'); T, ct = decode(res['tmax'][0], 'tmax')
    pp, pt = province_means(P), province_means(T)
    rows = []
    for k, pid in enumerate(PIDS):
        rows.append({'province_id': int(pid), 'r_1_28': float(np.nansum(pp[k, :28])), 'r_29_56': float(np.nansum(pp[k, 28:])),
                     'r_1_56': float(np.nansum(pp[k])), 'rmax_1_28': float(np.nanmax(pp[k, :28])),
                     'tx_1_28': float(np.nanmean(pt[k, :28])), 'tx_29_56': float(np.nanmean(pt[k, 28:]))})
    rec.update({'rows': rows, 'days_prate_complete': int((cp == 4).sum()), 'days_tmax_complete': int((ct == 4).sum()),
                'bytes_prate': len(res['prate'][1]), 'bytes_tmax': len(res['tmax'][1]),
                'sha_prate': hashlib.sha256(res['prate'][1]).hexdigest(), 'sha_tmax': hashlib.sha256(res['tmax'][1]).hexdigest()})
    np.savez_compressed(os.path.join(PARTS, f"{week.date()}_daily.npz"), prate=pp.astype(np.float32), tmax=pt.astype(np.float32))
    json.dump(rec, open(part, 'w'))
    return 'ok'

# uji satu run + cek grid
m0, _ = fetch_msgs(url(pd.Timestamp('2022-12-23'), 'prate'))
print('cek grid lat0', check_grid(m0[0][1]), 'pesan', len(m0), 'jam terakhir', m0[-1][0])

weeks = list(pd.date_range('2017-12-25', '2026-11-16', freq='W-MON'))
t0 = time.time(); done = {}
with ThreadPoolExecutor(6) as ex:
    futs = {ex.submit(one_week, w): w for w in weeks}
    for i, f in enumerate(as_completed(futs), 1):
        try:
            s = f.result()
        except Exception as e:
            s = 'error: ' + str(e)[:100]
        done[s.split(':')[0]] = done.get(s.split(':')[0], 0) + 1
        if i % 25 == 0:
            print(i, len(weeks), round(time.time() - t0), 's', done, flush=True)
print('selesai', round(time.time() - t0), 's', done)
'''

ASSEMBLE = r'''
import glob
recs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(PARTS, '*.json')))]
rows = []
for r in recs:
    for x in r.get('rows', []):
        rows.append({'week': r['week'], 'init': r.get('init'), **x, 'days_prate_complete': r.get('days_prate_complete'),
                     'days_tmax_complete': r.get('days_tmax_complete')})
df = pd.DataFrame(rows)
man = pd.DataFrame([{k: r.get(k) for k in ('week', 'init', 'bytes_prate', 'bytes_tmax', 'sha_prate', 'sha_tmax', 'days_prate_complete', 'days_tmax_complete')} | {'errors': '; '.join(v for k, v in r.items() if k.startswith('err_'))} for r in recs])
df.to_csv(os.path.join(OUT, 'cfsv2_province_weekly.csv'), index=False)
man.to_csv(os.path.join(OUT, 'cfsv2_manifest.csv'), index=False)
print(df.shape, man['init'].isna().sum(), 'minggu tanpa run'); print(df.describe().round(2))
import shutil
shutil.make_archive(os.path.join(OUT, 'cfsv2_parts'), 'zip', PARTS)   # agregat harian per provinsi (npz) + json per run
from google.colab import files
for fn in ('cfsv2_province_weekly.csv', 'cfsv2_manifest.csv', 'cfsv2_parts.zip'):
    files.download(os.path.join(OUT, fn))
'''

nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_markdown_cell("# KAGAMI D-160B — ekstraksi prakiraan operasional NOAA CFSv2 (prate, tmax) → agregat provinsi mingguan\n"
                                          "Persetujuan Danen 2026-11-26. Sumber: NCEI THREDDS fileServer (byte-range 56 hari pertama)."),
            nbformat.v4.new_code_cell(SETUP),
            nbformat.v4.new_code_cell("MAPPING_JSON = " + repr(json.dumps(MAPPING, separators=(",", ":"))) + "\n" + CODE),
            nbformat.v4.new_code_cell(ASSEMBLE)]
nb.metadata["colab"] = {"provenance": []}
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3"}
nbformat.write(nb, os.path.join(HERE, "kagami_d160_cfsv2.ipynb"))
print("ok")
