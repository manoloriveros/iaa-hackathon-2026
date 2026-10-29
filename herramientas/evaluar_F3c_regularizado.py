"""Comparación preinscrita F3c-R, sin ajuste, selección pública ni envío."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import math
import os
import sys
import time
import traceback
from unittest.mock import patch

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
import preparar_destino_F3c_regularizado as p
import continuar_destino_F3c_regularizado as execution
import entradas_F3c_regularizado as inp
import calibrador_F3c_regularizado as model
import registrar_avance_mision017_fase2 as w

BASE=R/'privado/semana2/F3c_regularizado_20261028'
TARGET=BASE/'target_real';OUT=BASE/'assessment'
PLAN=R/'registro/semana2_F3c_regularizado_evaluacion_plan.json'
DOC=R/'docs/archivo/semana2/F3C_REGULARIZADO_RESULTADOS_20261028.md'
OLD=inp.f.OUT;ACTIVE=inp.f.ACTIVE
AUDIT=inp.e.audit
NAMES=['F3c_R','matched_trainlevel_full','public_full']
COMPS=[('F3c_R','matched_trainlevel_full'),('F3c_R','public_full')]
COMP_NAMES=[a+'_vs_'+b for a,b in COMPS]
BROAD=['global','new_business','renewal']+inp.LINES
CELLS=[line+'_'+str(nb) for line in inp.LINES for nb in [0,1]]


def status(state,**kw):
    v={'author':'Codex','utc':p.utc(),'pid':os.getpid(),'state':state,**kw}
    temp=OUT/'status.tmp'
    with temp.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(temp,OUT/'status.json')


def masks(frame):
    nb=frame.new_business.eq(1).to_numpy()
    return {'global':np.ones(len(frame),bool),'new_business':nb,'renewal':~nb,
        **{line:frame.line.eq(line).to_numpy() for line in inp.LINES},
        **{line+'_'+str(b):frame.line.eq(line).to_numpy()&(nb==b) for line in inp.LINES for b in [0,1]},
        **{'saved_fold_'+str(k):frame.saved_fold.eq(k).to_numpy() for k in range(5)},
        'duration_short':frame.exposure.lt(.5).to_numpy(),
        'duration_medium':(frame.exposure.ge(.5)&frame.exposure.lt(.9)).to_numpy(),
        'duration_long':frame.exposure.ge(.9).to_numpy()}


def validate_arrays(frame,prices,y):
    assert frame.row_id.is_unique and len(frame)==len(y)
    assert np.isfinite(y).all() and (y>=0).all() and (y>0).any()
    assert set(prices)==set(NAMES)
    assert all(np.shape(v)==np.shape(y) and np.isfinite(v).all() and (v>0).all() for v in prices.values())
    assert set(frame.line)==set(inp.LINES) and set(frame.new_business)=={0,1}
    assert set(frame.saved_fold)==set(range(5)) and np.isfinite(frame.exposure).all() and frame.exposure.gt(0).all()


def score(y,mu,weight=None):
    weight=np.ones(len(y)) if weight is None else np.asarray(weight,float)
    den=AUDIT.null_loss(y,weight)
    assert den>0,'Segmento sin devianza nula positiva'
    return float(1-math.fsum((AUDIT.loss(y,mu)*weight).tolist())/den)


def independent_score(y,mu,weight=None):
    mean=np.average(y,weights=weight)
    den=mean_tweedie_deviance(y,np.full(len(y),mean),power=1.5,sample_weight=weight)
    return float(1-mean_tweedie_deviance(y,mu,power=1.5,sample_weight=weight)/den)


def stats_for_bootstrap(y,gains,ix,G,weights):
    arrays=[]
    for ww in weights.values():
        vals=[ww,ww*y,ww*np.sqrt(y)]+[ww*gains[:,j] for j in range(gains.shape[1])]
        arrays.append(np.stack([np.bincount(ix,weights=v,minlength=G) for v in vals],axis=1))
    return np.stack(arrays,axis=1).reshape(G,-1)


def grouped_draws(y,gains,groups,weights,draw_count,seed,first_expected=None):
    universe,ix=np.unique(groups,return_inverse=True);G=len(universe);C=gains.shape[1];W=len(weights)
    flat=stats_for_bootstrap(y,gains,ix,G,weights);rng=np.random.default_rng(seed)
    draws=np.empty((draw_count,W,C));first=None;direct_errors=[]
    for start in range(0,draw_count,25):
        size=min(25,draw_count-start)
        counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(size)])
        z=(counts@flat).reshape(size,W,3+C)
        den=8*(np.sqrt(z[:,:,0]*z[:,:,1])-z[:,:,2]);assert (den>0).all()
        draws[start:start+size]=z[:,:,3:]/den[:,:,None]
        if start==0:
            first=counts[:min(20,size)].copy()
            if first_expected is not None:assert np.array_equal(first[:len(first_expected)],first_expected)
            # Verificación por filas, otra agregación y sumas de precisión extendida.
            for i,one in enumerate(first):
                for j,ww in enumerate(weights.values()):
                    effective=one[ix]*ww;den2=AUDIT.null_loss(y,effective)
                    direct=np.array([math.fsum((effective*gains[:,c]).tolist())/den2 for c in range(C)])
                    direct_errors.append(float(np.max(np.abs(direct-draws[i,j]))))
    assert max(direct_errors)<1e-10
    return draws,first,{'max_direct_draw_error':max(direct_errors),'groups':G,'draws':draw_count}


def calculate(frame,prices,y,groups,composition,scenarios,draw_count=10000,first_expected=None):
    validate_arrays(frame,prices,y);ms=masks(frame)
    gains=np.stack([AUDIT.loss(y,prices[b])-AUDIT.loss(y,prices[a]) for a,b in COMPS],axis=1)
    results={};score_errors=[]
    for name,mask in ms.items():
        assert mask.any() and AUDIT.null_loss(y[mask])>0
        d2={key:score(y[mask],v[mask]) for key,v in prices.items()}
        score_errors += [abs(d2[key]-independent_score(y[mask],v[mask])) for key,v in prices.items()]
        delta=gains[mask].sum(axis=0)/AUDIT.null_loss(y[mask])
        assert np.allclose(delta,[d2[a]-d2[b] for a,b in COMPS],rtol=1e-10,atol=1e-12)
        results[name]={'rows':int(mask.sum()),'positive_periods':int((y[mask]>0).sum()),
            'observed_cost':float(y[mask].sum()),'predicted_cost':{k:float(v[mask].sum()) for k,v in prices.items()},
            'AE':{k:float(y[mask].sum()/v[mask].sum()) for k,v in prices.items()},
            'D2':d2,'deltas':dict(zip(COMP_NAMES,delta.tolist()))}
    assert np.isfinite(composition).all() and (composition>=0).all() and composition.sum()>0
    weights={name:ms[name].astype(float) for name in BROAD}
    weights.update(mix2025_global=composition,mix2025_new_business=composition*ms['new_business'])
    for name,ww in weights.items():
        if name.startswith('mix'):
            results[name]={'composition_only_not_future_labels':True,'D2':{k:score(y,v,ww) for k,v in prices.items()},
                'deltas':dict(zip(COMP_NAMES,((gains*ww[:,None]).sum(axis=0)/AUDIT.null_loss(y,ww)).tolist()))}
    draws,first,proof=grouped_draws(y,gains,groups,weights,draw_count,2026102301,first_expected)
    for j,name in enumerate(weights):
        results[name]['CI95']={c:np.quantile(draws[:,j,k],[.025,.975]).tolist() for k,c in enumerate(COMP_NAMES)}
        results[name]['family20']={c:np.quantile(draws[:,j,k],[.05/40,1-.05/40]).tolist() for k,c in enumerate(COMP_NAMES)}
    universe,ix=np.unique(groups,return_inverse=True);G=len(universe)
    positive=np.flatnonzero(y>0);top=positive[np.argsort(-y[positive],kind='stable')[:max(1,math.ceil(.01*len(positive)))]]
    tail={'positive_top_rows':len(top),'T0_cost_share':float(y[top].sum()/y.sum()),'gain_shares':{}}
    influence={};gates={}
    for j,comp in enumerate(COMP_NAMES):
        bygroup=np.bincount(ix,weights=gains[:,j],minlength=G);remove=max(5,math.ceil(.001*G))
        order=np.argsort(-bygroup,kind='stable');keep=~np.isin(ix,order[:remove])
        delta=float(gains[keep,j].sum()/AUDIT.null_loss(y[keep]))
        influence[comp]={'removed_favorable_groups':remove,'delta_after_removal':delta,
            'total_gain':float(gains[:,j].sum()),'removed_gain':float(bygroup[order[:remove]].sum())}
        tail['gain_shares'][comp]={'top_rows_gain':float(gains[top,j].sum()),'remaining_rows_gain':float(gains[:,j].sum()-gains[top,j].sum())}
        gates[comp]={'global_family20_lower_above_margin':results['global']['family20'][comp][0]>.0005,
            'NB_nonnegative_and_lower95_floor':results['new_business']['deltas'][comp]>=0 and results['new_business']['CI95'][comp][0]>=-.001,
            'broad_and_sixcell_floor':all(results[n]['deltas'][comp]>=-.001 for n in BROAD[1:]+CELLS),
            'four_savedfolds_positive':sum(results['saved_fold_'+str(k)]['deltas'][comp]>0 for k in range(5))>=4,
            'top_favorable_group_removal_nonnegative':delta>=0}
    stresses=[]
    for name,ys in scenarios:
        assert ys.shape==y.shape and np.isfinite(ys).all() and (ys>=0).all()
        gs=np.stack([AUDIT.loss(ys,prices[b])-AUDIT.loss(ys,prices[a]) for a,b in COMPS],axis=1)
        values={n:dict(zip(COMP_NAMES,(gs[ms[n]].sum(axis=0)/AUDIT.null_loss(ys[ms[n]])).tolist())) for n in BROAD}
        stresses.append({'scenario':name,'deltas':values})
    stressfloors={c:min(z['deltas'][n][c] for z in stresses for n in BROAD[1:]) for c in COMP_NAMES}
    for c in COMP_NAMES:gates[c]['fixed_price_stress_broad_floor']=stressfloors[c]>=-.001
    result={'metrics':results,'influence':influence,'tail':tail,'gates':gates,'groups':G,'family':20,
        'conditional_intervals_after_adaptive_search':True,'max_independent_point_score_error':max(score_errors),'bootstrap_proof':proof}
    assert max(score_errors)<1e-10
    return result,draws,first,{'scenarios':stresses,'worst_broad_delta':stressfloors,'fixed_prices_no_relearning':True,'no_scenario_probability_claim':True}


def register():
    execution.guard();assert not PLAN.exists() and not OUT.exists();OUT.mkdir()
    folds=ROOT/w.read(ROOT/'RUTAS_PROYECTO.json')['week_2_validation_partitions']
    deps=[Path(__file__),Path(execution.__file__),Path(inp.__file__),Path(model.__file__),Path(p.__file__),
        p.PLAN,execution.PLAN,R/'registro/semana2_F3c_regularizado_plan.json',
        OLD/'predictions2024.parquet',OLD/'labels2024.parquet',OLD/'parameters.json',
        ACTIVE/'predictions_T2b.parquet',ACTIVE/'composition_bootstrap_T2b.npz',ACTIVE/'scenario_results.json',
        inp.f.BASE/'revision_chat_documento_20261027/first4_original_group_multiplicities.npy',folds,
        Path(AUDIT.__file__)]
    deps+=list((ACTIVE/'scenarios').glob('*.npz'))
    plan={'author':'Codex','utc':p.utc(),'candidate':'F3c-R','comparisons':COMPS,
        'configuration':'Sin cambiar propuesta ni calibrador; evaluar solo despues del sello y controles destino reales.',
        'metric':'Tweedie D2 p1.5 por prima de periodo, sin ponderacion adicional por exposicion',
        'gates':p.read(R/'registro/semana2_F3c_regularizado_plan.json')['future_gates'],
        'bootstrap':{'draws':10000,'seed':2026102301,'groups':'componentes cliente-direccion2024','family':20,'quantiles':[.05/40,1-.05/40],
            'limit':'Dos nuevos contrastes finales; familia condicional, no correccion de toda la busqueda adaptativa ni refit bootstrap.'},
        'stresses':{'count':50,'source':'escenarios existentes congelados; precios fijos, sin volver a aprender','broad_floor':-.001},
        'whole_learning_stability':{'reuse':'cinco modelos de calibrador exteriores ya ajustados y sus propios troncos/curvas por ambito; lambda comun elegida solo con2023',
            'new_fit_count':0,'diagnostic_predictions2024':5,'not_selectable_candidates':True,
            'acceptance_before_production':'En cada omision de un fold, delta global>=0 y deltaNB>=-0.001 frente al control de su MISMO ambito y frente a public_full original.',
            'reason':'Concretar requisito pendiente de estabilidad del aprendizaje completo antes de generar o ver estos diagnosticos. Umbrales de las dos comparaciones finales intactos.',
            'limit':'Cinco omisiones deterministas; no garantiza comportamiento privado ni cubre toda incertidumbre de entrenamiento.'},
        'support':'Conservar analisis por duracion y advertencia de edificios nuevos largos; no retirar costes ni reagrupar bandas.',
        'checks':['alinea claves/metadatos/T0 por igualdad exacta','punto por sklearn','primeros20sorteos por filas y sumas independientes','fixture y controles adversos','aprendizaje bloqueado al producir diagnosticos de estabilidad'],
        'budget':{'new_fits':0,'synthetic_fits':0,'new2025_predictions':0,'submissions':0},
        'dependencies':[{'path':w.rel(q),'sha256':p.sha(q)} for q in deps]}
    p.dump(PLAN,plan)
    forum=p.io.post('Codex. Registro evaluador F3c-R antes de precios/resultados nuevos: dos comparaciones ya acordadas, familia20,10000sorteos por grupos y50escenarios existentes. '
        'Concreto el requisito de estabilidad completa usando cinco omisiones de folds cuyos modelos ya estan preinscritos: sin nuevos fits, misma lambda2023; cada omision debe conservar delta global no negativo yNB>=-0.001 frente a su control de mismo ambito y a F3c original. '
        'Son diagnosticos no seleccionables; no escoger el mejor fold ni retocar umbrales. Se informan soporte y duracion, influencia y cola. Primero prueba sintetica sin ajuste; luego solo al concluir controles reales destino. '
        'Conservo F3c/R1/B00 y adversos; sin2025 ni envio. Plan '+w.rel(PLAN)+' SHA '+p.sha(PLAN)+'.',
        'COD-S2-20261028-F3CR-EVALUADOR-PREVIO','F3c-R: comparacion y estabilidad del aprendizaje preinscritas')
    p.dump(OUT/'registration.json',{'utc':p.utc(),'plan_sha256':p.sha(PLAN),'forum':forum})
    status('REGISTERED');print(json.dumps({'registered':True,'plan_sha256':p.sha(PLAN)}),flush=True)


def guard():
    execution.guard();assert p.read(OUT/'registration.json')['plan_sha256']==p.sha(PLAN)
    amendment=p.read(OUT/'fixture_admission.json') if (OUT/'fixture_admission.json').exists() else {}
    for d in p.read(PLAN)['dependencies']:
        expected=amendment.get('corrected_dependencies',{}).get(d['path'],d['sha256'])
        assert p.sha(ROOT/d['path'])==expected,d['path']


def admit_fixture():
    assert not (OUT/'fixture_admission.json').exists() and not (OUT/'synthetic.json').exists()
    changes={d['path']:p.sha(ROOT/d['path']) for d in p.read(PLAN)['dependencies'] if p.sha(ROOT/d['path'])!=d['sha256']}
    assert set(changes)=={w.rel(Path(__file__))}
    forum=p.io.post('Codex. El fixture del evaluador no contenia periodos largos>=0.9; el control de segmento vacio detuvo correctamente la prueba. '
        'Amplio solo las exposiciones artificiales para cubrir las tres bandas predefinidas. No cambio el calculo, tolerancias, bandas reales ni criterios. '
        'Se conserva el codigo fallido y la traza; cero fits y cero scores reales. Repito exclusivamente esta prueba del evaluador nuevo.',
        'COD-S2-20261028-F3CR-EVALUADOR-FIXTURE','F3c-R: cobertura del fixture del evaluador antes de datos reales')
    p.dump(OUT/'fixture_admission.json',{'utc':p.utc(),'corrected_dependencies':changes,'forum':forum,'new_fits':0,'real_scores':0})


def synthetic():
    guard();assert not (OUT/'synthetic.json').exists()
    frame=p.fixture().loc[lambda d:d.year.eq(2023)].copy();frame['saved_fold']=frame.fold
    frame['exposure']=(30+11*(np.arange(len(frame))%30))/365.
    # Cada grupo contiene los seis ramos/negocios: remuestrear grupos conserva su dependencia.
    frame['group']=frame.fold.astype(str)+'_'+(np.arange(len(frame))%30).astype(str)
    y=frame.y.to_numpy();mu=(100+80*frame.line.map(dict(zip(inp.LINES,range(3)))).to_numpy())*frame.exposure.to_numpy()
    prices={'F3c_R':mu,'matched_trainlevel_full':mu*1.15,'public_full':mu*.75}
    future=np.linspace(.5,1.5,len(frame));scenarios=[('base',y),('up',y*1.25),('late_proxy',y*(1+.5*(np.arange(len(y))%3==0)))]
    result,draws,first,stresses=calculate(frame,prices,y,frame.group.to_numpy(),future,scenarios,draw_count=125)
    checks={'two_comparisons_dimension':draws.shape==(125,8,2),'point_independent':result['max_independent_point_score_error']<1e-10,
        'draws_independent':result['bootstrap_proof']['max_direct_draw_error']<1e-10,'all_masks_present':len(result['metrics'])==22,
        'all_stresses':len(stresses['scenarios'])==3,'group_count_correct':result['groups']==150}
    identical={k:mu.copy() for k in NAMES}
    gains=np.stack([AUDIT.loss(y,identical[b])-AUDIT.loss(y,identical[a]) for a,b in COMPS],axis=1)
    checks['identical_predictions_zero_gain']=np.array_equal(gains,np.zeros_like(gains))
    for key in ['duplicate','negative','missing_fold','bad_price']:
        ff=frame.copy();yy=y.copy();pp={k:v.copy() for k,v in prices.items()}
        if key=='duplicate':ff.iloc[0,ff.columns.get_loc('row_id')]=ff.row_id.iloc[1]
        elif key=='negative':yy[0]=-1
        elif key=='missing_fold':ff.loc[ff.saved_fold.eq(4),'saved_fold']=3
        else:pp['F3c_R'][0]=0
        try:validate_arrays(ff,pp,yy);checks['reject_'+key]=False
        except AssertionError:checks['reject_'+key]=True
    record={'author':'Codex','utc':p.utc(),'checks':checks,'all_passed':all(checks.values()),'new_fits':0,
        'max_independent_point_error':result['max_independent_point_score_error'],'bootstrap_proof':result['bootstrap_proof']}
    p.dump(OUT/'synthetic.json',record);assert record['all_passed'],checks
    print(json.dumps({'synthetic_passed':True,'checks':checks}),flush=True)


def load_target():
    seal=p.read(TARGET/'artifact_seal.json')
    for name,digest in seal['files'].items():assert p.sha(TARGET/name)==digest
    assert p.read(TARGET/'controls.json')['all_passed']
    pred=pd.read_parquet(TARGET/'predictions2024.parquet').sort_values('row_id').reset_index(drop=True)
    old=pd.read_parquet(OLD/'predictions2024.parquet').sort_values('row_id').reset_index(drop=True)
    assert pred.row_id.is_unique and np.array_equal(pred.row_id,old.row_id) and len(pred)==59202
    for col in ['line','new_business','exposure']:assert np.array_equal(pred[col],old[col])
    for col in ['customer_id','address_id']:pred[col]=old[col].to_numpy()
    pred['public_full']=old.public_full.to_numpy()
    labels=pd.read_parquet(TARGET/'labels2024.parquet').set_index('row_id').y
    oldlabels=pd.read_parquet(OLD/'labels2024.parquet').set_index('row_id').y
    y=pred.row_id.map(labels).to_numpy();assert np.array_equal(y,pred.row_id.map(oldlabels).to_numpy())
    fp=ROOT/p.read(ROOT/'RUTAS_PROYECTO.json')['week_2_validation_partitions']
    fold=pd.read_parquet(fp,columns=['row_id','fold']).set_index('row_id')['fold'];pred['saved_fold']=pred.row_id.map(fold)
    oldrows=pd.read_parquet(ACTIVE/'predictions_T2b.parquet',columns=['row_id']).row_id
    fw=np.load(ACTIVE/'composition_bootstrap_T2b.npz')['weights']
    composition=pred.row_id.map(pd.Series(fw,index=oldrows)).to_numpy()
    specs=p.read(ACTIVE/'scenario_results.json')['scenarios'];assert len(specs)==50
    scenarios=[]
    for i,spec in enumerate(specs):
        ys=np.load(ACTIVE/'scenarios'/f'{i:02d}.npz')['y']
        scenarios.append((spec['scenario'],pred.row_id.map(pd.Series(ys,index=oldrows)).to_numpy()))
    return pred,y,composition,scenarios


def stability(frame,prices,y):
    saved=p.read(TARGET/'primary_parameters.json');params=saved['adapter'];cal=saved['calibrator']
    selected=model.LAMBDAS.index(cal['selection']['lambda'])
    original=inp.e.load_em();source=execution.StrictSource(original);held=original[original.year.eq(2024)]
    records=[];allpred=[];gates={c:True for c in COMP_NAMES};ms=masks(frame)
    def forbidden(*a,**kw):raise AssertionError('Evaluador invoco aprendizaje')
    with patch.object(model,'fit',forbidden),patch.object(inp.e,'kopt',forbidden),patch.object(inp.e,'learn_recipe',forbidden),patch.object(inp.a,'completion',forbidden),patch.object(inp.e.v,'factor_train',forbidden),patch.object(inp.f.lgb,'train',forbidden):
        for fold in range(5):
            key=inp.scope_name((fold,));tr=inp.train_frame(original,(fold,));src=source.get((fold,),tr)
            features=inp.apply_features(held,src,params['base'][key],params['recipes'][key]).sort_values('row_id').reset_index(drop=True)
            assert np.array_equal(frame.row_id,features.row_id)
            fitted=cal['members'][fold][selected]['model'];mu=p.forward(features,fitted);allpred.append(mu)
            local={'F3c_R':mu,'matched_trainlevel_full':features.matched_trainlevel_full.to_numpy(),'public_full':prices['public_full']}
            gg=np.stack([AUDIT.loss(y,local[b])-AUDIT.loss(y,local[a]) for a,b in COMPS],axis=1)
            deltas={n:dict(zip(COMP_NAMES,(gg[ms[n]].sum(axis=0)/AUDIT.null_loss(y[ms[n]])).tolist())) for n in BROAD}
            own_gates={c:deltas['global'][c]>=0 and deltas['new_business'][c]>=-.001 for c in COMP_NAMES}
            for c in gates:gates[c]&=own_gates[c]
            records.append({'excluded_fold':fold,'lambda':fitted['lambda'],'beta':fitted['beta'],'deltas':deltas,'stability_gates':own_gates})
    source.verify_consumed()
    values=np.stack(allpred);ratio=values/prices['F3c_R'][None,:]
    pd.DataFrame({'row_id':frame.row_id,**{f'exclude_{k}':values[k] for k in range(5)}}).to_parquet(OUT/'stability_predictions2024.parquet',index=False)
    return {'folds':records,'all_five_gates':gates,'relative_to_full_prediction_quantiles':np.quantile(ratio,[0,.01,.5,.99,1]).tolist(),
        'new_fits':0,'members_not_selectable':True,'source_manifests':source.manifests,'no_independent_private_guarantee':True}


def evaluate():
    guard();assert p.read(OUT/'synthetic.json')['all_passed'];assert not (OUT/'results.json').exists()
    status('EVALUATING_SEALED_TARGET')
    frame,y,composition,scenarios=load_target();prices={n:frame[n].to_numpy() for n in NAMES}
    groups=AUDIT.groups(frame);assert len(set(groups))==36408
    first=np.load(inp.f.BASE/'revision_chat_documento_20261027/first4_original_group_multiplicities.npy')
    result,draws,counts,stresses=calculate(frame,prices,y,groups,composition,scenarios,first_expected=first)
    np.savez_compressed(OUT/'bootstrap.npz',delta=draws,comparisons=COMP_NAMES,segments=BROAD+['mix2025_global','mix2025_new_business'])
    np.save(OUT/'first20_group_counts.npy',counts)
    stable=stability(frame,prices,y)
    for c in COMP_NAMES:result['gates'][c]['whole_pipeline_fivefold_stability']=stable['all_five_gates'][c]
    result.update(author='Codex',utc=p.utc(),all_gates_pass={c:all(g.values()) for c,g in result['gates'].items()},
        private_generalization_established=False,adaptive2024=True,new_fits=0,new_prices2025=0,new_submissions=0,
        target_seal_sha256=p.sha(TARGET/'artifact_seal.json'),plan_sha256=p.sha(PLAN))
    guard();p.dump(OUT/'fixed_price_stresses.json',stresses);p.dump(OUT/'whole_pipeline_stability.json',stable);p.dump(OUT/'results.json',result)
    status('EVALUATION_COMPLETE_DOCUMENTATION_PENDING',all_gates_pass=result['all_gates_pass'])
    document()


def document():
    guard();result=p.read(OUT/'results.json');stresses=p.read(OUT/'fixed_price_stresses.json');stable=p.read(OUT/'whole_pipeline_stability.json')
    if (OUT/'documentation.json').exists():
        status('COMPLETE',all_gates_pass=result['all_gates_pass'],report=str(DOC));return
    rows=[]
    for n in BROAD+CELLS:
        z=result['metrics'][n];rows.append('| '+n+' | '+' | '.join(f'{z["D2"][k]:.6f}' for k in NAMES)+' | '+' | '.join(f'{z["deltas"][c]:+.6f}' for c in COMP_NAMES)+' |')
    gate_lines=['| '+g+' | '+' | '.join('pasa' if result['gates'][c][g] else 'no pasa' for c in COMP_NAMES)+' |' for g in result['gates'][COMP_NAMES[0]]]
    passed=all(result['all_gates_pass'].values())
    conclusion='Cumple los criterios exploratorios registrados. Aun faltan decision de produccion, soporte futuro y reproduccion2025; no se ha enviado.' if passed else 'No cumple todos los criterios registrados. Se conserva F3c y no se prepara otro envio con esta evidencia.'
    text='# F3c-R frente al modelo actual\n\nAutor Codex. Corte '+result['utc']+'. '+conclusion+'\n\n'
    text+='Entrenamiento2023 con flujo anidado completo; evaluacion temporal2024 adaptativa. Los dos controles son trainlevel_full del mismo nuevo tronco y public_full de F3c original. Las cifras son locales, no calificaciones de Kaggle ni garantia privada.\n\n'
    text+='| Segmento | F3c-R D2 | Control mismo tronco | F3c original | Delta vs control | Delta vs F3c |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(rows)+'\n\n'
    text+='| Criterio | vs control mismo tronco | vs F3c original |\n|---|---|---|\n'+'\n'.join(gate_lines)+'\n\n'
    for c in COMP_NAMES:
        z=result['metrics']['global'];nb=result['metrics']['new_business'];inf=result['influence'][c]
        text+=f'{c}: intervalo global familiar20 {z["family20"][c]}, intervalo95 de negocio nuevo {nb["CI95"][c]}. Al retirar {inf["removed_favorable_groups"]} grupos favorables, delta {inf["delta_after_removal"]:+.6f}. Peor delta de los50escenarios en segmentos amplios: {stresses["worst_broad_delta"][c]:+.6f}. Estabilidad de las cinco omisiones de entrenamiento: {stable["all_five_gates"][c]}.\n\n'
    text+='Los10000sorteos por grupos mantienen precios fijos; no repiten todo el aprendizaje. Familia20 es condicional y no cubre toda la busqueda adaptativa. Cinco omisiones completas de folds comprueban otra sensibilidad del entrenamiento, sin escoger al mejor miembro. Los escenarios no tienen probabilidades asignadas ni certifican reservas.\n\n'
    text+='Permanecen la dependencia de normalizaciones por lote, la historia publica de A_M1 y el soporte escaso de edificios nuevos largos. La composicion2025 usa solo pesos ya archivados; no son etiquetas privadas. B00, R1, F3c y F3c-R quedan conservados, junto a fallos y parciales.\n\n'
    text+='Trazabilidad: registro/semana2_F3c_regularizado_evaluacion_plan.json y privado/semana2/F3c_regularizado_20261028/assessment/{results.json,bootstrap.npz,fixed_price_stresses.json,whole_pipeline_stability.json}. Codigo y fuentes identificados por SHA en el plan. No nuevos ajustes desde el evaluador, precios2025 ni envios.\n'
    if not DOC.exists():DOC.write_text(text,encoding='utf-8')
    else:assert DOC.read_text(encoding='utf-8')==text
    forum_path=OUT/'forum_receipt.json'
    forum=p.read(forum_path) if forum_path.exists() else p.io.post('Codex. Termine la comparacion preinscrita F3c-R. '+conclusion+' D2 global local: '+', '.join(k+'='+format(result['metrics']['global']['D2'][k],'.6f') for k in NAMES)+'. '
        'Criterios conjuntos: '+str(result['all_gates_pass'])+'. Se conservan ambos modelos, B00/R1 y todos los adversos. Revisión propia exploratoria;2024 adaptativo, sin superioridad privada acreditada. '
        'Informe '+w.rel(DOC)+'. Ningun envio nuevo.', 'COD-S2-20261028-F3CR-EVALUACION-RESULTADO','F3c-R: resultados frente a F3c y estabilidad para el privado')
    if not forum_path.exists():p.dump(forum_path,forum)
    receipt={'author':'Codex','utc':p.utc(),'status':'evaluated_preserve_F3c','report':w.rel(DOC),'report_sha256':p.sha(DOC),
        'result':w.rel(OUT/'results.json'),'result_sha256':p.sha(OUT/'results.json'),'all_gates_pass':result['all_gates_pass'],
        'formal_promotion':False,'private_superiority_established':False,'new_submissions':0,'forum':forum}
    archive=R/'privado'/('f3cr_evaluated_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    w.update(R/'registro/semana2_F3c_regularizado_actual.json',{'utc':p.utc(),'status':'evaluated_preserve_F3c','assessment':receipt,'next_unit':'Revisar resultados y adversos. No envio ni lista definitiva por score local; conservar F3c.'},archive)
    w.update(ROOT/'Preparación/ESTADO_PROYECTO.json',{'week_2_F3c_regularized_assessment_20261028':receipt},archive)
    note='\n\n## F3c-R: evaluacion completa del experimento20261028\n\nCodex. '+conclusion+' Criterios: '+str(result['all_gates_pass'])+'. Informe '+w.rel(DOC)+'. Sin envios.2024adaptativo; conservar B00/R1/F3c/F3c-R y adversos.\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    p.dump(OUT/'documentation.json',receipt);status('COMPLETE',all_gates_pass=result['all_gates_pass'],report=str(DOC))


def wait():
    guard();assert p.read(OUT/'synthetic.json')['all_passed']
    with (OUT/'lease.json').open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'utc':p.utc()},f)
    while True:
        target=p.read(TARGET/'status.json')
        if target['state'].startswith('STOPPED'):raise RuntimeError('Destino detenido; conciliar antes de evaluar')
        if target['state']=='TARGET_COMPLETE_EVALUATION_PENDING':break
        status('WAITING_TARGET',target_state=target['state']);time.sleep(30)
    document() if (OUT/'results.json').exists() else evaluate()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','synthetic','evaluate','document','wait','admit_fixture']);args=parser.parse_args()
    try:
        with threadpool_limits(limits=2):globals()[args.mode]()
    except Exception:
        if OUT.exists():
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
            (OUT/f'failure_{stamp}.txt').write_text(traceback.format_exc(),encoding='utf-8')
            status('STOPPED_REQUIRES_RECONCILIATION',error=traceback.format_exc())
        raise
