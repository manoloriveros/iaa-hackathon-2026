"""Oráculo separado: curvas por peril, escala GLM y nuevos contrastes de cola."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,re,hashlib,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('tail_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;ATTEMPTS=0
def forbidden(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('Fit prohibido en replay')
def native_rate(b,f):
    assert f.year.eq(2023).all() and not f.is_test.any()
    if b['family']=='constant_line_rate':return np.full(len(f),b['rate'])
    if b['family']=='business_constant':return np.asarray([b['rates'][int(x)] for x in f.x_new_business])
    assert b['family']=='TweedieRegressor'
    return np.exp(np.asarray(b['transformer'].transform(f[b['columns']])@b['estimator'].coef_).ravel()+b['estimator'].intercept_)
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=c.read(run/'report.json');p=c.read(run/'plan_amendment_snapshot.json');firstplan=c.read(run/'plan_snapshot.json')
    source=ROOT/p['input_run'];link=ROOT/p['observation_run'];checks=[];details=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    close=lambda a,b:np.allclose(a,b,rtol=3e-9,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in p['frozen_sources']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    for it in c.read(run/'attempt_before_receipt_fix_manifest.json')['files']:check('Failed-attempt original preserved '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Original snapshots remain',c.sha(run/'code_snapshot.py')==firstplan['code_sha256'] and c.sha(run/'plan_snapshot.json')==p['implementation_amendment']['original_plan_sha256'])
    check('Continuation snapshot',c.sha(run/'continuation_code_snapshot.py')==r['code_sha256']==p['code_sha256'] and c.sha(run/'plan_amendment_snapshot.json')==r['plan_sha256'])
    f=(run/'forum_before_resume.md').read_text(encoding='utf-8');h=re.search(r'^## Codex \| COD-S2-20261024-023 \| ([^|]+) \|',f,re.M)
    check('Correction registered before continuation',h is not None and datetime.fromisoformat(h[1].strip())<datetime.fromisoformat(r['started_utc']))
    h0=re.search(r'^## Codex \| COD-S2-20261024-022 \| ([^|]+) \|',(run/'forum_before_fit.md').read_text(encoding='utf-8'),re.M)
    check('Recipe before initial fit',h0 is not None and datetime.fromisoformat(h0[1].strip())<datetime.fromisoformat(r['first_attempt_started_utc']))
    check('No repeated cached constants',len(r['resumed_cached_constant_bundles'])==2 and r['constants_calculated_before_receipt_error']==3 and r['constants_calculated_in_continuation']==27 and r['new_GLM_before_error']==0)
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    old=pq.read_table(run/'base_oof_2023.parquet').to_pandas();new=pq.read_table(run/'stress_oof_2023.parquet').to_pandas();mids=['W2-B00','W2-B12','W2-B14'];orig={m:q.sort_values(KEY).reset_index(drop=True) for m,q in old.groupby('model_id')}
    check('Catalog main index unchanged',c.sha(ROOT/p['main_model_index'])==p['main_model_index_sha256']);check('Six complete2023stress grids',len(new)==6*50094 and new.year.eq(2023).all() and not new.is_test.any() and not new.duplicated(['stress_id',*KEY]).any())
    counts={'GLM':0,'constant_values':0,'exact_content':0}
    for fold in range(5):
        fitclaims=pq.read_table(link/f'exclude_fold{fold}/reporting_fit_claims.parquet').to_pandas()
        check('Reporting fit own2023fold '+str(fold),fitclaims.year.eq(2023).all() and fitclaims.fold.ne(fold).all())
        for line in ['motor','buildings','contents']:
            frame=pq.read_table(source/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas();fit=frame[frame.fold.ne(fold)].copy();valid=frame[frame.fold.eq(fold)].copy()
            check('2023 and disjoint '+line+str(fold),frame.year.eq(2023).all() and not frame.is_test.any() and all(not set(fit[k])&set(valid[k]) for k in ['group_id','customer_id','address_id']))
            shares=c.read(link/f'exclude_fold{fold}/peril_cost_shares_{line}.json')['1.0'];columns=KEY+['year','is_test','exposure','q_cost_mix_1.0','e_cost_mix_1.0','e_cost_mix_tail0.1']+['qC_1.0_'+k for k in shares]
            lf=pq.read_table(link/f'exclude_fold{fold}/observation_link_{line}.parquet',filters=[('year','=',2023),('is_test','=',False)],columns=columns).to_pandas().set_index('row_id').loc[frame.row_id].reset_index()
            ws=np.asarray(list(shares.values()));ts=np.asarray([.1 if k in ['bodily_injury','subsidence'] else 0. for k in shares]);curves=lf[['qC_1.0_'+k for k in shares]].to_numpy()
            z=float(np.sum(ws/(1-ts)));newweights=(ws/(1-ts))/z;qbase=curves@ws;qfixed=curves@(ws*(1-ts));qrenorm=(curves*(1-ts))@newweights
            check('Mixture normalized '+line+str(fold),close(ws.sum(),1.) and close(newweights.sum(),1.))
            check('Peril formula fixed and renormalized '+line+str(fold),close(lf.exposure*qbase,frame['e_cost_mix_1.0']) and close(lf.exposure*qfixed,frame['e_cost_mix_tail0.1']) and close(qrenorm,qbase/z))
            for mid in mids:
                native=c.joblib.load(ROOT/p['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib')
                fixedpath=run/'models'/f'T10F_{mid}_{line}_fold{fold}/bundle.joblib';b=c.joblib.load(fixedpath);receipt=c.read(fixedpath.parent/'receipt.json')
                if line=='contents':
                    counts['exact_content']+=1;check('Exact contents bundle '+mid+str(fold),c.sha(fixedpath)==c.sha(ROOT/p['base_model_runs'][mid]/'models'/f'{mid}_{line}_fold{fold}/bundle.joblib'))
                elif mid!='W2-B14':
                    nvalues=1 if mid=='W2-B00' else 2;counts['constant_values']+=nvalues
                    for business in ([None] if mid=='W2-B00' else [0,1]):
                        cell=fit if business is None else fit[fit.x_new_business.eq(business)];e=cell['e_cost_mix_tail0.1'].to_numpy();y=cell.T0.to_numpy();rate=b['rate'] if business is None else b['rates'][business]
                        # Solve in log-rate through scalar minimization of total-unit deviance.
                        from scipy.optimize import minimize_scalar
                        opt=minimize_scalar(lambda eta:float(c.dev(y,e*np.exp(eta)).sum()),bounds=(np.log(rate)-1,np.log(rate)+1),method='bounded',options={'xatol':1e-10})
                        score=np.sum(y/np.sqrt(e*rate)-np.sqrt(e*rate))
                        check('Independent scalar optimum '+mid+line+str(fold)+str(business),opt.success and abs(np.log(rate)-opt.x)<2e-6 and abs(score)<1e-6)
                else:
                    counts['GLM']+=1;check('GLM params '+line+str(fold),b['estimator'].get_params()==native['estimator'].get_params() and b['estimator'].alpha==0 and b['estimator'].power==1.5)
                    tr=b['transformer'];numeric=tr.transformers_[0][2];expected=fit[numeric].median().fillna(0).to_numpy();check('Fit-only imputation '+line+str(fold),close(tr.named_transformers_['numeric'].named_steps['median'].statistics_,expected))
                    x=tr.transform(fit[b['columns']]);mu=native_rate(b,fit);e=fit['e_cost_mix_tail0.1'].to_numpy();y=fit.T0.to_numpy();score=np.sqrt(e)*(np.sqrt(mu)-y/e/np.sqrt(mu))/np.sqrt(e).sum();gradient=np.r_[np.asarray(x.T@score).ravel(),score.sum()]
                    check('GLM convergence score '+line+str(fold),np.abs(gradient).max()<=1e-4 and receipt['n_iter']<2000);details.append({'line':line,'fold':fold,'mean_score_max':float(abs(gradient).max())})
                q=new[new.stress_id.eq('T10F_'+mid)&new.line.eq(line)&new.fold.eq(fold)].set_index('row_id').loc[valid.row_id]
                check('Fixed exp replay/exposure '+mid+line+str(fold),close(q.annual_rate,native_rate(b,valid)) and close(q.effective_exposure,valid['e_cost_mix_tail0.1']))
                br=c.joblib.load(run/'models'/f'T10R_{mid}_{line}_fold{fold}/bundle.joblib');qr=new[new.stress_id.eq('T10R_'+mid)&new.line.eq(line)&new.fold.eq(fold)].set_index('row_id').loc[valid.row_id]
                rates=native_rate(native,valid);check('Renorm scale replay '+mid+line+str(fold),close(br['scale'],z) and close(qr.annual_rate,rates*z) and close(qr.effective_exposure,valid['e_cost_mix_1.0']/z))
                check('Renorm observed identity '+mid+line+str(fold),close(qr.prediction,valid['e_cost_mix_1.0']*rates) and close(qr.conditional_nominal_2023,valid.exposure*rates*z))
    check('Fit counters',counts=={'GLM':10,'constant_values':30,'exact_content':15} and r['new_price_GLM_fits']==10 and r['new_closed_form_constants']==30)
    seg=c.read(run/'diagnostics/segments.json')
    for sid,q in new.groupby('stress_id'):
        q=q.sort_values(KEY).reset_index(drop=True);base=orig[q.parent_model.iloc[0]];point=next(x for x in r['summary'] if x['stress_id']==sid)
        check('SameT0/keys '+sid,q[KEY].equals(base[KEY]) and q.T0.equals(base.T0));check('Metric/formula '+sid,close(q.unit_deviance,c.dev(q.T0,q.prediction)) and close(point['D2'],c.d2_tweedie_score(q.T0,q.prediction,power=1.5)))
        check('Nominal arithmetic '+sid,close(point['conditional_nominal_2023'],(q.exposure*q.annual_rate).sum()) and close(q.prediction,q.effective_exposure*q.annual_rate))
        if sid.startswith('T10R'):check('Observed identity allrows '+sid,close(q.prediction,base.prediction))
        for record in [z for z in seg if z['stress_id']==sid]:
            labels={'line':q.line.astype(str),'fold':q.fold.astype(str),'business':pd.Series(np.where(q.x_new_business.eq(1),'new_business','renewal')),
              'line_business':q.line.astype(str)+'_'+np.where(q.x_new_business.eq(1),'new_business','renewal')}[record['dimension']];cell=q[labels.eq(record['label'])]
            check('Segment '+sid+record['dimension']+record['label'],close(record['D2'],c.d2_tweedie_score(cell.T0,cell.prediction,power=1.5)) and close(record['conditional_nominal_2023'],(cell.exposure*cell.annual_rate).sum()))
    # Independent multiplicity bootstrap: six newly declared pairs only.
    ids=mids+['T10F_'+m for m in mids];parts={m:orig[m] for m in mids}
    parts.update({m:q.sort_values(KEY).reset_index(drop=True) for m,q in new[new.stress_id.str.startswith('T10F')].groupby('stress_id')})
    base=parts[mids[0]];code,groups=pd.factorize(base.group_id,sort=True);g=len(groups);n=np.bincount(code,minlength=g);y=np.bincount(code,weights=base.T0,minlength=g);root=np.bincount(code,weights=np.sqrt(base.T0),minlength=g)
    gl=np.column_stack([np.bincount(code,weights=c.dev(parts[m].T0,parts[m].prediction),minlength=g) for m in ids]);pairs=[(3,0),(4,1),(5,2),(4,3),(5,3),(5,4)];dists={pair:[] for pair in pairs};rng=np.random.default_rng(2026102302);digest=hashlib.sha256()
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        for start in range(0,2000,16):
            draw=rng.integers(0,g,size=(16,g),dtype=np.int64);digest.update(draw.tobytes());w=np.stack([np.bincount(v,minlength=g) for v in draw]);den=8*(np.sqrt((w@n)*(w@y))-w@root);loss=w@gl
            for a,b in pairs:dists[(a,b)].extend(((loss[:,b]-loss[:,a])/den).tolist())
    pr=c.read(run/'diagnostics/pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_6_pairs.parquet').to_pandas();check('Exactly6newpairs',len(boot)==12000 and len(pr['pairs'])==6 and digest.hexdigest()==pr['draws_sha256'])
    for a,b in pairs:
        point=next(x for x in pr['pairs'] if x['candidate']==ids[a] and x['reference']==ids[b]);dist=np.asarray(dists[(a,b)]);stored=boot[boot.candidate.eq(ids[a])&boot.reference.eq(ids[b])].sort_values('replicate').delta_D2
        adv=gl[:,b]-gl[:,a];keep=np.ones(g,bool);keep[np.argsort(-adv,kind='stable')[:31]]=False;den=8*(np.sqrt(n.sum()*y.sum())-root.sum());td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum())
        check('Bootstrap6 '+ids[a]+'/'+ids[b],close(stored,dist) and close([point['delta_D2'],point['exploratory_lower95'],point['exploratory_upper95'],point['delta_after_removal']],[adv.sum()/den,*np.percentile(dist,[2.5,97.5]),adv[keep].sum()/td]))
    selector=c.read(REPO/'registro/semana2_seleccion_actual.json');check('2024closed',not (ROOT/selector['ledger_workspace_relative']).exists() and r['test_predictions']==0 and r['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False})
    check('Replay nofit',ATTEMPTS==0);check('Reference retained',r['reference_retained']=='W2-B00' and not r['promotion'])
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checker_sha256':c.sha(Path(__file__)),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
      'new_GLM_gradients':details,'scope':'Changed tail mechanisms and consumers, no unchanged historical suite repeated','professional_independent_validation':False}
    (run/'verifications').mkdir(exist_ok=True);path=run/'verifications'/('cola_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json');path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(path),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
