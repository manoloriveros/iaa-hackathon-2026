"""Cotejo separado de datos, recetas, replay y métricas OOF. No importa el productor."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import os
import sys
import uuid

for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='2'
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import d2_tweedie_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from threadpoolctl import threadpool_limits

KEY=['market','line','row_id']
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def forbid_fit(*args,**kwargs):
    raise AssertionError('Se prohíbe entrenar en el comprobador de replay')


def dev(y,mu):
    # Expresión general de la familia p; diferente implementación del productor.
    p=1.5;y=np.asarray(y,dtype=float);mu=np.asarray(mu,dtype=float)
    return 2*(y**(2-p)/((1-p)*(2-p))-y*mu**(1-p)/(1-p)+mu**(2-p)/(2-p))


def safe_read(path):
    return pq.read_table(path,filters=[('year','=',2023)]).to_pandas()


def predict(bundle,frame):
    assert frame.year.eq(2023).all() and not frame.is_test.any()
    if bundle['family']=='constant_line_rate':return np.full(len(frame),bundle['rate'])
    x=frame[bundle['columns']].copy()
    if bundle['family']=='TweedieRegressor':return bundle['estimator'].predict(bundle['transformer'].transform(x))
    for col,levels in bundle['categories'].items():x[col]=pd.Categorical(x[col].astype(str),categories=levels)
    return bundle['estimator'].predict(x)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
    run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    assert (run/'manifest.json').exists(),'Esperar al cierre del entrenamiento'
    checks=[];gradients=[]
    def check(name,condition,detail=None):checks.append({'name':name,'pass':bool(condition),'detail':detail})
    def close(a,b,rtol=2e-11,atol=1e-8):return np.allclose(a,b,rtol=rtol,atol=atol,equal_nan=True)
    manifest=read(run/'manifest.json');report=read(run/'report.json');plan=read(run/'plan_snapshot.json')
    ready=read(run/'readiness_snapshot.json');source=ROOT/ready['run'];base=read(ROOT/ready['base_index'])
    contract=read(ROOT/ready['availability_contract'])
    for item in manifest['files']:check('Artifact '+item['path'],sha(run/item['path'])==item['sha256'])
    for item in read(run/'frozen_sources_before_fit.json')['files']:
        check('Source '+item['path'],sha(ROOT/item['path'])==item['sha256'])
    check('Code matches run snapshot',sha(run/'code_snapshot.py')==report['code_sha256'])
    check('Plan matches frozen snapshot',sha(run/'plan_snapshot.json')==report['plan_sha256'])
    check('No failed fit nodes',report['fit_nodes_failed']==0 and report['fit_nodes_completed']==45)
    check('2024 untouched by price consumer',report['scope_2024']=={'rows_materialized_for_price_fit_prediction_or_score':0,'predictions':0,'scores':0,'confirmation_open':False})
    check('No test/submission/promotion',report['test_predictions']==0 and report['submissions']==0 and not report['promotion'])
    check('Selector finding retained',any(w['id']=='S2-AUD-METRIC-BINDING' and w['status']=='open' for w in report['warnings']))
    selection=read(REPO/'registro/semana2_seleccion_actual.json')
    check('2024 confirmation ledger absent',not (ROOT/selection['ledger_workspace_relative']).exists())
    # Spy all fit entry points used by the producer. Loading and prediction must work with these blocked.
    for cls in [TweedieRegressor,SimpleImputer,StandardScaler,OneHotEncoder,ColumnTransformer,Pipeline,lgb.LGBMRegressor,lgb.LGBMModel]:
        cls.fit=forbid_fit
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbid_fit
    original_target=safe_read(ROOT/base['target']);partitions=safe_read(ROOT/base['partitions'])
    oof=pq.read_table(run/'oof_2023.parquet').to_pandas()
    check('Only 2023 in OOF',oof.year.eq(2023).all())
    check('All model/row keys unique',not oof.duplicated(['model_id',*KEY]).any())
    specs={x['id']:x for x in plan['models']}
    for mid in specs:
        part=oof.loc[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True)
        expected=original_target.sort_values(KEY).reset_index(drop=True)
        check('All original 2023 keys '+mid,part[KEY].equals(expected[KEY]) and len(part)==50094)
        for col in ['T0','reserve','T1_reserve075','T1_reserve125','exposure']:
            check('Original values '+mid+' '+col,close(part[col],expected[col],rtol=0,atol=0))
        check('Strict positivity '+mid,np.isfinite(part.annual_rate).all() and (part.annual_rate>0).all() and (part.prediction>0).all())
        check('Observed offset applied once '+mid,close(part.prediction,part.annual_rate*part['e_cost_mix_1.0'],rtol=0,atol=0))
        check('Unit loss '+mid,close(part.unit_deviance,dev(part.T0,part.prediction)))
        summary=next(x for x in report['summary'] if x['model_id']==mid)
        check('Global D2 '+mid,close(summary['D2'],d2_tweedie_score(part.T0,part.prediction,power=1.5)))
    for line in ['motor','buildings','contents']:
        data=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas()
        check('Input year/test guard '+line,data.year.eq(2023).all() and not data.is_test.any())
        f0=safe_read(ROOT/ready['F0'][line]['path']).sort_values(KEY).reset_index(drop=True)
        actual=data.sort_values(KEY).reset_index(drop=True);block=contract['blocks'][line]
        check('F0 original keys '+line,actual[KEY].equals(f0[KEY]))
        check('F0 original values '+line,actual[block['all']].equals(f0[block['all']]))
        partition=partitions.loc[partitions.line.eq(line)].sort_values(KEY).reset_index(drop=True)
        check('Persisted group/fold '+line,actual[['group_id','fold']].equals(partition[['group_id','fold']]))
        for fold in range(5):
            links=pq.read_table(run/f'links_2023/{line}_fold{fold}.parquet').to_pandas()
            check('Link year guard '+line+str(fold),links.year.eq(2023).all() and not links.is_test.any())
            original=safe_read(source/f'exclude_fold{fold}/observation_link_{line}.parquet')
            check('Link values preserved '+line+str(fold),links.sort_values(KEY).reset_index(drop=True).equals(original[links.columns].sort_values(KEY).reset_index(drop=True)))
            joined=data.merge(links[KEY+[c for c in links if c.startswith('e_cost_')]],on=KEY,validate='one_to_one')
            fit=joined.loc[joined.fold.ne(fold)];valid=joined.loc[joined.fold.eq(fold)]
            for col in ['group_id','customer_id','address_id']:
                check('Disjoint '+line+str(fold)+' '+col,not set(fit[col])&set(valid[col]))
            declared=safe_read(ROOT/base['run']/f'splits/development_2023_fold{fold}.parquet')
            declared=declared.loc[declared.line.eq(line)]
            saved=pq.read_table(run/f'fit_rows/{line}_fold{fold}.parquet').to_pandas().sort_values(KEY).reset_index(drop=True)
            check('Fit row roles persisted '+line+str(fold),saved[KEY+['role']].equals(declared.sort_values(KEY).reset_index(drop=True)[KEY+['role']]))
            for mid,spec in specs.items():
                node=f'{mid}_{line}_fold{fold}';bundle=joblib.load(run/'models'/node/'bundle.joblib')
                receipt=read(run/'models'/node/'receipt.json')
                check('Exact feature whitelist '+node,bundle['columns']==block['all']==receipt['features'])
                part=oof.loc[oof.model_id.eq(mid)&oof.line.eq(line)&oof.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
                valid=valid.sort_values(KEY).reset_index(drop=True)
                check('OOF fold identity '+node,part[KEY].equals(valid[KEY]))
                for col in [c for c in links if c.startswith('e_cost_')]:check('OOF offset '+node+' '+col,close(part[col],valid[col],rtol=0,atol=0))
                with threadpool_limits(limits=2):prediction=predict(bundle,valid)
                check('Serialized replay without fit '+node,np.array_equal(prediction,part.annual_rate.to_numpy()))
                check('Weight sum '+node,close(receipt['training_weight_sum'],np.sqrt(fit['e_cost_mix_1.0']).sum()))
                if mid=='W2-B00':
                    rate=math.fsum((fit.T0/np.sqrt(fit['e_cost_mix_1.0'])).tolist())/math.fsum(np.sqrt(fit['e_cost_mix_1.0']).tolist())
                    check('Closed-form constant '+node,close(bundle['rate'],rate))
                else:
                    params=bundle['estimator'].get_params()
                    check('Frozen parameters '+node,all(params.get(k)==v for k,v in spec['params'].items()))
                    if mid=='W2-B01':
                        transform=bundle['transformer'];num=transform.named_transformers_['numeric']
                        raw=fit[block['numeric']].to_numpy(float)
                        median=np.array([np.nanmedian(raw[:,j]) if np.isfinite(raw[:,j]).any() else 0. for j in range(raw.shape[1])])
                        check('Training-only medians '+node,close(num['median'].statistics_,median))
                        filled=np.where(np.isnan(raw),median,raw)
                        check('Training-only scaler mean '+node,close(num['scale'].mean_,filled.mean(axis=0)))
                        check('Training-only scaler variance '+node,close(num['scale'].var_,filled.var(axis=0)))
                        cats=transform.named_transformers_['categorical'].categories_
                        check('Training-only OHE categories '+node,all(np.array_equal(cats[j],np.sort(fit[col].unique())) for j,col in enumerate(block['categorical'])))
                        with threadpool_limits(limits=2):
                            matrix=transform.transform(fit[block['all']]);mu=bundle['estimator'].predict(matrix)
                            response=fit.T0.to_numpy()/fit['e_cost_mix_1.0'].to_numpy();w=np.sqrt(fit['e_cost_mix_1.0'].to_numpy())
                            grad=w*(mu-response)/np.sqrt(mu)/w.sum()
                            coef_grad=np.asarray(matrix.T@grad).ravel()+spec['params']['alpha']*bundle['estimator'].coef_
                            norm=float(max(np.max(np.abs(coef_grad)),abs(grad.sum())))
                        gradients.append({'node':node,'gradient_infinity_norm':norm})
                        check('GLM normalized weighted objective stationary '+node,norm<1e-4,norm)
                    else:
                        check('Training-only native categories '+node,all(levels==sorted(fit[col].astype(str).unique().tolist()) for col,levels in bundle['categories'].items()))
                        check('Fixed maximum boosting rounds '+node,receipt['details']['trees']==300)
    segments=read(run/'diagnostics/segments.json')
    for item in segments:
        part=oof.loc[oof.model_id.eq(item['model_id'])]
        if item['segment']=='line':part=part.loc[part.line.eq(item['label'])]
        elif item['segment']=='fold':part=part.loc[part.fold.eq(int(item['label']))]
        else:part=part.loc[part.x_new_business.eq(1) if item['label']=='new_business' else part.x_new_business.ne(1)]
        check('Segment score '+item['model_id']+item['segment']+item['label'],close(item['D2'],d2_tweedie_score(part.T0,part.prediction,power=1.5)))
    scenarios={'base':('T0','e_cost_mix_1.0'),'reserve075':('T1_reserve075','e_cost_mix_0.75'),
               'reserve125':('T1_reserve125','e_cost_mix_1.25'),'late_cost05':('T0','e_cost_mix_tail0.05'),'late_cost10':('T0','e_cost_mix_tail0.1')}
    for item in read(run/'diagnostics/observation_sensitivity.json'):
        part=oof.loc[oof.model_id.eq(item['model_id'])];ycol,ecol=scenarios[item['scenario']]
        check('Fixed-rate sensitivity '+item['model_id']+item['scenario'],close(item['D2'],d2_tweedie_score(part[ycol],part.annual_rate*part[ecol],power=1.5)))
    pairs=read(run/'diagnostics/pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_2023.parquet').to_pandas()
    ids=list(specs);ordered={mid:oof.loc[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True) for mid in ids}
    first=ordered[ids[0]];groups,codes=np.unique(first.group_id,return_inverse=True);g=len(groups)
    n=np.bincount(codes).astype(float);sy=np.bincount(codes,weights=first.T0);sr=np.bincount(codes,weights=np.sqrt(first.T0))
    losses=np.array([np.bincount(codes,weights=dev(ordered[mid].T0,ordered[mid].prediction)) for mid in ids]).T
    config=plan['diagnostics']['development_uncertainty'];rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();recomputed={}
    for pair in pairs['pairs']:recomputed[(pair['candidate'],pair['reference'])]=[]
    for start in range(0,config['replicates'],32):
        draw=rng.integers(0,g,size=(min(32,config['replicates']-start),g),dtype=np.int64);digest.update(draw.tobytes())
        denominator=8*(np.sqrt(n[draw].sum(axis=1)*sy[draw].sum(axis=1))-sr[draw].sum(axis=1))
        loss=losses[draw].sum(axis=1)
        for key in recomputed:
            a,b=ids.index(key[0]),ids.index(key[1]);recomputed[key].extend(((loss[:,b]-loss[:,a])/denominator).tolist())
    check('Shared bootstrap draws checksum',digest.hexdigest()==pairs['draws_sha256'])
    for pair in pairs['pairs']:
        key=(pair['candidate'],pair['reference']);dist=np.array(recomputed[key])
        saved=boot.loc[boot.candidate.eq(key[0])&boot.reference.eq(key[1])].sort_values('replicate')
        check('All 2000 paired replicates '+str(key),len(saved)==2000 and close(saved.delta_D2,dist))
        check('Exploratory interval '+str(key),close([pair['exploratory_lower95'],pair['exploratory_upper95']],np.quantile(dist,[.025,.975])))
        a,b=ids.index(key[0]),ids.index(key[1]);advantage=losses[:,b]-losses[:,a]
        denominator=8*(np.sqrt(n.sum()*sy.sum())-sr.sum())
        check('Paired point '+str(key),close(pair['delta_D2'],advantage.sum()/denominator))
        remove=min(g-1,max(5,math.ceil(.001*g)));keep=np.ones(g,dtype=bool);keep[np.argsort(-advantage,kind='stable')[:remove]]=False
        reduced=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum())
        check('Influence recomputed '+str(key),remove==pair['removed_favorable_groups'] and close(pair['delta_after_removal'],advantage[keep].sum()/reduced))
    directory=run/'verifications';directory.mkdir(exist_ok=True)
    path=directory/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source':str(Path(__file__).relative_to(ROOT)),
         'source_sha256':sha(Path(__file__)),'run':str(run.relative_to(ROOT)),'checks':checks,
         'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
         'GLM_gradients':gradients,'fit_calls':0,'pricing_2024_predictions_or_scores':0,
         'scope':'Separate implementation and blocked-fit replay by same Codex author; not professional independent validation'}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'verification':str(path.relative_to(ROOT)),'passed':result['passed'],'failed':result['failed'],
                      'failures':[x for x in checks if not x['pass']]},ensure_ascii=True))
    return 0 if result['failed']==0 else 2


if __name__=='__main__':raise SystemExit(main())
