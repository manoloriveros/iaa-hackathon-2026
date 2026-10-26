"""Cierra el contraste climático completo conservando adversos y contabilidad."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P37_validacion_clima_20261026'
INDEX = R/'registro/semana2_clima_A1S_validacion_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P37_VALIDACION_CLIMA_COMPLETA.md'
sp = importlib.util.spec_from_file_location('p37_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    raw = w.read(OUT/'report.json'); context = w.read(OUT/'P37_context_report.json')
    replay = w.read(OUT/'P37_replay_context.json'); cohort = w.read(OUT/'cohort_report.json'); climate = w.read(OUT/'range_report.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'P37_context_report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256'] == w.sha(OUT/'report.json')
    assert replay['new_fits'] == replay['new_resampling'] == replay['new_model_inference'] == 0
    calls = Counter(); primary = Counter(); adverse = Counter()
    for event in [json.loads(s) for s in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]:
        if event['kind'] == 'closed_completed':
            calls[event['role']] += 1; (primary if event['role'] == 'primary' else adverse).update(event['constants'])
    assert calls == {'primary': 30, 'poison': 30} and primary == adverse
    assert primary['new_source_component_calls'] == 30 and primary['new_residual_stage_calls'] == 40
    number = sum(primary[k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    passed = context['all_exploratory_gates_pass']; now = datetime.now(timezone.utc).isoformat()
    next_unit = ('Audit a complete local2025producer for the exact P37algorithm, including full-source annual weather features, source observation/ultimate normalization and all five H1members. Passing adaptive gates is not formal promotion or proof of private gain. Freeze code/configuration/ancestry and admission for the exact CSVhash before any further authorized public diagnostic; inspect current quota only when a candidate is admitted. Preserve B00/F3c and no automatic final selection.' if passed else
        'P38: use saved P37evidence to distinguish climate range limitations from source category handling without refitting or repeating P13/P32. First inspect existing source CatBoost recipes and current complete-model inputs; only prepare a materially distinct standard source alternative if current evidence documents a failure it can address. Preserve all gates and failed weather/weight recipes; no favorable-line rescue, ad-hoc climate extrapolation, new weights or publicscore tuning. No2025inference or upload from a failed P37.')
    text = '# P37: clima en el algoritmo completo\n\nCodex, '+now+'. '
    text += ('La prueba supera las guardas exploratorias preinscritas. Falta la revisión de producción y admisión del archivo exacto; no se publica ni promueve automáticamente.' if passed else
        'La prueba no supera todas las guardas de robustez. Se conservan los modelos y resultados; no hay adopción o nuevo envío.')
    text += ('\n\nSolo cambió la fuente A1S por los árboles de P36con siete campos climáticos anuales. Se mantuvieron mezcla50/50N3, residuales, media H1/G3y qsource. '
        'La comparación conserva objetivo, exposición, grupos y todos los criterios anteriores.\n\n'
        '| Esquema | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n')
    for evaluation in ['POOLED', 'TRANSFER']:
        a = raw['results'][evaluation]['NOMINAL']
        text += f"| {evaluation} | {a['delta']:+.7f} | [{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}] | {a['post31_delta']:+.7f} | {a['worst_cell_delta']:+.7f} |\n"
    text += '\n| Cohorte | Δ combinado | Δ transferencia |\n|---|---:|---:|\n'
    for name in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
        a = next(z for z in cohort['comparisons'] if z['evaluation'] == 'POOLED' and z['cohort'] == name)
        b = next(z for z in cohort['comparisons'] if z['evaluation'] == 'TRANSFER' and z['cohort'] == name)
        text += f"| {name} | {a['delta']:+.7f} | {b['delta']:+.7f} |\n"
    text += ('\n| Esquema | Fuera del rango wildfire fuente | Grupos con coste positivo | Δ nominal | IC95 |\n|---|---|---:|---:|---|\n')
    for a in climate['comparisons']:
        text += f"| {a['evaluation']} | {a['outside_source_wildfire_range']} | {a['positive_cost_groups']} | {a['delta']:+.7f} | [{a['marginal95'][0]:+.7f}; {a['marginal95'][1]:+.7f}] |\n"
    text += ('\nEl soporte climático se definió por los extremos empíricos de la fuente completa antes del ajuste destino. Las celdas pequeñas por ramo/año/negocio siguen visibles en el reporte. '
        'Las bandas adicionales de familia20se conservaron junto con las guardas previas de familia16, sin relajarlas. '
        'Que una fila esté dentro del rango marginal no acredita soporte multivariante, igualdad del mecanismo entre mercados o un pronóstico válido para2025. '
        'Aproximadamente23%de las covariables2025había excedido el rango wildfire de entrenamiento interno; el límite se registró antes de entrenar.\n\n'
        '| Escenario | Δ combinado | Δ transferencia |\n|---|---:|---:|\n')
    for scenario in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][scenario]; b = raw['results']['TRANSFER'][scenario]
        text += f"| {scenario} | {a['delta']:+.7f} | {b['delta']:+.7f} |\n"
    text += ('\nSe completaron30calibraciones cerradas primarias y30adversas; '+str(number)+'constantes primarias nuevas. '
        'Los18ajustes fuente P36no se cuentan otra vez. Se reutilizaron C0/N3/H1y el adaptador ya comprobado. Las nuevas membresías y el bloque métrico de rango se verificaron antes de ajustar. '
        'Los30flujos fueron invariantes al contaminar etiquetas y reservas retenidas; replay con aprendizaje e inferencia fuente bloqueados, precios y normalizadores exactos. '
        'Los puntos, intervalos y primeras multiplicidades de los contrastes de negocio y rango se reprodujeron sin remuestrear.\n\n'
        'Los grupos de bootstrap son componentes cliente/dirección. Las colas de las bandas20tienen resolución limitada con2000réplicas; no se refinó el remuestreo para cambiar la conclusión. '
        'Se mantienen ancestros fuente/observación comunes, clima retrospectivo, reserva/cola, maestros sin fecha y búsqueda adaptativa de2023/2024. '
        'La revisión propia no es validación profesional independiente ni evidencia observada de la privada. '
        'B00/F3c y todas las alternativas permanecen.2024está abierto como desarrollo adaptativo. Cero ajustes fuente/C0, inferencias2025, CSVfinales o envíos nuevos en P37.\n\n'
        'Guardas globales: '+json.dumps(context['global_gates'], ensure_ascii=False)+'. Guardas de negocio: '+json.dumps(context['new_business_gates'], ensure_ascii=False)+'. Guardas de rango: '+json.dumps(context['range_gates'], ensure_ascii=False)+'.\n\n'
        'Próximo trabajo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'P37_context_report.json')+'; '+w.rel(OUT/'range_report.json')+'; '+w.rel(OUT/'P37_replay_context.json')+'.\n')
    assert not DOC.exists(); DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    post = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P37-CLIMA-VALIDACION-RESULTADO', '--asunto', 'P37: contraste climático completo, rango y adversos conservados', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': 'P37complete_not_automatically_admitted', 'document': w.rel(DOC),
        'context_report': w.rel(OUT/'P37_context_report.json'), 'context_report_sha256': w.sha(OUT/'P37_context_report.json'),
        'replay': w.rel(OUT/'P37_replay_context.json'), 'replay_sha256': w.sha(OUT/'P37_replay_context.json'),
        'forum': json.loads(post.stdout), 'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
        'new_primary_constants': number, 'constants': dict(primary), 'all_exploratory_gates_pass': passed,
        'global_nominal': {c: {k: raw['results'][c]['NOMINAL'][k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for c in ['POOLED', 'TRANSFER']},
        'global_gates': context['global_gates'], 'new_business_gates': context['new_business_gates'], 'range_gates': context['range_gates'],
        'adopted': False, 'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0,
        'next_unit': next_unit, 'private_improvement_established': False, 'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P37_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(cp); assert 'phase2_private_P37_climate_target' not in counts
    w.update(cp, {'as_of_utc': now, 'cumulative_closed_form_constants': counts['cumulative_closed_form_constants']+number,
        'phase2_private_P37_climate_target': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_primary_constants': number,
            'constant_breakdown': dict(primary), 'new_iterative_price_fits': 0, 'new_source_fits': 0, 'new_C0_fits': 0, 'report': receipt['context_report']}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P37': receipt, 'next_unit': next_unit, 'last_progress_utc': now}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'private_P37': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: P34new support failure retained, P35weather inputs checked, P36source models fit/replayed, P37complete target and range safeguards evaluated/replayed; no unsupported upload'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P37=receipt, next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P37: contraste climático completo\n\nCodex, '+now+'. Guardas conjuntas='+str(passed)+';30calibraciones primarias/30adversas, '+str(number)+'constantes primarias nuevas. Rangos fuente fijados antes del ajuste, guardas previas conservadas; replay exacto sin aprendizaje/remuestreo. No adopción automática, inferencias2025o envíos. B00/F3c/alternativas conservados,2024abierto adaptativo. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_weather_full_validation_index': w.rel(INDEX), 'week_2_private_weather_full_validation_report': w.rel(DOC)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'closed': True, 'all_gates_pass': passed, 'new_primary_constants': number, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
