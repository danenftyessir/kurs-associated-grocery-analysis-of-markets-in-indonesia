"""Jalur A Workstream B2: ringkasan validasi manual 111 kandidat artikel GDELT (hasil/b_manual_labels.csv, dilabeli agent dari judul/URL).

Label: R = relevan (pasokan, produksi, panen, bencana sentra, kebijakan impor/ekspor/harga, distribusi, stabilisasi, stok untuk komoditas
KAGAMI atau bahan pokok), P = sebagian (laporan harga eceran reaktif, politik/umum, hukum, budidaya jangka panjang, bantuan politik),
I = tidak relevan (salah cocok substring, resep/gaya hidup, promo ritel, amal).
Varian penyaring yang dinilai pada sampel yang sama:
  F0  pola awal (tanpa batas kata)                          — semua kandidat
  F1  pola dengan batas kata + tanpa `sawit` + kecuali "pondok cabe"
  F2  F1 + wajib kata kunci pasokan/kebijakan (SUPPLY)
  F1d / F2d  F1 / F2 + deduplikasi judul per hari
→ hasil/b_manual_summary.json
"""
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hasil")
F1 = {
    "beras": r"\bberas\b|\bpadi\b|\bgabah\b",
    "bawang_putih": r"\bbawang putih\b",
    "bawang_merah": r"\bbawang merah\b",
    "cabai": r"\bcabai\b|\bcabe\b",
    "gula_pasir": r"\bgula pasir\b|\bgula kristal\b|\bgula\b",
    "minyak_goreng": r"\bminyak goreng\b|\bmigor\b|\bminyakita\b|\bcpo\b",
    "daging_sapi": r"\bdaging sapi\b|\bsapi impor\b|\bsapi bakalan\b",
    "daging_ayam": r"\bdaging ayam\b|\bayam ras\b|\bayam broiler\b|\blive bird\b",
    "telur_ayam": r"\btelur ayam\b|\bharga telur\b|\btelur\b",
    "umum": r"\bsembako\b|\bbahan pokok\b|\bbapok\b|\bpangan\b|\bbulog\b|\bbapanas\b|\binflasi pangan\b",
}
EXCLUDE = re.compile(r"pondok cabe", re.I)
SUPPLY = re.compile(
    r"\b(pasokan|stok|panen|gagal panen|impor|ekspor|larangan|distribusi|banjir|kekeringan|kemarau|operasi pasar|het|hap|"
    r"harga eceran tertinggi|harga acuan|kelangkaan|langka|cadangan|produksi|petani|peternak|pakan|subsidi|kuota|dmo|dpo|gudang|"
    r"penimbunan|timbun|bencana|hama|wabah|stabilisasi|stabilkan|sphp|pangan murah|penyerapan|serap|bansos beras|swasembada)\b", re.I)
PAT = {k: re.compile(v, re.I) for k, v in F1.items()}


def slug_text(url):
    u = re.sub(r"^https?://[^/]+", "", url or "")
    u = re.sub(r"\.(html?|php|aspx?)$", "", u)
    return re.sub(r"[-_/+]", " ", u)


def prec(d):
    n = len(d)
    return {"n": n, "R": int((d["label"] == "R").sum()), "P": int((d["label"] == "P").sum()), "I": int((d["label"] == "I").sum()),
            "precision_R": float((d["label"] == "R").mean()) if n else np.nan,
            "precision_RP": float(d["label"].isin(["R", "P"]).mean()) if n else np.nan}


if __name__ == "__main__":
    a = pd.read_csv(os.path.join(OUT, "b_gkg_sample_articles.csv"))
    lab = pd.read_csv(os.path.join(OUT, "b_manual_labels.csv"))
    d = a.reset_index().rename(columns={"index": "idx"}).merge(lab, on="idx")
    assert len(d) == len(a) == len(lab)
    d["text"] = (d["title"].fillna("") + " " + d["url"].map(slug_text)).str.lower()
    d["f1_groups"] = d["text"].map(lambda t: ";".join(k for k, p in PAT.items() if p.search(t)) if not EXCLUDE.search(t) else "")
    d["f1"] = d["f1_groups"] != ""
    d["f2"] = d["f1"] & d["text"].map(lambda t: bool(SUPPLY.search(t)))
    d["day"] = d["gdelt_date"].astype(str).str[:8]
    d["tkey"] = d["title"].fillna(d["url"]).str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
    d["dup"] = d.duplicated(["day", "tkey"])
    files = pd.read_csv(os.path.join(OUT, "b_gkg_sample_files.csv"))
    nb = int(files["ok"].sum())
    res = {"n_batches": nb, "n_candidates": int(len(d)),
           "F0": prec(d), "F1": prec(d[d["f1"]]), "F2": prec(d[d["f2"]]),
           "F1d": prec(d[d["f1"] & ~d["dup"]]), "F2d": prec(d[d["f2"] & ~d["dup"]]),
           "dup_share_F1": float(d.loc[d["f1"], "dup"].mean()),
           "false_match_share_F0": float((d["category"] == "false_match").mean()),
           "false_match_left_F1": int(((d["category"] == "false_match") & d["f1"]).sum()),
           "relevant_lost_by_F2": int(((d["label"] == "R") & d["f1"] & ~d["f2"]).sum()),
           "relevant_lost_by_F1": int(((d["label"] == "R") & ~d["f1"]).sum())}
    # keterkaitan komoditas: kelompok benar termuat di kelompok hasil penyaring
    rp = d[d["label"].isin(["R", "P"]) & d["f1"]]
    res["commodity_link_accuracy_RP_F1"] = float(np.mean([str(t) in g.split(";") for t, g in zip(rp["true_group"], rp["f1_groups"])]))
    res["share_umum_only_RP"] = float((rp["true_group"] == "umum").mean())
    res["category_R"] = d.loc[d["label"] == "R", "category"].value_counts().to_dict()
    res["category_P"] = d.loc[d["label"] == "P", "category"].value_counts().to_dict()
    res["price_report_share_RP"] = float((rp["category"] == "price_report").mean())
    # lokasi: V2Locations memuat ADM1 Indonesia
    r = d[d["label"] == "R"]
    res["share_R_with_id_adm1"] = float(r["id_adm1"].notna().mean())
    # ketepatan waktu: DATE GDELT vs tanggal di URL
    g = pd.to_datetime(d["gdelt_date"].astype(str), format="%Y%m%d%H%M%S")
    u = pd.to_datetime(d["url_date"], errors="coerce")
    lag = (g.dt.normalize() - u).dt.days
    ok = lag.notna()
    res["timeliness"] = {"n_with_url_date": int(ok.sum()), "lag_days_median": float(lag[ok].median()),
                         "share_lag_le_1d": float((lag[ok] <= 1).mean()), "lag_days_max": float(lag[ok].max()),
                         "share_lag_negative": float((lag[ok] < 0).mean())}
    # volume tersirat per hari nasional (96 batch/hari): relevan setelah F2d
    nd = d[d["f2"] & ~d["dup"]]
    res["implied_per_day_F2d_R"] = float((nd["label"] == "R").sum() / nb * 96)
    res["implied_per_day_F1d_RP"] = float(d[d["f1"] & ~d["dup"]]["label"].isin(["R", "P"]).sum() / nb * 96)
    res["by_year_F1d_R"] = d[d["f1"] & ~d["dup"] & (d["label"] == "R")]["ts"].astype(str).str[:4].value_counts().sort_index().to_dict()
    json.dump(res, open(os.path.join(OUT, "b_manual_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    d.drop(columns=["text"]).to_csv(os.path.join(OUT, "b_manual_scored.csv"), index=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
