"""Recupera componentes Q1 fuente ya ajustados, sin entrenamiento ni precios finales."""
from datetime import datetime, timezone
import argparse
import gc
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OLD = BASE/'tanda3_20261025_v3'; SOURCE = BASE/'fuente_f2_2024_v2'; TARGET = BASE/'linaje_T2b_v1'
OUT = BASE/'P38_CatBoost_guardado_20261026'
PLAN = R/'registro/semana2_CatBoost_guardado_privada_plan.json'
INDEX = R/'registro/semana2_CatBoost_guardado_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P38_CATBOOST_GUARDADO.md'
sys.path.insert(0, str(R/'src')); sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import catboost as cb
from scipy.special import logsumexp
from threadpoolctl import threadpool_limits
sp = importlib.util.spec_from_file_location('p38_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def sources():
    paths = [Path(__file__), R/'herramientas/mision017_fase2_tanda3_v3.py',
        R/'src/semana2/fuente_f2_2024_cb.py', R/'registro/semana2_mision017_fase2_tanda3_plan_v3.json',
        R/'registro/semana2_robustez2023_ciclo18_plan.json', OLD/'price_report.json', OLD/'validation_v1/report.json', SOURCE/'report.json',
        BASE/'P37_validacion_clima_20261026/completion_receipt.json']
    for line in LINES:
        paths += [OLD/f'CB_{line}.cbm', OLD/f'CB_{line}_metadata.json', OLD/f'raw_CB_{line}.parquet',
            SOURCE/f'{line}.parquet', TARGET/f'features_{line}.parquet', HOME/f'rows_s1_{line}.parquet',
            BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet']
    return paths


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    OUT.mkdir()
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Existing_Q1_source_CatBoost_component_recovery_not_a_new_fit',
        'necessity': 'Do not blindly repeat earlier CatBoost or add source capacity. Three saved source2021-2024Q1models already exist. Their N0/Q1/Q2/Q3target calibration is not the current complete S2/H1algorithm. Reuse the exact teachers to prepare a distinct whole-algorithm assay.',
        'precedents': 'C18Ordered2023GLM-residual and E15/T3CatBoost adverse results remain. T3Q1localD2was belowN0; Q2/Q3small average gains did not authorize a robust delivery. No family or source holdout novelty claimed.',
        'scope': 'Load exactly3existing models, nofit. Use exact saved sourceF2features/categorical conversion and source rows2021-2024. VerifyT0/e_cost against current A1Ssource rows and hashes, not a newC0. Reproduce saved historical2023/2024annual_CBvalues, then center raw deltas on source exposure_model for compatibility.',
        'relative': 'raw delta minus log(weighted source mean exp(delta)), weights=unchanged A1Ssource exposure_model. Initial source rate is already fixed in the saved model metadata; raw_log_rate=log(initial)+rawdelta. The center is covariate/model only, not reestimation of the pricing objective.',
        'controls': ['All source/model/metadata hashes unchanged and exact parameter/source lineage.',
            'No2025rows before prediction; historical keys/years match all current canonical rows.',
            'Existing CBannual cache replay by model; save/load/reversal and leaf-value sum by another method.',
            'Source centering by logsumexp and scalar summation; do not call historical producers which fit curves/models.',
            'Block CatBoostRegressor.fit during every model read/application.'],
        'budget': {'new_source_fits': 0, 'new_C0_fits': 0, 'new_target_fits': 0, 'new_scores': 0, 'new2025inference': 0, 'source_covariate_centers': 3, 'new_submissions': 0},
        'limits': ['Existing full-source models have no new independent source-held veto; do not fake a held-source assessment on their training rows.',
            'Recovery does not overcome old model failures or certify private benefit; whole-target protected comparison must be separately preregistered.',
            'Underlying F2features use persistent climate and undated master information, with source2024and snapshot/reporting assumptions.',
            'One saved model perline, not a three-seed ensemble. Compatibility filenames must state that difference.'],
        'technical_sources': ['https://catboost.ai/docs/en/concepts/python-reference_catboost', 'https://catboost.ai/docs/en/concepts/loss-functions-regression'],
        'sources': {w.rel(p): w.sha(p) for p in sources()}, '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P38recupera exactamente los3CatBoostfuente Q1ya ajustados y guardados, sin volver a entrenar. Se conservarán sus resultados adversos T3/C18/E15; no se presenta CatBoost como familia nueva. Se cotejarán fuente/objetivo/exposición, código/metadatos, predicción histórica guardada, suma de hojas y centro relativo para el adaptador actual. Un modelo por ramo, no3semillas. No se hará un falso veto fuente sobre sus propias filas de entrenamiento. Esta recuperación no adopta Q1ni evalúa aún el algoritmo completo; un contraste posterior S2/H1requiere receta previa y todas las guardas privadas. Cero ajustes/C0/scores/precios2025o envíos,2024abierto y B00/F3c/alternativas conservados. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P38-CB-RECUPERACION-PREVIO', '--asunto', 'P38: recuperar CatBoost fuente guardado antes de repetir entrenamiento', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P38registered_existing_models_only', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps({'registered': True, 'new_fits': 0, 'forum': receipt['forum']}))


def raw_leaf_sum(model, pool):
    leaves = model.calc_leaf_indexes(pool, thread_count=2)
    counts = model.get_tree_leaf_counts(); offsets = np.r_[0, np.cumsum(counts)[:-1]]
    values = model.get_leaf_values(); scale, bias = model.get_scale_and_bias()
    return scale*np.sum(values[leaves+offsets[None, :]], axis=1)+bias


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in sources()}
    oldsp = importlib.util.spec_from_file_location('p38_old_matrix_only', R/'herramientas/mision017_fase2_tanda3_v3.py')
    old = importlib.util.module_from_spec(oldsp); oldsp.loader.exec_module(old)
    def reject(*args, **kwargs): raise AssertionError('No model fitting during P38existing teacher recovery')
    cb.CatBoostRegressor.fit = reject
    results = []; outputs = {}
    for line in LINES:
        metadata = w.read(OLD/f'CB_{line}_metadata.json'); path = SOURCE/f'{line}.parquet'
        assert w.sha(path) == metadata['source_sha256'] and w.sha(OLD/f'CB_{line}.cbm') == metadata['model_sha256']
        assert metadata['params'] == {**old.CONFIG, 'l2_leaf_reg': 10/np.sqrt(metadata['scale'])}
        columns = metadata['columns']; categories = metadata['catcols']
        f = pd.read_parquet(path, columns=list(dict.fromkeys(['row_id', 'year', 'T0', 'e_cost', *columns])))
        a1 = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'T0', 'e_cost', 'exposure_model'])
        assert f.year.isin([2021, 2022, 2023, 2024]).all() and len(f) == metadata['source_rows']
        assert np.array_equal(f.row_id, a1.row_id) and np.array_equal(f.T0, a1.T0) and np.array_equal(f.e_cost, a1.e_cost)
        model = cb.CatBoostRegressor(); model.load_model(str(OLD/f'CB_{line}.cbm'))
        source_x = old.matrix(f, columns); raw = model.predict(cb.Pool(source_x, cat_features=categories), prediction_type='RawFormulaVal', thread_count=2)
        weights = a1.exposure_model.to_numpy(float); center = float(logsumexp(raw, b=weights)-np.log(weights.sum()))
        scalar = math.log(math.fsum(np.exp(raw)*weights)/math.fsum(weights))
        assert abs(center-scalar) < 1e-12 and abs(np.average(np.exp(raw-center), weights=weights)-1) < 2e-12
        t = pd.read_parquet(TARGET/f'features_{line}.parquet', columns=list(dict.fromkeys(['row_id', 'year', *columns])), filters=[('year', 'in', [2023, 2024])])
        assert t.year.isin([2023, 2024]).all() and t.row_id.is_unique
        canonical = pd.read_parquet(BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet', columns=['row_id', 'year'])
        assert set(t.row_id) == set(canonical.row_id)
        cx = canonical.set_index('row_id').loc[t.row_id]; assert np.array_equal(cx.year, t.year)
        tx = old.matrix(t, columns); pool = cb.Pool(tx, cat_features=categories)
        applied = model.predict(pool, prediction_type='RawFormulaVal', thread_count=2)
        cached = pd.read_parquet(OLD/f'raw_CB_{line}.parquet').set_index('row_id').loc[t.row_id]
        annual = metadata['initial_source_rate']*np.exp(applied)
        relative_error = float(np.max(np.abs(annual/cached.annual_CB.to_numpy()-1)))
        assert relative_error < 3e-12
        sample = np.unique(np.linspace(0, len(t)-1, 32, dtype=int)); loaded = cb.CatBoostRegressor(); loaded.load_model(str(OLD/f'CB_{line}.cbm'))
        check = loaded.predict(cb.Pool(tx.iloc[sample], cat_features=categories), prediction_type='RawFormulaVal', thread_count=2)
        reversed_check = loaded.predict(cb.Pool(tx.iloc[sample[::-1]], cat_features=categories), prediction_type='RawFormulaVal', thread_count=2)
        assert np.allclose(check, applied[sample], rtol=2e-13, atol=2e-13) and np.array_equal(check, reversed_check[::-1])
        leaf_error = float(np.max(np.abs(raw_leaf_sum(loaded, cb.Pool(tx.iloc[sample[:6]], cat_features=categories))-check[:6])))
        assert leaf_error < 1e-10
        result = t[['row_id', 'year']].copy(); result['is_test'] = False
        result['raw_log_rate'] = np.log(metadata['initial_source_rate'])+applied; result['log_relative_A1S'] = applied-center
        assert np.isfinite(result[['raw_log_rate', 'log_relative_A1S']].to_numpy()).all()
        output = OUT/f'historical_{line}_three_seed.parquet'; result.to_parquet(output, index=False); outputs[w.rel(output)] = w.sha(output)
        record = {'line': line, 'source_rows': len(f), 'historical_rows': len(t), 'one_existing_model_not_three_seeds': True,
            'source_T0_e_cost_keys_exact_current_A1S': True, 'source_center': center, 'source_center_scalar_exact': True,
            'old_annual_cache_relative_error': relative_error, 'save_load_reversal_parity': True, 'leaf_sum_error': leaf_error,
            'CatBoost_fit_blocked': True, 'model_sha256': metadata['model_sha256'], 'new_fits': 0, 'new2025inference': 0}
        dump(OUT/f'application_{line}.json', record); results.append(record)
        print(json.dumps({'recovered': line, 'historical_rows': len(t), 'cache_error': relative_error, 'new_fits': 0}), flush=True)
        del f, a1, source_x, raw, model, loaded, t, tx, pool; gc.collect()
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in sources()}
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P38existing_CB_components_recovered_no_fit', 'results': results, 'outputs': outputs,
        'new_source_fits': 0, 'new_source_centers': 3, 'new_C0_fits': 0, 'new_target_fits': 0, 'new_scores': 0, 'new2025inference': 0, 'new_submissions': 0,
        'source_gate_pass_claimed': False, 'old_adverse_results_preserved': True, 'source_identity': 'One fixed600tree model perline, not three seeds despite compatibility filenames.',
        'plan_sha256': w.sha(PLAN), '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    next_unit = 'P39: preregister a whole original50/50S2/H1comparison replacing only source relativity by the exact existing Q1CatBoost model perline. Keep all P30global/business/family16gates, C0/N3/H1/qsource and partitions. No new source fits or fake source-held veto. First freeze actual historical keys/bindings and prior adverse calibration differences; then30closed learners+30poison controls, no2025inference or upload before a supported exact-file admission.'
    text = '# P38: componentes CatBoost ya guardados\n\nCodex, '+report['utc']+'.\n\n'
    text += ('Se recuperaron exactamente los tres modelos fuente Q1guardados, uno por ramo. No hubo entrenamiento. Los modelos y las fuentes coinciden con sus metadatos; '
        'T0, exposición de coste y claves fuente coinciden con las entradas actuales A1S. Se reprodujeron las tasas anuales históricas guardadas, '
        'la aplicación de los modelos por otra carga y orden, y la suma de valores de hojas. Los nuevos centros fuente se comprobaron por suma escalar.\n\n'
        'T3Q1ya perdió frente a N0con su calibración anterior; las mezclas Q2/Q3tampoco justificaron entrega. C18/E15y todos esos adversos permanecen. '
        'La recuperación prepara una comparación del algoritmo S2/H1actual, con adaptaciones y media distintas. No demuestra que CatBoost mejore, '
        'ni se hace pasar una evaluación de entrenamiento por holdout fuente independiente.\n\n'
        'Cada archivo de compatibilidad llamado three_seed contiene un único modelo ya existente por ramo. No hay selección o promedio de semillas. '
        'Se bloquearon las llamadas fit. Cero ajustes, C0, puntuaciones o predicciones2025. Se calcularon tres centros relativos con fuente/modelos fijos. '
        'El clima de estos modelos es persistente, según su receta original; no se incorpora el clima anual P36fallido. '
        'B00/F3c/alternativas conservados,2024abierto adaptativo. No hay validación privada o profesional independiente.\n\n'
        'Próximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P38-CB-RECUPERACION-RESULTADO', '--asunto', 'P38: modelos Q1recuperados sin entrenamiento; falta el contraste completo', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': report['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'forum': json.loads(p.stdout), 'next_unit': next_unit, 'new_fits': 0, 'new_submissions': 0, 'goal_achieved': False, '2024_open': True}
    archive = R/'privado'/('corte_P38_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P38': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P38': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P38=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P38: CatBoost guardado recuperado\n\nCodex, '+receipt['utc']+'.3modelos fuente Q1recuperados, tasas históricas/hojas/centros comprobados, cero entrenamiento/C0/scores2025/envíos. Un modelo por ramo, no3semillas. Adversos previos conservados; falta comparación completa S2/H1. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_saved_CB_source_index': w.rel(INDEX), 'week_2_private_saved_CB_source_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'new_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); p = argparse.ArgumentParser(description=__doc__); p.add_argument('mode', choices=['prepare', 'run']); a = p.parse_args()
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run}[a.mode]()
