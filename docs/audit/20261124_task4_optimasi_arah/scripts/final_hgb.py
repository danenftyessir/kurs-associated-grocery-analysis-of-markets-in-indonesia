"""Konfigurasi terpilih (dibekukan dari origin pengembangan) dijalankan pada SEMUA origin, rolling-origin."""
import sys, json; sys.path.insert(0, r"<EXP_DIR>")
from engine import *
name = sys.argv[1]
b = json.load(open(fr"<EXP_DIR>/best_{name}.json"))
for h in (4, 8):
    with Timer() as t:
        r = run(h, "all", feature_cols(b["groups"], h, b["fx"]), params=b["best"]["params"], n_jobs=12)
    r.to_parquet(fr"<EXP_DIR>/preds/final_{name}_h{h}.parquet")
    print(name, h, len(r), r.origin.nunique(), round(t.s), flush=True)
