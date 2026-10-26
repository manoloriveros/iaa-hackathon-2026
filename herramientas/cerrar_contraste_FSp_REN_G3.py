"""Conserva el contraste y el fallo técnico previo, sin admitir otro envío."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'FSp_REN_G3_contraste_20261026_v2'
spec = importlib.util.spec_from_file_location('writer_close_RFS1', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    assert not (OUT / 'completion_receipt.json').exists()
    a = w.read(OUT / 'report.json'); assert len(a['numeric_controls']) == 15 and a['all_NB_exact']
    assert a['reused_v1_calibration_constants'] == 11 and a['new_v2_calibration_constants'] == 154
    assert not a['all_criteria_pass']
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    # Exact archival names identified from evaluar_final.py, not another search
    # for the already inventoried FSp/K files. No model inference or labels read.
    args = ['rg', '--files', '--hidden', '--no-ignore', '-g', 'gbm_dev212223*_v2*f1*.txt',
            '-g', 'lg_dev212223*_v2*f1*_em.parquet', '-g', '!**/.git/**', '-g', '!**/.venv/**',
            '-g', '!**/.venv-kaggle/**', '-g', '!**/node_modules/**', '-g', '!**/.cache/**', 'Hackaton', 'Preparación']
    found = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf8')
    assert found.returncode in [0, 1] and not found.stderr
    inventory = {'author': 'Codex', 'utc': stamp.isoformat(), 'command_argv': args, 'returncode': found.returncode,
                 'matches': found.stdout.splitlines(), 'roots': ['Hackaton', 'Preparación'],
                 'original_producer_saves_models': True,
                 'producer_code': w.rel(ROOT / 'Hackaton/Semana 2/Claude/validacion_nocturna_20261023/codigo/desarrollado_gbm.py'),
                 'not_global_absence_claim': True, 'new_fits': 0, 'new_inferences': 0, 'new_scores': 0}
    (OUT / 'A1_corrected_exact_tag_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf8')
    next_unit = ('RFS1 está completo:15ámbitos,165momentos únicos (11reutilizados de v1 y154nuevos en v2),sin nuevos árboles/C0. '
        'No repetirlo, retocar K/pesos o ocultar el fallo post31. '
        'Siguiente incertidumbre concreta: alinear el flujo de despliegue con la fuente2021–2024 disponible para ambos años objetivo. '
        'G3/T2b usa el padre fuente2021–2024 en2023/24, mientras el primer FSp usó dev2021–2023 en2023; '
        'la producción2025 necesita prod2021–2024. Registrar antes un control de consistencia usando únicamente las salidas prod ya guardadas, '
        'sin nuevos modelos, conservando todos los demás parámetros y criterios. No elegir la ventana por el mejor score ni reescribir RFS1. '
        'Además, sigue faltando el comparador F3c/F2 completo: el A1 corregido de tres semillas no tiene archivos históricos/modelos con los tags '
        'exactos en la búsqueda registrada (el código original sí los guardaba). No repetir ese inventario; revisar el contrato/offset/matrices y '
        'metadatos de rondas de ese productor antes de proponer una reconstrucción, no usar el A1 original2024como si fuera el corregido. '
        'No hay CSV nuevo listo o aprobado para enviar. Cuota0conservada,2024abierto,B00/alternativas preservados,meta0.17activa.')
    note = '\n\n## FSp aislado sobre G3: señal favorable, concentración pendiente, 26 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se completó el contraste único registrado de FSp en renovación: pesos motor/edificios de 0,25 y contenidos de 0,5, '
        'con los factores residuales G3 guardados, sin reestimarlos. Se mantuvieron exactamente nuevo negocio y los totales por año/ramo. '
        'Se usó la calibración recibida kf/ks/kg con contracción n/(n+100), adaptada expresamente al C0 protegido por grupos. '
        'No es el F4c/K original ni la igualación de coste sin contracción de la prueba anterior de edificios.\n\n')
    note += '| Medida | Resultado |\n|---|---:|\n'
    note += f'| D² G3 | {a["scores"]["G3"]:.8f} |\n| D² RFS1 | {a["scores"]["RFS1"]:.8f} |\n| Diferencia | {a["delta_vs_G3"]:+.8f} |\n'
    note += f'| IC 95 % por componentes | [{a["bootstrap95"][0]:+.8f}; {a["bootstrap95"][1]:+.8f}] |\n'
    note += f'| Aporte global de 2023 | {a["year_contributions"]["2023"]:+.8f} |\n| Aporte global de 2024 | {a["year_contributions"]["2024"]:+.8f} |\n'
    note += f'| Sin los 31 grupos más favorables, mismo denominador | {a["post31_favorable_groups_delta"]:+.8f} |\n'
    note += f'| Sin los 31 grupos de mayor coste observado | {a["remove31highest_cost_groups_delta"]:+.8f} |\n'
    note += ('\nLos cinco folds son positivos y ambos años ganan. El intervalo condicionado a los modelos fuente también es positivo. '
        'Aun así, la diferencia no llega al mínimo global de +0,002 y no resiste retirar los 31 grupos más favorables. '
        'Retirar los grupos de mayor coste observado mantiene una ganancia: esa comprobación distinta no sustituye el fallo de influencia. '
        'No se relaja el criterio ni se admite un envío por la media favorable.\n\n')
    note += '| Ramo, solo renovación | Aporte 2023 al D² global | Aporte 2024 al D² global |\n|---|---:|---:|\n'
    for line in ['motor', 'buildings', 'contents']:
        cells = {x['year']: x['delta_global'] for x in a['cells'] if x['line'] == line and x['NB'] == 0}
        note += f'| {line} | {cells[2023]:+.8f} | {cells[2024]:+.8f} |\n'
    note += ('\nMotor y contenidos ganan en ambos años. Edificios mejora en 2023 y pierde ligeramente en 2024 con esta receta; '
        'los modelos, variantes y fallos quedan conservados. La separación del componente frente a G3 es ahora numérica y no una atribución '
        'a partir de CSV compuestos con factores reestimados. G3 sigue siendo un sustituto: el comparador F3c/F2 completo y sus vetos no están '
        'reproducidos íntegramente. No se asigna al público de F3c la mejora local de este contraste.\n\n'
        'El primer intento falló antes de puntuar por un valor de control -1e30 que no cabe en int64. Se guardó el fallo, '
        'se cambió solo el payload adverso a un entero negativo válido y se preinscribió v2 antes de continuar. '
        'Las funciones matemáticas learn/apply/G3 conservaron su AST y los parámetros, criterios y bootstrap fueron idénticos. '
        'Se reutilizaron los 11 momentos de motor/fold0 ya guardados, sin estimarlos otra vez; los otros 154 se calcularon una sola vez. '
        'El control adverso recomputa esos mismos 165 momentos por separado y no añade parámetros distintos.\n\n'
        'Pasaron los 15 controles del flujo real: costes, recuentos y reservas retenidos alterados sin efecto; reproducción exacta de los artefactos '
        'guardados sin aprender; identidad de peso cero; orden de claves; suma independiente de momentos y aritmética por otra fórmula. '
        'La pérdida coincide con scikit-learn. El bootstrap por componentes usa 2.000 réplicas y recalcula el nulo por fórmula cerrada en cada réplica; '
        'la incertidumbre fuente queda condicionada a sus modelos fijos. Estas verificaciones no eliminan la concentración ni acreditan prospectividad.\n\n'
        'Coste: 15 niveles globales de coste, 75 momentos de frecuencia y 75 de marca; 75 factores contraídos derivados que no se cuentan otra vez como ajustes. '
        'Hay 30 normalizadores sin etiquetas, cero modelos/C0 nuevos, precios de2025 o envíos. Los 36 ajustes MC y los 24 de edificios ya estaban contabilizados. '
        '2024 es desarrollo adaptativo y se mantienen los límites de maestros sin fecha, completitud de coste, cola y reservas. '
        'El mejor recibo sigue en 0,16914, sin alcanzar 0,17; B00, F2/C1/F3c y todas las alternativas permanecen.\n\n'
        'Queda una diferencia concreta del flujo a resolver antes de preparar la producción: la referencia T2b/G3 usa fuente 2021–2024 para ambos años, '
        'mientras FSp usó 2021–2023 al evaluar 2023 en este contraste. La predicción 2025 usará fuente 2021–2024. '
        'Ese control de consistencia debe registrarse por adelantado y no convertirse en una elección de ventana por score. '
        'También se registró la búsqueda por tags exactos del A1 corregido de tres semillas: no aparecieron sus modelos o relatividades históricas '
        'en las raíces indicadas, aunque el productor original sí los guardaba. No se presenta el A1 original de2024 como su sustituto corregido.\n\n'
        'Evidencia: ' + w.rel(OUT / 'report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/semana2/MISION017_FSp_REN_G3_CONTRASTE.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-REN-G3-CONTRASTE-RESULTADO',
        '--asunto', 'FSp aislado gana en cinco folds; no supera mínimo e influencia', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'positive_partial_signal_no_admission',
               'report': w.rel(OUT / 'report.json'), 'report_sha256': w.sha(OUT / 'report.json'), 'document': w.rel(doc),
               'scores': a['scores'], 'delta': a['delta_vs_G3'], 'bootstrap95': a['bootstrap95'], 'criteria': a['criteria'],
               'empirical_constants': 165, 'reused_v1_constants': 11, 'new_v2_constants': 154,
               'derived_peril_factors_not_added_to_fit_count': 75, 'new_price_model_fits': 0, 'new_C0_fits': 0,
               'new_test_prices': 0, 'new_submissions': 0, 'goal_achieved': False, '2024_open': True,
               'next_unit': next_unit, 'forum': json.loads(response.stdout)}
    counter = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counter)
    assert 'phase2_FSp_REN_G3_contrast' not in c
    w.update(counter, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': c['cumulative_closed_form_constants'] + 165,
                       'phase2_FSp_REN_G3_contrast': {**receipt, 'moment_decomposition': {'global_cost': 15, 'frequency': 75, 'mark': 75}}}, archive)
    phasepath = R / 'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phasepath)
    assert phase['new_price_fits'] == 167 and phase['new_submissions'] == 2
    w.update(phasepath, {'utc': stamp.isoformat(), 'FSp_REN_G3_contrast': receipt, 'active_execution': None,
                         'new_FSp_calibration_moments': phase.get('new_FSp_calibration_moments', 0) + 165,
                         'new_FSp_derived_peril_factors': phase.get('new_FSp_derived_peril_factors', 0) + 75,
                         'next_unit': next_unit}, archive)
    statepath = ROOT / 'Preparación/ESTADO_PROYECTO.json'; own = w.read(statepath)['week_2_mission017_phase2_20261025']
    own.update(FSp_REN_G3_contrast=receipt, active_jobs=[], next_unit=next_unit)
    w.update(statepath, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(R / 'registro/semana2_mision017_renovaciones_FSp_actual.json', {'utc': stamp.isoformat(),
        'status': 'isolated_FSp_partial_positive_deployment_consistency_pending', 'isolated_FSp_G3_contrast': receipt, 'next_unit': next_unit}, archive)
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / filename, note, archive)
    w.append(R / 'docs/semana2/MISION017_RENOVACIONES_Y_RECUPERACION_FSp.md', note, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_FSp_REN_G3_report': w.rel(doc)}, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'delta': a['delta_vs_G3'], 'new_C0_fits': 0,
                      'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
