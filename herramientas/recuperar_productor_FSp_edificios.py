"""Recuperación acotada del productor FSp faltante; rondas existentes, sin búsqueda."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
MATRIX = BASE / 'FSp_edificios_matrices_20261026_v1'
OUT = BASE / 'FSp_edificios_productor_20261026_v1'
PLAN = R / 'registro/semana2_mision017_FSp_edificios_recuperacion_plan_v1.json'
ORIGINAL = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025/exp26_20261026/ml2'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_fsp_recovery', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd
import lightgbm as lgb

PF = dict(objective='poisson', learning_rate=.08, num_leaves=31, min_data_in_leaf=1000,
          feature_fraction=.8, bagging_fraction=.8, bagging_freq=1, lambda_l2=10.,
          max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261026)
PS = dict(objective='gamma', learning_rate=.05, num_leaves=15, min_data_in_leaf=200,
          feature_fraction=.8, bagging_fraction=.8, bagging_freq=1, lambda_l2=10.,
          max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261026)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def sources():
    paths = [Path(__file__), MATRIX / 'report.json',
             BASE / 'recuentos_fuente2024_v1/counts_buildings.parquet',
             BASE / 'FSp_edificios_recuperacion_entradas_20261026_v1/report.json',
             ORIGINAL / 'codigo/fsp_light.py', ORIGINAL / 'codigo/fsp_light_prod.py',
             ORIGINAL / 'trabajo/pred/fsp/buildings_meta.json',
             ORIGINAL / 'trabajo/pred/fsp/buildings_prod_meta.json']
    paths += [MATRIX / f'{kind}_{market}_{phase}.parquet'
              for phase in ['dev', 'prod'] for market in ['source', 'target'] for kind in ['rows', 'matrix']]
    return {w.rel(p): w.sha(p) for p in paths}


def register():
    assert not PLAN.exists() and not OUT.exists()
    matrix = w.read(MATRIX / 'report.json')
    assert matrix['source_raw_precision_restored_and_forward32_parity_passed']
    assert matrix['historical_target64_parity_passed'] and matrix['new_fits'] == 0
    OUT.mkdir(parents=True)
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
            'id': 'S2-MISION017-FSp-BUILDINGS-RECOVERY-V1',
            'hypothesis': 'The missing per-row buildings producer prevents evaluating the full renewal alternative. Restore that existing Poisson/Gamma component with fixed source-selected rounds before adding complexity or choosing a new blend.',
            'necessity': 'Original received producer did not persist Boosters; available F4c donor has buildings weight0. Source counts/marks/offsets and full-precision matrices now reconciled. Do not repeat completed model comparisons or tune from public score.',
            'reconstruction_not_exact_original_tree_replay': True,
            'comparator_for_later_preregistered_predictive_comparison': 'F3c unchanged including new business, B00 preserved; no candidate promotion in this recovery',
            'source_market': 'developed', 'source_dev_years': [2021, 2022, 2023], 'source_prod_years': [2021, 2022, 2023, 2024],
            'target_covariate_years': [2023, 2024, 2025], 'no_target_response_loaded': True,
            'dev_climate': {'source': [2021, 2022, 2023], 'target': [2023]},
            'prod_climate': {'source': [2021, 2022, 2023, 2024], 'target': [2023, 2024]},
            'history_mode': 'historia2, end=min(period_start,2024-12-31); original FSp runtime mode not known',
            'parameters': {'frequency': PF, 'severity': PS},
            'rounds': {phase: w.read(ORIGINAL / ('trabajo/pred/fsp/buildings' + suffix + '_meta.json'))
                       for phase, suffix in [('dev', ''), ('prod', '_prod')]},
            'offsets': 'Reuse saved b0/weighted observed mark mean, and source E_cost_peril/exposure with original q floor1e-4; no CDF or C0 estimation.',
            'semantics': 'Frequency uses cost-completion offset; f*s is a cost proxy, not an identified ultimate-event-frequency and severity decomposition. f includes period exposure exactly once; no future cp multiplication.',
            'frozen_cost': {'source_model_fits': 24, 'perils': 6, 'phases': 2, 'early_stopping_searches': 0,
                            'new_C0_fits': 0, 'new_target_price_fits': 0, 'new_calibrations': 0,
                            'new_submission_CSVs': 0, 'new_scores': 0, 'new_submissions': 0},
            'criteria_before_fit': ['All pinned source SHA unchanged', 'All90 prior feature checks passed',
                                    'Source rows/years match saved counts in each phase',
                                    'Counts, weighted positive marks and b0 match saved metadata'],
            'criteria_after_fit': ['Save every model and per-row f/s/raw outputs',
                                   'Finite positive components and exposure included once',
                                   'Exact save/load and shuffled-key inference replay',
                                   'Independent tree-leaf sum and exponent/offset arithmetic',
                                   'No target labels, reestimated C0, new hyperparameter search or submission'],
            'predictive_admission': False, 'new_candidate_weights_chosen': False,
            'B00_all_alternatives_preserved': True, '2024_open': True, 'sources': sources()}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Se registra antes de ajustar la recuperación del componente faltante de edificios: '
        '24 modelos fuente Poisson/Gamma (seis peligros, fases2021–2023 y2021–2024), con las rondas ya elegidas en los metadatos recibidos. '
        'No hay nueva búsqueda de rondas, hiperparámetros, pesos de mezcla o calibración. Las90 comprobaciones de entradas pasaron; '
        'se reutilizan C0/exposiciones de coste y las constantes guardadas. Se guardarán modelos y f/s por fila. '
        'Los originales no conservaron sus Boosters, por lo que es una reconstrucción numérica nueva, no un replay idéntico acreditado. '
        'Se aplica historia2 explícitamente; no está demostrado qué opción de historial usó el FSp original en2025. '
        'El offset de frecuencia usa completitud ponderada por coste y su producto con marcas observadas conserva esa limitación. '
        'No se cargan etiquetas emergentes ni se puntúa o produce un CSV de envío en esta etapa. '
        'Una recuperación mecánica satisfactoria no acredita mejora predictiva ni admite una entrega. '
        'B00 y todas las alternativas siguen guardados,2024abierto como desarrollo. Plan y fuentes: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-MISION017-FSP-EDIFICIOS-RECUPERACION-PREVIO',
        '--asunto', 'Recuperación acotada del productor faltante de edificios, sin búsqueda nueva', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'plan_sha256': w.sha(PLAN), 'budget_fits': 24, 'forum': json.loads(response.stdout)}))


def leaf_sum(model, X):
    leaves = np.asarray(model.predict(X, pred_leaf=True))
    if leaves.ndim == 1:
        leaves = leaves[:, None]
    total = np.zeros(len(X))
    for j, tree in enumerate(model.dump_model()['tree_info']):
        lookup = {}
        def visit(node):
            if 'leaf_value' in node:
                lookup[node.get('leaf_index', 0)] = node['leaf_value']
            else:
                visit(node['left_child']); visit(node['right_child'])
        visit(tree['tree_structure'])
        total += np.array([lookup[int(k)] for k in leaves[:, j]])
    return total


def run():
    registration = w.read(OUT / 'registration.json')
    assert w.sha(PLAN) == registration['plan_sha256'] and not (OUT / 'report.json').exists()
    plan = w.read(PLAN)
    assert sources() == plan['sources'], 'Pinned source changed.'
    started = OUT / 'started.json'
    if started.exists():
        old = w.read(started)
        assert old['plan_sha256'] == w.sha(PLAN), 'Reconcile previous execution before resuming.'
    else:
        dump(started, {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN)})
    counts = pd.read_parquet(BASE / 'recuentos_fuente2024_v1/counts_buildings.parquet')
    fitted = []; outputs = {}; start = time.monotonic()
    for phase in ['dev', 'prod']:
        rows = pd.read_parquet(MATRIX / f'rows_source_{phase}.parquet')
        target = pd.read_parquet(MATRIX / f'rows_target_{phase}.parquet')
        X = pd.read_parquet(MATRIX / f'matrix_source_{phase}.parquet')
        Xe = pd.read_parquet(MATRIX / f'matrix_target_{phase}.parquet')
        cn = counts.loc[counts.year.isin(plan['source_' + phase + '_years'])].reset_index(drop=True)
        assert np.array_equal(cn.row_id, rows.row_id) and len(X) == len(rows) and len(Xe) == len(target)
        assert np.array_equal(cn.exposure, rows.exposure)
        assert cn.year.isin(plan['source_' + phase + '_years']).all()
        result = target[['row_id', 'year', 'exposure']].copy()
        for peril, old in sorted(plan['rounds'][phase].items()):
            n = cn['N_' + peril].to_numpy(float)
            cost = cn['T0_cents_' + peril].to_numpy(float) / 100.
            exp = cn.exposure.to_numpy(float)
            q = cn['E_cost_' + peril].to_numpy(float) / exp
            offset = np.log(exp * np.maximum(q, 1e-4)) + old['b0']
            positive = (n > 0) & (cost > 0)
            assert int(n.sum()) == old['n_dev']
            assert abs(np.log(n.sum() / np.sum(exp * np.maximum(q, 1e-4))) - old['b0']) < 1e-12
            assert abs(cost[positive].sum() / n[positive].sum() / old['sev_media'] - 1) < 1e-10
            for kind, params, rounds in [('f', PF, old['rondas_f']), ('s', PS, old['rondas_s'])]:
                key = f'{phase}_{peril}_{kind}'
                folder = OUT / key
                folder.mkdir(exist_ok=True)
                record_path = folder / 'record.json'; model_path = folder / 'model.txt'
                if record_path.exists():
                    record = w.read(record_path)
                    assert record['plan_sha256'] == w.sha(PLAN) and w.sha(model_path) == record['model_sha256']
                    model = lgb.Booster(model_file=str(model_path))
                else:
                    assert not (folder / 'fit_started.json').exists(), 'Unfinished fit: reconcile it before any new fitting.'
                    dump(folder / 'fit_started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'key': key,
                                                       'plan_sha256': w.sha(PLAN), 'rounds': rounds})
                    if kind == 'f':
                        train = lgb.Dataset(X, label=n, init_score=offset)
                        fit_rows = len(X)
                    else:
                        fit_rows = int(positive.sum())
                        train = lgb.Dataset(X.loc[positive].reset_index(drop=True),
                                            label=cost[positive] / n[positive], weight=n[positive],
                                            init_score=np.full(fit_rows, np.log(old['sev_media'])))
                    model = lgb.train(params, train, num_boost_round=int(rounds))
                    model.save_model(str(model_path))
                    record = {'key': key, 'phase': phase, 'peril': peril, 'kind': kind, 'fit_rows': fit_rows,
                              'requested_fixed_rounds': rounds, 'actual_rounds': model.current_iteration(),
                              'parameters': params, 'lightgbm_version': lgb.__version__,
                              'plan_sha256': w.sha(PLAN), 'model_sha256': w.sha(model_path)}
                    # Persist immediately: this fit must not be repeated after a later failure.
                    dump(record_path, record)
                    del train
                raw = model.predict(Xe, raw_score=True, num_threads=2)
                assert np.isfinite(raw).all()
                sampled = np.unique(np.linspace(0, len(Xe) - 1, 64, dtype=int))
                loaded = lgb.Booster(model_file=str(model_path))
                assert np.array_equal(raw[sampled], loaded.predict(Xe.iloc[sampled], raw_score=True, num_threads=2))
                reverse = sampled[::-1]
                assert np.array_equal(raw[reverse], loaded.predict(Xe.iloc[reverse], raw_score=True, num_threads=2))
                independent_raw = leaf_sum(loaded, Xe.iloc[sampled[:8]])
                raw_error = float(np.max(np.abs(independent_raw - raw[sampled[:8]])))
                assert raw_error < 1e-11
                base = old['b0'] if kind == 'f' else np.log(old['sev_media'])
                value = np.exp(raw + base)
                if kind == 'f':
                    value *= target.exposure.to_numpy(float)
                assert np.isfinite(value).all() and (value > 0).all()
                # Different algebra: separate exp(raw), exp(base), then one exposure.
                other = np.exp(raw[sampled]) * np.exp(base)
                if kind == 'f':
                    other *= target.exposure.to_numpy(float)[sampled]
                assert np.allclose(value[sampled], other, rtol=2e-14, atol=0)
                result[kind + '_' + peril] = value
                result['raw_' + kind + '_' + peril] = raw
                fitted.append({**record, 'independent_raw_leaf_sum_max_error': raw_error,
                               'save_load_key_shuffle_exact': True, 'offset_exponent_exposure_math_passed': True,
                               'component_min': float(value.min()), 'component_max': float(value.max())})
                print(json.dumps({'completed': key, 'models': len(fitted), 'rounds': rounds,
                                  'elapsed_seconds': round(time.monotonic() - start, 1)}), flush=True)
                del loaded, model
        path = OUT / f'components_{phase}.parquet'
        assert not path.exists(), 'Do not overwrite an earlier completed phase.'
        result.to_parquet(path, index=False)
        back = pd.read_parquet(path)
        assert back.equals(result.reset_index(drop=True))
        outputs[path.name] = {'sha256': w.sha(path), 'rows': len(result),
                              'test_rows': int(target.is_test.sum()), 'columns': list(result.columns)}
    assert len(fitted) == 24 and sources() == plan['sources']
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'status': 'numerical_source_producer_reconstructed_predictive_admission_pending',
              'plan_sha256': w.sha(PLAN), 'sources_unchanged': True, 'models': fitted, 'outputs': outputs,
              'new_source_component_model_fits': 24, 'new_C0_fits': 0, 'new_target_price_fits': 0,
              'new_early_stopping_searches': 0, 'new_aggregated_price_CSVs': 0, 'new_scores': 0, 'new_submissions': 0,
              'target_component_rows_per_phase': len(target), 'new_model_component_predictions': 24 * len(target),
              'original_producer_author': 'Claude', 'reconstruction_author': 'Codex',
              'independent_professional_review': False, 'predictive_improvement_established': False,
              '2024_open': True, 'B00_all_alternatives_preserved': True,
              'semantics': plan['semantics'], 'original_exact_tree_replay_not_established': True,
              'history_mode_new_reconstruction': 'historia2',
              'next': 'Preregister a held-out group/temporal comparison on saved scopes and cached C0 before scoring. Separate new-business/renewal, peril mix, level, tail and group influence. Do not choose weights or submit from numerical QA.'}
    dump(OUT / 'report.json', report)
    print(json.dumps({k: report[k] for k in ['status', 'new_source_component_model_fits', 'new_C0_fits', 'new_scores', 'new_submissions']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['register', 'run']); args = p.parse_args()
    register() if args.mode == 'register' else run()
