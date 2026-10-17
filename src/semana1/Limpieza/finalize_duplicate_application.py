"""Cierra integración y memoria después de DUP01 verificado y del diagnóstico sobre la misma capa."""
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import json
import re
import shutil

import apply_duplicates as a


def main():
    root=a.ROOT;pointer=json.loads((a.BASE/'current_duplicate_application.json').read_text(encoding='utf-8'))
    out=root/pointer['workspace_relative_run'];assert pointer['status']=='verified_DUP01_frozen_cohort'
    verify=json.loads((out/'verification.json').read_text(encoding='utf-8'));assert verify['passed']
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'));manifest_hash=a.c.digest(out/'manifest.json')
    assert all(a.c.digest(out/e['path'])==e['sha256'] for e in manifest['files'])
    current=root/'Hackaton/Semana 1/Limpieza/current_dataset.json'
    assert json.loads(current.read_text(encoding='utf-8'))==pointer
    catalog=json.loads((out/'dataset_catalog.json').read_text(encoding='utf-8'))
    model=root/'Hackaton/Semana 1/Modelado'
    candidates=[]
    for path in (model/'diagnosticos').glob('objetivo_*/evidencia.json'):
        d=json.loads(path.read_text(encoding='utf-8'))
        if d.get('cleaning_run')==pointer['workspace_relative_run'] and d.get('claims_rule')=='DUP01':candidates.append((path,d))
    if not candidates:raise ValueError('First finish the current-catalog consumer diagnostic; no closure without that evidence.')
    diag_path,diag=sorted(candidates,key=lambda item:item[0].as_posix())[-1]
    diag_dir=diag_path.parent
    assert a.c.digest(diag_dir/'diagnostico_objetivo.py')==a.c.digest(model/'diagnostico_objetivo.py')
    closure=a.BASE/'closures'/datetime.now(timezone.utc).strftime('DUP01_closure_%Y%m%dT%H%M%SZ')
    (closure/'before').mkdir(parents=True,exist_ok=False);(closure/'after').mkdir()
    shutil.copy2(Path(__file__),closure/'finalize_duplicate_application.py')
    docs=['Preparación/DECISIONES.md','Preparación/MEMORIA_PROYECTO.md','Preparación/ESTADO_PROYECTO.json','RUTAS_PROYECTO.json',
        'Hackaton/Semana 1/README.md','Hackaton/Semana 1/Modelado/diagnosticos/actual.json']
    for path in docs:
        dest=closure/'before'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dest)
    for name in ['diagnostico_objetivo.py','METODOLOGIA_ACTUARIAL.md','protocolo_metodologico.json','README.md']:
        dest=closure/'modelado_after'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(model/name,dest)
    shutil.copy2(a.BASE/'README.md',closure/'cleaning_README_after.md')
    shutil.copy2(diag_path,closure/'consumer_diagnostic.json')
    checks=[]
    def check(name,passed):checks.append({'name':name,'passed':bool(passed)});assert passed,name
    check('active_catalog_and_verified_DUP01_pointer_agree',json.loads(current.read_text(encoding='utf-8'))==pointer and verify['excluded_records']==604)
    check('consumer_reads_derived_claims_hash',diag['provenance']['claims']['path']==catalog['claims']['workspace_relative_path']
          and diag['provenance']['claims']['sha256']==catalog['claims']['sha256'])
    check('all_consumer_input_hashes_match_active_catalog',all(entry['sha256']==catalog[name]['sha256'] and entry['path']==catalog[name]['workspace_relative_path']
        and a.c.digest(root/entry['path'])==entry['sha256'] for name,entry in diag['provenance'].items()))
    check('no_historical_EDA_cost_proxy_reused',diag['historical_EDA_claim_aggregates_reused'] is False and not any(name.startswith('eda_proxy') for name in diag['provenance']))
    check('consumer_financial_controls_clean_and_single_zero_preserved',diag['controls']['unique_claim_ids']
          and diag['controls']['accepted_zero_net_cost']==1 and not diag['controls']['unknown_statuses']
          and all(value==0 for key,value in diag['controls'].items() if key not in ['unique_claim_ids','accepted_zero_net_cost','unknown_statuses']))
    check('consumer_assignments_cover_all_162546_claims_and_413_prehistory',sum(x['input_claim_records'] for x in diag['diagnostic_claim_assignment_counts'])==162546
        and sum(x['before_first_observed_period'] for x in diag['diagnostic_claim_assignment_counts'])==413
        and all(x['ambiguous_or_other_unmatched']==0 for x in diag['diagnostic_claim_assignment_counts']))
    books=json.loads((out/'reconciliation.json').read_text(encoding='utf-8'))
    assigned=next(x for x in books if x['value']=='unique_period')
    stats=diag['observed_proxy_with_cleaned_exposure']
    check('current_consumer_accepted_count_matches_exact_book',sum(x['reported_accepted_claims'] for x in stats)==assigned['after_accepted']==160432)
    observed=Decimal(str(sum(x['observed_net_incurred'] for x in stats))).quantize(Decimal('.01'))
    check('current_consumer_cost_matches_exact_Decimal_book_to_cent',observed==Decimal(assigned['after_net_accepted_CU']))
    check('all_accepted_claim_diagnostic_count_matches_book',sum(x['reported_accepted_claims'] for x in diag['claims_by_peril_year'])==books[0]['after_accepted']==160841)
    protocol=json.loads((model/'protocolo_metodologico.json').read_text(encoding='utf-8'))
    archive=model/'archivo/pre_DUP01_20261016T200039Z'
    oldprotocol=json.loads((archive/'protocolo_metodologico.json').read_text(encoding='utf-8'))
    check('protocol_13_preserves_validation_features_metric_and_line_design',protocol['version']=='1.3'
          and all(protocol[key]==oldprotocol[key] for key in ['validation','features','metric','line_design']))
    check('protocol_frozen_DUP01_and_no_CON01_or_T0_activation',protocol['inputs']['claims_deduplication']['excluded_copies']==604
          and not protocol['inputs']['category_normalization']['t_w_semantic_merge'] and not protocol['target']['operational_T0_materialized'])
    olddiag=json.loads((model/'diagnosticos/objetivo_20261016T181306Z/evidencia.json').read_text(encoding='utf-8'))
    check('policy_entity_overlap_and_products_unchanged_by_claim_filter',diag['temporal_entity_overlap']==olddiag['temporal_entity_overlap']
          and diag['motor_products']==olddiag['motor_products'])
    check('consumer_is_descriptive_no_training_or_target_file',diag['models_trained']==0 and diag['source_files_modified'] is False
          and sorted(p.name for p in diag_dir.iterdir())==['diagnostico_objetivo.py','evidencia.json'])
    check('model_pre_DUP01_archive_matches_its_manifest',all(a.c.digest(archive/e['path'])==e['sha256'] for e in json.loads((archive/'manifest.json').read_text(encoding='utf-8'))['files']))
    cpaths=['data/claims.parquet','ledger/claim_id_aliases.parquet','ledger/exclusion_ledger.parquet','ledger/excluded_rows.parquet','dataset_catalog.json','informe.html','authorization.json']
    check('all_new_artifacts_exist',all((out/p).is_file() for p in cpaths))
    a.c.dump(closure/'consumer_integration_verification.json',{'passed':True,'checks_count':len(checks),'checks':checks,
        'consumer_run':diag_dir.relative_to(root).as_posix(),'consumer_source_sha256':a.c.digest(model/'diagnostico_objetivo.py'),
        'current_proxy_net_sum_CU':str(observed),'independent_validation':False,'models_trained':False})
    decisions=root/'Preparación/DECISIONES.md';before=decisions.read_text(encoding='utf-8')
    decision='D'+str(max(int(x) for x in re.findall(r'\bD(\d+)\b',before))+1)
    rel='../'+out.relative_to(root).as_posix();diagrel='../'+diag_path.relative_to(root).as_posix()
    decisions.write_text(before+f'''

### {decision}, DUP01 autorizado y aplicado en una nueva capa de siniestros, 16 de octubre de 2026, America/Bogota

El participante autorizó explícitamente aplicar DUP01 a los 604 pares de D41, conservar el ID de ocho dígitos y guardar bitácora y alias sin tocar originales ni otros siniestros. La solicitud completa queda en authorization.json. Nueva corrida {rel}, sobre el catálogo D38. Se usa la lista congelada de IDs y hashes revisados; no se redescubre la cohorte ni se excluye por longitud sola. La autorización aprueba esta transformación, no confirma la causa del generador, identidad real de eventos o una validación independiente.

claims pasa de 163.150 a 162.546 filas, conservando cada celda, el esquema/metadatos y el orden relativo de los retenidos. Se excluyen únicamente 604 gemelos de nueve dígitos: 411 motor, 109 edificios y 84 contenidos; 586 cerrados, 12 abiertos y seis rechazados. Permanecen los 604 representantes de ocho dígitos y los otros 161.942 registros ajenos a las parejas. Los 114 registros de los 57 grupos no idénticos por póliza/ocurrencia, incluidos M83268515 y M63592395, permanecen. Ningún importe, estado, fecha, reparador, tercero o asociación de un siniestro retenido cambia.

La bitácora CSV/Parquet conserva los 604 registros excluidos, grupo, alias, posiciones de origen y destino, huella de contenido, hashes, regla y autorización. excluded_rows.parquet conserva las filas con tipos y metadatos de origen; permite reconstruir exactamente el archivo anterior junto a la capa retenida y sus posiciones. claim_id_aliases CSV/Parquet resuelve ID excluido→representante y no debe unirse como si añadiera observaciones o coste. Los datos originales siguen en Datos; no se borran ni reescriben D38, D40 o D41.

La conciliación exacta con Decimal reduce el incurrido neto aceptado observado en 3.174.167,49 CU: 1.833.024,44 motor, 1.112.148,78 edificios y 228.994,27 contenidos. Dentro de periodos actuales la diferencia es 3.173.808,61 CU; fuera de historia, 358,88 CU. Los seis rechazados reducen expedientes brutos, sin reducir coste ni frecuencia aceptados. La nueva clasificación tiene 413 registros anteriores al primer periodo frente a 414 antes de excluir una copia; las fechas y la cobertura no cambian. Quedan 160.432 aceptados asignables de 160.841 aceptados totales.

Pasaron {verify['checks_count']} controles técnicos: cohorte exacta, comparación de todos los valores retenidos y su orden, IDs, alias y bitácora, reconstrucción completa del original, idempotencia, rechazo de estado parcial o representante alterado, igualdad de payload por algoritmo de tuplas, conservación de controles no idénticos, conciliación de todos los componentes, clasificación temporal, esquema, hashes, catálogo y autorización. La representación de fecha del diagnóstico anterior (timestamp de medianoche) y la nueva (date32 fuente) se comparó a una resolución común sin alterar ninguno; se preservaron el verificador inicial y la nota previa a su primera ejecución. La segunda invocación real del aplicador comprobó que el catálogo DUP01 ya está aplicado, sin otra exclusión o publicación.

Se conserva la referencia exacta de las otras diez tablas; ahora hay siete tablas derivadas (seis pólizas/test y claims) y cuatro originales referenciados. Los 2.073 CAP01 y 1.454 capitales pendientes permanecen intactos; CON01 no se activa. current_dataset.json se publicó atómicamente solo después de verificar, comprobando que el puntero padre no hubiese cambiado concurrentemente. current_run.json, current_capital_correction.json y current_refinement.json conservan su alcance histórico; current_duplicate_application.json identifica DUP01.

La integración detectó que diagnostico_objetivo.py leía claims vigente pero reutilizaba agregados monetarios D30 anteriores a la deduplicación. Se reemplazó esa reutilización por asignación y agregados calculados desde el catálogo activo, sin cambiar fórmulas económicas o particiones. Metodología/protocolo pasan a 1.3 con el contrato de siniestros y el conteo actual 413. Versiones 1.2 y lector anterior archivados en Modelado/archivo/pre_DUP01_20261016T200039Z. Se ejecutó el lector real una vez sobre DUP01: {diagrel}. Sus conteos y costes asignados concilian con el libro decimal; entidades y productos permanecen iguales. Pasaron {len(checks)} controles de integración del consumidor. El índice diagnóstico se actualiza a esa evidencia, conservando la anterior. El cálculo es descriptivo en memoria; no materializa T0 operativo ni entrena modelos.

Los informes y cifras históricos de D30/D35/D37/D38/D40/D41 siguen referidos a sus snapshots con copias; no certifican cantidades posteriores a DUP01. La revisión de capitales, NCB, calendario bisiesto, cobertura, disponibilidad F0 y desarrollo/IBNR continúa. La propia depuración no prueba mejora competitiva ni coste último verdadero. No hubo proveedor externo, envíos, publicación, nuevas dependencias o delegación.

Aplican IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.5–3.6. Codex implementó, verificó y documentó; el participante autorizó la operación y cohorte. La revisión sigue siendo propia asistida por IA. Consultar duplicate_application y el catálogo activo para continuar con T0/F0 y particiones; no aplicar el filtro otra vez a tablas históricas ni expandirlo a siniestros nuevos sin evidencia y decisión.
''',encoding='utf-8')
    memory=root/'Preparación/MEMORIA_PROYECTO.md'
    memory.write_text(memory.read_text(encoding='utf-8')+f'''

## {decision}: DUP01 aplicado por autorización expresa, 16 de octubre de 2026

Capa activa: [current_dataset.json](../Hackaton/Semana 1/Limpieza/current_dataset.json). [Informe DUP01]({rel}/informe.html), [bitácora]({rel}/ledger/exclusion_ledger.csv) y [alias]({rel}/ledger/claim_id_aliases.csv). Se excluyeron únicamente las 604 copias congeladas de D41 y se conservaron los representantes de ocho dígitos. claims pasa de 163.150 a 162.546 filas; los 161.942 registros ajenos a los pares y cada valor retenido permanecen iguales, incluido orden y esquema. Excluded_rows tipado y posiciones permiten reversión exacta; alias no son observaciones adicionales.

La diferencia del neto aceptado observado es 3.174.167,49 CU, 3.173.808,61 en periodos actuales y 358,88 fuera de historia. Quedan 413 registros anteriores al primer periodo, frente a 414 previos a quitar esa copia, sin cambiar fechas. Los 57 grupos no idénticos se conservan. Pasaron {verify['checks_count']} controles propios, incluidos reconstrucción, idempotencia, conflictos, componentes monetarios y hashes. Los otros diez archivos del catálogo no cambian; CAP01 y los 1.454 capitales pendientes se conservan; CON01 sigue sin activar. Los originales e informes anteriores siguen intactos.

El protocolo 1.3 incorpora claims derivado. El lector descriptivo se corrigió para dejar de mezclar claims vigente con agregados D30 y se ejecutó una vez sobre DUP01. [Evidencia del diagnóstico actual]({diagrel}); {len(checks)} controles del consumidor concilian conteos/coste y preservación de entidades/productos. La versión 1.2 y lector previo están archivados. Estadísticas de investigaciones previas conservan su alcance anterior a DUP01. No hay tabla T0 operativa, entrenamiento, validación independiente o aprobación global para modelar. Próximo: integrar conciliación/asignación en T0, disponibilidad F0 y particiones; mantener las demás incidencias. Consultar {decision} y duplicate_application.
''',encoding='utf-8')
    statepath=root/'Preparación/ESTADO_PROYECTO.json';state=json.loads(statepath.read_text(encoding='utf-8'))
    state['duplicate_application']={'decision_id':decision,'rule':'DUP01','status':'applied_verified_explicit_participant_authorization',
        'run':rel,'report':rel+'/informe.html','catalog':rel+'/dataset_catalog.json','verification':rel+'/verification.json',
        'active_prepared_index':'../Hackaton/Semana 1/Limpieza/current_dataset.json','application_index':'../Hackaton/Semana 1/Limpieza/current_duplicate_application.json',
        'ledger':rel+'/ledger/exclusion_ledger.parquet','ledger_csv':rel+'/ledger/exclusion_ledger.csv',
        'aliases':rel+'/ledger/claim_id_aliases.parquet','aliases_csv':rel+'/ledger/claim_id_aliases.csv','typed_excluded_rows':rel+'/ledger/excluded_rows.parquet',
        'source_rows':163150,'derived_rows':162546,'excluded_records':604,'retained_values_changed':0,
        'other_claim_records_preserved':161942,'short_id_representatives_preserved':604,
        'excluded_by_line':{'motor':411,'buildings':109,'contents':84},'excluded_by_status':{'closed':586,'open':12,'repudiated':6},
        'net_accepted_reduction_CU':'3174167.49','net_accepted_reduction_assigned_CU':'3173808.61','net_accepted_reduction_prehistory_CU':'358.88',
        'prehistory_records_after':413,'prehistory_records_before':414,'cohort_expanded':False,'other_catalog_entries_changed':0,
        'exact_reversal_verified':True,'idempotence_verified':True,'originals_modified':False,'historical_runs_modified':False,
        'technical_checks':verify['checks_count'],'consumer_integration_checks':len(checks),'consumer_diagnostic':diagrel,
        'methodological_protocol_version':'1.3','historical_EDA_claim_cost_aggregates_reused':False,
        'human_cohort_and_operation_approved':True,'source_events_confirmed_by_organizer':False,'independent_validation':False,
        'models_trained':False,'T0_operationally_materialized':False,'overall_modeling_approval':False,
        'pending_capitals_unchanged':1454,'capital_CAP01_inherited':2073,'CON01_activated':False,
        'closure':'../'+closure.relative_to(root).as_posix()}
    state['duplicate_claim_review']['followup_application_decision']=decision
    state['duplicate_claim_review']['application_authorized_later']=True
    state['data_validation_gap_review']['resolved_followups']={'VD04':{'decision':decision,'status':'DUP01_applied_frozen_cohort','remaining':'No general event-identity rule or external source confirmation.'}}
    state['competition_data']['active_prepared_catalog']=rel+'/dataset_catalog.json'
    state['competition_data']['current_prepared_claim_records']=162546
    state['data_cleaning']['active_followup_decision']=decision
    state['methodological_plan']['version']='1.3';state['methodological_plan']['input_update_decision']=decision
    state['methodological_plan']['current_diagnostic']=diagrel
    state['technique_research']['later_claims_input_update_decision']=decision
    state['technique_research']['claim_statistics_are_pre_DUP01']=True
    for item in state['pending_priorities']:
        if item['id']=='P05':
            item['action']='DUP01 aplicado a 604 copias ('+decision+'); integrar asignación/conciliación en T0, contrato F0 y particiones; 413 registros fuera de historia. Mantener revisión de calendario, coberturas, capitales, NCB y candidata T/W.'
            item['status']='duplicate_cohort_applied_target_and_other_semantics_pending'
    a.c.dump(statepath,state)
    routespath=root/'RUTAS_PROYECTO.json';routes=json.loads(routespath.read_text(encoding='utf-8'))
    routes['week_1_duplicate_claim_application_index']='Hackaton/Semana 1/Limpieza/current_duplicate_application.json';a.c.dump(routespath,routes)
    old_actual=json.loads((model/'diagnosticos/actual.json').read_text(encoding='utf-8'))
    a.c.dump(model/'diagnosticos/actual.json',{'evidence':diag_path.relative_to(model/'diagnosticos').as_posix(),
        'script_snapshot':(diag_dir/'diagnostico_objetivo.py').relative_to(model/'diagnosticos').as_posix(),
        'scope':'Descriptive current DUP01 catalog; current claims/date assignment; no operational T0 or training.',
        'claims_rule':'DUP01','previous_evidence_preserved':old_actual.get('evidence'),'models_trained':0})
    week=root/'Hackaton/Semana 1/README.md'
    week.write_text(week.read_text(encoding='utf-8')+'\n\nDUP01 quedó aplicado por autorización del participante: `Limpieza/current_duplicate_application.json` conserva la nueva capa de 162.546 siniestros, las 604 exclusiones, alias y reversión. `Limpieza/current_dataset.json` apunta al catálogo actualizado. Las revisiones D40/D41 siguen siendo históricas; el diagnóstico de modelado vigente recalcula los agregados con claims depurado. No cambian originales, pólizas o capitales.\n',encoding='utf-8')
    for path in docs:
        dest=closure/'after'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dest)
    final=[]
    def finalcheck(name,ok):final.append({'name':name,'passed':bool(ok)});assert ok,name
    finalcheck('core_manifest_and_every_artifact_still_identical',a.c.digest(out/'manifest.json')==manifest_hash and all(a.c.digest(out/e['path'])==e['sha256'] for e in manifest['files']))
    finalcheck('active_prepared_pointer_unchanged_during_documentation',json.loads(current.read_text(encoding='utf-8'))==pointer)
    finalcheck('state_and_current_catalog_agree',state['competition_data']['active_prepared_catalog']==rel+'/dataset_catalog.json')
    finalcheck('all_application_state_paths_exist',all((root/'Preparación'/state['duplicate_application'][key]).exists()
        for key in ['run','report','catalog','verification','ledger','aliases','typed_excluded_rows','consumer_diagnostic','closure']))
    finalcheck('all_prior_state_top_level_sections_preserved',set(json.loads((closure/'before/Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))).issubset(state))
    finalcheck('decision_unique_and_referenced_in_memory',len(re.findall(r'^### '+decision+r',',decisions.read_text(encoding='utf-8'),flags=re.M))==1 and decision in memory.read_text(encoding='utf-8'))
    finalcheck('actual_diagnostic_index_resolves_to_fresh_current_claims',json.loads((model/'diagnosticos/actual.json').read_text(encoding='utf-8'))['evidence']==diag_path.relative_to(model/'diagnosticos').as_posix())
    a.c.dump(closure/'documentation_verification.json',{'passed':True,'checks_count':len(final),'checks':final,'decision_id':decision,
        'core_manifest_sha256':manifest_hash,'independent_validation':False})
    a.c.dump(closure/'manifest.json',{'files':[{'path':p.relative_to(closure).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(closure.rglob('*')) if p.is_file()]})
    print(json.dumps({'decision':decision,'technical_checks':verify['checks_count'],'consumer_checks':len(checks),'documentation_checks':len(final),
        'consumer_diagnostic':str(diag_dir),'closure':str(closure),'claims_after':162546}),flush=True)


if __name__=='__main__':main()
