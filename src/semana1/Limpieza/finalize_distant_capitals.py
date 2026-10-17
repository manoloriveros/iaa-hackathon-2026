"""Cierra y activa CAP05R tras la verificación propia; conserva documentos antes/después."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import sys
import uuid
import apply_distant_capitals as a
import clean_data as c
import pandas as pd


def main(out):
    assert not (out/'manifest.json').exists(), 'Corrida cerrada; no sobrescribir.'
    v = json.loads((out/'verification.json').read_text('utf-8'))
    protected = json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed'] == 0 and v['capital_changes'] == 46 and v['pending_after'] == 421
    assert all(c.digest(out/path) == digest for path, digest in v['verified_files'].items())
    assert all(c.digest(c.ROOT/path) == digest for path, digest in protected.items())
    assert all(c.digest(c.BASE/name) == c.digest(out/'source_snapshot'/name) for name in a.SCRIPTS)
    assert not a.OP_INDEX.exists(), 'Ya existe índice de esta operación.'
    parent = json.loads((out/'evidence/parent_index.json').read_text('utf-8'))
    cat = json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT/e['workspace_relative_path']) == e['sha256'] for e in cat.values())
    now = datetime.now(timezone.utc)
    rel = out.relative_to(c.ROOT).as_posix()
    close = c.BASE/'closures'/now.strftime('CAP05R_closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True, exist_ok=False)
    paths = {name: c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json', 'MEMORIA_PROYECTO.md', 'DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json': c.ROOT/'RUTAS_PROYECTO.json',
        'protocol.json': c.ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md': c.ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'model_README.md': c.ROOT/'Hackaton/Semana 1/Modelado/README.md',
        'cleaning_README.md': c.BASE/'README.md', 'capital_rules.md': c.BASE/'CAPITALES.md'})
    for name, path in paths.items():
        shutil.copy2(path, close/('before_'+name))
    state = json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    routes = json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    memory, decisions = paths['MEMORIA_PROYECTO.md'].read_text('utf-8'), paths['DECISIONES.md'].read_text('utf-8')
    protocol = json.loads(paths['protocol.json'].read_text('utf-8'))
    assert protocol['version'] == '1.8'
    decision = 'D'+str(max(map(int, re.findall(r'\bD(\d+)\b', decisions)))+1)
    ledger = pd.read_parquet(out/'ledger/all_capital_changes.parquet')
    signal = ledger.loc[ledger.audit_ref_test2025]
    record = {'decision_id': decision, 'rule': a.RULE, 'decision_criterion': 'DIST01-R v1, frozen D57 list only',
        'status': 'applied_verified_retrospective_only', 'run': '../'+rel, 'report': '../'+rel+'/informe.html',
        'catalog': '../'+rel+'/dataset_catalog.json', 'ledger': '../'+rel+'/ledger/all_capital_changes.parquet',
        'ledger_csv': '../'+rel+'/ledger/all_capital_changes.csv', 'test2025_ledger': '../'+rel+'/ledger/test2025_supported_changes.csv',
        'corrected_test2025_ledger': '../'+rel+'/ledger/corrected_test2025_rows.csv',
        'cumulative_test2025_ledger': '../'+rel+'/ledger/cumulative_test2025_supported_changes.csv',
        'pending': '../'+rel+'/tables/pending_capitals.parquet', 'verification': '../'+rel+'/verification.json',
        'index': '../Hackaton/Semana 1/Limpieza/current_distant_capital_correction.json',
        'capital_changes': 46, 'changes_by_table': a.COUNTS, 'changes_by_line': {'buildings': 18, 'contents': 28},
        'new_test2025_supported_rows': 7, 'new_test2025_by_line': {'buildings': 1, 'contents': 6},
        'corrected_test2025_rows': 13, 'prior_anchors': 21, 'later_anchors': 25,
        'pending_in_retrospective_layer': 421, 'CAP01_inherited_changes': 2073, 'CAP02R_inherited_changes': 867,
        'CAP03R_inherited_changes': 11, 'CAP04R_inherited_changes': 109, 'retrospective_changes_total': 1033,
        'test2025_supported_cumulative_rows': 136, 'total_corrected_capitals': 3106, 'baseline_pending_unchanged': 1454,
        'originals_modified': False, 'other_fields_changed': 0, 'new_columns': 0, 'claims_modified': False,
        'test_tables_modified': True, 'dates_modified': False, 'keep_108_pending': True,
        'held_numeric_policies': ['C50633171', 'C56600576'], 'general_400day_rule_changed': False,
        'retrospective_only': True, 'source_units_confirmed': False, 'automatic_expansion': False,
        'technical_checks': v['passed'], 'independent_validation': False, 'models_trained': False, 'approved_for_modeling': False,
        'operational_T0_materialized': False, 'CON01_activated': False, 'calendar_dates_pending': True,
        'closure': '../'+close.relative_to(c.ROOT).as_posix()}
    money = lambda x: f'{float(x):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    all_columns = ['row_id', 'policy_id', 'line', 'source_table', 'old', 'new', 'selected_reference_row_id', 'selected_reference_capital_CU', 'selected_reference_direction', 'selected_start_gap_days', 'audit_ref_test2025', 'corrected_row_is_test2025']
    table = ledger[all_columns].to_html(index=False, border=0, float_format=money)
    signal_table = signal[['row_id', 'policy_id', 'line', 'old', 'new', 'selected_reference_source_table', 'selected_reference_row_id', 'selected_reference_period_start', 'selected_reference_capital_CU']].to_html(index=False, border=0, float_format=money)
    report = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CAP05R: 46 capitales divididos por mil</title><style>body{{font:16px/1.6 system-ui,sans-serif;background:#eef3f6;color:#183243;margin:0}}main{{max-width:1450px;margin:auto;padding:24px}}header,section{{padding:24px;background:white;border-radius:12px;margin-bottom:18px}}header{{background:#17394d;color:white}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:23px}}table{{border-collapse:collapse;font-size:13px;width:100%}}th,td{{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}}th{{position:sticky;top:0;background:#edf3f6}}.scroll{{overflow:auto;max-height:650px}}a{{color:#007d72}}.note{{border-left:4px solid #b47725;background:#fff5e2;padding:12px 18px}}</style></head><body><main>
<header><h1>46 capitales divididos por mil en CAP05R</h1><p>{decision} · Capa retrospectiva sobre CAP04R · Lista D57 autorizada</p><p>18 edificios · 28 contenidos · 7 respaldos de test 2025 · 421 pendientes conservados</p></header>
<section><h2>Los 46 cambios</h2><p>Solo cambia sum_insured en los 46 row_id congelados. Se crean cuatro archivos derivados: policies_buildings (11 cambios), policies_contents (22), test_buildings (7) y test_contents (6). Sus demás celdas, fechas, nulos, tipos, metadatos y orden permanecen idénticos a CAP04R. Las otras siete referencias completas del catálogo se conservan.</p><div class="scroll">{table}</div><p><a href="ledger/all_capital_changes.csv">Bitácora de las 46 filas, CSV</a> · <a href="ledger/all_capital_changes.parquet">Bitácora tipada</a> · <a href="dataset_catalog.json">Nuevo catálogo</a></p><p>Los límites afectados sumaban {money(ledger.old.sum())} CU y ahora suman {money(ledger.new.sum())} CU. Esta suma de periodos no representa pérdidas, primas ni una reducción del riesgo. El capital no se anualiza por exposición.</p></section>
<section><h2>Siete respaldos de test 2025</h2><p>Una fila de edificios y seis de contenidos se apoyan en anclas originales posteriores de test 2025. Se señalan con audit_ref_test2025=true en la bitácora y en esta extracción; no se añade ninguna columna a las pólizas.</p><div class="scroll">{signal_table}</div><p><a href="ledger/test2025_supported_changes.csv">Los siete respaldos nuevos</a> · <a href="ledger/cumulative_test2025_supported_changes.csv">Los 136 acumulados</a></p><div class="note">Hay trece filas corregidas que pertenecen a test 2025, distintas de los siete casos con ancla en test 2025. Las trece se apoyan en referencias anteriores de train. <a href="ledger/corrected_test2025_rows.csv">Ver las trece filas corregidas de test</a>.</div></section>
<section><h2>Excepción acotada de referencias distantes</h2><p>CAP05R materializa exclusivamente las 46 propuestas DIST01-R de D57. Se conserva el límite general de 400 días. La excepción exige extremos completos e iguales en los campos D34, la primera referencia original habitual completa en cada sentido elegida antes de comprobar contexto o importe, distancia mayor de 400 días y hasta dos años calendario, y una sola fila intermedia original habitual con faltantes y sin cambios conocidos. La hipótesis /1000 frente al ancla y cada paso monetario deben quedar entre 0,90 y 1,10. No se vuelve a seleccionar ni se amplía la lista.</p><p>Hay 21 anclas anteriores y 25 posteriores, a 427–731 días. Se mantienen los 20 huecos CAL00 de los 92 enlaces. No se imputan los contextos intermedios ni se afirma que todos los factores tarifarios sean constantes: days_unoccupied difiere entre los extremos de los 18 edificios.</p><p>B02977304/B00282158 pasa de 187.000.000 a 187.000 CU; los 193.000 intermedios con alarmas ausentes y el ancla de 198.000 permanecen iguales. B05543458/B02775002 de test 2025 pasa de 409.000.000 a 409.000 con ancla anterior de 385.000. B55826538/B01561508 pasa a 211.000 con ancla test 2025 de 224.000. C62678958/C02870429 pasa a 34.100; la referencia intermedia de 33.400 conserva los nulos de seguridad y bienes de valor.</p><div class="note">Toda la capa es retrospectiva. Una fecha anterior del ancla no prueba disponibilidad F0 ni aprueba un backtest causal. Tampoco se confirma la unidad mediante la fuente. No se entrena ni se cambia el objetivo.</div><p><a href="rules.json">Regla y límites</a> · <a href="evidence/review_protocol.json">Criterio histórico D57</a> · <a href="authorization.json">Solicitud íntegra y autorización</a></p></section>
<section><h2>421 pendientes conservados</h2><p>El inventario es el complemento exacto de los 467 anteriores, con todos sus campos y orden preservados. Incluye los 108 sin referencia original habitual y los dos conflictos de D57. C50633171/C00502745 conserva 27.200.000 y su ampliación C01153989, 39.400; C56600576/C00399729 conserva 25.700.000 y C01147928, 37.700. Esas ampliaciones completas no se saltan para usar solo 2023.</p><p>B19256617/B00962235 mantiene 377.000.000 y C48613718/C01596694 mantiene 29.300.000. No hay cascadas. Se conservan nulos, códigos T/W, fechas, exposición, primas, siniestros y marcas REN00/PRE00. <a href="tables/pending_capitals.csv">Inventario de los 421 pendientes</a> · <a href="tables/pending_capitals.parquet">Inventario tipado</a>.</p><p>Se heredan 2.073 CAP01, 867 CAP02R, once CAP03R y 109 CAP04R sin redivisión. La rama suma 3.106 capitales corregidos, de los cuales 1.033 son retrospectivos. Hay 136 respaldos test 2025 acumulados. La base current_dataset.json sigue idéntica con 1.454 pendientes. <a href="ledger/cumulative_retrospective_changes.csv">Las 1.033 correcciones retrospectivas</a>.</p></section>
<section><h2>Validación y reproducción</h2><p>Pasaron {v['passed']} controles propios. Se compararon completas las cuatro tablas Arrow, y las únicas diferencias son las 46 celdas autorizadas. Se comprobó cada división con Decimal, se releyeron las 210 filas históricas y se reconstruyó el criterio del ancla más próxima, contexto, ventana, fila intermedia y pasos de capital/calendario. Restaurar old en source_position recupera exactamente cada tabla padre y sus metadatos. Una segunda transformación no cambia valores; un importe inesperado se rechaza.</p><p>La bitácora conserva posición, identidad, old/new, ancla, dirección, distancia, señales temporales, divisor/regla y hashes de fuente, derivado, cohorte y autorización. Los falsos históricos de la propuesta se conservan; la solicitud posterior autoriza esta operación. <a href="verification.json">Controles completos</a> · <a href="lineage.json">Linaje</a> · <a href="manifest.json">Manifiesto SHA256</a>.</p><p>Desde C:/dev/Hakaton, usar Preparación/.venv/Scripts/python.exe con apply_distant_capitals.py; pasar la carpeta generada a verify_distant_capitals.py y, después de verificar, a finalize_distant_capitals.py. Se archivan los cinco scripts. El cierre comprueba una segunda invocación real del CLI sin cambios. current_retrospective_dataset.json avanza a CAP05R; current_distant_capital_correction.json conserva esta operación. Los demás índices de operación y corridas siguen intactos.</p><p>Se actualizan protocolo y metodología a 1.9, con documentos antes/después. Informe estático con tablas y enlaces comprobados; no se acredita renderizado de navegador ni revisión independiente. La IA preparó código y controles propios y el participante autorizó la lista. Siguen pendientes T0/F0, fechas, unidades y controles para modelar, incluida la exclusión de customer_service_contacts registrada en D56. Sin proveedor externo, entrenamiento, publicaciones o contactos.</p><p>IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad; son referencias educativas y no certificación.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report, encoding='utf-8')
    class ReportCheck(HTMLParser):
        def __init__(self):
            super().__init__()
            self.refs, self.table_rows, self.rows = [], [], 0
        def handle_starttag(self, tag, attrs):
            self.refs += [val for key, val in attrs if key in ['href', 'src']]
            if tag == 'table': self.rows = 0
            if tag == 'tr': self.rows += 1
        def handle_endtag(self, tag):
            if tag == 'table': self.table_rows.append(self.rows-1)
    parser = ReportCheck()
    parser.feed(report)
    assert parser.table_rows == [46, 7] and all(ref == 'manifest.json' or (out/ref).is_file() for ref in parser.refs)
    assert all(row_id in report for row_id in ledger.row_id)
    c.dump(out/'report_verification.json', {'status': 'passed_static_report_checks', 'tables_actual_data_rows': parser.table_rows,
        'local_links': len(parser.refs), 'all_46_ids_present': True, 'real_browser_rendering_verified': False, 'independent_validation': False})
    for name in ['README.md', 'PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name, out/'evidence'/('IAA_'+name))
    c.dump(out/'manifest.json', {'created_utc': now.isoformat(), 'type': 'immutable_CAP05R_capital_correction', 'files': [
        {'path': p.relative_to(out).as_posix(), 'sha256': c.digest(p), 'bytes': p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    pointer = {**parent, 'workspace_relative_run': rel, 'catalog_workspace_relative': rel+'/dataset_catalog.json',
        'status': 'verified_retrospective_CAP05R', 'capital_rule': a.RULE, 'capital_changes_this_layer': 46, 'capital_changes_inherited': 3060,
        'CAP01_inherited_changes': 2073, 'CAP02R_inherited_changes': 867, 'CAP03R_inherited_changes': 11, 'CAP04R_inherited_changes': 109,
        'total_capital_changes': 3106, 'retrospective_capital_changes_total': 1033, 'pending_capitals': 421,
        'later_test2025_supported_rows': 136, 'this_layer_test2025_supported_rows': 7, 'corrected_test2025_rows_this_layer': 13,
        'cohort_sha256': c.digest(out/'evidence/frozen_46_proposal.parquet'),
        'parent_catalog_index_sha256': c.digest(out/'evidence/parent_index.json'),
        'application_index_workspace_relative': a.OP_INDEX.relative_to(c.ROOT).as_posix(),
        'retrospective_only': True, 'not_approved_for_cutoff_specific_backtesting': True, 'approved_for_modeling': False}
    assert all(c.digest(c.ROOT/path) == digest for path, digest in protected.items())
    temp = c.BASE/('distant_index_'+uuid.uuid4().hex+'.json')
    c.dump(temp, pointer)
    temp.replace(a.INDEX)
    c.dump(a.OP_INDEX, {'workspace_relative_run': rel, 'report_workspace_relative': rel+'/informe.html', 'decision_id': decision,
        'status': 'applied_verified_retrospective_only', 'capital_changes': 46, 'new_test2025_supported_rows': 7,
        'corrected_test2025_rows': 13, 'pending': 421})
    protocol['version'] = '1.9'
    protocol['inputs'].setdefault('retrospective_capital_history', []).append(protocol['inputs']['retrospective_capital_layer'])
    protocol['inputs']['retrospective_capital_layer'] = {'latest_rule': a.RULE, 'decision_criterion': 'DIST01-R v1 frozen D57 cohort only',
        'rows_this_layer': 46, 'operation': 'sum_insured /1000', 'catalog_index': '../Limpieza/current_retrospective_dataset.json',
        'default_catalog_index_unchanged': '../Limpieza/current_dataset.json', 'retrospective_only': True,
        'CAP01_inherited': 2073, 'CAP02R_inherited': 867, 'CAP03R_inherited': 11, 'CAP04R_inherited': 109,
        'total_corrected_capitals': 3106, 'retrospective_corrections_total': 1033, 'test2025_supported_new': 7,
        'test2025_supported_cumulative': 136, 'pending_in_this_layer': 421, 'pending_in_default_layer': 1454,
        'test_rows_changed': 13, 'prior_anchors': 21, 'later_anchors': 25, 'all_other_fields_preserved': True,
        'general_400day_rule_changed': False, 'automatic_expansion': False, 'source_unit_confirmation': False, 'T_W_semantic_merge': False,
        'use_in_cutoff_specific_backtests': 'Not approved. Reconstruction and rule selection retrospective; earlier anchor dates do not prove F0 availability.',
        'audit_marker': 'audit_ref_test2025 in ledger only; seven test anchors distinct from thirteen corrected test rows; no added predictor.',
        'report': '../Limpieza/'+out.relative_to(c.BASE).as_posix()+'/informe.html'}
    c.dump(paths['protocol.json'], protocol)
    note = f'''\n\n{decision}, CAP05R autorizado: 46 filas D57 /1000 sobre CAP04R (18 edificios y 28 contenidos), siete respaldos posteriores de test 2025 (1/6) y 421 pendientes preservados, incluidos los 108 sin ancla y C50633171/C56600576. Se corrigen trece filas de test, conteo distinto del de anclas test. Las otras celdas, nulos, fechas y siniestros permanecen iguales. Se conservan las 3.060 correcciones heredadas; total 3.106, de las cuales 1.033 retrospectivas, con 136 respaldos test acumulados. La base sigue intacta con 1.454 pendientes. DIST01-R queda limitada a la lista congelada de 46, sin ampliar la regla general de 400 días. Protocolo 1.9; capa retrospectiva sin aprobación causal por corte. '''
    methodology = paths['methodology.md'].read_text('utf-8')
    old_header = 'Versión 1.8, con capas retrospectivas CAP02R/CAP03R/CAP04R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.'
    assert methodology.count(old_header) == 1
    methodology = methodology.replace(old_header, 'Versión 1.9, con capas retrospectivas CAP02R/CAP03R/CAP04R/CAP05R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.')
    paths['methodology.md'].write_text(methodology.rstrip()+note+f'[Informe y bitácora](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html).\n', encoding='utf-8')
    for key, prefix in [('model_README.md', '../Limpieza/'), ('cleaning_README.md', ''), ('capital_rules.md', '')]:
        paths[key].write_text(paths[key].read_text('utf-8').rstrip()+note+f'[Informe y bitácora]({prefix}{out.relative_to(c.BASE).as_posix()}/informe.html). Scripts: apply_distant_capitals.py, verify_distant_capitals.py y finalize_distant_capitals.py; índice de operación current_distant_capital_correction.json.\n', encoding='utf-8')
    state['distant_capital_application'] = record
    state['distant_capital_review']['followup_application_decision'] = decision
    state['distant_capital_review']['46_row_operation_authorized_later'] = True
    state['methodological_plan']['version'], state['memory_as_of'] = '1.9', now.isoformat()
    state['validation_backlog_update']['latest_data_layer_followup_decision'] = decision
    state['validation_backlog_update']['historical_snapshot_not_reaudited'] = True
    routes['week_1_distant_capital_application_index'] = 'Hackaton/Semana 1/Limpieza/current_distant_capital_correction.json'
    c.dump(paths['ESTADO_PROYECTO.json'], state)
    c.dump(paths['RUTAS_PROYECTO.json'], routes)
    local_date = now.astimezone(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d')
    decision_text = f'''\n\n### {decision}, CAP05R autorizado: 46 capitales /1000 y 421 pendientes conservados, {local_date}, America/Bogota

El participante autorizó dividir por mil exactamente las 46 propuestas de D57 en una nueva capa retrospectiva sobre CAP04R, conservar originales y los otros 421 pendientes, señalar los siete respaldos test 2025 y documentar/validar cada cambio. Solicitud íntegra en ../{rel}/authorization.json. Lista congelada SHA256 c0c1e6c9a9aa173020ad71c07e583681cdc83a3c609ba675e63006dae5d6f0d3, sin selección nueva o cascada. Solo cambia sum_insured en policies_buildings (11), policies_contents (22), test_buildings (7) y test_contents (6). Son 18 edificios y 28 contenidos. Los demás campos, filas, orden, nulos, fechas, tipos y metadatos permanecen idénticos. Las otras siete referencias completas del catálogo siguen iguales.

CAP05R materializa DIST01-R v1 únicamente sobre esta lista. Conserva el criterio general de 400 días: la excepción autorizada usa extremos D34 completos/iguales, primera referencia original habitual completa de cada sentido elegida antes del contexto/importe, distancia mayor de 400 días y hasta dos años calendario, una sola fila intermedia original habitual con faltantes y sin cambios conocidos, y razón /1000 frente al ancla y cada paso monetario entre 0,90–1,10. No se imputan campos ni se saltan contradicciones completas. Hay 21 anclas anteriores y 25 posteriores, a 427–731 días. Los 20 huecos CAL00 de 92 enlaces se conservan. No se afirma que todos los factores tarifarios sean constantes. Los dos años calendario pueden sumar 731 días.

Los siete respaldos test 2025, uno de edificios y seis de contenidos, se señalan solo en bitácora y extracción propia con audit_ref_test2025. Son distintos de las trece filas corregidas que pertenecen a test 2025 (siete edificios y seis contenidos), respaldadas por train anterior. El acumulado retrospectivo es 1.033 (867 CAP02R + 11 CAP03R + 109 CAP04R + 46 CAP05R), con 136 respaldos test (111+1+17+7); con 2.073 CAP01 suma 3.106 correcciones distintas. La fecha anterior de 21 anclas no prueba disponibilidad F0; esta capa y la selección de regla son retrospectivas y no aprueban backtest causal, entrenamiento o unidad de fuente.

Los 421 pendientes son el complemento exacto de los 467 anteriores, con inventario íntegro y orden conservados. Se mantienen los 108 sin referencia original habitual; C50633171/C00502745 conserva 27.200.000 y C56600576/C00399729, 25.700.000; sus ampliaciones completas C01153989/C01147928 siguen en 39.400/37.700. No se saltan para elegir solo 2023. C48613718/C01596694 sigue en 29.300.000 y B19256617/B00962235 en 377.000.000, sin cascadas. Los nulos de contextos intermedios siguen intactos, igual que T/W, siniestros, exposición, primas y marcas REN00/PRE00. No se recalcula el objetivo.

Cada cambio conserva posición, identidad, old/new, ancla original, dirección, distancia, señales de test/futuro, regla/divisor y hashes de fuente, derivado, cohorte y autorización. Pasaron {v['passed']} controles propios: diferencias completas de las cuatro tablas exactamente autorizadas, Decimal por fila, relectura de los 210 periodos y reconstrucción de criterio DIST01-R, preservación de pendientes y reparaciones heredadas, reversión exacta de las cuatro tablas Arrow y metadatos, segunda transformación sin cambios y rechazo de importes inesperados. El cierre comprueba además una segunda invocación real del CLI sin cambios. El informe estático contiene las 46 filas y los siete respaldos con enlaces locales comprobados; no se acredita renderizado de navegador o validación independiente.

current_retrospective_dataset.json avanza atómicamente a CAP05R solo después de verificar capa y puntero padre; current_distant_capital_correction.json identifica la operación. Los índices de operación anteriores y D57 permanecen intactos. La base current_dataset.json conserva su hash y 1.454 pendientes. Protocolo/metodología 1.9, documentos antes/después archivados; los anteriores permanecen como evidencia histórica. El backlog D56 sigue siendo fotografía histórica, no reauditoría: customer_service_contacts, T0/F0 y demás controles de modelado siguen pendientes. La IA preparó código y verificaciones propias; el participante autorizó esta lista. Sin proveedor externo, publicación, contacto a terceros o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad. Ver distant_capital_application.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+decision_text, encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+note+f'[Informe](../{rel}/informe.html), [46 cambios](../{rel}/ledger/all_capital_changes.csv), [siete respaldos test](../{rel}/ledger/test2025_supported_changes.csv). {v["passed"]} controles propios y reversión/idempotencia verificadas. current_retrospective_dataset.json avanza a CAP05R y current_distant_capital_correction.json conserva la operación. Sin entrenamiento, aprobación causal o validación independiente. Ver distant_capital_application y {decision}.\n', encoding='utf-8')
    after = close/'after'
    after.mkdir()
    for name, path in paths.items():
        shutil.copy2(path, after/name)
    pointer_sha, op_sha = c.digest(a.INDEX), c.digest(a.OP_INDEX)
    replay = subprocess.run([sys.executable, str(c.BASE/'apply_distant_capitals.py')], cwd=c.ROOT, capture_output=True, text=True, check=True)
    replay_result = json.loads(replay.stdout)
    mutable = a.INDEX.relative_to(c.ROOT).as_posix()
    post = [
        {'check': 'Actual second CLI invocation is verified no-op', 'passed': replay_result['status'] == 'already_applied_verified_noop' and replay_result['new_changes'] == 0},
        {'check': 'No-op preserves both current indexes', 'passed': c.digest(a.INDEX) == pointer_sha and c.digest(a.OP_INDEX) == op_sha},
        {'check': 'Originals, parent files, baseline and all prior indexes unchanged', 'passed': all(c.digest(c.ROOT/path) == digest for path, digest in protected.items() if path != mutable)},
        {'check': 'Closed new, CAP04R and D57 manifests intact', 'passed': a.cap.manifest_ok(out) and a.cap.manifest_ok(c.ROOT/parent['workspace_relative_run']) and a.cap.manifest_ok(a.REVIEW)},
        {'check': 'Active counts 421/3106/136/13 correct', 'passed': pointer['pending_capitals'] == 421 and pointer['total_capital_changes'] == 3106 and pointer['later_test2025_supported_rows'] == 136 and pointer['corrected_test2025_rows_this_layer'] == 13},
        {'check': 'Default catalog and no modeling approval preserved', 'passed': protocol['inputs']['catalog_index'] == '../Limpieza/current_dataset.json' and not pointer['approved_for_modeling'] and pointer['not_approved_for_cutoff_specific_backtesting']},
        {'check': 'Every report link resolves after sealing', 'passed': all((out/ref).is_file() for ref in parser.refs)}]
    assert all(x['passed'] for x in post)
    c.dump(close/'post_publication_verification.json', {'passed': len(post), 'failed': 0, 'checks': post, 'actual_second_cli': replay_result, 'stderr': replay.stderr, 'independent_validation': False})
    c.dump(close/'closure.json', {'created_utc': now.isoformat(), 'decision_id': decision, 'application': record,
        'manifest_sha256': c.digest(out/'manifest.json'), 'retrospective_index_sha256': pointer_sha,
        'post_publication_checks': len(post), 'documents': {p.relative_to(c.ROOT).as_posix(): c.digest(p) for p in [*paths.values(), a.INDEX, a.OP_INDEX]}})
    print(json.dumps({'decision': decision, 'run': str(out), 'report': str(out/'informe.html'), 'closure': str(close),
        'status': 'applied_verified_retrospective_only', 'post_publication_checks': len(post)}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
