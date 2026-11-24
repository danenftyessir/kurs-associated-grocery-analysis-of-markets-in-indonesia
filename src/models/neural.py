"""Model deep learning & foundation model untuk Task 4 (EKSPLORATIF, D-142; bukan uji praregistrasi).

Semua model meramal target Task 4 yang sama, y = p_{t+h} − p_t (h 4 & 8), pada origin & baris uji yang sama dengan
M0–M3 (`features.forecast.split_origin`), sehingga MAE, DM, dan metrik arah sebanding langsung:

- PTST    : PatchTST (Nie dkk. 2023) global, channel-independent: patch 8 minggu (langkah 4) dari 52 minggu terakhir
            log harga relatif harga di origin, encoder Transformer kecil + embedding komoditas.
- TSMX    : TSMixer (Chen dkk. 2023) global: blok MLP pencampur waktu & kanal, kanal = log harga relatif.
- TSMX_fx : TSMX + kanal de (Δ log JISDOR) dan dw (Δ log harga dunia rupiah, as-of `available_at`) → selisih
            TSMX_fx − TSMX = ablation kurs pada model deep learning.
- TFM     : TimesFM 3.0 (google/timesfm-3.0-pytorch) zero-shot pada riwayat log harga (tanpa pelatihan).
- TFM_fx  : TFM + kovariat masa lalu de & dw (past-only covariates; nilai masa depan tidak dipakai).

Pencegahan kebocoran: jendela latih hanya yang target-nya terealisasi sampai origin (t + h ≤ origin), skala dari data
latih, dw memakai nilai as-of dari `feature_table`, konteks TimesFM berhenti di origin. Model deep dilatih ulang setiap
`REFIT_EVERY` origin (16 minggu) dan dipakai untuk origin sesudahnya sampai refit berikutnya (selalu out-of-sample).
Hiperparameter di bawah DITETAPKAN SEBELUM melihat hasil, tidak dituning pada data uji; bukan bagian `params.yaml`
(dibekukan G6) karena eksploratif. Butuh PyTorch (dan paket `timesfm` 3.0 + bobot 1,32 GB untuk TFM, lisensi
non-komersial); bila tidak ada, model itu dilewati dengan pesan.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable

import numpy as np
import pandas as pd

from kagami.features.forecast import feature_table, origins, split_origin
from kagami.utils.config import Config

SEQ_MODELS = {"PTST": ("patchtst", False), "TSMX": ("tsmixer", False), "TSMX_fx": ("tsmixer", True)}
FOUNDATION_MODELS = {"TFM": False, "TFM_fx": True}
ALL_MODELS = (*SEQ_MODELS, *FOUNDATION_MODELS)
LOOKBACK = 52            # minggu riwayat input model deep
PATCH, STRIDE = 8, 4     # PatchTST
D_MODEL, N_LAYERS, N_HEADS, DROPOUT = 32, 2, 4, 0.1
EPOCHS, BATCH, LR, MAX_WINDOWS = 4, 512, 1e-3, 40_000
REFIT_EVERY = 4          # origin (= 16 minggu)
TFM_REPO = "google/timesfm-3.0-pytorch"
TORCH_SEED_OFFSET = 4201  # cfg.seed + 4201 (+ indeks refit) (+ 1000 · nomor replikasi)
REPLICATE = re.compile(r"^(?P<base>.+)_r(?P<rep>\d+)$")   # "PTST_r2" = PatchTST replikasi seed ke-2 (D-144)


def split_replicate(model: str) -> tuple[str, int]:
    """'TSMX_fx_r3' → ('TSMX_fx', 3); nama tanpa akhiran → (nama, 1). Replikasi hanya untuk model deep yang dilatih."""
    m = REPLICATE.match(model)
    return (m["base"], int(m["rep"])) if m and m["base"] in SEQ_MODELS else (model, 1)


# --------------------------------------------------------------------------- data berbentuk deret
def series_arrays(table: pd.DataFrame, horizons: list[int]) -> dict:
    """feature_table → matriks minggu × seri: log harga (ffill), de_1, dw_1 as-of (NaN → 0), target y_h, kode komoditas."""
    keys = ["province_id" if "province_id" in table else "region", "commodity"]
    piv = lambda col: table.pivot_table(index="week", columns=keys, values=col, aggfunc="first", dropna=False)  # noqa: E731
    lp = piv("log_p").sort_index()
    cols = lp.columns
    out = {"weeks": lp.index, "series": cols, "keys": keys,
           "p": lp.ffill().to_numpy(float), "p_raw": lp.to_numpy(float),
           "de": piv("de_1").reindex(index=lp.index, columns=cols).fillna(0.0).to_numpy(float),
           "dw": piv("dw_1").reindex(index=lp.index, columns=cols).fillna(0.0).to_numpy(float),
           "y": {h: piv(f"y_{h}").reindex(index=lp.index, columns=cols).to_numpy(float) for h in horizons}}
    com = cols.get_level_values("commodity")
    levels = sorted(set(com))
    out["cid"] = np.array([levels.index(c) for c in com])
    out["n_commodities"] = len(levels)
    return out


def _windows(arr: dict, t_idx: np.ndarray, s_idx: np.ndarray, fx: bool, scale: dict | None = None) -> np.ndarray:
    """Input (N × L × C): log harga relatif harga di t (+ de, dw bila fx), 0 untuk minggu sebelum data ada."""
    lag = np.arange(-LOOKBACK + 1, 1)
    tt = t_idx[:, None] + lag[None, :]
    ok = tt >= 0
    tt = np.clip(tt, 0, None)
    p = arr["p"][tt, s_idx[:, None]]
    x = np.where(ok, p - arr["p"][t_idx, s_idx][:, None], 0.0)
    x = np.nan_to_num(x)
    chans = [x / (scale["p"] if scale else 1.0)]
    if fx:
        for k in ("de", "dw"):
            v = np.where(ok, arr[k][tt, s_idx[:, None]], 0.0)
            chans.append(v / (scale[k] if scale else 1.0))
    return np.stack(chans, axis=-1).astype(np.float32)


def _train_index(arr: dict, origin_idx: int, horizons: list[int], rng: np.random.Generator) -> tuple[np.ndarray, ...]:
    """Pasangan (t, seri) latih: p_t ada, minimal satu target dengan t + h ≤ origin terisi; dicuplik ≤ MAX_WINDOWS."""
    T, S = arr["p"].shape
    t = np.arange(LOOKBACK - 1, origin_idx + 1)
    tt, ss = np.meshgrid(t, np.arange(S), indexing="ij")
    tt, ss = tt.ravel(), ss.ravel()
    Y = np.stack([np.where(tt + h <= origin_idx, arr["y"][h][tt, ss], np.nan) for h in horizons], axis=1)
    keep = np.isfinite(arr["p_raw"][tt, ss]) & np.isfinite(Y).any(axis=1)
    tt, ss, Y = tt[keep], ss[keep], Y[keep]
    if len(tt) > MAX_WINDOWS:
        pick = rng.choice(len(tt), MAX_WINDOWS, replace=False)
        tt, ss, Y = tt[pick], ss[pick], Y[pick]
    return tt, ss, Y


def _build_net(kind: str, n_chan: int, n_out: int, n_com: int):
    import torch
    from torch import nn

    class PatchTST(nn.Module):
        def __init__(self):
            super().__init__()
            self.n_patch = (LOOKBACK - PATCH) // STRIDE + 1
            self.embed = nn.Linear(PATCH, D_MODEL)
            self.pos = nn.Parameter(torch.zeros(1, self.n_patch, D_MODEL))
            self.com = nn.Embedding(n_com, D_MODEL)
            layer = nn.TransformerEncoderLayer(D_MODEL, N_HEADS, 2 * D_MODEL, DROPOUT, batch_first=True)
            self.enc = nn.TransformerEncoder(layer, N_LAYERS)
            self.head = nn.Sequential(nn.Flatten(), nn.Dropout(DROPOUT), nn.Linear(self.n_patch * D_MODEL, n_out))

        def forward(self, x, cid):                     # x: N × L × 1 (channel-independent: kanal harga saja)
            z = x[..., 0].unfold(1, PATCH, STRIDE)      # N × n_patch × PATCH
            z = self.embed(z) + self.pos + self.com(cid)[:, None, :]
            return self.head(self.enc(z))

    class MixerBlock(nn.Module):
        def __init__(self):
            super().__init__()
            self.nt, self.nf = nn.LayerNorm(n_chan), nn.LayerNorm(n_chan)
            self.time = nn.Sequential(nn.Linear(LOOKBACK, LOOKBACK), nn.ReLU(), nn.Dropout(DROPOUT))
            self.feat = nn.Sequential(nn.Linear(n_chan, D_MODEL), nn.ReLU(), nn.Dropout(DROPOUT), nn.Linear(D_MODEL, n_chan))

        def forward(self, x):                           # N × L × C
            x = x + self.time(self.nt(x).transpose(1, 2)).transpose(1, 2)
            return x + self.feat(self.nf(x))

    class TSMixer(nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = nn.Sequential(*[MixerBlock() for _ in range(N_LAYERS)])
            self.com = nn.Embedding(n_com, D_MODEL)
            self.head = nn.Sequential(nn.Linear(LOOKBACK * n_chan + D_MODEL, D_MODEL), nn.ReLU(), nn.Linear(D_MODEL, n_out))

        def forward(self, x, cid):
            z = self.blocks(x).flatten(1)
            return self.head(torch.cat([z, self.com(cid)], dim=1))

    return PatchTST() if kind == "patchtst" else TSMixer()


def fit_sequence_model(cfg: Config, model: str, arr: dict, origin_idx: int, horizons: list[int], seed: int):
    """D-142. Latih satu model deep (PTST / TSMX / TSMX_fx) pada jendela dengan target terealisasi s.d. origin_idx.
    Loss L1 (= kriteria MAE Task 4) pada target terskala, target yang belum terealisasi di-mask. → (net, skala)."""
    import torch

    kind, fx = SEQ_MODELS[model]
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    tt, ss, Y = _train_index(arr, origin_idx, horizons, rng)
    raw = _windows(arr, tt, ss, fx)
    scale = {"p": float(np.std(raw[..., 0])) or 1.0}
    if fx:
        scale.update(de=float(np.std(raw[..., 1])) or 1.0, dw=float(np.std(raw[..., 2])) or 1.0)
    X = torch.from_numpy(_windows(arr, tt, ss, fx, scale))
    ysd = np.nanstd(Y, axis=0)
    ysd = np.where(np.isfinite(ysd) & (ysd > 0), ysd, 1.0)
    Yt = torch.from_numpy(np.nan_to_num(Y / ysd).astype(np.float32))
    M = torch.from_numpy(np.isfinite(Y).astype(np.float32))
    C = torch.from_numpy(arr["cid"][ss].astype(np.int64))
    net = _build_net(kind, X.shape[-1], len(horizons), arr["n_commodities"])
    opt = torch.optim.Adam(net.parameters(), lr=LR)
    net.train()
    n = len(X)
    for _ in range(EPOCHS):
        perm = torch.from_numpy(rng.permutation(n))
        for i in range(0, n, BATCH):
            b = perm[i:i + BATCH]
            loss = ((net(X[b], C[b]) - Yt[b]).abs() * M[b]).sum() / M[b].sum().clamp(min=1)
            opt.zero_grad()
            loss.backward()
            opt.step()
    net.eval()
    return net, {"scale": scale, "ysd": ysd, "fx": fx}


def predict_sequence_model(net, meta: dict, arr: dict, t_idx: np.ndarray, s_idx: np.ndarray) -> np.ndarray:
    """Ramalan y (N × len(horizons)) untuk pasangan (t = origin, seri)."""
    import torch

    X = torch.from_numpy(_windows(arr, t_idx, s_idx, meta["fx"], meta["scale"]))
    with torch.no_grad():
        out = net(X, torch.from_numpy(arr["cid"][s_idx].astype(np.int64))).numpy()
    return out * meta["ysd"]


def load_timesfm(device: str = "cpu"):
    """Muat TimesFM 3.0 (paket `timesfm` ≥ 3.0, bobot dari Hugging Face, lisensi non-komersial). None bila tidak tersedia."""
    try:
        from timesfm3 import TimesFM3Forecaster
    except ImportError:
        print("[task4-deep] paket `timesfm` 3.x tidak terpasang -> TFM dilewati (pip install timesfm==3.0.2)")
        return None
    return TimesFM3Forecaster.from_pretrained(TFM_REPO, device=device, per_core_batch_size=64)


def predict_timesfm(forecaster, arr: dict, origin_idx: int, s_idx: np.ndarray, horizons: list[int],
                    fx: bool) -> np.ndarray:
    """D-142. Ramalan zero-shot TimesFM: konteks = log harga s.d. origin (tanpa nilai sesudahnya), satu ramalan horizon
    max(h) memberi semua h; y_h = ramalan(t + h) − p_t. fx: de & dw (as-of) sebagai kovariat masa lalu saja."""
    H = max(horizons)
    ctx = [arr["p_raw"][: origin_idx + 1, s] for s in s_idx]
    po = [np.stack([arr["de"][: origin_idx + 1, s], arr["dw"][: origin_idx + 1, s]]) for s in s_idx] if fx else None
    outs = list(forecaster.predict_batch(ctx, horizon=H, past_only_covariates=po))
    base = arr["p"][origin_idx, s_idx]
    return np.stack([[o.forecast[h - 1] for h in horizons] for o in outs]) - base[:, None]


def rolling_deep(cfg: Config, panel: pd.DataFrame, drivers: pd.DataFrame, world: pd.DataFrame,
                 models: list[str] | None = None, done: pd.DataFrame | None = None,
                 checkpoint: Callable[[pd.DataFrame], None] | None = None, forecaster=None) -> pd.DataFrame:
    """D-142. Rolling-origin untuk model deep & foundation pada origin dan baris uji Task 4 → origin, horizon, model,
    province_id|region, commodity, y_true, y_pred, large_move (kontrak `forecast_preds`). Pasangan (model, origin) di `done`
    dilewati (lanjut dari checkpoint; checkpoint dipanggil setelah setiap model × refit / origin TimesFM)."""
    import torch

    torch.set_num_threads(max(1, torch.get_num_threads()))
    p = cfg.params["forecast"]
    horizons = [int(h) for h in p["horizons"]]
    models = list(models or ALL_MODELS)
    table = feature_table(cfg, panel, drivers, world, horizons)
    arr = series_arrays(table, horizons)
    widx = {w: i for i, w in enumerate(arr["weeks"])}
    sidx = {k: i for i, k in enumerate(arr["series"])}
    keys = arr["keys"]
    keep = keys + (["region"] if keys[0] == "province_id" else [])
    cols = ["origin", "horizon", "model"] + keep + ["y_true", "y_pred", "large_move"]
    out = [done[cols]] if done is not None and len(done) else []
    finished = set(zip(done["model"], done["origin"])) if done is not None and len(done) else set()
    # baris uji per origin = gabungan horizon (seri yang punya target h itu)
    tests: dict[pd.Timestamp, dict[int, pd.DataFrame]] = {}
    for h in horizons:
        for o in origins(cfg, table["week"].drop_duplicates(), h):
            train, test = split_origin(cfg, table, o, h)
            if train.empty or test.empty:
                continue
            thr = np.nanpercentile(train["de_4"].abs(), p["large_move_pct"])
            tests.setdefault(o, {})[h] = test[keep].assign(origin=o, horizon=h, y_true=test["y"],
                                                           large_move=test["de_4"].abs() > thr)
    ords = sorted(tests)

    def emit(model: str, o: pd.Timestamp, pred: dict[tuple, np.ndarray]) -> None:
        for h, t in tests[o].items():
            k = [tuple(r) for r in t[keys].itertuples(index=False)]
            out.append(t.assign(model=model, y_pred=[pred[x][horizons.index(h)] for x in k])[cols])

    for model in models:
        base, rep_no = split_replicate(model)
        if base in SEQ_MODELS:
            todo = [o for o in ords if (model, o) not in finished]
            for r0 in range(0, len(ords), REFIT_EVERY):
                block = [o for o in ords[r0:r0 + REFIT_EVERY] if o in todo]
                if not block:
                    continue
                t0 = time.perf_counter()
                net, meta = fit_sequence_model(cfg, base, arr, widx[ords[r0]], horizons,
                                               cfg.seed + TORCH_SEED_OFFSET + r0 + 1000 * (rep_no - 1))
                for o in block:
                    ser = sorted({tuple(r) for t in tests[o].values() for r in t[keys].itertuples(index=False)})
                    s = np.array([sidx[x] for x in ser])
                    yhat = predict_sequence_model(net, meta, arr, np.full(len(s), widx[o]), s)
                    emit(model, o, dict(zip(ser, yhat)))
                print(f"[task4-deep] {model} refit origin={ords[r0].date()} ({len(block)} origin, "
                      f"{time.perf_counter() - t0:.1f} dtk)")
                if checkpoint is not None:
                    checkpoint(pd.concat(out, ignore_index=True))
        elif model in FOUNDATION_MODELS:
            forecaster = forecaster if forecaster is not None else load_timesfm()
            if forecaster is None:
                continue
            for o in ords:
                if (model, o) in finished:
                    continue
                t0 = time.perf_counter()
                ser = sorted({tuple(r) for t in tests[o].values() for r in t[keys].itertuples(index=False)})
                s = np.array([sidx[x] for x in ser])
                yhat = predict_timesfm(forecaster, arr, widx[o], s, horizons, FOUNDATION_MODELS[model])
                emit(model, o, dict(zip(ser, yhat)))
                print(f"[task4-deep] {model} origin={o.date()} ({len(s)} seri, {time.perf_counter() - t0:.1f} dtk)")
                if checkpoint is not None and ords.index(o) % 5 == 4:
                    checkpoint(pd.concat(out, ignore_index=True))
        else:
            raise ValueError(f"model tidak dikenal: {model}; pilih dari {ALL_MODELS}")
    return pd.concat(out, ignore_index=True)[cols] if out else pd.DataFrame(columns=cols)
