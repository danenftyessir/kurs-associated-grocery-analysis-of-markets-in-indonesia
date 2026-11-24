"""Registry artefak = kontrak data antar tahap.

Setiap artefak punya: path, tahap produsen, WP, kolom wajib, dan flag ``ship``
(ikut zip juri atau tidak; mengikuti hak redistribusi, proposal §7.2).
Pipeline menulis lewat ``kagami.utils.io.write_artifact`` (validasi kolom), aplikasi Streamlit
membaca lewat ``kagami.utils.io.read_artifact``. Ubah kontrak di sini DAN di docs/ARCHITECTURE.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Artifact:
    name: str
    path: str
    stage: str
    wp: str
    columns: tuple[str, ...]
    ship: bool
    description: str


_A = Artifact

ARTIFACTS: dict[str, Artifact] = {
    a.name: a
    for a in [
        # ---------------- Tahap 0 ----------------
        _A("checksums", "data/raw/checksums.csv", "snapshot", "WP-01",
           ("source", "file", "bytes", "sha256", "retrieved_at", "recorded_at"), True,
           "sha256 + retrieved_at setiap snapshot mentah"),
        _A("pihps_daily", "data/interim/pihps_daily.parquet", "stage0", "WP-03",
           ("date", "province_id", "commodity", "variant", "price"), False,
           "PIHPS harian long, varian representatif saja"),
        _A("panel_weekly", "data/processed/panel_weekly.parquet", "stage0", "WP-03",
           ("week", "province_id", "commodity", "price", "log_price", "n_days", "status"), True,
           "Panel mingguan provinsi x komoditas (dikirim: izin BI mencakup redistribusi turunan, D-104)"),
        _A("eligibility", "results/stage0/eligibility.csv", "stage0", "WP-04",
           ("province_id", "commodity", "missing_share", "max_gap_weeks", "min_year_coverage", "eligible"), True,
           "Kelayakan seri"),
        _A("drivers_weekly", "data/processed/drivers_weekly.parquet", "stage0", "WP-05",
           ("week", "log_e", "de", "de_pos", "de_neg", "log_brent", "db", "log_dxy", "d_dxy",
            "month", "idf_rel_week", "episode"), True,
           "Penggerak nasional mingguan + kalender musiman"),
        _A("world_prices_weekly", "data/processed/world_prices_weekly.parquet", "stage0", "WP-05",
           ("week", "commodity", "log_w_usd", "log_w_idr", "dw", "available_at"), True,
           "Harga dunia padanan (USD & rupiah) per komoditas, selaras periode observasi"),
        _A("episodes", "results/stage0/episodes.csv", "stage0", "WP-06",
           ("episode_id", "start_week", "end_week", "cum_dlog_e"), True,
           "Episode depresiasi kumulatif >= 3% dalam 8 minggu"),
        _A("fx_variation", "results/stage0/fx_variation.csv", "stage0", "WP-06",
           ("period", "n_dep_weeks", "n_app_weeks", "mean_dep", "mean_app", "sd_de"), True,
           "Tabel variasi kurs"),
        _A("concordance", "data/reference/concordance.csv", "stage0", "WP-07",
           ("commodity", "pihps_name", "variant", "hs_codes", "pinksheet", "faostat_items", "confidence"), True,
           "Concordance PIHPS-HS-Pink Sheet-FAOSTAT"),
        _A("exposure", "data/reference/exposure.csv", "stage0", "WP-07",
           ("commodity", "exposure_path", "import_ratio_direct", "imported_input_ordinal",
            "world_price_link", "source"), True,
           "Profil tiga jalur eksposur per komoditas"),
        _A("regulation", "data/reference/regulation.csv", "stage0", "WP-07",
           ("commodity", "instrument", "zone", "value_rp", "start_date", "end_date", "regulation", "verification"), True,
           "Tabel regulasi HET/HAP/HPP komoditas x zona x tanggal"),
        _A("province_features", "data/reference/province_features.csv", "stage0", "WP-07",
           ("province_id", "dist_hub_km", "ln_dist_hub", "rice_sufficiency", "n_kota"), True,
           "Karakteristik provinsi Z(r) untuk Task 3"),
        _A("panel_weekly_region", "data/processed/panel_weekly_region.parquet", "stage0", "WP-08",
           ("week", "region", "commodity", "log_price_index", "n_provinces"), True,
           "Rerata 7 wilayah, indeks berbasis minggu pertama (data minimum Tingkat B)"),
        _A("mde", "results/stage0/mde.csv", "stage0", "WP-09",
           ("commodity", "level", "horizon", "mde_beta", "mde_pt"), True,
           "MDE dari residual model tanpa kurs (sebelum Task 1)"),
        _A("stage0_report", "results/stage0/stage0_report.md", "stage0", "WP-10",
           (), True, "Laporan Tahap 0: cakupan, kelayakan, QA silang"),
        # ---------------- Task 1 ----------------
        _A("profiles", "results/task1/profiles.parquet", "task1", "WP-13",
           ("level", "unit", "commodity", "driver", "horizon", "estimate", "se", "ci_low", "ci_high",
            "n_weeks", "shrunk"), True,
           "Kurva respons nasional/wilayah/provinsi per penggerak & horizon"),
        _A("boot_replicates", "results/task1/boot_replicates.parquet", "task1", "WP-16",
           ("rep", "level", "unit", "commodity", "driver", "horizon", "estimate"), True,
           "Replikasi moving-block bootstrap bersama"),
        _A("placebo_stats", "results/task1/placebo_stats.parquet", "task1", "WP-16",
           ("rep", "level", "unit", "commodity", "driver", "horizon", "estimate"), True,
           "Profil di bawah null plasebo geser-melingkar (provinsi: hanya h=4,8,12); sumber semua statistik null"),
        _A("events", "results/task1/events.parquet", "task1", "WP-14",
           ("episode_id", "level", "unit", "commodity", "horizon", "dlog_price", "placebo_lo",
            "placebo_hi", "placebo_p"), True,
           "Event study per episode vs 499 jendela plasebo"),
        _A("response_features", "results/task1/response_features.parquet", "task1", "WP-17",
           ("level", "unit", "commodity", "R4", "R8", "R12", "W4", "W8", "W12", "PT8", "t_half", "A8"), True,
           "Fitur respons (tersusut EB untuk provinsi)"),
        # ---------------- Task 2 ----------------
        _A("heterogeneity", "results/task2/heterogeneity.csv", "task2", "WP-18",
           ("commodity", "horizon", "statistic", "value", "p_placebo", "q_fdr"), True,
           "Q, tau2, I2 per komoditas + rho_bar lintas komoditas vs plasebo"),
        _A("cluster_selection", "results/task2/cluster_selection.csv", "task2", "WP-19",
           ("k", "silhouette", "placebo_p95", "accepted"), True,
           "Pemilihan k terhadap plasebo"),
        _A("clusters", "results/task2/clusters.parquet", "task2", "WP-20",
           ("province_id", "method", "k", "cluster", "jaccard", "weak"), True,
           "Asignasi klaster Ward & K-Means + stabilitas"),
        _A("coassign", "results/task2/coassign.parquet", "task2", "WP-20",
           ("province_i", "province_j", "share"), True,
           "Matriks ko-asignasi bootstrap"),
        _A("partition_compare", "results/task2/partition_compare.csv", "task2", "WP-20",
           ("partition", "ari", "n_groups"), True,
           "ARI klaster vs zona HET beras, Jawa/luar Jawa, kuantil n_kota (cek artefak sampling)"),
        _A("planted_recovery", "results/task2/planted_recovery.csv", "task2", "WP-21",
           ("delta", "k_true", "recovery_rate", "ari_mean"), True,
           "Kurva pemulihan struktur tertanam (batas deteksi)"),
        # ---------------- Task 3 ----------------
        _A("assoc", "results/task3/assoc.csv", "task3", "WP-22",
           ("level", "feature", "outcome", "estimate", "ci_low", "ci_high", "p_value", "method",
            "jackknife_min", "jackknife_max"), True,
           "Asosiasi profil respons dengan eksposur & karakteristik provinsi"),
        _A("regime_profiles", "results/task3/regime_profiles.csv", "task3", "WP-22",
           ("commodity", "regime_id", "regime_start", "regime_end", "driver", "horizon", "estimate", "ci_low",
            "ci_high", "n_weeks"), True,
           "E2 eksploratif: β kurs & ω harga dunia nasional per rezim HET/HAP (D-124)"),
        _A("asymmetry", "results/task3/asymmetry.csv", "task3", "WP-13",
           ("commodity", "horizon", "estimate", "se", "ci_low", "ci_high", "p_value", "confirmatory", "reject"), True,
           "H2: uji Wald β⁺ = β⁻ nasional (SE cluster minggu) + pembanding bootstrap & plasebo (D-125)"),
        _A("national_calibrated", "results/task3/national_calibrated.csv", "task3", "WP-13",
           ("commodity", "driver", "horizon", "estimate", "se", "ci_low", "ci_high", "p_value", "q_fdr"), True,
           "β_e & ω nasional h kunci: interval ±crit·SE & p terkalibrasi plasebo, q BH (tambahan, D-129)"),
        # ---------------- Task 4 ----------------
        _A("forecast_preds", "data/interim/forecast_preds.parquet", "task4", "WP-26",
           ("origin", "horizon", "model", "region", "commodity", "y_true", "y_pred", "large_move"), False,
           "Prediksi rolling-origin M0-M3 + M2_nofx (input WP-27; di-push ke Drive agar tahan sesi Kaggle habis; tidak dikirim)"),
        _A("direction_preds", "data/interim/direction_preds.parquet", "task4", "WP-36",
           ("origin", "horizon", "model", "region", "commodity", "y_true", "p_up", "large_move"), False,
           "EKSPLORATIF (D-141): probabilitas naik klasifier arah C1 (tanpa kurs) & C2 (+ kurs), rolling-origin sama dengan Task 4; tidak dikirim"),
        _A("direction_tuned_preds", "data/interim/direction_tuned_preds.parquet", "task4", "WP-36",
           ("origin", "horizon", "model", "region", "commodity", "y_true", "p_up", "large_move"), False,
           "EKSPLORATIF (D-145): probabilitas naik klasifier arah tuned C1t (+ fitur dinamika harga) & C2t (+ kurs), rolling-origin sama dengan Task 4; tidak dikirim"),
        _A("deep_preds", "data/interim/deep_preds.parquet", "task4", "WP-36",
           ("origin", "horizon", "model", "region", "commodity", "y_true", "y_pred", "large_move"), False,
           "EKSPLORATIF (D-142): ramalan PatchTST, TSMixer (± kurs), TimesFM 3.0 zero-shot (± kurs) pada origin & baris Task 4; tidak dikirim"),
        _A("forecast_eval", "results/task4/forecast_eval.csv", "task4", "WP-27",
           ("horizon", "model", "subset", "commodity", "region", "mae", "rmse", "mae_ratio_vs_m1",
            "rmse_ratio_vs_m1", "dm_stat", "dm_p", "n_origins", "n_nonoverlap"), True,
           "Evaluasi rolling-origin M0-M3"),
        _A("ablation", "results/task4/ablation.csv", "task4", "WP-27",
           ("horizon", "commodity", "region", "mae_full", "mae_without_fx", "delta_mae"), True,
           "Ablation kelompok fitur kurs"),
        # ---------------- Robustness & validasi ----------------
        _A("robustness", "results/robustness.csv", "robustness", "WP-28",
           ("check_id", "tier", "commodity", "horizon", "estimate", "ci_low", "ci_high",
            "baseline_estimate", "note"), True,
           "Robustness Tier 1/2 + validasi V2-V4"),
        # ---------------- Laporan ----------------
        _A("findings", "results/findings.md", "report", "WP-33",
           (), True, "Temuan final berbahasa asosiasional (lolos pemeriksaan klaim G8); dibaca halaman app 6"),
    ]
}

