"""Adaptación estándar de hojas T2b, con topología fija y offset N3 del ámbito."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import inspect
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

scope = load('scope9', R / 'herramientas/mision017_fase2_tanda6_pendiente.py')
matrix = load('matrix9', R / 'herramientas/mision017_fase2_tanda4_marketing.py')
import numpy as np
import pandas as pd
import lightgbm as lgb
from threadpoolctl import threadpool_limits

BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda9_hojas_20261026_v3'
PLAN = R / 'registro/semana2_mision017_fase2_tanda9_plan_v3.json'
PARENT = matrix.PARENT; CV = matrix.CV
sha = matrix.sha; read = matrix.read; dump = matrix.dump; rel = matrix.rel
now = lambda: datetime.now(timezone.utc).isoformat()
DECAY = .9
NAMES = [('L1', 1.), ('L2', .5), ('L3', .25)]

def topology(model):
    def node(n):
        if 'leaf_index' in n: return {'leaf_index': n['leaf_index']}
        if 'split_index' not in n: return {'leaf_index': 0}
        return {**{k: n[k] for k in ['split_index', 'split_feature', 'threshold', 'decision_type', 'default_left', 'missing_type']},
                'left_child': node(n['left_child']), 'right_child': node(n['right_child'])}
    return {'features': model.feature_name(), 'categorical': model.pandas_categorical,
            'trees': [node(t['tree_structure']) for t in model.dump_model()['tree_info']]}

def digest(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def independent_refit(model, X, y, init_score, decay):
    """Reproduce v4.6.0 RefitTree y FitByExistingTree, sin llamar a fit/refit."""
    d = model.dump_model(); leaf = model.predict(X, pred_leaf=True, num_threads=2)
    # LightGBM stores labels and per-row gradients/Hessians as float32.
    label = np.asarray(y, dtype=np.float32).astype(float); score = np.asarray(init_score, float).copy(); outputs = []
    l2 = float(model.params.get('lambda_l2', 0)); l1 = float(model.params.get('lambda_l1', 0))
    assert l1 == 0 and float(model.params.get('path_smooth', 0)) == 0 and float(model.params.get('max_delta_step', 0)) == 0
    for j, tree in enumerate(d['tree_info']):
        root = np.exp(score / 2); g = np.asarray(root - label / root, np.float32).astype(float)
        h = np.asarray(.5 * (root + label / root), np.float32).astype(float)
        n = tree['num_leaves']; sg = np.bincount(leaf[:, j], weights=g, minlength=n)
        sh = np.bincount(leaf[:, j], weights=h, minlength=n)
        old = np.array([model.get_leaf_output(j, k) for k in range(n)])
        new = -sg / (sh + l2 + 1e-15) * tree['shrinkage']
        mixed = decay * old + (1 - decay) * new
        score += mixed[leaf[:, j]]; outputs.append(mixed)
    return outputs, score

def refit_scope(parent, X, f, held, raw, decay=DECAY):
    train = f.fold.ne(held).to_numpy(); tr = f.loc[train]
    assert train.any() and (~train).any() and not set(tr.group_id).intersection(f.loc[~train, 'group_id'])
    # Frozen N3 = a_i * exp(parent_raw_i). No protected costs are read.
    init = np.log(tr.base_N3.to_numpy(float)) - raw[train]
    model = parent.refit(X.loc[train], tr.T0.to_numpy(float), init_score=init, decay_rate=decay,
        validate_features=True, dataset_params={'num_threads': 2, 'verbosity': -1}, num_threads=2)
    assert topology(model) == topology(parent)
    trace = {'held_fold': int(held), 'training_rows': int(train.sum()), 'training_groups': len(set(tr.group_id)),
        'training_row_ids_digest': digest(sorted(tr.row_id)), 'training_groups_digest': digest(sorted(set(tr.group_id))),
        'training_label_digest': digest(tr.T0.to_numpy(float).tolist()), 'init_score_digest': digest(init.tolist()),
        'topology_digest': digest(topology(parent)), 'source_tree_count': parent.num_trees(),
        'fitted_tree_count': model.num_trees(), 'new_split_count': 0, 'decay_rate': decay,
        'objective': 'Tweedie1.5 observed total cost with init_score=log(frozen_N3)-source_raw',
        'protected_labels_accessed_for_fit': False, 'new_refit_calls': 1, 'new_C0_fits': 0}
    return model, trace

def apply(f, base, raw_delta, strength):
    factor = np.exp(strength * raw_delta); out = base.copy(); normalizers = {}
    assert np.isfinite(factor).all() and (factor > 0).all()
    for year in sorted(f.year.unique()):
        for nb in [0, 1]:
            mask = f.year.eq(year).to_numpy() & f.new_business.to_numpy(dtype=int).__eq__(nb); assert mask.any()
            norm = float(np.sum(base[mask] * factor[mask]) / base[mask].sum())
            out[mask] = base[mask] * factor[mask] / norm; normalizers[f'{int(year)}|{nb}'] = norm
            assert np.isclose(out[mask].sum(), base[mask].sum(), rtol=1e-12, atol=1e-6)
    return out, normalizers

def synthetic():
    rng = np.random.default_rng(2026102603); n = 1200
    X = pd.DataFrame({'x': rng.normal(size=n), 'category': pd.Categorical(rng.choice(['a', 'b', 'c'], n))})
    e = rng.uniform(.1, 1, n); y = rng.gamma(2, 60, n) * (rng.random(n) < .35)
    f = pd.DataFrame({'row_id': ['synthetic' + str(i) for i in range(n)], 'fold': np.arange(n) % 5,
        'group_id': ['g' + str(i) for i in range(n)], 'year': 2023 + (np.arange(n) // 2) % 2,
        'new_business': (np.arange(n) // 4) % 2, 'T0': y})
    p = dict(objective='tweedie', tweedie_variance_power=1.5, num_leaves=7, min_data_in_leaf=30,
        learning_rate=.05, lambda_l2=10., num_threads=2, verbosity=-1, seed=2026102603)
    parent = lgb.train(p, lgb.Dataset(X, label=y, init_score=np.log(e)), num_boost_round=12)
    raw = parent.predict(X, raw_score=True, num_threads=2); f['base_N3'] = e * np.exp(raw)
    before = parent.model_to_string(); fitted, trace = refit_scope(parent, X, f, 0, raw)
    assert parent.model_to_string() == before
    mutated = f.copy(); mutated.loc[mutated.fold.eq(0), 'T0'] = -1e30
    check, t2 = refit_scope(parent, X, mutated, 0, raw)
    assert fitted.model_to_string() == check.model_to_string() and trace == t2
    mutated.loc[mutated.fold.ne(0), 'T0'] *= 2
    changed, _ = refit_scope(parent, X, mutated, 0, raw)
    assert fitted.model_to_string() != changed.model_to_string()
    identity, _ = refit_scope(parent, X, f, 0, raw, decay=1.)
    assert np.array_equal(identity.predict(X, raw_score=True), raw)
    tr = f.fold.ne(0).to_numpy(); init = np.log(f.loc[tr, 'base_N3']) - raw[tr]
    outputs, _ = independent_refit(parent, X.loc[tr], y[tr], init, DECAY)
    error = max(abs(fitted.get_leaf_output(j, k) - value) for j, row in enumerate(outputs) for k, value in enumerate(row))
    assert error < 2e-6, str(error)
    valid = f.loc[~tr]; delta = fitted.predict(X.loc[~tr], raw_score=True) - raw[~tr]
    base = valid.base_N3.to_numpy(float); prediction, norm = apply(valid, base, delta, 1.)
    poison, n2 = apply(valid.assign(T0=-1e30), base, delta, 1.)
    zero, _ = apply(valid, base, np.zeros(len(base)), 1.)
    assert np.array_equal(poison, prediction) and norm == n2 and np.array_equal(zero, base)
    # Same Tweedie loss expressed as period costs or annual rates, including zero claims.
    rate = np.exp(raw); unit = matrix.unit
    assert np.allclose(unit(y, e * rate), np.sqrt(e) * unit(y / e, rate), rtol=1e-12, atol=1e-10)
    dump(OUT / 'synthetic.json', {'pass': True, 'synthetic_source_train_calls': 1, 'synthetic_refit_calls': 4,
        'real_fit_calls': 0, 'held_payload_learning_invariant': True, 'training_change_changes_learning': True,
        'parent_unchanged': True, 'topology_unchanged': True, 'decay1_prediction_bit_exact': True,
        'independent_Cpp_leaf_replay_max_abs_error': float(error), 'period_rate_loss_equivalence': True,
        'zero_overlay_identity': True, 'prediction_label_invariant': True, 'year_business_totals_preserved': True})

def preflight():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    with threadpool_limits(limits=2): synthetic()
    history = ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023'
    history_paths = [history / 'codigo/transfer2.py', history / 'codigo/e25_severidad.py',
        history / 'evolucion/EVOLUCION.md', history / 'evolucion/foro_cuerpo_e25_e26.md']
    paths = [Path(__file__), Path(matrix.__file__), scope.OUT / 'preflight.json', scope.OUT / 'validation_v1/report.json',
        CV / 'oof_2023_2024.parquet', BASE / 'tanda8_poisson_20261026_v2/validation_v1/report.json',
        R / 'registro/semana2_politica_desarrollo2024_v2.json', *history_paths]
    receipts = []
    for line in ['motor', 'buildings', 'contents']:
        source = PARENT / f'modelos/prod/T2b_{line}.txt'; feature = PARENT / f'features_{line}.parquet'
        rates = PARENT / f'raw_rates_{line}.parquet'; paths += [source, feature, rates]
        model = lgb.Booster(model_file=str(source)); features = pd.read_parquet(feature)
        X = matrix.source_matrix(features, model); raw = model.predict(X, raw_score=True, num_threads=2)
        old = pd.read_parquet(rates, columns=['row_id', 'annual_raw_T2b'])
        assert np.array_equal(features.row_id, old.row_id)
        assert np.allclose(np.exp(raw), old.annual_raw_T2b, rtol=2e-14, atol=1e-9)
        output = OUT / f'parent_raw_{line}.parquet'
        pd.DataFrame({'row_id': features.row_id, 'raw': raw}).to_parquet(output, index=False); paths.append(output)
        for held in range(5):
            inputs = scope.OUT / f'inputs_{line}_fold{held}.parquet'; parent = CV / f'learning_{line}_fold{held}.json'
            paths += [inputs, parent]; f = pd.read_parquet(inputs)
            assert np.array_equal(f.row_id, features.row_id) and f.year.isin([2023, 2024]).all()
            a = read(parent)['artifact']['C0']; train = f.fold.ne(held)
            assert sorted(f.loc[train, 'row_id']) == a['fit_row_ids']
            assert not set(f.loc[train, 'group_id']).intersection(f.loc[~train, 'group_id'])
            assert np.isfinite(f.base_N3).all() and f.base_N3.gt(0).all() and f.T0.ge(0).all()
            receipts.append({'line': line, 'held': held, 'scope_input': rel(inputs), 'scope_input_sha256': sha(inputs),
                'parent_C0': rel(parent), 'parent_C0_sha256': sha(parent), 'rows': len(f), 'training_rows': int(train.sum()),
                'source_tree_count': model.num_trees(), 'source_topology_digest': digest(topology(model)),
                'frozen_N3_and_C0_scope_reused': True, 'membership_and_group_exclusion_pass': True})
    dump(OUT / 'preflight.json', {'author': 'Codex', 'utc': now(), 'sources': {rel(p): sha(p) for p in paths},
        'scopes': receipts, 'LGBM_version': lgb.__version__, 'real_refits': 0, 'new_C0_fits': 0,
        'novelty': 'Frozen source-tree leaf refit only; not new target trees (T1), linear risk slope (T6), weather overlay (T7/T8), FS/FSt severity grid (E25) or source-mixture weighting (E26)',
        'public_technical_sources': ['https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html#lightgbm.Booster.refit',
            'https://raw.githubusercontent.com/microsoft/LightGBM/v4.6.0/src/boosting/gbdt.cpp',
            'https://raw.githubusercontent.com/microsoft/LightGBM/v4.6.0/src/treelearner/serial_tree_learner.cpp'],
        'local_refit_python_source_sha256': hashlib.sha256(inspect.getsource(lgb.Booster.refit).encode()).hexdigest()})
    print(json.dumps({'preflight_scopes': len(receipts), 'synthetic_pass': True, 'real_refits': 0, 'new_C0_fits': 0}))

def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = read(OUT / 'preflight.json'); assert read(OUT / 'synthetic.json')['pass'] and len(pre['scopes']) == 15
    sources = {**pre['sources'], rel(OUT / 'preflight.json'): sha(OUT / 'preflight.json'),
        rel(OUT / 'synthetic.json'): sha(OUT / 'synthetic.json')}
    for path, value in sources.items(): assert sha(ROOT / path) == value, path
    criterion = read(R / 'registro/semana2_mision017_fase2_tanda8_plan_v1.json')['criterion']
    plan = {'id': 'S2-MISION017-FASE2-TANDA9-HOJAS-v3', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'Fixed source-tree partitions can express market-specific nonlinear corrections missed by the failed target linear slopes without estimating new splits from sparse emerging claims. Retain90percent each old leaf via standard LGBM.refit, with frozen outer-training N3 offsets.',
        'reference': 'N3 research comparator, not complete C1/F2', 'configuration': {'LGBM_version': lgb.__version__,
            'source': 'Frozen T2b developed2021–2024, original source authorship Claude', 'tree_structure': 'unchanged all features, splits, leaves and iteration count',
            'data': 'emerging2023–2024, existing global component folds', 'objective': 'Tweedie1.5 period observed net total cost',
            'init_score': 'log(frozen training-scope N3_i)-parent_raw_i, including existing exposure and target calibration',
            'decay_rate': DECAY, 'regularization': 'All existing source objective/leaf penalties preserved, no new hyperparameter search',
            'new_features': [], 'new_splits': 0, 'application': 'N3 times exp(strength*(new_raw-old_raw))',
            'strengths_no_further_refit': dict(NAMES), 'normalization': 'Input/prediction-only per line/year/business, preserving N3 totals',
            'no_clipping': True}, 'criterion': criterion,
        'bootstrap': {'replicates': 2000, 'seed': 2026102603, 'unit': 'saved connected component'},
        'budget': {'real_leaf_refit_calls': 15, 'new_source_fits': 0, 'new_C0_fits': 0,
            'covariate_only_normalizers': 180, 'new_test_prices': 0, 'submissions': 0},
        'validation': ['Independent v4.6.0 sequential gradient/Hessian/leaf-output replay for every refit',
            'Frozen topology and source parent hashes, exact replay without fit', 'Held labels invariant in complete synthetic learning flow',
            'Real fit trace reads training labels only and excludes protected groups', 'Same primary criteria and additional vetoes as T8'],
        'limits': ['2024 adaptive development', 'Target calibration source-risk prior is conditional, not independent source validation',
            'Many fixed leaves and limited claim support can still overfit despite90percent shrinkage',
            '2025 weighting primary ESS failed and remains diagnostic only', 'No full correctedA1/F2 historical replay',
            'Case reserves, ultimate tail and master-date availability unresolved', 'No automatic test-price admission or slot use'],
        'sources': sources, 'B00_preserved': True, 'all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan); body = OUT / 'forum_previo.md'
    body.write_text('Se registra una prueba distinta de E25/E26 y de las tandas recientes. Se conservan las particiones y los árboles T2b de Claude; '
        'solo se adaptan sus valores de hoja con LightGBM.refit y decay0.9, sin aprender nuevas divisiones. '
        'La necesidad es contrastar correcciones de mercado no lineales que la pendiente GLM no capturó; la falta de soporte puede hacerla fallar igualmente.\n\n'
        'La respuesta sigue siendo T0 del periodo. El offset es log(N3 del ámbito)-raw del padre, con C0 y calibración ya guardados del entrenamiento exterior. '
        'No se estima otra curva ni se usa el fold retenido para aprender. Se aplican las intensidades1,0.5,0.25 a los mismos15ajustes y se conservan totales por ramo/año/negocio sin etiquetas. '
        'Se mantienen los criterios, controles de influencia y vetos anteriores.\n\n'
        'Antes del registro pasó el flujo sintético: exclusión del retenido, cambio de entrenamiento efectivo, identidad decay1, topología fija, '
        'gradientes/Hessianos y reproducción independiente de hojas conforme al código público de LightGBM4.6.0. '
        'Quedan15refit, cero C0, precios de test o envíos. 2024 abierto como desarrollo, B00/F2/C1 y alternativas conservados. Plan: ' + rel(PLAN) + '.\n', encoding='utf8')
    receipt = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA9-ALINEACION-PREVIO', '--asunto',
        'Adaptación de hojas T2b: topología fija y90porciento del valor fuente conservado', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(receipt.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'refit_budget': 15, 'new_C0_fits': 0, 'submissions': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, value in plan['sources'].items(): assert sha(ROOT / path) == value, path
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    original = pd.read_parquet(CV / 'oof_2023_2024.parquet'); parts = []; refits = 0
    with threadpool_limits(limits=2):
        for line in ['motor', 'buildings', 'contents']:
            model_path = PARENT / f'modelos/prod/T2b_{line}.txt'; parent = lgb.Booster(model_file=str(model_path))
            f = pd.read_parquet(PARENT / f'features_{line}.parquet'); X = matrix.source_matrix(f, parent)
            raw_frame = pd.read_parquet(OUT / f'parent_raw_{line}.parquet'); assert np.array_equal(raw_frame.row_id, f.row_id)
            raw = raw_frame.raw.to_numpy(float); before = parent.model_to_string()
            old_line = original.loc[original.line.eq(line)].copy()
            assert old_line.row_id.is_unique and set(old_line.row_id) == set(f.row_id)
            t = old_line.set_index('row_id').loc[f.row_id].reset_index()
            assert np.array_equal(t.row_id, f.row_id)
            for name, _ in NAMES: t[name] = np.nan
            for held in range(5):
                inputs = scope.OUT / f'inputs_{line}_fold{held}.parquet'; inp = pd.read_parquet(inputs)
                assert np.array_equal(inp.row_id, f.row_id)
                print(json.dumps({'event': 'refit_started', 'line': line, 'fold': held}), flush=True)
                fitted, trace = refit_scope(parent, X, inp, held, raw); refits += 1
                assert parent.model_to_string() == before
                path = OUT / f'model_{line}_fold{held}.txt'; fitted.save_model(str(path))
                dump(OUT / f'trace_{line}_fold{held}.json', {**trace, 'scope_input': rel(inputs), 'scope_input_sha256': sha(inputs),
                    'parent_model': rel(model_path), 'parent_model_sha256': sha(model_path), 'output_model_sha256': sha(path)})
                held_mask = inp.fold.eq(held).to_numpy(); valid = t.loc[held_mask]
                new_raw = fitted.predict(X.loc[held_mask], raw_score=True, num_threads=2); delta = new_raw - raw[held_mask]
                norms = {}
                for name, strength in NAMES:
                    prediction, norm = apply(valid, valid.N3.to_numpy(float), delta, strength)
                    t.loc[held_mask, name] = prediction; norms[name] = norm
                dump(OUT / f'normalizers_{line}_fold{held}.json', norms)
                print(json.dumps({'event': 'refit_completed', 'line': line, 'fold': held, 'refits': refits,
                    'raw_delta_quantiles': np.quantile(delta, [0, .01, .5, .99, 1]).tolist()}), flush=True)
            parts.append(t)
    p = pd.concat(parts, ignore_index=True); assert len(p) == 109296 and p.row_id.is_unique and refits == 15
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = matrix.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - matrix.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['N3', *dict(NAMES)]}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'prices_scored_validation_pending', 'scores': scores,
        'new_leaf_refit_calls': 15, 'new_source_fits': 0, 'new_splits': 0, 'new_C0_fits': 0,
        'covariate_only_normalizers': 180, 'new_test_predictions': 0, 'new_submissions': 0, 'B00_preserved': True})
    print(json.dumps({'scores': scores, 'new_leaf_refits': 15, 'new_C0_fits': 0, 'submissions': 0}))


def reuse_preflight():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    previous = BASE / 'tanda9_hojas_20261026_v2'
    pre = read(previous / 'preflight.json')
    assert read(previous / 'synthetic.json')['pass']
    assert not list(previous.glob('trace_*.json')) and not list(previous.glob('model_*.txt'))
    old = pd.read_parquet(CV / 'oof_2023_2024.parquet')
    for line in ['motor', 'buildings', 'contents']:
        keys = pd.read_parquet(PARENT / f'features_{line}.parquet', columns=['row_id'])
        t = old.loc[old.line.eq(line)]
        assert t.row_id.is_unique and set(t.row_id) == set(keys.row_id)
        t = t.set_index('row_id').loc[keys.row_id].reset_index()
        assert np.array_equal(t.row_id, keys.row_id)
        for held in range(5):
            inp = pd.read_parquet(scope.OUT / f'inputs_{line}_fold{held}.parquet')
            assert np.array_equal(inp.row_id, keys.row_id)
            mask = inp.fold.eq(held).to_numpy()
            assert np.array_equal(inp.base_N3.to_numpy(float)[mask], t.N3.to_numpy(float)[mask])
        source = previous / f'parent_raw_{line}.parquet'; target = OUT / source.name
        target.write_bytes(source.read_bytes()); assert sha(source) == sha(target)
    (OUT / 'synthetic.json').write_bytes((previous / 'synthetic.json').read_bytes())
    sources = {**pre['sources'], rel(Path(__file__)): sha(Path(__file__)),
        rel(previous / 'preflight.json'): sha(previous / 'preflight.json'),
        rel(R / 'registro/semana2_mision017_fase2_tanda9_plan_v2.json'): sha(R / 'registro/semana2_mision017_fase2_tanda9_plan_v2.json')}
    sources.update({rel(OUT / p.name): sha(OUT / p.name) for p in OUT.glob('parent_raw_*.parquet')})
    dump(OUT / 'preflight.json', {**pre, 'utc': now(), 'sources': sources,
        'previous_preflight_reused_no_refit_or_reinference': True,
        'integration_fix': 'Explicit one-to-one row_id alignment between feature-order scope inputs and fold-order OOF; all15 held N3 arrays bit-exact after alignment',
        'prior_registered_run_terminal': {'exit_code': 1, 'real_refit_calls': 0, 'before_first_fit': True},
        'new_synthetic_fits': 0, 'new_model_inferences': 0})
    print(json.dumps({'preflight_scopes': 15, 'synthetic_receipt_reused': True, 'N3_held_alignment_bit_exact': True,
        'real_refits': 0, 'new_synthetic_fits': 0, 'new_C0_fits': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['preflight', 'register', 'run']); args = parser.parse_args()
    try: {'preflight': reuse_preflight, 'register': register, 'run': run}[args.mode]()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc), 'preserve_completed_models_no_blind_retry': True})
        raise
