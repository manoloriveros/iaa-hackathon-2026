"""Reconstrucción independiente de C0, reservas y precio, sin importar productor."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,re,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('c0_reserve_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;MIDS=['W2-B00','W2-B12','W2-B14'];SCENARIOS=['R075','R125','L1'];ATTEMPTS=0
def forbidden(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('Fit bloqueado en comprobador')
def native(b,f):
    assert f.year.eq(2023).all() and not f.is_test.any()
    if b['family']=='constant_line_rate':return np.full(len(f),b['rate'])
    if b['family']=='business_constant':return np.asarray([b['rates'][int(x)] for x in f.x_new_business])
    assert b['family']=='TweedieRegressor'
    return np.exp(np.asarray(b['transformer'].transform(f[b['columns']])@b['estimator'].coef_).ravel()+b['estimator'].intercept_)
def distribution(g,b=1.):
    d=g.delay.to_numpy();age=g.age.to_numpy();net=g.T0_cents.to_numpy()/100+(b-1)*g.reserve_cents.to_numpy()/100
    support,events=np.unique(d,return_counts=True);risk=((d[:,None]<=support)&(age[:,None]>=support)).sum(axis=0)
    # Product form of the reverse product-limit CDF, rather than producer recursion.
    terms=1-events/risk;cdf=np.asarray([np.prod(terms[j+1:]) for j in range(len(support))]);mass=np.diff(np.r_[0.,cdf])
    mean=np.asarray([net[d==x].mean() for x in support]);costmass=mass*mean;total=float(costmass.sum());costmass/=total
    return support,cdf,mass,costmass,total
def completion(periods,support,mass):
    a=(pd.Timestamp('2024-12-31')-pd.to_datetime(periods.period_start)).dt.days.to_numpy();z=(pd.Timestamp('2024-12-31')-pd.to_datetime(periods.period_end)).dt.days.to_numpy();days=a-z+1
    # Direct count of covered days whose follow-up can contain each delay.
    result=np.zeros(len(periods))
    for start in range(0,len(support),32):
        ds=support[start:start+32];eligible=np.clip(a[:,None]-ds[None,:]+1,0,days[:,None]);result+=(eligible/days[:,None])@mass[start:start+32]
    return result
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=c.read(run/'report.json');p=c.read(run/'plan_snapshot.json');source=ROOT/p['input_run'];linkroot=ROOT/p['observation_run'];checks=[];gradients=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    close=lambda a,b:np.allclose(a,b,rtol=4e-9,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in p['frozen_sources']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Plan/code exact',c.sha(run/'code_snapshot.py')==r['code_sha256']==p['code_sha256'] and c.sha(run/'plan_snapshot.json')==r['plan_sha256'])
    h=re.search(r'^## Codex \| COD-S2-20261024-025 \| ([^|]+) \|',(run/'forum_before_fit.md').read_text(encoding='utf-8'),re.M)
    check('Recipe before execution',h is not None and datetime.fromisoformat(h[1].strip())<datetime.fromisoformat(r['started_utc']))
    check('Main catalog unchanged',c.sha(ROOT/p['main_model_index'])==p['main_model_index_sha256'])
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    claims=pq.read_table(run/'inputs_2023/claims_2023.parquet').to_pandas();new=pq.read_table(run/'mechanism_oof_2023.parquet').to_pandas();old=pq.read_table(run/'base_oof_2023.parquet').to_pandas()
    check('2023 claims canonical and unique',claims.year.eq(2023).all() and claims.included_in_T0.all() and claims.claim_id.is_unique)
    rawclaims=pq.read_table(ROOT/p['claim_audit'],filters=[('row_id','in',claims.row_id.unique().tolist())]).to_pandas();rawclaims=rawclaims[rawclaims.included_in_T0].sort_values('claim_id').reset_index(drop=True);saved=claims.sort_values('claim_id').reset_index(drop=True)
    check('Canonical claim cents/dates unchanged',rawclaims[['claim_id','T0_cents','reserve_cents','loss_date','report_date']].equals(saved[['claim_id','T0_cents','reserve_cents','loss_date','report_date']]))
    check('Nine full2023unique OOF',len(new)==9*50094 and new.year.eq(2023).all() and not new.is_test.any() and not new.duplicated(['stress_id',*KEY]).any())
    canonical=claims.groupby(KEY,as_index=False).agg(T0_cents=('T0_cents','sum'),reserve_cents=('reserve_cents','sum'));counts={'GLM':0,'constants':0,'reuse':0,'reporting':0}
    for fold in range(5):
        for line in ['motor','buildings','contents']:
            frame=pq.read_table(source/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas();fitmask=frame.fold.ne(fold);fit=frame[fitmask];valid=frame[~fitmask]
            check('2023 disjoint '+line+str(fold),frame.year.eq(2023).all() and not frame.is_test.any() and all(not set(fit[k])&set(valid[k]) for k in ['group_id','customer_id','address_id']))
            dates=pq.read_table(source/f'inputs_2023/raw_{line}.parquet',columns=['row_id','period_start','period_end']).to_pandas();periods=frame[['row_id']].merge(dates,on='row_id',validate='one_to_one');assert periods.row_id.equals(frame.row_id)
            fitted=claims[claims.line.eq(line)&claims.fold.ne(fold)];late=fitted[fitted.delay.gt(365)&fitted.T0_cents.gt(0)]
            scores=late.groupby('group_id').T0_cents.sum();selected=sorted(scores.index,key=lambda k:(-int(scores.loc[k]),str(k)))[0] if len(scores) else None
            saved_late=c.read(run/f'late_reporting/{line}_fold{fold}.json');rec=saved_late['record'];check('Training-only late group '+line+str(fold),rec['removed_group']==selected)
            if selected is not None:
                reduced=fitted[fitted.group_id.ne(selected)];remaining=fitmask&frame.group_id.ne(selected);counts['reporting']+=len(saved_late['models'])
                check('Reporting population exclusion '+line+str(fold),rec['remaining_reporting_periods']==int(remaining.sum()) and rec['fit_claims_after']==len(reduced) and rec['reporting_fit_ids_sha256']==hashlib.sha256('\n'.join(sorted(reduced.claim_id)).encode()).hexdigest())
                late_curves={};late_rates={}
                for peril,g in reduced.groupby('peril'):
                    model=saved_late['models'][peril];support,cdf,mass,costmass,total=distribution(g)
                    check('Reverse truncation and costCDF '+line+str(fold)+peril,np.array_equal(support,model['delay_days']) and close(cdf,model['count_cdf']) and close(np.cumsum(costmass),model['cost_cdf']['1.0']) and close(total,model['mean_net_mark']['1.0']))
                    qn=completion(periods,support,mass);qc=completion(periods,support,costmass);den=float(np.sum(frame.loc[remaining,'exposure']*qn[remaining]));late_rates[peril]=len(g)/den*total;late_curves[peril]=qc
                rate_total=sum(late_rates.values());expectedshares={k:v/rate_total for k,v in late_rates.items()};late_e=frame.exposure.to_numpy()*sum(expectedshares[k]*late_curves[k] for k in expectedshares)
                check('Late costshares '+line+str(fold),set(expectedshares)==set(rec['shares']) and all(close(expectedshares[k],rec['shares'][k]) for k in expectedshares))
            else:late_e=frame['e_cost_mix_1.0'].to_numpy()
            source_models=c.read(linkroot/f'exclude_fold{fold}/reporting_models.json');canonical_period=frame[KEY].merge(canonical,on=KEY,how='left',validate='one_to_one').fillna({'T0_cents':0,'reserve_cents':0})
            check('Canonical periodT0/reserve '+line+str(fold),close(frame.T0,canonical_period.T0_cents/100) and close(frame.reserve,canonical_period.reserve_cents/100))
            expected_variants={}
            for scenario,b in [('R075',.75),('R125',1.25)]:
                shares=c.read(linkroot/f'exclude_fold{fold}/peril_cost_shares_{line}.json')[str(b)];curves={}
                for peril,g in fitted.groupby('peril'):
                    model=source_models[line+'|'+peril];d=g.delay.to_numpy();net=g.T0_cents.to_numpy()/100+(b-1)*g.reserve_cents.to_numpy()/100;support=np.asarray(model['delay_days']);mass=np.diff(np.r_[0.,model['count_cdf']]);costmass=mass*np.asarray([net[d==x].mean() for x in support]);costmass/=costmass.sum()
                    check('Matched reserve costmark '+scenario+line+str(fold)+peril,close(np.cumsum(costmass),model['cost_cdf'][str(b)]));curves[peril]=completion(periods,support,costmass)
                e=frame.exposure.to_numpy()*sum(shares[k]*curves[k] for k in shares);y=(canonical_period.T0_cents+(b-1)*canonical_period.reserve_cents)/100;expected_variants[scenario]=(e,y)
            expected_variants['L1']=(late_e,frame.T0.to_numpy())
            for scenario,(e,y) in expected_variants.items():
                inp=pq.read_table(run/f'inputs_2023/{scenario}_{line}_fold{fold}.parquet').to_pandas();check('Complete target/link '+scenario+line+str(fold),close(inp.T_s,y) and close(inp.effective_exposure,e) and inp[KEY].equals(frame[KEY]))
                for mid in MIDS:
                    path=run/'models'/f'{scenario}_{mid}_{line}_fold{fold}/bundle.joblib';bundle=c.joblib.load(path);receipt=c.read(path.parent/'receipt.json');target=y[fitmask];et=e[fitmask]
                    check('All original price fit rows '+scenario+mid+line+str(fold),receipt['train_rows']==len(fit) and receipt['validation_rows']==len(valid))
                    if receipt['exact_reuse']:
                        counts['reuse']+=1;check('Exact reuse '+scenario+mid+line+str(fold),np.array_equal(inp.T_s,frame.T0) and close(inp.effective_exposure,frame['e_cost_mix_1.0']) and c.sha(path)==receipt['source_sha256'])
                    elif mid!='W2-B14':
                        from scipy.optimize import minimize_scalar
                        for business in ([None] if mid=='W2-B00' else [0,1]):
                            counts['constants']+=1;subset=np.ones(len(fit),bool) if business is None else fit.x_new_business.eq(business).to_numpy();rate=bundle['rate'] if business is None else bundle['rates'][business]
                            result=minimize_scalar(lambda eta:float(c.dev(np.asarray(target)[subset],et[subset]*np.exp(eta)).sum()),bounds=(np.log(rate)-1,np.log(rate)+1),method='bounded',options={'xatol':1e-10})
                            check('Scalar optimum '+scenario+mid+line+str(fold)+str(business),result.success and abs(result.x-np.log(rate))<2e-6)
                    else:
                        counts['GLM']+=1;tr=bundle['transformer'];numeric=tr.transformers_[0][2];params=bundle['estimator'].get_params();original=c.joblib.load(ROOT/p['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib')
                        check('Exact GLM params/imputer '+scenario+line+str(fold),params==original['estimator'].get_params() and close(tr.named_transformers_['numeric'].named_steps['median'].statistics_,fit[numeric].median().fillna(0)))
                        x=tr.transform(fit[bundle['columns']]);mu=native(bundle,fit);g=np.sqrt(et)*(np.sqrt(mu)-np.asarray(target)/et/np.sqrt(mu))/np.sqrt(et).sum();gradient=np.r_[np.asarray(x.T@g).ravel(),g.sum()]
                        check('GLM convergence score '+scenario+line+str(fold),abs(gradient).max()<=1e-4 and receipt['n_iter']<2000);gradients.append(float(abs(gradient).max()))
                    q=new[new.stress_id.eq(scenario+'_'+mid)&new.line.eq(line)&new.fold.eq(fold)].set_index('row_id').loc[valid.row_id]
                    check('Native exp replay '+scenario+mid+line+str(fold),close(q.annual_rate,native(bundle,valid)) and close(q.T_s,np.asarray(y)[~fitmask]) and close(q.prediction,np.asarray(e)[~fitmask]*q.annual_rate) and close(q.conditional_nominal_2023,q.exposure*q.annual_rate))
    check('Actual counters',counts=={'GLM':r['new_price_GLM_fits'],'constants':r['new_closed_form_constants'],'reuse':r['exact_reuses'],'reporting':r['new_reporting_peril_fits']} and r['cumulative_price_base_fits']==100+counts['GLM'] and r['cumulative_closed_form_constants']==90+counts['constants'])
    segments=c.read(run/'diagnostics/segments.json');parts={sid:q.sort_values(KEY).reset_index(drop=True) for sid,q in new.groupby('stress_id')}
    for sid,q in parts.items():
        base=old[old.model_id.eq(q.model_id.iloc[0])].sort_values(KEY).reset_index(drop=True);point=next(x for x in r['summary'] if x['stress_id']==sid)
        check('Same complete keys '+sid,q[KEY].equals(base[KEY]));check('Global metric '+sid,close(point['D2'],c.d2_tweedie_score(q.T_s,q.prediction,power=1.5)) and close(q.unit_deviance,c.dev(q.T_s,q.prediction)))
        for record in [z for z in segments if z['stress_id']==sid]:
            labels={'line':q.line.astype(str),'fold':q.fold.astype(str),'business':pd.Series(np.where(q.x_new_business.eq(1),'new_business','renewal')),'line_business':q.line.astype(str)+'_'+np.where(q.x_new_business.eq(1),'new_business','renewal')}[record['dimension']];cell=q[labels.eq(record['label'])]
            check('Segment '+sid+record['dimension']+record['label'],close(record['D2'],c.d2_tweedie_score(cell.T_s,cell.prediction,power=1.5)) and close(record['conditional_nominal_2023'],(cell.exposure*cell.annual_rate).sum()))
    # Reconstruct just12 newly declared contrasts, with each scenario own target/null.
    for mid in MIDS:
        q=old[old.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True).copy();q['T_s']=q.T0;parts[mid]=q
    ids=[s+'_'+m for s in SCENARIOS for m in MIDS]+MIDS;first=parts[ids[0]];codes,groups=pd.factorize(first.group_id,sort=True);g=len(groups);n=np.bincount(codes,minlength=g);gl=np.column_stack([np.bincount(codes,weights=c.dev(parts[sid].T_s,parts[sid].prediction),minlength=g) for sid in ids])
    target={s:(np.bincount(codes,weights=parts[s+'_'+MIDS[0]].T_s,minlength=g),np.bincount(codes,weights=np.sqrt(parts[s+'_'+MIDS[0]].T_s),minlength=g)) for s in SCENARIOS}
    pairlist=[(ids.index(s+'_'+MIDS[a]),ids.index(s+'_'+MIDS[b]),s) for s in SCENARIOS for a,b in [(1,0),(2,0),(2,1)]]+[(ids.index('L1_'+m),ids.index(m),'L1') for m in MIDS]
    rng=np.random.default_rng(2026102302);digest=hashlib.sha256();distributions={pair:[] for pair in pairlist}
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        for start in range(0,2000,16):
            draw=rng.integers(0,g,size=(16,g),dtype=np.int64);digest.update(draw.tobytes());w=np.stack([np.bincount(v,minlength=g) for v in draw]);loss=w@gl;den={s:8*(np.sqrt((w@n)*(w@y))-w@root) for s,(y,root) in target.items()}
            for a,b,scenario in pairlist:distributions[(a,b,scenario)].extend(((loss[:,b]-loss[:,a])/den[scenario]).tolist())
    pr=c.read(run/'diagnostics/pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_12_pairs.parquet').to_pandas();check('Exactly12newpairs/commonstream',len(boot)==24000 and len(pr['pairs'])==12 and digest.hexdigest()==pr['draws_sha256'])
    for a,b,scenario in pairlist:
        check('Same outcome per contrast '+ids[a]+ids[b],np.array_equal(parts[ids[a]].T_s,parts[ids[b]].T_s))
        record=next(x for x in pr['pairs'] if x['candidate']==ids[a] and x['reference']==ids[b]);dist=np.asarray(distributions[(a,b,scenario)]);stored=boot[boot.candidate.eq(ids[a])&boot.reference.eq(ids[b])].sort_values('replicate').delta_D2;y,root=target[scenario];den=8*(np.sqrt(n.sum()*y.sum())-root.sum());adv=gl[:,b]-gl[:,a];keep=np.ones(g,bool);keep[np.argsort(-adv,kind='stable')[:31]]=False;td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum())
        check('Bootstrap/CI/influence '+ids[a]+ids[b],close(stored,dist) and close([record['delta_D2'],record['exploratory_lower95'],record['exploratory_upper95'],record['delta_after_removal']],[adv.sum()/den,*np.percentile(dist,[2.5,97.5]),adv[keep].sum()/td]))
    selector=c.read(REPO/'registro/semana2_seleccion_actual.json');check('2024/test closed',not (ROOT/selector['ledger_workspace_relative']).exists() and r['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and r['test_predictions']==0)
    check('Replay nofit',ATTEMPTS==0);check('Reference/no promotion',r['reference']=='W2-B00' and not r['promotion'])
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checker_sha256':c.sha(Path(__file__)),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
      'max_GLM_score':max(gradients),'actual_counters':counts,'professional_independent_validation':False,'scope':'Changed reserve/late-report estimator and consumer only, no prior suite repeat'}
    (run/'verifications').mkdir(exist_ok=True);path=run/'verifications'/('c0_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json');path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(path),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
