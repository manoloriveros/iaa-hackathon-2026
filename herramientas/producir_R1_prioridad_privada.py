"""Produccion R1 de la familia T2b auditada, con tronco fuente congelado.

Reusa las funciones numericas de validar_cadena_f3c (autor Codex, otro chat),
sin invocar sus productores. No reentrena arboles ni curvas de desarrollo.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, ast, importlib.util, json, os, subprocess, sys

R=Path(__file__).resolve().parents[1]; ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from threadpoolctl import threadpool_limits
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('r1_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
v=module('r1_verified_helpers',R/'herramientas/validar_cadena_f3c.py')
BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'produccion_R1_privada_20261027'
REVIEW=BASE/'revision_chat_documento_20261027'
PARENT=v.RUN
ACTIVE=R/'privado/validacion_cadena_f3c_A1_mezcla/20261027T175434Z'
PLAN=R/'registro/semana2_produccion_R1_privada_plan.json'
INDEX=R/'registro/semana2_produccion_R1_privada_actual.json'
F3C=R/'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
F3CSHA='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
L=v.LINES
def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,x):
    s=json.dumps(v.clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:f.write(s)
def post(body,identifier,subject):
    p=OUT/(identifier+'.md');p.write_text(body,encoding='utf8')
    r=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(p)],capture_output=True,text=True,encoding='utf8',check=True)
    return json.loads(r.stdout)
def no_native(*a,**kw):raise AssertionError('Native/source/CDF refit forbidden in R1 frozen-source consumer')
lgb.train=no_native;v.fit_source=no_native;v.curves=no_native
def paths():
    result=[Path(__file__),Path(v.__file__),PLAN,REVIEW/'policy_results.json',REVIEW/'policy_verification.json',REVIEW/'scenario_review.json',REVIEW/'policy_T2b.parquet',
        PARENT/'baseline_parameters.json',PARENT/'training2023.parquet',ACTIVE/'parameters_T2b.json',ACTIVE/'predictions_T2b.parquet',ACTIVE/'prepared.json',F3C]
    for line in L:
        result += [ACTIVE/'prepared'/f'emerging_{line}.parquet']
        result += [PARENT/'models/baseline'/f'{line}{suffix}' for suffix in ['.txt','_receipt.json','_raw.parquet']]
        result += [v.LEGACY/'datos/emerging'/f'test_{line}.parquet']
    result += [v.LEGACY/'datos/emerging'/f'{name}.parquet' for name in ['claims','customers','addresses','weather']]
    return result
def guard():
    frozen=w.read(OUT/'freeze.json')
    for name,sha in frozen['sources'].items():assert v.sha(ROOT/name)==sha,name
    assert v.sha(F3C)==F3CSHA
def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert w.read(REVIEW/'completion_receipt.json')['research_controls_pass']
    OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'candidate':'R1_T2b_frozen_source_2023_target2023_2024',
      'hypothesis':'The validated R1 all-line NB fallback avoids an unsupported own residual block where future business is concentrated, retaining supported renewal effects. No guaranteed private gain over F3c.',
      'research':'2024 adaptive; retrospective policy known before production. No further candidate/view/weight selection.',
      'production_mapping':{'source':'EXACT three frozen T2b source2021-23 Boosters, seed20261024, noF1; categories and mature cost CDF from audited parent. Do not replace with legacyF3c or refit source2024.',
        'target':'All emerging2023+2024 T0 at valuation2024-12-31; same component grouping and fivefold OOF nuisance-level/completion learner then same F2/shape/own and final cell levels as validated. No future inputs enter learning.',
        'completion':'Frozen source CDF; target peril weights learned within every historical train scope. Future ultimate q=1 exactly, annualrisk times exact inclusive exposure once; no clipped-age CDF for2025.',
        'quote':'All lines NB returns exactly frozen sin_factores final price; renewal returns frozen own-block final price. No extra portfolio normalization or public overlay.',
        'history':'Known notices only, report and loss before cutoff=min(inception,2025-01-01); 365day lookback before cutoff, no amounts/status. History starts2023. No quote-time snapshot claim.',
        'climate':'Supplied <=2023 address means as in source validation, no2024/25 climate. Single baseline remains uncertain.',
        'timing':'Source/target master snapshots and quote-time fields unresolved; reserves/ultimate and longpolicy/NB transport remain conditional.',
        'controls':'Full59202row backtest application parity; homogeneous observed-to-ultimate bridge; synthetic immutable parameters, subset/order/appended-batch, NB exact fallback; full109296historical targets/keys/group exclusions; all209063future IDs/order/finitepositive values; no mutation of B00/F3c.'},
      'cost':{'native_fits':0,'CDF_fits':0,'source_Boosters_loaded':3,'target_OOF_scopes':5,'target_final_scope':1,'closed_parameter_learner':1,'future_predictions':209063,'maximum_submissions':1},
      'admission':'Require all frozen-family/research/production controls, committed producer and dependency, exactCSV seal, current quota and no pending duplicate. One submission only if supported; preserve F3c and no manual final selection or public-driven tuning.',
      'failure':'Preserve outputs and diagnose failure, no silent alternate family/clip/rescale/search. No formal promotion or independent professional validation.'}
    dump(PLAN,plan)
    dump(OUT/'freeze.json',{'utc':utc(),'sources':{w.rel(p):v.sha(p) for p in paths()}})
    receipt=post('Codex. Registro la produccion R1 antes de aprender parametros destino o predecir2025. Se conserva EXACTO el tronco T2b ya validado (fuente2021–2023, tres arboles, categorias y curvas congelados), y se amplia el aprendizaje cerrado destino a2023–2024 con la misma receta/OOF por componentes. Negocio nuevo devuelve la base exacta; renovacion el bloque propio. No es el F3c antiguo de tres semillas/F1/constantes publicas. Ultimo futuro lleva q=1 y exposicion una vez. No nuevos arboles ni curvas ni eleccion de vistas. Historia limitada al corte conocido, clima<=2023. Validare paridad completa retenida y puente homogeneo, aplicacion por fila, parametros ajenos a futuro y CSV completo. Conservamos reservas, temporalidad y transporte NB como limites. Solo si pasan controles y cupo actual cabe un envio autorizado, sin seleccionar manualmente la final. Plan '+w.rel(PLAN)+' SHA '+v.sha(PLAN),'COD-S2-20261027-R1-PRODUCCION-PREVIO','R1: produccion de familia validada y control de negocio nuevo')
    dump(INDEX,{'author':'Codex','utc':utc(),'status':'registered_before_target_learning_and_future_prediction','plan':w.rel(PLAN),'plan_sha256':v.sha(PLAN),'forum':receipt,'output':w.rel(OUT),'submission_made':False})
    print(json.dumps({'registered':True,'plan_sha256':v.sha(PLAN)}),flush=True)
def apply(t,p):
    m=t.base.to_numpy(float).copy()
    for f in p['F2']:m=v.factor_apply(t,m,v.ks(t,f['variable']),f)
    m=v.shape_apply(t,m,p['shape']);ce=v.cells(t)
    baseline=m*np.array([p['levels']['sin_factores'][c] for c in ce]);r1=baseline.copy()
    j=t.new_business.eq(0).to_numpy();renewal=t.loc[j].reset_index(drop=True);own=m[j].copy()
    for f in p['own']:own=v.factor_apply(renewal,own,v.ks(renewal,f['variable']),f)
    r1[j]=own*np.array([p['levels']['F3c_reaprendido'][c] for c in ce[j]])
    assert t.new_business.isin([0,1]).all() and np.isfinite(r1).all() and (r1>0).all()
    return r1,baseline
def preflight():
    guard();assert not (OUT/'preflight.json').exists()
    cols=['row_id','line','new_business','exposure','q','base','ncb_years','prior_claims_5y','gender','works_from_home','marketing_segment']
    t=pd.read_parquet(ACTIVE/'predictions_T2b.parquet',columns=cols);p=w.read(ACTIVE/'parameters_T2b.json')['recipe']
    expected=pd.read_parquet(REVIEW/'policy_T2b.parquet').set_index('row_id').DOC_R1
    r,b=apply(t,p);truth=t.row_id.map(expected).to_numpy();checks={}
    checks['ALL59202_backtest_R1_exact']=np.array_equal(r,truth)
    checks['NB_exact_baseline']=np.array_equal(r[t.new_business.eq(1)],b[t.new_business.eq(1)])
    u=t.copy();u['base']=t.base/t.q;u['q']=1.;ultimate,_=apply(u,p)
    err=float(np.max(np.abs(ultimate-r/t.q)/np.maximum(ultimate,1e-30)))
    checks['ALL59202_homogeneous_ultimate_bridge']=err<3e-13
    # Synthetic/scalar fixtures use frozen real parameters, with no fitting.
    s=t.groupby(['line','new_business'],sort=True).head(3).copy().reset_index(drop=True)
    z,_=apply(s,p);reverse,_=apply(s.iloc[::-1],p);joined,_=apply(pd.concat([s,s],ignore_index=True),p)
    checks['permutation_and_appended_batch_exact']=np.array_equal(z,reverse[::-1]) and np.array_equal(joined,np.r_[z,z])
    checks['singleton_exact']=all(np.array_equal(apply(s.iloc[[i]],p)[0],z[i:i+1]) for i in range(len(s)))
    x=s.copy();x['base']*=2;x['exposure']*=2
    checks['double_exposure_double_price']=np.allclose(apply(x,p)[0],2*z,rtol=3e-14,atol=0)
    before=v.digest(p);x=s[s.new_business.eq(1)].copy();x[['gender','works_from_home','marketing_segment']]='UNUSED_NB_POISON'
    checks['NB_unused_own_inputs_ignored']=np.array_equal(apply(x,p)[0],z[s.new_business.eq(1)])
    checks['no_parameter_mutation']=v.digest(p)==before
    tr=pd.read_parquet(PARENT/'training2023.parquet');empty=tr.iloc[:0].copy()
    _,learned=v.recipe(tr,empty)
    checks['historical_learner_parameters_exact']=learned==w.read(PARENT/'baseline_parameters.json')['recipe']
    checks['all_passed']=all(checks.values());dump(OUT/'preflight.json',{'utc':utc(),'checks':checks,'max_bridge_relative_error':err,'native_or_CDF_fits':0,'closed_recipe_replay2023':1})
    assert checks['all_passed'],checks
    print(json.dumps(checks),flush=True)
def historical():
    return pd.concat([pd.read_parquet(ACTIVE/'prepared'/f'emerging_{line}.parquet') for line in L],ignore_index=True)
def learn():
    guard();assert w.read(OUT/'preflight.json')['checks']['all_passed'];assert not (OUT/'parameters.json').exists()
    em=historical();assert len(em)==109296 and em.row_id.is_unique and set(em.year)=={2023,2024}
    em['group'],em['fold']=v.components(em)
    assert em.groupby('address_id').fold.nunique().eq(1).all() and em.groupby('customer_id').fold.nunique().eq(1).all()
    raw=pd.concat([pd.read_parquet(PARENT/'models/baseline'/f'{line}_raw.parquet') for line in L]).set_index('row_id').raw
    assert raw.index.is_unique and set(raw.index)==set(em.row_id)
    F={ast.literal_eval(k):np.array(x) for k,x in w.read(PARENT/'baseline_parameters.json')['source_curves'].items()}
    oof=[];scopes=[];calls={'kopt':0,'factor_train':0,'shape_train':0,'completion':0,'recipe':0}
    for name in calls:
        original=getattr(v,name)
        def wrapped(*a,_name=name,_original=original,**kw):calls[_name]+=1;return _original(*a,**kw)
        setattr(v,name,wrapped)
    for fold in range(5):
        a,b,p=v.target_base(em,raw,F,em.fold.ne(fold),em.fold.eq(fold))
        assert not set(a.group)&set(b.group)
        oof.append(b);scopes.append({'fold':fold,'train_rows':len(a),'apply_rows':len(b),'disjoint':True,'parameters':p,
            'train_key_sha256':v.digest(a[['row_id','group']]),'apply_key_sha256':v.digest(b[['row_id','group']])})
    tr=pd.concat(oof).sort_values('row_id').reset_index(drop=True)
    _,params=v.recipe(tr,tr.iloc[:0].copy())
    _,_,full=v.target_base(em,raw,F,np.ones(len(em),bool),np.zeros(len(em),bool))
    # Parent completion uses the application only to integrate q. Empty application is valid.
    result={'utc':utc(),'recipe':params,'full_base':full,'target_folds':scopes,'historical_rows':len(em),
        'target_by_year':{str(k):{'rows':len(g),'cost':float(g.y.sum())} for k,g in em.groupby('year')},
        'historical_keys_sha256':v.digest(em[['row_id','group','fold']]),'target_sha256':v.digest(em[['row_id','y']]),
        'learning_calls':calls,'native_fits':0,'CDF_fits':0,'source_basis':'frozen_source2021_2023','future_rows_in_learner':0}
    tr[['row_id','group','fold','year','y','q','base']].to_parquet(OUT/'target_oof.parquet',index=False)
    dump(OUT/'parameters.json',result)
    print(json.dumps({'parameters_saved':True,'rows':len(em),'calls':calls,'native_fits':0}),flush=True)
def features():
    d=v.LEGACY/'datos/emerging';cu=pd.read_parquet(d/'customers.parquet');ad=pd.read_parquet(d/'addresses.parquet')
    cu['occupation']=cu.occupation.str.lower().str.strip().str.replace('self-employed ','',regex=False).str.strip()
    weather=pd.read_parquet(d/'weather.parquet');weather=weather[weather.year.le(2023)].groupby('address_id')[v.WEATHER].mean().add_prefix('clima_')
    frames=[]
    for line in L:
        t=pd.read_parquet(d/f'test_{line}.parquet');n=len(t);t['line']=line
        for col in ['period_start','period_end']:t[col]=pd.to_datetime(t[col])
        t['year']=t.period_start.dt.year;assert t.year.eq(2025).all()
        t['exposure']=((t.period_end-t.period_start).dt.days+1)/365.
        t=t.merge(cu,on='customer_id',how='left',validate='m:1',indicator='customer_join')
        t=t.merge(ad,on='address_id',how='left',validate='m:1',indicator='address_join')
        assert len(t)==n and t.customer_join.eq('both').all() and t.address_join.eq('both').all()
        t=t.drop(columns=['customer_join','address_join']).merge(weather,on='address_id',how='left',validate='m:1')
        t['tenure_years']=t.year-t.customer_since_year;t['property_age']=t.year-t.year_built
        t['start_month']=t.period_start.dt.month;t['full_year']=t.exposure.ge(.99).astype(int);t['log_days_quote']=np.log1p(t.days_quote_to_inception.clip(lower=0))
        t['age_band']=t.driver_age_band if line=='motor' else t.policyholder_age_band
        t['occupation']=t.occupation.str.lower().str.strip()
        if line!='motor':
            cap=5000000 if line=='buildings' else 2000000
            t['sum_insured']=np.where(t.sum_insured.gt(cap),t.sum_insured/1000,t.sum_insured);t['log_si']=np.log(t.sum_insured);t['ncb_years']=np.nan
        else:t['ncb_years']=pd.to_numeric(t.ncb_years)
        if line=='buildings':t['construction']=t.construction_type.str.lower().map(v.CONSTR);assert t.construction.notna().all()
        frames.append(t)
    base=pd.concat(frames,ignore_index=True);assert len(base)==209063 and base.row_id.is_unique
    c=pd.read_parquet(d/'claims.parquet')
    for col in ['report_date','loss_date']:c[col]=pd.to_datetime(c[col])
    assert c.report_date.le(pd.Timestamp(v.V)).all()
    hist=historical();mapping=pd.concat([hist,base])[['policy_id','line','customer_id']].drop_duplicates();assert not mapping.duplicated(['policy_id','line']).any()
    hc=c.merge(mapping,on=['policy_id','line'],how='inner',validate='m:1')
    base['history_cutoff']=base.period_start.clip(upper=pd.Timestamp('2025-01-01'))
    for kind,key in [('pol','policy_id'),('cli','customer_id')]:
        keys=[key,'line'] if kind=='pol' else [key]
        merged=base[['row_id','history_cutoff']+keys].merge((c if kind=='pol' else hc)[keys+['report_date','loss_date']],on=keys)
        cut=merged.history_cutoff
        merged=merged[merged.report_date.lt(cut)&merged.report_date.ge(cut-pd.Timedelta(days=365))&merged.loss_date.lt(cut)]
        n=base.row_id.map(merged.groupby('row_id').size()).fillna(0)
        base['hist_'+kind+'_12m']=n.where(base.history_cutoff-pd.Timedelta(days=365)>=pd.Timestamp('2023-01-01'),np.nan)
    return base
def quote():
    guard();assert not (OUT/'R1_T2b_2025.csv').exists()
    pars=w.read(OUT/'parameters.json');t=features();t['q']=1.;t['raw']=np.nan
    missing={};models=[]
    for line in L:
        mask=t.line.eq(line);cols=v.POLIZA+v.CLIENTE+v.DIRECCION+v.RAMO[line]
        receipt=w.read(PARENT/'models/baseline'/f'{line}_receipt.json');model=PARENT/'models/baseline'/f'{line}.txt'
        assert v.sha(model)==receipt['model_sha256'];b=lgb.Booster(model_file=str(model));models.append(b)
        x=v.matrix(t[mask],cols,receipt['full_categories'])
        t.loc[mask,'raw']=b.predict(x,raw_score=True,num_threads=2)
        # All historical rows, not a sample: frozen model replay agrees with cache.
        hist=historical();h=hist[hist.line.eq(line)];rh=b.predict(v.matrix(h,cols,receipt['full_categories']),raw_score=True,num_threads=2)
        cache=pd.read_parquet(PARENT/'models/baseline'/f'{line}_raw.parquet').set_index('row_id').raw
        assert np.array_equal(rh,h.row_id.map(cache).to_numpy())
        missing[line]={col:int(x[col].isna().sum()) for col in x}
    t['base']=np.array([pars['full_base'][line]['level'] for line in t.line])*np.exp(t.raw)*t.exposure
    t['prediction'],t['baseline']=apply(t,pars['recipe'])
    t[['row_id','line','new_business','exposure','history_cutoff','hist_pol_12m','hist_cli_12m','raw','q','base','baseline','prediction']].to_parquet(OUT/'production_quotes.parquet',index=False)
    order=pd.read_csv(F3C,usecols=['row_id']);assert set(order.row_id)==set(t.row_id)
    out=order.merge(t[['row_id','prediction']],on='row_id',how='left',validate='1:1')
    out.to_csv(OUT/'R1_T2b_2025.csv',index=False,float_format='%.6f')
    dump(OUT/'quote_receipt.json',{'utc':utc(),'rows':len(out),'csv_sha256':v.sha(OUT/'R1_T2b_2025.csv'),'parameters_sha256':v.sha(OUT/'parameters.json'),
        'missing_by_line':missing,'source_historical_raw_replay_ALL109296_exact':True,'native_fits':0,'CDF_fits':0,'ultimate_q_exactly_one':True,'no_portfolio_normalization':True})
    print(json.dumps({'quote_complete':True,'rows':len(out),'sha256':v.sha(OUT/'R1_T2b_2025.csv')}),flush=True)
def validate():
    guard();p=w.read(OUT/'parameters.json');t=pd.read_parquet(OUT/'production_quotes.parquet');csv=pd.read_csv(OUT/'R1_T2b_2025.csv');checks={}
    checks['rows_columns_IDs_order']=len(csv)==209063 and list(csv)==['row_id','prediction'] and csv.row_id.is_unique and csv.row_id.equals(pd.read_csv(F3C,usecols=['row_id']).row_id)
    checks['finite_positive_after_serialization']=np.isfinite(csv.prediction).all() and csv.prediction.gt(0).all()
    checks['rounding_only']=np.max(np.abs(csv.prediction-csv.row_id.map(t.set_index('row_id').prediction)))<=.000000501
    f=features();f=f.merge(t[['row_id','q','base']],on='row_id',validate='1:1');pred,base=apply(f,p['recipe'])
    checks['whole_feature_quote_replay_exact']=np.array_equal(pred,t.prediction.to_numpy()) and np.array_equal(base,t.baseline.to_numpy())
    checks['all_NB_exact_baseline']=np.array_equal(t.loc[t.new_business.eq(1),'prediction'],t.loc[t.new_business.eq(1),'baseline'])
    # Frozen output and exposure invariance over full file, source raw scores held fixed.
    rev=apply(f.iloc[::-1],p['recipe'])[0][::-1];checks['all_future_order_exact']=np.array_equal(pred,rev)
    checks['future_q_one_and_asof_cap']=t.q.eq(1).all() and t.history_cutoff.eq(pd.Timestamp('2025-01-01')).all()
    checks['frozen_source_no_new_native_CDF']=p['native_fits']==0 and p['CDF_fits']==0
    checks['F3c_bytes_preserved']=v.sha(F3C)==F3CSHA
    checks['all_passed']=all(checks.values())
    desc={line:{'rows':len(g),'sum':float(g.prediction.sum()),'min':float(g.prediction.min()),'median':float(g.prediction.median()),'max':float(g.prediction.max())} for line,g in t.groupby('line')}
    dump(OUT/'production_validation.json',{'utc':utc(),'checks':checks,'summary':desc,'csv_sha256':v.sha(OUT/'R1_T2b_2025.csv'),'new_native_or_CDF_fits':0,'independent_professional_review':False})
    assert checks['all_passed'],checks
    print(json.dumps({'all_passed':True,'rows':len(t),'csv_sha256':v.sha(OUT/'R1_T2b_2025.csv')}),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','preflight','learn','quote','validate']);args=parser.parse_args()
    with threadpool_limits(limits=2):globals()[args.mode]()
