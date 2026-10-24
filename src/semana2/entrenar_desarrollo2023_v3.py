"""Ancla B00 de nivel y contracción fija en 2023; no ajusta estimadores base."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,os,sys,time,uuid
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='2'
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('dev3_frozen_utils',REPO/'src/semana2/entrenar_desarrollo2023.py')
u=importlib.util.module_from_spec(spec);sys.modules[spec.name]=u;spec.loader.exec_module(u)
np,pd,pq,pa,joblib=u.np,u.pd,u.pq,u.pa,u.joblib;KEY=u.KEY
PLAN=REPO/'registro/semana2_desarrollo2023_plan_v3.json'
BASE_FIT_ATTEMPTS=0


def forbid_fit(*args,**kwargs):
    global BASE_FIT_ATTEMPTS
    BASE_FIT_ATTEMPTS+=1
    raise RuntimeError('Los estimadores base están congelados en v3')


def block_base_fits():
    for cls in [u.TweedieRegressor,u.SimpleImputer,u.StandardScaler,u.OneHotEncoder,u.ColumnTransformer,u.Pipeline,u.lgb.LGBMRegressor,u.lgb.LGBMModel]:
        cls.fit=forbid_fit
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbid_fit


def anchor_scale(exposure,parent_rate,reference_rate):
    e=np.asarray(exposure,dtype=float);r=np.asarray(parent_rate,dtype=float);ref=np.asarray(reference_rate,dtype=float)
    u.require(e.ndim==1 and len(e)>0 and e.shape==r.shape==ref.shape,'Dimensiones inválidas')
    u.require(all(np.isfinite(x).all() and (x>0).all() for x in [e,r,ref]),'Entrada no positiva/finita')
    return float(np.dot(e,ref)/np.dot(e,r))


def fit_anchor(fit,parent,reference,heldout_fold):
    u.assert_2023(fit)
    u.require('fold' in fit and fit.fold.ne(heldout_fold).all(),'Fila retenida en ajuste de nivel')
    u.require(reference['family']=='constant_line_rate' and reference['rate']>0,'Ancla B00 inválida')
    # Deliberadamente no lee T0, reservas ni variables del fold retenido.
    r=u.predict_bundle(parent,fit);r0=u.predict_bundle(reference,fit);e=fit['e_cost_mix_1.0'].to_numpy()
    scale=anchor_scale(e,r,r0)
    return scale,{'fit_rows':len(fit),'exposure_sum':float(e.sum()),'parent_fit_total':float(np.dot(e,r)),
                  'reference_fit_total':float(np.dot(e,r0)),'scale':scale,'reference_rate':float(reference['rate'])},r


def predict(bundle,frame):
    u.assert_2023(frame)
    u.require(bundle['family']=='AnchoredRate' and bundle['shape_weight'] in [1.,.5],'Adaptador no registrado')
    u.require(np.isfinite(bundle['scale']) and bundle['scale']>0,'Escala inválida')
    r=u.predict_bundle(bundle['parent'],frame);w=bundle['shape_weight']
    return (1-w)*bundle['reference_rate']+w*bundle['scale']*r


def run():
    started=datetime.now(timezone.utc);timer=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['parent_run'];refdir=ROOT/plan['reference_model_run']
    u.require(u.sha(parent/'manifest.json')==plan['parent_manifest_sha256'] and u.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'],'Fuentes v2 cambiadas')
    u.require(u.sha(ROOT/plan['diagnostic_review'])==plan['diagnostic_sha256'],'Diagnóstico cambiado')
    u.require(u.sha(REPO/'src/semana2/entrenar_desarrollo2023.py')==u.read(refdir/'report.json')['code_sha256'],'Utilidades v1 cambiadas')
    selector_path=REPO/'registro/semana2_seleccion_actual.json';selector=u.read(selector_path);ledger=ROOT/selector['ledger_workspace_relative']
    u.require(not ledger.exists(),'Revisar ledger concurrente: este encargo mantiene 2024 cerrado')
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_bytes=forum.read_bytes()
    u.require(forum_bytes.count(b'<!-- aporte:COD-S2-20261023-012 -->')==1,'Falta preinscripción v3')
    u.require(u.sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'],'Política modificada')
    run_dir=parent.parent/('dev3_'+started.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);run_dir.mkdir()
    for name in ['inputs_2023','links_2023','fit_rows','models','factors','diagnostics']:(run_dir/name).mkdir()
    def event(kind,**values):
        text=json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event=kind,**values),ensure_ascii=True)
        with (run_dir/'events.jsonl').open('a',encoding='utf-8') as f:f.write(text+'\n')
        print(text,flush=True)
    event('run_started',run=u.relative(run_dir),year=2023,confirmation_2024_open=False)
    for src,dest in [(Path(__file__),'code_snapshot.py'),(PLAN,'plan_snapshot.json'),(parent/'readiness_snapshot.json','readiness_snapshot.json'),
                     (parent/'environment.json','environment.json'),(REPO/'src/semana2/entrenar_desarrollo2023.py','v1_utility_snapshot.py'),(selector_path,'selector_index_at_start.json')]:
        (run_dir/dest).write_bytes(src.read_bytes())
    (run_dir/'forum_before_training.md').write_bytes(forum_bytes)
    sources=[parent/x['path'] for x in u.read(parent/'manifest.json')['files']]
    sources += [parent/'manifest.json',PLAN,Path(__file__),REPO/'src/semana2/entrenar_desarrollo2023.py',ROOT/plan['diagnostic_review'],
                (ROOT/plan['diagnostic_review']).parent/'group_influence.parquet',ROOT/plan['selection_policy']]
    sources += [refdir/'models'/f'W2-B00_{line}_fold{fold}'/'bundle.joblib' for line in u.LINES for fold in range(5)]
    sources=list(dict.fromkeys(sources));frozen=[{'path':u.relative(p),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sources]
    u.dump(run_dir/'frozen_sources_before_fit.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':frozen})
    for folder in ['inputs_2023','links_2023','fit_rows']:
        for src in (parent/folder).glob('*.parquet'):(run_dir/folder/src.name).write_bytes(src.read_bytes())
    block_base_fits()
    baseline=pq.read_table(parent/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas();u.assert_2023(baseline.drop_duplicates(KEY))
    u.require(len(baseline)==6*50094,'Comparadores incompletos')
    ready=u.read(parent/'readiness_snapshot.json');blocks=u.read(ROOT/ready['availability_contract'])['blocks']
    outputs=[baseline];receipts=[];scales=[];training=[]
    for line in u.LINES:
        data=u.load_2023(run_dir/f'inputs_2023/{line}.parquet')
        for fold in range(5):
            links=u.load_2023(run_dir/f'links_2023/{line}_fold{fold}.parquet');offsets=[x[1] for x in u.SCENARIOS.values()]
            frame=data.merge(links[KEY+offsets],on=KEY,validate='one_to_one');fit=frame.loc[frame.fold.ne(fold)];valid=frame.loc[frame.fold.eq(fold)]
            for col in ['group_id','customer_id','address_id']:u.require(not set(fit[col])&set(valid[col]),'Fuga por '+col)
            reference_path=refdir/'models'/f'W2-B00_{line}_fold{fold}'/'bundle.joblib';reference=joblib.load(reference_path)
            cache={}
            for parent_id in ['W2-B03','W2-B05']:
                source_path=parent/'models'/f'{parent_id}_{line}_fold{fold}'/'bundle.joblib';source_receipt=u.read(source_path.with_name('receipt.json'))
                u.require(source_receipt['line']==line and source_receipt['fold']==fold,'Modelo padre fuera de ámbito')
                base=joblib.load(source_path);u.require(base['columns']==blocks[line]['all'],'Variables padre fuera de contrato')
                with u.threadpool_limits(limits=2):s,details,train_rate=fit_anchor(fit,base,reference,fold);rate=u.predict_bundle(base,valid)
                details.update(parent_model=parent_id,line=line,fold=fold,parent_bundle=u.relative(source_path),parent_sha256=u.sha(source_path),
                               reference_bundle=u.relative(reference_path),reference_sha256=u.sha(reference_path),heldout_rows=len(valid),
                               factor_fit_uses_heldout_rows=False,independent_calibration=False)
                u.dump(run_dir/'factors'/f'{parent_id}_{line}_fold{fold}.json',details);scales.append(details)
                cache[parent_id]=(base,s,rate,train_rate,details)
            for recipe in plan['models']:
                mid=recipe['id'];base,s,rate,train_rate,details=cache[recipe['parent_model']];w=recipe['shape_weight']
                bundle={'family':'AnchoredRate','parent':base,'parent_model_id':recipe['parent_model'],'columns':base['columns'],
                        'scale':s,'reference_rate':reference['rate'],'shape_weight':w,'line':line,'fold':fold}
                node=f'{mid}_{line}_fold{fold}';folder=run_dir/'models'/node;folder.mkdir()
                actual=(1-w)*reference['rate']+w*s*rate;fit_actual=(1-w)*reference['rate']+w*s*train_rate
                fit_sum=float(np.dot(fit['e_cost_mix_1.0'],fit_actual))
                u.require(np.isclose(fit_sum,details['reference_fit_total'],rtol=1e-12,atol=1e-8),'No conserva ancla de ajuste')
                pred=valid['e_cost_mix_1.0'].to_numpy()*actual;loss=u.unit_deviance(valid.T0,pred)
                u.require(np.isclose(loss.mean(),u.mean_tweedie_deviance(valid.T0,pred,power=1.5),rtol=1e-12,atol=1e-9),'Scorer discrepante')
                joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                with u.threadpool_limits(limits=2):replay=predict(joblib.load(folder/'bundle.joblib'),valid)
                u.require(np.array_equal(actual,replay),'Replay distinto')
                result=valid[KEY+['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','x_new_business',*offsets]].copy()
                result['model_id']=mid;result['annual_rate']=actual;result['prediction']=pred;result['unit_deviance']=loss;outputs.append(result)
                receipt={'node':node,'model_id':mid,'line':line,'fold':fold,'parent_model':recipe['parent_model'],'scale':s,'shape_weight':w,
                         'train_rows':len(fit),'validation_rows':len(valid),'fit_predicted_total':fit_sum,'fit_reference_total':details['reference_fit_total'],
                         'features':blocks[line]['all'],'parent_bundle':details['parent_bundle'],'parent_sha256':details['parent_sha256'],
                         'reference_bundle':details['reference_bundle'],'reference_sha256':details['reference_sha256'],'serialized_replay_exact':True,
                         'scope':'Training-level normalization; no independent or inner-OOF calibration'}
                u.dump(folder/'receipt.json',receipt);receipts.append(receipt)
                training.append({'model_id':mid,'line':line,'fold':fold,'fit_predicted_total':fit_sum,'reference_fit_total':details['reference_fit_total'],
                                 'deviance_sum':float(u.unit_deviance(fit.T0,fit['e_cost_mix_1.0'].to_numpy()*fit_actual).sum())})
            event('scope_completed',line=line,fold=fold,adapters=4)
    oof=pd.concat(outputs,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True);u.assert_2023(oof.drop_duplicates(KEY))
    u.require(not oof.duplicated(['model_id',*KEY]).any(),'OOF repetido')
    retained=oof.loc[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True)
    u.require(retained.equals(baseline.sort_values(['model_id',*KEY]).reset_index(drop=True)),'Comparadores cambiados')
    pq.write_table(pa.Table.from_pandas(oof,preserve_index=False),run_dir/'oof_2023.parquet')
    ids=plan['comparators_reused_without_refit']+[x['id'] for x in plan['models']];summary=[];segments=[];sensitivity=[]
    for mid in ids:
        part=oof.loc[oof.model_id.eq(mid)];u.require(len(part)==50094,'Receta incompleta')
        summary.append({'model_id':mid,'technical_complete':True,**u.metrics(part)})
        for dimension,labels in [('line',part.line),('fold',part.fold),('business',np.where(part.x_new_business.eq(1),'new_business','renewal'))]:
            for label,sub in part.assign(label=labels).groupby('label',observed=True):segments.append({'model_id':mid,'segment':dimension,'label':str(label),**u.metrics(sub)})
        for scenario,(ycol,ecol) in u.SCENARIOS.items():
            sub=part.assign(scenario_prediction=part.annual_rate*part[ecol]);sensitivity.append({'model_id':mid,'scenario':scenario,
               'scope':'Fixed base adapters/rates, not reanchored/refitted scenarios',**u.metrics(sub,ycol,'scenario_prediction')})
    pairs=u.paired_diagnostics(oof,ids,run_dir/'diagnostics',plan['diagnostics']['development_uncertainty'])
    u.dump(run_dir/'diagnostics/pairs.json',pairs);u.dump(run_dir/'diagnostics/segments.json',segments);u.dump(run_dir/'diagnostics/observation_sensitivity.json',sensitivity)
    u.dump(run_dir/'diagnostics/training_nodes.json',training)
    fixed=pq.read_table((ROOT/plan['diagnostic_review']).parent/'group_influence.parquet').to_pandas();influence=[]
    reference=oof.loc[oof.model_id.eq('W2-B00')].sort_values(KEY).reset_index(drop=True)
    for recipe in plan['models']:
        group_set=set(fixed.loc[fixed.model_id.eq(recipe['parent_model'])&fixed.favorable_rank.le(31),'group_id'])
        u.require(len(group_set)==31,'Lista congelada de padre incorrecta')
        part=oof.loc[oof.model_id.eq(recipe['id'])].sort_values(KEY).reset_index(drop=True);keep=~part.group_id.isin(group_set)
        delta=u.metrics(part.loc[keep])['D2']-u.metrics(reference.loc[keep])['D2']
        influence.append({'model_id':recipe['id'],'parent_model':recipe['parent_model'],'frozen_parent_groups_removed':31,
                          'delta_D2_after_frozen_parent_removal':delta,'scope':'Evaluation only, no fit or factor filtering'})
    u.dump(run_dir/'diagnostics/frozen_parent_influence.json',influence)
    for item in frozen:u.require(u.sha(ROOT/item['path'])==item['sha256'],'Fuente cambió '+item['path'])
    u.require(BASE_FIT_ATTEMPTS==0,'Se intentó ajustar un estimador base');u.require(not ledger.exists(),'No declarar cierre si cambió ledger concurrente')
    report={'id':plan['id'],'author':'Codex','started_utc':started.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),
      'run':u.relative(run_dir),'parent_run':plan['parent_run'],'parent_oof_sha256':plan['parent_oof_sha256'],'plan_sha256':u.sha(PLAN),'code_sha256':u.sha(Path(__file__)),
      'summary':summary,'pairs':pairs['pairs'],'training_level_factors':len(scales),'adapter_bundles':len(receipts),'base_estimator_fit_attempts':BASE_FIT_ATTEMPTS,
      'new_base_estimator_fits':0,'parent_comparators_exactly_unchanged':True,'factor_scope':'Outer-training rows only; normalization uses in-sample parent predictions, not independent calibration',
      'scales':scales,'frozen_parent_influence':influence,'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},
      'test_predictions':0,'submissions':0,'remote_training':False,'promotion':False,'reference_retained':'W2-B00','all_alternatives_preserved':True,
      'final_confirmation_roster_frozen':False,'search_disclosure':plan['search_disclosure'],'elapsed_seconds':time.perf_counter()-timer,'professional_independent_validation':False}
    u.dump(run_dir/'report.json',report);event('run_completed',run=u.relative(run_dir),factors=len(scales),adapters=len(receipts),seconds=report['elapsed_seconds'])
    u.dump(run_dir/'manifest.json',{'run':u.relative(run_dir),'files':[{'path':p.relative_to(run_dir).as_posix(),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sorted(run_dir.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':u.relative(run_dir),'new_summary':summary[6:],'new_reference_pairs':[p for p in pairs['pairs'] if p['reference']=='W2-B00' and p['candidate'] in [x['id'] for x in plan['models']]],
                      'base_fits':0,'factors':len(scales),'adapters':len(receipts)},ensure_ascii=True),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(run())
