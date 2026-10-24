"""Diagnóstico de modelos congelados. No ajusta modelos ni propone un ganador."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util, sys, json, uuid
REPO=Path(__file__).resolve().parents[1]; ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('diag7_utils',REPO/'src/semana2/entrenar_desarrollo2023.py')
u=importlib.util.module_from_spec(s);sys.modules[s.name]=u;s.loader.exec_module(u)
np,pd,pq=u.np,u.pd,u.pq

def main():
    idx=u.read(REPO/'registro/semana2_desarrollo2023_actual.json');u.require(idx['id']=='S2-DEV2023-v6-20261023','Corte inesperado')
    parent=ROOT/idx['run'];old=ROOT/u.read(parent/'plan_snapshot.json')['parent_run']
    u.require(u.sha(parent/'oof_2023.parquet')==idx['oof_sha256'],'OOF cambiado')
    out=parent.parent/('revision_filas_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
    frozen=[parent/'oof_2023.parquet',parent/'manifest.json',Path(__file__)]
    oldo=pq.read_table(parent/'oof_2023.parquet',filters=[('model_id','in',['W2-B13','W2-B14','W2-B15'])]).to_pandas()
    u.assert_2023(oldo.drop_duplicates(u.KEY));rows=[];capital_folds=[];motor_folds=[]
    # No fit is permitted in this diagnostic, including preprocessing.
    def forbidden(*args,**kwargs):raise AssertionError('Fit prohibido en diagnóstico congelado')
    for cls in [u.TweedieRegressor,u.SimpleImputer,u.StandardScaler,u.OneHotEncoder,u.ColumnTransformer,u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    for fold in range(5):
        cred=u.read(parent/f'auxiliary/credibility_fold{fold}.json')['ramos']['motor']
        bm=u.joblib.load(parent/f'models/W2-B14_motor_fold{fold}/bundle.joblib')
        cols=bm['transformer'].get_feature_names_out().tolist();j=cols.index('numeric__x_new_business')
        scale=bm['transformer'].named_transformers_['numeric'].named_steps['scale'].scale_[0]
        price_theta=float(bm['estimator'].coef_[j]/scale)
        f=np.exp((1-cred['Z_f'])*(cred['theta_f_dev']-cred['theta_f_em']))
        sev=np.exp((1-cred['Z_s'])*(cred['theta_s_dev']-cred['theta_s_em']))
        motor_folds.append({'fold':fold,'theta_price':price_theta,'theta_auxiliary_total':cred['theta_em'],'theta_credible':cred['theta_cred'],
          'c_frequency':float(f),'c_severity':float(sev),'c_full':cred['c'],'product_error':float(f*sev-cred['c']),
          'direct_final_theta':price_theta+np.log(cred['c']),'replacement_c_diagnostic_only_not_scored':float(np.exp(cred['theta_cred']-price_theta))})
        for line in ['buildings','contents']:
            p=parent/f'variant_inputs/{line}_fold{fold}.parquet';frozen.append(p)
            frame=u.load_2023(p);fit=frame[frame.fold.ne(fold)];v=frame[frame.fold.eq(fold)].copy();a=v[v.audit_capital_pass].copy()
            base=u.load_2023(parent/f'inputs_2023/{line}.parquet').set_index('row_id')
            b0=u.joblib.load(old/f'models/W2-B13_{line}_fold{fold}/bundle.joblib');b1=u.joblib.load(parent/f'models/W2-B14_{line}_fold{fold}/bundle.joblib')
            def components(b):
                tr=b['transformer'];names=tr.get_feature_names_out().tolist();k=names.index('numeric__x_log_sum_insured')
                num=tr.named_transformers_['numeric'];z=list(tr.transformers_[0][2]).index('x_log_sum_insured')
                return float(b['estimator'].coef_[k]/num.named_steps['scale'].scale_[z]),float(num.named_steps['median'].statistics_[z])
            coef0,med0=components(b0);coef1,med1=components(b1)
            original=a.copy();original['x_log_sum_insured']=original.row_id.map(base.x_log_sum_insured)
            with u.threadpool_limits(limits=2):r0=u.predict_bundle(b0,original);rcf=u.predict_bundle(b0,a);r1=u.predict_bundle(b1,a)
            normal=fit.loc[~fit.audit_capital_suspect,'x_log_sum_insured'].dropna();lo,hi=float(normal.min()),float(normal.max())
            capital_folds.append({'line':line,'fold':fold,'old_logcapital_coefficient':coef0,'new_logcapital_coefficient':coef1,
              'old_training_imputation_log':med0,'new_training_imputation_log':med1,'normal_training_log_min':lo,'normal_training_log_max':hi,
              'affected_heldout':len(a),'corrected_outside_normal_fit_support':int((~a.x_log_sum_insured.between(lo,hi)).sum())})
            for i,(_,row) in enumerate(a.iterrows()):
                rows.append({'market':row.market,'line':line,'row_id':row.row_id,'year':2023,'fold':fold,'group_id':row.group_id,'T0':row.T0,
                  'capital_raw':row.sum_insured,'capital_divided':row.sum_insured/1000,'written_premium_audit_only':row.written_premium,
                  'corrected_log':row.x_log_sum_insured,'old_imputed_log':med0,'old_coefficient':coef0,'new_coefficient':coef1,
                  'in_normal_training_support':bool(lo<=row.x_log_sum_insured<=hi),'old_rate':r0[i],'fixed_B13_corrected_rate':rcf[i],'new_B14_rate':r1[i],
                  'direct_log_effect':float(np.log(rcf[i]/r0[i])),'refit_log_effect':float(np.log(r1[i]/rcf[i])),
                  'total_relative_change':float(r1[i]/r0[i]-1),'formula_error':float(np.log(rcf[i]/r0[i])-coef0*(row.x_log_sum_insured-med0)),
                  'old_prediction':row['e_cost_mix_1.0']*r0[i],'new_prediction':row['e_cost_mix_1.0']*r1[i]})
    detail=pd.DataFrame(rows);detail.to_parquet(out/'capital_56_rows.parquet',index=False)
    motor=oldo[oldo.line.eq('motor')&oldo.x_new_business.eq(1)].copy();a=motor[motor.model_id.eq('W2-B14')].sort_values(u.KEY).reset_index(drop=True);b=motor[motor.model_id.eq('W2-B15')].sort_values(u.KEY).reset_index(drop=True)
    u.require(a[u.KEY].equals(b[u.KEY]),'Claves motor distintas');a['loss_increase']=b.unit_deviance-a.unit_deviance;a['prediction_B15']=b.prediction;a['loss_B15']=b.unit_deviance
    parts=[]
    for dim,labels in [('fold',a.fold.astype(str)),('outcome',np.where(a.T0.gt(0),'positive','zero'))]:
        for label,cell in a.assign(label=labels).groupby('label'):
            parts.append({'dimension':dim,'label':str(label),'rows':len(cell),'observed':float(cell.T0.sum()),'prediction_B14':float(cell.prediction.sum()),
              'prediction_B15':float(cell.prediction_B15.sum()),'loss_increase':float(cell.loss_increase.sum()),'groups':int(cell.group_id.nunique())})
    groups=a.groupby('group_id',as_index=False).agg(loss_increase=('loss_increase','sum'),observed=('T0','sum'),rows=('row_id','size')).sort_values('loss_increase',ascending=False)
    groups.to_parquet(out/'motor_new_group_loss.parquet',index=False);a.to_parquet(out/'motor_new_row_loss.parquet',index=False)
    cg=[]
    for line,cell in detail.groupby('line'):
        cg.append({'line':line,'rows':len(cell),'out_of_fit_support':int((~cell.in_normal_training_support).sum()),'all_T0_zero':bool(cell.T0.eq(0).all()),
          'relative_change_min':float(cell.total_relative_change.min()),'relative_change_median':float(cell.total_relative_change.median()),'relative_change_max':float(cell.total_relative_change.max()),
          'direct_log_effect_abs_median':float(cell.direct_log_effect.abs().median()),'refit_log_effect_abs_max':float(cell.refit_log_effect.abs().max()),
          'direct_effect_sign_consistent':bool((np.sign(cell.direct_log_effect)==np.sign(cell.total_relative_change)).all()),
          'largest_increase':cell.sort_values('total_relative_change').iloc[-1].to_dict(),'largest_decrease':cell.sort_values('total_relative_change').iloc[0].to_dict()})
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'run':u.relative(out),'source_run':u.relative(parent),'new_fits':0,'new_trial_scores':0,
      'capital_summary':cg,'capital_folds':capital_folds,'motor_credibility_decomposition':motor_folds,'motor_loss_parts':parts,
      'motor_loss_increase_total':float(a.loss_increase.sum()),'motor_harm_top5_sum':float(groups.head(5).loss_increase.sum()),
      'motor_harm_top31_sum':float(groups.head(31).loss_increase.sum()),'motor_harmed_groups':int(groups.loss_increase.gt(0).sum()),
      'capital_formula_error_max':float(detail.formula_error.abs().max()),'only_year':2023,'confirmation_2024_open':False,
      'notice':'Frozen-model counterfactual capital representation, not fitted candidate or economic confirmation; coefficient replacement factors listed but not scored.'}
    u.require(len(detail)==56 and detail.T0.eq(0).all() and report['capital_formula_error_max']<1e-10,'Diagnóstico capital no concilia')
    u.dump(out/'report.json',report);u.dump(out/'sources.json',{'files':[{'path':u.relative(p),'sha256':u.sha(p)} for p in frozen]})
    print(json.dumps({'run':u.relative(out),'capital':[{k:v for k,v in r.items() if not k.startswith('largest_')} for r in cg],
      'motor_factors':motor_folds,'motor_loss_parts':parts,'motor_total_loss':report['motor_loss_increase_total'],'top5_harm':report['motor_harm_top5_sum']}))
if __name__=='__main__':main()
