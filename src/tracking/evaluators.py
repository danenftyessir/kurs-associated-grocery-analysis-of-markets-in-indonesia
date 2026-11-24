"""WP-36. Evaluator spesifik per tahap. Setiap evaluator HANYA membaca artefak yang sudah ditulis (tidak mengubahnya),
mengambil metrik yang sudah dihitung tahap itu, dan menambah metrik generik berpenjaga (`tracking.metrics`) bila
datanya mendukung. Artefak yang tidak ada → `not_applicable` + alasan; galat satu bagian → `failed` tanpa menghentikan
bagian lain. Hitung ulang (silhouette, MAE) dipakai sebagai cek integritas terhadap artefak resmi.

Matriks tahap × metrik: docs/TRACKING.md §2.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from kagami.tracking.metrics import (clustering_metrics, direction_bootstrap, direction_metrics, direction_segment_table,
                                     failed, feature_health, interval_consistency, na, ok, paired_accuracy_diff,
                                     regression_metrics, selective_accuracy, share)
from kagami.stats.regression import diebold_mariano
from kagami.tracking.schemas import Metric
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact

STATUS_ORDER = ("observed", "carry_forward", "short", "missing")
DRIVERS_NAT = ("e", "w")
FORECAST_PROTOCOL = ("rolling-origin pseudo-real-time; latih hanya t + h ≤ origin, harga dunia as-of available_at "
                     "(features.forecast.split_origin; dites di tests/test_forecast.py)")
DIR_SEED_OFFSET = 3901       # RNG bootstrap blok origin metrik arah: cfg.seed + 3901 (D-140)
RIGID_CF_SHARE = 0.5         # komoditas "kaku" untuk segmen evaluasi: porsi sel carry_forward ≥ 0,5 (deskriptif, U22)


def _origin_block(cfg: Config, h: int) -> int:
    """Panjang blok bootstrap origin = ceil(h / langkah origin) + 1: origin yang target-nya bertumpuk selalu satu blok
    (h 4 → 2, h 8 → 3 dengan langkah 4 minggu)."""
    step = int(cfg.params["forecast"]["origin_step_weeks"])
    return int(np.ceil(h / step)) + 1


def _rigid_commodities(cfg: Config) -> list[str] | None:
    pw = _load(cfg, "panel_weekly")
    if pw is None:
        return None
    cf = (pw["status"] == "carry_forward").groupby(pw["commodity"]).mean()
    return sorted(cf.index[cf >= RIGID_CF_SHARE])


DEEP_MODELS = ("PTST", "TSMX", "TSMX_fx", "TFM", "TFM_fx")   # D-142 (= models.neural.ALL_MODELS)
SELECTIVE_COVERAGES = (1.0, 0.75, 0.5, 0.25)
BLOCK_SENSITIVITY = (2, 3, 4, 6)                  # panjang blok bootstrap origin yang diuji (D-144)
DM_LAG_SENSITIVITY = (1, 2, 3, 5)                 # lag HAC uji DM yang diuji (D-144)
REPLICATE_PAT = r"^(?P<base>.+)_r(?P<rep>\d+)$"   # replikasi seed model deep (= models.neural.REPLICATE)
EVALUATOR_VERSION = "2026-11-24.d144"             # naik setiap evaluator berubah; dicatat di RunRecord (D-144)   # prediksi selektif klasifier eksploratif (D-141; diagnostik)


def _attach_boot(ms: list[Metric], y_true, score, origin, block: int, seed: int) -> None:
    """Tambahkan interval bootstrap blok origin (D-140) ke konteks metrik arah yang berstatus ok."""
    if not any(m.status == "ok" for m in ms):
        return
    boot = direction_bootstrap(y_true, score, origin, block, seed=seed + DIR_SEED_OFFSET)
    if not boot:
        return
    for m in ms:
        if m.status != "ok":
            continue
        key = m.name.rsplit("_dir_", 1)[-1]
        if boot.get(key):
            m.context.update(ci_low=boot[key][0], ci_high=boot[key][1])
        if key == "accuracy" and boot.get("accuracy_gap"):
            m.context.update(gap_ci_low=boot["accuracy_gap"][0], gap_ci_high=boot["accuracy_gap"][1])
        pk = boot.get("accuracy_gap_p" if key == "accuracy" else f"{key}_p")
        if pk is not None:                                   # p bootstrap vs acuan → koreksi BH di assessment (D-143)
            m.context["p_boot"] = pk
        m.context.update(bootstrap=f"blok origin {boot['block']} × {boot['reps']} replikasi, {boot['n_origins']} origin")


def _max_run(flags: np.ndarray) -> int:
    """Panjang rangkaian True berurutan terpanjang."""
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def _load(cfg: Config, name: str) -> pd.DataFrame | None:
    return read_artifact(cfg, name) if exists(cfg, name) else None


def _missing(name: str, group: str, artifact: str) -> Metric:
    return na(name, group, f"artefak `{artifact}` tidak ada di lokasi baca (mis. paket Tingkat A atau belum ditarik)",
              artifact=artifact)


def _section(group: str, fn: Callable[[], list[Metric]]) -> list[Metric]:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 -- satu bagian gagal tidak menghentikan evaluasi lain
        return [failed(f"{group}: evaluator", group, f"{type(exc).__name__}: {exc}")]


def _key_h(cfg: Config) -> list[int]:
    return [int(h) for h in cfg.params["lp"]["key_horizons"]]


def _alpha(cfg: Config) -> float:
    return float(cfg.params["power"]["mde_alpha"])


def _bool(s: pd.Series) -> pd.Series:
    """Kolom boolean dari CSV (True/False/"True"/1/NaN, dtype object) → bool dengan NaN dipertahankan."""
    m = {True: True, False: False, "True": True, "False": False, "true": True, "false": False, 1: True, 0: False,
         1.0: True, 0.0: False}
    return s.map(lambda v: m.get(v, np.nan) if not (isinstance(v, float) and np.isnan(v)) else np.nan)


def _excludes_zero(df: pd.DataFrame) -> pd.Series:
    d = df[["ci_low", "ci_high"]]
    return ((d["ci_low"] > 0) | (d["ci_high"] < 0)).where(d.notna().all(axis=1))


# --------------------------------------------------------------------------- snapshot & Tahap 0
def evaluate_snapshot(cfg: Config) -> list[Metric]:
    g = "snapshot mentah"
    ck = _load(cfg, "checksums")
    if ck is None:
        return [_missing("n_files", g, "checksums")]
    return [ok("n_files", int(len(ck)), g, artifact="checksums"),
            ok("n_sources", int(ck["source"].nunique()), g, artifact="checksums"),
            ok("total_mb", round(float(ck["bytes"].sum()) / 2 ** 20, 2), g, artifact="checksums")]


def evaluate_stage0(cfg: Config) -> list[Metric]:
    out: list[Metric] = []

    def panel() -> list[Metric]:
        g = "kualitas data panel"
        pw = _load(cfg, "panel_weekly")
        if pw is None:
            return [_missing("panel_cells", g, "panel_weekly")]
        res = [ok("panel_cells", int(len(pw)), g, artifact="panel_weekly"),
               ok("n_provinces", int(pw["province_id"].nunique()), g, artifact="panel_weekly"),
               ok("n_weeks", int(pw["week"].nunique()), g, artifact="panel_weekly")]
        res += [ok(f"status_share_{s}", share(pw["status"] == s), g, artifact="panel_weekly") for s in STATUS_ORDER]
        res.append(ok("log_price_missing_share", share(pw["log_price"].isna()), g, artifact="panel_weekly",
                      note="sel tanpa harga (status missing/short) tidak diisi"))
        d = pw.sort_values(["commodity", "province_id", "week"])
        cf = d["status"].eq("carry_forward")
        streak = cf.groupby([d["commodity"], d["province_id"]]).apply(lambda s: _max_run(s.to_numpy()))
        rows = [{"commodity": c, "carry_forward_share": round(float(cf[d["commodity"] == c].mean()), 4),
                 "observed_share": round(float(d.loc[d["commodity"] == c, "status"].eq("observed").mean()), 4),
                 "max_carry_forward_streak_weeks": int(streak.loc[c].max()),
                 "median_series_max_streak_weeks": float(streak.loc[c].median())}
                for c in sorted(d["commodity"].unique())]
        res.append(ok("carry_forward_by_commodity", rows, g, artifact="panel_weekly",
                      note="kekakuan harga (U22): carry_forward = harga sama dengan minggu sebelumnya; bukan data jelek, "
                           "tetapi mengurangi variasi untuk mendeteksi respons kurs"))
        res.append(ok("n_rigid_commodities", int(sum(r["carry_forward_share"] >= RIGID_CF_SHARE for r in rows)), g,
                      artifact="panel_weekly", threshold=RIGID_CF_SHARE,
                      commodities=[r["commodity"] for r in rows if r["carry_forward_share"] >= RIGID_CF_SHARE]))
        return res

    def eligibility() -> list[Metric]:
        g = "kelayakan seri"
        el = _load(cfg, "eligibility")
        if el is None:
            return [_missing("eligible_series", g, "eligibility")]
        return [ok("eligible_series", int(el["eligible"].sum()), g, artifact="eligibility", n_series=int(len(el))),
                ok("eligible_share", share(el["eligible"].astype(bool)), g, artifact="eligibility")]

    def drivers() -> list[Metric]:
        g = "penggerak & episode"
        res = []
        eps = _load(cfg, "episodes")
        res.append(ok("n_episodes", int(len(eps)), g, artifact="episodes") if eps is not None
                   else _missing("n_episodes", g, "episodes"))
        if eps is not None and len(eps):
            res.append(ok("max_cum_dlog_e", float(eps["cum_dlog_e"].max()), g, artifact="episodes"))
        drv = _load(cfg, "drivers_weekly")
        if drv is None:
            return res + [_missing("sd_de", g, "drivers_weekly")]
        per = cfg.params["period"]
        w = pd.to_datetime(drv["week"])
        d = drv[(w >= pd.Timestamp(per["start"])) & (w <= pd.Timestamp(per["freeze"]))]
        ctx = {"artifact": "drivers_weekly", "period": f"{per['start']}..{per['freeze']}", "n_weeks": int(len(d))}
        res += [ok("sd_de", float(d["de"].std()), g, **ctx),
                ok("n_depreciation_weeks", int((d["de"] > 0).sum()), g, **ctx),
                ok("n_appreciation_weeks", int((d["de"] < 0).sum()), g, **ctx)]
        world = _load(cfg, "world_prices_weekly")
        res.append(ok("world_price_missing_share", share(world["log_w_idr"].isna()), g, artifact="world_prices_weekly")
                   if world is not None else _missing("world_price_missing_share", g, "world_prices_weekly"))
        return res

    def power() -> list[Metric]:
        g = "daya statistik (MDE)"
        mde = _load(cfg, "mde")
        if mde is None:
            return [_missing("mde_pt8", g, "mde")]
        p = cfg.params["power"]
        thr = float(p["mde_threshold_pt8"])
        d = mde[(mde["level"] == "national") & (mde["horizon"] == 8)].set_index("commodity")["mde_pt"]
        res = [ok(f"mde_pt8_{c}", float(d[c]), g, artifact="mde", threshold=thr) for c in p["mde_commodities"] if c in d]
        res.append(ok("n_mde_pt8_above_threshold", int(sum(float(d[c]) > thr for c in p["mde_commodities"] if c in d)),
                      g, artifact="mde", threshold=thr, commodities=list(p["mde_commodities"])))
        return res

    def qa() -> list[Metric]:
        g = "QA"
        daily = _load(cfg, "pihps_daily")
        if daily is None:
            return [_missing("price_spike_days", g, "pihps_daily")]
        from kagami.data.qa import flag_price_outliers

        return [ok("price_spike_days", int(len(flag_price_outliers(daily))), g, artifact="pihps_daily",
                   note="lonjakan satu hari |Δlog| > 0,5 yang berbalik; ditandai, tidak dihapus")]

    for grp, fn in (("kualitas data panel", panel), ("kelayakan seri", eligibility), ("penggerak & episode", drivers),
                    ("daya statistik (MDE)", power), ("QA", qa)):
        out += _section(grp, fn)
    return out


# --------------------------------------------------------------------------- Task 1
def evaluate_task1(cfg: Config) -> list[Metric]:
    H = _key_h(cfg)
    out: list[Metric] = []
    prof = _load(cfg, "profiles")

    def estimates() -> list[Metric]:
        g = "estimasi LP"
        if prof is None:
            return [_missing("n_estimates", g, "profiles")]
        res = [ok(f"n_estimates_{lv}", int((prof["level"] == lv).sum()), g, artifact="profiles")
               for lv in ("national", "region", "province")]
        nat = prof[(prof["level"] == "national") & prof["driver"].isin(DRIVERS_NAT) & prof["horizon"].isin(H)]
        ctx = {"artifact": "profiles", "subset": "nasional, β_e & ω, h kunci", "n": int(len(nat))}
        if nat.empty:
            return res + [na("share_ci_excludes_zero_national", g, "profiles tanpa baris nasional (versi wilayah)")]
        res += [ok("share_ci_excludes_zero_national", share(_excludes_zero(nat)), g, **ctx),
                ok("median_se_national", float(nat["se"].median()), g, **ctx),
                na("r2_in_sample", g, "LP dipakai untuk inferensi koefisien; fit_lp tidak menyimpan residual/R² di "
                   "artefak, dan R² dalam-sampel tidak menilai respons kurs")]
        return res

    def placebo() -> list[Metric]:
        g = "kalibrasi inferensi"
        ps = _load(cfg, "placebo_stats")
        if ps is None:
            return [_missing("placebo_false_positive_rate", g, "placebo_stats")]
        res = [ok("n_placebo_reps", int(ps["rep"].nunique()), g, artifact="placebo_stats")]
        d = ps[(ps["level"] == "national") & ps["driver"].isin(DRIVERS_NAT) & ps["horizon"].isin(H)]
        if "se" not in d or d.empty:
            return res + [na("placebo_false_positive_rate", g, "placebo_stats tanpa kolom se / baris nasional")]
        t = (d["estimate"] / d["se"]).replace([np.inf, -np.inf], np.nan)
        res.append(ok("placebo_false_positive_rate", share((t.abs() > 1.96).where(t.notna())), g,
                      artifact="placebo_stats", expected=0.05, n=int(t.notna().sum()),
                      note="porsi |t| > 1,96 di bawah null plasebo; > 0,05 = SE cluster terlalu sempit"))
        return res

    def bootstrap() -> list[Metric]:
        g = "kalibrasi inferensi"
        bs = _load(cfg, "boot_replicates")
        if bs is None or prof is None:
            return [_missing("boot_ratio_median", g, "boot_replicates" if bs is None else "profiles")]
        res = [ok("n_bootstrap_reps", int(bs["rep"].nunique()), g, artifact="boot_replicates")]
        key = ["commodity", "driver", "horizon"]
        b = bs[(bs["level"] == "national") & bs["driver"].isin(DRIVERS_NAT) & bs["horizon"].isin(H)]
        mean = b.groupby(key, as_index=False)["estimate"].mean().rename(columns={"estimate": "boot_mean"})
        nat = prof[(prof["level"] == "national") & prof["driver"].isin(DRIVERS_NAT) & prof["horizon"].isin(H)]
        m = nat[key + ["estimate"]].merge(mean, on=key)
        for h in H:
            r = (m.loc[m["horizon"] == h, "boot_mean"] / m.loc[m["horizon"] == h, "estimate"]).replace(
                [np.inf, -np.inf], np.nan).dropna()
            res.append(ok(f"boot_ratio_median_h{h}", float(r.median()), g, artifact="boot_replicates", n=int(len(r)),
                          note="rerata replikasi / estimasi; < 1 = bootstrap menarik ke nol (U107)")
                       if len(r) else na(f"boot_ratio_median_h{h}", g, "tidak ada pasangan replikasi–estimasi"))
        return res

    def events() -> list[Metric]:
        g = "event study"
        ev = _load(cfg, "events")
        if ev is None:
            return [_missing("share_events_placebo_p05", g, "events")]
        d = ev[(ev["level"] == "national") & ev["horizon"].isin(H)]
        if d.empty:
            d = ev[ev["horizon"].isin(H)]
        return [ok("n_event_episodes", int(ev["episode_id"].nunique()), g, artifact="events"),
                ok("share_events_placebo_p05", share((d["placebo_p"] < _alpha(cfg)).where(d["placebo_p"].notna())), g,
                   artifact="events", n=int(len(d)), subset=f"level {d['level'].iloc[0] if len(d) else '-'}, h kunci")]

    for grp, fn in (("estimasi LP", estimates), ("kalibrasi inferensi", placebo), ("kalibrasi bootstrap", bootstrap),
                    ("event study", events)):
        out += _section(grp, fn)
    return out


# --------------------------------------------------------------------------- Task 2
def evaluate_task2(cfg: Config) -> list[Metric]:
    out: list[Metric] = []
    sel = _load(cfg, "cluster_selection")
    k_sel = int(sel.loc[sel["accepted"].astype(bool), "k"].iloc[0]) if sel is not None and sel["accepted"].any() else 1

    def het() -> list[Metric]:
        g = "heterogenitas (H0-Het)"
        h = _load(cfg, "heterogeneity")
        if h is None:
            return [_missing("h0_het_rejected", g, "heterogeneity")]
        q = h[h["statistic"] == "Q"]
        rej = sorted(q.loc[q["reject"].astype(bool), "commodity"]) if "reject" in q else []
        return [ok("h0_het_rejected", int(len(rej)), g, artifact="heterogeneity", commodities=rej, n=int(len(q))),
                ok("min_q_fdr_Q", float(q["q_fdr"].min()), g, artifact="heterogeneity")]

    def selection() -> list[Metric]:
        g = "pemilihan k vs plasebo"
        if sel is None:
            return [_missing("selected_k", g, "cluster_selection")]
        d = sel[sel["k"] >= 2].dropna(subset=["silhouette"])
        thr = float(sel["placebo_p95"].dropna().iloc[0])
        res = [ok("selected_k", k_sel, g, artifact="cluster_selection"),
               ok("placebo_p95_silhouette", thr, g, artifact="cluster_selection")]
        res += [ok(f"silhouette_k{int(r.k)}", float(r.silhouette), g, artifact="cluster_selection", accepted=bool(r.accepted))
                for r in d.itertuples()]
        if len(d):
            res.append(ok("silhouette_margin_vs_placebo", float(d["silhouette"].max()) - thr, g,
                          artifact="cluster_selection", note="> 0 = struktur lolos uji plasebo"))
        return res

    def partition() -> list[Metric]:
        g = "partisi terpilih (Ward)"
        cl = _load(cfg, "clusters")
        feats = _load(cfg, "response_features")
        if cl is None or feats is None:
            return [_missing("n_clusters", g, "clusters" if cl is None else "response_features")]
        from kagami.features.clustering import feature_matrix
        from kagami.models.clustering import ward_labels

        ward = cl[cl["method"] == "ward"].set_index("province_id")
        X = feature_matrix(cfg, feats)
        lab = ward_labels(X.to_numpy(), k_sel)
        res = clustering_metrics(X.to_numpy(), lab, g, partition=f"Ward k = {k_sel}", artifact="response_features")
        fh = feature_health(X)
        note = ("fitur konstan = deviasi provinsi tersusut habis ke rerata oleh EB (τ² = 0); tidak membawa informasi "
                "antarprovinsi, jadi silhouette dihitung di ruang efektif yang lebih kecil")
        res += [ok("n_features", fh["n_features"], g, artifact="response_features"),
                ok("n_constant_features", fh["n_constant"], g, artifact="response_features",
                   features=fh["constant_features"], note=note),
                ok("effective_dimensions", fh["effective_dimensions"], g, artifact="response_features"),
                ok("n_redundant_feature_pairs", fh["n_redundant_pairs"], g, artifact="response_features",
                   note="pasangan fitur bervariasi dengan |r| ≥ 0,95")]
        stored = ward.reindex(X.index)["cluster"]
        res.append(ok("ward_labels_reproduced_ari", float(adjusted_rand_score(stored.astype(str), lab))
                      if k_sel >= 2 else float((stored.nunique() == 1)), g,
                      note="1 = label tersimpan = label dihitung ulang dari response_features", n=int(len(stored))))
        res.append(ok("min_jaccard", float(ward["jaccard"].min()), g, artifact="clusters"))
        res.append(ok("n_weak_clusters", int(ward.groupby("cluster")["weak"].first().astype(bool).sum()), g,
                      artifact="clusters"))
        ari = cl["ari_kmeans"].dropna() if "ari_kmeans" in cl else pd.Series(dtype=float)
        res.append(na("ari_kmeans_vs_ward", g, "k = 1: kedua metode memberi satu klaster, ARI trivial")
                   if k_sel < 2 else (ok("ari_kmeans_vs_ward", float(ari.iloc[0]), g, artifact="clusters")
                                      if len(ari) else na("ari_kmeans_vs_ward", g, "kolom ari_kmeans tidak ada")))
        return res

    def candidates() -> list[Metric]:
        g = "kandidat k ≥ 2 (diagnostik)"
        feats = _load(cfg, "response_features")
        if feats is None:
            return [_missing("silhouette_recompute_max_abs_diff", g, "response_features")]
        from kagami.features.clustering import feature_matrix
        from kagami.models.clustering import ward_labels

        X = feature_matrix(cfg, feats).to_numpy()
        res, diffs = [], []
        for k in [int(k) for k in cfg.params["clustering"]["k_range"] if int(k) >= 2]:
            ms = {m.name: m for m in clustering_metrics(X, ward_labels(X, k), g, partition=f"Ward k = {k}",
                                                        accepted=k == k_sel)}
            # silhouette kandidat sudah dilaporkan di "pemilihan k vs plasebo" (dari artefak); di sini hanya DB/CH
            # deskriptif + cek integritas silhouette dihitung ulang (D-140: tanpa metrik ganda / teks sebagai metrik)
            for name in ("davies_bouldin", "calinski_harabasz"):
                m = ms[name]
                m.name = f"{name}_k{k}"
                m.context["note"] = "deskriptif; k dipilih dari silhouette vs p95 plasebo, bukan DB/CH"
                res.append(m)
            if sel is not None and ms["silhouette"].status == "ok":
                stored = sel.loc[sel["k"] == k, "silhouette"]
                if len(stored) and pd.notna(stored.iloc[0]):
                    diffs.append(abs(ms["silhouette"].value - float(stored.iloc[0])))
        res.append(ok("silhouette_recompute_max_abs_diff", float(max(diffs)), g, artifact="cluster_selection",
                      note="cek integritas: silhouette dihitung ulang vs artefak") if diffs
                   else na("silhouette_recompute_max_abs_diff", g, "cluster_selection tidak ada / tanpa silhouette"))
        return res

    def planted() -> list[Metric]:
        g = "batas deteksi (struktur tertanam)"
        pr = _load(cfg, "planted_recovery")
        if pr is None:
            return [_missing("detection_delta", g, "planted_recovery")]
        from kagami.evaluation.planted import detection_limit

        return [ok(f"detection_delta_k{int(r.k_true)}", float(r.delta_min), g, artifact="planted_recovery",
                   rule="δ terkecil dengan recovery ≥ 0,8") if pd.notna(r.delta_min)
                else na(f"detection_delta_k{int(r.k_true)}", g, "recovery 0,8 tidak tercapai pada δ yang diuji")
                for r in detection_limit(pr).itertuples()]

    def compare() -> list[Metric]:
        g = "pembanding partisi"
        pc = _load(cfg, "partition_compare")
        if pc is None:
            return [_missing("ari_partitions", g, "partition_compare")]
        return [ok(f"ari_{r.partition}", float(r.ari), g, artifact="partition_compare") if pd.notna(r.ari)
                else na(f"ari_{r.partition}", g, "k = 1: ARI tidak terdefinisi untuk satu klaster (D-132)")
                for r in pc.itertuples()]

    for grp, fn in (("heterogenitas (H0-Het)", het), ("pemilihan k vs plasebo", selection),
                    ("partisi terpilih (Ward)", partition), ("kandidat k ≥ 2 (diagnostik)", candidates),
                    ("batas deteksi (struktur tertanam)", planted), ("pembanding partisi", compare)):
        out += _section(grp, fn)
    return out


# --------------------------------------------------------------------------- Task 3
def evaluate_task3(cfg: Config) -> list[Metric]:
    a = _alpha(cfg)
    out: list[Metric] = []

    def assoc() -> list[Metric]:
        g = "asosiasi (E1, meta-regresi)"
        df = _load(cfg, "assoc")
        if df is None:
            return [_missing("kendall_tau_b", g, "assoc")]
        res = []
        ken = df[df["method"].astype(str).str.startswith("kendall")]
        if len(ken):
            k = ken.iloc[0]
            res += [ok("kendall_tau_b", float(k["estimate"]), g, artifact="assoc", n=10),
                    ok("kendall_p_exact", float(k["p_value"]), g, artifact="assoc")]
        meta = df[df["method"].astype(str).str.startswith("meta_regression")]
        if len(meta):
            ctx = {"artifact": "assoc", "subset": "meta-regresi", "n": int(len(meta))}
            res += [ok("meta_n_p05", int((meta["p_value"] < a).sum()), g, **ctx)]
            res += ([ok("meta_n_q05", int((meta["q_fdr"] < a).sum()), g, **ctx)] if "q_fdr" in meta else [])
            res += interval_consistency(meta, g, alpha=a, name="meta_p_interval_consistency", artifact="assoc")
        else:
            res.append(na("meta_n_p05", g, "assoc tanpa baris meta-regresi (panel provinsi tidak ada)"))
        return res

    def asym() -> list[Metric]:
        g = "asimetri (H2)"
        df = _load(cfg, "asymmetry")
        if df is None:
            return [_missing("h2_confirmatory_rejected", g, "asymmetry")]
        conf = df[df["confirmatory"].astype(bool)]
        res = [ok("h2_n_confirmatory", int(len(conf)), g, artifact="asymmetry"),
               ok("h2_confirmatory_rejected", int(conf["reject"].astype(bool).sum()), g, artifact="asymmetry"),
               ok("h2_n_ci_excludes_zero", int(_excludes_zero(df).fillna(False).astype(bool).sum()), g,
                  artifact="asymmetry", n=int(len(df)))]
        res += interval_consistency(df, g, alpha=a, name="h2_p_interval_consistency", artifact="asymmetry",
                                    note="p = Wald, interval = Wald ∪ bootstrap (D-127): ketidakcocokan diharapkan")
        return res

    def regime() -> list[Metric]:
        g = "rezim HET/HAP (E2)"
        df = _load(cfg, "regime_profiles")
        if df is None:
            return [_missing("e2_n_cells", g, "regime_profiles")]
        res = [ok("e2_n_cells", int(len(df)), g, artifact="regime_profiles"),
               ok("e2_n_ci_excludes_zero", int(_excludes_zero(df).fillna(False).astype(bool).sum()), g,
                  artifact="regime_profiles")]
        if "q_fdr" in df:
            res.append(ok("e2_min_q_fdr", float(df["q_fdr"].min()), g, artifact="regime_profiles"))
        return res

    def calibrated() -> list[Metric]:
        g = "inferensi nasional terkalibrasi"
        df = _load(cfg, "national_calibrated")
        if df is None:
            return [_missing("cal_n_ci_excludes_zero", g, "national_calibrated")]
        res = [ok("cal_n_cells", int(len(df)), g, artifact="national_calibrated"),
               ok("cal_n_ci_excludes_zero", int(_excludes_zero(df).fillna(False).astype(bool).sum()), g,
                  artifact="national_calibrated"),
               ok("cal_n_q05", int((df["q_fdr"] < a).sum()), g, artifact="national_calibrated")]
        return res + interval_consistency(df, g, alpha=a, name="cal_p_interval_consistency",
                                          artifact="national_calibrated")

    for grp, fn in (("asosiasi (E1, meta-regresi)", assoc), ("asimetri (H2)", asym), ("rezim HET/HAP (E2)", regime),
                    ("inferensi nasional terkalibrasi", calibrated)):
        out += _section(grp, fn)
    return out


# --------------------------------------------------------------------------- Task 4
def evaluate_task4(cfg: Config) -> list[Metric]:
    out: list[Metric] = []
    fe = _load(cfg, "forecast_eval")

    def official() -> list[Metric]:
        g = "evaluasi rolling-origin (artefak)"
        if fe is None:
            return [_missing("mae", g, "forecast_eval")]
        d = fe[(fe["subset"] == "all") & (fe["commodity"] == "ALL") & (fe["region"] == "ALL")]
        if "level" in d:
            d = d[d["level"] == "all"]
        res = []
        for r in d.itertuples():
            ctx = {"artifact": "forecast_eval", "subset": "semua origin, semua seri", "horizon": int(r.horizon),
                   "n_origins": int(r.n_origins), "n_nonoverlap": int(r.n_nonoverlap), "protocol": FORECAST_PROTOCOL}
            res += [ok(f"mae_h{r.horizon}_{r.model}", float(r.mae), g, **ctx),
                    ok(f"rmse_h{r.horizon}_{r.model}", float(r.rmse), g, **ctx),
                    ok(f"mae_ratio_vs_m1_h{r.horizon}_{r.model}", float(r.mae_ratio_vs_m1), g, **ctx)]
            if r.model != "M1":
                res.append(ok(f"dm_p_h{r.horizon}_{r.model}", float(r.dm_p), g, **ctx) if pd.notna(r.dm_p)
                           else na(f"dm_p_h{r.horizon}_{r.model}", g, "DM tidak terdefinisi (model = pembanding / "
                                   "selisih galat konstan)", **ctx))
        if "h5_reject" in fe:
            h5 = fe[fe["h5_p_holm"].notna()] if "h5_p_holm" in fe else fe.iloc[0:0]
            res.append(ok("h5_rejected", bool(fe["h5_reject"].astype(bool).any()), g, artifact="forecast_eval",
                          n_tests=int(len(h5))))
            if len(h5):
                res.append(ok("h5_min_p_holm", float(h5["h5_p_holm"].min()), g, artifact="forecast_eval"))
        return res

    def recompute() -> list[Metric]:
        g = "galat out-of-sample (dihitung ulang)"
        preds = _load(cfg, "forecast_preds")
        if preds is None:
            return [_missing("mae_crosscheck_max_abs_diff", g, "forecast_preds")]
        res, diffs = [], []
        for (h, model), d in preds.groupby(["horizon", "model"], sort=True):
            ms = regression_metrics(d["y_true"], d["y_pred"], g, prefix=f"h{h}_{model}_", artifact="forecast_preds",
                                    horizon=int(h), model=model, protocol=FORECAST_PROTOCOL)
            res += ms
            if fe is not None:
                ref = fe[(fe["subset"] == "all") & (fe["commodity"] == "ALL") & (fe["region"] == "ALL")
                         & (fe["horizon"] == h) & (fe["model"] == model)]
                if "level" in ref:
                    ref = ref[ref["level"] == "all"]
                mae = next(m for m in ms if m.name.endswith("_mae"))
                if len(ref) and mae.status == "ok":
                    diffs.append(abs(mae.value - float(ref["mae"].iloc[0])))
        res.append(ok("mae_crosscheck_max_abs_diff", float(max(diffs)), g,
                      note="cek integritas: MAE dari forecast_preds vs forecast_eval") if diffs
                   else na("mae_crosscheck_max_abs_diff", g, "forecast_eval tidak ada untuk dibandingkan"))
        return res

    def direction() -> list[Metric]:
        g = "arah perubahan (diagnostik klasifikasi)"
        preds = _load(cfg, "forecast_preds")
        if preds is None:
            return [_missing("dir_accuracy", g, "forecast_preds")]
        res = []
        for (h, model), d in preds.groupby(["horizon", "model"], sort=True):
            ms = direction_metrics(d["y_true"], d["y_pred"], g, prefix=f"h{h}_{model}_", artifact="forecast_preds",
                                   horizon=int(h), model=model, protocol=FORECAST_PROTOCOL,
                                   note="diagnostik tambahan (bukan praregistrasi, D-139): tanda ramalan regresi vs "
                                        "tanda perubahan harga; uji resmi tetap MAE & DM")
            _attach_boot(ms, d["y_true"], d["y_pred"], d["origin"], _origin_block(cfg, int(h)), cfg.seed)
            res += ms
        return res

    def classifier() -> list[Metric]:
        g = "klasifier arah (eksploratif, D-141)"
        dp = _load(cfg, "direction_preds")
        if dp is None:
            return [na("classifier_available", g, "artefak `direction_preds` belum ada (eksploratif: `python -m kagami task4 "
                       "--direction`)", artifact="direction_preds")]
        note = ("EKSPLORATIF (D-141, bukan praregistrasi): klasifier HGB dilatih langsung untuk arah; skor = p_up − 0,5; "
                "C1 tanpa kurs, C2 + kurs (fitur M3); uji resmi H5 tetap MAE & DM")
        res = []
        for (h, model), d in dp.groupby(["horizon", "model"], sort=True):
            score = d["p_up"] - 0.5
            ms = direction_metrics(d["y_true"], score, g, prefix=f"h{h}_{model}_", artifact="direction_preds",
                                   horizon=int(h), model=model, protocol=FORECAST_PROTOCOL, note=note)
            _attach_boot(ms, d["y_true"], score, d["origin"], _origin_block(cfg, int(h)), cfg.seed)
            res += ms
            res.append(ok(f"h{h}_{model}_selective", selective_accuracy(d["y_true"], d["p_up"], d["origin"],
                                                                        SELECTIVE_COVERAGES), g,
                          artifact="direction_preds", horizon=int(h), model=model,
                          note="prediksi selektif: per origin hanya baris paling yakin |p − 0,5| (cakupan q); akurasi "
                               "harus dibaca bersama cakupan & baseline pada baris terpilih"))
        preds = _load(cfg, "forecast_preds")
        key = [c for c in ("horizon", "origin", "province_id", "region", "commodity") if c in dp.columns]
        wide = dp.assign(score=dp["p_up"] - 0.5).pivot_table(index=key, columns="model", values="score",
                                                            aggfunc="first")
        if preds is not None and set(key) <= set(preds.columns):
            for mo in ("M1", "M3"):                       # pembanding regresi pada baris yang sama
                if mo in set(preds["model"]):
                    wide = wide.join(preds[preds["model"] == mo].set_index(key)["y_pred"].rename(mo), how="left")
        y = dp.drop_duplicates(key).set_index(key)["y_true"].reindex(wide.index)
        w = wide.assign(y_true=y).reset_index()
        for h, d in w.groupby("horizon", sort=True):
            for a, b, what in (("C2", "C1", "ablation fitur kurs pada klasifier"),
                               ("C2", "M3", "klasifier vs regresi dengan fitur sama"),
                               ("C1", "M1", "klasifier tanpa kurs vs ridge dasar")):
                if a not in d or b not in d:
                    continue
                r = paired_accuracy_diff(d["y_true"], d[a], d[b], d["origin"], _origin_block(cfg, int(h)),
                                         seed=cfg.seed + DIR_SEED_OFFSET)
                name = f"h{h}_{a}_vs_{b}_accuracy_diff"
                res.append(ok(name, r["diff"], g, ci_low=r["ci_low"], ci_high=r["ci_high"], p_boot=r["p"], acc_a=r["acc_a"],
                              acc_b=r["acc_b"], n=r["n"], n_origins=r["n_origins"], comparison=what,
                              note="selisih akurasi arah pada baris yang sama; interval bootstrap blok origin berpasangan")
                           if r else na(name, g, "kurang dari 3 origin bersama"))
        return res

    def deep() -> list[Metric]:
        g = "model deep & foundation (eksploratif, D-142)"
        dd = _load(cfg, "deep_preds")
        if dd is None:
            return [na("deep_available", g, "artefak `deep_preds` belum ada (eksploratif: `python -m kagami task4 --deep`)",
                       artifact="deep_preds")]
        note = ("EKSPLORATIF (D-142, bukan praregistrasi): PatchTST/TSMixer dilatih ulang tiap 16 minggu, TimesFM 3.0 "
                "zero-shot; origin & baris uji sama dengan M0–M3; uji resmi H5 tetap M2 vs M1")
        preds = _load(cfg, "forecast_preds")
        dp = _load(cfg, "direction_preds")
        dd = dd[~dd["model"].astype(str).str.match(REPLICATE_PAT)]       # replikasi seed diringkas di seed_replication
        key = [c for c in ("horizon", "origin", "province_id", "region", "commodity") if c in dd.columns]
        step = int(cfg.params["forecast"]["origin_step_weeks"])
        frames = [dd] + ([preds[preds["model"].isin(["M1", "M3"])]] if preds is not None else [])
        if dp is not None:
            frames.append(dp[dp["model"] == "C2"].assign(y_pred=dp["p_up"] - 0.5).drop(columns="p_up"))
        allp = pd.concat(frames, ignore_index=True)
        wide = allp.pivot_table(index=key, columns="model", values="y_pred", aggfunc="first")
        y = dd.drop_duplicates(key).set_index(key)["y_true"]
        w = wide.join(y, how="inner").reset_index()
        res = []
        for (h, model), d in dd.groupby(["horizon", "model"], sort=True):
            ctx = dict(artifact="deep_preds", horizon=int(h), model=model, protocol=FORECAST_PROTOCOL, note=note)
            res += regression_metrics(d["y_true"], d["y_pred"], g, prefix=f"h{h}_{model}_", **ctx)
            ms = direction_metrics(d["y_true"], d["y_pred"], g, prefix=f"h{h}_{model}_", **ctx)
            _attach_boot(ms, d["y_true"], d["y_pred"], d["origin"], _origin_block(cfg, int(h)), cfg.seed)
            res += ms
        for h, d in w.groupby("horizon", sort=True):
            pairs = [(m, "M1") for m in DEEP_MODELS] + [("TSMX_fx", "TSMX"), ("TFM_fx", "TFM")]
            for a, b in pairs:
                if a not in d or b not in d or d[a].isna().all() or d[b].isna().all():
                    continue
                s = d.dropna(subset=[a, b, "y_true"])
                ea, eb = (s["y_true"] - s[a]).abs(), (s["y_true"] - s[b]).abs()
                pa = ea.groupby(s["origin"]).mean()
                pb = eb.groupby(s["origin"]).mean()
                stat, p = diebold_mariano(pb.to_numpy(), pa.to_numpy(), h=math.ceil(int(h) / step), loss="abs")
                ratio = float(ea.mean() / eb.mean())
                name = f"mae_ratio_vs_m1_h{h}_{a}" if b == "M1" else f"mae_ratio_h{h}_{a}_vs_{b}"
                res.append(ok(name, ratio, g, dm_p=None if not np.isfinite(p) else float(p), n=int(len(s)),
                              n_origins=int(s["origin"].nunique()), artifact="deep_preds",
                              note="rasio MAE pada baris yang sama; DM HAC pada selisih MAE per origin (seperti forecast_eval)"))
                if b == "M1":
                    res.append(ok(f"dm_p_h{h}_{a}", float(p), g, artifact="deep_preds") if np.isfinite(p)
                               else na(f"dm_p_h{h}_{a}", g, "DM tidak terdefinisi"))
            for a, b, what in [(m, "M3", "model deep vs regresi gradient boosting terbaik") for m in DEEP_MODELS] + \
                              [(m, "C2", "model deep vs klasifier arah (D-141)") for m in DEEP_MODELS] + \
                              [("TSMX_fx", "TSMX", "ablation kurs pada TSMixer"), ("TFM_fx", "TFM", "kovariat kurs pada TimesFM")]:
                if a not in d or b not in d or d[a].isna().all() or d[b].isna().all():
                    continue
                r = paired_accuracy_diff(d["y_true"], d[a], d[b], d["origin"], _origin_block(cfg, int(h)),
                                         seed=cfg.seed + DIR_SEED_OFFSET)
                name = f"h{h}_{a}_vs_{b}_accuracy_diff"
                res.append(ok(name, r["diff"], g, ci_low=r["ci_low"], ci_high=r["ci_high"], p_boot=r["p"], acc_a=r["acc_a"],
                              acc_b=r["acc_b"], n=r["n"], n_origins=r["n_origins"], comparison=what,
                              note="selisih akurasi arah pada baris yang sama; interval bootstrap blok origin berpasangan")
                           if r else na(name, g, "kurang dari 3 origin bersama"))
        return res

    def seeds() -> list[Metric]:
        g = "replikasi seed model deep (D-144)"
        dd = _load(cfg, "deep_preds")
        if dd is None or not dd["model"].astype(str).str.match(REPLICATE_PAT).any():
            return [na("seed_replication", g, "belum ada replikasi seed (`kagami task4 --deep PTST_r2 TSMX_r2 ...`)",
                       artifact="deep_preds")]
        preds = _load(cfg, "forecast_preds")
        key = [c for c in ("horizon", "origin", "province_id", "region", "commodity") if c in dd.columns]
        ext = dd["model"].astype(str).str.extract(REPLICATE_PAT)
        d = dd.assign(base=ext["base"].fillna(dd["model"].astype(str)), rep=ext["rep"].fillna("1").astype(int))
        d = d[d["base"].isin([b for b, x in d.groupby("base") if x["rep"].nunique() >= 2])]
        res = []
        for h, dh in d.groupby("horizon", sort=True):
            m1 = None
            if preds is not None:
                m1 = preds[(preds["model"] == "M1") & (preds["horizon"] == h)].set_index(key)["y_pred"]
            rows = []
            for (b, r), x in dh.groupby(["base", "rep"], sort=True):
                ms = {mm.name.rsplit("dir_", 1)[-1]: mm.value for mm in direction_metrics(x["y_true"], x["y_pred"], g)
                      if mm.status == "ok"}
                mae = float((x["y_true"] - x["y_pred"]).abs().mean())
                ratio = None
                if m1 is not None:
                    ref = m1.reindex(x.set_index(key).index).to_numpy()
                    ratio = mae / float(np.nanmean(np.abs(x["y_true"].to_numpy() - ref)))
                rows.append({"model": b, "seed": int(r), "mae": mae, "mae_ratio_vs_m1": ratio,
                             **{k: ms.get(k) for k in ("accuracy", "f1_macro", "f1_weighted", "mcc", "roc_auc")}})
            if not rows:
                continue
            tab = pd.DataFrame(rows)
            summ = []
            for b, x in tab.groupby("model"):
                s = {"model": b, "n_seeds": int(len(x))}
                for k in ("mae_ratio_vs_m1", "accuracy", "f1_macro", "f1_weighted", "mcc"):
                    v = pd.to_numeric(x[k], errors="coerce")
                    s.update({f"{k}_mean": float(v.mean()), f"{k}_sd": float(v.std(ddof=1)), f"{k}_min": float(v.min()),
                              f"{k}_max": float(v.max())})
                summ.append(s)
            res.append(ok(f"h{h}_seed_replication", summ, g, artifact="deep_preds", horizon=int(h), per_seed=rows,
                          note="seed berbeda pada origin, jendela, dan jadwal refit yang sama; sd antar seed = ketidakpastian "
                               "pelatihan, bukan ketidakpastian sampel"))
        return res

    def block_sensitivity() -> list[Metric]:
        g = "kepekaan panjang blok bootstrap (D-144)"
        preds = _load(cfg, "forecast_preds")
        if preds is None:
            return [_missing("block_sensitivity", g, "forecast_preds")]
        frames = [preds[preds["model"].isin(["M1", "M2", "M3"])]]
        dp, dd = _load(cfg, "direction_preds"), _load(cfg, "deep_preds")
        if dp is not None:
            frames.append(dp.assign(y_pred=dp["p_up"] - 0.5).drop(columns="p_up"))
        if dd is not None:
            frames.append(dd[~dd["model"].astype(str).str.match(REPLICATE_PAT)])
        allp = pd.concat(frames, ignore_index=True)
        key = [c for c in ("horizon", "origin", "province_id", "region", "commodity") if c in allp.columns]
        res = []
        for h, d in allp.groupby("horizon", sort=True):
            w = d.pivot_table(index=key, columns="model", values="y_pred", aggfunc="first").join(
                d.drop_duplicates(key).set_index(key)["y_true"]).reset_index()
            rows = []
            pairs = [("TFM", "M1"), ("TFM", "M3"), ("C2", "M3"), ("C2", "C1"), ("C1", "M1"), ("TSMX_fx", "TSMX"),
                     ("TFM_fx", "TFM")]
            for blk in BLOCK_SENSITIVITY:
                for mo in [c for c in ("M1", "M2", "M3", "C1", "C2", *DEEP_MODELS) if c in w]:
                    b = direction_bootstrap(w["y_true"], w[mo], w["origin"], blk, reps=499,
                                            seed=cfg.seed + DIR_SEED_OFFSET, ranking=False)
                    if b and b.get("accuracy_gap"):
                        rows.append({"block": str(blk), "comparison": f"{mo} vs baseline mayoritas",
                                     "ci_low": b["accuracy_gap"][0], "ci_high": b["accuracy_gap"][1],
                                     "p": b["accuracy_gap_p"]})
                for a, bb in pairs:
                    if a in w and bb in w:
                        r = paired_accuracy_diff(w["y_true"], w[a], w[bb], w["origin"], blk, reps=499,
                                                 seed=cfg.seed + DIR_SEED_OFFSET)
                        if r:
                            rows.append({"block": str(blk), "comparison": f"akurasi {a} − {bb}", "ci_low": r["ci_low"],
                                         "ci_high": r["ci_high"], "p": r["p"]})
            for lag in DM_LAG_SENSITIVITY:                                     # DM: kepekaan lag HAC
                for a, bb in (("TFM", "M1"), ("M2", "M1"), ("TFM_fx", "TFM"), ("TSMX_fx", "TSMX")):
                    if a in w and bb in w:
                        s = w.dropna(subset=[a, bb, "y_true"])
                        pa = (s["y_true"] - s[a]).abs().groupby(s["origin"]).mean()
                        pb = (s["y_true"] - s[bb]).abs().groupby(s["origin"]).mean()
                        _, pv = diebold_mariano(pb.to_numpy(), pa.to_numpy(), h=lag + 1, loss="abs")
                        rows.append({"block": f"DM lag {lag}", "comparison": f"MAE {a} / {bb}", "ci_low": None,
                                     "ci_high": None, "p": float(pv) if np.isfinite(pv) else None,
                                     "ratio": float((s["y_true"] - s[a]).abs().mean() / (s["y_true"] - s[bb]).abs().mean())})
            tab = pd.DataFrame(rows)
            stable = []
            for _, x in tab[tab["ci_low"].notna()].groupby("comparison"):
                dec = ((x["ci_low"] > 0).astype(int) - (x["ci_high"] < 0).astype(int)).tolist()
                stable.append(len(set(dec)) == 1)
            res.append(ok(f"h{h}_block_sensitivity", tab.to_dict("records"), g, horizon=int(h),
                          blocks=list(BLOCK_SENSITIVITY), dm_lags=list(DM_LAG_SENSITIVITY),
                          default_block=_origin_block(cfg, int(h)),
                          note="interval 95% selisih per panjang blok bootstrap origin (+ p DM per lag HAC); keputusan stabil "
                               "= sisi interval terhadap nol sama di semua panjang blok"))
            res.append(ok(f"h{h}_block_decisions_stable_share", float(np.mean(stable)) if stable else None, g,
                          horizon=int(h), n=len(stable),
                          note="porsi perbandingan yang keputusannya (di atas / memuat / di bawah nol) sama untuk blok "
                               + ", ".join(map(str, BLOCK_SENSITIVITY)) + " origin"))
        return res

    def segments() -> list[Metric]:
        g = "arah & galat per segmen"
        preds = _load(cfg, "forecast_preds")
        if preds is None:
            return [_missing("dir_by_segment", g, "forecast_preds")]
        com = cfg.commodities
        rigid = _rigid_commodities(cfg)
        dp = _load(cfg, "direction_preds")
        if dp is not None and set(dp.columns) >= {"y_true", "p_up"}:      # klasifier eksploratif (D-141): skor p − 0,5
            preds = pd.concat([preds, dp.assign(y_pred=dp["p_up"] - 0.5).drop(columns="p_up")], ignore_index=True)
        deep = _load(cfg, "deep_preds")                                    # model deep & foundation (D-142)
        if deep is not None:
            preds = pd.concat([preds, deep[~deep["model"].astype(str).str.match(REPLICATE_PAT)]], ignore_index=True)
        models = [m for m in ("M1", "M2", "M3", "C1", "C2", *DEEP_MODELS) if m in set(preds["model"])]
        res = []
        for h, d in preds.groupby("horizon", sort=True):
            d = d.reset_index(drop=True)
            c = d["commodity"]
            segs: dict[str, dict] = {"semua": {"ALL": np.ones(len(d), bool)},
                                     "komoditas": {k: (c == k).to_numpy() for k in sorted(c.unique())},
                                     "jalur eksposur": {p: c.isin([k for k, v in com.items() if v["exposure_path"] == p])
                                                        .to_numpy() for p in sorted({v["exposure_path"] for v in com.values()})},
                                     "grup H5 (fokus)": {p: c.isin([k for k, v in com.items() if v["role"] == "focus"
                                                                    and v["exposure_path"] == p]).to_numpy()
                                                         for p in ("direct_import", "imported_input")}}
            if rigid is not None:
                segs["kekakuan harga"] = {"kaku (carry-forward ≥ 50%)": c.isin(rigid).to_numpy(),
                                          "lentur": (~c.isin(rigid)).to_numpy()}
            yr = pd.to_datetime(d["origin"]).dt.year                     # D-144: stabilitas antar tahun (cek kontaminasi)
            segs["tahun origin"] = {str(y): (yr == y).to_numpy() for y in sorted(yr.unique())}
            rows = direction_segment_table(d, segs, models, _origin_block(cfg, int(h)), seed=cfg.seed + DIR_SEED_OFFSET,
                                           no_mae=("C1", "C2"))
            res.append(ok(f"h{h}_dir_by_segment", rows, g, artifact="forecast_preds", horizon=int(h),
                          rigid_commodities=sorted(rigid) if rigid is not None else None,
                          note="selisih accuracy − baseline kelas mayoritas segmen dengan interval bootstrap blok origin; "
                               "kaku = porsi sel carry_forward ≥ 50% di panel_weekly (U22); diagnostik, bukan uji resmi"))
        return res

    def ablation() -> list[Metric]:
        g = "ablation fitur kurs"
        ab = _load(cfg, "ablation")
        if ab is None:
            return [_missing("share_fx_improves", g, "ablation")]
        d = ab[(ab["subset"] == "all") & (ab["level"] == "commodity")] if {"subset", "level"} <= set(ab) else ab
        res = [ok("share_fx_improves", share(d["delta_mae"] > 0), g, artifact="ablation", n=int(len(d)),
                  n_improves=int((d["delta_mae"] > 0).sum()), subset="semua origin, per komoditas",
                  note="delta_mae = MAE tanpa kurs − MAE penuh; > 0 berarti fitur kurs menurunkan MAE")]
        preds = _load(cfg, "forecast_preds")
        if preds is not None and {"M1", "M2_nofx"} <= set(preds["model"]):
            key = [c for c in ("horizon", "origin", "province_id", "region", "commodity") if c in preds.columns]
            a = preds[preds["model"] == "M1"].set_index(key)["y_pred"]
            b = preds[preds["model"] == "M2_nofx"].set_index(key)["y_pred"].reindex(a.index)
            res.append(ok("ablation_model_equals_m1", bool(np.allclose(a.to_numpy(), b.to_numpy(), equal_nan=True)), g,
                          artifact="forecast_preds",
                          note="True = M2_nofx (M2 tanpa kelompok fitur kurs) identik dengan M1, jadi ablation = "
                               "perbandingan M2 vs M1 dan tidak menambah informasi"))
        return res

    for grp, fn in (("evaluasi rolling-origin (artefak)", official), ("galat out-of-sample (dihitung ulang)", recompute),
                    ("arah perubahan (diagnostik klasifikasi)", direction),
                    ("klasifier arah (eksploratif, D-141)", classifier),
                    ("model deep & foundation (eksploratif, D-142)", deep), ("arah & galat per segmen", segments),
                    ("replikasi seed model deep (D-144)", seeds),
                    ("kepekaan panjang blok bootstrap (D-144)", block_sensitivity),
                    ("ablation fitur kurs", ablation)):
        out += _section(grp, fn)
    return out


# --------------------------------------------------------------------------- Robustness
def evaluate_robustness(cfg: Config) -> list[Metric]:
    g = "robustness & validasi"

    def run() -> list[Metric]:
        rb = _load(cfg, "robustness")
        if rb is None:
            return [_missing("n_checks", g, "robustness")]
        res = []
        for tier, d in rb.groupby(rb["tier"].astype(str)):
            res.append(ok(f"n_rows_tier_{tier}", int(len(d)), g, artifact="robustness",
                          checks=sorted(d["check_id"].unique())))
            if "baseline_in_ci" in d and d["baseline_in_ci"].notna().any():
                res.append(ok(f"share_baseline_in_ci_tier_{tier}", share(_bool(d["baseline_in_ci"])), g,
                              artifact="robustness", n=int(d["baseline_in_ci"].notna().sum()),
                              note="cakupan tinggi bisa karena interval lebar; baca bersama kesamaan tanda & keputusan"))
                c = d.dropna(subset=["estimate", "baseline_estimate", "ci_low", "ci_high"])
                if len(c):
                    det = (c["ci_low"] > 0) | (c["ci_high"] < 0)
                    ctx = {"artifact": "robustness", "n": int(len(c))}
                    res += [ok(f"median_ci_width_tier_{tier}", float((c["ci_high"] - c["ci_low"]).median()), g, **ctx),
                            ok(f"sign_agreement_tier_{tier}", share((c["estimate"] * c["baseline_estimate"]) > 0), g,
                               **ctx, note="porsi estimasi cek dengan tanda sama dengan estimasi utama"),
                            ok(f"share_detected_tier_{tier}", share(det), g, **ctx,
                               note="porsi estimasi cek yang intervalnya tidak memuat nol")]
                    if "baseline_se" in c and c["baseline_se"].notna().any():
                        z = ((c["estimate"] - c["baseline_estimate"]).abs() / c["baseline_se"]).replace(
                            [np.inf, -np.inf], np.nan).dropna()
                        bdet = (c["baseline_estimate"].abs() > 1.96 * c["baseline_se"]).where(c["baseline_se"].notna())
                        res += [ok(f"median_abs_diff_over_se_tier_{tier}", float(z.median()), g, **ctx,
                                   note="|estimasi cek − estimasi utama| / SE utama; < 1 = perubahan di bawah satu SE"),
                                ok(f"decision_agreement_tier_{tier}", share((det == bdet).where(bdet.notna())), g, **ctx,
                                   note="porsi cek dengan keputusan terdeteksi/tidak (±1,96·SE utama) sama dengan utama")]
        v4 = rb[rb["check_id"].astype(str).str.startswith("V4")]
        if len(v4) and "sign_agree" in v4:
            res.append(ok("v4_mean_sign_agree", float(v4["sign_agree"].mean()), g, artifact="robustness",
                          n=int(v4["sign_agree"].notna().sum()),
                          note="sign_agree = porsi jalur event vs implikasi LP dengan tanda sama (per komoditas × h)"))
        if len(v4) and "corr" in v4 and v4["corr"].notna().any():
            res.append(ok("v4_mean_corr", float(v4["corr"].mean()), g, artifact="robustness"))
        return res

    return _section(g, run)


EVALUATORS: dict[str, Callable[[Config], list[Metric]]] = {
    "snapshot": evaluate_snapshot, "stage0": evaluate_stage0, "task1": evaluate_task1, "task2": evaluate_task2,
    "task3": evaluate_task3, "task4": evaluate_task4, "robustness": evaluate_robustness,
}


def evaluate(cfg: Config, task_id: str) -> list[Metric]:
    """Jalankan evaluator tahap; tahap tanpa evaluator → satu metrik not_applicable."""
    fn = EVALUATORS.get(task_id)
    if fn is None:
        return [na("evaluator", "umum", f"tidak ada evaluator untuk tahap {task_id}")]
    return _section(task_id, lambda: fn(cfg))
