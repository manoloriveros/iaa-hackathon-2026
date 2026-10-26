"""P8: sensibilidad parcial de exposición en nueve modelos fuente congelados.

No es una cotización alternativa: centros y demás variables quedan fijos.
No estima beneficio predictivo, efecto causal o que duración deba ser neutral.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import ast
import shutil

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
P6 = BASE/'P6_productor_S2_H1_nominal_20261026_v1'
STATIC = BASE/'P8_contrato_fuente_estatico_20261026_v1'
PREVIOUS = BASE/'P8_sonda_exposicion_fuente_20261026_v1'
OUT = BASE/'P8_sonda_exposicion_fuente_20261026_v2'
PLAN = R/'registro/semana2_sonda_exposicion_fuente_plan_v2.json'
SEEDS = [11, 12, 13]; CONDITIONS = [('BASE', 1.), ('D75', .75), ('D50', .5)]
BANDS = ['1-30', '31-90', '91-180', '181-366']
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader')); sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
import lightgbm as lgb
from threadpoolctl import threadpool_limits


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


parent = load('P8_standard_scope_helpers', R/'herramientas/validar_transferencia_anual_H1.py')
w = parent.w; n = parent.n; digest = parent.b.digest


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream: json.dump(value, stream, ensure_ascii=False, indent=2)


def event(kind, **fields):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as stream:
        stream.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'kind': kind, **fields})+'\n')


def sample_metadata(future):
    assert future.row_id.is_unique and future.year.eq(2025).all() and future.is_test.all()
    f = future[['row_id', 'new_business', 'period_start', 'period_end', 'exposure_calendar', 'exposure_model']].copy()
    f['days'] = ((pd.to_datetime(f.period_end)-pd.to_datetime(f.period_start)).dt.days+1).astype(int)
    assert f.days.between(1, 366).all() and np.array_equal(f.days.to_numpy()/365, f.exposure_calendar)
    assert np.array_equal(f.exposure_calendar.round(4), f.exposure_model)
    f['duration_band'] = pd.cut(f.days, [0, 30, 90, 180, 366], labels=BANDS).astype('string')
    f['selection_hash'] = [hashlib.sha256(('P8-exp-v1|'+str(x)).encode()).hexdigest() for x in f.row_id]
    pieces = []
    for nb in [0, 1]:
        for band in BANDS:
            cell = f.loc[f.new_business.astype(int).eq(nb) & f.duration_band.eq(band)]
            pieces.append(cell.sort_values(['selection_hash', 'row_id']).head(8))
    result = pd.concat(pieces, ignore_index=True)
    assert result.row_id.is_unique and 0 < len(result) <= 64
    assert not any(x in result for x in ['T0', 'reserve', 'prediction', 'raw_delta', 'log_relative_A1S'])
    return result


def changed_matrix(x, metadata, fraction):
    assert len(x) == len(metadata) and 'exposure_model' in x
    assert not {'T0', 'T0_cents', 'reserve', 'e_cost', 'prediction'}.intersection(x.columns)
    days = metadata.days.to_numpy(int)
    newdays = np.maximum(1, np.floor(days*fraction).astype(int))
    assert (newdays <= days).all() and (newdays >= 1).all()
    new = x.copy(deep=True)
    new['exposure_model'] = pd.Series(newdays/365).round(4).to_numpy()
    assert new.drop(columns='exposure_model').equals(x.drop(columns='exposure_model'))
    if fraction == 1.:
        assert new.equals(x)
    return new, newdays


def independent_leaf_sum(model, x):
    leaf = np.asarray(model.predict(x, pred_leaf=True, num_iteration=-1, num_threads=2, validate_features=True))
    treeinfo = model.dump_model()['tree_info']
    assert leaf.ndim == 2 and leaf.shape == (len(x), len(treeinfo))
    total = np.zeros(len(x))
    for j, tree in enumerate(treeinfo):
        values = {}
        def visit(node):
            if 'leaf_value' in node: values[int(node.get('leaf_index', 0))] = float(node['leaf_value'])
            else:
                visit(node['left_child']); visit(node['right_child'])
        visit(tree['tree_structure'])
        total += np.array([values[int(k)] for k in leaf[:, j]])
    return total


def sensitivity_summary(metadata, raw):
    # raw shape [seed, condition, row], all centres fixed so they cancel in
    # log relativity differences; no recentering on the intervention sample.
    assert raw.shape == (3, 3, len(metadata)) and np.isfinite(raw).all()
    result = []; row_values = metadata[['row_id', 'new_business', 'duration_band', 'days']].copy()
    for j, (condition, fraction) in enumerate(CONDITIONS[1:], 1):
        newdays = np.maximum(1, np.floor(metadata.days.to_numpy()*fraction).astype(int))
        changed = newdays < metadata.days.to_numpy(); delta = raw[:, j, :]-raw[:, 0, :]
        ratio = np.exp(delta.mean(axis=0))
        scalar = np.array([math.exp(math.fsum(delta[:, i].tolist())/3) for i in range(len(metadata))])
        assert np.allclose(ratio, scalar, rtol=3e-15, atol=0.)
        assert np.array_equal(ratio[~changed], np.ones(np.count_nonzero(~changed)))
        row_values[condition+'_new_days'] = newdays
        row_values[condition+'_annual_relative_ratio_geomean'] = ratio
        for si, seed in enumerate(SEEDS): row_values[condition+'_seed'+str(seed)+'_ratio'] = np.exp(delta[si])
        def summarize_mask(mask):
            actual = mask & changed
            if not actual.any(): return {'rows': int(mask.sum()), 'changed_rows': 0, 'ratio_quantiles': None, 'material_dependency_flag': False}
            z = ratio[actual]; absolute = np.abs(np.log(z)); p95 = float(np.quantile(absolute, .95)); median = float(np.median(absolute))
            return {'rows': int(mask.sum()), 'changed_rows': int(actual.sum()),
                    'ratio_quantiles': np.quantile(z, [0., .05, .5, .95, 1.]).tolist(),
                    'median_absolute_log_ratio': median, 'p95_absolute_log_ratio': p95,
                    'material_dependency_flag': bool(median >= math.log(1.02) or p95 >= math.log(1.1)),
                    'seed_ratios': {str(seed): np.quantile(np.exp(delta[si, actual]), [0., .5, 1.]).tolist() for si, seed in enumerate(SEEDS)}}
        full = summarize_mask(np.ones(len(metadata), bool)); strata = []
        for nb in [0, 1]:
            for band in BANDS:
                mask = metadata.new_business.astype(int).eq(nb).to_numpy() & metadata.duration_band.eq(band).to_numpy(dtype=bool)
                strata.append({'NB': nb, 'duration_band': band, **summarize_mask(mask)})
        result.append({'condition': condition, 'fraction': fraction, **full, 'strata': strata})
    return result, row_values


def synthetic():
    class FrozenToy:
        def predict(self, x, pred_leaf=False, **kwargs):
            leaf = np.where(x.exposure_model.to_numpy() < .5, 0, 1)
            return leaf.reshape(-1, 1) if pred_leaf else np.where(leaf == 0, .2, -.1)
        def dump_model(self):
            return {'tree_info': [{'tree_structure': {'split_index': 0, 'left_child': {'leaf_index': 0, 'leaf_value': .2},
                                                       'right_child': {'leaf_index': 1, 'leaf_value': -.1}}}]}
    days = np.array([1, 2, 30, 90, 120, 180, 200, 365]*2)
    future = pd.DataFrame({'row_id': ['toy'+str(i) for i in range(len(days))], 'year': 2025, 'is_test': True,
                           'new_business': np.arange(len(days)) % 2, 'period_start': pd.Timestamp('2025-01-01'),
                           'period_end': pd.Timestamp('2025-01-01')+pd.to_timedelta(days-1, unit='D'),
                           'exposure_calendar': days/365, 'exposure_model': pd.Series(days/365).round(4)})
    metadata = sample_metadata(future)
    assert metadata.equals(sample_metadata(future.sample(frac=1, random_state=71)))
    x = pd.DataFrame({'exposure_model': metadata.exposure_model.to_numpy(), 'numeric_missing': [np.nan]*len(metadata),
                      'category': pd.Categorical(['a', None]*(len(metadata)//2))})
    model = FrozenToy(); predictions = []
    for _, fraction in CONDITIONS:
        changed, newdays = changed_matrix(x, metadata, fraction)
        y = model.predict(changed); independent = independent_leaf_sum(model, changed)
        assert np.array_equal(y, independent)
        predictions.append(y)
    raw = np.tile(np.stack(predictions)[None, :, :], (3, 1, 1))
    summary, rows = sensitivity_summary(metadata, raw)
    ratio_columns = [c for c in rows if c.endswith('_ratio') or '_ratio_' in c]
    assert len(summary) == 2 and np.isfinite(rows[ratio_columns].to_numpy(float)).all()
    # A duration-dependent frozen source breaks the claim that a cached-relative
    # calendar-scaling test alone certifies the raw source dependency.
    assert any(np.any(np.abs(np.log(rows[k])) > .1) for k in rows if 'geomean' in k)
    neutral = np.zeros_like(raw); neutral_summary, neutral_rows = sensitivity_summary(metadata, neutral)
    assert all(not x['material_dependency_flag'] for x in neutral_summary)
    assert np.array_equal(neutral_rows[ratio_columns].to_numpy(), np.ones(neutral_rows[ratio_columns].shape))
    return {'author': 'Codex', 'fixture': 'Frozen numeric leafvalue toy, not an actual LightGBMtraining/API certificate',
            'selection_shuffle_exact': True, 'nonexposure_category_and_NaNfields_preserved': True,
            'zero_feature_dependency_identity': True, 'cached_relative_scaling_counterexample': True,
            'independent_leaf_arithmetic': True, 'new_model_fits': 0, 'new_actual_source_inference': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    failure = w.read(PREVIOUS/'defect_before_real_inference.json')
    assert failure['actual_source_inference_rows'] == failure['actual_source_model_loads'] == failure['new_model_fits'] == 0
    def bodies(path):
        return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text(encoding='utf8')).body if isinstance(node, ast.FunctionDef)}
    old, new = bodies(PREVIOUS/'prepare_attempt_v1.py'), bodies(Path(__file__))
    stable = ['sample_metadata', 'changed_matrix', 'independent_leaf_sum', 'sensitivity_summary', 'run', 'replay']
    assert all(old[name] == new[name] for name in stable)
    for name, sha in failure['prepared_input_files'].items():
        assert w.sha(PREVIOUS/name) == sha
        shutil.copyfile(PREVIOUS/name, OUT/name)
        assert w.sha(OUT/name) == sha
    dump(OUT/'input_reuse.json', {'author': 'Codex', 'failure': w.rel(PREVIOUS/'defect_before_real_inference.json'),
                                 'failure_sha256': w.sha(PREVIOUS/'defect_before_real_inference.json'),
                                 'unchanged_core_AST': stable, 'copied_input_hashes': failure['prepared_input_files'],
                                 'new_model_fits': 0, 'new_source_inference': 0})
    static = w.read(STATIC/'report.json'); source = w.read(HOME/'source_models/report.json')
    assert all(w.sha(ROOT/path) == sha for path, sha in static['source_hashes'].items())
    files = [Path(__file__), Path(parent.__file__), Path(n.__file__), Path(w.__file__),
             STATIC/'report.json', STATIC/'completion_receipt.json', HOME/'report.json', HOME/'source_models/report.json',
             P6/'report.json', P6/'production_artifacts_manifest.json',
             BASE/'P7_ventana_reporte_madura_20261026_v2/report.json',
             R/'herramientas/entrenar_nucleo_A1S.py', R/'registro/semana2_mision_privada_plan_v1.json',
             R/'registro/semana2_control_entregas_codex_actual.json']
    scopes = []
    for line in ['motor', 'buildings', 'contents']:
        metadata_path = P6/f'future_{line}.parquet'; future = pd.read_parquet(metadata_path)
        sample = sample_metadata(future); assert sample.equals(sample_metadata(future.sample(frac=1, random_state=72)))
        rows_path = HOME/f'rows_s2_{line}.parquet'; matrix_path = HOME/f'matrix_s2_{line}.parquet'
        rows = pd.read_parquet(rows_path, columns=['row_id', 'year', 'is_test']); x = pd.read_parquet(matrix_path)
        assert rows.row_id.is_unique and len(rows) == len(x)
        row_position = pd.Series(np.arange(len(rows)), index=rows.row_id).loc[sample.row_id].to_numpy()
        assert rows.iloc[row_position].year.eq(2025).all() and rows.iloc[row_position].is_test.all()
        selected = x.iloc[row_position].reset_index(drop=True)
        assert np.array_equal(selected.exposure_model, sample.exposure_model)
        assert not {'T0', 'T0_cents', 'reserve', 'e_cost', 'prediction'}.intersection(selected.columns)
        assert selected.equals(pd.read_parquet(OUT/f'X_{line}.parquet'))
        assert sample.equals(pd.read_parquet(OUT/f'metadata_{line}.parquet'))
        files += [metadata_path, rows_path, matrix_path, OUT/f'X_{line}.parquet', OUT/f'metadata_{line}.parquet']
        models = []
        for seed in SEEDS:
            folder = HOME/f'source_models/{line}_seed{seed}_full'; model = folder/'model.txt'
            assert w.sha(model) == static['source_hashes'][w.rel(model)] == w.read(folder/'fit_record.json')['model_sha256']
            names = next(s for s in model.read_text(encoding='utf8').splitlines() if s.startswith('feature_names=')).split('=', 1)[1].split()
            assert names == list(selected.columns)
            application = w.read(folder/'application.json'); comp = folder/'target_components.parquet'
            assert w.sha(comp) == application['outputs']['target_components.parquet']
            cached = pd.read_parquet(comp).set_index('row_id').loc[sample.row_id]
            assert cached.year.eq(2025).all() and cached.is_test.all()
            assert cached[['raw_delta', 'log_relative']].reset_index().equals(pd.read_parquet(OUT/f'baseline_{line}_seed{seed}.parquet'))
            files += [model, folder/'fit_record.json', folder/'application.json', comp, OUT/f'baseline_{line}_seed{seed}.parquet']
            models.append({'seed': seed, 'model': w.rel(model), 'model_sha256': w.sha(model),
                           'center': application['center'], 'baseline': w.rel(OUT/f'baseline_{line}_seed{seed}.parquet')})
        scopes.append({'line': line, 'rows': len(sample), 'metadata': w.rel(OUT/f'metadata_{line}.parquet'),
                       'matrix': w.rel(OUT/f'X_{line}.parquet'), 'models': models,
                       'cell_counts': sample.groupby(['new_business', 'duration_band'], observed=True).size().reset_index(name='rows').astype({'duration_band': str}).to_dict('records')})
    dump(OUT/'synthetic_report.json', synthetic()); files += [OUT/'synthetic_report.json', OUT/'input_reuse.json',
                                                            PREVIOUS/'defect_before_real_inference.json', PREVIOUS/'prepare_attempt_v1.py']
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'type': 'P8_frozen_source_exposure_feature_sensitivity',
            'repair_before_real_inference': 'V1fixture ratio-substring filter also selected duration_band. V2uses explicit ratio suffix/token only. Numeric transformation/selection/probe/summary/run/replay ASTunchanged. Preserve failure and15inputsnapshots byte-identically; zero actualsourceinferenceorfit inV1.',
            'hypothesis': 'The active exposure_model feature creates an annual source-relativity dependency not tested by changing calendar exposure with cached source relativities fixed. Quantify it as one possible model-risk route under cohortduration shift, without claiming it is wrong or explains the10.83percent basegap.',
            'selection': 'At most8future2025rows per line/NB-REN/durationband(1-30,31-90,91-180,181-366days), smallestSHA256(P8-exp-v1|rowid). No labels, predictions, influence or publicscore used; nonrepresentative diagnostic sample.',
            'interventions': 'BASE unchanged; D75/D50 replace only sourcefeatureexposure_model with round4(max(1,floor(originaldays*fraction))/365). Other matrixfeatures and sourcecentres fixed. Metadata daycounts are shortened within originalcoverage. Do not claim coherent completeS2/H1prices, source-featurecausality or duration-neutral annualrisk.',
            'frozen': 'All9sourceA1Sboosters and3seedgeometricmean, original per-seed centres, feature/categoricalorder, source/treatment/modelselection and nominaltarget. No refit, recentering, calibrator, C0or new full2025pricecandidate.',
            'criterion': 'Descriptive dependency flag perline/condition amongchangedrows if median(abs(log(geomeanrelative_ratio)))>=log1.02 or p95>=log1.10. Not a statistical acceptance or feature-removal criterion. Report all9seeds, bothinterventions and allstrata, no winnerselection or confidenceinterval from this probe.',
            'controls': ['Actual baseline raw_deltaandraw-center equal cachedperseedvalues at every selectedrow',
                         'Strict modelhash/featureorder, category/NaNpreservation and realactualLibraryflow',
                         'Changedinput rawscores agree with separately summed saved leafvalues at<=8fixedrows permodel/condition; leafindices frompred_leaf so routing is not an independentsecondimplementation',
                         'Independent scalar geomean arithmetic, one-day unchangedinputidentity, immutablemodel/treecountandsources',
                         'Training/update/refit APIs forbidden duringrun; pure numericfixture before realinference',
                         'Replay of saved rawarrays/centres with model loading/prediction forbidden; no repeatquery suite'],
            'budget': {'max_selected_rows_perline': 64, 'max_raw_prediction_calls': 27, 'max_primary_raw_prediction_rows': 1728,
                       'max_leafcontrol_calls': 27, 'max_leafcontrol_rows': 216, 'new_model_fits': 0, 'new_C0fits': 0,
                       'new_calibrationfits': 0, 'new_finaltestprices': 0, 'new_submissions': 0},
            'limits': ['Finite outcome-free selectedfeatureprobe not populationimpact, predictivegain or a causal exposureeffect',
                       'Only A1Ssourcefeature changes; T2b/member/S2prices are not recomputed so no fullpolicyforecastclaim',
                       'Cached baseline/centres and originalmodelcontext including2024 and undatedmasters remain conditional',
                       'Private performance, emerging support, nominalgainminimum and prioradverses unresolved'],
            'scopes': scopes, '2024_open': True, 'B00_all_alternatives_preserved': True, 'submission_allowed': False,
            'sources': {w.rel(path): w.sha(path) for path in files}}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. RegistroP8antes de nueva inferencia fuente. Muestra fija sin respuestas por negocio y duración, '
                    'hasta64filas porramo, en los nueve modelos fuente congelados. Dos intervenciones fijas acortan días y '
                    'cambian únicamente exposure_model; centros y otras variables se conservan. No representa una cotización '
                    'completa ni presupone que la duración deba ser neutral. El ancla debe reproducir toda la caché elegida; '
                    'las salidas intervenidas se contrastarán con sumas de hojas guardadas. Presupuesto≤1728filas de '
                    'predicciónrawy≤216controles de hojas, cero ajustes/C0/precios2025oenvíos. La prueba numérica de selección, '
                    'transformación y aritmética pasó con un árbol fixture; el flujo LightGBMreal se verificará después del registro. '
                    'Se reportarán todos los ramos/semillas/celdas. Un efecto material no decide retirar variables o reescalar. '
                    'B00/F3c/P6/alternativas intactos,2024abierto adaptativo y privada prioritaria. Plan: '+w.rel(PLAN)+'.', encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P8-SONDA-V2-PREVIO', '--asunto',
                             'P8 registrada: sensibilidad de exposición con modelos fuente congelados', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT/'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout)})
    print(json.dumps({'registered': True, 'selected': {s['line']: s['rows'] for s in scopes},
                      'synthetic': w.read(OUT/'synthetic_report.json'), 'forum': json.loads(result.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/path) == value for path, value in plan['sources'].items())
    assert lgb.__version__ == '4.6.0'
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': datetime.now(timezone.utc).isoformat(),
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT), 'kind': 'P8_frozen_source_feature_probe_no_prices'}
    dump(OUT/'started.json', execution); n.OUT = OUT; n.set_execution(execution)
    guards = []
    def reject(*args, **kwargs): raise AssertionError('No source or target fitting allowed during P8probe')
    for module, name in [(lgb, 'train'), (lgb.Booster, 'update'), (lgb.Booster, 'refit')]:
        guards.append((module, name, getattr(module, name))); setattr(module, name, reject)
    results = {}; controls = []; calls = 0; rows = 0; leaf_calls = 0; leaf_rows = 0
    try:
        for scope in plan['scopes']:
            line = scope['line']; x = pd.read_parquet(ROOT/scope['matrix']); metadata = pd.read_parquet(ROOT/scope['metadata'])
            raw = np.empty((3, 3, len(metadata))); centers = []
            for si, item in enumerate(scope['models']):
                model = lgb.Booster(model_file=str(ROOT/item['model'])); trees = model.num_trees()
                assert model.feature_name() == list(x.columns)
                description = model.dump_model(); assert not description.get('average_output', False) and description['num_tree_per_iteration'] == 1
                cached = pd.read_parquet(ROOT/item['baseline']); assert np.array_equal(cached.row_id, metadata.row_id)
                center = item['center']; centers.append(center)
                selected_controls = np.unique(np.linspace(0, len(x)-1, min(8, len(x)), dtype=int))
                errors = []
                for j, (condition, fraction) in enumerate(CONDITIONS):
                    changed, newdays = changed_matrix(x, metadata, fraction)
                    event('raw_prediction_started', line=line, seed=item['seed'], condition=condition, rows=len(x))
                    predicted = model.predict(changed, raw_score=True, num_iteration=-1, num_threads=2, validate_features=True)
                    calls += 1; rows += len(x); raw[si, j] = predicted
                    event('raw_prediction_completed', line=line, seed=item['seed'], condition=condition, rows=len(x))
                    if j == 0:
                        assert np.array_equal(predicted, cached.raw_delta.to_numpy())
                        assert np.array_equal(predicted-center, cached.log_relative.to_numpy())
                    control = independent_leaf_sum(model, changed.iloc[selected_controls])
                    leaf_calls += 1; leaf_rows += len(selected_controls)
                    error = float(np.max(np.abs(control-predicted[selected_controls]))); assert error < 1e-10
                    errors.append(error)
                    event('leaf_control_completed', line=line, seed=item['seed'], condition=condition, rows=len(selected_controls), max_abs_error=error)
                assert model.num_trees() == trees and w.sha(ROOT/item['model']) == item['model_sha256']
                controls.append({'line': line, 'seed': item['seed'], 'baseline_cache_exact': True, 'baseline_center_exact': True,
                                 'leaf_sum_max_abs_errors': errors, 'source_center_unchanged': center, 'tree_count_unchanged': trees})
            summary, values = sensitivity_summary(metadata, raw)
            results[line] = summary; values.to_parquet(OUT/f'sensitivity_{line}.parquet', index=False)
            np.savez(OUT/f'raw_arrays_{line}.npz', raw=raw, centers=np.asarray(centers))
            print(json.dumps({'line': line, 'selected': len(metadata), 'summary': [{k: r[k] for k in ['condition', 'changed_rows', 'ratio_quantiles', 'material_dependency_flag']} for r in summary]}), flush=True)
        assert calls <= 27 and rows <= 1728 and leaf_calls <= 27 and leaf_rows <= 216
        assert all(w.sha(ROOT/path) == value for path, value in plan['sources'].items())
        p6 = w.read(P6/'report.json'); assert w.sha(ROOT/p6['CSV']['path']) == p6['CSV']['sha256']
        report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P8frozen_source_exposure_probe_complete',
                  'results': results, 'controls': controls, 'actual_raw_prediction_calls': calls, 'primary_raw_prediction_rows': rows,
                  'actual_leaf_control_calls': leaf_calls, 'leaf_control_rows_separate': leaf_rows,
                  'new_model_fits': 0, 'new_C0fits': 0, 'new_calibrationfits': 0, 'new_finaltestprices': 0,
                  'new_submissions': 0, 'new_predictive_price_families': 0, 'feature_removal_adopted': False,
                  'P6_CSV_unchanged': True, 'private_improvement_established': False, 'formal_promotion': False,
                  'submission_allowed': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
                  'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits']}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'primary_rows': rows, 'leaf_rows': leaf_rows, 'new_fits': 0, 'new_prices': 0, 'new_submissions': 0}))
    except Exception as exc:
        dump(OUT/f'failure_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.json',
             {'exception': type(exc).__name__, 'message': str(exc), 'raw_calls': calls, 'primary_rows': rows,
              'leaf_calls': leaf_calls, 'leaf_rows': leaf_rows,
              'next': 'Preserve outputs and reconcile actual events; no blind repeat source queries'})
        raise
    finally:
        for module, name, old in reversed(guards): setattr(module, name, old)
        n.set_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    plan = w.read(PLAN); saved = w.read(OUT/'report.json')
    assert all(w.sha(ROOT/path) == value for path, value in plan['sources'].items())
    original_booster = lgb.Booster; before = w.sha(OUT/'events.jsonl')
    def reject(*args, **kwargs): raise AssertionError('Model loading/prediction forbidden during P8saved-array replay')
    lgb.Booster = reject
    try:
        for scope in plan['scopes']:
            line = scope['line']; data = np.load(OUT/f'raw_arrays_{line}.npz'); metadata = pd.read_parquet(ROOT/scope['metadata'])
            assert np.array_equal(data['centers'], np.array([a['center'] for a in scope['models']]))
            summary, values = sensitivity_summary(metadata, data['raw'])
            assert summary == saved['results'][line] and values.equals(pd.read_parquet(OUT/f'sensitivity_{line}.parquet'))
        assert w.sha(OUT/'events.jsonl') == before and all(w.sha(ROOT/path) == value for path, value in plan['sources'].items())
    finally: lgb.Booster = original_booster
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P8saved_array_replay_exact_without_model_loading',
               'all3lines_exact': True, 'model_loading_forbidden': True, 'new_source_inference_rows': 0,
               'new_model_fits': 0, 'new_prices': 0, 'new_submissions': 0, 'events_unchanged': True,
               'report_sha256': w.sha(OUT/'report.json')}
    dump(OUT/'replay_report.json', receipt); print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay']); args = parser.parse_args()
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
