"""Dev: HGB (C1t) vs LightGBM vs XGBoost vs ensemble rata-rata; spesialis kelompok komoditas; model 'berubah?' untuk dua tahap."""
import os, sys, json; sys.path.insert(0, r"<EXP_DIR>")
os.environ["KAGAMI_EXT"] = "ext2.parquet"
from engine import *
from feats import cols_for
from exp2 import run_spec, three_class
import evalx
SEL = ["lag", "rmean", "rstd", "mom", "season", "dev", "comm"]
P = {k: v for k, v in json.load(open(r"<EXP_DIR>/best_C1t.json"))["best"]["params"].items() if k not in ("balanced", "decay_years")}
out = {}
for h in (4, 8):
    cols = BASE + cols_for(SEL, h)
    cols_chg = cols + cols_for(["cf", "vol"], h)                 # tahap 1 'berubah?': + umur carry-forward & volatilitas
    spec = {"hgb": ("hgb", cols, CATS, P, "up", None), "lgb": ("lgb", cols, CATS, {}, "up", None),
            "xgb": ("xgb", cols, CATS, {}, "up", None), "hgb_spec": ("hgb", cols, CATS, P, "up", "grp"),
            "chg": ("hgb", cols_chg, CATS, P, "change", None)}
    with Timer() as t:
        r = run_spec(h, origin_list(h, "all"), spec, n_jobs=6)
    r["ens"] = r[["hgb", "lgb", "xgb"]].mean(axis=1)
    r.to_parquet(fr"<EXP_DIR>/preds/models2_h{h}.parquet")
    dev = r[r.origin.isin(origin_list(h, "dev"))]
    res = {m: macro_f1(dev.y_true, dev[m]) for m in ["hgb", "lgb", "xgb", "ens", "hgb_spec"]}
    for m in ["lgb", "xgb", "ens", "hgb_spec"]:
        d = evalx.paired_diff(dev.rename(columns={m: "score"}), dev.rename(columns={"hgb": "score"}), 0.5, 0.5, h)
        res[f"{m}-hgb"] = [round(d["diff"], 4), round(d["lo"], 4), round(d["hi"], 4), round(d["p"], 4)]
    # dua tahap pada dev: tau dipilih di dev
    taus = np.round(np.arange(0.30, 0.91, 0.01), 2)
    sc = [three_class(dev.y_true.to_numpy(), dev.chg.to_numpy(), dev.hgb.to_numpy(), tau)[0] for tau in taus]
    i = int(np.argmax(sc))
    res["three_class_dev"] = {"tau": float(taus[i]), "macro_f1_3": sc[i], "per_class": three_class(dev.y_true.to_numpy(), dev.chg.to_numpy(), dev.hgb.to_numpy(), taus[i])[1],
                              "share_flat_true": float((dev.y_true == 0).mean())}
    res["sec"] = round(t.s)
    out[h] = res
    print(h, json.dumps(res), flush=True)
json.dump(out, open(r"<EXP_DIR>/models2_dev.json", "w"), indent=1)
