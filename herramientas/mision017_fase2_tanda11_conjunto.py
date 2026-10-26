"""GLM Tweedie conjunto, mismos factores y contracción Fisher equivalente K300."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

b = load('sequential11', R / 'herramientas/mision017_fase2_tanda10_factores.py')
import numpy as np
import pandas as pd
from scipy import optimize, sparse
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

OUT = b.BASE / 'tanda11_conjunto_20261026_v1'; PLAN = R / 'registro/semana2_mision017_fase2_tanda11_plan_v1.json'
sha = b.sha; read = b.read; dump = b.dump; rel = b.rel; digest = b.digest
now = b.now; NAMES = ['J1', 'J2', 'J3']; K = 300.
FAMILIES = {'motor': {'J1': ['gender']}, 'contents': {'J1': ['gender'],
    'J2': ['gender', 'works_from_home'], 'J3': ['gender', 'works_from_home', 'marketing_segment']}}

def category_matrix(f, variables, categories):
    blocks = []
    for variable, levels in zip(variables, categories):
        code = pd.Categorical(b.key(f[variable]), categories=levels).codes; active = code >= 0
        rows = np.arange(len(f))[active]
        blocks.append(sparse.csr_matrix((np.ones(len(rows)), (rows, code[active])), shape=(len(f), len(levels))))
    return sparse.hstack(blocks, format='csr')

def fit_scope(f, held, line, family, variables, checkpoint=None):
    train = f.loc[f.fold.ne(held)].copy(); valid = f.loc[f.fold.eq(held)]
    assert not set(train.group_id).intersection(valid.group_id) and train.T0.ge(0).all()
    enc = OneHotEncoder(drop=None, sparse_output=True, handle_unknown='ignore')
    raw = pd.DataFrame({name: b.key(train[name]) for name in variables})
    cat = enc.fit_transform(raw); categories = [x.tolist() for x in enc.categories_]
    assert np.array_equal(cat.toarray(), category_matrix(train, variables, categories).toarray())
    nuisance_keys = ['2023|0', '2023|1', '2024|0', '2024|1']
    keys = np.array([f'{int(y)}|{int(nb)}' for y, nb in zip(train.year, train.new_business)])
    nuisance = np.column_stack([keys == key for key in nuisance_keys]).astype(float)
    assert (nuisance.sum(axis=0) > 0).all(); X = sparse.hstack([cat, sparse.csr_matrix(nuisance)], format='csr')
    y = train.T0.to_numpy(float); base = train.base_N3.to_numpy(float); offset = np.log(base)
    positives = int(np.count_nonzero(y > 0)); S = float(np.sqrt(base).sum()); assert positives > 0 and S > 0
    # On the sum loss: lambda=K*(sum sqrt(base))/n_positive. Dividing the
    # objective by S gives ridge=K/n_positive. No validation moment enters.
    ridge = K / positives; penalty = np.r_[np.full(cat.shape[1], ridge), np.zeros(4)]
    coef = np.zeros(X.shape[1])
    for j in range(4):
        mask = nuisance[:, j].astype(bool)
        k = float(np.sum(y[mask] / np.sqrt(base[mask])) / np.sum(np.sqrt(base[mask]))); assert k > 0
        coef[cat.shape[1] + j] = np.log(k)
    def objective(beta):
        root = np.exp((offset + X @ beta) / 2)
        value = 2 * np.sum(root + y / root - 2 * np.sqrt(y)) / S + .5 * np.dot(penalty * beta, beta)
        gradient = np.asarray(X.T @ ((root - y / root) / S)).ravel() + penalty * beta
        return float(value), gradient
    result = optimize.minimize(objective, coef, method='L-BFGS-B', jac=True,
        options={'maxiter': 2000, 'gtol': 1e-10, 'ftol': 1e-15, 'maxls': 50})
    value, gradient = objective(result.x)
    if checkpoint is not None: dump(checkpoint, {'utc': now(), 'line': line, 'family': family, 'fold': held,
        'coef': result.x.tolist(), 'success': bool(result.success), 'message': str(result.message),
        'objective': value, 'max_abs_gradient': float(abs(gradient).max()), 'iterations': int(result.nit), 'before_guard': True})
    assert result.success and abs(gradient).max() < 1e-6, str(result.message)
    root = np.exp((offset + X @ result.x) / 2)
    H = (X.T @ X.multiply((.5 * (root + y / root) / S)[:, None])).toarray() + np.diag(penalty)
    eigen = np.linalg.eigvalsh(H); assert eigen.min() > 0
    return {'line': line, 'family': family, 'held_fold': int(held), 'variables': variables, 'categories': categories,
        'nuisance_keys': nuisance_keys, 'coef': result.x.tolist(), 'cat_dimensions': cat.shape[1],
        'K': K, 'positive_training_periods': positives, 'baseline_Fisher_mass': S, 'ridge_normalized': ridge,
        'ridge_on_sum_loss': ridge * S, 'penalty': penalty.tolist(), 'objective': value,
        'max_abs_gradient': float(abs(gradient).max()), 'iterations': int(result.nit), 'hessian_min_eigenvalue': float(eigen.min()),
        'training_rows': len(train), 'training_row_ids_digest': digest(sorted(train.row_id)),
        'training_groups_digest': digest(sorted(set(train.group_id))), 'training_label_digest': digest(y.tolist()),
        'input_base_digest': digest(base.tolist()), 'new_GLM_fits': 1, 'no_nuisance_intercept_transferred': True}

def apply(f, base, artifact):
    X = category_matrix(f, artifact['variables'], artifact['categories'])
    factor = np.exp(X @ np.asarray(artifact['coef'][:artifact['cat_dimensions']]))
    return b.normalise(f, base, factor)

def synthetic():
    rng = np.random.default_rng(2026102605); n = 1400
    f = pd.DataFrame({'row_id': ['s_' + str(i) for i in range(n)], 'group_id': ['g_' + str(i) for i in range(n)],
        'fold': np.arange(n) % 5, 'year': 2023 + (np.arange(n) // 5) % 2, 'new_business': (np.arange(n) // 10) % 2,
        'gender': rng.choice(['M', 'F'], n), 'works_from_home': rng.integers(0, 2, n),
        'marketing_segment': rng.choice(['budget', 'mainstream', 'affluent'], n),
        'T0': rng.gamma(2, 60, n) * (rng.random(n) < .4), 'base_N3': rng.uniform(25, 180, n)})
    variables = FAMILIES['contents']['J3']; a = fit_scope(f, 0, 'contents', 'J3', variables)
    poisoned = f.copy(); poisoned.loc[poisoned.fold.eq(0), 'T0'] = -1e30
    z = fit_scope(poisoned, 0, 'contents', 'J3', variables); assert digest(a) == digest(z)
    changed = f.copy(); changed.loc[changed.fold.ne(0), 'T0'] *= np.where(changed.loc[changed.fold.ne(0), 'gender'].eq('M'), 1.6, .7)
    alt = fit_scope(changed, 0, 'contents', 'J3', variables); assert digest(a) != digest(alt)
    v = f.loc[f.fold.eq(0)]; base = v.base_N3.to_numpy(float); pred, norm = apply(v, base, a)
    bad, norm2 = apply(v.assign(T0=-1e30), base, a); assert np.array_equal(pred, bad) and norm == norm2
    zero = {**a, 'coef': [0.] * len(a['coef'])}; identity, _ = apply(v, base, zero); assert np.array_equal(identity, base)
    unseen = v.copy()
    for col in variables: unseen[col] = '__UNSEEN__'
    neutral, _ = apply(unseen, base, a); assert np.array_equal(neutral, base)
    dump(OUT / 'synthetic.json', {'pass': True, 'full_learning_held_cost_invariant': True,
        'training_change_changes_learning': True, 'prediction_label_invariant': True,
        'zero_effect_and_all_unseen_identity': True, 'year_business_totals_preserved': True,
        'positive_definite_penalized_Hessian': True, 'synthetic_GLM_fits': 3, 'contest_GLM_fits': 0})

def preflight():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    with threadpool_limits(limits=2): synthetic()
    previous = read(b.OUT / 'preflight.json'); assert len(previous['scopes']) == 10
    assert read(b.OUT / 'validation_v1/report.json')['factor_parameters'] == 90
    paths = [Path(__file__), Path(b.__file__), b.PLAN, b.OUT / 'preflight.json', b.OUT / 'validation_v1/report.json',
        b.OUT / 'oof_2023_2024.parquet', b.OUT / 'completion_receipt.json']
    sources = {**previous['sources'], **previous['outputs'], **{rel(p): sha(p) for p in paths}}
    for path, value in sources.items(): assert sha(ROOT / path) == value, path
    dump(OUT / 'preflight.json', {'author': 'Codex', 'utc': now(), 'sources': sources,
        'existing_ten_N3_C0_scopes_and_covariates_reused': True, 'prior_scalar_checks_not_repeated': True,
        'novelty': 'Joint symmetric categorical main-effects GLM with Fisher-equivalent K300 ridge, versus one-pass sequential conditional factors',
        'real_GLM_fits': 0, 'new_C0_fits': 0, 'new_scores': 0})
    print(json.dumps({'preflight': 'complete', 'synthetic_pass': True, 'real_GLM_fits': 0, 'new_C0_fits': 0}))

def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = read(OUT / 'preflight.json'); assert read(OUT / 'synthetic.json')['pass']
    sources = {**pre['sources'], rel(OUT / 'preflight.json'): sha(OUT / 'preflight.json'), rel(OUT / 'synthetic.json'): sha(OUT / 'synthetic.json')}
    for path, value in sources.items(): assert sha(ROOT / path) == value, path
    original = read(b.PLAN)
    plan = {'id': 'S2-MISION017-FASE2-TANDA11-CONJUNTO-v1', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'A single joint penalized Tweedie objective can handle dependence among the same residual main effects and nuisance levels more coherently than a heuristic sequential pass. No new variables, categories, K tuning or nonlinear capacity.',
        'reference': 'Frozen N3 research benchmark; matched G1/G2/G3 additionally veto deterioration. Not full C1/F2.',
        'models': {'J1': 'Joint gender in motor/contents', 'J2': 'J1 plus joint gender/telework in contents',
            'J3': 'J1 plus joint gender/telework/marketing in contents'},
        'configuration': {'years': [2023, 2024], 'folds': 'same saved global components', 'offset': 'log(frozen N3 outer-training baseline)',
            'features': FAMILIES, 'encoding': 'full categorical one-hot, symmetric positive ridge on every level, unknown neutral0logeffect',
            'nuisance': 'four year/business intercepts unpenalized, learned on training only and not transferred',
            'criterion_objective': 'half summed Tweedie1.5 deviance plus half lambda times squared categorical coefficients',
            'K': K, 'Fisher_mass_S': 'sum sqrt(training N3)', 'lambda_sum_loss': 'K*S/n_positive_training_periods',
            'normalized_objective': 'sum_loss/S; ridge normalized=K/n_positive; this approximates prior K-positive information per category',
            'optimizer': {'method': 'L-BFGS-B', 'maxiter': 2000, 'gtol': 1e-10, 'ftol': 1e-15, 'maxls': 50,
                'max_gradient_guard': 1e-6}, 'normalization': 'same prediction-only per year/business, baseline totals preserved',
            'no_clipping_no_category_regrouping': True},
        'criterion': {**original['criterion'], 'extra_matched_sequential_veto': 'own unweighted point delta versus matching G stage must be nonnegative'},
        'bootstrap': {'replicates': 2000, 'seed': 2026102605, 'unit': 'saved connected component'},
        'budget': {'new_joint_GLM_fits': 20, 'motor_shared_across_J_families': True, 'new_C0_fits': 0,
            'new_source_fits': 0, 'held_prediction_only_normalizers': 80, 'new_test_prices': 0, 'submissions': 0},
        'candidate_priority_if_all_checks_pass': ['J1', 'J2', 'J3'],
        'limits': original['limits'] + ['Fisher prior is an approximation, not empirical proof of K validity',
            'Bootstrap conditions on fixed OOF fits; adaptive development, not professional independent validation'],
        'sources': sources, 'B00_preserved': True, 'all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan); body = OUT / 'forum_previo.md'
    body.write_text('Se preinscribe un GLM Tweedie conjunto con los mismos efectos principales y categorías de G1-G3. '
        'La necesidad es tratar sus dependencias en un solo objetivo penalizado, frente al pase secuencial heurístico ya medido. '
        'Se mantiene K300: la precisión sobre pérdida sumada será300×Σ√N3/n_positivo del entrenamiento. '
        'La codificación completa por categoría es simétrica y los cuatro interceptos año/negocio quedan libres solo en entrenamiento; '
        'no se transfieren y los totales de N3 se conservan sin etiquetas.\n\n'
        'El flujo sintético completo ya comprueba exclusión del retenido, sensibilidad al entrenamiento, Hessiano definido positivo e identidades neutral/desconocida. '
        'Se reutilizan los diez ámbitos, covariables y C0 de la tanda10. No se cambian variables, categorías, K o criterios por los folds adversos. '
        'Se añade un veto de no empeorar la etapa G correspondiente.\n\n'
        'Presupuesto:20GLM (los cinco de género de motor se comparten),80normalizadores de evaluación, cero C0/fuente, precios de test o envíos. '
        'Receta congelada: ' + rel(PLAN) + '.2024 abierto como desarrollo, B00/F2/C1 y alternativas preservados.\n', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA11-PREVIO', '--asunto',
        'GLM conjunto de efectos principales, mismas variables y contracción equivalente K300', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'real_GLM_budget': 20, 'new_C0_fits': 0, 'submissions': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, value in plan['sources'].items(): assert sha(ROOT / path) == value, path
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    p = pd.read_parquet(b.CV / 'oof_2023_2024.parquet')
    for name in NAMES: p[name] = p.N3.to_numpy(float)
    fits = 0; normalizers_count = 0; lookup = pd.Series(p.index.to_numpy(), index=p.row_id)
    with threadpool_limits(limits=2):
        for line in FAMILIES:
            cov = pd.read_parquet(b.OUT / f'covariates_{line}.parquet').set_index('row_id')
            for held in range(5):
                f = pd.read_parquet(b.b.OUT / f'inputs_{line}_fold{held}.parquet')
                for col in ['gender', 'works_from_home', 'marketing_segment']: f[col] = cov.loc[f.row_id, col].to_numpy()
                valid = f.loc[f.fold.eq(held)]; outputs = {}; norms = {}
                for family, variables in FAMILIES[line].items():
                    print(json.dumps({'event': 'GLM_started', 'line': line, 'fold': held, 'family': family}), flush=True)
                    a = fit_scope(f, held, line, family, variables, checkpoint=OUT / f'solver_{line}_fold{held}_{family}.json'); fits += 1
                    dump(OUT / f'model_{line}_fold{held}_{family}.json', a)
                    outputs[family], norms[family] = apply(valid, valid.base_N3.to_numpy(float), a); normalizers_count += len(norms[family])
                    print(json.dumps({'event': 'GLM_completed', 'line': line, 'fold': held, 'family': family, 'fits': fits,
                        'max_gradient': a['max_abs_gradient']}), flush=True)
                for name in NAMES:
                    values = outputs[name if name in outputs else 'J1']; p.loc[lookup.loc[valid.row_id].to_numpy(), name] = values
                dump(OUT / f'normalizers_{line}_fold{held}.json', norms)
    assert fits == 20 and normalizers_count == 80 and len(p) == 109296 and p.row_id.is_unique
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = b.b.b.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - b.b.b.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['N3', *NAMES]}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'scored_validation_pending', 'scores': scores,
        'new_joint_GLM_fits': fits, 'held_prediction_only_normalizers': normalizers_count,
        'new_C0_fits': 0, 'new_source_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, '2024_open': True, 'goal_achieved': False})
    print(json.dumps({'scores': scores, 'new_GLM_fits': fits, 'new_C0_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['preflight', 'register', 'run']); args = parser.parse_args()
    try: {'preflight': preflight, 'register': register, 'run': run}[args.mode]()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc), 'preserve_solver_checkpoints_and_completed_models': True})
        raise
