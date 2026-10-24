"""Segunda tanda preinscrita: solo 2023; v1 y referencia se conservan."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys,time,traceback,uuid
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='2'
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
SPEC=importlib.util.spec_from_file_location('dev2023_v1_frozen',REPO/'src/semana2/entrenar_desarrollo2023.py')
v1=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=v1;SPEC.loader.exec_module(v1)
np,pd,pq,pa,joblib=v1.np,v1.pd,v1.pq,v1.pa,v1.joblib
KEY=v1.KEY;LINES=v1.LINES;PLAN=REPO/'registro/semana2_desarrollo2023_plan_v2.json'


def route(model_id,line):
    v1.require(line in LINES,'Ramo desconocido')
    if model_id=='W2-B03':return 'new_fit' if line=='buildings' else 'reuse_W2-B01'
    if model_id=='W2-B04':return 'prefix_W2-B02'
    if model_id=='W2-B05':return 'new_fit'
    raise ValueError('Receta v2 desconocida')


def prefix_bundle(parent,trees):
    v1.require(parent['family']=='LGBMRegressor','Padre no es bosque previsto')
    count=parent['estimator'].booster_.num_trees()
    v1.require(isinstance(trees,int) and 0<trees<=count,'Prefijo inválido')
    booster=v1.lgb.Booster(model_str=parent['estimator'].booster_.model_to_string(num_iteration=trees))
    v1.require(booster.num_trees()==trees,'Número de árboles exportado distinto')
    return {'family':'LGBMBoosterPrefix','columns':parent['columns'],'categories':parent['categories'],
            'booster':booster,'prefix_trees':trees}


def predict(bundle,frame):
    v1.assert_2023(frame)
    if bundle['family']=='LGBMBoosterPrefix':
        return bundle['booster'].predict(v1.prepare_lgb(frame,bundle['columns'],bundle['categories']))
    return v1.predict_bundle(bundle,frame)


def run():
    started=datetime.now(timezone.utc);tick=time.perf_counter();plan=v1.read(PLAN)
    parent=ROOT/plan['parent_run'];oldreport=v1.read(parent/'report.json');oldplan=v1.read(parent/'plan_snapshot.json')
    v1.require(v1.sha(parent/'manifest.json')==plan['parent_manifest_sha256'],'Manifiesto v1 distinto')
    v1.require(v1.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'],'OOF v1 distinto')
    v1.require(v1.sha(parent/'plan_snapshot.json')==plan['parent_recipe_sha256'],'Receta v1 distinta')
    v1.require(v1.sha(REPO/'src/semana2/entrenar_desarrollo2023.py')==oldreport['code_sha256'],'Productor v1 modificado')
    selection=v1.read(REPO/'registro/semana2_seleccion_actual.json');ledger=ROOT/selection['ledger_workspace_relative']
    v1.require(not ledger.exists(),'Revisar ledger concurrente antes de declarar 2024 cerrado')
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_bytes=forum.read_bytes()
    v1.require(forum_bytes.count(b'<!-- aporte:COD-S2-20261023-010 -->')==1,'Falta preinscripción v2')
    v1.require(v1.sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'],'Política cambiada')
    ready=v1.read(parent/'readiness_snapshot.json');contract=v1.read(ROOT/ready['availability_contract'])
    run_dir=parent.parent/('dev2_'+started.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);run_dir.mkdir()
    for name in ['inputs_2023','links_2023','fit_rows','models','diagnostics']:(run_dir/name).mkdir()
    def event(kind,**values):
        text=json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event=kind,**values),ensure_ascii=True)
        with (run_dir/'events.jsonl').open('a',encoding='utf-8') as f:f.write(text+'\n')
        print(text,flush=True)
    event('run_started',run=v1.relative(run_dir),year=2023,confirmation_2024_open=False)
    for origin,dest in [(Path(__file__),'code_snapshot.py'),(PLAN,'plan_snapshot.json'),
                        (parent/'code_snapshot.py','v1_code_snapshot.py'),(parent/'readiness_snapshot.json','readiness_snapshot.json'),
                        (parent/'environment.json','environment.json')]:
        (run_dir/dest).write_bytes(origin.read_bytes())
    (run_dir/'forum_before_training.md').write_bytes(forum_bytes)
    (run_dir/'selector_index_at_start.json').write_bytes((REPO/'registro/semana2_seleccion_actual.json').read_bytes())
    source_files=[parent/x['path'] for x in v1.read(parent/'manifest.json')['files']]
    source_files += [PLAN,Path(__file__),REPO/'src/semana2/entrenar_desarrollo2023.py',ROOT/plan['diagnostic_review'],ROOT/plan['selection_policy']]
    source_files=list(dict.fromkeys(source_files))
    sources=[{'path':v1.relative(p),'sha256':v1.sha(p),'bytes':p.stat().st_size} for p in source_files]
    v1.dump(run_dir/'frozen_sources_before_fit.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':sources})
    for folder in ['inputs_2023','links_2023','fit_rows']:
        for path in (parent/folder).glob('*.parquet'):(run_dir/folder/path.name).write_bytes(path.read_bytes())
    base_oof=pq.read_table(parent/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas()
    v1.assert_2023(base_oof.drop_duplicates(KEY));v1.require(len(base_oof)==3*50094,'Comparadores incompletos')
    predictions=[base_oof];receipts=[];failures=[];training_nodes=[]
    for line in LINES:
        data=v1.load_2023(run_dir/f'inputs_2023/{line}.parquet');block=contract['blocks'][line]
        for fold in range(5):
            links=v1.load_2023(run_dir/f'links_2023/{line}_fold{fold}.parquet')
            offsets=[x[1] for x in v1.SCENARIOS.values()]
            frame=data.merge(links[KEY+offsets],on=KEY,validate='one_to_one')
            fit=frame.loc[frame.fold.ne(fold)];valid=frame.loc[frame.fold.eq(fold)]
            v1.assert_2023(fit);v1.assert_2023(valid)
            for col in ['group_id','customer_id','address_id']:v1.require(not set(fit[col])&set(valid[col]),'Fuga de '+col)
            for recipe in plan['models']:
                mid=recipe['id'];node=f'{mid}_{line}_fold{fold}';folder=run_dir/'models'/node;folder.mkdir()
                mode=route(mid,line);node_tick=time.perf_counter();event('node_started',node=node,mode=mode)
                try:
                    parent_path=None;details={}
                    with v1.threadpool_limits(limits=2):
                        if mode=='new_fit':bundle,details=v1.fit_bundle(recipe,fit,block)
                        else:
                            parent_id='W2-B01' if mode=='reuse_W2-B01' else 'W2-B02'
                            parent_path=parent/'models'/f'{parent_id}_{line}_fold{fold}'/'bundle.joblib'
                            bundle=joblib.load(parent_path)
                            if mode=='prefix_W2-B02':
                                original=bundle;bundle=prefix_bundle(original,recipe['prefix_trees'])
                                expected=original['estimator'].predict(v1.prepare_lgb(valid,original['columns'],original['categories']),num_iteration=recipe['prefix_trees'])
                                v1.require(np.array_equal(predict(bundle,valid),expected),'Prefijo no coincide con padre')
                        rate=np.asarray(predict(bundle,valid),dtype=float)
                        train_rate=np.asarray(predict(bundle,fit),dtype=float)
                    v1.require(np.isfinite(rate).all() and (rate>0).all(),'Tasa inválida')
                    pred=rate*valid['e_cost_mix_1.0'].to_numpy();loss=v1.unit_deviance(valid.T0,pred)
                    v1.require(np.isclose(loss.mean(),v1.mean_tweedie_deviance(valid.T0,pred,power=1.5),rtol=1e-12,atol=1e-9),'Scorer discrepante')
                    if mode=='reuse_W2-B01':(folder/'bundle.joblib').write_bytes(parent_path.read_bytes())
                    else:joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                    if bundle['family']=='LGBMBoosterPrefix':bundle['booster'].save_model(str(folder/'booster.txt'))
                    if bundle['family']=='LGBMRegressor':bundle['estimator'].booster_.save_model(str(folder/'booster.txt'))
                    with v1.threadpool_limits(limits=2):replay=predict(joblib.load(folder/'bundle.joblib'),valid)
                    v1.require(np.array_equal(replay,rate),'Replay distinto')
                    output=valid[KEY+['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','x_new_business',*offsets]].copy()
                    output['model_id']=mid;output['annual_rate']=rate;output['prediction']=pred;output['unit_deviance']=loss;predictions.append(output)
                    train_pred=train_rate*fit['e_cost_mix_1.0'].to_numpy()
                    training_nodes.append({'model_id':mid,'line':line,'fold':fold,'rows':len(fit),'observed_total':float(fit.T0.sum()),
                        'predicted_total':float(train_pred.sum()),'deviance_sum':float(v1.unit_deviance(fit.T0,train_pred).sum())})
                    if mode=='new_fit':actual_params=bundle['estimator'].get_params()
                    elif mode=='reuse_W2-B01':actual_params=bundle['estimator'].get_params()
                    else:actual_params={'prefix_trees':recipe['prefix_trees'],'parent_model':'W2-B02'}
                    receipt={'node':node,'model_id':mid,'line':line,'fold':fold,'mode':mode,'year':2023,
                        'train_rows':len(fit),'validation_rows':len(valid),'features':block['all'],'details':details,
                        'effective_params':actual_params,'parent_bundle':v1.relative(parent_path) if parent_path else None,
                        'parent_bundle_sha256':v1.sha(parent_path) if parent_path else None,
                        'serialized_replay_exact':True,'seconds':time.perf_counter()-node_tick}
                    v1.dump(folder/'receipt.json',receipt);receipts.append(receipt);event('node_completed',node=node,seconds=receipt['seconds'])
                except Exception:
                    failure={'node':node,'traceback':traceback.format_exc()};v1.dump(folder/'failure.json',failure);failures.append(failure)
                    event('node_failed',**failure)
    oof=pd.concat(predictions,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True)
    v1.require(not oof.duplicated(['model_id',*KEY]).any(),'OOF duplicado');v1.assert_2023(oof.drop_duplicates(KEY))
    retained=oof.loc[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True)
    v1.require(retained.equals(base_oof.sort_values(['model_id',*KEY]).reset_index(drop=True)),'Comparadores modificados')
    pq.write_table(pa.Table.from_pandas(oof,preserve_index=False),run_dir/'oof_2023.parquet')
    ids=plan['comparators_reused_without_refit']+[x['id'] for x in plan['models']]
    summary=[];segments=[];sensitivities=[];complete=[]
    for mid in ids:
        part=oof.loc[oof.model_id.eq(mid)];valid=len(part)==50094 and not any(x['node'].startswith(mid+'_') for x in failures)
        summary.append({'model_id':mid,'technical_complete':valid,**(v1.metrics(part) if len(part) else {'rows':0})})
        if valid:complete.append(mid)
        if not len(part):continue
        for label,values in [('line',part.line),('fold',part.fold),('business',np.where(part.x_new_business.eq(1),'new_business','renewal'))]:
            for value,sub in part.assign(label=values).groupby('label',observed=True):segments.append({'model_id':mid,'segment':label,'label':str(value),**v1.metrics(sub)})
        for scenario,(ycol,ecol) in v1.SCENARIOS.items():
            sub=part.assign(scenario_prediction=part.annual_rate*part[ecol])
            sensitivities.append({'model_id':mid,'scenario':scenario,'scope':'Fixed base fitted OOF rates only; not refitted confirmation scenarios',**v1.metrics(sub,ycol,'scenario_prediction')})
    pairs=v1.paired_diagnostics(oof,complete,run_dir/'diagnostics',plan['diagnostics']['development_uncertainty'])
    v1.dump(run_dir/'diagnostics/pairs.json',pairs);v1.dump(run_dir/'diagnostics/segments.json',segments)
    v1.dump(run_dir/'diagnostics/observation_sensitivity.json',sensitivities)
    v1.dump(run_dir/'diagnostics/training_nodes.json',training_nodes)
    oldtrain=v1.read(parent/'diagnostics/fit_vs_oof.json');train_summary=[]
    for mid in ids:
        point=next(x for x in summary if x['model_id']==mid)
        if mid in plan['comparators_reused_without_refit']:
            a=next(x for x in oldtrain['summary'] if x['model_id']==mid)['training_repeated_rows']
        else:
            nodes=[x for x in training_nodes if x['model_id']==mid]
            if len(nodes)!=15:continue
            a={key:sum(x[key] for x in nodes) for key in ['rows','observed_total','predicted_total','deviance_sum']}
            a['D2']=1-a['deviance_sum']/(4*point['null_deviance_sum']);a['actual_over_expected']=a['observed_total']/a['predicted_total']
        train_summary.append({'model_id':mid,'training_repeated_rows':a,'OOF_D2':point['D2'],
                              'gap_train_minus_OOF':a['D2']-point['D2'],'OOF_actual_over_expected':point['actual_over_expected']})
    v1.dump(run_dir/'diagnostics/fit_vs_oof.json',{'scope':'Training rows repeated four times; no independent validation claim','summary':train_summary})
    for item in sources:v1.require(v1.sha(ROOT/item['path'])==item['sha256'],'Fuente cambió '+item['path'])
    v1.require(not ledger.exists(),'Ledger concurrente creado; no declarar cierre sin revisarlo')
    report={'id':plan['id'],'author':'Codex','started_utc':started.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),
        'run':v1.relative(run_dir),'parent_run':plan['parent_run'],'parent_oof_sha256':plan['parent_oof_sha256'],
        'plan_sha256':v1.sha(PLAN),'code_sha256':v1.sha(Path(__file__)),'summary':summary,'pairs':pairs['pairs'],
        'training_summary':train_summary,'nodes_completed':len(receipts),'nodes_failed':len(failures),'failures':failures,
        'new_estimator_fits':sum(x['mode']=='new_fit' for x in receipts),'GLM_bundle_reuses':sum(x['mode']=='reuse_W2-B01' for x in receipts),
        'prefix_exports':sum(x['mode']=='prefix_W2-B02' for x in receipts),'comparators_reused_exactly':True,
        'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,
        'reference_retained':'W2-B00','all_alternatives_preserved':True,'promotion':False,'final_confirmation_roster_frozen':False,
        'search_disclosure':plan['search_disclosure'],'scenario_scope':'Fixed base fitted OOF rates only',
        'elapsed_seconds':time.perf_counter()-tick,'submissions':0,'remote_training':False,'independent_professional_validation':False}
    v1.dump(run_dir/'report.json',report)
    event('run_completed',run=v1.relative(run_dir),new_fits=report['new_estimator_fits'],failures=len(failures),seconds=report['elapsed_seconds'])
    v1.dump(run_dir/'manifest.json',{'run':v1.relative(run_dir),'files':[{'path':p.relative_to(run_dir).as_posix(),'sha256':v1.sha(p),'bytes':p.stat().st_size} for p in sorted(run_dir.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':v1.relative(run_dir),'summary':summary,'training_summary':train_summary,'failed':len(failures)},ensure_ascii=True),flush=True)
    return 0 if not failures else 2


if __name__=='__main__':raise SystemExit(run())
