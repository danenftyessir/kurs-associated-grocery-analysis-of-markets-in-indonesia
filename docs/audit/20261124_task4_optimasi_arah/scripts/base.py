import pandas as pd, numpy as np
def mf1(y, s, thr=0.0):
    k = np.isfinite(y) & np.isfinite(s) & (y != 0) & (s != thr)
    up, pu = y[k] > 0, s[k] > thr
    tp=(up&pu).sum(); fn=(up&~pu).sum(); fp=(~up&pu).sum(); tn=(~up&~pu).sum()
    f1u=2*tp/(2*tp+fp+fn); f1d=2*tn/(2*tn+fn+fp)
    return (f1u+f1d)/2, k.sum()
dp=pd.read_parquet('data/interim/direction_preds.parquet').assign(s=lambda d:d.p_up-0.5)
dd=pd.read_parquet('data/interim/deep_preds.parquet').rename(columns={'y_pred':'s'})
fp=pd.read_parquet('data/interim/forecast_preds.parquet').rename(columns={'y_pred':'s'})
a=pd.concat([dp.drop(columns='p_up'),dd,fp])
a['dev']=a.origin+pd.to_timedelta(a.horizon*7,'D')<=pd.Timestamp('2023-12-31')
a['test']=a.origin>=pd.Timestamp('2024-01-01')
rows=[]
for (h,m),g in a.groupby(['horizon','model']):
    if '_r' in m: continue
    r={'h':h,'model':m}
    for part in ['all','dev','test']:
        gg=g if part=='all' else g[g[part]]
        r[part],r['n_'+part]=mf1(gg.y_true.values,gg.s.values)
        r['no_'+part]=gg.origin.nunique()
    rows.append(r)
print(pd.DataFrame(rows).round(3).to_string())
t=a[a.test]; print('test share up h8', (t[(t.horizon==8)&(t.model=='M1')&(t.y_true!=0)].y_true>0).mean())
d=a[a.dev]; print('dev share up h8', (d[(d.horizon==8)&(d.model=='M1')&(d.y_true!=0)].y_true>0).mean())
