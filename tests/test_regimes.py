"""E2: profil respons per rezim HET/HAP pada data sintetis dengan β berbeda per rezim (D-124)."""

import numpy as np
import pandas as pd

from kagami.evaluation import regimes as R
from tests.test_local_projection import _drivers


def _regulation(rows):
    base = {"in_scope": True, "zone": "Nasional", "value_rp": np.nan, "end_date": np.nan, "commodity_raw": "",
            "source": "", "date_status": "effective", "value_min_rp": np.nan, "value_max_rp": np.nan}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_regulation_changes_filters_and_merges(cfg):
    reg = _regulation([
        {"commodity": "beras", "instrument": "HET", "start_date": "2023-03-31", "regulation": "A", "verification": "verified"},
        {"commodity": "beras", "instrument": "HET", "start_date": "2023-03-31", "regulation": "B", "verification": "partial"},
        {"commodity": "beras", "instrument": "HET", "start_date": "2024-04-24", "regulation": "C", "verification": "unverified"},
        {"commodity": "beras", "instrument": "HAP_produsen", "start_date": "2024-09-25", "regulation": "D",
         "verification": "verified"},
        {"commodity": "beras", "instrument": "HET", "start_date": "2016-01-01", "regulation": "E", "verification": "verified"},
        {"commodity": "gula_pasir", "instrument": "HAP_konsumen", "start_date": "2024-09-25", "regulation": "F",
         "verification": "verified", "in_scope": False},
    ])
    ch = R.regulation_changes(cfg, reg)
    assert list(ch["commodity"]) == ["beras"] and ch["change_date"].iloc[0] == pd.Timestamp("2023-03-31")
    assert ch["regulation"].iloc[0] == "A; B"            # tanggal sama digabung; unverified, produsen, di luar periode dibuang


def test_regime_table_bounds(cfg):
    ch = pd.DataFrame({"commodity": ["beras", "beras"], "change_date": pd.to_datetime(["2022-01-03", "2024-01-01"]),
                       "regulation": ["X", "Y"]})
    t = R.regime_table(cfg, ch)
    assert list(t["regime_id"]) == [0, 1, 2]
    assert t["regime_start"].iloc[0] == pd.Timestamp(cfg.params["period"]["start"])
    assert t["regime_end"].iloc[0] == pd.Timestamp("2022-01-02") and t["regime_start"].iloc[1] == pd.Timestamp("2022-01-03")
    assert t["regime_end"].iloc[2] == pd.Timestamp(cfg.params["period"]["freeze"])
    assert t["label"].iloc[0] == "sebelum X" and t["label"].iloc[2] == "Y"


def test_regime_profiles_recover_regime_specific_beta(cfg):
    drv = _drivers(cfg, seed=5)
    change = pd.Timestamp("2022-06-06")
    weeks = drv["week"][drv["week"] >= pd.Timestamp(cfg.params["period"]["start"])]
    d = drv.set_index("week").loc[weeks]
    beta = np.where(weeks < change, 0.2, 0.9)                    # β kurs berbeda per rezim
    common = np.cumsum(beta * d["de"].fillna(0).to_numpy())
    rng = np.random.default_rng(7)
    panel = pd.concat([pd.DataFrame({"week": weeks, "province_id": u, "commodity": "gula_pasir",
                                     "log_price": 8 + u / 10 + common + rng.normal(0, 0.002, len(weeks)).cumsum()})
                       for u in range(1, 16)], ignore_index=True)
    reg = _regulation([{"commodity": "gula_pasir", "instrument": "HAP_konsumen", "start_date": str(change.date()),
                        "regulation": "Perbadan sintetis", "verification": "verified"}])
    out = R.regime_profiles(cfg, panel, drv, None, reg, horizons=[0, 4])
    assert set(R.REGIME_COLUMNS) <= set(out.columns)
    e0 = out[(out["driver"] == "e") & (out["horizon"] == 0)].set_index("regime_id")
    assert set(e0.index) == {0, 1}
    assert abs(e0.loc[0, "estimate"] - 0.2) < 0.02 and abs(e0.loc[1, "estimate"] - 0.9) < 0.02   # h = 0: tanpa noise kurs masa depan
    e4 = out[(out["driver"] == "e") & (out["horizon"] == 4)].set_index("regime_id")
    true4 = pd.Series({0: 0.2, 1: 0.9})
    assert ((e4["estimate"] - true4).abs() <= 2 * e4["se"]).all()                              # h = 4: dalam ±2 SE
    assert not e0.loc[0, "baseline_in_ci"] and not e0.loc[1, "baseline_in_ci"]                # pooled ≈ 0,55 di luar keduanya
    assert e0.loc[0, "regime_end"] < change <= e0.loc[1, "regime_start"]
    assert (e0["n_weeks"] > 0).all() and e0.loc[0, "label"] == "sebelum Perbadan sintetis"
