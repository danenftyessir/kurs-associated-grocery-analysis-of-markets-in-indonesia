"""WP-36. Evaluator spesifik per tahap. Setiap evaluator HANYA membaca artefak yang sudah ditulis (tidak mengubahnya),
mengambil metrik yang sudah dihitung tahap itu, dan menambah metrik generik berpenjaga (`tracking.metrics`) bila
datanya mendukung. Artefak yang tidak ada → `not_applicable` + alasan; galat satu bagian → `failed` tanpa menghentikan
bagian lain. Hitung ulang (silhouette, MAE) dipakai sebagai cek integritas terhadap artefak resmi.

Matriks tahap × metrik: docs/TRACKING.md §2.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from kagami.tracking.metrics import clustering_metrics, failed, interval_consistency, na, ok, regression_metrics, share
from kagami.tracking.schemas import Metric
from kagami.utils.config import Config
from kagami.utils.io import exists, read_artifact

STATUS_ORDER = ("observed", "carry_forward", "short", "missing")
DRIVERS_NAT = ("e", "w")
FORECAST_PROTOCOL = ("rolling-origin pseudo-real-time; latih hanya t + h ≤ origin, harga dunia as-of available_at "
                     "(features.forecast.split_origin; dites di tests/test_forecast.py)")


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
            for name in ("silhouette", "davies_bouldin", "calinski_harabasz"):
                m = ms[name]
                m.name = f"{name}_k{k}"
                res.append(m)
            if sel is not None and ms["silhouette"].status == "ok":
                stored = sel.loc[sel["k"] == k, "silhouette"]
                if len(stored) and pd.notna(stored.iloc[0]):
                    diffs.append(abs(ms["silhouette"].value - float(stored.iloc[0])))
        res.append(ok("silhouette_recompute_max_abs_diff", float(max(diffs)), g, artifact="cluster_selection",
                      note="cek integritas: silhouette dihitung ulang vs artefak") if diffs
                   else na("silhouette_recompute_max_abs_diff", g, "cluster_selection tidak ada / tanpa silhouette"))
        res.append(Metric("candidate_note", g, "kandidat k ≥ 2 tidak diterima bila silhouette ≤ p95 plasebo; DB/CH di "
                                                "sini deskriptif, bukan dasar pemilihan k", "ok"))
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

    def ablation() -> list[Metric]:
        g = "ablation fitur kurs"
        ab = _load(cfg, "ablation")
        if ab is None:
            return [_missing("share_fx_improves", g, "ablation")]
        d = ab[(ab["subset"] == "all") & (ab["level"] == "commodity")] if {"subset", "level"} <= set(ab) else ab
        return [ok("share_fx_improves", share(d["delta_mae"] > 0), g, artifact="ablation", n=int(len(d)),
                   subset="semua origin, per komoditas",
                   note="delta_mae = MAE tanpa kurs − MAE penuh; > 0 berarti fitur kurs menurunkan MAE")]

    for grp, fn in (("evaluasi rolling-origin (artefak)", official), ("galat out-of-sample (dihitung ulang)", recompute),
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
                              artifact="robustness", n=int(d["baseline_in_ci"].notna().sum())))
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
