"""Revisión separada de las ablaciones y de la explicación por fila; sin productor."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,argparse,json,uuid,hashlib,re
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v7_oracle_base',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;ATTEMPTS=0
def forbidden(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('Fit bloqueado durante revisión')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    report=c.read(run/'report.json');plan=c.read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    close=lambda a,b:np.allclose(a,b,rtol=3e-10,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in c.read(run/'frozen_sources_before_trial.json')['files']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Plan/code snapshot',c.sha(run/'code_snapshot.py')==report['code_sha256']==plan['code_sha256'] and c.sha(run/'plan_snapshot.json')==report['plan_sha256'])
    h=re.search(r'^## Codex \| '+plan['forum_preregistration']+r' \| ([^|]+) \|',(run/'forum_before_trial.md').read_text(encoding='utf-8'),re.M)
    check('Recipe precedes inference',h is not None and datetime.fromisoformat(h[1].strip())<datetime.fromisoformat(report['started_utc']))
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    old=pq.read_table(parent/'oof_2023.parquet').to_pandas();oof=pq.read_table(run/'oof_2023.parquet').to_pandas();ids=[f'W2-B{i:02d}' for i in range(19)]
    parts={m:p.sort_values(KEY).reset_index(drop=True) for m,p in oof.groupby('model_id')};base=parts['W2-B14'];first=parts['W2-B00']
    check('16 OOF exact',oof[oof.model_id.isin(ids[:16])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)))
    check('2023 unique',oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any() and set(parts)==set(ids))
    segments=c.read(run/'diagnostics/segments.json');scenarios=c.read(run/'diagnostics/observation_sensitivity.json')
    for mid in ids[16:]:
        p=parts[mid];check('Same complete keys '+mid,len(p)==50094 and p[KEY].equals(first[KEY]));check('Same target/link '+mid,p.T0.equals(base.T0) and p['e_cost_mix_1.0'].equals(base['e_cost_mix_1.0']))
        check('Positive/exposure once '+mid,np.isfinite(p.annual_rate).all() and p.annual_rate.gt(0).all() and np.array_equal(p.prediction,p.annual_rate*p['e_cost_mix_1.0']))
        check('General deviance formula '+mid,close(p.unit_deviance,c.dev(p.T0,p.prediction)))
        point=next(x for x in report['summary'] if x['model_id']==mid);check('External global D2 '+mid,close(point['D2'],c.d2_tweedie_score(p.T0,p.prediction,power=1.5)))
        unchanged=p.line.ne('motor')|p.x_new_business.ne(1);check('Home and renewals exact '+mid,np.array_equal(p.loc[unchanged,'annual_rate'],base.loc[unchanged,'annual_rate']))
        for record in [x for x in segments if x['model_id']==mid]:
            dim,label=record['segment'],record['label']
            lab={'line':p.line.astype(str),'fold':p.fold.astype(str),'business':pd.Series(np.where(p.x_new_business.eq(1),'new_business','renewal')),
              'line_business':p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal')}[dim]
            cell=p[lab.eq(label)];check('Segment '+mid+dim+label,close(record['D2'],c.d2_tweedie_score(cell.T0,cell.prediction,power=1.5)) and close(record['predicted_total'],cell.prediction.sum()))
        mapping={'nominal':('T0','e_cost_mix_1.0'),'reserve075':('T1_reserve075','e_cost_mix_0.75'),'reserve125':('T1_reserve125','e_cost_mix_1.25'),
          'late_cost05':('T0','e_cost_mix_tail0.05'),'late_cost10':('T0','e_cost_mix_tail0.1')}
        # Scenario names/columns are declared in the frozen first-wave plan; inspect that immutable contract.
        sourceplan=c.read(parent/'plan_snapshot.json')
        for record in [x for x in scenarios if x['model_id']==mid]:
            name=record['scenario'];keys={'base':('T0','e_cost_mix_1.0'),'reserve075':('T1_reserve075','e_cost_mix_0.75'),'reserve125':('T1_reserve125','e_cost_mix_1.25'),
              'late_cost05':('T0','e_cost_mix_tail0.05'),'late_cost10':('T0','e_cost_mix_tail0.1')}
            # Determine by the explicit stored name below (reject any unexpected scenario).
            if name in keys:yc,ec=keys[name]
            elif name in mapping:yc,ec=mapping[name]
            else:raise AssertionError('Escenario no previsto: '+name)
            check('Scenario '+mid+name,close(record['D2'],c.d2_tweedie_score(p[yc],p.annual_rate*p[ec],power=1.5)))
    for fold in range(5):
        cr=c.read(parent/f'auxiliary/credibility_fold{fold}.json')['ramos']['motor'];bundle=c.joblib.load(parent/f'models/W2-B14_motor_fold{fold}/bundle.joblib')
        tr=bundle['transformer'];numeric=list(tr.transformers_[0][2]);k=numeric.index('x_new_business');beta=bundle['estimator'].coef_;theta=float(beta[k]/tr.named_transformers_['numeric'].named_steps['scale'].scale_[k])
        tc_f=cr['Z_f']*cr['theta_f_em']+(1-cr['Z_f'])*cr['theta_f_dev'];tc_s=cr['Z_s']*cr['theta_s_em']+(1-cr['Z_s'])*cr['theta_s_dev']
        expected={'W2-B16':np.exp(tc_f-cr['theta_f_em']),'W2-B17':np.exp(tc_s-cr['theta_s_em']),'W2-B18':np.exp(tc_f+tc_s-theta)}
        check('Credibility components product fold'+str(fold),close(expected['W2-B16']*expected['W2-B17'],cr['c']))
        for line in ['motor','buildings','contents']:
            frame=pq.read_table(parent/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas();valid=frame[frame.fold.eq(fold)];fit=frame[frame.fold.ne(fold)]
            check('2023/disjoint '+line+str(fold),frame.year.eq(2023).all() and not frame.is_test.any() and all(not set(valid[z])&set(fit[z]) for z in ['group_id','customer_id','address_id']))
            for mid in ids[16:]:
                path=run/f'models/{mid}_{line}_fold{fold}/bundle.joblib';b=c.joblib.load(path);receipt=c.read(path.parent/'receipt.json')
                if line=='motor':
                    check('Factor '+mid+str(fold),close(b['c'],expected[mid]) and close(receipt['theta_price'],theta));native=b['parent']
                else:check('Home native exact '+mid+line+str(fold),c.sha(path)==c.sha(parent/f'models/W2-B14_{line}_fold{fold}/bundle.joblib'));native=b
                x=native['transformer'].transform(valid[native['columns']]);rate=np.exp(np.asarray(x@native['estimator'].coef_).ravel()+native['estimator'].intercept_)
                if line=='motor':rate*=np.where(valid.x_new_business.eq(1),expected[mid],1.)
                oracle=pd.DataFrame({'row_id':valid.row_id,'rate':rate}).set_index('row_id');p=parts[mid];p=p[p.line.eq(line)&p.fold.eq(fold)]
                check('Manual exp replay '+mid+line+str(fold),close(p.annual_rate,p.row_id.map(oracle.rate)))
    # Independent new-pair bootstrap through draw multiplicities and matrix products, not indexed loss sums.
    gf=pq.read_table(run/'diagnostics/group_aggregates.parquet').to_pandas();code,groups=pd.factorize(first.group_id,sort=True);g=len(groups)
    check('Group ordering',np.array_equal(groups,gf.group_id));n=np.bincount(code,minlength=g).astype(float);y=np.bincount(code,weights=first.T0,minlength=g);root=np.bincount(code,weights=np.sqrt(first.T0),minlength=g)
    gl=np.column_stack([np.bincount(code,weights=c.dev(parts[m].T0,parts[m].prediction),minlength=g) for m in ids])
    check('Independent group losses',close(gl,gf[['loss_'+m for m in ids]].to_numpy()))
    newpairs=[(a,b) for b in range(19) for a in range(max(16,b+1),19)];stored=pq.read_table(run/'diagnostics/bootstrap_new_51.parquet').to_pandas();reconstructed={p:[] for p in newpairs}
    rng=np.random.default_rng(2026102302);digest=hashlib.sha256()
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        for start in range(0,2000,16):
            draw=rng.integers(0,g,size=(16,g),dtype=np.int64);digest.update(draw.tobytes());weights=np.stack([np.bincount(v,minlength=g) for v in draw])
            den=8*(np.sqrt((weights@n)*(weights@y))-weights@root);loss=weights@gl
            for a,b in newpairs:reconstructed[(a,b)].extend(((loss[:,b]-loss[:,a])/den).tolist())
    pairs=c.read(run/'diagnostics/pairs.json');oldpairs=c.read(parent/'diagnostics/pairs.json')
    check('Old120 pairs exact',pairs['pairs'][:120]==oldpairs['pairs']);check('Same draw stream',digest.hexdigest()==pairs['draws_sha256']==oldpairs['draws_sha256'])
    check('Only51 new2000 replicates',len(stored)==51*2000 and len(pairs['pairs'])==171)
    for a,b in newpairs:
        label=ids[a]+'/'+ids[b];dist=stored.loc[stored.candidate.eq(ids[a])&stored.reference.eq(ids[b])].sort_values('replicate').delta_D2.to_numpy();rec=np.asarray(reconstructed[(a,b)])
        check('Bootstrap '+label,close(dist,rec));point=next(p for p in pairs['pairs'] if p['candidate']==ids[a] and p['reference']==ids[b]);adv=gl[:,b]-gl[:,a]
        den=8*(np.sqrt(n.sum()*y.sum())-root.sum());removed=np.argsort(-adv,kind='stable')[:31];keep=np.ones(g,bool);keep[removed]=False;td=8*(np.sqrt(n[keep].sum()*y[keep].sum())-root[keep].sum())
        check('Point/CI/influence '+label,close([point['delta_D2'],point['exploratory_lower95'],point['exploratory_upper95'],point['delta_after_removal']],
          [adv.sum()/den,*np.percentile(rec,[2.5,97.5]),adv[keep].sum()/td]))
    # Separate numerical check of all56 capital counterfactuals and motor loss partitions.
    review=ROOT/plan['diagnostic_review'];dr=c.read(review);cap=pq.read_table(review.parent/'capital_56_rows.parquet').to_pandas()
    check('56 capital complete,2023,T0zero',len(cap)==56 and cap.year.eq(2023).all() and cap.T0.eq(0).all() and not cap.duplicated(KEY).any())
    v5=ROOT/c.read(parent/'plan_snapshot.json')['parent_run']
    for fold in range(5):
        for line in ['buildings','contents']:
            q=cap[cap.fold.eq(fold)&cap.line.eq(line)];newf=pq.read_table(parent/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas();val=newf.set_index('row_id').loc[q.row_id].reset_index()
            b=c.joblib.load(v5/f'models/W2-B13_{line}_fold{fold}/bundle.joblib');numeric=list(b['transformer'].transformers_[0][2]);j=numeric.index('x_log_sum_insured');ntr=b['transformer'].named_transformers_['numeric'];median=ntr.named_steps['median'].statistics_[j];slope=b['estimator'].coef_[j]/ntr.named_steps['scale'].scale_[j]
            oldval=val.copy();oldval['x_log_sum_insured']=np.nan
            def manual(f):return np.exp(np.asarray(b['transformer'].transform(f[b['columns']])@b['estimator'].coef_).ravel()+b['estimator'].intercept_)
            check('Capital raw/corrected '+line+str(fold),close(q.capital_divided,q.capital_raw/1000) and close(q.corrected_log,np.log(q.capital_divided)))
            check('Capital exp/log decomposition '+line+str(fold),close(q.old_rate,manual(oldval)) and close(q.fixed_B13_corrected_rate,manual(val)) and close(q.direct_log_effect,slope*(q.corrected_log-median)) and close(q.direct_log_effect+q.refit_log_effect,np.log1p(q.total_relative_change)))
    m14=parts['W2-B14'];m15=parts['W2-B15'];mask=m14.line.eq('motor')&m14.x_new_business.eq(1);loss=c.dev(m15.loc[mask,'T0'],m15.loc[mask,'prediction'])-c.dev(m14.loc[mask,'T0'],m14.loc[mask,'prediction'])
    check('Motor aggregate harm',close(loss.sum(),dr['motor_loss_increase_total']))
    for record in dr['motor_loss_parts']:
        p=m14[mask];lab=p.fold.astype(str) if record['dimension']=='fold' else np.where(p.T0.gt(0),'positive','zero');cell=np.asarray(lab)==record['label'];check('Motor loss partition '+record['dimension']+record['label'],close(loss[cell].sum(),record['loss_increase']))
    selector=c.read(REPO/'registro/semana2_seleccion_actual.json');check('2024 ledger absent',not (ROOT/selector['ledger_workspace_relative']).exists())
    check('No other scope',report['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and report['test_predictions']==0 and report['new_price_base_fits']==report['new_auxiliary_fits']==0)
    check('No fits during replay',ATTEMPTS==0);check('B00 retained/no promotion',report['reference_retained']=='W2-B00' and not report['promotion'])
    (run/'verifications').mkdir(exist_ok=True);path=run/'verifications'/('v7_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','checker':str(Path(__file__)),'checker_sha256':c.sha(Path(__file__)),
      'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'new_fits':0,'professional_independent_validation':False}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'path':str(path),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}))
    return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
