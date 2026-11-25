"""Loader mentah -> DataFrame rapi. Satu fungsi per kunci di configs/sources.yaml.

Loader TIDAK membuang data dan TIDAK mengubah satuan; hanya parsing format.
Semua pembersihan/agregasi ada di weekly.py, drivers.py, reference.py.
Kolom keluaran setiap loader didokumentasikan di docs/DATASETS.md.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from kagami.utils.config import Config


# ---------------------------------------------------------------------------
# util
# ---------------------------------------------------------------------------
def norm_name(s: str) -> str:
    """Normalisasi nama: trim, spasi tunggal (tanpa ubah huruf)."""
    return re.sub(r"\s+", " ", str(s)).strip()


def _id_number(s: pd.Series) -> pd.Series:
    """'9.760,00' / '14.900' (format Indonesia) -> float."""
    s = s.astype(str).str.strip().replace({"": np.nan, "nan": np.nan, "-": np.nan})
    return pd.to_numeric(s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")


def province_lookup(cfg: Config) -> dict[str, int]:
    """Peta NAMA PROVINSI (upper) -> province_id 34 provinsi lama, termasuk alias/pemekaran."""
    m = {norm_name(n).upper(): int(i) for n, i in zip(cfg.regions.province, cfg.regions.province_id)}
    for a, i in zip(cfg.province_aliases.alias, cfg.province_aliases.province_id):
        m[norm_name(a).upper()] = int(i)
    return m


def map_province(cfg: Config, names: pd.Series) -> pd.Series:
    """Nama provinsi -> province_id (NaN bila tidak dikenal, mis. 'INDONESIA')."""
    lut = province_lookup(cfg)
    return names.map(lambda x: lut.get(norm_name(x).upper(), np.nan)).astype("Int64")


# ---------------------------------------------------------------------------
# Bank Indonesia
# ---------------------------------------------------------------------------
def load_jisdor(cfg: Config) -> pd.DataFrame:
    """-> date, idr_per_usd (hari kerja)."""
    raw = pd.read_excel(cfg.source_path("jisdor"), header=None, skiprows=5, usecols=[1, 2])
    raw.columns = ["date", "rate"]
    out = pd.DataFrame({
        "date": pd.to_datetime(raw["date"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"),
        "idr_per_usd": _id_number(raw["rate"]),
    }).dropna()
    return out.sort_values("date").drop_duplicates("date").reset_index(drop=True)


def load_pihps(cfg: Config, key: str = "pihps") -> pd.DataFrame:
    """-> date, province_id, province, level, commodity_group, item, price (Rp; NaN = tidak teramati).

    File per provinsi berformat lebar (kolom = tanggal). Baris level 1 = komoditas, level 2 = varian.
    Grup varian ditentukan dari PREFIKS nama (mis. 'Cabai Rawit Merah' -> 'Cabai Rawit'), BUKAN dari urutan
    baris: file v2 'merged' menaruh varian hasil penggabungan di akhir file (D-022). Kolom 'no' (format snapshot lama) dibuang bila ada.
    """
    frames = []
    with zipfile.ZipFile(cfg.source_path(key)) as zf:
        for name in sorted(n for n in zf.namelist() if n.startswith("pihps_prov") and n.endswith(".csv")):
            df = pd.read_csv(zf.open(name))
            df = df.drop(columns=[c for c in ("no",) if c in df.columns])
            df["commodity"] = df["commodity"].map(norm_name)
            df["commodity_group"] = _variant_group(df["commodity"], df["level"], name)
            id_cols = ["province_id", "province", "level", "commodity_group", "commodity"]
            long = df.melt(id_vars=id_cols, var_name="date", value_name="price")
            frames.append(long)
    out = pd.concat(frames, ignore_index=True).rename(columns={"commodity": "item"})
    out["date"] = pd.to_datetime(out["date"])
    out["price"] = pd.to_numeric(out["price"], errors="coerce").astype("float64")
    return out[["date", "province_id", "province", "level", "commodity_group", "item", "price"]]


def _variant_group(items: pd.Series, level: pd.Series, file: str) -> pd.Series:
    """Grup = nama level-1 terpanjang yang menjadi prefiks nama item (level 1 = dirinya sendiri)."""
    groups = sorted(set(items[level == 1]), key=len, reverse=True)

    def match(item: str) -> str:
        for g in groups:
            if item == g or item.startswith(g + " "):
                return g
        raise ValueError(f"{file}: varian '{item}' tidak cocok dengan komoditas level-1 mana pun")

    return items.map(match)


def load_pihps_manifest(cfg: Config, key: str = "pihps") -> pd.DataFrame | None:
    """MANIFEST.csv dalam zip v2 (sha256 per file, endpoint, retrieved_at). None bila tidak ada."""
    with zipfile.ZipFile(cfg.source_path(key)) as zf:
        if "MANIFEST.csv" not in zf.namelist():
            return None
        return pd.read_csv(zf.open("MANIFEST.csv"))


# ---------------------------------------------------------------------------
# Harga dunia & kontrol global
# ---------------------------------------------------------------------------
def load_pinksheet(cfg: Config) -> pd.DataFrame:
    """-> month (Timestamp awal bulan), series (nama ternormalisasi), unit, usd_price.

    Nama seri dinormalisasi: trim + buang penanda '**' (mis. 'Beef **' -> 'Beef').
    """
    raw = pd.read_excel(cfg.source_path("pinksheet"), sheet_name="Monthly Prices", header=None)
    names = raw.iloc[4, 1:].map(lambda x: norm_name(str(x).replace("*", "")))
    units = raw.iloc[5, 1:].astype(str).str.strip()
    body = raw.iloc[6:].copy()
    body = body[body[0].astype(str).str.match(r"^\d{4}M\d{2}$")]
    month = pd.to_datetime(body[0].str.replace("M", "-", regex=False) + "-01")
    vals = body.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    vals.columns = names.values
    vals.index = month.values
    long = vals.stack(future_stack=True).rename("usd_price").reset_index()
    long.columns = ["month", "series", "usd_price"]
    long["unit"] = long["series"].map(dict(zip(names.values, units.values)))
    return long.dropna(subset=["usd_price"]).reset_index(drop=True)


def load_fred(cfg: Config, key: str) -> pd.DataFrame:
    """key in {'brent','dollar_index'} -> date, value (hari libur = NaN dibuang)."""
    df = pd.read_csv(cfg.source_path(key))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().reset_index(drop=True)


def load_faostat_sua(cfg: Config, area: str = "Indonesia") -> pd.DataFrame:
    """-> year, item, element, unit, value (hanya area terpilih)."""
    with zipfile.ZipFile(cfg.source_path("faostat_sua")) as zf:
        df = pd.read_csv(zf.open("SUA_Crops_Livestock_E_Asia_NOFLAG.csv"), encoding="latin1")
    df = df[df["Area"] == area]
    ycols = [c for c in df.columns if re.fullmatch(r"Y\d{4}", c)]
    long = df.melt(id_vars=["Item", "Element", "Unit"], value_vars=ycols, var_name="year", value_name="value")
    long["year"] = long["year"].str[1:].astype(int)
    long = long.rename(columns={"Item": "item", "Element": "element", "Unit": "unit"})
    return long.dropna(subset=["value"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Perdagangan
# ---------------------------------------------------------------------------
def load_bps_import_monthly(cfg: Config) -> pd.DataFrame:
    """-> month, hs8_code (str), hs_description, import_value_usd, import_netweight_kg."""
    df = pd.read_csv(cfg.source_path("bps_import_monthly"), dtype={"hs8_code": str})
    df["month"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return df[["month", "hs8_code", "hs_description", "import_value_usd", "import_netweight_kg"]]


def load_bps_import_annual(cfg: Config) -> pd.DataFrame:
    """-> hs8_code, hs_description, year, total, file. Satuan 'Totals' dari portal BPS (diverifikasi di WP-10)."""
    frames = []
    for f in cfg.source_files("bps_import_annual"):
        df = pd.read_excel(f, header=None, skiprows=2, usecols=[0, 1, 2])
        df.columns = ["hs", "year", "total"]
        df["hs"] = df["hs"].ffill()
        ext = df["hs"].astype(str).str.extract(r"\[(\d+)\]\s*(.*)")
        df["hs8_code"], df["hs_description"] = ext[0], ext[1]
        df["file"] = f.name
        frames.append(df.dropna(subset=["year"]))
    out = pd.concat(frames, ignore_index=True)
    out["year"] = out["year"].astype(int)
    return out[["hs8_code", "hs_description", "year", "total", "file"]].drop_duplicates(["hs8_code", "year"])


def load_comtrade(cfg: Config, key: str = "comtrade_import") -> pd.DataFrame:
    """-> month, hs_code (str, HS4/HS6), hs_description, net_weight_kg, cif_usd, primary_value_usd.

    key = "comtrade_import" (2017-2022) atau "comtrade_import_2023" (QA tumpang tindih U102; skema sama).
    """
    df = pd.read_csv(cfg.source_path(key), dtype={"cmdCode": str, "period": str})
    out = pd.DataFrame({
        "month": pd.to_datetime(df["period"], format="%Y%m"),
        "hs_code": df["cmdCode"],
        "hs_description": df["cmdDesc"],
        "net_weight_kg": df["netWgt"],
        "cif_usd": df["cifvalue"],
        "primary_value_usd": df["primaryValue"],
    })
    return out


# ---------------------------------------------------------------------------
# Bapanas
# ---------------------------------------------------------------------------
def load_bapanas_panel(cfg: Config) -> pd.DataFrame:
    """-> month, commodity_bapanas, province_id (34 lama), province, price_geomean, status_map, ref_price."""
    df = pd.read_csv(cfg.source_path("bapanas_panel"))
    return pd.DataFrame({
        "month": pd.to_datetime(df["periode_mulai"]),
        "commodity_bapanas": df["komoditas"],
        "province_id": map_province(cfg, df["provinsi"]),
        "province": df["provinsi"],
        "price_geomean": pd.to_numeric(df["harga_rata_rata_geometrik_rp"], errors="coerce"),
        "status_map": df["status_map"],
        "ref_price": _id_number(df["hpp_hap_acuan"]),
    })


def load_bapanas_het_settings(cfg: Config) -> pd.DataFrame:
    """-> commodity_bapanas, type, zone, price, start_date, end_date."""
    df = pd.read_csv(cfg.source_path("bapanas_het_settings"))
    return pd.DataFrame({
        "commodity_bapanas": df["komoditas_nama"],
        "type": df["type_description"],
        "zone": df["nama_zona"],
        "price": pd.to_numeric(df["harga_provinsi"], errors="coerce"),
        "start_date": pd.to_datetime(df["start_date"], errors="coerce"),
        "end_date": pd.to_datetime(df["end_date"], errors="coerce"),
    })


# ---------------------------------------------------------------------------
# BPS pangan (karakteristik provinsi)
# ---------------------------------------------------------------------------
def load_padi(cfg: Config, year: int) -> pd.DataFrame:
    """-> year, province_raw, province_id (pemekaran dipetakan ke induk), harvest_ha, productivity_ku_ha, production_ton_gkg.

    Baris 'INDONESIA' dan catatan kaki dibuang. Agregasi pemekaran -> induk dilakukan di reference.py.
    """
    path = cfg.source_path(f"padi_{year}")
    # Kedua file berurutan: provinsi, luas panen, produktivitas, produksi. 2024 punya 4 baris judul.
    df = pd.read_csv(path, encoding="utf-8-sig", header=None, skiprows=4 if year == 2024 else 1)
    df.columns = ["province_raw", "harvest_ha", "productivity_ku_ha", "production_ton_gkg"]
    df["province_id"] = map_province(cfg, df["province_raw"])
    df = df.dropna(subset=["province_id"])
    for c in ("harvest_ha", "productivity_ku_ha", "production_ton_gkg"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.insert(0, "year", year)
    return df.reset_index(drop=True)


def load_konsumsi_beras(cfg: Config) -> pd.DataFrame:
    """-> province_raw, province_id, year, kg_per_capita_year."""
    df = pd.read_csv(cfg.source_path("konsumsi_beras"))
    cols = {c: int(re.search(r"(\d{4})", c).group(1)) for c in df.columns if c.startswith("konsumsi_beras_rt_")}
    long = df.melt(id_vars=["provinsi"], value_vars=list(cols), var_name="col", value_name="kg_per_capita_year")
    long["year"] = long["col"].map(cols)
    long["province_id"] = map_province(cfg, long["provinsi"])
    long = long.rename(columns={"provinsi": "province_raw"}).dropna(subset=["province_id"])
    return long[["province_raw", "province_id", "year", "kg_per_capita_year"]].reset_index(drop=True)


def load_neraca_beras(cfg: Config) -> pd.DataFrame:
    """Neraca beras nasional tahunan (ton), kolom asli."""
    return pd.read_csv(cfg.source_path("neraca_beras"))


# ---------------------------------------------------------------------------
# Regulasi (tabel buatan tim)
# ---------------------------------------------------------------------------
def load_het_hap_current(cfg: Config) -> pd.DataFrame:
    return pd.read_csv(cfg.source_path("het_hap_current"))


def load_regulation_history(cfg: Config) -> pd.DataFrame:
    return pd.read_csv(cfg.source_path("regulation_history"))


# ---------------------------------------------------------------------------
# Tabel tim & statistik tambahan (masuk 2026-11-20)
# ---------------------------------------------------------------------------
def load_jarak_hub(cfg: Config) -> pd.DataFrame:
    """-> province_raw, province_id, capital, lat, lon, km_jakarta, km_surabaya, km_makassar, nearest_hub,
    dist_hub_km, ln1p_dist_hub (38 provinsi; pemekaran Papua dipetakan ke induk, jadi province_id bisa berulang)."""
    df = pd.read_csv(cfg.source_path("jarak_hub"))
    out = pd.DataFrame({
        "province_raw": df["provinsi"], "province_id": map_province(cfg, df["provinsi"]), "capital": df["ibu_kota"],
        "lat": df["lat_perkiraan"], "lon": df["lon_perkiraan"], "km_jakarta": df["km_ke_jakarta"],
        "km_surabaya": df["km_ke_surabaya"], "km_makassar": df["km_ke_makassar"], "nearest_hub": df["hub_terdekat"],
        "dist_hub_km": df["jarak_hub_terdekat_km_garis_lurus"], "ln1p_dist_hub": df["ln1p_jarak_km"],
    })
    return out


def load_konkordansi_hs(cfg: Config) -> pd.DataFrame:
    """Konkordansi Comtrade (HS4/HS6) -> HS8 BPS; kode dibaca sebagai string (jaga nol depan), kolom asli."""
    return pd.read_csv(cfg.source_path("konkordansi_hs"), dtype={"comtrade_code": str, "bps_hs8_prefix": str})


def load_hortikultura(cfg: Config) -> pd.DataFrame:
    """-> commodity_atap, province_raw, province_id, year, production_ton, note.

    commodity_atap ∈ {bawang_merah, bawang_putih, cabai_besar_group, cabai_rawit}; baris nasional dibuang
    (province_id NaN). '-' di sumber = tanpa data (production_ton NaN, note diisi)."""
    df = pd.read_csv(cfg.source_path("hortikultura_produksi"))
    out = pd.DataFrame({
        "commodity_atap": df["komoditas"], "province_raw": df["provinsi"], "province_id": map_province(cfg, df["provinsi"]),
        "year": df["tahun"].astype(int), "production_ton": pd.to_numeric(df["produksi_ton"], errors="coerce"),
        "note": df["catatan"],
    })
    return out.dropna(subset=["province_id"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sumber manual untuk WP-07 (diisi Abi / diunggah Danen). File boleh belum ada:
# loader mengembalikan tabel kosong berkolom lengkap dan WP-07 menandai hasilnya NaN (U14, U15, U21).
# ---------------------------------------------------------------------------
PENDUDUK_COLUMNS = ["province_raw", "province_id", "year", "population"]
N_KOTA_COLUMNS = ["province_id", "province", "n_kota", "kota_list", "source_url"]
GKG_BERAS_COLUMNS = ["year", "factor", "source_url", "note"]
PENDUDUK_TOTAL_RANGE = (2.0e8, 4.0e8)    # penjaga satuan: total penduduk Indonesia ~280 juta jiwa


def _missing_source(cfg: Config, key: str, columns: list[str]) -> pd.DataFrame | None:
    """Tabel kosong berskema bila file sumber manual belum ada; None bila file ada."""
    if cfg.source_path(key).exists():
        return None
    print(f"[loaders] {key}: {cfg.sources[key]['path']} belum ada -> tabel kosong (hasil turunan NaN)")
    return pd.DataFrame(columns=columns)


def load_penduduk(cfg: Config, year: int = 2025) -> pd.DataFrame:
    """-> province_raw, province_id, year, population (jiwa). Pemekaran dipetakan ke induk (province_id bisa berulang).

    Skema CSV BPS belum dipastikan (U103): kolom provinsi = nama berisi 'provinsi'; kolom jumlah = satu-satunya kolom
    numerik, atau yang namanya memuat `year`. Satuan dibaca dari nama kolom ('ribu' x1.000, 'juta' x1.000.000) lalu
    dijaga: total harus 200-400 juta jiwa, selain itu ValueError (lebih baik berhenti daripada rasio salah 1.000x).
    """
    empty = _missing_source(cfg, "penduduk", PENDUDUK_COLUMNS)
    if empty is not None:
        return empty
    df = pd.read_csv(cfg.source_path("penduduk"), encoding="utf-8-sig")
    prov = [c for c in df.columns if "provinsi" in c.lower() or "province" in c.lower()]
    if not prov:
        raise ValueError(f"penduduk: kolom provinsi tidak ditemukan di {list(df.columns)}")
    num = [c for c in df.columns if c != prov[0] and pd.to_numeric(df[c], errors="coerce").notna().mean() > 0.8]
    pick = [c for c in num if str(year) in c] or num
    if len(pick) != 1:
        raise ValueError(f"penduduk: kolom jumlah penduduk {year} ambigu: {pick or list(df.columns)}")
    unit = pick[0].lower()
    scale = 1e6 if "juta" in unit else 1e3 if "ribu" in unit else 1.0
    out = pd.DataFrame({"province_raw": df[prov[0]], "province_id": map_province(cfg, df[prov[0]]),
                        "year": year, "population": pd.to_numeric(df[pick[0]], errors="coerce") * scale})
    out = out.dropna(subset=["province_id", "population"]).reset_index(drop=True)
    total = out["population"].sum()
    if not PENDUDUK_TOTAL_RANGE[0] <= total <= PENDUDUK_TOTAL_RANGE[1]:
        raise ValueError(f"penduduk: total {total:,.0f} jiwa di luar rentang wajar; "
                         f"periksa satuan kolom '{pick[0]}'")
    return out


def load_n_kota(cfg: Config) -> pd.DataFrame:
    """-> province_id, province, n_kota, kota_list, source_url (isi manual Abi, 34 provinsi; U15)."""
    empty = _missing_source(cfg, "n_kota", N_KOTA_COLUMNS)
    if empty is not None:
        return empty
    df = pd.read_csv(cfg.source_path("n_kota"), encoding="utf-8-sig")
    df["province_id"] = map_province(cfg, df["province"]) if "province_id" not in df else df["province_id"]
    df["n_kota"] = pd.to_numeric(df["n_kota"], errors="coerce")
    return df[N_KOTA_COLUMNS].reset_index(drop=True)


def load_gkg_beras(cfg: Config) -> pd.DataFrame:
    """-> year, factor, source_url, note: faktor konversi GKG -> beras per tahun (isi manual Abi; U21)."""
    empty = _missing_source(cfg, "gkg_beras", GKG_BERAS_COLUMNS)
    if empty is not None:
        return empty
    df = pd.read_csv(cfg.source_path("gkg_beras"), encoding="utf-8-sig")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["factor"] = pd.to_numeric(df["factor"], errors="coerce")
    return df[GKG_BERAS_COLUMNS].dropna(subset=["year", "factor"]).reset_index(drop=True)


# Registry: kunci sources.yaml -> loader. Dipakai oleh tests & `kagami status`.
LOADERS = {
    "jisdor": load_jisdor,
    "pihps": load_pihps,
    "pihps_wholesale": lambda cfg: load_pihps(cfg, "pihps_wholesale"),
    "pihps_producer": lambda cfg: load_pihps(cfg, "pihps_producer"),
    "pinksheet": load_pinksheet,
    "brent": lambda cfg: load_fred(cfg, "brent"),
    "dollar_index": lambda cfg: load_fred(cfg, "dollar_index"),
    "faostat_sua": load_faostat_sua,
    "bps_import_monthly": load_bps_import_monthly,
    "bps_import_annual": load_bps_import_annual,
    "comtrade_import": load_comtrade,
    "comtrade_import_2023": lambda cfg: load_comtrade(cfg, "comtrade_import_2023"),
    "bapanas_panel": load_bapanas_panel,
    "bapanas_het_settings": load_bapanas_het_settings,
    "padi_2024": lambda cfg: load_padi(cfg, 2024),
    "padi_2025": lambda cfg: load_padi(cfg, 2025),
    "konsumsi_beras": load_konsumsi_beras,
    "neraca_beras": load_neraca_beras,
    "het_hap_current": load_het_hap_current,
    "regulation_history": load_regulation_history,
    "jarak_hub": load_jarak_hub,
    "konkordansi_hs": load_konkordansi_hs,
    "hortikultura_produksi": load_hortikultura,
    "penduduk": load_penduduk,
    "n_kota": load_n_kota,
    "gkg_beras": load_gkg_beras,
}
