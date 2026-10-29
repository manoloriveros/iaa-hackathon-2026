"""Revisión de contratos y linaje P31; sin curvas, precios, inferencias o scores."""
from datetime import datetime, timezone
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P31_compatibilidad_puente_20261026'
INDEX = R/'registro/semana2_compatibilidad_puente_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P31_COMPATIBILIDAD_DEL_PUENTE.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
sp = importlib.util.spec_from_file_location('p31_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def functions(path):
    text = path.read_text(encoding='utf-8-sig'); tree = ast.parse(text)
    return text, {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not OUT.exists() and not INDEX.exists() and not DOC.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert phase['active_execution'] is None and not phase['active_jobs']
    OUT.mkdir()
    paths = [Path(__file__), R/'herramientas/validar_ablacion_fuente_P10.py',
        R/'herramientas/sensibilidad_congelada_media_H1.py', R/'herramientas/puente_ultimo_observado_H1.py',
        R/'herramientas/preflight_anidado_H1.py', R/'herramientas/evaluar_media_anidada_H1_v3.py',
        R/'herramientas/diagnosticar_completitud_por_riesgo_v2.py', R/'herramientas/contrastar_enlace_HET.py',
        R/'herramientas/validar_frecuencia_marca_P30.py', R/'herramientas/completar_fuente_frecuencia_P29.py',
        R/'registro/semana2_puente_ultimo_observado_H1_plan_v1.json',
        R/'registro/semana2_enlace_HET_plan_v1.json', R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json',
        BASE/'enlace_HET_20261026_v1/report.json', BASE/'puente_ultimo_observado_H1_20261026_v1/report.json',
        BASE/'preflight_anidado_H1_20261026_v1/report.json', BASE/'media_anidada_H1_20261026_v3/report.json',
        BASE/'sensibilidad_congelada_media_H1_20261026_v1/report.json',
        BASE/'P29_fuente_frecuencia_completa_20261026/report.json',
        BASE/'P29_fuente_frecuencia_completa_20261026/completion_receipt.json',
        BASE/'P30_validacion_frecuencia_marca_20261026/P30_context_report.json',
        BASE/'P30_validacion_frecuencia_marca_20261026/P30_replay_context.json']
    plan = w.read(R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json')
    for path in paths[1:10]:
        if w.rel(path) in plan['sources']: assert plan['sources'][w.rel(path)] == w.sha(path)
    driver_path = R/'herramientas/validar_ablacion_fuente_P10.py'
    text, defs = functions(driver_path)
    expressions = {node.targets[0].id: ast.unparse(node.value) for node in ast.walk(defs['run'])
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ['adapter', 'new_price']}
    assert expressions == {'adapter': 'old_price / expected_old', 'new_price': 'u * adapter'}
    observation_path = R/'herramientas/sensibilidad_congelada_media_H1.py'
    obs_text, obs_defs = functions(observation_path)
    observation_source = ast.get_source_segment(obs_text, obs_defs['completion'])
    assert "f['f_' + p]" in ast.unparse(obs_defs['completion']) and "f['s_' + p]" in ast.unparse(obs_defs['completion'])
    assert 'qg = qq @ mix' in ast.unparse(obs_defs['completion'])
    assert 'qh = np.sum(rr * qq, axis=1) / rr.sum(axis=1)' in ast.unparse(obs_defs['completion'])
    h1plan = w.read(R/'registro/semana2_puente_ultimo_observado_H1_plan_v1.json')
    nested = w.read(BASE/'media_anidada_H1_20261026_v3/report.json')
    preflight = w.read(BASE/'preflight_anidado_H1_20261026_v1/report.json')
    assert nested['complete_nested_correction_given_protected_S2base']
    assert preflight['source_profile_cross_outer_copies_exact']
    assert preflight['inherited_target_learned_prices_q_and_exposures_removed']
    source_report = w.read(BASE/'P29_fuente_frecuencia_completa_20261026/report.json')
    source_closed = w.read(BASE/'P29_fuente_frecuencia_completa_20261026/completion_receipt.json')
    assert source_closed['report_sha256'] == w.sha(BASE/'P29_fuente_frecuencia_completa_20261026/report.json')
    records = []
    for line in ['motor', 'buildings', 'contents']:
        target_path = BASE/f'P29_fuente_frecuencia_completa_20261026/historical_{line}_three_seed.parquet'
        canonical_path = BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet'
        paths += [target_path, canonical_path, HOME/f'rows_s1_{line}.parquet']
        assert source_report['outputs'][w.rel(target_path)] == w.sha(target_path)
        schema = pq.read_schema(target_path).names; canon_schema = pq.read_schema(canonical_path).names
        assert set(schema) == {'row_id', 'year', 'is_test', 'raw_log_rate', 'log_relative_A1S'}
        perils = preflight['perils'][line]
        assert all('f_'+p in canon_schema and 's_'+p in canon_schema for p in perils)
        record_paths = sorted((BASE/f'P29_fuente_frecuencia_completa_20261026/{line}').glob('*/fit_record.json'))
        assert len(record_paths) == 2*len(perils)
        for path in record_paths:
            record = w.read(path); assert record['source_scope'] == 'full developed2021-2024'
            assert record['model_sha256'] == w.sha(path.parent/'model.json')
            paths += [path, path.parent/'model.json']
        records.append({'line': line, 'historical_rows': pq.ParquetFile(target_path).metadata.num_rows,
            'persisted_new_source_columns': schema, 'persisted_peril_rates_in_new_historical_cache': False,
            'existing_canonical_FSp_perils': perils, 'new_source_model_JSONs_available': len(record_paths),
            'peril_profile_cannot_be_recovered_from_aggregate_sum_alone': True})
    now = datetime.now(timezone.utc).isoformat()
    finding = {'author': 'Codex', 'utc': now, 'status': 'P31compatibility_review_complete_no_numeric_bridge_defect_found',
        'current_adapter_expression': expressions,
        'algebra': 'old_price=U_old*mean5(R_H1_G3)*q_source; adapter=old_price/U_old; new_price=U_new*mean5(R_H1_G3)*q_source. The fixed adapter is shared by candidates, while q_source varies by row.',
        'observation_contract': {'q_global': 'Outer-fitted frequency*mean-mark mixture of outer cost curves.',
            'q_source': 'Risk-dependent weighted mean of the same outer peril cost curves; weights are the fixed canonical FSp f_p*s_p profiles, without target kappa.',
            'learning': 'Each H1/G3member learns its own protected C0, independent of outer held groups. Outer observation mapping is evaluation-only.',
            'fixed_means': 'Fixed across compared candidates, not a constant completion across insured rows.',
            'earlier_HET': 'Global/source/outer-risk links were already diagnosed and tested. They are not a new hypothesis to rediscover after P30.'},
        'prior_bridge_mathematics': h1plan['mathematics'],
        'metadata': records,
        'interpretation': ['Current new source annual-rate allocation is valid input to the declared common evaluation adapter; no arithmetic incompatibility is demonstrated.',
            'The common fixed FSp risk profile is still a modeling assumption, not identified ultimate mix or proof of private accuracy.',
            'New P29peril weights could define a different hypothesis only after legitimate component export and new contract/ancestry registration. They cannot be inferred from the aggregate cache.',
            'P30broker deterioration does not establish the observation bridge as its cause. No target, model, C0or bridge changes follow from this static review.'],
        'sources': {w.rel(path): w.sha(path) for path in paths}, 'new_fits': 0, 'new_C0_fits': 0,
        'new_model_inference': 0, 'new_predictions': 0, 'new_scores': 0, 'new_resampling': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', finding)
    next_unit = ('P32: preregister a bounded conditional-adequacy review of the saved P28source-held predictions by source business and broker/other, before another model. '
        'Use source metadata and saved candidate/constant/tree predictions, exact held-source group keys, no new source inference, fitting, target scores or2025prices. '
        'Measure observed-versus-expected cost and group concentration for all four source business/channel cells and all source years; do not select only favorable lines. '
        'Freeze any interaction screen and dominant-group sensitivity before readout. Determine whether a main-effects source limitation is actually present before considering one standard interaction; no automatic new fit or capacity from the P30target adverse. '
        'If source residuals do not support that mechanism, record it rather than tune another interaction. Preserve conditional observation/ancestry limits, B00/F3c/all alternatives and adaptive2024open.')
    text = '# P31: el puente es común entre candidatos y ya depende del riesgo\n\nCodex, '+now+'. '
    text += ('La revisión estática de contratos y artefactos no encontró un defecto numérico nuevo. '
        'El adaptador de P30es precio anterior/último anterior. Como el precio anterior es U_anterior*media5(H1/G3)*q_source, el nuevo precio es U_nuevo*la misma media*q_source. '
        'Esa regla se fijó antes de evaluar y permite sustituir relatividades anuales manteniendo el mismo contrato.\n\n'
        'q_sourceya varía por riesgo: combina las completitudes por peril de las curvas exteriores con pesos FSpf*scongelados. '
        'q_globalusa la mezcla exterior de frecuencias por marca media. La hipótesis de mezcla por riesgo ya se estudió en HET; no se repitieron sus diagnósticos ni sus ajustes. '
        'Los miembros H1/G3usan sus propios C0protegidos y el enlace exterior común es solo de evaluación. Se reutilizaron las pruebas P0/P1/P2y los replays actuales por hash.\n\n'
        'El puente observado/último también conserva el cociente de exposición redondeada/calendario y los productos de normalizadores de factores cuando se comparan las aplicaciones observada y última. '
        'P30avanza primero a último con sus nuevos normalizadores y después aplica la media y el enlace fijados. No se justifica otra renormalización observada posterior.\n\n'
        'Los tres cachés nuevos de P29conservan solo la suma anual y su relatividad,109.296filas históricas. '
        'Los30JSON por peril existen y sus metadatos corresponden a la fuente desarrollada2021–2024, pero no se persistieron tasas históricas separadas por peril en esos cachés. '
        'La suma no identifica sus pesos internos. Cambiar al perfil GLM requeriría una exportación nueva y otra hipótesis de observación, con ancestros, objetivo, comparador y coste registrados antes de predecir o puntuar. '
        'No se intercambian los f*sFSpviejos por una suma GLMnueva fingiendo que son el mismo perfil.\n\n'
        'La composición fija sigue siendo un supuesto sobre la mezcla última, y esta revisión no identifica la verdadera mezcla ni explica por sí sola el daño de broker nuevo. '
        'P30permanece sin adopción. Se corrige una posible interpretación: «enlace fijo» significa compartido entre candidatos, no uniforme entre riesgos. '
        'Se mantienen las limitaciones de fuente2024, búsqueda adaptativa, reservas/cola y soporte futuro. Cero ajustes, inferencias, precios, scores o envíos nuevos. '
        'B00/F3cy todas las alternativas se conservan,2024abierto adaptativo.\n\nPróximo trabajo: '+next_unit
        +'\n\nEvidencia: '+w.rel(OUT/'report.json')+'. La revisión inspecciona fórmulas, esquemas, metadatos y hashes; no es una nueva validación predictiva.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P31-PUENTE-COMPATIBILIDAD',
        '--asunto', 'P31: qSource ya depende del riesgo; puente común compatible, sin rescate de P30',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': finding['status'],
        'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC),
        'forum': json.loads(posted.stdout), 'next_unit': next_unit,
        'new_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_scores': 0, 'new_submissions': 0,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(INDEX, receipt); archive = R/'privado'/('corte_P31_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P31': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P31': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: common risk-dependent bridge contract traced to HET/P0/P2and actual P30driver; new-source component schema/metadata gap established without refitting or rescoring; stale delivery reason reconciled'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P31=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P31: compatibilidad del enlace, 26 de octubre de2026\n\nCodex, '+now+'. q_sourceya es por riesgo FSp y compartido entre candidatos; no se demuestra error al sustituir relatividades en P30. HET/P0/P2ya tratan esta composición y normalizadores. P29solo guarda sumas históricas; nuevos pesos por peril requerirían exportación y contrato distintos, no rescate posterior al score. Cero ajustes/inferencias/scores/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_bridge_compatibility_index': w.rel(INDEX), 'week_2_private_bridge_compatibility_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed': True, 'numeric_bridge_defect_demonstrated': False,
        'new_model_inference': 0, 'new_scores': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
