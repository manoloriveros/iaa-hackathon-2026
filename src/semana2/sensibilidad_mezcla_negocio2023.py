"""Mezclas C0 por negocio: frecuencia y severidad, con curvas por peril fijas."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,uuid,hashlib,time
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('mix_standard',REPO/'src/semana2/entrenar_desarrollo2023_v5.py');v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)
u=v.u;np,pd,pq=u.np,u.pd,u.pq;KEY=u.KEY;MIDS=['W2-B00','W2-B12','W2-B14'];VARIANTS=['MIXF','MIXFS'];PLAN=REPO/'registro/semana2_c0_mezcla_negocio2023_plan_v1.json'

def normalize(values):
    a=np.asarray(list(values.values()),float);u.require(np.isfinite(a).all() and (a>=0).all() and a.sum()>0,'Costes de mezcla inválidos')
    return {key:float(value/a.sum()) for key,value in values.items()}

def estimate_mixtures(frame,curves,claims,models,fold,line):
    u.assert_2023(frame);u.require(frame.line.eq(line).all() and frame.x_new_business.isin([0,1]).all(),'Ramo/negocio inválido')
    u.require(claims.year.eq(2023).all() and claims.fold.ne(fold).all() and claims.line.eq(line).all() and claims.claim_id.is_unique,'Reclamaciones ajenas al ajuste')
    fit=frame.fold.ne(fold);u.require(set(claims.row_id).issubset(set(frame.loc[fit,'row_id'])),'Retenido en mezcla')
    u.require(curves[KEY].equals(frame[KEY]),'Curvas desordenadas');perils=sorted(models);u.require(set(claims.peril)==set(perils),'Perils incompletos')
    rows=[];pooled_raw={};mixed={name:{} for name in VARIANTS};freq_count=0;severity_count=0
    for peril in perils:
        g=claims[claims.peril.eq(peril)];w=g.severity_probability_weight.to_numpy();net=g.T0_cents.to_numpy()/100
        u.require(np.isfinite(w).all() and (w>=0).all() and w.sum()>0,'Pesos de truncamiento inválidos')
        mean=float(models[peril]['mean_net_mark']['1.0']);den=float(np.sum(frame.loc[fit,'exposure']*curves.loc[fit,'qN_'+peril]))
        u.require(np.isclose(np.dot(w,net)/w.sum(),mean,rtol=1e-10,atol=1e-7),'Severidad pooled no reproduce C0')
        pooled_raw[peril]=len(g)/den*mean
    for business in [0,1]:
        selection=fit&frame.x_new_business.eq(business);u.require(selection.any(),'No hay exposición de negocio en ajuste')
        raw_frequency={};raw_both={}
        for peril in perils:
            g=claims[claims.peril.eq(peril)&claims.x_new_business.eq(business)];n=len(g);w=g.severity_probability_weight.to_numpy();y=g.T0_cents.to_numpy()/100
            den=float(np.sum(frame.loc[selection,'exposure']*curves.loc[selection,'qN_'+peril]));u.require(den>0,'Exposición por negocio/peril nula')
            frequency=n/den;mu=float(models[peril]['mean_net_mark']['1.0']);freq_count+=1
            if n:
                u.require(w.sum()>0 and np.dot(w,y)>0,'Severidad de negocio no estimable; sin fallback al retenido')
                severity=float(np.dot(w,y)/w.sum());ess=float(w.sum()**2/np.dot(w,w));largest=float((w*y).max()/np.dot(w,y));severity_count+=1
            else:severity=None;ess=0.;largest=None
            raw_frequency[peril]=frequency*mu;raw_both[peril]=frequency*(severity if severity is not None else 0.)
            rows.append({'line':line,'fold':fold,'business':business,'peril':peril,'claims':n,'groups':int(g.group_id.nunique()),'effective_count_exposure':den,
              'frequency_rate':frequency,'pooled_severity':mu,'business_severity':severity,'weight_sum':float(w.sum()),'weighted_effective_sample_size':ess,
              'largest_weighted_cost_share':largest,'zero_count_boundary':n==0,'fit_rows':int(selection.sum())})
        mixed['MIXF'][business]=normalize(raw_frequency);mixed['MIXFS'][business]=normalize(raw_both)
    exposures={}
    for variant in VARIANTS:
        q=np.zeros(len(frame))
        for business in [0,1]:
            mask=frame.x_new_business.eq(business);q[mask]=sum(mixed[variant][business][peril]*curves.loc[mask,'qC_1.0_'+peril].to_numpy() for peril in perils)
        exposures[variant]=frame.exposure.to_numpy()*q
        u.require(np.isfinite(q).all() and (q>0).all() and (q<=1+1e-10).all(),'Completitud de mezcla inválida')
    return exposures,{'line':line,'fold':fold,'pooled_shares_rebuilt':normalize(pooled_raw),'business_shares':mixed,'cell_estimates':rows,
      'new_frequency_constants':freq_count,'new_weighted_severity_means':severity_count,'curve_refits':0}

def as_oof(valid,variant,mid,rate,e):
    p=valid[KEY+['year','is_test','group_id','fold','exposure','T0','x_new_business']].copy();p['variant']=variant;p['model_id']=mid;p['stress_id']=variant+'_'+mid
    p['effective_exposure']=np.asarray(e);p['annual_rate']=rate;p['prediction']=np.asarray(e)*rate;p['conditional_nominal_2023']=p.exposure*rate;p['unit_deviance']=u.unit_deviance(p.T0,p.prediction)
    return p

def pair_diagnostics(oof,old,out,config):
    ids=[variant+'_'+mid for variant in VARIANTS for mid in MIDS]+MIDS;parts={sid:q.sort_values(KEY).reset_index(drop=True) for sid,q in oof.groupby('stress_id')}
    for mid in MIDS:parts[mid]=old[old.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True)
    first=parts[ids[0]];codes,groups=pd.factorize(first.group_id,sort=True);g=len(groups);n=np.bincount(codes,minlength=g).astype(float);y=np.bincount(codes,weights=first.T0,minlength=g);root=np.bincount(codes,weights=np.sqrt(first.T0),minlength=g)
    gl=[]
    for sid in ids:
        q=parts[sid];u.require(q[KEY].equals(first[KEY]) and q.T0.equals(first.T0),'Parejas con claves/target distintos');gl.append(np.bincount(codes,weights=q.unit_deviance,minlength=g))
    gl=np.column_stack(gl);pairs=[]
    for variant in VARIANTS:
        for a,b in [(1,0),(2,0),(2,1)]:pairs.append((ids.index(variant+'_'+MIDS[a]),ids.index(variant+'_'+MIDS[b])))
    for mid in MIDS:pairs.extend([(ids.index('MIXF_'+mid),ids.index(mid)),(ids.index('MIXFS_'+mid),ids.index('MIXF_'+mid))])
    rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();reps=[]
    for start in range(0,config['replicates'],32):
        count=min(32,config['replicates']-start);draw=rng.integers(0,g,size=(count,g),dtype=np.int64);digest.update(draw.tobytes());loss=gl[draw].sum(axis=1)
        den=8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-root[draw].sum(axis=1))
        for a,b in pairs:reps.extend({'replicate':start+k,'candidate':ids[a],'reference':ids[b],'delta_D2':float(value)} for k,value in enumerate((loss[:,b]-loss[:,a])/den))
    rf=pd.DataFrame(reps);rf.to_parquet(out/'bootstrap_12_pairs.parquet',index=False);records=[];den=8*(np.sqrt(n.sum()*y.sum())-root.sum())
    for a,b in pairs:
        adv=gl[:,b]-gl[:,a];keep=np.ones(g,bool);keep[np.argsort(-adv,kind='stable')[:31]]=False;td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum());dist=rf[rf.candidate.eq(ids[a])&rf.reference.eq(ids[b])].delta_D2
        records.append({'candidate':ids[a],'reference':ids[b],'delta_D2':float(adv.sum()/den),'exploratory_lower95':float(dist.quantile(.025)),'exploratory_upper95':float(dist.quantile(.975)),
          'removed_favorable_groups':31,'delta_after_removal':float(adv[keep].sum()/td)})
    return {'config':config,'draws_sha256':digest.hexdigest(),'pairs':records}

def main():
    start=datetime.now(timezone.utc);tick=time.perf_counter();plan=u.read(PLAN);parent=ROOT/plan['input_run'];linkroot=ROOT/plan['observation_run'];selector=u.read(REPO/'registro/semana2_seleccion_actual.json')
    u.require(not (ROOT/selector['ledger_workspace_relative']).exists(),'2024 cerrado')
    for it in plan['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambiada '+it['path'])
    u.require(u.sha(Path(__file__))==plan['code_sha256'],'Código cambiado');forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();u.require(forum.count(('<!-- aporte:'+plan['forum_preregistration']+' -->').encode())==1,'Falta receta previa')
    out=parent.parent/('mezcla_'+start.strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    for folder in ['models','inputs_2023','mixtures','diagnostics']:(out/folder).mkdir()
    (out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());(out/'plan_snapshot.json').write_bytes(PLAN.read_bytes());(out/'forum_before_fit.md').write_bytes(forum)
    u.dump(out/'environment.json',{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':u.pa.__version__,'threads':2,'seed':2026102302})
    old=pq.read_table(ROOT/plan['base_oof'],filters=[('year','=',2023),('model_id','in',MIDS)]).to_pandas();u.assert_2023(old.drop_duplicates(KEY));old.to_parquet(out/'base_oof_2023.parquet',index=False)
    meta=pd.concat([u.load_2023(parent/f'inputs_2023/{line}.parquet')[KEY+['x_new_business']] for line in u.LINES],ignore_index=True)
    claims=pq.read_table(ROOT/plan['claim_source_2023']).to_pandas().merge(meta,on=KEY,validate='many_to_one');u.require(claims.year.eq(2023).all() and claims.claim_id.is_unique,'Siniestros no2023/duplicados');claims.to_parquet(out/'inputs_2023/claims_2023.parquet',index=False)
    core=u.read(parent/'plan_snapshot.json')['core_recipe'];outputs=[];details=[];receipts=[];fitcount=0;constantcount=0;reuses=0;frequencycount=0;severitycount=0
    for fold in range(5):
        source_models=u.read(linkroot/f'exclude_fold{fold}/reporting_models.json')
        weight_source=pq.read_table(linkroot/f'exclude_fold{fold}/severity_fit_weights.parquet',filters=[('year','=',2023)]).to_pandas()
        for line in u.LINES:
            frame=u.load_2023(parent/f'variant_inputs/{line}_fold{fold}.parquet');perils=sorted(key.split('|',1)[1] for key in source_models if key.startswith(line+'|'));models={peril:source_models[line+'|'+peril] for peril in perils}
            columns=KEY+['qN_'+peril for peril in perils]+['qC_1.0_'+peril for peril in perils]
            curves=pq.read_table(linkroot/f'exclude_fold{fold}/observation_link_{line}.parquet',filters=[('year','=',2023),('is_test','=',False)],columns=columns).to_pandas();curves=frame[KEY].merge(curves,on=KEY,validate='one_to_one',sort=False)
            fclaims=claims[claims.line.eq(line)&claims.fold.ne(fold)].copy();weights=weight_source[weight_source.line.eq(line)]
            u.require(set(fclaims.claim_id)==set(weights.claim_id),'Pesos y claims de ajuste distintos');fclaims=fclaims.merge(weights[['claim_id','severity_probability_weight']],on='claim_id',validate='one_to_one')
            fclaims.to_parquet(out/f'inputs_2023/{line}_fold{fold}_fitclaims.parquet',index=False)
            exposures,detail=estimate_mixtures(frame,curves,fclaims,models,fold,line);baseline=u.read(linkroot/f'exclude_fold{fold}/peril_cost_shares_{line}.json')['1.0']
            u.require(all(np.isclose(detail['pooled_shares_rebuilt'][peril],baseline[peril],rtol=1e-10,atol=1e-12) for peril in perils),'No reproduce mezcla pooled')
            u.dump(out/f'mixtures/{line}_fold{fold}.json',detail);details.append(detail);frequencycount+=detail['new_frequency_constants'];severitycount+=detail['new_weighted_severity_means']
            fitmask=frame.fold.ne(fold);fit=frame.loc[fitmask];valid=frame.loc[~fitmask];u.require(all(not set(fit[key])&set(valid[key]) for key in ['group_id','customer_id','address_id']),'Fuga')
            for variant,e in exposures.items():
                train=fit.copy();train['e_cost_mix_1.0']=e[fitmask];u.assert_2023(train);u.require(train.fold.ne(fold).all(),'Retenido en precio')
                identity=float(np.max(np.abs(e-frame['e_cost_mix_1.0'].to_numpy())))<=plan['numerical_link_identity_atol']
                q=frame[KEY+['year','is_test','fold','group_id','exposure','T0','x_new_business']].copy();q['effective_exposure']=e;q['base_e']=frame['e_cost_mix_1.0'];q.to_parquet(out/f'inputs_2023/{variant}_{line}_fold{fold}.parquet',index=False)
                for mid in MIDS:
                    source=ROOT/plan['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib';folder=out/'models'/f'{variant}_{mid}_{line}_fold{fold}';folder.mkdir();notes={}
                    if identity:bundle=u.joblib.load(source);(folder/'bundle.joblib').write_bytes(source.read_bytes());reuses+=1
                    else:
                        if mid=='W2-B00':
                            et=train['e_cost_mix_1.0'].to_numpy();yt=train.T0.to_numpy();rate=float(np.sum(yt/np.sqrt(et))/np.sqrt(et).sum());bundle={'family':'constant_line_rate','rate':rate,'columns':[]};notes={'rate':rate};constantcount+=1
                        elif mid=='W2-B12':bundle,business_details=v.constant_fit(train,fold);notes={'business_details':business_details};constantcount+=2
                        else:
                            with u.threadpool_limits(limits=2):bundle,notes=v.glm_fit(train,fold,core,line)
                            fitcount+=1
                        u.joblib.dump(bundle,folder/'bundle.joblib',compress=3)
                    with u.threadpool_limits(limits=2):rate=v.predict(bundle,valid);replay=v.predict(u.joblib.load(folder/'bundle.joblib'),valid)
                    u.require(np.array_equal(rate,replay),'Replay distinto');outputs.append(as_oof(valid,variant,mid,rate,e[~fitmask]))
                    receipt={'variant':variant,'model_id':mid,'line':line,'fold':fold,'train_rows':len(train),'validation_rows':len(valid),'native_exact_reuse':identity,'source':u.relative(source),
                      'source_sha256':u.sha(source),'numerical_link_identity_atol':plan['numerical_link_identity_atol'],'replay_exact':True,'heldout_labels_used':False,**notes};u.dump(folder/'receipt.json',receipt);receipts.append(receipt)
            print(json.dumps({'event':'scope_completed','fold':fold,'line':line,'GLM_fits':fitcount,'price_constants':constantcount}),flush=True)
    oof=pd.concat(outputs,ignore_index=True).sort_values(['stress_id',*KEY]).reset_index(drop=True);u.require(len(oof)==6*50094 and oof.year.eq(2023).all() and not oof.duplicated(['stress_id',*KEY]).any(),'OOF inválido');oof.to_parquet(out/'mixture_oof_2023.parquet',index=False)
    summary=[];segments=[]
    for sid,q in oof.groupby('stress_id'):
        base=old[old.model_id.eq(q.model_id.iloc[0])].sort_values(KEY).reset_index(drop=True);q=q.sort_values(KEY).reset_index(drop=True);u.require(q[KEY].equals(base[KEY]) and q.T0.equals(base.T0),'Claves/target distintos')
        summary.append({'stress_id':sid,'variant':q.variant.iloc[0],'model_id':q.model_id.iloc[0],**u.metrics(q),'conditional_nominal_2023':float(q.conditional_nominal_2023.sum()),
          'base_nominal_2023':float((base.exposure*base.annual_rate).sum()),'nominal_relative_change':float(q.conditional_nominal_2023.sum()/(base.exposure*base.annual_rate).sum()-1)})
        for dimension,labels in [('line',q.line),('fold',q.fold.astype(str)),('business',np.where(q.x_new_business.eq(1),'new_business','renewal')),('line_business',q.line.astype(str)+'_'+np.where(q.x_new_business.eq(1),'new_business','renewal'))]:
            for label,cell in q.assign(label=labels).groupby('label',observed=True):segments.append({'stress_id':sid,'dimension':dimension,'label':str(label),**u.metrics(cell),'conditional_nominal_2023':float(cell.conditional_nominal_2023.sum())})
    pairs=pair_diagnostics(oof,old,out/'diagnostics',plan['bootstrap']);u.dump(out/'diagnostics/pairs.json',pairs);u.dump(out/'diagnostics/segments.json',segments)
    for it in plan['frozen_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente cambió')
    u.require(not (ROOT/selector['ledger_workspace_relative']).exists(),'2024 cerrado')
    report={'id':plan['id'],'author':'Codex','run':u.relative(out),'started_utc':start.isoformat(),'completed_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':u.sha(PLAN),'code_sha256':u.sha(Path(__file__)),
      'summary':summary,'mixture_details':details,'receipts':receipts,'new_price_GLM_fits':fitcount,'new_closed_form_constants':constantcount,'exact_native_reuses':reuses,
      'new_mixture_frequency_constants':frequencycount,'new_mixture_weighted_severity_means':severitycount,'new_reporting_curve_fits':0,'new_auxiliary_credibility_fits':0,
      'cumulative_price_base_fits':plan['counters_before']['cumulative_price_base_fits']+fitcount,'cumulative_closed_form_constants':plan['counters_before']['cumulative_closed_form_constants']+constantcount,
      'reference':'W2-B00','main_catalog_unchanged':True,'promotion':False,'professional_independent_validation':False,
      'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False},'test_predictions':0,'submissions':0,'remote':False,'elapsed_seconds':time.perf_counter()-tick}
    u.dump(out/'report.json',report);u.dump(out/'manifest.json',{'files':[{'path':path.relative_to(out).as_posix(),'sha256':u.sha(path),'bytes':path.stat().st_size} for path in sorted(out.rglob('*')) if path.is_file()]})
    print(json.dumps({'event':'completed','run':u.relative(out),'summary':summary,'price_fits':fitcount,'price_constants':constantcount,'frequency_constants':frequencycount,'weighted_severity_means':severitycount}),flush=True)
if __name__=='__main__':main()
