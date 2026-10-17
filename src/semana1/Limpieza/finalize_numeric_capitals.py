"""Publica CAP03R tras comprobar datos y puntero padre; conserva la base y CAP02R."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import sys
import uuid

import apply_numeric_capitals as a
import clean_data as c
import pandas as pd


def main(out):
    assert not (out/'manifest.json').exists(),'Corrida cerrada; no sobrescribir.'
    v=json.loads((out/'verification.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==0 and v['capital_changes']==11 and v['pending_unchanged']==576
    assert all(c.digest(out/path)==sha for path,sha in v['verified_files'].items())
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    for name in ['apply_numeric_capitals.py','verify_numeric_capitals.py','finalize_numeric_capitals.py','clean_data.py','correct_capitals.py']:
        assert c.digest(c.BASE/name)==c.digest(out/'source_snapshot'/name)
    parent=json.loads((out/'evidence/parent_index.json').read_text('utf-8'))
    cat=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT/entry['workspace_relative_path'])==entry['sha256'] for entry in cat.values())
    assert not a.OP_INDEX.exists(),'Ya existe índice de esta aplicación; no sustituirlo.'
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    close=c.BASE/'closures'/datetime.now(timezone.utc).strftime('CAP03R_closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':c.ROOT/'RUTAS_PROYECTO.json',
        'protocol.json':c.ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md':c.ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'model_README.md':c.ROOT/'Hackaton/Semana 1/Modelado/README.md',
        'cleaning_README.md':c.BASE/'README.md','capital_rules.md':c.BASE/'CAPITALES.md'})
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8');decisions=paths['DECISIONES.md'].read_text('utf-8')
    protocol=json.loads(paths['protocol.json'].read_text('utf-8'))
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    record={'decision_id':decision,'rule':a.RULE,'status':'applied_verified_retrospective_only','run':'../'+rel,
        'report':'../'+rel+'/informe.html','catalog':'../'+rel+'/dataset_catalog.json',
        'ledger':'../'+rel+'/ledger/all_capital_changes.parquet','ledger_csv':'../'+rel+'/ledger/all_capital_changes.csv',
        'test2025_ledger':'../'+rel+'/ledger/test2025_supported_changes.csv',
        'cumulative_test2025_ledger':'../'+rel+'/ledger/cumulative_test2025_supported_changes.csv',
        'pending':'../'+rel+'/tables/pending_capitals.parquet','verification':'../'+rel+'/verification.json',
        'index':'../Hackaton/Semana 1/Limpieza/current_numeric_capital_correction.json',
        'capital_changes':11,'source_table':'policies_contents','new_test2025_supported_rows':1,
        'new_test2025_policy':'C21091984','new_test2025_row':'C02362784','new_test2025_anchor':'C02964108',
        'pending_in_retrospective_layer':576,'C48613718_preserved_capital_CU':29300000,
        'CAP01_inherited_changes':2073,'CAP02R_inherited_changes':867,'retrospective_changes_total':878,
        'test2025_supported_cumulative_rows':112,'total_corrected_capitals':2951,'baseline_pending_unchanged':1454,
        'originals_modified':False,'other_fields_changed':0,'new_columns':0,'claims_modified':False,
        'normal_midterm_capitals_modified':False,'test_tables_modified':False,'dates_modified':False,
        'retrospective_only':True,'source_units_confirmed':False,'actual_contract_level_reset_confirmed':False,
        'automatic_expansion':False,'technical_checks':v['passed'],'independent_validation':False,
        'operational_T0_materialized':False,'models_trained':False,'approved_for_modeling':False,
        'CON01_activated':False,'calendar_dates_pending':True,'closure':'../'+close.relative_to(c.ROOT).as_posix()}
    ledger=pd.read_parquet(out/'ledger/all_capital_changes.parquet')
    display=ledger[['row_id','policy_id','old','new','initial_capital_CU','midterm_capital_CU','later_capital_CU','later_row_id','audit_ref_test2025']].rename(columns={
        'row_id':'Fila corregida','policy_id':'Póliza','old':'Capital anterior CU','new':'Capital nuevo CU',
        'initial_capital_CU':'Capital inicial previo CU','midterm_capital_CU':'Capital ampliado previo CU',
        'later_capital_CU':'Capital posterior CU','later_row_id':'Ancla posterior','audit_ref_test2025':'Ancla test 2025'})
    money=lambda x:f'{float(x):,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    table=display.to_html(index=False,border=0,float_format=money)
    report=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CAP03R: once capitales /1000</title><style>body{{font:16px/1.65 system-ui,sans-serif;background:#eef3f6;color:#183243;margin:0}}main{{max-width:1300px;margin:auto;padding:25px}}header,section{{padding:24px;border-radius:12px;background:white;margin-bottom:18px}}header{{background:#15384c;color:white}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:23px}}table{{border-collapse:collapse;font-size:13px;width:100%}}th,td{{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}}th{{background:#edf3f6;position:sticky;top:0}}.scroll{{overflow:auto;max-height:600px}}a{{color:#007d72}}code{{background:#edf3f6;color:#183243;padding:2px 4px}}.note{{border-left:4px solid #b47725;background:#fff5e2;padding:12px 18px}}</style></head><body><main>
<header><h1>CAP03R aplicado: once capitales divididos por mil</h1><p>{decision} · Lista congelada D51 autorizada · Nueva capa retrospectiva sobre CAP02R</p><p>11 filas de contenidos · 1 nuevo respaldo de test 2025 · 576 pendientes conservados</p></header>
<section><h2>Todos los cambios</h2><p>Solo cambia sum_insured en los once row_id propuestos y autorizados. La nueva tabla policies_contents conserva esquema, metadatos, filas, orden y todos los demás valores. Los capitales normales de los segmentos previos y posteriores también se conservan.</p><div class="scroll">{table}</div><p>Los once capitales sumaban {money(ledger.old.sum())} CU y ahora suman {money(ledger.new.sum())} CU. Son límites por periodo, no una reducción de primas, pérdidas o coste esperado. No se dividen primas, siniestros, exposición, objetivo ni predicciones.</p><p><a href="ledger/all_capital_changes.csv">Bitácora de los once cambios, CSV</a> · <a href="ledger/all_capital_changes.parquet">Bitácora tipada</a></p></section>
<section><h2>El respaldo posterior de test 2025</h2><p>C02362784, póliza C21091984, pasa de 26.200.000 a 26.200 CU. Su ancla posterior es C02964108 de test_contents, con capital 26.700 CU e inicio en 2025. audit_ref_test2025=true lo señala en la bitácora y en una extracción específica. Las tablas de test permanecen intactas.</p><p>CAP02R ya tenía 111 filas con ancla test 2025. Esta aplicación añade una y deja un acumulado de 112 entre las 878 reparaciones retrospectivas. Los diez cambios nuevos restantes tienen respaldo posterior de train. La marca es solo auditoría en la bitácora; no se añade una columna de póliza o predictor.</p><p><a href="ledger/test2025_supported_changes.csv">El nuevo caso con respaldo 2025</a> · <a href="ledger/cumulative_test2025_supported_changes.csv">Los 112 acumulados</a> · <a href="ledger/cumulative_retrospective_changes.csv">Las 878 reparaciones retrospectivas acumuladas</a></p><div class="note">La operación autorizada reconstruye una escala retrospectivamente. El respaldo posterior no era información disponible al inicio del periodo corregido. No se aprueba una preparación causal de backtests ni se confirma la unidad o la reversión contractual del nivel de capital.</div></section>
<section><h2>Lo que queda pendiente y se conserva</h2><p>Los otros 576 row_id conservan sus importes y todos los campos del inventario anterior. C48613718/C01596694 mantiene 29.300.000 CU. Su segmento inicial C00970610 conserva security_level nulo: no se imputa ni se convierte en una reparación implícita.</p><p>Se conservan íntegramente los 2.073 CAP01 y los 867 CAP02R, sin una segunda división. La rama retrospectiva reúne ahora 2.951 capitales corregidos (2.073+867+11), con 576 pendientes. La base current_dataset.json sigue byte a byte igual y mantiene sus 1.454 pendientes. Los 162.546 siniestros, sus marcas PRE00, REN00, fechas y exposición permanecen iguales.</p><p><a href="tables/pending_capitals.csv">Los 576 pendientes</a> · <a href="tables/pending_capitals.parquet">Inventario tipado</a></p></section>
<section><h2>Catálogo y linaje</h2><p>current_retrospective_dataset.json pasa a esta nueva capa después de verificarla. El catálogo CAP02R anterior y su índice de operación current_retrospective_capital_correction.json conservan su alcance histórico. current_numeric_capital_correction.json identifica específicamente CAP03R. De las once entradas del catálogo, diez referencias son exactamente iguales y solo policies_contents apunta al archivo nuevo.</p><p>Los falsos de autorización/aplicación en el fichero de propuesta D51 describen el momento de la revisión. La solicitud actual y la bitácora nueva documentan la autorización posterior. No se vuelve a seleccionar una cohorte sobre datos ya corregidos.</p><p><a href="dataset_catalog.json">Nuevo catálogo retrospectivo</a> · <a href="lineage.json">Linaje y conteos por regla</a> · <a href="authorization.json">Solicitud completa</a> · <a href="rules.json">Regla CAP03R</a></p></section>
<section><h2>Validación de cada fila</h2><p>Pasaron {v['passed']} controles propios. Se comparan todas las celdas y posiciones contra la tabla padre, con exactamente once diferencias de capital. Cada división se comprueba con Decimal y cada registro se enlaza con fuente, derivado, cohorte y autorización mediante SHA256.</p><p>Se revisan una por una las cuatro etapas originales, sus claves y los campos de riesgo completos e iguales. Los capitales ampliados normales se conservan aunque la renovación corregida quede por debajo: esta operación solo corrige escala. Restaurar old recupera exactamente la tabla padre Arrow, incluido su esquema. Repetir la transformación no divide otra vez y un importe inesperado se rechaza.</p><p>También se comprueban los 576 pendientes, el nulo de C48613718, todas las correcciones heredadas, las señales de test y los manifiestos de las corridas anteriores. Los costes del objetivo no se recalculan: siniestros, claves, fechas y componentes monetarios no cambian. No se materializa T0 ni se entrena.</p><p><a href="verification.json">Controles completos</a> · <a href="manifest.json">Manifiesto de integridad</a></p></section>
<section><h2>Reproducción y responsabilidad</h2><p>Desde C:/dev/Hakaton, usar Preparación/.venv/Scripts/python.exe con apply_numeric_capitals.py; pasar la nueva carpeta a verify_numeric_capitals.py y, después de verificar, a finalize_numeric_capitals.py. Una segunda invocación real del aplicador se comprueba sin cambios durante el cierre. Los scripts están en source_snapshot. Los informes y capas anteriores no se reescriben.</p><p>La IA preparó código y comprobaciones; el participante autorizó la lista y la operación. Verificación propia, sin revisión independiente. Protocolo/metodología 1.7 documentan el nuevo estado. La unidad de fuente y el motivo del nivel al renovar continúan sin confirmar. No se cambia CON01 ni las fechas pendientes, no hay proveedor externo, publicación o entrenamiento.</p><p>IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad; no son certificación profesional.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report,encoding='utf-8')
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.refs=[]
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ['href','src']:self.refs.append(value)
    links=Links();links.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in links.refs)
    c.dump(out/'report_verification.json',{'status':'passed_static_report_checks','local_links':len(links.refs),
        'all_11_rows_in_html':all(row_id in report for row_id in ledger.row_id),'real_browser_rendering_verified':False,'independent_validation':False})
    assert all(row_id in report for row_id in ledger.row_id)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    manifest={'created_utc':now,'type':'immutable_CAP03R_capital_correction','files':[
        {'path':path.relative_to(out).as_posix(),'sha256':c.digest(path),'bytes':path.stat().st_size}
        for path in sorted(out.rglob('*')) if path.is_file()]}
    c.dump(out/'manifest.json',manifest)
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    pointer={**parent,'workspace_relative_run':rel,'catalog_workspace_relative':rel+'/dataset_catalog.json',
        'status':'verified_retrospective_CAP03R','capital_rule':a.RULE,'capital_changes_this_layer':11,
        'capital_changes_inherited':2940,'CAP01_inherited_changes':2073,'CAP02R_inherited_changes':867,
        'total_capital_changes':2951,'retrospective_capital_changes_total':878,'pending_capitals':576,
        'later_test2025_supported_rows':112,'this_layer_test2025_supported_rows':1,
        'cohort_sha256':c.digest(out/'evidence/frozen_11_proposal.parquet'),
        'parent_catalog_index_sha256':c.digest(out/'evidence/parent_index.json'),
        'application_index_workspace_relative':a.OP_INDEX.relative_to(c.ROOT).as_posix(),
        'retrospective_only':True,'not_approved_for_cutoff_specific_backtesting':True,'approved_for_modeling':False}
    assert c.digest(a.INDEX)==protected[a.INDEX.relative_to(c.ROOT).as_posix()]
    temp=c.BASE/('numeric_index_'+uuid.uuid4().hex+'.json');c.dump(temp,pointer);temp.replace(a.INDEX)
    c.dump(a.OP_INDEX,{'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html','decision_id':decision,
        'status':'applied_verified_retrospective_only','capital_changes':11,'new_test2025_supported_rows':1,'pending':576})
    protocol['version']='1.7'
    history=protocol['inputs'].setdefault('retrospective_capital_history',[])
    if not history:history.append(protocol['inputs']['retrospective_capital_layer'])
    protocol['inputs']['retrospective_capital_layer']={'latest_rule':a.RULE,'rows_this_layer':11,'operation':'sum_insured /1000',
        'catalog_index':'../Limpieza/current_retrospective_dataset.json','default_catalog_index_unchanged':'../Limpieza/current_dataset.json',
        'retrospective_only':True,'CAP01_inherited':2073,'CAP02R_inherited':867,'total_corrected_capitals':2951,
        'retrospective_corrections_total':878,'test2025_supported_new':1,'test2025_supported_cumulative':112,
        'pending_in_this_layer':576,'pending_in_default_layer':1454,'C48613718_unchanged_capital_CU':29300000,
        'normal_midterm_capitals_preserved':True,'test_rows_changed':0,'all_other_fields_preserved':True,
        'source_unit_confirmation':False,'actual_contract_level_reset_confirmation':False,'automatic_expansion':False,
        'use_in_cutoff_specific_backtests':'Not approved; later evidence unavailable at corrected-period inception.',
        'audit_marker':'audit_ref_test2025 in ledger only; no added predictor or policy column.',
        'report':'../Limpieza/'+out.relative_to(c.BASE).as_posix()+'/informe.html'}
    c.dump(paths['protocol.json'],protocol)
    methodology=paths['methodology.md'].read_text('utf-8').replace(
        'Versión 1.6, con una capa retrospectiva CAP02R separada y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.',
        'Versión 1.7, con capas retrospectivas CAP02R/CAP03R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.')
    methodology+=f'''\n\n## CAP03R: once reparaciones exclusivas de escala\n\n{decision}: por autorización del participante se divide sum_insured por mil solo en las once filas de contenidos congeladas D51. La nueva capa sobre CAP02R conserva los capitales normales intermedios y posteriores. C48613718/C01596694 mantiene 29.300.000 CU y su referencia inicial mantiene security_level nulo. Quedan 576 pendientes en esta rama.\n\nC21091984/C02362784 pasa de 26.200.000 a 26.200 CU, con ancla posterior test_contents/C02964108 de 2025 (26.700 CU). Se añade una señal audit_ref_test2025 solo en bitácora; acumulado CAP02R+CAP03R de 112, con 878 reparaciones retrospectivas y 2.951 correcciones totales al incluir CAP01. La etiqueta retrospectiva y la exclusión de uso causal sin preparación por corte permanecen.\n\nLimpieza/current_retrospective_dataset.json identifica ahora CAP03R. La base current_dataset.json sigue intacta con 1.454 pendientes; el catálogo CAP02R anterior y su índice de operación se conservan. [Informe y once cambios](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html). No se corrige el nivel contractual ni se confirma su reversión, no se entrena ni se completa T0/F0.\n'''
    paths['methodology.md'].write_text(methodology,encoding='utf-8')
    for key,prefix in [('model_README.md','../Limpieza/'),('cleaning_README.md',''),('capital_rules.md','')]:
        paths[key].write_text(paths[key].read_text('utf-8').rstrip()+f'\n\n{decision}, CAP03R autorizado: once filas de contenidos /1000 sobre CAP02R, un nuevo respaldo test 2025 y 576 pendientes conservados, incluido C48613718 sin cambios. El índice retrospectivo apunta a la nueva capa; current_dataset.json permanece igual. Acumulado: 878 correcciones retrospectivas, 112 respaldadas por test 2025 y 2.951 capitales corregidos contando CAP01. [Informe y bitácora]({prefix}{out.relative_to(c.BASE).as_posix()}/informe.html). Aplicar/verificar/cerrar con apply_numeric_capitals.py, verify_numeric_capitals.py y finalize_numeric_capitals.py. Protocolo 1.7; solo escala, sin cambios en límites normales intermedios ni aprobación de backtest causal.\n',encoding='utf-8')
    state['numeric_capital_application']=record
    state['numeric_capital_discrepancy_review']['followup_application_decision']=decision
    state['numeric_capital_discrepancy_review']['eleven_row_operation_authorized_later']=True
    state['methodological_plan']['version']='1.7';state['memory_as_of']=now
    routes['week_1_numeric_capital_application_index']='Hackaton/Semana 1/Limpieza/current_numeric_capital_correction.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, CAP03R autorizado: once capitales /1000 y 576 pendientes conservados, 16 de octubre de 2026, America/Bogota\n\nEl participante autorizó dividir por mil las once filas propuestas D51 en otra capa retrospectiva, conservar originales y otros 576 pendientes incluido C48613718, señalar test 2025 y validar cada cambio. Solicitud íntegra en ../{rel}/authorization.json. La lista congelada se copia por hash y no se recalcula tras reparar. Cambia solo sum_insured en once posiciones de policies_contents. Se conservan todos los demás campos, filas, orden, nulos, tipos y metadatos; las otras diez referencias del catálogo quedan exactamente iguales. No se modifican los capitales normales anteriores o posteriores, aunque la renovación corregida sea menor que el último capital ampliado.\n\nC02362784/C21091984 pasa de 26.200.000 a 26.200 CU, con ancla posterior test_contents/C02964108 (26.700 CU, inicio 2025). Es la única nueva fila con audit_ref_test2025=true; existe extracción propia. Los diez cambios nuevos restantes tienen respaldo posterior de train. Se conserva el acumulado CAP02R de 111 señales y se añade una, total 112 entre 878 reparaciones retrospectivas. La bitácora acumulada distingue CAP02R y CAP03R. No se añade columna a las pólizas ni predictor; las tablas test permanecen intactas. Todo respaldo posterior conserva su carácter retrospectivo y no se presenta como conocido al inicio histórico.\n\nLos otros 576 pendientes se preservan exactamente como complemento de los 587 anteriores. C48613718/C01596694 conserva 29.300.000 CU; security_level sigue nulo en C00970610. Los 2.073 CAP01 y 867 CAP02R mantienen sus importes sin redivisión. La rama suma ahora 2.951 correcciones distintas y 576 pendientes. La base current_dataset.json conserva su hash y 1.454 pendientes. El índice current_retrospective_dataset.json se actualiza atómicamente después de verificar y comprobar el puntero padre; current_numeric_capital_correction.json identifica la nueva operación. CAP02R, D51, sus manifiestos e índices históricos no se reescriben.\n\nCada cambio conserva old/new, posición, tabla, fila, póliza, las cuatro etapas del capital, ancla posterior, señal 2025, divisor, regla y hashes de fuente/derivado/cohorte/autorización. Pasaron {v['passed']} controles propios: conjunto completo de diferencias exactamente autorizado, Decimal old/1000 por fila, cuatro etapas y campos de riesgo completos/equivalentes, conservación explícita de cada capital de referencia, reversión íntegra de la tabla padre Arrow, segunda transformación sin cambios y rechazo de importes inesperados. Se comprueban uno por uno los pendientes, las correcciones heredadas y la suma acumulada de señales. La segunda invocación real del CLI queda como no-op en el cierre.\n\nProtocolo/metodología 1.7 y documentos de uso explican el nuevo estado, preservando los documentos antes/después. Esta autorización corrige escala, no confirma unidad de fuente, motivo de la reversión contractual del nivel ni uso causal por corte. No se repite el diagnóstico de costes: claims, claves, fechas, exposición e importes del objetivo siguen idénticos. No se cambia CON01 ni fechas pendientes, no se materializa T0/F0 o entrena. Verificación propia asistida por IA, sin revisión independiente, proveedor externo, publicación o contacto a terceros. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad. Consultar numeric_capital_application.\n'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nCAP03R aplicado por autorización, {decision}: [informe](../{rel}/informe.html), [once cambios](../{rel}/ledger/all_capital_changes.csv). Solo once capitales de contenidos /1000 sobre CAP02R; C21091984/C02362784 usa ancla test 2025 y pasa de 26.200.000 a 26.200 CU. Quedan 576 pendientes, incluido C48613718 con 29.300.000 CU y su referencia inicial nula intacta. Se conservan los capitales normales intermedios, 2.073 CAP01, 867 CAP02R y todas las demás celdas. Acumulado de 878 reparaciones retrospectivas, 112 con ancla 2025 y 2.951 correcciones totales. current_retrospective_dataset.json avanza a CAP03R; la base current_dataset.json sigue idéntica con 1.454 pendientes. {v["passed"]} controles propios, reversión e idempotencia verificadas; protocolo 1.7. Sin confirmación de unidad o nivel contractual, preparación causal aprobada, entrenamiento o validación independiente. Ver numeric_capital_application y {decision}.\n',encoding='utf-8')
    after_docs=close/'after';after_docs.mkdir()
    for name,path in paths.items():shutil.copy2(path,after_docs/name)
    pointer_sha=c.digest(a.INDEX);operation_sha=c.digest(a.OP_INDEX)
    replay=subprocess.run([sys.executable,str(c.BASE/'apply_numeric_capitals.py')],cwd=c.ROOT,capture_output=True,text=True,check=True)
    replay_result=json.loads(replay.stdout)
    mutable=a.INDEX.relative_to(c.ROOT).as_posix()
    post=[{'check':'Actual second CLI invocation is verified no-op','passed':replay_result['status']=='already_applied_verified_noop' and replay_result['new_changes']==0},
        {'check':'Second invocation changes neither current index','passed':c.digest(a.INDEX)==pointer_sha and c.digest(a.OP_INDEX)==operation_sha},
        {'check':'All originals, prior files and baseline index unchanged','passed':all(c.digest(c.ROOT/path)==sha for path,sha in protected.items() if path!=mutable)},
        {'check':'Closed new run and previous CAP02R manifests intact','passed':a.cap.manifest_ok(out) and a.cap.manifest_ok(c.ROOT/parent['workspace_relative_run'])},
        {'check':'Retrospective pointer has 576 pending, 2951 corrections and 112 cumulative test signals','passed':pointer['pending_capitals']==576 and pointer['total_capital_changes']==2951 and pointer['later_test2025_supported_rows']==112},
        {'check':'Default protocol still points to unchanged baseline','passed':protocol['inputs']['catalog_index']=='../Limpieza/current_dataset.json'},
        {'check':'No modeling or causal backtest approval introduced','passed':not pointer['approved_for_modeling'] and pointer['not_approved_for_cutoff_specific_backtesting']}]
    assert all(item['passed'] for item in post)
    c.dump(close/'post_publication_verification.json',{'passed':len(post),'failed':0,'checks':post,'actual_second_cli':replay_result,'stderr':replay.stderr,'independent_validation':False})
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'application':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'retrospective_index_sha256':pointer_sha,'post_publication_checks':len(post),
        'documents':{path.relative_to(c.ROOT).as_posix():c.digest(path) for path in list(paths.values())+[a.INDEX,a.OP_INDEX]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),
                      'status':'applied_verified_retrospective_only','post_publication_checks':len(post)},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
