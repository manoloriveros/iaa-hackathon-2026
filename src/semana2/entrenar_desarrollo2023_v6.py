"""Capital y credibilidad en GLM estándar, sin integrar clima futuro o abrir2024."""
from pathlib import Path
from datetime import datetime,timezone,date
import importlib.util,sys,json,time,uuid
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
v5=module('v6_standard_frozen',REPO/'src/semana2/entrenar_desarrollo2023_v5.py');u=v5.u
a=module('v6_credibility',REPO/'src/semana2/credibilidad2023.py')
np,pd,pq,joblib=u.np,u.pd,u.pq,u.joblib;KEY=u.KEY;PLAN=REPO/'registro/semana2_desarrollo2023_plan_v6.json'
def predict(bundle,frame):
    u.assert_2023(frame)
    if bundle['family']=='CredibilityRate':
        u.require(np.isfinite(bundle['c']) and bundle['c']>0 and frame.x_new_business.isin([0,1]).all(),'Factor/negocio inválido')
        return u.predict_bundle(bundle['parent'],frame)*np.where(frame.x_new_business.eq(1),bundle['c'],1.)
    return u.predict_bundle(bundle,frame)
def main():
    start=datetime.now(timezone.utc);tick=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['parent_run'];rawroot=ROOT/'Hackaton/Semana 2/Datos/emerging'
    u.require(u.sha(parent/'manifest.json')==plan['parent_manifest_sha256'] and u.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'],'Fuente cambiada')
    u.require(u.sha(ROOT/plan['diagnostic_review'])==plan['diagnostic_sha256'],'Revisión cambiada')
    selector=u.read(REPO/'registro/semana2_seleccion_actual.json');ledger=ROOT/selector['ledger_workspace_relative'];u.require(not ledger.exists(),'2024 debe permanecer cerrado')
    u.require(u.sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'],'Política cambiada')
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(b'<!-- aporte:COD-S2-20261023-018 -->')==1,'Falta preinscripción')
    out=parent.parent/('dev6_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    for folder in ['inputs_2023','links_2023','fit_rows','variant_inputs','models','auxiliary','diagnostics']:(out/folder).mkdir()
    def event(kind,**values):
        text=json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'event':kind,**values})
        with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(text+'\n')
        print(text,flush=True)
    event('started',run=u.relative(out),year=2023)
    for p,name in [(PLAN,'plan_snapshot.json'),(Path(__file__),'code_snapshot.py'),(Path(a.__file__),'auxiliary_code_snapshot.py'),
      (parent/'readiness_snapshot.json','readiness_snapshot.json'),(parent/'environment.json','environment.json'),(Path(v5.__file__),'standard_utility_snapshot.py')]:
        (out/name).write_bytes(p.read_bytes())
    (out/'forum_before_fit.md').write_bytes(forum)
    baseidx=u.read(REPO/'registro/semana2_preparacion_actual.json');sources=[parent/x['path'] for x in u.read(parent/'manifest.json')['files']]
    sources += [parent/'manifest.json',PLAN,Path(__file__),Path(a.__file__),Path(v5.__file__),ROOT/baseidx['target'],ROOT/baseidx['claim_audit'],ROOT/plan['diagnostic_review'],ROOT/plan['selection_policy']]
    sources += [ROOT/x['path'] for x in plan['frozen_received_sources']]
    sources += [rawroot/f'policies_{l}.parquet' for l in u.LINES]+[rawroot/'addresses.parquet',rawroot/'weather.parquet']
    frozen=[{'path':u.relative(p),'sha256':u.sha(p)} for p in dict.fromkeys(sources)];u.dump(out/'frozen_sources_before_fit.json',{'files':frozen})
    for folder in ['inputs_2023','links_2023','fit_rows']:
        for p in (parent/folder).glob('*.parquet'):(out/folder/p.name).write_bytes(p.read_bytes())
    target=pq.read_table(ROOT/baseidx['target'],filters=[('year','=',2023),('is_test','=',False)],columns=KEY+['T0','n_positive']).to_pandas();u.require(target[KEY].duplicated().sum()==0,'Target no único')
    data={l:u.load_2023(out/f'inputs_2023/{l}.parquet').merge(target[KEY+['n_positive']],on=KEY,validate='one_to_one') for l in u.LINES}
    ids=[x for f in data.values() for x in f.row_id]
    claims=pq.read_table(ROOT/baseidx['claim_audit'],filters=[('row_id','in',ids)],columns=['claim_id','line','row_id','included_in_T0','T0_cents']).to_pandas()
    raw={l:pq.read_table(rawroot/f'policies_{l}.parquet',filters=[('period_start','>=',date(2023,1,1)),('period_start','<',date(2024,1,1))]).to_pandas() for l in u.LINES}
    for line in u.LINES:
        u.require(set(raw[line].row_id)==set(data[line].row_id),'Raw2023 distinto');raw[line].to_parquet(out/f'inputs_2023/raw_{line}.parquet',index=False)
    claims.to_parquet(out/'auxiliary/positive_claim_source_2023.parquet',index=False)
    author,evidence,prior=a.load_author(plan);u.dump(out/'auxiliary/developed_prior_snapshot.json',{'prior':prior,'seasonality':evidence['indice_estacional_desarrollado'],'references':evidence['referencias'],
      'original_fit_years':[2021,2022,2023],'new_developed_fits':0,'raw_fit_independently_reproduced':False})
    old=pq.read_table(parent/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas();u.assert_2023(old.drop_duplicates(KEY));u.require(len(old)==14*50094,'Comparadores incompletos')
    outputs=[old];capital_records=[];aux_details=[];cred_records=[];price_receipts=[];price_fits=0
    for fold in range(5):
        cache={};fe={}
        for line in u.LINES:
            links=u.load_2023(out/f'links_2023/{line}_fold{fold}.parquet');offsets=[x[1] for x in u.SCENARIOS.values()]
            frame=data[line].merge(links[KEY+offsets],on=KEY,validate='one_to_one')
            if line!='motor':frame,record=a.capital_frame(frame,raw[line],fold,plan['capital_rule']['thresholds'][line]);capital_records.append(record)
            frame.to_parquet(out/f'variant_inputs/{line}_fold{fold}.parquet',index=False)
            fit=frame[frame.fold.ne(fold)];valid=frame[frame.fold.eq(fold)]
            for col in ['group_id','customer_id','address_id']:u.require(not set(fit[col])&set(valid[col]),'Fuga '+col)
            source=parent/'models'/f'W2-B13_{line}_fold{fold}/bundle.joblib'
            if line=='motor':bundle=joblib.load(source);notes={'exact_source_reuse':u.relative(source),'source_sha256':u.sha(source)}
            else:
                with u.threadpool_limits(limits=2):bundle,notes=v5.glm_fit(fit,fold,plan['core_recipe'],line)
                price_fits+=1
            folder=out/'models'/f'W2-B14_{line}_fold{fold}';folder.mkdir()
            if line=='motor':(folder/'bundle.joblib').write_bytes(source.read_bytes())
            else:joblib.dump(bundle,folder/'bundle.joblib',compress=3)
            with u.threadpool_limits(limits=2):rate=predict(bundle,valid);replay=predict(joblib.load(folder/'bundle.joblib'),valid)
            u.require(np.array_equal(rate,replay),'Replay capital distinto');outputs.append(v5.as_oof(valid,'W2-B14',rate))
            receipt={'model_id':'W2-B14','line':line,'fold':fold,'train_rows':len(fit),'validation_rows':len(valid),'features':bundle['columns'],'replay_exact':True,**notes}
            u.dump(folder/'receipt.json',receipt);price_receipts.append(receipt)
            rawfit=raw[line][raw[line].row_id.isin(fit.row_id)].copy()
            with u.threadpool_limits(limits=2):fe[line],detail,prepared,severity=a.auxiliary_fit(author,evidence,rawfit,fit,claims,line,fold)
            prepared.to_parquet(out/f'auxiliary/{line}_fold{fold}_frequency.parquet',index=False);severity.to_parquet(out/f'auxiliary/{line}_fold{fold}_severity.parquet',index=False)
            u.dump(out/f'auxiliary/{line}_fold{fold}.json',detail);aux_details.append(detail);cache[line]=(bundle,valid,rate)
            event('scope_completed',line=line,fold=fold,price_refit=line!='motor',auxiliary_fits=2)
        cred=author.credibilidad(fe,prior);cred_records.append({'fold':fold,**cred});u.dump(out/f'auxiliary/credibility_fold{fold}.json',{'fold':fold,**cred})
        for line in u.LINES:
            bundle,valid,rate=cache[line];c=float(cred['ramos'][line]['c']);u.require(np.isfinite(c) and c>0,'Credibilidad no positiva')
            adapted={'family':'CredibilityRate','parent':bundle,'columns':bundle['columns'],'line':line,'fold':fold,'c':c,'credibility':cred['ramos'][line]}
            folder=out/'models'/f'W2-B15_{line}_fold{fold}';folder.mkdir();joblib.dump(adapted,folder/'bundle.joblib',compress=3)
            expected=rate*np.where(valid.x_new_business.eq(1),c,1.)
            with u.threadpool_limits(limits=2):replay=predict(joblib.load(folder/'bundle.joblib'),valid)
            u.require(np.array_equal(expected,replay),'Replay credibilidad distinto');outputs.append(v5.as_oof(valid,'W2-B15',replay))
            receipt={'model_id':'W2-B15','line':line,'fold':fold,'c':c,'features':bundle['columns'],'replay_exact':True,'heldout_labels_used':False,'extra_AE_calibration':False}
            u.dump(folder/'receipt.json',receipt)
    oof=pd.concat(outputs,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True)
    u.require(oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any(),'OOF inválido')
    u.require(oof[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)),'OOF previo cambiado')
    oof.to_parquet(out/'oof_2023.parquet',index=False);summary=[];segments=[];scenarios=[]
    ids=plan['comparators_reused_without_refit']+[x['id'] for x in plan['models']]
    for mid in ids:
        p=oof[oof.model_id.eq(mid)];u.require(len(p)==50094,'OOF incompleto');summary.append({'model_id':mid,**u.metrics(p)})
        for dim,lab in [('line',p.line),('fold',p.fold),('business',np.where(p.x_new_business.eq(1),'new_business','renewal')),
          ('line_business',p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal'))]:
            for label,sub in p.assign(label=lab).groupby('label',observed=True):segments.append({'model_id':mid,'segment':dim,'label':str(label),**u.metrics(sub)})
        for name,(yc,ec) in u.SCENARIOS.items():
            sub=p.assign(scenario_prediction=p.annual_rate*p[ec]);scenarios.append({'model_id':mid,'scenario':name,**u.metrics(sub,yc,'scenario_prediction')})
    pairs=u.paired_diagnostics(oof,ids,out/'diagnostics',plan['diagnostics']['development_uncertainty'])
    for name,obj in [('pairs',pairs),('segments',segments),('observation_sensitivity',scenarios)]:u.dump(out/f'diagnostics/{name}.json',obj)
    history=pq.read_table(rawroot/'weather.parquet',filters=[('year','<',2023)],columns=['address_id','year']);u.require(history.num_rows==0,'Revisar historia climática nueva')
    for item in frozen:u.require(u.sha(ROOT/item['path'])==item['sha256'],'Fuente cambió '+item['path'])
    u.require(price_fits==10 and len(aux_details)==15 and not ledger.exists(),'Conteo/ledger inesperado')
    report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':u.sha(Path(__file__)),
      'auxiliary_code_sha256':u.sha(Path(a.__file__)),'plan_sha256':u.sha(PLAN),'parent_oof_sha256':plan['parent_oof_sha256'],'summary':summary,'pairs':pairs['pairs'],
      'capital':capital_records,'credibility':cred_records,'auxiliary_details':aux_details,'price_receipts':price_receipts,
      'new_price_base_fits':10,'exact_motor_reuses':5,'new_auxiliary_fits':30,'new_credibility_factors':15,'cumulative_price_base_fits':90,'cumulative_closed_form_constants':60,
      'climate':{'candidate_admitted':False,'prior_to_2023_rows_available':history.num_rows,'reason':'2024 values and2025 selector dependency; no admissible history for prospective2023 test'},
      'parent_comparators_exactly_unchanged':True,'reference_retained':'W2-B00','all_alternatives_preserved':True,'promotion':False,'final_confirmation_roster_frozen':False,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote_training':False,
      'new_developed_fits':0,'professional_independent_validation':False,'search_disclosure':plan['search_disclosure'],'elapsed_seconds':time.perf_counter()-tick}
    u.dump(out/'report.json',report);event('completed',run=u.relative(out),seconds=report['elapsed_seconds'])
    u.dump(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':u.relative(out),'new_summary':summary[-2:],'primary_contrasts':[p for p in pairs['pairs'] if (p['candidate'],p['reference']) in [('W2-B14','W2-B13'),('W2-B15','W2-B14')]]}),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
