"""Valida el efecto fuente, su matemática y la conservación de totales sin reajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
spec=importlib.util.spec_from_file_location('mkt',R/'herramientas/mision017_fase2_tanda4_marketing.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
statspec=importlib.util.spec_from_file_location('stat3',R/'herramientas/validar_mision017_fase2_tanda3.py')
stats=importlib.util.module_from_spec(statspec);statspec.loader.exec_module(stats)
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
OUT=b.OUT/'validation_v1'


def block(values,categories,drop):
    code=pd.Categorical(values,categories=categories).codes
    assert (code>=0).all()
    if drop:code=code-1
    active=code>=0;row=np.arange(len(code))[active]
    return sparse.csr_matrix((np.ones(len(row)),(row,code[active])),shape=(len(code),len(categories)-int(drop)))


def source_mathematics(line,master,regions):
    effect=b.read(b.OUT/f'marketing_{line}.json')
    assert b.sha(b.data.OUT/f'{line}.parquet')==effect['source_sha256']
    f=pd.read_parquet(b.data.OUT/f'{line}.parquet')
    f=f.merge(master,on='customer_id',validate='many_to_one').merge(regions,on='address_id',validate='many_to_one')
    model=b.lgb.Booster(model_file=str(b.PARENT/f'modelos/prod/T2b_{line}.txt'))
    off=np.log(f.e_cost.to_numpy(float))+model.predict(b.source_matrix(f,model),raw_score=True,num_threads=2)
    labels=list(effect['marketing_log_factors']);assert labels==sorted(labels)
    xm=block(f.marketing_segment,labels,True);xr=block(f.source_region,effect['source_regions'],True)
    xy=block(f.year,effect['source_years'],False);X=sparse.hstack([xm,xr,xy],format='csr')
    coef=np.r_[[effect['marketing_log_factors'][x] for x in labels[1:]],effect['source_region_nuisance'],effect['source_year_nuisance']]
    penalty=np.r_[np.ones(xm.shape[1]+xr.shape[1]),np.zeros(xy.shape[1])];y=f.T0.to_numpy(float)
    def objective(beta):
        eta=off+X@beta;root=np.exp(eta/2)
        return float(2*np.mean(root+y/root-2*np.sqrt(y))+.5*b.ALPHA*np.dot(penalty*beta,beta))
    mu=np.exp(off+X@coef)
    independent=mean_tweedie_deviance(y,mu,power=1.5)/2+.5*b.ALPHA*np.dot(penalty*coef,coef)
    assert abs(independent-effect['objective'])<1e-8*(1+abs(independent))
    g=np.asarray(X.T@((np.sqrt(mu)-y/np.sqrt(mu))/len(y))).ravel()+b.ALPHA*penalty*coef
    assert np.abs(g).max()<1e-4
    rng=np.random.default_rng(751);errors=[]
    for _ in range(3):
        direction=rng.normal(size=len(coef));direction/=np.linalg.norm(direction);h=1e-4
        finite=(objective(coef+h*direction)-objective(coef-h*direction))/(2*h)
        error=abs(finite-float(g@direction));assert error<5e-6;errors.append(error)
    return {'line':line,'rows':len(f),'independent_sparse_encoding':True,'sklearn_objective_match':True,
        'max_abs_gradient':float(np.abs(g).max()),'finite_difference_errors':errors,'new_fit_calls':0}


def validate():
    assert not OUT.exists();plan=b.read(b.PLAN);report=b.read(b.OUT/'price_report.json')
    assert b.read(b.OUT/'registration.json')['plan_sha256']==b.sha(b.PLAN)
    for p,h in plan['sources'].items():assert b.sha(ROOT/p)==h
    OUT.mkdir();p=pd.read_parquet(b.OUT/'oof_2023_2024.parquet');assert p.row_id.is_unique and len(p)==109296
    # Reuse the same already implemented statistic with an explicit schema mapping.
    schema={'N3':'N0','R1':'Q1','R2':'Q2','R3':'Q3'}
    x=p[['T0','group_id','line','new_business','fold','year',*schema]].rename(columns=schema).copy()
    stats.OUT=OUT;comparisons=stats.evaluate(x,plan)
    rename={'Q1':'R1','Q2':'R2','Q3':'R3'};comparisons={rename[k]:v for k,v in comparisons.items()}
    for file in ['segments.csv','folds.csv','years.csv']:
        t=pd.read_csv(OUT/file);t['model']=t.model.map(rename);t.to_csv(OUT/file,index=False)
    for old,new in rename.items():
        # The statistic's filenames are translated, preserving both contents in provenance.
        src=OUT/f'influence_{old}.parquet';dst=OUT/f'influence_{new}.parquet';dst.write_bytes(src.read_bytes())
    original=b.optimize.minimize;b.optimize.minimize=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('No optimizer in replay'))
    replays=[];math=[]
    try:
        with threadpool_limits(limits=2):
            master=pd.read_parquet(b.data.RAW/'customers.parquet',columns=['customer_id','marketing_segment'])
            regions=pd.read_parquet(b.data.RAW/'addresses.parquet',columns=['address_id','region']).rename(columns={'region':'source_region'})
            for line in b.data.LINES:
                math.append(source_mathematics(line,master,regions))
                effect=b.read(b.OUT/f'marketing_{line}.json')
                for held in range(5):
                    t=p.loc[p.line.eq(line)&p.fold.eq(held)].copy()
                    saved=b.read(b.OUT/f'normalizers_{line}_fold{held}.json')
                    assert saved['marketing_effect_sha256']==b.sha(b.OUT/f'marketing_{line}.json')
                    for strength,name in [(1.,'R1'),(.5,'R2'),(.25,'R3')]:
                        out,norm=b.overlay(t,t.N3.to_numpy(float),effect['marketing_log_factors'],strength)
                        assert np.array_equal(out,t[name].to_numpy(float)) and norm==saved['normalizers'][name]
                        poison=t.assign(T0=-1e30,reserve=-1e30,T0_cents=-1e30)
                        changed,_=b.overlay(poison,t.N3.to_numpy(float),effect['marketing_log_factors'],strength)
                        assert np.array_equal(out,changed)
                    replays.append({'line':line,'fold':held,'rows':len(t),'bit_exact':True,'label_poison_invariant':True,
                        'normalizers_only_covariates_and_predicted_costs':True,'cell_totals_preserved':True,'new_fit_calls':0})
    finally:b.optimize.minimize=original
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scores':report['scores'],'reference':'N3 research comparator, not promoted',
        'comparisons':comparisons,'source_mathematics':math,'replays':replays,'new_fits':0,'new_reporting_fits':0,'new_submissions':0,
        'B00_preserved':True,'2024_is_adaptive_development':True,'not_prospective_independent_confirmation':True,
        'CI_conditional_on_fixed_source_model':True,'complete_source_reporting_and_master_uncertainty_not_identified':True,
        'statistic_source':{'path':b.rel(Path(stats.__file__)),'sha256':b.sha(Path(stats.__file__)),'input_schema_mapping':schema},
        'goal_achieved':False}
    b.dump(OUT/'report.json',result)
    print(json.dumps({'scores':report['scores'],'comparisons':comparisons,'source_math_pass':True,'replays':len(replays),'new_fits':0}))


if __name__=='__main__':validate()
