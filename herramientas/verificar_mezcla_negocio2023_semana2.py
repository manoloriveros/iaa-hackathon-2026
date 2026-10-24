"""Oráculo separado de la mezcla C0 por negocio y del consumidor de precio."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,re,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('mix_oracle_base',REPO/'herramientas/verificar_desarrollo2023_semana2.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;MIDS=['W2-B00','W2-B12','W2-B14'];VARIANTS=['MIXF','MIXFS'];ATTEMPTS=0
def forbidden(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('Fit bloqueado en comprobador')
def native(bundle,frame):
    assert frame.year.eq(2023).all() and not frame.is_test.any()
    if bundle['family']=='constant_line_rate':return np.full(len(frame),bundle['rate'])
    if bundle['family']=='business_constant':return np.asarray([bundle['rates'][int(x)] for x in frame.x_new_business])
    assert bundle['family']=='TweedieRegressor'
    return np.exp(np.asarray(bundle['transformer'].transform(frame[bundle['columns']])@bundle['estimator'].coef_).ravel()+bundle['estimator'].intercept_)
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=c.read(run/'report.json');p=c.read(run/'plan_snapshot.json');source=ROOT/p['input_run'];linkroot=ROOT/p['observation_run'];checks=[];gradients=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    close=lambda a,b:np.allclose(a,b,rtol=3e-9,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in p['frozen_sources']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Plan/code frozen',c.sha(run/'code_snapshot.py')==r['code_sha256']==p['code_sha256'] and c.sha(run/'plan_snapshot.json')==r['plan_sha256'])
    h=re.search(r'^## Codex \| COD-S2-20261024-027 \| ([^|]+) \|',(run/'forum_before_fit.md').read_text(encoding='utf-8'),re.M)
    check('Recipe before execution',h is not None and datetime.fromisoformat(h[1].strip())<datetime.fromisoformat(r['started_utc']))
    check('Main catalog exact',c.sha(ROOT/p['main_model_index'])==p['main_model_index_sha256'])
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    claims=pq.read_table(run/'inputs_2023/claims_2023.parquet').to_pandas();raw=pq.read_table(ROOT/p['claim_source_2023']).to_pandas();new=pq.read_table(run/'mixture_oof_2023.parquet').to_pandas();old=pq.read_table(run/'base_oof_2023.parquet').to_pandas()
    check('Canonical2023 claims and original fields',claims.year.eq(2023).all() and claims.claim_id.is_unique and claims.drop(columns='x_new_business').sort_values('claim_id').reset_index(drop=True).equals(raw.sort_values('claim_id').reset_index(drop=True)))
    check('Six full2023 OOF',len(new)==6*50094 and new.year.eq(2023).all() and not new.is_test.any() and not new.duplicated(['stress_id',*KEY]).any())
    counts={'GLM':0,'price_constants':0,'reuse':0,'mixture_frequency':0,'mixture_severity':0}
    from scipy.optimize import minimize_scalar
    for fold in range(5):
        models=c.read(linkroot/f'exclude_fold{fold}/reporting_models.json')
        for line in ['motor','buildings','contents']:
            frame=pq.read_table(source/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas();fitmask=frame.fold.ne(fold);fit=frame[fitmask];valid=frame[~fitmask]
            check('2023 disjoint '+line+str(fold),frame.year.eq(2023).all() and not frame.is_test.any() and all(not set(fit[k])&set(valid[k]) for k in ['group_id','customer_id','address_id']))
            fc=pq.read_table(run/f'inputs_2023/{line}_fold{fold}_fitclaims.parquet').to_pandas();gsource=claims[claims.line.eq(line)&claims.fold.ne(fold)]
            check('Only owntraining claims '+line+str(fold),fc.fold.ne(fold).all() and fc.year.eq(2023).all() and set(fc.claim_id)==set(gsource.claim_id))
            business_lookup=frame.set_index('row_id').x_new_business;check('Business from own policy '+line+str(fold),np.array_equal(fc.x_new_business,fc.row_id.map(business_lookup)))
            perils=sorted(key.split('|',1)[1] for key in models if key.startswith(line+'|'));columns=KEY+['qN_'+x for x in perils]+['qC_1.0_'+x for x in perils]
            curves=pq.read_table(linkroot/f'exclude_fold{fold}/observation_link_{line}.parquet',filters=[('year','=',2023),('is_test','=',False)],columns=columns).to_pandas();curves=frame[KEY].merge(curves,on=KEY,validate='one_to_one',sort=False)
            detail=c.read(run/f'mixtures/{line}_fold{fold}.json');rawcost={variant:{business:[] for business in [0,1]} for variant in VARIANTS};expected_pooled=[]
            for peril in perils:
                g=fc[fc.peril.eq(peril)];model=models[line+'|'+peril];support=np.asarray(model['delay_days']);events=np.asarray(model['events']);mass=np.maximum(np.diff(np.r_[0.,model['count_cdf']]),0);pos=np.searchsorted(support,g.delay.to_numpy());expected_w=len(g)*mass[pos]/events[pos]
                check('Truncation weight formula '+line+str(fold)+peril,close(g.severity_probability_weight,expected_w))
                y=g.T0_cents.to_numpy()/100;mu=float(np.sum(expected_w*y)/np.sum(expected_w));den=float(np.sum(frame.loc[fitmask,'exposure']*curves.loc[fitmask,'qN_'+peril]));expected_pooled.append(len(g)/den*mu)
                check('Pooled weighted mark '+line+str(fold)+peril,close(mu,model['mean_net_mark']['1.0']))
                for business in [0,1]:
                    cell=g[g.x_new_business.eq(business)];mask=fitmask&frame.x_new_business.eq(business);exposure=float(np.sum(frame.loc[mask,'exposure']*curves.loc[mask,'qN_'+peril]));n=len(cell);rate=n/exposure;counts['mixture_frequency']+=1
                    record=next(z for z in detail['cell_estimates'] if z['business']==business and z['peril']==peril)
                    check('Poisson exposure/count '+line+str(fold)+peril+str(business),record['claims']==n and close(record['effective_count_exposure'],exposure) and close(record['frequency_rate'],rate) and record['fit_rows']==int(mask.sum()))
                    if n:
                        counts['mixture_severity']+=1;w=cell.severity_probability_weight.to_numpy();net=cell.T0_cents.to_numpy()/100;mean=float(np.average(net,weights=w));ess=float(w.sum()**2/np.square(w).sum());largest=float(np.max(w*net)/np.dot(w,net))
                        poisson=minimize_scalar(lambda eta:float(exposure*np.exp(eta)-n*eta),bounds=(np.log(rate)-1,np.log(rate)+1),method='bounded',options={'xatol':1e-10})
                        gamma=minimize_scalar(lambda eta:float(np.dot(w,net/np.exp(eta)+eta)),bounds=(np.log(mean)-1,np.log(mean)+1),method='bounded',options={'xatol':1e-10})
                        check('Poisson/Gamma scalar optimum '+line+str(fold)+peril+str(business),poisson.success and gamma.success and abs(poisson.x-np.log(rate))<2e-6 and abs(gamma.x-np.log(mean))<2e-6)
                        check('Severity/ESS/concentration '+line+str(fold)+peril+str(business),close([record['business_severity'],record['weighted_effective_sample_size'],record['largest_weighted_cost_share']],[mean,ess,largest]))
                    else:
                        mean=0.;check('Zero frequency boundary, severity absent '+line+str(fold)+peril+str(business),record['frequency_rate']==0 and record['business_severity'] is None and record['weighted_effective_sample_size']==0)
                    rawcost['MIXF'][business].append(rate*mu);rawcost['MIXFS'][business].append(rate*mean)
            expected_pooled=np.asarray(expected_pooled);expected_pooled/=expected_pooled.sum();stored_pooled=c.read(linkroot/f'exclude_fold{fold}/peril_cost_shares_{line}.json')['1.0']
            check('Pooled source reconstruction '+line+str(fold),close(expected_pooled,[stored_pooled[x] for x in perils]) and close(expected_pooled,[detail['pooled_shares_rebuilt'][x] for x in perils]))
            for variant in VARIANTS:
                exposure=np.zeros(len(frame))
                for business in [0,1]:
                    costs=np.asarray(rawcost[variant][business]);shares=costs/costs.sum();saved=detail['business_shares'][variant][str(business)];mask=frame.x_new_business.eq(business)
                    check('Business convex weights '+variant+line+str(fold)+str(business),np.isfinite(shares).all() and (shares>=0).all() and close(shares.sum(),1.) and close(shares,[saved[x] for x in perils]))
                    exposure[mask]=frame.loc[mask,'exposure'].to_numpy()*(curves.loc[mask,['qC_1.0_'+x for x in perils]].to_numpy()@shares)
                inp=pq.read_table(run/f'inputs_2023/{variant}_{line}_fold{fold}.parquet').to_pandas();check('Complete business exposure '+variant+line+str(fold),close(inp.effective_exposure,exposure) and inp[KEY].equals(frame[KEY]) and (exposure>0).all() and (exposure<=frame.exposure+1e-10).all())
                for mid in MIDS:
                    path=run/'models'/f'{variant}_{mid}_{line}_fold{fold}/bundle.joblib';bundle=c.joblib.load(path);receipt=c.read(path.parent/'receipt.json')
                    check('Full price fit rows '+variant+mid+line+str(fold),receipt['train_rows']==len(fit) and receipt['validation_rows']==len(valid))
                    if receipt['native_exact_reuse']:
                        counts['reuse']+=1;check('Identity native reuse '+variant+mid+line+str(fold),c.sha(path)==receipt['source_sha256'] and np.max(np.abs(inp.effective_exposure-frame['e_cost_mix_1.0']))<=p['numerical_link_identity_atol'])
                    elif mid!='W2-B14':
                        for business in ([None] if mid=='W2-B00' else [0,1]):
                            counts['price_constants']+=1;sel=np.ones(len(fit),bool) if business is None else fit.x_new_business.eq(business).to_numpy();e=exposure[fitmask][sel];y=fit.T0.to_numpy()[sel];rate=bundle['rate'] if business is None else bundle['rates'][business]
                            optimum=minimize_scalar(lambda eta:float(c.dev(y,e*np.exp(eta)).sum()),bounds=(np.log(rate)-1,np.log(rate)+1),method='bounded',options={'xatol':1e-10});check('Price scalar optimum '+variant+mid+line+str(fold)+str(business),optimum.success and abs(optimum.x-np.log(rate))<2e-6)
                    else:
                        counts['GLM']+=1;tr=bundle['transformer'];numeric=tr.transformers_[0][2];original=c.joblib.load(ROOT/p['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib')
                        check('GLM original params/imputer '+variant+line+str(fold),bundle['estimator'].get_params()==original['estimator'].get_params() and close(tr.named_transformers_['numeric'].named_steps['median'].statistics_,fit[numeric].median().fillna(0)))
                        x=tr.transform(fit[bundle['columns']]);mu=native(bundle,fit);e=exposure[fitmask];y=fit.T0.to_numpy();score=np.sqrt(e)*(np.sqrt(mu)-y/e/np.sqrt(mu))/np.sqrt(e).sum();gradient=np.r_[np.asarray(x.T@score).ravel(),score.sum()]
                        check('GLM gradient '+variant+line+str(fold),abs(gradient).max()<=1e-4 and receipt['n_iter']<2000);gradients.append(float(abs(gradient).max()))
                    q=new[new.stress_id.eq(variant+'_'+mid)&new.line.eq(line)&new.fold.eq(fold)].set_index('row_id').loc[valid.row_id]
                    check('Native exponential replay '+variant+mid+line+str(fold),close(q.annual_rate,native(bundle,valid)) and close(q.prediction,exposure[~fitmask]*q.annual_rate) and close(q.conditional_nominal_2023,q.exposure*q.annual_rate))
    check('Actual estimate counters',counts=={'GLM':r['new_price_GLM_fits'],'price_constants':r['new_closed_form_constants'],'reuse':r['exact_native_reuses'],'mixture_frequency':r['new_mixture_frequency_constants'],'mixture_severity':r['new_mixture_weighted_severity_means']})
    check('Price cumulative counters',r['cumulative_price_base_fits']==135+counts['GLM'] and r['cumulative_closed_form_constants']==195+counts['price_constants'] and r['new_reporting_curve_fits']==r['new_auxiliary_credibility_fits']==0)
    segments=c.read(run/'diagnostics/segments.json');parts={sid:q.sort_values(KEY).reset_index(drop=True) for sid,q in new.groupby('stress_id')}
    for sid,q in parts.items():
        base=old[old.model_id.eq(q.model_id.iloc[0])].sort_values(KEY).reset_index(drop=True);point=next(z for z in r['summary'] if z['stress_id']==sid)
        check('Same2023keys/T0 '+sid,q[KEY].equals(base[KEY]) and q.T0.equals(base.T0));check('Global metric '+sid,close(point['D2'],c.d2_tweedie_score(q.T0,q.prediction,power=1.5)) and close(q.unit_deviance,c.dev(q.T0,q.prediction)))
        for record in [z for z in segments if z['stress_id']==sid]:
            labels={'line':q.line.astype(str),'fold':q.fold.astype(str),'business':pd.Series(np.where(q.x_new_business.eq(1),'new_business','renewal')),'line_business':q.line.astype(str)+'_'+np.where(q.x_new_business.eq(1),'new_business','renewal')}[record['dimension']];cell=q[labels.eq(record['label'])]
            check('Segment '+sid+record['dimension']+record['label'],close(record['D2'],c.d2_tweedie_score(cell.T0,cell.prediction,power=1.5)) and close(record['conditional_nominal_2023'],(cell.exposure*cell.annual_rate).sum()))
    for mid in MIDS:parts[mid]=old[old.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True)
    ids=[variant+'_'+mid for variant in VARIANTS for mid in MIDS]+MIDS;first=parts[ids[0]];code,groups=pd.factorize(first.group_id,sort=True);g=len(groups);n=np.bincount(code,minlength=g);y=np.bincount(code,weights=first.T0,minlength=g);root=np.bincount(code,weights=np.sqrt(first.T0),minlength=g)
    gl=np.column_stack([np.bincount(code,weights=c.dev(parts[sid].T0,parts[sid].prediction),minlength=g) for sid in ids]);pairs=[(ids.index(variant+'_'+MIDS[a]),ids.index(variant+'_'+MIDS[b])) for variant in VARIANTS for a,b in [(1,0),(2,0),(2,1)]]
    for mid in MIDS:pairs.extend([(ids.index('MIXF_'+mid),ids.index(mid)),(ids.index('MIXFS_'+mid),ids.index('MIXF_'+mid))])
    distributions={pair:[] for pair in pairs};rng=np.random.default_rng(2026102302);digest=hashlib.sha256()
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        for start in range(0,2000,16):
            draw=rng.integers(0,g,size=(16,g),dtype=np.int64);digest.update(draw.tobytes());multiplicity=np.stack([np.bincount(x,minlength=g) for x in draw]);loss=multiplicity@gl;den=8*(np.sqrt((multiplicity@n)*(multiplicity@y))-multiplicity@root)
            for a,b in pairs:distributions[(a,b)].extend(((loss[:,b]-loss[:,a])/den).tolist())
    pr=c.read(run/'diagnostics/pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_12_pairs.parquet').to_pandas();check('Exactly12newpairs/commonstream',len(boot)==24000 and len(pr['pairs'])==12 and digest.hexdigest()==pr['draws_sha256'])
    for a,b in pairs:
        record=next(z for z in pr['pairs'] if z['candidate']==ids[a] and z['reference']==ids[b]);dist=np.asarray(distributions[(a,b)]);stored=boot[boot.candidate.eq(ids[a])&boot.reference.eq(ids[b])].sort_values('replicate').delta_D2;adv=gl[:,b]-gl[:,a];keep=np.ones(g,bool);keep[np.argsort(-adv,kind='stable')[:31]]=False
        den=8*(np.sqrt(n.sum()*y.sum())-root.sum());trimden=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum());check('Bootstrap/CI/influence '+ids[a]+ids[b],close(stored,dist) and close([record['delta_D2'],record['exploratory_lower95'],record['exploratory_upper95'],record['delta_after_removal']],[adv.sum()/den,*np.percentile(dist,[2.5,97.5]),adv[keep].sum()/trimden]))
    selector=c.read(REPO/'registro/semana2_seleccion_actual.json');check('2024/test closed',not (ROOT/selector['ledger_workspace_relative']).exists() and r['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and r['test_predictions']==0)
    check('No fits during replay',ATTEMPTS==0);check('B00/no promotion',r['reference']=='W2-B00' and not r['promotion'])
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checker_sha256':c.sha(Path(__file__)),'passed':sum(z['pass'] for z in checks),'failed':sum(not z['pass'] for z in checks),'checks':checks,
      'actual_counters':counts,'max_GLM_score':max(gradients,default=0.),'professional_independent_validation':False,'scope':'New business mixtures/price consumers and12new contrasts only, no prior suite repetition'}
    (run/'verifications').mkdir(exist_ok=True);path=run/'verifications'/('mix_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json');path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(path),'passed':result['passed'],'failed':result['failed'],'failures':[z for z in checks if not z['pass']]}));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
