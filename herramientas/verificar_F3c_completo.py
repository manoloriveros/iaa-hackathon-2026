"""Comprobaciones por otra implementación para F3c completo, sin reajuste real."""
from pathlib import Path
import argparse,importlib.util,json,math,sys
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('F3c_evaluator_verify',R/'herramientas/evaluar_F3c_completo.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
np=e.np;pd=e.pd;OUT=e.OUT;dump=e.dump;read=e.read;sha=e.sha

def independent_factor(t,mu,p,var):
    maps={(unit,key):z for unit,key,z in p['factors']};out=[];cell=e.v.cells(t);key=e.v.ks(t,var)
    for i in range(len(t)):
        unit=cell[i] if p['kind']=='ae' else str(t.line.iloc[i]);out.append(float(mu[i])*maps.get((unit,str(key[i])),1.))
    out=np.asarray(out)
    for cc in sorted(set(cell)):
        ids=np.flatnonzero(cell==cc);c=math.fsum(float(mu[i]) for i in ids)/math.fsum(float(out[i]) for i in ids)
        for i in ids:out[i]*=c
    return out

def independent_shape(t,mu,powers):
    cell=e.v.cells(t);out=np.array(mu,copy=True);ef=(t.exposure*t.q).to_numpy()
    for cc,power in powers.items():
        ids=np.flatnonzero(cell==cc)
        if not len(ids):continue
        total=math.fsum(float(mu[i]) for i in ids);expo=math.fsum(float(ef[i]) for i in ids);mean=total/expo
        raw=[float(ef[i])*mean*math.exp(power*math.log(float(mu[i])/float(ef[i])/mean)) for i in ids];normal=total/math.fsum(raw)
        for i,z in zip(ids,raw):out[i]=z*normal
    return out

def synthetic():
    e.guard();rng=np.random.default_rng(20261028);n=360
    t=pd.DataFrame({'line':np.repeat(e.LINES,n//3),'new_business':np.tile(np.repeat([0,1],30),6),'exposure':rng.uniform(.1,1,n),'q':rng.uniform(.6,1,n),
        'gender':np.tile(['M','F','X'],120),'works_from_home':np.tile([True,False],180),'marketing_segment':np.tile(['a','b','c','d'],90),'ncb_years':np.tile(np.arange(12),30),
        'prior_claims_5y':np.tile([0,1,2],120),'y':rng.gamma(2,20,n),'year':2023,'row_id':['synthetic'+str(i) for i in range(n)]})
    t['T2b_raw']=rng.lognormal(3,1,n);t['mix']=rng.lognormal(3,1,n);e.ROLE='synthetic';params=e.learn_recipe(t);quotes=e.apply_recipe(t,params);checks={}
    for i,p in enumerate(params['F2']+params['own']):
        x=t['mix'].to_numpy();auto=e.batch_factor(t,x,p,p['variable']);manual=independent_factor(t,x,p,p['variable']);checks['factor_'+str(i)]=bool(np.allclose(auto,manual,rtol=3e-14,atol=1e-10))
        for cc in set(e.v.cells(t)):
            j=e.v.cells(t)==cc;assert math.isclose(math.fsum(auto[j]),math.fsum(x[j]),rel_tol=3e-14)
    shapes={'motor_0':.9,'motor_1':1.37,'contents_1':1.05};checks['shape_manual']=bool(np.allclose(e.batch_shape(t,t['mix'].to_numpy(),shapes),independent_shape(t,t['mix'].to_numpy(),shapes),rtol=3e-14,atol=1e-10))
    checks['recipe_all_positive']=all(np.isfinite(q).all() and (q>0).all() for q in quotes.values())
    bad=t.assign(year=2024)
    try:e.learn_recipe(bad)
    except AssertionError:checks['reject_target_year_training']=True
    else:checks['reject_target_year_training']=False
    from scipy.optimize import minimize_scalar
    y=t.y.to_numpy();mu=t['mix'].to_numpy();k=e.original_kopt(y,mu);opt=minimize_scalar(lambda x:math.fsum(e.audit.loss(y,mu*math.exp(x))),bounds=(math.log(k)-2,math.log(k)+2),method='bounded',options={'xatol':1e-12})
    checks['scalar_optimization']=math.isclose(k,math.exp(opt.x),rel_tol=3e-7)
    from sklearn.metrics import mean_tweedie_deviance
    checks['sklearn_metric']=math.isclose(mean_tweedie_deviance(y,mu,power=1.5),math.fsum(e.audit.loss(y,mu))/n,rel_tol=1e-12)
    checks['all_passed']=all(checks.values());dump(OUT/'evaluator_synthetic.json',{'utc':e.f.utc(),'checks':checks,'synthetic_analytical_counts':dict(e.COUNTS),'synthetic_numerical_optimizations':1,'new_real_fits':0});assert checks['all_passed'];print(json.dumps(checks))

def verify():
    e.guard();checks={};models=[]
    for line in e.LINES:
        for family in ['N0','F1']:
            for seed in e.f.SEEDS:
                base=read(OUT/'source'/line/'baseline'/f'{family}_seed{seed}'/'complete.json');replay=read(OUT/'source'/line/'poison2024'/f'{family}_seed{seed}'/'complete.json')
                for key in ['arguments_sha256','model_sha256','raw_sha256','rounds','source_center']:assert base[key]==replay[key],(line,family,seed,key)
                assert sha(e.f.ROOT/base['model'])==base['model_sha256'] and sha(e.f.ROOT/base['raw'])==base['raw_sha256']
                expect={'motor':49,'buildings':41,'contents':42}[line]+(2 if family=='F1' else 0);assert len(base['columns'])==expect
                model=e.f.lgb.Booster(model_file=str(e.f.ROOT/base['model']));assert list(model.feature_name())==base['columns'];del model
                models.append({'line':line,'family':family,'seed':seed,'features':expect,'rounds':base['rounds'],'reused':base['reused']})
    checks['all18_source_models_and18_replays_verified']=True
    checks['60_real_source_fits_recorded']=sum(len((OUT/('fit_attempts_'+line+'.jsonl')).read_text().splitlines()) for line in e.LINES)==60
    tr=pd.read_parquet(OUT/'training2023.parquet');te=pd.read_parquet(OUT/'predictions2024.parquet');pars=read(OUT/'parameters.json')['recipe'];replay=e.apply_recipe(te,pars)
    checks['saved_prediction_replay_exact']=all(np.array_equal(te[n],replay[n]) for n in e.NAMES)
    # Independent factor/shape implementation on real2024 values, without learning.
    x=te['mix'].to_numpy()
    for p in pars['F2']+pars['own']:
        assert np.allclose(e.batch_factor(te,x,p,p['variable']),independent_factor(te,x,p,p['variable']),rtol=5e-14,atol=1e-8)
    checks['all_real_factor_stages_scalar_math']=True
    checks['real_shape_scalar_math']=bool(np.allclose(e.batch_shape(te,x,{'motor_0':.9,'motor_1':1.37}),independent_shape(te,x,{'motor_0':.9,'motor_1':1.37}),rtol=5e-14,atol=1e-8))
    labels=pd.read_parquet(OUT/'labels2024.parquet').set_index('row_id').y;y=te.row_id.map(labels).to_numpy();result=read(OUT/'results.json');from sklearn.metrics import d2_tweedie_score
    for n in e.NAMES:assert math.isclose(result['metrics']['global']['D2'][n],d2_tweedie_score(y,te[n],power=1.5),rel_tol=2e-12,abs_tol=2e-14)
    checks['all_global_metrics_sklearn']=True
    groups=e.audit.groups(te);universe,ix=np.unique(groups,return_inverse=True);counts=np.load(OUT/'first20_group_counts.npy');pack=np.load(OUT/'bootstrap.npz');draws=pack['delta'];nms=pack['comparisons'].tolist()
    for b in range(20):
        ww=counts[b,ix]
        for c,(candidate,ref) in enumerate(e.COMPS):
            direct=e.metric(y,te[candidate].to_numpy(),ww)-e.metric(y,te[ref].to_numpy(),ww);assert math.isclose(direct,float(draws[b,0,c]),rel_tol=1e-9,abs_tol=1e-12)
    checks['20_bootstrap_draws_direct_weighted_metrics']=True
    comp=read(e.f.LEGACY.parent/'comparacion_final.json')['comparisons'];checks['exact_full_production_retraining_receipt']=comp['F3c']['bytes_exact'] and comp['A1fixF1b3n']['bytes_exact']
    checks['delivered_F3c_hash_preserved']=sha(e.f.ORIGINAL)==sha(e.f.LEGACY/'m017/exp26/F3c_2025.csv')==e.f.ORIGINAL_SHA
    checks['all_passed']=all(checks.values());dump(OUT/'verification.json',{'author':'Codex','utc':e.f.utc(),'checks':checks,'source_models':models,'verifier_code_sha256':sha(Path(__file__)),'new_real_fits':0,'new2025model_inferences':0,'new_submissions':0});assert checks['all_passed'];print(json.dumps(checks),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('mode',choices=['synthetic','verify']);args=p.parse_args()
    with e.threadpool_limits(limits=2):globals()[args.mode]()
