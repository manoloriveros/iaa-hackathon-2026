"""Publica la atribución verificada sin modificar modelos, OOF o contadores."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq

read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    run = REPO/'privado/semana2/desarrollo2023/b20_atribucion_20261024_v1a'
    p, r, v, f = [read(run/n) for n in ['plan_snapshot.json', 'report.json', 'verification_corrected.json', 'fixture_checks.json']]
    assert v['failed'] == f['failed'] == 0
    assert not (run/'decision_journal.json').exists(), 'Cierre ya registrado'
    for item in p['frozen_sources']:
        assert sha(ROOT/item['path']) == item['sha256'], item['path']
    now = datetime.now(timezone.utc).isoformat()
    summary = {x['reference']: x for x in r['summary']}
    seg = pq.read_table(run/'segment_attribution_2023.parquet').to_pandas()
    b14, b19 = summary['W2-B14'], summary['W2-B19']
    decisions = [
        {'id': 'ATTR-SIGN', 'hypothesis': p['hypothesis'], 'criterion': 'Group/row conservation and same original null versus recalculated positive null',
         'result': {'full_gain_B14': b14['all']['gain'], 'selected31_gain_B14': b14['selected31']['gain'], 'remaining_gain_B14': b14['remaining']['gain'],
                    'fixed_null_remaining_delta': b14['remaining']['contribution_full_null'], 'recalculated_null_remaining_delta': b14['remaining']['delta_own_null']},
         'consequence': 'Arithmetic explanation established: selected gain exceeds full net gain; remainder is adverse. Denominator cannot alone reverse sign.'},
        {'id': 'ATTR-CONCENTRATION', 'result': r['summary'],
         'consequence': 'Own31 groups are outcome-selected diagnostic perturbations. Do not delete valid costly claims, optimize k, or call this fresh validation; net share>100% reflects cancellation, not all gains concentrated there.'},
        {'id': 'ATTR-SEGMENTS', 'result': 'Remaining B20/B14 adverse gain is largest in buildings renewal and motornewbusiness; contentsrenewal remainspositive. Remaining B20/B19 mostly loses onzeroT0 rows.',
         'consequence': 'Keep adverse cells. No outcome-dependent price routing or posthoc persegment model choice.'},
        {'id': 'ATTR-COMPARATOR', 'result': read(run/'selection_overlap.json'),
         'consequence': 'Selections depend on reference. Cross-removal signs differ; no universal list of badcomponents.'},
        {'id': 'ATTR-MECHANISM', 'result': {'max_log_identity_error': r['max_log_identity_error'], 'identity': 'delta_lograte=intercept+business+coverage+other fixed-design coefficient contributions'},
         'consequence': 'Exact algebraic shrinkage decomposition, no newprices. Centering/reference coding affects attribution blocks; loss benefit is not causally assigned to coverage.'},
        {'id': 'ATTR-PRIOR12', 'result': {ref: s['fixed_B19_12'] for ref, s in summary.items()},
         'consequence': 'B20 partly improves priorB19 problem slice yet remains adverse versusB14/B00 there. The prior enriched selection is not independent confirmation.'},
        {'id': 'ATTR-VERIFICATION', 'result': {'separate_passed': v['passed'], 'adversaries_passed': f['passed'],
                    'initial_import_failure': p['amendment']['failure_evidence'], 'first_checker_attempt': 'verification.json', 'corrected_checker': 'verification_corrected.json'},
         'consequence': 'First import root fixed before calculation with preregistered amendment; original preserved. Checker None/NaN distinction fixed for undefined zero-target subset D2, no numeric/data changes. Own review, not professional independent validation.'},
        {'id': 'ATTR-MODEL-CONSEQUENCE', 'result': 'No source mismatch or algebraic error in the scored2023 comparisons; observed improvement remains fragile and adaptively investigated.',
         'consequence': 'Keep B00 andB01-B20. No new model,alpha,routing,claim exclusion or added complexity.2024/test/ledger closed; no newfits/bootstrap/submissions.'}
    ]
    dump(run/'decision_journal.json', {'id': p['id'], 'author': 'Codex', 'utc': now, 'decisions': decisions,
         'scope': p['scope'], 'professional_independent_validation': False})
    doc = REPO/'docs/semana2/ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md'
    lines = ['# Por qué se invierte la ventaja de B20 al retirar grupos favorables', '',
        'Codex, corte UTC '+now+'. La ventaja se invierte porque los componentes retirados aportaban más mejora que el saldo neto del portafolio. El resto ya tenía una diferencia agregada de pérdidas desfavorable. La descomposición usa exclusivamente los OOF de 2023 guardados, sin reajustar modelos, generar precios nuevos o repetir remuestreo.', '',
        '## La cuenta que explica el signo', '',
        'Para cada fila se define la ganancia como desviancia de la referencia menos desviancia de B20. Una ganancia positiva favorece a B20. La diferencia de D² es la suma de ganancias dividida por la desviancia nula común, positiva. Por tanto, el signo depende del numerador. Recalcular la nula al retirar filas modifica la magnitud; conservar la nula original mantiene la misma inversión.', '',
        '| Referencia | Ganancia total de desviancia | Ganancia de sus 31 grupos favorables | Ganancia del resto | Delta D² completo | Delta D² del resto |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for ref in ['W2-B19', 'W2-B14', 'W2-B00']:
        s = summary[ref]
        lines.append(f"| {ref} | {s['all']['gain']:,.2f} | {s['selected31']['gain']:,.2f} | {s['remaining']['gain']:,.2f} | {s['all']['delta_own_null']:+.6f} | {s['remaining']['delta_own_null']:+.6f} |")
    lines += ['', 'Las primeras tres columnas son diferencias de desviancia, no importes monetarios. Frente a B14: 48.637,02 − 33.833,36 = 14.803,66. Con la nula original, el resto aporta −0,006106; al recalcularla para las filas retenidas queda −0,006513. Ambas cuentas tienen signo negativo.', '',
        f"Los 31 grupos son el {100*31/b14['all']['groups']:.4f}% de los 30.869 componentes. Frente a B14 contienen {b14['selected31']['rows']} periodos, {b14['selected31']['positive_rows']} con T0 positivo, y {b14['selected31']['observed_total']:,.2f} CU de coste observado: {100*b14['selected31']['observed_total']/b14['all']['observed_total']:.2f}% del total. Se retira cada componente completo, con sus filas de coste cero y otros ramos; no solo sus filas convenientes.", '',
        f"Ese conjunto aporta el {100*b14['selected_share_net_gain']:.1f}% de la ganancia neta, pero el {100*b14['selected_share_gross_positive_gain']:.1f}% de las ganancias brutas positivas. El porcentaje neto supera cien porque otros grupos compensan las mejoras con pérdidas. No significa que todos los grupos restantes empeoren: hay {b14['positive_gain_groups']:,} componentes con ganancia positiva y {b14['negative_gain_groups']:,} con ganancia negativa en el contraste completo.", '',
        'La ordenación usa ganancia observada descendente y group_id ascendente para empates. En esa ordenación bastan los tres primeros grupos para invertir B20/B14; frente a B19 son diez y frente a B00 trece. Son prefijos descriptivos calculados con los mismos resultados que se diagnostican. No se adopta un tamaño de recorte, no se borran registros y no se trata al resto como una nueva muestra de validación.', '',
        '## Qué segmentos sostienen o pierden la ganancia', '',
        'La siguiente tabla usa siempre la nula global original. Sus aportaciones sí se suman para obtener el cambio global, a diferencia de los D² de cada segmento.', '',
        '| Segmento, B20 frente a B14 | Aportación antes de retirar | Aportación del resto |', '| --- | ---: | ---: |']
    for label in ['buildings_new_business', 'buildings_renewal', 'contents_new_business', 'contents_renewal', 'motor_new_business', 'motor_renewal']:
        q = seg[seg.reference.eq('W2-B14') & seg.dimension.eq('line_business') & seg.label.eq(label)]
        before = q[q.cohort.eq('all')].iloc[0]
        after = q[q.cohort.eq('remaining')].iloc[0]
        lines.append(f"| {label} | {before.contribution_full_null:+.6f} | {after.contribution_full_null:+.6f} |")
    lines += ['', 'En el resto frente a B14, renovación de edificios pierde 25.890,09 unidades de desviancia y autos nuevos pierde 7.894,23. Contenidos en renovación conserva una ganancia de 3.134,90. La inversión global no equivale a un deterioro uniforme de todas las filas o segmentos.', '',
        'Separando por resultado observado, frente a B14 el resto pierde 28.198,55 en periodos con T0 positivo y 5.634,81 en periodos sin coste. Frente a B19 la composición es distinta: pierde 2.039,30 en positivos y 17.771,88 en ceros. La clasificación por T0 es retrospectiva y solo diagnóstica; no está disponible para decidir una tarifa.', '',
        'La desviancia de potencia 1,5 permite separar exactamente la ganancia por fila en `4y(1/√μ_ref − 1/√μ_20)` y `4(√μ_ref − √μ_20)`. En los 31 grupos favorables frente a B14, el primer término aporta +48.924,82 y el segundo −287,80: la parte que escala con el coste observado domina esa mejora. En el resto ambos términos agregados son adversos. No son componentes causales del riesgo ni medidas de suficiencia.', '',
        '## Los grupos dependen del comparador', '',
        'Los conjuntos favorables frente a B19 y B14 comparten 21 grupos de 31; con el conjunto frente a B00 comparten cinco y cuatro, respectivamente. Al aplicar el mismo retiro a las otras parejas se obtiene:', '',
        '| Referencia del contraste B20 | Retiro elegido frente a B19 | Retiro elegido frente a B14 | Retiro elegido frente a B00 |', '| --- | ---: | ---: | ---: |']
    cross = read(run/'cross_selection_removal.json')
    for ref in ['W2-B19', 'W2-B14', 'W2-B00']:
        values = [next(x['delta_own_null'] for x in cross if x['reference'] == ref and x['selection_reference'] == selection) for selection in ['W2-B19', 'W2-B14', 'W2-B00']]
        lines.append('| '+ref+' | '+' | '.join(f'{x:+.6f}' for x in values)+' |')
    lines += ['', 'La diagonal reproduce el diagnóstico original. Las otras celdas no son pruebas independientes: comparten filas, modelos y selecciones observadas. Muestran que no existe una lista universal de componentes problemáticos. Retirar los seleccionados frente a B00, por ejemplo, no invierte B20 frente a B19 o B14.', '',
        'La selección fija de doce grupos de la revisión anterior de B19 se conserva sin volver a elegirla. En ella B20 mejora 14.620,81 unidades de desviancia frente a B19, pero pierde 16.127,18 frente a B14. Esto describe una recuperación parcial del problema anterior, sin confirmar superioridad. Es una selección enriquecida por errores e influencia de B19, no una muestra nueva; la trazabilidad previa no autoriza eliminar sus costes.', '',
        '## Qué hizo la contracción', '',
        'Con las mismas matrices de diseño, el cambio de logtasa B20−B19 se descompone exactamente en cambio de intercepto, negocio nuevo, cobertura y los demás efectos. La suma concilia con el logaritmo del cociente de tasas guardadas en las 50.094 filas, con error absoluto máximo de '+f"{r['max_log_identity_error']:.2e}"+'. No se ajustan coeficientes ni se construye otro precio.', '',
        'En los 32 periodos positivos de los grupos favorables frente a B19, el cambio medio de logtasa es aproximadamente +0,305. Sus bloques medios son +0,183 de intercepto, +0,005 de negocio, +0,051 de cobertura y +0,066 de otros efectos. La intervención ridge modifica toda la fórmula; estos bloques dependen del centrado y de las referencias categóricas. No asignan causalmente la ganancia de desviancia a una cobertura ni prueban una mejora futura en siniestros grandes.', '',
        '## Verificación y decisión', '',
        f"Pasaron {v['passed']} comprobaciones separadas y {f['passed']} adversos, con solapamiento. La segunda implementación usa la expresión cuadrática de desviancia, math.fsum y diccionarios para grupos y rankings; verifica pérdidas, perfiles, particiones, nulas, selecciones cruzadas y los bloques logarítmicos con indicadores independientes. Los comandos reales rechazan una fuente cambiada y una repetición de la corrida antes de calcular. Fit permanece bloqueado.", '',
        'El primer arranque del productor resolvió mal la raíz y no encontró la caché de PyArrow: falló antes de main y de leer los OOF. Se preservaron código, plan y fallo; la enmienda v1a corrigió solo la raíz antes del cálculo. El primer comprobador rechazó diez celdas con contraste propio indefinido: Parquet representa como NaN lo que JSON conserva como None cuando la nula es cero. Se corrigió esa lectura, conservando el recibo fallido; no se cambiaron valores del productor, modelos o datos. Los contrastes indefinidos siguen sin convertirse en cero.', '',
        'La decisión es mantener B00 como referencia y conservar B01–B20. La atribución explica fragilidad de la ganancia observada; no identifica un error de origen, no demuestra que B20 sea inferior en toda población y no exige más complejidad. No se busca otro alpha, combina una receta por segmento o elimina un coste válido para mejorar una métrica. Las siguientes comprobaciones pueden revisar calibración con bandas fijadas en ajuste y artefactos existentes, con su propio criterio previo.', '',
        'Cero entrenamientos, nuevas recetas de precio, precios nuevos o bootstrap. El contador se conserva en 195 ajustes de precio y 285 constantes, con auxiliares y curvas separados. 2024, test, actas, scores y ledger permanecen cerrados para este trabajo. Se mantiene declarada la exposición anterior de un título ajeno, sin usar sus cifras o afirmar ceguera completa. Sin envíos, remoto, delegación, publicación externa o cambios a otras automatizaciones. Revisión técnica propia, no profesional independiente.', '',
        '[Plan y enmienda](../../registro/semana2_b20_atribucion_plan_v1a.json), [índice](../../registro/semana2_b20_atribucion_actual.json), [productor](../../src/semana2/atribuir_b20_grupos2023.py), [verificador separado](../../herramientas/verificar_atribucion_b20_2023.py) y [adversos](../../herramientas/probar_atribucion_b20_2023.py). Las tablas por fila/grupo y sus IDs permanecen en `privado/semana2/desarrollo2023/b20_atribucion_20261024_v1a`, fuera de Git. El [ensayo B20](GLM_RIDGE_COBERTURAS_2023.md) conserva sus resultados y límites.']
    doc.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    evidence = lambda name: {'path': rel(run/name), 'sha256': sha(run/name)}
    index = {'id': p['id'], 'author': 'Codex', 'utc': now, 'path_base': 'workspace_root',
             'status': 'attribution_verified_reversal_from_gain_concentration_not_denominator_no_complexity',
             'run': rel(run), 'documentation': rel(doc), 'plan': rel(REPO/'registro/semana2_b20_atribucion_plan_v1a.json'),
             'plan_sha256': r['plan_sha256'], 'report': evidence('report.json'),
             'verification': evidence('verification_corrected.json') | {'passed': v['passed'], 'failed': 0},
             'fixtures': evidence('fixture_checks.json') | {'passed': f['passed'], 'failed': 0},
             'decision_journal': evidence('decision_journal.json'), 'manifest': evidence('manifest.json'),
             'references': ['W2-B19', 'W2-B14', 'W2-B00'], 'summary': r['summary'],
             'new_fits': 0, 'new_price_predictions': 0, 'new_candidate_recipes': 0, 'new_bootstrap': 0,
             'derived_subset_diagnostics': True, 'reference': 'W2-B00', 'promotion': False,
             'all_alternatives_preserved': True, 'scope': p['scope'], 'forum_prior': p['forum_prior'],
             'forum_amendment': p['forum_amendment'], 'forum_result': p['forum_result'],
             'professional_independent_validation': False}
    idx = REPO/'registro/semana2_b20_atribucion_actual.json'
    assert not idx.exists()
    dump(idx, index)
    nightpath = REPO/'registro/semana2_continuidad_nocturna.json'
    n = read(nightpath)
    assert n['current_unit']['id'] == p['id'], 'Unidad concurrente: conciliar sin sobrescribir'
    unit = {'id': p['id'], 'run': rel(run), 'documentation': rel(doc), 'verification': index['verification'],
            'fixtures': index['fixtures'], 'decision_journal': index['decision_journal'],
            'forum_result': p['forum_result'], 'index': rel(idx), 'new_fits': 0, 'new_bootstrap': 0}
    n['completed_units'].append(unit)
    n['current_unit'], n['latest_completed_unit'], n['updated_utc'] = None, unit, now
    n['status'] = 'scheduled_'+str(len(n['completed_units']))+'_units_B20_attribution_verified_limits_open'
    n['next_unit'] = 'If continuing, preregister a saved2023 risk-band calibration diagnostic with bands frozen from training rows, B20/B19 and segment uncertainty; no fit,alpha search,newmodel,2024/test or ledger. Do not repeat completed attribution or bootstrap.'
    n['queue'] = ['Review training-defined calibration bands only with a prior diagnostic plan and saved2023 artifacts.',
                  'Preserve B00/B01-B20 and all concentration,ultimate,reporting/capital conditions; no price changes from selectedoutcome groups.',
                  'Maintain existing Kaggle incident monitor and final honest balance at07:00Bogota, no repeated completed suites.']
    n['latest_b20_attribution_index'] = rel(idx)
    n['no_repetition_for_completed_b20_attribution'] = True
    n['integration_decisions']['B20_attribution'] = 'B14 own31gain48637 exceedsnet14804, remainder−33833. Denominator positivecannotreverse sign; selectedsets reference-dependent. No group deletion,promotion or complexity.'
    n['open_conditions'].append({'id': 'B20-ATTR-OUTCOME-SELECTION', 'status': 'open', 'effect': 'Outcome-selected removals and adaptive2023 research are diagnostic, not freshvalidation or a claim-exclusion rule. No stablepopulation-superiority conclusion.'})
    dump(nightpath, n)
    routepath = ROOT/'RUTAS_PROYECTO.json'
    routes = read(routepath)
    routes.update(week_2_b20_attribution_index=rel(idx), week_2_b20_attribution_report=rel(doc), week_2_b20_attribution_plan=index['plan'])
    dump(routepath, routes)
    statepath = ROOT/'Preparación/ESTADO_PROYECTO.json'
    raw = statepath.read_text(encoding='utf-8-sig')
    key = 'semana2_b20_atribucion2023_20261024'
    assert key not in json.loads(raw)
    raw = raw.replace('{', '{\n  '+json.dumps(key)+': '+json.dumps({'utc': now, 'author': 'Codex', 'path_base': 'workspace_root',
            'index': rel(idx), 'status': index['status'], 'new_fits': 0, 'new_bootstrap': 0, 'reference': 'W2-B00', 'promotion': False,
            '2024_test_closed': True}, ensure_ascii=False)+',', 1)
    statepath.write_text(raw, encoding='utf-8')
    note = '\n\n## S2-B20-ATRIBUCION2023-v1a-20261024: por qué se invierte la ventaja\n\nCodex, UTC '+now+'. Instrucción directa del participante: atribución por grupos/segmentos de B20, 2024/test cerrados y complejidad solo con evidencia. Plan previo y enmienda técnica registrados en B20-ATTR-PRE/AMD; salida privada b20_atribucion_20261024_v1a. Se usan exclusivamente los OOF/modelos guardados de 2023, con fit bloqueado; cero ajustes, precios nuevos, recetas o bootstrap.\n\nFrente a B14, la ganancia total de desviancia es 14.803,66: los 31 grupos más favorables aportan 48.637,02 y el resto −33.833,36. Recalcular la nula cambia la magnitud, no el signo: delta del resto −0,006106 con nula global fija y −0,006513 con nula retenida. El 0,1004% de componentes reúne 62 periodos, 31 positivos y 10,93% del coste T0. El resto conserva grupos favorables y adversos; no todos empeoran. Renovación de edificios y autos nuevos concentran el saldo restante adverso frente a B14; contenidos en renovación mantiene ganancia. Frente a B19, en cambio, gran parte del saldo adverso restante procede de filas cero.\n\nSelecciones por referencia distintas: B19/B14 comparten 21 de sus 31 grupos, B00 comparte cinco/cuatro. Retirar la selección de B00 no invierte B20 frente a B19/B14. Los prefijos adversos mínimos son diez/tres/trece para B19/B14/B00, descriptivos después de ordenar por resultado, no umbrales de selección. La selección previa de 12 grupos B19 mejora con B20 frente a B19, pero sigue adversa frente a B14. No hay una lista universal de errores o permiso para borrar costes válidos. Descomposición exacta de logtasa en bloques, error máximo 2,36e-15, dependiente de codificación/centrado y sin atribución causal de beneficio a cobertura.\n\nPasaron 1.014 verificaciones separadas y 16 adversos, con solapamiento. El primer arranque falló antes de main por raíz de dependencias; se preservó v1 y se enmendó raíz a v1a antes del cálculo. El primer verificador pasó 1.004 y rechazó diez contrastes indefinidos por tratar NaN de Parquet distinto de None de JSON; se preservó ese recibo, se corrigió solo la lectura y pasó la segunda invocación, sin modificar números o productor. No se convierten contrastes sin nula en cero. Conservados fuente/modelos/OOF, contador 195 ajustes y 285 constantes, B00 y B01–B20; no promoción, mezcla por segmento o complejidad nueva.\n\nInforme docs/semana2/ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md e índice registro/semana2_b20_atribucion_actual.json, relativos al repositorio común. Siguiente unidad posible: calibración con bandas definidas en ajuste y artefactos guardados, receta previa, sin fit/alpha/modelo. Selección por resultado y búsqueda adaptativa siguen abiertas; revisión propia, no profesional independiente. Exposición previa de título externo declarada sin uso ni ceguera completa; 2024/test/ledger cerrados. Sin envíos, remoto, delegación, mensajes externos o otras automatizaciones. Ventana nocturna y seguimiento de Kaggle conservados; balance parcial.\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        with (ROOT/'Preparación'/name).open('a', encoding='utf-8', newline='') as ff:
            ff.write(note)
    with (REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md').open('a', encoding='utf-8', newline='') as ff:
        ff.write('\n\n## Atribución B20 completada sin más ajustes\n\nLa [atribución por grupos y segmentos](ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md) explica la inversión por el saldo de pérdidas: los grupos retirados aportaban más ganancia que el neto. El denominador positivo no cambia el signo; las selecciones dependen de la referencia. No borrar costes válidos, escoger un modelo por segmento o añadir complejidad. Verificación corregida 1.014/0 y adversos 16/0, con intentos fallidos preservados. Contadores y modelos exactos, 2024/test cerrados y exposición previa declarada. Siguiente diagnóstico posible: bandas de calibración fijadas en ajuste, plan previo y artefactos existentes, sin fit o alpha. Ventana y programación existentes intactas.\n')
    body = 'Resultado de B20-ATTR-PRE/AMD, plan S2-B20-ATRIBUCION2023-v1a-20261024. Se explica aritméticamente la inversión sin fit, precios nuevos, recetas o bootstrap. B20/B14: ganancia de desviancia total +14.803,66 = +48.637,02 en31grupos favorables −33.833,36 en el resto. La diferencia del resto es −0,006106 con nula global original y −0,006513 con nula recalculada: el denominador positivo no puede cambiar signo. Esos31componentes,0,1004% del total, tienen62periodos/31positivos y10,93% de T0; son selección por resultado, no datos descartables o nuevo holdout.\n\nRenovación de edificios y autos nuevos dominan la pérdida restante frente a B14, contenidosrenovación sigue positivo. Frente a B19, el resto pierde sobre todo en filas cero. Las selecciones B19/B14 comparten21/31; conB00 cinco/cuatro. Aplicar la selección B00 a B20/B19 oB14 no invierte esos contrastes: no hay una lista universal de grupos malos. Los prefijos mínimos3/10/13 son diagnósticos posteriores a resultados, no reglas nuevas. Doce grupos previos B19 se conservan fijos; B20 mejora ahí contraB19, sigue adverso contraB14.\n\nIdentidad logtasa=B20/B19 por intercepto/negocio/cobertura/otros, error2,36e-15; asociación de bloques dependiente de codificación, no causalidad de beneficio. Verificador separado con desviancia cuadrática/math.fsum/diccionarios e indicadores manuales:1.014pases/0fallos en segunda invocación;16adversos pasan. Preservados el primer arranque por raíz antes de main y el primer verificador con10rechazos por None/NaN de contraste indefinido, corregidos sin datos o resultados numéricos cambiados. Fuentes y hashes conservados.\n\nInforme docs/semana2/ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md; índice registro/semana2_b20_atribucion_actual.json; corrida privada b20_atribucion_20261024_v1a y diario de ocho decisiones. B00/B01–B20 y contador195/285 exactos. No promoción, eliminación de siniestros, búsqueda de alpha, receta por segmento o complejidad nueva. 2024/test/ledger cerrados, exposición previa de título declarada sin uso. Revisión propia, no profesional independiente. Sin remoto/envíos/delegación/mensajes externos/otras automatizaciones. La cola deja calibración por bandas de ajuste solo con plan previo y artefactos existentes.\n'
    (REPO/'registro/COD-S2-20261024-B20-ATTR-RESULT_cuerpo.md').write_text(body, encoding='utf-8')
    print(json.dumps({'document': rel(doc), 'index': rel(idx), 'passed': v['passed'], 'adversaries': f['passed'], 'night_completed': len(n['completed_units']), 'new_fits': 0}))


if __name__ == '__main__':
    main()
