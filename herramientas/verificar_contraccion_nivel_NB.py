"""Verificacion numerica y replay de NB-CRED300, sin volver a ajustar la receta."""
from pathlib import Path
import importlib.util,json,math,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.metrics import d2_tweedie_score,mean_tweedie_deviance
from threadpoolctl import threadpool_limits
s=importlib.util.spec_from_file_location('NB_trial',R/'herramientas/probar_contraccion_nivel_NB.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def main():
    m.guard();result=m.w.read(m.OUT/'results.json');params=m.w.read(m.OUT/'parameters.json');tr=pd.read_parquet(m.OUT/'training_new_layer.parquet')
    t=pd.read_parquet(m.OUT/'predictions2024.parquet');label=pd.read_parquet(m.ACTIVE/'target2024_sealed.parquet').set_index('row_id').y;y=t.row_id.map(label).to_numpy(float)
    pars=params['params'];checks={};optimizers={}
    for line in m.LINES:
        g=tr[tr.line.eq(line)];mu=g.mu_afterF2shape.to_numpy();target=g.y.to_numpy();record=pars[line];expected=record['lambda_ramo']
        fit=minimize_scalar(lambda loglevel:mean_tweedie_deviance(target,mu*np.exp(loglevel),power=1.5),bounds=(-10,10),method='bounded',options={'xatol':1e-10})
        relative=abs(math.exp(fit.x)/expected-1);assert fit.success and relative<1e-6
        derivative=float(np.sum(target/np.sqrt(mu))-expected*np.sum(np.sqrt(mu)))
        assert abs(derivative)/max(1,float(np.sum(target/np.sqrt(mu))))<1e-12
        n=int(((g.y>0)&g.new_business.eq(1)).sum());z=n/(n+300)
        alternate=record['lambda_NB_original']**z*expected**(1-z)
        assert n==record['npositive_NB'] and math.isclose(alternate,record['lambda_NB_cred'],rel_tol=3e-14)
        optimizers[line]={'verification_only_optimum':float(math.exp(fit.x)),'registered_optimum':expected,'relative_error':relative,'derivative_residual':derivative,'success':bool(fit.success)}
    checks['three_ramo_optima_sklearn_scalar_optimizer']=True;checks['three_geometric_levels_by_weighted_power']=True
    quote=m.apply_new_layer(t,t.R1.to_numpy(),pars);poisoned=m.apply_new_layer(t.assign(y=999999999.),t.R1.to_numpy(),pars)
    checks['saved_parameter_replay_exact']=np.array_equal(quote,t.candidate.to_numpy())
    checks['held_y_application_poison_exact']=np.array_equal(quote,poisoned)
    nb=t.new_business.eq(1).to_numpy();checks['renewal_exact_all_rows']=np.array_equal(t.candidate.to_numpy()[~nb],t.R1.to_numpy()[~nb])
    checks['subset_singleton_order_exact']=np.array_equal(m.apply_new_layer(t.iloc[::-1],t.R1.to_numpy()[::-1],pars)[::-1],quote) and all(np.array_equal(m.apply_new_layer(t.iloc[[i]],t.R1.to_numpy()[i:i+1],pars),quote[i:i+1]) for i in range(0,len(t),701))
    prices={'R1':t.R1.to_numpy(),'full':t.F3c_reaprendido.to_numpy(),'baseline':t.sin_factores.to_numpy(),'candidate':quote}
    point_error=0.
    masks={'global':np.ones(len(t),bool),'new_business':nb,'renewal':~nb,**{l:t.line.eq(l).to_numpy() for l in m.LINES},
        **{l+'_'+str(b):t.line.eq(l).to_numpy()&(nb==b) for l in m.LINES for b in [0,1]}}
    for name,mask in masks.items():
        scores={k:d2_tweedie_score(y[mask],v[mask],power=1.5) for k,v in prices.items()}
        point_error=max(point_error,abs(scores['candidate']-result['metrics'][name]['D2_candidate']))
        for comp in m.COMPS:point_error=max(point_error,abs(scores['candidate']-scores[comp]-result['metrics'][name]['delta_vs_'+comp]))
    checks['point_metrics_sklearn']=point_error<3e-12
    new=np.load(m.OUT/'bootstrap_new_statistics.npz');original=np.load(m.REVIEW/'policy_bootstrap.npz');draws=new['delta']
    assert np.array_equal(new['segments'],original['segments']);assert str(original['views'][0])=='T2b'
    e0=np.max(np.abs((draws[:,:,2]-draws[:,:,0])-original['delta'][:,:,0,0]));e1=np.max(np.abs((draws[:,:,1]-draws[:,:,0])-original['delta'][:,:,0,1]))
    checks['all10000_original_contrast_identities']=bool(max(e0,e1)<3e-12)
    groups=m.a.groups(t);universe,ix=np.unique(groups,return_inverse=True);counts=np.load(m.OUT/'first20_original_group_counts.npy')
    weights=np.load(m.ACTIVE/'composition_bootstrap_T2b.npz')['weights'];boot_error=0.
    for i,count in enumerate(counts):
        row=count[ix]
        for name,ww in [('global',np.ones(len(t))),('new_business',nb),('mix2025_global',weights),('mix2025_new_business',weights*nb)]:
            weight=row*ww;scores={k:d2_tweedie_score(y,v,power=1.5,sample_weight=weight) for k,v in prices.items()};si=list(new['segments']).index(name)
            for ci,comp in enumerate(m.COMPS):boot_error=max(boot_error,abs(scores['candidate']-scores[comp]-draws[i,si,ci]))
    checks['20_cached_bootstrap_draws_sklearn']=boot_error<3e-12
    stressed=m.w.read(m.OUT/'fixed_price_stresses.json');stress_error=0.
    assert len(stressed['scenarios'])==50
    for i,record in enumerate(stressed['scenarios']):
        ys=np.load(m.ACTIVE/'scenarios'/f'{i:02d}.npz')['y']
        for name in ['global','new_business','buildings']:
            mask=masks[name];scores={k:d2_tweedie_score(ys[mask],v[mask],power=1.5) for k,v in prices.items()}
            for comp in ['R1','baseline']:stress_error=max(stress_error,abs(scores['candidate']-scores[comp]-record['metrics'][name]['delta_vs_'+comp]))
    checks['all50_fixed_stress_metrics_sklearn']=stress_error<3e-12
    attempts=[json.loads(x) for x in (m.OUT/'fit_attempts.jsonl').read_text().splitlines()];tagcounts={tag:sum(z['tag']==tag for z in attempts) for tag in sorted({z['tag'] for z in attempts})}
    checks['fit_budget_exact']=tagcounts=={'held2024_poison':3,'primary':3,'synthetic':3,'train_positive_control':3}
    checks['real_changed_layer_scope_control']=all(params['checks'][key] for key in ['held2024_poison_nonvacuous','new_params_exact_under_held_poison','train_positive_control_changes_params','original_recipe_hash_unchanged','saved_OOF_folds_preserved'])
    checks['no_2025_or_upload_file']=not list(m.OUT.glob('*.csv'))
    checks['original_R1_F3c_preserved']=m.w.sha(m.F3)==m.w.read(m.PLAN)['sources'][m.w.rel(m.F3)] and m.w.sha(m.R1)==m.w.read(m.PLAN)['sources'][m.w.rel(m.R1)]
    m.guard();checks['all_passed']=all(checks.values())
    output={'author':'Codex','utc':m.utc(),'checks':checks,'optimizer_checks':optimizers,'point_max_error':point_error,'bootstrap20_max_error':boot_error,
        'original10000_identity_max_error':float(max(e0,e1)),'stress_max_error':stress_error,'fit_attempt_counts':tagcounts,'verification_only_scalar_optimizations':3,
        'new_pricing_fits_by_verifier':0,'new_native_or_CDF_fits':0,'new_bootstrap_draws':0,'professional_independent_review':False,'verifier_sha256':m.w.sha(Path(__file__))}
    m.dump(m.OUT/'verification.json',output);assert checks['all_passed'],checks
    print(json.dumps({'all_passed':True,'point_max_error':point_error,'bootstrap20_max_error':boot_error,'original10000_identity_max_error':float(max(e0,e1)),'stress_max_error':stress_error,'optimizer_checks':optimizers}),flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=2):main()
