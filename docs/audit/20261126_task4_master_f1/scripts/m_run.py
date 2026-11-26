"""D-156: run rolling-origin semua kandidat yang dideklarasikan di PROTOKOL.md (hanya origin pengembangan).

Satu pekerjaan = (horizon, origin); split resmi `split_origin` (latih t + h ≤ origin) dari `fam.parquet` (tabel resmi + keluarga baru).
Checkpoint per pekerjaan di EXP/d156/<STAGE>/h<h>_<origin>.parquet (dilewati bila ada). Env: STAGE=main|combo, NJ, OMP_NUM_THREADS.
Konfigurasi learner tetap (tanpa pencarian); lihat LEARNERS.
"""
import os
import time

from c_feats import FAMILIES, fam_cols
from m_common import EXP, H, cfg, dev_origins, np, pd, table
from kagami.features.forecast import split_origin
from kagami.models.direction import TUNED_HGB, tuned_columns
from kagami.models.forecasting import _codes
from kagami.features.price_dynamics import GROUPS, SELECTED_GROUPS, group_columns

CATS = ["commodity", "region"]
SEED = cfg.seed
REMOVE = list(SELECTED_GROUPS)                     # hapus-satu kelompok C1t (seleksi fitur)


def variants(h, stage):
    base = tuned_columns("C1t", h)[0]
    V = {"base": {"cols": base}}
    if stage == "combo":
        sel = [f for f in os.environ["COMBO_FAMS"].split(",") if f]
        extra = [c for f in sel for c in fam_cols(f, h) if c not in base]
        return {"base": V["base"], "C_COMBO": {"cols": base + extra}}
    for f in FAMILIES:
        V[f"C_{f}"] = {"cols": base + [c for c in fam_cols(f, h) if c not in base]}
    for g in REMOVE:
        drop = set(group_columns([g], h))
        V[f"C_rm_{g}"] = {"cols": [c for c in base if c not in drop]}
    V["D_cw"] = {"cols": base, "class_weight": "balanced"}
    V["D_seed5"] = {"cols": base, "seeds": [SEED + k for k in range(5)]}
    V["B_recency"] = {"cols": base, "halflife_weeks": 104}
    V["B_win156"] = {"cols": base, "window_weeks": 156}
    for lrn in ("lgb", "xgb", "cat", "et", "lr"):
        V[f"E_{lrn}"] = {"cols": base, "learner": lrn}
    return V


def _xy(tr, te, cols):
    num = [c for c in cols if tr[c].notna().any()]
    Xtr = np.column_stack([tr[num].astype(float).to_numpy(), _codes(cfg, tr, CATS)])
    Xte = np.column_stack([te[num].astype(float).to_numpy(), _codes(cfg, te, CATS)])
    return num, Xtr, Xte


def _onehot_impute(Xtr, Xte, n_num):
    """Untuk ET/LR: imputasi median latih + indikator hilang pada numerik, one-hot kategori (kode tetap)."""
    from sklearn.impute import SimpleImputer
    imp = SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)
    A, Ate = imp.fit_transform(Xtr[:, :n_num]), imp.transform(Xte[:, :n_num])
    cat_tr, cat_te = Xtr[:, n_num:], Xte[:, n_num:]
    oh_tr, oh_te = [], []
    for j in range(cat_tr.shape[1]):
        lv = np.unique(cat_tr[:, j][np.isfinite(cat_tr[:, j])])
        oh_tr.append((cat_tr[:, j][:, None] == lv[None, :]).astype(float))
        oh_te.append((cat_te[:, j][:, None] == lv[None, :]).astype(float))
    return np.hstack([A] + oh_tr), np.hstack([Ate] + oh_te)


def fit_predict(tr, te, spec, origin):
    up = (tr["y"] > 0).to_numpy()
    num, Xtr, Xte = _xy(tr, te, spec["cols"])
    n = len(num)
    w = None
    if "halflife_weeks" in spec:
        age = (origin - tr["week"]).dt.days.to_numpy() / 7.0
        w = 0.5 ** (age / spec["halflife_weeks"])
    lrn = spec.get("learner", "hgb")
    if lrn == "hgb":
        from sklearn.ensemble import HistGradientBoostingClassifier
        ps = []
        for s in spec.get("seeds", [SEED]):
            m = HistGradientBoostingClassifier(**TUNED_HGB, categorical_features=[False] * n + [True] * len(CATS),
                                               class_weight=spec.get("class_weight"), random_state=s)
            m.fit(Xtr, up, sample_weight=w)
            ps.append(m.predict_proba(Xte)[:, list(m.classes_).index(True)])
        return np.mean(ps, axis=0)
    if lrn == "lgb":
        import lightgbm as lgb
        m = lgb.LGBMClassifier(n_estimators=250, learning_rate=0.0281, num_leaves=23, min_child_samples=319, reg_lambda=3.85,
                               colsample_bytree=0.335, random_state=SEED, n_jobs=2, verbose=-1)
        m.fit(Xtr, up, categorical_feature=list(range(n, n + len(CATS))))
        return m.predict_proba(Xte)[:, 1]
    if lrn == "xgb":
        import xgboost as xgb
        m = xgb.XGBClassifier(n_estimators=250, learning_rate=0.0281, max_leaves=23, grow_policy="lossguide", max_depth=0,
                              min_child_weight=80, reg_lambda=3.85, colsample_bynode=0.335, tree_method="hist", n_jobs=2,
                              random_state=SEED)
        m.fit(Xtr, up)
        return m.predict_proba(Xte)[:, 1]
    if lrn == "cat":
        from catboost import CatBoostClassifier
        def frame(X):
            d = pd.DataFrame(X[:, :n])
            for j in range(len(CATS)):
                d[f"cat{j}"] = pd.Series(X[:, n + j]).fillna(-1).astype(int).astype(str)
            return d
        m = CatBoostClassifier(iterations=500, learning_rate=0.05, depth=6, l2_leaf_reg=3, random_seed=SEED, thread_count=2,
                               verbose=0, allow_writing_files=False)
        m.fit(frame(Xtr), up, cat_features=[f"cat{j}" for j in range(len(CATS))])
        return m.predict_proba(frame(Xte))[:, 1]
    if lrn == "et":
        from sklearn.ensemble import ExtraTreesClassifier
        A, Ate = _onehot_impute(Xtr, Xte, n)
        m = ExtraTreesClassifier(n_estimators=300, min_samples_leaf=50, max_features=0.33, n_jobs=2, random_state=SEED)
        m.fit(A, up)
        return m.predict_proba(Ate)[:, 1]
    if lrn == "lr":
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        A, Ate = _onehot_impute(Xtr, Xte, n)
        sc = StandardScaler().fit(A)
        m = LogisticRegression(C=0.1, max_iter=3000)
        m.fit(sc.transform(A), up)
        return m.predict_proba(sc.transform(Ate))[:, 1]
    raise ValueError(lrn)


def job(h, o, stage):
    path = os.path.join(EXP, "d156", stage, f"h{h}_{o.date()}.parquet")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return path
    train, test = split_origin(cfg, table("fam"), o, h)
    tr = train[np.isfinite(train["y"].to_numpy(float)) & (train["y"] != 0)]
    out = []
    for name, spec in variants(h, stage).items():
        t0 = time.perf_counter()
        trv = tr[tr["week"] >= o - pd.Timedelta(weeks=spec["window_weeks"])] if "window_weeks" in spec else tr
        p = fit_predict(trv, test, spec, o)
        out.append(test[["province_id", "commodity"]].assign(origin=o, horizon=h, variant=name, y_true=test["y"].to_numpy(),
                                                             score=p, n_train=len(trv), n_cols=len(spec["cols"]),
                                                             sec=time.perf_counter() - t0))
    pd.concat(out, ignore_index=True).to_parquet(path)
    return path


if __name__ == "__main__":
    from joblib import Parallel, delayed
    stage = os.environ.get("STAGE", "main")
    os.makedirs(os.path.join(EXP, "d156", stage), exist_ok=True)
    jobs = [(h, o) for h in H for o in dev_origins(h)]
    print(stage, "pekerjaan", len(jobs), "varian", list(variants(4, stage)), flush=True)
    t0 = time.time()
    Parallel(n_jobs=int(os.environ.get("NJ", 6)), verbose=5)(delayed(job)(h, o, stage) for h, o in jobs)
    print("selesai", round(time.time() - t0), "dtk", flush=True)
