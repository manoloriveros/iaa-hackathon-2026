"""Tres CatBoost fuente conservadores y mezclas fijas; reutiliza C0 por componente."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import gc
import importlib.util
import json
import os
import sys
import subprocess
import time

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import catboost as cb
from threadpoolctl import threadpool_limits
from semana2 import fuente_f2_2024_cb as source
from semana2 import variables_ultimo as v
from semana2.fase2_2024_datos import sha,dump,BASE

OUT=R/'privado/semana2/mision017_fase2/tanda3_20261025_v3'
PARENT=source.PARENT
CV=OUT.parent/'tanda2_20261025_v1'
PLAN=R/'registro/semana2_mision017_fase2_tanda3_plan_v3.json'
rel=lambda p:p.relative_to(ROOT).as_posix()
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
CATS={'channel','payment_method','marital_status','age_band','occupation','urban_density','soil_type',
      'property_type','roof_type','energy_rating','body_type','transmission','fuel_type','cover_type',
      'overnight_parking','vehicle_use','construction','occupancy','tenure','security_level'}
CONFIG=dict(loss_function='Tweedie:variance_power=1.5',iterations=600,depth=5,learning_rate=.04,
    random_strength=0.,bootstrap_type='Bernoulli',subsample=.8,one_hot_max_size=8,max_ctr_complexity=1,
    border_count=64,boosting_type='Plain',leaf_estimation_iterations=3,leaf_estimation_method='Newton',
    thread_count=2,allow_writing_files=False,used_ram_limit='1536mb',rsm=.8,random_seed=2026102504)


def event(name,**kw):
    a={'utc':now(),'event':name,**kw}
    with (OUT/'events.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(a,default=float)+'\n');f.flush()
    print(json.dumps(a,default=float),flush=True)


def factor(y,m):return float(np.sum(y/np.sqrt(m))/np.sum(np.sqrt(m)))
def unit(y,m):return 4*y/np.sqrt(m)+4*np.sqrt(m)-8*np.sqrt(y)


def matrix(f,columns):
    X=pd.DataFrame(index=f.index)
    for c in columns:
        if c in CATS:X[c]=f[c].astype('string').fillna('__MISSING__').astype(str)
        else:X[c]=pd.to_numeric(f[c],errors='coerce').astype('float32')
    assert not np.isinf(X[[c for c in columns if c not in CATS]].to_numpy()).any()
    return X


def synthetic():
    rng=np.random.default_rng(506);n=500
    X=pd.DataFrame({'x':rng.normal(size=n),'cat':rng.choice(['a','b'],n)})
    y=rng.gamma(2,100,n)*(rng.random(n)<.2);e=rng.uniform(.05,1,n)
    scale=max(1000.,float(y.max())/1000);rate=factor(y,e)
    baseline=np.log(e*rate/scale)
    m=cb.CatBoostRegressor(loss_function='Tweedie:variance_power=1.5',iterations=20,depth=3,
        learning_rate=.03,l2_leaf_reg=10/np.sqrt(scale),thread_count=2,random_seed=11,
        allow_writing_files=False,verbose=False)
    m.fit(cb.Pool(X,label=y/scale,baseline=baseline,cat_features=['cat']))
    raw=m.predict(cb.Pool(X,cat_features=['cat']),prediction_type='RawFormulaVal')
    supplied=cb.Pool(X,baseline=baseline,cat_features=['cat'])
    withbase=m.predict(supplied,prediction_type='RawFormulaVal')
    # Pool stores baseline as float32; compare against that actual native input.
    native=supplied.get_baseline()[:,0]
    assert np.allclose(withbase,raw+native,atol=1e-12,rtol=0)
    mu=e*rate*np.exp(raw)
    assert np.allclose(unit(y,mu)/np.sqrt(scale),unit(y/scale,mu/scale),rtol=1e-10,atol=1e-10)
    file=OUT/'synthetic.cbm';m.save_model(str(file));loaded=cb.CatBoostRegressor();loaded.load_model(str(file))
    assert np.array_equal(raw,loaded.predict(cb.Pool(X,cat_features=['cat']),prediction_type='RawFormulaVal'))
    dump(OUT/'synthetic.json',{'pass':True,'pool_baseline_vs_manual_offset_identity':True,
        'native_baseline_dtype':str(native.dtype),'max_baseline_quantization':float(np.abs(native-baseline).max()),
        'Tweedie_units_homogeneity':True,'saved_model_exact_replay':True,'synthetic_price_fits':1,'contest_price_fits':0})


def register():
    assert not PLAN.exists()
    assert (OUT/'resume_manifest.json').exists()
    previous=OUT.parent/'tanda3_20261025_v2'
    proof=read(previous/'synthetic.json');assert proof['pass']
    # Unchanged model/offset component reuses its test; integration is validated on real data.
    dump(OUT/'synthetic_reuse.json',{'source':rel(previous/'synthetic.json'),'sha256':sha(previous/'synthetic.json'),
         'unchanged_components':['synthetic','matrix','CONFIG'],'new_real_price_fits':0})
    resume=read(OUT/'resume_manifest.json')
    for name,h in resume['files'].items():assert sha(OUT/name)==h
    assert read(PARENT/'replay_report.json')['all_pass']
    paths=[Path(__file__),Path(source.__file__),R/'src/semana2/variables_ultimo.py',
           CV/'oof_2023_2024.parquet',CV/'validation_v1/report.json',BASE/'partitions.parquet',
           source.OLD]+list(PARENT.glob('features_*.parquet'))+list(PARENT.glob('raw_rates_*.parquet'))+list(CV.glob('learning_*.json'))
    paths += [OUT/'resume_manifest.json']+[OUT/n for n in resume['files']]
    plan={'id':'S2-MISION017-FASE2-TANDA3-v3','author':'Codex','utc':now(),
        'execution_resume':resume,
        'hypothesis':'La transferencia LightGBM es la referencia más fuerte conciliada; los ajustes libres o por bandas no dieron una mejora robusta. Probar una familia estándar diversa, más regularizada que CB E15, con fuente ampliada a 2021–2024 y nivel emergente aprendido dentro de componentes 2023–2024.',
        'prior_adverse_evidence':['CB E15: fuente 2021–2023, depth6 lr.08 L2=3, pierde en emergente frente a T2b; no repetir ese ajuste.',
            'C18 propio: Ordered depth3/4 con GLM físico de 2023, no transfería robustamente.',
            'La tanda2 ganó solo .00142, inferior al umbral, y perdió al retirar31grupos favorables.'],
        'material_changes':'Fuente 2021–2024 completa; variables comunes del padre F2 reproducidas; depth5 lr.04 L2 original10; sin selección de rondas en etiquetas evaluadas. No es una repetición de los anteriores datos/configuraciones.',
        'prior_attempt':{'source_guard_failure':'274 prehistory claims in2020 were rejected before any curve or pricing fit; original historical CDF includes them. v2 preserves them for the CDF, never for period targets.','price_fits':0,'CDF_fits':0},
        'source_data':'Reconstruir fuente histórica F2 desde originales: clones exactos ya identificados fuera, periodos/días inclusivos, neto en centavos y curvas empíricas maduras de coste. Cotejar CDF, mezcla y T0 por año con preparacion.json histórico antes de ajustar.',
        'scope':'Toda la información histórica hasta diciembre2024 para la tarifa2025; CV emergente por componentes de ambos años. No es una validación prospectiva de 2024.',
        'models':{'Q1':'Solo CatBoost fuente con nivel por ramo aprendido en entrenamiento emergente',
            'Q2':'75%T2b+25%CB, cada tronco nivelado en entrenamiento y nuevo nivel de la mezcla aprendido allí',
            'Q3':'50%T2b+50%CB, misma regla; pesos fijos'},
        'reference':'N0 de tanda2 exacto; mantener B00, F2 y todas las alternativas',
        'CatBoost':{'version':cb.__version__,'params':CONFIG,'l2_leaf_reg':'10/sqrt(scale)',
            'scale':'max(1000,max(source_period_T0)/1000), fit source only; no clipping',
            'baseline':'log(source_e_cost*source_constant_rate/scale), no boost_from_average',
            'prediction':'source_constant_rate*exp(raw_model_without_pool_baseline)',
            'unit_reference':'https://catboost.ai/docs/en/concepts/loss-functions-regression'},
        'C0':'Consumir sin reestimar las15mezclas/75curvas por ámbito de tanda2; aplicar cada objeto tanto a las filas de entrenamiento como a las retenidas de ese fold. Ningún dato de etiquetas retenidas entra en niveles o mezclas.',
        'criterion':{'delta_min':.002,'lower95_gt':0.,'positive_folds_min':4,'min_cell_delta_full_null':-.001,
            'post31_nonnegative':True,'both_years_nonnegative':True},
        'bootstrap':{'replicates':2000,'seed':2026102504,'unit':'saved customer-address connected component','quantiles':[.025,.975]},
        'budget':{'price_estimator_fits':3,'price_fits_reused':1,'price_fits_new_this_execution':2,'source_empirical_CDF_reconstructions':15,'source_CDFs_reused_this_execution':15,'target_reporting_refits':0,
            'closed_form_price_levels':48,'new_source_mixtures':3,'submissions':0},
        'quality_limits':['Legacy capital normalization is replayed for parity, not newly certified in all cases.',
            'Undated profiles; conditional payment/discount snapshot; no contacts/outcome/premium identifiers as predictors.',
            'One2024valuation; maturity/tail/reserve assumptions remain conditional; no2025weather.',
            'No independent professional validation or formal v1 promotion.'],
        'sources':{rel(p):sha(p) for p in paths},'B00_preserved':True,'no_automatic_submission':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text(plan['hypothesis']+'\n\n'+plan['material_changes']+'\n\n'+
        '\n'.join(f'- {n}: {x}' for n,x in plan['models'].items())+'\n\n'+
        'Se conservan los resultados adversos anteriores de CatBoost; se cambia el ámbito y la configuración declarados, sin búsqueda de pesos. '+
        'El flujo sintético de unidades, offset y carga del modelo pasó antes de registrar. La documentación oficial recomienda escalar Tweedie en CPU: '+
        'https://catboost.ai/docs/en/concepts/loss-functions-regression .\n\n'+
        'Máximo tres nuevos estimadores de fuente y 48 constantes; cero reestimaciones del C0 emergente y cero envíos. '+
        'El constructor de fuente debe cotejar curvas, mezcla y etiquetas con su antecedente antes de entrenar. Criterios y hashes: '+rel(PLAN)+'.\n',encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261025-MISION017-FASE2-TANDA3-V3-PREVIO','--asunto','Fuente 2021–2024: CatBoost conservador y dos mezclas fijas','--cuerpo',str(body)],
        check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':sha(PLAN),'forum':json.loads(p.stdout)})
    print(json.dumps({'registered':rel(PLAN),'contest_fits':0}))


def run():
    plan=read(PLAN);assert read(OUT/'registration.json')['plan_sha256']==sha(PLAN)
    for p,h in plan['sources'].items():assert sha(ROOT/p)==h
    assert not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
    if not (source.OUT/'report.json').exists():source.prepare()
    datareport=read(source.OUT/'report.json');assert datareport['source_years']==[2021,2022,2023,2024]
    parts=pd.read_parquet(BASE/'partitions.parquet',filters=[('is_test','=',False)])
    target=pd.read_parquet(BASE/'target_T0_and_stresses.parquet',filters=[('is_test','=',False)])
    old=pd.read_parquet(CV/'oof_2023_2024.parquet').set_index('row_id');outputs=[]
    with threadpool_limits(limits=2):
        for line in source.LINES:
            path=source.OUT/f'{line}.parquet';assert sha(path)==datareport['outputs'][path.name]
            columns=next(z['source_columns'] for z in datareport['rows'] if z['line']==line)
            catcols=[c for c in columns if c in CATS]
            if (OUT/f'CB_{line}.cbm').exists():
                metadata=read(OUT/f'CB_{line}_metadata.json')
                assert metadata['source_sha256']==sha(path) and metadata['columns']==columns
                assert metadata['params']=={**CONFIG,'l2_leaf_reg':10/np.sqrt(metadata['scale'])}
                assert sha(OUT/f'CB_{line}.cbm')==metadata['model_sha256']
                initial=metadata['initial_source_rate'];model=cb.CatBoostRegressor()
                model.load_model(str(OUT/f'CB_{line}.cbm'))
                event('source_model_reused',line=line,new_price_fit_calls=0,sha256=metadata['model_sha256'])
            else:
                f=pd.read_parquet(path)
                assert f.market.eq('developed').all() and f.year.isin([2021,2022,2023,2024]).all()
                X=matrix(f,columns);y=f.T0.to_numpy(float);e=f.e_cost.to_numpy(float);initial=factor(y,e)
                scale=max(1000.,float(y.max())/1000);params={**CONFIG,'l2_leaf_reg':10/np.sqrt(scale)}
                model=cb.CatBoostRegressor(**params)
                event('fit_started',line=line,rows=len(f),scale=scale,source_years=[2021,2022,2023,2024])
                model.fit(cb.Pool(X,label=y/scale,baseline=np.log(e*initial/scale),cat_features=catcols),verbose=200)
                model.save_model(str(OUT/f'CB_{line}.cbm'))
                metadata={'line':line,'source_rows':len(f),'source_sha256':sha(path),'columns':columns,
                    'catcols':catcols,'initial_source_rate':initial,'scale':scale,'params':params,
                    'model_sha256':sha(OUT/f'CB_{line}.cbm'),'source_author':'Codex','source_feature_lineage':'Claude/F2, reconstructed and verified by Codex'}
                dump(OUT/f'CB_{line}_metadata.json',metadata)
                del f,X,y,e;gc.collect()
            t=pd.read_parquet(PARENT/f'features_{line}.parquet')
            Xt=None
            if (OUT/f'raw_CB_{line}.parquet').exists():
                cached=pd.read_parquet(OUT/f'raw_CB_{line}.parquet').set_index('row_id')
                assert set(cached.index)==set(t.row_id)
                annual=cached.annual_CB.reindex(t.row_id).to_numpy(float)
            else:
                Xt=matrix(t,columns)
                annual=initial*np.exp(model.predict(cb.Pool(Xt,cat_features=catcols),prediction_type='RawFormulaVal'))
                pd.DataFrame({'row_id':t.row_id,'annual_CB':annual}).to_parquet(OUT/f'raw_CB_{line}.parquet',index=False)
            assert np.isfinite(annual).all() and (annual>0).all()
            raw=pd.read_parquet(PARENT/f'raw_rates_{line}.parquet');t['annual_CB']=annual
            t=t.merge(raw[['row_id','annual_raw_T2b']],on='row_id',validate='one_to_one')
            t=t.merge(parts.loc[parts.line.eq(line),['row_id','fold','group_id']],on='row_id',validate='one_to_one')
            t=t.merge(target.loc[target.line.eq(line),['row_id','T0','reserve']],on='row_id',validate='one_to_one')
            t['exposure']=target.loc[target.line.eq(line)].set_index('row_id').exposure.reindex(t.row_id).to_numpy(float);t['is_test']=False
            for held in range(5):
                saved=read(CV/f'learning_{line}_fold{held}.json')['artifact'];c0=saved['C0']
                q=sum(w*v.average_completion(t,c0['curves'][p],'cost',1.) for p,w in c0['mixture'].items())
                e=t.exposure.to_numpy(float)*q;mask=t.fold.ne(held).to_numpy();ev=~mask;y=t.T0.to_numpy(float)
                kc=factor(y[mask],e[mask]*t.annual_CB.to_numpy()[mask]);kt=saved['k']
                rates={'N0':t.annual_raw_T2b.to_numpy(float)*kt,'Q1':t.annual_CB.to_numpy(float)*kc}
                levels={}
                for w,name in [(.25,'Q2'),(.5,'Q3')]:
                    mixed=(1-w)*rates['N0']+w*rates['Q1'];k=factor(y[mask],e[mask]*mixed[mask]);levels[name]=k;rates[name]=mixed*k
                out=t.loc[ev,['row_id','year','group_id','fold','new_business','exposure','T0','reserve']].copy();out['line']=line;out['e_cost']=e[ev]
                for name,rate in rates.items():out[name]=rate[ev]*e[ev]
                out['N0']=(t.annual_raw_T2b.to_numpy(float)[ev]*e[ev])*kt
                assert np.array_equal(out.N0.to_numpy(),old.loc[out.row_id,'N0'].to_numpy())
                outputs.append(out)
                dump(OUT/f'levels_{line}_fold{held}.json',{'CB_k':kc,'T2b_k':kt,'mixture_k':levels,
                    'C0_parent':rel(CV/f'learning_{line}_fold{held}.json'),'C0_parent_sha256':sha(CV/f'learning_{line}_fold{held}.json'),
                    'fit_row_ids':sorted(t.loc[mask,'row_id'].tolist()),'held_fold':held})
            event('line_complete',line=line,price_estimator_fits=1)
            del t,Xt,model;gc.collect()
    p=pd.concat(outputs,ignore_index=True);assert p.row_id.is_unique and len(p)==109296
    p.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
    y=p.T0.to_numpy(float);null=unit(y,np.full(len(y),y.mean())).sum()
    scores={name:float(1-unit(y,p[name].to_numpy(float)).sum()/null) for name in ['N0','Q1','Q2','Q3']}
    dump(OUT/'price_report.json',{'author':'Codex','utc':now(),'status':'prices_scored_validation_pending','scores':scores,
        'price_estimator_fits':3,'price_fits_reused':1,'price_fits_new_this_execution':2,'source_empirical_CDF_reconstructions':15,'source_CDFs_reused_this_execution':15,'target_reporting_refits':0,
        'closed_form_price_levels':48,'new_submissions':0,'B00_preserved':True,'goal_achieved':False})
    event('batch_complete',scores=scores)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args()
    try:register() if args.mode=='register' else run()
    except Exception as exc:
        if OUT.exists():
            with (OUT/f'failure_{args.mode}_{time.time_ns()}.json').open('x',encoding='utf8') as f:
                json.dump({'utc':now(),'type':type(exc).__name__,'error':str(exc)},f)
        raise
