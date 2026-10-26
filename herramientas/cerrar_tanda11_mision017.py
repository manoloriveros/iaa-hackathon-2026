"""Cierra el contraste conjunto: el pase secuencial no explica la inestabilidad."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer11', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda11_conjunto_20261026_v1'; P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    v = w.read(OUT / 'validation_v1/report.json'); price = w.read(OUT / 'price_report.json'); phase = w.read(P)
    assert len(v['joint_GLM_mathematics']) == 20 and len(v['replays']) == 10 and price['new_joint_GLM_fits'] == 20
    assert not any(z['all_exploratory_checks_pass'] for z in v['comparisons'].values())
    assert phase['current_batch']['batch'] == 10 and phase['new_price_fits'] == 87
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = ('No repetir el contraste secuencial/conjunto o retocar K/umbrales por sus resultados: la diferencia es mínima y no resuelve los folds adversos. '
        'Conciliar ahora mediante lectura la cuota y los recibos públicos propios actuales, sin leer private_score o enviar nada, '
        'para comprobar posibles cambios y evitar duplicados antes de decidir el siguiente experimento de entrega. '
        'Revisar de forma concreta el expediente de F3c recibido y su regla de aplicación sobre el C1 medido; separar evidencia estable de frecuencia, '
        'mejora media por ambos años y efecto marginal de cada paso de los controles que fallaron. '
        'Cualquier excepción para un envío de investigación debe quedar explícita y justificada, con receta/CSV, coste, trazabilidad y límites revisados; '
        'no equivale a promoción formal ni a declarar superados los criterios, y la propuesta de otra IA no es una autorización humana nueva. '
        'La autorización directa vigente del participante permite continuar y decidir sin nuevas preguntas, pero conserva el cuidado de los cupos, '
        'la consistencia y la robustez. No ejecutar colas antiguas o cambiar autorizaciones ajenas. '
        'Si no hay un candidato suficientemente respaldado, seguir con una necesidad material distinta documentada, no con reajustes pequeños sobre las mismas fuentes. '
        '2024 sigue abierto como desarrollo, B00/F2/C1 y alternativas permanecen. Meta0.17 activa, último recibo comprobado0.16519.')
    note = '\n\n## GLM conjunto de factores residuales: tanda 11, 26 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se completaron20GLM Tweedie sencillos con los mismos efectos principales de la tanda10. '
        'La contracción conserva K300 mediante precisión Fisher de entrenamiento; se estiman conjuntamente las categorías y '
        'los cuatro interceptos año/negocio, estos últimos sin transferir. Se mantuvieron grupos, años, C0/N3, exposición y categorías. '
        'No se eligió una penalización nueva ni se añadieron interacciones para corregir los folds que perdían.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | Diferencia frente a su etapa G | IC 95 % por componentes frente a N3 |\n|---|---:|---:|---:|---|\n'
    for name in ['J1', 'J2', 'J3']:
        z = v['comparisons'][name]; lo, hi = z['bootstrap95']
        note += f'| {name} | {price["scores"][name]:.6f} | {z["delta"]:+.6f} | {v["matched_sequential_delta"][name]:+.8f} | [{lo:+.6f}; {hi:+.6f}] |\n'
    note += ('\nEl ajuste conjunto produce prácticamente lo mismo que el pase secuencial. J3 gana+0,001849 frente a N3, '
        'pero queda−0,000001 frente a G3. Sigue por debajo de+0,002, solo tres folds son positivos y la diferencia tras retirar '
        'los31grupos favorables queda apenas negativa (−0,000011). El sustituto A1 original2024 también queda ligeramente negativo bajo '
        'la ponderación diagnóstica (−0,000145). J1/J2 tampoco pasan todos los controles. No se presenta la casi igualdad como una nueva mejora.\n\n'
        'La ganancia media de los factores se mantiene en ambos años y el intervalo simultáneo de J3 frente a N3 es positivo, '
        'pero eso no elimina la fragilidad por folds/influencia ni acredita mejora del C1/F2 completo. '
        'La sensibilidad hacia2025 es positiva y ancha, con intervalos compatibles con cero y el mismo fallo previo de ESS. '
        'No se admite otro CSV ni se gasta un envío por estas tandas. Las alternativas G/J quedan conservadas.\n\n'
        'Los20objetivos pasaron una codificación independiente de categorías completas, cálculo de la pérdida scikit-learn, '
        'gradientes y Hessianos por diferencias finitas. Todos los Hessianos penalizados son definidos positivos. '
        'Las10reproducciones por ámbito fueron exactas, con el optimizador bloqueado, C0 excluyendo al retenido y aplicación '
        'invariante a costes/reservas retenidos. El flujo sintético de aprendizaje también pasó la alteración del retenido y '
        'las identidades neutral/desconocida. La advertencia de pandas sobre futuras versiones ante categorías desconocidas apareció '
        'en esa prueba intencional y no invalida la identidad comprobada en el entorno actual; no se cambió la librería.\n\n'
        'Coste:20GLM reales (cinco de motor compartidos entre variantes),80normalizadores sin etiquetas, '
        'cero C0, modelos fuente, precios de test o envíos. Tres ajustes sintéticos se cuentan aparte. '
        'Quedan107ajustes iterativos nuevos en esta fase; las90estimaciones cerradas de factores y80niveles de la tanda10 se conservan en sus contadores separados. '
        'Los resultados son exploratorios tras búsqueda adaptativa; no revisión profesional independiente. '
        '2024 sigue abierto por instrucción humana y se mantiene como desarrollo. B00, F2, C1 y todas las versiones siguen guardadas. '
        'El mejor público comprobado continúa en0,16519:0,17 aún no está demostrado.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/semana2/MISION017_FASE2_TANDA11_RESULTADOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FASE2-TANDA11-RESULTADO', '--asunto',
        'GLM conjunto casi igual al secuencial; no resuelve folds e influencia', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 11, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'scores': price['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 20,
        'new_C0_fits': 0, 'prediction_only_normalizers': 80, 'new_test_predictions': 0, 'new_submissions': 0,
        'forum': json.loads(response.stdout)}
    counters = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counters); assert 'phase2_2024_tanda11' not in c
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': c['cumulative_price_base_fits'] + 20,
        'phase2_2024_tanda11': {'joint_GLM_fits': 20, 'new_C0_fits': 0, 'prediction_only_normalizers': 80,
            'synthetic_fits_separate': 3, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_price_fits': phase['new_price_fits'] + 20,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 80,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit,
        '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; branch = w.read(state_path)['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_batch=summary, next_unit=next_unit, active_jobs=[], status='active', goal_achieved=False,
        new_price_fits=phase['new_price_fits'] + 20)
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_joint_factor_report': w.rel(doc)}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'batch': 11, 'goal_status': 'active', 'phase_price_fits': phase['new_price_fits'] + 20,
        'new_submissions': 0, 'forum_id': summary['forum']['id']}))

if __name__ == '__main__': main()
