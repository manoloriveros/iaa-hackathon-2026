"""Cierra la sonda fuente P8 sin convertir dependencia en mejora predictiva."""
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/dev/Hakaton')
R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P8_sonda_exposicion_fuente_20261026_v2'
spec = importlib.util.spec_from_file_location('p8_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['all3lines_exact'] and replay['events_unchanged']
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    assert d['primary_raw_prediction_rows'] == 1728 and d['leaf_control_rows_separate'] == 216
    assert d['new_model_fits'] == d['new_finaltestprices'] == d['new_submissions'] == 0
    phase = R/'registro/semana2_mision017_fase2_actual.json'
    assert not w.read(phase).get('active_jobs') and not w.read(phase).get('active_execution')
    stamp = datetime.now(timezone.utc)
    cut = R/'privado'/('corte_P8_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('Preregister P9fixed-budget source exposure-feature ablation: drop only exposure_model from A1S, '
                 'retain offset/e_cost, source-only categories, all3seeds, original fullroundcounts/capacity and target recipes. '
                 'At most9new sourcefullfits; no new source earlystopsearch or C0fits. Reuse exact H1/G3inner ratios '
                 'because their learning is independent of A1S. Refit S2outercomponent in each originalscope, '
                 'validate pooled and conditional2023-to2024 transfer, all prior stressscenarios/cells/influence and '
                 'complete held-poison/replay flow. Do not infer a bug or adopt removal from P8. No uploads, '
                 'levelmatching or publicscore tuning; preserve B00/F3c/P6/alternatives and adaptive2024open.')
    note = '\n\n## Privada P8: sensibilidad fuente a la duración, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. La sonda preinscrita terminó sobre 64 filas futuras por ramo, '
             'elegidas sin respuestas dentro de negocio y duración. Solo se cambió exposure_model a la duración '
             'redondeada del 75% y del 50% de los días; los demás predictores, modelos y centros fuente quedaron fijos. '
             'El resultado es el cociente de relatividad anual fuente de las tres semillas.\n\n')
    note += '| Ramo | Días | Mediana del cociente | P05–P95 | Mínimo–máximo | Señal material previa |\n|---|---:|---:|---|---|---|\n'
    for line, conditions in d['results'].items():
        for a in conditions:
            q = a['ratio_quantiles']
            note += (f'| {line} | {100*a["fraction"]:.0f}% | {q[2]:.4f} | {q[1]:.4f}–{q[3]:.4f} '
                     f'| {q[0]:.4f}–{q[4]:.4f} | {a["material_dependency_flag"]} |\n')
    note += ('\nLa dependencia es material por el criterio descriptivo previo en edificios y contenidos. '
             'En autos el agregado no activa esa bandera, pero se conserva un extremo de 1,8099 al reducir '
             'a la mitad los días. En edificios el mínimo es 0,5579 y en contenidos 0,3897. '
             'Todos los detalles por semilla, negocio y banda permanecen en los artefactos. '
             'La muestra finita no mide el impacto poblacional ni la ganancia predictiva.\n\n'
             'Las nueve inferencias de base coinciden exactamente con las cachés originales. Se verificaron '
             '1728 filas de inferencia primaria y, por separado, 216 filas de control mediante suma de los '
             'valores de hojas guardadas; el enrutamiento procede de la misma biblioteca. El replay de los '
             'arrays guardados fue exacto con carga de modelos prohibida. Los hashes y el número de árboles '
             'no cambiaron. El intento V1 falló en un selector de columnas de un fixture antes de inferir '
             'con datos reales; V2 conserva ese fallo y reutiliza las entradas idénticas, con el núcleo '
             'numérico sin cambios.\n\n'
             'Esto justifica comparar una simplificación: quitar ese predictor manteniendo exposición en '
             'el offset, capacidad y semillas. No acredita doble conteo, fuga o error. La duración puede '
             'contener riesgo estacional o selección y retirarla podría empeorar. Tampoco se recalcularon '
             'T2b, miembros H1 o precios S2 para las intervenciones; no son cotizaciones alternativas. '
             'La retirada necesita una receta y una validación completas propias antes de cualquier adopción.\n\n'
             'Cero ajustes, C0, recalibraciones, precios finales o envíos nuevos. P6 conserva su CSV y sus '
             'adversos estadísticos. B00, F3c y todas las alternativas se mantienen. 2024 está abierto y '
             'es adaptativo; no se acredita mejora privada ni revisión profesional independiente.\n\n')
    note += f'Evidencia: {w.rel(OUT/"report.json")}; {w.rel(OUT/"replay_report.json")}.\n'
    doc = R/'docs/archivo/semana2/PRIVADA_P8_SENSIBILIDAD_EXPOSICION.md'
    assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
                             '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P8-SONDA-RESULTADO',
                             '--asunto', 'P8: dependencia material de duración; ablation estándar pendiente de validación',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k not in ['results', 'controls']}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'replay_report.json'), replay_sha256=w.sha(OUT/'replay_report.json'),
                   document=w.rel(doc), forum=json.loads(result.stdout), next_unit=next_unit)
    counters_path = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(counters_path)
    assert 'phase2_private_P8_frozen_source_probe' not in counters
    w.update(counters_path, {'as_of_utc': stamp.isoformat(),
                            'phase2_private_P8_frozen_source_probe': receipt}, cut)
    w.update(R/'registro/semana2_sonda_exposicion_fuente_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P8_probe': receipt, 'next_unit': next_unit}, cut)
    w.update(phase, {'utc': stamp.isoformat(), 'private_P8_probe': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'last_goal_turn_classification':
                     'progress: actual frozen-source exposure probe and saved replay complete; simpler feature-ablation justified for validation, no removal adopted'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P8_probe=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_exposure_probe_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_fits': 0, 'new_submissions': 0}))


if __name__ == '__main__': main()
