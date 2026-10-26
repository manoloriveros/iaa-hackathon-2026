"""Concilia P4 y guarda sus resultados, límites y coste real con autoría propia."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P4_transferencia_anual_H1_20261026_v1'
sp = importlib.util.spec_from_file_location('P4_state_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['all90_exact'] and report['committed_scopes'] == 90
    assert report['counts']['primary']['reporting_completed'] == 450
    assert report['counts']['poison']['reporting_completed'] == 450
    assert report['counts']['primary']['closed_learners_completed'] == 195
    assert report['counts']['poison']['closed_learners_completed'] == 195
    stamp = datetime.now(timezone.utc); archive = OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ'); archive.mkdir(parents=True)
    results = report['results']; primary = results['NOMINAL_VS_BASE']
    failed = [k for k, value in report['diagnostic_gates'].items() if not value]
    next_unit = (
        'Review P4year-transfer result together with existing P2/P3a/H3Badverses without tuning any heldyear '
        'level, mixture weight or split. The remaining distinct robustness unit is full target-valuation '
        'recalibration under the already frozen reserve075/125scenarios: held-price sensitivity alone '
        'cannot show how a complete learner changes with a different reserve basis. First preregister exact '
        'outer S2and inner G3/H1recalibration, objective/exposure/mark-CDFcoupling, fixed source and budget; '
        'use cached reporting count distributions only where algebraically valid, never inherited nominal '
        'price parameters as if recalibrated. Validate whole new numerical flow synthetically before real '
        'fits, no new capacity or public-driven adjustment. Preserve private priority,2024open adaptive, '
        'B00/F3c/all alternatives and H1submissionhold. The unresolved source2024asof/master vintage, '
        'additional emerging NBsupport and full deliveredF3creplay remain explicit limitations.'
    )
    note = '\n\n## Privada P4: transferencia entre años sin aprender etiquetas emergentes de 2024, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completaron los 90 ámbitos y su replay sin aprendizaje. '
    note += ('Los retenidos son exclusivamente periodos de 2024; todos los aprendices emergentes usaron solo 2023 '
             'y excluyeron también los componentes globales del fold retenido. La base S2 se reconstruyó dentro de cada '
             'ámbito exterior, con la misma mezcla fuente fija y reglas de credibilidad. Cada uno de los cinco miembros '
             'volvió a aprender su C0 y G3/H1 con sus grupos internos guardados. No se heredaron calibraciones '
             'de la prueba conjunta 2023–2024.\n\n')
    note += ('La media se hizo sobre costes de último antes de observarla con el adaptador exterior protegido. '
             'Exposición calendario y normalizadores de último se aplicaron al avance; la exposición redondeada original '
             'se conservó en el aprendizaje observado. El contraste secundario mide el promedio frente a una sola '
             'corrección exterior. Los cuatro escenarios alteran las etiquetas/observación declaradas, manteniendo '
             'los precios de último ya ajustados.\n\n')
    note += '| Contraste | Diferencia D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---:|---:|---:|\n'
    for name, a in results.items():
        note += (f'| {name} | {a["delta"]:+.8f} | [{a["bootstrap95"][0]:+.8f}, '
                 f'{a["bootstrap95"][1]:+.8f}] | {a["post31_delta"]:+.8f} | {a["worst_cell_delta"]:+.8f} |\n')
    note += '\n| Fold externo, nominal | Diferencia, denominador global |\n|---|---:|\n'
    for fold, value in primary['folds'].items():
        note += f'| {fold} | {value:+.8f} |\n'
    note += '\n| Celda 2024, nominal | Diferencia, denominador de celda | A/E base | A/E media |\n|---|---:|---:|---:|\n'
    for c in primary['cells']:
        note += f'| {c["line"]}, {"nuevo" if c["NB"] else "renovación"} | {c["delta_cell_null"]:+.8f} | {c["AE_base"]:.4f} | {c["AE_candidate"]:.4f} |\n'
    note += (f'\nCriterios diagnósticos incumplidos: {", ".join(failed) if failed else "ninguno de los declarados para este estrés"}. '
             'El criterio de dos años retenidos no puede probarse aquí: solo se retuvo 2024. '
             'No se sustituye con una ganancia ficticia cero en 2023. Los intervalos simultáneos exploratorios '
             'de seis contrastes, A/E, celdas y puntos ponderados completos se conservan en el JSON. '
             'Los pesos hacia 2025 siguen siendo sensibilidad y no una validación aprobada.\n\n')
    note += ('No se trata de un pronóstico reconstruido con información disponible en diciembre de 2023. '
             'Los importes tienen valoración común de diciembre de 2024; las fuentes congeladas incluyen datos '
             'desarrollados de 2024 y maestros sin fecha. La prueba aísla la transferencia sin etiquetas emergentes '
             'del año retenido, condicionada a esa fuente. Además, 2023/2024 ya fueron inspeccionados: no recuperan '
             'independencia por esta partición. S2 es un núcleo completo factible, distinto de un replay histórico '
             'exacto del F3c enviado. Ningún resultado acredita todavía la privada.\n\n')
    note += ('La revisión estática previa también preservó evidencia ajena, sin ejecutar sus productores: '
             'las variantes de tendencia tenían diferencias retenidas -0,00126413 y -0,00160053; '
             'el clima anual, +0,00025604 con IC95 [-0,00253861, +0,00320324]; '
             'el nivel E27 bajaba D² de 0,12599105 a 0,12478898. Son recibos de recetas anteriores de Claude, '
             'revisados por Codex; no son nuevas pruebas ni una aprobación de otro autor. '
             'Su existencia descarta presentar la repetición de esas recetas como una mejora nueva.\n\n')
    note += ('Los 90 controles reales alteraron T0/reserva retenidos y los importes, periles y fechas de '
             'todos los siniestros emergentes de 2024, incluidos los ausentes del ámbito. '
             'Cada papel adverso reajustó realmente sus propios objetos numéricos y coincidió exactamente '
             'con el primario. El replay recorrió esos mismos ámbitos con nueve entradas de ajuste bloqueadas, '
             'datos futuros corruptos y fuentes guardadas; recuperó todos los precios de último exactamente, '
             'sin nuevos eventos de ajuste o scores. Las sumas escalares de los momentos, el puente, la media '
             'y la métrica estándar también se cotejaron. Los SHA de las fuentes registradas antes de ajustar '
             'permanecieron iguales. Se añadió un corte de dependencias transitivas durante la ejecución; '
             'su alcance temporal se declara y no se presenta como recibo anterior a todos los ajustes.\n\n')
    constants = report['counts']['primary']['constants']['price_total']
    note += (f'Coste real: 450 curvas C0 y 195 aprendices cerrados primarios, con {constants} constantes de precio. '
             'Los 450/195 controles adversos se registran aparte, al igual que los normalizadores y los 30/18 ajustes sintéticos. '
             'Cero modelos iterativos/fuente, nuevas inferencias fuente, precios 2025, CSV o envíos. '
             'B00, F3c y todas las alternativas/fallos se conservan. 2024 sigue abierto para desarrollo adaptativo.\n\n')
    note += ('La próxima incertidumbre distinta es la recalibración integral del objetivo bajo las dos bases '
             'de reservas ya declaradas. La sensibilidad de precios congelados no demuestra la respuesta '
             'de todo el aprendizaje a una valoración diferente. Antes de ajustar se congelarán la relación '
             'etiqueta/CDF, los parámetros a recalcular, las fuentes, el coste y los controles; no se elegirán '
             'niveles, pesos o escenarios por el resultado retenido. La entrega H1 permanece diferida.\n\n')
    note += f'Evidencia: {w.rel(OUT/"report.json")}; replay {w.rel(OUT/"replay_report.json")}.\n'
    doc = R/'docs/semana2/PRIVADA_P4_TRANSFERENCIA_ENTRE_ANIOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, note, archive)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    res = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                          '--id', 'COD-S2-20261026-PRIVADA-P4-ANUAL-RESULTADO', '--asunto',
                          'P4: transferencia anual del algoritmo completo, adversos y límites conservados',
                          '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': report['status'], 'report': w.rel(OUT/'report.json'),
               'report_sha256': w.sha(OUT/'report.json'), 'replay': w.rel(OUT/'replay_report.json'),
               'replay_sha256': w.sha(OUT/'replay_report.json'), 'document': w.rel(doc), 'forum': json.loads(res.stdout),
               'results': results, 'diagnostic_gates': report['diagnostic_gates'], 'counts': report['counts'],
               'committed_scopes': 90, 'new_source_models': 0, 'new_source_inference': 0, 'new_final_test_prices': 0,
               'new_submissions': 0, 'source2024_excluded': False, 'prospective_asof2023_established': False,
               'private_improvement_established': False, 'formal_promotion': False, 'submission_allowed': False,
               '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False, 'next_unit': next_unit}
    counter_path = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(counter_path)
    assert 'phase2_private_P4_year_transfer' not in counters
    w.update(counter_path, {'as_of_utc': stamp.isoformat(),
                            'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+constants,
                            'supplementary_reporting_peril_fits_since_counter_start': counters['supplementary_reporting_peril_fits_since_counter_start']+450,
                            'mixture_frequency_constants_since_counter_start_separate': counters['mixture_frequency_constants_since_counter_start_separate']+450,
                            'mixture_positive_severity_means_since_counter_start_separate': counters['mixture_positive_severity_means_since_counter_start_separate']+1350,
                            'phase2_private_P4_year_transfer': {'counts': report['counts'], 'primary_reporting_scope_mixtures': 90,
                                                             'synthetic_reporting_fits_excluded': 30, 'synthetic_closed_learners_excluded': 18,
                                                             'replay_ultimate_normalizers_separate': replay['recomputed_covariate_only_ultimate_normalizers_separate'],
                                                             'new_iterative_price_fits': 0, 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, archive)
    index = R/'registro/semana2_transferencia_anual_H1_actual.json'; w.update(index, receipt, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P4': receipt, 'next_unit': next_unit}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; previous = w.read(phase)
    w.update(phase, {'utc': stamp.isoformat(), 'private_P4': receipt, 'mission_private_priority': w.read(priority),
                     'new_C0_fits': previous['new_C0_fits']+450, 'new_emerging_C0_fits': previous['new_emerging_C0_fits']+450,
                     'new_P4_adverse_C0_fits_separate': 450, 'next_unit': next_unit, 'active_execution': None, 'active_jobs': [],
                     'last_goal_turn_classification': 'progress: complete target-year transfer of full algorithm, genuine future-label poisoning, protected replay and honest limits'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P4=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, active_jobs=[], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_H1_target_year_transfer_index': w.rel(index),
                                        'week_2_private_H1_target_year_transfer_report': w.rel(doc)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'primary_delta': primary['delta'], 'failed_diagnostics': failed,
                      'forum': receipt['forum'], 'new_submissions': 0}))


if __name__ == '__main__':
    main()
