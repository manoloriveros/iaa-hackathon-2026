"""Un único GLM de edad NB por ramo, con base y ámbitos guardados."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';BASE=R/'privado/semana2/mision017_fase2'
PARENT=BASE/'FSp_REN_G3_prod_contraste_20261026_v1';OUT=BASE/'GLM_edad_NB_20261026_v1'
PLAN=R/'registro/semana2_mision017_GLM_edad_NB_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.metrics import mean_tweedie_deviance
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


stats=load('NB_fixed_statistics',R/'herramientas/contrastar_NB_FSp_guardado_v2.py')
w=stats.w;LEVELS=['17-24','25-34','35-49','50-64','65+'];YEARS=[2023,2024];K=300.


def dump(path,a):path.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')


def problem(f,held):
    # Every training-dependent quantity, including ridge strength and initial
    # year levels, is calculated after excluding held groups and selecting NB.
    tr=f.loc[f.fold.ne(held)&f.new_business.eq(1)].copy()
    val=f.loc[f.fold.eq(held)]
    assert not set(tr.group_id).intersection(val.group_id)
    assert tr.T0.ge(0).all() and tr.baseline_G3.gt(0).all()
    age=tr.age_band.astype('string').fillna('__MISSING__').to_numpy()
    A=np.column_stack([age==level for level in LEVELS]).astype(float)
    B=np.column_stack([tr.year.eq(year).to_numpy() for year in YEARS]).astype(float)
    assert (B.sum(axis=0)>0).all()
    X=np.column_stack([A,B]);y=tr.T0.to_numpy(float);base=tr.baseline_G3.to_numpy(float)
    S=float(np.sqrt(base).sum());positives=int((y>0).sum());assert S>0 and positives>0
    penalty=np.r_[np.full(5,K/positives),np.zeros(2)];initial=np.zeros(7)
    for j in range(2):
        mask=B[:,j].astype(bool);assert y[mask].sum()>0,'No positive support in a training NB year'
        initial[5+j]=np.log(np.sum(y[mask]/np.sqrt(base[mask]))/np.sum(np.sqrt(base[mask])))
    arrays={'X':X,'y':y,'base':base,'offset':np.log(base),'penalty':penalty,'initial':initial}
    digest=hashlib.sha256()
    for name,a in arrays.items():
        digest.update(name.encode());digest.update(str(a.shape).encode());digest.update(a.dtype.str.encode());digest.update(a.tobytes())
    digest.update(json.dumps(tr.row_id.tolist(),separators=(',',':')).encode())
    return {**arrays,'S':S,'positives':positives,'signature':digest.hexdigest(),
            'training_rows':len(tr),'training_row_ids':tr.row_id.tolist(),'training_groups':sorted(set(tr.group_id)),
            'age':age,'year':tr.year.to_numpy()}


def objective(p,coef):
    root=np.exp((p['offset']+p['X']@coef)/2)
    value=2*np.sum(root+p['y']/root-2*np.sqrt(p['y']))/p['S']+.5*np.dot(p['penalty']*coef,coef)
    grad=p['X'].T@((root-p['y']/root)/p['S'])+p['penalty']*coef
    return float(value),grad


def fit(p,line,held,checkpoint=None):
    result=optimize.minimize(lambda z:objective(p,z),p['initial'],method='L-BFGS-B',jac=True,
        options={'maxiter':2000,'gtol':1e-10,'ftol':1e-15,'maxls':50})
    value,grad=objective(p,result.x)
    a={'line':line,'held':held,'coef':result.x.tolist(),'levels':LEVELS,'years':YEARS,'K':K,
       'training_rows':p['training_rows'],'positive_training_periods':p['positives'],'S':p['S'],
       'ridge_normalized':K/p['positives'],'problem_signature':p['signature'],
       'training_row_ids':p['training_row_ids'],'training_groups':p['training_groups'],
       'objective':value,'max_abs_gradient':float(np.max(np.abs(grad))),'success':bool(result.success),
       'message':str(result.message),'iterations':int(result.nit),'new_GLM_fits':1,
       'nuisance_year_levels_not_transferred':True}
    if checkpoint is not None:dump(checkpoint,a)
    assert result.success and abs(grad).max()<1e-6,str(result.message)
    return a


def apply(f,a,base=None):
    base=f.baseline_G3.to_numpy(float) if base is None else np.asarray(base,float)
    age=f.age_band.astype('string').fillna('__MISSING__').to_numpy()
    effects={level:a['coef'][j] for j,level in enumerate(LEVELS)}
    factor=np.array([np.exp(effects.get(x,0.)) for x in age])
    result=base.copy();norms={}
    for year in sorted(f.year.unique()):
        mask=f.year.eq(year).to_numpy()&f.new_business.eq(1).to_numpy();assert mask.any()
        norm=float(np.sum(base[mask]*factor[mask])/np.sum(base[mask]))
        result[mask]=base[mask]*factor[mask]/norm;norms[str(year)]=norm
        assert abs(result[mask].sum()/base[mask].sum()-1)<1e-12
    assert np.array_equal(result[f.new_business.eq(0)],base[f.new_business.eq(0)])
    return result,norms


def mathematics(p,a):
    enc=OneHotEncoder(categories=[LEVELS,YEARS],drop=None,handle_unknown='ignore',sparse_output=False)
    raw=pd.DataFrame({'age':p['age'],'year':p['year']})
    X=enc.fit_transform(raw);assert np.array_equal(X,p['X'])
    coef=np.array(a['coef']);mu=np.exp(p['offset']+X@coef)
    independent=.5*mean_tweedie_deviance(p['y'],mu,power=1.5)*len(mu)/p['S']+.5*np.dot(p['penalty']*coef,coef)
    value,grad=objective(p,coef);assert abs(independent-value)<1e-10
    root=np.sqrt(mu);H=X.T@(X*(.5*(root+p['y']/root)/p['S'])[:,None])+np.diag(p['penalty'])
    eig=np.linalg.eigvalsh(H);assert eig.min()>0
    rng=np.random.default_rng(2026102615);first=[];second=[]
    for _ in range(3):
        d=rng.normal(size=7);d/=np.linalg.norm(d);step=1e-4
        vp,gp=objective(p,coef+step*d);vm,gm=objective(p,coef-step*d)
        e1=abs((vp-vm)/(2*step)-grad@d);e2=np.max(abs((gp-gm)/(2*step)-H@d))
        assert e1<1e-6 and e2<1e-6
        first.append(float(e1));second.append(float(e2))
    return {'independent_fixed_onehot_and_sklearn_objective':True,'min_hessian_eigenvalue':float(eig.min()),
            'gradient_direction_errors':first,'hessian_direction_errors':second}


def synthetic():
    rng=np.random.default_rng(2026102615);n=1600
    f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
        'fold':np.arange(n)%5,'year':2023+(np.arange(n)//5)%2,'new_business':(np.arange(n)//10)%2,
        'age_band':rng.choice(LEVELS,n),'baseline_G3':rng.uniform(20,200,n),
        'T0':rng.gamma(2,100,n)*(rng.random(n)<.4)})
    p=problem(f,0);a=fit(p,'synthetic',0);check=mathematics(p,a)
    poison=f.copy();poison.loc[poison.fold.eq(0),'T0']=-1e30
    q=problem(poison,0);assert p['signature']==q['signature'];b=fit(q,'synthetic',0);assert a==b
    changed=f.copy();changed.loc[changed.fold.ne(0)&changed.age_band.eq('17-24'),'T0']*=1.8
    c=fit(problem(changed,0),'synthetic',0);assert not np.array_equal(a['coef'],c['coef'])
    valid=f.loc[f.fold.eq(0)];pred,norm=apply(valid,a);other,nn=apply(valid.assign(T0=-1e30),a)
    assert np.array_equal(pred,other) and norm==nn
    identity,_=apply(valid,{**a,'coef':[0.]*7});assert np.array_equal(identity,valid.baseline_G3)
    unknown,_=apply(valid.assign(age_band='__UNKNOWN__'),a);assert np.array_equal(unknown,valid.baseline_G3)
    dump(OUT/'synthetic.json',{'full_numeric_learning_held_poison_exact':True,'training_change_changes_fit':True,
        'application_held_label_invariance':True,'zero_and_unknown_identity_exact':True,'mathematics':check,
        'synthetic_fits':3,'contest_fits':0})


def prepare():
    assert not OUT.exists();OUT.mkdir()
    with threadpool_limits(limits=2):synthetic()
    pre=w.read(PARENT/'preflight.json');paths=[Path(__file__),Path(stats.__file__),PARENT/'preflight.json',
        PARENT/'oof_2023_2024.parquet',PARENT/'A1_original2024_proxy_prices.parquet',
        BASE/'FSp_NB_aplicacion_20261026_v2/report.json',BASE/'estimando_cartera2025_v3/weights.parquet']
    ages={};scopes=[]
    for line in ['motor','buildings','contents']:
        rowpath=BASE/'FSp_edificios_matrices_20261026_v1/rows_target_prod.parquet' if line=='buildings' else BASE/f'FSp_MC_recuperacion_20261026_v1/matrices/rows_{line}_target_prod.parquet'
        matrixpath=BASE/'FSp_edificios_matrices_20261026_v1/matrix_target_prod.parquet' if line=='buildings' else BASE/f'FSp_MC_recuperacion_20261026_v1/matrices/matrix_{line}_target_prod.parquet'
        paths+=[rowpath,matrixpath];rows=pd.read_parquet(rowpath,columns=['row_id','year']);age=pd.read_parquet(matrixpath,columns=['age_band'])
        assert len(age)==len(rows);cov=pd.DataFrame({'row_id':rows.row_id,'age_band':age.age_band.astype('string')})
        cov=cov.loc[rows.year.isin(YEARS)].copy();assert cov.row_id.is_unique and cov.age_band.isin(LEVELS).all()
        ages[line]=cov.set_index('row_id');cov.to_parquet(OUT/f'age_{line}.parquet',index=False)
    for scope in pre['scopes']:
        line,held=scope['line'],scope['held'];path=ROOT/scope['input'];assert w.sha(path)==scope['sha256'];paths.append(path)
        f=pd.read_parquet(path,columns=['row_id','line','year','group_id','fold','new_business','exposure','T0','reserve','baseline_G3'])
        f['age_band']=ages[line].loc[f.row_id,'age_band'].to_numpy()
        c0path=BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json';paths.append(c0path);c0=w.read(c0path)['artifact']['C0']
        assert sorted(f.loc[f.fold.ne(held),'row_id'])==c0['fit_row_ids'] and c0['excluded_fold']==held
        train=f.loc[f.fold.ne(held)&f.new_business.eq(1)]
        assert all(train.loc[train.year.eq(y),'T0'].sum()>0 for y in YEARS)
        output=OUT/f'inputs_{line}_fold{held}.parquet';f.to_parquet(output,index=False)
        support=train.groupby(['year','age_band'],observed=True).agg(rows=('row_id','size'),positive=('T0',lambda x:int((x>0).sum()))).reset_index().to_dict('records')
        scopes.append({'line':line,'held':held,'input':w.rel(output),'sha256':w.sha(output),'training_NB_rows':len(train),'support':support})
    dump(OUT/'preflight.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scopes':scopes,
        'feature':'policy-supplied age band, fixed5levels; no new undated master feature',
        'existing_C0_and_baseline_ancestry_reused':True,'synthetic_fits':3,'contest_fits':0,'new_scores':0,
        'sources':{w.rel(path):w.sha(path) for path in paths}})
    print(json.dumps({'preflight':'passed','synthetic_fits':3,'real_fits':0,'scopes':15,'new_C0':0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json');assert w.read(OUT/'synthetic.json')['full_numeric_learning_held_poison_exact']
    reference=w.read(R/'registro/semana2_mision017_FSp_NB_aplicacion_plan_v2.json')
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'hypothesis':'A frozen-source G3price may need a small NB-specific age correction in the new market. Test one categorical GLM before more capacity after isolated FSpNB failed; no feature search or tuning.',
        'reference':'G3frozen; REN_FSp remains frozen for the full-portfolio combination. Not complete F3c.',
        'configuration':{'years':YEARS,'folds':'saved global components','training':'NB of non-held groups only',
            'features':['policy age band'],'levels':LEVELS,'new_variables_from_masters':0,
            'objective':'half summed Tweedie1.5deviance divided by S plus symmetric ridge on all5agecoefficients',
            'offset':'log(frozen G3observed-cost period price), already includes exposure and C0; no second exposure',
            'K':K,'S':'sum sqrt(training NB baseline)','ridge_normalized':'K/n_positive_training_NB_periods',
            'year_nuisance':'two unpenalized training-year intercepts, not transferred',
            'application':'exp(agecoefficient), NB-only prediction normalization per held year; REN exact',
            'unknown_age':'neutral0logeffect','optimizer':{'method':'L-BFGS-B','maxiter':2000,'gtol':1e-10,'ftol':1e-15,'maxls':50,'gradient_guard':1e-6},
            'no_choice_of_K_or_bands_from_validation':True},
        'criterion':reference['criterion'],'NB_addition_guard':reference['NB_addition_guard'],
        'bootstrap':{**reference['bootstrap'],'seed':2026102615},
        'budget':{'real_GLM_fits':15,'age_coefficients':75,'nuisance_year_intercepts':30,'synthetic_fits_separate':3,
            'new_C0_fits':0,'new_source_models':0,'new_source_inferences':0,'new_OOF_NB_rows':15037,
            'NB_normalizers':30,'A1_proxy_NB_normalizers':15,'new_test_prices':0,'new_submissions':0},
        'control':'Full numeric X,y,offset,penalty,initialization identical under held-label poison; no refitting actualdata for this check. Synthetic full-fit invariance. Independent onehot, sklearnobjective, gradient/Hessian and replay without optimizer.',
        'limits':['C0aggregateperil mixture remains a conditional observation link; reserve adequacy and full tail not identified',
                  '2024adaptive development, not pristine confirmation','G3and original A1proxy are not corrected full F3c',
                  'No automatic transfer to2025because NBmixture/ESSsupport differs'],
        '2024_open':True,'B00_all_alternatives_preserved':True,
        'sources':{**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),w.rel(OUT/'synthetic.json'):w.sha(OUT/'synthetic.json'),
                   **{x['input']:x['sha256'] for x in pre['scopes']}}}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro un único GLM Tweedie estándar de edad NB por ramo,15ajustes máximo. '
        'Cinco bandas de edad de póliza ya suministradas, sin variables adicionales de maestros, interacciones nuevas o búsqueda de bandas. '
        'Offset de precio G3 congelado, exposición/C0 una sola vez. Se conserva K300 y la escala Fisher usada en la tanda11; '
        'dos interceptos año de entrenamiento no transferidos. Se aplica solo la forma de edad y se conservan los totales NB; REN queda exacta. '
        'El fallo concreto anterior es la inestabilidad de transferencia FSpNB y su sensibilidad2025negativa; no demuestra necesidad de árboles más complejos. '
        'Los criterios y guardas NB no cambian. La aplicación conjunta con REN congelada se mide sin ocultar daño NB. '
        'Tres ajustes sintéticos y la prueba numérica completa pasaron antes; ningún ajuste real o score aún. '
        'Cero nuevos C0, modelos fuente, inferencias de fuente, precios de2025 o envíos. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    q=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-GLM-EDAD-NB-PREVIO','--asunto','GLM estándar de edad NB, fuerte contracción y receta congelada','--cuerpo',str(body)],
        capture_output=True,text=True,encoding='utf8',check=True)
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(q.stdout)})
    print(json.dumps({'registered':True,'real_fit_budget':15,'forum':json.loads(q.stdout)}))


def run():
    assert not (OUT/'started.json').exists();assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    plan=w.read(PLAN);assert all(w.sha(ROOT/path)==sha for path,sha in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':w.sha(PLAN)})
    pre=w.read(OUT/'preflight.json');p=pd.read_parquet(PARENT/'oof_2023_2024.parquet').rename(columns={'RFS1':'RFS_REN'})
    p['RFS_NB']=p.G3;p['RFS_ALL']=p.RFS_REN
    proxy=pd.read_parquet(PARENT/'A1_original2024_proxy_prices.parquet');proxy['A1_G3_NB']=proxy.A1_G3;proxy['A1_G3_ALL']=proxy.A1_G3_RFS1P
    proxy=proxy.join(p[['row_id','line','year','fold','new_business']].set_index('row_id'),on='row_id',validate='one_to_one')
    checks=[];fits=0
    with threadpool_limits(limits=2):
        for scope in pre['scopes']:
            line,held=scope['line'],scope['held'];f=pd.read_parquet(ROOT/scope['input']);pp=problem(f,held)
            path=OUT/f'model_{line}_fold{held}.json';a=fit(pp,line,held,path);fits+=1;mathcheck=mathematics(pp,a)
            poison=f.copy();poison.loc[poison.fold.eq(held),['T0','reserve']]=-1e30;qq=problem(poison,held)
            assert pp['signature']==qq['signature']
            for key in ['X','y','base','offset','penalty','initial']:assert np.array_equal(pp[key],qq[key])
            valid=f.loc[f.fold.eq(held)];pred,norms=apply(valid,a)
            # Explicit replay path has the optimizer blocked, not another fit.
            optimizer=optimize.minimize;optimize.minimize=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Replay must not fit'))
            try:
                replay,nn=apply(valid,w.read(path));assert np.array_equal(pred,replay) and nn==norms
                bad,_=apply(valid.assign(T0=-1e30,reserve=-1e30),a);assert np.array_equal(pred,bad)
            finally:optimize.minimize=optimizer
            idx=pd.Series(p.index.to_numpy(),index=p.row_id).loc[valid.row_id].to_numpy();p.loc[idx,'RFS_NB']=pred
            nb=valid.new_business.eq(1).to_numpy();p.loc[idx[nb],'RFS_ALL']=pred[nb]
            qi=proxy.index[proxy.line.eq(line)&proxy.fold.eq(held)];q=valid.set_index('row_id').loc[proxy.loc[qi,'row_id']].reset_index()
            value,_=apply(q,a,base=proxy.loc[qi,'A1_G3'].to_numpy());proxy.loc[qi,'A1_G3_NB']=value
            qnb=q.new_business.eq(1).to_numpy();proxy.loc[np.asarray(qi)[qnb],'A1_G3_ALL']=value[qnb]
            dump(OUT/f'application_{line}_fold{held}.json',{'normalizers':norms,'model_sha256':w.sha(path)})
            checks.append({'line':line,'fold':held,'full_numeric_optimizer_problem_held_invariant':True,
                           'no_optimizer_saved_replay_exact':True,'held_outcome_application_invariant':True,**mathcheck})
    assert fits==15 and np.array_equal(p.loc[p.new_business.eq(0),'RFS_ALL'],p.loc[p.new_business.eq(0),'RFS_REN'])
    stats.OUT=OUT;scores,comparisons=stats.metrics(p,plan);vetos=stats.additional_veto(p,proxy)
    nb=comparisons['RFS_NB'];guards={'point_nonnegative':nb['delta']>=0,'both_years_nonnegative':all(x>=0 for x in nb['years'].values()),
        'four_folds_positive':sum(x>0 for x in nb['folds'].values())>=4,'lower95_positive':nb['bootstrap95'][0]>0,
        'cell_min':min(x['delta_cell_null'] for x in nb['cells'])>=-.001}
    p.to_parquet(OUT/'oof_2023_2024.parquet',index=False);proxy.to_parquet(OUT/'A1_original2024_proxy_prices.parquet',index=False)
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scores_runner_aliases':scores,
        'aliases':{'RFS_NB':'AGE_NB','RFS_ALL':'frozen REN_FSp plus AGE_NB','RFS_REN':'previous frozen RFS1P'},
        'comparisons':comparisons,'NB_addition_guard':guards,'all_NB_guards_pass':all(guards.values()),'additional_vetoes':vetos,
        'all_full_recipe_primary_gates_pass':all(comparisons['RFS_ALL']['gates'].values()),'formal_admission':False,
        'mathematics_and_numeric_flow_checks':checks,'new_GLM_fits':fits,'new_source_models':0,'new_C0_fits':0,
        'new_source_inferences':0,'new_prediction_only_normalizers':45,'synthetic_fits_separate':3,
        'new_test_prices':0,'new_submissions':0,'plan_sha256':w.sha(PLAN),'B00_all_alternatives_preserved':True,
        '2024_open':True,'goal_achieved':False,'full_F3c_comparator_missing':True}
    assert all(w.sha(ROOT/path)==sha for path,sha in plan['sources'].items());dump(OUT/'report.json',result)
    print(json.dumps({'scores':scores,'AGE_NB_delta':nb['delta'],'AGE_NB_bootstrap95':nb['bootstrap95'],'NB_guards':guards,
        'full_delta':comparisons['RFS_ALL']['delta'],'full_gates':comparisons['RFS_ALL']['gates'],'vetoes':vetos,
        'new_GLM_fits':fits,'new_C0':0,'new_submissions':0}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','register','run'])
    a=parser.parse_args();{'prepare':prepare,'register':register,'run':run}[a.mode]()
