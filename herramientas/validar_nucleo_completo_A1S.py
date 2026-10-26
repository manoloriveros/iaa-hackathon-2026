"""Comparación nueva del núcleo completo, C0 guardado y calibración por ámbito."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
HOME = BASE/'A1S_nucleo_20261026_v1'
SOURCE = HOME/'source_models'
OUT = HOME/'target_complete_core'
PLAN = R/'registro/semana2_mision017_A1S_completo_plan_v1.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


w = load('complete_A1S_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
b = load('complete_A1S_closed_calibration', R/'herramientas/mision017_fase2_tanda2.py')
g = load('complete_A1S_residual_engine', R/'herramientas/mision017_fase2_tanda10_factores.py')
LINES = ['motor', 'buildings', 'contents']
NAMES = ['S0', 'S1', 'S2']


def dump(p, value):
    assert not p.exists(), 'Preserve existing artifact: '+str(p)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def fit_component(train, line):
    # This function receives only the outer training rows.
    assert train.T0.ge(0).all() and train.e_cost_scope.gt(0).all()
    value = np.exp(train.log_relative_A1S.to_numpy(float))*train.e_cost_scope.to_numpy(float)
    shapes = []
    for variable in (['ncb', 'prior'] if line == 'motor' else ['prior']):
        artifact, value = b.shape_fit(train, value, variable)
        shapes.append(artifact)
    k = b.factor(train.T0.to_numpy(float), value)
    cell = b.cell_levels(train, value, k)
    return {'line': line, 'shape': shapes, 'level': k, 'cell_level': cell,
            'fit_row_ids_digest': b.digest(sorted(train.row_id)),
            'fit_groups_digest': b.digest(sorted(set(train.group_id))),
            'shape_factor_constants': sum(len(a['factors']) for a in shapes),
            'shape_training_normalizers': sum(len(a['normalizers']) for a in shapes),
            'level_constants': 3}


def apply_component(f, artifact):
    value = np.exp(f.log_relative_A1S.to_numpy(float))*f.e_cost_scope.to_numpy(float)
    for shape in artifact['shape']:
        value = b.shape_apply(f, value, shape)
    return value*np.array([artifact['cell_level'][str(int(nb))] for nb in f.new_business])


def learn(f, held, line):
    mask = f.fold.ne(held).to_numpy()
    train = f.loc[mask].copy(); valid = f.loc[~mask].copy()
    assert not set(train.group_id).intersection(valid.group_id)
    component = fit_component(train, line)
    a_train = apply_component(train, component)
    a_valid = apply_component(valid, component)
    mix_train = .5*a_train + .5*train.base_N3.to_numpy(float)
    mix_valid = .5*a_valid + .5*valid.base_N3.to_numpy(float)
    stages = []; training_norms = {}; held_norms = {}
    residual_train = mix_train.copy(); residual_valid = mix_valid.copy()
    for variable in g.STAGES[line]:
        stage = g.fit_stage(train, residual_train, variable)
        residual_train, nt = g.apply_stage(train, residual_train, stage)
        residual_valid, nv = g.apply_stage(valid, residual_valid, stage)
        stages.append(stage); training_norms[variable] = nt; held_norms[variable] = nv
    artifact = {'line': line, 'held_fold': held, 'component': component,
                'stages': stages, 'training_normalizers': training_norms,
                'held_normalizers': held_norms,
                'fit_row_ids_digest': b.digest(sorted(train.row_id)),
                'fit_groups_digest': b.digest(sorted(set(train.group_id)))}
    return {'S0': a_valid, 'S1': mix_valid, 'S2': residual_valid}, artifact


def replay(valid, artifact):
    a = apply_component(valid, artifact['component'])
    mixture = .5*a + .5*valid.base_N3.to_numpy(float)
    result = mixture.copy(); norms = {}
    for stage in artifact['stages']:
        result, norm = g.apply_stage(valid, result, stage)
        norms[stage['variable']] = norm
    return {'S0': a, 'S1': mixture, 'S2': result}, norms


def scalar_controls():
    rng = np.random.default_rng(2026102610)
    n = 1600
    f = pd.DataFrame({'row_id': ['fake'+str(i) for i in range(n)],
        'group_id': ['group'+str(i) for i in range(n)], 'fold': np.arange(n)%5,
        'year': 2023+(np.arange(n)//5)%2, 'new_business': (np.arange(n)//10)%2,
        'T0': rng.gamma(2,100,n)*(rng.random(n)<.3), 'e_cost_scope': rng.uniform(.2,1,n),
        'log_relative_A1S': rng.normal(0,.4,n), 'base_N3': rng.uniform(30,150,n),
        'ncb_years': rng.integers(0,15,n), 'prior_claims_5y': rng.integers(0,3,n),
        'gender': rng.choice(['F','M'],n), 'works_from_home': rng.integers(0,2,n),
        'marketing_segment': rng.choice(['a','b','c'],n)})
    checks = []
    for line in LINES:
        pred, artifact = learn(f, 0, line)
        bad = f.copy(); bad.loc[bad.fold.eq(0), 'T0'] = -1e30
        poisoned, other = learn(bad, 0, line)
        assert b.digest(artifact) == b.digest(other)
        assert all(np.array_equal(pred[k], poisoned[k]) for k in NAMES)
        changed = f.copy(); changed.loc[changed.fold.ne(0), 'T0'] *= 2
        _, different = learn(changed,0,line)
        assert b.digest(different) != b.digest(artifact)
        valid = f.loc[f.fold.eq(0)]
        reproduced, norms = replay(valid, artifact)
        assert all(np.array_equal(pred[k], reproduced[k]) for k in NAMES)
        assert norms == artifact['held_normalizers']
        checks.append({'line': line, 'full_learning_held_response_invariant': True,
                       'training_response_changes_learning': True, 'saved_replay_exact': True})
    return {'checks': checks, 'synthetic_iterative_model_fits': 0,
            'synthetic_closed_component_calibrations': 9,
            'synthetic_residual_stage_calls': 12}


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert w.read(SOURCE/'report.json')['new_source_model_fits'] == 18
    OUT.mkdir()
    source_paths = [Path(__file__), Path(b.__file__), Path(g.__file__),
        SOURCE/'report.json', HOME/'report.json',
        BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet',
        R/'registro/semana2_politica_desarrollo2024_v2.json']
    original = pd.read_parquet(BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet').set_index('row_id')
    scopes = []
    for line in LINES:
        path = SOURCE/f'target_{line}_three_seed_components.parquet'
        source_paths.append(path)
        rel = pd.read_parquet(path).set_index('row_id')
        rp = HOME/f'rows_s2_{line}.parquet'; xp = HOME/f'matrix_s2_{line}.parquet'
        source_paths += [rp, xp]
        rowid = pd.read_parquet(rp, columns=['row_id'])
        feature_cols = ['prior_claims_5y'] + (['ncb_years'] if line == 'motor' else [])
        cov = pd.read_parquet(xp, columns=feature_cols)
        assert len(cov) == len(rowid)
        cov['row_id'] = rowid.row_id.to_numpy(); cov = cov.set_index('row_id')
        extra = None
        if line != 'buildings':
            cp = BASE/f'tanda10_factores_20261026_v1/covariates_{line}.parquet'
            source_paths.append(cp); extra = pd.read_parquet(cp).set_index('row_id')
        for held in range(5):
            inp = BASE/f'tanda6_pendiente_20261025_v1/inputs_{line}_fold{held}.parquet'
            parent = BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json'
            source_paths += [inp,parent]
            f = pd.read_parquet(inp)
            assert f.row_id.is_unique and f.year.isin([2023,2024]).all()
            for col in feature_cols:
                f[col] = cov.loc[f.row_id,col].to_numpy()
            if extra is not None:
                for col in ['gender','works_from_home','marketing_segment']:
                    f[col] = extra.loc[f.row_id,col].to_numpy()
            f['log_relative_A1S'] = rel.loc[f.row_id,'log_relative_A1S'].to_numpy()
            training = f.fold.ne(held)
            c0 = w.read(parent)['artifact']['C0']
            assert c0['excluded_fold'] == held
            assert sorted(f.loc[training,'row_id']) == c0['fit_row_ids']
            assert not set(f.loc[training,'group_id']).intersection(f.loc[~training,'group_id'])
            held_ref = original.loc[f.loc[~training,'row_id']]
            assert np.array_equal(held_ref.N3,f.loc[~training,'base_N3'])
            for col in ['T0','fold','group_id','year','new_business']:
                assert np.array_equal(held_ref[col],f.loc[~training,col])
            path = OUT/f'inputs_{line}_fold{held}.parquet'
            f.to_parquet(path,index=False)
            scopes.append({'line': line, 'held': held, 'input': w.rel(path), 'sha256': w.sha(path),
                           'C0_parent': w.rel(parent), 'C0_parent_sha256': w.sha(parent),
                           'training_rows': int(training.sum()), 'held_rows': int((~training).sum()),
                           'C0_membership_exact': True})
    dump(OUT/'synthetic.json',scalar_controls())
    dump(OUT/'preflight.json', {'utc': datetime.now(timezone.utc).isoformat(), 'author': 'Codex',
        'sources': {w.rel(p):w.sha(p) for p in source_paths}, 'scopes': scopes,
        'new_contest_calibrations': 0, 'new_contest_scores': 0, 'new_source_fits': 0, 'new_C0_fits': 0})
    print(json.dumps({'preflight': 'passed', 'scopes': len(scopes), 'contest_learning': 0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre = w.read(OUT/'preflight.json')
    paths = dict(pre['sources'])
    paths.update({a['input']:a['sha256'] for a in pre['scopes']})
    paths[w.rel(OUT/'preflight.json')] = w.sha(OUT/'preflight.json')
    paths[w.rel(OUT/'synthetic.json')] = w.sha(OUT/'synthetic.json')
    assert all(w.sha(ROOT/p)==v for p,v in paths.items())
    plan = {'author': 'Codex','utc': datetime.now(timezone.utc).isoformat(),
        'hypothesis': 'A full source-safe A1-family core, calibrated independently inside every emerging scope and averaged with T2b, may supply information absent from the T2b-only G3 surrogate.',
        'candidate_primary': 'S2, fixed in advance; S0 and S1 are declared ablations, not competing winners selected by retained scores.',
        'models': {'S0':'A1S three-seed geometric-mean relative risk, existing source-only model outputs; emerging NCB/prior shape and business-level credibility rule.',
                   'S1':'.5*S0+.5*saved scope N3 T2b prices, arithmetic fixed mixture, no learned mixture weight.',
                   'S2':'S1 plus existing G3-family sequential residual stages: motor gender; contents gender, telework, marketing; buildings none.'},
        'shape': {'variables':{'motor':['ncb','prior'],'buildings':['prior'],'contents':['prior']},
                  'factor':'Existing n_positive/(n_positive+300) arithmetic A/E-shape correction within business; training normalizers only.',
                  'levels':'One Tweedie1.5 line optimum, two business optima shrunk with n_positive/(n_positive+400), all training only.'},
        'residual': {'code':w.rel(Path(g.__file__)),'K':300,'nuisance':'Training-only year/business levels, not transferred.',
                     'normalization':'Prediction-only year/business totals on each application; no retained labels.'},
        'target':'Emerging2023+2024, same109296rows, saved five global customer/address component folds.2024explicitly open adaptive development.',
        'C0':'Reuse exactly the saved outer-scope C0/e_cost and existing N3. No curve, mixture or frequency estimation and no historical producer invocation.',
        'reference':'G3 saved OOF, with N3 additionally retained. G3 is not full delivered F3c. Historical corrected A1 unavailable; no claim of direct replay/comparison against full F3c.',
        'criterion':{'delta_min':.002,'lower95_gt':0,'positive_folds_min':4,'both_years_nonnegative':True,
                     'post31_favorable_groups_delta_min':0,'min_line_year_business_cell_delta_null':-.001},
        'bootstrap':{'replicates':2000,'seed':2026102611,'unit':'saved global connected component','single_primary_comparison':'S2 vs G3'},
        'level_sensitivity':[.95,1.,1.05],
        'weighted_sensitivity':'Reuse existing2025importance weights, no classifier/refit/resampling. Failed ESS remains a limitation; weighted score is not reliable independent confirmation.',
        'budget':{'new_iterative_model_fits':0,'new_source_inference':0,'new_C0_fits':0,
                  'component_shape_calibrations':20,'component_levels':45,
                  'residual_stage_calls':20,'residual_factors_max':90,'residual_nuisance_levels':80,
                  'target_outer_scope_learning_calls':15,'final_test_prices':0,'new_submissions':0},
        'controls':['Full estimator held-out T0/reserve poisoning must preserve every learned artifact and prediction in all15scopes',
                    'Replay with all learning functions blocked; exact predictions and normalizers',
                    'Scope row/group identity matches frozen C0 ancestors',
                    'Independent scalar moment/derivative, Tweedie metric and exposure arithmetic',
                    'Report all declared ablations, cells/folds/years, influence and level sensitivity; no case removal or gate relaxation'],
        'admission':'Exploratory gates only; no formal promotion or automatic submission. Prepare a concrete delivery separately only if justified, preserving the actual F3c0.16914 benchmark and quota.',
        'limits':['Adaptive search; not independent professional confirmation','Undated masters and snapshot/reporting-tail/reserve assumptions persist',
                  'Source2024fullsnapshot is available for2025production; historic evaluation is conditional development, not inception-time forecasting',
                  'No complete historic F3c numerical comparator; do not extrapolate this G3 gain to leaderboard'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'sources':paths}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Antes de calibrar o puntuar registro el contraste del núcleo A1S completo. '
        'S0 será A1S con las correcciones estándar NCB/previos y nivel por negocio; S1, mezcla aritmética fija 50/50 con N3/T2b; S2, esa mezcla más los factores residuales ya definidos. '
        'S2 es el candidato primario; S0/S1 son ablaciones, sin elegir ganador después de ver resultados. '
        'Se usan los 109.296 registros de 2023–2024 y sus cinco folds por componentes, con C0 exterior ya guardado. No se ajustan árboles ni curvas. '
        'Todos los nuevos factores/niveles excluyen el grupo retenido; se probará el estimador completo con respuestas retenidas alteradas y replay sin aprendizaje. '
        'Se conservan los umbrales previos de ganancia, incertidumbre, estabilidad y concentración, además de sensibilidad de nivel y cartera. '
        'G3 es el comparador local disponible, distinto de F3c completo: no se trasladará su ganancia directamente al público. '
        'B00, F3c (0,16914) y alternativas intactos; 2024 abierto y adaptativo. Sin precios de 2025 o envíos. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-A1S-COMPLETO-PREVIO','--asunto','Núcleo completo A1S: mezcla fija y calibración por grupos',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':w.sha(PLAN),'forum':json.loads(result.stdout)})
    print(json.dumps({'registered':True,'forum':json.loads(result.stdout)}))


def statistics(p, plan):
    y=p.T0.to_numpy(float); reference=p.G3.to_numpy(float)
    den=b.unit(y,np.full(len(y),y.mean())).sum()
    gains=np.column_stack([b.unit(y,reference)-b.unit(y,p[n].to_numpy(float)) for n in NAMES])
    primary=gains[:,2]
    for name in ['N3','G3']+NAMES:
        assert abs(b.unit(y,p[name].to_numpy(float)).mean()-mean_tweedie_deviance(y,p[name],power=1.5))<1e-9
    group=pd.DataFrame({'group_id':p.group_id,'gain':primary,'N':1.,'Y':y,'sqrtY':np.sqrt(y)}).groupby('group_id',sort=True).sum()
    assert abs((8*np.sqrt(group.N.sum()*group.Y.sum())-8*group.sqrtY.sum())/den-1)<1e-12
    rng=np.random.default_rng(plan['bootstrap']['seed']); values=group.to_numpy(); boot=[]
    for _ in range(plan['bootstrap']['replicates']):
        indices=rng.integers(0,len(group),len(group)); v=values[indices].sum(axis=0)
        boot.append(float(v[0]/(8*np.sqrt(v[1]*v[2])-8*v[3])))
    ci=np.quantile(boot,[.025,.975]).tolist()
    delta=float(primary.sum()/den)
    folds={str(k):float(primary[p.fold.eq(k)].sum()/den) for k in range(5)}
    years={str(k):float(primary[p.year.eq(k)].sum()/den) for k in [2023,2024]}
    cells=[]
    for (line,year,nb),ix in p.groupby(['line','year','new_business']).groups.items():
        ii=np.asarray(list(ix)); yy=y[ii]; dd=b.unit(yy,np.full(len(yy),yy.mean())).sum()
        cells.append({'line':line,'year':int(year),'new_business':int(nb),'rows':len(ii),
                      'positive':int(np.count_nonzero(yy>0)),'delta_global':float(primary[ii].sum()/den),
                      'delta_cell_null':float(primary[ii].sum()/dd),
                      'AE_G3':float(yy.sum()/reference[ii].sum()),'AE_S2':float(yy.sum()/p.S2.to_numpy()[ii].sum())})
    influence=group.sort_values('gain',ascending=False)
    post31=float((group.gain.sum()-influence.gain.iloc[:31].sum())/den)
    gates={'delta_ge_002':delta>=.002,'lower95_positive':ci[0]>0,
           'positive_folds_ge4':sum(v>0 for v in folds.values())>=4,
           'both_years_nonnegative':min(years.values())>=0,'post31_nonnegative':post31>=0,
           'cell_min_ge_minus001':min(x['delta_cell_null'] for x in cells)>=-.001}
    weight_path=BASE/'estimando_cartera2025_v3/weights.parquet'
    weights=pd.read_parquet(weight_path,columns=['row_id','weight']).set_index('row_id').loc[p.row_id,'weight'].to_numpy(float)
    nullmean=np.average(y,weights=weights)
    weighted=float(np.sum(weights*primary)/np.sum(weights*b.unit(y,np.full(len(y),nullmean))))
    levels={str(k):{n:float(1-b.unit(y,p[n].to_numpy(float)*k).sum()/den) for n in ['G3','S2']} for k in plan['level_sensitivity']}
    np.save(OUT/'primary_bootstrap_deltas.npy',np.array(boot))
    influence.to_parquet(OUT/'group_influence.parquet')
    return {'scores':{n:float(1-b.unit(y,p[n].to_numpy(float)).sum()/den) for n in ['N3','G3']+NAMES},
            'primary_delta_vs_G3':delta,'primary_bootstrap95':ci,'fold_contributions':folds,
            'year_contributions':years,'cells':cells,'post31_delta':post31,'gates':gates,
            'exploratory_gates_pass':all(gates.values()),'weighted2025_sensitivity_delta':weighted,
            'weighted_ESS_already_failed_not_independent_confirmation':True,
            'level_sensitivity':levels,'formal_admission':False,'submission_allowed':False,
            'full_delivered_F3c_comparator_reproduced':False,
            'declared_ablations_delta_vs_G3':{n:float(gains[:,j].sum()/den) for j,n in enumerate(NAMES)}}


def run():
    assert not (OUT/'report.json').exists() and not (OUT/'started.json').exists()
    plan=w.read(PLAN); assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    import os
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    oof=pd.read_parquet(BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet')
    for name in NAMES:oof[name]=np.nan
    rowindex=pd.Series(oof.index.to_numpy(),index=oof.row_id)
    checks=[];constants={'shape_factors':0,'shape_training_normalizers':0,'component_levels':0,'residual_factors':0,'residual_nuisance_levels':0}
    with threadpool_limits(limits=2):
        for line in LINES:
            for held in range(5):
                f=pd.read_parquet(OUT/f'inputs_{line}_fold{held}.parquet')
                valid=f.loc[f.fold.eq(held)].copy()
                predicted,artifact=learn(f,held,line)
                dump(OUT/f'learning_{line}_fold{held}.json',artifact)
                # Check the complete entry point, not just isolated factor functions.
                poisoned=f.copy(); poisoned.loc[poisoned.fold.eq(held),'T0']=-1e30
                poisoned.loc[poisoned.fold.eq(held),'reserve']=-1e30
                other,unchanged=learn(poisoned,held,line)
                assert b.digest(artifact)==b.digest(unchanged)
                assert all(np.array_equal(predicted[n],other[n]) for n in NAMES)
                old_component=globals()['fit_component']; old_stage=g.fit_stage
                def reject(*args,**kwargs):raise AssertionError('No learning during saved replay')
                globals()['fit_component']=reject;g.fit_stage=reject
                try:
                    replayed,norms=replay(valid,w.read(OUT/f'learning_{line}_fold{held}.json'))
                    assert norms==artifact['held_normalizers']
                    assert all(np.array_equal(predicted[n],replayed[n]) for n in NAMES)
                finally:
                    globals()['fit_component']=old_component;g.fit_stage=old_stage
                train=f.loc[f.fold.ne(held)]
                value=np.exp(train.log_relative_A1S.to_numpy(float))*train.e_cost_scope.to_numpy(float)
                for shape in artifact['component']['shape']:value=b.shape_apply(train,value,shape)
                root=np.sqrt(value); independent=float(np.dot(train.T0.to_numpy(float),1/root)/root.sum())
                assert abs(independent/artifact['component']['level']-1)<1e-13
                derivative=np.sqrt(independent)*root.sum()-np.dot(train.T0.to_numpy(float),1/root)/np.sqrt(independent)
                assert abs(derivative)/max(1,root.sum())<1e-11
                ii=rowindex.loc[valid.row_id].to_numpy()
                for name in NAMES:oof.loc[ii,name]=predicted[name]
                comp=artifact['component']
                constants['shape_factors']+=comp['shape_factor_constants']
                constants['shape_training_normalizers']+=comp['shape_training_normalizers']
                constants['component_levels']+=comp['level_constants']
                constants['residual_factors']+=sum(len(s['factors']) for s in artifact['stages'])
                constants['residual_nuisance_levels']+=sum(len(s['nuisance_year_business']) for s in artifact['stages'])
                checks.append({'line':line,'fold':held,'full_learning_cost_reserve_invariant':True,
                               'saved_replay_with_learning_blocked_exact':True,'level_independent_moment_and_derivative':True})
        assert oof[NAMES].notna().all().all() and (oof[NAMES]>0).all().all()
        oof.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
        result=statistics(oof,plan)
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
            'status':'complete_exploratory_no_formal_admission','plan_sha256':w.sha(PLAN),
            'rows':len(oof),'groups':int(oof.group_id.nunique()),'new_iterative_fits':0,'new_C0_fits':0,
            'unique_primary_learning_constants':constants,'control_recomputations_same_constants_separate':constants,
            'new_final_test_prices':0,'new_submissions':0,'numeric_controls':checks,**result,
            '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'limits':plan['limits']}
    dump(OUT/'report.json',report)
    print(json.dumps({k:report[k] for k in ['scores','primary_delta_vs_G3','primary_bootstrap95','fold_contributions','year_contributions','post31_delta','gates','weighted2025_sensitivity_delta','unique_primary_learning_constants']},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','register','run']);args=p.parse_args()
    {'prepare':prepare,'register':register,'run':run}[args.mode]()
