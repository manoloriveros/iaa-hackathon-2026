"""Coeficientes y grupos de B19, solo artefactos2023 y sin ajustar modelos."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,uuid
ROOT=Path(__file__).resolve().parents[4];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import joblib
from sklearn.linear_model import TweedieRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
KEY=['market','line','row_id'];MID='W2-B19';BASE='W2-B14'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def require(ok,msg):
    if not bool(ok):raise ValueError(msg)

def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n',encoding='utf-8')

def block_fit():
    def forbidden(*a,**k):raise RuntimeError('No fitting permitted in B19 artifact diagnostic')
    for cls in [TweedieRegressor,SimpleImputer,StandardScaler,OneHotEncoder,ColumnTransformer,Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden

def guard(f):
    require(len(f)>0 and f.year.eq(2023).all(),'Empty or non2023 scope')
    if 'is_test' in f:require(not f.is_test.any(),'Test forbidden')
    require(not f.duplicated(KEY).any(),'Duplicate period keys')

def null(n,y,root):return 8*(np.sqrt(np.asarray(n)*np.asarray(y))-np.asarray(root))

def delta(n,y,root,loss_delta):
    d=null(n,y,root)
    if np.ndim(d)==0:return float(-loss_delta/d) if d>1e-12 else None
    return np.divide(-loss_delta,d,out=np.full_like(np.asarray(d,float),np.nan),where=np.asarray(d)>1e-12)

def ranked(group_table,direction,k):
    require(direction in ['adverse','favorable'],'Unknown direction')
    g=group_table[group_table.loss_delta.gt(0) if direction=='adverse' else group_table.loss_delta.lt(0)]
    return g.sort_values(['loss_delta','group_id'],ascending=[direction!='adverse',True],kind='stable').head(k).group_id.tolist()

def coef_raw(bundle,line,fold,mid):
    tr=bundle['transformer'];num=tr.named_transformers_['numeric'];cols=tr.transformers_[0][2];rows=[]
    betas=bundle['estimator'].coef_;shift=float(bundle['estimator'].intercept_)
    for j,col in enumerate(cols):
        b=float(betas[j]/num['scale'].scale_[j]);shift-=b*num['scale'].mean_[j]
        rows.append({'model_id':mid,'line':line,'fold':fold,'feature':col,'level':'unit','reference':'one original unit','beta_raw':b,'kind':'numeric'})
    enc=tr.named_transformers_['categorical'];catcols=tr.transformers_[1][2];offset=len(cols)
    require(all(x is None for x in enc.infrequent_categories_),'Infrequent categories need explicit common coding; no fabricated comparison')
    for j,col in enumerate(catcols):
        levels=enc.categories_[j];drop=int(enc.drop_idx_[j]);reference=str(levels[drop])
        for k,level in enumerate(levels):
            value=0. if k==drop else float(betas[offset]);offset+=int(k!=drop)
            rows.append({'model_id':mid,'line':line,'fold':fold,'feature':col,'level':str(level),'reference':reference,'beta_raw':value,'kind':'categorical'})
    require(offset==len(betas),'Coefficient coding mismatch')
    rows.append({'model_id':mid,'line':line,'fold':fold,'feature':'intercept','level':'baseline','reference':'numericzero and stated categories','beta_raw':shift,'kind':'intercept'})
    return rows

def local_group_influence(frame,bundle,block,line,fold,max_condition):
    guard(frame);require(frame.fold.ne(fold).all(),'Heldout in local fit diagnostic')
    x=bundle['transformer'].transform(frame[bundle['columns']]);x=x.toarray() if hasattr(x,'toarray') else np.asarray(x)
    z=np.column_stack([x,np.ones(len(frame))]);theta=np.r_[bundle['estimator'].coef_,bundle['estimator'].intercept_]
    mu=np.exp(z@theta);e=frame['e_cost_mix_1.0'].to_numpy();y=frame.T0.to_numpy()/e;w=np.sqrt(e);w/=w.sum()
    score=w*(np.sqrt(mu)-y/np.sqrt(mu));curvature=.5*w*(np.sqrt(mu)+y/np.sqrt(mu))
    H=z.T@(curvature[:,None]*z);eigen=np.linalg.eigvalsh(H);condition=float(eigen[-1]/eigen[0]) if eigen[0]>0 else None
    info={'line':line,'fold':fold,'dimension':z.shape[1],'condition':condition,'min_eigenvalue':float(eigen[0]),'max_eigenvalue':float(eigen[-1]),
        'max_normalized_gradient':float(np.abs(z.T@score).max()),'method':'Full-Hessian local deletion approximation H^-1 G_group; no refit or changed-C0 approximation.'}
    if condition is None or condition>max_condition:
        info['status']='not_estimable_condition_guard';return [],info,{'H':H,'theta':theta}
    codes,groups=pd.factorize(frame.group_id,sort=True);G=np.zeros((len(groups),z.shape[1]));np.add.at(G,codes,score[:,None]*z)
    influence=np.linalg.solve(H,G.T).T
    solve=np.linalg.solve(H,z.T).T;leverage=curvature*np.einsum('ij,ij->i',z,solve)
    group_leverage=np.bincount(codes,weights=leverage,minlength=len(groups));nb=np.bincount(codes,weights=frame.x_new_business,minlength=len(groups))
    sizes=np.bincount(codes,minlength=len(groups));cost=np.bincount(codes,weights=frame.T0,minlength=len(groups));originalfold=frame.groupby('group_id').fold.first().reindex(groups).to_numpy()
    features=bundle['transformer'].get_feature_names_out().tolist();numeric=bundle['transformer'].named_transformers_['numeric']['scale'].scale_
    jnew=block['numeric'].index('x_new_business');scale_new=numeric[jnew]
    if line=='buildings':jcov=block['numeric'].index('x_accidental_damage_cover');scale_cov=numeric[jcov];covname='AD_yes / AD_no'
    else:jcov=features.index('categorical__x_cover_type_third_party_only');scale_cov=1.;covname='third_party_only / comprehensive'
    rows=[]
    for j,g in enumerate(groups):
        rows.append({'line':line,'fold':fold,'group_id':g,'group_validation_fold':int(originalfold[j]),'training_rows':int(sizes[j]),'training_new_rows':int(nb[j]),'T0_CU':float(cost[j]),
            'group_leverage_trace':float(group_leverage[j]),'coverage_contrast':covname,'current_coverage_beta_raw':float(theta[jcov]/scale_cov),
            'local_delete_delta_coverage_beta':float(influence[j,jcov]/scale_cov),'current_newbusiness_beta_raw':float(theta[jnew]/scale_new),
            'local_delete_delta_newbusiness_beta':float(influence[j,jnew]/scale_new),'gradient_group_norm':float(np.linalg.norm(G[j])),
            'solve_residual_inf':float(np.abs(H@influence[j]-G[j]).max())})
    info.update(status='local_approximation_only',sum_group_leverage=float(group_leverage.sum()),max_group_leverage=float(group_leverage.max()))
    return rows,info,{'H':H,'theta':theta}

def main():
    block_fit();pp=Path(sys.argv[1]).resolve();p=read(pp)
    require(sha(Path(__file__))==p['code_sha256'],'Code changed')
    for x in p['frozen_sources']:require(sha(ROOT/x['path'])==x['sha256'],'Frozen source '+x['path'])
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();require(forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1,'Preregister first')
    run=ROOT/p['b19_run'];out=REPO/'privado/semana2/desarrollo2023'/('estabilidad_b19_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir();(out/'hessians').mkdir()
    (out/'plan_snapshot.json').write_bytes(pp.read_bytes());(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    oof=pq.read_table(ROOT/p['oof'],filters=[('year','=',2023),('model_id','in',[MID,BASE])]).to_pandas();require(set(oof.model_id)=={MID,BASE},'Missing comparison model')
    parts={mid:oof[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True) for mid in [MID,BASE]}
    for mid,table in parts.items():guard(table);require(len(table)==50094,'Incomplete model')
    a,b=parts[MID],parts[BASE]
    for col in KEY+['year','fold','group_id','T0','exposure','e_cost_mix_1.0']:require(a[col].equals(b[col]),'Pair metadata changed '+col)
    pair=a[KEY+['year','fold','group_id','T0','x_new_business','exposure']].copy();pair['B19_prediction']=a.prediction;pair['B14_prediction']=b.prediction;pair['B19_loss']=a.unit_deviance;pair['B14_loss']=b.unit_deviance;pair['loss_delta']=a.unit_deviance-b.unit_deviance
    pair.to_parquet(out/'paired_oof_2023.parquet',index=False)
    coeff=[];influences=[];hinfo=[]
    parent=ROOT/p['b14_run'];recipe=read(run/'plan_snapshot.json')['recipe']
    for line in ['motor','buildings','contents']:
        for fold in range(5):
            bundle=joblib.load(run/f'models/{MID}_{line}_fold{fold}/bundle.joblib');parentbundle=joblib.load(parent/f'models/{BASE}_{line}_fold{fold}/bundle.joblib')
            coeff.extend(coef_raw(bundle,line,fold,MID));coeff.extend(coef_raw(parentbundle,line,fold,BASE))
            if line in ['motor','buildings']:
                frame=pq.read_table(run/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas();guard(frame);fit=frame[frame.fold.ne(fold)].copy()
                with threadpool_limits(limits=2):rows,info,matrices=local_group_influence(fit,bundle,recipe['features_by_line'][line],line,fold,p['max_hessian_condition'])
                influences.extend(rows);hinfo.append(info);np.savez(out/f'hessians/{line}_fold{fold}.npz',**matrices)
                check('Localgradient '+line+str(fold),info['max_normalized_gradient']<=1e-4)
                if info['status']=='local_approximation_only':check('Leverage sum dimension '+line+str(fold),np.isclose(info['sum_group_leverage'],info['dimension'],rtol=1e-9,atol=1e-9))
    pd.DataFrame(coeff).to_parquet(out/'coefficients_original_scale.parquet',index=False);pd.DataFrame(influences).to_parquet(out/'training_group_local_influence.parquet',index=False);dump(out/'hessian_conditions.json',hinfo)
    scopes={'buildings':pair.line.eq('buildings'),'motor_new':pair.line.eq('motor')&pair.x_new_business.eq(1)};aggregates=[];leaveone=[];removals=[];selection=[];focus_summaries=[]
    for scope,mask in scopes.items():
        table=pair[mask].copy();table['sqrt_T0']=np.sqrt(table.T0)
        groups=table.groupby('group_id',sort=True).agg(rows=('T0','size'),T0=('T0','sum'),sqrt_T0=('sqrt_T0','sum'),loss_delta=('loss_delta','sum'),B19_loss=('B19_loss','sum'),B14_loss=('B14_loss','sum'),fold=('fold','first')).reset_index()
        groups['scope']=scope;aggregates.append(groups);N=len(table);Y=float(table.T0.sum());R=float(np.sqrt(table.T0).sum());L=float(table.loss_delta.sum());base_delta=delta(N,Y,R,L)
        lo=groups[['group_id','scope']].copy();lo['delta_D2_without_group']=delta(N-groups.rows,Y-groups.T0,R-groups.sqrt_T0,L-groups.loss_delta);lo['change_from_full_delta']=lo.delta_D2_without_group-base_delta;leaveone.append(lo)
        focus_summaries.append({'scope':scope,'rows':N,'groups':len(groups),'delta_B19_minus_B14':base_delta,'net_loss_delta':L,
            'gross_adverse_loss':float(groups.loc[groups.loss_delta.gt(0),'loss_delta'].sum()),'gross_favorable_loss':float(-groups.loc[groups.loss_delta.lt(0),'loss_delta'].sum()),
            'T0':Y,'single_group_delta_min':float(lo.delta_D2_without_group.min()),'single_group_delta_max':float(lo.delta_D2_without_group.max())})
        for direction in ['adverse','favorable']:
            for k in p['removal_k']:
                ids=ranked(groups,direction,k);keep=~table.group_id.isin(ids);global_keep=~pair.group_id.isin(ids)
                def metric(t):return delta(len(t),t.T0.sum(),np.sqrt(t.T0).sum(),t.loss_delta.sum())
                removals.append({'scope':scope,'direction':direction,'requested_groups':k,'actual_groups':len(ids),'retained_scope_rows':int(keep.sum()),
                    'delta_scope_D2':metric(table[keep]),'delta_global_D2_full_components':metric(pair[global_keep]),
                    'selected_loss_delta':float(groups[groups.group_id.isin(ids)].loss_delta.sum()),'selected_T0':float(groups[groups.group_id.isin(ids)].T0.sum())})
                selection.extend({'scope':scope,'direction':direction,'requested_groups':k,'rank':j+1,'group_id':g} for j,g in enumerate(ids))
        check('Focused attribution sums '+scope,np.isclose(groups.loss_delta.sum(),L,rtol=1e-12,atol=1e-8))
    pd.concat(aggregates,ignore_index=True).to_parquet(out/'oof_group_contributions.parquet',index=False);pd.concat(leaveone,ignore_index=True).to_parquet(out/'leave_one_group_evaluation.parquet',index=False)
    pd.DataFrame(selection).to_parquet(out/'ranked_group_selections.parquet',index=False);dump(out/'group_removal_evaluation.json',removals);dump(out/'focus_summary.json',focus_summaries)
    # Enrich focus groups with canonical known perils, without changing costs/labels.
    claims=pq.read_table(ROOT/p['claims_2023']).to_pandas();require(claims.year.eq(2023).all() and claims.claim_id.is_unique,'Claim scope')
    perils=[]
    for scope,mask in scopes.items():
        focus=pair[mask];g=claims.merge(focus[KEY],on=KEY,how='inner',validate='many_to_one')
        check('Canonical cents match focus '+scope,int(g.T0_cents.sum())==int(round(focus.T0.sum()*100)))
        for keys,cell in g.groupby(['group_id','peril','status'],sort=True):perils.append({'scope':scope,'group_id':keys[0],'peril':keys[1],'status':keys[2],'claims':len(cell),'net_cents':int(cell.T0_cents.sum())})
    pd.DataFrame(perils).to_parquet(out/'focus_group_perils.parquet',index=False)
    result={'id':p['id'],'author':'Codex','run':rel(out),'completed_utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'fit_calls':0,'new_models':0,'new_bootstrap':0,'coefficient_rows':len(coeff),'training_group_diagnostics':len(influences),'local_hessians':len(hinfo),
        'hessians_not_estimable':sum(x['status']!='local_approximation_only' for x in hinfo),'focus_scopes':list(scopes),'reference':'W2-B00','all_alternatives_preserved':True,
        'ledger_read':False,'external2024_artifacts_read':False,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False}
    dump(out/'report.json',result);dump(out/'manifest.json',{'files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(out.rglob('*')) if x.is_file()]})
    require(result['failed']==0,'Artifact diagnostic failed, retain evidence')
    print(json.dumps({'run':rel(out),'passed':result['passed'],'failed':result['failed'],'fit_calls':0,'hessians_not_estimable':result['hessians_not_estimable'],'focus':focus_summaries}))

if __name__=='__main__':main()
