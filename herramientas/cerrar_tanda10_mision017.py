"""Conserva las mejoras parciales y sus controles adversos sin admitir un envío."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer10', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda10_factores_20261026_v1'; P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    v = w.read(OUT / 'validation_v1/report.json'); price = w.read(OUT / 'price_report.json'); phase = w.read(P)
    assert len(v['closed_form_mathematics']) == 20 and len(v['replays']) == 10 and price['factor_parameters'] == 90
    assert not any(z['all_exploratory_checks_pass'] for z in v['comparisons'].values())
    assert phase['current_batch']['batch'] == 9 and phase['new_price_fits'] == 87
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = ('Preparar y preinscribir GLM Tweedie1.5 conjunto de efectos principales para las mismas variables residuales, '
        'sin cambiar K300, grupos, años, C0, N3 o exposición. La necesidad concreta es contrastar el pase secuencial heurístico '
        'con un objetivo penalizado conjunto que trate la dependencia entre género, teletrabajo, segmento y los niveles nuisance. '
        'No ajustar K, relajar los criterios, reagrupar categorías o elegir covariables por el fold que pierde. '
        'Usar penalización equivalente a300positivos mediante información Fisher del baseline de entrenamiento; fijar fórmula, '
        'codificación simétrica, interceptos por año/negocio no transferidos, configuración del solver, presupuesto y comparación '
        'contra N3 y la etapa secuencial correspondiente antes de cualquier fit/score y del comentario previo. '
        'Reutilizar los diez ámbitos y covariables de esta tanda. Verificar matemáticamente el objetivo y todo el flujo con datos sintéticos. '
        'Conservar los resultados parciales G1-G3, B00/F2/C1 y alternativas;2024 abierto como desarrollo. '
        'Sin CSV2025 ni uso del cupo por esta ganancia todavía insuficiente/inestable. Meta0.17 activa, público comprobado0.16519.')
    note = '\n\n## Factores residuales por componentes: tanda 10, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se probaron los factores simples recibidos como hipótesis de F3c, con implementación y ámbito propios: '
        'género en autos/contenidos (G1), añadir teletrabajo en contenidos (G2) y añadir segmento en contenidos (G3). '
        'Cada etapa aprende solo en los componentes exteriores de entrenamiento y reutiliza su C0/N3 guardado. '
        'Los niveles de año/negocio son nuisance de entrenamiento y no se transfieren. Las predicciones conservan los totales de N3 por año/negocio sin etiquetas. '
        'Edificios permanece igual y no se adopta la razón de nivel del F3c recibido.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Sensibilidad a composición2025 |\n|---|---:|---:|---|---:|\n'
    for name in ['G1', 'G2', 'G3']:
        z = v['comparisons'][name]; lo, hi = z['bootstrap95']
        note += f'| {name} | {price["scores"][name]:.6f} | {z["delta"]:+.6f} | [{lo:+.6f}; {hi:+.6f}] | {v["weighted2025_sensitivity"][name]["delta"]:+.6f} |\n'
    note += ('\nN3=0,135250 es referencia de investigación, no el C1/F2 completo. '
        'G3 gana en ambos años (+0,001651 en2023 y +0,002068 en2024), su intervalo simultáneo entre las tres variantes queda sobre cero '
        'y conserva una diferencia apenas positiva al retirar los31grupos más favorables (+0,000016). '
        'Los seis segmentos ramo/negocio no pierden en G3. Es evidencia útil, pero no supera todos los criterios: '
        'falta el mínimo total de+0,002 y solo tres de cinco folds son positivos. '
        'Además, en el sustituto A1 original2024 la diferencia ponderada es ligeramente negativa (−0,000097). '
        'Las etapas menores también fallan influencia y sus intervalos simultáneos incluyen cero. '
        'No se admite otro envío ni se cambian los criterios a posteriori.\n\n'
        'La ponderación hacia2025 es positiva, pero sus intervalos siguen incluyendo cero y el fallo previo de ESS no ha desaparecido. '
        'Se mantiene como sensibilidad/veto, nunca como rescate del control principal. '
        'El signo de género y teletrabajo se conserva en los cinco ajustes, sin que eso certifique transporte a nuevo negocio o disponibilidad prospectiva. '
        'Los maestros están sin fecha; teletrabajo no cambia dentro del cliente en estos datos, pero esa estabilidad no prueba su fecha de conocimiento. '
        'La selección inicial de variables fue adaptativa y la evidencia recibida de otras IA no constituye revisión profesional independiente.\n\n'
        'Las20etapas y90factores pasaron el cálculo independiente de momentos suficientes, derivadas del óptimo Tweedie, '
        'comparación con la pérdida scikit-learn y fórmula de contracción. Se cotejaron los80niveles nuisance. '
        'Los10replays de ámbitos fueron exactos con el aprendizaje bloqueado, la alteración de costes/reservas retenidos no cambia la aplicación '
        'y C0 excluye sus grupos. El flujo sintético completo ya confirmó que modificar el retenido no cambia el aprendizaje. '
        'Se guardaron parámetros por fold y variación; no se repitieron permutaciones I/J/K o entrenamientos FSp.\n\n'
        'Coste real:20estimaciones cerradas de etapas,90factores y80niveles nuisance;80normalizadores de entrenamiento y80de evaluación, todos sin etiquetas para normalizar. '
        'Cero modelos de precio iterativos, curvas C0, inferencias fuente, precios de test o envíos nuevos. '
        'Los factores y niveles se cuentan separados de los GLM/árboles, como en las tandas cerradas anteriores. '
        'B00, F2, C1 y alternativas se conservan.2024 sigue abierto como desarrollo adaptativo. '
        'El mejor recibo público procesado continúa en0,16519 y la meta0,17 sigue activa.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FASE2_TANDA10_RESULTADOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA10-RESULTADO', '--asunto',
        'Factores residuales: mejora en ambos años, tres folds positivos y sin admisión de envío', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 10, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'scores': price['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 0,
        'closed_form_stage_calls': 20, 'factor_parameters': 90, 'nuisance_levels': 80, 'prediction_only_normalizers': 160,
        'new_C0_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0, 'forum': json.loads(response.stdout)}
    counters = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counters); assert 'phase2_2024_tanda10' not in c
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': c['cumulative_closed_form_constants'] + 80,
        'phase2_2024_tanda10': {'closed_stage_learning_calls': 20, 'factor_parameters': 90, 'training_nuisance_levels': 80,
            'prediction_only_normalizers': 160, 'new_iterative_price_fits': 0, 'new_C0_fits': 0, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_closed_form_levels': phase['new_closed_form_levels'] + 80,
        'new_bucket_factors': phase['new_bucket_factors'] + 90,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 160,
        'new_closed_form_factor_learning_calls': phase.get('new_closed_form_factor_learning_calls', 0) + 20,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit, '2024_open': True, '2024_closed': False, 'goal_achieved': False,
        'previous_goal_turn_audit': {'classification': 'progress', 'evidence': 'T8/T9 completed,27real new model attempts and independent validation; F3c/F4c evidence received and next scope changed with authoritative records.'}}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; branch = w.read(state_path)['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_batch=summary, next_unit=next_unit, active_jobs=[], status='active', goal_achieved=False)
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_residual_factor_report': w.rel(doc)}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'batch': 10, 'goal_status': 'active', 'G3_delta': v['comparisons']['G3']['delta'],
        'new_iterative_price_fits': 0, 'new_C0_fits': 0, 'new_submissions': 0, 'forum_id': summary['forum']['id']}))

if __name__ == '__main__': main()
