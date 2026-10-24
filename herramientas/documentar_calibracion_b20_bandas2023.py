"""Documenta calibración diagnóstica y conserva intactos modelos y contadores."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq

read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: __import__('hashlib').sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def es(value, digits=3):
    return f'{value:,.{digits}f}'.replace(',', '#').replace('.', ',').replace('#', '.')


def main():
    run = REPO/'privado/semana2/desarrollo2023/b20_bandas_calibracion_20261024_v1'
    p, r, v, f = [read(run/n) for n in ['plan_snapshot.json', 'report.json', 'verification.json', 'fixture_checks.json']]
    assert v['failed'] == f['failed'] == 0
    assert not (run/'decision_journal.json').exists(), 'Resultado ya documentado'
    for item in p['frozen_sources']:
        assert sha(ROOT/item['path']) == item['sha256'], item['path']
    now = datetime.now(timezone.utc).isoformat()
    cells = pq.read_table(run/'calibration_cells_2023.parquet').to_pandas()
    cuts = read(run/'band_cuts.json')
    table = []
    for line in ['motor', 'buildings', 'contents']:
        for band in range(1, 6):
            a = cells[cells.cohort.eq('heldout') & cells.dimension.eq('line') & cells.model_id.eq('W2-B20') & cells.label.eq(line) & cells.band.eq(band)].iloc[0]
            b = cells[cells.cohort.eq('heldout') & cells.dimension.eq('line') & cells.model_id.eq('W2-B19') & cells.label.eq(line) & cells.band.eq(band)].iloc[0]
            foldcells = cells[cells.cohort.eq('heldout') & cells.dimension.eq('line_fold') & cells.model_id.eq('W2-B20') & cells.label.str.startswith(line+'|') & cells.band.eq(band)]
            table.append({'line': line, 'band': band, 'B20_AE': float(a.actual_over_expected), 'B19_AE': float(b.actual_over_expected),
                          'rows': int(a.rows), 'positive_periods': int(a.positive_rows), 'positive_groups': int(a.positive_groups),
                          'largest_group_cost_share': float(a.largest_group_cost_share),
                          'cost_concentration_equivalent_groups': float(a.cost_concentration_equivalent_groups),
                          'fold_AE_min': float(foldcells.actual_over_expected.min()), 'fold_AE_max': float(foldcells.actual_over_expected.max()),
                          'fold_AE_above1': int(foldcells.actual_over_expected.gt(1).sum()), 'fold_AE_below1': int(foldcells.actual_over_expected.lt(1).sum())})
    dump(run/'readout.json', {'rows': table, 'global_B20_AE': r['global_AE_B20'], 'global_B19_AE': r['global_AE_B19'],
         'max_abs_training_intercept_score': max(abs(x['normalized_intercept_score']) for x in cuts),
         'training_AE_range': [min(x['fit_AE_not_forced_to_one'] for x in cuts), max(x['fit_AE_not_forced_to_one'] for x in cuts)],
         'tie_cut_scopes': sum(x['unique_cuts'] < 4 for x in cuts), 'new_fits': 0})
    decisions = [
        {'id': 'BANDS-SCOPE', 'criterion_before': p['band_definition'], 'result': '15savedB20models replayed only on owntraining2023rows; all15cutsets distinct and heldoutlabels unused. Fivebands retained including empty segmentcells.',
         'consequence': 'No heldoutquantiles, targetcut optimization, exposure-based risk ranking or ID tie splitting.'},
        {'id': 'BANDS-COMPARISON', 'criterion_before': p['comparison'], 'result': 'B20/B19 evaluated on identical50094OOFrows with identicalB20band membership,T0 andC0.',
         'consequence': 'Ratios compare the same population; no claim of superiority from ownmodel-band differences.'},
        {'id': 'BANDS-AGGREGATE', 'result': {'B20_global_AE': r['global_AE_B20'], 'B19_global_AE': r['global_AE_B19'], 'line_band_table': table},
         'consequence': 'Nearunit total A/E does not establish local calibration. Some extremeband discrepancies moderate, other cells worsen; no uniformimprovement or newmodelpromotion.'},
        {'id': 'BANDS-SUPPORT', 'result': 'Lowband buildingcost concentrated; newbusiness motor has0,2,6positiveperiods in first3bands; foldranges straddle1 and overlap bytraining construction.',
         'consequence': 'No bandfactor or detailedrouting from these sparsecells. Concentrationequivalent groupcount is descriptive,not inferential samplesize.'},
        {'id': 'BANDS-OBJECTIVE', 'result': 'Savedtraining normalizedinterceptscore is small, while trainingA/E spans about0.9873..1.0417.',
         'consequence': 'Tweedie intercept optimum does not impose sumobserved=sumexpected. No posthoc normalization toforceone.'},
        {'id': 'BANDS-EXTRAPOLATION', 'result': {'outside_training_rate_range_rows': r['outside_training_range_rows']},
         'consequence': 'Preserve flaggedfourOOFrows; no clipping, removal or changedcuts. Bands are relativeperlinefold,not fixedabsoluteprice brackets.'},
        {'id': 'BANDS-VERIFICATION', 'result': {'separate_passed': v['passed'], 'adversaries_passed': f['passed']},
         'consequence': 'Manualsaved-coefficient rate replay, Python orderstatistics/bisect and fsum/groupdictionary cells corroborated. Guardtarget/ID poison,ties,emptycells and nativebadsource/duplicate commands pass. Ownreview,not independentprofessionalvalidation.'},
        {'id': 'BANDS-NEXT', 'result': 'No fit, newmodel, recalibration, bootstrap or closure of ultimate/reporting/capital limits.',
         'consequence': 'Keep B00/B01-B20 and2024/testclosed. Consolidate existingB20 diagnostics and validationrequirements; no alpha/features/interactions/isotonic/normalization or perband recipe inferred.'}
    ]
    dump(run/'decision_journal.json', {'id': p['id'], 'author': 'Codex', 'utc': now, 'decisions': decisions,
         'scope': p['scope'], 'professional_independent_validation': False})
    doc = REPO/'docs/semana2/CALIBRACION_B20_BANDAS_AJUSTE_2023.md'
    lines = ['# Calibración de B20 en bandas definidas con el ajuste', '',
        'Codex, corte UTC '+now+'. Se revisaron los mismos 50.094 periodos OOF de 2023. El A/E global de B20 es '+es(r['global_AE_B20'])+', pero el equilibrio agregado oculta diferencias por banda. La regularización modera varios extremos de B19 sin producir una mejora uniforme de calibración. No se ha reentrenado, recalibrado o promovido un modelo.', '',
        '## Cómo se fijaron las bandas', '',
        'Se reproduce la tasa anual nominal con cada uno de los quince estimadores B20 guardados, exclusivamente en las filas que lo ajustaron. Para cada ramo y fold se fijan los quintiles 20, 40, 60 y 80 de esa tasa, con la inversa empírica sin interpolación. El objetivo T0 y las etiquetas retenidas no eligen cortes. Las filas OOF se asignan después por su tasa B20 ya guardada.', '',
        'La banda inferior incluye su límite superior; las siguientes son abiertas por abajo y cerradas por arriba. Se conservan cortes repetidos, empates y bandas vacías, sin desempatar por ID ni alterar el número de bandas. En este cálculo los quince conjuntos tienen cuatro cortes distintos. Las bandas representan posición relativa dentro del ajuste de cada ramo/fold; no son intervalos absolutos comunes de precio.', '',
        'B19 se resume sobre las mismas filas y bandas definidas por B20. Así se comparan poblaciones iguales. El A/E es suma de T0 observado dividida por suma de predicción observada con C0, no media de cocientes por póliza ni coste dividido por tasa anual sin exposición. Valores superiores a uno indican más T0 observado que esperado bajo ese vínculo; no prueban insuficiencia de último.', '',
        '## Calibración fuera de muestra', '',
        '| Ramo | Banda 1, menor tasa | Banda 2 | Banda 3 | Banda 4 | Banda 5, mayor tasa |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    labels = {'motor': 'Autos', 'buildings': 'Edificios', 'contents': 'Contenidos'}
    for line in ['motor', 'buildings', 'contents']:
        rows = [x for x in table if x['line'] == line]
        lines.append('| '+labels[line]+' | '+' | '.join(es(x['B20_AE']) for x in rows)+' |')
    lines += ['', 'El global es '+es(r['global_AE_B20'])+' para B20 y '+es(r['global_AE_B19'])+' para B19. Su proximidad a uno no implica que las bandas estén calibradas. En edificios, B19 pasa de A/E 2,232 a 1,966 con B20 en la banda inferior y de 0,644 a 0,714 en la superior: se moderan esos dos extremos. En las bandas intermedias 3 y 4 las desviaciones respecto a uno empeoran. En autos, la banda 5 se acerca de 0,840 a 0,981, mientras la banda 2 se aleja de 0,905 a 0,861.', '',
        'Contenidos mantiene una forma irregular: las bandas 3 y 5 quedan por debajo de uno, y la 4 por encima. Son diagnósticos de forma y nivel sobre 2023 ya usado adaptativamente. No se transforma este perfil en una curva de calibración, prueba de monotonía o justificación de una familia más compleja.', '',
        '## Soporte y concentración del coste', '',
        '| Ramo y banda | Periodos OOF | Periodos con T0 positivo | Mayor componente, % del T0 | Grupos equivalentes por concentración |',
        '| --- | ---: | ---: | ---: | ---: |']
    for line, band in [('buildings', 1), ('buildings', 5), ('contents', 1), ('contents', 5), ('motor', 1), ('motor', 5)]:
        x = next(x for x in table if x['line'] == line and x['band'] == band)
        lines.append(f"| {labels[line]}, {band} | {x['rows']} | {x['positive_periods']} | {es(100*x['largest_group_cost_share'], 2)} | {es(x['cost_concentration_equivalent_groups'], 2)} |")
    lines += ['', 'Los grupos equivalentes se calculan como (suma de coste por grupo)²/suma de costes de grupo². Describen cuánto se concentra el importe; no son tamaño muestral efectivo para un intervalo de confianza. Los conteos de grupos tampoco se suman entre bandas o ramos, pues un componente puede tener varios periodos.', '',
        'En autos nuevos, la banda 1 no contiene filas y su A/E queda indefinido. La banda 2 contiene trece periodos y dos positivos, con A/E 11,991; la banda 3 tiene 104 periodos y seis positivos, con A/E 6,786. Un componente reúne el 93,91% del coste de esta última celda. El grueso del nuevo negocio de autos queda en la banda 5: 2.145 periodos, 232 positivos y A/E 0,823. Las bandas se fijaron por ramo, no se vuelven a dividir dentro de nuevo negocio para llenar celdas.', '',
        'En nuevo negocio de edificios solo hay de seis a nueve periodos positivos por banda; en contenidos, de cuatro a diez. Los extremos observados no proporcionan una base estable para cinco factores comerciales o una regla distinta por banda. No se eliminan siniestros o componentes para suavizarlos.', '',
        '## Variación entre folds y alcance del ajuste', '',
        '| Ramo y banda | A/E mínimo entre folds | A/E máximo | Folds por encima / debajo de uno |', '| --- | ---: | ---: | ---: |']
    for line in ['motor', 'buildings', 'contents']:
        for band in [1, 5]:
            x = next(x for x in table if x['line'] == line and x['band'] == band)
            lines.append(f"| {labels[line]}, {band} | {es(x['fold_AE_min'])} | {es(x['fold_AE_max'])} | {x['fold_AE_above1']} / {x['fold_AE_below1']} |")
    lines += ['', 'Los ajustes comparten cuatro de cinco folds y las tablas comparten componentes; esos rangos no son intervalos de confianza ni cinco réplicas independientes. En edificios, incluso las bandas extremas cambian de lado respecto a uno entre folds. La banda 1 llega a tener un componente con 91,82% del coste dentro de un fold. Se conserva el diagnóstico, sin convertir su punto agrupado en una corrección cierta.', '',
        'Se encontraron cuatro tasas OOF fuera del rango mínimo/máximo de sus filas de ajuste: dos de edificios, una de contenidos y una de autos. Se conservan marcadas; no se recortan las tasas ni cambian los cortes. Pertenecer a una banda extrema no garantiza soporte de entrenamiento para cualquier tasa.', '',
        'El replay de las filas de ajuste suma 200.376 apariciones, porque cada periodo participa en cuatro modelos. Son 50.094 periodos originales, no cuatro muestras nuevas. La calibración de entrenamiento es descriptiva. El máximo score normalizado del intercepto es '+es(max(abs(x['normalized_intercept_score']) for x in cuts), 8)+', y el A/E de ajuste por modelo recorre '+es(min(x['fit_AE_not_forced_to_one'] for x in cuts), 4)+' a '+es(max(x['fit_AE_not_forced_to_one'] for x in cuts), 4)+'. El óptimo del intercepto Tweedie impone una suma ponderada de residuos, no igualdad exacta de sumas observada y esperada. No se normaliza el nivel para forzar uno.', '',
        '## Verificación y decisión', '',
        f"Pasaron {v['passed']} comprobaciones separadas y {f['passed']} adversos, con solapamiento entre controles. La revisión usa un predictor exp(Xβ) con indicadores manuales, estadísticas de orden de Python y bisect para los cortes, y math.fsum/diccionarios para importes, grupos y concentración. Contrasta la partición completa por banda, los originales T0/C0, las mismas filas de ambos modelos y el carácter exclusivo de las filas de ajuste. Las etiquetas e IDs alterados no cambian cortes; empates, celdas vacías y año/test inválidos se tratan según el contrato. Dos comandos nativos rechazan fuente alterada y repetición antes de producir trabajo nuevo. Fit estuvo bloqueado.", '',
        'Se mantiene B00 como referencia y B01–B20 como alternativas. No hay factores por banda, isotónica, búsqueda de alpha, variables/interacciones nuevas o enrutamiento de modelos. El diagnóstico confirma que la calibración agregada oculta heterogeneidad y soporte escaso; no demuestra una corrección validada ni exige aumentar complejidad. Corresponde consolidar esta evidencia con contracción y atribución, manteniendo la incertidumbre de último, reservas, reporte y capital.', '',
        'Cero ajustes nuevos, nuevas recetas, remuestreos o precios de 2024/test. Se hicieron quince inferencias sobre filas de ajuste con estimadores guardados, sin volver a estimar transformaciones o parámetros. El contador permanece en 195 ajustes de precio y 285 constantes. 2024, test, actas, scores y ledger siguen cerrados para este trabajo; la exposición previa del título ajeno queda declarada sin usar sus cifras o afirmar ceguera completa. Revisión propia de Codex, no profesional independiente. Sin remoto, envíos, delegación, publicación externa o cambios a otras automatizaciones.', '',
        '[Plan previo](../../registro/semana2_b20_bandas_calibracion_plan_v1.json), [índice](../../registro/semana2_b20_bandas_calibracion_actual.json), [productor](../../src/semana2/revisar_calibracion_b20_bandas2023.py), [comprobador separado](../../herramientas/verificar_calibracion_b20_bandas2023.py) y [adversos](../../herramientas/probar_calibracion_b20_bandas2023.py). Cortes exactos, replay de ajuste, asignaciones OOF y todas las celdas quedan en `privado/semana2/desarrollo2023/b20_bandas_calibracion_20261024_v1`, fuera de Git. La ficha del modelo y la distinción de revisión propia siguen Documentación IAA §3 y Gobernanza §2.8.']
    doc.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    evidence = lambda name: {'path': rel(run/name), 'sha256': sha(run/name)}
    idx = {'id': p['id'], 'author': 'Codex', 'utc': now, 'path_base': 'workspace_root',
           'status': 'training_only_bands_verified_local_calibration_heterogeneous_support_sparse_no_change',
           'run': rel(run), 'documentation': rel(doc), 'plan': rel(REPO/'registro/semana2_b20_bandas_calibracion_plan_v1.json'),
           'plan_sha256': r['plan_sha256'], 'report': evidence('report.json'), 'readout': evidence('readout.json'),
           'verification': evidence('verification.json') | {'passed': v['passed'], 'failed': 0},
           'fixtures': evidence('fixture_checks.json') | {'passed': f['passed'], 'failed': 0},
           'decision_journal': evidence('decision_journal.json'), 'manifest': evidence('manifest.json'),
           'new_fits': 0, 'new_model_recipes': 0, 'new_bootstrap': 0, 'saved_training_rate_replays': 15,
           'rows_heldout': 50094, 'training_replay_rows_not_independent': 200376,
           'reference': 'W2-B00', 'promotion': False, 'all_alternatives_preserved': True,
           'scope': p['scope'], '2024_test_closed': True, 'ledger_read': False,
           'forum_prior': p['forum_prior'], 'forum_result': p['forum_result'], 'professional_independent_validation': False}
    ip = REPO/'registro/semana2_b20_bandas_calibracion_actual.json'
    assert not ip.exists()
    dump(ip, idx)
    nightpath = REPO/'registro/semana2_continuidad_nocturna.json'
    n = read(nightpath)
    assert (n.get('current_unit') or {}).get('id') == p['id'], 'Unidad concurrente: no sobrescribir'
    unit = {'id': p['id'], 'run': rel(run), 'documentation': rel(doc), 'verification': idx['verification'],
            'fixtures': idx['fixtures'], 'decision_journal': idx['decision_journal'], 'index': rel(ip),
            'forum_result': p['forum_result'], 'new_fits': 0, 'new_bootstrap': 0, 'training_replay_scopes': 15}
    n['completed_units'].append(unit)
    n['current_unit'], n['latest_completed_unit'], n['updated_utc'] = None, unit, now
    n['status'] = 'scheduled_'+str(len(n['completed_units']))+'_units_B20_calibration_bands_verified_no_recalibration'
    n['next_unit'] = 'Consolidate completed B20 attribution/contraction/calibration receipts and pending validation requirements, without rerunning suites, fits, bootstrap or new price recipes. No bandfactors/alpha/routing; keepB00/all21recipes and2024/test/ledgerclosed.'
    n['queue'] = ['Consolidate existingB20 evidence and unresolved assumptions with cited frozen receipts, no repeated diagnostics.',
                  'No new model or recalibration without distinct necessity and prior recipe; keep2024/testclosed.',
                  'Preserve existing Kaggle incident monitor and final honest balance at07:00Bogota.']
    n['latest_b20_calibration_bands_index'], n['no_repetition_for_completed_b20_calibration_bands'] = rel(ip), True
    n['integration_decisions']['B20_calibration_bands'] = 'GlobalAE1.011 hides band/segment mismatch; buildinglow1.966/high0.714 and sparseconcentrated newbusinesscells. No adopted normalization or complexmodel.'
    n['open_conditions'].append({'id': 'B20-BANDS-CALIBRATION-SUPPORT', 'status': 'open',
        'effect': 'BandA/E heterogeneity and costconcentration, overlappingfolds and adaptive2023research do not support automatic calibrationfactors or modelpromotion.'})
    dump(nightpath, n)
    rp = ROOT/'RUTAS_PROYECTO.json'
    routes = read(rp)
    routes.update(week_2_b20_calibration_bands_index=rel(ip), week_2_b20_calibration_bands_report=rel(doc), week_2_b20_calibration_bands_plan=idx['plan'])
    dump(rp, routes)
    statepath = ROOT/'Preparación/ESTADO_PROYECTO.json'
    raw = statepath.read_text(encoding='utf-8-sig')
    key = 'semana2_b20_bandas_calibracion2023_20261024'
    assert key not in json.loads(raw)
    raw = raw.replace('{', '{\n  '+json.dumps(key)+': '+json.dumps({'utc': now, 'author': 'Codex', 'path_base': 'workspace_root',
            'index': rel(ip), 'status': idx['status'], 'new_fits': 0, 'new_bootstrap': 0, 'training_saved_model_replays': 15,
            '2024_test_closed': True, 'promotion': False}, ensure_ascii=False)+',', 1)
    statepath.write_text(raw, encoding='utf-8')
    note = '\n\n## S2-B20-BANDAS-CALIBRACION2023-v1-20261024: calibración en bandas de ajuste\n\nCodex, UTC '+now+'. Encargo humano de revisar calibración B20 con bandas fijadas en ajuste, artefactos guardados y sin reentrenar. Plan y comentario B20-BANDS-PRE preceden al cálculo. Quintiles de tasa anual nominal por ramo/fold, inversa empírica 20/40/60/80%, con fronteras superiores inclusivas, empates y vacíos conservados; cero etiquetas retenidas para cortes. B20/B19 se leen en idénticas bandas y filas B20. Se usaron quince estimadores guardados, inferencia de ajuste con fit bloqueado; 200.376 apariciones de 50.094 periodos, no nuevas muestras independientes.\n\nA/E OOF global B20 1,01128 y B19 0,99094. Bandas B20 de menor a mayor tasa: autos 1,082/0,861/1,038/1,019/0,981; edificios 1,966/1,563/0,856/1,198/0,714; contenidos 1,226/1,175/0,759/1,444/0,789. Algunos extremos moderan B19, otras bandas empeoran. En edificios banda1 69 positivos y mayor grupo31,65% del coste; banda5 124 positivos y mayor19,02%. Su A/E banda1 varía 0,342–3,457 entre folds solapados, sin interpretación de intervalo. Autos nuevos: banda1 vacía, banda2 trece periodos/dos positivos/A-E11,991; banda3 104/seis/6,786, con93,91% del coste en un grupo. No convertir esa oscilación en factores. Cuatro OOF fuera del rango de ajuste conservados, sin clipping.\n\nPasaron 2.121 verificaciones separadas y 21 adversos, con solapamiento; predictor manual, ordenación/bisect, fsum y diccionarios, particiones y fuentes exactas, target/IDs no influyen cortes. Empates/vacíos/AE cero legítimo y comandos nativos de fuente/repetición comprobados. Intercepto Tweedie con score pequeño no obliga A/E uno. No reajuste, receta nueva, factor, isotónica, alpha o enrutamiento. Contador 195/285 y B00/B01–B20 exactos; no promoción, no complejidad adicional. Informe docs/semana2/CALIBRACION_B20_BANDAS_AJUSTE_2023.md e índice registro/semana2_b20_bandas_calibracion_actual.json en repositorio común; corrida privada b20_bandas_calibracion_20261024_v1.\n\n2024/test/ledger cerrados y exposición previa de título externo declarada, sin uso ni ceguera completa. Revisión propia, no profesional independiente. Cero entrenamiento/remuestreo/envío/remoto/delegación/mensajes externos u otras automatizaciones. Próximo: consolidar recibos existentes de atribución/contracción/calibración y requisitos de validación, sin repetir suites o recetas. Condiciones de último, reporte, reservas y capital abiertas; ventana nocturna existente intacta y balance parcial.\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        with (ROOT/'Preparación'/name).open('a', encoding='utf-8', newline='') as ff:
            ff.write(note)
    with (REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md').open('a', encoding='utf-8', newline='') as ff:
        ff.write('\n\n## Bandas de calibración B20 verificadas sin ajuste\n\nLa [revisión](CALIBRACION_B20_BANDAS_AJUSTE_2023.md) fija quintiles exclusivamente en las tasas de ajuste y compara B19 sobre las mismas filas. A/E global cercano a uno oculta diferencias, con celdas concentradas/escasas y variación entre folds. No se adoptan factores, otra fórmula o mayor complejidad. Fuentes y contadores exactos, 2.121 verificaciones y 21 adversos; 2024/test cerrados. Próximo: consolidar evidencia B20 ya terminada y sus requisitos pendientes, sin más replay/suites/fit por rutina. Ventana y programación intactas.\n')
    body = 'Resultado de B20-BANDS-PRE, plan S2-B20-BANDAS-CALIBRACION2023-v1-20261024. Quince modelos B20 guardados, fit bloqueado; cortes quintiles solo de tasa anual de sus filas de ajuste por ramo/fold, con empates y vacíos conservados. B19 usa idénticas bandas/filas B20. 50.094 OOF únicos;200.376apariciones de ajuste son cuatro usos de cada periodo, no evidencia independiente. Sin reentrenar o reajustar transformaciones.\n\nA/E global B20 1,01128, B19 0,99094. Por bandas B20: autos1,082/0,861/1,038/1,019/0,981; edificios1,966/1,563/0,856/1,198/0,714; contenidos1,226/1,175/0,759/1,444/0,789. Modera varios extremos B19, empeora otras bandas. Edificiosbanda1:69positivos,31,65% coste en mayorcomponente, A/E por fold0,342–3,457; no intervalo. Nuevosautos:banda1vacía, banda2 13periodos/2positivos/AE11,991, banda3 104/6/6,786 con93,91% coste enungrupo. Cuatro tasas OOF fuera del rango de ajuste conservadas. No calibración uniforme o suficiencia última acreditadas.\n\nPasaron2.121comprobaciones separadas y21adversos: replay manual exp(Xbeta), ordenestadístico/bisect, math.fsum/diccionarios y particiones. Targets/IDs no cambian cortes, empates/vacíos tratados y dos CLI reales rechazan fuente/repetición. Intercepto Tweedie no fuerza A/E uno. No factores por banda/isotónica/alpha/modelo nuevo/routing o complejidad. B00/B01–B20 conservados; contador195/285 exacto. Cero ajuste/receta/remuestreo/2024/test/ledger/envío/remoto/delegación/mensaje externo. Exposición previa del título declarada sin uso, revisión propia sin independencia profesional.\n\nInforme docs/semana2/CALIBRACION_B20_BANDAS_AJUSTE_2023.md; índice registro/semana2_b20_bandas_calibracion_actual.json; corrida privada b20_bandas_calibracion_20261024_v1, diario de ocho decisiones y fuentes SHA. Próximo: consolidar atribución/contracción/calibración con recibos ya existentes y requisitos de validación pendientes, sin repetir suites o iniciar otra tanda. Ventana nocturna y otras automatizaciones intactas.\n'
    (REPO/'registro/COD-S2-20261024-B20-BANDS-RESULT_cuerpo.md').write_text(body, encoding='utf-8')
    print(json.dumps({'document': rel(doc), 'index': rel(ip), 'passed': v['passed'], 'adversaries': f['passed'], 'completed_units': len(n['completed_units']), 'new_fits': 0}))


if __name__ == '__main__':
    main()
