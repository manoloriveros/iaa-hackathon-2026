"""Guarda el adverso P26 y cuenta solo el aprendizaje realmente nuevo."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P26_validacion_ausencias_20261026'
INDEX = R/'registro/semana2_ausencias_validacion_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P26_VALIDACION_AUSENCIAS.md'
spec = importlib.util.spec_from_file_location('p26_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    raw = w.read(OUT/'report.json'); context = w.read(OUT/'P26_context_report.json')
    replay = w.read(OUT/'P26_replay_context.json'); cohort = w.read(OUT/'cohort_report.json')
    assert not context['all_exploratory_gates_pass']
    assert context['raw_engine_report_sha256'] == w.sha(OUT/'report.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'P26_context_report.json')
    assert replay['raw_engine_replay_sha256'] == w.sha(OUT/'replay_report.json')
    assert replay['new_fits'] == replay['new_resampling'] == replay['new_source_queries'] == 0
    events = [json.loads(x) for x in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]
    calls = Counter(); primary = Counter(); adverse = Counter()
    for event in events:
        if event['kind'] == 'closed_completed':
            calls[event['role']] += 1
            (primary if event['role'] == 'primary' else adverse).update(event['constants'])
    assert calls == {'primary': 30, 'poison': 30} and primary == adverse
    assert primary['new_source_component_calls'] == 30 and primary['new_residual_stage_calls'] == 40
    number = sum(primary[k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    now = datetime.now(timezone.utc).isoformat()
    next_unit = ('P27: inspect existing frequency/severity/peril recipes and their response/exposure/reporting contracts before considering a distinct standard source model. '
        'Use bounded existing B00-B20and phase2FS/FSp/tanda1/tanda8/tanda9recipes, preserve their adverse results and avoid rerunning them. '
        'Establish whether an untied count/severity model under current source2021-2024/eCost is genuinely new and identifiable with saved reporting objects. '
        'Never derive claim counts from aggregate positive T0, treat cost completion as frequency completion, or reuse absent C0ancestry. '
        'Inspect row/year/group/response/source hashes and missing dependencies only; no fitting, source inference, new target scores or2025prices in this readiness unit. '
        'If an equivalent recipe exists, reuse its evidence; if prerequisites fail, document the missing contract rather than fit an arbitrary offset. '
        'Do not search P25mask rates/seed/line mixtures or lift floors from its weak P26point gain. Keep B00/F3c and2024open/adaptive.')
    text = '# P26: el punto global favorable no resiste las guardas privadas\n\nCodex, '+now+'. '
    text += ('Se contrastó la receta preinscrita: relatividades fuente P25 con la misma mezcla50/50, calibración S2 y media H1/G3. '
        'La fuente no volvió a entrenarse. Los resultados se comparan con el algoritmo propio reproducible A1S/S2/H1, no con una reproducción exacta de F3c.\n\n')
    text += '| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for evaluation in ['POOLED', 'TRANSFER']:
        a = raw['results'][evaluation]['NOMINAL']
        text += f'| {evaluation} | {a["delta"]:+.7f} | [{a["bootstrap95"][0]:+.7f}; {a["bootstrap95"][1]:+.7f}] | {a["post31_delta"]:+.7f} | {a["worst_cell_delta"]:+.7f} |\n'
    text += ('\nEl combinado y la transferencia mejoran en punto, con intervalos que incluyen cero. '
        'Cuatro folds combinados y ambos años son positivos; no se alcanza el mínimo incremental registrado y la ganancia cambia de signo al retirar los31grupos más favorables. '
        'También falla el piso combinado por celda. No se adopta ni se envía la variante; tampoco se retira de las alternativas.\n\n')
    text += '| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |\n|---|---:|---|---:|---|\n'
    for name in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
        a = next(x for x in cohort['comparisons'] if x['evaluation'] == 'POOLED' and x['cohort'] == name)
        b = next(x for x in cohort['comparisons'] if x['evaluation'] == 'TRANSFER' and x['cohort'] == name)
        text += f'| {name} | {a["delta"]:+.7f} | [{a["marginal95"][0]:+.7f}; {a["marginal95"][1]:+.7f}] | {b["delta"]:+.7f} | [{b["marginal95"][0]:+.7f}; {b["marginal95"][1]:+.7f}] |\n'
    text += ('\nLas tres cohortes de negocio nuevo combinadas empeoran. Sus límites inferiores marginales y de familia16incumplen el piso, '
        'aunque los puntos permanecen dentro de este. Los puntos de transferencia positivos tampoco prueban mejora privada. '
        'No se rescatan ramos, semillas o máscaras. Las bandas son exploratorias tras búsqueda adaptativa y sus colas tienen poca resolución.\n\n')
    text += '| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for scenario in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][scenario]; b = raw['results']['TRANSFER'][scenario]
        text += f'| {scenario} | {a["delta"]:+.7f} | {a["worst_cell_delta"]:+.7f} | {b["delta"]:+.7f} | {b["worst_cell_delta"]:+.7f} |\n'
    text += ('\nSe completaron30aprendizajes cerrados primarios y30controles adversos:30componentes fuente recalibrados y40etapas residuales por rol. '
        'Constantes primarias nuevas: '+str(number)+', con desglose en el recibo. Los normalizadores de aplicación se registran aparte; no son tarifas por fila independientes del lote. '
        'No se vuelven a contar los18modelos fuente y9normalizadores de P25ni N3/C0/H1reutilizados. '
        'El adaptador nuevo rechazó claves duplicadas o ausentes, año incoherente, futuro, infinitos y etiquetas en su esquema. '
        'Se reutilizaron los fixtures completos y los replays de padres que no habían cambiado, vinculados por SHA. '
        'Los30flujos reales nuevos fueron invariantes a T0/reservas retenidos alterados. El replay bloqueó aprendizaje e inferencia fuente y cotejó precios, normalizadores, draws guardados e intervalos sin remuestreo.\n\n'
        'La sensibilidad de reservas/cola mantiene precios y enlaces congelados; no acredita suficiencia de reservas ni recalibra toda la valoración de cada rama. '
        'El soporte ponderado2025insuficiente y la disponibilidad temporal de fuente/marcas siguen abiertos. '
        'No hay mejora privada acreditada ni revisión profesional independiente, conforme a la distinción de Gobernanza IAA§2.8y Documentación§3. '
        'B00/F3c y todas las alternativas se conservan;2024es desarrollo adaptativo abierto. Cero ajustes fuente/C0, inferencias2025, precios finales o envíos nuevos.\n\n'
        'Siguiente trabajo: '+next_unit+'\n\n'
        'Evidencia: '+w.rel(OUT/'P26_context_report.json')+'; '+w.rel(OUT/'cohort_report.json')+'; '+w.rel(OUT/'P26_replay_context.json')+'. '
        'Código congelado antes de calibrar:prefijo de commit e06b28b8. El informe crudo conserva el prefijo P10del motor reutilizado; el contexto identifica P26.\n')
    assert not DOC.exists(); DOC.write_text(text, encoding='utf8')
    body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P26-AUSENCIAS-RESULTADO',
        '--asunto', 'P26: mejora global pequeña, concentrada y adversa en nuevo negocio; sin adopción',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': 'P26complete_weak_point_gain_not_admitted',
        'context_report': w.rel(OUT/'P26_context_report.json'), 'context_report_sha256': w.sha(OUT/'P26_context_report.json'),
        'replay': w.rel(OUT/'P26_replay_context.json'), 'replay_sha256': w.sha(OUT/'P26_replay_context.json'),
        'document': w.rel(DOC), 'forum': json.loads(posted.stdout),
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
        'new_primary_constants': number, 'constants': dict(primary),
        'global_nominal': {c: {k: raw['results'][c]['NOMINAL'][k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for c in ['POOLED', 'TRANSFER']},
        'global_gates': context['global_gates'], 'new_business_gates': context['new_business_gates'],
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0, 'new_final_prices': 0,
        'new_submissions': 0, 'adopted': False, 'private_improvement_established': False,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True, 'next_unit': next_unit}
    archive = R/'privado'/('corte_P26_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P26_missingness_target' not in counters
    w.update(cp, {'as_of_utc': now, 'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+number,
        'phase2_private_P26_missingness_target': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
            'new_primary_constants': number, 'constant_breakdown': dict(primary),
            'new_iterative_price_fits': 0, 'new_source_fits': 0, 'new_C0_fits': 0,
            'report': receipt['context_report'], 'report_sha256': receipt['context_report_sha256']}}, archive)
    w.update(INDEX, receipt, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P26': receipt, 'next_unit': next_unit, 'last_progress_utc': now}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'private_P26': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: P26new complete target comparison, all30held poison/saved-flow replays and all global/NBguards completed; weak global point gain failed robustness and retained without adoption'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P26=receipt, next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    brief = '\n\n## Privada P26: ausencias sin mejora robusta, 26 de octubre de 2026\n\nCodex, '+now+'. ΔD²combinado+0,0003331y transferencia+0,0004342, ambos ICincluyen cero. Post31negativo y nuevo negocio combinado−0,0004072; fallan guardas. No adopción/envío.30aprendizajes cerrados primarios/30adversos, '+str(number)+' constantes primarias nuevas; fuente/C0/N3/H1reutilizados. Replay30flujos/intervalos sin ajustes/remuestreo. B00/F3cconservados,2024abierto adaptativo; mejora privada no acreditada. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, brief, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_missing_tree_validation_index': w.rel(INDEX), 'week_2_private_missing_tree_validation_report': w.rel(DOC)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'closed': True, 'new_primary_constants': number, 'adopted': False, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
