"""Documenta la revisión de pendientes sin cambiar datos o corridas cerradas."""
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
import json
import re
import shutil
import subprocess

import audit_gaps as a


def main():
    root=a.ROOT
    pointer=json.loads((a.BASE/'current_run.json').read_text(encoding='utf-8'))
    out=root/pointer['workspace_relative_run']
    summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    manifest_hash=a.c.digest(out/'manifest.json')
    assert all(a.c.digest(out/e['path'])==e['sha256'] for e in manifest['files'])
    ident=datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ')
    closure=a.BASE/'closures'/ident
    (closure/'before').mkdir(parents=True,exist_ok=False);(closure/'after').mkdir()
    for name in ['verify_report.js','record_review.py']:shutil.copy2(a.BASE/name,closure/name)
    report=subprocess.run(['node',str(a.BASE/'verify_report.js'),str(out/'informe.html')],capture_output=True,text=True,encoding='utf-8',check=True)
    logic=json.loads(report.stdout);assert logic['passed']
    a.c.dump(closure/'report_logic_verification.json',logic)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.paths=[];self.ids=[]
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k=='id':self.ids.append(v)
                if k=='href' and v:self.paths.append(v)
    links=Links();links.feed((out/'informe.html').read_text(encoding='utf-8'))
    assert all((p[1:] in links.ids) if p.startswith('#') else (out/unquote(p)).is_file() for p in links.paths)
    assert len(links.ids)==len(set(links.ids))
    docs=['Preparación/DECISIONES.md','Preparación/MEMORIA_PROYECTO.md','Preparación/ESTADO_PROYECTO.json','RUTAS_PROYECTO.json','Hackaton/Semana 1/README.md']
    for path in docs:
        dst=closure/'before'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dst)
    decision_path=root/'Preparación/DECISIONES.md';text=decision_path.read_text(encoding='utf-8')
    decision='D'+str(max(int(x) for x in re.findall(r'\bD(\d+)\b',text))+1)
    rel='../'+out.relative_to(root).as_posix()
    duplicate=summary['new_screens']['semantic_duplicate_claims']
    decision_path.write_text(text+f'''

### {decision}, auditoría exhaustiva de pendientes y nuevos sondeos de calidad, 16 de octubre de 2026, America/Bogota

El participante pidió precisar exhaustivamente qué validación de datos falta. Se revisaron diccionario, evidencia D30/D32/D34/D35/D36/D37/D38/D39, protocolo 1.2 y prácticas IAA. La corrida {rel} conserva 58 controles/decisiones con alcance, estado, prioridad, trabajo restante y criterio de cierre, y un inventario de 105 nombres de campo y 242 apariciones en las once tablas de la capa activa D38. D39 sigue como candidata sin activar. No se declara que los 58 controles se hayan ejecutado o cerrado: cinco tienen evidencia técnica con alcance, trece están parciales y el resto conserva sus estados específicos. La prioridad es propia del proyecto y no un peso IAA.

Se añadieron sondeos dirigidos, sin corregir nada. Hay 604 pares idénticos en todos los campos salvo claim_id, incluidos reparador y tercero cuando constan: 1.208 filas, 604 adicionales si se confirmara conservar una por par, de ellas 598 aceptadas y seis rechazadas. La detección se comprobó con duplicación de filas y contador independiente de tuplas con nulos explícitos. Los IDs son únicos; por tanto, el control previo de clave no detectaba esta coincidencia de contenido. El incurrido neto aceptado de una fila adicional por par suma {duplicate['hypothetical_net_reduction_all_reported_CU']} CU en todo el fichero, de los que {duplicate['hypothetical_net_reduction_assigned_current_periods_CU']} CU son asignables a periodos observados y {duplicate['hypothetical_net_reduction_outside_history_CU']} CU anteriores a su historia. Es sensibilidad hipotética, no sobrecoste confirmado ni deduplicación aplicada. Los pares completos, claves, posiciones relativas y asignación se conservan para decidir antes de fijar T0. Ejemplo M27706820: CL40310602 y CL175619477, robo ocurrido 01-11-2022 y reportado 15-11-2022, mismo neto 1.418,65 CU.

Se detectan 500.245 continuidades con un día de hueco entre el fin 30-12-2024 y el inicio 01-01-2025: 200.063 motor, 150.111 edificios y 150.071 contenidos. Ningún periodo cubre el 31-12-2024 y no hay siniestros ocurridos ese día. EXP01 sigue coincidiendo con las fechas originales; la omisión de calendario es una cuestión distinta, potencial convención del generador sin confirmar. No se extienden fechas ni se inventa cobertura, exposición o siniestros. Guardar el supuesto y estudiar su materialidad antes de interpretar años completos.

En aceptados asignados por fecha, cuatro own_damage están fuera de comprehensive (tres TPFT y uno TPO); 506 accidental_damage de edificios y 1.090 de contenidos tienen cobertura opcional falsa. Los nombres no bastan para decidir si son errores, cobertura básica, excepciones o clasificación. Se conservan pagos y casos; no se eliminan ni se imponen ceros contractuales. Catorce de los registros señalados de daño accidental pertenecen también a pares potencialmente duplicados, por lo que no se suman las alertas como conjuntos independientes. Ocho siniestros de edificios y tres de contenidos superan el capital con su incurrido neto del periodo: revisar escala, límites, gastos e indexación sin truncar costes automáticamente.

En autos 2021–2025, 99.376 filas electric incluyen 96.843 cilindradas positivas y 2.533 ausentes; ninguna informada es cero. Requiere aclarar unidad/equivalencia o error antes de atribuirle significado físico o cambiarla. Son 76.878 positivas de entrenamiento y 19.965 de test. Otros 3.717 registros dan driver_age-years_licensed<16: 16 es un umbral de cribado analítico, no mínimo legal de una jurisdicción inventada. Conductor y tomador pueden ser personas distintas. No se aplica corrección de edades/licencia ni se transforma eléctrico a cilindrada cero.

Los sondeos comprueban también unicidad global de los 3.035.950 row_id de pólizas, una persona por policy_id en estos archivos, franquicias voluntarias en el vocabulario oficial y días de granizo/helada no superiores al año. Estos resultados no convierten relaciones plausibles en pruebas de disponibilidad temporal o de verdad de cada dato. Los perfiles anteriores de deriva D30 se marcan como previos a EXP01/CAP01/CAT01/AGE01; sus campos afectados no se reutilizan como perfil vigente sin actualización.

El orden recomendado es decidir/versionar VD04, integrar asignación y conciliación completa de siniestros, materializar T0 con componentes y ceros, fijar supuestos de calendario/cobertura, aplicar F0 con un contrato de disponibilidad por campo y guardar V22/V23/V24 y roles. Los bloques de clima realizado 2025, telemática, contactos, desocupación y maestros sin fecha pueden excluirse del piloto para acotar incertidumbre. La validación de último, IBNR, recuperaciones e inflación requiere sensibilidad; una única valoración no permite reconstruir trayectorias financieras ni un backtest histórico exacto. No esperar identificar perfectamente el último para iniciar una referencia T0 de alcance explícito; tampoco declarar lista una base por tener rangos y claves válidos.

Permanecen 1.454 capitales, NCB en 161.822 filas, nombre/adopción de T/W, nulos y su mecanismo, coherencia longitudinal de riesgo y producto, continuidad de maestros, deriva/soporte de segmentos, dependencia cliente-dirección-ramos-eventos, métricas/unidad y entrega. El informe define cierre por etapa. P0 significa que una decisión no debe quedar silenciosa al construir objetivo/variables/evaluación; puede resolverse con exclusión de bloque o escenario delimitado, no implica prohibir todo piloto hasta cerrar los 58 asuntos.

Pasaron 14 comprobaciones propias de lógica/coherencia de los sondeos, inventario y hashes; siete de filtros/búsqueda con DOM mínimo; enlaces e integración documental se revisan aparte. No equivalen a resolver los 58 pendientes ni a renderizar en navegador o validar independientemente. Los once originales, seis derivados y puntero activo permanecen por hash. Se conservan datos, corridas y capitales anteriores, incluidos 2.073 CAP01 y los 1.454 pendientes. No hubo entrenamiento, construcción operativa de T0, deduplicación, imputación, cambio de fechas, activación de CON01, proveedor externo, envío, publicación o delegación.

Aplican IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.1–3.3 y §§3.5–3.6. Codex revisó la cobertura, formuló sondeos y criterios de cierre, y documentó resultados deterministas. El participante pidió la revisión; las correcciones potenciales siguen sin aprobarse. Consultar data_validation_gap_review en ESTADO_PROYECTO.json y el índice Validacion_datos/current_run.json antes de construir las etiquetas.
''',encoding='utf-8')
    memory=root/'Preparación/MEMORIA_PROYECTO.md'
    memory.write_text(memory.read_text(encoding='utf-8')+f'''

## {decision}: pendientes exhaustivos de validación y nuevos hallazgos, 16 de octubre de 2026

El [informe]({rel}/informe.html) conserva 58 controles/decisiones y un inventario de 105 nombres de columna (242 apariciones). D38 sigue activo; D39 no se activó. La revisión de cobertura no certifica una base para modelar ni afirma haber cerrado todos los controles. El primer trabajo será decidir el tratamiento de duplicados semánticos, construir T0 con conciliación, aplicar F0 por disponibilidad y persistir particiones. Ver [matriz estructurada]({rel}/review_controls.json).

Hay 604 pares de siniestros idénticos salvo claim_id, con 1.208 filas implicadas. Si se confirmara una sola fila por par, la sensibilidad sería {duplicate['hypothetical_net_reduction_all_reported_CU']} CU de neto aceptado observado total, {duplicate['hypothetical_net_reduction_assigned_current_periods_CU']} CU dentro de periodos observados. No se deduplicó ni se declara sobrecoste confirmado. También hay 500.245 continuidades que omiten 31-12-2024 (200.063 motor, 150.111 edificios, 150.071 contenidos); ni periodos ni siniestros cubren ese día. EXP01 coincide con las fechas existentes; no corregirlas por inferencia.

Cuatro own_damage aceptados están fuera de comprehensive; 506/1.090 accidental_damage de edificios/contenidos tienen opción falsa; ocho/tres netos de hogar superan capital. Revisar alcance, clasificación, escala y límites, sin borrar pagos ni imponer ceros o topes. En eléctricos hay 96.843 cilindradas positivas de 99.376 filas (resto ausente), y 3.717 edades implícitas de licencia inferiores a 16 como cribado sin supuesto legal. Los conjuntos se solapan y no se suman como errores independientes.

Se conservan los 1.454 capitales pendientes y 161.822 NCB en revisión. Faltan disponibilidad por predictor, maestros históricos, nulos por cohorte, preparación dentro de folds, deriva actualizada y soporte/dependencia, desarrollo/IBNR y entrega. No se puede identificar completamente el último o la información financiera histórica con una única valoración; usar límites y sensibilidades. Un piloto T0 puede empezar con decisiones trazables y bloques dudosos excluidos sin esperar perfección. Catorce controles del sondeo y siete del informe pasaron; no son aprobación de toda la data ni revisión independiente. No cambió ningún dato, fecha, capital o catálogo preparado. Consultar {decision} y el estado nuevo.
''',encoding='utf-8')
    statepath=root/'Preparación/ESTADO_PROYECTO.json';state=json.loads(statepath.read_text(encoding='utf-8'))
    state['data_validation_gap_review']={
        'decision_id':decision,'status':'exhaustive_scope_review_with_new_screens_not_data_approval',
        'run':rel,'report':rel+'/informe.html','review_controls':rel+'/review_controls.json','field_inventory':rel+'/field_inventory.json',
        'current_index':'../Hackaton/Semana 1/Validacion_datos/current_run.json','review_items':58,'field_names':105,'column_occurrences':242,
        'semantic_duplicate_groups':604,'semantic_duplicate_member_rows':1208,'hypothetical_extra_rows':604,
        'duplicate_net_sensitivity_all_reported_CU':duplicate['hypothetical_net_reduction_all_reported_CU'],
        'duplicate_net_sensitivity_assigned_current_periods_CU':duplicate['hypothetical_net_reduction_assigned_current_periods_CU'],
        'duplicate_claims_not_deleted':True,'duplicate_errors_not_confirmed':True,
        'calendar_gap_rows_2024_2025':500245,'calendar_date_not_changed':True,
        'own_damage_outside_comprehensive':4,'home_accidental_damage_cover_false':1596,'claim_net_above_capital':11,
        'electric_positive_engine_cc_rows':96843,'electric_total_rows':99376,
        'implied_license_age_below_screen_16':3717,'screen_16_is_not_legal_rule':True,
        'screen_checks_passed':14,'report_logic_checks_passed':7,'all_58_items_closed':False,
        'new_priority_order':['review_semantic_duplicate_claims','T0_assignment_and_financial_reconciliation',
            'calendar_and_coverage_assumptions','F0_feature_availability_contract','persistent_temporal_partitions'],
        'no_data_changes':True,'active_dataset_changed':False,'construction_candidate_activated':False,
        'models_trained':False,'T0_materialized':False,'independent_validation':False,'browser_rendering_verified':False,
        'closure':'../'+closure.relative_to(root).as_posix()}
    state['methodological_plan']['validation_gap_review_decision']=decision
    for entry in state['pending_priorities']:
        if entry['id']=='P05':
            entry['action']='Revisión '+decision+': decidir duplicados de siniestros, convención del 31-12-2024 y coberturas; conciliar/materializar T0, fijar F0 y particiones; conservar capitales, NCB y candidata T/W hasta decisiones trazables.'
            entry['status']='new_semantic_screens_and_target_contract_pending'
    a.c.dump(statepath,state)
    routespath=root/'RUTAS_PROYECTO.json';routes=json.loads(routespath.read_text(encoding='utf-8'))
    routes['week_1_validation_gap_review_index']='Hackaton/Semana 1/Validacion_datos/current_run.json';a.c.dump(routespath,routes)
    week=root/'Hackaton/Semana 1/README.md'
    week.write_text(week.read_text(encoding='utf-8')+'\n\nLa revisión exhaustiva de validación se consulta en `Validacion_datos/current_run.json`: conserva 58 controles/decisiones, inventario de las 105 columnas y nuevos sondeos de duplicados semánticos de siniestros, calendario 2024–2025, coberturas y atributos de riesgo. Es una revisión con criterios de cierre; no modifica datos ni aprueba el conjunto para modelar.\n',encoding='utf-8')
    for path in docs:
        dst=closure/'after'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dst)
    integration=[]
    def check(name,ok):integration.append({'name':name,'passed':bool(ok)});assert ok,name
    check('review_manifest_and_all_run_artifacts_unchanged',a.c.digest(out/'manifest.json')==manifest_hash and all(a.c.digest(out/e['path'])==e['sha256'] for e in manifest['files']))
    check('report_local_files_and_anchors_resolve',all((p[1:] in links.ids) if p.startswith('#') else (out/unquote(p)).is_file() for p in links.paths))
    check('report_filters_pass_without_browser_claim',logic['passed'] and not logic['real_browser_rendering'])
    check('active_data_pointer_unchanged',a.c.digest(root/'Hackaton/Semana 1/Limpieza/current_dataset.json')==a.c.digest(out/'evidence/active_dataset.json'))
    check('state_paths_resolve',all((root/'Preparación'/state['data_validation_gap_review'][key]).exists() for key in ['run','report','review_controls','field_inventory','current_index','closure']))
    check('state_preserves_existing_top_level_sections',set(json.loads((closure/'before/Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))).issubset(state))
    check('state_keeps_D38_and_CON01_candidate_status',state['data_refinement']['decision_id']=='D38' and not state['construction_review']['active_dataset_modified'])
    check('decision_unique_and_memory_referenced',len(re.findall(r'^### '+decision+r',',decision_path.read_text(encoding='utf-8'),flags=re.M))==1 and decision in memory.read_text(encoding='utf-8'))
    a.c.dump(closure/'integration_verification.json',{'passed':True,'checks_count':len(integration),'checks':integration,
        'decision_id':decision,'review_manifest_sha256':manifest_hash,'independent_validation':False})
    a.c.dump(closure/'manifest.json',{'files':[{'path':p.relative_to(closure).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(closure.rglob('*')) if p.is_file()]})
    print(json.dumps({'decision':decision,'report_checks':logic['checks_count'],'integration_checks':len(integration),'closure':str(closure),'no_data_changes':True}),flush=True)


if __name__=='__main__':main()
