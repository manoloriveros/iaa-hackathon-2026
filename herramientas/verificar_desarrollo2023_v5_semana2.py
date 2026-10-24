"""Verificación separada: constantes, GLM pequeño, entrada y replay sin fit."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,math,re,argparse,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v5_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;ATTEMPTS=0
def blocked(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('fit bloqueado en comprobación')
def pred(b,f):
    assert f.year.eq(2023).all() and not f.is_test.any()
    if b['family']=='business_constant':return np.array([b['rates'][int(x)] for x in f.x_new_business])
    return c.predict(b,f)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();run=Path(a.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    r=c.read(run/'report.json');plan=c.read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];checks=[]
    def check(n,v,detail=None):checks.append({'name':n,'pass':bool(v),'detail':detail})
    close=lambda a,b:np.allclose(a,b,rtol=2e-10,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in c.read(run/'frozen_sources_before_fit.json')['files']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Code and plan',c.sha(run/'code_snapshot.py')==r['code_sha256'] and c.sha(run/'plan_snapshot.json')==r['plan_sha256'])
    header=re.search(r'^## Codex \| COD-S2-20261023-016 \| ([^|]+) \|',(run/'forum_before_fit.md').read_text(encoding='utf-8'),re.M)
    check('Preregistration precedes fit',header is not None and datetime.fromisoformat(header[1].strip())<datetime.fromisoformat(r['started_utc']))
    ready=c.read(run/'readiness_snapshot.json');contract=c.read(ROOT/ready['availability_contract'])['blocks']
    check('Availability matches prepared contract',c.sha(ROOT/ready['availability_contract'])==ready['availability_sha256'])
    policy=c.read(ROOT/plan['selection_policy'])
    for key in ['target','partitions']:check('Original base '+key,c.sha(ROOT/policy['base_manifest'][key]['path'])==policy['base_manifest'][key]['sha256'])
    selection=c.read(REPO/'registro/semana2_seleccion_actual.json')
    check('2024 ledger absent',not (ROOT/selection['ledger_workspace_relative']).exists())
    check('2024/test consumer closed',r['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and r['test_predictions']==0)
    check('B00 retained, no promotion',r['reference_retained']=='W2-B00' and not r['promotion'] and not r['final_confirmation_roster_frozen'])
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=blocked
        if hasattr(cls,'fit_transform'):cls.fit_transform=blocked
    old=pq.read_table(parent/'oof_2023.parquet').to_pandas();oof=pq.read_table(run/'oof_2023.parquet').to_pandas()
    check('Twelve recipes unchanged',oof[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)))
    check('Unique 2023 OOF',oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any())
    ordered={m:p.sort_values(KEY).reset_index(drop=True) for m,p in oof.groupby('model_id')};first=ordered['W2-B00'];new=['W2-B12','W2-B13']
    for mid,p in ordered.items():
        check('Complete keys '+mid,len(p)==50094 and p[KEY].equals(first[KEY]))
        if mid in new:
            for col in ['T0','fold','year','group_id','exposure','e_cost_mix_1.0']:check('Common '+mid+col,p[col].equals(first[col]))
            check('Positive single exposure '+mid,np.isfinite(p.annual_rate).all() and p.annual_rate.gt(0).all() and np.array_equal(p.prediction,p.annual_rate*p['e_cost_mix_1.0']))
            check('Independent unit deviance '+mid,close(p.unit_deviance,c.dev(p.T0,p.prediction)))
            row=next(x for x in r['summary'] if x['model_id']==mid);check('Independent global D2 '+mid,close(row['D2'],c.d2_tweedie_score(p.T0,p.prediction,power=1.5)))
    recipe=next(m for m in plan['models'] if m['id']=='W2-B13');constant_count=0;glm_count=0;gradient_records=[]
    for line in ['motor','buildings','contents']:
        data=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas();block=recipe['features_by_line'][line]
        check('Exact source and year '+line,c.sha(run/f'inputs_2023/{line}.parquet')==c.sha(parent/f'inputs_2023/{line}.parquet') and data.year.eq(2023).all() and not data.is_test.any())
        check('Six allowed core fields '+line,len(block['all'])==6 and set(block['all'])<=set(contract[line]['all']))
        for fold in range(5):
            tag=line+str(fold);lp=run/f'links_2023/{line}_fold{fold}.parquet';links=pq.read_table(lp).to_pandas()
            check('Exact C0 and roles '+tag,c.sha(lp)==c.sha(parent/f'links_2023/{line}_fold{fold}.parquet') and c.sha(run/f'fit_rows/{line}_fold{fold}.parquet')==c.sha(parent/f'fit_rows/{line}_fold{fold}.parquet'))
            ecol=[x for x in links if x.startswith('e_cost_')];f=data.merge(links[KEY+ecol],on=KEY,validate='one_to_one');fit=f[f.fold.ne(fold)];valid=f[f.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            for col in ['group_id','customer_id','address_id']:check('Disjoint '+tag+col,not set(fit[col])&set(valid[col]))
            b12=c.joblib.load(run/'models'/f'W2-B12_{line}_fold{fold}/bundle.joblib')
            for biz in [0,1]:
                sub=fit[fit.x_new_business.eq(biz)];e=sub['e_cost_mix_1.0'].to_numpy();q=math.fsum((sub.T0/np.sqrt(e)).tolist())/math.fsum(np.sqrt(e).tolist());constant_count+=1
                check('Constant from training oracle '+tag+str(biz),close(q,b12['rates'][biz]) and q>0)
                check('Constant score zero '+tag+str(biz),abs(math.fsum((np.sqrt(e*q)-sub.T0/np.sqrt(e*q)).tolist()))<1e-6)
            path=run/'models'/f'W2-B13_{line}_fold{fold}';b13=c.joblib.load(path/'bundle.joblib');receipt=c.read(path/'receipt.json');glm_count+=1
            check('Exact GLM parameters '+tag,all(b13['estimator'].get_params()[k]==v for k,v in recipe['params'].items()) and b13['columns']==block['all'] and b13['estimator'].n_iter_<2000)
            tr=b13['transformer'];num=tr.named_transformers_['numeric'];imp=num.named_steps['median'];scale=num.named_steps['scale'];enc=tr.named_transformers_['categorical']
            x=fit[block['numeric']].to_numpy(float);median=np.nanmedian(x,axis=0);median=np.where(np.isnan(median),0,median);imputed=np.where(np.isnan(x),median,x)
            check('Median and scale fit-only '+tag,close(imp.statistics_,median) and close(scale.mean_,imputed.mean(axis=0)) and close(scale.var_,imputed.var(axis=0)))
            check('Encoder configuration '+tag,enc.drop=='first' and enc.min_frequency==50 and enc.max_categories==40 and enc.handle_unknown=='ignore')
            for col,cats in zip(block['categorical'],enc.categories_):check('Categories training-only '+tag+col,set(cats.tolist())==set(fit[col].unique().tolist()))
            with c.threadpool_limits(limits=2):matrix=tr.transform(fit[block['all']]);train_rate=b13['estimator'].predict(matrix)
            e=fit['e_cost_mix_1.0'].to_numpy(float);mu=e*train_rate;score=(np.sqrt(mu)-fit.T0.to_numpy()/np.sqrt(mu))/math.fsum(np.sqrt(e).tolist())
            grad=np.r_[np.asarray(matrix.T@score).ravel(),math.fsum(score.tolist())];mx=float(np.abs(grad).max())
            check('Independent GLM score '+tag,mx<=1e-4 and close(mx,receipt['max_abs_score_gradient']));gradient_records.append({'line':line,'fold':fold,'max_abs_score':mx})
            # First numeric effect, last effect and intercept finite differences against total-unit loss.
            if fold==0:
                eta=np.log(train_rate);h=1e-5
                for j in [0,matrix.shape[1]-1,matrix.shape[1]]:
                    z=np.ones(len(fit)) if j==matrix.shape[1] else np.asarray(matrix[:,j].toarray()).ravel() if hasattr(matrix,'toarray') else matrix[:,j]
                    plus=e*np.exp(eta+h*z);minus=e*np.exp(eta-h*z)
                    fd=(c.dev(fit.T0,plus).sum()-c.dev(fit.T0,minus).sum())/(4*h*np.sqrt(e).sum())
                    check('Finite difference total loss '+tag+str(j),abs(fd-grad[j])<2e-6)
            for mid,b in [('W2-B12',b12),('W2-B13',b13)]:
                p=ordered[mid];p=p[p.line.eq(line)&p.fold.eq(fold)].reset_index(drop=True)
                with c.threadpool_limits(limits=2):rr=pred(b,valid);mut=valid.assign(T0=0.,reserve=0.);rr2=pred(b,mut)
                check('Replay blocked fit '+mid+tag,valid[KEY].equals(p[KEY]) and close(rr,p.annual_rate))
                check('Response invariant '+mid+tag,np.array_equal(rr,rr2))
    check('Fit accounting',glm_count==15 and constant_count==30 and r['new_base_estimator_fits']==15 and r['new_closed_form_constants']==30 and r['new_postfit_factors']==0)
    for row in c.read(run/'diagnostics/segments.json'):
        if row['model_id'] not in new:continue
        p=ordered[row['model_id']];dim,label=row['segment'],row['label']
        if dim=='line':m=p.line.eq(label)
        elif dim=='fold':m=p.fold.astype(str).eq(label)
        elif dim=='business':m=p.x_new_business.eq(1 if label=='new_business' else 0)
        else:m=(p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal')).eq(label)
        sub=p[m];check('Segment '+row['model_id']+dim+label,close(row['D2'],c.d2_tweedie_score(sub.T0,sub.prediction,power=1.5)) and close(row['actual_over_expected'],sub.T0.sum()/sub.prediction.sum()))
    for row in c.read(run/'diagnostics/observation_sensitivity.json'):
        if row['model_id'] not in new:continue
        p=ordered[row['model_id']];name=row['scenario']
        yc,ec=('T1_reserve075','e_cost_mix_0.75') if name=='reserve075' else ('T1_reserve125','e_cost_mix_1.25') if name=='reserve125' else ('T0','e_cost_mix_tail0.05') if name=='late_cost05' else ('T0','e_cost_mix_tail0.1') if name=='late_cost10' else ('T0','e_cost_mix_1.0')
        check('Fixed-rate scenario '+row['model_id']+name,close(row['D2'],c.d2_tweedie_score(p[yc],p.annual_rate*p[ec],power=1.5)))
    groups,codes=np.unique(first.group_id,return_inverse=True);ng=len(groups);ids=list(ordered)
    n=np.bincount(codes).astype(float);y=np.bincount(codes,weights=first.T0);sy=np.bincount(codes,weights=np.sqrt(first.T0));loss=np.stack([np.bincount(codes,weights=c.dev(ordered[mid].T0,ordered[mid].prediction)) for mid in ids],axis=1)
    pairs=c.read(run/'diagnostics/pairs.json');saved=pq.read_table(run/'diagnostics/bootstrap_2023.parquet').to_pandas();oracle={};digest=hashlib.sha256();rng=np.random.default_rng(2026102302)
    # Only the new contrasts need numerical replay; source/artifact checks retain prior results.
    contrasts=[(x['candidate'],x['reference']) for x in pairs['pairs'] if x['candidate'] in new]
    for start in range(0,2000,32):
        draws=rng.integers(0,ng,size=(min(32,2000-start),ng),dtype=np.int64);digest.update(draws.tobytes());den=8*(np.sqrt(n[draws].sum(axis=1)*y[draws].sum(axis=1))-sy[draws].sum(axis=1));ls=loss[draws].sum(axis=1)
        for ca,ref in contrasts:oracle.setdefault((ca,ref),[]).extend(((ls[:,ids.index(ref)]-ls[:,ids.index(ca)])/den).tolist())
    check('Common draws checksum',digest.hexdigest()==pairs['draws_sha256'])
    for ca,ref in contrasts:
        row=next(x for x in pairs['pairs'] if x['candidate']==ca and x['reference']==ref);dist=np.array(oracle[ca,ref]);bs=saved[saved.candidate.eq(ca)&saved.reference.eq(ref)].sort_values('replicate').delta_D2
        check('New bootstrap pair '+ca+ref,close(bs,dist) and close([row['exploratory_lower95'],row['exploratory_upper95']],np.quantile(dist,[.025,.975])))
        gain=loss[:,ids.index(ref)]-loss[:,ids.index(ca)];k=np.ones(ng,dtype=bool);k[np.argsort(-gain,kind='stable')[:31]]=False;den=8*(np.sqrt(n[k].sum()*y[k].sum())-sy[k].sum())
        check('New point and influence '+ca+ref,close(row['delta_D2'],gain.sum()/(8*(np.sqrt(n.sum()*y.sum())-sy.sum()))) and close(row['delta_after_removal'],gain[k].sum()/den))
    check('No checker fit attempted',ATTEMPTS==0)
    result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','checker_sha256':c.sha(Path(__file__)),'producer_imported':False,'fit_attempts':ATTEMPTS,'checks':checks,
      'gradient_records':gradient_records,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'professional_independent_validation':False}
    out=run/'verifications';out.mkdir(exist_ok=True);dest=out/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json');dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verification':dest.relative_to(ROOT).as_posix(),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}));return int(result['failed']>0)
if __name__=='__main__':raise SystemExit(main())
