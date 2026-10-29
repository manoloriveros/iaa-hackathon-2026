"""Conserva el adverso de adaptación de hojas y prioriza evidencia nueva del equipo."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer9', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda9_hojas_20261026_v3'; P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    validation = w.read(OUT / 'validation_v1/report.json'); price = w.read(OUT / 'price_report.json')
    assert len(validation['replays']) == len(validation['source_and_refit_mathematics']) == 15
    assert not any(x['all_exploratory_checks_pass'] for x in validation['comparisons'].values())
    assert price['new_leaf_refit_calls'] == 15 and price['new_C0_fits'] == 0
    phase = w.read(P); assert phase['new_price_fits'] == 72 and phase['new_submissions'] == 1
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = ('Revisar los aportes locales exp26 de Claude recién identificados: exp26_v2.tar.gz y exp26_codigo_y_evidencia.tar.gz, '
        'F3c_2025.csv y F4c_2025.csv, que usan el C1 procesado como base. Son nuevas fuentes de evidencia para esta revisión, '
        'no nuevos datos oficiales ni órdenes humanas. Conservar y cotejar sus SHA, código, parámetros, fechas/ámbito de aprendizaje, '
        'comparadores y resultados adversos recibidos; no atribuir a Codex la receta ni repetir reentrenamientos/suites ya documentados. '
        'Priorizar el aporte marginal de los factores simples (género en autos/contenidos, teletrabajo/segmento en contenidos) '
        'frente a la mezcla FSp y a los cambios de nivel. No sumar la ganancia de factores a la de FSp dos veces. '
        'La auditoría recibida ya advierte signos inestables de FSp en nuevo negocio y cp2025=0 en ciertos Parquet; '
        'no reutilizarlos como último sin explicitar el vínculo correcto. '
        'Antes de nuevos fit/score propios o de un envío, registrar el alcance y la necesidad material, revisar el flujo real, '
        'la exclusión por grupo/año y las diferencias respecto de C1. Las banderas/recomendaciones de otras IA no autorizan mensajes, remotos o selección final. '
        '2024 abierto como desarrollo; B00, C1/F2, alternativas y el último cupo conservados. Meta0.17 activa, mejor recibo0.16519.')
    note = '\n\n## Adaptación de hojas con estructura fija: tanda 9, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se adaptaron las hojas de T2b con LightGBM4.6.0.refit y decay0,9: cada actualización conserva el 90 % del valor anterior. '
        'Se mantuvieron las variables, categorías, umbrales, número de árboles y topología de la fuente de Claude. '
        'El objetivo es Tweedie1,5 sobre T0 del periodo. El offset log(N3 del ámbito)-raw del padre reutiliza C0 y calibraciones '
        'guardados del entrenamiento exterior. No se aprendieron nuevas divisiones con los siniestros emergentes.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Diferencia con ponderación2025, solo sensibilidad |\n|---|---:|---:|---|---:|\n'
    for name in ['L1', 'L2', 'L3']:
        z = validation['comparisons'][name]; lo, hi = z['bootstrap95']; sensitivity = validation['weighted2025_sensitivity'][name]['delta']
        note += f'| {name} | {price["scores"][name]:.6f} | {z["delta"]:+.6f} | [{lo:+.6f}; {hi:+.6f}] | {sensitivity:+.6f} |\n'
    note += (f'\nN3 = {price["scores"]["N3"]:.6f} es referencia de investigación; no reproduce C1/F2 completo. '
        'L1 aplica todo el cambio de hojas, L2 la mitad y L3 la cuarta parte, sin otros ajustes. '
        'Ninguna pasa los criterios previos. Las tres tienen intervalos compatibles con cero, solo tres folds positivos, '
        'signos opuestos entre años y diferencias negativas tras retirar los 31 grupos más favorables. '
        'L3 queda prácticamente igual a la referencia; no se interpreta su +0,000005 como una mejora. '
        'La sensibilidad ponderada hacia2025 también es negativa. El fallo previo de ESS continúa, sin recortar pesos o cambiar bandas.\n\n'
        'Aplicar el mismo cambio al A1 original2024 mejora ese sustituto: L1 da +0,003735 bajo esos pesos diagnósticos. '
        'Ese contraste no es un replay del A1 corregido o de C1 completo y no basta para inferir una mejora del envío. '
        'La validación sigue siendo desarrollo adaptativo tras búsqueda; no una confirmación independiente ni aprobación humana.\n\n'
        'Los quince ajustes se reprodujeron por otro cálculo, sin entrenar: gradientes y Hessianos Tweedie secuenciales, '
        'sumas por hoja, penalización y combinación con el valor fuente según el código público de LightGBM4.6.0. '
        'Se comprobó la representación float32 de etiquetas y gradientes del motor. Las quince reproducciones de precios y '
        'normalizadores fueron exactas; un segundo cálculo algebraico coincidió y cambiar costes/reservas retenidos no altera la aplicación. '
        'Los grupos de aprendizaje y retenidos son disjuntos. Las pruebas sintéticas del flujo de aprendizaje también comprobaron '
        'invariancia al retenido, respuesta al cambio del entrenamiento e identidad con decay1.\n\n'
        'Se conservan dos fallos previos, ambos con cero ajustes reales. v1 detectó que usar dot en el normalizador introducía '
        'un redondeo mínimo en la identidad; v2 cambió a la misma suma usada en el denominador. '
        'El flujo v2 se detuvo antes del primer refit porque OOF y las variables tenían distinto orden. '
        'v3 alinea por row_id con unión uno a uno y comprobó N3 retenido exacto en los15ámbitos. '
        'Reutilizó las pruebas sintéticas y predicciones del padre sin repetirlas. La receta y cada reanudación quedaron registradas antes del ajuste real.\n\n'
        'La advertencia de LightGBM sobre categorical_feature dentro de params no cambió la matriz: se pasó el DataFrame con las '
        'categorías originales por columna. Las categorías, topología y reproducción matemática se cotejaron en cada modelo. '
        'Coste real:15refit de hojas, cero modelos fuente, curvas C0, divisiones nuevas, precios de test o envíos;180normalizadores sin etiquetas. '
        'Hubo10ajustes sintéticos separados entre v1 y v2, no entrenamiento del concurso.\n\n'
        'E25/E26 de severidad y mezclas ya estaban terminados; se revisaron como evidencia y no se repitieron. '
        'La consulta pública no devolvió una discusión nueva en la página recibida; la respuesta vacía de notebooks no prueba ausencia universal. '
        'El mejor recibo procesado sigue en0,16519 (57651126), a0,00481 de0,17. B00, F2, C1 y alternativas se conservan;2024 sigue abierto.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '. '
        'Método: [Booster.refit](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html#lightgbm.Booster.refit), '
        '[GBDT v4.6.0](https://github.com/microsoft/LightGBM/blob/v4.6.0/src/boosting/gbdt.cpp), '
        '[hojas v4.6.0](https://github.com/microsoft/LightGBM/blob/v4.6.0/src/treelearner/serial_tree_learner.cpp).\n\n'
        'Siguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FASE2_TANDA9_RESULTADOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA9-RESULTADO', '--asunto',
        'Hojas de estructura fija: sin ganancia robusta; se revisarán los aportes F3c/F4c recibidos', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 9, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'reference': 'N3', 'scores': price['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 15,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_splits': 0, 'new_covariate_only_normalizers': 180,
        'new_test_prices': 0, 'new_submissions': 0, 'forum': json.loads(response.stdout)}
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file() and 'state_cuts' not in p.parts}}, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; counter = w.read(counters)
    assert 'phase2_2024_tanda9' not in counter
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counter['cumulative_price_base_fits'] + 15,
        'phase2_2024_tanda9': {'leaf_refit_calls': 15, 'new_source_fits': 0, 'new_C0_fits': 0,
            'covariate_only_normalizers': 180, 'synthetic_fits_separate': 10, 'v1_v2_real_fits': 0, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_price_fits': phase['new_price_fits'] + 15,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 180,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit,
        '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; branch = w.read(state_path)['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_batch=summary, active_jobs=[], next_unit=next_unit, status='active', goal_achieved=False,
        new_price_fits=phase['new_price_fits'] + 15, **{'2024_open': True, '2024_closed': False})
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_leaf_refit_report': w.rel(doc)}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'goal_status': 'active', 'batch': 9, 'phase_price_fits': phase['new_price_fits'] + 15,
        'new_C0_fits': 0, 'new_submissions': 0, 'best_public': .16519, 'forum_id': summary['forum']['id']}))

if __name__ == '__main__': main()
