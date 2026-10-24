"""Inspección de la tanda guardada: errores, coeficientes y soporte de hojas."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys,uuid

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('checker_brechas',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
out=run.parent/('revision_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
    cls.fit=c.forbid_fit
    if hasattr(cls,'fit_transform'):cls.fit_transform=c.forbid_fit
oof=pq.read_table(run/'oof_2023.parquet').to_pandas();assert oof.year.eq(2023).all()
build=pq.read_table(run/'inputs_2023/buildings.parquet').to_pandas()
b0=oof.loc[oof.model_id.eq('W2-B00')&oof.line.eq('buildings')].sort_values(c.KEY).reset_index(drop=True)
b1=oof.loc[oof.model_id.eq('W2-B01')&oof.line.eq('buildings')].sort_values(c.KEY).reset_index(drop=True)
assert b0[c.KEY].equals(b1[c.KEY]);base_null=float(c.dev(b0.T0,np.full(len(b0),b0.T0.mean())).sum())
compare=b1.merge(b0[c.KEY+['prediction','unit_deviance']],on=c.KEY,suffixes=('','_reference'),validate='one_to_one')
compare=compare.merge(build[c.KEY+['x_log_sum_insured','x_region','x_construction_type','x_property_type']],on=c.KEY,validate='one_to_one')
compare['loss_advantage']=compare.unit_deviance_reference-compare.unit_deviance
compare['cost_band']=pd.cut(compare.T0,[-.1,0,5000,50000,200000,np.inf],labels=['zero','0_to_5000','5000_to_50000','50000_to_200000','above_200000'])
compare['capital_known']=np.where(compare.x_log_sum_insured.isna(),'unknown','known')
compare['prediction_ratio_band']=pd.cut(compare.prediction/compare.prediction_reference,[0,.25,.5,1,2,np.inf],include_lowest=True).astype(str)
segments=[]
for col in ['cost_band','capital_known','x_region','x_construction_type','x_property_type','fold','prediction_ratio_band']:
    for label,part in compare.groupby(col,observed=True,dropna=False):
        segments.append({'dimension':col,'segment':str(label),'rows':len(part),'positive_rows':int(part.T0.gt(0).sum()),
          'observed':float(part.T0.sum()),'predicted_GLM':float(part.prediction.sum()),'predicted_reference':float(part.prediction_reference.sum()),
          'delta_D2_contribution_full_buildings_null':float(part.loss_advantage.sum()/base_null),
          'loss_reference':float(part.unit_deviance_reference.sum()),'loss_GLM':float(part.unit_deviance.sum())})
private_rows=compare.sort_values('loss_advantage').head(25)
pq.write_table(c.pq.read_table(run/'oof_2023.parquet').slice(0,0),out/'schema_only_oof.parquet')
private_rows.to_parquet(out/'buildings_worst_rows.parquet',index=False)
groups=compare.groupby('group_id',sort=True).loss_advantage.sum().sort_values()
influence=[]
for n in [1,5,31]:
    influence.append({'remove_most_adverse_groups':n,'removed_advantage':float(groups.iloc[:n].sum()),
          'remaining_advantage_over_original_null':float(groups.iloc[n:].sum()/base_null),
          'interpretation':'Diagnostic removal only; original untrimmed objective retained'})
coefs=[];leaves=[];lgb_fit=[]
for line in ['motor','buildings','contents']:
    data=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas();assert data.year.eq(2023).all() and not data.is_test.any()
    for fold in range(5):
        link=pq.read_table(run/f'links_2023/{line}_fold{fold}.parquet').to_pandas()
        fit=data.merge(link[c.KEY+['e_cost_mix_1.0']],on=c.KEY,validate='one_to_one').loc[lambda x:x.fold.ne(fold)]
        if line=='buildings':
            b=c.joblib.load(run/'models'/f'W2-B01_{line}_fold{fold}'/'bundle.joblib')
            names=b['transformer'].get_feature_names_out()
            coefs.extend({'fold':fold,'feature':str(name),'coefficient':float(value)} for name,value in zip(names,b['estimator'].coef_))
        b=c.joblib.load(run/'models'/f'W2-B02_{line}_fold{fold}'/'bundle.joblib')
        x=fit[b['columns']].copy()
        for col,levels in b['categories'].items():x[col]=pd.Categorical(x[col].astype(str),categories=levels)
        with c.threadpool_limits(limits=2):
            r=c.predict(b,fit);pred=r*fit['e_cost_mix_1.0'].to_numpy()
            leaf=b['estimator'].booster_.predict(x,pred_leaf=True,start_iteration=299,num_iteration=1).reshape(-1).astype(int)
        positive=fit.T0.gt(0).to_numpy();leaf_n=np.bincount(leaf);leaf_pos=np.bincount(leaf,weights=positive)
        observed_leaves=np.unique(leaf)
        leaves.append({'line':line,'fold':fold,'tree_index':299,'leaves':len(observed_leaves),
          'minimum_rows_in_leaf':int(leaf_n[observed_leaves].min()),'minimum_positive_rows_in_leaf':int(leaf_pos[observed_leaves].min()),
          'median_positive_rows_in_leaf':float(np.median(leaf_pos[observed_leaves])),
          'training_rows_in_leaves_with_at_most_5_positive':int(leaf_n[leaf_pos<=5].sum())})
        lgb_fit.append({'line':line,'fold':fold,'positive_training_rows':int(positive.sum()),
          'observed_total':float(fit.T0.sum()),'predicted_total':float(pred.sum()),
          'train_rate_p10':float(np.quantile(r,.1)),'train_rate_p90':float(np.quantile(r,.9))})
coef=pd.DataFrame(coefs);coef.to_parquet(out/'buildings_coefficients.parquet',index=False)
pivot=coef.pivot(index='feature',columns='fold',values='coefficient').fillna(0)
stability=pd.DataFrame({'mean':pivot.mean(axis=1),'std':pivot.std(axis=1),'min':pivot.min(axis=1),'max':pivot.max(axis=1)})
stability['sign_changes']=stability['min'].lt(-.05)&stability['max'].gt(.05)
stability.sort_values('std',ascending=False).to_csv(out/'buildings_coefficient_stability.csv')
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'parent_run':str(run.relative_to(ROOT)),
 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fit_calls':0,'year':2023,
 'buildings_GLM_segments':segments,'buildings_influence':influence,
 'buildings_coefficients_most_variable':stability.sort_values('std',ascending=False).head(12).reset_index().to_dict('records'),
 'boosting_last_tree_support':leaves,'boosting_fit':lgb_fit,
 'limits':['Outcome and removal segments are descriptive, not filters for training or final metric','A single terminal tree is a support diagnostic, not a causal explanation of forest error','No prefix scores, calibration factors or new recipe fits were computed'],
 'scope_2024':'closed; no price prediction or score'}
(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'review':str(out.relative_to(ROOT)),'buildings_cost_segments':[x for x in segments if x['dimension'] in ['cost_band','capital_known']],
 'influence':influence,'variable_coefficients':result['buildings_coefficients_most_variable'][:5],
 'leaf_support':leaves},ensure_ascii=True))
