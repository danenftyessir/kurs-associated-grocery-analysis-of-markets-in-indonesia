"""Setiap loader berjalan pada snapshot mentah dan menghasilkan kolom yang didokumentasikan (docs/DATASETS.md)."""

import pytest

from kagami.data.loaders import LOADERS

EXPECTED = {
    "jisdor": {"date", "idr_per_usd"},
    "pihps": {"date", "province_id", "province", "level", "commodity_group", "item", "price"},
    "pinksheet": {"month", "series", "unit", "usd_price"},
    "brent": {"date", "value"},
    "dollar_index": {"date", "value"},
    "faostat_sua": {"year", "item", "element", "unit", "value"},
    "bps_import_monthly": {"month", "hs8_code", "import_value_usd", "import_netweight_kg"},
    "bps_import_annual": {"hs8_code", "year", "total"},
    "comtrade_import": {"month", "hs_code", "net_weight_kg", "cif_usd"},
    "comtrade_import_2023": {"month", "hs_code", "net_weight_kg", "cif_usd", "primary_value_usd"},
    "bapanas_panel": {"month", "commodity_bapanas", "province_id", "price_geomean"},
    "bapanas_het_settings": {"commodity_bapanas", "zone", "price", "start_date", "end_date"},
    "padi_2024": {"year", "province_id", "production_ton_gkg"},
    "padi_2025": {"year", "province_id", "production_ton_gkg"},
    "konsumsi_beras": {"province_id", "year", "kg_per_capita_year"},
    "neraca_beras": {"tahun", "produksi_beras_ton", "impor_ton"},
    "het_hap_current": {"commodity", "instrument", "zone_or_scope", "value_min_rp"},
    "regulation_history": {"instrument", "commodity", "regulation", "signed_or_effective_date"},
    "jarak_hub": {"province_id", "dist_hub_km", "ln1p_dist_hub", "nearest_hub"},
    "konkordansi_hs": {"comtrade_code", "bps_hs8_prefix", "keyakinan_pemetaan"},
    "hortikultura_produksi": {"commodity_atap", "province_id", "year", "production_ton"},
    "penduduk": {"province_id", "year", "population"},
    "n_kota": {"province_id", "n_kota"},
    "gkg_beras": {"year", "factor"},
}


def test_every_source_has_loader(cfg):
    assert set(LOADERS) == set(cfg.sources) == set(EXPECTED)


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_loader(cfg, key):
    if not cfg.source_path(key).exists():
        pytest.skip(f"{key} mentah tidak ada")
    df = LOADERS[key](cfg)
    assert len(df) > 0
    assert EXPECTED[key] <= set(df.columns), EXPECTED[key] - set(df.columns)


def test_bps_monthly_v2_has_garlic(cfg):
    """v2 (2026-11-20) memuat bawang putih HS 070320; v1 tidak lengkap (di _superseded/)."""
    df = LOADERS["bps_import_monthly"](cfg)
    assert df["hs8_code"].str.startswith("070320").sum() >= 50 and df["hs8_code"].nunique() == 111


def test_pihps_shape(pihps):
    assert pihps["province_id"].nunique() == 34
    assert pihps["commodity_group"].nunique() == 10
    assert (pihps["level"] == 2).groupby(pihps["province_id"]).sum().min() > 0


def test_pihps_variant_groups_by_prefix(pihps):
    """Regresi D-022: varian yang ditaruh di akhir file v2 tetap masuk grup yang benar."""
    pairs = pihps[["province_id", "commodity_group", "item"]].drop_duplicates()
    assert pairs.apply(lambda r: r["item"].startswith(r["commodity_group"]), axis=1).all()
    assert not pairs.duplicated(["province_id", "item"]).any()
    aceh = pairs[pairs["province_id"] == 1].set_index("item")["commodity_group"]
    assert aceh["Cabai Rawit Merah"] == "Cabai Rawit"     # baris terakhir file Aceh


@pytest.mark.parametrize("key,col", [("padi_2024", "province_raw"), ("padi_2025", "province_raw"),
                                     ("konsumsi_beras", "province_raw"), ("bapanas_panel", "province"),
                                     ("jarak_hub", "province_raw"), ("hortikultura_produksi", "province_raw")])
def test_province_names_all_mapped(cfg, key, col):
    """Semua nama provinsi (termasuk pemekaran Papua) terpetakan ke 34 provinsi lama."""
    df = LOADERS[key](cfg)
    assert df["province_id"].nunique() == 34, key
    if key in ("bapanas_panel", "jarak_hub"):   # loader ini tidak membuang baris; tidak boleh ada yang gagal dipetakan
        assert df["province_id"].notna().all(), df.loc[df["province_id"].isna(), col].unique()


# --- sumber manual WP-07 (NaN-aman) -------------------------------------------------
@pytest.mark.parametrize("key", ["penduduk", "n_kota", "gkg_beras"])
def test_manual_loader_missing_file_gives_empty_schema(cfg, tmp_path, key):
    from dataclasses import replace
    df = LOADERS[key](replace(cfg, raw_root=tmp_path))
    assert len(df) == 0 and EXPECTED[key] <= set(df.columns)


def test_penduduk_unit_and_guard(cfg, tmp_path):
    from dataclasses import replace
    c = replace(cfg, raw_root=tmp_path)
    (tmp_path / "bps_kependudukan").mkdir()
    f = tmp_path / "bps_kependudukan" / "penduduk_provinsi_2025.csv"
    names = list(cfg.regions["province"])
    f.write_text("Provinsi,Jumlah Penduduk 2025 (ribu jiwa)\n" + "\n".join(f"{n},{8000}" for n in names), encoding="utf-8")
    out = LOADERS["penduduk"](c)
    assert out["population"].iloc[0] == 8_000_000 and out["province_id"].nunique() == 34   # ribu -> jiwa
    f.write_text("Provinsi,Jumlah Penduduk 2025\n" + "\n".join(f"{n},{8000}" for n in names), encoding="utf-8")
    with pytest.raises(ValueError, match="rentang wajar"):                # 8.000 jiwa x 34: satuan salah
        LOADERS["penduduk"](c)
