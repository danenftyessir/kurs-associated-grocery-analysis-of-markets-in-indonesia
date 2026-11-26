"""Jalur A Workstream A: audit prediksi maju beku D-152 (C1-tuned, IW_NAT) & D-158 (C1-tuned, FR_REF, FR_CITY). Baca-saja.

Memeriksa: sha256 prediksi vs manifest, waktu beku, hash kode sekarang vs manifest, status git (baca-saja: ls-files & log), isi
(jumlah baris, origin, seri, rentang p, NaN), kesamaan base antar pembekuan, kedekatan kandidat (korelasi, kesepakatan arah),
ketersediaan target pada snapshot sekarang, dan jadwal evaluasi (Jumat minggu origin + h).
→ hasil/a_forward_audit.json, hasil/a_forward_schedule.csv
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fw_common import FROZEN, OUT, ROOT, load_frozen, np, pd, sha256, target_ready  # noqa: E402


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # pragma: no cover
        return f"ERR {e}"


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rep = {"checked_at": pd.Timestamp.now(tz="Asia/Jakarta").isoformat(), "sources": {}}
    for src, f in FROZEN.items():
        man = json.load(open(f["manifest"], encoding="utf-8"))
        rel = os.path.relpath(f["preds"], ROOT).replace("\\", "/")
        relm = os.path.relpath(f["manifest"], ROOT).replace("\\", "/")
        code_now = {}
        for p, hsh in man["code_sha256"].items():
            fp = os.path.join(ROOT, p)
            code_now[p] = "sama" if os.path.exists(fp) and sha256(fp) == hsh else ("hilang" if not os.path.exists(fp) else "berubah")
        tracked = git("ls-files", "--error-unmatch", rel)
        rep["sources"][src] = {
            "preds": rel, "frozen_at_utc": man["frozen_at_utc"], "sha256_manifest": man["forward_preds_sha256"],
            "sha256_now": sha256(f["preds"]), "sha256_ok": sha256(f["preds"]) == man["forward_preds_sha256"],
            "n_rows_manifest": man["n_rows"], "code_vs_manifest": code_now,
            "git_tracked_preds": bool(tracked) and not tracked.startswith("error"),
            "git_tracked_manifest": bool(git("ls-files", relm)),
            "git_first_commit": git("log", "--diff-filter=A", "--format=%h %cI", "--", rel) or None,
            "pihps_zip_sha256": man["data"]["pihps_zip_sha256"],
        }
    d = load_frozen(verify=True)
    rep["rows"] = d.groupby(["horizon", "model"]).size().rename("n").reset_index().to_dict("records")
    rep["n_series"] = int(d[["province_id", "commodity"]].drop_duplicates().shape[0])
    rep["p_range"] = [float(d["p_up"].min()), float(d["p_up"].max())]
    rep["n_nan_p"] = int(d["p_up"].isna().sum())
    rep["dup_keys"] = int(d.duplicated(["origin", "horizon", "model", "province_id", "commodity"]).sum())
    W = d.pivot_table(index=["origin", "horizon", "province_id", "commodity"], columns="model", values="p_up").reset_index()
    near = []
    for h, g in W.groupby("horizon"):
        for m in ["IW_NAT", "FR_REF", "FR_CITY"]:
            near.append({"horizon": int(h), "model": m, "corr_vs_base": float(g[m].corr(g["base"])),
                         "agree_dir_vs_base": float(((g[m] > 0.5) == (g["base"] > 0.5)).mean()),
                         "share_up_pred": float((g[m] > 0.5).mean())})
        near.append({"horizon": int(h), "model": "FR_REF~IW_NAT", "corr_vs_base": float(g["FR_REF"].corr(g["IW_NAT"])),
                     "agree_dir_vs_base": float(((g["FR_REF"] > 0.5) == (g["IW_NAT"] > 0.5)).mean()), "share_up_pred": np.nan})
        near.append({"horizon": int(h), "model": "base", "corr_vs_base": 1.0, "agree_dir_vs_base": 1.0,
                     "share_up_pred": float((g["base"] > 0.5).mean())})
    rep["closeness"] = near
    # snapshot sekarang & jadwal
    from kagami.utils.config import get_config  # noqa: E402
    cfg = get_config()
    zp = cfg.source_path("pihps")
    rep["pihps_now"] = {"file": os.path.basename(str(zp)), "sha256": sha256(zp)}
    rep["pihps_now"]["same_as_frozen"] = rep["pihps_now"]["sha256"] == rep["sources"]["D-152"]["pihps_zip_sha256"]
    last = pd.Timestamp(json.load(open(FROZEN["D-152"]["manifest"], encoding="utf-8"))["data"]["last_daily_date"])
    sch = d[["origin", "horizon"]].drop_duplicates().sort_values(["horizon", "origin"]).reset_index(drop=True)
    sch["target_week"] = sch["origin"] + pd.to_timedelta(sch["horizon"] * 7, unit="D")
    sch["target_friday"] = sch["target_week"] + pd.Timedelta(days=4)
    sch["ready_on_current_snapshot"] = [bool(target_ready(o, h, last)) for o, h in zip(sch["origin"], sch["horizon"])]
    sch.to_csv(os.path.join(OUT, "a_forward_schedule.csv"), index=False, date_format="%Y-%m-%d")
    rep["snapshot_last_date"] = str(last.date())
    rep["n_targets_ready"] = int(sch["ready_on_current_snapshot"].sum())
    rep["first_target_friday"] = str(sch["target_friday"].min().date())
    rep["all_h4_friday"] = str(sch.loc[sch["horizon"] == 4, "target_friday"].max().date())
    rep["all_h8_friday"] = str(sch.loc[sch["horizon"] == 8, "target_friday"].max().date())
    json.dump(rep, open(os.path.join(OUT, "a_forward_audit.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"}, indent=1, ensure_ascii=False, default=str))
