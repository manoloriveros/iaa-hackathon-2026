"""Integra B20 verificado, con contadores y registro comunes; nunca entrena."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    run = REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1'
    plan, report, verification, fixtures = [read(run/x) for x in ['plan_snapshot.json', 'report.json', 'verification.json', 'fixture_checks.json']]
    assert verification['failed'] == fixtures['failed'] == 0
    assert report['new_price_base_fits'] == 15
    now = datetime.now(timezone.utc).isoformat()
    common = REPO/'registro/semana2_desarrollo2023_actual.json'
    counterpath = REPO/'registro/semana2_contadores_propios_actual.json'
    nightpath = REPO/'registro/semana2_continuidad_nocturna.json'
    before = {p: p.read_bytes() for p in [common, counterpath, nightpath]}
    previous, counter, night = [json.loads(before[p].decode('utf-8-sig')) for p in [common, counterpath, nightpath]]
    assert previous['id'] == 'S2-DEV2023-v8-20261024' and previous['run'] == plan['input_run'], 'Índice concurrente: conciliar sin repetir ajuste'
    assert counter['cumulative_price_base_fits'] == 180 and counter['cumulative_closed_form_constants'] == 285, 'Contador concurrente'
    assert all(x['id'] != plan['id'] for x in counter['increments']), 'Ya contado; no duplicar'
    parent_snapshot = REPO/'registro/semana2_desarrollo2023_v8_snapshot.json'
    if parent_snapshot.exists():
        assert parent_snapshot.read_bytes() == before[common]
    else:
        parent_snapshot.write_bytes(before[common])
    (run/'counter_before_integration.json').write_bytes(before[counterpath])
    (run/'main_index_before_integration.json').write_bytes(before[common])
    # Recheck frozen evidence after all technical work, before changing current pointers.
    for item in plan['frozen_sources']:
        assert sha(ROOT/item['path']) == item['sha256'], item['path']
    summary = {x['model_id']: x for x in report['summary']}
    segments = read(run/'diagnostics/segments.json')
    linebusiness = [x for x in segments if x['dimension'] == 'line_business' and x['model_id'] == 'W2-B20']
    evidence = lambda name: {'path': rel(run/name), 'sha256': sha(run/name)}
    decisions = [
        {'id': 'RIDGE-RECIPE', 'hypothesis': plan['hypothesis'], 'criterion_before_fit': plan['acceptance_before_fit'],
         'result': 'One fixed alpha1 recipe,15fits. Exactly same7features and source data asB19; no new variables or interactions.',
         'consequence': 'No hyperparameter scan, per-line picking or additional refit. All-coefficient shrinkage is not a coverage-only intervention.'},
        {'id': 'RIDGE-INTEGRITY', 'evidence': evidence('verification.json'),
         'result': '542separate checks pass: frozen sources,21recipe OOF with20old exact,training-only transforms,native/manual replay,KKT,finite-difference derivative,penalized objectives and coefficientnorms.',
         'consequence': 'Technically usable exploratory artifact; this does not establish predictive superiority or economic correctness of capital/ultimate.'},
        {'id': 'RIDGE-ADVERSARIES', 'evidence': evidence('fixture_checks.json'),
         'result': '48focused adversaries pass, including3actual native commands rejecting duplicate run,changedcode/changedsource beforefit. No additional fits.',
         'consequence': 'Preserve expected failures. Repeated recipe invocation cannot start another training run.'},
        {'id': 'RIDGE-PREDICTIVE', 'evidence': evidence('diagnostics/new_pairs.json'), 'result': report['pairs'],
         'consequence': 'Do not promote. B20/B14 interval crosses0; every own31group influence contrast becomesnegative. Positive B20/B19 interval is exploratory after adaptive search.'},
        {'id': 'RIDGE-SEGMENTS', 'evidence': evidence('diagnostics/segments.json'),
         'result': linebusiness,
         'consequence': 'Publish motornewbusiness andcontentsnewbusiness harm versusB14; no posthoc routing/blend or equivalence claim.'},
        {'id': 'RIDGE-COEFFICIENTS', 'evidence': evidence('diagnostics/coefficient_stability.json'),
         'result': 'Squared norms shrink inall15fits, but buildingcoverage ratio still crosses1 acrossfolds. Coefficient ratios conditional,notcausal or contract eligibility.',
         'consequence': 'Shrinkage is verified; stable coverage direction and a coverage-driven gain are not established.'},
        {'id': 'RIDGE-NEXT', 'result': 'KeepB00 andB01-B20,2024/testclosed,prior externalheader exposure disclosed; all ultimate/capital/climate/credibility conditions persist.',
         'consequence': 'Next useful step is saved-artifact group/segment attribution,without morefits,alpha tuning,new variables or added model complexity.'}
    ]
    journal = {'id': plan['id'], 'author': 'Codex', 'utc': now, 'decisions': decisions,
               'scope': plan['scope'], 'professional_independent_validation': False}
    dump(run/'decision_journal.json', journal)
    docpath = REPO/'docs/archivo/semana2/GLM_RIDGE_COBERTURAS_2023.md'
    lines = ['# GLM ridge con coberturas: ensayo estándar de estabilidad', '',
        'Codex, corte UTC '+now+'. Se completó una sola receta preinscrita con quince ajustes locales sobre los cinco folds de 2023. La motivación fue concreta: B19 mejoró el ajuste en todas las celdas, pero empeoró fuera de muestra frente a B14. Se probó contracción antes de añadir variables, interacciones u otra familia.', '',
        'La receta pasa la revisión técnica. Su punto global mejora, pero no hay respaldo suficiente para promoverla: el intervalo frente a B14 incluye cero y todas las ventajas se invierten en el diagnóstico de grupos favorables. B00 y las veinte alternativas se conservan.', '',
        '## Resultado fuera de muestra', '',
        '| Modelo | D² global 2023 | A/E | Total observado predicho, CU |', '| --- | ---: | ---: | ---: |']
    for mid in ['W2-B00', 'W2-B14', 'W2-B19', 'W2-B20']:
        r = summary[mid]
        lines.append(f"| {mid} | {r['D2']:.6f} | {r['actual_over_expected']:.4f} | {r['predicted_total']:,.2f} |")
    lines += ['', 'Las 50.094 filas y los 30.869 componentes son los mismos para todos los modelos. La métrica global usa su propia desviancia nula; no promedia los scores por ramo. Son resultados exploratorios sobre datos de 2023 usados repetidamente para investigar, con T0 observado y C0 condicionados.', '',
        '| Contraste nuevo | Cambio D² | Intervalo exploratorio 95% | Tras retirar 31 grupos favorables |', '| --- | ---: | --- | ---: |']
    for pair in report['pairs']:
        lines.append(f"| B20 / {pair['reference']} | {pair['delta_D2']:+.6f} | [{pair['exploratory_lower95']:+.6f}; {pair['exploratory_upper95']:+.6f}] | {pair['delta_after_removal']:+.6f} |")
    lines += ['', 'Se calcularon solo las tres parejas nuevas, con 2.000 remuestreos pareados por componente y sorteos comunes. Los intervalos no ajustan la búsqueda adaptativa ni la incertidumbre de volver a ajustar modelos y primera etapa. El intervalo positivo frente a B19 no supera esas limitaciones. El análisis de influencia cambia únicamente la evaluación: no se borran siniestros o grupos ni se vuelve a entrenar.', '',
        '## Deterioros que conserva la decisión', '',
        '| Segmento | D² B20 | Cambio frente a B14 |', '| --- | ---: | ---: |']
    for row in linebusiness:
        parent = next(x for x in segments if x['model_id'] == 'W2-B14' and x['dimension'] == 'line_business' and x['label'] == row['label'])
        lines.append(f"| {row['label']} | {row['D2']:.6f} | {row['D2']-parent['D2']:+.6f} |")
    nominal_change = summary['W2-B20']['conditional_nominal_2023']/summary['W2-B19']['conditional_nominal_2023']-1
    lines += ['', 'Los tres ramos mejoran su punto agregado frente a B19 y B14, pero autos nuevos y contenidos nuevos pierden frente a B14. No se elige una receta por ramo o segmento después de observarlos. En hogar el A/E agregado de B20 supera uno; una mejor desviancia no acredita suficiencia del nivel.', '',
        f"El nominal condicionado de los mismos periodos de 2023 cambia {100*nominal_change:+.3f}% frente a B19. Es exposición nominal por tasa bajo el vínculo declarado, no una estimación validada del nivel último de 2025.", '',
        '## Qué cambió en la receta', '',
        'Tweedie de potencia 1,5 y enlace log, con las mismas siete variables por ramo, T0, C0, capital y folds de B19. El único cambio de hiperparámetros es alpha de cero a uno. La penalización actúa sobre todos los coeficientes numéricos estandarizados y categóricos codificados; el intercepto queda libre. No es una intervención exclusiva sobre cobertura. Alpha uno procede de la primera receta B01 y se fijó antes del ensayo, sin buscar otras intensidades.', '',
        'Medianas, escalas y categorías se aprenden solo con las filas de ajuste. Se conserva OHE con primera categoría omitida, frecuencia mínima 50 y máximo 40 categorías; el efecto de ridge depende de esa codificación, que queda explícita y fija. La respuesta es T0/e, el peso es raíz(e) y la predicción observada aplica e una vez. No se añaden máscaras estructurales, clima, credibilidad o calibración de nivel.', '',
        'La norma cuadrada de coeficientes baja en los quince ajustes y el objetivo penalizado mejora respecto al coeficiente sin penalizar evaluado en el mismo diseño. Eso comprueba el mecanismo de contracción. En edificios, la razón condicional de cobertura accidental activa frente a inactiva todavía recorre aproximadamente 0,801 a 1,375 entre folds y cambia de dirección. Los folds se solapan; ese rango no es un intervalo ni una relación causal o contractual.', '',
        '## Comprobaciones y siguiente decisión', '',
        f"Pasaron {verification['passed']} comprobaciones separadas con fit bloqueado y {fixtures['passed']} adversos focales, con solapamiento entre controles. La revisión reconstruye medianas, escalas e indicadores, predicción manual, objetivo general, gradiente penalizado y su derivada por diferencias finitas. Reproduce métricas con sklearn y el remuestreo con multiplicidades. Tres comandos nativos rechazan repetición, código cambiado o fuente cambiada antes de ajustar. No se repitió el entrenamiento para comprobarlos.", '',
        'Se mantienen B00 y B01–B20. No se promueve, retira una alternativa ni congela una lista final. El siguiente diagnóstico útil atribuye la ganancia a grupos y segmentos con los artefactos guardados, sin ajustar alpha o añadir complejidad. La verificación propia de Codex no es validación profesional independiente.', '',
        '2024 y test permanecen cerrados para precios, predicciones y scores de este trabajo; no se leyó el ledger. Sigue declarada la exposición previa a métricas externas en un asunto del foro, sin usar esa información o afirmar ceguera completa. Permanecen las limitaciones de capital, último, reservas y reporte. La incidencia de Kaggle no autoriza enviar una prueba.', '',
        'Se hicieron quince ajustes nuevos: el contador propio pasa de 180 a 195 ajustes de precio y conserva 285 constantes. El linaje del catálogo principal tiene 120 ajustes y 60 constantes; las otras sensibilidades, auxiliares y curvas se cuentan aparte. Se reutilizan exactamente las veinte recetas anteriores.', '',
        '[Plan previo](../../registro/semana2_glm_ridge_coberturas_plan_v1.json), [índice](../../registro/semana2_glm_ridge_actual.json), [productor](../../src/semana2/entrenar_glm_ridge_coberturas2023.py), [comprobador](../../herramientas/verificar_glm_ridge_coberturas2023.py) y [adversos](../../herramientas/probar_glm_ridge_coberturas2023.py). La corrida, modelos y decisiones por fila permanecen en `privado/semana2/desarrollo2023/ridge20_20261024_v1`, fuera de Git. Se aplican las prácticas IAA de propósito y límites, validación y control de cambios y ficha del modelo, sin certificación.']
    docpath.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    history = list(previous.get('history', []))
    history.append({'id': previous['id'], 'index_snapshot': rel(parent_snapshot), 'sha256': sha(parent_snapshot)})
    index = {'id': plan['id'], 'author': 'Codex', 'as_of_utc': now, 'path_base': 'workspace_root',
             'status': 'standard_ridge_verified_uncertain_gain_and_segment_harms_no_promotion',
             'run': rel(run), 'documentation': rel(docpath), 'training_years': [2023], 'scored_years': [2023],
             'rows_per_model': 50094, 'groups': 30869, 'folds': 5,
             'new_price_base_fits': 15, 'new_closed_form_constants': 0,
             'cumulative_price_base_fits': 195, 'cumulative_closed_form_constants': 285,
             'catalog_lineage_price_base_fits': 120, 'catalog_lineage_closed_form_constants': 60,
             'models_consulted': [f'W2-B{i:02d}' for i in range(21)], 'summary': report['summary'], 'pairs': report['pairs'],
             'reference': 'W2-B00', 'alternatives_preserved': True, 'promotion': False,
             'confirmation_2024_open': False, 'confirmation_closed_by_current_user_instruction': True,
             'final_confirmation_roster_frozen': False, 'prior_external2024_header_exposure_disclosed': True,
             'scope_2024_test': report['scope_2024_test'], 'history': history,
             'forum_prior': plan['forum_prior'], 'forum_result': 'COD-S2-20261024-B20-RESULT',
             'oof': rel(run/'oof_2023.parquet'), 'oof_sha256': sha(run/'oof_2023.parquet'),
             'report': rel(run/'report.json'), 'report_sha256': sha(run/'report.json'),
             'plan': rel(REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json'), 'plan_sha256': report['plan_sha256'],
             'producer': plan['code'], 'producer_sha256': plan['code_sha256'],
             'verification': evidence('verification.json') | {'passed': verification['passed'], 'failed': 0},
             'fixtures': evidence('fixture_checks.json') | {'passed': fixtures['passed'], 'failed': 0},
             'manifest': rel(run/'manifest.json'), 'manifest_sha256': sha(run/'manifest.json'),
             'decision_journal': rel(run/'decision_journal.json'), 'decision_journal_sha256': sha(run/'decision_journal.json'),
             'submissions': 0, 'professional_independent_validation': False,
             'next_unit': 'Saved-artifact group/segment attribution; no newfit,alpha search,routing,2024 opening or complexity.'}
    counter['increments'].append({'id': plan['id'], 'run': rel(run), 'price_GLM_fits': 15,
                                  'constant_values': 0, 'auxiliary_fits': 0, 'reporting_fits': 0})
    counter['cumulative_price_base_fits'], counter['as_of_utc'] = 195, now
    assert counter['baseline']['price_base_fits']+sum(x['price_GLM_fits'] for x in counter['increments']) == 195
    unit = {'id': plan['id'], 'run': rel(run), 'documentation': rel(docpath),
            'verification': index['verification'], 'fixtures': index['fixtures'],
            'decision_journal': index['decision_journal'], 'forum_result': index['forum_result'],
            'index': 'Hackaton/Repositorio_IAA2026/registro/semana2_glm_ridge_actual.json'}
    night['completed_units'].append(unit)
    night['latest_completed_unit'], night['current_unit'] = unit, None
    night['updated_utc'] = now
    night['status'] = 'scheduled_ten_units_verified_B20_ridge_uncertain_and_segment_harms'
    night['next_unit'] = index['next_unit']+' Owncounters195/285; retainB00/B01-B20 and disclose prior2024header exposure. Keep existing window and Kaggle incident tracking.'
    night['queue'] = ['Attribute B20 group and segment gains/harms with saved2023 artifacts; no newfits,alpha scan,routing or more complexity.',
                      'Preserve ultimate/capital/reporting conditions and all21 recipes; no2024/test or additional confirmation.',
                      'Continue existing Kaggle incident monitor and honest final balance at07:00Bogota; do not repeat completed units.']
    night['latest_standard_ridge_index'] = unit['index']
    night['no_retraining_or_suite_repetition_for_completed_ridge20'] = True
    night['integration_decisions']['ridge_main_effects'] = 'B20 point improves vsB19/B14; B14 interval crosses0,31groupremoval reversesall gains,motor/contentsnewbusiness harms. No promotion or complexity added.'
    night['open_conditions'].append({'id': 'RIDGE-SEARCH-INFLUENCE-SEGMENTS', 'status': 'open',
                                     'effect': 'Conditional exploratory gains; adaptive search,groupinfluence,segment harms and unstablecoverage direction remain. No finalroster or2024opening.'})
    for p in before:
        assert p.read_bytes() == before[p], 'Actualización concurrente: '+str(p)
    for p, obj in [(counterpath, counter), (common, index), (nightpath, night)]:
        assert p.read_bytes() == before[p]
        dump(p, obj)
    dump(REPO/'registro/semana2_glm_ridge_actual.json', index)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'
    raw = state.read_text(encoding='utf-8-sig')
    key = 'semana2_glm_ridge_coberturas2023_20261024'
    assert key not in json.loads(raw)
    entry = {'utc': now, 'author': 'Codex', 'path_base': 'workspace_root', 'index': 'Hackaton/Repositorio_IAA2026/registro/semana2_glm_ridge_actual.json',
             'status': index['status'], 'new_fits': 15, 'own_cumulative_price_fits': 195,
             'constants_unchanged': 285, 'reference': 'W2-B00', 'promotion': False, 'confirmation_2024_open': False}
    raw = raw.replace('{', '{\n  '+json.dumps(key)+': '+json.dumps(entry, ensure_ascii=False)+',', 1)
    raw = re.sub(r'(?m)^  "memory_as_of": "[^"]+",', '  "memory_as_of": '+json.dumps(now)+',', raw, count=1)
    state.write_text(raw, encoding='utf-8')
    routespath = ROOT/'RUTAS_PROYECTO.json'
    routes = read(routespath)
    routes.update(week_2_ridge_index='Hackaton/Repositorio_IAA2026/registro/semana2_glm_ridge_actual.json',
                  week_2_development_v8_snapshot=rel(parent_snapshot), week_2_development_report=rel(docpath),
                  week_2_development_plan=index['plan'], week_2_development_oof=index['oof'])
    dump(routespath, routes)
    note = '\n\n## S2-GLM-RIDGE-COBERTURAS2023-v1-20261024: modelo estándar y validación local\n\nCodex, UTC '+now+'. Por instrucción directa del participante se continuó con un modelo estándar mientras Kaggle revisa la incidencia. Se concilió B19 ya terminado por la continuidad, sin repetir sus quince ajustes. La receta B20 quedó registrada en COD-S2-20261024-B20-PRE antes del fit: mismos siete efectos, T0, C0, capital y folds de 2023; alpha de cero a uno para todos los coeficientes, con intercepto libre. Alpha uno procede de la primera tanda, sin buscar intensidades. El indicio previo era mejora en ajuste y pérdida OOF de B19; no prueba causal de sobreajuste.\n\nB20 obtiene D² 0,08938179, frente a 0,08246970 de B19, 0,08671008 de B14 y 0,06858169 de B00, sobre 50.094 filas. La diferencia frente a B14 es +0,00267171, intervalo exploratorio sin ajuste [−0,00367289; +0,00868343]. La mejora frente a B19 tiene intervalo positivo, pero todos los contrastes se invierten al retirar sus 31 grupos favorables. Autos nuevos y contenidos nuevos empeoran frente a B14. No se promueve, retira una alternativa o congela lista final. Se conservan B00 y B01–B20. La norma de coeficientes se contrae en los quince ajustes, pero la dirección de cobertura en edificios sigue cambiando entre folds; no se atribuye causalidad a cobertura.\n\nPasaron 542 comprobaciones separadas con fit bloqueado y 48 adversos focales, con solapamiento. Tres comandos nativos rechazan repetición, código o fuente cambiados antes de fit; no hubo ajustes adicionales. Se verificaron replay, transformaciones de ajuste, objetivo penalizado, KKT, derivada numérica, métricas y tres parejas nuevas mediante multiplicidades. Quince GLM nuevos: contador propio 195 ajustes de precio y 285 constantes; linaje principal 120/60, auxiliares y curvas por separado. Modelos, OOF y diarios en privado/semana2/desarrollo2023/ridge20_20261024_v1 del repositorio común; informe docs/archivo/semana2/GLM_RIDGE_COBERTURAS_2023.md e índice registro/semana2_glm_ridge_actual.json.\n\n2024/test y ledger cerrados para este trabajo; exposición previa de un título de confirmación declarada, sin uso ni afirmación de ceguera completa. Sin envío, remoto, delegación o mensajes externos. Continúan los límites de último, reservas, capital y reporte; revisión técnica propia, no profesional independiente. La siguiente unidad atribuye ganancias a grupos/segmentos con artefactos guardados, sin más ajustes, alpha, variables o complejidad. Ventana nocturna y seguimiento de Kaggle conservados; décima unidad, balance todavía parcial.\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        with (ROOT/'Preparación'/name).open('a', encoding='utf-8', newline='') as f:
            f.write(note)
    with (REPO/'docs/archivo/semana2/PLAN_NOCTURNO_20261023.md').open('a', encoding='utf-8', newline='') as f:
        f.write('\n\n## Décima unidad: ridge estándar sin nuevas variables\n\nEl [ensayo B20](GLM_RIDGE_COBERTURAS_2023.md) mantiene los siete efectos de B19 y añade contracción fija, sin buscar alpha. Mejora el punto global pero no acredita reemplazo de la referencia: incertidumbre frente a B14, inversión bajo influencia y deterioro en dos segmentos nuevos. B00 y B01–B20 conservados, 542 comprobaciones y 48 adversos sin más ajustes. Contador propio 195/285; catálogo 120/60. La siguiente unidad atribuye grupos y segmentos usando artefactos guardados, sin complejizar. 2024/test cerrados y exposición previa declarada; ventana y seguimiento de Kaggle intactos.\n')
    body = 'Resultado de COD-S2-20261024-B20-PRE; receta S2-GLM-RIDGE-COBERTURAS2023-v1-20261024. Se reutilizó B19 terminado por la continuidad, sin repetir su ajuste. B20: quince GLM ridge estándar, mismas siete variables por ramo, alpha uno fijo, intercepto libre, sin interacciones o nueva selección de variables. Mismos T0/C0 y cinco folds de 2023.\n\nD² global: B20 0,08938179; B19 0,08246970; B14 0,08671008; B00 0,06858169. B20/B14 +0,00267171, intervalo exploratorio [−0,00367289; +0,00868343]; B20/B19 +0,00691209 [ +0,00141971; +0,01351104 ]. Tres parejas nuevas, 2.000 sorteos pareados, sin repetir las antiguas. Los tres contrastes invierten signo con sus 31 grupos favorables; no se borra o reentrena ningún grupo. Autos nuevos y contenidos nuevos empeoran frente a B14; B20 conserva D² negativo en autos nuevos. No promoción, retiro o lista final. B00 y B01–B20 preservados exactamente.\n\nPasaron 542 comprobaciones separadas y 48 adversos, con solapamiento. Replay nativo/manual con fit bloqueado, medianas/escalas/categorías de ajuste, objetivo general penalizado, KKT y derivada numérica, métricas sklearn y bootstrap por multiplicidades. Coeficientes se contraen en quince ajustes; cobertura de edificios sigue con razón a ambos lados de uno, sin estabilidad de dirección o causalidad probadas. Tres comandos nativos rechazan repetición, código o fuente cambiados antes de fit. Cero entrenamiento adicional de comprobación.\n\nFuentes, configuración y diario de siete decisiones: privado/semana2/desarrollo2023/ridge20_20261024_v1, en repositorio común. Informe docs/archivo/semana2/GLM_RIDGE_COBERTURAS_2023.md; índice registro/semana2_glm_ridge_actual.json y principal conciliado; snapshot v8 conservado. Contador propio 180 a 195 ajustes de precio, 285 constantes sin cambio; linaje principal 120/60, auxiliares/curvas separados. Próximo: atribuir grupos/segmentos con artefactos guardados, sin más alpha, variables, ajustes o complejidad.\n\n2024/test/ledger cerrados; exposición previa del título de confirmación declarada, sin usar resultados externos o afirmar ceguera completa. Sin envíos, remoto, delegación o mensajes externos. Condiciones de último/capital/reservas/reporte abiertas. Revisión propia, no validación profesional independiente. Ventana y automatización nocturnas existentes conservadas; décima unidad, balance parcial.\n'
    (REPO/'registro/COD-S2-20261024-B20-RESULT_cuerpo.md').write_text(body, encoding='utf-8')
    dump(run/'integration_receipt.json', {'utc': now, 'parent_main_index_sha256': sha(parent_snapshot),
         'new_main_index_sha256': sha(common), 'counter_before_sha256': sha(run/'counter_before_integration.json'),
         'counter_after_sha256': sha(counterpath), 'new_fits': 15, 'own_total_fits': 195, 'own_constants': 285,
         'historical_runs_rewritten': False, 'professional_independent_validation': False})
    print(json.dumps({'document': rel(docpath), 'index': index['id'], 'new_fits': 15, 'own_fits': 195,
                      'verification_passed': verification['passed'], 'adversaries_passed': fixtures['passed']}))


if __name__ == '__main__':
    main()
