"""Un GLM estándar de discrepancia entre dos riesgos fuente, sin nuevos árboles."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';PARENT=BASE/'A1S_nucleo_20261026_v1/target_complete_core'
OUT=BASE/'GLM_discrepancia_A1S_20261026_v1'
PLAN=R/'registro/semana2_mision017_GLM_discrepancia_A1S_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


c=load('A1S_discrepancy_parent',R/'herramientas/validar_nucleo_completo_A1S.py')
w=c.w;K=300.;LINES=c.LINES;YEARS=[2023,2024]
unit=c.b.unit


def dump(path,value):
    assert not path.exists(),'Preserve existing checkpoint: '+str(path)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def problem(f,held):
    train=f.loc[f.fold.ne(held)].copy();valid=f.loc[f.fold.eq(held)]
    assert not set(train.group_id).intersection(valid.group_id)
    y=train.T0.to_numpy(float);base=train.baseline_G3.to_numpy(float)
    assert (y>=0).all() and (base>0).all()
    nb=train.new_business.to_numpy(int);risk=train.source_discrepancy.to_numpy(float)
    S=float(np.sqrt(base).sum());slopes=np.zeros((len(train),2));centers={};scales={};penalty=[];support={}
    for business in [0,1]:
        sel=nb==business;center=float(np.average(risk[sel],weights=base[sel]))
        scale=float(np.sqrt(np.average((risk[sel]-center)**2,weights=base[sel])))
        npositive=int(np.count_nonzero(y[sel]>0));assert scale>1e-6 and npositive>0
        centers[str(business)]=center;scales[str(business)]=scale
        slopes[sel,business]=(risk[sel]-center)/scale
        share=float(np.sqrt(base[sel]).sum()/S)
        penalty.append(share*K/npositive)
        support[str(business)]={'rows':int(sel.sum()),'positive':npositive,'Fisher_scale_share':share}
    keys=[f'{year}|{nb}' for year in YEARS for nb in [0,1]]
    key=train.year.astype(str).to_numpy()+'|'+nb.astype(str)
    nuisance=np.column_stack([key==k for k in keys]).astype(float)
    assert (nuisance.sum(axis=0)>0).all()
    X=np.column_stack([slopes,nuisance]);initial=np.zeros(6)
    for j in range(4):
        sel=nuisance[:,j].astype(bool);assert y[sel].sum()>0
        initial[2+j]=np.log(c.b.factor(y[sel],base[sel]))
    arrays={'X':X,'y':y,'base':base,'offset':np.log(base),'penalty':np.r_[penalty,np.zeros(4)],'initial':initial}
    digest=hashlib.sha256()
    for key,a in arrays.items():
        digest.update(key.encode());digest.update(str(a.shape).encode());digest.update(a.dtype.str.encode());digest.update(a.tobytes())
    digest.update(json.dumps(train.row_id.tolist(),separators=(',',':')).encode())
    return {**arrays,'S':S,'centers':centers,'scales':scales,'support':support,'keys':keys,'signature':digest.hexdigest(),
            'training_rows':len(train),'training_groups_digest':c.b.digest(sorted(set(train.group_id)))}


def objective(p,coef):
    root=np.exp((p['offset']+p['X']@coef)/2)
    value=2*np.sum(root+p['y']/root-2*np.sqrt(p['y']))/p['S']+.5*np.dot(p['penalty']*coef,coef)
    gradient=p['X'].T@((root-p['y']/root)/p['S'])+p['penalty']*coef
    return float(value),gradient


def fit(p,line,held,path=None):
    result=optimize.minimize(lambda x:objective(p,x),p['initial'],jac=True,method='L-BFGS-B',
        options={'maxiter':2000,'gtol':1e-10,'ftol':1e-15,'maxls':50})
    value,grad=objective(p,result.x)
    a={'line':line,'held':held,'coef':result.x.tolist(),'K':K,'centers':p['centers'],'scales':p['scales'],
       'support':p['support'],'penalty':p['penalty'].tolist(),'problem_signature':p['signature'],
       'training_rows':p['training_rows'],'training_groups_digest':p['training_groups_digest'],
       'objective':value,'max_abs_gradient':float(np.abs(grad).max()),'success':bool(result.success),
       'message':str(result.message),'iterations':int(result.nit),'nuisance_keys':p['keys'],
       'nuisance_intercepts_not_transferred':True,'new_GLM_fits':1}
    if path is not None:dump(path,a)
    assert result.success and np.abs(grad).max()<1e-6,str(result.message)
    return a


def apply(f,a):
    base=f.baseline_G3.to_numpy(float);nb=f.new_business.to_numpy(int);risk=f.source_discrepancy.to_numpy(float)
    centers=np.array([a['centers'][str(k)] for k in nb]);scales=np.array([a['scales'][str(k)] for k in nb])
    coef=np.array([a['coef'][k] for k in nb]);factor=np.exp(coef*(risk-centers)/scales)
    return c.g.normalise(f,base,factor)


def mathematics(p,a):
    beta=np.array(a['coef']);value,grad=objective(p,beta)
    mu=np.exp(p['offset']+p['X']@beta)
    independent=.5*mean_tweedie_deviance(p['y'],mu,power=1.5)*len(mu)/p['S']+.5*np.dot(p['penalty']*beta,beta)
    assert abs(value-independent)<1e-9
    root=np.sqrt(mu);H=p['X'].T@(p['X']*(.5*(root+p['y']/root)/p['S'])[:,None])+np.diag(p['penalty'])
    eigen=np.linalg.eigvalsh(H);assert eigen.min()>0
    rng=np.random.default_rng(2026102612);err=[]
    for _ in range(3):
        d=rng.normal(size=6);d/=np.linalg.norm(d);h=1e-4
        vp,gp=objective(p,beta+h*d);vm,gm=objective(p,beta-h*d)
        e1=abs((vp-vm)/(2*h)-grad@d);e2=float(np.abs((gp-gm)/(2*h)-H@d).max())
        assert e1<1e-6 and e2<1e-6;err.append([float(e1),e2])
    return {'sklearn_objective':True,'gradient_Hessian_finite_difference_errors':err,'min_Hessian_eigenvalue':float(eigen.min())}


def synthetic():
    rng=np.random.default_rng(2026102612);n=1600
    f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
        'fold':np.arange(n)%5,'year':2023+(np.arange(n)//5)%2,'new_business':(np.arange(n)//10)%2,
        'baseline_G3':rng.uniform(20,200,n),'source_discrepancy':rng.normal(0,.4,n),
        'T0':rng.gamma(2,100,n)*(rng.random(n)<.4)})
    p=problem(f,0);a=fit(p,'synthetic',0);math=mathematics(p,a)
    poisoned=f.copy();poisoned.loc[poisoned.fold.eq(0),'T0']=-1e30
    q=problem(poisoned,0);assert p['signature']==q['signature']
    b=fit(q,'synthetic',0);assert a==b
    changed=f.copy();changed.loc[changed.fold.ne(0),'T0']*=np.exp(changed.loc[changed.fold.ne(0),'source_discrepancy'])
    z=fit(problem(changed,0),'synthetic',0);assert a['coef']!=z['coef']
    valid=f.loc[f.fold.eq(0)];pred,norm=apply(valid,a)
    replay,nn=apply(valid.assign(T0=-1e30),a);assert np.array_equal(pred,replay) and norm==nn
    zero,_=apply(valid,{**a,'coef':[0.]*6});assert np.array_equal(zero,valid.baseline_G3)
    return {'synthetic_fits':3,'contest_fits':0,'full_fit_held_response_invariance':True,
            'training_response_change_changes_fit':True,'zero_coef_identity_exact':True,'independent_math':math}


def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    assert w.read(PARENT/'report.json')['gates']['both_years_nonnegative'] is False
    paths=[Path(__file__),Path(c.__file__),Path(c.g.__file__),Path(c.b.__file__),PARENT/'report.json',PARENT.parent/'completion_receipt.json',
           BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet']
    old=pd.read_parquet(paths[-1]).set_index('row_id');scopes=[]
    for line in LINES:
        rp=BASE/f'linaje_T2b_v1/raw_rates_{line}.parquet';paths.append(rp)
        raw=pd.read_parquet(rp,columns=['row_id','annual_raw_T2b']).set_index('row_id')
        for held in range(5):
            inp=PARENT/f'inputs_{line}_fold{held}.parquet';paths.append(inp);f=pd.read_parquet(inp)
            f['source_discrepancy']=f.log_relative_A1S.to_numpy()-np.log(raw.loc[f.row_id,'annual_raw_T2b'].to_numpy(float))
            f['baseline_G3']=f.base_N3
            if line!='buildings':
                gp=BASE/f'tanda10_factores_20261026_v1/learning_{line}_fold{held}.json';paths.append(gp)
                stages=w.read(gp)['stages']
                for train in [True,False]:
                    mask=f.fold.ne(held) if train else f.fold.eq(held)
                    value=f.loc[mask,'base_N3'].to_numpy()
                    for stage in stages:value,_=c.g.apply_stage(f.loc[mask],value,stage)
                    f.loc[mask,'baseline_G3']=value
            valid=f.fold.eq(held)
            assert np.array_equal(f.loc[valid,'baseline_G3'],old.loc[f.loc[valid,'row_id'],'G3'])
            path=OUT/f'inputs_{line}_fold{held}.parquet';f.to_parquet(path,index=False)
            scopes.append({'line':line,'held':held,'input':w.rel(path),'sha256':w.sha(path)})
    with threadpool_limits(limits=2):dump(OUT/'synthetic.json',synthetic())
    dump(OUT/'preflight.json',{'utc':datetime.now(timezone.utc).isoformat(),'scopes':scopes,
        'new_contest_fits':0,'new_C0_fits':0,'new_scores':0,'sources':{w.rel(p):w.sha(p) for p in paths}})
    print(json.dumps({'preflight':'passed','synthetic_fits':3,'contest_fits':0,'scopes':15}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json')
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'hypothesis':'A fixed50/50A1S transfer failed mainly in building/motor renewals and2024. Let a small standard GLM estimate the contribution of the newly available source disagreement inside training, rather than select source weight after held losses.',
        'necessity':'New full-core A1S assay is closed and adverse, all6gates fail. The source pair information was unavailable in prior slope/age trials; no repetition of those designs or another tree training.',
        'model':'Single primary D1,15GLMs (3lines x5folds), two risk-disagreement coefficients by business and four year/business nuisance intercepts.',
        'feature':'log(source_A1S_three_seed_relative)-log(source_T2b_annual_raw); source-only input models, no target learned component-level artifacts used as the new feature.',
        'design':'Center/scale each business source-disagreement by training G3price-weighted mean/SD; multiply standardized value by business indicator. No extra slope variables or nonlinearities.',
        'objective':'Half sum Tweedie1.5deviance/S plus ridge; S=sum sqrt(trainingG3). K300fixed, each business ridge=(S_business/S)*(300/n_positive_business). Zero prior means retainG3.',
        'offset':'log(saved outer-scopeG3period cost), already contains exposure/C0 once. No extra exposure factor.',
        'nuisance':'Four unpenalized training-year/business intercepts, not transferred. Transfer only discrepancy slopes, prediction-only normalization by year/business preserves baseline totals.',
        'optimizer':{'method':'L-BFGS-B','maxiter':2000,'gtol':1e-10,'ftol':1e-15,'maxls':50,'gradient_guard':1e-6},
        'data':'Same109296emerging2023/2024rows and five global component folds;2024open adaptive. No band/seed/K/mixture search.',
        'criterion':w.read(c.PLAN)['criterion'],'bootstrap':{'replicates':2000,'seed':2026102612,'unit':'saved global connected component'},
        'budget':{'new_real_GLM_fits':15,'slope_coefficients':30,'nuisance_intercepts':60,'synthetic_fits_separate':3,
                  'new_C0_fits':0,'new_source_fits':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0},
        'control':'All numeric problem arrays/initialization/penalty byte invariant to held response/reserve poisoning; no refit of contest for this check. Synthetic complete fit invariance; independent sklearnobjective, finite-difference gradient/Hessian; optimizer blocked saved replay.',
        'limits':w.read(c.PLAN)['limits']+['Learned contribution is exploratory after observing full-core failure; not independent confirmation','No direct complete historicF3c numerical comparator; gain overG3not publicgain'],
        'sources':{**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),w.rel(OUT/'synthetic.json'):w.sha(OUT/'synthetic.json'),
                   **{a['input']:a['sha256'] for a in pre['scopes']}},'2024_open':True,'B00_all_alternatives_preserved':True}
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro un único GLM de discrepancia entre A1S y T2b. La mezcla fija anterior falló sus seis controles; el daño se concentra en renovaciones de edificios/autos y el año 2024. '
        'La información A1S por fila es nueva y queda guardada. Se harán 15 GLM estándar, con dos pendientes por tipo de negocio y cuatro interceptos de año/negocio no transferidos. '
        'El riesgo nuevo es la diferencia de log-relatividades fuente, sin factores target usados como feature. Se mantiene K=300, prior de efecto cero, objetivo Tweedie y offset G3 existente; no se elige una rejilla de pesos. '
        'Tres ajustes sintéticos pasaron; se comprobará el problema numérico completo bajo etiquetas retenidas alteradas, la matemática y replay sin optimizador. '
        'C0, árboles fuente, bandas y folds no cambian. Mismos umbrales de incertidumbre/concentración; sin precios de 2025 ni envíos. '
        'B00, F3c 0,16914 y alternativas conservados; 2024 abierto y adaptativo. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-GLM-DISCREPANCIA-A1S-PREVIO','--asunto','GLM estándar para el aporte A1S, sin pesos elegidos en validación',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(result.stdout)})
    print(json.dumps({'registered':True,'forum':json.loads(result.stdout)}))


def statistics(p,plan):
    y=p.T0.to_numpy(float);ref=p.G3.to_numpy();pred=p.D1.to_numpy()
    den=unit(y,np.full(len(y),y.mean())).sum();gain=unit(y,ref)-unit(y,pred)
    assert abs(unit(y,pred).mean()-mean_tweedie_deviance(y,pred,power=1.5))<1e-9
    group=pd.DataFrame({'group_id':p.group_id,'gain':gain,'N':1.,'Y':y,'sqrtY':np.sqrt(y)}).groupby('group_id',sort=True).sum()
    rng=np.random.default_rng(plan['bootstrap']['seed']);v=group.to_numpy();boot=[]
    for _ in range(2000):
        a=v[rng.integers(0,len(v),len(v))].sum(axis=0);boot.append(float(a[0]/(8*np.sqrt(a[1]*a[2])-8*a[3])))
    ci=np.quantile(boot,[.025,.975]).tolist();delta=float(gain.sum()/den)
    folds={str(k):float(gain[p.fold.eq(k)].sum()/den) for k in range(5)}
    years={str(k):float(gain[p.year.eq(k)].sum()/den) for k in YEARS};cells=[]
    for (line,year,nb),ix in p.groupby(['line','year','new_business']).groups.items():
        ii=np.array(list(ix));yy=y[ii];dd=unit(yy,np.full(len(yy),yy.mean())).sum()
        cells.append({'line':line,'year':int(year),'new_business':int(nb),'delta_global':float(gain[ii].sum()/den),'delta_cell_null':float(gain[ii].sum()/dd)})
    post31=float((group.gain.sum()-group.gain.nlargest(31).sum())/den)
    gates={'delta_ge_002':delta>=.002,'lower95_positive':ci[0]>0,'positive_folds_ge4':sum(v>0 for v in folds.values())>=4,
           'both_years_nonnegative':min(years.values())>=0,'post31_nonnegative':post31>=0,'cell_min_ge_minus001':min(x['delta_cell_null'] for x in cells)>=-.001}
    weights=pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet',columns=['row_id','weight']).set_index('row_id').loc[p.row_id,'weight'].to_numpy(float)
    weighted=float(np.sum(weights*gain)/np.sum(weights*unit(y,np.full(len(y),np.average(y,weights=weights)))))
    group.sort_values('gain',ascending=False).to_parquet(OUT/'influence.parquet');np.save(OUT/'bootstrap.npy',np.array(boot))
    return {'scores':{n:float(1-unit(y,p[n].to_numpy()).sum()/den) for n in ['N3','G3','D1']},'delta_vs_G3':delta,
            'bootstrap95':ci,'fold_contributions':folds,'year_contributions':years,'cells':cells,'post31_delta':post31,
            'weighted2025_sensitivity_delta':weighted,'weighted_ESS_already_failed':True,'gates':gates,'exploratory_gates_pass':all(gates.values()),
            'level_sensitivity':{str(k):{n:float(1-unit(y,p[n].to_numpy()*k).sum()/den) for n in ['G3','D1']} for k in [.95,1.,1.05]},
            'formal_admission':False,'submission_allowed':False}


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    import os
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    oof=pd.read_parquet(BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet');oof['D1']=np.nan
    idx=pd.Series(oof.index.to_numpy(),index=oof.row_id);checks=[]
    with threadpool_limits(limits=2):
        for scope in w.read(OUT/'preflight.json')['scopes']:
            f=pd.read_parquet(ROOT/scope['input']);held=scope['held'];line=scope['line']
            p=problem(f,held);a=fit(p,line,held,OUT/f'model_{line}_fold{held}.json')
            poison=f.copy();poison.loc[poison.fold.eq(held),['T0','reserve']]=-1e30
            other=problem(poison,held);assert p['signature']==other['signature']
            math=mathematics(p,a);valid=f.loc[f.fold.eq(held)];pred,norm=apply(valid,a)
            old=optimize.minimize
            def reject(*args,**kwargs):raise AssertionError('No optimizer during replay')
            optimize.minimize=reject
            try:
                replay,nn=apply(valid.assign(T0=-1e30,reserve=-1e30),w.read(OUT/f'model_{line}_fold{held}.json'))
                assert np.array_equal(pred,replay) and norm==nn
            finally:optimize.minimize=old
            oof.loc[idx.loc[valid.row_id].to_numpy(),'D1']=pred
            dump(OUT/f'application_{line}_fold{held}.json',{'normalizers':norm,'held_rows':len(valid)})
            checks.append({'line':line,'held':held,'full_numeric_problem_held_payload_invariant':True,
                           'replay_without_optimizer_exact':True,**math})
        assert oof.D1.notna().all() and oof.D1.gt(0).all()
        oof.to_parquet(OUT/'oof_2023_2024.parquet',index=False);result=statistics(oof,plan)
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'complete_exploratory',
        'new_real_GLM_fits':15,'new_C0_fits':0,'new_source_fits':0,'new_source_inference':0,
        'new_final_test_prices':0,'new_submissions':0,'numeric_controls':checks,'plan_sha256':w.sha(PLAN),
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,**result}
    dump(OUT/'report.json',report)
    print(json.dumps({k:report[k] for k in ['scores','delta_vs_G3','bootstrap95','fold_contributions','year_contributions','post31_delta','gates','weighted2025_sensitivity_delta']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','register','run']);a=p.parse_args()
    {'prepare':prepare,'register':register,'run':run}[a.mode]()
