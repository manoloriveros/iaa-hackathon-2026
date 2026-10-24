"""Oráculo independiente de capital, credibilidad y precio; sin importar productor."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib,math,re,argparse,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v6_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;ATTEMPTS=0
def forbidden(*a,**k):
    global ATTEMPTS
    ATTEMPTS+=1;raise AssertionError('Fit bloqueado en replay')
def text(series):return series.astype(object).where(series.notna(),'NA').map(str).to_numpy()
def design(frame,names):
    cols=[]
    for name in names:
        if name=='intercepto':col=np.ones(len(frame),dtype=np.float32)
        elif '=' in name:
            k,lv=name.split('=',1);col=(text(frame[k])==lv).astype(np.float32)
        else:col=frame[name].to_numpy(np.float32)
        cols.append(col)
    return np.column_stack(cols).astype(float)
def predict(bundle,f):
    assert f.year.eq(2023).all() and not f.is_test.any()
    if bundle['family']=='CredibilityRate':return c.predict(bundle['parent'],f)*np.where(f.x_new_business.eq(1),bundle['c'],1.)
    return c.predict(bundle,f)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    report=c.read(run/'report.json');plan=c.read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];checks=[];se_details=[]
    def check(n,v,detail=None):checks.append({'name':n,'pass':bool(v),'detail':detail})
    close=lambda a,b:np.allclose(a,b,rtol=2e-9,atol=1e-7,equal_nan=True)
    for it in c.read(run/'manifest.json')['files']:check('Artifact '+it['path'],c.sha(run/it['path'])==it['sha256'])
    for it in c.read(run/'frozen_sources_before_fit.json')['files']:check('Source '+it['path'],c.sha(ROOT/it['path'])==it['sha256'])
    check('Code frozen',c.sha(run/'code_snapshot.py')==report['code_sha256'] and c.sha(run/'auxiliary_code_snapshot.py')==report['auxiliary_code_sha256'] and c.sha(run/'plan_snapshot.json')==report['plan_sha256'])
    h=re.search(r'^## Codex \| COD-S2-20261023-018 \| ([^|]+) \|',(run/'forum_before_fit.md').read_text(encoding='utf-8'),re.M)
    check('Recipe before fit',h is not None and datetime.fromisoformat(h[1].strip())<datetime.fromisoformat(report['started_utc']))
    selection=c.read(REPO/'registro/semana2_seleccion_actual.json');check('2024 ledger absent',not (ROOT/selection['ledger_workspace_relative']).exists())
    check('2024/test closed',report['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and report['test_predictions']==0)
    check('No climate candidate',not report['climate']['candidate_admitted'] and report['climate']['prior_to_2023_rows_available']==0)
    check('B00 and no promotion',report['reference_retained']=='W2-B00' and not report['promotion'] and not report['final_confirmation_roster_frozen'])
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    old=pq.read_table(parent/'oof_2023.parquet').to_pandas();oof=pq.read_table(run/'oof_2023.parquet').to_pandas();ordered={m:p.sort_values(KEY).reset_index(drop=True) for m,p in oof.groupby('model_id')};first=ordered['W2-B00'];new=['W2-B14','W2-B15']
    check('Fourteen old OOF exact',oof[oof.model_id.isin(plan['comparators_reused_without_refit'])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)))
    check('Only unique2023 OOF',oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any())
    for mid,p in ordered.items():
        check('Same complete keys '+mid,len(p)==50094 and p[KEY].equals(first[KEY]))
        if mid in new:
            check('Same target/link '+mid,p.T0.equals(first.T0) and p['e_cost_mix_1.0'].equals(first['e_cost_mix_1.0']))
            check('Positive and exposure once '+mid,np.isfinite(p.annual_rate).all() and p.annual_rate.gt(0).all() and np.array_equal(p.prediction,p.annual_rate*p['e_cost_mix_1.0']))
            check('Unit deviance '+mid,close(p.unit_deviance,c.dev(p.T0,p.prediction)))
            point=next(x for x in report['summary'] if x['model_id']==mid);check('Global metric '+mid,close(point['D2'],c.d2_tweedie_score(p.T0,p.prediction,power=1.5)))
    prior=c.read(run/'auxiliary/developed_prior_snapshot.json');coeff=pd.read_csv(ROOT/'Hackaton/Semana 2/Claude/decisiones_20261023/tablas/coeficientes_glm_nb.csv')
    for line in ['motor','buildings','contents']:
        for comp in ['f','s']:
            subset=coeff[coeff.ramo.eq(line)&coeff.componente.eq(comp)&coeff.beta_dev.notna()&coeff.se_dev.notna()]
            check('Exact prior beta/SE '+line+comp,all(prior['prior'][line][comp][r.nivel]==r.beta_dev and prior['prior'][line][comp+'se'][r.nivel]==r.se_dev for _,r in subset.iterrows()))
    claims=pq.read_table(run/'auxiliary/positive_claim_source_2023.parquet').to_pandas();allfit={};aux_count=0;price_count=0
    for fold in range(5):
        for line in ['motor','buildings','contents']:
            tag=line+str(fold);olddata=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas();raw=pq.read_table(run/f'inputs_2023/raw_{line}.parquet').to_pandas();frame=pq.read_table(run/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas()
            check('Input2023 scope '+tag,frame.year.eq(2023).all() and not frame.is_test.any() and frame[KEY].equals(olddata[KEY]) and pd.to_datetime(raw.period_start).dt.year.eq(2023).all())
            check('Same source F0 '+tag,c.sha(run/f'inputs_2023/{line}.parquet')==c.sha(parent/f'inputs_2023/{line}.parquet'))
            fit=frame[frame.fold.ne(fold)];valid=frame[frame.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            for col in ['group_id','customer_id','address_id']:check('Disjoint '+tag+col,not set(fit[col])&set(valid[col]))
            if line!='motor':
                merged=olddata.merge(raw[['row_id','sum_insured','written_premium']],on='row_id',validate='one_to_one');threshold=plan['capital_rule']['thresholds'][line]
                normal=merged[merged.fold.ne(fold)&merged.sum_insured.gt(0)&merged.sum_insured.le(threshold)]
                ratios=[1000*float(p)/float(si) for p,si in zip(normal.written_premium,normal.sum_insured)];lo,hi=min(ratios),max(ratios)
                original=merged.x_log_sum_insured.to_numpy().copy();suspect=merged.sum_insured.gt(threshold).to_numpy();passed=[]
                for j,(si,wp) in enumerate(zip(merged.sum_insured,merged.written_premium)):
                    ok=si>threshold and 1000*wp/si<lo and lo<=1000000*wp/si<=hi;passed.append(ok)
                    if suspect[j]:original[j]=math.log(si/1000) if ok else np.nan
                check('Capital exact fit-bound rule '+tag,close(frame.x_log_sum_insured,original) and np.array_equal(frame.audit_capital_pass,passed))
                rec=next(x for x in report['capital'] if x['line']==line and x['fold']==fold)
                check('Capital bound receipt '+tag,close([lo,hi],[rec['fit_ppm_min'],rec['fit_ppm_max']]) and rec['normal_fit_row_ids_sha256']==hashlib.sha256('\n'.join(sorted(normal.row_id)).encode()).hexdigest())
                check('Other predictors unchanged '+tag,all(frame[col].equals(olddata[col]) for col in olddata if col.startswith('x_') and col!='x_log_sum_insured'))
            p14=run/'models'/f'W2-B14_{line}_fold{fold}/bundle.joblib';b14=c.joblib.load(p14);b15=c.joblib.load(run/'models'/f'W2-B15_{line}_fold{fold}/bundle.joblib')
            if line=='motor':check('Motor exact model reuse '+tag,c.sha(p14)==c.sha(parent/'models'/f'W2-B13_{line}_fold{fold}/bundle.joblib'))
            else:price_count+=1
            block=plan['core_recipe']['features_by_line'][line]
            check('Exact six-feature recipe '+tag,b14['columns']==block['all'] and all(b14['estimator'].get_params()[k]==v for k,v in plan['core_recipe']['params'].items()))
            num=b14['transformer'].named_transformers_['numeric'];x=fit[block['numeric']].to_numpy(float);med=np.nanmedian(x,axis=0);med=np.where(np.isnan(med),0,med);imputed=np.where(np.isnan(x),med,x)
            check('Price transforms fit-only '+tag,close(num.named_steps['median'].statistics_,med) and close(num.named_steps['scale'].mean_,imputed.mean(axis=0)))
            for mid,bundle in [('W2-B14',b14),('W2-B15',b15)]:
                p=ordered[mid];p=p[p.line.eq(line)&p.fold.eq(fold)].reset_index(drop=True)
                with c.threadpool_limits(limits=2):rr=predict(bundle,valid);rmut=predict(bundle,valid.assign(T0=0.,written_premium=-999.,reserve=0.))
                check('Blocked replay '+mid+tag,valid[KEY].equals(p[KEY]) and close(rr,p.annual_rate))
                check('No response/tariff pricing feature '+mid+tag,np.array_equal(rr,rmut))
            freq=pq.read_table(run/f'auxiliary/{line}_fold{fold}_frequency.parquet').to_pandas();sev=pq.read_table(run/f'auxiliary/{line}_fold{fold}_severity.parquet').to_pandas();detail=c.read(run/f'auxiliary/{line}_fold{fold}.json');allfit[line,fold]=detail['fit_summary']
            check('Aux fit exact outer-training rows '+tag,set(freq.row_id)==set(fit.row_id) and freq.year.eq(2023).all() and set(freq.group_id).isdisjoint(set(valid.group_id)))
            check('Aux clusters are graph components '+tag,freq.customer_id.equals(freq.group_id) and set(sev.customer_id)<=set(freq.group_id))
            canonical=claims[claims.line.eq(line)&claims.row_id.isin(fit.row_id)&claims.included_in_T0&claims.T0_cents.gt(0)].sort_values(['row_id','claim_id'])
            check('Canonical positive claims '+tag,len(sev)==len(canonical)==int(freq.n.sum()) and close(sorted(sev.net),sorted(canonical.T0_cents/100)))
            if line!='motor':
                expected=freq.row_id.map(fit.set_index('row_id').x_log_sum_insured);median=float(expected.median());expected=expected.fillna(median)
                check('Aux capital fit-only median/center '+tag,close(freq.log_si_raw,expected) and close(detail['capital_median_log'],median) and close(freq.log_si,expected-expected.mean()))
            # Rebuild the author's month-weighted exposure without importing its functions.
            months=[]
            for _,row in freq.iterrows():
                total=0.
                for month in range(1,13):
                    left=pd.Timestamp(2023,month,1);right=left+pd.offsets.MonthEnd(0);days=max(0,(min(pd.Timestamp(row.period_end),right)-max(pd.Timestamp(row.period_start),left)).days+1)
                    total+=days/365*detail['seasonality'][month-1]
                months.append(total)
            check('Independent seasonal exposure '+tag,close(freq.e_s,months) and close(detail['seasonality'],prior['seasonality'][line]))
            for comp,name in [('f','frequency'),('s','severity')]:
                names=detail[name+'_names'];capture=next(x for x in detail['estimates'] if x['family']==('poisson' if comp=='f' else 'gamma'));aux_count+=1
                if comp=='f':df=freq;yy=df.n.to_numpy(float);offset=np.log(df.e_s.to_numpy(float));clusters=df.group_id.to_numpy()
                else:
                    columns=list(dict.fromkeys([n.split('=',1)[0] for n in names if n!='intercepto']));df=sev.merge(freq[['row_id',*columns]],on='row_id',validate='many_to_one');yy=df.net.to_numpy(float);offset=np.zeros(len(df));clusters=df.customer_id.to_numpy()
                X=design(df,names);beta=np.array(capture['beta']);mu=np.exp(X@beta+offset);res=yy-mu if comp=='f' else (yy-mu)/mu
                grad=np.max(np.abs(X.T@res/len(df)));check('Independent auxiliary score '+tag+comp,grad<=1e-4 and capture['converged'] and close(grad,capture['mean_score_max']))
                group,codes=np.unique(clusters,return_inverse=True);S=np.column_stack([np.bincount(codes,weights=X[:,j]*res,minlength=len(group)) for j in range(X.shape[1])]);weight=mu if comp=='f' else np.ones(len(df))
                H=X.T@(weight[:,None]*X)+1e-8*np.eye(X.shape[1])
                with c.threadpool_limits(limits=2):solved=np.linalg.solve(H,S.T)
                standard=np.sqrt((solved*solved).sum(axis=1)*len(group)/(len(group)-1))
                check('Cluster sandwich independent solve '+tag+comp,np.allclose(standard,capture['se'],rtol=2e-3,atol=2e-5))
                check('Stored coefficient names '+tag+comp,close(list(detail['fit_summary'][comp].values()),beta) and close(list(detail['fit_summary'][comp+'se'].values()),capture['se']))
                se_details.append({'line':line,'fold':fold,'component':comp,'max_absolute_SE_difference':float(np.max(np.abs(standard-np.array(capture['se'])))),'matrix_condition':float(np.linalg.cond(H))})
        cred=c.read(run/f'auxiliary/credibility_fold{fold}.json');taus={}
        for comp in ['f','s']:
            terms=[]
            for line in ['motor','buildings','contents']:
                fe=allfit[line,fold];fd=prior['prior'][line]
                for key,beta in fe[comp].items():
                    if key in ['intercepto','nb','log_si'] or key.startswith('region=') or key not in fd[comp] or fe['conteos'].get(key,0)<100:continue
                    terms.append((beta-fd[comp][key])**2-fe[comp+'se'][key]**2-fd[comp+'se'][key]**2)
            tau=max(0.,math.fsum(terms)/len(terms)) if terms else 0.;taus[comp]=tau
            check('Tau training-only algebra '+str(fold)+comp,close(tau,cred['tau_'+comp]**2) and len(terms)==cred['niveles_tau_'+comp])
        for line in ['motor','buildings','contents']:
            fe=allfit[line,fold];fd=prior['prior'][line];theta=0.;z={}
            for comp in ['f','s']:
                z[comp]=taus[comp]/(taus[comp]+fe[comp+'se']['nb']**2) if taus[comp]+fe[comp+'se']['nb']**2 else 0.
                theta+=z[comp]*fe[comp]['nb']+(1-z[comp])*fd[comp]['nb']
            factor=math.exp(theta-fe['f']['nb']-fe['s']['nb']);rec=cred['ramos'][line];bundle=c.joblib.load(run/'models'/f'W2-B15_{line}_fold{fold}/bundle.joblib')
            check('Credibility c/Z application '+line+str(fold),close([factor,z['f'],z['s']],[bundle['c'],rec['Z_f'],rec['Z_s']]) and 0<=z['f']<=1 and 0<=z['s']<=1)
    check('Fit accounting',price_count==10 and aux_count==30 and report['new_developed_fits']==0 and report['new_credibility_factors']==15)
    for row in c.read(run/'diagnostics/segments.json'):
        if row['model_id'] not in new:continue
        p=ordered[row['model_id']];dim,label=row['segment'],row['label']
        if dim=='line':mask=p.line.eq(label)
        elif dim=='fold':mask=p.fold.astype(str).eq(label)
        elif dim=='business':mask=p.x_new_business.eq(1 if label=='new_business' else 0)
        else:mask=(p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new_business','renewal')).eq(label)
        sub=p[mask];check('Segment '+row['model_id']+dim+label,close(row['D2'],c.d2_tweedie_score(sub.T0,sub.prediction,power=1.5)) and close(row['actual_over_expected'],sub.T0.sum()/sub.prediction.sum()))
    for row in c.read(run/'diagnostics/observation_sensitivity.json'):
        if row['model_id'] not in new:continue
        p=ordered[row['model_id']];name=row['scenario'];yc,ec=('T1_reserve075','e_cost_mix_0.75') if name=='reserve075' else ('T1_reserve125','e_cost_mix_1.25') if name=='reserve125' else ('T0','e_cost_mix_tail0.05') if name=='late_cost05' else ('T0','e_cost_mix_tail0.1') if name=='late_cost10' else ('T0','e_cost_mix_1.0')
        check('Fixed-rate scenario '+row['model_id']+name,close(row['D2'],c.d2_tweedie_score(p[yc],p.annual_rate*p[ec],power=1.5)))
    groups,codes=np.unique(first.group_id,return_inverse=True);ng=len(groups);ids=list(ordered);n=np.bincount(codes).astype(float);y=np.bincount(codes,weights=first.T0);sy=np.bincount(codes,weights=np.sqrt(first.T0))
    losses=np.stack([np.bincount(codes,weights=c.dev(ordered[mid].T0,ordered[mid].prediction)) for mid in ids],axis=1);pairs=c.read(run/'diagnostics/pairs.json');bs=pq.read_table(run/'diagnostics/bootstrap_2023.parquet').to_pandas();contrasts=[(p['candidate'],p['reference']) for p in pairs['pairs'] if p['candidate'] in new]
    rng=np.random.default_rng(2026102302);digest=hashlib.sha256();oracle={}
    for start in range(0,2000,32):
        draw=rng.integers(0,ng,size=(min(32,2000-start),ng),dtype=np.int64);digest.update(draw.tobytes());den=8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-sy[draw].sum(axis=1));ls=losses[draw].sum(axis=1)
        for ca,ref in contrasts:oracle.setdefault((ca,ref),[]).extend(((ls[:,ids.index(ref)]-ls[:,ids.index(ca)])/den).tolist())
    check('Shared draws',digest.hexdigest()==pairs['draws_sha256'])
    for ca,ref in contrasts:
        pair=next(p for p in pairs['pairs'] if p['candidate']==ca and p['reference']==ref);dist=np.array(oracle[ca,ref]);saved=bs[bs.candidate.eq(ca)&bs.reference.eq(ref)].sort_values('replicate').delta_D2
        check('New bootstrap '+ca+ref,close(dist,saved) and close([pair['exploratory_lower95'],pair['exploratory_upper95']],np.quantile(dist,[.025,.975])))
        gain=losses[:,ids.index(ref)]-losses[:,ids.index(ca)];keep=np.ones(ng,dtype=bool);keep[np.argsort(-gain,kind='stable')[:31]]=False;den=8*(np.sqrt(n[keep].sum()*y[keep].sum())-sy[keep].sum())
        check('New influence '+ca+ref,close(pair['delta_after_removal'],gain[keep].sum()/den))
    check('No replay fit',ATTEMPTS==0)
    result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','checker_sha256':c.sha(Path(__file__)),'producer_imported':False,'fit_attempts':ATTEMPTS,'checks':checks,'SE_details':se_details,
      'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'professional_independent_validation':False}
    dest=run/'verifications';dest.mkdir(exist_ok=True);path=dest/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json');path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verification':path.relative_to(ROOT).as_posix(),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}));return int(result['failed']>0)
if __name__=='__main__':raise SystemExit(main())
