"""Comprobacion independiente del diagnostico, sin estimar un nuevo precio."""
from pathlib import Path
import importlib.util,json,math,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance,d2_tweedie_score
s=importlib.util.spec_from_file_location('bdiag',R/'herramientas/diagnosticar_prior_edificios_NB.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    m.guard();x=m.w.read(m.OUT/'results.json');t=pd.read_parquet(m.OUT/'buildings_period_diagnostic.parquet');c=pd.read_parquet(m.OUT/'buildings_claim_diagnostic.parquet');checks={};err=0.;graderr=0.
    for z in x['cohorts']:
        f=t[t.year.eq(z['year'])&t.new_business.eq(z['NB'])];y=f.y.to_numpy();old=f.R1.to_numpy();new=f.candidate.to_numpy()
        delta=float(d2_tweedie_score(y,new,power=1.5)-d2_tweedie_score(y,old,power=1.5));err=max(err,abs(delta-z['delta_D2']))
        raw=(mean_tweedie_deviance(y,old,power=1.5)-mean_tweedie_deviance(y,new,power=1.5))*len(y)
        assert math.isclose(raw,z['cost_term']+z['price_only_term'],rel_tol=2e-11,abs_tol=1e-7)
        eps=1e-6;fd=(mean_tweedie_deviance(y,old*np.exp(eps),power=1.5)-mean_tweedie_deviance(y,old*np.exp(-eps),power=1.5))*len(y)/(2*eps)
        analytic=z['gradient_dDeviance_dLogPrice'];scaled=abs(fd-analytic)/max(1,abs(analytic));graderr=max(graderr,scaled)
        assert scaled<1e-3
    checks['sklearn_cohort_D2_and_loss_split']=err<3e-12;checks['finite_difference_gradient']=graderr<1e-3
    n=t[t.year.eq(2024)&t.new_business];reference=m.w.read(m.TRIAL/'results.json')['metrics']['buildings_1']['delta_vs_R1']
    check_delta=d2_tweedie_score(n.y,n.candidate,power=1.5)-d2_tweedie_score(n.y,n.R1,power=1.5);checks['prior_failed_result_preserved']=abs(check_delta-reference)<3e-12
    claims=c.groupby('row_id').net.sum();checks['all_period_T0_cents_reconciled']=np.array_equal(np.rint(t.row_id.map(claims).fillna(0).to_numpy()*100).astype('int64'),np.rint(t.y.to_numpy()*100).astype('int64'))
    checks['paid_net_plus_reserve_net_exact']=np.max(abs(c.net_paid+c.reserve-c.net))<1e-7
    checks['peril_cost_term_sums_reconcile']=all(abs(sum(v['cost_gain_term'] for v in x['peril_cost_terms'] if v['year']==z['year'] and v['NB']==z['NB'])-z['cost_term'])<1e-7 for z in x['cohorts'])
    checks['claim_cost_term_same_as_period']=all(abs(z['cost_term_from_claims']-z['cost_term_from_periods'])<1e-7 for z in x['claim_timing'])
    checks['claim_paid_and_reserve_gain_parts_reconcile']=all(abs(z['paid_part_of_gain']+z['reserve_part_of_gain']-z['cost_term_from_claims'])<1e-7 for z in x['claim_timing'])
    checks['NB_folds_reconcile_total_gain']=abs(sum(v['gain_deviance'] for v in x['saved_2024_NB_folds'])-n.loss_gain.sum())<1e-7
    yorder=pd.read_parquet(m.TRIAL/'predictions2024.parquet',columns=['row_id']);mask=yorder.row_id.isin(n.row_id).to_numpy();n=n.set_index('row_id').loc[yorder.row_id[mask]]
    stress_error=0.
    for i,record in enumerate(x['fixed_stress_NB_buildings']):
        y=np.load(m.ACTIVE/'scenarios'/f'{i:02d}.npz')['y'][mask];score=d2_tweedie_score(y,n.candidate,power=1.5)-d2_tweedie_score(y,n.R1,power=1.5);stress_error=max(stress_error,abs(score-record['delta_D2_buildings_NB']))
    checks['all50_new_NB_slice_metrics_sklearn']=stress_error<3e-12
    checks['future_exposure_shares_sum1']=abs(sum(v['exposure_share'] for v in x['2025_exposure_only'])-1)<1e-12
    checks['no_new_submission_csv']=not list(m.OUT.glob('*.csv'))
    m.guard();checks['original_sources_and_models_unchanged']=True;checks['all_passed']=all(checks.values())
    output={'author':'Codex','utc':m.utc(),'checks':checks,'point_max_error':err,'gradient_relative_or_abs_scale_error':graderr,'stress_max_error':stress_error,
        'new_fitted_constants':0,'new_models_or_curves':0,'new_2025_quotes':0,'new_submissions':0,'review_scope':'computational own review, not independentprofessional or private-performance confirmation','verifier_sha256':m.w.sha(Path(__file__))}
    m.dump(m.OUT/'verification.json',output);assert checks['all_passed'],checks
    print(json.dumps({'all_passed':True,'point_max_error':err,'stress_max_error':stress_error,'gradient_error':graderr}),flush=True)
if __name__=='__main__':main()
