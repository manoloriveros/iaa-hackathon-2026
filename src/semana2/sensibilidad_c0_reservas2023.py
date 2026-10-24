"""Reservas y un adverso de reportes tardíos: solo2023 y modelos estándar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,uuid,hashlib,time
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
v=module('mechanism_standard',REPO/'src/semana2/entrenar_desarrollo2023_v5.py');u=v.u
obs=module('mechanism_reporting',REPO/'src/semana2/variables_ultimo.py')
np,pd,pq=u.np,u.pd,u.pq;KEY=u.KEY;MIDS=['W2-B00','W2-B12','W2-B14'];SCENARIOS=['R075','R125','L1'];PLAN=REPO/'registro/semana2_c0_reservas2023_plan_v1.json'

def choose_late_group(claims,fold,line):
    fit=claims[claims.line.eq(line)&claims.fold.ne(fold)];late=fit[fit.delay.gt(365)&fit.T0_cents.gt(0)]
    if late.empty:return None
    amounts=late.groupby('group_id',as_index=False).T0_cents.sum().sort_values(['T0_cents','group_id'],ascending=[False,True],kind='stable')
    return str(amounts.iloc[0].group_id)

def late_link(frame,raw,claims,fold,line):
    u.assert_2023(frame);removed=choose_late_group(claims,fold,line)
    fitclaims=claims[claims.line.eq(line)&claims.fold.ne(fold)].copy();before=fitclaims.copy()
    if removed is None:return frame['e_cost_mix_1.0'].to_numpy(),{'line':line,'fold':fold,'removed_group':None,'identity':True,'new_reporting_fits':0},{}
    fitclaims=fitclaims[fitclaims.group_id.ne(removed)];fitrows=frame.fold.ne(fold)&frame.group_id.ne(removed)
    periods=frame[KEY+['year','is_test','exposure']].merge(raw[['row_id','period_start','period_end']],on='row_id',validate='one_to_one')
    u.require(periods.row_id.equals(frame.row_id),'Orden de periodos cambió');models={};rates={};curves={}
    for peril,g in fitclaims.groupby('peril',sort=True):
        model,_=obs.fit_reporting(g.delay,g.age,g.T0_cents/100,g.reserve_cents/100);models[peril]=model
        count=obs.average_completion(periods,model);cost=obs.average_completion(periods,model,'cost',1.)
        denom=float(np.sum(frame.loc[fitrows,'exposure']*count[fitrows]));u.require(denom>0,'Exposición de reportes nula')
        rates[peril]=len(g)/denom*model['mean_net_mark']['1.0'];curves[peril]=cost
    u.require(set(models)==set(before.peril.unique()),'No fallback al perder un peril')
    total=sum(rates.values());shares={k:x/total for k,x in rates.items()};q=sum(shares[k]*curves[k] for k in shares)
    record={'line':line,'fold':fold,'removed_group':removed,'identity':False,'fit_claims_before':len(before),'fit_claims_after':len(fitclaims),
      'removed_claims':int(before.group_id.eq(removed).sum()),'removed_late_cost':float(before.loc[before.group_id.eq(removed)&before.delay.gt(365),'T0_cents'].sum()/100),
      'removed_all_cost':float(before.loc[before.group_id.eq(removed),'T0_cents'].sum()/100),'remaining_reporting_periods':int(fitrows.sum()),
      'new_reporting_fits':len(models),'shares':shares,'reporting_fit_ids_sha256':hashlib.sha256('\n'.join(sorted(fitclaims.claim_id)).encode()).hexdigest()}
    return frame.exposure.to_numpy()*q,record,models

def output(valid,scenario,mid,rate,e,y):
    result=valid[KEY+['year','is_test','group_id','fold','exposure','T0','reserve','x_new_business']].copy()
    result['scenario']=scenario;result['model_id']=mid;result['stress_id']=scenario+'_'+mid;result['T_s']=np.asarray(y);result['effective_exposure']=np.asarray(e)
    result['annual_rate']=rate;result['prediction']=np.asarray(e)*rate;result['conditional_nominal_2023']=valid.exposure.to_numpy()*rate
    result['unit_deviance']=u.unit_deviance(result.T_s,result.prediction);return result

def diagnostics(oof,old,out,config):
    ids=[s+'_'+m for s in SCENARIOS for m in MIDS]+MIDS
    parts={sid:q.sort_values(KEY).reset_index(drop=True) for sid,q in oof.groupby('stress_id')}
    for mid in MIDS:
        p=old[old.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True).copy();p['T_s']=p.T0;parts[mid]=p
    first=parts[ids[0]];codes,groups=pd.factorize(first.group_id,sort=True);g=len(groups);n=np.bincount(codes,minlength=g).astype(float)
    gl=np.column_stack([np.bincount(codes,weights=parts[sid].unit_deviance,minlength=g) for sid in ids]);target={}
    for scenario in SCENARIOS:
        t=parts[scenario+'_'+MIDS[0]].T_s.to_numpy();target[scenario]=(np.bincount(codes,weights=t,minlength=g),np.bincount(codes,weights=np.sqrt(t),minlength=g))
    pairs=[]
    for scenario in SCENARIOS:
        for a,b in [(1,0),(2,0),(2,1)]:pairs.append((ids.index(scenario+'_'+MIDS[a]),ids.index(scenario+'_'+MIDS[b]),scenario))
    for mid in MIDS:pairs.append((ids.index('L1_'+mid),ids.index(mid),'L1'))
    rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();reps=[]
    for start in range(0,config['replicates'],32):
        size=min(32,config['replicates']-start);draw=rng.integers(0,g,size=(size,g),dtype=np.int64);digest.update(draw.tobytes());loss=gl[draw].sum(axis=1)
        den={s:8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-root[draw].sum(axis=1)) for s,(y,root) in target.items()}
        for a,b,scenario in pairs:reps.extend({'replicate':start+k,'candidate':ids[a],'reference':ids[b],'scenario':scenario,'delta_D2':float(z)} for k,z in enumerate((loss[:,b]-loss[:,a])/den[scenario]))
    rf=pd.DataFrame(reps);rf.to_parquet(out/'bootstrap_12_pairs.parquet',index=False);records=[]
    for a,b,scenario in pairs:
        y,root=target[scenario];den=8*(np.sqrt(n.sum()*y.sum())-root.sum());dist=rf[rf.candidate.eq(ids[a])&rf.reference.eq(ids[b])].delta_D2;adv=gl[:,b]-gl[:,a]
        keep=np.ones(g,bool);keep[np.argsort(-adv,kind='stable')[:31]]=False;td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum())
        records.append({'candidate':ids[a],'reference':ids[b],'scenario':scenario,'delta_D2':float(adv.sum()/den),'exploratory_lower95':float(dist.quantile(.025)),
          'exploratory_upper95':float(dist.quantile(.975)),'removed_favorable_groups':31,'delta_after_removal':float(adv[keep].sum()/td)})
    return {'config':config,'draws_sha256':digest.hexdigest(),'pairs':records,'target_rule':'Pairs only within own target scenario; L1/ownbase sameT0. Never compare reserve-target D2 as common-outcome superiority.'}

def main():
    start=datetime.now(timezone.utc);tick=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['input_run'];linkroot=ROOT/plan['observation_run']
    selector=u.read(REPO/'registro/semana2_seleccion_actual.json');u.require(not (ROOT/selector['ledger_workspace_relative']).exists(),'2024 cerrado')
    for it in plan['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambiada '+it['path'])
    u.require(u.sha(Path(__file__))==plan['code_sha256'],'Código cambiado');forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(('<!-- aporte:'+plan['forum_preregistration']+' -->').encode())==1,'Falta receta previa')
    out=parent.parent/('mecanismo_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    for folder in ['models','inputs_2023','late_reporting','diagnostics']:(out/folder).mkdir()
    (out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());(out/'plan_snapshot.json').write_bytes(PLAN.read_bytes());(out/'forum_before_fit.md').write_bytes(forum)
    u.dump(out/'environment.json',{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':u.pa.__version__,'threads':2,'seed':2026102302})
    old=pq.read_table(ROOT/plan['base_oof'],filters=[('year','=',2023),('model_id','in',MIDS)]).to_pandas();u.assert_2023(old.drop_duplicates(KEY));old.to_parquet(out/'base_oof_2023.parquet',index=False)
    meta=pd.concat([u.load_2023(parent/f'inputs_2023/{line}.parquet')[KEY+['year','fold','group_id']] for line in u.LINES],ignore_index=True);u.assert_2023(meta)
    claims=pq.read_table(ROOT/plan['claim_audit'],filters=[('row_id','in',meta.row_id.tolist())]).to_pandas();claims=claims[claims.included_in_T0].merge(meta,on=KEY,validate='many_to_one')
    claims['delay']=(pd.to_datetime(claims.report_date)-pd.to_datetime(claims.loss_date)).dt.days;claims['age']=(pd.Timestamp('2024-12-31')-pd.to_datetime(claims.loss_date)).dt.days
    claims.to_parquet(out/'inputs_2023/claims_2023.parquet',index=False);core=u.read(parent/'plan_snapshot.json')['core_recipe']
    outputs=[];late_records=[];receipts=[];links=[];fitcount=0;constants=0;reuses=0;reportfits=0
    for fold in range(5):
        for line in u.LINES:
            frame=u.load_2023(parent/f'variant_inputs/{line}_fold{fold}.parquet');raw=u.load_2023(parent/f'inputs_2023/{line}.parquet')
            dates=pq.read_table(parent/f'inputs_2023/raw_{line}.parquet',columns=['row_id','period_start','period_end']).to_pandas();u.require(set(dates.row_id)==set(frame.row_id),'Fechas ajenas a2023')
            late_e,record,models=late_link(frame,dates,claims,fold,line);late_records.append(record);reportfits+=record['new_reporting_fits']
            u.dump(out/f'late_reporting/{line}_fold{fold}.json',{'record':record,'models':models})
            expected=pq.read_table(linkroot/f'exclude_fold{fold}/reporting_fit_claims.parquet',filters=[('year','=',2023),('line','=',line)]).to_pandas()
            u.require(set(expected.claim_id)==set(claims.loc[claims.line.eq(line)&claims.fold.ne(fold),'claim_id']),'Asignación C0 distinta')
            fitmask=frame.fold.ne(fold);validmask=~fitmask;fit=frame.loc[fitmask];valid=frame.loc[validmask]
            u.require(all(not set(fit[k])&set(valid[k]) for k in ['group_id','customer_id','address_id']),'Fuga')
            variants={'R075':(frame['e_cost_mix_0.75'].to_numpy(),frame.T1_reserve075.to_numpy()),'R125':(frame['e_cost_mix_1.25'].to_numpy(),frame.T1_reserve125.to_numpy()),'L1':(late_e,frame.T0.to_numpy())}
            for scenario,(e,y) in variants.items():
                u.require(np.isfinite(e).all() and (e>0).all() and np.isfinite(y).all() and (y>=0).all(),'Respuesta/enlace inválido')
                train=fit.copy();train['T0']=y[fitmask];train['e_cost_mix_1.0']=e[fitmask];u.assert_2023(train);u.require(train.fold.ne(fold).all(),'Retenido en entrenamiento')
                same=np.array_equal(e,frame['e_cost_mix_1.0'].to_numpy()) and np.array_equal(y,frame.T0.to_numpy())
                q=frame[KEY+['year','is_test','fold','group_id','exposure','T0','reserve','x_new_business']].copy();q['T_s']=y;q['effective_exposure']=e;q['base_e']=frame['e_cost_mix_1.0'];q['scenario']=scenario
                q.to_parquet(out/f'inputs_2023/{scenario}_{line}_fold{fold}.parquet',index=False)
                links.append({'scenario':scenario,'line':line,'fold':fold,'all_e_ratio_min':float((e/frame['e_cost_mix_1.0']).min()),'all_e_ratio_max':float((e/frame['e_cost_mix_1.0']).max()),
                  'e_ratio_mean_validation':float(np.mean(e[validmask]/frame.loc[validmask,'e_cost_mix_1.0'])),'identity':same})
                for mid in MIDS:
                    folder=out/'models'/f'{scenario}_{mid}_{line}_fold{fold}';folder.mkdir();source=ROOT/plan['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib';notes={}
                    if same:bundle=u.joblib.load(source);(folder/'bundle.joblib').write_bytes(source.read_bytes());reuses+=1
                    else:
                        if mid=='W2-B00':
                            et=train['e_cost_mix_1.0'].to_numpy();yt=train.T0.to_numpy();rate=float(np.sum(yt/np.sqrt(et))/np.sqrt(et).sum());bundle={'family':'constant_line_rate','rate':rate,'columns':[]};notes={'rate':rate};constants+=1
                        elif mid=='W2-B12':bundle,details=v.constant_fit(train,fold);notes={'business_details':details};constants+=2
                        else:
                            with u.threadpool_limits(limits=2):bundle,notes=v.glm_fit(train,fold,core,line)
                            fitcount+=1
                        u.joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                    with u.threadpool_limits(limits=2):rates=v.predict(bundle,valid);replay=v.predict(u.joblib.load(folder/'bundle.joblib'),valid)
                    u.require(np.array_equal(rates,replay),'Replay distinto');outputs.append(output(valid,scenario,mid,rates,e[validmask],y[validmask]))
                    receipt={'scenario':scenario,'model_id':mid,'line':line,'fold':fold,'train_rows':len(train),'validation_rows':len(valid),'exact_reuse':same,
                      'source_bundle':u.relative(source),'source_sha256':u.sha(source),'replay_exact':True,'heldout_labels_used':False,**notes};u.dump(folder/'receipt.json',receipt);receipts.append(receipt)
            print(json.dumps({'event':'scope_completed','line':line,'fold':fold,'GLM_fits_so_far':fitcount,'constant_values_so_far':constants,'reporting_fits_so_far':reportfits}),flush=True)
    oof=pd.concat(outputs,ignore_index=True).sort_values(['stress_id',*KEY]).reset_index(drop=True);u.require(len(oof)==9*50094 and oof.year.eq(2023).all() and not oof.duplicated(['stress_id',*KEY]).any(),'OOF inválido');oof.to_parquet(out/'mechanism_oof_2023.parquet',index=False)
    summary=[];segments=[]
    for sid,q in oof.groupby('stress_id'):
        base=old[old.model_id.eq(q.model_id.iloc[0])].sort_values(KEY).reset_index(drop=True);q=q.sort_values(KEY).reset_index(drop=True);u.require(q[KEY].equals(base[KEY]),'Claves distintas')
        summary.append({'stress_id':sid,'scenario':q.scenario.iloc[0],'model_id':q.model_id.iloc[0],**u.metrics(q,'T_s'),'conditional_nominal_2023':float(q.conditional_nominal_2023.sum()),
          'base_nominal_2023':float((base.exposure*base.annual_rate).sum()),'nominal_relative_change':float(q.conditional_nominal_2023.sum()/(base.exposure*base.annual_rate).sum()-1)})
        for dim,label in [('line',q.line),('fold',q.fold.astype(str)),('business',np.where(q.x_new_business.eq(1),'new_business','renewal')),('line_business',q.line.astype(str)+'_'+np.where(q.x_new_business.eq(1),'new_business','renewal'))]:
            for lab,cell in q.assign(label=label).groupby('label',observed=True):segments.append({'stress_id':sid,'dimension':dim,'label':str(lab),**u.metrics(cell,'T_s'),'conditional_nominal_2023':float(cell.conditional_nominal_2023.sum())})
    pairs=diagnostics(oof,old,out/'diagnostics',plan['bootstrap']);u.dump(out/'diagnostics/pairs.json',pairs);u.dump(out/'diagnostics/segments.json',segments)
    for it in plan['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambió')
    u.require(not (ROOT/selector['ledger_workspace_relative']).exists(),'2024 cerrado')
    report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':u.sha(Path(__file__)),'plan_sha256':u.sha(PLAN),
      'summary':summary,'links':links,'late_reporting':late_records,'receipts':receipts,'new_price_GLM_fits':fitcount,'new_closed_form_constants':constants,'exact_reuses':reuses,'new_reporting_peril_fits':reportfits,
      'new_auxiliary_fits':0,'cumulative_price_base_fits':plan['counters_before']['cumulative_price_base_fits']+fitcount,'cumulative_closed_form_constants':plan['counters_before']['cumulative_closed_form_constants']+constants,
      'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,'main_catalog_unchanged':True,'professional_independent_validation':False,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote':False,'elapsed_seconds':time.perf_counter()-tick}
    u.dump(out/'report.json',report);u.dump(out/'manifest.json',{'files':[{'path':q.relative_to(out).as_posix(),'sha256':u.sha(q),'bytes':q.stat().st_size} for q in sorted(out.rglob('*')) if q.is_file()]})
    print(json.dumps({'event':'completed','run':u.relative(out),'summary':summary,'new_price_fits':fitcount,'new_constants':constants,'new_report_fits':reportfits}),flush=True)
if __name__=='__main__':main()
