import pandas as pd, numpy as np, statsmodels.api as sm, json
T='/home/claude/ml2/trabajo'; D='/home/claude/ml2/datos'; P='/home/claude/m017/oof/pred'
W=['hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c']
w=pd.read_parquet(f'{D}/emerging/weather.parquet')
lab=pd.read_parquet('/home/claude/m017/base_etiquetas.parquet')
def dev(y,m):
    m=np.maximum(m,1e-9); return 4*(y/np.sqrt(m))+4*np.sqrt(m)-8*np.sqrt(y) if False else 2*(np.where(y>0,y**0.5/(0.5*(-0.5))*0,0))
def d15(y,m):
    m=np.maximum(m,1e-9); return np.sum(4*y/np.sqrt(m)+4*np.sqrt(m)-8*np.sqrt(y))
def kopt(y,m): return np.sum(y/np.sqrt(m))/np.sum(np.sqrt(m))
out={}
base_model='T2b'
for linea in ['motor','buildings','contents']:
    b=pd.read_parquet(f'{T}/base_emerging_{linea}.parquet',columns=['row_id','address_id','year','conjunto'])
    b=b[b.conjunto=='train']
    pr=pd.concat([pd.read_parquet(f'{P}/dev/{base_model}_{linea}.parquet'),pd.read_parquet(f'{P}/hold/{base_model}_{linea}.parquet')])
    df=b.merge(pr,on='row_id').merge(lab[['row_id','y','c_fila','exposure','new_business']],on='row_id')
    df['year']=df.year.astype(int)
    df=df.merge(w,on=['address_id','year'],how='left')
    wo=w.copy(); wo['year']=wo.year.map({2023:2024,2024:2023,2025:2099})
    df=df.merge(wo.rename(columns={c:c+'_o' for c in W}),on=['address_id','year'],how='left')
    df['m0']=df.mu*df.c_fila
    res={}
    for tr,te in [(2023,2024),(2024,2023)]:
        a=df[df.year==tr]; t=df[df.year==te]
        mu_=a[W].mean(); sd=a[W].std()
        X=sm.add_constant((a[W]-mu_)/sd)
        m=sm.GLM(a.y,X,family=sm.families.Tweedie(var_power=1.5,link=sm.families.links.Log()),offset=np.log(a.m0)).fit()
        Xt=sm.add_constant((t[W]-mu_)/sd)
        adj=np.exp(Xt.values@m.params.values)
        # level-free comparison: rescale both by own Tweedie-optimal scalar
        m_base=t.m0*kopt(t.y,t.m0); m_new=t.m0*adj; m_new=m_new*kopt(t.y,m_new)
        null=d15(t.y,np.full(len(t),kopt(t.y,np.ones(len(t)))**1*1.0)*0+ (np.sum(np.sqrt(t.y))/len(t))**2) 
        # null: constant c minimizing deviance: c = (mean sqrt y ... ) use kopt with m=1
        c=kopt(t.y,np.ones(len(t))); null=d15(t.y,np.full(len(t),c))
        g=(d15(t.y,m_base)-d15(t.y,m_new))/null
        # level ratio implied: sum adj*m0 vs sum m0 on test
        res[f'{tr}->{te}']=dict(gain_D2=round(g,5), d2_base=round(1-d15(t.y,m_base)/null,5), coefs=dict(zip(['const']+W,np.round(m.params.values,4))), z=dict(zip(['const']+W,np.round(m.tvalues.values,2))), level_ratio=float(np.sum(adj*t.m0)/np.sum(t.m0)*np.exp(-m.params['const'])))
    out[linea]=res
    print(linea, json.dumps(res,indent=0))
json.dump(out,open('glm_clima.json','w'),indent=1)
