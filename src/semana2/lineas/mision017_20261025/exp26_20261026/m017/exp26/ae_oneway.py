import pandas as pd, numpy as np
P='/home/claude/m017/oof/pred'; DE='/home/claude/m017/datos/emerging'
lab=pd.read_parquet('/home/claude/m017/base_etiquetas.parquet')
cu=pd.read_parquet(f'{DE}/customers.parquet'); ad=pd.read_parquet(f'{DE}/addresses.parquet')
def kopt(y,m): return np.sum(y/np.sqrt(m))/np.sum(np.sqrt(m))
VARS={'motor':['gender','driver_age_band','region','channel','previous_insurer','cover_type','payment_method','urban_density','vehicle_use','overnight_parking','fuel_type','marital_status'],
      'buildings':['gender','policyholder_age_band','region','channel','previous_insurer','construction_type','occupancy','property_type','soil_type','flood_zone','urban_density','marital_status'],
      'contents':['gender','policyholder_age_band','region','channel','previous_insurer','tenure','security_level','property_type','urban_density','flood_zone','marital_status']}
rows=[]
for l in ['motor','buildings','contents']:
    pol=pd.read_parquet(f'{DE}/policies_{l}.parquet').merge(cu,on='customer_id',how='left').merge(ad,on='address_id',how='left')
    pr=pd.concat([pd.read_parquet(f'{P}/dev/T2b_{l}.parquet'),pd.read_parquet(f'{P}/hold/T2b_{l}.parquet')])
    df=pol.merge(pr,on='row_id').merge(lab[['row_id','y','c_fila','year']],on='row_id')
    df['m']=df.mu*df.c_fila
    for yr in (2023,2024):
        i=df.year==yr; df.loc[i,'m']*=kopt(df.y[i],df.m[i])
    df['n']=0
    for v in VARS[l]:
        if v not in df: continue
        g=df.assign(v=df[v].astype(str)).groupby(['v','year']).agg(A=('y','sum'),E=('m','sum'),rows=('y','size'),pos=('y',lambda s:(s>0).sum())).reset_index()
        g=g.pivot(index='v',columns='year')
        for lv,r in g.iterrows():
            rows.append(dict(line=l,var=v,level=lv,rows23=r[('rows',2023)],pos23=r[('pos',2023)],ae23=r[('A',2023)]/r[('E',2023)],pos24=r[('pos',2024)],ae24=r[('A',2024)]/r[('E',2024)]))
r=pd.DataFrame(rows); r.to_csv('ae_oneway.csv',index=False)
pd.set_option('display.width',220); pd.set_option('display.max_rows',500)
r=r[(r.pos23>=30)&(r.pos24>=30)]
r['both']=np.sign(r.ae23-1)==np.sign(r.ae24-1)
print(r.round(3).to_string())
