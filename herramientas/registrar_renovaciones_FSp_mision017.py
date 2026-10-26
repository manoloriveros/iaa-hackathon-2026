"""Guarda conciliación, composición provisional y recuperación sin borrar otras ramas."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
PRODUCER = BASE / 'FSp_edificios_productor_20261026_v1'
P = R / 'registro/semana2_mision017_fase2_actual.json'
INDEX = R / 'registro/semana2_mision017_renovaciones_FSp_actual.json'
DOC = R / 'docs/semana2/MISION017_RENOVACIONES_Y_RECUPERACION_FSp.md'
spec = importlib.util.spec_from_file_location('writer_renewal_completion', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def ref(path):
    return {'path': w.rel(path), 'sha256': w.sha(path)}


def main(mode):
    stamp = datetime.now(timezone.utc)
    archive = PRODUCER / 'state_cuts' / (stamp.strftime('%Y%m%dT%H%M%SZ') + '_' + mode)
    archive.mkdir(parents=True)
    marker = PRODUCER / ('registration_' + mode + '_receipt.json')
    assert not marker.exists(), 'Do not duplicate registration or counters.'
    source_audit = BASE / 'renovacion_fsp_recepcion_20261026_v1/audit.json'
    candidate_report = BASE / 'renovacion_fsp_composicion_20261026_v1/report.json'
    inputs_report = BASE / 'FSp_edificios_recuperacion_entradas_20261026_v1/report.json'
    matrices_report = BASE / 'FSp_edificios_matrices_20261026_v1/report.json'
    refs = {'received_semantics_audit': ref(source_audit), 'provisional_candidate': ref(candidate_report),
            'count_offset_inputs': ref(inputs_report), 'raw_precision_matrices': ref(matrices_report),
            'producer_plan': ref(R / 'registro/semana2_mision017_FSp_edificios_recuperacion_plan_v1.json')}
    phase = w.read(P); statepath = ROOT / 'Preparación/ESTADO_PROYECTO.json'
    state = w.read(statepath); own = state['week_2_mission017_phase2_20261025']
    candidate = w.read(candidate_report)
    if mode == 'inputs':
        note = '\n\n## Renovaciones y entradas completas de edificios, 26 de octubre de 2026 (Bogotá)\n\n'
        note += f'Codex, {stamp.isoformat()}. '
        note += ('La conciliación establece que F3c/F3b y F4c/F4b solo cambian el nivel de las seis celdas de renovación, dentro del redondeo de los CSV. '
            'Sin embargo, poner a cero el peso FSp de nuevo negocio en la receta K recibida no congela sus precios: '
            'también se vuelven a estimar factores comunes aplicados a ese negocio. No se atribuye pureza FSp a una diferencia entre los CSV compuestos. '
            'La fórmula original K además diluye los multiplicadores F2; la variante posterior F4b conserva esos multiplicadores. No son un replay idéntico.\n\n'
            'Se conservó una composición provisional F3c/F4c solo para las renovaciones de motor y contenidos, registrada antes de construirla. '
            'Cambia37.504filas;171.559precios, incluido todo nuevo negocio y edificios, quedan exactamente iguales. '
            'Los totales de las dos celdas afectadas se mantienen antes del redondeo y la diferencia final conjunta es0,000051CU. '
            'Pasaron claves/orden, identidades, datos fuera de ámbito alterados, escala del donante y aritmética racional independiente. '
            'Es una composición del donante F4c con FSp y factores reestimados, no un componente FSp puro ni el K ausente. '
            'No tiene validación predictiva acreditada y no está lista para enviar.\n\n'
            'Edificios en renovación no fue rechazado por la evidencia recibida. Falta en este CSV provisional porque F4c tiene peso cero en edificios; '
            'el objetivo sigue siendo evaluar la alternativa completa. Las previsiones recibidas para K favorecían la variante con edificios, '
            'pero no se trasladan numéricamente a nuestra composición. No se repitió el inventario del CSV K que ya faltaba.\n\n'
            'Se conciliaron las12combinaciones fase/peligro de edificios: recuentos, marcas positivas y constantes de offset coinciden con los metadatos originales; '
            'el máximo error de b0 es0. Se restauraron las matrices desde los originales porque32variables fuente estaban cuantizadas a float32. '
            'Pasaron45controles de fuente al aplicar su redondeo original y45de histórico emergente en precisión completa. '
            'Hay523.725filas fuente en desarrollo,707.726en producción y79.742filas emergentes por fase, incluidas52.295de2025. '
            'Clima separado: fuente2021–2023/emergente2023 para desarrollo; fuente2021–2024/emergente2023–2024 para producción. '
            'No se leyó clima2025. El historial termina en min(inicio,2024-12-31), ventana de365días [inicio,fin); '
            'se cotejó por otro método y con casos de frontera. No está acreditada la opción ambiental usada por FSp original en2025, '
            'por lo que cualquier recuperación será una reconstrucción nueva.\n\n'
            'Los productores recibidos no guardaban Boosters. Antes de reconstruirlos se registró la receta de24ajustes fuente de edificios '
            '(Poisson/Gamma, seis peligros, dos fases), con las rondas existentes y sin nueva búsqueda. Se reutilizan C0 y las constantes guardadas. '
            'La frecuencia mantiene el offset de completitud de coste: f*s sigue siendo un proxy de coste y no identifica frecuencia de último por separado. '
            'El productor guardará modelos y componentes por fila; no estima pesos nuevos, no puntúa ni produce un CSV para enviar.\n\n'
            'Esta conciliación y preparación suman cero ajustes, cero C0 y cero envíos; sí se creó un CSV provisional con37.504precios derivados y '
            'dos normalizaciones sin etiquetas, contados aparte. El productor tiene su propio presupuesto de24ajustes reales. '
            'El mejor recibo sigue en0,16914 y faltan0,00086para0,17. La cuota consultada sigue siendo0 y el trabajo local continúa. '
            'B00/F2/C1/F3c, versiones fallidas y todas las alternativas permanecen;2024está abierto como desarrollo adaptativo. '
            'La revisión es propia y exploratoria, sin certificación de mejora ni aprobación humana inventada.\n')
        forum_id = 'COD-S2-20261026-MISION017-RENOVACIONES-ENTRADAS-RESULTADO'
        status = 'input_preparation_complete_numerical_producer_registered'
        next_unit = ('Conciliar la ejecución del productor de edificios registrado; recuperar24modelos fuente con rondas fijas, sin repetir matriz/count/C0. '
            'Guardar modelos y f/s/raw porfila; cerrar controles numéricos y contadores antes de registrar comparación predictiva sobre ámbitos guardados. '
            'La composición REN motor/contenidos es provisional y edificios permanece pendiente de evaluación, no excluido por resultado. '
            'No asignar previsiones K a esa composición ni llamarla FSp puro.2024abierto, cuota0, objetivo0.17activo.')
        if (PRODUCER / 'started.json').exists() and not (PRODUCER / 'report.json').exists():
            started = w.read(PRODUCER / 'started.json')
            execution = {**started, 'status': 'running_registered_source_recovery', 'exec_session_id': 96621,
                         'code': w.rel(R / 'herramientas/recuperar_productor_FSp_edificios.py'),
                         'output': w.rel(PRODUCER), 'budget_source_fits': 24}
        else:
            execution = None
    else:
        assert INDEX.exists()
        report = w.read(PRODUCER / 'report.json')
        assert report['new_source_component_model_fits'] == 24 and len(report['models']) == 24
        refs['numerical_producer'] = ref(PRODUCER / 'report.json')
        note = '\n\n## Productor numérico de edificios recuperado, 26 de octubre de 2026 (Bogotá)\n\n'
        note += f'Codex, {stamp.isoformat()}. '
        note += ('Se completaron los24modelos fuente registrados de edificios con rondas fijas, sin búsqueda nueva ni reestimación de C0. '
            'Se guardaron todos los Boosters, metadatos, puntuaciones brutas y componentes f/s para79.742filas emergentes en cada fase. '
            'La fuente de desarrollo cubre2021–2023y la de producción2021–2024; no se cargaron respuestas emergentes. '
            'Los24modelos pasaron reproducción exacta al guardar/cargar y al cambiar el orden de las filas. '
            'La suma independiente de hojas y el cálculo separado de exponenciales/offset/exposición también coinciden. '
            'Los SHA de entrada permanecieron iguales y los componentes son finitos y positivos.\n\n'
            'Son componentes nuevos de modelo, incluidos los de test2025, y no se oculta ese coste:24ajustes fuente y1.913.808predicciones de componente '
            'antes de los replays. No son24calibraciones de objetivo emergente ni un nuevo CSV agregado. '
            'No hubo C0, búsqueda de rondas, puntuación predictiva o envío. La reconstrucción conserva la limitación del offset de coste y '
            'la opción explícita historia2; no acredita los árboles originales bit a bit ni mejora de F3c.\n\n'
            'El faltante del productor de edificios quedó resuelto para una comparación posterior; aún falta esa comparación por grupos y años, '
            'la separación de efectos FSp/factores en motor y contenidos y la validación del candidato completo de renovación. '
            'Antes de puntuar se registrarán comparador, pesos fijos, C0 reutilizado, grupos y criterio. '
            'No se escogerán pesos para perseguir0,17con el público. B00 y todas las alternativas permanecen,2024abierto. '
            'El mejor recibo procesado sigue0,16914; objetivo no alcanzado.\n')
        forum_id = 'COD-S2-20261026-MISION017-FSP-EDIFICIOS-RECUPERACION-RESULTADO'
        status = 'numerical_producer_complete_predictive_comparison_pending'
        next_unit = ('Registrar el contraste predictivo de componentes de edificios sobre los ámbitos/C0 ya guardados, antes de puntuar. '
            'Auditar procedencia y fórmula de las entradas requeridas para que el comparador F3c/F2 completo no se sustituya silenciosamente por N3. '
            'Separar2023/2024,NB/REN,peligros,nivel,cola y grupos; pesos no afinados con retenidos o público. '
            'FSp de motor/contenidos no está aislado en los donantes compuestos; no atribuir el efecto entero a FSp. '
            'Modelos y matrices ya completos: no repetir24fits,90cotejos,curvas o inventario K sin cambio. Cuota0conservada;0.17activo.')
        execution = None
    note += '\nEvidencia:\n\n' + ''.join('- ' + name + ': ' + item['path'] + '\n' for name, item in refs.items())
    body = PRODUCER / ('forum_' + mode + '_resultado.md'); body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', forum_id, '--asunto', 'Renovaciones: trazabilidad y componente de edificios ' + ('preparado' if mode == 'inputs' else 'recuperado'),
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': status, 'evidence': refs,
               'provisional_candidate_ready': False, 'B00_preserved': True, '2024_open': True,
               'predictive_improvement_established': False, 'goal_achieved': False,
               'next_unit': next_unit, 'forum': json.loads(response.stdout)}
    if mode == 'inputs':
        assert not INDEX.exists() and not DOC.exists()
        INDEX.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
        DOC.write_text(note, encoding='utf8')
        counters = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counters)
        assert 'phase2_renewal_composition_preparation' not in c
        w.update(counters, {'as_of_utc': stamp.isoformat(), 'phase2_renewal_composition_preparation': {
            'derived_candidate_files': 1, 'derived_price_rows': 37504, 'prediction_only_normalizers': 2,
            'new_price_fits': 0, 'new_C0_fits': 0, 'new_submissions': 0, 'receipt': receipt}}, archive)
    else:
        w.update(INDEX, receipt, archive); w.append(DOC, note, archive)
        counters = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counters)
        assert 'phase2_source_FSp_buildings_recovery' not in c
        w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': c['cumulative_price_base_fits'] + 24,
            'phase2_source_FSp_buildings_recovery': {'source_Poisson_Gamma_component_fits': 24,
                'counted_in_cumulative_price_base_fits': True, 'new_C0_fits': 0, 'new_scores': 0,
                'new_aggregated_submission_CSVs': 0, 'new_submissions': 0, 'receipt': receipt}}, archive)
    values = {'utc': stamp.isoformat(), 'renewal_FSp_recovery': receipt, 'active_execution': execution,
              'next_unit': next_unit, '2024_open': True, '2024_closed': False, 'status': 'active'}
    if mode == 'producer':
        values.update(new_price_fits=phase['new_price_fits'] + 24, new_recovered_source_FSp_component_fits=24)
    w.update(P, values, archive)
    own.update(renewal_FSp_recovery=receipt, next_unit=next_unit, active_jobs=[] if execution is None else [execution])
    if mode == 'producer':
        own['new_price_fits'] = values['new_price_fits']
    w.update(statepath, {'week_2_mission017_phase2_20261025': own,
                         'week_2_mission017_phase2_execution': execution}, archive)
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / filename, note, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_renewal_FSp_index': w.rel(INDEX),
        'week_2_mission017_renewal_FSp_report': w.rel(DOC)}, archive)
    marker.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': status, 'forum': receipt['forum'], 'next_unit': next_unit}, ensure_ascii=True))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['inputs', 'producer'])
    main(parser.parse_args().mode)
