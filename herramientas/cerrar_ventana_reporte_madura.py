"""Integra P7: el diagnóstico no respalda un uplift global de cola fuente."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P7_ventana_reporte_madura_20261026_v2'
sp = importlib.util.spec_from_file_location('P7_state_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json'); preflight = w.read(OUT/'preflight.json')
    assert report['committed_scopes'] == replay['scopes'] == 30 and replay['learning_blocked']
    assert all(report['counts'][role]['reporting_completed']+report['counts'][role]['distribution_reuses'] == 150 for role in ['primary', 'poison'])
    p6 = w.read(BASE/'P6_productor_S2_H1_nominal_20261026_v1/report.json')
    assert w.sha(ROOT/p6['CSV']['path']) == p6['CSV']['sha256']
    stamp = datetime.now(timezone.utc); archive = OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ'); archive.mkdir(parents=True)
    next_unit = (
        'Review actual source/backbone feature and absolute-level contracts of S2 versus existing F3clineage, '
        'using current source code/feature lists/normalization receipts first, no newtraining or factor '
        'chosen to match totals. P7did not support a material global short-window deficit in mature '
        'developed2021context, so do not adopt a source-tail uplift to explain10.83percent. '
        'Look for a specific schema, exposure-as-feature, capital, normalization or source-to-target '
        'availability discrepancy not already resolved by earlier reviews. P6depends on cached source '
        'features and its half-exposure check is conditional on those cached relativities; do not present '
        'it as raw end-to-end sourceinference sensitivity. Only a documented material unresolved '
        'difference can justify a separately preregistered frozen-model probe or standard correction. '
        'Do not repeat C0backtest/lateclaiminventory, choose mixture/level/seed by scores, or consume quota. '
        'Preserve P6CSVunchanged/unadmitted, B00/F3c/all alternatives, adaptive2024open and private priority.'
    )
    note = '\n\n## Privada P7: la ventana corta no explica una gran brecha global en esta cohorte fuente, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completó el backtest preinscrito de reporte sobre coberturas desarrolladas de 2021. '
    note += ('Los cortes virtuales fueron diciembre de 2022 y diciembre de 2023; la referencia es el coste '
             'aceptado conocido a diciembre de 2024. Los cinco folds globales de cliente/dirección se conservaron. '
             'Cada curva se estimó con otros grupos y solo con reportes disponibles al corte. '
             'Las marcas y el estado final de siniestros se mantuvieron comunes, de modo que esto es un diagnóstico '
             'retrospectivo de reporte, no un backtest prospectivo de reservas o una CV de precios.\n\n')
    note += '| Corte virtual | Coste reportado / conocido2024 | Reconstruido / conocido2024 | IC95 por grupos |\n|---|---:|---:|---:|\n'
    for cut, a in report['summary']['primary'].items():
        note += (f'| {a["cutoff"]} | {100*a["raw_recovery"]:.4f}% | {100*a["reconstructed_recovery"]:.4f}% '
                 f'| [{100*a["bootstrap95"][0]:.4f}%, {100*a["bootstrap95"][1]:.4f}%] |\n')
    note += ('\nLa referencia suma 174.811.576 CU. El criterio previo de infrarrecuperación global material '
             'no se cumple en ninguno de los dos cortes. Los intervalos simultáneos exploratorios de los dos '
             'primarios también quedan próximos a uno. Esta evidencia no respalda aplicar un incremento general '
             'de cola para explicar la diferencia de nivel de 10,83% de P6 frente a F3c. '
             'Tampoco demuestra que la cola emergente sea igual o esté identificada.\n\n')
    note += '| Peril largo | Corte | Recuperación reconstruida | IC95 marginal exploratorio |\n|---|---|---:|---:|\n'
    for a in report['summary']['by_peril']:
        if a['peril'] in ['bodily_injury', 'subsidence']:
            note += (f'| {a["line"]}, {a["peril"]} | {a["cut"]} | {100*a["reconstructed_recovery"]:.4f}% '
                     f'| [{100*a["exploratory_marginal95"][0]:.4f}%, {100*a["exploratory_marginal95"][1]:.4f}%] |\n')
    note += ('\nSe conservaron todas las salidas por peril, fold y trimestre de ocurrencia. En lesiones corporales '
             'el fold1 del corte2022 recupera 94,9149%, aunque el agregado del peril sea 99,5449%. '
             'Incendio2022 sobre-reconstruye aproximadamente 1,45%. Los intervalos por peril son marginales '
             'exploratorios; no se presentan como una familia de confirmaciones simultáneas. '
             'El diagnóstico Post31 excluye grupos solo del cálculo descriptivo, sin borrar datos o reajustar.\n\n')
    note += ('La reconstrucción usa el coste de siniestros ya reportados al corte como entrada y lo divide '
             'por la completitud de coste estimada para su antigüedad. No se afirmó que pudiera ignorar esa '
             'entrada. El coste de reportes posteriores solo sirve como referencia: al alterar sus marcas, '
             'periles y fechas no cambió la reconstrucción. Al alterar todos los retenidos y los reportes '
             'no disponibles del entrenamiento, las curvas quedaron exactamente iguales.\n\n')
    note += ('Los 30 ámbitos pasaron la comprobación independiente del conjunto de riesgo por búsquedas ordenadas, '
             'producto-límite por logaritmos y CDF/marca de coste por probabilidades de evento. El replay del flujo '
             'real, con estimación bloqueada, recuperó exactamente 78.081 contribuciones reportadas de los dos cortes. '
             'El bootstrap Poisson por componentes comparte los mismos pesos entre ventanas y periles; '
             'condiciona en las curvas ajustadas y no representa incertidumbre completa de su estimación. '
             'Los componentes con coste nulo se conservan en la cohorte y se omiten solo de las multiplicaciones '
             'de ratios donde aportan exactamente cero.\n\n')
    note += ('La cohorte contiene 311.317 componentes, de los que 34.571 aportan coste positivo. '
             'Se conciliaron los céntimos con los periodos fuente guardados. El intento técnico V1 se detuvo '
             'antes de ajustar porque exigía que todo siniestro de calendario2021 perteneciera a coberturas2021. '
             'V2 conserva por separado 34 siniestros de autos, nueve de edificios y cinco de contenidos '
             'fuera de ese ámbito, con IDs exactamente iguales a los no asignados históricos. '
             'El denominador sigue siendo el de coberturas asignadas definido antes de cualquier resultado. '
             'Código/fallo V1 quedan preservados con cero ajustes; no se descartaron filas para mejorar el contraste.\n\n')
    fit_count = report['counts']['primary']['reporting_completed']
    note += (f'Coste: {fit_count} ajustes de reporte primarios y {report["counts"]["poison"]["reporting_completed"]} '
             'controles adversos separados. Se reutilizó una distribución por papel al ser idénticos todos '
             'los eventos/marcas y estar completamente observados en ambas ventanas; se cotejó la identidad '
             'con el conjunto de riesgo. Los 21 ajustes sintéticos se registran aparte. No hubo modelos de precio, '
             'C0 emergente, inferencias de modelos fuente, nuevos precios 2025, scores competitivos o envíos. '
             'El CSV P6 conserva su SHA.\n\n')
    note += ('Las limitaciones siguen siendo relevantes: un mercado fuente no aporta soporte emergente, '
             'la referencia observada2024 puede omitir desarrollos posteriores y las marcas finales no eran '
             'necesariamente conocidas en los cortes virtuales. La estacionalidad, dependencia de severidad '
             'y diferencias de cartera son explicaciones alternativas. La consulta bibliográfica archivada '
             'contiene resúmenes/fichas primarias; el acceso directo a los artículos falló y no se declara '
             'lectura íntegra o validación del método por esas fuentes.\n\n')
    note += ('Decisión: no adoptar un factor de cola fuente, no reescalar P6 a F3c y no modificar el objetivo '
             'nominal. La revisión siguiente comprobará contratos reales de variables, exposición y normalización '
             'de los backbones. En particular, una prueba de exposición sobre relatividades fuente ya guardadas '
             'no equivale a cambiar la exposición dentro de toda la inferencia fuente desde datos crudos. '
             'Cualquier discrepancia nueva material necesitará una prueba propia registrada antes de inferir o ajustar. '
             'B00, F3c, P6 y todas las alternativas/fallos permanecen; 2024 sigue abierto adaptativo y la privada '
             'continúa como prioridad. No se acredita mejora privada, promoción o validación profesional independiente.\n\n')
    note += f'Evidencia: {w.rel(OUT/"report.json")}; {w.rel(OUT/"replay_report.json")}; {w.rel(OUT/"preflight.json")}.\n'
    doc = R/'docs/semana2/PRIVADA_P7_VENTANA_REPORTE_MADURA.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P7-VENTANA-RESULTADO', '--asunto',
                             'P7: recuperación fuente cercana a100%; no hay base para un uplift global de cola', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': report['status'], 'report': w.rel(OUT/'report.json'),
               'report_sha256': w.sha(OUT/'report.json'), 'replay': w.rel(OUT/'replay_report.json'), 'replay_sha256': w.sha(OUT/'replay_report.json'),
               'document': w.rel(doc), 'forum': json.loads(result.stdout), 'primary': report['summary']['primary'],
               'counts': report['counts'], 'new_price_model_fits': 0, 'new_target_C0fits': 0,
               'new_source_model_inference': 0, 'new_targetprice_predictions': 0, 'new_finaltestprices': 0, 'new_submissions': 0,
               'source_tail_prior_adopted': False, 'cause_of_P6_F3c_gap_established': False,
               'P6_CSV_unchanged': True, 'P6_CSV_sha256': p6['CSV']['sha256'], 'formal_promotion': False,
               'submission_allowed': False, 'private_improvement_established': False, '2024_open': True,
               'B00_all_alternatives_preserved': True, 'goal_achieved': False, 'next_unit': next_unit}
    counters_path = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(counters_path)
    assert 'phase2_private_P7_mature_reporting_window' not in counters
    w.update(counters_path, {'as_of_utc': stamp.isoformat(),
                             'supplementary_reporting_peril_fits_since_counter_start': counters['supplementary_reporting_peril_fits_since_counter_start']+fit_count,
                             'diagnostic_reporting_fits_since_private_priority_separate': counters.get('diagnostic_reporting_fits_since_private_priority_separate', 0)+fit_count,
                             'phase2_private_P7_mature_reporting_window': {'counts': report['counts'], 'pricing_curves': 0,
                                                                        'new_diagnostic_weighted_mark_means_threebranches_separate': 3*fit_count,
                                                                        'synthetic_reporting_fits_excluded': 21, 'v1_real_fits': 0,
                                                                        'new_price_model_fits': 0, 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, archive)
    index = R/'registro/semana2_ventana_reporte_madura_actual.json'; w.update(index, receipt, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'; w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P7': receipt, 'next_unit': next_unit}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase, {'utc': stamp.isoformat(), 'private_P7': receipt, 'mission_private_priority': w.read(priority),
                     'new_P7_diagnostic_reporting_fits_separate': fit_count, 'new_P7_adverse_reporting_fits_separate': report['counts']['poison']['reporting_completed'],
                     'next_unit': next_unit, 'active_execution': None, 'active_jobs': [],
                     'last_goal_turn_classification': 'progress: mature-source cross-group reporting-window backtest and protected replay complete; no support for hypothesized large global tail uplift, alternative backbone review prioritized'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P7=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, active_jobs=[], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_mature_reporting_window_index': w.rel(index),
                                        'week_2_private_mature_reporting_window_report': w.rel(doc)}, archive)
    summary = ('\n\n## Ventana de reporte madura revisada, 26 de octubre de 2026\n\n'
               'P7reconstruyó99,9674%y100,0301%del coste fuente2021conocido a2024desde cortes virtuales2022/2023. '
               'No respalda un incremento general de cola para explicar la brecha de10,83%; no se transporta ese resultado como soporte emergente. '
               'Se mantienen marcas finales comunes, límites de referencia y bootstrap condicional. '
               'No hubo modelos/precios competitivos o envíos nuevos. P6no cambia. La siguiente revisión se centra en variables y normalización de las bases. '
               '[InformeP7](PRIVADA_P7_VENTANA_REPORTE_MADURA.md).\n')
    w.append(R/'docs/semana2/MISION_PRIVADA_PRIORIDAD_Y_PLAN.md', summary, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_submissions': 0,
                      'source_tail_prior_adopted': False, 'P6_unchanged': True}))


if __name__ == '__main__': main()
