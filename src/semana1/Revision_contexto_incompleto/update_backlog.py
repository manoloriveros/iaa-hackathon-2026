"""Reconcilia58 controles documentales con decisiones posteriores, sin cerrar trabajo por inferencia."""
from pathlib import Path
import importlib.util,json,sys
import review_incomplete as a
import clean_data as c
import pandas as pd

def main(out):
    assert not (out/'manifest.json').exists()
    old=json.loads((out/'evidence/D40_controls.json').read_text('utf-8'));state=json.loads((out/'evidence/state_before.json').read_text('utf-8'))
    spec=importlib.util.spec_from_file_location('observed_guard',a.ROOT/'Preparación/src/iaa_lab/predictor_guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    probe={name:guard.exclusion_reason(name) for name in ['renewal_decision','audit_ref_test2025','customer_service_contacts']}
    probe['selected_from_probe']=guard.select_predictor_columns(['renewal_decision','audit_ref_test2025','customer_service_contacts','sum_insured'])
    probe['scope']='Read-only diagnostic of exclusion guard alone, not a model run or a change. D50 recommends excluding contacts; current guard alone permits it.'
    probe['source_sha256']=c.digest(a.ROOT/'Preparación/src/iaa_lab/predictor_guard.py')
    c.dump(out/'predictor_guard_gap.json',probe)
    updates={
      'VD04':('implementado_en_cohorte_con_pendientes_residuales','DUP01 aplicado a 604 pares congelados, con alias y reversión. Los 57 grupos no idénticos D41 se conservaron y requieren criterio propio; no se declaran duplicados.', 'duplicate_application'),
      'VD05':('parcial_con_PRE00','Asignación por ocurrencia y guard PRE00 comprobados en diagnóstico; falta llevar conciliación y exclusión de 413 prehistóricos a T0 operativo.', 'prehistory_audit_application'),
      'VD06':('pendiente_implementacion','Materializar una fila por periodo con coste, conteos, pagos, reservas, recuperaciones y ceros legítimos; conciliar contra claims vigente.', 'prehistory_audit_application'),
      'VD09':('pendiente_revision_actualizada','Revisar own_damage fuera de comprehensive en claims vigente. El conteo D40 era previo a DUP01; no se presenta como un nuevo recuento.', 'duplicate_application'),
      'VD10':('pendiente_revision_actualizada','Revisar daño accidental frente a opción de hogar en claims vigente, distinguiendo semántica, endosos y datos. Los conteos D40 son históricos.', 'duplicate_application'),
      'VD11':('pendiente_recalculo_tras_capitales','Actualizar siniestros/costes frente a capitales y sublímites en CAP04R; no recortar pérdidas por capital ni trasladar el conteo D40 anterior a las reparaciones.', 'context_capital_application'),
      'VD16':('revisado_decision_pendiente','CAL00 mantiene fechas: 500.245 continuidades omiten 31-12-2024. Confirmar convención y tratar una eventual corrección con exposición/objetivo conciliados; no modificar hoy.', 'calendar_review'),
      'VD17':('parcial_con_REN00','REN00 conserva 2.742 pólizas rechazadas que continúan y sus siniestros. Faltan semántica contractual, cronología de endosos/cancelaciones y tratamiento prospectivo.', 'renewal_audit_application'),
      'VD18':('pendiente_contrato_operativo','Materializar disponibilidad por columna, fuente y ventana; excluir o separar datos posteriores/dudosos. F0 no está implementado completamente.', 'methodological_plan'),
      'VD23':('hallazgo_D50_sin_guard_completo','D50 pide excluir customer_service_contacts por fuga. La sonda actual confirma que el guard por sí solo aún lo permite; falta aplicar esa exclusión al contrato/selector y probarla. Fechar además impagos y desocupación.', 'technique_research_claude'),
      'VD24':('guard_implementado_semantica_pendiente','renewal_decision y audit_* ya bloqueados por el selector real; conservar la etiqueta y auditar la disponibilidad de sus derivados. No reabrir como tarea pendiente la marca REN00 ya aplicada.', 'renewal_audit_application'),
      'VD30':('parcial_467_pendientes_retrospectivos','CAP04R conserva 467 pendientes: 108 sin ancla (mantener por instrucción actual), 202 contexto incompleto (esta revisión), 138 otras contradicciones, 16 T/W, 2 dependencias CAP01 y 1 C48613718. Confirmar unidad y endosos, separar preparación por corte y no ampliar reglas por cascada.', 'context_capital_application'),
      'VD31':('candidato_sin_activar','D39 propone alias T/W; CON01 sigue inactivo y el material físico no está confirmado. Resolver significado o documentar hipótesis de modelado separada por fecha.', 'construction_review'),
      'VD41':('parcial_202_revisados_sin_imputar','Esta revisión distingue faltantes de fila y referencia en 202 casos. Aún faltan matrices generales de ausencia estructural/captura/temporal, coausencias y estabilidad por cohorte en todas las tablas.', None),
      'VD53':('parcial_linaje_actualizado','CAP01, CAP02R, CAP03R, CAP04R, DUP01, REN00 y PRE00 tienen bitácoras; conservar separación entre base y retrospectiva. Falta integrar esa elección en entrenamiento/inferencia reproducibles.', 'context_capital_application')}
    rows=[]
    for item in old:
        status,remaining,evidence=updates.get(item['id'],(item['status'],item['remaining_work'],None))
        source=state.get(evidence,{}) if evidence else {}
        rows.append({**item,'previous_status_D40':item['status'],'current_status':status,'remaining_work_current':remaining,
            'current_evidence_state_key':evidence,'current_evidence_location':source.get('run',source.get('workspace_relative_run',source.get('report',''))) if isinstance(source,dict) else '',
            'reconciliation_scope':'Documentary status reconciliation, not re-execution of all original 58 tests. Historical counts retained only as historical evidence.'})
    assert len(rows)==len({r['id'] for r in rows})==58
    c.dump(out/'validation_backlog_58.json',rows)
    flat=pd.DataFrame([{k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v) for k,v in row.items()} for row in rows]);a.save(flat,out,'validation_backlog_58')
    workstreams=[
      ('P0','Objetivo operativo T0','VD05,VD06,VD07','Persistir asignación única y componentes; conciliar costes/conteos y distinguir ceros de ausencia de etiqueta.'),
      ('P0','Disponibilidad F0 y fuga','VD18,VD23,VD24','Aplicar exclusión de contactos D50 en código; fechar cada predictor y probar rechazo de acceso al futuro.'),
      ('P0','Particiones y preparación por corte','VD26,VD27,VD28,VD29,VD42,VD47','Guardar V22/V23/V24, roles y dependencias; aprender imputación/transformaciones/historia dentro de cada corte, sin respaldos futuros.'),
      ('P0','Uniones y unidad de exposición','VD03,VD15,VD51','Exigir cardinalidades en construcción real de X/T0; conciliar filas, exposición y costes antes/después.'),
      ('P0','Reporte, desarrollo y recuperaciones','VD12,VD13,VD14,VD28','Acotar incertidumbre del último, retrasos e IBNR con sensibilidades; una sola valoración no identifica triángulos históricos.'),
      ('P0','Calendario y endosos','VD16,VD17','Confirmar el día omitido y convenciones; preservar CAL00/REN00 mientras no haya una decisión respaldada.'),
      ('P1','Capitales pendientes y escala','VD30','Conservar 108; revisar 202 sin imputar ni ampliar 400 días, y después 138 otras contradicciones, 16 T/W, 2 dependencias y 1 discrepancia residual.'),
      ('P1','Construcción T/W','VD31','Resolver significado y disponibilidad temporal de alias antes de activar una variante.'),
      ('P0','Cobertura frente a siniestros','VD09,VD10,VD11','Actualizar cruces en claims/CAP04R: peligro, opciones, capital y sublímites; conservar importes hasta aclarar.'),
      ('P1','Coherencia de autos','VD33,VD34,VD35,VD36,VD37','Revisar NCB/licencia, edades implícitas, cilindrada eléctrica, continuidad de vehículo/conductor, uso y kilometraje.'),
      ('P1','Hogar, ubicación y clima','VD38,VD39,VD40','Contrastar ocupación/protecciones/geografía y física del clima; no asumir maestros históricos o clima futuro disponible.'),
      ('P1','Faltantes, deriva y soporte','VD41,VD43,VD44','Perfilar coausencias y deriva en capa vigente, categorías nuevas y colas; separar no aplica, ausente y cero.'),
      ('P1','Colas, concentración e inflación','VD45,VD46','Examinar dependencia de eventos y grandes siniestros; separar tendencia, mezcla y desarrollo con límites explícitos.'),
      ('P1','Maestros, identidad y variables comerciales','VD08,VD19,VD20,VD21,VD22,VD25,VD48,VD49,VD55,VD56,VD57','Justificar ventanas y proxies de cliente/hogar/telemática/comercial; evitar memorización de IDs y uso de maestros posteriores.'),
      ('P0','Métrica, inferencia y segunda semana','VD50,VD51,VD52','Integrar Tweedie D² p=1,5 en CU por periodo, pesos/ceros/positividad; asegurar IDs/orden/cobertura y contrato de nuevos datos.'),
      ('P0','Aceptación, trazabilidad y revisión','VD01,VD02,VD04,VD32,VD53,VD54,VD58','Definir controles para piloto/comparación/entrega, reproducción desde cero y revisión humana; no atribuir independencia inexistente.')]
    streams=pd.DataFrame(workstreams,columns=['priority','workstream','control_ids','remaining_work']);a.save(streams,out,'validation_workstreams')
    c.dump(out/'validation_backlog_summary.json',{'controls_reconciled':58,'workstreams':len(streams),'not_reexecuted_all_controls':True,
        'already_implemented_scopes':['ID01/EXP01/CAT01/AGE01/CAP01','DUP01 exact 604 pairs','REN00 frozen 2742 policies','PRE00 exact 413 claims','CAP02R 867 + CAP03R 11 + CAP04R 109, retrospective only'],
        'new_operational_gap':'D50 contacts exclusion is documented, but exclusion_reason(customer_service_contacts) returns None in current guard.',
        'historical_D40_counts_not_refreshed':['Coverage screens','Electric engine and implied-license screens','General drift and missingness profiles'],
        'data_changed':False,'guard_modified':False,'models_trained':False,'independent_validation':False})
    print(json.dumps({'backlog_controls':58,'workstreams':len(streams),'contacts_guard_blocks':probe['customer_service_contacts'] is not None}))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
