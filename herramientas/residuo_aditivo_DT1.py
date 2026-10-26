"""Corrección aditiva DT1 acotada: una receta, ámbitos guardados, sin C0 nuevo."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HOME=BASE/'A1S_nucleo_20261026_v1'
OUT=BASE/'residuo_aditivo_DT1_20261026_v1'
PROPOSAL=R/'registro/semana2_mision017_residuo_acotado_propuesta_v1.json'
PLAN=R/'registro/semana2_mision017_DT1_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


d=load('DT1_existing_statistics',R/'herramientas/glm_discrepancia_A1S.py')
w=d.w;g=d.c.g;LINES=d.LINES
leaf=load('DT1_independent_leaf_sum',R/'herramientas/entrenar_nucleo_A1S.py').leaf_sum
PROPOSED=w.read(PROPOSAL);PARAMS=PROPOSED['parameters'];ROUNDS=PROPOSED['fixed_rounds']


def utc():return datetime.now(timezone.utc).isoformat()


def dump(path,a):
    assert not path.exists(),'Preserve artifact: '+str(path)
    path.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')


def problem(f,x,held):
    assert len(f)==len(x) and np.array_equal(f.index,x.index)
    mask=f.fold.ne(held).to_numpy();train=f.loc[mask]
    assert not set(train.group_id).intersection(f.loc[~mask,'group_id'])
    y=train.T0.to_numpy(float);base=train.baseline_G3.to_numpy(float)
    assert (y>=0).all() and (base>0).all() and np.isfinite(y).all()
    init=np.log(base);levels={}
    for year in [2023,2024]:
        for nb in [0,1]:
            sel=train.year.eq(year).to_numpy()&train.new_business.eq(nb).to_numpy()
            assert sel.any() and y[sel].sum()>0
            k=d.c.b.factor(y[sel],base[sel]);levels[f'{year}|{nb}']=k
            init[sel]+=np.log(k)
    X=x.loc[mask].copy()
    numeric={'y':y,'init_score':init,'baseline':base}
    h=hashlib.sha256()
    h.update(pd.util.hash_pandas_object(X,index=False).to_numpy().tobytes())
    cats={col:list(X[col].cat.categories) for col in X if isinstance(X[col].dtype,pd.CategoricalDtype)}
    h.update(json.dumps({'cols':list(X),'categories':cats,'params':PARAMS,'rounds':ROUNDS},sort_keys=True).encode())
    for key,a in numeric.items():h.update(key.encode());h.update(a.tobytes())
    h.update(json.dumps(train.row_id.tolist()).encode())
    return {'X':X,'y':y,'init_score':init,'levels':levels,'signature':h.hexdigest(),
            'training_rows':len(train),'held_rows':int((~mask).sum()),'mask':mask}


def fit(p,folder):
    folder.mkdir()
    dump(folder/'fit_invoked.json',{'utc':utc(),'pid':os.getpid(),'rounds':ROUNDS,'problem_signature':p['signature']})
    started=time.monotonic()
    model=lgb.train(PARAMS,lgb.Dataset(p['X'],label=p['y'],init_score=p['init_score']),num_boost_round=ROUNDS)
    model.save_model(str(folder/'model.txt'))
    record={'utc':utc(),'pid':os.getpid(),'model_sha256':w.sha(folder/'model.txt'),'parameters':PARAMS,
            'actual_rounds':model.current_iteration(),'rounds_limit':ROUNDS,'seconds':time.monotonic()-started,
            'training_rows':p['training_rows'],'held_rows':p['held_rows'],'problem_signature':p['signature'],
            'nuisance_year_business_levels':p['levels'],'nuisance_not_transferred':True,'lightgbm_version':lgb.__version__}
    dump(folder/'record.json',record)
    return model,record


def tree_bound(model):
    bound=PARAMS['learning_rate']*PARAMS['max_delta_step'];maxleaf=0.;depths=[]
    for tree in model.dump_model()['tree_info']:
        def visit(node,depth=0):
            nonlocal maxleaf
            if 'leaf_value' in node:
                maxleaf=max(maxleaf,abs(float(node['leaf_value'])));return depth
            return max(visit(node['left_child'],depth+1),visit(node['right_child'],depth+1))
        depths.append(visit(tree['tree_structure']))
    assert max(depths)<=1 and maxleaf<=bound+1e-12
    assert model.current_iteration()<=ROUNDS
    return {'max_depth':max(depths),'max_final_leaf_abs':maxleaf,'leaf_bound':bound,
            'raw_delta_bound':ROUNDS*bound,'normalized_ratio_bounds':np.exp(np.array([-2,2])*ROUNDS*bound).tolist()}


def apply(f,raw):
    assert np.isfinite(raw).all() and np.max(np.abs(raw))<=.06+1e-10
    pred,norm=g.normalise(f,f.baseline_G3.to_numpy(float),np.exp(raw))
    ratio=pred/f.baseline_G3.to_numpy(float)
    assert ratio.min()>=np.exp(-.12)-1e-12 and ratio.max()<=np.exp(.12)+1e-12
    return pred,norm


def numerical_checks(model,folder,x,p,f,raw):
    bound=tree_bound(model);loaded=lgb.Booster(model_file=str(folder/'model.txt'))
    sample=np.unique(np.linspace(0,len(x)-1,min(32,len(x)),dtype=int))
    assert np.array_equal(raw[sample],loaded.predict(x.iloc[sample],raw_score=True,num_threads=2))
    assert np.array_equal(raw[sample[::-1]],loaded.predict(x.iloc[sample[::-1]],raw_score=True,num_threads=2))
    independent=leaf(loaded,x.iloc[sample[:6]])
    assert np.max(np.abs(independent-raw[sample[:6]]))<1e-12
    train_raw=model.predict(p['X'],raw_score=True,num_threads=2)
    mu=np.exp(train_raw+p['init_score'])
    loss=d.unit(p['y'],mu).mean();sk=mean_tweedie_deviance(p['y'],mu,power=1.5)
    assert abs(loss-sk)<1e-9
    pred,norm=apply(f,raw)
    assert np.array_equal(pred,apply(f.assign(T0=-1e30,reserve=-1e30),raw)[0])
    identity,_=apply(f,np.zeros(len(f)));assert np.array_equal(identity,f.baseline_G3.to_numpy())
    return {**bound,'save_load_and_order_exact':True,'independent_leaf_sum':True,
            'sklearn_Tweedie_metric':True,'init_score_external_exposure_once':True,
            'zero_delta_identity_exact':True,'prediction_held_labels_invariant':True}


def synthetic():
    rng=np.random.default_rng(2026102613);n=8000
    xx=rng.uniform(-1,1,n)
    x=pd.DataFrame({'continuous':xx,'categorical':pd.Categorical(rng.choice(['a','b'],n))})
    base=rng.uniform(40,120,n)
    f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
        'fold':np.arange(n)%5,'year':2023+(np.arange(n)//5)%2,'new_business':(np.arange(n)//10)%2,
        'baseline_G3':base,'T0':rng.gamma(2,base/2)*np.exp(.5*xx),'reserve':0.})
    p=problem(f,x,0);model,_=fit(p,OUT/'synthetic_normal')
    valid=f.loc[~p['mask']];vx=x.loc[~p['mask']]
    raw=model.predict(vx,raw_score=True,num_threads=2)
    check=numerical_checks(model,OUT/'synthetic_normal',vx,p,valid,raw)
    bad=f.copy();bad.loc[bad.fold.eq(0),['T0','reserve']]=-1e30
    q=problem(bad,x,0);assert p['signature']==q['signature']
    other,_=fit(q,OUT/'synthetic_poisoned')
    assert model.model_to_string()==other.model_to_string()
    assert np.array_equal(raw,other.predict(vx,raw_score=True,num_threads=2))
    changed=f.copy();mask=changed.fold.ne(0);changed.loc[mask,'T0']*=np.exp(-xx[mask])
    alt,_=fit(problem(changed,x,0),OUT/'synthetic_training_changed')
    assert model.model_to_string()!=alt.model_to_string()
    return {'synthetic_model_fits':3,'contest_fits':0,'complete_fit_held_poison_invariant':True,
            'training_response_changes_model':True,'source_risk_is_external_offset_not_saved_initial_bias':True,
            'actual_saved_tree_bounds_verified':check}


def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert phase.get('active_execution') is None and not phase.get('active_jobs')
    paths=[Path(__file__),Path(d.__file__),Path(g.__file__),Path(d.c.__file__),Path(d.c.b.__file__),
           R/'herramientas/entrenar_nucleo_A1S.py',PROPOSAL,HOME/'report.json',
           BASE/'GLM_discrepancia_A1S_20261026_v1/report.json']
    inputreport=w.read(HOME/'report.json');scopes=[]
    for line in LINES:
        xp=HOME/f'matrix_s2_{line}.parquet';rp=HOME/f'rows_s2_{line}.parquet';paths+=[xp,rp]
        x=pd.read_parquet(xp);ids=pd.read_parquet(rp,columns=['row_id'])
        expected=next(v['features'] for v in inputreport['results'] if v['line']==line)
        assert list(x)==expected and len(x)==len(ids)
        assert not {'T0','reserve','original_premium','renewal_decision','row_id'}.intersection(x)
        ix=pd.Series(np.arange(len(ids)),index=ids.row_id);assert ix.index.is_unique
        historical=pd.read_parquet(BASE/f'GLM_discrepancia_A1S_20261026_v1/inputs_{line}_fold0.parquet',columns=['row_id'])
        matrix=x.iloc[ix.loc[historical.row_id].to_numpy()].reset_index(drop=True)
        mp=OUT/f'matrix_{line}.parquet';matrix.to_parquet(mp,index=False)
        for held in range(5):
            inp=BASE/f'GLM_discrepancia_A1S_20261026_v1/inputs_{line}_fold{held}.parquet'
            cp=BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json';paths+=[inp,cp]
            f=pd.read_parquet(inp,columns=['row_id','line','year','group_id','fold','new_business','exposure','T0','reserve','baseline_G3','e_cost_scope'])
            assert np.array_equal(f.row_id,historical.row_id)
            c0=w.read(cp)['artifact']['C0'];train=f.fold.ne(held)
            assert c0['excluded_fold']==held and sorted(f.loc[train,'row_id'])==c0['fit_row_ids']
            assert f.year.isin([2023,2024]).all() and f.row_id.is_unique
            assert not set(f.loc[train,'group_id']).intersection(f.loc[~train,'group_id'])
            fp=OUT/f'inputs_{line}_fold{held}.parquet';f.to_parquet(fp,index=False)
            scopes.append({'line':line,'held':held,'input':w.rel(fp),'sha256':w.sha(fp),
                           'matrix':w.rel(mp),'matrix_sha256':w.sha(mp),'C0_parent':w.rel(cp),'C0_parent_sha256':w.sha(cp)})
    with threadpool_limits(limits=2):dump(OUT/'synthetic.json',synthetic())
    dump(OUT/'preflight.json',{'utc':utc(),'author':'Codex','scopes':scopes,'sources':{w.rel(p):w.sha(p) for p in paths},
        'contest_fits':0,'new_C0_fits':0,'new_scores':0,'feature_counts':{line:len(pd.read_parquet(OUT/f'matrix_{line}.parquet').columns) for line in LINES}})
    print(json.dumps({'preflight':'passed','synthetic_fits':3,'scopes':15,'contest_fits':0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json');syn=w.read(OUT/'synthetic.json')
    assert syn['complete_fit_held_poison_invariant'] and syn['actual_saved_tree_bounds_verified']['max_depth']<=1
    sources={**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),w.rel(OUT/'synthetic.json'):w.sha(OUT/'synthetic.json')}
    for a in pre['scopes']:sources.update({a['input']:a['sha256'],a['matrix']:a['matrix_sha256']})
    assert all(w.sha(ROOT/p)==v for p,v in sources.items())
    plan={**PROPOSED,'author':'Codex','utc':utc(),'status':'registered_before_contest_fit_score',
          'primary_candidate':'DT1 only','parameters':PARAMS,'fixed_rounds':ROUNDS,
          'feature_counts':pre['feature_counts'],'synthetic_complete_flow':syn,
          'criterion':w.read(d.PLAN)['criterion'],'bootstrap':{'replicates':2000,'seed':2026102613,'unit':'saved global component'},
          'sources':sources,'budget':PROPOSED['budget_if_registered'],'technical_controls':'Whole numeric training problem hash under held poisoning; saved full-model replay and leaf bounds, independent leaf sum and Tweedie calculation. No contest refit for invariance;3synthetic complete fits separately.'}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro DT1 antes del primer ajuste o score del concurso. Una única corrección aditiva con 60 árboles de una división sobre G3, 15 ajustes máximo. '
        'Usa las 51/43/44 covariables oficiales ya guardadas; no añade A1S como precio o eje ni busca pesos. '
        'Difiere de B05/B09 por el offset fuente G3, ambos años y corrección acotada; T9 solo reajustaba hojas antiguas. '
        'Los cuatro niveles año/negocio de entrenamiento sirven de nuisance y no se transfieren. Se mantienen los totales G3 por predicciones, sin etiquetas retenidas. '
        'Tres ajustes sintéticos del flujo completo pasaron: etiquetas retenidas alteradas no cambian modelos, cambio en entrenamiento sí; modelo guardado sin sesgo inicial oculto, profundidad y hojas acotadas, suma independiente de hojas y métrica. '
        'Máxima corrección bruta de log-riesgo 0,06; tras normalizar, razón de precios dentro de exp(±0,12), cota que también se comprobará en cada modelo real. '
        'Parámetros, 60 rondas y criterios previos fijos, sin búsqueda ni early stopping. C0 y árboles fuente no se reestiman. '
        'B00/F3c 0,16914 y alternativas conservados; 2024 abierto y adaptativo. Sin precios finales de 2025 ni envíos. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-DT1-PREVIO','--asunto','DT1 registrado: corrección aditiva pequeña, flujo y cotas comprobados',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'utc':utc(),'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'forum':json.loads(response.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':utc(),'pid':os.getpid(),'plan_sha256':w.sha(PLAN)})
    oof=pd.read_parquet(BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet');oof['DT1']=np.nan
    idx=pd.Series(oof.index.to_numpy(),index=oof.row_id);checks=[]
    with threadpool_limits(limits=2):
        for scope in w.read(OUT/'preflight.json')['scopes']:
            f=pd.read_parquet(ROOT/scope['input']);x=pd.read_parquet(ROOT/scope['matrix'])
            p=problem(f,x,scope['held']);folder=OUT/f'model_{scope["line"]}_fold{scope["held"]}'
            model,record=fit(p,folder)
            bad=f.copy();bad.loc[bad.fold.eq(scope['held']),['T0','reserve']]=-1e30
            q=problem(bad,x,scope['held']);assert p['signature']==q['signature']
            valid=f.loc[~p['mask']];vx=x.loc[~p['mask']]
            raw=model.predict(vx,raw_score=True,num_threads=2)
            check=numerical_checks(model,folder,vx,p,valid,raw)
            original=lgb.train
            def reject(*args,**kwargs):raise AssertionError('No training during replay')
            lgb.train=reject
            try:
                loaded=lgb.Booster(model_file=str(folder/'model.txt'))
                reproduced=loaded.predict(vx,raw_score=True,num_threads=2)
                assert np.array_equal(raw,reproduced)
                pred,norm=apply(valid,reproduced)
            finally:lgb.train=original
            ii=idx.loc[valid.row_id].to_numpy();oof.loc[ii,'DT1']=pred
            pd.DataFrame({'row_id':valid.row_id,'raw_delta':raw,'DT1':pred}).to_parquet(folder/'held_predictions.parquet',index=False)
            dump(folder/'application.json',{'held_normalizers':norm,'checks':check,'full_numeric_problem_held_response_invariant':True,
                                          'replay_with_training_blocked_exact':True})
            checks.append({'line':scope['line'],'held':scope['held'],**check,'full_numeric_problem_held_response_invariant':True})
            print(json.dumps({'completed':folder.name,'rounds':record['actual_rounds'],'max_leaf':check['max_final_leaf_abs']}),flush=True)
        assert oof.DT1.notna().all() and oof.DT1.gt(0).all()
        oof.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
        d.OUT=OUT
        result=d.statistics(oof.rename(columns={'DT1':'D1'}),plan)
        result['scores']['DT1']=result['scores'].pop('D1')
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    report={'author':'Codex','utc':utc(),'status':'complete_exploratory_no_formal_admission','rows':len(oof),
            'new_target_price_model_fits':15,'new_nuisance_closed_levels':60,'new_source_fits':0,'new_C0_fits':0,
            'synthetic_fits_separate':3,'new_final_test_prices':0,'new_submissions':0,'numeric_controls':checks,
            'plan_sha256':w.sha(PLAN),'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,**result}
    dump(OUT/'report.json',report)
    print(json.dumps({k:report[k] for k in ['scores','delta_vs_G3','bootstrap95','fold_contributions','year_contributions','post31_delta','gates','weighted2025_sensitivity_delta']},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','register','run']);a=p.parse_args()
    {'prepare':prepare,'register':register,'run':run}[a.mode]()
