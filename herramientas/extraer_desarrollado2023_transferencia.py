"""Extrae solo2023 desarrollado como fuente, con objetivos por periodo propios."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';RAW=ROOT/'Hackaton/Semana 1/Datos'
OUT=R/'privado/semana2/robustez2023/fuente_desarrollado2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(R/'src'))
import pyarrow.parquet as pq
import pandas as pd,numpy as np
from semana2.preparar_base import reconcile_exposure
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
SPECS={
 'motor':['driver_age','ncb_years','vehicle_age','vehicle_value_group','cover_type'],
 'buildings':['sum_insured','accidental_damage_cover'],
 'contents':['sum_insured','accidental_damage_cover','high_value_items']}
META=['row_id','policy_id','customer_id','address_id','period_start','period_end','exposure','new_business']


def main():
    assert not OUT.exists(),'Fuente aislada ya iniciada; conciliar antes de repetir'
    OUT.mkdir(parents=True)
    sources=[RAW/f'policies_{line}.parquet' for line in SPECS]+[RAW/'claims.parquet',RAW/'addresses.parquet',Path(__file__),R/'src/semana2/preparar_base.py']
    before={rel(p):sha(p) for p in sources}
    address=pq.read_table(RAW/'addresses.parquet',columns=['address_id','region','property_type','year_built','flood_zone','bedrooms']).to_pandas()
    assert address.address_id.is_unique
    start,end=datetime(2023,1,1),datetime(2024,1,1)
    periods=[];audit=[]
    for line,cols in SPECS.items():
        path=RAW/f'policies_{line}.parquet'
        f=pq.read_table(path,columns=META+cols,filters=[('period_start','>=',start),('period_start','<',end)]).to_pandas()
        assert pd.to_datetime(f.period_start).dt.year.eq(2023).all() and pd.to_datetime(f.period_end).dt.year.eq(2023).all()
        f=reconcile_exposure(f);f['market']='developed';f['line']=line;f['year']=2023;f['is_test']=False
        assert not f.duplicated(['market','line','row_id']).any()
        periods.append(f)
    claims=pq.read_table(RAW/'claims.parquet',columns=['claim_id','policy_id','line','peril','loss_date','report_date','status','incurred_to_date','recoveries'],filters=[('loss_date','>=',start),('loss_date','<',end)]).to_pandas()
    assert pd.to_datetime(claims.loss_date).dt.year.eq(2023).all()
    assert pd.to_datetime(claims.report_date).ge(pd.to_datetime(claims.loss_date)).all()
    assert pd.to_datetime(claims.report_date).le(pd.Timestamp('2024-12-31')).all()
    assert claims.claim_id.is_unique and claims.status.isin(['closed','open','repudiated']).all()
    j=claims.merge(pd.concat([f[['market','line','row_id','policy_id','period_start','period_end']] for f in periods]),on=['line','policy_id'],how='left')
    assigned=j[j.loss_date.ge(j.period_start)&j.loss_date.le(j.period_end)].copy()
    assert not assigned.claim_id.duplicated().any()
    missing=claims.loc[~claims.claim_id.isin(assigned.claim_id),['claim_id','line','policy_id','loss_date','status']].copy()
    missing.to_parquet(OUT/'source_claims_without2023_period.parquet',index=False)
    good=assigned[assigned.status.ne('repudiated')].copy()
    a=np.rint(good.incurred_to_date.to_numpy()*100);b=np.rint(good.recoveries.to_numpy()*100)
    assert np.max(np.abs(a-good.incurred_to_date.to_numpy()*100),initial=0)<=1e-6
    assert np.max(np.abs(b-good.recoveries.to_numpy()*100),initial=0)<=1e-6
    assert np.isfinite(a-b).all() and ((a-b)>=0).all()
    good['T0_cents']=(a-b).astype(np.int64)
    costs=good.groupby(['market','line','row_id']).T0_cents.sum().reset_index()
    for f in periods:
        line=f.line.iloc[0]
        f=f.merge(costs,on=['market','line','row_id'],how='left',validate='one_to_one').merge(address,on='address_id',how='left',validate='many_to_one',indicator=True)
        assert f['_merge'].eq('both').all()
        f['T0_cents']=f.T0_cents.fillna(0).astype(np.int64);f['T0']=f.T0_cents/100
        out=f[['market','line','row_id','policy_id','customer_id','address_id','year','is_test','period_start','period_end','exposure','T0','T0_cents']].copy()
        out['x_new_business']=pd.to_numeric(f.new_business)
        for name in ['region']+(['cover_type'] if line=='motor' else ['property_type','accidental_damage_cover']):out['x_'+name]=f[name].to_numpy()
        if line=='motor':
            age=pd.to_numeric(f.driver_age);assert age.between(17,110).all()
            out['x_driver_age_band']=pd.cut(age,bins=[16,24,34,49,64,np.inf],labels=['17-24','25-34','35-49','50-64','65+']).astype(str)
            for name in ['ncb_years','vehicle_age','vehicle_value_group']:out['x_'+name]=pd.to_numeric(f[name])
        else:
            cap=pd.to_numeric(f.sum_insured);limit=1e7 if line=='buildings' else 1e6
            # Pantalla fuente conservadora: capitales sospechosos quedan ausentes; no se usa prima ni se reestima CAPS emergente.
            cap=cap.where(np.isfinite(cap)&cap.gt(0)&cap.le(limit))
            out['x_log_sum_insured']=np.log(cap)
            if line=='buildings':
                age=2023-pd.to_numeric(f.year_built);out['x_property_age']=age.where(age.ge(0));out['x_flood_zone']=pd.to_numeric(f.flood_zone)
            else:
                out['x_bedrooms']=pd.to_numeric(f.bedrooms);out['x_high_value_items']=pd.to_numeric(f.high_value_items)
        assert out.x_new_business.isin([0,1]).all() and out.year.eq(2023).all() and out.market.eq('developed').all()
        assert int(out.T0_cents.sum())==int(good.loc[good.line.eq(line),'T0_cents'].sum())
        out.to_parquet(OUT/f'{line}_2023.parquet',index=False)
        audit.append({'line':line,'rows':len(out),'net_cost_cents':int(out.T0_cents.sum()),'positive_periods':int(out.T0.gt(0).sum()),'exposure':float(out.exposure.sum())})
    assert before=={rel(p):sha(p) for p in sources}
    report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','source_market':'developed','cohort_years':[2023],
        'source_valuation':'2024-12-31; claims occurrence2023 only, no policy2024','rows':audit,'claims2023':len(claims),
        'claims_without2023_period':len(missing),'source_target':'net observed incurred, not independently identified ultimate',
        'source_observation_exposure':'nominal reconciled exposure; market intercept profiles level, no source C0 borrowed from emerging',
        'source_does_not_increase_emerging_group_support':True,'new_model_fits':0,'new_C0_fits':0,'2024_policy_rows_read':0,
        'source_hashes':before,'outputs':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.glob('*.parquet'))]}
    with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ['rows','claims2023','claims_without2023_period','new_model_fits','2024_policy_rows_read']},ensure_ascii=False))


if __name__=='__main__':main()
