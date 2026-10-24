"""Oráculo separado del escalar Tweedie y del estrés; replay con fit bloqueado."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,math,argparse,uuid,re
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('v4_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY
ATTEMPTS=0
def forbidden(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('No se entrena en replay')
def anchored(b,f):return .5*b['reference_rate']+.5*b['scale']*c.predict(b['parent'],f)
def business(b,f):return anchored(b['parent'],f)*np.array([b['factors'][int(x)] for x in f.x_new_business])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();run=Path(a.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    report=c.read(run/'report.json');plan=c.read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];checks=[]
    def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
    close=lambda a,b:np.allclose(a,b,rtol=2e-10,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in c.read(run/'frozen_sources_before_fit.json')['files']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Code and plan snapshots',c.sha(run/'code_snapshot.py')==report['code_sha256'] and c.sha(run/'plan_snapshot.json')==report['plan_sha256'])
    header=re.search(r'^## Codex \| COD-S2-20261023-014 \| ([^|]+) \|',(run/'forum_before_fit.md').read_text(encoding='utf-8'),re.M)
    check('Preregistration before fitting',header is not None and datetime.fromisoformat(header[1].strip())<datetime.fromisoformat(report['started_utc']))
    check('2024/test closed',report['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and report['test_predictions']==0)
    selection=c.read(REPO/'registro/semana2_seleccion_actual.json');check('Ledger absent',not (ROOT/selection['ledger_workspace_relative']).exists())
    check('B00 preserved, no promotion',report['reference_retained']=='W2-B00' and not report['promotion'] and not report['final_confirmation_roster_frozen'])
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    old=pq.read_table(parent/'oof_2023.parquet').to_pandas();oof=pq.read_table(run/'oof_2023.parquet').to_pandas();stress=pq.read_table(run/'stress_oof_2023.parquet').to_pandas()
    check('Ten old recipes exact',oof[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)))
    check('Unique 2023 OOF',oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any() and stress.year.eq(2023).all() and not stress.duplicated(['model_id',*KEY]).any())
    first=old[old.model_id.eq('W2-B00')].sort_values(KEY).reset_index(drop=True)
    ordered={mid:p.sort_values(KEY).reset_index(drop=True) for mid,p in oof.groupby('model_id')}
    sordered={mid:p.sort_values(KEY).reset_index(drop=True) for mid,p in stress.groupby('model_id')}
    for mid,p in {**ordered,**sordered}.items():
        check('Original complete keys '+mid,len(p)==50094 and p[KEY].equals(first[KEY]))
        if mid in ['W2-B10','W2-B11','S00','S08']:
            check('Observed T0 and C0 '+mid,p.T0.equals(first.T0) and p['e_cost_mix_1.0'].equals(first['e_cost_mix_1.0']))
            check('Positive and single offset '+mid,p.annual_rate.gt(0).all() and np.isfinite(p.annual_rate).all() and np.array_equal(p.prediction,p.annual_rate*p['e_cost_mix_1.0']))
            check('General formula unit loss '+mid,close(p.unit_deviance,c.dev(p.T0,p.prediction)))
            row=next(r for r in report['summary']+report['stress_summary'] if r['model_id']==mid)
            check('sklearn D2 '+mid,close(row['D2'],c.d2_tweedie_score(p.T0,p.prediction,power=1.5)))
    data={line:pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas() for line in ['motor','buildings','contents']}
    ready=c.read(run/'readiness_snapshot.json');blocks=c.read(ROOT/ready['availability_contract'])['blocks'];factor_count=0;glm_count=0
    for fold in range(5):
        pool=pd.concat([d[d.fold.ne(fold)] for d in data.values()],ignore_index=True)
        # Different implementation: Python dictionary accumulation and tuple ordering.
        totals={}
        for gid,y in zip(pool.group_id,pool.T0):totals.setdefault(gid,[]).append(float(y))
        rank=sorted(totals,key=lambda g:(-math.fsum(totals[g]),str(g)));excluded=set(rank[:math.ceil(len(rank)*.001)])
        saved=pq.read_table(run/f'stress_groups/fold{fold}.parquet').to_pandas()
        check('Training-only complete-group stress ranking '+str(fold),set(saved.group_id)==excluded and len(saved)==math.ceil(len(rank)*.001))
        check('Stress disjoint held-out components '+str(fold),not excluded&set(first.loc[first.fold.eq(fold),'group_id']))
        for line,d in data.items():
            tag=line+str(fold);check('Original input '+tag,c.sha(run/f'inputs_2023/{line}.parquet')==c.sha(parent/f'inputs_2023/{line}.parquet') and d.year.eq(2023).all() and not d.is_test.any())
            lp=run/f'links_2023/{line}_fold{fold}.parquet';links=pq.read_table(lp).to_pandas();ecols=[x for x in links if x.startswith('e_cost_')]
            check('Frozen 2023 C0 '+tag,c.sha(lp)==c.sha(parent/f'links_2023/{line}_fold{fold}.parquet') and links.year.eq(2023).all())
            f=d.merge(links[KEY+ecols],on=KEY,validate='one_to_one');fit=f[f.fold.ne(fold)];valid=f[f.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            for col in ['group_id','customer_id','address_id']:check('Disjoint '+tag+col,not set(fit[col])&set(valid[col]))
            for mid,pid in [('W2-B10','W2-B08'),('W2-B11','W2-B09')]:
                folder=run/'models'/f'{mid}_{line}_fold{fold}';b=c.joblib.load(folder/'bundle.joblib');r=c.read(folder/'receipt.json')
                source=parent/'models'/f'{pid}_{line}_fold{fold}/bundle.joblib';base=c.joblib.load(source)
                check('Exact parent source '+mid+tag,r['parent_sha256']==c.sha(source))
                # Check the embedded native model and adapter against the source, before evaluating q.
                check('Embedded adapter unchanged '+mid+tag,all(b['parent'][k]==base[k] for k in ['scale','reference_rate','shape_weight']))
                raw1,raw2=b['parent']['parent'],base['parent']
                if raw1['family']=='TweedieRegressor':same=np.array_equal(raw1['estimator'].coef_,raw2['estimator'].coef_) and raw1['estimator'].intercept_==raw2['estimator'].intercept_
                else:same=raw1['estimator'].booster_.model_to_string()==raw2['estimator'].booster_.model_to_string()
                check('Embedded estimator unchanged '+mid+tag,same)
                with c.threadpool_limits(limits=2):rate=anchored(base,fit);replay=business(b,valid)
                mu=fit['e_cost_mix_1.0'].to_numpy()*rate
                for biz in [0,1]:
                    m=fit.x_new_business.eq(biz).to_numpy();y=fit.T0.to_numpy()[m];mm=mu[m]
                    num=math.fsum((y/np.sqrt(mm)).tolist());den=math.fsum(np.sqrt(mm).tolist());q=num/den;factor_count+=1
                    check('Training scalar oracle '+mid+tag+str(biz),close(q,b['factors'][biz]) and q>0)
                    check('Training scalar derivative '+mid+tag+str(biz),abs(math.fsum((np.sqrt(q*mm)-y/np.sqrt(q*mm)).tolist()))<1e-6)
                    check('Scalar training minimum '+mid+tag+str(biz),c.dev(y,q*mm).sum()<=min(c.dev(y,mm).sum(),c.dev(y,q*.99*mm).sum(),c.dev(y,q*1.01*mm).sum())+1e-6)
                p=ordered[mid];p=p[p.line.eq(line)&p.fold.eq(fold)].reset_index(drop=True)
                check('Replay blocked fit '+mid+tag,close(replay,p.annual_rate) and valid[KEY].equals(p[KEY]))
                altered=valid.copy();altered.T0=0.;altered.reserve=0.
                with c.threadpool_limits(limits=2):check('Prediction does not read response '+mid+tag,np.array_equal(replay,business(b,altered)))
            reduced=fit[~fit.group_id.isin(excluded)];folder=run/'stress_models'/f'{line}_fold{fold}';b=c.joblib.load(folder/'bundle.joblib');rec=c.read(folder/'receipt.json')
            glm_count+=1;e=reduced['e_cost_mix_1.0'].to_numpy();q=math.fsum((reduced.T0/np.sqrt(e)).tolist())/math.fsum(np.sqrt(e).tolist())
            check('Stress constant oracle '+tag,close(q,b['S00']['rate']) and b['S08']['reference_rate']==b['S00']['rate'])
            check('Stress rows and scope '+tag,rec['remaining_fit_rows']==len(reduced) and rec['deleted_groups']==len(excluded) and rec['original_C0_fixed'])
            native=b['S08']['parent'];est=native['estimator'];check('Stress recipe convergence '+tag,est.alpha==(10. if line=='buildings' else 1.) and est.power==1.5 and est.n_iter_<2000 and native['columns']==blocks[line]['all'])
            transform=native['transformer'];numeric=transform.named_transformers_['numeric'];imputer=numeric.named_steps['median'];scaler=numeric.named_steps['scale']
            x=reduced[blocks[line]['numeric']].to_numpy(float);med=np.nanmedian(x,axis=0);med=np.where(np.isnan(med),0,med)
            check('Stress imputer training only '+tag,close(imputer.statistics_,med))
            imputed=np.where(np.isnan(x),med,x);check('Stress scaler training only '+tag,close(scaler.mean_,imputed.mean(axis=0)) and close(scaler.var_,imputed.var(axis=0)))
            with c.threadpool_limits(limits=2):raw=c.predict(native,reduced);rp=anchored(b['S08'],valid);r0=c.predict(b['S00'],valid)
            scale=math.fsum((e*q).tolist())/math.fsum((e*raw).tolist());check('Stress anchor oracle '+tag,close(scale,b['S08']['scale']))
            for mid,rr in [('S00',r0),('S08',rp)]:
                p=sordered[mid];p=p[p.line.eq(line)&p.fold.eq(fold)].reset_index(drop=True);check('Stress replay '+mid+tag,valid[KEY].equals(p[KEY]) and close(rr,p.annual_rate))
    check('Fit/factor accounting',factor_count==60 and glm_count==15 and report['new_candidate_base_fits']==0 and report['stress_glm_fits']==15 and report['stress_constants']==15)
    # Rebuild new segment/scenario metrics; previous recipes already have frozen verification.
    for path,table in [('segments.json',ordered),('stress_segments.json',sordered)]:
        for row in c.read(run/'diagnostics'/path):
            mid=row['model_id']
            if mid not in ['W2-B10','W2-B11','S00','S08']:continue
            p=table[mid];dim=row['segment'];label=row['label']
            if dim=='line':m=p.line.eq(label)
            elif dim=='fold':m=p.fold.astype(str).eq(label)
            elif dim=='business':m=p.x_new_business.eq(1 if label=='new_business' else 0)
            else:m=(p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal')).eq(label)
            sub=p[m];check('Segment '+mid+dim+label,close(row['D2'],c.d2_tweedie_score(sub.T0,sub.prediction,power=1.5)) and close(row['actual_over_expected'],sub.T0.sum()/sub.prediction.sum()))
    scenarios={'T0':('T0','e_cost_mix_1.0'),'reserve075':('T1_reserve075','e_cost_mix_0.75'),'reserve125':('T1_reserve125','e_cost_mix_1.25'),'late_cost05':('T0','e_cost_mix_tail0.05'),'late_cost10':('T0','e_cost_mix_tail0.1')}
    # Read actual frozen scenario names from the archived v1 source contract, using no producer import.
    for path,table in [('observation_sensitivity.json',ordered),('stress_scenarios.json',sordered)]:
        for row in c.read(run/'diagnostics'/path):
            if row['model_id'] not in ['W2-B10','W2-B11','S00','S08']:continue
            name=row['scenario'];p=table[row['model_id']]
            if '075' in name:ycol,ecol='T1_reserve075','e_cost_mix_0.75'
            elif '125' in name:ycol,ecol='T1_reserve125','e_cost_mix_1.25'
            elif '05' in name:ycol,ecol='T0','e_cost_mix_tail0.05'
            elif '10' in name:ycol,ecol='T0','e_cost_mix_tail0.1'
            else:ycol,ecol='T0','e_cost_mix_1.0'
            check('Fixed rate observation '+row['model_id']+name,close(row['D2'],c.d2_tweedie_score(p[ycol],p.annual_rate*p[ecol],power=1.5)))
    ids=list(ordered);groups,codes=np.unique(first.group_id,return_inverse=True);ng=len(groups);n=np.bincount(codes).astype(float);y=np.bincount(codes,weights=first.T0);sy=np.bincount(codes,weights=np.sqrt(first.T0))
    losses=np.stack([np.bincount(codes,weights=c.dev(ordered[mid].T0,ordered[mid].prediction)) for mid in ids],axis=1)
    null=c.dev(first.T0,np.repeat(first.T0.mean(),len(first))).sum();boot=pq.read_table(run/'diagnostics/bootstrap_2023.parquet').to_pandas();pairs=c.read(run/'diagnostics/pairs.json')
    rng=np.random.default_rng(2026102302);digest=hashlib.sha256();oracle={}
    for start in range(0,2000,32):
        draw=rng.integers(0,ng,size=(min(32,2000-start),ng),dtype=np.int64);digest.update(draw.tobytes())
        den=8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-sy[draw].sum(axis=1));ls=losses[draw].sum(axis=1)
        for b in range(len(ids)):
            for a in range(b+1,len(ids)):oracle.setdefault((ids[a],ids[b]),[]).extend(((ls[:,b]-ls[:,a])/den).tolist())
    check('Common draw checksum',digest.hexdigest()==pairs['draws_sha256'])
    for pair in pairs['pairs']:
        ca,refid=pair['candidate'],pair['reference'];a,b=ids.index(ca),ids.index(refid);dist=np.array(oracle[ca,refid]);saved=boot[boot.candidate.eq(ca)&boot.reference.eq(refid)].sort_values('replicate').delta_D2
        check('Paired bootstrap '+ca+refid,close(dist,saved) and close([pair['exploratory_lower95'],pair['exploratory_upper95']],np.quantile(dist,[.025,.975])))
        gain=losses[:,b]-losses[:,a];remove=np.argsort(-gain,kind='stable')[:31];keep=np.ones(ng,dtype=bool);keep[remove]=False;den=8*(np.sqrt(n[keep].sum()*y[keep].sum())-sy[keep].sum())
        check('Point and own group removal '+ca+refid,close(pair['delta_D2'],gain.sum()/null) and close(pair['delta_after_removal'],gain[keep].sum()/den))
    for row in report['frozen_parent_influence']:
        gain=losses[:,ids.index('W2-B00')]-losses[:,ids.index(row['parent'])];removed=set(groups[np.argsort(-gain,kind='stable')[:31]])
        p=ordered[row['model_id']];m=~p.group_id.isin(removed);check('Frozen parent removal '+row['model_id'],close(row['delta_D2_after_removal'],c.d2_tweedie_score(p.loc[m,'T0'],p.loc[m,'prediction'],power=1.5)-c.d2_tweedie_score(first.loc[m,'T0'],first.loc[m,'prediction'],power=1.5)))
    check('No fit attempted in independent replay',ATTEMPTS==0)
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checker_sha256':c.sha(Path(__file__)),'producer_imported':False,'fit_attempts':ATTEMPTS,
      'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
    folder=run/'verifications';folder.mkdir(exist_ok=True);dest=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json');dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verification':dest.relative_to(ROOT).as_posix(),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}))
    return int(result['failed']>0)

if __name__=='__main__':raise SystemExit(main())
