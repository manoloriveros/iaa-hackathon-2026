"""Calibración de pendiente aprendida dentro del fold, sin volver a estimar C0."""
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
spec = importlib.util.spec_from_file_location('base2', R / 'herramientas/mision017_fase2_tanda2.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
import numpy as np
import pandas as pd
from scipy import optimize
from threadpoolctl import threadpool_limits

OUT = R / 'privado/semana2/mision017_fase2/tanda6_pendiente_20261025_v1'
PLAN = R / 'registro/semana2_mision017_fase2_tanda6_plan_v1.json'
sha = b.sha; dump = b.dump; read = b.read; rel = b.rel
now = lambda: datetime.now(timezone.utc).isoformat()
ALPHA = 1.

def rebuild_scope(f, artifact, held):
    assert b.digest(artifact) == read(b.OUT / f'learning_{f.line.iloc[0]}_fold{held}.json')['training_signature']
    train = f.fold.ne(held).to_numpy()
    assert sorted(f.loc[train, 'row_id']) == artifact['C0']['fit_row_ids']
    assert not set(f.loc[train, 'group_id']) & set(f.loc[~train, 'group_id'])
    for key in ['customer_id', 'address_id']:
        assert not set(f.loc[train, key]) & set(f.loc[~train, key])
    c0 = artifact['C0']
    q = sum(weight * b.v.average_completion(f, c0['curves'][peril], 'cost', 1.) for peril, weight in c0['mixture'].items())
    e = f.exposure.to_numpy(float) * q
    m = f.annual_raw_T2b.to_numpy(float) * e
    for shape in artifact['shape']:
        m = b.shape_apply(f, m, shape)
    m *= np.array([artifact['cellshape'][str(int(nb))] for nb in f.new_business])
    assert np.isfinite(m).all() and (m > 0).all() and (e > 0).all()
    return m, e

def train_design(f, separate):
    nb = f.new_business.to_numpy(dtype=int)
    risk = np.log(f.base_N3.to_numpy(float) / f.e_cost_scope.to_numpy(float))
    weight = f.base_N3.to_numpy(float)
    centers = {str(k): float(np.average(risk[nb == k], weights=weight[nb == k])) for k in [0, 1]}
    centered = risk - np.array([centers[str(k)] for k in nb])
    scale = float(np.sqrt(np.average(centered ** 2, weights=weight)))
    assert scale > 1e-6
    x = centered / scale
    slopes = np.column_stack([x * (nb == k) for k in [0, 1]]) if separate else x[:, None]
    nuisance_keys = [f'{year}|{k}' for year in [2023, 2024] for k in [0, 1]]
    keys = f.year.astype(str).to_numpy() + '|' + nb.astype(str)
    nuisance = np.column_stack([keys == k for k in nuisance_keys]).astype(float)
    assert (nuisance.sum(axis=0) > 0).all()
    return np.column_stack([slopes, nuisance]), centers, scale, nuisance_keys

def fit(f, held, separate):
    # Exclude the protected payload before reading costs or calculating moments.
    tr = f.loc[f.fold.ne(held)].copy()
    assert len(tr) and tr.year.isin([2023, 2024]).all()
    X, centers, scale, nuisance_keys = train_design(tr, separate)
    ns = 2 if separate else 1
    penalty = np.r_[np.ones(ns), np.zeros(4)]
    y = tr.T0.to_numpy(float); offset = tr.base_N3.to_numpy(float)
    assert np.isfinite(y).all() and (y >= 0).all()
    beta = np.zeros(X.shape[1])
    for j in range(4):
        sel = X[:, ns + j].astype(bool)
        k = b.factor(y[sel], offset[sel]); assert k > 0
        beta[ns + j] = np.log(k)
    off = np.log(offset)
    def objective(coef):
        root = np.exp((off + X @ coef) / 2)
        value = 2 * np.mean(root + y / root - 2 * np.sqrt(y)) + .5 * ALPHA * np.dot(penalty * coef, coef)
        gradient = X.T @ ((root - y / root) / len(y)) + ALPHA * penalty * coef
        return float(value), gradient
    result = optimize.minimize(objective, beta, method='L-BFGS-B', jac=True,
        options={'maxiter': 1000, 'gtol': 1e-8, 'ftol': 1e-13, 'maxls': 40})
    value, gradient = objective(result.x)
    assert result.success and np.abs(gradient).max() < 1e-5, str(result.message)
    return {'separate': separate, 'coef': result.x.tolist(), 'centers': centers, 'scale': scale,
        'nuisance_keys': nuisance_keys, 'penalty': penalty.tolist(), 'alpha': ALPHA,
        'objective': value, 'iterations': int(result.nit), 'max_abs_gradient': float(np.abs(gradient).max()),
        'training_rows': len(tr), 'training_row_ids_digest': b.digest(sorted(tr.row_id)),
        'training_groups_digest': b.digest(sorted(set(tr.group_id))), 'held_fold': int(held),
        'transferred': 'Only slope deviations; year/business intercepts remain source-fit nuisance',
        'raw_logrisk_slope_by_business': {str(k): float(1 + result.x[k if separate else 0] / scale) for k in [0, 1]}}

def apply(f, artifact, strength):
    nb = f.new_business.to_numpy(dtype=int)
    risk = np.log(f.base_N3.to_numpy(float) / f.e_cost_scope.to_numpy(float))
    x = (risk - np.array([artifact['centers'][str(k)] for k in nb])) / artifact['scale']
    coef = np.array([artifact['coef'][int(k) if artifact['separate'] else 0] for k in nb])
    factor = np.exp(strength * coef * x)
    base = f.base_N3.to_numpy(float); out = base.copy(); normalizers = {}
    for k in [0, 1]:
        mask = nb == k; assert mask.any()
        norm = float(np.sum(base[mask] * factor[mask]) / np.sum(base[mask]))
        out[mask] = base[mask] * factor[mask] / norm; normalizers[str(k)] = norm
        assert np.isclose(out[mask].sum(), base[mask].sum(), rtol=1e-12, atol=1e-6)
    assert np.isfinite(out).all() and (out > 0).all()
    return out, normalizers

def synthetic():
    rng = np.random.default_rng(2026102507); n = 1000
    f = pd.DataFrame({'row_id': ['fake_' + str(i) for i in range(n)], 'group_id': ['g_' + str(i) for i in range(n)],
        'fold': np.arange(n) % 5, 'new_business': (np.arange(n) // 2) % 2, 'year': np.where(np.arange(n) % 2, 2023, 2024),
        'e_cost_scope': rng.uniform(.15, 1., n), 'T0': rng.gamma(2, 100, n) * (rng.random(n) < .4)})
    f['base_N3'] = f.e_cost_scope * np.exp(rng.normal(5, .5, n))
    results = []
    for separate in [False, True]:
        a = fit(f, 0, separate)
        poisoned = f.copy(); poisoned.loc[poisoned.fold.eq(0), 'T0'] = -1e30
        z = fit(poisoned, 0, separate); assert b.digest(a) == b.digest(z)
        shifted = f.copy(); shifted.loc[shifted.fold.ne(0), 'T0'] *= 2
        other = fit(shifted, 0, separate); assert b.digest(a) != b.digest(other)
        valid = f.loc[f.fold.eq(0)]; pred, norm = apply(valid, a, 1.)
        bad, norm2 = apply(valid.assign(T0=-1e30), a, 1.)
        assert np.array_equal(pred, bad) and norm == norm2
        zero = dict(a); zero['coef'] = [0.] * len(a['coef'])
        null, _ = apply(valid, zero, 1.); assert np.array_equal(null, valid.base_N3.to_numpy(float))
        results.append({'separate': separate, 'held_payload_invariant_learning': True, 'training_payload_changes_learning': True,
            'predictions_label_invariant': True, 'zero_slope_reproduces_base': True, 'cell_totals_preserved': True})
    dump(OUT / 'synthetic.json', {'pass': True, 'checks': results, 'synthetic_price_fits': 6, 'contest_price_fits': 0})

def preflight():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    with threadpool_limits(limits=2): synthetic()
    target = pd.read_parquet(b.BASE / 'target_T0_and_stresses.parquet', filters=[('is_test', '=', False)])
    parts = pd.read_parquet(b.BASE / 'partitions.parquet', filters=[('is_test', '=', False)])
    old = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet').set_index('row_id')
    sources = [Path(__file__), Path(b.__file__), R / 'src/semana2/variables_ultimo.py',
        b.BASE / 'target_T0_and_stresses.parquet', b.BASE / 'partitions.parquet', b.OUT / 'oof_2023_2024.parquet']
    receipts = []
    for line in b.v.LINES:
        paths = [b.PARENT / f'features_{line}.parquet', b.PARENT / f'raw_rates_{line}.parquet']; sources += paths
        f = pd.read_parquet(paths[0]).merge(pd.read_parquet(paths[1])[['row_id', 'annual_raw_T2b']], on='row_id', validate='one_to_one')
        f = f.merge(parts.loc[parts.line.eq(line), ['row_id', 'group_id', 'fold']], on='row_id', validate='one_to_one')
        f = f.merge(target.loc[target.line.eq(line), ['row_id', 'T0', 'reserve']], on='row_id', validate='one_to_one')
        f['line'] = line; f['is_test'] = False
        f['exposure'] = target.loc[target.line.eq(line)].set_index('row_id').exposure.reindex(f.row_id).to_numpy(float)
        for held in range(5):
            parent = b.OUT / f'learning_{line}_fold{held}.json'; sources.append(parent)
            a = read(parent)['artifact']; price, exposure = rebuild_scope(f, a, held)
            mask = f.fold.eq(held).to_numpy(); actual = old.loc[f.loc[mask, 'row_id']]
            assert np.array_equal(price[mask], actual.N3.to_numpy(float))
            assert np.array_equal(exposure[mask], actual.e_cost.to_numpy(float))
            inputs = f[['row_id', 'line', 'year', 'group_id', 'fold', 'new_business', 'exposure', 'T0', 'reserve']].copy()
            inputs['base_N3'] = price; inputs['e_cost_scope'] = exposure
            output = OUT / f'inputs_{line}_fold{held}.parquet'; inputs.to_parquet(output, index=False)
            receipts.append({'line': line, 'held_fold': held, 'rows': len(f), 'training_rows': int((~mask).sum()),
                'held_rows': int(mask.sum()), 'held_price_and_completion_bit_exact': True,
                'groups_customers_addresses_disjoint': True, 'original_training_membership_exact': True,
                'parent': rel(parent), 'parent_sha256': sha(parent), 'input': rel(output), 'input_sha256': sha(output)})
    dump(OUT / 'preflight.json', {'author': 'Codex', 'utc': now(), 'sources': {rel(p): sha(p) for p in sources},
        'scopes': receipts, 'new_price_fits': 0, 'new_C0_fits': 0, 'new_scores': 0,
        'original_baseline_scope_reproduction_only': True, '2024_is_adaptive_development': True})
    print(json.dumps({'preflight_scopes': len(receipts), 'replay_bit_exact': True, 'new_price_fits': 0, 'new_C0_fits': 0}))

def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = read(OUT / 'preflight.json'); assert len(pre['scopes']) == 15 and read(OUT / 'synthetic.json')['pass']
    sources = dict(pre['sources']); sources[rel(OUT / 'preflight.json')] = sha(OUT / 'preflight.json')
    for s in pre['scopes']: sources[s['input']] = s['input_sha256']
    for path, digest in sources.items(): assert sha(ROOT / path) == digest
    plan = {'id': 'S2-MISION017-FASE2-TANDA6-PENDIENTE-v1', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'Pooled 2023–2024 may estimate a regularized risk-calibration slope more stably than single-year shape curves. Learn it only on outer training groups, transfer slopes alone, and preserve held portfolio cell totals; no held optimal level.',
        'reference': 'N3 research comparator from frozen T2b; not a full replay of submitted F2',
        'configuration': {'objective': 'half Tweedie deviance power1.5, period observed net cost',
            'offset': 'log training-scope N3 price, including frozen scope C0 and credibility',
            'predictor': 'log(N3/e_cost) centered within business using training N3 weights, divided by pooled weighted training SD',
            'nuisance': 'four free year(2023/2024) × new_business intercepts; never transferred',
            'alpha_slope_deviation': ALPHA, 'normalization': 'Known held portfolio input/prediction-only normalizer preserves N3 sum within line × new_business',
            'optimizer': {'method': 'L-BFGS-B', 'maxiter': 1000, 'gtol': 1e-8, 'ftol': 1e-13, 'maxls': 40},
            'no_clipping_no_rebinning_no_target_changes': True},
        'models': {'T1': 'One common slope deviation per line; strength1',
            'T2': 'Separate new/renewal slope deviations per line; strength1', 'T3': 'Same T2 fit, fixed half strength'},
        'criterion': {'delta_min': .002, 'lower95_gt': 0., 'positive_folds_min': 4,
            'min_cell_delta_full_null': -.001, 'post31_nonnegative': True, 'both_years_nonnegative': True},
        'bootstrap': {'replicates': 2000, 'seed': 2026102507, 'unit': 'saved connected component', 'quantiles': [.025, .975]},
        'budget': {'price_GLM_fits': 30, 'C0_fits': 0, 'new_parent_model_fits': 0, 'portfolio_covariate_normalizers': 90,
            'source_models_new': 0, 'intercepts_part_of_GLM_not_separate_models': 120, 'submissions': 0},
        'limits': ['2024 is adaptive development, source T2b includes developed2024: start2025 information scope, not prospective2024 validation',
            'Held normalization uses known portfolio covariates/predictions, not online pricing confirmation',
            'Source/old C0/master snapshot and case-reserve uncertainty not fully identified',
            'Adaptive exploratory search, no professional independent approval; full historical A1/F2 comparison still missing'],
        'sources': sources, 'B00_preserved': True, 'all_alternatives_preserved': True, 'no_automatic_submission': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Se registran dos GLM de pendiente de riesgo y una contracción fija de la segunda receta, con el mismo N3 como referencia de investigación. '
        'Las curvas anteriores con niveles óptimos retenidos no prueban este aprendizaje fuera de componente.\n\n'
        'El preflight reprodujo exactamente los precios y la completitud retenidos de los 15 ámbitos, y verificó que clientes, direcciones y componentes no se mezclan. '
        'Se reutilizan C0 y credibilidad sin ajustar. Los controles sintéticos recorrieron aprendizaje, transferencia y normalización: cambiar etiquetas retenidas no cambia parámetros; cambiar entrenamiento sí.\n\n'
        'Cada GLM aprende desviaciones de pendiente con penalización 1 y cuatro interceptos año/negocio de control. Solo se transfiere la pendiente. '
        'El factor de cartera usa predicciones y preserva los totales por ramo/negocio, sin etiquetas retenidas. '
        'T1 tiene una pendiente por ramo, T2 dos por tipo de negocio, T3 usa la mitad de T2 sin otro ajuste.\n\n'
        'Se mantienen los criterios: diferencia mínima de D² 0,002, límite inferior del IC 95 % positivo, cuatro folds positivos, '
        'sin deterioro material por celda, ambos años no negativos y sensibilidad a los 31 grupos favorables no negativa. '
        'Presupuesto: 30 GLM, cero curvas C0, cero modelos fuente nuevos y cero envíos. '
        '2024 está abierto como desarrollo adaptativo. Esto no acredita una comparación íntegra con F2 ni una validación profesional independiente. '
        'Plan y fuentes: ' + rel(PLAN) + '.\n', encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA6-PREVIO', '--asunto',
        'Pendiente de riesgo aprendida dentro de cada fold: GLM sencillo, sin reestimar C0', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(p.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'real_GLM_fits': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, digest in plan['sources'].items(): assert sha(ROOT / path) == digest, path
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    outputs = []; fits = 0
    with threadpool_limits(limits=2):
        for scope in read(OUT / 'preflight.json')['scopes']:
            f = pd.read_parquet(ROOT / scope['input']); held = scope['held_fold']; line = scope['line']
            valid = f.loc[f.fold.eq(held)].copy(); models = {}
            for separate, name in [(False, 'global'), (True, 'business')]:
                artifact = fit(f, held, separate); models[name] = artifact; fits += 1
                dump(OUT / f'{name}_{line}_fold{held}.json', artifact)
            normalizers = {}
            for name, family, strength in [('T1', 'global', 1.), ('T2', 'business', 1.), ('T3', 'business', .5)]:
                pred, norm = apply(valid, models[family], strength); valid[name] = pred; normalizers[name] = norm
            dump(OUT / f'normalizers_{line}_fold{held}.json', normalizers)
            outputs.append(valid); print(json.dumps({'line': line, 'fold': held,
                'slopes': {k: a['raw_logrisk_slope_by_business'] for k, a in models.items()}, 'fits_total': fits}), flush=True)
    p = pd.concat(outputs, ignore_index=True); assert len(p) == 109296 and p.row_id.is_unique and fits == 30
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = b.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - b.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['base_N3', 'T1', 'T2', 'T3']}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'prices_scored_validation_pending',
        'scores': scores, 'price_GLM_fits': fits, 'new_C0_fits': 0, 'new_parent_model_fits': 0,
        'covariate_only_normalizers': 90, 'new_submissions': 0, 'B00_preserved': True, 'goal_achieved': False})
    print(json.dumps({'scores': scores, 'price_GLM_fits': fits, 'C0_refits': 0, 'submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['preflight', 'register', 'run']); args = parser.parse_args()
    try:
        {'preflight': preflight, 'register': register, 'run': run}[args.mode]()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc)})
        raise
