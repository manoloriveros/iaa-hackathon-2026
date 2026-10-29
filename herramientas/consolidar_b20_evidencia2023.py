"""Síntesis documental B20: solo JSON/Markdown guardados; no importa modelos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
ID = 'S2-B20-SINTESIS2023-v1-20261024'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_sintesis_20261024_v1'
PLAN = REPO / 'registro/semana2_b20_sintesis_plan_v1.json'
DOC = REPO / 'docs/archivo/semana2/SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md'
INDEX = REPO / 'registro/semana2_b20_sintesis_actual.json'
PRE = 'COD-S2-20261024-B20-SYNTH-PRE'
RESULT = 'COD-S2-20261024-B20-SYNTH-RESULT'


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(p):
    return p.relative_to(ROOT).as_posix()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def dump(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def es(x, n=3):
    return f'{x:.{n}f}'.replace('.', ',')


def evidence(p):
    return {'path': rel(p), 'sha256': sha(p)}


def prepare():
    assert not PLAN.exists() and not RUN.exists() and not INDEX.exists()
    sources = {}

    def add(p, expected=None):
        p = p.resolve(strict=True)
        assert p.is_relative_to(ROOT) and p.suffix in ('.json', '.md')
        assert '2024' not in rel(p).lower() and 'test' not in rel(p).lower()
        digest = sha(p)
        if expected:
            assert digest == expected, f'Fuente cambiada: {rel(p)}'
        sources[rel(p)] = digest

    indices = {}
    for label, filename in [('ridge', 'semana2_glm_ridge_actual.json'),
                            ('attribution', 'semana2_b20_atribucion_actual.json'),
                            ('contraction', 'semana2_b20_contraccion_actual.json'),
                            ('calibration', 'semana2_b20_bandas_calibracion_actual.json')]:
        path = REPO / 'registro' / filename
        add(path)
        d = read(path)
        indices[label] = rel(path)
        add(ROOT / d['documentation'], d.get('documentation_sha256'))
        add(ROOT / d['plan'], d.get('plan_sha256'))
        for key in ['report', 'verification', 'fixtures', 'decision_journal', 'manifest',
                    'readout', 'assessment', 'readout_reconciliation', 'focused_interpretation_receipt']:
            if key not in d:
                continue
            item = d[key]
            if isinstance(item, str):
                add(ROOT / item, d.get(key + '_sha256'))
            else:
                add(ROOT / item['path'], item['sha256'])
        if label != 'ridge':
            add(ROOT / d['run'] / 'closure_verification.json')
    for path in [REPO / 'registro/semana2_contadores_propios_actual.json',
                 REPO / 'registro/semana2_desarrollo2023_actual.json',
                 REPO / 'registro/semana2_politica_seleccion_v1.json',
                 REPO / 'docs/semana2/PROTOCOLO_SELECCION.md',
                 ROOT / 'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md']:
        add(path)
    RUN.mkdir()
    (RUN / 'sources').mkdir()
    frozen = []
    for number, (path, digest) in enumerate(sources.items()):
        src = ROOT / path
        dst = RUN / 'sources' / f'{number:02d}_{src.name}'
        dst.write_bytes(src.read_bytes())
        assert sha(dst) == digest
        frozen.append({'path': path, 'sha256': digest, 'snapshot': rel(dst)})
    plan = {'id': ID, 'author': 'Codex', 'utc': now(), 'path_base': 'workspace_root',
            'purpose': 'Consolidar atribución, contracción y bandas B20 existentes y delimitar evidencia pendiente.',
            'scope': '2023 saved aggregate JSON/Markdown only; no OOF/model/raw-data file reads.',
            'indices': indices, 'frozen_sources': frozen,
            'method': 'Conciliar SHA/recibos finales y magnitudes compartidas; ninguna nueva estimación o remuestreo.',
            'acceptance': ['SHA de fuentes y snapshots exactos', 'Recibos finales sin fallos',
                           'Coherencia de costes, poblaciones y ganancias entre diagnósticos',
                           'Separar validez técnica, diagnóstico descriptivo y promoción predictiva',
                           'Preservar B00, alternativas, contadores y unidad concurrente'],
            'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0, 'new_recipes': 0,
            '2024_test_closed': True, 'ledger_read': False,
            'prior_external2024_header_exposure_disclosed': True,
            'complete_blindness_claim_allowed': False, 'professional_independent_validation': False,
            'forum_prior': PRE, 'forum_result': RESULT,
            'no_next_model_authorized_or_selected': True}
    dump(PLAN, plan)
    dump(RUN / 'plan_snapshot.json', plan)
    nightpath = REPO / 'registro/semana2_continuidad_nocturna.json'
    n = read(nightpath)
    unit = {'id': ID, 'plan': rel(PLAN), 'status': 'preregistered_documentary_consolidation', 'forum_prior': PRE}
    if n.get('current_unit'):
        n.setdefault('parallel_artifact_diagnostics', {})[ID] = unit
    else:
        n['current_unit'] = unit
    n['updated_utc'] = now()
    dump(nightpath, n)
    (REPO / 'registro' / (PRE + '_cuerpo.md')).write_text(
        'Encargo humano: consolidar atribución, contracción y calibración B20 y explicar qué falta para el siguiente paso. '
        'Plan ' + ID + ' congelado antes de la síntesis. Solo JSON/Markdown agregados guardados, con snapshots y SHA; '
        'no se abren OOF, modelos, originales, 2024, test, actas, scores, SEL01 o ledger. '
        'Se cotejan los recibos finales y las magnitudes compartidas; no se repiten suites, replay, bootstrap o ajustes. '
        'Se registrarán límites, decisiones y condiciones para una propuesta posterior sin elegir ni autorizar otra receta. '
        'B00 y B01–B20 conservados, contador intacto y unidad concurrente respetada. '
        'La exposición previa de un título externo queda declarada sin usar sus cifras o afirmar ceguera completa. '
        'Revisión propia de Codex.\n', encoding='utf-8')
    print(json.dumps({'id': ID, 'sources': len(frozen), 'plan': rel(PLAN), 'new_fits': 0}))


def build():
    assert not (RUN / 'report.json').exists() and not DOC.exists()
    p = read(PLAN)
    for item in p['frozen_sources']:
        assert sha(ROOT / item['path']) == sha(ROOT / item['snapshot']) == item['sha256']
    frozen = {x['path']: ROOT / x['snapshot'] for x in p['frozen_sources']}
    load = lambda path: read(frozen[path])
    idx = {key: load(path) for key, path in p['indices'].items()}
    pointer = lambda item: load(item['path'] if isinstance(item, dict) else item)
    a, c, b, ridge = (idx[x] for x in ['attribution', 'contraction', 'calibration', 'ridge'])
    cr, br, cal = pointer(c['readout']), pointer(b['readout']), pointer(b['report'])
    comparisons = [{**x, 'attribution': next(y for y in a['summary'] if y['reference'] == x['reference'])}
                   for x in ridge['pairs']]
    decisions = [
        {'id': 'SYN-01', 'decision': 'B20 sigue como alternativa; B00 conserva referencia y se preserva B01–B20.',
         'basis': 'Ventaja OOF adaptativa y sensible a grupos; los recibos técnicos no constituyen promoción.'},
        {'id': 'SYN-02', 'decision': 'No retirar grupos, capar costes o volver a elegir subconjuntos.',
         'basis': 'Los 31 favorables son distintos por comparación y se eligen con resultados observados.'},
        {'id': 'SYN-03', 'decision': 'Describir contracción conjunta, sin prometer contracción de cada efecto.',
         'basis': '15 normas menores; 14 pares con alguna coordenada creciente, 33 excepciones.'},
        {'id': 'SYN-04', 'decision': 'No atribuir la ganancia a cobertura de forma causal ni al nivel agregado.',
         'basis': 'Cambian intercepto y todos los bloques; los mismos términos de cobertura tienen totales opuestos.'},
        {'id': 'SYN-05', 'decision': 'No adoptar factores por banda, normalización, isotónica o enrutamiento.',
         'basis': 'Bandas comparables muestran heterogeneidad, concentración y soporte escaso; faltan validación y estabilidad.'},
        {'id': 'SYN-06', 'decision': 'No buscar otro alpha ni añadir interacciones, árboles u otra capacidad.',
         'basis': 'No hay mecanismo residual estable identificado que requiera mayor capacidad.'},
        {'id': 'SYN-07', 'decision': 'No repetir suites, inferencias, bootstrap o entrenamiento en esta unidad.',
         'basis': 'Se consolidan recibos finales ya guardados con SHA, sin nueva evidencia de muestreo.'},
        {'id': 'SYN-08', 'decision': 'Mantener 2024/test/ledger cerrados y declarar exposición externa previa.',
         'basis': 'Mandato humano vigente; no se comprueba aquí el estado global de otra tanda ni se recupera ceguera.'},
        {'id': 'SYN-09', 'decision': 'El siguiente trabajo justificable es un diseño previo revisable, sin entrenarlo.',
         'basis': 'Primero mecanismo, objetivo y soporte; después una sola modificación estándar, criterios y coste congelados.'}]
    gaps = [
        {'id': 'G1', 'question': '¿Qué fallo concreto exige un cambio?', 'status': 'not_established',
         'required': 'Hipótesis única sobre un mecanismo residual reproducible, separada de pocos costes altos y de maduración/puente C0. Un A/E extremo aislado no basta.',
         'next_allowed': 'Redactar el diseño y citar los recibos ya existentes; no producir otro diagnóstico por rutina.'},
        {'id': 'G2', 'question': '¿Hay soporte para recalibrar?', 'status': 'insufficient',
         'required': 'Soporte por componentes y positivos, estabilidad predefinida y evaluación fuera de las filas usadas para fijar cualquier corrección. La calibración y sus hiperparámetros deben quedar dentro del aprendizaje validado.',
         'next_allowed': 'Definir antes del ensayo comparador, métrica y regla de aceptación; no inferir cinco factores de los A/E actuales.'},
        {'id': 'G3', 'question': '¿Se justifica más capacidad?', 'status': 'not_justified',
         'required': 'Fallo persistente y material de una opción estándar, mecanismo interpretable y mejora incremental comprobada sin daño relevante ni dependencia extrema de grupos. Complejidad no resuelve falta de información sobre último.',
         'next_allowed': 'Mantener opciones estándar; congelar una sola modificación solo si G1/G2 aportan evidencia suficiente.'},
        {'id': 'G4', 'question': '¿La evidencia predictiva es confirmatoria?', 'status': 'not_from_this_work',
         'required': 'Validación admisible que considere búsqueda adaptativa y el procedimiento completo de aprendizaje. Remuestrear OOF fijas no incorpora refit ni incertidumbre del puente. Más consultas a 2023 no crean una muestra nueva.',
         'next_allowed': 'Explicar el límite; no abrir 2024/test o repetir bootstrap. Estado/autorizaciones de confirmación requieren conciliación separada sin consultar resultados aquí.'},
        {'id': 'G5', 'question': '¿Cumple promoción y límites de riesgo?', 'status': 'not_evaluated_here',
         'required': 'Acta y recibos de política común: mejora útil, intervalo simultáneo, escenarios, nueva población, segmentos, influencia y bloqueos resueltos con evidencia. No basta declarar una limitación aceptada.',
         'next_allowed': 'Conservar B00 y todas las alternativas; no fijar roster ni retirar candidatos.'},
        {'id': 'G6', 'question': '¿Está sustentado el objetivo actuarial?', 'status': 'conditional',
         'required': 'Evidencia aplicable de último, reservas/reaperturas, retrasos, capital, semántica contractual y ancla de nivel; revisión humana competente registrada para el uso previsto. Un corte de siniestros o A/E T0/C0 no lo certifica.',
         'next_allowed': 'Mantener condiciones abiertas y delimitar uso. La revisión propia de Codex no es revisión profesional independiente.'}]
    report = {'id': ID, 'author': 'Codex', 'utc': now(), 'source_indices': p['indices'],
              'source_count': len(frozen), 'source_plan_sha256': sha(PLAN),
              'comparisons': comparisons, 'contraction_readout': cr, 'calibration_readout': br,
              'rows': cal['heldout_rows'], 'groups': cal['groups'],
              'observed_total': cal['total_observed'], 'expected_B20': cal['total_expected_B20'],
              'expected_B19': cal['total_expected_B19'],
              'decisions': decisions, 'evidence_gaps': gaps,
              'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0, 'new_recipes': 0,
              '2024_test_closed': True, 'ledger_read': False, 'promotion': False,
              'reference': 'W2-B00', 'alternatives_preserved': True,
              'prior_external2024_header_exposure_disclosed': True,
              'complete_blindness_claim_allowed': False, 'professional_independent_validation': False,
              'later_concurrent_diagnostics_included': False}
    dump(RUN / 'report.json', report)
    dump(RUN / 'decision_journal.json', {'id': ID, 'utc': now(), 'author': 'Codex', 'decisions': decisions})
    dump(RUN / 'evidence_gaps.json', {'id': ID, 'gaps': gaps, 'no_new_training_authorized': True})
    lines = ['# B20: síntesis de atribución, contracción y calibración', '',
             'B20 queda como alternativa estándar. Su regularización reduce la norma conjunta de los coeficientes y mejora el D² OOF agregado, pero la ventaja se invierte al retirar unos pocos grupos favorables. Las bandas muestran diferencias de calibración con soporte desigual. Esta evidencia explica el comportamiento; todavía no justifica recalibrar, promover B20 o añadir capacidad.', '',
             'Codex, corte documental UTC ' + report['utc'] + '. Se reúnen tres diagnósticos terminados de 2023 y el recibo original de B20. Solo se leen JSON y Markdown agregados guardados: cero entrenamiento, inferencia, remuestreo o lectura de OOF, modelos y originales. La unidad concurrente de incendio/AD queda fuera de este corte y se conserva sin alterar.', '',
             '## Evidencia que comparten los diagnósticos', '',
             'B20 conserva los siete efectos principales, transformaciones, folds por cliente/domicilio y objetivo T0/puente C0 de B19; cambia la penalización ridge de alpha 0 a 1 con intercepto libre. La comparación usa 50.094 periodos OOF y 30.869 componentes. El objetivo evaluado es coste observado: μ = C0 × tasa anual; sus totales no certifican coste último de 2025. El conteo propio acumulado sigue en 195 ajustes de precio y 285 constantes; esta síntesis añade cero.', '',
             '| Comparación B20 frente a | ΔD² completo | IC 95% exploratorio guardado | ΔD² sin sus 31 grupos más favorables |',
             '| --- | ---: | ---: | ---: |']
    for x in comparisons:
        lines.append(f"| {x['reference'].replace('W2-', '')} | {es(x['delta_D2'],6)} | [{es(x['exploratory_lower95'],6)}; {es(x['exploratory_upper95'],6)}] | {es(x['delta_after_removal'],6)} |")
    lines += ['', 'Son intervalos condicionales a predicciones y ajustes ya realizados, procedentes de investigación adaptativa en 2023. No incorporan volver a estimar el modelo o el puente y no equivalen al intervalo simultáneo del protocolo de promoción. No se vuelven a calcular.', '',
              '## Por qué se invierte la ventaja', '',
              'La ganancia aditiva es devianza de la referencia menos devianza de B20. Frente a B14, el total es +14.803,66: sus 31 componentes más favorables aportan +48.637,02 y los restantes −33.833,36. Son 62 periodos, 31 positivos y el 10,93% del coste observado, aunque solo representan el 0,10% de los componentes. La ganancia de esos 31 supera la ganancia neta porque compensa pérdidas en otras filas.', '',
              'Al excluirlos, el numerador pasa a negativo. El nuevo denominador nulo modifica la magnitud, pero al ser positivo no causa el cambio de signo. Aun manteniendo el denominador completo, la contribución restante frente a B14 es −0,006106 de D²; al recalcularlo queda −0,006513. Frente a B19 y B00 ocurre el mismo mecanismo con listas favorables diferentes. Estas listas se eligieron con resultados observados: describen sensibilidad, no una regla para depurar datos o identificar una población estable.', '',
              'La pérdida remanente frente a B14 se extiende por varios segmentos, especialmente renovación de edificios y autos nuevos, mientras renovación de contenidos conserva ganancia. No significa que todos los grupos restantes empeoren: hay ganancias y pérdidas compensadas. Los 12 grupos/20 periodos fijados en el análisis anterior de B19 tampoco son una muestra representativa ni coinciden con cada lista de 31.', '',
              '## Qué cambia la contracción', '',
              f"Las 15 parejas de ajustes reducen la norma L2 estandarizada entre {es(100*cr['joint_norm_reduction_range'][0],1)}% y {es(100*cr['joint_norm_reduction_range'][1],1)}%. En {cr['pairs_with_growing_coordinates']} de ellas aumenta al menos una coordenada en valor absoluto: hay {cr['growing_coordinates_across_pairs']} excepciones. La penalización contrae el conjunto; no garantiza que cada coeficiente o precio se acerque a cero o a una referencia comercial. La interpretación depende de codificación, centrado y categorías de referencia comunes.", '',
              'El total esperado observado baja de 15.436.941,83 a 15.126.408,70 CU (2,01%). En los 12 grupos fijados baja 1,64%, mientras los cinco autos nuevos adversos aumentan 12,10%. El nivel global no explica por sí solo qué filas mejoran.', '',
              '| Caso ya fijado | Coste T0 observado, CU | μ B19 → B20, CU | Ganancia de devianza B20 |',
              '| --- | ---: | ---: | ---: |']
    case_names = ['Autos nuevos, lesión corporal', 'Edificios, incendio OOF más adverso', 'Edificios, incendio influyente sobre AD']
    for label, x in zip(case_names, cr['cases_no_private_ids']):
        lines.append(f"| {label} | {es(x['T0_CU'],2)} | {es(x['B19_expected_period_CU'],2)} → {es(x['B20_expected_period_CU'],2)} | {es(x['saved_deviance_gain_B20'],2)} |")
    lines += ['', 'Los dos incendios comparten el mismo cambio de cobertura en log-tasa (+0,004636), pero el cambio total es +0,374102 y −0,017907. Los otros efectos explican la diferencia; no es un efecto causal aislado de la cobertura AD. La esperanza de coste del periodo tampoco tiene que igualar la severidad realizada de un siniestro.', '',
              'Los 20 periodos fijados aportan +14.620,81 de los +38.299,18 globales frente a B19 (38,2% de ganancia neta). Un incendio aporta +13.724,81 y el otro −557,25. Este cotejo coincide con atribución y muestra compensación en una selección previa; no aporta una segunda validación independiente.', '',
              '## Qué revela la calibración', '',
              'A/E es suma observada dividida por suma esperada. El global B20 de 1,0113 y el B19 de 0,9909 ocultan diferencias entre riesgos. Los quintiles de tasa anual se fijaron exclusivamente en las filas de ajuste de cada ramo/fold. B19 se evalúa sobre las mismas bandas y filas de B20. Las bandas son posiciones relativas dentro de cada ajuste, no cinco umbrales monetarios universales.', '',
              '| A/E B20, de menor a mayor tasa | Banda 1 | Banda 2 | Banda 3 | Banda 4 | Banda 5 |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for line, label in [('motor', 'Autos'), ('buildings', 'Edificios'), ('contents', 'Contenidos')]:
        vals = [x['B20_AE'] for x in br['rows'] if x['line'] == line]
        lines.append('| ' + label + ' | ' + ' | '.join(es(x) for x in vals) + ' |')
    lines += ['', 'Varios extremos se acercan a uno frente a B19, pero otras bandas empeoran. En edificios, banda 1 tiene 69 periodos positivos y un componente reúne 31,65% del coste; su A/E varía entre 0,342 y 3,457 según fold. La banda 5 tiene 124 positivos y A/E 0,714. Los folds comparten entrenamiento: sus rangos no son intervalos de confianza ni cinco réplicas independientes.', '',
              'En autos nuevos la banda 1 está vacía; la 2 tiene 13 periodos y dos positivos (A/E 11,991); la 3, 104 y seis (A/E 6,786), con 93,91% del coste en un componente. No se redibujan bandas para llenar celdas. El quintil más alto concentra 2.145 periodos, 232 positivos y A/E 0,823. El número de positivos cuenta periodos, no siniestros.', '',
              'El replay guardado de ajuste tiene 200.376 apariciones de 50.094 periodos, no nuevas observaciones independientes. Un intercepto Tweedie libre satisface un score ponderado, no fuerza igualdad de sumas observada/esperada. Por eso A/E de ajuste distinto de uno no exige normalización automática. Cuatro tasas OOF fuera del rango de ajuste permanecen señaladas, sin recorte.', '',
              '## Qué falta y qué decisión permite', '',
              '| Pregunta pendiente | Evidencia necesaria | Consecuencia actual |',
              '| --- | --- | --- |',
              '| Fallo residual concreto | Mecanismo material y reproducible que se distinga de concentración de costes, soporte o maduración | No añadir una receta para perseguir un A/E extremo |',
              '| Recalibración | Soporte y estabilidad; corrección aprendida dentro de ajuste y evaluada fuera de sus filas de estimación, con comparador y criterio previos | No factores por banda, isotónica o normalización |',
              '| Complejidad adicional | Mejora incremental verificable de una modificación mínima que resuelva el mecanismo y conserve límites de riesgo | Mantener modelos estándar; no interacciones, árboles o routing por ahora |',
              '| Confirmación predictiva | Evidencia admisible que trate búsqueda adaptativa e incertidumbre del aprendizaje completo; conciliación separada del estado y autorizaciones comunes | Más remuestreo de las mismas OOF no cierra la carencia; 2024/test siguen cerrados aquí |',
              '| Promoción | Acta y recibos aplicables de la política común, además de advertencias resueltas con evidencia | B00 conserva referencia, todas las alternativas permanecen |',
              '| Uso actuarial | Sustento de último, reservas/reaperturas, retrasos, capital, semántica y ancla de nivel; revisión humana competente registrada | Mantener el alcance condicional, sin certificar suficiencia de primas |', '',
              'La política común ya fija ΔD² mínimo útil de 0,0005, límite inferior del intervalo simultáneo de 99,1667% estrictamente superior a ese margen, salvaguardas para población nueva, escenarios de reservas/cola y veto por segmentos. También exige influencia admisible y explicar variaciones nominales por ramo superiores al 5%. Aquí no se ejecuta esa evaluación ni se cambia ningún umbral. Los intervalos y cortes diagnósticos de 2023 no la sustituyen.', '',
              'El siguiente paso defendible consiste en un diseño previo revisable: una hipótesis residual concreta, una sola modificación estándar, fuentes y disponibilidad temporal, separación de ajuste/evaluación, comparador, métricas, salvaguardas, criterio de parada y coste. Aún falta evidencia suficiente para escoger esa modificación. No queda autorizado ni seleccionado un B21, otro alpha o un calibrador. Si el mecanismo procede del objetivo o de información de último insuficiente, la respuesta es resolver esa carencia antes de aumentar capacidad.', '',
              '2024 y test permanecen cerrados en este trabajo. Se conserva declarada la exposición previa a métricas en un título de otro chat, sin reproducirlas o usarlas; no se afirma ceguera completa. Esta síntesis no consulta la apertura global, actas, scores o ledger, ni presupone válida o inválida la autorización ajena. Una eventual conciliación de alcance requiere una actuación separada; no crea otra tanda ni restaura un holdout intacto.', '',
              '## Recibos y decisiones registradas', '',
              '| Diagnóstico | Recibo final consultado | Alcance |',
              '| --- | --- | --- |',
              '| Atribución | 1.014 comprobaciones, 16 adversos; cierre 20/0 | Ganancias por grupos/segmentos y descomposición de log-tasa |',
              '| Contracción | 690 comprobaciones; cierre 227/0 | 15 parejas de coeficientes y replay focal de 20 periodos ya fijados |',
              '| Bandas | 2.121 comprobaciones, 21 adversos; cierre 21/0 | Cortes solo de ajuste, mismas filas B20/B19 y soporte |', '',
              'Se consultan esos recibos guardados, no se repiten sus suites ni se suman como evidencia independiente. Atribución usa el recibo corregido de representación null/NaN; el fallo inicial y la enmienda de arranque permanecen archivados. La contracción v1 se sustituyó antes de cálculo por v2. No se borran intentos adversos ni se presentan como éxito inicial.', '',
              'Las decisiones SYN-01 a SYN-09 y las carencias G1 a G6 quedan en JSON, enlazadas a snapshots y SHA. Se aplica Documentación IAA §3 para la ficha de modelo y Gobernanza §2.8 para distinguir comprobación propia de revisión independiente; las consideraciones de propósito, desigualdad entre segmentos y competencia siguen §§3.1, 3.3 y 3.7–3.8. Esta revisión de Codex no constituye revisión profesional independiente.', '',
              '[Atribución](ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md), [contracción](CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md), [calibración](CALIBRACION_B20_BANDAS_AJUSTE_2023.md), [B20 original](GLM_RIDGE_COBERTURAS_2023.md), [política común](../../registro/semana2_politica_seleccion_v1.json), [plan de síntesis](../../registro/semana2_b20_sintesis_plan_v1.json) e [índice](../../registro/semana2_b20_sintesis_actual.json). Los snapshots y recibos de esta consolidación están en `privado/semana2/desarrollo2023/b20_sintesis_20261024_v1`, fuera de Git.']
    DOC.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'document': rel(DOC), 'decisions': len(decisions), 'gaps': len(gaps), 'new_fits': 0}))


if __name__ == '__main__':
    {'prepare': prepare, 'build': build}[sys.argv[1]]()
