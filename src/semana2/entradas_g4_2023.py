"""Ingreso de datos reales2023, sin estimadores, C0 calculado ni inferencia.

Prueba el ámbito en el footer antes de decodificar columnas. Los lectores de
ajuste solo abren archivos de los folds permitidos. No admite cachés exteriores.
"""
from pathlib import Path
from datetime import date,datetime
import hashlib,json
from numbers import Integral
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .ambitos_c0_b20_2023 import KEY,membership_digest,select_scope

KEY=list(KEY)
META=KEY+['year','is_test','fold','group_id','customer_id','address_id','policy_id']
STATIC=['x_new_business','x_property_age','x_flood_zone','x_accidental_damage_cover','x_property_type','x_region']
READS=[]

def require(ok,message):
    if not bool(ok):raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def safe_path(root,relative):
    root=Path(root).resolve();p=(root/relative).resolve()
    require(p.is_relative_to(root),'Ruta fuera del workspace')
    parts={x.lower() for x in p.parts}
    require(not parts.intersection({'models','test','sel01','actas','ledger','2024'}),'Ruta de modelo,confirmación o año cerrado')
    require(not p.name.lower().startswith(('oof_','prediction','score','ledger')),'No leer predicciones o scores como entrada')
    require(p.suffix=='.parquet','Solo Parquet de entradas declaradas')
    return p

def footer_proof(path,columns,kind='prepared',expected_fold=None):
    with pq.ParquetFile(path) as pf:
        names=pf.schema_arrow.names
        require(set(columns).issubset(names),'Faltan columnas de entrada')
        proof=[]
        for i in range(pf.num_row_groups):
            rg=pf.metadata.row_group(i)
            if rg.num_rows==0:continue
            needed=['period_start','period_end'] if kind=='raw_periods' else ['year']
            if 'is_test' in names:needed.append('is_test')
            if expected_fold is not None:needed.append('fold')
            for name in needed:
                require(name in names,'Falta columna para probar ámbito: '+name)
                stat=rg.column(names.index(name)).statistics
                require(stat is not None and stat.has_min_max and stat.null_count==0,'Ámbito no acreditado por estadísticas: '+name)
                low,high=stat.min,stat.max
                if name=='year':require(low==high==2023,'Archivo mixto o ajeno a2023; no decodificar')
                elif name=='is_test':require(low is False and high is False,'Test o flag no acreditado')
                elif name=='fold':require(low==high==expected_fold,'Archivo de otro fold')
                else:
                    a,b=pd.Timestamp(low),pd.Timestamp(high)
                    require(a.year==b.year==2023,'Fecha fuera de2023 en footer')
                proof.append({'row_group':i,'column':name,'min':str(low),'max':str(high)})
        return {'rows':pf.metadata.num_rows,'row_groups':pf.num_row_groups,'columns_requested':columns,'proof':proof}

def read_pinned(root,spec,columns=None,expected_fold=None):
    path=safe_path(root,spec['path']);cols=spec['columns'] if columns is None else columns
    require(set(cols).issubset(spec['columns']),'Lectura fuera de whitelist')
    require(sha(path)==spec['sha256'],'Fuente modificada; no decodificar')
    proof=footer_proof(path,cols,spec.get('kind','prepared'),expected_fold)
    READS.append({'path':spec['path'],'columns':cols,'fold':expected_fold,'rows':proof['rows']})
    frame=pq.read_table(path,columns=cols).to_pandas()
    if 'year' in frame:require(frame.year.eq(2023).all(),'Fila ajena a2023')
    if 'is_test' in frame:require(frame.is_test.eq(False).all(),'Fila test')
    return frame,proof

def validate_membership(meta):
    require(set(META).issubset(meta.columns) and len(meta)>0,'Metadatos incompletos')
    require(meta[META].notna().all().all(),'Metadatos ausentes')
    require(meta.market.eq('emerging').all() and meta.line.isin(['motor','buildings','contents']).all(),'Mercado o ramo ajeno')
    require(meta.year.eq(2023).all() and meta.is_test.map(lambda x:isinstance(x,(bool,np.bool_)) and not x).all(),'Solo2023, sin test')
    require(meta.fold.map(lambda x:isinstance(x,Integral) and not isinstance(x,bool) and x in range(5)).all(),'Fold no entero0..4')
    for col in KEY+['group_id','customer_id','address_id','policy_id']:
        require(meta[col].map(lambda x:isinstance(x,str) and bool(x.strip())).all(),'ID no textual/vacío')
    require(not meta.duplicated(KEY).any(),'Claves compuestas repetidas')
    for col in ['group_id','customer_id','address_id']:
        require(meta.groupby(col,dropna=False).fold.nunique().le(1).all(),'Cruce de folds en '+col)
    for col in ['customer_id','address_id']:
        require(meta.groupby(col,dropna=False).group_id.nunique().le(1).all(),'Componente partido en '+col)
    return membership_digest(meta.to_dict('records'))

def build_frames(inputs):
    meta=pd.concat([inputs[line][META] for line in ['motor','buildings','contents']],ignore_index=True).sort_values(KEY).reset_index(drop=True)
    validate_membership(meta)
    base=inputs['buildings'].sort_values(KEY).reset_index(drop=True)
    f=inputs['static'].sort_values(KEY).reset_index(drop=True)
    require(np.array_equal(base[KEY].to_numpy(object),f[KEY].to_numpy(object)),'Características y pertenencias no coinciden')
    for name in ['policy_id','customer_id','address_id','fold','group_id']:
        require(base[name].eq(f[name]).all(),'Linaje discrepante: '+name)
    for name in ['period_start','period_end']:
        require(pd.to_datetime(base[name]).eq(pd.to_datetime(f[name])).all(),'Fechas discrepantes')
    require(np.array_equal(base.exposure.to_numpy(float),f.exposure.to_numpy(float)),'Exposición preparada discrepante')
    raw=inputs['raw'].copy();raw['market']='emerging';raw['line']='buildings';raw=raw.sort_values(KEY).reset_index(drop=True)
    require(np.array_equal(raw[KEY].to_numpy(object),base[KEY].to_numpy(object)) and not raw.duplicated(KEY).any(),'Raw2023 no coincide')
    for name in ['policy_id','customer_id','address_id']:
        require(raw[name].eq(base[name]).all(),'Raw con clave distinta')
    for name in ['period_start','period_end']:
        require(pd.to_datetime(raw[name]).eq(pd.to_datetime(base[name])).all(),'Raw con fecha distinta')
    require(np.array_equal(raw.new_business.to_numpy(float),base.x_new_business.to_numpy(float)),'Nuevo negocio distinto')
    require(np.array_equal(raw.accidental_damage_cover.to_numpy(float),f.x_accidental_damage_cover.to_numpy(float)),'AD distinto')
    periods=base[META+['period_start','period_end','exposure']].copy()
    for name in STATIC:periods[name]=f[name].to_numpy()
    require(np.isfinite(periods.exposure.to_numpy(float)).all() and periods.exposure.gt(0).all(),'Exposición preparada no positiva/finita')
    require(pd.to_datetime(periods.period_end).ge(pd.to_datetime(periods.period_start)).all(),'Periodo invertido')
    for name in ['x_new_business','x_accidental_damage_cover']:require(periods[name].isin([0.,1.]).all(),'Indicador contractual inválido')
    require('x_log_sum_insured' not in periods and not any(c.startswith('e_cost') for c in periods),'No copiar capital aprendido/C0')
    capital=base[META].copy();capital['sum_insured_original']=raw.sum_insured.to_numpy()
    capital['written_premium_audit_only']=raw.written_premium.to_numpy();capital['exposure_supplied_raw_audit_only']=raw.exposure.to_numpy()
    target=base[META].copy();target['T0_observed_source']=f.T0.to_numpy(float)
    cents=np.rint(target.T0_observed_source.to_numpy()*100)
    require(np.isfinite(cents).all() and (cents>=0).all() and np.all(np.abs(cents-target.T0_observed_source.to_numpy()*100)<=1e-6),'T0 no interpretable en centavos')
    target['T0_cents']=cents.astype('int64')
    cc=inputs['claims'].copy()
    require(cc.claim_id.map(lambda x:isinstance(x,str) and bool(x.strip())).all(),'claim_id no textual/vacío')
    require(cc.year.eq(2023).all() and pd.to_datetime(cc.loss_date).dt.year.eq(2023).all(),'Siniestro fuera de ocurrencia2023')
    require(not cc.duplicated(['market','line','claim_id']).any(),'Siniestro duplicado')
    require(cc.included_in_T0.map(lambda x:isinstance(x,(bool,np.bool_))).all(),'Bandera de inclusión no booleana')
    cc=cc.merge(base[META+['period_start','period_end']].rename(columns={'is_test':'period_is_test'}),on=KEY,how='left',suffixes=('','_p'),validate='many_to_one',indicator=True)
    require(cc['_merge'].eq('both').all(),'Siniestro sin periodo')
    for name in ['year','fold','group_id','policy_id']:require(cc[name].eq(cc[name+'_p']).all(),'Siniestro con '+name+' discrepante')
    cc['fold']=cc.fold_p.astype('int64');cc['year']=cc.year_p.astype('int64')
    cc['is_test']=cc.period_is_test
    selected=cc.included_in_T0.eq(True)
    rejected=cc.loc[~selected,inputs['claims'].columns].copy()
    accepted=cc.loc[selected].copy()
    loss=pd.to_datetime(accepted.loss_date);report=pd.to_datetime(accepted.report_date)
    require(loss.dt.tz is None and report.dt.tz is None and loss.eq(loss.dt.normalize()).all() and report.eq(report.dt.normalize()).all(),'Fechas de siniestro con hora/zona')
    require(loss.ge(pd.to_datetime(accepted.period_start)).all() and loss.le(pd.to_datetime(accepted.period_end)).all(),'Ocurrencia fuera de cobertura')
    require(report.ge(loss).all() and report.le(pd.Timestamp('2024-12-31')).all(),'Reporte fuera de valoración')
    require(np.isfinite(accepted.T0_cents.to_numpy(float)).all() and accepted.T0_cents.ge(0).all() and accepted.T0_cents.eq(np.floor(accepted.T0_cents)).all(),'Centavos de siniestro inválidos')
    accepted['T0_cents']=accepted.T0_cents.astype('int64')
    # Conserva T0 heredado; esta suma solo concilia las nuevas entradas.
    total=accepted.groupby(KEY).T0_cents.sum().rename('claim_sum').reset_index()
    check=target.merge(total,on=KEY,how='left',validate='one_to_one');require(check.T0_cents.eq(check.claim_sum.fillna(0)).all(),'T0 heredado y siniestros no concilian')
    columns=KEY+['claim_id','policy_id','year','is_test','fold','group_id','included_in_T0','loss_date','report_date','peril','T0_cents']
    accepted=accepted[columns].sort_values(KEY+['claim_id']).reset_index(drop=True)
    return {'metadata':meta,'periods':periods,'targets':target,'capital_audit':capital,'claims':accepted,'excluded_claim_audit':rejected}

def make_scopes(metadata,fold_files):
    validate_membership(metadata);scopes={}
    from itertools import combinations
    for excluded in [[i] for i in range(5)]+[list(x) for x in combinations(range(5),2)]:
        fit,protected=select_scope(metadata.to_dict('records'),excluded)
        key='exclude_'+'_'.join(map(str,excluded));allowed=sorted(set(range(5))-set(excluded))
        files=[{'fold':i,**fold_files[str(i)]} for i in allowed]
        scopes[key]={'excluded_folds':excluded,'training_folds':allowed,'training_rows':len(fit),'protected_rows':len(protected),
            'fit_membership_sha256':membership_digest(fit),'protected_membership_sha256':membership_digest(protected),
            'training_files':files,'training_input_sha256':digest({'membership':membership_digest(fit),'files':files}),
            'learned_capital_parameters_present':False,'C0_present':False,'learned_objects_present':False}
    return scopes

def load_training_scope(root,manifest,excluded):
    excluded=sorted(excluded);key='exclude_'+'_'.join(map(str,excluded))
    require(key in manifest['scopes'],'Ámbito no declarado')
    scope=manifest['scopes'][key];meta,_=read_pinned(root,manifest['metadata'])
    validate_membership(meta);selected,_=select_scope(meta.to_dict('records'),excluded)
    require(membership_digest(selected)==scope['fit_membership_sha256'],'Pertenencia cambiada')
    out={name:[] for name in ['periods','targets','claims','capital_audit']}
    for file_set in scope['training_files']:
        require(file_set['fold'] not in excluded,'Archivo protegido en la lista de ajuste')
        for name in out:
            frame,_=read_pinned(root,file_set[name],expected_fold=file_set['fold']);out[name].append(frame)
    out={k:pd.concat(v,ignore_index=True).sort_values(KEY).reset_index(drop=True) for k,v in out.items()}
    expected={tuple(x[k] for k in KEY) for x in selected}
    require(set(map(tuple,out['periods'][KEY].itertuples(index=False,name=None)))==expected,'Filas de ajuste incompletas')
    for name,f in out.items():require(not f.fold.isin(excluded).any(),'Fold protegido materializado en '+name)
    out.update(cohort_metadata=meta,scope=scope,model_input_ready=False,capital_parameters_required=True,C0_present=False)
    return out

def masked_periods_for_future_C0(data):
    """Solo esquema para futuro C0: valores permitidos y metadatos protegidos."""
    meta=data['cohort_metadata'];p=data['periods']
    return meta.merge(p[KEY+['period_start','period_end','exposure']],on=KEY,how='left',validate='one_to_one')

def apply_frozen_capital(data,parameters=None):
    """No estima referencias. Requiere parámetros futuros del MISMO ámbito."""
    require(parameters is not None,'Capital no preparado para GLM: faltan parámetros de ámbito, no estimados aquí')
    require(parameters['training_input_sha256']==data['scope']['training_input_sha256'] and parameters['excluded_folds']==data['scope']['excluded_folds'],'Parámetros de capital de otro ámbito')
    require(parameters['threshold']==10000000. and 0<parameters['ppm_min']<=parameters['ppm_max'],'Regla de capital incompatible')
    p=data['periods'].merge(data['capital_audit'][KEY+['sum_insured_original','written_premium_audit_only']],on=KEY,validate='one_to_one')
    cap=p.sum_insured_original.to_numpy(float);prem=p.written_premium_audit_only.to_numpy(float)
    valid=np.isfinite(cap)&(cap>0)
    suspect=valid&(cap>parameters['threshold']);ppm=np.divide(1000*prem,cap,out=np.full(len(cap),np.nan),where=valid)
    passed=suspect&(ppm<parameters['ppm_min'])&(ppm*1000>=parameters['ppm_min'])&(ppm*1000<=parameters['ppm_max'])
    cleaned=np.where(valid,np.where(suspect,np.where(passed,cap/1000,np.nan),cap),np.nan)
    result=p[META+['period_start','period_end','exposure']+STATIC].copy();result['x_log_sum_insured']=np.log(cleaned)
    return result
