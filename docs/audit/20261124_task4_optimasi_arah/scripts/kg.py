import importlib.util, sys, os
ROOT = r"C:\Users\HYPE R Series\OneDrive - Institut Teknologi Bandung\Documents\ITB\Competition\datmin"
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("kagami", "src/__init__.py", submodule_search_locations=["src"])
mod = importlib.util.module_from_spec(spec); sys.modules["kagami"] = mod; spec.loader.exec_module(mod)
from kagami.utils.config import get_config
from kagami.utils.io import read_artifact
cfg = get_config()
def load():
    return (read_artifact(cfg, "panel_weekly"), read_artifact(cfg, "drivers_weekly"), read_artifact(cfg, "world_prices_weekly"))
