"""Sensibilidad de observación2023: pesos fijos frente a mezcla renormalizada."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,uuid,time
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('tail_standard_frozen',REPO/'src/semana2/entrenar_desarrollo2023_v5.py')
v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)
u=v.u;np,pd,pq=u.np,u.pd,u.pq;KEY=u.KEY;PLAN=REPO/'registro/semana2_cola2023_plan_v1a.json'
PARENTS=['W2-B00','W2-B12','W2-B14']

def scope(frame,fold,fit=False):
    u.assert_2023(frame);u.require(not frame.is_test.any(),'Test prohibido')
    u.require((frame.fold.ne(fold) if fit else frame.fold.eq(fold)).all(),'Ámbito de fold incorrecto')

def factor_from_shares(shares):
    u.require(shares and all(np.isfinite(x) and x>=0 for x in shares.values()) and abs(sum(shares.values())-1)<1e-10,'Mezcla inválida')
    return float(sum(w/(.9 if p in ['bodily_injury','subsidence'] else 1.) for p,w in shares.items()))

def predict(bundle,frame):
    u.assert_2023(frame)
    if bundle['family']=='TailScale':
        scope(frame,bundle['fold']);u.require(frame.line.eq(bundle['line']).all(),'Ramo incorrecto')
        return v.predict(bundle['parent'],frame)*bundle['scale']
    return v.predict(bundle,frame)

def make_oof(frame,rate,sid,parent,e):
    out=frame[KEY+['year','is_test','group_id','fold','exposure','T0','x_new_business']].copy()
    out['stress_id']=sid;out['parent_model']=parent;out['base_effective_exposure']=frame['e_cost_mix_1.0'].to_numpy();out['effective_exposure']=np.asarray(e)
    out['annual_rate']=rate;out['prediction']=np.asarray(e)*rate;out['conditional_nominal_2023']=out.exposure*rate
    out['unit_deviance']=u.unit_deviance(out.T0,out.prediction)
    u.require(np.isfinite(rate).all() and (rate>0).all() and np.isfinite(out.prediction).all() and out.prediction.gt(0).all(),'Tasa/precio inválido')
    return out

def pairs_for_fixed(oof,old,out,config):
    series={}
    for mid in PARENTS:series[mid]=old[old.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True)
    for sid,q in oof[oof.stress_id.str.startswith('T10F')].groupby('stress_id'):series[sid]=q.sort_values(KEY).reset_index(drop=True)
    ids=PARENTS+['T10F_'+x for x in PARENTS];first=series[ids[0]];codes,groups=pd.factorize(first.group_id,sort=True);g=len(groups)
    n=np.bincount(codes,minlength=g).astype(float);y=np.bincount(codes,weights=first.T0,minlength=g);root=np.bincount(codes,weights=np.sqrt(first.T0),minlength=g)
    gl=np.column_stack([np.bincount(codes,weights=series[m].unit_deviance,minlength=g) for m in ids]);gf=pd.DataFrame({'group_id':groups,'rows':n,'T0':y,'sqrt_T0':root})
    for j,mid in enumerate(ids):gf['loss_'+mid]=gl[:,j]
    gf.to_parquet(out/'group_losses.parquet',index=False)
    pairs=[(3,0),(4,1),(5,2),(4,3),(5,3),(5,4)];rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();reps=[]
    for start in range(0,config['replicates'],32):
        size=min(32,config['replicates']-start);draw=rng.integers(0,g,size=(size,g),dtype=np.int64);digest.update(draw.tobytes())
        den=8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-root[draw].sum(axis=1));loss=gl[draw].sum(axis=1)
        for a,b in pairs:reps.extend({'replicate':start+k,'candidate':ids[a],'reference':ids[b],'delta_D2':float(z)} for k,z in enumerate((loss[:,b]-loss[:,a])/den))
    rf=pd.DataFrame(reps);rf.to_parquet(out/'bootstrap_6_pairs.parquet',index=False);den=8*(np.sqrt(n.sum()*y.sum())-root.sum());records=[]
    for a,b in pairs:
        dist=rf.loc[rf.candidate.eq(ids[a])&rf.reference.eq(ids[b]),'delta_D2'];adv=gl[:,b]-gl[:,a];removed=np.argsort(-adv,kind='stable')[:31];keep=np.ones(g,bool);keep[removed]=False
        td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum())
        records.append({'candidate':ids[a],'reference':ids[b],'delta_D2':float(adv.sum()/den),'exploratory_lower95':float(dist.quantile(.025)),
          'exploratory_upper95':float(dist.quantile(.975)),'removed_favorable_groups':31,'delta_after_removal':float(adv[keep].sum()/td)})
    return {'config':config,'draws_sha256':digest.hexdigest(),'pairs':records,'renormalized_interval':'Not simulated: exact observed-prediction identity up to floating point; no redundant bootstrap.'}

def main():
    start=datetime.now(timezone.utc);u.require(start<datetime(2026,10,24,12,tzinfo=timezone.utc),'Ventana terminada');tick=time.perf_counter();plan=u.read(PLAN)
    parent=ROOT/plan['input_run'];prices={m:ROOT/p for m,p in plan['base_model_runs'].items()};linkroot=ROOT/plan['observation_run'];selector=u.read(REPO/'registro/semana2_seleccion_actual.json')
    u.require(not (ROOT/selector['ledger_workspace_relative']).exists(),'2024 cerrado');u.require(u.sha(Path(__file__))==plan['code_sha256'],'Código cambiado')
    for it in plan['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambiada '+it['path'])
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(('<!-- aporte:'+plan['forum_preregistration']+' -->').encode())==1,'Falta preinscripción')
    u.require(len(sys.argv)==2,'Esta corrección solo reanuda el intento conciliado')
    out=Path(sys.argv[1]).resolve();out.relative_to(parent.parent);u.require(u.relative(out)==plan['resume_run'],'Corrida de reanudación incorrecta')
    u.require((out/'failed_attempt.json').exists() and not (out/'report.json').exists(),'Revisar estado antes de reanudar')
    original=u.read(out/'plan_snapshot.json');u.require(original['id']==plan['id'],'La receta cambió de ámbito')
    for path,name in [(Path(__file__),'continuation_code_snapshot.py'),(PLAN,'plan_amendment_snapshot.json')]:
        with (out/name).open('xb') as handle:handle.write(path.read_bytes())
    (out/'forum_before_resume.md').write_bytes(forum)
    old=pq.read_table(out/'base_oof_2023.parquet').to_pandas();u.assert_2023(old.drop_duplicates(KEY))
    outputs=[];receipts=[];scale_records=[];new_glm=0;new_constants=0;exact=0;cached=[]
    core=u.read(parent/'plan_snapshot.json')['core_recipe']
    for fold in range(5):
        for line in u.LINES:
            sourceframe=parent/f'variant_inputs/{line}_fold{fold}.parquet';frame=u.load_2023(sourceframe);e0=frame['e_cost_mix_1.0'].to_numpy();ef=frame['e_cost_mix_tail0.1'].to_numpy()
            shares=u.read(linkroot/f'exclude_fold{fold}/peril_cost_shares_{line}.json')['1.0'];z=factor_from_shares(shares);er=e0/z
            fit=frame[frame.fold.ne(fold)].copy();valid=frame[frame.fold.eq(fold)].copy();scope(fit,fold,True);scope(valid,fold)
            u.require(all(not set(fit[k])&set(valid[k]) for k in ['group_id','customer_id','address_id']),'Solapamiento de ajuste/validación')
            frame[['market','line','row_id','year','is_test','group_id','fold','T0','exposure','x_new_business','e_cost_mix_1.0','e_cost_mix_tail0.1']].to_parquet(out/f'inputs_2023/{line}_fold{fold}.parquet',index=False)
            unchanged=np.array_equal(e0,ef);u.require(unchanged==(line=='contents'),'Alcance de cola diferente del registrado')
            scale_records.append({'line':line,'fold':fold,'Z':z,'longtail_share':sum(w for p,w in shares.items() if p in ['bodily_injury','subsidence']),
              'fixed_e_over_base_min':float((ef/e0).min()),'fixed_e_over_base_max':float((ef/e0).max()),'renormalized_e_over_base':1/z,'contents_identity':unchanged})
            train=fit.copy();train['e_cost_mix_1.0']=train['e_cost_mix_tail0.1']
            for mid in PARENTS:
                source=prices[mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib';base=u.joblib.load(source)
                fixedfolder=out/'models'/f'T10F_{mid}_{line}_fold{fold}';fixedfolder.mkdir(exist_ok=True)
                if unchanged:
                    fixed=base;notes={'exact_reuse':True};(fixedfolder/'bundle.joblib').write_bytes(source.read_bytes());exact+=1
                else:
                    scope(train,fold,True)
                    if (fixedfolder/'bundle.joblib').exists():
                        u.require(fold==0 and line=='motor' and mid in ['W2-B00','W2-B12'],'Caché inesperada')
                        fixed=u.joblib.load(fixedfolder/'bundle.joblib');notes={'recovered_after_receipt_error':True};cached.append(u.relative(fixedfolder/'bundle.joblib'))
                        new_constants+=1 if mid=='W2-B00' else 2
                    elif mid=='W2-B00':
                        e=train['e_cost_mix_1.0'].to_numpy();y=train.T0.to_numpy();rate=float(np.sum(y/np.sqrt(e))/np.sqrt(e).sum())
                        fixed={'family':'constant_line_rate','rate':rate,'columns':[]};notes={'closed_form_rate':rate};new_constants+=1
                    elif mid=='W2-B12':
                        fixed,business_details=v.constant_fit(train,fold);notes={'business_details':business_details};new_constants+=2
                    else:
                        with u.threadpool_limits(limits=2):fixed,notes=v.glm_fit(train,fold,core,line)
                        new_glm+=1
                    if not (fixedfolder/'bundle.joblib').exists():u.joblib.dump(fixed,fixedfolder/'bundle.joblib',compress=3)
                with u.threadpool_limits(limits=2):rate=predict(fixed,valid);replay=predict(u.joblib.load(fixedfolder/'bundle.joblib'),valid)
                u.require(np.array_equal(rate,replay),'Replay fijo distinto');sid='T10F_'+mid;outputs.append(make_oof(valid,rate,sid,mid,valid['e_cost_mix_tail0.1']))
                receipt={'stress_id':sid,'parent':mid,'line':line,'fold':fold,'source':u.relative(source),'source_sha256':u.sha(source),'Z':z,'fit_rows':len(train),'validation_rows':len(valid),'new_fit':not unchanged,**notes}
                if not (fixedfolder/'receipt.json').exists():u.dump(fixedfolder/'receipt.json',receipt)
                receipts.append(receipt)
                renorm={'family':'TailScale','parent':base,'columns':base['columns'],'scale':z,'fold':fold,'line':line}
                folder=out/'models'/f'T10R_{mid}_{line}_fold{fold}';folder.mkdir(exist_ok=True)
                if not (folder/'bundle.joblib').exists():u.joblib.dump(renorm,folder/'bundle.joblib',compress=3)
                with u.threadpool_limits(limits=2):rate=predict(renorm,valid);replay=predict(u.joblib.load(folder/'bundle.joblib'),valid)
                u.require(np.array_equal(rate,replay),'Replay renormalizado distinto');outputs.append(make_oof(valid,rate,'T10R_'+mid,mid,valid['e_cost_mix_1.0']/z))
                if not (folder/'receipt.json').exists():u.dump(folder/'receipt.json',{'stress_id':'T10R_'+mid,'parent':mid,'line':line,'fold':fold,'scale':z,'new_fits':0,'intercept_shift_log':float(np.log(z))})
    oof=pd.concat(outputs,ignore_index=True).sort_values(['stress_id',*KEY]).reset_index(drop=True)
    u.require(oof.year.eq(2023).all() and not oof.is_test.any() and not oof.duplicated(['stress_id',*KEY]).any(),'OOF de estrés inválido');oof.to_parquet(out/'stress_oof_2023.parquet',index=False)
    summary=[];segments=[];sensitivity=[]
    for sid,q in oof.groupby('stress_id'):
        p=old[old.model_id.eq(q.parent_model.iloc[0])].sort_values(KEY).reset_index(drop=True);q=q.sort_values(KEY).reset_index(drop=True);u.require(q[KEY].equals(p[KEY]),'Claves cambiadas')
        summary.append({'stress_id':sid,**u.metrics(q),'conditional_nominal_2023':float(q.conditional_nominal_2023.sum()),'parent_conditional_nominal_2023':float((p.exposure*p.annual_rate).sum())})
        for dim,labels in [('line',q.line),('fold',q.fold.astype(str)),('business',np.where(q.x_new_business.eq(1),'new_business','renewal')),
          ('line_business',q.line.astype(str)+'_'+np.where(q.x_new_business.eq(1),'new_business','renewal'))]:
            for label,cell in q.assign(label=labels).groupby('label',observed=True):segments.append({'stress_id':sid,'dimension':dim,'label':str(label),**u.metrics(cell),'conditional_nominal_2023':float(cell.conditional_nominal_2023.sum())})
        ratio=q.annual_rate.to_numpy()/p.annual_rate.to_numpy();observeddiff=q.prediction.to_numpy()-p.prediction.to_numpy()
        sensitivity.append({'stress_id':sid,'rate_ratio_min':float(ratio.min()),'rate_ratio_median':float(np.median(ratio)),'rate_ratio_max':float(ratio.max()),
          'observed_prediction_max_absolute_difference':float(abs(observeddiff).max()),'observed_total_difference':float(observeddiff.sum()),'same_T0':q.T0.equals(p.T0),
          'conditional_nominal_relative_change':float(q.conditional_nominal_2023.sum()/(p.exposure*p.annual_rate).sum()-1)})
    pairs=pairs_for_fixed(oof,old,out/'diagnostics',plan['bootstrap']);u.dump(out/'diagnostics/pairs.json',pairs);u.dump(out/'diagnostics/segments.json',segments)
    u.require(new_glm==10 and new_constants==30 and exact==15 and len(cached)==2,'Conteo distinto de receta')
    for it in plan['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambió')
    u.require(not (ROOT/selector['ledger_workspace_relative']).exists(),'2024 cerrado')
    report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':u.sha(PLAN),'code_sha256':u.sha(Path(__file__)),
      'summary':summary,'sensitivity':sensitivity,'scales':scale_records,'receipts':receipts,'new_price_GLM_fits':10,'new_closed_form_constants':30,'exact_content_reuses':15,
      'new_reporting_fits':0,'new_auxiliary_fits':0,'analytic_scale_adapters':45,'cumulative_price_base_fits':100,'cumulative_closed_form_constants':90,
      'main_model_catalog_unchanged':True,'reference_retained':'W2-B00','promotion':False,'final_confirmation_roster_frozen':False,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'professional_independent_validation':False,
      'elapsed_seconds':time.perf_counter()-tick,'first_attempt_started_utc':'2026-10-24T00:11:14+00:00','resumed_cached_constant_bundles':cached,
      'constants_calculated_before_receipt_error':3,'constants_calculated_in_continuation':27,'new_GLM_before_error':0,
      'notice':'Six observation-sensitivity configurations, not a new common-link candidate roster. No true ultimate labels or2025 predictions.'}
    u.dump(out/'report.json',report);u.dump(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':u.relative(out),'summary':summary,'sensitivity':sensitivity}),flush=True)
if __name__=='__main__':main()
