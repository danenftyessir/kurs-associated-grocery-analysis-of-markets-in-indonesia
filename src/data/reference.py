"""Tabel buatan tim (WP-07): concordance, exposure, regulation, province_features.

Semua tabel ini CC BY 4.0 dan ikut zip juri. Spesifikasi: docs/METHODS.md §M0, docs/DATASETS.md.
Input manual (penduduk, n_kota, gkg_beras) boleh belum ada: kolom terkait NaN + pesan `[reference]`.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from kagami.data.loaders import norm_name
from kagami.utils.config import Config

# Struktur, bukan parameter analisis
FAOSTAT_ELEMENTS = {"production": "Production", "import": "Import quantity", "export": "Export quantity"}
IMPORTED_INPUT_ORDINAL = {"imported_input": 2}      # 0 tidak ada, 1 rendah (belum dipakai), 2 tinggi (D-200)
PRODUCTION_ATAP = {"bawang_putih": "bawang_putih"}  # tanpa FAOSTAT -> id komoditas di hortikultura_produksi
NERACA_COMMODITY = "beras"
BAPANAS_SOURCE = "Panel Harga Bapanas (setting)"
_REG_COLUMNS = ["commodity", "instrument", "zone", "value_rp", "start_date", "end_date", "regulation", "verification",
                "commodity_raw", "in_scope", "source", "date_status", "value_min_rp", "value_max_rp"]


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Jarak great-circle (km). Dipakai untuk dist_hub_km."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------
# concordance
# ---------------------------------------------------------------------------
def build_concordance(cfg: Config, pinksheet: pd.DataFrame | None = None,
                      faostat: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-07. Dari configs/commodities.yaml + cek keberadaan seri Pink Sheet/item FAOSTAT di data (bila diberikan).

    confidence: high (padanan langsung) | medium (komposit Pink Sheet, atau item FAOSTAT dipakai >1 komoditas = proksi)
                | low (tidak ada padanan Pink Sheet maupun FAOSTAT).
    Seri Pink Sheet / item FAOSTAT yang tercantum di commodities.yaml tetapi tidak ada di data -> ValueError.
    """
    use_count: dict[str, int] = {}
    for spec in cfg.commodities.values():
        for item in spec.get("faostat_items") or []:
            use_count[item] = use_count.get(item, 0) + 1
    if pinksheet is not None:
        wanted = {s for v in cfg.commodities.values() for s in (v.get("pinksheet") or {})}
        missing = sorted(wanted - set(pinksheet["series"]))
        if missing:
            raise ValueError(f"seri Pink Sheet tidak ada di data: {missing}")
    if faostat is not None:
        missing = sorted(set(use_count) - set(faostat["item"]))
        if missing:
            raise ValueError(f"item FAOSTAT tidak ada di data: {missing}")

    rows = []
    for cid, spec in cfg.commodities.items():
        ps, fao = spec.get("pinksheet") or {}, list(spec.get("faostat_items") or [])
        if not ps and not fao:
            conf = "low"
        elif len(ps) > 1 or any(use_count[i] > 1 for i in fao):
            conf = "medium"
        else:
            conf = "high"
        rows.append({
            "commodity": cid, "pihps_name": spec["pihps_name"], "variant": spec["variant"],
            "hs_codes": ";".join(spec["hs_codes"]),
            "pinksheet": ";".join(f"{s}:{w:g}" for s, w in ps.items()),
            "faostat_items": ";".join(fao), "confidence": conf,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# exposure
# ---------------------------------------------------------------------------
def _fao_import_ratio(fao: pd.DataFrame, items: list[str], years: tuple[int, int]) -> tuple[float, list[int]]:
    """Rerata tahunan impor / (produksi + impor - ekspor) FAOSTAT; kuantitas item dijumlahkan dulu."""
    sub = fao[fao["item"].isin(items) & fao["element"].isin(FAOSTAT_ELEMENTS.values())
              & fao["year"].between(*years)]
    if sub.empty:
        return np.nan, []
    if (sub.groupby("element")["unit"].nunique() > 1).any():
        raise ValueError(f"satuan FAOSTAT berbeda antar item {items}")
    pv = sub.pivot_table(index="year", columns="element", values="value", aggfunc="sum")
    prod, imp = pv.get(FAOSTAT_ELEMENTS["production"]), pv.get(FAOSTAT_ELEMENTS["import"])
    if prod is None or imp is None:
        return np.nan, []
    exp = pv.get(FAOSTAT_ELEMENTS["export"], pd.Series(0.0, index=pv.index)).fillna(0.0)
    den = prod + imp - exp
    ratio = (imp / den).where((den > 0) & prod.notna() & imp.notna()).dropna()
    return (float(ratio.mean()) if len(ratio) else np.nan), [int(y) for y in ratio.index]


def _full_year_kg(df: pd.DataFrame, month: str, kg: str) -> pd.Series:
    """Total kg per tahun, hanya tahun dengan 12 bulan teramati."""
    g = df.groupby(df[month].dt.year)
    out = g[kg].sum()
    return out[g[month].nunique() == 12]


def _trade_import_ratio(cfg: Config, spec: dict, atap: str, bps: pd.DataFrame, comtrade: pd.DataFrame,
                        horti: pd.DataFrame, konkordansi: pd.DataFrame | None,
                        years: tuple[int, int]) -> tuple[float, list[int]]:
    """Rasio impor tanpa FAOSTAT: impor (BPS >= 2023, Comtrade sebelumnya) / (produksi ATAP + impor); ekspor diabaikan."""
    prefixes = tuple(spec["hs_codes"])
    ct = comtrade.copy()
    if konkordansi is not None and len(konkordansi):
        bridge = dict(zip(konkordansi["comtrade_code"], konkordansi["bps_hs8_prefix"]))
        ct["hs_code"] = ct["hs_code"].map(lambda c: bridge.get(c, c))
    ct = ct[ct["hs_code"].str.startswith(prefixes)]
    bp = bps[bps["hs8_code"].str.startswith(prefixes)]
    first_bps = bp["month"].min() if len(bp) else pd.NaT
    if pd.notna(first_bps):
        ct = ct[ct["month"] < first_bps]
    imp = pd.concat([_full_year_kg(ct, "month", "net_weight_kg"),
                     _full_year_kg(bp, "month", "import_netweight_kg")]) / 1000.0     # kg -> ton
    prod = horti[horti["commodity_atap"] == atap].groupby("year")["production_ton"].sum(min_count=1)
    both = pd.concat([imp.rename("imp"), prod.rename("prod")], axis=1).dropna()
    both = both[both.index.to_series().between(*years)]
    if both.empty:
        return np.nan, []
    ratio = both["imp"] / (both["prod"] + both["imp"])
    return float(ratio.mean()), [int(y) for y in ratio.index]


def build_exposure(cfg: Config, faostat: pd.DataFrame, bps_monthly: pd.DataFrame,
                   comtrade: pd.DataFrame, neraca_beras: pd.DataFrame,
                   hortikultura: pd.DataFrame | None = None,
                   konkordansi: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-07. Profil tiga jalur per komoditas.

    import_ratio_direct = impor / (produksi + impor - ekspor) rerata params.association.import_ratio_years (FAOSTAT SUA);
    komoditas tanpa item FAOSTAT (bawang putih, U5) -> impor BPS/Comtrade (via konkordansi_hs) dibagi (produksi ATAP + impor)
    pada tahun yang punya keduanya; tanpa data -> NaN dan source menyebut alasannya.
    imported_input_ordinal: 0 tidak ada, 1 rendah, 2 tinggi (jalur imported_input = 2, D-200).
    world_price_link: ada padanan Pink Sheet. source: asal angka. import_ratio_neraca (ekstra): cek silang beras dari neraca BPS.
    """
    years = tuple(int(y) for y in cfg.params["association"]["import_ratio_years"])
    horti = hortikultura if hortikultura is not None else pd.DataFrame(
        columns=["commodity_atap", "year", "production_ton"])
    rows = []
    for cid, spec in cfg.commodities.items():
        items = list(spec.get("faostat_items") or [])
        if items:
            ratio, used = _fao_import_ratio(faostat, items, years)
            src = (f"FAOSTAT SUA {used[0]}-{used[-1]} ({len(used)} thn): {'; '.join(items)}"
                   if used else "FAOSTAT SUA: tidak ada tahun lengkap")
        elif cid in PRODUCTION_ATAP and len(horti):
            ratio, used = _trade_import_ratio(cfg, spec, PRODUCTION_ATAP[cid], bps_monthly, comtrade, horti,
                                              konkordansi, years)
            src = (f"impor BPS/Comtrade HS {'/'.join(spec['hs_codes'])} / (produksi ATAP + impor), tahun {used}; "
                   "ekspor diabaikan (U5)"
                   if used else "tidak ada tahun dengan impor dan produksi lengkap (U5)")
        else:
            ratio, src = np.nan, "tidak tersedia: tanpa item FAOSTAT dan tanpa sumber produksi (U5)"
        neraca = np.nan
        if cid == NERACA_COMMODITY and len(neraca_beras):
            n = neraca_beras
            den = n["produksi_beras_ton"] + n["impor_ton"] - n["ekspor_ton"].fillna(0)
            neraca = float((n["impor_ton"] / den).mean())
        rows.append({
            "commodity": cid, "exposure_path": spec["exposure_path"], "import_ratio_direct": ratio,
            "imported_input_ordinal": IMPORTED_INPUT_ORDINAL.get(spec["exposure_path"], 0),
            "world_price_link": bool(spec.get("pinksheet")), "source": src, "import_ratio_neraca": neraca,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# regulation
# ---------------------------------------------------------------------------
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def parse_regulation_dates(text) -> tuple[pd.Timestamp, pd.Timestamp, str]:
    """Teks tanggal sumber -> (start, end, date_status). Tidak menebak tanggal yang tidak tertulis.

    date_status: range (a s.d. b) | effective (berlaku/diundangkan eksplisit) | signed_only (hanya ditetapkan,
    atau diundangkan kosong) | unlabeled (tanggal telanjang) | unknown (tanpa tanggal terverifikasi).
    """
    t = str(text)
    dates = _ISO.findall(t)
    if not dates:
        return pd.NaT, pd.NaT, "unknown"
    if "tidak terverifikasi" in t.lower():
        return pd.NaT, pd.Timestamp(dates[-1]), "unknown"
    if re.search(r"s\.d\.|sampai", t):
        end = pd.Timestamp(dates[1]) if len(dates) > 1 else pd.NaT
        return pd.Timestamp(dates[0]), end, "range" if len(dates) > 1 else "effective"
    blocked = "diundangkan kosong" in t
    for seg in re.split(r";", t):
        d = _ISO.search(seg)
        if d and re.search(r"berlaku|diundangkan", seg) and not (blocked and "kosong" in seg):
            return pd.Timestamp(d.group()), pd.NaT, "effective"
    status = "unlabeled" if "(" not in t else "signed_only"
    return pd.Timestamp(dates[0]), pd.NaT, status


def classify_verification(text) -> str:
    """Teks verifikasi sumber -> verified | partial | confirmed | unverified."""
    t = str(text)
    if t.startswith("TERVERIFIKASI"):
        return "partial" if re.search(r"belum|tidak terbaca", t) else "verified"
    if "TERVERIFIKASI" in t:
        return "partial"
    if re.search(r"erkonfirmasi|JDIH|Hukumonline", t):
        return "confirmed"
    return "unverified"


def _map_commodities(cfg: Config, text) -> list[tuple[str, bool]]:
    """Teks komoditas regulasi -> [(id komoditas / slug, in_scope)]; daftar bertanda ';' dipecah."""
    out: list[tuple[str, bool]] = []
    for tok in str(text).split(";"):
        s = norm_name(tok).lower()
        ids: list[str] = []
        if "beras" in s:
            ids = ["beras"]
        elif "minyak goreng" in s or "minyakita" in s:
            ids = ["minyak_goreng"]
        elif s.startswith("gula"):
            ids = ["gula_pasir"]
        elif s.startswith("daging sapi"):
            ids = ["daging_sapi"]
        elif s.startswith("daging ayam"):
            ids = ["daging_ayam"]
        elif s.startswith("telur"):
            ids = ["telur_ayam"]
        elif s.startswith("bawang merah"):
            ids = ["bawang_merah"]
        elif s.startswith("bawang putih"):
            ids = ["bawang_putih"]
        elif s.startswith("cabai"):
            both = ["cabai_merah", "cabai_rawit"]
            ids = ["cabai_rawit"] if "rawit" in s else ["cabai_merah"] if re.search("merah|keriting", s) else both
        ids = [i for i in ids if i in cfg.commodities]
        out += [(i, True) for i in ids] or [(re.sub(r"\W+", "_", s).strip("_") or "tidak_diketahui", False)]
    return out


def _norm_instrument(text) -> str:
    s = str(text).strip()
    fam = s.split()[0].upper() if s else ""
    if fam == "HAP":
        return "HAP_produsen" if "produsen" in s.lower() else "HAP_konsumen" if "konsumen" in s.lower() else "HAP"
    return fam


def _norm_zone(text) -> str:
    s = str(text).lower()
    m = re.search(r"zona\s*(\d)(?:\s*-\s*(\d))?", s)
    if m:
        return f"Zona {m.group(1)}-{m.group(2)}" if m.group(2) else f"Zona {m.group(1)}"
    if "semua zona" in s:
        return "Semua zona"
    if "di luar" in s or "non timur" in s:
        return "Non-Timur/3T"
    if re.search(r"maluku|papua|timur|3t", s):
        return "Timur/3T"
    return "Nasional"


def _team_rows(cfg: Config, df: pd.DataFrame | None, source: str) -> list[dict]:
    rows: list[dict] = []
    if df is None or df.empty:
        return rows
    for r in df.to_dict("records"):
        start, end, dstat = parse_regulation_dates(r["signed_or_effective_date"])
        ver = "unverified" if dstat == "unknown" else classify_verification(r["verification"])
        vmin = pd.to_numeric(r["value_min_rp"], errors="coerce")
        vmax = pd.to_numeric(r["value_max_rp"], errors="coerce")
        for cid, in_scope in _map_commodities(cfg, r["commodity"]):
            rows.append({
                "commodity": cid, "instrument": _norm_instrument(r["instrument"]), "zone": _norm_zone(r["zone_or_scope"]),
                "value_rp": vmin if vmin == vmax else np.nan, "start_date": start, "end_date": end,
                "regulation": r["regulation"], "verification": ver, "commodity_raw": r["commodity"], "in_scope": in_scope,
                "source": source, "date_status": dstat, "value_min_rp": vmin, "value_max_rp": vmax,
            })
    return rows


def build_regulation(cfg: Config, het_current: pd.DataFrame, history: pd.DataFrame,
                     bapanas_settings: pd.DataFrame) -> pd.DataFrame:
    """WP-07. Gabung riwayat HET/HAP/HPP -> satu baris per (komoditas, instrumen, zona, periode berlaku).

    Tanggal 'tidak terverifikasi' dipertahankan dengan verification='unverified' (jangan ditebak); end_date hanya dari
    rentang eksplisit (tidak disimpulkan dari regulasi pengganti). Daftar komoditas dalam satu regulasi dipecah per
    komoditas (nilai NaN). Baris Bapanas hanya dipakai bila tanggal mulai ada dan belum tercakup tabel tim
    (komoditas, HET/HAP, zona, nilai sama); verification='unverified' (jendela setting panel, bukan tanggal hukum).
    Kolom ekstra: commodity_raw, in_scope (salah satu dari 10 komoditas), source, date_status, value_min_rp, value_max_rp.
    """
    rows = _team_rows(cfg, het_current, "het_hap_current") + _team_rows(cfg, history, "regulation_history")
    out = pd.DataFrame(rows, columns=None if rows else _REG_COLUMNS)
    if bapanas_settings is not None and len(bapanas_settings):
        fam = lambda d: d["instrument"].str.split("_").str[0]          # noqa: E731
        seen = set(zip(out["commodity"], fam(out), out["zone"], out["value_rp"])) if len(out) else set()
        extra = []
        for r in bapanas_settings.dropna(subset=["start_date"]).to_dict("records"):
            zone, inst = _norm_zone(r["zone"]), str(r["type"]).upper()
            for cid, in_scope in _map_commodities(cfg, r["commodity_bapanas"]):
                if (cid, inst, zone, r["price"]) in seen:
                    continue
                extra.append({"commodity": cid, "instrument": inst, "zone": zone, "value_rp": r["price"],
                              "start_date": r["start_date"], "end_date": r["end_date"], "regulation": BAPANAS_SOURCE,
                              "verification": "unverified", "commodity_raw": r["commodity_bapanas"], "in_scope": in_scope,
                              "source": "bapanas_het_settings", "date_status": "range" if pd.notna(r["end_date"]) else "effective",
                              "value_min_rp": r["price"], "value_max_rp": r["price"]})
        out = pd.concat([out, pd.DataFrame(extra)], ignore_index=True)
    n_unv = int((out["verification"] == "unverified").sum()) if len(out) else 0
    print(f"[reference] regulation: {len(out)} baris, {n_unv} unverified (U6)")
    order = ["commodity", "instrument", "zone", "start_date"]
    return out.sort_values(order, na_position="first").reset_index(drop=True)


# ---------------------------------------------------------------------------
# province_features
# ---------------------------------------------------------------------------
def _rice_sufficiency(cfg: Config, padi: pd.DataFrame, konsumsi: pd.DataFrame, penduduk: pd.DataFrame | None,
                      gkg: pd.DataFrame | None) -> pd.DataFrame:
    """Produksi beras / kebutuhan beras per province_id (pemekaran dijumlahkan ke induk). Kosong bila input kurang."""
    cols = ["province_id", "rice_sufficiency", "rice_production_ton", "rice_need_ton"]
    empty = pd.DataFrame(columns=cols)
    if penduduk is None or penduduk.empty:
        print("[reference] rice_sufficiency NaN: populasi belum ada (U14)")
        return empty
    if gkg is None or gkg.empty:
        print("[reference] rice_sufficiency NaN: faktor konversi GKG->beras belum ada (U21)")
        return empty
    common = set(padi["year"]) & set(konsumsi["year"]) & set(penduduk["year"]) & set(gkg["year"].astype(int))
    if not common:
        print("[reference] rice_sufficiency NaN: tidak ada tahun yang ada di padi, konsumsi, penduduk, dan faktor GKG")
        return empty
    year = max(common)
    factor = float(gkg.loc[gkg["year"].astype(int) == year, "factor"].iloc[0])
    prod = padi[padi["year"] == year].groupby("province_id")["production_ton_gkg"].sum(min_count=1) * factor
    pop = penduduk[penduduk["year"] == year].groupby("province_id")["population"].sum()
    # konsumsi per kapita provinsi induk = rerata berbobot penduduk sub-provinsi (nama dicocokkan; cadangan rerata biasa)
    k = konsumsi[konsumsi["year"] == year].copy()
    p = penduduk[penduduk["year"] == year]
    norm = lambda s: norm_name(s).upper()                                            # noqa: E731
    k["key"], p = k["province_raw"].map(norm), p.assign(key=p["province_raw"].map(norm))
    k = k.merge(p[["key", "population"]], on="key", how="left")
    per_cap = k.groupby("province_id").apply(
        lambda g: np.average(g["kg_per_capita_year"], weights=g["population"]) if g["population"].notna().all() and len(g) > 1
        else g["kg_per_capita_year"].mean(), include_groups=False)
    need = per_cap * pop / 1000.0                                                # kg -> ton
    out = pd.DataFrame({"rice_production_ton": prod, "rice_need_ton": need}).dropna()
    out["rice_sufficiency"] = out["rice_production_ton"] / out["rice_need_ton"]
    print(f"[reference] rice_sufficiency tahun {year}, faktor GKG->beras {factor:g}")
    return out.reset_index()[cols]


def build_province_features(cfg: Config, padi: pd.DataFrame, konsumsi: pd.DataFrame,
                            penduduk: pd.DataFrame | None = None, gkg_beras: pd.DataFrame | None = None,
                            n_kota: pd.DataFrame | None = None, jarak_hub: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-07. Z(r) untuk Task 3b.

    dist_hub_km = jarak ibu kota ke hub terdekat (params.association.hubs; koordinat di region_crosswalk.csv;
                  provinsi hub sendiri -> jarak 0, pakai ln(1 + km)).
    rice_sufficiency = produksi beras (GKG x faktor konversi tahun itu) / kebutuhan beras (konsumsi per kapita x penduduk);
                       tahun = terbaru yang ada di semua sumber; NaN bila penduduk/faktor GKG belum ada (U14, U21).
                       Pemekaran Papua dijumlahkan ke induk sebelum rasio.
    n_kota = jumlah kota sampel PIHPS per provinsi (isi manual Abi, U15); NaN bila belum ada.
    jarak_hub (opsional): cek silang -> kolom ekstra dist_hub_km_check dan pesan selisih maksimum.
    """
    reg = cfg.regions[["province_id", "province", "lat", "lon"]].copy()
    hubs = reg[reg["province"].isin(cfg.params["association"]["hubs"])]
    lat, lon = reg["lat"].to_numpy(), reg["lon"].to_numpy()
    d = np.column_stack([haversine_km(lat, lon, h.lat, h.lon) for h in hubs.itertuples()])
    reg["dist_hub_km"] = d.min(axis=1)
    reg["ln_dist_hub"] = np.log1p(reg["dist_hub_km"])

    reg["dist_hub_km_check"] = np.nan
    if jarak_hub is not None and len(jarak_hub):
        own = jarak_hub.assign(key=jarak_hub["province_raw"].map(lambda s: norm_name(s).upper()))
        chk = reg.assign(key=reg["province"].map(lambda s: norm_name(s).upper())).merge(
            own[["key", "dist_hub_km"]].rename(columns={"dist_hub_km": "chk"}), on="key", how="left")
        reg["dist_hub_km_check"] = chk["chk"].to_numpy()
        diff = (reg["dist_hub_km"] - reg["dist_hub_km_check"]).abs()
        print(f"[reference] dist_hub_km vs jarak_hub: selisih maks {diff.max():.1f} km "
              f"({int(diff.notna().sum())} provinsi)")

    reg = reg.merge(_rice_sufficiency(cfg, padi, konsumsi, penduduk, gkg_beras), on="province_id", how="left")
    if n_kota is not None and n_kota["n_kota"].notna().any():
        nk = n_kota[["province_id", "n_kota"]].drop_duplicates("province_id")
        reg = reg.merge(nk, on="province_id", how="left")
    else:
        print("[reference] n_kota NaN: n_kota.csv belum ada (U15)")
        reg["n_kota"] = np.nan
    for c in ("rice_sufficiency", "rice_production_ton", "rice_need_ton"):
        if c not in reg:
            reg[c] = np.nan
    return reg[["province_id", "dist_hub_km", "ln_dist_hub", "rice_sufficiency", "n_kota",
                "rice_production_ton", "rice_need_ton", "dist_hub_km_check"]].sort_values("province_id").reset_index(drop=True)
