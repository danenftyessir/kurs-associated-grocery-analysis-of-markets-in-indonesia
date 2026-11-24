"""TSMixer untuk arah: hyperparameter dapat diatur (monkeypatch konstanta models.neural), loss L1 (regresi) atau BCE (arah).
Rolling-origin sama dengan D-142: refit tiap REFIT origin, jendela latih hanya t + h <= origin refit."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd

from kg import cfg  # noqa: E402
from kagami.features.forecast import origins  # noqa: E402
from kagami.models import neural  # noqa: E402

HERE = os.path.dirname(__file__)
HORIZONS = [4, 8]
_ARR = {}


def arrays():
    if "a" not in _ARR:
        tab = pd.read_parquet(os.path.join(HERE, "tab.parquet"))
        _ARR["a"] = neural.series_arrays(tab, HORIZONS)
        _ARR["tab"] = tab
    return _ARR["a"]


def set_hp(hp):
    neural.LOOKBACK = int(hp.get("lookback", 52))
    neural.D_MODEL = int(hp.get("d_model", 32))
    neural.N_LAYERS = int(hp.get("n_layers", 2))
    neural.DROPOUT = float(hp.get("dropout", 0.1))
    neural.EPOCHS = int(hp.get("epochs", 4))
    neural.LR = float(hp.get("lr", 1e-3))
    neural.MAX_WINDOWS = int(hp.get("max_windows", 40_000))
    neural.BATCH = int(hp.get("batch", 512))


def fit(hp, arr, origin_idx, seed, fx=False):
    import torch
    set_hp(hp)
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    tt, ss, Y = neural._train_index(arr, origin_idx, HORIZONS, rng)
    raw = neural._windows(arr, tt, ss, fx)
    scale = {"p": float(np.std(raw[..., 0])) or 1.0}
    if fx:
        scale.update(de=float(np.std(raw[..., 1])) or 1.0, dw=float(np.std(raw[..., 2])) or 1.0)
    X = torch.from_numpy(neural._windows(arr, tt, ss, fx, scale))
    loss_kind = hp.get("loss", "l1")
    if loss_kind == "bce":
        M = torch.from_numpy((np.isfinite(Y) & (np.nan_to_num(Y) != 0)).astype(np.float32))
        Yt = torch.from_numpy((np.nan_to_num(Y) > 0).astype(np.float32))
        ysd = np.ones(len(HORIZONS))
    else:
        ysd = np.nanstd(Y, axis=0)
        ysd = np.where(np.isfinite(ysd) & (ysd > 0), ysd, 1.0)
        Yt = torch.from_numpy(np.nan_to_num(Y / ysd).astype(np.float32))
        M = torch.from_numpy(np.isfinite(Y).astype(np.float32))
    C = torch.from_numpy(arr["cid"][ss].astype(np.int64))
    net = neural._build_net("tsmixer", X.shape[-1], len(HORIZONS), arr["n_commodities"])
    opt = torch.optim.AdamW(net.parameters(), lr=neural.LR, weight_decay=float(hp.get("weight_decay", 0.0)))
    bce = torch.nn.BCEWithLogitsLoss(reduction="none")
    net.train()
    n = len(X)
    for _ in range(neural.EPOCHS):
        perm = torch.from_numpy(rng.permutation(n))
        for i in range(0, n, neural.BATCH):
            b = perm[i:i + neural.BATCH]
            out = net(X[b], C[b])
            el = bce(out, Yt[b]) if loss_kind == "bce" else (out - Yt[b]).abs()
            loss = (el * M[b]).sum() / M[b].sum().clamp(min=1)
            opt.zero_grad()
            loss.backward()
            opt.step()
    net.eval()
    return net, {"scale": scale, "ysd": ysd, "fx": fx, "loss": loss_kind, "hp": hp}


def predict(net, meta, arr, t_idx, s_idx):
    """→ skor (N × 2): logit/probabilitas naik untuk BCE (dikonversi ke p_up), ramalan y untuk L1."""
    import torch
    set_hp(meta["hp"])
    X = torch.from_numpy(neural._windows(arr, t_idx, s_idx, meta["fx"], meta["scale"]))
    with torch.no_grad():
        out = net(X, torch.from_numpy(arr["cid"][s_idx].astype(np.int64))).numpy()
    if meta["loss"] == "bce":
        return 1 / (1 + np.exp(-out))
    return out * meta["ysd"]


def rolling(hp, ords, seed_base, refit=4, fx=False):
    """Prediksi pada origin `ords` (urut), refit tiap `refit` origin dengan data s.d. origin refit. → long DataFrame."""
    arr = arrays()
    tab = _ARR["tab"]
    widx = {w: i for i, w in enumerate(arr["weeks"])}
    rows = []
    for r0 in range(0, len(ords), refit):
        net, meta = fit(hp, arr, widx[ords[r0]], seed_base + r0, fx)
        for o in ords[r0:r0 + refit]:
            t = widx[o]
            s = np.arange(arr["p"].shape[1])
            ok = np.isfinite(arr["p_raw"][t, s])
            s = s[ok]
            sc = predict(net, meta, arr, np.full(len(s), t), s)
            for j, h in enumerate(HORIZONS):
                y = arr["y"][h][t, s]
                keys = arr["series"][s]
                rows.append(pd.DataFrame({"origin": o, "horizon": h, "province_id": keys.get_level_values(0),
                                          "commodity": keys.get_level_values(1), "y_true": y, "score": sc[:, j]}))
    out = pd.concat(rows, ignore_index=True)
    return out[np.isfinite(out["y_true"])]


def all_origins(h):
    return origins(cfg, _ARR["tab"]["week"].drop_duplicates() if "tab" in _ARR else pd.read_parquet(
        os.path.join(HERE, "tab.parquet"))["week"].drop_duplicates(), h)
