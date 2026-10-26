import pandas as pd, numpy as np, statsmodels.api as sm, sys
T='/home/claude/ml2/trabajo'; D='/home/claude/ml2/datos'
W=['hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c']
mercado=sys.argv[1]
w=pd.read_parquet(f'{D}/{mercado}/weather.parquet')
wm=w[w.year<=2024].groupby('address_id')[W].mean()
for linea in ['motor','buildings','contents']:
    cols=None
    b=pd.read_parquet(f'{T}/base_{mercado}_{linea}.parquet')
    b=b[b.conjunto=='train'] if 'conjunto' in b else b
    per=[c for c in b.columns if c.startswith('y_')]
    b=b[['row_id','address_id','year','exposure','y']+per].copy(); b['year']=b.year.astype(int)
    b=b.merge(w,on=['address_id','year'],how='left').merge(wm.add_suffix('_m'),left_on='address_id',right_index=True,how='left')
    tot=b.y.sum()
    print(f'== {mercado} {linea} rows {len(b)} cost {tot:,.0f}')
    for p in per:
        sh=b[p].sum()/tot; n=(b[p]>0).sum()
        ind=(b[p]>0).astype(float)
        out=[]
        for v in W:
            X=pd.DataFrame({'s':b[v],'m':b[v+'_m']})
            for yy in sorted(b.year.unique())[1:]: X[f'y{yy}']=(b.year==yy).astype(float)
            X=sm.add_constant(X)
            try:
                m=sm.GLM(ind,X,family=sm.families.Poisson(),offset=np.log(b.exposure.clip(1e-4))).fit()
                if abs(m.tvalues['s'])>3 or abs(m.tvalues['m'])>3:
                    out.append(f"{v}: s {m.params['s']:+.4f} (z{m.tvalues['s']:+.1f}) m {m.params['m']:+.4f} (z{m.tvalues['m']:+.1f})")
            except Exception as e: out.append(str(e)[:50])
        print(f'  {p[2:]:18s} share {sh:.3f} n {n:6d} | '+' ; '.join(out))
