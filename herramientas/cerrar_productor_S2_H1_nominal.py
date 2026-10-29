"""Registra P6 como productor reproducible y CSV técnico, sin admisión o envío."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P6_productor_S2_H1_nominal_20261026_v1'
sp = importlib.util.spec_from_file_location('P6_state_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); replay = w.read(OUT/'independent_process_replay.json')
    export = w.read(OUT/'reproduccion_comando_2025.receipt.json'); context = w.read(OUT/'level_context.json')
    assert report['counts']['reporting_completed'] == 15 and report['counts']['closed_calibrations'] == 6
    assert replay['CSV_bytes_exact'] and export['sha256'] == report['CSV']['sha256']
    assert w.sha(ROOT/report['CSV']['path']) == report['CSV']['sha256']
    assert report['new_submissions'] == 0 and not report['F3c_predictions_consumed']
    stamp = datetime.now(timezone.utc); archive = OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ'); archive.mkdir(parents=True)
    next_unit = (
        'Finite review of the material final-level gap without rescaling to F3c or using publicfeedback. '
        'First identify existing mature-developed-cohort observation-window/pseudo-truncation evidence '
        'in current code/results to avoid repeating old lateclaim inventories or C0suites. The new full '
        'targetC0uses at most2023/2024reporting support while ultimate2025pricing assumes full completion; '
        'unobserved late tail is not identified by targetdata. If no equivalent audit exists, preregister '
        'a conditional mature2021source-cohort censoring-window backtest before any estimatorfit, with '
        'protected groups, earlier reportcutoffs and common final marks explicitly distinguished from '
        'prospective valuation. Measure reconstruction of mature observed cost, not hidden private scores. '
        'Source market cannot be counted as emerging support and no source-tail prior is adopted by this '
        'proposal. Inspect backbone/calibration differences as alternate explanations; aggregate gap '
        'alone does not establish cause. Keep P6nominalCSV unchanged/unadmitted, no quotas/upload, '
        'B00/F3c/all alternatives preserved, adaptive2024open and private priority.'
    )
    note = '\n\n## Privada P6: productor nominal S2/H1 y CSV reproducible, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se preparó un CSV técnico de 209.063 predicciones con la base S2/H1 que se ha evaluado localmente. '
    note += ('El productor ajustó la base estándar con los 109.296 periodos de 2023–2024 y reutilizó las tasas fuente, '
             'relatividades A1S y cinco correcciones H1/G3 de producción ya guardadas. No consumió los precios F3c '
             'ni la forma de renovaciones de PUL2. Se conservaron objetivo T0, modelos fuente, credibilidad, variables '
             'y pesos del algoritmo. La ampliación de tamaños de entrenamiento, de 80/64% a 100/80%, es el ajuste '
             'final habitual del algoritmo; no se presenta como una nueva validación o una mejora probada por tener más datos.\n\n')
    note += '| Artefacto o control | Resultado |\n|---|---|\n'
    note += f'| CSV técnico | `{Path(report["CSV"]["path"]).name}` |\n'
    note += f'| Filas y orden oficial | {report["CSV"]["rows"]:,}; coincidencia exacta |\n'
    note += '| Redondeo | Una sola vez, tras la media, a seis decimales; racional binario y Decimal independientes |\n'
    note += '| Replay con respuestas futuras corruptas | Exacto, con ajustes bloqueados |\n'
    note += '| Reordenar toda la cartera | Precios idénticos tras orden canónico |\n'
    note += '| Otro proceso y comando de exportación | Mismo CSV byte por byte |\n'
    note += '| Envíos o scores nuevos | Ninguno |\n\n'
    note += ('La aplicación exige la cartera completa porque sus normalizadores dependen de ella. Rechaza '
             'claves faltantes/duplicadas, lotes parciales, año incorrecto y exposición no positiva. '
             'Los marcadores observados cero de 2025 no entran en el precio último; se usa una sola exposición calendario. '
             'El flujo sintético de los tres ramos también verificó la identidad al reducir a la mitad toda la exposición, '
             'la paridad del componente N3 y el rechazo de entrenamiento con periodos futuros.\n\n')
    constants = report['counts']['constants']['price_total']
    note += (f'Se hicieron únicamente 15 ajustes de reporte y seis calibraciones cerradas, con {constants} constantes '
             'de precio. No se repitieron los modelos fuente o miembros ya aprendidos. Las 15 curvas y nueve aprendices '
             'sintéticos, controles de replay y normalizadores se cuentan aparte. Los nuevos C0 completos pasaron el '
             'cotejo de marcas/CDF por probabilidades de evento; los niveles se comprobaron por sumas escalares. '
             'Los SHA de fuentes registradas permanecieron iguales.\n\n')
    note += ('El proceso independiente reconstruyó todas las predicciones desde JSON y Parquet guardados, con 13 '
             'entradas de estimación bloqueadas. Se validó después un comando de exportación real que escribe otra '
             'copia exacta; su código tiene su propio recibo, sin atribuirle automáticamente el anterior. '
             'La reproducción comprobada es local y usa las cachés fuente preparadas del workspace. '
             'No se ha verificado portabilidad a otra máquina o un productor de nuevas cohortes desde datos crudos.\n\n')
    note += '| Contexto de nivel, sin score predictivo nuevo | Coste total CU |\n|---|---:|\n'
    note += f'| Base S2 completa, antes de H1 | {context["P6_S2base_unrounded_total_CU"]:,.2f} |\n'
    note += f'| Candidato S2/H1 | {report["CSV"]["total_CU"]:,.2f} |\n'
    note += f'| F3c conservado, CSV publicado previamente | {context["reference_F3c_total_microCU"]/1_000_000:,.2f} |\n'
    note += (f'\nLa corrección H1 aumenta la base S2 un {context["H1_increment_on_S2_percent"]:.4f}%. '
             f'El nuevo candidato tiene un total {abs(context["P6_minus_F3c_percent"]):.4f}% menor que F3c. '
             'La diferencia de base es material y no se ha aislado su causa. No demuestra una mejora o deterioro privado, '
             'ni autoriza igualar totales con un multiplicador. La referencia F3c conserva su recibo público 0,16914; '
             'ese score no pertenece a este nuevo CSV.\n\n')
    note += ('Decisión: conservar el CSV como artefacto técnico reproducible, sin promoción, admisión predictiva '
             'o envío. Persisten los adversos de precios congelados, la pérdida en autos nuevos de 2023 con reservas125, '
             'el mínimo nominal conjunto incumplido y el escaso soporte hacia la cartera de 2025. '
             '2023/2024 siguen siendo desarrollo adaptativo; los maestros sin fecha, la valoración común y la cola tardía '
             'limitan la interpretación. Ninguna revisión propia constituye aprobación humana o validación profesional independiente. '
             'B00, F3c y todas las alternativas/fallos se conservan; 2024 permanece abierto.\n\n')
    note += ('El siguiente paso es revisar la brecha de nivel y la evidencia disponible sobre ventanas de reporte '
             'en cohortes desarrolladas maduras, comprobando primero qué se hizo ya. La nueva C0 completa solo '
             've la historia emergente 2023/2024 y no identifica una cola posterior a su soporte. Un backtest de '
             'ventanas sobre una cohorte madura puede comprobar esa limitación del estimador, condicionado a marcas '
             'finales y mercado fuente; necesita receta, grupos, cortes y criterio previos si aún no existe. '
             'No aportará soporte emergente por sustitución ni se adoptará un prior de cola sin evidencia. '
             'También se conservarán como explicaciones alternativas las diferencias de backbone y calibración.\n\n')
    note += f'Evidencia: {w.rel(OUT/"report.json")}; {w.rel(OUT/"independent_process_replay.json")}; {w.rel(OUT/"reproduccion_comando_2025.receipt.json")}; {w.rel(OUT/"level_context.json")}.\n'
    note += f'\nSHA256 del CSV: `{report["CSV"]["sha256"]}`.\n'
    doc = R/'docs/archivo/semana2/PRIVADA_P6_PRODUCTOR_NOMINAL_Y_CSV.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    readme = ('# Productor nominal S2/H1, P6\n\n'
              'CSV técnico reproducible para la cartera oficial 2025. No enviado ni promovido. '
              'Los resultados de validación y sus adversos están en el informe P6.\n\n'
              'El modelo usa la base S2 calibrada con2023/2024y la media de cinco cocientes H1/G3 guardados. '
              'Las fuentes permanecen congeladas. Los parámetros están en parameters_motor, parameters_buildings y parameters_contents; '
              'production_artifacts_manifest.json registra las huellas. future_*.parquet y components_*.parquet son las entradas congeladas.\n\n'
              'Desde este workspace se puede regenerar el CSV sin ajustar ni enviar. Elegir una ruta de salida nueva:\n\n'
              '```powershell\n'
              "& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/herramientas/exportar_S2_H1_guardado.py' --output 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P6_productor_S2_H1_nominal_20261026_v1/reproduccion_usuario_2025.csv'\n"
              '```\n\n'
              'El comando rechaza sobrescrituras y requiere las fuentes registradas. La copia de comprobación reproduccion_comando_2025.csv '
              'tiene los mismos bytes que codex_S2_H1_nominal_2025.csv. No usa una API de Kaggle. '
              'Se verificó la reproducción local; no portabilidad o reconstrucción cruda en otra máquina.\n\n'
              'No usar un lote parcial: los normalizadores pertenecen a toda la cartera. '
              'Los resultados privados siguen siendo desconocidos y no hay autorización predictiva nueva por crear este archivo.\n')
    (OUT/'README.md').write_text(readme, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, note, archive)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P6-PRODUCTOR-RESULTADO', '--asunto',
                             'P6: CSV S2/H1 reproducible; brecha de nivel pendiente y ningún envío', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': report['status'],
               'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
               'CSV': report['CSV'], 'model_manifest': w.rel(OUT/'production_artifacts_manifest.json'),
               'model_manifest_sha256': w.sha(OUT/'production_artifacts_manifest.json'),
               'independent_replay': w.rel(OUT/'independent_process_replay.json'),
               'independent_replay_sha256': w.sha(OUT/'independent_process_replay.json'),
               'export_command': w.rel(R/'herramientas/exportar_S2_H1_guardado.py'),
               'export_command_sha256': w.sha(R/'herramientas/exportar_S2_H1_guardado.py'),
               'export_test': w.rel(OUT/'reproduccion_comando_2025.receipt.json'),
               'export_test_sha256': w.sha(OUT/'reproduccion_comando_2025.receipt.json'),
               'level_context': context, 'document': w.rel(doc), 'forum': json.loads(result.stdout), 'counts': report['counts'],
               'new_model_fits': 0, 'new_C0_fits': 15, 'new_closed_calibrations': 6, 'new_source_inference': 0,
               'new_candidate_final_price_rows': 209063, 'diagnostic_base_rows': 209063,
               'new_predictive_CSVs': 1, 'reproduced_CSV_copies': 1,
               'new_submissions': 0, 'formal_promotion': False, 'submission_allowed': False,
               'private_improvement_established': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
               'goal_achieved': False, 'next_unit': next_unit}
    counter_path = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(counter_path)
    assert 'phase2_private_P6_nominal_producer' not in counters
    w.update(counter_path, {'as_of_utc': stamp.isoformat(),
                            'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+constants,
                            'supplementary_reporting_peril_fits_since_counter_start': counters['supplementary_reporting_peril_fits_since_counter_start']+15,
                            'mixture_frequency_constants_since_counter_start_separate': counters['mixture_frequency_constants_since_counter_start_separate']+15,
                            'mixture_positive_severity_means_since_counter_start_separate': counters['mixture_positive_severity_means_since_counter_start_separate']+45,
                            'phase2_private_P6_nominal_producer': {'counts': report['counts'], 'new_source_inference': 0,
                                                                 'synthetic_C0_fits_excluded': 15, 'synthetic_closed_learners_excluded': 9,
                                                                 'normalizers_separate': {'primary': 8, 'embedded_replay': 8, 'shuffle': 8, 'other_process': 8, 'CLIexport': 8},
                                                                 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, archive)
    index = R/'registro/semana2_productor_S2_H1_nominal_actual.json'; w.update(index, receipt, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P6': receipt, 'next_unit': next_unit}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; old = w.read(phase)
    w.update(phase, {'utc': stamp.isoformat(), 'private_P6': receipt, 'mission_private_priority': w.read(priority),
                     'new_C0_fits': old['new_C0_fits']+15, 'new_emerging_C0_fits': old['new_emerging_C0_fits']+15,
                     'next_unit': next_unit, 'active_execution': None, 'active_jobs': [],
                     'last_goal_turn_classification': 'progress: actual nominal validated-family producer, full-target parameters, final CSV, other-process replay and export command verified; unresolved level/support risks retained'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P6=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, active_jobs=[], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_nominal_producer_index': w.rel(index),
                                        'week_2_private_nominal_producer_report': w.rel(doc),
                                        'week_2_private_nominal_unadmitted_CSV': report['CSV']['path']}, archive)
    summary = ('\n\n## Productor nominal S2/H1 preparado, 26 de octubre de 2026\n\n'
               'P6generó209063predicciones con baseS2ajustada a todo2023/2024y las cinco correcciones H1/G3guardadas. '
               'CSV, replay separado y comando de exportación coinciden byteporbyte, sin nuevos modelos fuente o envíos. '
               'El total es77.816.901,61CU,10,83%menor queF3c. No se identificó la causa de la brecha ni se eligió un reescalado. '
               'Es un productor técnico reproducible, sin promoción o prueba de mejora privada. '
               'La revisión siguiente se centra en ventana de observación/cola y diferencias de base, después de comprobar qué evidencia existe. '
               'Los adversos y referencias permanecen;2024abierto adaptativo. [InformeP6](PRIVADA_P6_PRODUCTOR_NOMINAL_Y_CSV.md).\n')
    w.append(R/'docs/archivo/semana2/MISION_PRIVADA_PRIORIDAD_Y_PLAN.md', summary, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'CSV': receipt['CSV'], 'forum': receipt['forum'], 'new_submissions': 0}))


if __name__ == '__main__': main()
