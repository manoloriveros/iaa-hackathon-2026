"""Reconstruye las entradas históricas de T2b y coteja su forma; no ajusta ni puntúa."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(R/'src'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from semana2.fase2_2024_datos import sha,dump

OUT=R/'privado/semana2/mision017_fase2/linaje_T2b_v1'
RAW=ROOT/'Hackaton/Semana 2/Datos/emerging'
PLAN=R/'registro/semana2_mision017_padre_F2_replay_v1.json'
CATS={'channel','payment_method','marital_status','age_band','occupation','urban_density','soil_type',
      'property_type','roof_type','energy_rating','body_type','transmission','fuel_type','cover_type',
      'overnight_parking','vehicle_use','construction','occupancy','tenure','security_level'}
LINES=['motor','buildings','contents']
rel=lambda p:p.relative_to(ROOT).as_posix()


def register():
    assert not PLAN.exists()
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'purpose':'Reutilizar el padre T2b de F2 con autoría Claude y comprobar su forma numérica antes de nuevas pruebas. No cambiar precios ni elegir por scores.',
        'models':'modelos/prod/T2b, desarrollado 2021–2024; comparar sus tasas con OOF pcv 2023–2024 guardado.',
        'not_temporal_2023_to_2024':'Los modelos prod usan fuente desarrollada 2024; solo son admisibles para desarrollo con información disponible al inicio de 2025 y validación por grupos emergentes. No son una predicción prospectiva de 2024.',
        'acceptance':'En cada ramo y antiguo fold por cliente, mu_guardada/(exposición_nominal*exp(raw)) debe ser una constante positiva, variación relativa máxima <=1e-8. Reconstrucción de perfiles sin costes, sin clima 2025, historial con report_date anterior al inicio y ventana completa.',
        'source_implementation':'Código histórico inspeccionado, reimplementación explícita; no ejecutar scripts del archivo ni sus puntos de entrada.',
        'source_authorship':'Claude; reconstrucción y revisión propia por Codex, no revisión humana independiente.',
        'known_conditional_features':['maestros sin fecha','missed_payments_12m y discount_applied según instantánea provista','clima 2023–2024 como información histórica disponible al inicio de 2025'],
        'no_labels_read_for_predictors':True,'new_fits':0,'new_C0':0,'new_scores':0,'submissions':0,'B00_preserved':True,
        'code':{rel(Path(__file__)):sha(Path(__file__))},
        'parents':{rel(p):sha(p) for p in list((OUT/'modelos/prod').glob('T2b_*.txt'))+list((OUT/'pred/pcv').glob('T2b_*.parquet'))}}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Después del resultado adverso de la primera tanda, se concilia el padre ya entrenado de F2 antes de intentar sustituirlo. '+
        plan['acceptance']+'\n\n'+plan['not_temporal_2023_to_2024']+'\n\n'+
        'Autor original Claude; reconstrucción Codex. Cero ajustes, C0, scores o envíos nuevos. B00 y todas las alternativas se conservan. Plan: '+rel(PLAN)+'.\n',encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261025-MISION017-PADRE-F2-PREVIO','--asunto','Replay del padre de F2 antes de otra tanda: alcance 2025, sin ajuste','--cuerpo',str(body)],
        check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'replay_registration.json',{'plan_sha256':sha(PLAN),'forum':json.loads(p.stdout)})


def run():
    plan=json.loads(PLAN.read_text(encoding='utf8'))
    assert json.loads((OUT/'replay_registration.json').read_text())['plan_sha256']==sha(PLAN)
    for p,h in {**plan['code'],**plan['parents']}.items():assert sha(ROOT/p)==h
    assert not (OUT/'replay_started.json').exists()
    dump(OUT/'replay_started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    paths=[RAW/(n+'.parquet') for n in ['customers','addresses','weather','claims','policies_motor','policies_buildings','policies_contents']]
    before={rel(p):sha(p) for p in paths}
    cu=pd.read_parquet(RAW/'customers.parquet');ad=pd.read_parquet(RAW/'addresses.parquet')
    cu['occupation']=cu.occupation.str.lower().str.strip().str.replace('self-employed ','',regex=False).str.strip()
    weather=pd.read_parquet(RAW/'weather.parquet',filters=[('year','<=',2024)])
    assert not weather.year.gt(2024).any()
    cols=['wind_exposure_index','wildfire_index','rainfall_mm','mean_temperature_c']
    climate=weather.loc[weather.year.isin([2023,2024])].groupby('address_id')[cols].mean().add_prefix('clima_').reset_index()
    del weather
    # Only keys and report dates: no paid/incurred/reserve/target enters historical predictors.
    claims=pd.read_parquet(RAW/'claims.parquet',columns=['claim_id','policy_id','line','report_date'])
    claims['report_date']=pd.to_datetime(claims.report_date)
    raw={line:pd.read_parquet(RAW/f'policies_{line}.parquet') for line in LINES}
    mapping=pd.concat([f[['policy_id','customer_id']].assign(line=line) for line,f in raw.items()]).drop_duplicates(['policy_id','line'])
    cc=claims.merge(mapping,on=['policy_id','line'],validate='many_to_one')
    results=[]
    for line,frame in raw.items():
        f=frame.copy();f['period_start']=pd.to_datetime(f.period_start);f['period_end']=pd.to_datetime(f.period_end)
        f['year']=f.period_start.dt.year;assert f.year.isin([2023,2024]).all()
        f['exposure']=((f.period_end-f.period_start).dt.days+1)/365
        f=f.merge(cu,on='customer_id',validate='many_to_one').merge(ad,on='address_id',validate='many_to_one').merge(climate,on='address_id',validate='many_to_one')
        f['tenure_years']=f.year-f.customer_since_year;f['property_age']=f.year-f.year_built
        f['start_month']=f.period_start.dt.month;f['full_year']=(f.exposure>=.99).astype(int)
        f['log_days_quote']=np.log1p(f.days_quote_to_inception.clip(lower=0))
        f['age_band']=f['driver_age_band' if line=='motor' else 'policyholder_age_band']
        if line!='motor':
            limit=5e6 if line=='buildings' else 2e6
            f['sum_insured']=np.where(f.sum_insured>limit,f.sum_insured/1000,f.sum_insured)
            f['log_si']=np.log(f.sum_insured)
        if line=='buildings':
            f['construction']=f.construction_type.str.lower().map({'brk':'brick','stn':'stone','wod':'timber','mix':'non_standard'})
        ok=(f.period_start-pd.Timedelta(days=365))>=pd.Timestamp('2023-01-01')
        hp=claims.loc[claims.line.eq(line),['policy_id','report_date']].merge(f[['row_id','policy_id','period_start']],on='policy_id')
        hp=hp.loc[hp.report_date.lt(hp.period_start)&hp.report_date.ge(hp.period_start-pd.Timedelta(days=365))]
        hc=cc[['customer_id','report_date']].merge(f[['row_id','customer_id','period_start']],on='customer_id')
        hc=hc.loc[hc.report_date.lt(hc.period_start)&hc.report_date.ge(hc.period_start-pd.Timedelta(days=365))]
        f['hist_pol_12m']=f.row_id.map(hp.groupby('row_id').size()).fillna(0).where(ok,np.nan)
        f['hist_cli_12m']=f.row_id.map(hc.groupby('row_id').size()).fillna(0).where(ok,np.nan)
        model=lgb.Booster(model_file=str(OUT/f'modelos/prod/T2b_{line}.txt'))
        columns=model.feature_name();catcols=[c for c in columns if c in CATS]
        assert len(catcols)==len(model.pandas_categorical)
        X=f[columns].copy()
        for c in columns:
            if c in CATS:X[c]=pd.Categorical(X[c].astype('string'),categories=model.pandas_categorical[catcols.index(c)])
            else:X[c]=pd.to_numeric(X[c],errors='coerce').astype(float)
        annual=np.exp(model.predict(X,raw_score=True,num_threads=2))
        rates=pd.DataFrame({'row_id':f.row_id,'year':f.year,'customer_id':f.customer_id,'exposure_legacy':f.exposure,'annual_raw_T2b':annual})
        rates['legacy_fold']=[int(hashlib.sha256(('mlind_v1|'+c).encode()).hexdigest()[:16],16)%5 for c in rates.customer_id]
        old=pd.read_parquet(OUT/f'pred/pcv/T2b_{line}.parquet')
        z=rates.merge(old,on='row_id',validate='one_to_one');assert len(z)==len(f)
        z['k_old']=z.mu/(z.exposure_legacy*z.annual_raw_T2b)
        errors=[];levels=[]
        for fold,g in z.groupby('legacy_fold'):
            k=float(g.k_old.median());err=float(np.max(np.abs(g.k_old/k-1)));errors.append(err);levels.append({'fold':int(fold),'k':k,'max_relative_deviation':err})
        rates.to_parquet(OUT/f'raw_rates_{line}.parquet',index=False)
        # Expose the reconstructed covariates for a later explicitly scoped, grouped study.
        out=f[['row_id','customer_id','address_id','policy_id','year','period_start','period_end','exposure',*columns]].copy()
        out.to_parquet(OUT/f'features_{line}.parquet',index=False)
        results.append({'line':line,'rows':len(f),'levels':levels,'max_relative_deviation':max(errors),'pass':max(errors)<=1e-8})
    assert before=={rel(p):sha(p) for p in paths}
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'results':results,
        'all_pass':all(x['pass'] for x in results),'sources':before,'new_fits':0,'new_C0':0,'new_scores':0,'submissions':0,
        'feature_labels_read':False,'weather2025_loaded':False,'source_cutoff':'developed through 2024; scope is availability at start of 2025',
        'not_prospective_2024_evaluation':True,'source_author':'Claude','reviewer':'Codex',
        'remaining':'A correct component-heldout calibration/observation link over 2023–2024 is still needed; archived pcv did not prove it.',
        'outputs':{p.name:sha(p) for p in list(OUT.glob('raw_rates_*.parquet'))+list(OUT.glob('features_*.parquet'))}}
    dump(OUT/'replay_report.json',report)
    print(json.dumps({'all_pass':report['all_pass'],'results':results,'new_fits':0,'new_scores':0}))


if __name__=='__main__':
    register() if sys.argv[1]=='register' else run()
