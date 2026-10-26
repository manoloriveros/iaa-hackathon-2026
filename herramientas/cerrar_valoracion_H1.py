"""Conserva P5 y sus adversos, sin escoger la valoración por resultados retenidos."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P5_recalibracion_reservas_H1_20261026_v1'
sp = importlib.util.spec_from_file_location('P5_state_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert report['committed_scopes'] == 180 and replay['all180_exact']
    assert report['new_C0_fits'] == report['new_source_models'] == report['new_submissions'] == 0
    assert all(report['counts'][role]['closed_learners_completed'] == 390 for role in ['primary', 'poison'])
    stamp = datetime.now(timezone.utc); archive = OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ'); archive.mkdir(parents=True)
    next_unit = (
        'Preflight a concrete nominal2025model whose executable producer matches the actually tested '
        'complete S2/H1algorithm, without labeling its evidence as validation of the different F3cbackbone. '
        'Inventory and reconcile exact full-target nominal C0/calibration caches before proposing any '
        'newfit; no duplicate source/model/C0training. Confirm existing future canonicalmetadata, cached '
        'T2bannualrates/A1Srelativity and production H1/G3components by keys/SHA/representation. '
        'Then preregister only the necessary full-training standard calibration and exact forecast/rounding '
        'contract, with whole-flow synthetic controls, before newparameters/prices. Do not choose a '
        'reserve valuation, base mixture weight or level from held/public scores. Preserve all P2/P3a/P4/P5 '
        'and H3Badverses, private priority, adaptive2024open, B00/F3c/all alternatives and H1submissionhold. '
        'P5does not erase frozen-price failures, the motorNB2023reserve125regression, low2025support, '
        'source vintage/late-tail limits or the failed pooled nominal gain minimum.'
    )
    note = '\n\n## Privada P5: recalibración completa de precios emergentes bajo reservas75/125, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completaron los 180 ámbitos de los dos escenarios y su replay con ajustes bloqueados. '
    note += ('En cada escenario cambiaron tanto las etiquetas de entrenamiento como el enlace de observación correspondiente. '
             'Se aprendieron nuevamente las formas de NCB/previos, niveles por negocio, factores residuales, base S2 '
             'y cinco miembros G3/H1. El resultado no es una aplicación de un multiplicador a precios nominales. '
             'Se conservaron folds, grupos, reglas de credibilidad, fuentes y pesos fijos del algoritmo.\n\n')
    note += '| Contraste | Diferencia D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---:|---:|---:|\n'
    for name, a in report['results'].items():
        note += (f'| {name} | {a["delta"]:+.8f} | [{a["bootstrap95"][0]:+.8f}, '
                 f'{a["bootstrap95"][1]:+.8f}] | {a["post31_delta"]:+.8f} | {a["worst_cell_delta"]:+.8f} |\n')
    note += ('\nAmbos primarios, frente a sus propias bases recalibradas, mantienen intervalos agregados positivos, '
             'también con la corrección exploratoria de cuatro contrastes. Ambos años y los cinco folds aportan '
             'ganancia. Los dos escenarios siguen por debajo del mínimo histórico 0,002. '
             'Con reservas125 persiste una pérdida de -0,00163690 en autos nuevos de 2023, superior al suelo admitido. '
             'Ese fallo se conserva aunque el agregado sea favorable.\n\n')
    note += ('Los secundarios comparan cada candidato recalibrado con los precios nominales congelados observados '
             'bajo ese mismo escenario en P3a. Sus intervalos incluyen cero. Con reservas125, la ganancia secundaria '
             'se vuelve negativa después de descontar los 31 grupos más favorables. La recalibración no queda '
             'establecida como mejora sobre mantener los precios congelados y muestra pérdidas locales. '
             'No se escogerá una valoración por su score ni se cambiará el objetivo nominal de producción.\n\n')
    note += '| Contraste con pérdida superior a0,001 | Celda | Diferencia de celda |\n|---|---|---:|\n'
    for name, a in report['results'].items():
        for c in a['cells']:
            if c['delta_cell_null'] < -.001:
                note += (f'| {name} | {c["line"]}, {c["year"]}, {"nuevo" if c["NB"] else "renovación"} '
                         f'| {c["delta_cell_null"]:+.8f} |\n')
    note += ('\nEsta es una recalibración completa del precio emergente condicionada a fuentes fijas. '
             'Los modelos fuente y sus perfiles de periles no se revaloraron. Se usaron las ramas de coste '
             'protegidas que ya se habían comprobado por probabilidades de evento en P3a; las distribuciones '
             'de conteo y sus frecuencias no cambian con la marca de reserva. Por eso no se ajustaron curvas '
             'otra vez ni se repitió esa auditoría. La cola hipotética tampoco se presentó como un modelo '
             'conjunto de frecuencia y severidad identificado.\n\n')
    constants = report['counts']['primary']['constants']['price_total']
    commits = [w.read(p) for p in OUT.glob('*/scope_*/committed.json')]
    norm_primary = sum(c['primary_ultimate_normalizers'] for c in commits)
    norm_control = sum(c['adverse_ultimate_normalizers_separate'] for c in commits)
    note += (f'Los 390 aprendices cerrados primarios produjeron {constants} constantes de precio; los 390 '
             'controles adversos se cuentan aparte. Todos los artefactos y precios de último coincidieron '
             'exactamente al alterar T0 y reservas retenidos. El replay de los 180 ámbitos bloqueó nueve '
             'entradas de ajuste y recuperó los mismos precios con etiquetas corruptas, sin añadir eventos '
             'de aprendizaje. Se cotejaron momentos por suma escalar, puente de observación, media, métricas '
             'y etiquetas oficiales por clave. Los SHA registrados antes de ajustar permanecieron iguales. '
             'Los 54 aprendices sintéticos y los normalizadores se registran separados. '
             'Hubo cero C0, modelos fuente, inferencias fuente, precios 2025, CSV o envíos nuevos.\n\n')
    note += ('La evidencia sigue siendo exploratoria sobre 2023/2024 inspeccionados y sobre S2, un núcleo '
             'completo factible distinto del F3c recibido. El soporte ponderado hacia 2025 continúa siendo '
             'insuficiente; el mercado desarrollado no añade soporte emergente. Estos controles no identifican '
             'la reserva verdadera o la cola tardía, restauran disponibilidad histórica de los maestros '
             'o acreditan mejora privada.\n\n')
    note += ('Decisión: conservar objetivo nominal, B00, F3c, H1 y todas las alternativas/fallos. '
             '2024 permanece abierto para desarrollo adaptativo. H1 no se promueve y su entrega sigue diferida. '
             'P5 no borra el fallo previo del precio congelado en autos nuevos, ni sustituye el resultado '
             'anual favorable de P4 por una aprobación general. El siguiente paso es preparar un productor '
             'nominal que coincida con el algoritmo S2/H1 realmente evaluado. Antes de ajustar o predecir, '
             'se conciliarán las cachés de entrenamiento completo y entradas futuras existentes para evitar '
             'repeticiones, y se registrará solo lo que falte.\n\n')
    note += f'Evidencia: {w.rel(OUT/"report.json")}; replay {w.rel(OUT/"replay_report.json")}.\n'
    doc = R/'docs/semana2/PRIVADA_P5_RECALIBRACION_RESERVAS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, note, archive)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    res = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                          '--id', 'COD-S2-20261026-PRIVADA-P5-RESERVAS-RESULTADO', '--asunto',
                          'P5: señal agregada bajo recalibración, persiste fallo en autos nuevos con reservas125',
                          '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': report['status'], 'report': w.rel(OUT/'report.json'),
               'report_sha256': w.sha(OUT/'report.json'), 'replay': w.rel(OUT/'replay_report.json'),
               'replay_sha256': w.sha(OUT/'replay_report.json'), 'document': w.rel(doc), 'forum': json.loads(res.stdout),
               'results': report['results'], 'diagnostic_gates': report['diagnostic_gates'], 'counts': report['counts'],
               'primary_ultimate_normalizers': norm_primary, 'adverse_ultimate_normalizers_separate': norm_control,
               'replay_ultimate_normalizers_separate': replay['ultimate_normalizers_recomputed_separate'],
               'new_C0_fits': 0, 'new_source_models': 0, 'new_source_inference': 0, 'new_final_test_prices': 0,
               'new_submissions': 0, 'nominal_objective_changed': False, 'private_improvement_established': False,
               'formal_promotion': False, 'submission_allowed': False, '2024_open': True,
               'B00_all_alternatives_preserved': True, 'goal_achieved': False, 'next_unit': next_unit}
    counters = R/'registro/semana2_contadores_propios_actual.json'; previous = w.read(counters)
    assert 'phase2_private_P5_reserve_recalibration' not in previous
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': previous['cumulative_closed_form_constants']+constants,
                        'phase2_private_P5_reserve_recalibration': {'counts': report['counts'], 'new_C0_fits': 0,
                                                                 'new_iterative_price_fits': 0, 'synthetic_closed_learners_excluded': 54,
                                                                 'primary_ultimate_normalizers': norm_primary,
                                                                 'adverse_ultimate_normalizers_separate': norm_control,
                                                                 'replay_ultimate_normalizers_separate': replay['ultimate_normalizers_recomputed_separate'],
                                                                 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, archive)
    index = R/'registro/semana2_recalibracion_reservas_H1_actual.json'; w.update(index, receipt, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P5': receipt, 'next_unit': next_unit}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase, {'utc': stamp.isoformat(), 'private_P5': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'active_execution': None, 'active_jobs': [],
                     'last_goal_turn_classification': 'progress: complete two-valuation target recalibration and blocked-learning replay, retained aggregate and local adverse outcomes'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P5=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, active_jobs=[], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_H1_reserve_recalibration_index': w.rel(index),
                                        'week_2_private_H1_reserve_recalibration_report': w.rel(doc)}, archive)
    summary = ('\n\n## Avance de validación con prioridad privada, 26 de octubre de 2026\n\n'
               'La prueba anual P4 mantuvo todo aprendizaje emergente en2023y evaluó2024: diferencia nominal+0,00226431, '
               'IC95por grupos[+0,00129454,+0,00332922], cincofoldspositivos y cuatro escenarios favorables. '
               'Es condicional a fuente/valoración2024, no confirmación prospectiva o privada. '
               'P5recalibró de verdad las dos bases de reservas: diferencias+0,00112276y+0,00101494con intervalos positivos, '
               'pero reservas125pierde-0,00163690en autos nuevos2023. No cambia el objetivo nominal ni se aprueba entrega. '
               'La mezclaH3Bse preservó adversa; los promedios de miembros no prueban una ventaja por sí solos. '
               'La siguiente preparación debe hacer coincidir productor nominal y algoritmo evaluado, conciliando primero las cachés. '
               'Cero envíos nuevos; B00/F3c/alternativas intactos,2024abierto adaptativo. '
               'Informes: [P4](PRIVADA_P4_TRANSFERENCIA_ENTRE_ANIOS.md) y [P5](PRIVADA_P5_RECALIBRACION_RESERVAS.md).\n')
    w.append(R/'docs/semana2/MISION_PRIVADA_PRIORIDAD_Y_PLAN.md', summary, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_submissions': 0,
                      'constant_counter': w.read(counters)['cumulative_closed_form_constants'], 'adverse_retained': True}))


if __name__ == '__main__':
    main()
