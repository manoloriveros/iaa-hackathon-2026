"""Primera tanda local de precios: solo desarrollo 2023, sin consumidor 2024."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import sys
import time
import traceback
import uuid
import warnings

for _name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[_name] = '2'
REPO = Path(__file__).resolve().parents[2]
ROOT = REPO.parents[1]
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import scipy
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

KEY = ['market', 'line', 'row_id']
LINES = ['motor', 'buildings', 'contents']
PLAN = REPO/'registro/semana2_desarrollo2023_plan_v1.json'
SCENARIOS = {'base': ('T0','e_cost_mix_1.0'), 'reserve075': ('T1_reserve075','e_cost_mix_0.75'),
             'reserve125': ('T1_reserve125','e_cost_mix_1.25'),
             'late_cost05': ('T0','e_cost_mix_tail0.05'), 'late_cost10': ('T0','e_cost_mix_tail0.1')}


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def relative(path):
    return path.relative_to(ROOT).as_posix()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False,
                    default=lambda x: x.item() if hasattr(x, 'item') else str(x))+'\n', encoding='utf-8')


def assert_2023(frame):
    require(len(frame)>0 and frame.year.eq(2023).all(), 'Solo se permite materializar desarrollo 2023')
    if 'is_test' in frame:
        require(not frame.is_test.any(), 'Test vedado en este consumidor')
    require(not frame.duplicated(KEY).any(), 'Claves repetidas')


def load_2023(path, columns=None):
    require('year' in pq.ParquetFile(path).schema_arrow.names, 'Fuente sin filtro temporal')
    frame = pq.read_table(path, filters=[('year','=',2023)], columns=columns).to_pandas()
    assert_2023(frame)
    return frame


def unit_deviance(y, mu):
    y = np.asarray(y, dtype=float); mu = np.asarray(mu, dtype=float)
    require(np.isfinite(y).all() and (y>=0).all(), 'Respuesta inválida')
    require(np.isfinite(mu).all() and (mu>0).all(), 'Predicción no positiva/finita')
    dev = 4*(y/np.sqrt(mu)+np.sqrt(mu)-2*np.sqrt(y))
    require(dev.min(initial=0)>=-1e-7, 'Devianza numéricamente inválida')
    return np.maximum(dev,0.)


def metrics(frame, target='T0', prediction='prediction'):
    y = frame[target].to_numpy(float); pred = frame[prediction].to_numpy(float)
    loss = unit_deviance(y,pred)
    null = float(unit_deviance(y,np.full(len(y),y.mean())).sum()) if y.sum()>0 else 0.
    return {'rows':len(frame), 'observed_total':float(y.sum()), 'predicted_total':float(pred.sum()),
            'actual_over_expected':float(y.sum()/pred.sum()), 'deviance_sum':float(loss.sum()),
            'null_deviance_sum':null, 'D2':float(1-loss.sum()/null) if null>0 else None}


def prepare_lgb(frame, columns, cat_levels):
    x = frame[columns].copy()
    for col, levels in cat_levels.items():
        x[col] = pd.Categorical(x[col].astype(str), categories=levels)
    return x


def predict_bundle(bundle, frame):
    assert_2023(frame)
    if bundle['family']=='constant_line_rate':
        return np.full(len(frame), bundle['rate'])
    if bundle['family']=='TweedieRegressor':
        return bundle['estimator'].predict(bundle['transformer'].transform(frame[bundle['columns']]))
    if bundle['family']=='LGBMRegressor':
        return bundle['estimator'].predict(prepare_lgb(frame,bundle['columns'],bundle['categories']))
    raise ValueError('Familia desconocida')


def fit_bundle(spec, fit, block):
    assert_2023(fit)
    e = fit['e_cost_mix_1.0'].to_numpy(float)
    require(np.isfinite(e).all() and (e>0).all(), 'Exposición efectiva inválida')
    y = fit.T0.to_numpy(float); weight = np.sqrt(e); response = y/e
    cols = block['all']
    require(set(cols)==set(c for c in fit if c.startswith('x_')), 'F0 fuera de contrato')
    family = spec['family']; bundle = {'family':family, 'columns':cols}
    if family=='constant_line_rate':
        rate = float(np.average(response,weights=weight))
        bundle.update(rate=rate, actuarial_sum_ratio=float(y.sum()/e.sum()))
        return bundle, {'closed_form_rate':rate,'actuarial_sum_ratio':bundle['actuarial_sum_ratio']}
    if family=='TweedieRegressor':
        numeric = Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),
                            ('scale',StandardScaler())])
        transform = ColumnTransformer([('numeric',numeric,block['numeric']),
                    ('categorical',OneHotEncoder(handle_unknown='ignore',min_frequency=50,
                                     max_categories=40,sparse_output=True),block['categorical'])],
                    sparse_threshold=1.)
        matrix = transform.fit_transform(fit[cols])
        estimator = TweedieRegressor(**spec['params'])
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter('always')
            estimator.fit(matrix,response,sample_weight=weight)
        notes = [{'category':w.category.__name__,'message':str(w.message)} for w in seen]
        require(not any(issubclass(w.category,ConvergenceWarning) for w in seen), 'GLM no convergió: '+str(notes))
        require(estimator.n_iter_<spec['params']['max_iter'], 'GLM alcanzó máximo de iteraciones')
        bundle.update(transformer=transform,estimator=estimator)
        receipt = {'n_iter':int(estimator.n_iter_),'transformed_features':int(matrix.shape[1]),
                   'effective_params':estimator.get_params(),'warnings':notes}
        return bundle, receipt
    if family=='LGBMRegressor':
        levels = {col:sorted(fit[col].astype(str).unique().tolist()) for col in block['categorical']}
        x = prepare_lgb(fit,cols,levels)
        estimator = lgb.LGBMRegressor(**spec['params'])
        estimator.fit(x,response,sample_weight=weight,categorical_feature=block['categorical'])
        bundle.update(estimator=estimator,categories=levels)
        return bundle, {'trees':estimator.booster_.num_trees(),'effective_params':estimator.get_params(),
                        'booster_params':estimator.booster_.params}
    raise ValueError(family)


def paired_diagnostics(oof, model_ids, outdir, config):
    first = oof.loc[oof.model_id.eq(model_ids[0])].sort_values(KEY).reset_index(drop=True)
    loss = []
    for model_id in model_ids:
        part = oof.loc[oof.model_id.eq(model_id)].sort_values(KEY).reset_index(drop=True)
        require(part[KEY].equals(first[KEY]), 'Pares con filas distintas')
        require(np.array_equal(part.T0,first.T0), 'Pares con objetivos distintos')
        require(np.array_equal(part['e_cost_mix_1.0'],first['e_cost_mix_1.0']), 'Vínculos distintos')
        loss.append(part.unit_deviance.to_numpy())
    codes, groups = pd.factorize(first.group_id,sort=True)
    g = len(groups)
    n = np.bincount(codes,minlength=g).astype(float)
    sy = np.bincount(codes,weights=first.T0,minlength=g)
    syroot = np.bincount(codes,weights=np.sqrt(first.T0),minlength=g)
    gl = np.array([np.bincount(codes,weights=x,minlength=g) for x in loss]).T
    groupframe = pd.DataFrame({'group_id':groups,'rows':n,'T0':sy,'sqrt_T0':syroot})
    for j, mid in enumerate(model_ids):
        groupframe['loss_'+mid] = gl[:,j]
    pq.write_table(pa.Table.from_pandas(groupframe,preserve_index=False),outdir/'group_aggregates.parquet')
    rng = np.random.default_rng(config['seed']); digest = hashlib.sha256(); reps = []
    for start in range(0,config['replicates'],32):
        count = min(32,config['replicates']-start)
        draw = rng.integers(0,g,size=(count,g),dtype=np.int64)
        digest.update(draw.tobytes())
        ns = n[draw].sum(axis=1); ys = sy[draw].sum(axis=1)
        denominator = 8*(np.sqrt(ns*ys)-syroot[draw].sum(axis=1))
        require((denominator>0).all(), 'Réplica sin devianza nula')
        losses = gl[draw].sum(axis=1)
        for b in range(len(model_ids)):
            for a in range(b+1,len(model_ids)):
                delta = (losses[:,b]-losses[:,a])/denominator
                reps.extend({'replicate':start+k,'candidate':model_ids[a],'reference':model_ids[b],
                             'delta_D2':float(v)} for k,v in enumerate(delta))
    repframe = pd.DataFrame(reps)
    pq.write_table(pa.Table.from_pandas(repframe,preserve_index=False),outdir/'bootstrap_2023.parquet')
    denom = 8*(np.sqrt(n.sum()*sy.sum())-syroot.sum())
    pairs = []
    for b in range(len(model_ids)):
        for a in range(b+1,len(model_ids)):
            dist = repframe.loc[repframe.candidate.eq(model_ids[a])&repframe.reference.eq(model_ids[b]),'delta_D2']
            advantage = gl[:,b]-gl[:,a]
            remove = min(g-1,max(5,int(np.ceil(.001*g))))
            excluded = np.argsort(-advantage,kind='stable')[:remove]
            keep = np.ones(g,dtype=bool);keep[excluded]=False
            trimmed_denom = 8*(np.sqrt(n[keep].sum()*sy[keep].sum())-syroot[keep].sum())
            pairs.append({'candidate':model_ids[a],'reference':model_ids[b],
                 'delta_D2':float(advantage.sum()/denom), 'exploratory_lower95':float(dist.quantile(.025)),
                 'exploratory_upper95':float(dist.quantile(.975)), 'groups':g,
                 'removed_favorable_groups':remove, 'delta_after_removal':float(advantage[keep].sum()/trimmed_denom),
                 'largest_favorable_group_delta':float(advantage.max()/denom),
                 'interpretation':'Exploratory 2023 only; no simultaneous confirmation or promotion'})
    return {'config':config,'draws_sha256':digest.hexdigest(),'pairs':pairs}


def run():
    started = datetime.now(timezone.utc); timer = time.perf_counter()
    plan = read(PLAN); active_path = ROOT/plan['readiness_index']; active = read(active_path)
    base = read(ROOT/active['base_index']); source = ROOT/active['run']; base_dir = ROOT/base['run']
    contract = read(ROOT/active['availability_contract'])
    require(active['readiness']['development_2023_training'] and not active['readiness']['confirmation_2024_open'], 'Ámbito no habilitado')
    selection = read(REPO/'registro/semana2_seleccion_actual.json')
    ledger = ROOT/selection['ledger_workspace_relative']
    require(not ledger.exists(), 'Revisar ledger común antes de este consumidor 2023')
    forum_path = ROOT/'Hackaton/Semana 2/Foro/FORO.md'
    forum_bytes = forum_path.read_bytes()
    require(forum_bytes.count(b'<!-- aporte:COD-S2-20261023-008 -->')==1, 'Falta preinscripción única')
    run_dir = REPO/'privado/semana2/desarrollo2023'/('dev_'+started.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    run_dir.mkdir(parents=True)
    for name in ['inputs_2023','links_2023','models','fit_rows','diagnostics']:
        (run_dir/name).mkdir()
    events_path = run_dir/'events.jsonl'
    def event(kind, **kwargs):
        obj = dict(utc=datetime.now(timezone.utc).isoformat(),event=kind,**kwargs)
        text = json.dumps(obj,ensure_ascii=True,allow_nan=False)
        with events_path.open('a',encoding='utf-8') as handle: handle.write(text+'\n')
        print(text,flush=True)
    event('run_started',run=relative(run_dir),scope='2023_only',confirmation_2024_open=False)
    (run_dir/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (run_dir/'plan_snapshot.json').write_bytes(PLAN.read_bytes())
    (run_dir/'readiness_snapshot.json').write_bytes(active_path.read_bytes())
    (run_dir/'forum_before_training.md').write_bytes(forum_bytes)
    dump(run_dir/'environment.json',{'python':sys.version,'platform':platform.platform(),'cpu_count':os.cpu_count(),
         'versions':{name:mod.__version__ for name,mod in [('numpy',np),('pandas',pd),('pyarrow',pa),('scipy',scipy),('sklearn',sklearn),('lightgbm',lgb),('joblib',joblib)]},
         'threads':2,'seed':2026102302})
    sources = [PLAN,ROOT/base['target'],ROOT/base['partitions'],ROOT/active['availability_contract'],ROOT/plan['selection_policy'],
               ROOT/active['producer'],ROOT/active['verification']['path'],Path(__file__)]
    sources += [source/f'F0_{line}.parquet' for line in LINES]
    for fold in range(5):
        sources.append(base_dir/f'splits/development_2023_fold{fold}.parquet')
        sources += [source/f'exclude_fold{fold}/observation_link_{line}.parquet' for line in LINES]
    # Hashing the closed shared sources does not deserialize 2024 labels or create predictions.
    source_manifest = [{'path':relative(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sources]
    require(sha(ROOT/base['target'])==plan['base_target_sha256'] and sha(ROOT/base['partitions'])==plan['partitions_sha256'], 'Base distinta de la previa')
    require(sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'], 'Política cambiada')
    for line, info in active['F0'].items(): require(sha(ROOT/info['path'])==info['sha256'], 'Matriz modificada '+line)
    old_manifest = read(source/'manifest.json')
    expected = {item['path']:item['sha256'] for item in old_manifest['files']}
    for fold in range(5):
        for line in LINES:
            name=f'exclude_fold{fold}/observation_link_{line}.parquet'
            require(sha(source/name)==expected[name], 'Vínculo modificado '+name)
    dump(run_dir/'frozen_sources_before_fit.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':source_manifest})
    target_cols = [*KEY,'year','is_test','exposure','T0','reserve','T1_reserve075','T1_reserve125']
    target = load_2023(ROOT/base['target'],target_cols)
    partition = load_2023(ROOT/base['partitions'],[*KEY,'year','group_id','fold'])
    require(len(target)==50094 and len(partition)==50094, 'Población 2023 inesperada')
    all_predictions=[];fit_receipts=[]; failures=[];counts=[]
    for line in LINES:
        f0 = load_2023(ROOT/active['F0'][line]['path'])
        block = contract['blocks'][line]
        frame = f0.merge(target.loc[target.line.eq(line),KEY+['T0','reserve','T1_reserve075','T1_reserve125']],on=KEY,validate='one_to_one')
        frame = frame.merge(partition.loc[partition.line.eq(line),KEY+['group_id','fold']],on=KEY,validate='one_to_one').sort_values(KEY).reset_index(drop=True)
        assert_2023(frame);require(len(frame)==len(f0), 'Pérdida de filas al unir')
        pq.write_table(pa.Table.from_pandas(frame,preserve_index=False),run_dir/f'inputs_2023/{line}.parquet')
        counts.append({'line':line,'rows':len(frame),'groups':frame.group_id.nunique(),'positive_claim_rows':int(frame.T0.gt(0).sum())})
        for fold in range(5):
            declared = load_2023(base_dir/f'splits/development_2023_fold{fold}.parquet')
            declared = declared.loc[declared.line.eq(line)]
            link_cols = [*KEY,'year','is_test','exposure',*[v[1] for v in SCENARIOS.values()]]
            links = load_2023(source/f'exclude_fold{fold}/observation_link_{line}.parquet',link_cols)
            pq.write_table(pa.Table.from_pandas(links,preserve_index=False),run_dir/f'links_2023/{line}_fold{fold}.parquet')
            df = frame.merge(links[KEY+[*[v[1] for v in SCENARIOS.values()]]],on=KEY,validate='one_to_one')
            fit = df.loc[df.fold.ne(fold)].copy(); valid = df.loc[df.fold.eq(fold)].copy()
            for role, subset in [('train',fit),('validation',valid)]:
                wanted=declared.loc[declared.role.eq(role)].sort_values(KEY).reset_index(drop=True)
                require(subset[KEY].sort_values(KEY).reset_index(drop=True).equals(wanted[KEY]), 'Split guardado distinto')
                assert_2023(subset)
            for col in ['group_id','customer_id','address_id']:
                require(not set(fit[col])&set(valid[col]), 'Entidades compartidas '+col)
            saved_rows=df[KEY+['year','group_id','fold']].copy()
            saved_rows['role']=np.where(saved_rows.fold.eq(fold),'validation','train')
            pq.write_table(pa.Table.from_pandas(saved_rows,preserve_index=False),run_dir/f'fit_rows/{line}_fold{fold}.parquet')
            for spec in plan['models']:
                model_id=spec['id']; node=f'{model_id}_{line}_fold{fold}'; node_dir=run_dir/'models'/node;node_dir.mkdir()
                tick=time.perf_counter();event('fit_started',node=node,train_rows=len(fit),validation_rows=len(valid))
                try:
                    with threadpool_limits(limits=2):
                        bundle, details=fit_bundle(spec,fit,block)
                        rate=np.asarray(predict_bundle(bundle,valid),dtype=float)
                    require(np.isfinite(rate).all() and (rate>0).all(), 'Tasa no positiva/finita')
                    pred=valid['e_cost_mix_1.0'].to_numpy(float)*rate
                    unit=unit_deviance(valid.T0,pred)
                    require(np.isclose(unit.mean(),mean_tweedie_deviance(valid.T0,pred,power=1.5),rtol=1e-12,atol=1e-9), 'Scorer discrepante')
                    joblib.dump(bundle,node_dir/'bundle.joblib',compress=3)
                    if spec['family']=='LGBMRegressor': bundle['estimator'].booster_.save_model(str(node_dir/'booster.txt'))
                    with threadpool_limits(limits=2): replay=predict_bundle(joblib.load(node_dir/'bundle.joblib'),valid)
                    require(np.array_equal(rate,replay), 'Replay inmediato distinto')
                    out=valid[KEY+['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','x_new_business',*[v[1] for v in SCENARIOS.values()]]].copy()
                    out['model_id']=model_id;out['annual_rate']=rate;out['prediction']=pred;out['unit_deviance']=unit
                    all_predictions.append(out)
                    unknown={col:int((~valid[col].astype(str).isin(fit[col].astype(str).unique())).sum()) for col in block['categorical']}
                    receipt={'node':node,'model_id':model_id,'line':line,'fold':fold,'year':2023,
                             'train_rows':len(fit),'validation_rows':len(valid),'fit_seconds':time.perf_counter()-tick,
                             'scope':f'exclude_fold{fold}','features':block['all'],'unknown_category_rows':unknown,
                             'training_weight_sum':float(np.sqrt(fit['e_cost_mix_1.0']).sum()),
                             'finite_positive_predictions':True,'serialized_replay_exact':True,'details':details}
                    dump(node_dir/'receipt.json',receipt);fit_receipts.append(receipt)
                    event('fit_completed',node=node,seconds=receipt['fit_seconds'])
                except Exception:
                    failure={'node':node,'traceback':traceback.format_exc()}
                    dump(node_dir/'failure.json',failure);failures.append(failure)
                    event('fit_failed',node=node,error=failure['traceback'])
    require(all_predictions, 'Ningún modelo produjo OOF')
    oof=pd.concat(all_predictions,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True)
    assert_2023(oof.drop_duplicates(KEY))
    require(not oof.duplicated(['model_id',*KEY]).any(), 'Predicción OOF duplicada')
    pq.write_table(pa.Table.from_pandas(oof,preserve_index=False),run_dir/'oof_2023.parquet')
    complete=[];summary=[];segments=[];sensitivities=[]
    for spec in plan['models']:
        model_id=spec['id'];part=oof.loc[oof.model_id.eq(model_id)]
        okay=len(part)==len(target) and not any(x['node'].startswith(model_id+'_') for x in failures)
        if len(part)==0:
            summary.append({'model_id':model_id,'technical_complete':False,'rows':0})
            continue
        summary.append({'model_id':model_id,'technical_complete':okay,**metrics(part)})
        if okay: complete.append(model_id)
        for segment, labels in [('line',part.line),('fold',part.fold),('business',np.where(part.x_new_business.eq(1),'new_business','renewal'))]:
            tmp=part.assign(segment_label=labels)
            for label, block in tmp.groupby('segment_label',sort=True,observed=True):
                segments.append({'model_id':model_id,'segment':segment,'label':str(label),**metrics(block)})
        for scenario,(target_col,exposure_col) in SCENARIOS.items():
            tmp=part.assign(scenario_prediction=part.annual_rate*part[exposure_col])
            sensitivities.append({'model_id':model_id,'scenario':scenario,
                'scope':'Fixed base-model rates; observation-only diagnostic, not refitted scenario',
                **metrics(tmp,target_col,'scenario_prediction')})
    pairs=paired_diagnostics(oof,complete,run_dir/'diagnostics',plan['diagnostics']['development_uncertainty']) if len(complete)>=2 else {'pairs':[]}
    dump(run_dir/'diagnostics/pairs.json',pairs)
    dump(run_dir/'diagnostics/segments.json',segments)
    dump(run_dir/'diagnostics/observation_sensitivity.json',sensitivities)
    for item in source_manifest: require(sha(ROOT/item['path'])==item['sha256'], 'Fuente cambió durante el ajuste '+item['path'])
    require(not ledger.exists(), 'Se creó un ledger concurrente; revisar antes de declarar 2024 cerrado')
    notes=[{'id':'DEV2023-EXPLORATORY','class':'inform','status':'open','effect':'Development results do not establish temporal superiority or promote/retire models'},
           {'id':'DEV2023-ULTIMATE-ASSUMPTIONS','class':'condition','status':'open','effect':'T0, reserve adequacy, delay stationarity, unseen tail and physical-master assumptions remain unvalidated; see prior report'},
           {'id':'S2-AUD-METRIC-BINDING','class':'block','status':'open','effect':'Verified promotion blocked; do not open 2024 before documented semantic fix and required frozen evidence'},
           {'id':'DEV2023-SCENARIOS-NOT-REFIT','class':'inform','status':'open','effect':'Fixed-rate sensitivities are diagnostics; do not satisfy complete refitted confirmation scenarios'}]
    report={'id':plan['id'],'author':'Codex','started_utc':started.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),
            'run':relative(run_dir),'plan_sha256':sha(PLAN),'code_sha256':sha(Path(__file__)),
            'scope':'2023 grouped development only','input_counts':counts,'summary':summary,'pairs':pairs['pairs'],
            'fit_nodes_completed':len(fit_receipts),'fit_nodes_failed':len(failures),'failures':failures,
            'pricing_estimators_fitted':sum(x['model_id']!='W2-B00' for x in fit_receipts),
            'closed_form_constants_fitted':sum(x['model_id']=='W2-B00' for x in fit_receipts),
            'scope_2024':{'rows_materialized_for_price_fit_prediction_or_score':0,'predictions':0,'scores':0,'confirmation_open':False},
            'test_predictions':0,'submissions':0,'promotion':False,'final_confirmation_roster_frozen':False,
            'all_alternatives_preserved':True,'warnings':notes,'elapsed_seconds':time.perf_counter()-timer,
            'professional_independent_validation':False,'human_review':'pending'}
    dump(run_dir/'report.json',report)
    event('run_completed',run=relative(run_dir),complete_models=complete,failed_nodes=len(failures),elapsed_seconds=report['elapsed_seconds'])
    dump(run_dir/'manifest.json',{'run':relative(run_dir),'files':[{'path':p.relative_to(run_dir).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
            for p in sorted(run_dir.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':relative(run_dir),'summary':summary,'pairs':pairs['pairs'],'failed_nodes':len(failures)},ensure_ascii=True),flush=True)
    return 0 if not failures else 2


if __name__=='__main__':
    raise SystemExit(run())
