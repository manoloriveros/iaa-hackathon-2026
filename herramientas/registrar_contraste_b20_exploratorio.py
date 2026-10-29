"""Cierra el ensayo autorizado, conserva adversos y actualiza contadores propios."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepend(path, key, value):
    raw = path.read_text(encoding='utf-8-sig')
    assert key not in json.loads(raw), 'Entrada ya existente: ' + key
    entry = json.dumps({key: value}, ensure_ascii=False, indent=2)[1:-1].strip('\n')
    result = '{\n' + entry + ',\n' + raw[raw.index('{') + 1:].lstrip('\r\n')
    json.loads(result)
    assert path.read_text(encoding='utf-8-sig') == raw, 'Cambio concurrente; reintentar cierre.'
    path.write_text(result, encoding='utf-8')


def main():
    index = REPO / 'registro/semana2_b20_contraste_exploratorio_actual.json'
    assert not index.exists(), 'Ensayo ya registrado; no duplicar contadores.'
    plan, evaluation = read(RUN / 'plan_execution.json'), read(RUN / 'evaluation.json')
    verification, work = read(RUN / 'verification.json'), read(RUN / 'training_completed.json')
    assert verification['failed'] == 0 and evaluation['2024_test_closed']
    assert not evaluation['promotion'] and not evaluation['submission']
    assert sha(RUN / 'plan_execution.json') == evaluation['plan_sha256']
    for source in plan['frozen_sources'] + plan['implementation_sources']:
        assert sha(ROOT / source['path']) == source['sha256'], 'Fuente cambió antes de cerrar.'
    utc = datetime.now(timezone.utc).isoformat()
    counter_path = REPO / 'registro/semana2_contadores_propios_actual.json'
    previous = counter_path.read_bytes()
    (RUN / 'counter_before.json').write_bytes(previous)
    counters = json.loads(previous.decode('utf-8-sig'))
    assert counters['cumulative_price_base_fits'] == 195 and counters['cumulative_closed_form_constants'] == 285
    increment = {'id': plan['id'], 'run': rel(RUN), 'price_GLM_fits': work['new_price_GLMs'],
        'constant_values': work['new_intercept_values'], 'slope_calibration_fits_separate': 5,
        'reporting_fits': 60, 'mixture_frequency_constants_separate': 60,
        'mixture_positive_severity_means_from_reporting_separate': 60,
        'normalized_mixtures_separate': 10, 'outer_bundles_reused_not_fits': 5,
        'synthetic_preflight_invocations_excluded_from_actual_fit_counter': 32}
    counters['increments'].append(increment)
    counters['as_of_utc'] = utc
    counters['cumulative_price_base_fits'] += increment['price_GLM_fits']
    counters['cumulative_closed_form_constants'] += increment['constant_values']
    counters['supplementary_reporting_peril_fits_since_counter_start'] += 60
    counters['mixture_frequency_constants_since_counter_start_separate'] += 60
    counters['mixture_positive_severity_means_since_counter_start_separate'] += 60
    counters['slope_calibration_fits_since_counter_start_separate'] = counters.get('slope_calibration_fits_since_counter_start_separate', 0) + 5
    counters['latest_exploratory_contrast_index'] = rel(index)
    counters['reporting_counter_notice'] = '135 supplementary reporting-peril fits:75 prior sensitivity +60 B20 nested exploration; historical preparation105 and other authors remain separate.'
    counters['constant_counter_notice'] = 'This contrast adds10 terminal profiled/level intercept values,5 slope fits separate,60 frequency constants separate and60 weighted marks from reporting separate. Optimizer profile evaluations are not independent fitted models.'
    dump(RUN / 'counter_after.json', counters)
    dump(counter_path, counters)
    summary = evaluation['summary']
    influence = {x['reference']: x for x in evaluation['influence']}
    slopes = [x['calibration']['b_S'] for x in evaluation['folds']]
    source_plan = REPO / 'registro/semana2_b20_enmienda_exploratoria_v2_20261024.json'
    amendment_doc = REPO / 'docs/archivo/semana2/ENMIENDA_CONTRASTE_B20_2023_V2.md'
    amendment_doc.write_text(f'''# Enmienda exploratoria del contraste de B20

Codex. Autorización directa del participante: «{plan['authorization_literal']}». Criterios registrados el {plan['registered_utc']}, antes del entrenamiento real iniciado el {read(RUN / 'training_started.json')['utc']}.

La versión 1 queda conservada con soporte fallido y mecanismo plausible, sin establecer. La versión 2 permite entrenar una sola comparación exploratoria aun con esa concentración conocida. No declara el soporte resuelto ni cambia la política común de promoción. Mantiene integridad, exclusión de folds y todos los umbrales predictivos previos.

S comprime las relatividades de edificios mediante una pendiente entre cero y uno y su intercepto perfilado; L mantiene pendiente uno y ajusta solo nivel. B20 original es el ancla. Se conservan alpha1, siete efectos, T0, rho1, folds y todas las pérdidas. Autos y contenidos deben mantener tasas y predicciones exactas. No hay búsqueda de parámetros, recetas adicionales, factores por bandas o eliminación de siniestros.

Los criterios conjuntos son: mejora global S−L de al menos0,0005; S−B20 no negativa; al menos4/5folds no negativos frente a L y peor fold no inferior a−0,001; pendiente interior en al menos4/5y ninguna pendiente cero; reducción de al menos20% de la brecha de A/E entre bandas extremas originales, sin invertirla; pérdidas por segmento frente a B20 no inferiores a−0,001; ventaja no negativa después del diagnóstico de influencia en ambas comparaciones; cambio absoluto del total nominal de edificios no superior al5%. Los criterios se aplican con precisión completa.

La concentración deja de ser veto previo únicamente para este ensayo. Sus fallos se conservan y siguen limitando la interpretación. Un incumplimiento predictivo produce rechazo exploratorio y conserva B20 original; incluso un cumplimiento total solo aportaría una señal para revisión, sin promoción. No se añaden intervalos o bootstrap: se informan los cinco folds, dispersión de pendientes e influencia conforme al diseño previo.

Validación anidada: cada calibrador exterior excluye su fold de todos los ancestros; cada predicción interna excluye además su propio fold. C0, medianas, escalas, categorías y GLM comparten esos tres folds de ajuste. Antes de datos reales pasaron seis pruebas sintéticas del flujo completo. La preparación materializó únicamente periodos y siniestros de ocurrencia2023. El origen de notificaciones multiaño se leyó con predicado Arrow de mercado/ramo/IDs aceptados/ocurrencia2023 antes de materializar, sin convertir la tabla completa.

Presupuesto ejecutado:10GLM internos de edificios,60curvas de reporte,60constantes de frecuencia,60marcas medias salidas de esas curvas,10mezclas,5pendientes y10valores finales de intercepto. Se reutilizan cinco modelos exteriores; no hay ajustes nuevos de otros ramos. Los valores de intercepto de ambos brazos se cuentan por separado; las evaluaciones numéricas del perfil no son modelos adicionales. CPU local, dos hilos.

La versión y el código previos a la reparación de escritura Parquet permanecen en `implementation_attempt1/`. La reparación ocurrió antes de cualquier ajuste real y solo sustituyó el motor de escritura de pandas por Arrow; no cambió datos, modelo o criterios. La validación2024/test queda cerrada. Sin promoción, catálogo nuevo, Kaggle, remoto, nuevas automatizaciones o delegación.

[Contrato estructurado]({source_plan.relative_to(REPO).as_posix().replace('registro/', '../../registro/')}) y [resultado](CONTRASTE_EXPLORATORIO_B20_2023.md). La versión1 y todos sus resultados adversos permanecen intactos. Investigación adaptativa sobre2023, revisión propia de Codex; no confirmación independiente o revisión profesional humana.
''', encoding='utf-8')
    report_path = REPO / 'docs/archivo/semana2/CONTRASTE_EXPLORATORIO_B20_2023.md'
    fold_rows = '\n'.join(f"| {x['fold']} | {x['calibration']['b_S']:.4f} | {x['delta_S_L']:+.6f} | {x['delta_S_raw']:+.6f} |" for x in evaluation['folds'])
    failed = ', '.join(evaluation['failed_criteria'])
    report_path.write_text(f'''# Contraste exploratorio B20: mejora media frágil, rechazo por influencia

Codex, cierre UTC {utc}. El contraste se entrenó y se evaluó una sola vez con la [enmienda autorizada](ENMIENDA_CONTRASTE_B20_2023_V2.md). Cumple17de19condiciones predictivas y falla los dos controles de influencia. Se conserva B20 original y todas las alternativas. No se promueve un modelo ni se envía a Kaggle.

## Resultado sobre2023

| Brazo | D² global | A/E global | Coste observado predicho, millones CU |
| --- | ---: | ---: | ---: |
| B20 original | {summary['raw']['D2']:.6f} | {summary['raw']['actual_over_expected']:.4f} | {summary['raw']['predicted_total']/1e6:.3f} |
| L, solo nivel | {summary['L']['D2']:.6f} | {summary['L']['actual_over_expected']:.4f} | {summary['L']['predicted_total']/1e6:.3f} |
| S, compresión y nivel | {summary['S']['D2']:.6f} | {summary['S']['actual_over_expected']:.4f} | {summary['S']['predicted_total']/1e6:.3f} |

Son las mismas50.094filas y30.869componentes, con T0 observado y C0 condicionado; no es validación del coste último2025. La ganancia global de S es {evaluation['delta_S_L']:+.6f} frente a L y {evaluation['delta_S_raw']:+.6f} frente al B20 original. La hipótesis de compresión resulta compatible con estos puntos, pero la influencia impide aceptar la mejora como estable.

| Fold exterior | Pendiente S | ΔD² S−L | ΔD² S−B20 |
| --- | ---: | ---: | ---: |
{fold_rows}

Las cinco pendientes son interiores, entre {min(slopes):.3f} y {max(slopes):.3f}. S mejora frente a L en los cinco folds, pero pierde ligeramente frente al B20 original en dos. Ese rango no es un intervalo de confianza: los conjuntos de ajuste se solapan y2023ya se usó repetidamente para investigar.

## Por qué se rechaza

La regla previa elimina únicamente de la evaluación los31componentes más favorables de cada comparación. No se borran del ajuste, no se corrigen sus costes y no se reentrena.

| Comparación | ΔD² completo | ΔD² sin los31componentes más favorables | Regla previa |
| --- | ---: | ---: | --- |
| S−L | {evaluation['delta_S_L']:+.6f} | {influence['L']['delta_after_removal']:+.6f} | Debía seguir≥0; falla |
| S−B20 | {evaluation['delta_S_raw']:+.6f} | {influence['raw']['delta_after_removal']:+.6f} | Debía seguir≥0; falla |

Pasaron los demás criterios: magnitud global, acuerdo por fold, pendientes no degeneradas, segmentos, invariancia de autos/contenidos y nivel. La brecha logarítmica entre las bandas extremas originales baja de {evaluation['tail_gap']['L']['G']:.4f} con L a {evaluation['tail_gap']['S']['G']:.4f} con S. Los A/E extremos pasan de1,68/0,61a1,06/1,03. El total nominal condicionado de edificios cambia {evaluation['buildings_nominal_change_S_raw']:+.2%}, dentro del máximo previo de5%. Esas mejoras no compensan los dos incumplimientos de influencia.

El soporte original sigue fallido. Se pudo medir además el soporte de las diez colas interiores de calibración, antes desconocido: solo una cumple las reglas originales. No se agrupan bandas o relajan umbrales para convertir ese resultado en aprobado. El entrenamiento exploratorio estaba autorizado precisamente conservando esta carencia, no dando por resuelto su soporte.

## Integridad y recursos

Las seis pruebas sintéticas previas comprobaron C0, imputación, escala, categorías, GLM e intercepto/pendiente en conjunto: alterar las etiquetas del fold exterior no cambió ningún objeto aprendido. Hubo32invocaciones sintéticas del flujo, incluidas las rechazadas; no se suman a los ajustes del concurso.

La comprobación posterior pasa219controles: fuentes y criterios congelados, pertenencias exactas de los diez ámbitos internos, pesos de notificaciones, ausencia de cruces por componente/cliente/dirección, replay exacto de tasas/C0, identidades del intercepto y condiciones de primer orden. La métrica se coteja con scikit-learn. Se bloquearon las rutinas de ajuste durante esta comprobación: cero reentrenamientos.

Se hicieron diez GLM interiores, sesenta ajustes de reporte, sesenta constantes de frecuencia, diez mezclas y cinco calibraciones de pendiente con diez interceptos finales. Cinco B20 exteriores se reutilizaron y sus predicciones originales se reprodujeron exactamente. Los contadores propios de precios pasan195→205y de constantes285→295; pendientes y auxiliares se contabilizan aparte. Los519siniestros de edificios y los12.580periodos usados por la etapa interna pertenecen a2023. No se materializaron etiquetas de pólizas2024/test ni se ejecutaron sus productores.

El fallo de escritura Parquet se produjo antes del primer ajuste real, se conservó y se reparó sin cambiar criterios. Se guardan las diez parejas C0/GLM, predicciones internas, cinco calibradores, anclas exteriores, tres OOF completos y resultados adversos en privado. No hay un CSV2025nuevo, modelo promovido, cambio de política común o envío a Kaggle. Este resultado no dispara otra pendiente, alpha, banda, semilla o receta.

[Contrato previo](../../registro/semana2_b20_enmienda_exploratoria_v2_20261024.json), [índice del resultado](../../registro/semana2_b20_contraste_exploratorio_actual.json) y evidencia completa en `privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2`. El informe conserva precisión resumida; `evaluation.json` contiene valores completos y las19condiciones, y `verification.json` sus recibos técnicos. Revisión propia de Codex, sin revisión profesional humana o confirmación independiente. Propósito y límites, procedencia y cambios se documentan conforme a las prácticas IAA adoptadas por el proyecto.
''', encoding='utf-8')
    record = {'id': plan['id'], 'author': 'Codex', 'utc': utc, 'path_base': 'workspace_root',
        'status': 'trained_and_verified_exploratory_rejected_on_two_influence_criteria',
        'authorization_literal': plan['authorization_literal'], 'run': rel(RUN),
        'amendment': rel(source_plan), 'amendment_sha256': sha(source_plan),
        'preregistered_utc': plan['registered_utc'], 'execution_plan_sha256': sha(RUN / 'plan_execution.json'),
        'documentation': rel(report_path), 'documentation_sha256': sha(report_path),
        'evaluation': {'path': rel(RUN / 'evaluation.json'), 'sha256': sha(RUN / 'evaluation.json')},
        'verification': {'path': rel(RUN / 'verification.json'), 'sha256': sha(RUN / 'verification.json'), 'passed': verification['passed'], 'failed': 0},
        'summary': summary, 'delta_S_L': evaluation['delta_S_L'], 'delta_S_raw': evaluation['delta_S_raw'],
        'failed_criteria': evaluation['failed_criteria'], 'predictive_checks_passed': 17, 'predictive_checks_total': 19,
        'influence': [{k: v for k, v in x.items() if k != 'selected_group_ids'} for x in evaluation['influence']],
        'support_v1': 'FAILED preserved', 'inner_tail_cells_passing_v1': 1, 'inner_tail_cells_total': 10,
        'training_work': work, 'counters_before': {'path': rel(RUN / 'counter_before.json'), 'sha256': sha(RUN / 'counter_before.json')},
        'counters_after': {'path': rel(RUN / 'counter_after.json'), 'sha256': sha(RUN / 'counter_after.json')},
        'counter_current_path_changed_by_this_authorized_registration': True,
        'reference': 'W2-B00 for this historical line', 'raw_B20_preserved': True,
        'promotion': False, 'submission': False, 'new_catalog_recipes': 0, '2024_test_closed': True,
        'remote': False, 'delegation': False, 'professional_independent_validation': False,
        'forum_prior': plan['forum_prior'], 'forum_result': 'COD-S2-20261024-B20-EXPL-V2-RESULT',
        'known_limits': evaluation['limits']}
    dump(index, record)
    prepend(ROOT / 'Preparación/ESTADO_PROYECTO.json', 'semana2_b20_contraste_exploratorio_v2_20261024',
        {k: record[k] for k in ['id', 'author', 'utc', 'path_base', 'status', 'run', 'documentation',
                              'delta_S_L', 'delta_S_raw', 'failed_criteria', 'support_v1', 'promotion', 'submission', '2024_test_closed']})
    prepend(ROOT / 'RUTAS_PROYECTO.json', 'week_2_b20_exploratory_contrast_index', rel(index))
    prepend(ROOT / 'RUTAS_PROYECTO.json', 'week_2_b20_exploratory_contrast_report', rel(report_path))
    note = f'''\n\n## S2-B20-CONTRASTE-EXPLORATORIO-v2-20261024: entrenado, rechazado por influencia

Codex, UTC{utc}. Instrucción directa: «{plan['authorization_literal']}». Enmienda v2 registrada antes de fit en foro{plan['forum_prior']} y {rel(source_plan)}. Permite este entrenamiento exploratorio conservando soporte v1FAILED/mecanismo plausible; todos los umbrales predictivos originales intactos, sin promoción o2024. Se completó el flujo anidado C0/imputación/escala/OHE/GLM/calibración, diez ámbitos interiores de tres folds y cinco calibradores exteriores; seis pruebas sintéticas completas y219controles de artefactos, sin fallo técnico. Solo2023:519notificaciones de edificios/12.580periodos,50.094filas al evaluar tres brazos con autos/contenidos exactos.

D²2023: B20 {summary['raw']['D2']:.9f}, L {summary['L']['D2']:.9f}, S {summary['S']['D2']:.9f}. S−L {evaluation['delta_S_L']:+.9f}, S−raw {evaluation['delta_S_raw']:+.9f}. Pendientes0,396–0,544y cincofolds positivos frente a L.17/19criterios pasan; fallan únicamente influencia S−L yS−raw: sin31componentes más favorables en evaluación, {influence['L']['delta_after_removal']:+.9f} y{influence['raw']['delta_after_removal']:+.9f}. Sin borrado/refit, no adoptar por mejora agregada. Soporte v1 conservado y colas interiores ahora medidas:1/10pasa. Investigación adaptativa, sin CI/bootstrap nuevos, confirmación independiente o revisión humana implícitas.

Trabajo nuevo:10GLM interiores,60curvas/60frecuencias/60marcas derivadas/10mezclas,5pendientes y10interceptos;5B20 exteriores reutilizados. Contadores propios195→205precios y285→295constantes; pendientes/auxiliares separados. Primer fallo técnico de escritura antes de fit preservado, resuelto con Arrow sin modificar criterios; no repetir entrenamiento. Informe {rel(report_path)}, índice {rel(index)}, recibos/modelos/OOF en {rel(RUN)}. No cambia B00/B20 o catálogo/política común; no2024/test, producción2025, promoción, Kaggle, remoto, automatización o delegación. Resultado adverso no dispara otra receta. La nueva instrucción humana y v2 sustituyen solo la prohibición de ejecutar este ensayo de los cortes previos, conservados como historia.
'''
    for path in [ROOT / 'Preparación/MEMORIA_PROYECTO.md', ROOT / 'Preparación/DECISIONES.md']:
        with path.open('a', encoding='utf-8') as handle:
            handle.write(note)
    (RUN / 'aporte_resultado.md').write_text(note, encoding='utf-8')
    files = [{'path': p.relative_to(RUN).as_posix(), 'sha256': sha(p)} for p in sorted(RUN.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    dump(RUN / 'manifest.json', {'utc': utc, 'files': files})
    print(json.dumps({'index': rel(index), 'verdict': evaluation['verdict'], 'price_counter': 205,
                      'constants_counter': 295, 'promotion': False, 'submission': False}))


if __name__ == '__main__':
    main()
