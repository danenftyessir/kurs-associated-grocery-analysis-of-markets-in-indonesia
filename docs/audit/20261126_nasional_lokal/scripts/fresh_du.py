"""D-158 iterasi 2 — layar DU "kesegaran" (origin pengembangan): apakah sinyal kb_up_1 & breadth intraminggu tingkat kota menambah
informasi di luar keluarga intraminggu provinsi (iw_gap) dan sinyal nasional yang sudah dipakai?

Fitur kota baru (harga minggu t hingga Jumat; sama dengan ketersediaan harga provinsi):
  iwc(kota, t)  = log harga hari teramati terakhir minggu t − log rerata hari teramati minggu t
  kb_iw_up      = porsi kota (komoditas sama, nasional) dengan iwc > 0;  kb_iw_med = median iwc nasional
  kp_iw_up      = porsi kota di provinsi itu dengan iwc > 0;            kp_iw_med = median iwc kota provinsi
Residual C1t; korelasi parsial per komoditas terhadap CTRL = nat_dp_1, nat_dp_4, lag_dp_4, dev_ma13 dan CTRL+IW = CTRL + iw_gap +
rerata nasional iw_gap. → hasil/fresh_du.csv, EXP/fresh.parquet (kolom kota baru per baris tabel br)"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "20261126_task4_master_f1", "scripts"))
sys.path.insert(0, HERE)
from m_common import AUD, EXP, H, bh_fdr, np, official_c1t, pd, table  # noqa: E402
import kb_build as KBB  # noqa: E402

sys.path.insert(0, os.path.join(AUD, "20261125_crisp_du", "scripts"))
from du import screen  # noqa: E402

OUT = os.path.join(HERE, "..", "hasil")
FRESH = ["kb_iw_up", "kb_iw_med", "kp_iw_up", "kp_iw_med"]


def city_intraweek(daily):
    d = daily.sort_values(["commodity", "regency_id", "date"]).copy()
    d["week"] = d["date"] - pd.to_timedelta(d["date"].dt.dayofweek, unit="D")
    g = d.groupby(["commodity", "regency_id", "province_id", "week"])["price"]
    w = pd.DataFrame({"last": g.last(), "mean": g.mean()}).reset_index()
    w["iwc"] = np.log(w["last"]) - np.log(w["mean"])
    nat = w.groupby(["commodity", "week"])["iwc"].agg(kb_iw_up=lambda s: (s > 0).mean(), kb_iw_med="median").reset_index()
    prov = w.groupby(["province_id", "commodity", "week"])["iwc"].agg(kp_iw_up=lambda s: (s > 0).mean(), kp_iw_med="median").reset_index()
    return nat, prov


if __name__ == "__main__":
    br = table("br")
    daily = KBB.read_city_daily()
    nat, prov = city_intraweek(daily)
    f = br[["week", "province_id", "commodity"]].merge(nat, on=["commodity", "week"], how="left").merge(
        prov, on=["province_id", "commodity", "week"], how="left")
    fr = pd.concat([br, f[FRESH].set_index(br.index)], axis=1)
    fr["iw_gap_nat"] = fr.groupby(["commodity", "week"])["iw_gap"].transform("mean")
    fr.to_parquet(os.path.join(EXP, "fresh.parquet"))
    P = official_c1t("dev")
    P = P[P["y_true"] != 0].copy()
    P["r"] = (P["y_true"] > 0).astype(float) - P["score"]
    CT = ["nat_dp_1", "nat_dp_4", "lag_dp_4", "dev_ma13"]
    D = P.merge(fr[["week", "province_id", "commodity", "kb_up_1", "iw_gap", "iw_gap_nat"] + FRESH + CT].rename(columns={"week": "origin"}),
                on=["origin", "province_id", "commodity"], how="left")

    def partial(d, x, ctrl):
        out = pd.Series(np.nan, index=d.index)
        for _, g in d.groupby("commodity"):
            g = g.dropna(subset=[x] + ctrl)
            if len(g) < 50 or g[x].std() == 0:
                continue
            X = np.column_stack([np.ones(len(g)), g[ctrl].to_numpy(float)])
            b, *_ = np.linalg.lstsq(X, g[x].to_numpy(float), rcond=None)
            out.loc[g.index] = g[x].to_numpy(float) - X @ b
        return out

    rows = []
    for h in H:
        d = D[D["horizon"] == h].copy()
        for x in ["iw_gap", "iw_gap_nat", "kb_up_1"] + FRESH:
            rows.append({"horizon": h, "feature": x, "kind": "mentah", **screen(d, x, h)})
            for kind, ctrl in (("parsial_CTRL", CT), ("parsial_CTRL+IW", CT + ["iw_gap", "iw_gap_nat"])):
                if x in ("iw_gap", "iw_gap_nat") and kind == "parsial_CTRL+IW":
                    continue
                d[f"{x}__{kind}"] = partial(d, x, ctrl)
                rows.append({"horizon": h, "feature": x, "kind": kind, **screen(d, f"{x}__{kind}", h)})
    t = pd.DataFrame(rows)
    t["q_bh"] = np.nan
    for (h, kind), g in t.groupby(["horizon", "kind"]):
        ok = g["p"].notna()
        t.loc[g.index[ok], "q_bh"] = bh_fdr(g.loc[ok, "p"].to_numpy())
    t.round(4).to_csv(os.path.join(OUT, "fresh_du.csv"), index=False)
    pd.set_option("display.width", 220)
    print(t.pivot_table(index=["feature", "kind"], columns="horizon", values=["rho", "lo", "hi", "q_bh"]).round(3).to_string())
