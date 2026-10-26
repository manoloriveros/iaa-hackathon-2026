"""GLM por peril, solo entrenamiento fuente interno con offsets número/marca."""
from datetime import datetime, timezone
import argparse
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import warnings

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
P27 = BASE/'P27_contrato_frecuencia_20261026'
COUNTS = BASE/'recuentos_fuente2024_v1'; LINKS = BASE/'recuentos_fuente2024_rkm_reuse_v1'
OUT = BASE/'P28_fuente_frecuencia_marca_20261026'
PLAN = R/'registro/semana2_fuente_frecuencia_marca_privada_plan.json'
INDEX = R/'registro/semana2_fuente_frecuencia_marca_privada_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor, TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance
from scipy.special import xlogy
from threadpoolctl import threadpool_limits


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


p14 = load('p28_source_only_preprocessing', R/'herramientas/GLM_ausentes_privada_P14.py')
p27 = load('p28_response_contract', R/'herramientas/preparar_contrato_frecuencia_P27.py')
w = p27.w; LINES = ['motor', 'buildings', 'contents']
EST = {'fit_intercept': True, 'solver': 'lbfgs', 'max_iter': 3000, 'tol': 1e-7}


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def digest(values): return hashlib.sha256('\n'.join(sorted(map(str, values))).encode()).hexdigest()


def array_digest(values): return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def objective(matrix, y, weight, beta, intercept, family, alpha):
    mu = np.exp(matrix@beta+intercept)
    loss = 2*(xlogy(y, y/mu)-y+mu) if family == 'frequency' else 4*y/np.sqrt(mu)-8*np.sqrt(y)+4*np.sqrt(mu)
    return float(.5*np.average(loss, weights=weight)+.5*alpha*np.dot(beta, beta))


def gradient(matrix, y, weight, beta, intercept, family, alpha):
    mu = np.exp(matrix@beta+intercept)
    value = mu-y if family == 'frequency' else np.sqrt(mu)-y/np.sqrt(mu)
    g = weight*value/weight.sum()
    return np.r_[np.asarray(matrix.T@g).ravel()+alpha*beta, g.sum()]


def coefficients(matrix, y, weight, family, alpha):
    assert len(y) == matrix.shape[0] and np.isfinite(y).all() and (y >= 0).all()
    assert np.isfinite(weight).all() and (weight > 0).all() and np.sum(weight*y) > 0
    cls = PoissonRegressor if family == 'frequency' else TweedieRegressor
    kwargs = {} if family == 'frequency' else {'power': 1.5, 'link': 'log'}
    estimator = cls(alpha=alpha, **EST, **kwargs)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always'); estimator.fit(matrix, y, sample_weight=weight)
    model = {'family': family, 'coef': estimator.coef_.tolist(), 'intercept': float(estimator.intercept_),
        'parameters': estimator.get_params(), 'iterations': int(estimator.n_iter_),
        'warnings': [str(z.message) for z in notes],
        'convergence_warning': any(issubclass(z.category, ConvergenceWarning) for z in notes)}
    return model, estimator


def predict(matrix, model):
    return np.exp(np.asarray(matrix@np.asarray(model['coef'])).ravel()+model['intercept'])


def controls(matrix, y, weight, model, estimator, finite_difference=False):
    alpha = model['parameters']['alpha']; family = model['family']
    beta = np.asarray(model['coef']); grad = gradient(matrix, y, weight, beta, model['intercept'], family, alpha)
    assert not model['convergence_warning'] and np.max(np.abs(grad)) <= 1e-4
    mu = predict(matrix, model); assert np.isfinite(mu).all() and (mu > 0).all()
    assert np.allclose(mu, estimator.predict(matrix), rtol=3e-14)
    sample = np.unique(np.linspace(0, len(y)-1, min(16, len(y)), dtype=int))
    loaded = json.loads(json.dumps(model)); assert np.array_equal(predict(matrix[sample], loaded), mu[sample])
    assert np.array_equal(predict(matrix[sample[::-1]], loaded), mu[sample[::-1]])
    manual = [math.exp(math.fsum((row*beta).tolist())+model['intercept']) for row in matrix[sample].toarray()]
    assert np.allclose(manual, mu[sample], rtol=5e-13)
    errors = []
    if finite_difference:
        theta = np.r_[beta, model['intercept']]
        for j in range(len(theta)):
            plus = theta.copy(); minus = theta.copy(); plus[j] += 1e-5; minus[j] -= 1e-5
            numeric = (objective(matrix, y, weight, plus[:-1], plus[-1], family, alpha)-
                objective(matrix, y, weight, minus[:-1], minus[-1], family, alpha))/(2e-5)
            errors.append(abs(numeric-grad[j]))
        assert max(errors) < 3e-6
    return {'max_abs_gradient': float(np.max(np.abs(grad))), 'JSON_order_exact': True,
        'manual_predictor_parity': True, 'finite_difference_max_error': max(errors) if errors else None}


def synthetic():
    rng = np.random.default_rng(2026102668); n = 600
    x = pd.DataFrame({'numeric': rng.normal(size=n), 'exposure_model': rng.uniform(.1, 1, n),
        'category': pd.Categorical(np.where(np.arange(n)%2, 'A', 'B'))})
    x.loc[np.arange(n)%17 == 0, 'numeric'] = np.nan
    prep = p14.fit_preprocessor(x.iloc[:480]); prep.pop('penalty', None)
    matrix, names = p14.transform(x, prep); train = np.arange(n) < 480
    nn = rng.poisson(.4, n).astype(float); en = rng.uniform(.2, 1, n)
    rr = rng.uniform(.6, 1.3, n); ec = en*rr; cost = nn*rng.gamma(2, 100, n)
    cost[np.flatnonzero(nn > 0)[0]] = 0.
    selected, ratio, mark, weight = p27.transformed_mark(nn, cost, en, ec)
    assert (mark[train[selected]] == 0).any()
    controls_list = []
    for family in ['frequency', 'mark']:
        if family == 'frequency':
            mat = matrix[train]; y = nn[train]/en[train]; ww = en[train]
            alpha = .001*train.sum()/ww.sum()
        else:
            pick = ~np.zeros(selected.sum(), dtype=bool); pick &= train[selected]
            mat = matrix[selected][pick]; y = mark[pick]; ww = weight[pick]
            alpha = 1.*nn[selected][pick].sum()/ww.sum()
        model, estimator = coefficients(mat, y, ww, family, alpha)
        checked = controls(mat, y, ww, model, estimator, finite_difference=True)
        controls_list.append({'family': family, **checked})
    # Preprocessing is trained only on the same source training rows. Changes
    # to held labels cannot change any response/weight argument passed to fit.
    poisoned_n = nn.copy(); poisoned_cost = cost.copy()
    poisoned_n[~train] = 1e8; poisoned_cost[~train] = 1e20
    assert np.array_equal(poisoned_n[train], nn[train]) and np.array_equal(poisoned_cost[train], cost[train])
    loaded = json.loads(json.dumps(prep)); transformed, other_names = p14.transform(x, loaded)
    assert names == other_names and np.array_equal(matrix.toarray(), transformed.toarray())
    return {'author': 'Codex', 'utc': utc(), 'synthetic_GLM_fits_separate': 2,
        'new_contest_fits': 0, 'source_only_preprocessing_JSON_exact': True,
        'source_held_payload_argument_boundary': True, 'zero_mark_retained': True, 'controls': controls_list,
        'limit': 'Argument-boundary and synthetic objective checks; not repeated real fits under source-held poisoning.'}


def source_paths():
    paths = [Path(__file__), Path(p14.__file__), Path(p14.old.__file__), Path(p27.__file__),
        P27/'report.json', P27/'completion_receipt.json', P27/'synthetic_objective_identity.json',
        R/'registro/semana2_robustez2023_ciclo8_plan.json', R/'registro/semana2_robustez2023_ciclo16_plan.json',
        COUNTS/'report.json', LINKS/'report.json']
    for line in LINES:
        paths += [HOME/f'matrix_s1_{line}.parquet', HOME/f'rows_s1_{line}.parquet',
            HOME/f'partition_source/folds_{line}.parquet', COUNTS/f'counts_{line}.parquet', LINKS/f'rkm_links_{line}.parquet']
        paths += [BASE/f'P25_fuente_ausencias_20261026/{line}_seed{seed}_inner/validation_predictions.parquet' for seed in [11, 12, 13]]
    return paths


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    ready = w.read(P27/'report.json'); assert ready['all_preflight_support_pass']
    assert all(w.sha(ROOT/p) == z for p, z in ready['sources'].items())
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Paired_reporting_peril_Poisson_Tweedie15_main_effects_source_inner',
        'hypothesis': 'El coste agregado mezcla perils con retrasos y severidades distintos. Una suma de GLM número/marca con vínculos explícitos puede aportar una estructura de transporte más simple, sin árboles o interacciones.',
        'precedent': ready['prior_recipes'],
        'necessity_and_limits': 'P26small gain was concentrated and adverse in pooled newbusiness. Aggregate standard GLM/GAM variants failed whole-target gates. This does not prove causality of reporting or that another model will improve; source current4year paired-offset main effects differs from prior2023GLMs and FS/FSp cost proxies.',
        'features_and_preprocessing': 'All unchanged A1Smatrix predictors including duration, P14main effects and missing indicators. Fit preprocessing on source training groups only: median,0.5/99.5percentnumeric clip/scales,categories min100max40/dropfirst/OTHER, missing flags. No row/claim cost winsorization, feature search or interactions.',
        'configuration': {'frequency': {'class': 'PoissonRegressor', 'nominal_alpha': .001,
                'response': 'N/E_N_RKM', 'weight': 'E_N_RKM', 'alpha': '.001*n_original_training_rows/sum(E_N_RKM)'},
            'mark': {'class': 'TweedieRegressor', 'power': 1.5, 'nominal_alpha': 1.,
                'response': 'C/(N*r),r=E_C/E_N_RKM', 'weight': 'N*sqrt(r)', 'alpha': 'sum(N)/sum(N*sqrt(r))'},
            'estimator': EST, 'counts': 'Actual accepted claims, no T0positive-period proxy',
            'reference_constants': 'Per-peril Poisson rate=sum(N)/sum(E_N); mark=sum(C/sqrt(r))/sum(N*sqrt(r)), source training only.',
            'held_observed_cost': 'sum_perils(E_C*predicted_frequency*predicted_mark)'},
        'source_gate': {'comparator': 'Same-peril constant number/mark model trained on same source training groups, same paired offsets.',
            'max_relative_deviance_increase_each_line': .002, 'rule': 'All3lines aggregate held cost deviance <=1.002times same-contract constant baseline.',
            'A1S_tree_reference': 'Record original saved source-inner ensemble native predictions as context; no relative tree noninferiority gate for this different low-capacity family. Never infer target admission from this source gate.',
            'why': 'Standard family must improve its own same-estimand constant comparator; its transport merits require the unchanged later whole-target global/NBcriteria, not source tree imitation.'},
        'budget': {'source_inner_GLM_fits': 30, 'source_closed_baseline_constants': 30,
            'synthetic_GLM_fits_separate': 2, 'source_full_refits': 0, 'new_C0_fits': 0,
            'new_target_calibrations': 0, 'new_target_scores': 0, 'new_future_inference': 0, 'new_final_prices': 0, 'new_submissions': 0},
        'criteria': ['Save each JSONmodel before gradient/convergence checks, reconcile actual attempts, never blindly repeat failed fit.',
            'Gradient<=1e-4,no convergencewarning, finite positive predictions, JSON/ordering/scalar predictor agreement.',
            'Exact source training groups and rows from current partition; preprocessing and fit arguments exclude held labels/covariates.',
            'Argument extraction invariance for held count/cost poisoning, without extra real refits.',
            'All source gates and labels/offsets unchanged; no full refit or target assessment in this source-inner unit.'],
        'checkpoint': 'Stop between saved perils after30minutes; resume only after process reconciliation and all invoked fits have records. No failed-fit retry.',
        'sources': {w.rel(p): w.sha(p) for p in source_paths()}, 'synthetic': fixture,
        'limits': ready['estimand_limits']+['A main-effects mixture may underfit within-peril nonlinearities; no guarantee from simplicity.',
            'Source holdout and prior search are adaptive/conditional; no private-performance or professional independent-validation claim.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. Registro P28 antes de ajustar: GLM de efectos principales por15perils, '
        'Poisson de número y Tweedie1,5de marca, con los vínculos E_N RKM y E_C guardados. '
        'No es una primera familia FS: ciclo3/8/16y FS/FSpse conservan y sus contratos '
        'difieren. Usa fuente2021–2024actual, preprocesamiento P14aprendido solo en grupos '
        'fuente de entrenamiento, sin árboles, interacciones o búsqueda. Respuesta/peso '
        'y alpha reescalado según P27; se conserva la marca cero. Presupuesto30GLM '
        'internos y30constantes de referencia, dos GLM sintéticos aparte. Cero refits '
        'completos, C0, calibración/score destino, inferencia2025, precios o envíos. '
        'Veto fuente por ramo: desviación agregada retenida no mayor de1,002veces la '
        'referencia constante por peril bajo el mismo contrato. La referencia A1Sse '
        'reporta como contexto, sin fingir equivalencia de capacidad o un pase destino. '
        'Criterios globales/NB posteriores se mantienen; no se adopta por este veto. '
        'Pasaron dos ajustes sintéticos con gradientes por diferencias finitas, JSON, '
        'orden y predictor escalar; límites de argumentos retenidos explícitos. '
        'B00/F3c y adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P28-FRECUENCIA-PREVIO',
        '--asunto', 'P28: GLM número/marca con offsets pareados y veto fuente propio, sin refits completos',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P28registered_before_source_inner_fits',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'source_inner_budget': 30, 'forum': receipt['forum']}))


def state(status, execution):
    archive = R/'privado'/('p28_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    invoked = sorted(p.parent.name for p in OUT.glob('*/*/fit_invoked.json'))
    completed = sorted(p.parent.name for p in OUT.glob('*/*/fit_record.json'))
    cp = R/'registro/semana2_contadores_propios_actual.json'; counter = w.read(cp)
    old = counter.get('phase2_private_P28_source_pairs', {}).get('counted_keys', [])
    assert set(old).issubset(invoked); extra = len(set(invoked)-set(old))
    current = {'author': 'Codex', 'utc': utc(), 'status': status, 'execution': execution,
        'attempts': len(invoked), 'completed': len(completed), 'output': w.rel(OUT),
        'new_C0_fits': 0, 'new_target_scores': 0, 'new_submissions': 0}
    w.update(cp, {'cumulative_price_base_fits': counter['cumulative_price_base_fits']+extra,
        'phase2_private_P28_source_pairs': {'counted_keys': invoked, 'attempts': len(invoked), 'completed': len(completed)}}, archive)
    w.update(INDEX, current, archive); phase_path = R/'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phase_path)
    jobs = [] if execution is None else [execution]
    w.update(phase_path, {'private_P28_source': current, 'active_execution': execution, 'active_jobs': jobs,
        'new_price_fits': phase['new_price_fits']+extra}, archive)
    sp = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(sp)['week_2_mission017_phase2_20261025']
    own.update(private_P28_source=current, active_jobs=jobs, new_price_fits=phase['new_price_fits']+extra)
    w.update(sp, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


def fit(folder, matrix, y, weight, family, alpha, metadata):
    assert not (folder/'fit_invoked.json').exists(); start = time.monotonic()
    dump(folder/'fit_invoked.json', {'utc': utc(), 'pid': os.getpid(), 'family': family,
        'plan_sha256': w.sha(PLAN), 'rows': len(y), 'y_sha256': array_digest(y), 'weight_sha256': array_digest(weight), **metadata})
    execution = {'author': 'Codex', 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'kind': 'P28source_inner_pairs', 'checkpoint': folder.name}
    state('P28source_fit_running', execution)
    try:
        model, estimator = coefficients(matrix, y, weight, family, alpha)
        dump(folder/'model.json', model)
        dump(folder/'fit_record.json', {'utc': utc(), 'seconds': time.monotonic()-start, 'model_sha256': w.sha(folder/'model.json'),
            'plan_sha256': w.sha(PLAN), 'rows': len(y), 'family': family, 'iterations': model['iterations'], **metadata})
        checked = controls(matrix, y, weight, model, estimator); dump(folder/'controls.json', checked)
    except BaseException as exc:
        dump(folder/'failure.json', {'utc': utc(), 'exception': type(exc).__name__, 'message': str(exc), 'no_blind_retry': True})
        raise
    state('P28source_fit_saved', execution)
    print(json.dumps({'fit': folder.name, 'iterations': model['iterations'], 'seconds': round(time.monotonic()-start, 1), 'gradient': checked['max_abs_gradient']}), flush=True)
    return model


def run(resume=False):
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in source_paths()}
    if resume:
        import psutil
        for proc in psutil.process_iter(['pid', 'cmdline']):
            if proc.pid != os.getpid():
                assert not any(Path(arg).name == Path(__file__).name for arg in (proc.info['cmdline'] or []))
        assert all((p.parent/'controls.json').exists() for p in OUT.glob('*/*/fit_invoked.json'))
        for path in OUT.glob('*/*/fit_record.json'):
            assert w.read(path)['model_sha256'] == w.sha(path.parent/'model.json')
        dump(OUT/('resume_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'), {'utc': utc(), 'pid': os.getpid()})
    else: dump(OUT/'started.json', {'utc': utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN)})
    begin = time.monotonic(); checkpointed = False
    try:
        for line in LINES:
            folder = OUT/line; folder.mkdir(exist_ok=True)
            if (folder/'summary.json').exists():
                assert w.read(folder/'summary.json')['held_predictions_sha256'] == w.sha(folder/'held_predictions.parquet')
                continue
            x = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
            rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'T0', 'T0_cents', 'year'])
            part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
            count = pd.read_parquet(COUNTS/f'counts_{line}.parquet'); link = pd.read_parquet(LINKS/f'rkm_links_{line}.parquet')
            assert all(np.array_equal(f.row_id, rows.row_id) for f in [part, count, link])
            assert np.array_equal(count.T0_cents_total, rows.T0_cents) and rows.year.isin([2021, 2022, 2023, 2024]).all()
            held = part.internal_validation.to_numpy(bool); train = ~held
            assert set(part.loc[train, 'source_group']).isdisjoint(part.loc[held, 'source_group'])
            prep_path = folder/'preprocessor.json'
            if not prep_path.exists():
                prep = p14.fit_preprocessor(x.loc[train]); prep.pop('penalty', None); dump(prep_path, prep)
            else: prep = w.read(prep_path)
            matrix, names = p14.transform(x, prep)
            meta = {'scope_training_row_digest': digest(rows.loc[train, 'row_id']), 'scope_training_group_digest': digest(part.loc[train, 'source_group'].unique()),
                'preprocessor_sha256': w.sha(prep_path), 'columns': names}
            all_new = np.zeros(held.sum()); all_constant = np.zeros(held.sum())
            perils = [z['peril'] for z in w.read(P27/'report.json')['by_line_peril'] if z['line'] == line]
            for peril in perils:
                n = count['N_'+peril].to_numpy(float); cost = count['T0_cents_'+peril].to_numpy(float)/100
                en = link['E_count_rkm_'+peril].to_numpy(float); ec = count['E_cost_'+peril].to_numpy(float)
                selected, ratio, ymark, wmark = p27.transformed_mark(n, cost, en, ec)
                positive = selected&train; informative = (en > 0)&train
                poison_n = n.copy(); poison_c = cost.copy(); poison_n[held] = 1e8; poison_c[held] = 1e20
                assert np.array_equal(poison_n[train], n[train]) and np.array_equal(poison_c[train], cost[train])
                models = {}
                for family in ['frequency', 'mark']:
                    target = folder/f'{line}_{peril}_{family}'; target.mkdir(exist_ok=True)
                    if family == 'frequency':
                        idx = informative; mat = matrix[idx]; y = n[idx]/en[idx]; weight = en[idx]
                        alpha = .001*train.sum()/weight.sum()
                    else:
                        idx = positive; mark_train = train[selected]; mat = matrix[idx]
                        y = ymark[mark_train]; weight = wmark[mark_train]
                        alpha = n[idx].sum()/weight.sum()
                    if not (target/'controls.json').exists():
                        model_meta = {**meta, 'fit_row_digest': digest(rows.loc[idx, 'row_id']),
                            'fit_group_digest': digest(part.loc[idx, 'source_group'].unique())}
                        models[family] = fit(target, mat, y, weight, family, alpha, model_meta)
                    else:
                        saved = w.read(target/'fit_record.json'); assert saved['model_sha256'] == w.sha(target/'model.json')
                        models[family] = w.read(target/'model.json')
                lambda0 = float(n[train].sum()/en[train].sum())
                rr = ec[positive]/en[positive]
                mark0 = float(np.sum(cost[positive]/np.sqrt(rr))/np.sum(n[positive]*np.sqrt(rr)))
                assert lambda0 > 0 and mark0 > 0
                path = folder/(peril+'_constant.json')
                if not path.exists(): dump(path, {'frequency': lambda0, 'mark': mark0, 'new_closed_constants': 2})
                else: assert w.read(path) == {'frequency': lambda0, 'mark': mark0, 'new_closed_constants': 2}
                annual = predict(matrix[held], models['frequency'])*predict(matrix[held], models['mark'])
                all_new += ec[held]*annual; all_constant += ec[held]*lambda0*mark0
                if time.monotonic()-begin > 30*60:
                    checkpointed = True; state('P28checkpoint_between_saved_perils', None)
                    print(json.dumps({'checkpoint': line+'|'+peril}), flush=True); return
            old = [pd.read_parquet(BASE/f'P25_fuente_ausencias_20261026/{line}_seed{seed}_inner/validation_predictions.parquet', columns=['row_id', 'old_native']) for seed in [11, 12, 13]]
            assert all(np.array_equal(o.row_id, rows.loc[held, 'row_id']) for o in old)
            tree = np.exp(np.mean([o.old_native.to_numpy() for o in old], axis=0))
            held_rows = rows.loc[held, ['row_id', 'year']].copy(); held_rows['candidate'] = all_new
            held_rows['constant'] = all_constant; held_rows['original_tree'] = tree
            held_rows.to_parquet(folder/'held_predictions.parquet', index=False)
            y = rows.T0.to_numpy(float)[held]
            assert np.isfinite(all_new).all() and (all_new > 0).all()
            lc = float(mean_tweedie_deviance(y, all_new, power=1.5)); lb = float(mean_tweedie_deviance(y, all_constant, power=1.5))
            summary = {'line': line, 'rows': len(y), 'candidate_deviance': lc, 'constant_deviance': lb,
                'original_tree_deviance_context': float(mean_tweedie_deviance(y, tree, power=1.5)),
                'relative_loss_vs_constant': lc/lb-1, 'source_gate_pass': lc <= 1.002*lb,
                'held_predictions_sha256': w.sha(folder/'held_predictions.parquet'),
                'protected_argument_boundary_not_extra_poison_fits': True}
            dump(folder/'summary.json', summary)
            del x, rows, part, count, link, matrix; gc.collect()
        assert plan['sources'] == {w.rel(p): w.sha(p) for p in source_paths()}
        summaries = [w.read(OUT/line/'summary.json') for line in LINES]
        assert len(list(OUT.glob('*/*/fit_invoked.json'))) == len(list(OUT.glob('*/*/controls.json'))) == 30
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P28source_inner_complete_not_admitted',
            'source_gate_all_pass': all(s['source_gate_pass'] for s in summaries), 'results': summaries,
            'new_source_GLM_fits': 30, 'new_source_baseline_constants': 30, 'source_full_refits': 0,
            'new_C0_fits': 0, 'new_target_scores': 0, 'new_future_inference': 0, 'new_submissions': 0,
            'plan_sha256': w.sha(PLAN), 'private_improvement_established': False, 'goal_achieved': False,
            '2024_open': True, 'B00_all_alternatives_preserved': True, 'limits': plan['limits']}
        dump(OUT/'report.json', report); state(report['status'], None)
        print(json.dumps({'status': report['status'], 'source_gate_all_pass': report['source_gate_all_pass'], 'results': summaries}), flush=True)
    finally:
        if not (OUT/'report.json').exists() and not checkpointed: state('P28unfinished_reconcile_saved_attempts_before_any_resume', None)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'resume']); args = parser.parse_args()
    with threadpool_limits(limits=2):
        if args.mode == 'prepare': prepare()
        else: run(resume=args.mode == 'resume')
