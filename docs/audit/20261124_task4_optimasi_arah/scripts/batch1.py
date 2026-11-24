import sys; sys.path.insert(0, r"<EXP_DIR>")
import stage2, report
from engine import origin_list
for h in (4, 8):
    c = stage2.residual_calibrated(h, origin_list(h, "all"), "TFM", by_commodity=False)
    c.to_parquet(fr"<EXP_DIR>/preds/tfmcal_h{h}.parquet")
spec = {"C1t": ("final_C1t_h{h}.parquet", "prob", "p_up"), "TFMcal": ("tfmcal_h{h}.parquet", "prob", "p_up")}
comps = [(("C1t", "default"), ("C1", "default")), (("C1t", "default"), ("C2", "default")), (("C1t", "default"), ("TFM", "default")),
         (("C1t", "dev"), ("C1", "dev")), (("C1t", "dev"), ("TFM", "dev")),
         (("TFMcal", "default"), ("TFM", "default")), (("TFMcal", "dev"), ("TFM", "dev")), (("TFM", "dev"), ("TFM", "default"))]
res, comp = report.main(spec, comps, r"<EXP_DIR>/batch1.md", r"<EXP_DIR>/batch1.json")
print(open(r"<EXP_DIR>/batch1.md", encoding="utf-8").read())
