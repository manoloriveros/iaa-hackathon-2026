"""Registra solo la recuperación nueva de motor/contenidos y su coste real."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; HOME = BASE / 'FSp_MC_recuperacion_20261026_v1'; OUT = HOME / 'productor'
spec = importlib.util.spec_from_file_location('writer_MC_finished', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    assert not (OUT / 'completion_receipt.json').exists()
    report = w.read(OUT / 'report.json'); assert len(report['models']) == report['new_source_component_model_fits'] == 36
    assert report['new_C0_fits'] == report['new_scores'] == report['new_submissions'] == 0
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = ('Los36modelos MC y los24de edificios ya están completos, con matrices/modelos/componentes guardados: no repetirlos. '
        'Preparar y registrar un contraste único de FSp aislado sobre la referencia G3 de factores residuales guardados, sin reestimarlos, '
        'solo REN y pesos fijos recibidos motor.25/buildings.25/contents.5. '
        'La calibración recibida contiene kf/ks/kg y n/(n+100), distinta de la igualación de coste sin contracción probada antes en edificios; '
        'documentar esa necesidad y adaptar expresamente a C0 protegido por grupos, sin llamarlo replay exacto de F4c. '
        'Usar los ámbitos guardados, exposición una sola vez, NB/total de celda fijos y los criterios sin relajar. '
        'Registrar antes de estimar constantes o puntuar. Sin nuevos árboles/C0/test/envíos en el contraste. '
        'El F3c completo sigue como comparador no reproducido íntegramente; G3 es proxy.2024abierto;cuota0;meta0.17activa.')
    note = '\n\n## Motor y contenidos: componentes fuente recuperados, 26 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se completó la recuperación registrada de motor y contenidos: 36 modelos Poisson/Gamma con las rondas fuente existentes, '
        'sin nueva búsqueda ni reestimación de C0. Pasaron 196 cotejos de precisión de variables y 18 comprobaciones de recuentos, marcas y offsets. '
        'Se guardaron todos los modelos y sus salidas f/s/brutas para las fases fuente 2021–2023 y 2021–2024. '
        'El historial usa explícitamente el corte min(inicio,2024-12-31), y el clima se limita a las ventanas históricas por fase. '
        'No se leyó clima 2025 ni respuestas emergentes en este productor.\n\n'
        'Los 36 modelos pasaron la reproducción exacta al guardar/cargar y al invertir el orden de las filas. '
        'Se comprobó la suma independiente de hojas y la aplicación del offset/exposición por otra fórmula. '
        'Todos los componentes son finitos y positivos; las fuentes conservaron sus huellas. La recuperación produce componentes nuevos para 2025 '
        'y ese trabajo se cuenta, aunque todavía no exista un nuevo precio agregado: ' + str(report['new_component_row_predictions_before_replays']) +
        ' predicciones de componente antes de replays. No se reivindica identidad bit a bit con árboles originales no guardados.\n\n'
        'El inventario de los aportes recibidos se conservó: tres raíces, sin Parquet FSp ni archivos de modelos numéricos disponibles en ellas; '
        'no es una afirmación de ausencia global. Las dos carpetas ya revisadas y la búsqueda K anterior no se repitieron. '
        'El código y la receta son de Claude; esta reconstrucción, verificaciones y registro son de Codex. No equivalen a revisión profesional independiente.\n\n'
        'La revisión del código de calibración recibido encontró kf/ks/kg y contracción fija n/(n+100). '
        'La prueba adversa anterior de edificios usó otra igualación de coste, sin contracción, y sigue guardada con ese ámbito. '
        'Antes de comparar el componente recuperado se registrará la diferencia de receta y el uso de C0 retenido por grupos; '
        'no se retocará K o el peso por el score adverso. La frecuencia conserva la semántica de proxy basada en completitud de coste, '
        'con reservas y cola de último no identificadas. Los maestros sin fecha también siguen condicionados.\n\n'
        'Coste nuevo: 36 ajustes fuente, cero C0, calibraciones emergentes, scores o envíos. Los 24 modelos anteriores de edificios no se ajustaron otra vez. '
        'Quedan 167 ajustes nuevos en la fase y 1.503 en el contador propio acumulado; se preserva el linaje de esos conteos. '
        'El mejor público continúa en 0,16914, con 0,00086 pendientes para 0,17. B00, F2/C1/F3c, los fallos y las alternativas quedan guardados. '
        '2024 permanece abierto como desarrollo adaptativo y la cuota 0 se conserva para el siguiente periodo.\n\n'
        'Evidencia: ' + w.rel(OUT / 'report.json') + '; matrices: ' + w.rel(HOME / 'matrices/report.json') +
        '; semántica de calibración recibida: ' + w.rel(HOME / 'calibracion_recibida_contrato.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FSp_MOTOR_CONTENIDOS_RECUPERACION.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-MC-RECUPERACION-RESULTADO',
        '--asunto', 'Motor y contenidos recuperados: 36 modelos fijos, falta contraste predictivo', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'source_recovery_complete_no_predictive_admission',
               'report': w.rel(OUT / 'report.json'), 'report_sha256': w.sha(OUT / 'report.json'), 'document': w.rel(doc),
               'new_source_component_model_fits': 36, 'new_C0_fits': 0, 'new_scores': 0, 'new_submissions': 0,
               'new_component_row_predictions': report['new_component_row_predictions_before_replays'],
               'goal_achieved': False, '2024_open': True, 'next_unit': next_unit, 'forum': json.loads(response.stdout)}
    counter = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counter); assert 'phase2_source_FSp_MC_recovery' not in c
    w.update(counter, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': c['cumulative_price_base_fits'] + 36,
                       'phase2_source_FSp_MC_recovery': {**receipt, 'included_in_cumulative_price_base_fits': True}}, archive)
    phasepath = R / 'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phasepath)
    assert phase['new_price_fits'] == 131
    w.update(phasepath, {'utc': stamp.isoformat(), 'FSp_MC_source_recovery': receipt, 'active_execution': None,
                         'new_price_fits': phase['new_price_fits'] + 36,
                         'new_recovered_source_FSp_component_fits': phase['new_recovered_source_FSp_component_fits'] + 36,
                         'next_unit': next_unit}, archive)
    statepath = ROOT / 'Preparación/ESTADO_PROYECTO.json'; own = w.read(statepath)['week_2_mission017_phase2_20261025']
    own.update(FSp_MC_source_recovery=receipt, new_price_fits=167, active_jobs=[], next_unit=next_unit)
    w.update(statepath, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    index = R / 'registro/semana2_mision017_renovaciones_FSp_actual.json'
    w.update(index, {'utc': stamp.isoformat(), 'status': 'all_source_components_recovered_predictive_comparison_pending',
                     'motor_contents_source_recovery': receipt, 'next_unit': next_unit}, archive)
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / filename, note, archive)
    w.append(R / 'docs/archivo/semana2/MISION017_RENOVACIONES_Y_RECUPERACION_FSp.md', note, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_FSp_MC_recovery_report': w.rel(doc)}, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'new_source_models': 36, 'phase_price_fits': 167,
                      'new_C0_fits': 0, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
