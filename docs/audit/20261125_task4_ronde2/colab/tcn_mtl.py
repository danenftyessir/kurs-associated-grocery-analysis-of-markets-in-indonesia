"""TCN kausal multi-task untuk arah harga (EKSPLORATIF, D-146). Dijalankan di Colab GPU.

Input  : ext.parquet (feature_table + fitur dinamika harga, satu baris per minggu × provinsi × komoditas; turunan PIHPS,
         hanya di folder Drive tim yang privat).
Model  : per sampel (seri, minggu t): jendela L minggu kanal deret (log harga relatif p_t, Δp, deviasi spasial, Δp nasional
         komoditas, deviasi MA13) → TCN kausal dilated → ⊕ fitur tabular C1-tuned pada t ⊕ embedding komoditas & provinsi
         → dua kepala logit (arah h 4, arah h 8). Loss BCE, label hanya bila y ≠ 0 dan terealisasi s.d. origin refit.
Protokol: origin Task 4 (tiap 4 minggu sejak 2021-01-04); refit tiap REFIT origin dengan sampel t + h ≤ origin refit;
         prediksi origin sesudahnya s.d. refit berikutnya (selalu out-of-sample). Skala dari data latih.
Output : <OUT>/tcn_preds_<variant>_r<seed>.parquet (origin, horizon, province_id, commodity, y_true, p_up) + checkpoint
         per refit (lanjut otomatis bila sesi putus).
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

CHANNELS = ["rel_p", "d1", "spatial_dev", "nat_dp_1", "dev_ma13"]
BASE = ["lag_dp_1", "lag_dp_4", "lag_dp_8", "month", "idf_rel_week", "db_1", "db_4"]
TAB = BASE + ["dp1_l1", "dp1_l2", "dp1_l3", "lag_dp_13", "lag_dp_26", "lag_dp_52", "ewm_dp_4", "ewm_dp_13", "std_dp_4",
              "std_dp_13", "std_dp_26", "up_share_13", "dn_share_13", "accel_4", "run_sign", "woy_sin", "woy_cos",
              "dev_ma13", "dev_ma52", "range_pos_52", "spatial_dev", "spatial_dev_chg4", "nat_dp_1", "nat_dp_4",
              "nat_dp_8", "nat_up_share_4", "nat_std_13"]          # + yseas_52/104 per horizon digabung jadi 4 kolom
SEAS = ["yseas_52_h4", "yseas_104_h4", "yseas_52_h8", "yseas_104_h8"]
HS = (4, 8)
FIRST_ORIGIN, STEP = pd.Timestamp("2021-01-04"), 4


class Chomp(nn.Module):
    def __init__(self, k):
        super().__init__()
        self.k = k

    def forward(self, x):
        return x[..., :-self.k] if self.k else x


class Block(nn.Module):
    def __init__(self, cin, cout, k, d, drop):
        super().__init__()
        pad = (k - 1) * d
        self.net = nn.Sequential(nn.Conv1d(cin, cout, k, padding=pad, dilation=d), Chomp(pad), nn.GELU(), nn.Dropout(drop),
                                 nn.Conv1d(cout, cout, k, padding=pad, dilation=d), Chomp(pad), nn.GELU(), nn.Dropout(drop))
        self.res = nn.Conv1d(cin, cout, 1) if cin != cout else nn.Identity()

    def forward(self, x):
        return self.net(x) + self.res(x)


class TCNMTL(nn.Module):
    def __init__(self, n_ch, n_tab, n_com, n_prov, width, levels, k, drop, use_tab, use_seq):
        super().__init__()
        self.use_tab, self.use_seq = use_tab, use_seq
        layers, c = [], n_ch
        for i in range(levels):
            layers.append(Block(c, width, k, 2 ** i, drop))
            c = width
        self.tcn = nn.Sequential(*layers)
        self.com, self.prov = nn.Embedding(n_com, 8), nn.Embedding(n_prov, 8)
        d_in = 16 + (width if use_seq else 0) + (n_tab if use_tab else 0)
        self.trunk = nn.Sequential(nn.Linear(d_in, 128), nn.GELU(), nn.Dropout(drop), nn.Linear(128, 64), nn.GELU())
        self.heads = nn.Linear(64, len(HS))

    def forward(self, seq, tab, com, prov):
        parts = [self.com(com), self.prov(prov)]
        if self.use_seq:
            parts.append(self.tcn(seq)[..., -1])
        if self.use_tab:
            parts.append(tab)
        return self.heads(self.trunk(torch.cat(parts, 1)))


def arrays(ext):
    keys = ["province_id", "commodity"]
    piv = lambda c: ext.pivot(index="week", columns=keys, values=c).sort_index()  # noqa: E731
    lp = piv("log_p")
    cols = lp.columns
    pf = lp.ffill(limit=8)
    A = {"weeks": lp.index, "series": cols, "p": pf.to_numpy(float), "p_raw": lp.to_numpy(float)}
    A["ch"] = {c: (pf.diff() if c == "d1" else piv(c).reindex(index=lp.index, columns=cols)).to_numpy(float)
               for c in CHANNELS if c != "rel_p"}
    A["tab"] = np.stack([piv(c).reindex(index=lp.index, columns=cols).to_numpy(float) for c in TAB + SEAS], axis=-1)
    A["y"] = {h: piv(f"y_{h}").reindex(index=lp.index, columns=cols).to_numpy(float) for h in HS}
    com = cols.get_level_values("commodity")
    A["cid"] = pd.Categorical(com).codes.astype(np.int64)
    A["pid"] = (cols.get_level_values("province_id").astype(int) - 1).to_numpy().astype(np.int64)
    A["n_com"], A["n_prov"] = int(A["cid"].max()) + 1, int(A["pid"].max()) + 1
    return A


def windows(A, t, s, L):
    lag = np.arange(-L + 1, 1)
    tt = np.clip(t[:, None] + lag[None, :], 0, None)
    ok = (t[:, None] + lag[None, :]) >= 0
    out = [np.where(ok, A["p"][tt, s[:, None]] - A["p"][t, s][:, None], 0.0)]
    for c in CHANNELS[1:]:
        out.append(np.where(ok, A["ch"][c][tt, s[:, None]], 0.0))
    return np.nan_to_num(np.stack(out, 1)).astype(np.float32)                   # N × C × L


def train_index(A, oi, L, max_n, rng):
    T, S = A["p"].shape
    t = np.arange(L - 1, oi + 1)
    tt, ss = (x.ravel() for x in np.meshgrid(t, np.arange(S), indexing="ij"))
    Y = np.stack([np.where(tt + h <= oi, A["y"][h][tt, ss], np.nan) for h in HS], 1)
    keep = np.isfinite(A["p_raw"][tt, ss]) & (np.isfinite(Y) & (Y != 0)).any(1)
    tt, ss, Y = tt[keep], ss[keep], Y[keep]
    if len(tt) > max_n:
        pick = rng.choice(len(tt), max_n, replace=False)
        tt, ss, Y = tt[pick], ss[pick], Y[pick]
    return tt, ss, Y


def fit(A, oi, hp, seed, dev):
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    tt, ss, Y = train_index(A, oi, hp["L"], hp["max_n"], rng)
    X = windows(A, tt, ss, hp["L"])
    xs = X.reshape(len(X), X.shape[1], -1).std(axis=(0, 2)) + 1e-6
    tab = A["tab"][tt, ss]
    mu, sd = np.nanmean(tab, 0), np.nanstd(tab, 0) + 1e-6
    scale = {"xs": xs, "mu": mu, "sd": sd}
    Xt = torch.from_numpy(X / xs[None, :, None]).to(dev)
    Tt = torch.from_numpy(np.nan_to_num((tab - mu) / sd).astype(np.float32)).to(dev)
    Yt = torch.from_numpy((np.nan_to_num(Y) > 0).astype(np.float32)).to(dev)
    Mt = torch.from_numpy((np.isfinite(Y) & (np.nan_to_num(Y) != 0)).astype(np.float32)).to(dev)
    C = torch.from_numpy(A["cid"][ss]).to(dev)
    Pv = torch.from_numpy(A["pid"][ss]).to(dev)
    net = TCNMTL(X.shape[1], Tt.shape[1], A["n_com"], A["n_prov"], hp["width"], hp["levels"], hp["k"], hp["drop"],
                 hp["use_tab"], hp["use_seq"]).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=hp["lr"], weight_decay=hp["wd"])
    bce = nn.BCEWithLogitsLoss(reduction="none")
    n = len(Xt)
    for _ in range(hp["epochs"]):
        net.train()
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, hp["batch"]):
            b = perm[i:i + hp["batch"]]
            loss = (bce(net(Xt[b], Tt[b], C[b], Pv[b]), Yt[b]) * Mt[b]).sum() / Mt[b].sum().clamp(min=1)
            opt.zero_grad()
            loss.backward()
            opt.step()
    net.eval()
    return net, scale


def predict(A, net, scale, t, s, hp, dev):
    X = windows(A, t, s, hp["L"]) / scale["xs"][None, :, None]
    tab = np.nan_to_num((A["tab"][t, s] - scale["mu"]) / scale["sd"]).astype(np.float32)
    with torch.no_grad():
        z = net(torch.from_numpy(X.astype(np.float32)).to(dev), torch.from_numpy(tab).to(dev),
                torch.from_numpy(A["cid"][s]).to(dev), torch.from_numpy(A["pid"][s]).to(dev))
    return torch.sigmoid(z).cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ext", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variant", default="tcn_tab", choices=["tcn", "tab", "tcn_tab"])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--refit", type=int, default=4)
    ap.add_argument("--smoke", action="store_true", help="uji cepat: data latih & epoch kecil")
    ap.add_argument("--until", default=None, help="hanya origin <= tanggal ini (mis. 2023-11-06 untuk pengembangan)")
    a = ap.parse_args()
    hp = {"L": 104, "width": 32, "levels": 5, "k": 3, "drop": 0.2, "lr": 1e-3, "wd": 1e-4, "epochs": 6, "batch": 1024,
          "max_n": 120_000, "use_seq": a.variant != "tab", "use_tab": a.variant != "tcn"}
    if a.smoke:
        hp.update(max_n=3000, epochs=1)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(a.out, exist_ok=True)
    tag = f"{a.variant}_r{a.seed}"
    ck = os.path.join(a.out, f"tcn_preds_{tag}.parquet")
    json.dump({"hp": hp, "variant": a.variant, "seed": a.seed, "device": dev}, open(os.path.join(a.out, f"tcn_hp_{tag}.json"), "w"))
    A = arrays(pd.read_parquet(a.ext))
    weeks = A["weeks"]
    widx = {w: i for i, w in enumerate(weeks)}
    last = weeks.max()
    ords = [o for o in pd.date_range(FIRST_ORIGIN, last - pd.Timedelta(weeks=min(HS)), freq=f"{STEP}W-MON")]
    if a.until:
        ords = [o for o in ords if o <= pd.Timestamp(a.until)]
    done = pd.read_parquet(ck) if os.path.exists(ck) else pd.DataFrame()
    have = set(done["origin"]) if len(done) else set()
    rows = [done] if len(done) else []
    for r0 in range(0, len(ords), a.refit):
        block = [o for o in ords[r0:r0 + a.refit] if o not in have]
        if not block:
            continue
        t0 = time.time()
        net, scale = fit(A, widx[ords[r0]], hp, a.seed * 1000 + r0, dev)
        for o in block:
            t = widx[o]
            s = np.where(np.isfinite(A["p_raw"][t]))[0]
            P = predict(A, net, scale, np.full(len(s), t), s, hp, dev)
            for j, h in enumerate(HS):
                y = A["y"][h][t, s]
                ok = np.isfinite(y)
                rows.append(pd.DataFrame({"origin": o, "horizon": h, "province_id": A["series"][s[ok]].get_level_values(0),
                                          "commodity": A["series"][s[ok]].get_level_values(1), "y_true": y[ok], "p_up": P[ok, j]}))
        pd.concat(rows, ignore_index=True).to_parquet(ck)                       # checkpoint tiap refit
        print(f"[tcn] {tag} refit {ords[r0].date()} ({len(block)} origin) {time.time() - t0:.1f} dtk", flush=True)
    print("[tcn] selesai", ck, flush=True)


if __name__ == "__main__":
    main()
