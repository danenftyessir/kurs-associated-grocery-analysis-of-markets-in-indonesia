"""D-152 §4: daya validasi maju dari interval berpasangan test D-151 (IW_NAT − C1-tuned). Keluaran hasil/forward_power.csv."""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
pr = pd.read_csv(os.path.join(HERE, "..", "..", "20261125_pilot_produsen_intraminggu", "hasil", "iw_test_paired.csv"))
met = pd.read_csv(os.path.join(HERE, "..", "..", "20261125_pilot_produsen_intraminggu", "hasil", "iw_test_metrics.csv"))
rows = []
for _, r in pr.iterrows():
    h = int(r["horizon"])
    n_test = int(met.loc[(met["horizon"] == h) & (met["variant"] == "base"), "n_origins"].iloc[0])
    se = (r["hi"] - r["lo"]) / 3.92
    need = n_test * (2.8 * se / r["diff"]) ** 2          # origin berjarak 4 minggu untuk mendeteksi selisih titik D-151
    rows.append({"horizon": h, "n_test_origins": n_test, "diff_test": r["diff"], "se_test": se,
                 "mde_test": 2.8 * se,
                 "mde_forward_neff1": 2.8 * se * (n_test / 1) ** 0.5, "mde_forward_neff2": 2.8 * se * (n_test / 2) ** 0.5,
                 "origins_needed_4wk": need, "years_needed": need / 13})
out = pd.DataFrame(rows)
out.round(4).to_csv(os.path.join(HERE, "..", "hasil", "forward_power.csv"), index=False)
print(out.round(4).to_string(index=False))
