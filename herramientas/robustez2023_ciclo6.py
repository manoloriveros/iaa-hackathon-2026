"""Dos GLM físicos preinscritos; lectores estrictos y comparación OOF2023."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys,time,warnings
ROOT=Path('C:/dev/Hakaton');REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_profesor2023 as m
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
from sklearn.metrics import mean_tweedie_deviance
OUT=REPO/'privado/semana2/robustez2023/ciclo6_20261025_v1'
PLAN=REPO/'registro/semana2_robustez2023_ciclo6_plan.json'
BASE=REPO/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
OOF=REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
FID='COD-S2-20261025-ROBUSTEZ6-PREVIO'
now=lambda:datetime.now(timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x));f.write('\n')


def event(name,**kw):
    rec={'utc':now(),'event':name,**kw}
    with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
    print(json.dumps(rec,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),flush=True)


def synthetic():
    n=12000;rng=np.random.default_rng(744);line='motor'
    f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
    f['e_cost_mix_1.0']=f.exposure*.98
    for col in m.FEATURES[line]['numeric']:f[col]=rng.uniform(0,5,n)
    for col in m.FEATURES[line]['categorical']:f[col]=np.where(np.arange(n)%2,'A','B')
    f['x_new_business']=(np.arange(n)%2).astype(float)
    risk=.2+2*((f.x_ncb_years>2.5)&(f.x_vehicle_age>2.5));f['T0']=rng.poisson(risk,n)*rng.gamma(3,80,n)
    source=f.copy();source['market']='developed';source['T0']=rng.poisson(risk,n)*rng.gamma(3,240,n)
    train=f[f.fold.ne(0)].copy();valid=f[f.fold.eq(0)].copy();checks=[]
    with threadpool_limits(limits=2):
        teachers,note=m.fit_teachers(source,line)
        for mid,teacher in teachers.items():
            before=joblib.hash(teacher);rec={'id':mid,'synthetic':True,'_teacher':teacher}
            b,receipt=m.fit(train,line,0,rec);pred=m.predict(b,valid)
            assert np.array_equal(pred,m.predict(b,valid.assign(T0=1e12))) and joblib.hash(teacher)==before
            checks.append(mid+'_full_teacher_adapter_flow')
    for name,bad in [('source2024',source.assign(year=2024)),('source_market',source.assign(market='emerging'))]:
        try:m.fit_teachers(bad,line)
        except AssertionError:checks.append(name+'_rejected')
        else:raise AssertionError(name)
    dump(OUT/'synthetic.json',{'checks':checks,'synthetic_price_fits':4,'real_fits':0,'source_receipt':note,'last_adapter_receipt':receipt})


def prepare():
    assert not PLAN.exists() and not OUT.exists()
    OUT.mkdir(parents=True)
    sources=[BASE/f'{line}_fold{fold}.parquet' for line in m.FEATURES for fold in range(5)]
    sources += [OOF,Path(m.__file__),Path(m.base.__file__),Path(__file__),REPO/'registro/semana2_politica_seleccion_v1.json']
    sources += [REPO/f'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/{line}_2023.parquet' for line in m.FEATURES]+[REPO/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/report.json']
    sources += [REPO/'src/semana2/modelo_transferencia2023_v2.py',REPO/'src/semana2/modelos_robustos_compuestos2023.py']
    for p in sources[:15]:
        pf=pq.ParquetFile(p);schema=pf.schema_arrow
        y=pq.read_table(p,columns=['year','is_test']).to_pandas()
        assert y.year.eq(2023).all() and y.is_test.eq(False).all()
        needed={'T0','e_cost_mix_1.0','fold','group_id','customer_id','address_id'}
        assert needed<=set(schema.names)
    plan={'id':'S2-ROBUSTEZ2023-CICLO6-v1-20261025','author':'Codex','utc':now(),
        'authorization':'trabaja sin parar hasta tener un modelo mucho más robusto, con resultados significativamente mejores',
        'forum_prior':FID,'run':rel(OUT),'training_years':[2023],'heldout_years':[2023],
        'C0':'reuse exact current outer-fold inputs; no recalculation, no nested tuning',
        'folds':'same five connected-component folds; verify group/customer/address disjoint',
        'models':[{'id':'W2-COD-R31','shape':'source_GLM_teacher_with_target_adapter'}, {'id':'W2-COD-R32','shape':'source_GLM_residual_teacher_with_target_adapter'}],
        'hypothesis':'Pooled interactions overfit target and degrade; isolate shape estimation entirely in developed2023, then fit only intercept/new-business/region adapter inside emerging outer fit. Compare standard sourceGLM teacher to sourceGLM plus small fixed source-only tree correction.',
        'features':m.FEATURES,'excluded':['premium','claims_as_predictors','days_unoccupied','realized_climate','IDs','start_month','channel','payment_method','make_model'],
        'temporal_scope':'conditional benchmark with supplied period attributes, NOT historically timestamped prospective pricing; F02 limits retained. No 2024 cohort/metrics.',
        'numeric':'median then train-only clip0.005/0.995 then StandardScaler',
        'categorical':'drop first, min_frequency100,max_categories40,unknown ignore; learned fit-only',
        'Tweedie':{'power':1.5,'link':'log','max_iter':3000,'tol':1e-7,'response':'T0/C0','weight':'sqrt(C0)'},
        'comparators':['W2-B00','W2-B20'],'reference_preserved':'W2-B00','real_fit_budget':36,
        'primary_material_delta_D2_over_B20':.005,'lower_exploratory_bound_over_B20':.0005,
        'bootstrap':{'seed':2026102501,'replicates':2000,'quantiles':[.0041666666667,.9958333333333],'unit':'connected group; common null recalculated'},
        'stability':{'positive_folds_min':4,'max_segment_harm_over_full_null':.0005,'remove_favorable_group_fraction':.001,'delta_after_removal_min':.0005},
        'no_formal_promotion':True,'2024_closed':True,'no_auto_submission_from_training':True,
        'search_disclosure':'exploratory after B00-B20 and publicG4 result; bootstrap does not erase adaptive search',
        'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
    synthetic()
    dump(PLAN,plan);dump(OUT/'plan.json',plan)
    for p in [Path(m.__file__),Path(__file__)]:
        (OUT/p.name).write_bytes(p.read_bytes())
    print(json.dumps({'plan':rel(PLAN),'models':plan['models'],'fit_budget':30,'synthetic_checks':6}),flush=True)


def check_sources(plan):
    for p in plan['sources']:assert sha(ROOT/p['path'])==p['sha256'],p['path']


def run():
    plan=read(PLAN);check_sources(plan)
    assert (OUT/'forum_prior_receipt.json').exists()
    assert not (OUT/'started.json').exists(),'Concilia corrida anterior; no repetir fits'
    dump(OUT/'started.json',{'utc':now(),'pid':os.getpid(),'expected_real_fits':30})
    old=pq.read_table(OOF,filters=[('model_id','in',['W2-B00','W2-B20']),('year','=',2023)]).to_pandas()
    refs={mid:old[old.model_id.eq(mid)].sort_values(m.KEY).reset_index(drop=True) for mid in ['W2-B00','W2-B20']}
    assert len(refs['W2-B20'])==50094
    outputs=[];receipts=[];tv=[]
    for line in m.FEATURES:
        for fold in range(5):
            path=BASE/f'{line}_fold{fold}.parquet'
            block=m.FEATURES[line];rawcols=[x.replace('x_log_voluntary_excess','x_voluntary_excess').replace('x_log_compulsory_excess','x_compulsory_excess').replace('x_log_distance_to_river_km','x_distance_to_river_km') for x in block['numeric']+block['categorical']]
            cols=list(dict.fromkeys(m.KEY+['year','is_test','fold','group_id','customer_id','address_id','T0','n_positive','exposure','e_cost_mix_1.0','reserve','T1_reserve075','T1_reserve125','e_cost_mix_0.75','e_cost_mix_1.25','e_cost_mix_tail0.05','e_cost_mix_tail0.1']+rawcols))
            f=pq.read_table(path,columns=cols,filters=[('year','=',2023)]).to_pandas();m.guard(f,line)
            f=m.features(f,line);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].copy()
            for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
            valid_ref=refs['W2-B20'].loc[lambda x:x.line.eq(line)&x.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
            val=val.sort_values(m.KEY).reset_index(drop=True)
            assert val[m.KEY].equals(valid_ref[m.KEY])
            for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),valid_ref[c].to_numpy()),c
            for recipe in plan['models']:
                event('fit_started',model_id=recipe['id'],line=line,fold=fold)
                with threadpool_limits(limits=2):
                    bundle,rec=m.fit(fit,line,fold,recipe)
                    rates=m.predict(bundle,val);fitrates=m.predict(bundle,fit)
                dst=OUT/'models'/f"{recipe['id']}_{line}_fold{fold}.joblib";dst.parent.mkdir(exist_ok=True)
                joblib.dump(bundle,dst,compress=3)
                with threadpool_limits(limits=2):replay=m.predict(joblib.load(dst),val)
                assert np.array_equal(rates,replay)
                # El replay se hace con un objeto desde disco, sin fit posterior.
                rec.update(model_id=recipe['id'],replay_exact=True,fit_group_hash=hashlib.sha256('\n'.join(sorted(fit.group_id.unique())).encode()).hexdigest(),
                    valid_group_hash=hashlib.sha256('\n'.join(sorted(val.group_id.unique())).encode()).hexdigest())
                dump(dst.with_suffix('.json'),rec);receipts.append(rec)
                o=valid_ref.copy();o['model_id']=recipe['id'];o['annual_rate']=rates;o['prediction']=rates*val['e_cost_mix_1.0'].to_numpy();o['unit_deviance']=m.unit_deviance(o.T0,o.prediction);outputs.append(o)
                for role,part,rate in [('fit',fit,fitrates),('validation',val,rates)]:
                    tv.append({'model_id':recipe['id'],'line':line,'fold':fold,'role':role,**m.metrics(part.assign(prediction=rate*part['e_cost_mix_1.0']))})
                event('fit_complete',model_id=recipe['id'],line=line,fold=fold,completed_fits=len(receipts))
    oof=pd.concat(outputs,ignore_index=True).sort_values(['model_id']+m.KEY).reset_index(drop=True)
    assert len(oof)==2*50094 and not oof.duplicated(['model_id']+m.KEY).any()
    oof.to_parquet(OUT/'new_oof_2023.parquet',index=False)
    dump(OUT/'training_receipts.json',receipts);dump(OUT/'train_validation.json',tv)
    summaries=[];segments=[];pairs=[];sens=[]
    parts={**refs,**{x['id']:oof[oof.model_id.eq(x['id'])].sort_values(m.KEY).reset_index(drop=True) for x in plan['models']}}
    base=refs['W2-B20'];codes,groups=pd.factorize(base.group_id,sort=True);g=len(groups)
    n=np.bincount(codes,minlength=g);ys=np.bincount(codes,weights=base.T0,minlength=g);roots=np.bincount(codes,weights=np.sqrt(base.T0),minlength=g)
    losses={mid:np.bincount(codes,weights=p.unit_deviance,minlength=g) for mid,p in parts.items()}
    fullnull=m.metrics(base)['null_deviance_sum']
    for mid,part in parts.items():
        summaries.append({'model_id':mid,**m.metrics(part)})
        labels={'line':part.line.astype(str),'fold':part.fold.astype(str),'business':np.where(part.x_new_business.eq(1),'new','renewal'),'line_business':part.line.astype(str)+'_'+np.where(part.x_new_business.eq(1),'new','renewal')}
        for dim,lab in labels.items():
            for name,cell in part.assign(label=lab).groupby('label',observed=True):segments.append({'model_id':mid,'dimension':dim,'label':str(name),**m.metrics(cell)})
        for target,exposure in [('T1_reserve075','e_cost_mix_0.75'),('T1_reserve125','e_cost_mix_1.25'),('T0','e_cost_mix_tail0.05'),('T0','e_cost_mix_tail0.1')]:
            sens.append({'model_id':mid,'target':target,'effective_exposure':exposure,**m.metrics(part.assign(stress=part.annual_rate*part[exposure]),prediction='stress',target=target)})
    boot={r['id']:[] for r in plan['models']};rng=np.random.default_rng(plan['bootstrap']['seed']);drawsha=hashlib.sha256()
    for start in range(0,2000,32):
        draws=rng.integers(0,g,size=(min(32,2000-start),g));drawsha.update(draws.tobytes())
        null=8*(np.sqrt(n[draws].sum(axis=1)*ys[draws].sum(axis=1))-roots[draws].sum(axis=1))
        for mid in boot:boot[mid].extend(((losses['W2-B20'][draws].sum(axis=1)-losses[mid][draws].sum(axis=1))/null).tolist())
    gates=[]
    for recipe in plan['models']:
        mid=recipe['id'];adv=losses['W2-B20']-losses[mid];keep=np.ones(g,bool);k=max(5,int(np.ceil(.001*g)));keep[np.argsort(-adv,kind='stable')[:k]]=False
        remaining_null=8*(np.sqrt(n[keep].sum()*ys[keep].sum())-roots[keep].sum())
        q=np.quantile(boot[mid],plan['bootstrap']['quantiles']);delta=float(adv.sum()/fullnull)
        foldrows=[];harms=[]
        for dim in ['fold','line_business']:
            c=[x for x in segments if x['model_id']==mid and x['dimension']==dim]
            for cell in c:
                b=next(x for x in segments if x['model_id']=='W2-B20' and x['dimension']==dim and x['label']==cell['label'])
                change=(b['deviance_sum']-cell['deviance_sum'])/fullnull
                if dim=='fold':foldrows.append(change)
                else:harms.append({'segment':cell['label'],'delta_over_full_null':change})
        after=float(adv[keep].sum()/remaining_null)
        pair={'candidate':mid,'reference':'W2-B20','delta_D2':delta,'exploratory_interval':q.tolist(),
              'removed_favorable_groups':k,'delta_after_removal':after,'positive_folds':sum(x>0 for x in foldrows),
              'segment_deltas_over_full_null':harms,'adaptive_search_disclosed':True}
        pairs.append(pair)
        checks={'material_gain':delta>=.005,'lower_bound':q[0]>.0005,'four_folds':sum(x>0 for x in foldrows)>=4,
                'segment_harm':min(x['delta_over_full_null'] for x in harms)>=-.0005,'not_few_groups':after>=.0005}
        gates.append({'model_id':mid,'checks':checks,'all_pass':all(checks.values()),'formal_promotion':False})
    check_sources(plan)
    report={'id':plan['id'],'utc':now(),'author':'Codex','new_price_fits':sum(x['price_estimator_fits'] for x in receipts)+6,'source_teacher_fits':6,'target_adapter_fits':30,'new_C0_fits':0,
            'summaries':summaries,'pairs':pairs,'gates':gates,'segments':segments,'sensitivity':sens,
            'bootstrap_draws_sha256':drawsha.hexdigest(),'plan_sha256':sha(PLAN),'2024_closed':True,'B00_preserved':True,
            'promotion':False,'public_score_used_for_parameters':False,'new_submissions':0}
    dump(OUT/'report.json',report)
    dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]})
    event('complete',summary=summaries,gates=gates)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
    if a.action=='prepare':prepare()
    else:run()
