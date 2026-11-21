"""WP-07: tabel buatan tim (concordance, exposure, regulation, province_features) dengan data sintetis berjawaban pasti."""

import numpy as np
import pandas as pd
import pytest

from kagami.data import reference as R


# --------------------------------------------------------------------------- concordance
def test_concordance_contract_and_confidence(cfg):
    c = R.build_concordance(cfg).set_index("commodity")
    assert len(c) == 10 and set(c.index) == set(cfg.commodities)
    assert c.loc["bawang_putih", "confidence"] == "low"                 # tanpa Pink Sheet & FAOSTAT
    assert c.loc["daging_ayam", "confidence"] == "medium"               # komposit pakan
    assert c.loc["cabai_merah", "confidence"] == "medium"               # item FAOSTAT dipakai dua komoditas
    assert c.loc["beras", "confidence"] == "high" and c.loc["beras", "pinksheet"] == "Rice, Thai 5%:1"
    assert c.loc["daging_ayam", "pinksheet"] == "Maize:0.6;Soybean meal:0.4"


def test_concordance_missing_series_raises(cfg):
    ps = pd.DataFrame({"series": ["Palm oil"]})
    with pytest.raises(ValueError, match="Pink Sheet"):
        R.build_concordance(cfg, pinksheet=ps)


# --------------------------------------------------------------------------- exposure
def _fao(cfg, item, prod, imp, exp, years=range(2018, 2024)):
    rows = []
    for y in years:
        for el, v in (("Production", prod), ("Import quantity", imp), ("Export quantity", exp)):
            rows.append({"year": y, "item": item, "element": el, "unit": "t", "value": v})
    return pd.DataFrame(rows)


def test_exposure_fao_ratio_and_ordinals(cfg):
    fao = _fao(cfg, "Rice", prod=90.0, imp=20.0, exp=10.0)              # 20 / (90 + 20 - 10) = 0,2
    neraca = pd.DataFrame({"produksi_beras_ton": [80.0], "impor_ton": [20.0], "ekspor_ton": [0.0]})
    e = R.build_exposure(cfg, fao, pd.DataFrame(), pd.DataFrame(), neraca).set_index("commodity")
    assert np.isclose(e.loc["beras", "import_ratio_direct"], 0.2)
    assert np.isclose(e.loc["beras", "import_ratio_neraca"], 0.2)
    assert e.loc["daging_ayam", "imported_input_ordinal"] == 2 and e.loc["beras", "imported_input_ordinal"] == 0
    assert bool(e.loc["beras", "world_price_link"]) and not bool(e.loc["bawang_putih", "world_price_link"])
    assert np.isnan(e.loc["gula_pasir", "import_ratio_direct"])           # item tidak ada di data sintetis
    assert e["source"].str.len().gt(0).all()                              # setiap angka punya source


def test_exposure_fao_window_excludes_outside_years(cfg):
    fao = pd.concat([_fao(cfg, "Rice", 90.0, 20.0, 10.0, years=range(2018, 2024)),
                     _fao(cfg, "Rice", 10.0, 90.0, 0.0, years=[2017, 2024])])    # di luar jendela 2018-2023
    e = R.build_exposure(cfg, fao, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()).set_index("commodity")
    assert np.isclose(e.loc["beras", "import_ratio_direct"], 0.2)


def test_exposure_garlic_from_trade_and_production(cfg):
    # Comtrade 2021-2022: 1000 t/th; BPS 2023: 3000 t/th; produksi 1000 t/th -> rasio 0,5; 0,5; 0,75
    months = lambda y: pd.date_range(f"{y}-01-01", periods=12, freq="MS")           # noqa: E731
    ct = pd.concat([pd.DataFrame({"month": months(y), "hs_code": "070320", "net_weight_kg": 1e6 / 12})
                    for y in (2021, 2022)])
    bp = pd.DataFrame({"month": months(2023), "hs8_code": "07032000", "import_netweight_kg": 3e6 / 12})
    horti = pd.DataFrame({"commodity_atap": "bawang_putih", "year": [2021, 2022, 2023],
                          "production_ton": [1000.0] * 3})
    e = R.build_exposure(cfg, pd.DataFrame(columns=["year", "item", "element", "unit", "value"]), bp, ct,
                         pd.DataFrame(), hortikultura=horti).set_index("commodity")
    assert np.isclose(e.loc["bawang_putih", "import_ratio_direct"], (0.5 + 0.5 + 0.75) / 3)
    assert "U5" in e.loc["bawang_putih", "source"]


def test_exposure_garlic_without_production_is_nan(cfg):
    e = R.build_exposure(cfg, pd.DataFrame(columns=["year", "item", "element", "unit", "value"]),
                         pd.DataFrame(), pd.DataFrame(), pd.DataFrame()).set_index("commodity")
    assert np.isnan(e.loc["bawang_putih", "import_ratio_direct"]) and "U5" in e.loc["bawang_putih", "source"]


# --------------------------------------------------------------------------- regulation
@pytest.mark.parametrize("text, start, end, status", [
    ("2020-03-16 (ditetapkan); 2020-03-19 (diundangkan/berlaku)", "2020-03-19", None, "effective"),
    ("2025-01-12 (ditetapkan); berlaku 2025-01-15", "2025-01-15", None, "effective"),
    ("2024-04-03 s.d. 2024-06-30", "2024-04-03", "2024-06-30", "range"),
    ("2024-06-02 sampai terbit Perbadan", "2024-06-02", None, "effective"),
    ("2024-09-25 (ditetapkan)", "2024-09-25", None, "signed_only"),
    ("2024-06-03 (ditetapkan); tanggal diundangkan kosong di salinan; berlaku pada tanggal diundangkan",
     "2024-06-03", None, "signed_only"),
    ("2025-08-22", "2025-08-22", None, "unlabeled"),
    ("tidak terverifikasi s.d. 2024-03-23 lalu diperpanjang s.d. 2024-05-31", None, "2024-05-31", "unknown"),
    ("belum ada", None, None, "unknown"),
])
def test_parse_regulation_dates(text, start, end, status):
    s, e, st = R.parse_regulation_dates(text)
    assert (s == pd.Timestamp(start)) if start else pd.isna(s)
    assert (e == pd.Timestamp(end)) if end else pd.isna(e)
    assert st == status


@pytest.mark.parametrize("text, expected", [
    ("TERVERIFIKASI dari Lampiran PDF resmi", "verified"),
    ("TERVERIFIKASI dari Lampiran PDF resmi (nilai); tanggal berlaku belum diketahui", "partial"),
    ("Nomor dan tanggal terkonfirmasi (Kontan); nilai sama dengan Lampiran yang TERVERIFIKASI", "partial"),
    ("Terkonfirmasi >=3 sumber berita", "confirmed"),
    ("Tanggal dari JDIH Kemendag", "confirmed"),
    ("belum dicek", "unverified"),
])
def test_classify_verification(text, expected):
    assert R.classify_verification(text) == expected


def _team(**kw):
    base = dict(commodity="Beras medium", instrument="HET", zone_or_scope="Zona 1 (Jawa; Sumsel)", value_min_rp=13500,
                value_max_rp=13500, regulation="Kepbadan 299/2025",
                signed_or_effective_date="2025-08-22 (berlaku segera)",
                verification="TERVERIFIKASI dari Lampiran PDF resmi")
    base.update(kw)
    return base


def test_regulation_merge_rules(cfg):
    cur = pd.DataFrame([_team(), _team(commodity="Cabai rawit merah", instrument="HAP konsumen",
                                       zone_or_scope="Nasional (rentang)", value_min_rp=40000, value_max_rp=57000)])
    hist = pd.DataFrame([_team(commodity="Telur; daging ayam; jagung", instrument="HAP", zone_or_scope="Nasional",
                               value_min_rp=np.nan, value_max_rp=np.nan, regulation="Perbadan 6/2024",
                               signed_or_effective_date="2024-06-13 (ditetapkan)"),
                         _team(commodity="Beras premium", value_min_rp=14900, value_max_rp=14900,
                               signed_or_effective_date="tidak terverifikasi s.d. 2024-05-31",
                               verification="Terkonfirmasi (Katadata)")])
    bap = pd.DataFrame([
        dict(commodity_bapanas="Beras Medium", type="HET", zone="Zona 1", price=13500.0,
             start_date=pd.Timestamp("2024-06-02"), end_date=pd.Timestamp("2024-12-30")),   # nilai sama: tercakup
        dict(commodity_bapanas="Minyakita", type="HET", zone="Nasional", price=15700.0,
             start_date=pd.Timestamp("2025-01-01"), end_date=pd.Timestamp("2025-12-31")),   # baru: masuk, unverified
        dict(commodity_bapanas="Gula Konsumsi", type="HAP", zone="Nasional", price=18500.0,
             start_date=pd.NaT, end_date=pd.NaT)])                                          # tanpa tanggal: dibuang
    r = R.build_regulation(cfg, cur, hist, bap)

    ras = r[(r["commodity"] == "beras") & (r["instrument"] == "HET") & (r["zone"] == "Zona 1")]
    assert (ras["value_rp"] == 13500).sum() == 1 and "bapanas_het_settings" not in set(ras["source"])
    prem = r[r["commodity_raw"] == "Beras premium"].iloc[0]
    assert pd.isna(prem["start_date"]) and prem["verification"] == "unverified"       # tanggal tak terverifikasi
    cabai = r[r["commodity"] == "cabai_rawit"].iloc[0]
    assert cabai["instrument"] == "HAP_konsumen" and pd.isna(cabai["value_rp"]) and cabai["value_max_rp"] == 57000
    assert set(r.loc[r["source"] == "regulation_history", "commodity"]) >= {"telur_ayam", "daging_ayam", "jagung"}
    assert not r.loc[r["commodity"] == "jagung", "in_scope"].any()
    mg = r[r["commodity"] == "minyak_goreng"].iloc[0]
    assert mg["source"] == "bapanas_het_settings" and mg["verification"] == "unverified"
    assert "gula_pasir" not in set(r["commodity"])
    contract = {"commodity", "instrument", "zone", "value_rp", "start_date", "end_date", "regulation", "verification"}
    assert contract <= set(r.columns)


def test_regulation_empty_inputs(cfg):
    r = R.build_regulation(cfg, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    assert len(r) == 0 and "verification" in r.columns


# --------------------------------------------------------------------------- province_features
def test_dist_hub_from_crosswalk(cfg):
    f = R.build_province_features(cfg, pd.DataFrame(), pd.DataFrame()).set_index("province_id")
    reg = cfg.regions.set_index("province")
    assert len(f) == 34
    for hub in cfg.params["association"]["hubs"]:
        assert f.loc[reg.loc[hub, "province_id"], "dist_hub_km"] == 0
    assert np.allclose(f["ln_dist_hub"], np.log1p(f["dist_hub_km"]))
    assert f["dist_hub_km"].min() == 0 and f["dist_hub_km"].max() > 1000
    assert f[["rice_sufficiency", "n_kota"]].isna().all().all()     # input manual belum ada -> NaN, tidak error


def test_rice_sufficiency_with_pemekaran(cfg):
    ids = list(cfg.regions["province_id"])
    names = dict(zip(cfg.regions["province_id"], cfg.regions["province"]))
    padi = pd.DataFrame({"year": 2025, "province_id": ids, "production_ton_gkg": 1000.0})
    # induk 33 (Papua) punya dua baris: pemekaran dijumlahkan ke induk (produksi 2 x 1000 GKG)
    padi = pd.concat([padi, pd.DataFrame({"year": [2025], "province_id": [33], "production_ton_gkg": [1000.0]})])
    kons = pd.DataFrame({"province_raw": [names[i] for i in ids] + ["Papua Selatan"], "province_id": ids + [33],
                         "year": 2025, "kg_per_capita_year": 100.0})
    pend = pd.DataFrame({"province_raw": [names[i] for i in ids] + ["Papua Selatan"], "province_id": ids + [33],
                         "year": 2025, "population": 20000.0})
    gkg = pd.DataFrame({"year": [2025], "factor": [0.5]})
    f = R.build_province_features(cfg, padi, kons, pend, gkg).set_index("province_id")
    assert np.isclose(f.loc[1, "rice_production_ton"], 500.0)               # 1000 GKG x 0,5
    assert np.isclose(f.loc[1, "rice_need_ton"], 2000.0)                    # 100 kg x 20.000 jiwa / 1000
    assert np.isclose(f.loc[1, "rice_sufficiency"], 0.25)
    assert np.isclose(f.loc[33, "rice_production_ton"], 1000.0) and np.isclose(f.loc[33, "rice_need_ton"], 4000.0)


def test_rice_sufficiency_nan_without_factor(cfg):
    ids = list(cfg.regions["province_id"])
    padi = pd.DataFrame({"year": 2025, "province_id": ids, "production_ton_gkg": 1.0})
    pend = pd.DataFrame({"year": [2025], "population": [1.0]})
    f = R.build_province_features(cfg, padi, pd.DataFrame({"year": []}), pend,
                                  pd.DataFrame(columns=["year", "factor"]))
    assert f["rice_sufficiency"].isna().all()


def test_n_kota_merge(cfg):
    nk = pd.DataFrame({"province_id": [1, 2], "n_kota": [3.0, 5.0]})
    f = R.build_province_features(cfg, pd.DataFrame(), pd.DataFrame(), n_kota=nk).set_index("province_id")
    assert f.loc[1, "n_kota"] == 3 and f.loc[2, "n_kota"] == 5 and f["n_kota"].isna().sum() == 32
