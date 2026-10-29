"""Conserva el adverso de indicadores y concreta el siguiente contraste estándar."""
from pathlib import Path
from datetime import datetime, timezone
import collections
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P15_validacion_ausentes_20261026'
sp = importlib.util.spec_from_file_location('p15_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'context_report.json'); raw = w.read(OUT/'report.json'); replay = w.read(OUT/'P15_replay_context.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'context_report.json') and replay['paired_secondary_intervals_exact']
    assert not all(d['primary_diagnostic_gates'].values())
    totals = {'primary': collections.Counter(), 'poison': collections.Counter()}; calls = collections.Counter()
    for line in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines():
        a = json.loads(line)
        if a['kind'] == 'closed_completed': totals[a['role']].update(a['constants']); calls[a['role']] += 1
    assert calls == {'primary': 30, 'poison': 30} and totals['primary'] == totals['poison']
    number = sum(totals['primary'][k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    assert number == 670
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P15_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('P16preflight: fixed additive source main effects on current2021-2024contract, retaining P14missing flags '
                 'and alpha1; no interactions or hypersearch. Reuse the historical sourceGAMfixed risk-variable list '
                 'as a domain specification rather than select from target gains: motor ncb_years,vehicle_age,years_licensed,'
                 'vehicle_value_group,engine_size_cc; buildings log_si,prop_age,distance_to_river_km,elevation_m; '
                 'contents log_si,bedrooms,distance_to_river_km,elevation_m. Use4source-only quantileknots,degree2,'
                 'constant extrapolation and source standardized basis, no source2023fit repetition. Preserve direct '
                 'columns/offsets/C0and all remaining linear/categorical features. Before fitting, demonstrate JSONbasis '
                 'serialization, endpoint/missing treatment, gradient and complete synthetic fit/forward replay; then '
                 'freeze code,hypothesis,cost and forum. At most3sourcefits; separately registered complete comparison '
                 'versus incumbent primary and P15linear-MIsecondary. P13allocated-loss failures justify testing functional '
                 'flexibility, but do not prove nonlinear causality; P15did not validate missingness as the cause. '
                 'No oraclelevels, line selection, new2025prices or uploads until appropriate review. Preserve alladverses '
                 'and private priority,2024adaptiveopen. Version this completed block locally without claiming full '
                 'historical repository regularization.')
    note = '\n\n## Privada P15: indicadores sin mejora robusta establecida, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Se cerró la comparación completa de GLM4_MI/S2/H1frente al '
             'algoritmo A1S/S2/H1y, secundariamente, al GLMlineal P12. Los mismos grupos, C0, N3, exposición, '
             'mitades fuente/N3y media de cinco cocientes H1/G3se mantuvieron.\n\n')
    note += '| Nominal frente a A1S/S2/H1 | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort, a in d['primary_nominal'].items():
        note += f'| {cohort} | {a["delta"]:.7f} | [{a["bootstrap95"][0]:.7f}, {a["bootstrap95"][1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nEl punto combinado mejora ligeramente y ambos años contribuyen positivamente, pero solo '
             'tres folds mejoran, el intervalo incluye cero y Post31es negativo. La transferencia de '
             'destino2023a2024empeora. En edificios nuevos2024la pérdida es −0,0111331en el combinado '
             'y −0,0161575en transferencia. La variante incumple los criterios primarios conservados.\n\n')
    note += '| Nominal frente a GLM sin indicadores | Δ D² | IC95 emparejado | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort, result in d['secondary_vs_plain_GLM'].items():
        a = result['NOMINAL']; ci = a['bootstrap95_paired_existing_draws']
        note += f'| {cohort} | {a["delta"]:.7f} | [{ci[0]:.7f}, {ci[1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nLos indicadores no acreditan una mejora consistente ni siquiera frente al GLMsin '
             'indicadores. La brecha de ausentes y la colisión de representación siguen siendo hechos, '
             'pero no se ha establecido que expliquen el adverso. Los intervalos secundarios se '
             'obtuvieron restando draws con los mismos grupos, etiquetas, orden, semillas y denominadores. '
             'Se verificaron las diferencias con las pérdidas directas y un replay de los arrays; '
             'no se repitió el remuestreo anterior. Son intervalos condicionales exploratorios, '
             'no una replicación independiente ni ajuste global por toda la búsqueda.\n\n')
    note += '| Escenario frente a referencia | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for name in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][name]; z = raw['results']['TRANSFER'][name]
        note += f'| {name} | {a["delta"]:.7f} | {a["worst_cell_delta"]:.7f} | {z["delta"]:.7f} | {z["worst_cell_delta"]:.7f} |\n'
    note += ('\nLas sensibilidades fijadas no resuelven los pisos: reservas75%alcanza −0,0198787en la '
             'peor celda de transferencia. Son precios congelados con objetivo/enlace de observación '
             'variados, sin nuevas calibraciones completas de cada valoración. Todos los adversos '
             'nominales y de escenarios se conservan; no se eligen pesos o ramas positivas para una mezcla.\n\n'
             'Se hicieron treinta calibraciones cerradas primarias,670constantes de precio, y treinta '
             'controles adversos separados. Alterar todos los T0y reservas retenidos dejó exactamente '
             'iguales artefactos y precios últimos. El momento se cotejó por sumas escalares y los '
             'treinta flujos reales guardados pasaron replay con aprendizaje/inferencia fuente bloqueados. '
             'Los tres fitsfuente se cuentan solo en P14; P15no ajustó modelos fuente ni C0y no '
             'produjo inferencias2025, precios finales o envíos.\n\n'
             'Decisión: no adoptar GLM4_MIcomo sustitución. Antes de más complejidad se contrastará '
             'una forma aditiva estándar con curvas univariadas fijadas, sin interacciones. P13mostró '
             'pérdidas de asignación que un escalar no compensaba en algunas celdas; P15no demostró '
             'que indicadores solos las resuelvan. Eso justifica probar flexibilidad funcional, sin '
             'afirmar una causa no lineal. La lista física y4nudos/grado2procederán de la especificación '
             'GAMfuente anterior, aplicada al contrato actual de cuatro años y conservando indicadores; '
             'no se elegirán por ganancias de celda. Los experimentos fuente2023históricos no se repetirán '
             'sobre las mismas entradas. El nuevo preflight y la receta completa se congelarán antes '
             'de cualquier ajuste.\n\n'
             'B00/F3c/P6y todas las variantes fallidas se mantienen. La fuente contiene2024y destino '
             'es adaptativo; el ESS2025sigue insuficiente. No se acredita mejora privada, promoción '
             'formal o validación profesional independiente.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'context_report.json')+'; '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'P15_replay_context.json')+'.\n'
    doc = R/'docs/archivo/semana2/PRIVADA_P15_VALIDACION_AUSENTES.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P15-AUSENTES-RESULTADO', '--asunto',
                             'P15: indicadores sin mejora estable; siguiente forma aditiva estándar predefinida', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k != 'secondary_vs_plain_GLM'}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'context_report.json'), report_sha256=w.sha(OUT/'context_report.json'),
                   replay=w.rel(OUT/'P15_replay_context.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   secondary_nominal={c: a['NOMINAL'] for c, a in d['secondary_vs_plain_GLM'].items()},
                   primary_constants=number, primary_constant_breakdown=dict(totals['primary']),
                   adverse_constant_breakdown_separate=dict(totals['poison']), missing_indicator_GLM_adopted=False, next_unit=next_unit)
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P15_missing_GLM_validation' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+number,
                  'phase2_private_P15_missing_GLM_validation': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
                    'unique_primary_price_constants': number, 'constant_breakdown': dict(totals['primary']),
                    'secondary_new_resampling': 0, 'new_source_fits': 0, 'new_C0_fits': 0,
                    'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(INDEX := R/'registro/semana2_GLM_ausentes_validacion_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P15': receipt, 'next_unit': next_unit}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P15': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'last_goal_turn_classification':
                     'progress: missingness representation hypothesis tested on full algorithm, paired secondary intervals/replay complete; no established improvement, additive preflight next'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P15=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_missing_GLM_validation_index': w.rel(INDEX),
                                        'week_2_private_missing_GLM_validation_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'new_submissions': 0, 'adopted': False, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
