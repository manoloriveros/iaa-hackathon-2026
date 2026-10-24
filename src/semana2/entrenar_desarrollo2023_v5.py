"""Constantes por negocio y GLM pequeño sin interacciones: solo 2023."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,time,uuid,warnings
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('dev5_frozen_utils',REPO/'src/semana2/entrenar_desarrollo2023.py')
u=importlib.util.module_from_spec(s);sys.modules[s.name]=u;s.loader.exec_module(u)
np,pd,pq,joblib=u.np,u.pd,u.pq,u.joblib;KEY=u.KEY;PLAN=REPO/'registro/semana2_desarrollo2023_plan_v5.json'

def constant_fit(frame,fold):
    u.assert_2023(frame);u.require(frame.fold.ne(fold).all(),'Retenido en ajuste')
    u.require(set(frame.x_new_business.unique())=={0.,1.},'Segmento inválido')
    result={};details=[]
    for b in [0,1]:
        f=frame.loc[frame.x_new_business.eq(b)];e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)
        u.require(np.isfinite(e).all() and (e>0).all() and np.isfinite(y).all() and (y>=0).all(),'Respuesta/exposición inválida')
        r=float(np.sum(y/np.sqrt(e))/np.sqrt(e).sum());u.require(r>0 and np.isfinite(r),'Constante no positiva')
        result[b]=r;details.append({'business':b,'rate':r,'fit_rows':len(f),'positive_rows':int(f.T0.gt(0).sum()),'exposure_sum':float(e.sum()),'observed':float(y.sum())})
    return {'family':'business_constant','rates':result,'columns':['x_new_business']},details

def predict(bundle,frame):
    u.assert_2023(frame)
    if bundle['family']=='business_constant':
        u.require(frame.x_new_business.isin([0,1]).all(),'Negocio inválido');return np.array([bundle['rates'][int(x)] for x in frame.x_new_business])
    return u.predict_bundle(bundle,frame)

def glm_fit(frame,fold,recipe,line):
    u.assert_2023(frame);u.require(frame.fold.ne(fold).all(),'Retenido en GLM')
    block=recipe['features_by_line'][line];cols=block['all'];u.require(len(cols)==6 and len(set(cols))==6,'Core distinto')
    transformer=u.ColumnTransformer([('numeric',u.Pipeline([('median',u.SimpleImputer(strategy='median',keep_empty_features=True)),('scale',u.StandardScaler())]),block['numeric']),
      ('categorical',u.OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,max_categories=40,sparse_output=True),block['categorical'])],sparse_threshold=1.)
    x=transformer.fit_transform(frame[cols]);e=frame['e_cost_mix_1.0'].to_numpy(float);y=frame.T0.to_numpy(float)/e;weight=np.sqrt(e)
    est=u.TweedieRegressor(**recipe['params'])
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');est.fit(x,y,sample_weight=weight)
    messages=[{'category':n.category.__name__,'message':str(n.message)} for n in notes]
    u.require(not any(issubclass(n.category,u.ConvergenceWarning) for n in notes) and est.n_iter_<2000,'No convergió '+str(messages))
    rate=est.predict(x);g=weight*(np.sqrt(rate)-y/np.sqrt(rate))/weight.sum();gradient=np.r_[np.asarray(x.T@g).ravel(),g.sum()]
    # Fixed numerical readout, not a model/metric selection threshold.
    u.require(float(np.abs(gradient).max())<=1e-4,'Gradiente GLM no concuerda con convergencia a tolerancia técnica fija 1e-4')
    bundle={'family':'TweedieRegressor','columns':cols,'transformer':transformer,'estimator':est}
    return bundle,{'n_iter':int(est.n_iter_),'transformed_features':x.shape[1],'parameters':est.get_params(),'warnings':messages,
                   'max_abs_score_gradient':float(np.abs(gradient).max()),'gradient_threshold_before_fit':1e-4,'fit_rows':len(frame)}

def as_oof(valid,mid,r):
    cols=KEY+['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','x_new_business',*[x[1] for x in u.SCENARIOS.values()]]
    p=valid[cols].copy();p['model_id']=mid;p['annual_rate']=r;p['prediction']=valid['e_cost_mix_1.0'].to_numpy()*r
    u.require(np.isfinite(r).all() and (r>0).all(),'Predicción inválida');p['unit_deviance']=u.unit_deviance(valid.T0,p.prediction);return p

def main():
    start=datetime.now(timezone.utc);tick=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['parent_run']
    u.require(u.sha(parent/'manifest.json')==plan['parent_manifest_sha256'] and u.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'],'Padre cambiado')
    selector=u.read(REPO/'registro/semana2_seleccion_actual.json');ledger=ROOT/selector['ledger_workspace_relative'];u.require(not ledger.exists(),'2024 debe permanecer cerrado')
    u.require(u.sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'],'Política cambiada')
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(b'<!-- aporte:COD-S2-20261023-016 -->')==1,'Falta receta previa')
    out=parent.parent/('dev5_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    for name in ['inputs_2023','links_2023','fit_rows','models','diagnostics']:(out/name).mkdir()
    def event(name,**values):
        t=json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'event':name,**values})
        with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(t+'\n')
        print(t,flush=True)
    event('started',run=u.relative(out),year=2023)
    for p,name in [(PLAN,'plan_snapshot.json'),(Path(__file__),'code_snapshot.py'),(parent/'readiness_snapshot.json','readiness_snapshot.json'),
                   (parent/'environment.json','environment.json'),(REPO/'src/semana2/entrenar_desarrollo2023.py','utility_snapshot.py')]:
        (out/name).write_bytes(p.read_bytes())
    (out/'forum_before_fit.md').write_bytes(forum)
    sources=[parent/x['path'] for x in u.read(parent/'manifest.json')['files']]+[parent/'manifest.json',PLAN,Path(__file__),ROOT/plan['selection_policy'],REPO/'src/semana2/entrenar_desarrollo2023.py']
    frozen=[{'path':u.relative(p),'sha256':u.sha(p)} for p in dict.fromkeys(sources)];u.dump(out/'frozen_sources_before_fit.json',{'files':frozen})
    for folder in ['inputs_2023','links_2023','fit_rows']:
        for p in (parent/folder).glob('*.parquet'):(out/folder/p.name).write_bytes(p.read_bytes())
    base=pq.read_table(parent/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas();u.assert_2023(base.drop_duplicates(KEY));u.require(len(base)==12*50094 and not base.duplicated(['model_id',*KEY]).any(),'OOF de referencia incompleto')
    ready=u.read(out/'readiness_snapshot.json');availability=u.read(ROOT/ready['availability_contract'])['blocks'];outputs=[base];receipts=[]
    glm=next(x for x in plan['models'] if x['id']=='W2-B13')
    for line in u.LINES:
        data=u.load_2023(out/f'inputs_2023/{line}.parquet');block=glm['features_by_line'][line]
        u.require(set(block['all'])<=set(availability[line]['all']),'Core fuera de contrato')
        for fold in range(5):
            links=u.load_2023(out/f'links_2023/{line}_fold{fold}.parquet');offsets=[x[1] for x in u.SCENARIOS.values()]
            f=data.merge(links[KEY+offsets],on=KEY,validate='one_to_one');fit=f[f.fold.ne(fold)];valid=f[f.fold.eq(fold)]
            for col in ['group_id','customer_id','address_id']:u.require(not set(fit[col])&set(valid[col]),'Fuga '+col)
            with u.threadpool_limits(limits=2):b12,n12=constant_fit(fit,fold);b13,n13=glm_fit(fit,fold,glm,line)
            for mid,bundle,notes in [('W2-B12',b12,{'segment_constants':n12}),('W2-B13',b13,n13)]:
                folder=out/'models'/f'{mid}_{line}_fold{fold}';folder.mkdir();joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                with u.threadpool_limits(limits=2):r=predict(bundle,valid);replay=predict(joblib.load(folder/'bundle.joblib'),valid)
                u.require(np.array_equal(r,replay),'Replay distinto');outputs.append(as_oof(valid,mid,r))
                record={'model_id':mid,'line':line,'fold':fold,'train_rows':len(fit),'validation_rows':len(valid),'features':bundle['columns'],'replay_exact':True,**notes}
                u.dump(folder/'receipt.json',record);receipts.append(record)
            event('scope_completed',line=line,fold=fold,glm_gradient=n13['max_abs_score_gradient'])
    oof=pd.concat(outputs,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True)
    u.require(oof[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True).equals(base.sort_values(['model_id',*KEY]).reset_index(drop=True)),'Referencias cambiadas')
    u.require(oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any(),'OOF inválido');oof.to_parquet(out/'oof_2023.parquet',index=False)
    summary=[];segments=[];scenarios=[]
    ids=plan['comparators_reused_without_refit']+[m['id'] for m in plan['models']]
    for mid in ids:
        p=oof[oof.model_id.eq(mid)];u.require(len(p)==50094,'Modelo incompleto');summary.append({'model_id':mid,**u.metrics(p)})
        for dim,lab in [('line',p.line),('fold',p.fold),('business',np.where(p.x_new_business.eq(1),'new_business','renewal')),
                        ('line_business',p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal'))]:
            for label,sub in p.assign(label=lab).groupby('label',observed=True):segments.append({'model_id':mid,'segment':dim,'label':str(label),**u.metrics(sub)})
        for name,(yc,ec) in u.SCENARIOS.items():
            pp=p.assign(scenario_prediction=p.annual_rate*p[ec]);scenarios.append({'model_id':mid,'scenario':name,**u.metrics(pp,yc,'scenario_prediction')})
    pairs=u.paired_diagnostics(oof,ids,out/'diagnostics',plan['diagnostics']['development_uncertainty'])
    for name,value in [('pairs',pairs),('segments',segments),('observation_sensitivity',scenarios)]:u.dump(out/f'diagnostics/{name}.json',value)
    for item in frozen:u.require(u.sha(ROOT/item['path'])==item['sha256'],'Fuente cambiada '+item['path'])
    u.require(not ledger.exists(),'Ledger concurrente');report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),
      'plan_sha256':u.sha(PLAN),'code_sha256':u.sha(Path(__file__)),'parent_oof_sha256':plan['parent_oof_sha256'],'summary':summary,'pairs':pairs['pairs'],'receipts':receipts,
      'new_base_estimator_fits':15,'new_closed_form_constants':30,'cumulative_base_estimator_fits':80,'cumulative_closed_form_constants':60,
      'new_postfit_factors':0,'parent_comparators_exactly_unchanged':True,'reference_retained':'W2-B00','all_alternatives_preserved':True,'promotion':False,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote_training':False,
      'final_confirmation_roster_frozen':False,'professional_independent_validation':False,'search_disclosure':plan['search_disclosure'],'elapsed_seconds':time.perf_counter()-tick}
    u.dump(out/'report.json',report);event('completed',run=u.relative(out),seconds=report['elapsed_seconds'])
    u.dump(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':u.relative(out),'new_summary':summary[-2:],'primary_contrasts':[p for p in pairs['pairs'] if (p['candidate'],p['reference']) in [('W2-B12','W2-B00'),('W2-B13','W2-B12')]]}),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
