import pandas as pd, numpy as np
T='/home/claude/ml2/trabajo'; D='/home/claude/ml2/datos'
res=[]
import sys
for mercado in sys.argv[1:]:
    w=pd.read_parquet(f'{D}/{mercado}/weather.parquet')
    for linea in ['motor','buildings','contents']:
        b=pd.read_parquet(f'{T}/base_{mercado}_{linea}.parquet')
        b=b[b.conjunto=='train'] if 'conjunto' in b else b
        perils=[c for c in b.columns if c.startswith('y_')]
        b['year']=b['year'].astype(int)
        yrs=sorted(b.year.unique())
        ws=w.rename(columns={c:c+'_s' for c in w.columns if c not in('address_id','year')})
        b=b.merge(ws,on=['address_id','year'],how='left')
        # other-year mean (all other years in data excluding same year, within 2023-2025 range of market)
        wm=w.groupby('address_id').mean(numeric_only=True).drop(columns='year')
        cnt=w.groupby('address_id').size()
        b=b.merge(wm.add_suffix('_all'),left_on='address_id',right_index=True,how='left')
        for v in ['hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c']:
            n=b.address_id.map(cnt)
            b[v+'_o']=(b[v+'_all']*n-b[v+'_s'])/(n-1)
            b[v+'_d']=b[v+'_s']-b[v+'_o']
        for p in perils:
            ind=(b[p]>0).astype(float)
            e=b.exposure
            for v in ['hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c']:
                # Poisson regression freq ~ exp(a + b1*other + b2*dev) with year FE, quick via statsmodels
                import statsmodels.api as sm
                X=pd.DataFrame({'o':b[v+'_o'],'d':b[v+'_d']})
                X=(X-X.mean())/X.std()
                for yy in yrs[1:]: X[f'y{yy}']=(b.year==yy).astype(float)
                X=sm.add_constant(X)
                try:
                    m=sm.GLM(ind,X,family=sm.families.Poisson(),offset=np.log(e.clip(1e-4))).fit()
                    res.append(dict(mercado=mercado,linea=linea,peril=p[2:],var=v,n=int(ind.sum()),b_other=m.params['o'],z_other=m.tvalues['o'],b_dev=m.params['d'],z_dev=m.tvalues['d']))
                except Exception as ex: print(ex)
r=pd.DataFrame(res)
r.to_csv('test_clima.csv',index=False)
pd.set_option('display.width',200)
print(r[(r.z_dev.abs()>3)|(r.z_other.abs()>3)].round(3).to_string())
