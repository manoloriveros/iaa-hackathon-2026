"""Enmienda previa a fit: bedrooms lineal; reutiliza dos GAM ya completos."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; PREVIOUS = BASE/'P16_GAM_fuente_20261026'
OUT = BASE/'P16_GAM_bedrooms_lineal_20261026'
PLAN = R/'registro/semana2_GAM_bedrooms_lineal_plan.json'
INDEX = R/'registro/semana2_GAM_bedrooms_lineal_actual.json'
sp = importlib.util.spec_from_file_location('p16_original_GAM_functions', R/'herramientas/GAM_fuente_privada_P16.py')
original = importlib.util.module_from_spec(sp); sp.loader.exec_module(original)
np = original.np; pd = original.pd; w = original.w; producer = original.producer
original.CURVES['contents'] = ['log_si', 'distance_to_river_km', 'elevation_m']
producer.OUT = OUT; producer.PLAN = PLAN; producer.INDEX = INDEX


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2)


def event(kind, **values):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as f: f.write(json.dumps({'utc': utc(), 'kind': kind, **values})+'\n')


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not (PREVIOUS/'report.json').exists()
    assert not w.read(producer.state.PHASE).get('active_jobs') and not w.read(producer.state.PHASE).get('active_execution')
    OUT.mkdir()
    previous_path = R/'registro/semana2_GAM_fuente_privada_plan.json'; previous = w.read(previous_path)
    assert all(w.sha(ROOT/p) == z for p, z in previous['sources'].items())
    assert (PREVIOUS/'contents/fit_invoked.json').exists() and not (PREVIOUS/'contents/model.json').exists()
    assert previous['basis']['duplicate_quantile_rule'].startswith('Fail before model fitting')
    x = pd.read_parquet(original.producer.HOME/'matrix_s1_contents.parquet', columns=['bedrooms', 'log_si', 'distance_to_river_km', 'elevation_m'])
    quantiles = {}
    for name in x:
        a = x[name].to_numpy(float); a = np.where(np.isfinite(a), a, np.nanmedian(a)); lo, hi = np.quantile(a, [.005, .995]); a = np.clip(a, lo, hi)
        if name == 'distance_to_river_km': a = np.log1p(a)
        quantiles[name] = np.quantile(a, np.linspace(0, 1, 4)).tolist()
        if name != 'bedrooms': assert np.all(np.diff(quantiles[name]) > 0)
    assert not np.all(np.diff(quantiles['bedrooms']) > 0)
    idx = np.arange(240)
    toy = pd.DataFrame({'log_si': np.log(10000+idx*100), 'bedrooms': np.where(idx < 180, 2., 3.),
                        'distance_to_river_km': .1+idx/100, 'elevation_m': idx.astype(float),
                        'high_value_items': (idx % 4).astype(float), 'exposure_model': .5+(idx % 20)/50})
    toy.loc[3, 'high_value_items'] = np.nan
    y = np.where(idx % 7 == 0, 10.+idx/20, 0.); e = toy.exposure_model.to_numpy()
    model, raw, controls = producer.fit_source(toy, y, e)
    assert 'bedrooms' in model['feature_names'] and 'bedrooms' not in model['preprocessor']['splines']
    assert len(model['preprocessor']['splines']) == 3
    assert np.array_equal(producer.predict(toy, json.loads(json.dumps(model))), raw)
    assert np.array_equal(producer.predict(toy.iloc[::-1], model), raw[::-1])
    reuse = {}; paths = [Path(__file__), Path(original.__file__), previous_path]
    for line in ['motor', 'buildings']:
        assert original.CURVES[line] == previous['curves'][line]
        old_folder = PREVIOUS/line; new_folder = OUT/line
        assert old_folder.is_relative_to(BASE) and new_folder.is_relative_to(BASE)
        shutil.copytree(old_folder, new_folder)
        historic = PREVIOUS/f'historical_{line}_three_seed.parquet'; shutil.copyfile(historic, OUT/historic.name)
        all_paths = [p for p in old_folder.rglob('*') if p.is_file()]+[historic]
        paths += all_paths
        reuse[line] = {p.relative_to(PREVIOUS).as_posix(): w.sha(p) for p in all_paths}
        for relative, sha in reuse[line].items(): assert w.sha(OUT/relative) == sha
    paths += list(PREVIOUS.glob('failure*.json'))+[PREVIOUS/'contents/fit_invoked.json']
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'GAM4_MI_bedrooms_linear',
            'amendment': 'Actual source bedrooms has tied quantile knots. Original preregistered guard stopped before contents estimator.fit. Retain the already-registered linear main effect for bedrooms; no new knot count/location is searched.',
            'actual_contents_quantiles_covariates_only': quantiles,
            'retained': 'Original motor/buildings curve definitions/data/methods exactly; reuse their completed artifacts. Contents retains3other source curves, all indicators, alpha1 and original other predictors/offsets.',
            'original_plan': w.rel(previous_path), 'original_plan_sha256': w.sha(previous_path),
            'curves': original.CURVES, 'reuse': reuse,
            'fit_accounting': {'original_price_pipeline_invocations': 3, 'original_actual_estimator_fits': 2,
                               'original_preprocessing_failures_before_estimator_fit': 1,
                               'new_actual_estimator_fits': 1, 'combined_actual_source_GAMfits': 3,
                               'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0,
                               'new_future2025inference': 0, 'new_finaltestprices': 0, 'new_submissions': 0},
            'reused_functions_unchanged': ['P16fit_preprocessor', 'P16transform', 'P16basis_input', 'P11fit_source'],
            'preflight': {'one_new_synthetic_GAMfit': 1, 'tied_bedrooms_retained_linear': True,
                          'other3actual_source_quantile_sets_strict': True, 'JSONreplay_order_exact': True},
            'predictive_adoption': False, 'sources': {**previous['sources'], **{w.rel(p): w.sha(p) for p in paths}},
            'limits': ['Amendment based only on source covariates and pre-fit failure, not target score.',
                       'Motor/buildings fit under original recipe, contents under this lower-capacity amendment; both recipes/failure preserved.',
                       'No claim that this change establishes private generalization. Complete target validation still required.'],
            '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Enmienda P16antes de ajustar contenidos: los cuantiles fuente de bedroomsno son distintos; el guardia preinscrito detuvo su preprocesamiento antes de estimator.fit. '
                    'Quedan2GAMreales completos y1fallo de preprocesamiento, no3modelos ajustados. '
                    'Faltó comprobar este caso discreto en el preflight original; se conserva código, plan, fallo y artefactos. '
                    'bedroomsmantendrá el efecto lineal previo, sin buscar otro número/ubicación de nudos. Las otras3curvas de contenidos sí tienen cuantiles fuente estrictos. '
                    'Los modelos de autos/edificios se reutilizan byte a byte: no cambian sus listas, datos ni funciones. Solo habrá1fitnuevo, total3fitsGAMreales combinados. '
                    'Un fixture nuevo de contenidos con cuantiles de dormitorios repetidos pasó ajuste,JSONyorden, conservando dormitorios lineales. '
                    'No se ha puntuado esta familia en destino; no es un cambio por score. CeroC0,calibraciones,precios2025oenvíos. '
                    'B00/F3c/P6y adversos preservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P16-BEDROOMS-ENMIENDA', '--asunto',
                             'P16 enmienda previa: dormitorios lineales por nudos repetidos, dos GAM reutilizados', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P16contents_amendment_registered_before_fit',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'actual_quantiles': quantiles, 'reused_models': 2, 'new_fits_planned': 1, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'kind': 'P16contents_only_GAMamendment',
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); producer.state.state_execution(execution)
    original_fit = producer.TweedieRegressor.fit
    def counted_fit(estimator, *args, **kwargs):
        event('actual_estimator_fit_started', line='contents')
        result = original_fit(estimator, *args, **kwargs)
        event('actual_estimator_fit_completed', line='contents'); return result
    producer.TweedieRegressor.fit = counted_fit
    try:
        line = 'contents'; folder = OUT/line; folder.mkdir(); started = time.monotonic()
        x = pd.read_parquet(producer.HOME/f'matrix_s1_{line}.parquet'); rows = pd.read_parquet(producer.HOME/f'rows_s1_{line}.parquet')
        dump(folder/'fit_invoked.json', {'utc': utc(), 'plan_sha256': w.sha(PLAN), 'line': line})
        model, raw, controls = producer.fit_source(x, rows.T0.to_numpy(float), rows.e_cost.to_numpy(float))
        dump(folder/'model.json', model)
        dump(folder/'fit_record.json', {'utc': utc(), 'line': line, 'model_sha256': w.sha(folder/'model.json'),
                                        'seconds': time.monotonic()-started, 'parameters': len(model['coef'])+1,
                                        'max_abs_gradient': model['max_abs_gradient'], 'iterations': model['iterations'],
                                        'controls': controls, 'plan_sha256': w.sha(PLAN)})
        weight = rows.exposure_model.to_numpy(float)
        center = float(producer.logsumexp(raw, b=weight)-np.log(weight.sum()))
        assert abs(center-producer.state.scalar_center(raw, weight)) < 1e-12
        source = rows[['row_id', 'year']].copy(); source['raw_log_rate'] = raw; source.to_parquet(folder/'source_raw.parquet', index=False)
        tr = pd.read_parquet(producer.HOME/f'rows_s2_{line}.parquet'); use = ~tr.is_test.to_numpy(bool)
        tx = pd.read_parquet(producer.HOME/f'matrix_s2_{line}.parquet').loc[use]
        f = tr.loc[use, ['row_id', 'year', 'is_test']].copy().reset_index(drop=True)
        prediction = producer.predict(tx, model); assert np.array_equal(prediction, producer.predict(tx, w.read(folder/'model.json')))
        ii = np.unique(np.linspace(0, len(tx)-1, 32, dtype=int))
        assert np.array_equal(prediction[ii[::-1]], producer.predict(tx.iloc[ii[::-1]], model))
        f['raw_log_rate'] = prediction; f['log_relative_A1S'] = prediction-center
        assert np.isfinite(np.exp(f.log_relative_A1S)).all() and not f.is_test.any()
        f.to_parquet(OUT/f'historical_{line}_three_seed.parquet', index=False)
        dump(folder/'application.json', {'source_center': center, 'source_rows': len(rows), 'historical_rows': len(f),
                                        'new_future2025inference': 0, 'JSONsave_load_order_exact': True,
                                        'raw_source_sha256': w.sha(folder/'source_raw.parquet'),
                                        'historical_components_sha256': w.sha(OUT/f'historical_{line}_three_seed.parquet')})
        for paths in plan['reuse'].values():
            for path, sha in paths.items(): assert w.sha(OUT/path) == sha
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P16combined_GAMcomplete_after_contents_amendment',
                  'candidate': 'GAM4_MI_bedrooms_linear', 'reused_models': 2, 'new_source_GAMfits_in_amendment': 1,
                  'combined_source_GAMfits': 3, 'failed_preprocessing_scopes_before_price_fit': 1,
                  'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0, 'new_future2025inference': 0,
                  'new_finaltestprices': 0, 'new_submissions': 0, 'curves': original.CURVES,
                  'plan_sha256': w.sha(PLAN), 'private_improvement_established': False, '2024_open': True,
                  'B00_all_alternatives_preserved': True}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'new_fit': 1, 'reused_models': 2, 'contents_parameters': len(model['coef'])+1}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'next': 'Preserve invocation/model and reconcile; no automatic refit'})
        raise
    finally:
        producer.TweedieRegressor.fit = original_fit; producer.state.state_execution(None)


def replay():
    producer.replay()  # Fresh combined JSONflow; no previous all-three GAMreplay existed.
    dump(OUT/'amendment_replay_context.json', {'author': 'Codex', 'utc': utc(), 'candidate': 'GAM4_MI_bedrooms_linear',
                                             'reused_model_hashes_bound_in_plan': True,
                                             'engine_receipt': w.rel(OUT/'replay_report.json'),
                                             'engine_receipt_sha256': w.sha(OUT/'replay_report.json'),
                                             'new_fits': 0, 'new_test_inference': 0})


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with producer.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
