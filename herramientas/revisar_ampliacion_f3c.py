"""Verificación de ámbitos y aritmética de A1/mezcla sin ajustar modelos."""
import argparse, importlib.util, json, gc
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import d2_tweedie_score

REPO=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('expanded',REPO/'herramientas/ampliar_validacion_cadena_f3c.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
R=a.RUN;v=a.v

def preopen():
    a.verify_inputs();assert a.read(R/'source_training_complete.json')['all_passed'];assert a.read(R/'prediction_checks.json')['all_passed']
    src,em,asg=a.load_prepared();checks={};errors={}
    checks['poison2024_changes_positive_amounts_both_markets']=all(bool((c.loss_date.dt.year.eq(2024)&c.incurred_to_date.gt(0)).any()) for c in asg.values())
    c=asg['emerging'];checks['poison_fold0_changes_positive_amounts']=bool((c.period_year.eq(2023)&c.row_fold.eq(0)&c.incurred_to_date.gt(0)).any())
    # Cotejar los filtros rápidos con membresía literal por row_id, antes de cap/RKM.
    for outer in [None,0,1,2,3,4]:
        name='full' if outer is None else f'fold{outer}';old=a.read(R/f'curves_{name}.json')
        erows=em[em.year.eq(2023)&(em.fold.ne(outer) if outer is not None else True)]
        for branch in ['inner','full']:
            sr=src[src.year.le(2023)&(src.fold.ne(0) if branch=='inner' else True)]
            filtered={'developed':asg['developed'][asg['developed'].row_id.isin(set(sr.row_id))].copy(),'emerging':asg['emerging'][asg['emerging'].row_id.isin(set(erows.row_id))].copy()}
            sr=sr.copy(deep=False);er=erows.copy(deep=False);sr.attrs['excluded_fold']=None;er.attrs['excluded_fold']=None
            C,N,_=a.rkm(filtered,sr,er)
            checks[name+'_'+branch+'_literal_membership']=a.curves_json(C)==old[branch] and a.curves_json(N)==old[branch+'_count']
    raw=a.objects()[0];curves0=a.parse_curves(a.read(R/'curves_fold0.json')['full']);F2=a.t2b_curves()
    poisoned=em.copy();held=poisoned.year.eq(2023)&poisoned.fold.eq(0)
    for c in ['y']+[c for c in em if c.startswith('y_')]:poisoned.loc[held,c]*=2
    baseline=[];adverse=[]
    for ee,ra in [(em,raw['fold0']),(poisoned,a.raw_series('replay_fold0'))]:
        tt,et,_=a.target_base(ee,raw['T2b'],F2,0,'T2b');ta,ea,_=a.target_base(ee,ra,curves0,0,'A1')
        tables={'T2b':(tt,et),'A1':(ta,ea),'mezcla':(a.blend(tt,ta),a.blend(et,ea))};results={}
        for view,(tr,te) in tables.items():te['y']=np.nan;results[view]=v.recipe(tr,te)
        (baseline if ee is em else adverse).append(results)
    for view in a.VIEWS:
        p0,z0=baseline[0][view];p1,z1=adverse[0][view]
        checks[view+'_whole_fold0_parameters_exact']=z0==z1
        checks[view+'_whole_fold0_prices_exact']=all(np.array_equal(p0[k],p1[k]) for k in a.MODELS)
    canonical=REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/target_T0_and_stresses.parquet'
    assert a.sha(canonical)=='114dd8ae8048a04530855c7be8f8e718ebd9fe969f491c4513fc1fadbd0bcca6'
    c=pd.read_parquet(canonical,columns=['market','row_id','year','T0_cents']);c=c[c.market.eq('emerging')&c.year.eq(2024)]
    y=pd.read_parquet(R/'target2024_sealed.parquet').merge(c[['row_id','T0_cents']],on='row_id',validate='1:1')
    checks['canonical_T0_by_cent']=len(y)==59202 and np.array_equal(np.rint(y.y.to_numpy()*100).astype(np.int64),y.T0_cents.to_numpy(np.int64))
    checks['source_addresses_isolated']=bool(src[src.year.le(2023)].groupby('address_id').fold.nunique().le(1).all())
    checks['target_addresses_isolated']=bool(em[em.year.eq(2023)].groupby('address_id').fold.nunique().le(1).all())
    checks['F3c_preserved']=a.sha(REPO/'privado/semana2/claude_mision017_20261025/F3c_2025.csv')=='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
    assert all(checks.values()),checks
    fits=(R/'fit_attempts.jsonl').read_text().splitlines();assert len(fits)==48
    a.save(R/'preopening_verification.json',{'utc':a.now(),'checks':checks,'all_passed':True,'source_native_fits':len(fits),'new_fits_by_verifier':0,'new_scores2024':0,'verifier_sha256':a.sha(__file__)})
    print(json.dumps(v.clean({'preopening_verified':True,'checks':len(checks),'fits':len(fits)})))

def post():
    a.verify_inputs();checks={};r=a.read(R/'results.json');target=pd.read_parquet(R/'target2024_sealed.parquet').set_index('row_id').y
    err=0.;bootstrap_error=0.;tables={}
    for view in a.VIEWS:
        t=pd.read_parquet(R/f'predictions_{view}.parquet');tables[view]=t;y=t.row_id.map(target).to_numpy(float)
        for seg,mask in a.segments(t).items():
            for model in a.MODELS:
                score=d2_tweedie_score(y[mask],t[model].to_numpy()[mask],power=1.5)
                err=max(err,abs(score-r['views'][view]['metrics'][seg]['D2'][model]))
        boot=np.load(R/f'bootstrap_{view}.npz');ss=list(boot['segments']);models=list(boot['models']);groups,ix=np.unique(v.components(t)[0],return_inverse=True)
        rng=np.random.default_rng(2026102301)
        for n in range(20):
            counts=np.bincount(rng.integers(0,len(groups),size=len(groups)),minlength=len(groups));w=counts[ix]
            for model in a.MODELS:
                score=d2_tweedie_score(y,t[model].to_numpy(),sample_weight=w,power=1.5)
                bootstrap_error=max(bootstrap_error,abs(score-boot['scores'][n,ss.index('global'),models.index(model)]))
    checks['baseline_metrics_sklearn']=err<1e-12;checks['bootstrap_twenty_draws_all_views']=bootstrap_error<1e-12
    composition=a.read(R/'composition_results.json');composition_error=0.;composition_boot_error=0.
    for view in a.VIEWS:
        t=tables[view];y=t.row_id.map(target).to_numpy(float);pack=np.load(R/f'composition_bootstrap_{view}.npz');weights=pack['weights']
        groups,ix=np.unique(v.components(t)[0],return_inverse=True);rng=np.random.default_rng(2026102301)
        masks=[np.ones(len(t),bool),t.new_business.to_numpy(bool)]
        for name,mask in zip(['global','new_business'],masks):
            scores=[d2_tweedie_score(y[mask],t[k].to_numpy()[mask],sample_weight=weights[mask],power=1.5) for k in a.MODELS[:2]]
            composition_error=max(composition_error,abs(scores[1]-scores[0]-composition['views'][view][name]['delta']))
        for n in range(20):
            count=np.bincount(rng.integers(0,len(groups),size=len(groups)),minlength=len(groups));w=weights*count[ix]
            for j,mask in enumerate(masks):
                scores=[d2_tweedie_score(y[mask],t[k].to_numpy()[mask],sample_weight=w[mask],power=1.5) for k in a.MODELS[:2]]
                composition_boot_error=max(composition_boot_error,abs(scores[1]-scores[0]-pack['delta'][n,j]))
    checks['composition_metrics_sklearn']=composition_error<1e-12;checks['composition_twenty_draws_sklearn']=composition_boot_error<1e-12
    scen=a.read(R/'scenario_results.json');assert len(scen['scenarios'])==50
    serr=0.;changes=[]
    for i,item in enumerate(scen['scenarios']):
        pack=np.load(R/'scenarios'/f'{i:02d}.npz');p=pack['predictions'];y=pack['y'];assert p.shape==(3,3,59202) and np.isfinite(p).all() and (p>0).all()
        cellchanges={}
        for vi,view in enumerate(a.VIEWS):
            t=tables[view];cellchanges[view]={}
            for mi,model in enumerate(a.MODELS):
                score=d2_tweedie_score(y,p[vi,mi],power=1.5);reported=item['views'][view]['target_relearned']['global']['D2'][model];serr=max(serr,abs(score-reported))
                score=d2_tweedie_score(y,t[model].to_numpy(),power=1.5);reported=item['views'][view]['fixed_prices']['global']['D2'][model];serr=max(serr,abs(score-reported))
            base=t['F3c_reaprendido'].to_numpy();new=p[vi,1];ratio=new/base-1
            cellchanges[view]={'total_relative_change':float(new.sum()/base.sum()-1),'max_abs_individual_relative_change':float(np.abs(ratio).max()),'rows_abs_change_ge10pct':int((np.abs(ratio)>=.1).sum())}
            if item['scenario']=='cost_curve_train_peril_mix':checks[view+'_cost_curve_identity']=np.allclose(p[vi],np.stack([t[k].to_numpy() for k in a.MODELS]),rtol=1e-10,atol=1e-9)
        changes.append({'scenario':item['scenario'],'views':cellchanges})
    checks['all_scenario_global_metrics_sklearn']=serr<1e-12
    checks['T2b_parent_delta_preserved']=abs(r['views']['T2b']['metrics']['global']['delta']-a.read(a.PARENT/'resultados.json')['metrics']['global']['delta'])<1e-10
    assert all(checks.values()),checks
    a.save(R/'scenario_price_changes.json',{'utc':a.now(),'changes':changes,'period':'2024; ninguna prima nueva2025'})
    a.save(R/'post_verification.json',{'utc':a.now(),'checks':checks,'all_passed':True,'metric_max_error':err,'bootstrap_max_error':bootstrap_error,'composition_metric_max_error':composition_error,'composition_bootstrap_max_error':composition_boot_error,'scenario_metric_max_error':serr,'source_native_fits':48,'scenarios':50,'new_fits_by_verifier':0,'professional_independent_review':False,'verifier_sha256':a.sha(__file__)})
    print(json.dumps(v.clean({'post_verified':True,'metric_error':err,'bootstrap_error':bootstrap_error,'scenario_error':serr})))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['preopen','post']);z=p.parse_args();{'preopen':preopen,'post':post}[z.stage]()
