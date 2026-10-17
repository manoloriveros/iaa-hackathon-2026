"""Publica REN00 solo después de verificar datos y selector; registra la autorización y sus límites."""
from pathlib import Path
from datetime import datetime, timezone
import html
import json
import re
import shutil
import sys
import uuid

import clean_data as c
import apply_renewal_audit as a
import pandas as pd


def main(out):
    assert not (out / 'manifest.json').exists(), 'Closed run; do not overwrite.'
    verification = json.loads((out / 'verification.json').read_text('utf-8'))
    guard = json.loads((out / 'predictor_exclusion_verification.json').read_text('utf-8'))
    assert verification['failed'] == guard['failed'] == 0 and guard['targeted_tests'] >= 12
    active = c.BASE / 'current_dataset.json'
    parent_pointer = json.loads((out / 'evidence/parent_index.json').read_text('utf-8'))
    protected = json.loads((out / 'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT / p) == sha for p, sha in protected.items())
    assert c.digest(c.ROOT / 'Preparación/src/iaa_lab/data.py') == guard['core_data_sha256']
    assert c.digest(c.ROOT / 'Preparación/src/iaa_lab/predictor_guard.py') == guard['guard_sha256']
    now = datetime.now(timezone.utc).isoformat()
    rel = out.relative_to(c.ROOT).as_posix()
    s = json.loads((out / 'summary.json').read_text('utf-8'))
    close = c.BASE / 'closures' / datetime.now(timezone.utc).strftime('REN00_closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True, exist_ok=False)
    paths = {name: c.ROOT / 'Preparación' / name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json': c.ROOT / 'RUTAS_PROYECTO.json',
        'protocol.json': c.ROOT / 'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md': c.ROOT / 'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'model_README.md': c.ROOT / 'Hackaton/Semana 1/Modelado/README.md', 'cleaning_README.md': c.BASE / 'README.md'})
    for name,p in paths.items():
        shutil.copy2(p, close / ('before_' + name))
    state = json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    memory = paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decisions = paths['DECISIONES.md'].read_text('utf-8')
    routes = json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    protocol = json.loads(paths['protocol.json'].read_text('utf-8'))
    methodology = paths['methodology.md'].read_text('utf-8')
    decision = 'D' + str(max(map(int,re.findall(r'\bD(\d+)\b',decisions))) + 1)
    review = {'decision_id':decision, 'rule':'REN00', 'status':'applied_verified_audit_only', 'column':a.FLAG,
        'run':'../' + rel, 'report':'../' + rel + '/informe.html', 'catalog':'../' + rel + '/dataset_catalog.json',
        'ledger':'../' + rel + '/ledger/ren00_marked_rows.parquet', 'ledger_csv':'../' + rel + '/ledger/ren00_marked_rows.csv',
        'verification':'../' + rel + '/verification.json', 'predictor_verification':'../' + rel + '/predictor_exclusion_verification.json',
        'frozen_policies':2742, 'marked_period_rows':12041, 'marked_train_rows':9110, 'marked_test_rows':2931,
        'policy_records_preserved':3035950, 'claims_records_preserved':162546, 'original_cells_changed':0,
        'policy_rows_removed':0, 'audit_only':True, 'predictor_exclusion_enforced':True, 'guard_version':'1.0',
        'dates_changed':False, 'labels_changed':False, 'exposure_changed':False, 'claims_changed':False,
        'calendar_pending':True, 'semantics_confirmed':False, 'audit_mark_explicitly_authorized':True,
        'technical_checks':verification['passed'], 'predictor_guard_checks':guard['passed'], 'targeted_core_tests':guard['targeted_tests'],
        'full_F0_availability_contract_implemented':False, 'operational_T0_materialized':False,
        'models_trained':False, 'independent_validation':False, 'pending_capitals_unchanged':1454,
        'CON01_activated':False, 'closure':'../' + close.relative_to(c.ROOT).as_posix()}
    protocol['version'] = '1.4'
    protocol['inputs']['audit_annotations'] = {'rule':'REN00', 'column':a.FLAG, 'role':'audit_only', 'policy_ids':2742,
        'marked_periods':12041, 'mark_scope':'All periods of frozen cohort policies, including historical rows; no claim rows modified.',
        'all_source_values_preserved':True, 'forward_looking_membership':True, 'automatic_expansion':False,
        'report':'../Limpieza/' + out.relative_to(c.BASE).as_posix() + '/informe.html'}
    protocol['features']['excluded_initially'] = list(dict.fromkeys(protocol['features']['excluded_initially'] + ['audit_ren00','audit_*','derived_renewal_decision_fields']))
    protocol['features']['exclusion_guard'] = {'version':'1.0','module':'Preparación/src/iaa_lab/predictor_guard.py',
        'consumer':'iaa_lab.data.feature_frames, used by the existing runner',
        'blocked':'Any name containing renewal_decision, audit_ prefix (case-insensitive), or explicit audit_only role.',
        'explicit_forbidden_request':'ValueError', 'automatic_selection':'Removes blocked columns while preserving all rows.',
        'verification_run':rel,'F0_availability_complete':False,'generic_runner_fully_adapted_to_2026':False}
    methodology = methodology.replace('Versión 1.3, con DUP01 autorizado sobre la capa CAP01/CAT01/AGE01.',
        'Versión 1.4, con REN00 como marca de auditoría sobre la capa DUP01/CAP01/CAT01/AGE01.')
    methodology = methodology.replace('neto de franquicias y recuperaciones, excluyendo rechazados |',
        'neto de franquicias y recuperaciones, excluyendo siniestros repudiated; conservar las pólizas con declined_by_insurer |')
    methodology += f'''\n\n## REN00 y exclusión operativa de decisiones y auditoría\n\n{decision}: se añade audit_ren00 a las seis tablas derivadas. True identifica pertenencia a las 2.742 pólizas de la cohorte congelada D44 en cualquiera de sus 12.041 periodos; no afirma rechazo en cada fila. False significa fuera de esa lista. La pertenencia usa el resultado 2024 y la continuidad 2025, por lo que también es información futura respecto de los periodos históricos y está prohibida como predictor. Los roles de los dos extremos y el resto del historial quedan en la bitácora. Todas las celdas previas, los 162.546 siniestros DUP01 y las fechas permanecen iguales.\n\nEl selector real iaa_lab.data.feature_frames excluye renewal_decision y cualquier nombre que contenga ese texto, junto a audit_*. El guard permite rechazar solicitudes explícitas de columnas prohibidas y roles audit_only. Se validó sobre esquemas de las seis tablas y muestras reales con marcas positivas/negativas, perturbando decisiones y marcas sin alterar la matriz seleccionada. Esto impone la exclusión solicitada; no completa la matriz F0, sus cortes de disponibilidad, el objetivo T0 ni la adaptación del runner a Tweedie D². No hubo entrenamiento.\n\n[Informe REN00](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html). La semántica de declined_by_insurer y las fechas de CAL00 siguen pendientes. El rechazo de póliza no debe confundirse con el estado repudiated de un expediente.\n'''
    # An application report needs no new cost estimation or historical diagnostic rerun.
    counts = pd.DataFrame(s['by_table']).to_html(index=False,border=0,escape=True)
    report = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>REN00 aplicado como auditoría</title><style>body{{font:16px/1.65 system-ui,sans-serif;background:#f2f5f7;color:#183243;margin:0}}main{{max-width:1250px;margin:auto;padding:30px}}section,header{{background:white;padding:25px;border-radius:12px;margin-bottom:20px}}header{{background:#15374b;color:white}}h1{{font-size:30px}}h2{{font-size:22px}}table{{border-collapse:collapse;white-space:nowrap;font-size:13px}}th,td{{padding:9px;border-bottom:1px solid #dbe3e9;text-align:left}}.scroll{{overflow:auto}}a{{color:#00786b}}code{{background:#e6edf1;color:#15374b;padding:2px 4px}}</style></head><body><main><header><h1>REN00 aplicado como marca de auditoría</h1><p>{decision} · Autorización explícita del participante. Originales y todas las celdas anteriores conservados.</p></header>
<section><h2>Qué cambió</h2><p>Se añade únicamente <code>audit_ren00</code>, booleano sin nulos, a seis tablas derivadas. Tiene valor true en 12.041 periodos de las 2.742 pólizas congeladas: 9.110 filas train y 2.931 test. Las otras 3.023.909 filas reciben false. Se preservan los 3.035.950 periodos y los 162.546 siniestros DUP01.</p><p>La marca identifica pertenencia a la cohorte, también en periodos históricos. No significa que cada fila fue rechazada. False significa fuera de esta lista; no certifica ausencia de otros problemas. Los extremos 2024/2025 y periodos de contexto se distinguen en la bitácora.</p><div class="scroll">{counts}</div></section>
<section><h2>Fechas, etiquetas y siniestros</h2><p>No se cambia period_start, period_end, exposure, renewal_decision, prima, capital o cualquier valor previo. Las 2.742 decisiones literales siguen siendo declined_by_insurer; las de los demás periodos también se conservan. CAL00 y la semántica del rechazo siguen pendientes. Claims conserva exactamente su referencia y hash DUP01, junto con sus alias y bitácora anteriores.</p><p>La verificación compara cada valor original, tipo, metadato y orden de fila. Quitar solo audit_ren00 reconstruye la tabla padre de forma exacta. La marca no elimina filas o siniestros ni impone predicciones cero.</p></section>
<section><h2>Exclusión comprobada en los predictores</h2><p>El protocolo pasa a 1.4 y el selector real usado por el runner excluye renewal_decision, campos derivados cuyo nombre contiene ese texto y cualquier audit_*. También existe un guard que rechaza una lista explícita con campos prohibidos o metadatos audit_only.</p><p>Se probaron esquemas de las seis tablas y muestras reales que incluyen true y false. Cambiar decisiones, invertir la marca y añadir campos derivados de prueba deja exactamente iguales las matrices seleccionadas. Se conserva renewal_count, que es un campo diferente. No se filtró ninguna fila.</p><p>La pertenencia REN00 usa continuidad observada 2025 y resultado 2024: es información futura para años históricos y no puede entrar en tarifa. Este control de exclusión no completa F0, T0 ni la adaptación del runner al reto 2026; no hubo entrenamiento.</p><p>Pasaron {verification['passed']} controles técnicos, {guard['passed']} controles del selector y {guard['targeted_tests']} pruebas focalizadas del núcleo. Son verificaciones propias asistidas por IA, sin validación independiente.</p></section>
<section><h2>Bitácora y reproducción</h2><p><a href="ledger/ren00_marked_rows.csv">12.041 filas marcadas y roles</a> · <a href="ledger/schema_additions.csv">Seis adiciones de esquema y valores false implícitos</a> · <a href="rules.json">Definición de la marca</a> · <a href="authorization.json">Autorización</a> · <a href="dataset_catalog.json">Catálogo derivado</a></p><p><a href="verification.json">Verificación completa de datos</a> · <a href="predictor_exclusion_verification.json">Prueba del selector real</a> · <a href="predictor_schema_inventory.json">Inventario de exclusión, sin aprobación F0</a> · <a href="predictor_guard_pytest.xml">Pruebas focalizadas</a> · <a href="manifest.json">SHA256 de la corrida</a></p><p>Desde C:/dev/Hakaton, apply_renewal_audit.py crea otra capa sobre el snapshot autorizado o verifica que REN00 ya está aplicado sin modificar nada. Antes de publicar se usan verify_renewal_audit.py, las pruebas focalizadas, verify_predictor_exclusion.py y finalize_renewal_audit.py. Los scripts y el selector están archivados en source_snapshot; el código y la documentación previos se conservan en {html.escape(a.ARCHIVE.relative_to(c.ROOT).as_posix())}.</p></section>
<section><h2>Alcance y responsabilidad</h2><p>La autorización aplica una marca de auditoría, sin confirmar la intención del generador o la etiqueta correcta. Se heredan 2.073 CAP01, se conservan 1.454 capitales pendientes y CON01 no se activa. Los diagnósticos anteriores permanecen ligados a sus snapshots; la igualdad de las columnas originales acredita conservación numérica sin repetir sus agregados por una marca.</p><p>IAA Documentación §2 y §§4–6: trazabilidad y uso; Gobernanza §2.8: verificación propia; Consideraciones profesionales §3.2 y §§3.5–3.6: interpretación y responsabilidad humana. No hubo proveedor externo, envío o publicación.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report,encoding='utf-8')
    for ref in re.findall(r'href="([^"]+)"', report):
        assert ref == 'manifest.json' or (out/ref).is_file(), ref
    manifest = {'created_utc':now,'type':'immutable_REN00_application','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out/'manifest.json',manifest)
    # Publish only after both data checks and actual selector checks, and reject concurrent pointer drift.
    assert c.digest(active) == protected[active.relative_to(c.ROOT).as_posix()]
    next_pointer = {**parent_pointer, 'workspace_relative_run':rel, 'catalog_workspace_relative':rel+'/dataset_catalog.json',
        'status':'verified_REN00_audit_only', 'audit_rules':['REN00'], 'audit_columns':[a.FLAG], 'audit_marked_rows':12041,
        'audit_frozen_policies':2742, 'predictor_exclusion_guard_version':'1.0', 'approved_for_modeling':False}
    temp = c.BASE / ('ren00_index_' + uuid.uuid4().hex + '.json')
    c.dump(temp,next_pointer); temp.replace(active)
    c.dump(c.BASE/'current_renewal_audit_application.json', {'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html',
        'decision_id':decision,'status':'applied_verified_audit_only','marked_period_rows':12041,'frozen_policies':2742})
    protocol_text = json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False)
    paths['protocol.json'].write_text(protocol_text,encoding='utf-8')
    paths['methodology.md'].write_text(methodology,encoding='utf-8')
    paths['model_README.md'].write_text(paths['model_README.md'].read_text('utf-8').rstrip()+f'\n\nREN00, {decision}: protocolo 1.4 y marca audit_ren00 en seis derivados. renewal_decision y audit_* quedan excluidos por el selector real iaa_lab.data.feature_frames y el guard de predictores. [Verificación e informe](../Limpieza/{out.relative_to(c.BASE).as_posix()}/informe.html). No se completa F0/T0 ni se entrena. El diagnóstico anterior conserva su snapshot DUP01; no se repite porque ninguna columna previa cambió.\n',encoding='utf-8')
    paths['cleaning_README.md'].write_text(paths['cleaning_README.md'].read_text('utf-8').rstrip()+f'\n\nREN00, {decision}, añade audit_ren00 a las seis tablas de pólizas/test en otra capa, sin cambiar ninguna celda anterior. Identifica 2.742 pólizas congeladas en 12.041 periodos (9.110 train, 2.931 test); todos los siniestros DUP01 se conservan. La marca y renewal_decision están prohibidas como predictores por el selector real. [Informe y bitácora]({out.relative_to(c.BASE).as_posix()}/informe.html); [índice REN00](current_renewal_audit_application.json). Usar current_dataset.json para la capa activa; los índices anteriores son históricos. Se aplica con apply_renewal_audit.py, se verifica con verify_renewal_audit.py y verify_predictor_exclusion.py y se publica con finalize_renewal_audit.py después de las pruebas focalizadas. Una repetición del aplicador comprueba la marca existente sin añadir otra columna.\n',encoding='utf-8')
    state['renewal_audit_application'] = review
    state['declined_renewal_review']['followup_application_decision'] = decision
    state['declined_renewal_review']['audit_mark_authorized_later'] = True
    state['calendar_review']['participant_followup']['dates_remain_pending'] = True
    state['methodological_plan']['version'] = '1.4'
    state['memory_as_of'] = now
    routes['week_1_renewal_audit_application_index'] = 'Hackaton/Semana 1/Limpieza/current_renewal_audit_application.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state); c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text = f'''\n\n### {decision}, REN00 autorizado como auditoría y exclusión operativa de predictores, 16 de octubre de 2026, America/Bogota\n\nEl participante autorizó aplicar REN00 en derivados, conservar pólizas/siniestros y no cambiar fechas o etiquetas, y pidió validar renewal_decision fuera de predictores. Autorización completa en ../{rel}/authorization.json. La nueva capa añade únicamente audit_ren00 booleano no nulo a seis tablas. True indica pertenencia a las 2.742 pólizas congeladas D44 (1.513 motor, 1.010 edificios, 219 contenidos) en todos sus periodos: 12.041 filas, 9.110 train y 2.931 test. No significa rechazo ocurrido en cada fila. False en las otras 3.023.909 filas solo indica fuera de esa cohorte. No se expande a los otros rechazos históricos. Bitácora por fila/posición/rol y hash para los true; adiciones de esquema y regla false implícita definen todos los valores añadidos.\n\nSe conservan 3.035.950 periodos y los 162.546 siniestros DUP01. Ninguna celda anterior, fecha, decisión, exposición, prima, capital, nulo, tipo, orden o metadato de esquema previo cambia. Las cinco referencias restantes del catálogo, incluida claims y sus alias/bitácora heredados, permanecen exactamente iguales. Quitar audit_ren00 reconstruye íntegramente cada tabla padre. La adición es idempotente y rechaza marcas o metadatos contradictorios. CAL00 y la semántica de declined_by_insurer siguen pendientes, los 2.073 CAP01 se heredan, 1.454 capitales permanecen pendientes y CON01 no se activa.\n\nLa exclusión solo estaba documentada en protocolo 1.3: el selector genérico podía aceptar renewal_decision si se copiaba a test. Se incorpora iaa_lab.predictor_guard 1.0 y se integra en iaa_lab.data.feature_frames, que consume el runner existente. Excluye todo nombre que contenga renewal_decision y el prefijo audit_, sin distinguir mayúsculas, y permite rechazar listas explícitas con columnas prohibidas o roles audit_only. validate_frames compara el esquema predictivo excluyendo esos metadatos; sigue rechazando diferencias de predictores permitidos, objetivo en test, IDs duplicados/solapados y reglas sin confirmar. renewal_count se conserva como un campo distinto. No hay renombrado arbitrario a variables aparentemente legítimas autorizado; mantener metadatos y guard al seleccionar columnas.\n\nSe ejercitó el selector real con esquemas completos y muestras de los seis derivados, incluyendo marcas true/false. Invertir marcas, alterar decisiones y añadir variantes derivadas en train/test deja iguales nombres, valores y filas seleccionados. Las pruebas generan solo inventarios de exclusión, sin aprobar la matriz F0: disponibilidad temporal, maestros, coste último, T0, folds y adaptación del runner a 2026 continúan. La pertenencia usa resultado 2024 y continuidad 2025 y es futura respecto a años históricos; nunca usar la marca en tarifa. El objetivo distingue siniestros repudiated de pólizas declined_by_insurer; estas pólizas y pérdidas aceptadas se conservan.\n\nPasaron {verification['passed']} controles de preservación completa, metadatos, cohorte por algoritmo distinto, bitácora, reversión, idempotencia y conflicto; {guard['passed']} controles del selector y {guard['targeted_tests']} pruebas focalizadas del núcleo. Versiones previas de data.py/protocolo/documentación archivadas en {a.ARCHIVE.relative_to(c.ROOT).as_posix()}. Protocolo/metodología 1.4 y READMEs explican uso y límites. No se repiten agregados históricos porque la única adición es de auditoría y todas las columnas numéricas/fechas previas son iguales; los diagnósticos existentes permanecen atribuidos a su snapshot. No hay entrenamiento, T0 operativo, proveedor externo, envío, publicación o delegación. Verificación propia, sin independencia.\n\nCatálogo activo publicado atómicamente tras las verificaciones y control de puntero padre. El índice current_renewal_audit_application.json identifica la operación; los índices anteriores conservan alcance histórico. No se reescriben D42/D43/D44 ni otras corridas. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 respaldan trazabilidad, explicación y responsabilidad. Autorización humana de marca/exclusión no equivale a confirmación semántica del organizador o aprobación global de modelado. Consultar renewal_audit_application.\n'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nREN00 aplicado por autorización, {decision}: [catálogo activo](../Hackaton/Semana 1/Limpieza/current_dataset.json), [informe](../{rel}/informe.html). audit_ren00 identifica las 2.742 pólizas D44 en 12.041 periodos (9.110 train, 2.931 test), sin cambiar ningún dato previo. Se conservan los 3.035.950 periodos y 162.546 siniestros DUP01. renewal_decision, sus derivados identificables y audit_* se excluyen en el selector real del runner; protocolo 1.4. Pasaron {verification["passed"]} controles de datos, {guard["passed"]} del selector y {guard["targeted_tests"]} pruebas del núcleo. Fechas y semántica siguen pendientes; marca futura de cohorte es solo auditoría, nunca predictor. No hay F0 completo, T0 operativo ni entrenamiento. Ver renewal_audit_application y {decision}.\n',encoding='utf-8')
    after = close/'after'; after.mkdir()
    for name,p in paths.items():
        shutil.copy2(p,after/name)
    protected_after = {p:c.digest(c.ROOT/p) for p in protected if p != active.relative_to(c.ROOT).as_posix()}
    assert all(sha == protected[p] for p,sha in protected_after.items())
    assert all(c.digest(out/e['path']) == e['sha256'] for e in manifest['files'])
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':review,'manifest_sha256':c.digest(out/'manifest.json'),
        'active_index_sha256':c.digest(active),'source_and_parent_data_preserved':True,
        'post_documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[active,c.BASE/'current_renewal_audit_application.json']}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),'status':'applied_verified_audit_only'},ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
