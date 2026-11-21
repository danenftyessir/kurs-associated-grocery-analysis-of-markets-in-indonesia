"""Konsistensi configs/ dan data/reference/ dengan data mentah."""

import pytest

from kagami.data.loaders import load_pinksheet, norm_name


def test_commodity_design(cfg):
    c = cfg.commodities
    assert len(c) == 10
    roles = [v["role"] for v in c.values()]
    assert roles.count("focus") == 6 and roles.count("control") == 3 and roles.count("other") == 1
    groups = {v["focus_group"] for v in c.values() if v["role"] == "focus"}
    assert len(groups) == 5, "5 grup fokus konfirmatori (ayam & telur = 'pakan')"
    for v in c.values():
        assert v["exposure_path"] in {"direct_import", "imported_input", "export_parity", "domestic"}
        if v["pinksheet"]:
            assert abs(sum(v["pinksheet"].values()) - 1) < 1e-9


def test_regions(cfg):
    r = cfg.regions
    assert len(r) == 34 and r["province_id"].is_unique
    assert r["region"].nunique() == 7
    assert set(cfg.params["association"]["hubs"]) <= set(r["province"])
    assert set(r["het_zone_beras"]) == {1, 2, 3}


def test_sources_exist(cfg):
    for key, src in cfg.sources.items():
        files = cfg.source_files(key)
        if src.get("optional") and not all(f.exists() for f in files):
            continue                                    # sumber manual yang belum diisi (WP-07 NaN-aman)
        assert files and all(f.exists() for f in files), f"{key}: {src['path']} tidak ada di {cfg.raw_dir}"


def test_variants_exist_in_pihps(cfg, pihps):
    items = set(pihps["item"].map(norm_name))
    groups = set(pihps["commodity_group"])
    for k, v in cfg.commodities.items():
        assert v["pihps_name"] in groups, k
        assert norm_name(v["variant"]) in items, f"{k}: varian '{v['variant']}' tidak ada di PIHPS"


def test_pinksheet_series_exist(cfg):
    if not cfg.source_path("pinksheet").exists():
        pytest.skip("Pink Sheet tidak ada")
    series = set(load_pinksheet(cfg)["series"])
    for k, v in cfg.commodities.items():
        for s in v["pinksheet"]:
            assert s in series, f"{k}: seri Pink Sheet '{s}' tidak ditemukan"
