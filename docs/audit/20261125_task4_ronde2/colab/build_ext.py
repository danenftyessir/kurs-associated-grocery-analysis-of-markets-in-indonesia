"""Colab: bangun tabel fitur (feature_table + price_dynamics) dari artefak di folder Drive tim → parquet lokal."""
import os, sys
code, team, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ["KAGAMI_ROOT"] = code
os.environ["KAGAMI_ARTIFACT_DIRS"] = team
os.environ["KAGAMI_OUT_DIR"] = "/content/kagami_out"
os.environ["KAGAMI_TRACKING"] = "0"
sys.path.insert(0, os.path.dirname(code))
import importlib.util
spec = importlib.util.spec_from_file_location("kagami", os.path.join(code, "src", "__init__.py"),
                                              submodule_search_locations=[os.path.join(code, "src")])
mod = importlib.util.module_from_spec(spec); sys.modules["kagami"] = mod; spec.loader.exec_module(mod)
from kagami.utils.config import get_config
from kagami.utils.io import read_artifact
from kagami.features.forecast import feature_table
from kagami.features.price_dynamics import extend_table
cfg = get_config()
pw, dr, wd = (read_artifact(cfg, n) for n in ("panel_weekly", "drivers_weekly", "world_prices_weekly"))
ext = extend_table(feature_table(cfg, pw, dr, wd, [4, 8]), pw, [4, 8])
ext.to_parquet(out)
print("ext", ext.shape, "->", out)
