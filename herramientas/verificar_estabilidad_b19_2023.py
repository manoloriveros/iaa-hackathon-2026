"""Otra cuenta de coeficientes, grupos y derivadas locales; sin entrenar."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,math,importlib.util,subprocess
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from scipy.linalg import cho_factor,cho_solve,solve_triangular
from sklearn.metrics import d2_tweedie_score
from sklearn.linear_model import TweedieRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
KEY=['market','line','row_id'];read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()

def dev(y,mu):
    power=1.5;y=np.asarray(y);mu=np.asarray(mu)
    return 2*(y**(2-power)/((1-power)*(2-power))-y*mu**(1-power)/(1-power)+mu**(2-power)/(2-power))

def main():
    run=Path(sys.argv[1]).resolve();p=read(run/'plan_snapshot.json');checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    def close(a,b,rtol=2e-9,atol=2e-8):return np.allclose(a,b,rtol=rtol,atol=atol,equal_nan=True)
    def forbidden(*a,**k):raise RuntimeError('Fit blocked in independent artifact check')
    for cls in [TweedieRegressor,SimpleImputer,StandardScaler,OneHotEncoder,ColumnTransformer,Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    for x in p['frozen_sources']:check('Frozen '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for x in read(run/'manifest.json')['files']:check('Artifact '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    table=pq.read_table(run/'paired_oof_2023.parquet').to_pandas();coef=pq.read_table(run/'coefficients_original_scale.parquet').to_pandas();inf=pq.read_table(run/'training_group_local_influence.parquet').to_pandas()
    groups=pq.read_table(run/'oof_group_contributions.parquet').to_pandas();loo=pq.read_table(run/'leave_one_group_evaluation.parquet').to_pandas();sel=pq.read_table(run/'ranked_group_selections.parquet').to_pandas()
    check('Unique2023pairedkeys',len(table)==50094 and table.year.eq(2023).all() and not table.duplicated(KEY).any())
    # Coefficient identities use native bundles but no producer extraction function.
    for mid,parent in [('W2-B19',ROOT/p['b19_run']),('W2-B14',ROOT/p['b14_run'])]:
        for line in ['motor','buildings','contents']:
            for fold in range(5):
                b=joblib.load(parent/f'models/{mid}_{line}_fold{fold}/bundle.joblib');tr=b['transformer'];num=tr.named_transformers_['numeric'];numcols=tr.transformers_[0][2];betas=b['estimator'].coef_
                rows=coef[coef.model_id.eq(mid)&coef.line.eq(line)&coef.fold.eq(fold)];ident=mid+line+str(fold)
                raw=np.array([rows[rows.feature.eq(col)].beta_raw.iloc[0] for col in numcols])
                check('Originalscale numeric '+ident,close(raw*num['scale'].scale_,betas[:len(numcols)]))
                intercept=rows[rows.feature.eq('intercept')].beta_raw.iloc[0]
                check('Rawintercept shift '+ident,close(intercept+raw@num['scale'].mean_,b['estimator'].intercept_))
                enc=tr.named_transformers_['categorical'];offset=len(numcols)
                for j,col in enumerate(tr.transformers_[1][2]):
                    rr=rows[rows.feature.eq(col)];levels=enc.categories_[j];ref=str(levels[enc.drop_idx_[j]])
                    check('Categoricalbaseline '+ident+col,rr.reference.eq(ref).all() and rr[rr.level.eq(ref)].beta_raw.iloc[0]==0)
                    for k,level in enumerate(levels):
                        if k==enc.drop_idx_[j]:continue
                        check('Categoricalcoefficient '+ident+col+str(level),close(rr[rr.level.eq(str(level))].beta_raw.iloc[0],betas[offset]));offset+=1
    # Rebuild local derivatives and use Cholesky dual solves, not full solve(H,G.T).
    original=ROOT/p['b19_run'];recipe=read(original/'plan_snapshot.json')['recipe'];hinfo=read(run/'hessian_conditions.json');derivatives=[]
    for line in ['motor','buildings']:
        for fold in range(5):
            ident=line+str(fold);frame=pq.read_table(original/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas();fit=frame[frame.fold.ne(fold)]
            b=joblib.load(original/f'models/W2-B19_{line}_fold{fold}/bundle.joblib');x=b['transformer'].transform(fit[b['columns']]);x=x.toarray() if hasattr(x,'toarray') else np.asarray(x);z=np.column_stack([x,np.ones(len(fit))])
            theta=np.r_[b['estimator'].coef_,b['estimator'].intercept_];mu=np.exp(z@theta);response=fit.T0.to_numpy()/fit['e_cost_mix_1.0'].to_numpy();w=np.sqrt(fit['e_cost_mix_1.0'].to_numpy());w/=w.sum();power=1.5
            g=w*(mu-response)*mu**(1-power);h=w*((2-power)*mu**(2-power)-(1-power)*response*mu**(1-power))
            H=(z*np.sqrt(h)[:,None]).T@(z*np.sqrt(h)[:,None]);saved=np.load(run/f'hessians/{line}_fold{fold}.npz');info=next(v for v in hinfo if v['line']==line and v['fold']==fold)
            check('HessianweightedGram '+ident,close(H,saved['H']) and close(theta,saved['theta']))
            check('Hessianstatus '+ident,(info['status']=='local_approximation_only')==(np.linalg.eigvalsh(H)[0]>0 and np.linalg.cond(H)<=p['max_hessian_condition']))
            rng=np.random.default_rng(2026102409+fold+(10 if line=='motor' else 0))
            for j in range(2):
                direction=rng.normal(size=z.shape[1]);direction/=np.linalg.norm(direction);step=1e-6;eta=z@direction
                def gradient(sign):
                    rate=mu*np.exp(sign*step*eta);return z.T@(w*(rate-response)*rate**(1-power))
                numeric=(gradient(1)-gradient(-1))/(2*step);analytic=H@direction;error=float(np.max(np.abs(numeric-analytic))/max(1,np.max(np.abs(analytic))))
                derivatives.append({'line':line,'fold':fold,'direction':j,'relative_error':error});check('DirectionalHessian '+ident+str(j),error<1e-7)
            if info['status']!='local_approximation_only':continue
            labels,codes=np.unique(fit.group_id,return_inverse=True);groupgrad=np.column_stack([np.bincount(codes,weights=g*z[:,j],minlength=len(labels)) for j in range(z.shape[1])])
            record=inf[inf.line.eq(line)&inf.fold.eq(fold)].sort_values('group_id').reset_index(drop=True);check('GroupHscope '+ident,record.group_id.tolist()==labels.tolist() and record.group_validation_fold.ne(fold).all())
            block=recipe['features_by_line'][line];scales=b['transformer'].named_transformers_['numeric']['scale'].scale_;jnew=block['numeric'].index('x_new_business');features=b['transformer'].get_feature_names_out().tolist()
            jcov=block['numeric'].index('x_accidental_damage_cover') if line=='buildings' else features.index('categorical__x_cover_type_third_party_only');scov=scales[jcov] if line=='buildings' else 1.
            with threadpool_limits(limits=2):
                factor=cho_factor(H,lower=True)
                for column,coordinate,scale in [('local_delete_delta_coverage_beta',jcov,scov),('local_delete_delta_newbusiness_beta',jnew,scales[jnew])]:
                    unit=np.eye(len(theta))[coordinate];dual=cho_solve(factor,unit);expected=groupgrad@dual/scale
                    check('Choleskydual influence '+ident+column,close(record[column],expected))
                chol=np.linalg.cholesky(H);normalized=solve_triangular(chol,(z*np.sqrt(h)[:,None]).T,lower=True);lev=np.sum(normalized**2,axis=0)
            expected_lev=np.bincount(codes,weights=lev,minlength=len(labels));check('Choleskyleverage '+ident,close(record.group_leverage_trace,expected_lev) and close(expected_lev.sum(),len(theta)))
            check('Linear solve residual '+ident,record.solve_residual_inf.max()<1e-8)
    # Direct row-level metrics verify selected deletions; dictionaries/fsum verify all groups.
    masks={'buildings':table.line.eq('buildings'),'motor_new':table.line.eq('motor')&table.x_new_business.eq(1)}
    for scope,mask in masks.items():
        t=table[mask].copy();gg=groups[groups.scope.eq(scope)].sort_values('group_id');ll=loo[loo.scope.eq(scope)].set_index('group_id')
        records={key:cell for key,cell in t.groupby('group_id',sort=True)}
        sums={key:math.fsum((dev(cell.T0,cell.B19_prediction)-dev(cell.T0,cell.B14_prediction)).tolist()) for key,cell in records.items()}
        check('All new group contributions '+scope,all(close(x.loss_delta,sums[x.group_id]) and x.rows==len(records[x.group_id]) for x in gg.itertuples(index=False)))
        for direction in ['adverse','favorable']:
            ordered=sorted([key for key,value in sums.items() if value>0] if direction=='adverse' else [key for key,value in sums.items() if value<0],key=lambda key:(-sums[key] if direction=='adverse' else sums[key],key))
            for k in p['removal_k']:
                ids=ordered[:k];savedids=sel[sel.scope.eq(scope)&sel.direction.eq(direction)&sel.requested_groups.eq(k)].sort_values('rank').group_id.tolist()
                check('Signed ranking '+scope+direction+str(k),savedids==ids)
                rr=next(x for x in read(run/'group_removal_evaluation.json') if x['scope']==scope and x['direction']==direction and x['requested_groups']==k)
                def metric(f):return float(d2_tweedie_score(f.T0,f.B19_prediction,power=1.5)-d2_tweedie_score(f.T0,f.B14_prediction,power=1.5))
                check('Direct sklearn segmentdeletion '+scope+direction+str(k),close(rr['delta_scope_D2'],metric(t[~t.group_id.isin(ids)])))
                check('Direct sklearn fullcomponent deletion '+scope+direction+str(k),close(rr['delta_global_D2_full_components'],metric(table[~table.group_id.isin(ids)])))
        candidates=set(gg.iloc[np.linspace(0,len(gg)-1,10,dtype=int)].group_id)|{max(sums,key=sums.get),min(sums,key=sums.get)}
        for key in candidates:
            retained=t[t.group_id.ne(key)];direct=d2_tweedie_score(retained.T0,retained.B19_prediction,power=1.5)-d2_tweedie_score(retained.T0,retained.B14_prediction,power=1.5)
            check('Single-group direct metric '+scope+key,close(ll.loc[key,'delta_D2_without_group'],direct))
    # Producer imported only for focal guards and technical edge cases below.
    sp=importlib.util.spec_from_file_location('stability_adversaries',ROOT/p['code']);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.block_fit()
    def reject(name,fn):
        try:fn()
        except ValueError:check(name,True)
        else:check(name,False)
    bad=table.head(2).copy();bad['year']=2024;reject('Year guard',lambda:m.guard(bad))
    reject('Duplicate guard',lambda:m.guard(pd.concat([table.head(1),table.head(1)],ignore_index=True)))
    check('Zero-null gives no inventedD2',m.delta(1,0.,0.,1.) is None)
    fixture=pd.DataFrame({'group_id':['b','a','c','d'],'loss_delta':[2.,2.,-1.,0.]})
    check('Ties byID, no opposite-sign padding',m.ranked(fixture,'adverse',31)==['a','b'] and m.ranked(fixture.iloc[::-1],'favorable',31)==['c'])
    originalframe=pq.read_table(original/'inputs_2023/buildings_fold0.parquet').to_pandas();bundle=joblib.load(original/'models/W2-B19_buildings_fold0/bundle.joblib')
    singular=originalframe[originalframe.fold.ne(0)].head(1).copy()
    with threadpool_limits(limits=2):rows,info,_=m.local_group_influence(singular,bundle,recipe['features_by_line']['buildings'],'buildings',0,p['max_hessian_condition'])
    check('SingularHguard no ridge/pseudoinverse',not rows and info['status']=='not_estimable_condition_guard')
    reject('Local diagnostic rejects heldout',lambda:m.local_group_influence(originalframe[originalframe.fold.eq(0)].head(1),bundle,recipe['features_by_line']['buildings'],'buildings',0,p['max_hessian_condition']))
    # Real command rejects a poisoned pairing before any Hessian diagnostic or training.
    ad=run/'adversaries';ad.mkdir(exist_ok=False);oof=pq.read_table(ROOT/p['oof'],filters=[('model_id','in',['W2-B19','W2-B14'])]).to_pandas();bad=oof.copy();idx=bad.index[bad.model_id.eq('W2-B19')][0];bad.loc[idx,'T0']+=1.
    fixturefile=ad/'poisoned_T0.parquet';bad.to_parquet(fixturefile,index=False);negative=dict(p,oof=rel(fixturefile),frozen_sources=[{'path':rel(fixturefile),'sha256':sha(fixturefile)}]);pp=ad/'plan.json';pp.write_text(json.dumps(negative),encoding='utf-8')
    before=set(run.parent.glob('estabilidad_b19_*'));proc=subprocess.run([sys.executable,str(ROOT/p['code']),str(pp)],capture_output=True,text=True);created=sorted(set(run.parent.glob('estabilidad_b19_*'))-before)
    (ad/'stderr.txt').write_text(proc.stderr,encoding='utf-8');check('Real flow rejects pairT0 change',proc.returncode!=0 and 'Pair metadata changed T0' in proc.stderr and len(created)==1 and not list((created[0]/'hessians').glob('*.npz')))
    for path in created:(path/'expected_adversary_failure.json').write_text(json.dumps({'kind':'expected_negative_fixture_not_pending','owner_run':rel(run),'fit_calls':0}),encoding='utf-8')
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'directional_derivatives':derivatives,
        'expected_failure_runs':[rel(x) for x in created],'fit_calls':0,'new_bootstrap':0,'scope':'Separate raw coefficient identities, generaldeviance and row-level sklearn evaluation deletions, Choleskydual influence/leverage and directional derivatives; blocked fitting, no refit or prior bootstrap repetition. Own review, not professional independent validation.'}
    (run/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':result['passed'],'failed':result['failed'],'expected_failure_runs':len(created)}))
    if result['failed']:print(json.dumps([x for x in checks if not x['pass']]));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
