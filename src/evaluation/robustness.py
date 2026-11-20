"""Robustness Tier 1/2 dan validasi V2-V4 (WP-28, WP-29, WP-30). docs/METHODS.md §M5.

Tier 1 TIDAK BOLEH dipotong (D-014). Semua keluaran -> artefak 'robustness'.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.models import local_projection as lp
from kagami.stats.regression import ols_cluster
from kagami.utils.config import Config
from kagami.utils.todo import todo

TIER1 = (
    "horizon_8_vs_12",
    "lags_2_4_8",
    "subperiod_pre_post_2021-04-05",      # juga V3
    "exclude_covid_and_extreme_brent",
    "fx_decomposition_global_dollar_vs_idr_specific",
    "monthly_frequency",
)
TIER2 = (
    "alternative_variants",               # termasuk Minyak Goreng Curah (D-023)
    "last_observation_aggregation",
    "alternative_exposure_remoteness",
    "bapanas_outcome",
)

ROBUSTNESS_COLUMNS = ["check_id", "tier", "commodity", "horizon", "estimate", "ci_low", "ci_high",
                      "baseline_estimate", "note"]
_EXTRA = ["driver", "variant", "se", "baseline_se", "baseline_in_ci", "n_weeks", "n_obs"]
_WEEKS_PER_MONTH = 52 / 12   # konversi kalender (struktural), bukan parameter analisis


# --------------------------------------------------------------------------------------------- sampel
def _window_ok(weeks: pd.Series, lags: int, horizon: int, excluded: list[tuple[pd.Timestamp, pd.Timestamp]]
               ) -> np.ndarray:
    """True bila jendela data observasi minggu t, yaitu hari [t-(L+1) minggu, t+h minggu+6 hari]
    (p_{t-1}, lag Δp & lag penggerak s.d. p_{t+h}), tidak beririsan dengan satu pun interval `excluded`."""
    t = pd.DatetimeIndex(weeks)
    start = t - pd.Timedelta(weeks=lags + 1)
    end = t + pd.Timedelta(weeks=horizon) + pd.Timedelta(days=6)
    ok = np.ones(len(t), dtype=bool)
    for a, b in excluded:
        ok &= ~((start <= b) & (end >= a))
    return ok


def _restrict(design: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    """Batasi desain LP ke sub-sampel lalu ulang within-transform per unit.

    Desain sudah di-demean pada sampel penuh; demean ulang pada sub-sampel = demean data asli pada sub-sampel
    (transformasi linear), jadi efek tetap seri tetap tepat tanpa membangun ulang desain."""
    d = design.loc[np.asarray(mask)].copy()
    num = ["y", *lp.regressors(d)]
    d[num] = d[num] - d.groupby("unit")[num].transform("mean")
    d.attrs.update(design.attrs, n_weeks=int(d["week"].nunique()))
    return d.reset_index(drop=True)


def _brent_extreme_months(cfg: Config, drivers: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Bulan kalender dengan |Δ log rerata bulanan Brent| > params.calendar.exclusions.brent_extreme_abs_monthly_logchg."""
    thr = float(cfg.params["calendar"]["exclusions"]["brent_extreme_abs_monthly_logchg"])
    d = drivers.dropna(subset=["log_brent"])
    m = d.groupby(d["week"].dt.to_period("M"))["log_brent"].apply(lambda s: np.log(np.exp(s).mean()))
    chg = m.diff().abs()
    return [(p.start_time, p.end_time.normalize()) for p in chg.index[chg > thr]]


def fx_decomposition(cfg: Config, drivers: pd.DataFrame) -> pd.DataFrame:
    """WP-28. de = a + b·d_dxy + ε pada minggu period.start..freeze (METHODS §M5).

    Return drivers + kolom de_global (= a + b·d_dxy, komponen dolar global) dan de_idr (= ε, spesifik rupiah);
    NaN bila de atau d_dxy kosong. attrs: a, b, r2.
    """
    d = drivers.sort_values("week").reset_index(drop=True).copy()
    p = cfg.params["period"]
    in_p = (d["week"] >= pd.Timestamp(p["start"])) & (d["week"] <= pd.Timestamp(p["freeze"]))
    ok = in_p & d["de"].notna() & d["d_dxy"].notna()
    X = np.column_stack([np.ones(int(ok.sum())), d.loc[ok, "d_dxy"].to_numpy(float)])
    a, b = np.linalg.lstsq(X, d.loc[ok, "de"].to_numpy(float), rcond=None)[0]
    d["de_global"] = a + b * d["d_dxy"]
    d["de_idr"] = d["de"] - d["de_global"]
    r2 = 1 - d.loc[ok, "de_idr"].var() / d.loc[ok, "de"].var()
    d.attrs.update(a=float(a), b=float(b), r2=float(r2))
    return d


# --------------------------------------------------------------------------------------- frekuensi bulanan
def _monthly_design(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                    commodity: str, h_m: int, L_m: int, elig: pd.DataFrame | None) -> pd.DataFrame:
    """Desain LP bulanan: log harga = rerata log mingguan per bulan kalender (label Senin); e, w, b = rerata bulanan.

    y = p_{m+h} - p_{m-1}; regresor de, dw (lag 0..L), dp lag 1..L, db lag 0..L, porsi minggu relatif Idulfitri
    (rerata bulanan dummy mingguan), dummy bulan 2..12. Within per seri, cluster per bulan (kolom group)."""
    p = panel.loc[panel["commodity"] == commodity, ["week", "province_id", "commodity", "log_price"]]
    if elig is not None:
        ok = elig.loc[elig["eligible"].astype(bool), ["province_id", "commodity"]]
        p = p.merge(ok, on=["province_id", "commodity"], how="inner")
    p = p.assign(mon=p["week"].dt.to_period("M"))
    P = p.pivot_table(index="mon", columns="province_id", values="log_price", aggfunc="mean")
    months = pd.period_range(P.index.min(), P.index.max(), freq="M")
    P = P.reindex(months)
    Y = P.shift(-h_m) - P.shift(1)
    dP = P.diff()

    d = drivers.sort_values("week").copy()
    d["mon"] = d["week"].dt.to_period("M")
    ctrl = lp._common_controls(drivers)
    idf_cols = [c for c in ctrl.columns if c.startswith("idf_")]
    idf = ctrl[idf_cols].groupby(ctrl.index.to_period("M")).mean()
    g = d.groupby("mon")
    e = g["log_e"].mean()
    b = g["log_brent"].apply(lambda s: np.log(np.exp(s.dropna()).mean()) if s.notna().any() else np.nan)
    com: dict[str, pd.Series] = {}
    for l in range(L_m + 1):
        com[f"de" if l == 0 else f"de_l{l}"] = e.diff().shift(l)
    if commodity in set(world["commodity"]):
        wc = world.loc[world["commodity"] == commodity]
        w = wc.groupby(wc["week"].dt.to_period("M"))["log_w_idr"].mean()
        for l in range(L_m + 1):
            com["dw" if l == 0 else f"dw_l{l}"] = w.diff().shift(l)
    for l in range(L_m + 1):
        com[f"db_l{l}"] = b.diff().shift(l)
    C = pd.DataFrame(com).join(idf, how="left")
    for m in range(2, 13):
        C[f"month_{m}"] = (C.index.month == m).astype(float)
    C = C.reindex(months)

    nM, nU = len(months), P.shape[1]
    data = {"week": np.repeat(months.to_timestamp().to_numpy(), nU), "unit": np.tile(P.columns.to_numpy(), nM),
            "y": Y.to_numpy().ravel()}
    for c in [c for c in C.columns if c.startswith(("de", "dw"))]:
        data[c] = np.repeat(C[c].to_numpy(float), nU)
    for l in range(1, L_m + 1):
        data[f"dp_l{l}"] = dP.shift(l).to_numpy().ravel()
    for c in [c for c in C.columns if not c.startswith(("de", "dw"))]:
        data[c] = np.repeat(C[c].to_numpy(float), nU)
    df = pd.DataFrame(data)
    per = cfg.params["period"]
    df = df[(df["week"] >= pd.Timestamp(per["start"])) & (df["week"] <= pd.Timestamp(per["freeze"]))]
    reg = [c for c in df.columns if c not in ("week", "unit", "y")]
    df = df[df[["y", *reg]].notna().all(axis=1)].reset_index(drop=True)
    num = ["y", *reg]
    df[num] = df[num] - df.groupby("unit")[num].transform("mean")
    df["group"] = df["week"]
    return df[["week", "unit", "y", *reg, "group"]]


# ----------------------------------------------------------------------------------------------- tier 1
def _fit(cfg: Config, design: pd.DataFrame, rename: dict[str, str] | None = None) -> pd.DataFrame:
    f = lp.fit_lp(cfg, design)
    if rename:
        f["driver"] = f["driver"].replace(rename)
    return f


def tier1(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame, *,
          elig: pd.DataFrame | None = None, commodities: list[str] | None = None,
          horizons: list[int] | None = None) -> pd.DataFrame:
    """WP-28. Ulang LP nasional (models.local_projection) untuk setiap cek di TIER1 (METHODS §M5).

    Baseline = spesifikasi utama (simetris, L = params.lp.lags, sampel penuh, minggu) per (komoditas, h, driver);
    h = params.lp.key_horizons. Driver yang dilaporkan: e (β kurs) dan w (ω harga dunia, bila ada padanan).
    Interval = estimate ± 1,96·SE cluster minggu (bulan untuk cek bulanan); bootstrap tidak diulang per cek.
      horizon_8_vs_12 : baris h=12 dengan baseline_estimate = β(8) (horizon utama H0-Het/H2/E1).
      lags_2_4_8      : L ∈ params.lp.lags_robust selain baseline.
      subperiod       : variant pre/post terhadap params.calendar.breaks.jisdor_method_change; observasi
                        dipakai hanya bila seluruh jendela datanya [t-(L+1), t+h] di dalam sub-periode.
      exclude_covid…  : buang observasi yang jendelanya beririsan dengan params.calendar.exclusions.covid atau bulan
                        |Δlog Brent bulanan| > ambang (_brent_extreme_months).
      fx_decomposition: de = a + b·d_dxy + ε → driver e_global (fitted) & e_idr (ε) dalam satu LP; baseline = β_e.
      monthly_frequency: LP bulanan, h_bulan = round(h·12/52), L_bulan = max(1, round(L·12/52)); kolom horizon
                        tetap horizon minggu padanannya (variant = "h_m=..").
    Keluaran: kolom kontrak 'robustness' (tier = 1) + driver, variant, se, baseline_se, baseline_in_ci, n_weeks, n_obs.
    """
    pl = cfg.params["lp"]
    L = int(pl["lags"])
    H = [int(h) for h in (horizons if horizons is not None else pl["key_horizons"])]
    present = set(panel["commodity"].unique())
    coms = [c for c in (commodities or cfg.commodity_ids()) if c in present]
    cal = cfg.params["calendar"]
    brk = pd.Timestamp(cal["breaks"]["jisdor_method_change"])
    covid = tuple(pd.Timestamp(x) for x in cal["exclusions"]["covid"])
    excl = [covid, *_brent_extreme_months(cfg, drivers)]
    dec = fx_decomposition(cfg, drivers)
    drv_dec = dec.assign(de_pos=dec["de_global"], de_neg=dec["de_idr"])
    L_m = max(1, round(L / _WEEKS_PER_MONTH))
    excl_note = "; ".join(f"{a:%Y-%m-%d}..{b:%Y-%m-%d}" for a, b in excl)

    rows: list[dict] = []

    def add(check, com, h, fit, base, variant, note):
        for r in fit.itertuples(index=False):
            key = "e" if r.driver in ("e_global", "e_idr") else r.driver
            if key not in base:
                continue
            be, bse = base[key]
            lo, hi = r.estimate - 1.96 * r.se, r.estimate + 1.96 * r.se
            rows.append({"check_id": check, "tier": 1, "commodity": com, "horizon": h, "driver": r.driver,
                         "variant": variant, "estimate": r.estimate, "se": r.se, "ci_low": lo, "ci_high": hi,
                         "baseline_estimate": be, "baseline_se": bse,
                         "baseline_in_ci": bool(lo <= be <= hi) if np.isfinite(be) and np.isfinite(lo) else np.nan,
                         "n_weeks": r.n_weeks, "n_obs": r.n_obs, "note": note})

    for com in coms:
        base_by_h: dict[int, dict[str, tuple[float, float]]] = {}
        for h in sorted(set(H) | {8, 12}):
            D = lp.build_design(cfg, panel, drivers, world, com, h, L, elig=elig)
            f = _fit(cfg, D)
            base_by_h[h] = {r.driver: (r.estimate, r.se) for r in f.itertuples(index=False)}
            if h not in H:
                continue
            base = base_by_h[h]
            # lag alternatif
            for Lr in pl["lags_robust"]:
                if int(Lr) == L:
                    continue
                add("lags_2_4_8", com, h, _fit(cfg, lp.build_design(cfg, panel, drivers, world, com, h, int(Lr),
                                                                       elig=elig)),
                    base, f"L={int(Lr)}", f"lag-augmentation L={int(Lr)} vs baseline L={L}")
            # sub-periode (V3)
            for name, ex in (("pre", [(brk, pd.Timestamp.max)]),
                             ("post", [(pd.Timestamp.min, brk - pd.Timedelta(days=1))])):
                Ds = _restrict(D, _window_ok(D["week"], L, h, ex))
                add(TIER1[2], com, h, _fit(cfg, Ds), base, name,
                    f"{name} {brk:%Y-%m-%d} (jendela [t-{L + 1}, t+h] utuh dalam sub-periode)")
            # tanpa COVID & bulan Brent ekstrem
            Dx = _restrict(D, _window_ok(D["week"], L, h, excl))
            add(TIER1[3], com, h, _fit(cfg, Dx), base, "excl",
                f"jendela observasi tidak beririsan dengan {excl_note}")
            # dekomposisi kurs
            Dd = lp.build_design(cfg, panel, drv_dec, world, com, h, L, asymmetric=True, elig=elig)
            fd = _fit(cfg, Dd, {"e_pos": "e_global", "e_neg": "e_idr"})
            add(TIER1[4], com, h, fd, base, "decomp",
                f"de = {dec.attrs['a']:.5f} + {dec.attrs['b']:.3f}·d_dxy + ε (R² {dec.attrs['r2']:.2f}); "
                "e_global = fitted, e_idr = ε; baseline = β_e")
            # frekuensi bulanan
            h_m = max(1, round(h / _WEEKS_PER_MONTH))
            Dm = _monthly_design(cfg, panel, drivers, world, com, h_m, L_m, elig)
            add(TIER1[5], com, h, _fit(cfg, Dm), base, f"h_m={h_m}",
                f"LP bulanan h={h_m} bulan, L={L_m}; n_weeks = jumlah bulan; SE cluster bulan")
        # horizon 8 vs 12
        if 12 in base_by_h and 8 in base_by_h:
            f12 = pd.DataFrame([{"driver": k, "estimate": v[0], "se": v[1], "n_weeks": np.nan, "n_obs": np.nan}
                                for k, v in base_by_h[12].items()])
            add(TIER1[0], com, 12, f12, base_by_h[8], "h=12", "β(12) vs baseline β(8) (horizon utama)")
    out = pd.DataFrame(rows, columns=ROBUSTNESS_COLUMNS + _EXTRA)
    return out[ROBUSTNESS_COLUMNS + _EXTRA]


VALIDATION_CHECKS = ("V2_case_study_events", "V2_case_study_forecast", "V4_lp_vs_event_study")


def lp_implied_paths(cfg: Config, profiles: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                     starts: pd.Series, commodity: str) -> np.ndarray:
    """WP-29. Respons LP nasional yang diimplikasikan untuk jendela berawal s: y(s,h) = p_{s+h} - p_{s-1} ≈
    Σ_{j=0..h} β_e(h-j)·de_{s+j} + Σ_j ω(h-j)·dw_{s+j} (superposisi impuls mingguan, LP linear; METHODS §M5, D-114).

    profiles: baris level='national', driver e (& w bila ada), horizon 0..H. Return array (len(starts), H+1);
    NaN bila de/dw atau β/ω untuk suatu suku tidak tersedia."""
    H = int(max(cfg.params["lp"]["horizons"]))
    nat = profiles.loc[(profiles["level"] == "national") & (profiles["commodity"] == commodity)]
    coef = {d: nat.loc[nat["driver"] == d].set_index("horizon")["estimate"].reindex(range(H + 1)).to_numpy(float)
            for d in ("e", "w")}
    imp = {"e": drivers.sort_values("week").set_index("week")["de"]}
    if np.isfinite(coef["w"]).any() and commodity in set(world["commodity"]):
        imp["w"] = world.loc[world["commodity"] == commodity].set_index("week")["dw"].sort_index()
    out = np.zeros((len(starts), H + 1))
    for drv, x in imp.items():
        b = coef[drv]
        for i, s in enumerate(pd.to_datetime(pd.Series(starts))):
            dx = x.reindex(pd.date_range(s, periods=H + 1, freq="W-MON")).to_numpy(float)
            for h in range(H + 1):
                out[i, h] += float(np.dot(b[h::-1], dx[: h + 1]))       # Σ_j β(h-j)·dx_{s+j}
    return out


def validation(cfg: Config, profiles: pd.DataFrame, events: pd.DataFrame, episodes: pd.DataFrame,
               drivers: pd.DataFrame, world: pd.DataFrame,
               forecast_eval: pd.DataFrame | None = None) -> pd.DataFrame:
    """WP-29. Validasi V2 & V4 (proposal §6.2; METHODS §M5; D-114). V1 = Task 4, V3 = Tier 1 subperiod.

    Respons episode "di atas normal" = dlog_price - median plasebo (kolom events.placebo_median; cadangan
    (placebo_lo + placebo_hi)/2 bila tidak ada -- titik tengah peka terhadap ekor, D-114; level national), dibandingkan dengan respons LP yang diimplikasikan (lp_implied_paths, profiles national).
    V4_lp_vs_event_study: per komoditas × h ∈ key_horizons atas episode in_period dengan outcome lengkap:
        estimate = rerata kelebihan event (ci = ± 1,96·sd/√n antar episode), baseline_estimate = rerata implikasi LP;
        kolom ekstra sign_agree (porsi episode dengan tanda sama), corr (korelasi antar episode), n_episodes.
    V2_case_study_events: per episode yang mulai di tahun freeze, komoditas, h dengan outcome lengkap:
        estimate = kelebihan event, ci = pita plasebo dikurangi median (rentang null), baseline = implikasi LP.
    V2_case_study_forecast (bila forecast_eval ada): subset case_study, model M2 & M3, level all/commodity:
        estimate = rasio MAE vs M1 (origin tahun freeze), baseline = rasio subset all; ci NaN (deskriptif, DM p di note).
    Keluaran: kolom kontrak 'robustness' (tier = 'V') + driver, variant, n_episodes, sign_agree, corr.
    """
    H_key = [int(h) for h in cfg.params["lp"]["key_horizons"]]
    year = pd.Timestamp(cfg.params["period"]["freeze"]).year
    eps = episodes.copy()
    eps["start_week"] = pd.to_datetime(eps["start_week"])
    if "in_period" in eps.columns:
        eps = eps[eps["in_period"].astype(bool)].reset_index(drop=True)
    ev = events.loc[events["level"] == "national"].copy()
    center = ev["placebo_median"] if "placebo_median" in ev.columns else (ev["placebo_lo"] + ev["placebo_hi"]) / 2
    ev["excess"] = ev["dlog_price"] - center
    ev["null_lo"], ev["null_hi"] = ev["placebo_lo"] - center, ev["placebo_hi"] - center
    rows: list[dict] = []
    base = {"tier": "V", "driver": "e+w"}
    for com in [c for c in cfg.commodity_ids() if c in set(ev["commodity"])]:
        imp = lp_implied_paths(cfg, profiles, drivers, world, eps["start_week"], com)
        impl = pd.DataFrame(imp, index=eps["episode_id"].to_numpy()).stack().rename("implied")
        impl.index.names = ["episode_id", "horizon"]
        e = ev[ev["commodity"] == com].merge(impl.reset_index(), on=["episode_id", "horizon"], how="inner")
        e = e.merge(eps[["episode_id", "start_week"]], on="episode_id")
        for h in H_key:
            g = e[(e["horizon"] == h) & np.isfinite(e["excess"]) & np.isfinite(e["implied"])]
            n = len(g)
            if n:
                m = g["excess"].mean()
                half = 1.96 * g["excess"].std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
                rows.append({**base, "check_id": VALIDATION_CHECKS[2], "commodity": com, "horizon": h,
                             "variant": "episodes_mean", "estimate": m, "ci_low": m - half, "ci_high": m + half,
                             "baseline_estimate": g["implied"].mean(), "n_episodes": n,
                             "sign_agree": float((np.sign(g["excess"]) == np.sign(g["implied"])).mean()),
                             "corr": float(g["excess"].corr(g["implied"])) if n > 2 else np.nan,
                             "note": "kelebihan event (dlog - median plasebo) vs implikasi LP Σβ·de + Σω·dw; "
                                     "ci = ±1,96·sd/√n antar episode"})
            for r in g[g["start_week"].dt.year == year].itertuples(index=False):
                rows.append({**base, "check_id": VALIDATION_CHECKS[0], "commodity": com, "horizon": h,
                             "variant": f"episode_{r.episode_id}", "estimate": r.excess,
                             "ci_low": r.null_lo, "ci_high": r.null_hi, "baseline_estimate": r.implied,
                             "n_episodes": 1, "sign_agree": float(np.sign(r.excess) == np.sign(r.implied)),
                             "corr": np.nan,
                             "note": f"episode mulai {r.start_week:%Y-%m-%d}; ci = pita plasebo 95% relatif terhadap median; "
                                     f"placebo_p {r.placebo_p:.3f}"})
    if forecast_eval is not None and len(forecast_eval):
        fe = forecast_eval
        sel = fe["model"].isin(["M2", "M3"]) & (fe["region"] == "ALL")
        if "level" in fe.columns:
            sel &= fe["level"].isin(["all", "commodity"])
        key = ["horizon", "model", "commodity", "region"]
        cs = fe[sel & (fe["subset"] == "case_study")]
        al = fe[sel & (fe["subset"] == "all")][key + ["mae_ratio_vs_m1"]].rename(columns={"mae_ratio_vs_m1": "base"})
        for r in cs.merge(al, on=key, how="left").itertuples(index=False):
            rows.append({**base, "check_id": VALIDATION_CHECKS[1], "commodity": r.commodity, "horizon": int(r.horizon),
                         "driver": r.model, "variant": "mae_ratio_vs_m1", "estimate": r.mae_ratio_vs_m1,
                         "ci_low": np.nan, "ci_high": np.nan, "baseline_estimate": r.base, "n_episodes": np.nan,
                         "sign_agree": np.nan, "corr": np.nan,
                         "note": f"origin {year} (outcome lengkap), n_origins {r.n_origins}, n_nonoverlap "
                                 f"{r.n_nonoverlap}, DM p {r.dm_p:.3f}; baseline = rasio semua origin; deskriptif"})
    cols = ROBUSTNESS_COLUMNS + ["driver", "variant", "n_episodes", "sign_agree", "corr"]
    return pd.DataFrame(rows, columns=cols)


def tier2(cfg: Config) -> pd.DataFrame:
    """WP-30. Opsional; yang pertama dipotong bila waktu habis."""
    todo("WP-30")
