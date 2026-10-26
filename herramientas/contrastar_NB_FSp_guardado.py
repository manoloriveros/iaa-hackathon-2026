"""Aplicación NB sin aprender: prueba el núcleo congelado y la receta completa."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys
import subprocess

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; PARENT = BASE / 'FSp_REN_G3_prod_contraste_20261026_v1'
OUT = BASE / 'FSp_NB_aplicacion_20261026_v1'
PLAN = R / 'registro/semana2_mision017_FSp_NB_aplicacion_plan_v1.json'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


ENGINE = R / 'herramientas/contrastar_FSp_REN_contra_G3_v2.py'
engine = load('frozen_RFS_NB_math', ENGINE); w = engine.w; unit = engine.unit
WEIGHTS = {'motor': .25, 'buildings': .25, 'contents': .5}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    pre = w.read(PARENT / 'preflight.json'); oldplan = w.read(R / 'registro/semana2_mision017_FSp_REN_G3_prod_plan_v1.json')
    paths = [Path(__file__), ENGINE, PARENT / 'preflight.json', PARENT / 'report.json', PARENT / 'oof_2023_2024.parquet',
             PARENT / 'additional_veto_points.json', PARENT / 'A1_original2024_proxy_prices.parquet',
             BASE / 'estimando_cartera2025_v3/weights.parquet']
    for scope in pre['scopes']:
        path = ROOT / scope['input']; assert w.sha(path) == scope['sha256']; paths.append(path)
        path = PARENT / f'learning_{scope["line"]}_fold{scope["held"]}.json'; paths.append(path)
        a = w.read(path); f = pd.read_parquet(ROOT / scope['input'], columns=['row_id','group_id','fold','new_business','year'])
        train = f.fold.ne(scope['held'])
        assert sorted(f.loc[train,'row_id']) == a['training_row_ids']
        assert not set(f.loc[~train,'group_id']).intersection(a['training_groups'])
        assert all((f.loc[~train].year.eq(year) & f.loc[~train].new_business.eq(1)).any() for year in [2023,2024])
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'hypothesis': 'Test the isolated NB effect of the reconstructed group-safe production-aligned FSp core before adding models or variables. Received NB losses arose under a different compound recipe/scope and do not measure this frozen stage.',
        'primary': 'Fixed full REN+NB recipe versus G3; NB-only decomposition versus G3 and incremental full-versus-REN are explicit.',
        'configuration': {'weights': WEIGHTS, 'KP': 100, 'source': 'saved prod2021–2024', 'years': [2023,2024],
                          'G3': 'unchanged saved reference', 'groups': 'saved global customer/address components',
                          'C0_and_kappa': 'already learned excluding held group; exact artifacts reused, no reestimation',
                          'new_application': 'Same risk/ratio equation, select NB instead of REN; prediction-only normalization by line/year/NB.',
                          'combined': 'Copy saved RFS1P on REN; replace only NB with new application. No selection or weights learned from either score.'},
        'criterion': oldplan['criterion'],
        'NB_addition_guard': {'point_nonnegative': True, 'both_years_nonnegative': True, 'positive_folds_min': 4,
                              'lower95_positive': True, 'no_cell_worse_than_minus001': True},
        'not_a_formal_promotion_from_surrogate': True,
        'bootstrap': {'replicates': 2000, 'seed': 2026102614, 'unit': 'saved component',
                      'null_recomputed_per_resample': True, 'conditional_on_frozen_source_and_calibration': True,
                      'only_new_NB_and_full_comparisons': True},
        'additional_veto': 'Cached2025weights sensitivity point and original A1 proxy; prior ESS failure remains. No domain-classifier refit/bootstrap.',
        'control': 'No learning permitted. Held T0/counts/reserves poisoning; exact copied REN; swapped population equivalent to frozen REN application; independent log-space formula; zero weight identity.',
        'budget': {'new_model_fits': 0, 'new_C0_fits': 0, 'new_calibration_constants': 0, 'new_source_inferences': 0,
                   'new_OOF_NB_price_rows': 15037, 'NB_prediction_only_normalizers': 30, 'A1_proxy_NB_normalizers': 15,
                   'new_test_prices': 0, 'new_submissions': 0},
        'B00_all_alternatives_preserved': True, '2024_open': True,
        'sources': {w.rel(path): w.sha(path) for path in paths}}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Registro antes de puntuar la primera aplicación NB aislada del núcleo FSp reconstruido y protegido por grupos. '
        'Se mantienen productor prod2021–2024, G3, kappa/C0, KP100 y pesos .25/.25/.5. Ningún parámetro se estima otra vez. '
        'Se cambia solo la población de aplicación y se conservan los totales por año/ramo/negocio mediante predicciones. '
        'La receta completa suma el bloque NB nuevo a las REN ya guardadas de RFS1P; también se mide NB separado para no ocultar deterioros. '
        'Los criterios globales permanecen. La incorporación NB necesita además señal no negativa en ambos años, cuatro folds positivos e intervalo positivo. '
        'El rechazo NB recibido corresponde a otra receta/ámbito; no se repite esa prueba ni se retocan pesos por sus resultados. '
        'Se usan solo las 15.037filas NB históricas para la nueva aplicación. Cero modelos, C0, constantes, inferencias de fuente, precios de2025 o envíos. '
        'La evaluación sigue siendo exploratoria y el comparador completo F3c falta. B00 y todas las alternativas se conservan,2024abierto. '
        'Plan: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-NB-APLICACION-PREVIO',
        '--asunto', 'FSp en nuevo negocio: contraste aislado sin nuevos ajustes', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'new_models': 0, 'new_calibrations': 0, 'forum': json.loads(response.stdout)}))


def apply_NB(f, perils, a, line, weight=None):
    risk = sum(a['perils'][p]['kappa'] * f['f_'+p].to_numpy() * f['s_'+p].to_numpy() * f['q_'+p].to_numpy() for p in perils)
    base = f.baseline_G3.to_numpy(float); result = base.copy(); norms = {}
    weight = WEIGHTS[line] if weight is None else weight
    for year in sorted(f.year.unique()):
        mask = f.year.eq(year).to_numpy() & f.new_business.eq(1).to_numpy(); assert mask.any()
        factor = (risk[mask] / f.unshaped_T2b.to_numpy()[mask]) ** weight
        assert np.isfinite(factor).all() and (factor > 0).all()
        norm = float(np.dot(base[mask],factor) / base[mask].sum())
        result[mask] = base[mask] * factor / norm; norms[str(year)] = norm
        assert abs(result[mask].sum()/base[mask].sum()-1) < 1e-12
    assert np.array_equal(result[f.new_business.eq(0)],base[f.new_business.eq(0)])
    return result,norms


def metrics(p, plan):
    y=p.T0.to_numpy(float); base=p.G3.to_numpy(float); den=unit(y,np.full(len(y),y.mean())).sum()
    gains={name:unit(y,base)-unit(y,p[name].to_numpy(float)) for name in ['RFS_NB','RFS_ALL']}
    prior=unit(y,base)-unit(y,p.RFS_REN.to_numpy(float))
    assert np.array_equal(gains['RFS_ALL'],gains['RFS_NB']+prior)
    scores={name:float(1-unit(y,p[name].to_numpy(float)).sum()/den) for name in ['G3','RFS_REN','RFS_NB','RFS_ALL']}
    for name in scores:
        assert abs(unit(y,p[name].to_numpy()).mean()-mean_tweedie_deviance(y,p[name],power=1.5))<1e-10
    group=pd.DataFrame({'group':p.group_id,'N':1.,'Y':y,'sqrtY':np.sqrt(y),**gains}).groupby('group').sum()
    rng=np.random.default_rng(plan['bootstrap']['seed']);boot=[]
    stats=group[['N','Y','sqrtY','RFS_NB','RFS_ALL']].to_numpy()
    for _ in range(2000):
        ix=rng.integers(0,len(group),len(group));s=stats[ix].sum(axis=0)
        d=8*(np.sqrt(s[0]*s[1])-s[2]);assert d>0;boot.append(s[3:]/d)
    boot=np.array(boot);result={}
    topcost=set(p.groupby('group_id').T0.sum().nlargest(31).index)
    for j,name in enumerate(['RFS_NB','RFS_ALL']):
        gain=gains[name];folds={str(k):float(gain[p.fold.eq(k)].sum()/den) for k in range(5)}
        years={str(k):float(gain[p.year.eq(k)].sum()/den) for k in [2023,2024]}
        cells=[]
        for (line,year,nb),ix in p.groupby(['line','year','new_business']).groups.items():
            ix=np.asarray(list(ix));yy=y[ix];dd=unit(yy,np.full(len(yy),yy.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(nb),'rows':len(ix),
                          'delta_global':float(gain[ix].sum()/den),'delta_cell_null':float(gain[ix].sum()/dd)})
        sortedgain=group[name].sort_values(ascending=False)
        post31=float((group[name].sum()-sortedgain.iloc[:31].sum())/den)
        delta=float(gain.sum()/den);ci=np.quantile(boot[:,j],[.025,.975]).tolist()
        gates={'delta_min':delta>=plan['criterion']['delta_min'],'lower95_positive':ci[0]>0,
               'at_least4positive_folds':sum(x>0 for x in folds.values())>=4,
               'both_years_nonnegative':all(x>=0 for x in years.values()),'post31_nonnegative':post31>=0,
               'cell_min':min(x['delta_cell_null'] for x in cells)>=-.001}
        result[name]={'delta':delta,'bootstrap95':ci,'folds':folds,'years':years,'cells':cells,
                      'post31':post31,'remove31highest_cost_groups_delta':float(gain[~p.group_id.isin(topcost)].sum()/den),'gates':gates}
    group.to_parquet(OUT/'group_influence.parquet');np.save(OUT/'bootstrap_new_NB_and_full.npy',boot)
    return scores,result


def additional_veto(p, proxy):
    weightpath=BASE/'estimando_cartera2025_v3/weights.parquet'
    weight=pd.read_parquet(weightpath,columns=['row_id','weight']).set_index('row_id').loc[p.row_id,'weight'].to_numpy()
    y=p.T0.to_numpy();den=8*(np.sqrt(np.dot(weight,y)*weight.sum())-np.dot(weight,np.sqrt(y)))
    wdelta={name:float(np.dot(weight,unit(y,p.G3.to_numpy())-unit(y,p[name].to_numpy()))/den) for name in ['RFS_NB','RFS_ALL']}
    q=p.loc[p.year.eq(2024)].merge(proxy,on='row_id',validate='one_to_one')
    wq=pd.read_parquet(weightpath,columns=['row_id','weight']).set_index('row_id').loc[q.row_id,'weight'].to_numpy()
    yy=q.T0.to_numpy();dd=8*(np.sqrt(np.dot(wq,yy)*wq.sum())-np.dot(wq,np.sqrt(yy)))
    adelta={name:float(np.dot(wq,unit(yy,q.A1.to_numpy())-unit(yy,q[name].to_numpy()))/dd) for name in ['A1_G3_NB','A1_G3_ALL']}
    for name in adelta:
        assert abs(np.average(unit(yy,q[name]),weights=wq)-mean_tweedie_deviance(yy,q[name],power=1.5,sample_weight=wq))<1e-7
    return {'weighted2025_deltas_vs_G3':wdelta,'original_A1_2024_weighted_deltas':adelta,
            'weighted_primary_ESS_still_failed':True,'original_A1_not_corrected_or_complete_F3c':True,'new_bootstrap_or_classifiers':0}


def run():
    assert not (OUT/'started.json').exists()
    assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    plan=w.read(PLAN);assert all(w.sha(ROOT/path)==sha for path,sha in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':w.sha(PLAN)})
    pre=w.read(PARENT/'preflight.json');p=pd.read_parquet(PARENT/'oof_2023_2024.parquet')
    p=p.rename(columns={'RFS1':'RFS_REN'});p['RFS_NB']=p.G3;p['RFS_ALL']=p.RFS_REN
    proxy=pd.read_parquet(PARENT/'A1_original2024_proxy_prices.parquet')
    proxy['A1_G3_NB']=proxy.A1_G3;proxy['A1_G3_ALL']=proxy.A1_G3_RFS1P
    meta=p[['row_id','line','year','fold','new_business']].set_index('row_id');proxy=proxy.join(meta,on='row_id',validate='one_to_one')
    controls=[];NBrows=0
    def reject(*a,**k):raise AssertionError('No estimator permitted in saved NB application')
    engine.learn=reject
    for scope in pre['scopes']:
        line,held=scope['line'],scope['held'];f=pd.read_parquet(ROOT/scope['input'])
        valid=f.loc[f.fold.eq(held)].copy();a=w.read(PARENT/f'learning_{line}_fold{held}.json');perils=pre['perils'][line]
        assert not set(valid.group_id).intersection(a['training_groups'])
        pred,norms=apply_NB(valid,perils,a,line)
        bad=valid.copy();bad[['T0','reserve',*['y_'+q for q in perils],*['n_'+q for q in perils]]]=-1_000_000_000
        poison,nn=apply_NB(bad,perils,a,line);assert np.array_equal(poison,pred) and nn==norms
        swapped=valid.copy();swapped['new_business']=1-swapped.new_business.astype(int)
        independent,ni=engine.apply(swapped,perils,a,line);assert np.array_equal(independent,pred) and ni==norms
        identity,_=apply_NB(valid,perils,a,line,weight=0.);assert np.array_equal(identity,valid.baseline_G3)
        outside=valid.copy();outside.loc[outside.new_business.eq(0),['f_'+q for q in perils]]=1e20
        assert np.array_equal(apply_NB(outside,perils,a,line)[0],pred)
        for year in [2023,2024]:
            mask=valid.year.eq(year).to_numpy()&valid.new_business.eq(1).to_numpy()
            risk=np.column_stack([valid['f_'+q].to_numpy()*valid['s_'+q].to_numpy()*valid['q_'+q].to_numpy() for q in perils])@np.array([a['perils'][q]['kappa'] for q in perils])
            z=np.exp(np.log(valid.baseline_G3.to_numpy()[mask])+WEIGHTS[line]*(np.log(risk[mask])-np.log(valid.unshaped_T2b.to_numpy()[mask])))
            z*=valid.baseline_G3.to_numpy()[mask].sum()/z.sum();assert np.allclose(z,pred[mask],rtol=1e-12,atol=1e-10)
        indices=pd.Series(p.index.to_numpy(),index=p.row_id).loc[valid.row_id].to_numpy()
        p.loc[indices,'RFS_NB']=pred
        nb=valid.new_business.eq(1).to_numpy();NBrows+=int(nb.sum());p.loc[indices[nb],'RFS_ALL']=pred[nb]
        # A1 proxy addition: saved REN result reused; only NB application is new.
        qi=proxy.index[proxy.line.eq(line)&proxy.fold.eq(held)]
        q=valid.set_index('row_id').loc[proxy.loc[qi,'row_id']].reset_index()
        q['baseline_G3']=proxy.loc[qi,'A1_G3'].to_numpy()
        value,_=apply_NB(q,perils,a,line);proxy.loc[qi,'A1_G3_NB']=value
        qnb=q.new_business.eq(1).to_numpy();proxy.loc[np.asarray(qi)[qnb],'A1_G3_ALL']=value[qnb]
        dump(OUT/f'application_{line}_fold{held}.json',{'line':line,'fold':held,'normalizers':norms,'new_estimates':0,'kappa_source_sha256':w.sha(PARENT/f'learning_{line}_fold{held}.json')})
        controls.append({'line':line,'fold':held,'held_payload_ignored':True,'population_swap_to_frozen_engine_exact':True,
                         'outside_REN_values_ignored':True,'zero_weight_identity_exact':True,'independent_log_math':True})
    assert NBrows==15037 and np.array_equal(p.loc[p.new_business.eq(0),'RFS_ALL'],p.loc[p.new_business.eq(0),'RFS_REN'])
    scores,comparisons=metrics(p,plan);vetos=additional_veto(p,proxy)
    nb=comparisons['RFS_NB'];guards={'point_nonnegative':nb['delta']>=0,'both_years_nonnegative':all(x>=0 for x in nb['years'].values()),
        'four_folds_positive':sum(x>0 for x in nb['folds'].values())>=4,'lower95_positive':nb['bootstrap95'][0]>0,
        'cell_min':min(x['delta_cell_null'] for x in nb['cells'])>=-.001}
    p.to_parquet(OUT/'oof_2023_2024.parquet',index=False);proxy.to_parquet(OUT/'A1_original2024_proxy_prices.parquet',index=False)
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scores':scores,'comparisons':comparisons,
        'NB_addition_guard':guards,'all_NB_guards_pass':all(guards.values()),'additional_vetoes':vetos,
        'all_full_recipe_primary_gates_pass':all(comparisons['RFS_ALL']['gates'].values()),
        'full_F3c_comparator_missing':True,'formal_admission':False,'controls':controls,'new_OOF_NB_rows':NBrows,
        'new_model_fits':0,'new_C0_fits':0,'new_calibration_constants':0,'new_source_inferences':0,
        'new_prediction_only_normalizers':45,'new_test_prices':0,'new_submissions':0,'2024_open':True,
        'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    assert all(w.sha(ROOT/path)==sha for path,sha in plan['sources'].items())
    dump(OUT/'report.json',report)
    print(json.dumps({'scores':scores,'NB_delta':nb['delta'],'NB_bootstrap95':nb['bootstrap95'],'NB_guards':guards,
        'full_delta':comparisons['RFS_ALL']['delta'],'full_gates':comparisons['RFS_ALL']['gates'],'vetoes':vetos,
        'new_models':0,'new_C0':0,'new_submissions':0}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run'])
    a=parser.parse_args();register() if a.mode=='register' else run()
