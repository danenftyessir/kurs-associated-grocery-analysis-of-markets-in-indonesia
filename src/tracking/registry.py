"""WP-36. Spesifikasi tahap untuk log: jenis pekerjaan, algoritma, bagian params.yaml yang relevan, dan graf
dependensi yang dibaca dari REQUIRES/OPTIONAL pipeline (bukan diasumsikan linear).

Keluarga metrik yang TIDAK berlaku untuk proyek ini dicatat di NOT_APPLICABLE_FAMILIES (tidak ada klasifikasi
berlabel, reduksi dimensi, atau teks) agar dashboard menjelaskan mengapa metrik itu tidak muncul.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import Config


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    label: str
    kind: str
    algorithms: tuple[str, ...]
    params_keys: tuple[str, ...]


TASKS: dict[str, TaskSpec] = {t.task_id: t for t in [
    TaskSpec("snapshot", "Snapshot · data mentah", "data_snapshot", ("sha256 per file mentah",), ()),
    TaskSpec("stage0", "Tahap 0 · fondasi data", "data_engineering",
             ("agregasi mingguan PIHPS", "aturan kelayakan seri", "deteksi episode depresiasi",
              "MDE bentuk skor di bawah H0", "QA silang sumber"),
             ("period", "weekly", "eligibility", "episodes", "power")),
    TaskSpec("task1", "Task 1 · profil respons", "inference_estimation",
             ("local projections + SE cluster minggu", "moving-block bootstrap bersama", "plasebo geser-melingkar",
              "event study vs jendela plasebo", "penyusutan empirical Bayes (DL)"),
             ("lp", "inference", "shrinkage")),
    TaskSpec("task2", "Task 2 · pola regional", "clustering",
             ("Q/τ²/I² vs plasebo + BH", "Ward (Euclidean)", "K-Means (pembanding)", "stabilitas bootstrap Jaccard",
              "uji struktur tertanam"),
             ("clustering",)),
    TaskSpec("task3", "Task 3 · asosiasi & uji", "association_tests",
             ("Kendall τ-b permutasi eksak", "meta-regresi efek acak (CR2 + bootstrap)", "interaksi efek tetap",
              "Wald H2 β⁺ = β⁻", "LP per rezim HET/HAP (E2)", "kalibrasi plasebo nasional"),
             ("association",)),
    TaskSpec("task4", "Task 4 · evaluasi prediktif", "forecasting_regression",
             ("M0 tanpa perubahan", "M1 ridge dasar", "M2 ridge + kurs & harga dunia", "M3 gradient boosting",
              "Diebold–Mariano HAC"),
             ("forecast",)),
    TaskSpec("robustness", "Robustness & validasi", "robustness",
             ("Tier 1: LP ulang per cek", "validasi V2/V4", "Tier 2 (opsional)"),
             ("lp", "calendar")),
]}

ORDER = tuple(TASKS)

NOT_APPLICABLE_FAMILIES: dict[str, str] = {
    "klasifikasi (accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix)":
        "tidak ada tahap klasifikasi berlabel; klaster Task 2 tanpa ground truth",
    "reduksi dimensi (explained variance, reconstruction error)":
        "tidak ada PCA/SVD/embedding di pipeline; fitur clustering = z-score fitur respons",
    "NLP (BLEU, ROUGE, perplexity, vocabulary, OOV)": "tidak ada data teks yang dimodelkan",
}


def task_params(cfg: Config, task_id: str) -> dict[str, Any]:
    """Bagian params.yaml yang relevan untuk tahap (salinan, untuk log & perbandingan run)."""
    spec = TASKS.get(task_id)
    if spec is None:
        return {}
    out = {k: cfg.params[k] for k in spec.params_keys if k in cfg.params}
    out["seed"] = cfg.seed
    return out


def stage_requires() -> dict[str, dict[str, tuple[str, ...]]]:
    """tahap → {"required": REQUIRES, "optional": OPTIONAL} dibaca dari modul pipeline (impor lokal: hindari siklus)."""
    from kagami.pipelines import robustness, stage0, task1, task2, task3, task4

    mods = {"stage0": stage0, "task1": task1, "task2": task2, "task3": task3, "task4": task4,
            "robustness": robustness}
    out: dict[str, dict[str, tuple[str, ...]]] = {"snapshot": {"required": (), "optional": ()}}
    for k, m in mods.items():
        out[k] = {"required": tuple(m.REQUIRES), "optional": tuple(getattr(m, "OPTIONAL", ()))}
    return out


def dependency_edges() -> list[dict[str, Any]]:
    """Sisi graf: producer (tahap penulis artefak) → consumer, per artefak, wajib/opsional. stage0 menjalankan snapshot
    di dalamnya (tidak lewat REQUIRES), jadi sisi snapshot → stage0 ditambahkan eksplisit."""
    edges = [{"producer": "snapshot", "consumer": "stage0", "artifact": "checksums", "required": True}]
    for consumer, req in stage_requires().items():
        for kind in ("required", "optional"):
            for name in req[kind]:
                prod = ARTIFACTS[name].stage
                edges.append({"producer": prod, "consumer": consumer, "artifact": name, "required": kind == "required"})
    return edges


def stage_outputs(task_id: str) -> list[str]:
    """Artefak registry yang ditulis tahap ini."""
    return [n for n, a in ARTIFACTS.items() if a.stage == task_id]
