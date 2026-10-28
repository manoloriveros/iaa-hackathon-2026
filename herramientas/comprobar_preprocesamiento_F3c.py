"""Cotejo de valores del preprocesamiento original, sin fit ni inferencia."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,gc,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import numpy as np
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=load('a1_feature_audit',R/'herramientas/ampliar_validacion_cadena_f3c.py')
legacy=R/'privado/reentrenamiento_completo_20261026/corrida/noche'
original=load('original_features_audit',legacy/'codigo/variables.py')
OUT=R/'privado/semana2/mision017_fase2/F3c_validacion_completa_20261027'
def values():
    assert not (OUT/'feature_value_parity.json').exists();records=[]
    for market,mk in [('developed','s1'),('emerging','s2')]:
        for line in ['motor','buildings','contents']:
            basepath=legacy/'salidas'/mk/f'base_{line}.parquet'
            base=pd.read_parquet(basepath,filters=[('year','==',2023)] if mk=='s1' else [('year','in',[2023,2024])])
            population=len(base)
            if mk=='s1':base=base.iloc[np.linspace(0,len(base)-1,min(5000,len(base))).astype(int)].copy()
            base=base.reset_index(drop=True);assert base.row_id.is_unique and base.year.le(2024).all()
            X,_,_=original.features(base,line,mk);X['exposure_model']=base.exposure_model.to_numpy();del _;gc.collect()
            p=a.RUN/'prepared'/f'{market}_{line}.parquet';now=pd.read_parquet(p,filters=[('row_id','in',base.row_id.tolist())]).set_index('row_id').loc[base.row_id].reset_index()
            new=a.a1_features(now,line);diff={}
            for col in new:
                assert col in X
                if col in a.CAT:bad=X[col].astype('string').fillna('missing').to_numpy()!=new[col].astype('string').fillna('missing').to_numpy()
                else:bad=~np.isclose(X[col].to_numpy(float),new[col].to_numpy(float),rtol=0,atol=1e-12,equal_nan=True)
                count=int(np.sum(bad))
                if count:diff[col]={'different_rows':count,'max_abs':float(np.nanmax(np.abs(X[col].to_numpy(float)-new[col].to_numpy(float)))) if col not in a.CAT else None}
            records.append({'market':market,'line':line,'rows_compared':len(base),'eligible_rows':population,'scope':'systematic5000source2023' if mk=='s1' else 'alltarget2023and2024','features_compared':len(new.columns),'mismatches':diff,'row_key_digest':hashlib.sha256(json.dumps(base.row_id.tolist(),separators=(',',':')).encode()).hexdigest(),'original_feature_code_sha256':a.v.sha(Path(original.__file__))})
            print(json.dumps(records[-1]),flush=True);del X,new,now,base;gc.collect()
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'records':records,'all_passed':all(not z['mismatches'] for z in records),'model_inferences':0,'native_fits':0,'2025_rows_read':0,'source_sample_not_all_source_rows':True,'code_sha256':a.v.sha(Path(__file__))}
    with (OUT/'feature_value_parity.json').open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2)
    assert result['all_passed'],'Original/temporal feature preprocessing discrepancy; preserve receipt and investigate before claiming equivalence.'

def metadata():
    old=a.v.read(OUT/'feature_value_parity.json');records=[];schemas=a.v.read(OUT/'original18_source_schemas.json')['records']
    for rec in old['records']:
        mk='s1' if rec['market']=='developed' else 's2';base=pd.read_parquet(legacy/'salidas'/mk/f'base_{rec["line"]}.parquet',columns=['row_id','year'],filters=[('year','==',2023)] if mk=='s1' else [('year','in',[2023,2024])])
        if mk=='s1':base=base.iloc[np.linspace(0,len(base)-1,min(5000,len(base))).astype(int)]
        assert len(base)==rec['rows_compared'];features=next(x['feature_count'] for x in schemas if x['line']==rec['line'] and x['family']=='N0')
        records.append({**rec,'features_compared':features,'row_key_digest':hashlib.sha256(json.dumps(base.row_id.tolist(),separators=(',',':')).encode()).hexdigest()})
    result={**old,'utc':datetime.now(timezone.utc).isoformat(),'records':records,'metadata_correction_only':True,'previous_receipt_sha256':a.v.sha(OUT/'feature_value_parity.json'),
        'reason':'len(DataFrame) originally recorded rows instead of columns. Object-array tobytes digest was nonportable and is replaced with SHA of canonical JSON IDs. Neither item was used to compare values. Values are not recomputed.','code_sha256':a.v.sha(Path(__file__))}
    with (OUT/'feature_value_parity_corrected_metadata.json').open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'metadata_corrected_without_new_value_comparison':True,'features_by_line':{line:next(x['features_compared'] for x in records if x['line']==line) for line in ['motor','buildings','contents']},'zero_value_discrepancies':result['all_passed']}),flush=True)

def history():
    f=load('history_producer_audit',R/'herramientas/validar_F3c_completo.py');records=[]
    for market,mk in [('developed','s1'),('emerging','s2')]:
        for line in ['motor','buildings','contents']:
            cols=['row_id','policy_id','period_start','year'];cut=2023 if mk=='s1' else 2024
            original_rows=pd.read_parquet(legacy/'salidas'/mk/f'base_{line}.parquet',columns=cols,filters=[('year','<=',cut)]);original_rows['period_start']=pd.to_datetime(original_rows.period_start)
            query=original_rows[original_rows.year.eq(2023)] if mk=='s1' else original_rows
            if mk=='s1':query=query.iloc[np.linspace(0,len(query)-1,min(5000,len(query))).astype(int)]
            query=query.reset_index(drop=True);first=original_rows.groupby('policy_id').period_start.min();years=((query.period_start-query.policy_id.map(first)).dt.days/365.25).to_numpy()
            ec=['policy_id','report_date','accepted'];old_events=pd.read_parquet(legacy/'salidas'/mk/'asignacion.parquet',columns=ec,filters=[('line','==',line),('accepted','==',True)])
            old_events=old_events[old_events.policy_id.isin(query.policy_id)];events={p:np.sort(pd.to_datetime(g.report_date).to_numpy('datetime64[ns]')) for p,g in old_events.groupby('policy_id')}
            counts=np.array([np.searchsorted(events.get(p,np.array([],dtype='datetime64[ns]')),np.datetime64(start,'ns'),side='left') for p,start in query[['policy_id','period_start']].itertuples(index=False,name=None)],float)
            prepared=pd.read_parquet(a.RUN/'prepared'/f'{market}_{line}.parquet',columns=cols,filters=[('year','<=',cut)]);prepared['period_start']=pd.to_datetime(prepared.period_start)
            idx=prepared.groupby('policy_id').period_start.idxmin();anchors=prepared.loc[idx];anchors=anchors[anchors.policy_id.isin(query.policy_id)]
            q=prepared.set_index('row_id').loc[query.row_id].reset_index();small=pd.concat([q,anchors[~anchors.row_id.isin(q.row_id)]],ignore_index=True)
            new_events=pd.read_parquet(a.RUN/'prepared'/f'{market}_claims.parquet',columns=ec,filters=[('line','==',line),('accepted','==',True)])
            new_count,new_years=f.history(small,new_events);n_diff=int(np.sum(new_count[:len(q)]!=counts));y_diff=int(np.sum(~np.isclose(new_years[:len(q)],years,rtol=0,atol=1e-12)))
            records.append({'market':market,'line':line,'rows_compared':len(query),'source_sample_not_all_rows':mk=='s1','claim_history_discrepancies':n_diff,'history_duration_discrepancies':y_diff,'method':'Original accepted-assignment reports counted by sorted-date left search; actual producer history on query plus first-inception anchors, full original earliest-inception durations.','2025_rows_materialized':0})
            print(json.dumps(records[-1]),flush=True);del original_rows,query,first,old_events,events,prepared,anchors,small,q,new_events;gc.collect()
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'records':records,'all_passed':all(z['claim_history_discrepancies']==z['history_duration_discrepancies']==0 for z in records),'new_fits':0,'model_inference':0,'accepted_status_availability_vintage_unproven':True,'code_sha256':a.v.sha(Path(__file__))}
    with (OUT/'F1_history_value_parity.json').open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2)
    assert result['all_passed'],'F1 history discrepancy; preserve before claiming equivalence.'

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('mode',choices=['values','metadata','history']);args=p.parse_args();globals()[args.mode]()
