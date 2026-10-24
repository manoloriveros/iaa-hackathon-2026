"""B19: comprobación separada con fit bloqueado, objetivo y dos parejas nuevas."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,math
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('dev8_oracle_base',REPO/'herramientas/verificar_desarrollo2023_semana2.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY

def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');p=c.read(run/'plan_snapshot.json');r=c.read(run/'report.json');checks=[];nested=[]
    def check(n,x,detail=None):checks.append({'name':n,'pass':bool(x),'detail':detail})
    def close(a,b,rtol=2e-10,atol=1e-8):return np.allclose(a,b,rtol=rtol,atol=atol,equal_nan=True)
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline]:
        cls.fit=c.forbid_fit
        if hasattr(cls,'fit_transform'):cls.fit_transform=c.forbid_fit
    for item in p['frozen_sources']:check('Source '+item['path'],c.sha(ROOT/item['path'])==item['sha256'])
    for item in c.read(run/'manifest.json')['files']:check('Artifact '+item['path'],c.sha(run/item['path'])==item['sha256'])
    check('Code/plan snapshots',c.sha(run/'code_snapshot.py')==p['code_sha256'] and c.sha(run/'plan_snapshot.json')==r['plan_sha256'])
    check('Only fifteen fits, no new constants/curves/aux',r['new_price_base_fits']==15 and r['new_closed_form_constants']==r['new_curve_fits']==r['new_auxiliary_fits']==0)
    check('Own scope2024testclosed',r['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'ledger_read':False,'confirmation_open':False} and r['test_predictions']==0)
    old=pq.read_table(ROOT/p['parent_oof']).to_pandas();new=pq.read_table(run/'new_oof_2023.parquet').to_pandas();all_oof=pq.read_table(run/'oof_2023.parquet').to_pandas()
    check('All old alternatives exact',all_oof[all_oof.model_id.ne('W2-B19')].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)))
    check('20catalog recipes retained',all_oof.model_id.nunique()==20 and len(all_oof)==20*50094 and not all_oof.duplicated(['model_id',*KEY]).any())
    parent=old[old.model_id.eq('W2-B14')].sort_values(KEY).reset_index(drop=True);new=new.sort_values(KEY).reset_index(drop=True)
    check('Full new2023 keys',len(new)==50094 and new.year.eq(2023).all() and new[KEY].equals(parent[KEY]) and new.group_id.nunique()==30869)
    for col in [x for x in parent if x not in ['model_id','annual_rate','prediction','unit_deviance']]:check('Frozen OOF field '+col,new[col].equals(parent[col]))
    check('ObservedC0 applied once',close(new.prediction,new.annual_rate*new['e_cost_mix_1.0'],rtol=0,atol=0))
    check('New unit deviance general formula',close(new.unit_deviance,c.dev(new.T0,new.prediction)))
    for row in r['summary']:
        f=all_oof[all_oof.model_id.eq(row['model_id'])]
        check('GlobalD2 sklearn '+row['model_id'],close(row['D2'],c.d2_tweedie_score(f.T0,f.prediction,power=1.5)))
        check('Global totals '+row['model_id'],close([row['observed_total'],row['predicted_total'],row['conditional_nominal_2023']],[f.T0.sum(),f.prediction.sum(),(f.exposure*f.annual_rate).sum()]))
    data={};coverage=[];base=ROOT/p['input_run'];trainval=c.read(run/'diagnostics/train_validation.json')
    for line in ['motor','buildings','contents']:
        block=p['recipe']['features_by_line'][line];field='x_cover_type' if line=='motor' else 'x_accidental_damage_cover'
        for fold in range(5):
            label=line+str(fold);frame=pq.read_table(run/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas();original=pq.read_table(base/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas()
            check('Full original input exact '+label,frame.equals(original));check('Only2023input '+label,frame.year.eq(2023).all() and not frame.is_test.any())
            fit=frame[frame.fold.ne(fold)];valid=frame[frame.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            check('Disjoint graph '+label,all(set(fit[col]).isdisjoint(valid[col]) for col in ['group_id','customer_id','address_id']))
            roles=pq.read_table(run/f'fit_rows/{line}_fold{fold}.parquet').to_pandas();check('Saved row roles '+label,roles[KEY].equals(frame[KEY]) and np.array_equal(roles.role,np.where(frame.fold.eq(fold),'validation','fit')))
            node=run/'models'/f'W2-B19_{line}_fold{fold}';bundle=c.joblib.load(node/'bundle.joblib');receipt=c.read(node/'receipt.json');params=bundle['estimator'].get_params()
            parentbundle=c.joblib.load(base/f'models/W2-B14_{line}_fold{fold}/bundle.joblib')
            check('Exactlyparent6pluscoverage '+label,len(bundle['columns'])==7 and set(bundle['columns'])==set(parentbundle['columns'])|{field} and bundle['columns']==block['all'])
            check('Frozen hyperparameters '+label,all(params.get(k)==v for k,v in p['recipe']['params'].items()) and params['alpha']==0.)
            check('Convergence evidence '+label,receipt['n_iter']<2000 and receipt['max_abs_score_gradient']<=1e-4 and not any(x['category']=='ConvergenceWarning' for x in receipt['warnings']))
            transformer=bundle['transformer'];num=transformer.named_transformers_['numeric'];enc=transformer.named_transformers_['categorical']
            raw=fit[block['numeric']].to_numpy(float);med=np.array([np.nanmedian(raw[:,j]) if np.isfinite(raw[:,j]).any() else 0. for j in range(raw.shape[1])]);filled=np.where(np.isnan(raw),med,raw)
            check('Training medians '+label,close(num['median'].statistics_,med));check('Training scale mean/variance '+label,close(num['scale'].mean_,filled.mean(axis=0)) and close(num['scale'].var_,filled.var(axis=0)))
            check('Training OHE categories '+label,all(np.array_equal(enc.categories_[j],np.sort(fit[col].unique())) for j,col in enumerate(block['categorical'])))
            check('OHE frozen config '+label,enc.drop=='first' and enc.min_frequency==50 and enc.max_categories==40 and enc.handle_unknown=='ignore')
            for j,col in enumerate(block['categorical']):
                counts=fit[col].value_counts();expected=np.array([x for x in enc.categories_[j] if counts[x]<50]);actual=enc.infrequent_categories_[j]
                check('Rarecategory support '+label+col,(actual is None and len(expected)==0) or (actual is not None and np.array_equal(actual,expected)))
            part=new[new.line.eq(line)&new.fold.eq(fold)].reset_index(drop=True)
            with c.threadpool_limits(limits=2):
                replay=c.predict(bundle,valid);parentrate=c.predict(parentbundle,valid);fitrate=c.predict(bundle,fit);parentfit=c.predict(parentbundle,fit)
            check('Replay with allfit methods blocked '+label,np.array_equal(replay,part.annual_rate.to_numpy()))
            bp=parent[parent.line.eq(line)&parent.fold.eq(fold)].reset_index(drop=True);check('Parent replay exact '+label,np.array_equal(parentrate,bp.annual_rate.to_numpy()))
            # Numeric values are prepared independently; actual low-cardinality categories use literal indicator columns.
            matrix_num=(np.where(np.isnan(valid[block['numeric']].to_numpy(float)),med,valid[block['numeric']].to_numpy(float))-num['scale'].mean_)/num['scale'].scale_
            if all(x is None for x in enc.infrequent_categories_):
                indicators=[]
                for j,col in enumerate(block['categorical']):
                    for k,level in enumerate(enc.categories_[j]):
                        if k!=enc.drop_idx_[j]:indicators.append(valid[col].eq(level).to_numpy(float))
                matrix_cat=np.column_stack(indicators) if indicators else np.empty((len(valid),0))
            else:matrix_cat=enc.transform(valid[block['categorical']]).toarray()
            matrix=np.column_stack([matrix_num,matrix_cat]);manual=np.exp(matrix@bundle['estimator'].coef_+bundle['estimator'].intercept_)
            check('Manualexp numeric/indicator replay '+label,close(manual,replay,rtol=2e-12,atol=1e-8))
            with c.threadpool_limits(limits=2):x=transformer.transform(fit[block['all']])
            y=fit.T0.to_numpy()/fit['e_cost_mix_1.0'].to_numpy();w=np.sqrt(fit['e_cost_mix_1.0'].to_numpy());g=w*(fitrate-y)/np.sqrt(fitrate)/w.sum();score=np.r_[np.asarray(x.T@g).ravel(),g.sum()]
            check('NormalizedGLMscore '+label,np.abs(score).max()<=1e-4)
            check('Observedloss equalsweightedrateobjective '+label,close(c.dev(fit.T0,fit['e_cost_mix_1.0']*fitrate),np.sqrt(fit['e_cost_mix_1.0'])*c.dev(y,fitrate),rtol=2e-10,atol=2e-8))
            for role,ff,rr in [('fit',fit,fitrate),('validation',valid,replay)]:
                item=next(z for z in trainval if z['line']==line and z['fold']==fold and z['role']==role)
                check('Trainvalidation readout '+label+role,close(item['D2'],c.d2_tweedie_score(ff.T0,ff['e_cost_mix_1.0']*rr,power=1.5)))
            ndev=float(c.dev(fit.T0,fit['e_cost_mix_1.0']*fitrate).sum());pdev=float(c.dev(fit.T0,fit['e_cost_mix_1.0']*parentfit).sum())
            nested.append({'line':line,'fold':fold,'B19_fit_deviance':ndev,'B14_fit_deviance':pdev,'B19_minus_B14_fit_deviance':ndev-pdev,
                'B14_fit_D2':float(c.d2_tweedie_score(fit.T0,fit['e_cost_mix_1.0']*parentfit,power=1.5))})
            if fold==0:
                cov=frame[KEY+[field]].copy();cov['coverage']=cov[field].astype(str) if line=='motor' else np.where(cov[field].eq(1),'AD_yes','AD_no');coverage.append(cov[KEY+['coverage']])
    meta=pd.concat(coverage,ignore_index=True)
    for item in c.read(run/'diagnostics/segments.json'):
        f=all_oof[all_oof.model_id.eq(item['model_id'])].merge(meta,on=KEY,validate='one_to_one');dim=item['dimension']
        labels={'line':f.line.astype(str),'fold':f.fold.astype(str),'business':np.where(f.x_new_business.eq(1),'new_business','renewal'),
            'line_business':f.line.astype(str)+'_'+np.where(f.x_new_business.eq(1),'new_business','renewal'),'line_coverage':f.line.astype(str)+'_'+f.coverage,
            'line_business_coverage':f.line.astype(str)+'_'+np.where(f.x_new_business.eq(1),'new_business','renewal')+'_'+f.coverage}[dim]
        f=f[np.asarray(labels)==item['label']]
        check('Segment '+item['model_id']+dim+item['label'],len(f)==item['rows'] and close(item['D2'],c.d2_tweedie_score(f.T0,f.prediction,power=1.5)) and close(item['predicted_total'],f.prediction.sum()))
    # Two fresh pairs only; multiplicity matrix replaces indexed repeated sums.
    ids=['W2-B19','W2-B14','W2-B00'];ordered={mid:all_oof[all_oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True) for mid in ids}
    first=ordered[ids[0]];groups,codes=np.unique(first.group_id,return_inverse=True);G=len(groups);n=np.bincount(codes,minlength=G);sy=np.bincount(codes,weights=first.T0,minlength=G);sr=np.bincount(codes,weights=np.sqrt(first.T0),minlength=G)
    losses=np.column_stack([np.bincount(codes,weights=c.dev(ordered[mid].T0,ordered[mid].prediction),minlength=G) for mid in ids]);config=p['bootstrap'];rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();values={ref:[] for ref in ids[1:]}
    for start in range(0,config['replicates'],32):
        draw=rng.integers(0,G,size=(min(32,config['replicates']-start),G),dtype=np.int64);digest.update(draw.tobytes());count=np.stack([np.bincount(row,minlength=G) for row in draw]);nn=count@n;yy=count@sy;rr=count@sr;mu=yy/nn
        null=4*(yy/np.sqrt(mu)+nn*np.sqrt(mu)-2*rr);bootloss=count@losses
        for j,ref in enumerate(ids[1:],1):values[ref].extend(((bootloss[:,j]-bootloss[:,0])/null).tolist())
    pairs=c.read(run/'diagnostics/new_pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_new_pairs.parquet').to_pandas()
    check('Exactly2newpairs',len(pairs['pairs'])==2 and len(boot)==4000)
    check('Bootstrap common draw checksum',digest.hexdigest()==pairs['draws_sha256'])
    for j,ref in enumerate(ids[1:],1):
        pair=next(x for x in pairs['pairs'] if x['reference']==ref);dist=np.array(values[ref]);saved=boot[boot.reference.eq(ref)].sort_values('replicate')
        check('Multiplicity bootstrap '+ref,close(saved.delta_D2,dist,rtol=2e-8,atol=2e-11))
        check('Percentileinterval '+ref,close([pair['exploratory_lower95'],pair['exploratory_upper95']],np.quantile(dist,[.025,.975]),rtol=2e-8,atol=2e-11))
        advantage=losses[:,j]-losses[:,0];null=8*(np.sqrt(n.sum()*sy.sum())-sr.sum());keep=np.ones(G,bool);keep[np.argsort(-advantage,kind='stable')[:31]]=False;reduced=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum())
        check('Point/influence '+ref,close(pair['delta_D2'],advantage.sum()/null) and pair['removed_favorable_groups']==31 and close(pair['delta_after_removal'],advantage[keep].sum()/reduced))
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'nested_fit_diagnostics':nested,'fit_calls':0,'scope':'Separate checker, nativefit blocked; generaldeviance/sklearn, numeric/imputed/indicator manualexp, native replay, multiplicity bootstrap for only2newpairs. Own review, not professional independent validation.'}
    (run/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],'nested_fit_deviance_deltas':[x['B19_minus_B14_fit_deviance'] for x in nested]}))
    if result['failed']:print(json.dumps([x for x in checks if not x['pass']]));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
