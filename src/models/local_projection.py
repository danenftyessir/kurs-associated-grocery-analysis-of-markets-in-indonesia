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
    unit_col = _detect(panel, unit_col, ("province_id", "region", "unit"), "unit")
    price_col = _detect(panel, price_col, ("log_price", "log_price_index", "dev"), "log harga")
    p = panel.loc[panel["commodity"] == commodity, ["week", unit_col, "commodity", price_col]]
    if elig is not None:
        ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
        p = p.merge(ok, left_on=[unit_col, "commodity"], right_on=["province_id", "commodity"], how="inner")
    P = p.pivot_table(index="week", columns=unit_col, values=price_col, aggfunc="first", dropna=False)
    P = P.reindex(pd.date_range(P.index.min(), P.index.max(), freq="W-MON"))
    P = P.reindex(columns=sorted(P.columns))
    weeks, units = P.index, P.columns
    Y = P.shift(-horizon) - P.shift(1)
    dP = P.diff()

    common = pd.concat([_fx_block(drivers, world, commodity, lags, asymmetric), _common_controls(drivers)],
                       axis=1).reindex(weeks)
    nW, nU = len(weeks), len(units)
    data: dict[str, np.ndarray] = {
        "week": np.repeat(weeks.to_numpy(), nU),
        "unit": np.tile(units.to_numpy(), nW),
        "y": Y.to_numpy().ravel(),
    }
    fx_cols = [c for c in common.columns if c.startswith(("de", "dw"))]
    for c in fx_cols:
        data[c] = np.repeat(common[c].to_numpy(dtype=float), nU)
    for l in range(1, lags + 1):
        data[f"dp_l{l}"] = dP.shift(l).to_numpy().ravel()
    for c in common.columns:
        if c not in fx_cols:
            data[c] = np.repeat(common[c].to_numpy(dtype=float), nU)
    df = pd.DataFrame(data)
    df = df[np.repeat(_period_weeks(cfg, weeks), nU)]
    reg = [c for c in df.columns if c not in _META]
    keep = df[["y", *reg]].notna().all(axis=1)
    n_dropped = int((~keep).sum())
    df = df[keep].reset_index(drop=True)
    num = ["y", *reg]
    df[num] = df[num] - df.groupby("unit")[num].transform("mean")
    df["group"] = df["week"]
    df.attrs.update(n_dropped=n_dropped, n_weeks=int(df["week"].nunique()), commodity=commodity, horizon=horizon)
    return df[["week", "unit", "y", *reg, "group"]]


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
    rows = []
    for com in coms:
        for h in H:
            for asym in (False, True):
                fit = fit_lp(cfg, build_design(cfg, panel, drivers, world, com, h, L, asym, elig=elig))
                if asym:
                    fit = fit[fit["driver"] != "w"]
                for r in fit.itertuples(index=False):
                    rows.append({"commodity": com, "driver": r.driver, "horizon": h, "estimate": r.estimate,
                                 "se": r.se, "n_weeks": r.n_weeks, "n_obs": r.n_obs})
                    if r.driver == "e":
                        rows.append({"commodity": com, "driver": "PT", "horizon": h,
                                     "estimate": r.estimate / gamma[h], "se": np.nan,
                                     "n_weeks": r.n_weeks, "n_obs": r.n_obs})
    out = pd.DataFrame(rows, columns=["commodity", "driver", "horizon", "estimate", "se", "n_weeks", "n_obs"])
    out.insert(0, "unit", "ALL")
    out.insert(0, "level", "national")
    out["ci_low"] = out["estimate"] - 1.96 * out["se"]
    out["ci_high"] = out["estimate"] + 1.96 * out["se"]
    out["shrunk"] = False
    return out[PROFILE_COLUMNS + ["n_obs"]]
