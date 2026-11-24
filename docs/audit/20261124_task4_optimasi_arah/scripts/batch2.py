import sys; sys.path.insert(0, r"<EXP_DIR>")
import report
spec = {"C1t": ("final_C1t_h{h}.parquet", "prob", "p_up"), "C2t": ("final_C2t_h{h}.parquet", "prob", "p_up"),
        "TFMhead": ("final_TFMhead_h{h}.parquet", "prob", "p_up"), "TFMcal": ("tfmcal_h{h}.parquet", "prob", "p_up")}
comps = [(("C2t", "default"), ("C1t", "default")), (("C2t", "default"), ("C2", "default")),
         (("TFMhead", "default"), ("TFM", "default")), (("TFMhead", "default"), ("C1t", "default")),
         (("TFMhead", "dev"), ("TFM", "dev"))]
res, comp = report.main(spec, comps, r"<EXP_DIR>/batch2.md", r"<EXP_DIR>/batch2.json")
print(res[res.model.isin(["C1t","C2t","TFMhead"])][["model","h","threshold","thr","macro_f1","macro_f1_lo","macro_f1_hi","f1_up","f1_down","mcc","roc_auc","pr_auc","coverage"]].round(4).to_string(index=False))
print(comp.round(4).to_string(index=False))
