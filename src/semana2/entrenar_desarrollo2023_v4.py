"""Nivel por negocio y sensibilidad de reentrenamiento, exclusivamente 2023."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,uuid,copy,time
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('dev4_utils',REPO/'src/semana2/entrenar_desarrollo2023.py')
u=importlib.util.module_from_spec(spec);sys.modules[spec.name]=u;spec.loader.exec_module(u)
np,pd,pq,pa,joblib=u.np,u.pd,u.pq,u.pa,u.joblib;KEY=u.KEY
PLAN=REPO/'registro/semana2_desarrollo2023_plan_v4.json'

def parent_predict(bundle,frame):
    u.assert_2023(frame)
    u.require(bundle['family']=='AnchoredRate' and bundle['shape_weight']==.5,'Padre fuera de receta')
    return .5*bundle['reference_rate']+.5*bundle['scale']*u.predict_bundle(bundle['parent'],frame)

def business_factor(fit,rate,fold):
    u.assert_2023(fit);u.require(fit.fold.ne(fold).all(),'Fila retenida en calibración')
    e=fit['e_cost_mix_1.0'].to_numpy(float);r=np.asarray(rate,dtype=float);y=fit.T0.to_numpy(float)
    u.require(r.shape==e.shape and np.isfinite(r).all() and (r>0).all() and np.isfinite(e).all() and (e>0).all(),'Tasa o exposición inválida')
    u.require(np.isfinite(y).all() and (y>=0).all() and set(fit.x_new_business.unique())=={0.,1.},'Respuesta/segmentos inválidos')
    rows=[];mu=e*r
    for b in [0,1]:
        m=fit.x_new_business.eq(b).to_numpy();num=float(np.sum(y[m]/np.sqrt(mu[m])));den=float(np.sqrt(mu[m]).sum());q=num/den
        u.require(np.isfinite(q) and q>0,'Segmento sin factor positivo, se detiene la receta')
        rows.append({'business':b,'q':q,'numerator':num,'denominator':den,'fit_rows':int(m.sum()),'positive_rows':int((y[m]>0).sum()),
          'fit_observed':float(y[m].sum()),'fit_before':float(mu[m].sum()),'fit_after':float((q*mu[m]).sum())})
    return rows

def predict(bundle,frame):
    u.assert_2023(frame)
    u.require(bundle['family']=='BusinessLevelRate' and frame.x_new_business.isin([0,1]).all(),'Adaptador/segmento inválido')
    r=parent_predict(bundle['parent'],frame);q=np.where(frame.x_new_business.eq(1),bundle['factors'][1],bundle['factors'][0])
    u.require(np.isfinite(q).all() and (q>0).all(),'Escala inválida');return q*r

def stress_group_ids(frame,fold):
    u.assert_2023(frame);u.require(frame.fold.ne(fold).all(),'Fila retenida en selección de estrés')
    by=frame.groupby('group_id',observed=True).T0.sum().reset_index();by['tie']=by.group_id.astype(str)
    by=by.sort_values(['T0','tie'],ascending=[False,True],kind='stable');n=int(np.ceil(.001*len(by)))
    return by.iloc[:n].drop(columns='tie'),len(by)

def as_oof(valid,mid,rate):
    cols=KEY+['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','x_new_business',*[x[1] for x in u.SCENARIOS.values()]]
    result=valid[cols].copy();result['model_id']=mid;result['annual_rate']=rate;result['prediction']=valid['e_cost_mix_1.0'].to_numpy()*rate
    u.require(np.isfinite(rate).all() and (rate>0).all(),'Predicción no positiva/finita');result['unit_deviance']=u.unit_deviance(valid.T0,result.prediction);return result

def summarize(oof):
    summary=[];segments=[];scenarios=[]
    for mid,part in oof.groupby('model_id',observed=True):
        u.require(len(part)==50094,'OOF incompleto');summary.append({'model_id':mid,**u.metrics(part)})
        for dim,labels in [('line',part.line),('fold',part.fold),('business',np.where(part.x_new_business.eq(1),'new_business','renewal')),
                           ('line_business',part.line.astype(str)+'_'+np.where(part.x_new_business.eq(1),'new_business','renewal'))]:
            for label,sub in part.assign(label=labels).groupby('label',observed=True):segments.append({'model_id':mid,'segment':dim,'label':str(label),**u.metrics(sub)})
        for scenario,(ycol,ecol) in u.SCENARIOS.items():
            sub=part.assign(scenario_prediction=part.annual_rate*part[ecol]);scenarios.append({'model_id':mid,'scenario':scenario,**u.metrics(sub,ycol,'scenario_prediction')})
    return summary,segments,scenarios

def run():
    start=datetime.now(timezone.utc);clock=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['parent_run'];reference=ROOT/plan['reference_model_run']
    u.require(u.sha(parent/'manifest.json')==plan['parent_manifest_sha256'] and u.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'],'Fuente cambiada')
    u.require(u.sha(ROOT/plan['diagnostic_review'])==plan['diagnostic_sha256'],'Diagnóstico cambiado')
    selection=u.read(REPO/'registro/semana2_seleccion_actual.json');ledger=ROOT/selection['ledger_workspace_relative'];u.require(not ledger.exists(),'2024 debe seguir cerrado')
    u.require(u.sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'],'Política cambiada')
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_bytes=forum.read_bytes();u.require(forum_bytes.count(b'<!-- aporte:COD-S2-20261023-014 -->')==1,'Falta preinscripción')
    out=parent.parent/('dev4_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    for folder in ['inputs_2023','links_2023','fit_rows','models','factors','stress_models','stress_groups','diagnostics']:(out/folder).mkdir()
    def event(kind,**values):
        t=json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'event':kind,**values})
        with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(t+'\n')
        print(t,flush=True)
    event('started',run=u.relative(out),year=2023)
    for src,dest in [(PLAN,'plan_snapshot.json'),(Path(__file__),'code_snapshot.py'),(parent/'readiness_snapshot.json','readiness_snapshot.json'),
                     (parent/'environment.json','environment.json'),(REPO/'src/semana2/entrenar_desarrollo2023.py','utility_snapshot.py')]:
        (out/dest).write_bytes(src.read_bytes())
    (out/'forum_before_fit.md').write_bytes(forum_bytes)
    sources=[parent/x['path'] for x in u.read(parent/'manifest.json')['files']]+[parent/'manifest.json',PLAN,Path(__file__),
             ROOT/plan['diagnostic_review'],ROOT/plan['selection_policy'],REPO/'src/semana2/entrenar_desarrollo2023.py',reference/'plan_snapshot.json']
    for name in ['inputs_2023','links_2023','fit_rows']:
        for p in (parent/name).glob('*.parquet'):(out/name/p.name).write_bytes(p.read_bytes())
    frozen=[{'path':u.relative(p),'sha256':u.sha(p)} for p in dict.fromkeys(sources)]
    u.dump(out/'frozen_sources_before_fit.json',{'files':frozen})
    baseline=pq.read_table(parent/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas()
    u.assert_2023(baseline.drop_duplicates(KEY));u.require(not baseline.duplicated(['model_id',*KEY]).any() and len(baseline)==10*50094,'Comparadores incompletos')
    ready=u.read(out/'readiness_snapshot.json');blocks=u.read(ROOT/ready['availability_contract'])['blocks']
    data={line:u.load_2023(out/f'inputs_2023/{line}.parquet') for line in u.LINES}
    cfg=u.read(reference/'plan_snapshot.json');glm=next(x for x in cfg['models'] if x['id']=='W2-B01');constant=next(x for x in cfg['models'] if x['id']=='W2-B00')
    outputs=[baseline];stress=[];receipts=[];stress_receipts=[];fit_count=0
    for fold in range(5):
        pooled=pd.concat([df.loc[df.fold.ne(fold),KEY+['year','is_test','group_id','fold','T0']] for df in data.values()],ignore_index=True)
        dropped,n_groups=stress_group_ids(pooled,fold);excluded=set(dropped.group_id);dropped.to_parquet(out/f'stress_groups/fold{fold}.parquet',index=False)
        u.require(not excluded&set(pd.concat([df.loc[df.fold.eq(fold),'group_id'] for df in data.values()])),'Grupo retenido elegido para estrés')
        for line in u.LINES:
            links=u.load_2023(out/f'links_2023/{line}_fold{fold}.parquet');offsets=[x[1] for x in u.SCENARIOS.values()]
            frame=data[line].merge(links[KEY+offsets],on=KEY,validate='one_to_one');fit=frame.loc[frame.fold.ne(fold)].copy();valid=frame.loc[frame.fold.eq(fold)].copy()
            for col in ['group_id','customer_id','address_id']:u.require(not set(fit[col])&set(valid[col]),'Fuga '+col)
            for recipe in plan['models']:
                mid=recipe['id'];path=parent/'models'/f"{recipe['parent_model']}_{line}_fold{fold}/bundle.joblib";base=joblib.load(path)
                u.require(base['columns']==blocks[line]['all'],'Variables cambiadas')
                with u.threadpool_limits(limits=2):r=parent_predict(base,fit);rr=parent_predict(base,valid)
                details=business_factor(fit,r,fold);qs={x['business']:x['q'] for x in details}
                bundle={'family':'BusinessLevelRate','parent':base,'factors':qs,'columns':base['columns'],'line':line,'fold':fold,'parent_model':recipe['parent_model']}
                folder=out/'models'/f'{mid}_{line}_fold{fold}';folder.mkdir();joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                expected=rr*np.where(valid.x_new_business.eq(1),qs[1],qs[0])
                with u.threadpool_limits(limits=2):replay=predict(joblib.load(folder/'bundle.joblib'),valid)
                u.require(np.array_equal(expected,replay),'Replay de negocio distinto');outputs.append(as_oof(valid,mid,replay))
                rec={'model_id':mid,'line':line,'fold':fold,'parent':u.relative(path),'parent_sha256':u.sha(path),'factors':details,'train_rows':len(fit),'validation_rows':len(valid),'replay_exact':True}
                receipts.append(rec);u.dump(folder/'receipt.json',rec);u.dump(out/'factors'/f'{mid}_{line}_fold{fold}.json',rec)
            reduced=fit.loc[~fit.group_id.isin(excluded)].copy();u.require(len(reduced)>0 and reduced.fold.ne(fold).all(),'Estrés vacío/fuera de ámbito')
            spec_glm=copy.deepcopy(glm);spec_glm['params']['alpha']=10. if line=='buildings' else 1.
            with u.threadpool_limits(limits=2):
                ref,cn=u.fit_bundle(constant,reduced,blocks[line]);native,gn=u.fit_bundle(spec_glm,reduced,blocks[line]);fit_count+=1
                raw=u.predict_bundle(native,reduced);r=u.predict_bundle(native,valid)
            e=reduced['e_cost_mix_1.0'].to_numpy();s=float((e*ref['rate']).sum()/np.dot(e,raw))
            adapter={'family':'AnchoredRate','parent':native,'parent_model_id':'stress_B03','columns':native['columns'],'scale':s,'reference_rate':ref['rate'],'shape_weight':.5,'line':line,'fold':fold}
            folder=out/'stress_models'/f'{line}_fold{fold}';folder.mkdir();joblib.dump({'S00':ref,'S08':adapter},folder/'bundle.joblib',compress=3)
            saved=joblib.load(folder/'bundle.joblib')
            with u.threadpool_limits(limits=2):rv=parent_predict(saved['S08'],valid);r0=u.predict_bundle(saved['S00'],valid)
            u.require(np.array_equal(rv,.5*ref['rate']+.5*s*r),'Replay estrés distinto')
            stress.extend([as_oof(valid,'S08',rv),as_oof(valid,'S00',r0)])
            rec={'line':line,'fold':fold,'original_training_groups':n_groups,'deleted_groups':len(excluded),'original_fit_rows':len(fit),'remaining_fit_rows':len(reduced),
                 'deleted_rows_in_line':len(fit)-len(reduced),'deleted_observed_in_line':float(fit.T0.sum()-reduced.T0.sum()),'glm':gn,'constant':cn,'scale':s,
                 'original_C0_fixed':True,'heldout_rows':len(valid),'replay_exact':True}
            u.dump(folder/'receipt.json',rec);stress_receipts.append(rec);event('scope_completed',fold=fold,line=line)
    oof=pd.concat(outputs,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True)
    stress=pd.concat(stress,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True)
    u.require(not oof.duplicated(['model_id',*KEY]).any() and oof.year.eq(2023).all(),'Claves/años OOF inválidos')
    u.require(oof[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True).equals(baseline.sort_values(['model_id',*KEY]).reset_index(drop=True)),'Comparadores cambiados')
    oof.to_parquet(out/'oof_2023.parquet',index=False);stress.to_parquet(out/'stress_oof_2023.parquet',index=False)
    summary,segments,scenarios=summarize(oof);ssummary,ssegments,sscenarios=summarize(stress)
    for name,content in [('segments',segments),('observation_sensitivity',scenarios),('stress_segments',ssegments),('stress_scenarios',sscenarios)]:u.dump(out/f'diagnostics/{name}.json',content)
    pairs=u.paired_diagnostics(oof,plan['comparators_reused_without_refit']+[m['id'] for m in plan['models']],out/'diagnostics',plan['diagnostics']['development_uncertainty'])
    u.dump(out/'diagnostics/pairs.json',pairs)
    fixed=[];review=(ROOT/plan['diagnostic_review']).parent;ref=oof[oof.model_id.eq('W2-B00')].sort_values(KEY).reset_index(drop=True)
    for m in plan['models']:
        groups=pq.read_table(review/f"{m['parent_model']}_influence.parquet").to_pandas().sort_values('gain',ascending=False,kind='stable').index[:31]
        p=oof[oof.model_id.eq(m['id'])].sort_values(KEY).reset_index(drop=True);keep=~p.group_id.isin(groups)
        fixed.append({'model_id':m['id'],'parent':m['parent_model'],'removed_groups':31,'delta_D2_after_removal':u.metrics(p.loc[keep])['D2']-u.metrics(ref.loc[keep])['D2']})
    u.dump(out/'diagnostics/frozen_parent_influence.json',fixed)
    rates=[]
    for mid in ['W2-B08','W2-B09']:
        p=oof[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True)
        s=stress[stress.model_id.eq('S08')].sort_values(KEY).reset_index(drop=True)
        if mid=='W2-B08':
            ratios=s.annual_rate.to_numpy()/p.annual_rate.to_numpy()-1
            rates.append({'stress':'S08','comparison':mid,'median_relative_rate_change':float(np.median(ratios)),'p01':float(np.quantile(ratios,.01)),'p99':float(np.quantile(ratios,.99)),'max_absolute':float(np.abs(ratios).max())})
    for item in frozen:u.require(u.sha(ROOT/item['path'])==item['sha256'],'Fuente modificada '+item['path'])
    u.require(fit_count==15 and not ledger.exists(),'Recuento/ledger cambiado')
    report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),
      'code_sha256':u.sha(Path(__file__)),'plan_sha256':u.sha(PLAN),'parent_oof_sha256':plan['parent_oof_sha256'],'summary':summary,'stress_summary':ssummary,
      'pairs':pairs['pairs'],'factors':receipts,'frozen_parent_influence':fixed,'stress_receipts':stress_receipts,'stress_rate_changes':rates,
      'new_candidate_base_fits':0,'new_level_factors':60,'new_adapter_bundles':30,'stress_glm_fits':15,'stress_constants':15,
      'cumulative_base_estimator_fits':65,'cumulative_constants':30,'parent_comparators_exactly_unchanged':True,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote_training':False,
      'promotion':False,'reference_retained':'W2-B00','all_alternatives_preserved':True,'final_confirmation_roster_frozen':False,
      'professional_independent_validation':False,'search_disclosure':plan['search_disclosure'],'stress_scope':plan['stability_stress']['observation_link'],
      'elapsed_seconds':time.perf_counter()-clock}
    u.dump(out/'report.json',report);event('completed',run=u.relative(out),seconds=report['elapsed_seconds'])
    u.dump(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':u.relative(out),'new_summary':summary[-2:],'stress_summary':ssummary,'stress_rate_changes':rates}),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(run())
