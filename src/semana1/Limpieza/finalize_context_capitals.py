"""Activa CAP04R solo tras comprobar toda la capa y el puntero padre."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import sys
import uuid
import apply_context_capitals as a
import clean_data as c
import pandas as pd

def main(out):
    assert not (out/'manifest.json').exists(),'Corrida cerrada; no sobrescribir.'
    v=json.loads((out/'verification.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==0 and v['capital_changes']==109 and v['pending_after']==467
    assert all(c.digest(out/path)==sha for path,sha in v['verified_files'].items())
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    for name in ['apply_context_capitals.py','verify_context_capitals.py','finalize_context_capitals.py','clean_data.py','correct_capitals.py']:
        assert c.digest(c.BASE/name)==c.digest(out/'source_snapshot'/name)
    assert not a.OP_INDEX.exists(),'Ya existe índice de esta operación.'
    parent=json.loads((out/'evidence/parent_index.json').read_text('utf-8'));cat=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT/e['workspace_relative_path'])==e['sha256'] for e in cat.values())
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    close=c.BASE/'closures'/datetime.now(timezone.utc).strftime('CAP04R_closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':c.ROOT/'RUTAS_PROYECTO.json',
        'protocol.json':c.ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md':c.ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'model_README.md':c.ROOT/'Hackaton/Semana 1/Modelado/README.md',
        'cleaning_README.md':c.BASE/'README.md','capital_rules.md':c.BASE/'CAPITALES.md'})
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8');decisions=paths['DECISIONES.md'].read_text('utf-8')
    protocol=json.loads(paths['protocol.json'].read_text('utf-8'));assert protocol['version']=='1.7'
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    record={'decision_id':decision,'rule':a.RULE,'status':'applied_verified_retrospective_only','run':'../'+rel,
        'report':'../'+rel+'/informe.html','catalog':'../'+rel+'/dataset_catalog.json',
        'ledger':'../'+rel+'/ledger/all_capital_changes.parquet','ledger_csv':'../'+rel+'/ledger/all_capital_changes.csv',
        'test2025_ledger':'../'+rel+'/ledger/test2025_supported_changes.csv',
        'cumulative_test2025_ledger':'../'+rel+'/ledger/cumulative_test2025_supported_changes.csv',
        'pending':'../'+rel+'/tables/pending_capitals.parquet','verification':'../'+rel+'/verification.json',
        'index':'../Hackaton/Semana 1/Limpieza/current_context_capital_correction.json',
        'capital_changes':109,'changes_by_table':{'policies_buildings':75,'policies_contents':34},
        'new_test2025_supported_rows':17,'new_test2025_by_line':{'buildings':6,'contents':11},
        'pending_in_retrospective_layer':467,'CAP01_inherited_changes':2073,'CAP02R_inherited_changes':867,
        'CAP03R_inherited_changes':11,'retrospective_changes_total':987,'test2025_supported_cumulative_rows':129,
        'total_corrected_capitals':3060,'baseline_pending_unchanged':1454,'originals_modified':False,
        'other_fields_changed':0,'new_columns':0,'claims_modified':False,'test_tables_modified':False,'dates_modified':False,
        'B19256617_B00962235_pending_capital_CU':377000000,'C48613718_pending_capital_CU':29300000,
        'retrospective_only':True,'source_units_confirmed':False,'automatic_expansion':False,
        'technical_checks':v['passed'],'independent_validation':False,'models_trained':False,'approved_for_modeling':False,
        'operational_T0_materialized':False,'CON01_activated':False,'calendar_dates_pending':True,
        'closure':'../'+close.relative_to(c.ROOT).as_posix()}
    ledger=pd.read_parquet(out/'ledger/all_capital_changes.parquet');signal=ledger.loc[ledger.audit_ref_test2025]
    columns=['row_id','policy_id','line','old','new','prior_capital_CU','prior_changed_fields','later_row_id','later_capital_CU','audit_ref_test2025']
    money=lambda x:f'{float(x):,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    table=ledger[columns].to_html(index=False,border=0,float_format=money)
    signal_table=signal[['row_id','policy_id','line','old','new','later_source_table','later_row_id','later_period_start','later_capital_CU']].to_html(index=False,border=0,float_format=money)
    report=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CAP04R: 109 capitales divididos por mil</title><style>body{{font:16px/1.65 system-ui,sans-serif;background:#eef3f6;color:#183243;margin:0}}main{{max-width:1400px;margin:auto;padding:25px}}header,section{{padding:24px;background:white;border-radius:12px;margin-bottom:18px}}header{{background:#17394d;color:white}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:23px}}table{{border-collapse:collapse;font-size:13px;width:100%}}th,td{{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}}th{{position:sticky;top:0;background:#edf3f6}}.scroll{{overflow:auto;max-height:650px}}a{{color:#007d72}}.note{{border-left:4px solid #b47725;background:#fff5e2;padding:12px 18px}}</style></head><body><main>
<header><h1>CAP04R aplicado: 109 capitales divididos por mil</h1><p>{decision} · Nueva capa retrospectiva sobre CAP03R · Lista D53 autorizada</p><p>75 edificios · 34 contenidos · 17 respaldos de test 2025 · 467 pendientes conservados</p></header>
<section><h2>Cada cambio autorizado</h2><p>Solo cambia sum_insured en los 109 row_id de la propuesta congelada D53. Se conservan filas, orden, esquema, metadatos y todos los demás valores de policies_buildings y policies_contents. Las otras nueve referencias del catálogo siguen exactamente iguales.</p><div class="scroll" id="allChanges">{table}</div><p>Los límites afectados sumaban {money(ledger.old.sum())} CU y ahora suman {money(ledger.new.sum())} CU. Esta diferencia no es una reducción de pérdidas, primas o coste esperado: los límites se repiten por periodo y no se interpretan como suma de riesgo independiente.</p><p><a href="ledger/all_capital_changes.csv">Bitácora de los 109 cambios, CSV</a> · <a href="ledger/all_capital_changes.parquet">Bitácora tipada</a> · <a href="ledger/policies_buildings_sum_insured.csv">75 edificios</a> · <a href="ledger/policies_contents_sum_insured.csv">34 contenidos</a></p></section>
<section><h2>Los 17 respaldos de test 2025</h2><p>Seis edificios y once contenidos llevan audit_ref_test2025=true en la bitácora y una extracción específica. Las tablas test no cambian. Los otros 92 cambios tienen respaldo posterior de train.</p><div class="scroll" id="testSignals">{signal_table}</div><p><a href="ledger/test2025_supported_changes.csv">Los 17 nuevos respaldos 2025</a> · <a href="ledger/cumulative_test2025_supported_changes.csv">Los 129 acumulados</a> · <a href="ledger/cumulative_retrospective_changes.csv">Las 987 correcciones retrospectivas acumuladas</a></p><div class="note">Todos los respaldos eran posteriores al inicio del periodo corregido. La capa es retrospectiva y no constituye preparación causal aprobada para backtests. La señal queda en bitácora, sin añadir columnas a pólizas ni predictores.</div></section>
<section><h2>Se conservan los cambios de contexto</h2><p>Los 31 casos T→W se corrigen mediante el respaldo posterior W→W, sin unificar códigos ni activar CON01. Otros 44 edificios y 34 contenidos cambian de dirección frente al capital anterior. La operación conserva esos cambios y el nivel propio del nuevo riesgo; no copia el límite del inmueble previo.</p><p>B13523069 pasa de 382.000.000 a 382.000 CU, con referencia posterior 393.000 y límite anterior 105.000. B03817872 pasa de 185.000.000 a 185.000, aunque el inmueble previo tuviera 301.000. C04555093 pasa de 24.400.000 a 24.400, con 24.900 posteriores.</p><p>B19256617/B01414378 pasa de 388.000.000 a 388.000 CU, con respaldo original B02040322 de 400.000. Su fila B00962235 conserva 377.000.000 CU pendiente fuera del grupo: no se genera una cascada.</p><p>Los nulos de smoke_alarms de tres riesgos anteriores permanecen intactos. Contexto igual se refiere a los campos D34 explícitos de la revisión: days_unoccupied cambia en 68 pares informados y otro tiene faltante. No se afirma que todos los factores tarifarios o el riesgo físico sean constantes. El capital no se anualiza por exposición.</p></section>
<section><h2>467 pendientes y correcciones heredadas</h2><p>Los otros 467 conservan sus capitales y todos los campos del inventario anterior, incluido C48613718/C01596694 con 29.300.000 CU y su referencia C00970610 con security_level nulo. Se conservan los 2.073 CAP01, 867 CAP02R y once CAP03R sin redivisión.</p><p>La rama suma 3.060 capitales corregidos: 2.073 CAP01 y 987 retrospectivos (867+11+109). Hay 129 respaldos de test 2025 acumulados (111+1+17). La base current_dataset.json permanece idéntica con 1.454 pendientes. No se modifican primas, exposición, fechas, siniestros, marcas REN00/PRE00 u objetivo.</p><p><a href="tables/pending_capitals.csv">Los 467 pendientes</a> · <a href="tables/pending_capitals.parquet">Inventario tipado</a></p></section>
<section><h2>Validación de datos y linaje</h2><p>Pasaron {v['passed']} controles propios. Las dos tablas se comparan completas contra CAP03R: solo aparecen las 109 diferencias autorizadas en sum_insured. Cada fila conserva old/new, posición, identidad, comparaciones anteriores, ancla posterior, señal test, regla, divisor y hashes de fuente, derivado, cohorte y autorización.</p><p>Cada división se comprueba con Decimal. Se releen los campos de las referencias publicadas y los importes originales posteriores; restaurar old recupera exactamente las tablas padre Arrow y su esquema. Una segunda transformación no cambia valores y un importe inesperado se rechaza. También se prueba una segunda invocación real del CLI al cerrar.</p><p>Los falsos de autorización/aplicación en la propuesta histórica D53 se conservan. La solicitud actual y la bitácora de CAP04R registran la autorización posterior. No se recalcula ni amplía la cohorte.</p><p><a href="dataset_catalog.json">Nuevo catálogo</a> · <a href="lineage.json">Linaje</a> · <a href="authorization.json">Solicitud completa</a> · <a href="rules.json">Regla CAP04R</a> · <a href="verification.json">Todas las comprobaciones</a> · <a href="manifest.json">Manifiesto SHA256</a></p></section>
<section><h2>Reproducción y alcance</h2><p>Desde C:/dev/Hakaton, usar Preparación/.venv/Scripts/python.exe con apply_context_capitals.py. Pasar la carpeta generada a verify_context_capitals.py y, tras verificar, a finalize_context_capitals.py. Los cinco scripts y las evidencias están archivados. current_retrospective_dataset.json avanza a CAP04R; current_context_capital_correction.json identifica esta operación. Los índices de operación CAP02R/CAP03R y las corridas anteriores permanecen intactos.</p><p>Protocolo y metodología 1.8. La IA preparó código y verificaciones propias; el participante autorizó esta lista y operación. Sin validación independiente ni renderizado de navegador acreditados. Continúan pendientes la confirmación de unidades por la fuente, fechas y disponibilidad para modelar. No se materializa T0/F0, entrena, publica, contacta a terceros o llama a un proveedor externo.</p><p>IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad; no son certificación profesional.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report,encoding='utf-8')
    class ReportCheck(HTMLParser):
        def __init__(self):super().__init__();self.refs=[];self.table_rows=[];self.rows=0
        def handle_starttag(self,tag,attrs):
            self.refs += [val for key,val in attrs if key in ['href','src']]
            if tag=='table':self.rows=0
            if tag=='tr':self.rows+=1
        def handle_endtag(self,tag):
            if tag=='table':self.table_rows.append(self.rows-1)
    parser=ReportCheck();parser.feed(report)
    assert parser.table_rows==[109,17] and all(ref=='manifest.json' or (out/ref).is_file() for ref in parser.refs)
    assert all(row_id in report for row_id in ledger.row_id)
    c.dump(out/'report_verification.json',{'status':'passed_static_report_checks','tables_actual_data_rows':parser.table_rows,
        'local_links':len(parser.refs),'all_109_ids_present':True,'real_browser_rendering_verified':False,'independent_validation':False})
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'manifest.json',{'created_utc':now,'type':'immutable_CAP04R_capital_correction','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    pointer={**parent,'workspace_relative_run':rel,'catalog_workspace_relative':rel+'/dataset_catalog.json',
        'status':'verified_retrospective_CAP04R','capital_rule':a.RULE,'capital_changes_this_layer':109,'capital_changes_inherited':2951,
        'CAP01_inherited_changes':2073,'CAP02R_inherited_changes':867,'CAP03R_inherited_changes':11,
        'total_capital_changes':3060,'retrospective_capital_changes_total':987,'pending_capitals':467,
        'later_test2025_supported_rows':129,'this_layer_test2025_supported_rows':17,
        'cohort_sha256':c.digest(out/'evidence/frozen_109_proposal.parquet'),
        'parent_catalog_index_sha256':c.digest(out/'evidence/parent_index.json'),
        'application_index_workspace_relative':a.OP_INDEX.relative_to(c.ROOT).as_posix(),
        'retrospective_only':True,'not_approved_for_cutoff_specific_backtesting':True,'approved_for_modeling':False}
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    temp=c.BASE/('context_index_'+uuid.uuid4().hex+'.json');c.dump(temp,pointer);temp.replace(a.INDEX)
    c.dump(a.OP_INDEX,{'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html','decision_id':decision,
        'status':'applied_verified_retrospective_only','capital_changes':109,'new_test2025_supported_rows':17,'pending':467})
    protocol['version']='1.8';protocol['inputs'].setdefault('retrospective_capital_history',[]).append(protocol['inputs']['retrospective_capital_layer'])
    protocol['inputs']['retrospective_capital_layer']={'latest_rule':a.RULE,'rows_this_layer':109,'operation':'sum_insured /1000',
        'catalog_index':'../Limpieza/current_retrospective_dataset.json','default_catalog_index_unchanged':'../Limpieza/current_dataset.json',
        'retrospective_only':True,'CAP01_inherited':2073,'CAP02R_inherited':867,'CAP03R_inherited':11,'total_corrected_capitals':3060,
        'retrospective_corrections_total':987,'test2025_supported_new':17,'test2025_supported_cumulative':129,
        'pending_in_this_layer':467,'pending_in_default_layer':1454,'C48613718_unchanged_capital_CU':29300000,
        'B19256617_B00962235_unchanged_capital_CU':377000000,'test_rows_changed':0,'all_other_fields_preserved':True,
        'source_unit_confirmation':False,'automatic_expansion':False,'T_W_semantic_merge':False,
        'use_in_cutoff_specific_backtests':'Not approved; later evidence unavailable at corrected-period inception.',
        'audit_marker':'audit_ref_test2025 in ledger only; no added predictor or policy column.',
        'report':'../Limpieza/'+out.relative_to(c.BASE).as_posix()+'/informe.html'}
    c.dump(paths['protocol.json'],protocol)
    note=f'''\n\n{decision}, CAP04R autorizado: 109 filas D53 /1000 sobre CAP03R (75 edificios y 34 contenidos), 17 respaldos posteriores de test 2025 (6/11) y 467 pendientes preservados. B19256617/B00962235 mantiene 377.000.000 CU y C48613718/C01596694, 29.300.000. La nueva capa conserva los demás campos, T/W y las reparaciones anteriores. Acumulado de 987 correcciones retrospectivas, 129 respaldos test 2025 y 3.060 correcciones contando CAP01. La base sigue intacta con 1.454 pendientes. Protocolo 1.8; reconstrucción retrospectiva sin aprobación causal por corte. '''
    methodology=paths['methodology.md'].read_text('utf-8').replace('Versión 1.7, con capas retrospectivas CAP02R/CAP03R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.',
        'Versión 1.8, con capas retrospectivas CAP02R/CAP03R/CAP04R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.')
    paths['methodology.md'].write_text(methodology.rstrip()+note+f'[Informe y bitácora](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html).\n',encoding='utf-8')
    for key,prefix in [('model_README.md','../Limpieza/'),('cleaning_README.md',''),('capital_rules.md','')]:
        paths[key].write_text(paths[key].read_text('utf-8').rstrip()+note+f'[Informe y bitácora]({prefix}{out.relative_to(c.BASE).as_posix()}/informe.html). Scripts: apply_context_capitals.py, verify_context_capitals.py y finalize_context_capitals.py; índice de operación current_context_capital_correction.json.\n',encoding='utf-8')
    state['context_capital_application']=record;state['context_capital_review']['followup_application_decision']=decision
    state['context_capital_review']['109_row_operation_authorized_later']=True
    state['methodological_plan']['version']='1.8';state['memory_as_of']=now
    routes['week_1_context_capital_application_index']='Hackaton/Semana 1/Limpieza/current_context_capital_correction.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, CAP04R autorizado: 109 capitales /1000 y 467 pendientes conservados, 16 de octubre de 2026, America/Bogota

El participante autorizó dividir por mil exactamente las 109 filas propuestas D53 en otra capa retrospectiva, preservar originales y otros 467 pendientes, señalar los 17 respaldos test 2025 y documentar/validar cada cambio. Solicitud íntegra en ../{rel}/authorization.json. Se copia la lista por hash y no se vuelve a seleccionar. Solo cambia sum_insured en 75 posiciones de policies_buildings y 34 de policies_contents. Se conservan todas las demás celdas, filas, orden, nulos, tipos y metadatos; las otras nueve referencias completas del catálogo permanecen iguales.

Las 17 señales nuevas audit_ref_test2025 están solo en bitácora y extracción específica, seis edificios y once contenidos. Las otras 92 tienen respaldo posterior de train, también futuro al inicio del periodo corregido. Las tablas test no cambian. El acumulado de CAP02R/CAP03R/CAP04R tiene 987 reparaciones retrospectivas y 129 respaldos test 2025 (111+1+17). Con 2.073 CAP01, se conservan 3.060 correcciones distintas. No se añade predictor o columna de póliza, no se aprueba uso causal por corte y no se confirma la unidad de fuente.

Los otros 467 pendientes son el complemento exacto de los 576 anteriores, con todos sus campos y orden preservados. B19256617/B01414378 pasa de 388.000.000 a 388.000 con ancla original B02040322 de 400.000. Su fila B00962235 permanece pendiente con 377.000.000, sin cascada. C48613718/C01596694 conserva 29.300.000 y C00970610 conserva security_level nulo. Los 31 cambios T/W no activan CON01; las mudanzas, alarmas y faltantes se mantienen. La igualdad D34 es parcial respecto de todos los factores tarifarios: days_unoccupied tiene 68 diferencias informadas y un par con faltante, sin reparación de esos campos.

Cada registro conserva old/new, posición, tabla/fila/póliza, contexto previo, ancla posterior, bandera 2025, divisor/regla y hashes de fuente/derivado/cohorte/autorización. Pasaron {v['passed']} controles propios: conjunto completo de diferencias exactamente autorizado, división Decimal por fila, relectura de campos e importes de las referencias, preservación de todos los pendientes y reparaciones heredadas, reversión exacta de ambas tablas Arrow, segunda transformación sin cambios y rechazo de importes inesperados. El cierre comprueba además una segunda invocación real del CLI sin cambios. El informe estático contiene las 109 filas y los 17 respaldos, con enlaces locales comprobados; no se acredita renderizado de navegador o revisión independiente.

current_retrospective_dataset.json avanza atómicamente a CAP04R solo después de verificar la capa y el puntero padre. current_context_capital_correction.json identifica esta operación; los índices de operación CAP02R/CAP03R y D53 se conservan. La base current_dataset.json sigue byte a byte igual, con 1.454 pendientes. Protocolo/metodología 1.8, documentos antes/después archivados. Los 162.546 siniestros y componentes del objetivo, fechas y exposición no cambian; no se repite diagnóstico de costes ni se entrena o materializa T0/F0. La IA preparó código y controles propios; el participante autorizó esta lista. Sin proveedor externo, publicación, contacto a terceros o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad. Consultar context_capital_application.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+note+f'[Informe](../{rel}/informe.html), [109 cambios](../{rel}/ledger/all_capital_changes.csv). {v["passed"]} controles propios, reversión e idempotencia verificadas. Los 17 respaldos test tienen extracción propia y señal solo en bitácora. current_retrospective_dataset.json avanza a CAP04R; current_context_capital_correction.json conserva la operación. Sin cambios en fechas, siniestros o CON01, sin entrenamiento o validación independiente. Ver context_capital_application y {decision}.\n',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,path in paths.items():shutil.copy2(path,after/name)
    pointer_sha=c.digest(a.INDEX);op_sha=c.digest(a.OP_INDEX)
    replay=subprocess.run([sys.executable,str(c.BASE/'apply_context_capitals.py')],cwd=c.ROOT,capture_output=True,text=True,check=True)
    replay_result=json.loads(replay.stdout);mutable=a.INDEX.relative_to(c.ROOT).as_posix()
    post=[{'check':'Actual second CLI invocation is verified no-op','passed':replay_result['status']=='already_applied_verified_noop' and replay_result['new_changes']==0},
        {'check':'No-op preserves both current indexes','passed':c.digest(a.INDEX)==pointer_sha and c.digest(a.OP_INDEX)==op_sha},
        {'check':'Originals, parent files, baseline and prior operation/review indexes unchanged','passed':all(c.digest(c.ROOT/path)==sha for path,sha in protected.items() if path!=mutable)},
        {'check':'Closed new and parent/review manifests intact','passed':a.cap.manifest_ok(out) and a.cap.manifest_ok(c.ROOT/parent['workspace_relative_run']) and a.cap.manifest_ok(a.REVIEW)},
        {'check':'Pointer counts 467/3060/129 correct','passed':pointer['pending_capitals']==467 and pointer['total_capital_changes']==3060 and pointer['later_test2025_supported_rows']==129},
        {'check':'Default protocol baseline unchanged and no modeling approval','passed':protocol['inputs']['catalog_index']=='../Limpieza/current_dataset.json' and not pointer['approved_for_modeling'] and pointer['not_approved_for_cutoff_specific_backtesting']},
        {'check':'All report links resolve after sealing','passed':all((out/ref).is_file() for ref in parser.refs)}]
    assert all(x['passed'] for x in post)
    c.dump(close/'post_publication_verification.json',{'passed':len(post),'failed':0,'checks':post,'actual_second_cli':replay_result,'stderr':replay.stderr,'independent_validation':False})
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'application':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'retrospective_index_sha256':pointer_sha,'post_publication_checks':len(post),
        'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[a.INDEX,a.OP_INDEX]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),
        'status':'applied_verified_retrospective_only','post_publication_checks':len(post)},ensure_ascii=False))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
