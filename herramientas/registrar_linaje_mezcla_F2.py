"""Registra una conciliación parcial de artefactos, sin declararla validación predictiva."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
OUT = R / 'privado/semana2/mision017_fase2/conciliacion_mezcla_F2_v3'
P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    report = w.read(OUT / 'report.json'); stamp = datetime.now(timezone.utc)
    assert report['new_price_fits'] == report['new_C0_fits'] == report['new_scores'] == report['new_submissions'] == 0
    exact_exposure = report['F2_published_rounded_parameter_reconstruction'][2]
    assert exact_exposure['rows_within_published_rounding_envelope'] == 209063
    assert not report['F2_exact_historical_replay_established']
    archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    note = '\n\n## Linaje local de la mezcla F2, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se cotejaron los cuatro CSV existentes, sus huellas y sus 209.063 IDs en el mismo orden. '
        'La mezcla v1 es 50 % A1fixF1b3n y 50 % prediccion_2025_mlind v1 de Claude. '
        'La diferencia máxima frente a su media aritmética es 0,000000500001 CU, compatible con seis decimales del CSV; '
        'nueve filas también se verificaron con aritmética Decimal. No se trata de la mezcla v2 con frecuencia/severidad.\n\n'
        'El nivel global guardado, 1,187658238648521, reproduce el total anterior a F2: 81.943.158,72 CU. '
        'Después de NCB, siniestros previos, forma y razones de nivel por celda, la reconstrucción con efectos publicados redondeados es aproximada. '
        'El primer control falló por asumir que la exposición recibida o redondeada a cuatro decimales reproducía el denominador original. '
        'Se conserva el código y el fallo, sin declarar ese control superado. La lectura del productor original etiquetas.py muestra días inclusivos/365 a precisión completa. '
        'Con esa definición las 209.063 filas quedan dentro del margen de redondeo publicado, con error relativo máximo de 0,00011953. '
        'El total reconstruido es 80.680.313,03 CU frente a 80.678.630,85 CU de F2. Esa diferencia y los parámetros redondeados impiden llamarlo replay exacto. '
        'No se cambia la exposición canónica de las pruebas nuevas ni los CSV existentes.\n\n'
        'El Parquet local predicciones_2024 contiene A1 original, A2, A3 y R0. No contiene A1fixF1b3n. '
        'No se hallaron las relatividades compuestas corregidas ni los archivos de pesos con los nombres del productor en las carpetas revisadas del proyecto. '
        'Eso describe la disponibilidad local, sin afirmar ausencia en entornos históricos ajenos. Faltan los efectos sin redondear de F2 y las entradas/relatividades históricas '
        'o los pesos de A1 corregido, con su matriz y procedencia, para acreditar el flujo histórico completo.\n\n'
        'Las cinco tandas recientes contrastaron ingredientes frente a T2b/N3, no el envío F2 completo. '
        'La tanda 5, incluida la prima residual, quedó registrada como adversa. Esta conciliación no añade un resultado predictivo ni convierte sus candidatos en mejoras de F2. '
        'No hubo ajuste, nueva inferencia de modelos, recalibración, score, CSV candidato o envío. B00, F2, las versiones fallidas y la autoría de Claude se conservan. '
        '2024 está abierto por autorización directa y se trata como desarrollo adaptativo.\n\n'
        'Siguiente trabajo: preparar una calibración GLM sencilla de la pendiente de riesgo, con efectos por tipo de negocio y regularización, sobre los ámbitos de 2023–2024 ya guardados. '
        'Debe distinguirse de las curvas de forma anteriores con niveles óptimos calculados en el año evaluado. '
        'Antes de ajustar se reconstruirán los precios de entrenamiento de cada ámbito con los objetos C0 y de credibilidad existentes; '
        'se fijarán código, comparador, criterio y coste y se registrará en el foro. La carencia de A1 limita qué comparaciones se pueden certificar, '
        'pero no vuelve a bloquear 2024 ni la investigación autorizada.\n\n'
        'Evidencia: ' + w.rel(OUT / 'report.json') + '. La misión 0,17 sigue activa; no hay recibo nuevo que la dé por alcanzada.\n')
    doc = R / 'docs/semana2/MISION017_FASE2_MEZCLA_F2_LINAJE.md'; assert not doc.exists()
    doc.write_text(note, encoding='utf8'); body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    forum = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-MEZCLA-F2-LINAJE', '--asunto',
        'Mezcla de F2 conciliada; reproducción histórica exacta de A1 aún no acreditada', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'partial_lineage_established_no_new_predictive_result',
        'report': w.rel(OUT / 'report.json'), 'report_sha256': w.sha(OUT / 'report.json'),
        'mixture_CSV_arithmetic_verified': True, 'F2_unrounded_historical_replay_verified': False,
        'source_component_author': 'Claude', 'new_fits': 0, 'new_scores': 0, 'new_submissions': 0,
        'forum': json.loads(forum.stdout)}
    (OUT / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    next_unit = ('Preparar la calibración GLM de pendiente global/por negocio en 2023–2024 con regularización y C0/credibilidad por ámbito ya congelados. '
        'Primero reconstruir sus precios de entrenamiento sin reestimar los objetos y demostrar que el retenido no entra en el aprendizaje. '
        'La forma se aprenderá en entrenamiento, con interceptos nuisance y conservación de totales en la cartera evaluada, sin nivel óptimo retenido. '
        'No ajustar ni puntuar hasta fijar receta/código/criterio/coste y comentario previo. '
        'Contrastar con la investigación T2b/N3 y declarar por separado la evidencia que falta para el F2 completo; no presentar los cinco experimentos como una comparación íntegra frente a F2. '
        '2024 abierto como desarrollo, misión activa, B00/F2 y alternativas conservados, sin gasto automático de cupos.')
    w.update(P, {'utc': stamp.isoformat(), 'F2_full_mix_lineage': receipt, 'next_unit': next_unit,
        'active_jobs': [], 'active_execution': None, 'status': 'active', '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; state = w.read(state_path)
    branch = state['week_2_mission017_phase2_20261025'].copy()
    branch.update(F2_full_mix_lineage=receipt, next_unit=next_unit, active_jobs=[], status='active', **{'2024_open': True, '2024_closed': False})
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'status': 'active', 'partial_F2_lineage_recorded': True,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0, 'forum_id': receipt['forum']['id']}))

if __name__ == '__main__':
    main()
