"""Validasi prospektif — pemeriksaan integritas BACA-SAJA prediksi maju beku (D-152, D-158, D-164) dan evaluatornya.

Dijalankan sebelum SETIAP evaluasi maju (FORWARD_VALIDATION_PROTOCOL.md §3 langkah 1). Tidak membaca target, tidak menulis ke
folder prediksi, hanya memakai perintah git baca-saja (`ls-files`, `diff --quiet`, `show`, `log`).

Pemakaian (dari root project):  python docs/audit/20261127_prospective_validation/scripts/integrity_check.py
Keluaran: hasil/integrity_<YYYY-MM-DD>.json + ringkasan di layar; kode keluar 1 bila ada pemeriksaan WAJIB yang gagal.
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(HERE, "..", "hasil")
A = "docs/audit/"

FAMILIES = {
    "D-152": {"preds": A + "20261125_iw_validasi/hasil/forward_preds.csv",
              "manifest": A + "20261125_iw_validasi/hasil/forward_manifest.json", "sha_key": "forward_preds_sha256"},
    "D-158": {"preds": A + "20261126_nasional_lokal/hasil/forward_preds_d158.csv",
              "manifest": A + "20261126_nasional_lokal/hasil/forward_manifest_d158.json", "sha_key": "forward_preds_sha256"},
    "D-164": {"preds": A + "20261126_k4_risiko_material/hasil/k4_forward_preds.csv",
              "manifest": A + "20261126_k4_risiko_material/hasil/k4_forward_manifest.json", "sha_key": "sha256"},
}
# evaluator → (berkas hash beku, kunci); None = belum ada hash beku (hanya dibandingkan dengan git HEAD)
EVALUATORS = {
    A + "20261125_iw_validasi/scripts/fw_eval.py": ("manifest:D-152", A + "20261125_iw_validasi/scripts/fw_eval.py"),
    A + "jalur_a_macro_f1/scripts/a_forward_eval.py": ("sha256txt", A + "jalur_a_macro_f1/hasil/a_protocol_sha256.txt"),
    A + "jalur_a_macro_f1/scripts/fw_common.py": ("sha256txt", A + "jalur_a_macro_f1/hasil/a_protocol_sha256.txt"),
    A + "20261126_k4_risiko_material/scripts/k4_eval.py": (None, None),
    A + "20261126_k4_risiko_material/scripts/k4_freeze.py": (None, None),
    A + "20261126_k4_risiko_material/scripts/k4_common.py": ("sha256txt_k4", A + "20261126_k4_risiko_material/hasil/protocol_sha256.txt"),
    A + "20261127_prospective_validation/scripts/k4_forward_eval.py": ("sha256txt", A + "20261127_prospective_validation/hasil/pv_protocol_sha256.txt"),
    A + "20261127_prospective_validation/FORWARD_VALIDATION_PROTOCOL.md": ("sha256txt", A + "20261127_prospective_validation/hasil/pv_protocol_sha256.txt"),
}


def sha_file(rel):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, rel), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args, binary=False):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    return r.returncode, (r.stdout if binary else r.stdout.decode("utf-8", "replace").strip())


def git_state(rel):
    tracked = git("ls-files", "--error-unmatch", rel)[0] == 0
    clean = tracked and git("diff", "--quiet", "HEAD", "--", rel)[0] == 0
    code, blob = git("show", f"HEAD:{rel}", binary=True)
    head_sha = hashlib.sha256(blob).hexdigest() if code == 0 else None
    # blob git disimpan LF (core.autocrlf); berkas beku D-152/D-158 ditulis CRLF oleh pandas di Windows → bandingkan juga versi CRLF
    head_crlf = hashlib.sha256(blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest() if code == 0 else None
    last = git("log", "-1", "--format=%h %ad", "--date=iso", "--", rel)[1] or None
    eol = git("ls-files", "--eol", rel)[1]
    return {"tracked": tracked, "clean_vs_head": clean, "head_sha256": head_sha, "head_sha256_as_crlf": head_crlf,
            "eol": " ".join(eol.split()[:2]) if eol else None, "last_commit": last}


def sha_from_txt(txt_rel, target_rel, strip_prefix=""):
    for line in open(os.path.join(ROOT, txt_rel), encoding="utf-8"):
        parts = line.strip().split(" *")
        if len(parts) == 2 and (strip_prefix + parts[1]) == target_rel:
            return parts[0]
    return None


def main():
    rep = {"checked_at": datetime.now().astimezone().isoformat(timespec="seconds"), "families": {}, "evaluators": {}, "failures": []}
    for fam, f in FAMILIES.items():
        man = json.load(open(os.path.join(ROOT, f["manifest"]), encoding="utf-8"))
        now = sha_file(f["preds"])
        gp, gm = git_state(f["preds"]), git_state(f["manifest"])
        r = {"sha256_manifest": man[f["sha_key"]], "sha256_now": now, "sha256_ok": now == man[f["sha_key"]],
             "n_rows_manifest": man["n_rows"], "preds_git": gp, "manifest_git": gm,
             "head_equals_frozen": man[f["sha_key"]] in (gp["head_sha256"], gp["head_sha256_as_crlf"]),
             "frozen_bytes_are_crlf": gp["head_sha256"] != man[f["sha_key"]] and gp["head_sha256_as_crlf"] == man[f["sha_key"]]}
        rep["families"][fam] = r
        if r["frozen_bytes_are_crlf"]:
            rep.setdefault("warnings", []).append(
                f"{fam}: sha256 beku = berkas CRLF; blob git LF → verifikasi byte hanya cocok pada checkout dengan core.autocrlf=true")
        if not r["sha256_ok"]:
            rep["failures"].append(f"{fam}: sha256 prediksi ≠ manifest")
        if not (r["head_equals_frozen"] and gp["clean_vs_head"] and gm["tracked"] and gm["clean_vs_head"]):
            rep["failures"].append(f"{fam}: versi beku (prediksi + manifest) belum di-commit apa adanya")
    d152 = json.load(open(os.path.join(ROOT, FAMILIES["D-152"]["manifest"]), encoding="utf-8"))
    for ev, (kind, ref) in EVALUATORS.items():
        now = sha_file(ev)
        if kind == "manifest:D-152":
            frozen = d152["code_sha256"].get(ref)
        elif kind == "sha256txt":
            frozen = sha_from_txt(ref, ev)
        elif kind == "sha256txt_k4":
            frozen = sha_from_txt(ref, ev, strip_prefix=A + "20261126_k4_risiko_material/")
        else:
            frozen = None
        g = git_state(ev)
        raw = open(os.path.join(ROOT, ev), "rb").read().replace(b"\r\n", b"\n")
        variants = {now, hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()}
        r = {"sha256_now": now, "sha256_frozen": frozen, "frozen_ok": (frozen in variants) if frozen else None,
             "frozen_byte_exact": (now == frozen) if frozen else None, "git": g}
        rep["evaluators"][ev] = r
        if frozen and not r["frozen_ok"]:
            rep["failures"].append(f"{ev}: berubah sejak dibekukan")
        if frozen and not g["clean_vs_head"]:
            rep["failures"].append(f"{ev}: versi beku belum di-commit (bukti waktu pra-target)")
    pv = A + "20261127_prospective_validation/hasil/pv_protocol_sha256.txt"
    if not git_state(pv)["clean_vs_head"]:
        rep["failures"].append(f"{pv}: berkas hash beku belum di-commit")
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"integrity_{datetime.now().date()}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    for fam, r in rep["families"].items():
        print(f"{fam}: sha_ok={r['sha256_ok']} head=frozen={r['head_equals_frozen']} manifest_tracked={r['manifest_git']['tracked']}")
    for ev, r in rep["evaluators"].items():
        print(f"{os.path.basename(ev)}: frozen_ok={r['frozen_ok']} clean_vs_head={r['git']['clean_vs_head']}")
    for w in rep.get("warnings", []):
        print("PERINGATAN:", w)
    print("GAGAL:" if rep["failures"] else "semua pemeriksaan wajib lolos", *rep["failures"], sep="\n  ")
    print("→", os.path.relpath(path, ROOT))
    sys.exit(1 if rep["failures"] else 0)


if __name__ == "__main__":
    main()
