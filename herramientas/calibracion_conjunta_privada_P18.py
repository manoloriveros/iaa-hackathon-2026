"""Receta completa más simple: GAM absoluto y calibración Tweedie conjunta.

Sin mezcla N3, bandas destino, media H1 o normalizadores al predecir.
Los C0guardados se reutilizan como enlaces de observación, sin reajustarlos.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
import warnings

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; SOURCE = BASE/'P16_GAM_bedrooms_lineal_20261026'
PREVIOUS = BASE/'P17_validacion_GAM_20261026'; OUT = BASE/'P18_calibracion_conjunta_20261026'
PLAN = R/'registro/semana2_calibracion_conjunta_privada_plan.json'
INDEX = R/'registro/semana2_calibracion_conjunta_privada_actual.json'
sp = importlib.util.spec_from_file_location('p18_common_evaluation', R/'herramientas/validar_GAM_privada_P17.py')
parent = importlib.util.module_from_spec(sp); sp.loader.exec_module(parent)
engine = parent.engine; w = parent.w; np = parent.np; pd = parent.pd
engine.OUT = OUT
from scipy import sparse
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning

LINES = ['motor', 'buildings', 'contents']
VARIABLES = {'motor': ['gender'], 'buildings': [], 'contents': ['gender', 'works_from_home', 'marketing_segment']}
PARAMS = dict(power=1.5, alpha=1., link='log', solver='lbfgs', max_iter=3000, tol=1e-7)
OTHER = '__P18_OTHER__'; MISSING = '__P18_MISSING__'


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def event(kind, **obj):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as f: f.write(json.dumps({'utc': utc(), 'kind': kind, **obj})+'\n')


def cat(s): return s.astype(object).where(s.notna(), MISSING).astype(str)


def design(f, enc):
    columns = []; names = []
    for line in LINES:
        for nb in [0, 1]:
            columns.append((f.line.eq(line) & f.new_business.eq(bool(nb))).to_numpy(float))
            names.append(line+'|NB'+str(nb))
    for key, levels in enc['levels'].items():
        line, variable = key.split('|'); values = cat(f[variable]); app = f.line.eq(line).to_numpy()
        values = values.where(values.isin(levels), OTHER)
        for level in levels:
            columns.append(app*values.eq(level).to_numpy(float)); names.append(key+'='+level)
    raw = np.column_stack(columns)
    if 'mean' in enc: raw = (raw-np.asarray(enc['mean']))/np.asarray(enc['scale'])
    return sparse.csr_matrix(raw), names


def encoder(train):
    enc = {'levels': {}}
    for line, variables in VARIABLES.items():
        for variable in variables:
            levels = sorted(cat(train.loc[train.line.eq(line), variable]).unique().tolist())
            assert OTHER not in levels and len(levels) <= 30
            enc['levels'][line+'|'+variable] = levels+[OTHER]
    raw, names = design(train, enc); dense = raw.toarray()
    mean = dense.mean(axis=0); scale = dense.std(axis=0); scale = np.where(scale > 1e-12, scale, 1.)
    enc.update(mean=mean.tolist(), scale=scale.tolist(), feature_names=names)
    return enc


def factor(f, model):
    mat, names = design(f, model['encoder']); assert names == model['encoder']['feature_names']
    value = np.exp(np.asarray(mat@np.asarray(model['coef'])).ravel()+model['intercept'])
    assert np.isfinite(value).all() and (value > 0).all(); return value


def ultimate(f, model): return f.source_annual_rate.to_numpy(float)*f.exposure_calendar.to_numpy(float)*factor(f, model)


def learn(f, folder=None, tag='', role='primary'):
    train = f.loc[~f.is_held].copy()
    assert not set(train.group_id).intersection(f.loc[f.is_held, 'group_id'])
    y = train.T0.to_numpy(float); base = train.m0.to_numpy(float)
    assert (y >= 0).all() and np.isfinite(base).all() and (base > 0).all()
    enc = encoder(train); mat, _ = design(train, enc); ratio = y/base; weight = np.sqrt(base)
    estimator = TweedieRegressor(**PARAMS)
    if folder:
        folder.mkdir(parents=True); dump(folder/'fit_invoked.json', {'utc': utc(), 'tag': tag, 'role': role, 'plan_sha256': w.sha(PLAN)})
        event('estimator_fit_started', tag=tag, role=role)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always'); estimator.fit(mat, ratio, sample_weight=weight)
    model = {'encoder': enc, 'coef': estimator.coef_.tolist(), 'intercept': float(estimator.intercept_),
             'parameters': PARAMS, 'iterations': int(estimator.n_iter_),
             'training_row_digest': engine.b.digest(sorted(train.row_id)),
             'training_group_digest': engine.b.digest(sorted(set(train.group_id)))}
    if folder:
        dump(folder/'model_raw.json', model); event('estimator_fit_returned', tag=tag, role=role)
    assert not any(issubclass(a.category, ConvergenceWarning) for a in notes)
    r = factor(train, model); z = weight*(np.sqrt(r)-ratio/np.sqrt(r))/weight.sum()
    gradient = np.r_[np.asarray(mat.T@z).ravel()+estimator.coef_, z.sum()]
    assert np.abs(gradient).max() <= 1e-4
    without_intercept = np.exp(np.asarray(mat@estimator.coef_).ravel())
    moment = math.fsum((y/np.sqrt(base*without_intercept)).tolist())/math.fsum(np.sqrt(base*without_intercept).tolist())
    error = abs(moment/np.exp(model['intercept'])-1); assert error < 1e-4
    ii = np.unique(np.linspace(0, len(train)-1, min(16, len(train)), dtype=int))
    actual = engine.unit(y[ii], base[ii]*r[ii]).sum()
    normalized = np.sum(np.sqrt(base[ii])*engine.unit(ratio[ii], r[ii]))
    assert math.isclose(float(actual), float(normalized), rel_tol=2e-12, abs_tol=1e-7)
    controls = {'max_abs_gradient': float(np.abs(gradient).max()), 'training_intercept_moment_relative_error': error,
                'ratio_weight_cost_deviance_equivalence': True, 'warnings': [str(a.message) for a in notes]}
    if folder:
        dump(folder/'model.json', model); dump(folder/'controls.json', controls)
        event('estimator_fit_completed', tag=tag, role=role, parameters=len(model['coef'])+1)
    return model, controls


def frames():
    result = {}
    for line in LINES:
        f = pd.read_parquet(engine.P1/f'canonical_{line}.parquet')
        source = pd.read_parquet(SOURCE/f'historical_{line}_three_seed.parquet').set_index('row_id').loc[f.row_id]
        assert np.array_equal(source.year, f.year) and not source.is_test.any()
        f['source_annual_rate'] = np.exp(source.raw_log_rate.to_numpy(float))
        assert np.isfinite(f.source_annual_rate).all() and f.source_annual_rate.gt(0).all()
        result[line] = f
    return result


def scope_data(all_frames, cohort, outer):
    parts = []
    for line, full in all_frames.items():
        if cohort == 'POOLED':
            f = full.copy(); f['original_fold'] = f.fold.to_numpy(); f['is_held'] = f.fold.eq(outer)
            path = BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json'
            c0 = w.read(path)['artifact']['C0']
        else:
            f = engine.parent.make_scope(full, outer, -1); f['is_held'] = f.fold.eq(1)
            path = engine.P4/f'scope_{line}_outer{outer}_member-1/primary/C0.json'; c0 = w.read(path)
            assert f.loc[~f.is_held, 'year'].eq(2023).all() and f.loc[f.is_held, 'year'].eq(2024).all()
        assert c0['fit_row_ids'] == sorted(f.loc[~f.is_held, 'row_id'])
        _, q = engine.parent.frozen.completion(f, c0)
        assert np.isfinite(q).all() and (q > 0).all()
        f['eval_q'] = q; f['m0'] = f.source_annual_rate.to_numpy()*f.exposure.to_numpy()*q
        parts.append(f)
    f = pd.concat(parts, ignore_index=True)
    assert f.row_id.is_unique and not set(f.loc[~f.is_held, 'group_id']).intersection(f.loc[f.is_held, 'group_id'])
    return f


def synthetic():
    i = np.arange(360); lines = np.array(LINES)[i % 3]
    f = pd.DataFrame({'row_id': ['toy'+str(z) for z in i], 'group_id': ['g'+str(z % 60) for z in i],
                      'line': lines, 'new_business': (i//3) % 2 == 0, 'gender': np.where(i % 2, 'M', 'F'),
                      'works_from_home': i % 2 == 0, 'marketing_segment': np.where(i % 4, 'a', 'b'),
                      'source_annual_rate': np.array([500., 350., 100.])[i % 3],
                      'exposure': .3+(i % 7)/10, 'exposure_calendar': .30001+(i % 7)/10,
                      'eval_q': .8, 'is_held': i % 5 == 0, 'reserve': 0.})
    f['m0'] = f.source_annual_rate*f.exposure*f.eval_q
    f['T0'] = np.where(i % 7 == 0, f.m0*7, 0.)
    model, controls = learn(f); bad = f.copy(); bad.loc[bad.is_held, ['T0', 'reserve']] = -1e20
    other, _ = learn(bad); assert engine.b.digest(model) == engine.b.digest(other)
    valid = f.loc[f.is_held].copy(); predicted = ultimate(valid, model)
    loaded = json.loads(json.dumps(model)); assert np.array_equal(predicted, ultimate(valid, loaded))
    perm = np.arange(len(valid))[::-1]; assert np.array_equal(predicted[perm], ultimate(valid.iloc[perm], loaded))
    split = len(valid)//2; assert np.array_equal(predicted, np.r_[ultimate(valid.iloc[:split], loaded), ultimate(valid.iloc[split:], loaded)])
    tr = f.loc[~f.is_held]; mat, _ = design(tr, model['encoder']); base = tr.m0.to_numpy(); y = tr.T0.to_numpy()
    theta = np.r_[model['coef'], model['intercept']]
    def obj(t): return float(.5*engine.unit(y, base*np.exp(mat@t[:-1]+t[-1])).sum()/np.sqrt(base).sum()+.5*np.dot(t[:-1], t[:-1]))
    r = factor(tr, model); z = np.sqrt(base)*(np.sqrt(r)-(y/base)/np.sqrt(r))/np.sqrt(base).sum()
    grad = np.r_[np.asarray(mat.T@z).ravel()+theta[:-1], z.sum()]; errors = []
    for j in range(len(theta)):
        a = theta.copy(); b = theta.copy(); a[j] += 1e-5; b[j] -= 1e-5
        errors.append(abs((obj(a)-obj(b))/2e-5-grad[j]))
    assert max(errors) < 1e-7
    return {'synthetic_joint_GLMfits_separate': 2, 'complete_held_poison_JSON_shuffle_batch_invariant': True,
            'offset_objective_gradient_two_methods': True, 'gradient_finite_difference_max_error': max(errors),
            'no_application_normalizers': True, 'new_contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert not w.read(engine.state.PHASE).get('active_jobs') and not w.read(engine.state.PHASE).get('active_execution')
    OUT.mkdir(); all_frames = frames(); scopes = []; paths = [Path(__file__), Path(parent.__file__), Path(engine.__file__),
        SOURCE/'report.json', SOURCE/'amendment_replay_context.json', R/'registro/semana2_GAM_bedrooms_lineal_plan.json',
        PREVIOUS/'report.json', PREVIOUS/'context_report.json', BASE/'estimando_cartera2025_v3/weights.parquet']
    for line in LINES: paths += [engine.P1/f'canonical_{line}.parquet', SOURCE/f'historical_{line}_three_seed.parquet']
    for cohort in ['POOLED', 'TRANSFER']:
        paths += [PREVIOUS/(cohort+'_prices.parquet'), PREVIOUS/(cohort+'_joint_bootstrap.npy')]
        for outer in range(5):
            f = scope_data(all_frames, cohort, outer); tr = f.loc[~f.is_held]
            scopes.append({'cohort': cohort, 'outer': outer, 'train_rows': len(tr), 'held_rows': int(f.is_held.sum()),
                           'training_row_digest': engine.b.digest(sorted(tr.row_id)),
                           'training_group_digest': engine.b.digest(sorted(set(tr.group_id)))})
            for line in LINES:
                paths.append(BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json' if cohort == 'POOLED' else engine.P4/f'scope_{line}_outer{outer}_member-1/primary/C0.json')
    fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    previous_plan = w.read(R/'registro/semana2_GAM_validacion_privada_plan.json')
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'GAM_absolute_joint_ridge',
            'hypothesis': 'Joint country calibration with regularized line/business main effects may reduce level variance while retaining fixed source risk functions and existing target covariates.',
            'necessity': 'P17sourceGAMpoint gain is not robust and buildings component levels vary across folds. Existing credibility already uses positive claims, not row counts; no counting bug is alleged.',
            'algorithm': 'New complete simpler algorithm: absolute sourceGAMannualrate plus one joint ridgeTweediecalibrator. No N3blend, target band corrections, H1member mean or prediction-cohort normalization.',
            'calibration': {'parameters': PARAMS, 'global_intercept_unpenalized': True,
                            'cell_effects': 'All6line/newbusinesscells, full symmetric onehot; alpha1coefficient penalty.',
                            'covariates': VARIABLES, 'encoding': 'Training-only category levels with OTHERfallback, full onehot, training mean/std; constant-columnscale1.',
                            'objective': 'm0=absoluteGAMannualrate*roundedE*qSource; response=T0/m0,weights=sqrt(m0). Weighted Tweedie1.5deviance equals costdeviance up to fixed normalizer. Alpha1fixed in normalized objective, no search.'},
            'forward': 'sourceannualrate*calendarE*exp(intercept+Zbeta), rowwise with fixed training encoders/scales. No observed outcome, qSource or cohort normalizer in ultimate prediction.',
            'evaluation': 'Same frozen qSource outer adapter and4scenarios as A1S/S2/H1. PureGammaalgorithm versus incumbent primary and P17GAM/S2/H1secondary; not a one-change causal ablation.',
            'budget': {'primary_joint_price_GLMfits': 10, 'adverse_joint_price_GLMfits_separate': 10,
                       'new_source_fits': 0, 'new_C0_fits': 0, 'new_future2025inference': 0, 'new_finaltestprices': 0, 'new_submissions': 0},
            'bootstrap': previous_plan['bootstrap'], 'level_sensitivity': previous_plan['level_sensitivity'],
            'criteria': previous_plan['criteria'], 'source_models_per_line': 1, 'preflight': fixture,
            'scopes': scopes, 'sources': {w.rel(p): w.sha(p) for p in dict.fromkeys(paths)},
            'limits': ['Pooling assumes country-scale adjustments can borrow across lines; genuinely different market effects may be overshrunk.',
                       'Several components are removed together, so a gain cannot be assigned solely to ridge regularization.',
                       'Current source2024and adaptive target2023/2024remain conditional; no private outcome is available.',
                       'Frozen valuation/tail sensitivities do not revalue/refit the source or every branch.',
                       'Covariate temporal availability and failed2025weightESS remain unresolved.'],
            '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P18antes de ajustar: nueva receta completa más sencilla, GAMabsoluto con calibración Tweedie conjunta regularizada. '
                    'Intercepto país libre, seis efectos ramo/negocio y solo covariables destino G3existentes; alpha1fijo, encoders/escalas de entrenamiento. '
                    'm0=GAMabs×Eredondeada×qSource; respuestaT0/m0,pesos√m0, con igualdad exacta de desviación de coste comprobada. '
                    'El precio último esGAMabs×Ecalendario×factor, sin N3, bandas destino, media H1o normalizadores de cohorte. Es un cambio completo de algoritmo, no una ablación causal única. '
                    'La credibilidad anterior ya cuenta positivos, no filas; se prueba compartir escala, no se corrige un bug de conteo. '
                    'Los10ámbitos(5combinados+5transferencia) conservan grupos/C0; presupuesto10GLMprimarios+10adversos, cero fuente/C0/precios2025/envíos. '
                    'El fixture completo pasó poison,JSON,orden,lotesygradiente independiente; no se estimó ningún precio del concurso. '
                    'Primario contra A1S/S2/H1, secundario contra P17; mismos mínimos, intervalos, Post31,pisos y escenarios. '
                    'La hipótesis de pooling puede fallar si los mercados difieren por ramo; no se eligen pesos o penalizaciones por score. '
                    'B00/F3c/P6y adversos intactos,2024abierto adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    r = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                        '--id', 'COD-S2-20261026-PRIVADA-P18-CONJUNTA-PREVIO', '--asunto',
                        'P18 previo: calibración conjunta estándar sobre GAM absoluto, sin normalizadores al predecir',
                        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P18registered_before_pricefits', 'plan': w.rel(PLAN),
               'plan_sha256': w.sha(PLAN), 'forum': json.loads(r.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'scopes': 10, 'new_contest_fits': 0, 'forum': receipt['forum']}))


def evaluate(plan):
    results = {}
    for cohort in ['POOLED', 'TRANSFER']:
        ref = pd.read_parquet(engine.P2/'held_nested_prices.parquet' if cohort == 'POOLED' else engine.P4/'held2024_transfer_prices.parquet')
        meta = ref[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']].copy().reset_index(drop=True)
        held = pd.concat([pd.read_parquet(OUT/f'{cohort}_{k}/prices.parquet') for k in range(5)]).set_index('row_id').loc[meta.row_id]
        base = ref.T_B.to_numpy() if cohort == 'POOLED' else ref.nominal_mean.to_numpy()
        candidate = held.new_nominal.to_numpy(); y = meta.T0.to_numpy(float)
        previous = pd.read_parquet(PREVIOUS/(cohort+'_prices.parquet')).set_index('row_id').loc[meta.row_id]
        reserve = pd.concat([pd.read_parquet(engine.P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in LINES]).set_index('row_id').loc[meta.row_id].reserve.to_numpy()
        ys = [y, y-.25*reserve, y+.25*reserve, y, y]; data = [(y, base, candidate)]
        saved = meta.copy(); saved['old_nominal'] = base; saved['new_nominal'] = candidate
        for j, name in enumerate(engine.NAMES[1:], 1):
            ratio = previous[name+'_new'].to_numpy()/previous.new_nominal.to_numpy()
            old = previous[name+'_old'].to_numpy(); new = candidate*ratio
            data.append((ys[j], old, new)); saved[name+'_old'] = old; saved[name+'_new'] = new
        weight = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[meta.row_id]
        assert np.array_equal(weight.group_id, meta.group_id)
        results[cohort] = engine.metrics(meta, data, cohort, weight.weight.to_numpy(), plan)
        saved.to_parquet(OUT/(cohort+'_prices.parquet'), index=False)
    return results


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.sha(PLAN) == w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'script': w.rel(Path(__file__)),
                 'kind': 'P18joint_ridge_complete_algorithm', 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); engine.state.state_execution(execution)
    try:
        all_frames = frames()
        for scope in plan['scopes']:
            cohort, outer = scope['cohort'], scope['outer']; tag = cohort+'|'+str(outer)
            folder = OUT/f'{cohort}_{outer}'; folder.mkdir(); f = scope_data(all_frames, cohort, outer)
            assert engine.b.digest(sorted(f.loc[~f.is_held, 'row_id'])) == scope['training_row_digest']
            model, controls = learn(f, folder/'primary', tag, 'primary')
            bad = f.copy(); bad.loc[bad.is_held, ['T0', 'reserve']] = -1e20
            other, _ = learn(bad, folder/'poison', tag, 'poison'); assert engine.b.digest(model) == engine.b.digest(other)
            valid = f.loc[f.is_held].copy(); u = ultimate(valid, model)
            assert np.array_equal(u, ultimate(bad.loc[bad.is_held], other))
            observed_raw = valid.m0.to_numpy()*factor(valid, model)
            assert np.allclose(observed_raw, u*(valid.exposure/valid.exposure_calendar).to_numpy()*valid.eval_q.to_numpy(), rtol=3e-15)
            perm = np.arange(len(valid))[::-1]; assert np.array_equal(u[perm], ultimate(valid.iloc[perm], model))
            split = len(valid)//2; assert np.array_equal(u, np.r_[ultimate(valid.iloc[:split], model), ultimate(valid.iloc[split:], model)])
            prices = pd.DataFrame({'row_id': valid.row_id.to_numpy(), 'new_ultimate': u,
                                   'eval_q': valid.eval_q.to_numpy(), 'new_nominal': u*valid.eval_q.to_numpy()})
            prices.to_parquet(folder/'prices.parquet', index=False)
            dump(folder/'committed.json', {'scope': scope, 'whole_current_learner_held_poison_exact': True,
                                           'row_shuffle_batch_exact': True, 'observation_bridge_checked': True,
                                           'controls': controls, 'outputs': {w.rel(p): w.sha(p) for p in folder.rglob('*') if p.is_file()}})
            print(json.dumps({'scope': tag, 'complete': True, 'parameters': len(model['coef'])+1}), flush=True)
        results = evaluate(plan); a = results['POOLED']['NOMINAL']; t = results['TRANSFER']['NOMINAL']
        gates = {'pooled_delta_ge002': a['delta'] >= .002, 'pooled_lower95_positive': a['bootstrap95'][0] > 0,
                 'pooled_atleast4positive_folds': sum(v > 0 for v in a['folds'].values()) >= 4,
                 'both_pooled_years_nonnegative': min(a['years'].values()) >= 0, 'pooled_post31_nonnegative': a['post31_delta'] >= 0,
                 'conditional_transfer_nonnegative': t['delta'] >= 0,
                 'all_nominal_and_stress_cell_floors': all(v['worst_cell_delta'] >= -.001 for c in results.values() for v in c.values())}
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P18joint_ridge_complete_algorithm_evaluated',
                  'results': results, 'diagnostic_gates': gates, 'new_primary_joint_GLMfits': 10,
                  'new_adverse_joint_GLMfits_separate': 10, 'new_source_fits': 0, 'new_C0_fits': 0,
                  'new_future2025inference': 0, 'new_finaltestprices': 0, 'new_submissions': 0,
                  'rowwise_forward_no_application_normalizers': True, 'formal_promotion': False,
                  'private_improvement_established': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
                  'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits']}
        dump(OUT/'report.json', report)
        paired = parent.paired; paired.OUT = OUT; paired.PREVIOUS = PREVIOUS; paired.PLAN = PLAN
        secondary = paired.secondary_results(report)
        dump(OUT/'secondary_report.json', {'author': 'Codex', 'utc': utc(), 'comparator': 'P17GAM_S2_H1',
                                          'results': secondary, 'new_resampling': 0, 'report_sha256': w.sha(OUT/'report.json')})
        print(json.dumps({'status': report['status'], 'gates': gates, 'primary_nominal':
                           {c: {k: a['NOMINAL'][k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for c, a in results.items()}}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'committed_scopes': len(list(OUT.glob('*/committed.json'))),
              'next': 'Reconcile actual estimator events/raw models before continuing; never blind-refit committed scopes'})
        raise
    finally: engine.state.state_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    plan = w.read(PLAN); assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    old_fit = TweedieRegressor.fit
    def reject(*a, **kw): raise AssertionError('Joint calibration fitting forbidden in replay')
    TweedieRegressor.fit = reject
    try:
        all_frames = frames()
        for scope in plan['scopes']:
            cohort, outer = scope['cohort'], scope['outer']; folder = OUT/f'{cohort}_{outer}'
            commit = w.read(folder/'committed.json'); assert all(w.sha(ROOT/p) == z for p, z in commit['outputs'].items())
            f = scope_data(all_frames, cohort, outer); f.loc[f.is_held, ['T0', 'reserve']] = 1e30
            valid = f.loc[f.is_held]; model = w.read(folder/'primary/model.json'); p = pd.read_parquet(folder/'prices.parquet')
            assert np.array_equal(valid.row_id, p.row_id) and np.array_equal(ultimate(valid, model), p.new_ultimate)
            assert np.array_equal(p.new_ultimate.to_numpy()*valid.eval_q.to_numpy(), p.new_nominal)
    finally: TweedieRegressor.fit = old_fit
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P18all10saved_joint_flows_exact',
                                  'scopes': 10, 'held_payload_poisoned': True, 'fit_blocked': True,
                                  'new_fits': 0, 'new_source_inference': 0, 'report_sha256': w.sha(OUT/'report.json')})
    print(json.dumps({'replay': 'exact', 'scopes': 10, 'new_fits': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with engine.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
