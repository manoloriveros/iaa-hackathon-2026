"""Cierra el contraste GLM sin promover una ganancia agregada inestable."""
import collections
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P12_validacion_GLM_20261026'
sp = importlib.util.spec_from_file_location('p12_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['scopes'] == 30 and replay['learning_and_source_inference_blocked'] and replay['events_unchanged']
    assert replay['report_sha256'] == w.sha(OUT/'report.json') and not all(d['diagnostic_gates'].values())
    assert w.read(OUT/'P12_replay_context.json')['source_models_per_line'] == 1
    totals = {'primary': collections.Counter(), 'poison': collections.Counter()}; calls = collections.Counter()
    for line in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines():
        a = json.loads(line)
        if a['kind'] == 'closed_completed': totals[a['role']].update(a['constants']); calls[a['role']] += 1
    assert calls == {'primary': 30, 'poison': 30} and totals['primary'] == totals['poison']
    number = sum(totals['primary'][k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    assert number == 670
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P12_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('Before another model fit, attribute current GLM4versus A1Sadverses using only P12stored prices and '
                 'existing source relativities/covariates: analytic profile-level versus allocation loss on fixed cells '
                 'and factual source/target support, without new bootstrap, inference or training. Diagnostic profiled '
                 'levels are oracles, never admissible prices or calibration factors. Do not rescue by positive-line '
                 'selection, mixtures, penalty/seed searches or totalmatching. A later standard correction needs a '
                 'concrete unresolved mechanism and preregistration. Preserve B00/F3c/P6, all failed variants and '
                 'private priority;2024adaptiveopen. Complete own code version checkpoint before future deliveries; '
                 'no upload/publicscore tuning now. Current public-source check does not create a new modeling assumption.')
    note = '\n\n## Privada P12: GLM simple sin estabilidad suficiente, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Se comparó GLM4/S2/H1 con A1S/S2/H1, conservando C0, exposición, '
             'mitades fuente/N3, etapas de calibración y los cinco cocientes H1/G3. Los grupos de treinta '
             'ámbitos se conciliaron exactamente antes de ajustar. El motor numérico es el de P10, con '
             'fuentes y preinscripción propias; se reutilizaron sus controles sin repetir fixtures idénticos.\n\n')
    note += '| Nominal | Δ D² | IC95 por grupos | Después de 31 grupos | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort in ['POOLED', 'TRANSFER']:
        a = d['results'][cohort]['NOMINAL']
        note += f'| {cohort} | {a["delta"]:.7f} | [{a["bootstrap95"][0]:.7f}, {a["bootstrap95"][1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nEl punto agregado sube ligeramente y ambos años contribuyen positivamente en el esquema '
             'combinado, pero solo tres folds mejoran, el intervalo incluye cero y Post31 es negativo. '
             'El mínimo incremental0,002 no se cumple. Al aprender destino solo2023y retener2024, el '
             'resultado global empeora. La peor celda combinada es contenidos nuevos2023; edificios '
             'nuevos2024 pierde −0,011638 en el combinado y −0,017187 en transferencia. '
             'Una forma más simple no acredita por sí misma un modelo más robusto.\n\n')
    note += '| Escenario fijado | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for name in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = d['results']['POOLED'][name]; z = d['results']['TRANSFER'][name]
        note += f'| {name} | {a["delta"]:.7f} | {a["worst_cell_delta"]:.7f} | {z["delta"]:.7f} | {z["worst_cell_delta"]:.7f} |\n'
    note += ('\nEn reservas75% la peor celda de transferencia llega a −0,021365. Las sensibilidades '
             'mantienen precios y enlaces comunes fijados; no son nuevas calibraciones de todas las '
             'ramas. Se conservan los intervalos de familia10, la influencia por componente, A/E y los '
             'puntos ponderados2025con su ESS insuficiente. No se usan celdas positivas para una mezcla '
             'por ramo ni para cambiar la penalización después del resultado.\n\n'
             'Treinta calibraciones cerradas produjeron670constantes primarias. Otras treinta llamadas '
             'adversas alteraron todos los T0 y reservas retenidos: artefactos y precios últimos fueron '
             'exactamente iguales. El momento del nivel pasó por sumas independientes y los treinta '
             'replays guardados fueron exactos con aprendizaje e inferencia fuente bloqueados. P12 '
             'no ajustó GLMfuente ni C0: los tres GLM se cuentan en P11. Tampoco calculó precios2025o envíos.\n\n'
             'Decisión: no adoptar el GLM como sustitución completa ni retirar A1S. Se conserva con sus '
             'adversos y costes. La siguiente revisión distinguirá, sobre precios ya guardados, error '
             'de nivel y asignación relativa para precisar qué falla antes de otra receta. Cualquier '
             'nivel perfilado con respuestas retenidas será un oráculo de diagnóstico y no un factor '
             'admisible para predecir. No se inicia otra búsqueda para rescatar un score.\n\n'
             'La interpretación continúa condicionada por fuentes2021–2024y valoración final común. '
             'Los años emergentes son adaptativos. La comparación no reproduce el F3c histórico completo '
             'y no establece rendimiento privado. B00/F3c/P6y todas las alternativas se mantienen; '
             '2024abierto. Ningún nuevo envío en estos ciclos.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'; '+w.rel(OUT/'P12_replay_context.json')+'.\n'
    doc = R/'docs/archivo/semana2/PRIVADA_P12_VALIDACION_GLM.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P12-GLM-RESULTADO', '--asunto',
                             'P12: GLM sin mejora robusta; adversos de transferencia y nuevo negocio conservados', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k != 'results'}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'replay_report.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   nominal={c: d['results'][c]['NOMINAL'] for c in ['POOLED', 'TRANSFER']},
                   primary_constants=number, primary_constant_breakdown=dict(totals['primary']),
                   adverse_constant_breakdown_separate=dict(totals['poison']), GLM_replacement_adopted=False, next_unit=next_unit)
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P12_standard_GLM_validation' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+number,
                  'phase2_private_P12_standard_GLM_validation': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
                    'unique_primary_price_constants': number, 'constant_breakdown': dict(totals['primary']),
                    'new_synthetic_fits': 0, 'new_source_fits': 0, 'new_C0_fits': 0,
                    'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(R/'registro/semana2_GLM_fuente_validacion_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P12': receipt, 'next_unit': next_unit}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; current = w.read(phase)
    assert not current.get('active_execution') and not current.get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P12': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'last_goal_turn_classification':
                     'progress: standard four-year sourceGLMcomplete validation/replay done; unstable aggregate and negative transfer retained, no substitution adopted'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P12=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_standard_GLM_validation_index': w.rel(R/'registro/semana2_GLM_fuente_validacion_actual.json'),
                                        'week_2_private_standard_GLM_validation_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'constants': number,
                      'GLM_replacement_adopted': False, 'new_submissions': 0}))


if __name__ == '__main__': main()
