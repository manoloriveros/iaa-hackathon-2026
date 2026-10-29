"""Linaje y entradas climáticas oficiales para A1S, sin respuestas o modelos."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P35_entradas_clima_20261026'
INDEX = R/'registro/semana2_entradas_clima_A1S_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P35_ENTRADAS_CLIMA_A1S.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
sp = importlib.util.spec_from_file_location('p35_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
FIELDS = ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']
LINES = ['motor', 'buildings', 'contents']


def dump(path, value):
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, ident, subject):
    a = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', ident, '--asunto', subject, '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    return json.loads(a.stdout)


def join(rows, weather):
    assert rows.row_id.is_unique and not weather.duplicated(['address_id', 'year']).any()
    z = rows[['row_id', 'address_id', 'year']].merge(weather, on=['address_id', 'year'], how='left', validate='many_to_one', sort=False)
    assert np.array_equal(z.row_id, rows.row_id)
    assert np.isfinite(z[FIELDS].to_numpy(float)).all()
    return z[['row_id', 'year', *FIELDS]].rename(columns={v: 'annual_'+v for v in FIELDS})


def main():
    assert not OUT.exists() and not INDEX.exists(); OUT.mkdir()
    paths = [Path(__file__), R/'herramientas/preparar_nucleo_A1S.py',
        R/'registro/semana2_alcance_covariables_oficiales2025_v3.json',
        R/'src/semana2/lineas/ml_independiente_20261023/codigo/e13_clima_anual.py',
        R/'registro/semana2_mision017_fase2_tanda7_plan_v2.json',
        R/'registro/semana2_mision017_fase2_tanda8_plan_v2.json',
        ROOT/'Hackaton/Semana 1/Datos/weather.parquet', ROOT/'Hackaton/Semana 2/Datos/emerging/weather.parquet']
    paths += [HOME/f'{kind}_{market}_{line}.parquet' for line in LINES for market in ['s1', 's2'] for kind in ['matrix', 'rows']]
    paths += [HOME/f'partition_source/folds_{line}.parquet' for line in LINES]
    before = {w.rel(p): w.sha(p) for p in paths}
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Review schema/lineage for construction/occupancy/excess and missing weather features, without repeating F02value audits or P13/P22/P31/P32outcome diagnostics. Build official address/year weather-only joins.',
        'annual_climate_availability': 'Conditional retrospective competition input, not known at quote time or genuine forecast. No invented forecast or external future data.',
        'checks': ['Source and historical target keys/order complete and unique; seven finite annual fields',
            'Original structural underwriting variables already in A1S schema, no repeated outcome attribution',
            'Source train-only min/max coverage of held source and official2025covariates, descriptive only; no threshold search'],
        'sources': before, 'new_fits': 0, 'new_scores': 0, 'new_submissions': 0}
    dump(OUT/'plan.json', plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P35revisa una ausencia concreta del esquema A1S: clima anual oficial. Construcción, ocupación, desocupación, alarmas y franquicias se comprobarán solo por linaje/esquema para no repetir F02. Se preparan cruces dirección/año y coberturas de rango con covariables, sin etiquetas o modelos. E13y los GLM climáticos previos se conservan como precedentes, sin presentar esta idea como inédita. Ningún ajuste o envío,2024abierto y B00/F3c/alternativas conservados. Plan '+w.rel(OUT/'plan.json'), encoding='utf8')
    prior = post(body, 'COD-S2-20261026-PRIVADA-P35-CLIMA-ENTRADAS-PREVIO', 'P35: linaje de variables y entradas climáticas, sin modelos')
    dump(OUT/'registration.json', {'plan_sha256': w.sha(OUT/'plan.json'), 'forum': prior})
    source_weather = pd.read_parquet(ROOT/'Hackaton/Semana 1/Datos/weather.parquet', columns=['address_id', 'year', *FIELDS], filters=[('year', '<=', 2024)])
    target_weather = pd.read_parquet(ROOT/'Hackaton/Semana 2/Datos/emerging/weather.parquet', columns=['address_id', 'year', *FIELDS], filters=[('year', 'in', [2023, 2024, 2025])])
    results = []; outputs = {}
    for line in LINES:
        source = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'address_id', 'year'])
        target = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'address_id', 'year', 'is_test'])
        part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'internal_validation'])
        assert np.array_equal(source.row_id, part.row_id) and source.year.isin([2021, 2022, 2023, 2024]).all()
        assert np.array_equal(target.is_test, target.year.eq(2025))
        source_cov = join(source, source_weather); target_cov = join(target, target_weather)
        cols = pq.read_schema(HOME/f'matrix_s1_{line}.parquet').names
        required = ['voluntary_excess', 'compulsory_excess'] + (['construction_type', 'occupancy', 'days_unoccupied', 'smoke_alarms'] if line == 'buildings' else [])
        assert all(c in cols for c in required)
        assert not any('annual_' in c or 'clima_' in c or c.startswith('cl_') for c in cols)
        train = ~part.internal_validation.to_numpy(bool); coverage = []
        for field in FIELDS:
            key = 'annual_'+field; lo = float(source_cov.loc[train, key].min()); hi = float(source_cov.loc[train, key].max())
            assert lo < hi
            for role, values in [('source_held', source_cov.loc[~train, key]), ('target2025', target_cov.loc[target.is_test, key])]:
                coverage.append({'field': field, 'role': role, 'train_min': lo, 'train_max': hi,
                    'rows': len(values), 'outside_train_minmax_fraction': float(((values < lo)|(values > hi)).mean())})
        for market, z in [('s1', source_cov), ('s2_historical', target_cov.loc[~target.is_test].copy())]:
            path = OUT/f'weather_{market}_{line}.parquet'; z.to_parquet(path, index=False)
            outputs[path.name] = {'rows': len(z), 'sha256': w.sha(path)}
        results.append({'line': line, 'structural_fields_already_present': required,
            'original_source_weather_feature_count': 0, 'added_official_annual_fields': FIELDS,
            'source_rows': len(source), 'target_historical_rows': int((~target.is_test).sum()),
            'target2025_covariate_rows_only': int(target.is_test.sum()), 'coverage': coverage})
    assert before == {w.rel(p): w.sha(p) for p in paths}
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P35official_climate_inputs_ready_no_fit',
        'results': results, 'outputs': outputs, 'sources': before, 'all_keys_and_values_complete': True,
        'source_future_weather_read': False, 'outcome_or_model_objects_read': False,
        'precedents': 'E13replaced persistent weather in old T2b, source2021-2023; T7aggregateGLM and T8perilPoisson residual overlays on N3did not pass. New current source-safe A1Scarries no weather at all. Adding the same seven fields is related prior research, not a first weather idea; changed full algorithm and current observation/history/source partitions must be explicit.',
        'remaining_hypothesis': 'A same-capacity source tree can represent nonadditive annual climate/physical-risk relationships absent from current A1S. A source-held veto and full target transfer/cohort/tail gates must establish usefulness; feature presence cannot.',
        'no_calendar_prospectivity_claim': True, 'new_fits': 0, 'new_C0_fits': 0, 'new_inference': 0, 'new_scores': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(OUT/'report.json', report)
    text = '# P35: clima ausente en A1S y entradas oficiales\n\nCodex, '+report['utc']+'.\n\n'
    text += ('El esquema A1S ya incluye construcción, ocupación, desocupación, alarmas y franquicias pertinentes. No se repitieron sus diagnósticos. '
        'El clima sí falta en los tres ramos de esta fuente. Se prepararon siete columnas anuales oficiales por dirección/año, con todas las claves y valores completos, '
        'conservando filas, orden y particiones. Las entradas de aplicación guardadas contienen solo2023/2024;2025se consultó como covariables para describir cobertura, sin modelos o precios.\n\n'
        'E13ya probó clima anual en otra base, con fuente2021–2023; T7/T8probaron overlays GLM de coste/frecuencia y fallaron la estabilidad de destino. '
        'Agregar las mismas variables a A1S es una hipótesis relacionada y adaptativa, no una novedad por cambiarle el nombre. '
        'La diferencia comprobable es el núcleo actual, sus historias notificadas, offset fuente, partición por componentes y ausencia total de clima. '
        'Una eventual prueba mantendrá capacidad y rondas de los árboles, sin mayor búsqueda de parámetros. El fallo de los GLM motiva examinar representación no aditiva; no prueba que un árbol climático mejore.\n\n'
        'El clima anual es información condicional del concurso. No hay fecha de publicación o vintage que lo haga disponible al cotizar. '
        'La cobertura min/max usa solo entrenamiento fuente; los porcentajes se conservan descriptivos, sin escoger cortes para pasar. '
        'P34y los pesos finos siguen fallidos, y la fuente no resuelve el soporte de negocio nuevo emergente.\n\n'
        'Cero ajustes, C0, inferencias, scores o envíos. B00/F3c y alternativas conservados.2024es desarrollo abierto y adaptativo. '
        'Evidencia: '+w.rel(OUT/'report.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = post(body, 'COD-S2-20261026-PRIVADA-P35-CLIMA-ENTRADAS-RESULTADO', 'P35: A1S omite clima; entradas preparadas y precedentes adversos conservados')
    next_unit = 'P36: separately preregister adding only seven annual official climate variables to original A1S source trees, unchanged per-seed capacity/rounds, source-only internal groups, no importance weights. Budget9inner+9conditional full fits; source-held same-row ensemble deviance veto per line<=1.002original. Export historical components only after all source vetoes pass, then separately preregister complete target evaluation with unchanged P30gates. No2025model inference or CSVfrom this source stage.'
    receipt = {'author': 'Codex', 'utc': report['utc'], 'status': report['status'], 'report': w.rel(OUT/'report.json'),
        'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC), 'forum': posted, 'next_unit': next_unit,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0, 'goal_achieved': False, '2024_open': True}
    dump(INDEX, receipt)
    archive = R/'privado'/('corte_P35_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P35': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P35': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P35=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P35: entradas climáticas oficiales\n\nCodex, '+report['utc']+'. A1Ssin clima en los tres ramos; variables estructurales ya presentes. Cruces anuales completos, solo covariables; no se repitieron F02o atribuciones. E13/T7/T8adversos conservados; nueva prueba condicionada a una receta del algoritmo actual. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_weather_inputs_index': w.rel(INDEX), 'week_2_private_source_weather_inputs_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'all_keys_complete': True, 'new_fits': 0, 'forum': posted}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); main()
