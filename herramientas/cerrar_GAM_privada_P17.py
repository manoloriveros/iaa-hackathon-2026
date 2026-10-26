"""Conserva el adverso GAM y precisa el contraste de calibración siguiente."""
from pathlib import Path
from datetime import datetime, timezone
import collections
import importlib.util
import json
import math
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P17_validacion_GAM_20261026'
sp = importlib.util.spec_from_file_location('p17_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'context_report.json'); raw = w.read(OUT/'report.json'); replay = w.read(OUT/'P17_replay_context.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'context_report.json') and replay['paired_secondary_intervals_exact']
    assert not all(d['primary_diagnostic_gates'].values())
    totals = {'primary': collections.Counter(), 'poison': collections.Counter()}; calls = collections.Counter()
    for line in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines():
        a = json.loads(line)
        if a['kind'] == 'closed_completed': totals[a['role']].update(a['constants']); calls[a['role']] += 1
    assert calls == {'primary': 30, 'poison': 30} and totals['primary'] == totals['poison']
    number = sum(totals['primary'][k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels']); assert number == 670
    levels = []
    for cohort in ['POOLED', 'TRANSFER']:
        for line in ['motor', 'buildings', 'contents']:
            center = w.read(BASE/f'P16_GAM_bedrooms_lineal_20261026/{line}/application.json')['source_center']
            components = [w.read(OUT/f'{cohort}_{line}_{k}/learning.json')['component'] for k in range(5)]
            values = [a['level'] for a in components]
            levels.append({'cohort': cohort, 'line': line, 'learned_line_levels': values,
                           'max_min_ratio': max(values)/min(values),
                           'normalized_component_target_to_absolute_source': [v/math.exp(center) for v in values],
                           'component_only_not_whole_algorithm': True})
    (OUT/'component_level_metadata.json').write_text(json.dumps(levels, indent=2), encoding='utf8')
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P17_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('P18: preregister a simpler joint ridge-Tweedie calibration prototype on fixed absolute '
                 'GAMsource annual rates, with one unpenalized country intercept, six regularized line/business '
                 'cell main effects and only existing G3target covariates by line (motor gender; contents '
                 'gender/work-from-home/marketing). Same alpha1/no search, training-only encoders/scales. '
                 'Use ratio target T0/m0 and sqrt(m0)weights with m0=source_abs_rate*roundedE*qSource; '
                 'prove exact cost-deviance equivalence and full grouped learner/JSON/poison/batch flow on synthetic data. '
                 'This is a new complete lower-complexity algorithm, not a one-change causal ablation: '
                 'no N3blend, target band corrections or five-member H1ratio at forward, and no application '
                 'cohort normalizers. Forward annual source rate*calendarE*learned factor; evaluate with '
                 'same frozen qSource and scenarios as incumbent, keeping minimum/gates. Reuse saved outer '
                 'C0objects with exact membership; at most10joint primary GLMs(5pooled+5transfer)and10poison '
                 'controls, zero source/C0fits or futureinference. Primary versus A1S/S2/H1, secondary versus '
                 'P17GAM/S2/H1with paired draws. Document pooling assumption and source-level uncertainty; '
                 'the existing credibility already uses positive claims, not row count. Do not claim a '
                 'counting bug or use held-oracle levels. Freeze code/config/cost/forum before real fit. '
                 'No uploads, line selection or publicscore tuning; B00/F3c/all alternatives preserved,2024open.')
    note = '\n\n## Privada P17: GAM mejora el punto, pero no supera estabilidad, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completó el contraste preinscrito del GAMcon curvas5/4/3y dormitorios lineales, en el algoritmo completo S2/H1.\n\n'
    note += '| Nominal frente a A1S/S2/H1 | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort, a in d['primary_nominal'].items():
        note += f'| {cohort} | {a["delta"]:.7f} | [{a["bootstrap95"][0]:.7f}, {a["bootstrap95"][1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nEl punto mejora en ambos años y al menos cuatro folds, y la transferencia es positiva. '
             'Persisten intervalos compatibles con cero, Post31negativo y pérdidas por celda. '
             'El mínimo0,002no se cumple en el combinado. No se adopta ni se envía el GAM.\n\n')
    note += '| Nominal frente al GLM con indicadores | Δ D² | IC95 emparejado | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort, result in d['secondary_vs_linear_MI'].items():
        a = result['NOMINAL']; ci = a['bootstrap95_paired_existing_draws']
        note += f'| {cohort} | {a["delta"]:.7f} | [{ci[0]:.7f}, {ci[1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nLa comparación secundaria de transferencia es prometedora en punto, pero su intervalo '
             'también incluye cero. Se obtuvieron diferencias de draws existentes con los mismos grupos, '
             'outcomes, orden, semillas y denominadores; no hubo otro remuestreo para el secundario. '
             'No se atribuye causalmente la diferencia a una curva o variable concreta.\n\n')
    note += '| Escenario frente a referencia | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for name in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][name]; z = raw['results']['TRANSFER'][name]
        note += f'| {name} | {a["delta"]:.7f} | {a["worst_cell_delta"]:.7f} | {z["delta"]:.7f} | {z["worst_cell_delta"]:.7f} |\n'
    note += ('\nLas sensibilidades no resuelven los pisos; reservas75%empeora hasta−0,0221378en una '
             'celda de transferencia. Son precios congelados bajo objetivos/enlaces fijados, no '
             'recalibraciones completas de cada valoración. Todo adverso queda guardado.\n\n'
             'La inspección de parámetros guardados muestra que el nivel de la mitad fuente de '
             'edificios varía1,20veces entre folds de transferencia, frente a1,14en autos y1,06en '
             'contenidos. Son parámetros de un componente, no niveles de todo el algoritmo. '
             'La credibilidad existente ya cuenta siniestros con coste positivo en sus pesos, '
             'no filas; no se ha encontrado un fallo de conteo. P13ya distinguió pérdida de '
             'nivel y de asignación. No corresponde añadir capacidad fuente para corregir '
             'sin más una calibración de nivel inestable.\n\n'
             'Siguiente contraste: un algoritmo más sencillo, GAMfuente absoluto con calibración '
             'Tweedie conjunta regularizada. Un intercepto país y ajustes de ramo/negocio compartirán '
             'información, con penalización fija y solo las covariables destino de G3ya usadas. '
             'No conservará N3ni la corrección de cinco miembros o normalizadores de cartera al '
             'predecir: es otra receta completa, no una ablación de un único efecto. La hipótesis '
             'de compartir escala entre ramos necesita validación y puede fallar si sus diferencias '
             'entre mercados son reales. No se ha aplicado todavía una nueva tarifa. '
             'El prototipo y el criterio se preinscribirán antes de ajustar.\n\n'
             'Se hicieron treinta calibraciones cerradas primarias,670constantes de precio y treinta '
             'controles adversos separados. La alteración completa de T0/reserva retenidos dejó '
             'iguales artefactos y precios últimos. El momento se cotejó por sumas independientes '
             'y los treinta replays reales guardados fueron exactos con aprendizaje/inferencia fuente '
             'bloqueados; el secundario emparejado también pasó replay. Cero modelos fuente, C0, '
             'inferencias2025, precios finales o envíos en P17.\n\n'
             'B00/F3c/P6y todos los fallos/alternativas permanecen.2024está abierto adaptativo; '
             'fuente y marcas incluyen2024, y el soporte ponderado2025sigue insuficiente. No se '
             'acredita mejora privada ni validación profesional independiente.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'context_report.json')+'; '+w.rel(OUT/'P17_replay_context.json')+'; '+w.rel(OUT/'component_level_metadata.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P17_VALIDACION_GAM.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P17-GAM-RESULTADO', '--asunto',
                             'P17: GAM sin estabilidad suficiente; calibración conjunta estándar como siguiente contraste',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k != 'secondary_vs_linear_MI'}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'context_report.json'), report_sha256=w.sha(OUT/'context_report.json'),
                   replay=w.rel(OUT/'P17_replay_context.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   secondary_nominal={c: a['NOMINAL'] for c, a in d['secondary_vs_linear_MI'].items()},
                   primary_constants=number, primary_constant_breakdown=dict(totals['primary']),
                   adverse_constant_breakdown_separate=dict(totals['poison']), GAM_adopted=False, next_unit=next_unit)
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp); assert 'phase2_private_P17_GAM_validation' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+number,
                  'phase2_private_P17_GAM_validation': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
                    'unique_primary_price_constants': number, 'constant_breakdown': dict(totals['primary']),
                    'secondary_new_resampling': 0, 'new_source_fits': 0, 'new_C0_fits': 0,
                    'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(INDEX := R/'registro/semana2_GAM_validacion_privada_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'; w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P17': receipt, 'next_unit': next_unit}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P17': receipt, 'mission_private_priority': w.read(priority), 'next_unit': next_unit,
                     'last_goal_turn_classification': 'progress: complete additive source algorithm evaluated/replayed; point gains but concentration/NB floors fail; simpler joint calibration hypothesis specified'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P17=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_GAM_validation_index': w.rel(INDEX), 'week_2_private_GAM_validation_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'adopted': False, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
