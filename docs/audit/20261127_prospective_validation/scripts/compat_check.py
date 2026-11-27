"""Validasi prospektif: bandingkan zip PIHPS eceran hasil fetch_pihps.py --price-type 1 dengan snapshot beku `pihps`.

Pemakaian (dari root project): python docs/audit/20261127_prospective_validation/scripts/compat_check.py <zip baru>
Jendela banding tetap 2026-09-01..2026-11-18 (tanggal terakhir snapshot beku). Untuk cek revisi saat evaluasi, ganti `lo`/`hi`
menjadi seluruh periode bersama; JANGAN membandingkan tanggal sesudah 2026-11-18 (tidak ada di snapshot beku).
"""
import importlib.util, sys, types, zipfile, io
spec = importlib.util.spec_from_file_location("kagami", "src/__init__.py", submodule_search_locations=["src"])
mod = importlib.util.module_from_spec(spec); sys.modules["kagami"] = mod; spec.loader.exec_module(mod)
import pandas as pd, numpy as np
from kagami.utils.config import get_config
from kagami.data.loaders import load_pihps
from kagami.data.weekly import select_variants
cfg = get_config()
new_zip = sys.argv[1]
def daily(p):
    shim = types.SimpleNamespace(source_path=lambda key: p)
    return select_variants(cfg, load_pihps(shim, "pihps"))
old = daily(str(cfg.source_path("pihps"))); new = daily(new_zip)
lo, hi = pd.Timestamp("2026-09-01"), pd.Timestamp("2026-11-18")
old = old[(old.date >= lo) & (old.date <= hi)]
print("kolom", list(new.columns))
k = ["date", "province_id", "commodity"]
m = old[k + ["price"]].merge(new[k + ["price"]], on=k, how="outer", suffixes=("_old", "_new"), indicator=True)
print(m["_merge"].value_counts().to_dict())
b = m[m["_merge"] == "both"]
eq = np.isclose(b.price_old, b.price_new)
print("baris bersama", len(b), "harga sama", int(eq.sum()), "beda", int((~eq).sum()))
d = b[~eq].assign(rel=lambda x: x.price_new / x.price_old - 1)
if len(d):
    print(d.groupby("commodity").size().to_dict()); print(d.sort_values("date").tail(15).to_string(index=False))
    print("beda per tanggal (10 terakhir)", d.groupby("date").size().tail(10).to_dict())
only_new = m[m["_merge"] == "right_only"]; only_old = m[m["_merge"] == "left_only"]
print("hanya baru per tanggal", only_new.groupby("date").size().tail(8).to_dict())
print("hanya lama per tanggal", only_old.groupby("date").size().tail(8).to_dict())
print("hanya baru per komoditas", only_new.groupby("commodity").size().to_dict())
print("hanya lama per komoditas", only_old.groupby("commodity").size().to_dict())
print("tanggal terakhir baru", new.date.max(), "lama", old.date.max())
