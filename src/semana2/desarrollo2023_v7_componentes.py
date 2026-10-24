"""Ablaciones de GLM congelados, exclusivamente en autos nuevos2023."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,uuid,hashlib,time
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v7_frozen_standard',REPO/'src/semana2/entrenar_desarrollo2023_v5.py')
v5=importlib.util.module_from_spec(s);sys.modules[s.name]=v5;s.loader.exec_module(v5)
u=v5.u;np,pd,pq=u.np,u.pd,u.pq;KEY=u.KEY;PLAN=REPO/'registro/semana2_desarrollo2023_plan_v7.json'

def factors(cred,bundle):
    names=bundle['transformer'].get_feature_names_out().tolist();j=names.index('numeric__x_new_business')
    block=list(bundle['transformer'].transformers_[0][2]);k=block.index('x_new_business')
    scale=bundle['transformer'].named_transformers_['numeric'].named_steps['scale'].scale_[k]
    theta_price=float(bundle['estimator'].coef_[j]/scale)
    result={'W2-B16':float(np.exp((1-cred['Z_f'])*(cred['theta_f_dev']-cred['theta_f_em']))),
      'W2-B17':float(np.exp((1-cred['Z_s'])*(cred['theta_s_dev']-cred['theta_s_em']))),
      'W2-B18':float(np.exp(cred['theta_cred']-theta_price))}
    u.require(all(np.isfinite(x) and x>0 for x in result.values()),'Factor inválido')
    return result,theta_price

def predict(bundle,frame):
    u.assert_2023(frame);u.require(not frame.is_test.any() if 'is_test' in frame else True,'Test prohibido')
    if bundle['family']=='MotorCredibilityRate':
        u.require(frame.line.eq('motor').all() and frame.fold.eq(bundle['fold']).all(),'Ramo/fold no corresponde')
        u.require(frame.x_new_business.isin([0,1]).all(),'Negocio inválido')
        return u.predict_bundle(bundle['parent'],frame)*np.where(frame.x_new_business.eq(1),bundle['c'],1.)
    return u.predict_bundle(bundle,frame)

def extend_pairs(oof,parent,out,ids,config):
    old=u.read(parent/'diagnostics/pairs.json');gf=pq.read_table(parent/'diagnostics/group_aggregates.parquet').to_pandas()
    newids=ids[16:];first=oof[oof.model_id.eq('W2-B00')].sort_values(KEY).reset_index(drop=True)
    codes,groups=pd.factorize(first.group_id,sort=True);u.require(np.array_equal(groups,gf.group_id),'Orden de grupos distinto')
    for mid in newids:
        p=oof[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True);u.require(p[KEY].equals(first[KEY]),'Filas distintas')
        gf['loss_'+mid]=np.bincount(codes,weights=p.unit_deviance,minlength=len(gf))
    gf.to_parquet(out/'group_aggregates.parquet',index=False)
    g=len(gf);n=gf.rows.to_numpy();y=gf.T0.to_numpy();root=gf.sqrt_T0.to_numpy();gl=gf[['loss_'+m for m in ids]].to_numpy()
    newpairs=[(a,b) for b in range(len(ids)) for a in range(max(16,b+1),len(ids))]
    rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();reps=[]
    for start in range(0,config['replicates'],32):
        count=min(32,config['replicates']-start);draw=rng.integers(0,g,size=(count,g),dtype=np.int64);digest.update(draw.tobytes())
        denominator=8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-root[draw].sum(axis=1));loss=gl[draw].sum(axis=1)
        for a,b in newpairs:
            delta=(loss[:,b]-loss[:,a])/denominator
            reps.extend({'replicate':start+k,'candidate':ids[a],'reference':ids[b],'delta_D2':float(v)} for k,v in enumerate(delta))
    u.require(digest.hexdigest()==old['draws_sha256'],'Sorteos distintos');rf=pd.DataFrame(reps);rf.to_parquet(out/'bootstrap_new_51.parquet',index=False)
    denom=8*(np.sqrt(n.sum()*y.sum())-root.sum());pairs=list(old['pairs'])
    for a,b in newpairs:
        dist=rf.loc[rf.candidate.eq(ids[a])&rf.reference.eq(ids[b]),'delta_D2'];adv=gl[:,b]-gl[:,a]
        removed=max(5,int(np.ceil(.001*g)));excluded=np.argsort(-adv,kind='stable')[:removed];keep=np.ones(g,bool);keep[excluded]=False
        td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum())
        pairs.append({'candidate':ids[a],'reference':ids[b],'delta_D2':float(adv.sum()/denom),'exploratory_lower95':float(dist.quantile(.025)),
          'exploratory_upper95':float(dist.quantile(.975)),'groups':g,'removed_favorable_groups':removed,'delta_after_removal':float(adv[keep].sum()/td),
          'largest_favorable_group_delta':float(adv.max()/denom),'interpretation':'Exploratory 2023 only; no simultaneous confirmation or promotion'})
    u.require(len(pairs)==171 and len(newpairs)==51,'Número de parejas inválido')
    return {'config':config,'draws_sha256':digest.hexdigest(),'pairs':pairs,'new_pairs':51,'reused_pairs_exact':120,
      'inherited_bootstrap':u.relative(parent/'diagnostics/bootstrap_2023.parquet'),'inherited_bootstrap_sha256':u.sha(parent/'diagnostics/bootstrap_2023.parquet')}

def main():
    start=datetime.now(timezone.utc);tick=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['parent_run'];selector=u.read(REPO/'registro/semana2_seleccion_actual.json')
    ledger=ROOT/selector['ledger_workspace_relative'];u.require(not ledger.exists(),'2024 cerrado')
    u.require(u.sha(parent/'manifest.json')==plan['parent_manifest_sha256'] and u.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'],'Padre cambiado')
    u.require(u.sha(Path(__file__))==plan['code_sha256'] and u.sha(ROOT/plan['diagnostic_review'])==plan['diagnostic_sha256'],'Código/revisión cambiada')
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(('<!-- aporte:'+plan['forum_preregistration']+' -->').encode())==1,'Falta receta previa')
    out=parent.parent/('dev7_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir();(out/'models').mkdir();(out/'diagnostics').mkdir()
    (out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());(out/'plan_snapshot.json').write_bytes(PLAN.read_bytes());(out/'forum_before_trial.md').write_bytes(forum)
    sources=[parent/x['path'] for x in u.read(parent/'manifest.json')['files']]+[parent/'manifest.json',PLAN,Path(__file__),ROOT/plan['diagnostic_review'],ROOT/plan['selection_policy'],Path(v5.__file__),Path(u.__file__)]
    frozen=[{'path':u.relative(p),'sha256':u.sha(p)} for p in dict.fromkeys(sources)];u.dump(out/'frozen_sources_before_trial.json',{'files':frozen})
    def forbidden(*a,**k):raise AssertionError('No se autorizan ajustes en ablación congelada')
    for cls in [u.TweedieRegressor,u.SimpleImputer,u.StandardScaler,u.OneHotEncoder,u.ColumnTransformer,u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    old=pq.read_table(parent/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas();u.assert_2023(old.drop_duplicates(KEY));outputs=[old];receipts=[]
    ids=plan['comparators_reused_without_refit']+[m['id'] for m in plan['models']]
    for fold in range(5):
        cred=u.read(parent/f'auxiliary/credibility_fold{fold}.json')['ramos']['motor'];motor=u.joblib.load(parent/f'models/W2-B14_motor_fold{fold}/bundle.joblib');cs,theta=factors(cred,motor)
        for line in u.LINES:
            f=u.load_2023(parent/f'variant_inputs/{line}_fold{fold}.parquet');valid=f[f.fold.eq(fold)].copy();fit=f[f.fold.ne(fold)]
            for col in ['group_id','customer_id','address_id']:u.require(not set(valid[col])&set(fit[col]),'Fuga '+col)
            source=parent/f'models/W2-B14_{line}_fold{fold}/bundle.joblib';base=u.joblib.load(source)
            for mid in ids[16:]:
                folder=out/'models'/f'{mid}_{line}_fold{fold}';folder.mkdir()
                if line=='motor':bundle={'family':'MotorCredibilityRate','parent':base,'columns':base['columns'],'fold':fold,'c':cs[mid],'model_id':mid};u.joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                else:bundle=base;(folder/'bundle.joblib').write_bytes(source.read_bytes())
                with u.threadpool_limits(limits=2):rate=predict(bundle,valid);replay=predict(u.joblib.load(folder/'bundle.joblib'),valid)
                u.require(np.array_equal(rate,replay),'Replay distinto');outputs.append(v5.as_oof(valid,mid,rate))
                receipt={'model_id':mid,'line':line,'fold':fold,'factor':cs[mid] if line=='motor' else 1.,'theta_price':theta if line=='motor' else None,
                  'source_bundle':u.relative(source),'source_sha256':u.sha(source),'heldout_labels_used_for_factor':False,'native_home_exact':line!='motor','replay_exact':True,'new_fits':0}
                u.dump(folder/'receipt.json',receipt);receipts.append(receipt)
    oof=pd.concat(outputs,ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True);u.require(not oof.duplicated(['model_id',*KEY]).any() and oof.year.eq(2023).all(),'OOF inválido')
    u.require(oof[oof.model_id.isin(ids[:16])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)),'Historial cambiado')
    oof.to_parquet(out/'oof_2023.parquet',index=False);summary=list(u.read(parent/'report.json')['summary']);segments=[];scenarios=[]
    for mid in ids[16:]:
        p=oof[oof.model_id.eq(mid)];summary.append({'model_id':mid,**u.metrics(p)})
        for dim,lab in [('line',p.line),('fold',p.fold),('business',np.where(p.x_new_business.eq(1),'new_business','renewal')),
          ('line_business',p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal'))]:
            for label,cell in p.assign(label=lab).groupby('label',observed=True):segments.append({'model_id':mid,'segment':dim,'label':str(label),**u.metrics(cell)})
        for name,(yc,ec) in u.SCENARIOS.items():scenarios.append({'model_id':mid,'scenario':name,**u.metrics(p.assign(scenario_prediction=p.annual_rate*p[ec]),yc,'scenario_prediction')})
    pairs=extend_pairs(oof,parent,out/'diagnostics',ids,plan['diagnostics']['development_uncertainty'])
    for name,obj in [('pairs',pairs),('segments',segments),('observation_sensitivity',scenarios)]:u.dump(out/f'diagnostics/{name}.json',obj)
    for it in frozen:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambiada '+it['path'])
    u.require(not ledger.exists(),'2024 sigue cerrado')
    report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),
      'plan_sha256':u.sha(PLAN),'code_sha256':u.sha(Path(__file__)),'summary':summary,'pairs':pairs['pairs'],'receipts':receipts,
      'new_price_base_fits':0,'new_auxiliary_fits':0,'new_calibrated_factors':0,'new_motor_algebraic_factors':15,'native_home_exact_reuses':30,
      'cumulative_price_base_fits':90,'cumulative_closed_form_constants':60,'auxiliary_fits_v6_reused':30,
      'parent_comparators_exactly_unchanged':True,'reference_retained':'W2-B00','promotion':False,'final_confirmation_roster_frozen':False,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote_training':False,
      'professional_independent_validation':False,'search_disclosure':plan['search_disclosure'],'elapsed_seconds':time.perf_counter()-tick}
    u.dump(out/'report.json',report);u.dump(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':u.sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'run':u.relative(out),'new_summary':summary[-3:],'primary_contrasts':[p for p in pairs['pairs'] if p['candidate'] in ids[16:] and p['reference']=='W2-B14']}),flush=True)
if __name__=='__main__':main()
