"""Registra el adverso de P10 y conserva el modelo con predictor de duración."""
import collections
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P10_validacion_sin_exposicion_20261026'
sp = importlib.util.spec_from_file_location('p10_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['scopes'] == 30 and replay['learning_and_source_inference_blocked'] and replay['events_unchanged']
    assert replay['report_sha256'] == w.sha(OUT/'report.json') and not all(d['diagnostic_gates'].values())
    totals = {'primary': collections.Counter(), 'poison': collections.Counter()}; calls = collections.Counter()
    for line in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines():
        a = json.loads(line)
        if a['kind'] == 'closed_completed': totals[a['role']].update(a['constants']); calls[a['role']] += 1
    assert calls == {'primary': 30, 'poison': 30} and totals['primary'] == totals['poison']
    primary_constants = sum(totals['primary'][k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    assert primary_constants == 670
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P10_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('Bounded review of existing developed-source GLM recipes before any new fit: distinguish source2023-only '
                 'physical-teacher experiments from a fixed main-effects GLM on current A1Ssource2021-2024/history/C0contract. '
                 'If not already tested on identical sources, preregister a three-line standard TweedieGLM with no interactions '
                 'or hyperparametersearch, source-only preprocessing, correct rate/weight offset algebra and complete pooled/'
                 'conditional-year comparator. Do not repeat old source2023GLMs or tune duration/removal by P10positivecells. '
                 'Keep exposure predictor/current recipes, all alternatives/adverses, private priority and2024adaptiveopen. '
                 'No uploads or publicscore tuning; keep original minimum/gates and failed futureweightESS visible.')
    note = '\n\n## Privada P10: la retirada de duración no acredita mejora robusta, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Se comparó el algoritmo completo S2/H1 con los nueve modelos fuente '
             'sin predictor de duración frente al mismo algoritmo original. Los 30 ámbitos de integración '
             'reprodujeron exactamente los precios últimos originales antes de cambiar la fuente. Se reutilizaron '
             'C0, N3 y los cinco cocientes H1/G3 por su independencia de A1S; se aprendieron solo las calibraciones '
             'S2 afectadas, bajo los grupos y la exposición originales.\n\n')
    note += '| Comparación nominal | Δ D² | IC95 por grupos | Después de 31 grupos | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort in ['POOLED', 'TRANSFER']:
        a = d['results'][cohort]['NOMINAL']
        note += f'| {cohort} | {a["delta"]:.7f} | [{a["bootstrap95"][0]:.7f}, {a["bootstrap95"][1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nLa comparación combinada pierde en 2023 (contribución −0,0002290), mejora en 2024 '
             '(+0,0003601) y solo dos de los cinco folds aportan ganancia. Los intervalos incluyen cero '
             'y las mejoras quedan por debajo del mínimo incremental 0,002 fijado antes de probar. '
             'En autos nuevos2023 el deterioro de celda es −0,0039066; en edificios nuevos2024, −0,0028924. '
             'La transferencia de destino2023a2024 también depende de pocos grupos y empeora edificios '
             'nuevos en −0,0033421. No se seleccionan ramas o mezclas a partir de estas celdas.\n\n')
    note += '| Escenario fijado | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for name in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = d['results']['POOLED'][name]; z = d['results']['TRANSFER'][name]
        note += f'| {name} | {a["delta"]:.7f} | {a["worst_cell_delta"]:.7f} | {z["delta"]:.7f} | {z["worst_cell_delta"]:.7f} |\n'
    note += ('\nLas cuatro sensibilidades conservan precios y cambian solo objetivo de valoración/enlace de '
             'observación común según el contrato anterior; no son recalibraciones completas de D0 en cada '
             'rama. Sus intervalos también incluyen cero y no resuelven los pisos por celda. Los intervalos '
             'simultáneos de la familia de diez contrastes, los cocientes A/E y sensibilidades de nivel '
             'comunes quedan guardados. Los pesos2025 se usaron solo para puntos descriptivos porque su '
             'ESS sigue siendo insuficiente. No se reestimaron para favorecer esta alternativa.\n\n'
             'Treinta llamadas de aprendizaje cerrado primarias produjeron 670 constantes de precio; '
             'separadamente se hicieron treinta controles con todos los T0 y reservas retenidos alterados. '
             'Artefactos y precios últimos fueron exactamente iguales. El momento del nivel se verificó '
             'por sumas escalares independientes. Un proceso de replay recuperó los treinta flujos exactos '
             'con aprendizaje e inferencia fuente bloqueados. Cero C0, modelos fuente, inferencias2025, '
             'precios finales o envíos nuevos en esta etapa. Los nueve modelos fuente se cuentan en P9.\n\n'
             'El fixture inicial acoplaba año y negocio y dejó celdas vacías: hubo una llamada sintética '
             'incompleta, sin ajuste con datos del concurso. Se conserva el intento y el fallo. Se corrigió '
             'solo el año sintético y pasaron seis llamadas sintéticas completas. Los replays originales '
             'anteriores al fallo no tenían recibo durable; la comprobación de integración se repitió para '
             'guardar evidencia verificable, sin repetir estimaciones o puntuar otra receta.\n\n'
             'Decisión: no adoptar D0 ni quitar exposure_model del modelo actual. Dependencia de una '
             'variable no implica que retirarla ayude. Se mantiene la referencia y la alternativa fallida '
             'con sus costes y adversos. Antes de otra familia se cotejarán los GLM fuente ya hechos y '
             'la diferencia real de ámbito respecto a un GLM de efectos principales sobre los cuatro '
             'años actuales; no se repetirá la receta histórica2023 con otro nombre.\n\n'
             'La fuente contiene2024y las marcas finales son comunes, así que la transferencia no es una '
             'validación prospectiva completa. Ambos años destino son adaptativos. No se reprodujo el '
             'F3c histórico completo y no se afirma ganancia frente a su envío ni mejora privada. '
             'B00/F3c/P6y todas las alternativas permanecen; 2024abierto por autorización humana vigente.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P10_VALIDACION_ABLACION.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P10-ABLACION-RESULTADO', '--asunto',
                             'P10: retirada de duración sin mejora robusta, se conserva la receta original',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k != 'results'}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'replay_report.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   nominal={cohort: d['results'][cohort]['NOMINAL'] for cohort in ['POOLED', 'TRANSFER']},
                   primary_constants=primary_constants, primary_constant_breakdown=dict(totals['primary']),
                   adverse_constant_breakdown_separate=dict(totals['poison']), feature_removal_adopted=False, next_unit=next_unit)
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P10_source_ablation_validation' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+primary_constants,
                  'phase2_private_P10_source_ablation_validation': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
                    'unique_primary_price_constants': primary_constants, 'constant_breakdown': dict(totals['primary']),
                    'synthetic_completed_closed_calls_separate': 6, 'synthetic_failed_call_separate': 1,
                    'new_source_fits': 0, 'new_C0_fits': 0, 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(R/'registro/semana2_ablacion_fuente_validacion_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P10': receipt, 'next_unit': next_unit}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; current = w.read(phase)
    assert not current.get('active_execution') and not current.get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P10': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'last_goal_turn_classification':
                     'progress: complete fixed-capacity source ablation evaluated and replayed; negative concentration/year/NB evidence retained, no removal adopted'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P10=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_ablation_validation_index': w.rel(R/'registro/semana2_ablacion_fuente_validacion_actual.json'),
                                        'week_2_private_source_ablation_validation_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'constants': primary_constants,
                      'feature_removal_adopted': False, 'new_submissions': 0}))


if __name__ == '__main__': main()
