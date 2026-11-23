"""Local projections dengan lag-augmentation (WP-13). Persamaan: docs/METHODS.md §M1."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.config import Config
from kagami.stats.regression import ols_cluster

# kolom impuls -> nama driver di artefak 'profiles'
IMPULSES = {"de": "e", "dw": "w", "de_pos": "e_pos", "de_neg": "e_neg"}
_META = ("week", "unit", "y", "group")


def _period_weeks(cfg: Config, weeks: pd.Index) -> np.ndarray:
    p = cfg.params["period"]
    return np.asarray((weeks >= pd.Timestamp(p["start"])) & (weeks <= pd.Timestamp(p["freeze"])))


def _lagged(s: pd.Series, name: str, lags: range) -> dict[str, pd.Series]:
    return {(name if l == 0 else f"{name}_l{l}"): s.shift(l) for l in lags}


def _common_controls(drivers: pd.DataFrame) -> pd.DataFrame:
    """Kontrol bersama per minggu (grid penggerak): db lag 0..4, dummy minggu relatif Idulfitri, dummy bulan (2..12)."""
    d = drivers.sort_values("week").set_index("week")
    cols = {f"db_l{l}": d["db"].shift(l) for l in range(0, 5)}
    idf = d["idf_rel_week"]
    for k in sorted(idf.dropna().unique()):
        cols[f"idf_{'m' if k < 0 else 'p'}{abs(int(k))}"] = (idf == k).astype(float)
    month = d.index.month
    for m in range(2, 13):
        cols[f"month_{m}"] = pd.Series((month == m).astype(float), index=d.index)
    return pd.DataFrame(cols, index=d.index)


def _fx_block(drivers: pd.DataFrame, world: pd.DataFrame | None, commodity: str, lags: int,
              asymmetric: bool) -> pd.DataFrame:
    d = drivers.sort_values("week").set_index("week")
    cols: dict[str, pd.Series] = {}
    impulses = ("de_pos", "de_neg") if asymmetric else ("de",)
    for name in impulses:
        cols.update(_lagged(d[name], name, range(0, lags + 1)))
    if world is not None and len(world) and commodity in set(world["commodity"]):
        dw = world.loc[world["commodity"] == commodity].set_index("week")["dw"].sort_index()
        dw = dw.reindex(d.index)
        cols.update(_lagged(dw, "dw", range(0, lags + 1)))
    return pd.DataFrame(cols, index=d.index)


def _detect(panel: pd.DataFrame, given: str | None, options: tuple[str, ...], what: str) -> str:
    if given is not None:
        return given
    for c in options:
        if c in panel.columns:
            return c
    raise KeyError(f"kolom {what} tidak ditemukan (coba salah satu {options})")


def build_design(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None,
                 commodity: str, horizon: int, lags: int, asymmetric: bool = False, *,
                 elig: pd.DataFrame | None = None, unit_col: str | None = None,
                 price_col: str | None = None) -> pd.DataFrame:
    """WP-13. Susun y^{(h)} = p_{t+h} - p_{t-1} dan regresor untuk satu komoditas & horizon (METHODS §M1.1).

    panel   : baris (week, <unit>, commodity, <log harga>) pada grid mingguan; unit = province_id | region | unit
              (deteksi otomatis atau `unit_col`), log harga = log_price | log_price_index | dev (atau `price_col`).
    elig    : bila diberikan, hanya seri (province_id, commodity) eligible yang dipakai.
    Regresor (konvensi nama -- dipakai power.compute_mde):
      blok kurs  : de, de_l1..de_lL (asymmetric: de_pos, de_neg + lag masing-masing); dw, dw_l1..dw_lL bila
                   komoditas punya padanan di `world`. Semua kolom blok kurs berawalan 'de' atau 'dw'.
      kontrol    : dp_l1..dp_lL (lag Δp seri), db_l0..db_l4, idf_m6..idf_p4 (minggu relatif Idulfitri),
                   month_2..month_12.
    Sampel: minggu period.start..period.freeze; baris dengan y atau regresor NaN dibuang (jumlahnya di
    attrs['n_dropped']). Efek tetap seri α_{i,r,h} via within-transform per unit SETELAH pembuangan baris.
    Keluaran: week, unit, y, regresor..., group (= week, untuk cluster). attrs: n_dropped, n_weeks, commodity, horizon.
    """
    parts = _design_parts(cfg, panel, drivers, world, commodity, lags, asymmetric, elig, unit_col, price_col)
    y, X, names, wk, un, n_dropped = _design_arrays(parts, horizon)
    weeks = parts["weeks"][wk]
    df = pd.DataFrame({"week": weeks, "unit": parts["units"].to_numpy()[un], "y": y})
    df = pd.concat([df, pd.DataFrame(X, columns=names)], axis=1)
    df["group"] = df["week"]
    df.attrs.update(n_dropped=n_dropped, n_weeks=int(len(np.unique(wk))), commodity=commodity, horizon=horizon)
    return df


def _design_parts(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None,
                  commodity: str, lags: int, asymmetric: bool, elig: pd.DataFrame | None,
                  unit_col: str | None, price_col: str | None) -> dict:
    """Bagian desain yang TIDAK bergantung pada horizon: matriks log harga minggu x unit, Δp, blok kurs & kontrol.

    Dipakai build_design (satu horizon) dan national_profiles (semua horizon tanpa membangun ulang; D-118)."""
    unit_col = _detect(panel, unit_col, ("province_id", "region", "unit"), "unit")
    price_col = _detect(panel, price_col, ("log_price", "log_price_index", "dev"), "log harga")
    p = panel.loc[panel["commodity"] == commodity, ["week", unit_col, "commodity", price_col]]
    if elig is not None:
        ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
        p = p.merge(ok, left_on=[unit_col, "commodity"], right_on=["province_id", "commodity"], how="inner")
    P = p.pivot_table(index="week", columns=unit_col, values=price_col, aggfunc="first", dropna=False)
    P = P.reindex(pd.date_range(P.index.min(), P.index.max(), freq="W-MON"))
    P = P.reindex(columns=sorted(P.columns))
    weeks = P.index
    common = pd.concat([_fx_block(drivers, world, commodity, lags, asymmetric), _common_controls(drivers)],
                       axis=1).reindex(weeks)
    fx_cols = [c for c in common.columns if c.startswith(("de", "dw"))]
    ctrl_cols = [c for c in common.columns if c not in fx_cols]
    return {"weeks": weeks, "units": P.columns, "P": P.to_numpy(dtype=float),
            "dP": P.diff().to_numpy(dtype=float), "fx": common[fx_cols].to_numpy(dtype=float),
            "ctrl": common[ctrl_cols].to_numpy(dtype=float), "fx_cols": fx_cols, "ctrl_cols": ctrl_cols,
            "lags": lags, "period": _period_weeks(cfg, weeks)}


def _shift(A: np.ndarray, k: int) -> np.ndarray:
    """Geser baris seperti DataFrame.shift(k) (k > 0 ke bawah, k < 0 ke atas), isi NaN."""
    out = np.full_like(A, np.nan)
    if k > 0:
        out[k:] = A[:-k]
    elif k < 0:
        out[:k] = A[-k:]
    else:
        out[:] = A
    return out


def _design_arrays(parts: dict, horizon: int) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray,
                                                         np.ndarray, int]:
    """Susun y^{(h)} & regresor (urutan: blok kurs, dp_l1..dp_lL, kontrol) dari _design_parts, buang baris NaN
    dalam periode, lalu within-transform per unit. Return (y, X, nama regresor, indeks minggu, indeks unit, n_dropped)."""
    P, L = parts["P"], parts["lags"]
    nW, nU = P.shape
    names = [*parts["fx_cols"], *(f"dp_l{l}" for l in range(1, L + 1)), *parts["ctrl_cols"]]
    if "X" not in parts:                       # regresor tidak bergantung pada horizon -> dibangun sekali
        nf, nc = len(parts["fx_cols"]), len(parts["ctrl_cols"])
        X = np.empty((nW * nU, nf + L + nc))
        X[:, :nf] = np.repeat(parts["fx"], nU, axis=0)
        for l in range(1, L + 1):
            X[:, nf + l - 1] = _shift(parts["dP"], l).ravel()
        X[:, nf + L:] = np.repeat(parts["ctrl"], nU, axis=0)
        in_p = np.repeat(parts["period"], nU)
        parts.update(X=X, in_p=in_p, x_ok=in_p & np.isfinite(X).all(axis=1))
    y = (_shift(P, -horizon) - _shift(P, 1)).ravel()
    keep = parts["x_ok"] & np.isfinite(y)
    n_dropped = int(parts["in_p"].sum() - keep.sum())
    idx = np.flatnonzero(keep)
    y, X, wk, un = y[idx], parts["X"][idx], idx // nU, idx % nU
    if len(y):
        cnt = np.bincount(un, minlength=nU).astype(float)
        cnt[cnt == 0] = 1.0
        y = y - (np.bincount(un, weights=y, minlength=nU) / cnt)[un]
        for j in range(X.shape[1]):
            X[:, j] -= (np.bincount(un, weights=X[:, j], minlength=nU) / cnt)[un]
    return y, X, names, wk, un, n_dropped


def regressors(design: pd.DataFrame) -> list[str]:
    """WP-13. Nama kolom regresor sebuah desain (semua kolom selain week, unit, y, group)."""
    return [c for c in design.columns if c not in _META]


def fit_lp(cfg: Config, design: pd.DataFrame) -> pd.DataFrame:
    """WP-13. OLS + SE cluster per minggu (stats.regression.ols_cluster). -> driver, estimate, se, n_weeks.

    Satu baris per kolom impuls yang ada di desain (de -> e, dw -> w, de_pos -> e_pos, de_neg -> e_neg).
    Kolom ekstra: n_obs (baris), n_clusters. Desain tanpa baris -> estimate/se NaN.
    """
    reg = regressors(design)
    imp = [c for c in reg if c in IMPULSES]
    if len(design) == 0:
        return pd.DataFrame({"driver": [IMPULSES[c] for c in imp], "estimate": np.nan, "se": np.nan,
                             "n_weeks": 0, "n_obs": 0, "n_clusters": 0})
    res = ols_cluster(design["y"].to_numpy(), design[reg].to_numpy(dtype=float), design["group"].to_numpy())
    pos = {c: i for i, c in enumerate(reg)}
    return pd.DataFrame({"driver": [IMPULSES[c] for c in imp],
                         "estimate": [res.beta[pos[c]] for c in imp],
                         "se": [res.se[pos[c]] for c in imp],
                         "n_weeks": int(design["week"].nunique()), "n_obs": res.n_obs,
                         "n_clusters": res.n_clusters})


def _fit_arrays(y: np.ndarray, X: np.ndarray, names: list[str], wk: np.ndarray) -> list[tuple]:
    """fit_lp pada larik (cluster = indeks minggu) -> [(driver, estimate, se, n_weeks, n_obs)] per impuls."""
    imp = [c for c in names if c in IMPULSES]
    if len(y) == 0:
        return [(IMPULSES[c], np.nan, np.nan, 0, 0) for c in imp]
    res = ols_cluster(y, X, wk)
    n_weeks = int(len(np.unique(wk)))
    return [(IMPULSES[c], float(res.beta[names.index(c)]), float(res.se[names.index(c)]), n_weeks, res.n_obs)
            for c in imp]


def fx_self_response(cfg: Config, drivers: pd.DataFrame, horizon: int, lags: int) -> float:
    """WP-13. γ(h): respons kumulatif log kurs terhadap de-nya sendiri (LP e_{t+h}-e_{t-1} pada de_t + lag).

    Kontrol sama dengan LP harga tanpa lag Δp & dw: de lag 1..L, db lag 0..4, dummy Idulfitri & bulan, konstanta.
    Sampel minggu period.start..period.freeze (y butuh e_{t+h} teramati). γ(0) = 1 menurut konstruksi.
    Dipakai untuk PT(i,h) = β(i,h)/γ(h) (proposal §5.2a) dan MDE_PT (WP-09).
    """
    d = drivers.sort_values("week").set_index("week")
    y = d["log_e"].shift(-horizon) - d["log_e"].shift(1)
    X = pd.concat([pd.DataFrame(_lagged(d["de"], "de", range(0, lags + 1))), _common_controls(drivers)], axis=1)
    X.insert(0, "const", 1.0)
    m = _period_weeks(cfg, d.index)
    res = ols_cluster(y.to_numpy()[m], X.to_numpy(dtype=float)[m], d.index.to_numpy()[m])
    return float(res.beta[list(X.columns).index("de")])


PROFILE_COLUMNS = ["level", "unit", "commodity", "driver", "horizon", "estimate", "se", "ci_low", "ci_high",
                   "n_weeks", "shrunk"]


def national_profiles(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame,
                      world: pd.DataFrame, *, elig: pd.DataFrame | None = None,
                      horizons: list[int] | None = None, commodities: list[str] | None = None) -> pd.DataFrame:
    """WP-13. Loop komoditas x horizon 0..12 x {simetris, asimetris} -> baris artefak 'profiles' level='national'.

    driver ∈ {e, w, e_pos, e_neg, PT}. ci = estimate ± 1.96·se (interval bootstrap ditambahkan WP-16).
    Panel provinsi pooled (efek tetap seri, SE cluster minggu; METHODS §M1.1), L = params.lp.lags.
    e & w dari spesifikasi simetris; e_pos & e_neg dari spesifikasi asimetris (w tidak diulang).
    PT = β_e(h) / γ(h) (fx_self_response, drivers yang sama -> rasio ikut dihitung ulang di tiap replikasi bootstrap);
    se & ci PT = NaN di sini karena interval PT hanya dari bootstrap (METHODS §M1.2, WP-16).
    elig      : filter seri eligible (disarankan; Task 1 meneruskannya).
    horizons  : default params.lp.horizons (plasebo boleh memakai params.lp.key_horizons).
    commodities: default semua komoditas yang ada di panel (urutan configs/commodities.yaml).
    Kolom ekstra: n_obs.
    """
    L = int(cfg.params["lp"]["lags"])
    H = [int(h) for h in (horizons if horizons is not None else cfg.params["lp"]["horizons"])]
    present = set(panel["commodity"].unique())
    coms = [c for c in (commodities or cfg.commodity_ids()) if c in present]
    gamma = {h: fx_self_response(cfg, drivers, h, L) for h in H}
    fits: dict[tuple[str, int, bool], list[tuple]] = {}
    for com in coms:
        for asym in (False, True):
            parts = _design_parts(cfg, panel, drivers, world, com, L, asym, elig, None, None)  # sekali per spesifikasi
            for h in H:
                y, X, names, wk, _, _ = _design_arrays(parts, h)
                fits[(com, h, asym)] = _fit_arrays(y, X, names, wk)
    rows = []
    for com in coms:
        for h in H:
            for asym in (False, True):
                for drv, est, se, n_weeks, n_obs in fits[(com, h, asym)]:
                    if asym and drv == "w":
                        continue
                    rows.append({"commodity": com, "driver": drv, "horizon": h, "estimate": est,
                                 "se": se, "n_weeks": n_weeks, "n_obs": n_obs})
                    if drv == "e":
                        rows.append({"commodity": com, "driver": "PT", "horizon": h,
                                     "estimate": est / gamma[h], "se": np.nan,
                                     "n_weeks": n_weeks, "n_obs": n_obs})
    out = pd.DataFrame(rows, columns=["commodity", "driver", "horizon", "estimate", "se", "n_weeks", "n_obs"])
    out.insert(0, "unit", "ALL")
    out.insert(0, "level", "national")
    out["ci_low"] = out["estimate"] - 1.96 * out["se"]
    out["ci_high"] = out["estimate"] + 1.96 * out["se"]
    out["shrunk"] = False
    return out[PROFILE_COLUMNS + ["n_obs"]]


ASYMMETRY_COLUMNS = ["commodity", "horizon", "beta_pos", "beta_neg", "estimate", "se", "n_weeks", "n_obs"]


def asymmetry_wald(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame | None, *,
                   elig: pd.DataFrame | None = None, horizons: list[int] | None = None,
                   commodities: list[str] | None = None) -> pd.DataFrame:
    """WP-13 (H2). Uji Wald β⁺(h) = β⁻(h) nasional dengan SE cluster minggu (PREREGISTRATION H2; D-125).

    Spesifikasi asimetris yang sama dengan national_profiles (panel provinsi pooled, efek tetap seri, L = params.lp.lags).
    Parametrisasi ulang β⁺·de⁺ + β⁻·de⁻ = β⁻·de + (β⁺ − β⁻)·de⁺ (lag de⁺/de⁻ tetap bebas): satu OLS memberi
    estimate = β⁺ − β⁻ (koefisien de⁺; tanda sama dengan fitur A8) dan SE cluster CR1-nya = SE uji Wald satu restriksi.
    horizons default params.lp.key_horizons. Kolom: ASYMMETRY_COLUMNS (beta_pos/beta_neg = estimasi spesifikasi asimetris).
    """
    L = int(cfg.params["lp"]["lags"])
    H = [int(h) for h in (horizons if horizons is not None else cfg.params["lp"]["key_horizons"])]
    present = set(panel["commodity"].unique())
    rows = []
    for com in [c for c in (commodities or cfg.commodity_ids()) if c in present]:
        parts = _design_parts(cfg, panel, drivers, world, com, L, True, elig, None, None)
        for h in H:
            y, X, names, wk, _, _ = _design_arrays(parts, h)
            row = {"commodity": com, "horizon": h, "beta_pos": np.nan, "beta_neg": np.nan, "estimate": np.nan,
                   "se": np.nan, "n_weeks": int(len(np.unique(wk))), "n_obs": int(len(y))}
            if len(y):
                i_pos, i_neg = names.index("de_pos"), names.index("de_neg")
                X = X.copy()
                X[:, i_neg] = X[:, i_pos] + X[:, i_neg]          # kolom de⁻ -> de = de⁺ + de⁻
                res = ols_cluster(y, X, wk)
                diff, b_neg = float(res.beta[i_pos]), float(res.beta[i_neg])
                row.update(beta_pos=b_neg + diff, beta_neg=b_neg, estimate=diff, se=float(res.se[i_pos]),
                           n_obs=int(res.n_obs))
            rows.append(row)
    return pd.DataFrame(rows, columns=ASYMMETRY_COLUMNS)
