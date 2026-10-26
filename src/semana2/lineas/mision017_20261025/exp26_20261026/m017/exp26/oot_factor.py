import pandas as pd, numpy as np, sys
P='/home/claude/m017/oof/pred'; DE='/home/claude/m017/datos/emerging'
lab=pd.read_parquet('/home/claude/m017/base_etiquetas.parquet')
cu=pd.read_parquet(f'{DE}/customers.parquet'); ad=pd.read_parquet(f'{DE}/addresses.parquet')
def kopt(y,m): return np.sum(y/np.sqrt(m))/np.sum(np.sqrt(m))
def d15(y,m): m=np.maximum(m,1e-12); return np.sum(4*y/np.sqrt(m)+4*np.sqrt(m)-8*np.sqrt(y))
def d2(y,m):
    c=kopt(y,np.ones(len(y))); return 1-d15(y,m)/d15(y,np.full(len(y),c))
K=float(sys.argv[1]) if len(sys.argv)>1 else 300
base=sys.argv[2] if len(sys.argv)>2 else 'T2b'
out=[]
data={}
for l in ['motor','buildings','contents']:
    pol=pd.read_parquet(f'{DE}/policies_{l}.parquet').merge(cu,on='customer_id',how='left').merge(ad,on='address_id',how='left')
    pr=pd.concat([pd.read_parquet(f'{P}/dev/{base}_{l}.parquet'),pd.read_parquet(f'{P}/hold/{base}_{l}.parquet')])
    df=pol.merge(pr,on='row_id').merge(lab[['row_id','y','c_fila','year']],on='row_id')
    df['m']=df.mu*df.c_fila
    df['occ']=df.occupation.astype(str).str.lower().str.replace('self-employed ','',regex=False).str.strip()
    df['selfemp']=df.occupation.astype(str).str.lower().str.contains('self-employed')
    for yr in (2023,2024):
        i=df.year==yr; df.loc[i,'m']*=kopt(df.y[i],df.m[i])
    data[l]=df
    cands=[c for c in ['gender','previous_insurer','region','campaign_code','branch_id','email_domain','marketing_segment','occ','selfemp','driver_age_band','policyholder_age_band','marketing_consent','document_preference','channel','payment_method','make_model','vehicle_colour','licence_points','household_size','marital_status'] if c in df]
    for v in cands:
        df['v']=df[v].astype(str)
        for tr,te in ((2023,2024),(2024,2023)):
            a=df[df.year==tr]; t=df[df.year==te]
            g=a.groupby('v').agg(A=('y','sum'),E=('m','sum'),n=('y',lambda s:(s>0).sum()))
            # credibility on claim count
            z=g.n/(g.n+K); f=(1+z*(g.A/g.E-1))
            ff=t.v.map(f).fillna(1.0).values
            mm=t.m.values*ff; mm*=kopt(t.y.values,mm)
            out.append(dict(line=l,var=v,tr=tr,levels=len(g),gain=d2(t.y.values,mm)-d2(t.y.values,t.m.values)))
r=pd.DataFrame(out)
p=r.pivot_table(index=['line','var'],columns='tr',values='gain').round(5)
p['min']=p.min(axis=1)
print(f'K={K} base={base}'); print(p.sort_values('min',ascending=False).to_string())
