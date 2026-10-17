"""Publica PRE00 verificado, conserva evidencia y actualiza memoria sin reescribir historia."""
from datetime import datetime, timezone
from pathlib import Path
import html
import json
import re
import shutil
import subprocess
import sys
import uuid

import clean_data as c
import apply_prehistory_audit as a
import pandas as pd


def main(out):
    assert not (out/'manifest.json').exists(), 'Corrida cerrada; no sobrescribir.'
    verification=json.loads((out/'verification.json').read_text('utf-8'))
    consumer=json.loads((out/'consumer_verification.json').read_text('utf-8'))
    assert verification['failed']==0 and verification['passed']>0 and consumer['periods_checked']==3035950
    assert all(c.digest(c.ROOT/p)==sha for p,sha in consumer['files'].items())
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    assert a.manifest_ok(a.REVIEW)
    parent=json.loads((out/'evidence/parent_index.json').read_text('utf-8'))
    active=c.BASE/'current_dataset.json'
    rel=out.relative_to(c.ROOT).as_posix()
    close=c.BASE/'closures'/datetime.now(timezone.utc).strftime('PRE00_closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True,exist_ok=False)
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':c.ROOT/'RUTAS_PROYECTO.json',
        'protocol.json':c.ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md':c.ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'model_README.md':c.ROOT/'Hackaton/Semana 1/Modelado/README.md','cleaning_README.md':c.BASE/'README.md'})
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decisions=paths['DECISIONES.md'].read_text('utf-8')
    protocol=json.loads(paths['protocol.json'].read_text('utf-8'))
    routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    now=datetime.now(timezone.utc).isoformat()
    application={'decision_id':decision,'rule':'PRE00','status':'applied_verified_audit_only',
        'column':a.FLAG,'run':'../'+rel,'report':'../'+rel+'/informe.html',
        'catalog':'../'+rel+'/dataset_catalog.json','ledger':'../'+rel+'/ledger/pre00_marked_claims.parquet',
        'ledger_csv':'../'+rel+'/ledger/pre00_marked_claims.csv','verification':'../'+rel+'/verification.json',
        'consumer_verification':'../'+rel+'/consumer_verification.json',
        'financial_reconciliation':'../'+rel+'/financial_reconciliation.json',
        'assignment':'../'+rel+'/tables/claim_period_assignment.parquet',
        'claims_preserved':162546,'marked_claims':413,'unmarked_claims':162133,'accepted_marked_claims':409,
        'marked_net_accepted_CU':'1721459.84','assigned_net_accepted_CU':'741156868.43',
        'assigned_claim_records':162133,'original_cells_changed':0,'claims_removed':0,'dates_changed':False,
        'amounts_changed':False,'statuses_changed':False,'other_10_catalog_entries_unchanged':True,
        'all_marked_claims_outside_current_period_target':True,'target_guard_version':'1.0',
        'predictor_exclusion_verified':True,'source_coverage_confirmed':False,'automatic_expansion':False,
        'technical_checks':verification['passed'],'current_periods_consumer_checked':3035950,
        'operational_T0_materialized':False,'models_trained':False,'independent_validation':False,
        'calendar_dates_pending':True,'pending_capitals_unchanged':1454,'CON01_activated':False,
        'closure':'../'+close.relative_to(c.ROOT).as_posix()}
    protocol['version']='1.5'
    protocol['inputs']['prehistory_audit']={'rule':'PRE00','column':a.FLAG,'role':'audit_only',
        'claims':413,'accepted_claims':409,'observed_net_accepted_CU':'1721459.84',
        'scope':'Frozen D46 claim list; all source cells, dates, status and amounts retained.',
        'actual_historical_coverage_confirmed':False,'automatic_expansion':False,
        'report':'../Limpieza/'+out.relative_to(c.BASE).as_posix()+'/informe.html'}
    protocol['target']['prehistory_audit_guard']={'version':'1.0','column':a.FLAG,
        'module':'Hackaton/Semana 1/Modelado/target_scope.py',
        'consumer':'diagnostico_objetivo.descriptive_proxy before period aggregation',
        'conflicting_marked_assignment':'ValueError; review coverage/cohort before continuing, never silently shift or zero amounts.',
        'current_period_cost_exclusion_verified':True,'verification_run':rel,
        'operational_T0_materialized':False,'historical_unmarked_snapshots':'Assignment remains loss-date interval based.'}
    protocol['features']['excluded_initially']=list(dict.fromkeys(protocol['features']['excluded_initially']+[a.FLAG]))
    methodology=paths['methodology.md'].read_text('utf-8').replace(
        'Versión 1.4, con REN00 como marca de auditoría sobre la capa DUP01/CAP01/CAT01/AGE01.',
        'Versión 1.5, con PRE00 y REN00 como marcas de auditoría sobre la capa DUP01/CAP01/CAT01/AGE01.')
    methodology+=f'''\n\n## PRE00: siniestros anteriores al primer periodo observado\n\n{decision}: por autorización expresa se añade audit_pre00 a claims en otra capa derivada. True marca exactamente los 413 expedientes congelados D46; false en los otros 162.133 significa fuera de esa lista. Se conservan los 162.546 registros DUP01 y todas las celdas previas, fechas, importes, estados e identificadores. La clasificación diagnóstica (244 compatibles con truncamiento de historia en 2021 y 169 anteriores al nuevo negocio registrado) permanece en bitácora y no confirma cobertura real. Las diez referencias restantes del catálogo, incluidas las marcas REN00, permanecen iguales.\n\nLos 409 siniestros aceptados PRE00 conservan 1.721.459,84 CU de incurrido neto observado en conciliación separada. No se asignan al primer periodo ni por report_date. Los 162.133 expedientes asignados por fecha de ocurrencia conservan 741.156.868,43 CU de neto aceptado. El consumidor descriptivo real produce exactamente los mismos componentes por cada uno de los 3.035.950 periodos. El control target_scope.assert_prehistory_excluded detiene una asignación de un expediente marcado a un periodo antes de agregar su coste. Una futura corrección de cobertura requiere revisar la lista y su autorización.\n\nLa marca es audit_only y el selector real excluye audit_*. Esta aplicación no aprueba predictores de historia de siniestros, no hace disponible el estado/importe final en años anteriores y no materializa el objetivo T0 operativo. [Informe, bitácora y conciliación PRE00](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html). Fechas CAL00, cobertura histórica y demás incidencias siguen pendientes.\n'''
    books=json.loads((out/'financial_reconciliation.json').read_text('utf-8'))
    financial=pd.DataFrame(books)[['scope','records','accepted','paid_accepted_CU','incurred_accepted_CU','recoveries_accepted_CU','net_accepted_CU']].rename(columns={
        'scope':'Ámbito','records':'Expedientes','accepted':'Aceptados','paid_accepted_CU':'Pagado CU',
        'incurred_accepted_CU':'Incurrido CU','recoveries_accepted_CU':'Recuperaciones CU','net_accepted_CU':'Neto aceptado CU'})
    financial['Ámbito']=financial['Ámbito'].map({'all':'Todos los conservados','assigned':'Asignados a periodos actuales','prehistory':'PRE00 separado del objetivo'})
    table=financial.to_html(index=False,border=0,escape=True)
    report=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PRE00 aplicado: auditoría y separación de costes</title><style>body{{font:16px/1.65 system-ui,sans-serif;background:#f2f5f7;color:#183243;margin:0}}main{{max-width:1180px;margin:auto;padding:28px}}header,section{{background:white;padding:24px;border-radius:12px;margin-bottom:18px}}header{{background:#15374b;color:white}}h1{{font-size:30px;line-height:1.25}}h2{{font-size:22px}}table{{border-collapse:collapse;white-space:nowrap;font-size:13px}}th,td{{padding:10px;border-bottom:1px solid #dbe3e9;text-align:left}}.scroll{{overflow:auto}}a{{color:#00786b}}code{{background:#e6edf1;color:#15374b;padding:2px 4px}}.metric{{font-size:22px;font-weight:600}}</style></head><body><main>
<header><h1>PRE00 aplicado en una nueva capa derivada</h1><p>{decision} · Autorización explícita del participante · Verificación propia asistida por IA</p><p class="metric">413 expedientes marcados · 162.546 conservados · 0 celdas previas modificadas</p></header>
<section><h2>El cambio exacto</h2><p>Claims recibe una sola columna: <code>audit_pre00</code>, booleano sin nulos. True identifica los 413 IDs de la lista congelada D46; las otras 162.133 filas reciben false. Los marcados son 296 de motor, 67 de edificios y 50 de contenidos. La marca permanece fuera de predictores por su nombre audit_* y sus metadatos audit_only.</p><p>Se conservan cada identificador, fecha de ocurrencia y reporte, estado, importe, nulo, tipo, metadato previo y posición. Quitar únicamente la nueva columna reconstruye íntegramente la tabla padre en Arrow. Los archivos originales y las capas anteriores conservan sus SHA256. Las diez referencias restantes del catálogo, incluidas las seis tablas con REN00, no cambian.</p><p>La lista no se amplía automáticamente. False significa fuera de la cohorte revisada; no certifica calidad, cobertura o elegibilidad. Las 244 observaciones compatibles con historia truncada en 2021 y las 169 anteriores al nuevo negocio registrado mantienen su clasificación solo en bitácora, sin convertirla en una decisión de cobertura.</p></section>
<section><h2>El dinero se conserva y queda separado</h2><div class="scroll">{table}</div><p>Los 413 registros PRE00 incluyen 409 aceptados (394 closed y 15 open) y 4 repudiated. Conservan 1.721.459,84 CU de incurrido neto aceptado, calculado como incurred_to_date menos recoveries. Este coste continúa fuera del objetivo de los periodos publicados. No se pone a cero ningún importe del expediente ni se elimina el siniestro.</p><p>Los componentes monetarios y conteos de todos = asignados + PRE00 concilian exactamente con Decimal, y coinciden con D46. Se preservan los 221 otros siniestros de estas pólizas que sí corresponden a periodos observados. El representante DUP01 CL85711436 continúa una sola vez; su alias anterior sigue excluido.</p></section>
<section><h2>Protección del objetivo y de los predictores</h2><p>La asignación exige policy_id, ramo y un intervalo publicado que contenga loss_date. Los 413 PRE00 mantienen row_id sin asignar y before_first_observed_period. No se usa report_date, no se fuerza el primer periodo y no se inventa exposición histórica.</p><p>Se reconstruyó la asignación de los 162.546 siniestros mediante una búsqueda temporal as-of, tras comprobar que los intervalos no se solapan, y se comparó con el cruce de intervalos de D46. El consumidor real diagnostico_objetivo.descriptive_proxy devuelve exactamente iguales costes y conteos por cada uno de los 3.035.950 periodos, antes y después de la marca.</p><p>El nuevo control target_scope.assert_prehistory_excluded se invoca antes de agregar costes. Si una asignación intenta cargar un PRE00 a un periodo actual, se detiene con ValueError para revisar cobertura y cohorte. Se probó ese fallo, la detección de marcas inválidas y el caso válido real. El selector real feature_frames también fue probado: invertir audit_pre00 no altera sus entradas seleccionadas.</p><p>Estas pruebas verifican el diagnóstico y el contrato de exclusión. El T0 operativo completo, la matriz F0 y los modelos continúan pendientes; no hubo entrenamiento ni se aprobó usar estos expedientes como historia predictiva.</p></section>
<section><h2>Bitácora y evidencia</h2><p><a href="ledger/pre00_marked_claims.csv">Bitácora CSV de los 413 siniestros</a> · <a href="ledger/pre00_marked_claims.parquet">Bitácora tipada</a> · <a href="ledger/schema_additions.csv">Adición de esquema y valores false</a></p><p>La bitácora conserva todos los campos anteriores de cada marcado, posición, clase diagnóstica, primer periodo observado, distancia temporal y hashes de origen, derivado, cohorte y autorización. Para las otras filas, la regla false y el hash de la tabla padre definen todas las celdas añadidas.</p><p><a href="tables/pre00_target_exclusion.csv">413 exclusiones del objetivo actual, sin exclusión del archivo</a> · <a href="financial_reconciliation.json">Conciliación monetaria</a> · <a href="tables/financial_reconciliation.csv">Conciliación CSV</a> · <a href="tables/claim_period_assignment.parquet">Asignación completa comprobada</a></p><p><a href="verification.json">{verification['passed']} controles propios superados</a> · <a href="consumer_verification.json">Consumidores reales y versiones</a> · <a href="authorization.json">Solicitud completa</a> · <a href="rules.json">Regla y reversión</a> · <a href="lineage.json">Linaje</a> · <a href="dataset_catalog.json">Nuevo catálogo</a> · <a href="manifest.json">Manifiesto SHA256</a></p></section>
<section><h2>Reproducción y límites</h2><p>Desde C:/dev/Hakaton se crea la capa con Preparación/.venv/Scripts/python.exe y Hackaton/Semana 1/Limpieza/apply_prehistory_audit.py. Se pasa la carpeta generada a verify_prehistory_audit.py y, solo tras sus comprobaciones, a finalize_prehistory_audit.py. Los scripts y consumidores comprobados están en source_snapshot. El catálogo activo se consulta a través de Limpieza/current_dataset.json; los índices de operaciones anteriores conservan su alcance histórico. Repetir el aplicador sobre la capa activa verifica una operación sin cambios.</p><p>Las causas de la prehistoria y la cobertura real siguen sin confirmación de la fuente. CAL00 y los 1.454 capitales pendientes siguen abiertos; CON01 permanece sin activar. Las aplicaciones heredadas CAP01, CAT01, AGE01, DUP01 y REN00 se conservan. Las fechas y los importes no se corrigieron.</p><p>La IA preparó código, documentación y controles; el participante autorizó la marca y su separación del objetivo. Verificación propia, sin revisión independiente. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, comunicación y responsabilidad; no son una certificación. No se enviaron datos a proveedores externos, no hubo publicación ni entrenamiento.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report,encoding='utf-8')
    for ref in re.findall(r'href="([^"]+)"',report):
        assert ref=='manifest.json' or (out/ref).is_file(),ref
    manifest={'created_utc':now,'type':'immutable_PRE00_application','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out/'manifest.json',manifest)
    assert c.digest(active)==protected[active.relative_to(c.ROOT).as_posix()]
    next_pointer={**parent,'workspace_relative_run':rel,'catalog_workspace_relative':rel+'/dataset_catalog.json',
        'status':'verified_REN00_PRE00_audit_only','audit_rules':list(dict.fromkeys(parent.get('audit_rules',[])+['PRE00'])),
        'audit_columns':list(dict.fromkeys(parent.get('audit_columns',[])+[a.FLAG])),
        'audit_marked_claims':413,'audit_counts_by_rule':{'REN00':{'policy_period_rows':12041,'policy_ids':2742},
                                                      'PRE00':{'claim_rows':413,'policy_ids':413}},
        'approved_for_modeling':False}
    temp=c.BASE/('pre00_index_'+uuid.uuid4().hex+'.json')
    c.dump(temp,next_pointer);temp.replace(active)
    own_index=c.BASE/'current_prehistory_audit_application.json'
    c.dump(own_index,{'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html',
        'decision_id':decision,'status':'applied_verified_audit_only','marked_claims':413,'claims_preserved':162546})
    c.dump(paths['protocol.json'],protocol)
    paths['methodology.md'].write_text(methodology,encoding='utf-8')
    paths['model_README.md'].write_text(paths['model_README.md'].read_text('utf-8').rstrip()+f'\n\nPRE00, {decision}, protocolo 1.5: audit_pre00 en claims conserva 413 expedientes y separa su coste de los periodos actuales. El diagnóstico real aplica target_scope.assert_prehistory_excluded antes de agregar costes y se verificó igualdad exacta de todos los periodos; no se materializa T0 ni se entrena. [Informe y conciliación](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html). El índice del diagnóstico histórico D42 conserva su snapshot y no se atribuye a esta capa; las nuevas pruebas del consumidor están en el informe PRE00.\n',encoding='utf-8')
    paths['cleaning_README.md'].write_text(paths['cleaning_README.md'].read_text('utf-8').rstrip()+f'\n\nPRE00, {decision}: una nueva tabla claims añade solo audit_pre00 a la lista congelada de 413 siniestros D46. Se conservan los 162.546 registros y todas sus celdas previas. Las otras diez entradas del catálogo, REN00 y el linaje DUP01 permanecen iguales. Los 409 aceptados conservan 1.721.459,84 CU en conciliación separada del objetivo de los periodos actuales; los costes asignados permanecen iguales. [Informe y bitácora]({out.relative_to(c.BASE).as_posix()}/informe.html), [índice PRE00](current_prehistory_audit_application.json). Aplicar con apply_prehistory_audit.py, verificar con verify_prehistory_audit.py y publicar con finalize_prehistory_audit.py. Usar current_dataset.json como catálogo activo. La marca es solo auditoría, sin decisión de cobertura ni corrección de fechas/importes.\n',encoding='utf-8')
    state['prehistory_audit_application']=application
    state['prehistory_claim_review']['followup_application_decision']=decision
    state['prehistory_claim_review']['audit_mark_authorized_later']=True
    state['methodological_plan']['version']='1.5'
    state['methodological_plan']['input_update_decision']=decision
    state['memory_as_of']=now
    routes['week_1_prehistory_audit_application_index']='Hackaton/Semana 1/Limpieza/current_prehistory_audit_application.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    decision_text=f'''\n\n### {decision}, PRE00 autorizado: auditoría de 413 siniestros y coste fuera de periodos actuales, 16 de octubre de 2026, America/Bogota\n\nEl participante autorizó aplicar PRE00 como marca en otra capa, conservar originales, fechas e importes y mantener su coste fuera del objetivo actual. Solicitud completa en ../{rel}/authorization.json. Se añade únicamente audit_pre00 booleano no nulo a claims: true para los 413 IDs congelados D46 (296 motor, 67 edificios, 50 contenidos), false en los otros 162.133. No hay expansión automática. Se conservan los 162.546 expedientes DUP01, todos sus campos anteriores, tipos, nulos, metadatos y orden. Quitar solo la marca reconstruye exactamente la tabla padre en Arrow. Los originales conservan su hash. Las otras diez entradas del catálogo quedan exactamente iguales, incluidas las marcas REN00. Alias y bitácora DUP01 se heredan sin restaurar copias.\n\nLa bitácora registra cada marcado con su payload original, posición, primer periodo, distancia temporal, clase diagnóstica y hashes de origen/derivado/cohorte/autorización. Las 244 compatibles con truncamiento de historia en 2021 y las 169 anteriores al nuevo negocio registrado siguen siendo hipótesis diagnósticas, sin cobertura real confirmada. La regla false y la adición de esquema identifican todas las celdas nuevas restantes. True no significa repudiated y false no certifica calidad.\n\nLos 413 siguen sin row_id asignado, como before_first_observed_period. Los 409 aceptados mantienen pagado 1.616.071,21 CU, incurrido 1.786.628,82, recuperaciones 65.168,98 y neto 1.721.459,84 CU en conciliación separada del objetivo. Se conservan sus 394 closed, 15 open y 4 repudiated, sin poner importes a cero. Los 162.133 expedientes asignados conservan 741.156.868,43 CU de neto aceptado. Conteos y cada componente monetario concilian todos = asignados + PRE00 con Decimal y coinciden con D46. Permanecen los 221 otros siniestros asignados de las pólizas afectadas y el representante CL85711436 una sola vez.\n\nLa verificación reconstruye la asignación por búsqueda as-of después de demostrar que los intervalos no se solapan, un algoritmo distinto del cruce de intervalos D46. Coinciden las 162.546 asignaciones. El consumidor real diagnostico_objetivo.descriptive_proxy produce exactamente los mismos conteos y costes por cada uno de los 3.035.950 periodos antes/después. Se integra target_scope.assert_prehistory_excluded 1.0 antes de agregar; una marca asignada a un periodo provoca ValueError, sin desplazamiento, borrado o corrección silenciosa. Se prueban asignaciones forzadas y el fallo real del consumidor en los tres ramos. El selector real feature_frames excluye audit_pre00 y permanece idéntico si se invierte esa marca; el guard rechaza su solicitud explícita. No se aprueban predictores de historia ni se materializa T0.\n\nPasaron {verification['passed']} controles propios de preservación, cohorte, metadatos, bitácora, idempotencia, conflicto, asignación, conciliación y consumidores. El código y protocolo anteriores a PRE00 se conservan en Modelado/archivo/pre_PRE00_20261016T211435Z; los scripts aplicados y consumidores están en source_snapshot. Protocolo/metodología 1.5. El diagnóstico D42 conserva su snapshot histórico: no se reescribe ni se presenta como prueba de esta versión. CAL00, 1.454 capitales y confirmación de fuente siguen pendientes; los 2.073 CAP01 se heredan y CON01 no se activa.\n\nEl nuevo catálogo se publica atómicamente después de verificar y comprobar que el puntero padre no cambió. Se conserva el índice específico de PRE00 y un cierre con documentos antes/después y prueba CLI de repetición sin cambios. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad. Verificación propia asistida por IA; no revisión independiente, entrenamiento, proveedor externo, publicación, envío o delegación. La autorización de esta marca no confirma cobertura ni aprueba globalmente el modelado. Consultar prehistory_audit_application.\n'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+decision_text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nPRE00 aplicado por autorización, {decision}: [catálogo activo](../Hackaton/Semana 1/Limpieza/current_dataset.json), [informe y bitácora](../{rel}/informe.html). Solo se añade audit_pre00 a los 413 IDs D46; se conservan los 162.546 siniestros y todas las celdas previas. Los 409 aceptados mantienen 1.721.459,84 CU separados del objetivo actual; los asignados conservan 741.156.868,43 CU. Las diez referencias restantes, REN00 y DUP01 permanecen iguales. Pasaron {verification["passed"]} controles; asignación reconstruida por otro algoritmo y consumidor real idéntico en 3.035.950 periodos. Control PRE00 rechaza asignaciones incompatibles antes de sumar; audit_* queda fuera de predictores. Protocolo 1.5, sin T0 operativo ni entrenamiento. Cobertura histórica, fechas y demás pendientes conservados. Ver prehistory_audit_application y {decision}.\n',encoding='utf-8')
    after_docs=close/'after';after_docs.mkdir()
    for name,p in paths.items():shutil.copy2(p,after_docs/name)
    # Actual CLI repetition after activation must not produce a new layer or alter any file.
    active_hash=c.digest(active);own_hash=c.digest(own_index)
    replay=subprocess.run([sys.executable,str(c.BASE/'apply_prehistory_audit.py')],cwd=c.ROOT,text=True,capture_output=True,check=True)
    replay_result=json.loads(replay.stdout)
    post=[{'check':'Actual second CLI invocation is verified no-op','passed':replay_result['status']=='already_applied_verified_noop' and replay_result['new_columns_added']==0},
          {'check':'Active and operation indexes unchanged by second CLI invocation','passed':c.digest(active)==active_hash and c.digest(own_index)==own_hash},
          {'check':'Immutable application manifest intact','passed':a.manifest_ok(out)},
          {'check':'Every original, parent and review hash unchanged','passed':all(c.digest(c.ROOT/p)==sha for p,sha in protected.items() if p!=active.relative_to(c.ROOT).as_posix())},
          {'check':'Parent closed run and D46 review manifests intact','passed':a.manifest_ok(c.ROOT/parent['workspace_relative_run']) and a.manifest_ok(a.REVIEW)},
          {'check':'No global modeling approval introduced','passed':not next_pointer['approved_for_modeling']},
          {'check':'Protocol 1.5 keeps REN00 and adds PRE00 separately','passed':protocol['inputs']['audit_annotations']['rule']=='REN00' and protocol['inputs']['prehistory_audit']['rule']=='PRE00'}]
    assert all(item['passed'] for item in post)
    c.dump(close/'post_publication_verification.json',{'passed':len(post),'failed':0,'checks':post,
        'actual_second_cli':replay_result,'stderr':replay.stderr,'independent_validation':False})
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'application':application,
        'manifest_sha256':c.digest(out/'manifest.json'),'active_index_sha256':active_hash,
        'source_and_parent_data_preserved':True,'post_publication_checks':len(post),
        'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[active,own_index]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),
        'closure':str(close),'status':'applied_verified_audit_only','post_publication_checks':len(post)},ensure_ascii=False))


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
