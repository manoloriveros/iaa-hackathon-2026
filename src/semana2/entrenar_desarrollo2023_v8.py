"""B19: siete efectos principales, misma respuesta/enlace que B14, solo2023."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,uuid,time,warnings
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('dev8_frozen_utils',REPO/'src/semana2/entrenar_desarrollo2023.py')
u=importlib.util.module_from_spec(s);sys.modules[s.name]=u;s.loader.exec_module(u)
np,pd,pq=u.np,u.pd,u.pq;KEY=u.KEY;MID='W2-B19'

def guard(frame,line,fold=None):
    u.assert_2023(frame)
    u.require(frame.line.eq(line).all() and frame.x_new_business.isin([0,1]).all(),'Ramo/negocio inválido')
    if fold is not None:u.require(frame.fold.ne(fold).all(),'Retenido en GLM')
    col='x_cover_type' if line=='motor' else 'x_accidental_damage_cover'
    u.require(frame[col].notna().all(),'Cobertura ausente')
    u.require(frame[col].isin(['comprehensive','third_party_fire_theft','third_party_only'] if line=='motor' else [0.,1.]).all(),'Cobertura desconocida')
    e=frame['e_cost_mix_1.0'].to_numpy();y=frame.T0.to_numpy()
    u.require(np.isfinite(e).all() and (e>0).all() and np.isfinite(y).all() and (y>=0).all(),'Respuesta/exposición inválida')

def fit_glm7(frame,fold,recipe,line):
    guard(frame,line,fold);block=recipe['features_by_line'][line];cols=block['all']
    u.require(len(cols)==7 and len(set(cols))==7 and set(cols)==set(block['numeric']+block['categorical']),'Siete efectos exactos')
    transformer=u.ColumnTransformer([('numeric',u.Pipeline([('median',u.SimpleImputer(strategy='median',keep_empty_features=True)),('scale',u.StandardScaler())]),block['numeric']),
        ('categorical',u.OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,max_categories=40,sparse_output=True),block['categorical'])],sparse_threshold=1.)
    x=transformer.fit_transform(frame[cols]);e=frame['e_cost_mix_1.0'].to_numpy(float);y=frame.T0.to_numpy(float)/e;w=np.sqrt(e)
    est=u.TweedieRegressor(**recipe['params'])
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
    messages=[{'category':n.category.__name__,'message':str(n.message)} for n in notes]
    u.require(not any(issubclass(n.category,u.ConvergenceWarning) for n in notes) and est.n_iter_<recipe['params']['max_iter'],'No convergió '+str(messages))
    rate=est.predict(x);g=w*(np.sqrt(rate)-y/np.sqrt(rate))/w.sum();score=np.r_[np.asarray(x.T@g).ravel(),g.sum()]
    u.require(np.abs(score).max()<=1e-4,'Gradiente normalizado supera tolerancia técnica previa')
    return {'family':'TweedieRegressor','columns':cols,'transformer':transformer,'estimator':est}, {'n_iter':int(est.n_iter_),'transformed_features':x.shape[1],
        'parameters':est.get_params(),'warnings':messages,'max_abs_score_gradient':float(np.abs(score).max()),'gradient_threshold_before_fit':1e-4,
        'fit_rows':len(frame),'fit_weight_sum':float(w.sum())}

def predict(bundle,frame,line):
    guard(frame,line);return u.predict_bundle(bundle,frame)

def pair_diagnostics(new,old,out,config):
    mids=[MID,'W2-B14','W2-B00'];parts={MID:new.sort_values(KEY).reset_index(drop=True)}
    for mid in mids[1:]:parts[mid]=old[old.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True)
    first=parts[MID];codes,groups=pd.factorize(first.group_id,sort=True);g=len(groups)
    n=np.bincount(codes,minlength=g).astype(float);sy=np.bincount(codes,weights=first.T0,minlength=g);sr=np.bincount(codes,weights=np.sqrt(first.T0),minlength=g)
    losses=[]
    for mid in mids:
        f=parts[mid];u.require(f[KEY].equals(first[KEY]) and f.T0.equals(first.T0),'Parejas con claves/target distintos')
        losses.append(np.bincount(codes,weights=f.unit_deviance,minlength=g))
    losses=np.column_stack(losses);rng=np.random.default_rng(config['seed']);digest=__import__('hashlib').sha256();replicates=[]
    for start in range(0,config['replicates'],32):
        draw=rng.integers(0,g,size=(min(32,config['replicates']-start),g),dtype=np.int64);digest.update(draw.tobytes())
        null=8*(np.sqrt(n[draw].sum(axis=1)*sy[draw].sum(axis=1))-sr[draw].sum(axis=1));bootloss=losses[draw].sum(axis=1)
        for j,ref in enumerate(mids[1:],1):replicates.extend({'replicate':start+k,'candidate':MID,'reference':ref,'delta_D2':float(x)} for k,x in enumerate((bootloss[:,j]-bootloss[:,0])/null))
    rf=pd.DataFrame(replicates);rf.to_parquet(out/'bootstrap_new_pairs.parquet',index=False);pairs=[]
    null=8*(np.sqrt(n.sum()*sy.sum())-sr.sum())
    for j,ref in enumerate(mids[1:],1):
        advantage=losses[:,j]-losses[:,0];keep=np.ones(g,bool);keep[np.argsort(-advantage,kind='stable')[:31]]=False
        reduced=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum());dist=rf[rf.reference.eq(ref)].delta_D2
        pairs.append({'candidate':MID,'reference':ref,'delta_D2':float(advantage.sum()/null),'exploratory_lower95':float(dist.quantile(.025)),'exploratory_upper95':float(dist.quantile(.975)),
            'groups':g,'removed_favorable_groups':31,'delta_after_removal':float(advantage[keep].sum()/reduced)})
    return {'config':config,'draws_sha256':digest.hexdigest(),'pairs':pairs,'conditional_on_frozen_fits':True}

def main():
    planpath=Path(sys.argv[1]).resolve();p=u.read(planpath);tick=time.perf_counter();start=datetime.now(timezone.utc)
    u.require(u.sha(Path(__file__))==p['code_sha256'],'Código cambió')
    for it in p['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambió '+it['path'])
    u.require(u.sha(ROOT/p['main_index_at_prereg'])==p['parent_index_sha256'],'Índice concurrente')
    u.require(u.sha(ROOT/p['counter_index'])==p['counter_before_sha256'],'Contador concurrente')
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1,'Falta receta previa')
    out=REPO/'privado/semana2/desarrollo2023'/('dev8_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    for folder in ['inputs_2023','fit_rows','models','diagnostics']:(out/folder).mkdir()
    (out/'plan_snapshot.json').write_bytes(planpath.read_bytes());(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());(out/'forum_before_fit.md').write_bytes(forum)
    def event(name,**kw):
        record={'utc':datetime.now(timezone.utc).isoformat(),'event':name,**kw}
        with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        print(json.dumps(record),flush=True)
    event('started',run=u.relative(out),expected_price_fits=15)
    source=ROOT/p['input_run'];old=pq.read_table(ROOT/p['parent_oof']).to_pandas();u.assert_2023(old.drop_duplicates(KEY))
    u.require(old.model_id.nunique()==19 and len(old)==19*50094,'Padre incompleto')
    availability=u.read(ROOT/p['availability_contract'])['blocks'];outputs=[];receipts=[];trainval=[];coefs=[];fits=0
    for line in u.LINES:
        block=p['recipe']['features_by_line'][line];u.require(set(block['all'])<=set(availability[line]['all']),'Fuera de contrato F0')
        field='x_cover_type' if line=='motor' else 'x_accidental_damage_cover';rawfield='cover_type' if line=='motor' else 'accidental_damage_cover'
        audited=pq.read_table(ROOT/p['coverage_audit_run']/f'inputs_2023/{line}.parquet',columns=KEY+[rawfield]).to_pandas()
        for fold in range(5):
            frame=u.load_2023(source/f'variant_inputs/{line}_fold{fold}.parquet');guard(frame,line)
            coverage=frame[KEY+[field]].merge(audited,on=KEY,validate='one_to_one');u.require(coverage[field].eq(coverage[rawfield]).all(),'Cobertura cambia respecto a auditoría')
            base=old[old.model_id.eq('W2-B14')&old.line.eq(line)].sort_values(KEY).reset_index(drop=True);actual=frame.sort_values(KEY).reset_index(drop=True)
            u.require(actual[KEY].equals(base[KEY]),'Claves distintas de B14')
            for col in ['T0','exposure','fold','group_id']:u.require(actual[col].equals(base[col]),'T0/partición cambió '+col)
            # OOF contains each row's OWN held fold link, while this input has the
            # current fold's link also on its training rows. Compare like scopes.
            av=actual[actual.fold.eq(fold)].reset_index(drop=True);bv=base[base.fold.eq(fold)].reset_index(drop=True)
            for col in [c for c in base if c.startswith('e_cost_mix_')]:u.require(av[col].equals(bv[col]),'C0 retenido cambió '+col)
            fit=frame[frame.fold.ne(fold)].copy();valid=frame[frame.fold.eq(fold)].copy()
            u.require(all(set(fit[c]).isdisjoint(valid[c]) for c in ['group_id','customer_id','address_id']),'Fuga de componente')
            frame.to_parquet(out/f'inputs_2023/{line}_fold{fold}.parquet',index=False)
            roles=frame[KEY+['year','fold','group_id']].copy();roles['role']=np.where(frame.fold.eq(fold),'validation','fit');roles.to_parquet(out/f'fit_rows/{line}_fold{fold}.parquet',index=False)
            event('fit_started',line=line,fold=fold,train_rows=len(fit))
            with u.threadpool_limits(limits=2):bundle,notes=fit_glm7(fit,fold,p['recipe'],line)
            fits+=1;folder=out/'models'/f'{MID}_{line}_fold{fold}';folder.mkdir();u.joblib.dump(bundle,folder/'bundle.joblib',compress=3)
            with u.threadpool_limits(limits=2):
                rate=predict(bundle,valid,line);replay=predict(u.joblib.load(folder/'bundle.joblib'),valid,line);trainrate=predict(bundle,fit,line)
            u.require(np.array_equal(rate,replay),'Replay distinto')
            vpart=base[base.fold.eq(fold)].copy();ordered=valid.sort_values(KEY).reset_index(drop=True);rate_order=pd.DataFrame({**{k:valid[k].to_numpy() for k in KEY},'rate':rate}).sort_values(KEY).rate.to_numpy()
            u.require(vpart[KEY].reset_index(drop=True).equals(ordered[KEY]),'Claves OOF distintas')
            vpart['model_id']=MID;vpart['annual_rate']=rate_order;vpart['prediction']=ordered['e_cost_mix_1.0'].to_numpy()*rate_order;vpart['unit_deviance']=u.unit_deviance(ordered.T0,vpart.prediction);outputs.append(vpart)
            for name,f,rr in [('fit',fit,trainrate),('validation',valid,rate)]:
                q=f.assign(prediction=f['e_cost_mix_1.0'].to_numpy()*rr);trainval.append({'model_id':MID,'line':line,'fold':fold,'role':name,**u.metrics(q)})
            feature_names=bundle['transformer'].get_feature_names_out()
            coefs.extend({'line':line,'fold':fold,'feature':str(name),'coefficient':float(coef)} for name,coef in zip(feature_names,bundle['estimator'].coef_))
            coefs.append({'line':line,'fold':fold,'feature':'intercept','coefficient':float(bundle['estimator'].intercept_)})
            receipt={'model_id':MID,'line':line,'fold':fold,'features':block['all'],'new_coverage_field':field,'T0_C0_unchanged':True,'validation_rows':len(valid),'replay_exact':True,**notes}
            u.dump(folder/'receipt.json',receipt);receipts.append(receipt);event('fit_completed',line=line,fold=fold,price_fits=fits,gradient=notes['max_abs_score_gradient'])
    new=pd.concat(outputs,ignore_index=True).sort_values(KEY).reset_index(drop=True);u.require(len(new)==50094 and not new.duplicated(KEY).any(),'B19 OOF incompleto')
    new.to_parquet(out/'new_oof_2023.parquet',index=False)
    combined=pd.concat([old,new],ignore_index=True).sort_values(['model_id',*KEY]).reset_index(drop=True);u.require(combined[combined.model_id.ne(MID)].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)),'Alternativas cambiaron')
    combined.to_parquet(out/'oof_2023.parquet',index=False)
    compare=combined[combined.model_id.isin([MID,'W2-B14','W2-B00'])].copy();segments=[];summaries=[]
    meta=pd.concat([pq.read_table(out/f'inputs_2023/{line}_fold0.parquet',columns=KEY+['x_cover_type' if line=='motor' else 'x_accidental_damage_cover']).to_pandas().assign(coverage=lambda f:f['x_cover_type'].astype(str) if 'x_cover_type' in f else np.where(f.x_accidental_damage_cover.eq(1),'AD_yes','AD_no'))[KEY+['coverage']] for line in u.LINES],ignore_index=True)
    compare=compare.merge(meta,on=KEY,validate='many_to_one')
    for mid,g in compare.groupby('model_id'):
        summaries.append({'model_id':mid,**u.metrics(g),'conditional_nominal_2023':float((g.exposure*g.annual_rate).sum())})
        dimensions={'line':g.line.astype(str),'fold':g.fold.astype(str),'business':np.where(g.x_new_business.eq(1),'new_business','renewal'),
            'line_business':g.line.astype(str)+'_'+np.where(g.x_new_business.eq(1),'new_business','renewal'),'line_coverage':g.line.astype(str)+'_'+g.coverage,
            'line_business_coverage':g.line.astype(str)+'_'+np.where(g.x_new_business.eq(1),'new_business','renewal')+'_'+g.coverage}
        for dimension,labels in dimensions.items():
            for label,cell in g.assign(label=labels).groupby('label',observed=True):segments.append({'model_id':mid,'dimension':dimension,'label':str(label),**u.metrics(cell),'conditional_nominal_2023':float((cell.exposure*cell.annual_rate).sum())})
    pairs=pair_diagnostics(new,old,out/'diagnostics',p['bootstrap'])
    for name,value in [('new_pairs',pairs),('segments',segments),('train_validation',trainval),('coefficients',coefs)]:u.dump(out/f'diagnostics/{name}.json',value)
    for it in p['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambió '+it['path'])
    u.require(u.sha(ROOT/p['main_index_at_prereg'])==p['parent_index_sha256'] and u.sha(ROOT/p['counter_index'])==p['counter_before_sha256'],'Concurrencia al cerrar')
    report={'id':p['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':u.sha(planpath),'code_sha256':u.sha(Path(__file__)),
        'summary':summaries,'pairs':pairs['pairs'],'receipts':receipts,'new_price_base_fits':fits,'new_closed_form_constants':0,'new_auxiliary_fits':0,'new_curve_fits':0,
        'cumulative_own_price_base_fits':p['counters_before']['cumulative_price_base_fits']+fits,'cumulative_own_closed_form_constants':p['counters_before']['cumulative_closed_form_constants'],
        'catalog_lineage_price_base_fits':105,'catalog_lineage_closed_form_constants':60,'parent_comparators_exactly_unchanged':True,'reference':'W2-B00','all_alternatives_preserved':True,
        'promotion':False,'final_confirmation_roster_frozen':False,'professional_independent_validation':False,'external2024_subject_exposure_previously_disclosed':True,
        'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'ledger_read':False,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote':False,'elapsed_seconds':time.perf_counter()-tick}
    u.require(fits==15,'Número de ajustes distinto');u.dump(out/'report.json',report)
    u.dump(out/'manifest.json',{'files':[{'path':x.relative_to(out).as_posix(),'sha256':u.sha(x),'bytes':x.stat().st_size} for x in sorted(out.rglob('*')) if x.is_file()]})
    print(json.dumps({'event':'completed','run':u.relative(out),'new_price_fits':fits,'summary':summaries,'new_pairs':pairs['pairs']}),flush=True)

if __name__=='__main__':main()
