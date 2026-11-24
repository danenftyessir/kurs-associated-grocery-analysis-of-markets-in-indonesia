import sys; sys.path.insert(0, r"<EXP_DIR>")
from engine import *
import stage2
dp = pd.read_parquet('data/interim/deep_preds.parquet')
for h in (4, 8):
    dev = origin_list(h, 'dev')
    for m in ['TFM','TSMX','PTST','TFM_fx']:
        d = dp[(dp.model==m)&(dp.horizon==h)&dp.origin.isin(dev)]
        grid = np.quantile(d.y_pred, np.linspace(0.2, 0.8, 61))
        t, f = best_threshold(d.y_true.values, d.y_pred.values, grid)
        print(h, m, 'f1@0', round(macro_f1(d.y_true, d.y_pred, 0.0),4), 'best thr', round(t,4), round(f,4), 'share>thr', round((d.y_pred>t).mean(),3))
    for byc in (True, False):
        c = stage2.residual_calibrated(h, dev, 'TFM', by_commodity=byc)
        dd = dp[(dp.model=='TFM')&(dp.horizon==h)&dp.origin.isin(c.origin.unique())]
        print(h, 'resid-cal byc', byc, 'n_orig', c.origin.nunique(), 'f1@.5', round(macro_f1(c.y_true, c.p_up, .5),4),
              'raw TFM same origins', round(macro_f1(dd.y_true, dd.y_pred, 0),4),
              'brier', round(float(((c.p_up-(c.y_true>0))**2)[c.y_true!=0].mean()),4))
