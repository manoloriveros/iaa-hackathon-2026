"""Registra el hallazgo estático P8 sin interpretar splits como efecto causal."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P8_contrato_fuente_estatico_20261026_v1'
sp = importlib.util.spec_from_file_location('P8_contract_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    stamp = datetime.now(timezone.utc)
    # A short private archive root avoids recursively duplicating the long
    # source path inside its own directory on Windows. Original data stay put.
    cut = R/'privado'/('corte_P8_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir(parents=True)
    assert len(str(cut/(OUT/'report.json').relative_to(ROOT))) < 250
    if not (OUT/'integration_path_failure.json').exists():
        (OUT/'integration_path_failure.json').write_text(json.dumps({
            'author': 'Codex', 'utc': stamp.isoformat(), 'stage': 'before_first_report_update_or_document/forum_write',
            'failure': 'Windows MAX_PATH while saving a private report under its own long state_cuts hierarchy',
            'effect_on_model_or_science': 'None; failed before report write, no fit/inference/price or forum mutation',
            'repair': 'Use short private archive root and preserve original artifacts',
        }, ensure_ascii=False, indent=2), encoding='utf8')
    report = w.read(OUT/'report.json')
    traincode = R/'herramientas/entrenar_nucleo_A1S.py'
    report['source_hashes'][w.rel(traincode)] = w.sha(traincode)
    report['offset_contract'] = ('Existing source-only log(e_cost)+source initialbase as init_score; exposure_model also supplied '
                                 'as a predictor. This is not automatically double counting or leakage; it creates a separate feature-dependence path.')
    w.update(OUT/'report.json', report, cut)
    next_unit = (
        'Preregister and implement P8finite frozen-source exposure-feature sensitivity, no newfit or pricecandidate. '
        'Choose up to64future rows per line deterministically by rowid within NB/RENand calendar-durationcells, without '
        'labels/predictions. Bind cached source matrices/model featureorder and baselineper-seed logrelativity/centre exactly. '
        'Compare unchanged input versus two fixed shorter-day-count exposure_model values, holding all other sourcefeatures '
        'and sourcecentres fixed; label this isolated source-feature probe, not a coherent completeS2/H1forecast or a test '
        'that annualrisk must be durationneutral. Use all9fixedsourceboosters, budget primary<=1728raw prediction rows '
        'plus<=216leafsumcontrolrows; no sourcefit/C0/calibration/fulltargetprices/publicscore. Verify changedinputpredictions '
        'by independently summing savedtree leafvalues, with category/NaNschema explicit. Freeze code/criterion/configuration/'
        'cost and forum comment before newsourceinference; report all lines/seeds/strata without selecting a feature removal, '
        'level or alternative by probevalue. Preserve current CSVand private-validationadverses,2024open,B00/F3c/alternatives, '
        'no uploads. Materialmodeldependence only motivates a future validation; it does not prove a bug or explain10.83percent.'
    )
    note = '\n\n## Privada P8, revisión estática previa del contrato fuente, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se revisaron los textos de los nueve modelos fuente congelados y sus listas de variables, sin cargarlos para inferencia. '
    note += ('La suma de índices de partición de sus árboles coincide con la importancia por número de splits guardada en cada archivo. '
             'exposure_model está presente y activo en los nueve: 195/170/234 splits en autos, 99/136/74 en edificios y '
             '393/372/333 en contenidos. El capital log_si está presente y activo en edificios y contenidos; '
             'no se declara una omisión de capital.\n\n')
    note += ('El contrato de entrenamiento usa log(e_cost) como offset de fuente y también permite exposure_model como predictor. '
             'La prueba de escalado de calendario de P6 mantuvo constantes las relatividades fuente guardadas. '
             'Por tanto, no cubre la ruta que cambia ese predictor dentro del modelo fuente. Esto no demuestra doble conteo, '
             'fuga, error o causa de la brecha: la duración puede representar diferencias de riesgo o selección de cartera. '
             'Los conteos de splits tampoco miden magnitud o calidad predictiva.\n\n')
    note += ('Siguiente unidad: registrar una prueba finita de sensibilidad del predictor de exposición en los nueve modelos congelados. '
             'Selección determinista sin respuestas, dos intervenciones fijas de días más cortos, ancla con cachés/centros originales '
             'y suma de hojas independiente. Será una intervención parcial de variables fuente; no se presentará como una cotización '
             'alternativa o prueba de que todo riesgo anual deba ser constante. Antes de inferir se congelarán código, criterio, '
             'configuración, coste y comentario previo. No se decide retirar la variable, reescalar, entrenar otra familia o enviar '
             'por esta revisión. La autorización humana automática existente sigue vigente; lo pendiente es concretar y verificar '
             'la prueba, no solicitar otra aprobación.\n\n')
    note += ('Cero ajustes, modelos cargados para predecir, inferencias, precios, scores o envíos nuevos. P6 y sus límites permanecen; '
             'B00/F3c/alternativas intactos y 2024 abierto adaptativo. Evidencia: '+w.rel(OUT/'report.json')+'.\n')
    doc = R/'docs/archivo/semana2/PRIVADA_P8_CONTRATO_FUENTE_PREVIO.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P8-CONTRATO-ESTATICO', '--asunto',
                             'P8 previo: exposición activa en fuente, capital presente; sensibilidad pendiente', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': report['status'], 'report': w.rel(OUT/'report.json'),
               'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(doc), 'forum': json.loads(result.stdout),
               'new_model_fits': 0, 'new_source_inference': 0, 'new_price_predictions': 0, 'new_scores': 0, 'new_submissions': 0,
               '2024_open': True, 'B00_all_alternatives_preserved': True, 'feature_removal_adopted': False,
               'goal_achieved': False, 'next_unit': next_unit}
    index = R/'registro/semana2_contrato_fuente_exposicion_actual.json'; assert not index.exists()
    index.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P8_static': receipt, 'next_unit': next_unit}, cut)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'utc': stamp.isoformat(), 'private_P8_static': receipt,
             'mission_private_priority': w.read(priority), 'next_unit': next_unit,
             'last_goal_turn_classification': 'progress: P7negative-tail finding closed, actual frozen-source exposure-feature route identified statically; no unsupported correction adopted'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P8_static=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_exposure_contract_index': w.rel(index),
                                        'week_2_private_source_exposure_contract_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_inference': 0}))


if __name__ == '__main__': main()
