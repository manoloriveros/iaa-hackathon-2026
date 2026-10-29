"""Conserva el adverso climático, el fallo de soporte y la siguiente necesidad estándar."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda7_clima_20261026_v2'
P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    validation = w.read(OUT / 'validation_v1/report.json'); price = w.read(OUT / 'price_report.json')
    assert len(validation['replays']) == 15 and len(validation['source_mathematics']) == 6
    assert not any(x['all_exploratory_checks_pass'] for x in validation['comparisons'].values())
    assert price['new_source_GLM_fits'] == 6 and price['new_test_predictions'] == 0
    phase = w.read(P); assert phase['new_price_fits'] == 54 and phase['new_submissions'] == 1
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    weights = w.read(BASE / 'estimando_cartera2025_v3/report.json')
    assert not weights['proposed_weighted_primary_estimand_eligibility']
    next_unit = (
        'Revisar y preparar recuentos de siniestros por peril del desarrollado 2021–2024, solo si no existe ya el vínculo completo recuperable. '
        'Reutilizar la asignación y T0 conciliados: mismos 604 duplicados fuente excluidos, siniestros2020 anteriores a cobertura solo para historia de reporte, ninguna póliza inventada. '
        'Buscar primero los objetos ya guardados de CDF de número de reportes y las recetas FS/FSp, para no repetir estimaciones o entrenamiento terminado. '
        'La necesidad a contrastar es separar respuesta de frecuencia del ruido de los importes en los efectos climáticos; el GLM de coste agregado no dio mejora estable y FSp histórico tuvo frecuencias que no aprendieron. '
        'No presentar otro FSp o FS de cuatro años como nuevo. Una eventual alternativa Poisson estándar necesita diferencia material documentada, exposición de número correcta por peril, fuentes verificadas y receta/coste/criterio registrados antes del ajuste. '
        'Este paso siguiente prepara evidencia y entradas; no ajusta modelos, rehace C0 emergente, cambia etiquetas, agrupa bandas o produce precios2025. '
        'Se conserva el umbral fallido de la ponderación2025 y no se usa para promover tandas anteriores. B00, F2, C1 y alternativas permanecen; último cupo conservado, objetivo0.17 activo.')
    note = '\n\n## Clima residual: resultado de la tanda 7, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se probaron seis GLM sencillos en la fuente desarrollada 2021–2024. La receta conserva el riesgo T2b persistente y añade efectos climáticos residuales. '
        'W1 usa anomalías de viento, incendio forestal, lluvia y temperatura; W2 añade granizo, heladas y sequedad del año; W3 aplica la mitad de W2 sin otro ajuste. '
        'Los controles de región y año se quedan en la fuente. Se conservaron los totales de cada ramo/año/negocio mediante covariables y predicciones, sin etiquetas retenidas.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Diferencia con mezcla de 2025, solo sensibilidad |\n|---|---:|---:|---|---:|\n'
    for name in ['W1', 'W2', 'W3']:
        z = validation['comparisons'][name]; lo, hi = z['bootstrap95']; sensitivity = validation['weighted2025_sensitivity'][name]['delta']
        note += f'| {name} | {price["scores"][name]:.6f} | {z["delta"]:+.6f} | [{lo:+.6f}; {hi:+.6f}] | {sensitivity:+.6f} |\n'
    note += (f'\nN3 = {price["scores"]["N3"]:.6f} es referencia de investigación sobre T2b, no el envío F2/C1 completo. '
        'Ninguna variante supera los criterios preinscritos. W1 tiene tres folds positivos, un intervalo compatible con cero y pasa a diferencia negativa tras retirar los 31 grupos más favorables. '
        'W2 y W3 también deterioran el sustituto A1 original de 2024 bajo la composición de 2025. No se admite ninguna variante ni se produce un CSV de test con ellas.\n\n'
        'La ponderación propuesta se calculó antes de los modelos y sin leer siniestros o precios: 18 estratos de ramo, negocio y duración, con los cortes históricos 0,5 y 0,9, '
        'y cada año ajustado a la composición conocida de 2025. Todos los estratos tienen filas, pero el ESS es solo 2.920,86 filas (2,67 % del conjunto) '
        'y 1.572,31 componentes (4,32 %), con peso máximo 73,18. Falló el umbral previo del 10 %; se conserva ese fallo. '
        'No se recortaron pesos, reagruparon bandas o admitieron retrospectivamente modelos fallidos. La ponderación se usó solo como sensibilidad adicional. '
        'La versión inicial no guardaba el detalle del fallo y una revisión de observabilidad falló al serializar un booleano NumPy; ambos códigos y errores se preservan. '
        'La tercera versión guarda el informe completo y termina con el mismo control no superado, sin ajustar precios.\n\n'
        'Los seis GLM pasaron codificación independiente, pertenencia exacta de filas/costes/años de la fuente, objetivo scikit-learn, gradiente y Hessiano por diferencias finitas. '
        'Se reprodujo la covarianza aproximada por 48 bloques región/año en cada ajuste. Varias señales climáticas son pequeñas respecto de esa incertidumbre; '
        'no se interpretan las significancias parciales como descubrimientos independientes tras búsqueda adaptativa. '
        'Las 15 reproducciones de precios fueron exactas con el optimizador bloqueado; cambiar siniestros retenidos no cambia la corrección ni los normalizadores.\n\n'
        'La primera versión se detuvo en una prueba sintética por una referencia a un helper inexistente, antes de registrar la receta o ajustar datos del concurso. '
        'Se preservó y corrigió en v2 antes del registro. Coste real de la tanda: seis GLM fuente, tres inferencias fuente T2b ahora guardadas como entradas reutilizables, '
        '180 normalizadores sin etiquetas, cero C0 nuevo, cero precios de test y cero envíos. Los controles de modelo no se vuelven a contar como ajustes.\n\n'
        'El clima de 2025 existe en los Parquet oficiales y se admitió bajo un alcance condicional nuevo. Eso no prueba disponibilidad al cotizar, '
        'no cierra el hallazgo prospectivo F05 ni demuestra utilidad predictiva. La fuente de aprendizaje siguió usando solo 2021–2024. '
        '2024 es desarrollo adaptativo, los intervalos de destino condicionan en la fuente fijada y el soporte de nuevo negocio de duración larga sigue siendo escaso. '
        'La revisión propia no constituye revisión profesional independiente ni aprobación humana.\n\n'
        'El mejor recibo público procesado continúa en 0,16519, referencia 57651126; no hay un score nuevo en este ciclo y falta 0,00481 para 0,17. '
        'B00, F2, C1, todas las alternativas y el último cupo se conservan.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '; ' + w.rel(BASE / 'estimando_cartera2025_v3/report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FASE2_TANDA7_RESULTADOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA7-RESULTADO', '--asunto',
        'Clima residual: ganancia pequeña e inestable; ponderación2025 sin soporte suficiente como principal', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 7, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'reference': 'N3', 'scores': price['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 6,
        'new_source_T2b_offset_inferences_cached': 3, 'new_C0_fits': 0, 'new_covariate_only_normalizers': 180,
        'new_test_predictions': 0, 'new_submissions': 0, 'forum': json.loads(response.stdout)}
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file() and 'state_cuts' not in p.parts}}, indent=2), encoding='utf8')
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; counter = w.read(counters)
    assert 'phase2_2024_tanda7' not in counter
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counter['cumulative_price_base_fits'] + 6,
        'phase2_2024_tanda7': {'source_GLM_fits': 6, 'new_C0_fits': 0, 'new_parent_fits': 0,
            'cached_source_offset_inferences': 3, 'covariate_only_normalizers': 180, 'synthetic_fits_separate': 2, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_price_fits': phase['new_price_fits'] + 6,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 180,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit,
        'weighted2025_preflight': {'report': w.rel(BASE / 'estimando_cartera2025_v3/report.json'),
            'report_sha256': w.sha(BASE / 'estimando_cartera2025_v3/report.json'), 'eligible_as_primary': False,
            'row_ESS': weights['row_ESS'], 'group_ESS': weights['group_ESS'], 'diagnostic_only': True},
        '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; state = w.read(state_path)
    branch = state['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_batch=summary, active_jobs=[], next_unit=next_unit, status='active', goal_achieved=False)
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'goal_status': 'active', 'batch': 7, 'phase_price_fits': phase['new_price_fits'] + 6,
        'new_C0_fits': 0, 'new_submissions': 0, 'new_test_predictions': 0, 'best_public': .16519,
        'last_known_available_slots': phase['last_quota']['num_allowed_now'], 'forum_id': summary['forum']['id']}))

if __name__ == '__main__':
    main()
