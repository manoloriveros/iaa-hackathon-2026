"""Cierra la consistencia prod y el prototipo; mantiene F3c como entrega vigente."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'; BASE = R / 'privado/semana2/mision017_fase2'
CV = BASE / 'FSp_REN_G3_prod_contraste_20261026_v1'; PROTO = BASE / 'F3c_FSp_REN_prototipo_20261026_v1'
HISTORY = BASE / 'FSp_historia_compatibilidad_20261026_v1'; LINK = BASE / 'enlace_numero_marca_revision_20261026_v1'
spec = importlib.util.spec_from_file_location('writer_RFS1P_close', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def reference(path):
    return {'path': w.rel(path), 'sha256': w.sha(path)}


def main():
    assert not (CV / 'completion_receipt.json').exists()
    a = w.read(CV / 'report.json'); v = w.read(CV / 'additional_veto_points.json')
    p = w.read(PROTO / 'report.json'); h = w.read(HISTORY / 'report.json'); link = w.read(LINK / 'report.json')
    assert a['candidate_id'] == 'RFS1P' and not a['all_criteria_pass'] and a['old_calibration_reused'] == 0
    assert p['submission_allowed'] is False and p['CSV']['rows'] == 209063 and p['NB_rows'] == 158980
    assert h['all199explained'] and h['prototype_unchanged_SHA'] == p['CSV']['sha256']
    assert link['new_model_fits'] == 0 and link['synthetic_homogeneous_risk_identities']['old_cost_proxy_product_recovers_lambda_mu_in_expectation']
    stamp = datetime.now(timezone.utc); archive = CV / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = ('No repetir los60modelos fuente, las matrices, RFS1/RFS1P, el bootstrap REN o la compatibilidad de199filas: ya terminaron. '
        'El test2025es76.04%NB y la receta REN no lo cambia; la sensibilidad ponderada de RFS1P es solo+.00038157 y el veto A1 original sigue negativo. '
        'Antes de añadir modelos/variables, registrar un único contraste de aplicación FSp a NB con la misma configuración prod, G3, C0 protegido, '
        'kappa por ámbito ya guardados y pesos .25/.25/.5. No reestimar nada. Medir la aportación NB separadamente y la receta completa REN+NB '
        'como combinación fija, con totales año/ramo/negocio conservados y criterios existentes. La evidencia NB negativa recibida era de otra '
        'receta/ámbito y no sustituye este contraste aislado sobre el núcleo reconstruido. Registrar hipótesis, coste y foro antes de puntuar; '
        'si también falla, documentar el fallo concreto antes de una calibración estándar adicional. '
        'El prototipo ed639b1c conserva158980NB y50083RENcambiadas, está explícitamente no admitido; no enviarlo al recuperar cuota. '
        'La revisión número/marca preserva la validez del producto proxy agregado en un riesgo homogéneo y no demuestra superioridad de otro enlace: '
        'no rehacer30modelos solo por una diferencia semántica. Para interpretar frecuencia nativa se necesitarían ambos offsets coherentes y nueva prueba. '
        'Falta aún F3c/F2 histórico completo y el A1 corregido; no sustituirlo por A1 original ni repetir el inventario exacto sin cambios. '
        '2024abierto como desarrollo, B00/alternativas preservados, mejor público0.16914,cuota0,meta0.17activa.')
    note = '\n\n## Despliegue FSp y prototipo2025: mejora parcial, nuevo negocio pendiente, 26 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('El control RFS1P usa los mismos productores fuente 2021–2024 y clima emergente 2023–2024 que el despliegue previsto. '
        'Sustituyó solo los componentes f/s de 2023 del contraste anterior; G3, grupos, C0, pesos, KP100, normalización y criterios quedaron iguales. '
        'Los 60 modelos ya guardados no se ajustaron otra vez. Este es un control del flujo disponible al corte de diciembre de 2024, '
        'no una predicción prospectiva de 2023 con información entonces disponible.\n\n')
    note += '| Medida | Resultado |\n|---|---:|\n'
    note += f'| D² G3 | {a["scores"]["G3"]:.8f} |\n| D² RFS1P | {a["scores"]["RFS1"]:.8f} |\n| Diferencia global | {a["delta_vs_G3"]:+.8f} |\n'
    note += f'| IC 95 % por componentes, fuente fija | [{a["bootstrap95"][0]:+.8f}; {a["bootstrap95"][1]:+.8f}] |\n'
    note += f'| Tras quitar los 31 grupos favorables | {a["post31_favorable_groups_delta"]:+.8f} |\n'
    note += f'| Sensibilidad hacia composición2025, solo punto | {v["weighted2025_incremental_delta_vs_G3"]:+.8f} |\n'
    note += f'| Sustituto A1 original2024, G3+RFS1P frente a A1 | {v["A1_original2024_weighted_deltas"]["A1_G3_RFS1P"]:+.8f} |\n'
    note += ('\nLos cinco folds y los dos años son positivos, con un intervalo positivo. Persisten el mínimo global de +0,002 incumplido '
        'y la concentración de la ganancia. El sustituto A1 original mejora respecto de añadir solo G3, pero la diferencia total sigue ligeramente negativa. '
        'Los pesos2025 se reutilizaron sin clasificador o remuestreo nuevo; su fallo anterior de ESS continúa, así que son sensibilidad y veto, no una evaluación primaria rescatada. '
        'El A1 original tampoco sustituye al A1 corregido o al F3c/F2 completo que aún falta reproducir.\n\n'
        'La composición es decisiva: 94.259 de 109.296 filas históricas son renovación, frente a 50.083 de 209.063 en2025. '
        'El 76,04 % del test es nuevo negocio. La variante que solo cambia renovaciones deja ese bloque mayoritario intacto; '
        'no se extrapola su diferencia local de +0,00185 como si fuera una ganancia pública de igual tamaño. '
        'Antes de más complejidad se medirá la aportación aislada de FSp en NB con el mismo núcleo, sin ajustar otro parámetro.\n\n'
        'Se construyó el prototipo2025 con el F3c medido como padre real. Son 209.063 filas en orden oficial, con los 158.980 precios NB exactamente iguales '
        'y 50.083 renovaciones modificadas. Usa la media fija de cinco miembros normalizados, cuyos kappa ya estaban guardados. '
        'No se aprendieron pesos de mezcla. El OOF evaluó un estimador por ámbito retenido y no un ensemble anidado de estos cinco miembros; esa diferencia de despliegue queda pendiente. '
        'Los totales REN se mantienen antes de redondear y cambian en conjunto solo +0,000074CU tras el redondeo.\n\n'
        'El flujo anualiza f por su exposición original, forma una razón sin unidades frente a T2b y mantiene el precio de periodo del padre. '
        'El futuro usa q=1 y no multiplica por un cp2025cero. Se hicieron tres inferencias T2b sobre50.083REN, 192filas históricas de control '
        'y96de orden, además de15normalizadores sin etiquetas. Los 192controles históricos coinciden exactamente con las tasas guardadas. '
        'Pasaron identidad de peso cero, claves/orden, cambios arbitrarios de componentes NB ignorados, rechazo de claves faltantes/duplicadas y tasas negativas, '
        'redondeo racional exacto contrastado con Decimal y fórmula escalar independiente en espacio logarítmico.\n\n'
        'Aparecieron 199 discrepancias de compatibilidad con el T2b publicado de2025, incluidas diferencias grandes por fila. '
        'Se registró antes una prueba de199inferencias: al cambiar únicamente los dos historiales al modo legado, las199reproducen el CSV antiguo dentro de1microCU. '
        'Esto explica la diferencia de ventana, sin certificar cuál fue el entorno original ni cambiar el prototipo para forzar coincidencia. '
        'El prototipo conserva la ventana explícita que termina en el corte conocido; no interpreta el tramo posterior al corte como observado sin avisos. '
        'Las fechas de reporte aportadas llegan al30/12/2024; no se extendió su conocimiento a un día no observado.\n\n'
        'El archivo resultante es un prototipo mecánicamente comprobado, no una entrega admitida. Fallan pruebas predictivas y faltan comparador completo y '
        'validación del ensemble final. Su creación no autoriza enviarlo cuando cambie la cuota. Se mantienen F3c como entrega vigente y B00, F2/C1 y todas las alternativas. '
        'No hubo envíos, nuevos modelos o C0 en esta unidad. Sí se cuentan165momentos de calibración del control prod,30normalizadores del contraste, '
        '30nuevos del sustituto A1 y40reproducidos de G3,15del prototipo, un CSV nuevo y las inferencias descritas.\n\n'
        'Se revisó también el enlace número/marca con los quince peligros de la fuente. El ejemplo homogéneo confirma que el producto del proxy con offset de coste '
        'y la marca observada puede recuperar el coste esperado; no se declaró inválido FSp. El enlace con offset de número y marca corregida por G_C/G_N '
        'permite interpretar sus componentes bajo supuestos condicionales, pero esta revisión sin ajuste no demuestra mejor rendimiento ni justifica rehacer treinta modelos. '
        'En autos NB2024 las razones de coste/número son cercanas a uno para la mayor parte de exposiciones; subsidence y algunos peligros de hogar tienen mayor variación. '
        'Los supuestos de cola1095, reservas y maestros sin fecha siguen abiertos.\n\n'
        'Mejor público procesado: 0,16914; objetivo0,17 aún no conseguido. La cuota consultada continúa en0 y se preserva. 2024 sigue abierto por autorización humana, '
        'con evaluación exploratoria adaptativa y sin revisión profesional independiente.\n\n'
        'Evidencia principal: ' + w.rel(CV / 'report.json') + '; vetos: ' + w.rel(CV / 'additional_veto_points.json') +
        '; prototipo: ' + w.rel(PROTO / 'report.json') + '; compatibilidad: ' + w.rel(HISTORY / 'report.json') +
        '; número/marca: ' + w.rel(LINK / 'report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_RFS1P_Y_PROTO2025.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = CV / 'forum_resultado_y_prototipo.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-RFS1P-PROTOTIPO-RESULTADO',
        '--asunto', 'RFS1P y prototipo2025: mejora parcial; el bloque NB sigue pendiente', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'production_consistency_positive_partial_prototype_not_admitted',
        'document': w.rel(doc), 'CV': reference(CV / 'report.json'), 'vetoes': reference(CV / 'additional_veto_points.json'),
        'prototype': reference(PROTO / 'report.json'), 'prototype_CSV': p['CSV'],
        'history_compatibility': reference(HISTORY / 'report.json'), 'count_mark_review': reference(LINK / 'report.json'),
        'new_empirical_moment_constants': 165, 'new_price_model_fits': 0, 'new_C0_fits': 0,
        'new_T2b_primary_future_inference_rows': 50083, 'historic_check_rows': 192, 'future_shuffle_check_rows': 96,
        'diagnostic_legacy_history_inference_rows': 199, 'new_candidate_price_rows': 50083, 'new_CSVs': 1,
        'new_submissions': 0, 'submission_allowed': False, 'submission_ready': False, 'formal_promotion': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False,
        'next_unit': next_unit, 'forum': json.loads(response.stdout)}
    counter = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counter)
    assert 'phase2_RFS1P_and_prototype' not in c
    w.update(counter, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': c['cumulative_closed_form_constants'] + 165,
                       'phase2_RFS1P_and_prototype': receipt}, archive)
    phasepath = R / 'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phasepath)
    assert phase['new_price_fits'] == 167 and phase['new_submissions'] == 2
    w.update(phasepath, {'utc': stamp.isoformat(), 'FSp_REN_G3_production_consistency': receipt,
                         'pending_local_prototype': {'status': p['status'], 'CSV': p['CSV'], 'submission_allowed': False,
                                                     'predictive_admission_established': False, 'evidence': reference(PROTO / 'report.json')},
                         'new_FSp_calibration_moments': phase['new_FSp_calibration_moments'] + 165,
                         'new_FSp_derived_peril_factors': phase['new_FSp_derived_peril_factors'] + 75,
                         'active_execution': None, 'next_unit': next_unit}, archive)
    statepath = ROOT / 'Preparación/ESTADO_PROYECTO.json'; own = w.read(statepath)['week_2_mission017_phase2_20261025']
    own.update(FSp_REN_G3_production_consistency=receipt, pending_local_prototype={'CSV': p['CSV'], 'submission_allowed': False},
               active_jobs=[], next_unit=next_unit)
    w.update(statepath, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(R / 'registro/semana2_mision017_renovaciones_FSp_actual.json', {'utc': stamp.isoformat(),
        'status': receipt['status'], 'production_consistency_and_prototype': receipt, 'next_unit': next_unit}, archive)
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / filename, note, archive)
    w.append(R / 'docs/archivo/semana2/MISION017_RENOVACIONES_Y_RECUPERACION_FSp.md', note, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_RFS1P_prototype_report': w.rel(doc),
        'week_2_mission017_unadmitted_FSp_prototype_CSV': p['CSV']['path']}, archive)
    (CV / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'new_moments': 165, 'new_models': 0, 'new_C0': 0,
                      'new_submissions': 0, 'prototype_submission_allowed': False, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
