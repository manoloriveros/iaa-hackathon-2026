"""Contracción y nivel B20/B19 sobre componentes fijados; solo replay2023."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys,uuid

REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from threadpoolctl import threadpool_limits
from sklearn.linear_model import TweedieRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

KEY=['market','line','row_id'];E='e_cost_mix_1.0'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def require(ok,msg):
    if not bool(ok):raise ValueError(msg)


def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False,default=lambda v:v.item() if hasattr(v,'item') else str(v));f.write('\n')


def block_fit():
    def forbidden(*a,**k):raise RuntimeError('B20 diagnostic forbids fitting')
    for cls in [TweedieRegressor,SimpleImputer,StandardScaler,OneHotEncoder,ColumnTransformer,Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden


def guard(frame):
    require(len(frame)>0 and frame.year.eq(2023).all(),'Empty/non2023 diagnostic scope')
    require(frame[KEY].notna().all().all(),'Missing period key')
    require(not frame.duplicated(KEY).any(),'Duplicate period keys')
    if 'is_test' in frame:require(not frame.is_test.any(),'Test forbidden')
    require(np.isfinite(frame[E]).all() and frame[E].gt(0).all(),'Nonpositive/nonfinite C0 exposure')


def pair_guard(a,b):
    guard(a);guard(b)
    require(len(a)==len(b)==50094,'Incomplete paired OOF')
    for col in KEY+['year','fold','group_id','T0','reserve','exposure','x_new_business',E]:
        require(a[col].equals(b[col]),'Pair changed '+col)


def transforms_equal(a,b):
    require(a['columns']==b['columns'],'Different predictors')
    ta,tb=a['transformer'],b['transformer']
    require(np.array_equal(ta.get_feature_names_out(),tb.get_feature_names_out()),'Different transformed coding')
    for step,attrs in [('median',['statistics_']),('scale',['mean_','var_','scale_','n_samples_seen_'])]:
        for attr in attrs:
            x=getattr(ta.named_transformers_['numeric'][step],attr);y=getattr(tb.named_transformers_['numeric'][step],attr)
            require(np.array_equal(x,y,equal_nan=True),'Different training transform '+step+'.'+attr)
    ea,eb=ta.named_transformers_['categorical'],tb.named_transformers_['categorical']
    require(len(ea.categories_)==len(eb.categories_) and all(np.array_equal(x,y) for x,y in zip(ea.categories_,eb.categories_)),'Different OHE levels')
    require(np.array_equal(ea.drop_idx_,eb.drop_idx_),'Different OHE reference')
    require(all(x is None for x in ea.infrequent_categories_) and all(x is None for x in eb.infrequent_categories_),'Rare coding not comparable')


def materialize(planpath):
    block_fit();p=read(planpath)
    run=REPO/'privado/semana2/desarrollo2023'/('contraccion_b20_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);run.mkdir()
    (run/'plan_snapshot.json').write_bytes(planpath.read_bytes());(run/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});require(ok,name)
    try:
        for x in p['frozen_sources']:check('Frozen source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
        forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
        check('Diagnostic registered before calculation',forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1)
        b20=pq.read_table(ROOT/p['b20_oof']).to_pandas().sort_values(KEY).reset_index(drop=True)
        b19=pq.read_table(ROOT/p['b19_oof'],filters=[('model_id','=','W2-B19')]).to_pandas().sort_values(KEY).reset_index(drop=True)
        check('Model IDs exact',set(b20.model_id)=={'W2-B20'} and set(b19.model_id)=={'W2-B19'})
        pair_guard(b20,b19);check('Full saved2023 metadata and C0 identical',True)
        fixed=pq.read_table(ROOT/p['fixed_periods'],columns=KEY+['group_id','fold','year','T0','x_new_business']).to_pandas().sort_values(KEY).reset_index(drop=True)
        selected=b19.merge(fixed[KEY],on=KEY,how='inner',validate='one_to_one').sort_values(KEY).reset_index(drop=True)
        check('Exactly original20periods/12groups',len(fixed)==len(selected)==20 and fixed.group_id.nunique()==12)
        for col in KEY+['group_id','fold','year','T0','x_new_business']:check('Fixed cohort exact '+col,np.array_equal(selected[col].to_numpy(),fixed[col].to_numpy()))
        f=b19[KEY+['year','fold','group_id','T0','x_new_business','exposure',E]].copy()
        for mid,table in [('B19',b19),('B20',b20)]:
            for col in ['annual_rate','prediction','unit_deviance']:f[mid+'_'+col]=table[col]
        f['saved_deviance_gain_B20']=f.B19_unit_deviance-f.B20_unit_deviance
        focus=f.merge(fixed[KEY],on=KEY,validate='one_to_one').sort_values(KEY).reset_index(drop=True)
        focus.to_parquet(run/'fixed_period_comparison_2023.parquet',index=False)
        groups=focus.groupby(['group_id','line','fold'],as_index=False).agg(rows=('T0','size'),T0=('T0','sum'),B19_prediction=('B19_prediction','sum'),B20_prediction=('B20_prediction','sum'),saved_deviance_gain_B20=('saved_deviance_gain_B20','sum'))
        groups['prediction_ratio_B20_B19']=groups.B20_prediction/groups.B19_prediction
        groups.to_parquet(run/'fixed_group_comparison_2023.parquet',index=False)
        def level(cell):
            old=float(cell.B19_prediction.sum());new=float(cell.B20_prediction.sum())
            return {'rows':len(cell),'groups':int(cell.group_id.nunique()),'observed_T0':float(cell.T0.sum()),
                    'B19_observed_bridge_total':old,'B20_observed_bridge_total':new,'observed_bridge_ratio_B20_B19':new/old,
                    'B19_nominal_total':float((cell.exposure*cell.B19_annual_rate).sum()),
                    'B20_nominal_total':float((cell.exposure*cell.B20_annual_rate).sum()),
                    'saved_deviance_gain_B20':float(cell.saved_deviance_gain_B20.sum())}
        levels=[{'dimension':'global','label':'all2023',**level(f)},{'dimension':'fixed_union','label':'same12groups20periods',**level(focus)}]
        for dim,labels in [('line',f.line),('business',np.where(f.x_new_business.eq(1),'new','renewal')),('line_business',f.line+'_'+np.where(f.x_new_business.eq(1),'new','renewal')),('fold',f.fold.astype(str))]:
            for label,cell in f.assign(label=labels).groupby('label',sort=True):levels.append({'dimension':dim,'label':str(label),**level(cell)})
        reasons=pq.read_table(ROOT/p['selection_reasons']).to_pandas()
        for scope,line in [('buildings','buildings'),('motor_new','motor')]:
            ids=set(reasons.loc[reasons.reason.eq('OOF_top5_adverse_'+scope),'group_id'])
            cell=focus[focus.group_id.isin(ids)&focus.line.eq(line)]
            levels.append({'dimension':'fixed_OOF_top5','label':scope,**level(cell)})
        dump(run/'level_diagnostics_2023.json',levels)
        spec=importlib.util.spec_from_file_location('rawcoef_saved',ROOT/p['coefficient_helper']);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        norms=[];coefs=[];decomp=[]
        for line in ['motor','buildings','contents']:
            for fold in range(5):
                old=joblib.load(ROOT/p['b19_run']/f'models/W2-B19_{line}_fold{fold}/bundle.joblib')
                new=joblib.load(ROOT/p['b20_run']/f'models/{line}_fold{fold}/bundle.joblib')
                transforms_equal(old,new);check('Identical saved training transforms '+line+str(fold),True)
                po=old['estimator'].get_params();pn=new['estimator'].get_params()
                check('Only alpha changed '+line+str(fold),po.pop('alpha')==0 and pn.pop('alpha')==1 and po==pn)
                bo=old['estimator'].coef_;bn=new['estimator'].coef_
                no=float(np.linalg.norm(bo));nn=float(np.linalg.norm(bn))
                norms.append({'line':line,'fold':fold,'coordinates':len(bo),'B19_std_L2':no,'B20_std_L2':nn,'relative_norm_reduction':1-nn/no if no>0 else None,
                              'absolute_coordinates_larger':int((np.abs(bn)>np.abs(bo)+1e-10).sum()),
                              'std_intercept_B19':float(old['estimator'].intercept_),'std_intercept_B20':float(new['estimator'].intercept_),
                              'joint_norm_contracts':nn<=no+1e-10})
                coefs.extend(helper.coef_raw(old,line,fold,'W2-B19'));coefs.extend(helper.coef_raw(new,line,fold,'W2-B20'))
                expected=focus[focus.line.eq(line)&focus.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
                if not len(expected):continue
                frame=pq.read_table(ROOT/p['b19_run']/f'inputs_2023/{line}_fold{fold}.parquet',filters=[('row_id','in',expected.row_id.tolist())]).to_pandas().sort_values(KEY).reset_index(drop=True)
                guard(frame);check('Replay selected heldout keys '+line+str(fold),frame[KEY].equals(expected[KEY]) and frame.fold.eq(fold).all())
                with threadpool_limits(limits=2):
                    xo=old['transformer'].transform(frame[old['columns']]);xn=new['transformer'].transform(frame[new['columns']])
                    xo=xo.toarray() if hasattr(xo,'toarray') else np.asarray(xo);xn=xn.toarray() if hasattr(xn,'toarray') else np.asarray(xn)
                    check('Selected transformed rows exact '+line+str(fold),np.array_equal(xo,xn))
                    ro=old['estimator'].predict(xo);rn=new['estimator'].predict(xn)
                check('B19 selected replay '+line+str(fold),np.allclose(ro,expected.B19_annual_rate,rtol=5e-13,atol=1e-10))
                check('B20 selected replay '+line+str(fold),np.allclose(rn,expected.B20_annual_rate,rtol=5e-13,atol=1e-10))
                names=old['transformer'].get_feature_names_out().tolist()
                cov=[j for j,name in enumerate(names) if name.startswith('categorical__x_cover_type_')] if line=='motor' else [names.index('numeric__x_accidental_damage_cover')]
                nb=[names.index('numeric__x_new_business')];other=[j for j in range(len(names)) if j not in cov+nb]
                d=bn-bo;intercept=float(new['estimator'].intercept_-old['estimator'].intercept_)
                terms={'delta_coverage':xo[:,cov]@d[cov],'delta_newbusiness':xo[:,nb]@d[nb],'delta_other_main_effects':xo[:,other]@d[other]}
                total=intercept+sum(terms.values());logratio=np.log(rn/ro)
                check('Exact native log-rate decomposition '+line+str(fold),np.allclose(total,logratio,rtol=1e-11,atol=1e-11))
                for j,row in expected.iterrows():
                    decomp.append({**{key:row[key] for key in KEY+['group_id','fold']},'delta_intercept':intercept,
                        **{key:float(value[j]) for key,value in terms.items()},'delta_log_rate':float(total[j]),
                        'existing_prediction_ratio_B20_B19':float(row.B20_prediction/row.B19_prediction)})
        pd.DataFrame(norms).to_parquet(run/'standardized_coefficient_norms.parquet',index=False)
        pd.DataFrame(coefs).to_parquet(run/'coefficients_original_scale.parquet',index=False)
        pd.DataFrame(decomp).to_parquet(run/'fixed_period_logratio_decomposition.parquet',index=False)
        check('Twenty native decomposition rows',len(decomp)==20)
        check('Fifteen coefficient pair comparisons',len(norms)==15)
        oldreport=read(ROOT/p['b20_run']/'report.json');summary={x['model_id']:x for x in oldreport['summary']}
        gain=summary['W2-B19']['deviance_sum']-summary['W2-B20']['deviance_sum'];selectedgain=float(focus.saved_deviance_gain_B20.sum())
        attribution={'saved_global_deviance_gain_B20':gain,'fixed_group_saved_gain':selectedgain,'remaining_group_saved_gain':gain-selectedgain,
                     'fixed_gain_over_global_net_gain':selectedgain/gain if abs(gain)>1e-12 else None,
                     'ratio_is_share_of_net_gain_not_gross_or_probability':True,'no_new_group_ranking_or_removal':True}
        check('Saved global gain consistency',np.isclose(f.saved_deviance_gain_B20.sum(),gain,rtol=1e-11,atol=1e-6))
        dump(run/'fixed_gain_attribution.json',attribution)
        report={'id':p['id'],'author':'Codex','completed_utc':datetime.now(timezone.utc).isoformat(),'run':rel(run),'passed':len(checks),'failed':0,'checks':checks,
                'coefficient_pairs':15,'fixed_groups':12,'fixed_periods':20,'native_replay_rows_per_model':20,
                'norm_contracting_pairs':int(sum(x['joint_norm_contracts'] for x in norms)),
                'successful_fit_calls':0,'new_models':0,'new_price_recipes':0,'new_price_predictions':0,
                'existing_prediction_replay_only':True,'new_bootstrap':0,'new_global_D2_or_CI':False,
                'reference':'W2-B00','all_alternatives_preserved':True,'ledger_read':False,'policy_years':[2023],
                'professional_independent_validation':False}
        dump(run/'report.json',report)
        paths=[x for x in run.rglob('*') if x.is_file()]
        dump(run/'manifest.json',{'files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths)]})
        print(json.dumps({k:report[k] for k in ['run','passed','failed','coefficient_pairs','fixed_periods','norm_contracting_pairs','successful_fit_calls']}))
        return run
    except Exception as exc:
        dump(run/'failure.json',{'error':str(exc),'run':rel(run),'checks':checks,'successful_fit_calls':0,'new_bootstrap':0});raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);materialize(Path(parser.parse_args().plan).resolve())
