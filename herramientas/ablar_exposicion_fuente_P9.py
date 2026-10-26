"""Ablación fija: exposición solo en offset, sin búsqueda nueva de capacidad.

Esta etapa fuente no puntúa ni produce precios finales emergentes.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import importlib.util
import json
import math
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P9_fuente_sin_exposicion_20261026'
PLAN = R/'registro/semana2_ablacion_exposicion_fuente_plan.json'
INDEX = R/'registro/semana2_ablacion_exposicion_fuente_actual.json'
PHASE = R/'registro/semana2_mision017_fase2_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.special import logsumexp
from threadpoolctl import threadpool_limits

spec = importlib.util.spec_from_file_location('p9_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']; SEEDS = [11, 12, 13]


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2)


def event(kind, **values):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as f:
        f.write(json.dumps({'utc': utc(), 'kind': kind, **values})+'\n')


def state_execution(execution):
    current = w.read(PHASE)
    if execution is not None:
        assert current.get('active_execution') is None and not current.get('active_jobs')
    elif current.get('active_execution'):
        assert current['active_execution']['pid'] == os.getpid()
    cut = R/'privado'/('corte_P9_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    w.update(PHASE, {'active_execution': execution, 'active_jobs': [] if execution is None else [execution]}, cut)
    p = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(p)['week_2_mission017_phase2_20261025']
    own['active_jobs'] = [] if execution is None else [execution]
    w.update(p, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, cut)


def predictor_frame(x):
    assert 'exposure_model' in x and x.columns.is_unique
    f = x.drop(columns=['exposure_model'])
    assert not {'row_id', 'T0', 'T0_cents', 'reserve', 'e_cost', 'exposure_model'}.intersection(f)
    return f


def scalar_center(raw, exposure):
    m = float(np.max(raw))
    return m+math.log(math.fsum((exposure*np.exp(raw-m)).tolist()))-math.log(math.fsum(exposure.tolist()))


def synthetic():
    x = pd.DataFrame({'risk': np.linspace(-1, 1, 80), 'exposure_model': np.linspace(.1, 1, 80),
                      'category': pd.Categorical(['a', 'b']*40)})
    y = np.where(np.arange(80) % 3 == 0, 5., 0.); e = np.full(80, .7)
    z = x.copy(); z['exposure_model'] = -99999.
    assert predictor_frame(x).equals(predictor_frame(z))
    params = dict(objective='tweedie', tweedie_variance_power=1.5, num_leaves=3, min_data_in_leaf=5,
                  verbosity=-1, num_threads=2, deterministic=True, force_row_wise=True, seed=11)
    models = [lgb.train(params, lgb.Dataset(predictor_frame(a), label=y, init_score=np.log(e)), num_boost_round=4)
              for a in [x, z]]
    assert models[0].model_to_string() == models[1].model_to_string()
    raw = models[0].predict(predictor_frame(x), raw_score=True, num_threads=2)
    c = float(logsumexp(raw, b=e)-np.log(e.sum()))
    assert abs(c-scalar_center(raw, e)) < 1e-12
    assert abs(np.average(np.exp(raw-c), weights=e)-1) < 1e-12
    return {'whole_synthetic_fit_invariant_to_excluded_predictor': True, 'synthetic_source_fits_separate': 2,
            'centering_two_methods': True, 'source_offset_preserved': True, 'new_contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert not w.read(PHASE).get('active_jobs') and not w.read(PHASE).get('active_execution')
    OUT.mkdir()
    sources = [Path(__file__), HOME/'report.json', HOME/'source_models/report.json',
               BASE/'P8_sonda_exposicion_fuente_20261026_v2/report.json']
    scopes = []
    for line in LINES:
        for market in ['s1', 's2']:
            sources += [HOME/f'matrix_{market}_{line}.parquet', HOME/f'rows_{market}_{line}.parquet']
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet')
        assert rows.row_id.is_unique and rows.year.isin([2021, 2022, 2023, 2024]).all() and not rows.is_test.any()
        assert rows.T0.ge(0).all() and rows.e_cost.gt(0).all()
        source_base = float(np.log(rows.T0.sum()/rows.e_cost.sum()))
        target = pd.read_parquet(HOME/f'rows_s2_{line}.parquet')
        hist = target.loc[~target.is_test].copy()
        assert hist.row_id.is_unique and hist.year.isin([2023, 2024]).all()
        for seed in SEEDS:
            old = HOME/f'source_models/{line}_seed{seed}_full/fit_record.json'; sources.append(old)
            record = w.read(old)
            assert math.isclose(record['initial_base'], source_base, rel_tol=1e-13)
            scopes.append({'line': line, 'seed': seed, 'rounds': record['current_iteration'],
                           'parameters': record['parameters'], 'initial_base': record['initial_base'],
                           'source_rows': len(rows), 'historical_application_rows': len(hist),
                           'old_record': w.rel(old), 'old_record_sha256': w.sha(old)})
    fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1S_D0_fixed_capacity',
            'hypothesis': 'Duration dependence can be simplified by removing exposure_model from source predictors without changing exposure offset; test the complete target algorithm later rather than infer benefit from sensitivity.',
            'necessity': 'P8shows material partial duration dependence in buildings/contents and a retained motor extreme. This is not a bug finding or proof that annual risk must be duration neutral.',
            'change': 'Drop exactly exposure_model, preserve all other source predictors/categories/T0/e_cost/offset/initialization.',
            'budget': {'source_full_fits': 9, 'new_earlystopping_fits': 0, 'new_C0_fits': 0,
                       'target_calibrations': 0, 'new_target_scores': 0, 'new_final2025prices': 0, 'new_submissions': 0},
            'fixed_rounds': 'Original all-source full-model tree count per line/seed. No new tuning/early stopping. Original round selection used source exposure predictor; this is a conditional fixed-capacity ablation.',
            'target_application': 'Historical2023/2024 covariates only after each source fit. No future2025inference in this unit. Source centering uses original exposure_model metadata as weights, not as a predictor.',
            'aggregation': 'All three seeds, geometric mean of annual relativities. No seed selection or per-line recipe selection.',
            'acceptance': 'Technical only: exact schemas/keys/hashes; finite positive components; independent scalar centering and leaf sums; saved-model reload and order exact. No predictive adoption from source stage.',
            'next_validation': 'Separately preregister complete S2/H1pooled group folds and conditional2023-to2024 target transfer versus same original S2/H1. Reuse unaffected C0/N3 and H1/G3ratios with exact bindings. Preserve minimum .002, group intervals, stress/cell/influence gates and inadequate futureweight ESS; no publicscore or totalmatching.',
            'limits': ['Source2021-2024and frozen all-source C0 remain conditional; not a prospective asof2023source holdout',
                       'Exposure may encode legitimate seasonality/selection; removal may harm performance',
                       'Dropping one column changes feature-subsampling index mapping, so trees are not a perfect isolated-path intervention',
                       'Emerging2024is open/adaptive; no private performance conclusion',
                       'No new climate/capital/valuation/tail assumptions or capacity search'],
            'scopes': scopes, 'preflight': fixture, 'sources': {w.rel(p): w.sha(p) for p in sources},
            '2024_open': True, 'B00_all_alternatives_preserved': True, 'max_cycle_minutes': 45}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P9, ablación estándar de A1S: quitar solo exposure_model de los predictores, conservando exposición y C0 fuente en el offset. '
                    'No se retira del modelo vigente. P8 justifica la comparación por dependencia material, no acredita un error. '
                    'Se fijan los mismos parámetros, semillas11/12/13 y rondas originales por ramo/semilla:9fitsfull, sin earlystopping nuevo. '
                    'La matriz emergente se lee para aplicar solo después de aprender en fuente; aquí no se calibra ni puntúa. '
                    'Se conservarán centros fuente ponderados por exposición, modelos, hashes, cachés históricas y controles numéricos. '
                    'No se infiere con2025ni se produce otro CSV. La retirada puede perder estacionalidad o selección legítima. '
                    'Una evaluación completa posterior usará los mismos grupos, referencias, sensibilidades y criterios, sin perseguir el público ni empatar totales. '
                    'El fixture verificó invariancia del ajuste al predictor excluido con dos fits sintéticos, fuera del presupuesto real. '
                    '2024abierto adaptativo; B00/F3c/P6y adversos intactos. Plan: '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P9-FUENTE-PREVIO', '--asunto',
                             'P9 previo: simplificar predictor de duración con capacidad fija, nueve ajustes fuente',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'source_ablation_registered_before_real_fit',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout),
               'output': w.rel(OUT), 'new_real_fits': 0, 'new_submissions': 0, '2024_open': True}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'preflight': 'passed', 'source_fits_planned': 9, 'synthetic_fits': 2, 'forum': receipt['forum']}))


def leaf_control(model, x):
    leaves = model.predict(x, pred_leaf=True, num_threads=2)
    description = model.dump_model(); totals = np.zeros(len(x))
    def values(node, found):
        if 'leaf_index' in node: found[node['leaf_index']] = node['leaf_value']
        else:
            values(node['left_child'], found); values(node['right_child'], found)
    for j, tree in enumerate(description['tree_info']):
        found = {}; values(tree['tree_structure'], found)
        totals += np.asarray([found[int(i)] for i in leaves[:, j]])
    return totals


def run():
    assert not (OUT/'report.json').exists() and not (OUT/'started.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': utc(), 'script': w.rel(Path(__file__)),
                 'kind': 'P9fixed_capacity_source_exposure_ablation', 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); state_execution(execution)
    try:
        records = []; applications = []
        for line in LINES:
            x = predictor_frame(pd.read_parquet(HOME/f'matrix_s1_{line}.parquet'))
            rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet')
            y = rows.T0.to_numpy(float); e = rows.e_cost.to_numpy(float); ew = rows.exposure_model.to_numpy(float)
            assert len(x) == len(rows) and np.isfinite(e).all() and np.isfinite(y).all()
            components = []
            for scope in [a for a in plan['scopes'] if a['line'] == line]:
                seed = scope['seed']; folder = OUT/f'{line}_{seed}'; folder.mkdir()
                dump(folder/'fit_invoked.json', {'utc': utc(), 'scope': scope, 'plan_sha256': w.sha(PLAN)})
                event('source_fit_started', line=line, seed=seed)
                started = time.monotonic()
                dataset = lgb.Dataset(x, label=y, init_score=np.log(e)+scope['initial_base'])
                model = lgb.train(scope['parameters'], dataset, num_boost_round=scope['rounds'])
                model.save_model(str(folder/'model.txt'))
                record = {'utc': utc(), 'line': line, 'seed': seed, 'rounds': model.current_iteration(),
                          'model_sha256': w.sha(folder/'model.txt'), 'seconds': time.monotonic()-started,
                          'initial_base': scope['initial_base'], 'parameters': scope['parameters'],
                          'lightgbm_version': lgb.__version__, 'plan_sha256': w.sha(PLAN)}
                dump(folder/'fit_record.json', record); event('source_fit_completed', **record)
                assert record['rounds'] == scope['rounds'] and model.feature_name() == list(x)
                raw = model.predict(x, raw_score=True, num_threads=2, validate_features=True)
                center = float(logsumexp(raw, b=ew)-np.log(ew.sum()))
                independent = scalar_center(raw, ew)
                assert abs(center-independent) < 1e-12
                assert abs(np.average(np.exp(raw-center), weights=ew)-1) < 2e-12
                # Target covariates are first opened after this source-only fit is saved.
                target_rows = pd.read_parquet(HOME/f'rows_s2_{line}.parquet')
                hist = ~target_rows.is_test.to_numpy(bool)
                tx = predictor_frame(pd.read_parquet(HOME/f'matrix_s2_{line}.parquet')).loc[hist].copy()
                metadata = target_rows.loc[hist, ['row_id', 'year', 'is_test']].copy().reset_index(drop=True)
                assert list(tx) == list(x) and metadata.year.isin([2023, 2024]).all() and not metadata.is_test.any()
                traw = model.predict(tx, raw_score=True, num_threads=2, validate_features=True)
                assert np.isfinite(raw).all() and np.isfinite(traw).all()
                loaded = lgb.Booster(model_file=str(folder/'model.txt'))
                ii = np.unique(np.linspace(0, len(tx)-1, 16, dtype=int))
                assert np.array_equal(traw[ii], loaded.predict(tx.iloc[ii], raw_score=True, num_threads=2))
                assert np.array_equal(traw[ii[::-1]], loaded.predict(tx.iloc[ii[::-1]], raw_score=True, num_threads=2))
                error = float(np.max(np.abs(leaf_control(loaded, tx.iloc[ii[:8]])-traw[ii[:8]])))
                assert error < 1e-10
                source = rows[['row_id', 'year']].copy(); source['raw_delta'] = raw
                metadata['raw_delta'] = traw; metadata['log_relative'] = traw-center
                assert np.isfinite(np.exp(metadata.log_relative)).all() and np.exp(metadata.log_relative).gt(0).all()
                source.to_parquet(folder/'source_raw.parquet', index=False)
                metadata.to_parquet(folder/'historical_components.parquet', index=False)
                application = {'line': line, 'seed': seed, 'source_center': center, 'scalar_center': independent,
                               'source_prediction_rows': len(x), 'historical_application_rows': len(tx),
                               'future2025inference_rows': 0, 'save_load_order_exact': True, 'leaf_sum_max_abs_error': error,
                               'control_inference_rows_separate': 40,
                               'source_raw_sha256': w.sha(folder/'source_raw.parquet'),
                               'historical_components_sha256': w.sha(folder/'historical_components.parquet')}
                dump(folder/'application.json', application)
                records.append(record); applications.append(application); components.append(metadata)
                del dataset, model, loaded, tx, raw, traw; gc.collect()
                print(json.dumps({'completed': line+'_'+str(seed), 'rounds': record['rounds'], 'seconds': record['seconds']}), flush=True)
            assert all(np.array_equal(f.row_id, components[0].row_id) for f in components)
            result = components[0][['row_id', 'year', 'is_test']].copy()
            result['log_relative_A1S'] = np.mean(np.stack([f.log_relative.to_numpy() for f in components]), axis=0)
            result.to_parquet(OUT/f'historical_{line}_three_seed.parquet', index=False)
            del x, rows, components; gc.collect()
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P9source_ablation_complete_target_validation_pending',
                  'new_source_full_fits': 9, 'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0,
                  'new_future2025inference_rows': 0, 'new_finaltestprices': 0, 'new_submissions': 0,
                  'records': records, 'applications': applications, 'plan_sha256': w.sha(PLAN),
                  'private_improvement_established': False, 'predictive_adoption': False, '2024_open': True,
                  'B00_all_alternatives_preserved': True, 'limits': plan['limits']}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'new_source_fits': 9, 'target_scores': 0}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'completed_models': len(list(OUT.glob('*/fit_record.json'))),
              'next': 'Reconcile saved fit attempts and applications before any resume; no blind repeats'})
        raise
    finally: state_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    plan = w.read(PLAN); d = w.read(OUT/'report.json')
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    before = w.sha(OUT/'events.jsonl'); old = lgb.Booster
    def reject(*a, **kw): raise AssertionError('No model loading or fits in saved-array replay')
    lgb.Booster = reject
    try:
        for line in LINES:
            ew = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['exposure_model']).exposure_model.to_numpy(float)
            frames = []
            for seed in SEEDS:
                folder = OUT/f'{line}_{seed}'; app = w.read(folder/'application.json')
                assert w.sha(folder/'model.txt') == w.read(folder/'fit_record.json')['model_sha256']
                raw = pd.read_parquet(folder/'source_raw.parquet').raw_delta.to_numpy(float)
                assert abs(scalar_center(raw, ew)-app['source_center']) < 1e-12
                assert app['historical_components_sha256'] == w.sha(folder/'historical_components.parquet')
                f = pd.read_parquet(folder/'historical_components.parquet')
                assert np.array_equal(f.raw_delta.to_numpy()-app['source_center'], f.log_relative.to_numpy())
                frames.append(f)
            mean = np.mean(np.stack([f.log_relative.to_numpy() for f in frames]), axis=0)
            saved = pd.read_parquet(OUT/f'historical_{line}_three_seed.parquet')
            assert np.array_equal(saved.row_id, frames[0].row_id) and np.array_equal(mean, saved.log_relative_A1S)
    finally: lgb.Booster = old
    assert w.sha(OUT/'events.jsonl') == before
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P9saved_array_replay_exact',
                                  'all3lines_exact': True, 'new_source_queries': 0, 'new_fits': 0,
                                  'report_sha256': w.sha(OUT/'report.json'), 'events_unchanged': True})
    print(json.dumps({'replay': 'exact', 'new_source_queries': 0, 'new_fits': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
