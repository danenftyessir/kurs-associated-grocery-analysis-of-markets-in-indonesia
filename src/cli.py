"""CLI: ``python -m kagami <command>``. Notebook memanggil modul yang sama (kagami.pipelines.*).

  status            sumber mentah & artefak (ada/belum, lokasi, WP produsen)
  snapshot          hash semua file mentah -> data/raw/checksums.csv
  download [KEY..]  Tingkat C: unduh ulang sumber http / cetak instruksi manual
  stage0|task1|task2|task3|task4|robustness   jalankan satu tahap (= satu notebook)
  all               stage0 -> task1 -> task2 -> task3 -> task4 -> robustness
  package           zip submission juri (allowlist hak data)
  bundle [--raw]    zip kode untuk Kaggle/Colab (+ zip data mentah PRIVAT bila --raw)
  drive-pull [TAHAP|all ..]   unduh artefak input tahap (atau semua) dari folder Drive tim ke out_dir
  drive-push TAHAP ..         unggah artefak hasil tahap ke folder Drive tim
  drive-push-raw              unggah semua data mentah (+checksums) ke data/raw/ di Drive tim (MD5 sama dilewati)
  drive-pull-raw              unduh data mentah yang belum ada di raw_dir dari Drive tim (tidak menimpa)
  drive-auth --client-secret F  buat token OAuth Drive (sekali per anggota; isi untuk Kaggle Secret)
  app               jalankan Streamlit (Tingkat A)
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from kagami.data import download, snapshot
from kagami.pipelines import package, robustness, stage0, task1, task2, task3, task4
from kagami.utils import drive
from kagami.utils.artifacts import ARTIFACTS
from kagami.utils.config import get_config
from kagami.utils.env import artifact_status

PIPELINE = {
    "stage0": stage0.run,
    "task1": task1.run,
    "task2": task2.run,
    "task3": task3.run,
    "task4": task4.run,
    "robustness": robustness.run,
}
_MODULES = {"stage0": stage0, "task1": task1, "task2": task2, "task3": task3, "task4": task4, "robustness": robustness}
# input yang ditarik `drive-pull <tahap>`: wajib + opsional (panel provinsi, D-122)
PIPELINE_REQUIRES = {k: tuple(m.REQUIRES) + tuple(getattr(m, "OPTIONAL", ())) for k, m in _MODULES.items()}


def status(cfg) -> None:
    print(f"== Sumber mentah (raw_dir = {cfg.raw_dir})")
    for key, src in cfg.sources.items():
        ok = all(f.exists() for f in cfg.source_files(key)) and bool(cfg.source_files(key))
        print(f"  [{'x' if ok else ' '}] {key:22s} {src['path']}")
    print(f"== Artefak (src/utils/artifacts.py; dibaca dari {[str(d) for d in cfg.read_dirs]})")
    for r in artifact_status(cfg).itertuples():
        print(f"  [{'x' if r.available else ' '}] {r.artifact:22s} {r.wp:6s} {r.stage:10s} "
              f"{'ship' if r.ship else '    '} {r.location}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kagami", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["status", "snapshot", "download", *PIPELINE, "all", "package",
                                        "bundle", "app", "drive-pull", "drive-push", "drive-auth",
                                        "drive-push-raw", "drive-pull-raw"])
    ap.add_argument("keys", nargs="*", help="kunci sumber (`download`) atau nama tahap (`drive-pull`, `drive-push`)")
    ap.add_argument("--client-secret", help="drive-auth: file client_secret OAuth (Desktop app) dari Google Cloud")
    ap.add_argument("--tier2", action="store_true", help="robustness: sertakan Tier 2")
    ap.add_argument("--allow-missing", action="store_true", help="package: izinkan artefak belum lengkap")
    ap.add_argument("--raw", action="store_true", help="bundle: sertakan zip data mentah PRIVAT")
    args = ap.parse_args(argv)
    cfg = get_config()

    if args.command == "status":
        status(cfg)
    elif args.command == "snapshot":
        snapshot.run(cfg)
    elif args.command == "download":
        download.run(cfg, args.keys or None)
    elif args.command == "robustness":
        robustness.run(cfg, include_tier2=args.tier2)
    elif args.command in PIPELINE:
        PIPELINE[args.command](cfg)
    elif args.command == "all":
        for name, fn in PIPELINE.items():
            print(f"== {name}")
            fn(cfg)
    elif args.command == "package":
        package.submission(cfg, allow_missing=args.allow_missing)
    elif args.command == "bundle":
        package.code_bundle(cfg)
        if args.raw:
            package.raw_bundle(cfg)
    elif args.command == "drive-pull":
        stages = args.keys or ["all"]
        names = list(ARTIFACTS) if "all" in stages else sorted({n for s in stages for n in PIPELINE_REQUIRES[s]})
        drive.pull(cfg, names, strict=True)
    elif args.command == "drive-push":
        if not args.keys:
            ap.error("drive-push butuh nama tahap, mis. `drive-push stage0`")
        stages = set(args.keys) | ({"snapshot"} if "stage0" in args.keys else set())
        drive.push(cfg, stages, strict=True)
    elif args.command == "drive-push-raw":
        drive.push_raw(cfg, strict=True)
    elif args.command == "drive-pull-raw":
        drive.pull_raw(cfg, strict=True)
    elif args.command == "drive-auth":
        if not args.client_secret:
            ap.error("drive-auth butuh --client-secret <file client_secret.json>")
        drive.authorize_local(cfg, args.client_secret)
    elif args.command == "app":
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(cfg.path("app/Home.py"))])
    return 0
