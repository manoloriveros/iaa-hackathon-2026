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

def verify_factor_learning(t,mu,p,var,lines=None):
    cell=e.v.cells(t);key=e.v.ks(t,var);y=t.y.to_numpy();actual={(u,k):z for u,k,z in p['factors']};ref=mu.copy()
    if p['kind']=='tw':
        for cc in np.unique(cell):
            j=cell==cc;ref[j]*=math.fsum((y[j]/np.sqrt(ref[j])).tolist())/math.fsum(np.sqrt(ref[j]).tolist())
    units=np.unique(cell) if p['kind']=='ae' else lines
    expected={}
    for unit in units:
        i=cell==unit if p['kind']=='ae' else t.line.eq(unit).to_numpy()
        base=math.fsum(y[i].tolist())/math.fsum(mu[i].tolist())
        for label in np.unique(key[i]):
            j=i&(key==label);n=int((y[j]>0).sum())
            if p['kind']=='ae':z=1+n/(n+300)*(math.fsum(y[j].tolist())/math.fsum(mu[j].tolist())/base-1)
            elif n:z=math.exp(n/(n+300)*math.log(max(math.fsum((y[j]/np.sqrt(ref[j])).tolist())/math.fsum(np.sqrt(ref[j]).tolist()),1e-3)))
            else:continue
            expected[(unit,str(label))]=z
    assert expected.keys()==actual.keys()
    assert all(math.isclose(z,actual[k],rel_tol=5e-14,abs_tol=1e-14) for k,z in expected.items())

def independent_recipe(t,p):
    bridge=t.q.to_numpy().copy();u=t.copy();u['q']=1.;base=t['mix'].to_numpy()/bridge
    cell=e.v.cells(t);pb=read(e.f.PLAN)['preprocessing_full_structure']['public_blocks']
    def scale(mu,d):return np.asarray([float(x)*d[c] for x,c in zip(mu,cell)])
    def f2(mu):
        for fac in p['F2']:mu=independent_factor(u,mu,fac,fac['variable'])
        return independent_shape(u,mu,{'motor_0':.9})
    def own(mu):
        for fac in p['own']:mu=independent_factor(u,mu,fac,fac['variable'])
        return scale(mu,p['own_ratio'])
    public=scale(f2(base*pb['g']),p['F2_ratio']);public=independent_shape(u,public,{line+'_1':z for line,z in pb['NB_shapes'].items()});public=scale(scale(public,p['shape_ratio']),pb['cell_level_relative_to_g'])
    secondary=scale(f2(base),p['F2_ratio'])
    return {'public_noown':public*bridge,'public_full':own(public)*bridge,'trainlevel_noown':scale(secondary,p['secondary_levels']['noown'])*bridge,'trainlevel_full':scale(own(secondary),p['secondary_levels']['full'])*bridge}

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

def bridge():
    e.guard();e.ROLE='synthetic_bridge';rng=np.random.default_rng(20261028);n=120
    t=pd.DataFrame({'line':np.repeat(e.LINES,40),'new_business':np.tile(np.repeat([0,1],20),3),'exposure':rng.uniform(.1,1,n),'q':rng.uniform(.6,1,n),
        'gender':np.tile(['M','F'],60),'works_from_home':np.tile([True,False],60),'marketing_segment':np.tile(['a','b','c'],40),'ncb_years':np.tile(np.arange(12),10),
        'prior_claims_5y':np.tile([0,1,2],40),'y':rng.gamma(2,20,n),'year':2023,'row_id':['toy'+str(i) for i in range(n)]})
    t['T2b_raw']=rng.lognormal(3,1,n);t['mix']=rng.lognormal(3,1,n);p=e.learn_recipe(t);pred=e.apply_recipe(t,p);manual=independent_recipe(t,p)
    checks={'full_independent_pipeline_variable_q':all(np.allclose(pred[k],manual[k],rtol=2e-13,atol=1e-9) for k in pred)}
    u=t.copy();u['mix']=t['mix']/t.q;u['q']=1.;ultimate=e.apply_recipe(u,p)
    checks['ultimate_before_final_observed_bridge']=all(np.allclose(pred[k],ultimate[k]*t.q.to_numpy(),rtol=2e-14,atol=1e-10) for k in pred)
    oldlines=e.LINES;oldscope=e.base_scope
    def fixture(em,raw,F,fold,style,balance=False):
        z=pd.DataFrame({'row_id':['f'+str(fold)+'a','f'+str(fold)+'b'],'line':['motor']*2,'new_business':[0,1],'exposure':[.1,1.],'q':[.3,.8],'y':[4.,10.],
            'annual':{'t':[20.,15.],'n':[30.,12.],'h':[6.,6.]}[raw]});return z,{'fixture':True}
    try:
        e.LINES=['motor'];e.base_scope=fixture;_,target,_=e.build_trunk(None,{'T2b':'t','N0':'n','F1':'h'})
    finally:e.LINES=oldlines;e.base_scope=oldscope
    expo=np.array([.1,1.]);neutral=np.sum(np.array([30.,12.])*expo)/np.sum(np.array([6.,6.])*expo);uf1=np.array([6.,6.])*expo*neutral
    raw=np.array([20.,15.])*expo*np.array([.3,.8]);level=e.original_kopt(np.array([4.,10.]),raw)
    checks['periodpremium_neutralization']=bool(np.allclose(target.A1_F1,uf1,rtol=1e-14))
    checks['mixture_periodpremium_final_bridge']=bool(np.allclose(target['mix'],.5*(uf1*np.array([.3,.8])+raw*level),rtol=1e-14))
    checks['all_passed']=all(checks.values());assert checks['all_passed'];dump(OUT/'bridge_verifier.json',{'utc':e.f.utc(),'checks':checks,'synthetic_counts':dict(e.COUNTS),'real_fits':0,'verifier_code_sha256':sha(Path(__file__))});print(json.dumps(checks))

def verify():
    e.guard();checks={};models=[];schemas={}
    for line in e.LINES:
        for family in ['N0','F1']:
            for seed in e.f.SEEDS:
                base=read(OUT/'source'/line/'baseline'/f'{family}_seed{seed}'/'complete.json');replay=read(OUT/'source'/line/'poison2024'/f'{family}_seed{seed}'/'complete.json')
                for key in ['arguments_sha256','model_sha256','raw_sha256','rounds','source_center']:assert base[key]==replay[key],(line,family,seed,key)
                assert sha(e.f.ROOT/base['model'])==base['model_sha256'] and sha(e.f.ROOT/base['raw'])==base['raw_sha256']
                expect={'motor':49,'buildings':41,'contents':42}[line]+(2 if family=='F1' else 0);assert len(base['columns'])==expect
                model=e.f.lgb.Booster(model_file=str(e.f.ROOT/base['model']));assert list(model.feature_name())==base['columns'];del model
                schemas[(line,family)]=base['columns']
                models.append({'line':line,'family':family,'seed':seed,'features':expect,'rounds':base['rounds'],'reused':base['reused']})
    checks['all18_source_models_and18_replays_verified']=True
    originals=read(OUT/'original18_source_schemas.json')['records'];assert len(originals)==18
    for rec in originals:
        path=R/rec['path'];assert sha(path)==rec['sha256']
        with path.open(encoding='utf8') as stream:
            names=next(line.strip().split('=',1)[1].split() for line in stream if line.startswith('feature_names='))
        assert names==schemas[(rec['line'],rec['family'])]
    checks['all18_original_production_feature_orders_match_temporal_family']=True
    checks['60_real_source_fits_recorded']=sum(len((OUT/('fit_attempts_'+line+'.jsonl')).read_text().splitlines()) for line in e.LINES)==60
    tr=pd.read_parquet(OUT/'training2023.parquet');te=pd.read_parquet(OUT/'predictions2024.parquet');pars=read(OUT/'parameters.json')['recipe'];replay=e.apply_recipe(te,pars)
    checks['saved_prediction_replay_exact']=all(np.array_equal(te[n],replay[n]) for n in e.NAMES)
    manual=independent_recipe(te,pars);checks['complete_ultimate_pipeline_and_final_bridge_scalar_math']=all(np.allclose(te[n],manual[n],rtol=2e-13,atol=1e-8) for n in e.NAMES)
    mx=tr.T2b_raw.to_numpy().copy()
    for p in pars['F2']:
        verify_factor_learning(tr,mx,p,p['variable']);mx=independent_factor(tr,mx,p,p['variable'])
    mx=independent_shape(tr,mx,{'motor_0':.9});pb=read(e.f.PLAN)['preprocessing_full_structure']['public_blocks'];mx=independent_shape(tr,mx,{'motor_1':pb['own_training_motor_NB_shape_A_M1']})
    for p,(_,lines) in zip(pars['own'],e.v.SEQ):
        verify_factor_learning(tr,mx,p,p['variable'],lines);mx=independent_factor(tr,mx,p,p['variable'])
    checks['all_factor_learning_scalar_sums_and_credibility']=True
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
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('mode',choices=['synthetic','bridge','verify']);args=p.parse_args()
    with e.threadpool_limits(limits=2):globals()[args.mode]()
