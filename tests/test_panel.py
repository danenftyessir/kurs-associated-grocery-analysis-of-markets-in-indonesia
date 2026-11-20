"""WP-08: panel 7 wilayah (indeks log, bebas lompatan komposisi)."""

import numpy as np
import pandas as pd
import pytest

from kagami.data.panel import build_region_panel


def _weekly(cfg, n_weeks=10):
    weeks = pd.date_range("2018-01-01", periods=n_weeks, freq="W-MON")
    reg = cfg.regions
    rows = []
    for pid in reg["province_id"]:
        for t, wk in enumerate(weeks):
            # level berbeda per provinsi (pid/10), tren bersama 0.01 per minggu
            rows.append({"week": wk, "province_id": pid, "commodity": "beras",
                         "log_price": 9 + pid / 10 + 0.01 * t, "status": "observed"})
    w = pd.DataFrame(rows)
    elig = pd.DataFrame({"province_id": reg["province_id"], "commodity": "beras", "eligible": True})
    return w, elig, weeks


def test_region_panel_shape_and_index(cfg):
    w, elig, weeks = _weekly(cfg)
    r = build_region_panel(cfg, w, elig)
    assert len(r) == 7 * len(weeks)
    assert set(r["region"]) == set(cfg.regions["region"])
    assert list(r.columns) == ["week", "region", "commodity", "log_price_index", "n_provinces"]
    first = r[r["week"] == weeks[0]]
    assert np.allclose(first["log_price_index"], 0)                  # indeks relatif minggu pertama
    assert np.allclose(r.groupby("region")["log_price_index"].diff().dropna(), 0.01)
    n = r[r["week"] == weeks[0]].set_index("region")["n_provinces"]
    assert n.to_dict() == cfg.regions.groupby("region").size().to_dict()


def test_region_panel_composition_change_no_jump(cfg):
    w, elig, weeks = _weekly(cfg)
    papua = cfg.regions.loc[cfg.regions["region"] == "Papua", "province_id"]
    drop = w["province_id"].eq(papua.iloc[0]) & w["week"].eq(weeks[4])
    w.loc[drop, ["log_price", "status"]] = [np.nan, "missing"]
    r = build_region_panel(cfg, w, elig).query("region == 'Papua'").set_index("week")
    assert r.loc[weeks[4], "n_provinces"] == 1
    assert np.allclose(r["log_price_index"].diff().dropna(), 0.01)  # rerata biasa akan melompat ±0.05


def test_region_panel_only_eligible_and_all_missing(cfg):
    w, elig, weeks = _weekly(cfg)
    maluku = cfg.regions.loc[cfg.regions["region"] == "Maluku", "province_id"]
    elig.loc[elig["province_id"] == maluku.iloc[0], "eligible"] = False
    w.loc[w["province_id"].eq(maluku.iloc[1]) & w["week"].eq(weeks[2]), "log_price"] = np.nan
    r = build_region_panel(cfg, w, elig).query("region == 'Maluku'").set_index("week")
    assert (r.drop(index=weeks[2])["n_provinces"] == 1).all()
    assert r.loc[weeks[2], "n_provinces"] == 0 and np.isnan(r.loc[weeks[2], "log_price_index"])


def test_region_panel_real_data(cfg):
    from kagami.utils.io import exists, read_artifact
    if not (exists(cfg, "panel_weekly") and exists(cfg, "eligibility")):
        pytest.skip("panel_weekly/eligibility belum ada")
    wk, elig = read_artifact(cfg, "panel_weekly"), read_artifact(cfg, "eligibility")
    r = build_region_panel(cfg, wk, elig)
    assert len(r) == 7 * 10 * wk["week"].nunique()
    assert "price" not in r.columns and "log_price" not in r.columns   # tidak ada level Rp
    assert r["log_price_index"].isna().mean() < 0.01
    assert (r.groupby(["region", "commodity"])["log_price_index"].first() == 0).all()
