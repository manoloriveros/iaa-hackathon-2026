"""Publica el catálogo retrospectivo CAP02R y su documentación, preservando la base."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re
import shutil
import subprocess
import sys
import uuid

import apply_retrospective_capitals as a
import clean_data as c
import pandas as pd


def main(out):
    assert not (out/'manifest.json').exists(),'Corrida cerrada; no sobrescribir.'
    verification=json.loads((out/'verification.json').read_text('utf-8'))
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert verification['failed']==0 and verification['capital_changes']==867
    assert all(c.digest(out/p)==sha for p,sha in verification['verified_files'].items())
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    assert not a.INDEX.exists(),'El índice retrospectivo cambió; no sustituirlo.'
    parent=json.loads((out/'evidence/base_index.json').read_text('utf-8'))
    catalog=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT/e['workspace_relative_path'])==e['sha256'] for e in catalog.values())
    for name in ['apply_retrospective_capitals.py','verify_retrospective_capitals.py','finalize_retrospective_capitals.py','clean_data.py','correct_capitals.py']:
        assert c.digest(c.BASE/name)==c.digest(out/'source_snapshot'/name)
    s=json.loads((out/'summary.json').read_text('utf-8'));rel=out.relative_to(c.ROOT).as_posix()
    close=c.BASE/'closures'/datetime.now(timezone.utc).strftime('CAP02R_closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True,exist_ok=False)
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':c.ROOT/'RUTAS_PROYECTO.json',
        'protocol.json':c.ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md':c.ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'model_README.md':c.ROOT/'Hackaton/Semana 1/Modelado/README.md',
        'cleaning_README.md':c.BASE/'README.md','capital_rules.md':c.BASE/'CAPITALES.md'})
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    decisions=paths['DECISIONES.md'].read_text('utf-8');memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    protocol=json.loads(paths['protocol.json'].read_text('utf-8'))
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    now=datetime.now(timezone.utc).isoformat()
    record={'decision_id':decision,'rule':a.RULE,'status':'applied_verified_retrospective_only',
        'run':'../'+rel,'report':'../'+rel+'/informe.html','catalog':'../'+rel+'/dataset_catalog.json',
        'ledger':'../'+rel+'/ledger/all_capital_changes.parquet','ledger_csv':'../'+rel+'/ledger/all_capital_changes.csv',
        'test2025_supported_ledger':'../'+rel+'/ledger/test2025_supported_changes.csv',
        'pending':'../'+rel+'/tables/pending_capitals.parquet','verification':'../'+rel+'/verification.json',
        'index':'../Hackaton/Semana 1/Limpieza/current_retrospective_dataset.json',
        'capital_changes':867,'buildings_changes':430,'contents_changes':437,'test2025_supported_changes':111,
        'test2025_buildings_support':50,'test2025_contents_support':61,'pending_in_retrospective_layer':587,
        'pending_in_baseline_unchanged':1454,'CAP01_inherited_changes':2073,'total_retrospective_capital_changes':2940,
        'originals_modified':False,'baseline_catalog_modified':False,'test_tables_modified':False,'claims_modified':False,
        'dates_modified':False,'exposure_modified':False,'new_columns':0,'other_fields_changed':0,
        'retrospective_only':True,'available_at_corrected_period_inception':False,'source_units_confirmed':False,
        'automatic_expansion':False,'technical_checks':verification['passed'],'independent_validation':False,
        'operational_T0_materialized':False,'models_trained':False,'approved_for_modeling':False,
        'calendar_dates_pending':True,'CON01_activated':False,'closure':'../'+close.relative_to(c.ROOT).as_posix()}
    protocol['version']='1.6'
    protocol['inputs']['retrospective_capital_layer']={'rule':a.RULE,'rows':867,'operation':'sum_insured /1000',
        'explicit_participant_authorization':True,'catalog_index':'../Limpieza/current_retrospective_dataset.json',
        'default_catalog_index_unchanged':'../Limpieza/current_dataset.json','temporal_scope':'retrospective_only',
        'test2025_supported_rows':111,'test_rows_corrected':0,'pending_in_this_layer':587,'pending_in_default_layer':1454,
        'capital_changes_inherited_CAP01':2073,'total_corrected_capitals_in_this_layer':2940,
        'all_other_fields_preserved':True,'source_unit_confirmation':False,'automatic_expansion':False,
        'use_in_cutoff_specific_backtests':'Not approved; later policy evidence unavailable at corrected-period inception. Keep preparation by cutoff separate.',
        'audit_marker':'audit_ref_test2025 in ledger only, not a predictor or policy-table column.',
        'report':'../Limpieza/'+out.relative_to(c.BASE).as_posix()+'/informe.html'}
    ledger=pd.read_parquet(out/'ledger/all_capital_changes.parquet')
    supported=pd.read_parquet(out/'ledger/test2025_supported_changes.parquet')
    money=lambda v:f'{float(v):,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    support_table=supported[['row_id','policy_id','line','old','new','original_later_row_id','original_later_source_table','original_later_period_start']].rename(columns={
        'row_id':'Fila histórica corregida','policy_id':'Póliza','line':'Ramo','old':'Capital anterior CU','new':'Capital nuevo CU',
        'original_later_row_id':'Ancla test','original_later_source_table':'Tabla del ancla','original_later_period_start':'Inicio ancla'}).to_html(index=False,border=0,float_format=money)
    counts=pd.DataFrame(s['by_table']).to_html(index=False,border=0)
    old_total=sum(ledger.old);new_total=sum(ledger.new)
    sample=ledger.groupby('line',sort=True).head(3)
    sample_table=sample[['row_id','policy_id','old','new','original_later_row_id','audit_ref_test2025']].to_html(index=False,border=0,float_format=money)
    report=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CAP02R: 867 capitales corregidos en capa retrospectiva</title><style>body{{font:16px/1.65 system-ui,sans-serif;background:#eef3f6;color:#183243;margin:0}}main{{max-width:1300px;margin:auto;padding:26px}}header,section{{background:white;padding:24px;border-radius:12px;margin-bottom:18px}}header{{background:#15384c;color:white}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:23px}}.scroll{{overflow:auto;max-height:600px}}table{{border-collapse:collapse;font-size:13px;width:100%}}th,td{{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}}th{{background:#eef4f6;position:sticky;top:0}}a{{color:#007d72}}code{{background:#eef3f6;color:#183243;padding:2px 4px}}.note{{border-left:4px solid #b97624;background:#fff5e2;padding:12px 18px}}.metric{{font-size:21px}}</style></head><body><main>
<header><h1>CAP02R aplicado: 867 capitales /1000</h1><p>{decision} · Capa derivada retrospectiva · Autorización explícita del participante</p><p class="metric">430 edificios · 437 contenidos · 111 con respaldo de test 2025 · 587 pendientes conservados</p></header>
<section><h2>Qué cambió</h2><p>Se cambia solo sum_insured en los 867 row_id de la propuesta congelada D48. Las nuevas tablas históricas conservan exactamente esquema, metadatos, filas, orden, nulos y todos los campos ajenos al capital, incluidas las marcas REN00. Las otras nueve referencias del catálogo permanecen iguales: test, autos, claims PRE00, maestros y plantilla.</p><div class="scroll">{counts}</div><p>Los capitales seleccionados sumaban {money(old_total)} CU; ahora suman {money(new_total)} CU. Se comparan límites de periodos, con posibles pólizas repetidas; estas sumas no representan prima, coste esperado o ahorro. No se dividen primas, pérdidas, exposición, objetivo o predicciones por mil.</p><div class="scroll">{sample_table}</div></section>
<section><h2>Cómo consultar esta versión</h2><p>La capa dispone de <code>Limpieza/current_retrospective_dataset.json</code> y un catálogo completo de once tablas. <code>Limpieza/current_dataset.json</code> conserva su contenido y hash previos; por ello los lectores que usan la versión base no adoptan automáticamente una reparación respaldada por información posterior.</p><p>La versión retrospectiva hereda los 2.073 CAP01 y añade estos 867 CAP02R: 2.940 capitales corregidos y 587 pendientes. La base anterior conserva sus 2.073 correcciones y 1.454 pendientes. Los índices históricos y la revisión D48 no se reescriben.</p><div class="note">Las 867 reparaciones usan evidencia posterior al periodo corregido. En 111, el respaldo más próximo es una fila de test 2025. Esta autorización aprueba una reconstrucción retrospectiva y su operación; no confirma que esa información estuviera disponible al inicio histórico ni aprueba su uso en un backtest por fecha. La unidad sigue siendo una inferencia del proyecto.</div></section>
<section><h2>Las 111 con respaldo de test 2025</h2><p>Se identifican con <code>audit_ref_test2025=true</code> en la bitácora y en una extracción separada: 50 edificios y 61 contenidos. Todas son filas históricas de 2024. Las tablas de test no se modifican. Las otras 756 correcciones tienen anclas posteriores de train y también conservan la etiqueta retrospectiva.</p><p>La marca es solo metadato de auditoría en la bitácora. No se añade una columna a las tablas de pólizas ni se incorpora como predictor.</p><div class="scroll">{support_table}</div><p><a href="ledger/test2025_supported_changes.csv">Lista completa de las 111, CSV</a> · <a href="ledger/test2025_supported_changes.parquet">Extracción tipada</a></p></section>
<section><h2>Los otros 587 capitales permanecen pendientes</h2><p>Se conserva cada uno de los 587 row_id restantes y su importe: 163 en policies_buildings, 234 en policies_contents, 98 en test_buildings y 92 en test_contents. Incluyen las doce discrepancias numéricas excluidas del grupo retrospectivo D34. La lista no se expande mediante referencias nuevas creadas por esta reparación.</p><p>CON01 sigue sin activar, T/W permanece como estaba y las fechas siguen pendientes. Los 162.546 siniestros DUP01 y las 413 marcas PRE00 conservan su misma referencia y hash. La operación no altera el coste asignable al objetivo ni la conciliación previa.</p><p><a href="tables/pending_capitals.csv">Los 587 pendientes conservados</a> · <a href="tables/pending_capitals.parquet">Pendientes tipados</a></p></section>
<section><h2>Qué valida cada cambio</h2><p>Pasaron {verification['passed']} comprobaciones propias. El conjunto completo de diferencias se compara con las 867 posiciones autorizadas. Cada old/new se comprueba con Decimal como old/1000; restaurar old reconstruye exactamente la tabla padre Arrow, con esquema y metadatos. Una segunda transformación conserva los valores corregidos y un valor inesperado se rechaza.</p><p>Se revisan una por una las 867 anclas originales posteriores, contexto conocido e igual en los campos de D34, ausencia de solapamiento, distancia de 1–400 días y continuidad numérica. Las 111 señales se recalculan de forma independiente desde tabla y fecha del ancla. Se comprueban los 587 pendientes, los 2.073 CAP01 heredados y todos los hashes protegidos.</p><p>La bitácora por cambio guarda tabla, posición, fila, póliza, cliente, dirección, fechas, old/new, divisor, regla, referencia posterior, cociente, señal test 2025 y hashes de fuente, derivado, cohorte y autorización. Los flags false del fichero de propuesta D48 describen el estado al revisarlo; la autorización posterior se conserva por separado y en la bitácora.</p><p><a href="ledger/all_capital_changes.csv">Bitácora de los 867 cambios</a> · <a href="ledger/all_capital_changes.parquet">Bitácora tipada</a> · <a href="verification.json">Verificación completa</a> · <a href="tables/change_summary.csv">Resumen por tabla</a> · <a href="authorization.json">Solicitud íntegra</a> · <a href="rules.json">Regla CAP02R</a> · <a href="lineage.json">Linaje</a> · <a href="dataset_catalog.json">Catálogo retrospectivo</a> · <a href="manifest.json">Manifiesto SHA256</a></p></section>
<section><h2>Reproducción y límites</h2><p>Desde C:/dev/Hakaton, usar Preparación/.venv/Scripts/python.exe con apply_retrospective_capitals.py. Pasar la carpeta generada a verify_retrospective_capitals.py y, tras superar sus controles, a finalize_retrospective_capitals.py. El aplicador repetido sobre el índice retrospectivo verifica una operación sin cambios. Los scripts comprobados están en source_snapshot.</p><p>Protocolo/metodología 1.6 documentan ambas versiones sin sustituir el catálogo base. La preparación por corte temporal, F0, el objetivo T0 operativo y el modelado siguen pendientes. No hubo entrenamiento, publicación o contacto a terceros. La IA preparó código y comprobaciones; el participante autorizó esta lista. Verificación propia, sin revisión independiente.</p><p>IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan recorrido del dato, límites y responsabilidad. No acreditan confirmación de la fuente ni certificación profesional.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report,encoding='utf-8')
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ['href','src']:self.links.append(value)
    links=Links();links.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in links.links)
    c.dump(out/'report_verification.json',{'status':'passed_static_report_checks','local_links':len(links.links),
        'all_111_records_in_html':all(row_id in report for row_id in supported.row_id),
        'real_browser_rendering_verified':False,'independent_validation':False})
    assert json.loads((out/'report_verification.json').read_text('utf-8'))['all_111_records_in_html']
    manifest={'created_utc':now,'type':'immutable_CAP02R_retrospective_capital_correction','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out/'manifest.json',manifest)
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    next_pointer={**parent,'workspace_relative_run':rel,'catalog_workspace_relative':rel+'/dataset_catalog.json',
        'status':'verified_retrospective_CAP02R','capital_rule':a.RULE,'capital_changes_this_layer':867,
        'capital_changes_inherited':2073,'total_capital_changes':2940,'pending_capitals':587,
        'retrospective_only':True,'later_test2025_supported_rows':111,
        'not_approved_for_cutoff_specific_backtesting':True,'base_catalog_index_workspace_relative':(c.BASE/'current_dataset.json').relative_to(c.ROOT).as_posix(),
        'base_catalog_index_sha256':c.digest(c.BASE/'current_dataset.json'),
        'cohort_sha256':c.digest(out/'evidence/frozen_867_proposal.parquet'),'approved_for_modeling':False}
    temp=c.BASE/('retrospective_index_'+uuid.uuid4().hex+'.json');c.dump(temp,next_pointer)
    assert not a.INDEX.exists();temp.replace(a.INDEX)
    own_index=c.BASE/'current_retrospective_capital_correction.json'
    c.dump(own_index,{'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html','decision_id':decision,
        'status':'applied_verified_retrospective_only','capital_changes':867,'test2025_supported_changes':111,'pending':587})
    c.dump(paths['protocol.json'],protocol)
    methodology=paths['methodology.md'].read_text('utf-8').replace('Versión 1.5, con PRE00 y REN00 como marcas de auditoría sobre la capa DUP01/CAP01/CAT01/AGE01.',
        'Versión 1.6, con una capa retrospectiva CAP02R separada y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.')
    methodology+=f'''\n\n## CAP02R: capa retrospectiva autorizada y separada\n\n{decision}: se divide por mil sum_insured en las 867 filas congeladas de D48, 430 edificios y 437 contenidos. Se conservan originales, los 587 capitales restantes de esa lista y cada campo ajeno al capital. La capa retrospectiva hereda 2.073 CAP01 y tiene 2.940 capitales corregidos. Se consulta en Limpieza/current_retrospective_dataset.json. El índice base current_dataset.json permanece idéntico, con 1.454 pendientes en esa versión; no adopta automáticamente reparaciones apoyadas en información posterior.\n\nLas 867 anclas son posteriores al periodo corregido; 111 son de test 2025 (50 edificios y 61 contenidos, todas respaldando filas 2024). audit_ref_test2025 existe solo en bitácora y en una extracción de 111 registros. Las tablas test no cambian y no se añaden columnas de auditoría a las pólizas. La autorización de reconstrucción retrospectiva no acredita disponibilidad al inicio histórico ni aprueba su uso en backtests por corte. No se dividen prima, exposición, siniestro, etiqueta o predicción.\n\nLa bitácora registra old/new, posición, ancla posterior y hashes. Restaurar old recupera exactamente el padre; repetir no divide dos veces. [Informe CAP02R](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html). Los 587 continúan pendientes únicamente en esta rama; confirmar unidad/contrato sigue abierto. No se amplía la cohorte, no se activa CON01, no se cambian fechas ni se completa T0/F0 o entrenamiento.\n'''
    paths['methodology.md'].write_text(methodology,encoding='utf-8')
    for key,label in [('model_README.md','../Limpieza/'),('cleaning_README.md','')]:
        paths[key].write_text(paths[key].read_text('utf-8').rstrip()+f'\n\n{decision}, CAP02R autorizado en una capa retrospectiva separada: 867 capitales /1000, 111 con ancla test 2025 y 587 pendientes conservados. Consultar {label}current_retrospective_dataset.json para esa versión. current_dataset.json conserva la base anterior (1.454 pendientes), sin adoptar información futura de forma automática. [Informe y bitácora]({label}{out.relative_to(c.BASE).as_posix()}/informe.html). Protocolo 1.6; no se aprueba uso en backtests por fecha ni se entrena.\n',encoding='utf-8')
    paths['capital_rules.md'].write_text(paths['capital_rules.md'].read_text('utf-8').rstrip()+f'\n\n## CAP02R, reconstrucción retrospectiva autorizada\n\n{decision} aplica /1000 a la lista congelada de 867 filas D48 en una capa separada; no amplía CAP01 ni reemplaza su índice. [Informe]({out.relative_to(c.BASE).as_posix()}/informe.html). Índice propio current_retrospective_dataset.json; base current_dataset.json intacta. Se señalan las 111 referencias test 2025 en ledger/test2025_supported_changes y audit_ref_test2025 dentro de la bitácora. Las pólizas no reciben columnas nuevas. Quedan 587 pendientes en la rama retrospectiva; la base conserva sus 1.454. Se valida cada old/new, reversión, idempotencia, ancla y hash. Aplicador apply_retrospective_capitals.py, verificador verify_retrospective_capitals.py y cierre finalize_retrospective_capitals.py. La autorización está en la corrida y no acredita disponibilidad causal histórica.\n',encoding='utf-8')
    state['retrospective_capital_application']=record
    state['pending_capital_review']['followup_application_decision']=decision
    state['pending_capital_review']['retrospective_operation_authorized_later']=True
    state['methodological_plan']['version']='1.6';state['memory_as_of']=now
    routes['week_1_retrospective_prepared_data_index']='Hackaton/Semana 1/Limpieza/current_retrospective_dataset.json'
    routes['week_1_retrospective_capital_application_index']='Hackaton/Semana 1/Limpieza/current_retrospective_capital_correction.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, CAP02R autorizado: 867 capitales /1000 en una rama retrospectiva, 16 de octubre de 2026, America/Bogota\n\nEl participante autorizó aplicar la propuesta D48 de 867 filas en una capa derivada retrospectiva, preservar originales y otros 587 pendientes y señalar 111 con respaldo test 2025. La solicitud íntegra está en ../{rel}/authorization.json. Se congela el Parquet D48 por SHA256, sin volver a seleccionar después de reparar. Solo sum_insured cambia en 430 filas de policies_buildings y 437 de policies_contents. Las nueve referencias restantes del catálogo quedan idénticas, incluidas todas las tablas test, autos y claims PRE00. No se añaden columnas, cambian fechas, primas, exposición, costes, estados, marcas, IDs, orden, nulos, tipos o metadatos. Los originales y todas las corridas previas conservan sus hashes.\n\nLa capa completa se consulta por Limpieza/current_retrospective_dataset.json y el índice de operación current_retrospective_capital_correction.json. Se conserva byte a byte current_dataset.json como base previa: la solicitud autoriza una reconstrucción retrospectiva, por lo que se evita que los lectores por defecto la adopten como información disponible en cada corte. La base conserva 2.073 CAP01 y 1.454 pendientes; la rama retrospectiva hereda esos CAP01, suma 867 CAP02R y tiene 2.940 correcciones distintas con 587 pendientes. No confundir ambas cifras de pendientes ni reescribir índices históricos CAP01/D48.\n\nTodas las 867 referencias son posteriores al periodo reparado. Las 111 basadas en test 2025 son 50 edificios y 61 contenidos y respaldan filas históricas de 2024; ninguna fila test cambia. audit_ref_test2025 es un bool de bitácora, con extracción CSV/Parquet de esas 111, nunca una columna nueva de pólizas o predictor. Las otras 756 usan referencias posteriores de train. La operación no confirma que el capital correcto estuviera disponible al cotizar ni la unidad del sistema generador. No se aprueba su uso en backtests por fecha; la preparación por corte sigue separada.\n\nLos 587 pendientes se conservan íntegramente por row_id e importe: 163 policies_buildings, 234 policies_contents, 98 test_buildings y 92 test_contents. Incluyen las doce discrepancias numéricas excluidas en D48. No se expande la cohorte en cascada por referencias que esta reparación cree. La bitácora por cada cambio conserva old/new, divisor, posición, periodo, póliza/cliente/dirección, ancla posterior, cociente, señal 2025, regla y hashes de archivo fuente/derivado/cohorte/autorización. Los flags false de autorización y aplicación en el fichero D48 congelado describen la revisión anterior; la autorización humana posterior consta aquí y en la nueva bitácora.\n\nPasaron {verification['passed']} controles propios: diferencia completa de posiciones autorizadas, esquema y todos los campos ajenos al capital, Decimal old/1000, reversión íntegra de la tabla padre Arrow, segunda transformación sin doble división, rechazo de valores inesperados, preservación de los 587 pendientes y 2.073 CAP01, anclas originales posteriores una a una y señales test 2025 recalculadas desde tabla/fecha. La publicación verifica otra vez hashes de archivos candidatos y fuentes, y el segundo CLI real queda registrado como no-op en el cierre. No se repite el diagnóstico del objetivo: claims, claves, fechas, exposición y todos sus campos de asignación permanecen idénticos, por lo que la reparación no cambia los componentes de coste.\n\nProtocolo/metodología 1.6, READMEs y CAPITALES.md explican las dos ramas; versiones anteriores y posteriores quedan en el cierre. El catálogo retrospectivo se publica por reemplazo atómico solo después de verificar, sin sustituir la base. Catálogo base, reglas heredadas DUP01/REN00/PRE00, fechas pendientes y CON01 sin activar permanecen como estaban. No se materializa T0, no se aprueba F0/modelado, no hay entrenamiento, publicación o proveedor externo. Verificación propia asistida por IA, sin revisión independiente. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad. Consultar retrospective_capital_application.\n'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nCAP02R aplicado por autorización, {decision}: [informe](../{rel}/informe.html), [catálogo retrospectivo](../Hackaton/Semana 1/Limpieza/current_retrospective_dataset.json). Se dividen por mil 867 filas D48 (430 edificios, 437 contenidos); 111 usan respaldo posterior test 2025 (50/61), señaladas en bitácora y extracción propia. Las tablas test no cambian. Se conservan originales, todos los campos ajenos al capital, 2.073 CAP01 y 587 pendientes en esta rama. Total retrospectivo: 2.940 capitales corregidos. La base current_dataset.json permanece idéntica, con sus 1.454 pendientes, para no adoptar reconstrucción futura como preparación por corte. {verification["passed"]} controles propios, reversión e idempotencia verificadas. Protocolo 1.6; no aprobación para backtests por fecha, T0/F0 o entrenamiento. Consultar retrospective_capital_application y {decision}.\n',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,p in paths.items():shutil.copy2(p,after/name)
    replay_hash=c.digest(a.INDEX)
    replay=subprocess.run([sys.executable,str(c.BASE/'apply_retrospective_capitals.py')],cwd=c.ROOT,capture_output=True,text=True,check=True)
    replay_result=json.loads(replay.stdout)
    post=[{'check':'Actual second CLI invocation changes nothing','passed':replay_result['status']=='already_applied_verified_noop' and replay_result['new_changes']==0},
        {'check':'Retrospective index unchanged by second invocation','passed':c.digest(a.INDEX)==replay_hash},
        {'check':'Baseline index, all originals and protected parent/review files unchanged','passed':all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())},
        {'check':'Closed application manifest intact','passed':a.cap.manifest_ok(out)},
        {'check':'No test/claims catalog replacement introduced','passed':all(catalog[name]==json.loads((out/'evidence/base_catalog.json').read_text('utf-8'))[name] for name in ['test_buildings','test_contents','test_motor','claims'])},
        {'check':'Protocol defaults to base and describes retrospective layer separately','passed':protocol['inputs']['catalog_index']=='../Limpieza/current_dataset.json' and protocol['inputs']['retrospective_capital_layer']['rows']==867},
        {'check':'No global modeling or cutoff-backtest approval','passed':not next_pointer['approved_for_modeling'] and next_pointer['not_approved_for_cutoff_specific_backtesting']}]
    assert all(x['passed'] for x in post)
    c.dump(close/'post_publication_verification.json',{'passed':len(post),'failed':0,'checks':post,'actual_second_cli':replay_result,'stderr':replay.stderr,'independent_validation':False})
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'application':record,
        'manifest_sha256':c.digest(out/'manifest.json'),'retrospective_index_sha256':c.digest(a.INDEX),
        'base_catalog_index_sha256':c.digest(c.BASE/'current_dataset.json'),'post_publication_checks':len(post),
        'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[a.INDEX,own_index]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),
        'status':'applied_verified_retrospective_only','post_publication_checks':len(post)},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
