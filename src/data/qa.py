"""QA Tahap 0 + laporan (WP-10). Semua cek silang antar sumber ada di sini."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config

# Ambang QA (bukan parameter analisis; tidak memengaruhi estimasi -- hanya penandaan, U17).
_SPIKE_LOG = 0.5
# Pemetaan Panel Harga Bapanas -> komoditas PIHPS (U20, D-110). Hanya pasangan yang jelas setara;
# dikecualikan: Beras Premium, Kedelai, Cabai Merah Besar (tidak ada di 10 komoditas) dan Minyakita
# (minyak goreng program pemerintah, bukan Kemasan Bermerk 1).
BAPANAS_TO_PIHPS = {
    "Beras Medium": "beras",
    "Bawang Merah": "bawang_merah",
    "Bawang Putih Bonggol": "bawang_putih",
    "Cabai Merah Keriting": "cabai_merah",
    "Cabai Rawit Merah": "cabai_rawit",
    "Daging Sapi Murni": "daging_sapi",
    "Daging Ayam Ras": "daging_ayam",
    "Telur Ayam Ras": "telur_ayam",
    "Gula Konsumsi": "gula_pasir",
}


def flag_price_outliers(daily: pd.DataFrame) -> pd.DataFrame:
    """WP-10. Tandai lonjakan satu hari (mis. Papua 2017-07-03 beras: 29.750 lalu 9.500).

    Aturan default: |Δlog| > 0.5 terhadap hari sebelum DAN sesudah berbalik -> flag (tidak dihapus otomatis).
    Hari sebelum/sesudah = hari teramati terdekat pada seri (province_id, commodity) yang sama.
    -> date, province_id, commodity, variant, price, prev_price, next_price, dlog_prev, dlog_next.
    """
    d = daily.sort_values(["province_id", "commodity", "date"]).reset_index(drop=True)
    g = d.groupby(["province_id", "commodity"])["price"]
    d["prev_price"], d["next_price"] = g.shift(1), g.shift(-1)
    d["dlog_prev"] = np.log(d["price"] / d["prev_price"])
    d["dlog_next"] = np.log(d["next_price"] / d["price"])
    spike = ((d["dlog_prev"].abs() > _SPIKE_LOG) & (d["dlog_next"].abs() > _SPIKE_LOG)
             & (np.sign(d["dlog_prev"]) != np.sign(d["dlog_next"])))
    cols = ["date", "province_id", "commodity", "variant", "price", "prev_price", "next_price", "dlog_prev", "dlog_next"]
    return d.loc[spike, [c for c in cols if c in d.columns]].reset_index(drop=True)


def check_import_totals(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    """WP-10. Σ bulanan BPS vs total tahunan portal (tentukan satuan 'Totals': USD atau kg).

    'Totals' = USD (D-019) -> dibandingkan dengan Σ import_value_usd. Satu baris per (hs8_code, year) yang ada di
    kedua sumber: n_months, monthly_sum_usd, annual_total_usd, ratio, ok (|ratio - 1| <= 0,001).
    """
    m = (monthly.assign(year=monthly["month"].dt.year)
         .groupby(["hs8_code", "year"])
         .agg(n_months=("month", "nunique"), monthly_sum_usd=("import_value_usd", "sum")).reset_index())
    a = annual.drop_duplicates(["hs8_code", "year"]).rename(columns={"total": "annual_total_usd"})
    out = m.merge(a[["hs8_code", "year", "annual_total_usd"]], on=["hs8_code", "year"], how="inner")
    out["ratio"] = out["monthly_sum_usd"] / out["annual_total_usd"]
    out["ok"] = (out["ratio"] - 1).abs() <= 1e-3
    return out.sort_values(["year", "hs8_code"]).reset_index(drop=True)


def check_bapanas_bias(weekly: pd.DataFrame, bapanas: pd.DataFrame) -> pd.DataFrame:
    """WP-10. Rerata bulanan PIHPS vs Panel Harga Bapanas per provinsi x komoditas (2022-2026): bias & korelasi Δ.

    PIHPS: rerata log harga mingguan per bulan (bulan hari Senin). Bapanas: log price_geomean, provinsi pemekaran
    dirata-rata ke provinsi induk (34). Pemetaan komoditas: BAPANAS_TO_PIHPS (U20).
    -> commodity, province_id, n_months, bias_log (rerata log PIHPS - log Bapanas), corr_dlog (korelasi Δ log bulanan).
    """
    b = bapanas[bapanas["commodity_bapanas"].isin(BAPANAS_TO_PIHPS) & (bapanas["price_geomean"] > 0)].copy()
    b["commodity"] = b["commodity_bapanas"].map(BAPANAS_TO_PIHPS)
    b["log_b"] = np.log(b["price_geomean"])
    b = b.dropna(subset=["province_id"]).groupby(["commodity", "province_id", "month"])["log_b"].mean().reset_index()
    w = weekly.dropna(subset=["log_price"]).copy()
    w["month"] = w["week"].dt.to_period("M").dt.to_timestamp()
    p = w.groupby(["commodity", "province_id", "month"])["log_price"].mean().rename("log_p").reset_index()
    j = p.merge(b, on=["commodity", "province_id", "month"], how="inner").sort_values(["commodity", "province_id", "month"])
    j["gap"] = j["log_p"] - j["log_b"]
    grp = j.groupby(["commodity", "province_id"])
    j["d_p"], j["d_b"] = grp["log_p"].diff(), grp["log_b"].diff()

    def summarize(g: pd.DataFrame) -> pd.Series:
        ok = g[["d_p", "d_b"]].dropna()
        corr = ok["d_p"].corr(ok["d_b"]) if len(ok) > 2 else np.nan
        return pd.Series({"n_months": len(g), "bias_log": g["gap"].mean(), "corr_dlog": corr})

    out = j.groupby(["commodity", "province_id"])[["gap", "d_p", "d_b"]].apply(summarize).reset_index()
    out["n_months"] = out["n_months"].astype(int)
    return out


def coverage_table(frames: dict[str, tuple[pd.DataFrame, str]]) -> pd.DataFrame:
    """WP-10. Cakupan per sumber: {nama: (DataFrame, kolom tanggal)} -> source, n_rows, start, end."""
    rows = []
    for name, (df, col) in frames.items():
        d = pd.to_datetime(df[col])
        rows.append({"source": name, "n_rows": len(df), "start": d.min().date(), "end": d.max().date()})
    return pd.DataFrame(rows)


def _md_table(df: pd.DataFrame, floatfmt: str = "{:.3f}", max_rows: int = 40) -> str:
    """DataFrame -> tabel markdown sederhana (tanpa dependensi tabulate)."""
    if df is None or len(df) == 0:
        return "_(kosong)_\n"
    d = df.head(max_rows)
    def fmt(v) -> str:
        if isinstance(v, pd.Timestamp):
            return str(v.date()) if v == v.normalize() else str(v)
        if isinstance(v, (float, np.floating)):
            return floatfmt.format(v) if np.isfinite(v) else "–"
        return str(v)
    lines = ["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * len(d.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in d.itertuples(index=False)]
    more = f"\n_({len(df) - max_rows} baris lain tidak ditampilkan)_" if len(df) > max_rows else ""
    return "\n".join(lines) + more + "\n"


def stage0_report(cfg: Config, sections: dict[str, pd.DataFrame]) -> str:
    """WP-10. Markdown -> artefak 'stage0_report': cakupan per sumber, kelayakan, episode, variasi kurs, MDE, QA.

    sections (semua opsional; bagian yang tidak ada dilewati): coverage, eligibility, episodes, fx_variation, mde,
    g_power (satu baris: komoditas, mde_pt8, threshold, lp_secondary), price_outliers, import_totals, bapanas_bias.
    """
    s = sections
    out = ["# Laporan Tahap 0 — KAGAMI", "",
           f"Periode {cfg.params['period']['start']} .. {cfg.params['period']['freeze']}. Dibangun oleh "
           "`pipelines.stage0`; angka di bawah berasal dari artefak Tahap 0. Hasil bersifat asosiasional.", ""]
    if "coverage" in s:
        out += ["## 1. Cakupan per sumber", "", _md_table(s["coverage"])]
    if "eligibility" in s:
        e = s["eligibility"]
        per = (e.groupby("commodity").agg(n_series=("eligible", "size"), n_eligible=("eligible", "sum"),
                                          max_missing=("missing_share", "max")).reset_index())
        out += ["## 2. Kelayakan seri", "", f"{int(e['eligible'].sum())}/{len(e)} seri layak.", "", _md_table(per)]
    if "episodes" in s:
        out += ["## 3. Episode depresiasi (Σ de 8 minggu ≥ 3%)", "", _md_table(s["episodes"])]
    if "fx_variation" in s:
        out += ["## 4. Variasi kurs per tahun", "", _md_table(s["fx_variation"], "{:.4f}")]
    if "mde" in s:
        m = s["mde"]
        nat = m[m["level"] == "national"].pivot_table(index="commodity", columns="horizon", values="mde_pt").reset_index()
        nat.columns = ["commodity"] + [f"MDE_PT(h={c})" for c in nat.columns[1:]]
        out += ["## 5. MDE (sebelum β dilihat)", "", "MDE_PT nasional (α 0,05, power 0,80):", "", _md_table(nat)]
        if "g_power" in s:
            g = s["g_power"]
            sec = bool(g["lp_secondary"].iloc[0])
            out += [_md_table(g[["commodity", "mde_pt8", "threshold"]]),
                    f"Gerbang G-power (D-007): {'LP SEKUNDER' if sec else 'LP tetap UTAMA'} "
                    f"(syarat: ketiga komoditas > {g['threshold'].iloc[0]}).", ""]
    if "price_outliers" in s:
        po = s["price_outliers"]
        out += ["## 6. QA: lonjakan harga satu hari (ditandai, tidak dihapus; U17)", "",
                f"{len(po)} hari ditandai (|Δlog| > {_SPIKE_LOG} ke hari sebelum dan berbalik ke hari sesudah).", "",
                _md_table(po.groupby("commodity").size().rename("n_flagged").reset_index()) if len(po) else ""]
    if "import_totals" in s:
        it = s["import_totals"]
        per = it.groupby("year").agg(n_hs8=("hs8_code", "size"), n_ok=("ok", "sum"),
                                     ratio_total=("monthly_sum_usd", "sum")).reset_index()
        per["ratio_total"] = per["ratio_total"] / it.groupby("year")["annual_total_usd"].sum().to_numpy()
        out += ["## 7. QA: Σ impor BPS bulanan vs total tahunan (USD, D-019)", "", _md_table(per, "{:.4f}")]
    if "bapanas_bias" in s:
        bb = s["bapanas_bias"]
        per = bb.groupby("commodity").agg(n_prov=("province_id", "size"), median_bias_log=("bias_log", "median"),
                                          median_corr_dlog=("corr_dlog", "median")).reset_index()
        out += ["## 8. QA: PIHPS vs Panel Harga Bapanas (bulanan, 2022–2026)", "",
                "bias_log = rerata log(PIHPS/Bapanas); corr_dlog = korelasi perubahan log bulanan. Minyak goreng tidak "
                "dibandingkan (Minyakita ≠ Kemasan Bermerk 1; U20).", "", _md_table(per)]
    return "\n".join(out).rstrip() + "\n"
